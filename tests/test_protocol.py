import pytest

from haste2_battery.protocol import decode_response


def report(level, width=64):
    return (b'\x51\x02' + bytes([level])).ljust(width, b'\0')


def test_decodes_64_byte_report():
    assert decode_response(report(87)) == 87


def test_decodes_65_byte_report_with_report_id():
    assert decode_response(b'\0' + report(42)) == 42


def test_finds_report_in_second_frame():
    assert decode_response(b'\x00' * 64 + report(10)) == 10


@pytest.mark.parametrize('data', [b'', b'\x51\x02\x65'.ljust(64, b'\0'), b'\x51\x02\x10'])
def test_rejects_invalid(data):
    with pytest.raises(ValueError):
        decode_response(data)


def test_ignores_pattern_not_on_frame_boundary():
    data = (b'\0' + b'\x51\x02\x20').ljust(64, b'\0')
    with pytest.raises(ValueError):
        decode_response(data)
