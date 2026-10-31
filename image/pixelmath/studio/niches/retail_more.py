"""More retail / studio niches: fashion boutique, furniture showroom, mobile store, printing studio, tailor, bike showroom, pottery, design studio."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, mix, scale
from .retail_fashion import _chaikin, _fillpoly, _hpoly, _spoly

WOOD = (0.64, 0.43, 0.25)
GOLD = (0.88, 0.70, 0.30)
GOLD_L = (1.0, 0.90, 0.58)
GOLD_D = (0.58, 0.40, 0.12)
CHROME = (0.80, 0.82, 0.86)
DENIM = (0.22, 0.34, 0.56)
SKIN = (0.93, 0.80, 0.68)


# ------------------------------------------------------------------------------------------------ shared helpers
def _pal(color, name, default):
    return getattr(color, name, default) if color is not None and not isinstance(color, tuple) else default


def _dark(S):
    return S.pal.mood == "dark"


def _k(S, dark=0.55):
    return dark if S.pal.mood == "dark" else 1.0


def _sky(dk):
    return dict(sky_top=(0.08, 0.10, 0.24), sky_bot=(0.20, 0.24, 0.40)) if dk else {}


def _glow_floor(S, u, v, a, b, color, alpha=0.2):
    S.soft(u, v, a, b, color, alpha, 1.5, add=True)


def _sym(c, cu, top, half, col, left=None, right=None, k=0.07, smooth=1, alpha=1.0):
    """Symmetric garment from a half profile [(x, depth_below_top)] around the centre cu, shaded left (lit) to right."""
    pts = [(cu + x, top - d) for x, d in half] + [(cu - x, top - d) for x, d in reversed(half)]
    _hpoly(c, pts, left or scale(col, 1.10), right or scale(col, 0.70), k, alpha, 1.0, smooth)


def _dots(c, n, u0, u1, v0, v1, col, r=0.007, alpha=0.9):
    rng = c.rng
    for _ in range(n):
        c.ellipse(rng.uniform(u0, u1), rng.uniform(v0, v1), r, r, col, lift=0, alpha=alpha)


def _stitch(c, p0, p1, n, col, w=0.004, dash=0.45, alpha=0.9):
    """A dashed seam of n stitches between two points."""
    for i in range(n):
        t0, t1 = i / float(n), (i + dash) / float(n)
        c.line(p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0, p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1, w, col, alpha)


def _box3(c, u, v, w, h, d, col, k=1.0, r=0.0):
    """A shaded box seen from the left-front: front face, top face, right side face (base centre u, v)."""
    left, right = scale(col, 1.06 * k), scale(col, 0.80 * k)
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + d, v + h + d * TILT), (u - w / 2 + d, v + h + d * TILT)], scale(col, 1.16 * k), lift=0.04)
    c.poly([(u + w / 2, v), (u + w / 2 + d, v + d * TILT), (u + w / 2 + d, v + h + d * TILT), (u + w / 2, v + h)], scale(col, 0.62 * k), lift=0.04)
    craft.hshade_box(c, u, v + h / 2, w, h, left, right, r=r)


# ================================================================================================ FASHION BOUTIQUE
def _hanger(c, cu, rail_v, top, w=0.12, col=(0.28, 0.20, 0.14)):
    c.line(cu, rail_v + 0.012, cu, top + 0.012, 0.005, (0.78, 0.78, 0.82), 0.95)
    c.line(cu - w, top - 0.02, cu, top + 0.012, 0.007, col, 0.95)
    c.line(cu + w, top - 0.02, cu, top + 0.012, 0.007, col, 0.95)


def _fold_lines(c, cu, top, x0, d0, x1, d1, n, col, alpha=0.22):
    for i in range(n):
        f = (i + 0.5) / n * 2 - 1
        c.line(cu + x0 * f, top - d0, cu + x1 * f, top - d1, 0.006, col, alpha)


def _tube(c, pts, ws, left, right, k=0.06, smooth=1, hi=None, lo=None):
    """A tapered tube (sleeve, limb) along a polyline: half widths `ws` per point, shaded lit-left to dark-right, with a soft highlight and shadow edge."""
    for _ in range(2):                                                                   # round the centre line (open corner cutting), keep the end points
        np_, nw = [pts[0]], [ws[0]]
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            np_ += [(a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25), (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)]
            nw += [ws[i] * 0.75 + ws[i + 1] * 0.25, ws[i] * 0.25 + ws[i + 1] * 0.75]
        np_.append(pts[-1])
        nw.append(ws[-1])
        pts, ws = np_, nw
    n = len(pts)
    ls, rs = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        ls.append((x + nx * ws[i], y + ny * ws[i]))
        rs.append((x - nx * ws[i], y - ny * ws[i]))
    _hpoly(c, ls + rs[::-1], left, right, k, 1.0, 1.0, 0)
    lit_left = ls[0][0] < rs[0][0]
    for col, edge, sh, al in ((hi, ls if lit_left else rs, 0.35, 0.30), (lo, rs if lit_left else ls, 0.70, 0.32)):
        if col is None:
            continue
        inner = [(e[0] * (1 - sh) + q[0] * sh, e[1] * (1 - sh) + q[1] * sh) for e, q in zip(edge, pts)]
        outer = [(e[0] * 0.92 + q[0] * 0.08, e[1] * 0.92 + q[1] * 0.08) for e, q in zip(edge, pts)]
        c.poly(inner + outer[::-1], col, alpha=al, lift=0.0)


def _dress(c, cu, top, L, hem, col, kind, trim=None, dots=None):
    """A dress on a hanger: `hem` half width at the hem, kind in flare / sheath / wrap."""
    if kind == "flare":
        half = [(0.030, 0.0), (0.058, 0.04), (0.080, 0.10), (0.064, 0.18), (0.070, 0.23), (hem * 0.6, L * 0.62), (hem, L * 0.97), (hem * 0.92, L)]
    elif kind == "sheath":
        half = [(0.030, 0.0), (0.062, 0.04), (0.088, 0.11), (0.074, 0.22), (0.098, 0.34), (hem, L * 0.96), (hem * 0.96, L)]
    else:
        half = [(0.040, 0.0), (0.075, 0.03), (0.100, 0.09), (0.070, 0.20), (0.085, 0.27), (hem * 0.7, L * 0.7), (hem, L)]
    _sym(c, cu, top, half, col)
    c.poly([(cu - 0.032, top), (cu + 0.032, top), (cu, top - 0.075)], scale(col, 0.50), lift=0.0, alpha=0.9)          # neckline, back of the dress
    c.line(cu - 0.075, top - 0.115, cu + 0.075, top - 0.115, 0.004, scale(col, 0.82), 0.5)
    if kind == "wrap":
        c.line(cu - 0.03, top - 0.01, cu + 0.09, top - 0.22, 0.009, scale(col, 0.62), 0.7)
        c.line(cu + 0.02, top - 0.26, cu + hem * 0.92, top - L * 0.97, 0.006, scale(col, 0.6), 0.5)
    _fold_lines(c, cu, top, 0.06, 0.20, hem * 0.9, L * 0.96, 5, scale(col, 0.58))
    _fold_lines(c, cu - 0.01, top, 0.05, 0.22, hem * 0.7, L * 0.9, 3, mix(col, WHITE, 0.45), 0.2)
    if dots:
        _dots(c, 34, cu - hem * 0.8, cu + hem * 0.8, top - L * 0.9, top - 0.14, dots, 0.0075, 0.85)
    if trim:
        c.rect(cu, top - 0.205, 0.145, 0.016, trim, lift=0.05)
        c.ellipse(cu, top - 0.205, 0.012, 0.01, GOLD, lift=0.1)
    c.rect(cu, top - L + 0.004, hem * 1.85, 0.008, scale(col, 0.78), lift=0, alpha=0.7)


def _jacket(c, cu, top, L, col, kind):
    rng = c.rng
    sl = L * 0.92
    for sgn in (-1, 1):                                                     # sleeves
        c.line(cu + sgn * 0.115, top - 0.035, cu + sgn * 0.150, top - sl, 0.062, scale(col, 0.96 if sgn < 0 else 0.7), 1.0)
        c.line(cu + sgn * 0.121, top - 0.04, cu + sgn * 0.152, top - sl * 0.9, 0.012, mix(col, WHITE, 0.25), 0.28 if sgn < 0 else 0.1)
        c.line(cu + sgn * 0.150, top - sl + 0.012, cu + sgn * 0.152, top - sl - 0.012, 0.062, scale(col, 0.62), 0.9)
    half = [(0.030, 0.0), (0.100, 0.025), (0.118, 0.10), (0.110, 0.24), (0.122, L)]
    _sym(c, cu, top, half, col)
    inner = (0.95, 0.94, 0.92) if kind == "blazer" else (0.30, 0.31, 0.38)
    c.poly([(cu - 0.034, top - 0.005), (cu + 0.034, top - 0.005), (cu, top - 0.23)], inner, lift=0.08)
    for sgn in (-1, 1):                                                     # lapels
        c.poly([(cu + sgn * 0.034, top - 0.005), (cu + sgn * 0.082, top - 0.075), (cu + sgn * 0.032, top - 0.165), (cu + sgn * 0.0, top - 0.23)],
               scale(col, 1.12 if sgn < 0 else 0.84), lift=0.06)
    c.line(cu, top - 0.23, cu, top - L, 0.004, scale(col, 0.55), 0.8)
    for i in range(2):
        c.ellipse(cu + 0.014, top - 0.31 - i * 0.07, 0.008, 0.008, GOLD if kind == "blazer" else (0.8, 0.5, 0.2), lift=0.1)
    if kind == "denim":
        for sgn in (-1, 1):
            c.rect(cu + sgn * 0.06, top - 0.17, 0.05, 0.05, scale(col, 1.1), lift=0.08)
            _stitch(c, (cu + sgn * 0.035, top - 0.145), (cu + sgn * 0.085, top - 0.145), 4, (0.95, 0.70, 0.30), 0.003)
        _stitch(c, (cu - 0.11, top - 0.34), (cu + 0.11, top - 0.34), 11, (0.95, 0.70, 0.30), 0.003)
    else:
        c.line(cu - 0.09, top - 0.33, cu - 0.045, top - 0.33, 0.012, scale(col, 1.25), 0.4)
        c.line(cu + 0.05, top - 0.33, cu + 0.09, top - 0.33, 0.012, scale(col, 0.55), 0.5)
    _fold_lines(c, cu, top, 0.09, 0.30, 0.10, L * 0.98, 3, scale(col, 0.58), 0.2)


@sprop("fb_dress_rail", aspect=1.4, fill=1.0)
def fb_dress_rail(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.85, 0.1, 0.38))
    acc2 = _pal(color, "accent2", (0.9, 0.3, 0.3))
    for sgn in (-1, 1):                                                  # chrome posts, round feet
        x = sgn * 0.66
        ao(c, x, 0.0, 0.26, 0.06, 0.6)
        c.ellipse(x, 0.012, 0.10, 0.10 * TILT, (0.45, 0.46, 0.50), lift=0)
        c.ellipse(x, 0.02, 0.09, 0.09 * TILT, CHROME, lift=0.12)
        craft.hshade_box(c, x, 0.5, 0.020, 0.97, (0.97, 0.97, 1.0), (0.45, 0.47, 0.52))
        c.ellipse(x, 0.985, 0.016, 0.016, CHROME, lift=0.1)
    c.line(-0.67, 0.96, 0.67, 0.96, 0.020, (0.62, 0.64, 0.68), 1.0)
    c.line(-0.67, 0.966, 0.67, 0.966, 0.006, (0.97, 0.97, 1.0), 0.85)
    cream, camel = (0.95, 0.91, 0.84), (0.78, 0.58, 0.38)
    items = [("dress", acc, "flare", None, None), ("jacket", cream, "blazer", None, None), ("dress", (0.10, 0.12, 0.18), "sheath", None, None),
             ("jacket", DENIM, "denim", None, None), ("dress", (0.96, 0.95, 0.92), "wrap", None, acc), ("jacket", camel, "blazer", None, None)]
    xs = [-0.55, -0.33, -0.10, 0.12, 0.35, 0.58]
    for (kind, col, sub, trim, dots), cu in zip(items, xs):
        top = 0.905 - rng.uniform(0.0, 0.012)
        _hanger(c, cu, 0.96, top)
        if kind == "dress":
            L = 0.60 if sub != "sheath" else 0.64
            _dress(c, cu, top, L, 0.17 if sub == "flare" else 0.12 if sub == "sheath" else 0.15, col, sub, trim, dots)
        else:
            _jacket(c, cu, top, 0.40, col, sub)
        soft_disc(c, cu - 0.125, 0.66, 0.05, 0.28, BLACK, 0.22, 1.3)
    soft_disc(c, -0.1, 0.99, 0.9, 0.05, WHITE, 0.18, 1.4, add=True)


@sprop("fb_mannequin", aspect=0.52, fill=1.0)
def fb_mannequin(c, color):
    acc = _pal(color, "accent", (0.85, 0.1, 0.38))
    ao(c, 0.0, 0.0, 0.46, 0.08, 0.5)
    c.ellipse(0.0, 0.010, 0.20, 0.20 * TILT, (0.10, 0.10, 0.12), lift=0)                 # round black base
    c.ellipse(0.0, 0.020, 0.19, 0.19 * TILT, (0.20, 0.20, 0.23), lift=0.12)
    c.ellipse(-0.05, 0.026, 0.09, 0.03, (0.38, 0.38, 0.42), alpha=0.55, lift=0)
    craft.hshade_box(c, 0.02, 0.26, 0.022, 0.46, CHROME, (0.45, 0.47, 0.52))
    cream, cream_d = (0.95, 0.91, 0.86), (0.68, 0.62, 0.57)
    for sgn in (-1, 1):                                                                  # calves in nude pumps
        x = sgn * 0.055
        _spoly(c, [(x - 0.030, 0.30), (x + 0.030, 0.30), (x + 0.022, 0.07), (x - 0.022, 0.07)], cream if sgn < 0 else scale(cream, 0.82), 1)
        c.poly([(x - 0.026, 0.075), (x + 0.040, 0.050), (x + 0.040, 0.030), (x - 0.026, 0.038)], (0.15, 0.10, 0.10), lift=0.1)
    # arms (left lit arm hangs, right hand on hip)
    c.line(-0.185, 0.80, -0.245, 0.55, 0.040, cream, 1.0)
    c.line(-0.245, 0.55, -0.232, 0.45, 0.032, scale(cream, 0.93), 1.0)
    c.ellipse(-0.230, 0.435, 0.020, 0.030, scale(cream, 0.9), lift=0.05)
    c.line(0.185, 0.80, 0.262, 0.645, 0.040, scale(cream, 0.80), 1.0)
    c.line(0.262, 0.645, 0.15, 0.55, 0.032, scale(cream, 0.76), 1.0)
    # white top + torso
    _sym(c, 0.0, 0.84, [(0.032, 0.0), (0.170, 0.015), (0.150, 0.10), (0.108, 0.22), (0.112, 0.27)], (0.97, 0.96, 0.94), None, (0.70, 0.68, 0.66), 0.05)
    c.ellipse(0.0, 0.855, 0.040, 0.02, cream, lift=0.0)                                   # neck base
    craft.hshade_box(c, 0.0, 0.89, 0.062, 0.10, cream, cream_d)
    c.ellipse(0.0, 0.965, 0.058, 0.080, cream, lift=0.1)                                  # head: smooth egg
    soft_disc(c, 0.02, 0.945, 0.06, 0.07, BLACK, 0.22, 1.4)
    gloss(c, -0.022, 0.985, 0.022, 0.032, 15, 0.55)
    # skirt: flared midi in the accent colour with a belt
    skirt = acc
    _sym(c, 0.0, 0.595, [(0.100, 0.0), (0.150, 0.06), (0.200, 0.18), (0.235, 0.32)], skirt, None, None, 0.07, 2)
    for i in range(7):
        f = (i + 0.5) / 7 * 2 - 1
        c.line(f * 0.10, 0.585, f * 0.225, 0.285, 0.008, scale(skirt, 0.55) if i % 2 else mix(skirt, WHITE, 0.4), 0.22)
    c.rect(0.0, 0.592, 0.215, 0.026, (0.13, 0.10, 0.10), lift=0.1)
    c.rect(0.012, 0.592, 0.030, 0.026, GOLD, r=0.004, lift=0.15)
    c.rect(0.012, 0.592, 0.018, 0.014, (0.30, 0.2, 0.05), lift=0)
    # camel blazer worn open
    camel = (0.80, 0.60, 0.40)
    cl, cd = scale(camel, 1.14), scale(camel, 0.56)
    # left (lit) sleeve: shoulder cap, tapered upper arm, bent elbow, cuff with buttons
    _tube(c, [(-0.172, 0.815), (-0.222, 0.730), (-0.243, 0.630), (-0.246, 0.560)], [0.031, 0.027, 0.023, 0.020], cl, scale(camel, 0.82), 0.07, 2, mix(camel, WHITE, 0.45), cd)
    _tube(c, [(-0.246, 0.572), (-0.246, 0.538)], [0.0215, 0.0215], scale(camel, 0.80), scale(camel, 0.52), 0.05, 1)
    for dy in (0.002, -0.0160):
        c.ellipse(-0.249, 0.560 + dy, 0.0065, 0.0065, GOLD, lift=0.15)
    c.line(-0.262, 0.640, -0.230, 0.628, 0.0035, cd, 0.30)                                                      # a wrinkle at the elbow
    # right sleeve (in shade): upper arm out to the elbow, forearm back to the hip
    _tube(c, [(0.172, 0.815), (0.236, 0.745), (0.270, 0.660), (0.236, 0.600), (0.176, 0.578)], [0.031, 0.027, 0.023, 0.021, 0.020], scale(camel, 0.84), scale(camel, 0.50), 0.06, 2,
          mix(camel, WHITE, 0.2), cd)
    _tube(c, [(0.176, 0.578), (0.150, 0.568)], [0.021, 0.021], scale(camel, 0.62), scale(camel, 0.40), 0.05, 1)
    c.line(0.262, 0.640, 0.292, 0.628, 0.0035, scale(camel, 0.35), 0.30)
    _spoly(c, [(-0.17, 0.835), (-0.055, 0.84), (-0.090, 0.66), (-0.082, 0.50), (-0.160, 0.50), (-0.135, 0.66)], scale(camel, 1.08), 1)
    _spoly(c, [(0.17, 0.835), (0.055, 0.84), (0.090, 0.66), (0.082, 0.50), (0.160, 0.50), (0.135, 0.66)], scale(camel, 0.76), 1)
    for sgn in (-1, 1):
        c.poly([(sgn * 0.055, 0.845), (sgn * 0.115, 0.80), (sgn * 0.075, 0.70), (sgn * 0.028, 0.745)], scale(camel, 1.2 if sgn < 0 else 0.86), lift=0.05)
    c.line(-0.085, 0.58, -0.085, 0.50, 0.004, scale(camel, 0.6), 0.5)
    # a silk scarf in the accent colour
    c.line(-0.04, 0.84, 0.02, 0.74, 0.020, mix(acc, WHITE, 0.15), 1.0)
    c.line(0.02, 0.74, 0.015, 0.64, 0.016, mix(acc, WHITE, 0.25), 0.95)
    soft_disc(c, -0.10, 0.74, 0.05, 0.10, WHITE, 0.22, 1.2, add=True)


def _denim_fold(c, u, v, w, h, col, d=0.06):
    left, right = scale(col, 1.08), scale(col, 0.72)
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + d, v + h + d * TILT), (u - w / 2 + d, v + h + d * TILT)], scale(col, 1.2), lift=0.03)
    craft.hshade_box(c, u, v + h / 2, w, h, left, right, r=h * 0.1)
    c.rect(u + w / 2 - 0.006, v + h / 2, 0.016, h * 0.9, scale(col, 0.58), alpha=0.5, lift=0)
    _stitch(c, (u - w / 2 + 0.01, v + h - 0.012), (u + w / 2 - 0.02, v + h - 0.012), max(6, int(w / 0.03)), (0.95, 0.72, 0.32), 0.0025, 0.5, 0.8)
    c.line(u - w / 2 + 0.01, v + h * 0.46, u + w / 2 - 0.02, v + h * 0.46, 0.0022, mix(col, WHITE, 0.2), 0.32)


@sprop("fb_denim_cubes", aspect=1.0, fill=1.0)
def fb_denim_cubes(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.85, 0.1, 0.38))
    ao(c, 0.0, 0.0, 0.98, 0.12, 0.5)
    wood = (0.80, 0.66, 0.48)
    craft.hshade_box(c, 0.0, 0.34, 0.92, 0.66, scale(wood, 0.55), scale(wood, 0.35))               # dark back of the cubbies
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.46, 0.34, 0.040, 0.68, wood, scale(wood, 0.72))
    craft.hshade_box(c, 0.0, 0.34, 0.040, 0.64, wood, scale(wood, 0.72))
    for v in (0.015, 0.34, 0.675):
        craft.hshade_box(c, 0.0, v, 0.96, 0.036, scale(wood, 1.08), scale(wood, 0.78), r=0.004)
    denims = [(0.22, 0.34, 0.56), (0.14, 0.22, 0.40), (0.42, 0.55, 0.72), (0.09, 0.12, 0.22), (0.30, 0.42, 0.62)]
    for row, v0 in enumerate((0.038, 0.358)):
        for col_i, u in enumerate((-0.23, 0.23)):
            n = 5 if (row + col_i) % 2 == 0 else 4
            v = v0
            for i in range(n):
                w = 0.35 + rng.uniform(-0.012, 0.012)
                _denim_fold(c, u + rng.uniform(-0.01, 0.01), v, w, 0.050, denims[(i + row * 2 + col_i) % len(denims)])
                v += 0.052
            soft_disc(c, u, v0 + 0.30, 0.21, 0.04, BLACK, 0.20, 1.5)
    # sweaters on top
    cols = [mix(acc, WHITE, 0.1), (0.96, 0.93, 0.88), (0.20, 0.20, 0.24)]
    v = 0.693
    for i in range(3):
        _denim_fold(c, -0.10 + rng.uniform(-0.01, 0.01), v, 0.40, 0.060, cols[i], 0.07)
        v += 0.060
    c.poly([(0.26, 0.69), (0.44, 0.69), (0.44, 0.72), (0.26, 0.72)], (0.55, 0.38, 0.24), lift=0)
    craft.hshade_box(c, 0.35, 0.80, 0.16, 0.20, (0.80, 0.62, 0.42), (0.55, 0.38, 0.24), r=0.03)            # straw bag
    craft.arc(c, 0.35, 0.90, 0.07, 0.11, 0, 180, 0.012, (0.50, 0.34, 0.20), 0.95)


def _bag(c, u, v, w, h, col, cord, logo=None, k=1.0):
    d = w * 0.22
    c.poly([(u + w / 2, v), (u + w / 2 + d, v + d * 0.35), (u + w / 2 + d, v + h + d * 0.35), (u + w / 2, v + h)], scale(col, 0.62 * k), lift=0.05)
    craft.hshade_box(c, u, v + h / 2, w, h, scale(col, 1.08 * k), scale(col, 0.82 * k))
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + d, v + h + d * 0.35), (u - w / 2 + d, v + h + d * 0.35)], scale(col, 1.1), lift=0.05)
    c.rect(u, v + h - 0.008, w, 0.016, scale(col, 0.75), lift=0, alpha=0.6)
    for dx in (-0.22, 0.22):
        craft.arc(c, u + dx * w + d * 0.5, v + h + 0.01, w * 0.12, h * 0.34, 0, 180, 0.007, cord, 0.95)
        c.ellipse(u + dx * w + (0.12 * w if dx < 0 else -0.12 * w), v + h - 0.01, 0.007, 0.007, scale(cord, 0.6), lift=0)
    if logo:
        c.ellipse(u, v + h * 0.48, w * 0.15, w * 0.15, logo, lift=0.08)
        c.ellipse(u, v + h * 0.48, w * 0.085, w * 0.085, scale(col, 1.05), lift=0)
        c.line(u - w * 0.3, v + h * 0.2, u + w * 0.3, v + h * 0.2, 0.006, logo, 0.8)
    soft_disc(c, u - w * 0.3, v + h * 0.6, w * 0.12, h * 0.35, WHITE, 0.16, 1.2, add=True)


@sprop("fb_shopping_bags", aspect=1.1, fill=1.0)
def fb_shopping_bags(c, color):
    acc = _pal(color, "accent", (0.85, 0.1, 0.38))
    ao(c, 0.0, 0.0, 1.0, 0.20, 0.5)
    _bag(c, -0.30, 0.04, 0.38, 0.60, (0.14, 0.14, 0.16), GOLD_L, mix(GOLD, WHITE, 0.2))
    c.poly([(-0.34, 0.66), (-0.30, 0.74), (-0.24, 0.66)], (0.96, 0.90, 0.92), alpha=0.95, lift=0.1)                # tissue paper
    c.poly([(-0.27, 0.66), (-0.20, 0.72), (-0.16, 0.66)], mix(acc, WHITE, 0.6), alpha=0.95, lift=0.1)
    _bag(c, 0.24, 0.0, 0.42, 0.50, acc, (0.97, 0.94, 0.90), WHITE)
    _bag(c, 0.03, 0.0, 0.30, 0.34, (0.96, 0.93, 0.88), mix(acc, BLACK, 0.2), acc)


def _hat(c, u, v, kind, col, band):
    if kind == "wide":
        c.ellipse(u, v + 0.03, 0.17, 0.17 * 0.34, scale(col, 0.62), lift=0)
        craft.hshade_box(c, u, v + 0.10, 0.17, 0.12, mix(col, WHITE, 0.15), scale(col, 0.7), r=0.05)
        c.ellipse(u, v + 0.155, 0.085, 0.032, mix(col, WHITE, 0.2), lift=0.1)
        c.ellipse(u, v + 0.05, 0.17, 0.17 * 0.34, col, lift=0.05, alpha=0.0)
        c.ellipse(u, v + 0.045, 0.185, 0.185 * 0.30, col, lift=0.12)
        c.rect(u, v + 0.075, 0.17, 0.020, band, lift=0.05)
        c.ellipse(u, v + 0.055, 0.17, 0.05, scale(col, 0.55), lift=0, alpha=0.0)
    elif kind == "fedora":
        c.ellipse(u, v + 0.035, 0.145, 0.145 * 0.32, scale(col, 0.7), lift=0)
        craft.hshade_box(c, u, v + 0.12, 0.13, 0.14, col, scale(col, 0.62), r=0.03)
        c.ellipse(u, v + 0.19, 0.065, 0.026, scale(col, 1.18), lift=0.05)
        c.line(u, v + 0.185, u, v + 0.198, 0.012, scale(col, 0.62), 0.9)
        c.ellipse(u, v + 0.04, 0.15, 0.15 * 0.30, col, lift=0.1)
        c.rect(u, v + 0.095, 0.13, 0.026, band, lift=0.05)
    else:
        c.ellipse(u, v + 0.04, 0.12, 0.12 * 0.5, scale(col, 0.7), lift=0)
        c.ellipse(u, v + 0.05, 0.115, 0.115 * 0.5, col, lift=0.14)
        c.line(u + 0.01, v + 0.095, u + 0.012, v + 0.113, 0.012, scale(col, 0.7), 0.9)


@sprop("fb_hat_shelf", aspect=3.0, fill=1.0)
def fb_hat_shelf(c, color):
    acc = _pal(color, "accent", (0.85, 0.1, 0.38))
    ao(c, 0.0, 0.07, 1.4, 0.06, 0.5)
    _hat(c, -0.55, 0.10, "wide", (0.90, 0.78, 0.52), acc)
    _hat(c, -0.12, 0.10, "fedora", (0.45, 0.33, 0.25), (0.13, 0.10, 0.10))
    _hat(c, 0.28, 0.10, "wide", (0.96, 0.93, 0.88), (0.2, 0.2, 0.22))
    _hat(c, 0.62, 0.10, "beret", scale(acc, 0.85), acc)
    wood = (0.78, 0.62, 0.45)
    craft.hshade_box(c, 0.0, 0.085, 1.60, 0.040, scale(wood, 1.1), scale(wood, 0.70), r=0.01)
    for u in (-0.62, 0.62):
        c.poly([(u - 0.02, 0.065), (u + 0.02, 0.065), (u + 0.02, 0.0), (u - 0.02, 0.012)], (0.2, 0.2, 0.22), lift=0)


@niche("fashion-boutique", "Fashion boutique", subjects=("fb_mannequin",),
       strong=("clothing boutique", "fashion boutique", "fashion store", "womenswear", "women's clothing", "dress shop", "apparel store", "clothing store",
               "garments", "dresses", "fashion clothing", "ladies clothing", "kapdon ki dukaan", "कपड़ों की दुकान", "कपड़े की दुकान", "फैशन बुटीक", "ड्रेस"),
       weak=("apparel", "fashion", "boutique", "outfit", "jeans", "jackets", "wardrobe", "clothes", "collection", "editorial", "model in", "पोशाक", "पश्चिमी", "outfits"),
       accent="#d81b60", mood="light", group="retail", avoid=("kurti", "saree", "sari", "कुर्ती", "साड़ी"))
def fashion_boutique(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.55)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for i in range(10):                                                                       # wall moulding panels
            S.rect(-1.0 + i * 0.5, 0.28, 0.40, 0.46, scale(P.wall_top, 0.97), r=0.005, lift=0.0, alpha=0.6)
            S.rect(-1.0 + i * 0.5, 0.28, 0.37, 0.43, scale(P.wall_bot, 0.99), r=0.005, lift=0.0, alpha=0.5)
        S.rect(1.0, 0.535, 14.0, 0.130, scale(mix(P.wall_bot, P.accent_dark, 0.18), 0.94), lift=0.0)                 # wainscot panelling with a gilt rail
        for i in range(22):
            S.rect(-1.5 + i * 0.28, 0.54, 0.22, 0.095, scale(mix(P.wall_bot, P.accent_dark, 0.18), 0.86), r=0.004, lift=0.0, alpha=0.7)
        S.rect(1.0, 0.470, 14.0, 0.012, scale(GOLD, 0.85 * k), lift=0.0)
        S.rect(1.55, 0.26, 0.30, 0.46, scale(GOLD, 0.8 * k), r=0.15, lift=0.0)                  # arched gilt mirror
        S.rect(1.55, 0.26, 0.26, 0.42, mix(P.wall_top, (0.82, 0.88, 0.95), 0.6) if not dk else (0.10, 0.12, 0.2), r=0.13, lift=0.05)
        S.glow(1.55, 0.22, 0.4, P.light, 0.16 if not dk else 0.10)
        S.rect(0.55, 0.20, 0.34, 0.26, scale(GOLD, 0.8 * k), lift=0.0)                          # framed fashion print
        S.rect(0.55, 0.20, 0.30, 0.22, scale(mix(P.accent, WHITE, 0.55), k), lift=0.05)
        S.ellipse(0.55, 0.20, 0.06, 0.08, scale(mix(P.accent, BLACK, 0.2), k), lift=0.0, alpha=0.8)
        for u in (0.40, 0.95, 1.30):
            S.pendant(u, -0.1, 0.14 + 0.02 * (u > 1), (1.0, 0.88, 0.62), shade_w=0.08)
        S.bokeh(8, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.9, 0.7), (1.0, 0.8, 0.7)], 0.01, 0.035, 0.22)
        S.floor(0.60, P.floor_top, P.floor_bot)
    wood = mix(P.surface, WHITE, 0.45) if not dk else scale(P.surface, 0.8)
    S.wood(-5.0, 0.60, 7.0, 2.6, wood, plank=0.11, grain=0.32)
    for i in range(14):                                                                                   # board ends staggered across the planks: a laid floor, not a flat plane
        v = 0.60 + 0.11 * (i % 18) + 0.055
        S.rect(S.rng.uniform(-0.2, 2.2), v, 0.003, 0.11, scale(wood, 0.66), lift=0.0, alpha=0.5)
    S.rect(1.0, 0.60, 14.0, 0.008, scale(P.surface, 0.5), lift=0.0)
    S.rect(1.0, 0.615, 14.0, 0.028, (0.0, 0.0, 0.0), alpha=0.16, lift=0.0)                                   # skirting-board shadow where wall meets floor
    for u0 in (0.05, 0.95, 1.55):                                                                          # window light falling across the boards
        S.soft(u0, 0.78 + (u0 - 0.05) * 0.04, 0.42, 0.06, (1.0, 0.95, 0.80), 0.10 if not dk else 0.14, 1.5, angle=-8.0, add=True)
    _glow_floor(S, 1.05, 0.86, 1.1, 0.16, (1.0, 0.9, 0.7), 0.30 if dk else 0.20)
    # a cream rug with an accent border and gilt inner band, so the pink mannequin stands out against it
    cream = mix((0.96, 0.92, 0.84), P.accent, 0.04)
    rc, ru, rv, ra, rb = (cream if not dk else scale(cream, 0.50)), 1.08, 0.89, 0.86, 0.19
    S.ellipse(ru, rv, ra, rb, scale(P.accent, 0.80 if not dk else 0.42), lift=0.0)
    S.ellipse(ru, rv, ra * 0.95, rb * 0.93, rc, lift=0.0)
    for i in range(30):                                                                                    # motif ring on the border
        a = i * 2 * math.pi / 30
        S.poly([(ru + math.cos(a) * ra * 0.895, rv + math.sin(a) * rb * 0.87 - 0.008), (ru + math.cos(a) * ra * 0.895 + 0.009, rv + math.sin(a) * rb * 0.87),
                (ru + math.cos(a) * ra * 0.895, rv + math.sin(a) * rb * 0.87 + 0.008), (ru + math.cos(a) * ra * 0.895 - 0.009, rv + math.sin(a) * rb * 0.87)],
               scale(GOLD, 0.95 if not dk else 0.5), alpha=0.9)
    for i in range(44):                                                                                    # inner band of small accent dashes
        a = i * 2 * math.pi / 44
        S.circle(ru + math.cos(a) * ra * 0.83, rv + math.sin(a) * rb * 0.80, 0.0075, scale(P.accent_dark, 0.9 if not dk else 0.45), alpha=0.7, lift=0)
    for i in range(30):                                                                                    # soft pile and a medallion
        S.circle(S.rng.uniform(ru - ra * 0.7, ru + ra * 0.7), S.rng.uniform(rv - rb * 0.6, rv + rb * 0.6), S.rng.uniform(0.004, 0.009), scale(rc, S.rng.uniform(0.9, 0.96)), alpha=0.5, lift=0)
    S.ellipse(ru, rv, ra * 0.40, rb * 0.38, mix(rc, P.accent, 0.10), lift=0.0)
    S.put("fb_hat_shelf", 0.60, 0.42, 0.13, color=P, shadow=False, framed=False)
    S.put("fb_denim_cubes", 0.58, 0.88, 0.25, color=P)
    S.put("fb_dress_rail", 1.30, 0.86, 0.40, color=P, shadow=False)
    S.soft(1.30, 0.64, 0.42, 0.18, mix(P.wall_bot, WHITE, 0.3), 0.22 if not dk else 0.0, 1.4)                  # the rail sits a little behind: aerial haze
    S.put("fb_mannequin", 1.00, 0.98, 0.68, color=P, subject=True)
    S.put("fb_shopping_bags", 1.27, 1.00, 0.20, color=P)
    S.focus("detail", 1.00, 0.62)
    if dk:
        S.glow(1.00, 0.58, 0.46, (1.0, 0.88, 0.7), 0.22)
    with S.near(16.0):
        S.circle(0.58, 0.99, 0.05, mix(P.accent, WHITE, 0.25), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.95, 0.85), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ FURNITURE SHOWROOM
def _tag(c, u, v, drop=0.07, col=(0.97, 0.95, 0.90), red=False):
    """A hanging price tag (string, card, a few bars instead of digits)."""
    c.line(u, v, u + 0.01, v - drop * 0.35, 0.0025, (0.35, 0.3, 0.25), 0.9)
    c.rect(u + 0.012, v - drop * 0.35 - 0.036, 0.046, 0.066, scale(col, 0.82), r=0.004, lift=0)
    c.rect(u + 0.010, v - drop * 0.35 - 0.034, 0.044, 0.064, col, r=0.004, lift=0.05)
    c.ellipse(u + 0.010, v - drop * 0.35 - 0.0065, 0.0045, 0.0045, (0.45, 0.4, 0.35), lift=0)
    c.rect(u + 0.010, v - drop * 0.35 - 0.040, 0.030, 0.007, (0.82, 0.12, 0.12) if red else (0.25, 0.22, 0.2), lift=0)
    c.rect(u + 0.010, v - drop * 0.35 - 0.055, 0.022, 0.004, (0.5, 0.48, 0.45), lift=0)


def _fab(c, n, u0, u1, v0, v1, col, alpha=0.35):
    """Woven fabric texture: short seeded dashes inside a box."""
    rng = c.rng
    for _ in range(n):
        u, v = rng.uniform(u0, u1), rng.uniform(v0, v1)
        l = rng.uniform(0.012, 0.03)
        c.line(u, v, u + l, v + rng.uniform(-0.004, 0.004), 0.0022, scale(col, rng.uniform(0.78, 1.18)), alpha)


def _pillow(c, u, v, w, col, ang=0.0, pattern=None):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(-w / 2, -w * 0.46), (w / 2, -w * 0.46), (w * 0.53, w * 0.0), (w / 2, w * 0.46), (-w / 2, w * 0.46), (-w * 0.53, 0.0)]
    pts = [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in pts]
    _spoly(c, pts, col, 2, 0.12)
    c.line(u - w * 0.30 * ca, v - w * 0.30 * sa, u + w * 0.30 * ca, v + w * 0.30 * sa, 0.006, scale(col, 0.65), 0.35)
    if pattern:
        c.line(u - w * 0.36 * ca - w * 0.1 * sa, v - w * 0.36 * sa + w * 0.1 * ca, u + w * 0.36 * ca - w * 0.1 * sa, v + w * 0.36 * sa + w * 0.1 * ca, 0.012, pattern, 0.8)
    soft_disc(c, u - w * 0.18, v + w * 0.14, w * 0.20, w * 0.14, WHITE, 0.2, 1.3, add=True)


@sprop("fu_sofa", aspect=2.5, fill=1.0)
def fu_sofa(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.55, 0.43, 0.39))
    acc2 = _pal(color, "accent2", (0.6, 0.45, 0.35))
    fab = mix(acc, (0.74, 0.72, 0.68), 0.52)
    wood = (0.50, 0.34, 0.22)
    ao(c, 0.0, 0.0, 2.3, 0.26, 0.55)
    for x in (-1.08, 1.08, -0.62, 0.62):                                      # tapered wooden legs
        sp = 1.0 if x > 0 else -1.0
        c.poly([(x - 0.035, 0.12), (x + 0.035, 0.12), (x + 0.018 + 0.02 * sp, 0.0), (x - 0.018 + 0.02 * sp, 0.0)], scale(wood, 0.9 if abs(x) > 1 else 0.7), lift=0.1)
    craft.hshade_box(c, 0.0, 0.62, 2.12, 0.62, scale(fab, 0.95), scale(fab, 0.70), r=0.14)           # back frame
    craft.hshade_box(c, 0.0, 0.24, 2.36, 0.26, scale(fab, 0.88), scale(fab, 0.64), r=0.06)           # base
    c.rect(0.0, 0.14, 2.36, 0.012, scale(fab, 0.5), lift=0, alpha=0.6)
    for i in range(3):                                                                              # back cushions
        u = -0.66 + 0.66 * i
        craft.hshade_box(c, u + rng.uniform(-0.01, 0.01), 0.64, 0.64, 0.38, scale(fab, 1.14), scale(fab, 0.84), r=0.09)
        c.rect(u, 0.80, 0.56, 0.02, scale(fab, 1.28), r=0.01, lift=0, alpha=0.6)
        soft_disc(c, u + 0.32, 0.64, 0.015, 0.20, BLACK, 0.35, 1.2)
        for bx in (-0.14, 0.14):                                                                    # tufted buttons
            for by in (0.56, 0.72):
                c.ellipse(u + bx, by, 0.011, 0.011, scale(fab, 0.5), lift=0)
                c.ellipse(u + bx, by - 0.004, 0.007, 0.006, scale(fab, 0.75), lift=0, alpha=0.7)
    for sgn in (-1, 1):                                                                              # arms
        x = sgn * 1.10
        craft.hshade_box(c, x, 0.44, 0.26, 0.60, scale(fab, 1.06 if sgn < 0 else 0.82), scale(fab, 0.70 if sgn < 0 else 0.62), r=0.10)
        c.ellipse(x, 0.735, 0.12, 0.05, scale(fab, 1.18 if sgn < 0 else 0.95), lift=0.1)
        c.line(x - 0.10 * sgn, 0.67, x - 0.10 * sgn, 0.28, 0.008, scale(fab, 0.5), 0.35)
    for i in range(3):                                                                              # seat cushions with piping
        u = -0.66 + 0.66 * i
        c.poly([(u - 0.30, 0.43), (u + 0.30, 0.43), (u + 0.33, 0.40 + 0.075), (u - 0.27, 0.40 + 0.075)], scale(fab, 1.22), lift=0.05, alpha=1.0)
        craft.hshade_box(c, u, 0.36, 0.64, 0.14, scale(fab, 1.12), scale(fab, 0.78), r=0.05)
        c.rect(u, 0.425, 0.60, 0.008, scale(fab, 1.35), lift=0, alpha=0.6)
        c.rect(u + 0.31, 0.37, 0.012, 0.12, scale(fab, 0.5), lift=0, alpha=0.5)
    _fab(c, 55, -1.05, 1.05, 0.30, 0.86, fab, 0.28)
    _pillow(c, -0.72, 0.58, 0.30, acc, 14, mix(acc2, WHITE, 0.4))
    _pillow(c, 0.76, 0.56, 0.27, mix(acc2, WHITE, 0.15), -12, (0.97, 0.95, 0.90))
    _pillow(c, -0.52, 0.52, 0.24, (0.95, 0.92, 0.86), -6)
    soft_disc(c, -0.60, 0.88, 0.70, 0.08, WHITE, 0.16, 1.4, add=True)
    _tag(c, 1.08, 0.74)


def _chair_front(c, u, v, col, wood):
    """Dining chair seen from the front: back with slats, seat, legs (base centre u, v)."""
    for x in (-0.085, 0.085):
        c.line(u + x, v + 0.30, u + x * 1.15, v, 0.016, scale(wood, 0.8), 1.0)
    craft.hshade_box(c, u, v + 0.31, 0.21, 0.032, scale(col, 1.1), scale(col, 0.75), r=0.012)
    for x in (-0.085, 0.085):
        craft.hshade_box(c, u + x, v + 0.52, 0.016, 0.42, scale(wood, 1.1), scale(wood, 0.7))
    craft.hshade_box(c, u, v + 0.66, 0.20, 0.17, scale(col, 1.05), scale(col, 0.72), r=0.02)
    craft.hshade_box(c, u, v + 0.77, 0.20, 0.020, scale(wood, 1.15), scale(wood, 0.75), r=0.008)
    for i in range(3):
        c.rect(u - 0.06 + 0.06 * i, v + 0.66, 0.008, 0.16, scale(col, 0.6), lift=0, alpha=0.4)


@sprop("fu_dining_set", aspect=1.55, fill=1.0)
def fu_dining_set(c, color):
    rng = c.rng
    wood = (0.62, 0.42, 0.26)
    chair = (0.86, 0.82, 0.74)
    ao(c, 0.0, 0.0, 1.45, 0.26, 0.5)
    _chair_front(c, -0.30, 0.20, chair, scale(wood, 0.9))
    _chair_front(c, 0.30, 0.20, chair, scale(wood, 0.9))
    # side chair in profile at the right end
    for x in (0.74, 0.96):
        c.line(x, 0.30, x, 0.0, 0.020, scale(wood, 0.85), 1.0)
    craft.hshade_box(c, 0.85, 0.31, 0.32, 0.036, chair, scale(chair, 0.7), r=0.012)
    c.poly([(0.97, 0.33), (1.02, 0.33), (1.08, 0.78), (1.03, 0.78)], scale(wood, 1.0), lift=0.1)
    c.poly([(0.965, 0.40), (1.0, 0.40), (1.045, 0.70), (1.01, 0.70)], scale(chair, 0.9), lift=0.05)
    # table: legs, apron, top
    for x, v0, v1, k in ((-0.62, 0.50, 0.16, 0.7), (0.62, 0.50, 0.16, 0.6), (-0.66, 0.46, 0.0, 1.0), (0.66, 0.46, 0.0, 0.8)):
        craft.hshade_box(c, x, (v0 + v1) / 2, 0.050, v0 - v1, scale(wood, 1.05 * k), scale(wood, 0.62 * k))
    c.poly([(-0.66, 0.60), (0.66, 0.60), (0.78, 0.43), (-0.78, 0.43)], scale(wood, 1.18), lift=0.06)
    for i in range(6):
        t = (i + 0.5) / 6
        a, b = -0.66 + 1.32 * t, -0.78 + 1.56 * t
        c.line(a, 0.598, b, 0.435, 0.0028, scale(wood, rng.uniform(0.78, 0.92)), 0.4)
    c.poly([(-0.66, 0.60), (0.66, 0.60), (0.68, 0.595), (-0.68, 0.595)], scale(wood, 0.7), lift=0)
    craft.hshade_box(c, 0.0, 0.415, 1.56, 0.032, scale(wood, 1.04), scale(wood, 0.66), r=0.01)
    c.rect(0.0, 0.43, 1.52, 0.006, mix(wood, WHITE, 0.45), lift=0, alpha=0.55)
    soft_disc(c, -0.3, 0.52, 0.55, 0.05, WHITE, 0.22, 1.4, add=True)
    # tableware: a fruit bowl and a vase
    c.ellipse(-0.12, 0.505, 0.14, 0.045, (0.95, 0.94, 0.9), lift=0.05)
    c.ellipse(-0.12, 0.510, 0.11, 0.030, (0.82, 0.8, 0.76), lift=0.0)
    for i, (dx, col) in enumerate(((-0.17, (0.88, 0.32, 0.18)), (-0.10, (0.95, 0.75, 0.2)), (-0.06, (0.55, 0.72, 0.28)))):
        c.ellipse(-0.0 + dx, 0.54, 0.035, 0.032, col, lift=0.15)
        gloss(c, dx - 0.01, 0.552, 0.01, 0.006, 20, 0.6)
    craft.hshade_box(c, 0.36, 0.55, 0.06, 0.13, (0.92, 0.9, 0.86), (0.66, 0.64, 0.6), r=0.025)
    for a in (-30, 15, 60):
        craft.strand(c, 0.36, 0.62, 0.15, 60 + a, 0.006, (0.3, 0.5, 0.25), 0.95, 0.3)
    c.ellipse(0.35, 0.78, 0.022, 0.022, (0.95, 0.4, 0.45), lift=0.1)
    c.ellipse(0.40, 0.74, 0.02, 0.02, (0.98, 0.85, 0.5), lift=0.1)
    _tag(c, 0.62, 0.43, 0.06, red=True)


@sprop("fu_wardrobe", aspect=0.95, fill=1.0)
def fu_wardrobe(c, color):
    rng = c.rng
    wood = (0.50, 0.32, 0.20)
    ao(c, 0.0, 0.0, 0.92, 0.12, 0.55)
    for x in (-0.40, 0.40):
        c.poly([(x - 0.04, 0.05), (x + 0.04, 0.05), (x + 0.025, 0.0), (x - 0.025, 0.0)], scale(wood, 0.6), lift=0)
    craft.hshade_box(c, 0.0, 0.52, 0.95, 0.92, scale(wood, 1.04), scale(wood, 0.66), r=0.012)
    craft.hshade_box(c, 0.0, 0.985, 1.00, 0.04, scale(wood, 1.15), scale(wood, 0.72), r=0.008)          # crown moulding
    craft.hshade_box(c, 0.0, 0.07, 0.97, 0.05, scale(wood, 0.95), scale(wood, 0.6), r=0.006)
    for i, u in enumerate((-0.31, 0.0, 0.31)):
        c.rect(u, 0.52, 0.29, 0.82, scale(wood, 1.12 - 0.12 * i), r=0.006, lift=0.05)
        if i == 1:                                                                                   # mirrored middle door
            c.rect(u, 0.55, 0.23, 0.70, (0.75, 0.82, 0.88), r=0.006, lift=0.1)
            c.poly([(u - 0.115, 0.85), (u - 0.02, 0.85), (u - 0.115, 0.50)], (0.94, 0.97, 1.0), alpha=0.4)
            c.poly([(u + 0.04, 0.9), (u + 0.09, 0.9), (u - 0.06, 0.28), (u - 0.11, 0.28)], WHITE, alpha=0.16)
            c.rect(u, 0.55, 0.23, 0.70, BLACK, r=0.006, lift=0, alpha=0.0)
            c.rect(u + 0.115, 0.55, 0.008, 0.70, scale(wood, 0.5), lift=0, alpha=0.6)
        else:
            c.rect(u, 0.52, 0.22, 0.70, scale(wood, 1.0), r=0.006, lift=0.12)
            c.rect(u, 0.52, 0.18, 0.64, scale(wood, 0.86), r=0.004, lift=0.12, alpha=0.8)
            for k in range(14):                                                                      # veneer grain
                x = rng.uniform(u - 0.1, u + 0.1)
                y0 = rng.uniform(0.25, 0.7)
                c.line(x, y0, x + rng.uniform(-0.01, 0.01), y0 + rng.uniform(0.1, 0.3), 0.0022, scale(wood, rng.uniform(0.62, 0.9)), 0.35)
        c.rect(u + (0.11 if i != 1 else -0.115), 0.52, 0.012, 0.12, GOLD, r=0.004, lift=0.2)
        c.rect(u + (0.11 if i != 1 else -0.115) - 0.002, 0.53, 0.004, 0.10, GOLD_L, lift=0, alpha=0.7)
    soft_disc(c, -0.38, 0.62, 0.08, 0.36, WHITE, 0.14, 1.3, add=True)
    _tag(c, -0.20, 0.50, 0.08, red=True)


@sprop("fu_bed", aspect=1.95, fill=1.0)
def fu_bed(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.55, 0.43, 0.39))
    wood = (0.60, 0.42, 0.28)
    fab = mix(acc, (0.74, 0.72, 0.68), 0.55)
    ao(c, 0.0, 0.0, 1.8, 0.24, 0.5)
    craft.hshade_box(c, 0.0, 0.62, 1.68, 0.60, scale(fab, 1.0), scale(fab, 0.66), r=0.10)              # padded headboard
    for i in range(7):
        u = -0.72 + i * 0.24
        c.rect(u, 0.62, 0.012, 0.50, scale(fab, 0.55), lift=0, alpha=0.5)
        c.rect(u + 0.012, 0.62, 0.008, 0.50, scale(fab, 1.3), lift=0, alpha=0.5)
    c.rect(0.0, 0.90, 1.60, 0.012, scale(fab, 1.3), lift=0, alpha=0.5)
    for x in (-0.86, 0.86):
        craft.hshade_box(c, x, 0.60, 0.060, 0.62, scale(wood, 1.05), scale(wood, 0.66), r=0.01)           # posts
    # bed frame and legs
    for x in (-0.86, 0.86):
        craft.hshade_box(c, x, 0.05, 0.05, 0.10, scale(wood, 0.8), scale(wood, 0.5))
    craft.hshade_box(c, 0.0, 0.20, 1.78, 0.20, scale(wood, 1.1), scale(wood, 0.66), r=0.01)
    c.rect(0.0, 0.21, 1.72, 0.012, mix(wood, WHITE, 0.4), lift=0, alpha=0.5)
    # mattress (top face with perspective) and linen
    c.poly([(-0.82, 0.50), (0.82, 0.50), (0.88, 0.30), (-0.88, 0.30)], (0.96, 0.95, 0.93), lift=0.05)
    craft.hshade_box(c, 0.0, 0.36, 1.76, 0.12, (0.97, 0.96, 0.94), (0.78, 0.76, 0.74), r=0.04)
    # pillows
    for u, col, a in ((-0.42, (0.97, 0.96, 0.94), 0), (0.0, mix(acc, WHITE, 0.2), 0), (0.42, (0.97, 0.96, 0.94), 0)):
        craft.hshade_box(c, u, 0.54, 0.38, 0.16, scale(col, 1.05), scale(col, 0.76), r=0.07)
        c.rect(u, 0.60, 0.30, 0.012, scale(col, 0.7), lift=0, alpha=0.35)
        soft_disc(c, u - 0.08, 0.58, 0.14, 0.04, WHITE, 0.18, 1.3, add=True)
    # duvet folded over the foot
    c.poly([(-0.90, 0.46), (0.90, 0.46), (0.93, 0.33), (-0.93, 0.33)], mix(acc, (0.9, 0.85, 0.78), 0.25), lift=0.08)
    craft.hshade_box(c, 0.0, 0.31, 1.86, 0.20, scale(mix(acc, (0.9, 0.85, 0.78), 0.25), 1.05), scale(mix(acc, (0.9, 0.85, 0.78), 0.25), 0.72), r=0.05)
    c.rect(0.0, 0.40, 1.80, 0.028, (0.96, 0.94, 0.9), r=0.01, lift=0.05)
    _fab(c, 40, -0.85, 0.85, 0.22, 0.42, mix(acc, (0.9, 0.85, 0.78), 0.25), 0.3)
    c.rect(0.0, 0.215, 1.86, 0.010, scale(acc, 0.5), lift=0, alpha=0.5)
    _tag(c, 0.78, 0.50, 0.07)


@sprop("fu_floor_lamp", aspect=0.42, fill=1.0)
def fu_floor_lamp(c, color):
    ao(c, 0.0, 0.0, 0.34, 0.06, 0.5)
    c.ellipse(0.0, 0.012, 0.13, 0.13 * TILT, (0.12, 0.12, 0.14), lift=0)
    craft.hshade_box(c, 0.0, 0.46, 0.016, 0.84, (0.62, 0.52, 0.30), (0.22, 0.18, 0.10))
    c.poly([(-0.18, 0.99), (0.18, 0.99), (0.21, 0.74), (-0.21, 0.74)], (1.0, 0.92, 0.74), lift=0.1)
    c.ellipse(0.0, 0.99, 0.18, 0.045, (1.0, 0.96, 0.84), lift=0)
    c.ellipse(0.0, 0.74, 0.21, 0.05, (0.9, 0.78, 0.55), lift=0, alpha=0.9)
    soft_disc(c, 0.0, 0.88, 0.30, 0.22, (1.0, 0.9, 0.6), 0.28, 1.5, add=True)


@niche("furniture", "Furniture showroom", subjects=("fu_sofa",),
       strong=("furniture showroom", "furniture store", "furniture shop", "sofa set", "sofa", "dining table", "bed frames", "wardrobe", "home furniture",
               "furniture", "furniture ki dukaan", "sofa set showroom", "फर्नीचर", "फर्नीचर शोरूम", "सोफा", "सोफा सेट", "अलमारी"),
       weak=("sofa", "bed", "wardrobe", "dining", "couch", "cabinet", "armchair", "home decor", "mattress", "interiors"),
       accent="#8d6e63", mood="warm", group="retail", avoid=("interior design", "interior designer", "इंटीरियर डिज़ाइन"))
def furniture(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.55)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        for i in range(26):                                                                      # vertical wood slat feature wall
            S.rect(-0.2 + i * 0.075, 0.30, 0.050, 0.62, scale(mix(P.surface, P.wall_bot, 0.25), 0.9 * k) if i % 2 else scale(P.surface, 0.8 * k), lift=0.0, alpha=0.38)
        S.window(0.30, 0.28, 0.40, 0.40, bars=True, **_sky(dk))
        S.rect(1.72, 0.26, 0.34, 0.44, scale(GOLD, 0.7 * k), lift=0.0)                         # large framed artwork
        S.rect(1.72, 0.26, 0.30, 0.40, scale(mix(P.accent, WHITE, 0.55), k), lift=0.05)
        S.ellipse(1.72, 0.30, 0.09, 0.09, scale(mix(P.accent_dark, WHITE, 0.15), k), lift=0.0, alpha=0.8)
        S.rect(1.0, 0.04, 6.0, 0.020, scale(P.wall_bot, 0.45), lift=0.0)                         # track light rail with spots
        for u in (0.5, 0.95, 1.4, 1.85):
            S.glow(u, 0.07, 0.20, (1.0, 0.94, 0.8), 0.5 if not dk else 0.7)
            S.glow(u, 0.30, 0.42, (1.0, 0.92, 0.74), 0.10 if not dk else 0.16)
        S.bokeh(7, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.9, 0.7)], 0.01, 0.03, 0.2)
        S.floor(0.62, P.floor_top, P.floor_bot)
    fa = mix(P.paper, P.surface, 0.18) if not dk else scale(P.surface, 0.5)
    fb = mix(P.paper, P.surface, 0.28) if not dk else scale(P.surface, 0.42)
    S.tiles(-5.0, 0.62, 7.0, 2.6, fa, fb, 0.34)
    S.rect(1.0, 0.62, 14.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    S.soft(1.1, 0.85, 1.2, 0.16, (1.0, 0.92, 0.75), 0.30 if dk else 0.16, 1.5, add=True)
    rug = mix(P.accent, (0.9, 0.82, 0.7), 0.35) if not dk else scale(P.accent_dark, 0.7)
    S.ellipse(0.88, 0.93, 0.50, 0.10, scale(rug, 0.8), lift=0.0, alpha=0.8)
    S.ellipse(0.88, 0.925, 0.46, 0.085, rug, lift=0.03)
    S.put("fu_floor_lamp", 0.50, 0.78, 0.36, framed=False)
    S.put("fu_bed", 0.80, 0.74, 0.28, color=P, shadow_alpha=0.16)
    S.put("fu_wardrobe", 1.42, 0.74, 0.42, color=P, shadow_alpha=0.16)
    S.put("fu_dining_set", 1.43, 1.00, 0.27, color=P, shadow_alpha=0.14)
    S.put("fu_sofa", 0.86, 0.99, 0.24, color=P, subject=True, shadow_alpha=0.16)
    S.focus("detail", 0.86, 0.84)
    with S.near(16.0):
        S.circle(0.55, 0.99, 0.05, mix(P.accent, WHITE, 0.3), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.75, 0.20, 0.06, (1.0, 0.95, 0.85), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ MOBILE & ELECTRONICS STORE
def _vgrad(c, u, v, w, h, top, bot, r=0.0, alpha=1.0):
    """Rectangle (centre u, v) filled with a top-to-bottom gradient."""
    cx, cy, hw, hh = c.X(u), c.Y(v), w * c.s / 2, h * c.s / 2
    y0, sp = cy - hh, max(1.0, 2 * hh)
    c.cv.box(cx, cy, hw, hh, top, rad=min(r * c.s, hw, hh), alpha=alpha, shade=lambda px, py: mix(top, bot, clamp((py - y0) / sp)))


def _phone(c, u, v, w, h, scr, glow=None, cam=True):
    """A smartphone standing with its base centre at (u, v): dark bezel, gradient wallpaper, notch, glare, camera."""
    body = (0.07, 0.07, 0.09)
    _vgrad(c, u, v + h / 2, w, h, (0.45, 0.46, 0.5), body, r=w * 0.17)
    _vgrad(c, u, v + h / 2, w * 0.94, h * 0.97, body, scale(body, 1.4), r=w * 0.15)
    _vgrad(c, u, v + h / 2, w * 0.86, h * 0.91, scr[0], scr[1], r=w * 0.11)
    if glow:
        soft_disc(c, u + w * 0.1, v + h * 0.35, w * 0.34, h * 0.22, glow, 0.8, 1.3, add=True)
    c.ellipse(u, v + h * 0.935, w * 0.045, w * 0.045, (0.02, 0.02, 0.03), lift=0)
    c.rect(u, v + h * 0.75, w * 0.40, h * 0.035, mix(scr[0], WHITE, 0.55), r=0.004, lift=0, alpha=0.55)       # clock widget
    for i in range(3):
        c.ellipse(u - w * 0.26 + i * w * 0.26, v + h * 0.12, w * 0.07, w * 0.07, mix(scr[1], WHITE, 0.35), lift=0, alpha=0.75)
    c.poly([(u - w * 0.40, v + h * 0.90), (u - w * 0.05, v + h * 0.90), (u - w * 0.40, v + h * 0.28)], WHITE, alpha=0.12)


def _phone_back(c, u, v, w, h, col):
    _vgrad(c, u, v + h / 2, w, h, scale(col, 1.2), scale(col, 0.72), r=w * 0.16)
    c.rect(u - w * 0.2, v + h * 0.86, w * 0.4, w * 0.4, scale(col, 0.45), r=w * 0.1, lift=0.1)
    for dy in (-0.07, 0.07):
        c.ellipse(u - w * 0.2 + dy * w * 0.0 - w * 0.07 + w * 0.14 * (dy > 0), v + h * 0.86 + dy * w * 1.1, w * 0.075, w * 0.075, (0.05, 0.05, 0.07), lift=0.1)
        c.ellipse(u - w * 0.2 - w * 0.07 + w * 0.14 * (dy > 0), v + h * 0.86 + dy * w * 1.1, w * 0.04, w * 0.04, (0.2, 0.25, 0.4), lift=0.2)
    gloss(c, u - w * 0.18, v + h * 0.5, w * 0.1, h * 0.3, 8, 0.4)


SCREENS = [((0.10, 0.25, 0.60), (0.85, 0.35, 0.55)), ((0.95, 0.60, 0.20), (0.55, 0.10, 0.35)), ((0.05, 0.45, 0.50), (0.45, 0.85, 0.65)),
           ((0.30, 0.15, 0.65), (0.15, 0.55, 0.9)), ((0.9, 0.25, 0.30), (0.98, 0.7, 0.35))]


@sprop("mo_glass_counter", aspect=3.0, fill=1.0)
def mo_glass_counter(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.1, 0.45, 0.8))
    dark = (0.11, 0.12, 0.15)
    ao(c, 0.0, 0.0, 3.0, 0.14, 0.5)
    craft.hshade_box(c, 0.0, 0.035, 2.94, 0.07, (0.08, 0.08, 0.10), (0.04, 0.04, 0.05))
    craft.hshade_box(c, 0.0, 0.31, 3.0, 0.50, scale(dark, 1.3), scale(dark, 0.6), r=0.01)                    # cabinet frame
    _vgrad(c, 0.0, 0.31, 2.88, 0.42, (0.62, 0.74, 0.84), (0.20, 0.27, 0.36))                                # glass front
    c.rect(0.0, 0.31, 2.88, 0.42, (0.05, 0.08, 0.12), alpha=0.25, lift=0)
    for v, n in ((0.20, 11), (0.38, 11)):                                                                     # two glass shelves of phones
        c.rect(0.0, v, 2.86, 0.014, (0.8, 0.9, 1.0), lift=0, alpha=0.55)
        for i in range(n):
            u = -1.30 + i * 0.26 + rng.uniform(-0.01, 0.01)
            sc = SCREENS[(i + int(v * 10)) % len(SCREENS)]
            if i % 3 == 2:
                _phone_back(c, u, v + 0.008, 0.095, 0.15, mix(sc[0], (0.5, 0.5, 0.55), 0.4))
            else:
                _phone(c, u, v + 0.008, 0.095, 0.15, sc, mix(sc[1], WHITE, 0.2))
        c.rect(0.0, v - 0.012, 2.86, 0.012, mix(acc, WHITE, 0.4), lift=0, alpha=0.6)                          # LED edge under the shelf
        soft_disc(c, 0.0, v - 0.02, 1.4, 0.05, mix(acc, WHITE, 0.4), 0.22, 1.5, add=True)
    c.poly([(-1.35, 0.52), (-0.55, 0.52), (-1.05, 0.10), (-1.45, 0.10)], WHITE, alpha=0.10)                  # reflections
    c.poly([(0.20, 0.52), (0.50, 0.52), (0.05, 0.10), (-0.25, 0.10)], WHITE, alpha=0.08)
    c.poly([(1.0, 0.52), (1.25, 0.52), (0.95, 0.10), (0.70, 0.10)], WHITE, alpha=0.07)
    c.rect(0.0, 0.52, 3.0, 0.016, (0.7, 0.78, 0.86), lift=0.1)                                               # aluminium edge
    for x in (-1.5, 1.5):
        c.rect(x, 0.31, 0.028, 0.50, (0.7, 0.74, 0.8), lift=0.1, alpha=0.8)
    c.poly([(-1.5, 0.528), (1.5, 0.528), (1.44, 0.605), (-1.44, 0.605)], (0.72, 0.84, 0.94), alpha=0.9, lift=0.06)   # glass top
    c.poly([(-1.5, 0.535), (-0.4, 0.535), (-0.45, 0.60), (-1.44, 0.60)], WHITE, alpha=0.18)
    # display phones on acrylic stands (on the counter top)
    for i, u in enumerate((-1.18, -0.78, -0.38)):
        sc = SCREENS[(i * 2) % len(SCREENS)]
        c.poly([(u - 0.09, 0.565), (u + 0.09, 0.565), (u + 0.07, 0.585), (u - 0.07, 0.585)], (0.9, 0.95, 1.0), alpha=0.65, lift=0.05)
        _phone(c, u, 0.575, 0.18, 0.37, sc, mix(sc[1], WHITE, 0.2))
        c.rect(u, 0.553, 0.11, 0.028, (0.97, 0.97, 0.95), r=0.004, lift=0.05)
        c.rect(u - 0.025, 0.557, 0.045, 0.006, acc, lift=0)
        c.rect(u + 0.02, 0.549, 0.04, 0.005, (0.4, 0.4, 0.42), lift=0)
    craft.hshade_box(c, 0.14, 0.60, 0.20, 0.14, (0.97, 0.97, 0.98), (0.72, 0.74, 0.78), r=0.012)             # boxed phone
    c.rect(0.14, 0.60, 0.14, 0.075, mix(acc, WHITE, 0.15), r=0.008, lift=0.05)
    c.ellipse(0.14, 0.60, 0.022, 0.022, WHITE, lift=0, alpha=0.8)
    c.rect(0.14, 0.64, 0.20, 0.008, (0.82, 0.84, 0.88), lift=0)
    _vgrad(c, 0.48, 0.66, 0.30, 0.20, (0.05, 0.05, 0.07), (0.1, 0.1, 0.13), r=0.012)                         # demo tablet
    _vgrad(c, 0.48, 0.665, 0.27, 0.17, SCREENS[2][0], SCREENS[2][1], r=0.008)
    soft_disc(c, 0.52, 0.66, 0.10, 0.05, (1, 0.9, 0.6), 0.6, 1.3, add=True)


def _pack(c, u, v, w, h, kind, col, acc):
    """A hanging blister pack: card with a header stripe and the product."""
    c.line(u, v + h, u, v + h + 0.02, 0.004, (0.7, 0.7, 0.75), 0.9)
    c.rect(u, v + h / 2, w, h, (0.96, 0.96, 0.97), r=0.006, lift=0.1)
    c.rect(u, v + h - 0.022, w, 0.040, acc, r=0.004, lift=0.05)
    c.ellipse(u - w * 0.30, v + h - 0.022, 0.009, 0.009, WHITE, lift=0, alpha=0.8)
    c.rect(u + w * 0.1, v + h - 0.022, w * 0.40, 0.006, WHITE, lift=0, alpha=0.7)
    mu, mv = u, v + h * 0.44
    if kind == "case":
        _vgrad(c, mu, mv, w * 0.50, h * 0.62, scale(col, 1.2), scale(col, 0.7), r=0.014)
        c.ellipse(mu - w * 0.10, mv + h * 0.2, 0.017, 0.017, (0.06, 0.06, 0.08), lift=0.1)
        c.ellipse(mu - w * 0.10, mv + h * 0.2 - 0.036, 0.017, 0.017, (0.06, 0.06, 0.08), lift=0.1)
    elif kind == "charger":
        craft.hshade_box(c, mu - w * 0.08, mv + h * 0.1, w * 0.30, h * 0.34, WHITE, (0.78, 0.8, 0.84), r=0.01)
        c.rect(mu - w * 0.08, mv + h * 0.30, w * 0.14, 0.012, (0.6, 0.6, 0.65), lift=0)
        craft.arc(c, mu + w * 0.08, mv - h * 0.1, w * 0.17, h * 0.17, 180, 360, 0.0065, col, 0.95)
        craft.arc(c, mu + w * 0.08, mv - h * 0.1, w * 0.12, h * 0.12, 180, 360, 0.006, col, 0.95)
    elif kind == "buds":
        for sgn in (-1, 1):
            c.ellipse(mu + sgn * w * 0.16, mv + h * 0.20, 0.020, 0.024, col if sgn < 0 else scale(col, 0.8), lift=0.2)
            c.ellipse(mu + sgn * w * 0.16, mv + h * 0.20, 0.009, 0.011, scale(col, 0.4), lift=0)
            c.line(mu + sgn * w * 0.16, mv + h * 0.14, mu + sgn * w * 0.04, mv - h * 0.06, 0.004, scale(col, 0.6), 0.95)
        craft.arc(c, mu, mv - h * 0.18, w * 0.18, h * 0.13, 0, 360, 0.0045, scale(col, 0.7), 0.95, 14)
        c.rect(mu, mv - h * 0.02, 0.012, 0.022, (0.15, 0.15, 0.18), lift=0.1)
    elif kind == "bank":
        _vgrad(c, mu, mv, w * 0.40, h * 0.56, scale(col, 0.4), scale(col, 0.18), r=0.012)
        for i in range(4):
            c.ellipse(mu - w * 0.12 + i * w * 0.08, mv + h * 0.18, 0.005, 0.005, (0.3, 0.95, 0.5) if i < 3 else (0.3, 0.3, 0.35), lift=0)
        c.rect(mu, mv - h * 0.05, w * 0.28, 0.010, mix(acc, WHITE, 0.2), lift=0, alpha=0.8)
    else:                                                                                                 # smartwatch
        c.rect(mu, mv, w * 0.17, h * 0.78, scale(col, 0.9), r=0.01, lift=0.1)
        craft.hshade_box(c, mu, mv, w * 0.30, w * 0.30, (0.15, 0.16, 0.2), (0.05, 0.05, 0.07), r=0.014)
        c.rect(mu, mv, w * 0.24, w * 0.24, (0.3, 0.6, 0.9), r=0.01, lift=0.1)
        c.ellipse(mu, mv, w * 0.05, w * 0.05, (0.95, 0.4, 0.3), lift=0.1, alpha=0.9)


def _price_tag(c, u, v, col=(1.0, 0.85, 0.15)):
    c.rect(u, v, 0.045, 0.022, col, r=0.003, lift=0.05)
    c.rect(u, v, 0.028, 0.004, (0.25, 0.2, 0.1), lift=0, alpha=0.7)


def _headphones(c, u, v, col, acc):
    """Over-ear headphones standing on a ledge: band, two cushioned cups."""
    craft.arc(c, u, v + 0.10, 0.085, 0.095, 0, 180, 0.020, scale(col, 0.8), 1.0, 14)
    craft.arc(c, u, v + 0.10, 0.085, 0.095, 40, 140, 0.007, mix(col, WHITE, 0.45), 0.7, 8)
    for sgn in (-1, 1):
        craft.hshade_box(c, u + sgn * 0.085, v + 0.05, 0.040, 0.085, scale(col, 1.1 if sgn < 0 else 0.78), scale(col, 0.55), r=0.016)
        c.ellipse(u + sgn * 0.085, v + 0.05, 0.012, 0.028, scale(acc, 0.95), lift=0.1, alpha=0.9)
    soft_disc(c, u - 0.05, v + 0.17, 0.04, 0.02, WHITE, 0.4, 1.3, add=True)


def _speaker(c, u, v, col, acc, r=0.055, h=0.15):
    """A cylindrical Bluetooth speaker with a mesh grille, rubber ends and an LED ring."""
    craft.hshade_box(c, u, v + h / 2, r * 2, h, scale(col, 1.12), scale(col, 0.50), r=r * 0.5)
    for i in range(7):
        c.rect(u, v + 0.03 + i * (h - 0.06) / 6.0, r * 1.8, 0.004, scale(col, 0.38), lift=0, alpha=0.7)
    c.rect(u, v + h - 0.012, r * 2.0, 0.020, (0.10, 0.10, 0.12), r=0.006, lift=0.1)
    c.rect(u, v + 0.012, r * 2.0, 0.018, (0.10, 0.10, 0.12), r=0.006, lift=0.1)
    c.ellipse(u, v + h * 0.52, 0.007, 0.007, mix(acc, WHITE, 0.6), lift=0, alpha=0.95)
    soft_disc(c, u - r * 0.5, v + h * 0.7, r * 0.35, h * 0.25, WHITE, 0.25, 1.3, add=True)


def _power_bank(c, u, v, w, h, col):
    craft.hshade_box(c, u, v + h / 2, w, h, scale(col, 1.15), scale(col, 0.62), r=0.01)
    for i in range(4):
        c.ellipse(u - w * 0.3 + i * w * 0.2, v + h * 0.85, 0.0045, 0.0045, (0.3, 0.95, 0.5) if i < 3 else (0.35, 0.36, 0.4), lift=0)
    c.rect(u, v + h * 0.42, w * 0.55, 0.008, mix(col, WHITE, 0.55), lift=0, alpha=0.7)
    c.rect(u, v + h * 0.30, w * 0.35, 0.005, mix(col, WHITE, 0.4), lift=0, alpha=0.6)


def _cable_coil(c, u, v, col):
    for i in range(3):
        craft.arc(c, u, v + 0.03, 0.034 - i * 0.005, 0.025 - i * 0.004, 0, 360, 0.006, col, 0.95, 14)
    c.rect(u + 0.036, v + 0.012, 0.014, 0.020, WHITE, r=0.003, lift=0.05)


@sprop("mo_acc_wall", aspect=0.92, fill=1.0)
def mo_acc_wall(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.1, 0.45, 0.8))
    navy = (0.13, 0.17, 0.26)
    ao(c, 0.0, 0.0, 0.8, 0.07, 0.4)
    craft.hshade_box(c, 0.0, 0.5, 0.92, 1.0, scale(navy, 1.25), scale(navy, 0.8), r=0.01)
    for i in range(30):                                                                                    # pegboard: vertical grooves
        c.rect(-0.44 + i * 0.030, 0.47, 0.0025, 0.90, scale(navy, 0.55), lift=0, alpha=0.35)
    for v in (0.275, 0.575):                                                                                # two display ledges
        craft.hshade_box(c, 0.0, v, 0.92, 0.026, mix(navy, WHITE, 0.30), scale(navy, 0.7), r=0.004)
        c.rect(0.0, v + 0.014, 0.90, 0.004, mix(acc, WHITE, 0.55), lift=0, alpha=0.8)
        soft_disc(c, 0.0, v - 0.03, 0.46, 0.035, mix(acc, WHITE, 0.4), 0.30, 1.4, add=True)
    # header sign: a lit light-box
    craft.hshade_box(c, 0.0, 0.955, 0.86, 0.075, scale(acc, 0.85), scale(acc, 0.55), r=0.008)
    c.rect(-0.18, 0.955, 0.40, 0.018, WHITE, r=0.004, lift=0, alpha=0.9)
    c.rect(0.20, 0.955, 0.16, 0.012, mix(acc, WHITE, 0.6), r=0.004, lift=0, alpha=0.8)
    soft_disc(c, 0.0, 0.955, 0.5, 0.06, mix(acc, WHITE, 0.4), 0.35, 1.4, add=True)
    accs = [acc, mix(acc, (1.0, 0.5, 0.2), 0.5), (0.2, 0.7, 0.5), (0.85, 0.2, 0.35)]
    # row 1: hanging packs in different sizes and colours, with a gap, and tags
    _pack(c, -0.35, 0.665, 0.18, 0.21, "case", (0.88, 0.25, 0.35), accs[0])
    _pack(c, -0.15, 0.700, 0.17, 0.17, "buds", (0.95, 0.75, 0.2), accs[2])
    _pack(c, 0.04, 0.655, 0.19, 0.23, "watch", (0.2, 0.2, 0.24), accs[1])
    _pack(c, 0.24, 0.690, 0.17, 0.18, "charger", (0.15, 0.6, 0.55), accs[3])
    _pack(c, 0.40, 0.670, 0.14, 0.20, "case", (0.3, 0.35, 0.8), accs[2])
    _price_tag(c, -0.35, 0.655)
    _price_tag(c, 0.24, 0.683, (0.95, 0.35, 0.3))
    # first ledge: headphones, speaker, a boxed smart speaker
    _headphones(c, -0.30, 0.59, (0.14, 0.14, 0.17), accs[0])
    _speaker(c, -0.04, 0.59, (0.62, 0.20, 0.25), accs[1])
    craft.hshade_box(c, 0.22, 0.65, 0.17, 0.14, (0.96, 0.96, 0.97), (0.72, 0.74, 0.78), r=0.006)
    c.rect(0.22, 0.66, 0.11, 0.07, mix(acc, WHITE, 0.15), r=0.01, lift=0.05)
    c.ellipse(0.22, 0.66, 0.025, 0.025, scale(navy, 0.8), lift=0.1)
    _speaker(c, 0.40, 0.59, (0.20, 0.55, 0.52), accs[3], 0.040, 0.11)
    # row 2: charger / bud / case packs below, on another rail
    _pack(c, -0.33, 0.325, 0.19, 0.20, "charger", (0.95, 0.75, 0.2), accs[1])
    _pack(c, -0.12, 0.345, 0.18, 0.18, "case", (0.2, 0.2, 0.24), accs[3])
    _pack(c, 0.09, 0.320, 0.20, 0.21, "buds", (0.88, 0.25, 0.35), accs[0])
    _pack(c, 0.30, 0.340, 0.17, 0.19, "bank", (0.3, 0.35, 0.8), accs[2])
    _price_tag(c, -0.12, 0.337, (0.95, 0.35, 0.3))
    _price_tag(c, 0.09, 0.312)
    # lower ledge: power banks and cable coils, boxed accessories on the bottom shelf
    for i, (col, w_, hh) in enumerate((((0.88, 0.25, 0.35), 0.075, 0.14), ((0.15, 0.6, 0.55), 0.075, 0.12), ((0.3, 0.35, 0.8), 0.08, 0.16), ((0.95, 0.75, 0.2), 0.07, 0.11))):
        _power_bank(c, -0.34 + i * 0.09, 0.288, w_, hh, col)
    _cable_coil(c, 0.08, 0.288, (0.95, 0.95, 0.97))
    _cable_coil(c, 0.20, 0.288, accs[3])
    _cable_coil(c, 0.32, 0.288, (0.2, 0.2, 0.24))
    for i, (col, w_) in enumerate((((0.96, 0.96, 0.97), 0.26), (mix(acc, WHITE, 0.2), 0.22), ((0.2, 0.22, 0.28), 0.24))):                       # boxes on the bottom shelf
        craft.hshade_box(c, -0.30 + i * 0.30, 0.095, w_, 0.15, scale(col, 1.05), scale(col, 0.70), r=0.006)
        c.rect(-0.30 + i * 0.30, 0.115, w_ * 0.6, 0.012, scale(col, 0.55), lift=0, alpha=0.6)
        c.ellipse(-0.30 + i * 0.30 - w_ * 0.28, 0.075, 0.010, 0.010, accs[i], lift=0.1)
    soft_disc(c, 0.0, 0.98, 0.5, 0.06, (0.9, 0.95, 1.0), 0.2, 1.4, add=True)


@sprop("mo_repair_mat", aspect=1.2, fill=1.0)
def mo_repair_mat(c, color):
    """The repair bench: a workbench with an ESD mat, an opened phone, tools and a lit magnifier lamp."""
    acc = _pal(color, "accent", (0.1, 0.45, 0.8))
    mat = (0.13, 0.34, 0.32)
    wood = (0.80, 0.66, 0.48)
    ao(c, 0.0, 0.0, 1.2, 0.08, 0.5)
    for sgn in (-1, 1):                                                                                      # cabinet legs and drawer unit
        craft.hshade_box(c, sgn * 0.52, 0.15, 0.05, 0.30, (0.30, 0.32, 0.38), (0.12, 0.13, 0.16))
    craft.hshade_box(c, 0.25, 0.16, 0.50, 0.28, (0.40, 0.43, 0.50), (0.14, 0.15, 0.19), r=0.006)
    for v in (0.085, 0.165, 0.245):
        c.rect(0.25, v, 0.44, 0.004, (0.08, 0.08, 0.10), lift=0, alpha=0.8)
        c.rect(0.25, v + 0.035, 0.12, 0.010, (0.80, 0.82, 0.88), r=0.004, lift=0.1)
    craft.hshade_box(c, 0.0, 0.325, 1.14, 0.045, scale(wood, 1.08), scale(wood, 0.72), r=0.006)              # bench top
    c.poly([(-0.52, 0.62), (0.52, 0.62), (0.57, 0.35), (-0.57, 0.35)], scale(mat, 1.08), lift=0.1)              # ESD mat in perspective
    for i in range(1, 8):
        tt = i / 8.0
        c.line(-0.52 + 1.04 * tt, 0.62, -0.57 + 1.14 * tt, 0.35, 0.004, mix(mat, WHITE, 0.45), 0.45)
    for j in (0.43, 0.51, 0.57):
        c.line(-0.55, j, 0.55, j, 0.004, mix(mat, WHITE, 0.45), 0.45)
    # the opened phone: back plate, logic board, battery, camera holes
    c.poly([(-0.34, 0.60), (0.10, 0.60), (0.14, 0.38), (-0.40, 0.38)], (0.12, 0.12, 0.15), lift=0.1)
    c.poly([(-0.30, 0.57), (-0.10, 0.57), (-0.10, 0.45), (-0.34, 0.45)], (0.20, 0.58, 0.38), lift=0.1)
    for i in range(6):
        c.rect(-0.28 + (i % 3) * 0.055, 0.53 - (i // 3) * 0.055, 0.035, 0.028, (0.10, 0.14, 0.11) if i % 2 else (0.78, 0.78, 0.72), lift=0.05)
    c.poly([(-0.08, 0.57), (0.08, 0.57), (0.10, 0.45), (-0.08, 0.45)], (0.76, 0.79, 0.84), lift=0.1)
    c.rect(0.0, 0.51, 0.09, 0.012, (0.50, 0.53, 0.58), lift=0, alpha=0.8)
    c.ellipse(-0.28, 0.585, 0.020, 0.012, (0.04, 0.04, 0.06), lift=0.2)
    c.ellipse(-0.22, 0.585, 0.020, 0.012, (0.04, 0.04, 0.06), lift=0.2)
    for i in range(7):                                                                                      # tiny screws
        c.ellipse(-0.50 + i * 0.030, 0.42 + (i % 2) * 0.018, 0.009, 0.0055, (0.88, 0.88, 0.92), lift=0.2)
    for k, u in enumerate((0.22, 0.30, 0.38)):                                                              # screwdrivers
        col = (0.9, 0.3, 0.2) if k == 0 else (0.95, 0.75, 0.2) if k == 1 else acc
        c.line(u, 0.46 - k * 0.018, u + 0.12, 0.52 - k * 0.018, 0.026, col, 1.0)
        c.line(u - 0.07, 0.43 - k * 0.018, u, 0.46 - k * 0.018, 0.008, (0.78, 0.8, 0.85), 1.0)
        c.line(u + 0.03, 0.47 - k * 0.018, u + 0.10, 0.50 - k * 0.018, 0.008, mix(col, WHITE, 0.5), 0.6)
    c.line(0.20, 0.38, 0.32, 0.37, 0.008, (0.75, 0.78, 0.82), 1.0)                                         # tweezers
    c.ellipse(0.46, 0.46, 0.055, 0.030, (0.05, 0.05, 0.07), lift=0.2)                                      # suction cup
    c.ellipse(0.46, 0.465, 0.035, 0.018, (0.22, 0.22, 0.27), lift=0.2)
    # magnifier lamp: clamp, two-segment arm, round lens with a lit ring
    c.rect(0.46, 0.64, 0.05, 0.03, (0.15, 0.16, 0.19), r=0.006, lift=0.1)
    c.line(0.46, 0.64, 0.36, 0.84, 0.018, (0.55, 0.58, 0.64), 1.0)
    c.line(0.36, 0.84, 0.10, 0.92, 0.016, (0.55, 0.58, 0.64), 1.0)
    c.line(0.37, 0.83, 0.12, 0.905, 0.005, WHITE, 0.5)
    c.ellipse(0.36, 0.84, 0.014, 0.014, (0.2, 0.2, 0.24), lift=0.2)
    c.ellipse(-0.02, 0.90, 0.135, 0.135 * 0.8, (0.10, 0.10, 0.13), lift=0)
    c.ellipse(-0.02, 0.90, 0.120, 0.120 * 0.8, (0.72, 0.88, 0.98), lift=0.1, alpha=0.9)
    c.ellipse(-0.02, 0.90, 0.100, 0.100 * 0.8, (1.0, 1.0, 0.95), lift=0.0, alpha=0.55)
    gloss(c, -0.07, 0.915, 0.05, 0.022, 14, 0.7)
    soft_disc(c, -0.02, 0.62, 0.34, 0.26, (1.0, 0.97, 0.85), 0.32, 1.5, add=True)                         # the lamp lights the mat
    soft_disc(c, -0.02, 0.88, 0.18, 0.10, (1.0, 0.97, 0.85), 0.40, 1.6, add=True)


@sprop("mo_tv_shelf", aspect=1.45, fill=1.0)
def mo_tv_shelf(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.1, 0.45, 0.8))
    frame = (0.16, 0.17, 0.21)
    ao(c, 0.0, 0.0, 1.35, 0.12, 0.45)
    craft.hshade_box(c, 0.0, 0.5, 1.44, 1.0, scale(frame, 0.7), scale(frame, 0.4), r=0.008)
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.71, 0.5, 0.045, 1.0, scale(frame, 1.5), scale(frame, 0.9))
    for v in (0.02, 0.45, 0.97):
        craft.hshade_box(c, 0.0, v, 1.44, 0.04, scale(frame, 1.7), scale(frame, 0.95), r=0.004)
    # TV
    craft.hshade_box(c, -0.05, 0.72, 1.00, 0.44, (0.04, 0.04, 0.05), (0.02, 0.02, 0.03), r=0.012)
    _vgrad(c, -0.05, 0.72, 0.97, 0.41, (0.08, 0.20, 0.45), (0.95, 0.55, 0.30), r=0.006)
    c.ellipse(0.15, 0.62, 0.16, 0.16, (1.0, 0.85, 0.55), lift=0, alpha=0.9)
    soft_disc(c, 0.15, 0.62, 0.32, 0.22, (1.0, 0.8, 0.5), 0.6, 1.3, add=True)
    c.poly([(-0.55, 0.52), (-0.40, 0.68), (-0.24, 0.55), (-0.10, 0.74), (0.12, 0.52)], (0.10, 0.12, 0.22), lift=0.0, alpha=0.92)
    c.poly([(-0.05, 0.52), (0.2, 0.52), (0.4, 0.74), (0.44, 0.52)], (0.14, 0.16, 0.28), lift=0.0, alpha=0.9)
    c.poly([(-0.52, 0.93), (-0.12, 0.93), (-0.40, 0.52), (-0.52, 0.52)], WHITE, alpha=0.09)
    craft.hshade_box(c, -0.05, 0.495, 0.14, 0.03, (0.25, 0.26, 0.3), (0.1, 0.1, 0.12))
    craft.hshade_box(c, -0.05, 0.465, 0.42, 0.012, (0.25, 0.26, 0.3), (0.1, 0.1, 0.12))
    # speaker on the right of the TV
    craft.hshade_box(c, 0.56, 0.58, 0.20, 0.26, (0.18, 0.18, 0.22), (0.06, 0.06, 0.08), r=0.025)
    for dv, r in ((0.08, 0.055), (-0.04, 0.036)):
        c.ellipse(0.56, 0.58 + dv, r, r, (0.05, 0.05, 0.06), lift=0)
        c.ellipse(0.56, 0.58 + dv, r * 0.55, r * 0.55, (0.2, 0.2, 0.25), lift=0.2)
    # lower shelf: open laptop, stack of laptop boxes, tablet
    c.poly([(-0.62, 0.16), (-0.20, 0.16), (-0.22, 0.42), (-0.60, 0.42)], (0.05, 0.06, 0.08), lift=0)
    _vgrad(c, -0.41, 0.29, 0.34, 0.23, (0.20, 0.42, 0.72), (0.75, 0.35, 0.55), r=0.005)
    c.poly([(-0.64, 0.16), (-0.18, 0.16), (-0.12, 0.10), (-0.58, 0.10)], (0.78, 0.8, 0.84), lift=0.1)
    c.poly([(-0.58, 0.14), (-0.22, 0.14), (-0.20, 0.12), (-0.56, 0.12)], (0.35, 0.37, 0.42), lift=0)
    c.rect(-0.41, 0.135, 0.46, 0.04, (0.8, 0.82, 0.86), lift=0.1)
    soft_disc(c, -0.40, 0.30, 0.26, 0.10, WHITE, 0.14, 1.3, add=True)
    for i, col in enumerate(((0.95, 0.95, 0.96), mix(acc, WHITE, 0.2), (0.2, 0.22, 0.28))):
        craft.hshade_box(c, 0.30 + 0.02 * (i % 2), 0.06 + i * 0.065, 0.46, 0.060, scale(col, 1.05), scale(col, 0.72), r=0.006)
        c.rect(0.30 + 0.02 * (i % 2) - 0.1, 0.06 + i * 0.065, 0.12, 0.012, scale(col, 0.62), lift=0, alpha=0.6)
    c.poly([(0.56, 0.27), (0.54, 0.43), (0.70, 0.43), (0.70, 0.27)], (0.05, 0.05, 0.07), lift=0)
    soft_disc(c, 0.0, 0.0, 1.0, 0.02, BLACK, 0.2, 1.4)


@niche("mobile-store", "Mobile & electronics store", subjects=("mo_glass_counter",),
       strong=("mobile shop", "mobile store", "smartphone store", "mobile accessories", "phone repair", "mobile repair", "electronics store",
               "mobile phone shop", "mobile showroom", "mobile ki dukaan", "मोबाइल शॉप", "मोबाइल की दुकान", "मोबाइल रिपेयर", "स्मार्टफोन", "इलेक्ट्रॉनिक्स"),
       weak=("smartphone", "mobile", "charger", "earphones", "gadgets", "laptop", "tablet", "tv", "phone case", "electronics"),
       accent="#1976d2", mood="cool", group="retail", avoid=("mobile app", "app development", "ऐप डेवलपमेंट"))
def mobile_store(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.7)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        for i, u in enumerate((0.0, 0.62, 1.24, 1.86)):                                              # backlit LED wall panels
            S.rect(u + 0.31, 0.26, 0.58, 0.50, scale(mix(P.accent_dark, P.wall_bot, 0.4), k), lift=0.0, alpha=0.8)
            S.glow(u + 0.31, 0.26, 0.5, mix(P.accent, WHITE, 0.3), 0.18 if not dk else 0.30)
        for v in (0.06, 0.52):                                                                       # LED strips
            S.rect(1.0, v, 6.0, 0.010, mix(P.accent, WHITE, 0.7), lift=0.0, alpha=0.9)
            S.soft(1.0, v, 3.0, 0.035, mix(P.accent, WHITE, 0.5), 0.4 if not dk else 0.6, 1.5, add=True)
        S.rect(0.30, 0.28, 0.34, 0.20, (0.05, 0.06, 0.09), r=0.01, lift=0.0)                         # wall TV, glowing
        S.gradient_rect(0.14, 0.19, 0.46, 0.37, (0.1, 0.3, 0.6), (0.9, 0.5, 0.35))
        S.glow(0.30, 0.28, 0.4, (0.9, 0.7, 0.6), 0.2)
        for u in (0.55, 1.0, 1.45, 1.9):
            S.glow(u, 0.01, 0.22, (0.9, 0.95, 1.0), 0.5 if not dk else 0.7)
        S.bokeh(10, 0.0, 0.1, 2.0, 0.55, [mix(P.accent, WHITE, 0.5), (0.9, 0.95, 1.0), (0.6, 0.8, 1.0)], 0.01, 0.035, 0.25)
        S.floor(0.62, mix(P.floor_top, P.wall_bot, 0.55), mix(P.floor_bot, P.wall_bot, 0.4))
    fa = mix(P.paper, (0.5, 0.58, 0.68), 0.45) if not dk else (0.09, 0.10, 0.14)
    fb = mix(P.paper, (0.5, 0.58, 0.68), 0.6) if not dk else (0.06, 0.07, 0.10)
    S.tiles(-5.0, 0.62, 7.0, 2.6, fa, fb, 0.30)
    S.rect(1.0, 0.62, 14.0, 0.007, scale(fa, 0.55), lift=0.0)
    S.soft(1.1, 0.90, 1.1, 0.14, mix(P.accent, WHITE, 0.5), 0.26 if dk else 0.14, 1.5, add=True)
    for _ in range(4):                                                                                  # reflections of the ceiling spots on the polished tiles
        S.soft(S.rng.uniform(0.4, 1.8), S.rng.uniform(0.72, 1.1), S.rng.uniform(0.03, 0.05), S.rng.uniform(0.06, 0.12), (0.9, 0.96, 1.0), 0.12 if dk else 0.07, 1.5, add=True)
    S.put("mo_acc_wall", 0.74, 0.76, 0.52, color=P, shadow_alpha=0.2)
    S.put("mo_tv_shelf", 1.29, 0.78, 0.42, color=P, shadow_alpha=0.2)
    S.put("mo_glass_counter", 0.98, 0.98, 0.31, color=P, subject=True)
    S.put("mo_repair_mat", 1.38, 1.04, 0.36, color=P, shadow_alpha=0.3)
    S.focus("detail", 0.85, 0.82)
    if dk:
        S.glow(1.05, 0.80, 0.5, mix(P.accent, WHITE, 0.4), 0.14)
    with S.near(16.0):
        S.circle(0.55, 0.99, 0.05, mix(P.accent, WHITE, 0.3), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.18, 0.06, (0.85, 0.92, 1.0), alpha=0.25, lift=0, soft=6.0)


# ================================================================================================ PRINTING STUDIO
CYAN, MAGENTA, YELLOW, KEY = (0.0, 0.68, 0.92), (0.90, 0.10, 0.52), (1.0, 0.88, 0.10), (0.10, 0.10, 0.12)


def _gpoly(c, pts, top, bot, smooth=0, alpha=1.0):
    """Polygon filled with a top-to-bottom gradient (scanline fill)."""
    if smooth:
        pts = _chaikin(pts, smooth)
    px = [(c.X(u), c.Y(v)) for u, v in pts]
    ys = [p[1] for p in px]
    y0, sp = min(ys), max(1.0, max(ys) - min(ys))
    _fillpoly(c, px, top, alpha, lambda x, y: mix(top, bot, clamp((y - y0) / sp)))


@sprop("pr_plotter", aspect=2.1, fill=1.0)
def pr_plotter(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.9, 0.22, 0.2))
    acc2 = _pal(color, "accent2", (0.95, 0.45, 0.2))
    ao(c, 0.0, 0.0, 1.9, 0.22, 0.5)
    # stand: two legs, cross bar, castors
    for sgn in (-1, 1):
        x = sgn * 0.80
        craft.hshade_box(c, x, 0.30, 0.070, 0.58, (0.42, 0.44, 0.50), (0.18, 0.19, 0.23))
        c.ellipse(x, 0.012, 0.15, 0.15 * TILT, (0.2, 0.2, 0.24), lift=0.1)
        c.ellipse(x, 0.05, 0.034, 0.034, (0.08, 0.08, 0.1), lift=0.1)
    craft.hshade_box(c, 0.0, 0.14, 1.56, 0.030, (0.5, 0.52, 0.58), (0.25, 0.26, 0.3))
    # paper roll on the top (a white cylinder lying across) and its dark spindle ends
    craft.hshade_box(c, 0.0, 0.955, 1.62, 0.13, (0.99, 0.99, 0.99), (0.70, 0.72, 0.76), r=0.012)
    c.rect(0.0, 0.985, 1.58, 0.012, WHITE, lift=0, alpha=0.8)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.82, 0.955, 0.035, 0.068, (0.92, 0.92, 0.94) if sgn < 0 else (0.7, 0.7, 0.74), lift=0.1)
        c.ellipse(sgn * 0.82, 0.955, 0.012, 0.025, (0.45, 0.35, 0.25), lift=0.2)
        c.rect(sgn * 0.86, 0.955, 0.06, 0.016, (0.2, 0.2, 0.24), lift=0.1)
    # body
    body = (0.95, 0.95, 0.96)
    craft.hshade_box(c, 0.0, 0.72, 1.90, 0.32, scale(body, 1.03), scale(body, 0.72), r=0.04)
    c.rect(0.0, 0.855, 1.86, 0.030, (0.32, 0.34, 0.4), r=0.012, lift=0.1)                      # top cover seam
    c.rect(0.0, 0.575, 1.84, 0.020, (0.05, 0.05, 0.07), r=0.008, lift=0)                      # media slot
    soft_disc(c, 0.0, 0.57, 0.9, 0.03, BLACK, 0.4, 1.5)
    craft.hshade_box(c, 0.0, 0.58, 1.84, 0.010, (0.7, 0.72, 0.78), (0.4, 0.42, 0.48))
    # control panel with a touch screen and indicator lights
    c.rect(-0.62, 0.74, 0.34, 0.15, (0.07, 0.08, 0.11), r=0.012, lift=0.1)
    _vgrad(c, -0.62, 0.745, 0.30, 0.11, (0.25, 0.55, 0.85), (0.1, 0.25, 0.5), r=0.006)
    for i in range(4):
        c.rect(-0.70 + i * 0.05, 0.74, 0.03, 0.05, (CYAN, MAGENTA, YELLOW, (0.9, 0.9, 0.92))[i], lift=0.1, alpha=0.9)
    for i in range(3):
        c.ellipse(-0.40 + i * 0.04, 0.78, 0.008, 0.008, (0.3, 0.95, 0.5) if i < 2 else (1.0, 0.7, 0.2), lift=0)
    # ink tank windows (CMYK)
    c.rect(0.62, 0.725, 0.56, 0.13, (0.10, 0.11, 0.14), r=0.012, lift=0.08)
    for i, col in enumerate((CYAN, MAGENTA, YELLOW, KEY)):
        c.rect(0.42 + i * 0.13, 0.725, 0.085, 0.10, scale(col, 0.55), r=0.008, lift=0)
        c.rect(0.42 + i * 0.13, 0.70, 0.075, 0.062, col, r=0.006, lift=0.15)
        c.rect(0.415 + i * 0.13, 0.73, 0.012, 0.075, mix(col, WHITE, 0.6), lift=0, alpha=0.6)
    soft_disc(c, -0.5, 0.80, 0.9, 0.06, WHITE, 0.18, 1.4, add=True)
    c.rect(0.0, 0.62, 1.86, 0.014, (0.74, 0.75, 0.8), lift=0, alpha=0.5)
    # the printed banner coming out of the slot and hanging down in front
    pts = [(-0.60, 0.565), (0.60, 0.565), (0.62, 0.30), (0.63, 0.05), (0.40, 0.02), (0.20, 0.06), (-0.05, 0.025), (-0.28, 0.05), (-0.50, 0.02), (-0.62, 0.05),
           (-0.62, 0.30)]
    shadow_pts = [(x + 0.06, y - 0.01) for x, y in pts]
    _spoly(c, shadow_pts, (0.0, 0.0, 0.0), 1, 0.0, 0.28)
    _gpoly(c, pts, mix(acc, (0.25, 0.05, 0.10), 0.55), mix(acc2, (1.0, 0.8, 0.4), 0.3), 1)
    c.ellipse(-0.20, 0.38, 0.19, 0.19, (0.99, 0.96, 0.9), lift=0.04)
    c.ellipse(-0.20, 0.38, 0.12, 0.12, scale(acc, 0.9), lift=0.06)
    for i in range(3):
        c.rect(0.25, 0.46 - i * 0.07, 0.34 - i * 0.07, 0.030, (0.99, 0.97, 0.94), r=0.01, lift=0, alpha=0.95)
    c.rect(0.25, 0.25, 0.34, 0.012, (0.99, 0.97, 0.94), lift=0, alpha=0.6)
    for i, col in enumerate((CYAN, MAGENTA, YELLOW, KEY)):                                      # colour bar and crop marks
        c.rect(-0.45 + i * 0.075, 0.115, 0.07, 0.04, col, lift=0.05)
    for x in (-0.58, 0.58):
        c.line(x, 0.53, x, 0.49, 0.004, (0.1, 0.1, 0.1), 0.8)
    c.poly([(-0.60, 0.56), (-0.40, 0.56), (-0.48, 0.05), (-0.62, 0.05)], WHITE, alpha=0.12)         # soft light down the left of the banner
    c.poly([(0.60, 0.56), (0.45, 0.56), (0.50, 0.05), (0.63, 0.05)], BLACK, alpha=0.18)
    _dots(c, 0, 0, 0, 0, 0, WHITE)
    c.line(-0.60, 0.545, 0.60, 0.545, 0.012, (0.0, 0.0, 0.0), 0.25)
    soft_disc(c, 0.0, 0.03, 0.65, 0.05, BLACK, 0.3, 1.4)


@sprop("pr_table", aspect=1.9, fill=1.0)
def pr_table(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.8, 0.20, 0.5)
    metal = (0.55, 0.57, 0.63)
    for x, v1, k in ((-0.82, 0.0, 1.0), (0.82, 0.0, 1.0), (-0.74, 0.0, 0.7), (0.74, 0.0, 0.6)):
        craft.hshade_box(c, x, 0.42, 0.055, 0.84, scale(metal, 1.1 * k), scale(metal, 0.55 * k))
    craft.hshade_box(c, 0.0, 0.32, 1.56, 0.032, scale(metal, 0.9), scale(metal, 0.5))                  # lower shelf
    c.poly([(-0.88, 0.88), (0.88, 0.88), (0.94, 0.80), (-0.94, 0.80)], (0.95, 0.95, 0.94), lift=0.05)
    craft.hshade_box(c, 0.0, 0.79, 1.88, 0.040, (0.92, 0.9, 0.86), (0.62, 0.6, 0.56), r=0.006)
    c.poly([(-0.80, 0.865), (0.80, 0.865), (0.86, 0.82), (-0.86, 0.82)], (0.30, 0.55, 0.45), alpha=0.35)       # green cutting mat
    for i in range(1, 12):
        t = i / 12.0
        c.line(-0.80 + 1.6 * t, 0.865, -0.86 + 1.72 * t, 0.82, 0.003, WHITE, 0.25)
    soft_disc(c, -0.4, 0.87, 0.8, 0.05, WHITE, 0.2, 1.4, add=True)
    for i, col in enumerate((mix((0.95, 0.95, 0.96), CYAN, 0.0), (0.9, 0.9, 0.88), (0.85, 0.85, 0.88))):                      # paper reams below
        craft.hshade_box(c, -0.30 + i * 0.12, 0.40 + 0.0, 0.50, 0.060, scale(col, 1.05), scale(col, 0.75), r=0.004)
    craft.hshade_box(c, 0.45, 0.375, 0.46, 0.060, (0.2, 0.4, 0.8), (0.1, 0.2, 0.5), r=0.004)
    craft.hshade_box(c, 0.45, 0.435, 0.46, 0.060, (0.95, 0.95, 0.96), (0.72, 0.72, 0.76), r=0.004)


def _card(c, u, v, w, h, col, acc, d=0.05):
    left, right = scale(col, 1.04), scale(col, 0.76)
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u + w / 2 + d, v + h + d * TILT), (u - w / 2 + d, v + h + d * TILT)], scale(col, 1.06), lift=0.03)
    craft.hshade_box(c, u, v + h / 2, w, h, left, right)
    for i in range(1, 5):
        c.line(u - w / 2, v + h * i / 5, u + w / 2, v + h * i / 5, 0.0018, scale(col, 0.7), 0.4)
    c.ellipse(u - w * 0.2 + d * 0.5, v + h + d * TILT * 0.5, d * 0.35, d * 0.14, acc, lift=0, alpha=0.9)
    c.rect(u + w * 0.14 + d * 0.5, v + h + d * TILT * 0.5, w * 0.36, 0.004, scale(col, 0.45), lift=0, alpha=0.8)


@sprop("pr_card_stacks", aspect=1.5, fill=0.55)
def pr_card_stacks(c, color):
    acc = _pal(color, "accent", (0.9, 0.22, 0.2))
    ao(c, 0.0, 0.0, 1.3, 0.22, 0.5)
    _card(c, -0.38, 0.02, 0.44, 0.17, (0.97, 0.96, 0.94), acc, 0.12)
    _card(c, 0.14, 0.02, 0.44, 0.13, mix(acc, WHITE, 0.7), acc, 0.12)
    _card(c, 0.50, 0.05, 0.36, 0.10, (0.14, 0.14, 0.17), mix(acc, WHITE, 0.2), 0.10)
    # fanned cards leaning in front
    for i, (u, a, col) in enumerate(((-0.12, 12, (0.98, 0.97, 0.95)), (-0.02, 3, mix(acc, WHITE, 0.82)), (0.09, -7, (0.14, 0.14, 0.17)))):
        pts = [(-0.11, 0.0), (0.11, 0.0), (0.11, 0.13), (-0.11, 0.13)]
        r_ = math.radians(a)
        pp = [(u + x * math.cos(r_) - y * math.sin(r_), 0.025 + x * math.sin(r_) + y * math.cos(r_)) for x, y in pts]
        _spoly(c, pp, col, 0, 0.04)
        c.rect(u + math.sin(r_) * -0.04, 0.085, 0.10, 0.004, acc if i != 2 else (0.9, 0.9, 0.92), lift=0, alpha=0.9)
        c.ellipse(u - 0.05, 0.11, 0.012, 0.012, acc if i != 2 else (0.9, 0.9, 0.92), lift=0)


@sprop("pr_flyers", aspect=1.3, fill=0.6)
def pr_flyers(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.9, 0.22, 0.2))
    acc2 = _pal(color, "accent2", (0.95, 0.45, 0.2))
    ao(c, 0.0, 0.0, 1.15, 0.22, 0.5)
    for i in range(7):                                                                           # stack of printed flyers
        w = 0.62 + rng.uniform(-0.01, 0.01)
        craft.hshade_box(c, -0.22 + rng.uniform(-0.008, 0.008), 0.012 + i * 0.011, w, 0.012, (0.98, 0.98, 0.97), (0.78, 0.78, 0.8))
    c.poly([(-0.53, 0.09), (0.09, 0.09), (0.19, 0.17), (-0.43, 0.17)], (0.97, 0.97, 0.96), lift=0.03)
    c.poly([(-0.50, 0.095), (0.06, 0.095), (0.14, 0.155), (-0.42, 0.155)], mix(acc, (0.2, 0.05, 0.1), 0.2), lift=0.06)
    c.poly([(-0.42, 0.12), (-0.14, 0.12), (-0.08, 0.15), (-0.36, 0.15)], (0.99, 0.95, 0.88), lift=0, alpha=0.85)
    c.ellipse(-0.03, 0.128, 0.04, 0.012, acc2, lift=0.1)
    for u, a, col in ((0.44, -9, acc2), (0.33, 4, (0.98, 0.98, 0.97)), (0.52, 14, mix(acc, WHITE, 0.6))):          # loose leaflets, fan
        r_ = math.radians(a)
        pts = [(-0.10, 0.0), (0.10, 0.0), (0.10, 0.28), (-0.10, 0.28)]
        pp = [(u + x * math.cos(r_) - y * math.sin(r_), 0.015 + x * math.sin(r_) + y * math.cos(r_)) for x, y in pts]
        _spoly(c, pp, col, 0, 0.05)
        c.rect(u - math.sin(r_) * 0.08, 0.16, 0.10, 0.012, scale(col, 0.7), lift=0, alpha=0.7)
        c.rect(u - math.sin(r_) * 0.10, 0.20, 0.08, 0.008, scale(col, 0.7), lift=0, alpha=0.6)


@sprop("pr_ink_cans", aspect=1.2, fill=1.0)
def pr_ink_cans(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.22, 0.55)
    for i, (u, v, h, col) in enumerate(((-0.28, 0.20, 0.46, MAGENTA), (0.20, 0.22, 0.48, CYAN), (-0.06, 0.04, 0.40, YELLOW), (0.44, 0.02, 0.36, KEY))):
        r = 0.17
        mid = scale(col, 1.0)
        craft.cylinder(c, u, v, r, h, scale(col, 1.18), scale(col, 0.58), (0.78, 0.8, 0.84), lip=True)
        c.rect(u, v + h * 0.52, 2 * r, h * 0.36, (0.96, 0.96, 0.95), lift=0.04)                      # label
        craft.hshade_box(c, u, v + h * 0.52, 2 * r, h * 0.36, (0.98, 0.98, 0.97), (0.70, 0.7, 0.72))
        c.rect(u, v + h * 0.62, 2 * r, h * 0.10, mid, lift=0.1)
        c.ellipse(u, v + h * 0.47, r * 0.40, r * 0.40, mid, lift=0.1)
        c.rect(u, v + h * 0.38, r * 1.2, 0.006, scale(col, 0.4), lift=0, alpha=0.6)
        c.rect(u, v + h * 0.82, 2 * r, h * 0.05, scale(col, 0.7), lift=0.05)                                 # shoulder band
        c.ellipse(u, v + h, r * 0.68, r * 0.68 * TILT, scale(col, 0.82), lift=0.1)                    # ink inside the open lid
        gloss(c, u - r * 0.35, v + h * 0.60, r * 0.12, h * 0.22, 10, 0.5)
        if i == 0:
            c.ellipse(u + 0.06, v + h * 0.95, 0.026, 0.020, col, lift=0.1)                                # an ink drip
            c.line(u + 0.06, v + h * 0.95, u + 0.07, v + h * 0.80, 0.020, col, 0.95)
            c.ellipse(u + 0.07, v + h * 0.78, 0.014, 0.020, col, lift=0.1)


@sprop("pr_paper_rolls", aspect=1.2, fill=1.0)
def pr_paper_rolls(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.22, 0.5)
    for u, v, h, tone in ((-0.24, 0.12, 0.92, (0.97, 0.96, 0.93)), (0.32, 0.18, 0.78, (0.93, 0.95, 0.97)), (0.02, 0.0, 0.62, (0.99, 0.99, 0.98))):
        r = 0.23
        craft.cylinder(c, u, v, r, h, scale(tone, 1.04), scale(tone, 0.66), scale(tone, 0.95), lip=False)
        for _ in range(7):
            vv = rng.uniform(v + 0.05, v + h - 0.03)
            c.line(u - r * 0.9, vv, u + r * 0.9, vv + rng.uniform(-0.006, 0.006), 0.003, scale(tone, 0.82), 0.4)
        c.ellipse(u, v + h, r, r * TILT, scale(tone, 0.96), lift=0.04)
        c.ellipse(u, v + h, r * 0.55, r * TILT * 0.55, scale(tone, 0.88), lift=0)
        c.ellipse(u, v + h + 0.004, r * 0.26, r * TILT * 0.26, (0.55, 0.40, 0.26), lift=0.1)
        c.ellipse(u, v + h + 0.008, r * 0.17, r * TILT * 0.17, (0.2, 0.15, 0.1), lift=0)


@niche("printing", "Printing studio", subjects=("pr_plotter",),
       strong=("printing press", "printing shop", "printing studio", "flex printing", "banner printing", "visiting cards", "digital printing", "offset printing",
               "large format printing", "business card printing", "print shop", "प्रिंटिंग", "प्रिंटिंग प्रेस", "फ्लेक्स प्रिंटिंग", "विजिटिंग कार्ड", "छपाई", "flex banner"),
       weak=("printer", "plotter", "flyers", "brochures", "banners", "posters", "stationery", "cmyk", "pamphlets", "print"),
       accent="#e53935", mood="light", group="retail", avoid=("3d printing", "3d print", "tattoo"))
def printing(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.55)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for r_i, v in enumerate((0.20, 0.38)):                                                      # tall rack with paper boxes and rolls
            S.rect(0.35, v + 0.07, 0.90, 0.012, scale((0.55, 0.57, 0.62), k), lift=0.0)
            for i in range(8):
                u = -0.05 + i * 0.105
                if (i + r_i) % 3 == 0:
                    S.rect(u, v + 0.02, 0.07, 0.10, scale((0.75, 0.62, 0.45), k), lift=0.0)
                else:
                    S.circle(u, v + 0.01, 0.045, scale(mix((0.97, 0.96, 0.93), P.accent, 0.1 * (i % 3)), k), lift=0.0)
        for i, col in enumerate((P.accent, (0.0, 0.62, 0.85), (0.95, 0.8, 0.1), (0.15, 0.15, 0.18), P.accent2, (0.95, 0.95, 0.95))):        # pinned print samples
            S.rect(1.15 + i * 0.17, 0.22 + 0.04 * (i % 2), 0.13, 0.18 + 0.03 * (i % 3), scale(col, k), lift=0.05)
        S.rect(1.0, 0.04, 6.0, 0.012, scale(P.wall_bot, 0.5), lift=0.0)
        for u in (0.3, 0.9, 1.5, 2.1):                                                              # ceiling strip lights
            S.rect(u, 0.03, 0.42, 0.016, (1.0, 1.0, 1.0), lift=0.0)
            S.glow(u, 0.04, 0.34, (0.95, 0.97, 1.0), 0.4 if not dk else 0.55)
        S.bokeh(7, 0.0, 0.1, 2.0, 0.5, [(0.95, 0.95, 1.0), mix(P.accent, WHITE, 0.5)], 0.01, 0.03, 0.18)
        S.floor(0.60, P.floor_top, P.floor_bot)
    fa = mix(P.paper, (0.62, 0.64, 0.68), 0.45) if not dk else (0.10, 0.10, 0.12)
    fb = mix(P.paper, (0.62, 0.64, 0.68), 0.58) if not dk else (0.07, 0.07, 0.09)
    S.tiles(-5.0, 0.60, 7.0, 2.6, fa, fb, 0.40)
    S.rect(1.0, 0.60, 14.0, 0.007, scale(fa, 0.55), lift=0.0)
    S.soft(1.0, 0.86, 1.1, 0.15, (1.0, 0.98, 0.92), 0.28 if dk else 0.14, 1.5, add=True)
    S.put("pr_table", 1.45, 0.84, 0.30, color=P)
    S.put("pr_plotter", 0.95, 0.97, 0.52, color=P, subject=True)
    S.put("pr_paper_rolls", 0.40, 0.92, 0.26, color=P, framed=False, shadow_alpha=0.18)
    S.put("pr_card_stacks", 1.43, 0.575 + 0.12 * 0.0 + 0.0, 0.10, color=P, shadow=False)
    S.put("pr_flyers", 1.55, 0.585, 0.12, color=P, shadow=False)
    S.put("pr_ink_cans", 1.37, 1.00, 0.15, color=P, shadow_alpha=0.2)
    S.focus("detail", 0.95, 0.70)
    with S.near(16.0):
        S.circle(0.55, 0.99, 0.05, mix(P.accent, WHITE, 0.3), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.95, 0.85), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ TAILOR
@sprop("tl_sewing_machine", aspect=1.56, fill=1.0)
def tl_sewing_machine(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.43, 0.3, 0.25))
    acc2 = _pal(color, "accent2", (0.7, 0.4, 0.3))
    fab = mix(acc, (0.8, 0.25, 0.3), 0.55) if _pal(color, "mood", "") != "dark" else mix(acc, (0.8, 0.25, 0.3), 0.55)
    chrome = (0.82, 0.84, 0.88)
    ao(c, 0.0, 0.0, 1.45, 0.22, 0.55)
    craft.hshade_box(c, -0.02, 0.030, 1.50, 0.060, (0.62, 0.42, 0.25), (0.30, 0.18, 0.10), r=0.01)               # wooden base board
    craft.hshade_box(c, -0.02, 0.145, 1.30, 0.130, (0.24, 0.24, 0.28), (0.05, 0.05, 0.07), r=0.025)                # machine bed
    c.poly([(-0.64, 0.205), (0.56, 0.205), (0.60, 0.240), (-0.60, 0.240)], (0.60, 0.62, 0.68), lift=0.08)            # steel plate on the bed top
    c.rect(-0.30, 0.215, 0.20, 0.012, (0.9, 0.9, 0.94), lift=0, alpha=0.7)                                           # slide plate
    _hpoly(c, [(0.28, 0.20), (0.62, 0.20), (0.60, 0.72), (0.30, 0.72)], (0.22, 0.22, 0.26), (0.04, 0.04, 0.06), 0.05, 1.0, 2)        # pillar
    _hpoly(c, [(-0.52, 0.58), (0.62, 0.58), (0.64, 0.88), (-0.52, 0.88)], (0.26, 0.26, 0.30), (0.04, 0.04, 0.06), 0.06, 1.0, 2)       # arm
    _hpoly(c, [(-0.66, 0.46), (-0.34, 0.46), (-0.34, 0.88), (-0.66, 0.88)], (0.28, 0.28, 0.32), (0.05, 0.05, 0.07), 0.05, 1.0, 2)     # head
    c.line(-0.44, 0.865, 0.56, 0.865, 0.012, (0.62, 0.64, 0.70), 0.45)                                               # top highlight
    craft.arc(c, 0.02, 0.74, 0.36, 0.06, 195, 345, 0.008, GOLD, 0.9)                                                  # gold decals
    craft.arc(c, 0.02, 0.71, 0.30, 0.04, 200, 340, 0.004, GOLD_L, 0.8)
    c.line(-0.30, 0.80, 0.52, 0.80, 0.005, GOLD, 0.7)
    c.ellipse(-0.52, 0.66, 0.045, 0.045, (0.04, 0.04, 0.06), lift=0)                                                 # stitch-length dial
    c.ellipse(-0.52, 0.66, 0.036, 0.036, chrome, lift=0.18)
    for a in range(0, 360, 45):
        c.line(-0.52, 0.66, -0.52 + 0.034 * math.cos(math.radians(a)), 0.66 + 0.034 * math.sin(math.radians(a)), 0.003, (0.35, 0.36, 0.4), 0.7)
    c.ellipse(0.46, 0.45, 0.075, 0.075, (0.04, 0.04, 0.06), lift=0)                                                  # pillar dial
    c.ellipse(0.46, 0.45, 0.06, 0.06, chrome, lift=0.18)
    c.ellipse(0.46, 0.45, 0.025, 0.025, (0.3, 0.3, 0.35), lift=0.1)
    # hand wheel on the right end
    c.ellipse(0.66, 0.74, 0.050, 0.145, (0.12, 0.12, 0.15), lift=0)
    c.ellipse(0.665, 0.74, 0.042, 0.135, chrome, lift=0.18)
    c.ellipse(0.69, 0.74, 0.022, 0.07, (0.3, 0.3, 0.35), lift=0.1)
    for i in range(7):
        c.line(0.64, 0.74 - 0.12 + i * 0.04, 0.68, 0.74 - 0.12 + i * 0.04, 0.003, (0.45, 0.47, 0.52), 0.5)
    # needle bar, presser foot, needle
    c.line(-0.50, 0.50, -0.50, 0.265, 0.016, (0.74, 0.76, 0.82), 1.0)
    c.line(-0.495, 0.50, -0.495, 0.30, 0.004, WHITE, 0.6)
    c.rect(-0.50, 0.252, 0.060, 0.024, chrome, r=0.004, lift=0.1)
    c.line(-0.50, 0.26, -0.50, 0.218, 0.0045, (0.95, 0.95, 0.98), 1.0)
    c.rect(-0.62, 0.50, 0.04, 0.025, (0.5, 0.5, 0.55), lift=0.1)
    c.ellipse(-0.50, 0.46, 0.030, 0.014, (1.0, 0.92, 0.7), lift=0)                                                    # work light
    soft_disc(c, -0.50, 0.30, 0.18, 0.12, (1.0, 0.9, 0.6), 0.45, 1.4, add=True)
    # thread spool on top and the thread path
    c.line(0.04, 0.88, 0.04, 0.97, 0.007, chrome, 1.0)
    craft.cylinder(c, 0.04, 0.89, 0.050, 0.075, scale(acc2, 1.2), scale(acc2, 0.6), scale(acc2, 0.9), lip=False)
    c.ellipse(0.04, 0.965, 0.050, 0.020, (0.85, 0.7, 0.45), lift=0.1)
    c.rect(0.04, 0.89, 0.108, 0.010, (0.8, 0.66, 0.4), lift=0)
    c.rect(0.04, 0.965, 0.108, 0.010, (0.8, 0.66, 0.4), lift=0)
    craft.arc(c, -0.24, 0.96, 0.28, 0.06, 0, 180, 0.0025, mix(acc2, WHITE, 0.4), 0.95)
    c.line(-0.52, 0.94, -0.52, 0.75, 0.0025, mix(acc2, WHITE, 0.4), 0.95)
    c.line(-0.52, 0.52, -0.50, 0.30, 0.0025, mix(acc2, WHITE, 0.4), 0.95)
    # the fabric being stitched, draping off the bed in front
    pts = [(-0.74, 0.225), (-0.12, 0.225), (-0.16, 0.12), (-0.34, 0.075), (-0.60, 0.10), (-0.80, 0.07)]
    _gpoly(c, pts, scale(fab, 1.12), scale(fab, 0.66), 1)
    for i in range(5):
        c.line(-0.72 + i * 0.12, 0.22, -0.70 + i * 0.12 + rng.uniform(-0.03, 0.03), 0.10, 0.006, scale(fab, 0.55 if i % 2 else 1.25), 0.3)
    _stitch(c, (-0.50, 0.236), (-0.74, 0.236), 10, WHITE, 0.0035, 0.5, 0.95)
    _stitch(c, (-0.50, 0.236), (-0.12, 0.236), 8, (0.95, 0.92, 0.85), 0.0025, 0.5, 0.5)
    gloss(c, -0.38, 0.84, 0.30, 0.03, 0, 0.35)


@sprop("tl_fabric_rolls", aspect=1.2, fill=1.0)
def tl_fabric_rolls(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.43, 0.3, 0.25))
    acc2 = _pal(color, "accent2", (0.7, 0.4, 0.3))
    ao(c, 0.0, 0.0, 1.1, 0.14, 0.5)
    wood = (0.70, 0.50, 0.32)
    craft.hshade_box(c, 0.0, 0.5, 1.2, 1.0, scale(wood, 0.45), scale(wood, 0.28), r=0.01)
    for sgn in (-1, 0, 1):
        craft.hshade_box(c, sgn * 0.595 if sgn else 0.0, 0.5, 0.034, 1.0, scale(wood, 1.1), scale(wood, 0.7))
    for sgn in (-1, 1):
        pass
    c.rect(0.0, 0.5, 0.034, 1.0, scale(wood, 1.0), lift=0.05)
    for v in (0.012, 0.506, 0.99):
        craft.hshade_box(c, 0.0, v, 1.22, 0.034, scale(wood, 1.15), scale(wood, 0.72), r=0.004)
    cols = [mix(acc2, WHITE, 0.15), (0.20, 0.32, 0.52), (0.93, 0.88, 0.78), mix(acc, WHITE, 0.15), (0.80, 0.30, 0.38), (0.30, 0.45, 0.35)]
    for row, v0 in enumerate((0.030, 0.524)):
        for i, u in enumerate((-0.30, 0.30)):
            col = cols[(row * 2 + i) % len(cols)]
            r = 0.215
            cx, cy = u, v0 + r + 0.012
            c.ellipse(cx + 0.012, cy - 0.006, r, r, scale(col, 0.42), lift=0)                                       # roll body behind the end face
            c.ellipse(cx, cy, r, r, col, lift=0.12)
            for k in range(1, 7):                                                                                   # wound layers
                rr = r * (1.0 - k * 0.13)
                craft.arc(c, cx, cy, rr, rr, rng.uniform(0, 60), rng.uniform(250, 340), 0.0045, scale(col, 0.66 if k % 2 else 1.18), 0.7, 12)
            c.ellipse(cx, cy, r * 0.17, r * 0.17, (0.62, 0.48, 0.32), lift=0.1)
            c.ellipse(cx + 0.004, cy - 0.003, r * 0.10, r * 0.10, (0.12, 0.09, 0.07), lift=0)
            if (row + i) % 2 == 0:                                                                                  # printed dots
                _dots(c, 14, cx - r * 0.8, cx + r * 0.8, cy - r * 0.8, cy + r * 0.8, mix(col, WHITE, 0.6), 0.008, 0.6)
            poly = [(cx - r * 0.55, cy - r * 0.78), (cx + r * 0.62, cy - r * 0.76), (cx + r * 0.7, cy - r * 1.05), (cx - r * 0.5, cy - r * 1.04)]
            _spoly(c, poly, scale(col, 0.9), 0, 0.1, 0.0)
            soft_disc(c, cx - r * 0.35, cy + r * 0.35, r * 0.5, r * 0.4, WHITE, 0.2, 1.3, add=True)
            soft_disc(c, cx + r * 0.5, cy - r * 0.4, r * 0.7, r * 0.7, BLACK, 0.10, 1.3)
    c.rect(0.0, 0.99, 0.5, 0.01, WHITE, lift=0, alpha=0.0)


@sprop("tl_dress_form", aspect=0.52, fill=1.0)
def tl_dress_form(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.43, 0.3, 0.25))
    ao(c, 0.0, 0.0, 0.46, 0.08, 0.5)
    for a in (-35, 90, 215):                                                  # wooden tripod
        x = 0.20 * math.cos(math.radians(a))
        c.line(0.0, 0.17, x, 0.012 - 0.01 * math.sin(math.radians(a)), 0.022, (0.55, 0.37, 0.22), 1.0)
    craft.hshade_box(c, 0.0, 0.34, 0.034, 0.34, (0.66, 0.46, 0.28), (0.34, 0.22, 0.13))
    c.ellipse(0.0, 0.18, 0.04, 0.025, (0.3, 0.2, 0.12), lift=0.1)
    c.ellipse(0.0, 0.50, 0.032, 0.02, GOLD, lift=0.15)                                                              # height knob
    linen = (0.88, 0.80, 0.66)
    _sym(c, 0.0, 0.93, [(0.045, 0.0), (0.150, 0.025), (0.175, 0.10), (0.150, 0.20), (0.115, 0.30), (0.140, 0.38), (0.165, 0.46), (0.120, 0.52)], linen,
         None, scale(linen, 0.62), 0.06)
    c.ellipse(0.0, 0.935, 0.055, 0.020, scale(linen, 0.8), lift=0.1)                                                 # neck cap
    craft.hshade_box(c, 0.0, 0.955, 0.050, 0.035, (0.45, 0.30, 0.18), (0.25, 0.17, 0.10))
    c.ellipse(0.0, 0.975, 0.025, 0.010, (0.5, 0.35, 0.2), lift=0.1)
    # muslin seam lines on the form
    c.line(0.0, 0.92, 0.0, 0.45, 0.004, scale(linen, 0.55), 0.5)
    craft.arc(c, 0.0, 0.64, 0.115, 0.08, 200, 340, 0.004, scale(linen, 0.55), 0.5)
    # half-stitched garment (accent coloured) draped over the left half, raw edge pinned
    g = mix(acc, (0.85, 0.28, 0.36), 0.5)
    _spoly(c, [(-0.17, 0.92), (-0.04, 0.925), (0.0, 0.84), (0.015, 0.56), (0.02, 0.28), (-0.10, 0.20), (-0.23, 0.26), (-0.19, 0.50), (-0.14, 0.66), (-0.19, 0.80)],
           g, 2, 0.10)
    for i in range(6):
        f = i / 5.0
        c.line(-0.17 + 0.18 * f, 0.88 - 0.1 * f, -0.19 + 0.20 * f, 0.26, 0.007, scale(g, 0.55 if i % 2 else 1.2), 0.22)
    _stitch(c, (0.015, 0.84), (0.025, 0.28), 14, (0.97, 0.95, 0.9), 0.004, 0.5, 0.95)                               # basting along the raw edge
    c.line(0.02, 0.62, 0.02, 0.60, 0.003, WHITE, 0.0)
    for i in range(7):                                                                                               # pins with coloured heads
        y = 0.80 - i * 0.075
        x = 0.0 + rng.uniform(-0.01, 0.01)
        c.line(x - 0.045, y + 0.012, x + 0.040, y - 0.006, 0.0032, (0.85, 0.86, 0.9), 1.0)
        c.ellipse(x + 0.045, y - 0.008, 0.0075, 0.0075, (0.95, 0.75, 0.2) if i % 2 else (0.9, 0.2, 0.3), lift=0.2)
    c.line(-0.10, 0.62, -0.02, 0.36, 0.004, (0.98, 0.97, 0.9), 0.7)                                                  # chalk marks
    c.line(-0.14, 0.44, -0.05, 0.44, 0.004, (0.98, 0.97, 0.9), 0.7)
    # tape measure round the neck, hanging over the chest
    c.line(-0.07, 0.915, -0.045, 0.60, 0.022, (0.96, 0.82, 0.22), 1.0)
    for i in range(14):
        t = i / 13.0
        c.line(-0.07 + 0.025 * t - 0.011, 0.915 - 0.315 * t, -0.07 + 0.025 * t + 0.011, 0.915 - 0.315 * t, 0.0022, (0.1, 0.1, 0.1), 0.8)
    craft.arc(c, 0.0, 0.915, 0.075, 0.03, 180, 360, 0.016, (0.96, 0.82, 0.22), 1.0)
    soft_disc(c, -0.09, 0.78, 0.06, 0.12, WHITE, 0.2, 1.2, add=True)


@sprop("tl_notions", aspect=2.4, fill=0.42)
def tl_notions(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.43, 0.3, 0.25))
    ao(c, 0.0, 0.0, 2.1, 0.22, 0.4)
    for i, col in enumerate((acc, (0.95, 0.75, 0.2), (0.25, 0.5, 0.6), (0.92, 0.9, 0.85))):                      # thread spools
        u = -0.90 + i * 0.18
        craft.cylinder(c, u, 0.02, 0.07, 0.20, scale(col, 1.2), scale(col, 0.6), scale(col, 0.9), lip=False)
        c.rect(u, 0.02, 0.145, 0.020, (0.82, 0.68, 0.42), lift=0.08)
        c.ellipse(u, 0.22, 0.07, 0.07 * TILT, (0.82, 0.68, 0.42), lift=0.1)
        c.rect(u, 0.22, 0.145, 0.018, (0.82, 0.68, 0.42), lift=0.08)
        for k in range(4):
            c.line(u - 0.065, 0.06 + k * 0.034, u + 0.065, 0.065 + k * 0.034, 0.003, scale(col, 0.8), 0.35)
    # measuring tape coil
    c.ellipse(0.02, 0.05, 0.18, 0.18 * TILT, (0.82, 0.68, 0.18), lift=0)
    craft.hshade_box(c, 0.02, 0.10, 0.36, 0.10, (0.98, 0.84, 0.25), (0.70, 0.55, 0.10))
    c.ellipse(0.02, 0.15, 0.18, 0.18 * TILT, (1.0, 0.88, 0.32), lift=0.1)
    c.ellipse(0.02, 0.152, 0.10, 0.10 * TILT, (0.9, 0.72, 0.15), lift=0)
    for i in range(13):
        c.line(-0.16 + i * 0.027, 0.12, -0.16 + i * 0.027, 0.095, 0.003, (0.1, 0.1, 0.1), 0.7)
    c.line(0.18, 0.11, 0.62, 0.04, 0.036, (0.98, 0.84, 0.25), 1.0)
    for i in range(13):
        c.line(0.20 + i * 0.033, 0.106 - i * 0.0055 + 0.012, 0.20 + i * 0.033, 0.106 - i * 0.0055 - 0.012, 0.0025, (0.1, 0.1, 0.1), 0.8)
    # pin cushion with pins
    c.ellipse(0.88, 0.07, 0.15, 0.065, (0.65, 0.1, 0.12), lift=0)
    c.ellipse(0.88, 0.10, 0.14, 0.11, (0.88, 0.2, 0.2), lift=0.15)
    gloss(c, 0.84, 0.15, 0.06, 0.03, 15, 0.5)
    for i in range(11):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.02, 0.10)
        x, y = 0.88 + math.cos(a) * r, 0.14 + math.sin(a) * r * 0.5
        c.line(x, y, x + rng.uniform(-0.04, 0.04), y + 0.09, 0.0035, (0.85, 0.86, 0.9), 1.0)
        c.ellipse(x + 0.0, y + 0.01, 0.008, 0.008, rng.choice([(0.95, 0.75, 0.2), (0.3, 0.55, 0.85), WHITE]), lift=0.2)
    for i in range(6):                                                                                              # buttons
        c.ellipse(-0.45 + i * 0.04, 0.012, 0.016, 0.010, rng.choice([WHITE, (0.9, 0.7, 0.3), (0.3, 0.3, 0.35)]), lift=0.15)


@sprop("tl_shears", aspect=2.6, fill=0.30)
def tl_shears(c, color):
    ao(c, 0.0, 0.0, 2.2, 0.28, 0.35)
    steel, dk = (0.88, 0.9, 0.94), (0.45, 0.47, 0.52)
    c.poly([(-0.20, 0.10), (1.10, 0.16), (1.12, 0.14), (-0.20, 0.08)], steel, lift=0.1)                              # blades
    c.poly([(-0.20, 0.10), (1.10, 0.15), (1.10, 0.13), (-0.20, 0.09)], dk, lift=0)
    c.poly([(-0.20, 0.13), (1.08, 0.205), (1.12, 0.19), (-0.20, 0.10)], mix(steel, WHITE, 0.2), lift=0.1)
    c.ellipse(-0.18, 0.10, 0.012, 0.010, (0.2, 0.2, 0.25), lift=0.2)
    for ang, off, col in ((16, 0.0, (0.82, 0.14, 0.14)), (-8, -0.0, (0.1, 0.1, 0.12))):                                 # loops
        pass
    c.ellipse(-0.72, 0.15, 0.20, 0.070, (0.82, 0.14, 0.14), lift=0.1)
    c.ellipse(-0.72, 0.15, 0.13, 0.042, (0.55, 0.10, 0.10), lift=0)
    c.ellipse(-0.70, 0.075, 0.20, 0.070, (0.10, 0.10, 0.12), lift=0.1)
    c.ellipse(-0.70, 0.075, 0.13, 0.042, (0.03, 0.03, 0.05), lift=0)
    c.line(-0.52, 0.14, -0.20, 0.11, 0.050, (0.82, 0.14, 0.14), 1.0)
    c.line(-0.50, 0.08, -0.20, 0.09, 0.050, (0.10, 0.10, 0.12), 1.0)
    gloss(c, 0.5, 0.17, 0.4, 0.015, 3, 0.5)


@niche("tailor", "Tailor & alterations", subjects=("tl_sewing_machine",),
       strong=("tailor", "tailoring", "stitching", "alterations", "ladies tailor", "boutique stitching", "sewing machine", "custom stitching", "garment alteration",
               "tailor shop", "दर्ज़ी", "दर्जी", "सिलाई", "सिलाई मशीन", "लेडीज़ टेलर", "darzi", "silai"),
       weak=("sewing", "measuring tape", "fabric", "bespoke", "blouse", "suit", "thread", "needle", "alteration"),
       accent="#6d4c41", mood="warm", group="retail", avoid=("kurti store", "saree boutique"))
def tailor(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.55)
    thread = [P.accent, (0.85, 0.25, 0.3), (0.95, 0.78, 0.2), (0.2, 0.5, 0.55), (0.92, 0.9, 0.84), (0.35, 0.3, 0.6), (0.3, 0.6, 0.35), (0.9, 0.5, 0.2)]
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        S.rect(0.60, 0.26, 1.30, 0.40, scale(mix(P.surface, P.wall_bot, 0.3), 0.85 * k), lift=0.0)                      # pegboard of thread spools
        for r_i in range(5):
            for i in range(14):
                u = 0.0 + i * 0.092
                S.rect(u, 0.10 + r_i * 0.075, 0.05, 0.05, scale(thread[(i * 3 + r_i * 5) % len(thread)], k), r=0.006, lift=0.0)
        S.window(1.55, 0.26, 0.46, 0.38, **_sky(dk))
        S.rect(1.55, 0.05, 6.0, 0.012, scale(P.wall_bot, 0.5), lift=0.0)
        S.pendant(0.95, -0.1, 0.14, (1.0, 0.85, 0.55))
        S.pendant(1.45, -0.1, 0.10, (1.0, 0.85, 0.55))
        S.bokeh(8, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.88, 0.6), (1.0, 0.78, 0.5)], 0.01, 0.035, 0.22)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.wood(-5.0, 0.58, 7.0, 2.6, mix(P.surface, WHITE, 0.08) if not dk else P.surface, plank=0.13, grain=0.5)
    S.rect(1.0, 0.58, 14.0, 0.008, scale(P.surface, 0.45), lift=0.0)
    _glow_floor(S, 1.1, 0.80, 1.2, 0.16, (1.0, 0.88, 0.6), 0.30 if dk else 0.18)
    # a length of cloth with chalked pattern pieces laid on the table
    cloth = mix(P.accent2, (0.92, 0.85, 0.72), 0.55)
    S.poly([(0.55, 0.88), (1.60, 0.88), (1.72, 1.02), (0.45, 1.02)], scale(cloth, 0.85), soft=1.0)
    S.poly([(0.58, 0.885), (1.57, 0.885), (1.68, 1.01), (0.49, 1.01)], cloth)
    S.line(0.80, 0.93, 1.05, 0.93, 0.004, (0.98, 0.97, 0.9), 0.7)
    S.line(1.05, 0.93, 1.10, 0.99, 0.004, (0.98, 0.97, 0.9), 0.7)
    S.line(1.10, 0.99, 0.78, 0.99, 0.004, (0.98, 0.97, 0.9), 0.7)
    S.line(0.78, 0.99, 0.80, 0.93, 0.004, (0.98, 0.97, 0.9), 0.7)
    S.put("tl_fabric_rolls", 0.56, 0.86, 0.32, color=P, framed=False)
    S.put("tl_dress_form", 1.46, 0.92, 0.56, color=P)
    S.put("tl_sewing_machine", 1.04, 0.94, 0.37, color=P, subject=True)
    S.put("tl_notions", 1.26, 1.01, 0.09, color=P, shadow=False)
    S.put("tl_shears", 0.80, 1.00, 0.08, color=P, shadow=False)
    S.focus("detail", 0.90, 0.78)
    with S.near(16.0):
        S.circle(0.55, 0.99, 0.05, mix(P.accent, WHITE, 0.25), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.9, 0.7), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ BIKE SHOWROOM
class _Side:
    """Mirror-aware drawing for side views: all x are multiplied by `d` (+1 faces right, -1 faces left)."""
    def __init__(self, c, d):
        self.c, self.d = c, d

    def ln(self, x0, y0, x1, y1, w, col, a=1.0):
        self.c.line(self.d * x0, y0, self.d * x1, y1, w, col, a)

    def el(self, x, y, a, b, col, lift=0.1, alpha=1.0, ang=0.0):
        self.c.ellipse(self.d * x, y, a, b, col, angle=ang * self.d, lift=lift, alpha=alpha)

    def sp(self, pts, col, smooth=2, lift=0.1, alpha=1.0):
        _spoly(self.c, [(self.d * x, y) for x, y in pts], col, smooth, lift, alpha)

    def hp(self, pts, left, right, k=0.07, smooth=1):
        _hpoly(self.c, [(self.d * x, y) for x, y in pts], left, right, k, 1.0, 1.0, smooth)

    def gl(self, x, y, a, b, ang=0.0, alpha=0.5):
        gloss(self.c, self.d * x, y, a, b, ang * self.d, alpha)

    def arc(self, x, y, a, b, a0, a1, w, col, alpha=1.0):
        if self.d < 0:
            a0, a1 = 180 - a1, 180 - a0
        craft.arc(self.c, self.d * x, y, a, b, a0, a1, w, col, alpha, 12)


def _wheel(s, x, y, r, rim=(0.55, 0.57, 0.62), disc=False, small=False):
    s.el(x, y, r, r, (0.04, 0.04, 0.05), lift=0.0)
    s.el(x, y, r * 0.93, r * 0.93, (0.10, 0.10, 0.12), lift=0.1)
    s.el(x, y, r * 0.72, r * 0.72, rim, lift=0.18)
    s.el(x, y, r * 0.62, r * 0.62, (0.07, 0.07, 0.09), lift=0.0)
    n = 5
    for i in range(n):
        a = math.radians(90 + 360 * i / n)
        s.ln(x + math.cos(a) * r * 0.10, y + math.sin(a) * r * 0.10, x + math.cos(a) * r * 0.64, y + math.sin(a) * r * 0.64, r * 0.13, rim, 1.0)
        s.ln(x + math.cos(a) * r * 0.10, y + math.sin(a) * r * 0.10 + 0.004, x + math.cos(a) * r * 0.62, y + math.sin(a) * r * 0.62 + 0.004, r * 0.04,
             mix(rim, WHITE, 0.5), 0.6)
    if disc:
        s.el(x, y, r * 0.52, r * 0.52, (0.72, 0.74, 0.78), lift=0.1, alpha=0.85)
        s.el(x, y, r * 0.44, r * 0.44, (0.07, 0.07, 0.09), lift=0.0, alpha=0.9)
    s.el(x, y, r * 0.15, r * 0.15, (0.7, 0.72, 0.78), lift=0.2)
    craft.arc(s.c, s.d * x, y, r * 0.96, r * 0.96, 50, 130, r * 0.05, (0.45, 0.45, 0.5), 0.6, 8)                # tyre sheen


@sprop("bk_motorcycle", aspect=1.95, fill=1.0)
def bk_motorcycle(c, color):
    rng = c.rng
    body, d = color if isinstance(color, tuple) and len(color) == 2 else ((0.8, 0.12, 0.12), 1)
    s = _Side(c, d)
    dark = (0.10, 0.10, 0.12)
    R = 0.215
    _wheel(s, -0.60, R + 0.01, R, (0.50, 0.52, 0.57))
    _wheel(s, 0.60, R + 0.01, R, (0.50, 0.52, 0.57), disc=True)
    s.ln(0.60, 0.225, 0.60, 0.20, 0.0, dark)
    s.ln(-0.60, R + 0.01, -0.60, R + 0.01, 0.0, dark)
    # swingarm, chain
    s.ln(-0.26, 0.30, -0.60, R + 0.01, 0.040, (0.30, 0.31, 0.35), 1.0)
    s.ln(-0.26, 0.31, -0.60, R + 0.02, 0.012, (0.65, 0.66, 0.7), 0.6)
    s.ln(-0.28, 0.34, -0.60, 0.25, 0.006, (0.78, 0.78, 0.8), 0.9)
    # engine block with fins, then exhaust
    s.hp([(-0.28, 0.25), (0.16, 0.25), (0.22, 0.34), (0.20, 0.52), (-0.18, 0.54), (-0.30, 0.42)], (0.52, 0.54, 0.60), (0.12, 0.13, 0.16), 0.06, 1)
    for i in range(5):
        s.ln(-0.04 + i * 0.045, 0.485, -0.04 + i * 0.045, 0.40 + 0.0, 0.008, (0.80, 0.82, 0.88), 0.45)
    s.el(-0.06, 0.31, 0.065, 0.065, (0.25, 0.26, 0.3), lift=0.1)
    s.el(-0.06, 0.31, 0.045, 0.045, (0.62, 0.64, 0.7), lift=0.15)
    s.sp([(0.0, 0.50), (0.20, 0.50), (0.24, 0.44), (0.02, 0.46)], (0.20, 0.21, 0.25), 1)
    s.ln(0.17, 0.30, 0.02, 0.17, 0.028, (0.62, 0.64, 0.70), 1.0)
    s.ln(0.02, 0.17, -0.40, 0.17, 0.036, (0.62, 0.64, 0.70), 1.0)
    s.ln(-0.40, 0.17, -0.80, 0.30, 0.046, (0.58, 0.60, 0.66), 1.0)
    s.ln(-0.80, 0.30, -0.90, 0.33, 0.052, (0.1, 0.1, 0.12), 1.0)
    s.ln(0.0, 0.18, -0.38, 0.18, 0.007, WHITE, 0.5)
    s.ln(-0.40, 0.19, -0.78, 0.31, 0.007, WHITE, 0.45)
    # trellis frame and the front fork
    s.ln(0.28, 0.66, -0.18, 0.40, 0.020, (0.3, 0.3, 0.34), 1.0)
    s.ln(0.30, 0.62, 0.08, 0.30, 0.020, (0.3, 0.3, 0.34), 1.0)
    s.ln(0.40, 0.74, 0.60, R + 0.01, 0.034, (0.78, 0.80, 0.86), 1.0)
    s.ln(0.405, 0.74, 0.60, R + 0.02, 0.010, WHITE, 0.55)
    s.ln(0.37, 0.76, 0.56, 0.30, 0.044, (0.12, 0.12, 0.15), 1.0)
    s.sp([(0.64, 0.19), (0.70, 0.17), (0.68, 0.26), (0.62, 0.27)], (0.85, 0.65, 0.2), 1)                          # brake caliper
    # rear shock with a coil spring, between the swingarm and the subframe
    s.ln(-0.40, 0.31, -0.30, 0.56, 0.026, (0.16, 0.16, 0.19), 1.0)
    for i in range(7):
        t = (i + 0.5) / 7.0
        s.ln(-0.40 + 0.10 * t - 0.018, 0.31 + 0.25 * t, -0.40 + 0.10 * t + 0.018, 0.31 + 0.25 * t + 0.01, 0.010, (0.95, 0.62, 0.15), 0.95)
    # one flowing body: tank, side panel and tail cowl are a single silhouette, the seat sits in it
    top = [(0.35, 0.73), (0.27, 0.80), (0.08, 0.835), (-0.10, 0.800), (-0.22, 0.730), (-0.34, 0.640), (-0.55, 0.628), (-0.72, 0.672), (-0.90, 0.745)]
    bot = [(-0.99, 0.735), (-0.98, 0.670), (-0.86, 0.585), (-0.62, 0.535), (-0.34, 0.525), (-0.14, 0.535), (0.06, 0.565), (0.24, 0.615), (0.34, 0.665)]
    s.hp(top + bot, scale(body, 1.20), scale(body, 0.58), 0.06, 2)
    s.hp([(-0.99, 0.706), (-0.98, 0.650), (-0.92, 0.612), (-0.90, 0.722)], scale(body, 0.95), scale(body, 0.5), 0.05, 1)
    s.sp([(-0.97, 0.655), (-0.86, 0.592), (-0.62, 0.543), (-0.34, 0.533), (-0.14, 0.543), (0.06, 0.573), (0.24, 0.622), (0.31, 0.655),
          (0.22, 0.650), (0.06, 0.612), (-0.14, 0.583), (-0.34, 0.575), (-0.62, 0.585), (-0.84, 0.628)], scale(body, 0.30), 1, 0.0, 0.42)       # belly shade: the body turns under
    s.ln(0.30, 0.640, 0.08, 0.585, 0.007, scale(body, 0.40), 0.7)                                                 # panel line under the tank
    s.ln(0.08, 0.585, -0.16, 0.560, 0.007, scale(body, 0.40), 0.7)
    s.ln(-0.34, 0.56, -0.62, 0.575, 0.006, scale(body, 0.42), 0.6)
    s.ln(-0.62, 0.575, -0.90, 0.640, 0.006, scale(body, 0.42), 0.6)
    s.sp([(-0.215, 0.725), (-0.34, 0.700), (-0.62, 0.690), (-0.745, 0.712), (-0.77, 0.670), (-0.62, 0.628), (-0.34, 0.622), (-0.205, 0.668)], (0.17, 0.14, 0.14), 1, 0.12)       # seat
    s.ln(-0.30, 0.693, -0.68, 0.700, 0.007, (0.62, 0.52, 0.46), 0.55)                                              # seat piping and highlight
    s.ln(-0.34, 0.650, -0.70, 0.666, 0.004, (0.60, 0.50, 0.44), 0.45)
    for i in range(8):                                                                                            # seat stitching
        s.ln(-0.27 - i * 0.055, 0.668 + 0.004 * i, -0.29 - i * 0.055, 0.668 + 0.004 * i, 0.003, (0.8, 0.7, 0.6), 0.5)
    s.ln(0.32, 0.745, 0.08, 0.80, 0.014, scale(body, 1.55), 0.55)                                                 # specular line along tank, seat edge and tail
    s.ln(0.08, 0.80, -0.10, 0.774, 0.012, scale(body, 1.45), 0.50)
    s.ln(-0.76, 0.690, -0.94, 0.712, 0.010, scale(body, 1.5), 0.55)
    s.ln(0.20, 0.755, -0.12, 0.745, 0.022, (0.97, 0.97, 0.97), 0.8)                                               # tank stripe, continues over the tail
    s.ln(-0.80, 0.690, -0.96, 0.705, 0.016, (0.97, 0.97, 0.97), 0.8)
    s.gl(-0.02, 0.79, 0.16, 0.030, 4, 0.7)
    s.gl(-0.62, 0.652, 0.14, 0.018, 6, 0.5)
    s.el(-0.34, 0.70, 0.004, 0.004, WHITE, lift=0.0, alpha=0.0)
    s.sp([(-0.99, 0.690), (-0.93, 0.688), (-0.93, 0.650), (-0.98, 0.648)], (1.0, 0.22, 0.15), 0, 0.15)             # tail light
    soft_disc(c, s.d * -1.0, 0.67, 0.05, 0.05, (1.0, 0.25, 0.15), 0.5, 1.6, add=True)
    s.ln(-0.60, 0.545, -0.90, 0.60, 0.012, (0.12, 0.12, 0.14), 0.9)                                               # tail underside + plate hanger
    # nose: sleek headlight cowl on the fork, screen, round LED eye
    s.hp([(0.36, 0.805), (0.50, 0.790), (0.58, 0.715), (0.57, 0.635), (0.47, 0.585), (0.36, 0.600)], scale(body, 1.14), scale(body, 0.6), 0.07, 2)
    s.ln(0.38, 0.79, 0.52, 0.775, 0.010, scale(body, 1.5), 0.55)
    s.el(0.535, 0.685, 0.058, 0.066, (0.08, 0.08, 0.10), lift=0.0)
    s.el(0.537, 0.685, 0.048, 0.055, (1.0, 0.97, 0.84), lift=0.1)
    s.el(0.540, 0.685, 0.028, 0.034, WHITE, lift=0.0)
    s.arc(0.537, 0.685, 0.048, 0.055, 120, 300, 0.006, (0.75, 0.78, 0.84), 0.9)
    soft_disc(c, s.d * 0.60, 0.685, 0.16, 0.11, (1.0, 0.95, 0.75), 0.5, 1.6, add=True)
    s.sp([(0.40, 0.81), (0.32, 0.93), (0.44, 0.88), (0.50, 0.79)], (0.75, 0.88, 0.98), 1, 0.05, 0.50)           # screen
    s.ln(0.34, 0.80, 0.25, 0.775, 0.018, (0.12, 0.12, 0.15), 1.0)                                                # handlebar, grip, mirror
    s.ln(0.255, 0.777, 0.20, 0.765, 0.026, (0.06, 0.06, 0.08), 1.0)
    s.ln(0.28, 0.80, 0.26, 0.89, 0.006, (0.2, 0.2, 0.22), 1.0)
    s.el(0.25, 0.905, 0.034, 0.022, (0.7, 0.75, 0.82), lift=0.1)
    s.hp([(0.42, 0.50), (0.74, 0.50), (0.81, 0.405), (0.74, 0.37), (0.44, 0.44)], scale(body, 1.1), scale(body, 0.58), 0.06, 1)             # front mudguard
    s.ln(0.45, 0.485, 0.74, 0.475, 0.008, scale(body, 1.5), 0.45)
    s.arc(-0.60, 0.226, R + 0.035, R + 0.035, 28, 152, 0.030, scale(body, 0.62), 1.0)                                    # rear hugger over the tyre
    s.arc(-0.60, 0.226, R + 0.045, R + 0.045, 40, 130, 0.008, scale(body, 1.4), 0.5)
    s.ln(-0.10, 0.19, -0.18, 0.12, 0.020, (0.18, 0.18, 0.2), 1.0)                                                # foot peg


@sprop("bk_scooter", aspect=1.45, fill=1.0)
def bk_scooter(c, color):
    body, d = color if isinstance(color, tuple) and len(color) == 2 else ((0.95, 0.95, 0.95), 1)
    s = _Side(c, d)
    R = 0.16
    dark = (0.12, 0.12, 0.14)
    _wheel(s, -0.50, R + 0.01, R, (0.75, 0.77, 0.82))
    _wheel(s, 0.52, R + 0.01, R, (0.75, 0.77, 0.82), disc=True)
    s.sp([(-0.64, 0.20), (-0.18, 0.17), (-0.04, 0.25), (-0.08, 0.36), (-0.60, 0.38)], scale(body, 0.55), 1, 0.08)           # engine and swingarm cover
    s.ln(-0.14, 0.215, -0.66, 0.19, 0.050, (0.84, 0.86, 0.90), 1.0)                                                     # chrome muffler
    s.ln(-0.14, 0.235, -0.62, 0.215, 0.010, WHITE, 0.7)
    s.el(-0.70, 0.19, 0.020, 0.030, (0.3, 0.3, 0.34), lift=0.1)
    # one rounded body: rear bulb with a wheel arch, floor and leg shield flow into each other
    top = [(-0.76, 0.42), (-0.76, 0.54), (-0.66, 0.65), (-0.44, 0.715), (-0.20, 0.70), (-0.06, 0.62), (0.0, 0.50), (0.06, 0.36)]
    bot = [(0.04, 0.30), (-0.10, 0.28), (-0.22, 0.31), (-0.30, 0.38), (-0.42, 0.415), (-0.58, 0.41), (-0.68, 0.36), (-0.76, 0.33)]
    s.hp(top + bot, scale(body, 1.12), scale(body, 0.62), 0.06, 2)
    s.hp([(-0.04, 0.34), (0.34, 0.34), (0.36, 0.25), (-0.02, 0.24)], scale(body, 0.78), scale(body, 0.42), 0.05, 1)         # floor board
    s.sp([(-0.04, 0.345), (0.32, 0.345), (0.32, 0.36), (-0.04, 0.36)], (0.14, 0.14, 0.16), 0, 0.1)
    for i in range(6):
        s.ln(0.0 + i * 0.055, 0.347, 0.0 + i * 0.055, 0.358, 0.005, (0.4, 0.4, 0.44), 0.7)
    s.hp([(0.12, 0.30), (0.34, 0.30), (0.42, 0.42), (0.46, 0.62), (0.46, 0.80), (0.38, 0.88), (0.31, 0.72), (0.24, 0.52), (0.14, 0.40)], scale(body, 1.15), scale(body, 0.60), 0.07, 2)
    s.ln(0.18, 0.40, 0.30, 0.74, 0.012, scale(body, 1.35), 0.45)                                                         # highlight on the apron
    s.ln(-0.70, 0.46, -0.10, 0.50, 0.007, scale(body, 0.45), 0.7)                                                        # side panel groove
    for i in range(4):                                                                                                    # cooling vents
        s.ln(-0.56 + i * 0.04, 0.555, -0.54 + i * 0.04, 0.60, 0.007, scale(body, 0.4), 0.7)
    s.el(-0.36, 0.56, 0.030, 0.030, (0.80, 0.16, 0.14), lift=0.15)                                                         # badge
    s.sp([(-0.62, 0.68), (-0.14, 0.715), (-0.08, 0.675), (-0.60, 0.64)], (0.15, 0.12, 0.12), 1, 0.12)                    # seat
    s.ln(-0.58, 0.69, -0.16, 0.71, 0.006, (0.70, 0.60, 0.54), 0.6)
    s.sp([(-0.80, 0.60), (-0.76, 0.58), (-0.72, 0.64), (-0.74, 0.70)], (0.30, 0.31, 0.35), 1, 0.08)                      # chrome grab rail
    s.ln(0.54, R + 0.01, 0.43, 0.80, 0.034, (0.78, 0.80, 0.86), 1.0)
    s.ln(0.545, R + 0.01, 0.44, 0.78, 0.010, WHITE, 0.5)
    s.hp([(0.38, 0.47), (0.74, 0.43), (0.78, 0.36), (0.62, 0.325), (0.42, 0.40)], scale(body, 1.12), scale(body, 0.6), 0.06, 1)  # front fender
    s.ln(0.43, 0.89, 0.40, 0.94, 0.026, dark, 1.0)                                                                       # handlebar and grip
    s.hp([(0.30, 0.90), (0.46, 0.96), (0.58, 0.90), (0.54, 0.80), (0.42, 0.78), (0.32, 0.82)], scale(body, 1.1), scale(body, 0.58), 0.06, 2)  # headset
    s.el(0.535, 0.865, 0.038, 0.046, (0.9, 0.9, 0.93), lift=0.1)
    s.el(0.538, 0.865, 0.028, 0.034, (1.0, 0.97, 0.84), lift=0.1)
    s.el(0.542, 0.865, 0.014, 0.017, WHITE, lift=0.0)
    soft_disc(c, s.d * 0.60, 0.865, 0.12, 0.09, (1.0, 0.95, 0.75), 0.5, 1.6, add=True)
    s.ln(0.40, 0.94, 0.36, 1.02, 0.006, (0.2, 0.2, 0.22), 1.0)
    s.el(0.35, 1.035, 0.034, 0.022, (0.7, 0.75, 0.82), lift=0.1)
    s.el(-0.77, 0.50, 0.012, 0.030, (1.0, 0.2, 0.15), lift=0.2)
    s.gl(-0.42, 0.68, 0.16, 0.020, 4, 0.6)
    s.gl(-0.62, 0.54, 0.06, 0.08, 20, 0.35)


@sprop("bk_plinth", aspect=2.2, fill=0.9)
def bk_plinth(c, color):
    acc = _pal(color, "accent", (0.78, 0.16, 0.16))
    w, t = 1.0, 0.30
    c.ellipse(0.0, 0.44, w, w * t, (0.03, 0.03, 0.04), lift=0)
    c.ellipse(0.0, 0.515, w * 0.985, w * t * 0.97, mix(acc, (0.1, 0.1, 0.12), 0.72), lift=0.1)
    c.ellipse(0.0, 0.527, w * 0.93, w * t * 0.91, (0.10, 0.10, 0.12), lift=0.08)
    craft.arc(c, 0.0, 0.515, w * 0.985, w * t * 0.97, 190, 350, 0.020, mix(acc, WHITE, 0.2), 0.95, 18)


@sprop("bk_helmets", aspect=2.0, fill=0.55)
def bk_helmets(c, color):
    acc = _pal(color, "accent", (0.78, 0.16, 0.16))
    ao(c, 0.0, 0.0, 1.5, 0.12, 0.4)
    craft.hshade_box(c, 0.0, 0.03, 1.80, 0.060, (0.30, 0.30, 0.34), (0.1, 0.1, 0.12), r=0.006)
    for u, col, st in ((-0.52, acc, (0.97, 0.97, 0.97)), (0.0, (0.95, 0.95, 0.96), acc), (0.52, (0.10, 0.10, 0.12), mix(acc, WHITE, 0.2))):
        c.ellipse(u + 0.02, 0.33, 0.24, 0.235, scale(col, 0.45), lift=0)
        c.ellipse(u, 0.34, 0.235, 0.230, scale(col, 1.0), lift=0.16)
        c.poly([(u - 0.12, 0.50), (u + 0.02, 0.54), (u + 0.16, 0.40), (u - 0.02, 0.20)], st, alpha=0.9, lift=0.05)
        c.poly([(u + 0.0, 0.40), (u + 0.24, 0.40), (u + 0.24, 0.28), (u + 0.02, 0.26)], (0.04, 0.05, 0.08), lift=0.2)            # visor
        c.poly([(u + 0.02, 0.38), (u + 0.20, 0.38), (u + 0.12, 0.34)], (0.5, 0.6, 0.8), alpha=0.55)
        c.ellipse(u + 0.14, 0.15, 0.09, 0.065, scale(col, 0.72), lift=0.1)                                                       # chin bar
        c.line(u + 0.20, 0.17, u + 0.26, 0.17, 0.02, (0.1, 0.1, 0.12), 0.9)
        soft_disc(c, u - 0.10, 0.50, 0.12, 0.06, WHITE, 0.45, 1.2, add=True)


@niche("bike-showroom", "Motorcycle / two-wheeler showroom", subjects=("bk_motorcycle",),
       strong=("bike showroom", "motorcycle showroom", "two wheeler dealer", "two wheeler showroom", "scooter showroom", "bike dealership", "motorcycle dealer",
               "motorbike showroom", "bike dealer", "bike showroom", "बाइक शोरूम", "बाइक की दुकान", "मोटरसाइकिल शोरूम", "टू व्हीलर", "दोपहिया", "दुपहिया", "two wheeler dealership"),
       weak=("motorcycle", "bike", "scooter", "motorbike", "helmet", "two wheeler", "dealership", "ride"),
       accent="#c62828", mood="dark", group="auto", avoid=("car showroom", "bicycle", "cycle shop", "कार शोरूम"))
def bike_showroom(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.7)
    sky_t, sky_b = ((0.05, 0.07, 0.16), (0.16, 0.18, 0.30)) if dk else ((0.55, 0.74, 0.92), (0.88, 0.94, 1.0))
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.gradient_rect(-0.5, 0.04, 2.6, 0.58, sky_t, sky_b)                                                  # glass front: dusk outside
        for i in range(16):                                                                                     # distant city lights through the glass
            u = -0.4 + i * 0.17 + S.rng.uniform(-0.03, 0.03)
            S.rect(u, 0.50 - S.rng.uniform(0, 0.08), 0.06, S.rng.uniform(0.06, 0.2), scale(mix(sky_b, P.accent_dark, 0.3), 0.8), lift=0.0, alpha=0.7)
            S.circle(u, 0.52 - S.rng.uniform(0.0, 0.1), 0.012, (1.0, 0.85, 0.5), alpha=0.8 if dk else 0.0, lift=0, soft=3.0)
        for u in (-0.2, 0.5, 1.2, 1.9):                                                                       # mullions
            S.rect(u, 0.31, 0.022, 0.56, scale(P.wall_bot, 0.4), lift=0.0)
        S.rect(1.0, 0.04, 6.0, 0.05, scale(P.wall_bot, 0.4), lift=0.0)
        S.rect(1.0, 0.59, 6.0, 0.03, scale(P.wall_bot, 0.4), lift=0.0)
        S.poly([(0.0, 0.08), (0.60, 0.08), (0.56, 0.24), (0.0, 0.24)], scale(P.accent, 0.9 * k))             # banner with a swoosh mark
        S.poly([(0.06, 0.22), (0.30, 0.12), (0.52, 0.12), (0.30, 0.16), (0.12, 0.22)], scale(WHITE, 0.95 * k))
        S.glow(0.30, 0.16, 0.5, P.accent, 0.20 if not dk else 0.32)
        for u in (0.45, 0.95, 1.45):                                                                          # spot lights
            S.glow(u, 0.01, 0.20, (1.0, 0.97, 0.9), 0.55 if not dk else 0.75)
            S.glow(u, 0.25, 0.42, (1.0, 0.95, 0.85), 0.07 if dk else 0.05)
        S.rect(1.12, 0.32, 1.30, 0.56, (0.10, 0.11, 0.14) if dk else (0.22, 0.23, 0.27), r=0.01, lift=0.0)      # backlit brand panel behind the hero bike
        S.gradient_rect(0.50, 0.06, 1.74, 0.58, scale(P.accent, 0.30 * k), (0.03, 0.03, 0.05), alpha=0.40)
        for dx in (-0.62, 0.62):
            S.rect(1.12 + dx, 0.32, 0.014, 0.56, mix(P.accent, WHITE, 0.6), lift=0.0, alpha=0.9)
        S.rect(1.12, 0.045, 1.30, 0.014, mix(P.accent, WHITE, 0.6), lift=0.0, alpha=0.9)
        S.glow(1.12, 0.40, 0.70, P.accent, 0.16 if dk else 0.08)
        S.floor(0.60, mix(P.floor_top, (0.12, 0.12, 0.14), 0.4), mix(P.floor_bot, (0.06, 0.06, 0.07), 0.4))
    fa = (0.30, 0.31, 0.34) if not dk else (0.09, 0.09, 0.11)
    fb = (0.36, 0.37, 0.40) if not dk else (0.06, 0.06, 0.08)
    S.tiles(-5.0, 0.60, 7.0, 2.6, fa, fb, 0.36)
    for _ in range(4):                                                                                         # polished-floor reflections of the ceiling spots
        u0 = S.rng.uniform(0.2, 1.9)
        S.soft(u0, S.rng.uniform(0.66, 1.1), S.rng.uniform(0.03, 0.07), S.rng.uniform(0.05, 0.14), (1.0, 0.95, 0.88), 0.10 if dk else 0.06, 1.5, add=True)
    S.rect(1.0, 0.60, 14.0, 0.007, scale(fa, 0.5), lift=0.0)
    S.soft(1.05, 0.93, 0.85, 0.17, mix(P.accent, WHITE, 0.4), 0.34 if dk else 0.16, 1.5, add=True)
    S.put("bk_helmets", 0.62, 0.50, 0.12, color=P, shadow=False, framed=False)
    # background row: a black bike and a white scooter parked behind and partly hidden by the hero
    S.put("bk_motorcycle", 0.58, 0.80, 0.27, color=((0.17, 0.17, 0.20), -1), shadow_alpha=0.4, framed=False)
    S.put("bk_scooter", 1.66, 0.84, 0.25, color=((0.94, 0.94, 0.95), -1), shadow_alpha=0.4, framed=False)
    S.soft(1.1, 0.70, 1.5, 0.22, (0.0, 0.0, 0.02), 0.30 if dk else 0.14, 1.4)                                    # depth haze: the back row sits in shade
    S.put("bk_plinth", 1.05, 0.96 + 0.5 * 0.50 / 0.9, 0.50, color=P, shadow=False, framed=False)
    S.put("bk_motorcycle", 1.05, 0.96, 0.52, color=(P.accent, 1), subject=True, shadow_alpha=0.45)
    S.focus("detail", 1.0, 0.70)
    with S.near(16.0):
        S.circle(0.55, 0.99, 0.05, mix(P.accent, WHITE, 0.2), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.9, 0.85), alpha=0.25, lift=0, soft=6.0)


# ================================================================================================ POTTERY STUDIO
CLAY = (0.60, 0.42, 0.32)


def _profile(c, cu, v0, h, prof, col, left=None, right=None, k=0.06, ridges=0, rim=None):
    """A turned vessel from a radius profile [(t, radius)] (t 0 = foot, 1 = lip): shaded cylinder-like body with an opening at the top."""
    pts = [(cu + r, v0 + t * h) for t, r in prof] + [(cu - r, v0 + t * h) for t, r in reversed(prof)]
    _hpoly(c, pts, left or scale(col, 1.14), right or scale(col, 0.58), k, 1.0, 1.0, 1)
    rl = prof[-1][1]
    c.ellipse(cu, v0 + h, rl, rl * 0.30, scale(col, 0.62), lift=0.05)
    c.ellipse(cu, v0 + h - 0.002, rl * 0.78, rl * 0.22, scale(col, 0.30), lift=0.0)
    c.ellipse(cu - rl * 0.1, v0 + h + 0.003, rl * 0.98, rl * 0.28, scale(col, 1.2), lift=0.0, alpha=0.0)
    for i in range(ridges):                                                                                    # throwing rings
        t = (i + 0.7) / (ridges + 0.4)
        r = max(rr for tt, rr in prof if tt <= t) if t < 1 else rl
        rad = _interp(prof, t)
        craft.arc(c, cu, v0 + t * h, rad, rad * 0.22, 190, 350, 0.0035, scale(col, 0.62 if i % 2 else 1.25), 0.55, 8)


def _interp(prof, t):
    for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
        if t0 <= t <= t1:
            return r0 + (r1 - r0) * (t - t0) / max(1e-6, t1 - t0)
    return prof[-1][1]


def _hand(c, u, v, ang, left, col=(0.88, 0.70, 0.58)):
    """A forearm, palm and four curled fingers (angle in degrees, 0 = pointing right), wet with clay slip."""
    rng = c.rng
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    sk = col if left else scale(col, 0.84)
    c.line(u - 0.30 * ca, v - 0.30 * sa, u, v, 0.105, sk, 1.0)
    c.line(u - 0.28 * ca, v - 0.28 * sa + 0.02, u - 0.02 * ca, v - 0.02 * sa + 0.02, 0.020, mix(sk, WHITE, 0.3), 0.35)
    c.ellipse(u + 0.03 * ca, v + 0.03 * sa, 0.085, 0.07, sk, lift=0.1)
    for i in range(4):
        off = (i - 1.5) * 0.034
        fx, fy = u + 0.08 * ca - off * sa, v + 0.08 * sa + off * ca
        c.line(fx, fy, fx + 0.075 * ca, fy + 0.075 * sa - 0.012, 0.030, scale(sk, 0.95), 1.0)
        c.ellipse(fx + 0.085 * ca, fy + 0.085 * sa - 0.012, 0.016, 0.016, scale(sk, 0.9), lift=0.1)
    for _ in range(12):                                                                                       # wet clay slip smears
        x = u + rng.uniform(-0.22, 0.1) * ca - rng.uniform(-0.04, 0.04) * sa
        y = v + rng.uniform(-0.22, 0.1) * sa + rng.uniform(-0.04, 0.04) * ca
        c.ellipse(x, y, rng.uniform(0.012, 0.03), rng.uniform(0.007, 0.014), (0.52, 0.38, 0.30), lift=0, alpha=0.55)
    soft_disc(c, u - 0.1 * ca, v + 0.03, 0.12, 0.03, WHITE, 0.35, 1.2, add=True)


@sprop("po_wheel", aspect=1.45, fill=1.0)
def po_wheel(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.63, 0.53, 0.5))
    ao(c, 0.0, 0.0, 1.2, 0.20, 0.55)
    steel = (0.50, 0.55, 0.60)
    for sgn in (-1, 1):                                                                                      # frame legs
        craft.hshade_box(c, sgn * 0.36, 0.20, 0.070, 0.40, scale(steel, 1.1), scale(steel, 0.5))
        c.ellipse(sgn * 0.36, 0.012, 0.12, 0.12 * TILT, (0.15, 0.16, 0.2), lift=0)
    craft.hshade_box(c, 0.0, 0.33, 0.80, 0.14, scale(steel, 1.05), scale(steel, 0.52), r=0.02)               # motor housing
    c.rect(0.0, 0.33, 0.56, 0.012, scale(steel, 1.4), lift=0, alpha=0.7)
    c.ellipse(-0.28, 0.33, 0.026, 0.026, (0.9, 0.3, 0.2), lift=0.2)
    c.line(0.30, 0.30, 0.60, 0.07, 0.014, (0.1, 0.1, 0.12), 0.95)                                            # cable to the foot pedal
    craft.hshade_box(c, 0.62, 0.035, 0.26, 0.05, (0.2, 0.2, 0.24), (0.06, 0.06, 0.08), r=0.012)
    c.poly([(0.52, 0.06), (0.74, 0.06), (0.70, 0.095), (0.54, 0.095)], (0.3, 0.3, 0.34), lift=0.1)
    # splash pan
    c.ellipse(0.0, 0.40, 0.66, 0.66 * 0.36, scale(steel, 0.45), lift=0)
    c.ellipse(0.0, 0.425, 0.65, 0.65 * 0.35, scale(steel, 1.15), lift=0.1)
    c.ellipse(0.0, 0.43, 0.60, 0.60 * 0.34, (0.42, 0.32, 0.27), lift=0.05)                                    # slip-filled well
    c.ellipse(-0.05, 0.435, 0.50, 0.50 * 0.30, (0.50, 0.38, 0.32), lift=0.0, alpha=0.6)
    soft_disc(c, -0.25, 0.44, 0.30, 0.06, WHITE, 0.25, 1.3, add=True)
    for _ in range(14):                                                                                       # slip splashes
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0.2, 0.55)
        c.ellipse(math.cos(a) * r, 0.43 + math.sin(a) * r * 0.30, rng.uniform(0.01, 0.025), rng.uniform(0.005, 0.012), (0.62, 0.48, 0.40), lift=0, alpha=0.6)
    # wheel head
    c.ellipse(0.0, 0.455, 0.33, 0.33 * 0.36, scale(steel, 0.5), lift=0)
    c.ellipse(0.0, 0.48, 0.32, 0.32 * 0.35, (0.74, 0.77, 0.82), lift=0.14)
    for r in (0.24, 0.16):
        craft.arc(c, 0.0, 0.48, r, r * 0.35, 190, 350, 0.004, (0.45, 0.47, 0.52), 0.6, 10)
    # the vessel being thrown, with throwing rings
    prof = [(0.0, 0.17), (0.07, 0.19), (0.25, 0.235), (0.42, 0.22), (0.60, 0.17), (0.78, 0.115), (0.92, 0.108), (1.0, 0.125)]
    _profile(c, 0.0, 0.50, 0.42, prof, CLAY, (0.74, 0.54, 0.42), (0.34, 0.22, 0.17), 0.05, 10)
    soft_disc(c, -0.10, 0.76, 0.05, 0.17, WHITE, 0.36, 1.2, add=True)
    soft_disc(c, 0.09, 0.66, 0.06, 0.16, BLACK, 0.18, 1.3)
    # two wet hands shaping the vase (left cups the belly, right pinches the neck)
    _hand(c, -0.20, 0.62, 18, True)
    _hand(c, 0.20, 0.80, 162, False)
    for i in range(4):                                                                                        # slip dripping down the vase
        x = -0.12 + i * 0.07
        c.line(x, 0.72 - i * 0.02, x + 0.004, 0.62 - i * 0.04, 0.007, (0.78, 0.62, 0.52), 0.5)
    c.ellipse(0.17, 0.43, 0.014, 0.011, (0.55, 0.75, 0.9), lift=0.2, alpha=0.7)


def _glaze_vase(c, u, v, h, w, kind, col, band=None):
    rng = c.rng
    if kind == "moon":
        prof = [(0.0, w * 0.45), (0.10, w * 0.62), (0.40, w), (0.62, w * 0.82), (0.82, w * 0.36), (0.94, w * 0.30), (1.0, w * 0.36)]
    elif kind == "tall":
        prof = [(0.0, w * 0.55), (0.18, w * 0.78), (0.55, w * 0.72), (0.88, w * 0.42), (0.95, w * 0.32), (1.0, w * 0.40)]
    elif kind == "jar":
        prof = [(0.0, w * 0.60), (0.12, w * 0.78), (0.60, w * 0.80), (0.82, w * 0.62), (0.88, w * 0.40), (1.0, w * 0.42)]
    else:
        prof = [(0.0, w * 0.50), (0.2, w * 0.86), (0.62, w * 0.92), (0.92, w * 0.62), (1.0, w * 0.64)]
    _profile(c, u, v, h, prof, col, None, None, 0.07, 0)
    if band:
        for t in (0.30, 0.36):
            rad = _interp(prof, t)
            craft.arc(c, u, v + h * t, rad, rad * 0.24, 190, 350, 0.007, band, 0.9, 8)
    for _ in range(10):                                                                                       # glaze specks
        t = rng.uniform(0.1, 0.8)
        rad = _interp(prof, t)
        c.ellipse(u + rng.uniform(-0.8, 0.8) * rad, v + h * t, 0.004, 0.003, scale(col, rng.choice([0.55, 1.35])), lift=0, alpha=0.55)
    rad = _interp(prof, 0.55)
    soft_disc(c, u - rad * 0.45, v + h * 0.58, rad * 0.16, h * 0.28, WHITE, 0.55, 1.2, add=True)
    soft_disc(c, u + rad * 0.55, v + h * 0.4, rad * 0.3, h * 0.35, BLACK, 0.15, 1.3)


def _bowl(c, u, v, r, col, inner=None):
    hh = r * 0.55
    _hpoly(c, [(u - r, v + hh), (u + r, v + hh), (u + r * 0.82, v + hh * 0.35), (u + r * 0.40, v), (u - r * 0.40, v), (u - r * 0.82, v + hh * 0.35)],
           scale(col, 1.14), scale(col, 0.58), 0.06, 1.0, 1)
    c.ellipse(u, v + hh, r, r * 0.30, scale(col, 0.7), lift=0.05)
    c.ellipse(u, v + hh - 0.002, r * 0.88, r * 0.24, inner or scale(col, 0.42), lift=0.0)
    soft_disc(c, u - r * 0.4, v + hh * 0.55, r * 0.2, hh * 0.3, WHITE, 0.5, 1.2, add=True)


@sprop("po_shelf", aspect=1.3, fill=1.0)
def po_shelf(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.63, 0.53, 0.5))
    ao(c, 0.0, 0.0, 1.2, 0.12, 0.5)
    wood = (0.62, 0.44, 0.28)
    craft.hshade_box(c, 0.0, 0.5, 1.30, 1.0, scale(wood, 0.40), scale(wood, 0.25), r=0.006)
    for sgn in (-1, 1):
        craft.hshade_box(c, sgn * 0.64, 0.5, 0.040, 1.0, scale(wood, 1.1), scale(wood, 0.68))
    sh = (0.015, 0.345, 0.675, 0.985)
    for v in sh:
        craft.hshade_box(c, 0.0, v, 1.30, 0.032, scale(wood, 1.18), scale(wood, 0.74), r=0.004)
    teal, ochre, cream, navy, terra, black = (0.25, 0.58, 0.55), (0.88, 0.62, 0.20), (0.93, 0.89, 0.80), (0.14, 0.22, 0.45), (0.76, 0.40, 0.25), (0.14, 0.14, 0.16)
    rows = [[("jar", cream, 0.27, 0.15, terra, -0.45), ("moon", teal, 0.30, 0.17, None, -0.10), ("bowl", ochre, 0.0, 0.17, None, 0.22), ("tall", navy, 0.31, 0.12, cream, 0.48)],
            [("tall", terra, 0.31, 0.12, cream, -0.48), ("bowl", teal, 0.0, 0.18, None, -0.15), ("jar", black, 0.27, 0.15, ochre, 0.18), ("moon", cream, 0.29, 0.15, navy, 0.48)],
            [("moon", ochre, 0.30, 0.17, None, -0.42), ("tall", teal, 0.31, 0.12, None, -0.12), ("bowl", cream, 0.0, 0.18, None, 0.18), ("jar", navy, 0.26, 0.15, cream, 0.48)]]
    for r_i, row in enumerate(rows):
        v0 = sh[r_i] + 0.020
        for kind, col, h, w, band, u in row:
            if kind == "bowl":
                _bowl(c, u, v0, w, col)
                _bowl(c, u + 0.0, v0 + 0.105, w * 0.7, scale(col, 0.9)) if r_i == 1 and u > 0 else None
            else:
                _glaze_vase(c, u, v0, h, w, kind, col, band)
        soft_disc(c, 0.0, v0 - 0.005, 0.62, 0.03, BLACK, 0.3, 1.4)
    soft_disc(c, -0.5, 0.98, 0.5, 0.04, WHITE, 0.15, 1.4, add=True)


@sprop("po_clay_tools", aspect=2.3, fill=0.45)
def po_clay_tools(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 2.0, 0.25, 0.5)
    wood = (0.62, 0.44, 0.28)
    craft.hshade_box(c, 0.0, 0.08, 2.0, 0.16, scale(wood, 1.05), scale(wood, 0.62), r=0.01)                    # wooden crate
    for i in range(4):
        c.rect(0.0, 0.03 + i * 0.04, 1.96, 0.005, scale(wood, 0.5), lift=0, alpha=0.6)
    c.poly([(-1.0, 0.16), (1.0, 0.16), (1.06, 0.20), (-0.94, 0.20)], scale(wood, 1.2), lift=0.05)
    # block of clay in plastic and a thrown-off ball
    craft.hshade_box(c, -0.62, 0.30, 0.50, 0.20, (0.60, 0.46, 0.38), (0.34, 0.25, 0.20), r=0.02)
    c.poly([(-0.87, 0.40), (-0.37, 0.40), (-0.30, 0.44), (-0.80, 0.44)], (0.70, 0.55, 0.45), lift=0.05)
    c.line(-0.80, 0.34, -0.40, 0.33, 0.010, (0.2, 0.15, 0.12), 0.8)                                            # wire-cut line
    c.ellipse(-0.20, 0.25, 0.10, 0.09, (0.58, 0.42, 0.34), lift=0.14)
    gloss(c, -0.23, 0.29, 0.03, 0.02, 10, 0.5)
    # ribs, loop tools, sponge, needle tool
    c.ellipse(0.12, 0.23, 0.12, 0.05, (0.72, 0.55, 0.30), lift=0.12)
    c.ellipse(0.12, 0.235, 0.05, 0.02, (0.4, 0.3, 0.2), lift=0)
    for i, (x0, y0, x1, y1) in enumerate(((0.35, 0.22, 0.85, 0.30), (0.40, 0.19, 0.90, 0.24), (0.38, 0.27, 0.80, 0.37))):
        c.line(x0, y0, x1, y1, 0.026, scale(wood, 1.25 - 0.15 * i), 1.0)
        c.line(x0, y0 + 0.01, x1, y1 + 0.01, 0.006, mix(wood, WHITE, 0.5), 0.5)
    c.line(0.88, 0.30, 0.98, 0.33, 0.012, (0.7, 0.72, 0.78), 1.0)
    craft.arc(c, 0.98, 0.34, 0.05, 0.05, 0, 360, 0.006, (0.75, 0.77, 0.82), 1.0, 12)
    c.ellipse(1.12, 0.26, 0.15, 0.10, (0.90, 0.78, 0.30), lift=0.14)                                           # sponge
    for _ in range(16):
        c.ellipse(1.12 + rng.uniform(-0.12, 0.12), 0.26 + rng.uniform(-0.07, 0.07), rng.uniform(0.006, 0.014), rng.uniform(0.004, 0.008), (0.62, 0.5, 0.15), lift=0, alpha=0.8)
    gloss(c, 1.08, 0.31, 0.06, 0.03, 10, 0.5)
    for _ in range(5):
        c.ellipse(rng.uniform(-0.1, 0.5), 0.205, rng.uniform(0.01, 0.02), 0.006, (0.5, 0.38, 0.3), lift=0, alpha=0.6)


@niche("pottery", "Pottery studio", subjects=("po_wheel",),
       strong=("pottery studio", "ceramics", "pottery classes", "clay art", "potter", "pottery wheel", "ceramic studio", "pottery workshop", "kumhar", "कुम्हार",
               "मिट्टी के बर्तन", "मिट्टी", "पॉटरी", "सिरेमिक", "mitti ke bartan"),
       weak=("clay", "vase", "glaze", "kiln", "handmade", "terracotta", "bowls", "wheel thrown", "earthenware"),
       accent="#a1887f", mood="warm", group="retail", avoid=("tattoo", "painting class"))
def pottery(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.6)
    glaze = [(0.25, 0.58, 0.55), (0.88, 0.62, 0.20), (0.93, 0.89, 0.80), (0.14, 0.22, 0.45), (0.76, 0.40, 0.25), (0.55, 0.62, 0.45)]
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for i in range(18):                                                                                      # rough plaster blotches
            S.circle(S.rng.uniform(-0.4, 2.4), S.rng.uniform(0.0, 0.55), S.rng.uniform(0.08, 0.2), scale(P.wall_bot, S.rng.uniform(0.9, 1.05)), alpha=0.35, lift=0, soft=6.0)
        S.rect(0.50, 0.26, 0.40, 0.52, scale(P.surface, 0.5 * k), r=0.19, lift=0.0)                           # arched window
        S.rect(0.50, 0.26, 0.34, 0.46, (0.08, 0.1, 0.2) if dk else (0.88, 0.94, 1.0), r=0.16, lift=0.05)
        S.glow(0.50, 0.26, 0.55, P.light, 0.30 if not dk else 0.14)
        for r_i, v in enumerate((0.22, 0.40)):                                                                    # wall shelf of pots
            S.rect(1.55, v + 0.06, 0.80, 0.012, scale(P.surface, 0.55 * k), lift=0.0)
            for i in range(6):
                u = 1.22 + i * 0.12
                S.ellipse(u, v + 0.0, 0.04 + 0.01 * (i % 2), 0.055, scale(glaze[(i + r_i * 2) % len(glaze)], k), lift=0.0)
        S.pendant(1.05, -0.1, 0.18, (1.0, 0.85, 0.55))
        S.bokeh(7, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.88, 0.62)], 0.01, 0.035, 0.18)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.wood(-5.0, 0.60, 7.0, 2.6, mix(P.surface, (0.7, 0.65, 0.6), 0.35) if not dk else scale(P.surface, 0.8), plank=0.15, grain=0.3)
    S.rect(1.0, 0.60, 14.0, 0.008, scale(P.surface, 0.45), lift=0.0)
    if not dk:
        S.light_shaft(0.30, 0.62, 0.70, 0.62, 1.15, 1.02, 0.52, 1.02, P.light, 0.16)
    _glow_floor(S, 0.95, 0.86, 1.0, 0.15, (1.0, 0.88, 0.62), 0.32 if dk else 0.16)
    S.put("po_shelf", 1.44, 0.80, 0.44, color=P)
    S.put("po_clay_tools", 0.60, 0.98, 0.16, color=P)
    S.put("po_wheel", 1.00, 0.96, 0.50, color=P, subject=True)
    S.focus("detail", 1.00, 0.66)
    if dk:
        S.glow(1.00, 0.70, 0.35, (1.0, 0.85, 0.6), 0.16)
    with S.near(16.0):
        S.circle(0.58, 0.99, 0.05, mix(P.accent, WHITE, 0.25), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.9, 0.7), alpha=0.28, lift=0, soft=6.0)


# ================================================================================================ DESIGN STUDIO (analogue)
GRAPHITE = (0.20, 0.20, 0.26)
PAPER = (0.97, 0.95, 0.90)


def _el(c, u, v, a, col, w=0.007, alpha=0.9, a0=0, a1=360, k=0.42):
    craft.arc(c, u, v, a, a * k, a0, a1, w, col, alpha, 14)


def _rot(c, u, v, ang, pts, col, smooth=0, lift=0.06, alpha=1.0):
    r = math.radians(ang)
    ca, sa = math.cos(r), math.sin(r)
    _spoly(c, [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in pts], col, smooth, lift, alpha)


@sprop("ds_sketchbook", aspect=2.15, fill=0.46)
def ds_sketchbook(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.48, 0.12, 0.64))
    acc2 = _pal(color, "accent2", (0.75, 0.2, 0.55))
    ao(c, 0.0, 0.0, 2.0, 0.20, 0.5)
    c.poly([(-1.06, 0.0), (1.06, 0.0), (1.03, 0.030), (-1.03, 0.030)], scale(acc, 0.45), lift=0.05)                 # cover edge
    c.poly([(-1.04, 0.026), (1.04, 0.026), (1.0, 0.045), (-1.0, 0.045)], (0.92, 0.9, 0.85), lift=0.04)                # page block edge
    for i in range(5):
        c.line(-1.02, 0.030 + i * 0.0035, 1.02, 0.030 + i * 0.0035, 0.0014, (0.7, 0.68, 0.62), 0.5)
    _gpoly(c, [(-1.0, 0.045), (-0.03, 0.045), (-0.05, 0.40), (-0.90, 0.40)], PAPER, scale(PAPER, 0.86), 0)
    _gpoly(c, [(0.03, 0.045), (1.0, 0.045), (0.90, 0.40), (0.05, 0.40)], PAPER, scale(PAPER, 0.90), 0)
    soft_disc(c, 0.0, 0.22, 0.10, 0.20, BLACK, 0.34, 1.3)                                                           # gutter
    for u in (-0.03, 0.03):
        c.line(u, 0.05, u * 1.6, 0.39, 0.003, scale(PAPER, 0.7), 0.5)
    for i in range(4):                                                                                              # faint dot grid
        for j in range(8):
            c.ellipse(-0.90 + j * 0.105 + i * 0.01, 0.10 + i * 0.075, 0.0025, 0.0018, (0.65, 0.65, 0.7), lift=0, alpha=0.5)
    # left page: thumbnail logo sketches in a 3 x 2 grid
    cells = [(-0.78, 0.13), (-0.52, 0.13), (-0.27, 0.13), (-0.80, 0.29), (-0.54, 0.29), (-0.29, 0.29)]
    for i, (u, v) in enumerate(cells):
        c.rect(u, v, 0.20, 0.095, (0.9, 0.88, 0.84), lift=0, alpha=0.5)
        if i == 0:
            _el(c, u, v, 0.06, GRAPHITE, 0.006)
            c.ellipse(u + 0.012, v + 0.002, 0.026, 0.012, acc, lift=0, alpha=0.9)
        elif i == 1:
            _spoly(c, [(u - 0.05, v - 0.030), (u + 0.05, v - 0.030), (u, v + 0.036)], acc2, 0, 0.0, 0.9)
            _el(c, u, v, 0.034, GRAPHITE, 0.005)
        elif i == 2:
            craft.arc(c, u - 0.02, v, 0.05, 0.036, -60, 60, 0.006, GRAPHITE, 0.9)
            craft.arc(c, u + 0.02, v, 0.05, 0.036, 120, 240, 0.006, GRAPHITE, 0.9)
            c.ellipse(u, v, 0.012, 0.007, acc, lift=0, alpha=0.9)
        elif i == 3:
            pts = [(u + 0.055 * math.cos(math.radians(60 * k_)), v + 0.032 * math.sin(math.radians(60 * k_))) for k_ in range(7)]
            for p_, q_ in zip(pts, pts[1:]):
                c.line(p_[0], p_[1], q_[0], q_[1], 0.005, GRAPHITE, 0.9)
            c.line(u - 0.03, v, u + 0.03, v, 0.007, acc, 0.9)
        elif i == 4:
            for p_, q_ in (((-0.05, -0.03), (-0.05, 0.03)), ((-0.05, 0.03), (0.0, -0.01)), ((0.0, -0.01), (0.05, 0.03)), ((0.05, 0.03), (0.05, -0.03))):
                c.line(u + p_[0], v + p_[1], u + q_[0], v + q_[1], 0.007, GRAPHITE, 0.9)
        else:
            c.ellipse(u, v, 0.045, 0.022, acc, lift=0, alpha=0.85)
            c.line(u - 0.06, v, u + 0.06, v, 0.004, GRAPHITE, 0.8)
            c.line(u, v - 0.034, u, v + 0.034, 0.004, GRAPHITE, 0.8)
    for i in range(3):
        c.rect(-0.55, 0.355 - 0.0, 0.5 - i * 0.1, 0.004, (0.55, 0.55, 0.6), lift=0, alpha=0.0)
    c.line(-0.84, 0.36, -0.40, 0.36, 0.004, (0.55, 0.55, 0.6), 0.6)
    # right page: the refined mark with construction circles and guides
    for k_ in range(5):
        c.line(0.12 + k_ * 0.17, 0.06, 0.12 + k_ * 0.155, 0.38, 0.0018, (0.45, 0.65, 0.9), 0.35)
    for j in range(4):
        c.line(0.08, 0.10 + j * 0.08, 0.94 - j * 0.01, 0.10 + j * 0.08, 0.0018, (0.45, 0.65, 0.9), 0.35)
    _el(c, 0.52, 0.22, 0.30, (0.45, 0.65, 0.9), 0.003, 0.55)
    _el(c, 0.52, 0.22, 0.21, (0.45, 0.65, 0.9), 0.003, 0.55)
    c.ellipse(0.52, 0.22, 0.20, 0.085, acc, lift=0.06)
    c.ellipse(0.55, 0.23, 0.115, 0.048, PAPER, lift=0)
    _spoly(c, [(0.30, 0.15), (0.52, 0.28), (0.80, 0.14), (0.52, 0.20)], mix(acc2, WHITE, 0.15), 0, 0.06, 0.95)
    c.ellipse(0.52, 0.22, 0.045, 0.02, acc, lift=0.05)
    _el(c, 0.52, 0.22, 0.20, GRAPHITE, 0.004, 0.7)
    c.rect(0.52, 0.355, 0.50, 0.012, GRAPHITE, lift=0, alpha=0.5)
    # a pencil resting across the book and a ribbon bookmark
    c.line(0.50, 0.01, 0.82, 0.12, 0.030, (0.95, 0.75, 0.15), 1.0)
    c.line(0.50, 0.020, 0.82, 0.13, 0.008, (1.0, 0.92, 0.55), 0.6)
    _spoly(c, [(0.44, 0.0), (0.50, 0.01), (0.50, -0.01)], (0.9, 0.7, 0.5), 0, 0.0)
    c.line(0.82, 0.12, 0.90, 0.145, 0.026, (0.85, 0.35, 0.4), 1.0)
    c.line(-0.02, 0.0, -0.03, -0.0, 0.0, acc)
    soft_disc(c, -0.5, 0.36, 0.9, 0.05, WHITE, 0.2, 1.4, add=True)


@sprop("ds_swatch_fan", aspect=1.5, fill=1.0)
def ds_swatch_fan(c, color):
    acc = _pal(color, "accent", (0.48, 0.12, 0.64))
    ao(c, 0.0, 0.0, 0.9, 0.16, 0.5)
    cols = [(0.16, 0.16, 0.2), (0.15, 0.45, 0.8), (0.1, 0.65, 0.6), (0.55, 0.8, 0.25), (0.98, 0.82, 0.12), (0.98, 0.55, 0.12), (0.9, 0.25, 0.3), (0.85, 0.2, 0.6), acc,
            (0.30, 0.2, 0.7), (0.45, 0.75, 0.92)]
    n = len(cols)
    L, W = 0.90, 0.17
    for i, col in enumerate(cols):
        ang = -56 + 112.0 * i / (n - 1)
        pts = [(-W / 2, 0.0), (W / 2, 0.0), (W / 2, L), (-W / 2, L)]
        _rot(c, 0.0, 0.12, -ang, [(x, y) for x, y in pts], (0.96, 0.96, 0.95), 1, 0.05)
        _rot(c, 0.0, 0.12, -ang, [(-W / 2 + 0.008, L * 0.34), (W / 2 - 0.008, L * 0.34), (W / 2 - 0.008, L - 0.010), (-W / 2 + 0.008, L - 0.010)], col, 0, 0.10)
        r_ = math.radians(-ang)
        cx, cy = 0.12 * 0 - 0.0, 0.12
        px_, py_ = -math.sin(r_) * L * 0.20, 0.12 + math.cos(r_) * L * 0.20
        c.line(px_ - 0.04 * math.cos(r_), py_ - 0.04 * math.sin(r_), px_ + 0.04 * math.cos(r_), py_ + 0.04 * math.sin(r_), 0.006, (0.6, 0.6, 0.62), 0.8)
        tx, ty = -math.sin(r_) * L * 0.60 - W * 0.30 * math.cos(r_), 0.12 + math.cos(r_) * L * 0.60 - W * 0.30 * math.sin(r_)
        c.line(tx - 0.05 * math.sin(r_), ty + 0.05 * math.cos(r_), tx + 0.04 * math.sin(r_), ty - 0.04 * math.cos(r_), 0.0, WHITE, 0.0)
        soft_disc(c, -math.sin(r_) * L * 0.70 - 0.02, 0.12 + math.cos(r_) * L * 0.70, 0.03, 0.12, WHITE, 0.2, 1.3, add=True)
    c.ellipse(0.0, 0.12, 0.060, 0.045, (0.16, 0.16, 0.2), lift=0.1)                                                  # holder and rivet
    c.ellipse(0.0, 0.125, 0.028, 0.020, (0.8, 0.8, 0.84), lift=0.2)
    c.ellipse(0.0, 0.14, 0.01, 0.007, (0.4, 0.4, 0.45), lift=0)


@sprop("ds_poster", aspect=0.72, fill=1.0)
def ds_poster(c, color):
    acc = _pal(color, "accent", (0.48, 0.12, 0.64))
    acc2 = _pal(color, "accent2", (0.75, 0.2, 0.55))
    ao(c, 0.0, 0.0, 0.7, 0.07, 0.4)
    c.rect(0.02, 0.5, 0.72, 1.0, (0.0, 0.0, 0.0), alpha=0.22, lift=0)
    _gpoly(c, [(-0.36, 0.0), (0.36, 0.0), (0.36, 1.0), (-0.36, 1.0)], scale(acc, 0.62), scale(acc, 0.34), 0)
    c.rect(0.0, 0.5, 0.64, 0.92, (0.0, 0.0, 0.0), alpha=0.0, lift=0)
    c.ellipse(-0.05, 0.62, 0.26, 0.26, (0.98, 0.93, 0.82), lift=0.04)                                                 # big cream disc
    c.ellipse(0.04, 0.60, 0.18, 0.18, acc2, lift=0.05)
    _spoly(c, [(-0.30, 0.20), (0.26, 0.20), (-0.04, 0.50)], (0.98, 0.78, 0.12), 0, 0.08)
    c.rect(0.0, 0.88, 0.60, 0.05, (0.15, 0.7, 0.65), lift=0.05)
    for i in range(5):
        c.rect(-0.10 + (i % 2) * 0.03, 0.13 - i * 0.022, 0.40 - i * 0.04, 0.010, (0.98, 0.96, 0.92), lift=0, alpha=0.9)
    c.ellipse(-0.27, 0.12, 0.03, 0.03, (0.98, 0.55, 0.12), lift=0.1)
    c.rect(0.0, 0.5, 0.67, 0.95, WHITE, alpha=0.0, lift=0)
    craft.arc(c, -0.05, 0.62, 0.30, 0.30, 25, 150, 0.006, WHITE, 0.7, 12)
    for x, y in ((-0.33, 0.97), (0.33, 0.97)):                                                                        # pins
        c.ellipse(x, y, 0.016, 0.016, (0.9, 0.9, 0.3), lift=0.2)
        c.ellipse(x - 0.004, y + 0.004, 0.005, 0.005, WHITE, lift=0, alpha=0.8)
    c.poly([(-0.36, 1.0), (0.36, 1.0), (0.36, 0.97), (-0.36, 0.95)], WHITE, alpha=0.12)
    soft_disc(c, -0.20, 0.8, 0.12, 0.3, WHITE, 0.10, 1.3, add=True)


@sprop("ds_type_specimen", aspect=0.78, fill=1.0)
def ds_type_specimen(c, color):
    acc = _pal(color, "accent", (0.48, 0.12, 0.64))
    ao(c, 0.0, 0.0, 0.7, 0.07, 0.4)
    c.rect(0.02, 0.5, 0.78, 1.0, BLACK, alpha=0.22, lift=0)
    _gpoly(c, [(-0.39, 0.0), (0.39, 0.0), (0.39, 1.0), (-0.39, 1.0)], (0.99, 0.98, 0.95), (0.90, 0.88, 0.83), 0)
    for v in (0.86, 0.50, 0.38):                                                                                      # type guides: cap, x-height, baseline
        c.line(-0.34, v, 0.34, v, 0.003, mix(acc, WHITE, 0.45), 0.7)
    c.text("AG", 0.0, 0.52, 0.34, (0.10, 0.09, 0.12), 0.26)
    c.line(-0.30, 0.90, -0.30, 0.34, 0.003, mix(acc, WHITE, 0.5), 0.6)
    c.rect(0.0, 0.94, 0.64, 0.012, GRAPHITE, lift=0, alpha=0.8)
    for i, w_ in enumerate((0.62, 0.54, 0.60, 0.46)):
        c.rect(-0.34 + w_ / 2, 0.27 - i * 0.055, w_, 0.020 + 0.004 * (3 - i), (0.12, 0.12, 0.16), lift=0, alpha=0.85)
    c.ellipse(0.28, 0.05, 0.022, 0.022, acc, lift=0.1)
    c.poly([(-0.39, 1.0), (0.39, 1.0), (0.39, 0.97), (-0.39, 0.95)], WHITE, alpha=0.2)
    soft_disc(c, -0.2, 0.8, 0.15, 0.3, WHITE, 0.14, 1.3, add=True)


@sprop("ds_pencil_cup", aspect=0.9, fill=1.0)
def ds_pencil_cup(c, color):
    rng = c.rng
    acc = _pal(color, "accent", (0.48, 0.12, 0.64))
    ao(c, 0.0, 0.0, 0.50, 0.09, 0.5)
    items = [(-26, (0.95, 0.75, 0.15), 0.62, 0.024, "pencil"), (-15, (0.15, 0.45, 0.8), 0.74, 0.030, "marker"), (-6, (0.9, 0.25, 0.3), 0.66, 0.022, "pencil"),
             (4, (0.2, 0.2, 0.24), 0.80, 0.044, "brush"), (13, (0.1, 0.65, 0.6), 0.70, 0.030, "marker"), (23, (0.98, 0.55, 0.12), 0.60, 0.022, "pencil"),
             (31, acc, 0.52, 0.030, "marker")]
    for ang, col, L, w_, kind in items:
        r_ = math.radians(90 - ang)
        x0, y0 = 0.02 * math.sin(math.radians(ang)) * 2, 0.20
        x1, y1 = x0 + math.cos(r_) * L, y0 + math.sin(r_) * L
        c.line(x0, y0, x1, y1, w_, col, 1.0)
        c.line(x0 - 0.004, y0, x1 - 0.004, y1, w_ * 0.25, mix(col, WHITE, 0.5), 0.5)
        if kind == "pencil":
            c.line(x1, y1, x1 + math.cos(r_) * 0.07, y1 + math.sin(r_) * 0.07, w_ * 0.8, (0.9, 0.75, 0.55), 1.0)
            c.line(x1 + math.cos(r_) * 0.06, y1 + math.sin(r_) * 0.06, x1 + math.cos(r_) * 0.085, y1 + math.sin(r_) * 0.085, w_ * 0.35, col, 1.0)
        elif kind == "marker":
            c.line(x1 - math.cos(r_) * 0.06, y1 - math.sin(r_) * 0.06, x1, y1, w_ * 1.18, scale(col, 0.75), 1.0)
            c.line(x1, y1, x1 + math.cos(r_) * 0.028, y1 + math.sin(r_) * 0.028, w_ * 0.7, (0.12, 0.12, 0.14), 1.0)
        else:
            c.line(x1, y1, x1 + math.cos(r_) * 0.10, y1 + math.sin(r_) * 0.10, w_ * 0.9, (0.85, 0.82, 0.78), 1.0)
            c.ellipse(x1 + math.cos(r_) * 0.14, y1 + math.sin(r_) * 0.14, w_ * 0.6, 0.04, (0.12, 0.1, 0.1), lift=0.1)
    craft.cylinder(c, 0.0, 0.02, 0.21, 0.30, scale(acc, 1.25), scale(acc, 0.55), scale(acc, 0.7), lip=True)
    c.ellipse(0.0, 0.32, 0.17, 0.17 * TILT, scale(acc, 0.3), lift=0, alpha=0.0)
    c.rect(0.0, 0.14, 0.42, 0.014, mix(acc, WHITE, 0.55), lift=0, alpha=0.7)
    gloss(c, -0.12, 0.20, 0.025, 0.10, 6, 0.55)


@sprop("ds_markers", aspect=2.8, fill=0.30)
def ds_markers(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 2.4, 0.30, 0.4)
    # a clear ruler with ticks
    c.poly([(-1.2, 0.12), (0.2, 0.12), (0.22, 0.04), (-1.18, 0.04)], (0.82, 0.92, 0.98), alpha=0.55, lift=0.1)
    for i in range(24):
        c.line(-1.16 + i * 0.058, 0.115, -1.16 + i * 0.058, 0.10 if i % 2 else 0.085, 0.0025, (0.25, 0.3, 0.4), 0.8)
    cols = [(0.9, 0.25, 0.3), (0.98, 0.82, 0.12), (0.1, 0.65, 0.6), (0.15, 0.45, 0.8), (0.48, 0.12, 0.64), (0.98, 0.55, 0.12)]
    for i, col in enumerate(cols):                                                                                     # markers lying in a row
        u0, v0 = 0.20 + i * 0.015, 0.06 + i * 0.037
        c.line(u0, v0, u0 + 0.95, v0 + 0.02, 0.040, col, 1.0)
        c.line(u0, v0 + 0.008, u0 + 0.95, v0 + 0.028, 0.008, mix(col, WHITE, 0.5), 0.55)
        c.line(u0 + 0.62, v0 + 0.014, u0 + 0.95, v0 + 0.02, 0.046, scale(col, 0.7), 1.0)
        c.line(u0 - 0.03, v0 - 0.0, u0 + 0.0, v0, 0.022, (0.1, 0.1, 0.12), 1.0)
    c.line(-0.40, 0.20, 0.10, 0.215, 0.020, (0.95, 0.75, 0.15), 1.0)                                                   # pencil and eraser
    _spoly(c, [(-0.46, 0.195), (-0.40, 0.21), (-0.40, 0.19)], (0.9, 0.75, 0.55), 0, 0.0)
    craft.hshade_box(c, -0.80, 0.19, 0.22, 0.08, (0.95, 0.85, 0.85), (0.75, 0.62, 0.62), r=0.012)
    c.rect(-0.86, 0.19, 0.06, 0.082, (0.3, 0.4, 0.8), lift=0.1)


@niche("design-studio", "Graphic / brand design studio", subjects=("ds_sketchbook",),
       strong=("graphic design studio", "logo design", "brand identity", "branding studio", "illustrator", "poster design", "graphic designer", "brand design",
               "logo designer", "branding agency", "लोगो डिज़ाइन", "ग्राफिक डिज़ाइन", "ब्रांडिंग", "graphic design"),
       weak=("logo", "brand", "typography", "pantone", "sketchbook", "posters", "visual identity", "creative studio", "design"),
       accent="#7b1fa2", mood="light", group="retail", avoid=("website development", "web design", "interior", "app development"))
def design_studio(S):
    P = S.pal
    dk, k = _dark(S), _k(S, 0.6)
    pins = [P.accent, (0.98, 0.82, 0.12), (0.1, 0.65, 0.6), (0.9, 0.25, 0.3), (0.15, 0.45, 0.8), (0.98, 0.55, 0.12), (0.95, 0.93, 0.88)]
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.52)
        cork = scale(mix(P.surface, P.wall_bot, 0.4), 0.9 * k)
        S.rect(1.00, 0.24, 2.10, 0.40, cork, lift=0.0, alpha=0.6)                                                    # pinboard wall of work in progress
        for i in range(14):
            u = 0.0 + (i % 7) * 0.30 + S.rng.uniform(-0.02, 0.02)
            v = 0.15 + (i // 7) * 0.20
            w_, h_ = S.rng.uniform(0.14, 0.24), S.rng.uniform(0.14, 0.18)
            S.rect(u + 0.1, v, w_, h_, scale(pins[(i * 3) % len(pins)], k), lift=0.05)
            S.circle(u + 0.1 + w_ * 0.2, v + h_ * 0.1, 0.035, scale(pins[(i * 5 + 2) % len(pins)], k), lift=0.0)
        S.rect(1.0, 0.54, 8.0, 0.012, scale(P.wall_bot, 0.6), lift=0.0)
        S.pendant(0.62, -0.1, 0.12, (1.0, 0.92, 0.75), shade_w=0.09)
        S.pendant(1.40, -0.1, 0.10, (1.0, 0.92, 0.75), shade_w=0.09)
        S.bokeh(7, 0.0, 0.05, 2.0, 0.45, [(1.0, 0.92, 0.75), mix(P.accent, WHITE, 0.6)], 0.01, 0.03, 0.18)
        S.floor(0.52, P.floor_top, P.floor_bot)
    oak = mix(P.surface, (0.9, 0.82, 0.68), 0.35) if not dk else scale(P.surface, 0.9)
    S.wood(-5.0, 0.52, 7.0, 2.6, oak, plank=0.45, grain=0.4)
    S.rect(1.0, 0.52, 14.0, 0.010, scale(oak, 0.5), lift=0.0)
    S.soft(1.05, 0.80, 1.2, 0.18, (1.0, 0.96, 0.85), 0.30 if dk else 0.16, 1.5, add=True)
    S.put("ds_type_specimen", 0.66, 0.78, 0.30, color=P)
    S.put("ds_poster", 1.50, 0.74, 0.38, color=P)
    S.put("ds_pencil_cup", 1.14, 0.76, 0.19, color=P)
    S.put("ds_sketchbook", 0.90, 0.96, 0.25, color=P, subject=True)
    S.put("ds_swatch_fan", 1.43, 0.93, 0.24, color=P)
    S.put("ds_markers", 1.12, 1.0, 0.05, color=P, shadow=False, framed=False)
    S.focus("detail", 0.96, 0.86)
    with S.near(16.0):
        S.circle(0.58, 0.99, 0.05, mix(P.accent, WHITE, 0.25), alpha=0.35, lift=0, soft=6.0)
        S.circle(1.78, 0.2, 0.06, (1.0, 0.95, 0.85), alpha=0.28, lift=0, soft=6.0)
