# Quick Start - Enhanced UI

## Paso 1: Detectar Cámaras Disponibles

```bash
python tools/camera_detector.py
```

Esto mostrará:
- ✓ Cámaras detectadas y sus índices
- ✓ Resolución y FPS de cada cámara
- ✓ Cuáles cámaras funcionan

## Paso 2: Ejecutar la Interfaz Mejorada

```bash
python main_enhanced.py
```

## Paso 3: Usar la Interfaz

### Panel de Información (Derecha)
Muestra en tiempo real:
- 📷 Cámara actual
- 👐 Manos detectadas (0-2)
- ✋ Gestos reconocidos
- 🖐️ Estado de dedos (✓ extendido, ✗ plegado)
- ⚡ FPS actual
- 🎯 Último gesto

### Controles de Teclado
| Tecla | Acción |
|-------|--------|
| **C** | Cambiar a próxima cámara |
| **R** | Resetear dispatcher |
| **Q** | Salir |

### Notificación de Acciones (Centro)
Cuando un gesto ejecuta una acción:
```
Mano Abierta  →  SPACE
```

## Paso 4: Cambiar Cámaras

**Presionar C** para ciclar entre cámaras disponibles:
- **Camera 0**: Laptop (por defecto)
- **Camera 1**: USB/Externa
- **Camera 2**: Teléfono (con DroidCam)

## Paso 5: Probar con Teléfono

### Opción A: DroidCam (Recomendado)
1. Descargar **DroidCam** en Android
2. Conectar a la misma WiFi
3. Ejecutar: `python main_enhanced.py --camera 1`

### Opción B: IP Webcam
1. Descargar **IP Webcam** en Android
2. Anotar IP:PORT
3. Ejecutar: `python main_enhanced.py --camera 1`

## Ejemplos de Uso

### Usar cámara específica
```bash
python main_enhanced.py --camera 1
```

### Modo debug (mostrar coordenadas)
```bash
python main_enhanced.py --debug
```

### Solo detección (sin acciones)
```bash
python main_enhanced.py --no-actions
```

### Combinado
```bash
python main_enhanced.py --camera 1 --debug --no-actions
```

## Gestos Disponibles

```
Puño          → ✗ ✗ ✗ ✗ ✗
Mano abierta  → ✓ ✓ ✓ ✓ ✓
Señalar       → ✗ ✓ ✗ ✗ ✗
Victoria      → ✗ ✓ ✓ ✗ ✗
Rock          → ✗ ✓ ✗ ✗ ✓
Pulgar arriba → ✓ ✗ ✗ ✗ ✗
Pulgar abajo  → ✓ ✗ ✗ ✗ ✗
OK            → ✓ ✓ ✓ ✓ ✓
```

## Solución de Problemas

### Cámara no detectada
```bash
python tools/camera_detector.py
```
Verifica qué cámaras están disponibles y usa el índice correcto.

### Imagen lenta
- Reduce resolución en `config/settings.yaml`:
  ```yaml
  camera:
    width: 640
    height: 480
  ```

### Información no visible
Verifica que esté habilitada en `config/settings.yaml`:
```yaml
renderer:
  show_info_panel: true
```

## Características

✨ **Cambio de cámara en tiempo real** - Presiona C
✨ **Panel de información mejorado** - Detalles de gestos
✨ **Detección de cámaras automática** - Funciona con USB y teléfonos
✨ **Compatible con 1 o 2 manos** - Detección simultánea
✨ **Historial de gestos** - Sigue los últimos reconocidos
✨ **Estadísticas en vivo** - FPS y contadores

## Documentación Completa

Para más detalles, lee:
- **UI_GUIDE.md** - Guía completa de la interfaz
- **CHANGELOG_UI.md** - Cambios técnicos realizados
- **README.md** - Información general del proyecto

## Próximos Pasos

1. Personaliza gestos en `config/mappings.yaml`
2. Entrena gestos personalizados con `tools/collect_data.py`
3. Experimenta con diferentes configuraciones
4. Configura cámaras específicas para tus casos de uso

## Soporte

- Revisa `UI_GUIDE.md` para preguntas específicas
- Ejecuta `python tools/camera_detector.py` para diagnosticar cámaras
- Verifica `config/settings.yaml` para opciones avanzadas

---

¡Disfruta controlando gestos! 🎮👐
