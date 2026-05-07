"""Tests for the post-update relauncher helper."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from src import _update_relauncher as relauncher


class TestProcessAlive:
    """_process_alive — cross-platform PID check."""

    def test_zero_pid_returns_false(self):
        assert relauncher._process_alive(0) is False

    def test_negative_pid_returns_false(self):
        assert relauncher._process_alive(-1) is False

    def test_current_pid_returns_true(self):
        # Our own process is definitely alive.
        import os
        assert relauncher._process_alive(os.getpid()) is True

    def test_nonexistent_pid_returns_false(self):
        # PID 999_999_999 is virtually guaranteed to be unused on every
        # supported platform.
        assert relauncher._process_alive(999_999_999) is False


class TestWaitForParentExit:
    """_wait_for_parent_exit — polls until process is gone or timeout."""

    def test_immediate_return_when_already_dead(self):
        with patch.object(relauncher, "_process_alive", return_value=False):
            start = time.monotonic()
            ok = relauncher._wait_for_parent_exit(12345, timeout_s=5.0)
            elapsed = time.monotonic() - start
        assert ok is True
        # Should be near-instant.
        assert elapsed < 0.5

    def test_timeout_when_parent_never_exits(self):
        with patch.object(relauncher, "_process_alive", return_value=True):
            ok = relauncher._wait_for_parent_exit(12345, timeout_s=0.6)
        assert ok is False


class TestWaitForNewExe:
    """_wait_for_new_exe — confirms the install actually wrote a new exe."""

    def test_returns_true_when_file_appears_with_fresh_mtime(self, tmp_path):
        target = tmp_path / "alpha-osk.exe"
        # Write the file with an mtime *after* a fixed reference.
        target.write_bytes(b"binary contents")
        ref = time.time() - 60  # parent died a minute ago
        ok = relauncher._wait_for_new_exe(target, ref, timeout_s=2.0)
        assert ok is True

    def test_rejects_stale_mtime(self, tmp_path):
        target = tmp_path / "alpha-osk.exe"
        target.write_bytes(b"binary contents")
        # Pretend the parent died well after the file was written —
        # that means the file is the OLD exe.
        ref = time.time() + 60
        ok = relauncher._wait_for_new_exe(target, ref, timeout_s=0.6)
        assert ok is False

    def test_returns_true_when_file_exists_and_no_reference(self, tmp_path):
        target = tmp_path / "alpha-osk.exe"
        target.write_bytes(b"x")
        ok = relauncher._wait_for_new_exe(target, None, timeout_s=2.0)
        assert ok is True

    def test_zero_byte_file_is_rejected(self, tmp_path):
        target = tmp_path / "alpha-osk.exe"
        target.touch()
        ok = relauncher._wait_for_new_exe(target, None, timeout_s=0.6)
        assert ok is False

    def test_timeout_when_file_never_appears(self, tmp_path):
        target = tmp_path / "alpha-osk.exe"
        ok = relauncher._wait_for_new_exe(target, None, timeout_s=0.6)
        assert ok is False


class TestWriteHandoff:
    """_write_handoff — drops a JSON breadcrumb for the new OSK to read."""

    def test_writes_expected_fields(self, tmp_path):
        relauncher._write_handoff(tmp_path, "1.0.16", "1.0.15")
        path = tmp_path / "update_handoff.json"
        assert path.is_file()
        data = json.loads(path.read_text())
        assert data["version"] == "1.0.16"
        assert data["previous_version"] == "1.0.15"
        assert isinstance(data["completed_at"], (int, float))
        # Completed-at must be a recent timestamp.
        assert abs(data["completed_at"] - time.time()) < 5

    def test_creates_config_dir_if_missing(self, tmp_path):
        nested = tmp_path / "nested" / "config"
        relauncher._write_handoff(nested, "1.0.16", "1.0.15")
        assert (nested / "update_handoff.json").is_file()


class TestRunRelauncherIntegration:
    """End-to-end-ish: simulate the full flow with mocked subprocess + PID."""

    def test_happy_path(self, tmp_path):
        # Stage a "freshly installed" exe with an mtime in the future
        # so the relauncher's "newer than parent_death_time" check
        # passes deterministically. In production the installer's file
        # write happens after the parent's death, so mtime > death by
        # whatever the install took (seconds at minimum).
        import os as _os
        target_exe = tmp_path / "alpha-osk.exe"
        target_exe.write_bytes(b"freshly installed")
        future_mtime = time.time() + 3600
        _os.utime(target_exe, (future_mtime, future_mtime))
        config_dir = tmp_path / "config"

        argv = [
            "alpha-osk.exe",
            "--update-relauncher",
            "--parent-pid", "999999999",  # already dead
            "--new-version", "1.0.16",
            "--previous-version", "1.0.15",
            "--target-exe", str(target_exe),
            "--config-dir", str(config_dir),
        ]

        # Bypass the 5-second installer-grace sleep so the test is fast.
        with patch.object(relauncher, "_INSTALLER_GRACE_S", 0), \
             patch.object(relauncher, "_NEW_EXE_TIMEOUT_S", 2):
            with patch.object(relauncher, "_launch_new_osk", return_value=True) as mock_launch:
                rc = relauncher.run_relauncher(argv)

        assert rc == 0
        mock_launch.assert_called_once()
        # Handoff was written.
        handoff = config_dir / "update_handoff.json"
        assert handoff.is_file()
        data = json.loads(handoff.read_text())
        assert data["version"] == "1.0.16"
        assert data["previous_version"] == "1.0.15"

    def test_returns_error_when_parent_never_dies(self, tmp_path):
        target_exe = tmp_path / "alpha-osk.exe"
        target_exe.write_bytes(b"x")
        config_dir = tmp_path / "config"

        argv = [
            "alpha-osk.exe",
            "--update-relauncher",
            "--parent-pid", "12345",
            "--new-version", "1.0.16",
            "--previous-version", "1.0.15",
            "--target-exe", str(target_exe),
            "--config-dir", str(config_dir),
        ]

        with patch.object(relauncher, "_PARENT_EXIT_TIMEOUT_S", 0.5), \
             patch.object(relauncher, "_process_alive", return_value=True):
            rc = relauncher.run_relauncher(argv)

        assert rc == 2  # parent-exit timeout

    def test_returns_error_when_new_exe_never_appears(self, tmp_path):
        # Path doesn't exist — install "fails" to write.
        target_exe = tmp_path / "alpha-osk.exe"
        config_dir = tmp_path / "config"

        argv = [
            "alpha-osk.exe",
            "--update-relauncher",
            "--parent-pid", "999999999",
            "--new-version", "1.0.16",
            "--previous-version", "1.0.15",
            "--target-exe", str(target_exe),
            "--config-dir", str(config_dir),
        ]

        with patch.object(relauncher, "_INSTALLER_GRACE_S", 0), \
             patch.object(relauncher, "_NEW_EXE_TIMEOUT_S", 0.5):
            rc = relauncher.run_relauncher(argv)

        assert rc == 3  # new-exe timeout

    def test_returns_error_when_launch_fails(self, tmp_path):
        import os as _os
        target_exe = tmp_path / "alpha-osk.exe"
        target_exe.write_bytes(b"x")
        future_mtime = time.time() + 3600
        _os.utime(target_exe, (future_mtime, future_mtime))
        config_dir = tmp_path / "config"

        argv = [
            "alpha-osk.exe",
            "--update-relauncher",
            "--parent-pid", "999999999",
            "--new-version", "1.0.16",
            "--previous-version", "1.0.15",
            "--target-exe", str(target_exe),
            "--config-dir", str(config_dir),
        ]

        with patch.object(relauncher, "_INSTALLER_GRACE_S", 0), \
             patch.object(relauncher, "_NEW_EXE_TIMEOUT_S", 2), \
             patch.object(relauncher, "_launch_new_osk", return_value=False):
            rc = relauncher.run_relauncher(argv)

        assert rc == 4  # launch failed
        # Handoff should NOT be written if launch failed — would be
        # misleading on the next manual launch.
        assert not (config_dir / "update_handoff.json").is_file()
