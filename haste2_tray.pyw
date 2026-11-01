"""Haste 2 Wireless tray monitor. Uses the battery request verified on user's receiver."""
import os
import sys
import time
import threading
from pathlib import Path

VID, PID = 0x03F0, 0x0F98
VERSION = "1.4.0"


def launch_command():
    import subprocess
    args = [sys.executable]
    if not getattr(sys, "frozen", False):
        args.append(str(Path(__file__).resolve()))
    return subprocess.list2cmdline(args)


def battery_color(value):
    if value is None:
        return '#94a3b8'
    if value >= 80:
        return '#22c55e'
    if value >= 50:
        return '#facc15'
    if value >= 20:
        return '#fb923c'
    return '#ef4444'


def decode_response(data):
    """Read battery reports on HID frame boundaries, never arbitrary substrings."""
    data = bytes(data)
    for width in (64, 65):
        if not data or len(data) % width:
            continue
        for offset in range(0, len(data), width):
            report = data[offset:offset + width]
            if width == 65:
                if report[0] != 0:
                    continue
                report = report[1:]
            if report[:2] == b'\x51\x02' and report[2] <= 100:
                return report[2]
    raise ValueError('No valid battery report in this HID read')


class IntervalSettings:
    OPTIONS = (1, 3, 5)

    def __init__(self, path):
        import json
        self.path = Path(path)
        self.lock = threading.Lock()
        self._minutes = 3
        try:
            value = json.loads(self.path.read_text(encoding='utf-8'))['interval_minutes']
            if type(value) is int and value in self.OPTIONS:
                self._minutes = value
        except (OSError, ValueError, KeyError, TypeError):
            pass

    @property
    def minutes(self):
        with self.lock:
            return self._minutes

    def set(self, value):
        import json
        if type(value) is not int or value not in self.OPTIONS:
            raise ValueError('Invalid polling interval')
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'interval_minutes': value}), encoding='utf-8')
            temporary.replace(self.path)
            self._minutes = value


class ReadingCache:
    def __init__(self):
        self.value = None
        self.at = 0.0
        self.clock = ''
        self.failures = 0

    def success(self, value, now):
        self.value = value
        self.at = now
        self.clock = time.strftime('%H:%M:%S')
        self.failures = 0

    def unknown_deadline(self):
        if self.value is None or self.failures == 0:
            return float('inf')
        # Quick manual retries must not discard a recent valid reading.
        return self.at + (180 if self.failures >= 3 else 900)

    def visible_value(self, now):
        if self.value is None or now >= self.unknown_deadline():
            return None
        return self.value

    def after_failure(self, now):
        self.failures += 1
        return self.visible_value(now)


def next_wake_delay(now, last_attempt, minutes, cache, shown_value):
    deadline = last_attempt + minutes * 60
    if shown_value is not None:
        deadline = min(deadline, cache.unknown_deadline())
    return max(0, deadline - now)


class RefreshGate:
    def __init__(self):
        self.lock = threading.Lock()
        self.busy = False
        self.last = float('-inf')
        self.pending = False

    def request(self, event, now):
        with self.lock:
            if self.busy or now - self.last < 5:
                return False
            self.last = now
            self.pending = True
            event.set()
            return True

    def begin(self, event, now):
        with self.lock:
            self.busy = True
            self.pending = False
            self.last = now
            event.clear()

    def consume_request(self):
        with self.lock:
            pending = self.pending
            self.pending = False
            return pending

    def finish(self):
        with self.lock:
            self.busy = False


def read_battery():
    import hid
    candidates = [d for d in hid.enumerate(VID, PID)
                  if d['interface_number'] == 2]
    if len(candidates) != 1:
        raise OSError('Mouse receiver unavailable or ambiguous')
    device = hid.device()
    try:
        device.open_path(candidates[0]['path'])
        if device.write([0x50, 0x02] + [0] * 62) != 64:
            raise OSError('Incomplete battery request')
        deadline = time.monotonic() + 3
        summary = []
        while time.monotonic() < deadline:
            packet = bytes(device.read(256, 200))
            if not packet:
                continue
            if len(summary) < 12:
                summary.append(f'{len(packet)}B:{packet[:4].hex()}')
            try:
                return decode_response(packet)
            except ValueError:
                continue
        raise ValueError('Battery reply timeout (3s); HID reads=' + ','.join(summary))
    finally:
        device.close()


def make_image(value, stale=False):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 7, 62, 57), radius=10, fill=battery_color(value))
    label = '?' if value is None else str(value)
    size = 30 if len(label) == 3 else 40
    font_path = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'arialbd.ttf'
    try:
        font = ImageFont.truetype(str(font_path), size)
    except OSError:
        font = ImageFont.load_default(size=size)
    box = draw.textbbox((0, 0), label, font=font)
    draw.text(((64 - (box[2]-box[0]))/2-box[0],
               (64 - (box[3]-box[1]))/2-box[1]),
              label, font=font, fill='#101827')
    if stale:
        draw.ellipse((49, 1, 63, 15), fill='#64748b', outline='#ffffff', width=2)
    return image


def run():
    import msvcrt
    import logging
    from logging.handlers import RotatingFileHandler
    import pystray

    folder = Path(os.environ['LOCALAPPDATA']) / 'Haste2Battery'
    folder.mkdir(parents=True, exist_ok=True)
    lock = open(folder / 'instance.lock', 'a+b')
    lock.seek(0, 2)
    if not lock.tell():
        lock.write(b'0')
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
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
    import startup_config
    command = launch_command()

    def autostart_enabled(item=None):
        try:
            return startup_config.is_enabled(command)
        except OSError:
            logger.exception('Could not read Windows startup state')
            return False

    def toggle_autostart(icon, item):
        try:
            startup_config.set_enabled(command, not startup_config.is_enabled(command))
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


if __name__ == '__main__':
    try:
        run()
    except Exception:
        import traceback
        report = traceback.format_exc()
        folder = Path(os.environ.get('LOCALAPPDATA', '.')) / 'Haste2Battery'
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'startup-error.txt').write_text(report, encoding='utf-8')
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, report, 'Haste2 Battery: помилка запуску', 16)
        else:
            raise
