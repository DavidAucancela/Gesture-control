# Reconocimiento de Gestos

## El problema

Tenemos 21 puntos (x, y, z) por mano = 63 números por frame.
El objetivo es convertir esos 63 números en un nombre de gesto como "victoria" o "punio".

Hay dos enfoques en este proyecto: **reglas deterministas** y **Machine Learning**.

---

## Enfoque 1 — Sistema de reglas (rule-based)

### La idea central: ¿qué dedos están extendidos?

La observación clave es que la mayoría de los gestos se pueden describir
en términos de qué dedos están levantados y cuáles cerrados.

Se representa como una lista de 5 booleanos:
```
[pulgar, índice, medio, anular, meñique]
True  = extendido
False = doblado
```

### Cómo se determina si un dedo está extendido

**Para dedos 2 al 5 (índice, medio, anular, meñique):**

Se compara la posición Y de la punta con la del nudo PIP.
En coordenadas de imagen, Y crece hacia abajo.
Si la punta está más arriba que el nudo (y menor = más arriba), el dedo está extendido.

```python
# src/gestures.py
fingers.append(lm[_INDEX_TIP].y < lm[_INDEX_PIP].y)   # índice
fingers.append(lm[_MIDDLE_TIP].y < lm[_MIDDLE_PIP].y) # medio
fingers.append(lm[_RING_TIP].y < lm[_RING_PIP].y)     # anular
fingers.append(lm[_PINKY_TIP].y < lm[_PINKY_PIP].y)   # meñique
```

**Para el pulgar:**

El pulgar se mueve lateralmente, no verticalmente.
Se compara la posición X de la punta con la de la articulación IP.
La dirección depende de si es mano derecha o izquierda (post-flip).

```python
if handedness == "Right":
    fingers.append(lm[_THUMB_TIP].x < lm[_THUMB_IP].x)
else:
    fingers.append(lm[_THUMB_TIP].x > lm[_THUMB_IP].x)
```

### Tabla de gestos y sus firmas de dedos

| Gesto | `[pulgar, índice, medio, anular, meñique]` | Lógica adicional |
|---|---|---|
| `punio` | `[F, F, F, F, F]` | todos cerrados |
| `mano_abierta` | `[T, T, T, T, T]` | todos abiertos |
| `señalar` | `[F, T, F, F, F]` | solo índice |
| `victoria` | `[F, T, T, F, F]` | índice y medio |
| `rock` | `[F, T, F, F, T]` | índice y meñique |
| `pulgar_arriba` | `[T, F, F, F, F]` | punta.y < MCP.y |
| `pulgar_abajo` | `[T, F, F, F, F]` | punta.y > CMC.y |
| `ok` | distancia pulgar-índice | < 0.06 + medio/anular/meñique arriba |
| `tres` | `[F, T, T, T, F]` | índice, medio, anular |
| `cuatro` | `[F, T, T, T, T]` | índice, medio, anular, meñique |

### El gesto OK — distancia euclidiana

El gesto OK es especial porque no se puede describir solo con dedos extendidos.
En el OK, el pulgar y el índice forman un círculo tocándose, mientras los otros tres están arriba.

La detección usa **distancia euclidiana** entre la punta del pulgar y la del índice:

```python
_OK_DISTANCE_THRESHOLD = 0.06  # en coordenadas normalizadas

if _distance(lm[_THUMB_TIP], lm[_INDEX_TIP]) < _OK_DISTANCE_THRESHOLD:
    if middle and ring and pinky:
        return "ok"
```

El umbral de 0.06 equivale aproximadamente al 6% del ancho de la imagen,
que es la distancia a la que las puntas se consideran "tocándose".

### Limitaciones del sistema de reglas

- Asume que la mano está más o menos de frente a la cámara
- Gestos con la mano girada o en perfil pueden fallar
- No puede aprender de errores ni adaptarse al usuario
- El gesto OK puede dar falsos positivos si la mano está en ciertos ángulos

---

## Enfoque 2 — Clasificador ML (Random Forest)

### Cuándo se usa

Si existen los archivos `models/gesture_v1.pkl` y `models/label_encoder.pkl`
(generados con `python tools/train.py`), el sistema usa el clasificador ML
en lugar de las reglas. Si no existen, usa reglas automáticamente.

```python
# src/gestures.py — recognize()
try:
    from src.classifier import GestureClassifier
    clf = GestureClassifier.get_instance()
    if clf is not None and clf.is_loaded():
        gesture_name, confidence = clf.predict(lm)
        return GestureResult(name=gesture_name, confidence=confidence, ...)
except ImportError:
    pass

# fallback a reglas
gesture_name = _recognize_rule_based(lm, fingers)
```

### Feature extraction (preparación de datos)

Antes de pasarle los landmarks al modelo, se normalizan **restando la posición de la muñeca**:

```python
# src/classifier.py
wrist = landmarks[0]
features = []
for lm in landmarks:
    features.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
```

Esto hace que el gesto sea **invariante a la posición en pantalla**.
Un "señalar" a la izquierda de la pantalla y uno a la derecha producen los mismos features.

Resultado: vector de `21 × 3 = 63 floats` por muestra.

### Por qué Random Forest

- Funciona bien con features numéricos continuos
- No necesita normalización de escala
- Rápido para inferencia en tiempo real
- Produce probabilidades por clase (se puede ver la confianza)
- No requiere GPU

---

## El flujo completo de reconocimiento

```
Frame RGB
    │
    ▼
HandDetector.detect()
    │  devuelve HandData con 21 landmarks
    ▼
gestures.recognize()
    │
    ├──► ¿Existe modelo ML?
    │         │
    │    Sí   │   No
    │         │    │
    │         ▼    ▼
    │    classifier  _recognize_rule_based()
    │    .predict()
    │
    ▼
GestureResult(name, confidence, fingers_up, hand)
```

### El objeto GestureResult

```python
@dataclass
class GestureResult:
    name: str           # "victoria", "punio", "ok", etc. — o "desconocido"
    confidence: float   # 0.0-1.0 (reglas siempre devuelven 1.0, ML devuelve prob real)
    fingers_up: list[bool]  # [pulgar, índice, medio, anular, meñique]
    hand: str           # "Right" o "Left"
```

---

## Debounce — evitar acciones repetidas

Cuando mantenés un gesto durante varios frames, el dispatcher lo recibiría 30 veces por segundo.
Eso causaría que se ejecute la acción 30 veces por segundo (muy molesto para volumen o clicks).

La solución es **debounce**: solo se ejecuta la acción si pasó suficiente tiempo desde la última.

```python
# src/actions.py
_DEFAULT_COOLDOWN_MS = 800  # 0.8 segundos entre disparos del mismo gesto
```

Si necesitás que los gestos respondan más rápido o más lento, podés cambiar este valor.
