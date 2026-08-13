"""Main desktop application window: wires the video feed, sidebar panels,
background capture worker, and mapping editor together.

Threading contract: this class and everything it owns directly (widgets,
PhotoImages, the matplotlib canvas) run exclusively on the Tk main thread.
The only cross-thread communication is via the two queues handed to
CaptureWorker — see src/gui/worker.py for the worker side of the contract.

ActionDispatcher (keyboard/mouse execution) is owned and called here, on
the main thread, deliberately — not by CaptureWorker. macOS's Text Input
Source Manager, which pynput's keyboard backend touches internally, only
allows being called from the main thread and raises SIGTRAP otherwise.
"""

import logging
import queue
from typing import Optional

import customtkinter as ctk
from PIL import Image

from src.actions import ActionDispatcher
from src.gui.camera_bar import CameraBar
from src.gui.charts import FpsHistoryChart
from src.gui.gesture_panel import GesturePanel
from src.gui.labels import format_action, gesture_label
from src.gui.mapping_editor import MappingEditorDialog
from src.gui.video_panel import VideoPanel
from src.gui.worker import CaptureWorker
from src.ui.camera_control import CameraSelector

logger = logging.getLogger(__name__)

_MAPPINGS_PATH = "config/mappings.yaml"
_POLL_INTERVAL_MS = 33
_TOAST_DURATION_MS = 1500


class GestureControlApp(ctk.CTk):
    """Top-level application window.

    Args:
        settings: Parsed config/settings.yaml dict.
        enable_actions: If False, gestures are recognized but no keyboard/mouse
            action is ever dispatched (mirrors the old --no-actions flag). The
            mapping editor remains available either way.
        initial_camera: Camera device index to start with, overriding settings.
        debug: If True, logs wrist landmark coordinates for the first hand each frame.
    """

    def __init__(
        self,
        settings: dict,
        enable_actions: bool = True,
        initial_camera: Optional[int] = None,
        debug: bool = False,
    ) -> None:
        super().__init__()

        gui_cfg = settings.get("gui", {})
        ctk.set_appearance_mode(gui_cfg.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        self.title("Control por Gestos")
        width = gui_cfg.get("window_width", 1280)
        height = gui_cfg.get("window_height", 800)
        self.geometry(f"{width}x{height}")
        self.minsize(1000, 650)

        cam_cfg = settings["camera"]
        mp_cfg = settings["mediapipe"]
        device_id = initial_camera if initial_camera is not None else cam_cfg.get("device_id", 0)

        self._camera_selector = CameraSelector(device_id)
        if (
            self._camera_selector.available_cameras
            and device_id not in self._camera_selector.available_cameras
        ):
            logger.warning("Configured camera %d not available, using first detected", device_id)
            device_id = self._camera_selector.available_cameras[0]
            self._camera_selector.switch_camera(device_id)

        self._dispatcher: Optional[ActionDispatcher] = None
        if enable_actions:
            try:
                self._dispatcher = ActionDispatcher(_MAPPINGS_PATH)
            except FileNotFoundError:
                logger.warning("%s not found — actions disabled", _MAPPINGS_PATH)
            except Exception as exc:  # noqa: BLE001 - keep the app usable without actions
                logger.warning("ActionDispatcher init failed: %s — actions disabled", exc)

        self._out_queue: queue.Queue = queue.Queue(maxsize=2)
        self._cmd_queue: queue.Queue = queue.Queue()

        self._worker = CaptureWorker(
            device_id=device_id,
            cam_cfg=cam_cfg,
            mp_cfg=mp_cfg,
            out_queue=self._out_queue,
            cmd_queue=self._cmd_queue,
            debug=debug,
        )

        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._worker.start()
        self.after(_POLL_INTERVAL_MS, self._poll_queue)

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=380)
        self.grid_rowconfigure(0, weight=1)

        self._video_panel = VideoPanel(self)
        self._video_panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        sidebar = ctk.CTkFrame(self, width=380)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        sidebar.grid_propagate(False)

        camera_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        camera_section.pack(fill="x", padx=4, pady=(4, 8))
        ctk.CTkLabel(
            camera_section, text="Cámara", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 4))
        self._camera_bar = CameraBar(
            camera_section, self._camera_selector, on_change=self._on_camera_change
        )
        self._camera_bar.pack(fill="x")

        self._gesture_panel = GesturePanel(sidebar)
        self._gesture_panel.pack(fill="x", padx=0, pady=(0, 8))

        self._chart = FpsHistoryChart(sidebar)
        self._chart.pack(fill="both", expand=True, padx=0, pady=(0, 8))

        self._toast_label = ctk.CTkLabel(
            sidebar, text="", font=ctk.CTkFont(size=13, weight="bold"), text_color="#00e6ff"
        )
        self._toast_label.pack(fill="x", padx=4, pady=(0, 4))

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=4, pady=(0, 8))

        edit_btn = ctk.CTkButton(
            footer, text="Editar mapeos de gestos…", command=self._open_mapping_editor
        )
        edit_btn.pack(fill="x", pady=(0, 6))

        self._status_label = ctk.CTkLabel(
            footer, text="Iniciando…", font=ctk.CTkFont(size=11), text_color="#888888"
        )
        self._status_label.pack(anchor="w")

    def _on_camera_change(self, device_id: int) -> None:
        self._cmd_queue.put(("switch_camera", device_id))
        name = self._camera_selector.get_camera_name(device_id)
        self._status_label.configure(text=f"Cambiando a {name}…")

    def _open_mapping_editor(self) -> None:
        MappingEditorDialog(self, _MAPPINGS_PATH, on_saved=self._on_mappings_saved)

    def _on_mappings_saved(self) -> None:
        if self._dispatcher:
            self._dispatcher.reload()
            logger.info("Gesture mappings reloaded")

    def _poll_queue(self) -> None:
        latest_update = None
        while True:
            try:
                latest_update = self._out_queue.get_nowait()
            except queue.Empty:
                break

        if latest_update is not None:
            self._apply_update(latest_update)

        self.after(_POLL_INTERVAL_MS, self._poll_queue)

    def _apply_update(self, update) -> None:
        if update.camera_error:
            self._video_panel.show_message(f"Error de cámara:\n{update.camera_error}")
            self._status_label.configure(text="Cámara no disponible")
            return

        pil_image = Image.fromarray(update.frame)
        self._video_panel.update_frame(pil_image)
        self._gesture_panel.update_gestures(update.gestures)

        primary_gesture = update.gestures[0].name if update.gestures else None
        self._chart.push_sample(update.fps, primary_gesture)

        name = self._camera_selector.get_camera_name(self._camera_selector.current_device_id)
        self._status_label.configure(
            text=f"{name}  •  {update.hands_count} mano(s)  •  {update.fps:.1f} FPS"
        )

        if self._dispatcher:
            for gesture in update.gestures:
                fired = self._dispatcher.dispatch(gesture)
                if fired:
                    gesture_name, action_str = fired
                    self._show_toast(
                        f"{gesture_label(gesture_name)}  →  {format_action(action_str)}"
                    )

    def _show_toast(self, text: str) -> None:
        self._toast_label.configure(text=text)
        self.after(_TOAST_DURATION_MS, lambda: self._toast_label.configure(text=""))

    def _on_close(self) -> None:
        self._worker.stop()
        self._cmd_queue.put(("stop",))
        self._worker.join(timeout=2.0)
        self.destroy()
