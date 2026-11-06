"""Remove only this utility: scoped processes, own startup values and shortcuts."""
import os
import sys
import re
import json
import ntpath
import time
import shutil
import base64
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from haste2_battery.platforms.windows import autostart as startup_config  # noqa: E402


def powershell(script):
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive',
                           '-EncodedCommand', encoded], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding='utf-8', errors='replace').stdout


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def owned_process(proc, root):
    name = (proc.get('Name') or '').casefold()
    executable = (proc.get('ExecutablePath') or '').casefold()
    prefix = str(root).rstrip('\\/').replace('/', '\\').casefold() + '\\'
    if name == 'haste2battery.exe':
        return executable.replace('/', '\\').startswith(prefix)
    if name in ('pythonw.exe', 'python.exe'):
        old = ntpath.join(str(root), 'haste2_tray.pyw')
        # Match the complete old script argument, not arbitrary Python processes.
        pattern = r'(?:^|\s)"?' + re.escape(old) + r'"?(?:\s|$)'
        return re.search(pattern, proc.get('CommandLine') or '', re.IGNORECASE) is not None
    return False


def stop_own_processes(root):
    script = '''[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Get-CimInstance Win32_Process -Filter "Name='Haste2Battery.exe' OR Name='pythonw.exe' OR Name='python.exe'" |
Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress'''
    raw = powershell(script).strip()
    procs = json.loads(raw) if raw else []
    if isinstance(procs, dict):
        procs = [procs]
    for proc in procs:
        pid = int(proc['ProcessId'])
        if pid == os.getpid() or not owned_process(proc, root):
            continue
        print('Stopping old Haste2 Battery process:', pid)
        powershell(f'''$ErrorActionPreference='Stop'
$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue
if ($p) {{ $p.Kill(); if (-not $p.WaitForExit(5000)) {{ throw 'App did not exit' }} }}''')


def remove_shortcuts(root):
    script = ("$ErrorActionPreference='Stop';"
              "$ws=New-Object -ComObject WScript.Shell;"
              "$root="+quote(str(root).rstrip('\\')+'\\')+";"
              "foreach($folder in @([Environment]::GetFolderPath('Desktop'),"
              "[Environment]::GetFolderPath('Startup'))) {"
              "$link=Join-Path $folder 'Haste2 Battery.lnk';"
              "if(Test-Path -LiteralPath $link) {"
              "$sc=$ws.CreateShortcut($link);"
              "if($sc.TargetPath.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) {"
              "Remove-Item -LiteralPath $link -Force } } }")
    powershell(script)


def remove_installed(root):
    startup_config.remove_registration(root)
    stop_own_processes(root)
    remove_shortcuts(root)
    for attempt in range(6):
        try:
            if root.exists():
                shutil.rmtree(root)
            return
        except OSError:
            if attempt == 5:
                raise
            time.sleep(0.5)


def main():
    if sys.platform != 'win32':
        raise RuntimeError('Requires Windows 11.')
    root = Path(os.environ['LOCALAPPDATA'])/'Haste2Battery'
    # Never delete the installer/cleanup source while it is running.
    source = Path(__file__).resolve()
    if source.is_relative_to(root.resolve()):
        raise RuntimeError('Extract the ZIP outside the installed Haste2Battery folder first.')
    remove_installed(root)
    print('Removed installed Haste2 Battery, its shortcut and own startup entries.')
    print('Python, other programs and their startup entries were NOT removed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Cleanup failed:', error)
        sys.exit(1)
