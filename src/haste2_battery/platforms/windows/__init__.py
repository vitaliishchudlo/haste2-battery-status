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


RELEASE_SUFFIX = '-win'
UPDATE_ASSET = 'Haste2Battery-Setup.exe'


def apply_update(release):
    """Download + verify the new Setup exe and start it silently. Returns True: the caller must exit."""
    import shutil
    import subprocess
    from haste2_battery import updater
    from .installer import DETACHED, NO_WINDOW
    if not getattr(sys, 'frozen', False):
        raise RuntimeError('Auto-update works only in the installed exe')
    exe_url = release.assets.get(UPDATE_ASSET)
    sha_url = release.assets.get(UPDATE_ASSET + '.sha256')
    if not exe_url or not sha_url:
        raise RuntimeError('The release has no installer or checksum')
    folder = data_dir() / 'update'
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    exe = folder / UPDATE_ASSET
    updater.download(exe_url, exe)
    updater.verify_sha256(exe, updater.fetch_text(sha_url))
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT='1')
    subprocess.Popen([str(exe), '--update'], cwd=str(folder), env=env,
                     creationflags=DETACHED | NO_WINDOW, close_fds=True)
    return True


def cleanup_update():
    import shutil
    shutil.rmtree(data_dir() / 'update', ignore_errors=True)
