# AforoAI

Prototipo universitario para deteccion y conteo local de personas.

## Fase actual: vision artificial local

La webcam se procesa localmente con YOLO. Solo se detecta la clase `person` y no se guardan imagenes.

### Windows / PowerShell

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python vision/detector.py
```

En la primera ejecucion Ultralytics puede descargar automaticamente `yolo11n.pt`.
Presiona `Q` en la ventana de video para finalizar.

La prueba basica de webcam sigue disponible:

```powershell
python vision/test_camera.py
```
