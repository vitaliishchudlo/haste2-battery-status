# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Changed
- Repository restructured: `src/haste2_battery` package, platform backends in `platforms/`,
  installers per OS in `installers/`, tests in `tests/`.
- Windows installer moved to `installers/windows/`.

### Added
- macOS and Linux backend placeholders (not implemented).
- Automated tests and CI; release workflow that builds a Windows package on version tags.

## [1.4.0]

Last version before the restructuring (Windows 11 only).
