# Visión por Computadora — Conceptos Base

## ¿Qué es la visión por computadora?

La visión por computadora (Computer Vision) es el campo de la inteligencia artificial
que enseña a las máquinas a interpretar y entender imágenes y video.
En lugar de ver "una foto de una mano", la computadora ve una grilla de números
y aprende a extraer información útil de esos números.

---

## Cómo funciona una cámara digital

Una cámara digital captura luz a través de un sensor formado por millones de celdas fotosensibles.
Cada celda mide la intensidad de la luz en ese punto y produce un número.

El resultado es una **imagen digital**: una grilla rectangular de valores numéricos.

```
[...] [241] [238] [201] [...]
[...] [200] [185] [170] [...]
[...] [160] [142] [130] [...]
```

Cada celda de la grilla se llama **píxel** (picture element).

---

## Píxeles y canales de color

Una imagen en color no tiene un solo valor por píxel sino **tres** (un canal por color):

- **R** — Red (rojo)
- **G** — Green (verde)
- **B** — Blue (azul)

Cada canal tiene valores de 0 a 255. La combinación de los tres define el color del píxel.

```
Píxel blanco:  R=255, G=255, B=255
Píxel negro:   R=0,   G=0,   B=0
Píxel rojo:    R=255, G=0,   B=0
Píxel piel:    R=220, G=180, B=140  (aproximado)
```

Una imagen de 1280×720 con 3 canales ocupa `1280 × 720 × 3 = 2.764.800 bytes` (~2.6 MB) por frame.

---

## BGR vs RGB

OpenCV (la librería que usamos para la cámara) almacena los canales en orden **BGR** en vez de RGB.
Esto es una decisión histórica de la librería.

MediaPipe, en cambio, espera imágenes en orden **RGB**.

Por eso en el código hay una conversión explícita antes de enviar el frame al detector:

```python
# src/main.py — línea 107
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
detection = detector.detect(rgb)
```

Si no se hace esta conversión, los colores quedan invertidos y MediaPipe detecta mal.

---

## Frames y video

Un video es simplemente una secuencia de imágenes mostradas a alta velocidad.
La tasa de imágenes por segundo se llama **FPS** (frames per second).

- 24 FPS → cine
- 30 FPS → video estándar
- 60 FPS → video fluido

En este proyecto, la cámara captura a 30 FPS en resolución 1280×720.
Cada frame pasa por todo el pipeline de detección y acción en tiempo real.

```
Frame 1 → detectar → reconocer → actuar → mostrar
Frame 2 → detectar → reconocer → actuar → mostrar
...
30 veces por segundo
```

Si el procesamiento de un frame tarda más de 33ms (1/30 segundo),
el FPS baja y la app se siente lenta.

---

## Mirror mode (espejo)

Las webcams capturan la imagen "al derecho" desde la perspectiva de la cámara,
pero eso significa que si levantás la mano derecha, en pantalla aparece a la izquierda.
Esto es desorientador para el usuario.

La solución es **flippear horizontalmente** cada frame:

```python
# src/capture.py — línea 83
frame = cv2.flip(frame, 1)
```

El `1` significa flip horizontal (eje Y). Después del flip, la imagen funciona como un espejo:
lo que está a tu derecha aparece a la derecha en pantalla.

Esto también afecta la detección del pulgar: el código en `gestures.py` tiene en cuenta
el handedness (izquierda/derecha) para determinar en qué dirección apunta el pulgar.

---

## Coordenadas normalizadas

MediaPipe no trabaja con píxeles absolutos sino con **coordenadas normalizadas** en el rango [0, 1]:

- `x = 0.0` → borde izquierdo de la imagen
- `x = 1.0` → borde derecho
- `y = 0.0` → borde superior
- `y = 1.0` → borde inferior
- `z` → profundidad relativa a la muñeca (negativo = más cerca de la cámara)

La ventaja es que estas coordenadas son independientes de la resolución.
Un gesto detectado en 640×480 y uno en 1920×1080 producen los mismos valores `x`, `y`.

Para convertir a píxeles reales cuando se necesita dibujar:

```python
# src/renderer.py
xs = [lm.x * w for lm in hand_lm.landmark]
ys = [lm.y * h for lm in hand_lm.landmark]
```
