"""Haste2 Battery: tray battery monitor for the HyperX Pulsefire Haste 2 Wireless."""
import sys

# Each platform is versioned and released independently (tags `win-vX.Y.Z` / `mac-vX.Y.Z`).
# See AGENTS.md for when to bump which one.
WINDOWS_VERSION = "1.2.0"
MACOS_VERSION = "1.2.0"

__version__ = {'win32': WINDOWS_VERSION, 'darwin': MACOS_VERSION}.get(sys.platform, WINDOWS_VERSION)
