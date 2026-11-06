"""Per-user LaunchAgent for autostart. Pure file operations, no launchctl.

Enabling only writes the plist (launchd loads it at the next login); disabling only
removes it. We deliberately never call `launchctl bootout`: if the running app was
started by launchd, that would kill it.
"""
import os
import plistlib
from pathlib import Path

LABEL = 'com.haste2battery.app'


def agents_dir():
    return Path.home() / 'Library' / 'LaunchAgents'


def plist_path(directory=None):
    return Path(directory or agents_dir()) / (LABEL + '.plist')


def is_enabled(command, directory=None):
    try:
        with open(plist_path(directory), 'rb') as handle:
            data = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException, ValueError):
        return False
    return data.get('Label') == LABEL and data.get('ProgramArguments') == list(command) \
        and data.get('RunAtLoad') is True


def set_enabled(command, enabled, directory=None):
    path = plist_path(directory)
    if not enabled:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'Label': LABEL,
        'ProgramArguments': list(command),
        'RunAtLoad': True,
        'KeepAlive': False,
        'ProcessType': 'Interactive',
        'LimitLoadToSessionType': 'Aqua',
    }
    temporary = path.with_suffix('.tmp')
    with open(temporary, 'wb') as handle:
        plistlib.dump(data, handle)
    os.replace(temporary, path)
    if not is_enabled(command, directory):
        raise OSError('Could not write the LaunchAgent: ' + str(path))
