"""Tray icon rendering. Platform independent (needs Pillow)."""
import os
from pathlib import Path


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
