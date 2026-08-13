"""Live FPS + gesture-frequency chart, embedded via matplotlib's Tk backend.

push_sample() is cheap (O(1) append) and safe to call every polled frame;
the actual matplotlib redraw is decoupled and throttled to ~2Hz via its own
self.after() cycle, so it never competes frame-for-frame with video updates.
"""

from collections import Counter, deque
from typing import Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.gui.labels import gesture_label

_MAX_SAMPLES = 120
_REDRAW_INTERVAL_MS = 500
_TOP_N_GESTURES = 6

_FACE_COLOR = "#1a1a1a"
_AXIS_COLOR = "#888888"
_LINE_COLOR = "#3b8ed0"
_BAR_COLOR = "#3b8ed0"


class FpsHistoryChart(ctk.CTkFrame):
    """Sidebar panel with an FPS-over-time line and a gesture-frequency bar chart."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        title = ctk.CTkLabel(self, text="Actividad", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(10, 4))

        self._fps_samples: deque = deque(maxlen=_MAX_SAMPLES)
        self._gesture_counts: Counter = Counter()

        self._figure = Figure(figsize=(3.6, 2.8), dpi=100, facecolor=_FACE_COLOR)
        self._ax_fps = self._figure.add_subplot(2, 1, 1)
        self._ax_gestures = self._figure.add_subplot(2, 1, 2)
        self._figure.subplots_adjust(hspace=0.6, left=0.15, right=0.95, top=0.92, bottom=0.15)

        self._chart_canvas = FigureCanvasTkAgg(self._figure, master=self)
        self._chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._style_axes()
        self._redraw()
        self.after(_REDRAW_INTERVAL_MS, self._scheduled_redraw)

    def push_sample(self, fps: float, gesture_name: Optional[str]) -> None:
        """Record one frame's stats. Cheap — safe to call at full video framerate.

        Args:
            fps: Instantaneous FPS for this frame.
            gesture_name: Recognized gesture name for this frame, or None.
        """
        self._fps_samples.append(fps)
        if gesture_name and gesture_name != "desconocido":
            self._gesture_counts[gesture_name] += 1

    def reset_stats(self) -> None:
        """Clear accumulated gesture-frequency counts (FPS history is left as-is)."""
        self._gesture_counts.clear()

    def _style_axes(self) -> None:
        for ax in (self._ax_fps, self._ax_gestures):
            ax.set_facecolor(_FACE_COLOR)
            ax.tick_params(colors=_AXIS_COLOR, labelsize=7)
            for spine in ax.spines.values():
                spine.set_color(_AXIS_COLOR)

    def _scheduled_redraw(self) -> None:
        self._redraw()
        self.after(_REDRAW_INTERVAL_MS, self._scheduled_redraw)

    def _redraw(self) -> None:
        self._ax_fps.clear()
        self._ax_gestures.clear()
        self._style_axes()

        self._ax_fps.set_title("FPS", color=_AXIS_COLOR, fontsize=8, loc="left")
        if self._fps_samples:
            self._ax_fps.plot(list(self._fps_samples), color=_LINE_COLOR, linewidth=1.5)
        self._ax_fps.set_ylim(0, 35)
        self._ax_fps.set_xticks([])

        self._ax_gestures.set_title("Gestos frecuentes", color=_AXIS_COLOR, fontsize=8, loc="left")
        top = self._gesture_counts.most_common(_TOP_N_GESTURES)
        if top:
            names = [gesture_label(n) for n, _ in reversed(top)]
            counts = [c for _, c in reversed(top)]
            self._ax_gestures.barh(names, counts, color=_BAR_COLOR)

        self._chart_canvas.draw_idle()
