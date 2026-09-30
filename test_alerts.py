import time
from datetime import datetime, timezone

import requests


API_URL = "http://127.0.0.1:8000/api/mediciones"

DEVICE_ID = "TEST-ALERTAS"
CAPACIDAD = 25


def enviar_medicion(personas: int):
    porcentaje = round((personas / CAPACIDAD) * 100, 2)

    if porcentaje > 100:
        estado = "AFORO_SUPERADO"
    elif porcentaje >= 80:
        estado = "ALTO"
    elif porcentaje >= 40:
        estado = "NORMAL"
    else:
        estado = "BAJO"

    medicion = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "personas": personas,
        "capacidad": CAPACIDAD,
        "ocupacion_porcentaje": porcentaje,
        "estado": estado,
        "origen": "REAL",
    }

    print(
        f"Enviando: {personas}/{CAPACIDAD} "
        f"({porcentaje} %) - {estado}"
    )

    response = requests.post(
        API_URL,
        json=medicion,
        timeout=10,
    )

    print(
        f"Respuesta API: {response.status_code} "
        f"{response.text}"
    )

    response.raise_for_status()


def main():
    pruebas = [
        (10, "Sin alerta"),
        (20, "Proximo al limite"),
        (22, "Mismo nivel: NO debe repetir alerta"),
        (25, "Aforo completo"),
        (25, "Mismo nivel: NO debe repetir alerta"),
        (27, "Aforo excedido"),
        (28, "Mismo nivel: NO debe repetir alerta"),
        (10, "Regreso a nivel normal"),
    ]

    print("\n=== AforoAI - Prueba de alertas ===\n")

    for personas, descripcion in pruebas:
        print(f"\n--- {descripcion} ---")

        try:
            enviar_medicion(personas)
        except requests.RequestException as error:
            print(f"\nERROR comunicando con AforoAI: {error}")
            print(
                "Comprueba que el backend este ejecutandose "
                "en http://127.0.0.1:8000"
            )
            return

        time.sleep(2)

    print("\n=== Prueba finalizada ===")
    print("Revisa Telegram.")
    print("Deberias haber recibido solo 3 alertas:")
    print("1. Proximo al limite")
    print("2. Aforo completo")
    print("3. Aforo excedido")


if __name__ == "__main__":
    main()