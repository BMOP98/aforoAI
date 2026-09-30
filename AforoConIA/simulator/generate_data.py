"""Genera histórico sintético y lo envía por la misma API que el dispositivo real."""
import math
import random
from datetime import datetime, timedelta, timezone
import requests

API_URL = "http://127.0.0.1:8000"
DEVICE_ID = "SIM-AULA-01"
CAPACIDAD = 25
DAYS = 7
INTERVAL_MINUTES = 30


def expected(hour: float) -> float:
    morning = 13 * math.exp(-((hour - 10.5) / 2.0) ** 2)
    afternoon = 18 * math.exp(-((hour - 15.5) / 2.2) ** 2)
    return 2 + morning + afternoon


def main():
    random.seed(42)
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - timedelta(days=DAYS)
    current = start
    sent = 0
    while current <= end:
        weekday_factor = 0.55 if current.weekday() >= 5 else 1.0
        hour = current.hour + current.minute / 60
        people = max(0, round(expected(hour) * weekday_factor + random.gauss(0, 2.2)))
        if random.random() < 0.015:
            people += random.randint(7, 12)
        payload = {
            "device_id": DEVICE_ID,
            "timestamp": current.isoformat(),
            "personas": people,
            "capacidad": CAPACIDAD,
            "origen": "SIMULADO",
        }
        r = requests.post(f"{API_URL}/api/mediciones", json=payload, timeout=5)
        r.raise_for_status()
        sent += 1
        current += timedelta(minutes=INTERVAL_MINUTES)
    print(f"OK: {sent} mediciones simuladas creadas.")


if __name__ == "__main__":
    main()
