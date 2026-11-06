# Haste2 Battery

A lightweight Windows system tray battery monitor for the **HyperX Pulsefire Haste 2 Wireless** mouse.

Check your mouse battery without running HyperX NGENUITY.

## Features

- Battery percentage displayed directly in the tray icon.
- Color indicators: green, yellow, orange, and red.
- Configurable refresh interval: **1, 3, or 5 minutes**.
- Manual refresh from the tray menu.
- Optional startup with Windows, enabled during installation.
- Remembers your refresh interval.
- Temporarily retains the last successful reading when the mouse is unavailable and marks it as stale.
- Ukrainian tray menu.

## Supported hardware

Designed for the wireless USB receiver with:

- Vendor ID: `03F0`
- Product ID: `0F98`

Other HyperX mice and receiver variants are not currently supported.

## Requirements

- Windows 11.
- The mouse's wireless USB receiver connected to the computer.

No Python, pip or internet connection is needed to install.

## Installation

1. Download `Haste2Battery-Setup.exe` from the [latest release](../../releases/latest).
2. Double-click it and confirm.

The app is installed for the current user (no administrator rights), a desktop shortcut is created
and the app starts. Startup with Windows is enabled and can be disabled from the tray menu.
Default refresh interval: **3 minutes**.

Windows SmartScreen may warn about an unknown publisher because the file is not code-signed:
choose *More info -> Run anyway*.

## Usage

Right-click the tray icon to:

- View battery status and the last reading time.
- Refresh immediately.
- Select a refresh interval.
- Enable or disable startup with Windows.
- Exit the application.

If Windows hides the icon, move it from the tray overflow into the visible tray area.

## Updating

Run the new `Haste2Battery-Setup.exe`. It stops the old version, replaces it and keeps your settings.

## Uninstalling

Windows Settings -> Apps -> *Haste2 Battery* -> Uninstall. This removes the app, its settings,
the shortcut and the startup entry. It does not touch HyperX NGENUITY.

## How it works

The application uses HIDAPI to send a battery query directly to the USB receiver.

It does not send commands to change DPI, button assignments, profiles, or firmware.

Main components:

- Python
- HIDAPI
- pystray
- Pillow
- PyInstaller

## Platform support

| Platform | Status |
|----------|--------|
| Windows 11 | Supported |
| macOS | Planned (`src/haste2_battery/platforms/macos`, `installers/macos`) |
| Linux | TODO, future |

## Project structure

```
src/haste2_battery/
  protocol.py        HID battery query (cross-platform)
  state.py           settings, reading cache, refresh throttling (cross-platform)
  render.py          tray icon drawing (cross-platform)
  app.py             tray app and menu
  platforms/         one backend per OS: data dir, single instance, autostart
    windows/  macos/  linux/
installers/          build/install scripts per OS
assets/              icon
```

Adding a new OS means implementing the same small set of functions as `platforms/windows`
and adding an installer under `installers/<os>`.

## Development

Run from source (Windows): `pip install hidapi pystray Pillow`, then `python installers/windows/launcher.pyw`.

Build the installer locally: `installers/windows/build.cmd` -> `dist/Haste2Battery-Setup.exe`.

## Releases

Versions follow SemVer ([CHANGELOG.md](CHANGELOG.md)). Pushing a tag such as `v1.5.0`
(it must match `__version__` in `src/haste2_battery/__init__.py`) makes GitHub Actions build
`Haste2Battery-Setup.exe` and attach it to a GitHub Release.

## Development status

Version **1.4.0**. Hardware behavior and installation should be verified on the target computer.

## Acknowledgments

Battery protocol reference:
[czQery/waybar-hyperx-haste2](https://github.com/czQery/waybar-hyperx-haste2)

## Disclaimer

This is an unofficial community utility. It is not affiliated with or endorsed by HyperX or HP.
