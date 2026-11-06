"""Selects the backend for the current OS. Each backend exposes the same functions."""
import sys

if sys.platform == 'win32':
    from . import windows as backend
elif sys.platform == 'darwin':
    from . import macos as backend
elif sys.platform.startswith('linux'):
    from . import linux as backend
else:
    raise NotImplementedError('Unsupported platform: ' + sys.platform)
