# MediaPipe y Landmarks de Mano

## ¿Qué es MediaPipe?

MediaPipe es una librería de Google para procesar video y audio en tiempo real.
Incluye modelos pre-entrenados para detectar caras, manos, cuerpos, poses, y más.

En este proyecto usamos **MediaPipe Hands**, que:
1. Detecta si hay manos en el frame
2. Localiza 21 puntos clave (landmarks) por cada mano
3. Determina si la mano es derecha o izquierda
4. Todo en tiempo real (~30 FPS en CPU)

---

## Cómo funciona MediaPipe Hands internamente

MediaPipe Hands usa una **pipeline de dos etapas**:

### Etapa 1 — Detección (palm detector)

Un modelo liviano de detección de palmas analiza el frame completo y devuelve
el bounding box (rectángulo) de cada palma encontrada.

Este modelo solo se ejecuta cuando:
- No hay manos trackeadas aún
- El tracking de una mano se pierde

Parámetro que controla su sensibilidad:
```yaml
# config/settings.yaml
mediapipe:
  min_detection_confidence: 0.75
```

### Etapa 2 — Landmark regression

Para cada palma detectada, un segundo modelo más preciso analiza el recorte
de esa región y predice la posición de los 21 landmarks en 3D.

Este modelo se ejecuta en **todos los frames** mientras hay una mano.
El tracking hace que no sea necesario re-detectar desde cero cada frame.

Parámetro:
```yaml
min_tracking_confidence: 0.65
```

Si la confianza de tracking cae por debajo de este umbral (mano muy rápida,
oclusión parcial, etc.), vuelve a ejecutar la detección completa.

---

## Los 21 landmarks

Cada mano tiene exactamente 21 landmarks numerados del 0 al 20:

```
                  8   12  16  20
                  |   |   |   |
                  7   11  15  19
              4   |   |   |   |
              |   6   10  14  18
              3   |   |   |   |
              |   5---9--13--17
              2  /
              | /
              1/
              |
              0  ← WRIST (muñeca)
```

### Tabla completa de landmarks

| Índice | Nombre | Descripción |
|---|---|---|
| 0 | WRIST | Muñeca |
| 1 | THUMB_CMC | Pulgar — articulación carpometacarpiana |
| 2 | THUMB_MCP | Pulgar — nudillo base |
| 3 | THUMB_IP | Pulgar — articulación intermedia |
| 4 | THUMB_TIP | Pulgar — punta |
| 5 | INDEX_MCP | Índice — nudillo base |
| 6 | INDEX_PIP | Índice — articulación proximal |
| 7 | INDEX_DIP | Índice — articulación distal |
| 8 | INDEX_TIP | Índice — punta |
| 9 | MIDDLE_MCP | Medio — nudillo base |
| 10 | MIDDLE_PIP | Medio — articulación proximal |
| 11 | MIDDLE_DIP | Medio — articulación distal |
| 12 | MIDDLE_TIP | Medio — punta |
| 13 | RING_MCP | Anular — nudillo base |
| 14 | RING_PIP | Anular — articulación proximal |
| 15 | RING_DIP | Anular — articulación distal |
| 16 | RING_TIP | Anular — punta |
| 17 | PINKY_MCP | Meñique — nudillo base |
| 18 | PINKY_PIP | Meñique — articulación proximal |
| 19 | PINKY_DIP | Meñique — articulación distal |
| 20 | PINKY_TIP | Meñique — punta |

### Terminología articular

- **MCP** (Metacarpophalangeal) — el nudillo donde el dedo se une a la palma
- **PIP** (Proximal Interphalangeal) — el primer nudo del dedo (más cerca de la palma)
- **DIP** (Distal Interphalangeal) — el segundo nudo (más cerca de la punta)
- **TIP** — la punta del dedo
- **CMC** (Carpometacarpal) — solo el pulgar, donde el metacarpo se une al carpo
- **IP** (Interphalangeal) — solo el pulgar, el único nudo que tiene

---

## Estructura de los datos que devuelve el detector

El `HandDetector` en `src/detector.py` envuelve MediaPipe y devuelve datos estructurados:

```python
@dataclass
class HandData:
    landmarks: list        # 21 NormalizedLandmark (x, y, z en [0,1])
    handedness: str        # 'Right' o 'Left'
    world_landmarks: list  # 21 landmarks en coordenadas métricas 3D (metros)

@dataclass
class DetectionResult:
    hands: list[HandData]  # 0, 1 o 2 manos
    raw_result: Any        # resultado crudo de MediaPipe (para dibujar el skeleton)
```

### Diferencia entre landmarks normalizados y world landmarks

**Normalized landmarks** (`landmarks`):
- `x`, `y` en [0, 1] relativo al frame
- `z` relativo a la profundidad de la muñeca (sin unidades absolutas)
- Cambian si la mano se mueve por la pantalla
- Usados para reconocimiento de gestos y dibujo

**World landmarks** (`world_landmarks`):
- Coordenadas en metros, centradas en la muñeca
- No cambian si la mano se mueve por la pantalla (solo cambian si cambia la pose)
- Útiles para medir ángulos articulares reales
- En este proyecto no se usan actualmente, pero están disponibles

---

## Handedness: izquierda vs derecha

MediaPipe devuelve el handedness **desde la perspectiva de la persona**,
considerando que la imagen ya fue flippeada (modo espejo).

Esto es importante para el pulgar: la lógica de "pulgar extendido" es diferente
para mano izquierda y derecha porque el pulgar apunta en direcciones opuestas.

```python
# src/gestures.py
if handedness == "Right":
    fingers.append(lm[_THUMB_TIP].x < lm[_THUMB_IP].x)  # pulgar apunta a la izquierda
else:
    fingers.append(lm[_THUMB_TIP].x > lm[_THUMB_IP].x)  # pulgar apunta a la derecha
```

---

## Parámetros de configuración

En `config/settings.yaml`:

```yaml
mediapipe:
  max_num_hands: 2          # máximo de manos a detectar simultáneamente
  min_detection_confidence: 0.75   # umbral para el palm detector (0.0-1.0)
  min_tracking_confidence: 0.65    # umbral para mantener el tracking (0.0-1.0)
  static_image_mode: false  # false = modo video (tracking), true = imagen estática
```

**Consejos de ajuste:**
- Subir `min_detection_confidence` → menos detecciones falsas, pero puede perder la mano más seguido
- Bajar `min_tracking_confidence` → mantiene el tracking más tiempo, pero puede haber más "drift"
- `max_num_hands: 1` → más rápido si solo necesitás una mano
