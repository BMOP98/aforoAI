import cv2


def main():
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: No se pudo acceder a la cámara.")
        return

    print("Cámara detectada correctamente.")
    print("Presiona Q para cerrar.")

    while True:
        success, frame = camera.read()

        if not success:
            print("ERROR: No se pudo obtener una imagen de la cámara.")
            break

        cv2.imshow("AforoAI - Prueba de camara", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("Cámara cerrada correctamente.")


if __name__ == "__main__":
    main()