# AforoAI — MVP local

Flujo funcional: **cámara/YOLO → cliente IoT → FastAPI → SQLite → dashboard**. Las imágenes se procesan localmente y no se almacenan ni transmiten.

## Inicio rápido (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Terminal 1 — API
```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload
```
Comprueba: http://127.0.0.1:8000/docs

### Terminal 2 — crear histórico simulado (una vez)
```powershell
.\.venv\Scripts\Activate.ps1
python simulator\generate_data.py
```

### Terminal 2 — dispositivo real con cámara
```powershell
python vision\detector_iot.py
```
Envía un conteo REAL cada 10 segundos. Q cierra la cámara.

### Terminal 3 — dashboard
```powershell
.\.venv\Scripts\Activate.ps1
cd frontend
python -m http.server 5173
```
Abre: http://127.0.0.1:5173

## Persistencia
SQLite se crea automáticamente en `backend/aforoai.db`. No subir el archivo a Git.

## Machine Learning +30 min
Con el backend y datos simulados ya creados:

    python ml\train.py

Se guarda `ml/models/occupancy_model.pkl` y `metrics.json`. Reinicia el backend si estaba abierto y consulta `/api/prediccion` o abre el dashboard.

El objetivo de entrenamiento es la cantidad de personas 30 minutos después. El entrenamiento usa división temporal 80/20 y reporta MAE, RMSE y R².

## Alertas Telegram
1. Copia `.env.example` como `.env`.
2. Completa `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
3. Prueba con `python test_telegram.py`.
4. Las mediciones REAL disparan alertas al cambiar de nivel: PROXIMO (>=80% y <100%), COMPLETO (=100%) y EXCEDIDO (>100%).
5. Los datos SIMULADO no notifican por defecto para evitar spam.
