"""Windows backend: data folder, single-instance lock, autostart, error dialog."""
import os
import sys
from pathlib import Path

NAME = 'Haste2Battery'
AUTOSTART_LABEL = 'Запускати з Windows'

from . import autostart  # noqa: E402


def data_dir():
    return Path(os.environ.get('LOCALAPPDATA', '.')) / NAME


def acquire_single_instance(folder):
    """Return a lock handle to keep alive, or None if another instance runs."""
    import msvcrt
    lock = open(folder / 'instance.lock', 'a+b')
    lock.seek(0, 2)
    if not lock.tell():
        lock.write(b'0')
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        return None
    return lock


def show_error(title, text):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, text, title, 16)


def launch_command():
    import subprocess
    args = [sys.executable]
    if not getattr(sys, 'frozen', False):
        args.append(str(Path(sys.argv[0]).resolve()))
    return subprocess.list2cmdline(args)


def autostart_enabled(command):
    return autostart.is_enabled(command)


def set_autostart(command, enabled):
    autostart.set_enabled(command, enabled)


def handle_cli(argv):
    """Handle --install / --uninstall (and first-run install of the downloaded exe)."""
    from . import installer
    return installer.handle_cli(argv)
