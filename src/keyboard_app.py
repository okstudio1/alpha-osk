"""
Keyboard Application - QML engine setup and window configuration.

Launches the on-screen keyboard as a PySide6/QML application with
proper window flags for an OSK (stays on top, doesn't steal focus).
"""

from __future__ import annotations

import sys
import os
import logging
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from .keyboard_bridge import KeyboardBridge

_logger = logging.getLogger("KeyboardApp")


def qml_path() -> Path:
    """Resolve the path to Main.qml relative to this file."""
    here = Path(__file__).resolve().parent
    project_root = here.parent
    return project_root / "qml" / "Main.qml"


def main() -> int:
    """Launch the Alpha-OSK on-screen keyboard."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(levelname)s: %(message)s",
    )

    # Set environment hints for proper OSK behavior on X11
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Alpha-OSK")
    app.setOrganizationName("alpha-osk")

    # Create the bridge
    bridge = KeyboardBridge()

    if not bridge.synthAvailable:
        _logger.warning(
            "No key synthesis tool found. Install xdotool: sudo apt install xdotool"
        )

    # Set up QML engine
    engine = QQmlApplicationEngine()

    # Expose bridge to QML
    engine.rootContext().setContextProperty("keyboard", bridge)

    # Load QML
    main_qml = qml_path()
    if not main_qml.exists():
        _logger.error("QML file not found: %s", main_qml)
        return 1

    _logger.info("Loading QML from: %s", main_qml)
    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        _logger.error("Failed to load QML")
        return 1

    # Apply window flags for OSK behavior
    root = engine.rootObjects()[0]
    if root:
        root.setFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
