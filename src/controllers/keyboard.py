"""Keyboard control wrapper using pynput (Windows-compatible)."""

import logging

from pynput import keyboard as pynput_keyboard

logger = logging.getLogger(__name__)

_controller = pynput_keyboard.Controller()

# Map string names to pynput Key objects.
# On Windows: ctrl/alt/shift map to their left variants, which is standard.
# Volume keys use Windows multimedia key codes via pynput.
def _key(name: str):
    return getattr(pynput_keyboard.Key, name, None)


_SPECIAL_KEYS: dict[str, pynput_keyboard.Key] = {
    k: v for k, v in {
        "space": _key("space"),
        "enter": _key("enter"),
        "tab": _key("tab"),
        "backspace": _key("backspace"),
        "delete": _key("delete"),
        "esc": _key("esc"),
        "escape": _key("esc"),
        "ctrl": _key("ctrl"),
        "ctrl_l": _key("ctrl_l"),
        "ctrl_r": _key("ctrl_r"),
        "alt": _key("alt"),
        "alt_l": _key("alt_l"),
        "alt_r": _key("alt_r"),
        "shift": _key("shift"),
        "shift_l": _key("shift_l"),
        "shift_r": _key("shift_r"),
        # Windows key (Super on Linux / Cmd on Mac)
        "win": _key("cmd"),
        "super": _key("cmd"),
        "cmd": _key("cmd"),
        # Arrow keys
        "up": _key("up"),
        "down": _key("down"),
        "left": _key("left"),
        "right": _key("right"),
        # Media / volume keys
        "volumeup": _key("media_volume_up"),
        "volumedown": _key("media_volume_down"),
        "volumemute": _key("media_volume_mute"),
        "media_play": _key("media_play_pause"),
        "media_next": _key("media_next"),
        "media_prev": _key("media_previous"),
        # Navigation
        "home": _key("home"),
        "end": _key("end"),
        "page_up": _key("page_up"),
        "page_down": _key("page_down"),
        "insert": _key("insert"),
        # Function keys
        "f1": _key("f1"),
        "f2": _key("f2"),
        "f3": _key("f3"),
        "f4": _key("f4"),
        "f5": _key("f5"),
        "f6": _key("f6"),
        "f7": _key("f7"),
        "f8": _key("f8"),
        "f9": _key("f9"),
        "f10": _key("f10"),
        "f11": _key("f11"),
        "f12": _key("f12"),
        # Print screen / scroll lock / pause
        "print_screen": _key("print_screen"),
        "scroll_lock": _key("scroll_lock"),
        "pause": _key("pause"),
        "caps_lock": _key("caps_lock"),
        "num_lock": _key("num_lock"),
    }.items() if v is not None
}


def _parse_key(key_str: str):
    """Convert a key name string to a pynput key object or character.

    Args:
        key_str: Key name such as 'ctrl', 'c', 'space', 'f5'.

    Returns:
        pynput Key object or single character string.
    """
    key_str = key_str.strip().lower()
    return _SPECIAL_KEYS.get(key_str, key_str)


def press_key(key_combo: str) -> None:
    """Press and release a key or key combination.

    Args:
        key_combo: Key combination string such as 'ctrl+c', 'space', 'f5'.
    """
    parts = [p.strip() for p in key_combo.split("+")]
    keys = [_parse_key(p) for p in parts]

    try:
        # Press all modifier keys, then the final key
        for key in keys[:-1]:
            _controller.press(key)
        _controller.press(keys[-1])
        _controller.release(keys[-1])
        for key in reversed(keys[:-1]):
            _controller.release(key)
        logger.debug("Pressed key combo: %s", key_combo)
    except ValueError as exc:
        logger.error("Invalid key in combo '%s': %s", key_combo, exc)


def hold_key(key: str) -> None:
    """Press and hold a key without releasing.

    Args:
        key: Key name string.
    """
    parsed = _parse_key(key)
    try:
        _controller.press(parsed)
        logger.debug("Holding key: %s", key)
    except ValueError as exc:
        logger.error("Invalid key '%s': %s", key, exc)


def release_key(key: str) -> None:
    """Release a previously held key.

    Args:
        key: Key name string.
    """
    parsed = _parse_key(key)
    try:
        _controller.release(parsed)
        logger.debug("Released key: %s", key)
    except ValueError as exc:
        logger.error("Invalid key '%s': %s", key, exc)
