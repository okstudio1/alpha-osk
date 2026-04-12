"""
Password Field Detection
=========================

Detects whether the currently focused UI element is a password field,
so the on-screen keyboard can suppress prediction and learning to
protect sensitive input.

Windows
-------
Uses the UI Automation COM interface (``IUIAutomation``) via ctypes to
query ``UIA_IsPasswordPropertyId`` on the focused element.  This works
for native Win32 controls **and** web browsers (Chrome, Edge, Firefox
all expose password state through UIA).  Falls back to the Win32
``EM_GETPASSWORDCHAR`` message if UIA fails to initialise.

Linux
-----
Not yet implemented — returns False.  Users should use the manual
privacy-mode toggle for now.

Dependencies: none beyond Python's standard library (``ctypes``).
"""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import Any, Optional, Protocol

_logger = logging.getLogger("PasswordDetect")


class _Detector(Protocol):
    def check(self) -> bool: ...


# ====================================================================== #
#  Public API
# ====================================================================== #

_detector: Optional[_Detector] = None  # lazy-initialised


def is_password_field() -> bool:
    """Return True if the currently focused UI element is a password field."""
    global _detector
    if _detector is None:
        _detector = _create_detector()
    try:
        return _detector.check()
    except Exception:
        return False


def _create_detector() -> _Detector:
    if sys.platform == "win32":
        det = _WindowsUIADetector()
        if det.available:
            _logger.info("Password detection: Windows UIA")
            return det
        _logger.info("Password detection: Windows Win32 fallback")
        return _WindowsWin32Detector()
    _logger.info("Password detection: not available on this platform")
    return _NullDetector()


# ====================================================================== #
#  Null detector (unsupported platforms)
# ====================================================================== #

class _NullDetector:
    def check(self) -> bool:
        return False


# ====================================================================== #
#  Windows — UI Automation via COM (ctypes)
# ====================================================================== #

if sys.platform == "win32":
    import ctypes.wintypes as wintypes

    class _GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    # CUIAutomation {ff48dba4-60ef-4201-aa87-54103eef594e}
    _CLSID_CUIAutomation = _GUID(
        0xFF48DBA4, 0x60EF, 0x4201,
        (ctypes.c_ubyte * 8)(0xAA, 0x87, 0x54, 0x10, 0x3E, 0xEF, 0x59, 0x4E),
    )
    # IUIAutomation {30cbe57d-d9d0-452a-ab13-7ac5ac4825ee}
    _IID_IUIAutomation = _GUID(
        0x30CBE57D, 0xD9D0, 0x452A,
        (ctypes.c_ubyte * 8)(0xAB, 0x13, 0x7A, 0xC5, 0xAC, 0x48, 0x25, 0xEE),
    )

    _UIA_IsPasswordPropertyId = 30019
    _VT_BOOL = 11

    class _VARIANT(ctypes.Structure):
        """Minimal COM VARIANT (24 bytes on 64-bit)."""
        _fields_ = [
            ("vt", ctypes.c_ushort),
            ("wReserved1", ctypes.c_ushort),
            ("wReserved2", ctypes.c_ushort),
            ("wReserved3", ctypes.c_ushort),
            ("val", ctypes.c_longlong),
            ("_pad", ctypes.c_longlong),
        ]

    def _vtable_func(obj: ctypes.c_void_p, index: int, restype: type,
                     *argtypes: type) -> Any:
        """Get a function pointer from a COM object's vtable."""
        vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.c_void_p))[0]
        fptr = ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))[index]
        proto = ctypes.CFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
        return proto(fptr)

    def _com_release(obj: ctypes.c_void_p) -> None:
        """Call IUnknown::Release (vtable index 2)."""
        if obj:
            try:
                _vtable_func(obj, 2, ctypes.c_ulong)(obj)
            except Exception:
                pass

    class _WindowsUIADetector:
        """Detect password fields via IUIAutomation COM interface."""

        def __init__(self) -> None:
            self.available = False
            self._automation = ctypes.c_void_p()

            try:
                ole32 = ctypes.windll.ole32
                hr = ole32.CoInitializeEx(None, 0)
                if hr not in (0, 1):  # S_OK or S_FALSE
                    return

                hr = ole32.CoCreateInstance(
                    ctypes.byref(_CLSID_CUIAutomation), None, 1,  # CLSCTX_INPROC_SERVER
                    ctypes.byref(_IID_IUIAutomation),
                    ctypes.byref(self._automation),
                )
                if hr != 0 or not self._automation:
                    return

                self.available = True
            except Exception as exc:
                _logger.debug("UIA init failed: %s", exc)

        def check(self) -> bool:
            if not self.available or not self._automation:
                return False

            element = ctypes.c_void_p()
            try:
                # IUIAutomation::GetFocusedElement — vtable index 8
                get_focused = _vtable_func(
                    self._automation, 8,
                    ctypes.c_long, ctypes.POINTER(ctypes.c_void_p),
                )
                hr = get_focused(self._automation, ctypes.byref(element))
                if hr != 0 or not element:
                    return False

                # IUIAutomationElement::GetCurrentPropertyValue — vtable index 10
                variant = _VARIANT()
                get_prop = _vtable_func(
                    element, 10,
                    ctypes.c_long, ctypes.c_int, ctypes.POINTER(_VARIANT),
                )
                hr = get_prop(element, _UIA_IsPasswordPropertyId, ctypes.byref(variant))
                if hr != 0:
                    return False

                return bool(variant.vt == _VT_BOOL and variant.val != 0)

            except Exception:
                return False
            finally:
                _com_release(element)

    # ------------------------------------------------------------------
    #  Win32 fallback (EM_GETPASSWORDCHAR)
    # ------------------------------------------------------------------

    _EM_GETPASSWORDCHAR = 0x00D2

    class _GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    class _WindowsWin32Detector:
        """Fallback: detect password edit controls via EM_GETPASSWORDCHAR."""

        def __init__(self) -> None:
            self._user32 = ctypes.windll.user32

        def check(self) -> bool:
            try:
                hwnd = self._user32.GetForegroundWindow()
                if not hwnd:
                    return False

                tid = self._user32.GetWindowThreadProcessId(hwnd, None)
                if not tid:
                    return False

                info = _GUITHREADINFO()
                info.cbSize = ctypes.sizeof(info)
                if not self._user32.GetGUIThreadInfo(tid, ctypes.byref(info)):
                    return False

                focused = info.hwndFocus
                if not focused:
                    return False

                # EM_GETPASSWORDCHAR returns the mask char (e.g. '*') or 0
                result: int = self._user32.SendMessageW(
                    focused, _EM_GETPASSWORDCHAR, 0, 0
                )
                return result != 0

            except Exception:
                return False
