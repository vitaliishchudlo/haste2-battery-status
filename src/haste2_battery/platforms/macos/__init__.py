"""macOS backend: data folder, single-instance lock, LaunchAgent autostart, dialogs, install.

Normal install is `installers/macos/install.sh` (curl). The app can also install itself
when launched from a downloaded .dmg/.zip (copies the bundle to ~/Applications).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import autostart

NAME = 'Haste2Battery'
TITLE = 'Haste2 Battery'
AUTOSTART_LABEL = 'Запускати при вході в систему'
APP_DIR = Path.home() / 'Applications'


def data_dir():
    return Path.home() / 'Library' / 'Application Support' / NAME


def acquire_single_instance(folder):
    """Return a lock handle to keep alive, or None if another instance runs."""
    import fcntl
    lock = open(folder / 'instance.lock', 'a+b')
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        return None
    return lock


def _osascript(script, *args):
    return subprocess.run(['osascript', '-e', script, *args], capture_output=True,
                          text=True, check=False)


def _dialog(text, icon, buttons='{"OK"}'):
    script = ('on run argv\n'
              f'display dialog (item 1 of argv) with title "{TITLE}" buttons {buttons} '
              f'default button 1 with icon {icon}\n'
              'end run')
    return _osascript(script, text)


def show_error(title, text):
    _dialog(f'{title}\n\n{text}'[:1500], 'stop')


def ask(text):
    script = ('on run argv\n'
              f'display dialog (item 1 of argv) with title "{TITLE}" '
              'buttons {"Ні", "Так"} default button "Так" cancel button "Ні" with icon note\n'
              'end run')
    return _osascript(script, text).returncode == 0


def info(text):
    _dialog(text, 'note')


def launch_command():
    """Argument list that starts this app (stored in the LaunchAgent)."""
    if getattr(sys, 'frozen', False):
        return [str(Path(sys.executable).resolve())]
    return [sys.executable, str(Path(sys.argv[0]).resolve())]


def autostart_enabled(command):
    return autostart.is_enabled(command)


def set_autostart(command, enabled):
    autostart.set_enabled(command, enabled)


def bundle_path():
    """The running .app bundle, or None when not frozen into one."""
    if not getattr(sys, 'frozen', False):
        return None
    for parent in Path(sys.executable).resolve().parents:
        if parent.suffix == '.app':
            return parent
    return None


def _installed_here(bundle):
    return bundle.parent in (APP_DIR.resolve(), Path('/Applications'))


def _stop_other_instances():
    """Terminate other running copies of this app (not this process)."""
    result = subprocess.run(['pgrep', '-x', NAME], capture_output=True, text=True, check=False)
    for line in result.stdout.split():
        if line.isdigit() and int(line) != os.getpid():
            try:
                os.kill(int(line), 15)
            except OSError:
                pass


def install():
    bundle = bundle_path()
    if bundle is None:
        return
    if not ask('Встановити Haste2 Battery для поточного користувача?\n\n'
               'Застосунок буде скопійовано в ~/Applications і додано до автозапуску.'):
        return
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        target = APP_DIR / bundle.name
        _stop_other_instances()
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(bundle, target, symlinks=True)
        subprocess.run(['xattr', '-dr', 'com.apple.quarantine', str(target)], check=False,
                       capture_output=True)
        autostart.set_enabled([str(target / 'Contents' / 'MacOS' / Path(sys.executable).name)], True)
        subprocess.Popen(['open', str(target)])
    except Exception as exc:
        show_error('Не вдалося встановити', str(exc))


def uninstall():
    if not ask('Видалити Haste2 Battery разом з налаштуваннями?'):
        return
    try:
        autostart.set_enabled([], False)
        _stop_other_instances()
        for path in (APP_DIR / (NAME + '.app'), Path('/Applications') / (NAME + '.app')):
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(data_dir(), ignore_errors=True)
    except Exception as exc:
        show_error('Не вдалося видалити', str(exc))
        return
    info('Haste2 Battery видалено.')


def handle_cli(argv):
    """Return True if this launch was a CLI/install request and the app must not start."""
    if '--version' in argv:
        from haste2_battery import __version__
        print(__version__)
        return True
    if '--enable-autostart' in argv:      # used by install.sh
        autostart.set_enabled(launch_command(), True)
        return True
    if '--uninstall' in argv:
        uninstall()
        return True
    bundle = bundle_path()
    if '--install' in argv or (bundle is not None and not _installed_here(bundle)):
        install()
        return True
    return False


RELEASE_SUFFIX = '-mac'
INSTALL_SCRIPT = ('https://raw.githubusercontent.com/vitaliishchudlo/haste2-battery-status/'
                  'production/installers/macos/install.sh')


def apply_update(release):
    """Run the same one-liner as a manual install. It stops this app, replaces the bundle
    and relaunches, so on success we are killed while waiting. Returning means it failed."""
    process = subprocess.Popen(
        ['/bin/bash', '-c', f'curl -fsSL "{INSTALL_SCRIPT}" | bash'],
        start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    code = process.wait()
    raise RuntimeError(f'install.sh exited with code {code}')


def cleanup_update():
    pass
