"""Polling state: settings, cached reading, refresh throttling. Platform independent."""
import json
import threading
import time
from pathlib import Path


class IntervalSettings:
    OPTIONS = (1, 3, 5, 30, 60, 180, 360)   # minutes

    def __init__(self, path):
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
        if type(value) is not int or value not in self.OPTIONS:
            raise ValueError('Invalid polling interval')
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'interval_minutes': value}), encoding='utf-8')
            temporary.replace(self.path)
            self._minutes = value


class UpdateSettings:
    """Remembers which new version was already announced (the check period is fixed)."""
    CHECK_SECONDS = 6 * 3600     # plus one check at start

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self._notified = ''
        try:
            value = json.loads(self.path.read_text(encoding='utf-8')).get('notified')
            if isinstance(value, str):
                self._notified = value
        except (OSError, ValueError, AttributeError):
            pass

    @property
    def notified(self):
        with self.lock:
            return self._notified

    def set_notified(self, version):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps({'notified': version}), encoding='utf-8')
            temporary.replace(self.path)
            self._notified = version


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
