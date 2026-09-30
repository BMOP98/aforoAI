"""AforoAI - detección local de personas con YOLO.

Procesa la webcam localmente. No almacena ni transmite imágenes.
"""
from pathlib import Path
import cv2
from ultralytics import YOLO

MODEL_NAME = "yolo11n.pt"
CONFIDENCE = 0.45
CAMERA_INDEX = 0
WINDOW_NAME = "AforoAI - Deteccion de personas"


def main() -> None:
    print("AforoAI - iniciando modelo de vision...")
    print("La primera ejecucion puede descargar automaticamente el modelo YOLO.")

    model = YOLO(MODEL_NAME)
    camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        print("ERROR: No se pudo acceder a la camara.")
        return

    print("Camara lista. Presiona Q para cerrar.")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("ERROR: No se pudo obtener una imagen de la camara.")
                break

            results = model.predict(
                source=frame,
                classes=[0],  # COCO: 0 = person
                conf=CONFIDENCE,
                verbose=False,
            )

            result = results[0]
            person_count = len(result.boxes)
            annotated = result.plot()

            cv2.rectangle(annotated, (10, 10), (300, 62), (0, 0, 0), -1)
            cv2.putText(
                annotated,
                f"Personas: {person_count}",
                (22, 46),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(WINDOW_NAME, annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("AforoAI finalizado correctamente.")


if __name__ == "__main__":
    main()
