# La interfaz gráfica (CustomTkinter)

Hasta el commit `5d69989` la "interfaz" era una ventana de OpenCV (`cv2.imshow`)
con texto dibujado a mano sobre el frame (`cv2.putText`). Eso tenía un problema
serio: `cv2.putText` no sabe renderizar UTF-8, así que cualquier acento, la "ñ"
o símbolos como ✓/✗ salían como signos de interrogación. Además la UI era muy
limitada — no había forma de ver el historial de gestos, cambiar de cámara
desde la ventana, o editar los mapeos sin tocar el YAML a mano.

El commit `f631ec4` reemplaza esa ventana por una aplicación de escritorio real
construida con [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
(un wrapper con estética moderna sobre Tkinter).

---

## Estructura de `src/gui/`

| Archivo | Rol |
|---|---|
| `app.py` | `GestureControlApp`, la ventana principal. Arma el layout (video + sidebar), arranca el worker de cámara y hace polling de sus resultados. |
| `worker.py` | `CaptureWorker`: hilo en background que corre `CameraCapture` + `HandDetector` + `recognize()` en loop y publica resultados por una `queue.Queue`. |
| `video_panel.py` | Widget que muestra el frame de video (con el skeleton ya dibujado) escalado al tamaño del panel. |
| `gesture_panel.py` | Muestra el gesto actual: un ícono generado dinámicamente (PIL) + el estado de cada dedo (arriba/abajo). |
| `charts.py` | `FpsHistoryChart`: gráfico en vivo de FPS e historial de gestos reconocidos, con matplotlib embebido en un `CTkFrame`. Se actualiza a 2Hz (throttle) para no saturar el hilo principal. |
| `camera_bar.py` | Dropdown para elegir cámara cuando hay más de una disponible. |
| `mapping_editor.py` | `MappingEditorDialog`: ventana modal para editar `config/mappings.yaml` (gesto → acción) sin reiniciar la app. |
| `icons.py`, `labels.py`, `fonts.py` | Utilidades de soporte: generación de íconos con PIL, textos legibles para gestos/acciones, y una fuente que sí soporta emoji/UTF-8. |

`main.py` es ahora el único punto de entrada de la app (se borraron
`main_enhanced.py`, `src/renderer.py` y `src/ui/gesture_panel.py`, que quedaron
como código muerto tras el reemplazo).

---

## El contrato de threading (por qué existe `worker.py`)

La app tiene dos hilos:

- **Hilo principal (Tk main thread)**: dueño de todos los widgets, el
  `PhotoImage` que se pinta en pantalla, el canvas de matplotlib, y — esto es
  la parte importante — el `ActionDispatcher` (teclado/mouse vía `pynput`).
- **`CaptureWorker`**: un hilo aparte que solo hace captura de cámara +
  MediaPipe + reconocimiento de gestos, y publica los resultados en una
  `queue.Queue` que el hilo principal consume cada 33ms (`_POLL_INTERVAL_MS`,
  ≈30 FPS) vía `self.after(...)`.

Esto no es una decisión de estilo: **se detectó un crash real (SIGTRAP)** al
ejecutar acciones de `pynput` desde el hilo de background. En macOS, el Text
Input Source Manager — que el backend de teclado de `pynput` toca
internamente — solo permite ser invocado desde el hilo principal; si se llama
desde otro hilo, el proceso recibe SIGTRAP y muere.

Por eso `ActionDispatcher` vive y se ejecuta exclusivamente en
`GestureControlApp` (`app.py`), nunca en `CaptureWorker`. El worker solo
produce datos (frame + gestos detectados); quien decide disparar una tecla o
clic es siempre el hilo principal, en `_apply_update()`.

```
CaptureWorker (hilo background)          GestureControlApp (hilo principal)
────────────────────────────────         ──────────────────────────────────
CameraCapture.read()
HandDetector.process()
recognize()                    ──queue──▶  _poll_queue() cada 33ms
                                            _apply_update():
                                              - pinta el frame (VideoPanel)
                                              - actualiza GesturePanel
                                              - alimenta el chart de FPS
                                              - ActionDispatcher.dispatch()
                                                (teclado/mouse — SOLO aquí)
```

La comunicación en el otro sentido (cambiar de cámara, detener el worker) usa
una segunda cola, `cmd_queue`, en `app.py`:`_on_camera_change` /
`_on_close`.

---

## Hot-reload del editor de mapeos

`MappingEditorDialog` permite editar gesto → acción desde la UI y guardar
directo a `config/mappings.yaml`. Al guardar, llama a
`_on_mappings_saved()` en `app.py`, que hace `self._dispatcher.reload()` —
esto vuelve a leer el YAML sin reiniciar la app ni perder la sesión de cámara.
Ese método `reload()` se agregó a `ActionDispatcher` específicamente para
soportar este flujo.

---

## Otros cambios del mismo commit

- Se quitó el gesto **"rock"** de `config/mappings.yaml`: el modelo ML
  entrenado solo tiene 7 clases y nunca podía reconocerlo. Se agregaron
  **"tres"** y **"cuatro"** en su lugar.
- `requirements.txt` suma `customtkinter`, `matplotlib` y `Pillow` como
  dependencias directas de la GUI.
- README y GUIDE se actualizaron para reflejar el nuevo punto de entrada
  (`python main.py`) y las flags (`--camera`, `--no-actions`, `--debug`).

## Cambio menor posterior

En un commit siguiente se normalizó el formato de `config/mappings.yaml`
(se quitó el alineado de columnas con espacios extra, dejando
`clave: valor` simple) — sin cambios funcionales, solo estilo.
