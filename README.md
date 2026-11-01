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
- Python with pip and venv available.
- Internet connection during installation to download build dependencies.
- The mouse’s wireless USB receiver connected to the computer.

Python is required to build the application during installation. After installation, the application runs as a standalone executable.

## Installation

1. Download the project ZIP and extract it.
2. Open the extracted application folder.
3. Double-click `INSTALL.cmd`.
4. Wait for the build and installation to finish.

The application starts automatically and creates a desktop shortcut.

The default refresh interval is **3 minutes**. Startup with Windows is enabled during installation and can be disabled from the tray menu.

## Usage

Right-click the tray icon to:

- View battery status and the last reading time.
- Refresh immediately.
- Select a refresh interval.
- Enable or disable startup with Windows.
- Exit the application.

If Windows hides the icon, move it from the tray overflow into the visible tray area.

## Updating

1. Exit the running application from its tray menu.
2. Extract the new version into a separate folder.
3. Run `INSTALL.cmd`.

Your saved refresh interval is preserved during normal updates.

## Uninstalling

Exit the application and run `CLEAN_OLD.cmd` from the extracted project folder.

This removes the utility’s installed files, shortcut, and startup entries. It does not uninstall Python or HyperX NGENUITY.

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

The current version targets **Windows 11**.

macOS and Linux versions are not implemented yet.

## Development status

Version **1.4.0**.

Automated checks with simulated inputs cover battery response parsing, polling behavior, cached readings, and startup configuration. Hardware behavior and installation should also be verified on the target computer.

## Acknowledgments

Battery protocol reference:
[czQery/waybar-hyperx-haste2](https://github.com/czQery/waybar-hyperx-haste2)

## Disclaimer

This is an unofficial community utility. It is not affiliated with or endorsed by HyperX or HP.
