"""Readable text without any font file: a single-stroke vector font drawn with anti-aliased round strokes.

Latin letters live here; Devanagari words are shaped by devanagari.py and a set of common Chinese characters comes from hanzi.py.

Supports A-Z (lowercase is drawn as capitals), 0-9 and  . , ! ? - & % + : ' / ( ) $ and the rupee sign.
Glyph space: x 0..width, y 0..6 (cap height 6, y up, baseline 0).
"""
import math
import unicodedata

from . import devanagari, hanzi
from .raster import clamp, sdf_capsule


def _arc(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def _flip(strokes, w):
    return [[(w - x, 6 - y) for x, y in s] for s in strokes]


_SIX = [[(3.4, 5.6), (2.2, 6.0), (0.9, 5.2), (0.15, 3.5), (0.15, 1.6), (1.0, 0.15), (2.7, 0.15), (3.8, 1.2), (3.7, 2.6),
         (2.7, 3.5), (1.2, 3.4), (0.25, 2.6)]]
_S = [(3.7, 4.9), (3.0, 5.9), (1.0, 5.9), (0.25, 4.8), (0.45, 3.8), (2.0, 3.1), (3.6, 2.3), (3.8, 1.2), (3.0, 0.1), (1.0, 0.1), (0.2, 1.0)]
_P = [(0, 0), (0, 6), (2.8, 6), (3.8, 5.1), (3.8, 4.0), (2.8, 3.1), (0, 3.1)]

GLYPHS = {
    "A": (4, [[(0, 0), (2, 6), (4, 0)], [(0.8, 2.2), (3.2, 2.2)]]),
    "B": (4, [[(0, 0), (0, 6), (2.8, 6), (3.6, 5.2), (3.6, 4.4), (2.8, 3.4), (0, 3.4)],
              [(2.8, 3.4), (3.8, 2.6), (3.8, 1.0), (2.8, 0), (0, 0)]]),
    "C": (4, [_arc(2, 3, 2, 3, 42, 318)]),
    "D": (4, [[(0, 0), (0, 6), (2, 6), (3.6, 4.6), (3.6, 1.4), (2, 0), (0, 0)]]),
    "E": (3.8, [[(3.6, 6), (0, 6), (0, 0), (3.6, 0)], [(0, 3), (3, 3)]]),
    "F": (3.6, [[(3.6, 6), (0, 6), (0, 0)], [(0, 3), (3, 3)]]),
    "G": (4, [_arc(2, 3, 2, 3, 42, 360) + [(2.2, 3)]]),
    "H": (4, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
    "I": (1.2, [[(0.6, 0), (0.6, 6)]]),
    "J": (3.4, [[(3.2, 6), (3.2, 1.4), (2.2, 0), (1, 0), (0, 1.2)]]),
    "K": (4, [[(0, 0), (0, 6)], [(3.8, 6), (0, 2.6)], [(1.2, 3.6), (3.8, 0)]]),
    "L": (3.4, [[(0, 6), (0, 0), (3.4, 0)]]),
    "M": (4.6, [[(0, 0), (0, 6), (2.3, 2.4), (4.6, 6), (4.6, 0)]]),
    "N": (4, [[(0, 0), (0, 6), (4, 0), (4, 6)]]),
    "O": (4, [_arc(2, 3, 2, 3, 0, 360, 24)]),
    "P": (4, [_P]),
    "Q": (4, [_arc(2, 3, 2, 3, 0, 360, 24), [(2.4, 1.6), (4.0, -0.3)]]),
    "R": (4, [_P, [(1.8, 3.1), (3.8, 0)]]),
    "S": (4, [_S]),
    "T": (4, [[(0, 6), (4, 6)], [(2, 6), (2, 0)]]),
    "U": (4, [[(0, 6), (0, 1.8), (1, 0), (3, 0), (4, 1.8), (4, 6)]]),
    "V": (4, [[(0, 6), (2, 0), (4, 6)]]),
    "W": (5.4, [[(0, 6), (1.3, 0), (2.7, 4.2), (4.1, 0), (5.4, 6)]]),
    "X": (4, [[(0, 6), (4, 0)], [(4, 6), (0, 0)]]),
    "Y": (4, [[(0, 6), (2, 3), (4, 6)], [(2, 3), (2, 0)]]),
    "Z": (4, [[(0, 6), (4, 6), (0, 0), (4, 0)]]),
    "0": (3.6, [_arc(1.8, 3, 1.8, 3, 0, 360, 24)]),
    "1": (2.6, [[(0.4, 4.8), (1.8, 6), (1.8, 0)]]),
    "2": (4, [[(0.2, 4.6), (0.8, 5.6), (2, 6), (3.2, 5.6), (3.8, 4.6), (3.4, 3.4), (0.2, 0), (3.8, 0)]]),
    "3": (4, [[(0.3, 5.5), (1.2, 6), (2.8, 6), (3.6, 5.2), (3.5, 4.0), (2.2, 3.2)],
              [(2.2, 3.2), (3.7, 2.5), (3.9, 1.2), (2.9, 0.1), (1.1, 0.1), (0.2, 0.8)]]),
    "4": (4, [[(3, 0), (3, 6), (0, 1.8), (4, 1.8)]]),
    "5": (4, [[(3.6, 6), (0.4, 6), (0.2, 3.2), (1.8, 3.8), (3.2, 3.4), (3.9, 2.2), (3.7, 0.9), (2.8, 0.1), (1, 0.1), (0.1, 0.9)]]),
    "6": (4, _SIX),
    "7": (4, [[(0, 6), (4, 6), (1.6, 0)]]),
    "8": (4, [_arc(2, 4.5, 1.6, 1.5, 0, 360, 20), _arc(2, 1.5, 1.9, 1.5, 0, 360, 20)]),
    "9": (4, _flip(_SIX, 4)),
    ".": (1.0, [[(0.5, 0.0), (0.5, 0.02)]]),
    ",": (1.0, [[(0.6, 0.3), (0.2, -1.0)]]),
    "!": (1.0, [[(0.5, 6), (0.5, 2)], [(0.5, 0.0), (0.5, 0.02)]]),
    "?": (3.8, [[(0.2, 4.8), (0.6, 5.7), (2, 6), (3.2, 5.6), (3.6, 4.6), (3.2, 3.6), (2, 2.8), (2, 1.8)], [(2, 0.0), (2, 0.02)]]),
    "-": (3.0, [[(0.2, 3), (2.8, 3)]]),
    "&": (4.4, [[(4.0, 0), (0.6, 4.2), (0.5, 5.4), (1.5, 6), (2.5, 5.4), (2.4, 4.2), (0.2, 1.6), (0.8, 0.2), (2.2, 0), (3.2, 1), (4.0, 2.4)]]),
    "%": (4.2, [_arc(1.0, 5.0, 0.9, 1.0, 0, 360, 16), _arc(3.2, 1.0, 0.9, 1.0, 0, 360, 16), [(4.0, 6), (0.2, 0)]]),
    "+": (3.6, [[(1.8, 1.4), (1.8, 4.6)], [(0.3, 3), (3.3, 3)]]),
    ":": (1.0, [[(0.5, 4.2), (0.5, 4.22)], [(0.5, 1.2), (0.5, 1.22)]]),
    "'": (1.0, [[(0.5, 6), (0.5, 4.6)]]),
    "/": (3.2, [[(0, 0), (3.2, 6)]]),
    "(": (2.0, [_arc(2.2, 3, 1.8, 3.4, 110, 250, 10)]),
    ")": (2.0, [_arc(-0.2, 3, 1.8, 3.4, -70, 70, 10)]),
    "$": (4, [_S, [(2.0, -0.6), (2.0, 6.6)]]),
    "₹": (4, [[(0.3, 6), (3.9, 6)], [(0.3, 4.6), (3.9, 4.6)], [(0.9, 6), (2.4, 6), (3.3, 5.3), (3.3, 4.9), (2.4, 3.9), (0.9, 3.9)],
                    [(0.9, 3.9), (3.5, 0)]]),
    " ": (2.2, []),
}
GAP = 1.0


def supported(ch):
    return ch.upper() in GLYPHS or devanagari.supports(ch) or hanzi.supports(ch)


def clean(text, limit=40):
    """Keep what the fonts can draw, collapse spaces."""
    text = unicodedata.normalize("NFC", text)
    out = "".join(ch.upper() if ch.upper() in GLYPHS else ch for ch in text if supported(ch))
    return " ".join(out.split())[:limit]


def _layout(text):
    """Text -> (items, total width in glyph units). Each item is (x_offset, strokes, weight_factor), strokes in glyph units."""
    items, pen, first = [], 0.0, True
    for wi, word in enumerate(text.split(" ")):
        if wi:
            pen += GLYPHS[" "][0] + GAP
        i = 0
        while i < len(word):
            ch = word[i]
            if devanagari.supports(ch):
                j = i
                while j < len(word) and devanagari.supports(word[j]):
                    j += 1
                width, strokes = devanagari.layout_word(word[i:j])
                items.append((pen, strokes, getattr(devanagari, "WEIGHT", 1.0)))
                pen += width + GAP
                i = j
            elif hanzi.supports(ch):
                items.append((pen, hanzi.strokes(ch), getattr(hanzi, "WEIGHT", 1.0)))
                pen += hanzi.ADVANCE
                i += 1
            elif ch in GLYPHS:
                width, strokes = GLYPHS[ch]
                items.append((pen, strokes, 1.0))
                pen += width + GAP
                i += 1
            else:
                i += 1
    return items, max(0.0, pen - GAP)


def measure(text):
    """Width of the text in glyph units."""
    text = clean(text, 400)
    return _layout(text)[1] if text else 0.0


def draw_text(cv, text, x, y, height, color, weight=0.16, align="center", max_width=None, alpha=1.0, shadow=None):
    """Draw `text` with its vertical centre at y and horizontal anchor x. Returns the pixel bbox (x0, y0, x1, y1)."""
    text = clean(text)
    if not text:
        return None
    items, units = _layout(text)
    scale = height / 6.0
    if max_width is not None and units * scale > max_width:
        scale = max_width / units
        height = 6.0 * scale
    total = units * scale
    left = x - total / 2 if align == "center" else x if align == "left" else x - total
    base = y + height / 2.0
    r = max(0.8, weight * height / 2.0)
    box = [1e9, 1e9, -1e9, -1e9]
    for offset, strokes, wf in items:
        r_item = max(0.7, r * wf)                                   # CJK/Devanagari can ask for thinner strokes
        segs = []
        for st in strokes:
            pts = [(left + (offset + gx) * scale, base - gy * scale) for gx, gy in st]
            if len(pts) == 1:
                pts = [pts[0], (pts[0][0] + 0.01, pts[0][1])]
            segs += [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:])]
        if not segs:
            continue
        xs = [sg[0] for sg in segs] + [sg[2] for sg in segs]
        ys = [sg[1] for sg in segs] + [sg[3] for sg in segs]
        fns = [sdf_capsule(ax, ay, bx, by, r_item) for ax, ay, bx, by in segs]
        sdf = lambda px, py, fns=fns: min(f(px, py) for f in fns)            # noqa: E731
        bb = (min(xs) - r_item - 2, min(ys) - r_item - 2, max(xs) + r_item + 2, max(ys) + r_item + 2)
        if shadow:
            off = max(1.0, 0.07 * height)
            cv.shape((bb[0] + off, bb[1] + off, bb[2] + off, bb[3] + off),
                     lambda px, py, f=sdf, o=off: f(px - o, py - o), shadow[0], shadow[1] * alpha)
        cv.shape(bb, sdf, color, alpha)
        box = [min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3])]
    return tuple(box)


def luminance_under(cv, bbox, step=3):
    x0, y0, x1, y1 = [int(v) for v in bbox]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(cv.w, x1), min(cv.h, y1)
    vals = []
    for yy in range(y0, y1, step):
        for xx in range(x0, x1, step):
            i = (yy * cv.w + xx) * 3
            vals.append(0.299 * cv.px[i] + 0.587 * cv.px[i + 1] + 0.114 * cv.px[i + 2])
    if not vals:
        return 0.5, 0.0
    m = sum(vals) / len(vals)
    return m, (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5


def draw_headline(cv, text, x, y, height, max_width, weight=0.17):
    """Text with automatic contrast: dark on light areas, light on dark ones, plus a soft plate on busy areas."""
    text = clean(text)
    if not text:
        return None
    probe_w = min(max_width, measure(text) * height / 6.0)
    probe = (x - probe_w / 2 - height * 0.4, y - height * 0.8, x + probe_w / 2 + height * 0.4, y + height * 0.8)
    lum, spread = luminance_under(cv, probe)
    dark_text = lum > 0.52
    color = (0.07, 0.08, 0.12) if dark_text else (1.0, 1.0, 1.0)
    if spread > 0.13:
        plate = (1.0, 1.0, 1.0) if dark_text else (0.05, 0.06, 0.1)
        pw, ph = probe_w / 2 + height * 0.45, height * 0.85
        cv.box(x, y, pw, ph, plate, rad=ph * 0.45, alpha=0.62, soft=3.0)
    sh = ((0.0, 0.0, 0.0), 0.28) if not dark_text else ((1.0, 1.0, 1.0), 0.25)
    return draw_text(cv, text, x, y, height, color, weight, "center", max_width, 1.0, sh)
