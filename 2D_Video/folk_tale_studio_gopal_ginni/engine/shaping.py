"""
Bangla text shaping using HarfBuzz + FontTools + Pillow.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

# FontTools is required independently of HarfBuzz
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

# HarfBuzz is optional
try:
    import uharfbuzz as hb
    AVAILABLE = True
    IMPORT_ERROR = None

except ImportError as exc:
    AVAILABLE = False
    IMPORT_ERROR = exc

SS = 4


class _FlatPen(BasePen):
    """Collects glyph outlines as lists of points (curves are flattened)."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours, self._cur = [], []

    def _moveTo(self, p):
        self._cur = [p]

    def _lineTo(self, p):
        self._cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, 9):
            t = i / 8
            mt = 1 - t
            self._cur.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                              mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, 7):
            t = i / 6
            mt = 1 - t
            self._cur.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                              mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []

    _endPath = _closePath


class HBText:
    """A Bengali font that shapes with HarfBuzz. Same idea as ImageFont, but correct for Bangla."""

    def __init__(self, path, size):
        self.path, self.size = str(path), size
        self.face = hb.Face(hb.Blob.from_file_path(self.path))
        self.font = hb.Font(self.face)
        self.upem = self.face.upem
        self.scale = size / self.upem
        self.tt = TTFont(self.path)
        self.glyph_set = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        ext = self.font.get_font_extents("ltr")
        self.ascent = ext.ascender * self.scale
        self.descent = -ext.descender * self.scale
        self._outline = {}
        self._mask = {}

    def _shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions

    def length(self, text):
        _, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * self.scale

    def _glyph(self, gid):
        if gid not in self._outline:
            pen = _FlatPen(self.glyph_set)
            self.glyph_set[self.order[gid]].draw(pen)
            self._outline[gid] = pen.contours
        return self._outline[gid]

    def mask(self, text):
        """Returns (L-mode mask, baseline_row). Row `baseline_row` of the mask is the text baseline."""
        if text in self._mask:
            return self._mask[text]
        infos, pos = self._shape(text)
        width = int(sum(p.x_advance for p in pos) * self.scale) + 8
        height = int(self.ascent + self.descent) + 8
        base = int(self.ascent) + 4
        acc = Image.new("L", (width * SS, height * SS), 0)
        pen_x = 0.0
        k = self.scale * SS
        for info, p in zip(infos, pos):
            ox = (pen_x + p.x_offset) * self.scale * SS + 4 * SS
            oy = (base * SS) - p.y_offset * k
            contours = [[(ox + x * k, oy - y * k) for x, y in c] for c in self._glyph(info.codepoint)]
            if contours:
                xs = [x for c in contours for x, _ in c]
                ys = [y for c in contours for _, y in c]
                x0, y0 = int(min(xs)) - 1, int(min(ys)) - 1
                w, h = int(max(xs)) - x0 + 2, int(max(ys)) - y0 + 2
                glyph = Image.new("1", (w, h), 0)
                for c in contours:                      # XOR = holes (e.g. inside ঠ, ও) stay empty
                    tmp = Image.new("1", (w, h), 0)
                    ImageDraw.Draw(tmp).polygon([(x - x0, y - y0) for x, y in c], fill=1)
                    glyph = ImageChops.logical_xor(glyph, tmp)
                acc.paste(255, (x0, y0), glyph)
            pen_x += p.x_advance
        out = acc.resize((width, height), Image.LANCZOS)
        self._mask[text] = (out, base)
        return self._mask[text]
