"""
Linux Key Synthesizer
======================

Implements key synthesis for Linux using **xdotool** (X11) or **ydotool**
(Wayland) as subprocess backends.

Backend Selection
-----------------
1. If ``xdotool`` is on ``$PATH`` and ``$WAYLAND_DISPLAY`` is *not* set →
   use xdotool (X11).
2. If ``ydotool`` is on ``$PATH`` → use ydotool (Wayland-compatible).
3. Otherwise → :meth:`is_available` returns False and all send methods
   log a warning and no-op.

Key Name Mapping
----------------
The bridge layer uses platform-neutral names (``"BackSpace"``, ``"Return"``,
``"F1"``, etc.).  These happen to match xdotool's X11 keysym names exactly,
so the Linux backend's key map is mostly pass-through.  ydotool uses
different keycode integers — those are mapped in ``_YDOTOOL_KEY_MAP``.

Dependencies
------------
- ``xdotool``:  ``sudo apt install xdotool``
- ``ydotool``:  ``sudo apt install ydotool`` (needs ``ydotoold`` running)

See Also
--------
- ``base.py`` — abstract interface this class implements.
- ``docs/PLATFORM_ARCHITECTURE.md`` — design rationale.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import List, Optional

from .base import KeySynthesizerBase

_logger = logging.getLogger("LinuxKeySynthesizer")


class LinuxKeySynthesizer(KeySynthesizerBase):
    """
    Linux key synthesis via xdotool (X11) or ydotool (Wayland).

    Attributes:
        _tool: Name of the detected tool (``"xdotool"`` or ``"ydotool"``),
               or ``None`` if neither is available.
    """

    def __init__(self) -> None:
        self._tool = self._detect_tool()
        if self._tool:
            _logger.info("Linux key synthesizer ready: %s", self._tool)
        else:
            _logger.warning(
                "No key synthesis tool found. "
                "Install xdotool (X11) or ydotool (Wayland)."
            )

    # ------------------------------------------------------------------ #
    #  Detection
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_tool() -> Optional[str]:
        """
        Detect the best available key synthesis tool.

        Prefers xdotool on X11, ydotool on Wayland.

        Returns:
            ``"xdotool"``, ``"ydotool"``, or ``None``.
        """
        is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))

        if is_wayland:
            # Prefer ydotool on Wayland
            if shutil.which("ydotool"):
                return "ydotool"
            if shutil.which("xdotool"):
                _logger.warning(
                    "Wayland detected but only xdotool found. "
                    "Some features may not work. Install ydotool."
                )
                return "xdotool"
        else:
            # X11 — prefer xdotool
            if shutil.which("xdotool"):
                return "xdotool"
            if shutil.which("ydotool"):
                return "ydotool"

        return None

    # ------------------------------------------------------------------ #
    #  Interface implementation
    # ------------------------------------------------------------------ #

    def is_available(self) -> bool:
        """True if xdotool or ydotool is on $PATH."""
        return self._tool is not None

    def backend_name(self) -> str:
        """Return ``"xdotool"``, ``"ydotool"``, or ``"none"``."""
        return self._tool or "none"

    def send_key(
        self,
        key_name: str,
        modifiers: Optional[List[str]] = None,
    ) -> None:
        """
        Send a single key event, optionally with modifier keys.

        For xdotool the modifiers are joined with ``+`` to form a chord
        string (e.g. ``ctrl+shift+c``).

        Args:
            key_name: Platform-neutral key name (xdotool keysym).
            modifiers: Optional list of ``"ctrl"``, ``"alt"``, ``"shift"``,
                       ``"win"`` strings.
        """
        if not self._tool:
            _logger.warning("No synth tool — cannot send key: %s", key_name)
            return

        modifiers = modifiers or []
        # Map "win" → "super" for xdotool
        mapped_mods = [("super" if m == "win" else m) for m in modifiers]

        try:
            if self._tool == "xdotool":
                if mapped_mods:
                    combo = "+".join(mapped_mods + [key_name])
                    self._log_send(f"xdotool key {combo}")
                    subprocess.Popen(
                        ["xdotool", "key", "--clearmodifiers", combo],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    self._log_send(f"xdotool key {key_name}")
                    subprocess.Popen(
                        ["xdotool", "key", "--clearmodifiers", key_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            elif self._tool == "ydotool":
                self._log_send(f"ydotool key {key_name}")
                subprocess.Popen(
                    ["ydotool", "key", key_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            _logger.error("Failed to send key %s: %s", key_name, e)

    def send_text(self, text: str) -> None:
        """
        Type a string of text using ``xdotool type``.

        Falls back to sending individual key events on ydotool.

        Args:
            text: The Unicode string to type.
        """
        if not self._tool:
            return

        try:
            if self._tool == "xdotool":
                self._log_send(f"xdotool type '{text}'")
                subprocess.Popen(
                    ["xdotool", "type", "--clearmodifiers", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._tool == "ydotool":
                self._log_send(f"ydotool type '{text}'")
                subprocess.Popen(
                    ["ydotool", "type", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            _logger.error("Failed to type text: %s", e)

    def hold_modifier(self, key_name: str) -> None:
        """Send a modifier key-down so it stays held at the OS level."""
        if not self._tool:
            return
        mapped = "super" if key_name == "win" else key_name
        try:
            if self._tool == "xdotool":
                self._log_send(f"xdotool keydown {mapped}")
                subprocess.Popen(
                    ["xdotool", "keydown", mapped],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._tool == "ydotool":
                self._log_send(f"ydotool key --key-down {mapped}")
                subprocess.Popen(
                    ["ydotool", "key", "--key-down", mapped],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            _logger.error("Failed to hold modifier %s: %s", key_name, e)

    def release_modifier(self, key_name: str) -> None:
        """Send a modifier key-up to release a held modifier."""
        if not self._tool:
            return
        mapped = "super" if key_name == "win" else key_name
        try:
            if self._tool == "xdotool":
                self._log_send(f"xdotool keyup {mapped}")
                subprocess.Popen(
                    ["xdotool", "keyup", mapped],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._tool == "ydotool":
                self._log_send(f"ydotool key --key-up {mapped}")
                subprocess.Popen(
                    ["ydotool", "key", "--key-up", mapped],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            _logger.error("Failed to release modifier %s: %s", key_name, e)

    def send_combination(self, keys: List[str]) -> None:
        """
        Send a multi-key chord (e.g. Ctrl+Alt+Delete).

        Args:
            keys: Ordered list of key names. Modifiers first, action key
                  last.
        """
        if not keys:
            return
        # Last key is the action key; everything before is a modifier
        *modifiers, action_key = keys
        self.send_key(action_key, modifiers=modifiers if modifiers else None)
