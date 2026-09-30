import os
import sqlite3
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
ALERT_THRESHOLD = float(os.getenv("TELEGRAM_ALERT_THRESHOLD", "80"))
NOTIFY_SIMULATED = os.getenv("TELEGRAM_NOTIFY_SIMULATED", "false").lower() in {"1", "true", "yes", "si"}


def telegram_configurado() -> bool:
    return bool(BOT_TOKEN and CHAT_ID)


def nivel_alerta(personas: int, capacidad: int) -> str:
    if personas > capacidad:
        return "EXCEDIDO"
    if personas == capacidad:
        return "COMPLETO"
    porcentaje = personas / capacidad * 100
    if porcentaje >= ALERT_THRESHOLD:
        return "PROXIMO"
    return "NORMAL"


def _mensaje(nivel: str, medicion: dict) -> str:
    personas = medicion["personas"]
    capacidad = medicion["capacidad"]
    porcentaje = medicion["ocupacion_porcentaje"]
    device = medicion["device_id"]
    timestamp = medicion["timestamp"]

    if nivel == "PROXIMO":
        titulo = "⚠️ AforoAI — AFORO PRÓXIMO A COMPLETARSE"
        detalle = "El espacio se está acercando a su capacidad máxima."
    elif nivel == "COMPLETO":
        titulo = "🔴 AforoAI — AFORO COMPLETO"
        detalle = "El espacio ha alcanzado su capacidad máxima."
    else:
        titulo = "🚨 AforoAI — AFORO EXCEDIDO"
        detalle = f"Se ha superado la capacidad máxima por {personas - capacidad} persona(s)."

    return (
        f"{titulo}\n\n"
        f"{detalle}\n"
        f"Personas: {personas} / {capacidad}\n"
        f"Ocupación: {porcentaje:.2f}%\n"
        f"Estado: {medicion['estado']}\n"
        f"Dispositivo: {device}\n"
        f"Timestamp: {timestamp}"
    )


def enviar_telegram(texto: str) -> None:
    if not telegram_configurado():
        raise RuntimeError("Telegram no configurado: revisa TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": CHAT_ID, "text": texto}, timeout=10)
    response.raise_for_status()


def procesar_alerta(conn: sqlite3.Connection, medicion: dict) -> Optional[str]:
    """Envía solo cuando cambia el nivel de alerta. Retorna nivel enviado o None."""
    if medicion.get("origen") == "SIMULADO" and not NOTIFY_SIMULATED:
        return None
    if not telegram_configurado():
        return None

    nivel = nivel_alerta(medicion["personas"], medicion["capacidad"])
    device = medicion["device_id"]

    conn.execute("""
        CREATE TABLE IF NOT EXISTS estado_alertas (
            device_id TEXT PRIMARY KEY,
            nivel TEXT NOT NULL
        )
    """)
    row = conn.execute("SELECT nivel FROM estado_alertas WHERE device_id=?", (device,)).fetchone()
    anterior = row["nivel"] if row else "NORMAL"

    conn.execute(
        "INSERT INTO estado_alertas(device_id,nivel) VALUES(?,?) "
        "ON CONFLICT(device_id) DO UPDATE SET nivel=excluded.nivel",
        (device, nivel),
    )

    if nivel == "NORMAL" or nivel == anterior:
        return None

    enviar_telegram(_mensaje(nivel, medicion))
    return nivel
