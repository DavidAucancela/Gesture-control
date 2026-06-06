# gesture-control

Real-time hand gesture detection and system control via webcam.

Recognizes hand gestures (fist, open hand, point, victory, OK, rock, thumbs up/down, etc.)
and maps them to configurable actions: keyboard shortcuts, mouse clicks, or custom callbacks.

## Supported gestures

| Gesture | Name | Default action |
|---|---|---|
| Fist | `punio` | none |
| Open hand | `mano_abierta` | Space key |
| Point | `señalar` | none |
| Victory | `victoria` | Ctrl+C |
| Rock | `rock` | Ctrl+Z |
| Thumbs up | `pulgar_arriba` | Volume up |
| Thumbs down | `pulgar_abajo` | Volume down |
| OK | `ok` | Mouse left click |

## Requirements

- Python 3.11+
- Windows 10/11 (also works on macOS and Linux)
- Webcam (built-in or USB)

## Installation

### Windows

```bat
git clone <repo-url>
cd gesture-control
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS

```bash
git clone <repo-url>
cd gesture-control
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **macOS — Accessibility permissions required:**
> For keyboard/mouse actions to work, go to
> `System Settings → Privacy & Security → Accessibility`
> and add your terminal app (Terminal, iTerm2, etc.).
> Without this, gestures are detected and the toast appears, but no actions are triggered.

> **mediapipe version:** must be exactly `==0.10.9`. Newer versions removed `mp.solutions`.

## Quick start

```bat
python main.py
```

Options:

```bat
python main.py --camera 1       # use camera index 1
python main.py --no-actions     # detection only, no keyboard/mouse
python main.py --debug          # show wrist coordinate overlay
```

Press **Q** to quit.

> **Camera not detected?** Try `--camera 1` or change `device_id` in `config/settings.yaml`.
> If the image is slow to start, the `backend: dshow` setting (already default) uses Windows
> DirectShow for fastest initialization.

## Configure mappings

Edit `config/mappings.yaml`:

```yaml
gestures:
  victoria:   key_press:ctrl+c   # copy
  rock:       key_press:ctrl+z   # undo
  señalar:    mouse_click:left   # left click
  punio:      none               # no action
```

Available action types:

| Type | Example |
|---|---|
| `key_press:combo` | `key_press:ctrl+shift+t` |
| `mouse_click:button` | `mouse_click:right` |
| `mouse_scroll:dir:n` | `mouse_scroll:up:5` |
| `none` | `none` |

Special key names: `space`, `enter`, `esc`, `tab`, `backspace`, `delete`,
`ctrl`, `alt`, `shift`, `win`, `up`, `down`, `left`, `right`,
`volumeup`, `volumedown`, `volumemute`, `media_play`, `media_next`, `media_prev`,
`f1`–`f12`, `home`, `end`, `page_up`, `page_down`, `print_screen`.

## Train your own classifier (Phase 3)

### 1. Collect data

```bat
python tools/collect_data.py
```

- `SPACE` — record a sample for the current gesture
- `N` — advance to the next gesture
- `Q` — save and quit

Collected data is saved to `data/raw/<gesture>.csv`.
Aim for >= 200 samples per gesture.

### 2. Train

```bat
python tools/train.py
```

Output: `models/gesture_v1.pkl` and `models/label_encoder.pkl`.

Once the model files exist, `main.py` automatically uses the ML classifier
instead of the rule-based system.

## Project structure

```
gesture-control/
├── src/
│   ├── capture.py        # Webcam capture (mirror mode, FPS tracking)
│   ├── detector.py       # MediaPipe Hands wrapper
│   ├── gestures.py       # Rule-based + ML gesture recognition
│   ├── renderer.py       # Visual overlay (skeleton, labels, FPS)
│   ├── actions.py        # Gesture -> action dispatcher with debounce
│   ├── classifier.py     # ML classifier wrapper (optional)
│   └── controllers/
│       ├── keyboard.py   # pynput keyboard wrapper
│       └── mouse.py      # pynput mouse wrapper
├── config/
│   ├── settings.yaml     # Camera, MediaPipe, renderer settings
│   └── mappings.yaml     # Gesture -> action mappings
├── tests/
│   ├── test_gestures.py  # Gesture recognition unit tests
│   └── test_actions.py   # Dispatcher unit tests
├── tools/
│   ├── collect_data.py   # Interactive data collection
│   └── train.py          # Model training script
├── models/               # Trained model artifacts
├── main.py               # Entry point
└── requirements.txt
```

## Adding a new gesture

1. **Add the rule** in `src/gestures.py` inside `_recognize_rule_based()`:
   ```python
   if fingers == [False, True, False, True, False]:
       return "mi_gesto"
   ```

2. **Map an action** in `config/mappings.yaml`:
   ```yaml
   mi_gesto: key_press:ctrl+v
   ```

3. **(Optional) Collect ML data** using `tools/collect_data.py` and retrain.

4. **Add a test** in `tests/test_gestures.py`:
   ```python
   def test_mi_gesto():
       lms = _make_default_landmarks()
       # extend the right fingers ...
       result = recognize(_make_hand(lms))
       assert result.name == "mi_gesto"
   ```
