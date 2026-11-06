# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Changed
- Windows installation is now a single self-installing `Haste2Battery-Setup.exe`
  (built by CI, attached to GitHub Releases). Python is no longer required on the user's PC.
- Uninstall via Windows Settings -> Apps (or `Haste2Battery.exe --uninstall`).
- Repository restructured: `src/haste2_battery` package, platform backends in `platforms/`,
  installers per OS in `installers/`.

### Added
- macOS and Linux backend placeholders (not implemented).
- Release workflow that builds the Windows installer on version tags.

### Removed
- `INSTALL.cmd`, `CLEAN_OLD.cmd`, `setup.py`, `cleanup.py` (replaced by the self-installing exe).

## [1.4.0]

Last version before the restructuring (Windows 11 only).
