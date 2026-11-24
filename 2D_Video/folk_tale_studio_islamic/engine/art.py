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
        if not line and len(fill) == 4 and fill[3] < 255:          # see-through shapes (blush) must blend, not punch holes
            layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).ellipse(b, fill=fill)
            self.im.alpha_composite(layer)
            return
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
    # ---- the Gopal Bhar cast (original drawings inspired by the folk-tale tradition) ----
    # Chikna Bhar (the lead jester): bald (takla) head with a small tuft (tiki), tilak, big moustache, dhoti + shoulder cloth, bare feet
    "chikna": dict(skin=(240, 200, 160), hair=(30, 24, 22), face_w=176, face_h=164, nose=1.75, beard="none",
                  hat="bald", hat_main=(240, 200, 160), hat_accent=(200, 40, 60),
                  coat=(246, 214, 52), trim=(214, 48, 38), style="kurta_dhoti", build=1.2, shoulder=72,
                  pants=(236, 98, 40), shoes=(32, 28, 30), curled=False, jewelry=False, scale=0.60),
    # Raja Krishnachandra: royal pagri with jewel + plume, maroon-and-gold coat, pearls, grand moustache
    "krishnachandra": dict(skin=(226, 174, 128), hair=(32, 26, 24), face_w=160, face_h=170, nose=1.05, beard="mustache",
                           hat="pagri", hat_main=(170, 28, 50), hat_accent=(240, 196, 80),
                           coat=(120, 22, 46), trim=(240, 196, 80), style="kurta", build=1.14,
                           pants=(246, 238, 214), shoes=(240, 196, 80), curled=True, jewelry=True, scale=0.71),
    # Mantri: tall violet pagri, white moustache and pointed beard, scheming look, long shawl
    "mantri": dict(skin=(196, 144, 104), hair=(232, 228, 220), face_w=130, face_h=186, nose=1.2, beard="goatee",
                   hat="pagri_tall", hat_main=(86, 52, 128), hat_accent=(240, 196, 80),
                   coat=(58, 66, 128), trim=(214, 208, 226), style="kurta", build=0.94,
                   pants=(240, 232, 214), shoes=(90, 60, 42), curled=False, jewelry=False, scale=0.73),
    # Ginni (Gopal's wife): plump, hair parted and pulled back, red bindi, blue saree + yellow blouse, red bangle, bare feet
    "ginni": dict(skin=(240, 200, 165), hair=(28, 22, 22), face_w=164, face_h=160, nose=0.8, beard="none",
                  hat="bun", bindi=True, sindoor=False, earrings=False, nath=False, flowers=False, hat_main=(28, 22, 22),
                  hat_accent=(240, 196, 80), coat=(70, 156, 206), trim=(30, 104, 160), blouse=(246, 210, 60),
                  style="saree", build=1.38, pants=(70, 156, 206), shoes=(240, 200, 165), curled=False,
                  jewelry=False, scale=0.60),
}


DESIGNS["gopal"] = DESIGNS["chikna"]          # old name still works

# ---- the Islamic-content cast (original drawings; ordinary people only - no prophets, sahaba or angels are drawn) ----
DESIGNS.update({
    # Hujur: white turban (amama), long white beard, white panjabi, green accents
    "hujur": dict(skin=(226, 176, 132), hair=(238, 236, 230), face_w=150, face_h=172, nose=1.0, beard="full",
                  hat="amama", hat_main=(248, 246, 240), hat_accent=(92, 150, 110),
                  coat=(244, 242, 234), trim=(92, 150, 110), style="panjabi", build=1.12,
                  pants=(236, 234, 226), shoes=(84, 62, 46), curled=False, jewelry=False, scale=0.70),
    # Baba (father): white topi, short trimmed beard, blue-grey panjabi
    "baba": dict(skin=(214, 160, 116), hair=(34, 28, 26), face_w=154, face_h=166, nose=1.1, beard="short",
                 hat="topi", hat_main=(246, 242, 230), hat_accent=(214, 208, 190),
                 coat=(84, 118, 156), trim=(240, 238, 230), style="panjabi", build=1.14,
                 pants=(232, 230, 222), shoes=(70, 52, 40), curled=False, jewelry=False, scale=0.68),
    # Ma (mother): plum head scarf, teal modest dress, scarf draped over the chest
    "ma": dict(skin=(234, 188, 148), hair=(34, 28, 26), face_w=150, face_h=156, nose=0.8, beard="none",
               hat="hijab", hat_main=(132, 66, 118), hat_accent=(240, 220, 190),
               coat=(70, 150, 140), trim=(240, 226, 196), style="gown", build=1.16,
               pants=(70, 150, 140), shoes=(70, 52, 40), curled=False, jewelry=False, scale=0.62),
    # Child (boy): small, white topi, green panjabi
    "child": dict(skin=(238, 194, 154), hair=(30, 24, 22), face_w=150, face_h=148, nose=0.7, beard="none",
                  hat="topi", hat_main=(246, 242, 230), hat_accent=(214, 208, 190),
                  coat=(88, 168, 118), trim=(250, 248, 240), style="panjabi", build=0.9,
                  pants=(240, 238, 230), shoes=(70, 52, 40), curled=False, jewelry=False, scale=0.43),
    # Girl (child): small, rose head scarf, yellow dress
    "girl": dict(skin=(238, 194, 154), hair=(30, 24, 22), face_w=148, face_h=146, nose=0.7, beard="none",
                 hat="hijab", hat_main=(226, 120, 150), hat_accent=(250, 230, 200),
                 coat=(244, 200, 80), trim=(250, 248, 240), style="gown", build=0.9,
                 pants=(244, 200, 80), shoes=(70, 52, 40), curled=False, jewelry=False, scale=0.43),
    # Student: school shirt, dark trousers (give him a topi + panjabi with  hat=topi style=panjabi  for a madrasa look)
    "student": dict(skin=(212, 160, 120), hair=(30, 24, 22), face_w=146, face_h=160, nose=1.0, beard="none",
                    hat="none", hat_main=(30, 24, 22), hat_accent=(214, 208, 190),
                    coat=(78, 126, 196), trim=(250, 250, 246), style="shirt", build=1.0,
                    pants=(56, 62, 92), shoes=(40, 36, 36), curled=False, jewelry=False, scale=0.58),
})



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
    # hijab / head scarf: the cloth behind the face (ears are hidden), front pieces are drawn with the hat below
    if d["hat"] == "hijab":
        _t = HCY - fh / 2
        _hw = fw / 2 + 26
        _half = [(HCX, _t - 30), (HCX + fw * 0.36, _t - 20), (HCX + _hw, HCY - 50), (HCX + _hw + 4, HCY + 30),
                 (HCX + _hw + 10, 300), (HCX + _hw - 10, 324)]
        _pts = _half + [(2 * HCX - x, y) for x, y in reversed(_half[1:])]
        c.poly(smooth(_pts, True, 8), col(d["hat_main"]))
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
    if d["beard"] == "handlebar":                              # big upturned moustache (Gopal Bhar)
        r = [(HCX + 2, my - 8), (HCX + 26, my - 16), (HCX + 54, my - 8), (HCX + 80, my - 16), (HCX + 92, my - 40),
             (HCX + 84, my - 44), (HCX + 74, my - 20), (HCX + 56, my + 4), (HCX + 30, my + 10), (HCX + 2, my + 6)]
        pts = smooth(mirror_pts(r[::-1], HCX) + r, closed=True, n=6)
        c.poly(pts, hair, lw=2)
    if d["beard"] == "goatee":
        g = [(HCX - 20, HCY + fh / 2 - 22), (HCX + 20, HCY + fh / 2 - 22), (HCX + 16, HCY + fh / 2 + 2),
             (HCX, HCY + fh / 2 + 24), (HCX - 16, HCY + fh / 2 + 2)]
        c.poly(smooth(g, True, 6), hair, lw=2)
    if d["beard"] in ("full", "short"):                        # hujur: long full beard, no moustache. baba: short trimmed beard
        ext1, ext2 = (44, 54) if d["beard"] == "full" else (6, 10)
        outer_r = [(HCX + fw * 0.48, HCY - 6), (HCX + fw * 0.47, HCY + fh * 0.28), (HCX + fw * 0.33, HCY + fh * 0.50),
                   (HCX + fw * 0.14, HCY + fh / 2 + ext1), (HCX, HCY + fh / 2 + ext2)]
        outer = outer_r + [(2 * HCX - x, y) for x, y in reversed(outer_r)]
        _lo = 0 if d["beard"] == "full" else 14                                      # short beard = thinner band
        inner_l = [(HCX - fw * 0.40, HCY - 4 + _lo), (HCX - fw * 0.37, HCY + 26 + _lo), (HCX - fw * 0.22, my - 8 + _lo * 0.6),
                   (HCX - 30, my - 16 + _lo * 0.4), (HCX, my - 12 + _lo * 0.4)]
        inner = inner_l + [(2 * HCX - x, y) for x, y in reversed(inner_l[:-1])]
        c.poly(smooth(outer + inner, True, 6), hair, lw=2)
        _mw = 27 if d["beard"] == "full" else 22
        c.ell((HCX - _mw, my - 9, HCX + _mw, my + 13), skin, line=None)               # skin around the mouth
        if d["beard"] == "full":
            for k in (-2, -1, 0, 1, 2):                                             # beard strands
                c.line([(HCX + k * 16, HCY + fh / 2 + 4), (HCX + k * 13, HCY + fh / 2 + 36)], fill=shade(d["hair"], 0.78), lw=2)

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
    elif d["hat"] == "tiki":                                   # bald (takla) head, shiny, with a small tuft
        c.arc((HCX - fw * 0.30, top + 2, HCX + fw * 0.02, top + 40), 200, 290, fill=(255, 238, 215, 200), lw=6)
        c.poly(smooth([(HCX - 5, top + 6), (HCX - 12, top - 20), (HCX - 2, top - 44), (HCX + 14, top - 26),
                       (HCX + 9, top + 6)], True, 6), hair, lw=2.4)
        c.ell((HCX - 6, top - 10, HCX + 8, top + 8), shade(d["skin"], 0.92), line=None)
        c.line([(HCX - 6, top - 16), (HCX + 4, top - 40)], fill=(70, 55, 50, 255), lw=2)
    elif d["hat"] == "pagri":                                  # Raja Krishnachandra's royal turban
        by = top + 22
        c.poly(smooth([(HCX - fw / 2 - 14, by + 16), (HCX - fw / 2 - 12, by - 30), (HCX - 44, by - 82),
                       (HCX + 10, by - 100), (HCX + fw / 2 + 8, by - 62), (HCX + fw / 2 + 14, by + 16),
                       (HCX, by + 28)], True, 8), hm)
        for k, off in enumerate((-26, 0, 26)):
            c.arc((HCX - fw / 2 - 8, by - 88 + k * 4, HCX + fw / 2 + 16, by + 26 + k * 6), 200 + off, 340 + off,
                  fill=shade(d["hat_main"], 0.68), lw=3)
        c.rrect((HCX - fw / 2 - 14, by + 4, HCX + fw / 2 + 14, by + 28), 9, ha)            # gold band
        for px in (-46, -22, 22, 46):
            c.ell((HCX + px - 5, by + 11, HCX + px + 5, by + 21), (250, 248, 240, 255), lw=1.6)
        # jewel (sarpech) + plume (kalgi)
        c.poly(smooth([(HCX - 4, by - 6), (HCX - 22, by - 52), (HCX - 6, by - 108), (HCX + 18, by - 66),
                       (HCX + 10, by - 10)], True, 8), (250, 246, 236, 255), lw=2.4)
        c.line([(HCX, by - 10), (HCX - 2, by - 90)], fill=(200, 190, 175, 255), lw=2)
        c.poly(smooth([(HCX - 20, by + 2), (HCX, by - 16), (HCX + 20, by + 2), (HCX, by + 26)], True, 6), ha, lw=2.4)
        c.ell((HCX - 8, by + 1, HCX + 8, by + 17), (20, 140, 90, 255), lw=2)
        c.poly(smooth([(HCX + fw / 2 + 8, by - 16), (HCX + fw / 2 + 40, by + 12), (HCX + fw / 2 + 30, by + 56),
                       (HCX + fw / 2 + 14, by + 16)], True, 6), hm)
    elif d["hat"] == "pagri_tall":                             # Mantri's tall turban
        by = top + 20
        c.poly(smooth([(HCX - fw / 2 - 10, by + 14), (HCX - fw / 2 - 8, by - 50), (HCX - 30, by - 120),
                       (HCX + 18, by - 134), (HCX + fw / 2 + 2, by - 70), (HCX + fw / 2 + 10, by + 14),
                       (HCX, by + 26)], True, 8), hm)
        for k, off in enumerate((-34, -8, 18, 40)):
            c.arc((HCX - fw / 2 - 6, by - 126 + k * 14, HCX + fw / 2 + 12, by + 24 + k * 4), 200 + off, 340 + off,
                  fill=shade(d["hat_main"], 0.7), lw=3)
        c.rrect((HCX - fw / 2 - 10, by + 6, HCX + fw / 2 + 10, by + 26), 9, ha)
        c.ell((HCX - 9, by + 7, HCX + 9, by + 25), (200, 40, 60, 255), lw=2)
        c.poly(smooth([(HCX + fw / 2 + 4, by - 20), (HCX + fw / 2 + 34, by + 10), (HCX + fw / 2 + 26, by + 56),
                       (HCX + fw / 2 + 10, by + 14)], True, 6), hm)
    elif d["hat"] == "amama":                                  # hujur: white turban (amama) with a tail
        by = top + 22
        c.poly(smooth([(HCX - fw / 2 - 10, by + 14), (HCX - fw / 2 - 8, by - 28), (HCX - 38, by - 66),
                       (HCX + 14, by - 78), (HCX + fw / 2 + 2, by - 44), (HCX + fw / 2 + 10, by + 14),
                       (HCX, by + 24)], True, 8), hm)
        for k, off in enumerate((-30, -4, 22)):
            c.arc((HCX - fw / 2 - 6, by - 72 + k * 6, HCX + fw / 2 + 12, by + 22 + k * 6), 200 + off, 340 + off,
                  fill=shade(d["hat_main"], 0.80), lw=3)
        c.rrect((HCX - fw / 2 - 10, by + 4, HCX + fw / 2 + 10, by + 24), 9, shade(d["hat_main"], 0.94))
        c.poly(smooth([(HCX + fw / 2 + 4, by - 16), (HCX + fw / 2 + 30, by + 14), (HCX + fw / 2 + 24, by + 66),
                       (HCX + fw / 2 + 8, by + 16)], True, 6), hm)
    elif d["hat"] == "hijab":                                  # front of the scarf: forehead band + drape under the chin
        _pts = [(HCX - fw / 2 - 8, HCY + 6), (HCX - fw / 2 - 8, HCY - fh * 0.35), (HCX - fw * 0.3, top - 8),
                (HCX, top - 14), (HCX + fw * 0.3, top - 8), (HCX + fw / 2 + 8, HCY - fh * 0.35), (HCX + fw / 2 + 8, HCY + 6),
                (HCX + fw * 0.42, HCY - 6), (HCX + fw * 0.38, HCY - fh * 0.27), (HCX + fw * 0.17, HCY - fh * 0.34),
                (HCX, HCY - fh * 0.36), (HCX - fw * 0.17, HCY - fh * 0.34), (HCX - fw * 0.38, HCY - fh * 0.27),
                (HCX - fw * 0.42, HCY - 6)]
        c.poly(smooth(_pts, True, 6), hm)
        c.arc((HCX - fw * 0.40, top - 4, HCX + fw * 0.40, HCY - fh * 0.10), 205, 335, fill=shade(d["hat_main"], 0.78), lw=2.4)
        _dr = [(HCX - fw * 0.44, HCY + fh * 0.10), (HCX - fw * 0.37, HCY + fh * 0.33), (HCX - fw * 0.17, HCY + fh * 0.46),
               (HCX, HCY + fh * 0.49), (HCX + fw * 0.17, HCY + fh * 0.46), (HCX + fw * 0.37, HCY + fh * 0.33),
               (HCX + fw * 0.44, HCY + fh * 0.10), (HCX + fw / 2 + 28, 250), (HCX + fw / 2 + 12, 330),
               (HCX - fw / 2 - 12, 330), (HCX - fw / 2 - 28, 250)]
        c.poly(smooth(_dr, True, 6), hm)
        for k in (-1, 0, 1):
            c.line([(HCX + k * 26, HCY + fh * 0.62), (HCX + k * 34, 318)], fill=shade(d["hat_main"], 0.8), lw=2)
    elif d["hat"] == "none":                                   # bare head with hair
        c.poly(smooth([(HCX - fw / 2 + 2, top + 52), (HCX - fw / 2 + 8, top + 10), (HCX, top - 8),
                       (HCX + fw / 2 - 8, top + 10), (HCX + fw / 2 - 2, top + 52), (HCX + fw * 0.30, top + 30),
                       (HCX, top + 20), (HCX - fw * 0.30, top + 30)], True, 8), hair, lw=2.5)
    elif d["hat"] == "topi":                                   # simple white cap
        c.poly(smooth([(HCX - fw / 2 + 4, top + 40), (HCX - fw / 2 + 12, top - 2), (HCX, top - 14),
                       (HCX + fw / 2 - 12, top - 2), (HCX + fw / 2 - 4, top + 40), (HCX, top + 30)], True, 8),
               (246, 242, 230, 255), lw=2.8)
        for k in range(-2, 3):
            c.line([(HCX + k * 22, top + 26), (HCX + k * 18, top - 8)], fill=(214, 208, 190, 255), lw=2)
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
    elif d["hat"] == "bald":                                   # shiny bald head (hair only at the ears, drawn above)
        c.arc((HCX - fw * 0.34, top + 4, HCX + fw * 0.02, top + 46), 200, 285, fill=(255, 248, 232, 220), lw=7)
        c.arc((HCX - fw * 0.5, top - 2, HCX + fw * 0.5, top + 40), 210, 330, fill=shade(d["skin"], 0.9), lw=2)
    elif d["hat"] == "bun":                                    # Ginni: centre-parted hair, big bun, flowers
        hl = HCX - fw / 2
        c.poly(smooth([(hl - 2, top + 70), (hl + 2, top + 18), (HCX - fw * 0.25, top - 8), (HCX, top - 12),
                       (HCX + fw * 0.25, top - 8), (HCX + fw / 2 - 2, top + 18), (HCX + fw / 2 + 2, top + 70),
                       (HCX + fw * 0.40, top + 36), (HCX + fw * 0.16, top + 24), (HCX, top + 30),
                       (HCX - fw * 0.16, top + 24), (HCX - fw * 0.40, top + 36)], True, 8), hair, lw=2.5)
        c.arc((HCX - fw * 0.42, top - 2, HCX - fw * 0.02, top + 42), 200, 300, fill=(120, 110, 125, 200), lw=3)   # shine
        c.ell((HCX - 32, top - 46, HCX + 32, top + 10), hair, lw=2.5)                                              # bun
        c.arc((HCX - 26, top - 44, HCX + 26, top + 2), 190, 330, fill=(120, 110, 125, 200), lw=2.4)
        for fx_ in ((-34, -17, 0, 17, 34) if d.get("flowers", True) else ()):                                                                           # jasmine garland
            c.ell((HCX + fx_ - 7, top - 10 + abs(fx_) * 0.12, HCX + fx_ + 7, top + 4 + abs(fx_) * 0.12), (252, 250, 240, 255), lw=1.8)
        if d.get("sindoor"):                                                                                        # red line in the parting
            c.line([(HCX, top - 10), (HCX, top + 34)], fill=(210, 30, 40, 255), lw=4)
    if d.get("tilak"):                                          # sandal-paste mark on the forehead
        c.poly(smooth([(HCX, top + 12), (HCX + 8, top + 22), (HCX, top + 40), (HCX - 8, top + 22)], True, 6),
               (205, 52, 40, 255), lw=1.8)
        c.line([(HCX - 26, top + 20), (HCX + 26, top + 20)], fill=(250, 244, 230, 230), lw=3)
    if d.get("bindi"):                                          # big round red bindi
        c.ell((HCX - 8, HCY - fh * 0.27 - 8, HCX + 8, HCY - fh * 0.27 + 8), (205, 28, 40, 255), lw=1.5)
    if d.get("earrings"):                                       # gold jhumka earrings
        for sx in (-1, 1):
            ex = HCX + sx * (fw / 2 + 4)
            c.ell((ex - 6, HCY + 24, ex + 6, HCY + 36), (240, 196, 80, 255), lw=2)
            c.poly([(ex - 8, HCY + 34), (ex + 8, HCY + 34), (ex + 5, HCY + 52), (ex - 5, HCY + 52)], (240, 196, 80, 255), lw=2)
    if d.get("nath"):                                           # nose ring
        c.arc((HCX + 5, HCY + 24, HCX + 21, HCY + 40), 270, 150, fill=(240, 196, 80, 255), lw=3)
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


def draw_torso_dhoti(d):
    """Bare chest, pot belly, dhoti waist and a shoulder cloth (uttariya) - Gopal Bhar's costume."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    skin, cloth, edge = col(d["skin"]), col(d["coat"]), col(d["trim"])
    cx = 110
    sw, ww, hw = 60 * b, 56 * b, 66 * b
    top = 36
    body = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
            (cx + sw, top + 4), (cx + ww + 6, 110), (cx + ww + 14, 170), (cx + hw, 246), (cx - hw, 246),
            (cx - ww - 14, 170), (cx - ww - 6, 110)]
    c.poly(smooth(body, True, 4), skin)
    # chest line + navel
    c.arc((cx - 40, top + 22, cx - 2, top + 54), 20, 160, fill=shade(d["skin"], 0.7), lw=2)
    c.arc((cx + 2, top + 22, cx + 40, top + 54), 20, 160, fill=shade(d["skin"], 0.7), lw=2)
    c.ell((cx - 4, 168, cx + 4, 176), shade(d["skin"], 0.6), line=None)
    # sacred thread across the chest
    c.line([(cx - sw + 14, top + 2), (cx + 10, 118), (cx + ww, 190)], fill=(250, 246, 236, 255), lw=3)
    # shoulder cloth: over the left shoulder and hanging down the front
    c.poly(smooth([(cx - sw - 4, top + 2), (cx - 18, top - 12), (cx + 8, top + 16), (cx - 6, 120),
                   (cx - 20, 206), (cx - 56, 196), (cx - sw + 6, 90)], True, 6), cloth, lw=2.8)
    c.line([(cx - 14, top + 14), (cx - 22, 196)], fill=edge, lw=5)
    c.line([(cx - 52, 192), (cx - 24, 202)], fill=edge, lw=5)
    for k in range(3):
        c.line([(cx - sw + 8 + k * 6, top + 18 + k * 18), (cx - 26 + k * 5, top + 40 + k * 22)],
               fill=shade(d["coat"], 0.75), lw=2)
    # dhoti knot and waist band
    c.poly([(cx - hw - 2, 196), (cx + hw + 2, 196), (cx + hw + 4, 246), (cx - hw - 4, 246)], col(d["pants"]), lw=2.8)
    c.poly([(cx - hw - 2, 196), (cx + hw + 2, 196), (cx + hw + 2, 210), (cx - hw - 2, 210)], edge, lw=2.4)
    c.poly(smooth([(cx - 16, 208), (cx, 228), (cx + 16, 208), (cx + 8, 238), (cx - 8, 238)], True, 4),
           col(d["pants"]), lw=2.2)
    for k in range(-3, 4):
        c.line([(cx + k * 18, 214), (cx + k * 20, 244)], fill=(214, 206, 188, 255), lw=1.8)
    return c.done()


def draw_torso_saree(d):
    """Ginni's costume: short-sleeved blouse, bare midriff, saree pleats at the waist and the pallu over the left shoulder."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    skin, saree, edge, blouse = col(d["skin"]), col(d["coat"]), col(d["trim"]), col(d.get("blouse", d["trim"]))
    cx = 110
    sw, ww, hw = 56 * b, 52 * b, 68 * b
    top = 36
    # body base (skin shows at the neck and midriff)
    base = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
            (cx + sw, top + 4), (cx + ww + 4, 120), (cx + ww + 8, 180), (cx + hw, 246), (cx - hw, 246),
            (cx - ww - 8, 180), (cx - ww - 4, 120)]
    c.poly(smooth(base, True, 4), skin)
    # blouse
    c.poly(smooth([(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
                   (cx + sw, top + 4), (cx + ww + 4, 100), (cx - ww - 4, 100)], True, 4), blouse)
    c.poly(smooth([(cx - 26, top - 10), (cx, top + 22), (cx + 26, top - 10)], False, 8) + [(cx + 26, top - 14), (cx - 26, top - 14)],
           skin, lw=2.5)                                                       # round neckline
    c.line([(cx - ww - 4, 100), (cx + ww + 4, 100)], fill=shade(d.get("blouse", d["trim"]), 0.7), lw=3)
    # saree wrapped round the waist, falling in pleats to the hem; red border at the waist and the hem
    c.poly(smooth([(cx - ww - 8, 134), (cx + ww + 8, 134), (cx + ww + 14, 186), (cx + hw, 246), (cx - hw, 246),
                   (cx - ww - 14, 186)], True, 4), saree)
    c.poly([(cx - ww - 8, 134), (cx + ww + 8, 134), (cx + ww + 10, 150), (cx - ww - 10, 150)], edge, lw=2.4)
    c.ell((cx - 4, 118, cx + 4, 126), shade(d["skin"], 0.6), line=None)           # navel
    for k in range(-3, 4):                                                      # pleats (kuchi)
        c.line([(cx + k * 9, 160), (cx + k * 11, 244)], fill=(214, 206, 192, 255), lw=1.8)
    # pallu: from the left shoulder across the chest and down the front, red border along its edge
    c.poly(smooth([(cx - sw - 6, top + 2), (cx - 18, top - 12), (cx + 6, top + 14), (cx + 30, 100), (cx + 40, 176),
                   (cx + 6, 214), (cx - 34, 190), (cx - sw + 4, 100)], True, 6), saree, lw=2.8)
    c.line([(cx + 6, top + 16), (cx + 30, 100), (cx + 40, 174)], fill=edge, lw=7)
    c.line([(cx + 40, 176), (cx + 6, 212), (cx - 34, 190)], fill=edge, lw=7)
    for k in range(3):
        c.line([(cx - sw + 8 + k * 7, top + 18 + k * 16), (cx - 8 + k * 8, top + 40 + k * 22)],
               fill=(222, 214, 200, 255), lw=1.8)
    if d.get("jewelry"):                                                        # gold necklace
        c.arc((cx - 28, top - 18, cx + 28, top + 34), 20, 160, fill=(240, 196, 80, 255), lw=4)
    return c.done()


def draw_torso_gopal(d):
    """Round belly in a yellow kurta, orange dhoti below, red gamchha (scarf) round the neck - Gopal Bhar's TV look."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    yellow, red, dhoti = col(d["coat"]), col(d["trim"]), col(d["pants"])
    cx, top = 110, 36
    sw, bw, hm, hw = 58 * b, 86 * b, 80 * b, 64 * b
    c.poly([(cx - hw, 188), (cx + hw, 188), (cx + hw + 4, 246), (cx - hw - 4, 246)], dhoti)         # dhoti
    for k in range(-3, 4):
        c.line([(cx + k * 9, 214), (cx + k * 7, 244)], fill=shade(d["pants"], 0.72), lw=2)
    body = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
            (cx + sw, top + 4), (cx + bw, 112), (cx + bw + 3, 156), (cx + hm, 204), (cx + hm - 8, 220),
            (cx - hm + 8, 220), (cx - hm, 204), (cx - bw - 3, 156), (cx - bw, 112)]
    c.poly(smooth(body, True, 4), yellow)                                                              # kurta
    c.line([(cx, top + 24), (cx, 218)], fill=shade(d["coat"], 0.7), lw=2.6)                           # placket
    for k in range(4):
        c.ell((cx - 3.5, 92 + k * 28, cx + 3.5, 99 + k * 28), shade(d["coat"], 0.62), line=None)
    c.arc((cx - 50 * b, 78, cx - 4, 112), 20, 160, fill=shade(d["coat"], 0.72), lw=2)                # chest creases
    c.arc((cx + 4, 78, cx + 50 * b, 112), 20, 160, fill=shade(d["coat"], 0.72), lw=2)
    c.arc((cx - hm + 6, 150, cx + hm - 6, 212), 30, 150, fill=shade(d["coat"], 0.78), lw=2)         # belly curve
    c.poly(smooth([(cx - 26, top - 10), (cx, top + 20), (cx + 26, top - 10)], False, 8) + [(cx + 26, top - 14), (cx - 26, top - 14)],
           col(d["skin"]), lw=2.5)                                                                     # collar opening
    # gamchha: round the neck, both ends hanging down the front
    c.poly(smooth([(cx - 34, top - 6), (cx - 10, top + 20), (cx + 10, top + 20), (cx + 34, top - 6),
                   (cx + 40, top + 8), (cx, top + 34), (cx - 40, top + 8)], True, 4), red)
    for sx in (-1, 1):
        c.poly(smooth([(cx + sx * 42, top + 4), (cx + sx * 18, top + 24), (cx + sx * 16, 150), (cx + sx * 40, 156)], True, 4), red)
        c.line([(cx + sx * 26, top + 22), (cx + sx * 28, 152)], fill=shade(d["trim"], 0.72), lw=2.2)
        c.line([(cx + sx * 16, 148), (cx + sx * 40, 154)], fill=(252, 236, 200, 255), lw=3)
    return c.done()


def _neck_open(c, d, cx, top):
    c.poly(smooth([(cx - 26, top - 10), (cx, top + 26), (cx + 26, top - 10)], False, 8) + [(cx + 26, top - 14), (cx - 26, top - 14)],
           col(d["skin"]), lw=2.5)


def draw_torso_panjabi(d):
    """Long panjabi (kurta) with a collar band, a button placket and soft folds. No sash."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    coat, trim = col(d["coat"]), col(d["trim"])
    cx, top = 110, 36
    sw, ww, hw = 62 * b, 56 * b, 72 * b
    pts = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
           (cx + sw, top + 4), (cx + ww, 140), (cx + hw, 246), (cx - hw, 246), (cx - ww, 140)]
    c.poly(smooth(pts, True, 3), coat)
    for k in (-1, 1):                                                           # soft folds
        c.line([(cx + k * 30 * b, 100), (cx + k * 40 * b, 238)], fill=shade(d["coat"], 0.9), lw=2)
    c.line([(cx, top + 14), (cx, 190)], fill=shade(d["coat"], 0.66), lw=3)      # placket
    for k in range(4):
        c.ell((cx + 5, 66 + k * 24, cx + 12, 73 + k * 24), trim, lw=1.6)
    c.poly([(cx - 8, top + 12), (cx + 8, top + 12), (cx + 8, 190), (cx - 8, 190)], shade(d["coat"], 0.94), line=None)
    c.line([(cx - 8, top + 12), (cx - 8, 190)], fill=shade(d["coat"], 0.7), lw=2)
    c.line([(cx + 8, top + 12), (cx + 8, 190)], fill=shade(d["coat"], 0.7), lw=2)
    _neck_open(c, d, cx, top)
    c.poly([(cx - 26, top - 10), (cx - 18, top + 10), (cx - 6, top + 20), (cx - 6, top + 4)], trim, lw=2)      # collar band
    c.poly([(cx + 26, top - 10), (cx + 18, top + 10), (cx + 6, top + 20), (cx + 6, top + 4)], trim, lw=2)
    c.poly([(cx - hw, 238), (cx + hw, 238), (cx + hw, 246), (cx - hw, 246)], shade(d["coat"], 0.88), lw=2)  # hem
    return c.done()


def draw_torso_gown(d):
    """Modest long dress (like an abaya / kameez) with a scarf draped over the chest."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    coat, trim = col(d["coat"]), col(d["trim"])
    cx, top = 110, 36
    sw, ww, hw = 58 * b, 54 * b, 76 * b
    pts = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
           (cx + sw, top + 4), (cx + ww, 130), (cx + hw, 246), (cx - hw, 246), (cx - ww, 130)]
    c.poly(smooth(pts, True, 3), coat)
    for k in (-2, -1, 1, 2):
        c.line([(cx + k * 18 * b, 150), (cx + k * 27 * b, 242)], fill=shade(d["coat"], 0.86), lw=2)
    c.poly([(cx - hw, 232), (cx + hw, 232), (cx + hw, 246), (cx - hw, 246)], trim, lw=2.4)            # hem band
    c.poly([(cx - ww - 2, 128), (cx + ww + 2, 128), (cx + ww + 4, 140), (cx - ww - 4, 140)], trim, lw=2)  # belt line
    _neck_open(c, d, cx, top)
    sc = col(d["hat_main"])                                                                           # scarf drape
    c.poly(smooth([(cx - 38, top - 6), (cx - 6, top + 24), (cx + 30, top - 6), (cx + 42, top + 60), (cx + 24, 150),
                   (cx - 6, 118), (cx - 40, 140), (cx - 46, top + 50)], True, 6), sc, lw=2.6)
    for k in range(3):
        c.line([(cx - 28 + k * 10, top + 16 + k * 10), (cx - 20 + k * 14, 112 + k * 4)], fill=shade(d["hat_main"], 0.8), lw=2)
    return c.done()


def draw_torso_shirt(d):
    """School / casual shirt with a collar, a pocket and a belt."""
    c = Cv(TORSO_W, TORSO_H)
    b = d["build"]
    coat, trim = col(d["coat"]), col(d["trim"])
    cx, top = 110, 36
    sw, ww, hw = 60 * b, 52 * b, 56 * b
    pts = [(cx - sw, top + 4), (cx - sw + 6, top - 4), (cx - 22, top - 10), (cx + 22, top - 10), (cx + sw - 6, top - 4),
           (cx + sw, top + 4), (cx + ww, 140), (cx + hw, 232), (cx - hw, 232), (cx - ww, 140)]
    c.poly(smooth(pts, True, 3), coat)
    c.rrect((cx - hw - 2, 226, cx + hw + 2, 246), 4, col(d["pants"]), lw=2.5)                         # belt / waistband
    c.rrect((cx - 7, 228, cx + 7, 244), 3, (236, 190, 60, 255), lw=1.8)
    c.line([(cx, top + 16), (cx, 226)], fill=shade(d["coat"], 0.68), lw=2.6)
    for k in range(5):
        c.ell((cx - 3, 66 + k * 30, cx + 3, 72 + k * 30), trim, lw=1.4)
    c.rrect((cx + 18 * b, 84, cx + 44 * b, 112), 3, shade(d["coat"], 0.92), lw=2)                     # pocket
    _neck_open(c, d, cx, top)
    c.poly([(cx - 28, top - 12), (cx - 2, top + 26), (cx - 30, top + 22), (cx - 36, top - 4)], trim, lw=2)  # collar
    c.poly([(cx + 28, top - 12), (cx + 2, top + 26), (cx + 30, top + 22), (cx + 36, top - 4)], trim, lw=2)
    return c.done()


def draw_torso(d):
    if d["style"] == "panjabi":
        return draw_torso_panjabi(d)
    if d["style"] == "gown":
        return draw_torso_gown(d)
    if d["style"] == "shirt":
        return draw_torso_shirt(d)
    if d["style"] == "kurta_dhoti":
        return draw_torso_gopal(d)
    if d["style"] == "saree":
        return draw_torso_saree(d)
    if d["style"] == "dhoti":
        return draw_torso_dhoti(d)
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
    if d["style"] == "kurta_dhoti":                             # yellow kurta sleeve
        c.rrect((4, 4, 40, 92), 15, col(d["coat"]))
        c.line([(5, 88), (39, 88)], fill=shade(d["coat"], 0.7), lw=2.4)
        return c.done()
    if d["style"] == "saree":                                   # skin arm, short blouse sleeve at the top
        c.rrect((8, 6, 36, 92), 13, col(d["skin"]))
        c.rrect((5, 4, 39, 34), 13, col(d.get("blouse", d["trim"])))
        c.line([(6, 32), (38, 32)], fill=shade(d.get("blouse", d["trim"]), 0.7), lw=2.4)
        return c.done()
    if d["style"] == "dhoti":                                   # bare arm with a small armlet
        c.rrect((8, 6, 36, 92), 13, col(d["skin"]))
        c.rrect((6, 14, 38, 28), 5, tr, lw=2.2)
        return c.done()
    c.rrect((6, 6, 38, 92), 14, sl)
    if d["style"] == "tunic":
        c.rrect((6, 6, 38, 36), 14, col(d["hat_main"]))
        c.line([(6, 36), (38, 36)], lw=2)
    return c.done()


def draw_forearm(d, hand="open", soot=False):
    c = Cv(FA_W, FA_H)
    sl, tr = sleeve_colors(d)
    skin = (38, 32, 32, 255) if soot else col(d["skin"])
    if d["style"] == "saree":                                    # bare forearm with red-and-white bangles (shakha-pola)
        c.rrect((9, 4, 35, 62), 12, col(d["skin"]))
        for yy in (46, 53):                                      # red bangles
            c.rrect((7, yy, 37, yy + 6), 3, (210, 36, 44, 255), lw=1.8)
    elif d["style"] == "kurta_dhoti":                              # bare forearm coming out of the sleeve
        c.rrect((9, 0, 35, 62), 12, col(d["skin"]))
    elif d["style"] == "dhoti":                                    # bare forearm, thin bangle instead of a cuff
        c.rrect((9, 4, 35, 62), 12, col(d["skin"]))
        c.rrect((7, 50, 37, 60), 4, tr, lw=2.2)
    else:
        c.rrect((8, 4, 36, 60), 12, sl)
        c.rrect((6, 46, 38, 62), 5, tr, lw=2.5)                  # cuff
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
    if d["style"] == "kurta_dhoti":                             # orange dhoti to the ankle, black shoes
        c.poly([(4, 4), (64, 4), (66, 112), (2, 112)], col(d["pants"]))
        for k in (16, 30, 44, 56):
            c.line([(k, 8), (k + (k - 34) * 0.12, 108)], fill=shade(d["pants"], 0.72), lw=2)
        c.rrect((22, 106, 46, 126), 6, col(d["skin"]))
        c.poly(smooth([(8, 126), (50, 120), (76, 134), (74, 150), (10, 150)], True, 5), col(d["shoes"]))
        c.line([(12, 146), (72, 146)], fill=(90, 84, 86, 255), lw=2)
        return c.done()
    if d["style"] == "saree":                                   # saree to the ankle with a red border, bare feet with alta
        sk = col(d["skin"])
        c.rrect((24, 108, 46, 132), 8, sk)
        c.poly([(8, 4), (60, 4), (62, 116), (6, 116)], col(d["coat"]))
        c.poly([(6, 104), (62, 104), (62, 118), (6, 118)], col(d["trim"]), lw=2.2)
        for k in (20, 34, 48):
            c.line([(k, 8), (k + (k - 34) * 0.1, 102)], fill=(214, 206, 192, 255), lw=1.8)
        c.poly(smooth([(14, 128), (46, 122), (66, 132), (72, 146), (64, 152), (16, 152)], True, 5), sk)
        return c.done()
    if d["style"] == "dhoti":                                   # dhoti to the shin, bare calf and bare foot
        sk = col(d["skin"])
        c.rrect((22, 90, 46, 128), 8, sk)
        c.poly([(12, 4), (56, 4), (58, 100), (10, 100)], pants)
        c.poly([(10, 92), (58, 92), (58, 102), (10, 102)], col(d["trim"]), lw=2.2)
        for k in (22, 34, 46):
            c.line([(k, 8), (k + (k - 34) * 0.12, 90)], fill=(214, 206, 188, 255), lw=1.8)
        c.poly(smooth([(14, 126), (46, 120), (68, 130), (74, 146), (66, 152), (16, 152)], True, 5), sk)
        for k in range(3):
            c.line([(60 + k * 4, 140 + k * 3), (70 + k * 2, 142 + k * 3)], fill=shade(d["skin"], 0.6), lw=1.4)
        return c.done()
    c.poly([(16, 4), (52, 4), (50, 120), (18, 120)], pants)
    if d["style"] == "tunic":
        c.poly([(16, 4), (52, 4), (51, 34), (17, 34)], col(d["hat_accent"]), lw=2.5)
        c.poly([(18, 64), (50, 64), (50, 94), (18, 94)], col(d["hat_accent"]), lw=2.5)
    if d["style"] not in ("panjabi", "gown", "shirt"):
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


# ------------------------------------------------------------------ RAJSHOBHA (royal durbar hall)
GOLD = (240, 196, 80, 255)
GOLD_D = (190, 142, 44, 255)
MAROON = (140, 26, 44, 255)
MAROON_D = (96, 14, 30, 255)


def _cusp_arch(cx, yb, r, h, lobes=7, bulge=9):
    """Outline of a multi-foil (cusped) arch, as used in Bengal / Mughal palaces. Returns a polygon."""
    pts = [(cx - r, yb)]
    n = lobes
    for j in range(n):
        for k in range(9):
            t = k / 8
            th = math.pi * (j + t) / n                      # 0..pi from left to right
            ex, ey = -r * math.cos(th), -h * math.sin(th)
            nrm = (ex / r, ey / h)
            ln = math.hypot(*nrm) or 1
            b = bulge * math.sin(math.pi * t)
            pts.append((cx + ex + b * nrm[0] / ln, yb + ey + b * nrm[1] / ln))
    pts.append((cx + r, yb))
    return pts


def _seated_courtier(c, x, y, s, turban, robe, skin, beard=True, fan=False):
    """A small seated sabhasad (court member). y = floor line."""
    # cushion
    c.rrect((x - 40 * s, y - 10 * s, x + 40 * s, y + 4 * s), 6 * s, (170, 40, 56, 255), lw=2)
    # crossed legs / lap
    c.poly(smooth([(x - 44 * s, y - 6 * s), (x - 30 * s, y - 30 * s), (x + 30 * s, y - 30 * s),
                   (x + 44 * s, y - 6 * s), (x, y + 2 * s)], True, 6), shade(robe, 0.9), lw=2)
    # torso
    c.poly(smooth([(x - 30 * s, y - 28 * s), (x - 24 * s, y - 78 * s), (x + 24 * s, y - 78 * s),
                   (x + 30 * s, y - 28 * s)], True, 6), robe, lw=2)
    c.line([(x, y - 76 * s), (x, y - 30 * s)], fill=shade(robe, 0.7), lw=2)
    # arms resting on knees
    for sx in (-1, 1):
        c.rrect((x + sx * 30 * s - 8 * s, y - 70 * s, x + sx * 30 * s + 8 * s, y - 32 * s), 6 * s, robe, lw=2)
        c.ell((x + sx * 33 * s - 8 * s, y - 36 * s, x + sx * 33 * s + 8 * s, y - 22 * s), skin, lw=1.6)
    # head
    c.rrect((x - 7 * s, y - 86 * s, x + 7 * s, y - 72 * s), 3 * s, shade(skin, 0.88), line=None)
    c.ell((x - 20 * s, y - 114 * s, x + 20 * s, y - 80 * s), skin, lw=2)
    if beard:
        c.poly(smooth([(x - 16 * s, y - 96 * s), (x + 16 * s, y - 96 * s), (x + 12 * s, y - 84 * s),
                       (x, y - 72 * s), (x - 12 * s, y - 84 * s)], True, 5), (60, 50, 48, 255), lw=1.6)
        c.ell((x - 7 * s, y - 98 * s, x + 7 * s, y - 92 * s), skin, line=None)
    for sx in (-1, 1):
        c.ell((x + sx * 8 * s - 3 * s, y - 104 * s, x + sx * 8 * s + 3 * s, y - 99 * s), (30, 24, 24, 255), line=None)
    # turban
    c.poly(smooth([(x - 24 * s, y - 104 * s), (x - 20 * s, y - 130 * s), (x, y - 142 * s), (x + 22 * s, y - 128 * s),
                   (x + 24 * s, y - 104 * s), (x, y - 110 * s)], True, 6), turban, lw=2)
    c.line([(x - 22 * s, y - 114 * s), (x + 22 * s, y - 126 * s)], fill=shade(turban, 0.72), lw=2)


def make_rajshobha(evening=False):
    """Royal court (rajshobha): cusped arches, carved pillars, canopied throne on a dais,
    seated courtiers on both sides, chandeliers, marigold garlands and a gold picture frame."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    # back wall
    img.alpha_composite(vgrad(W, 480, (240, 214, 164), (214, 168, 112)))
    # window light behind the arches (left bays only)
    sky_top, sky_bot = ((255, 170, 110), (120, 90, 150)) if evening else ((140, 196, 240), (232, 242, 250))
    bays = [130, 390, 650]
    for bx in bays:
        w, h = 190, 300
        win = vgrad(w, h, sky_top, sky_bot)
        wc = Cv(w, h)
        wc.ell((-70, 200, 120, 380), (60, 112, 72, 255) if not evening else (40, 60, 70, 255), line=None)
        wc.ell((50, 230, 260, 400), (84, 142, 84, 255) if not evening else (50, 70, 80, 255), line=None)
        for px, ph in ((40, 90), (150, 70)):                    # palms
            wc.line([(px, 300), (px + 6, 300 - ph)], fill=(90, 66, 44, 255), lw=5)
            for a in (-70, -35, 0, 35, 70):
                ex = px + 6 + 34 * math.sin(math.radians(a))
                ey = 300 - ph + 20 - 22 * math.cos(math.radians(a))
                wc.line([(px + 6, 300 - ph), (ex, ey)], fill=(50, 120, 60, 255), lw=4)
        win.alpha_composite(wc.done())
        mask = Image.new("L", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.polygon([(x * 1, y * 1) for x, y in _cusp_arch(w / 2, 150, 92, 120)] + [(w - 2, h), (2, h)], fill=255)
        md.rectangle((0, 150, w, h), fill=255)
        wcv = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        wcv.paste(win, (0, 0), mask)
        img.alpha_composite(wcv, (bx - w // 2, 128))
    c = Cv(W, H)
    # frieze + scalloped valance
    c.poly([(0, 0), (W, 0), (W, 60), (0, 60)], MAROON_D, line=None)
    for i in range(0, W + 40, 40):
        c.poly(smooth([(i, 60), (i + 20, 92), (i + 40, 60)], False, 6) + [(i + 40, 56), (i, 56)], MAROON, lw=2)
        c.ell((i + 16, 76, i + 24, 84), GOLD, lw=1.4)
    c.line([(0, 60), (W, 60)], fill=GOLD, lw=5)
    for i in range(0, W, 40):
        c.poly([(i + 20, 14), (i + 32, 30), (i + 20, 46), (i + 8, 30)], GOLD, lw=1.6)
    # cusped arch outlines over the three window bays
    for bx in bays:
        c.line(_cusp_arch(bx, 278, 100, 128), fill=GOLD, lw=7)
        c.line(_cusp_arch(bx, 278, 112, 138, lobes=9, bulge=7), fill=GOLD_D, lw=3)
    # carved pillars between bays
    for px in (0, 260, 520, 780):
        c.rrect((px - 30, 100, px + 30, 482), 6, (190, 120, 76, 255), lw=3)
        c.rrect((px - 40, 94, px + 40, 126), 6, GOLD, lw=3)
        c.rrect((px - 40, 456, px + 40, 488), 6, GOLD, lw=3)
        for yy in range(150, 440, 38):
            c.poly([(px - 22, yy + 14), (px, yy), (px + 22, yy + 14), (px, yy + 28)], (160, 96, 60, 255), lw=1.8)
    img.alpha_composite(c.done())

    # ---- right: throne alcove (maroon wall hangings, canopy, throne, dais)
    t = Cv(W, H)
    t.rrect((820, 100, 1262, 480), 14, MAROON, lw=4)
    t.rrect((836, 116, 1246, 480), 10, MAROON_D, line=None)
    for i in range(10):                                              # gold brocade pattern
        for j in range(5):
            x0, y0 = 860 + i * 40 + (20 if j % 2 else 0), 140 + j * 62
            if x0 > 1226:
                continue
            t.poly([(x0, y0 - 14), (x0 + 11, y0), (x0, y0 + 14), (x0 - 11, y0)], GOLD_D, line=None)
    img.alpha_composite(t.done())
    # dais (three steps) and carpet runner
    d = Cv(W, H)
    d.poly([(780, 470), (1280, 470), (1280, 500), (780, 500)], (236, 224, 196, 255), lw=3)
    d.poly([(800, 440), (1280, 440), (1280, 470), (800, 470)], (226, 210, 176, 255), lw=3)
    d.poly([(820, 418), (1280, 418), (1280, 440), (820, 440)], (240, 228, 200, 255), lw=3)
    for yy in (452, 428):
        d.line([(826, yy), (1280, yy)], fill=GOLD, lw=3)
    d.poly([(930, 418), (1110, 418), (1130, 500), (910, 500)], MAROON, lw=2.5)
    img.alpha_composite(d.done())
    # throne
    th = Cv(W, H)
    tx = 1020
    th.rrect((tx - 90, 250, tx + 90, 424), 46, GOLD, lw=4)                        # back
    th.rrect((tx - 72, 272, tx + 72, 410), 34, MAROON, lw=3)
    th.arc((tx - 60, 276, tx + 60, 396), 200, 340, fill=GOLD, lw=4)
    for k in range(-2, 3):                                                         # peacock-feather crest
        th.ell((tx + k * 30 - 11, 214 - abs(k) * 8, tx + k * 30 + 11, 262 - abs(k) * 8), (30, 130, 120, 255), lw=2.4)
        th.ell((tx + k * 30 - 5, 228 - abs(k) * 8, tx + k * 30 + 5, 244 - abs(k) * 8), (240, 196, 80, 255), line=None)
    th.rrect((tx - 106, 380, tx - 70, 428), 10, GOLD, lw=3.4)                      # arms
    th.rrect((tx + 70, 380, tx + 106, 428), 10, GOLD, lw=3.4)
    th.rrect((tx - 100, 404, tx + 100, 440), 10, (176, 40, 56, 255), lw=3.4)       # cushion
    th.rrect((tx - 108, 436, tx + 108, 462), 8, GOLD, lw=3.4)                      # base
    for sx in (-1, 1):
        th.ell((tx + sx * 84 - 10, 456, tx + sx * 84 + 10, 474), GOLD, lw=2.4)
    img.alpha_composite(th.done())
    # canopy (chandratap) with fringe
    cn = Cv(W, H)
    cn.poly([(850, 150), (1190, 150), (1170, 112), (870, 112)], MAROON, lw=3.4)
    cn.poly(smooth([(870, 112), (1020, 52), (1170, 112)], False, 10) + [(1170, 112)], GOLD, lw=3.4)
    cn.ell((1012, 40, 1028, 58), GOLD, lw=2.4)
    cn.rrect((850, 146, 1190, 164), 4, GOLD, lw=3)
    for i in range(18):
        x0 = 856 + i * 19
        cn.poly([(x0, 164), (x0 + 16, 164), (x0 + 8, 186)], MAROON, lw=2)
        cn.ell((x0 + 4, 184, x0 + 12, 194), GOLD, lw=1.4)
    img.alpha_composite(cn.done())

    # ---- floor: marble tiles in perspective
    fl = vgrad(W, 250, (220, 198, 158), (160, 128, 92))
    img.alpha_composite(fl, (0, 470))
    f = Cv(W, H)
    horizon = 330.0
    rows = [470 + 250 * (j / 7) ** 1.7 for j in range(8)]
    for j in range(7):
        ya, yb = rows[j], rows[j + 1]
        sa, sb = (ya - horizon) / 140.0, (yb - horizon) / 140.0
        for i in range(-14, 15):
            if (i + j) % 2:
                f.poly([(640 + i * 62 * sa, ya), (640 + (i + 1) * 62 * sa, ya),
                        (640 + (i + 1) * 62 * sb, yb), (640 + i * 62 * sb, yb)], (190, 158, 114, 255), line=None)
    # carpet
    f.poly([(420, 470), (860, 470), (1240, 720), (40, 720)], (150, 30, 44, 255), lw=3)
    f.poly([(446, 470), (834, 470), (1160, 720), (120, 720)], (176, 44, 56, 255), line=None)
    f.line([(446, 474), (120, 716)], fill=GOLD, lw=4)
    f.line([(834, 474), (1160, 716)], fill=GOLD, lw=4)
    for k in range(1, 6):                                                           # carpet border motifs
        t_ = k / 6
        yy = 470 + 250 * t_ ** 1.2
        xl, xr = 446 - 326 * t_ ** 1.2 * 1.0, 834 + 326 * t_ ** 1.2 * 1.0
        for xx in (xl + 20 + 14 * t_, xr - 20 - 14 * t_):
            f.poly([(xx, yy - 8 * (0.5 + t_)), (xx + 8 * (0.5 + t_), yy), (xx, yy + 8 * (0.5 + t_)),
                    (xx - 8 * (0.5 + t_), yy)], GOLD, lw=1.4)
    img.alpha_composite(f.done())

    # ---- courtiers (sabhasad): two rows on the left, a few at the right edge in front of the dais
    cc = Cv(W, H)
    robes = [(46, 110, 96), (196, 96, 48), (70, 86, 150), (170, 60, 80), (110, 130, 60), (214, 170, 60)]
    turbans = [(240, 236, 226), (200, 60, 52), (250, 214, 90), (90, 60, 130), (240, 236, 226), (60, 120, 100)]
    skins = [(206, 152, 110), (186, 130, 92), (220, 168, 124), (176, 124, 88)]
    for i, x in enumerate((60, 170, 280)):                           # back row (small)
        _seated_courtier(cc, x, 506, 0.78, turbans[i], robes[i], skins[i % 4], beard=i != 1)
    for i, x in enumerate((20, 118, 224, 330)):                      # front row
        _seated_courtier(cc, x, 548, 0.95, turbans[(i + 3) % 6], robes[(i + 2) % 6], skins[(i + 1) % 4], beard=i % 2 == 0)
    for i, x in enumerate((1236, 1160)):
        _seated_courtier(cc, x, 560, 0.95, turbans[i + 1], robes[i + 3], skins[i], beard=True)
    cim = cc.done()
    tint = Image.new("RGBA", (W, H), (70, 40, 40, 0))
    tint.putalpha(cim.getchannel("A").point(lambda v: int(v * 0.22)))
    img.alpha_composite(cim)
    img.alpha_composite(tint)

    # ---- curtains + chandeliers + marigold garlands
    cu = Cv(W, H)
    for side in (0, 1):
        xs = 0 if side == 0 else W
        sg = 1 if side == 0 else -1
        cu.poly([(xs, 0), (xs + sg * 96, 0), (xs + sg * 64, 240), (xs + sg * 48, 470), (xs, 480)], MAROON, lw=3)
        for i in range(1, 4):
            cu.line([(xs + sg * i * 22, 0), (xs + sg * (i * 14 + 8), 470)], fill=MAROON_D, lw=3)
    img.alpha_composite(cu.done())
    lm = Cv(W, H)
    lamp_x = (130, 390, 650)
    for x in lamp_x:
        lm.line([(x, 92), (x, 150)], fill=(90, 60, 40, 255), lw=3)
        lm.poly(smooth([(x - 40, 190), (x - 26, 158), (x + 26, 158), (x + 40, 190), (x + 20, 204), (x - 20, 204)], True, 6),
                GOLD, lw=2.8)
        for k in range(-2, 3):
            lm.rrect((x + k * 14 - 3, 140, x + k * 14 + 3, 164), 2, (250, 246, 236, 255), lw=1.4)
            lm.ell((x + k * 14 - 4, 134, x + k * 14 + 4, 144), (255, 224, 130, 255), line=None)
        lm.ell((x - 8, 200, x + 8, 222), GOLD, lw=2.2)
    # marigold garlands draped between pillars
    for x0, x1 in ((0, 260), (260, 520), (520, 780)):
        for k in range(17):
            t_ = k / 16
            gx = x0 + (x1 - x0) * t_
            gy = 112 + 26 * math.sin(math.pi * t_)
            lm.ell((gx - 7, gy - 7, gx + 7, gy + 7), (250, 150, 30, 255) if k % 2 else (255, 196, 40, 255), lw=1.4)
    img.alpha_composite(lm.done())
    if evening:
        img.alpha_composite(Image.new("RGBA", (W, H), (50, 30, 80, 105)))
    for x in lamp_x:
        g = glow(150 if evening else 90, (255, 214, 120), 190 if evening else 70)
        img.alpha_composite(g, (x - g.width // 2, 190 - g.height // 2))

    # ---- gold picture frame (the "rajshobha frame")
    fr = Cv(W, H)
    fr.line([(8, 8), (W - 8, 8), (W - 8, H - 8), (8, H - 8), (8, 8)], fill=GOLD, lw=8)
    fr.line([(18, 18), (W - 18, 18), (W - 18, H - 18), (18, H - 18), (18, 18)], fill=GOLD_D, lw=3)
    for (cx_, cy_, sx, sy) in ((8, 8, 1, 1), (W - 8, 8, -1, 1), (8, H - 8, 1, -1), (W - 8, H - 8, -1, -1)):
        fr.ell((cx_ + sx * 4 - 22, cy_ + sy * 4 - 22, cx_ + sx * 4 + 22, cy_ + sy * 4 + 22), MAROON, lw=4)
        fr.ell((cx_ + sx * 4 - 10, cy_ + sy * 4 - 10, cx_ + sx * 4 + 10, cy_ + sy * 4 + 10), GOLD, lw=2.4)
    img.alpha_composite(fr.done())
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


def make_market():
    """Village bazaar with striped stalls."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.alpha_composite(vgrad(W, 480, (160, 212, 244), (255, 240, 208)))
    c = Cv(W, H)
    c.ell((1030, 50, 1130, 150), (255, 236, 150, 255), line=None)
    c.poly(smooth([(-40, 430), (220, 350), (480, 410), (760, 340), (1040, 410), (1320, 360), (1320, 480), (-40, 480)], True, 8),
           (126, 178, 124, 255), line=None)
    for hx, hy, s, wc, rc in [(120, 380, 1.1, (236, 206, 160), (180, 100, 70)), (300, 392, 0.9, (240, 220, 180), (150, 90, 60)),
                              (980, 384, 1.0, (232, 196, 150), (170, 96, 66)), (1150, 396, 0.85, (240, 214, 170), (140, 84, 58))]:
        c.poly([(hx - 50 * s, hy), (hx + 50 * s, hy), (hx + 50 * s, hy + 70 * s), (hx - 50 * s, hy + 70 * s)], wc, lw=2.5)
        c.poly([(hx - 62 * s, hy), (hx, hy - 46 * s), (hx + 62 * s, hy)], rc, lw=2.5)
        c.rrect((hx - 10 * s, hy + 30 * s, hx + 12 * s, hy + 70 * s), 3, (120, 80, 50, 255), lw=2)
    img.alpha_composite(c.done())
    g = vgrad(W, 250, (212, 176, 128), (160, 120, 82))
    img.alpha_composite(g, (0, 470))
    f = Cv(W, H)
    rng = np.random.default_rng(7)
    for _ in range(140):
        x, y = int(rng.integers(0, W)), int(rng.integers(485, 716))
        f.ell((x - 9, y - 4, x + 9, y + 4), (190, 152, 108, 255), lw=1.4)
    img.alpha_composite(f.done())
    # stalls
    s = Cv(W, H)
    stalls = [(40, 330, (214, 60, 52), "sweets"), (470, 300, (46, 150, 120), "fruit"), (900, 330, (236, 160, 40), "cloth")]
    for x0, w, colr, kind in stalls:
        top, base = 230, 470
        for px in (x0 + 8, x0 + w - 20):
            s.rrect((px, top + 30, px + 12, base), 3, (120, 80, 50, 255), lw=2.5)
        s.poly([(x0 + 10, base - 120), (x0 + w - 10, base - 120), (x0 + w - 10, base), (x0 + 10, base)], (150, 100, 66, 255), lw=3)
        s.poly([(x0, top + 40), (x0 + w, top + 40), (x0 + w + 20, top - 10), (x0 - 20, top - 10)], colr, lw=3)
        n = 8
        for i in range(n):
            if i % 2 == 0:
                xa, xb = x0 - 20 + i * (w + 40) / n, x0 - 20 + (i + 1) * (w + 40) / n
                s.poly([(xa, top - 10), (xb, top - 10), (xb - 4 * 0 + (x0 - (x0 - 20)) * 0, top + 40), (xa, top + 40)], (250, 246, 236, 255), line=None)
        for i in range(n + 1):
            xx = x0 + i * w / n
            s.poly([(xx - 22, top + 40), (xx + 22, top + 40), (xx, top + 62)], colr if i % 2 == 0 else (250, 246, 236, 255), lw=2)
        for i in range(6):
            xx = x0 + 34 + i * (w - 68) / 5
            if kind == "sweets":
                s.ell((xx - 22, base - 148, xx + 22, base - 114), (244, 170, 40, 255), lw=2.5)
                s.ell((xx - 12, base - 142, xx + 6, base - 128), (255, 214, 110, 255), line=None)
            elif kind == "fruit":
                s.ell((xx - 22, base - 148, xx + 22, base - 114), [(210, 50, 50, 255), (140, 190, 60, 255)][i % 2], lw=2.5)
            else:
                s.rrect((xx - 24, base - 156, xx + 24, base - 114), 6, [(60, 100, 180, 255), (200, 80, 120, 255), (240, 200, 60, 255)][i % 3], lw=2.5)
    img.alpha_composite(s.done())
    # bunting
    b = Cv(W, H)
    b.line([(0, 70), (320, 110), (640, 80), (960, 112), (1280, 74)], fill=(90, 60, 40, 255), lw=3)
    cols = [(214, 60, 52, 255), (244, 196, 48, 255), (46, 150, 120, 255), (60, 100, 180, 255)]
    for i in range(30):
        x = 20 + i * 42
        y = 70 + 40 * (0.5 - abs(((x % 640) / 640) - 0.5)) * 1.0 + (0 if x < 640 else 0)
        yy = 78 + 30 * math.sin(math.pi * (x % 320) / 320) * 0.6 + (x / 1280) * 12
        b.poly([(x - 12, yy), (x + 12, yy), (x, yy + 26)], cols[i % 4], lw=2)
    img.alpha_composite(b.done())
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
    make_rajshobha(False).save(out / "bg_rajshobha.png")
    make_rajshobha(True).save(out / "bg_rajshobha_evening.png")
    make_garden(True).save(out / "bg_garden.png")
    make_garden(False).save(out / "bg_garden_empty.png")
    make_market().save(out / "bg_market.png")
    make_title_bg().save(out / "bg_title.png")
    draw_pot().save(out / "prop_pot.png")
    draw_golden_mango(60).save(out / "prop_mango.png")
    from .art_islamic import build_islamic_assets
    build_islamic_assets(out)
