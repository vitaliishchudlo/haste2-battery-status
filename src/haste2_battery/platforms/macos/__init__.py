"""macOS backend. TODO: not implemented yet.

Must provide the same functions as `platforms.windows`:
data_dir, acquire_single_instance, show_error, launch_command,
autostart_enabled, set_autostart, handle_cli.

Notes for the implementation:
  - data dir: ~/Library/Application Support/Haste2Battery
  - single instance: fcntl.flock on a lock file
  - autostart: LaunchAgent plist in ~/Library/LaunchAgents
  - tray: pystray works on macOS but needs the main thread
  - HID: hidapi works; the mouse may need Input Monitoring permission
"""
raise NotImplementedError('macOS support is not implemented yet')
