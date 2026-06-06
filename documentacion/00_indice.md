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
ActionDispatcher       ← mapea nombre de gesto a acción, aplica debounce
  │
  ▼
keyboard / mouse       ← pynput ejecuta la acción real en el sistema operativo
  │
  ▼
Renderer               ← dibuja skeleton, label, FPS y toast sobre el frame
  │
  ▼
cv2.imshow()           ← muestra la ventana al usuario
```

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
