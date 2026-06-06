# Pipeline Completo — De la Cámara a la Acción

## Visión general

Cada frame que produce la cámara recorre exactamente este camino:

```
Cámara (hardware)
    │  30 frames/seg
    ▼
CameraCapture.read()        src/capture.py
    │  frame BGR flippeado
    ▼
cv2.cvtColor(BGR→RGB)       main.py
    │  frame RGB
    ▼
HandDetector.detect()       src/detector.py
    │  DetectionResult (0-2 manos con 21 landmarks cada una)
    ▼
gestures.recognize()        src/gestures.py   ← uno por mano
    │  GestureResult (nombre, confianza, dedos)
    ▼
ActionDispatcher.dispatch() src/actions.py    ← uno por mano
    │  (si debounce lo permite)
    ▼
keyboard / mouse controller src/controllers/
    │  acción real en el sistema operativo
    ▼
Renderer.draw()             src/renderer.py
    │  frame con overlays dibujados
    ▼
cv2.imshow()                main.py
    │
    ▼
    [siguiente frame]
```

---

## Módulo 1 — CameraCapture (`src/capture.py`)

**Responsabilidad:** abrir la cámara, leer frames y calcular FPS.

**Entradas:** configuración de dispositivo, resolución y backend  
**Salida:** frame BGR como `numpy.ndarray` de forma `(720, 1280, 3)`

### Detalles importantes

**Flip horizontal:**
```python
frame = cv2.flip(frame, 1)
```
Se flipea cada frame para que funcione como espejo.
Esto es necesario para que el handedness coincida con la mano visual del usuario.

**FPS real:**
```python
elapsed = now - self._last_frame_time
self._fps = 1.0 / elapsed
```
Se mide el tiempo entre frames consecutivos para calcular el FPS real (no el target).

**Backend de cámara:**
- `dshow` (Windows DirectShow) — más rápido en Windows
- `""` (auto) — deja que OpenCV elija, funciona en macOS/Linux

---

## Módulo 2 — HandDetector (`src/detector.py`)

**Responsabilidad:** envolver MediaPipe Hands y devolver datos estructurados.

**Entradas:** frame RGB como `numpy.ndarray`  
**Salida:** `DetectionResult` con lista de `HandData`

### Configuración relevante

```yaml
mediapipe:
  max_num_hands: 2               # 1 o 2
  min_detection_confidence: 0.75 # palm detector
  min_tracking_confidence: 0.65  # landmark tracker
```

### Qué hace internamente

```python
result = self._hands.process(frame_rgb)
# result.multi_hand_landmarks  → lista de conjuntos de 21 landmarks
# result.multi_handedness      → lista de clasificaciones Left/Right
# result.multi_hand_world_landmarks → landmarks en metros
```

MediaPipe usa una red neuronal para estimar los 21 landmarks en 3D a partir de la imagen 2D.

---

## Módulo 3 — Gestures (`src/gestures.py`)

**Responsabilidad:** convertir 21 landmarks en un nombre de gesto.

**Entradas:** `HandData` (landmarks + handedness)  
**Salida:** `GestureResult` (nombre, confianza, dedos, mano)

**Detalle:** si existe el modelo ML, lo usa. Si no, usa reglas.
Ver `03_reconocimiento_de_gestos.md` para la lógica completa.

---

## Módulo 4 — ActionDispatcher (`src/actions.py`)

**Responsabilidad:** mapear nombre de gesto a acción y ejecutarla con debounce.

**Entradas:** `GestureResult`  
**Salida:** ejecuta acción en el sistema + retorna `(gesture, action)` o `None`

### Cómo lee el mapping

```python
# config/mappings.yaml
gestures:
  victoria: key_press:ctrl+c
  ok:       mouse_click:left
```

Al inicializar, carga todo el YAML en un dict:
```python
self._mappings = {"victoria": "key_press:ctrl+c", "ok": "mouse_click:left", ...}
```

### Parsing de la acción

```python
# "key_press:ctrl+c"  →  action_type="key_press",  payload="ctrl+c"
# "mouse_click:left"  →  action_type="mouse_click", payload="left"
# "none"              →  no hace nada
```

### Debounce

```python
now_ms = time.time() * 1000
last = self._last_dispatch.get(gesture_name, 0.0)
if now_ms - last >= cooldown_ms:      # 800ms por defecto
    self._last_dispatch[gesture_name] = now_ms
    return True   # ejecutar
return False      # todavía en cooldown
```

---

## Módulo 5 — Controllers (`src/controllers/`)

**Responsabilidad:** ejecutar la acción real en el sistema operativo.

### keyboard.py

Usa `pynput.keyboard.Controller` para simular teclas.

```python
# key_press:ctrl+c  →  press(ctrl), press(c), release(c), release(ctrl)
for key in keys[:-1]:      # modificadores (ctrl, alt, shift)
    _controller.press(key)
_controller.press(keys[-1])   # tecla principal
_controller.release(keys[-1])
for key in reversed(keys[:-1]):
    _controller.release(key)
```

### mouse.py

Usa `pynput.mouse.Controller` para clics y scroll.

```python
# mouse_click:left
_controller.click(Button.left, 1)

# mouse_scroll:up:3
_controller.scroll(0, 3)   # (dx, dy) — positivo = arriba
```

**Nota macOS:** pynput necesita permiso de Accesibilidad en
`System Settings → Privacy & Security → Accessibility`.

---

## Módulo 6 — Renderer (`src/renderer.py`)

**Responsabilidad:** dibujar todos los overlays visuales sobre el frame.

**Entradas:** frame BGR, DetectionResult, lista de GestureResult, FPS  
**Salida:** frame BGR con overlays

### Qué dibuja

1. **Skeleton de la mano** — usa `mp.solutions.drawing_utils` para dibujar
   los 21 landmarks y las conexiones entre ellos (los "huesos")

2. **Label del gesto** — texto con el nombre del gesto encima de cada mano,
   posicionado en la esquina superior del bounding box de la mano

3. **FPS counter** — esquina superior izquierda

4. **Action toast** — aparece al centro inferior cuando se ejecuta una acción,
   se desvanece en 1.8 segundos usando `cv2.addWeighted` para la transparencia

5. **Status bar** — barra en la parte inferior con ayuda de teclas

### Alpha blending (transparencia)

Para dibujar fondos semitransparentes:
```python
overlay = frame.copy()
cv2.rectangle(overlay, ...)    # dibuja en la copia
cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
# resultado = overlay * alpha + frame * (1-alpha)
```

Con `alpha=0.55`, el fondo queda al 55% opaco y se transparenta el 45% del frame original.

---

## Loop principal (`main.py`)

El corazón de la app es un `while True` que se ejecuta hasta que el usuario presiona Q:

```python
while True:
    ret, frame = cap.read()             # capturar frame
    rgb = cv2.cvtColor(frame, BGR2RGB)  # convertir para MediaPipe
    detection = detector.detect(rgb)    # detectar manos

    gesture_results = [recognize(hand) for hand in detection.hands]

    if dispatcher:
        for gesture in gesture_results:
            result = dispatcher.dispatch(gesture)  # ejecutar acción
            if result:
                renderer.notify_action(*result)    # mostrar toast

    fps = cap.get_fps()
    output = renderer.draw(frame, detection, gesture_results, fps)
    cv2.imshow("Gesture Control", output)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
```

`cv2.waitKey(1)` espera 1ms entre frames, lo que permite que OpenCV procese eventos de la ventana
(como presionar Q) sin bloquear el loop.
