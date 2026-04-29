"""Tests for the platform abstraction layer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from src.platform import CURRENT_PLATFORM, get_config_dir, get_model_dir
from src.platform.base import KeySynthesizerBase


class TestPlatformDetection:
    """Platform identification."""

    def test_current_platform_is_string(self):
        assert isinstance(CURRENT_PLATFORM, str)

    def test_current_platform_is_valid(self):
        assert CURRENT_PLATFORM in ("windows", "linux", "unsupported")

    def test_current_platform_matches_sys(self):
        if sys.platform == "win32":
            assert CURRENT_PLATFORM == "windows"
        elif sys.platform.startswith("linux"):
            assert CURRENT_PLATFORM == "linux"


class TestFactory:
    """create_key_synthesizer factory."""

    def test_factory_returns_synthesizer(self):
        from src.platform import create_key_synthesizer
        synth = create_key_synthesizer()
        assert isinstance(synth, KeySynthesizerBase)

    def test_factory_returns_correct_backend(self):
        from src.platform import create_key_synthesizer
        synth = create_key_synthesizer()
        if CURRENT_PLATFORM == "windows":
            from src.platform.windows import WindowsKeySynthesizer
            assert isinstance(synth, WindowsKeySynthesizer)
        elif CURRENT_PLATFORM == "linux":
            from src.platform.linux import LinuxKeySynthesizer
            assert isinstance(synth, LinuxKeySynthesizer)

    def test_synthesizer_has_backend_name(self):
        from src.platform import create_key_synthesizer
        synth = create_key_synthesizer()
        name = synth.backend_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_synthesizer_reports_availability(self):
        from src.platform import create_key_synthesizer
        synth = create_key_synthesizer()
        # Just verify it returns bool, not that it's True/False
        assert isinstance(synth.is_available(), bool)


class TestConfigPaths:
    """Configuration directory helpers."""

    def test_get_config_dir_returns_path(self):
        result = get_config_dir()
        assert isinstance(result, Path)

    def test_get_config_dir_exists(self):
        result = get_config_dir()
        assert result.exists()

    def test_get_config_dir_correct_platform(self):
        result = get_config_dir()
        if CURRENT_PLATFORM == "windows":
            assert "alpha-osk" in str(result)
        elif CURRENT_PLATFORM == "linux":
            assert ".config/alpha-osk" in str(result)

    def test_get_model_dir_returns_path(self):
        result = get_model_dir()
        assert isinstance(result, Path)

    def test_get_model_dir_is_under_config(self):
        config = get_config_dir()
        model = get_model_dir()
        assert str(model).startswith(str(config))

    def test_get_model_dir_exists(self):
        result = get_model_dir()
        assert result.exists()


class TestBaseSynthesizerInterface:
    """Verify the ABC contract."""

    def test_cannot_instantiate_base(self):
        with pytest.raises(TypeError):
            KeySynthesizerBase()

    def test_base_has_required_methods(self):
        methods = ["is_available", "backend_name", "send_key", "send_text", "send_combination"]
        for method in methods:
            assert hasattr(KeySynthesizerBase, method)


class TestLinuxReplaceText:
    """LinuxKeySynthesizer.replace_text() — atomic select-and-replace.

    These tests stub the subprocess runner and a synthesizer tool so they
    run on any OS (including the Windows CI lane, where xdotool is absent).
    """

    def _make_synth(self, tool: str, monkeypatch):
        from src.platform import linux as linux_mod

        calls: list[list[str]] = []
        monkeypatch.setattr(linux_mod, "_run", lambda cmd: calls.append(cmd))
        synth = linux_mod.LinuxKeySynthesizer.__new__(linux_mod.LinuxKeySynthesizer)
        synth._tool = tool
        return synth, calls

    def test_xdotool_chain_is_single_invocation(self, monkeypatch):
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.replace_text(3, "hello")
        # One `key` invocation carrying all 3 chords, plus one `type`.
        assert calls[0] == [
            "xdotool", "key", "--clearmodifiers",
            "shift+Left", "shift+Left", "shift+Left",
        ]
        assert calls[1] == ["xdotool", "type", "--clearmodifiers", "hello"]
        assert len(calls) == 2

    def test_xdotool_zero_backspace_skips_selection(self, monkeypatch):
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.replace_text(0, "hi")
        # No shift+Left chain; falls through to send_text.
        assert calls == [["xdotool", "type", "--clearmodifiers", "hi"]]

    def test_xdotool_empty_text_still_selects(self, monkeypatch):
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.replace_text(2, "")
        assert calls == [[
            "xdotool", "key", "--clearmodifiers",
            "shift+Left", "shift+Left",
        ]]

    def test_ydotool_frames_shift_around_lefts(self, monkeypatch):
        synth, calls = self._make_synth("ydotool", monkeypatch)
        synth.replace_text(2, "hi")
        assert calls == [
            ["ydotool", "key", "--key-down", "shift"],
            ["ydotool", "key", "Left"],
            ["ydotool", "key", "Left"],
            ["ydotool", "key", "--key-up", "shift"],
            ["ydotool", "type", "hi"],
        ]

    def test_no_tool_is_silent_noop(self, monkeypatch):
        synth, calls = self._make_synth(None, monkeypatch)
        synth.replace_text(3, "x")
        assert calls == []


class TestLinuxSendKeyPunctuationChord:
    """Modifier+punctuation chords on Linux must rewrite the literal
    char to its X11 keysym name — xdotool's chord parser uses ``+`` as
    the separator, so ``ctrl+-`` is malformed and the canonical form
    ``ctrl+minus`` is what triggers the app's shortcut handler.
    """

    def _make_synth(self, tool: str, monkeypatch):
        from src.platform import linux as linux_mod

        calls: list[list[str]] = []
        monkeypatch.setattr(linux_mod, "_run", lambda cmd: calls.append(cmd))
        synth = linux_mod.LinuxKeySynthesizer.__new__(linux_mod.LinuxKeySynthesizer)
        synth._tool = tool
        return synth, calls

    def test_xdotool_ctrl_minus_uses_keysym(self, monkeypatch):
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("-", modifiers=["ctrl"])
        assert calls == [["xdotool", "key", "--clearmodifiers", "ctrl+minus"]]

    def test_xdotool_ctrl_equals_uses_keysym(self, monkeypatch):
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("=", modifiers=["ctrl"])
        assert calls == [["xdotool", "key", "--clearmodifiers", "ctrl+equal"]]

    def test_xdotool_ctrl_slash_uses_keysym(self, monkeypatch):
        # VS Code / many editors: comment toggle.
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("/", modifiers=["ctrl"])
        assert calls == [["xdotool", "key", "--clearmodifiers", "ctrl+slash"]]

    def test_xdotool_letter_passes_through(self, monkeypatch):
        # Letters need no remap — xdotool accepts ``a`` verbatim.
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("a", modifiers=["ctrl"])
        assert calls == [["xdotool", "key", "--clearmodifiers", "ctrl+a"]]

    def test_xdotool_digit_passes_through(self, monkeypatch):
        # Digits need no remap either.
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("1", modifiers=["ctrl"])
        assert calls == [["xdotool", "key", "--clearmodifiers", "ctrl+1"]]

    def test_xdotool_no_modifiers_still_remaps(self, monkeypatch):
        # ``xdotool key -`` is also ambiguous — the dash looks like a
        # flag.  Always remap to the keysym name regardless of chord.
        synth, calls = self._make_synth("xdotool", monkeypatch)
        synth.send_key("-")
        assert calls == [["xdotool", "key", "--clearmodifiers", "minus"]]

    def test_ydotool_ctrl_minus_remaps(self, monkeypatch):
        # ydotool would see ``-`` as a CLI flag start; keysym name
        # avoids that and is also closer to a real key name.
        synth, calls = self._make_synth("ydotool", monkeypatch)
        synth.send_key("-", modifiers=["ctrl"])
        assert calls == [["ydotool", "key", "minus"]]


class TestWindowsReplaceText:
    """WindowsKeySynthesizer.replace_text() — terminal-aware select-and-replace.

    Bypasses ``__init__`` (which loads user32.dll) and stubs the event
    builders so the tests can assert the dispatch behavior on any OS,
    including the Linux CI lane.
    """

    def _make_synth(self, foreground_class: str):
        from src.platform import windows as win_mod

        synth = win_mod.WindowsKeySynthesizer.__new__(win_mod.WindowsKeySynthesizer)
        captured: list = []
        synth._inject = lambda events: captured.append(list(events))
        synth._make_key_event = lambda vk, key_down: ("vk", vk, key_down)
        synth._make_unicode_events = lambda c: [("uni", c)]
        # Bypass GetForegroundWindow / GetClassNameW directly — mocking
        # them via ctypes is brittle off-Windows.
        synth._get_foreground_window_class = lambda: foreground_class
        return synth, captured

    def test_terminal_uses_backspace_path(self):
        from src.platform.windows import VK_BACK
        synth, captured = self._make_synth("ConsoleWindowClass")
        synth.replace_text(3, "Ow")
        assert captured == [[
            ("vk", VK_BACK, True),  ("vk", VK_BACK, False),
            ("vk", VK_BACK, True),  ("vk", VK_BACK, False),
            ("vk", VK_BACK, True),  ("vk", VK_BACK, False),
            ("uni", "O"), ("uni", "w"),
        ]]

    def test_windows_terminal_class_also_uses_backspace(self):
        from src.platform.windows import VK_BACK
        synth, captured = self._make_synth("CASCADIA_HOSTING_WINDOW_CLASS")
        synth.replace_text(1, "x")
        assert captured == [[
            ("vk", VK_BACK, True), ("vk", VK_BACK, False),
            ("uni", "x"),
        ]]

    def test_mintty_class_also_uses_backspace(self):
        from src.platform.windows import VK_BACK
        synth, captured = self._make_synth("mintty")
        synth.replace_text(2, "")
        assert captured == [[
            ("vk", VK_BACK, True), ("vk", VK_BACK, False),
            ("vk", VK_BACK, True), ("vk", VK_BACK, False),
        ]]

    def test_non_terminal_uses_shift_left_path(self):
        from src.platform.windows import VK_LEFT, VK_SHIFT
        synth, captured = self._make_synth("Chrome_WidgetWin_1")
        synth.replace_text(2, "hi")
        assert captured == [[
            ("vk", VK_SHIFT, True),
            ("vk", VK_LEFT, True),  ("vk", VK_LEFT, False),
            ("vk", VK_LEFT, True),  ("vk", VK_LEFT, False),
            ("vk", VK_SHIFT, False),
            ("uni", "h"), ("uni", "i"),
        ]]

    def test_zero_backspace_in_terminal_just_types(self):
        synth, captured = self._make_synth("ConsoleWindowClass")
        synth.replace_text(0, "abc")
        assert captured == [[("uni", "a"), ("uni", "b"), ("uni", "c")]]

    def test_zero_backspace_outside_terminal_skips_selection(self):
        from src.platform.windows import VK_SHIFT
        synth, captured = self._make_synth("Notepad")
        synth.replace_text(0, "abc")
        # No Shift bookends when there's nothing to select.
        events = captured[0]
        assert all(e[0] == "uni" for e in events)
        assert ("vk", VK_SHIFT, True) not in events

    def test_unknown_class_treated_as_non_terminal(self):
        from src.platform.windows import VK_SHIFT
        synth, captured = self._make_synth("")
        synth.replace_text(1, "x")
        # Empty class name (e.g. GetClassNameW failed) → safe default
        # is the existing Shift+Left path, not BackSpace.
        assert ("vk", VK_SHIFT, True) in captured[0]


class TestWindowsSendKeyPunctuationChord:
    """Modifier+punctuation chords (Ctrl+-, Ctrl+=) must produce a real
    VK keystroke, not a Unicode injection — apps' shortcut handlers
    listen for WM_KEYDOWN(VK_OEM_*), and Unicode events alone don't
    trigger zoom/etc. when a modifier is held.
    """

    def _make_synth(self, vk_scan_results: dict):
        from src.platform import windows as win_mod

        synth = win_mod.WindowsKeySynthesizer.__new__(win_mod.WindowsKeySynthesizer)
        captured: list = []
        synth._inject = lambda events: captured.append(list(events))
        synth._make_key_event = lambda vk, key_down: ("vk", vk, key_down)
        synth._make_unicode_events = lambda c: [("uni", c)]

        class _StubUser32:
            def VkKeyScanW(self_inner, ch):
                return vk_scan_results.get(ch, -1)
        synth._user32 = _StubUser32()
        return synth, captured

    def test_ctrl_minus_uses_vk_oem_minus(self):
        from src.platform.windows import VK_CONTROL
        # US-layout VkKeyScanW('-') = (low=VK_OEM_MINUS=0xBD, high=0)
        synth, captured = self._make_synth({"-": 0x00BD})
        synth.send_key("-", modifiers=["ctrl"])
        # Ctrl-down → VK_OEM_MINUS-down → VK_OEM_MINUS-up → Ctrl-up,
        # all virtual-key events (no Unicode injection).
        assert captured == [[
            ("vk", VK_CONTROL, True),
            ("vk", 0xBD, True), ("vk", 0xBD, False),
            ("vk", VK_CONTROL, False),
        ]]

    def test_ctrl_equals_uses_vk_oem_plus(self):
        from src.platform.windows import VK_CONTROL
        # US-layout VkKeyScanW('=') = (low=VK_OEM_PLUS=0xBB, high=0)
        synth, captured = self._make_synth({"=": 0x00BB})
        synth.send_key("=", modifiers=["ctrl"])
        assert captured == [[
            ("vk", VK_CONTROL, True),
            ("vk", 0xBB, True), ("vk", 0xBB, False),
            ("vk", VK_CONTROL, False),
        ]]

    def test_shift_required_char_prepends_shift(self):
        from src.platform.windows import VK_CONTROL, VK_SHIFT
        # US-layout VkKeyScanW('+') = (low=VK_OEM_PLUS=0xBB, high=1) —
        # '+' is Shift+'=' physically, so the synth must add a Shift
        # press around the chord.
        synth, captured = self._make_synth({"+": 0x01BB})
        synth.send_key("+", modifiers=["ctrl"])
        # Shift gets prepended, so order is Shift→Ctrl press, then key,
        # then Ctrl→Shift release.
        assert captured == [[
            ("vk", VK_SHIFT, True),
            ("vk", VK_CONTROL, True),
            ("vk", 0xBB, True), ("vk", 0xBB, False),
            ("vk", VK_CONTROL, False),
            ("vk", VK_SHIFT, False),
        ]]

    def test_unmappable_char_falls_back_to_unicode(self):
        from src.platform.windows import VK_CONTROL
        # VkKeyScanW returns -1 for chars not on the active layout.
        synth, captured = self._make_synth({})  # everything → -1
        synth.send_key("ñ", modifiers=["ctrl"])
        # Ctrl is still wrapped around the keystroke; the action key
        # falls through to the Unicode path.
        assert captured == [[
            ("vk", VK_CONTROL, True),
            ("uni", "ñ"),
            ("vk", VK_CONTROL, False),
        ]]


class TestPlatformInfo:
    """get_platform_info diagnostic."""

    def test_platform_info_returns_dict(self):
        from src.platform import get_platform_info
        info = get_platform_info()
        assert isinstance(info, dict)

    def test_platform_info_has_platform(self):
        from src.platform import get_platform_info
        info = get_platform_info()
        assert "platform" in info
        assert info["platform"] == CURRENT_PLATFORM

    def test_platform_info_has_python(self):
        from src.platform import get_platform_info
        info = get_platform_info()
        assert "python" in info
