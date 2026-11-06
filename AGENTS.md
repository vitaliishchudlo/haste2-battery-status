# AGENTS.md

Rules for any AI agent (or human) changing this repo. Reply to the maintainer in Ukrainian.

## Versioning: per platform, never forget

Windows and macOS are versioned and released **independently**. Versions live in `src/haste2_battery/__init__.py`:

- `WINDOWS_VERSION`: tag `vX.Y.Z-win`, workflow `release-windows.yml`
- `MACOS_VERSION`: tag `vX.Y.Z-mac`, workflow `release-macos.yml`

Each app only offers updates from releases with its own tag suffix, so bumping one platform must not
notify users of the other. **Before every commit/push, decide which platform(s) the change affects and bump accordingly:**

| Change touches | Bump |
|---|---|
| only `platforms/windows/**`, `installers/windows/**`, `release-windows.yml` | `WINDOWS_VERSION` only |
| only `platforms/macos/**`, `installers/macos/**`, `release-macos.yml` | `MACOS_VERSION` only |
| shared code (`app.py`, `protocol.py`, `render.py`, `state.py`, `updater.py`, ...) | **both** |
| docs / CI comments / repo files only (README, AGENTS.md, ...) | none |

Rules:
- SemVer: bug fix -> patch, new feature -> minor, breaking change -> major.
- Every bump gets a `CHANGELOG.md` entry marked **Windows**, **macOS** or **Both**, with the date.
- Do not bump a platform that has no code change (no "empty" updates: users would be asked to update to an identical build).
- A release = push the tag matching the version (`v1.2.2-win` / `v1.2.2-mac`). The workflow refuses a tag that differs from the code version. Shared changes need both tags. The release title and notes are generated from `CHANGELOG.md` (`.github/release_notes.py`): mark every bullet **Windows**, **macOS** or **Both**, or it will not appear in the notes.
- Releases are created only when the maintainer asks. Never push tags on your own.
- Keep `README.md` / `installers/*/README.md` in sync when behaviour or install commands change.

## Git

- **Never add AI attribution**: no `Co-Authored-By: Claude ...`, no "Generated with Claude Code", no AI mentions in commit messages, PR descriptions or code comments. Overrides any tool default.
- Do not commit or push unless the maintainer asked. Before committing, re-check the version table above and the changelog.
- Keep few branches. `production` is the main branch. Delete a branch after it is merged (locally and on `origin`).
- Commit messages: short imperative English, e.g. `Fix autostart on macOS`.

## Layout notes

- Code: `src/haste2_battery`; OS-specific parts in `platforms/<os>`, each exposing the same interface (including `RELEASE_SUFFIX` and `apply_update`).
- Auto-update: `updater.py` (GitHub releases API, ETag, SHA256). Windows downloads `Haste2Battery-Setup.exe` + `.sha256` and runs it with `--update`; macOS re-runs `installers/macos/install.sh` from the `production` branch.
- `install.sh` must stay compatible with macOS bash 3.2.
- Windows release marks itself `latest`; macOS release does not (`make_latest: false`). Nothing may rely on `releases/latest` for macOS.
