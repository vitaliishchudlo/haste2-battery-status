# macOS installer

- `install.sh` - one-line curl installer (also update/uninstall). Attached to every release.
- `build.sh` - builds `Haste2Battery.app` with PyInstaller (ad-hoc signed), `.tar.gz` and `.dmg`. Apple Silicon only.
- CI: `.github/workflows/release-macos.yml` builds, smoke-tests `install.sh` on a macOS runner, and on a `v*` tag attaches the files to the release.
  Pushing a branch named `macos-*` runs build + smoke test without releasing.

Backend code: `src/haste2_battery/platforms/macos/`.
