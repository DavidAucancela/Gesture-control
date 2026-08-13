# UI Layout - Visual Guide

## Full Screen Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Gesture Control — Enhanced                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                    ┌─────────────────┤
│                                                    │ Camera: Laptop  │
│                                                    │ Hands: 1/2      │
│                                                    │                 │
│                    VIDEO FEED                      │ Gestures:       │
│                    (from camera)                   │   R: Mano Abie  │
│                                                    │   Fingers:      │
│                  ┌──────────────────┐              │   ✓ ✓ ✓ ✓ ✓    │
│                  │  ╭─────╮         │              │                 │
│                  │  │ ◯ ◯ │  Hand   │              │ Stats:          │
│                  │  │  ▼  │ Skeleton│              │  FPS: 28.5     │
│                  │  ╰─────╯         │              │  Last: victoria │
│                  └──────────────────┘              │                 │
│                                                    └─────────────────┤
│                                                                      │
│                      FPS: 28.5                                       │
│                                                                      │
│  Toast Notification (when action triggered):                        │
│     ┌──────────────────────────────────────┐                       │
│     │  Mano Abierta  →  SPACE             │                       │
│     └──────────────────────────────────────┘                       │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Q: salir  |  R: resetear  |  C: cambiar cámara  |  I: info         │
└─────────────────────────────────────────────────────────────────────┘
```

## Info Panel (Derecha) - Detalle

### Panel Colapsado (Cuando hay 1 mano)
```
┌─────────────────┐
│ Camera: Laptop  │
│ Hands: 1/2      │
│                 │
│ Gestures:       │
│   R: Señalar    │
│   Fingers:      │
│   ✗ ✓ ✗ ✗ ✗    │
│                 │
│ Stats:          │
│  FPS: 28.5      │
│  Last: victoria │
└─────────────────┘
```

### Panel Expandido (Con 2 manos)
```
┌─────────────────┐
│ Camera: Phone   │
│ Hands: 2/2      │
│                 │
│ Gestures:       │
│   R: OK         │
│   Fingers:      │
│   ✓ ✓ ✓ ✓ ✓    │
│                 │
│   L: Victoria   │
│   Fingers:      │
│   ✗ ✓ ✓ ✗ ✗    │
│                 │
│ Stats:          │
│  FPS: 30.0      │
│  Last: rock     │
└─────────────────┘
```

## Finger States Legend

```
Símbolo  | Significado      | Dedo
---------|------------------|--------
✓        | Extendido/Abierto| Arriba
✗        | Plegado/Cerrado  | Abajo
(space)  | No detectado     | -

Posición: T I M R P
         (Thumb, Index, Middle, Ring, Pinky)

Ejemplo: ✓ ✓ ✗ ✗ ✗
         (Thumb + Index extendidos = Señalar)
```

## State Transitions

### Cambio de Cámara (Tecla C)

```
Before:                          After (300-500ms):
┌─────────────────┐              ┌─────────────────┐
│ Camera: Laptop  │              │ Camera: Phone   │
│ Hands: 1/2      │   ──[C]──>  │ Hands: 1/2      │
│ R: Señalar      │              │ R: Señalar      │
│ ✗ ✓ ✗ ✗ ✗      │              │ ✗ ✓ ✗ ✗ ✗      │
└─────────────────┘              └─────────────────┘
```

### Reconocimiento de Gesto

```
No gesture:
┌─────────────────┐
│ Camera: Laptop  │
│ Hands: 0/2      │
│ (empty)         │
│ Stats:          │
│  FPS: 28.5      │
│  Last: (none)   │
└─────────────────┘

                    ↓ [Hand enters frame] ↓

Detection:
┌─────────────────┐
│ Camera: Laptop  │
│ Hands: 1/2      │
│ R: Detectando...│
│ Stats:          │
│  FPS: 28.5      │
│  Last: (none)   │
└─────────────────┘

                    ↓ [Gesture recognized] ↓

Recognized:
┌─────────────────┐
│ Camera: Laptop  │
│ Hands: 1/2      │
│ R: Mano Abierta │
│ ✓ ✓ ✓ ✓ ✓      │
│ Stats:          │
│  FPS: 28.5      │
│  Last: victoria │
└─────────────────┘
```

## Toast Notification

### Appearance
```
When action is dispatched:

    ┌──────────────────────────────────┐
    │                                  │
    │   Mano Abierta  →  SPACE        │
    │                                  │
    └──────────────────────────────────┘

Duration: 1.8 seconds
Fade-out: Last 0.5 seconds
Position: Center, above status bar
```

### Examples

```
Gesture Detected          Action Sent
──────────────────────────────────────

Mano Abierta              SPACE
    ↓                       ↓
  ┌──────────────────────────────┐
  │ Mano Abierta  →  SPACE      │
  └──────────────────────────────┘


Señalar                   Click Left
    ↓                       ↓
  ┌──────────────────────────────┐
  │ Señalar  →  Click Left       │
  └──────────────────────────────┘


Victoria                  Ctrl+C
    ↓                       ↓
  ┌──────────────────────────────┐
  │ Victoria  →  CTRL+C         │
  └──────────────────────────────┘
```

## Status Bar

### Layout
```
┌─────────────────────────────────────────────────────────────────────┐
│ Q: salir  |  R: resetear  |  C: cambiar cámara  |  I: info         │
└─────────────────────────────────────────────────────────────────────┘
```

### After Pressing C
```
La cámara cambia del índice 0 → 1:

Before:                    After:
┌────────────────────┐    ┌────────────────────┐
│ Camera: Laptop     │    │ Camera: USB Camera │
│ (Cámara 0)         │    │ (Cámara 1)         │
└────────────────────┘    └────────────────────┘
```

## Responsive Elements

### FPS Indicator
```
High FPS (Good):           Low FPS (Warning):
FPS: 30.0                  FPS: 12.3
Color: Green               Color: Yellow (future)
```

### Hand Detection
```
0 Hands:                1 Hand:                2 Hands:
Hands: 0/2              Hands: 1/2             Hands: 2/2
(gray)                  (white)                (bright)
```

### Gesture Confidence
```
Panel shows:
✓ = 100% confident (rule-based)
✓ = ML confidence (when using trained model)
```

## Color Scheme

```
Element              Color (BGR)     Hex
─────────────────────────────────────────
Panel Background     (30, 30, 30)    #1E1E1E
Panel Border         (0, 150, 255)   #FF9600
Text (Normal)        (200, 200, 200) #C8C8C8
Text (Title)         (0, 200, 255)   #FFC800
FPS Text            (0, 255, 0)     #00FF00
Status Bar          (20, 20, 20)    #141414
Toast Background    (20, 20, 20)    #141414
Toast Text          (0, 230, 255)   #FFE600
Overlay Alpha       0.85            (85%)
```

## Responsive Positioning

```
Resolution: 1280x720

Video Area:           0, 0 → 1000x720
Info Panel:           1010, 30 → 1270x690
Toast:                Center, Y: 645
Status Bar:           0, 690 → 1280x720
FPS Counter:          10, 30
Gesture Label:        Per hand location
```

## Future UI Enhancements

### Planned: Toggle Info Panel (Key I)
```
With I pressed:
┌─────────────────────────────────────────────────────────────────────┐
│                                                    (panel hidden)    │
│                    VIDEO FEED                                       │
│                    (full width)                                     │
│                                                                      │
│  FPS: 28.5 (only FPS shown)                                        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Q: salir  |  R: resetear  |  C: cambiar cámara  |  I: info         │
└─────────────────────────────────────────────────────────────────────┘
```

### Planned: Camera Selector (Floating)
```
┌──────────────────────┐
│ Select Camera        │
├──────────────────────┤
│ ◉ Camera 0 (Laptop)  │
│ ○ Camera 1 (USB)     │
│ ○ Camera 2 (Phone)   │
├──────────────────────┤
│  [Select] [Cancel]   │
└──────────────────────┘
```

## Accessibility Features

- ✓ Alto contraste entre texto y fondo
- ✓ Iconos claros (✓ y ✗)
- ✓ Monospace font para números
- ✓ Notificaciones visuales grandes
- ✓ Status bar siempre visible

## Performance Indicators

```
Good Performance:
├── FPS: 28-30
├── Hands: 1-2
└── Response: <100ms

Warning (May need optimization):
├── FPS: 15-20
├── Resolution: 1280x720
└── Multiple apps running
```

---

¡Disfruta la nueva interfaz mejorada! 🎮
