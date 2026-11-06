"""Tray application: wires the worker thread, tray icon and menu together."""
import logging
import sys
import threading
import time
from logging.handlers import RotatingFileHandler

from . import __version__ as VERSION
from .platforms import backend
from .protocol import read_battery
from .render import make_image
from . import updater
from .state import IntervalSettings, ReadingCache, RefreshGate, UpdateSettings, next_wake_delay


def interval_label(minutes):
    return f'Раз на {minutes} хв' if minutes < 60 else f'Раз на {minutes // 60} год'


def run():
    import pystray

    folder = backend.data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    lock = backend.acquire_single_instance(folder)
    if lock is None:
        return

    logger = logging.getLogger('Haste2Battery')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(folder/'monitor.log', maxBytes=100000, backupCount=1,
                                  encoding='utf-8')
    logger.addHandler(handler)
    refresh = threading.Event()
    stopped = threading.Event()
    status = {'text': 'Очікування відповіді від мишки…'}
    gate = RefreshGate()
    cache = ReadingCache()
    settings = IntervalSettings(folder / 'settings.json')
    update_settings = UpdateSettings(folder / 'updates.json')
    update_state = updater.UpdateState()
    update_wake = threading.Event()
    feed = updater.ReleaseFeed()
    view = {'value': None, 'stale': False}
    backend.cleanup_update()
    logger.info('%s: Starting Haste2 Battery %s', time.strftime('%Y-%m-%d %H:%M:%S'), VERSION)
    command = backend.launch_command()

    def autostart_enabled(item=None):
        try:
            return backend.autostart_enabled(command)
        except OSError:
            logger.exception('Could not read autostart state')
            return False

    def toggle_autostart(icon, item):
        try:
            backend.set_autostart(command, not backend.autostart_enabled(command))
        except OSError as error:
            logger.exception('Autostart change failed')
            icon.notify(str(error), 'Не вдалося змінити автозапуск')
        finally:
            icon.update_menu()

    def request_refresh(icon, item):
        gate.request(refresh, time.monotonic())

    def choose_interval(minutes):
        def apply(icon, item):
            try:
                settings.set(minutes)
                refresh.set()  # Recalculate deadline; do not query immediately unless due.
            except OSError as error:
                logger.exception('Could not save interval')
                icon.notify(str(error), 'Не вдалося зберегти інтервал')
            icon.update_menu()
        return apply

    def interval_checked(minutes):
        return lambda item: settings.minutes == minutes

    def redraw():
        available, _, _ = update_state.snapshot()
        icon.icon = make_image(view['value'], view['stale'], available is not None)

    def update_label(item):
        available, busy, failed = update_state.snapshot()
        if busy:
            return 'Оновлення…'
        if failed:
            return 'Не вдалося оновити — спробувати знову'
        if available:
            return 'Оновити до версії ' + available.version
        return 'Застосунок оновлено, версія ' + VERSION

    def update_enabled(item):
        available, busy, _ = update_state.snapshot()
        return available is not None and not busy

    def apply_update(icon, item):
        release = update_state.begin()
        if release is None:
            return
        icon.update_menu()

        def job():
            ok = False
            try:
                if backend.apply_update(release):
                    ok = True
                    quit_app(icon, None)
            except Exception as error:
                logger.exception('Update failed')
                icon.notify(str(error), 'Не вдалося оновити')
            finally:
                update_state.finish(ok)
                icon.update_menu()
        threading.Thread(target=job, name='updater', daemon=True).start()

    def check_now(icon, item):
        update_wake.set()

    def update_worker():
        while not stopped.is_set():
            update_wake.clear()
            try:
                release = updater.check(feed, backend.RELEASE_SUFFIX, VERSION)
                update_state.set_available(release)
                if release and update_settings.notified != release.version:
                    update_settings.set_notified(release.version)
                    icon.notify('Доступна версія ' + release.version
                                + '. Натисніть на іконку → «Оновити».', 'Haste2 Battery')
            except Exception as error:
                logger.warning('%s: update check failed: %s', time.strftime('%Y-%m-%d %H:%M:%S'), error)
            redraw()
            icon.update_menu()
            update_wake.wait(UpdateSettings.CHECK_SECONDS)

    def quit_app(icon, item):
        stopped.set()
        refresh.set()
        update_wake.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem('Haste2 Battery ' + VERSION, None, enabled=False),
        pystray.MenuItem(lambda item: status['text'], None, enabled=False),
        pystray.MenuItem(update_label, apply_update, enabled=update_enabled),
        pystray.MenuItem('Перевірити оновлення', check_now),
        pystray.MenuItem('Оновити % заряду', request_refresh, default=True),
        pystray.MenuItem('Частота оновлення', pystray.Menu(
            *[pystray.MenuItem(interval_label(n), choose_interval(n),
                              checked=interval_checked(n), radio=True)
              for n in IntervalSettings.OPTIONS])),
        pystray.MenuItem(backend.AUTOSTART_LABEL, toggle_autostart, checked=autostart_enabled),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Вийти', quit_app))
    icon = pystray.Icon('Haste2Battery', make_image(None), 'Haste 2: очікування…', menu)

    def publish():
        value = cache.visible_value(time.monotonic())
        stale = cache.failures > 0 and value is not None
        if stale:
            label = f'Останній: {value}% о {cache.clock}; збоїв: {cache.failures}'
        elif value is not None:
            label = f'Заряд: {value}% · {cache.clock}'
        else:
            label = f'Немає актуального заряду; збоїв: {cache.failures}'
        status['text'] = label
        view['value'], view['stale'] = value, stale
        redraw()
        icon.title = 'HyperX Haste 2 — ' + label
        icon.update_menu()
        return value

    def worker():
        while not stopped.is_set():
            last_attempt = time.monotonic()
            gate.begin(refresh, last_attempt)
            try:
                value = read_battery()
                cache.success(value, time.monotonic())
            except Exception as error:
                cache.after_failure(time.monotonic())
                logger.warning('%s: %s', time.strftime('%Y-%m-%d %H:%M:%S'), error)
            finally:
                gate.finish()
            if stopped.is_set():
                break
            shown = publish()
            while not stopped.is_set():
                if gate.consume_request():
                    break
                now = time.monotonic()
                if now >= last_attempt + settings.minutes * 60:
                    break
                if shown is not None and now >= cache.unknown_deadline():
                    shown = publish()  # Expire cached UI without another hardware request.
                delay = next_wake_delay(now, last_attempt, settings.minutes, cache, shown)
                refresh.wait(delay)
                refresh.clear()

    thread = None
    def setup(tray):
        nonlocal thread
        tray.visible = True
        thread = threading.Thread(target=worker, name='battery-reader', daemon=True)
        thread.start()
        threading.Thread(target=update_worker, name='update-checker', daemon=True).start()

    try:
        icon.run(setup=setup)
    finally:
        stopped.set()
        refresh.set()
        update_wake.set()
        if thread:
            thread.join(timeout=4)
        lock.close()


def check_update_cli():
    """`--check-update`: one real update check, exit code 0 = ok, 1 = failed (used by CI)."""
    try:
        release = updater.check(updater.ReleaseFeed(), backend.RELEASE_SUFFIX, VERSION)
    except Exception as error:
        print('update check failed:', error, file=sys.stderr)
        return 1
    print('update available: ' + release.version if release else 'up to date: ' + VERSION)
    return 0


def main():
    if '--check-update' in sys.argv:       # before backend.handle_cli: must never install
        sys.exit(check_update_cli())
    if backend.handle_cli(sys.argv[1:]):
        return
    try:
        run()
    except Exception:
        import traceback
        report = traceback.format_exc()
        folder = backend.data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'startup-error.txt').write_text(report, encoding='utf-8')
        backend.show_error('Haste2 Battery: помилка запуску', report)
