import json
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


TABLE_NAME = "AforoAI-Mediciones"
MODEL_PATH = "/var/task/occupancy_model.json"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

MODEL = None


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=decimal_to_float)
    }


def load_model():
    global MODEL

    if MODEL is None:
        with open(MODEL_PATH, "r", encoding="utf-8") as f:
            MODEL = json.load(f)

    return MODEL


def tree_predict(tree, features):
    node = 0

    while tree["children_left"][node] != -1:

        feature_index = tree["feature"][node]
        threshold = tree["threshold"][node]

        if features[feature_index] <= threshold:
            node = tree["children_left"][node]
        else:
            node = tree["children_right"][node]

    return tree["value"][node]


def random_forest_predict(model, features):

    predictions = []

    for tree in model["trees"]:
        predictions.append(
            tree_predict(tree, features)
        )

    return sum(predictions) / len(predictions)


def estado_para(porcentaje):
    if porcentaje <= 40:
        return "BAJO"

    if porcentaje <= 70:
        return "NORMAL"

    if porcentaje <= 100:
        return "ALTO"

    return "AFORO_SUPERADO"


def lambda_handler(event, context):

    method = (
        event
        .get("requestContext", {})
        .get("http", {})
        .get("method")
    )

    path = (
        event
        .get("requestContext", {})
        .get("http", {})
        .get("path", "")
    )


    # ==========================================
    # POST /api/mediciones
    # ==========================================

    if method == "POST":

        if isinstance(event.get("body"), str):
            data = json.loads(event["body"])
        else:
            data = event

        device_id = data["device_id"]
        personas = int(data["personas"])
        capacidad = int(data.get("capacidad", 25))

        ocupacion = round(
            (personas / capacidad) * 100,
            2
        )

        if ocupacion > 100:
            estado = "EXCEDIDO"
        elif ocupacion == 100:
            estado = "COMPLETO"
        elif ocupacion >= 80:
            estado = "PROXIMO"
        else:
            estado = "NORMAL"

        item = {
            "device_id": device_id,
            "timestamp": data.get(
                "timestamp",
                datetime.now(timezone.utc).isoformat()
            ),
            "personas": personas,
            "capacidad": capacidad,
            "ocupacion_porcentaje": Decimal(str(ocupacion)),
            "estado": estado,
            "origen": data.get("origen", "REAL")
        }

        table.put_item(Item=item)

        return response(201, item)


    # ==========================================
    # GET /api/historico
    # ==========================================

    if method == "GET" and path.endswith("/historico"):

        result = table.query(
            KeyConditionExpression=
            Key("device_id").eq("CAM-AULA-01"),

            ScanIndexForward=False,

            Limit=100
        )

        items = result["Items"]

        items.reverse()

        return response(
            200,
            items
        )


    # ==========================================
    # GET /api/prediccion
    # ==========================================

    if method == "GET" and path.endswith("/prediccion"):

        result = table.query(
            KeyConditionExpression=
            Key("device_id").eq("CAM-AULA-01"),

            ScanIndexForward=False,

            Limit=3
        )

        rows = result["Items"]

        if not rows:
            return response(
                404,
                {"error": "No existen mediciones"}
            )

        latest = rows[0]

        chronological = list(reversed(rows))

        values = [
            int(row["personas"])
            for row in chronological
        ]

        while len(values) < 3:
            values.insert(0, values[0])

        timestamp = datetime.fromisoformat(
            latest["timestamp"].replace(
                "Z",
                "+00:00"
            )
        )

        hora_decimal = (
            timestamp.hour +
            timestamp.minute / 60
        )

        dia_semana = timestamp.weekday()

        personas = int(latest["personas"])

        capacidad = int(latest["capacidad"])

        ocupacion = float(
            latest["ocupacion_porcentaje"]
        )

        lag_1 = values[-2]

        lag_2 = values[-3]

        promedio_3 = sum(values[-3:]) / 3


        features = [
            hora_decimal,
            dia_semana,
            personas,
            ocupacion,
            lag_1,
            lag_2,
            promedio_3
        ]


        model = load_model()

        predicted = random_forest_predict(
            model,
            features
        )

        predicted = max(
            0,
            int(round(predicted))
        )

        predicted_percentage = round(
            predicted / capacidad * 100,
            2
        )

        return response(
            200,
            {
                "personas_actuales": personas,
                "capacidad": capacidad,
                "horizonte_minutos": 30,
                "personas_estimadas": predicted,
                "ocupacion_estimada_porcentaje":
                    predicted_percentage,
                "estado_estimado":
                    estado_para(predicted_percentage),
                "modelo":
                    "RandomForestRegressor"
            }
        )


    return response(
        404,
        {
            "error": "Ruta no soportada",
            "method": method,
            "path": path
        }
    )