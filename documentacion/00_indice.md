# Documentación — Gesture Control

Índice de todos los documentos de este proyecto.

---

## Archivos

| Archivo | Contenido |
|---|---|
| `01_vision_por_computadora.md` | Qué es la visión por computadora, cómo funciona una cámara, frames, píxeles y espacios de color |
| `02_mediapipe_y_landmarks.md` | Qué es MediaPipe, cómo detecta manos, los 21 puntos de landmark y cómo se usan |
| `03_reconocimiento_de_gestos.md` | Cómo se traduce un landmark a un gesto: sistema de dedos, reglas y umbrales |
| `04_pipeline_completo.md` | El flujo completo de datos desde la cámara hasta la acción del sistema, módulo por módulo |
| `05_machine_learning.md` | Cómo funciona el clasificador Random Forest, entrenamiento, features, y cuándo usarlo |
| `06_como_extender.md` | Guía práctica para agregar gestos, cambiar acciones y ajustar parámetros |
| `07_interfaz_grafica.md` | La app de escritorio CustomTkinter: estructura de `src/gui/`, el contrato de threading (por qué pynput vive en el hilo principal), y el editor de mapeos con hot-reload |

---

## Mapa conceptual del sistema

```
Cámara
  │
  ▼
CameraCapture          ← captura frames BGR, los flippea horizontalmente
  │
  ▼
HandDetector           ← MediaPipe detecta hasta 2 manos, devuelve 21 landmarks por mano
  │
  ▼
recognize()            ← convierte landmarks en nombre de gesto (reglas o ML)
  │
  ▼
CaptureWorker          ← publica frame + gestos en una queue (hilo background)
  │
  ▼
GestureControlApp      ← consume la queue cada 33ms (hilo principal Tk)
  │
  ├─▶ VideoPanel / GesturePanel / FpsHistoryChart   (pintan la UI)
  │
  ▼
ActionDispatcher       ← mapea gesto a acción, aplica debounce
  │
  ▼
keyboard / mouse       ← pynput ejecuta la acción real (SOLO en el hilo principal)
```

Ver `07_interfaz_grafica.md` para el detalle de por qué `ActionDispatcher`
debe correr en el hilo principal y no en `CaptureWorker`.

---

## Stack tecnológico

| Librería | Versión | Rol |
|---|---|---|
| OpenCV (`cv2`) | >= 4.9 | Captura de cámara, procesamiento de imagen, UI |
| MediaPipe | 0.10.9 | Detección y tracking de manos |
| pynput | >= 1.7 | Control de teclado y mouse |
| scikit-learn | >= 1.4 | Clasificador Random Forest para ML |
| numpy | >= 1.26 | Álgebra lineal, arrays |
| PyYAML | >= 6.0 | Carga de configuración |
| pandas | — | Solo usado en `tools/train.py` para procesar CSV |
| CustomTkinter | >= 5.2 | Ventana principal de la app de escritorio (`src/gui/`) |
| matplotlib | >= 3.8 | Gráfico en vivo de FPS/gestos, embebido en la sidebar |
| Pillow (PIL) | >= 10.0 | Conversión de frames a `PhotoImage` y generación de íconos de gesto |
