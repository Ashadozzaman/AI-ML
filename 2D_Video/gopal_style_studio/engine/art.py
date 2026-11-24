"""
art.py - draws everything with Pillow (no external images needed).

Characters are built from separate PNG parts (head, torso, arms, legs, face features)
so rig.py can rotate them around pivot points, like paper cut-out animation.
Edit the "design" block of a character in story.json to change the look.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 3                                # supersampling factor (smooth edges)
OUT = (58, 36, 28, 255)               # outline colour (dark brown)
W, H = 1280, 720


def col(c, a=255):
    return (int(c[0]), int(c[1]), int(c[2]), a)


def shade(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))), 255)


# ------------------------------------------------------------------ drawing helper
class Cv:
    """Transparent canvas drawn at SS x resolution and shrunk at the end."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts, fill, line=OUT, lw=3):
        p = self.P(pts)
        self.d.polygon(p, fill=fill)
        if line:
            self.d.line(p + [p[0]], fill=line, width=int(lw * SS), joint="curve")

    def ell(self, box, fill, line=OUT, lw=3):
        b = [v * SS for v in box]
        if line:
            self.d.ellipse(b, fill=fill, outline=line, width=int(lw * SS))
        else:
            self.d.ellipse(b, fill=fill)

    def rrect(self, box, r, fill, line=OUT, lw=3):
        b = [v * SS for v in box]
        if line:
            self.d.rounded_rectangle(b, radius=r * SS, fill=fill, outline=line, width=int(lw * SS))
        else:
            self.d.rounded_rectangle(b, radius=r * SS, fill=fill)

    def line(self, pts, fill=OUT, lw=3):
        self.d.line(self.P(pts), fill=fill, width=int(lw * SS), joint="curve")

    def arc(self, box, a0, a1, fill=OUT, lw=3):
        self.d.arc([v * SS for v in box], a0, a1, fill=fill, width=int(lw * SS))

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def smooth(pts, closed=True, n=10):
    """Catmull-Rom spline through points -> smooth polyline."""
    pts = list(pts)
    out = []
    m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[(i + 1) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(pts[-1])
    return out


def mirror_pts(pts, cx):
    return [(2 * cx - x, y) for x, y in pts]


# ------------------------------------------------------------------ default designs
DESIGNS = {
    "king": dict(skin=(222, 168, 120), hair=(35, 28, 25), face_w=156, face_h=168, nose=1.0, beard="mustache",
                 hat="crown", hat_main=(236, 190, 60), hat_accent=(200, 40, 60),
                 coat=(150, 30, 50), trim=(236, 190, 60), style="kurta", build=1.12,
                 pants=(245, 235, 210), shoes=(236, 190, 60), curled=True, jewelry=True, scale=0.70),
    "minister": dict(skin=(196, 140, 98), hair=(30, 25, 25), face_w=132, face_h=184, nose=1.15, beard="goatee",
                     hat="turban", hat_main=(60, 110, 84), hat_accent=(236, 190, 60),
                     coat=(112, 82, 58), trim=(60, 110, 84), style="kurta", build=0.92,
                     pants=(240, 232, 214), shoes=(90, 60, 42), curled=False, jewelry=False, scale=0.72),
    "jester": dict(skin=(205, 150, 108), hair=(40, 28, 22), face_w=148, face_h=160, nose=1.45, beard="none",
                   hat="jester", hat_main=(214, 60, 52), hat_accent=(244, 196, 48),
                   coat=(46, 150, 120), trim=(244, 196, 48), style="tunic", build=0.98,
                   pants=(214, 60, 52), shoes=(244, 196, 48), curled=True, jewelry=False, scale=0.65),
}


def design(name_or_dict):
    if isinstance(name_or_dict, str):
        return dict(DESIGNS[name_or_dict])
    base = dict(DESIGNS.get(name_or_dict.get("base", "king")))
    base.update({k: v for k, v in name_or_dict.items() if k != "base"})
    return base


# ------------------------------------------------------------------ HEAD
HEAD_W, HEAD_H = 260, 340
HCX, HCY = 130, 190                    # face centre in head canvas
HEAD_PIVOT = (130, 312)                # neck base


def draw_head(d):
    c = Cv(HEAD_W, HEAD_H)
    skin, hair = col(d["skin"]), col(d["hair"])
    fw, fh = d["face_w"], d["face_h"]

    # neck
    c.rrect((HCX - 25, HCY + fh / 2 - 22, HCX + 25, HEAD_PIVOT[1] + 2), 8, shade(d["skin"], 0.88))
    # hair behind ears / sideburns
    for sx in (-1, 1):
        c.rrect((HCX + sx * (fw / 2 - 2) - 9, HCY - 36, HCX + sx * (fw / 2 - 2) + 9, HCY + 22), 8, hair, line=None)
    # ears
    for sx in (-1, 1):
        ex = HCX + sx * (fw / 2 + 4)
        c.ell((ex - 16, HCY - 12, ex + 16, HCY + 28), skin)
        c.ell((ex - 7, HCY - 2, ex + 7, HCY + 18), shade(d["skin"], 0.82), line=None)
    # face
    right = [(HCX, HCY - fh / 2), (HCX + fw * 0.34, HCY - fh * 0.46), (HCX + fw / 2 * 0.98, HCY - fh * 0.2),
             (HCX + fw / 2, HCY + fh * 0.06), (HCX + fw * 0.4, HCY + fh * 0.34), (HCX + fw * 0.17, HCY + fh * 0.5)]
    pts = right + [(HCX, HCY + fh / 2 + 3)] + mirror_pts(right[:0:-1], HCX)
    pts = smooth(pts, closed=True, n=8)
    c.poly(pts, skin)
    # cheeks
    for sx in (-1, 1):
        c.ell((HCX + sx * 44 - 20, HCY + 22, HCX + sx * 44 + 20, HCY + 46), (235, 120, 110, 70), line=None)
    # nose
    nz = d["nose"]
    ny = HCY + 14
    c.ell((HCX - 15 * nz, ny - 6 * nz, HCX + 15 * nz, ny + 20 * nz),
          shade(d["skin"], 1.04) if nz < 1.3 else (225, 140, 110, 255), lw=2.6)
    c.arc((HCX - 11 * nz, ny + 8 * nz, HCX - 1, ny + 20 * nz), 20, 160, lw=2)
    c.arc((HCX + 1, ny + 8 * nz, HCX + 11 * nz, ny + 20 * nz), 20, 160, lw=2)

    # facial hair
    my = HCY + 44
    if d["beard"] in ("mustache", "goatee"):
        r = [(HCX + 2, my - 6), (HCX + 24, my - 13), (HCX + 48, my - 8), (HCX + 66, my - 20), (HCX + 60, my + 2),
             (HCX + 36, my + 8), (HCX + 2, my + 4)]
        pts = smooth(mirror_pts(r[::-1], HCX) + r, closed=True, n=6)
        c.poly(pts, hair, lw=2)
    if d["beard"] == "goatee":
        g = [(HCX - 20, HCY + fh / 2 - 22), (HCX + 20, HCY + fh / 2 - 22), (HCX + 16, HCY + fh / 2 + 2),
             (HCX, HCY + fh / 2 + 24), (HCX - 16, HCY + fh / 2 + 2)]
        c.poly(smooth(g, True, 6), hair, lw=2)

    # hats
    top = HCY - fh / 2
    hm, ha = col(d["hat_main"]), col(d["hat_accent"])
    if d["hat"] == "crown":
        base_y = top + 26
        c.rrect((HCX - fw / 2 - 2, top + 4, HCX + fw / 2 + 2, base_y), 8, ha if False else col(d["hat_main"]))
        peaks = [(-70, 36), (-46, 78), (-23, 44), (0, 92), (23, 44), (46, 78), (70, 36)]
        pts = [(HCX - 76, base_y)] + [(HCX + px, base_y - ph) for px, ph in peaks] + [(HCX + 76, base_y)]
        c.poly(pts, col(d["hat_main"]))
        c.rrect((HCX - 76, base_y - 18, HCX + 76, base_y + 6), 6, shade(d["hat_main"], 0.86))
        for px in (-48, -16, 16, 48):
            c.ell((HCX + px - 8, base_y - 12, HCX + px + 8, base_y + 4), ha, lw=2)
        for px, ph in peaks[1::2]:
            c.ell((HCX + px - 6, base_y - ph - 6, HCX + px + 6, base_y - ph + 6), (250, 250, 245, 255), lw=2)
        c.poly(smooth([(HCX - 6, base_y - 88), (HCX - 24, base_y - 108), (HCX + 4, base_y - 124),
                       (HCX + 30, base_y - 108), (HCX + 8, base_y - 90)], True, 8), (250, 246, 236, 255), lw=2.5)
        c.line([(HCX, base_y - 90), (HCX + 3, base_y - 116)], fill=(200, 190, 175, 255), lw=2)
    elif d["hat"] == "turban":
        by = top + 20
        c.poly(smooth([(HCX - fw / 2 - 12, by + 14), (HCX - fw / 2 - 8, by - 36), (HCX - 36, by - 74),
                       (HCX + 20, by - 88), (HCX + fw / 2 + 4, by - 50), (HCX + fw / 2 + 12, by + 14),
                       (HCX, by + 26)], True, 8), hm)
        for k, off in enumerate((-30, -2, 26)):
            c.arc((HCX - fw / 2 - 6, by - 78 + k * 4, HCX + fw / 2 + 14, by + 24 + k * 6), 200 + off, 340 + off,
                  fill=shade(d["hat_main"], 0.72), lw=3)
        c.line([(HCX - fw / 2 - 8, by - 10), (HCX + fw / 2 + 10, by - 40)], fill=shade(d["hat_main"], 0.8), lw=3)
        c.rrect((HCX - fw / 2 - 12, by + 6, HCX + fw / 2 + 12, by + 28), 9, ha)
        c.ell((HCX - 10, by + 7, HCX + 10, by + 27), (200, 40, 60, 255), lw=2)
        c.poly(smooth([(HCX + fw / 2 + 6, by - 20), (HCX + fw / 2 + 36, by + 10), (HCX + fw / 2 + 28, by + 52),
                       (HCX + fw / 2 + 12, by + 14)], True, 6), hm)
    elif d["hat"] == "jester":
        by = top + 18
        c.rrect((HCX - fw / 2 - 2, by, HCX + fw / 2 + 2, by + 24), 8, ha)
        for sx in (-1, 1):
            horn = [(HCX + sx * 22, by + 6), (HCX + sx * 70, by - 36), (HCX + sx * 118, by - 24),
                    (HCX + sx * 126, by + 28), (HCX + sx * 100, by + 6), (HCX + sx * 62, by + 8)]
            c.poly(smooth(horn, True, 8), hm)
            c.ell((HCX + sx * 126 - 11, by + 24, HCX + sx * 126 + 11, by + 46), ha, lw=2.5)
        c.poly(smooth([(HCX - 40, by + 6), (HCX - 24, by - 70), (HCX + 6, by - 108), (HCX + 30, by - 70),
                       (HCX + 40, by + 6)], True, 8), hm)
        c.ell((HCX - 4, by - 124, HCX + 18, by - 100), ha, lw=2.5)
        c.line([(HCX - 14, by + 6), (HCX - 4, by - 60)], fill=shade(d["hat_main"], 0.75), lw=3)
        c.line([(HCX + 20, by + 6), (HCX + 14, by - 60)], fill=shade(d["hat_main"], 0.75), lw=3)
        for k in range(5):
            xx = HCX - 56 + k * 28
            c.poly([(xx, by + 24), (xx + 14, by + 36), (xx + 28, by + 24)], ha, lw=2)
    return c.done()


# ------------------------------------------------------------------ FACE FEATURES (same canvas as head)
def eyes_img(d, state="open", gaze=0):
    c = Cv(HEAD_W, HEAD_H)
    ey = HCY - 14
    dx = 36 if d["face_w"] > 140 else 31
    for sx in (-1, 1):
        ex = HCX + sx * dx
        if state in ("open", "wide", "squint"):
            rx, ry = (17, 14) if state == "open" else (19, 20) if state == "wide" else (17, 8)
            c.ell((ex - rx, ey - ry, ex + rx, ey + ry), (252, 250, 245, 255), lw=2.6)
            pr = 8 if state != "wide" else 7
            px = ex + gaze * 6
            c.ell((px - pr, ey - pr + 1, px + pr, ey + pr + 1), (28, 22, 22, 255), line=None)
            c.ell((px - 3 + 1, ey - 5, px + 2, ey), (255, 255, 255, 255), line=None)
        elif state == "closed":
            c.arc((ex - 16, ey - 12, ex + 16, ey + 10), 20, 160, lw=3.4)
        elif state == "happy":
            c.arc((ex - 16, ey - 8, ex + 16, ey + 16), 200, 340, lw=3.6)
    return c.done()


def brows_img(d, state="neutral"):
    c = Cv(HEAD_W, HEAD_H)
    by = HCY - 46
    dx = 36 if d["face_w"] > 140 else 31
    colr = col(d["hair"])
    for sx in (-1, 1):
        ex = HCX + sx * dx
        inner, outer = ex - sx * 20, ex + sx * 22
        if state == "neutral":
            pts = [(inner, by + 2), (ex, by - 4), (outer, by + 2)]
        elif state == "angry":
            pts = [(inner, by + 10), (ex, by - 2), (outer, by - 8)]
        elif state == "surprised":
            pts = [(inner, by - 10), (ex, by - 20), (outer, by - 8)]
        elif state == "sad":
            pts = [(inner, by - 6), (ex, by - 2), (outer, by + 8)]
        else:  # happy / raised
            pts = [(inner, by - 2), (ex, by - 12), (outer, by - 2)]
        c.line(smooth(pts, closed=False, n=8), fill=colr, lw=7)
    return c.done()


def mouth_img(d, kind="closed"):
    c = Cv(HEAD_W, HEAD_H)
    my = HCY + 56
    inner, tongue, teeth = (92, 22, 34, 255), (222, 96, 110, 255), (252, 250, 244, 255)
    if kind == "closed":
        c.arc((HCX - 20, my - 14, HCX + 20, my + 6), 25, 155, lw=3.4)
    elif kind == "smile":
        c.arc((HCX - 28, my - 20, HCX + 28, my + 12), 15, 165, lw=3.6)
    elif kind == "frown":
        c.arc((HCX - 22, my - 2, HCX + 22, my + 24), 200, 340, lw=3.6)
    elif kind == "small":
        c.ell((HCX - 10, my - 8, HCX + 10, my + 8), inner, lw=2.6)
    elif kind == "mid":
        c.ell((HCX - 17, my - 10, HCX + 17, my + 12), inner, lw=2.8)
        c.ell((HCX - 9, my + 3, HCX + 9, my + 13), tongue, line=None)
    elif kind == "open":
        c.ell((HCX - 21, my - 12, HCX + 21, my + 22), inner, lw=3)
        c.ell((HCX - 12, my + 7, HCX + 12, my + 22), tongue, line=None)
        c.rrect((HCX - 15, my - 9, HCX + 15, my - 1), 3, teeth, line=None)
    elif kind == "wide":
        c.poly(smooth([(HCX - 32, my - 12), (HCX, my - 6), (HCX + 32, my - 12), (HCX + 26, my + 18),
                       (HCX, my + 30), (HCX - 26, my + 18)], True, 8), inner, lw=3)
        c.rrect((HCX - 24, my - 9, HCX + 24, my + 2), 4, teeth, line=None)
        c.ell((HCX - 14, my + 12, HCX + 14, my + 28), tongue, line=None)
    elif kind == "O":
        c.ell((HCX - 12, my - 8, HCX + 12, my + 16), inner, lw=3)
    return c.done()


# ------------------------------------------------------------------ TORSO
TORSO_W, TORSO_H = 220, 250
TORSO_PIVOT = (110, 246)               # hip centre (bottom centre)
NECK_FROM_PIVOT = (0, -214)            # neck point relative to pivot
SHOULDER_FROM_PIVOT = (66, -184)       # right shoulder offset (left = mirrored x)


def draw_torso(d):
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    coat, trim = col(d["coat"]), col(d["trim"])
    cx = 110
    sw, ww, hw = 62 * b, 54 * b, 70 * b
    top = 36
    if d["style"] == "kurta":
        pts = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
               (cx + sw, top + 4), (cx + ww, 140), (cx + hw, 246), (cx - hw, 246), (cx - ww, 140)]
    else:
        pts = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
               (cx + sw, top + 4), (cx + ww, 140), (cx + hw - 4, 214)]
        zig = []
        n = 8
        for i in range(n + 1):
            x = cx + hw - 4 - i * (2 * (hw - 4)) / n
            zig.append((x, 214 if i % 2 == 0 else 236))
        pts += zig + [(cx - ww, 140)]
    c.poly(smooth(pts, True, 3) if d["style"] == "kurta" else pts, coat)
    if d["style"] == "tunic":
        # pants waist so there is no gap between tunic and legs
        c.rrect((cx - hw + 8, 226, cx + hw - 8, 246), 4, col(d["pants"]), lw=2.5)
        # diamond pattern
        for i in range(-2, 3):
            for j in range(3):
                x, y = cx + i * 26 + (13 if j % 2 else 0), 70 + j * 36
                if abs(x - cx) > 44:
                    continue
                c.poly([(x, y - 14), (x + 13, y), (x, y + 14), (x - 13, y)], col(d["trim"]) if (i + j) % 2 else col(d["hat_main"]), lw=1.8)
    else:
        # front opening + buttons
        c.line([(cx, top + 10), (cx, 244)], fill=shade(d["coat"], 0.68), lw=3)
        for k in range(5):
            c.ell((cx - 5, 62 + k * 28, cx + 5, 72 + k * 28), trim, lw=2)
        # sash
        c.poly([(cx - ww - 2, 134), (cx + ww + 2, 134), (cx + ww + 3, 156), (cx - ww - 3, 156)], trim, lw=2.5)
        # hem trim
        c.poly([(cx - hw, 232), (cx + hw, 232), (cx + hw, 246), (cx - hw, 246)], trim, lw=2.5)
    # neckline (skin showing)
    c.poly(smooth([(cx - 26, top - 10), (cx, top + 26), (cx + 26, top - 10)], False, 8) + [(cx + 26, top - 14), (cx - 26, top - 14)],
           col(d["skin"]), lw=2.5)
    if d["jewelry"]:
        for k in range(11):
            a = math.pi * (0.08 + 0.84 * k / 10)
            x, y = cx - 34 * math.cos(a), top - 10 + 44 * math.sin(a)
            c.ell((x - 6, y - 6, x + 6, y + 6), (250, 248, 240, 255) if k != 5 else (200, 30, 60, 255), lw=1.8)
    if d["hat"] == "turban":                                    # minister's shawl
        c.poly([(cx - sw, top + 2), (cx - 20, top - 10), (cx + sw - 10, 150), (cx + sw - 34, 190), (cx - sw + 8, 78)],
               col(d["trim"]), lw=2.5)
        c.line([(cx - sw + 8, top + 22), (cx + sw - 24, 160)], fill=shade(d["trim"], 0.7), lw=2)
    if d["hat"] == "jester":                                    # ruffled collar
        for k in range(9):
            x = cx - 44 + k * 11
            c.poly([(x, top - 8), (x + 6, top + 14), (x + 12, top - 8)], col(d["trim"]), lw=2)
    return c.done()


# ------------------------------------------------------------------ ARMS
UP_W, UP_H = 44, 100
UP_PIVOT = (22, 18)
UP_LEN = 72
FA_W, FA_H = 44, 130
FA_PIVOT = (22, 16)
FA_LEN = 50


def sleeve_colors(d):
    return col(d["coat"]), col(d["trim"])


def draw_upper_arm(d):
    c = Cv(UP_W, UP_H)
    sl, tr = sleeve_colors(d)
    c.rrect((6, 6, 38, 92), 14, sl)
    if d["style"] == "tunic":
        c.rrect((6, 6, 38, 36), 14, col(d["hat_main"]))
        c.line([(6, 36), (38, 36)], lw=2)
    return c.done()


def draw_forearm(d, hand="open", soot=False):
    c = Cv(FA_W, FA_H)
    sl, tr = sleeve_colors(d)
    skin = (38, 32, 32, 255) if soot else col(d["skin"])
    c.rrect((8, 4, 36, 60), 12, sl)
    c.rrect((6, 46, 38, 62), 5, tr, lw=2.5)                      # cuff
    if hand == "open":
        c.ell((8, 58, 36, 98), skin)
        c.ell((26, 62, 42, 84), skin)                             # thumb
        c.line([(14, 76), (14, 92)], lw=1.6)
        c.line([(22, 78), (22, 94)], lw=1.6)
    elif hand == "fist":
        c.ell((7, 58, 37, 90), skin)
        c.line([(14, 64), (14, 80)], lw=1.6)
        c.line([(23, 64), (23, 80)], lw=1.6)
    elif hand == "point":
        c.ell((8, 58, 34, 84), skin)
        c.rrect((16, 76, 28, 124), 6, skin)                       # extended index finger
        c.ell((34, 64, 44, 78), skin, lw=2)
    return c.done()


# ------------------------------------------------------------------ LEGS
LEG_W, LEG_H = 90, 170
LEG_PIVOT = (34, 10)
LEG_LEN = 128                          # hip joint to ground when standing


def draw_leg(d):
    """Right leg (shoe points to +x). The left leg is the mirror image."""
    c = Cv(LEG_W, LEG_H)
    pants, shoes = col(d["pants"]), col(d["shoes"])
    c.poly([(16, 4), (52, 4), (50, 120), (18, 120)], pants)
    if d["style"] == "tunic":
        c.poly([(16, 4), (52, 4), (51, 34), (17, 34)], col(d["hat_accent"]), lw=2.5)
        c.poly([(18, 64), (50, 64), (50, 94), (18, 94)], col(d["hat_accent"]), lw=2.5)
    c.rrect((14, 108, 54, 124), 5, col(d["trim"]) if d["style"] != "tunic" else col(d["hat_accent"]), lw=2.5)
    # shoe
    if d["curled"]:
        pts = [(12, 124), (58, 120), (76, 130), (84, 114), (86, 132), (74, 148), (14, 150)]
    else:
        pts = [(12, 124), (58, 120), (78, 136), (74, 150), (14, 150)]
    c.poly(smooth(pts, True, 5), shoes)
    if d["curled"]:
        c.ell((80, 106, 94, 120), col(d["hat_accent"]) if d["style"] == "tunic" else col(d["trim"]), lw=2)
    return c.done()


# ------------------------------------------------------------------ PROPS
def draw_pot():
    c = Cv(220, 260)
    c.poly(smooth([(60, 70), (160, 70), (190, 130), (176, 210), (110, 234), (44, 210), (30, 130)], True, 8), (186, 100, 66, 255))
    c.rrect((70, 52, 150, 78), 10, (160, 80, 54, 255))
    c.ell((78, 58, 142, 74), (60, 40, 36, 255), lw=2)
    for (x, y, rx, ry) in [(88, 120, 30, 20), (136, 150, 24, 30), (100, 182, 26, 16)]:
        c.ell((x - rx, y - ry, x + rx, y + ry), (40, 32, 32, 255), line=None)
    c.line([(64, 120), (150, 118)], fill=(120, 60, 40, 255), lw=3)
    # stool
    c.rrect((50, 226, 170, 244), 6, (120, 80, 50, 255))
    c.rrect((62, 244, 78, 260), 3, (100, 66, 42, 255))
    c.rrect((142, 244, 158, 260), 3, (100, 66, 42, 255))
    return c.done()


def draw_golden_mango(size=60):
    c = Cv(size, int(size * 1.2))
    s = size
    c.poly(smooth([(s * .5, s * .1), (s * .85, s * .35), (s * .9, s * .7), (s * .55, s * 1.12), (s * .15, s * .8),
                   (s * .15, s * .38)], True, 8), (250, 200, 40, 255), lw=2.4)
    c.ell((s * .3, s * .3, s * .46, s * .5), (255, 238, 150, 255), line=None)
    c.line([(s * .5, s * .1), (s * .52, 0)], lw=2.4)
    return c.done()


def character_sheet_parts(d):
    """All parts for one character: used by rig.py."""
    d = design(d) if not isinstance(d, dict) or "skin" not in d else d
    parts = {
        "head": draw_head(d),
        "torso": draw_torso(d),
        "upper": draw_upper_arm(d),
        "leg_r": draw_leg(d),
    }
    parts["leg_l"] = parts["leg_r"].transpose(Image.FLIP_LEFT_RIGHT)
    for hand in ("open", "fist", "point"):
        for soot in (False, True):
            parts[f"fore_{hand}_{'soot' if soot else 'skin'}"] = draw_forearm(d, hand, soot)
    return d, parts


# ------------------------------------------------------------------ BACKGROUNDS
def vgrad(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float)[None, None, :]
    b = np.array(bottom, float)[None, None, :]
    img = (a * (1 - t) + b * t) * np.ones((1, w, 1))
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")


def glow(size, color, alpha=170):
    y, x = np.mgrid[-size:size, -size:size]
    r = np.sqrt(x * x + y * y) / size
    a = np.clip(1 - r, 0, 1) ** 2 * alpha
    arr = np.zeros((2 * size, 2 * size, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def make_court(evening=False):
    """Palace court hall. evening=True -> dusk windows, lamp glow, darker tint."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 480, (236, 196, 140), (206, 150, 96)))
    c = Cv(W, H)
    # frieze band
    c.poly([(0, 48), (W, 48), (W, 84), (0, 84)], (140, 34, 48, 255), line=None)
    for i in range(0, W, 40):
        c.poly([(i + 20, 52), (i + 36, 66), (i + 20, 80), (i + 4, 66)], (240, 196, 80, 255), lw=1.6)
    # pillars and arched windows
    sky_top, sky_bot = ((255, 170, 110), (120, 90, 150)) if evening else ((130, 190, 240), (230, 240, 250))
    win = vgrad(190, 300, sky_top, sky_bot)
    for k in range(5):
        x0 = 40 + k * 250
        mask = Image.new("L", (190, 300), 0)
        md = ImageDraw.Draw(mask)
        md.rectangle((0, 95, 190, 300), fill=255)
        md.ellipse((0, 0, 190, 190), fill=255)
        wcv = Image.new("RGBA", (190, 300), (0, 0, 0, 0))
        wcv.paste(win, (0, 0), mask)
        # distant hills & palms inside the window
        wd = ImageDraw.Draw(wcv)
        wd.ellipse((-60, 230, 140, 400), fill=(60, 110, 70, 255) if not evening else (40, 60, 70, 255))
        wd.ellipse((60, 250, 280, 420), fill=(80, 140, 80, 255) if not evening else (50, 70, 80, 255))
        wcv.putalpha(Image.composite(wcv.getchannel("A"), Image.new("L", (190, 300), 0), mask))
        img.alpha_composite(wcv, (x0 + 10, 110))
    c2 = Cv(W, H)
    for k in range(6):
        x0 = k * 250 - 20 + 0
        c2.rrect((x0, 100, x0 + 56, 480), 6, (178, 108, 70, 255))
        c2.rrect((x0 - 8, 96, x0 + 64, 124), 6, (240, 196, 80, 255), lw=2.5)
        c2.rrect((x0 - 8, 454, x0 + 64, 484), 6, (240, 196, 80, 255), lw=2.5)
        for yy in range(150, 440, 46):
            c2.line([(x0 + 10, yy), (x0 + 46, yy)], fill=(140, 80, 52, 255), lw=2)
    for k in range(5):                                          # arch outlines
        x0 = 50 + k * 250
        c2.arc((x0 - 2, 106, x0 + 208, 316), 180, 360, lw=6, fill=(240, 196, 80, 255))
    img.alpha_composite(c2.done())
    # floor
    fl = vgrad(W, 250, (214, 190, 150), (150, 118, 84))
    img.alpha_composite(fl, (0, 470))
    f = Cv(W, H)
    for k in range(-6, 16):                                     # tile lines in perspective
        f.line([(W / 2 + (k - 4.5) * 40, 470), (W / 2 + (k - 4.5) * 190, 720)], fill=(120, 90, 64, 120), lw=1.6)
    for k in range(1, 6):
        yy = 470 + (k ** 1.6) * 20
        f.line([(0, yy), (W, yy)], fill=(120, 90, 64, 120), lw=1.6)
    # red carpet
    f.poly([(420, 470), (860, 470), (1240, 720), (40, 720)], (150, 30, 44, 255), lw=3)
    f.poly([(446, 470), (834, 470), (1160, 720), (120, 720)], (176, 44, 56, 255), line=None)
    f.line([(446, 474), (120, 716)], fill=(240, 196, 80, 255), lw=4)
    f.line([(834, 474), (1160, 716)], fill=(240, 196, 80, 255), lw=4)
    img.alpha_composite(f.done())
    # throne on the right
    t = Cv(W, H)
    t.rrect((970, 250, 1130, 470), 40, (236, 190, 60, 255), lw=4)
    t.rrect((990, 276, 1110, 440), 30, (170, 30, 50, 255), lw=3)
    t.rrect((960, 430, 1140, 484), 10, (236, 190, 60, 255), lw=4)
    t.ell((1030, 252, 1070, 292), (200, 30, 60, 255), lw=3)
    t.poly([(950, 250), (1150, 250), (1100, 190), (1000, 190)], (150, 30, 50, 255), lw=3)
    img.alpha_composite(t.done())
    # curtains
    cu = Cv(W, H)
    for side in (0, 1):
        xs = 0 if side == 0 else W
        sg = 1 if side == 0 else -1
        cu.poly([(xs, 0), (xs + sg * 120, 0), (xs + sg * 80, 240), (xs + sg * 60, 470), (xs, 480)], (150, 30, 44, 255), lw=3)
        for i in range(1, 4):
            cu.line([(xs + sg * i * 28, 0), (xs + sg * (i * 18 + 10), 470)], fill=(110, 20, 34, 255), lw=3)
    cu.poly([(0, 0), (W, 0), (W, 40), (0, 40)], (110, 20, 34, 255), line=None)
    img.alpha_composite(cu.done())
    # hanging lamps
    lamp_x = (330, 640, 950)
    lm = Cv(W, H)
    for x in lamp_x:
        lm.line([(x, 40), (x, 118)], fill=(90, 60, 40, 255), lw=3)
        lm.poly([(x - 22, 118), (x + 22, 118), (x + 14, 150), (x - 14, 150)], (240, 196, 80, 255), lw=2.5)
        lm.ell((x - 8, 134, x + 8, 158), (255, 230, 150, 255), lw=2)
    img.alpha_composite(lm.done())
    if evening:
        shadow = Image.new("RGBA", (W, H), (50, 30, 80, 105))
        img.alpha_composite(shadow)
    for x in lamp_x:
        g = glow(150 if evening else 90, (255, 214, 120), 190 if evening else 70)
        img.alpha_composite(g, (x - g.width // 2, 146 - g.height // 2))
    return img.convert("RGB")


def make_garden(mango_on_tree=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 480, (126, 196, 244), (252, 238, 196)))
    c = Cv(W, H)
    c.ell((120, 60, 220, 160), (255, 236, 150, 255), line=None)                 # sun
    # far hills
    c.poly(smooth([(-40, 430), (200, 330), (420, 400), (640, 340), (900, 410), (1120, 350), (1320, 420), (1320, 480), (-40, 480)], True, 8),
           (122, 176, 120, 255), line=None)
    c.poly(smooth([(-40, 470), (260, 400), (520, 450), (820, 410), (1100, 455), (1320, 430), (1320, 500), (-40, 500)], True, 8),
           (92, 152, 90, 255), line=None)
    # village huts
    for hx, hy, s in [(220, 410, 1.0), (350, 424, 0.8), (560, 418, 0.9)]:
        c.poly([(hx - 40 * s, hy), (hx + 40 * s, hy), (hx + 40 * s, hy + 44 * s), (hx - 40 * s, hy + 44 * s)], (222, 190, 140, 255), lw=2.5)
        c.poly([(hx - 52 * s, hy), (hx, hy - 38 * s), (hx + 52 * s, hy)], (186, 132, 70, 255), lw=2.5)
        c.rrect((hx - 8 * s, hy + 16 * s, hx + 10 * s, hy + 44 * s), 3, (120, 80, 50, 255), lw=2)
    img.alpha_composite(c.done())
    # ground
    g = vgrad(W, 250, (118, 176, 78), (70, 128, 60))
    img.alpha_composite(g, (0, 470))
    p = Cv(W, H)
    p.poly([(500, 470), (780, 470), (1000, 720), (140, 720)], (214, 184, 130, 255), line=None)
    for _ in range(0):
        pass
    rng = np.random.default_rng(4)
    for _ in range(90):
        x, y = rng.integers(0, W), rng.integers(480, 716)
        if 500 - (y - 470) * 0.7 < x < 780 + (y - 470) * 0.9:
            continue
        p.line([(x, y), (x - 3, y - 12)], fill=(50, 110, 50, 255), lw=2)
        p.line([(x, y), (x + 3, y - 10)], fill=(50, 110, 50, 255), lw=2)
    for _ in range(26):
        x, y = rng.integers(0, W), rng.integers(500, 710)
        if 500 - (y - 470) * 0.7 < x < 780 + (y - 470) * 0.9:
            continue
        colr = [(255, 120, 150, 255), (255, 230, 90, 255), (250, 250, 250, 255)][int(rng.integers(0, 3))]
        p.ell((x - 5, y - 5, x + 5, y + 5), colr, lw=1.6)
    img.alpha_composite(p.done())
    # mango tree (right)
    t = Cv(W, H)
    t.poly([(1040, 560), (1060, 300), (1100, 300), (1120, 560), (1170, 580), (1000, 580)], (112, 76, 50, 255), lw=3)
    t.line([(1080, 330), (960, 250)], fill=(112, 76, 50, 255), lw=14)
    t.line([(1090, 320), (1190, 240)], fill=(112, 76, 50, 255), lw=14)
    for (x, y, r, shd) in [(1080, 180, 170, 0.78), (930, 240, 110, 0.85), (1200, 220, 110, 0.85),
                           (1080, 130, 120, 1.0), (980, 170, 90, 1.05), (1170, 150, 90, 1.05)]:
        t.ell((x - r, y - r * 0.8, x + r, y + r * 0.8), shade((60, 140, 64), shd), lw=3)
    for (x, y) in [(960, 300), (1020, 270), (1150, 300), (1210, 280), (1100, 240)]:
        t.ell((x - 13, y - 8, x + 13, y + 22), (150, 190, 70, 255), lw=2)
    img.alpha_composite(t.done())
    if mango_on_tree:
        m = draw_golden_mango(64)
        gl = glow(60, (255, 220, 90), 140)
        img.alpha_composite(gl, (940 - gl.width // 2, 360 - gl.height // 2))
        img.alpha_composite(m, (908, 318))
    else:
        d = Cv(W, H)
        d.line([(938, 322), (944, 346)], fill=(112, 76, 50, 255), lw=4)
        d.ell((936, 344, 948, 352), (150, 110, 60, 255), lw=2)
        img.alpha_composite(d.done())
    return img.convert("RGB")


def make_title_bg():
    img = vgrad(W, H, (110, 20, 40), (60, 10, 30))
    c = Cv(W, H)
    for r in (310, 250, 190):
        c.ell((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), None if False else (0, 0, 0, 0), line=(240, 196, 80, 120), lw=2)
    for i in range(0, W, 48):
        c.poly([(i + 24, 12), (i + 40, 30), (i + 24, 48), (i + 8, 30)], (240, 196, 80, 255), lw=1.6)
        c.poly([(i + 24, H - 48), (i + 40, H - 30), (i + 24, H - 12), (i + 8, H - 30)], (240, 196, 80, 255), lw=1.6)
    img.alpha_composite(c.done())
    gl = glow(220, (255, 210, 110), 90)
    img.alpha_composite(gl, (W // 2 - gl.width // 2, 215 - gl.height // 2 + 90))
    m = draw_golden_mango(110)
    img.alpha_composite(m, (W // 2 - m.width // 2, 140))
    return img.convert("RGB")


def build_all_assets(out_dir):
    """Write every background / prop PNG into assets/ (called by notebook 01)."""
    from pathlib import Path
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    make_court(False).save(out / "bg_court.png")
    make_court(True).save(out / "bg_court_evening.png")
    make_garden(True).save(out / "bg_garden.png")
    make_garden(False).save(out / "bg_garden_empty.png")
    make_title_bg().save(out / "bg_title.png")
    draw_pot().save(out / "prop_pot.png")
    draw_golden_mango(60).save(out / "prop_mango.png")
