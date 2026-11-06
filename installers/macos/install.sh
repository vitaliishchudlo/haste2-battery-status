#!/bin/bash
# Haste2 Battery installer for macOS (Apple Silicon).
#   Install / update:  curl -fsSL https://github.com/vitaliishchudlo/haste2-battery-status/releases/latest/download/install.sh | bash
#   Uninstall:         curl -fsSL .../install.sh | bash -s -- --uninstall
# Downloading with curl leaves no quarantine flag, so Gatekeeper does not block the app.
set -euo pipefail

REPO="vitaliishchudlo/haste2-battery-status"
NAME="Haste2Battery"
ARCHIVE="$NAME-macos-arm64.tar.gz"
URL="${HASTE2_ARCHIVE_URL:-https://github.com/$REPO/releases/latest/download/$ARCHIVE}"
APP_DIR="$HOME/Applications"
APP="$APP_DIR/$NAME.app"
PLIST="$HOME/Library/LaunchAgents/com.haste2battery.app.plist"
DATA="$HOME/Library/Application Support/$NAME"

say() { printf '%s\n' "$*"; }
die() { printf 'Помилка: %s\n' "$*" >&2; exit 1; }

stop_app() { pkill -x "$NAME" 2>/dev/null || true; sleep 1; }

[ "$(uname -s)" = "Darwin" ] || die "цей інсталятор лише для macOS."

if [ "${1:-}" = "--uninstall" ]; then
  stop_app
  rm -f "$PLIST"
  rm -rf "$APP" "$DATA"
  say "Haste2 Battery видалено."
  exit 0
fi

[ "$(uname -m)" = "arm64" ] || die "підтримується лише Apple Silicon (arm64)."

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say "Завантаження Haste2 Battery…"
curl -fsSL "$URL" -o "$TMP/$ARCHIVE" || die "не вдалося завантажити $URL"
tar -xzf "$TMP/$ARCHIVE" -C "$TMP" || die "архів пошкоджено."
[ -d "$TMP/$NAME.app" ] || die "в архіві немає $NAME.app."

say "Встановлення в $APP_DIR…"
stop_app
mkdir -p "$APP_DIR"
rm -rf "$APP"
mv "$TMP/$NAME.app" "$APP"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

"$APP/Contents/MacOS/$NAME" --enable-autostart || die "не вдалося ввімкнути автозапуск."
open "$APP"

say "Готово: Haste2 Battery встановлено, запущено і додано до автозапуску."
say "Іконка з'явиться в рядку меню. macOS може запитати дозвіл «Input Monitoring» — дозвольте."
