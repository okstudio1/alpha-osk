"""Detached helper that relaunches Alpha-OSK after an auto-update.

Background
==========

The auto-updater downloads + verifies + launches the signed NSIS
installer with elevation (UAC). The installer's ``customInit`` taskkills
the running ``alpha-osk.exe`` so the new exe can be written. Without a
relaunch, the user is left with no keyboard until they manually find
the Start Menu — a hard problem for the accessibility audience this
keyboard serves.

The previous mechanism was a one-line ``Exec '"$WINDIR\\explorer.exe"
"$INSTDIR\\alpha-osk.exe"'`` inside ``installer.nsh``. That trick
works in theory (explorer running at the user's medium IL spawns the
new exe at medium IL too) but in practice fails silently: the elevated
installer's ``Exec`` ends up handing off across the IL boundary, and
Windows can refuse the relay without surfacing any error. Result:
"the new keyboard never opens" — reported by users.

This module is the replacement. It runs as a detached process owned by
the user session (spawned by the updater BEFORE elevation kicks in),
polls for the install to finish, then launches the new exe directly.
Because the helper was already running at user IL when the elevated
installer started, there is no IL handoff to fail.

Flow
====

1. Wait for the parent ``alpha-osk.exe`` to exit (the installer's
   taskkill in ``customInit``).
2. Wait an extra grace period for the installer to finish writing
   files. Polling ``$INSTDIR\\alpha-osk.exe`` for an mtime newer than
   parent-death is the strongest signal we have without parsing PE
   headers; "exists + readable + non-zero size" is the floor.
3. Launch the new exe via ``subprocess.Popen`` from the user session.
4. Write ``update_handoff.json`` next to ``$APPDATA/alpha-osk/`` so the
   newly launched OSK can flash a "✓ Updated to vX.Y.Z" toast.

Failure modes are deliberately silent — there is no UI surface to
report into and the user already lacks a keyboard. Everything goes to
the relauncher log file at ``$APPDATA/alpha-osk/relauncher.log`` for
post-mortem.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("UpdateRelauncher")

# Polling cadence — fast enough to feel snappy, slow enough not to peg
# a CPU core. Total budget for the whole flow is ~3 minutes; in practice
# the install finishes inside 30 s.
_POLL_INTERVAL_S = 0.5
_PARENT_EXIT_TIMEOUT_S = 60
_NEW_EXE_TIMEOUT_S = 180
_INSTALLER_GRACE_S = 5  # after parent dies, wait for installer file copy


def _configure_log(log_dir: Path) -> None:
    """Set up a file logger for the detached process.

    Stdout/stderr aren't visible (the helper runs hidden), so log
    aggressively to a known path. Failures during log setup are
    swallowed — there's no fallback surface.
    """
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "relauncher.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s",
        ))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    except Exception:
        pass


def _process_alive(pid: int) -> bool:
    """Cross-platform "is this PID still around" check.

    Uses ``OpenProcess`` on Windows (the cheapest signal) and
    ``os.kill(pid, 0)`` on POSIX. Returns False on any error — a dead
    process is the safer assumption since we want the relauncher to
    proceed once the OSK is gone.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid,
            )
            if not handle:
                return False
            # GetExitCodeProcess returns STILL_ACTIVE (259) for a live
            # process; any other value means it has exited.
            STILL_ACTIVE = 259
            exit_code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            if not ok:
                return False
            return exit_code.value == STILL_ACTIVE
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _wait_for_parent_exit(pid: int, timeout_s: float) -> bool:
    """Block until the parent OSK process has exited or we time out."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not _process_alive(pid):
            return True
        time.sleep(_POLL_INTERVAL_S)
    return False


def _wait_for_new_exe(
    target: Path, after_mtime: Optional[float], timeout_s: float,
) -> bool:
    """Block until ``target`` exists and looks like the freshly-written exe.

    ``after_mtime`` is the parent OSK's death time; an exe whose mtime
    predates that is the OLD exe (installer hasn't finished). Waiting
    for ``mtime > after_mtime`` is a much stronger signal than just
    "file exists." If we don't have a death time, fall back to the
    weaker existence-and-non-empty check.
    """
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            if target.is_file():
                stat = target.stat()
                if stat.st_size > 0:
                    if after_mtime is None or stat.st_mtime > after_mtime:
                        return True
        except OSError:
            pass
        time.sleep(_POLL_INTERVAL_S)
    return False


def _launch_new_osk(exe_path: Path) -> bool:
    """Spawn the freshly-installed ``alpha-osk.exe`` as a detached process.

    Returns True on launch success (i.e. ``Popen`` didn't raise). Note
    that "spawn succeeded" is not "OSK is running" — but if Popen fails
    we know to log the error rather than silently exiting.
    """
    try:
        flags = 0
        if sys.platform == "win32":
            # Detach so we can exit immediately. CREATE_NEW_PROCESS_GROUP
            # also prevents Ctrl+C in any future console attach from
            # bubbling into the new OSK.
            flags = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        subprocess.Popen(
            [str(exe_path)],
            creationflags=flags,
            close_fds=True,
            cwd=str(exe_path.parent),
        )
        return True
    except Exception as exc:  # noqa: BLE001
        _logger.error("Failed to launch %s: %s", exe_path, exc)
        return False


def _write_handoff(
    config_dir: Path,
    new_version: str,
    previous_version: str,
) -> None:
    """Drop the breadcrumb the new OSK reads to surface its toast.

    Format is forward-compatible — adding fields is fine, but the new
    OSK must tolerate missing fields since users can update across
    multiple versions.
    """
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": new_version,
            "previous_version": previous_version,
            "completed_at": time.time(),
        }
        path = config_dir / "update_handoff.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        _logger.warning("Failed to write handoff file: %s", exc)


def run_relauncher(argv: list[str]) -> int:
    """CLI entry point. Returns a process exit code (0 = success)."""
    parser = argparse.ArgumentParser(prog="alpha-osk --update-relauncher")
    parser.add_argument("--update-relauncher", action="store_true")
    parser.add_argument("--parent-pid", type=int, required=True)
    parser.add_argument("--new-version", type=str, required=True)
    parser.add_argument("--previous-version", type=str, default="")
    parser.add_argument("--target-exe", type=str, required=True)
    parser.add_argument("--config-dir", type=str, required=True)
    args = parser.parse_args(argv[1:])

    config_dir = Path(args.config_dir)
    _configure_log(config_dir)
    _logger.info(
        "Relauncher starting — parent_pid=%d new_version=%s target=%s",
        args.parent_pid, args.new_version, args.target_exe,
    )

    if not _wait_for_parent_exit(args.parent_pid, _PARENT_EXIT_TIMEOUT_S):
        _logger.error("Parent OSK still alive after %.0fs — giving up",
                      _PARENT_EXIT_TIMEOUT_S)
        return 2

    parent_death_time = time.time()
    _logger.info("Parent OSK exited; waiting %.0fs for installer file copy",
                 _INSTALLER_GRACE_S)
    time.sleep(_INSTALLER_GRACE_S)

    target_exe = Path(args.target_exe)
    if not _wait_for_new_exe(target_exe, parent_death_time, _NEW_EXE_TIMEOUT_S):
        _logger.error("New exe never appeared at %s within %.0fs",
                      target_exe, _NEW_EXE_TIMEOUT_S)
        return 3

    _logger.info("New exe ready at %s — launching", target_exe)
    if not _launch_new_osk(target_exe):
        return 4

    _write_handoff(config_dir, args.new_version, args.previous_version)
    _logger.info("Relauncher done")
    return 0


if __name__ == "__main__":  # pragma: no cover — CLI entry
    sys.exit(run_relauncher(sys.argv))
