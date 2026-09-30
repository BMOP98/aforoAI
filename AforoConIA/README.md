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
