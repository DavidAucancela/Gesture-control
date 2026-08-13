"""Current-gesture info card: icon, name, per-hand finger states, and short history."""

from collections import deque

import customtkinter as ctk

from src.gestures import GestureResult
from src.gui.icons import get_gesture_icon
from src.gui.labels import gesture_label

_FINGER_LETTERS = ("T", "I", "M", "R", "P")
_HISTORY_LEN = 6


class GesturePanel(ctk.CTkFrame):
    """Shows the currently recognized gesture(s) with icon, name, and finger states."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._history: deque = deque(maxlen=_HISTORY_LEN)
        self._last_shown = None
        self._hand_widgets: dict[str, "_HandCard"] = {}

        title = ctk.CTkLabel(self, text="Gesto actual", font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(anchor="w", padx=12, pady=(10, 4))

        self._hands_container = ctk.CTkFrame(self, fg_color="transparent")
        self._hands_container.pack(fill="x", padx=12, pady=(0, 6))

        self._empty_label = ctk.CTkLabel(
            self._hands_container,
            text="No se detectan manos",
            font=ctk.CTkFont(size=12),
            text_color="#666666",
        )
        self._empty_label.pack(pady=10)

        history_label = ctk.CTkLabel(
            self, text="Historial:", font=ctk.CTkFont(size=12), text_color="#999999"
        )
        history_label.pack(anchor="w", padx=12, pady=(4, 0))
        self._history_label = ctk.CTkLabel(
            self,
            text="—",
            font=ctk.CTkFont(size=12),
            text_color="#cccccc",
            wraplength=340,
            justify="left",
        )
        self._history_label.pack(anchor="w", padx=12, pady=(0, 10))

    def update_gestures(self, gestures: list) -> None:
        """Refresh the panel with the current frame's gesture results.

        Args:
            gestures: List of GestureResult for this frame (0-2 entries).
        """
        present_hands = set()
        for gesture in gestures:
            present_hands.add(gesture.hand)
            card = self._hand_widgets.get(gesture.hand)
            if card is None:
                card = _HandCard(self._hands_container, gesture.hand)
                card.pack(side="left", padx=(0, 10))
                self._hand_widgets[gesture.hand] = card
            card.update(gesture)

            if gesture.name != "desconocido" and gesture.name != self._last_shown:
                self._history.appendleft(gesture_label(gesture.name))
                self._last_shown = gesture.name

        for hand in list(self._hand_widgets):
            if hand not in present_hands:
                self._hand_widgets[hand].destroy()
                del self._hand_widgets[hand]

        if self._hand_widgets:
            self._empty_label.pack_forget()
        else:
            self._empty_label.pack(pady=10)

        if self._history:
            self._history_label.configure(text="  ›  ".join(self._history))


class _HandCard(ctk.CTkFrame):
    """One hand's icon + name + finger-state row."""

    def __init__(self, master, hand: str, **kwargs) -> None:
        super().__init__(master, fg_color="#232323", corner_radius=10, **kwargs)
        self._hand = hand

        header = ctk.CTkLabel(
            self, text=f"Mano {hand[0]}", font=ctk.CTkFont(size=11), text_color="#999999"
        )
        header.pack(pady=(8, 0))

        self._icon_label = ctk.CTkLabel(self, text="")
        self._icon_label.pack(padx=14, pady=4)

        self._name_label = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=14, weight="bold"))
        self._name_label.pack(pady=(0, 4))

        fingers_frame = ctk.CTkFrame(self, fg_color="transparent")
        fingers_frame.pack(pady=(0, 10))
        self._finger_dots = []
        for letter in _FINGER_LETTERS:
            col = ctk.CTkFrame(fingers_frame, fg_color="transparent")
            col.pack(side="left", padx=3)
            dot = ctk.CTkLabel(col, text="●", font=ctk.CTkFont(size=16), text_color="#555555")
            dot.pack()
            letter_lbl = ctk.CTkLabel(col, text=letter, font=ctk.CTkFont(size=9), text_color="#777777")
            letter_lbl.pack()
            self._finger_dots.append(dot)

    def update(self, gesture: GestureResult) -> None:
        """Refresh this hand's icon, name, and finger indicators."""
        icon = get_gesture_icon(gesture.fingers_up, size=72)
        self._icon_label.configure(image=icon)
        self._name_label.configure(text=gesture_label(gesture.name))
        for dot, extended in zip(self._finger_dots, gesture.fingers_up):
            dot.configure(text_color="#3b8ed0" if extended else "#4a4a4a")
