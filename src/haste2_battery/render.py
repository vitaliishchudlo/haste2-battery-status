"""Tray icon rendering. Platform independent (needs Pillow)."""
import os
import sys
from pathlib import Path


def font_candidates():
    if sys.platform == 'darwin':
        return [('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 0),
                ('/System/Library/Fonts/Helvetica.ttc', 1)]
    return [(str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'arialbd.ttf'), 0)]


def load_font(size):
    from PIL import ImageFont
    for path, index in font_candidates():
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


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


def make_image(value, stale=False, update=False):
    from PIL import Image, ImageDraw
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 7, 62, 57), radius=10, fill=battery_color(value))
    label = '?' if value is None else str(value)
    size = 30 if len(label) == 3 else 40
    font = load_font(size)
    box = draw.textbbox((0, 0), label, font=font)
    draw.text(((64 - (box[2]-box[0]))/2-box[0],
               (64 - (box[3]-box[1]))/2-box[1]),
              label, font=font, fill='#101827')
    if stale:
        draw.ellipse((49, 1, 63, 15), fill='#64748b', outline='#ffffff', width=2)
    if update:   # blue dot, top-left (the stale marker is top-right)
        draw.ellipse((1, 1, 15, 15), fill='#3b82f6', outline='#ffffff', width=2)
    return image
