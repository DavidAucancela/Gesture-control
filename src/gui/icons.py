"""Programmatic gesture icon generation.

Draws a simple stylized hand icon from a fingers_up boolean list
([thumb, index, middle, ring, pinky]) using PIL. Only 2**5 = 32 finger-state
combinations exist, so results are cached — this auto-generates an icon for
every gesture the recognizer can ever produce (including future/retrained
gestures) without maintaining a per-name asset.
"""

from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw

_PALM_COLOR = (90, 90, 100, 255)
_EXTENDED_COLOR = (59, 142, 208, 255)  # CTk default accent blue
_CURLED_COLOR = (70, 70, 78, 255)
_TRANSPARENT = (0, 0, 0, 0)

_FINGER_ORDER = ("thumb", "index", "middle", "ring", "pinky")


@lru_cache(maxsize=64)
def _render_icon(fingers: tuple, size: int) -> Image.Image:
    """Render (and cache) a stylized hand as a PIL RGBA image.

    Args:
        fingers: (thumb, index, middle, ring, pinky) booleans.
        size: Icon side length in pixels.

    Returns:
        RGBA PIL Image.
    """
    img = Image.new("RGBA", (size, size), _TRANSPARENT)
    draw = ImageDraw.Draw(img)

    palm_w = size * 0.5
    palm_h = size * 0.38
    palm_x0 = (size - palm_w) / 2
    palm_y0 = size - palm_h - size * 0.08
    draw.rounded_rectangle(
        [palm_x0, palm_y0, palm_x0 + palm_w, palm_y0 + palm_h],
        radius=palm_w * 0.25,
        fill=_PALM_COLOR,
    )

    finger_w = size * 0.11
    gap = size * 0.03
    total_w = finger_w * 4 + gap * 3
    start_x = (size - total_w) / 2
    long_len = size * 0.42
    short_len = size * 0.14
    base_y = palm_y0 + size * 0.05

    for i, name in enumerate(("index", "middle", "ring", "pinky")):
        extended = fingers[_FINGER_ORDER.index(name)]
        length = long_len if extended else short_len
        color = _EXTENDED_COLOR if extended else _CURLED_COLOR
        x0 = start_x + i * (finger_w + gap)
        y1 = base_y
        y0 = y1 - length
        draw.rounded_rectangle([x0, y0, x0 + finger_w, y1], radius=finger_w * 0.45, fill=color)

    thumb_extended = fingers[_FINGER_ORDER.index("thumb")]
    thumb_len = size * 0.32 if thumb_extended else size * 0.12
    thumb_w = size * 0.13
    thumb_color = _EXTENDED_COLOR if thumb_extended else _CURLED_COLOR
    tx0 = palm_x0 - thumb_len * 0.55
    ty0 = palm_y0 + palm_h * 0.15
    draw.rounded_rectangle(
        [tx0, ty0, tx0 + thumb_len, ty0 + thumb_w],
        radius=thumb_w * 0.45,
        fill=thumb_color,
    )

    return img


def get_gesture_icon(fingers_up: list, size: int = 96) -> ctk.CTkImage:
    """Return a CTkImage of a stylized hand for the given finger states.

    Args:
        fingers_up: [thumb, index, middle, ring, pinky] booleans.
        size: Icon side length in pixels.

    Returns:
        A CTkImage ready to pass as a CTkLabel's image=.
    """
    key = tuple(bool(f) for f in fingers_up)
    pil_img = _render_icon(key, size)
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
