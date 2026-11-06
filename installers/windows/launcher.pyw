"""PyInstaller / dev entry point for the Windows build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))

from haste2_battery.app import main

if __name__ == '__main__':
    main()
