"""Learning, leisure and hospitality niches: playschool, driving-school, music-academy, sports-academy, robotics-lab, hotel,
taxi, gaming-zone.

Props are prefixed ``learn_``. Big shapes use the scan-line fillers of auto_events (``_poly`` / ``_rr`` / ``_oval``) so the
scenes stay fast. Scene layout never depends on ``S.rng`` (the dry pass does not consume it): decor uses a local Random.
"""
import math
import random

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, gloss, soft_disc
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale
from .auto_events import (CARS, _car, _cyl_fn, _wheel, _hair, _hfill, _oval, _oval_pts, _poly, _rr, _rrpts, _scan, _sfill, _shair, _spoly)

CREAM = (1.0, 0.97, 0.88)
RED = (0.89, 0.22, 0.20)
BLUE = (0.20, 0.55, 0.90)
YEL = (0.98, 0.78, 0.15)
GRN = (0.25, 0.70, 0.35)
ORG = (0.95, 0.52, 0.14)
PUR = (0.60, 0.34, 0.80)
STEEL = (0.62, 0.65, 0.70)


# ====================================================================================== shared helpers
def _dk(P):
    return P.mood == "dark"


def _tn(P, col, k=0.4):
    """Natural colour dimmed in the dark mood."""
    return scale(col, k) if _dk(P) else col


def _box3(c, u, v, w, h, d, front, top=None, right=None, r=0.0, lift=0.07, tilt=(0.34, 0.30)):
    """Cuboid in raised 3/4 view, base-front centre at (u, v): lit top, front, shaded right side."""
    dx, dy = d * tilt[0], d * tilt[1]
    top = top or mix(front, WHITE, 0.28)
    right = right or scale(front, 0.66)
    x0, x1 = u - w / 2, u + w / 2
    _poly(c, [(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], right, scale(right, 0.88))
    _poly(c, [(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, scale(top, 0.94))
    _rr(c, x0, v, x1, v + h, scale(front, 1 + lift), scale(front, 1 - lift), r)


def _flat(u, v, pts, k=TILT):
    """Shape drawn on a floor (x, y local) squashed by the viewing tilt."""
    return [(u + x, v + y * k) for x, y in pts]


def _planks(S, v0, top, bot, spacing=0.20, vp=(1.05, -0.2), tone=0.05):
    """Floor with perspective boards: gradient + converging seams + a few tone bands (cheap)."""
    S.floor(v0, top, bot)
    if S.dry:
        return
    u0, u1 = S.visible_u()
    lo, hi = min(u0, u1) - 1.5, max(u0, u1) + 1.5
    vp_u, vp_v = vp
    rng = random.Random(5)
    k = (1.9 - vp_v) / (v0 - vp_v)
    n0, n1 = int((lo - vp_u) / spacing) - 2, int((hi - vp_u) / spacing) + 2
    for i in range(n0, n1):
        ua, ub = vp_u + i * spacing, vp_u + (i + 1) * spacing
        t = rng.uniform(-tone, tone)
        if t > 0.01:
            _spoly(S, [(vp_u + (ua - vp_u) * 1.0, v0), (vp_u + (ub - vp_u), v0), (vp_u + (ub - vp_u) * k, 1.9), (vp_u + (ua - vp_u) * k, 1.9)],
                   WHITE, None, t * 1.4)
        elif t < -0.01:
            _spoly(S, [(ua, v0), (ub, v0), (vp_u + (ub - vp_u) * k, 1.9), (vp_u + (ua - vp_u) * k, 1.9)], BLACK, None, -t * 1.6)
        _shair(S, ua, v0, vp_u + (ua - vp_u) * k, 1.9, scale(bot, 0.5), 0.35)


def _pool(S, u, v, a, b, col, alpha=0.3, power=1.4, add=True):
    """Wide light pool made of a few overlapping soft discs (one wide soft disc costs a full square of pixels, this is ~3x cheaper)."""
    n = max(1, int(round(a / max(0.05, b * 2.2))))
    if n == 1:
        S.soft(u, v, a, b, col, alpha, power, add=add)
        return
    for i in range(n):
        uu = u + (i - (n - 1) / 2.0) * (2.0 * a / n) * 0.78
        S.soft(uu, v, a / n * 1.45, b, col, alpha * 0.78, power, add=add)


def _sky(P):
    if _dk(P):
        return scale(P.wall_top, 0.8), mix(scale(P.wall_bot, 1.4), P.accent_dark, 0.35)
    return mix(P.wall_top, (0.55, 0.78, 0.97), 0.75), mix(P.wall_bot, (0.90, 0.96, 1.0), 0.7)


def _text(S, txt, u, v, h, col, weight=0.18):
    S.text(txt, u, v, h, col, weight)


def _cloud(S, u, v, s, col, alpha=0.85):
    for du, dv, r in ((-0.6, 0.1, 0.55), (0.0, -0.1, 0.75), (0.65, 0.05, 0.6), (0.2, 0.2, 0.5), (-0.2, 0.15, 0.5)):
        S.circle(u + du * s, v + dv * s * 0.6, r * s * 0.5, col, alpha=alpha, lift=0.0, soft=3.0)


# ====================================================================================== playschool
def _block(c, u, v, s, col, letter):
    _box3(c, u, v, s, s, s * 0.9, col, r=s * 0.06)
    pw = s * 0.74
    _rr(c, u - pw / 2, v + s * 0.13, u + pw / 2, v + s * 0.13 + pw, CREAM, mix(CREAM, col, 0.18), pw * 0.10)
    c.text(letter, u, v + s * 0.5, s * 0.46, scale(col, 0.85), 0.28)
    _poly(c, [(u - s / 2 + s * 0.02, v + s * 0.04), (u - s / 2 + s * 0.07, v + s * 0.04), (u - s / 2 + s * 0.07, v + s * 0.96),
              (u - s / 2 + s * 0.02, v + s * 0.96)], WHITE, None, 0.22)
    soft_disc(c, u + s * 0.3, v + s * 0.1, s * 0.4, s * 0.12, BLACK, 0.15, 1.2)


@sprop("learn_abc_blocks", aspect=1.10, fill=1.06)
def learn_abc_blocks(c, color):
    s = 0.30
    ao(c, 0.12, 0.0, 1.15, 0.20)
    for k, (u, ch, col) in enumerate(((-0.32, "A", RED), (0.0, "B", BLUE), (0.32, "C", YEL))):
        _block(c, u, 0.0, s, col, ch)
    for u, ch, col in ((-0.16, "1", GRN), (0.16, "2", ORG)):
        _block(c, u, 0.345, s, col, ch)
    _block(c, 0.0, 0.69, s, PUR, "D")
    _block(c, 0.70, -0.02, 0.19, BLUE, "Z")
    _poly(c, [(0.58, -0.02), (0.82, -0.02), (0.70, 0.15)], (0.95, 0.35, 0.40), scale((0.95, 0.35, 0.40), 0.7), 0.0)


def _teddy(c, u, v, k):
    br = (0.72, 0.48, 0.28)
    c.ellipse(u, v + 0.12 * k, 0.10 * k, 0.12 * k, br, lift=0.2)
    c.ellipse(u, v + 0.27 * k, 0.085 * k, 0.075 * k, mix(br, WHITE, 0.08), lift=0.2)
    for s in (-1, 1):
        c.ellipse(u + s * 0.07 * k, v + 0.33 * k, 0.03 * k, 0.03 * k, scale(br, 0.8), lift=0.1)
        c.ellipse(u + s * 0.10 * k, v + 0.04 * k, 0.035 * k, 0.04 * k, scale(br, 0.85), lift=0.1)
        c.ellipse(u + s * 0.03 * k, v + 0.285 * k, 0.008 * k, 0.010 * k, (0.1, 0.07, 0.05), lift=0)
    c.ellipse(u, v + 0.255 * k, 0.03 * k, 0.022 * k, (0.92, 0.80, 0.62), lift=0.1)
    c.ellipse(u, v + 0.265 * k, 0.011 * k, 0.008 * k, (0.1, 0.07, 0.05), lift=0)
    c.ellipse(u, v + 0.12 * k, 0.05 * k, 0.07 * k, (0.92, 0.80, 0.62), alpha=0.7, lift=0)


@sprop("learn_toy_shelf", aspect=1.34, fill=0.80)
def learn_toy_shelf(c, color):
    wood = color or (0.88, 0.70, 0.46)
    w, h, d = 1.0, 0.78, 0.30
    ao(c, 0.06, 0.0, 1.1, 0.10)
    _box3(c, 0.0, 0.0, w, h, d, wood, r=0.015)
    cw, ch = 0.285, 0.325
    col_u = (-0.325, 0.0, 0.325)
    rows = (0.04, 0.42)
    for ri, v0 in enumerate(rows):
        for ci, u in enumerate(col_u):
            _rr(c, u - cw / 2, v0, u + cw / 2, v0 + ch, scale(wood, 0.36), scale(wood, 0.62), 0.006)
            _poly(c, [(u - cw / 2, v0 + ch), (u + cw / 2, v0 + ch), (u + cw / 2 - 0.02, v0 + ch - 0.06), (u - cw / 2 + 0.02, v0 + ch - 0.06)], BLACK, None, 0.28, 0.0)
            _poly(c, [(u - cw / 2, v0), (u - cw / 2, v0 + ch), (u - cw / 2 + 0.025, v0 + ch - 0.02), (u - cw / 2 + 0.025, v0 + 0.02)], BLACK, None, 0.25)
            b = v0 + 0.012
            kind = ri * 3 + ci
            if kind == 0:
                _teddy(c, u, b, 1.0)
            elif kind == 1:
                _rr(c, u - 0.10, b, u + 0.10, b + 0.12, (0.55, 0.38, 0.22), (0.40, 0.27, 0.15), 0.02)
                for bu, bc in ((-0.06, RED), (0.0, YEL), (0.06, BLUE), (-0.02, GRN)):
                    c.ellipse(bu, b + 0.15, 0.045, 0.045, bc, lift=0.25)
                    gloss(c, bu - 0.015, b + 0.165, 0.012, 0.008, 0, 0.7)
            elif kind == 2:
                for i, bc in enumerate((RED, BLUE, GRN, ORG)):
                    _poly(c, [(u - 0.10 + i * 0.05, b), (u - 0.065 + i * 0.05, b), (u - 0.05 + i * 0.05, b + 0.25), (u - 0.085 + i * 0.05, b + 0.25)], bc, scale(bc, 0.7))
            elif kind == 3:
                _rr(c, u - 0.12, b + 0.03, u + 0.12, b + 0.10, (0.90, 0.2, 0.18), (0.62, 0.10, 0.10), 0.03)
                _rr(c, u - 0.06, b + 0.10, u + 0.07, b + 0.15, (0.75, 0.88, 0.95), (0.45, 0.6, 0.7), 0.02)
                for wu in (-0.07, 0.07):
                    c.ellipse(u + wu, b + 0.03, 0.035, 0.035, (0.1, 0.1, 0.12), lift=0.1)
                    c.ellipse(u + wu, b + 0.03, 0.014, 0.014, STEEL, lift=0.1)
            elif kind == 4:
                c.rect(u, b + 0.12, 0.014, 0.24, scale(wood, 0.8), lift=0)
                for i, rc in enumerate((RED, ORG, YEL, GRN, BLUE)):
                    c.ellipse(u, b + 0.02 + i * 0.035, 0.095 - i * 0.012, 0.03, rc, lift=0.2)
                c.ellipse(u, b + 0.215, 0.018, 0.018, PUR, lift=0.2)
            else:
                _rr(c, u - 0.085, b, u + 0.085, b + 0.14, (0.35, 0.60, 0.90), (0.20, 0.38, 0.65), 0.012)
                _rr(c, u - 0.085, b + 0.12, u + 0.085, b + 0.16, (0.95, 0.9, 0.82), (0.8, 0.74, 0.66), 0.01)
                _poly(c, [(u - 0.06, b + 0.16), (u + 0.06, b + 0.16), (u, b + 0.25)], YEL, scale(YEL, 0.8))
    for u in (-0.16, 0.16):                                                            # dividers read as bevelled wood
        c.line(u, 0.02, u, h - 0.02, 0.004, mix(wood, WHITE, 0.5), 0.35)
    c.line(-0.48, 0.40, 0.48, 0.40, 0.006, mix(wood, WHITE, 0.55), 0.4)
    c.line(-0.48, h - 0.01, 0.48, h - 0.01, 0.01, mix(wood, WHITE, 0.6), 0.55)
    gloss(c, -0.32, 0.72, 0.18, 0.04, 0, 0.18)


def _chair(c, u, v, col, wood):
    for lu in (-0.11, 0.11):
        _rr(c, u + lu - 0.014, v, u + lu + 0.014, v + 0.20, scale(wood, 1.0), scale(wood, 0.6), 0.004)
    _rr(c, u - 0.14, v + 0.20, u + 0.14, v + 0.46, scale(col, 1.05), scale(col, 0.78), 0.03)
    _rr(c, u - 0.10, v + 0.25, u + 0.10, v + 0.43, mix(col, WHITE, 0.15), col, 0.02, 0.55)
    _box3(c, u, v + 0.18, 0.30, 0.035, 0.24, col, r=0.008)
    soft_disc(c, u - 0.04, v + 0.38, 0.06, 0.04, WHITE, 0.4, 1.2, 0, True)


@sprop("learn_kid_table", aspect=2.9, fill=0.66)
def learn_kid_table(c, color):
    rng = c.rng
    wood = (0.85, 0.66, 0.42)
    ao(c, 0.0, 0.0, 1.6, 0.26)
    _chair(c, -0.66, 0.04, BLUE, wood)
    _chair(c, 0.68, 0.04, RED, wood)
    top = color or (0.99, 0.82, 0.30)
    for lu, lv in ((-0.34, 0.0), (0.34, 0.0), (-0.22, 0.14), (0.22, 0.14)):
        _rr(c, lu - 0.022, lv, lu + 0.022, lv + 0.38, wood, scale(wood, 0.55), 0.006)
    c.ellipse(0.0, 0.37, 0.55, 0.55 * TILT, scale(top, 0.62), lift=0)
    c.ellipse(0.0, 0.405, 0.55, 0.55 * TILT, scale(top, 0.82), lift=0.04)
    c.ellipse(0.0, 0.425, 0.55, 0.55 * TILT, top, lift=0.10)
    soft_disc(c, -0.15, 0.46, 0.40, 0.10, WHITE, 0.3, 1.1, 0, True)
    # paper with a crayon drawing, loose crayons, a pencil cup
    _poly(c, [(-0.26, 0.40), (0.04, 0.40), (0.10, 0.50), (-0.20, 0.50)], (0.99, 0.99, 0.97), (0.90, 0.90, 0.88))
    c.ellipse(-0.14, 0.455, 0.035, 0.022, YEL, lift=0.2)
    for a in range(0, 360, 45):
        c.line(-0.14 + math.cos(math.radians(a)) * 0.045, 0.455 + math.sin(math.radians(a)) * 0.028, -0.14 + math.cos(math.radians(a)) * 0.065,
               0.455 + math.sin(math.radians(a)) * 0.04, 0.005, ORG, 0.9)
    c.line(-0.24, 0.425, -0.06, 0.44, 0.008, GRN, 0.9)
    c.line(-0.06, 0.44, 0.0, 0.425, 0.008, BLUE, 0.9)
    for i, cc in enumerate((RED, GRN, BLUE)):
        c.line(0.14 + i * 0.03, 0.40 - i * 0.012, 0.28 + i * 0.03, 0.43 - i * 0.012, 0.016, cc)
        c.line(0.26 + i * 0.03, 0.428 - i * 0.012, 0.28 + i * 0.03, 0.43 - i * 0.012, 0.016, scale(cc, 0.6))
    _hfill(c, 0.34, 0.44, 0.42, 0.53, _cyl_fn((0.95, 0.4, 0.45), (0.55, 0.15, 0.2), 0.3))
    for i, cc in enumerate((YEL, RED, GRN, BLUE)):
        c.line(0.355 + i * 0.019, 0.52, 0.34 + i * 0.03, 0.62, 0.014, cc)
    _block(c, -0.40, 0.43, 0.09, GRN, "A")


@sprop("learn_play_rug", aspect=2.55, fill=0.64)
def learn_play_rug(c, color):
    """Woven play rug: a segmented border, a pastel field, printed shapes that sit INSIDE the pile (shadowed edges + pile strands)."""
    rng = c.rng
    R = 0.80
    cy = 0.32
    n = 28
    soft_pastel = lambda col, t=0.14: mix(col, CREAM, t)             # noqa: E731
    _oval(c, 0.0, cy - 0.03, R * 1.03, R * TILT * 1.04, (0.20, 0.15, 0.10), None, 0.50)
    cols = [RED, ORG, YEL, GRN, BLUE, PUR, (0.92, 0.38, 0.60), (0.25, 0.75, 0.80)]
    _oval(c, 0.0, cy - 0.012, R * 1.005, R * 1.005 * TILT, (0.30, 0.22, 0.16), None)               # rug thickness
    for k in range(n):
        a0, a1 = 360.0 * k / n, 360.0 * (k + 1) / n + 1.5
        pa = [(math.cos(math.radians(a0 + (a1 - a0) * t / 3)) * R, math.sin(math.radians(a0 + (a1 - a0) * t / 3)) * R * TILT) for t in range(4)]
        pb = [(math.cos(math.radians(a1 - (a1 - a0) * t / 3)) * R * 0.86, math.sin(math.radians(a1 - (a1 - a0) * t / 3)) * R * 0.86 * TILT) for t in range(4)]
        col = soft_pastel(cols[k % len(cols)])
        _poly(c, [(x, cy + y) for x, y in pa + pb], col, scale(col, 0.82))
    _oval(c, 0.0, cy, R * 0.865, R * 0.865 * TILT, (0.99, 0.97, 0.92), (0.92, 0.88, 0.80))                 # keyline
    sky = (0.78, 0.90, 0.96)
    _oval(c, 0.0, cy, R * 0.83, R * 0.83 * TILT, sky, scale(sky, 0.90))
    _oval(c, 0.0, cy + 0.01, R * 0.58, R * 0.58 * TILT, (0.99, 0.95, 0.84), (0.96, 0.90, 0.78), 0.55)       # warm island in the middle
    for a, kind, col in ((200, "circle", RED), (265, "square", BLUE), (330, "tri", GRN), (35, "star", YEL), (100, "circle", PUR), (150, "square", ORG)):
        ar = math.radians(a)
        pu, pv = math.cos(ar) * 0.58, cy + math.sin(ar) * 0.58 * TILT
        s = 0.105
        col = soft_pastel(col, 0.08)
        if kind == "circle":
            pts = _oval_pts(0.0, 0.0, s, s, 18)[:-1]
        elif kind == "square":
            pts = [(-s, -s), (s, -s), (s, s), (-s, s)]
        elif kind == "tri":
            pts = [(-s * 1.1, -s), (s * 1.1, -s), (0, s * 1.2)]
        else:
            pts = []
            for i in range(10):
                rr_ = s * 1.25 if i % 2 == 0 else s * 0.55
                pts.append((math.cos(math.radians(90 + 36 * i)) * rr_, math.sin(math.radians(90 + 36 * i)) * rr_))
        _poly(c, _flat(pu, pv - 0.012, pts), BLACK, None, 0.22)                                   # edge shadow: the shape is woven into the pile
        _poly(c, _flat(pu, pv, pts), mix(col, WHITE, 0.10), scale(col, 0.82))
        _poly(c, _flat(pu, pv + 0.004, [(x * 0.62, y * 0.62) for x, y in pts]), WHITE, None, 0.12)
    for k in range(44):                                                                # pile strands over everything
        a = rng.uniform(0, 6.28)
        r = math.sqrt(rng.random()) * R * 0.97
        u0, v0 = math.cos(a) * r, cy + math.sin(a) * r * TILT
        ln = rng.uniform(0.02, 0.05)
        ang = rng.uniform(0.2, 2.9)
        c.line(u0, v0, u0 + math.cos(ang) * ln, v0 + math.sin(ang) * ln * TILT, 0.004, WHITE if k % 2 else BLACK, 0.20 if k % 2 else 0.13)
    soft_disc(c, -0.3, cy + 0.12, 0.7, 0.14, WHITE, 0.20, 1.2, 0, True)
    soft_disc(c, 0.35, cy - 0.08, 0.7, 0.12, BLACK, 0.12, 1.3)


@sprop("learn_toy_train", aspect=2.2, fill=0.55)
def learn_toy_train(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.10)
    for i, (u, col) in enumerate(((-0.62, RED), (0.0, BLUE), (0.62, GRN))):
        w = 0.50
        _box3(c, u, 0.08, w, 0.28, 0.2, col, r=0.03)
        for k in (-1, 1):
            c.ellipse(u + k * 0.15, 0.08, 0.075, 0.075, (0.25, 0.18, 0.12), lift=0.1)
            c.ellipse(u + k * 0.15, 0.08, 0.03, 0.03, (0.9, 0.85, 0.7), lift=0.1)
        c.line(u + w / 2, 0.18, u + 0.62 - w / 2, 0.18, 0.02, (0.45, 0.3, 0.2))
    c.ellipse(0.62, 0.54, 0.05, 0.05, YEL, lift=0.2)
    _rr(c, 0.52, 0.36, 0.72, 0.52, (0.95, 0.7, 0.15), (0.7, 0.45, 0.08), 0.02)


@sprop("learn_ball", aspect=1.0, fill=0.5)
def learn_ball(c, color):
    """Soft play ball with colour panels."""
    r = 0.25
    ao(c, 0.02, 0.0, 0.6, 0.10)
    cy = r + 0.01
    c.ellipse(0.0, cy, r, r, scale(RED, 0.55), lift=0)
    c.ellipse(-r * 0.04, cy + r * 0.05, r * 0.95, r * 0.95, RED, lift=0.2)
    craft.arc(c, 0.0, cy + r * 0.05, r * 0.90, r * 0.30, 190, 350, r * 0.26, WHITE, 1.0, steps=10, angle=0)
    craft.arc(c, 0.0, cy + r * 0.05, r * 0.82, r * 0.78, 40, 140, r * 0.20, BLUE, 1.0, steps=8, angle=0)
    soft_disc(c, r * 0.30, cy - r * 0.32, r * 0.70, r * 0.62, BLACK, 0.36, 1.3)
    gloss(c, -r * 0.34, cy + r * 0.38, r * 0.30, r * 0.17, 28, 0.7)


def _drawing(S, u, v, w, h, kind, tilt=0.0):
    S.shadow(u + 0.01, v + h / 2, w * 0.9, 0.02, 0.18)
    S.rect(u, v, w, h, (0.99, 0.98, 0.94), lift=0.03)
    x0, y0 = u - w / 2, v - h / 2
    if kind == 0:                                                       # sun over a house
        S.circle(x0 + w * 0.75, y0 + h * 0.25, h * 0.14, YEL, lift=0.0)
        for a in range(0, 360, 45):
            S.line(x0 + w * 0.75 + math.cos(math.radians(a)) * h * 0.18, y0 + h * 0.25 + math.sin(math.radians(a)) * h * 0.18,
                   x0 + w * 0.75 + math.cos(math.radians(a)) * h * 0.27, y0 + h * 0.25 + math.sin(math.radians(a)) * h * 0.27, 0.004, ORG)
        S.rect(x0 + w * 0.35, y0 + h * 0.70, w * 0.38, h * 0.36, RED, lift=0.0)
        S.poly([(x0 + w * 0.12, y0 + h * 0.52), (x0 + w * 0.58, y0 + h * 0.52), (x0 + w * 0.35, y0 + h * 0.28)], BLUE)
        S.rect(x0 + w * 0.35, y0 + h * 0.78, w * 0.09, h * 0.20, YEL, lift=0.0)
    elif kind == 1:                                                     # rainbow
        for i, col in enumerate((RED, ORG, YEL, GRN, BLUE)):
            r = h * (0.42 - i * 0.055)
            for a in range(0, 180, 20):
                a0, a1 = math.radians(a), math.radians(a + 22)
                S.line(u + math.cos(a0) * r * 0.9, y0 + h * 0.78 - math.sin(a0) * r, u + math.cos(a1) * r * 0.9, y0 + h * 0.78 - math.sin(a1) * r, 0.007, col)
        S.circle(x0 + w * 0.15, y0 + h * 0.82, h * 0.07, (0.8, 0.88, 0.97), lift=0.0)
    else:                                                               # tree and flower
        S.rect(x0 + w * 0.35, y0 + h * 0.70, w * 0.07, h * 0.40, (0.55, 0.36, 0.2), lift=0.0)
        S.circle(x0 + w * 0.35, y0 + h * 0.36, h * 0.22, GRN, lift=0.0)
        S.line(x0 + w * 0.75, y0 + h * 0.9, x0 + w * 0.75, y0 + h * 0.55, 0.004, GRN)
        for a in range(0, 360, 72):
            S.circle(x0 + w * 0.75 + math.cos(math.radians(a)) * h * 0.08, y0 + h * 0.48 + math.sin(math.radians(a)) * h * 0.08, h * 0.05, (0.95, 0.4, 0.6), lift=0.0)
        S.circle(x0 + w * 0.75, y0 + h * 0.48, h * 0.04, YEL, lift=0.0)
    S.rect(x0 + w * 0.5, y0, w * 0.16, h * 0.07, (0.95, 0.9, 0.6), alpha=0.8, lift=0.0)            # tape


def _rainbow(S, u, v, r0, bw, dk, alpha=0.92):
    """Painted pastel rainbow on the wall (arcs built from capsules; drawn in the blurred far layer)."""
    cols = [RED, ORG, YEL, GRN, BLUE, PUR]
    for i, col in enumerate(cols):
        col = mix(col, WHITE, 0.45)
        col = scale(col, 0.45) if dk else col
        r = r0 - i * bw
        pts = [(u + math.cos(math.radians(a)) * r, v - math.sin(math.radians(a)) * r) for a in range(-4, 185, 8)]
        for p, q in zip(pts, pts[1:]):
            S.line(p[0], p[1], q[0], q[1], bw * 1.08, col, alpha)


@niche("playschool", "Play school and daycare", subjects=("learn_abc_blocks",),
       strong=("play school", "playschool", "preschool", "pre school", "daycare", "day care", "nursery school", "kindergarten", "creche", "play group",
               "playgroup", "plesschool", "प्लेस्कूल", "प्ले स्कूल", "नर्सरी", "बालवाड़ी", "किंडरगार्टन", "क्रेच"),
       weak=("toddler", "kids", "children", "nursery", "alphabet", "crayon", "play", "बच्चे"),
       accent="#fbc02d", mood="light", group="education",
       avoid=("college", "university", "coaching", "tuition", "gym", "restaurant"))
def playschool(S):
    P = S.pal
    dk = _dk(P)
    band = mix(P.wall_bot, P.accent_light, 0.45)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.50, 14.0, 0.20, band, lift=0.0)
        S.rect(1.0, 0.402, 14.0, 0.014, mix(P.accent, WHITE, 0.4), lift=0.0)
        sky_t = (0.10, 0.12, 0.24) if dk else (0.62, 0.82, 0.97)
        sky_b = (0.20, 0.22, 0.38) if dk else (0.92, 0.97, 1.0)
        S.window(0.30, 0.24, 0.34, 0.34, sky_t, sky_b, frame=mix(P.paper, WHITE, 0.5))
        S.window(1.98, 0.24, 0.30, 0.34, sky_t, sky_b, frame=mix(P.paper, WHITE, 0.5))
        if not dk:
            S.light_shaft(0.18, 0.40, 0.42, 0.40, 0.90, 1.1, 0.40, 1.1, P.light, 0.08)
        # painted rainbow and cloud mural behind the play area
        _rainbow(S, 1.04, 0.60, 0.46, 0.048, dk)
        _cloud(S, 0.58, 0.55, 0.20, scale(WHITE, 0.45) if dk else WHITE, 0.95)
        _cloud(S, 1.52, 0.55, 0.24, scale(WHITE, 0.45) if dk else WHITE, 0.95)
        for k in range(14):                                                    # bunting
            u = -0.2 + k * 0.17
            sag = math.sin((u + 0.2) / 2.4 * math.pi) * 0.07
            S.poly([(u, 0.06 + sag), (u + 0.12, 0.06 + sag), (u + 0.06, 0.15 + sag)], [RED, YEL, BLUE, GRN, ORG][k % 5] if not dk else scale([RED, YEL, BLUE, GRN, ORG][k % 5], 0.5))
        S.glow(1.05, 0.38, 1.2, P.light, 0.30 if not dk else 0.16)
        S.bokeh(8, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.9, 0.6), (1.0, 0.7, 0.8), (0.7, 0.9, 1.0)], 0.01, 0.04, 0.22)
        if dk:
            for u in (0.55, 1.05, 1.55):
                S.pendant(u, -0.05, 0.14, (1.0, 0.85, 0.55))
    _planks(S, 0.60, mix(P.floor_top, P.accent_light, 0.2), mix(P.floor_bot, P.accent_light, 0.1), 0.24)
    _pool(S, 1.05, 0.82, 1.1, 0.20, P.light, 0.30 if not dk else 0.18)
    if not dk:                                                                 # sunbeams from the two windows slanting across the floor
        _spoly(S, [(0.12, 0.61), (0.46, 0.61), (1.10, 1.40), (0.50, 1.40)], P.light, P.light, 0.16, 0.03)
        _spoly(S, [(1.85, 0.61), (2.10, 0.61), (1.62, 1.40), (1.14, 1.40)], P.light, P.light, 0.12, 0.03)
    S.rect(1.0, 0.603, 14.0, 0.014, scale(P.wall_bot, 0.55), lift=0.0)
    # wall: crayon drawings
    _drawing(S, 0.40, 0.31, 0.20, 0.17, 0)
    _drawing(S, 1.74, 0.30, 0.19, 0.17, 2)
    _drawing(S, 1.58, 0.17, 0.15, 0.13, 1)
    for i, ch in enumerate("ABCDEFG"):
        S.rect(1.05 + (i - 3) * 0.13, 0.082, 0.11, 0.085, [RED, YEL, BLUE, GRN, ORG, PUR, RED][i], r=0.012, lift=0.05)
        S.text(ch, 1.05 + (i - 3) * 0.13, 0.082, 0.05, WHITE, 0.22)
    S.put("learn_toy_shelf", 0.80, 0.80, 0.34, color=mix((0.88, 0.70, 0.46), P.accent_light, 0.18), shadow_w=0.5, subject=False)
    S.put("learn_kid_table", 1.31, 0.86, 0.15, color=mix((0.99, 0.82, 0.30), P.accent, 0.2))
    S.put("learn_play_rug", 1.02, 0.99, 0.30, shadow=False)
    S.put("learn_abc_blocks", 1.02, 0.95, 0.50, subject=True, shadow_w=1.0)
    S.put("learn_toy_train", 1.35, 1.045, 0.115, shadow_w=0.3)
    S.put("learn_ball", 0.66, 1.06, 0.09, shadow_w=0.12)
    S.focus("detail", 1.02, 0.78)
    with S.near(blur=18):
        S.soft(1.0, 1.0, 0.6, 0.10, P.light, 0.12, 1.2, add=True)
        for bu, bv, rr_, col in ((1.62, 1.04, 0.075, mix(RED, P.accent, 0.1)), (1.76, 1.10, 0.058, mix(BLUE, P.accent, 0.1))):        # out-of-focus balloons
            S.line(bu, bv + rr_ * 0.8, bu - 0.03, bv + 0.34, 0.004, scale(col, 0.7), 0.8)
            S.ellipse(bu, bv, rr_ * 0.84, rr_, col, lift=0.18)
            S.poly([(bu - 0.012, bv + rr_ * 0.95), (bu + 0.012, bv + rr_ * 0.95), (bu, bv + rr_ * 1.2)], scale(col, 0.8))
            S.soft(bu - rr_ * 0.3, bv - rr_ * 0.35, rr_ * 0.28, rr_ * 0.2, WHITE, 0.5, 1.2, add=True)


# ====================================================================================== driving school
_HK = 0.88                                                  # horizontal squeeze: a hatchback is short for its height
_HV = 0.84                                                  # vertical squeeze above the sills: low roof, not a crossover


def _V(v):
    return 0.17 + (v - 0.17) * _HV


def _hk(pts):
    return [(u * _HK, _V(v)) for u, v in pts]


CARS["learn_hatch"] = dict(
    # compact 5-door hatchback: short bonnet, roof peaking over the driver and falling in one line to a short, blunt tail
    prof=_hk([(-1.24, 0.20), (-1.28, 0.34), (-1.27, 0.52), (-1.24, 0.64), (-1.18, 0.74), (-1.06, 0.83), (-0.84, 0.90), (-0.50, 0.935), (-0.10, 0.94),
              (0.22, 0.91), (0.46, 0.80), (0.60, 0.69), (0.98, 0.645), (1.18, 0.60), (1.30, 0.52), (1.32, 0.40), (1.29, 0.20), (0.9, 0.17), (-0.9, 0.17)]),
    glass=[_hk([(-0.08, 0.705), (-0.08, 0.905), (-0.45, 0.91), (-0.82, 0.87), (-1.0, 0.79), (-1.08, 0.705)]),
           _hk([(0.0, 0.705), (0.0, 0.905), (0.15, 0.905), (0.43, 0.785), (0.52, 0.705)])],
    wheels=[(-0.80 * _HK, 0.225), (0.84 * _HK, 0.225)], belt=_V(0.67), roof=_V(0.94), door=[-0.60 * _HK, 0.02 * _HK, 0.50 * _HK],
    head=(1.27 * _HK, _V(0.46)), tail=(-1.27 * _HK, _V(0.50)), mirror=(0.42 * _HK, _V(0.77)), sill=0.17)


def _lplate(c, u, v, s):
    _rr(c, u - s, v - s, u + s, v + s, (1.0, 1.0, 1.0), (0.88, 0.88, 0.9), s * 0.12)
    _rr(c, u - s * 0.40, v - s * 0.62, u - s * 0.05, v + s * 0.62, (0.85, 0.08, 0.10), (0.70, 0.04, 0.06), 0.0)
    _rr(c, u - s * 0.40, v - s * 0.62, u + s * 0.48, v - s * 0.28, (0.85, 0.08, 0.10), (0.70, 0.04, 0.06), 0.0)


@sprop("learn_hatchback", aspect=2.30, fill=1.0)
def learn_hatchback(c, color):
    acc = color or (0.26, 0.64, 0.28)
    body = (0.96, 0.97, 0.98)
    H, V = _HK, _V
    _car(c, "learn_hatch", body, caliper=acc)
    k = CARS["learn_hatch"]
    bl = k["belt"]
    # white lower body: cover the shared renderer's dark gradient and SUV-style cladding, then redraw door cuts, arches and wheels
    _poly(c, [(-1.19 * H, 0.168), (1.21 * H, 0.168), (1.28 * H, 0.30), (1.25 * H, 0.45), (1.10 * H, bl - 0.005), (-1.19 * H, bl - 0.005), (-1.25 * H, 0.45),
               (-1.26 * H, 0.30)], mix(body, WHITE, 0.2), scale(body, 0.80))
    _poly(c, [(-1.19 * H, 0.168), (1.21 * H, 0.168), (1.21 * H, 0.20), (-1.19 * H, 0.20)], BLACK, None, 0.22)
    _poly(c, [(-1.15 * H, bl - 0.03), (1.15 * H, bl - 0.03), (1.15 * H, bl - 0.012), (-1.15 * H, bl - 0.012)], WHITE, None, 0.55)     # shoulder highlight
    for du in k["door"]:
        c.line(du, 0.23, du + 0.01, bl - 0.01, 0.006, scale(body, 0.50), 0.8)
        c.line(du + 0.012, 0.23, du + 0.02, bl - 0.01, 0.003, WHITE, 0.6)
    for du in k["door"][1:]:
        _rr(c, du - 0.20, bl - 0.075, du - 0.07, bl - 0.052, mix(body, WHITE, 0.2), scale(body, 0.6), 0.012)
    for wu, wr in k["wheels"]:
        ar = wr + 0.04
        pts = [(wu + ar * math.cos(math.radians(a_)), wr + ar * math.sin(math.radians(a_))) for a_ in range(0, 181, 15)]
        _poly(c, [(wu - ar, 0.15)] + pts + [(wu + ar, 0.15)], (0.04, 0.04, 0.05))
        _wheel(c, wu, wr, wr, caliper=acc)
    # accent stripe with the school name along the doors
    _poly(c, [(-1.14 * H, 0.33), (1.12 * H, 0.36), (1.14 * H, 0.435), (-1.16 * H, 0.405)], acc, scale(acc, 0.75), 0.94)
    c.line(-1.05 * H, 0.445, 1.02 * H, 0.456, 0.006, WHITE, 0.6)
    c.text("DRIVING SCHOOL", 0.02, 0.385, 0.052, WHITE, 0.22)
    # hatch details: roof spoiler, wiper, hatch shut-line, number plate
    _poly(c, [(-1.20 * H, V(0.755)), (-1.10 * H, V(0.84)), (-1.04 * H, V(0.83)), (-1.15 * H, V(0.74))], (0.10, 0.10, 0.12), (0.04, 0.04, 0.05))
    c.line(-1.00 * H, V(0.76), -0.88 * H, V(0.775), 0.006, (0.05, 0.05, 0.06), 0.9)
    c.line(-1.205 * H, V(0.70), -1.27 * H, 0.38, 0.004, scale(body, 0.45), 0.7)
    _rr(c, -1.285 * H, 0.34, -1.235 * H, 0.40, (0.97, 0.97, 0.98), (0.85, 0.85, 0.88), 0.01)
    # roof sign carrier with the L plate (low profile, sits on the flat of the roof)
    rv = k["roof"]
    for fu in (-0.44 * H, -0.14 * H):
        _rr(c, fu - 0.02, rv - 0.012, fu + 0.02, rv + 0.025, (0.2, 0.2, 0.22), (0.1, 0.1, 0.12), 0.0)
    _rr(c, -0.54 * H, rv + 0.02, 0.0, rv + 0.135, (1.0, 1.0, 1.0), (0.82, 0.84, 0.88), 0.03)
    _rr(c, -0.54 * H, rv + 0.02, 0.0, rv + 0.037, (0.7, 0.72, 0.76), (0.55, 0.57, 0.6), 0.0)
    _rr(c, -0.30 * H, rv + 0.05, -0.255 * H, rv + 0.122, (0.85, 0.08, 0.10), (0.7, 0.04, 0.06), 0.0)
    _rr(c, -0.30 * H, rv + 0.05, -0.15 * H, rv + 0.069, (0.85, 0.08, 0.10), (0.7, 0.04, 0.06), 0.0)
    c.line(-0.52 * H, rv + 0.125, -0.02 * H, rv + 0.125, 0.006, WHITE, 0.7)
    _lplate(c, 1.26 * H, 0.28, 0.046)
    _lplate(c, -1.255 * H, 0.28, 0.042)
    c.glow(-0.22, rv + 0.05, 0.40, (1.0, 1.0, 1.0), 0.10)


def _pole(c, h, w=0.022):
    _hfill(c, -w, 0.0, w, h, _cyl_fn((0.80, 0.82, 0.86), (0.35, 0.37, 0.42), 0.4), strips=6)


def _signface(c, pts, col, rim=(1.0, 1.0, 1.0)):
    _poly(c, pts, scale(rim, 0.95), scale(rim, 0.78))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    inner = [(cx + (x - cx) * 0.88, cy + (y - cy) * 0.88) for x, y in pts]
    _poly(c, inner, mix(col, WHITE, 0.14), scale(col, 0.82))
    return cx, cy


@sprop("learn_sign_stop", aspect=0.62, fill=1.0)
def learn_sign_stop(c, color):
    ao(c, 0.0, 0.0, 0.26, 0.05)
    _pole(c, 0.62)
    pts = [(math.cos(math.radians(22.5 + 45 * k)) * 0.30, 0.74 + math.sin(math.radians(22.5 + 45 * k)) * 0.30) for k in range(8)]
    cx, cy = _signface(c, pts, (0.85, 0.10, 0.12))
    c.text("STOP", cx, cy, 0.10, WHITE, 0.30)
    gloss(c, -0.1, 0.9, 0.1, 0.05, 20, 0.3)


@sprop("learn_sign_speed", aspect=0.62, fill=1.0)
def learn_sign_speed(c, color):
    ao(c, 0.0, 0.0, 0.26, 0.05)
    _pole(c, 0.62)
    c.ellipse(0.0, 0.74, 0.30, 0.30, (0.95, 0.95, 0.96), lift=0.12)
    c.ellipse(0.0, 0.74, 0.27, 0.27, (0.86, 0.10, 0.12), lift=0.1)
    c.ellipse(0.0, 0.74, 0.19, 0.19, (0.98, 0.98, 0.98), lift=0.06)
    c.text("40", 0.0, 0.74, 0.17, (0.1, 0.1, 0.12), 0.30)
    gloss(c, -0.1, 0.9, 0.1, 0.05, 20, 0.3)


@sprop("learn_sign_warn", aspect=0.62, fill=1.0)
def learn_sign_warn(c, color):
    ao(c, 0.0, 0.0, 0.26, 0.05)
    _pole(c, 0.55)
    pts = [(-0.34, 0.60), (0.34, 0.60), (0.0, 1.0)]
    _poly(c, pts, (0.97, 0.97, 0.98), (0.82, 0.82, 0.85))
    _poly(c, [(-0.29, 0.635), (0.29, 0.635), (0.0, 0.95)], (0.88, 0.12, 0.14), (0.70, 0.06, 0.08))
    _poly(c, [(-0.23, 0.655), (0.23, 0.655), (0.0, 0.90)], (0.99, 0.99, 0.99), (0.93, 0.93, 0.95))
    c.text("!", 0.0, 0.74, 0.13, (0.1, 0.1, 0.12), 0.36)
    gloss(c, -0.08, 0.80, 0.08, 0.04, 20, 0.25)


@sprop("learn_sign_park", aspect=0.62, fill=1.0)
def learn_sign_park(c, color):
    ao(c, 0.0, 0.0, 0.26, 0.05)
    _pole(c, 0.62)
    _rr(c, -0.28, 0.46, 0.28, 1.02, (0.97, 0.97, 0.98), (0.82, 0.83, 0.86), 0.05)
    _rr(c, -0.245, 0.495, 0.245, 0.985, (0.15, 0.38, 0.80), (0.08, 0.24, 0.62), 0.035)
    c.text("P", 0.0, 0.74, 0.28, WHITE, 0.36)
    gloss(c, -0.1, 0.92, 0.1, 0.05, 20, 0.28)


@sprop("learn_cone", aspect=0.62, fill=1.0)
def learn_cone(c, color):
    org = color or (0.98, 0.45, 0.10)
    ao(c, 0.04, 0.0, 0.60, 0.10)
    _box3(c, 0.0, 0.0, 0.52, 0.06, 0.5, (0.18, 0.18, 0.20), r=0.01)

    def hw(v):
        return 0.20 - 0.13 * (v - 0.06) / 0.92
    _poly(c, [(-hw(0.06), 0.06), (hw(0.06), 0.06), (hw(0.98), 0.98), (-hw(0.98), 0.98)], mix(org, WHITE, 0.08), scale(org, 0.78))
    _poly(c, [(hw(0.06) * 0.2, 0.06), (hw(0.06), 0.06), (hw(0.98), 0.98), (hw(0.98) * 0.2, 0.98)], scale(org, 0.5), None, 0.45)
    _poly(c, [(-hw(0.06) * 0.78, 0.06), (-hw(0.06) * 0.42, 0.06), (-hw(0.98) * 0.42, 0.98), (-hw(0.98) * 0.78, 0.98)], WHITE, None, 0.22)
    for v0, v1 in ((0.52, 0.66), (0.28, 0.38)):
        _poly(c, [(-hw(v0), v0), (hw(v0), v0), (hw(v1), v1), (-hw(v1), v1)], (0.97, 0.97, 0.97), (0.84, 0.84, 0.86))
        _poly(c, [(hw(v0) * 0.2, v0), (hw(v0), v0), (hw(v1), v1), (hw(v1) * 0.2, v1)], BLACK, None, 0.2)
    c.ellipse(0.0, 0.98, 0.065, 0.025, scale(org, 0.7), lift=0.1)
    gloss(c, -0.05, 0.75, 0.02, 0.15, 6, 0.4)


def _dial(c, u, v, r, needle, glow_col):
    c.ellipse(u, v, r * 1.12, r * 1.12, (0.05, 0.05, 0.06), lift=0)
    c.ellipse(u, v, r, r, (0.10, 0.12, 0.15), lift=0.15)
    for k in range(9):
        a_ = math.radians(215 - k * 32)
        c.line(u + math.cos(a_) * r * 0.78, v + math.sin(a_) * r * 0.78, u + math.cos(a_) * r * 0.92, v + math.sin(a_) * r * 0.92, 0.006, (0.85, 0.88, 0.92), 0.85)
    c.line(u, v, u + math.cos(math.radians(needle)) * r * 0.78, v + math.sin(math.radians(needle)) * r * 0.78, 0.008, glow_col)
    c.ellipse(u, v, r * 0.14, r * 0.14, (0.7, 0.72, 0.78), lift=0.3)
    gloss(c, u - r * 0.3, v + r * 0.35, r * 0.5, r * 0.22, 20, 0.35)


@sprop("learn_steering_wheel", aspect=1.00, fill=1.0)
def learn_steering_wheel(c, color):
    """Training rig: base plate with three pedals, a dashboard panel with two dials, the column, the wheel and a gear lever."""
    acc = color or (0.26, 0.64, 0.28)
    ao(c, 0.0, 0.0, 0.95, 0.12)
    _box3(c, 0.0, 0.0, 0.88, 0.055, 0.46, (0.20, 0.21, 0.24), top=(0.30, 0.31, 0.35), r=0.01, tilt=(0.30, 0.34))
    for k, (pu, col) in enumerate(((-0.30, (0.15, 0.15, 0.17)), (-0.18, (0.15, 0.15, 0.17)), (0.0, (0.15, 0.15, 0.17)))):     # clutch, brake, accelerator
        w_ = 0.075 if k < 2 else 0.055
        _poly(c, [(pu - w_ / 2, 0.075), (pu + w_ / 2, 0.075), (pu + w_ * 0.45, 0.19), (pu - w_ * 0.45, 0.19)], mix(col, WHITE, 0.15), scale(col, 0.5))
        for r_ in range(3):
            c.line(pu - w_ * 0.35, 0.10 + r_ * 0.03, pu + w_ * 0.35, 0.10 + r_ * 0.03, 0.005, (0.55, 0.56, 0.60), 0.8)
    # dashboard panel with the dials
    _rr(c, -0.40, 0.46, 0.40, 0.90, (0.20, 0.21, 0.25), (0.07, 0.07, 0.09), 0.05)
    _rr(c, -0.37, 0.49, 0.37, 0.87, (0.13, 0.14, 0.17), (0.06, 0.06, 0.08), 0.035, 0.8)
    _dial(c, -0.20, 0.69, 0.115, 140, (1.0, 0.45, 0.25))
    _dial(c, 0.20, 0.69, 0.115, 55, (0.4, 1.0, 0.6))
    c.rect(0.0, 0.78, 0.07, 0.04, (0.05, 0.08, 0.10), lift=0)
    c.text("D", 0.0, 0.78, 0.03, (0.4, 1.0, 0.6), 0.3)
    c.glow(0.0, 0.69, 0.5, (0.5, 0.8, 1.0), 0.14)
    # gear lever
    c.line(0.50, 0.06, 0.50, 0.30, 0.022, (0.55, 0.56, 0.60))
    c.ellipse(0.50, 0.33, 0.04, 0.04, (0.14, 0.14, 0.16), lift=0.3)
    gloss(c, 0.49, 0.35, 0.014, 0.01, 0, 0.7)
    # column and wheel
    _hfill(c, -0.04, 0.05, 0.04, 0.46, _cyl_fn((0.55, 0.56, 0.6), (0.14, 0.14, 0.16), 0.3), strips=6)
    cu, cv_, a, b = 0.0, 0.60, 0.40, 0.34
    soft_disc(c, 0.03, cv_ - 0.04, 0.45, 0.22, BLACK, 0.35, 1.3)
    for w, col, al in ((0.105, (0.07, 0.07, 0.08), 1.0), (0.078, (0.16, 0.16, 0.18), 1.0)):
        craft.arc(c, cu, cv_, a, b, 0, 360, w, col, al, steps=32, angle=8)
    craft.arc(c, cu, cv_, a, b, 105, 175, 0.018, (0.7, 0.72, 0.78), 0.55, steps=10, angle=8)
    craft.arc(c, cu, cv_, a * 0.98, b * 0.98, 190, 300, 0.012, (0.0, 0.0, 0.0), 0.35, steps=10, angle=8)
    for k in range(18):                                                              # stitching
        t = math.radians(k * 20 + 8)
        c.ellipse(cu + math.cos(t) * (a - 0.04), cv_ + math.sin(t) * (b - 0.04), 0.006, 0.004, (0.8, 0.8, 0.5), alpha=0.8, lift=0)
    for ang in (205, 335, 90):
        t = math.radians(ang)
        c.line(cu, cv_, cu + math.cos(t) * (a - 0.03), cv_ + math.sin(t) * (b - 0.03), 0.06, (0.11, 0.11, 0.13))
    c.ellipse(cu, cv_, 0.11, 0.10, (0.16, 0.16, 0.18), lift=0.3)
    c.ellipse(cu, cv_, 0.07, 0.065, acc, lift=0.35)
    c.text("L", cu, cv_, 0.065, WHITE, 0.3)
    gloss(c, cu - 0.05, cv_ + 0.04, 0.04, 0.02, 20, 0.5)


@niche("driving-school", "Driving school", subjects=("learn_hatchback",),
       strong=("driving school", "learn driving", "driving classes", "driving licence", "driving license", "car driving lessons", "driving lessons",
               "driving instructor", "motor driving", "ड्राइविंग स्कूल", "गाड़ी सीखें", "कार ड्राइविंग", "ड्राइविंग क्लास", "लाइसेंस", "driving sikho",
               "gaadi sikhna", "driving school wale", "learning to drive", "learn to drive", "dual control car", "dual control", "learner car"),
       weak=("driving", "learner", "licence", "license", "rto", "instructor", "ड्राइविंग", "road test", "driving test"),
       accent="#43a047", mood="light", group="education",
       avoid=("car wash", "car repair", "showroom", "taxi", "cab", "garage"))
def driving_school(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(21)
    sk_t, sk_b = _sky(P)
    grass = mix((0.38, 0.65, 0.30), P.accent, 0.3)
    grass = _tn(P, grass, 0.32)
    asph = _tn(P, (0.30, 0.31, 0.34), 0.5)
    with S.far():
        S.wall(sk_t, sk_b, 0.60)
        S.glow(1.7 if not dk else 0.4, 0.14, 0.6, (1.0, 0.95, 0.80) if not dk else (0.8, 0.85, 1.0), 0.4)
        if not dk:
            _cloud(S, 0.35, 0.16, 0.4, WHITE)
            _cloud(S, 1.55, 0.10, 0.5, WHITE, 0.8)
            _cloud(S, 2.15, 0.22, 0.35, WHITE, 0.7)
        S.ellipse(0.4, 0.62, 1.6, 0.14, _tn(P, mix(grass, (0.5, 0.7, 0.6), 0.4), 0.33), lift=0.0, soft=8)       # far hills
        S.ellipse(1.9, 0.63, 1.4, 0.11, _tn(P, mix(grass, (0.45, 0.65, 0.55), 0.35), 0.3), lift=0.0, soft=8)
        for i in range(16):                                                              # tree line
            u = -0.3 + i * 0.17
            tr = 0.07 + 0.03 * ((i * 7) % 5) / 4
            S.rect(u, 0.58, 0.012, 0.08, _tn(P, (0.35, 0.24, 0.16), 0.4), lift=0.0)
            S.circle(u, 0.50 - tr * 0.2, tr * 1.3, _tn(P, mix((0.20, 0.50, 0.24), P.accent, 0.2 + 0.1 * (i % 3)), 0.35), lift=0.18)
            S.circle(u + 0.03, 0.46, tr * 0.8, _tn(P, mix((0.28, 0.6, 0.28), P.accent, 0.2), 0.35), lift=0.18)
        S.rect(1.0, 0.64, 14.0, 0.10, grass, lift=0.0)
        S.floor(0.67, asph, scale(asph, 0.66))
        S.rect(1.0, 0.67, 14.0, 0.035, _tn(P, (0.78, 0.78, 0.76), 0.45), lift=0.0)             # kerb
        S.rect(1.0, 0.65, 14.0, 0.006, _tn(P, (0.5, 0.5, 0.5), 0.45), lift=0.0)
        S.soft(1.1, 0.82, 1.2, 0.18, P.light, 0.28 if not dk else 0.5, 1.4, add=True)
        if dk:
            for u in (0.3, 1.0, 1.8):
                S.glow(u, 0.38, 0.5, (1.0, 0.85, 0.55), 0.45)
                S.circle(u, 0.38, 0.016, (1.0, 0.95, 0.8), lift=0.0)
                S.rect(u, 0.5, 0.008, 0.24, (0.3, 0.3, 0.35), lift=0.0)
    # asphalt: tone patches, aggregate speckle, tyre marks, a zebra crossing and lane lines
    S.rect(1.0, 0.70, 14.0, 0.008, _tn(P, WHITE, 0.6), lift=0.0, alpha=0.8)                   # edge line
    for _ in range(7):
        u, v = rng.uniform(-0.2, 2.4), rng.uniform(0.74, 1.3)
        _spoly(S, [(u - 0.3, v - 0.04), (u + 0.3, v - 0.05), (u + 0.35, v + 0.05), (u - 0.25, v + 0.06)], BLACK if rng.random() < 0.6 else WHITE, None, 0.05)
    for _ in range(170):
        u, v = rng.uniform(-0.3, 2.5), rng.uniform(0.73, 1.35)
        S.rect(u, v, rng.uniform(0.003, 0.008), rng.uniform(0.002, 0.005), WHITE if rng.random() < 0.5 else BLACK, lift=0.0, alpha=rng.uniform(0.08, 0.2))
    for off in (-0.012, 0.012):
        _shair(S, 0.2, 1.08 + off, 2.2, 1.12 + off, BLACK, 0.12)
    for k in range(-8, 14):
        u = 1.0 + k * 0.34
        S.poly([(u, 1.06), (u + 0.20, 1.06), (u + 0.22, 1.09), (u - 0.02, 1.09)], _tn(P, WHITE, 0.6), 0.7)
    for k in range(7):                                                                      # zebra crossing stripes behind the signs
        u = 0.0 + k * 0.16
        _spoly(S, [(u, 0.735), (u + 0.09, 0.735), (u + 0.10 + k * 0.004, 0.80), (u - 0.02 + k * 0.004, 0.80)], _tn(P, WHITE, 0.6), None, 0.34)
    if dk:                                                                                  # headlight beam on the road
        _spoly(S, [(1.34, 0.86), (2.4, 0.74), (2.4, 1.24), (1.34, 0.98)], (1.0, 0.95, 0.80), (1.0, 0.95, 0.80), 0.30, 0.0)
    S.put("learn_sign_stop", 0.64, 0.74, 0.27, shadow_w=0.2)
    S.put("learn_sign_speed", 0.80, 0.74, 0.25, shadow_w=0.2)
    S.put("learn_sign_warn", 1.50, 0.74, 0.25, shadow_w=0.2)
    S.put("learn_sign_park", 1.82, 0.74, 0.25, shadow_w=0.2, framed=False)
    S.put("learn_hatchback", 1.14, 0.92, 0.36, color=P.accent, subject=True, shadow_w=0.8)
    S.put("learn_steering_wheel", 0.60, 1.07, 0.24, color=P.accent, shadow_w=0.4)
    S.put("learn_cone", 1.50, 1.00, 0.15, shadow_w=0.2)
    S.put("learn_cone", 1.41, 1.04, 0.12, shadow_w=0.2)
    S.put("learn_cone", 0.88, 1.06, 0.10, shadow_w=0.2, framed=False)
    S.focus("detail", 1.10, 0.74)
    with S.near(blur=18):
        S.soft(0.4, 1.05, 0.3, 0.1, P.accent_light, 0.22, 1.2, add=True)
        o = (0.95, 0.45, 0.12) if not dk else (0.45, 0.22, 0.08)                              # out-of-focus cone
        S.rect(1.78, 1.12, 0.17, 0.025, scale(o, 0.45), r=0.01, lift=0.1)
        S.poly([(1.72, 1.10), (1.84, 1.10), (1.805, 0.96), (1.755, 0.96)], o)
        S.poly([(1.735, 1.035), (1.825, 1.035), (1.815, 1.0), (1.745, 1.0)], WHITE if not dk else (0.5, 0.5, 0.5), 0.9)
        S.soft(1.75, 1.0, 0.03, 0.05, WHITE, 0.35, 1.2, add=True)


# ====================================================================================== music and dance academy
@sprop("learn_guitar", aspect=0.50, fill=1.0)
def learn_guitar(c, color):
    wood = color or (0.84, 0.52, 0.22)
    ao(c, 0.0, 0.0, 0.5, 0.07)
    for s in (-1, 1):                                                                   # stand
        c.line(s * 0.03, 0.12, s * 0.20, 0.0, 0.018, (0.10, 0.10, 0.12))
    c.line(0.0, 0.12, 0.0, 0.02, 0.016, (0.16, 0.16, 0.18))
    # neck and head
    _rr(c, -0.026, 0.50, 0.026, 0.90, (0.30, 0.17, 0.10), (0.18, 0.10, 0.06), 0.004)
    for k in range(13):
        v = 0.56 + k * 0.026
        c.line(-0.026, v, 0.026, v, 0.003, (0.85, 0.85, 0.80), 0.8)
    for v in (0.66, 0.74, 0.82):
        c.ellipse(0.0, v, 0.007, 0.007, (0.95, 0.95, 0.9), lift=0)
    _poly(c, [(-0.036, 0.89), (0.036, 0.89), (0.046, 1.0), (-0.046, 1.0)], (0.26, 0.15, 0.09), (0.15, 0.08, 0.05))
    for k in range(3):
        for s in (-1, 1):
            c.ellipse(s * 0.056, 0.915 + k * 0.03, 0.011, 0.009, (0.85, 0.86, 0.9), lift=0.3)
    # body: dark side, sunburst top, waist
    _oval(c, 0.0, 0.215, 0.215, 0.165, scale(wood, 0.36), None)
    _oval(c, 0.0, 0.47, 0.168, 0.125, scale(wood, 0.36), None)
    _poly(c, [(-0.15, 0.33), (0.15, 0.33), (0.15, 0.43), (-0.15, 0.43)], scale(wood, 0.36))
    _oval(c, 0.0, 0.225, 0.20, 0.15, mix(wood, (1.0, 0.8, 0.4), 0.2), scale(wood, 0.74))
    _oval(c, 0.0, 0.475, 0.153, 0.112, mix(wood, (1.0, 0.8, 0.4), 0.25), scale(wood, 0.78))
    _poly(c, [(-0.134, 0.33), (0.134, 0.33), (0.134, 0.43), (-0.134, 0.43)], mix(wood, (1.0, 0.8, 0.4), 0.22), scale(wood, 0.9))
    soft_disc(c, 0.0, 0.34, 0.24, 0.26, (0.15, 0.06, 0.02), 0.32, 1.6)
    soft_disc(c, 0.0, 0.40, 0.12, 0.13, (1.0, 0.85, 0.5), 0.30, 1.3, 0, True)
    c.ellipse(0.0, 0.40, 0.07, 0.07, (0.05, 0.03, 0.02), lift=0)
    for r, col in ((0.082, (0.20, 0.10, 0.05)), (0.074, (0.9, 0.78, 0.55)), (0.068, (0.15, 0.08, 0.04))):
        c.ellipse(0.0, 0.40, r, r, col, lift=0)
    c.ellipse(0.0, 0.40, 0.062, 0.062, (0.03, 0.02, 0.02), lift=0)
    soft_disc(c, 0.0, 0.40, 0.06, 0.06, BLACK, 0.5, 0.8)
    _poly(c, [(0.09, 0.30), (0.17, 0.26), (0.17, 0.36), (0.09, 0.40)], (0.12, 0.08, 0.07), None, 0.35)          # pick guard
    _rr(c, -0.07, 0.165, 0.07, 0.19, (0.20, 0.11, 0.07), (0.10, 0.06, 0.04), 0.008)
    c.line(-0.05, 0.178, 0.05, 0.178, 0.006, (0.9, 0.9, 0.85), 0.8)
    for k in range(6):                                                                 # strings
        u0 = -0.0225 + k * 0.009
        c.line(u0 * 1.6, 0.178, u0, 0.90, 0.0022, (0.92, 0.9, 0.82), 0.8)
    gloss(c, -0.10, 0.52, 0.05, 0.12, 20, 0.45)
    gloss(c, -0.12, 0.28, 0.04, 0.09, 30, 0.35)


@sprop("learn_keys", aspect=1.75, fill=0.78)
def learn_keys(c, color):
    w, h, d = 1.2, 0.07, 0.46
    dx, dy = d * 0.34, d * 0.30
    v0 = 0.40
    ao(c, 0.1, 0.0, 1.3, 0.14)
    for s in (-1, 1):                                                                     # X stand
        c.line(s * 0.40, v0 - 0.02, -s * 0.30 + 0.05, 0.0, 0.026, (0.10, 0.10, 0.12))
        c.line(s * 0.40, v0 - 0.02, s * 0.46, 0.0, 0.020, (0.14, 0.14, 0.16), 0.0)
    _box3(c, 0.0, v0, w, h, d, (0.11, 0.11, 0.13), top=(0.16, 0.16, 0.19), right=(0.06, 0.06, 0.07), r=0.01)
    x0 = -w / 2
    kd = 0.72
    n = 14
    kw = w / n
    vt = v0 + h
    for i in range(n):
        xa = x0 + i * kw
        _poly(c, [(xa + 0.002, vt), (xa + kw - 0.002, vt), (xa + kw - 0.002 + dx * kd, vt + dy * kd), (xa + 0.002 + dx * kd, vt + dy * kd)],
              (0.98, 0.98, 0.97), (0.86, 0.86, 0.85))
    for i in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12):
        xa = x0 + (i + 1) * kw - kw * 0.30
        q = [(xa, vt + dy * 0.30), (xa + kw * 0.6, vt + dy * 0.30), (xa + kw * 0.6 + dx * kd, vt + dy * kd), (xa + dx * kd, vt + dy * kd)]
        _poly(c, [(x, y - 0.012) for x, y in q], (0.02, 0.02, 0.03))
        _poly(c, q, (0.18, 0.18, 0.21), (0.05, 0.05, 0.06))
    _rr(c, x0, vt - 0.004, w / 2, vt + 0.008, (1.0, 1.0, 1.0), (0.78, 0.78, 0.78), 0.0)
    for k in range(3):                                                                    # knobs
        c.ellipse(0.40 + k * 0.07 + dx * 0.9, vt + dy * 0.88, 0.016, 0.009, (0.7, 0.72, 0.78), lift=0.2)
    c.ellipse(-0.40 + dx * 0.9, vt + dy * 0.88, 0.014, 0.008, (0.2, 1.0, 0.5), lift=0)
    c.glow(-0.40 + dx * 0.9, vt + dy * 0.88, 0.05, (0.2, 1.0, 0.5), 0.5)
    soft_disc(c, -0.25, vt + 0.04, 0.5, 0.05, WHITE, 0.18, 1.2, 0, True)


@sprop("learn_music_stand", aspect=0.78, fill=1.0)
def learn_music_stand(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.07)
    for s in (-1, 1):
        c.line(s * 0.02, 0.36, s * 0.24, 0.0, 0.016, (0.12, 0.12, 0.14))
    c.line(0.0, 0.36, 0.0, 0.02, 0.014, (0.2, 0.2, 0.22))
    _hfill(c, -0.014, 0.32, 0.014, 0.58, _cyl_fn((0.55, 0.56, 0.6), (0.14, 0.14, 0.16), 0.3), strips=4)
    _poly(c, [(-0.31, 0.56), (0.31, 0.56), (0.29, 1.0), (-0.29, 1.0)], (0.14, 0.14, 0.17), (0.08, 0.08, 0.10))
    _poly(c, [(-0.28, 0.605), (0.28, 0.605), (0.265, 0.985), (-0.265, 0.985)], (0.99, 0.97, 0.92), (0.90, 0.88, 0.82))
    _rr(c, -0.31, 0.54, 0.31, 0.60, (0.18, 0.18, 0.21), (0.08, 0.08, 0.1), 0.01)
    for si in range(4):
        v0 = 0.91 - si * 0.095
        for k in range(5):
            c.line(-0.24, v0 - k * 0.0125, 0.24, v0 - k * 0.0125, 0.0022, (0.2, 0.2, 0.25), 0.8)
        c.line(-0.24, v0, -0.24, v0 - 0.05, 0.003, (0.2, 0.2, 0.25), 0.9)
        for ni in range(7):
            nu = -0.20 + ni * 0.066 + (si % 2) * 0.01
            nv = v0 - 0.0125 * ((ni * 3 + si * 2) % 5)
            c.ellipse(nu, nv, 0.012, 0.0085, (0.08, 0.08, 0.1), angle=20, lift=0)
            c.line(nu + 0.011, nv, nu + 0.011, nv + 0.05, 0.0025, (0.1, 0.1, 0.12), 0.9)
    soft_disc(c, -0.1, 0.9, 0.3, 0.3, WHITE, 0.15, 1.2, 0, True)


@sprop("learn_tabla", aspect=1.65, fill=0.80)
def learn_tabla(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.22)
    # bayan (left, copper bowl) and dayan (right, wooden)
    for cu, kind in ((-0.36, "bayan"), (0.40, "dayan")):
        for r, col in ((0.34, (0.55, 0.12, 0.10)), (0.30, (0.78, 0.22, 0.16))):                    # cloth ring
            c.ellipse(cu, 0.045, r * (1.0 if kind == "bayan" else 0.8), 0.07, col, lift=0.1)
        if kind == "bayan":
            _oval(c, cu, 0.30, 0.34, 0.27, mix((0.80, 0.50, 0.30), WHITE, 0.15), scale((0.80, 0.50, 0.30), 0.45))
            _poly(c, [(cu + 0.12, 0.10), (cu + 0.32, 0.30), (cu + 0.30, 0.45), (cu + 0.20, 0.50), (cu + 0.30, 0.20)], BLACK, None, 0.28)
            soft_disc(c, cu - 0.14, 0.34, 0.10, 0.16, WHITE, 0.42, 1.1, 0, True)
            hv, hr = 0.55, 0.35
        else:
            _poly(c, [(cu - 0.20, 0.09), (cu + 0.20, 0.09), (cu + 0.26, 0.58), (cu - 0.26, 0.58)], (0.62, 0.34, 0.15), (0.36, 0.17, 0.07))
            _poly(c, [(cu + 0.05, 0.09), (cu + 0.20, 0.09), (cu + 0.26, 0.58), (cu + 0.10, 0.58)], BLACK, None, 0.30)
            soft_disc(c, cu - 0.11, 0.38, 0.04, 0.18, (1.0, 0.8, 0.5), 0.40, 1.1, 0, True)
            hv, hr = 0.60, 0.27
        # straps
        for k in range(8):
            ua = cu - hr * 0.9 + k * hr * 1.8 / 7
            c.line(ua, hv - 0.02, cu + (ua - cu) * 0.55, 0.12 if kind == "dayan" else 0.2, 0.012, (0.30, 0.17, 0.10), 0.9)
            c.line(ua + 0.012, hv - 0.02, cu + (ua - cu) * 0.55 + 0.02, 0.12 if kind == "dayan" else 0.2, 0.004, (0.55, 0.38, 0.25), 0.7)
        # head: rim, skin, black spot (syahi)
        c.ellipse(cu, hv, hr, hr * TILT, (0.14, 0.09, 0.06), lift=0.1)
        c.ellipse(cu, hv + 0.008, hr * 0.92, hr * TILT * 0.9, (0.93, 0.87, 0.74), lift=0.08)
        sx = cu - hr * 0.2 if kind == "bayan" else cu
        c.ellipse(sx, hv + 0.01, hr * 0.46, hr * TILT * 0.44, (0.05, 0.04, 0.04), lift=0.1)
        c.ellipse(sx, hv + 0.012, hr * 0.46, hr * TILT * 0.44, (0.10, 0.08, 0.08), alpha=0.5, lift=0)
        soft_disc(c, cu - hr * 0.35, hv + 0.03, hr * 0.4, hr * 0.12, WHITE, 0.4, 1.1, 0, True)
    c.ellipse(0.04, 0.08, 0.05, 0.02, (0.6, 0.6, 0.62), lift=0.2)
    c.line(0.30, 0.02, 0.50, 0.025, 0.028, (0.85, 0.82, 0.76))                                # hammer


@sprop("learn_violin", aspect=2.2, fill=0.46)
def learn_violin(c, color):
    rng = c.rng
    wood = color or (0.70, 0.30, 0.10)
    sq = 0.62
    ang = 8.0
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    cy = 0.22

    def P_(x, y):
        return (x * ca - y * sq * sa, cy + x * sa + y * sq * ca)

    ao(c, 0.0, 0.0, 1.5, 0.15)
    # bow behind
    bx0, by0 = P_(-0.60, -0.28)
    bx1, by1 = P_(0.65, -0.24)
    c.line(bx0, by0 - 0.03, bx1, by1 - 0.03, 0.012, BLACK, 0.25)
    c.line(bx0, by0, bx1, by1, 0.012, (0.45, 0.22, 0.10))
    c.line(bx0, by0 + 0.02, bx1, by1 + 0.02, 0.008, (0.95, 0.93, 0.85))
    c.ellipse(bx0, by0, 0.03, 0.02, (0.1, 0.1, 0.1), lift=0.1)
    # body
    def blob(dx, dy, ex, k):
        for (x, y, a, b, col) in ((-0.30, 0.0, 0.22, 0.20, k), (0.0, 0.0, 0.17, 0.15, k)):
            u, v = P_(x + dx, y + dy)
            c.ellipse(u, v, a + ex, (b + ex) * sq, col, angle=ang, lift=0.1)
        u, v = P_(-0.15 + dx, dy)
        c.ellipse(u, v, 0.12, 0.10 * sq, k, angle=ang, lift=0.0)
    blob(0.0, -0.03, 0.01, scale(wood, 0.35))
    blob(0.0, 0.0, 0.0, wood)
    u, v = P_(-0.30, 0.02)
    soft_disc(c, u, v, 0.24, 0.2 * sq, (1.0, 0.7, 0.3), 0.26, 1.4, ang, True)
    for k, (fx, fy) in enumerate(((-0.16, 0.07), (-0.16, -0.07))):                              # f-holes
        u, v = P_(fx, fy)
        c.ellipse(u, v, 0.03, 0.007, (0.08, 0.04, 0.02), angle=ang + 70, lift=0)
    u, v = P_(-0.15, 0.0)
    c.line(u, v - 0.03, u, v + 0.03, 0.02, (0.9, 0.8, 0.6))
    # neck, scroll, strings
    n0, n1 = P_(0.14, 0.0), P_(0.62, 0.0)
    c.line(n0[0], n0[1], n1[0], n1[1], 0.04, (0.12, 0.08, 0.06))
    c.ellipse(n1[0] + 0.03, n1[1] + 0.005, 0.03, 0.026, (0.45, 0.20, 0.08), lift=0.2)
    for k in range(4):
        a0, a1 = P_(-0.12, (k - 1.5) * 0.012), P_(0.62, (k - 1.5) * 0.008)
        c.line(a0[0], a0[1], a1[0], a1[1], 0.002, (0.95, 0.93, 0.8), 0.8)
    gloss(c, P_(-0.32, 0.08)[0], P_(-0.32, 0.08)[1], 0.10, 0.03, ang, 0.5)


@sprop("learn_ghungroo", aspect=2.6, fill=0.24)
def learn_ghungroo(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.10)
    n = 20
    pts = [(-0.55 + 1.1 * t / (n - 1), 0.07 + 0.035 * math.sin(t * 0.55)) for t in range(n)]
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], 0.022, (0.55, 0.06, 0.12))
        c.line(p[0], p[1] + 0.006, q[0], q[1] + 0.006, 0.006, (0.85, 0.3, 0.3), 0.6)
    gold = (0.92, 0.70, 0.18)
    for u, v in pts:
        c.ellipse(u, v - 0.01, 0.034, 0.034, scale(gold, 0.55), lift=0)
        c.ellipse(u - 0.003, v, 0.031, 0.031, gold, lift=0.25)
        c.line(u - 0.02, v - 0.008, u + 0.02, v - 0.008, 0.004, (0.3, 0.18, 0.04), 0.9)
        gloss(c, u - 0.011, v + 0.012, 0.01, 0.007, 20, 0.85)
        soft_disc(c, u + 0.01, v - 0.012, 0.016, 0.012, BLACK, 0.3, 1.2)


def _mirror(S, u0, v0, u1, v1, P, dk):
    base = mix(P.wall_bot, (0.72, 0.80, 0.90), 0.45) if not dk else mix(scale(P.wall_bot, 1.6), (0.25, 0.3, 0.42), 0.5)
    S.rect((u0 + u1) / 2, (v0 + v1) / 2, u1 - u0 + 0.04, v1 - v0 + 0.04, scale(P.accent_dark, 0.7), lift=0.0)
    S.gradient_rect(u0, v0, u1, v1, mix(base, WHITE, 0.25 if not dk else 0.0), scale(base, 0.82))
    for k in range(5):                                                                    # reflected light / sheen
        x = u0 + (u1 - u0) * (0.08 + 0.22 * k)
        S.poly([(x, v0), (x + 0.10, v0), (x - 0.08, v1), (x - 0.18, v1)], WHITE, 0.08 if not dk else 0.05)
    n = 5
    for k in range(n):
        S.rect(u0 + (u1 - u0) * (k + 1) / (n + 1) * 0.5 * 0 + u0 + (u1 - u0) * (k + 1) / (n + 1) - u0, (v0 + v1) / 2, 0.006, v1 - v0, scale(P.accent_dark, 0.6), lift=0.0, alpha=0.8)


@niche("music-academy", "Music and dance academy", subjects=("learn_guitar",),
       strong=("music academy", "music classes", "guitar classes", "dance academy", "singing classes", "music school", "dance classes", "tabla classes",
               "संगीत विद्यालय", "संगीत अकादमी", "म्यूजिक क्लास", "गिटार क्लास", "डांस अकादमी", "गाना सीखें", "sangeet vidyalaya", "music sikhna",
               "dance class", "kathak classes"),
       weak=("guitar", "piano", "violin", "tabla", "dance", "singing", "संगीत", "नृत्य"),
       accent="#8e24aa", mood="warm", group="education",
       avoid=("recording studio", "dj", "wedding"))
def music_academy(S):
    P = S.pal
    dk = _dk(P)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # acoustic panels with a diamond pattern on the left and right
        for (a, b) in ((-1.4, 0.35), (1.90, 3.4)):
            n = int((b - a) / 0.14)
            for i in range(n):
                for j in range(4):
                    col = mix(P.accent_dark, P.accent, 0.4 + 0.3 * ((i + j) % 2))
                    if dk:
                        col = scale(col, 0.6)
                    S.rect(a + i * 0.14 + 0.07, 0.06 + j * 0.14 + 0.07, 0.13, 0.13, col, lift=0.1, r=0.01)
        _mirror(S, 0.46, 0.08, 1.80, 0.58, P, dk)
        # barre in front of the mirror
        S.rect(1.13, 0.46, 1.45, 0.016, (0.78, 0.55, 0.32) if not dk else (0.40, 0.27, 0.16), lift=0.2)
        for u in (0.55, 1.13, 1.71):
            S.rect(u, 0.49, 0.012, 0.06, (0.2, 0.2, 0.22), lift=0.0)
        S.glow(0.7, 0.30, 0.5, (1.0, 0.75, 0.45), 0.35 if not dk else 0.45)
        S.glow(1.55, 0.25, 0.4, (1.0, 0.85, 0.6), 0.25 if not dk else 0.35)
        S.circle(0.7, 0.30, 0.03, (1.0, 0.9, 0.7), alpha=0.6, lift=0.0, soft=3)
        S.pendant(0.16, -0.05, 0.18, (1.0, 0.80, 0.5))
        S.pendant(1.95, -0.05, 0.14, (1.0, 0.80, 0.5))
        S.bokeh(10, 0.4, 0.1, 1.8, 0.5, [(1.0, 0.8, 0.5), (1.0, 0.6, 0.9), (0.9, 0.7, 1.0)], 0.01, 0.035, 0.22)
        S.rect(1.0, 0.585, 14.0, 0.03, scale(P.wall_bot, 0.55), lift=0.0)                       # skirting
    _planks(S, 0.60, mix(P.floor_top, (0.78, 0.55, 0.30), 0.4), mix(P.floor_bot, (0.5, 0.33, 0.18), 0.4), 0.22, vp=(1.1, -0.3))
    S.soft(1.2, 0.86, 1.3, 0.20, (1.0, 0.82, 0.55), 0.36 if not dk else 0.40, 1.4, add=True)
    for k in range(5):                                                                    # mirror reflection on polished floor
        S.soft(0.7 + k * 0.28, 0.74, 0.10, 0.16, (1.0, 0.85, 0.6), 0.08, 1.2, add=True)
    S.put("learn_music_stand", 0.74, 0.88, 0.44, shadow_w=0.4)
    S.put("learn_keys", 1.58, 0.86, 0.33, shadow_w=0.8)
    S.put("learn_guitar", 1.12, 0.93, 0.52, color=mix((0.84, 0.52, 0.22), P.accent, 0.1), subject=True, shadow_w=0.4)
    S.put("learn_tabla", 0.72, 1.02, 0.20, shadow_w=0.6)
    S.put("learn_violin", 1.38, 1.01, 0.11, shadow_w=0.6)
    S.put("learn_ghungroo", 1.02, 1.05, 0.065, shadow_w=0.3, framed=False)
    S.focus("detail", 1.12, 0.72)
    with S.near(blur=16):
        S.soft(0.5, 1.02, 0.25, 0.10, (1.0, 0.7, 0.4), 0.30, 1.2, add=True)
        S.ellipse(1.80, 1.05, 0.12, 0.08, scale(P.accent, 0.7), lift=0.1)


# ====================================================================================== shared shapes (round things)
def _lathe(c, hw, v0, v1, col, cu=0.0, n=16, hi=0.30, sh=0.38):
    """Surface of revolution seen from the side: silhouette from the half width function hw(v), lit left, shaded right."""
    vs = [v0 + (v1 - v0) * i / float(n) for i in range(n + 1)]
    L = [(cu - hw(v), v) for v in vs]
    R = [(cu + hw(v), v) for v in vs]
    _poly(c, L + R[::-1], mix(col, WHITE, 0.10), scale(col, 0.80))
    _poly(c, [(cu + hw(v) * 0.30, v) for v in vs] + R[::-1], BLACK, None, sh)
    _poly(c, [(cu - hw(v) * 0.78, v) for v in vs] + [(cu - hw(v) * 0.34, v) for v in vs][::-1], WHITE, None, hi)


def _sphere(c, u, v, r, col, spec=0.6):
    c.ellipse(u, v, r, r, scale(col, 0.58), lift=0)
    c.ellipse(u - r * 0.05, v + r * 0.06, r * 0.94, r * 0.94, col, lift=0.2)
    soft_disc(c, u + r * 0.28, v - r * 0.30, r * 0.66, r * 0.60, BLACK, 0.34, 1.3)
    gloss(c, u - r * 0.34, v + r * 0.38, r * 0.30, r * 0.17, 28, spec)


def _rot(pts, ang, org=(0.0, 0.0)):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(org[0] + x * ca - y * sa, org[1] + x * sa + y * ca) for x, y in pts]


# ====================================================================================== sports academy
@sprop("learn_stumps_bat", aspect=1.05, fill=1.0)
def learn_stumps_bat(c, color):
    rng = c.rng
    ao(c, 0.1, 0.0, 1.0, 0.14)
    wood = (0.90, 0.78, 0.55)
    for u in (-0.15, 0.0, 0.15):
        _hfill(c, u - 0.024, 0.02, u + 0.024, 0.74, _cyl_fn(mix(wood, WHITE, 0.2), scale(wood, 0.55), 0.28), strips=6)
        c.ellipse(u, 0.74, 0.024, 0.01, scale(wood, 0.8), lift=0.2)
        c.line(u, 0.02, u, 0.70, 0.003, scale(wood, 0.5), 0.35)
    for u0, u1 in ((-0.15, 0.0), (0.0, 0.15)):                                        # bails
        c.line(u0 + 0.01, 0.765, u1 - 0.01, 0.765, 0.016, mix(wood, WHITE, 0.2))
        c.line(u0 + 0.01, 0.772, u1 - 0.01, 0.772, 0.005, WHITE, 0.6)
    # bat leaning on the stumps from the right
    blade = (0.92, 0.76, 0.50)
    bp = [(0.0, 0.0), (0.0, 0.17), (0.60, 0.15), (0.60, -0.15), (0.0, -0.17)]
    ang = 72
    org = (0.30, 0.0)
    pts = _rot([(x, y) for x, y in [(-0.02, -0.075), (0.60, -0.095), (0.60, 0.095), (-0.02, 0.075)]], ang, org)
    c.line(org[0] + 0.02, 0.0, org[0] + 0.02 + math.cos(math.radians(ang)) * 0.60, math.sin(math.radians(ang)) * 0.60, 0.0, BLACK, 0.0)
    _poly(c, pts, mix(blade, WHITE, 0.12), scale(blade, 0.78))
    edge = _rot([(0.0, -0.075), (0.60, -0.095), (0.60, -0.04), (0.0, -0.03)], ang, org)
    _poly(c, edge, BLACK, None, 0.20)
    hl = _rot([(0.02, 0.05), (0.58, 0.07), (0.58, 0.085), (0.02, 0.066)], ang, org)
    _poly(c, hl, WHITE, None, 0.40)
    for k in range(6):                                                                 # grain
        a = _rot([(0.05 + k * 0.01, -0.06 + k * 0.022), (0.56, -0.07 + k * 0.025)], ang, org)
        c.line(a[0][0], a[0][1], a[1][0], a[1][1], 0.002, scale(blade, 0.65), 0.4)
    hs = _rot([(0.60, -0.017), (0.84, -0.017), (0.84, 0.017), (0.60, 0.017)], ang, org)
    _poly(c, hs, (0.80, 0.62, 0.40), (0.55, 0.40, 0.22))
    gp = _rot([(0.72, -0.024), (0.94, -0.024), (0.94, 0.024), (0.72, 0.024)], ang, org)
    _poly(c, gp, (0.12, 0.35, 0.65), (0.06, 0.2, 0.42))
    for k in range(5):
        a = _rot([(0.73 + k * 0.04, -0.024), (0.75 + k * 0.04, 0.024)], ang, org)
        c.line(a[0][0], a[0][1], a[1][0], a[1][1], 0.004, WHITE, 0.45)
    # ball at the foot
    _sphere(c, 0.52, 0.045, 0.045, (0.75, 0.10, 0.10), 0.7)
    craft.arc(c, 0.52, 0.045, 0.045, 0.045, 20, 160, 0.004, (0.95, 0.9, 0.8), 0.9, steps=8)


@sprop("learn_football", aspect=1.0, fill=1.0)
def learn_football(c, color):
    r = 0.5
    ao(c, 0.04, 0.0, 1.0, 0.16)
    cx, cy = 0.0, r
    c.ellipse(cx, cy, r, r, (0.62, 0.62, 0.64), lift=0)
    c.ellipse(cx - 0.01, cy + 0.015, r * 0.97, r * 0.97, (0.97, 0.97, 0.97), lift=0.14)

    def pent(px, py, s, k):
        pts = [(px + math.cos(math.radians(90 + 72 * i)) * s, py + math.sin(math.radians(90 + 72 * i)) * s * k) for i in range(5)]
        _poly(c, pts, (0.13, 0.13, 0.15), (0.04, 0.04, 0.05))
    pent(-0.04, cy + 0.06, 0.20, 0.95)
    for i in range(5):
        a = math.radians(90 + 72 * i + 18)
        px, py = -0.04 + math.cos(a) * 0.42, cy + 0.06 + math.sin(a) * 0.40
        pent(px, py, 0.115, 0.7)
        c.line(-0.04 + math.cos(a) * 0.19, cy + 0.06 + math.sin(a) * 0.19, px - math.cos(a) * 0.08, py - math.sin(a) * 0.08, 0.008, (0.55, 0.55, 0.58), 0.8)
    soft_disc(c, 0.18, cy - 0.18, 0.40, 0.36, BLACK, 0.40, 1.3)
    gloss(c, -0.18, cy + 0.22, 0.14, 0.08, 30, 0.7)


@sprop("learn_racket", aspect=0.52, fill=1.0)
def learn_racket(c, color):
    acc = color or (0.95, 0.45, 0.10)
    ang = -14
    org = (0.0, 0.02)
    ao(c, 0.0, 0.0, 0.5, 0.06)
    # head: frame ring, string grid
    hc = (0.0, 0.70)
    a, b = 0.205, 0.255
    hp = lambda x, y: _rot([(x, y)], ang, (0.0, 0.40))[0]            # noqa: E731  rotate about the throat
    for k in range(9):
        t = -0.85 + k * 0.2125
        xa = t * a
        yh = b * math.sqrt(max(0.0, 1 - t * t))
        p0, p1 = hp(xa, hc[1] - yh), hp(xa, hc[1] + yh)
        c.line(p0[0], p0[1], p1[0], p1[1], 0.003, (0.95, 0.95, 0.92), 0.8)
    for k in range(11):
        t = -0.9 + k * 0.18
        ya = hc[1] + t * b
        xw = a * math.sqrt(max(0.0, 1 - t * t))
        p0, p1 = hp(-xw, ya), hp(xw, ya)
        c.line(p0[0], p0[1], p1[0], p1[1], 0.003, (0.95, 0.95, 0.92), 0.8)
    ctr = hp(0.0, hc[1])
    craft.arc(c, ctr[0], ctr[1], a, b, 0, 360, 0.030, scale(acc, 0.55), 1.0, steps=30, angle=ang + 90 - 90)
    craft.arc(c, ctr[0], ctr[1], a, b, 0, 360, 0.020, acc, 1.0, steps=30, angle=ang)
    craft.arc(c, ctr[0], ctr[1], a, b, 95, 170, 0.006, WHITE, 0.6, steps=8, angle=ang)
    # throat, shaft, handle
    for sgn in (-1, 1):
        p0, p1 = hp(sgn * 0.07, hc[1] - b + 0.02), hp(sgn * 0.013, 0.34)
        c.line(p0[0], p0[1], p1[0], p1[1], 0.016, acc)
    p0, p1 = hp(0.0, 0.40), hp(0.0, 0.10)
    c.line(p0[0], p0[1], p1[0], p1[1], 0.014, (0.2, 0.2, 0.22))
    p2, p3 = hp(0.0, 0.26), hp(0.0, 0.0)
    c.line(p2[0], p2[1], p3[0], p3[1], 0.034, (0.10, 0.10, 0.12))
    c.line(p2[0] - 0.008, p2[1], p3[0] - 0.008, p3[1], 0.006, (0.5, 0.5, 0.55), 0.7)
    for k in range(5):
        q = hp(0.0, 0.03 + k * 0.045)
        c.line(q[0] - 0.017, q[1], q[0] + 0.017, q[1] + 0.01, 0.005, acc, 0.8)


@sprop("learn_shuttle", aspect=0.9, fill=1.0)
def learn_shuttle(c, color):
    ao(c, 0.0, 0.0, 0.7, 0.10)
    n = 14
    for k in range(n):
        t = (k + 0.5) / n * 2 - 1
        bu = t * 0.10
        tu = t * 0.34
        _poly(c, [(bu - 0.012, 0.22), (bu + 0.012, 0.22), (tu + 0.028, 0.95), (tu - 0.028, 0.95)], (0.99, 0.99, 0.97), (0.86, 0.87, 0.88), 0.97)
    for v in (0.50, 0.80):
        c.line(-0.07 - (v - 0.5) * 0.28, v, 0.07 + (v - 0.5) * 0.28, v, 0.006, (0.6, 0.6, 0.62), 0.8)
    c.ellipse(0.0, 0.95, 0.35, 0.09, (0.88, 0.9, 0.92), lift=0.0, alpha=0.7)
    _sphere(c, 0.0, 0.15, 0.13, (0.92, 0.72, 0.48), 0.5)
    c.ellipse(0.0, 0.17, 0.12, 0.03, (0.98, 0.98, 0.98), lift=0.1, alpha=0.9)


@sprop("learn_trophy", aspect=0.78, fill=1.0)
def learn_trophy(c, color):
    gold = (0.95, 0.74, 0.20)
    ao(c, 0.0, 0.0, 0.7, 0.12)
    _box3(c, 0.0, 0.0, 0.50, 0.10, 0.30, (0.20, 0.17, 0.15), top=(0.30, 0.26, 0.22), r=0.012)
    _rr(c, -0.17, 0.035, 0.17, 0.075, (0.95, 0.80, 0.35), (0.70, 0.52, 0.12), 0.006)
    c.text("1", 0.0, 0.055, 0.03, (0.3, 0.2, 0.05), 0.3)
    _lathe(c, lambda v: 0.07 - 0.03 * (v - 0.10) / 0.2 if v < 0.30 else 0.04, 0.10, 0.31, gold, n=6)
    _lathe(c, lambda v: 0.10 + 0.05 * math.sin((v - 0.28) / 0.07 * 1.5), 0.28, 0.35, gold, n=6)
    # handles
    for s in (-1, 1):
        craft.arc(c, s * 0.215, 0.72, 0.09, 0.15, -90 if s > 0 else 90, 90 if s > 0 else 270, 0.028, scale(gold, 0.7), 1.0, steps=10)
        craft.arc(c, s * 0.215, 0.72, 0.09, 0.15, -80 if s > 0 else 100, 80 if s > 0 else 260, 0.014, mix(gold, WHITE, 0.4), 0.9, steps=10)
    # bowl
    _lathe(c, lambda v: 0.22 * (1 - ((v - 0.88) / 0.5) ** 2) ** 0.55 if v < 0.88 else 0.22 * (1 - ((v - 0.88) / 0.12) ** 2) ** 0.5 * 0 + 0.215 * max(0.0, 1 - (v - 0.88) / 0.12 * 0.15),
           0.40, 0.98, gold, n=18, hi=0.45)
    c.ellipse(0.0, 0.98, 0.215, 0.045, mix(gold, WHITE, 0.3), lift=0.2)
    c.ellipse(0.0, 0.982, 0.19, 0.032, scale(gold, 0.4), lift=0)
    _sphere(c, 0.0, 0.335, 0.05, gold, 0.6)
    gloss(c, -0.12, 0.78, 0.03, 0.14, 8, 0.7)
    # star badge
    pts = []
    for i in range(10):
        r_ = 0.05 if i % 2 == 0 else 0.022
        pts.append((math.cos(math.radians(90 + 36 * i)) * r_, 0.68 + math.sin(math.radians(90 + 36 * i)) * r_))
    _poly(c, pts, (1.0, 0.95, 0.7), (0.9, 0.7, 0.2))


@niche("sports-academy", "Sports academy", subjects=("learn_stumps_bat",),
       strong=("sports academy", "cricket coaching", "football coaching", "badminton coaching", "swimming classes", "cricket academy", "football academy",
               "sports coaching", "sports club", "खेल अकादमी", "क्रिकेट कोचिंग", "क्रिकेट अकादमी", "फुटबॉल अकादमी", "बैडमिंटन कोचिंग", "स्पोर्ट्स अकादमी",
               "cricket sikhna", "khel academy"),
       weak=("cricket", "football", "badminton", "trophy", "coaching", "tournament", "खेल", "क्रिकेट"),
       accent="#ef6c00", mood="light", group="education",
       avoid=("gym", "fitness", "yoga"))
def sports_academy(S):
    P = S.pal
    dk = _dk(P)
    sk_t, sk_b = _sky(P)
    grass_a = _tn(P, mix((0.33, 0.62, 0.27), P.accent, 0.12), 0.34)
    grass_b = _tn(P, mix((0.26, 0.54, 0.22), P.accent, 0.10), 0.34)
    with S.far():
        S.wall(sk_t, sk_b, 0.58)
        # stands with a crowd
        S.rect(1.0, 0.40, 14.0, 0.24, _tn(P, mix((0.55, 0.58, 0.64), P.accent_light, 0.15), 0.35), lift=0.0)
        rng = random.Random(3)
        cols = [(0.9, 0.3, 0.25), (0.25, 0.5, 0.9), (0.95, 0.8, 0.2), (0.95, 0.95, 0.95), P.accent, (0.3, 0.75, 0.4)]
        for row in range(5):
            for i in range(60):
                u = -1.2 + i * 0.058 + (row % 2) * 0.03
                S.circle(u, 0.30 + row * 0.04 + rng.uniform(-0.005, 0.005), 0.014, _tn(P, cols[rng.randrange(6)], 0.5), alpha=0.85, lift=0.0)
        S.rect(1.0, 0.54, 14.0, 0.05, _tn(P, (0.78, 0.78, 0.8), 0.4), lift=0.0)
        S.rect(1.0, 0.565, 14.0, 0.018, P.accent if not dk else scale(P.accent, 0.6), lift=0.0)
        for u in (0.15, 1.95):                                                           # floodlight towers
            S.rect(u, 0.20, 0.014, 0.6, _tn(P, (0.45, 0.47, 0.5), 0.4), lift=0.0)
            S.rect(u, -0.02, 0.16, 0.08, _tn(P, (0.3, 0.32, 0.36), 0.5), lift=0.0)
            for k in range(6):
                S.circle(u - 0.06 + (k % 3) * 0.06, -0.04 + (k // 3) * 0.04, 0.014, (1.0, 0.98, 0.9), lift=0.0)
            S.glow(u, -0.02, 0.7, (1.0, 0.95, 0.8), 0.5 if dk else 0.30)
        if dk:
            S.light_shaft(0.12, 0.0, 0.18, 0.0, 1.0, 0.9, 0.4, 0.9, (1.0, 0.95, 0.8), 0.08)
        S.rect(1.0, 0.58, 14.0, 0.05, grass_a, lift=0.0)
        S.floor(0.60, grass_a, grass_b)
        S.soft(1.1, 0.80, 1.3, 0.22, P.light, 0.30 if not dk else 0.42, 1.4, add=True)
    # mowing stripes (alternating bands that widen towards the camera)
    v = 0.60
    k = 0
    h = 0.05
    while v < 1.9:
        if k % 2 == 0:
            S.rect(1.0, v + h / 2, 14.0, h, _tn(P, (1.0, 1.0, 1.0), 0.4), alpha=0.07, lift=0.0)
        else:
            S.rect(1.0, v + h / 2, 14.0, h, BLACK, alpha=0.06, lift=0.0)
        v += h
        h *= 1.17
        k += 1
    S.rect(1.0, 0.76, 14.0, 0.006, _tn(P, WHITE, 0.7), alpha=0.7, lift=0.0)                 # white line
    S.put("learn_trophy", 1.34, 0.84, 0.40, shadow_w=0.3)
    S.put("learn_stumps_bat", 0.98, 0.93, 0.48, subject=True, shadow_w=0.8)
    S.put("learn_racket", 0.70, 0.97, 0.46, color=P.accent, shadow_w=0.3)
    S.put("learn_football", 1.50, 1.01, 0.17, shadow_w=0.25)
    S.put("learn_shuttle", 0.84, 1.03, 0.12, shadow_w=0.2)
    S.put("learn_cone", 1.62, 0.90, 0.12, color=(0.98, 0.50, 0.10), shadow_w=0.15)
    S.put("learn_cone", 0.40, 0.90, 0.11, color=(0.98, 0.78, 0.15), shadow_w=0.15, framed=False)
    S.focus("detail", 1.20, 0.78)
    with S.near(blur=18):
        S.soft(0.45, 1.05, 0.3, 0.10, P.accent_light, 0.25, 1.2, add=True)
        S.circle(1.85, 1.08, 0.08, (0.85, 0.85, 0.85) if not dk else (0.3, 0.3, 0.35), lift=0.1)


# ====================================================================================== robotics and STEM lab
def _seg(c, p0, p1, w, col, led=None):
    """A rounded robot-arm link between two points: lit side, shaded side, centre seam and an optional glowing stripe."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * w / 2, dx / ln * w / 2
    quad = [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]
    c.line(p0[0], p0[1], p1[0], p1[1], w, scale(col, 0.62))
    c.line(p0[0] + nx * 0.1, p0[1] + ny * 0.1 + 0.002, p1[0] + nx * 0.1, p1[1] + ny * 0.1 + 0.002, w * 0.86, col)
    c.line(p0[0] + nx * 0.42, p0[1] + ny * 0.42, p1[0] + nx * 0.42, p1[1] + ny * 0.42, w * 0.20, WHITE, 0.40)
    c.line(p0[0] - nx * 0.62, p0[1] - ny * 0.62, p1[0] - nx * 0.62, p1[1] - ny * 0.62, w * 0.22, BLACK, 0.22)
    if led is not None:
        a = (p0[0] + dx * 0.25, p0[1] + dy * 0.25)
        b = (p0[0] + dx * 0.75, p0[1] + dy * 0.75)
        c.line(a[0], a[1], b[0], b[1], w * 0.12, led, 0.95)
        c.glow((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, ln * 0.5, led, 0.30)


def _joint(c, u, v, r, col, led):
    c.ellipse(u, v, r * 1.06, r * 1.06, scale(col, 0.5), lift=0)
    c.ellipse(u - r * 0.03, v + r * 0.04, r, r, col, lift=0.22)
    c.ellipse(u, v, r * 0.62, r * 0.62, (0.10, 0.12, 0.15), lift=0.1)
    c.ellipse(u, v, r * 0.42, r * 0.42, led, lift=0.0)
    c.glow(u, v, r * 2.4, led, 0.5)
    gloss(c, u - r * 0.4, v + r * 0.45, r * 0.3, r * 0.15, 25, 0.55)


@sprop("learn_robot_arm", aspect=1.0, fill=1.0)
def learn_robot_arm(c, color):
    led = color or (0.15, 0.85, 1.0)
    shell = (0.90, 0.92, 0.95)
    dark = (0.18, 0.20, 0.25)
    ao(c, 0.0, 0.0, 0.7, 0.12)
    _lathe(c, lambda v: 0.26 - 0.02 * (v / 0.09), 0.0, 0.09, dark, n=4)
    c.ellipse(0.0, 0.095, 0.25, 0.25 * TILT * 0.9, mix(dark, WHITE, 0.1), lift=0.2)
    craft.arc(c, 0.0, 0.07, 0.25, 0.10, 190, 350, 0.012, led, 0.95, steps=12)
    c.glow(0.0, 0.07, 0.4, led, 0.25)
    _rr(c, -0.15, 0.09, 0.15, 0.30, mix(shell, WHITE, 0.1), scale(shell, 0.72), 0.04)
    c.rect(0.0, 0.20, 0.02, 0.16, dark, lift=0)
    sh = (0.0, 0.36)
    el = (0.19, 0.74)
    wr = (0.60, 0.62)
    _seg(c, sh, el, 0.17, shell, led)
    _joint(c, sh[0], sh[1], 0.115, dark, led)
    _seg(c, el, wr, 0.13, shell, led)
    _joint(c, el[0], el[1], 0.095, dark, led)
    _joint(c, wr[0], wr[1], 0.07, dark, led)
    # wrist and gripper holding a cube
    _rr(c, wr[0] - 0.06, wr[1] - 0.11, wr[0] + 0.06, wr[1] - 0.04, dark, scale(dark, 0.6), 0.015)
    for s in (-1, 1):
        _seg(c, (wr[0] + s * 0.045, wr[1] - 0.10), (wr[0] + s * 0.045, wr[1] - 0.25), 0.032, (0.75, 0.78, 0.82))
        c.rect(wr[0] + s * 0.032, wr[1] - 0.25, 0.012, 0.03, (0.1, 0.1, 0.12), lift=0)
    _box3(c, wr[0], wr[1] - 0.33, 0.09, 0.09, 0.08, (1.0, 0.55, 0.12), r=0.008)
    c.glow(wr[0], wr[1] - 0.28, 0.12, (1.0, 0.6, 0.2), 0.22)


def _fq(u0, v0, x, y, k=0.42, sk=0.35, z=0.0):
    return (u0 + x + y * sk, v0 + y * k + z)


def _fquad(c, u0, v0, x0, y0, x1, y1, top, bot=None, alpha=1.0, z=0.0):
    _poly(c, [_fq(u0, v0, x0, y0, z=z), _fq(u0, v0, x1, y0, z=z), _fq(u0, v0, x1, y1, z=z), _fq(u0, v0, x0, y1, z=z)], top, bot, alpha)


def _fbox(c, u0, v0, x0, y0, x1, y1, h, top, side=None):
    side = side or scale(top, 0.5)
    _poly(c, [_fq(u0, v0, x1, y0), _fq(u0, v0, x1, y1), _fq(u0, v0, x1, y1, z=h), _fq(u0, v0, x1, y0, z=h)], scale(side, 0.8), None)
    _poly(c, [_fq(u0, v0, x0, y0), _fq(u0, v0, x1, y0), _fq(u0, v0, x1, y0, z=h), _fq(u0, v0, x0, y0, z=h)], side, None)
    _fquad(c, u0, v0, x0, y0, x1, y1, top, scale(top, 0.9), z=h)


def _chip(c, u0, v0, x, y, w, d, h=0.025, pins=5):
    for k in range(pins):
        px = x + w * (k + 0.5) / pins
        _poly(c, [_fq(u0, v0, px - 0.006, y - 0.012), _fq(u0, v0, px + 0.006, y - 0.012), _fq(u0, v0, px + 0.006, y + 0.004), _fq(u0, v0, px - 0.006, y + 0.004)],
              (0.75, 0.75, 0.78))
    _fbox(c, u0, v0, x, y, x + w, y + d, h, (0.09, 0.09, 0.11), (0.04, 0.04, 0.05))
    _fquad(c, u0, v0, x + w * 0.08, y + d * 0.12, x + w * 0.5, y + d * 0.30, WHITE, None, 0.12, z=h)


@sprop("learn_pcb", aspect=3.6, fill=0.30)
def learn_pcb(c, color):
    rng = c.rng
    led = color or (0.15, 0.85, 1.0)
    u0, v0 = -0.45, 0.0
    ao(c, 0.1, 0.0, 1.5, 0.12)
    gr = (0.04, 0.38, 0.27)
    _fbox(c, u0, v0, 0.0, 0.0, 1.0, 0.62, 0.02, gr, (0.02, 0.18, 0.13))
    _fquad(c, u0, v0, 0.02, 0.02, 0.98, 0.60, mix(gr, WHITE, 0.08), scale(gr, 0.85), 0.8, z=0.02)
    gold = (0.95, 0.78, 0.35)
    tp = lambda x, y: _fq(u0, v0, x, y, z=0.021)                                                   # noqa: E731
    for k in range(9):                                                                              # traces
        y = 0.08 + k * 0.058
        pa, pb, pc_ = tp(0.10, y), tp(0.40 + (k % 3) * 0.08, y), tp(0.55 + (k % 4) * 0.06, y + 0.05)
        c.line(pa[0], pa[1], pb[0], pb[1], 0.004, gold, 0.75)
        c.line(pb[0], pb[1], pc_[0], pc_[1], 0.004, gold, 0.75)
    for k in range(4):
        pa, pb = tp(0.62 + k * 0.08, 0.08), tp(0.62 + k * 0.08, 0.55)
        c.line(pa[0], pa[1], pb[0], pb[1], 0.004, gold, 0.6)
    _chip(c, u0, v0, 0.18, 0.18, 0.30, 0.22, 0.03, 7)
    _chip(c, u0, v0, 0.58, 0.30, 0.20, 0.16, 0.025, 4)
    for i in range(10):                                                                             # header pins
        p = _fq(u0, v0, 0.12 + i * 0.045, 0.56, z=0.02)
        c.ellipse(p[0], p[1] + 0.006, 0.009, 0.007, (0.1, 0.1, 0.12), lift=0.1)
        c.ellipse(p[0], p[1] + 0.012, 0.005, 0.004, gold, lift=0.2)
    for i, (x, y) in enumerate(((0.10, 0.10), (0.15, 0.10), (0.80, 0.14), (0.86, 0.45), (0.50, 0.10))):    # capacitors
        p = _fq(u0, v0, x, y, z=0.02)
        c.rect(p[0], p[1] + 0.02, 0.026, 0.04, (0.12, 0.12, 0.14) if i % 2 else (0.15, 0.25, 0.55), lift=0.15)
        c.ellipse(p[0], p[1] + 0.04, 0.013, 0.007, (0.75, 0.75, 0.78), lift=0.2)
    for x, y, col in ((0.90, 0.10, led), (0.90, 0.18, (1.0, 0.3, 0.25))):                           # LEDs
        p = _fq(u0, v0, x, y, z=0.02)
        c.glow(p[0], p[1] + 0.01, 0.07, col, 0.7)
        c.ellipse(p[0], p[1] + 0.01, 0.014, 0.01, mix(col, WHITE, 0.5), lift=0)
    for k in range(6):                                                                              # SMD resistors
        p = _fq(u0, v0, 0.54 + (k % 3) * 0.05, 0.12 + (k // 3) * 0.05, z=0.02)
        c.rect(p[0], p[1] + 0.006, 0.026, 0.012, (0.08, 0.08, 0.09), lift=0.1)
        c.rect(p[0] - 0.01, p[1] + 0.006, 0.006, 0.012, (0.85, 0.85, 0.85), lift=0)
        c.rect(p[0] + 0.01, p[1] + 0.006, 0.006, 0.012, (0.85, 0.85, 0.85), lift=0)
    soft_disc(c, 0.0, 0.14, 0.8, 0.12, WHITE, 0.12, 1.2, 0, True)


@sprop("learn_arduino", aspect=2.8, fill=0.34)
def learn_arduino(c, color):
    u0, v0 = -0.40, 0.0
    ao(c, 0.15, 0.0, 1.3, 0.12)
    bl = (0.0, 0.46, 0.54)
    gold = (0.95, 0.78, 0.35)
    _fbox(c, u0, v0, 0.0, 0.0, 0.92, 0.64, 0.022, bl, scale(bl, 0.4))
    _fquad(c, u0, v0, 0.01, 0.01, 0.91, 0.63, mix(bl, WHITE, 0.08), scale(bl, 0.9), 0.8, z=0.022)
    _fbox(c, u0, v0, -0.04, 0.38, 0.14, 0.58, 0.10, (0.78, 0.80, 0.84), (0.45, 0.47, 0.52))                 # USB
    _fquad(c, u0, v0, -0.03, 0.42, 0.0, 0.54, (0.1, 0.1, 0.12), None, 1.0, z=0.10)
    _fbox(c, u0, v0, -0.03, 0.06, 0.12, 0.26, 0.085, (0.12, 0.12, 0.14), (0.05, 0.05, 0.06))               # DC jack
    _chip(c, u0, v0, 0.50, 0.22, 0.36, 0.12, 0.03, 14)
    _chip(c, u0, v0, 0.24, 0.20, 0.14, 0.14, 0.02, 4)
    _fbox(c, u0, v0, 0.22, 0.42, 0.36, 0.52, 0.05, (0.8, 0.8, 0.82), (0.5, 0.5, 0.52))
    # headers (black strips with gold pin tips) top and bottom
    for y in (0.58, 0.02):
        _fbox(c, u0, v0, 0.20, y, 0.86, y + 0.055, 0.04, (0.10, 0.10, 0.12), (0.04, 0.04, 0.05))
        for i in range(15):
            p = _fq(u0, v0, 0.215 + i * 0.043, y + 0.027, z=0.04)
            c.ellipse(p[0], p[1], 0.008, 0.005, gold, lift=0.2)
    c.text("UNO", _fq(u0, v0, 0.40, 0.34, z=0.023)[0] + 0.0, _fq(u0, v0, 0.40, 0.34, z=0.023)[1], 0.036, (0.9, 0.97, 1.0), 0.25)
    p = _fq(u0, v0, 0.16, 0.50, z=0.022)
    c.ellipse(p[0], p[1] + 0.01, 0.018, 0.012, (0.85, 0.15, 0.12), lift=0.3)
    for k, col in enumerate(((0.3, 1.0, 0.4), (1.0, 0.8, 0.2))):
        p = _fq(u0, v0, 0.78 + k * 0.05, 0.40, z=0.022)
        c.glow(p[0], p[1], 0.06, col, 0.6)
        c.ellipse(p[0], p[1], 0.01, 0.007, mix(col, WHITE, 0.5), lift=0)
    soft_disc(c, 0.0, 0.14, 0.7, 0.12, WHITE, 0.12, 1.2, 0, True)


@sprop("learn_drone", aspect=1.45, fill=0.72)
def learn_drone(c, color):
    led = color or (0.15, 0.85, 1.0)
    ao(c, 0.0, 0.0, 1.2, 0.2)
    dark = (0.14, 0.15, 0.18)
    shell = (0.84, 0.86, 0.90)
    mots = [(-0.52, 0.52), (0.52, 0.52), (-0.60, 0.18), (0.60, 0.18)]
    cy = 0.30
    for s in (-1, 1):                                                                                   # skids
        c.line(s * 0.22, 0.10, s * 0.24, 0.0, 0.016, (0.1, 0.1, 0.12))
    for i, (mu, mv) in enumerate(mots):
        if mv > 0.4:
            _seg(c, (0.0, cy + 0.03), (mu, mv - 0.04), 0.05, dark)
    c.ellipse(0.0, cy + 0.02, 0.28, 0.20, scale(dark, 0.7), lift=0)
    _rr(c, -0.20, cy - 0.04, 0.20, cy + 0.14, mix(shell, WHITE, 0.15), scale(shell, 0.60), 0.07)
    _rr(c, -0.14, cy + 0.10, 0.14, cy + 0.17, scale(shell, 1.0), scale(shell, 0.7), 0.04)
    c.line(-0.14, cy + 0.025, 0.14, cy + 0.025, 0.014, led, 0.95)
    c.glow(0.0, cy + 0.025, 0.28, led, 0.35)
    c.ellipse(0.0, cy - 0.02, 0.045, 0.045, (0.04, 0.04, 0.05), lift=0.2)                               # camera gimbal
    c.ellipse(0.0, cy - 0.02, 0.022, 0.022, (0.1, 0.25, 0.5), lift=0.3)
    gloss(c, -0.08, cy + 0.12, 0.07, 0.02, 0, 0.55)
    for i, (mu, mv) in enumerate(mots):
        if mv <= 0.4:
            _seg(c, (0.0, cy), (mu, mv - 0.02), 0.06, dark)
    for i, (mu, mv) in enumerate(mots):
        c.ellipse(mu, mv, 0.05, 0.05 * 0.9, dark, lift=0.3)
        c.ellipse(mu, mv + 0.03, 0.30, 0.30 * 0.17, WHITE, alpha=0.10, lift=0)
        c.ellipse(mu, mv + 0.03, 0.30, 0.30 * 0.17, (0.7, 0.8, 0.9), alpha=0.10, lift=0)
        a = 12 if i % 2 else -12
        c.line(mu - 0.29, mv + 0.03 - 0.02 * a / 12, mu + 0.29, mv + 0.03 + 0.02 * a / 12, 0.015, (0.07, 0.07, 0.09), 0.55)
        c.ellipse(mu, mv + 0.04, 0.02, 0.02 * 0.6, (0.6, 0.62, 0.68), lift=0.2)
        col = (1.0, 0.3, 0.25) if i < 2 else led
        c.ellipse(mu, mv - 0.03, 0.011, 0.011, col, lift=0)
        c.glow(mu, mv - 0.03, 0.08, col, 0.5)


@sprop("learn_solder", aspect=1.55, fill=0.50)
def learn_solder(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.3, 0.2)
    _box3(c, -0.15, 0.0, 0.60, 0.10, 0.36, (0.15, 0.16, 0.19), r=0.012)
    c.ellipse(-0.32, 0.17, 0.10, 0.06, (0.95, 0.80, 0.25), lift=0.2)                                   # brass sponge pot
    c.ellipse(-0.32, 0.175, 0.07, 0.04, (0.85, 0.7, 0.2), lift=0.2)
    for k in range(5):
        c.line(-0.40 + k * 0.04, 0.17, -0.38 + k * 0.04, 0.2, 0.004, (0.5, 0.35, 0.1), 0.7)
    for k in range(6):                                                                                   # coil holder
        c.ellipse(0.02, 0.12 + k * 0.03, 0.075, 0.025, (0.75, 0.77, 0.80), lift=0.3, alpha=0.9)
    _poly(c, [(-0.04, 0.12), (0.08, 0.12), (0.08, 0.30), (-0.04, 0.30)], BLACK, None, 0.0)
    # iron: handle (rubber), silver body, tip glowing
    ang = 18
    org = (-0.05, 0.40)
    h = _rot([(0.0, -0.034), (0.62, -0.040), (0.62, 0.040), (0.0, 0.034)], ang, org)
    _poly(c, h, (0.18, 0.18, 0.20), (0.08, 0.08, 0.10))
    h2 = _rot([(0.10, -0.034), (0.40, -0.04), (0.40, 0.040), (0.10, 0.034)], ang, org)
    _poly(c, h2, (0.95, 0.45, 0.12), (0.72, 0.28, 0.06))
    h3 = _rot([(0.05, 0.012), (0.58, 0.016), (0.58, 0.034), (0.05, 0.030)], ang, org)
    _poly(c, h3, WHITE, None, 0.25)
    t = _rot([(-0.16, -0.012), (0.0, -0.022), (0.0, 0.022), (-0.16, 0.012)], ang, org)
    _poly(c, t, (0.80, 0.82, 0.86), (0.5, 0.52, 0.56))
    tip = _rot([(-0.30, 0.0)], ang, org)[0]
    c.line(t[0][0], t[0][1], tip[0], tip[1], 0.014, (0.88, 0.5, 0.35))
    c.glow(tip[0], tip[1], 0.10, (1.0, 0.45, 0.2), 0.55)
    craft.steam(c, tip[0], tip[1] + 0.02, 0.28, 0.025, 2, 0.15)
    # solder spool
    c.ellipse(0.52, 0.04, 0.17, 0.17 * TILT, (0.55, 0.5, 0.42), lift=0)
    _rr(c, 0.35, 0.04, 0.69, 0.22, (0.72, 0.74, 0.78), (0.4, 0.42, 0.46), 0.01)
    c.ellipse(0.52, 0.22, 0.17, 0.17 * TILT, (0.82, 0.84, 0.88), lift=0.2)
    c.ellipse(0.52, 0.225, 0.065, 0.065 * TILT, (0.2, 0.2, 0.22), lift=0)
    for k in range(5):
        c.line(0.38, 0.07 + k * 0.026, 0.66, 0.07 + k * 0.026, 0.006, (0.9, 0.92, 0.95), 0.6)
    gloss(c, 0.43, 0.20, 0.06, 0.012, 0, 0.6)


@niche("robotics-lab", "Robotics and STEM lab", subjects=("learn_robot_arm",),
       strong=("robotics lab", "stem lab", "arduino", "coding for kids", "drone workshop", "robotics classes", "atal tinkering lab", "tinkering lab",
               "robotics training", "रोबोटिक्स", "रोबोटिक लैब", "आर्डिनो", "ड्रोन", "स्टेम लैब", "robotics sikhna", "robot banana"),
       weak=("robot", "circuit", "drone", "soldering", "electronics", "iot", "raspberry pi", "3d printing", "ai"),
       accent="#00acc1", mood="dark", group="education",
       avoid=("electrician", "plumbing", "repair"))
def robotics_lab(S):
    P = S.pal
    dk = _dk(P)
    cy_ = (0.15, 0.85, 1.0)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.30, 14.0, 0.012, mix(P.accent, WHITE, 0.4), lift=0.0)
        # shelving with part bins on the left
        for r in range(3):
            S.rect(0.35, 0.18 + r * 0.17, 0.90, 0.012, scale(P.accent_dark, 0.7), lift=0.0)
            for i in range(8):
                col = mix(P.wall_bot, P.accent, 0.35 + 0.1 * ((i + r) % 3))
                S.rect(-0.02 + i * 0.105, 0.13 + r * 0.17, 0.09, 0.075, scale(col, 0.55) if dk else col, lift=0.1, r=0.006)
                S.rect(-0.02 + i * 0.105, 0.145 + r * 0.17, 0.04, 0.012, cy_ if dk else (0.9, 0.95, 1.0), lift=0.0, alpha=0.9)
        # pegboard with silhouettes of tools
        S.rect(1.95, 0.22, 0.75, 0.38, scale(P.wall_bot, 0.75), lift=0.0)
        for i in range(6):
            S.line(1.65 + i * 0.12, 0.08, 1.65 + i * 0.12, 0.22 + (i % 3) * 0.04, 0.012, (0.6, 0.65, 0.7) if not dk else (0.25, 0.3, 0.38))
        # monitors with waveforms
        for (mu, w) in ((0.95, 0.42), (1.45, 0.32)):
            S.rect(mu, 0.24, w, w * 0.62, (0.04, 0.05, 0.08), r=0.01, lift=0.0)
            S.gradient_rect(mu - w / 2 + 0.015, 0.24 - w * 0.31 + 0.015, mu + w / 2 - 0.015, 0.24 + w * 0.31 - 0.015, scale(P.accent_dark, 0.5), (0.02, 0.06, 0.10))
            S.glow(mu, 0.24, w * 1.5, cy_, 0.50 if dk else 0.25)
            for k in range(14):
                S.line(mu - w / 2 + 0.04 + k * (w - 0.08) / 14, 0.24 + math.sin(k * 0.9 + mu * 5) * w * 0.12,
                       mu - w / 2 + 0.04 + (k + 1) * (w - 0.08) / 14, 0.24 + math.sin((k + 1) * 0.9 + mu * 5) * w * 0.12, 0.006, cy_)
        S.rect(1.0, 0.56, 14.0, 0.012, cy_, lift=0.0, alpha=0.9)
        S.glow(1.0, 0.56, 1.6, cy_, 0.50 if dk else 0.25, 1.6)
        S.bokeh(12, 0.0, 0.1, 2.0, 0.55, [cy_, (0.4, 0.9, 1.0), (1.0, 0.6, 0.3)], 0.008, 0.03, 0.30)
        bt = (0.09, 0.12, 0.16) if dk else mix((0.74, 0.78, 0.84), P.wall_bot, 0.3)
        S.floor(0.60, bt, scale(bt, 0.65))
        S.soft(1.1, 0.80, 1.3, 0.22, cy_ if dk else P.light, 0.35 if dk else 0.30, 1.4, add=True)
    # ESD mat with grid
    mat = (0.06, 0.20, 0.24) if dk else mix((0.45, 0.70, 0.72), P.accent, 0.3)
    _spoly(S, [(0.40, 0.69), (1.95, 0.69), (2.20, 1.30), (0.10, 1.30)], mat, scale(mat, 0.8))
    for k in range(-2, 12):
        _shair(S, 0.40 + k * 0.18, 0.69, 0.10 + k * 0.24 - 0.0, 1.30, WHITE, 0.10)
    for vv in (0.74, 0.82, 0.92, 1.06, 1.22):
        _shair(S, 0.10, vv, 2.2, vv, WHITE, 0.10)
    S.put("learn_pcb", 0.74, 0.84, 0.15, color=cy_, shadow_w=0.6)
    S.put("learn_drone", 1.58, 0.88, 0.40, color=cy_, shadow_w=0.7)
    S.put("learn_robot_arm", 1.00, 0.92, 0.55, color=cy_, subject=True, shadow_w=0.5)
    S.put("learn_arduino", 0.78, 1.02, 0.15, shadow_w=0.6)
    S.put("learn_solder", 1.40, 1.02, 0.22, shadow_w=0.6)
    S.focus("detail", 1.0, 0.70)
    with S.near(blur=16):
        S.soft(0.5, 1.04, 0.30, 0.10, cy_, 0.28 if dk else 0.12, 1.2, add=True)
        S.ellipse(1.85, 1.07, 0.09, 0.06, (0.2, 0.9, 1.0) if dk else (0.3, 0.6, 0.7), lift=0.1)


# ====================================================================================== hotel
@sprop("learn_hotel_bed", aspect=2.05, fill=0.98)
def learn_hotel_bed(c, color):
    rng = c.rng
    acc = color or (0.17, 0.33, 0.38)                     # headboard fabric
    gold = mix(acc, (0.93, 0.74, 0.32), 0.78)
    ao(c, 0.10, 0.0, 1.6, 0.24)
    soft_disc(c, 0.07, 0.50, 0.95, 0.55, (1.0, 0.82, 0.5), 0.12, 1.4, 0, True)           # cove light washing the headboard
    tl = (0.18, 0.30)
    # channel-tufted headboard with gold nail-head trim
    _rr(c, -0.62, 0.24, 0.76, 0.94, mix(acc, WHITE, 0.10), scale(acc, 0.62), 0.09)
    _rr(c, -0.585, 0.275, 0.725, 0.905, mix(acc, WHITE, 0.04), scale(acc, 0.78), 0.07, 0.95)
    nch = 8
    cw = 1.30 / nch
    for i in range(nch):
        x0 = -0.565 + i * cw
        _poly(c, [(x0 + cw * 0.04, 0.295), (x0 + cw * 0.40, 0.295), (x0 + cw * 0.40, 0.89), (x0 + cw * 0.04, 0.89)], WHITE, None, 0.13)
        _poly(c, [(x0 + cw * 0.70, 0.295), (x0 + cw * 0.97, 0.295), (x0 + cw * 0.97, 0.89), (x0 + cw * 0.70, 0.89)], BLACK, None, 0.18)
        c.line(x0 + cw, 0.30, x0 + cw, 0.885, 0.006, scale(acc, 0.45), 0.55)
        for j in range(5):
            by = 0.38 + j * 0.115
            c.ellipse(x0 + cw, by, 0.010, 0.009, gold, lift=0.3)
            gloss(c, x0 + cw - 0.003, by + 0.003, 0.005, 0.004, 0, 0.7)
    for k in range(34):                                                                    # nail heads along the top and sides
        t = k / 33.0
        c.ellipse(-0.58 + 1.30 * t, 0.90, 0.007, 0.007, gold, lift=0.3)
    soft_disc(c, -0.2, 0.86, 0.6, 0.12, WHITE, 0.16, 1.2, 0, True)
    # base frame and legs
    _rr(c, -0.68, 0.0, 0.68, 0.11, (0.26, 0.18, 0.12), (0.13, 0.09, 0.06), 0.01)
    for lu in (-0.64, 0.64):
        _rr(c, lu - 0.03, 0.0, lu + 0.03, 0.06, (0.20, 0.14, 0.10), (0.1, 0.07, 0.05), 0.0)
        c.ellipse(lu, 0.01, 0.03, 0.012, gold, lift=0.3)
    # mattress / duvet
    _box3(c, 0.0, 0.09, 1.30, 0.25, 0.70, (0.97, 0.96, 0.93), top=(1.0, 0.99, 0.97), right=(0.82, 0.81, 0.79), r=0.03, lift=0.04, tilt=tl)
    soft_disc(c, 0.0, 0.14, 0.7, 0.05, BLACK, 0.10, 1.2)
    dx, dy = 0.7 * tl[0], 0.7 * tl[1]
    vt = 0.09 + 0.25
    for k in range(-5, 6):                                                                 # quilting on the duvet
        c.line(k * 0.12 - 0.25, 0.11, k * 0.12 + 0.05, 0.31, 0.003, (0.78, 0.77, 0.74), 0.30)
        c.line(k * 0.12 + 0.25, 0.11, k * 0.12 - 0.05, 0.31, 0.003, (0.78, 0.77, 0.74), 0.30)
    # folded throw across the foot
    def tq(t0, t1):
        return [(-0.65 + dx * t0, vt + dy * t0), (0.65 + dx * t0, vt + dy * t0), (0.65 + dx * t1, vt + dy * t1), (-0.65 + dx * t1, vt + dy * t1)]
    _poly(c, [(-0.65, vt + 0.006), (0.65, vt + 0.006), (0.65, vt - 0.15), (-0.65, vt - 0.15)], mix(gold, WHITE, 0.05), scale(gold, 0.66))
    _poly(c, tq(0.04, 0.38), mix(gold, WHITE, 0.16), scale(gold, 0.92))
    for t in (0.10, 0.22, 0.30):
        _poly(c, tq(t, t + 0.03), mix(gold, WHITE, 0.55), None, 0.6)
    for k in range(18):                                                                    # woven stripes on the throw front
        c.line(-0.62 + k * 0.073, vt - 0.01, -0.62 + k * 0.073, vt - 0.14, 0.004, scale(gold, 0.6), 0.35)
    _poly(c, [(-0.65, vt - 0.15), (0.65, vt - 0.15), (0.65, vt - 0.166), (-0.65, vt - 0.166)], scale(gold, 0.5), None, 0.8)
    # pillows: two big white ones behind, a bolster and two accent cushions in front
    for pu in (-0.30, 0.34):
        pu += 0.05
        pv = vt + dy * 0.66
        soft_disc(c, pu + 0.03, pv - 0.01, 0.32, 0.07, BLACK, 0.30, 1.4)
        _rr(c, pu - 0.25, pv, pu + 0.25, pv + 0.22, (1.0, 1.0, 0.99), (0.86, 0.85, 0.83), 0.10)
        soft_disc(c, pu - 0.06, pv + 0.16, 0.2, 0.05, WHITE, 0.6, 1.2, 0, True)
        c.line(pu - 0.19, pv + 0.035, pu + 0.19, pv + 0.035, 0.006, (0.72, 0.71, 0.69), 0.5)
    for pu, col in ((-0.14, gold), (0.42, mix(acc, WHITE, 0.15))):
        pu += 0.05
        pv = vt + dy * 0.36
        soft_disc(c, pu + 0.02, pv - 0.01, 0.15, 0.04, BLACK, 0.3, 1.4)
        _poly(c, [(pu - 0.13, pv + 0.02), (pu + 0.13, pv), (pu + 0.14, pv + 0.18), (pu - 0.12, pv + 0.20)], mix(col, WHITE, 0.1), scale(col, 0.72))
        c.line(pu - 0.09, pv + 0.18, pu + 0.09, pv + 0.04, 0.009, mix(col, WHITE, 0.55), 0.5)
        c.line(pu - 0.10, pv + 0.04, pu + 0.10, pv + 0.17, 0.005, scale(col, 0.55), 0.5)
    _rr(c, 0.10, vt + dy * 0.18, 0.30, vt + dy * 0.18 + 0.065, mix(gold, WHITE, 0.2), scale(gold, 0.7), 0.03)     # bolster
    gloss(c, -0.4, 0.40, 0.3, 0.03, 0, 0.12)


@sprop("learn_hotel_bench", aspect=4.2, fill=0.9)
def learn_hotel_bench(c, color):
    """Upholstered bench at the foot of the bed: gold legs, a folded towel and a tray."""
    cl = color or (0.17, 0.33, 0.38)
    ao(c, 0.0, 0.0, 1.9, 0.30)
    for lu in (-0.88, 0.88):
        for off in (0.0, 0.18):
            _rr(c, lu - 0.03 + off * 0.5, 0.0, lu + 0.03 + off * 0.5, 0.34, (0.95, 0.78, 0.40), (0.55, 0.40, 0.16), 0.01)
    _box3(c, 0.0, 0.30, 2.0, 0.46, 0.40, cl, top=mix(cl, WHITE, 0.22), r=0.06, tilt=(0.30, 0.34))
    for k in range(-4, 5):
        c.line(k * 0.22, 0.34, k * 0.22, 0.72, 0.012, scale(cl, 0.55), 0.35)
    _poly(c, [(-0.95, 0.76), (0.95, 0.76), (0.95 + 0.12, 0.76 + 0.13), (-0.95 + 0.12, 0.76 + 0.13)], mix(cl, WHITE, 0.30), scale(cl, 0.9))
    _rr(c, -0.55, 0.80, -0.15, 0.93, (0.98, 0.97, 0.94), (0.82, 0.81, 0.78), 0.04)                  # towel stack
    _rr(c, -0.53, 0.93, -0.17, 0.99, (1.0, 0.99, 0.97), (0.86, 0.85, 0.82), 0.03)
    c.line(-0.54, 0.86, -0.16, 0.86, 0.005, (0.75, 0.78, 0.82), 0.5)
    _rr(c, 0.22, 0.80, 0.78, 0.84, (0.60, 0.42, 0.24), (0.38, 0.26, 0.14), 0.01)                   # tray with cup
    c.ellipse(0.42, 0.88, 0.07, 0.03, (0.98, 0.98, 0.98), lift=0.2)
    c.ellipse(0.42, 0.89, 0.05, 0.02, (0.35, 0.20, 0.10), lift=0.0)
    soft_disc(c, -0.4, 0.78, 0.8, 0.07, WHITE, 0.25, 1.2, 0, True)


@sprop("learn_nightstand", aspect=0.62, fill=1.0)
def learn_nightstand(c, color):
    wood = (0.55, 0.38, 0.24)
    ao(c, 0.04, 0.0, 0.6, 0.10)
    for lu in (-0.18, 0.18):
        _rr(c, lu - 0.015, 0.0, lu + 0.015, 0.10, scale(wood, 0.7), scale(wood, 0.4), 0.0)
    _box3(c, 0.0, 0.08, 0.46, 0.34, 0.30, wood, top=mix(wood, WHITE, 0.2), r=0.012)
    _rr(c, -0.19, 0.12, 0.19, 0.20, scale(wood, 0.9), scale(wood, 0.7), 0.01)
    _rr(c, -0.19, 0.23, 0.19, 0.38, scale(wood, 1.0), scale(wood, 0.78), 0.01)
    for v in (0.16, 0.305):
        c.ellipse(0.0, v, 0.022, 0.016, (0.95, 0.8, 0.4), lift=0.3)
        gloss(c, -0.006, v + 0.004, 0.008, 0.005, 0, 0.8)
    # lamp
    lv = 0.51
    _lathe(c, lambda v: 0.055 * (1 - ((v - lv - 0.06) / 0.075) ** 2) ** 0.5 + 0.004 if v > lv else 0.05, lv - 0.01, lv + 0.12, (0.92, 0.88, 0.80), n=8)
    c.rect(0.0, lv + 0.16, 0.012, 0.06, (0.8, 0.65, 0.3), lift=0.2)
    c.glow(0.0, lv + 0.31, 0.7, (1.0, 0.82, 0.5), 0.45)
    _poly(c, [(-0.13, lv + 0.19), (0.13, lv + 0.19), (0.085, lv + 0.38), (-0.085, lv + 0.38)], (1.0, 0.92, 0.72), (0.98, 0.80, 0.50))
    soft_disc(c, 0.0, lv + 0.28, 0.1, 0.10, (1.0, 0.9, 0.6), 0.5, 1.3, 0, True)
    c.ellipse(0.0, lv + 0.19, 0.13, 0.025, (0.95, 0.78, 0.45), lift=0.1, alpha=0.9)


@sprop("learn_bell_keys", aspect=1.9, fill=0.42)
def learn_bell_keys(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.14)
    wood = (0.50, 0.34, 0.22)
    _box3(c, 0.0, 0.0, 0.96, 0.04, 0.36, wood, top=mix(wood, WHITE, 0.18), r=0.008)
    # service bell: base plate, dome, button
    c.ellipse(-0.26, 0.055, 0.15, 0.15 * TILT, (0.55, 0.42, 0.18), lift=0.1)
    c.ellipse(-0.26, 0.075, 0.14, 0.14 * TILT, (0.95, 0.78, 0.35), lift=0.25)
    _lathe(c, lambda v: 0.115 * max(0.0, 1 - ((v - 0.075) / 0.17) ** 2) ** 0.5 + 0.004, 0.075, 0.24, (0.93, 0.74, 0.30), cu=-0.26, n=14, hi=0.5)
    c.rect(-0.26, 0.255, 0.012, 0.03, (0.8, 0.8, 0.82), lift=0.2)
    c.ellipse(-0.26, 0.275, 0.028, 0.02, (0.9, 0.2, 0.18), lift=0.3)
    gloss(c, -0.30, 0.17, 0.02, 0.07, 10, 0.8)
    # key with tag and key card
    c.ellipse(0.12, 0.052, 0.07, 0.025, (0.8, 0.65, 0.3), lift=0.2)
    c.ellipse(0.12, 0.054, 0.045, 0.014, (0.28, 0.2, 0.14), lift=0)
    c.line(0.17, 0.055, 0.33, 0.062, 0.016, (0.86, 0.70, 0.30))
    for k in range(3):
        c.line(0.28 + k * 0.016, 0.062, 0.28 + k * 0.016, 0.075, 0.01, (0.86, 0.70, 0.30))
    _rr(c, -0.03, 0.045, 0.06, 0.12, (0.15, 0.30, 0.45), (0.08, 0.17, 0.28), 0.012)
    c.text("12", 0.015, 0.082, 0.026, (1.0, 0.95, 0.8), 0.3)
    _poly(c, [(0.20, 0.044), (0.40, 0.044), (0.43, 0.075), (0.23, 0.075)], (0.98, 0.97, 0.94), (0.82, 0.8, 0.76))
    c.rect(0.31, 0.058, 0.17, 0.012, (0.1, 0.1, 0.12), lift=0, alpha=0.8)
    c.line(0.24, 0.067, 0.30, 0.067, 0.006, (0.75, 0.6, 0.25))


@sprop("learn_suitcase", aspect=0.76, fill=1.0)
def learn_suitcase(c, color):
    col = color or (0.14, 0.38, 0.46)
    ao(c, 0.04, 0.0, 0.8, 0.12)
    for lu in (-0.22, 0.22):
        c.ellipse(lu, 0.035, 0.035, 0.035, (0.08, 0.08, 0.1), lift=0.1)
    # telescopic handle
    for lu in (-0.15, 0.15):
        c.line(lu, 0.78, lu, 0.97, 0.016, (0.7, 0.72, 0.76))
    _rr(c, -0.20, 0.95, 0.20, 1.0, (0.2, 0.2, 0.22), (0.08, 0.08, 0.1), 0.02)
    # shell with ribs
    _rr(c, -0.31, 0.06, 0.31, 0.80, mix(col, WHITE, 0.14), scale(col, 0.62), 0.06)
    _poly(c, [(0.14, 0.08), (0.30, 0.08), (0.30, 0.78), (0.14, 0.78)], BLACK, None, 0.26)
    _poly(c, [(-0.30, 0.10), (-0.22, 0.10), (-0.22, 0.76), (-0.30, 0.76)], WHITE, None, 0.20)
    for k in range(6):
        u = -0.20 + k * 0.08
        c.line(u, 0.12, u, 0.74, 0.012, scale(col, 0.7), 0.7)
        c.line(u - 0.006, 0.12, u - 0.006, 0.74, 0.004, mix(col, WHITE, 0.35), 0.6)
    for (uu, vv) in ((-0.30, 0.07), (0.30, 0.07), (-0.30, 0.79), (0.30, 0.79)):
        c.ellipse(uu, vv, 0.035, 0.035, (0.75, 0.62, 0.30), lift=0.3)
    _rr(c, -0.33, 0.40, 0.33, 0.44, (0.80, 0.66, 0.32), (0.55, 0.42, 0.16), 0.0)
    # luggage tag
    c.line(0.15, 0.80, 0.23, 0.62, 0.006, (0.2, 0.2, 0.2), 0.8)
    _rr(c, 0.18, 0.52, 0.28, 0.64, (0.97, 0.85, 0.45), (0.85, 0.68, 0.25), 0.012)
    gloss(c, -0.18, 0.66, 0.05, 0.18, 6, 0.4)
    # small bag leaning at its side
    _rr(c, 0.34, 0.04, 0.62, 0.34, mix((0.55, 0.38, 0.24), WHITE, 0.1), scale((0.55, 0.38, 0.24), 0.62), 0.04)
    c.line(0.40, 0.34, 0.56, 0.34, 0.01, (0.2, 0.15, 0.1))
    craft.arc(c, 0.48, 0.34, 0.07, 0.07, 0, 180, 0.012, (0.25, 0.18, 0.12), 1.0, steps=8)
    c.line(0.35, 0.16, 0.61, 0.16, 0.004, (0.9, 0.8, 0.6), 0.5)


def _curtain(S, u0, u1, v0, v1, col, dark, sheer=False):
    n = int(round((u1 - u0) / 0.035))
    for i in range(n):
        tone = 1.0 + 0.16 * math.sin(i * 1.7) - (0.15 if i % 2 else 0)
        c_ = scale(col, tone * (0.45 if dark else 1.0))
        S.rect(u0 + (i + 0.5) * (u1 - u0) / n, (v0 + v1) / 2, (u1 - u0) / n + 0.003, v1 - v0, c_, lift=0.0, alpha=0.72 if sheer else 1.0)


def _hotel_rug(S, dk, P):
    """Patterned rug under the bed: border, cream field, gold keyline and a lattice of diamonds (perspective trapezoid)."""
    def trap(inset, v0=0.78, v1=1.26):
        u0a, u1a, u0b, u1b = 0.42 + inset, 1.70 - inset, 0.12 + inset * 1.2, 2.00 - inset * 1.2
        return [(u0a, v0 + inset * 0.3), (u1a, v0 + inset * 0.3), (u1b, v1 - inset * 0.3), (u0b, v1 - inset * 0.3)]
    teal = mix((0.13, 0.30, 0.35), P.accent_dark, 0.15)
    cream = (0.93, 0.88, 0.76)
    k = 0.45 if dk else 1.0
    _spoly(S, trap(0.0), scale(teal, 0.9 * k), scale(teal, 0.75 * k), 0.96)
    _spoly(S, trap(0.045), scale(cream, k * 0.96), scale(cream, 0.88 * k), 1.0)
    _spoly(S, trap(0.075), scale(teal, k), scale(teal, 0.85 * k), 0.30)
    _spoly(S, trap(0.095), scale(cream, 1.02 * k), scale(cream, 0.9 * k), 1.0)
    # lattice of diamonds in the field
    gold = scale((0.84, 0.64, 0.28), k)
    rows, cols = 4, 9
    for r in range(rows):
        t = (r + 0.5) / rows
        v = 0.84 + t * 0.36
        spread = 0.52 + t * 0.68
        for q in range(cols):
            u = 1.06 + (q - (cols - 1) / 2.0) * spread / (cols - 1) * 2.0 * (0.9 if q % 2 == 0 else 0.9)
            u += ((r % 2) * 0.5) * spread / (cols - 1) * 2.0
            if abs(u - 1.06) > spread * 1.02:
                continue
            w, h = 0.05 + t * 0.04, 0.018 + t * 0.018
            _spoly(S, [(u, v - h), (u + w, v), (u, v + h), (u - w, v)], gold if (q + r) % 2 == 0 else scale(teal, k), None, 0.40)
    _spoly(S, trap(0.11), scale(gold, 0.9), None, 0.0)


@niche("hotel", "Hotel, resort and stay", subjects=("learn_hotel_bed",),
       strong=("hotel", "resort", "guest house", "guesthouse", "homestay", "lodge", "boutique hotel", "hotel room", "luxury stay", "hotel booking",
               "होटल", "रिसॉर्ट", "गेस्ट हाउस", "होमस्टे", "लॉज", "hotel room booking", "hotel wala", "rooms available"),
       weak=("stay", "rooms", "suite", "booking", "hospitality", "check in", "accommodation", "बुकिंग"),
       accent="#b8860b", mood="warm", group="travel",
       avoid=("hospital", "restaurant", "cafe", "travel agency"))
def hotel(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(9)
    sky_t = (0.10, 0.12, 0.26) if dk else (0.62, 0.80, 0.95)
    sky_b = (0.40, 0.30, 0.42) if dk else (0.95, 0.93, 0.88)
    wall = mix(P.wall_bot, P.accent_light, 0.1)
    teal = mix((0.13, 0.30, 0.35), P.accent_dark, 0.15)
    feat = scale(teal, 0.5) if dk else teal                                     # feature wall behind the bed
    gold = mix(P.accent, (0.95, 0.78, 0.40), 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # striped wallpaper
        for k in range(-30, 70):
            S.rect(k * 0.1, 0.28, 0.04, 0.60, scale(wall, 0.94 if not dk else 1.25), lift=0.0, alpha=0.55)
        # wainscot panels in dark wood
        wain = mix(P.accent_dark, (0.20, 0.13, 0.08), 0.5)
        wain = scale(wain, 0.55) if dk else wain
        S.rect(1.0, 0.54, 14.0, 0.17, wain, lift=0.0)
        for k in range(-8, 24):
            S.rect(k * 0.3, 0.545, 0.25, 0.12, scale(wain, 1.14), lift=0.05, r=0.006, alpha=0.9)
        S.rect(1.0, 0.465, 14.0, 0.012, gold, lift=0.0, alpha=0.8)
        S.rect(1.0, 0.62, 14.0, 0.03, scale(wain, 0.55), lift=0.0)
        # fluted feature wall behind the bed, gold trim, warm cove light
        fu0, fu1 = 0.38, 1.74
        S.rect((fu0 + fu1) / 2, 0.27, fu1 - fu0, 0.72, feat, lift=0.0)
        n = int((fu1 - fu0) / 0.045)
        for i in range(n):
            u = fu0 + (i + 0.5) * (fu1 - fu0) / n
            S.rect(u - 0.011, 0.27, 0.014, 0.70, scale(feat, 1.30), lift=0.0, alpha=0.60)
            S.rect(u + 0.014, 0.27, 0.012, 0.70, scale(feat, 0.55), lift=0.0, alpha=0.55)
        for fu in (fu0, fu1):
            S.rect(fu, 0.27, 0.014, 0.72, gold, lift=0.0)
        S.rect((fu0 + fu1) / 2, 0.612, fu1 - fu0, 0.014, gold, lift=0.0)
        S.rect((fu0 + fu1) / 2, -0.07, fu1 - fu0, 0.03, mix(gold, WHITE, 0.6), lift=0.0)
        S.glow(1.06, -0.04, 1.1, (1.0, 0.82, 0.5), 0.75 if dk else 0.45, 1.5)
        S.glow(1.06, 0.30, 0.9, (1.0, 0.8, 0.5), 0.22 if dk else 0.10, 1.6)
        # large painting above the bed
        S.rect(1.06, 0.27, 0.50, 0.20, gold, lift=0.1)
        S.gradient_rect(0.84, 0.19, 1.28, 0.35, mix(sky_t, P.accent, 0.3), mix(sky_b, P.accent_light, 0.4))
        S.ellipse(1.10, 0.29, 0.12, 0.06, mix(P.accent, (0.9, 0.5, 0.3), 0.3), lift=0.0, alpha=0.8)
        S.ellipse(0.96, 0.32, 0.10, 0.045, scale(teal, 1.2), lift=0.0, alpha=0.7)
        # window with city view (right) and sheer + heavy drapes
        wu = 1.96
        S.gradient_rect(wu - 0.24, 0.04, wu + 0.24, 0.54, sky_t, sky_b)
        for k in range(9):
            hh = 0.06 + rng.random() * 0.14
            S.rect(wu - 0.22 + k * 0.055, 0.54 - hh / 2, 0.045, hh, _tn(P, (0.45, 0.5, 0.6), 0.35), lift=0.0)
            if dk:
                S.circle(wu - 0.22 + k * 0.055, 0.54 - hh * 0.6, 0.008, (1.0, 0.85, 0.5), lift=0.0)
        S.glow(wu, 0.28, 0.8, P.light if not dk else (0.6, 0.6, 1.0), 0.40 if not dk else 0.22)
        S.rect(wu, 0.29, 0.012, 0.50, (0.95, 0.95, 0.95) if not dk else (0.3, 0.3, 0.35), lift=0.0)
        _curtain(S, wu - 0.24, wu + 0.24, 0.02, 0.58, (0.98, 0.96, 0.90), dk, sheer=True)
        _curtain(S, wu - 0.46, wu - 0.22, 0.02, 0.60, teal, dk)
        _curtain(S, wu + 0.22, wu + 0.46, 0.02, 0.60, teal, dk)
        S.rect(wu, 0.02, 1.0, 0.02, gold, lift=0.1)
        # bedside pendants and a floor lamp on the left
        for pu in (0.60, 1.52):
            S.pendant(pu, -0.10, 0.28, (1.0, 0.82, 0.5), 0.10)
            S.glow(pu, 0.30, 0.55, (1.0, 0.8, 0.5), 0.5 if dk else 0.22)
        S.rect(0.14, 0.45, 0.016, 0.34, (0.55, 0.42, 0.22), lift=0.0)
        S.poly([(0.07, 0.30), (0.21, 0.30), (0.18, 0.22), (0.10, 0.22)], (1.0, 0.9, 0.7), 0.95)
        S.glow(0.14, 0.27, 0.55, (1.0, 0.82, 0.5), 0.55 if dk else 0.28)
        S.bokeh(7, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.85, 0.55)], 0.01, 0.035, 0.18)
        S.floor(0.62, mix(P.floor_top, P.accent_dark, 0.18), mix(P.floor_bot, P.accent_dark, 0.18))
    # walnut floor with real planks, a reflection of the cove light and light pools
    fl = mix(P.floor_top, P.accent_dark, 0.18)
    S.wood(-0.9, 0.62, 3.0, 1.40, fl if not dk else scale(fl, 0.9), plank=0.065, grain=0.45)
    S.rect(1.0, 0.62, 14.0, 0.03, scale(wain, 0.5), lift=0.0, alpha=0.9)
    _pool(S, 1.06, 0.80, 1.5, 0.16, (1.0, 0.85, 0.6), 0.30 if not dk else 0.45)
    S.soft(1.55, 0.95, 0.30, 0.10, (1.0, 0.8, 0.5), 0.26 if dk else 0.14, 1.3, add=True)
    _hotel_rug(S, dk, P)
    S.put("learn_nightstand", 1.55, 0.86, 0.27, shadow_w=0.25)
    S.put("learn_hotel_bed", 1.06, 0.93, 0.50, color=mix((0.17, 0.33, 0.38), P.accent_dark, 0.12), subject=True, shadow_w=1.2)
    S.put("learn_hotel_bench", 1.06, 1.03, 0.10, color=mix((0.17, 0.33, 0.38), P.accent_dark, 0.12), shadow_w=0.5)
    S.put("learn_suitcase", 0.64, 1.02, 0.30, color=mix((0.52, 0.12, 0.17), P.accent_dark, 0.10), shadow_w=0.3)
    S.put("learn_bell_keys", 1.40, 1.06, 0.10, shadow_w=0.3)
    S.focus("detail", 1.06, 0.70)
    with S.near(blur=18):
        S.soft(0.4, 1.05, 0.28, 0.10, (1.0, 0.8, 0.5), 0.25, 1.2, add=True)
        for k, (du, dv, rr) in enumerate(((0.0, 0.0, 0.07), (0.07, -0.05, 0.06), (-0.06, -0.04, 0.05))):          # out-of-focus plant leaves
            S.ellipse(1.80 + du, 1.06 + dv, rr * 0.6, rr * 1.8, _tn(P, (0.20, 0.42, 0.25), 0.4), angle=(k - 1) * 28, lift=0.1)
        S.ellipse(1.77, 1.10, 0.09, 0.05, scale(P.accent, 0.8), lift=0.1)


# ====================================================================================== taxi
@sprop("learn_taxi", aspect=3.15, fill=1.17)
def learn_taxi(c, color):
    body = mix(color or (0.99, 0.82, 0.10), (1.0, 0.92, 0.25), 0.5)
    _car(c, "sedan", body, caliper=(0.15, 0.15, 0.17), sheen=1.2)
    # black-and-white checker band and black door cut lines
    sq = 0.05
    n = int((1.28 + 1.38) / sq)
    for j in range(2):
        for i in range(n):
            u = -1.38 + i * sq
            col = (0.06, 0.06, 0.07) if (i + j) % 2 == 0 else (0.97, 0.97, 0.97)
            _rr(c, u, 0.505 + j * 0.045, u + sq, 0.55 + j * 0.045, col, scale(col, 0.88), 0.0)
    # roof sign
    _rr(c, -0.29, 0.94, 0.09, 1.07, (0.99, 0.97, 0.80), (0.92, 0.88, 0.60), 0.03)
    _rr(c, -0.29, 0.94, 0.09, 0.96, (0.2, 0.2, 0.2), (0.1, 0.1, 0.1), 0.0)
    c.text("TAXI", -0.10, 1.01, 0.058, (0.08, 0.08, 0.1), 0.28)
    soft_disc(c, 0.0, 0.42, 1.55, 0.20, (1.0, 0.82, 0.12), 0.5, 0.55, 0, True)
    c.glow(-0.10, 1.01, 0.4, (1.0, 0.95, 0.6), 0.40)
    gloss(c, -0.2, 1.05, 0.08, 0.012, 0, 0.6)


@sprop("learn_phone_map", aspect=0.52, fill=1.0)
def learn_phone_map(c, color):
    acc = color or (0.99, 0.82, 0.10)
    ao(c, 0.03, 0.0, 0.5, 0.08)
    for s in (-1, 1):
        c.line(s * 0.10, 0.04, s * 0.18, 0.0, 0.02, (0.12, 0.12, 0.14))
    _rr(c, -0.26, 0.04, 0.26, 1.0, (0.20, 0.20, 0.23), (0.06, 0.06, 0.08), 0.06)
    _rr(c, -0.245, 0.055, 0.245, 0.985, (0.92, 0.94, 0.90), (0.86, 0.90, 0.85), 0.05)
    # map: park, water, roads
    _poly(c, [(-0.24, 0.30), (-0.05, 0.38), (-0.08, 0.55), (-0.24, 0.52)], (0.72, 0.88, 0.68), None)
    _poly(c, [(0.10, 0.62), (0.24, 0.58), (0.24, 0.86), (0.08, 0.80)], (0.70, 0.84, 0.96), None)
    for (a, b, w) in (((-0.24, 0.72), (0.24, 0.78), 0.035), ((-0.05, 0.06), (0.05, 0.98), 0.03), ((-0.24, 0.42), (0.24, 0.50), 0.025), ((-0.24, 0.20), (0.24, 0.26), 0.02)):
        c.line(a[0], a[1], b[0], b[1], w + 0.008, (0.78, 0.78, 0.76), 0.9)
        c.line(a[0], a[1], b[0], b[1], w, WHITE)
    # route and pins
    route = [(-0.15, 0.30), (-0.14, 0.50), (0.0, 0.52), (0.02, 0.74), (0.14, 0.76)]
    for p, q in zip(route, route[1:]):
        c.line(p[0], p[1], q[0], q[1], 0.038, (0.10, 0.14, 0.25))
    for p, q in zip(route, route[1:]):
        c.line(p[0], p[1], q[0], q[1], 0.024, (0.25, 0.50, 0.95))
    c.ellipse(-0.15, 0.30, 0.03, 0.03, WHITE, lift=0)
    c.ellipse(-0.15, 0.30, 0.018, 0.018, (0.25, 0.50, 0.95), lift=0)
    px_, py_ = 0.14, 0.78
    c.ellipse(px_, py_ - 0.01, 0.034, 0.012, BLACK, alpha=0.35, lift=0)
    _poly(c, [(px_ - 0.04, py_ + 0.06), (px_ + 0.04, py_ + 0.06), (px_, py_ - 0.005)], (0.88, 0.16, 0.16), (0.70, 0.08, 0.08))
    c.ellipse(px_, py_ + 0.075, 0.048, 0.048, (0.92, 0.2, 0.18), lift=0.25)
    c.ellipse(px_, py_ + 0.075, 0.02, 0.02, WHITE, lift=0)
    # search bar and bottom card
    _rr(c, -0.21, 0.88, 0.21, 0.95, WHITE, (0.94, 0.94, 0.94), 0.03)
    c.line(-0.17, 0.915, 0.06, 0.915, 0.012, (0.65, 0.65, 0.68), 0.9)
    _rr(c, -0.245, 0.055, 0.245, 0.24, WHITE, (0.95, 0.95, 0.95), 0.03)
    _rr(c, -0.20, 0.10, -0.08, 0.19, acc, scale(acc, 0.85), 0.02)
    c.rect(-0.14, 0.145, 0.07, 0.02, (0.1, 0.1, 0.1), lift=0)
    c.line(-0.03, 0.165, 0.18, 0.165, 0.014, (0.35, 0.35, 0.38), 0.9)
    c.line(-0.03, 0.13, 0.12, 0.13, 0.01, (0.65, 0.65, 0.68), 0.9)
    c.ellipse(0.0, 0.975, 0.02, 0.008, (0.05, 0.05, 0.06), lift=0)
    c.glow(0.0, 0.5, 0.9, (0.9, 0.95, 1.0), 0.14)
    _poly(c, [(-0.23, 0.97), (-0.10, 0.97), (-0.16, 0.5), (-0.23, 0.5)], WHITE, None, 0.12)


@niche("taxi", "Cab and taxi service", subjects=("learn_taxi",),
       strong=("taxi service", "cab booking", "car rental", "airport taxi", "outstation cabs", "cab service", "taxi booking", "outstation taxi",
               "टैक्सी", "कैब", "टैक्सी सर्विस", "कैब बुकिंग", "taxi wala", "cab wala", "car on rent", "किराये की गाड़ी"),
       weak=("taxi", "cab", "ride", "airport transfer", "chauffeur", "pickup", "drop", "ओला", "उबर"),
       accent="#fdd835", mood="light", group="travel",
       avoid=("driving school", "car wash", "car repair", "showroom"))
def taxi(S):
    P = S.pal
    dk = _dk(P)
    sk_t, sk_b = _sky(P)
    rng = random.Random(21)
    asph = _tn(P, (0.30, 0.30, 0.33), 0.5)
    with S.far():
        S.wall(sk_t, sk_b, 0.66)
        S.glow(0.3, 0.2, 0.7, (1.0, 0.9, 0.7) if not dk else (0.7, 0.6, 1.0), 0.30)
        for k in range(18):                                                                 # skyline, two depths
            u = -0.5 + k * 0.15
            hh = 0.22 + rng.random() * 0.32
            col = _tn(P, mix((0.62, 0.66, 0.74), P.accent_light, 0.15 + 0.1 * (k % 3)), 0.30)
            S.rect(u, 0.64 - hh / 2, 0.14, hh, col, lift=0.05)
            for r in range(int(hh / 0.05)):
                for cc in range(3):
                    if rng.random() < (0.55 if dk else 0.30):
                        S.rect(u - 0.04 + cc * 0.04, 0.64 - 0.04 - r * 0.05, 0.022, 0.026, (1.0, 0.85, 0.5) if dk else mix(col, WHITE, 0.4), lift=0.0, alpha=0.9)
        S.rect(1.0, 0.655, 14.0, 0.05, _tn(P, (0.72, 0.72, 0.72), 0.4), lift=0.0)          # pavement
        S.rect(1.0, 0.68, 14.0, 0.012, _tn(P, (0.5, 0.5, 0.5), 0.4), lift=0.0)
        for u in (0.25, 1.55):                                                               # street lamps and a traffic light
            S.rect(u, 0.38, 0.012, 0.58, _tn(P, (0.25, 0.27, 0.3), 0.5), lift=0.0)
            S.glow(u + 0.04, 0.10, 0.45, (1.0, 0.88, 0.6), 0.55 if dk else 0.25)
            S.rect(u + 0.025, 0.10, 0.06, 0.012, _tn(P, (0.25, 0.27, 0.3), 0.5), lift=0.0)
        S.rect(1.95, 0.40, 0.012, 0.5, _tn(P, (0.2, 0.2, 0.22), 0.5), lift=0.0)
        S.rect(1.95, 0.20, 0.05, 0.13, (0.1, 0.1, 0.12), r=0.01, lift=0.0)
        for k, col in enumerate(((1.0, 0.25, 0.2), (1.0, 0.8, 0.2), (0.3, 1.0, 0.5))):
            S.circle(1.95, 0.16 + k * 0.04, 0.014, col if k == 2 else scale(col, 0.45), lift=0.0)
        S.glow(1.95, 0.24, 0.3, (0.3, 1.0, 0.5), 0.5)
        S.bokeh(10, 0.0, 0.3, 2.0, 0.62, [(1.0, 0.8, 0.4), (1.0, 0.4, 0.3), (0.9, 0.95, 1.0)], 0.01, 0.03, 0.35 if dk else 0.22)
        S.put("learn_taxi", 0.12, 0.76, 0.17, color=P.accent, shadow=False, framed=False)
        S.put("learn_taxi", 1.92, 0.76, 0.17, color=P.accent, shadow=False, framed=False)
        S.floor(0.70, asph, scale(asph, 0.66))
        S.soft(1.1, 0.86, 1.3, 0.22, P.light, 0.26 if not dk else 0.5, 1.4, add=True)
    # road markings: edge line, dashed centre, zebra crossing, wet-look reflections in the dark
    S.rect(1.0, 0.72, 14.0, 0.008, _tn(P, WHITE, 0.65), alpha=0.85, lift=0.0)
    for k in range(-8, 14):
        u = 1.0 + k * 0.40
        _spoly(S, [(u, 1.045), (u + 0.24, 1.045), (u + 0.26, 1.085), (u - 0.02, 1.085)], _tn(P, WHITE, 0.65), None, 0.85)
    for k in range(8):
        u = 0.30 + k * 0.075
        _spoly(S, [(u, 0.74), (u + 0.045, 0.74), (u + 0.05 - 0.04, 0.96), (u - 0.0 - 0.04, 0.96)], _tn(P, WHITE, 0.65), None, 0.55)
    S.put("learn_taxi", 1.16, 0.89, 0.30, color=P.accent, subject=True, shadow_w=0.85)
    S.put("learn_phone_map", 0.58, 1.03, 0.34, color=P.accent, shadow_w=0.3)
    S.put("learn_cone", 1.64, 1.0, 0.10, shadow_w=0.15, framed=False)
    S.focus("detail", 1.16, 0.74)
    with S.near(blur=18):
        S.soft(0.3, 1.05, 0.3, 0.10, P.accent_light, 0.22, 1.2, add=True)
        S.circle(1.85, 1.08, 0.08, mix(P.accent, WHITE, 0.2) if not dk else scale(P.accent, 0.5), lift=0.1)


# ====================================================================================== gaming zone
RGB = [(0.65, 0.30, 1.0), (0.30, 0.50, 1.0), (0.15, 0.90, 0.95), (1.0, 0.30, 0.75)]


def _fan(c, u, v, r, col, rng):
    c.ellipse(u, v, r * 1.05, r * 1.05, (0.03, 0.03, 0.04), lift=0)
    c.glow(u, v, r * 2.0, col, 0.55)
    craft.arc(c, u, v, r * 0.95, r * 0.95, 0, 360, r * 0.14, col, 0.95, steps=20)
    c.ellipse(u, v, r * 0.80, r * 0.80, (0.04, 0.04, 0.06), lift=0)
    for k in range(7):
        a = math.radians(k * 360 / 7 + 10)
        c.line(u + math.cos(a) * r * 0.2, v + math.sin(a) * r * 0.2, u + math.cos(a + 0.5) * r * 0.74, v + math.sin(a + 0.5) * r * 0.74, r * 0.20,
               mix((0.12, 0.12, 0.16), col, 0.25))
    c.ellipse(u, v, r * 0.2, r * 0.2, (0.08, 0.08, 0.1), lift=0.3)
    c.ellipse(u, v, r * 0.11, r * 0.11, col, lift=0)


@sprop("learn_gaming_pc", aspect=0.56, fill=1.0)
def learn_gaming_pc(c, color):
    rng = c.rng
    col = color or RGB[0]
    ao(c, 0.08, 0.0, 0.7, 0.12)
    c.glow(0.0, 0.5, 0.80, col, 0.26)
    for lu in (-0.18, 0.18):
        _rr(c, lu - 0.04, 0.0, lu + 0.04, 0.04, (0.08, 0.08, 0.1), (0.03, 0.03, 0.04), 0.0)
    _box3(c, 0.0, 0.035, 0.50, 0.95, 0.40, (0.08, 0.08, 0.10), top=(0.16, 0.16, 0.20), right=(0.04, 0.04, 0.05), r=0.015, tilt=(0.20, 0.22))
    # tempered glass window
    _rr(c, -0.22, 0.10, 0.22, 0.95, (0.05, 0.06, 0.10), (0.02, 0.02, 0.04), 0.012)
    _poly(c, [(-0.22, 0.95), (0.22, 0.95), (0.22, 0.30), (-0.22, 0.60)], WHITE, None, 0.07)
    # PSU shroud, motherboard, RAM sticks, tubing
    _rr(c, -0.22, 0.10, 0.22, 0.24, (0.10, 0.10, 0.13), (0.05, 0.05, 0.07), 0.0)
    c.line(-0.18, 0.17, 0.0, 0.17, 0.008, col, 0.9)
    c.text("RGB", 0.12, 0.17, 0.03, mix(col, WHITE, 0.4), 0.25)
    _rr(c, -0.05, 0.28, 0.20, 0.90, (0.09, 0.10, 0.14), (0.05, 0.05, 0.08), 0.01)
    for k in range(4):
        c.rect(0.15 - k * 0.022, 0.82, 0.012, 0.13, mix(RGB[k % 4], WHITE, 0.2), lift=0.1)
        c.glow(0.15 - k * 0.022, 0.82, 0.07, RGB[k % 4], 0.45)
    _rr(c, -0.02, 0.60, 0.10, 0.76, (0.16, 0.17, 0.22), (0.06, 0.06, 0.09), 0.01)                  # CPU cooler block
    c.ellipse(0.04, 0.68, 0.04, 0.04, col, lift=0)
    c.glow(0.04, 0.68, 0.15, col, 0.5)
    # GPU with two fans
    _rr(c, -0.20, 0.36, 0.20, 0.52, (0.20, 0.21, 0.26), (0.07, 0.07, 0.10), 0.01)
    _fan(c, -0.09, 0.44, 0.058, RGB[2], rng)
    _fan(c, 0.09, 0.44, 0.058, RGB[2], rng)
    c.line(-0.2, 0.525, 0.2, 0.525, 0.006, RGB[3], 0.95)
    c.glow(0.0, 0.525, 0.25, RGB[3], 0.35)
    # side fan column
    for k in range(3):
        _fan(c, -0.145, 0.88 - k * 0.19 + 0.0, 0.07, RGB[k % 3], rng)
    # liquid tubing
    for k in range(3):
        craft.arc(c, 0.10, 0.74, 0.07 + k * 0.012, 0.12, 270, 450, 0.008, mix(col, WHITE, 0.2 * k), 0.85, steps=10)
    # glass reflection
    _poly(c, [(-0.22, 0.95), (-0.10, 0.95), (0.12, 0.10), (0.0, 0.10)], WHITE, None, 0.08)
    c.line(-0.22, 0.10, -0.22, 0.95, 0.005, mix(col, WHITE, 0.4), 0.7)
    c.glow(0.0, 0.5, 0.6, col, 0.20)


@sprop("learn_monitor", aspect=1.85, fill=0.60)
def learn_monitor(c, color):
    col = color or RGB[0]
    ao(c, 0.0, 0.0, 0.9, 0.12)
    c.glow(0.0, 0.40, 0.62, col, 0.42)
    # stand
    c.ellipse(0.0, 0.025, 0.20, 0.05, (0.10, 0.10, 0.12), lift=0.3)
    _hfill(c, -0.035, 0.03, 0.035, 0.22, _cyl_fn((0.45, 0.46, 0.5), (0.08, 0.08, 0.1), 0.3), strips=4)
    _rr(c, -0.50, 0.19, 0.50, 0.62, (0.12, 0.12, 0.15), (0.03, 0.03, 0.05), 0.02)
    # screen: dusk sky, sun, mountains, HUD
    x0, x1, y0, y1 = -0.485, 0.485, 0.205, 0.605
    _rr(c, x0, y0, x1, y1, (0.28, 0.12, 0.55), (0.98, 0.45, 0.35), 0.01)
    c.ellipse(0.12, 0.40, 0.09, 0.09, (1.0, 0.85, 0.5), lift=0)
    c.glow(0.12, 0.40, 0.3, (1.0, 0.7, 0.4), 0.5)
    _poly(c, [(x0, y0), (x0, 0.36), (-0.30, 0.45), (-0.15, 0.34), (0.0, 0.42), (0.20, 0.30), (0.38, 0.40), (x1, 0.33), (x1, y0)], (0.10, 0.06, 0.20), (0.05, 0.03, 0.10))
    _poly(c, [(x0, y0), (x0, 0.28), (-0.2, 0.30), (0.1, 0.25), (0.35, 0.29), (x1, 0.27), (x1, y0)], (0.04, 0.02, 0.08), None)
    # character silhouette with a glowing sword
    c.ellipse(-0.14, 0.33, 0.016, 0.02, (0.02, 0.01, 0.04), lift=0)
    c.rect(-0.14, 0.29, 0.03, 0.06, (0.02, 0.01, 0.04), lift=0)
    c.line(-0.12, 0.33, -0.05, 0.46, 0.008, (0.4, 1.0, 1.0))
    c.glow(-0.08, 0.40, 0.1, (0.3, 1.0, 1.0), 0.6)
    _rr(c, -0.46, 0.55, -0.22, 0.575, (0.2, 0.05, 0.1), (0.1, 0.02, 0.05), 0.0)
    _rr(c, -0.46, 0.55, -0.31, 0.575, (0.2, 0.95, 0.4), (0.1, 0.6, 0.2), 0.0)
    c.ellipse(0.40, 0.52, 0.045, 0.045, (0.05, 0.08, 0.12), lift=0, alpha=0.8)
    c.line(0.0, 0.44, 0.0, 0.47, 0.004, WHITE, 0.8)
    c.line(-0.015, 0.455, 0.015, 0.455, 0.004, WHITE, 0.8)
    _poly(c, [(-0.485, 0.605), (-0.20, 0.605), (-0.40, 0.205), (-0.485, 0.205)], WHITE, None, 0.07)
    c.line(-0.50, 0.19, 0.50, 0.19, 0.008, col, 0.9)


@sprop("learn_console", aspect=0.46, fill=1.0)
def learn_console(c, color):
    """Upright console: black core, two sculpted white wings, blue LED seams, vents, disc slot and a round stand."""
    blue = (0.30, 0.55, 1.0)
    ao(c, 0.04, 0.0, 0.58, 0.12)
    c.glow(0.0, 0.5, 0.65, blue, 0.20)
    c.ellipse(0.0, 0.028, 0.26, 0.055, (0.07, 0.07, 0.09), lift=0.1)
    c.ellipse(0.0, 0.040, 0.24, 0.045, (0.88, 0.90, 0.94), lift=0.25)
    _rr(c, -0.155, 0.05, 0.155, 0.985, (0.10, 0.10, 0.14), (0.02, 0.02, 0.04), 0.05)
    c.glow(0.0, 0.5, 0.40, blue, 0.30)
    for s_ in (-1, 1):                                                                 # sculpted wings: bulge in the middle, taper to the ends
        outer, inner = [], []
        for k in range(13):
            t = k / 12.0
            v = 0.045 + 0.945 * t
            bulge = math.sin(math.pi * t) ** 0.75
            outer.append((s_ * (0.150 + 0.062 * bulge), v))
            inner.append((s_ * (0.085 + 0.008 * math.sin(math.pi * t)), v))
        pts = outer + inner[::-1]
        _poly(c, pts, (0.99, 0.99, 1.0), (0.80, 0.82, 0.88))
        sh = [(s_ * (0.150 + 0.062 * math.sin(math.pi * k / 12.0) ** 0.75) * 0.99, 0.045 + 0.945 * k / 12.0) for k in range(13)]
        if s_ > 0:                                                                     # right wing is in shade, left wing catches the key light
            _poly(c, sh + [(0.08, 0.99), (0.08, 0.045)], BLACK, None, 0.20)
        else:
            _poly(c, [(-0.205, 0.30), (-0.165, 0.30), (-0.165, 0.85), (-0.205, 0.85)], WHITE, None, 0.32)
        c.line(s_ * 0.092, 0.07, s_ * 0.092, 0.97, 0.014, blue, 0.95)                    # LED seam between core and wing
        c.line(s_ * 0.147, 0.07, s_ * 0.147, 0.97, 0.004, (0.55, 0.60, 0.70), 0.7)
    for k in range(9):                                                                 # vent ribs on the core
        c.line(-0.05, 0.10 + k * 0.018, 0.05, 0.10 + k * 0.018, 0.005, (0.30, 0.32, 0.40), 0.9)
    _rr(c, -0.07, 0.69, 0.07, 0.715, (0.01, 0.01, 0.02), (0.0, 0.0, 0.0), 0.012)         # disc slot
    c.line(-0.06, 0.70, 0.06, 0.70, 0.003, (0.5, 0.6, 0.8), 0.6)
    c.ellipse(-0.03, 0.80, 0.012, 0.012, (0.35, 0.80, 1.0), lift=0)                      # status LEDs
    c.glow(-0.03, 0.80, 0.07, (0.3, 0.8, 1.0), 0.5)
    c.ellipse(0.025, 0.80, 0.010, 0.010, (0.9, 0.9, 0.95), lift=0.2)
    gloss(c, -0.19, 0.72, 0.02, 0.17, 4, 0.45)
    c.ellipse(0.0, 0.985, 0.10, 0.012, (0.70, 0.72, 0.80), lift=0.2, alpha=0.8)


@sprop("learn_controller", aspect=1.6, fill=0.36)
def learn_controller(c, color):
    col = color or RGB[1]
    body = (0.14, 0.15, 0.19)
    ao(c, 0.02, 0.0, 1.0, 0.12)
    k = 0.62
    for s in (-1, 1):                                                                 # grips
        c.ellipse(s * 0.36, 0.10, 0.16, 0.20 * k + 0.05, scale(body, 0.6), lift=0)
        c.ellipse(s * 0.36, 0.115, 0.155, 0.185 * k + 0.05, body, lift=0.25)
    c.ellipse(0.0, 0.21, 0.42, 0.14, scale(body, 0.6), lift=0)
    c.ellipse(0.0, 0.225, 0.41, 0.135, mix(body, WHITE, 0.05), lift=0.25)
    soft_disc(c, -0.1, 0.28, 0.35, 0.05, WHITE, 0.25, 1.2, 0, True)
    c.line(-0.14, 0.32, 0.14, 0.32, 0.014, col, 0.95)
    c.glow(0.0, 0.32, 0.3, col, 0.35)
    for sx in (-0.15, 0.15):                                                          # sticks
        c.ellipse(sx, 0.185, 0.07, 0.045, (0.03, 0.03, 0.04), lift=0)
        c.ellipse(sx, 0.205, 0.058, 0.036, (0.20, 0.21, 0.25), lift=0.3)
        c.ellipse(sx, 0.212, 0.04, 0.022, (0.12, 0.12, 0.15), lift=0.1)
    c.rect(-0.30, 0.255, 0.05, 0.018, (0.8, 0.8, 0.85), lift=0.2)                     # d-pad
    c.rect(-0.30, 0.255, 0.018, 0.045, (0.8, 0.8, 0.85), lift=0.2)
    for (du, dv, cc) in ((0.0, 0.04, (0.3, 0.8, 0.4)), (0.05, 0.0, (0.95, 0.3, 0.3)), (-0.05, 0.0, (0.3, 0.5, 1.0)), (0.0, -0.035, (0.95, 0.8, 0.2))):
        c.ellipse(0.30 + du, 0.255 + dv, 0.016, 0.012, cc, lift=0.3)
    c.ellipse(-0.30, 0.30, 0.1, 0.02, scale(body, 1.3), lift=0.2)
    c.ellipse(0.30, 0.30, 0.1, 0.02, scale(body, 1.3), lift=0.2)


@sprop("learn_headset", aspect=0.95, fill=1.0)
def learn_headset(c, color):
    col = color or RGB[3]
    ao(c, 0.0, 0.0, 0.5, 0.08)
    _rr(c, -0.17, 0.0, 0.17, 0.035, (0.12, 0.12, 0.15), (0.04, 0.04, 0.06), 0.01)
    c.line(0.0, 0.03, 0.0, 0.34, 0.026, (0.1, 0.1, 0.12))
    craft.arc(c, 0.0, 0.34, 0.12, 0.05, 0, 180, 0.03, (0.1, 0.1, 0.12), 1.0, steps=8)
    craft.arc(c, 0.0, 0.52, 0.40, 0.46, 12, 168, 0.075, (0.07, 0.07, 0.09), 1.0, steps=22)
    craft.arc(c, 0.0, 0.52, 0.40, 0.46, 12, 168, 0.045, (0.18, 0.18, 0.22), 1.0, steps=22)
    craft.arc(c, 0.0, 0.55, 0.40, 0.47, 70, 150, 0.01, WHITE, 0.4, steps=8)
    for s in (-1, 1):
        cu = s * 0.37
        c.glow(cu, 0.50, 0.3, col, 0.5)
        c.ellipse(cu, 0.50, 0.13, 0.20, (0.07, 0.07, 0.09), lift=0.1)
        c.ellipse(cu, 0.50, 0.105, 0.17, (0.15, 0.15, 0.19), lift=0.3)
        c.ellipse(cu, 0.50, 0.07, 0.12, col, lift=0.0, alpha=0.9)
        c.ellipse(cu, 0.50, 0.055, 0.10, (0.06, 0.06, 0.08), lift=0.0)
        c.ellipse(cu - s * 0.085, 0.58, 0.02, 0.05, WHITE, alpha=0.3, lift=0)
    craft.arc(c, -0.37, 0.28, 0.12, 0.14, 180, 330, 0.012, (0.1, 0.1, 0.12), 1.0, steps=8)
    c.ellipse(-0.27, 0.19, 0.035, 0.022, (0.1, 0.1, 0.12), lift=0.2)


@sprop("learn_kbd_mouse", aspect=3.3, fill=0.30)
def learn_kbd_mouse(c, color):
    u0, v0 = -0.62, 0.0
    ao(c, 0.1, 0.0, 1.9, 0.14)
    k, sk = 0.40, 0.22
    mat = (0.07, 0.07, 0.10)
    _poly(c, [_fq(u0, v0, -0.08, -0.12, k, sk), _fq(u0, v0, 1.6, -0.12, k, sk), _fq(u0, v0, 1.6, 0.56, k, sk), _fq(u0, v0, -0.08, 0.56, k, sk)], mat, scale(mat, 0.6))
    for i in range(24):
        hue = RGB[(i * 4 // 24) % 4]
        t = i / 24.0
        col = mix(RGB[min(3, int(t * 4))], RGB[min(3, int(t * 4) + 1) if int(t * 4) < 3 else 3], (t * 4) % 1)
        a, b = _fq(u0, v0, -0.08 + i * 0.07, -0.12, k, sk), _fq(u0, v0, -0.08 + (i + 1) * 0.07, -0.12, k, sk)
        c.line(a[0], a[1], b[0], b[1], 0.012, col, 0.95)
    c.glow(0.5, 0.06, 1.0, RGB[0], 0.22)
    # keyboard body and keys
    _fbox(c, u0, v0, 0.0, 0.0, 1.05, 0.38, 0.03, (0.07, 0.07, 0.09), (0.03, 0.03, 0.04))
    for r in range(5):
        n = 15 if r != 4 else 9
        for i in range(n):
            x = 0.02 + i * (1.01 / 15) + (0.04 if r == 4 else 0.0)
            y = 0.02 + r * 0.068
            w_ = 0.058 if r != 4 or i != 4 else 0.3
            if r == 4 and i > 4:
                x += 0.24
            t = x / 1.05
            col = mix(RGB[min(3, int(t * 4))], RGB[min(3, int(t * 4) + 1) if int(t * 4) < 3 else 3], (t * 4) % 1)
            q = [_fq(u0, v0, x, y, k, sk), _fq(u0, v0, x + w_, y, k, sk), _fq(u0, v0, x + w_, y + 0.056, k, sk), _fq(u0, v0, x, y + 0.056, k, sk)]
            q = [(a, b + 0.03) for a, b in q]
            _poly(c, q, mix((0.14, 0.14, 0.17), col, 0.18), (0.06, 0.06, 0.08))
            c.line(q[0][0], q[0][1], q[1][0], q[1][1], 0.004, col, 0.9)
    c.line(0.1 * 0 + _fq(u0, v0, 0.0, 0.0, k, sk)[0], 0.04, _fq(u0, v0, 1.05, 0.0, k, sk)[0], 0.04, 0.004, RGB[2], 0.8)
    # mouse
    mu, mv = 1.12, 0.07
    c.ellipse(mu + 0.04, mv, 0.075, 0.035, BLACK, alpha=0.4, lift=0)
    c.ellipse(mu, mv + 0.015, 0.065, 0.045, (0.10, 0.10, 0.13), lift=0.3)
    c.ellipse(mu - 0.01, mv + 0.03, 0.05, 0.028, (0.18, 0.18, 0.22), lift=0.3)
    c.line(mu, mv + 0.04, mu, mv + 0.065, 0.006, RGB[2], 1.0)
    c.glow(mu, mv + 0.015, 0.12, RGB[1], 0.45)
    c.line(mu - 0.05, mv + 0.012, mu + 0.05, mv + 0.012, 0.004, RGB[0], 0.9)


@sprop("learn_can", aspect=0.52, fill=1.0)
def learn_can(c, color):
    """Energy drink can with a neon band and a condensation sheen."""
    col = color or RGB[2]
    ao(c, 0.02, 0.0, 0.5, 0.08)
    _hfill(c, -0.20, 0.03, 0.20, 0.94, _cyl_fn(scale(col, 0.55), scale(col, 0.15), 0.35), strips=9)
    _hfill(c, -0.20, 0.30, 0.20, 0.62, _cyl_fn((0.10, 0.10, 0.13), (0.02, 0.02, 0.03), 0.30), strips=9)
    c.line(-0.20, 0.31, 0.20, 0.31, 0.012, col, 0.95)
    c.line(-0.20, 0.61, 0.20, 0.61, 0.012, col, 0.95)
    c.glow(0.0, 0.46, 0.35, col, 0.22)
    c.text("RUSH", 0.0, 0.46, 0.09, mix(col, WHITE, 0.6), 0.28)
    c.ellipse(0.0, 0.03, 0.20, 0.05, scale(col, 0.18), lift=0)
    c.ellipse(0.0, 0.94, 0.20, 0.05, (0.62, 0.64, 0.70), lift=0.3)
    c.ellipse(0.0, 0.94, 0.15, 0.036, (0.28, 0.29, 0.33), lift=0.2)
    c.ellipse(0.04, 0.945, 0.04, 0.016, (0.80, 0.82, 0.86), lift=0.3)
    gloss(c, -0.12, 0.60, 0.025, 0.30, 4, 0.5)
    for k in range(7):                                                                  # condensation
        c.ellipse((c.rng.random() - 0.5) * 0.32, 0.14 + k * 0.10, 0.008, 0.011, WHITE, alpha=0.35, lift=0)


def _hex(S, u, v, r, col, alpha=1.0):
    S.poly([(u + r * math.cos(math.radians(60 * k + 30)), v + r * math.sin(math.radians(60 * k + 30))) for k in range(6)], col, alpha)


def _desk_weave(S, u0, u1, v0, v1, dk):
    """Carbon-fibre / brushed texture on a desk top: two sets of diagonal hairlines (very cheap Wu lines)."""
    if S.dry:
        return
    span = v1 - v0
    lit = 0.13 if dk else 0.10
    k = u0
    n = 0
    while k < u1 and n < 90:
        _shair(S, k, v0, k + span * 0.9, v1, WHITE, lit)
        _shair(S, k + span * 0.45, v0, k - span * 0.45, v1, BLACK, 0.28)
        k += 0.034
        n += 1


@niche("gaming-zone", "Gaming zone and esports cafe", subjects=("learn_gaming_pc",),
       strong=("gaming zone", "gaming cafe", "esports", "ps5", "video games", "arcade", "gaming lounge", "gaming pc", "esports arena", "game zone",
               "गेमिंग ज़ोन", "गेमिंग जोन", "गेमिंग कैफे", "वीडियो गेम", "ई-स्पोर्ट्स", "गेम ज़ोन", "gaming wala", "ps5 gaming", "playstation"),
       weak=("gaming", "gamer", "console", "rgb", "joystick", "controller", "tournament", "गेमिंग", "गेम"),
       accent="#7c4dff", mood="dark", group="leisure",
       avoid=("play school", "casino"))
def gaming_zone(S):
    P = S.pal
    dk = _dk(P)
    neon = mix(P.accent, WHITE, 0.25)
    DV = 0.745                                                                  # back edge of the desk
    with S.far():
        S.wall(P.wall_top, P.wall_bot, DV)
        # hex acoustic panels with a few lit edges
        rng = random.Random(4)
        r = 0.075
        for i in range(-2, 34):
            for j in range(0, 7):
                u = -0.7 + i * r * 1.74 + (j % 2) * r * 0.87
                v = 0.04 + j * r * 1.5
                lit = rng.random() < 0.18
                base = scale(P.wall_bot, 1.25) if dk else scale(P.wall_bot, 0.96)
                _hex(S, u, v, r * 0.95, mix(base, neon, 0.55) if lit else base, 0.95 if lit else 0.8)
        S.glow(1.05, 0.28, 1.4, P.accent, 0.50 if dk else 0.28, 1.6)
        # neon bars behind the desk, a big blurred neon sign, a lit shelf strip
        S.rect(1.05, 0.50, 1.7, 0.016, neon, lift=0.0)
        S.glow(1.05, 0.50, 1.2, neon, 0.55 if dk else 0.28, 1.6)
        S.rect(0.18, 0.26, 0.014, 0.4, RGB[2], lift=0.0)
        S.glow(0.18, 0.26, 0.4, RGB[2], 0.45 if dk else 0.2)
        S.rect(1.95, 0.26, 0.014, 0.4, RGB[3], lift=0.0)
        S.glow(1.95, 0.26, 0.4, RGB[3], 0.45 if dk else 0.2)
        for w_, col in ((0.30, scale(P.accent, 0.8)), (0.12, mix(neon, WHITE, 0.4))):
            S.text("GAME ON", 0.80, 0.29, 0.10, col, w_)
        S.glow(0.80, 0.29, 0.6, P.accent, 0.5 if dk else 0.25)
        S.bokeh(10, 0.0, 0.1, 2.0, 0.60, [neon, RGB[2], RGB[3]], 0.01, 0.035, 0.35 if dk else 0.2)
        dt = (0.07, 0.07, 0.10) if dk else mix((0.30, 0.31, 0.36), P.wall_bot, 0.3)
        S.floor(DV, dt, scale(dt, 0.6))
    # the desk: glossy dark top with weave, a lit back edge, an RGB under-glow and the screen reflected in it
    dtop = (0.085, 0.08, 0.115) if dk else mix((0.30, 0.31, 0.37), P.wall_bot, 0.25)
    EV = 1.19
    S.floor(DV, scale(dtop, 1.7), scale(dtop, 0.35))
    _desk_weave(S, 0.0, 2.2, DV + 0.01, EV, dk)
    hot = 0.55 if dk else 0.28
    _spoly(S, [(-4, DV), (6, DV), (6, DV + 0.18), (-4, DV + 0.18)], neon, neon, hot, 0.0)                 # rim light on the back edge
    S.rect(1.0, DV + 0.003, 14.0, 0.010, scale(neon, 0.9), lift=0.0, alpha=0.9)
    _spoly(S, [(0.80, DV + 0.02), (1.28, DV + 0.02), (1.80, EV), (0.26, EV)], P.accent, P.accent, 0.30 if dk else 0.14, 0.02)   # light fanning over the desk
    # XXL desk mat with a stitched edge and angular neon lines
    mat = (0.035, 0.035, 0.06) if dk else (0.16, 0.17, 0.22)
    _spoly(S, _rrpts(0.43, 0.895, 1.61, 1.125, 0.014, 3), scale(mat, 1.5), scale(mat, 0.8), 1.0)
    _spoly(S, _rrpts(0.45, 0.91, 1.59, 1.11, 0.012, 3), scale(mat, 0.9), scale(mat, 0.7), 0.55)
    for k in range(-5, 6):
        S.line(1.02 + k * 0.10, 1.105, 1.02 + k * 0.10 + 0.07, 0.915, 0.003, neon, 0.22)
    S.line(0.50, 1.10, 0.86, 1.10, 0.005, RGB[2], 0.85)
    S.line(0.86, 1.10, 0.98, 0.93, 0.005, RGB[2], 0.85)
    S.line(1.56, 0.93, 1.60, 1.09, 0.005, RGB[3], 0.85)
    _spoly(S, [(0.43, 0.893), (1.61, 0.893), (1.61, 0.93), (0.43, 0.93)], mix(neon, WHITE, 0.2), neon, 0.40 if dk else 0.2, 0.0)   # mat back edge catching light
    for u in (0.75, 1.05, 1.45):
        S.soft(u, 0.80, 0.14, 0.14, RGB[(int(u * 5)) % 4], 0.14 if dk else 0.06, 1.3, add=True)
    # reflections of the screen and RGB lights on the glossy top
    _spoly(S, [(0.70, DV + 0.015), (1.34, DV + 0.015), (1.28, 1.02), (0.76, 1.02)], (1.0, 0.55, 0.40), (0.35, 0.20, 0.60), 0.26, 0.02)
    for u, col in ((1.40, RGB[2]), (1.52, RGB[3])):
        S.soft(u, 0.98, 0.03, 0.10, col, 0.30 if dk else 0.12, 1.3, add=True)
    # the front edge of the desk with its under-glow, and the floor below
    _spoly(S, [(-4, EV), (6, EV), (6, EV + 0.04), (-4, EV + 0.04)], scale(dtop, 2.0), scale(dtop, 1.0), 1.0)
    S.rect(1.0, EV + 0.002, 14.0, 0.006, mix(neon, WHITE, 0.35), lift=0.0, alpha=0.95)
    S.floor(EV + 0.04, scale(dtop, 0.5), scale(dtop, 0.2))
    _spoly(S, [(-4, EV + 0.04), (6, EV + 0.04), (6, EV + 0.24), (-4, EV + 0.24)], neon, neon, 0.45 if dk else 0.2, 0.0)
    S.put("learn_console", 0.66, 0.86, 0.30, shadow_w=0.3)
    S.put("learn_monitor", 1.02, 0.84, 0.38, color=P.accent, shadow_w=0.8)
    S.put("learn_gaming_pc", 1.43, 0.90, 0.48, color=mix(P.accent, WHITE, 0.1), subject=True, shadow_w=0.5)
    S.put("learn_kbd_mouse", 1.02, 1.04, 0.14, shadow_w=1.0)
    S.put("learn_controller", 0.66, 1.03, 0.12, color=RGB[1], shadow_w=0.4)
    S.put("learn_headset", 1.40, 1.06, 0.16, color=RGB[3], shadow_w=0.3)
    S.put("learn_can", 0.52, 1.10, 0.12, color=RGB[2], shadow_w=0.1)
    S.focus("detail", 1.43, 0.66)
    with S.near(blur=18):
        S.soft(0.4, 1.06, 0.3, 0.10, P.accent, 0.35 if dk else 0.18, 1.2, add=True)
        S.ellipse(1.85, 1.08, 0.10, 0.06, scale(neon, 0.8), lift=0.1)
