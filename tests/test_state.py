import json
import threading

import pytest

from haste2_battery.render import battery_color
from haste2_battery.state import IntervalSettings, ReadingCache, RefreshGate, next_wake_delay


def test_colors():
    assert battery_color(None) == '#94a3b8'
    assert battery_color(80) == '#22c55e'
    assert battery_color(79) == '#facc15'
    assert battery_color(50) == '#facc15'
    assert battery_color(49) == '#fb923c'
    assert battery_color(20) == '#fb923c'
    assert battery_color(19) == '#ef4444'


def test_settings_default_and_persist(tmp_path):
    path = tmp_path / 's.json'
    assert IntervalSettings(path).minutes == 3
    IntervalSettings(path).set(5)
    assert IntervalSettings(path).minutes == 5


@pytest.mark.parametrize('bad', [2, '3', True, None, 0])
def test_settings_rejects_invalid_value(tmp_path, bad):
    with pytest.raises(ValueError):
        IntervalSettings(tmp_path / 's.json').set(bad)


def test_settings_ignores_corrupt_file(tmp_path):
    path = tmp_path / 's.json'
    path.write_text(json.dumps({'interval_minutes': 99}))
    assert IntervalSettings(path).minutes == 3
    path.write_text('not json')
    assert IntervalSettings(path).minutes == 3


def test_cache_keeps_reading_then_expires():
    cache = ReadingCache()
    cache.success(70, now=1000)
    assert cache.visible_value(1001) == 70
    assert cache.after_failure(1010) == 70          # 1 failure -> 15 min grace
    assert cache.visible_value(1000 + 899) == 70
    assert cache.visible_value(1000 + 900) is None


def test_cache_expires_faster_after_three_failures():
    cache = ReadingCache()
    cache.success(70, now=1000)
    for _ in range(3):
        cache.after_failure(1010)
    assert cache.visible_value(1000 + 179) == 70
    assert cache.visible_value(1000 + 180) is None


def test_cache_success_resets_failures():
    cache = ReadingCache()
    cache.success(70, 0)
    cache.after_failure(1)
    cache.success(60, 2)
    assert cache.failures == 0 and cache.visible_value(10**6) == 60


def test_next_wake_delay_uses_earliest_deadline():
    cache = ReadingCache()
    cache.success(50, 0)
    cache.after_failure(1)                           # expires at 900
    assert next_wake_delay(100, 100, 3, cache, 50) == 180
    assert next_wake_delay(800, 700, 5, cache, 50) == 100   # cache deadline wins
    assert next_wake_delay(10**6, 0, 1, cache, None) == 0


def test_refresh_gate_throttles_and_blocks_while_busy():
    gate, event = RefreshGate(), threading.Event()
    assert gate.request(event, 100) is True and event.is_set()
    assert gate.request(event, 102) is False         # within 5 s
    assert gate.request(event, 106) is True
    gate.begin(event, 107)
    assert not event.is_set()
    assert gate.request(event, 200) is False         # busy
    gate.finish()
    assert gate.request(event, 200) is True
    assert gate.consume_request() is True
    assert gate.consume_request() is False
