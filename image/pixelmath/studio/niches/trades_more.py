"""More trade niches: painting, carpentry, AC repair, packers and movers, landscaping, welding, tyres, security systems."""
import colorsys
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, arc, disc, gloss, hshade_box, leaf, soft_disc
from ..niches import niche
from ..palette import hsv
from ..stage import sprop
from ...raster import mix, scale

METAL = (0.76, 0.78, 0.81)
STEEL = (0.70, 0.73, 0.77)
CARD = (0.70, 0.52, 0.34)
BRASS = (0.80, 0.62, 0.26)


# ====================================================================================================== shared helpers
def _prism(c, u, v, w, h, dx, dy, front, top=None, side=None, lift=0.07, r=0.0):
    """Oblique box: front face w x h with its base centre at (u, v); depth goes right and up by (dx, dy)."""
    x0, x1 = u - w / 2, u + w / 2
    top = top or mix(front, WHITE, 0.22)
    side = side or scale(front, 0.68)
    c.poly([(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], side, lift=lift)
    c.poly([(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, lift=0.04)
    c.rect(u, v + h / 2, w, h, front, lift=lift, r=r)


def _tube(c, u0, v0, u1, v1, w, base, hl=0.7):
    """A shiny tube between two points: dark body, lit core shifted to the key light, thin highlight."""
    c.line(u0, v0, u1, v1, w, scale(base, 0.58))
    c.line(u0 - w * 0.10, v0 + w * 0.12, u1 - w * 0.10, v1 + w * 0.12, w * 0.66, base)
    c.line(u0 - w * 0.20, v0 + w * 0.24, u1 - w * 0.20, v1 + w * 0.24, w * 0.18, mix(base, WHITE, hl), 0.85)


def _rot(pts, ang, ox=0.0, oy=0.0, sv=1.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(ox + x * ca - y * sa, oy + (x * sa + y * ca) * sv) for x, y in pts]


def _hue(P, shift, s=0.72, v=0.92):
    h = colorsys.rgb_to_hsv(*P.accent)[0]
    return hsv(h + shift, s, v)


def _bead(c, u, v, r, col):
    """A glossy droplet."""
    c.ellipse(u, v, r, r * 0.95, col, lift=0.18)
    soft_disc(c, u - r * 0.3, v + r * 0.3, r * 0.45, r * 0.35, WHITE, 0.7, 1.0, add=True)


def _spark(c, u, v, r, color=(1.0, 0.85, 0.5), alpha=0.9):
    soft_disc(c, u, v, r * 1.2, r * 1.2, color, alpha * 0.5, 1.6, add=True)
    c.line(u - r, v, u + r, v, r * 0.07, WHITE, alpha)
    c.line(u, v - r, u, v + r, r * 0.07, WHITE, alpha)
    c.line(u - r * 0.5, v - r * 0.5, u + r * 0.5, v + r * 0.5, r * 0.04, color, alpha * 0.7)
    c.line(u - r * 0.5, v + r * 0.5, u + r * 0.5, v - r * 0.5, r * 0.04, color, alpha * 0.7)


# ---- scan-line fill (fast for long diagonal shapes: the stage polygon cost grows with the bounding box)
def _blend(px, i, col, a):
    ia = 1.0 - a
    px[i] = px[i] * ia + col[0] * a
    px[i + 1] = px[i + 1] * ia + col[1] * a
    px[i + 2] = px[i + 2] * ia + col[2] * a


def _span(px, w, y, xa, xb, col, al):
    if xb <= 0 or xa >= w or xb <= xa:
        return
    xa, xb = max(0.0, xa), min(float(w), xb)
    il, ir = int(xa), int(xb)
    base = y * w
    if il == ir:
        _blend(px, (base + il) * 3, col, al * (xb - xa))
        return
    _blend(px, (base + il) * 3, col, al * (il + 1 - xa))
    n = ir - il - 1
    if n > 0:
        i = (base + il + 1) * 3
        if al >= 0.999:
            px[i:i + n * 3] = [col[0], col[1], col[2]] * n
        else:
            ia = 1.0 - al
            add = [col[0] * al, col[1] * al, col[2] * al] * n
            px[i:i + n * 3] = [a * ia + b for a, b in zip(px[i:i + n * 3], add)]
    if ir < w:
        _blend(px, (base + ir) * 3, col, al * (xb - ir))


def _scan(cv, pts, top, bot=None, alpha=1.0):
    bot = top if bot is None else bot
    n = len(pts)
    ys = [p[1] for p in pts]
    ymin, ymax = min(ys), max(ys)
    y0, y1 = max(0, int(math.floor(ymin))), min(cv.h - 1, int(math.ceil(ymax)))
    span = max(1.0, ymax - ymin)
    edges = []
    for i in range(n):
        xa, ya = pts[i]
        xb, yb = pts[(i + 1) % n]
        if ya == yb:
            continue
        if ya > yb:
            xa, ya, xb, yb = xb, yb, xa, ya
        edges.append((ya, yb, xa, (xb - xa) / (yb - ya)))
    for y in range(y0, y1 + 1):
        yc = y + 0.5
        xs = sorted([xa + (yc - ya) * sl for ya, yb, xa, sl in edges if ya <= yc < yb])
        if len(xs) < 2:
            continue
        t = min(1.0, max(0.0, (yc - ymin) / span))
        col = (top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t, top[2] + (bot[2] - top[2]) * t)
        al = alpha
        if y == y0 or y == y1:
            al *= max(0.0, min(1.0, (y0 + 1 - ymin) if y == y0 else (ymax - y1))) if y0 != y1 else 1.0
        for k in range(0, len(xs) - 1, 2):
            _span(cv.px, cv.w, y, xs[k], xs[k + 1], col, al)


def _qpoly(c, pts, color, lift=0.10, alpha=1.0):
    """Shaded polygon in unit coordinates, scan-line filled."""
    _scan(c.cv, [(c.X(u), c.Y(v)) for u, v in pts], scale(color, 1 + lift), scale(color, 1 - lift * 1.2), alpha)


# ====================================================================================================== painting
def _can(c, u, v, r, h, paint, drips, metal=METAL):
    """An open paint can with a paint surface, paper label and paint running down the front."""
    ao(c, u, v, r * 2.3, r * 0.9)
    hshade_box(c, u, v + h / 2, 2 * r, h, scale(metal, 1.08), scale(metal, 0.62))
    c.ellipse(u, v, r, r * TILT, scale(metal, 0.56), lift=0)
    hshade_box(c, u, v + h / 2 + 0.001, 2 * r, h, scale(metal, 1.08), scale(metal, 0.62))
    hshade_box(c, u, v + h * 0.30, 2 * r * 0.995, h * 0.40, (0.97, 0.95, 0.90), (0.70, 0.67, 0.63))
    c.rect(u - r * 0.05, v + h * 0.21, r * 1.25, h * 0.12, paint, r=0.008, lift=0.18)
    c.rect(u - r * 0.05, v + h * 0.38, r * 1.05, h * 0.018, (0.25, 0.25, 0.3), lift=0, alpha=0.55)
    c.rect(u - r * 0.15, v + h * 0.33, r * 0.8, h * 0.014, (0.25, 0.25, 0.3), lift=0, alpha=0.4)
    c.rect(u, v + h * 0.12, 2 * r, 0.007, scale(metal, 0.7), lift=0, alpha=0.8)
    c.rect(u, v + h * 0.87, 2 * r, 0.007, scale(metal, 0.7), lift=0, alpha=0.8)
    soft_disc(c, u + r * 0.75, v + h * 0.5, r * 0.45, h * 0.55, BLACK, 0.22, 1.3)
    gloss(c, u - r * 0.62, v + h * 0.55, r * 0.06, h * 0.42, 0, 0.55)
    # open top
    c.ellipse(u, v + h, r * 1.03, r * 1.03 * TILT, scale(metal, 1.1), lift=0.1)
    c.ellipse(u, v + h + 0.004, r * 0.94, r * 0.94 * TILT, scale(metal, 0.45), lift=0)
    c.ellipse(u, v + h - 0.002, r * 0.88, r * 0.88 * TILT, paint, lift=0.14)
    for k in range(3):
        arc(c, u + r * 0.1 * k, v + h, r * (0.3 + 0.2 * k), r * (0.3 + 0.2 * k) * TILT, 20 + k * 60, 140 + k * 50, 0.006, mix(paint, WHITE, 0.35), 0.55, 6)
    gloss(c, u - r * 0.3, v + h + r * 0.1, r * 0.4, r * 0.1, 0, 0.55)
    # paint running down the front
    for du, ln, wd in drips:
        x = u + du * r
        y0 = v + h - math.sqrt(max(0.0, 1 - du * du)) * r * TILT * 0.98
        c.ellipse(x, y0 + 0.002, wd * 0.9, 0.012, paint, lift=0.1)
        ln = min(ln, h * 0.40)
        c.rect(x, y0 - ln / 2, wd, ln, paint, r=wd / 2, lift=0.10)
        c.line(x - wd * 0.22, y0 - 0.004, x - wd * 0.22, y0 - ln * 0.9, wd * 0.18, mix(paint, WHITE, 0.55), 0.7)
        _bead(c, x, y0 - ln - wd * 0.2, wd * 0.62, paint)


@sprop("pt_cans", aspect=2.0, fill=0.70)
def pt_cans(c, P):
    rng = c.rng
    p1 = P.accent
    p2 = _hue(P, 0.50, 0.72, 0.90)
    p3 = _hue(P, 0.14, 0.85, 0.98)
    _can(c, -0.02, 0.10, 0.20, 0.50, p2, ((-0.55, 0.16, 0.05), (0.12, 0.26, 0.055), (0.62, 0.10, 0.04)))
    _can(c, -0.52, 0.04, 0.17, 0.36, p1, ((-0.45, 0.20, 0.05), (0.2, 0.30, 0.06), (0.7, 0.12, 0.04)))
    _can(c, 0.48, 0.0, 0.16, 0.30, p3, ((-0.3, 0.14, 0.05), (0.5, 0.20, 0.05)))
    # puddle of paint at the foot of the left can, and a stir stick across the tall can
    c.ellipse(-0.42, -0.015, 0.10, 0.026, p1, lift=0.12)
    gloss(c, -0.45, -0.008, 0.045, 0.008, 0, 0.7)
    c.line(-0.20, 0.64, 0.17, 0.57, 0.026, (0.80, 0.64, 0.42))
    c.line(0.10, 0.575, 0.17, 0.57, 0.026, p2)
    c.line(-0.20, 0.652, 0.12, 0.592, 0.007, mix((0.80, 0.64, 0.42), WHITE, 0.5), 0.7)
    # lid lying in front, with paint smears inside
    disc(c, 0.12, 0.0, 0.15, scale(METAL, 1.05), 0.34, 0.1)
    c.ellipse(0.12, 0.003, 0.115, 0.115 * 0.34, scale(METAL, 0.5), lift=0)
    c.ellipse(0.10, 0.004, 0.10, 0.10 * 0.34, p2, lift=0.1, alpha=0.9)
    gloss(c, 0.06, 0.01, 0.05, 0.008, 0, 0.6)
    for _ in range(8):
        c.circle(rng.uniform(-0.1, 0.5), rng.uniform(-0.03, 0.0), rng.uniform(0.004, 0.011), rng.choice((p1, p2, p3)), lift=0.1)


@sprop("pt_roller_tray", aspect=2.5, fill=0.58)
def pt_roller_tray(c, P):
    rng = c.rng
    paint = P.accent
    gr = (0.88, 0.89, 0.91)
    ao(c, 0.0, 0.0, 1.15, 0.22)
    c.poly([(-0.52, 0.02), (0.52, 0.02), (0.50, 0.12), (-0.50, 0.12)], scale(gr, 0.66), lift=0.1)
    c.poly([(-0.50, 0.12), (0.50, 0.12), (0.45, 0.32), (-0.45, 0.32)], gr, lift=0.06)
    c.poly([(-0.45, 0.32), (0.45, 0.32), (0.45, 0.345), (-0.45, 0.345)], scale(gr, 0.78), lift=0)
    c.ellipse(0.0, 0.175, 0.42, 0.055, paint, lift=0.12)
    c.ellipse(0.0, 0.18, 0.42, 0.055, mix(paint, WHITE, 0.15), alpha=0.5, lift=0)
    gloss(c, -0.15, 0.19, 0.17, 0.02, 0, 0.7)
    for k in range(5):
        y = 0.215 + k * 0.022
        wd = 0.46 - k * 0.012
        c.line(-wd, y, wd, y, 0.006, scale(gr, 0.7), 0.7)
    # loaded roller lying on the ramp
    c.rect(0.0, 0.265, 0.70, 0.17, scale(paint, 0.78), r=0.085, lift=0.2)
    c.rect(-0.03, 0.272, 0.64, 0.14, paint, r=0.07, lift=0.2)
    for _ in range(40):
        c.circle(rng.uniform(-0.31, 0.31), rng.uniform(0.215, 0.33), rng.uniform(0.004, 0.009), mix(paint, WHITE, rng.uniform(0.2, 0.5)), lift=0, alpha=0.5)
    gloss(c, -0.12, 0.31, 0.2, 0.014, 0, 0.55)
    c.ellipse(0.355, 0.265, 0.03, 0.085, scale(paint, 0.62), lift=0)
    c.ellipse(0.356, 0.265, 0.014, 0.04, (0.9, 0.9, 0.92), lift=0)
    c.line(0.37, 0.265, 0.50, 0.265, 0.012, STEEL)
    c.line(0.50, 0.265, 0.60, 0.40, 0.012, STEEL)
    c.line(0.60, 0.40, 0.66, 0.36, 0.012, STEEL)
    c.line(0.64, 0.38, 0.92, 0.60, 0.075, P.accent_dark, 1.0)
    c.line(0.64, 0.40, 0.92, 0.62, 0.02, mix(P.accent_dark, WHITE, 0.45), 0.7)
    for _ in range(5):
        _bead(c, rng.uniform(-0.35, 0.35), rng.uniform(0.06, 0.1), rng.uniform(0.008, 0.014), paint)


@sprop("pt_brush_jar", aspect=0.95, fill=1.0)
def pt_brush_jar(c, P):
    ao(c, 0.0, 0.0, 0.5, 0.1)
    tip_cols = (P.accent, _hue(P, 0.5, 0.7, 0.9), _hue(P, 0.14, 0.85, 0.98), (0.95, 0.95, 0.95))
    c.ellipse(0.0, 0.40, 0.19, 0.19 * TILT, (0.12, 0.12, 0.14), lift=0)
    for i, (ang, ln, col) in enumerate(((-24, 0.62, 0), (-8, 0.74, 1), (10, 0.66, 2), (26, 0.58, 3))):
        a = math.radians(90 + ang)
        ux, uy = math.cos(a), math.sin(a)
        bx, by = -ux * 0.14 * 0 + 0.0 + (i - 1.5) * 0.04, 0.38
        ex, ey = bx + ux * ln, by + uy * ln
        c.line(bx, by, ex, ey, 0.040, (0.86, 0.70, 0.46) if i % 2 else (0.20, 0.24, 0.30))
        c.line(bx - 0.008, by, ex - 0.008, ey, 0.010, (0.97, 0.88, 0.7), 0.5)
        fx, fy = ex + ux * 0.10, ey + uy * 0.10
        c.line(ex, ey, fx, fy, 0.062, scale(METAL, 0.9))
        c.line(ex - 0.01, ey, fx - 0.01, fy, 0.014, WHITE, 0.55)
        tx, ty = fx + ux * 0.14, fy + uy * 0.14
        c.poly(_rot([(-0.036, 0.0), (0.036, 0.0), (0.042, 0.14), (-0.042, 0.14)], ang, fx, fy), (0.96, 0.93, 0.82), lift=0.1)
        c.poly(_rot([(-0.040, 0.06), (0.040, 0.06), (0.043, 0.14), (-0.043, 0.14)], ang, fx, fy), tip_cols[col], lift=0.1)
        for k in range(4):
            xx = (k - 1.5) * 0.02
            c.line(*_rot([(xx, 0.01)], ang, fx, fy)[0], *_rot([(xx, 0.13)], ang, fx, fy)[0], 0.003, scale(tip_cols[col], 0.7), 0.45)
    hshade_box(c, 0.0, 0.19, 0.38, 0.38, (0.80, 0.90, 0.95), (0.45, 0.58, 0.66), r=0.02, alpha=0.55)
    c.ellipse(0.0, 0.0, 0.19, 0.19 * TILT, (0.55, 0.68, 0.76), lift=0, alpha=0.6)
    c.rect(0.0, 0.08, 0.36, 0.14, mix(P.accent, (0.8, 0.9, 0.95), 0.4), lift=0.1, alpha=0.5)
    arc(c, 0.0, 0.38, 0.19, 0.19 * TILT, 190, 350, 0.010, (0.95, 0.98, 1.0), 0.9, 8)
    gloss(c, -0.12, 0.20, 0.016, 0.16, 0, 0.7)
    gloss(c, 0.13, 0.20, 0.008, 0.14, 0, 0.35)
    for _ in range(14):
        c.circle(c.rng.uniform(-0.17, 0.17), c.rng.uniform(0.03, 0.34), c.rng.uniform(0.004, 0.009), c.rng.choice(tip_cols), lift=0)


@sprop("pt_swatch_fan", aspect=1.35, fill=0.60)
def pt_swatch_fan(c, P):
    ao(c, 0.0, 0.0, 0.5, 0.08)
    n = 9
    pv = (-0.18, 0.05)
    cols = []
    for k in range(n):
        t = k / float(n - 1)
        if t < 0.5:
            cols.append(mix(P.accent_dark, P.accent, t / 0.5))
        else:
            cols.append(mix(P.accent, P.accent_light, (t - 0.5) / 0.5))
    cols[1] = _hue(P, 0.50, 0.55, 0.85)
    cols[6] = _hue(P, 0.12, 0.75, 0.96)
    for k in range(n):
        ang = 12 + k * 12.5
        quad = _rot([(0.0, -0.075), (0.92, -0.075), (0.92, 0.075), (0.0, 0.075)], ang, pv[0], pv[1])
        _qpoly(c, [(x + 0.012, y - 0.012) for x, y in quad], BLACK, 0.0, 0.18)
        _qpoly(c, quad, (0.97, 0.96, 0.93), 0.04)
        face = _rot([(0.30, -0.065), (0.90, -0.065), (0.90, 0.065), (0.30, 0.065)], ang, pv[0], pv[1])
        _qpoly(c, face, cols[k], 0.14)
        a, b = _rot([(0.34, 0.0), (0.64, 0.0)], ang, pv[0], pv[1])
        c.line(a[0], a[1], b[0], b[1], 0.016, scale((0.4, 0.4, 0.44), 1.0), 0.35)
    c.circle(pv[0], pv[1], 0.04, scale(METAL, 0.8), lift=0.3)
    c.circle(pv[0] - 0.01, pv[1] + 0.01, 0.014, WHITE, lift=0, alpha=0.8)


@sprop("pt_stepladder", aspect=0.78, fill=1.0)
def pt_stepladder(c, P):
    rng = c.rng
    al = (0.80, 0.82, 0.85)
    ao(c, 0.04, 0.0, 0.75, 0.16)
    # rear leg (a little to the right, seen in perspective) then front rails and steps
    _qpoly(c, [(0.06, 0.02), (0.14, 0.02), (0.32, 0.88), (0.24, 0.88)], scale(al, 0.55), 0.1)
    _qpoly(c, [(0.36, 0.0), (0.44, 0.0), (0.34, 0.88), (0.26, 0.88)], scale(al, 0.6), 0.1)
    for k in range(5):
        v = 0.10 + k * 0.165
        w = 0.58 - k * 0.075
        c.rect(0.02, v, w, 0.045, scale(al, 0.95), lift=0.18, r=0.008)
        c.rect(0.02, v + 0.022, w, 0.008, WHITE, lift=0, alpha=0.5)
    _qpoly(c, [(-0.34, 0.0), (-0.26, 0.0), (-0.12, 0.90), (-0.20, 0.90)], al, 0.12)
    _qpoly(c, [(0.22, 0.0), (0.30, 0.0), (0.16, 0.90), (0.08, 0.90)], scale(al, 0.82), 0.12)
    c.line(-0.29, 0.1, -0.15, 0.85, 0.008, WHITE, 0.55)
    for _ in range(18):
        xv = rng.uniform(0.0, 1.0)
        colr = rng.choice((P.accent, _hue(P, 0.5, 0.7, 0.9), WHITE, P.accent_light))
        c.circle(-0.30 + xv * 0.5 + rng.uniform(-0.02, 0.02), rng.uniform(0.04, 0.88), rng.uniform(0.004, 0.012), colr, lift=0.1)
    # top platform with a paint bucket
    c.rect(-0.02, 0.915, 0.38, 0.05, scale(al, 0.92), lift=0.2, r=0.01)
    c.rect(-0.02, 0.935, 0.38, 0.008, WHITE, lift=0, alpha=0.5)
    c.rect(-0.02, 0.88, 0.34, 0.02, P.accent_dark, lift=0.1, alpha=0.9)
    hshade_box(c, -0.02, 1.01, 0.22, 0.12, (0.95, 0.96, 0.97), (0.62, 0.64, 0.68), r=0.01)
    c.ellipse(-0.02, 1.07, 0.11, 0.11 * TILT, P.accent, lift=0.2)
    c.rect(-0.02, 1.01, 0.22, 0.05, P.accent, lift=0.2, alpha=0.9)


@niche("painting", "Painting service", subjects=("pt_cans",),
       strong=("painter", "painting service", "painting services", "painting contractor", "house painting", "home painting", "wall painting", "interior painting",
               "exterior painting", "whitewash", "wall putty", "paint job", "painter ka kaam", "rang rogan", "पेंटर", "रंगाई", "पेंटिंग सर्विस", "रंग रोगन", "पुताई"),
       weak=("paint", "colour", "color", "wall", "putty", "brush", "roller", "emulsion", "texture"),
       accent="#e91e63", mood="light", group="trades", avoid=("oil painting", "art gallery", "canvas painting", "nail paint"))
def painting(S):
    P = S.pal
    rng = S.rng
    cloth = mix(P.paper, (0.84, 0.80, 0.72), 0.45)
    if P.mood == "dark":
        cloth = scale(cloth, 0.40)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # the right part of the wall is already painted: roller strokes, a ragged edge, wet sheen
        S.gradient_rect(1.32, -0.5, 7.0, 0.62, scale(P.accent, 1.06), scale(P.accent, 0.88))
        for k in range(26):
            x = 1.38 + k * 0.095 + rng.uniform(-0.02, 0.02)
            S.rect(x, 0.05 + rng.uniform(0, 0.5), 0.07, 0.9, WHITE if k % 2 else BLACK, lift=0.0, alpha=0.05)
        for k in range(8):
            S.rect(1.32 - rng.uniform(0.0, 0.04), 0.06 + k * 0.075, 0.05, 0.075, scale(P.accent, 1.0 + 0.04 * (k % 3)), lift=0.0)
        S.glow(2.0, 0.22, 0.6, mix(P.accent_light, WHITE, 0.4), 0.18)
        S.rect(1.32, 0.31, 0.014, 0.62, (0.42, 0.62, 0.90), lift=0.0, alpha=0.9)               # masking tape on the paint edge
        S.rect(1.0, 0.598, 14.0, 0.036, mix(P.paper, WHITE, 0.4), lift=0.0)                    # skirting board
        S.rect(1.0, 0.618, 14.0, 0.008, scale(P.wall_bot, 0.5), lift=0.0)
        S.window(0.42, 0.27, 0.40, 0.40)
        S.light_shaft(0.28, 0.45, 0.60, 0.45, 1.55, 1.0, 0.65, 1.0, alpha=0.16)
        S.floor(0.62, P.floor_top, P.floor_bot)
    # dust sheet over the floor with folds and splatters
    S.floor(0.66, mix(cloth, WHITE, 0.08), scale(cloth, 0.68))
    S.rect(1.0, 0.66, 14.0, 0.014, scale(cloth, 0.55), lift=0.0, alpha=0.7)
    for _ in range(26):
        v = rng.uniform(0.72, 1.4)
        u = rng.uniform(-0.2, 2.2)
        S.line(u, v, u + rng.uniform(0.2, 0.7), v + rng.uniform(-0.02, 0.02), 0.004, scale(cloth, rng.choice((0.8, 1.1))), 0.3)
    for _ in range(34):
        col = rng.choice((P.accent, P.accent, P.accent2, P.accent_dark, _hue(P, 0.5, 0.7, 0.9)))
        S.circle(rng.uniform(0.2, 2.0), rng.uniform(0.74, 1.3), rng.uniform(0.003, 0.011), col, lift=0.1, soft=0.8)
    for _ in range(3):                                                   # soft folds in the cloth
        S.soft(rng.uniform(0.0, 2.1), rng.uniform(0.80, 1.3), rng.uniform(0.2, 0.5), rng.uniform(0.012, 0.03), WHITE, 0.22, 1.2, rng.uniform(-8, 8), add=True)
        S.soft(rng.uniform(0.0, 2.1), rng.uniform(0.80, 1.3), rng.uniform(0.2, 0.5), rng.uniform(0.010, 0.02), BLACK, 0.14, 1.2, rng.uniform(-8, 8))
    S.soft(1.15, 0.86, 0.85, 0.16, P.light, 0.26, 1.5, add=True)
    S.put("pt_stepladder", 0.66, 0.80, 0.62, color=P)
    S.put("pt_swatch_fan", 1.46, 0.80, 0.27, color=P)
    S.put("pt_roller_tray", 0.88, 0.985, 0.18, color=P, shadow_w=0.5)
    S.put("pt_cans", 1.17, 0.93, 0.36, color=P, subject=True)
    S.put("pt_brush_jar", 1.58, 0.95, 0.23, color=P)
    S.focus("detail", 1.17, 0.80)
    with S.near():
        S.circle(0.52, 1.10, 0.09, P.accent, 0.9)
        S.ellipse(1.80, 1.08, 0.10, 0.04, _hue(P, 0.5, 0.7, 0.9), 0.35, 20)


# ====================================================================================================== carpentry
PINE = (0.86, 0.70, 0.48)
OAK = (0.70, 0.50, 0.30)


def _grain(c, u0, u1, v0, v1, base, n, alpha=0.3, vertical=False):
    rng = c.rng
    for _ in range(n):
        if vertical:
            u = rng.uniform(u0, u1)
            a = rng.uniform(v0, v1)
            c.line(u, a, u + rng.uniform(-0.004, 0.004), min(v1, a + rng.uniform(0.05, 0.25)), 0.003, scale(base, rng.uniform(0.66, 0.86)), alpha)
        else:
            v = rng.uniform(v0, v1)
            a = rng.uniform(u0, u1)
            c.line(a, v, min(u1, a + rng.uniform(0.08, 0.35)), v + rng.uniform(-0.004, 0.004), 0.003, scale(base, rng.uniform(0.66, 0.86)), alpha)


def _board(c, u, v, w, h, dx, dy, tone, rng, grain=4):
    """A plank seen from the front and above: long face, lit top, darker end grain with rings."""
    _prism(c, u, v, w, h, dx, dy, tone, mix(tone, WHITE, 0.18), scale(tone, 0.66), lift=0.08)
    x1 = u + w / 2
    for k in range(2):
        c.ellipse(x1 + dx * 0.5, v + h * 0.5 + dy * 0.5, dx * (0.18 + 0.2 * k), h * (0.12 + 0.18 * k), scale(tone, 0.52), lift=0, alpha=0.5)
    _grain(c, u - w / 2 + 0.02, x1 - 0.02, v + 0.01, v + h - 0.01, tone, grain, 0.35)
    _grain(c, u - w / 2 + dx * 0.4, x1 + dx * 0.3, v + h + 0.01, v + h + dy - 0.005, tone, 2, 0.3)


@sprop("cw_chair", aspect=0.95, fill=1.0)
def cw_chair(c, P):
    rng = c.rng
    ao(c, 0.12, 0.0, 0.85, 0.22)
    dx, dy = 0.17, 0.10
    rough = scale(PINE, 0.92)
    dark = scale(PINE, 0.62)
    # back legs / uprights
    for ux in (-0.13, 0.35):
        c.rect(ux, 0.55, 0.065, 0.90, scale(PINE, 0.80), lift=0.12, r=0.01)
        c.line(ux - 0.016, 0.12, ux - 0.016, 0.96, 0.008, mix(PINE, WHITE, 0.4), 0.55)
    # back slats and top rail
    for k, vv in enumerate((0.64, 0.77, 0.90)):
        c.rect(0.11, vv, 0.50, 0.075, mix(PINE, WHITE, 0.06 * k), lift=0.14, r=0.012)
        c.rect(0.11, vv + 0.033, 0.50, 0.008, WHITE, lift=0, alpha=0.35)
        _grain(c, -0.12, 0.34, vv - 0.03, vv + 0.03, PINE, 3, 0.35)
    c.rect(0.11, 0.99, 0.56, 0.05, scale(PINE, 1.04), lift=0.2, r=0.02)
    # side and back stretchers
    c.line(-0.30, 0.19, -0.13, 0.29, 0.032, dark)
    c.line(0.18, 0.19, 0.35, 0.29, 0.032, scale(PINE, 0.5))
    c.line(-0.13, 0.30, 0.35, 0.30, 0.03, scale(PINE, 0.5))
    # seat slab
    _prism(c, -0.06, 0.40, 0.70, 0.055, dx, dy, PINE, mix(PINE, WHITE, 0.2), dark, lift=0.1)
    _grain(c, -0.40, 0.45, 0.46, 0.54, PINE, 7, 0.32)
    for _ in range(3):                                              # pencil marks and a cut line
        v0 = rng.uniform(0.47, 0.53)
        c.line(rng.uniform(-0.3, 0.0), v0, rng.uniform(0.1, 0.4), v0 + rng.uniform(-0.02, 0.02), 0.004, (0.32, 0.32, 0.36), 0.45)
    soft_disc(c, -0.20, 0.52, 0.28, 0.05, WHITE, 0.28, 1.2, add=True)
    # front legs and front stretcher
    for ux in (-0.30, 0.18):
        c.poly([(ux - 0.036, 0.0), (ux + 0.036, 0.0), (ux + 0.042, 0.41), (ux - 0.042, 0.41)], scale(PINE, 0.95), lift=0.14)
        c.line(ux - 0.016, 0.03, ux - 0.020, 0.38, 0.008, mix(PINE, WHITE, 0.45), 0.55)
        c.ellipse(ux, 0.0, 0.036, 0.012, scale(PINE, 0.55), lift=0)
    c.rect(-0.06, 0.17, 0.48, 0.032, scale(PINE, 0.88), lift=0.16, r=0.008)
    soft_disc(c, 0.04, 0.22, 0.30, 0.10, BLACK, 0.18, 1.4)
    # bar clamp gripping the seat edge
    cx = 0.52
    c.rect(cx, 0.46, 0.028, 0.62, scale(STEEL, 0.9), lift=0.3)
    c.rect(cx - 0.006, 0.46, 0.008, 0.58, WHITE, lift=0, alpha=0.5)
    c.rect(cx - 0.02, 0.69, 0.11, 0.03, scale(STEEL, 0.75), lift=0.2, r=0.006)
    c.rect(cx - 0.02, 0.28, 0.11, 0.04, scale(P.accent, 0.95), lift=0.25, r=0.008)
    c.rect(cx, 0.22, 0.014, 0.10, scale(STEEL, 0.6), lift=0.1)
    c.line(cx - 0.07, 0.19, cx + 0.07, 0.19, 0.022, P.accent_dark)
    c.circle(cx - 0.07, 0.19, 0.016, P.accent, lift=0.2)
    c.circle(cx + 0.07, 0.19, 0.016, P.accent, lift=0.2)
    # glue squeeze-out, wooden dowel pegs and sawdust
    for ux, vv in ((-0.30, 0.40), (0.18, 0.40), (-0.13, 0.64), (0.35, 0.77)):
        c.circle(ux, vv, 0.012, scale(OAK, 0.6), lift=0.1)
    for _ in range(26):
        c.circle(rng.uniform(-0.40, 0.55), rng.uniform(-0.01, 0.07), rng.uniform(0.004, 0.010), mix(PINE, WHITE, rng.uniform(0.1, 0.4)), lift=0, alpha=0.8)


@sprop("cw_planks", aspect=2.7, fill=0.44)
def cw_planks(c, P):
    rng = c.rng
    ao(c, 0.1, 0.0, 1.2, 0.2)
    for i, (off, w, tone) in enumerate(((0.0, 1.10, OAK), (-0.06, 1.0, PINE), (0.05, 1.05, scale(OAK, 1.08)), (-0.02, 0.96, PINE),
                                        (0.04, 1.02, mix(OAK, PINE, 0.5)))):
        _board(c, off, i * 0.082, w, 0.07, 0.12, 0.05, tone, rng)
    c.rect(0.50, 0.04, 0.05, 0.08, scale(OAK, 0.5), lift=0.1)
    soft_disc(c, -0.3, 0.38, 0.5, 0.06, WHITE, 0.25, 1.2, add=True)


@sprop("cw_plane", aspect=3.2, fill=0.50)
def cw_plane(c, P):
    rng = c.rng
    c.x += 0.065 * c.s                                   # centre the drawing in its declared box
    ao(c, 0.0, 0.0, 1.15, 0.12)
    # curly shavings
    for k, (u, v, r) in enumerate(((-0.62, 0.05, 0.075), (-0.78, 0.04, 0.06), (-0.52, 0.02, 0.05), (0.72, 0.03, 0.05))):
        for j in range(3):
            arc(c, u + j * 0.02, v + 0.03, r - j * 0.016, (r - j * 0.016) * 1.0, 20 + j * 40, 340 - j * 10, 0.016, mix(PINE, WHITE, 0.3 + 0.1 * j), 0.95, 10)
    c.line(-0.42, 0.20, -0.55, 0.12, 0.022, mix(PINE, WHITE, 0.35))
    # steel sole and wooden stock
    c.rect(0.12, 0.03, 1.12, 0.035, scale(STEEL, 0.8), lift=0.3)
    c.rect(0.12, 0.12, 1.12, 0.16, OAK, r=0.03, lift=0.2)
    c.rect(0.12, 0.185, 1.12, 0.02, mix(OAK, WHITE, 0.25), lift=0, alpha=0.6)
    _grain(c, -0.4, 0.62, 0.07, 0.17, OAK, 8, 0.4)
    # iron and wedge in the mouth
    c.poly([(0.06, 0.20), (0.15, 0.20), (0.02, 0.03), (-0.01, 0.03)], scale(STEEL, 1.05), lift=0.3)
    c.poly([(0.16, 0.20), (0.24, 0.20), (0.15, 0.10), (0.11, 0.11)], PINE, lift=0.1)
    c.rect(0.10, 0.215, 0.12, 0.022, P.accent_dark, lift=0.2, r=0.006)
    # front knob and rear tote handle
    c.circle(-0.34, 0.25, 0.05, scale(OAK, 0.75), lift=0.25)
    c.rect(-0.34, 0.20, 0.04, 0.06, scale(OAK, 0.7), lift=0.1)
    c.poly([(0.44, 0.20), (0.52, 0.20), (0.60, 0.46), (0.52, 0.50), (0.46, 0.33)], scale(OAK, 0.9), lift=0.25)
    c.poly([(0.52, 0.20), (0.62, 0.20), (0.64, 0.30), (0.56, 0.30)], scale(OAK, 0.85), lift=0.2)
    gloss(c, 0.48, 0.38, 0.012, 0.05, 20, 0.55)
    gloss(c, -0.12, 0.19, 0.30, 0.012, 0, 0.5)
    c.circle(0.31, 0.19, 0.012, BRASS, lift=0.2)


@sprop("cw_saw", aspect=5.8, fill=0.30)
def cw_saw(c, P):
    c.x += 0.075 * c.s                                   # centre the drawing in its declared box
    ao(c, 0.0, 0.0, 1.6, 0.14)
    # blade: long tapered trapezoid with a zigzag tooth edge
    c.poly([(-0.95, 0.02), (0.45, 0.04), (0.45, 0.19), (-0.95, 0.09)], scale(STEEL, 1.02), lift=0.3)
    c.poly([(-0.90, 0.075), (0.45, 0.14), (0.45, 0.19), (-0.90, 0.085)], WHITE, lift=0, alpha=0.32)
    n = 30
    for k in range(n):
        t = k / float(n)
        u0 = -0.95 + 1.40 * t
        u1 = -0.95 + 1.40 * (t + 1.0 / n)
        v0 = 0.02 + 0.02 * t
        c.poly([(u0, v0), (u1, v0 + 0.002), ((u0 + u1) / 2 + 0.01, v0 - 0.022)], scale(STEEL, 0.78), lift=0.1)
    c.line(-0.9, 0.09, 0.45, 0.17, 0.004, scale(STEEL, 0.6), 0.5)
    # wooden D handle with a hole and brass rivets
    c.poly([(0.42, 0.02), (0.64, 0.04), (0.80, 0.22), (0.74, 0.30), (0.52, 0.29), (0.42, 0.19)], scale(OAK, 0.82), lift=0.25)
    c.ellipse(0.62, 0.19, 0.075, 0.05, scale(OAK, 0.4), lift=0, angle=15)
    c.ellipse(0.615, 0.19, 0.06, 0.036, (0.35, 0.28, 0.22), lift=0, angle=15, alpha=0.9)
    for u, v in ((0.47, 0.08), (0.47, 0.16)):
        c.circle(u, v, 0.012, BRASS, lift=0.2)
    gloss(c, -0.4, 0.09, 0.45, 0.01, 4, 0.7)


@sprop("cw_chisels", aspect=6.7, fill=0.28)
def cw_chisels(c, P):
    c.x -= 0.345 * c.s                                   # centre the drawing in its declared box
    ao(c, 0.0, 0.0, 1.2, 0.12)
    cols = (P.accent, _hue(P, 0.5, 0.6, 0.85), (0.15, 0.15, 0.17), P.accent_dark)
    for i, (v, wb) in enumerate(((0.02, 0.060), (0.095, 0.045), (0.165, 0.075), (0.230, 0.04))):
        u0 = -0.55 + 0.04 * (i % 2)
        c.rect(u0 + 0.24, v + 0.02, 0.56, wb, scale(STEEL, 1.05), lift=0.3, r=0.004)
        c.poly([(u0 - 0.04, v + 0.02 - wb / 2), (u0 + 0.12, v + 0.02 - wb / 2), (u0 + 0.12, v + 0.02 + wb / 2), (u0 - 0.04, v + 0.02 + wb / 2 - 0.012)],
               mix(STEEL, WHITE, 0.45), lift=0.1)
        c.rect(u0 + 0.54, v + 0.02, 0.05, wb * 0.9, scale(BRASS, 0.95), lift=0.3)
        c.rect(u0 + 0.80, v + 0.02, 0.48, wb * 1.2, cols[i], r=0.02, lift=0.25)
        c.line(u0 + 0.58, v + 0.034, u0 + 1.18, v + 0.034, 0.008, mix(cols[i], WHITE, 0.5), 0.7)
        c.line(u0 + 0.10, v + 0.035, u0 + 0.50, v + 0.035, 0.005, WHITE, 0.7)


@niche("carpentry", "Carpentry and woodwork", subjects=("cw_chair",),
       strong=("carpenter", "carpentry", "woodwork", "wood work", "wooden furniture", "modular kitchen", "wardrobe maker", "furniture maker", "furniture making",
               "carpenter near me", "barhai", "badhai ka kaam", "furniture wala", "बढ़ई", "बढई", "कारपेंटर", "लकड़ी का काम", "फर्नीचर"),
       weak=("wood", "timber", "plywood", "furniture", "saw", "joinery", "cabinet", "sawdust"),
       accent="#8d6e63", mood="warm", group="trades", avoid=("interior design",))
def carpentry(S):
    P = S.pal
    rng = S.rng
    peg = mix(P.wall_top, scale(P.surface, 1.05), 0.55)
    dk = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # pegboard wall with hanging tool silhouettes
        S.gradient_rect(-5.0, -0.5, 7.0, 0.60, peg, scale(peg, 0.84))
        for k in range(60):
            S.rect(-3.0 + k * 0.115, 0.2, 0.004, 0.8, scale(peg, 0.7), lift=0.0, alpha=0.5)
        for k in range(8):
            S.rect(1.0, 0.04 + k * 0.075, 2.4, 0.004, scale(peg, 0.7), lift=0.0, alpha=0.5)
        tool = scale(P.ink, 1.6) if not dk else mix(P.accent_light, WHITE, 0.2)
        S.line(0.30, 0.12, 0.30, 0.46, 0.012, tool)                                             # saw
        S.poly([(0.30, 0.20), (0.40, 0.46), (0.30, 0.46)], scale(STEEL, 0.9))
        S.line(0.62, 0.10, 0.62, 0.40, 0.016, scale(OAK, 0.8))                                 # hammer
        S.rect(0.62, 0.10, 0.09, 0.03, tool, lift=0.0)
        S.rect(0.92, 0.20, 0.14, 0.012, P.accent, lift=0.0)                                    # square
        S.rect(0.86, 0.26, 0.012, 0.14, P.accent, lift=0.0)
        for k in range(5):                                                                      # chisels row
            S.rect(1.32 + k * 0.04, 0.30, 0.012, 0.17, scale(STEEL, 0.9), lift=0.0)
            S.rect(1.32 + k * 0.04, 0.20, 0.016, 0.08, mix(P.accent, scale(OAK, 0.8), (k % 2) * 0.7), lift=0.0)
        S.circle(1.72, 0.30, 0.07, scale(STEEL, 0.9), lift=0.0)                                # clamp / coil
        S.circle(1.72, 0.30, 0.04, peg, lift=0.0)
        S.rect(1.0, 0.585, 14.0, 0.03, scale(P.wall_bot, 0.55), lift=0.0)
        S.pendant(1.12, -0.1, 0.12, (1.0, 0.82, 0.52), 0.10)
        S.glow(0.2, 0.30, 0.7, P.light, 0.22)
        S.glow(1.12, 0.30, 0.9, (1.0, 0.86, 0.60), 0.34 if not dk else 0.30)
        S.floor(0.60, scale(P.floor_top, 0.9), scale(P.floor_bot, 0.8))
        S.light_shaft(0.10, 0.2, 0.45, 0.2, 1.25, 1.0, 0.4, 1.0, alpha=0.12)
    # workbench: darker walnut planks so the pale pine pieces stand out, dog holes, front apron
    top = scale(mix(P.surface, (0.46, 0.28, 0.16), 0.62), 0.92)
    if dk:
        top = scale(top, 0.85)
    S.wood(-5.0, 0.64, 7.0, 2.6, top, plank=0.20, vertical=True, grain=0.7)
    S.rect(1.0, 0.67, 14.0, 0.06, scale(top, 0.7), lift=0.0)
    S.rect(1.0, 0.64, 14.0, 0.006, scale(top, 1.45), lift=0.0)
    for k in range(18):
        S.ellipse(-0.9 + k * 0.28, 0.69, 0.016, 0.008, scale(top, 0.35), lift=0.0)
    for k in range(7):                                                                          # glossy varnish streaks and a tool-mark band
        S.rect(-0.6 + k * 0.62, 1.05, 0.05, 0.7, mix(top, WHITE, 0.30), lift=0.0, alpha=0.10)
    # a drawing sheet with plans and measurements under the work: the paper gives clean contrast to the wood
    paper = mix(P.paper, (1.0, 0.97, 0.88), 0.5) if not dk else scale(mix(P.paper, (1.0, 0.95, 0.85), 0.5), 0.78)
    _spoly(S, [(0.66, 0.80), (1.62, 0.78), (1.74, 1.04), (0.56, 1.06)], scale(paper, 0.80), 0.9)
    _spoly(S, [(0.68, 0.81), (1.60, 0.79), (1.71, 1.025), (0.59, 1.04)], paper)
    ink = (0.22, 0.30, 0.50) if not dk else (0.45, 0.60, 0.85)
    for k in range(6):                                                                          # ruled grid and pencil lines
        v = 0.85 + k * 0.035
        S.line(0.66 - k * 0.012, v, 1.66 + k * 0.016, v - 0.003, 0.0016, ink, 0.28)
    for k in range(9):
        u = 0.72 + k * 0.11
        S.line(u, 0.81, u - 0.02 + k * 0.004, 1.03, 0.0016, ink, 0.22)
    S.line(0.80, 0.96, 1.28, 0.93, 0.003, ink, 0.55)                                            # elevation of a chair
    S.line(0.86, 0.96, 0.84, 0.86, 0.003, ink, 0.55)
    S.line(1.22, 0.93, 1.24, 0.85, 0.003, ink, 0.55)
    S.line(1.40, 0.88, 1.62, 0.86, 0.003, (0.75, 0.15, 0.10), 0.55)
    for _ in range(46):                                                                         # sawdust
        S.circle(rng.uniform(0.3, 2.0), rng.uniform(0.74, 1.3), rng.uniform(0.002, 0.006), mix(PINE, WHITE, rng.uniform(0.2, 0.5)), lift=0, alpha=0.8, soft=0.8)
    S.soft(1.12, 0.84, 0.95, 0.17, P.light, 0.46 if not dk else 0.52, 1.4, add=True)
    S.put("cw_planks", 0.84, 0.80, 0.20, color=P)
    S.put("cw_chisels", 1.34, 0.90, 0.075, color=P)
    S.put("cw_chair", 1.12, 0.93, 0.56, color=P, subject=True, shadow_w=0.6)
    S.put("cw_saw", 0.90, 1.00, 0.12, color=P)
    S.put("cw_plane", 1.36, 1.01, 0.15, color=P)
    S.focus("detail", 1.20, 0.90)
    with S.near():
        S.circle(0.55, 1.10, 0.07, mix(PINE, P.accent, 0.2), 0.9)
        S.ellipse(1.82, 1.08, 0.09, 0.03, scale(OAK, 0.9), 0.6, 15)


# ====================================================================================================== AC and appliance repair
COPPER = (0.82, 0.47, 0.28)


def _sline(S, u0, v0, u1, v1, w, color, alpha=1.0):
    """A thin straight band between two stage points, scan-line filled (long diagonals are slow with S.line)."""
    (x0, y0), (x1, y1) = S.px(u0, v0), S.px(u1, v1)
    hw = max(0.5, S.length(w) / 2)
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n * hw, dx / n * hw
    if S.dry:
        return
    _scan(S.cv, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color, color, alpha)


def _cable(c, pts, w, col, alpha=1.0):
    """A smooth cable / hose drawn as short capsules (corner-cut curve; much cheaper than a big path shape)."""
    pts = list(pts)
    for _ in range(2):
        q = [pts[0]]
        for p0, p1 in zip(pts, pts[1:]):
            q.append((p0[0] * 0.75 + p1[0] * 0.25, p0[1] * 0.75 + p1[1] * 0.25))
            q.append((p0[0] * 0.25 + p1[0] * 0.75, p0[1] * 0.25 + p1[1] * 0.75))
        q.append(pts[-1])
        pts = q
    for p0, p1 in zip(pts, pts[1:]):
        c.line(p0[0], p0[1], p1[0], p1[1], w, col, alpha)


def _spoly(S, pts, color, alpha=1.0):
    """A flat polygon between stage points, scan-line filled (the stage polygon is slow for big shapes)."""
    px = [S.px(u, v) for u, v in pts]
    if S.dry:
        return
    _scan(S.cv, px, color, color, alpha)


def _gauge(c, u, v, r, ring, needle_ang):
    c.circle(u + r * 0.06, v - r * 0.06, r * 1.04, BLACK, lift=0, alpha=0.28)
    c.circle(u, v, r, scale(CHROME, 0.75), lift=0.3)
    c.circle(u, v, r * 0.90, CHROME, lift=0.1)
    c.circle(u, v, r * 0.82, (0.97, 0.97, 0.96), lift=0.04)
    arc(c, u, v, r * 0.64, r * 0.64, 30, 150, r * 0.10, (0.20, 0.55, 0.30), 0.9, 6)
    arc(c, u, v, r * 0.64, r * 0.64, -80, 30, r * 0.10, (0.88, 0.70, 0.12), 0.9, 6)
    arc(c, u, v, r * 0.64, r * 0.64, 150, 260, r * 0.10, ring, 0.9, 6)
    for k in range(13):
        a = math.radians(-60 + k * 20)
        c.line(u + math.cos(a) * r * 0.74, v + math.sin(a) * r * 0.74, u + math.cos(a) * r * 0.82, v + math.sin(a) * r * 0.82, r * 0.025, (0.15, 0.15, 0.18), 0.9)
    a = math.radians(needle_ang)
    c.line(u, v, u + math.cos(a) * r * 0.66, v + math.sin(a) * r * 0.66, r * 0.045, (0.80, 0.10, 0.08))
    c.circle(u, v, r * 0.09, (0.15, 0.15, 0.18), lift=0.2)
    c.line(u - r * 0.55, v + r * 0.5, u - r * 0.1, v + r * 0.72, r * 0.07, WHITE, 0.45)


CHROME = (0.82, 0.85, 0.89)


@sprop("ac_split", aspect=2.0, fill=1.0)
def ac_split(c, P):
    rng = c.rng
    wh = (0.97, 0.98, 0.99)
    soft_disc(c, 0.05, 0.54, 1.0, 0.10, BLACK, 0.30, 1.3)
    # cold air under the louvre: soft light-blue streaks and sparkles
    for k in range(4):
        u = -0.66 + k * 0.44 + rng.uniform(-0.05, 0.05)
        soft_disc(c, u, 0.30, 0.18, 0.26, (0.70, 0.90, 1.0), 0.28, 1.3, add=True)
    for k in range(4):
        _spark(c, -0.6 + k * 0.4 + rng.uniform(-0.08, 0.08), rng.uniform(0.14, 0.36), rng.uniform(0.035, 0.06), (0.7, 0.92, 1.0), 0.8)
    # body: rounded front, darker lower lip, grille slots, louvre flap
    c.rect(0.0, 0.80, 1.84, 0.46, scale(wh, 0.80), r=0.07, lift=0.0)
    c.rect(-0.01, 0.805, 1.80, 0.44, wh, r=0.07, lift=0.10)
    c.rect(0.0, 0.62, 1.76, 0.12, (0.90, 0.92, 0.95), r=0.05, lift=0.12)
    for k in range(22):
        c.rect(-0.80 + k * 0.076, 0.965, 0.05, 0.012, (0.62, 0.66, 0.72), lift=0, alpha=0.8)
    c.rect(0.0, 0.575, 1.52, 0.05, (0.10, 0.14, 0.20), lift=0.0, r=0.015)
    c.poly([(-0.76, 0.60), (0.76, 0.60), (0.73, 0.545), (-0.73, 0.545)], (0.92, 0.94, 0.97), lift=0.12)
    c.line(-0.72, 0.597, 0.72, 0.597, 0.008, WHITE, 0.7)
    c.rect(0.0, 0.742, 1.74, 0.006, scale(wh, 0.8), lift=0, alpha=0.8)
    # display and brand strip
    c.rect(0.62, 0.84, 0.36, 0.13, (0.07, 0.10, 0.16), r=0.02, lift=0.1)
    soft_disc(c, 0.58, 0.84, 0.24, 0.08, (0.4, 0.8, 1.0), 0.45, 1.3, add=True)
    c.text("24", 0.55, 0.84, 0.075, (0.65, 0.92, 1.0), 0.20)
    c.circle(0.74, 0.865, 0.011, (0.3, 1.0, 0.5), lift=0)
    c.circle(0.74, 0.82, 0.011, P.accent_light, lift=0)
    c.rect(-0.62, 0.86, 0.34, 0.022, P.accent, r=0.008, lift=0.2)
    c.rect(-0.66, 0.82, 0.22, 0.010, mix(P.accent, WHITE, 0.4), r=0.004, lift=0, alpha=0.8)
    gloss(c, -0.35, 0.95, 0.72, 0.03, 0, 0.7)
    soft_disc(c, 0.9, 0.78, 0.18, 0.42, BLACK, 0.16, 1.3)
    soft_disc(c, -0.1, 0.70, 0.8, 0.10, WHITE, 0.18, 1.3, add=True)


@sprop("ac_gauges", aspect=2.7, fill=0.72)
def ac_gauges(c, P):
    ao(c, 0.0, 0.0, 1.5, 0.14)
    BLUE, RED, YEL = (0.15, 0.40, 0.85), (0.85, 0.15, 0.12), (0.95, 0.80, 0.12)
    # hoses coiling on the floor
    _cable(c, [(-0.50, 0.17), (-0.80, 0.10), (-0.92, 0.04), (-0.60, 0.02)], 0.05, scale(BLUE, 0.75))
    _cable(c, [(-0.50, 0.17), (-0.80, 0.10), (-0.92, 0.04), (-0.60, 0.02)], 0.03, BLUE)
    _cable(c, [(0.50, 0.17), (0.80, 0.11), (0.94, 0.05), (0.62, 0.02)], 0.05, scale(RED, 0.75))
    _cable(c, [(0.50, 0.17), (0.80, 0.11), (0.94, 0.05), (0.62, 0.02)], 0.03, RED)
    _cable(c, [(0.0, 0.14), (0.0, 0.05), (0.20, 0.02), (0.55, 0.035)], 0.05, scale(YEL, 0.75))
    _cable(c, [(0.0, 0.14), (0.0, 0.05), (0.20, 0.02), (0.55, 0.035)], 0.03, YEL)
    # manifold block, knobs and sight glass
    c.rect(0.0, 0.20, 1.04, 0.16, scale(CHROME, 0.9), r=0.04, lift=0.3)
    c.rect(0.0, 0.245, 1.0, 0.02, WHITE, lift=0, alpha=0.5)
    c.circle(0.0, 0.20, 0.065, (0.15, 0.20, 0.30), lift=0.2)
    c.circle(0.0, 0.20, 0.045, (0.55, 0.78, 0.95), lift=0.3)
    for sg, col in ((-1, BLUE), (1, RED)):
        c.rect(sg * 0.32, 0.10, 0.04, 0.08, scale(CHROME, 0.8), lift=0.2)
        c.circle(sg * 0.32, 0.075, 0.075, col, lift=0.3)
        c.circle(sg * 0.32, 0.075, 0.04, scale(col, 0.7), lift=0.1)
        gloss(c, sg * 0.32 - 0.02, 0.10, 0.025, 0.02, 0, 0.6)
    # the two dials
    _gauge(c, -0.32, 0.46, 0.25, (0.20, 0.45, 0.85), 70)
    _gauge(c, 0.32, 0.46, 0.25, (0.85, 0.18, 0.12), 25)


@sprop("ac_cylinder", aspect=0.46, fill=1.0)
def ac_cylinder(c, P):
    ao(c, 0.0, 0.0, 0.5, 0.10)
    col = mix(P.accent, (0.6, 0.8, 0.95), 0.35)
    hshade_box(c, 0.0, 0.34, 0.40, 0.68, scale(col, 1.12), scale(col, 0.50), r=0.02)
    c.ellipse(0.0, 0.0, 0.20, 0.20 * TILT * 0.8, scale(col, 0.45), lift=0)
    hshade_box(c, 0.0, 0.34 + 0.001, 0.40, 0.68, scale(col, 1.12), scale(col, 0.50), r=0.02)
    c.poly([(-0.20, 0.68), (0.20, 0.68), (0.10, 0.84), (-0.10, 0.84)], scale(col, 0.85), lift=0.25)
    c.ellipse(0.0, 0.68, 0.20, 0.06, scale(col, 0.9), lift=0.15)
    hshade_box(c, 0.0, 0.88, 0.14, 0.08, scale(STEEL, 1.1), scale(STEEL, 0.6), r=0.01)
    c.rect(0.0, 0.95, 0.10, 0.06, scale(BRASS, 1.0), lift=0.3, r=0.01)
    c.rect(0.0, 0.99, 0.30, 0.025, P.accent_dark, lift=0.3, r=0.01)
    c.rect(0.12, 0.93, 0.07, 0.035, scale(BRASS, 0.8), lift=0.3)
    c.rect(0.0, 0.40, 0.38, 0.30, (0.96, 0.96, 0.94), lift=0.04)
    c.rect(0.0, 0.50, 0.38, 0.08, P.accent_dark, lift=0.2)
    c.text("R32", 0.0, 0.50, 0.07, WHITE, 0.2)
    for k in range(4):
        c.rect(0.0, 0.38 - k * 0.04, 0.26 - (k % 2) * 0.1, 0.012, (0.3, 0.3, 0.34), lift=0, alpha=0.6)
    soft_disc(c, 0.14, 0.34, 0.12, 0.40, BLACK, 0.25, 1.3)
    gloss(c, -0.12, 0.40, 0.025, 0.28, 0, 0.6)


@sprop("ac_pipe_coil", aspect=1.5, fill=0.40)
def ac_pipe_coil(c, P):
    ao(c, 0.0, 0.0, 1.0, 0.2)
    for k in range(4):                                         # insulated pipe lying in a coil: stacked ellipse rings
        v = 0.07 + k * 0.045
        c.ellipse(0.0, v, 0.46, 0.46 * 0.42, (0.10, 0.10, 0.12), lift=0)
        c.ellipse(0.0, v + 0.01, 0.43, 0.43 * 0.42, (0.22, 0.22, 0.26), lift=0.2, alpha=0.0)
        arc(c, 0.0, v + 0.012, 0.455, 0.455 * 0.42, 195, 345, 0.032, (0.30, 0.30, 0.34), 1.0, 12)
        arc(c, 0.0, v + 0.025, 0.455, 0.455 * 0.42, 200, 340, 0.008, (0.62, 0.62, 0.68), 0.7, 10)
    for k in range(3):
        v = 0.22 + k * 0.0
        arc(c, 0.0, 0.0 + 0.19, 0.34 - k * 0.08, (0.34 - k * 0.08) * 0.42, 20, 340, 0.030, scale(COPPER, 0.8), 1.0, 14)
        arc(c, -0.01, 0.0 + 0.205, 0.34 - k * 0.08, (0.34 - k * 0.08) * 0.42, 40, 320, 0.008, mix(COPPER, WHITE, 0.6), 0.8, 12)
    c.rect(0.55, 0.12, 0.30, 0.05, scale(COPPER, 0.9), lift=0.3, r=0.02)
    c.rect(0.74, 0.12, 0.06, 0.07, scale(BRASS, 1.0), lift=0.3)
    c.line(0.55, 0.138, 0.82, 0.138, 0.008, mix(COPPER, WHITE, 0.6), 0.8)


@sprop("ac_remote", aspect=5.0, fill=0.20)
def ac_remote(c, P):
    ao(c, 0.0, 0.0, 1.1, 0.12)
    c.rect(0.0, 0.035, 1.0, 0.07, scale((0.82, 0.84, 0.87), 0.7), r=0.03, lift=0.1)
    c.poly([(-0.48, 0.06), (0.48, 0.06), (0.44, 0.20), (-0.44, 0.20)], (0.92, 0.93, 0.95), lift=0.1)
    c.rect(-0.20, 0.135, 0.34, 0.07, (0.10, 0.18, 0.26), r=0.01, lift=0.1)
    soft_disc(c, -0.20, 0.135, 0.18, 0.05, (0.4, 0.8, 1.0), 0.4, 1.3, add=True)
    c.text("26", -0.24, 0.135, 0.05, (0.7, 0.95, 1.0), 0.2)
    for k in range(5):
        c.ellipse(0.12 + k * 0.075, 0.13, 0.026, 0.020, scale(P.accent, 1.0) if k == 0 else (0.72, 0.74, 0.78), lift=0.2)
    gloss(c, -0.1, 0.19, 0.3, 0.012, 0, 0.5)


@sprop("ac_toolbox", aspect=1.55, fill=0.80)
def ac_toolbox(c, P):
    rng = c.rng
    body = mix(P.accent, (0.16, 0.26, 0.58), 0.25)
    dark = scale(body, 0.55)
    ao(c, 0.0, 0.0, 1.25, 0.2)
    # carry handle (chrome tube) behind the lid line
    _cable(c, [(-0.34, 0.40), (-0.30, 0.56), (0.30, 0.56), (0.34, 0.40)], 0.050, scale(STEEL, 0.55))
    _cable(c, [(-0.335, 0.41), (-0.295, 0.555), (0.295, 0.555), (0.335, 0.41)], 0.030, STEEL)
    c.line(-0.26, 0.565, 0.24, 0.565, 0.008, WHITE, 0.7)
    # lower tray and lid (two stacked boxes with a recessed seam)
    _prism(c, 0.0, 0.0, 1.0, 0.20, 0.14, 0.12, body, mix(body, WHITE, 0.2), dark, lift=0.18, r=0.025)
    _prism(c, 0.0, 0.215, 1.0, 0.19, 0.14, 0.12, mix(body, WHITE, 0.06), mix(body, WHITE, 0.32), dark, lift=0.2, r=0.025)
    c.rect(0.0, 0.205, 1.02, 0.022, (0.05, 0.06, 0.09), lift=0, alpha=0.8)
    # embossed ribs and rivets on the front
    for u in (-0.34, 0.0, 0.34):
        c.rect(u, 0.10, 0.20, 0.07, scale(body, 0.78), r=0.015, lift=0.25)
        c.line(u - 0.09, 0.128, u + 0.09, 0.128, 0.006, mix(body, WHITE, 0.55), 0.7)
    for sg in (-1, 1):
        for v in (0.03, 0.37):
            c.circle(sg * 0.47, v, 0.012, scale(STEEL, 0.9), lift=0.3)
        c.rect(sg * 0.32, 0.215, 0.10, 0.12, STEEL, r=0.012, lift=0.3)            # latches
        c.rect(sg * 0.32, 0.19, 0.055, 0.035, scale(STEEL, 0.45), lift=0)
        c.line(sg * 0.32 - 0.04, 0.265, sg * 0.32 + 0.04, 0.265, 0.008, WHITE, 0.6)
    c.rect(0.0, 0.31, 0.28, 0.07, (0.93, 0.93, 0.95), r=0.01, lift=0.05)           # label plate
    c.rect(0.0, 0.31, 0.22, 0.012, scale(body, 0.7), lift=0)
    # tools lying on the lid: spanner and pliers
    c.line(-0.30, 0.43, 0.20, 0.45, 0.034, scale(STEEL, 0.6))
    c.line(-0.30, 0.44, 0.20, 0.46, 0.020, mix(STEEL, WHITE, 0.3))
    c.circle(0.22, 0.455, 0.045, scale(STEEL, 0.85), lift=0.3)
    c.circle(0.23, 0.455, 0.02, scale(body, 0.5), lift=0)
    soft_disc(c, -0.28, 0.30, 0.46, 0.12, WHITE, 0.26, 1.2, add=True)
    soft_disc(c, 0.52, 0.22, 0.14, 0.26, BLACK, 0.22, 1.3)
    for _ in range(16):
        c.circle(rng.uniform(-0.46, 0.46), rng.uniform(0.02, 0.38), rng.uniform(0.003, 0.007), mix(body, WHITE, 0.45), lift=0, alpha=0.3)


@niche("ac-repair", "AC and appliance repair", subjects=("ac_split",),
       strong=("ac repair", "air conditioner repair", "ac service", "ac servicing", "hvac", "refrigerator repair", "fridge repair", "washing machine repair",
               "split ac installation", "ac gas filling", "ac technician", "appliance repair", "एसी रिपेयर", "एसी सर्विस", "फ्रिज रिपेयर", "वाशिंग मशीन रिपेयर"),
       weak=("air conditioner", "cooling", "gas refill", "compressor", "split ac", "technician", "refrigerator"),
       accent="#29b6f6", mood="cool", group="trades", avoid=("car ac",))
def ac_repair(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    feat = mix(P.wall_top, P.accent, 0.28) if not dk else mix(P.wall_top, P.accent, 0.25)
    tile = mix(P.paper, P.accent_light, 0.18) if not dk else scale(mix(P.accent, (0.3, 0.35, 0.4), 0.5), 0.34)
    grout = scale(tile, 0.80)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.64)
        S.gradient_rect(0.15, -0.5, 2.05, 0.64, scale(feat, 1.04), scale(feat, 0.88))              # accent feature wall behind the unit
        S.rect(0.15, 0.07, 0.02, 0.9, scale(feat, 0.7), lift=0.0, alpha=0.6)
        S.window(-0.42, 0.28, 0.42, 0.42)
        S.rect(-0.05, 0.28, 0.14, 0.42, mix(P.accent_light, WHITE, 0.3), lift=0.0, alpha=0.9)      # curtain edge
        S.glow(1.1, 0.25, 0.9, mix(P.accent_light, WHITE, 0.5), 0.2)
        S.rect(1.0, 0.625, 14.0, 0.028, mix(P.paper, WHITE, 0.4), lift=0.0)
        S.floor(0.64, tile, scale(tile, 0.85))
        S.light_shaft(-0.55, 0.45, -0.28, 0.45, 0.9, 1.0, 0.2, 1.0, alpha=0.14)
    # polished tile floor in perspective with grout lines and a reflection pool
    S.floor(0.64, mix(tile, WHITE, 0.05), scale(tile, 0.66))
    vpu, vpv = 1.05, 0.10
    for i in range(-18, 19):
        ub = vpu + i * 0.36
        t = (0.64 - vpv) / (0.98 - vpv)
        _sline(S, vpu + (ub - vpu) * t, 0.64, vpu + (ub - vpu) * (2.2 - vpv) / (0.98 - vpv), 2.2, 0.004, grout, 0.7)
    for n in range(0, 8):
        v = vpv + 0.54 / (1 - 0.12 * n)
        S.rect(1.0, v, 14.0, 0.004, grout, lift=0.0, alpha=0.7)
    S.soft(1.1, 0.84, 0.9, 0.16, mix(P.accent_light, WHITE, 0.5) if not dk else P.accent, 0.34 if not dk else 0.38, 1.5, add=True)
    S.put("ac_split", 1.12, 0.62, 0.48, color=P, subject=True, shadow=False)
    S.put("ac_pipe_coil", 0.78, 0.88, 0.19, color=P)
    S.put("ac_cylinder", 1.52, 0.93, 0.40, color=P)
    S.put("ac_toolbox", 0.80, 1.00, 0.21, color=P)
    S.put("ac_gauges", 1.23, 1.00, 0.26, color=P)
    S.put("ac_remote", 1.40, 1.00, 0.09, color=P, framed=False)
    S.focus("detail", 1.10, 0.40)
    with S.near():
        S.circle(0.55, 1.10, 0.08, mix(P.accent_light, WHITE, 0.3), 0.7)
        S.ellipse(1.80, 1.08, 0.10, 0.035, P.accent, 0.5, 10)


# ====================================================================================================== packers and movers
def _box(c, u, v, w, h, dx, dy, tone, P, rng, label=False, fragile=False, hole=False):
    """A cardboard box (front, lit top, shaded side) sealed with accent-coloured tape, optionally labelled."""
    _prism(c, u, v, w, h, dx, dy, tone, mix(tone, WHITE, 0.20), scale(tone, 0.66), lift=0.08)
    x0, x1 = u - w / 2, u + w / 2
    for k in range(5):                                                       # corrugation hints and worn corners
        yy = v + h * (0.15 + 0.17 * k)
        c.line(x0 + 0.01, yy, x1 - 0.01, yy, 0.0035, scale(tone, 0.82), 0.22)
    c.rect(u, v + h * 0.04, w, h * 0.06, BLACK, lift=0, alpha=0.10)
    tw = min(0.09, w * 0.16)
    tape = P.accent if not fragile else (0.86, 0.14, 0.12)
    c.poly([(u - tw / 2, v + h), (u + tw / 2, v + h), (u + tw / 2 + dx, v + h + dy), (u - tw / 2 + dx, v + h + dy)], tape, lift=0.15)
    c.rect(u, v + h * 0.86, tw, h * 0.28, tape, lift=0.15)
    c.line(u - tw * 0.25, v + h * 0.98, u - tw * 0.25, v + h * 0.74, tw * 0.14, mix(tape, WHITE, 0.55), 0.7)
    c.line(x0 + 0.01, v + h - 0.004, x1 - 0.01, v + h - 0.004, 0.006, mix(tone, WHITE, 0.45), 0.55)
    c.line(x1 + dx * 0.0, v + h * 0.04, x1, v + h * 0.96, 0.004, scale(tone, 0.55), 0.4)
    if label:
        lu, lv = u - w * 0.18, v + h * 0.42
        c.rect(lu, lv, w * 0.38, h * 0.30, (0.97, 0.97, 0.95), lift=0.03, r=0.004)
        c.rect(lu - w * 0.06, lv + h * 0.07, w * 0.22, h * 0.035, (0.25, 0.25, 0.30), lift=0, alpha=0.75)
        c.rect(lu - w * 0.04, lv + h * 0.01, w * 0.26, h * 0.025, (0.25, 0.25, 0.30), lift=0, alpha=0.55)
        for k in range(9):
            c.rect(lu - w * 0.13 + k * w * 0.026, lv - h * 0.08, w * 0.012, h * 0.07, (0.12, 0.12, 0.15), lift=0, alpha=0.8)
    if fragile:
        c.text("FRAGILE", u + w * 0.12, v + h * 0.40, h * 0.12, (0.86, 0.14, 0.12), 0.20)
        c.line(u - w * 0.30, v + h * 0.16, u - w * 0.30, v + h * 0.30, w * 0.014, (0.15, 0.15, 0.18))
        c.poly([(u - w * 0.30 - w * 0.04, v + h * 0.28), (u - w * 0.30 + w * 0.04, v + h * 0.28), (u - w * 0.30, v + h * 0.35)], (0.15, 0.15, 0.18), lift=0)
    if hole:
        c.ellipse(x1 + dx * 0.5, v + h * 0.55 + dy * 0.5, dx * 0.35, h * 0.07, scale(tone, 0.28), lift=0)
    soft_disc(c, u - w * 0.25, v + h * 0.78, w * 0.4, h * 0.2, WHITE, 0.22, 1.2, add=True)


@sprop("mv_boxes", aspect=1.45, fill=0.85)
def mv_boxes(c, P):
    rng = c.rng
    ao(c, 0.1, 0.0, 1.45, 0.24)
    _box(c, -0.28, 0.0, 0.62, 0.40, 0.14, 0.09, scale(CARD, 1.02), P, rng, label=True)
    _box(c, 0.46, 0.0, 0.52, 0.34, 0.12, 0.08, scale(CARD, 0.94), P, rng, fragile=True, hole=True)
    _box(c, 0.03, 0.40, 0.48, 0.32, 0.13, 0.08, scale(CARD, 1.08), P, rng, label=False, hole=True)
    # a little bubble-wrap-wrapped lamp / loose packing paper on top
    for k in range(5):
        c.circle(-0.30 + k * 0.05, 0.75 + (k % 2) * 0.012, 0.03, (0.93, 0.93, 0.88), lift=0.2, alpha=0.9)


@sprop("mv_trolley", aspect=0.85, fill=1.0)
def mv_trolley(c, P):
    rng = c.rng
    frame = P.accent_dark
    ao(c, 0.0, 0.0, 0.8, 0.18)
    for ux in (-0.17, 0.17):
        c.rect(ux, 0.52, 0.038, 0.96, scale(frame, 0.9), lift=0.3, r=0.01)
        c.line(ux - 0.010, 0.10, ux - 0.010, 0.94, 0.008, mix(frame, WHITE, 0.5), 0.6)
    for vv in (0.58, 0.82):
        c.rect(0.0, vv, 0.34, 0.026, scale(STEEL, 0.9), lift=0.3)
    c.rect(0.0, 0.99, 0.50, 0.045, frame, lift=0.3, r=0.02)
    c.line(-0.25, 0.99, -0.17, 0.92, 0.03, frame)
    c.line(0.25, 0.99, 0.17, 0.92, 0.03, frame)
    c.rect(0.0, 0.99, 0.28, 0.022, (0.10, 0.10, 0.12), lift=0.2, r=0.01)
    # wheels
    for sg in (-1, 1):
        u = sg * 0.30
        c.circle(u + 0.01, 0.115, 0.125, BLACK, lift=0, alpha=0.25, soft=3.0)
        c.circle(u, 0.12, 0.12, (0.10, 0.10, 0.12), lift=0.3)
        c.circle(u, 0.12, 0.075, (0.55, 0.57, 0.62), lift=0.3)
        c.circle(u, 0.12, 0.028, (0.25, 0.26, 0.30), lift=0.2)
        for k in range(5):
            a = k * 1.2566
            c.circle(u + math.cos(a) * 0.05, 0.12 + math.sin(a) * 0.05, 0.007, (0.2, 0.2, 0.24), lift=0)
        gloss(c, u - 0.04, 0.17, 0.035, 0.02, 20, 0.5)
    # load plate and boxes strapped on
    c.poly([(-0.30, 0.04), (0.30, 0.04), (0.34, 0.0), (-0.34, 0.0)], scale(STEEL, 0.7), lift=0.2)
    _box(c, 0.0, 0.05, 0.56, 0.28, 0.09, 0.05, scale(CARD, 1.0), P, rng, label=True)
    _box(c, 0.0, 0.34, 0.48, 0.26, 0.08, 0.05, scale(CARD, 1.1), P, rng, fragile=True)
    c.line(-0.30, 0.16, 0.30, 0.16, 0.014, (0.12, 0.12, 0.14), 0.9)
    c.line(-0.30, 0.18, 0.30, 0.18, 0.004, (0.5, 0.5, 0.56), 0.7)
    c.circle(0.0, 0.17, 0.020, scale(STEEL, 1.0), lift=0.3)


@sprop("mv_bubble_wrap", aspect=1.9, fill=0.50)
def mv_bubble_wrap(c, P):
    rng = c.rng
    ao(c, 0.1, 0.0, 1.3, 0.22)
    sheet = (0.86, 0.94, 1.0)
    # unrolled sheet on the floor with a grid of bubbles
    c.poly([(-0.52, 0.22), (0.50, 0.22), (0.66, 0.0), (-0.40, 0.0)], sheet, lift=0.06, alpha=0.85)
    for r in range(4):
        v = 0.04 + r * 0.045
        for k in range(10):
            u = -0.38 + k * 0.095 + r * 0.045 + (0.02 if r % 2 else 0.0) - r * 0.0
            c.ellipse(u + (0.12 - r * 0.04) * 0.0 + 0.0, v, 0.034, 0.020, mix(sheet, (0.55, 0.75, 0.92), 0.5), lift=0.2, alpha=0.7)
            c.ellipse(u - 0.01, v + 0.007, 0.012, 0.006, WHITE, lift=0, alpha=0.9)
    # the roll lying behind it
    c.rect(-0.02, 0.38, 1.04, 0.28, scale(sheet, 0.92), r=0.14, lift=0.25, alpha=0.95)
    c.rect(-0.02, 0.44, 1.0, 0.08, mix(sheet, WHITE, 0.5), r=0.04, lift=0, alpha=0.6)
    for r in range(3):
        for k in range(14):
            c.ellipse(-0.50 + k * 0.073 + (0.03 if r % 2 else 0.0), 0.28 + r * 0.09, 0.028, 0.026, mix(sheet, (0.55, 0.75, 0.92), 0.55), lift=0.2, alpha=0.6)
    c.ellipse(0.50, 0.38, 0.075, 0.14, scale(sheet, 0.85), lift=0.1)
    c.ellipse(0.50, 0.38, 0.05, 0.10, (0.82, 0.66, 0.42), lift=0.1)
    c.ellipse(0.50, 0.38, 0.022, 0.045, (0.35, 0.28, 0.22), lift=0)
    gloss(c, -0.2, 0.50, 0.42, 0.018, 0, 0.7)
    for _ in range(6):
        c.ellipse(rng.uniform(-0.4, 0.5), rng.uniform(0.02, 0.2), 0.012, 0.01, WHITE, lift=0, alpha=0.7)


@sprop("mv_tape_gun", aspect=1.2, fill=0.62)
def mv_tape_gun(c, P):
    ao(c, 0.0, 0.0, 0.9, 0.16)
    tape = (0.84, 0.66, 0.40)
    body = P.accent
    c.line(0.06, 0.30, 0.48, 0.08, 0.13, scale(body, 0.7))                     # grip
    c.line(0.04, 0.32, 0.46, 0.10, 0.10, body)
    for k in range(5):
        t = 0.2 + k * 0.14
        c.line(0.06 + 0.42 * t - 0.03, 0.30 - 0.22 * t - 0.01, 0.06 + 0.42 * t + 0.03, 0.30 - 0.22 * t + 0.03, 0.012, (0.1, 0.1, 0.12), 0.7)
    c.circle(0.02, 0.45, 0.36, scale(tape, 0.55), lift=0.1)                      # tape roll seen from the side
    c.circle(0.0, 0.46, 0.34, tape, lift=0.18)
    c.circle(0.0, 0.46, 0.17, (0.92, 0.88, 0.78), lift=0.1)
    c.circle(0.0, 0.46, 0.14, (0.55, 0.45, 0.32), lift=0.1)
    c.circle(0.0, 0.46, 0.06, scale(body, 0.8), lift=0.3)
    for k in range(18):
        a = k * 0.35
        c.circle(math.cos(a) * 0.255, 0.46 + math.sin(a) * 0.255, 0.012, mix(tape, WHITE, 0.3), lift=0, alpha=0.4)
    gloss(c, -0.12, 0.62, 0.10, 0.05, 40, 0.55)
    c.poly([(-0.34, 0.20), (-0.55, 0.08), (-0.52, 0.04), (-0.30, 0.14)], tape, lift=0.1)       # loose tape end
    c.poly([(-0.20, 0.12), (-0.30, 0.14), (-0.26, 0.06), (-0.18, 0.06)], scale(STEEL, 1.0), lift=0.3)   # blade
    c.rect(-0.01, 0.46, 0.04, 0.38, body, lift=0.2)


def _truck(S, u, v, k, P, dark):
    """A box truck (side view, facing right) standing on the road at stage (u, v); k = length."""
    body = mix(P.paper, WHITE, 0.3) if not dark else scale(P.paper, 0.55)
    S.rect(u - k * 0.10, v - k * 0.24, k * 0.78, k * 0.40, body, lift=0.05, r=0.01)
    S.rect(u - k * 0.10, v - k * 0.12, k * 0.78, k * 0.06, P.accent, lift=0.0)
    S.rect(u - k * 0.26, v - k * 0.28, k * 0.26, k * 0.12, P.accent_light, lift=0.0, alpha=0.9)
    S.poly([(u + k * 0.30, v - k * 0.02), (u + k * 0.30, v - k * 0.38), (u + k * 0.46, v - k * 0.38), (u + k * 0.56, v - k * 0.22), (u + k * 0.56, v - k * 0.02)],
           scale(P.accent, 0.95))
    S.poly([(u + k * 0.40, v - k * 0.33), (u + k * 0.47, v - k * 0.33), (u + k * 0.53, v - k * 0.22), (u + k * 0.40, v - k * 0.22)], (0.62, 0.80, 0.92))
    S.rect(u + k * 0.08, v - k * 0.015, k * 1.12, k * 0.04, (0.12, 0.12, 0.14), lift=0.0)
    for wu in (-0.22, 0.12, 0.44):
        S.circle(u + k * wu, v + k * 0.0, k * 0.075, (0.08, 0.08, 0.10), lift=0.1)
        S.circle(u + k * wu, v + k * 0.0, k * 0.035, (0.62, 0.64, 0.68), lift=0.1)


@niche("movers", "Packers and movers", subjects=("mv_boxes",),
       strong=("packers and movers", "packers movers", "movers and packers", "movers", "relocation", "home shifting", "house shifting", "packers", "office shifting",
               "moving company", "shifting service", "पैकर्स एंड मूवर्स", "पैकर्स", "मूवर्स", "घर शिफ्टिंग", "सामान शिफ्टिंग"),
       weak=("moving", "shifting", "cartons", "boxes", "transport", "truck", "relocate", "loading"),
       accent="#ef6c00", mood="light", group="trades", avoid=("courier", "logistics"))
def movers(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    plank = mix(P.floor_top, P.surface, 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # wide roller-door opening onto a street with the moving truck parked outside
        S.rect(1.15, 0.31, 1.80, 0.56, scale(P.wall_bot, 0.55), lift=0.0)
        sky_t, sky_b = ((0.58, 0.78, 0.96), (0.93, 0.96, 1.0)) if not dk else ((0.10, 0.14, 0.30), (0.75, 0.50, 0.40))
        S.gradient_rect(0.30, 0.05, 2.00, 0.50, sky_t, sky_b)
        for k in range(7):                                                                          # distant buildings
            S.rect(0.38 + k * 0.26, 0.40, 0.18, 0.12 + 0.04 * (k % 3), scale(sky_b, 0.78 if not dk else 0.5), lift=0.0, alpha=0.9)
        S.rect(1.15, 0.52, 1.7, 0.08, (0.40, 0.42, 0.46) if not dk else (0.14, 0.15, 0.2), lift=0.0)           # road
        S.rect(1.15, 0.53, 1.7, 0.006, (0.95, 0.85, 0.3), lift=0.0, alpha=0.8)
        _truck(S, 1.18, 0.55, 0.78, P, dk)
        S.glow(1.15, 0.25, 1.0, mix(P.light, WHITE, 0.5), 0.30 if not dk else 0.18)
        S.rect(0.30, 0.31, 0.04, 0.58, scale(P.wall_bot, 0.4), lift=0.0)
        S.rect(2.0, 0.31, 0.04, 0.58, scale(P.wall_bot, 0.4), lift=0.0)
        S.rect(1.0, 0.598, 14.0, 0.028, mix(P.paper, WHITE, 0.4), lift=0.0)
        S.floor(0.62, plank, scale(plank, 0.8))
        S.light_shaft(0.35, 0.60, 1.95, 0.60, 2.6, 1.0, -0.15, 1.0, alpha=0.16)
    S.wood(-5.0, 0.62, 7.0, 2.6, plank, plank=0.12, grain=0.5)
    S.gradient_rect(-5.0, 0.62, 7.0, 0.68, scale(plank, 0.65), scale(plank, 0.95), alpha=0.9)
    S.soft(1.15, 0.86, 1.0, 0.18, P.light, 0.30, 1.5, add=True)
    S.put("mv_trolley", 0.70, 0.92, 0.52, color=P)
    S.put("mv_bubble_wrap", 1.56, 0.96, 0.16, color=P)
    S.put("mv_boxes", 1.10, 0.90, 0.44, color=P, subject=True)
    S.put("mv_tape_gun", 1.12, 0.995, 0.085, color=P)
    S.focus("detail", 1.10, 0.76)
    with S.near():
        S.circle(0.54, 1.10, 0.09, mix(CARD, P.accent, 0.3), 0.8)
        S.ellipse(1.84, 1.08, 0.10, 0.04, P.accent, 0.5, 15)


# ====================================================================================================== garden and lawn care
GRASS = (0.30, 0.58, 0.20)
MOWER = (0.92, 0.34, 0.12)
TERRA = (0.78, 0.40, 0.25)


def _petal_flower(c, u, v, r, col, centre=(0.98, 0.82, 0.18), n=5):
    for k in range(n):
        a = 2 * math.pi * k / n
        c.ellipse(u + math.cos(a) * r * 0.62, v + math.sin(a) * r * 0.62, r * 0.50, r * 0.38, col, angle=math.degrees(a), lift=0.15)
    c.circle(u, v, r * 0.34, centre, lift=0.2)


@sprop("ld_mower", aspect=1.55, fill=1.0)
def ld_mower(c, P):
    rng = c.rng
    body = MOWER
    c.x -= 0.13 * c.s                                    # recentre the drawing (bag and handle reach far right) so the framed box matches it
    ao(c, 0.1, 0.0, 1.3, 0.2)
    # clippings thrown into the bag
    for _ in range(14):
        c.ellipse(rng.uniform(0.25, 0.60), rng.uniform(0.18, 0.34), rng.uniform(0.012, 0.024), rng.uniform(0.006, 0.010), GRASS if rng.random() < 0.7 else (0.55, 0.78, 0.30),
                  angle=rng.uniform(0, 180), lift=0.1)
    # handle (behind the bag) and control bar
    c.line(0.38, 0.32, 0.70, 0.93, 0.045, scale(STEEL, 0.55))
    c.line(0.375, 0.32, 0.685, 0.93, 0.012, mix(STEEL, WHITE, 0.55), 0.7)
    c.line(0.60, 0.80, 0.80, 0.84, 0.03, scale(STEEL, 0.6))
    c.line(0.62, 0.92, 0.84, 0.98, 0.07, (0.10, 0.10, 0.12))
    c.line(0.62, 0.94, 0.84, 1.0, 0.012, (0.45, 0.46, 0.5), 0.8)
    c.line(0.56, 0.78, 0.70, 0.90, 0.016, (0.95, 0.80, 0.15))
    # grass bag: mesh fabric with a stitched frame and speckle
    bag = (0.46, 0.62, 0.30)
    _qpoly(c, [(0.40, 0.24), (0.84, 0.28), (0.88, 0.52), (0.74, 0.62), (0.46, 0.58)], scale(bag, 0.78), lift=0.2)
    _qpoly(c, [(0.40, 0.30), (0.78, 0.31), (0.80, 0.50), (0.68, 0.58), (0.46, 0.56)], bag, lift=0.22)
    for _ in range(26):
        c.circle(rng.uniform(0.46, 0.80), rng.uniform(0.30, 0.56), rng.uniform(0.004, 0.008), scale(bag, rng.choice((0.7, 1.25))), lift=0, alpha=0.55)
    c.line(0.46, 0.58, 0.74, 0.62, 0.018, scale(bag, 0.55))
    gloss(c, 0.58, 0.52, 0.12, 0.04, 20, 0.35)
    # wheels
    for (u, v, r) in ((0.26, 0.17, 0.17), (-0.46, 0.11, 0.11)):
        c.circle(u + 0.015, v - 0.015, r * 1.05, BLACK, lift=0, alpha=0.3)
        c.circle(u, v, r, (0.09, 0.09, 0.10), lift=0.25)
        c.circle(u, v, r * 0.62, scale(body, 0.7), lift=0.3)
        c.circle(u, v, r * 0.25, (0.80, 0.82, 0.86), lift=0.3)
        for k in range(8):
            a = k * 0.7854
            c.circle(u + math.cos(a) * r * 0.9, v + math.sin(a) * r * 0.9, r * 0.05, (0.28, 0.28, 0.30), lift=0)
        gloss(c, u - r * 0.35, v + r * 0.45, r * 0.3, r * 0.14, 30, 0.5)
    # steel deck and engine cover
    _qpoly(c, [(-0.58, 0.20), (0.50, 0.20), (0.50, 0.38), (-0.50, 0.36), (-0.60, 0.28)], scale(body, 0.74), lift=0.25)
    c.rect(-0.05, 0.215, 1.08, 0.018, mix(body, WHITE, 0.4), lift=0, alpha=0.6)
    c.rect(-0.05, 0.36, 1.0, 0.012, mix(body, WHITE, 0.3), lift=0, alpha=0.7)
    _qpoly(c, [(-0.36, 0.37), (0.32, 0.37), (0.28, 0.52), (0.10, 0.62), (-0.20, 0.62), (-0.34, 0.50)], scale(body, 0.98), lift=0.3)
    for k in range(5):
        c.line(-0.18 + k * 0.07, 0.50, -0.16 + k * 0.07, 0.40, 0.012, scale(body, 0.5), 0.8)
    c.rect(0.12, 0.575, 0.12, 0.05, (0.10, 0.10, 0.12), lift=0.2, r=0.02)
    c.circle(-0.02, 0.62, 0.035, (0.12, 0.12, 0.14), lift=0.3)
    gloss(c, -0.20, 0.54, 0.16, 0.05, 25, 0.65)
    soft_disc(c, 0.28, 0.42, 0.10, 0.14, BLACK, 0.25, 1.3)
    c.rect(-0.62, 0.20, 0.12, 0.04, scale(body, 0.6), lift=0.2, r=0.012)
    # deck detail: pressed ribs, a white brand stripe with badge, bolt row, rubber skirt, discharge chute and wet clippings
    c.rect(-0.04, 0.28, 1.02, 0.020, scale(body, 0.52), lift=0, alpha=0.8)
    c.rect(-0.04, 0.297, 1.00, 0.008, mix(body, WHITE, 0.55), lift=0, alpha=0.75)
    c.rect(-0.04, 0.325, 0.96, 0.026, (0.97, 0.96, 0.93), lift=0.12, r=0.008)
    c.rect(-0.30, 0.325, 0.26, 0.012, scale(body, 0.6), lift=0, alpha=0.8)
    c.circle(0.32, 0.325, 0.034, (0.12, 0.12, 0.14), lift=0.3)
    c.circle(0.32, 0.325, 0.020, (0.86, 0.82, 0.55), lift=0.3)
    for k in range(6):
        c.circle(-0.50 + k * 0.17, 0.236, 0.011, (0.82, 0.82, 0.85), lift=0.3)
    c.rect(-0.05, 0.188, 1.10, 0.026, (0.07, 0.07, 0.08), lift=0.1, r=0.01)
    _qpoly(c, [(0.46, 0.22), (0.64, 0.24), (0.62, 0.34), (0.48, 0.36)], scale(body, 0.5), lift=0.2)
    c.line(0.50, 0.30, 0.60, 0.31, 0.012, (0.05, 0.05, 0.06), 0.8)
    c.line(-0.52, 0.34, -0.40, 0.46, 0.014, (0.80, 0.82, 0.86))
    c.circle(-0.39, 0.465, 0.026, (0.10, 0.10, 0.12), lift=0.3)
    for _ in range(7):
        c.ellipse(rng.uniform(-0.50, 0.44), rng.uniform(0.21, 0.35), rng.uniform(0.010, 0.020), rng.uniform(0.004, 0.007), GRASS, angle=rng.uniform(0, 180), lift=0, alpha=0.7)
    gloss(c, -0.30, 0.355, 0.30, 0.012, 0, 0.55)


@sprop("ld_watering_can", aspect=1.75, fill=0.80)
def ld_watering_can(c, P):
    rng = c.rng
    col = (0.80, 0.84, 0.88)
    ao(c, 0.1, 0.0, 1.0, 0.18)
    # long spout with a rose, and the water it sprinkles
    _tube(c, -0.18, 0.12, -0.70, 0.62, 0.08, scale(col, 0.95), 0.6)
    c.ellipse(-0.72, 0.64, 0.10, 0.045, scale(col, 0.7), angle=50, lift=0.2)
    c.ellipse(-0.73, 0.65, 0.075, 0.032, scale(col, 1.15), angle=50, lift=0.2)
    for k in range(6):
        c.circle(-0.76 + k * 0.012, 0.65 + k * 0.006, 0.006, (0.2, 0.2, 0.26), lift=0)
    for k in range(10):
        c.line(-0.78 - k * 0.012, 0.60 - k * 0.02, -0.80 - k * 0.03, 0.40 - k * 0.04, 0.006, (0.78, 0.90, 1.0), 0.55)
    # handle behind, then the tin body with a darker side and a hoop
    c.path([(0.26, 0.20), (0.50, 0.30), (0.48, 0.55), (0.18, 0.64)], 0.055, scale(col, 0.7), smooth=True)
    hshade_box(c, 0.0, 0.25, 0.60, 0.50, scale(col, 1.10), scale(col, 0.58), r=0.03)
    c.ellipse(0.0, 0.0, 0.30, 0.30 * TILT * 0.8, scale(col, 0.5), lift=0)
    hshade_box(c, 0.0, 0.25 + 0.001, 0.60, 0.50, scale(col, 1.10), scale(col, 0.58), r=0.03)
    c.ellipse(0.0, 0.50, 0.30, 0.30 * TILT, scale(col, 1.2), lift=0.1)
    c.ellipse(0.0, 0.505, 0.26, 0.26 * TILT, scale(col, 0.38), lift=0)
    c.ellipse(0.0, 0.49, 0.25, 0.25 * TILT, (0.45, 0.65, 0.85), lift=0.1, alpha=0.9)
    c.rect(0.0, 0.11, 0.60, 0.012, scale(col, 0.6), lift=0, alpha=0.9)
    c.rect(0.0, 0.38, 0.60, 0.012, scale(col, 0.6), lift=0, alpha=0.9)
    c.path([(-0.28, 0.46), (-0.10, 0.76), (0.30, 0.74), (0.34, 0.46)], 0.05, scale(col, 0.85), smooth=True)
    c.path([(-0.285, 0.47), (-0.11, 0.765), (0.30, 0.745)], 0.012, mix(col, WHITE, 0.55), alpha=0.8, smooth=True)
    gloss(c, -0.20, 0.30, 0.024, 0.18, 0, 0.6)
    soft_disc(c, 0.22, 0.25, 0.12, 0.25, BLACK, 0.2, 1.3)
    for _ in range(8):
        c.circle(rng.uniform(-0.2, 0.2), rng.uniform(0.05, 0.4), rng.uniform(0.004, 0.009), mix(col, WHITE, 0.4), lift=0, alpha=0.4)


@sprop("ld_pots", aspect=1.65, fill=0.92)
def ld_pots(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.22)
    specs = ((-0.50, 0.30, 0.19, 0), (0.0, 0.40, 0.24, 1), (0.50, 0.34, 0.20, 2))
    for u, h, r, kind in specs:
        top = TERRA
        _qpoly(c, [(u - r, h), (u + r, h), (u + r * 0.72, 0.0), (u - r * 0.72, 0.0)], scale(top, 0.72), lift=0.2)
        _qpoly(c, [(u - r, h), (u + r * 0.25, h), (u + r * 0.20, 0.0), (u - r * 0.72, 0.0)], scale(top, 1.12), lift=0.12)
        c.ellipse(u, 0.0, r * 0.72, r * 0.72 * TILT * 0.7, scale(top, 0.55), lift=0)
        c.rect(u, h - 0.025, r * 2.12, 0.07, scale(top, 1.04), lift=0.25, r=0.014)
        c.ellipse(u, h + 0.01, r * 1.0, r * 0.38, (0.22, 0.14, 0.10), lift=0)
        c.line(u - r * 0.9, h - 0.01, u + r * 0.9, h - 0.01, 0.006, scale(top, 0.55), 0.6)
        gloss(c, u - r * 0.62, h * 0.55, r * 0.07, h * 0.32, 0, 0.45)
        base_v = h + 0.015
        if kind == 0:                                                        # succulent rosette
            for k in range(9):
                a = k * 0.449*14/11 + rng.uniform(-0.1, 0.1)
                ln = 0.13 if k < 8 else 0.09
                leaf(c, u, base_v + 0.01, ln, math.degrees(a) % 360 * 0.5 + 25 + (k % 2) * 70, (0.35, 0.62, 0.45) if k % 2 else (0.28, 0.54, 0.40), 0.55)
        elif kind == 1:                                                      # leafy plant with a few flowers
            for k in range(8):
                leaf(c, u + rng.uniform(-0.05, 0.05), base_v, rng.uniform(0.28, 0.42), rng.uniform(40, 140), (0.16 + rng.random() * 0.1, 0.46 + rng.random() * 0.14, 0.2), 0.45)
            for k in range(3):
                fu, fv = u + (k - 1) * 0.12 + rng.uniform(-0.03, 0.03), base_v + 0.26 + (k % 2) * 0.12
                c.line(u, base_v, fu, fv, 0.012, (0.2, 0.5, 0.2))
                _petal_flower(c, fu, fv, 0.075, P.accent)
        else:                                                                # flowering pot
            for k in range(8):
                leaf(c, u + rng.uniform(-0.04, 0.04), base_v, rng.uniform(0.14, 0.22), rng.uniform(30, 150), (0.2, 0.5, 0.22), 0.5)
            for k in range(3):
                fu, fv = u + rng.uniform(-0.15, 0.15), base_v + rng.uniform(0.07, 0.20)
                _petal_flower(c, fu, fv, 0.055, rng.choice((P.accent_light, (0.98, 0.85, 0.25), (0.98, 0.97, 0.95), P.accent2)))


@sprop("ld_trimmer", aspect=3.4, fill=0.28)
def ld_trimmer(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.12)
    c.path([(0.62, 0.05), (0.80, 0.0), (0.98, 0.07), (1.12, 0.02)], 0.018, (0.08, 0.08, 0.10), smooth=True)
    c.rect(-0.35, 0.12, 0.98, 0.07, scale(STEEL, 1.0), lift=0.3, r=0.01)
    for k in range(18):
        u = -0.80 + k * 0.058
        c.poly([(u, 0.09), (u + 0.04, 0.09), (u + 0.02, 0.04)], scale(STEEL, 0.8), lift=0.2)
        c.rect(u + 0.02, 0.16, 0.030, 0.018, scale(STEEL, 0.65), lift=0.1)
    c.line(-0.80, 0.14, 0.12, 0.14, 0.008, WHITE, 0.6)
    body = MOWER
    c.rect(0.38, 0.19, 0.56, 0.20, scale(body, 0.85), r=0.07, lift=0.3)
    c.rect(0.36, 0.22, 0.50, 0.12, body, r=0.05, lift=0.25)
    c.rect(0.22, 0.34, 0.20, 0.05, (0.10, 0.10, 0.12), lift=0.2, r=0.02)
    c.path([(0.50, 0.34), (0.62, 0.52), (0.82, 0.50), (0.78, 0.30)], 0.045, (0.12, 0.12, 0.14), smooth=True)
    c.rect(0.12, 0.23, 0.12, 0.06, scale(body, 0.65), lift=0.2)
    gloss(c, 0.28, 0.27, 0.16, 0.025, 0, 0.6)
    for k in range(6):
        c.line(0.46 + k * 0.05, 0.14, 0.46 + k * 0.05, 0.19, 0.010, scale(body, 0.5), 0.8)
    for _ in range(8):
        c.ellipse(rng.uniform(-0.8, -0.1), rng.uniform(0.0, 0.06), rng.uniform(0.012, 0.022), 0.008, GRASS, angle=rng.uniform(0, 180), lift=0.1)


@niche("landscape", "Garden and lawn care", subjects=("ld_mower",),
       strong=("lawn care", "gardening service", "gardening services", "landscaping", "landscape design", "garden maintenance", "lawn mowing", "nursery", "plant nursery",
               "gardener", "garden design", "माली", "बागवानी", "लॉन", "गार्डन सर्विस", "mali", "bagwani"),
       weak=("garden", "lawn", "plants", "grass", "hedge", "flowers", "pots", "greenery"),
       accent="#558b2f", mood="light", group="trades", avoid=("florist", "farm"))
def landscape(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    k = 0.42 if dk else 1.0
    g1, g2 = scale((0.38, 0.66, 0.22), k), scale((0.30, 0.58, 0.18), k)
    g1, g2 = mix(g1, P.accent, 0.18), mix(g2, P.accent, 0.18)
    g1, g2 = mix(g1, (0.55, 0.60, 0.30), 0.22), mix(g2, (0.45, 0.52, 0.26), 0.22)                # less saturated, sun-bleached olive greens
    sky_t, sky_b = ((0.52, 0.76, 0.96), (0.92, 0.97, 1.0)) if P.mood != "dark" else ((0.07, 0.10, 0.22), (0.35, 0.30, 0.42))
    if P.mood == "warm":
        sky_t, sky_b = (0.62, 0.80, 0.95), (1.0, 0.93, 0.80)
    hedge = scale(mix((0.16, 0.38, 0.14), P.accent_dark, 0.2), 0.7 if not dk else 0.5)
    with S.far():
        S.gradient_rect(-5.0, -0.8, 7.0, 0.62, sky_t, sky_b)
        S.glow(0.25, 0.06, 0.8, mix(P.light, WHITE, 0.4), 0.35 if not dk else 0.1)
        for k_ in range(9):                                                                         # tree crowns far away
            u = -0.2 + k_ * 0.27 + rng.uniform(-0.05, 0.05)
            r = rng.uniform(0.11, 0.18)
            S.circle(u, 0.30 - r * 0.2, r, scale(hedge, 1.35), lift=0.0)
            S.circle(u - r * 0.3, 0.28 - r * 0.3, r * 0.6, scale(hedge, 1.65), lift=0.0, alpha=0.8)
        S.rect(1.0, 0.50, 14.0, 0.26, hedge, lift=0.0)                                              # clipped hedge
        for k_ in range(30):
            S.circle(-1.6 + k_ * 0.16 + rng.uniform(-0.03, 0.03), 0.375 + rng.uniform(-0.02, 0.02), rng.uniform(0.04, 0.07), scale(hedge, rng.uniform(0.9, 1.35)), lift=0.0)
        S.rect(1.0, 0.64, 14.0, 0.04, scale(hedge, 0.6), lift=0.0)
        if dk:
            S.bokeh(26, -0.4, 0.28, 2.4, 0.56, [(1.0, 0.85, 0.5), (1.0, 0.72, 0.4)], 0.01, 0.03, 0.55)
        else:
            S.bokeh(10, 0.0, 0.1, 2.0, 0.4, [(1.0, 0.98, 0.8), (0.9, 1.0, 0.8)], 0.012, 0.04, 0.3)
        S.light_shaft(0.15, 0.0, 0.4, 0.0, 1.5, 0.64, 0.7, 0.64, alpha=0.10 if not dk else 0.04)
    # striped lawn: soft gradient with alternating mown bands, dappled sun, clover and blade texture
    S.rect(1.0, 1.6, 14.0, 2.2, scale(g1, 1.08), lift=0.0)
    for i in range(7):                                                                             # lawn darkens towards the camera in soft steps (cheap gradient)
        S.rect(1.0, 0.62 + (2.7 - 0.62) / 2 + 0.16 * i, 14.0, (2.7 - 0.62) - 0.32 * i, scale(g2, 0.62), lift=0.0, alpha=0.075)
    vs = [0.60 + 0.30 / (1 - 0.10 * n) - 0.30 for n in range(0, 10)]
    for n in range(0, 9):
        v0, v1 = vs[n], vs[n + 1]
        if n % 2 == 1:
            S.rect(1.0, (v0 + v1) / 2, 14.0, v1 - v0 + 0.002, scale(g1, 0.80), lift=0.0, alpha=0.40)
        else:
            S.rect(1.0, (v0 + v1) / 2, 14.0, v1 - v0 + 0.002, mix(g1, (0.85, 0.85, 0.45), 0.35), lift=0.0, alpha=0.14)
    S.rect(1.0, 0.70, 14.0, 0.07, scale(hedge, 0.5), lift=0.0, alpha=0.22)                       # hedge shadow on the lawn
    for _ in range(110):                                                                           # grass blades
        u, v = rng.uniform(-0.2, 2.4), rng.uniform(0.70, 1.35)
        sc = 0.5 + (v - 0.7) * 1.3
        S.line(u, v, u + rng.uniform(-0.012, 0.012), v - rng.uniform(0.012, 0.03) * sc, 0.0035 * sc, scale(g1, rng.choice((0.72, 0.85, 1.25, 1.4))), 0.55)
    for _ in range(10):                                                                            # clover leaves and tiny daisies
        u, v = rng.uniform(0.0, 2.2), rng.uniform(0.78, 1.3)
        S.ellipse(u, v, 0.014, 0.006, scale(g2, 0.82), lift=0.0, alpha=0.6)
        if rng.random() < 0.4:
            S.circle(u + 0.02, v - 0.006, 0.005, (0.98, 0.97, 0.9), lift=0.0, alpha=0.9)
    # flower bed along the hedge
    soil = scale((0.30, 0.20, 0.13), 1.0 if not dk else 0.6)
    S.rect(1.0, 0.655, 14.0, 0.06, soil, lift=0.0)
    for _ in range(46):
        u = rng.uniform(0.1, 2.1)
        v = 0.63 + rng.uniform(0.0, 0.03)
        col = rng.choice((P.accent, P.accent2, P.accent_light, (0.98, 0.86, 0.25), (0.97, 0.96, 0.94)))
        S.line(u, v + 0.03, u, v, 0.004, (0.2, 0.45, 0.2))
        S.circle(u, v - 0.004, rng.uniform(0.012, 0.022), scale(col, 0.7 if dk else 1.0), lift=0.15)
    S.soft(1.1, 0.86, 0.9, 0.18, P.light if not dk else (1.0, 0.8, 0.5), 0.26 if not dk else 0.4, 1.5, add=True)
    S.put("ld_pots", 0.80, 0.82, 0.27, color=P)
    S.put("ld_watering_can", 0.62, 1.02, 0.22, color=P)
    S.put("ld_mower", 1.10, 0.97, 0.52, color=P, subject=True)
    S.put("ld_trimmer", 1.30, 1.01, 0.085, color=P)
    S.focus("detail", 1.02, 0.80)
    with S.near():
        S.ellipse(0.50, 1.08, 0.12, 0.05, g1 if not dk else (0.2, 0.4, 0.2), 20)
        S.circle(1.82, 1.10, 0.07, P.accent2, 0.7)


# ====================================================================================================== fabrication and welding
HOT = (1.0, 0.62, 0.22)
SPARK = (1.0, 0.86, 0.55)


def _sparks_c(c, u, v, n, spread, rng, length=0.2, up=1.0):
    """A fountain of sparks (bright streaks with a hot glow) in prop space."""
    soft_disc(c, u, v, spread * 0.5, spread * 0.4, HOT, 0.55, 1.6, add=True)
    for _ in range(n):
        a = math.radians(rng.uniform(15, 165)) if up > 0 else math.radians(rng.uniform(-60, 60))
        ln = rng.uniform(0.3, 1.0) * length
        du, dv = math.cos(a) * ln, math.sin(a) * ln * (1.0 if up > 0 else 0.6) - (ln * 0.25 if up > 0 else 0.0)
        c.line(u, v, u + du, v + dv, 0.006, SPARK, 0.9)
        c.line(u + du * 0.55, v + dv * 0.55, u + du, v + dv, 0.003, WHITE, 0.9)
        if rng.random() < 0.5:
            c.circle(u + du * 1.05, v + dv * 1.05, 0.007, (1.0, 0.95, 0.75), lift=0, alpha=0.9)


def _sparks_s(S, u, v, n, length, rng, up=True):
    S.glow(u, v, length * 1.1, HOT, 0.55)
    for _ in range(n):
        a = math.radians(rng.uniform(10, 170)) if up else math.radians(rng.uniform(-70, 70))
        ln = rng.uniform(0.3, 1.0) * length
        du, dv = math.cos(a) * ln, -math.sin(a) * ln * (1.0 if up else 0.5) + (ln * 0.2 if up else 0.0)
        S.line(u, v, u + du, v + dv, 0.003, SPARK, 0.85)
        S.line(u + du * 0.6, v + dv * 0.6, u + du, v + dv, 0.0016, WHITE, 0.9)


def _flame(c, x0, y0, h, w, sweep, col, lift=0.25, alpha=1.0, n=16, curl=0.0):
    """One smooth flame tongue: a bulging teardrop whose spine sweeps right in an S and ends in a fine tip that curls back."""
    left, right = [], []
    for k in range(n + 1):
        t = k / float(n)
        sx = x0 + sweep * (t ** 1.25) - curl * (t ** 3.0) + math.sin(t * 3.6) * w * 0.12 * t
        sy = y0 + h * t
        hw = w * 0.5 * (1.0 - t) ** 0.7 * (1.0 + 0.10 * math.sin(t * 5.0))
        left.append((sx - hw, sy))
        right.append((sx + hw, sy))
    _qpoly(c, left + right[::-1], col, lift, alpha)


@sprop("wd_helmet", aspect=1.10, fill=1.0)
def wd_helmet(c, P):
    rng = c.rng
    shell = (0.27, 0.29, 0.34)
    ao(c, 0.0, 0.0, 1.0, 0.18)
    c.ellipse(0.0, 0.13, 0.40, 0.11, (0.02, 0.02, 0.03), lift=0)
    body = [(-0.44, 0.10), (0.44, 0.10), (0.51, 0.40), (0.47, 0.78), (0.30, 0.96), (0.0, 1.0), (-0.30, 0.96), (-0.47, 0.78), (-0.51, 0.40)]
    _qpoly(c, body, shell, 0.34)
    c.rect(0.47, 0.45, 0.07, 0.62, BLACK, lift=0, alpha=0.18)
    # satin dome sheen from the key light, a cool rim on the lit edge and an orange rim from the sparks
    soft_disc(c, -0.28, 0.80, 0.30, 0.20, (0.80, 0.88, 1.0), 0.42, 1.4, add=True)
    c.line(-0.50, 0.40, -0.46, 0.78, 0.016, (0.78, 0.86, 1.0), 0.55)
    c.line(-0.46, 0.78, -0.30, 0.955, 0.016, (0.78, 0.86, 1.0), 0.6)
    c.line(-0.30, 0.955, 0.0, 0.995, 0.014, (0.85, 0.9, 1.0), 0.55)
    c.line(0.0, 0.995, 0.30, 0.955, 0.012, mix(HOT, WHITE, 0.3), 0.45)
    # flame decal: smooth tongues sweeping across the lower shell (three layers: accent, hot, white-yellow core)
    flames = ((0.10, 0.13, 0.15, 0.20, 0.20, 0.10), (-0.07, 0.13, 0.23, 0.26, 0.26, 0.14), (-0.27, 0.13, 0.19, 0.22, 0.22, 0.12),
              (-0.42, 0.13, 0.15, 0.17, 0.15, 0.06))
    deep = scale(P.accent, 0.80)
    for (x0, y0, h, w, sw, cu) in flames:
        _flame(c, x0, y0, h, w, sw, deep, 0.25, curl=cu)
        _flame(c, x0 - 0.004, y0 + 0.006, h * 0.74, w * 0.56, sw * 0.80, mix(HOT, WHITE, 0.30), 0.18, 0.95, 12, cu * 0.7)
    c.rect(0.0, 0.135, 0.84, 0.020, scale(P.accent, 0.5), lift=0.1, alpha=0.9)
    c.rect(0.0, 0.905, 0.80, 0.045, P.accent, r=0.02, lift=0.3)
    c.rect(0.0, 0.915, 0.78, 0.010, mix(P.accent, WHITE, 0.6), lift=0, alpha=0.8)
    # visor frame and dark glass with reflections
    c.rect(0.0, 0.55, 0.80, 0.37, (0.06, 0.06, 0.08), r=0.05, lift=0.2)
    c.rect(0.0, 0.55, 0.72, 0.29, (0.03, 0.10, 0.07), r=0.035, lift=0.3)
    soft_disc(c, 0.26, 0.45, 0.30, 0.12, HOT, 0.55, 1.4, add=True)
    c.line(-0.28, 0.66, -0.06, 0.42, 0.014, WHITE, 0.30)
    c.line(-0.18, 0.67, 0.04, 0.44, 0.008, WHITE, 0.22)
    c.line(-0.36, 0.72, -0.30, 0.72, 0.006, WHITE, 0.2)
    # side knobs, bolts and rim light from the sparks
    for sg in (-1, 1):
        c.circle(sg * 0.49, 0.55, 0.05, scale(STEEL, 1.0), lift=0.3)
        c.circle(sg * 0.49, 0.55, 0.022, (0.2, 0.2, 0.24), lift=0.2)
        c.circle(sg * 0.38, 0.31, 0.014, scale(STEEL, 0.9), lift=0.3)
    c.line(0.50, 0.30, 0.46, 0.78, 0.018, HOT, 0.75)
    for _ in range(12):
        c.circle(rng.uniform(-0.4, 0.4), rng.uniform(0.18, 0.95), rng.uniform(0.003, 0.007), (0.45, 0.46, 0.5), lift=0, alpha=0.45)
    gloss(c, -0.34, 0.90, 0.10, 0.04, 20, 0.5)


@sprop("wd_gate", aspect=1.25, fill=1.0)
def wd_gate(c, P):
    rng = c.rng
    steel = (0.40, 0.43, 0.47)
    ao(c, 0.0, 0.0, 1.3, 0.12)
    for sg in (-1, 1):                                                       # posts
        hshade_box(c, sg * 0.56, 0.5, 0.08, 1.0, scale(steel, 1.25), scale(steel, 0.55))
        c.rect(sg * 0.56, 1.0, 0.10, 0.02, scale(steel, 0.9), lift=0.2)
    for v in (0.12, 0.88):                                                   # rails
        hshade_box(c, 0.0, v, 1.04, 0.07, scale(steel, 1.3), scale(steel, 0.6))
    for k in range(7):                                                       # pickets with spear tips
        u = -0.45 + k * 0.15
        hshade_box(c, u, 0.50, 0.032, 0.76, scale(steel, 1.2), scale(steel, 0.6))
        c.poly([(u - 0.024, 0.88), (u + 0.024, 0.88), (u, 0.97)], scale(steel, 1.1), lift=0.2)
    c.line(-0.52, 0.16, 0.52, 0.84, 0.022, scale(steel, 0.8))                # brace
    arc(c, 0.0, 0.50, 0.17, 0.17, 0, 360, 0.022, scale(steel, 1.05), 1.0, 16)  # scroll ring
    arc(c, 0.0, 0.50, 0.09, 0.09, 0, 360, 0.016, scale(steel, 1.05), 1.0, 12)
    gloss(c, -0.56, 0.5, 0.012, 0.45, 0, 0.5)
    # fresh weld seams glowing at the joints, sparks over the top
    for (u, v) in ((-0.56, 0.12), (0.56, 0.12), (-0.56, 0.88), (0.56, 0.88), (0.0, 0.34), (0.30, 0.50)):
        c.circle(u, v, 0.022, (0.9, 0.55, 0.25), lift=0.1)
        soft_disc(c, u, v, 0.07, 0.07, HOT, 0.55, 1.6, add=True)
    c.circle(0.30, 0.50, 0.012, WHITE, lift=0)
    _sparks_c(c, 0.30, 0.50, 14, 0.25, rng, 0.22)
    for _ in range(30):                                                      # scratches / mill scale
        c.circle(rng.uniform(-0.6, 0.6), rng.uniform(0.05, 0.95), rng.uniform(0.003, 0.007), scale(steel, rng.choice((0.7, 1.4))), lift=0, alpha=0.5)


@sprop("wd_sheets", aspect=2.6, fill=0.36)
def wd_sheets(c, P):
    rng = c.rng
    ao(c, 0.1, 0.0, 1.25, 0.22)
    for i, (off, w, tone) in enumerate(((0.0, 1.10, 0.62), (0.04, 1.0, 0.76), (-0.05, 1.06, 0.58), (0.03, 0.98, 0.84), (-0.02, 1.04, 0.70))):
        t = scale(STEEL, tone)
        _prism(c, off, i * 0.062, w, 0.05, 0.12, 0.05, t, mix(t, WHITE, 0.3), scale(t, 0.6), lift=0.12)
        c.line(off - w / 2 + 0.02, i * 0.062 + 0.046, off + w / 2 - 0.02, i * 0.062 + 0.046, 0.005, WHITE, 0.6)
    for _ in range(26):
        u = rng.uniform(-0.45, 0.55)
        v = 0.31 + rng.uniform(0.0, 0.04)
        c.line(u, v, u + rng.uniform(0.04, 0.2), v + rng.uniform(-0.01, 0.015), 0.0025, WHITE if rng.random() < 0.5 else (0.2, 0.2, 0.24), 0.35)
    c.rect(0.0, 0.30, 1.0, 0.012, (0.7, 0.42, 0.2), lift=0, alpha=0.3)
    soft_disc(c, 0.5, 0.2, 0.2, 0.25, HOT, 0.25, 1.5, add=True)


@sprop("wd_grinder", aspect=2.3, fill=0.62)
def wd_grinder(c, P):
    rng = c.rng
    body = (0.10, 0.10, 0.12)
    ao(c, 0.0, 0.0, 1.2, 0.14)
    c.path([(-0.55, 0.10), (-0.85, 0.02), (-1.05, 0.08), (-1.12, 0.04)], 0.024, (0.05, 0.05, 0.06), smooth=True)
    c.rect(-0.12, 0.20, 0.82, 0.22, scale(P.accent, 0.95), r=0.09, lift=0.3)
    c.rect(-0.60, 0.19, 0.18, 0.15, body, r=0.04, lift=0.25)
    for k in range(7):
        c.line(-0.30 + k * 0.045, 0.11, -0.30 + k * 0.045, 0.19, 0.012, scale(P.accent, 0.45), 0.9)
    c.rect(-0.05, 0.285, 0.62, 0.022, mix(P.accent, WHITE, 0.5), lift=0, alpha=0.8)
    c.rect(-0.28, 0.35, 0.16, 0.05, body, r=0.02, lift=0.3)
    gloss(c, -0.15, 0.27, 0.30, 0.03, 0, 0.6)
    c.rect(0.38, 0.22, 0.26, 0.30, scale(STEEL, 0.65), r=0.05, lift=0.3)
    c.line(0.28, 0.10, 0.18, 0.02, 0.05, body)                                # side handle
    c.line(0.30, 0.10, 0.30, 0.34, 0.035, body)
    c.ellipse(0.62, 0.24, 0.05, 0.30, scale(STEEL, 0.5), lift=0.2)           # guard
    c.ellipse(0.66, 0.20, 0.038, 0.26, (0.82, 0.84, 0.87), lift=0.3)           # disc edge-on
    c.ellipse(0.66, 0.20, 0.016, 0.26, (0.55, 0.57, 0.62), lift=0)
    c.circle(0.66, 0.045, 0.03, (1.0, 0.8, 0.4), lift=0)
    _sparks_c(c, 0.70, 0.04, 26, 0.45, rng, 0.52, up=-1)
    gloss(c, 0.30, 0.34, 0.04, 0.05, 0, 0.5)


@niche("welding", "Fabrication and welding", subjects=("wd_helmet",),
       strong=("welding", "welder", "fabrication", "metal work", "metal fabrication", "steel gates", "iron gate", "grills", "steel fabrication", "welding work",
               "welding shop", "वेल्डिंग", "वेल्डर", "फैब्रिकेशन", "लोहे का काम", "गेट ग्रिल", "lohe ka kaam"),
       weak=("steel", "iron", "metal", "gate", "grill", "sparks", "grinding"),
       accent="#ff6f00", mood="dark", group="trades", avoid=("jewellery",))
def welding(S):
    P = S.pal
    rng = S.rng
    steel_t, steel_b = (0.34, 0.37, 0.42), (0.14, 0.15, 0.19)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        for k in range(46):                                                                # corrugated sheet wall: soft ridges, not bars
            x = -3.3 + k * 0.14
            S.rect(x, 0.2, 0.034, 0.9, scale(P.wall_bot, 0.6), lift=0.0, alpha=0.13)
            S.rect(x + 0.05, 0.2, 0.02, 0.9, mix(P.wall_top, WHITE, 0.35), lift=0.0, alpha=0.07)
        for k in range(9):                                                                 # rust streaks and a riveted seam
            S.rect(-2.8 + k * 0.85 + rng.uniform(0, 0.2), 0.12 + rng.uniform(0, 0.1), 0.03, rng.uniform(0.15, 0.3), (0.45, 0.22, 0.10), lift=0.0, alpha=0.10)
        for k in range(36):
            S.circle(-3.0 + k * 0.19, 0.30, 0.007, scale(P.wall_bot, 0.5), alpha=0.35, lift=0.0)
        # pipes and beams on racks
        for k, (rw, ru) in enumerate(((1.1, 0.62), (0.9, 0.52), (1.1, 0.62))):
            S.rect(ru, 0.20 + k * 0.07, rw, 0.026, scale(STEEL, 0.5), lift=0.0, alpha=0.8)
        S.rect(1.55, 0.18, 0.04, 0.40, scale(STEEL, 0.4), lift=0.0)
        S.rect(2.0, 0.18, 0.04, 0.40, scale(STEEL, 0.4), lift=0.0)
        for k in range(4):
            S.rect(1.78, 0.04 + k * 0.1, 0.5, 0.02, scale(STEEL, 0.45), lift=0.0)
        # a second welder at work in the back: a blinding spot with bokeh sparks
        S.glow(0.45, 0.40, 0.9, (1.0, 0.55, 0.2), 0.55)
        S.glow(0.45, 0.40, 0.25, (1.0, 0.95, 0.85), 0.9)
        S.bokeh(16, 0.1, 0.15, 0.9, 0.5, [(1.0, 0.7, 0.3), (1.0, 0.85, 0.5), (1.0, 0.55, 0.2)], 0.008, 0.025, 0.6)
        S.pendant(1.35, -0.1, 0.10, (1.0, 0.78, 0.45), 0.12)
        S.glow(1.35, 0.14, 0.9, (1.0, 0.78, 0.45), 0.25)
        S.glow(1.12, 0.52, 0.55, (1.0, 0.72, 0.4), 0.32)                                   # warm backlight behind the subject
        S.rect(1.0, 0.585, 14.0, 0.03, scale(P.wall_bot, 0.4), lift=0.0)
        S.floor(0.58, scale(P.floor_top, 0.55), scale(P.floor_bot, 0.4))
    # steel bench top: scratched dark plate with a bright edge and reflections of the arc
    S.floor(0.62, steel_t, scale(steel_b, 0.5))
    S.rect(1.0, 0.62, 14.0, 0.014, (0.66, 0.70, 0.76), lift=0.0)
    S.rect(1.0, 0.60, 14.0, 0.04, scale(steel_t, 0.6), lift=0.0)
    for _ in range(90):
        u, v = rng.uniform(-0.2, 2.3), rng.uniform(0.68, 1.4)
        S.line(u, v, u + rng.uniform(0.05, 0.3), v + rng.uniform(-0.01, 0.01), 0.002, (0.75, 0.78, 0.84) if rng.random() < 0.6 else (0.05, 0.05, 0.07), 0.25)
    for k in range(14):                                                                    # clamp holes of the weld table
        S.ellipse(-0.8 + k * 0.28, 0.66, 0.012, 0.006, (0.04, 0.04, 0.06), lift=0.0)
        S.ellipse(-0.8 + k * 0.28, 0.80, 0.010, 0.005, (0.04, 0.04, 0.06), lift=0.0, alpha=0.7)
    S.soft(1.15, 0.80, 0.95, 0.20, (1.0, 0.68, 0.32), 0.50, 1.5, add=True)               # orange arc pool on the plate
    for _ in range(12):                                                                    # weld spatter on the plate
        S.circle(rng.uniform(0.7, 1.7), rng.uniform(0.8, 1.05), rng.uniform(0.003, 0.006), (0.55, 0.40, 0.25), alpha=0.7, lift=0.0)
    S.put("wd_gate", 0.86, 0.84, 0.50, color=P)
    S.put("wd_sheets", 0.90, 1.00, 0.13, color=P)
    S.put("wd_helmet", 1.14, 0.94, 0.52, color=P, subject=True)
    S.put("wd_grinder", 1.37, 1.00, 0.15, color=P)
    S.focus("detail", 1.12, 0.70)
    _sparks_s(S, 0.93, 0.70, 22, 0.16, rng)
    with S.near():
        for _ in range(7):
            S.circle(rng.uniform(0.5, 1.8), rng.uniform(0.9, 1.1), rng.uniform(0.012, 0.03), (1.0, 0.7, 0.3), 0.8)
        S.soft(0.52, 1.08, 0.12, 0.06, (1.0, 0.55, 0.15), 0.5, 1.2, add=True)


# ====================================================================================================== tyres and auto accessories
RUBBER = (0.10, 0.10, 0.11)
ALLOY = (0.80, 0.82, 0.86)


def _alloy_face(c, u, v, r, P, spokes=5, tilt=1.0, rng=None):
    """An alloy wheel face (tilt 1 = facing the viewer): brake disc, spokes, hub cap, lug nuts, rim lip."""
    t = tilt
    c.ellipse(u, v, r, r * t, (0.10, 0.10, 0.12), lift=0)
    c.ellipse(u, v, r * 0.74, r * 0.74 * t, (0.30, 0.31, 0.34), lift=0.2)
    c.ellipse(u, v, r * 0.52, r * 0.52 * t, (0.14, 0.14, 0.16), lift=0)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes + 0.3
        pts = []
        for ra, da in ((0.14, -0.20), (0.96, -0.30), (0.96, 0.10), (0.14, 0.20)):
            ang = a + da
            pts.append((u + math.cos(ang) * r * ra, v + math.sin(ang) * r * ra * t))
        _qpoly(c, pts, ALLOY, 0.28)
        mx, my = u + math.cos(a) * r * 0.5, v + math.sin(a) * r * 0.5 * t
        soft_disc(c, mx - r * 0.04, my + r * 0.04, r * 0.15, r * 0.06, WHITE, 0.4, 1.3, add=True)
    arc(c, u, v, r * 0.98, r * 0.98 * t, 0, 360, r * 0.07, scale(ALLOY, 0.9), 1.0, 20)
    arc(c, u, v, r * 0.98, r * 0.98 * t, 100, 200, r * 0.03, WHITE, 0.8, 8)
    c.ellipse(u, v, r * 0.15, r * 0.15 * t, scale(ALLOY, 0.8), lift=0.3)
    c.ellipse(u, v, r * 0.10, r * 0.10 * t, P.accent, lift=0.3)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.9
        c.circle(u + math.cos(a) * r * 0.2, v + math.sin(a) * r * 0.2 * t, r * 0.025, (0.4, 0.42, 0.46), lift=0.2)


@sprop("ty_stack", aspect=1.3, fill=0.92)
def ty_stack(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.3)
    for i, (du, r) in enumerate(((0.0, 0.40), (0.015, 0.39), (-0.01, 0.40))):
        v = i * 0.15
        hshade_box(c, du, v + 0.075, 2 * r, 0.15, (0.26, 0.26, 0.28), (0.04, 0.04, 0.05), r=0.01)
        c.ellipse(du, v, r, r * TILT, (0.03, 0.03, 0.04), lift=0)
        hshade_box(c, du, v + 0.075 + 0.001, 2 * r, 0.15, (0.26, 0.26, 0.28), (0.04, 0.04, 0.05), r=0.01)
        for k in range(24):                                                    # tread blocks and sidewall highlights
            x = du - r * 0.94 + k * (2 * r * 0.94 / 23.0)
            c.line(x, v + 0.025, x, v + 0.125, 0.006, (0.02, 0.02, 0.03), 0.55)
        c.line(du - r * 0.95, v + 0.10, du + r * 0.95, v + 0.10, 0.004, (0.5, 0.5, 0.54), 0.30)
        c.text("225/45 R17", du - 0.04, v + 0.075, 0.032, (0.62, 0.62, 0.66), 0.14)
        gloss(c, du - r * 0.6, v + 0.09, r * 0.05, 0.05, 0, 0.35)
    # the top tyre carries an alloy wheel
    top = 3 * 0.15
    disc(c, 0.0, top, 0.40, (0.07, 0.07, 0.08), TILT, 0.12, rim=False)
    c.ellipse(0.0, top, 0.33, 0.33 * TILT, (0.14, 0.14, 0.16), lift=0.1)
    _alloy_face(c, 0.0, top + 0.004, 0.29, P, 5, TILT, rng)
    soft_disc(c, -0.12, top + 0.05, 0.30, 0.08, WHITE, 0.18, 1.3, add=True)
    soft_disc(c, 0.20, top, 0.18, 0.12, BLACK, 0.28, 1.4)


@sprop("ty_wheel", aspect=0.95, fill=1.0)
def ty_wheel(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.14)
    cx, cy, R = 0.0, 0.50, 0.50
    # tyre edge thickness at the left, then tyre, sidewall, rim
    c.ellipse(cx - 0.06, cy, R, R, (0.05, 0.05, 0.06), lift=0)
    c.circle(cx, cy, R, (0.09, 0.09, 0.10), lift=0.25)
    for k in range(48):
        a = k * 0.1309
        c.circle(cx + math.cos(a) * R * 0.97, cy + math.sin(a) * R * 0.97, 0.010, (0.02, 0.02, 0.03), lift=0, alpha=0.8)
    c.circle(cx, cy, R * 0.90, (0.13, 0.13, 0.15), lift=0.2)
    arc(c, cx, cy, R * 0.80, R * 0.80, 20, 340, 0.016, (0.55, 0.55, 0.6), 0.45, 24)
    arc(c, cx, cy, R * 0.64, R * 0.64, 0, 360, 0.010, (0.2, 0.2, 0.23), 0.8, 24)
    _alloy_face(c, cx, cy, R * 0.62, P, 5, 1.0, rng)
    c.circle(cx + R * 0.50, cy - R * 0.38, 0.016, (0.55, 0.55, 0.6), lift=0.2)               # valve
    c.text("MICHELIN", cx - 0.02, cy + R * 0.82, 0.04, (0.70, 0.70, 0.74), 0.14)
    soft_disc(c, -0.20, 0.82, 0.30, 0.16, WHITE, 0.20, 1.3, 30, add=True)
    # little stand feet
    c.rect(-0.20, 0.02, 0.18, 0.04, scale(STEEL, 0.6), lift=0.2)
    c.rect(0.20, 0.02, 0.18, 0.04, scale(STEEL, 0.6), lift=0.2)


@sprop("ty_battery", aspect=1.35, fill=0.62)
def ty_battery(c, P):
    ao(c, 0.0, 0.0, 1.0, 0.2)
    body = (0.13, 0.14, 0.17)
    _prism(c, 0.0, 0.0, 0.84, 0.40, 0.16, 0.12, body, mix(body, WHITE, 0.25), scale(body, 0.6), lift=0.18, r=0.02)
    c.rect(0.0, 0.30, 0.84, 0.07, (0.95, 0.80, 0.12), lift=0.25)
    c.rect(0.0, 0.33, 0.84, 0.012, WHITE, lift=0, alpha=0.5)
    c.rect(-0.12, 0.17, 0.46, 0.17, (0.95, 0.95, 0.93), lift=0.04, r=0.008)
    c.text("12V 65Ah", -0.12, 0.19, 0.06, (0.12, 0.12, 0.15), 0.18)
    c.rect(-0.12, 0.125, 0.36, 0.014, (0.25, 0.25, 0.3), lift=0, alpha=0.5)
    for sg, col in ((-1, (0.85, 0.12, 0.10)), (1, (0.12, 0.12, 0.14))):
        c.rect(sg * 0.26 + 0.07, 0.50, 0.12, 0.05, scale(STEEL, 0.9), lift=0.3, r=0.01)
        c.rect(sg * 0.26 + 0.07, 0.47, 0.10, 0.07, col, lift=0.3, r=0.015)
        c.circle(sg * 0.26 + 0.07, 0.535, 0.03, scale(STEEL, 1.0), lift=0.3)
    c.line(-0.16, 0.40, 0.16, 0.40, 0.04, (0.06, 0.06, 0.08))
    gloss(c, -0.30, 0.30, 0.16, 0.012, 0, 0.5)


@sprop("ty_shelf", aspect=0.95, fill=1.0)
def ty_shelf(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.14)
    frame = (0.22, 0.23, 0.26)
    for sg in (-1, 1):
        c.rect(sg * 0.44, 0.50, 0.04, 1.0, frame, lift=0.3)
    for v in (0.05, 0.38, 0.70, 0.99):
        c.rect(0.0, v, 0.92, 0.035, scale(frame, 1.5), lift=0.3)
        c.rect(0.0, v + 0.015, 0.90, 0.006, WHITE, lift=0, alpha=0.3)
    cols = (P.accent2, (0.9, 0.2, 0.15), (0.95, 0.8, 0.12), (0.15, 0.45, 0.8), (0.95, 0.95, 0.95))
    for k in range(5):                                                    # oil cans / polish bottles on the bottom shelves
        u = -0.34 + k * 0.17
        h = 0.20 + (k % 2) * 0.05
        hshade_box(c, u, 0.07 + h / 2, 0.11, h, scale(cols[k], 1.1), scale(cols[k], 0.55), r=0.012)
        c.rect(u, 0.07 + h + 0.02, 0.05, 0.04, (0.1, 0.1, 0.12), lift=0.2)
        c.rect(u, 0.07 + h * 0.5, 0.10, 0.07, WHITE, lift=0, alpha=0.8)
    for k in range(4):                                                    # floor mats rolled up, wiper blades, covers
        c.rect(-0.30 + k * 0.20, 0.55, 0.15, 0.30, scale((0.18, 0.18, 0.2), 0.9 + k * 0.1), r=0.06, lift=0.3)
        c.ellipse(-0.30 + k * 0.20, 0.70, 0.075, 0.03, (0.26, 0.26, 0.3), lift=0.2)
    c.line(-0.30, 0.78, 0.30, 0.78, 0.014, (0.1, 0.1, 0.12))
    c.line(-0.30, 0.74, 0.30, 0.74, 0.014, (0.1, 0.1, 0.12))
    for k in range(5):                                                    # steering-wheel covers hanging
        c.circle(-0.30 + k * 0.15, 0.87, 0.06, (0.15, 0.15, 0.17) if k % 2 else P.accent_dark, lift=0.25)
        c.circle(-0.30 + k * 0.15, 0.87, 0.028, (0.05, 0.05, 0.06), lift=0)
    soft_disc(c, 0.4, 0.5, 0.12, 0.5, BLACK, 0.2, 1.4)


@niche("tyres", "Tyre and auto accessories", subjects=("ty_stack",),
       strong=("tyre shop", "tire shop", "tyre dealer", "tyre dealers", "wheel alignment", "wheel balancing", "car accessories", "puncture repair", "battery shop",
               "tyre showroom", "alloy wheels", "tyre fitting", "टायर", "टायर की दुकान", "पंक्चर", "व्हील अलाइनमेंट", "tyre puncture"),
       weak=("tyre", "tire", "wheel", "alloy", "battery", "puncture", "accessories", "rim"),
       accent="#424242", mood="dark", group="trades", avoid=("car wash", "showroom"))
def tyres(S):
    P = S.pal
    rng = S.rng
    conc_t, conc_b = mix((0.34, 0.35, 0.37), P.floor_top, 0.2), mix((0.16, 0.16, 0.18), P.floor_bot, 0.2)
    if P.mood in ("light", "warm"):
        conc_t, conc_b = (0.62, 0.62, 0.64), (0.40, 0.40, 0.43)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # racks of stacked tyres along the back wall
        for r_ in range(3):
            for k in range(14):
                S.ellipse(-0.6 + k * 0.20, 0.17 + r_ * 0.14, 0.085, 0.055, (0.06, 0.06, 0.07), lift=0.0)
                S.ellipse(-0.6 + k * 0.20, 0.17 + r_ * 0.14, 0.04, 0.025, (0.16, 0.17, 0.2), lift=0.0)
            S.rect(1.0, 0.235 + r_ * 0.14, 14.0, 0.014, (0.55, 0.12, 0.10), lift=0.0)
        for k in range(10):
            S.rect(-0.5 + k * 0.55, 0.30, 0.02, 0.60, (0.25, 0.26, 0.3), lift=0.0)
        S.rect(1.0, 0.02, 14.0, 0.05, (0.95, 0.95, 1.0), lift=0.0)
        S.glow(0.5, 0.03, 1.1, (0.8, 0.9, 1.0), 0.45)
        S.glow(1.6, 0.03, 1.1, (0.8, 0.9, 1.0), 0.45)
        S.rect(1.0, 0.585, 14.0, 0.04, (0.9, 0.75, 0.12), lift=0.0)
        S.floor(0.62, conc_t, conc_b)
    S.floor(0.62, scale(conc_t, 1.1), scale(conc_b, 0.6))
    S.rect(1.0, 0.64, 14.0, 0.012, scale(conc_t, 0.6), lift=0.0)
    for _ in range(18):
        S.soft(rng.uniform(0.0, 2.2), rng.uniform(0.8, 1.4), rng.uniform(0.05, 0.14), rng.uniform(0.015, 0.04), BLACK, 0.18, 1.4, rng.uniform(-10, 10))
    S.soft(1.1, 0.84, 1.0, 0.18, (0.85, 0.92, 1.0), 0.30, 1.5, add=True)
    S.put("ty_shelf", 0.62, 0.80, 0.46, color=P)
    S.put("ty_wheel", 1.50, 0.88, 0.40, color=P)
    S.put("ty_stack", 1.08, 0.93, 0.40, color=P, subject=True)
    S.put("ty_battery", 0.80, 0.985, 0.16, color=P)
    S.focus("detail", 1.08, 0.58)
    with S.near():
        S.circle(0.52, 1.10, 0.08, (0.05, 0.05, 0.06), 0.9)
        S.ellipse(1.84, 1.06, 0.10, 0.05, (0.9, 0.75, 0.12), 0.35, 12)


# ====================================================================================================== security systems
def _feed(c, u, v, w, h, kind, rng, tint):
    """One camera picture on a monitor: dark tinted view with simple shapes, a REC dot and a label."""
    c.rect(u, v, w, h, mix((0.05, 0.10, 0.14), tint, 0.28), lift=0.2)
    if kind == 0:                                                          # corridor
        c.poly([(u - w * 0.5, v - h * 0.5), (u + w * 0.5, v - h * 0.5), (u + w * 0.14, v + h * 0.1), (u - w * 0.14, v + h * 0.1)], mix((0.12, 0.2, 0.26), tint, 0.3), lift=0.1)
        c.rect(u, v + h * 0.12, w * 0.20, h * 0.30, (0.62, 0.82, 0.9), lift=0.1)
    elif kind == 1:                                                        # car park
        c.rect(u - w * 0.18, v - h * 0.14, w * 0.34, h * 0.18, (0.34, 0.44, 0.5), lift=0.2, r=0.01)
        c.rect(u + w * 0.22, v - h * 0.10, w * 0.26, h * 0.22, (0.5, 0.52, 0.56), lift=0.2, r=0.01)
        c.rect(u, v + h * 0.38, w, h * 0.12, (0.16, 0.2, 0.24), lift=0)
    elif kind == 2:                                                        # entrance with a person
        c.rect(u, v + h * 0.04, w * 0.42, h * 0.72, (0.20, 0.30, 0.36), lift=0.1)
        c.rect(u + w * 0.12, v - h * 0.02, w * 0.10, h * 0.40, (0.78, 0.84, 0.88), lift=0.2, r=0.01)
        c.circle(u + w * 0.12, v - h * 0.30, w * 0.045, (0.80, 0.84, 0.86), lift=0.2)
    else:                                                                  # lobby
        c.rect(u, v - h * 0.15, w * 0.9, h * 0.30, (0.22, 0.34, 0.42), lift=0.1)
        for k in range(3):
            c.rect(u - w * 0.3 + k * w * 0.3, v + h * 0.1, w * 0.12, h * 0.26, (0.3, 0.4, 0.46), lift=0.1)
    c.circle(u - w * 0.40, v + h * 0.40, h * 0.04, (0.95, 0.15, 0.12), lift=0)
    c.text("CAM %d" % (kind + 1), u + w * 0.28, v + h * 0.40, h * 0.09, (0.8, 0.95, 1.0), 0.14)
    for k in range(5):                                                     # scan lines
        c.rect(u, v - h * 0.4 + k * h * 0.2, w, 0.004, (0.0, 0.0, 0.0), lift=0, alpha=0.15)


@sprop("sc_dome", aspect=2.0, fill=0.50)
def sc_dome(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.24)
    white = (0.93, 0.94, 0.97)
    # mounting base: a white drum with a blue light ring
    c.ellipse(0.0, 0.0, 0.46, 0.46 * TILT, scale(white, 0.6), lift=0)
    hshade_box(c, 0.0, 0.05, 0.92, 0.10, white, scale(white, 0.66))
    disc(c, 0.0, 0.10, 0.46, scale(white, 0.96), TILT, 0.06, rim=True)
    c.rect(0.0, 0.05, 0.90, 0.012, P.accent, lift=0.3, alpha=0.95)
    soft_disc(c, 0.0, 0.052, 0.50, 0.04, P.accent, 0.45, 1.5, add=True)
    for sg in (-1, 1):
        c.circle(sg * 0.30, 0.0, 0.018, (0.5, 0.52, 0.56), lift=0.2)
    gloss(c, -0.28, 0.09, 0.12, 0.015, 0, 0.6)
    # smoked glass dome rising out of the base, with the lens module inside
    r = 0.34
    c.ellipse(0.0, 0.10, r * 1.02, r * 1.02 * TILT, (0.55, 0.57, 0.62), lift=0)
    pts = [(r * math.cos(math.radians(a)), 0.10 + r * 1.0 * math.sin(math.radians(a))) for a in range(0, 181, 10)]
    _qpoly(c, pts, (0.07, 0.09, 0.13), 0.35)
    skirt = [(r * k / 8.0, 0.10 - r * TILT * math.sqrt(max(0.0, 1 - (k / 8.0) ** 2))) for k in range(-8, 9)]
    _qpoly(c, skirt + [(r, 0.10), (-r, 0.10)], (0.07, 0.09, 0.13), 0.2)
    c.circle(-0.01, 0.23, 0.17, (0.02, 0.03, 0.05), lift=0)
    c.circle(-0.01, 0.23, 0.13, (0.10, 0.12, 0.18), lift=0.3)
    c.circle(-0.01, 0.23, 0.085, (0.04, 0.07, 0.14), lift=0.2)
    c.circle(-0.02, 0.24, 0.05, mix(P.accent, (0.1, 0.1, 0.3), 0.35), lift=0.4)
    soft_disc(c, -0.04, 0.26, 0.05, 0.035, WHITE, 0.75, 1.2, add=True)
    for k in range(8):                                                     # infra-red LEDs round the lens
        a = k * 0.785
        c.circle(-0.01 + math.cos(a) * 0.15, 0.23 + math.sin(a) * 0.15, 0.011, (0.55, 0.10, 0.10), lift=0.2)
        c.circle(-0.01 + math.cos(a) * 0.15, 0.23 + math.sin(a) * 0.15, 0.005, (1.0, 0.4, 0.3), lift=0)
    arc(c, 0.0, 0.10, r * 0.94, r * 0.94, 25, 150, 0.018, WHITE, 0.55, 10)
    soft_disc(c, -0.13, 0.32, 0.13, 0.08, WHITE, 0.30, 1.2, 30, add=True)
    arc(c, 0.0, 0.10, r, r * TILT, 180, 360, 0.016, (0.78, 0.80, 0.84), 0.95, 12)


@sprop("sc_bullet", aspect=2.0, fill=0.62)
def sc_bullet(c, P):
    ao(c, 0.1, 0.0, 1.1, 0.2)
    white = (0.93, 0.94, 0.97)
    # base plate and arm
    c.ellipse(0.15, 0.03, 0.30, 0.30 * TILT * 0.9, scale(white, 0.7), lift=0.2)
    c.rect(0.15, 0.04, 0.60, 0.06, scale(white, 0.82), r=0.02, lift=0.2)
    c.rect(0.15, 0.20, 0.075, 0.32, scale(STEEL, 1.0), lift=0.3)
    c.circle(0.15, 0.36, 0.06, scale(STEEL, 0.8), lift=0.3)
    c.path([(0.72, 0.50), (0.9, 0.46), (0.95, 0.30)], 0.035, (0.08, 0.08, 0.10), smooth=True)
    # cylinder body, sun shield, lens end
    hshade_box(c, 0.02, 0.50, 1.40, 0.26, white, scale(white, 0.60), r=0.12)
    c.rect(0.0, 0.64, 1.30, 0.045, scale(white, 0.9), r=0.02, lift=0.25)
    c.rect(-0.04, 0.665, 1.30, 0.012, WHITE, lift=0, alpha=0.7)
    c.ellipse(-0.62, 0.50, 0.075, 0.15, (0.04, 0.05, 0.08), lift=0)
    c.ellipse(-0.63, 0.50, 0.05, 0.11, (0.10, 0.14, 0.24), lift=0.3)
    c.ellipse(-0.63, 0.51, 0.022, 0.05, mix(P.accent, (0.1, 0.1, 0.3), 0.3), lift=0.3)
    for k in range(6):
        a = k * 1.047
        c.circle(-0.63 + math.cos(a) * 0.05, 0.50 + math.sin(a) * 0.115, 0.008, (1.0, 0.45, 0.35), lift=0)
    c.rect(0.55, 0.50, 0.05, 0.25, scale(white, 0.5), lift=0.1)
    c.rect(0.0, 0.40, 1.34, 0.014, P.accent, lift=0.3, alpha=0.9)
    gloss(c, -0.20, 0.58, 0.42, 0.018, 0, 0.7)


@sprop("sc_monitor", aspect=1.7, fill=1.0)
def sc_monitor(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.16)
    c.ellipse(0.0, 0.01, 0.30, 0.07, (0.10, 0.11, 0.14), lift=0.2)
    c.rect(0.0, 0.13, 0.12, 0.26, (0.14, 0.15, 0.18), lift=0.3)
    c.rect(0.0, 0.58, 1.70, 0.84, (0.04, 0.05, 0.07), r=0.035, lift=0.2)
    soft_disc(c, 0.0, 0.58, 0.95, 0.52, P.accent, 0.16, 1.6, add=True)
    tw, th = 0.80, 0.37
    tint = mix(P.accent, (0.2, 0.7, 0.7), 0.3)
    for k in range(4):
        _feed(c, -0.41 + (k % 2) * 0.82, 0.74 - (k // 2) * 0.39, tw, th, k, rng, tint)
    c.rect(0.0, 0.58, 1.64, 0.008, (0.02, 0.03, 0.05), lift=0)
    c.rect(0.0, 0.58, 0.008, 0.78, (0.02, 0.03, 0.05), lift=0)
    soft_disc(c, -0.40, 0.82, 0.6, 0.18, WHITE, 0.10, 1.3, 15, add=True)
    c.circle(0.74, 0.205, 0.011, (0.2, 1.0, 0.4), lift=0)


@sprop("sc_keypad", aspect=0.72, fill=1.0)
def sc_keypad(c, P):
    ao(c, 0.0, 0.0, 0.6, 0.12)
    c.rect(0.0, 0.03, 0.40, 0.05, (0.12, 0.13, 0.16), lift=0.2, r=0.01)
    c.rect(0.0, 0.52, 0.70, 0.96, (0.06, 0.07, 0.09), r=0.06, lift=0.2)
    c.rect(0.0, 0.52, 0.66, 0.92, (0.11, 0.12, 0.15), r=0.05, lift=0.25)
    c.rect(0.0, 0.84, 0.50, 0.16, (0.04, 0.10, 0.08), r=0.02, lift=0.2)
    soft_disc(c, 0.0, 0.84, 0.36, 0.10, (0.3, 1.0, 0.5), 0.35, 1.4, add=True)
    c.text("ARMED", 0.0, 0.85, 0.07, (0.5, 1.0, 0.65), 0.2)
    for r_ in range(4):
        for k in range(3):
            u, v = -0.17 + k * 0.17, 0.62 - r_ * 0.13
            c.rect(u, v, 0.13, 0.095, (0.16, 0.18, 0.22), r=0.02, lift=0.3)
            soft_disc(c, u, v, 0.09, 0.07, P.accent, 0.25, 1.4, add=True)
            c.rect(u, v, 0.035, 0.012, mix(P.accent, WHITE, 0.55), lift=0, alpha=0.9)
    for k, col in enumerate(((0.2, 1.0, 0.4), (1.0, 0.7, 0.2), (1.0, 0.2, 0.2))):
        c.circle(-0.20 + k * 0.07, 0.95, 0.016, col, lift=0)
        soft_disc(c, -0.20 + k * 0.07, 0.95, 0.05, 0.05, col, 0.5, 1.4, add=True)
    c.rect(0.12, 0.95, 0.20, 0.012, P.accent, lift=0.3, alpha=0.9)
    gloss(c, -0.22, 0.70, 0.04, 0.22, 0, 0.18)


@sprop("sc_padlock", aspect=0.80, fill=1.0)
def sc_padlock(c, P):
    ao(c, 0.0, 0.0, 0.55, 0.12)
    sh = [(-0.17, 0.50), (-0.17, 0.70), (-0.10, 0.83), (0.0, 0.87), (0.10, 0.83), (0.17, 0.70), (0.17, 0.50)]
    c.path(sh, 0.075, scale(STEEL, 0.55), smooth=True)
    c.path(sh, 0.05, scale(STEEL, 1.0), smooth=True)
    c.path([(x - 0.014, y + 0.0) for x, y in sh], 0.014, WHITE, alpha=0.7, smooth=True)
    body = BRASS
    hshade_box(c, 0.0, 0.27, 0.58, 0.48, scale(body, 1.18), scale(body, 0.52), r=0.07)
    c.rect(0.0, 0.485, 0.58, 0.04, scale(body, 1.25), lift=0.3, r=0.02)
    c.circle(0.0, 0.31, 0.06, (0.10, 0.08, 0.06), lift=0)
    c.poly([(-0.025, 0.31), (0.025, 0.31), (0.04, 0.15), (-0.04, 0.15)], (0.10, 0.08, 0.06), lift=0)
    for u in (-0.23, 0.23):
        c.circle(u, 0.43, 0.017, scale(body, 0.6), lift=0.3)
        c.circle(u, 0.10, 0.017, scale(body, 0.6), lift=0.3)
    c.rect(0.0, 0.06, 0.50, 0.03, scale(body, 0.62), lift=0.2, r=0.01)
    gloss(c, -0.20, 0.34, 0.03, 0.17, 0, 0.65)
    soft_disc(c, 0.2, 0.25, 0.14, 0.22, BLACK, 0.25, 1.3)


@niche("security", "Security systems", subjects=("sc_dome",),
       strong=("cctv", "cctv camera", "cctv installation", "security systems", "security system", "surveillance", "alarm system", "access control", "burglar alarm",
               "video door phone", "biometric attendance", "सीसीटीवी", "सीसीटीवी कैमरा", "सिक्योरिटी सिस्टम", "सर्विलांस", "cctv wala", "camera lagwana"),
       weak=("camera", "security", "alarm", "monitoring", "dvr", "nvr", "lock", "guard"),
       accent="#1e88e5", mood="dark", group="trades", avoid=("security guard agency",))
def security(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    desk_t, desk_b = ((0.16, 0.18, 0.24), (0.05, 0.06, 0.09)) if dk else ((0.36, 0.39, 0.45), (0.16, 0.18, 0.22))
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # monitor wall: a grid of glowing camera feeds
        S.rect(1.0, 0.27, 5.0, 0.52, (0.03, 0.04, 0.06), lift=0.0)
        for r_ in range(3):
            for k in range(20):
                u, v = -2.0 + k * 0.255, 0.07 + r_ * 0.16
                base = mix((0.10, 0.20, 0.28), P.accent, rng.uniform(0.0, 0.5))
                if (k * 3 + r_ * 7) % 11 == 0:
                    base = (0.55, 0.12, 0.10)
                S.rect(u, v, 0.235, 0.14, scale(base, rng.uniform(0.7, 1.35)), lift=0.1)
                S.glow(u, v, 0.20, base, 0.18)
                S.rect(u, v + 0.04, 0.12, 0.05, scale(base, 1.5), lift=0.0, alpha=0.5)
        S.glow(1.0, 0.25, 1.4, P.accent, 0.20)
        S.bokeh(14, -0.3, 0.45, 2.4, 0.58, [P.accent_light, (0.4, 1.0, 0.6), (1.0, 0.3, 0.3)], 0.006, 0.02, 0.6)
        S.rect(1.0, 0.585, 14.0, 0.03, (0.02, 0.03, 0.04), lift=0.0)
        S.floor(0.60, scale(desk_t, 0.6), scale(desk_b, 0.6))
    # glossy console desk with reflections of the screens
    S.floor(0.64, desk_t, scale(desk_b, 0.6))
    S.rect(1.0, 0.64, 14.0, 0.016, mix(P.accent_light, WHITE, 0.4), lift=0.0, alpha=0.9 if dk else 0.6)
    S.rect(1.0, 0.62, 14.0, 0.04, scale(desk_t, 0.5), lift=0.0)
    S.soft(1.1, 0.66, 1.1, 0.06, P.accent, 0.55, 1.6, add=True)
    for _ in range(30):
        u, v = rng.uniform(-0.2, 2.3), rng.uniform(0.7, 1.4)
        S.line(u, v, u + rng.uniform(0.05, 0.25), v + rng.uniform(-0.008, 0.008), 0.002, WHITE, 0.07)
    S.soft(1.1, 0.90, 0.7, 0.12, P.accent_light if dk else P.light, 0.28, 1.5, add=True)
    S.put("sc_monitor", 0.78, 0.82, 0.44, color=P)
    S.put("sc_keypad", 1.60, 0.84, 0.34, color=P)
    S.put("sc_dome", 1.10, 0.95, 0.30, color=P, subject=True, shadow_w=0.5)
    S.put("sc_bullet", 1.50, 0.985, 0.15, color=P)
    S.put("sc_padlock", 0.70, 0.985, 0.17, color=P)
    S.focus("detail", 1.14, 0.80)
    with S.near():
        S.soft(0.52, 1.08, 0.14, 0.07, P.accent, 0.55, 1.2, add=True)
        S.circle(1.84, 1.10, 0.05, (0.2, 1.0, 0.5), 0.8)


# --- END ---
