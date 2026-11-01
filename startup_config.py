"""Own per-user Run registration + Windows StartupApproved state.

StartupApproved is Windows implementation detail, not a stable public API.
Only this application's value is read/written. Never change state on app launch.
"""
import os
import time
import subprocess
from pathlib import Path

NAME = 'Haste2Battery'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
APPROVAL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run'
LEGACY_APPROVAL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run32'


def access(reg, write=False):
    return (reg.KEY_SET_VALUE if write else reg.KEY_READ) | reg.KEY_WOW64_64KEY


def read_value(reg, path):
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, path, 0, access(reg)) as key:
            return reg.QueryValueEx(key, NAME)
    except FileNotFoundError:
        return None


def approval_enabled(value):
    if value is None:
        return True
    data, kind = value
    # Fail closed for unrecognized/corrupt data instead of a misleading checkmark.
    return kind == 3 and isinstance(data, bytes) and len(data) == 12 and data[0:4] in (
        b'\x02\0\0\0', b'\x06\0\0\0')


def is_enabled(command, reg=None):
    if reg is None:
        import winreg as reg
    registration = read_value(reg, RUN_KEY)
    if registration is None or registration[0] != command:
        return False
    return approval_enabled(read_value(reg, APPROVAL_KEY))


def set_enabled(command, enabled, reg=None):
    if reg is None:
        import winreg as reg
    if enabled:
        with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, RUN_KEY, 0, access(reg, True)) as key:
            reg.SetValueEx(key, NAME, 0, reg.REG_SZ, command)
    else:
        registration = read_value(reg, RUN_KEY)
        if registration is None:
            return
        if registration[0] != command:
            raise OSError('Startup entry points to another application version. Reinstall the current version.')
    timestamp = 0 if enabled else int((time.time() + 11644473600) * 10000000)
    blob = (2 if enabled else 3).to_bytes(4, 'little') + timestamp.to_bytes(8, 'little')
    with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, APPROVAL_KEY, 0, access(reg, True)) as key:
        reg.SetValueEx(key, NAME, 0, reg.REG_BINARY, blob)
    if is_enabled(command, reg) != enabled:
        raise OSError('Windows did not accept the requested startup state.')


def remove_registration(root, reg=None):
    if reg is None:
        import winreg as reg
    current = read_value(reg, RUN_KEY)
    prefix = str(root).replace('/', '\\').rstrip('\\').casefold() + '\\'
    if current and prefix not in str(current[0]).replace('/', '\\').casefold():
        raise OSError('An unrelated entry uses the name Haste2Battery; cleanup stopped.')
    # The exact value name is ours in v1.0, v1.1 and v1.2.
    for path in (RUN_KEY, APPROVAL_KEY, LEGACY_APPROVAL_KEY):
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, path, 0, access(reg, True)) as key:
                reg.DeleteValue(key, NAME)
        except FileNotFoundError:
            pass
