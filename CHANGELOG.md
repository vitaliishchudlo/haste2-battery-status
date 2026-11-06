# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: [SemVer](https://semver.org/).

Windows and macOS are versioned and released separately (tags `win-vX.Y.Z` / `mac-vX.Y.Z`). Entries are marked **Windows**, **macOS** or **Both**; 1.1.0 and older were released together under `v*` tags.

## [1.2.1] - 2026-11-07

- **Both:** the refresh menu item is renamed to «Оновити % заряду» (it reads the mouse battery, it is not an app update).

## [1.2.0] - 2026-11-07

- **Both:** automatic update check at start and then every 6 h (plus a menu item to check now). A blue dot on the icon and a notification announce a new version; the menu item *Оновити до версії X* installs it after the user clicks.
- **Windows:** the update is downloaded from the release, verified with SHA256 and installed silently over the old exe.
- **macOS:** the update runs the same `install.sh` one-liner.
- **Both:** the battery refresh interval can now also be 30 min, 1, 3 or 6 h.
- **Both:** per-platform release tags; `install.sh` is now served from the `production` branch.

## [1.1.0] - 2026-11-06

- macOS (Apple Silicon) support: `.app` + `install.sh` one-line installer, LaunchAgent autostart, `.dmg` fallback.

## [1.0.0]

First public release.

- Tray battery monitor for the HyperX Pulsefire Haste 2 Wireless (Windows 11).
- Single self-installing `Haste2Battery-Setup.exe`: no Python required; uninstall via Windows Settings -> Apps.
- Refresh interval 1 / 3 / 5 minutes, manual refresh, start with Windows.
- Platform backends (`platforms/`) prepared for macOS and Linux (not implemented yet).
