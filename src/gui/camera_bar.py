"""Camera selection dropdown, backed by src.ui.camera_control.CameraSelector."""

from typing import Callable

import customtkinter as ctk

from src.ui.camera_control import CameraSelector


class CameraBar(ctk.CTkFrame):
    """Dropdown + refresh button for choosing the active camera.

    Args:
        master: Parent widget.
        selector: CameraSelector instance (owns available-camera detection).
        on_change: Callback invoked with the newly selected device_id.
    """

    def __init__(self, master, selector: CameraSelector, on_change: Callable, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selector = selector
        self._on_change = on_change
        self._name_to_id: dict = {}

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        self._menu = ctk.CTkOptionMenu(row, values=["—"], command=self._on_select)
        self._menu.pack(side="left", fill="x", expand=True)

        refresh_btn = ctk.CTkButton(row, text="⟳", width=32, command=self._refresh)
        refresh_btn.pack(side="left", padx=(6, 0))

        self._populate()

    def _populate(self) -> None:
        names = []
        self._name_to_id.clear()
        for device_id in self._selector.available_cameras:
            name = self._selector.get_camera_name(device_id)
            label = f"{name} ({device_id})"
            names.append(label)
            self._name_to_id[label] = device_id

        if not names:
            names = ["Sin cámaras"]

        self._menu.configure(values=names)
        current_label = names[0]
        for label, device_id in self._name_to_id.items():
            if device_id == self._selector.current_device_id:
                current_label = label
                break
        self._menu.set(current_label)

    def _refresh(self) -> None:
        self._selector.refresh_cameras()
        self._populate()

    def _on_select(self, label: str) -> None:
        device_id = self._name_to_id.get(label)
        if device_id is not None and device_id != self._selector.current_device_id:
            self._selector.switch_camera(device_id)
            self._on_change(device_id)
