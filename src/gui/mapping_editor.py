"""Gesture -> action mapping editor dialog, with save-to-YAML and hot-reload.

Writes config/mappings.yaml directly (plain file I/O, safe from the GUI
thread) and calls back into app.py's on_saved callback, which calls
ActionDispatcher.reload() directly — both the dialog and the dispatcher
live on the Tk main thread, so no cross-thread command is needed.
"""

import logging
from typing import Callable, Optional

import customtkinter as ctk
import yaml

from src.gui.icons import get_gesture_icon
from src.gui.labels import ACTIONABLE_GESTURES, gesture_label

logger = logging.getLogger(__name__)

_ACTION_TYPES = ["none", "key_press", "key_hold", "mouse_click", "mouse_scroll"]
_MOUSE_BUTTONS = ["left", "right", "middle"]
_SCROLL_DIRS = ["up", "down"]

_HEADER_COMMENT = (
    "# Formato: nombre_gesto: tipo_accion:payload\n"
    "# Tipos disponibles: key_press, key_hold, mouse_click, mouse_scroll, none\n"
)

# Representative fingers_up pattern per gesture, used only to render an icon
# in the editor (mirrors the rules in src/gestures.py::_recognize_rule_based).
_GESTURE_ICON_FINGERS = {
    "punio": [False, False, False, False, False],
    "mano_abierta": [True, True, True, True, True],
    "señalar": [False, True, False, False, False],
    "victoria": [False, True, True, False, False],
    "pulgar_arriba": [True, False, False, False, False],
    "pulgar_abajo": [True, False, False, False, False],
    "ok": [False, False, True, True, True],
    "tres": [False, True, True, True, False],
    "cuatro": [False, True, True, True, True],
}


class MappingEditorDialog(ctk.CTkToplevel):
    """Modal dialog to edit gesture -> action mappings, saved to mappings.yaml.

    Args:
        master: Parent window.
        mappings_path: Path to config/mappings.yaml.
        on_saved: Called after a successful save (used to trigger hot-reload).
    """

    def __init__(self, master, mappings_path: str, on_saved: Callable[[], None], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.title("Editar mapeos de gestos")
        self.geometry("560x600")
        self._mappings_path = mappings_path
        self._on_saved = on_saved
        self._rows: list = []

        current = self._load_current()

        scroll = ctk.CTkScrollableFrame(self, label_text="Gesto → Acción")
        scroll.pack(fill="both", expand=True, padx=14, pady=(14, 6))

        for name in ACTIONABLE_GESTURES:
            row = _MappingRow(scroll, name, current.get(name, "none"))
            row.pack(fill="x", pady=4)
            self._rows.append(row)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(0, 14))

        self._status_label = ctk.CTkLabel(footer, text="", text_color="#4caf50")
        self._status_label.pack(side="left")

        save_btn = ctk.CTkButton(footer, text="Guardar", command=self._save)
        save_btn.pack(side="right")

        self.transient(master)
        self.grab_set()

    def _load_current(self) -> dict:
        try:
            with open(self._mappings_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("gestures", {}) or {}
        except FileNotFoundError:
            return {}

    def _save(self) -> None:
        mapping = {row.gesture_name: row.get_action_string() for row in self._rows}
        try:
            with open(self._mappings_path, "w", encoding="utf-8") as f:
                f.write(_HEADER_COMMENT)
                yaml.safe_dump({"gestures": mapping}, f, allow_unicode=True, sort_keys=False)
        except OSError as exc:
            logger.error("Failed to save mappings: %s", exc)
            self._status_label.configure(text=f"Error: {exc}", text_color="#e05555")
            return

        self._status_label.configure(text="Guardado ✓", text_color="#4caf50")
        self._on_saved()
        self.after(1200, lambda: self._status_label.configure(text=""))


class _MappingRow(ctk.CTkFrame):
    """One editable gesture -> action row."""

    def __init__(self, master, gesture_name: str, action_str: str, **kwargs) -> None:
        super().__init__(master, fg_color="#232323", corner_radius=8, **kwargs)
        self.gesture_name = gesture_name

        icon = get_gesture_icon(_GESTURE_ICON_FINGERS.get(gesture_name, [False] * 5), size=36)
        icon_label = ctk.CTkLabel(self, text="", image=icon)
        icon_label.pack(side="left", padx=(8, 6), pady=8)

        name_label = ctk.CTkLabel(self, text=gesture_label(gesture_name), width=110, anchor="w")
        name_label.pack(side="left", padx=(0, 6))

        action_type, _, payload = (action_str or "none").partition(":")
        if action_type not in _ACTION_TYPES:
            action_type = "none"

        self._type_menu = ctk.CTkOptionMenu(
            self, values=_ACTION_TYPES, width=120, command=self._on_type_change
        )
        self._type_menu.set(action_type)
        self._type_menu.pack(side="left", padx=(0, 6))

        self._payload_container = ctk.CTkFrame(self, fg_color="transparent")
        self._payload_container.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._key_entry: Optional[ctk.CTkEntry] = None
        self._click_menu: Optional[ctk.CTkOptionMenu] = None
        self._scroll_dir_menu: Optional[ctk.CTkOptionMenu] = None
        self._scroll_amount_entry: Optional[ctk.CTkEntry] = None

        self._build_payload_widgets(action_type, payload)

    def _on_type_change(self, _value: str) -> None:
        self._build_payload_widgets(self._type_menu.get(), "")

    def _build_payload_widgets(self, action_type: str, payload: str) -> None:
        for child in self._payload_container.winfo_children():
            child.destroy()
        self._key_entry = None
        self._click_menu = None
        self._scroll_dir_menu = None
        self._scroll_amount_entry = None

        if action_type in ("key_press", "key_hold"):
            self._key_entry = ctk.CTkEntry(self._payload_container, placeholder_text="ej. ctrl+c")
            if payload:
                self._key_entry.insert(0, payload)
            self._key_entry.pack(fill="x")
        elif action_type == "mouse_click":
            self._click_menu = ctk.CTkOptionMenu(self._payload_container, values=_MOUSE_BUTTONS)
            self._click_menu.set(payload if payload in _MOUSE_BUTTONS else "left")
            self._click_menu.pack(fill="x")
        elif action_type == "mouse_scroll":
            direction, _, amount = payload.partition(":")
            row = ctk.CTkFrame(self._payload_container, fg_color="transparent")
            row.pack(fill="x")
            self._scroll_dir_menu = ctk.CTkOptionMenu(row, values=_SCROLL_DIRS, width=70)
            self._scroll_dir_menu.set(direction if direction in _SCROLL_DIRS else "up")
            self._scroll_dir_menu.pack(side="left")
            self._scroll_amount_entry = ctk.CTkEntry(row, width=50, placeholder_text="3")
            if amount:
                self._scroll_amount_entry.insert(0, amount)
            self._scroll_amount_entry.pack(side="left", padx=(6, 0))
        # "none" -> no payload widgets

    def get_action_string(self) -> str:
        """Build the 'type' or 'type:payload' string this row currently represents."""
        action_type = self._type_menu.get()
        if action_type == "none":
            return "none"
        if action_type in ("key_press", "key_hold"):
            payload = self._key_entry.get().strip() if self._key_entry else ""
            return f"{action_type}:{payload}" if payload else "none"
        if action_type == "mouse_click":
            button = self._click_menu.get() if self._click_menu else "left"
            return f"mouse_click:{button}"
        if action_type == "mouse_scroll":
            direction = self._scroll_dir_menu.get() if self._scroll_dir_menu else "up"
            amount = self._scroll_amount_entry.get().strip() if self._scroll_amount_entry else ""
            amount = amount if amount.isdigit() else "3"
            return f"mouse_scroll:{direction}:{amount}"
        return "none"
