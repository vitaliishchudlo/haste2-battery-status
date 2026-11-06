"""Build a named Windows executable locally, then install/update for this user."""
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from haste2_battery import __version__ as VERSION  # noqa: E402
from haste2_battery.platforms.windows import autostart as startup_config  # noqa: E402

NAME = 'Haste2Battery'
HERE = Path(__file__).resolve().parent


def ps_quote(text):
    return "'" + str(text).replace("'", "''") + "'"


def ensure_closed(target):
    import msvcrt
    path = target / 'instance.lock'
    if not path.exists():
        return
    with open(path, 'r+b') as lock:
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise RuntimeError('Close Haste2 Battery using its tray menu (Exit), then retry.')
        msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def make_shortcut(exe, icon, target):
    script = (
        "$ErrorActionPreference='Stop';"
        "$ws=New-Object -ComObject WScript.Shell;"
        "$desktop=[Environment]::GetFolderPath('Desktop');"
        "$sc=$ws.CreateShortcut((Join-Path $desktop 'Haste2 Battery.lnk'));"
        '$sc.TargetPath=' + ps_quote(exe) + ';'
        "$sc.Arguments='';"
        '$sc.WorkingDirectory=' + ps_quote(target) + ';'
        '$sc.IconLocation=' + ps_quote(str(icon)+',0') + ';'
        "$sc.Description='Haste2 Battery - wireless mouse battery monitor';"
        '$sc.Save()'
    )
    subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], check=True)


def main():
    if sys.platform != 'win32':
        raise RuntimeError('This installer requires Windows 11.')
    source = ROOT
    target = Path(os.environ['LOCALAPPDATA']) / NAME
    if source.is_relative_to(target.resolve()):
        raise RuntimeError('Extract the ZIP outside the installed Haste2Battery folder first.')
    target.mkdir(parents=True, exist_ok=True)
    ensure_closed(target)
    print('Haste2 Battery', VERSION)
    print('Building the Windows executable locally. First install may take a few minutes.')
    print('The previous version is kept until the build succeeds.\n')
    print('Startup will be enabled by default, as requested.')

    with tempfile.TemporaryDirectory(prefix='haste2-build-') as temp:
        temp = Path(temp)
        # Isolate build dependencies from the user's existing Python packages.
        subprocess.run([sys.executable, '-m', 'venv', str(temp/'venv')], check=True)
        python = temp/'venv'/'Scripts'/'python.exe'
        subprocess.run([str(python), '-m', 'pip', 'install', '--only-binary=:all:',
                        'hidapi==0.15.0', 'pystray==0.19.5', 'Pillow>=10.1,<14',
                        'pyinstaller>=6.11,<7'], check=True)
        subprocess.run([
            str(python), '-m', 'PyInstaller', '--noconfirm', '--clean',
            '--onedir', '--windowed', '--name', NAME,
            '--icon', str(source/'assets'/'haste2.ico'),
            '--version-file', str(HERE/'version_info.txt'),
            '--hidden-import', 'pystray._win32',
            '--paths', str(source/'src'),
            '--distpath', str(temp/'dist'), '--workpath', str(temp/'build'),
            '--specpath', str(temp), str(HERE/'launcher.pyw')
        ], cwd=temp, check=True)
        built = temp/'dist'/NAME
        if not (built/(NAME+'.exe')).is_file():
            raise RuntimeError('Build did not create the executable.')
        ensure_closed(target)
        # Versioned folders keep old executable intact if copying fails.
        destination = target/('app-'+VERSION)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(built, destination)
        shutil.copy2(source/'assets'/'haste2.ico', target/'haste2.ico')
        exe = destination/(NAME+'.exe')
        make_shortcut(exe, target/'haste2.ico', destination)
        startup_config.remove_registration(target)
        # Explicit user preference for v1.2: startup ON after installation.
        startup_config.set_enabled(subprocess.list2cmdline([str(exe)]), True)
        # Prevent an old manual .pyw launch from creating a second installation.
        old_script = target/'haste2_tray.pyw'
        if old_script.exists():
            old_script.unlink()
        (target/'installed-version.txt').write_text(VERSION, encoding='utf-8')
        subprocess.Popen([str(exe)], cwd=destination)
    print('\nUpdated and started. Desktop shortcut: Haste2 Battery')
    print('Executable: Haste2Battery.exe (not pythonw.exe)')
    print('Windows startup: ENABLED (registration and Windows approval both checked).')
    print('If Task Manager shows old information, close it and reopen it.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('\nInstallation failed:', error)
        sys.exit(1)
