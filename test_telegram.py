from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.telegram_notifier import enviar_telegram

if __name__ == "__main__":
    enviar_telegram(
        "✅ AforoAI — Prueba de Telegram\n\n"
        "La integración de alertas está configurada correctamente."
    )
    print("OK: mensaje de prueba enviado a Telegram.")
