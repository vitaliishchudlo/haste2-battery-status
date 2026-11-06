"""Tray application: wires the worker thread, tray icon and menu together."""
import logging
import threading
import time
from logging.handlers import RotatingFileHandler

from . import __version__ as VERSION
from .platforms import backend
from .protocol import read_battery
from .render import make_image
from .state import IntervalSettings, ReadingCache, RefreshGate, next_wake_delay


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
    status = {'text': 'Очікування відповіді мишки…'}
    gate = RefreshGate()
    cache = ReadingCache()
    settings = IntervalSettings(folder / 'settings.json')
    logger.info('%s: Starting Haste2 Battery %s', time.strftime('%Y-%m-%d %H:%M:%S'), VERSION)
    command = backend.launch_command()

    def autostart_enabled(item=None):
        try:
            return backend.autostart_enabled(command)
        except OSError:
            logger.exception('Could not read Windows startup state')
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

    def quit_app(icon, item):
        stopped.set()
        refresh.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem('Haste2 Battery ' + VERSION, None, enabled=False),
        pystray.MenuItem(lambda item: status['text'], None, enabled=False),
        pystray.MenuItem('Оновити зараз', request_refresh, default=True),
        pystray.MenuItem('Частота оновлення', pystray.Menu(
            *[pystray.MenuItem(f'Раз на {n} хв', choose_interval(n),
                              checked=interval_checked(n), radio=True)
              for n in IntervalSettings.OPTIONS])),
        pystray.MenuItem('Запускати з Windows', toggle_autostart, checked=autostart_enabled),
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
        icon.icon = make_image(value, stale)
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

    try:
        icon.run(setup=setup)
    finally:
        stopped.set()
        refresh.set()
        if thread:
            thread.join(timeout=4)
        lock.close()


def main():
    try:
        run()
    except Exception:
        import traceback
        report = traceback.format_exc()
        folder = backend.data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'startup-error.txt').write_text(report, encoding='utf-8')
        backend.show_error('Haste2 Battery: помилка запуску', report)
