"""
art_islamic.py - calm backgrounds and props for the Islamic-content videos (all drawn with Pillow, no image files needed).

Backgrounds:  masjid (prayer hall) | masjid_yard (outside, dome + minarets) | home (living room) | classroom (madrasa)
Title card :  title_islamic
Props:        dastarkhan (food spread) | glass_pieces (broken glass) | rehal (Quran stand, no writing drawn)
No living thing is drawn in any background.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from .art import Cv, W, H, smooth, vgrad, glow, shade

GREEN = (28, 112, 92, 255)
GREEN_D = (16, 70, 60, 255)
GOLD = (236, 196, 96, 255)
GOLD_D = (190, 146, 58, 255)
CREAM = (244, 236, 214, 255)
NOLINE = None


# ------------------------------------------------------------------ small helpers
def star8(c, cx, cy, r, fill, line=(58, 36, 28, 255), lw=1.6):
    """Eight-pointed star (two squares) - the classic geometric Islamic pattern."""
    for rot in (0, math.pi / 4):
        pts = [(cx + r * math.cos(rot + k * math.pi / 2 + math.pi / 4), cy + r * math.sin(rot + k * math.pi / 2 + math.pi / 4)) for k in range(4)]
        c.poly(pts, fill, line=line, lw=lw)


def pointed_arch(cx, y_base, half_w, h):
    """Points of a pointed (Islamic) arch from the bottom-left, over the top, to the bottom-right."""
    pts = [(cx - half_w, y_base)]
    for k in range(0, 21):
        t = k / 20.0
        a = math.pi - t * math.pi
        x = cx + half_w * math.cos(a)
        rise = (1 - abs(2 * t - 1) ** 1.7)
        pts.append((x, y_base - (h - 20) * 0.45 - rise * (h - (h - 20) * 0.45)))
    pts.append((cx + half_w, y_base))
    return pts


def crescent(img, cx, cy, r, color=GOLD):
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    d.ellipse((cx - r * 0.62 + r * 0.38, cy - r * 0.86, cx + r * 1.12 + r * 0.38, cy + r * 0.86), fill=0)
    solid = Image.new("RGBA", img.size, color)
    img.paste(solid, (0, 0), layer)


def _lattice(c, x0, y0, x1, y1, step=52, col=(0, 0, 0, 40)):
    for y in range(int(y0), int(y1), step):
        for x in range(int(x0), int(x1), step):
            star8(c, x + step / 2, y + step / 2, step * 0.34, (0, 0, 0, 0), line=col, lw=1.2)


def _perspective_floor(img, y0, top_col, bot_col, line_col, vx=640, n=14):
    img.alpha_composite(vgrad(W, H - y0, top_col, bot_col), (0, y0))
    c = Cv(W, H)
    for i in range(-n, n + 1):                                    # lines running to the vanishing point
        c.line([(vx + i * 26, y0), (vx + i * 150, H)], fill=line_col, lw=2)
    yy = y0
    gap = 12
    while yy < H:
        c.line([(0, yy), (W, yy)], fill=line_col, lw=2)
        yy += gap
        gap *= 1.28
    img.alpha_composite(c.done())


def _arch_window(img, cx, y_base, half_w, h, sky_top=(170, 214, 240), sky_bot=(236, 246, 250)):
    pts = pointed_arch(cx, y_base, half_w, h)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    sky = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sky.alpha_composite(vgrad(int(half_w * 2), int(h), sky_top, sky_bot), (int(cx - half_w), int(y_base - h)))
    img.paste(sky, (0, 0), mask)
    c = Cv(W, H)
    c.poly(pts, (0, 0, 0, 0), line=GOLD_D, lw=7)
    c.line([(cx, y_base - h + 24), (cx, y_base)], fill=GOLD_D, lw=4)
    for k in (0.38, 0.66):
        c.line([(cx - half_w, y_base - h * k), (cx + half_w, y_base - h * k)], fill=GOLD_D, lw=4)
    img.alpha_composite(c.done())


# ------------------------------------------------------------------ MASJID (inside)
def make_masjid(evening=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 490, (240, 232, 208), (222, 206, 172) if not evening else (200, 176, 140)))
    c = Cv(W, H)
    c.poly([(0, 36), (W, 36), (W, 78), (0, 78)], GREEN, line=NOLINE)                      # frieze
    for x in range(30, W, 60):
        star8(c, x, 57, 17, GOLD)
    c.poly([(0, 78), (W, 78), (W, 86), (0, 86)], GOLD_D, line=NOLINE)
    _lattice(c, 0, 92, W, 470, 64, (150, 120, 70, 50))
    img.alpha_composite(c.done())
    # mihrab niche (centre)
    c = Cv(W, H)
    outer = pointed_arch(640, 500, 190, 380)
    c.poly(outer, GOLD_D, lw=3)
    mid = pointed_arch(640, 500, 166, 350)
    c.poly(mid, GREEN_D, lw=2.4)
    inner = pointed_arch(640, 500, 134, 316)
    c.poly(inner, (22, 96, 80, 255), lw=2)
    img.alpha_composite(c.done())
    glow_ = glow(190, (255, 230, 150), 90 if not evening else 140)
    img.alpha_composite(glow_, (640 - glow_.width // 2, 360 - glow_.height // 2))
    c = Cv(W, H)
    for k in range(5):                                                                       # niche shell ribs
        c.line([(640, 220), (640 + (k - 2) * 52, 330)], fill=(240, 200, 100, 150), lw=2.4)
    c.arc((540, 220, 740, 340), 200, 340, fill=(240, 200, 100, 200), lw=3)
    star8(c, 640, 190, 22, GOLD)
    # side windows
    img.alpha_composite(c.done())
    sky = ((255, 190, 130), (150, 120, 170)) if evening else ((170, 214, 240), (236, 246, 250))
    _arch_window(img, 250, 470, 82, 300, *sky)
    _arch_window(img, 1030, 470, 82, 300, *sky)
    # pillars
    c = Cv(W, H)
    for px in (70, 1210):
        c.rrect((px - 34, 140, px + 34, 500), 8, (226, 210, 176, 255), lw=3)
        c.rrect((px - 46, 118, px + 46, 160), 8, GOLD, lw=3)
        c.rrect((px - 44, 470, px + 44, 506), 8, GOLD_D, lw=3)
        for k in (-14, 0, 14):
            c.line([(px + k, 170), (px + k, 466)], fill=(196, 178, 140, 255), lw=2)
    # hanging lamps
    for lx, ly in ((470, 190), (810, 190)):
        c.line([(lx, 86), (lx, ly - 20)], fill=GOLD_D, lw=3)
        c.poly([(lx - 22, ly - 20), (lx + 22, ly - 20), (lx + 30, ly + 14), (lx, ly + 36), (lx - 30, ly + 14)], GOLD, lw=2.6)
        c.ell((lx - 12, ly - 6, lx + 12, ly + 20), (255, 246, 196, 255), lw=2)
    img.alpha_composite(c.done())
    for lx, ly in ((470, 190), (810, 190)):
        g = glow(70, (255, 226, 140), 150)
        img.alpha_composite(g, (lx - g.width // 2, ly - g.height // 2 + 6))
    # carpet floor with rows of prayer mats
    _perspective_floor(img, 490, (86, 144, 104), (46, 98, 72), (230, 214, 150, 120))
    if evening:
        img.alpha_composite(Image.new("RGBA", (W, H), (30, 20, 60, 46)))
    return img.convert("RGB")


# ------------------------------------------------------------------ MASJID (outside)
def make_masjid_yard(evening=False):
    top, bot = ((250, 170, 120), (252, 226, 180)) if evening else ((132, 194, 240), (232, 244, 250))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 500, top, bot))
    c = Cv(W, H)
    for cx_, cy_, s in ((200, 120, 1.0), (980, 90, 1.3), (1150, 200, 0.8)):              # clouds
        for dx, dy, r in ((0, 0, 40), (40, 10, 34), (-40, 12, 30), (10, -22, 30)):
            c.ell((cx_ + dx * s - r * s, cy_ + dy * s - r * 0.7 * s, cx_ + dx * s + r * s, cy_ + dy * s + r * 0.7 * s), (255, 255, 255, 235), line=NOLINE)
    img.alpha_composite(c.done())
    c = Cv(W, H)
    for mx in (330, 950):                                                                   # minarets
        c.rrect((mx - 26, 190, mx + 26, 500), 4, (240, 230, 206, 255), lw=3)
        c.poly([(mx - 36, 190), (mx + 36, 190), (mx + 30, 170), (mx - 30, 170)], GOLD_D, lw=2.4)
        c.rrect((mx - 24, 130, mx + 24, 172), 6, (240, 230, 206, 255), lw=3)
        c.poly([(mx - 30, 130), (mx + 30, 130), (mx, 70)], GREEN, lw=3)
        for yy in (250, 330, 410):
            c.rrect((mx - 8, yy - 16, mx + 8, yy + 16), 7, GREEN_D, lw=2)
    # main hall + dome
    c.rrect((420, 300, 860, 500), 6, (244, 236, 214, 255), lw=3.4)
    c.poly([(400, 300), (880, 300), (880, 284), (400, 284)], GOLD_D, lw=2.4)
    dome = [(470, 284)] + [(640 + 170 * math.cos(math.pi - k * math.pi / 24), 284 - 160 * math.sin(k * math.pi / 24)) for k in range(25)] + [(810, 284)]
    c.poly(dome, GREEN, lw=3.4)
    for k in (-2, -1, 0, 1, 2):
        c.line([(640 + k * 28, 284 - 150 * math.sqrt(max(0, 1 - (k * 28 / 170) ** 2))), (640 + k * 64, 284)], fill=GREEN_D, lw=2.4)
    c.line([(640, 124), (640, 96)], fill=GOLD_D, lw=4)
    for x in (480, 560, 720, 800):                                                          # arched windows
        c.poly(pointed_arch(x, 400, 22, 78), (120, 170, 190, 255), lw=2.4)
    c.poly(pointed_arch(640, 500, 52, 150), (96, 66, 44, 255), lw=3)                       # door
    c.poly(pointed_arch(640, 500, 40, 126), (126, 88, 58, 255), lw=2)
    c.line([(640, 380), (640, 500)], fill=(80, 54, 36, 255), lw=3)
    img.alpha_composite(c.done())
    crescent(img, 640, 80, 26)
    for mx in (330, 950):
        crescent(img, mx, 56, 16)
    # trees on the sides
    c = Cv(W, H)
    for tx in (90, 1190):
        c.rrect((tx - 12, 380, tx + 12, 520), 4, (112, 76, 50, 255), lw=3)
        for dx, dy, r in ((0, 330, 76), (-44, 372, 56), (44, 372, 56), (0, 290, 56)):
            c.ell((tx + dx - r, dy - r * 0.8, tx + dx + r, dy + r * 0.8), (66, 140, 80, 255) if dy > 300 else (84, 160, 92, 255), lw=3)
    img.alpha_composite(c.done())
    # paved courtyard
    img.alpha_composite(vgrad(W, H - 500, (226, 210, 176), (196, 176, 138)), (0, 500))
    c = Cv(W, H)
    for i in range(-12, 13):
        c.line([(640 + i * 20, 500), (640 + i * 150, H)], fill=(160, 140, 104, 140), lw=2)
    yy, gap = 500, 14
    while yy < H:
        c.line([(0, yy), (W, yy)], fill=(160, 140, 104, 140), lw=2)
        yy += gap
        gap *= 1.3
    img.alpha_composite(c.done())
    if evening:
        img.alpha_composite(Image.new("RGBA", (W, H), (60, 30, 70, 40)))
    return img.convert("RGB")


# ------------------------------------------------------------------ HOME
def make_home(evening=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 490, (250, 238, 214), (236, 216, 184)))
    c = Cv(W, H)
    c.poly([(0, 400), (W, 400), (W, 490), (0, 490)], (214, 186, 146, 255), line=NOLINE)    # lower wall panel
    c.poly([(0, 396), (W, 396), (W, 408), (0, 408)], (170, 130, 90, 255), line=NOLINE)
    img.alpha_composite(c.done())
    # window with curtains (left)
    sky = ((255, 190, 130), (170, 130, 170)) if evening else ((150, 204, 244), (236, 246, 250))
    img.alpha_composite(vgrad(200, 250, *sky), (170, 120))
    c = Cv(W, H)
    c.rrect((170, 120, 370, 370), 4, (0, 0, 0, 0), lw=7, line=(130, 96, 66, 255))
    c.line([(270, 120), (270, 370)], fill=(130, 96, 66, 255), lw=5)
    c.line([(170, 245), (370, 245)], fill=(130, 96, 66, 255), lw=5)
    c.ell((190, 380 - 330, 250, 380 - 270), (255, 255, 255, 200), line=NOLINE)
    for sx, x0, x1 in ((-1, 120, 190), (1, 350, 420)):
        c.poly(smooth([(x0, 100), (x1, 100), (x1 + sx * 6, 250), (x1, 392), (x0, 392), (x0 - sx * 6, 250)], True, 5), (160, 60, 74, 255), lw=2.6)
        for k in range(1, 4):
            c.line([(x0 + k * (x1 - x0) / 4, 104), (x0 + k * (x1 - x0) / 4, 388)], fill=(132, 40, 56, 255), lw=2)
    c.line([(100, 100), (440, 100)], fill=(130, 96, 66, 255), lw=6)
    # geometric wall frame (centre) - a star pattern, no writing
    c.rrect((520, 110, 760, 330), 10, (250, 244, 228, 255), lw=5, line=(130, 96, 66, 255))
    c.rrect((536, 126, 744, 314), 6, GREEN, lw=2.4)
    star8(c, 640, 220, 62, GOLD, lw=2.4)
    star8(c, 640, 220, 34, GREEN_D, lw=2)
    c.ell((624, 204, 656, 236), GOLD, lw=2)
    # bookshelf (right)
    c.rrect((880, 120, 1200, 380), 6, (150, 106, 70, 255), lw=3.4)
    for sy in (200, 290):
        c.line([(886, sy), (1194, sy)], fill=(110, 76, 48, 255), lw=6)
    rng = np.random.default_rng(7)
    cols = [(60, 110, 150), (150, 60, 70), (80, 140, 100), (210, 170, 70), (110, 80, 140), (230, 226, 210)]
    for row, (y0, y1) in enumerate(((126, 197), (206, 287), (296, 376))):
        x = 892
        while x < 1186:
            wd = int(rng.integers(18, 34))
            hh = int(rng.integers(52, y1 - y0 - 4))
            c.rrect((x, y1 - hh, min(x + wd, 1190), y1), 3, cols[int(rng.integers(0, len(cols)))], lw=2)
            x += wd + 2
    img.alpha_composite(c.done())
    # wood floor
    img.alpha_composite(vgrad(W, H - 490, (198, 148, 102), (150, 102, 68)), (0, 490))
    c = Cv(W, H)
    for i in range(-14, 15):
        c.line([(640 + i * 30, 490), (640 + i * 170, H)], fill=(120, 80, 52, 120), lw=2)
    yy, gap = 490, 18
    while yy < H:
        c.line([(0, yy), (W, yy)], fill=(120, 80, 52, 90), lw=2)
        yy += gap
        gap *= 1.22
    # rug
    c.poly([(330, 560), (950, 560), (1040, 700), (240, 700)], (96, 36, 52, 255), lw=3)
    c.poly([(352, 572), (928, 572), (1006, 690), (274, 690)], (30, 100, 84, 255), lw=2.4)
    for k in range(9):
        star8(c, 400 + k * 60 + (0 if k % 2 == 0 else 6), 628 + (4 if k % 2 else 0), 12, GOLD, lw=1.4)
    img.alpha_composite(c.done())
    if evening:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 160, 60, 38)))
    return img.convert("RGB")


# ------------------------------------------------------------------ CLASSROOM (madrasa)
def make_classroom():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 490, (232, 242, 228), (212, 226, 206)))
    c = Cv(W, H)
    c.poly([(0, 410), (W, 410), (W, 490), (0, 490)], (178, 202, 176, 255), line=NOLINE)
    c.poly([(0, 404), (W, 404), (W, 416), (0, 416)], GREEN_D, line=NOLINE)
    for x in range(30, W, 60):
        star8(c, x, 40, 15, GREEN, lw=1.2)
    c.poly([(0, 66), (W, 66), (W, 72), (0, 72)], GOLD_D, line=NOLINE)
    # green board with chalk drawings (no letters)
    c.rrect((300, 110, 980, 360), 8, (150, 108, 70, 255), lw=3.4)
    c.rrect((318, 126, 962, 344), 4, (44, 92, 76, 255), lw=2.4)
    c.line([(330, 352), (970, 352)], fill=(120, 84, 54, 255), lw=8)
    for k in range(3):
        c.ell((620 + k * 70, 340, 660 + k * 70, 352), (240, 240, 235, 255), lw=1.4)
    chalk = (236, 240, 232, 255)
    star8(c, 470, 220, 56, (0, 0, 0, 0), line=chalk, lw=3)
    c.ell((780, 170, 860, 250), (0, 0, 0, 0), line=chalk, lw=3)
    c.arc((770, 160, 870, 260), 40, 320, fill=chalk, lw=3)
    for k in range(4):
        c.line([(620, 170 + k * 34), (740 - (k % 2) * 40, 170 + k * 34)], fill=chalk, lw=3)
    c.line([(790, 290), (806, 308), (840, 264)], fill=(250, 220, 120, 255), lw=5)            # a tick mark
    # window (right) and clock (left)
    c.poly(pointed_arch(1130, 380, 62, 250), (0, 0, 0, 0), line=(130, 96, 66, 255), lw=6)
    c.ell((120, 120, 220, 220), (252, 250, 240, 255), lw=5, line=(130, 96, 66, 255))
    for a in range(12):
        ang = a * math.pi / 6
        c.line([(170 + 42 * math.sin(ang), 170 - 42 * math.cos(ang)), (170 + 36 * math.sin(ang), 170 - 36 * math.cos(ang))], fill=(58, 36, 28, 255), lw=2)
    c.line([(170, 170), (170, 140)], fill=(58, 36, 28, 255), lw=3.4)
    c.line([(170, 170), (190, 178)], fill=(58, 36, 28, 255), lw=3.4)
    img.alpha_composite(c.done())
    _arch_window(img, 1130, 380, 56, 244)
    # floor with long sitting mats
    img.alpha_composite(vgrad(W, H - 490, (196, 152, 108), (150, 108, 72)), (0, 490))
    c = Cv(W, H)
    for i in range(-14, 15):
        c.line([(640 + i * 30, 490), (640 + i * 170, H)], fill=(120, 80, 52, 110), lw=2)
    yy, gap = 490, 18
    while yy < H:
        c.line([(0, yy), (W, yy)], fill=(120, 80, 52, 80), lw=2)
        yy += gap
        gap *= 1.22
    for k, (y0, y1, inset) in enumerate(((505, 540, 150), (640, 700, 40))):
        c.poly([(inset, y0), (W - inset, y0), (W - inset + 20, y1), (inset - 20, y1)], (236, 232, 214, 255), lw=2.6)
        c.poly([(inset + 10, y0 + 5), (W - inset - 10, y0 + 5), (W - inset + 6, y1 - 5), (inset - 6, y1 - 5)], (86, 150, 120, 120), lw=2)
    img.alpha_composite(c.done())
    return img.convert("RGB")


# ------------------------------------------------------------------ TITLE CARD (calm, green and gold)
def make_title_islamic():
    img = vgrad(W, H, (14, 84, 72), (6, 46, 44))
    c = Cv(W, H)
    _lattice(c, 0, 0, W, H, 80, (255, 226, 140, 26))
    img.alpha_composite(c.done())
    gl = glow(380, (255, 220, 130), 70)
    img.alpha_composite(gl, (W // 2 - gl.width // 2, H // 2 - gl.height // 2 + 20))
    c = Cv(W, H)
    c.rrect((20, 20, W - 20, H - 20), 22, (0, 0, 0, 0), line=GOLD, lw=4)
    c.rrect((36, 36, W - 36, H - 36), 16, (0, 0, 0, 0), line=(236, 196, 96, 140), lw=2)
    for x in range(80, W - 60, 56):
        star8(c, x, 52, 9, GOLD, lw=1)
        star8(c, x, H - 52, 9, GOLD, lw=1)
    star8(c, W / 2, 112, 8, GOLD, lw=1)
    img.alpha_composite(c.done())
    crescent(img, W // 2 + 4, 140, 30)
    return img.convert("RGB")


# ------------------------------------------------------------------ PROPS
def draw_dastarkhan():
    """Food spread on a cloth on the floor: cloth, a big dish of rice, a curry bowl, flat bread, a glass."""
    c = Cv(560, 150)
    c.poly([(10, 66), (550, 66), (538, 140), (22, 140)], (250, 246, 232, 255), lw=3)
    c.poly([(10, 66), (550, 66), (546, 80), (14, 80)], GREEN, lw=2.4)
    c.ell((190, 36, 370, 96), (236, 236, 230, 255), lw=3)                                    # big plate
    c.ell((208, 28, 352, 80), (250, 226, 150, 255), lw=2.4)                                  # rice
    for k in range(7):
        c.ell((226 + k * 16, 40 + (k % 2) * 8, 238 + k * 16, 48 + (k % 2) * 8), (210, 90, 60, 255), line=None)
    c.ell((60, 70, 150, 110), (236, 236, 230, 255), lw=3)                                    # bowl
    c.ell((68, 70, 142, 92), (200, 120, 60, 255), lw=2)
    c.ell((414, 78, 500, 116), (236, 236, 230, 255), lw=3)                                   # roti plate
    c.ell((424, 76, 490, 100), (230, 190, 120, 255), lw=2)
    c.poly([(388, 44), (412, 44), (410, 82), (390, 82)], (200, 230, 244, 200), lw=2.4)       # glass
    return c.done()


def draw_glass_pieces():
    c = Cv(220, 70)
    for pts in ([(20, 50), (60, 20), (80, 54)], [(90, 56), (120, 26), (150, 58)], [(150, 44), (186, 30), (196, 58)],
                [(50, 62), (70, 50), (98, 64)]):
        c.poly(pts, (200, 232, 246, 220), lw=2.2)
    return c.done()


def draw_rehal():
    """Wooden folding stand with an open book (lines only - no writing)."""
    c = Cv(260, 200)
    c.line([(50, 190), (200, 90)], fill=(112, 76, 50, 255), lw=14)
    c.line([(210, 190), (60, 90)], fill=(112, 76, 50, 255), lw=14)
    c.poly([(30, 90), (230, 90), (222, 110), (38, 110)], (150, 106, 70, 255), lw=3)
    c.poly([(40, 90), (128, 20), (128, 90)], (252, 246, 226, 255), lw=3)
    c.poly([(220, 90), (132, 20), (132, 90)], (252, 246, 226, 255), lw=3)
    for k in range(5):
        c.line([(52 + k * 6, 84 - k * 11), (118, 84 - k * 11 - 2)], fill=(150, 130, 90, 255), lw=2)
        c.line([(208 - k * 6, 84 - k * 11), (142, 84 - k * 11 - 2)], fill=(150, 130, 90, 255), lw=2)
    return c.done()


def build_islamic_assets(out):
    from pathlib import Path
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    make_masjid(False).save(out / "bg_masjid.png")
    make_masjid(True).save(out / "bg_masjid_evening.png")
    make_masjid_yard(False).save(out / "bg_masjid_yard.png")
    make_masjid_yard(True).save(out / "bg_masjid_yard_evening.png")
    make_home(False).save(out / "bg_home.png")
    make_home(True).save(out / "bg_home_evening.png")
    make_classroom().save(out / "bg_classroom.png")
    make_title_islamic().save(out / "bg_title_islamic.png")
    draw_dastarkhan().save(out / "prop_dastarkhan.png")
    draw_glass_pieces().save(out / "prop_glass_pieces.png")
    draw_rehal().save(out / "prop_rehal.png")
