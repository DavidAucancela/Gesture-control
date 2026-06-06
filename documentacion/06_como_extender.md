# Cómo Extender el Sistema

## 1. Cambiar acciones de gestos existentes

El lugar más fácil para modificar es `config/mappings.yaml`.
No hace falta tocar código Python.

```yaml
gestures:
  punio:          key_press:ctrl+z      # deshacer
  mano_abierta:   key_press:space       # pausa/play
  señalar:        mouse_click:left      # click
  victoria:       key_press:ctrl+c      # copiar
  rock:           key_press:ctrl+v      # pegar
  pulgar_arriba:  key_press:volumeup
  pulgar_abajo:   key_press:volumedown
  ok:             mouse_click:left
```

### Ejemplos de acciones útiles

```yaml
# Navegación de slides (PowerPoint / Keynote)
mano_abierta:  key_press:right          # slide siguiente
punio:         key_press:left           # slide anterior
victoria:      key_press:f5             # iniciar presentación

# YouTube / Spotify
mano_abierta:  key_press:space          # pausa/play
pulgar_arriba: key_press:k              # pausa (YouTube)
señalar:       key_press:f              # pantalla completa
rock:          key_press:m              # silenciar

# VS Code
victoria:      key_press:ctrl+shift+p   # command palette
ok:            key_press:ctrl+grave     # abrir terminal

# Combos con modificadores
señalar:       key_press:cmd+tab        # cambiar app (macOS)
```

---

## 2. Agregar un gesto nuevo con reglas

### Paso 1 — Identificar la firma de dedos

Corré la app con `--debug` y mirá qué valor de `fingers_up` tiene el gesto que querés.
O pensá en qué dedos están extendidos:

```
Gesto "pinza" (pulgar + índice): [True, True, False, False, False]
Gesto "llamame" (pulgar + meñique): [True, False, False, False, True]
```

### Paso 2 — Agregar la regla en `src/gestures.py`

Abrir `_recognize_rule_based()` y agregar **antes** del `return "desconocido"` al final:

```python
# Ejemplo: gesto "pinza" — pulgar e índice extendidos
if fingers == [True, True, False, False, False]:
    return "pinza"

# Ejemplo: gesto "llamame" — pulgar y meñique
if fingers == [True, False, False, False, True]:
    return "llamame"
```

### Paso 3 — Mapear en `config/mappings.yaml`

```yaml
gestures:
  pinza:    key_press:ctrl+s      # guardar
  llamame:  key_press:ctrl+z      # deshacer
```

### Paso 4 — Agregar el label display en `src/renderer.py`

Para que el toast muestre un nombre bonito:

```python
_ACTION_LABELS = {
    ...
    "pinza": "Pinza",
    "llamame": "Llamame",
}
```

---

## 3. Agregar un gesto con ML (recomendado)

Con el clasificador ML podés agregar gestos sin tocar reglas.
Solo necesitás datos.

```bash
# 1. Recolectar datos del nuevo gesto
python tools/collect_data.py
# Cuando llegues al nuevo gesto, presioná SPACE 200+ veces variando ángulo

# 2. Reentrenar el modelo
python tools/train.py

# 3. Mapear la acción
# Editar config/mappings.yaml con el nombre exacto del gesto

# 4. Reiniciar la app
python main.py
```

---

## 4. Ajustar sensibilidad

### Hacer que los gestos respondan más rápido/lento

```python
# src/actions.py — línea 12
_DEFAULT_COOLDOWN_MS = 800   # bajar = más rápido (mínimo ~200ms)
                              # subir = más lento/estable
```

O al crear el dispatcher en `main.py`:
```python
dispatcher = ActionDispatcher("config/mappings.yaml", cooldown_ms=400)
```

### Hacer que el detector sea más/menos exigente

```yaml
# config/settings.yaml
mediapipe:
  min_detection_confidence: 0.75  # bajar = detecta más fácil pero más falsos positivos
  min_tracking_confidence: 0.65   # bajar = no pierde la mano tan seguido
```

### Cambiar el umbral del gesto OK

```python
# src/gestures.py — línea 28
_OK_DISTANCE_THRESHOLD = 0.06   # subir = más fácil hacer el OK
                                 # bajar = más preciso, requiere cerrar más
```

---

## 5. Soporte para dos manos

El sistema ya detecta hasta 2 manos simultáneamente (configurado en `settings.yaml`).
El loop en `main.py` ya itera sobre todas las manos detectadas:

```python
gesture_results = [recognize(hand) for hand in detection.hands]
for gesture in gesture_results:
    dispatcher.dispatch(gesture)
```

Lo que falta es distinguir gestos por mano y por combinación.

### Ejemplo: gesto diferente según qué mano

Modificar `ActionDispatcher.dispatch()` para usar `gesture.hand`:

```python
def dispatch(self, gesture: GestureResult):
    # key = "victoria_Right" o "victoria_Left"
    mapping_key = f"{gesture.name}_{gesture.hand}"
    action_str = self._mappings.get(mapping_key) or self._mappings.get(gesture.name, "none")
    ...
```

Y en `mappings.yaml`:
```yaml
gestures:
  victoria_Right: key_press:ctrl+c    # mano derecha: copiar
  victoria_Left:  key_press:ctrl+v    # mano izquierda: pegar
```

### Ejemplo: acción cuando dos manos hacen el mismo gesto

Agregar lógica en `main.py`:

```python
gesture_names = [g.name for g in gesture_results]
if gesture_names.count("mano_abierta") == 2:
    # ambas manos abiertas → acción especial
    press_key("ctrl+shift+s")
```

---

## 6. Control del cursor con la mano

`src/controllers/mouse.py` ya tiene `move_relative(dx, dy)`.
Lo que falta es calcular cuánto moverse basado en la posición de la muñeca.

Idea básica en `main.py`:

```python
prev_wrist_x = None

for hand in detection.hands:
    wrist = hand.landmarks[0]
    if prev_wrist_x is not None and gesture.name == "señalar":
        # mapear movimiento de muñeca a movimiento de cursor
        dx = int((wrist.x - prev_wrist_x) * screen_width * sensitivity)
        dy = int((wrist.y - prev_wrist_y) * screen_height * sensitivity)
        from src.controllers.mouse import move_relative
        move_relative(dx, dy)
    prev_wrist_x = wrist.x
    prev_wrist_y = wrist.y
```

---

## 7. Agregar scroll con movimiento de mano

Similar al cursor, pero usando la velocidad vertical de la palma:

```python
if gesture.name == "mano_abierta":
    wrist_y = hand.landmarks[0].y
    if prev_wrist_y is not None:
        dy = wrist_y - prev_wrist_y
        if abs(dy) > 0.01:  # umbral mínimo de movimiento
            direction = "down" if dy > 0 else "up"
            from src.controllers.mouse import scroll
            scroll(direction, amount=3)
```

---

## 8. Perfiles de mappings por aplicación

Para cambiar el comportamiento según la app activa, necesitás detectar la ventana en foco.

En macOS:
```python
import subprocess

def get_active_app():
    result = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to get name of first application process whose frontmost is true'],
        capture_output=True, text=True
    )
    return result.stdout.strip()
```

Luego en el loop principal, cargar el mapping correspondiente:
```python
app = get_active_app()
mapping_file = f"config/mappings_{app.lower()}.yaml"
if not os.path.exists(mapping_file):
    mapping_file = "config/mappings.yaml"
dispatcher = ActionDispatcher(mapping_file)
```
