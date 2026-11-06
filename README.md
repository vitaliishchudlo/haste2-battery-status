# Haste2 Battery

A lightweight tray battery monitor for the **HyperX Pulsefire Haste 2 Wireless** mouse. No NGENUITY needed.

## Features

- Battery percentage right in the tray icon, color-coded (green / yellow / orange / red).
- Refresh the battery reading every 1, 3, 5, 30 minutes or 1, 3, 6 hours, or manually.
- Keeps the last reading and marks it as stale when the mouse is unavailable.
- Starts at login (can be turned off in the menu).
- Checks for updates (at start, then every 6 h, or on demand from the menu); when a new version exists the icon gets a blue dot, and the menu item *Оновити до версії X* installs it.

## Supported

| Platform | Status |
|----------|--------|
| Windows 11 | Supported |
| macOS 11+ (Apple Silicon) | Supported; Intel Macs are not built |
| Linux | Future |

Hardware: Haste 2 Wireless **USB receiver** (VID `03F0`, PID `0F98`). Other mice and receivers are not supported.

## Installation

### Windows

1. Download `Haste2Battery-Setup.exe` from the [latest release](../../releases/latest).
2. Double-click it and confirm.

No Python or admin rights needed. Windows SmartScreen may warn because the file is not code-signed: click *More info → Run anyway*.

Updates: use the menu item above, or run the new Setup. To uninstall, use Windows Settings → Apps.

### macOS (Apple Silicon)

Paste in Terminal:

```
curl -fsSL https://raw.githubusercontent.com/vitaliishchudlo/haste2-battery-status/production/installers/macos/install.sh | bash
```

It installs to `~/Applications`, enables start at login and launches the app. No Apple account, no Gatekeeper warning (curl downloads are not quarantined).
On first run macOS asks for **Input Monitoring** permission: allow it, otherwise the mouse cannot be read.
Update: use the menu item in the app, or run the same command again. Uninstall: same command with `| bash -s -- --uninstall`.
The app lives in the menu bar (no Dock icon). Logs: `~/Library/Application Support/Haste2Battery/`.
Fallback: download the `.dmg` from the release; the first launch needs Settings → Privacy & Security → *Open Anyway*.

## Usage

Right-click the tray icon (macOS: click the menu bar icon) to refresh, change the interval, toggle startup, or exit.
If the icon is hidden, drag it out of the tray overflow.

## Development

Build locally with `installers/windows/build.cmd` → `dist/Haste2Battery-Setup.exe` (Windows) or `installers/macos/build.sh` → `dist/Haste2Battery-macos-arm64.tar.gz` (macOS).
Each platform has its own version and release: pushing `win-v1.5.0` builds the Windows release, `mac-v1.5.0` the macOS one (the tag must match `WINDOWS_VERSION` / `MACOS_VERSION` in `src/haste2_battery/__init__.py`). The apps only offer updates from their own tag prefix. The macOS job also smoke-tests `install.sh`. See [CHANGELOG.md](CHANGELOG.md) and [AGENTS.md](AGENTS.md).

Code lives in `src/haste2_battery`; OS-specific parts are in `platforms/<os>`.

## Credits

Battery protocol: [czQery/waybar-hyperx-haste2](https://github.com/czQery/waybar-hyperx-haste2).
Unofficial community project, not affiliated with HyperX or HP.
