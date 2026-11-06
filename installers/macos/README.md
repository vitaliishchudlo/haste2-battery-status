# macOS installer

- `install.sh` - one-line curl installer (also update/uninstall). Attached to every release.
- `build.sh` - builds `Haste2Battery.app` with PyInstaller (ad-hoc signed), `.tar.gz` and `.dmg`. Apple Silicon only.
- CI: `.github/workflows/release-macos.yml` builds, smoke-tests `install.sh` on a macOS runner, and on a `v*` tag attaches the files to the release.
  Pushing a branch named `macos-*` runs build + smoke test without releasing.

Backend code: `src/haste2_battery/platforms/macos/`.

## Testing a build before release (on a Mac)

Normal users use the `curl` command from the main README. To test a build that is not released yet:

**Option A - CI artifact (no tools needed).** On GitHub: Actions -> a green `Release (macOS)` run (branches named `macos-*` and tags build it) -> Artifacts -> `macos-build` (needs GitHub login). Unzip it, then in Terminal:

```
cd ~/Downloads/macos-build   # the folder with the unzipped files
HASTE2_ARCHIVE_URL="file://$PWD/Haste2Battery-macos-arm64.tar.gz" bash path/to/install.sh
```

(`install.sh` is in this repo: `installers/macos/install.sh`.)

**Option B - build locally.** Needs Python 3.10+ (`xcode-select --install` or python.org):

```
git clone https://github.com/vitaliishchudlo/haste2-battery-status.git
cd haste2-battery-status
bash installers/macos/build.sh
HASTE2_ARCHIVE_URL="file://$PWD/dist/Haste2Battery-macos-arm64.tar.gz" bash installers/macos/install.sh
```

**What to check**
1. An icon appears in the menu bar. macOS asks for *Input Monitoring*: allow it (System Settings -> Privacy & Security -> Input Monitoring), then choose *Refresh now* from the menu (or restart the app).
2. With the Haste 2 USB receiver plugged in the icon shows the battery %. Without the mouse it shows `?`/stale.
3. Menu: refresh now, interval 1/3/5 min, start-at-login toggle, quit.
4. Autostart: log out/in (or reboot) - the icon returns. Turn the toggle off, log out/in - it does not start.
5. Running the install command again updates in place; starting the app twice does not create a second icon.
6. Logs: `~/Library/Application Support/Haste2Battery/monitor.log` (and `startup-error.txt` if the app failed to start).

**Uninstall:** `bash installers/macos/install.sh --uninstall`
(or, after a release: `curl -fsSL https://github.com/vitaliishchudlo/haste2-battery-status/releases/latest/download/install.sh | bash -s -- --uninstall`).
