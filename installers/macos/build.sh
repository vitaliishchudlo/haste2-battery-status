#!/bin/bash
# Developer build on a Mac (Apple Silicon): produces dist/Haste2Battery-macos-arm64.tar.gz and .dmg
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
NAME="Haste2Battery"
PY="${PYTHON:-python3}"

"$PY" -m venv build/venv
build/venv/bin/python -m pip install --only-binary=:all: -q \
  hidapi==0.15.0 pystray==0.19.5 "Pillow>=10.1,<14" certifi "pyinstaller>=6.11,<7"

# .icns from the Windows icon
build/venv/bin/python - <<'PY'
from PIL import Image
img = Image.open('assets/haste2.ico')
img = img.convert('RGBA').resize((512, 512))
img.save('build/haste2.icns')
PY

rm -rf dist/"$NAME".app
build/venv/bin/python -m PyInstaller --noconfirm --clean --windowed --name "$NAME" \
  --icon "$ROOT/build/haste2.icns" --osx-bundle-identifier com.haste2battery.app \
  --hidden-import pystray._darwin --paths "$ROOT/src" \
  --distpath "$ROOT/dist" --workpath "$ROOT/build/pyinstaller" --specpath "$ROOT/build" \
  "$ROOT/installers/windows/launcher.pyw"

# Menu-bar-only app (no Dock icon); version from the package
build/venv/bin/python - <<'PY'
import plistlib, sys
sys.path.insert(0, 'src')
from haste2_battery import __version__
path = 'dist/Haste2Battery.app/Contents/Info.plist'
with open(path, 'rb') as f:
    data = plistlib.load(f)
data.update({'LSUIElement': True, 'CFBundleShortVersionString': __version__,
             'CFBundleVersion': __version__, 'CFBundleDisplayName': 'Haste2 Battery',
             'LSMinimumSystemVersion': '11.0'})
with open(path, 'wb') as f:
    plistlib.dump(data, f)
PY

# Ad-hoc signature (free; required for arm64 binaries to run)
codesign --force --deep -s - "dist/$NAME.app"
codesign --verify --deep --strict "dist/$NAME.app"

tar -C dist -czf "dist/$NAME-macos-arm64.tar.gz" "$NAME.app"

# Fallback .dmg (drag-and-drop)
rm -rf build/dmg && mkdir -p build/dmg
cp -R "dist/$NAME.app" build/dmg/
ln -s /Applications build/dmg/Applications
hdiutil create -volname "Haste2 Battery" -srcfolder build/dmg -ov -format UDZO "dist/$NAME-macos-arm64.dmg"

echo "Done: dist/$NAME-macos-arm64.tar.gz, dist/$NAME-macos-arm64.dmg"
