#!/usr/bin/env python3
"""Erzeugt Linkvorschau-Bilder (1200 x 630) im Flyer-Look.

make_og(ziel, zeile1, zeile2, unten) – wird von build.py aufgerufen.
Braucht Pillow und die Schriften in _quellen/src/fonts/.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
W, H = 1200, 630
NAVY = (38, 50, 107)
BERRY = (189, 59, 115)
HOT = (221, 35, 125)
WHITE = (255, 255, 255)


def font(weight, size, fam='league-spartan'):
    return ImageFont.truetype(os.path.join(SRC, 'fonts', f'{fam}-latin-{weight}-normal.woff'), size)


def fit(text, weight, size, maxw, fam='league-spartan'):
    while size > 30:
        f = font(weight, size, fam)
        if f.getbbox(text)[2] <= maxw:
            return f
        size -= 2
    return font(weight, size, fam)


def make_og(dest, line1, line2, bottom, photo='demo-blockade.jpg'):
    img = Image.new('RGB', (W, H), NAVY)
    # Foto oben
    ph = Image.open(os.path.join(SRC, 'img', photo)).convert('RGB')
    r = W / ph.width
    ph = ph.resize((W, int(ph.height * r)), Image.LANCZOS)
    top = int(ph.height * 0.18)
    ph = ph.crop((0, top, W, top + 300))
    ph = ImageEnhance.Brightness(ph).enhance(0.85)
    img.paste(ph, (0, 0))

    # Schräge Balken (wie Flyer, -3°)
    layer = Image.new('RGBA', (W + 300, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, W + 300, 8), fill=WHITE)
    d.rectangle((0, 8, W + 300, 150), fill=NAVY)
    d.rectangle((0, 150, W + 300, 158), fill=WHITE)
    d.rectangle((0, 158, W + 300, 360), fill=BERRY)
    f1 = fit(line1, 800, 92, 1000)
    d.text((190, 80), line1, font=f1, fill=WHITE, anchor='lm')
    f2 = fit(line2, 800, 76, 860)
    d.text((W + 120, 222), line2, font=f2, fill=WHITE, anchor='rm')
    layer = layer.rotate(3, resample=Image.BICUBIC, expand=True)
    img.paste(layer, (-150, 222), layer)

    # Navy unten
    d = ImageDraw.Draw(img)
    d.polygon([(0, 630), (0, 545), (W, 482), (W, 630)], fill=NAVY)

    # Logo mit weißem Ring
    logo = Image.open(os.path.join(SRC, 'img', 'logo.webp')).convert('RGBA').resize((200, 200), Image.LANCZOS)
    ring = Image.new('RGBA', (216, 216), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, 215, 215), fill=WHITE)
    ring.paste(logo, (8, 8), logo)
    img.paste(ring, (56, 396), ring)

    # Unten rechts: Aufforderung mit gezeichnetem Pfeil
    fb = font(700, 34, 'figtree')
    tw = fb.getbbox(bottom)[2]
    x1 = W - 56
    x0 = x1 - tw - 22 - 40 - 22
    y0, y1 = 536, 600
    d.rectangle((x0, y0, x1, y1), fill=HOT)
    d.text((x0 + 22, (y0 + y1) // 2 + 2), bottom, font=fb, fill=WHITE, anchor='lm')
    ax, ay = x1 - 22 - 26, (y0 + y1) // 2
    d.line((ax - 4, ay, ax + 22, ay), fill=WHITE, width=5)
    d.polygon([(ax + 26, ay), (ax + 12, ay - 12), (ax + 12, ay + 12)], fill=WHITE)

    img.save(dest, 'PNG', optimize=True)
    return dest


if __name__ == '__main__':
    make_og('/tmp/og-test.png', 'Wir stehen zusammen.', 'SOZIALSTAAT VERTEIDIGEN.', 'Gib dein Protestversprechen ab')
