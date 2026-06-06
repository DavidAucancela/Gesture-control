"""Mouse control wrapper using pynput."""

import logging

from pynput import mouse as pynput_mouse

logger = logging.getLogger(__name__)

_controller = pynput_mouse.Controller()

_BUTTONS = {
    "left": pynput_mouse.Button.left,
    "right": pynput_mouse.Button.right,
    "middle": pynput_mouse.Button.middle,
}


def click(button: str = "left") -> None:
    """Perform a single mouse click.

    Args:
        button: Button to click — 'left', 'right', or 'middle'.
    """
    btn = _BUTTONS.get(button.lower(), pynput_mouse.Button.left)
    _controller.click(btn, 1)
    logger.debug("Mouse click: %s", button)


def scroll(direction: str, amount: int = 3) -> None:
    """Scroll the mouse wheel.

    Args:
        direction: 'up' or 'down'.
        amount: Number of scroll steps.
    """
    dy = amount if direction.lower() == "up" else -amount
    _controller.scroll(0, dy)
    logger.debug("Mouse scroll: %s x%d", direction, amount)


def move_relative(dx: int, dy: int) -> None:
    """Move the mouse cursor by a relative offset.

    Args:
        dx: Horizontal offset in pixels (positive = right).
        dy: Vertical offset in pixels (positive = down).
    """
    _controller.move(dx, dy)
    logger.debug("Mouse move: dx=%d, dy=%d", dx, dy)
