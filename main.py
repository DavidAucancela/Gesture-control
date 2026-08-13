"""
Gesture Control — Entry point.

Launches the CustomTkinter desktop app: live camera feed with hand-skeleton
overlay, a sidebar with the current gesture (icon + finger states), a live
FPS/gesture-frequency chart, a camera selector, and a gesture-mapping editor.

Usage:
    python main.py                  # default camera
    python main.py --camera 1       # specific camera index
    python main.py --no-actions     # detection only, no keyboard/mouse control
    python main.py --debug          # log wrist landmark coordinates
"""

import argparse
import logging
import sys

import yaml


def _setup_logging(level_str: str = "INFO") -> None:
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-time hand gesture control")
    parser.add_argument("--camera", type=int, default=None, help="Camera device index")
    parser.add_argument("--no-actions", action="store_true", help="Disable keyboard/mouse actions")
    parser.add_argument("--debug", action="store_true", help="Log wrist landmark coordinates")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        settings = _load_settings()
    except FileNotFoundError:
        print("ERROR: config/settings.yaml not found. Run from the project root.", file=sys.stderr)
        return 1
    except yaml.YAMLError as exc:
        print(f"ERROR: Invalid settings.yaml — {exc}", file=sys.stderr)
        return 1

    log_level = settings.get("logging", {}).get("level", "INFO")
    _setup_logging(log_level)

    from src.gui.app import GestureControlApp

    app = GestureControlApp(
        settings,
        enable_actions=not args.no_actions,
        initial_camera=args.camera,
        debug=args.debug,
    )
    app.mainloop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
