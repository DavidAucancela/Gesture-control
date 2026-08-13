"""Human-readable display names for gesture identifiers.

Single source of truth for gesture -> label text, used everywhere a gesture
name is shown in the GUI. Unlike the old renderer's _ACTION_LABELS dict, this
covers every name recognize() can ever return (including "tres", "cuatro",
and "desconocido"), so a lookup never silently falls back to the raw
internal name.
"""

GESTURE_LABELS: dict[str, str] = {
    "punio": "Puño",
    "mano_abierta": "Mano abierta",
    "señalar": "Señalar",
    "victoria": "Victoria",
    "pulgar_arriba": "Pulgar arriba",
    "pulgar_abajo": "Pulgar abajo",
    "ok": "OK",
    "tres": "Tres",
    "cuatro": "Cuatro",
    "desconocido": "Desconocido",
}

# Gestures the model can actually recognize AND the user can map to an
# action. "desconocido" is excluded — ActionDispatcher.dispatch() special-
# cases it and it can never be usefully mapped.
ACTIONABLE_GESTURES: list[str] = [
    "punio",
    "mano_abierta",
    "señalar",
    "victoria",
    "pulgar_arriba",
    "pulgar_abajo",
    "ok",
    "tres",
    "cuatro",
]

_ACTION_TYPE_LABELS: dict[str, str] = {
    "key_press": "Tecla",
    "key_hold": "Mantener tecla",
    "mouse_click": "Clic",
    "mouse_scroll": "Scroll",
    "none": "Sin acción",
}


def gesture_label(name: str) -> str:
    """Return the display label for a gesture name, falling back to the raw name."""
    return GESTURE_LABELS.get(name, name)


def format_action(action_str: str) -> str:
    """Format an action string ('type' or 'type:payload') for display."""
    if not action_str or action_str == "none":
        return "Sin acción"
    action_type, _, payload = action_str.partition(":")
    type_label = _ACTION_TYPE_LABELS.get(action_type, action_type)
    if not payload:
        return type_label
    if action_type == "key_press" or action_type == "key_hold":
        return f"{type_label}: {payload.upper()}"
    if action_type == "mouse_click":
        return f"{type_label} {payload}"
    if action_type == "mouse_scroll":
        direction = payload.split(":")[0]
        return f"{type_label} {direction}"
    return f"{type_label}: {payload}"
