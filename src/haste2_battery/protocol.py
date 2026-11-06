"""HID battery query for the Haste 2 receiver. Platform independent (needs `hidapi`)."""
import time

VID, PID = 0x03F0, 0x0F98


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
