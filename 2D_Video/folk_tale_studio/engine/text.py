"""
text.py - Bangla captions.
The Noto Sans Bengali font has no glyph for , . : ; - so those marks are drawn with a
Latin fallback font. Change LATIN_FONT_CANDIDATES if your computer has other fonts.
"""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

LATIN_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",       # Linux
    "/Library/Fonts/Arial Bold.ttf",                              # macOS
    "C:/Windows/Fonts/arialbd.ttf",                               # Windows
    "DejaVuSans-Bold.ttf", "arialbd.ttf",
]

_FONTS = {}
_CMAP = {}


def _latin_path():
    for p in LATIN_FONT_CANDIDATES:
        try:
            ImageFont.truetype(p, 12)
            return p
        except OSError:
            continue
    return None


def get_fonts(root, size):
    """(bengali_font, latin_font) at the given size."""
    key = (str(root), size)
    if key not in _FONTS:
        bn_path = Path(root) / "fonts" / "NotoSansBengali-Bold.ttf"
        bn = ImageFont.truetype(str(bn_path), size)
        lp = _latin_path()
        lat = ImageFont.truetype(lp, size) if lp else ImageFont.load_default()
        _FONTS[key] = (bn, lat, bn_path)
        try:
            from fontTools.ttLib import TTFont
            _CMAP[str(bn_path)] = set(TTFont(str(bn_path)).getBestCmap().keys())
        except Exception:
            _CMAP[str(bn_path)] = None
    bn, lat, bn_path = _FONTS[key]
    return bn, lat, _CMAP[str(bn_path)]


def _runs(text, cmap):
    runs = []
    for ch in text:
        bn = cmap is None or ch in " \u200c\u200d" or ord(ch) in cmap
        if runs and runs[-1][0] == bn:
            runs[-1][1] += ch
        else:
            runs.append([bn, ch])
    return runs


def text_len(draw, text, fonts):
    bn, lat, cmap = fonts
    return sum(draw.textlength(t, font=bn if is_bn else lat) for is_bn, t in _runs(text, cmap))


def draw_text(draw, cx, base_y, text, fonts, fill, anchor="center"):
    """Draw one line of text. Baseline at base_y; centred on cx (or left aligned at cx)."""
    bn, lat, cmap = fonts
    x = cx - text_len(draw, text, fonts) / 2 if anchor == "center" else cx
    for is_bn, t in _runs(text, cmap):
        f = bn if is_bn else lat
        draw.text((x, base_y), t, fill=fill, font=f, anchor="ls")
        x += draw.textlength(t, font=f)


def wrap(draw, text, fonts, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if text_len(draw, trial, fonts) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def split_caption(text, max_chars=58):
    """Sentence by sentence; long sentences are cut at commas / spaces."""
    text = text.replace("—", ", ").replace("–", ", ").replace("...", "…")
    sentences = [s.strip() for s in re.findall(r"[^।?!]+[।?!]?…?", text) if s.strip()]
    chunks = []
    for s in sentences:
        while len(s) > max_chars:
            cut = max(s.rfind(",", 0, max_chars), s.rfind(" ", 0, max_chars))
            if cut < 18:
                cut = max_chars
            chunks.append(s[:cut + 1].strip())
            s = s[cut + 1:].strip()
        if s:
            chunks.append(s)
    return chunks


def caption_image(root, text, label, width=1280, font_size=31):
    """Small RGBA image (caption box + speaker pill) and its top-left position on screen."""
    fonts = get_fonts(root, font_size)
    pill_fonts = get_fonts(root, 24)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = wrap(probe, text, fonts, 1060)
    lh = 44
    box_h = lh * len(lines) + 18
    box_w = max(text_len(probe, ln, fonts) for ln in lines) + 70
    box_w = int(min(1160, max(380, box_w)))
    img_h = box_h + 44
    im = Image.new("RGBA", (box_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 40, box_w - 1, img_h - 1), radius=20, fill=(12, 10, 24, 205))
    for i, ln in enumerate(lines):
        draw_text(d, box_w / 2, 40 + 9 + i * lh + 33, ln, fonts, (255, 255, 255, 255))
    if label:
        pw = int(text_len(d, label, pill_fonts) + 36)
        d.rounded_rectangle((16, 4, 16 + pw, 40), radius=16, fill=(236, 190, 60, 255))
        draw_text(d, 16 + pw / 2, 31, label, pill_fonts, (60, 20, 30, 255))
    x = (width - box_w) // 2
    y = 720 - img_h - 8
    return im, (x, y)
