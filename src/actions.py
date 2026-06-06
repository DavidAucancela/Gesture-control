"""Gesture-to-action dispatcher with debounce protection."""

import logging
import time
from typing import Optional, Tuple

import yaml

from src.gestures import GestureResult

logger = logging.getLogger(__name__)

# Default cooldown between repeated firings of the same gesture (milliseconds)
_DEFAULT_COOLDOWN_MS = 800


class ActionDispatcher:
    """Loads gesture→action mappings and executes actions with debounce.

    Args:
        mappings_path: Path to mappings.yaml file.
        cooldown_ms: Minimum milliseconds between repeated same-gesture dispatches.
    """

    def __init__(self, mappings_path: str, cooldown_ms: int = _DEFAULT_COOLDOWN_MS) -> None:
        self._cooldown_ms = cooldown_ms
        self._last_dispatch: dict[str, float] = {}
        self._mappings: dict[str, str] = {}
        self._load_mappings(mappings_path)

    def _load_mappings(self, path: str) -> None:
        """Load gesture mappings from YAML file.

        Args:
            path: Filesystem path to mappings.yaml.

        Raises:
            FileNotFoundError: If the mappings file does not exist.
            yaml.YAMLError: If the file contains invalid YAML.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        gestures = data.get("gestures", {})
        self._mappings = {k: (v or "none") for k, v in gestures.items()}
        logger.info("Loaded %d gesture mappings from %s", len(self._mappings), path)

    def dispatch(self, gesture: GestureResult) -> Optional[Tuple[str, str]]:
        """Execute the action mapped to the given gesture, if debounce allows.

        Returns:
            (gesture_name, action_str) if an action fired, else None.
        """
        name = gesture.name
        if name == "desconocido":
            return None

        action_str = self._mappings.get(name, "none")
        if action_str == "none":
            return None

        if not self._debounce(name, self._cooldown_ms):
            return None

        self._execute(action_str)
        return (name, action_str)

    def _debounce(self, gesture_name: str, cooldown_ms: int) -> bool:
        """Check whether enough time has passed since the last dispatch.

        Args:
            gesture_name: Name of the gesture being checked.
            cooldown_ms: Required gap in milliseconds.

        Returns:
            True if the action should proceed, False if still cooling down.
        """
        now_ms = time.time() * 1000
        last = self._last_dispatch.get(gesture_name, 0.0)
        if now_ms - last >= cooldown_ms:
            self._last_dispatch[gesture_name] = now_ms
            return True
        return False

    def _execute(self, action_str: str) -> None:
        """Parse and execute an action string.

        Format: 'action_type:payload' or just 'action_type'.

        Args:
            action_str: Action descriptor such as 'key_press:ctrl+c'.
        """
        if ":" in action_str:
            action_type, payload = action_str.split(":", 1)
        else:
            action_type = action_str
            payload = ""

        try:
            if action_type == "key_press":
                from src.controllers.keyboard import press_key  # noqa: PLC0415
                press_key(payload)
            elif action_type == "key_hold":
                from src.controllers.keyboard import hold_key  # noqa: PLC0415
                hold_key(payload)
            elif action_type == "mouse_click":
                from src.controllers.mouse import click  # noqa: PLC0415
                click(payload)
            elif action_type == "mouse_scroll":
                from src.controllers.mouse import scroll  # noqa: PLC0415
                direction, _, amount_str = payload.partition(":")
                scroll(direction, int(amount_str) if amount_str else 3)
            else:
                logger.warning("Unknown action type: %s", action_type)
        except ImportError as exc:
            logger.error("Controller import failed: %s", exc)
        except OSError as exc:
            logger.error("Action execution failed for '%s': %s", action_str, exc)
