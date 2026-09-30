import os
from datetime import datetime, timezone
import requests

API_URL = os.getenv("AFOROAI_API_URL", "http://127.0.0.1:8000")
DEVICE_ID = os.getenv("AFOROAI_DEVICE_ID", "CAM-AULA-01")
CAPACIDAD = int(os.getenv("AFOROAI_CAPACIDAD", "25"))


def enviar_medicion(personas: int, origen: str = "REAL") -> dict:
    payload = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "personas": int(personas),
        "capacidad": CAPACIDAD,
        "origen": origen,
    }
    response = requests.post(f"{API_URL}/api/mediciones", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()
