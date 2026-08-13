"""Video display panel — a CTkLabel used purely as an image surface."""

import customtkinter as ctk
from PIL import Image


class VideoPanel(ctk.CTkFrame):
    """Displays the live camera feed, or a status message when no frame is available.

    Args:
        master: Parent widget.
    """

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="#101010", **kwargs)
        self._label = ctk.CTkLabel(
            self, text="Iniciando cámara…", text_color="#888888", font=ctk.CTkFont(size=16)
        )
        self._label.pack(fill="both", expand=True)
        self._current_image = None  # keep a reference so Tk doesn't garbage-collect it

    def update_frame(self, pil_image: Image.Image) -> None:
        """Display a new RGB frame.

        Args:
            pil_image: RGB PIL Image to display.
        """
        w, h = pil_image.size
        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w, h))
        self._current_image = ctk_image
        self._label.configure(image=ctk_image, text="")

    def show_message(self, text: str) -> None:
        """Display a text message instead of a frame (e.g. a camera error)."""
        self._current_image = None
        self._label.configure(image=None, text=text)
