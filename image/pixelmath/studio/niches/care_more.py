"""Care and personal-service niches: Ayurveda clinic, physiotherapy, skin clinic, eye clinic, optical store, mehendi artist, tattoo studio, pet shop."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, lerp_stops, mix, scale

WOOD = (0.64, 0.43, 0.25)
BRASS = (0.80, 0.58, 0.22)
GLASS = (0.90, 0.95, 0.97)
SKIN = (0.92, 0.72, 0.58)


# ------------------------------------------------------------------------------------------------ shared helpers
def _pal(color, name, default):
    """Props receive the palette through `color` (S.put(..., color=S.pal)); fall back to a default colour."""
    return getattr(color, name, default) if color is not None and not isinstance(color, tuple) else default


def _dark(S):
    return S.pal.mood == "dark"


def _chaikin(pts, n=2):
    for _ in range(n):
        out = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        pts = out
    return pts


def _fillpoly(c, px, color, alpha=1.0, shade=None):
    """Anti-aliased scanline polygon fill (fast, also for large or smoothed outlines)."""
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
        if all(len(sp) == 1 for sp in spans):
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


def _hpoly(c, pts, left, right, k=0.07, alpha=1.0, power=1.0, smooth=0):
    """Polygon (unit coordinates) shaded left-to-right (lit side `left`) and lightly top-to-bottom."""
    if smooth:
        pts = _chaikin(pts, smooth)
    if hasattr(c, "pt"):                                    # rotated drawing frame (see _Rot)
        pts = [c.pt(u, v) for u, v in pts]
        c = c.c
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    x0, y0 = min(xs), min(ys)
    sx, sy = max(1.0, max(xs) - x0), max(1.0, max(ys) - y0)

    def shade(x, y):
        return scale(mix(left, right, clamp((x - x0) / sx) ** power), 1.0 + k * (1.0 - 2.0 * (y - y0) / sy))
    _fillpoly(c, px, left, alpha, shade)


def _vpoly(c, pts, top, bottom, smooth=0, alpha=1.0):
    """Polygon shaded top-to-bottom (scanline fill)."""
    if smooth:
        pts = _chaikin(pts, smooth)
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    ys = [p[1] for p in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    _fillpoly(c, px, top, alpha, lambda x, y: mix(top, bottom, clamp((y - y0) / sp)))


def _leaf(c, u, v, length, angle, color, width=0.45, vein=True):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = [(t * length, math.sin(math.pi * t) ** 0.8 * wd) for t in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    out = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    px = [(c.X(u + x * ca - y * sa), c.Y(v + x * sa + y * ca)) for x, y in out]
    ys = [p_[1] for p_ in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    top, bot = scale(color, 1.12), scale(color, 0.80)
    _fillpoly(c, px, color, 1.0, lambda x, y: mix(top, bot, clamp((y - y0) / sp)))
    if vein:
        c.line(u, v, u + length * 0.9 * ca, v + length * 0.9 * sa, length * 0.04, scale(color, 0.66), 0.6)


def _spoly(c, pts, stops, k=0.05, alpha=1.0, smooth=0):
    """Polygon shaded left-to-right through colour `stops` [(t, colour)] (metal, glass, glossy plastic bands) and a little top-to-bottom."""
    if smooth:
        pts = _chaikin(pts, smooth)
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    x0, y0 = min(xs), min(ys)
    sx, sy = max(1.0, max(xs) - x0), max(1.0, max(ys) - y0)
    _fillpoly(c, px, stops[0][1], alpha, lambda x, y: scale(lerp_stops(stops, clamp((x - x0) / sx)), 1.0 + k * (1.0 - 2.0 * (y - y0) / sy)))


def _bands(col, kind="metal"):
    """Colour stops across a cylinder for metal (bright core band, dark band, soft reflected light on the shadow side) or matte."""
    if kind == "metal":
        return [(0.0, scale(col, 0.55)), (0.14, scale(col, 1.35)), (0.30, scale(col, 1.0)), (0.55, scale(col, 0.62)), (0.80, scale(col, 0.95)),
                (0.92, scale(col, 0.70)), (1.0, scale(col, 0.40))]
    if kind == "glass":
        return [(0.0, scale(col, 0.55)), (0.15, scale(col, 1.25)), (0.4, scale(col, 1.0)), (0.75, scale(col, 0.62)), (0.90, scale(col, 0.85)), (1.0, scale(col, 0.45))]
    return [(0.0, scale(col, 1.2)), (0.4, scale(col, 1.0)), (1.0, scale(col, 0.55))]


def _lathe(c, u, v, prof, col, kl=1.18, kr=0.60, tilt=TILT, rim=True, inner=None, rimcol=None, k=0.05, power=1.0, foot=True, kind=None):
    """A turned vessel: `prof` = [(radius, height)] bottom to top, base centre (u, v). Shaded left-to-right (`kind` metal / glass / matte
    for banded shading); the top is an open ellipse (inner wall darker) when `rim` is set."""
    r0 = prof[0][0]
    if foot:
        c.ellipse(u, v + prof[0][1], r0, r0 * tilt, scale(col, max(kr, 0.5) * 0.95), lift=0)
    pts = [(u + r, v + h) for r, h in prof] + [(u - r, v + h) for r, h in reversed(prof)]
    if kind:
        _spoly(c, pts, _bands(col, kind), k)
    else:
        _hpoly(c, pts, scale(col, kl), scale(col, kr), k, power=power)
    rt, ht = prof[-1]
    if rim:
        c.ellipse(u, v + ht, rt, rt * tilt, rimcol or scale(col, 1.12), lift=0.0)
        c.ellipse(u, v + ht + rt * tilt * 0.06, rt * 0.90, rt * tilt * 0.86, inner or scale(col, 0.45), lift=0.0)
        soft_disc(c, u + rt * 0.25, v + ht + rt * tilt * 0.1, rt * 0.75, rt * tilt * 0.6, BLACK, 0.25, 1.2)


def _ball(c, u, v, r, col, spec=0.6, dk=0.40):
    """A shaded sphere (flat-ish look avoided: lit core, dark terminator, highlight)."""
    c.ellipse(u, v, r, r, scale(col, 0.62), lift=0.10)
    soft_disc(c, u - r * 0.22, v + r * 0.24, r * 0.80, r * 0.78, scale(col, 1.28), 0.95, 0.85)
    soft_disc(c, u + r * 0.38, v - r * 0.38, r * 0.55, r * 0.55, BLACK, dk, 1.3)
    soft_disc(c, u - r * 0.38, v + r * 0.40, r * 0.28, r * 0.20, WHITE, spec, 1.0, 35, add=True)


class _Cx:
    """Minimal stand-in for a Ctx so the scanline fill can draw straight onto the stage canvas."""
    def __init__(self, cv):
        self.cv = cv


def _spoly_stage(S, pts, color, alpha=1.0):
    """Fast (scanline) polygon in stage units, for big areas such as a table runner or a window beam."""
    if S.dry:
        return
    S._ensure_mid() if S._layer is S.main else None
    _fillpoly(_Cx(S.cv), [S.px(u, v) for u, v in pts], color, alpha)


def _blobs(S, n, u0, v0, u1, v1, color, alpha, rmin, rmax):
    for _ in range(n):
        r = S.rng.uniform(rmin, rmax)
        S.soft(S.rng.uniform(u0, u1), S.rng.uniform(v0, v1), r, r * S.rng.uniform(0.6, 1.0), color, alpha, 1.0)


def _scatter_leaves(S, n, u0, v0, u1, v1, cols, ln=0.05):
    """Loose leaves lying on the surface (stage drawing, so they sit in the same plane as the table)."""
    for _ in range(n):
        u, v = S.rng.uniform(u0, u1), S.rng.uniform(v0, v1)
        a = S.rng.uniform(0, 6.28)
        l = ln * S.rng.uniform(0.7, 1.3)
        col = cols[S.rng.randrange(len(cols))]
        S.ellipse(u, v, l * 0.5, l * 0.2, col, angle=math.degrees(a), lift=0.12)


# ====================================================================================== AYURVEDA
@sprop("care_ayur_bowls", aspect=2.5, fill=0.5)
def ayur_bowls(c, color):
    """A wooden tray carrying three brass bowls of herbal powders (turmeric, neem, kumkum) with a spoon and loose leaves."""
    rng = c.rng
    wood = (0.50, 0.32, 0.18)
    ao(c, 0.0, 0.0, 1.30, 0.26, 0.7)
    soft_disc(c, 0.02, 0.01, 0.66, 0.045, BLACK, 0.6, 1.2)
    # tray: thick front face, top rim, dark inner floor
    c.rect(0.0, 0.07, 1.26, 0.10, scale(wood, 0.70), r=0.04, lift=0.0)
    craft.hshade_box(c, 0.0, 0.07, 1.26, 0.10, scale(wood, 1.15), scale(wood, 0.62), r=0.04)
    for _ in range(16):
        x = rng.uniform(-0.6, 0.6)
        c.line(x, 0.04, x + rng.uniform(0.04, 0.14), 0.04 + rng.uniform(-0.004, 0.006), 0.0025, scale(wood, rng.uniform(0.6, 0.8)), 0.4)
    c.rect(0.0, 0.205, 1.26, 0.24, scale(wood, 1.02), r=0.05, lift=0.18)
    c.rect(0.0, 0.205, 1.14, 0.17, scale(wood, 0.62), r=0.035, lift=0.0)
    c.rect(0.0, 0.222, 1.14, 0.14, scale(wood, 0.92), r=0.03, lift=0.10)
    for _ in range(14):
        x, y = rng.uniform(-0.52, 0.52), rng.uniform(0.17, 0.27)
        c.line(x, y, x + rng.uniform(0.06, 0.2), y + rng.uniform(-0.004, 0.004), 0.002, scale(wood, rng.uniform(0.7, 0.8)), 0.45)
    c.rect(0.0, 0.318, 1.24, 0.008, scale(wood, 1.4), r=0.004, lift=0, alpha=0.55)
    # three bowls: brass lathe + mound of powder
    for u, v, r, h, pc, pc2 in ((-0.38, 0.19, 0.19, 0.15, (0.95, 0.72, 0.10), (0.99, 0.84, 0.28)),
                                (0.02, 0.215, 0.20, 0.16, (0.42, 0.52, 0.18), (0.58, 0.68, 0.30)),
                                (0.42, 0.185, 0.19, 0.15, (0.78, 0.12, 0.09), (0.92, 0.28, 0.16))):
        prof = [(r * 0.60, 0.0), (r * 0.78, 0.03), (r * 0.94, 0.085), (r * 1.0, h * 0.88), (r * 1.02, h)]
        soft_disc(c, u + r * 0.12, v - 0.004, r * 1.15, r * TILT * 0.8, BLACK, 0.55, 1.2)
        _lathe(c, u, v, prof, BRASS, inner=scale(BRASS, 0.5), kind="metal")
        # powder mound heaped above the rim
        c.ellipse(u, v + h + 0.004, r * 0.90, r * TILT * 0.80, scale(pc, 0.75), lift=0)
        c.ellipse(u, v + h + 0.030, r * 0.80, r * TILT * 1.02, pc, lift=0.16)
        soft_disc(c, u - r * 0.2, v + h + 0.055, r * 0.55, r * 0.28, pc2, 0.9, 1.0)
        soft_disc(c, u + r * 0.4, v + h + 0.012, r * 0.55, r * 0.22, BLACK, 0.30, 1.2)
        for _ in range(26):
            a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * r * 0.72
            c.ellipse(u + math.cos(a) * rr, v + h + 0.034 + math.sin(a) * rr * TILT * 0.9, rng.uniform(0.003, 0.008), rng.uniform(0.002, 0.005),
                      scale(pc, rng.choice((0.78, 1.18))), alpha=0.6, lift=0)
        # brass gloss on the side and a warm reflection of the powder
        soft_disc(c, u - r * 0.52, v + h * 0.5, r * 0.10, h * 0.40, (1.0, 0.93, 0.7), 0.55, 1.0, add=True)
        soft_disc(c, u + r * 0.4, v + h * 0.3, r * 0.3, h * 0.35, pc, 0.25, 1.2)
        craft.arc(c, u, v + h, r * 1.01, r * TILT * 1.01, 200, 340, 0.006, (1.0, 0.92, 0.7), 0.55, steps=8)
    # a small wooden spoon in the middle bowl and a few leaves
    c.line(0.08, 0.40, 0.30, 0.52, 0.016, (0.55, 0.36, 0.20), 1.0)
    c.ellipse(0.06, 0.385, 0.03, 0.02, (0.62, 0.42, 0.24), lift=0.1, angle=30)
    for k in range(5):
        _leaf(c, rng.uniform(-0.55, 0.55), rng.uniform(0.2, 0.28), rng.uniform(0.07, 0.10), rng.uniform(0, 360), (0.28 + 0.1 * rng.random(), 0.5, 0.22), 0.5, vein=False)


@sprop("care_ayur_oils", aspect=1.18, fill=1.0)
def ayur_oils(c, color):
    """Three medicinal oil bottles (amber and cobalt glass) with cork stoppers and cream labels."""
    rng = c.rng
    acc = _pal(color, "accent", (0.25, 0.5, 0.3))
    ao(c, 0.0, 0.0, 1.05, 0.14, 0.5)

    def bottle(u, h, w, glass, oil_k, label_h, cork_col, drop=False):
        r = w / 2
        v = 0.0
        sh = h * 0.60
        neck = r * 0.40
        prof = [(r * 0.88, 0.0), (r, 0.025), (r, sh), (r * 0.86, sh + h * 0.08), (neck * 1.15, h * 0.80), (neck, h * 0.88), (neck, h * 0.98)]
        c.ellipse(u, v + 0.012, r, r * TILT * 0.8, scale(glass, 0.35), lift=0)
        _hpoly(c, [(u + rr, v + hh) for rr, hh in prof] + [(u - rr, v + hh) for rr, hh in reversed(prof)], scale(glass, 1.25), scale(glass, 0.42), 0.0, power=1.3)
        # liquid inside is a bit lighter at the bottom (light passes through), darker at the edge
        c.rect(u + r * 0.12, sh * 0.46, r * 1.2, sh * 0.82, scale(glass, 1.45), r=r * 0.2, lift=0.0, alpha=0.30)
        soft_disc(c, u + r * 0.2, sh * 0.30, r * 0.6, sh * 0.35, mix(glass, (1.0, 0.8, 0.3), 0.5), 0.35, 1.2, add=True)
        # label
        lv = sh * 0.55
        c.rect(u, lv, r * 1.72, label_h, (0.96, 0.92, 0.82), r=0.006, lift=0.05)
        c.rect(u, lv + label_h * 0.28, r * 1.72, label_h * 0.14, acc, lift=0.0)
        c.rect(u, lv - label_h * 0.30, r * 1.0, label_h * 0.08, scale((0.5, 0.4, 0.3), 1.0), lift=0, alpha=0.7)
        c.rect(u, lv - label_h * 0.12, r * 1.25, label_h * 0.05, (0.5, 0.4, 0.3), lift=0, alpha=0.6)
        c.ellipse(u, lv + label_h * 0.02, r * 0.14, r * 0.16, scale(acc, 0.8), lift=0.1)
        # cork / dropper cap
        cap = h * 0.98
        craft.hshade_box(c, u, cap + h * 0.055, neck * 1.9, h * 0.10, scale(cork_col, 1.15), scale(cork_col, 0.62), r=0.012)
        c.ellipse(u, cap + h * 0.105, neck * 0.95, neck * 0.38, scale(cork_col, 1.25), lift=0)
        if drop:
            c.rect(u, cap + h * 0.14, neck * 0.7, h * 0.07, (0.14, 0.14, 0.15), lift=0.2)
            c.ellipse(u, cap + h * 0.22, neck * 0.9, h * 0.075, (0.14, 0.14, 0.15), lift=0.3)
            soft_disc(c, u - neck * 0.3, cap + h * 0.23, neck * 0.35, h * 0.03, WHITE, 0.5, 1.0, add=True)
        # glass highlights
        c.rect(u - r * 0.62, sh * 0.52, r * 0.10, sh * 0.78, WHITE, r=r * 0.05, lift=0, alpha=0.55)
        c.rect(u - r * 0.62, sh + h * 0.07, r * 0.05, h * 0.07, WHITE, lift=0, alpha=0.4)
        c.rect(u + r * 0.70, sh * 0.5, r * 0.04, sh * 0.7, scale(glass, 1.6), lift=0, alpha=0.4)
        soft_disc(c, u - r * 0.3, sh * 0.2, r * 0.3, sh * 0.1, WHITE, 0.2, 1.0, add=True)

    bottle(-0.30, 0.78, 0.30, (0.62, 0.30, 0.05), 1.0, 0.17, (0.62, 0.44, 0.26))
    bottle(0.05, 1.0, 0.34, (0.42, 0.16, 0.03), 1.0, 0.20, (0.58, 0.40, 0.24), drop=True)
    bottle(0.40, 0.66, 0.28, (0.12, 0.28, 0.50), 1.0, 0.15, (0.62, 0.44, 0.26))
    # a dropper spill: a glossy droplet in front
    craft.drip(c, 0.22, 0.016, 0.014, (0.80, 0.44, 0.08))


@sprop("care_ayur_mortar", aspect=1.35, fill=0.62)
def ayur_mortar(c, color):
    """Dark stone mortar full of crushed herbs, a pestle leaning in it, a few whole spices and leaves beside."""
    rng = c.rng
    st = (0.30, 0.28, 0.27)
    ao(c, 0.0, 0.0, 1.0, 0.2, 0.5)
    prof = [(0.17, 0.0), (0.25, 0.015), (0.31, 0.12), (0.35, 0.28), (0.355, 0.37)]
    _lathe(c, 0.0, 0.03, prof, st, 1.55, 0.50, inner=scale(st, 0.5), power=1.2)
    # foot ring
    c.ellipse(0.0, 0.03, 0.18, 0.18 * TILT, scale(st, 0.4), lift=0, alpha=0.0)
    # herbs mounded in the bowl
    top = 0.03 + 0.37
    c.ellipse(0.0, top + 0.01, 0.31, 0.31 * TILT * 0.92, (0.22, 0.30, 0.12), lift=0.0)
    for _ in range(34):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.28
        col = rng.choice(((0.30, 0.46, 0.18), (0.20, 0.34, 0.12), (0.46, 0.58, 0.24), (0.52, 0.40, 0.18)))
        _leaf(c, math.cos(a) * rr, top + 0.025 + math.sin(a) * rr * TILT, rng.uniform(0.05, 0.10), rng.uniform(0, 360), col, 0.5, vein=False)
    for _ in range(22):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.26
        c.ellipse(math.cos(a) * rr, top + 0.04 + math.sin(a) * rr * TILT, rng.uniform(0.005, 0.01), rng.uniform(0.004, 0.008),
                  rng.choice(((0.12, 0.09, 0.05), (0.85, 0.65, 0.2), (0.6, 0.2, 0.1))), lift=0.1)
    # pestle: stone club leaning to the right
    p0, p1 = (0.05, top + 0.03), (0.44, 0.74)
    d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    nx, ny = -(p1[1] - p0[1]) / d, (p1[0] - p0[0]) / d
    _hpoly(c, [(p0[0] + nx * 0.03, p0[1] + ny * 0.03), (p1[0] + nx * 0.055, p1[1] + ny * 0.055), (p1[0] - nx * 0.055, p1[1] - ny * 0.055),
               (p0[0] - nx * 0.03, p0[1] - ny * 0.03)], scale(st, 1.7), scale(st, 0.5), 0.0)
    c.ellipse(p1[0], p1[1], 0.058, 0.058, scale(st, 1.2), lift=0.2)
    gloss(c, p1[0] - 0.02, p1[1] + 0.02, 0.025, 0.018, 0, 0.5)
    # stone gloss + speckle
    for _ in range(26):
        c.ellipse(rng.uniform(-0.32, 0.32), rng.uniform(0.07, 0.34), rng.uniform(0.003, 0.007), rng.uniform(0.002, 0.005), scale(st, rng.choice((0.6, 1.9))), alpha=0.5, lift=0)
    gloss(c, -0.23, 0.26, 0.04, 0.10, 12, 0.45)
    # whole spices at the foot
    for k in range(6):
        c.ellipse(0.42 + rng.uniform(-0.05, 0.18), rng.uniform(0.02, 0.07), 0.016, 0.012, (0.22, 0.12, 0.06), lift=0.2)
    for k in range(3):
        _leaf(c, -0.45 - k * 0.05, 0.03 + k * 0.012, 0.11, 160 + k * 25, (0.26, 0.5, 0.22), 0.5)


@sprop("care_ayur_tulsi", aspect=0.95, fill=1.0)
def ayur_tulsi(c, color):
    """A tulsi plant in a terracotta pot: layers of oval leaves, a few flower spikes."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.62, 0.12, 0.5)
    clay = (0.74, 0.38, 0.22)
    prof = [(0.15, 0.0), (0.19, 0.06), (0.22, 0.16), (0.235, 0.26)]
    _lathe(c, 0.0, 0.02, prof, clay, 1.2, 0.52, inner=(0.18, 0.12, 0.08))
    c.rect(0.0, 0.26, 0.50, 0.04, scale(clay, 1.05), r=0.015, lift=0.1)
    craft.hshade_box(c, 0.0, 0.275, 0.50, 0.045, scale(clay, 1.25), scale(clay, 0.60), r=0.016)
    for k in range(3):
        x = -0.15 + k * 0.15
        c.line(x, 0.10, x + 0.02, 0.22, 0.003, scale(clay, 0.78), 0.5)
    c.rect(-0.14, 0.14, 0.025, 0.2, WHITE, alpha=0.18, lift=0, r=0.01)
    stems = []
    for i in range(9):
        a = math.radians(90 + (i - 4) * 14 + rng.uniform(-5, 5))
        ln = rng.uniform(0.50, 0.82)
        stems.append((a, ln))
    for a, ln in stems:
        c.line(0.0, 0.30, math.cos(a) * ln * 0.55, 0.30 + math.sin(a) * ln, 0.012, (0.30, 0.38, 0.18), 1.0)
    for a, ln in stems:
        for k in range(5):
            t = 0.30 + k * 0.17
            x, y = math.cos(a) * ln * 0.55 * t, 0.30 + math.sin(a) * ln * t
            for s in (-1, 1):
                col = (0.18 + 0.12 * rng.random(), 0.42 + 0.14 * rng.random(), 0.17)
                if k >= 3 and rng.random() < 0.35:
                    col = (0.30, 0.22, 0.30)
                _leaf(c, x, y, 0.15 * (1.1 - 0.15 * k) + 0.04, 90 + s * rng.uniform(40, 80), col, 0.62)
    for a, ln in stems[::3]:
        x, y = math.cos(a) * ln * 0.55, 0.30 + math.sin(a) * ln
        c.line(x, y, x, y + 0.07, 0.012, (0.48, 0.36, 0.38), 1.0)
        for k in range(4):
            c.ellipse(x + rng.uniform(-0.012, 0.012), y + 0.015 + k * 0.016, 0.014, 0.009, (0.62, 0.50, 0.66), lift=0.1)
    soft_disc(c, -0.1, 0.8, 0.25, 0.15, (0.8, 1.0, 0.6), 0.14, 1.2, add=True)


@niche("ayurveda", "Ayurvedic clinic", subjects=("care_ayur_bowls",),
       strong=("ayurveda", "ayurvedic", "ayurvedic clinic", "ayurvedic treatment", "panchakarma", "herbal medicine", "naturopathy",
               "herbal powder", "ayurved", "ayurvedik", "jadi booti", "आयुर्वेद", "आयुर्वेदिक", "जड़ी बूटी", "पंचकर्म"),
       weak=("herbal", "natural medicine", "ayush", "vaidya", "वैद्य", "herbs", "tulsi", "wellness", "holistic", "organic"),
       accent="#3f7d4f", mood="warm", group="wellness")
def ayurveda(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.6 if dark else 1.0
    clay = mix(P.wall_bot, (0.80, 0.55, 0.36), 0.35 if not dark else 0.15)
    with S.far():
        S.wall(mix(P.wall_top, clay, 0.45), scale(mix(P.wall_bot, clay, 0.55), 0.92), 0.58)
        # plaster texture
        _blobs(S, 22, -1.0, 0.0, 3.0, 0.58, scale(clay, 0.78), 0.20, 0.12, 0.34)
        _blobs(S, 14, -1.0, 0.0, 3.0, 0.58, scale(clay, 1.25), 0.16, 0.10, 0.28)
        # arched niche with shelves full of clay jars
        S.rect(1.55, 0.30, 0.62, 0.50, scale(clay, 0.5 if not dark else 0.4), r=0.02, lift=0.0)
        S.circle(1.55, 0.05, 0.31, scale(clay, 0.5 if not dark else 0.4), lift=0.0)
        S.rect(1.55, 0.30, 0.54, 0.56, scale(clay, 0.34), r=0.02, lift=0.0)
        S.glow(1.55, 0.28, 0.5, (1.0, 0.72, 0.38), 0.45 * gl, 1.7)
        for v in (0.19, 0.37, 0.55):
            S.rect(1.55, v + 0.02, 0.56, 0.016, scale(WOOD, 0.8), lift=0.0)
            for k in range(5):
                u = 1.34 + k * 0.105 + S.rng.uniform(-0.01, 0.01)
                h = S.rng.uniform(0.07, 0.12)
                col = S.rng.choice(((0.72, 0.42, 0.25), (0.82, 0.62, 0.36), (0.40, 0.30, 0.22), (0.55, 0.55, 0.32)))
                S.ellipse(u, v - h / 2, 0.038, h / 2, col, lift=0.14)
                S.rect(u, v - h, 0.05, 0.016, scale(col, 0.8), lift=0.0)
        # window on the left with warm daylight
        S.window(0.32, 0.26, 0.34, 0.36, sky_top=(1.0, 0.88, 0.62), sky_bot=(1.0, 0.96, 0.82), frame=scale(WOOD, 0.9))
        S.glow(0.32, 0.30, 0.9, (1.0, 0.82, 0.5), 0.34 * gl, 1.7)
        # hanging herb bundles
        for u, ln in ((0.80, 0.22), (0.94, 0.30), (1.04, 0.18), (0.66, 0.15)):
            S.line(u, 0.0, u, ln - 0.03, 0.004, (0.35, 0.25, 0.15), 0.9)
            S.ellipse(u, ln, 0.026, 0.06, S.rng.choice(((0.30, 0.45, 0.2), (0.5, 0.45, 0.2), (0.34, 0.5, 0.26))), lift=0.1)
        S.bokeh(8, 0.0, 0.08, 2.0, 0.5, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.4)], 0.012, 0.04, 0.3 * gl)
        S.floor(0.58, P.floor_top, P.floor_bot)
    # dark carved wood table with a woven cotton runner
    wood = mix(P.surface, (0.40, 0.25, 0.14), 0.45)
    S.soft(1.05, 0.64, 0.9, 0.12, (1.0, 0.8, 0.5), 0.20 * gl, 1.4, add=True)
    S.wood(-5.0, 0.58, 7.0, 2.6, wood, plank=0.12, grain=0.4)
    S.rect(1.0, 0.58, 14.0, 0.008, scale(wood, 0.4), lift=0.0)
    cloth = scale(mix(P.accent_light, (0.93, 0.70, 0.46), 0.80), 0.55 if dark else 0.93)
    _spoly_stage(S, [(0.15, 0.66), (2.05, 0.66), (2.50, 1.06), (-0.35, 1.06)], cloth)
    for k in range(9):
        t = k / 8.0
        S.line(0.15 + 1.9 * t, 0.66, -0.35 + 2.85 * t, 1.06, 0.004, mix(P.accent, WHITE, 0.2), 0.55 if k % 4 == 0 else 0.22)
    S.line(0.15, 0.66, -0.35, 1.06, 0.006, P.accent_dark, 0.7)
    S.line(2.05, 0.66, 2.50, 1.06, 0.006, P.accent_dark, 0.7)
    S.soft(1.1, 0.84, 0.9, 0.12, WHITE, 0.16 * (0.5 if dark else 1.0), 1.4, add=True)
    # light from the window falling across the table
    _spoly_stage(S, [(0.45, 0.60), (0.80, 0.60), (1.30, 1.10), (0.70, 1.10)], mix(P.light, (1.0, 0.85, 0.5), 0.4), 0.09 * gl)
    # loose leaves
    _scatter_leaves(S, 10, 0.6, 0.78, 1.7, 1.02, ((0.25, 0.48, 0.2), (0.34, 0.52, 0.24)), 0.07)
    S.put("care_ayur_oils", 0.70, 0.80, 0.36, color=P, shadow_w=0.34)
    S.put("care_ayur_tulsi", 1.58, 0.78, 0.40, shadow_w=0.3)
    S.put("care_ayur_mortar", 1.55, 0.97, 0.22, shadow_w=0.4)
    S.put("care_ayur_bowls", 1.08, 0.94, 0.30, subject=True, shadow_w=0.6)
    S.focus("detail", 1.08, 0.84)
    if dark:                                    # practical light: a brass oil lamp (diya) glowing on the table
        S.glow(0.95, 0.82, 0.55, (1.0, 0.62, 0.25), 0.40, 1.8)
        S.soft(1.1, 0.95, 0.6, 0.12, (1.0, 0.7, 0.35), 0.18, 1.5, add=True)
    with S.near():
        S.circle(0.42, 1.10, 0.06, (1.0, 0.8, 0.45), alpha=0.32, lift=0)
        S.poly([(1.76, 1.0), (2.0, 0.92), (2.1, 1.1), (1.8, 1.14)], mix(P.accent, (0.2, 0.4, 0.2), 0.5), alpha=0.9)


# ====================================================================================== PHYSIOTHERAPY
@sprop("care_physio_table", aspect=2.7, fill=0.5)
def physio_table(c, color):
    """Treatment table: padded vinyl top with stitched edge, steel frame, pillow and folded towel."""
    rng = c.rng
    vin = _pal(color, "accent", (0.16, 0.6, 0.55))
    vin = mix(vin, WHITE, 0.15)
    steel = (0.62, 0.66, 0.70)
    ao(c, 0.0, 0.0, 1.45, 0.26, 0.6)
    soft_disc(c, 0.02, 0.01, 0.70, 0.04, BLACK, 0.55, 1.2)
    # far legs (darker, set back and to the right), stretcher
    for x in (-0.44, 0.60):
        _spoly(c, [(x - 0.025, 0.05), (x + 0.025, 0.05), (x + 0.025, 0.24), (x - 0.025, 0.24)], [(0.0, scale(steel, 0.45)), (0.5, scale(steel, 0.8)), (1.0, scale(steel, 0.35))], 0.0)
        c.ellipse(x, 0.045, 0.05, 0.016, (0.1, 0.1, 0.11), lift=0.1)
    c.rect(0.05, 0.12, 1.1, 0.020, scale(steel, 0.8), lift=0.25, r=0.008)
    c.rect(0.05, 0.126, 1.06, 0.005, WHITE, alpha=0.5, lift=0)
    # top face (seen from above), then the thick front cushion
    top = [(-0.66, 0.31), (0.66, 0.31), (0.76, 0.42), (-0.56, 0.42)]
    _vpoly(c, top, scale(vin, 1.22), scale(vin, 1.04))
    for x in (-0.15, 0.30):
        c.line(x, 0.31, x + 0.10, 0.42, 0.004, scale(vin, 0.6), 0.45)
    soft_disc(c, 0.20, 0.375, 0.50, 0.04, WHITE, 0.35, 1.2, add=True)
    c.line(-0.56, 0.42, 0.76, 0.42, 0.004, scale(vin, 0.7), 0.5)
    craft.hshade_box(c, 0.0, 0.24, 1.34, 0.14, scale(vin, 1.12), scale(vin, 0.62), r=0.05)
    c.rect(0.0, 0.302, 1.30, 0.012, scale(vin, 1.5), lift=0, alpha=0.5, r=0.006)
    for k in range(33):                                     # stitched piping along the lower edge
        x = -0.62 + k * 0.0385
        c.line(x, 0.205, x + 0.017, 0.205, 0.004, scale(vin, 0.45), 0.6)
    soft_disc(c, -0.25, 0.268, 0.36, 0.014, WHITE, 0.40, 1.1, add=True)
    soft_disc(c, 0.0, 0.17, 0.68, 0.025, BLACK, 0.5, 1.3)
    # near legs
    for x in (-0.56, 0.56):
        _spoly(c, [(x - 0.03, 0.01), (x + 0.03, 0.01), (x + 0.03, 0.175), (x - 0.03, 0.175)], _bands(steel, "metal"), 0.0)
        c.rect(x, 0.012, 0.11, 0.024, (0.14, 0.14, 0.16), r=0.01, lift=0.2)
        c.rect(x, 0.17, 0.08, 0.016, scale(steel, 0.7), lift=0.1)
    # pillow with a white cover and folded towel lying on the top face
    soft_disc(c, -0.33, 0.378, 0.24, 0.04, BLACK, 0.25, 1.3)
    c.rect(-0.37, 0.405, 0.38, 0.085, scale(WHITE, 0.80), r=0.040, lift=0.0)
    c.rect(-0.37, 0.415, 0.36, 0.075, (0.97, 0.97, 0.98), r=0.036, lift=0.10)
    soft_disc(c, -0.44, 0.435, 0.12, 0.028, WHITE, 0.7, 1.0, add=True)
    soft_disc(c, -0.22, 0.395, 0.12, 0.03, BLACK, 0.12, 1.3)
    for k in range(3):
        c.rect(0.42, 0.395 + k * 0.026, 0.30 - k * 0.014, 0.030, (0.97, 0.98, 0.99) if k != 1 else (0.82, 0.92, 0.93), r=0.012, lift=0.12)
    soft_disc(c, 0.44, 0.385, 0.19, 0.022, BLACK, 0.3, 1.3)
    c.rect(0.42, 0.455, 0.26, 0.004, WHITE, alpha=0.6, lift=0)


@sprop("care_physio_ball", aspect=1.0, fill=1.0)
def physio_ball(c, color):
    """A large exercise ball: glossy vinyl with moulded seam lines and a valve."""
    col = _pal(color, "accent", (0.16, 0.6, 0.55))
    col = mix(col, (0.1, 0.55, 0.6), 0.2)
    ao(c, 0.0, 0.0, 0.8, 0.14, 0.6)
    c.ellipse(0.0, 0.5, 0.5, 0.5, scale(col, 0.50), lift=0.0)
    soft_disc(c, -0.10, 0.60, 0.42, 0.42, scale(col, 1.45), 0.95, 0.95)
    soft_disc(c, 0.0, 0.5, 0.48, 0.48, scale(col, 0.9), 0.0, 1.0)
    soft_disc(c, 0.22, 0.22, 0.30, 0.30, BLACK, 0.40, 1.1)
    # seam lines wrapping the sphere
    craft.arc(c, 0.0, 0.5, 0.49, 0.49, 60, 120, 0.007, scale(col, 0.45), 0.5, steps=8)
    for k, a in enumerate((-0.28, 0.0, 0.28)):
        craft.arc(c, a, 0.5, 0.18 + abs(a) * 0.3, 0.485, 80, 280, 0.004, scale(col, 0.55), 0.35, steps=14, angle=0)
    craft.arc(c, 0.0, 0.5, 0.47, 0.13, 195, 345, 0.004, scale(col, 0.58), 0.4, steps=14)
    c.ellipse(0.10, 0.12, 0.020, 0.010, scale(col, 0.4), lift=0.2)
    soft_disc(c, -0.24, 0.76, 0.17, 0.10, WHITE, 0.80, 1.0, 35, add=True)
    soft_disc(c, -0.28, 0.80, 0.045, 0.03, WHITE, 0.95, 1.2, 35, add=True)
    craft.arc(c, 0.0, 0.5, 0.485, 0.485, 200, 330, 0.008, scale(col, 1.5), 0.25, steps=12)


def _vbands_poly(c, pts, stops, alpha=1.0):
    """Polygon shaded top-to-bottom through colour `stops` (horizontal cylinders, tubes)."""
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    ys = [p[1] for p in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    _fillpoly(c, px, stops[0][1], alpha, lambda x, y: lerp_stops(stops, clamp((y - y0) / sp)))


@sprop("care_physio_spine", aspect=0.62, fill=1.0)
def physio_spine(c, color):
    """Anatomical spine model seen from the side: skull, 16 vertebrae (rounded bodies, spinous processes, blue discs) along the natural S-curve,
    sacrum and pelvis, on a round plinth with a support pole."""
    rng = c.rng
    bone = (0.93, 0.86, 0.72)
    ao(c, 0.0, 0.0, 0.8, 0.12, 0.6)
    c.ellipse(0.0, 0.02, 0.31, 0.31 * TILT, (0.08, 0.08, 0.10), lift=0.2)
    c.ellipse(0.0, 0.055, 0.29, 0.29 * TILT, (0.19, 0.20, 0.24), lift=0.3)
    c.ellipse(0.0, 0.062, 0.255, 0.255 * TILT, (0.12, 0.13, 0.16), lift=0.1)
    soft_disc(c, -0.10, 0.07, 0.17, 0.045, WHITE, 0.28, 1.2, add=True)
    _spoly(c, [(0.20, 0.06), (0.245, 0.06), (0.245, 0.76), (0.20, 0.76)], _bands((0.55, 0.57, 0.62), "metal"), 0.0)
    craft.hshade_box(c, 0.12, 0.745, 0.26, 0.026, (0.78, 0.80, 0.85), (0.35, 0.37, 0.42), r=0.012)
    # pelvis: far iliac wing, near wing, sacrum
    c.ellipse(0.05, 0.215, 0.085, 0.100, scale(bone, 0.58), lift=0.1, angle=-18)
    c.ellipse(-0.04, 0.205, 0.095, 0.108, scale(bone, 0.95), lift=0.2, angle=-18)
    c.ellipse(-0.05, 0.200, 0.030, 0.040, (0.18, 0.15, 0.12), lift=0)
    _hpoly(c, [(-0.07, 0.32), (0.07, 0.32), (0.075, 0.24), (0.045, 0.16), (-0.005, 0.15), (-0.03, 0.22)], scale(bone, 1.10), scale(bone, 0.68), 0.04, smooth=1)
    soft_disc(c, 0.09, 0.19, 0.10, 0.06, BLACK, 0.22, 1.2)
    # vertebrae
    n = 16
    discc = (0.40, 0.58, 0.80)
    pts = []
    for i in range(n):
        t = i / float(n - 1)
        v = 0.335 + t * 0.455
        u = -0.030 + 0.045 * math.sin(t * 2 * math.pi * 1.1 + 0.6) - 0.02 * t
        w = 0.150 - 0.095 * t ** 0.85
        pts.append((u, v, w, t))
    d = 0.455 / (n - 1)
    for (u, v, w, t) in pts:
        hb = d * 0.70
        # spinous process (back, to the right) and a rear arch
        pr = w * (1.15 - 0.45 * t) + 0.02
        c.line(u + w * 0.42, v, u + w * 0.42 + pr, v - d * 0.18 - 0.012 * (1 - t), 0.022 - 0.010 * t, scale(bone, 0.60), 1.0)
        c.line(u + w * 0.42, v + 0.004, u + w * 0.42 + pr * 0.94, v - d * 0.12 - 0.010 * (1 - t) + 0.004, 0.010 - 0.004 * t, scale(bone, 0.92), 0.8)
        # disc under the body
        craft.hshade_box(c, u + w * 0.02, v - hb * 0.5 - d * 0.14, w * 1.32, d * 0.30, scale(discc, 1.15), scale(discc, 0.55), r=d * 0.12)
        # vertebral body
        craft.hshade_box(c, u, v, w * 1.5, hb, scale(bone, 1.15), scale(bone, 0.64), r=hb * 0.35)
        c.rect(u - w * 0.22, v + hb * 0.22, w * 0.9, hb * 0.14, WHITE, alpha=0.30, lift=0, r=hb * 0.07)
        c.ellipse(u + w * 0.46, v, w * 0.17, hb * 0.28, scale(bone, 0.50), lift=0, alpha=0.8)     # canal shadow
    # skull on the top vertebra
    su, sv = pts[-1][0] - 0.035, 0.885
    c.ellipse(su + 0.012, sv - 0.005, 0.088, 0.078, scale(bone, 0.72), lift=0.1)
    _ball(c, su, sv, 0.083, bone, spec=0.28, dk=0.25)
    c.ellipse(su - 0.042, sv - 0.014, 0.019, 0.024, (0.12, 0.09, 0.07), lift=0)
    craft.hshade_box(c, su - 0.032, sv - 0.080, 0.075, 0.032, scale(bone, 1.02), scale(bone, 0.62), r=0.014)
    for k in range(5):
        c.line(su - 0.062 + k * 0.014, sv - 0.068, su - 0.062 + k * 0.014, sv - 0.080, 0.0035, (0.99, 0.97, 0.92), 0.9)
    # nerve roots and a highlight down the lit side
    for k in range(1, n, 3):
        u, v, w, t = pts[k]
        craft.strand(c, u - w * 0.78, v - 0.01, 0.045 + 0.025 * (1 - t), 195, 0.0028, (0.95, 0.78, 0.25), 0.85, 0.5)
    soft_disc(c, -0.08, 0.56, 0.06, 0.28, WHITE, 0.10, 1.2, add=True)


@sprop("care_physio_bands", aspect=3.0, fill=1.0)
def physio_bands(c, color):
    """Rehab kit on the floor: a ribbed grey foam roller, a stack of flat loop bands in muted sand / sage / dusty blue, and a tube band with handles."""
    rng = c.rng
    ao(c, 0.0, 0.0, 2.7, 0.30, 0.55)
    # foam roller (horizontal cylinder, textured grid surface)
    r, rv = 0.31, 0.31
    base = (0.30, 0.34, 0.38)
    L, R = -1.38, 0.10
    stops = [(0.0, scale(base, 1.55)), (0.18, scale(base, 1.30)), (0.55, scale(base, 0.85)), (0.85, scale(base, 0.55)), (1.0, scale(base, 0.40))]
    _vbands_poly(c, [(L, rv - r), (R, rv - r), (R, rv + r), (L, rv + r)], stops)
    c.ellipse(R, rv, r * 0.36, r, scale(base, 0.50), lift=0.0)
    c.ellipse(R + 0.01, rv, r * 0.30, r * 0.90, scale(base, 1.15), lift=0.15)
    c.ellipse(R + 0.01, rv, r * 0.11, r * 0.34, scale(base, 0.45), lift=0.0)
    c.ellipse(L, rv, r * 0.16, r, scale(base, 1.45), lift=0.0, alpha=0.6)
    for k in range(13):                                            # ribs wrapping the roller
        x = L + 0.10 + k * 0.105
        craft.arc(c, x, rv, 0.03, r * 0.97, -90, 90, 0.007, scale(base, 0.45), 0.6, steps=8)
    for _ in range(30):                                            # foam pores
        c.ellipse(rng.uniform(L + 0.1, R - 0.08), rv + rng.uniform(-r * 0.85, r * 0.85), 0.006, 0.004, scale(base, rng.uniform(0.5, 1.5)), lift=0, alpha=0.5)
    soft_disc(c, -0.60, rv + r * 0.62, 0.62, 0.05, WHITE, 0.40, 1.1, add=True)
    soft_disc(c, -0.55, rv - r * 0.85, 0.70, 0.04, BLACK, 0.30, 1.2)
    # stack of loop bands
    for (u, v, cc) in ((0.78, 0.10, (0.58, 0.72, 0.58)), (0.84, 0.19, (0.88, 0.76, 0.52)), (0.74, 0.28, (0.50, 0.64, 0.82))):
        c.ellipse(u, v, 0.43, 0.15, scale(cc, 0.55), lift=0.0)
        c.ellipse(u, v + 0.02, 0.43, 0.15, cc, lift=0.18)
        c.ellipse(u + 0.01, v + 0.045, 0.33, 0.105, scale(cc, 0.62), lift=0.0)
        c.ellipse(u + 0.01, v + 0.055, 0.30, 0.085, scale(cc, 0.80), lift=0.0)
        soft_disc(c, u - 0.18, v + 0.07, 0.17, 0.020, WHITE, 0.50, 1.1, add=True)
    # tube band lying in front with two handles
    cc = (0.80, 0.44, 0.38)
    tp = [(-1.15 + k * 0.17, 0.045 + 0.030 * math.sin(k * 0.9)) for k in range(14)]
    for a, b in zip(tp, tp[1:]):
        c.line(a[0], a[1], b[0], b[1], 0.065, scale(cc, 0.55), 1.0)
    for a, b in zip(tp, tp[1:]):
        c.line(a[0], a[1] + 0.012, b[0], b[1] + 0.012, 0.044, cc, 1.0)
        c.line(a[0] - 0.01, a[1] + 0.024, b[0] - 0.01, b[1] + 0.024, 0.013, scale(cc, 1.55), 0.7)
    for (xx, vv) in (tp[0], tp[-1]):
        craft.hshade_box(c, xx, vv + 0.02, 0.085, 0.20, (0.30, 0.31, 0.34), (0.08, 0.08, 0.09), r=0.034)
        c.line(xx - 0.02, vv - 0.04, xx - 0.02, vv + 0.08, 0.012, WHITE, 0.30)


@niche("physio", "Physiotherapy centre", subjects=("care_physio_table",),
       strong=("physiotherapy", "physio", "physiotherapist", "physiotherapy clinic", "rehabilitation", "physical therapy", "back pain treatment",
               "sports injury", "physio clinic", "fisiotherapy", "फिजियोथेरेपी", "फिजियो", "पुनर्वास", "फिजियोथेरेपिस्ट"),
       weak=("physical", "exercise", "recovery", "spine", "posture", "chiropractic", "massage", "joint pain", "mobility"),
       avoid=("gym", "yoga"), accent="#2a9d8f", mood="cool", group="wellness")
def physio(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    slat = mix(P.accent_dark, P.wall_bot, 0.45)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # acoustic wood-slat wainscot below, daylight window and anatomy chart above, a hand rail and wall bars
        S.rect(1.0, 0.46, 14.0, 0.28, scale(slat, 0.8 if not dark else 0.55), lift=0.0)
        for k in range(120):
            u = -5.0 + k * 0.1
            S.rect(u, 0.46, 0.055, 0.28, scale(slat, 1.12 if k % 2 else 0.92), lift=0.0)
        S.rect(1.0, 0.322, 14.0, 0.014, (0.90, 0.78, 0.60) if not dark else (0.45, 0.38, 0.30), lift=0.0)
        S.window(0.40, 0.20, 0.62, 0.34, sky_top=(0.55, 0.76, 0.93), sky_bot=(0.82, 0.92, 0.98), frame=(0.95, 0.97, 0.98))
        S.rect(0.25, 0.19, 0.02, 0.34, (0.95, 0.97, 0.98), lift=0.0)
        S.rect(0.55, 0.19, 0.02, 0.34, (0.95, 0.97, 0.98), lift=0.0)
        for k in range(5):                                                                       # a plant on the sill and rooftops outside
            S.rect(0.18 + k * 0.12, 0.30, 0.09, 0.07 + 0.02 * (k % 3), (0.45, 0.58, 0.68), lift=0.0, alpha=0.7)
        S.glow(0.40, 0.24, 1.0, (0.85, 0.94, 1.0), 0.30 * gl, 1.7)
        for k in range(2):
            S.rect(1.78 + k * 0.30, 0.22, 0.025, 0.52, scale(WOOD, 0.95 if not dark else 0.5), lift=0.0)
        for k in range(9):
            S.rect(1.93, 0.00 + k * 0.058, 0.30, 0.014, scale(WOOD, 1.0 if not dark else 0.55), lift=0.0)
        S.rect(1.10, 0.17, 0.26, 0.30, (0.97, 0.98, 0.99) if not dark else (0.25, 0.3, 0.38), r=0.004, lift=0.0)       # anatomy chart
        S.rect(1.10, 0.17, 0.05, 0.24, (0.55, 0.60, 0.68) if not dark else (0.4, 0.5, 0.6), lift=0.0, alpha=0.8)
        for k in range(8):
            S.rect(1.10, 0.07 + k * 0.026, 0.12 - 0.006 * (k % 3), 0.009, (0.85, 0.6, 0.5), lift=0.0, alpha=0.8)
        S.rect(1.10, 0.17, 0.30, 0.34, (0.82, 0.86, 0.9) if not dark else (0.3, 0.35, 0.42), lift=0.0, alpha=0.0)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.42, [(0.85, 0.95, 1.0), (0.6, 0.9, 0.9)], 0.012, 0.04, 0.3 * gl)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # light maple floor, satin, with window light and a rubber exercise mat
    fl = mix(P.surface, (0.88, 0.78, 0.62), 0.5) if not dark else scale(P.surface, 0.7)
    S.wood(-5.0, 0.60, 7.0, 2.6, fl, plank=0.10, grain=0.45)
    for _ in range(40):                                                                       # staggered butt joints between boards
        S.line(*(lambda u, v: (u, v, u, v + 0.10))(S.rng.uniform(-0.5, 2.8), 0.60 + 0.10 * S.rng.randrange(0, 20)), 0.003, scale(fl, 0.62), 0.5)
    S.rect(1.0, 0.60, 14.0, 0.008, scale(fl, 0.5), lift=0.0)
    S.rect(1.0, 0.616, 14.0, 0.022, scale(slat, 0.8), lift=0.0)                                   # skirting
    S.soft(1.0, 0.92, 1.30, 0.34, (0.85, 0.94, 1.0), 0.20 * gl, 1.4, add=True)
    S.soft(0.98, 1.04, 0.55, 0.05, (0.5, 0.9, 0.85), 0.18 * gl, 1.3, add=True)                    # reflection of the table on the satin floor
    _spoly_stage(S, [(0.45, 0.66), (0.80, 0.66), (1.25, 1.35), (0.50, 1.35)], (0.85, 0.94, 1.0), 0.10 * gl)
    _spoly_stage(S, [(0.95, 0.66), (1.20, 0.66), (1.75, 1.35), (1.45, 1.35)], (0.85, 0.94, 1.0), 0.07 * gl)
    mat = scale(P.accent, 0.82 if not dark else 0.5)
    _spoly_stage(S, [(0.40, 0.90), (1.95, 0.90), (2.35, 1.16), (-0.05, 1.16)], scale(mat, 0.7))
    _spoly_stage(S, [(0.42, 0.915), (1.93, 0.915), (2.30, 1.15), (-0.01, 1.15)], mat)
    S.line(0.42, 0.915, 1.93, 0.915, 0.006, scale(mat, 1.3), 0.7)
    for k in range(26):                                                                       # textured rubber: seeded speckle
        S.circle(S.rng.uniform(0.2, 2.1), S.rng.uniform(0.93, 1.14), 0.003, scale(mat, S.rng.choice((0.8, 1.3))), alpha=0.5, lift=0, soft=0.5)
    S.put("care_physio_table", 0.94, 0.90, 0.39, color=P, subject=True, shadow_w=0.9, shadow_alpha=0.16)
    S.put("care_physio_ball", 0.55, 1.02, 0.30, color=P, shadow_w=0.30)
    S.put("care_physio_spine", 1.42, 1.00, 0.56, shadow_w=0.26)
    S.put("care_physio_bands", 1.02, 1.09, 0.20, shadow_w=0.5)
    S.focus("detail", 1.28, 0.80)
    if dark:                                    # practical light: ceiling spots on the floor and an LED strip under the table
        S.soft(1.06, 0.93, 0.7, 0.12, (0.5, 0.95, 0.9), 0.38, 1.5, add=True)
        S.soft(1.50, 0.90, 0.22, 0.08, (1.0, 0.9, 0.7), 0.25, 1.5, add=True)
        S.soft(0.70, 1.00, 0.3, 0.08, (0.6, 0.9, 1.0), 0.20, 1.5, add=True)
    with S.near():
        S.soft(0.45, 1.14, 0.35, 0.12, BLACK, 0.55, 1.0)
        S.circle(1.90, 0.66, 0.05, (0.8, 0.95, 1.0), alpha=0.30, lift=0)


# ====================================================================================== SKIN CLINIC
@sprop("care_skin_face", aspect=0.85, fill=1.0)
def skin_face(c, color):
    """A bust model with a spa headband and glowing, soft-lit skin: egg-shaped head, closed eyes, nose shading, tinted lips."""
    rng = c.rng
    skin = (0.90, 0.69, 0.57)
    acc = _pal(color, "accent", (0.85, 0.55, 0.7))
    hair = (0.17, 0.10, 0.08)
    ao(c, 0.0, 0.0, 0.8, 0.14, 0.5)
    soft_disc(c, 0.0, 0.66, 0.50, 0.55, (1.0, 0.78, 0.82), 0.22, 1.4, add=True)               # glow around the face
    # dark hair: a bun on top and the mass behind the head (gives the pale skin a contrasting outline)
    _ball(c, 0.025, 1.075, 0.075, hair, spec=0.35, dk=0.35)
    for k in range(9):
        craft.arc(c, 0.025, 1.075, 0.06 - k * 0.004, 0.06 - k * 0.004, 20 + k * 12, 140 + k * 12, 0.003, scale(hair, 2.2), 0.45, steps=5)
    _hpoly(c, [(-0.235, 0.62), (-0.24, 0.80), (-0.19, 0.96), (-0.07, 1.04), (0.07, 1.04), (0.19, 0.96), (0.24, 0.80), (0.235, 0.62), (0.20, 0.56), (-0.20, 0.56)],
           scale(hair, 1.5), scale(hair, 0.65), 0.03, smooth=2)
    # shoulders with a white towel wrap
    sh = [(-0.36, 0.0), (0.36, 0.0), (0.37, 0.09), (0.26, 0.19), (0.09, 0.25), (-0.09, 0.25), (-0.26, 0.19), (-0.37, 0.09)]
    _hpoly(c, sh, scale(skin, 1.04), scale(skin, 0.72), 0.04, power=1.2, smooth=2)
    tw = [(-0.37, 0.0), (0.37, 0.0), (0.375, 0.10), (0.25, 0.165), (0.05, 0.115), (-0.05, 0.115), (-0.25, 0.165), (-0.375, 0.10)]
    _hpoly(c, tw, (0.99, 0.98, 0.97), (0.78, 0.76, 0.76), 0.03, power=1.1, smooth=2)
    for k in range(6):
        x = -0.30 + k * 0.12
        c.line(x, 0.01, x + 0.03, 0.12, 0.003, (0.8, 0.78, 0.78), 0.4)
    # neck
    craft.hshade_box(c, 0.0, 0.31, 0.15, 0.20, scale(skin, 1.0), scale(skin, 0.70), r=0.03)
    soft_disc(c, 0.01, 0.40, 0.11, 0.05, BLACK, 0.34, 1.2)
    # head: egg shape, wider at the brow than the chin
    pts = []
    for i in range(40):
        th = 2 * math.pi * i / 40
        pts.append((0.205 * math.sin(th) * (1.0 + 0.10 * math.cos(th)), 0.67 + 0.29 * math.cos(th)))
    for sgn in (-1, 1):                                                  # ears
        c.ellipse(sgn * 0.205, 0.64, 0.028, 0.052, scale(skin, 0.80 if sgn > 0 else 0.95), lift=0.05)
    _hpoly(c, pts, scale(skin, 1.07), scale(skin, 0.80), 0.05, power=1.3)
    # modelling light: forehead and cheek highlights, shaded right side, blush
    soft_disc(c, -0.06, 0.84, 0.13, 0.075, WHITE, 0.30, 1.2, add=True)
    soft_disc(c, -0.10, 0.62, 0.08, 0.06, WHITE, 0.22, 1.2, add=True)
    soft_disc(c, 0.19, 0.64, 0.08, 0.24, (0.5, 0.25, 0.2), 0.34, 1.3)
    soft_disc(c, -0.115, 0.585, 0.065, 0.045, (1.0, 0.45, 0.5), 0.34, 1.2)
    soft_disc(c, 0.115, 0.585, 0.065, 0.045, (1.0, 0.45, 0.5), 0.30, 1.2)
    soft_disc(c, 0.02, 0.42, 0.10, 0.04, BLACK, 0.20, 1.4)                  # under the chin
    # closed eyes: lids, lashes, brows
    for sgn in (-1, 1):
        x = sgn * 0.085
        soft_disc(c, x, 0.715, 0.055, 0.025, (0.85, 0.5, 0.55), 0.30, 1.2)
        craft.arc(c, x, 0.708, 0.050, 0.020, 200, 340, 0.006, (0.30, 0.16, 0.14), 0.95, steps=8)
        for k in range(4):
            a = math.radians(210 + k * 30)
            c.line(x + math.cos(a) * 0.05, 0.708 + math.sin(a) * 0.02, x + math.cos(a) * 0.065, 0.708 + math.sin(a) * 0.036 - 0.004, 0.003, (0.25, 0.13, 0.12), 0.8)
        craft.arc(c, x + sgn * 0.005, 0.745, 0.060, 0.022, 45 if sgn < 0 else 95, 135 if sgn < 0 else 185, 0.011, (0.22, 0.14, 0.11), 0.9, steps=6)
    for _ in range(18):                                              # freckles and pores
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random())
        fx, fy = math.cos(a) * 0.16 * rr, 0.60 + math.sin(a) * 0.10 * rr
        c.ellipse(fx, fy, 0.004, 0.003, (0.62, 0.36, 0.28), lift=0, alpha=0.22)
    # nose
    c.line(0.0, 0.70, 0.004, 0.60, 0.010, WHITE, 0.12)
    soft_disc(c, 0.028, 0.62, 0.025, 0.06, (0.55, 0.28, 0.22), 0.30, 1.2)
    c.ellipse(0.0, 0.575, 0.036, 0.020, scale(skin, 0.90), lift=0.1)
    soft_disc(c, -0.008, 0.585, 0.016, 0.010, WHITE, 0.45, 1.0, add=True)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.020, 0.563, 0.009, 0.005, (0.45, 0.22, 0.2), lift=0)
    # lips
    c.ellipse(0.0, 0.497, 0.065, 0.020, (0.78, 0.30, 0.38), lift=0.1)
    c.ellipse(0.0, 0.478, 0.055, 0.022, (0.88, 0.40, 0.46), lift=0.12)
    c.line(-0.058, 0.489, 0.058, 0.489, 0.004, (0.5, 0.15, 0.2), 0.8)
    soft_disc(c, -0.015, 0.482, 0.025, 0.008, WHITE, 0.55, 1.0, add=True)
    # towel headband
    band = [(-0.215, 0.79), (-0.20, 0.92), (-0.10, 1.0), (0.0, 1.02), (0.10, 1.0), (0.20, 0.92), (0.215, 0.79), (0.185, 0.835), (0.10, 0.865), (0.0, 0.875),
            (-0.10, 0.865), (-0.185, 0.835)]
    bandc = mix(acc, (0.55, 0.20, 0.38), 0.45)                       # a deep rose terry headband: clear contrast against wall and skin
    _hpoly(c, band, scale(bandc, 1.25), scale(bandc, 0.62), 0.04, power=1.1, smooth=2)
    for k in range(10):                                              # terry loops
        a = math.radians(25 + k * 13)
        c.line(math.cos(a) * 0.185, 0.84 + math.sin(a) * 0.165, math.cos(a) * 0.205, 0.87 + math.sin(a) * 0.165, 0.004, scale(bandc, 1.5), 0.45)
    for k in range(5):
        x = -0.15 + k * 0.075
        c.ellipse(x, 0.93 + 0.045 * (1 - abs(x) / 0.2), 0.012, 0.007, mix(bandc, WHITE, 0.6), lift=0, alpha=0.7)
    soft_disc(c, -0.08, 0.97, 0.09, 0.03, WHITE, 0.55, 1.0, add=True)
    soft_disc(c, 0.0, 0.84, 0.20, 0.03, BLACK, 0.32, 1.2)
    for sgn in (-1, 1):                                              # loose wisps at the temples, gold hoop earring
        craft.strand(c, sgn * 0.20, 0.80, 0.07, 270 + sgn * 12, 0.004, hair, 0.9, 0.4)
        craft.arc(c, sgn * 0.205, 0.575, 0.016, 0.026, 0, 360, 0.004, (0.95, 0.78, 0.35), 0.95, steps=10)


def _dropper(c, u, h, w, liquid, cap, label=None, gold=True):
    """Glass dropper bottle with a rubber bulb: tinted liquid, pipette, label."""
    r = w / 2
    neck = r * 0.42
    sh = h * 0.60
    glass = liquid
    prof = [(r * 0.90, 0.0), (r, 0.02), (r, sh), (r * 0.80, sh + h * 0.07), (neck * 1.2, h * 0.76), (neck, h * 0.80)]
    c.ellipse(u, 0.01, r, r * TILT * 0.8, scale(glass, 0.35), lift=0)
    _spoly(c, [(u + rr, hh) for rr, hh in prof] + [(u - rr, hh) for rr, hh in reversed(prof)],
           [(0.0, scale(glass, 0.62)), (0.16, scale(glass, 1.25)), (0.45, scale(glass, 1.0)), (0.80, scale(glass, 0.72)), (0.92, scale(glass, 1.0)), (1.0, scale(glass, 0.6))], 0.04)
    # pipette inside
    c.rect(u + r * 0.05, sh * 0.5, neck * 0.5, sh * 0.95, WHITE, alpha=0.30, lift=0, r=neck * 0.2)
    soft_disc(c, u + r * 0.1, sh * 0.3, r * 0.6, sh * 0.2, WHITE, 0.22, 1.2, add=True)
    if label:
        c.rect(u, sh * 0.5, r * 1.3, sh * 0.35, (0.98, 0.97, 0.95), r=0.006, lift=0.04)
        c.rect(u, sh * 0.5 + sh * 0.1, r * 1.3, sh * 0.04, label, lift=0)
        c.rect(u, sh * 0.5 - sh * 0.05, r * 0.7, sh * 0.025, (0.6, 0.55, 0.55), lift=0, alpha=0.7)
    # collar and bulb
    collar = (0.88, 0.70, 0.35) if gold else (0.85, 0.86, 0.9)
    craft.hshade_box(c, u, h * 0.80 + h * 0.035, neck * 2.3, h * 0.07, scale(collar, 1.15), scale(collar, 0.55), r=0.006)
    bw = neck * 1.6
    c.rect(u, h * 0.80 + h * 0.14, bw * 2, h * 0.12, cap, r=bw * 0.9, lift=0.0)
    _hpoly(c, [(u - bw, h * 0.87), (u + bw, h * 0.87), (u + bw * 0.8, h * 0.97), (u + bw * 0.4, h * 1.03), (u - bw * 0.4, h * 1.03), (u - bw * 0.8, h * 0.97)],
           scale(cap, 1.5), scale(cap, 0.5), 0.05, smooth=2)
    soft_disc(c, u - bw * 0.4, h * 0.97, bw * 0.3, h * 0.04, WHITE, 0.55, 1.0, add=True)
    c.rect(u - r * 0.62, sh * 0.5, r * 0.10, sh * 0.8, WHITE, r=r * 0.05, lift=0, alpha=0.5)
    c.rect(u + r * 0.74, sh * 0.5, r * 0.04, sh * 0.7, scale(glass, 1.6), lift=0, alpha=0.35)


@sprop("care_skin_serums", aspect=1.35, fill=0.9)
def skin_serums(c, color):
    """Serum dropper bottles (rose, amber, aqua) beside a white cream jar with a gold lid."""
    acc = _pal(color, "accent", (0.85, 0.55, 0.7))
    ao(c, 0.0, 0.0, 1.1, 0.14, 0.45)
    c.ellipse(0.46, 0.015, 0.22, 0.05, BLACK, alpha=0.25, lift=0)
    # cream jar (right)
    jar = (0.97, 0.96, 0.95)
    _lathe(c, 0.46, 0.01, [(0.18, 0.0), (0.20, 0.02), (0.20, 0.22), (0.19, 0.26)], jar, kind="matte", rim=False)
    craft.hshade_box(c, 0.46, 0.30, 0.43, 0.075, (1.0, 0.88, 0.55), (0.55, 0.40, 0.14), r=0.02)
    c.ellipse(0.46, 0.335, 0.215, 0.215 * TILT, (0.98, 0.84, 0.50), lift=0.1)
    c.ellipse(0.46, 0.337, 0.185, 0.185 * TILT, (0.88, 0.70, 0.35), lift=0.18)
    soft_disc(c, 0.40, 0.345, 0.12, 0.03, WHITE, 0.6, 1.0, add=True)
    c.rect(0.46, 0.15, 0.20, 0.07, acc, r=0.008, lift=0.05, alpha=0.9)
    c.rect(0.46, 0.15, 0.14, 0.012, WHITE, lift=0, alpha=0.8)
    c.rect(0.46, 0.125, 0.10, 0.008, WHITE, lift=0, alpha=0.5)
    soft_disc(c, 0.37, 0.15, 0.03, 0.10, WHITE, 0.4, 1.1, add=True)
    # droppers
    _dropper(c, -0.40, 0.66, 0.22, (0.96, 0.62, 0.72), (0.12, 0.12, 0.13), label=acc)
    _dropper(c, -0.08, 0.86, 0.26, (0.88, 0.62, 0.22), (0.95, 0.93, 0.9), label=scale(acc, 0.8))
    _dropper(c, 0.20, 0.56, 0.20, (0.55, 0.82, 0.90), (0.12, 0.12, 0.13), label=mix(acc, WHITE, 0.2))
    # a liquid droplet on the surface
    craft.drip(c, -0.22, 0.014, 0.012, (0.88, 0.62, 0.22))


@sprop("care_skin_lamp", aspect=0.78, fill=1.0)
def skin_lamp(c, color):
    """A treatment magnifier ring-lamp: weighted base, pole, and a round LED ring around a glass lens."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.12, 0.55)
    steel = (0.90, 0.91, 0.93)
    c.ellipse(0.04, 0.02, 0.22, 0.22 * TILT, scale(steel, 0.55), lift=0)
    c.ellipse(0.04, 0.04, 0.20, 0.20 * TILT, steel, lift=0.25)
    soft_disc(c, -0.04, 0.05, 0.12, 0.03, WHITE, 0.6, 1.0, add=True)
    _spoly(c, [(0.015, 0.05), (0.07, 0.05), (0.07, 0.50), (0.015, 0.50)], _bands(steel, "metal"), 0.0)
    # ring housing: shadow offset, outer white ring, LED band, glass lens
    cx, cy, R = 0.10, 0.74, 0.27
    c.ellipse(cx + 0.02, cy - 0.015, R, R, (0.45, 0.46, 0.5), lift=0)
    c.ellipse(cx, cy, R, R, scale(steel, 1.02), lift=0.18)
    c.ellipse(cx, cy, R * 0.90, R * 0.90, (0.99, 0.97, 0.9), lift=0.0)
    for k in range(28):
        a = 2 * math.pi * k / 28
        c.ellipse(cx + math.cos(a) * R * 0.84, cy + math.sin(a) * R * 0.84, 0.012, 0.012, (1.0, 0.96, 0.78), lift=0, alpha=0.95)
    soft_disc(c, cx, cy, R * 1.05, R * 1.05, (1.0, 0.94, 0.75), 0.30, 1.6, add=True)
    c.ellipse(cx, cy, R * 0.74, R * 0.74, scale(steel, 0.85), lift=0.0)
    c.ellipse(cx, cy, R * 0.70, R * 0.70, (0.74, 0.86, 0.92), lift=0.20)
    soft_disc(c, cx - 0.06, cy + 0.07, R * 0.45, R * 0.28, WHITE, 0.55, 1.1, 30, add=True)
    soft_disc(c, cx + 0.07, cy - 0.07, R * 0.4, R * 0.35, (0.2, 0.35, 0.45), 0.25, 1.3)
    craft.arc(c, cx, cy, R * 0.66, R * 0.66, 120, 200, 0.010, WHITE, 0.7, steps=8)
    c.ellipse(0.045, 0.50, 0.04, 0.04, scale(steel, 0.7), lift=0.3)


@sprop("care_skin_cotton", aspect=1.1, fill=0.7)
def skin_cotton(c, color):
    """A glass jar heaped with cotton balls and a small stack of round cotton pads."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.14, 0.45)
    # pads stack
    for k in range(5):
        c.ellipse(0.40, 0.03 + k * 0.022, 0.19, 0.19 * TILT, scale(WHITE, 0.82), lift=0)
        c.ellipse(0.40, 0.04 + k * 0.022, 0.19, 0.19 * TILT, (0.98, 0.97, 0.96) if k % 2 else (0.95, 0.94, 0.93), lift=0.08)
    soft_disc(c, 0.36, 0.17, 0.12, 0.025, WHITE, 0.6, 1.0, add=True)
    # jar
    glass = (0.82, 0.90, 0.92)
    c.ellipse(-0.18, 0.02, 0.26, 0.26 * TILT, scale(glass, 0.5), lift=0)
    # cotton heap behind glass
    for _ in range(26):
        x, y = rng.uniform(-0.36, 0.0), rng.uniform(0.05, 0.40)
        r = rng.uniform(0.04, 0.065)
        c.ellipse(x, y, r, r * 0.9, scale(WHITE, rng.uniform(0.84, 0.97)), lift=0.12, alpha=0.9)
        soft_disc(c, x - r * 0.25, y + r * 0.3, r * 0.6, r * 0.5, WHITE, 0.45, 1.0)
    craft.hshade_box(c, -0.18, 0.24, 0.54, 0.44, WHITE, WHITE, r=0.04, alpha=0.0)
    c.rect(-0.18, 0.22, 0.52, 0.40, glass, r=0.05, lift=0.0, alpha=0.20)
    c.rect(-0.40, 0.23, 0.035, 0.34, WHITE, r=0.015, lift=0, alpha=0.55)
    c.rect(-0.02, 0.23, 0.02, 0.32, WHITE, r=0.01, lift=0, alpha=0.25)
    for _ in range(5):                                       # cotton above the rim
        x = rng.uniform(-0.34, -0.02)
        r = rng.uniform(0.045, 0.06)
        c.ellipse(x, 0.46 + rng.uniform(0, 0.03), r, r * 0.9, (0.97, 0.97, 0.96), lift=0.1)
    craft.hshade_box(c, -0.18, 0.435, 0.56, 0.035, (0.95, 0.80, 0.50), (0.60, 0.44, 0.2), r=0.012)
    soft_disc(c, -0.30, 0.435, 0.12, 0.01, WHITE, 0.6, 1.0, add=True)


@niche("skin-clinic", "Skin clinic / dermatologist", subjects=("care_skin_face",),
       strong=("skin clinic", "dermatologist", "dermatology", "acne treatment", "pigmentation", "skin care clinic", "skin treatment", "laser hair removal",
               "skin specialist", "tvacha", "chehre ka ilaj", "त्वचा रोग", "त्वचा विशेषज्ञ", "स्किन क्लिनिक", "मुंहासे"),
       weak=("skin", "facial", "serum", "glow", "cosmetic", "aesthetic", "hair removal", "त्वचा", "cream"),
       avoid=("salon", "barber"), accent="#d98cb3", mood="light", group="wellness")
def skin_clinic(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    pink = mix(P.accent_light, (1.0, 0.82, 0.86), 0.4)
    wt = mix(P.wall_top, pink, 0.55 if not dark else 0.2)
    wb = mix(P.wall_bot, pink, 0.65 if not dark else 0.2)
    sage = (0.62, 0.74, 0.66) if not dark else (0.18, 0.28, 0.25)
    with S.far():
        S.wall(wt, wb, 0.58)
        # sage zellige-tile wainscot, a big backlit mirror in a brass ring, glass shelves with bottles, plant leaves
        S.rect(1.0, 0.505, 14.0, 0.15, sage, lift=0.0)
        for j in range(3):
            for k in range(96):
                S.rect(-4.0 + k * 0.09 + (0.045 if j % 2 else 0.0), 0.455 + j * 0.05, 0.085, 0.046, scale(sage, S.rng.uniform(0.90, 1.10)), lift=0.0)
        S.rect(1.0, 0.43, 14.0, 0.012, (0.92, 0.76, 0.42) if not dark else (0.5, 0.4, 0.25), lift=0.0)
        S.glow(1.30, 0.22, 0.75, (1.0, 0.86, 0.88), 0.50 * gl, 1.6)
        S.circle(1.30, 0.22, 0.285, (0.92, 0.74, 0.40) if not dark else (0.6, 0.45, 0.25), lift=0.1)
        S.circle(1.30, 0.22, 0.255, (0.90, 0.94, 0.96) if not dark else (0.40, 0.45, 0.55), lift=0.12)
        S.soft(1.22, 0.16, 0.14, 0.18, WHITE, 0.45, 1.2, add=True)
        for v in (0.14, 0.34):
            S.rect(0.30, v + 0.02, 0.50, 0.014, (0.92, 0.76, 0.42) if not dark else (0.5, 0.42, 0.3), lift=0.0)
            for k in range(7):
                u = 0.08 + k * 0.07 + S.rng.uniform(-0.01, 0.01)
                h = S.rng.uniform(0.05, 0.12)
                col = S.rng.choice((P.accent, (0.97, 0.9, 0.85), P.accent_dark, (0.85, 0.92, 0.95), (0.98, 0.98, 0.98)))
                S.rect(u, v - h / 2 + 0.014, 0.034, h, col, r=0.01, lift=0.1)
            S.glow(0.30, v + 0.02, 0.35, (1.0, 0.92, 0.85), 0.20 * gl, 1.8)
        for k in range(5):
            S.ellipse(1.92 + S.rng.uniform(-0.04, 0.05), 0.36 - k * 0.07, 0.02, 0.09, (0.35, 0.55, 0.38), angle=S.rng.uniform(-40, 40), lift=0.1)
        S.bokeh(7, 0.0, 0.05, 2.0, 0.4, [(1.0, 0.85, 0.88), (1.0, 0.95, 0.85)], 0.012, 0.04, 0.3 * gl)
        S.floor(0.58, P.floor_top, P.floor_bot)
    # rose terrazzo counter: a mid-tone surface with chips (contrast against the pale wall), a light pool and a sheen
    mt = (0.84, 0.70, 0.67) if not dark else (0.24, 0.17, 0.21)
    mb = (0.70, 0.55, 0.54) if not dark else (0.12, 0.08, 0.11)
    S.floor(0.58, mt, mb)
    chips = ((0.98, 0.95, 0.93), (0.95, 0.84, 0.82), (0.55, 0.62, 0.56), (0.36, 0.28, 0.30), (0.90, 0.72, 0.52))
    if dark:
        chips = tuple(scale(ch, 0.45) for ch in chips)
    for _ in range(200):
        u = S.rng.uniform(-0.2, 2.4)
        v = S.rng.uniform(0.62, 1.30)
        r = S.rng.uniform(0.0025, 0.0065) * (0.7 + (v - 0.58) * 1.0)
        S.ellipse(u, v, r * 1.5, r, chips[S.rng.randrange(5)], angle=S.rng.uniform(0, 180), lift=0.0, alpha=0.60, soft=0.5)
    S.rect(1.0, 0.58, 14.0, 0.010, scale(mb, 0.55), lift=0.0)
    S.rect(1.0, 0.592, 14.0, 0.008, (0.95, 0.80, 0.50) if not dark else (0.5, 0.4, 0.25), lift=0.0)
    S.soft(1.1, 0.82, 1.0, 0.16, (1.0, 0.92, 0.9), 0.24 if not dark else 0.14, 1.4, add=True)
    S.soft(1.30, 0.78, 0.35, 0.10, (1.0, 0.85, 0.88), 0.18 if not dark else 0.35, 1.5, add=True)
    S.put("care_skin_lamp", 1.40, 0.86, 0.46, shadow_w=0.26)
    S.put("care_skin_face", 1.08, 0.93, 0.56, color=P, subject=True, shadow_w=0.5)
    S.put("care_skin_serums", 0.76, 0.96, 0.28, color=P, shadow_w=0.55)
    S.put("care_skin_cotton", 1.28, 1.06, 0.17, shadow_w=0.3)
    S.focus("detail", 0.90, 0.80)
    if dark:                                    # practical light: pink glow from the mirror and a spot on the face
        S.glow(1.08, 0.60, 0.5, (1.0, 0.7, 0.8), 0.22, 1.8)
    with S.near():
        S.circle(0.45, 1.08, 0.07, (1.0, 0.85, 0.88), alpha=0.35, lift=0)
        S.poly([(1.85, 1.02), (2.05, 0.96), (2.12, 1.12), (1.88, 1.14)], mix(P.accent_light, WHITE, 0.5), alpha=0.85)


# ====================================================================================== EYE CLINIC
@sprop("care_eye_phoropter", aspect=1.1, fill=1.0)
def eye_phoropter(c, color):
    """A phoropter (refractor) on its mounting arm: dark housing, two glowing lens apertures with rotating lens wheels, dials and a pole."""
    rng = c.rng
    steel = (0.66, 0.70, 0.76)
    body = (0.34, 0.37, 0.43)
    ao(c, 0.12, 0.0, 0.95, 0.14, 0.6)
    # base, pole, articulated arm
    c.ellipse(0.42, 0.025, 0.20, 0.20 * TILT, (0.08, 0.08, 0.10), lift=0)
    c.ellipse(0.42, 0.045, 0.175, 0.175 * TILT, (0.30, 0.32, 0.37), lift=0.3)
    soft_disc(c, 0.36, 0.055, 0.10, 0.025, WHITE, 0.5, 1.0, add=True)
    _spoly(c, [(0.395, 0.05), (0.445, 0.05), (0.445, 0.88), (0.395, 0.88)], _bands(steel, "metal"), 0.0)
    _spoly(c, [(0.04, 0.885), (0.45, 0.885), (0.45, 0.93), (0.04, 0.93)], [(0.0, scale(steel, 1.1)), (0.5, scale(steel, 0.8)), (1.0, scale(steel, 0.45))], 0.0)
    c.rect(0.25, 0.925, 0.4, 0.006, WHITE, alpha=0.5, lift=0)
    c.ellipse(0.43, 0.905, 0.05, 0.05, scale(steel, 0.8), lift=0.3)
    gloss(c, 0.41, 0.92, 0.02, 0.015, 0, 0.6)
    _spoly(c, [(0.03, 0.78), (0.085, 0.78), (0.085, 0.89), (0.03, 0.89)], _bands(steel, "metal"), 0.0)
    # housing: a solid block (front, lit top and shaded right side) so it reads as an instrument, not a face
    soft_disc(c, 0.0, 0.46, 0.5, 0.04, BLACK, 0.4, 1.2)
    hx, hy, hw_, hh_ = -0.12, 0.62, 0.80, 0.32
    _hpoly(c, [(hx + hw_ / 2, hy + hh_ / 2), (hx + hw_ / 2 + 0.07, hy + hh_ / 2 + 0.05), (hx + hw_ / 2 + 0.07, hy - hh_ / 2 + 0.05), (hx + hw_ / 2, hy - hh_ / 2)],
           scale(body, 0.62), scale(body, 0.30), 0.0)
    _hpoly(c, [(hx - hw_ / 2, hy + hh_ / 2), (hx + hw_ / 2, hy + hh_ / 2), (hx + hw_ / 2 + 0.07, hy + hh_ / 2 + 0.05), (hx - hw_ / 2 + 0.07, hy + hh_ / 2 + 0.05)],
           scale(body, 1.75), scale(body, 1.25), 0.0)
    craft.hshade_box(c, hx, hy, hw_, hh_, scale(body, 1.35), scale(body, 0.55), r=0.07)
    c.rect(hx, 0.765, 0.74, 0.012, scale(body, 2.0), lift=0, alpha=0.6, r=0.006)
    c.rect(hx, 0.49, 0.74, 0.016, BLACK, lift=0, alpha=0.4, r=0.006)
    # forehead rest on a rod above the nose bridge, nose bridge block
    c.line(hx, 0.78, hx, 0.99, 0.020, _bands(steel, "metal")[2][1], 1.0)
    craft.hshade_box(c, hx, 1.00, 0.15, 0.05, (0.20, 0.20, 0.22), (0.05, 0.05, 0.06), r=0.022)
    soft_disc(c, hx - 0.03, 1.015, 0.05, 0.012, WHITE, 0.5, 1.0, add=True)
    c.rect(hx, 0.62, 0.10, 0.16, scale(body, 0.8), r=0.015, lift=0.2)
    # two lens tubes: a visible tube wall, steel front ring with graduations, dark coated glass with a window reflection (no glowing "eyes")
    for ex in (-0.31, 0.07):
        c.ellipse(ex + 0.016, 0.600, 0.120, 0.120, (0.03, 0.03, 0.04), lift=0)
        c.ellipse(ex, 0.615, 0.121, 0.121, scale(steel, 0.40), lift=0.0)
        c.ellipse(ex, 0.617, 0.112, 0.112, scale(steel, 0.95), lift=0.3)
        c.ellipse(ex, 0.615, 0.094, 0.094, (0.07, 0.09, 0.12), lift=0)
        c.ellipse(ex, 0.615, 0.082, 0.082, (0.10, 0.17, 0.22), lift=0.15)
        soft_disc(c, ex + 0.03, 0.585, 0.065, 0.055, (0.25, 0.55, 0.62), 0.55, 1.4, add=True)
        poly = [(ex - 0.05, 0.665), (ex - 0.03, 0.68), (ex + 0.04, 0.57), (ex + 0.02, 0.555)]
        c.poly([(ex + (x - ex) * 0.98, 0.615 + (y - 0.615) * 0.98) for x, y in poly], (0.75, 0.88, 0.95), alpha=0.16, lift=0)
        for k in range(24):                                       # lens wheel graduations
            a = math.radians(k * 15)
            r1 = 0.098 if k % 2 == 0 else 0.104
            c.line(ex + math.cos(a) * r1, 0.615 + math.sin(a) * r1, ex + math.cos(a) * 0.110, 0.615 + math.sin(a) * 0.110, 0.0026, (0.12, 0.12, 0.14), 0.75)
        craft.arc(c, ex, 0.615, 0.104, 0.104, 115, 190, 0.005, WHITE, 0.45, steps=8)
        # Risley dial on top of each tube: a knurled wheel
        craft.hshade_box(c, ex, 0.806, 0.12, 0.05, scale(steel, 1.25), scale(steel, 0.45), r=0.016)
        for k in range(9):
            c.line(ex - 0.048 + k * 0.012, 0.784, ex - 0.048 + k * 0.012, 0.828, 0.002, scale(steel, 0.35), 0.6)
        c.ellipse(ex, 0.488, 0.052, 0.020, scale(steel, 0.8), lift=0.3)
    # side knobs, a cross-cylinder lever and measurement marks
    for kx, ky in ((-0.51, 0.66), (0.28, 0.66)):
        c.ellipse(kx, ky, 0.042, 0.042, scale(steel, 0.9), lift=0.35)
        c.ellipse(kx, ky, 0.026, 0.026, scale(steel, 0.5), lift=0.2)
        c.line(kx, ky - 0.03, kx, ky + 0.03, 0.003, WHITE, 0.6)
    c.line(-0.12, 0.515, -0.12, 0.44, 0.012, scale(steel, 0.8), 1.0)
    c.ellipse(-0.12, 0.435, 0.026, 0.026, (0.75, 0.2, 0.18), lift=0.3)
    for k in range(10):
        c.line(-0.46 + k * 0.016, 0.5, -0.46 + k * 0.016, 0.5 + (0.016 if k % 5 == 0 else 0.009), 0.002, (0.9, 0.92, 0.95), 0.7)


@sprop("care_eye_chart", aspect=0.62, fill=1.0)
def eye_chart(c, color):
    """A wall-mounted illuminated Snellen chart: white face, rows of letters getting smaller, dark frame, glow."""
    soft_disc(c, 0.0, 0.5, 0.65, 0.65, (0.9, 0.96, 1.0), 0.30, 1.6, add=True)
    c.rect(0.0, 0.5, 0.64, 0.94, (0.12, 0.13, 0.15), r=0.02, lift=0.1)
    c.rect(0.0, 0.5, 0.58, 0.88, (0.97, 0.98, 0.99), r=0.012, lift=0.0)
    soft_disc(c, 0.0, 0.5, 0.30, 0.44, WHITE, 0.4, 1.4, add=True)
    rows = (("E", 0.20), ("F P", 0.15), ("T O Z", 0.115), ("L P E D", 0.088), ("P E C F D", 0.066), ("E D F C Z P", 0.05), ("F E L O P Z D", 0.038))
    v = 0.86
    for txt, h in rows:
        v -= h * 0.62
        c.text(txt, 0.0, v, h * 0.7, (0.05, 0.05, 0.07), 0.2)
        v -= h * 0.62
    c.rect(0.0, 0.02, 0.2, 0.01, (0.4, 0.4, 0.45), lift=0)


@sprop("care_eye_model", aspect=0.95, fill=1.0)
def eye_model(c, color):
    """An anatomical eye model on a stand: sclera with blood vessels, blue iris with pupil, cornea highlight, muscles and optic nerve."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.12, 0.55)
    # stand: foot, neck, cradle ring
    c.ellipse(0.0, 0.025, 0.22, 0.22 * TILT, (0.06, 0.06, 0.08), lift=0)
    c.ellipse(0.0, 0.045, 0.20, 0.20 * TILT, (0.20, 0.21, 0.25), lift=0.3)
    _spoly(c, [(-0.035, 0.05), (0.035, 0.05), (0.035, 0.22), (-0.035, 0.22)], _bands((0.7, 0.72, 0.78), "metal"), 0.0)
    cx, cy, R = 0.0, 0.58, 0.34
    # optic nerve and muscles (behind / on the sphere)
    craft.hshade_box(c, 0.36, 0.50, 0.16, 0.12, (1.0, 0.92, 0.62), (0.7, 0.58, 0.30), r=0.04)
    c.ellipse(0.44, 0.50, 0.03, 0.06, (0.8, 0.66, 0.36), lift=0.1)
    _ball(c, cx, cy, R, (0.97, 0.94, 0.88), spec=0.35, dk=0.35)
    # blood vessels
    for _ in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(0.10, 0.30)
        x0, y0 = cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.95
        if (x0 - cx) ** 2 + (y0 - cy) ** 2 > (R * 0.92) ** 2:
            continue
        craft.strand(c, x0, y0, rng.uniform(0.05, 0.12), math.degrees(a) + rng.uniform(-40, 40), 0.003, (0.75, 0.15, 0.15), 0.55, 0.6)
    # extra-ocular muscle bands across the top right
    craft.arc(c, cx, cy, R * 0.93, R * 0.93, 30, 85, 0.045, (0.72, 0.28, 0.28), 0.85, steps=8)
    craft.arc(c, cx, cy, R * 0.93, R * 0.93, 95, 130, 0.040, (0.72, 0.28, 0.28), 0.85, steps=6)
    # iris / pupil / cornea, turned a little to the left
    ix, iy = -0.10, 0.58
    c.ellipse(ix, iy, 0.150, 0.178, (0.18, 0.24, 0.36), lift=0)                           # limbal ring
    c.ellipse(ix, iy, 0.140, 0.168, (0.36, 0.58, 0.82), lift=0.1)
    for k in range(30):                                                                      # radial iris fibres
        a = 2 * math.pi * k / 30
        c.line(ix + math.cos(a) * 0.05, iy + math.sin(a) * 0.06, ix + math.cos(a) * 0.135, iy + math.sin(a) * 0.162, 0.004,
               (0.65, 0.82, 0.95) if k % 2 else (0.18, 0.34, 0.58), 0.55)
    c.ellipse(ix, iy, 0.06, 0.072, (0.02, 0.02, 0.03), lift=0)
    c.ellipse(ix, iy, 0.075, 0.09, (0.8, 0.6, 0.2), alpha=0.0, lift=0)
    soft_disc(c, ix, iy, 0.17, 0.2, (0.8, 0.9, 1.0), 0.18, 1.3, add=True)
    soft_disc(c, ix - 0.05, iy + 0.07, 0.07, 0.055, WHITE, 0.9, 1.0, 35, add=True)
    soft_disc(c, ix + 0.05, iy - 0.06, 0.03, 0.02, WHITE, 0.55, 1.0, add=True)
    craft.arc(c, ix, iy, 0.15, 0.178, 110, 190, 0.007, WHITE, 0.45, steps=8)


@sprop("care_eye_lenses", aspect=3.0, fill=0.32)
def eye_lenses(c, color):
    """An open trial-lens case: felt-lined tray with rows of round lenses in metal rims, front lid edge."""
    rng = c.rng
    wood = (0.18, 0.13, 0.10)
    ao(c, 0.0, 0.0, 1.0, 0.16, 0.55)
    top = [(-0.47, 0.095), (0.47, 0.095), (0.42, 0.30), (-0.42, 0.30)]
    _vpoly(c, top, (0.22, 0.24, 0.30), (0.10, 0.11, 0.15))
    craft.hshade_box(c, 0.0, 0.055, 0.96, 0.075, scale(wood, 1.8), scale(wood, 0.8), r=0.014)
    c.rect(0.0, 0.09, 0.95, 0.008, (0.75, 0.6, 0.35), lift=0, alpha=0.8)
    c.line(-0.47, 0.095, -0.42, 0.30, 0.012, scale(wood, 1.3), 1.0)
    c.line(0.47, 0.095, 0.42, 0.30, 0.012, scale(wood, 1.0), 1.0)
    c.line(-0.42, 0.30, 0.42, 0.30, 0.012, scale(wood, 1.0), 1.0)
    for ri, (v, sc) in enumerate(((0.135, 1.0), (0.20, 0.88), (0.258, 0.78))):
        n = 9
        half = (0.43 - ri * 0.012)
        for k in range(n):
            u = -half + (2 * half) * (k + 0.5) / n
            r = 0.030 * sc
            col = ((0.78, 0.86, 0.95), (0.95, 0.80, 0.85), (0.8, 0.95, 0.85))[(k + ri) % 3]
            c.ellipse(u, v, r * 1.12, r * 0.62, (0.05, 0.05, 0.06), lift=0)
            c.ellipse(u, v + 0.002, r * 1.05, r * 0.58, (0.78, 0.80, 0.84), lift=0.3)
            c.ellipse(u, v + 0.004, r * 0.80, r * 0.44, col, lift=0.2)
            soft_disc(c, u - r * 0.3, v + 0.01, r * 0.5, r * 0.2, WHITE, 0.8, 1.0, add=True)
            c.rect(u + r * 1.2, v, r * 0.4, 0.006, (0.8, 0.8, 0.85), lift=0, alpha=0.8)


@sprop("care_eye_drops", aspect=0.85, fill=1.0)
def eye_drops(c, color):
    """A small white eye-drops bottle with a blue tip cap, standing in front of its carton."""
    acc = _pal(color, "accent", (0.23, 0.48, 0.84))
    ao(c, 0.0, 0.0, 0.8, 0.12, 0.5)
    craft.hshade_box(c, 0.20, 0.36, 0.30, 0.72, scale(acc, 1.15), scale(acc, 0.55), r=0.012)
    c.rect(0.20, 0.50, 0.30, 0.24, (0.97, 0.98, 1.0), lift=0.0, alpha=0.9)
    c.ellipse(0.20, 0.50, 0.075, 0.075, scale(acc, 0.9), lift=0.2)
    c.ellipse(0.20, 0.50, 0.035, 0.05, WHITE, lift=0.0)
    c.ellipse(0.20, 0.50, 0.016, 0.016, (0.1, 0.1, 0.12), lift=0)
    c.rect(0.20, 0.28, 0.22, 0.012, WHITE, lift=0, alpha=0.8)
    c.rect(0.20, 0.25, 0.15, 0.008, WHITE, lift=0, alpha=0.6)
    soft_disc(c, 0.09, 0.40, 0.02, 0.28, WHITE, 0.25, 1.1, add=True)
    _lathe(c, -0.16, 0.0, [(0.095, 0.0), (0.105, 0.03), (0.105, 0.34), (0.08, 0.40), (0.05, 0.42)], (0.96, 0.97, 0.98), kind="matte", rim=False)
    craft.hshade_box(c, -0.16, 0.45, 0.10, 0.06, scale(acc, 1.3), scale(acc, 0.6), r=0.01)
    _hpoly(c, [(-0.205, 0.48), (-0.115, 0.48), (-0.135, 0.585), (-0.185, 0.585)], scale(acc, 1.35), scale(acc, 0.65), 0.04)
    c.ellipse(-0.16, 0.585, 0.025, 0.012, scale(acc, 1.5), lift=0.2)
    c.rect(-0.16, 0.20, 0.13, 0.10, acc, r=0.006, lift=0.1, alpha=0.9)
    c.rect(-0.16, 0.20, 0.08, 0.012, WHITE, lift=0, alpha=0.8)
    soft_disc(c, -0.21, 0.24, 0.018, 0.14, WHITE, 0.5, 1.1, add=True)


@niche("eye-clinic", "Eye clinic / eye hospital", subjects=("care_eye_phoropter",),
       strong=("eye clinic", "eye hospital", "ophthalmologist", "ophthalmology", "cataract", "lasik", "eye doctor", "eye specialist", "eye checkup",
               "eye care", "aankhon ka hospital", "netra", "आँखों का अस्पताल", "आंखों का अस्पताल", "नेत्र", "मोतियाबिंद", "नेत्र रोग"),
       weak=("vision", "retina", "eye test", "glaucoma", "eyesight", "optometrist", "optometry", "eye", "आंख", "आँख"),
       avoid=("optical store", "spectacles", "eyeglasses shop"), accent="#3a7bd5", mood="cool", group="wellness")
def eye_clinic(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # ceiling light panel, window blinds on the left, framed anatomy print
        S.glow(1.05, -0.02, 0.9, (0.9, 0.96, 1.0), 0.40 * gl, 1.6)
        S.window(0.30, 0.27, 0.38, 0.40, sky_top=(0.70, 0.84, 0.96), sky_bot=(0.92, 0.97, 1.0), frame=(0.92, 0.95, 0.97), bars=False)
        for k in range(8):
            S.rect(0.30, 0.10 + k * 0.045, 0.37, 0.020, (0.86, 0.9, 0.95) if not dark else (0.3, 0.36, 0.46), lift=0.0, alpha=0.95)
        S.glow(0.30, 0.28, 0.8, (0.8, 0.92, 1.0), 0.26 * gl, 1.7)
        S.rect(0.64, 0.26, 0.22, 0.28, (0.95, 0.96, 0.98) if not dark else (0.22, 0.27, 0.36), r=0.004, lift=0.0)
        S.circle(0.64, 0.26, 0.07, P.accent_light if not dark else P.accent, lift=0.1)
        S.circle(0.64, 0.26, 0.035, P.accent_dark, lift=0.0)
        S.bokeh(7, 0.0, 0.08, 2.0, 0.5, [(0.85, 0.95, 1.0), (0.7, 0.85, 1.0)], 0.012, 0.04, 0.3 * gl)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # exam desk: glossy walnut top with a pale front edge band, window reflections and the lens glow spilling onto it
    wal = (0.52, 0.36, 0.25) if not dark else (0.22, 0.15, 0.12)
    S.wood(-5.0, 0.60, 7.0, 2.6, wal, plank=0.17, grain=0.45)
    S.rect(1.0, 0.60, 14.0, 0.010, scale(wal, 0.45), lift=0.0)
    S.rect(1.0, 0.612, 14.0, 0.008, (0.95, 0.92, 0.86) if not dark else (0.5, 0.52, 0.58), alpha=0.7, lift=0.0)
    _spoly_stage(S, [(0.30, 0.64), (0.75, 0.64), (1.20, 1.4), (0.30, 1.4)], (0.85, 0.94, 1.0), 0.08 * gl)          # window light on the varnish
    _spoly_stage(S, [(1.05, 0.64), (1.40, 0.64), (2.10, 1.4), (1.55, 1.4)], (0.85, 0.94, 1.0), 0.05 * gl)
    S.soft(1.1, 0.80, 0.95, 0.14, (0.85, 0.94, 1.0), 0.20 if not dark else 0.10, 1.4, add=True)
    S.put("care_eye_chart", 1.40, 0.565, 0.38, shadow=False)
    S.put("care_eye_phoropter", 1.02, 0.94, 0.66, subject=True, shadow_w=0.6)
    S.put("care_eye_model", 0.68, 1.00, 0.27, shadow_w=0.28)
    S.put("care_eye_lenses", 1.22, 1.06, 0.12, shadow_w=0.40)
    S.put("care_eye_drops", 0.90, 1.07, 0.12, color=P, shadow_w=0.2)
    S.focus("detail", 1.00, 0.70)
    S.soft(1.02, 0.94, 0.30, 0.10, (0.45, 0.85, 1.0), 0.20 * gl, 1.6, add=True)            # lens glow spilling onto the desk
    S.soft(1.02, 1.00, 0.55, 0.05, (0.8, 0.9, 1.0), 0.14 * gl, 1.3, add=True)               # reflection of the instrument in the varnish
    with S.near():
        S.soft(0.46, 1.12, 0.35, 0.12, BLACK, 0.5, 1.0)
        S.circle(1.88, 0.62, 0.06, (0.8, 0.92, 1.0), alpha=0.30, lift=0)


# ====================================================================================== OPTICAL STORE
def _specs(c, u, v, w, frame, tint=(0.80, 0.90, 0.95), kind="rect", sun=False, alpha=0.5):
    """A pair of spectacles seen from the front, base centre (u, v), total width w: frame, tinted glass with reflections, bridge, pads, temples."""
    lw = w * 0.43
    lh = lw * (0.80 if kind in ("rect", "cat") else 0.92)
    gap = w * 0.11
    t = max(0.006, w * 0.045)
    cy = v + lh / 2
    for sgn in (-1, 1):                                                  # temples (arms) going back
        c.line(u + sgn * (lw + gap / 2), cy + lh * 0.30, u + sgn * (lw + gap / 2 + w * 0.07), cy + lh * 0.36, t * 0.8, scale(frame, 0.6), 0.9)
    for sgn in (-1, 1):
        lu = u + sgn * (lw / 2 + gap / 2)
        if kind == "round":
            c.ellipse(lu, cy, lw / 2, lh / 2, frame, lift=0.2)
            c.ellipse(lu, cy, lw / 2 - t, lh / 2 - t, tint, lift=0.1, alpha=alpha if not sun else 0.95)
        elif kind == "cat":
            c.rect(lu, cy, lw, lh, frame, r=lh * 0.42, lift=0.2)
            c.rect(lu + sgn * lw * 0.05, cy - lh * 0.02, lw - 2 * t, lh - 2 * t, tint, r=lh * 0.38, lift=0.1, alpha=alpha if not sun else 0.95)
        else:
            c.rect(lu, cy, lw, lh, frame, r=lh * 0.30, lift=0.2)
            c.rect(lu, cy, lw - 2 * t, lh - 2 * t, tint, r=lh * 0.26, lift=0.1, alpha=alpha if not sun else 0.95)
        if sun:                                                          # gradient lens: darker at the top
            c.rect(lu, cy + lh * 0.18, lw - 2.4 * t, lh * 0.45, BLACK, r=lh * 0.2, lift=0, alpha=0.30)
        c.line(lu - lw * 0.28, cy + lh * 0.22, lu - lw * 0.05, cy + lh * 0.32, t * 0.45, WHITE, 0.55 if not sun else 0.35)
        c.line(lu - lw * 0.18, cy + lh * 0.10, lu + lw * 0.02, cy + lh * 0.20, t * 0.25, WHITE, 0.35)
        c.line(lu - lw / 2 + t * 0.8, cy + lh * 0.38, lu + lw / 2 - t * 0.8, cy + lh * 0.38, t * 0.30, scale(frame, 1.5), 0.45)
    c.line(u - gap * 0.7, cy + lh * 0.18, u + gap * 0.7, cy + lh * 0.18, t * 0.9, frame, 1.0)
    c.line(u - gap * 0.7, cy + lh * 0.22, u + gap * 0.7, cy + lh * 0.22, t * 0.3, scale(frame, 1.6), 0.5)
    for sgn in (-1, 1):
        c.ellipse(u + sgn * gap * 0.55, cy - lh * 0.12, w * 0.012, w * 0.022, (0.95, 0.95, 0.97), alpha=0.8, lift=0)


@sprop("care_opt_rack", aspect=1.7, fill=0.82)
def opt_rack(c, color):
    """A stepped oak display rack with nine pairs of glasses in different frame styles and colours, LED strip on each step."""
    rng = c.rng
    acc = _pal(color, "accent", (0.12, 0.43, 0.55))
    oak = (0.82, 0.64, 0.42)
    ao(c, 0.0, 0.0, 1.45, 0.22, 0.5)
    soft_disc(c, 0.02, 0.01, 0.72, 0.04, BLACK, 0.5, 1.2)
    # three steps (back to front: tall to low)
    steps = ((0.50, 0.56), (0.32, 0.64), (0.14, 0.72))
    for v, w in steps:
        _vpoly(c, [(-w / 2 - 0.03, v), (w / 2 + 0.03, v), (w / 2, v + 0.09), (-w / 2, v + 0.09)], scale(oak, 1.2), scale(oak, 1.0))
    # draw back step first with its glasses, front steps later to overlap
    frames = (((0.12, 0.12, 0.14), "rect"), ((0.62, 0.25, 0.18), "round"), ((0.82, 0.68, 0.34), "rect"), ((0.12, 0.43, 0.55), "cat"),
              ((0.30, 0.20, 0.14), "rect"), ((0.85, 0.80, 0.78), "round"), ((0.55, 0.15, 0.25), "cat"), ((0.14, 0.14, 0.18), "round"), ((0.2, 0.45, 0.30), "rect"))
    k = 0
    for ri, (v, w) in enumerate(steps):
        # front face of the previous step and LED strip
        c.rect(0.0, v - 0.05, w + 0.06, 0.12, scale(oak, 0.85), lift=0.1, r=0.005)
        craft.hshade_box(c, 0.0, v - 0.05, w + 0.06, 0.12, scale(oak, 1.15), scale(oak, 0.65), r=0.005)
        c.rect(0.0, v + 0.004, w + 0.05, 0.007, (1.0, 0.96, 0.8), lift=0)
        soft_disc(c, 0.0, v + 0.03, w * 0.6, 0.06, (1.0, 0.94, 0.75), 0.35, 1.3, add=True)
        for j in range(3):
            fr, kind = frames[k]
            k += 1
            uu = (j - 1) * (w * 0.31)
            _specs(c, uu, v + 0.045, w * 0.29, fr, tint=(0.82, 0.90, 0.95), kind=kind)
        for x in (-0.18, 0.18):
            c.line(x, v - 0.10, x + 0.002, v + 0.02, 0.003, scale(oak, 0.65), 0.3)
    # grain
    for _ in range(18):
        x, y = rng.uniform(-0.34, 0.34), rng.uniform(0.04, 0.50)
        c.line(x, y, x + rng.uniform(0.04, 0.14), y + rng.uniform(-0.002, 0.002), 0.002, scale(oak, rng.uniform(0.7, 0.85)), 0.3)
    # a small brand plate
    c.rect(0.0, 0.075, 0.22, 0.032, scale(acc, 0.8), r=0.006, lift=0.2)
    c.rect(0.0, 0.075, 0.16, 0.007, WHITE, lift=0, alpha=0.8)


@sprop("care_opt_sunstand", aspect=0.52, fill=1.0)
def opt_sunstand(c, color):
    """A rotating sunglasses tower: weighted base, steel column, small mirror on top and four tiers of sunglasses."""
    rng = c.rng
    steel = (0.78, 0.80, 0.84)
    ao(c, 0.0, 0.0, 0.7, 0.12, 0.55)
    c.ellipse(0.0, 0.02, 0.25, 0.25 * TILT, (0.08, 0.08, 0.10), lift=0)
    c.ellipse(0.0, 0.04, 0.23, 0.23 * TILT, scale(steel, 0.7), lift=0.3)
    soft_disc(c, -0.08, 0.05, 0.12, 0.03, WHITE, 0.5, 1.0, add=True)
    # column
    _spoly(c, [(-0.05, 0.05), (0.05, 0.05), (0.05, 0.94), (-0.05, 0.94)], _bands(steel, "metal"), 0.0)
    # tiers of sunglasses (a pair left, centre and right on each tier, turned on the rotating tower)
    kinds = ("rect", "round", "cat", "rect")
    cols = ((0.10, 0.10, 0.12), (0.55, 0.35, 0.18), (0.8, 0.2, 0.25), (0.15, 0.30, 0.55))
    for i in range(4):
        v = 0.12 + i * 0.185
        c.ellipse(0.0, v, 0.21, 0.21 * TILT * 0.7, scale(steel, 0.55), lift=0.2)
        c.ellipse(0.0, v + 0.01, 0.20, 0.20 * TILT * 0.7, steel, lift=0.2)
        for j, (uu, sc) in enumerate(((-0.17, 0.78), (0.0, 1.0), (0.17, 0.78))):
            fr = cols[(i + j) % 4]
            _specs(c, uu, v + 0.02 + (0.0 if j == 1 else 0.006), 0.22 * sc, fr, tint=(0.18, 0.2, 0.26) if (i + j) % 2 else (0.25, 0.3, 0.35), kind=kinds[(i + j) % 4], sun=True)
    # mirror cap
    c.rect(0.0, 0.965, 0.16, 0.06, (0.35, 0.3, 0.25), r=0.01, lift=0.1)
    c.rect(0.0, 0.965, 0.14, 0.045, (0.82, 0.90, 0.95), r=0.008, lift=0.1)
    soft_disc(c, -0.03, 0.975, 0.05, 0.015, WHITE, 0.8, 1.0, add=True)


@sprop("care_opt_mirror", aspect=0.78, fill=1.0)
def opt_mirror(c, color):
    """A tabletop try-on mirror: oval gold frame on a little stand, sky-and-room reflection with a diagonal glint."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.09, 0.5)
    gold = (0.85, 0.66, 0.30)
    c.ellipse(0.0, 0.02, 0.17, 0.17 * TILT, scale(gold, 0.5), lift=0)
    c.ellipse(0.0, 0.035, 0.155, 0.155 * TILT, gold, lift=0.3)
    soft_disc(c, -0.06, 0.045, 0.07, 0.02, WHITE, 0.6, 1.0, add=True)
    c.rect(0.0, 0.10, 0.04, 0.12, scale(gold, 1.0), lift=0.3)
    c.ellipse(0.0, 0.58, 0.31, 0.42, scale(gold, 0.55), lift=0)
    c.ellipse(0.0, 0.585, 0.30, 0.41, gold, lift=0.3)
    c.ellipse(0.0, 0.585, 0.265, 0.375, scale(gold, 0.7), lift=0)
    c.ellipse(0.0, 0.585, 0.255, 0.365, (0.78, 0.88, 0.94), lift=0.25)
    soft_disc(c, 0.07, 0.45, 0.2, 0.20, (0.95, 0.85, 0.7), 0.45, 1.2)
    soft_disc(c, -0.08, 0.76, 0.18, 0.14, (0.55, 0.78, 0.95), 0.5, 1.2)
    c.poly([(-0.20, 0.74), (-0.12, 0.80), (0.12, 0.40), (0.04, 0.34)], WHITE, alpha=0.20)
    c.line(-0.16, 0.78, 0.06, 0.38, 0.012, WHITE, 0.25)
    craft.arc(c, 0.0, 0.585, 0.30, 0.41, 110, 200, 0.012, (1.0, 0.95, 0.75), 0.6, steps=10)
    craft.arc(c, 0.0, 0.585, 0.28, 0.39, 200, 330, 0.010, scale(gold, 0.45), 0.5, steps=10)


@sprop("care_opt_tray", aspect=2.4, fill=0.28)
def opt_tray(c, color):
    """A velvet lens tray with folded spectacles, a lens cloth and a cleaning-spray bottle."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.12, 0.5)
    vel = _pal(color, "accent_dark", (0.10, 0.28, 0.36))
    c.rect(0.0, 0.10, 0.68, 0.17, scale(vel, 0.55), r=0.03, lift=0.05)
    _vpoly(c, [(-0.34, 0.085), (0.34, 0.085), (0.31, 0.20), (-0.31, 0.20)], scale(vel, 1.25), scale(vel, 0.85), smooth=1)
    craft.hshade_box(c, 0.0, 0.045, 0.68, 0.065, scale(vel, 1.1), scale(vel, 0.5), r=0.015)
    soft_disc(c, -0.1, 0.15, 0.3, 0.04, WHITE, 0.14, 1.3, add=True)
    # folded glasses lying flat: two flattened lens ellipses and arms folded across them
    for (u, v, fr, rot) in ((-0.16, 0.135, (0.12, 0.12, 0.14), 0), (0.10, 0.16, (0.72, 0.52, 0.22), 6)):
        for sgn in (-1, 1):
            lu = u + sgn * 0.065
            c.ellipse(lu, v, 0.058, 0.032, fr, lift=0.2, angle=rot)
            c.ellipse(lu, v + 0.002, 0.048, 0.025, (0.82, 0.9, 0.95), alpha=0.55, lift=0.1, angle=rot)
            soft_disc(c, lu - 0.02, v + 0.01, 0.02, 0.008, WHITE, 0.8, 1.0, add=True)
        c.line(u - 0.012, v + 0.005, u + 0.012, v + 0.005, 0.008, fr, 1.0)
        c.line(u - 0.12, v - 0.01, u + 0.10, v - 0.018, 0.007, scale(fr, 0.7), 0.9)
    # lens cloth and spray
    c.ellipse(0.26, 0.13, 0.06, 0.028, (0.93, 0.95, 0.97), lift=0.12)
    c.ellipse(0.275, 0.138, 0.04, 0.018, (0.8, 0.86, 0.9), lift=0.1)
    craft.hshade_box(c, -0.30, 0.145, 0.05, 0.10, (0.9, 0.95, 0.98), (0.55, 0.65, 0.72), r=0.012)
    c.rect(-0.30, 0.20, 0.025, 0.03, (0.15, 0.15, 0.17), lift=0.2)
    c.rect(-0.30, 0.145, 0.04, 0.03, _pal(color, "accent", (0.12, 0.43, 0.55)), lift=0.1)


@niche("optical", "Optical store / eyewear", subjects=("care_opt_rack",),
       strong=("optical store", "optical shop", "eyeglasses", "spectacles", "optician", "sunglasses", "eyewear", "frames and lenses", "chashma",
               "chasma", "chashme ki dukaan", "चश्मा", "चश्मे की दुकान", "ऑप्टिकल", "चश्मे"),
       weak=("glasses", "lens", "contact lenses", "frames", "vision care", "optics", "goggles", "lenses"),
       avoid=("eye hospital", "ophthalmologist"), accent="#1f6f8b", mood="light", group="retail")
def optical(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # slat-wall of hanging eyeglasses, lit by LED shelf strips
        frames = ((0.1, 0.1, 0.12), (0.6, 0.3, 0.2), P.accent, (0.8, 0.65, 0.3), (0.85, 0.85, 0.88), P.accent_dark, (0.55, 0.2, 0.3))
        for row in range(4):
            v = 0.10 + row * 0.125
            S.rect(1.0, v + 0.055, 3.4, 0.012, scale(WOOD, 1.2 if not dark else 0.6), lift=0.0)
            S.rect(1.0, v + 0.064, 3.4, 0.005, (1.0, 0.96, 0.82), lift=0.0)
            S.glow(1.0, v + 0.07, 1.6, (1.0, 0.95, 0.8), 0.14 * gl, 1.8)
            u = -0.60
            while u < 2.6:
                fr = frames[S.rng.randrange(len(frames))]
                S.circle(u - 0.022, v + 0.02, 0.020, fr, lift=0.15)
                S.circle(u + 0.022, v + 0.02, 0.020, fr, lift=0.15)
                S.circle(u - 0.022, v + 0.02, 0.014, (0.85, 0.92, 0.96), lift=0.0, alpha=0.8)
                S.circle(u + 0.022, v + 0.02, 0.014, (0.85, 0.92, 0.96), lift=0.0, alpha=0.8)
                u += 0.15 + S.rng.uniform(-0.01, 0.02)
        S.bokeh(6, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.95, 0.8), (0.8, 0.95, 1.0)], 0.012, 0.04, 0.25 * gl)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # white counter with a pale wooden edge, a soft light pool
    top = mix((0.94, 0.95, 0.95), P.accent_light, 0.14) if not dark else (0.16, 0.20, 0.24)
    S.floor(0.60, scale(top, 1.02), scale(top, 0.82))
    S.rect(1.0, 0.60, 14.0, 0.012, scale(top, 0.55), lift=0.0)
    S.rect(1.0, 0.614, 14.0, 0.006, WHITE, alpha=0.6 if not dark else 0.12, lift=0.0)
    S.soft(1.1, 0.82, 1.0, 0.15, (1.0, 0.96, 0.85), 0.28 if not dark else 0.14, 1.4, add=True)
    S.put("care_opt_mirror", 0.68, 0.86, 0.34, shadow_w=0.26)
    S.put("care_opt_sunstand", 1.58, 0.86, 0.50, shadow_w=0.3)
    S.put("care_opt_rack", 1.10, 0.91, 0.36, color=P, subject=True, shadow_w=0.55)
    S.put("care_opt_tray", 1.22, 1.02, 0.12, color=P, shadow_w=0.3)
    S.focus("detail", 1.10, 0.78)
    if dark:
        S.soft(1.10, 0.82, 0.4, 0.10, (1.0, 0.94, 0.75), 0.28, 1.5, add=True)
        S.soft(1.58, 0.70, 0.18, 0.16, (1.0, 0.94, 0.75), 0.20, 1.5, add=True)
    with S.near():
        S.circle(0.46, 1.08, 0.07, (0.95, 0.98, 1.0), alpha=0.32, lift=0)
        S.soft(1.90, 1.12, 0.3, 0.1, BLACK, 0.45, 1.0)


# ====================================================================================== MEHENDI
HENNA = (0.30, 0.12, 0.05)


def _finger(c, p0, p1, w0, w1, sk):
    """A tapered finger: polygon with rounded tip, shaded left-to-right."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy)
    nx, ny = -dy / d, dx / d
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    pts = [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (mid[0] + nx * (w0 + w1) / 4, mid[1] + ny * (w0 + w1) / 4), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
           (p1[0] + dx / d * w1 * 0.42, p1[1] + dy / d * w1 * 0.42), (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2),
           (mid[0] - nx * (w0 + w1) / 4, mid[1] - ny * (w0 + w1) / 4), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]
    _hpoly(c, pts, scale(sk, 1.08), scale(sk, 0.74), 0.03, power=1.1, smooth=2)
    for f in (0.34, 0.62):                                       # finger joint creases
        x, y = p0[0] + dx * f, p0[1] + dy * f
        c.line(x - nx * w0 * 0.30, y - ny * w0 * 0.30, x + nx * w0 * 0.30, y + ny * w0 * 0.30, 0.003, scale(sk, 0.66), 0.45)


def _ring(c, u, v, a, b, w, col, alpha=1.0, steps=22):
    craft.arc(c, u, v, a, b, 0, 360, w, col, alpha, steps=steps)


def _dots(c, pts, r, col, alpha=1.0):
    for x, y in pts:
        c.ellipse(x, y, r, r, col, lift=0.0, alpha=alpha)


def _paisley(c, u, v, ln, ang, col):
    """A teardrop paisley motif with a curl, angle in degrees (pointing direction of the tail)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for k in range(9):
        t = k / 8.0
        w = math.sin(math.pi * t) ** 0.7 * ln * 0.28 * (1.0 - 0.3 * t)
        x = t * ln
        y = ln * 0.18 * math.sin(t * math.pi * 1.0) * t
        pts.append((x, y + w))
    pts += [(x, y - 2 * w_) for (x, y), w_ in zip(reversed(pts), [math.sin(math.pi * (8 - k) / 8.0) ** 0.7 * ln * 0.28 * (1.0 - 0.3 * (8 - k) / 8.0) for k in range(9)])]
    poly = [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in pts]
    c.poly(poly, col, lift=0.0)
    c.ellipse(u + ln * 0.2 * ca, v + ln * 0.2 * sa, ln * 0.06, ln * 0.06, mix(col, WHITE, 0.55), lift=0.0, alpha=0.5)


class _Rot:
    """Draws a prop in a rotated frame (the hand lies on the table at an angle): the same drawing calls as a Ctx, positions rotated by `deg`
    (counter-clockwise, degrees) about `pivot`."""
    def __init__(self, c, deg, pivot=(0.0, 0.0)):
        self.c, self.deg, self.pv = c, deg, pivot
        a = math.radians(deg)
        self.ca, self.sa = math.cos(a), math.sin(a)

    def pt(self, u, v):
        du, dv = u - self.pv[0], v - self.pv[1]
        return (self.pv[0] + du * self.ca - dv * self.sa, self.pv[1] + du * self.sa + dv * self.ca)

    def ellipse(self, u, v, a, b, color, angle=0.0, lift=0.10, alpha=1.0, soft=1.0):
        u, v = self.pt(u, v)
        self.c.ellipse(u, v, a, b, color, angle + self.deg, lift, alpha, soft)

    def line(self, u0, v0, u1, v1, w, color, alpha=1.0):
        a, b = self.pt(u0, v0), self.pt(u1, v1)
        self.c.line(a[0], a[1], b[0], b[1], w, color, alpha)

    def poly(self, pts, color, lift=0.10, alpha=1.0):
        self.c.poly([self.pt(u, v) for u, v in pts], color, lift, alpha)

    def soft(self, u, v, a, b, color, alpha=0.5, power=1.7, angle=0.0, add=False):
        u, v = self.pt(u, v)
        soft_disc(self.c, u, v, a, b, color, alpha, power, angle - self.deg, add)


def _hleaf(h, u, v, length, angle, color, width=0.5):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = [(t * length, math.sin(math.pi * t) ** 0.8 * wd) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    out = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    h.poly([(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in out], color, 0.0)


@sprop("care_mehendi_hand", aspect=1.0, fill=1.0)
def mehendi_hand(c, color):
    """A forearm in a silk sleeve and bangles, hand lying on the table palm up and turned about 20 degrees: intricate henna in progress (mandala on
    the palm, vines and dots on the fingers, two freshly piped tips, an unfinished corner), thumb relaxed against the palm."""
    rng = c.rng
    sk = (0.80, 0.57, 0.43)
    hn = HENNA
    ao(c, 0.0, 0.0, 1.0, 0.16, 0.5)
    h = _Rot(c, -21.0, (0.0, 0.10))
    # forearm and silk sleeve cuff (the arm runs out of the picture to the lower left)
    _hpoly(h, [(-0.118, 0.16), (0.118, 0.16), (0.128, -0.12), (-0.128, -0.12)], scale(sk, 1.06), scale(sk, 0.70), 0.04)
    cuff = (0.62, 0.10, 0.18)
    _hpoly(h, [(-0.16, -0.01), (0.16, -0.01), (0.18, -0.34), (-0.18, -0.34)], scale(cuff, 1.35), scale(cuff, 0.55), 0.04)
    h.line(-0.162, -0.01, 0.162, -0.01, 0.014, (0.93, 0.76, 0.35), 1.0)
    for k in range(7):
        h.ellipse(-0.12 + k * 0.04, -0.07, 0.010, 0.010, (0.95, 0.80, 0.4), lift=0.1)
        h.ellipse(-0.12 + k * 0.04, -0.15, 0.007, 0.007, (0.95, 0.80, 0.4), lift=0.1, alpha=0.8)
    h.soft(-0.08, -0.17, 0.07, 0.15, WHITE, 0.14, 1.2, add=True)
    # thumb relaxed against the palm, fingers slightly splayed
    _finger(h, (-0.13, 0.23), (-0.235, 0.43), 0.098, 0.072, sk)
    _finger(h, (-0.125, 0.48), (-0.155, 0.86), 0.066, 0.052, sk)
    _finger(h, (-0.045, 0.50), (-0.058, 0.96), 0.070, 0.054, sk)
    _finger(h, (0.040, 0.50), (0.056, 0.90), 0.066, 0.052, sk)
    _finger(h, (0.115, 0.46), (0.158, 0.76), 0.056, 0.044, sk)
    # palm
    palm = [(-0.125, 0.10), (-0.165, 0.24), (-0.175, 0.40), (-0.16, 0.52), (-0.05, 0.57), (0.05, 0.57), (0.15, 0.52), (0.18, 0.40), (0.165, 0.24), (0.125, 0.10)]
    _hpoly(h, palm, scale(sk, 1.10), scale(sk, 0.76), 0.04, power=1.1, smooth=2)
    h.soft(-0.06, 0.40, 0.11, 0.12, WHITE, 0.16, 1.2, add=True)
    h.soft(0.17, 0.30, 0.05, 0.22, (0.4, 0.2, 0.1), 0.25, 1.3)
    h.soft(-0.13, 0.30, 0.04, 0.12, (0.5, 0.25, 0.12), 0.2, 1.3)
    for pts in (((-0.10, 0.42), (-0.03, 0.34), (0.02, 0.24)), ((-0.12, 0.30), (-0.02, 0.28), (0.11, 0.33))):    # palm creases
        for a, b in zip(pts, pts[1:]):
            h.line(a[0], a[1], b[0], b[1], 0.003, scale(sk, 0.60), 0.35)
    # --- henna: palm mandala
    mu, mv = 0.0, 0.31
    for k in range(18):
        a = 2 * math.pi * k / 18
        h.ellipse(mu + math.cos(a) * 0.118, mv + math.sin(a) * 0.118, 0.0055, 0.0055, hn, lift=0)
    craft.arc(h, mu, mv, 0.098, 0.098, 0, 360, 0.005, hn, 0.95, steps=22)
    for k in range(18):
        a = 2 * math.pi * k / 18 + 0.17
        craft.arc(h, mu + math.cos(a) * 0.132, mv + math.sin(a) * 0.132, 0.014, 0.014, math.degrees(a) - 80, math.degrees(a) + 80, 0.004, hn, 0.9, steps=4)
    for k in range(14):
        a = 2 * math.pi * k / 14
        h.ellipse(mu + math.cos(a) * 0.072, mv + math.sin(a) * 0.072, 0.020, 0.0095, hn, angle=math.degrees(a), lift=0)
        h.ellipse(mu + math.cos(a) * 0.072, mv + math.sin(a) * 0.072, 0.012, 0.0035, scale(sk, 1.2), angle=math.degrees(a), lift=0, alpha=0.7)
    craft.arc(h, mu, mv, 0.043, 0.043, 0, 360, 0.006, hn, 1.0, steps=18)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        h.ellipse(mu + math.cos(a) * 0.027, mv + math.sin(a) * 0.027, 0.011, 0.005, hn, angle=math.degrees(a), lift=0)
    h.ellipse(mu, mv, 0.012, 0.012, hn, lift=0)
    # paisleys and vines from the mandala up to the finger bases
    for (u, v, ln, ang) in ((-0.125, 0.42, 0.075, 100), (0.125, 0.41, 0.07, 80), (-0.095, 0.19, 0.06, 250), (0.095, 0.19, 0.06, 290)):
        _paisley(h, u, v, ln, ang, hn)
    for (x0, y0, x1, y1) in ((-0.06, 0.44, -0.10, 0.50), (0.0, 0.43, 0.0, 0.52), (0.06, 0.44, 0.09, 0.50)):
        craft.strand(h, x0, y0, math.hypot(x1 - x0, y1 - y0), math.degrees(math.atan2(y1 - y0, x1 - x0)), 0.006, hn, 1.0, 0.5)
    # finger work: a central vine with leaves and dot lines; the first two tips are filled with fresh paste
    for (bx, by, tx, ty, done) in ((-0.125, 0.48, -0.155, 0.86, True), (-0.045, 0.50, -0.058, 0.96, True), (0.040, 0.50, 0.056, 0.90, False), (0.115, 0.46, 0.158, 0.76, False)):
        n = 7 if done else 3
        for k in range(n):
            t = 0.10 + 0.78 * k / 7.0
            x, y = bx + (tx - bx) * t, by + (ty - by) * t
            h.ellipse(x, y, 0.0075 if k % 2 == 0 else 0.0045, 0.012 if k % 2 == 0 else 0.0045, hn, lift=0, angle=-5)
            if done and k % 2 == 0:
                _hleaf(h, x, y, 0.036, 55, hn, 0.5)
                _hleaf(h, x, y, 0.036, 125, hn, 0.5)
        if done:
            h.line(bx, by + 0.02, tx, ty - 0.05, 0.004, hn, 1.0)
            h.ellipse(tx, ty - 0.02, 0.019, 0.045, hn, lift=0, angle=-3)
            h.soft(tx - 0.006, ty - 0.005, 0.006, 0.02, (1.0, 0.82, 0.6), 0.65, 1.0, add=True)
        else:
            h.line(bx, by + 0.02, bx + (tx - bx) * 0.4, by + (ty - by) * 0.4, 0.0035, scale(hn, 1.5), 0.55)
    # thumb: a vine
    for k in range(5):
        t = 0.25 + k * 0.14
        h.ellipse(-0.13 + (-0.235 + 0.13) * t, 0.23 + 0.20 * t, 0.007, 0.007, hn, lift=0)
    # wrist band: chevrons, dots and glass bangles around the forearm
    for k in range(8):
        x = -0.105 + k * 0.03
        h.line(x, 0.135, x + 0.015, 0.115, 0.004, hn, 1.0)
        h.line(x + 0.015, 0.115, x + 0.03, 0.135, 0.004, hn, 1.0)
    for k, col in enumerate(((0.80, 0.12, 0.18), (0.92, 0.74, 0.30), (0.14, 0.52, 0.34), (0.92, 0.74, 0.30), (0.80, 0.12, 0.18), (0.92, 0.74, 0.30))):
        v = 0.085 - k * 0.019
        craft.arc(h, 0.0, v, 0.134, 0.030, 180, 360, 0.013, scale(col, 0.7), 1.0, steps=10)
        craft.arc(h, 0.0, v + 0.004, 0.134, 0.030, 190, 350, 0.008, col, 1.0, steps=10)
        craft.arc(h, 0.0, v + 0.006, 0.12, 0.026, 205, 250, 0.003, WHITE, 0.8, steps=4)
    # unfinished area: faint guide lines only (bottom right of the palm)
    for k in range(5):
        a = math.radians(205 + k * 12)
        h.line(0.07 + math.cos(a) * 0.02, 0.17 + math.sin(a) * 0.01, 0.12, 0.16 + k * 0.02, 0.002, scale(sk, 0.58), 0.5)
    h.soft(-0.10, 0.55, 0.05, 0.03, WHITE, 0.2, 1.0, add=True)


@sprop("care_mehendi_cone", aspect=2.6, fill=0.36)
def mehendi_cone(c, color):
    """A henna cone: cream translucent plastic (reads against the dark cloth) with a dark paste core toward the nozzle, a crimped tail tied with a gold
    ribbon, and a fresh squiggle of henna trailing from the tip."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.16, 0.5)
    T, B = (-0.30, 0.060), (0.28, 0.190)
    dx, dy = B[0] - T[0], B[1] - T[1]
    d = math.hypot(dx, dy)
    nx, ny = -dy / d, dx / d
    hw = 0.130
    paste = (0.26, 0.13, 0.06)
    cream = (0.97, 0.93, 0.84)
    pts = [T, (T[0] + dx * 0.5 + nx * hw * 0.55, T[1] + dy * 0.5 + ny * hw * 0.55), (B[0] + nx * hw, B[1] + ny * hw), (B[0] - nx * hw, B[1] - ny * hw),
           (T[0] + dx * 0.5 - nx * hw * 0.55, T[1] + dy * 0.5 - ny * hw * 0.55)]
    _hpoly(c, pts, scale(cream, 1.06), scale(cream, 0.62), 0.04, power=1.0, smooth=2)
    # paste core visible through the plastic: dark near the tip, fading out toward the tail
    core = [T, (T[0] + dx * 0.34 + nx * hw * 0.34, T[1] + dy * 0.34 + ny * hw * 0.34), (T[0] + dx * 0.62 + nx * hw * 0.50, T[1] + dy * 0.62 + ny * hw * 0.50),
            (T[0] + dx * 0.62 - nx * hw * 0.50, T[1] + dy * 0.62 - ny * hw * 0.50), (T[0] + dx * 0.34 - nx * hw * 0.34, T[1] + dy * 0.34 - ny * hw * 0.34)]
    _hpoly(c, core, scale(paste, 1.9), scale(paste, 0.5), 0.04, power=1.0, smooth=2, alpha=0.92)
    for k in range(4):                                      # paste fading into the cream plastic
        t = 0.60 + k * 0.05
        soft_disc(c, T[0] + dx * t, T[1] + dy * t, hw * 0.55, hw * 0.55, scale(paste, 1.3), 0.30 - k * 0.06, 1.0)
    c.line(T[0] + dx * 0.12 + nx * 0.03, T[1] + dy * 0.12 + ny * 0.03, B[0] - dx * 0.05 + nx * hw * 0.70, B[1] - dy * 0.05 + ny * hw * 0.70, 0.012, WHITE, 0.55)
    c.line(T[0] + dx * 0.30 - nx * 0.015, T[1] + dy * 0.30 - ny * 0.015, B[0] - dx * 0.14 - nx * hw * 0.5, B[1] - dy * 0.14 - ny * hw * 0.5, 0.006, WHITE, 0.22)
    soft_disc(c, B[0] - 0.10, B[1] + 0.04, 0.12, 0.05, WHITE, 0.30, 1.1, add=True)
    # crimped plastic tail and a gold ribbon
    tail = [(B[0] + nx * hw * 0.95, B[1] + ny * hw * 0.95), (B[0] + dx * 0.20 + nx * hw * 0.62, B[1] + dy * 0.20 + ny * hw * 0.62),
            (B[0] + dx * 0.20 - nx * hw * 0.62, B[1] + dy * 0.20 - ny * hw * 0.62), (B[0] - nx * hw * 0.95, B[1] - ny * hw * 0.95)]
    _hpoly(c, tail, (0.98, 0.96, 0.92), (0.66, 0.64, 0.62), 0.0, alpha=0.9)
    for k in range(5):
        t = 0.2 + k * 0.16
        x, y = B[0] + dx * 0.20 * t, B[1] + dy * 0.20 * t
        c.line(x + nx * hw * 0.8, y + ny * hw * 0.8, x - nx * hw * 0.8, y - ny * hw * 0.8, 0.003, (0.55, 0.55, 0.58), 0.6)
    gx, gy = B[0] + dx * 0.02, B[1] + dy * 0.02
    c.line(gx + nx * hw * 0.98, gy + ny * hw * 0.98, gx - nx * hw * 0.98, gy - ny * hw * 0.98, 0.026, (0.90, 0.68, 0.26), 1.0)
    c.line(gx + nx * hw * 0.9 - 0.006, gy + ny * hw * 0.9 + 0.006, gx - nx * hw * 0.9 - 0.006, gy - ny * hw * 0.9 + 0.006, 0.008, (1.0, 0.92, 0.6), 0.8)
    # tip + fresh squiggle of henna
    c.ellipse(T[0] - 0.004, T[1], 0.014, 0.011, scale(paste, 0.9), lift=0.2)
    pts2 = []
    for k in range(20):
        t = k / 19.0
        pts2.append((T[0] - 0.02 - t * 0.17, T[1] - 0.012 + 0.024 * math.sin(t * 9.0) * (0.6 + t)))
    for a_, b_ in zip(pts2, pts2[1:]):
        c.line(a_[0], a_[1], b_[0], b_[1], 0.013, scale(paste, 0.9), 1.0)
        c.line(a_[0], a_[1] + 0.004, b_[0], b_[1] + 0.004, 0.004, (0.75, 0.50, 0.28), 0.6)


@sprop("care_mehendi_dish", aspect=3.5, fill=0.30)
def mehendi_dish(c, color):
    """A shallow brass dish heaped with marigold, rose and jasmine petals."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.05, 0.18, 0.55)
    prof = [(0.28, 0.0), (0.40, 0.025), (0.49, 0.075), (0.52, 0.105)]
    _lathe(c, 0.0, 0.0, prof, BRASS, inner=scale(BRASS, 0.45), kind="metal")
    top = 0.105
    c.ellipse(0.0, top + 0.006, 0.45, 0.45 * TILT * 0.9, (0.55, 0.20, 0.10), lift=0)
    cols = ((0.98, 0.58, 0.08), (1.0, 0.72, 0.12), (0.88, 0.20, 0.30), (0.98, 0.55, 0.65), (0.98, 0.97, 0.93), (0.95, 0.40, 0.10))
    for _ in range(54):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.40
        u, v = math.cos(a) * rr, top + 0.012 + math.sin(a) * rr * TILT * 0.9 + rr * 0.10
        col = cols[rng.randrange(len(cols))]
        c.ellipse(u, v, rng.uniform(0.020, 0.035), rng.uniform(0.010, 0.018), col, angle=rng.uniform(0, 180), lift=0.15)
    # three full marigold heads
    for (u, v, r) in ((-0.16, top + 0.075, 0.075), (0.14, top + 0.085, 0.085), (0.01, top + 0.04, 0.07)):
        for k in range(14):
            a = 2 * math.pi * k / 14
            c.ellipse(u + math.cos(a) * r * 0.62, v + math.sin(a) * r * 0.52, r * 0.42, r * 0.22, (0.98, 0.58, 0.06) if k % 2 else (1.0, 0.68, 0.10),
                      angle=math.degrees(a), lift=0.15)
        c.ellipse(u, v, r * 0.40, r * 0.30, (0.92, 0.42, 0.04), lift=0.15)
        soft_disc(c, u - r * 0.15, v + r * 0.1, r * 0.5, r * 0.3, (1.0, 0.9, 0.5), 0.6, 1.0)
    soft_disc(c, -0.20, 0.07, 0.12, 0.012, (1.0, 0.93, 0.7), 0.6, 1.0, add=True)
    craft.arc(c, 0.0, top, 0.515, 0.515 * TILT, 195, 345, 0.006, (1.0, 0.92, 0.7), 0.55, steps=10)


@niche("mehendi", "Mehendi / henna artist", subjects=("care_mehendi_hand",),
       strong=("mehendi", "mehndi", "henna", "henna artist", "bridal mehendi", "bridal henna", "mehendi artist", "mehndi design", "mehandi", "arabic mehendi",
               "मेहंदी", "मेहन्दी", "मेहंदी आर्टिस्ट", "दुल्हन की मेहंदी"),
       weak=("bridal", "henna cone", "wedding", "sangeet", "hand art", "festive", "karwa chauth", "bridal makeup"),
       avoid=("tattoo studio", "tattoo"), accent="#b5651d", mood="warm", group="events")
def mehendi(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    maroon = scale(mix(P.accent_dark, (0.55, 0.08, 0.16), 0.6), 0.9)
    with S.far():
        S.wall(mix(P.wall_top, P.accent_light, 0.15), mix(P.wall_bot, P.accent_light, 0.2), 0.58)
        # silk drape in vertical folds with a golden border, string lights and a marigold garland
        for k in range(46):
            u = -3.5 + k * 0.17
            tone = 0.85 + 0.3 * abs(math.sin(k * 1.3))
            S.rect(u + 0.085, 0.26, 0.17, 0.56, scale(maroon if not dark else scale(maroon, 0.7), tone), lift=0.0)
            S.rect(u + 0.02, 0.26, 0.012, 0.56, (1.0, 0.8, 0.6), lift=0.0, alpha=0.18)
        S.rect(1.0, 0.54, 12.0, 0.035, (0.90, 0.72, 0.32), lift=0.0)
        S.rect(1.0, 0.50, 12.0, 0.012, (0.95, 0.82, 0.45), lift=0.0)
        for k in range(20):
            u = 0.0 + k * 0.1
            S.circle(u, 0.12 + 0.07 * math.sin(k * 0.8), 0.026, (1.0, 0.62, 0.08) if k % 2 else (1.0, 0.76, 0.14), lift=0.15)
        S.bokeh(20, 0.0, 0.02, 2.0, 0.46, [(1.0, 0.85, 0.45), (1.0, 0.7, 0.3), (1.0, 0.95, 0.7)], 0.012, 0.04, 0.45 * gl)
        S.glow(1.0, 0.28, 1.0, (1.0, 0.7, 0.35), 0.28 * gl, 1.7)
        S.floor(0.58, P.floor_top, P.floor_bot)
    # table covered with an embroidered cloth: deep red with gold rows of mirror-work
    S.floor(0.58, scale(maroon, 1.1), scale(maroon, 0.62))
    S.rect(1.0, 0.58, 14.0, 0.010, scale(maroon, 0.35), lift=0.0)
    S.rect(1.0, 0.592, 14.0, 0.008, (0.92, 0.74, 0.34), lift=0.0)
    for row, v in enumerate((0.70, 0.82, 0.96, 1.12)):
        n = int(3.6 / (0.07 + row * 0.02))
        for k in range(n):
            u = -1.0 + k * (0.07 + row * 0.02) + (0.03 if row % 2 else 0.0)
            S.circle(u, v, 0.007 + row * 0.002, (0.95, 0.78, 0.38), lift=0.1, alpha=0.8)
            S.circle(u, v - 0.012, 0.003, (1.0, 0.95, 0.8), lift=0.0, alpha=0.7)
        S.line(-2.0, v + 0.04 + row * 0.01, 4.2, v + 0.04 + row * 0.01, 0.003, (0.92, 0.74, 0.34), 0.45)
    S.soft(1.08, 0.82, 0.95, 0.15, (1.0, 0.75, 0.4), 0.28 * gl, 1.4, add=True)
    # a cream brocade runner under the hand and cone: light backing so the dark henna reads, and the table perspective
    cream = (0.96, 0.89, 0.74) if not dark else (0.40, 0.27, 0.17)
    _spoly_stage(S, [(0.60, 0.80), (1.40, 0.80), (1.52, 1.17), (0.50, 1.17)], scale(cream, 0.80))
    _spoly_stage(S, [(0.62, 0.815), (1.38, 0.815), (1.49, 1.155), (0.53, 1.155)], cream)
    S.line(0.64, 0.835, 1.36, 0.835, 0.004, (0.88, 0.66, 0.26), 0.9)
    for k in range(18):
        S.circle(0.68 + k * 0.040, 0.855, 0.006, (0.85, 0.55, 0.25), alpha=0.8, lift=0.1, soft=0.5)
    for k in range(20):
        S.circle(0.56 + k * 0.047, 1.14, 0.007, (0.75, 0.20, 0.25), alpha=0.7, lift=0.1, soft=0.5)
    S.soft(1.08, 0.98, 0.62, 0.14, (1.0, 0.85, 0.55), 0.18 * gl, 1.3, add=True)
    _scatter_leaves(S, 9, 0.56, 0.86, 1.42, 1.14, ((1.0, 0.62, 0.10), (0.9, 0.25, 0.35), (1.0, 0.8, 0.2), (0.98, 0.9, 0.9)), 0.040)
    S.put("care_mehendi_dish", 0.78, 0.89, 0.13, shadow_w=0.38)
    S.put("care_mehendi_hand", 1.00, 0.92, 0.64, subject=True, shadow_w=0.5)
    S.put("care_mehendi_cone", 1.26, 1.08, 0.20, shadow_w=0.4)
    S.focus("detail", 1.08, 0.78)
    if dark:                                    # practical light: fairy lights warming the cloth and a spot on the hand
        S.soft(1.08, 0.80, 0.4, 0.3, (1.0, 0.7, 0.35), 0.30, 1.5, add=True)
    with S.near():
        S.circle(0.46, 1.10, 0.06, (1.0, 0.75, 0.3), alpha=0.38, lift=0)
        S.circle(1.88, 0.72, 0.045, (1.0, 0.85, 0.5), alpha=0.35, lift=0)
        S.ellipse(1.82, 1.08, 0.05, 0.02, (1.0, 0.6, 0.1), angle=20, alpha=0.9)


# ====================================================================================== TATTOO STUDIO
@sprop("care_tat_machine", aspect=2.6, fill=0.5)
def tat_machine(c, color):
    """A coil tattoo machine: steel frame, two copper-wound coils, armature bar with spring and contact screw, black knurled grip tube with a needle."""
    rng = c.rng
    steel = (0.80, 0.83, 0.88)
    copper = (0.86, 0.46, 0.18)
    ao(c, 0.0, 0.0, 1.3, 0.18, 0.7)
    soft_disc(c, 0.02, 0.01, 0.62, 0.035, BLACK, 0.7, 1.2)
    # frame: base bar, rear riser and front post
    _vpoly(c, [(-0.34, 0.05), (0.42, 0.05), (0.42, 0.125), (-0.34, 0.125)], (0.92, 0.94, 0.97), (0.28, 0.30, 0.36))
    c.rect(0.04, 0.119, 0.74, 0.006, WHITE, lift=0, alpha=0.8)
    _spoly(c, [(0.335, 0.12), (0.43, 0.12), (0.43, 0.36), (0.335, 0.36)], _bands(steel, "metal"), 0.0)
    _spoly(c, [(-0.37, 0.12), (-0.29, 0.12), (-0.29, 0.30), (-0.37, 0.30)], _bands(steel, "metal"), 0.0)
    # rear coil, then front coil (copper winding with vertical wire lines)
    for (cu, cv, k) in ((0.04, 0.265, 0.72), (0.0, 0.225, 1.0)):
        L = 0.42
        c.rect(cu, cv, L, 0.115, scale(copper, k), r=0.04, lift=0.30)
        for i in range(34):
            x = cu - L / 2 + 0.012 + i * (L - 0.024) / 33.0
            c.line(x, cv - 0.052, x, cv + 0.052, 0.0030, scale(copper, 0.55 * k), 0.55)
            if i % 2:
                c.line(x + 0.003, cv - 0.04, x + 0.003, cv + 0.045, 0.0016, scale(copper, 1.5 * k), 0.4)
        soft_disc(c, cu - 0.05, cv + 0.035, 0.17, 0.016, (1.0, 0.85, 0.6), 0.65 * k, 1.1, add=True)
        for ex in (cu - L / 2 - 0.012, cu + L / 2 + 0.012):
            c.rect(ex, cv, 0.026, 0.128, scale(steel, 0.9 * k), r=0.006, lift=0.2)
            c.rect(ex - 0.004, cv + 0.02, 0.006, 0.08, WHITE, lift=0, alpha=0.5)
        c.ellipse(cu + L / 2 + 0.03, cv, 0.014, 0.022, scale(steel, 0.7), lift=0.3)
    # armature bar across the coils, spring at the front, contact screw at the back
    _vpoly(c, [(-0.30, 0.340), (0.30, 0.350), (0.30, 0.366), (-0.30, 0.356)], (0.95, 0.96, 0.98), (0.42, 0.45, 0.5))
    for k in range(6):
        x = -0.38 + k * 0.016
        c.line(x, 0.30 + (0.03 if k % 2 else 0.0), x + 0.016, 0.30 + (0.0 if k % 2 else 0.03), 0.004, steel, 1.0)
    c.rect(0.33, 0.40, 0.03, 0.06, scale(steel, 0.9), lift=0.3)
    c.ellipse(0.33, 0.435, 0.026, 0.012, scale(steel, 1.1), lift=0.3)
    for k in range(5):
        c.line(0.31 + k * 0.01, 0.43, 0.31 + k * 0.01, 0.442, 0.002, scale(steel, 0.4), 0.6)
    c.ellipse(0.385, 0.375, 0.022, 0.022, scale(steel, 0.9), lift=0.3)
    c.ellipse(0.385, 0.375, 0.009, 0.009, scale(steel, 0.4), lift=0.1)
    # rubber bands
    for x in (-0.17, 0.19):
        c.rect(x, 0.225, 0.014, 0.125, (0.75, 0.10, 0.12), lift=0.2)
    # grip tube hanging down-left to the needle tip
    p0, p1 = (-0.33, 0.24), (-0.60, 0.03)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy)
    nx, ny = -dy / d, dx / d
    w = 0.036
    _hpoly(c, [(p0[0] + nx * w, p0[1] + ny * w), (p1[0] + nx * w * 0.8, p1[1] + ny * w * 0.8), (p1[0] - nx * w * 0.8, p1[1] - ny * w * 0.8),
               (p0[0] - nx * w, p0[1] - ny * w)], (0.40, 0.42, 0.46), (0.05, 0.05, 0.07), 0.0, power=0.9)
    for k in range(9):
        t = 0.12 + k * 0.08
        x, y = p0[0] + dx * t, p0[1] + dy * t
        c.line(x + nx * w * 0.8, y + ny * w * 0.8, x - nx * w * 0.8, y - ny * w * 0.8, 0.003, (0.5, 0.52, 0.56), 0.5)
    c.line(p0[0] + dx * 0.05 + nx * w * 0.6, p0[1] + dy * 0.05 + ny * w * 0.6, p1[0] + nx * w * 0.5, p1[1] + ny * w * 0.5, 0.005, WHITE, 0.30)
    tip = (p1[0] + dx / d * 0.07, p1[1] + dy / d * 0.07)
    c.poly([(p1[0] + nx * w * 0.7, p1[1] + ny * w * 0.7), (tip[0] + nx * 0.008, tip[1] + ny * 0.008), (tip[0] - nx * 0.008, tip[1] - ny * 0.008),
            (p1[0] - nx * w * 0.7, p1[1] - ny * w * 0.7)], scale(steel, 0.9), lift=0.2)
    c.line(tip[0], tip[1], tip[0] + dx / d * 0.03, tip[1] + dy / d * 0.03, 0.003, WHITE, 0.9)
    # clip cord curling out of the back and down
    craft.strand(c, 0.43, 0.34, 0.45, 8, 0.016, (0.08, 0.08, 0.09), 1.0, -0.5)
    craft.strand(c, 0.43, 0.345, 0.42, 8, 0.004, (0.5, 0.5, 0.55), 0.5, -0.5)


@sprop("care_tat_inks", aspect=2.4, fill=0.46)
def tat_inks(c, color):
    """A stainless tray with a row of ink caps (black, red, blue, yellow, green, white) and three dark ink bottles with coloured labels."""
    rng = c.rng
    steel = (0.78, 0.80, 0.84)
    ao(c, 0.0, 0.0, 1.2, 0.2, 0.7)
    soft_disc(c, 0.02, 0.01, 0.6, 0.035, BLACK, 0.6, 1.2)
    top = [(-0.60, 0.075), (0.60, 0.075), (0.54, 0.25), (-0.54, 0.25)]
    _vpoly(c, top, scale(steel, 0.95), scale(steel, 0.72))
    c.poly([(-0.55, 0.095), (0.55, 0.095), (0.50, 0.23), (-0.50, 0.23)], scale(steel, 0.55), lift=0.1)
    soft_disc(c, -0.1, 0.17, 0.4, 0.04, WHITE, 0.30, 1.3, add=True)
    # bottles behind (dark glass with coloured labels)
    for u, h, col in ((-0.34, 0.40, (0.85, 0.12, 0.14)), (0.0, 0.46, (0.15, 0.40, 0.85)), (0.34, 0.36, (0.95, 0.75, 0.15))):
        r = 0.085
        c.ellipse(u, 0.20, r, r * TILT * 0.8, (0.02, 0.02, 0.03), lift=0)
        prof = [(r, 0.20), (r, 0.20 + h * 0.62), (r * 0.80, 0.20 + h * 0.72), (r * 0.40, 0.20 + h * 0.86), (r * 0.40, 0.20 + h * 0.96)]
        _spoly(c, [(u + rr, hh) for rr, hh in prof] + [(u - rr, hh) for rr, hh in reversed(prof)],
               [(0.0, (0.10, 0.10, 0.12)), (0.18, (0.38, 0.40, 0.45)), (0.40, (0.14, 0.14, 0.17)), (0.8, (0.05, 0.05, 0.06)), (1.0, (0.02, 0.02, 0.03))], 0.0)
        craft.hshade_box(c, u, 0.20 + h * 1.02, r * 0.95, h * 0.08, (0.35, 0.35, 0.40), (0.05, 0.05, 0.06), r=0.01)
        c.rect(u, 0.20 + h * 0.34, r * 1.75, h * 0.30, (0.08, 0.08, 0.1), r=0.006, lift=0.1)
        c.rect(u, 0.20 + h * 0.44, r * 1.75, h * 0.06, col, lift=0.0)
        c.rect(u, 0.20 + h * 0.34, r * 1.0, h * 0.025, (0.75, 0.75, 0.78), lift=0, alpha=0.8)
        c.rect(u, 0.20 + h * 0.27, r * 1.3, h * 0.015, (0.6, 0.6, 0.65), lift=0, alpha=0.6)
        c.rect(u - r * 0.55, 0.20 + h * 0.45, 0.008, h * 0.7, WHITE, r=0.004, lift=0, alpha=0.35)
        soft_disc(c, u + 0.02, 0.20 + h * 0.9, 0.04, 0.012, scale(col, 1.3), 0.35, 1.2, add=True)
    # ink caps in a row
    inks = ((0.04, 0.04, 0.05), (0.85, 0.10, 0.12), (0.12, 0.30, 0.80), (0.98, 0.80, 0.12), (0.12, 0.62, 0.30), (0.96, 0.96, 0.98))
    for i, col in enumerate(inks):
        u = -0.44 + i * 0.176
        v = 0.115
        r = 0.052
        soft_disc(c, u + 0.02, v - 0.005, r * 1.2, r * 0.5, BLACK, 0.5, 1.3)
        _lathe(c, u, v, [(r * 0.7, 0.0), (r, 0.02), (r, 0.055)], (0.92, 0.94, 0.96), kind="matte", rim=False)
        c.ellipse(u, v + 0.055, r, r * TILT, (0.96, 0.97, 0.98), lift=0)
        c.ellipse(u, v + 0.052, r * 0.84, r * TILT * 0.84, scale(col, 0.7) if col[0] < 0.9 or col[2] < 0.9 else (0.8, 0.8, 0.82), lift=0)
        c.ellipse(u, v + 0.056, r * 0.78, r * TILT * 0.78, col, lift=0.1)
        soft_disc(c, u - r * 0.25, v + 0.062, r * 0.35, r * 0.14, WHITE, 0.8, 1.0, add=True)
        if col[0] < 0.2 and col[1] < 0.2:
            soft_disc(c, u - r * 0.25, v + 0.062, r * 0.5, r * 0.2, (0.6, 0.6, 0.7), 0.5, 1.0, add=True)
    craft.arc(c, 0.0, 0.075, 0.60, 0.016, 180, 360, 0.006, WHITE, 0.45, steps=6)


def _icon_heart(c, u, v, s, ink, spot):
    pts = []
    for k in range(28):
        t = 2 * math.pi * k / 28
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 17.0, y / 17.0))
    c.poly([(u + x * s * 1.14, v + y * s * 1.14) for x, y in pts], ink, lift=0)
    c.poly([(u + x * s * 0.92, v + y * s * 0.92) for x, y in pts], spot, lift=0.1)
    c.line(u - s * 0.55, v + s * 0.15, u - s * 0.2, v + s * 0.55, s * 0.08, WHITE, 0.6)
    # ribbon
    c.rect(u, v - s * 0.78, s * 1.5, s * 0.30, (0.97, 0.93, 0.82), lift=0.0)
    c.rect(u, v - s * 0.78, s * 1.5, s * 0.02, ink, lift=0)
    c.line(u - s * 0.55, v - s * 0.78, u + s * 0.55, v - s * 0.78, s * 0.05, ink, 0.9)


def _icon_dagger(c, u, v, s, ink, spot):
    c.poly([(u - s * 0.20, v - s * 0.2), (u + s * 0.20, v - s * 0.2), (u + s * 0.16, v + s * 0.85), (u, v + s * 1.05), (u - s * 0.16, v + s * 0.85)], ink, lift=0)
    c.poly([(u - s * 0.15, v - s * 0.15), (u + s * 0.15, v - s * 0.15), (u + s * 0.11, v + s * 0.8), (u, v + s * 0.98), (u - s * 0.11, v + s * 0.8)], (0.82, 0.84, 0.88), lift=0.15)
    c.line(u, v - s * 0.1, u, v + s * 0.9, s * 0.03, (0.45, 0.47, 0.52), 0.8)
    c.rect(u, v - s * 0.24, s * 0.72, s * 0.12, ink, r=s * 0.04, lift=0)
    c.rect(u, v - s * 0.24, s * 0.62, s * 0.06, spot, lift=0.1)
    c.rect(u, v - s * 0.60, s * 0.14, s * 0.55, ink, lift=0)
    c.ellipse(u, v - s * 0.92, s * 0.14, s * 0.14, ink, lift=0)
    c.ellipse(u, v - s * 0.92, s * 0.08, s * 0.08, spot, lift=0.1)


def _icon_anchor(c, u, v, s, ink, spot):
    w = s * 0.085
    craft.arc(c, u, v + s * 0.85, s * 0.17, s * 0.17, 0, 360, w, ink, 1.0, steps=14)
    c.line(u, v + s * 0.68, u, v - s * 0.78, w, ink, 1.0)
    c.line(u - s * 0.40, v + s * 0.40, u + s * 0.40, v + s * 0.40, w, ink, 1.0)
    craft.arc(c, u, v - s * 0.35, s * 0.62, s * 0.52, 190, 350, w * 1.1, ink, 1.0, steps=14)
    c.poly([(u - s * 0.67, v - s * 0.30), (u - s * 0.50, v - s * 0.18), (u - s * 0.72, v - s * 0.10)], ink, lift=0)
    c.poly([(u + s * 0.67, v - s * 0.30), (u + s * 0.50, v - s * 0.18), (u + s * 0.72, v - s * 0.10)], ink, lift=0)
    craft.arc(c, u, v - s * 0.35, s * 0.62, s * 0.52, 215, 325, w * 0.45, spot, 0.9, steps=10)


def _icon_rose(c, u, v, s, ink, spot):
    for k in range(5):
        a = math.radians(90 + k * 72 + 18)
        _leaf(c, u + math.cos(a) * s * 0.35, v + math.sin(a) * s * 0.35 - s * 0.3, s * 0.55, math.degrees(a) - 10, ink, 0.5, vein=False)
    c.ellipse(u, v, s * 0.62, s * 0.60, ink, lift=0)
    c.ellipse(u, v, s * 0.55, s * 0.53, spot, lift=0.12)
    for r, a0, a1 in ((0.45, 20, 330), (0.34, 80, 380), (0.22, 140, 440), (0.11, 200, 500)):
        craft.arc(c, u, v, s * r, s * r * 0.95, a0, a1, s * 0.05, ink, 1.0, steps=10)
    c.line(u, v - s * 0.55, u - s * 0.05, v - s * 1.0, s * 0.06, ink, 1.0)


def _icon_star(c, u, v, s, ink, spot):
    pts = []
    for k in range(10):
        a = math.radians(90 + k * 36)
        r = s * (0.72 if k % 2 == 0 else 0.30)
        pts.append((u + math.cos(a) * r, v + math.sin(a) * r))
    c.poly([(u + (x - u) * 1.18, v + (y - v) * 1.18) for x, y in pts], ink, lift=0)
    c.poly(pts, spot, lift=0.1)
    c.ellipse(u, v, s * 0.12, s * 0.12, ink, lift=0)


def _icon_skull(c, u, v, s, ink, spot):
    c.ellipse(u, v + s * 0.15, s * 0.58, s * 0.55, ink, lift=0)
    c.ellipse(u, v + s * 0.17, s * 0.52, s * 0.49, (0.96, 0.94, 0.88), lift=0.1)
    c.rect(u, v - s * 0.42, s * 0.50, s * 0.30, ink, r=s * 0.05, lift=0)
    c.rect(u, v - s * 0.42, s * 0.44, s * 0.24, (0.96, 0.94, 0.88), r=s * 0.04, lift=0.1)
    for sgn in (-1, 1):
        c.ellipse(u + sgn * s * 0.22, v + s * 0.12, s * 0.15, s * 0.17, ink, lift=0)
        c.ellipse(u + sgn * s * 0.22, v + s * 0.12, s * 0.06, s * 0.06, spot, lift=0.2)
    c.poly([(u - s * 0.06, v - s * 0.10), (u + s * 0.06, v - s * 0.10), (u, v + s * 0.0)], ink, lift=0)
    for k in range(4):
        c.line(u - s * 0.15 + k * s * 0.10, v - s * 0.34, u - s * 0.15 + k * s * 0.10, v - s * 0.5, s * 0.025, ink, 1.0)


@sprop("care_tat_flash", aspect=1.4, fill=0.78)
def tat_flash(c, color):
    """Flash art on the wall: three paper sheets pinned with tape, each with classic designs (heart and banner, dagger, anchor, rose, star, skull)."""
    rng = c.rng
    ink = (0.07, 0.06, 0.08)
    red, blue = (0.85, 0.15, 0.18), (0.14, 0.38, 0.78)
    kd = 0.50 if _pal(color, "mood", "") == "dark" else 1.0
    # sheets: (u, v, w, h, designs)
    sheets = ((-0.42, 0.40, 0.46, 0.74, (_icon_heart, _icon_dagger, _icon_rose, _icon_star), (0.97, 0.94, 0.84)),
              (0.12, 0.34, 0.58, 0.64, (_icon_anchor, _icon_skull, _icon_heart, _icon_dagger), (0.95, 0.90, 0.78)),
              (0.56, 0.44, 0.34, 0.60, (_icon_rose, _icon_star, _icon_anchor), (0.98, 0.95, 0.88)))
    for (u, v, w, h, icons, paper) in sheets:
        paper = scale(paper, kd)
        soft_disc(c, u + 0.02, v - 0.02, w * 0.62, h * 0.58, BLACK, 0.35, 1.3)
        c.rect(u, v, w, h, scale(paper, 0.78), lift=0.0)
        c.rect(u, v, w - 0.012, h - 0.012, paper, lift=0.08)
        soft_disc(c, u - w * 0.2, v + h * 0.2, w * 0.5, h * 0.4, WHITE, 0.35, 1.3, add=True)
        for _ in range(4):                                         # paper stains
            c.ellipse(u + rng.uniform(-w * 0.4, w * 0.4), v + rng.uniform(-h * 0.4, h * 0.4), rng.uniform(0.012, 0.03), rng.uniform(0.01, 0.025),
                      scale(paper, 0.85), alpha=0.3, lift=0)
        cols, rows = (2, 2) if len(icons) == 4 else ((1, 3) if len(icons) == 3 and w < 0.4 else (3, 1))
        if len(icons) == 3 and w >= 0.4:
            cols, rows = 2, 2
        k = 0
        for ri in range(rows):
            for ci in range(cols):
                if k >= len(icons):
                    break
                cu = u - w / 2 + (ci + 0.5) * w / cols
                cv = v + h / 2 - (ri + 0.5) * h / rows
                s = min(w / cols, h / rows) * 0.36
                icons[k](c, cu, cv, s, ink, scale(red if (k + ri) % 2 == 0 else blue, 0.5 + 0.5 * kd))
                k += 1
        c.rect(u, v + h / 2 - 0.002, w * 0.25, 0.04, (0.92, 0.88, 0.72), lift=0, alpha=0.8)          # tape
        c.rect(u, v - h / 2 + 0.002, w * 0.18, 0.03, (0.92, 0.88, 0.72), lift=0, alpha=0.75)


@sprop("care_tat_stencil", aspect=2.4, fill=0.24)
def tat_stencil(c, color):
    """A stencil transfer sheet with a purple floral design, a stylus pen and a roll of green soap bottle cap beside it."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.12, 0.45)
    paper = (0.88, 0.84, 0.94)
    pts = [(-0.30, 0.03), (0.26, 0.03), (0.32, 0.22), (-0.22, 0.22)]
    c.poly([(x + 0.015, y - 0.012) for x, y in pts], BLACK, alpha=0.30)
    _vpoly(c, pts, scale(paper, 1.08), scale(paper, 0.88))
    soft_disc(c, -0.1, 0.17, 0.2, 0.03, WHITE, 0.4, 1.2, add=True)
    pur = (0.35, 0.22, 0.60)
    # flower: petals as arcs and strokes, with leaves
    fu, fv = 0.0, 0.125
    for k in range(8):
        a = 2 * math.pi * k / 8
        c.ellipse(fu + math.cos(a) * 0.06, fv + math.sin(a) * 0.034, 0.038, 0.016, pur, angle=math.degrees(a), lift=0, alpha=0.0)
        craft.arc(c, fu + math.cos(a) * 0.055, fv + math.sin(a) * 0.030, 0.034, 0.016, math.degrees(a) - 100, math.degrees(a) + 100, 0.003, pur, 0.9, steps=6,
                  angle=math.degrees(a))
    _ring(c, fu, fv, 0.024, 0.013, 0.003, pur, 0.9, steps=10)
    c.ellipse(fu, fv, 0.006, 0.004, pur, lift=0)
    for sgn in (-1, 1):
        _leaf(c, fu + sgn * 0.11, fv - 0.01, 0.08, 0 if sgn > 0 else 180, pur, 0.35, vein=False)
        craft.strand(c, fu + sgn * 0.10, fv - 0.02, 0.07, 0 if sgn > 0 else 180, 0.003, pur, 0.8, 0.4)
    c.line(-0.20, 0.20, 0.20, 0.20, 0.0025, pur, 0.5)
    # stylus pen
    c.line(0.30, 0.095, 0.50, 0.13, 0.026, (0.10, 0.10, 0.12), 1.0)
    c.line(0.30, 0.103, 0.50, 0.138, 0.007, (0.8, 0.82, 0.88), 0.7)
    c.line(0.285, 0.092, 0.31, 0.097, 0.012, (0.75, 0.77, 0.82), 1.0)
    # soap bottle cap
    craft.hshade_box(c, -0.45, 0.07, 0.13, 0.10, (0.45, 0.85, 0.55), (0.12, 0.45, 0.25), r=0.03)
    c.ellipse(-0.45, 0.12, 0.065, 0.022, (0.55, 0.92, 0.62), lift=0.1)
    soft_disc(c, -0.48, 0.08, 0.012, 0.03, WHITE, 0.6, 1.0, add=True)


@niche("tattoo", "Tattoo studio", subjects=("care_tat_machine",),
       strong=("tattoo studio", "tattoo artist", "tattoo parlour", "tattoo parlor", "tattoo shop", "piercing", "body art", "tattoo removal", "tattoos",
               "tatoo", "tattoo", "टैटू", "टैटू स्टूडियो", "गोदना", "टैटू आर्टिस्ट"),
       weak=("ink", "body piercing", "skin art", "inked", "permanent ink", "flash art", "बॉडी आर्ट"),
       avoid=("mehendi", "henna", "salon"), accent="#e53935", mood="dark", group="events")
def tattoo(S):
    P = S.pal
    dark = _dark(S)
    red = (1.0, 0.18, 0.20)
    gl = 1.0 if dark else 0.6
    brick = mix(P.wall_bot, (0.45, 0.2, 0.15), 0.35 if not dark else 0.18)
    with S.far():
        S.wall(mix(P.wall_top, brick, 0.5), mix(P.wall_bot, brick, 0.5), 0.58)
        # brick wall courses
        for row in range(11):
            v = row * 0.056
            off = 0.0 if row % 2 else 0.12
            for k in range(-20, 28):
                u = off + k * 0.24
                tone = S.rng.uniform(0.72, 1.18)
                S.rect(u + 0.12, v + 0.028, 0.232, 0.050, scale(brick, tone), lift=0.0)
        # neon sign: bloom + hot core
        S.glow(1.29, 0.24, 0.8, red, 0.42 * (1.0 if dark else 0.5), 1.6)
        S.text("INK", 1.29, 0.24, 0.20, scale(red, 0.55), 0.40)
        S.text("INK", 1.29, 0.24, 0.20, (1.0, 0.55, 0.55), 0.16)
        S.bokeh(8, 0.0, 0.06, 2.0, 0.5, [(1.0, 0.3, 0.3), (1.0, 0.55, 0.4), (0.4, 0.5, 1.0)], 0.012, 0.04, 0.3 * (1.0 if dark else 0.6))
        S.floor(0.58, P.floor_top, P.floor_bot)
    # sharp flash-art sheets pinned on the brick wall
    S.put("care_tat_flash", 0.78, 0.60, 0.44, color=P, shadow=False, framed=False)
    S.put("care_tat_flash", 1.78, 0.60, 0.42, color=P, shadow=False, framed=False)
    # dark leather tattoo bench with diamond tufting
    leather = (0.13, 0.08, 0.075) if dark else (0.30, 0.18, 0.14)
    S.floor(0.58, scale(leather, 1.35), scale(leather, 0.55))
    S.rect(1.0, 0.58, 14.0, 0.010, scale(leather, 0.3), lift=0.0)
    S.rect(1.0, 0.592, 14.0, 0.006, scale(leather, 2.2), lift=0.0, alpha=0.6)
    rows = (0.70, 0.80, 0.94, 1.14)
    for ri, v in enumerate(rows):
        sp = 0.18 + ri * 0.05
        for k in range(-24, 30):
            u = k * sp + (sp / 2 if ri % 2 else 0.0)
            if ri < len(rows) - 1:
                nv = rows[ri + 1]
                nsp = 0.18 + (ri + 1) * 0.05
                nu = (u + nsp / 2) if (ri + 1) % 2 else (u - nsp / 2 + (0 if ri % 2 == 0 else 0))
            S.circle(u, v, 0.007 + ri * 0.002, scale(leather, 0.5), lift=0.0)
            S.circle(u - 0.002, v - 0.002, 0.0035 + ri * 0.001, scale(leather, 2.6), lift=0.0, alpha=0.8)
    for ri, v in enumerate(rows[:-1]):                                             # tufting creases between the button rows
        S.line(-3, v + 0.045 + ri * 0.012, 5, v + 0.045 + ri * 0.012, 0.003, scale(leather, 0.4), 0.5)
    S.soft(1.1, 0.80, 1.0, 0.16, (1.0, 0.3, 0.3) if dark else (1.0, 0.9, 0.8), 0.20 * (1.0 if dark else 0.5), 1.4, add=True)
    S.soft(1.1, 0.74, 0.8, 0.10, (1.0, 0.85, 0.7), 0.18, 1.5, add=True)
    S.put("care_tat_inks", 0.72, 0.84, 0.24, shadow_w=0.55)
    S.put("care_tat_machine", 1.10, 0.97, 0.38, subject=True, shadow_w=0.8)
    S.put("care_tat_stencil", 1.52, 0.90, 0.10, shadow_w=0.4)
    S.focus("detail", 1.10, 0.86)
    S.soft(1.1, 0.88, 0.45, 0.12, red, 0.26 if dark else 0.12, 1.6, add=True)           # neon rim light on the props
    S.soft(0.70, 0.78, 0.35, 0.10, red, 0.20 if dark else 0.10, 1.6, add=True)
    with S.near():
        S.soft(0.42, 1.12, 0.35, 0.12, BLACK, 0.7, 1.0)
        S.circle(1.90, 0.66, 0.05, (1.0, 0.3, 0.3), alpha=0.36, lift=0)


# ====================================================================================== PET SHOP
def _paw(c, u, v, s, col, alpha=1.0):
    """A paw print: one pad and four toes."""
    c.ellipse(u, v, s * 0.55, s * 0.45, col, lift=0, alpha=alpha)
    for k, (dx, dy) in enumerate(((-0.62, 0.55), (-0.22, 0.95), (0.22, 0.95), (0.62, 0.55))):
        c.ellipse(u + dx * s, v + dy * s, s * 0.22, s * 0.28, col, lift=0, alpha=alpha, angle=(-1 if dx < 0 else 1) * 14)


def _fish(c, u, v, ln, col1, col2, d=1, stripe=None):
    """A little fish swimming to the right (d=1) or left (d=-1)."""
    h = ln * 0.52
    c.poly([(u - d * ln * 0.38, v), (u - d * ln * 0.78, v + h * 0.55), (u - d * ln * 0.70, v), (u - d * ln * 0.78, v - h * 0.55)], col2, lift=0.1, alpha=0.95)
    c.poly([(u - d * ln * 0.10, v + h * 0.40), (u + d * ln * 0.10, v + h * 0.95), (u - d * ln * 0.25, v + h * 0.40)], col2, lift=0.1, alpha=0.95)
    c.ellipse(u, v, ln * 0.50, h * 0.50, scale(col1, 0.75), lift=0.0)
    c.ellipse(u, v + h * 0.04, ln * 0.48, h * 0.46, col1, lift=0.2)
    c.ellipse(u + d * ln * 0.02, v - h * 0.14, ln * 0.40, h * 0.22, mix(col1, WHITE, 0.45), alpha=0.7, lift=0)
    if stripe:
        for k in (-0.1, 0.12):
            c.rect(u + d * ln * k, v, ln * 0.06, h * 0.78, stripe, lift=0, alpha=0.85)
    c.ellipse(u + d * ln * 0.30, v + h * 0.08, ln * 0.055, ln * 0.055, WHITE, lift=0)
    c.ellipse(u + d * ln * 0.31, v + h * 0.08, ln * 0.028, ln * 0.028, BLACK, lift=0)
    soft_disc(c, u - d * ln * 0.05, v + h * 0.22, ln * 0.18, h * 0.08, WHITE, 0.55, 1.0, add=True)


@sprop("care_pet_foodbag", aspect=0.68, fill=1.0)
def pet_foodbag(c, color):
    """A bag of dog food: glossy laminate in the shop colours, crimped top seal, cream label with a happy dog, 'DOG FOOD' and paw prints."""
    rng = c.rng
    acc = _pal(color, "accent", (0.95, 0.60, 0.10))
    main = mix(acc, (0.62, 0.28, 0.04), 0.30)
    ao(c, 0.0, 0.0, 0.8, 0.13, 0.65)
    soft_disc(c, 0.02, 0.01, 0.34, 0.03, BLACK, 0.5, 1.2)
    body = [(-0.28, 0.02), (0.28, 0.02), (0.305, 0.28), (0.315, 0.55), (0.305, 0.80), (0.29, 0.89), (-0.29, 0.89), (-0.305, 0.80), (-0.315, 0.55), (-0.305, 0.28)]
    _hpoly(c, body, scale(main, 1.28), scale(main, 0.55), 0.05, power=1.15, smooth=2)
    # darker base and a lighter band of colour at the top
    soft_disc(c, 0.0, 0.02, 0.32, 0.10, BLACK, 0.40, 1.3)
    _hpoly(c, [(-0.31, 0.72), (0.31, 0.72), (0.30, 0.80), (0.29, 0.89), (-0.29, 0.89), (-0.30, 0.80)], scale(acc, 1.25), scale(acc, 0.62), 0.0)
    for k in range(3):
        _paw(c, -0.15 + k * 0.15, 0.775 - (0.03 if k % 2 else 0.0), 0.034, scale(WHITE, 0.95), 0.9)
    # crimped top seal
    craft.hshade_box(c, 0.0, 0.925, 0.585, 0.075, scale(main, 1.2), scale(main, 0.55), r=0.012)
    for k in range(30):
        x = -0.28 + k * 0.0193
        c.line(x, 0.89, x + 0.002, 0.962, 0.0028, scale(main, 0.45 if k % 2 else 1.5), 0.55)
    c.rect(0.0, 0.964, 0.58, 0.006, WHITE, lift=0, alpha=0.35)
    # label panel: cream rounded card with a dog's head
    c.rect(0.0, 0.46, 0.46, 0.44, scale(main, 0.45), r=0.07, lift=0.1)
    c.rect(0.0, 0.46, 0.44, 0.42, (0.98, 0.94, 0.84), r=0.065, lift=0.08)
    soft_disc(c, -0.08, 0.60, 0.22, 0.15, WHITE, 0.5, 1.2, add=True)
    brown, dk = (0.62, 0.38, 0.20), (0.34, 0.19, 0.09)
    for sgn in (-1, 1):                                                              # floppy ears
        c.ellipse(sgn * 0.115, 0.575, 0.055, 0.105, dk, lift=0.15, angle=sgn * 14)
    c.ellipse(0.0, 0.575, 0.125, 0.115, brown, lift=0.2)
    c.ellipse(0.0, 0.545, 0.075, 0.06, (0.90, 0.76, 0.56), lift=0.15)
    c.ellipse(0.0, 0.57, 0.026, 0.018, (0.08, 0.06, 0.06), lift=0.3)
    c.line(0.0, 0.555, 0.0, 0.52, 0.006, (0.2, 0.1, 0.08), 0.9)
    c.ellipse(0.0, 0.505, 0.03, 0.025, (0.95, 0.45, 0.50), lift=0.15)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.052, 0.605, 0.016, 0.019, (0.10, 0.07, 0.06), lift=0)
        c.ellipse(sgn * 0.052 - 0.004, 0.612, 0.005, 0.006, WHITE, lift=0)
    c.rect(0.0, 0.452, 0.14, 0.022, (0.82, 0.14, 0.16), r=0.01, lift=0.2)
    c.ellipse(0.0, 0.436, 0.017, 0.017, (0.95, 0.80, 0.25), lift=0.3)
    c.text("DOG FOOD", 0.0, 0.365, 0.058, scale(main, 0.55), 0.20)
    c.text("COMPLETE NUTRITION", 0.0, 0.318, 0.020, scale(main, 0.6), 0.14)
    c.rect(0.0, 0.29, 0.34, 0.004, scale(main, 0.7), lift=0, alpha=0.6)
    # weight badge
    c.ellipse(0.19, 0.19, 0.06, 0.06, (0.98, 0.95, 0.88), lift=0.1)
    c.text("20", 0.19, 0.20, 0.036, scale(main, 0.5), 0.2)
    c.text("KG", 0.19, 0.165, 0.016, scale(main, 0.5), 0.15)
    # laminate gloss and shading, wrinkles near the seal and bottom
    soft_disc(c, -0.23, 0.50, 0.03, 0.34, WHITE, 0.22, 1.2, add=True)
    soft_disc(c, 0.28, 0.45, 0.07, 0.36, BLACK, 0.30, 1.3)
    soft_disc(c, 0.0, 0.88, 0.30, 0.04, BLACK, 0.22, 1.3)
    for _ in range(10):
        x, y = rng.uniform(-0.27, 0.27), rng.choice((rng.uniform(0.80, 0.88), rng.uniform(0.03, 0.12)))
        c.line(x, y, x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.04, 0.04), 0.003, scale(main, rng.choice((0.4, 1.6))), 0.28)


@sprop("care_pet_aquarium", aspect=1.40, fill=1.0)
def pet_aquarium(c, color):
    """A small aquarium on a cabinet: LED lid with light rays, tinted water, gravel and pebbles, plants, a rock, rising bubbles and three fish."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.18, 0.6)
    wood = (0.28, 0.19, 0.13)
    # cabinet
    craft.hshade_box(c, 0.0, 0.17, 1.30, 0.34, scale(wood, 1.4), scale(wood, 0.62), r=0.01)
    c.rect(0.0, 0.17, 1.18, 0.27, scale(wood, 0.95), r=0.01, lift=0.1)
    c.line(0.0, 0.04, 0.0, 0.30, 0.006, scale(wood, 0.5), 0.8)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.06, 0.18, 0.012, 0.03, (0.8, 0.8, 0.84), lift=0.3)
    c.rect(0.0, 0.335, 1.32, 0.012, scale(wood, 1.9), lift=0, alpha=0.7)
    # tank: back wall, water, gravel
    x0, x1, y0, y1 = -0.62, 0.62, 0.36, 0.90
    c.rect(0.0, 0.63, 1.24, 0.54, (0.12, 0.38, 0.50), lift=0.0)
    _vpoly(c, [(x0, y1), (x1, y1), (x1, y0), (x0, y0)], (0.62, 0.90, 0.94), (0.10, 0.46, 0.58))
    soft_disc(c, -0.15, 0.82, 0.55, 0.20, (0.9, 1.0, 1.0), 0.28, 1.3, add=True)
    # light rays from the lid
    for (a, b, w) in ((-0.35, -0.20, 0.10), (0.05, 0.12, 0.14), (0.40, 0.30, 0.10)):
        c.poly([(a - w / 2, y1), (a + w / 2, y1), (b + w * 1.3, y0 + 0.03), (b - w * 1.3, y0 + 0.03)], WHITE, alpha=0.10)
    # gravel with pebbles
    c.rect(0.0, 0.405, 1.24, 0.09, (0.78, 0.66, 0.46), lift=0.1)
    for _ in range(44):
        u, v = rng.uniform(-0.60, 0.60), rng.uniform(0.37, 0.45)
        c.ellipse(u, v, rng.uniform(0.010, 0.022), rng.uniform(0.007, 0.013), rng.choice(((0.88, 0.80, 0.64), (0.55, 0.45, 0.32), (0.92, 0.90, 0.86), (0.38, 0.34, 0.30))), lift=0.2)
    # rock
    c.ellipse(0.28, 0.46, 0.12, 0.07, (0.35, 0.36, 0.40), lift=0.2)
    c.ellipse(0.26, 0.50, 0.08, 0.06, (0.46, 0.47, 0.52), lift=0.2)
    soft_disc(c, 0.23, 0.53, 0.04, 0.02, WHITE, 0.4, 1.0, add=True)
    # plants swaying
    for (bx, n, hh) in ((-0.50, 4, 0.36), (-0.38, 3, 0.26), (0.52, 3, 0.30)):
        for k in range(n):
            _leaf(c, bx + k * 0.02, 0.42, hh * rng.uniform(0.8, 1.1), 90 + (k - n / 2.0) * 12 + rng.uniform(-6, 6), (0.12 + 0.12 * rng.random(), 0.52 + 0.18 * rng.random(), 0.22), 0.20)
    # bubbles
    for k in range(9):
        r = 0.008 + 0.002 * (k % 3)
        c.ellipse(0.05 + 0.012 * math.sin(k * 1.7), 0.45 + k * 0.05, r, r, (0.9, 1.0, 1.0), alpha=0.6, lift=0)
        soft_disc(c, 0.05 + 0.012 * math.sin(k * 1.7) - r * 0.3, 0.45 + k * 0.05 + r * 0.3, r * 0.5, r * 0.5, WHITE, 0.8, 1.0, add=True)
    c.ellipse(0.05, 0.435, 0.025, 0.012, (0.25, 0.25, 0.3), lift=0.2)
    # fish
    _fish(c, -0.18, 0.66, 0.20, (0.98, 0.52, 0.10), (0.98, 0.35, 0.05), 1)
    _fish(c, 0.30, 0.74, 0.16, (0.98, 0.60, 0.15), (0.95, 0.30, 0.06), -1)
    _fish(c, 0.02, 0.56, 0.14, (0.25, 0.55, 0.95), (0.98, 0.85, 0.2), 1, stripe=(0.98, 0.95, 0.4))
    # water surface, glass reflections and silicone corners
    c.rect(0.0, y1 - 0.012, 1.24, 0.012, (0.85, 1.0, 1.0), lift=0, alpha=0.7)
    c.poly([(-0.55, 0.88), (-0.45, 0.88), (-0.30, 0.40), (-0.40, 0.40)], WHITE, alpha=0.13)
    c.rect(-0.58, 0.63, 0.016, 0.50, WHITE, lift=0, alpha=0.4, r=0.008)
    for x in (x0, x1):
        c.rect(x, 0.63, 0.012, 0.56, (0.08, 0.1, 0.12), lift=0, alpha=0.8)
    c.rect(0.0, y0 - 0.005, 1.28, 0.016, (0.08, 0.08, 0.10), lift=0.2, r=0.004)
    # lid with a glowing LED bar
    craft.hshade_box(c, 0.0, 0.935, 1.30, 0.075, (0.30, 0.32, 0.36), (0.05, 0.05, 0.07), r=0.01)
    c.rect(0.0, 0.905, 1.16, 0.010, (0.95, 1.0, 1.0), lift=0)
    soft_disc(c, 0.0, 0.895, 0.7, 0.05, (0.85, 1.0, 1.0), 0.55, 1.4, add=True)
    c.rect(0.0, 0.962, 1.22, 0.006, WHITE, lift=0, alpha=0.35)


@sprop("care_pet_cage", aspect=0.78, fill=1.0)
def pet_cage(c, color):
    """A brass bird cage: onion dome, vertical bars, a perch with a little budgie, a swing and a seed cup, on a tray base."""
    rng = c.rng
    brass = (0.88, 0.68, 0.28)
    ao(c, 0.0, 0.0, 0.8, 0.13, 0.55)
    soft_disc(c, 0.02, 0.01, 0.4, 0.03, BLACK, 0.5, 1.2)
    acc = _pal(color, "accent_dark", (0.45, 0.28, 0.05))
    # base tray and seed scatter
    craft.hshade_box(c, 0.0, 0.05, 0.74, 0.10, scale(brass, 1.2), scale(brass, 0.45), r=0.02)
    c.rect(0.0, 0.10, 0.70, 0.016, scale(acc, 1.2), r=0.006, lift=0.2)
    for _ in range(12):
        c.ellipse(rng.uniform(-0.30, 0.30), 0.118 + rng.uniform(0, 0.01), 0.007, 0.004, (0.88, 0.76, 0.4), lift=0)
    # inside back: darker space between the bars
    _hpoly(c, [(-0.31, 0.11), (0.31, 0.11), (0.31, 0.60), (0.20, 0.78), (0.0, 0.92), (-0.20, 0.78), (-0.31, 0.60)], (0.94, 0.90, 0.78), (0.64, 0.58, 0.46), 0.0, alpha=0.18, smooth=2)
    # perch, swing, seed cup
    c.line(-0.31, 0.36, 0.31, 0.36, 0.018, (0.55, 0.36, 0.18), 1.0)
    c.line(-0.31, 0.368, 0.31, 0.368, 0.005, (0.85, 0.65, 0.4), 0.6)
    c.line(-0.18, 0.60, -0.18, 0.46, 0.004, (0.5, 0.4, 0.25), 0.9)
    craft.arc(c, -0.18, 0.40, 0.04, 0.012, 180, 360, 0.010, (0.8, 0.2, 0.2), 1.0, steps=6)
    craft.hshade_box(c, -0.27, 0.20, 0.07, 0.05, (0.85, 0.25, 0.22), (0.45, 0.08, 0.08), r=0.01)
    # budgie
    bu, bv = 0.10, 0.37
    c.poly([(bu - 0.02, bv + 0.12), (bu + 0.02, bv + 0.12), (bu + 0.03, bv - 0.01), (bu - 0.015, bv - 0.01)], (0.2, 0.45, 0.85), lift=0.1)
    c.ellipse(bu, bv + 0.12, 0.062, 0.088, (0.40, 0.76, 0.22), lift=0.2)
    c.ellipse(bu + 0.03, bv + 0.12, 0.034, 0.072, (0.22, 0.52, 0.2), lift=0.1, angle=-10)
    c.ellipse(bu - 0.01, bv + 0.115, 0.045, 0.052, (0.95, 0.94, 0.5), lift=0.0, alpha=0.0)
    c.ellipse(bu - 0.012, bv + 0.225, 0.052, 0.052, (0.98, 0.88, 0.30), lift=0.2)
    c.ellipse(bu - 0.040, bv + 0.208, 0.016, 0.014, (0.35, 0.55, 0.95), lift=0.1)
    c.ellipse(bu - 0.036, bv + 0.232, 0.013, 0.013, WHITE, lift=0)
    c.ellipse(bu - 0.037, bv + 0.232, 0.007, 0.007, BLACK, lift=0)
    c.poly([(bu - 0.058, bv + 0.220), (bu - 0.082, bv + 0.210), (bu - 0.058, bv + 0.200)], (0.98, 0.65, 0.18), lift=0.1)
    for k in range(4):
        c.line(bu - 0.02 + k * 0.012, bv + 0.14, bu - 0.01 + k * 0.012, bv + 0.20, 0.003, (0.1, 0.2, 0.1), 0.4)
    soft_disc(c, bu - 0.03, bv + 0.16, 0.03, 0.05, WHITE, 0.35, 1.1, add=True)
    for dx in (-0.01, 0.025):
        c.line(bu + dx, bv + 0.03, bu + dx, bv + 0.005, 0.005, (0.95, 0.6, 0.45), 1.0)
    # bars: straight below the shoulder, converging into the dome above it
    bars = [-0.30 + k * 0.05 for k in range(13)]
    for x in bars:
        lit = 0.8 if x < 0 else 0.5
        c.line(x, 0.11, x, 0.60, 0.0085, scale(brass, 0.55), 1.0)
        c.line(x - 0.0012, 0.11, x - 0.0012, 0.60, 0.0035, scale(brass, 1.5), lit)
        pts = [(x, 0.60), (x * 0.86, 0.70), (x * 0.52, 0.80), (x * 0.20, 0.88), (0.0, 0.92)]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], 0.0075, scale(brass, 0.6), 1.0)
            c.line(a[0] - 0.001, a[1], b[0] - 0.001, b[1], 0.003, scale(brass, 1.5), 0.6)
    for v in (0.60, 0.25):
        c.line(-0.31, v, 0.31, v, 0.012, scale(brass, 0.8), 1.0)
        c.line(-0.31, v + 0.003, 0.31, v + 0.003, 0.004, scale(brass, 1.6), 0.7)
    # finial and hanging ring
    c.ellipse(0.0, 0.935, 0.030, 0.030, scale(brass, 1.1), lift=0.3)
    craft.arc(c, 0.0, 0.965, 0.06, 0.05, 0, 180, 0.010, scale(brass, 0.9), 1.0, steps=8)
    gloss(c, -0.02, 0.945, 0.012, 0.012, 0, 0.9)


@sprop("care_pet_rack", aspect=0.95, fill=1.0)
def pet_rack(c, color):
    """A pegboard on the wall with hooks and hanging collars (buckles, tags), leashes with clips and a rubber bone toy."""
    rng = c.rng
    acc = _pal(color, "accent", (0.95, 0.60, 0.10))
    panel = mix(_pal(color, "accent_light", (0.98, 0.85, 0.55)), WHITE, 0.45)
    c.rect(0.0, 0.5, 0.94, 0.98, scale(panel, 0.62), r=0.02, lift=0.0)
    craft.hshade_box(c, 0.0, 0.5, 0.92, 0.96, scale(panel, 1.05), scale(panel, 0.88), r=0.02)
    soft_disc(c, -0.2, 0.7, 0.45, 0.35, WHITE, 0.18, 1.3, add=True)
    for i in range(10):
        for j in range(11):
            c.ellipse(-0.40 + i * 0.089, 0.06 + j * 0.088, 0.008, 0.008, scale(panel, 0.45), lift=0, alpha=0.8)
    cols = ((0.85, 0.16, 0.20), (0.15, 0.40, 0.85), (0.18, 0.60, 0.32), (0.90, 0.45, 0.10), (0.55, 0.25, 0.70), (0.10, 0.10, 0.12))
    # collars: tall rings hanging from hooks
    for i, u in enumerate((-0.28, 0.0, 0.28)):
        col = cols[(i * 2) % 6]
        v = 0.88
        soft_disc(c, u + 0.02, v - 0.11, 0.09, 0.14, BLACK, 0.30, 1.2)
        c.ellipse(u, v - 0.12, 0.080, 0.125, scale(col, 0.6), lift=0.0)
        c.ellipse(u, v - 0.12, 0.062, 0.108, mix(panel, scale(panel, 0.8), 0.5), lift=0.0)
        craft.arc(c, u, v - 0.12, 0.071, 0.117, 90, 270, 0.012, scale(col, 1.3), 0.8, steps=10)
        for k in range(5):
            a = math.radians(40 + k * 18 + 180)
            c.ellipse(u + math.cos(a) * 0.071, v - 0.12 + math.sin(a) * 0.117, 0.004, 0.004, WHITE, lift=0, alpha=0.55)
        c.rect(u, v - 0.23, 0.032, 0.024, (0.85, 0.7, 0.3), r=0.004, lift=0.3)
        c.ellipse(u, v - 0.27, 0.026, 0.026, (0.95, 0.80, 0.30), lift=0.3)
        c.ellipse(u, v - 0.27, 0.013, 0.013, scale((0.95, 0.80, 0.30), 0.7), lift=0, alpha=0.8)
        soft_disc(c, u - 0.008, v - 0.262, 0.008, 0.008, WHITE, 0.9, 1.0, add=True)
        c.line(u, v + 0.02, u, v + 0.0, 0.008, (0.7, 0.72, 0.78), 1.0)
        c.ellipse(u, v + 0.02, 0.012, 0.012, (0.8, 0.82, 0.88), lift=0.3)
    # leashes: long loops with clips
    for i, u in enumerate((-0.30, 0.0)):
        col = cols[(i * 2 + 1) % 6]
        v = 0.52
        soft_disc(c, u + 0.02, v - 0.14, 0.06, 0.24, BLACK, 0.25, 1.2)
        craft.arc(c, u, v - 0.11, 0.055, 0.21, 0, 360, 0.016, scale(col, 0.75), 1.0, steps=22)
        craft.arc(c, u, v - 0.11, 0.055, 0.21, 100, 250, 0.008, scale(col, 1.45), 0.7, steps=10)
        c.rect(u + 0.055, v - 0.33, 0.026, 0.050, (0.78, 0.8, 0.85), r=0.006, lift=0.3)
        c.ellipse(u + 0.055, v - 0.37, 0.013, 0.013, (0.78, 0.8, 0.85), lift=0.2)
        c.line(u, v + 0.02, u, v + 0.0, 0.008, (0.7, 0.72, 0.78), 1.0)
    # rubber bone toy hanging on the right
    bu, bv = 0.30, 0.46
    soft_disc(c, bu + 0.02, bv - 0.02, 0.08, 0.20, BLACK, 0.25, 1.2)
    c.rect(bu, bv, 0.07, 0.30, scale(acc, 1.0), r=0.03, lift=0.25)
    for dy in (-0.16, 0.16):
        for dx in (-0.034, 0.034):
            c.ellipse(bu + dx, bv + dy, 0.040, 0.040, scale(acc, 1.0), lift=0.25)
    soft_disc(c, bu - 0.02, bv + 0.05, 0.012, 0.12, WHITE, 0.5, 1.0, add=True)
    c.ellipse(bu, bv + 0.20, 0.010, 0.010, (0.7, 0.72, 0.78), lift=0.3)
    # a tennis-ball pack hanging low
    for k in range(2):
        _ball(c, 0.00 + k * 0.10, 0.12, 0.045, (0.85, 0.92, 0.22), spec=0.5)


@sprop("care_pet_toys", aspect=3.2, fill=0.28)
def pet_toys(c, color):
    """Steel food bowl heaped with kibble, a tennis ball and an orange rubber bone."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.14, 0.5)
    # bowl
    steel = (0.78, 0.80, 0.84)
    soft_disc(c, -0.25, 0.01, 0.28, 0.05, BLACK, 0.5, 1.3)
    _lathe(c, -0.28, 0.015, [(0.12, 0.0), (0.16, 0.02), (0.205, 0.075), (0.225, 0.11)], steel, inner=scale(steel, 0.4), kind="metal")
    top = 0.125
    c.ellipse(-0.28, top + 0.01, 0.20, 0.20 * TILT * 0.9, (0.45, 0.26, 0.12), lift=0)
    for _ in range(34):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.17
        c.ellipse(-0.28 + math.cos(a) * rr, top + 0.025 + math.sin(a) * rr * TILT * 0.9 + rr * 0.15, rng.uniform(0.012, 0.018), rng.uniform(0.010, 0.014),
                  rng.choice(((0.58, 0.34, 0.16), (0.72, 0.46, 0.22), (0.45, 0.26, 0.12), (0.8, 0.55, 0.28))), lift=0.25)
    soft_disc(c, -0.40, 0.09, 0.015, 0.05, (1.0, 1.0, 1.0), 0.6, 1.0, add=True)
    # tennis ball
    _ball(c, 0.12, 0.065, 0.062, (0.85, 0.92, 0.20), spec=0.6)
    craft.arc(c, 0.12 - 0.04, 0.065, 0.045, 0.062, -70, 70, 0.006, (0.97, 0.97, 0.90), 0.9, steps=8)
    craft.arc(c, 0.12 + 0.04, 0.065, 0.045, 0.062, 110, 250, 0.006, (0.97, 0.97, 0.90), 0.9, steps=8)
    # rubber bone lying at an angle
    for dy, col in ((0.0, (0.95, 0.52, 0.10)),):
        bu, bv = 0.42, 0.045
        soft_disc(c, bu + 0.02, bv - 0.015, 0.20, 0.04, BLACK, 0.4, 1.3)
        c.rect(bu, bv + 0.01, 0.26, 0.045, col, r=0.02, lift=0.3, alpha=1.0)
        for dx in (-0.13, 0.13):
            for sy in (-0.020, 0.032):
                c.ellipse(bu + dx, bv + 0.012 + sy, 0.028, 0.028, col, lift=0.3)
        soft_disc(c, bu - 0.04, bv + 0.03, 0.08, 0.008, WHITE, 0.6, 1.0, add=True)
        c.text("PET", bu, bv + 0.012, 0.016, scale(col, 0.55), 0.2)


@niche("petshop", "Pet shop", subjects=("care_pet_foodbag",),
       strong=("pet shop", "pet store", "pet supplies", "dog food", "pet accessories", "pet food", "pet products", "pet care store", "aquarium shop",
               "pets shop", "petshop", "पेट शॉप", "पेट स्टोर", "पालतू जानवर", "कुत्ते का खाना", "पेट फूड"),
       weak=("pets", "dog", "cat", "puppy", "bird cage", "aquarium", "leash", "collar", "पालतू", "kutta"),
       avoid=("veterinary", "vet clinic"), accent="#f39c12", mood="light", group="retail")
def petshop(S):
    P = S.pal
    dark = _dark(S)
    gl = 1.7 if dark else 1.0
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        # shelves along the back wall stacked with colourful boxes, tins and bags
        box_cols = (P.accent, P.accent_light, (0.25, 0.55, 0.85), (0.90, 0.30, 0.30), (0.30, 0.65, 0.40), (0.95, 0.85, 0.40), P.accent_dark, (0.85, 0.85, 0.9))
        for row, v in enumerate((0.16, 0.34, 0.52)):
            S.rect(1.0, v + 0.01, 6.0, 0.014, scale(WOOD, 1.0 if not dark else 0.55), lift=0.0)
            u = -1.5
            while u < 3.8:
                w = S.rng.uniform(0.07, 0.14)
                h = S.rng.uniform(0.09, 0.15)
                col = box_cols[S.rng.randrange(len(box_cols))]
                if dark:
                    col = scale(col, 0.5)
                S.rect(u + w / 2, v - h / 2 + 0.004, w - 0.008, h, col, r=0.004 if row == 1 else 0.0, lift=0.08)
                S.rect(u + w / 2, v - h * 0.35, w - 0.02, h * 0.22, mix(col, WHITE, 0.55), lift=0.0, alpha=0.8)
                u += w + 0.004
            S.glow(1.0, v + 0.03, 1.8, (1.0, 0.95, 0.8), 0.12 * gl, 1.8)
        # hanging round pet sign and pendants
        S.line(0.34, 0.0, 0.34, 0.08, 0.004, (0.3, 0.3, 0.3), 0.8)
        S.circle(0.34, 0.15, 0.075, P.accent, lift=0.12)
        S.circle(0.34, 0.15, 0.058, mix(P.accent, WHITE, 0.55), lift=0.0)
        S.pendant(1.30, -0.1, 0.10, color=(1.0, 0.9, 0.65), shade_w=0.10)
        S.pendant(1.92, -0.1, 0.12, color=(1.0, 0.9, 0.65), shade_w=0.09)
        S.bokeh(6, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.95, 0.75), (1.0, 0.8, 0.5)], 0.012, 0.04, 0.25 * gl)
        S.floor(0.58, P.floor_top, P.floor_bot)
    # floor of cream and tan tiles in perspective, with a soft light pool
    c1 = mix((0.96, 0.92, 0.82), P.accent_light, 0.18) if not dark else scale(P.floor_top, 1.1)
    c2 = mix((0.86, 0.78, 0.62), P.accent, 0.12) if not dark else scale(P.floor_bot, 0.8)
    rows_, cols_, span, vh, uc = 7, 16, 7.0, -0.9, 1.05
    vs = [0.58 + (1.30 - 0.58) * (i / float(rows_)) ** 1.55 for i in range(rows_ + 1)]
    S.rect(1.0, 0.94, 8.0, 0.72, c2, lift=0.0)
    for r in range(rows_):
        for k in range(cols_):
            if (r + k) % 2:
                continue
            pts = []
            for v, ua in ((vs[r], k), (vs[r], k + 1), (vs[r + 1], k + 1), (vs[r + 1], k)):
                f = (v - vh) / (1.0 - vh)
                pts.append((uc + (ua / cols_ - 0.5) * span * f, v))
            if max(p[0] for p in pts) < -1.0 or min(p[0] for p in pts) > 3.2:
                continue
            S.poly(pts, c1, soft=0.6)
    S.rect(1.0, 0.58, 14.0, 0.010, scale(c2, 0.5), lift=0.0)
    S.rect(1.0, 0.598, 14.0, 0.018, scale(P.wall_bot, 0.85), lift=0.0)
    S.soft(1.1, 0.86, 1.0, 0.16, (1.0, 0.94, 0.78), 0.26 if not dark else 0.14, 1.4, add=True)
    # pegboard with collars and leashes on the wall behind
    S.put("care_pet_rack", 0.60, 0.62, 0.46, color=P, shadow=False, framed=False)
    S.put("care_pet_cage", 1.56, 0.86, 0.44, color=P, shadow_w=0.3)
    S.put("care_pet_aquarium", 1.15, 0.84, 0.32, shadow_w=0.5)
    S.put("care_pet_foodbag", 0.82, 0.98, 0.46, color=P, subject=True, shadow_w=0.35)
    S.put("care_pet_foodbag", 0.62, 0.93, 0.38, color=P, shadow_w=0.3)
    S.put("care_pet_toys", 1.28, 1.03, 0.12, shadow_w=0.45)
    S.focus("detail", 1.15, 0.64)
    if dark:                                    # practical light: warm spots over the aquarium and the bags
        S.soft(1.15, 0.80, 0.5, 0.2, (0.5, 0.95, 1.0), 0.26, 1.6, add=True)
        S.soft(0.74, 0.90, 0.35, 0.25, (1.0, 0.85, 0.55), 0.25, 1.6, add=True)
    with S.near():
        S.circle(0.40, 1.12, 0.07, (1.0, 0.9, 0.6), alpha=0.35, lift=0)
        S.soft(1.88, 1.10, 0.28, 0.1, BLACK, 0.45, 1.0)


# END
