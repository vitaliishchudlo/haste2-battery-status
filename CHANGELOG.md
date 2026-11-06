# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: [SemVer](https://semver.org/).

## [1.1.0] - 2026-11-06

- macOS (Apple Silicon) support: `.app` + `install.sh` one-line installer, LaunchAgent autostart, `.dmg` fallback.

## [1.0.0]

First public release.

- Tray battery monitor for the HyperX Pulsefire Haste 2 Wireless (Windows 11).
- Single self-installing `Haste2Battery-Setup.exe`: no Python required; uninstall via Windows Settings -> Apps.
- Refresh interval 1 / 3 / 5 minutes, manual refresh, start with Windows.
- Platform backends (`platforms/`) prepared for macOS and Linux (not implemented yet).
