# Guía completa — Gesture Control

## Cómo correr la app

```bash
cd "/Users/david/Documents/Projects/Computer visio/app1"
source venv/bin/activate
python main.py
```

Opciones disponibles:

| Flag | Efecto |
|---|---|
| `--camera 1` | Usa cámara con índice 1 (si la default no anda) |
| `--no-actions` | Solo detecta, no ejecuta teclado/mouse |
| `--debug` | Muestra coordenadas de muñeca en pantalla |

---

## Gestos actuales

| Gesto | Acción |
|---|---|
| Mano abierta | `Space` |
| Victoria ✌️ | `Ctrl+C` |
| Rock 🤘 | `Ctrl+Z` (deshacer) |
| Pulgar arriba 👍 | Subir volumen |
| Pulgar abajo 👇 | Bajar volumen |
| OK 👌 | Click izquierdo del mouse |
| Puño | sin acción |
| Señalar | sin acción |

---

## Cambiar qué hace cada gesto

Editar `config/mappings.yaml`:

```yaml
gestures:
  victoria:       key_press:ctrl+v    # pegar en vez de copiar
  señalar:        mouse_click:left    # señalar = click
  punio:          key_press:ctrl+z    # puño = deshacer
  mano_abierta:   mouse_scroll:up:3   # scroll arriba
```

### Tipos de acciones disponibles

| Tipo | Ejemplo | Descripción |
|---|---|---|
| `key_press:combo` | `key_press:ctrl+shift+t` | Presiona y suelta |
| `mouse_click:botón` | `mouse_click:right` | `left`, `right`, `middle` |
| `mouse_scroll:dir:n` | `mouse_scroll:up:5` | `up`/`down`, n = pasos |
| `none` | `none` | Sin acción |

### Teclas especiales disponibles

`space`, `enter`, `esc`, `tab`, `backspace`, `delete`,
`ctrl`, `alt`, `shift`, `cmd`, `up`, `down`, `left`, `right`,
`volumeup`, `volumedown`, `volumemute`,
`media_play`, `media_next`, `media_prev`,
`f1`–`f12`, `home`, `end`, `page_up`, `page_down`, `caps_lock`

---

## Agregar un gesto nuevo (regla manual)

### 1. Entender el sistema de dedos

MediaPipe devuelve 21 landmarks por mano. El código usa una lista de 5 bools
`[pulgar, índice, medio, anular, meñique]` donde `True` = dedo extendido.

### 2. Agregar la regla en `src/gestures.py`

Abrir `_recognize_rule_based()` y agregar antes del `return "desconocido"`:

```python
# Ejemplo: índice y meñique extendidos, resto cerrado = "cuernos"
if fingers == [False, True, False, False, True]:
    return "cuernos"
```

### 3. Mapear la acción en `config/mappings.yaml`

```yaml
gestures:
  cuernos: key_press:ctrl+shift+t
```

### 4. Agregar test en `tests/test_gestures.py`

```python
def test_cuernos():
    lms = _make_default_landmarks()
    # extender índice y meñique ...
    result = recognize(_make_hand(lms))
    assert result.name == "cuernos"
```

---

## Siguiente nivel: entrenar tu propio clasificador ML

El sistema rule-based funciona bien pero puede confundirse con gestos similares.
El clasificador ML (Random Forest) aprende de tus propios movimientos y es más preciso.

### Paso 1 — Recolectar datos

```bash
python tools/collect_data.py
```

Controles durante la recolección:
- `SPACE` — grabar muestra del gesto actual
- `N` — avanzar al siguiente gesto
- `Q` — guardar y salir

**Recomendación:** al menos 200 muestras por gesto, variando ángulo y distancia a la cámara.

Los datos se guardan en `data/raw/<gesto>.csv`.

### Paso 2 — Entrenar

```bash
python tools/train.py
```

Genera `models/gesture_v1.pkl` y `models/label_encoder.pkl`.
Una vez que existen esos archivos, `main.py` los usa automáticamente.

### Paso 3 — Evaluar

El script imprime accuracy y una matriz de confusión. Si un gesto tiene < 85% accuracy,
recolectá más muestras o ajustá la regla de ese gesto.

---

## Ideas para lo que sigue

### Corto plazo (fácil)
- **Cambiar mappings** para tus shortcuts favoritos (Figma, VS Code, YouTube, Spotify)
- **Agregar `señalar` como click** — es el gesto más natural para navegar
- **Silencio con puño** — mapear `punio: key_press:volumemute`

### Mediano plazo
- **Gestos con dos manos** — el detector ya soporta `max_hands=2`, falta lógica en `gestures.py`
- **Scroll con mano abierta** — detectar si la mano se mueve arriba/abajo y hacer scroll
- **Modo presentación** — gesto anterior/siguiente slide con swipe

### Largo plazo
- **Entrenamiento ML personalizado** — gestos únicos tuyos con alta precisión
- **Perfiles por app** — cambiar mappings automáticamente según la ventana activa
- **Cursor control** — mover el mouse con la posición de la mano (ya tiene acceso al mouse)

---

## Archivos clave

```
config/
  mappings.yaml     ← acá se cambian los gestos
  settings.yaml     ← cámara, sensibilidad, UI

src/
  gestures.py       ← lógica de reconocimiento (agregar gestos acá)
  actions.py        ← dispatcher gesto → acción
  renderer.py       ← todo lo visual (landmarks, toast, FPS)
  controllers/
    keyboard.py     ← wrapper de teclado
    mouse.py        ← wrapper de mouse

tools/
  collect_data.py   ← recolectar datos para ML
  train.py          ← entrenar modelo
```
