"""Retail niches: kurti store, saree boutique, shoe store, jewellery, grocery, bookstore, florist, toy store."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, mix, scale

WOOD = (0.64, 0.43, 0.25)
GOLD = (0.88, 0.70, 0.30)
GOLD_L = (1.0, 0.90, 0.58)
GOLD_D = (0.58, 0.40, 0.12)


# ------------------------------------------------------------------------------------------------ shared helpers
def _pal(color, name, default):
    """Props receive the palette through `color` (S.put(..., color=S.pal)); fall back to a default colour."""
    return getattr(color, name, default) if color is not None and not isinstance(color, tuple) else default


def _chaikin(pts, n=2):
    """Round off the corners of a closed polygon (corner cutting)."""
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        pts = out
    return pts


def _fillpoly(c, px, color, alpha=1.0, shade=None):
    """Anti-aliased scanline polygon fill (cost grows with rows x edges, not pixels x edges: fast even for smoothed outlines)."""
    cv = c.cv
    W, H, buf = cv.w, cv.h, cv.px
    n = len(px)
    ys_all = [p[1] for p in px]
    y0, y1 = max(0, int(min(ys_all))), min(H - 1, int(max(ys_all)))
    SUB = 3
    edges = []
    for i in range(n):
        (xa, ya), (xb, yb) = px[i], px[(i + 1) % n]
        if ya != yb:
            edges.append((min(ya, yb), max(ya, yb), xa, ya, (xb - xa) / (yb - ya)))
    for y in range(y0, y1 + 1):
        spans = []
        for si in range(SUB):
            yy = y + (si + 0.5) / SUB
            xs = sorted(e[2] + (yy - e[3]) * e[4] for e in edges if e[0] <= yy < e[1])
            spans.append([(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)])
        lo = min((sp[0][0] for sp in spans if sp), default=None)
        if lo is None:
            continue
        hi = max(sp[-1][1] for sp in spans if sp)
        xa_i, xb_i = max(0, int(lo)), min(W - 1, int(hi))
        simple = all(len(sp) == 1 for sp in spans)
        if simple:
            full0 = int(max(sp[0][0] for sp in spans)) + 1
            full1 = int(min(sp[0][1] for sp in spans))
        else:
            full0, full1 = xb_i + 1, xb_i
        for x in range(xa_i, xb_i + 1):
            if full0 <= x < full1:
                cov = 1.0
            else:
                cov = 0.0
                for sp in spans:
                    for (sa, sb) in sp:
                        o = min(sb, x + 1.0) - max(sa, float(x))
                        if o > 0:
                            cov += o
                cov /= SUB
                if cov <= 0.0:
                    continue
                if cov > 1.0:
                    cov = 1.0
            a = cov * alpha
            col = shade(x, y) if shade else color
            i = (y * W + x) * 3
            if a >= 0.999:
                buf[i], buf[i + 1], buf[i + 2] = col
            else:
                ia = 1.0 - a
                buf[i] = buf[i] * ia + col[0] * a
                buf[i + 1] = buf[i + 1] * ia + col[1] * a
                buf[i + 2] = buf[i + 2] * ia + col[2] * a


def _spoly(c, pts, color, smooth=2, lift=0.10, alpha=1.0):
    """Smoothed (rounded-corner) polygon with a top-to-bottom shade; fast scanline fill."""
    if smooth:
        pts = _chaikin(pts, smooth)
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    ys = [p[1] for p in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    top, bot = scale(color, 1 + lift), scale(color, 1 - lift * 1.2)
    _fillpoly(c, px, color, alpha, (lambda x, y: mix(top, bot, clamp((y - y0) / sp))) if lift else None)


def _hpoly(c, pts, left, right, k=0.07, alpha=1.0, power=1.0, smooth=0):
    """Polygon shaded left-to-right (lit side `left`) and lightly top-to-bottom (scanline fill)."""
    if smooth:
        pts = _chaikin(pts, smooth)
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    x0, y0 = min(xs), min(ys)
    sx, sy = max(1.0, max(xs) - x0), max(1.0, max(ys) - y0)

    def shade(x, y):
        return scale(mix(left, right, clamp((x - x0) / sx) ** power), 1.0 + k * (1.0 - 2.0 * (y - y0) / sy))
    _fillpoly(c, px, left, alpha, shade)


def _leaf(c, u, v, length, angle, color, width=0.45, vein=True):
    """A pointed leaf drawn with the fast scanline fill (angle in degrees, 0 = pointing right)."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = [(t * length, math.sin(math.pi * t) ** 0.8 * wd) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    out = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    px = [(c.X(u + x * ca - y * sa), c.Y(v + x * sa + y * ca)) for x, y in out]
    ys = [p_[1] for p_ in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    top, bot = scale(color, 1.12), scale(color, 0.82)
    _fillpoly(c, px, color, 1.0, lambda x, y: mix(top, bot, clamp((y - y0) / sp)))
    if vein:
        c.line(u, v, u + length * 0.9 * ca, v + length * 0.9 * sa, length * 0.04, scale(color, 0.68), 0.6)


def _dark(S):
    return S.pal.mood == "dark"


def _mood_k(S, dark=0.55, other=1.0):
    return dark if S.pal.mood == "dark" else other


def _fold(c, u, v, w, h, col, d=0.10, border=None, stripe=None, k=1.0):
    """One folded cloth layer (front face + top face + a rounded fold edge), base centre (u, v)."""
    left, right = scale(col, 1.06 * k), scale(col, 0.78 * k)
    # top face (parallelogram, going back and slightly right)
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + d * 0.55, v + h + d * TILT), (u - w / 2 + d * 0.55, v + h + d * TILT)],
           scale(col, 1.14 * k), lift=0.05)
    craft.hshade_box(c, u, v + h / 2, w, h, left, right, r=h * 0.12)
    c.rect(u + w / 2 - w * 0.012, v + h / 2, w * 0.03, h * 0.92, scale(col, 0.62 * k), alpha=0.55, lift=0)       # folded edge, shaded
    c.rect(u - w / 2 + w * 0.012, v + h / 2 + h * 0.04, w * 0.02, h * 0.8, scale(col, 1.2 * k), alpha=0.5, lift=0)
    if stripe:
        c.rect(u, v + h * 0.5, w * 0.98, h * 0.26, stripe, lift=0.08, alpha=0.95)
        c.rect(u, v + h * 0.5, w * 0.98, h * 0.05, mix(stripe, WHITE, 0.4), lift=0, alpha=0.6)
    if border:
        c.rect(u, v + h * 0.12, w * 0.98, h * 0.14, border, lift=0.05, alpha=0.95)
    soft_disc(c, u + w * 0.08, v + h * 0.96, w * 0.52, h * 0.3, BLACK, 0.16, 1.4)                      # AO under the next layer


def _sparkle(S, u, v, r, color=(1.0, 0.95, 0.8), strength=0.9):
    """A four-point glint (additive) drawn on the stage."""
    S.glow(u, v, r * 1.2, color, 0.45 * strength, 2.0)
    S.line(u - r, v, u + r, v, r * 0.07, mix(color, WHITE, 0.6), 0.55 * strength)
    S.line(u, v - r, u, v + r, r * 0.07, mix(color, WHITE, 0.6), 0.55 * strength)
    S.glow(u, v, r * 0.28, WHITE, 0.9 * strength, 1.5)


def _floor_glow(S, u, v, a, b, color, alpha=0.2):
    S.soft(u, v, a, b, color, alpha, 1.5, add=True)


# ================================================================================================ KURTI STORE
KURTI_COLS = None


def _kurti(c, cu, top, length, w, col, trim, style, sleeve=0.55, depth_dark=1.0):
    """A hanging kurti seen from the front. (cu, top) = middle of the shoulder line, `length` down to the hem."""
    rng = c.rng
    sw, hw = w * 0.40, w * 0.54
    arm = top - length * 0.20
    base_l, base_r = scale(col, 1.05 * depth_dark), scale(col, 0.74 * depth_dark)
    # sleeves first (behind the body edge)
    for sgn in (-1, 1):
        sl = length * sleeve * 0.55
        c.poly([(cu + sgn * (sw - 0.01), top + 0.004), (cu + sgn * (sw + w * 0.30), top - sl * 0.28),
                (cu + sgn * (sw + w * 0.25), top - sl), (cu + sgn * (sw - 0.02), arm)], scale(col, (0.92 if sgn < 0 else 0.7) * depth_dark), lift=0.05)
        c.line(cu + sgn * (sw + w * 0.25), top - sl, cu + sgn * (sw - 0.02), top - sl * 1.02 + 0.0, 0.006, trim, 0.9)
    _hpoly(c, [(cu - sw, top), (cu + sw, top), (cu + sw * 1.02, arm), (cu + hw, top - length), (cu - hw, top - length), (cu - sw * 1.02, arm)],
           base_l, base_r, 0.06)

    def half(v):
        return (sw + (hw - sw) * clamp((top - v) / length)) * 0.88

    # patterns
    if style == 0:                                                       # block print: flower motifs on a half-drop grid
        row = 0
        v = top - length * 0.30
        while v > top - length * 0.93:
            n = 3
            for i in range(n):
                uu = cu + (i - (n - 1) / 2.0 + (0.5 if row % 2 else 0.0)) * w * 0.27
                if abs(uu - cu) > half(v):
                    continue
                for a in range(5):
                    t = a * 1.2566 + row
                    c.ellipse(uu + math.cos(t) * w * 0.035, v + math.sin(t) * w * 0.035, w * 0.028, w * 0.017, trim, angle=math.degrees(t), lift=0, alpha=0.88)
                c.ellipse(uu, v, w * 0.014, w * 0.014, scale(col, 0.62), lift=0, alpha=0.9)
            v -= length * 0.105
            row += 1
    elif style == 1:                                                     # embroidered yoke
        for rr, nn, rad in ((0.30, 22, 0.012), (0.37, 26, 0.010), (0.44, 30, 0.009)):
            for i in range(nn):
                a = math.pi * (1.08 + 0.84 * i / (nn - 1))
                uu, vv = cu + math.cos(a) * w * rr * 1.3, top - length * 0.02 + math.sin(a) * length * rr * 0.95
                if abs(uu - cu) > sw * 0.95:
                    continue
                c.ellipse(uu, vv, rad, rad, GOLD_L if i % 3 else mix(trim, WHITE, 0.35), lift=0.1, alpha=0.95)
        for i in range(7):
            c.ellipse(cu + (i - 3) * w * 0.07, top - length * (0.17 + 0.03 * abs(i - 3)), w * 0.022, w * 0.016, trim, lift=0, alpha=0.9)
    elif style == 2:                                                     # vertical ikat stripes
        for i in range(-5, 6):
            uu = cu + i * w * 0.095
            if abs(uu) > 0 and abs(uu - cu) > half(top - length * 0.5):
                continue
            c.rect(uu, top - length * 0.58, w * 0.03, length * 0.74, trim, lift=0, alpha=0.62 if i % 2 else 0.35)
    elif style == 3:                                                     # bandhani dots
        for _ in range(46):
            v = rng.uniform(top - length * 0.92, top - length * 0.25)
            uu = cu + rng.uniform(-1, 1) * half(v)
            c.ellipse(uu, v, w * 0.012, w * 0.012, mix(trim, WHITE, 0.3), lift=0, alpha=0.9)
    else:                                                                # plain with a printed border (lace)
        for i in range(-4, 5):
            c.ellipse(cu + i * w * 0.115, top - length * 0.80, w * 0.032, w * 0.05, trim, lift=0, alpha=0.7)
        c.rect(cu, top - length * 0.72, w * 1.0, 0.007, trim, lift=0, alpha=0.9)
    # hem band with motifs
    bh = length * 0.075
    _hpoly(c, [(cu - hw, top - length + bh), (cu + hw * 0.985, top - length + bh), (cu + hw, top - length), (cu - hw, top - length)],
           trim, scale(trim, 0.72), 0.04)
    for i in range(-5, 6):
        uu = cu + i * hw * 0.19
        if abs(uu - cu) < hw * 0.95:
            c.ellipse(uu, top - length + bh * 0.5, bh * 0.22, bh * 0.22, mix(trim, WHITE, 0.5), lift=0, alpha=0.8)
    # neckline: V cut showing the lining, gold piping, placket and buttons
    c.poly([(cu - w * 0.10, top + 0.002), (cu + w * 0.10, top + 0.002), (cu, top - length * 0.15)], scale(col, 0.34), lift=0)
    c.line(cu - w * 0.10, top, cu, top - length * 0.15, 0.007, GOLD, 0.95)
    c.line(cu + w * 0.10, top, cu, top - length * 0.15, 0.007, GOLD, 0.95)
    c.line(cu, top - length * 0.15, cu, top - length * 0.34, 0.006, trim, 0.9)
    for i in range(4):
        c.ellipse(cu, top - length * (0.19 + 0.045 * i), 0.006, 0.006, GOLD_L, lift=0.1)
    # drape folds, shading and a soft highlight on the lit side
    for i in range(4):
        x = cu + (i - 1.5) * w * 0.17
        c.line(x, top - length * 0.28, x + (i - 1.5) * 0.012, top - length * 0.96, 0.006, BLACK, 0.07)
    soft_disc(c, cu - w * 0.2, top - length * 0.42, w * 0.17, length * 0.32, WHITE, 0.14, 1.3, add=True)
    soft_disc(c, cu + w * 0.38, top - length * 0.55, w * 0.18, length * 0.45, BLACK, 0.20, 1.4)


@sprop("rf_clothing_rail", aspect=1.28, fill=1.0)
def rf_clothing_rail(c, color):
    rng = c.rng
    P = color
    acc = _pal(P, "accent", (0.69, 0.23, 0.44))
    acc2 = _pal(P, "accent2", (0.8, 0.4, 0.3))
    cols = [(acc, (0.97, 0.86, 0.55), 0), (mix((0.10, 0.45, 0.50), acc, 0.1), (0.96, 0.92, 0.82), 1), (mix((0.93, 0.78, 0.35), acc2, 0.2), (0.55, 0.12, 0.2), 2),
            ((0.96, 0.93, 0.88), mix(acc, BLACK, 0.2), 4), (mix((0.20, 0.30, 0.55), acc, 0.15), (0.95, 0.80, 0.40), 3)]
    for sgn in (-1, 1):                                                  # brass posts with feet
        x = sgn * 0.60
        ao(c, x, 0.0, 0.30, 0.07, 0.6)
        c.ellipse(x, 0.012, 0.11, 0.11 * TILT * 0.8, (0.45, 0.32, 0.15), lift=0)
        c.ellipse(x, 0.02, 0.10, 0.10 * TILT * 0.8, GOLD, lift=0.1)
        craft.hshade_box(c, x, 0.5, 0.022, 0.97, GOLD_L, GOLD_D)
    c.rect(0.0, 0.955, 1.28, 0.022, GOLD, lift=0.2)
    c.rect(0.0, 0.962, 1.26, 0.006, GOLD_L, lift=0, alpha=0.8)
    order = [0, 2, 4, 1, 3]
    for n, i in enumerate(order):
        cu = -0.50 + 0.25 * n
        col, trim, st = cols[i]
        top = 0.905 - (0.012 if n % 2 else 0.0)
        c.line(cu, 0.955, cu, 0.925, 0.005, GOLD_D, 0.9)
        c.poly([(cu, 0.925), (cu - 0.13, top - 0.01), (cu + 0.13, top - 0.01)], (0.55, 0.38, 0.22), alpha=0.9, lift=0)
        _kurti(c, cu, top, 0.60 - 0.02 * (n % 2), 0.32, col, trim, st, sleeve=0.45 + 0.2 * (n % 2))
        soft_disc(c, cu - 0.15, 0.62, 0.05, 0.30, BLACK, 0.28, 1.3)                           # shadow cast on the left neighbour
    soft_disc(c, -0.05, 0.98, 0.9, 0.06, WHITE, 0.2, 1.4, add=True)


@sprop("rf_dress_form", aspect=0.52, fill=1.0)
def rf_dress_form(c, color):
    P = color
    acc = _pal(P, "accent", (0.69, 0.23, 0.44))
    acc2 = _pal(P, "accent2", (0.8, 0.4, 0.3))
    ao(c, 0.0, 0.0, 0.5, 0.06)
    for a in (-30, 90, 210):                                             # tripod legs
        x = 0.20 * math.cos(math.radians(a))
        c.line(0.0, 0.07, x, 0.012 - 0.01 * math.sin(math.radians(a)), 0.02, (0.22, 0.17, 0.12), 1.0)
    c.ellipse(0.0, 0.06, 0.05, 0.03, (0.3, 0.22, 0.15), lift=0.1)
    craft.hshade_box(c, 0.0, 0.26, 0.032, 0.40, (0.58, 0.42, 0.26), (0.30, 0.20, 0.12))
    cream = (0.93, 0.88, 0.80)
    _hpoly(c, [(-0.17, 0.90), (0.17, 0.90), (0.20, 0.82), (0.15, 0.68), (0.10, 0.58), (0.16, 0.44), (-0.16, 0.44), (-0.10, 0.58), (-0.15, 0.68), (-0.20, 0.82)],
           cream, scale(cream, 0.70), 0.05)
    craft.hshade_box(c, 0.0, 0.935, 0.07, 0.07, (0.62, 0.45, 0.28), (0.40, 0.27, 0.16), r=0.02)
    c.ellipse(0.0, 0.975, 0.032, 0.02, (0.55, 0.38, 0.22), lift=0.1)
    # kurti on the form: yoke embroidery, flare to the knee
    _kurti(c, 0.0, 0.905, 0.52, 0.40, acc, GOLD_L, 1, sleeve=0.2)
    # dupatta over one shoulder with a gold border
    c.poly([(-0.20, 0.90), (-0.12, 0.915), (0.20, 0.72), (0.27, 0.47), (0.19, 0.44), (0.12, 0.70)], mix(acc2, WHITE, 0.25), alpha=0.9, lift=0.12)
    c.line(0.20, 0.72, 0.27, 0.47, 0.012, GOLD, 0.95)
    c.line(0.12, 0.70, 0.19, 0.44, 0.012, GOLD, 0.95)
    c.line(0.19, 0.44, 0.27, 0.47, 0.012, GOLD, 0.95)
    soft_disc(c, -0.06, 0.76, 0.07, 0.12, WHITE, 0.22, 1.2, add=True)


@sprop("rf_fold_stack", aspect=1.1, fill=0.95)
def rf_fold_stack(c, color):
    P = color
    acc = _pal(P, "accent", (0.69, 0.23, 0.44))
    acc2 = _pal(P, "accent2", (0.8, 0.4, 0.3))
    ao(c, 0.0, 0.0, 1.0, 0.15)
    for sgn in (-1, 1):                                                  # low wooden display table
        craft.hshade_box(c, sgn * 0.40, 0.09, 0.045, 0.18, WOOD, scale(WOOD, 0.6))
    c.poly([(-0.52, 0.19), (0.52, 0.19), (0.60, 0.215), (-0.44, 0.215)], scale(WOOD, 1.15), lift=0.05)
    craft.hshade_box(c, 0.0, 0.17, 1.04, 0.04, scale(WOOD, 0.95), scale(WOOD, 0.62), r=0.01)
    layers = [(mix(acc, BLACK, 0.15), (0.97, 0.86, 0.55)), ((0.14, 0.45, 0.48), (0.96, 0.92, 0.82)), (mix((0.93, 0.78, 0.35), acc2, 0.2), (0.55, 0.12, 0.2)),
              ((0.94, 0.91, 0.86), mix(acc, BLACK, 0.2)), (acc, GOLD_L)]
    v = 0.19
    rng = c.rng
    for i, (col, trim) in enumerate(layers):
        w = 0.84 - 0.02 * (i % 2) + rng.uniform(-0.02, 0.02)
        h = 0.12
        _fold(c, rng.uniform(-0.018, 0.018), v, w, h, col, d=0.14, border=trim if i % 2 == 0 else None, stripe=None)
        for _ in range(7):                                               # print dots on the front
            c.ellipse(rng.uniform(-w * 0.45, w * 0.45), v + rng.uniform(0.02, 0.10), 0.012, 0.01, mix(trim, col, 0.2), lift=0, alpha=0.7)
        v += h * 0.96
    soft_disc(c, -0.25, v + 0.10, 0.28, 0.05, WHITE, 0.22, 1.3, add=True)


@niche("kurti-store", "Kurti & ethnic wear store", subjects=("rf_clothing_rail",),
       strong=("kurti", "kurtis", "kurta", "ethnic wear", "ladies kurti", "women ethnic wear", "kurti shop", "kurti store", "कुर्ती", "कुर्ता",
               "kurti ki dukaan", "designer kurti", "indian wear", "salwar suit"),
       weak=("boutique", "dupatta", "embroidery", "block print", "ladies wear", "fashion", "ethnic"), accent="#b03a6f", mood="light", group="retail",
       avoid=("saree", "sari", "साड़ी"))
def kurti_store(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.5)
    pans = [mix((0.82, 0.30, 0.45), P.accent, 0.5), mix((0.15, 0.50, 0.52), P.accent, 0.15), (0.94, 0.86, 0.60), (0.95, 0.92, 0.86),
            mix((0.25, 0.30, 0.55), P.accent, 0.2), P.accent, mix(P.accent2, WHITE, 0.2)]
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for i in range(24):                                                                      # wall battens
            S.rect(-1.5 + i * 0.2, 0.2, 0.012, 0.8, scale(P.wall_bot, 0.88), lift=0.0, alpha=0.5)
        S.rect(1.0, 0.31, 6.0, 0.012, scale(GOLD, k), lift=0.0)                                  # wall rail with a row of hanging garments
        for i in range(34):
            u = -2.0 + i * 0.12 + S.rng.uniform(-0.01, 0.01)
            col = scale(pans[i % len(pans)], k)
            ln = S.rng.uniform(0.24, 0.30)
            S.poly([(u - 0.045, 0.32), (u + 0.045, 0.32), (u + 0.065, 0.32 + ln), (u - 0.065, 0.32 + ln)], col)
            S.rect(u, 0.32 + ln - 0.02, 0.13, 0.03, scale(mix(col, WHITE, 0.4), k), lift=0.0)
        S.rect(0.35, 0.14, 0.34, 0.24, scale(GOLD, 0.8 * k), lift=0.0)                          # framed print
        S.rect(0.35, 0.14, 0.30, 0.20, scale(mix(P.accent, WHITE, 0.45), k), lift=0.05)
        S.rect(1.78, 0.17, 0.30, 0.38, scale(GOLD, 0.8 * k), r=0.15, lift=0.0)                  # arched gilt mirror
        S.rect(1.78, 0.17, 0.26, 0.34, mix(P.wall_top, (0.8, 0.88, 0.95), 0.6) if not dk else (0.12, 0.13, 0.2), r=0.13, lift=0.05)
        S.glow(1.78, 0.17, 0.4, P.light, 0.16 if not dk else 0.10)
        S.pendant(0.62, -0.1, 0.16, (1.0, 0.85, 0.55))
        S.pendant(1.20, -0.1, 0.12, (1.0, 0.85, 0.55))
        S.pendant(1.62, -0.1, 0.17, (1.0, 0.85, 0.55))
        S.bokeh(8, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.9, 0.7), (1.0, 0.8, 0.6)], 0.01, 0.035, 0.22)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.60, 5.0, 2.5, mix(P.surface, WHITE, 0.30), plank=0.14, grain=0.3)
    S.rect(1.0, 0.60, 8.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    _floor_glow(S, 1.1, 0.80, 1.1, 0.16, (1.0, 0.88, 0.62), 0.30 if dk else 0.16)
    # rug under the display
    rug = mix(P.accent_dark, BLACK, 0.2 if dk else 0.0)
    S.poly([(0.38, 0.83), (1.86, 0.83), (1.98, 1.03), (0.26, 1.03)], rug, soft=1.0)
    S.poly([(0.46, 0.855), (1.78, 0.855), (1.88, 1.005), (0.36, 1.005)], mix(rug, GOLD, 0.35))
    S.poly([(0.50, 0.865), (1.74, 0.865), (1.83, 0.995), (0.41, 0.995)], mix(rug, P.accent, 0.4))
    S.put("rf_clothing_rail", 1.10, 0.90, 0.64, color=P, shadow=False)
    S.mark_subject("rf_clothing_rail", 0.96, 0.38, 1.24, 0.86)
    S.put("rf_dress_form", 1.60, 0.95, 0.54, color=P)
    S.put("rf_fold_stack", 0.70, 0.99, 0.30)
    S.focus("detail", 1.10, 0.60)
    with S.near(16.0):
        S.circle(1.74, 0.98, 0.07, mix(P.accent, WHITE, 0.25), alpha=0.35, lift=0, soft=6.0)
        S.circle(0.48, 0.97, 0.05, (1.0, 0.85, 0.6), alpha=0.3, lift=0, soft=6.0)


# ================================================================================================ SAREE BOUTIQUE
def _zari(c, u0, u1, v, h, motif=True, base=GOLD):
    """A woven gold (zari) border band centred at height v with a row of small diamond motifs."""
    w = u1 - u0
    um = (u0 + u1) / 2
    c.rect(um, v, w, h, base, lift=0.18)
    c.rect(um, v + h * 0.30, w, h * 0.14, GOLD_L, lift=0, alpha=0.75)
    c.rect(um, v - h * 0.42, w, h * 0.10, GOLD_D, lift=0, alpha=0.55)
    if motif:
        n = max(2, int(w / (h * 1.5)))
        for i in range(n):
            x = u0 + w * (i + 0.5) / n
            c.poly([(x - h * 0.34, v), (x, v + h * 0.3), (x + h * 0.34, v), (x, v - h * 0.3)], GOLD_D, alpha=0.65, lift=0)


@sprop("rf_saree_stack", aspect=1.25, fill=0.92)
def rf_saree_stack(c, color):
    P = color
    acc = _pal(P, "accent", (0.56, 0.27, 0.68))
    rng = c.rng
    ao(c, 0.0, 0.0, 1.05, 0.14)
    for sgn in (-1, 1):                                                  # carved wooden plinth
        craft.hshade_box(c, sgn * 0.42, 0.08, 0.06, 0.16, scale(WOOD, 0.9), scale(WOOD, 0.5))
    craft.hshade_box(c, 0.0, 0.16, 1.08, 0.045, scale(WOOD, 0.95), scale(WOOD, 0.55), r=0.012)
    c.poly([(-0.54, 0.182), (0.54, 0.182), (0.62, 0.21), (-0.46, 0.21)], scale(WOOD, 1.2), lift=0.05)
    silks = [mix(acc, (0.2, 0.0, 0.3), 0.2), (0.78, 0.10, 0.18), (0.10, 0.45, 0.42), (0.95, 0.62, 0.18), mix(acc, WHITE, 0.25), (0.12, 0.28, 0.50),
             (0.86, 0.30, 0.42)]
    v = 0.21
    for i, col in enumerate(silks):
        w = 0.86 + rng.uniform(-0.03, 0.03)
        h = 0.095
        u = rng.uniform(-0.02, 0.02)
        _fold(c, u, v, w, h, col, d=0.14)
        # woven zari border along the front, a pallu end panel on the left, sheen
        c.rect(u, v + h * 0.78, w * 0.985, h * 0.15, GOLD, lift=0.1, alpha=0.95)
        c.rect(u, v + h * 0.22, w * 0.985, h * 0.12, GOLD, lift=0.1, alpha=0.92)
        for k in range(int(w / 0.045)):
            x = u - w / 2 + 0.025 + k * 0.045
            c.ellipse(x, v + h * 0.78, 0.008, 0.008, GOLD_D, lift=0, alpha=0.6)
        for _ in range(10):
            c.ellipse(u + rng.uniform(-w * 0.45, w * 0.45), v + rng.uniform(h * 0.4, h * 0.65), 0.006, 0.005, GOLD_L, lift=0, alpha=0.6)
        soft_disc(c, u - w * 0.22, v + h * 0.5, w * 0.2, h * 0.3, WHITE, 0.18, 1.3, add=True)
        v += h * 0.95
    soft_disc(c, 0.1, v + 0.06, 0.42, 0.07, WHITE, 0.22, 1.3, add=True)


@sprop("rf_saree_form", aspect=0.54, fill=1.0)
def rf_saree_form(c, color):
    P = color
    acc = _pal(P, "accent", (0.56, 0.27, 0.68))
    silk = mix(acc, (0.6, 0.05, 0.25), 0.35)
    blouse = (0.95, 0.80, 0.42)
    skin = (0.92, 0.85, 0.74)
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.06)
    c.ellipse(0.0, 0.02, 0.22, 0.22 * TILT * 0.8, scale(WOOD, 0.45), lift=0)
    # torso (cream), neck and head
    _hpoly(c, [(-0.15, 0.85), (0.15, 0.85), (0.175, 0.80), (0.14, 0.70), (0.085, 0.60), (0.115, 0.52), (-0.115, 0.52), (-0.085, 0.60), (-0.14, 0.70), (-0.175, 0.80)],
           skin, scale(skin, 0.62), 0.05)
    craft.hshade_box(c, 0.0, 0.87, 0.04, 0.06, skin, scale(skin, 0.65))
    c.ellipse(0.0, 0.935, 0.05, 0.062, skin, lift=0.1)
    soft_disc(c, -0.016, 0.95, 0.022, 0.035, WHITE, 0.5, 1.2, add=True)
    # saree skirt with pleats, flowing to the floor
    _hpoly(c, [(-0.115, 0.60), (0.115, 0.60), (0.235, 0.05), (-0.235, 0.05)], mix(silk, WHITE, 0.10), scale(silk, 0.52), 0.05, power=1.2)
    c.ellipse(0.0, 0.05, 0.235, 0.235 * 0.17, scale(silk, 0.5), lift=0)
    c.ellipse(0.0, 0.055, 0.232, 0.232 * 0.15, mix(silk, WHITE, 0.04), lift=0.05)
    for i in range(1, 13):
        t = i / 13.0
        c.line(-0.115 + 0.23 * t, 0.595, -0.235 + 0.47 * t, 0.07, 0.004, BLACK if i % 2 else WHITE, 0.14 if i % 2 else 0.11)
    c.poly([(-0.04, 0.60), (0.06, 0.60), (0.09, 0.07), (-0.12, 0.07)], mix(silk, WHITE, 0.16), alpha=0.33, lift=0)
    for i in range(5):                                                   # tucked pleats at the waist
        c.poly([(-0.05 + i * 0.022, 0.60), (-0.03 + i * 0.022, 0.60), (-0.04 + i * 0.022, 0.50)], scale(silk, 0.75 + 0.07 * i), alpha=0.9, lift=0)
    # gold hem border with motifs
    c.poly([(-0.228, 0.105), (0.228, 0.105), (0.235, 0.06), (-0.235, 0.06)], GOLD, lift=0.15)
    c.poly([(-0.222, 0.14), (0.222, 0.14), (0.228, 0.11), (-0.228, 0.11)], mix(silk, GOLD, 0.5), lift=0.1)
    for i in range(13):
        c.poly([(-0.21 + i * 0.035, 0.083), (-0.20 + i * 0.035, 0.095), (-0.19 + i * 0.035, 0.083), (-0.20 + i * 0.035, 0.07)], GOLD_D, alpha=0.7, lift=0)
    # blouse: short, fitted, with gold trim
    _hpoly(c, [(-0.15, 0.85), (0.15, 0.85), (0.175, 0.80), (0.14, 0.70), (0.12, 0.64), (-0.12, 0.64), (-0.14, 0.70), (-0.175, 0.80)], blouse, scale(blouse, 0.6), 0.05)
    c.line(-0.12, 0.64, 0.12, 0.64, 0.008, GOLD_D, 0.7)
    c.ellipse(0.0, 0.85, 0.075, 0.025, skin, lift=0.0)
    # pallu: across the chest from the left shoulder, falling past the right hip
    c.poly([(-0.17, 0.835), (-0.09, 0.855), (0.16, 0.62), (0.245, 0.18), (0.155, 0.16), (0.09, 0.56)], silk, lift=0.08)
    c.poly([(-0.17, 0.835), (-0.09, 0.855), (0.16, 0.62), (0.13, 0.58)], scale(silk, 0.8), alpha=0.45, lift=0)
    for (a0, b0, a1, b1) in ((-0.16, 0.83, 0.09, 0.56), (-0.09, 0.855, 0.16, 0.62), (0.09, 0.56, 0.155, 0.16), (0.16, 0.62, 0.245, 0.18)):
        c.line(a0, b0, a1, b1, 0.010, GOLD, 0.95)
    c.poly([(0.154, 0.30), (0.243, 0.32), (0.245, 0.18), (0.155, 0.16)], GOLD, alpha=0.4, lift=0)
    for i in range(7):
        t = i / 6.0
        x = 0.16 + 0.082 * t
        c.poly([(x - 0.012, 0.165 - 0.07 * 0), (x + 0.012, 0.165), (x, 0.30)], GOLD, alpha=0.85, lift=0)
    for _ in range(26):
        t = rng.random()
        c.ellipse(0.13 + 0.11 * t + rng.uniform(-0.02, 0.02), rng.uniform(0.2, 0.58), 0.006, 0.006, GOLD_L, lift=0, alpha=0.8)
    soft_disc(c, -0.05, 0.45, 0.05, 0.2, WHITE, 0.22, 1.3, add=True)
    soft_disc(c, 0.19, 0.42, 0.07, 0.30, BLACK, 0.20, 1.4)


@sprop("rf_brass_lamp", aspect=0.30, fill=1.0)
def rf_brass_lamp(c, color):
    ao(c, 0.0, 0.0, 0.3, 0.06)
    c.ellipse(0.0, 0.03, 0.14, 0.14 * TILT, GOLD_D, lift=0.1)
    craft.hshade_box(c, 0.0, 0.28, 0.035, 0.5, GOLD_L, GOLD_D)
    for v in (0.1, 0.3, 0.52):
        c.ellipse(0.0, v, 0.055, 0.025, GOLD, lift=0.15)
    c.poly([(-0.14, 0.60), (0.14, 0.60), (0.09, 0.53), (-0.09, 0.53)], GOLD, lift=0.15)
    c.ellipse(0.0, 0.60, 0.14, 0.14 * TILT, GOLD_D, lift=0)
    c.ellipse(0.0, 0.605, 0.12, 0.12 * TILT * 0.8, (1.0, 0.75, 0.3), lift=0.1)
    c.ellipse(0.0, 0.66, 0.035, 0.07, (1.0, 0.9, 0.55), lift=0.1)
    soft_disc(c, 0.0, 0.67, 0.35, 0.30, (1.0, 0.7, 0.3), 0.55, 1.6, add=True)


@niche("saree-boutique", "Saree boutique", subjects=("rf_saree_form",),
       strong=("saree", "sarees", "sari", "saris", "banarasi", "silk saree", "saree shop", "saree showroom", "साड़ी", "साडी", "सारी",
               "kanjivaram", "saree ki dukaan", "zari", "paithani"),
       weak=("silk", "boutique", "bridal wear", "ethnic", "handloom", "pallu", "weaves"), accent="#8e44ad", mood="warm", group="retail",
       avoid=("kurti", "kurta"))
def saree_boutique(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.62)
    wall = mix(P.wall_bot, P.accent, 0.12 if not dk else 0.0)
    cols = [(0.78, 0.10, 0.18), mix(P.accent, (0.2, 0.0, 0.3), 0.2), (0.10, 0.45, 0.42), (0.95, 0.62, 0.18), mix(P.accent, WHITE, 0.3),
            (0.12, 0.28, 0.50), (0.86, 0.30, 0.42)]
    with S.far():
        S.wall(mix(P.wall_top, wall, 0.5), wall, 0.62)
        for au in (0.15, 0.80, 1.45, 2.10):                                                   # arched alcoves with hanging sarees
            S.rect(au, 0.30, 0.46, 0.60, scale(mix(wall, GOLD, 0.35), k), r=0.23, lift=0.0)
            S.rect(au, 0.31, 0.40, 0.56, scale(mix(wall, (1.0, 0.8, 0.5), 0.35), 0.95 if not dk else 0.35), r=0.20, lift=0.0)
            S.glow(au, 0.32, 0.45, (1.0, 0.82, 0.55), 0.35 if not dk else 0.30)
            for j in range(7):
                x = au - 0.15 + j * 0.05
                col = scale(cols[(j + int(au * 3)) % len(cols)], k)
                S.rect(x, 0.36, 0.042, 0.48, col, lift=0.05)
                S.rect(x, 0.15, 0.042, 0.02, scale(GOLD, k), lift=0.0)
        S.rect(1.0, 0.60, 8.0, 0.025, scale(GOLD, 0.8 * k), lift=0.0)
        S.pendant(0.45, -0.1, 0.12, (1.0, 0.8, 0.5))
        S.pendant(1.15, -0.1, 0.15, (1.0, 0.8, 0.5))
        S.pendant(1.80, -0.1, 0.11, (1.0, 0.8, 0.5))
        S.bokeh(10, 0.0, 0.05, 2.0, 0.58, [(1.0, 0.85, 0.55), (1.0, 0.7, 0.4)], 0.01, 0.04, 0.26)
        S.floor(0.62, mix(P.floor_top, P.accent_dark, 0.15), mix(P.floor_bot, P.accent_dark, 0.3))
    S.wood(-3.0, 0.62, 5.0, 2.5, mix(P.surface, P.accent_dark, 0.12 if not dk else 0.0), plank=0.16, grain=0.25)
    S.rect(1.0, 0.62, 8.0, 0.008, scale(P.surface, 0.4), lift=0.0)
    _floor_glow(S, 1.15, 0.82, 1.1, 0.17, (1.0, 0.82, 0.5), 0.34 if dk else 0.20)
    S.poly([(0.42, 0.84), (1.90, 0.84), (2.0, 1.02), (0.30, 1.02)], mix(P.accent_dark, BLACK, 0.25))
    S.poly([(0.49, 0.865), (1.83, 0.865), (1.92, 1.0), (0.39, 1.0)], mix(P.accent_dark, GOLD, 0.45))
    S.poly([(0.53, 0.875), (1.79, 0.875), (1.87, 0.99), (0.44, 0.99)], mix(P.accent_dark, P.accent, 0.45))
    S.put("rf_brass_lamp", 1.74, 0.91, 0.30, framed=False)
    S.put("rf_saree_form", 1.40, 0.945, 0.62, color=P)
    S.mark_subject("rf_saree_form", 1.31, 0.45, 1.49, 0.80)
    S.put("rf_saree_stack", 0.82, 0.975, 0.36, color=P)
    S.glow(1.40, 0.45, 0.35, (1.0, 0.85, 0.55), 0.08)
    S.focus("detail", 1.40, 0.60)
    with S.near(16.0):
        S.circle(0.55, 0.12, 0.07, (1.0, 0.85, 0.55), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ SHOE STORE
def _two(color, a, b):
    """Shoe props take (body, panel) colours through `color`."""
    if isinstance(color, tuple) and len(color) == 2 and isinstance(color[0], tuple):
        return color
    return a, b


def _lace_run(c, p0, p1, n, step, col, w=0.034, eyelet=(0.2, 0.2, 0.22)):
    """n laces along the throat line p0 -> p1, each a short diagonal band with an eyelet."""
    for i in range(n):
        t = i / float(max(1, n - 1))
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        c.line(x, y - 0.008, x + step[0], y + step[1] - 0.008, w, BLACK, 0.22)
        c.line(x, y, x + step[0], y + step[1], w, col, 1.0)
        c.line(x, y + w * 0.2, x + step[0] * 0.9, y + step[1] * 0.9 + w * 0.2, w * 0.3, WHITE, 0.35)
        c.ellipse(x, y, 0.016, 0.016, eyelet, lift=0.1)


@sprop("rf_sneaker", aspect=2.3, fill=1.0)
def rf_sneaker(c, color):
    body, panel = _two(color, (0.16, 0.50, 0.73), (0.97, 0.97, 0.97))
    rng = c.rng
    ao(c, 0.0, 0.0, 2.1, 0.20)
    # midsole + outsole
    _hpoly(c, [(-1.10, 0.09), (-0.95, 0.005), (0.85, 0.005), (1.02, 0.04), (1.05, 0.22), (-1.13, 0.22)], (0.98, 0.98, 0.98), (0.66, 0.67, 0.70), 0.04, smooth=1)
    c.poly([(-0.97, 0.02), (0.87, 0.02), (0.85, 0.0), (-0.94, 0.0)], (0.20, 0.20, 0.22), lift=0)
    c.line(-1.02, 0.115, 1.0, 0.125, 0.012, BLACK, 0.16)
    c.ellipse(0.62, 0.115, 0.17, 0.045, mix(body, WHITE, 0.55), alpha=0.8, lift=0.1)                # visible air unit
    # upper
    up = [(-1.12, 0.21), (-1.13, 0.34), (-1.02, 0.50), (-0.80, 0.58), (-0.55, 0.62), (-0.40, 0.72), (-0.25, 0.84), (-0.12, 0.98), (0.05, 1.0), (0.14, 0.88),
          (0.30, 0.80), (0.55, 0.82), (0.80, 0.90), (0.92, 0.86), (0.99, 0.62), (1.04, 0.21)]
    _hpoly(c, up, mix(body, WHITE, 0.12), scale(body, 0.62), 0.08, power=1.1, smooth=2)
    _spoly(c, [(-1.12, 0.21), (-1.13, 0.34), (-1.02, 0.50), (-0.80, 0.58), (-0.66, 0.56), (-0.62, 0.21)], mix(panel, body, 0.1), 1, alpha=0.95, lift=0.08)        # toe cap
    _spoly(c, [(0.70, 0.21), (1.04, 0.21), (0.99, 0.62), (0.92, 0.86), (0.80, 0.78), (0.70, 0.5)], panel, 1, alpha=0.96, lift=0.1)                          # heel counter
    _spoly(c, [(-0.55, 0.28), (-0.10, 0.33), (0.35, 0.50), (0.72, 0.72), (0.42, 0.56), (-0.05, 0.44), (-0.50, 0.37)], panel, 2, lift=0.1)                    # side stripe
    for i in range(5):                                                                                 # toe perforations
        for j in range(3):
            c.ellipse(-1.0 + i * 0.065 + (j % 2) * 0.03, 0.30 + j * 0.065 + i * 0.018, 0.011, 0.011, scale(body, 0.45), lift=0, alpha=0.7)
    for i in range(34):                                                                                # outsole tread notches
        c.rect(-0.95 + i * 0.058, 0.018, 0.02, 0.022, (0.3, 0.3, 0.33), lift=0, alpha=0.55)
    c.line(-0.62, 0.22, -0.64, 0.56, 0.008, scale(body, 0.5), 0.5)                                    # stitched seam
    c.line(0.70, 0.23, 0.70, 0.5, 0.008, scale(body, 0.5), 0.5)
    # collar lining, tongue, laces
    c.poly([(0.14, 0.89), (0.30, 0.80), (0.55, 0.82), (0.80, 0.90), (0.55, 0.86), (0.30, 0.85)], (0.17, 0.18, 0.2), lift=0)
    c.poly([(-0.30, 0.80), (-0.12, 1.0), (0.06, 1.01), (0.14, 0.89), (-0.12, 0.82)], mix(panel, WHITE, 0.2), lift=0.1)
    c.rect(-0.02, 0.93, 0.07, 0.07, body, r=0.015, lift=0.1)
    _lace_run(c, (-0.46, 0.70), (-0.11, 0.84), 5, (0.16, -0.22), mix(panel, WHITE, 0.4))
    c.poly([(-0.46, 0.70), (-0.38, 0.74), (-0.1, 0.83), (-0.12, 0.8), (-0.40, 0.70)], scale(body, 0.5), alpha=0.5, lift=0)
    soft_disc(c, -0.78, 0.50, 0.24, 0.07, WHITE, 0.32, 1.2, 10, add=True)
    soft_disc(c, -0.1, 0.18, 0.7, 0.07, WHITE, 0.25, 1.3, add=True)
    soft_disc(c, 0.86, 0.45, 0.14, 0.35, BLACK, 0.26, 1.4)


@sprop("rf_leather_shoe", aspect=2.6, fill=1.0)
def rf_leather_shoe(c, color):
    leather, _ = _two(color, (0.45, 0.22, 0.09), (0.0, 0.0, 0.0))
    ao(c, 0.0, 0.0, 2.3, 0.2)
    dark = scale(leather, 0.38)
    c.poly([(-1.28, 0.10), (-1.24, 0.0), (0.8, 0.0), (1.08, 0.0), (1.09, 0.17), (-1.28, 0.12)], dark, lift=0.05)                  # sole with a heel block
    c.rect(0.9, 0.09, 0.40, 0.17, scale(leather, 0.30), lift=0.05)
    up = [(-1.27, 0.12), (-1.29, 0.24), (-1.17, 0.37), (-0.92, 0.45), (-0.65, 0.50), (-0.47, 0.60), (-0.32, 0.74), (-0.16, 0.88), (0.0, 0.90), (0.12, 0.78),
          (0.45, 0.72), (0.82, 0.78), (1.0, 0.80), (1.07, 0.5), (1.08, 0.17)]
    _hpoly(c, up, mix(leather, WHITE, 0.10), scale(leather, 0.50), 0.10, power=1.1)
    c.line(-1.26, 0.135, 1.04, 0.19, 0.012, mix(leather, WHITE, 0.45), 0.5)                                                         # welt stitch
    for k in range(34):
        x = -1.22 + k * 0.07
        c.ellipse(x, 0.155 + 0.05 * (x + 1.2) / 2.3, 0.008, 0.005, GOLD_L, lift=0, alpha=0.65)
    craft.arc(c, -0.86, 0.14, 0.34, 0.34, 80, 200, 0.010, scale(leather, 0.45), 0.9, 8)                                         # toe cap seam
    for k in range(9):                                                                                                  # brogue perforations
        a = math.radians(95 + k * 11)
        c.ellipse(-0.86 + math.cos(a) * 0.34, 0.14 + math.sin(a) * 0.34 * 0.82, 0.011, 0.01, scale(leather, 0.3), lift=0)
    c.poly([(0.12, 0.78), (0.45, 0.72), (0.82, 0.78), (0.45, 0.76)], (0.12, 0.08, 0.05), lift=0)
    c.poly([(-0.34, 0.72), (-0.16, 0.9), (0.02, 0.92), (0.14, 0.78), (-0.15, 0.74)], mix(leather, BLACK, 0.18), lift=0.1)
    _lace_run(c, (-0.52, 0.60), (-0.12, 0.76), 5, (0.15, -0.20), (0.18, 0.10, 0.05), 0.035, (0.75, 0.6, 0.35))
    craft.arc(c, 0.90, 0.5, 0.15, 0.25, -80, 80, 0.012, scale(leather, 0.45), 0.9, 6)
    soft_disc(c, -0.88, 0.36, 0.20, 0.05, WHITE, 0.55, 1.2, 8, add=True)                       # patent-like shine
    soft_disc(c, -0.1, 0.62, 0.30, 0.05, WHITE, 0.30, 1.2, 28, add=True)
    soft_disc(c, 0.6, 0.62, 0.18, 0.04, WHITE, 0.25, 1.2, 0, add=True)
    soft_disc(c, 0.95, 0.4, 0.14, 0.35, BLACK, 0.3, 1.3)


@sprop("rf_shoe_box", aspect=1.45, fill=1.0)
def rf_shoe_box(c, color):
    P = color
    acc = _pal(P, "accent", (0.16, 0.50, 0.73))
    ao(c, 0.0, 0.0, 1.35, 0.22)
    d = 0.18
    for (v0, h, col, off) in ((0.0, 0.46, acc, 0.0), (0.46, 0.34, (0.96, 0.96, 0.96), 0.03)):
        w = 1.2
        c.poly([(-w / 2 + off, v0 + h), (w / 2 + off, v0 + h), (w / 2 + off + d * 0.5, v0 + h + d * 0.55), (-w / 2 + off + d * 0.5, v0 + h + d * 0.55)],
               scale(col, 1.12), lift=0.05)
        craft.hshade_box(c, off, v0 + h / 2, w, h, scale(col, 1.05), scale(col, 0.72), r=0.01)
        c.rect(off + w / 2 + 0.002, v0 + h / 2 + d * 0.2, 0.02, h * 0.98, scale(col, 0.55), alpha=0.5, lift=0)
        c.rect(off, v0 + h * 0.5, w * 0.98, 0.012, scale(col, 0.7), lift=0, alpha=0.6)
    c.rect(-0.1, 0.23, 0.50, 0.14, (0.97, 0.97, 0.97), lift=0.04)                      # label on the lower box
    c.rect(-0.18, 0.245, 0.26, 0.03, scale(acc, 0.85), lift=0)
    c.rect(-0.06, 0.20, 0.38, 0.02, (0.6, 0.6, 0.62), lift=0)
    c.rect(0.03, 0.63, 0.62, 0.05, scale(acc, 0.9), lift=0.1)                          # brand band on the lid
    soft_disc(c, -0.3, 0.9, 0.35, 0.05, WHITE, 0.3, 1.3, add=True)
    soft_disc(c, 0.0, 0.46, 0.6, 0.03, BLACK, 0.3, 1.3)


@sprop("rf_plinth", aspect=2.2, fill=0.5)
def rf_plinth(c, color):
    ao(c, 0.0, 0.0, 1.1, 0.15)
    base = (0.93, 0.94, 0.96)
    c.ellipse(0.0, 0.01, 0.55, 0.55 * TILT, scale(base, 0.55), lift=0)
    craft.cylinder(c, 0.0, 0.03, 0.54, 0.25, base, scale(base, 0.58), scale(base, 1.04), tilt=TILT, lip=True)
    soft_disc(c, -0.2, 0.34, 0.3, 0.07, WHITE, 0.4, 1.2, add=True)


@sprop("rf_stool", aspect=1.8, fill=0.5)
def rf_stool(c, color):
    ao(c, 0.0, 0.0, 0.9, 0.14)
    for sgn in (-1, 1):
        c.line(sgn * 0.30, 0.02, sgn * 0.22, 0.36, 0.06, scale(WOOD, 0.62), 1.0)
    craft.cylinder(c, 0.0, 0.34, 0.42, 0.10, scale(WOOD, 1.05), scale(WOOD, 0.62), scale(WOOD, 1.1), tilt=TILT)
    for k in range(5):
        craft.arc(c, 0.0, 0.44, 0.1 + 0.06 * k, (0.1 + 0.06 * k) * TILT, 20, 330, 0.004, scale(WOOD, 0.8), 0.4, 8)


@niche("shoe-store", "Shoe store", subjects=("rf_sneaker",),
       strong=("shoe store", "shoe shop", "footwear", "sneakers", "sneaker", "shoes", "juta", "joote", "जूते", "जूता", "चप्पल", "फुटवियर",
               "jooton ki dukaan", "leather shoes", "sports shoes"),
       weak=("sandals", "heels", "loafers", "boots", "slippers", "trainers", "cobbler"), accent="#2980b9", mood="light", group="retail")
def shoe_store(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.55)
    shoe_cols = [(0.16, 0.50, 0.73), (0.88, 0.30, 0.22), (0.95, 0.75, 0.15), (0.25, 0.25, 0.28), (0.90, 0.90, 0.92), (0.2, 0.65, 0.45), (0.55, 0.35, 0.2),
                 (0.75, 0.3, 0.55)]
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        for row, v in enumerate((0.20, 0.36, 0.52)):                                         # shoe wall: shelves of shoes and boxes
            S.rect(1.0, v + 0.065, 6.0, 0.012, scale(WHITE, k), lift=0.0)
            for i in range(30):
                u = -1.6 + i * 0.13 + (row % 2) * 0.06 + S.rng.uniform(-0.01, 0.01)
                col = scale(shoe_cols[(i * 3 + row) % len(shoe_cols)], k)
                if (i + row) % 4 == 0:
                    S.rect(u, v + 0.015, 0.11, 0.095, scale(mix(col, WHITE, 0.4), k), r=0.005, lift=0.0)
                else:
                    S.rect(u, v + 0.032, 0.11, 0.05, col, r=0.022, lift=0.0)
                    S.rect(u, v + 0.062, 0.115, 0.016, scale(WHITE, 0.9 * k), r=0.006, lift=0.0)
        S.rect(1.0, 0.64, 6.0, 0.03, scale(P.wall_bot, 0.8), lift=0.0)
        for u in (0.4, 1.1, 1.8):                                                            # track spot lights
            S.glow(u, 0.05, 0.28, (1.0, 0.97, 0.9), 0.5 if not dk else 0.6)
            S.glow(u, 0.38, 0.5, (1.0, 0.95, 0.85), 0.15 if not dk else 0.2)
        S.rect(1.0, 0.012, 6.0, 0.03, scale(P.wall_bot, 0.55), lift=0.0)
        S.floor(0.64, mix(P.floor_top, WHITE, 0.45), mix(P.floor_bot, WHITE, 0.3))
    fl_a = mix(P.paper, P.surface, 0.14) if not dk else scale(P.surface, 0.5)
    fl_b = mix(P.paper, P.surface, 0.24) if not dk else scale(P.surface, 0.42)
    S.tiles(-3.0, 0.64, 5.0, 2.6, fl_a, fl_b, 0.20)
    S.rect(1.0, 0.64, 8.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    _floor_glow(S, 1.1, 0.78, 1.1, 0.18, (1.0, 0.97, 0.9), 0.40 if dk else 0.20)
    S.rect(1.12, 0.462, 1.0, 0.014, (0.95, 0.95, 0.96), lift=0.1)                              # floating shelf with sneakers
    S.rect(1.12, 0.474, 0.96, 0.006, P.accent, lift=0.0, alpha=0.8)
    S.soft(1.12, 0.50, 0.5, 0.06, (1.0, 0.97, 0.9), 0.30, 1.4, add=True)
    for u, a_, b_ in ((0.78, (0.95, 0.60, 0.15), (0.97, 0.97, 0.97)), (1.12, (0.2, 0.62, 0.42), (0.96, 0.96, 0.96)), (1.46, (0.35, 0.35, 0.42), (0.9, 0.35, 0.3))):
        S.put("rf_sneaker", u, 0.455, 0.075, color=(a_, b_), shadow=False)
    S.put("rf_stool", 0.66, 0.95, 0.18)
    S.put("rf_leather_shoe", 0.66, 0.835, 0.115, color=((0.45, 0.22, 0.09), (0, 0, 0)), shadow=False)
    S.put("rf_plinth", 1.12, 0.95, 0.26, framed=False)
    S.put("rf_sneaker", 1.12, 0.815, 0.23, color=(P.accent, (0.97, 0.97, 0.97)), subject=True, shadow=False)
    S.put("rf_shoe_box", 1.54, 0.95, 0.24, color=P)
    S.put("rf_sneaker", 1.54, 0.745, 0.08, color=((0.90, 0.32, 0.22), (0.96, 0.96, 0.96)), shadow=False)       # on top of the boxes
    S.focus("detail", 1.12, 0.66)
    with S.near(16.0):
        S.circle(0.55, 0.98, 0.05, mix(P.accent, WHITE, 0.3), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.15, 0.06, (1.0, 0.95, 0.85), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ JEWELLERY
RUBY = (0.80, 0.06, 0.16)
EMERALD = (0.04, 0.56, 0.32)
PEARL = (0.96, 0.93, 0.87)
DIAMOND = (0.88, 0.95, 1.0)
VELVET = (0.30, 0.05, 0.11)
NAVY = (0.07, 0.09, 0.20)


def _glint(c, u, v, r, alpha=0.9):
    """A four-point sparkle drawn with additive soft discs and two hair-thin strokes."""
    soft_disc(c, u, v, r * 1.3, r * 1.3, (1.0, 0.93, 0.75), 0.5 * alpha, 2.0, add=True)
    soft_disc(c, u, v, r * 1.0, r * 0.07, WHITE, alpha, 1.0, add=True)
    soft_disc(c, u, v, r * 0.07, r * 1.0, WHITE, alpha, 1.0, add=True)
    soft_disc(c, u, v, r * 0.22, r * 0.22, WHITE, alpha, 1.5, add=True)


def _gem(c, u, v, r, col, glint=True):
    """A faceted stone seen from the side: crown, girdle, pavilion, with bright and dark facets."""
    c.poly([(u - r, v), (u - r * 0.62, v + r * 0.5), (u + r * 0.62, v + r * 0.5), (u + r, v), (u, v - r * 0.95)], mix(col, WHITE, 0.15), lift=0.12)
    c.poly([(u - r, v), (u, v - r * 0.95), (u - r * 0.15, v)], scale(col, 0.62), alpha=0.7, lift=0)
    c.poly([(u + r, v), (u, v - r * 0.95), (u + r * 0.2, v)], scale(col, 0.5), alpha=0.7, lift=0)
    c.poly([(u - r * 0.62, v + r * 0.5), (u - r * 0.15, v), (u + r * 0.15, v + r * 0.5)], mix(col, WHITE, 0.55), alpha=0.8, lift=0)
    c.poly([(u + r * 0.62, v + r * 0.5), (u + r * 0.3, v), (u + r * 0.1, v + r * 0.5)], mix(col, WHITE, 0.25), alpha=0.7, lift=0)
    c.line(u - r, v, u + r, v, r * 0.07, WHITE, 0.55)
    if glint:
        _glint(c, u - r * 0.3, v + r * 0.25, r * 1.6, 0.8)


def _bead(c, u, v, r, col=GOLD):
    c.ellipse(u, v, r, r, scale(col, 0.62), lift=0)
    c.ellipse(u - r * 0.08, v + r * 0.1, r * 0.9, r * 0.88, col, lift=0.2)
    c.ellipse(u - r * 0.3, v + r * 0.35, r * 0.3, r * 0.22, WHITE, alpha=0.85, lift=0)


def _chain(c, p0, p1, p2, n, r, col=GOLD, alt=None):
    """n beads along a quadratic curve p0 -> p2 bent towards p1."""
    for i in range(n):
        t = i / float(n - 1)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        _bead(c, x, y, r, alt if (alt and i % 4 == 2) else col)


@sprop("rf_jewel_bust", aspect=0.82, fill=1.0)
def rf_jewel_bust(c, color):
    rng = c.rng
    nv = color if isinstance(color, tuple) else NAVY
    ao(c, 0.0, 0.0, 0.62, 0.08)
    c.ellipse(0.0, 0.02, 0.26, 0.26 * TILT, scale(GOLD_D, 0.7), lift=0.1)
    craft.hshade_box(c, 0.0, 0.09, 0.07, 0.14, mix(GOLD, WHITE, 0.15), scale(GOLD_D, 0.8))
    # velvet bust: sloped shoulders, neck, cut top
    _hpoly(c, [(-0.42, 0.16), (0.42, 0.16), (0.42, 0.30), (0.36, 0.42), (0.21, 0.51), (0.115, 0.58), (0.10, 0.88), (-0.10, 0.88), (-0.115, 0.58), (-0.21, 0.51),
                (-0.36, 0.42), (-0.42, 0.30)], mix(nv, WHITE, 0.18), scale(nv, 0.40), 0.10, power=1.1, smooth=1)
    c.ellipse(0.0, 0.88, 0.10, 0.10 * TILT * 0.8, mix(nv, WHITE, 0.2), lift=0.1)
    c.ellipse(0.0, 0.88, 0.075, 0.075 * TILT * 0.7, scale(nv, 0.4), lift=0)
    soft_disc(c, -0.24, 0.36, 0.14, 0.09, WHITE, 0.32, 1.4, add=True)                  # velvet sheen on the lit shoulder
    soft_disc(c, 0.32, 0.28, 0.12, 0.12, BLACK, 0.4, 1.3)
    # necklaces: choker, main chain with a drop, and ruby / pearl strands
    _chain(c, (-0.105, 0.80), (0.0, 0.67), (0.105, 0.80), 13, 0.015, GOLD)
    _chain(c, (-0.12, 0.74), (0.0, 0.25), (0.12, 0.74), 28, 0.017, GOLD, RUBY)
    _chain(c, (-0.11, 0.76), (0.0, 0.46), (0.11, 0.76), 22, 0.014, PEARL)
    # pendant: gold frame, big ruby, emerald side stones, hanging drops
    pu, pv = 0.0, 0.43
    c.ellipse(pu, pv, 0.115, 0.135, scale(GOLD_D, 0.8), lift=0)
    c.ellipse(pu, pv + 0.004, 0.108, 0.128, GOLD, lift=0.2)
    for k in range(16):
        a = 2 * math.pi * k / 16
        c.ellipse(pu + math.cos(a) * 0.098, pv + math.sin(a) * 0.118, 0.01, 0.01, GOLD_L, lift=0.1)
    c.ellipse(pu, pv, 0.072, 0.09, scale(RUBY, 0.55), lift=0)
    c.ellipse(pu, pv + 0.004, 0.066, 0.083, RUBY, lift=0.2)
    c.ellipse(pu - 0.02, pv + 0.03, 0.02, 0.026, (1.0, 0.7, 0.7), alpha=0.8, lift=0)
    for sgn in (-1, 1):
        c.ellipse(pu + sgn * 0.168, pv - 0.005, 0.036, 0.046, scale(GOLD, 0.8), lift=0.1)
        c.ellipse(pu + sgn * 0.168, pv - 0.003, 0.026, 0.034, EMERALD, lift=0.2)
        c.line(pu + sgn * 0.168, pv - 0.05, pu + sgn * 0.168, pv - 0.1, 0.006, GOLD, 1.0)
        _bead(c, pu + sgn * 0.168, pv - 0.115, 0.017, PEARL)
    for k, du in enumerate((-0.07, 0.0, 0.07)):
        c.line(pu + du, pv - 0.12, pu + du, pv - 0.19 - 0.02 * (k == 1), 0.006, GOLD, 1.0)
        _bead(c, pu + du, pv - 0.21 - 0.02 * (k == 1), 0.022, PEARL if k != 1 else RUBY)
    _glint(c, pu - 0.03, pv + 0.05, 0.13, 0.9)
    _glint(c, 0.12, 0.60, 0.07, 0.7)
    _glint(c, -0.13, 0.50, 0.08, 0.7)


@sprop("rf_ring_box", aspect=1.25, fill=0.8)
def rf_ring_box(c, color):
    ao(c, 0.0, 0.0, 1.1, 0.16)
    vel = VELVET
    # lid (open, leaning back), box body, cushion with slit, ring
    _hpoly(c, [(-0.46, 0.5), (0.46, 0.5), (0.5, 0.78), (-0.5, 0.78)], scale(vel, 1.05), scale(vel, 0.5), 0.05)
    c.rect(0.0, 0.64, 0.84, 0.18, mix(vel, WHITE, 0.08), r=0.03, lift=0.1)
    c.line(-0.5, 0.78, 0.5, 0.78, 0.015, GOLD, 0.95)
    craft.hshade_box(c, 0.0, 0.22, 1.0, 0.44, scale(vel, 1.1), scale(vel, 0.45), r=0.03)
    c.rect(0.0, 0.43, 1.0, 0.025, GOLD, lift=0.2)
    c.rect(0.0, 0.405, 0.92, 0.012, GOLD_D, lift=0, alpha=0.7)
    c.poly([(-0.44, 0.45), (0.44, 0.45), (0.38, 0.54), (-0.38, 0.54)], mix(vel, WHITE, 0.14), lift=0.05)            # cushion
    c.line(-0.36, 0.495, 0.36, 0.495, 0.02, BLACK, 0.7)                                                          # ring slot
    # ring standing in the slot
    c.ellipse(0.0, 0.70, 0.19, 0.24, scale(GOLD_D, 0.7), lift=0)
    c.ellipse(0.0, 0.705, 0.18, 0.23, GOLD, lift=0.25)
    c.ellipse(0.0, 0.715, 0.135, 0.185, scale(vel, 0.45), lift=0)
    craft.arc(c, 0.0, 0.705, 0.155, 0.205, 100, 190, 0.012, GOLD_L, 0.9, 8)
    _gem(c, 0.0, 0.90, 0.085, DIAMOND)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.13, 0.86, 0.016, 0.016, DIAMOND, lift=0.2)
    _glint(c, 0.03, 0.95, 0.2, 1.0)
    soft_disc(c, 0.0, 0.43, 0.5, 0.04, GOLD_L, 0.25, 1.4, add=True)


@sprop("rf_jhumka_stand", aspect=0.62, fill=1.0)
def rf_jhumka_stand(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.07)
    c.ellipse(0.0, 0.02, 0.2, 0.2 * TILT, scale(GOLD_D, 0.7), lift=0.1)
    craft.hshade_box(c, 0.0, 0.40, 0.035, 0.76, mix(NAVY, WHITE, 0.2), scale(NAVY, 0.4))
    craft.hshade_box(c, 0.0, 0.86, 0.60, 0.05, mix(VELVET, WHITE, 0.14), scale(VELVET, 0.5), r=0.02)
    for sgn in (-1, 1):
        x = sgn * 0.20
        c.line(x, 0.84, x, 0.74, 0.012, GOLD_L, 1.0)
        # jhumka: dome, bell skirt, scalloped hem and pearl drops
        c.poly([(x - 0.075, 0.70), (x + 0.075, 0.70), (x + 0.05, 0.76), (x - 0.05, 0.76)], GOLD, lift=0.2)
        c.ellipse(x, 0.735, 0.06, 0.04, GOLD, lift=0.2)
        c.poly([(x - 0.065, 0.70), (x + 0.065, 0.70), (x + 0.13, 0.50), (x - 0.13, 0.50)], scale(GOLD, 0.98), lift=0.2)
        c.poly([(x + 0.03, 0.70), (x + 0.065, 0.70), (x + 0.13, 0.50), (x + 0.06, 0.50)], scale(GOLD_D, 0.8), alpha=0.5, lift=0)
        c.poly([(x - 0.05, 0.69), (x - 0.02, 0.69), (x - 0.06, 0.52), (x - 0.10, 0.52)], GOLD_L, alpha=0.45, lift=0)
        for k in range(6):
            _bead(c, x - 0.115 + k * 0.046, 0.50, 0.022, GOLD)
        for k in range(5):
            xx = x - 0.092 + k * 0.046
            c.line(xx, 0.48, xx, 0.43 - 0.012 * (k % 2), 0.005, GOLD, 1.0)
            _bead(c, xx, 0.415 - 0.012 * (k % 2), 0.020, PEARL)
        for k in range(3):
            c.ellipse(x - 0.04 + k * 0.04, 0.62, 0.011, 0.011, RUBY if k == 1 else GOLD_D, lift=0.15)
        c.ellipse(x, 0.575, 0.016, 0.016, EMERALD, lift=0.2)
        _glint(c, x - 0.03, 0.66, 0.09, 0.85)


@sprop("rf_bangle_tray", aspect=4.3, fill=0.42)
def rf_bangle_tray(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.7, 0.14)
    vel = NAVY if False else scale(VELVET, 0.9)
    c.ellipse(0.0, 0.03, 0.92, 0.92 * 0.34, scale(vel, 0.4), lift=0)
    craft.hshade_box(c, 0.0, 0.07, 1.82, 0.08, scale(GOLD_D, 0.9), scale(GOLD_D, 0.5), r=0.02)
    c.ellipse(0.0, 0.14, 0.9, 0.9 * 0.32, GOLD, lift=0.1)
    c.ellipse(0.0, 0.145, 0.85, 0.85 * 0.30, vel, lift=0.12)
    soft_disc(c, -0.2, 0.17, 0.6, 0.08, WHITE, 0.14, 1.3, add=True)
    # stacked gold bangles with stone settings
    for k, (bu, bv, br) in enumerate(((-0.45, 0.17, 0.30), (-0.30, 0.19, 0.30), (-0.15, 0.17, 0.30), (0.04, 0.19, 0.30))):
        col = GOLD if k % 2 == 0 else mix(GOLD, (0.95, 0.8, 0.5), 0.4)
        c.ellipse(bu, bv, br, br * 0.40, scale(col, 0.6), lift=0)
        c.ellipse(bu, bv + 0.012, br * 0.97, br * 0.38, col, lift=0.2)
        c.ellipse(bu, bv + 0.02, br * 0.80, br * 0.30, vel, lift=0)
        c.ellipse(bu, bv + 0.012, br * 0.80, br * 0.28, scale(vel, 0.7), lift=0)
        craft.arc(c, bu, bv + 0.012, br * 0.97, br * 0.38, 150, 210, 0.012, GOLD_L, 0.9, 6)
        for q in range(7):
            a = math.radians(205 + q * 18)
            c.ellipse(bu + math.cos(a) * br * 0.93, bv + 0.01 + math.sin(a) * br * 0.34, 0.016, 0.014, RUBY if q % 3 == 1 else (GOLD_L if q % 2 else DIAMOND), lift=0.15)
    # pearl strand curled on the tray and loose rings
    for i in range(26):
        t = i / 25.0
        a = math.radians(-20 + 250 * t)
        _bead(c, 0.50 + math.cos(a) * 0.28, 0.18 + math.sin(a) * 0.08, 0.026, PEARL)
    for ru, rv in ((0.50, 0.17), (0.72, 0.21)):
        c.ellipse(ru, rv, 0.075, 0.032, scale(GOLD_D, 0.8), lift=0)
        c.ellipse(ru, rv + 0.008, 0.07, 0.027, GOLD, lift=0.2)
        c.ellipse(ru, rv + 0.012, 0.05, 0.017, scale(vel, 0.6), lift=0)
        _gem(c, ru + 0.02, rv + 0.05, 0.028, DIAMOND if ru < 0.6 else EMERALD, glint=False)
    _glint(c, -0.25, 0.25, 0.14, 0.9)
    _glint(c, 0.62, 0.26, 0.11, 0.8)


@niche("jewellery", "Jewellery store", subjects=("rf_jewel_bust",),
       strong=("jewellery", "jewelry", "jeweller", "jeweler", "gold", "ornaments", "sonar", "sona", "gahne", "gehne", "ज्वेलरी", "गहने", "सोना",
               "zewar", "jewellery shop", "gold necklace", "diamond ring"),
       weak=("necklace", "bangles", "earrings", "diamond", "silver", "kundan", "bridal"), accent="#d4af37", mood="dark", group="retail")
def jewellery(S):
    P = S.pal
    dk = _dark(S)
    wallc = (0.07, 0.04, 0.09) if dk else mix(P.wall_bot, VELVET, 0.45)
    wallt = (0.12, 0.07, 0.13) if dk else mix(P.wall_top, VELVET, 0.30)
    with S.far():
        S.wall(wallt, wallc, 0.60)
        for i in range(14):                                                                  # velvet curtain folds
            S.rect(-1.5 + i * 0.28, 0.25, 0.12, 0.9, scale(wallc, 0.7 if i % 2 else 1.25), lift=0.0, alpha=0.45)
        for cu in (0.30, 1.95):                                                              # lit wall niches
            S.rect(cu, 0.30, 0.40, 0.36, scale(GOLD_D, 0.55), r=0.02, lift=0.0)
            S.rect(cu, 0.30, 0.36, 0.32, (0.10, 0.06, 0.08), lift=0.0)
            S.glow(cu, 0.30, 0.30, (1.0, 0.78, 0.42), 0.28 if dk else 0.2)
        S.bokeh(18, 0.0, 0.05, 2.0, 0.58, [(1.0, 0.85, 0.5), (1.0, 0.72, 0.35), (1.0, 0.95, 0.8)], 0.008, 0.03, 0.55 if dk else 0.3)
        for u in (0.55, 1.1, 1.6):
            S.glow(u, 0.0, 0.55, (1.0, 0.82, 0.5), 0.55 if dk else 0.35)
        S.floor(0.60, (0.08, 0.05, 0.08) if dk else scale(P.accent_dark, 0.5), (0.03, 0.02, 0.04) if dk else scale(P.accent_dark, 0.3))
    # glossy dark counter with a gold edge and spot pools
    S.floor(0.62, (0.17, 0.10, 0.15) if dk else mix(P.accent_dark, BLACK, 0.4), (0.05, 0.03, 0.06) if dk else mix(P.accent_dark, BLACK, 0.65))
    S.rect(1.0, 0.62, 8.0, 0.012, GOLD_D, lift=0.0)
    S.rect(1.0, 0.628, 8.0, 0.004, GOLD_L, lift=0.0, alpha=0.7)
    for u, a_ in ((0.75, 0.5), (1.12, 0.8), (1.52, 0.5)):
        S.light_shaft(u - 0.04, -0.05, u + 0.04, -0.05, u + 0.34, 0.88, u - 0.34, 0.88, (1.0, 0.85, 0.55), 0.035 * a_ + (0.02 if dk else 0.0))
    _floor_glow(S, 1.12, 0.84, 0.95, 0.20, (1.0, 0.82, 0.5), 0.55 if dk else 0.30)
    _floor_glow(S, 1.12, 0.95, 0.60, 0.07, (1.0, 0.85, 0.55), 0.30 if dk else 0.2)
    S.put("rf_jhumka_stand", 1.58, 0.90, 0.36)
    S.put("rf_jewel_bust", 1.10, 0.86, 0.56)
    S.mark_subject("rf_jewel_bust", 1.0, 0.42, 1.2, 0.62)
    S.put("rf_ring_box", 0.74, 0.92, 0.22)
    S.put("rf_bangle_tray", 1.34, 0.99, 0.14)
    S.focus("detail", 1.10, 0.56)
    for u, v, r in ((1.07, 0.60, 0.06), (0.74, 0.76, 0.07), (1.58, 0.56, 0.06), (1.26, 0.50, 0.05)):
        _sparkle(S, u, v, r, (1.0, 0.92, 0.7), 0.8)
    with S.near(18.0):
        S.circle(0.52, 0.98, 0.05, (1.0, 0.8, 0.4), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.75, 0.20, 0.07, (1.0, 0.85, 0.5), alpha=0.3, lift=0, soft=6.0)
        S.circle(0.62, 0.12, 0.04, (1.0, 0.9, 0.7), alpha=0.35, lift=0, soft=6.0)


# ================================================================================================ GROCERY
TOMATO = (0.86, 0.15, 0.10)
ORANGE = (0.97, 0.56, 0.10)
APPLE = (0.82, 0.14, 0.12)
LEMON = (0.96, 0.82, 0.15)
GREEN = (0.30, 0.62, 0.20)
JUTE = (0.78, 0.65, 0.44)
PACKETS = [(0.85, 0.18, 0.16), (0.96, 0.72, 0.12), (0.15, 0.55, 0.30), (0.18, 0.40, 0.75), (0.93, 0.45, 0.12), (0.55, 0.25, 0.60), (0.95, 0.92, 0.85),
           (0.10, 0.60, 0.65)]


def _fruit(c, u, v, r, col, hl=0.55):
    c.ellipse(u + r * 0.05, v - r * 0.06, r, r * 0.97, scale(col, 0.55), lift=0)
    c.ellipse(u - r * 0.04, v + r * 0.04, r * 0.95, r * 0.92, col, lift=0.18)
    c.ellipse(u - r * 0.35, v + r * 0.40, r * 0.30, r * 0.20, WHITE, angle=25, alpha=hl, lift=0)


@sprop("rf_produce_crate", aspect=1.85, fill=0.66)
def rf_produce_crate(c, color):
    rng = c.rng
    kind = color if isinstance(color, str) else "tomato"
    ao(c, 0.0, 0.0, 1.3, 0.14)
    c.rect(0.0, 0.40, 1.16, 0.12, scale(WOOD, 0.45), lift=0)                       # inside of the back wall
    cols = {"tomato": [TOMATO, (0.92, 0.25, 0.12), (0.78, 0.10, 0.08)], "orange": [ORANGE, (0.99, 0.62, 0.14), (0.92, 0.48, 0.08)],
            "apple": [APPLE, (0.70, 0.12, 0.10), (0.55, 0.72, 0.22)], "lemon": [LEMON, (0.98, 0.88, 0.25), (0.90, 0.75, 0.10)],
            "greens": [GREEN, (0.20, 0.52, 0.16), (0.40, 0.70, 0.25)]}[kind]
    if kind == "greens":
        for _ in range(26):
            _leaf(c, rng.uniform(-0.5, 0.5), rng.uniform(0.34, 0.5), rng.uniform(0.22, 0.34), rng.uniform(40, 140), rng.choice(cols), 0.5)
        for _ in range(14):
            _leaf(c, rng.uniform(-0.5, 0.5), rng.uniform(0.38, 0.52), rng.uniform(0.2, 0.3), rng.uniform(30, 150), rng.choice(cols), 0.55)
    else:
        for row, (vv, n, r) in enumerate(((0.55, 7, 0.085), (0.50, 8, 0.088), (0.45, 8, 0.09), (0.41, 8, 0.092))):
            for i in range(n):
                u = -0.50 + (i + (0.5 if row % 2 else 0.0)) * (1.0 / (n - 0.5 if row % 2 else n)) + rng.uniform(-0.015, 0.015)
                col = rng.choice(cols)
                _fruit(c, u, vv + rng.uniform(-0.01, 0.01), r, col)
                if kind == "tomato":
                    for k in range(4):
                        _leaf(c, u, vv + r * 0.85, r * 0.45, 90 + (k - 1.5) * 50, (0.22, 0.5, 0.2), 0.3, False)
    # front slats, corner posts, price tag
    for i in range(3):
        v0 = 0.04 + i * 0.105
        craft.hshade_box(c, 0.0, v0 + 0.045, 1.2, 0.092, scale(WOOD, 1.1 + 0.04 * (i % 2)), scale(WOOD, 0.62), r=0.008)
        for _ in range(5):
            x = rng.uniform(-0.55, 0.5)
            c.line(x, v0 + 0.045 + rng.uniform(-0.02, 0.02), x + rng.uniform(0.08, 0.25), v0 + 0.045 + rng.uniform(-0.01, 0.01), 0.004, scale(WOOD, 0.65), 0.4)
        c.rect(0.0, v0 + 0.097, 1.2, 0.009, BLACK, lift=0, alpha=0.4)
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.57, 0.19, 0.075, 0.34, scale(WOOD, 1.0), scale(WOOD, 0.55), r=0.008)
        c.ellipse(sgn * 0.57, 0.08, 0.012, 0.012, (0.4, 0.35, 0.3), lift=0.1)
        c.ellipse(sgn * 0.57, 0.30, 0.012, 0.012, (0.4, 0.35, 0.3), lift=0.1)
    c.rect(-0.2, 0.16, 0.34, 0.15, (0.97, 0.95, 0.88), r=0.01, lift=0.05)
    c.rect(-0.2, 0.225, 0.34, 0.02, P_GREEN, lift=0)
    c.line(-0.33, 0.17, -0.12, 0.17, 0.014, (0.25, 0.25, 0.25), 0.8)
    c.line(-0.33, 0.12, -0.20, 0.12, 0.010, (0.4, 0.4, 0.4), 0.7)


P_GREEN = (0.15, 0.62, 0.34)


@sprop("rf_shelf_rack", aspect=1.0, fill=1.0)
def rf_shelf_rack(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.1)
    c.rect(0.0, 0.5, 1.0, 1.0, (0.90, 0.89, 0.84), lift=0.06)
    c.rect(0.0, 0.5, 1.0, 1.0, BLACK, lift=0, alpha=0.05)
    for si, sv in enumerate((0.07, 0.37, 0.67)):
        x = -0.46
        while x < 0.40:
            kind = rng.random()
            if kind < 0.55:                                                        # packet
                w, h = rng.uniform(0.10, 0.15), rng.uniform(0.15, 0.23)
                col = rng.choice(PACKETS)
                craft.hshade_box(c, x + w / 2, sv + 0.015 + h / 2, w, h, mix(col, WHITE, 0.08), scale(col, 0.65), r=0.008)
                c.rect(x + w / 2, sv + 0.015 + h * 0.5, w * 0.8, h * 0.22, WHITE, lift=0, alpha=0.88)
                c.rect(x + w / 2, sv + 0.015 + h * 0.5, w * 0.5, h * 0.06, scale(col, 0.7), lift=0, alpha=0.9)
                c.rect(x + w / 2, sv + 0.015 + h * 0.92, w * 0.9, h * 0.05, scale(col, 0.7), lift=0, alpha=0.5)
            elif kind < 0.82:                                                      # tin
                w, h = rng.uniform(0.09, 0.12), rng.uniform(0.11, 0.16)
                col = rng.choice(PACKETS)
                craft.hshade_box(c, x + w / 2, sv + 0.015 + h / 2, w, h, (0.88, 0.88, 0.9), (0.52, 0.52, 0.56), r=0.005)
                c.rect(x + w / 2, sv + 0.015 + h * 0.5, w, h * 0.55, col, lift=0.1, alpha=0.95)
                c.ellipse(x + w / 2, sv + 0.015 + h, w / 2, w / 2 * 0.35, (0.8, 0.8, 0.82), lift=0.1)
                c.ellipse(x + w / 2 - w * 0.1, sv + 0.015 + h * 0.55, w * 0.1, h * 0.22, WHITE, alpha=0.5, lift=0)
            else:                                                                  # glass jar
                w, h = rng.uniform(0.09, 0.12), rng.uniform(0.15, 0.2)
                col = rng.choice([(0.85, 0.65, 0.2), (0.7, 0.25, 0.15), (0.5, 0.6, 0.2)])
                craft.hshade_box(c, x + w / 2, sv + 0.015 + h * 0.45, w, h * 0.9, mix(col, WHITE, 0.15), scale(col, 0.6), r=0.012)
                c.rect(x + w / 2, sv + 0.015 + h * 0.93, w * 0.8, h * 0.14, (0.75, 0.15, 0.12), lift=0.12)
                c.rect(x + w / 2 - w * 0.2, sv + 0.015 + h * 0.45, w * 0.1, h * 0.6, WHITE, lift=0, alpha=0.5)
            x += w + rng.uniform(0.008, 0.03)
        craft.hshade_box(c, 0.0, sv, 1.0, 0.03, (0.78, 0.78, 0.78), (0.5, 0.5, 0.52), r=0.004)
        c.rect(0.0, sv + 0.012, 1.0, 0.005, WHITE, lift=0, alpha=0.6)
        c.rect(0.0, sv - 0.03, 1.0, 0.03, BLACK, lift=0, alpha=0.12)
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.495, 0.5, 0.034, 1.0, (0.85, 0.85, 0.87), (0.45, 0.45, 0.5))
    c.rect(0.0, 0.985, 1.03, 0.03, P_GREEN, lift=0.1)


@sprop("rf_wicker_basket", aspect=1.35, fill=0.9)
def rf_wicker_basket(c, color):
    rng = c.rng
    wick = (0.78, 0.56, 0.30)
    ao(c, 0.0, 0.0, 1.0, 0.14)
    craft.arc(c, 0.0, 0.62, 0.5, 0.42, 0, 180, 0.05, scale(wick, 0.8), 1.0, 14)            # handle
    c.ellipse(0.0, 0.58, 0.52, 0.52 * TILT, scale(wick, 0.5), lift=0)
    # onions heaped above the rim
    for row, (vv, n) in enumerate(((0.72, 4), (0.66, 5), (0.61, 5))):
        for i in range(n):
            u = -0.38 + (i + 0.5 * (row % 2)) * (0.76 / (n - 0.5 * (row % 2) - 0.0)) * 0.98
            _fruit(c, u, vv + rng.uniform(-0.01, 0.01), 0.11, rng.choice([(0.70, 0.30, 0.42), (0.78, 0.40, 0.46), (0.62, 0.22, 0.36)]), 0.5)
            c.line(u, vv + 0.1, u + 0.01, vv + 0.17, 0.012, (0.7, 0.6, 0.35), 1.0)
    # woven body (brick pattern of small plaits)
    body = [(-0.55, 0.60), (0.55, 0.60), (0.42, 0.04), (-0.42, 0.04)]
    _hpoly(c, body, scale(wick, 1.05), scale(wick, 0.58), 0.04)
    for r_ in range(7):
        v = 0.07 + r_ * 0.078
        half = 0.42 + 0.13 * (v - 0.04) / 0.56
        n = 9
        for i in range(n):
            x = -half + (i + 0.5 * (r_ % 2)) * (2 * half / n)
            if abs(x) > half - 0.02:
                continue
            c.rect(x, v + 0.035, 2 * half / n * 0.86, 0.058, scale(wick, 0.95 + 0.12 * rng.random() - (x + 0.5) * 0.28), r=0.012, lift=0.12)
        c.line(-half, v + 0.0, half, v + 0.0, 0.006, scale(wick, 0.45), 0.55)
    craft.hshade_box(c, 0.0, 0.595, 1.12, 0.05, scale(wick, 1.0), scale(wick, 0.6), r=0.02)
    c.rect(0.0, 0.615, 1.1, 0.01, scale(wick, 1.2), lift=0, alpha=0.6)
    soft_disc(c, -0.25, 0.32, 0.18, 0.2, WHITE, 0.15, 1.3, add=True)


@sprop("rf_grain_sack", aspect=0.95, fill=0.9)
def rf_grain_sack(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.14)
    body = [(-0.42, 0.52), (-0.46, 0.30), (-0.40, 0.05), (0.40, 0.05), (0.46, 0.30), (0.42, 0.52)]
    _hpoly(c, body, scale(JUTE, 1.08), scale(JUTE, 0.62), 0.05, smooth=2)
    for _ in range(40):                                                                    # woven jute texture
        x, y = rng.uniform(-0.4, 0.4), rng.uniform(0.08, 0.5)
        if rng.random() < 0.5:
            c.line(x, y, x + rng.uniform(0.04, 0.12), y, 0.004, scale(JUTE, rng.uniform(0.7, 0.85)), 0.35)
        else:
            c.line(x, y, x, y + rng.uniform(0.04, 0.1), 0.004, scale(JUTE, rng.uniform(0.7, 0.85)), 0.35)
    c.rect(0.0, 0.28, 0.5, 0.18, (0.97, 0.95, 0.9), lift=0.04, alpha=0.95)                 # printed label
    c.rect(0.0, 0.34, 0.5, 0.035, P_GREEN, lift=0)
    c.ellipse(0.0, 0.25, 0.08, 0.06, (0.85, 0.65, 0.2), lift=0.1)
    c.line(-0.2, 0.19, 0.2, 0.19, 0.014, (0.3, 0.3, 0.3), 0.7)
    c.ellipse(0.0, 0.52, 0.43, 0.43 * 0.30, scale(JUTE, 0.7), lift=0)                       # open rolled top
    c.ellipse(0.0, 0.535, 0.40, 0.40 * 0.26, (0.55, 0.42, 0.22), lift=0)
    c.ellipse(0.0, 0.575, 0.35, 0.11, (0.90, 0.72, 0.26), lift=0.15)                       # dal / grain mound
    for _ in range(46):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.33
        c.ellipse(math.cos(a) * r, 0.585 + math.sin(a) * r * 0.30, 0.012, 0.009, rng.choice([(0.98, 0.84, 0.36), (0.80, 0.60, 0.18), (1.0, 0.92, 0.5)]),
                  lift=0.1, alpha=0.95)
    c.ellipse(0.12, 0.62, 0.07, 0.04, (0.8, 0.82, 0.85), lift=0.2)                          # steel scoop
    c.ellipse(0.12, 0.625, 0.055, 0.028, (0.55, 0.45, 0.25), lift=0)
    c.line(0.16, 0.64, 0.30, 0.72, 0.018, (0.7, 0.72, 0.75), 1.0)
    soft_disc(c, -0.22, 0.38, 0.14, 0.22, WHITE, 0.18, 1.3, add=True)
    soft_disc(c, 0.36, 0.3, 0.1, 0.25, BLACK, 0.25, 1.4)


@niche("grocery", "Grocery store", subjects=("rf_produce_crate",),
       strong=("grocery", "grocery store", "kirana", "kirana store", "supermarket", "provision store", "general store", "किराना", "किराने की दुकान",
               "kirane ki dukaan", "fruits and vegetables", "sabzi", "सब्जी", "मंडी", "ration shop"),
       weak=("vegetables", "fruits", "produce", "organic", "daily needs", "dal chawal", "market"), accent="#27ae60", mood="light", group="retail")
def grocery(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        S.rect(1.0, 0.07, 6.0, 0.11, scale(P.accent, k), lift=0.0)                           # shop sign band
        S.rect(1.0, 0.07, 6.0, 0.012, scale(WHITE, k), lift=0.0, alpha=0.8)
        for row, v in enumerate((0.22, 0.38, 0.54)):                                         # shelves of packets
            S.rect(1.0, v + 0.065, 6.0, 0.014, scale((0.8, 0.8, 0.8), k), lift=0.0)
            for i in range(36):
                u = -1.9 + i * 0.115 + S.rng.uniform(-0.01, 0.01)
                col = scale(PACKETS[(i * 5 + row * 3) % len(PACKETS)], k)
                h = S.rng.uniform(0.08, 0.125)
                S.rect(u, v + 0.058 - h / 2, 0.095, h, col, lift=0.0)
                S.rect(u, v + 0.058 - h * 0.5, 0.07, h * 0.28, scale(WHITE, 0.9 * k), lift=0.0, alpha=0.85)
        for u in (0.3, 1.1, 1.9):                                                            # fluorescent lights
            S.rect(u, 0.005, 0.5, 0.015, scale(WHITE, k), lift=0.0)
            S.glow(u, 0.03, 0.55, (1.0, 0.98, 0.9), 0.35 if not dk else 0.5)
        S.floor(0.62, P.floor_top, P.floor_bot)
    t1 = mix(P.paper, P.accent, 0.10) if not dk else scale(P.floor_top, 0.8)
    t2 = mix(P.paper, P.accent, 0.20) if not dk else scale(P.floor_top, 0.6)
    S.tiles(-3.0, 0.62, 5.0, 2.6, t1, t2, 0.18)
    S.rect(1.0, 0.62, 8.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    _floor_glow(S, 1.1, 0.80, 1.1, 0.18, (1.0, 0.98, 0.9), 0.45 if dk else 0.18)
    S.put("rf_shelf_rack", 0.82, 0.74, 0.46, color=P, framed=False)
    S.put("rf_shelf_rack", 1.52, 0.74, 0.46, color=P, framed=False)
    S.put("rf_produce_crate", 0.56, 0.90, 0.26, color="orange")
    S.put("rf_produce_crate", 1.50, 0.90, 0.26, color="greens")
    S.put("rf_produce_crate", 1.03, 0.975, 0.33, color="tomato", subject=True)
    S.put("rf_wicker_basket", 1.50, 1.0, 0.17)
    S.put("rf_grain_sack", 0.58, 1.0, 0.2)
    S.focus("detail", 1.02, 0.80)
    with S.near(16.0):
        S.circle(0.55, 0.12, 0.06, (1.0, 0.98, 0.9), alpha=0.28, lift=0, soft=6.0)
        S.circle(1.76, 0.98, 0.07, mix(P.accent, WHITE, 0.2), alpha=0.35, lift=0, soft=6.0)


# ================================================================================================ BOOKSTORE
SPINES = [(0.62, 0.14, 0.18), (0.14, 0.24, 0.45), (0.15, 0.38, 0.27), (0.88, 0.66, 0.18), (0.10, 0.45, 0.48), (0.93, 0.88, 0.75), (0.72, 0.32, 0.15),
          (0.40, 0.18, 0.42), (0.25, 0.25, 0.28), (0.80, 0.45, 0.40), (0.35, 0.50, 0.22), (0.95, 0.60, 0.15)]
WALNUT = (0.36, 0.21, 0.12)


def _spine(c, x, base, w, h, col, rng, lean=0.0):
    """One book seen from the spine: shaded cloth, gold bands, a title plate, a lighter top edge."""
    if lean:
        pts = [(x - w / 2, base), (x + w / 2, base), (x + w / 2 + lean * h, base + h), (x - w / 2 + lean * h, base + h)]
        _hpoly(c, pts, mix(col, WHITE, 0.12), scale(col, 0.62), 0.04)
        return
    craft.hshade_box(c, x, base + h / 2, w, h, mix(col, WHITE, 0.10), scale(col, 0.60), r=0.003)
    c.rect(x, base + h - 0.018, w * 0.9, 0.007, GOLD, lift=0, alpha=0.85)
    c.rect(x, base + 0.02, w * 0.9, 0.007, GOLD, lift=0, alpha=0.85)
    if rng.random() < 0.7:
        c.rect(x, base + h * 0.55, w * 0.55, h * 0.22, mix(col, WHITE, 0.7) if rng.random() < 0.6 else scale(col, 0.4), lift=0, alpha=0.9)
        c.rect(x, base + h * 0.55, w * 0.38, 0.004, scale(col, 0.4), lift=0, alpha=0.7)
    c.rect(x - w * 0.3, base + h / 2, w * 0.1, h * 0.96, WHITE, lift=0, alpha=0.14)


@sprop("rf_bookshelf", aspect=1.0, fill=1.0)
def rf_bookshelf(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.1)
    c.rect(0.0, 0.5, 1.0, 1.0, scale(WALNUT, 0.6), lift=0.08)                          # back panel
    shelves = (0.10, 0.37, 0.64)
    for si, sv in enumerate(shelves):
        x = -0.455
        top = sv + 0.22
        while x < 0.43:
            r = rng.random()
            if r < 0.07:                                                                  # a gap with a small decor item
                _fruit(c, x + 0.05, sv + 0.045, 0.045, rng.choice([(0.25, 0.5, 0.55), (0.85, 0.55, 0.2)]), 0.6)
                x += 0.12
                continue
            w, h = rng.uniform(0.032, 0.062), rng.uniform(0.15, 0.245)
            lean = 0.0
            if r > 0.92 and x < 0.30:
                lean = 0.18
            _spine(c, x + w / 2, sv + 0.016, w, h, rng.choice(SPINES), rng, lean)
            x += w + 0.002 + (h * lean * 0.5 if lean else 0.0)
        craft.hshade_box(c, 0.0, sv, 1.0, 0.032, scale(WALNUT, 1.25), scale(WALNUT, 0.7))
        c.rect(0.0, sv + 0.012, 1.0, 0.005, scale(WALNUT, 1.7), lift=0, alpha=0.5)
        c.rect(0.0, sv - 0.03, 0.94, 0.03, BLACK, lift=0, alpha=0.18)
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.49, 0.5, 0.045, 1.0, scale(WALNUT, 1.2), scale(WALNUT, 0.55))
    craft.hshade_box(c, 0.0, 0.93, 1.06, 0.06, scale(WALNUT, 1.3), scale(WALNUT, 0.7), r=0.008)
    c.rect(0.0, 0.962, 1.07, 0.008, scale(WALNUT, 1.8), lift=0, alpha=0.55)
    craft.hshade_box(c, 0.0, 0.03, 1.02, 0.06, scale(WALNUT, 1.0), scale(WALNUT, 0.5))
    soft_disc(c, -0.3, 0.55, 0.25, 0.4, (1.0, 0.85, 0.55), 0.12, 1.3, add=True)


@sprop("rf_book_stack", aspect=1.25, fill=0.8)
def rf_book_stack(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.16)
    v = 0.02
    cols = [rng.choice(SPINES) for _ in range(5)]
    for i, col in enumerate(cols):
        w = rng.uniform(0.74, 0.96)
        h = rng.uniform(0.07, 0.1)
        u = rng.uniform(-0.06, 0.06)
        c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + 0.12, v + h + 0.05), (u - w / 2 + 0.12, v + h + 0.05)], scale(col, 1.15), lift=0.05)
        craft.hshade_box(c, u, v + h / 2, w, h, mix(col, WHITE, 0.08), scale(col, 0.6), r=0.008)
        c.rect(u + w / 2 + 0.02, v + h / 2 + 0.01, 0.02, h * 0.85, (0.95, 0.9, 0.78), lift=0, alpha=0.9)        # page block
        c.rect(u, v + h * 0.55, w * 0.6, h * 0.22, GOLD, lift=0, alpha=0.8)
        c.line(u - w / 2 + 0.04, v + h * 0.88, u + w / 2 - 0.04, v + h * 0.88, 0.007, GOLD, 0.8)
        v += h * 0.98
    # a teacup with steam on top
    c.ellipse(0.0, v + 0.015, 0.11, 0.04, (0.9, 0.9, 0.88), lift=0)
    craft.hshade_box(c, 0.0, v + 0.06, 0.16, 0.09, (0.98, 0.97, 0.94), (0.72, 0.7, 0.68), r=0.03)
    c.ellipse(0.0, v + 0.105, 0.08, 0.03, (0.45, 0.25, 0.12), lift=0.1)
    craft.arc(c, 0.095, v + 0.06, 0.04, 0.04, -70, 70, 0.014, (0.95, 0.94, 0.9), 1.0, 6)
    craft.steam(c, 0.0, v + 0.13, 0.22, 0.03, 2, 0.20)
    soft_disc(c, -0.25, v - 0.02, 0.4, 0.06, WHITE, 0.2, 1.3, add=True)


@sprop("rf_armchair", aspect=1.0, fill=1.0)
def rf_armchair(c, color):
    rng = c.rng
    col = color if isinstance(color, tuple) else (0.15, 0.42, 0.42)
    ao(c, 0.0, 0.0, 0.95, 0.16)
    for sgn in (-1, 1):                                                                # tapered wooden legs
        c.poly([(sgn * 0.38 - 0.03, 0.12), (sgn * 0.38 + 0.03, 0.12), (sgn * 0.40 + 0.015, 0.0), (sgn * 0.40 - 0.015, 0.0)], scale(WOOD, 0.7), lift=0.05)
    craft.hshade_box(c, 0.0, 0.70, 0.78, 0.60, mix(col, WHITE, 0.08), scale(col, 0.62), r=0.12)         # back
    for rr in range(3):                                                                # button tufting
        for cc in range(4):
            c.ellipse(-0.27 + cc * 0.18 + (rr % 2) * 0.09, 0.60 + rr * 0.11, 0.012, 0.012, scale(col, 0.35), lift=0)
            c.line(-0.27 + cc * 0.18 + (rr % 2) * 0.09, 0.60 + rr * 0.11, -0.27 + cc * 0.18 + (rr % 2) * 0.09 + 0.07, 0.60 + rr * 0.11 + 0.05, 0.005, scale(col, 0.5), 0.35)
    craft.hshade_box(c, 0.0, 0.26, 0.96, 0.24, mix(col, WHITE, 0.1), scale(col, 0.62), r=0.06)           # seat front
    c.poly([(-0.44, 0.38), (0.44, 0.38), (0.50, 0.46), (-0.38, 0.46)], mix(col, WHITE, 0.2), lift=0.05)
    craft.hshade_box(c, 0.0, 0.40, 0.84, 0.10, mix(col, WHITE, 0.16), scale(col, 0.66), r=0.04)         # seat cushion
    c.line(-0.4, 0.352, 0.4, 0.352, 0.008, scale(col, 0.4), 0.6)
    for sgn in (-1, 1):                                                                # arms
        craft.hshade_box(c, sgn * 0.47, 0.34, 0.16, 0.40, mix(col, WHITE, 0.06) if sgn < 0 else scale(col, 0.72), scale(col, 0.55), r=0.07)
        c.ellipse(sgn * 0.47, 0.54, 0.08, 0.035, mix(col, WHITE, 0.15), lift=0)
    pc = (0.93, 0.74, 0.25)                                                            # throw pillow
    c.poly([(-0.20, 0.50), (-0.05, 0.60), (-0.15, 0.78), (-0.31, 0.67)], pc, lift=0.1)
    c.line(-0.2, 0.52, -0.2, 0.7, 0.01, (0.8, 0.5, 0.15), 0.5)
    soft_disc(c, -0.2, 0.74, 0.18, 0.2, WHITE, 0.14, 1.3, add=True)


@sprop("rf_floor_lamp", aspect=0.32, fill=1.0)
def rf_floor_lamp(c, color):
    ao(c, 0.0, 0.0, 0.3, 0.05)
    c.ellipse(0.0, 0.012, 0.11, 0.11 * TILT, (0.2, 0.15, 0.1), lift=0.1)
    craft.hshade_box(c, 0.0, 0.40, 0.022, 0.78, (0.85, 0.65, 0.35), (0.45, 0.3, 0.12))
    c.poly([(-0.16, 0.74), (0.16, 0.74), (0.10, 0.96), (-0.10, 0.96)], (0.98, 0.86, 0.60), lift=0.15)
    c.ellipse(0.0, 0.96, 0.10, 0.03, (1.0, 0.95, 0.75), lift=0)
    soft_disc(c, 0.0, 0.85, 0.2, 0.16, (1.0, 0.85, 0.5), 0.8, 1.2, add=True)
    soft_disc(c, 0.0, 0.74, 0.12, 0.04, (1.0, 0.9, 0.6), 0.8, 1.2, add=True)


@niche("bookstore", "Bookstore", subjects=("rf_bookshelf",),
       strong=("bookstore", "book store", "bookshop", "book shop", "books", "library", "novels", "kitab ki dukaan", "kitabein", "kitab", "किताब", "किताबें",
               "पुस्तकालय", "बुक स्टोर", "पुस्तक"),
       weak=("reading", "publisher", "stationery", "literature", "author", "bestseller"), accent="#8e5b3a", mood="warm", group="retail")
def bookstore(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.55)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        for col_i in range(8):                                                               # wall-to-wall shelving, rows of spines
            bu = -1.2 + col_i * 0.62
            for row, v in enumerate((0.10, 0.25, 0.40, 0.55)):
                x = bu - 0.28
                while x < bu + 0.28:
                    w, h = S.rng.uniform(0.016, 0.034), S.rng.uniform(0.095, 0.125)
                    S.rect(x + w / 2, v + 0.125 - h / 2, w, h, scale(S.rng.choice(SPINES), k), lift=0.0)
                    x += w + 0.002
                S.rect(bu, v + 0.132, 0.58, 0.012, scale(WALNUT, 0.9 * k), lift=0.0)
            S.rect(bu + 0.30, 0.34, 0.016, 0.62, scale(WALNUT, 0.8 * k), lift=0.0)
        for u in (0.45, 1.1, 1.75):                                                          # warm pendants over the aisles
            S.pendant(u, -0.1, 0.14 if u == 1.1 else 0.10, (1.0, 0.8, 0.45))
        S.bokeh(8, 0.0, 0.05, 2.0, 0.55, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.4)], 0.01, 0.035, 0.3)
        S.floor(0.62, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.62, 5.0, 2.6, mix(P.surface, WALNUT, 0.3), plank=0.12, grain=0.4)
    S.rect(1.0, 0.62, 8.0, 0.008, scale(P.surface, 0.4), lift=0.0)
    _floor_glow(S, 1.05, 0.82, 1.1, 0.18, (1.0, 0.82, 0.5), 0.40 if dk else 0.22)
    rug = mix(P.accent_dark, (0.45, 0.12, 0.12), 0.4)
    S.poly([(0.42, 0.85), (1.86, 0.85), (1.98, 1.03), (0.30, 1.03)], scale(rug, 0.7))
    S.poly([(0.49, 0.875), (1.79, 0.875), (1.90, 1.0), (0.38, 1.0)], mix(rug, GOLD, 0.35))
    S.poly([(0.53, 0.885), (1.75, 0.885), (1.85, 0.99), (0.43, 0.99)], rug)
    S.put("rf_floor_lamp", 1.30, 0.84, 0.50)
    S.put("rf_bookshelf", 0.88, 0.88, 0.58)
    S.mark_subject("rf_bookshelf", 0.78, 0.40, 0.98, 0.62)
    S.put("rf_armchair", 1.56, 0.97, 0.34, color=mix((0.15, 0.42, 0.42), P.accent, 0.12))
    S.put("rf_book_stack", 1.14, 1.0, 0.18)
    S.glow(1.30, 0.38, 0.55, (1.0, 0.82, 0.48), 0.40 if dk else 0.28)
    S.soft(1.30, 0.8, 0.6, 0.12, (1.0, 0.82, 0.48), 0.30, 1.5, add=True)
    S.focus("detail", 0.90, 0.62)
    with S.near(16.0):
        S.circle(0.50, 0.99, 0.06, mix(P.accent, WHITE, 0.2), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.18, 0.07, (1.0, 0.85, 0.5), alpha=0.3, lift=0, soft=6.0)


# ================================================================================================ FLORIST
LEAFG = [(0.18, 0.46, 0.22), (0.26, 0.55, 0.26), (0.14, 0.38, 0.24), (0.36, 0.60, 0.30)]
EUCA = [(0.52, 0.68, 0.60), (0.45, 0.62, 0.56), (0.60, 0.74, 0.66)]
KRAFT = (0.80, 0.64, 0.44)


def _rose(c, u, v, r, col):
    """A rose seen from above at an angle: dark base, a ring of overlapping outer petals, tighter inner petals and a curled bud."""
    c.ellipse(u, v, r, r * 0.84, scale(col, 0.48), lift=0)
    for k in range(6):                                                                     # outer petals
        a = 2 * math.pi * k / 6 + 0.4
        pu, pv = u + math.cos(a) * r * 0.52, v + math.sin(a) * r * 0.42
        c.ellipse(pu, pv, r * 0.48, r * 0.40, mix(col, WHITE, 0.04 + 0.05 * (k % 2)), angle=math.degrees(a) + 90, lift=0.14)
        craft.arc(c, pu, pv + r * 0.02, r * 0.42, r * 0.34, 20, 160, r * 0.045, mix(col, WHITE, 0.30), 0.65, 4)
    for k in range(4):                                                                     # inner petals
        a = 2 * math.pi * k / 4 + 1.1
        c.ellipse(u + math.cos(a) * r * 0.26, v + math.sin(a) * r * 0.21 + r * 0.04, r * 0.32, r * 0.26, mix(col, WHITE, 0.14 + 0.04 * k), angle=math.degrees(a) + 90, lift=0.14)
        craft.arc(c, u + math.cos(a) * r * 0.26, v + math.sin(a) * r * 0.21 + r * 0.06, r * 0.26, r * 0.2, 20, 160, r * 0.04, mix(col, WHITE, 0.4), 0.6, 4)
    c.ellipse(u, v + r * 0.08, r * 0.2, r * 0.16, scale(col, 0.78), lift=0.12)
    craft.arc(c, u, v + r * 0.1, r * 0.14, r * 0.11, 200, 340, r * 0.05, scale(col, 0.5), 0.8, 4)
    c.ellipse(u - r * 0.38, v + r * 0.42, r * 0.24, r * 0.12, WHITE, angle=22, alpha=0.38, lift=0)


def _daisy(c, u, v, r, col=(0.98, 0.97, 0.95)):
    for k in range(11):
        a = 2 * math.pi * k / 11
        c.ellipse(u + math.cos(a) * r * 0.55, v + math.sin(a) * r * 0.44, r * 0.44, r * 0.15, col if k % 2 else scale(col, 0.94), angle=math.degrees(a), lift=0.08)
    c.ellipse(u, v, r * 0.28, r * 0.23, (0.95, 0.72, 0.10), lift=0.12)
    c.ellipse(u - r * 0.05, v + r * 0.05, r * 0.14, r * 0.1, (1.0, 0.88, 0.4), lift=0, alpha=0.8)


def _sunflower(c, u, v, r):
    for k in range(16):
        a = 2 * math.pi * k / 16
        c.ellipse(u + math.cos(a) * r * 0.66, v + math.sin(a) * r * 0.52, r * 0.42, r * 0.13, (0.98, 0.78 + 0.08 * (k % 2), 0.08), angle=math.degrees(a), lift=0.1)
    c.ellipse(u, v, r * 0.44, r * 0.36, (0.30, 0.17, 0.08), lift=0.1)
    c.ellipse(u, v + r * 0.03, r * 0.34, r * 0.27, (0.42, 0.25, 0.10), lift=0.1)
    for k in range(10):
        a = 2.4 * k
        c.ellipse(u + math.cos(a) * r * 0.2 * (k / 10.0 + 0.2), v + math.sin(a) * r * 0.16 * (k / 10.0 + 0.2), r * 0.035, r * 0.03, (0.65, 0.45, 0.2), lift=0, alpha=0.8)


def _tulip(c, u, v, r, col):
    c.ellipse(u - r * 0.30, v, r * 0.46, r * 0.78, scale(col, 0.82), angle=12, lift=0.1)
    c.ellipse(u + r * 0.30, v, r * 0.46, r * 0.78, scale(col, 0.72), angle=-12, lift=0.1)
    c.ellipse(u, v + r * 0.04, r * 0.48, r * 0.82, col, lift=0.18)
    c.ellipse(u - r * 0.15, v + r * 0.3, r * 0.12, r * 0.38, WHITE, alpha=0.30, lift=0)
    c.line(u, v - r * 0.5, u, v + r * 0.6, r * 0.04, scale(col, 0.6), 0.35)


def _stem(c, u0, v0, u1, v1, w=0.014):
    c.line(u0, v0, u1, v1, w, (0.20, 0.45, 0.20), 1.0)
    c.line(u0 - w * 0.2, v0, u1 - w * 0.2, v1, w * 0.35, (0.35, 0.62, 0.30), 0.7)


def _bloom_dome(c, cx, base_v, spread, height, n, kinds, rng, rmin, rmax, stem_to):
    """A domed arrangement: stems + greenery first (back), then flower heads sorted back to front."""
    pts = []
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(rng.random())
        x = cx + math.cos(ang) * spread * rr
        depth = math.sin(ang) * rr                                   # -1 back ... +1 front
        v = base_v + height * (1.0 - (rr ** 1.8) * 0.55) + depth * -0.03 + rng.uniform(-0.02, 0.02)
        pts.append((v, x, depth))
    pts.sort(key=lambda p: -p[0])
    for v, x, d in pts:
        _stem(c, x * 0.5 + cx * 0.5, stem_to, x, v - 0.02)
    for _ in range(max(8, int(n * 1.2))):                           # greenery between the blooms
        x = cx + rng.uniform(-spread * 1.05, spread * 1.05)
        v = base_v + height * rng.uniform(0.35, 0.95) - abs(x - cx) * 0.25
        if rng.random() < 0.5:
            _leaf(c, x, v, rng.uniform(0.14, 0.24), 90 + (x - cx) / spread * 55 + rng.uniform(-18, 18), rng.choice(LEAFG), 0.42)
        else:
            c.ellipse(x, v, 0.04, 0.032, rng.choice(EUCA), lift=0.1)
    for v, x, d in pts:
        kind = kinds[rng.randrange(len(kinds))]
        r = rng.uniform(rmin, rmax) * (1.0 + 0.1 * d)
        if kind[0] == "rose":
            _rose(c, x, v, r, kind[1])
        elif kind[0] == "daisy":
            _daisy(c, x, v, r * 0.9)
        elif kind[0] == "tulip":
            _tulip(c, x, v, r * 0.9, kind[1])
        else:
            _sunflower(c, x, v, r * 1.1)


def _mix_kinds(P):
    acc = _pal(P, "accent", (0.91, 0.26, 0.58))
    return [("rose", acc), ("rose", mix(acc, WHITE, 0.45)), ("rose", (0.98, 0.72, 0.62)), ("daisy", None), ("tulip", mix(acc, (1.0, 0.8, 0.2), 0.25)),
            ("rose", mix(acc, (0.55, 0.15, 0.3), 0.4))]


@sprop("rf_flower_bucket", aspect=1.0, fill=1.0)
def rf_flower_bucket(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.13)
    steel = (0.80, 0.83, 0.87)
    c.ellipse(0.0, 0.34, 0.31, 0.31 * TILT * 0.9, scale(steel, 0.35), lift=0)
    _bloom_dome(c, 0.0, 0.30, 0.40, 0.50, 20, _mix_kinds(color), rng, 0.085, 0.115, 0.34)
    _hpoly(c, [(-0.31, 0.34), (0.31, 0.34), (0.25, 0.02), (-0.25, 0.02)], mix(steel, WHITE, 0.2), scale(steel, 0.50), 0.05, power=1.1)
    for vv in (0.10, 0.19, 0.28):
        c.line(-0.30 + (0.34 - vv) * 0.0 + (0.34 - vv) * 0.05, vv, 0.30 - (0.34 - vv) * 0.05, vv, 0.008, BLACK, 0.12)
        c.line(-0.30 + (0.34 - vv) * 0.05, vv + 0.008, 0.30 - (0.34 - vv) * 0.05, vv + 0.008, 0.005, WHITE, 0.25)
    craft.arc(c, 0.0, 0.34, 0.31, 0.31 * TILT * 0.9, 180, 360, 0.016, mix(steel, WHITE, 0.4), 1.0, 10)
    c.ellipse(0.04, 0.17, 0.055, 0.04, (0.97, 0.95, 0.88), lift=0.05)                  # tag
    c.line(0.0, 0.17, 0.08, 0.17, 0.006, (0.3, 0.3, 0.3), 0.7)
    soft_disc(c, -0.16, 0.20, 0.06, 0.14, WHITE, 0.45, 1.2, add=True)
    soft_disc(c, 0.26, 0.18, 0.05, 0.15, BLACK, 0.3, 1.3)


@sprop("rf_wrapped_bouquet", aspect=0.9, fill=1.0)
def rf_wrapped_bouquet(c, color):
    P = color
    acc = _pal(P, "accent", (0.91, 0.26, 0.58))
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.10)
    c.line(-0.08, 0.3, -0.12, 0.62, 0.016, (0.2, 0.45, 0.2), 1.0)
    _bloom_dome(c, 0.0, 0.48, 0.34, 0.38, 11, [("rose", acc), ("rose", mix(acc, WHITE, 0.5)), ("daisy", None), ("rose", (0.98, 0.74, 0.60)),
                                                ("tulip", mix(acc, (1.0, 0.85, 0.3), 0.3))], rng, 0.08, 0.11, 0.5)
    # kraft paper cone with folds, a sheer inner layer and a ribbon bow
    _hpoly(c, [(-0.40, 0.56), (0.40, 0.56), (0.07, 0.015), (-0.07, 0.015)], mix(KRAFT, WHITE, 0.12), scale(KRAFT, 0.62), 0.06)
    for k in range(5):
        x0 = -0.34 + k * 0.17
        c.line(x0, 0.54, x0 * 0.2, 0.04, 0.006, scale(KRAFT, 0.55), 0.4)
    c.poly([(-0.40, 0.56), (-0.12, 0.60), (0.10, 0.56), (0.40, 0.56), (0.2, 0.48), (-0.2, 0.48)], mix(KRAFT, WHITE, 0.45), alpha=0.9, lift=0.08)
    c.poly([(-0.40, 0.56), (-0.2, 0.48), (-0.12, 0.60)], scale(KRAFT, 0.8), alpha=0.6, lift=0)
    c.rect(0.0, 0.33, 0.30, 0.04, acc, lift=0.12)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.11, 0.345, 0.085, 0.055, acc, angle=sgn * -20, lift=0.15)
        c.ellipse(sgn * 0.11, 0.345, 0.05, 0.028, scale(acc, 0.65), angle=sgn * -20, lift=0)
        c.line(sgn * 0.03, 0.31, sgn * 0.10, 0.12, 0.028, mix(acc, WHITE, 0.1), 1.0)
    c.ellipse(0.0, 0.33, 0.04, 0.034, scale(acc, 0.8), lift=0.2)
    soft_disc(c, -0.2, 0.36, 0.14, 0.2, WHITE, 0.25, 1.3, add=True)
    soft_disc(c, 0.28, 0.30, 0.08, 0.25, BLACK, 0.2, 1.4)


@sprop("rf_glass_vase", aspect=0.78, fill=1.0)
def rf_glass_vase(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.08)
    c.ellipse(0.0, 0.03, 0.15, 0.15 * TILT, (0.78, 0.86, 0.88), alpha=0.7, lift=0)
    for k in range(7):                                                                   # stems seen through the glass
        x = -0.07 + k * 0.025
        c.line(x, 0.05, x * 2.8 + (k - 3) * 0.02, 0.42, 0.012, (0.22, 0.50, 0.22), 1.0)
    c.poly([(-0.16, 0.42), (0.16, 0.42), (0.14, 0.04), (-0.14, 0.04)], (0.55, 0.82, 0.88), alpha=0.35, lift=0.1)               # water
    c.poly([(-0.18, 0.48), (0.18, 0.48), (0.17, 0.06), (-0.17, 0.06)], (0.88, 0.95, 0.97), alpha=0.22, lift=0.1)               # glass body
    c.line(-0.165, 0.46, -0.15, 0.08, 0.012, WHITE, 0.55)
    c.line(0.15, 0.44, 0.14, 0.10, 0.008, WHITE, 0.3)
    c.ellipse(0.0, 0.48, 0.18, 0.18 * 0.28, (0.9, 0.96, 0.98), alpha=0.5, lift=0)
    _bloom_dome(c, 0.0, 0.56, 0.30, 0.38, 7, [("sun", None), ("sun", None), ("daisy", None), ("tulip", (0.97, 0.78, 0.25))], rng, 0.09, 0.115, 0.46)
    craft.arc(c, 0.0, 0.48, 0.18, 0.18 * 0.28, 180, 360, 0.01, WHITE, 0.6, 8)
    soft_disc(c, -0.10, 0.28, 0.03, 0.16, WHITE, 0.4, 1.2, add=True)


@sprop("rf_potted_fern", aspect=0.9, fill=0.9)
def rf_potted_fern(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.11)
    terracotta = (0.80, 0.42, 0.26)
    for k in range(14):
        _leaf(c, rng.uniform(-0.06, 0.06), 0.34, rng.uniform(0.34, 0.5), rng.uniform(25, 155), rng.choice(LEAFG), 0.28)
    craft.hshade_box(c, 0.0, 0.17, 0.46, 0.34, terracotta, scale(terracotta, 0.55), r=0.02)
    c.rect(0.0, 0.34, 0.54, 0.07, mix(terracotta, WHITE, 0.08), r=0.012, lift=0.1)
    c.rect(0.0, 0.30, 0.50, 0.012, BLACK, lift=0, alpha=0.25)
    soft_disc(c, -0.12, 0.2, 0.05, 0.1, WHITE, 0.25, 1.2, add=True)


@niche("florist", "Florist", subjects=("rf_flower_bucket",),
       strong=("florist", "flower shop", "flowers", "bouquet", "floral", "flower delivery", "phool", "phoolwala", "phool ki dukaan", "फूल", "फूलों की दुकान",
               "गुलदस्ता", "फ्लोरिस्ट", "roses"),
       weak=("garden", "wedding decor", "plants", "petals", "bloom", "nursery"), accent="#e84393", mood="light", group="retail")
def florist(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        brick = scale(mix(P.paper, P.wall_bot, 0.4), 1.0)
        for row in range(11):                                                                # whitewashed brick
            for i in range(30):
                u = -1.5 + i * 0.13 + (0.065 if row % 2 else 0.0)
                S.rect(u, 0.02 + row * 0.056, 0.12, 0.05, scale(brick, 0.95 + 0.07 * S.rng.random()), lift=0.0, alpha=0.8)
        S.window(1.55, 0.27, 0.46, 0.40, (0.72, 0.88, 0.97), (0.95, 0.98, 1.0), (0.97, 0.97, 0.97))
        for u in (0.25, 0.75, 1.15, 1.95):                                                   # hanging plants
            S.line(u, -0.1, u, 0.12, 0.004, scale((0.4, 0.3, 0.2), k))
            for j in range(6):
                S.ellipse(u + S.rng.uniform(-0.07, 0.07), 0.14 + S.rng.uniform(0, 0.12), S.rng.uniform(0.04, 0.07), S.rng.uniform(0.03, 0.06),
                          scale(LEAFG[j % 4], k), lift=0.0)
            S.rect(u, 0.12, 0.07, 0.04, scale((0.8, 0.45, 0.3), k), r=0.01, lift=0.0)
        S.rect(0.55, 0.46, 1.2, 0.014, scale(WOOD, 0.9 * k), lift=0.0)                       # a wall shelf with pots
        for j in range(6):
            S.rect(0.1 + j * 0.2, 0.42, 0.06, 0.06, scale(rf_c(j), k), lift=0.0)
            S.ellipse(0.1 + j * 0.2, 0.37, 0.05, 0.04, scale(LEAFG[j % 4], k), lift=0.0)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [(1.0, 0.95, 0.8), (1.0, 0.85, 0.85)], 0.01, 0.035, 0.25)
        S.floor(0.62, P.floor_top, P.floor_bot)
    S.light_shaft(1.25, 0.12, 1.85, 0.12, 1.55, 1.02, 0.55, 1.02, (1.0, 0.97, 0.88), 0.10 if not dk else 0.06)
    S.wood(-3.0, 0.62, 5.0, 2.6, mix(P.surface, WHITE, 0.35), plank=0.15, grain=0.3)
    S.rect(1.0, 0.62, 8.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    _floor_glow(S, 1.1, 0.80, 1.1, 0.17, (1.0, 0.97, 0.88), 0.4 if dk else 0.2)
    S.put("rf_wrapped_bouquet", 0.70, 0.93, 0.40, color=P)
    S.put("rf_glass_vase", 1.56, 0.88, 0.42)
    S.put("rf_flower_bucket", 1.10, 0.95, 0.52, color=P)
    S.mark_subject("rf_flower_bucket", 1.0, 0.50, 1.2, 0.86)
    S.put("rf_potted_fern", 1.40, 1.0, 0.16)
    S.focus("detail", 1.10, 0.62)
    with S.near(16.0):
        S.circle(0.50, 0.15, 0.06, mix(P.accent, WHITE, 0.4), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.76, 0.98, 0.07, (0.5, 0.75, 0.4), alpha=0.35, lift=0, soft=6.0)


def rf_c(j):
    return [(0.80, 0.45, 0.30), (0.92, 0.92, 0.9), (0.55, 0.62, 0.7), (0.80, 0.45, 0.30), (0.95, 0.75, 0.3), (0.92, 0.92, 0.9)][j % 6]


# ================================================================================================ TOY STORE
FUR = (0.80, 0.55, 0.32)
TOYC = [(0.92, 0.25, 0.25), (0.20, 0.55, 0.90), (0.98, 0.78, 0.15), (0.25, 0.72, 0.38), (0.95, 0.5, 0.15), (0.6, 0.35, 0.78)]


def _fur(c, rng, u, v, a, b, n, col):
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(rng.random()) * 0.96
        x, y = u + math.cos(ang) * a * rr, v + math.sin(ang) * b * rr
        c.line(x, y, x + math.cos(ang) * 0.025, y + math.sin(ang) * 0.025, 0.006, mix(col, WHITE if rng.random() < 0.5 else BLACK, 0.3), 0.30)


@sprop("rf_teddy", aspect=0.95, fill=1.0)
def rf_teddy(c, color):
    P = color
    acc = _pal(P, "accent", (0.95, 0.77, 0.06))
    rng = c.rng
    cream = (0.96, 0.84, 0.64)
    ao(c, 0.0, 0.0, 0.95, 0.13)
    for sgn in (-1, 1):                                                                    # feet with pads
        x = sgn * 0.25
        c.ellipse(x, 0.12, 0.17, 0.12, scale(FUR, 0.55), lift=0)
        c.ellipse(x, 0.13, 0.165, 0.115, scale(FUR, 1.0 if sgn < 0 else 0.85), lift=0.16)
        c.ellipse(x, 0.12, 0.085, 0.07, (0.93, 0.68, 0.62), lift=0.1)
        for k in range(3):
            c.ellipse(x + (k - 1) * 0.04, 0.17, 0.016, 0.014, (0.93, 0.68, 0.62), lift=0)
    c.ellipse(0.0, 0.36, 0.34, 0.33, scale(FUR, 0.52), lift=0)
    c.ellipse(-0.01, 0.37, 0.33, 0.32, FUR, lift=0.16)
    c.ellipse(0.0, 0.34, 0.21, 0.23, cream, lift=0.12)
    _fur(c, rng, 0.0, 0.36, 0.32, 0.31, 40, FUR)
    for sgn in (-1, 1):                                                                    # arms
        c.ellipse(sgn * 0.37, 0.44, 0.115, 0.215, scale(FUR, 0.55), angle=sgn * -22, lift=0)
        c.ellipse(sgn * 0.365, 0.45, 0.11, 0.205, FUR if sgn < 0 else scale(FUR, 0.86), angle=sgn * -22, lift=0.16)
        c.ellipse(sgn * 0.405, 0.30, 0.07, 0.06, cream, lift=0.1)
    # heart patch on the belly
    c.ellipse(-0.035, 0.36, 0.045, 0.045, acc, lift=0.1)
    c.ellipse(0.035, 0.36, 0.045, 0.045, acc, lift=0.1)
    c.poly([(-0.078, 0.345), (0.078, 0.345), (0.0, 0.26)], acc, lift=0.1)
    # head
    c.ellipse(0.0, 0.745, 0.27, 0.245, scale(FUR, 0.5), lift=0)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.20, 0.93, 0.095, 0.095, scale(FUR, 0.6), lift=0)
        c.ellipse(sgn * 0.20, 0.93, 0.085, 0.085, FUR if sgn < 0 else scale(FUR, 0.88), lift=0.14)
        c.ellipse(sgn * 0.20, 0.925, 0.05, 0.05, (0.93, 0.66, 0.6), lift=0.05)
    c.ellipse(-0.005, 0.755, 0.265, 0.24, FUR, lift=0.16)
    _fur(c, rng, 0.0, 0.75, 0.25, 0.22, 34, FUR)
    c.ellipse(0.0, 0.70, 0.12, 0.09, scale(cream, 0.86), lift=0)
    c.ellipse(0.0, 0.705, 0.115, 0.085, cream, lift=0.14)
    c.ellipse(0.0, 0.735, 0.04, 0.028, (0.18, 0.1, 0.07), lift=0.1)
    c.ellipse(-0.012, 0.742, 0.012, 0.007, WHITE, alpha=0.7, lift=0)
    c.line(0.0, 0.71, 0.0, 0.675, 0.008, (0.25, 0.14, 0.09), 0.9)
    craft.arc(c, -0.03, 0.675, 0.03, 0.02, 180, 360, 0.007, (0.25, 0.14, 0.09), 0.9, 5)
    craft.arc(c, 0.03, 0.675, 0.03, 0.02, 180, 360, 0.007, (0.25, 0.14, 0.09), 0.9, 5)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.095, 0.80, 0.027, 0.03, (0.09, 0.06, 0.05), lift=0.1)
        c.ellipse(sgn * 0.095 - 0.008, 0.81, 0.009, 0.009, WHITE, lift=0)
    # bow tie
    for sgn in (-1, 1):
        c.poly([(0.0, 0.535), (sgn * 0.13, 0.575), (sgn * 0.13, 0.495)], scale(acc, 1.0 if sgn < 0 else 0.82), lift=0.12)
    c.ellipse(0.0, 0.535, 0.03, 0.03, scale(acc, 0.7), lift=0.15)
    soft_disc(c, -0.12, 0.55, 0.2, 0.3, WHITE, 0.15, 1.3, add=True)
    soft_disc(c, 0.2, 0.28, 0.16, 0.26, BLACK, 0.20, 1.4)


@sprop("rf_toy_blocks", aspect=1.05, fill=0.95)
def rf_toy_blocks(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.16)
    w = 0.30
    d = w * 0.32
    layout = [(-0.33, 0.0, 0, "A"), (0.0, 0.0, 1, "B"), (0.33, 0.0, 2, "C"), (-0.17, 0.30, 3, "1"), (0.17, 0.30, 4, "2"), (0.0, 0.60, 5, "")]
    for (u, v, ci, g) in layout:
        col = TOYC[ci]
        c.poly([(u + w / 2, v), (u + w / 2 + d, v + d * 0.8), (u + w / 2 + d, v + w + d * 0.8), (u + w / 2, v + w)], scale(col, 0.58), lift=0.05)
        c.poly([(u - w / 2, v + w), (u + w / 2, v + w), (u + w / 2 + d, v + w + d * 0.8), (u - w / 2 + d, v + w + d * 0.8)], mix(col, WHITE, 0.30), lift=0.05)
        craft.hshade_box(c, u, v + w / 2, w, w, mix(col, WHITE, 0.06), scale(col, 0.80), r=0.012)
        c.rect(u, v + w * 0.5, w * 0.78, w * 0.78, mix(col, WHITE, 0.55), r=0.02, lift=0.04, alpha=0.55)
        if g:
            c.text(g, u, v + w * 0.5, w * 0.46, scale(col, 0.55), 0.22)
        else:
            c.poly([(u + math.cos(math.radians(90 + 72 * k)) * w * (0.30 if k % 2 == 0 else 0.13) * 1.0, v + w * 0.5 + math.sin(math.radians(90 + 72 * k)) * w *
                     (0.30 if k % 2 == 0 else 0.13)) for k in range(5)], WHITE, lift=0) if False else c.ellipse(u, v + w * 0.5, w * 0.24, w * 0.24, WHITE, alpha=0.9, lift=0.05)
            c.ellipse(u, v + w * 0.5, w * 0.12, w * 0.12, col, lift=0.1)
        c.line(u - w / 2 + 0.004, v + 0.01, u - w / 2 + 0.004, v + w - 0.01, 0.008, WHITE, 0.35)
        soft_disc(c, u - w * 0.2, v + w * 0.8, w * 0.2, w * 0.15, WHITE, 0.25, 1.3, add=True)


@sprop("rf_toy_car", aspect=1.9, fill=1.0)
def rf_toy_car(c, color):
    P = color
    red = (0.90, 0.20, 0.18)
    ao(c, 0.0, 0.0, 2.0, 0.22)
    body = [(-1.0, 0.22), (-1.02, 0.46), (-0.80, 0.54), (-0.46, 0.60), (-0.34, 0.90), (0.30, 0.92), (0.56, 0.62), (0.90, 0.52), (1.02, 0.42), (1.0, 0.22)]
    _hpoly(c, body, mix(red, WHITE, 0.12), scale(red, 0.58), 0.10, power=1.1, smooth=2)
    _spoly(c, [(-0.30, 0.64), (-0.24, 0.84), (0.26, 0.86), (0.46, 0.64)], (0.62, 0.84, 0.95), 1, lift=0.15)
    c.line(0.08, 0.64, 0.08, 0.86, 0.025, red, 1.0)
    c.line(-0.30, 0.54, 0.95, 0.46, 0.014, scale(red, 0.5), 0.5)
    c.ellipse(-0.08, 0.40, 0.14, 0.14, WHITE, lift=0.08)                                    # race number roundel
    c.text("7", -0.08, 0.40, 0.16, red, 0.2)
    c.rect(-1.0, 0.30, 0.07, 0.10, (0.88, 0.88, 0.9), lift=0.1)
    c.ellipse(0.96, 0.43, 0.06, 0.055, (1.0, 0.92, 0.5), lift=0.1)
    for x in (-0.58, 0.58):
        c.ellipse(x, 0.24, 0.27, 0.27, (0.10, 0.10, 0.12), lift=0)
        c.ellipse(x, 0.245, 0.25, 0.25, (0.17, 0.17, 0.19), lift=0.1)
        c.ellipse(x, 0.245, 0.14, 0.14, (0.98, 0.80, 0.15), lift=0.15)
        c.ellipse(x, 0.245, 0.04, 0.04, scale((0.98, 0.8, 0.15), 0.6), lift=0)
        for k in range(5):
            a = 2 * math.pi * k / 5
            c.line(x, 0.245, x + math.cos(a) * 0.12, 0.245 + math.sin(a) * 0.12, 0.016, scale((0.98, 0.8, 0.15), 0.7), 0.8)
        c.ellipse(x - 0.07, 0.31, 0.06, 0.03, WHITE, alpha=0.35, lift=0)
    soft_disc(c, -0.55, 0.58, 0.35, 0.05, WHITE, 0.45, 1.2, 8, add=True)
    soft_disc(c, 0.7, 0.4, 0.2, 0.15, BLACK, 0.2, 1.4)


@sprop("rf_rocking_horse", aspect=1.35, fill=1.0)
def rf_rocking_horse(c, color):
    P = color
    acc = _pal(P, "accent", (0.95, 0.77, 0.06))
    rng = c.rng
    wood = (0.80, 0.55, 0.28)
    cream = (0.96, 0.92, 0.84)
    ao(c, 0.0, 0.0, 1.35, 0.16)
    craft.arc(c, 0.0, 0.20, 0.66, 0.17, 184, 356, 0.065, scale(wood, 0.75), 1.0, 16)
    craft.arc(c, 0.0, 0.215, 0.66, 0.17, 188, 352, 0.03, mix(wood, WHITE, 0.2), 0.9, 14)
    for (x0, x1, dark) in ((-0.30, -0.45, 0.78), (0.30, 0.46, 0.78), (-0.22, -0.30, 1.0), (0.22, 0.34, 1.0)):                      # legs
        _spoly(c, [(x0 - 0.05, 0.50), (x0 + 0.05, 0.50), (x1 + 0.03, 0.12), (x1 - 0.03, 0.12)], scale(cream, dark), 1, lift=0.08)
        c.ellipse(x1, 0.12, 0.045, 0.03, scale(wood, 0.5), lift=0)
    _spoly(c, [(-0.50, 0.55), (-0.40, 0.72), (-0.1, 0.78), (0.35, 0.74), (0.52, 0.62), (0.44, 0.44), (0.0, 0.40), (-0.42, 0.44)], cream, 2, lift=0.14)
    for _ in range(9):                                                                     # dapples
        c.ellipse(rng.uniform(-0.3, 0.36), rng.uniform(0.48, 0.68), rng.uniform(0.04, 0.07), rng.uniform(0.03, 0.05), (0.78, 0.74, 0.68), lift=0, alpha=0.6)
    _spoly(c, [(-0.52, 0.62), (-0.50, 0.92), (-0.30, 1.0), (-0.12, 0.96), (-0.15, 0.78), (-0.32, 0.58)], cream, 2, lift=0.14)         # neck + head
    _spoly(c, [(-0.80, 0.80), (-0.66, 0.96), (-0.45, 0.98), (-0.36, 0.86), (-0.60, 0.74)], cream, 2, lift=0.14)
    c.ellipse(-0.79, 0.80, 0.05, 0.04, (0.95, 0.7, 0.65), lift=0.1)
    c.ellipse(-0.57, 0.915, 0.02, 0.02, (0.1, 0.07, 0.05), lift=0.1)
    c.poly([(-0.48, 0.98), (-0.44, 1.07), (-0.38, 0.98)], scale(cream, 0.9), lift=0.1)
    for k in range(8):                                                                     # mane + tail
        t = k / 7.0
        _spoly(c, [(-0.30 + 0.1 * t, 0.99 - 0.30 * t), (-0.24 + 0.1 * t, 0.96 - 0.30 * t), (-0.16 + 0.12 * t, 0.86 - 0.30 * t)], scale(acc, 0.7 + 0.05 * (k % 3)), 0, lift=0.1)
    for k in range(6):
        c.line(0.50, 0.66, 0.66 + 0.02 * k, 0.50 - 0.06 * k, 0.02, scale(acc, 0.7 + 0.04 * k), 0.95)
    _spoly(c, [(-0.18, 0.76), (0.20, 0.76), (0.24, 0.70), (-0.22, 0.70)], acc, 1, lift=0.15)                                         # saddle
    c.line(-0.52, 0.86, -0.58, 0.96, 0.012, (0.2, 0.15, 0.1), 0.8)
    soft_disc(c, -0.25, 0.72, 0.2, 0.06, WHITE, 0.4, 1.2, add=True)


@niche("toy-store", "Toy store", subjects=("rf_teddy",),
       strong=("toy store", "toy shop", "toys", "toy", "teddy bear", "kids toys", "baby toys", "khilone", "khilauna", "khilono ki dukaan", "खिलौने", "खिलौना",
               "खिलौनों की दुकान", "playthings"),
       weak=("kids", "children", "games", "dolls", "puzzles", "playroom", "gifts"), accent="#f1c40f", mood="light", group="retail")
def toy_store(S):
    P = S.pal
    dk, k = _dark(S), _mood_k(S, 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        for i in range(24):                                                                    # bunting
            u = -1.2 + i * 0.16
            sag = 0.03 * math.sin(i * 0.5)
            S.poly([(u - 0.05, 0.06 + sag), (u + 0.05, 0.06 + sag), (u, 0.14 + sag)], scale(TOYC[i % len(TOYC)], k))
        S.rect(1.0, 0.06, 6.0, 0.006, scale(WHITE, k), lift=0.0)
        for cu in range(7):                                                                    # cubby shelving with toys
            bu = -0.9 + cu * 0.60
            for row, v in enumerate((0.27, 0.45)):
                S.rect(bu, v, 0.50, 0.16, scale(TOYC[(cu + row * 2) % len(TOYC)], k), lift=0.0)
                S.rect(bu, v + 0.012, 0.44, 0.13, scale(mix(P.paper, TOYC[(cu + row * 2) % len(TOYC)], 0.25), k), lift=0.0)
                S.circle(bu - 0.1, v + 0.04, 0.045, scale(TOYC[(cu + row + 1) % len(TOYC)], k), lift=0.0)
                S.rect(bu + 0.08, v + 0.045, 0.07, 0.07, scale(TOYC[(cu + row + 3) % len(TOYC)], k), lift=0.0)
        for u in (0.4, 1.1, 1.8):                                                              # round ceiling lights
            S.circle(u, 0.03, 0.05, scale(WHITE, k), lift=0.0)
            S.glow(u, 0.04, 0.55, (1.0, 0.98, 0.9), 0.4 if not dk else 0.5)
        S.bokeh(10, 0.0, 0.1, 2.0, 0.55, [(1.0, 0.4, 0.4), (0.4, 0.7, 1.0), (1.0, 0.85, 0.3), (0.5, 0.9, 0.5)], 0.015, 0.045, 0.3)
        S.floor(0.62, P.floor_top, P.floor_bot)
    # interlocking foam play mat
    cols = [mix(P.paper, c_, 0.55) if not dk else scale(c_, 0.35) for c_ in TOYC]
    n = 0
    for j in range(12):
        for i in range(34):
            S.rect(-3.0 + (i + 0.5) * 0.24, 0.62 + (j + 0.5) * 0.17, 0.244, 0.174, cols[(i * 2 + j * 3 + (i // 3)) % len(cols)], lift=0.0, soft=0.5)
            n += 1
    S.rect(1.0, 0.62, 8.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    _floor_glow(S, 1.1, 0.82, 1.1, 0.17, (1.0, 0.98, 0.9), 0.35 if dk else 0.16)
    S.put("rf_rocking_horse", 1.55, 0.84, 0.40, color=P)
    S.put("rf_toy_blocks", 0.70, 0.93, 0.30)
    S.put("rf_teddy", 1.10, 0.96, 0.50, color=P)
    S.mark_subject("rf_teddy", 0.98, 0.48, 1.22, 0.80)
    S.put("rf_toy_car", 1.36, 1.0, 0.11, color=P, framed=False)
    S.focus("detail", 1.10, 0.62)
    with S.near(16.0):
        S.circle(0.50, 0.12, 0.07, (1.0, 0.45, 0.45), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.97, 0.07, (0.4, 0.7, 1.0), alpha=0.35, lift=0, soft=6.0)
