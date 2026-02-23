#!/usr/bin/env python3
"""
Alpha-OSK Launcher

Handles virtual environment setup, dependency checking, and launches the
on-screen keyboard application. Can also launch the project dashboard.

Usage:
    python run.py              # Launch the on-screen keyboard
    python run.py --dashboard  # Launch the project dashboard
"""

import sys
import subprocess
import os
import shutil
import venv
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 9):
        print("ERROR: Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True


def check_system_deps():
    """Check for system-level dependencies."""
    warnings = []
    if not shutil.which("xdotool") and not shutil.which("ydotool"):
        warnings.append(
            "  WARNING: Neither xdotool nor ydotool found.\n"
            "  Key synthesis won't work. Install with:\n"
            "    sudo apt install xdotool"
        )
    return warnings


def setup_virtual_environment():
    """Create virtual environment if it doesn't exist."""
    venv_path = SCRIPT_DIR / "venv"

    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            venv.create(str(venv_path), with_pip=True)
            print("Virtual environment created successfully!")
        except Exception as e:
            print(f"ERROR: Failed to create virtual environment: {e}")
            return False

    return True


def get_venv_python():
    """Get the path to Python executable in virtual environment."""
    return SCRIPT_DIR / "venv" / "bin" / "python"


def check_dependencies():
    """Check if required packages are installed in virtual environment."""
    venv_python = get_venv_python()

    if not venv_python.exists():
        print("ERROR: Virtual environment Python not found")
        return False

    # Check if PySide6 is importable
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import PySide6"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("Installing dependencies in virtual environment...")
            subprocess.check_call(
                [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                stdout=subprocess.DEVNULL,
            )
            subprocess.check_call(
                [str(venv_python), "-m", "pip", "install", "-r",
                 str(SCRIPT_DIR / "requirements.txt")],
            )
            print("Dependencies installed successfully!")

        return True

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error during dependency check: {e}")
        return False


def run_keyboard():
    """Launch the on-screen keyboard via the virtual environment."""
    venv_python = get_venv_python()
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "src.keyboard_app"],
            cwd=str(SCRIPT_DIR),
        )
        return result.returncode
    except Exception as e:
        print(f"ERROR: Failed to run keyboard: {e}")
        return 1


def run_dashboard():
    """Launch the project dashboard (simple HTTP server)."""
    import http.server
    import socketserver
    import webbrowser
    from functools import partial

    port = 8080
    templates_dir = SCRIPT_DIR / "templates"

    if not templates_dir.exists():
        print(f"Error: Templates directory not found: {templates_dir}")
        return 1

    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/" or self.path == "":
                self.path = "/dashboard.html"
            elif self.path == "/slides" or self.path == "/slides/":
                self.path = "/slides.html"
            return super().do_GET()

        def log_message(self, format, *args):
            print(f"[Dashboard] {args[0]}")

    handler = partial(DashboardHandler, directory=str(templates_dir))
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"Dashboard: {url}")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard...")
    return 0


def main():
    """Main launcher function."""
    print("=" * 50)
    print("  Alpha-OSK — On-Screen Keyboard for Linux")
    print("=" * 50)
    print()

    os.chdir(SCRIPT_DIR)

    # Dashboard mode
    if "--dashboard" in sys.argv:
        return run_dashboard()

    # Check Python version
    if not check_python_version():
        return 1

    # Check system dependencies
    warnings = check_system_deps()
    for w in warnings:
        print(w)
    if warnings:
        print()

    # Setup virtual environment
    if not setup_virtual_environment():
        return 1

    # Check/install Python dependencies
    if not check_dependencies():
        return 1

    print("Starting Alpha-OSK keyboard...")
    print()

    try:
        return run_keyboard()
    except KeyboardInterrupt:
        print("\nKeyboard closed.")
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
