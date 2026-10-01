# AforoAI - Infraestructura AWS

Esta carpeta contiene los recursos relacionados con el despliegue de AforoAI en AWS.

## Arquitectura

El sistema utiliza los siguientes servicios:

- Amazon S3
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB

---

## 1. Amazon S3

### Frontend

Bucket:

`aforoai-dashboard-front`

Contiene el dashboard web de AforoAI.

El frontend está compuesto principalmente por:

- `index.html`
- `app.js`
- `styles.css`

El navegador consulta la API de AforoAI para obtener las mediciones históricas y la predicción.

### Modelo de Machine Learning

Bucket:

`aforoai-modelo-2026-bmop`

Archivo:

`occupancy_model.json`

Este archivo contiene el modelo Random Forest exportado para ser utilizado por AWS Lambda.

La función Lambda obtiene el modelo desde este bucket cuando necesita realizar una predicción.

---

## 2. AWS Lambda

Función:

`AforoAI-ProcesarMedicion`

Código fuente:

`aws/lambda/procesar-medicion/lambda_function.py`

La función Lambda concentra la lógica principal de procesamiento de las mediciones y predicciones.

### POST /api/mediciones

Recibe una medición de ocupación y la almacena en DynamoDB.

Los principales datos recibidos son:

- `device_id`
- `timestamp`
- `personas`
- `capacidad`
- `origen`

La función calcula:

- porcentaje de ocupación
- estado de ocupación

y almacena la medición en la tabla `AforoAI-Mediciones`.

### GET /api/historico

Obtiene las mediciones históricas almacenadas para el dispositivo:

`CAM-AULA-01`

Las mediciones son utilizadas por el dashboard para mostrar el comportamiento histórico de la ocupación.

### GET /api/prediccion

Obtiene las mediciones recientes y construye las variables necesarias para realizar una predicción.

El modelo utilizado es:

`RandomForestRegressor`

La predicción corresponde a la cantidad estimada de personas dentro de:

`30 minutos`

La función también calcula el porcentaje de ocupación estimado y determina el estado estimado de ocupación.

---

## 3. Amazon DynamoDB

Tabla:

`AforoAI-Mediciones`

La tabla almacena las mediciones de ocupación recopiladas por el sistema.

Cada medición contiene información como:

- `device_id`
- `timestamp`
- `personas`
- `capacidad`
- `ocupacion_porcentaje`
- `estado`
- `origen`

Los datos pueden tener diferentes orígenes, por ejemplo:

- `REAL`
- datos de prueba

Las mediciones reales son enviadas por el componente IoT después de que la cámara realiza el conteo de personas mediante visión artificial.

---

## 4. Amazon API Gateway

API:

`AforoAI-API`

La API permite que el frontend y los componentes del sistema se comuniquen con AWS Lambda mediante solicitudes HTTP.

Las rutas utilizadas son:

```text
POST /api/mediciones
GET  /api/historico
GET  /api/prediccion
```

### POST /api/mediciones

Permite enviar una nueva medición de ocupación al sistema.

El componente IoT utiliza esta ruta para enviar el conteo de personas obtenido mediante YOLO.

### GET /api/historico

Permite obtener las mediciones históricas almacenadas en DynamoDB.

El dashboard utiliza esta información para mostrar el historial de ocupación.

### GET /api/prediccion

Permite obtener la predicción de ocupación para los próximos 30 minutos.

El dashboard utiliza esta respuesta para mostrar:

- personas actuales
- personas estimadas
- porcentaje de ocupación estimado
- estado estimado
- modelo utilizado

---

## 5. Modelo de Machine Learning

El código de entrenamiento se encuentra en:

`ml/train.py`

El modelo entrenado se encuentra en:

`ml/models/occupancy_model.pkl`

El modelo exportado para su utilización en AWS se encuentra en:

`ml/models/occupancy_model.json`

Las métricas obtenidas durante el entrenamiento fueron:

- MAE: `2.21`
- RMSE: `2.804`
- R²: `0.824`

El objetivo del modelo es estimar:

`personas dentro de 30 minutos`

Las variables utilizadas por el modelo son:

- `hora_decimal`
- `dia_semana`
- `personas`
- `ocupacion_porcentaje`
- `lag_1`
- `lag_2`
- `promedio_3`

El modelo utilizado es:

`RandomForestRegressor`

---

## 6. Flujo completo de datos

El flujo principal del sistema es:

```text
Cámara
   |
   v
YOLO11n
   |
   | Conteo de personas
   v
vision/detector_iot.py
   |
   v
iot/sender.py
   |
   | HTTP POST
   v
Amazon API Gateway
   |
   v
AWS Lambda
   |
   v
Amazon DynamoDB
   |
   +-------------------------+
   |                         |
   v                         v
Histórico                 Predicción
                              |
                              v
                    RandomForestRegressor
                              |
                              v
                       Amazon S3
                  occupancy_model.json
                              |
                              v
                       Resultado de
                        predicción
                              |
                              v
                         Dashboard
```

---

## 7. Componentes locales

### Visión artificial

Código principal:

`vision/detector_iot.py`

Utiliza YOLO11n para detectar personas mediante la cámara del computador.

El sistema no realiza reconocimiento facial ni identificación de personas.

El resultado de la detección es únicamente la cantidad de personas presentes.

### IoT

Código:

`iot/sender.py`

Envía la cantidad de personas detectadas hacia la API de AforoAI.

Las mediciones contienen información como:

- dispositivo
- fecha y hora
- cantidad de personas
- capacidad
- origen

### Backend

Código:

`backend/main.py`

Permite ejecutar localmente la API utilizada durante el desarrollo y las pruebas.

### Frontend

Código:

`frontend/`

Contiene el dashboard web utilizado para visualizar:

- ocupación actual
- capacidad
- porcentaje de ocupación
- estado
- estadísticas
- histórico
- predicción

---

## 8. Seguridad

Las credenciales y secretos locales no forman parte del repositorio.

El archivo:

`.env`

contiene información privada y está excluido mediante `.gitignore`.

El repositorio contiene únicamente:

`.env.example`

como plantilla de configuración.

No se deben almacenar tokens, contraseñas, claves AWS u otras credenciales dentro del repositorio.

---

## 9. Despliegue actual

El despliegue de AforoAI en AWS se realizó manualmente utilizando la consola de AWS.

El código fuente de Lambda se conserva en:

`aws/lambda/procesar-medicion/lambda_function.py`

El modelo utilizado por Lambda se encuentra publicado en:

`aforoai-modelo-2026-bmop/occupancy_model.json`

El frontend se encuentra publicado en:

`aforoai-dashboard-front`

El archivo ZIP utilizado para actualizar Lambda es un artefacto de despliegue y no forma parte del repositorio.

---

## 10. Recursos AWS utilizados

### Amazon S3

```text
aforoai-dashboard-front
aforoai-modelo-2026-bmop
```

### AWS Lambda

```text
AforoAI-ProcesarMedicion
```

### Amazon DynamoDB

```text
AforoAI-Mediciones
```

### Amazon API Gateway

API utilizada por el sistema:

```text
https://vlfoqr98de.execute-api.us-east-1.amazonaws.com/api
```

---

## 11. Arquitectura general

La arquitectura final integra IoT, visión artificial, computación en la nube, almacenamiento, Machine Learning y visualización.

```text
                AforoAI
                   |
          +--------+--------+
          |                 |
          v                 v
       Cámara           Datos históricos
          |                 |
          v                 |
       YOLO11n              |
          |                 |
          v                 |
     Conteo personas        |
          |                 |
          +--------+--------+
                   |
                   v
              API Gateway
                   |
                   v
                Lambda
              /         \
             /           \
            v             v
       DynamoDB          S3
       Histórico       Modelo ML
            |             |
            |             v
            |        Random Forest
            |             |
            +------+------+
                   |
                   v
               Dashboard
```

---

## 12. Objetivo del prototipo

El objetivo de AforoAI es demostrar un flujo completo de IoT, Cloud Computing, Inteligencia Artificial y análisis de datos.

El sistema permite:

1. Capturar imágenes mediante una cámara.
2. Detectar personas mediante YOLO11n.
3. Obtener el conteo de personas.
4. Enviar la medición hacia AWS.
5. Almacenar las mediciones en DynamoDB.
6. Analizar datos históricos.
7. Utilizar un modelo Random Forest para estimar la ocupación futura.
8. Mostrar los resultados mediante un dashboard web.