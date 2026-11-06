"""Self-install / uninstall for the frozen Windows exe. No Python needed on the user's PC.

Double-clicking Haste2Battery-Setup.exe copies itself to %LOCALAPPDATA%\\Haste2Battery,
creates a desktop shortcut, enables autostart and registers an uninstall entry in
Windows "Apps & features".
"""
import base64
import json
import ntpath
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import NAME, autostart, data_dir

EXE = NAME + '.exe'
TITLE = 'Haste2 Battery'
UNINSTALL_KEY = 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + NAME
NO_WINDOW = 0x08000000      # CREATE_NO_WINDOW
DETACHED = 0x00000008       # DETACHED_PROCESS


def _box(text, flags):
    import ctypes
    return ctypes.windll.user32.MessageBoxW(None, text, TITLE, flags)


def ask(text):
    return _box(text, 0x04 | 0x20) == 6   # Yes/No, question icon


def info(text):
    _box(text, 0x40)


def error(text):
    _box(text, 0x10)


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def powershell(script):
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        encoding='utf-8', errors='replace', creationflags=NO_WINDOW).stdout


def owned_process(proc, root):
    name = (proc.get('Name') or '').casefold()
    executable = (proc.get('ExecutablePath') or '').casefold()
    prefix = str(root).rstrip('\\/').replace('/', '\\').casefold() + '\\'
    if name == EXE.casefold():
        return executable.replace('/', '\\').startswith(prefix)
    if name in ('pythonw.exe', 'python.exe'):   # very old script-based installs
        old = ntpath.join(str(root), 'haste2_tray.pyw')
        pattern = r'(?:^|\s)"?' + re.escape(old) + r'"?(?:\s|$)'
        return re.search(pattern, proc.get('CommandLine') or '', re.IGNORECASE) is not None
    return False


def stop_own_processes(root):
    """Kill running copies installed under `root` (not this process or its bootloader parent)."""
    raw = powershell('''[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Get-CimInstance Win32_Process -Filter "Name='Haste2Battery.exe' OR Name='pythonw.exe' OR Name='python.exe'" |
Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress''').strip()
    procs = json.loads(raw) if raw else []
    if isinstance(procs, dict):
        procs = [procs]
    skip = {os.getpid(), os.getppid()}
    for proc in procs:
        pid = int(proc['ProcessId'])
        if pid in skip or not owned_process(proc, root):
            continue
        powershell(f'''$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue
if ($p) {{ $p.Kill(); [void]$p.WaitForExit(5000) }}''')


def make_shortcut(exe):
    powershell(
        "$ErrorActionPreference='Stop';"
        "$ws=New-Object -ComObject WScript.Shell;"
        "$link=Join-Path ([Environment]::GetFolderPath('Desktop')) 'Haste2 Battery.lnk';"
        "$sc=$ws.CreateShortcut($link);"
        f"$sc.TargetPath={quote(exe)};$sc.WorkingDirectory={quote(exe.parent)};"
        f"$sc.IconLocation={quote(str(exe) + ',0')};"
        "$sc.Description='Haste2 Battery - wireless mouse battery monitor';$sc.Save()")


def remove_shortcuts(root):
    powershell(
        "$ErrorActionPreference='Stop';$ws=New-Object -ComObject WScript.Shell;"
        f"$root={quote(str(root).rstrip(chr(92)) + chr(92))};"
        "foreach($f in @([Environment]::GetFolderPath('Desktop'),[Environment]::GetFolderPath('Startup'))){"
        "$l=Join-Path $f 'Haste2 Battery.lnk';if(Test-Path -LiteralPath $l){"
        "$s=$ws.CreateShortcut($l);if($s.TargetPath.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)){"
        "Remove-Item -LiteralPath $l -Force}}}")


def register_uninstall(exe):
    import winreg
    from haste2_battery import __version__
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, 0, winreg.KEY_SET_VALUE) as key:
        for name, value in (('DisplayName', TITLE), ('DisplayVersion', __version__),
                            ('InstallLocation', str(exe.parent)), ('DisplayIcon', str(exe)),
                            ('UninstallString', subprocess.list2cmdline([str(exe), '--uninstall']))):
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        for name in ('NoModify', 'NoRepair'):
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)


def unregister_uninstall():
    import winreg
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except FileNotFoundError:
        pass


def _replace_with_retry(src, dst):
    for attempt in range(10):
        try:
            src.replace(dst)
            return
        except OSError:
            if attempt == 9:
                raise
            time.sleep(0.5)


def install():
    source = Path(sys.executable).resolve()
    target = data_dir()
    if not ask('Встановити Haste2 Battery для поточного користувача?\n\n'
               'Буде створено ярлик на робочому столі та ввімкнено запуск з Windows.'):
        return
    try:
        target.mkdir(parents=True, exist_ok=True)
        stop_own_processes(target)
        dest, staging = target / EXE, target / (EXE + '.new')
        shutil.copy2(source, staging)
        _replace_with_retry(staging, dest)
        for old in target.glob('app-*'):                  # layout of versions up to 1.4.0
            shutil.rmtree(old, ignore_errors=True)
        (target / 'haste2_tray.pyw').unlink(missing_ok=True)
        make_shortcut(dest)
        autostart.remove_registration(target)
        autostart.set_enabled(subprocess.list2cmdline([str(dest)]), True)
        register_uninstall(dest)
        env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT='1')
        subprocess.Popen([str(dest)], cwd=str(target), env=env, creationflags=DETACHED | NO_WINDOW)
    except Exception as exc:
        error(f'Не вдалося встановити:\n\n{exc}')
        return
    info('Haste2 Battery встановлено і запущено.\n\n'
         "Іконка з'явиться в треї (можливо, у прихованих значках).\n"
         'Видалити програму можна у «Параметри → Програми».')


def uninstall():
    target = data_dir()
    if not ask('Видалити Haste2 Battery разом з налаштуваннями?'):
        return
    try:
        autostart.remove_registration(target)
        stop_own_processes(target)
        remove_shortcuts(target)
        unregister_uninstall()
        # Our own exe may live in `target`; delete after this process exits.
        subprocess.Popen(
            ['powershell.exe', '-NoProfile', '-WindowStyle', 'Hidden', '-Command',
             'for($i=0;$i -lt 20;$i++){Start-Sleep 1;'
             f'Remove-Item -LiteralPath {quote(target)} -Recurse -Force -ErrorAction SilentlyContinue;'
             f'if(-not (Test-Path -LiteralPath {quote(target)})){{break}}}}'],
            creationflags=DETACHED | NO_WINDOW)
    except Exception as exc:
        error(f'Не вдалося видалити:\n\n{exc}')
        return
    info('Haste2 Battery видалено.')


def handle_cli(argv):
    """Return True if this launch was an install/uninstall request."""
    if '--uninstall' in argv:
        uninstall()
        return True
    installed_here = (os.path.normcase(str(Path(sys.executable).resolve().parent))
                      == os.path.normcase(str(data_dir().resolve())))
    if '--install' in argv or (getattr(sys, 'frozen', False) and not installed_here):
        install()
        return True
    return False
