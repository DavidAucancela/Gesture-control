"""Unit tests for ActionDispatcher."""

import time
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.actions import ActionDispatcher
from src.gestures import GestureResult


def _make_gesture(name: str, hand: str = "Right") -> GestureResult:
    return GestureResult(name=name, confidence=1.0, fingers_up=[False] * 5, hand=hand)


def _write_mappings(tmp_path, mappings: dict) -> str:
    path = tmp_path / "mappings.yaml"
    path.write_text(yaml.dump({"gestures": mappings}), encoding="utf-8")
    return str(path)


def test_mapping_carga_correcto(tmp_path):
    """Dispatcher should load all gesture mappings from YAML."""
    mappings = {"punio": "none", "victoria": "key_press:ctrl+c"}
    path = _write_mappings(tmp_path, mappings)
    dispatcher = ActionDispatcher(path)
    assert "punio" in dispatcher._mappings
    assert dispatcher._mappings["victoria"] == "key_press:ctrl+c"


def test_desconocido_no_dispara_accion(tmp_path):
    """'desconocido' gesture should never trigger any action."""
    path = _write_mappings(tmp_path, {"desconocido": "key_press:space"})
    dispatcher = ActionDispatcher(path)
    with patch("src.controllers.keyboard.press_key") as mock_press:
        dispatcher.dispatch(_make_gesture("desconocido"))
        mock_press.assert_not_called()


def test_debounce_previene_spam(tmp_path):
    """Two rapid dispatches of the same gesture should trigger only once."""
    path = _write_mappings(tmp_path, {"victoria": "key_press:ctrl+c"})
    dispatcher = ActionDispatcher(path, cooldown_ms=500)

    call_count = 0

    def fake_press(key):
        nonlocal call_count
        call_count += 1

    with patch("src.controllers.keyboard.press_key", side_effect=fake_press):
        dispatcher.dispatch(_make_gesture("victoria"))
        dispatcher.dispatch(_make_gesture("victoria"))  # should be blocked

    assert call_count == 1, "Debounce should prevent the second dispatch"


def test_debounce_permite_despues_cooldown(tmp_path):
    """After cooldown expires, the same gesture should trigger again."""
    path = _write_mappings(tmp_path, {"victoria": "key_press:ctrl+c"})
    dispatcher = ActionDispatcher(path, cooldown_ms=50)

    call_count = 0

    def fake_press(key):
        nonlocal call_count
        call_count += 1

    with patch("src.controllers.keyboard.press_key", side_effect=fake_press):
        dispatcher.dispatch(_make_gesture("victoria"))
        time.sleep(0.06)  # wait longer than cooldown
        dispatcher.dispatch(_make_gesture("victoria"))

    assert call_count == 2, "After cooldown, second dispatch should proceed"


def test_none_action_no_dispara(tmp_path):
    """Gestures mapped to 'none' should not trigger any action."""
    path = _write_mappings(tmp_path, {"punio": "none"})
    dispatcher = ActionDispatcher(path)
    with patch("src.controllers.keyboard.press_key") as mock_press:
        dispatcher.dispatch(_make_gesture("punio"))
        mock_press.assert_not_called()
