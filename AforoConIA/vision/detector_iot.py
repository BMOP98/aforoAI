"""Visión + IoT: detecta personas localmente y envía solo el conteo a la API."""
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from iot.sender import enviar_medicion

MODEL_NAME = "yolo11n.pt"
CONFIDENCE = 0.45
CAMERA_INDEX = 0
SEND_INTERVAL_SECONDS = 10


def main():
    model = YOLO(MODEL_NAME)
    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("ERROR: No se pudo acceder a la camara.")
        return

    last_sent = 0.0
    print("AforoAI conectado. Q = salir. Se envia una medicion REAL cada 10 segundos.")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            result = model.predict(frame, classes=[0], conf=CONFIDENCE, verbose=False)[0]
            count = len(result.boxes)
            annotated = result.plot()
            cv2.rectangle(annotated, (10, 10), (330, 64), (0, 0, 0), -1)
            cv2.putText(annotated, f"Personas: {count}", (22, 47), cv2.FONT_HERSHEY_SIMPLEX, .9, (255,255,255), 2)

            now = time.monotonic()
            if now - last_sent >= SEND_INTERVAL_SECONDS:
                try:
                    saved = enviar_medicion(count, "REAL")
                    print(f"Medicion enviada: {saved['personas']} personas | {saved['estado']}")
                    last_sent = now
                except Exception as exc:
                    print(f"API no disponible: {exc}")

            cv2.imshow("AforoAI - Vision + IoT", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
