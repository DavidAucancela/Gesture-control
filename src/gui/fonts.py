"""UTF-8 capable TTF font resolution for text drawn directly onto image data.

Only needed if a future feature burns text into the video frame itself via
PIL. All GUI text goes through native CTkLabel/CTkFont widgets instead,
which use the OS font renderer and already display Spanish accents and
Unicode glyphs correctly — unlike cv2.putText's ASCII-only Hershey fonts.
This module exists so that path, if ever used, doesn't reintroduce the same
class of bug.
"""

import logging

from PIL import ImageFont

logger = logging.getLogger(__name__)

_CANDIDATE_PATHS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/SFNS.ttf",
]


def load_utf8_font(size: int = 20) -> ImageFont.FreeTypeFont:
    """Return a PIL TrueType font capable of rendering Spanish accents.

    Falls back to PIL's built-in bitmap font (ASCII-only) if none of the
    known system font paths are present.
    """
    for path in _CANDIDATE_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    logger.warning("No UTF-8 TTF font found among %s — falling back to default", _CANDIDATE_PATHS)
    return ImageFont.load_default()
