"""Auto, photography, wedding / party, travel and logistics niches.

Car repair, car wash, car showroom, photography studio, wedding mandap, party / event, travel agency, logistics.
Props are prefixed ``auto_``. Big shaded shapes use a small scan-line filler (``_poly``) instead of the per pixel
signed distance shapes, so cars and warehouses stay fast.
"""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, gloss, soft_disc
from ..niches import niche
from ..stage import sprop
from ...props.core import _catmull
from ...raster import mix, scale

STEEL = (0.62, 0.65, 0.70)
DARK = (0.10, 0.10, 0.12)


# ====================================================================================== scan-line toolkit
def _blend(px, i, col, a):
    ia = 1.0 - a
    px[i] = px[i] * ia + col[0] * a
    px[i + 1] = px[i + 1] * ia + col[1] * a
    px[i + 2] = px[i + 2] * ia + col[2] * a


def _span(px, w, y, xa, xb, col, al):
    if xb <= 0 or xa >= w or xb <= xa:
        return
    if xa < 0:
        xa = 0.0
    if xb > w:
        xb = float(w)
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


def _scan(cv, pts, top, bot=None, alpha=1.0, a_bot=None):
    """Fill a simple polygon (pixel coordinates) with a vertical colour / alpha gradient and anti-aliased left/right edges."""
    bot = top if bot is None else bot
    a_bot = alpha if a_bot is None else a_bot
    n = len(pts)
    if n < 3:
        return
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
    w, px = cv.w, cv.px
    for y in range(y0, y1 + 1):
        yc = y + 0.5
        xs = sorted([xa + (yc - ya) * s for ya, yb, xa, s in edges if ya <= yc < yb])
        if len(xs) < 2:
            continue
        t = (yc - ymin) / span
        t = 0.0 if t < 0 else 1.0 if t > 1 else t
        col = (top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t, top[2] + (bot[2] - top[2]) * t)
        al = alpha + (a_bot - alpha) * t
        if y == y0 or y == y1:
            cov = (y0 + 1 - ymin) if y == y0 else (ymax - y1)
            al *= max(0.0, min(1.0, cov)) if y0 != y1 else 1.0
        for k in range(0, len(xs) - 1, 2):
            _span(px, w, y, xs[k], xs[k + 1], col, al)


def _poly(c, pts, top, bot=None, alpha=1.0, a_bot=None):
    _scan(c.cv, [(c.X(u), c.Y(v)) for u, v in pts], top, bot, alpha, a_bot)


def _rrpts(u0, v0, u1, v1, r, seg=4):
    r = min(r, (u1 - u0) / 2, (v1 - v0) / 2)
    if r <= 0:
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    pts = []
    for cu, cv_, a0 in ((u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90), (u0 + r, v0 + r, 180), (u1 - r, v0 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cu + r * math.cos(a), cv_ + r * math.sin(a)))
    return pts


def _rr(c, u0, v0, u1, v1, top, bot=None, r=0.0, alpha=1.0, a_bot=None):
    """Rounded rectangle (v0 bottom, v1 top) with a vertical gradient."""
    _poly(c, _rrpts(u0, v0, u1, v1, r), top, bot, alpha, a_bot)


def _oval_pts(u, v, a, b, n, a0=0.0, a1=360.0):
    return [(u + a * math.cos(math.radians(a0 + (a1 - a0) * k / n)), v + b * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _oval(c, u, v, a, b, top, bot=None, alpha=1.0, a_bot=None):
    n = max(14, min(48, int(max(a, b) * c.s * 0.7)))
    _poly(c, _oval_pts(u, v, a, b, n)[:-1], top, bot, alpha, a_bot)


def _hfill(c, u0, v0, u1, v1, fn, strips=None):
    """Flat vertical strips whose colour depends on the position across the width (cylinders, bottles, posts, cloth)."""
    cv = c.cv
    xa, xb = c.X(u0), c.X(u1)
    ya, yb = c.Y(v1), c.Y(v0)
    if xb < xa:
        xa, xb = xb, xa
    n = strips or max(3, min(28, int(xb - xa) // 2))
    for k in range(n):
        t = (k + 0.5) / n
        cv.fill_rect(xa + (xb - xa) * k / n, ya, xa + (xb - xa) * (k + 1) / n + 0.6, yb, fn(t))


def _cyl_fn(left, right, hi=0.28):
    """Colour across a cylinder: lit left, soft highlight, dark right edge."""
    def fn(t):
        base = mix(left, right, min(1.0, t * 1.25) ** 1.2)
        h = max(0.0, 1.0 - abs(t - 0.3) / 0.14)
        base = mix(base, WHITE, hi * h * h)
        if t > 0.92:
            base = scale(base, 0.75)
        return base
    return fn


def _hair(cv, x0, y0, x1, y1, col, al=1.0):
    """Anti-aliased one pixel line (Wu), very cheap even when it is long."""
    dx, dy = x1 - x0, y1 - y0
    n = int(max(abs(dx), abs(dy))) + 1
    if n < 2:
        return
    px, w, h = cv.px, cv.w, cv.h
    steep = abs(dy) > abs(dx)
    for k in range(n):
        t = k / float(n - 1)
        x, y = x0 + dx * t, y0 + dy * t
        if steep:
            xi = int(math.floor(x))
            f = x - xi
            yy = int(y)
            if 0 <= yy < h:
                for xx, a in ((xi, 1 - f), (xi + 1, f)):
                    if 0 <= xx < w:
                        _blend(px, (yy * w + xx) * 3, col, al * a)
        else:
            yi = int(math.floor(y))
            f = y - yi
            xx = int(x)
            if 0 <= xx < w:
                for yy, a in ((yi, 1 - f), (yi + 1, f)):
                    if 0 <= yy < h:
                        _blend(px, (yy * w + xx) * 3, col, al * a)


def _shair(S, u0, v0, u1, v1, col, al=1.0):
    if S.dry:
        return
    if S._layer is S.main:
        S._ensure_mid()
    (xa, ya), (xb, yb) = S.px(u0, v0), S.px(u1, v1)
    _hair(S.cv, xa, ya, xb, yb, col, al)


# stage level (outside props)
def _spoly(S, pts, top, bot=None, alpha=1.0, a_bot=None):
    if S.dry:
        return
    if S._layer is S.main:
        S._ensure_mid()
    _scan(S.cv, [S.px(u, v) for u, v in pts], top, bot, alpha, a_bot)


def _sfill(S, u0, v0, u1, v1, color, alpha=1.0):
    """Flat axis-aligned rectangle given by corners (fast)."""
    if S.dry:
        return
    if S._layer is S.main:
        S._ensure_mid()
    (xa, ya), (xb, yb) = S.px(u0, v0), S.px(u1, v1)
    S.cv.fill_rect(min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb), color, alpha)


# ====================================================================================== cars
# kind -> outline (clockwise from the rear bumper), glass panes, wheel centres/radius, belt line height, height of the roof
CARS = {
    "sedan": dict(
        prof=[(-1.43, 0.20), (-1.46, 0.34), (-1.44, 0.52), (-1.36, 0.60), (-1.10, 0.65), (-0.88, 0.67), (-0.62, 0.84), (-0.34, 0.945),
              (0.16, 0.95), (0.50, 0.85), (0.68, 0.68), (1.0, 0.63), (1.30, 0.55), (1.44, 0.44), (1.46, 0.30), (1.42, 0.20),
              (0.9, 0.17), (-0.9, 0.17)],
        glass=[[(-0.80, 0.70), (-0.58, 0.855), (-0.36, 0.91), (-0.10, 0.91), (-0.06, 0.70)],
               [(0.0, 0.70), (0.0, 0.91), (0.15, 0.91), (0.44, 0.82), (0.58, 0.70)]],
        wheels=[(-0.88, 0.215), (0.92, 0.215)], belt=0.67, roof=0.95, door=[-0.93, -0.03, 0.62], head=(1.40, 0.50), tail=(-1.42, 0.54),
        mirror=(0.56, 0.74), sill=0.17),
    "coupe": dict(
        prof=[(-1.50, 0.21), (-1.53, 0.34), (-1.50, 0.50), (-1.32, 0.585), (-1.0, 0.66), (-0.72, 0.775), (-0.36, 0.855), (-0.06, 0.88),
              (0.28, 0.855), (0.62, 0.70), (1.0, 0.60), (1.36, 0.50), (1.53, 0.39), (1.54, 0.28), (1.49, 0.20),
              (0.96, 0.16), (-0.96, 0.16)],
        glass=[[(-0.86, 0.685), (-0.50, 0.81), (-0.20, 0.855), (0.12, 0.855), (0.30, 0.82), (0.50, 0.69)]],
        wheels=[(-0.95, 0.235), (0.99, 0.235)], belt=0.665, roof=0.88, door=[-0.52, 0.53], head=(1.47, 0.45), tail=(-1.50, 0.52),
        mirror=(0.47, 0.71), sill=0.16),
    "suv": dict(
        prof=[(-1.38, 0.23), (-1.42, 0.40), (-1.41, 0.68), (-1.37, 0.92), (-1.24, 1.01), (0.38, 1.03), (0.60, 0.94), (0.93, 0.73),
              (1.30, 0.63), (1.43, 0.49), (1.44, 0.32), (1.39, 0.23), (0.9, 0.20), (-0.9, 0.20)],
        glass=[[(-1.26, 0.745), (-1.29, 0.93), (-1.17, 0.975), (-0.62, 0.975), (-0.62, 0.745)],
               [(-0.54, 0.745), (-0.54, 0.975), (-0.05, 0.975), (-0.05, 0.745)],
               [(0.03, 0.745), (0.03, 0.975), (0.36, 0.975), (0.54, 0.905), (0.78, 0.745)]],
        wheels=[(-0.90, 0.245), (0.93, 0.245)], belt=0.74, roof=1.03, door=[-0.58, -0.01], head=(1.40, 0.52), tail=(-1.40, 0.64),
        mirror=(0.58, 0.80), sill=0.20),
}
CAR_LEN = {"sedan": 2.95, "coupe": 3.1, "suv": 2.9}


def _topv(poly, u):
    """Height of the upper outline of a polygon at position u."""
    best = None
    n = len(poly)
    for i in range(n):
        (ua, va), (ub, vb) = poly[i], poly[(i + 1) % n]
        if ua == ub or not (min(ua, ub) <= u <= max(ua, ub)):
            continue
        v = va + (vb - va) * (u - ua) / (ub - ua)
        if best is None or v > best:
            best = v
    return best


def _follow(c, poly, u0, u1, off, th, color, alpha, vmax=9.0, n=12):
    """A thin lens shaped reflection band that follows the upper outline of the body between u0 and u1."""
    top, bot = [], []
    for k in range(n + 1):
        t = k / float(n)
        u = u0 + (u1 - u0) * t
        tv = _topv(poly, u)
        if tv is None:
            continue
        v = min(tv - off, vmax)
        tp = math.sin(math.pi * t) ** 0.7
        top.append((u, v + th * tp))
        bot.append((u, v - th * 0.6 * tp))
    if len(top) > 2:
        _poly(c, top + bot[::-1], color, None, alpha)


def _smooth(pts, n=4):
    return _catmull(pts, n, True)[:-1]


def _hstrips(c, u0, u1, lo_fn, hi_fn, col_fn, n=None):
    """Vertical strips with their own bottom / top (tapered cylinders, buckets, cups) and a colour across the width."""
    cv = c.cv
    n = n or max(4, min(30, int(abs(c.X(u1) - c.X(u0))) // 2))
    for k in range(n):
        t = (k + 0.5) / n
        xa, xb = c.X(u0 + (u1 - u0) * k / n), c.X(u0 + (u1 - u0) * (k + 1) / n) + 0.6
        cv.fill_rect(min(xa, xb), c.Y(hi_fn(t)), max(xa, xb), c.Y(lo_fn(t)), col_fn(t))


def _wheel(c, u, v, r, rim=STEEL, caliper=None, spokes=5, angle=0.0):
    c.ellipse(u, v, r, r, (0.05, 0.05, 0.06), lift=0.05)
    c.ellipse(u - r * 0.02, v + r * 0.03, r * 0.90, r * 0.90, (0.10, 0.10, 0.11), lift=0.0)
    c.ellipse(u, v, r * 0.66, r * 0.66, scale(rim, 0.62), lift=0.0)
    c.ellipse(u - r * 0.01, v + r * 0.02, r * 0.62, r * 0.62, mix(rim, WHITE, 0.15), lift=0.30)
    c.ellipse(u, v, r * 0.46, r * 0.46, (0.08, 0.08, 0.09), lift=0.0, alpha=0.9)
    if caliper is not None:
        craft.arc(c, u, v, r * 0.52, r * 0.52, 20, 80, r * 0.15, caliper, 0.95, steps=5)
    for k in range(spokes):
        a = math.radians(angle + 360.0 * k / spokes + 90)
        c.line(u + math.cos(a) * r * 0.08, v + math.sin(a) * r * 0.08, u + math.cos(a) * r * 0.60, v + math.sin(a) * r * 0.60, r * 0.13, mix(rim, WHITE, 0.25))
    c.ellipse(u, v, r * 0.13, r * 0.13, mix(rim, WHITE, 0.4), lift=0.2)
    craft.gloss(c, u - r * 0.2, v + r * 0.28, r * 0.25, r * 0.12, 20, 0.35)


def _car(c, kind, body, lift=0.0, glass_tint=(0.10, 0.14, 0.20), sky=(0.55, 0.70, 0.85), caliper=None, sheen=1.0, reflect=False):
    """Side view car, facing right, wheels on v = lift. Unit space: length ~2.9, height ~0.95 (+ lift)."""
    k = CARS[kind]
    rng = c.rng
    sill = k["sill"] + lift
    prof = [(u, v + lift) for u, v in k["prof"]]
    poly = _smooth(prof, 4)
    hi, lo = mix(body, WHITE, 0.20), scale(body, 0.40)
    wr = k["wheels"][0][1]
    if reflect:                                                          # mirrored copy on a glossy floor
        flip = [(u, -v + 2 * lift) for u, v in poly]
        _poly(c, flip, scale(body, 0.8), scale(body, 0.5), 0.34, 0.0)
        for wu, wrr in k["wheels"]:
            _poly(c, _oval_pts(wu, -wrr + lift, wrr, wrr, 14), (0.05, 0.05, 0.06), None, 0.30, 0.0)
        for pane in k["glass"]:
            _poly(c, [(u, -v + 2 * lift) for u, v in pane], (0.5, 0.6, 0.75), None, 0.14, 0.0)
        return
    for wu, wrr in k["wheels"]:                                          # contact shadows under the tyres
        soft_disc(c, wu + 0.04, lift, wrr * 1.6, wrr * 0.28, BLACK, 0.7, 1.4)
    _poly(c, poly, hi, lo)
    # long reflections that follow the body: shoulder, hood, roof, lower crease
    b = k["belt"] + lift
    ulo, uhi = min(p[0] for p in prof), max(p[0] for p in prof)
    _follow(c, poly, ulo + 0.12, uhi - 0.12, 0.075, 0.035, WHITE, 0.26 * sheen, vmax=b - 0.03)
    _follow(c, poly, uhi - 0.75, uhi - 0.10, 0.045, 0.03, mix(body, WHITE, 0.55), 0.30 * sheen)
    _follow(c, poly, ulo + 0.10, ulo + 0.75, 0.045, 0.025, mix(body, WHITE, 0.5), 0.25 * sheen)
    _poly(c, [(ulo + 0.05, sill), (uhi - 0.05, sill), (uhi - 0.08, sill + 0.115), (ulo + 0.08, sill + 0.115)], scale(body, 0.28), scale(body, 0.40), 0.55, 0.30)
    _follow(c, [(ulo, sill + 0.19), (uhi, sill + 0.19), (uhi, 0.0), (ulo, 0.0)], ulo + 0.3, uhi - 0.3, 0.0, 0.022, mix(body, sky, 0.5), 0.22 * sheen)
    # wheel arches
    for wu, wrr in k["wheels"]:
        ar = wrr + 0.045
        pts = [(wu + ar * math.cos(math.radians(a)), wrr + lift + ar * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        _poly(c, [(wu - ar, sill - 0.02)] + pts + [(wu + ar, sill - 0.02)], (0.04, 0.04, 0.05))
    # glass
    for pane in k["glass"]:
        pp = [(u, v + lift) for u, v in pane]
        _poly(c, pp, mix(glass_tint, sky, 0.35), scale(glass_tint, 0.65))
        gu0 = min(p[0] for p in pp)
        gu1 = max(p[0] for p in pp)
        gv0 = min(p[1] for p in pp)
        gv1 = max(p[1] for p in pp)
        m = (gu0 + gu1) / 2
        w_ = (gu1 - gu0) * 0.18
        _poly(c, [(m - w_ * 0.2, gv0), (m + w_ * 1.1, gv0), (m + w_ * 1.9, gv1), (m + w_ * 0.6, gv1)], WHITE, None, 0.13, 0.05)
    # door cuts, handles, mirror, lamps
    for du in k["door"]:
        c.line(du, sill + 0.06, du + 0.01, b - 0.01, 0.007, scale(body, 0.30), 0.75)
        c.line(du + 0.012, sill + 0.06, du + 0.022, b - 0.01, 0.003, mix(body, WHITE, 0.5), 0.45)
    for du in k["door"][1:]:
        _rr(c, du - 0.20, b - 0.075, du - 0.07, b - 0.052, mix(body, WHITE, 0.45), scale(body, 0.65), 0.012)
    mu, mv = k["mirror"]
    _rr(c, mu, mv + lift - 0.035, mu + 0.12, mv + lift + 0.04, scale(body, 0.8), scale(body, 0.5), 0.03)
    hu, hv = k["head"]
    c.glow(hu, hv + lift, 0.22, (1.0, 0.96, 0.82), 0.40)
    _poly(c, [(hu - 0.17, hv + lift - 0.035), (hu + 0.04, hv + lift - 0.06), (hu + 0.03, hv + lift + 0.03), (hu - 0.14, hv + lift + 0.045)], (1.0, 0.98, 0.88), (0.80, 0.82, 0.86))
    tu, tv = k["tail"]
    _poly(c, [(tu + 0.03, tv + lift - 0.06), (tu - 0.01, tv + lift - 0.05), (tu - 0.01, tv + lift + 0.05), (tu + 0.16, tv + lift + 0.035)], (0.95, 0.12, 0.12), (0.55, 0.05, 0.06))
    c.glow(tu, tv + lift, 0.12, (1.0, 0.1, 0.1), 0.25)
    # bright rim light along the roof and hood outline
    prev = None
    for kk in range(40):
        u = ulo + 0.02 + (uhi - ulo - 0.04) * kk / 39.0
        v = _topv(poly, u)
        if v is not None and prev is not None and v > sill + 0.3:
            c.line(prev[0], prev[1] - 0.004, u, v - 0.004, 0.006, WHITE, 0.42 * sheen)
        prev = (u, v) if v is not None else None
    # bumper lines and a glint
    c.line(uhi - 0.12, sill + 0.14, uhi - 0.02, sill + 0.19, 0.012, scale(body, 0.35), 0.5)
    for wu, wrr in k["wheels"]:
        _wheel(c, wu, wrr + lift, wrr, caliper=caliper)
    soft_disc(c, ulo + (uhi - ulo) * 0.62, b + 0.02, 0.30, 0.025, WHITE, 0.30 * sheen, 1.1, 4, True)
    soft_disc(c, ulo + (uhi - ulo) * 0.30, b + 0.20 + lift * 0.0, 0.16, 0.03, WHITE, 0.18 * sheen, 1.1, 20, True)


@sprop("auto_car_sedan", aspect=3.1, fill=1.0)
def auto_car_sedan(c, color):
    _car(c, "sedan", color or (0.85, 0.86, 0.88))


# ====================================================================================== car repair
@sprop("auto_lift_car", aspect=2.06, fill=1.70)
def auto_lift_car(c, color):
    """A car raised on a two-post lift: posts with a top beam, lifting arms under the sills."""
    rng = c.rng
    acc = color or (0.9, 0.5, 0.15)
    lift = 0.52
    # floor contact of posts and base plates
    for pu in (-1.62, 1.62):
        ao(c, pu, 0.0, 0.5, 0.10, 0.5)
        _rr(c, pu - 0.20, 0.0, pu + 0.20, 0.045, scale(acc, 0.75), scale(acc, 0.35), 0.01)
    # car (in front of the far side details, behind near arms)
    _car(c, "sedan", (0.17, 0.33, 0.62), lift=lift, caliper=(0.9, 0.5, 0.1))
    # under body details seen through the gap: a dark underside strip and a dripping fluid pan
    _rr(c, -1.25, lift + 0.12, 1.25, lift + 0.185, (0.06, 0.06, 0.07), (0.10, 0.10, 0.11), 0.02, 0.8)
    # posts
    for pu in (-1.62, 1.62):
        _hfill(c, pu - 0.115, 0.04, pu + 0.115, 1.62, _cyl_fn(mix(acc, WHITE, 0.25), scale(acc, 0.50), 0.18))
        _rr(c, pu - 0.135, 1.61, pu + 0.135, 1.68, mix(acc, WHITE, 0.15), scale(acc, 0.55), 0.015)
        for k in range(8):                                       # hydraulic / carriage detail
            c.line(pu - 0.09, 0.2 + k * 0.17, pu + 0.09, 0.2 + k * 0.17, 0.006, scale(acc, 0.45), 0.5)
        _rr(c, pu - 0.14, lift - 0.02, pu + 0.14, lift + 0.12, scale(acc, 0.75), scale(acc, 0.35), 0.015)       # carriage
        c.rect(pu - 0.03, lift + 0.05, 0.03, 0.045, (0.12, 0.12, 0.14), lift=0)
    # top beam (clear floor lift)
    _rr(c, -1.64, 1.53, 1.64, 1.61, scale(acc, 1.0), scale(acc, 0.50), 0.02)
    c.line(-1.6, 1.595, 1.6, 1.595, 0.01, mix(acc, WHITE, 0.45), 0.6)
    # lifting arms with rubber pads
    for pu, du in ((-1.62, 1.0), (1.62, -1.0)):
        x0, x1 = (pu + 0.10 * du, pu + 0.62 * du)
        _rr(c, min(x0, x1), lift + 0.02, max(x0, x1), lift + 0.10, (0.25, 0.26, 0.29), (0.12, 0.12, 0.14), 0.02)
        pad = pu + 0.62 * du
        _rr(c, pad - 0.06, lift + 0.10, pad + 0.06, lift + 0.17, (0.12, 0.12, 0.12), (0.05, 0.05, 0.05), 0.02)
        c.line(min(x0, x1), lift + 0.095, max(x0, x1), lift + 0.095, 0.006, mix(STEEL, WHITE, 0.3), 0.7)
    # a drip pan with oil drips under the engine
    _rr(c, 0.55, 0.0, 1.20, 0.05, (0.35, 0.37, 0.4), (0.15, 0.15, 0.17), 0.015)
    c.ellipse(0.88, 0.048, 0.28, 0.02, (0.05, 0.04, 0.02), lift=0.1)
    gloss(c, 0.80, 0.052, 0.12, 0.008, 0, 0.5)
    for k in range(3):
        c.line(0.88 + k * 0.01, lift + 0.12 - k * 0.07, 0.88 + k * 0.01, lift + 0.07 - k * 0.07, 0.012, (0.07, 0.05, 0.02), 0.9)
    c.ellipse(0.88, 0.16, 0.014, 0.02, (0.10, 0.07, 0.03), lift=0.4)


@sprop("auto_pegboard", aspect=1.25, fill=1.0)
def auto_pegboard(c, color):
    """Wall pegboard with a row of hanging wrenches, pliers, a hammer and screwdrivers."""
    rng = c.rng
    acc = color or (0.9, 0.5, 0.15)
    w = 1.25
    _rr(c, -w / 2, 0.0, w / 2, 1.0, (0.50, 0.38, 0.28), (0.38, 0.28, 0.20), 0.02)
    _rr(c, -w / 2 + 0.02, 0.02, w / 2 - 0.02, 0.98, (0.58, 0.45, 0.33), (0.45, 0.34, 0.25), 0.02, 0.65)
    for gu in range(12):
        for gv in range(10):
            c.cv.fill_rect(c.X(-0.58 + gu * 0.105) - 0.7, c.Y(0.06 + gv * 0.095) - 0.7, c.X(-0.58 + gu * 0.105) + 0.7, c.Y(0.06 + gv * 0.095) + 0.7,
                           (0.22, 0.16, 0.12), 0.8)
    soft_disc(c, -0.25, 0.8, 0.7, 0.35, WHITE, 0.12, 1.2, 0, True)
    # wrenches, longest left
    for k in range(7):
        u = -0.52 + k * 0.095
        ln = 0.72 - k * 0.055
        top = 0.92
        col = mix(STEEL, WHITE, 0.12 * (k % 2))
        c.line(u + 0.014, top - 0.005, u + 0.014, top - ln, 0.034, BLACK, 0.30)                       # cast shadow on the board
        c.line(u, top, u, top - ln, 0.030, col)
        c.line(u - 0.008, top - 0.01, u - 0.008, top - ln + 0.02, 0.008, mix(col, WHITE, 0.6), 0.8)
        c.ellipse(u, top, 0.048, 0.044, col, lift=0.2)
        c.ellipse(u, top + 0.012, 0.022, 0.026, (0.40, 0.30, 0.22), lift=0)
        c.ellipse(u, top - ln, 0.040, 0.037, col, lift=0.2)
        c.ellipse(u, top - ln - 0.012, 0.016, 0.02, (0.40, 0.30, 0.22), lift=0)
    # pliers
    px_ = 0.20
    for sgn in (-1, 1):
        c.line(px_, 0.50, px_ + sgn * 0.045, 0.74, 0.026, acc if sgn < 0 else scale(acc, 0.8))
        c.line(px_, 0.50, px_ + sgn * 0.02, 0.28, 0.034, STEEL)
    c.ellipse(px_, 0.50, 0.02, 0.02, (0.2, 0.2, 0.22), lift=0.3)
    # hammer
    hu = 0.40
    c.line(hu + 0.012, 0.18, hu + 0.012, 0.80, 0.036, BLACK, 0.30)
    c.line(hu, 0.2, hu, 0.78, 0.028, (0.70, 0.50, 0.28))
    _rr(c, hu - 0.085, 0.76, hu + 0.085, 0.86, (0.72, 0.74, 0.78), (0.32, 0.33, 0.36), 0.02)
    # screwdrivers with accent handles
    for k in range(3):
        su = 0.54 + k * 0.07
        ln = 0.52 - k * 0.04
        c.line(su, 0.78, su, 0.78 - ln, 0.009, STEEL)
        _rr(c, su - 0.020, 0.78, su + 0.020, 0.92, acc, scale(acc, 0.55), 0.015)
    # a shelf under with a few cans
    _rr(c, -0.60, -0.0, 0.60, 0.035, (0.30, 0.24, 0.20), (0.18, 0.14, 0.12), 0.01)


@sprop("auto_toolchest", aspect=0.95, fill=1.0)
def auto_toolchest(c, color):
    """Roller cabinet with drawers and chrome handles, tools on the lid."""
    rng = c.rng
    acc = color or (0.8, 0.2, 0.12)
    ao(c, 0.0, 0.0, 0.9, 0.12, 0.4)
    w = 0.88
    _hfill(c, -w / 2, 0.10, w / 2, 0.80, _cyl_fn(mix(acc, WHITE, 0.14), scale(acc, 0.55), 0.0), strips=14)
    _rr(c, -w / 2 - 0.02, 0.77, w / 2 + 0.02, 0.84, mix(acc, WHITE, 0.2), scale(acc, 0.6), 0.015)           # lid
    for k in range(5):
        v0 = 0.14 + k * 0.125
        _rr(c, -w / 2 + 0.03, v0, w / 2 - 0.03, v0 + 0.11, mix(acc, WHITE, 0.10), scale(acc, 0.62), 0.012)
        c.line(-0.30, v0 + 0.085, 0.30, v0 + 0.085, 0.012, mix(STEEL, WHITE, 0.4))
        c.line(-0.30, v0 + 0.073, 0.30, v0 + 0.073, 0.005, (0.15, 0.15, 0.17), 0.7)
        c.line(-w / 2 + 0.04, v0 + 0.105, w / 2 - 0.04, v0 + 0.105, 0.004, WHITE, 0.25)
    for su in (-0.32, 0.32):                                     # casters
        c.ellipse(su, 0.045, 0.045, 0.045, (0.08, 0.08, 0.09), lift=0.1)
        c.line(su, 0.09, su, 0.12, 0.02, (0.4, 0.4, 0.42))
    # tools on the lid: a small toolbox, a spanner
    _rr(c, -0.30, 0.84, -0.04, 0.95, (0.85, 0.75, 0.2), (0.55, 0.45, 0.1), 0.02)
    c.line(-0.24, 0.95, -0.10, 0.95, 0.018, (0.2, 0.2, 0.22))
    c.line(0.08, 0.86, 0.34, 0.875, 0.02, STEEL)
    c.ellipse(0.35, 0.877, 0.03, 0.03, STEEL, lift=0.2)
    craft.gloss(c, -0.2, 0.60, 0.20, 0.09, 8, 0.25)


@sprop("auto_worklight", aspect=0.55, fill=1.0)
def auto_worklight(c, color):
    """Hanging cage work light: cord, hook, glowing bulb inside a wire guard."""
    c.line(0.0, 1.0, 0.0, 0.68, 0.014, (0.08, 0.08, 0.09))
    _rr(c, -0.07, 0.62, 0.07, 0.70, (0.9, 0.7, 0.1), (0.5, 0.35, 0.05), 0.02)
    c.glow(0.0, 0.34, 1.9, (1.0, 0.82, 0.45), 0.55)
    c.glow(0.0, 0.34, 0.8, (1.0, 0.92, 0.7), 0.7)
    c.ellipse(0.0, 0.40, 0.17, 0.2, (1.0, 0.95, 0.75), lift=0.0, alpha=0.9)
    c.ellipse(0.0, 0.40, 0.09, 0.12, WHITE, lift=0.0)
    for k in range(-3, 4):
        a = k * 0.095
        c.line(a * 0.45, 0.62, a * 1.5, 0.22, 0.009, (0.14, 0.14, 0.15), 0.9)
    for vv in (0.28, 0.40, 0.52):
        c.line(-0.2 + abs(vv - 0.40) * 0.2, vv, 0.2 - abs(vv - 0.40) * 0.2, vv, 0.008, (0.14, 0.14, 0.15), 0.9)


@sprop("auto_tire_stack", aspect=0.95, fill=0.62)
def auto_tire_stack(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.2, 0.5)
    for k in range(3):
        v = 0.07 + k * 0.17
        r = 0.44
        c.ellipse(0.0, v - 0.05, r, r * TILT, (0.04, 0.04, 0.05), lift=0)
        _rr(c, -r, v - 0.05, r, v + 0.09, (0.12, 0.12, 0.13), (0.04, 0.04, 0.05), 0.04)
        c.ellipse(0.0, v + 0.09, r, r * TILT, (0.10, 0.10, 0.11), lift=0.1)
        c.ellipse(0.0, v + 0.095, r * 0.60, r * 0.60 * TILT, STEEL if k == 2 else (0.05, 0.05, 0.06), lift=0.2)
        c.ellipse(0.0, v + 0.10, r * 0.46, r * 0.46 * TILT, (0.03, 0.03, 0.04), lift=0.0)
        for j in range(14):
            a = rng.uniform(0, 2 * math.pi)
            c.line(math.cos(a) * r * 0.97, v + 0.02 + math.sin(a) * r * TILT * 0.4, math.cos(a) * r * 0.97, v + 0.07, 0.01, (0.20, 0.20, 0.22), 0.5)
    gloss(c, -0.22, 0.52, 0.15, 0.03, 6, 0.28)


def _lamp_tube(S, u, v, w, color=(1.0, 0.96, 0.85), power=0.55):
    S.glow(u, v, w * 0.9, color, power * 0.7)
    S.rect(u, v, w, 0.012, mix(color, WHITE, 0.5), lift=0.0)


@niche("car-repair", "Car repair garage", subjects=("auto_lift_car",),
       strong=("car repair", "mechanic", "garage", "car service", "auto repair", "car workshop", "auto garage", "car mechanic",
               "gaadi repair", "bike garage", "गैराज", "मैकेनिक", "कार रिपेयर", "वर्कशॉप", "गाड़ी रिपेयर"),
       weak=("workshop", "car", "auto", "tyre", "engine", "oil change", "repair", "spare parts", "denting painting", "puncture"), accent="#e67e22", mood="dark",
       group="auto", avoid=("showroom", "dealer", "dealership", "car wash", "detailing"))
def car_repair(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for k in range(-6, 14):                                                      # concrete block joints
            S.rect(-1.0 + k * 0.42, 0.20, 0.004, 0.62, scale(P.wall_bot, 0.78), lift=0.0, alpha=0.5)
        S.rect(1.0, 0.31, 6.0, 0.004, scale(P.wall_bot, 0.76), lift=0.0, alpha=0.5)
        S.rect(1.0, 0.50, 6.0, 0.004, scale(P.wall_bot, 0.76), lift=0.0, alpha=0.5)
        # roller shutter on the left, a window with daylight on the right
        S.rect(0.25, 0.28, 0.55, 0.50, scale(P.wall_bot, 1.1 if not dk else 1.5), lift=0.05)
        for k in range(14):
            S.rect(0.25, 0.04 + k * 0.034, 0.55, 0.005, scale(P.wall_bot, 0.55), lift=0.0, alpha=0.8)
        S.glow(0.25, 0.60, 0.6, mix(P.light, (1.0, 0.8, 0.5), 0.5), 0.25)
        S.window(1.95, 0.24, 0.34, 0.22, bars=True)
        # shelving unit with oil cans and boxes
        for sv in (0.30, 0.43, 0.56):
            S.rect(1.60, sv, 0.44, 0.012, (0.20, 0.22, 0.28), lift=0.0)
        S.rect(1.40, 0.43, 0.012, 0.28, (0.20, 0.22, 0.28), lift=0.0)
        S.rect(1.80, 0.43, 0.012, 0.28, (0.20, 0.22, 0.28), lift=0.0)
        for sv in (0.30, 0.43, 0.56):
            uu = 1.42
            while uu < 1.78:
                wd = rng.uniform(0.035, 0.07)
                ht = rng.uniform(0.05, 0.10)
                col = rng.choice([P.accent, (0.85, 0.85, 0.9), (0.2, 0.3, 0.55), (0.75, 0.65, 0.45), P.accent_dark])
                S.rect(uu + wd / 2, sv - ht / 2 - 0.006, wd, ht, col, lift=0.1)
                uu += wd + 0.01
        # hazard band and tube lights
        for k in range(30):
            S.rect(-1.0 + k * 0.16, 0.615, 0.07, 0.02, (0.95, 0.75, 0.1) if k % 2 == 0 else (0.15, 0.15, 0.15), lift=0.0)
        for ul in (0.55, 1.15, 1.75):
            _lamp_tube(S, ul, 0.06, 0.20, (1.0, 0.96, 0.88), 0.85 if dk else 0.6)
        S.bokeh(8, 0.2, 0.1, 1.9, 0.5, [(1.0, 0.8, 0.5), (1.0, 0.95, 0.85)], 0.012, 0.035, 0.25)
        S.floor(0.62, P.floor_top, P.floor_bot)
        S.soft(1.12, 0.84, 1.0, 0.22, mix(P.light, (1.0, 0.85, 0.6), 0.5), 0.55 if dk else 0.3, 1.4, add=True)
        S.soft(1.12, 0.70, 1.5, 0.25, (1.0, 0.92, 0.75), 0.25 if dk else 0.12, 1.2, add=True)
    # concrete floor details (sharp): joints, oil stains, scuffs
    _sfill(S, -3, 0.62, 5, 0.628, (0.0, 0.0, 0.0), 0.28)
    for k in range(-5, 12):
        _shair(S, 0.30 + k * 0.45, 0.63, 0.30 + k * 0.45 - 0.7 + k * 0.11, 1.4, (0.0, 0.0, 0.0), 0.22)
    for vv in (0.74, 0.92, 1.18):
        _shair(S, -2, vv, 4, vv, (0.0, 0.0, 0.0), 0.2)
    for _ in range(9):
        S.soft(rng.uniform(0.3, 1.7), rng.uniform(0.7, 1.1), rng.uniform(0.04, 0.16), rng.uniform(0.012, 0.04), (0.0, 0.0, 0.0), rng.uniform(0.18, 0.35), 1.2)
    S.soft(0.88, 0.89, 0.25, 0.045, (0.02, 0.02, 0.02), 0.55, 1.2)                        # oil puddle under the engine
    S.soft(0.78, 0.885, 0.09, 0.008, (1.0, 0.9, 0.7), 0.30, 1.1, add=True)
    # pegboard on the wall at the left, tool chest below it, lift in the middle
    S.glow(1.12, 0.52, 0.75, mix(P.accent, WHITE, 0.2), 0.20 if dk else 0.10)
    S.put("auto_pegboard", 0.56, 0.60, 0.30, color=P.accent, shadow=False)
    S.put("auto_toolchest", 0.57, 0.90, 0.28, color=mix(P.accent, (0.8, 0.12, 0.1), 0.35), shadow_alpha=0.4)
    S.put("auto_lift_car", 1.14, 0.92, 0.55, color=P.accent, shadow_w=0.9, shadow_alpha=0.45)
    S.mark_subject("auto_lift_car", 0.86, 0.43, 1.42, 0.78)
    S.put("auto_tire_stack", 1.60, 0.98, 0.17, shadow_alpha=0.4, framed=False)
    S.put("auto_worklight", 0.80, 0.44, 0.20, framed=False, shadow=False)
    S.focus("detail", 1.14, 0.62)
    with S.near(blur=16):
                S.soft(1.62, 0.28, 0.35, 0.18, (1.0, 0.85, 0.55), 0.20, 1.2, add=True)


# ====================================================================================== car showroom
@sprop("auto_showroom_car", aspect=3.15, fill=1.12)
def auto_showroom_car(c, color):
    """A sleek coupe on a glossy turntable with an LED ring, reflected in the floor."""
    rng = c.rng
    body = color or (0.75, 0.12, 0.10)
    ring = mix(body, WHITE, 0.25)
    # turntable: dark stepped disc with a glowing accent edge
    _oval(c, 0.0, -0.01, 1.78, 0.34, (0.02, 0.02, 0.03), (0.01, 0.01, 0.015))
    _rr(c, -1.76, -0.01, 1.76, 0.10, (0.10, 0.10, 0.12), (0.03, 0.03, 0.04), 0.0)
    c.ellipse(0.0, 0.10, 1.76, 0.34, (0.05, 0.05, 0.07), lift=0.0)
    c.glow(0.0, 0.0, 2.4, body, 0.16)
    craft.arc(c, 0.0, 0.055, 1.76, 0.34, 190, 350, 0.014, ring, 0.9, steps=26)
    craft.arc(c, 0.0, 0.10, 1.74, 0.335, 190, 350, 0.006, WHITE, 0.55, steps=26)
    c.ellipse(0.0, 0.11, 1.70, 0.325, (0.13, 0.13, 0.16), lift=0.12)
    c.ellipse(0.0, 0.115, 1.50, 0.285, (0.10, 0.10, 0.13), lift=0.05)
    soft_disc(c, 0.0, 0.11, 1.7, 0.28, WHITE, 0.16, 1.1, 0, True)
    # reflection and car
    _car(c, "coupe", body, lift=0.10, reflect=True)
    _car(c, "coupe", body, lift=0.10, caliper=(0.95, 0.85, 0.5), sheen=1.4)


@sprop("auto_rope_posts", aspect=1.7, fill=1.0)
def auto_rope_posts(c, color):
    """Two chrome stanchions with a sagging velvet rope."""
    rope = color or (0.65, 0.08, 0.10)
    for pu in (-0.65, 0.65):
        ao(c, pu, 0.0, 0.34, 0.08, 0.5)
        c.ellipse(pu, 0.025, 0.14, 0.14 * TILT, (0.55, 0.56, 0.60), lift=0.0)
        c.ellipse(pu, 0.04, 0.125, 0.125 * TILT, (0.88, 0.90, 0.94), lift=0.25)
        _hfill(c, pu - 0.028, 0.04, pu + 0.028, 0.92, _cyl_fn((0.92, 0.94, 0.98), (0.30, 0.32, 0.36), 0.5))
        c.ellipse(pu, 0.95, 0.065, 0.065, (0.70, 0.72, 0.76), lift=0.3)
        gloss(c, pu - 0.02, 0.97, 0.03, 0.025, 0, 0.8)
    pts = []
    for k in range(13):
        t = k / 12.0
        pts.append((-0.65 + 1.3 * t, 0.84 - math.sin(math.pi * t) * 0.17))
    for p0, p1 in zip(pts, pts[1:]):
        c.line(p0[0], p0[1] - 0.012, p1[0], p1[1] - 0.012, 0.055, scale(rope, 0.45))
        c.line(p0[0], p0[1], p1[0], p1[1], 0.050, rope)
        c.line(p0[0], p0[1] + 0.012, p1[0], p1[1] + 0.012, 0.016, mix(rope, WHITE, 0.4), 0.8)


@sprop("auto_spot", aspect=0.5, fill=1.0)
def auto_spot(c, color):
    """Ceiling spotlight can with a bright lens."""
    _rr(c, -0.05, 0.9, 0.05, 1.0, (0.2, 0.2, 0.22), (0.08, 0.08, 0.09), 0.01)
    _poly(c, [(-0.07, 0.9), (0.07, 0.9), (0.12, 0.62), (-0.12, 0.62)], (0.25, 0.25, 0.28), (0.07, 0.07, 0.09))
    c.glow(0.0, 0.6, 1.2, (1.0, 0.95, 0.85), 0.6)
    c.ellipse(0.0, 0.62, 0.11, 0.035, WHITE, lift=0)


@niche("car-showroom", "Car showroom", subjects=("auto_showroom_car",),
       strong=("car showroom", "car dealer", "dealership", "new cars", "automobile", "luxury cars", "car dealership",
               "used cars", "gaadi showroom", "कार डीलर", "कार शोरूम", "ऑटोमोबाइल", "गाड़ी का शोरूम"),
       weak=("showroom", "शोरूम", "cars", "car", "vehicle", "auto", "motors", "test drive", "pre owned"), accent="#c0392b", mood="dark", group="auto",
       avoid=("repair", "mechanic", "garage", "car wash", "detailing", "bike", "bikes", "motorcycle", "scooter", "furniture", "sofa", "mobile", "tv", "electronics", "jewellery", "shoe", "saree", "kurti", "tile", "mattress", "kitchen", "बाइक", "फर्नीचर"))
def car_showroom(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    glass_top = (0.06, 0.08, 0.16) if dk else (0.62, 0.80, 0.95)
    glass_bot = (0.16, 0.18, 0.30) if dk else (0.90, 0.95, 1.0)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # tall glass wall with city bokeh behind it
        for k in range(-3, 9):
            S.gradient_rect(-1.2 + k * 0.52 + 0.01, 0.02, -1.2 + k * 0.52 + 0.51, 0.60, glass_top, glass_bot)
        cols = [(1.0, 0.78, 0.45), (1.0, 0.55, 0.30), (0.6, 0.75, 1.0), (1.0, 0.95, 0.8)] if dk else [(1.0, 1.0, 1.0), (0.7, 0.85, 1.0)]
        S.bokeh(26 if dk else 8, -0.4, 0.30, 2.4, 0.57, cols, 0.008, 0.026, 0.55 if dk else 0.25)
        for k in range(-3, 10):
            S.rect(-1.2 + k * 0.52, 0.31, 0.014, 0.60, scale(P.wall_bot, 0.55) if dk else (0.8, 0.82, 0.85), lift=0.0)
        S.rect(1.0, 0.025, 6, 0.05, scale(P.wall_top, 0.8), lift=0.0)
        S.rect(1.0, 0.605, 6, 0.012, mix(P.paper, P.wall_bot, 0.4) if not dk else scale(P.accent, 0.5), lift=0.0)
        # backlit feature wall behind the car: dark panel with glowing accent strips
        S.gradient_rect(0.55, 0.10, 1.68, 0.60, (0.04, 0.03, 0.04) if dk else (0.80, 0.81, 0.84), (0.10, 0.07, 0.08) if dk else (0.93, 0.93, 0.95))
        S.glow(1.1, 0.40, 0.9, P.accent, 0.50 if dk else 0.22)
        for k in range(6):
            S.rect(0.70 + k * 0.18, 0.35, 0.010, 0.46, P.accent_light if dk else P.accent, lift=0.0)
            S.glow(0.70 + k * 0.18, 0.35, 0.10, P.accent, 0.35 if dk else 0.12)
        # a second car and rope in the distance
        S.put("auto_car_sedan", 0.15, 0.62, 0.22, color=scale(P.accent_dark, 0.8), shadow=False, framed=False)
        S.put("auto_car_sedan", 2.1, 0.62, 0.22, color=(0.7, 0.72, 0.78), shadow=False, framed=False)
        for ul in (0.5, 0.9, 1.3, 1.7):
            S.glow(ul, 0.02, 0.45, (1.0, 0.95, 0.85), 0.5 if dk else 0.22)
            S.rect(ul, 0.02, 0.10, 0.01, WHITE, lift=0.0)
        for uc in (0.70, 1.10, 1.50):                                               # light cones from the ceiling spots
            S.light_shaft(uc - 0.02, 0.02, uc + 0.02, 0.02, uc + 0.34, 0.74, uc - 0.34, 0.74, (1.0, 0.95, 0.85), 0.10 if dk else 0.06)
        S.floor(0.62, P.floor_top, P.floor_bot)
        S.soft(1.1, 0.78, 1.2, 0.20, mix(P.light, (1.0, 0.92, 0.85), 0.5), 0.55 if dk else 0.28, 1.3, add=True)
        for uu in (0.5, 1.1, 1.7):                                                   # reflections of the lights on the polished floor
            S.soft(uu, 0.82, 0.05, 0.22, (1.0, 0.95, 0.9), 0.25 if dk else 0.10, 1.2, add=True)
        S.soft(1.1, 0.80, 0.8, 0.20, P.accent, 0.32 if dk else 0.12, 1.3, add=True)
    # polished floor grid
    for k in range(-9, 10):
        _shair(S, 1.1 + k * 0.10, 0.62, 1.1 + k * 0.55, 1.5, (1.0, 1.0, 1.0) if dk else (0.3, 0.3, 0.35), 0.10 if dk else 0.14)
    for vv in (0.66, 0.72, 0.81, 0.95, 1.15):
        _shair(S, -2, vv, 4, vv, (1.0, 1.0, 1.0) if dk else (0.3, 0.3, 0.35), 0.09)
    S.put("auto_showroom_car", 1.10, 0.86, 0.40, color=P.accent, shadow=False)
    S.mark_subject("auto_showroom_car", 0.88, 0.52, 1.32, 0.83)
    S.soft(1.10, 0.88, 0.75, 0.10, (0.0, 0.0, 0.0), 0.40, 1.5)
    S.put("auto_rope_posts", 0.66, 0.99, 0.20, color=P.accent_dark, shadow_alpha=0.3)
    S.put("auto_spot", 0.72, 0.18, 0.12, framed=False, shadow=False)
    S.put("auto_spot", 1.10, 0.12, 0.12, framed=False, shadow=False)
    S.put("auto_spot", 1.48, 0.18, 0.12, framed=False, shadow=False)
    S.focus("detail", 1.10, 0.68)
    with S.near(blur=16):
        S.soft(0.55, 0.30, 0.20, 0.16, (1.0, 0.9, 0.7), 0.20, 1.2, add=True)
        S.soft(1.62, 1.0, 0.25, 0.10, P.accent, 0.25, 1.2, add=True)


# ====================================================================================== car wash
def _car_poly(kind, lift=0.0):
    return _smooth([(u, v + lift) for u, v in CARS[kind]["prof"]], 4)


def _bubble(c, u, v, r):
    c.ellipse(u + 0.004, v - 0.008, r, r * 0.95, (0.66, 0.78, 0.92), lift=0.0, alpha=0.9)
    c.ellipse(u, v, r * 0.96, r * 0.92, (0.97, 0.985, 1.0), lift=0.06)
    c.ellipse(u - r * 0.28, v + r * 0.30, r * 0.30, r * 0.22, WHITE, lift=0.0, alpha=0.95)


@sprop("auto_foam_car", aspect=3.0, fill=1.1)
def auto_foam_car(c, color):
    """An SUV covered in soap foam: heaps of bubbles on the roof and hood, drips down the doors, beads of water."""
    rng = c.rng
    body = color or (0.20, 0.52, 0.85)
    _car(c, "suv", body, glass_tint=(0.12, 0.2, 0.3), sky=(0.7, 0.85, 1.0), sheen=1.2)
    poly = _car_poly("suv")
    ulo, uhi = -1.40, 1.42
    for _ in range(11):                                      # drips and rivulets (under the foam)
        u = rng.uniform(ulo + 0.2, uhi - 0.2)
        tv = _topv(poly, u) or 0.8
        v0 = tv - rng.uniform(0.18, 0.42)
        ln = rng.uniform(0.10, 0.30)
        c.line(u, v0, u + rng.uniform(-0.01, 0.01), max(0.30, v0 - ln), 0.016, (0.96, 0.98, 1.0), 0.80)
        c.ellipse(u, max(0.30, v0 - ln), 0.013, 0.017, (0.97, 0.99, 1.0), lift=0.1, alpha=0.9)
    for i in range(100):                                     # heaps of foam along the top outline, smaller ones sliding down
        u = rng.uniform(ulo + 0.12, uhi - 0.1)
        tv = _topv(poly, u) or 0.8
        depth = rng.random() ** 1.7 * 0.42
        v = tv - depth + rng.uniform(-0.01, 0.03)
        if v < 0.45:
            continue
        r = rng.uniform(0.04, 0.10) * (1.0 - depth * 0.85)
        _bubble(c, u, v, r)
        if i % 3 == 0:
            c.ellipse(u + r * 0.30, v - r * 0.30, r * 0.20, r * 0.16, (0.80, 0.92, 1.0), lift=0.0, alpha=0.6)
    for _ in range(26):                                      # beads of clean water on the lower body
        u = rng.uniform(ulo + 0.25, uhi - 0.25)
        v = rng.uniform(0.28, 0.58)
        r = rng.uniform(0.008, 0.016)
        c.ellipse(u, v, r, r * 1.1, mix(body, WHITE, 0.45), lift=0.2, alpha=0.9)
        c.ellipse(u - r * 0.3, v + r * 0.35, r * 0.35, r * 0.3, WHITE, lift=0.0)


@sprop("auto_bucket", aspect=0.95, fill=0.85)
def auto_bucket(c, color):
    """Bucket brimming with suds and a yellow sponge."""
    rng = c.rng
    col = color or (0.20, 0.52, 0.85)
    ao(c, 0.0, 0.0, 0.62, 0.12, 0.45)
    c.ellipse(0.0, 0.03, 0.27, 0.27 * TILT, scale(col, 0.4), lift=0.0)
    _hstrips(c, -0.29, 0.29, lambda t: 0.03, lambda t: 0.60, _cyl_fn(mix(col, WHITE, 0.2), scale(col, 0.45), 0.35), n=22)
    c.ellipse(0.0, 0.03, 0.28, 0.28 * TILT * 0.85, scale(col, 0.40), lift=0.0, alpha=0.0)
    c.ellipse(0.0, 0.60, 0.32, 0.32 * TILT, mix(col, WHITE, 0.35), lift=0.1)
    c.ellipse(0.0, 0.595, 0.29, 0.29 * TILT, scale(col, 0.55), lift=0.0)
    c.line(-0.29, 0.52, 0.29, 0.52, 0.012, scale(col, 0.45), 0.5)
    craft.arc(c, 0.0, 0.62, 0.31, 0.55, 20, 160, 0.018, (0.7, 0.72, 0.76), 0.95, steps=10)
    for i in range(34):                                      # suds
        a = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(rng.random()) * 0.26
        _bubble(c, math.cos(a) * rr, 0.63 + math.sin(a) * rr * TILT + rng.uniform(0.0, 0.10) * (1 - rr / 0.26), rng.uniform(0.035, 0.075))
    _rr(c, 0.04, 0.72, 0.26, 0.82, (1.0, 0.86, 0.22), (0.85, 0.62, 0.08), 0.03)               # sponge
    for _ in range(14):
        c.ellipse(rng.uniform(0.06, 0.24), rng.uniform(0.735, 0.81), 0.008, 0.006, (0.7, 0.5, 0.05), lift=0, alpha=0.7)
    _rr(c, 0.04, 0.82, 0.26, 0.85, (0.20, 0.72, 0.45), (0.12, 0.5, 0.3), 0.012)
    gloss(c, -0.12, 0.40, 0.05, 0.16, 90, 0.4)


@sprop("auto_spray_gun", aspect=2.6, fill=0.9)
def auto_spray_gun(c, color):
    """Pressure washer gun at the right with a fan of water streaming to the left."""
    rng = c.rng
    acc = color or (0.2, 0.52, 0.85)
    nu, nv = -0.55, 0.62
    _poly(c, [(nu, nv), (nu - 1.10, nv + 0.62), (nu - 1.30, nv + 0.20)], (1.0, 1.0, 1.0), (0.80, 0.92, 1.0), 0.42, 0.06)
    _poly(c, [(nu, nv), (nu - 1.00, nv + 0.50), (nu - 1.12, nv + 0.30)], (1.0, 1.0, 1.0), None, 0.35, 0.10)
    for _ in range(38):                                      # droplets of the spray
        t = rng.uniform(0.05, 1.0)
        ang = math.radians(rng.uniform(18, 38))
        d = t * 1.25
        u = nu - math.cos(ang) * d
        v = nv + math.sin(ang) * d - t * t * 0.05
        r = rng.uniform(0.010, 0.022) * (1.0 + t * 0.4)
        c.ellipse(u, v, r * 1.3, r, (0.95, 0.98, 1.0), lift=0.1, alpha=rng.uniform(0.6, 0.98))
    for _ in range(12):
        t = rng.uniform(0.05, 0.9)
        ang = math.radians(rng.uniform(20, 36))
        u0, v0 = nu - math.cos(ang) * t * 1.25, nv + math.sin(ang) * t * 1.25
        c.line(u0, v0, u0 - 0.10, v0 - 0.06, 0.009, WHITE, 0.8)
    _hstrips(c, -0.54, 0.20, lambda t: 0.595, lambda t: 0.635, lambda t: mix((0.95, 0.96, 0.98), (0.3, 0.32, 0.36), t), n=10)
    _rr(c, -0.60, 0.585, -0.52, 0.645, (0.8, 0.82, 0.85), (0.3, 0.3, 0.33), 0.01)
    _rr(c, 0.15, 0.50, 0.60, 0.72, mix(acc, WHITE, 0.2), scale(acc, 0.55), 0.06)
    _rr(c, 0.22, 0.40, 0.34, 0.54, (0.12, 0.12, 0.14), (0.05, 0.05, 0.06), 0.02)
    c.line(0.10, 0.56, 0.38, 0.40, 0.03, (0.10, 0.10, 0.12))
    gloss(c, 0.32, 0.67, 0.12, 0.03, 0, 0.5)
    for k in range(10):                                      # hose
        t = k / 9.0
        c.line(0.60 + t * 0.45, 0.60 - t * 0.5 + math.sin(t * 6) * 0.03, 0.60 + (t + 0.11) * 0.45, 0.60 - (t + 0.11) * 0.5, 0.075, (0.10, 0.11, 0.14))
    c.line(0.60, 0.62, 1.2, 0.2, 0.01, (0.4, 0.42, 0.48), 0.5)


def _tile_wall(S, u0, u1, v0, v1, c1, size=0.09):
    rng = S.rng
    nu, nv = int((u1 - u0) / size), int((v1 - v0) / size)
    _sfill(S, u0, v0, u1, v1, scale(c1, 0.90))
    for i in range(nu):
        for j in range(nv):
            _sfill(S, u0 + i * size + 0.003, v0 + j * size + 0.003, u0 + (i + 1) * size - 0.003, v0 + (j + 1) * size - 0.003, scale(c1, 1.0 + rng.uniform(-0.03, 0.02)))


@niche("car-wash", "Car wash", subjects=("auto_foam_car",),
       strong=("car wash", "car detailing", "carwash", "foam wash", "auto detailing", "car cleaning", "vehicle wash", "car spa",
               "gaadi dhulai", "कार वॉश", "कार धुलाई", "कार डिटेलिंग", "गाड़ी धुलाई", "गाड़ी की धुलाई", "car after detailing"),
       weak=("detailing", "wash", "foam", "polish", "ceramic coating", "bike wash", "धुलाई", "चमकाने", "sparkling clean", "glossy car"), accent="#3498db", mood="light", group="auto",
       avoid=("repair", "mechanic", "garage", "showroom", "dealer"))
def car_wash(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        tile_a = mix(P.wall_top, WHITE, 0.35 if not dk else 0.0)
        _tile_wall(S, -3.0, 5.0, 0.0, 0.62, tile_a, 0.10)
        S.rect(1.0, 0.28, 6.0, 0.06, P.accent, lift=0.0)                                       # brand stripe
        S.rect(1.0, 0.34, 6.0, 0.012, mix(P.accent, WHITE, 0.5), lift=0.0)
        if dk:                                                                                  # neon feel in the dark variant
            for ug in (0.3, 0.8, 1.3, 1.8):
                S.glow(ug, 0.30, 0.45, P.accent, 0.55)
        S.gradient_rect(0.15, 0.04, 0.85, 0.50, (0.55, 0.78, 0.97) if not dk else (0.08, 0.1, 0.2), (0.95, 0.98, 1.0) if not dk else (0.25, 0.28, 0.4))
        S.rect(0.50, 0.505, 0.78, 0.016, mix(P.paper, scale(P.wall_bot, 0.8), 0.5), lift=0.0)
        S.glow(0.5, 0.3, 0.7, (1.0, 0.98, 0.9), 0.35 if not dk else 0.4)
        S.circle(1.95, 0.30, 0.10, P.accent, lift=0.15)                                        # hose reel and shelf with bottles
        S.circle(1.95, 0.30, 0.065, mix(P.accent, WHITE, 0.5), lift=0.1)
        S.circle(1.95, 0.30, 0.025, scale(P.accent_dark, 0.7), lift=0.0)
        for k in range(5):
            S.rect(1.40 + k * 0.05, 0.32, 0.028, 0.10 + (k % 2) * 0.03, [P.accent, WHITE, P.accent2, (0.95, 0.85, 0.3), P.accent][k], lift=0.1)
        S.rect(1.50, 0.385, 0.38, 0.01, scale(P.wall_bot, 0.55), lift=0.0)
        for ul in (0.5, 1.1, 1.7):
            S.glow(ul, 0.04, 0.5, (1.0, 0.98, 0.92), 0.8 if dk else 0.35)
            S.rect(ul, 0.04, 0.16, 0.014, WHITE, lift=0.0)
        S.bokeh(10, 0.1, 0.1, 2.0, 0.55, [(1.0, 1.0, 1.0), (0.75, 0.9, 1.0)], 0.01, 0.03, 0.30 if not dk else 0.35)
        S.floor(0.62, mix(P.floor_top, (0.74, 0.79, 0.84), 0.75), mix(P.floor_bot, (0.50, 0.55, 0.62), 0.75))
        S.rect(1.0, 0.68, 6.0, 0.035, scale(mix(P.floor_top, (0.5, 0.55, 0.6), 0.7), 0.60), lift=0.0)           # drain channel
        for ul in (0.5, 1.1, 1.7):
            S.soft(ul, 0.80, 0.07, 0.20, (1.0, 1.0, 1.0), 0.28 if not dk else 0.3, 1.2, add=True)
        S.soft(1.15, 0.76, 1.0, 0.2, (1.0, 1.0, 1.0), 0.45 if not dk else 0.5, 1.3, add=True)
        S.soft(1.1, 0.80, 0.9, 0.14, P.accent, 0.20, 1.3, add=True)
    for k in range(-5, 12):                                                                   # wet concrete: joints and puddles
        _shair(S, 0.2 + k * 0.4, 0.64, 0.2 + k * 0.4 - 0.8 + k * 0.13, 1.4, (0.0, 0.0, 0.0), 0.10)
    for vv in (0.76, 0.96, 1.2):
        _shair(S, -2, vv, 4, vv, (0.0, 0.0, 0.0), 0.10)
    for u, v, a, b in ((0.72, 0.92, 0.22, 0.045), (1.45, 0.95, 0.30, 0.05), (1.05, 1.02, 0.4, 0.055), (1.7, 1.06, 0.2, 0.035)):
        S.soft(u, v, a, b, (0.35, 0.50, 0.65), 0.45, 1.2)
        S.soft(u - a * 0.2, v - b * 0.2, a * 0.7, b * 0.5, (0.95, 0.98, 1.0), 0.5, 1.1, add=True)
    S.put("auto_foam_car", 1.08, 0.88, 0.42, color=P.accent, shadow_w=0.95, shadow_alpha=0.34)
    S.mark_subject("auto_foam_car", 0.85, 0.50, 1.31, 0.84)
    S.put("auto_bucket", 0.74, 1.0, 0.20, color=P.accent, shadow_alpha=0.3)
    S.put("auto_spray_gun", 1.62, 1.0, 0.27, color=P.accent2, shadow=False)
    S.focus("detail", 1.0, 0.56)
    for _ in range(16):                                                                      # floating soap bubbles
        u, v, r = rng.uniform(0.5, 1.7), rng.uniform(0.3, 0.95), rng.uniform(0.008, 0.024)
        S.circle(u, v, r, (0.85, 0.95, 1.0), alpha=0.22, lift=0.0)
        S.soft(u - r * 0.35, v - r * 0.35, r * 0.4, r * 0.3, WHITE, 0.9, 1.0, add=True)
        S.soft(u + r * 0.3, v + r * 0.3, r * 0.5, r * 0.5, (0.9, 0.7, 1.0), 0.25, 1.0, add=True)
    with S.near(blur=18):
        for _ in range(9):
            u, v = rng.uniform(0.5, 1.7), rng.uniform(0.2, 1.0)
            r = rng.uniform(0.02, 0.06)
            S.soft(u, v, r, r, (0.85, 0.95, 1.0), 0.28, 1.0, add=True)


# ====================================================================================== photography studio
def _glass(c, u, v, r, tint, hi=0.8):
    """A coated lens glass element: dark tinted gradient disc with soft reflections."""
    c.ellipse(u, v, r, r, scale(tint, 0.25), lift=0.0)
    c.ellipse(u, v + r * 0.04, r * 0.92, r * 0.92, mix(tint, (0.05, 0.05, 0.10), 0.35), lift=0.35)
    c.ellipse(u, v, r * 0.62, r * 0.62, scale(tint, 0.45), lift=0.25, alpha=0.9)
    c.ellipse(u, v, r * 0.30, r * 0.30, (0.02, 0.02, 0.05), lift=0.0)
    soft_disc(c, u - r * 0.35, v + r * 0.35, r * 0.5, r * 0.28, WHITE, 0.55 * hi, 1.1, 35, True)
    soft_disc(c, u + r * 0.35, v - r * 0.38, r * 0.34, r * 0.18, mix(tint, WHITE, 0.4), 0.5 * hi, 1.1, 35, True)
    c.ellipse(u - r * 0.46, v + r * 0.52, r * 0.07, r * 0.05, WHITE, lift=0.0)


@sprop("auto_camera_tripod", aspect=0.98, fill=1.0)
def auto_camera_tripod(c, color):
    """A DSLR seen from the front on a tripod: ribbed lens with coloured glass, prism, grip, dials, ball head, three legs."""
    rng = c.rng
    acc = color or (0.56, 0.27, 0.68)
    # tripod: back leg, hub and the two front legs with ribs and rubber feet
    ao(c, 0.0, 0.0, 1.05, 0.14, 0.5)
    c.line(0.03, 0.40, 0.05, 0.04, 0.026, (0.10, 0.10, 0.12))
    for sgn in (-1, 1):
        x1 = sgn * 0.44
        c.line(0.0, 0.40, x1 + 0.012, 0.025, 0.040, BLACK, 0.25)
        c.line(0.0, 0.40, x1, 0.03, 0.034, (0.17, 0.18, 0.21))
        c.line(-0.004 * sgn, 0.40, x1 - 0.008 * sgn, 0.03, 0.010, (0.55, 0.58, 0.64), 0.7)
        for t in (0.35, 0.62):
            c.ellipse(x1 * t, 0.40 - 0.37 * t, 0.026, 0.026, (0.08, 0.08, 0.09), lift=0.3)
        c.ellipse(x1, 0.022, 0.032, 0.022, (0.05, 0.05, 0.05), lift=0.1)
    _hfill(c, -0.016, 0.38, 0.016, 0.62, _cyl_fn((0.80, 0.83, 0.88), (0.28, 0.30, 0.35), 0.5))
    c.ellipse(0.0, 0.42, 0.055, 0.04, (0.12, 0.12, 0.14), lift=0.3)
    c.ellipse(0.0, 0.40, 0.034, 0.026, (0.5, 0.52, 0.58), lift=0.4)
    # ball head, quick release plate, pan handle
    c.ellipse(0.0, 0.625, 0.045, 0.040, (0.10, 0.10, 0.12), lift=0.4)
    gloss(c, -0.015, 0.64, 0.015, 0.012, 0, 0.7)
    c.line(0.04, 0.60, 0.18, 0.50, 0.016, (0.08, 0.08, 0.1))
    c.ellipse(0.19, 0.495, 0.025, 0.025, (0.9, 0.5, 0.1), lift=0.3)
    _rr(c, -0.17, 0.642, 0.17, 0.668, (0.55, 0.57, 0.62), (0.18, 0.19, 0.22), 0.01)
    # camera body: leatherette with a lit top edge
    _rr(c, -0.37, 0.668, 0.37, 0.935, (0.22, 0.22, 0.25), (0.06, 0.06, 0.08), 0.045)
    for _ in range(70):
        u, v = rng.uniform(-0.35, 0.35), rng.uniform(0.68, 0.92)
        c.ellipse(u, v, 0.003, 0.002, (0.03, 0.03, 0.04) if rng.random() < 0.6 else (0.34, 0.34, 0.38), lift=0, alpha=0.6)
    _rr(c, -0.35, 0.917, 0.35, 0.930, (0.55, 0.56, 0.62), (0.20, 0.21, 0.24), 0.01, 0.8)
    _rr(c, 0.18, 0.69, 0.35, 0.92, (0.16, 0.16, 0.18), (0.04, 0.04, 0.05), 0.04)                                   # grip
    _rr(c, -0.35, 0.69, -0.20, 0.92, (0.19, 0.19, 0.21), (0.05, 0.05, 0.06), 0.03)
    c.line(0.185, 0.70, 0.185, 0.91, 0.005, (0.5, 0.5, 0.55), 0.35)
    # pentaprism, hot shoe, popup flash window, dials
    _poly(c, [(-0.17, 0.935), (-0.11, 1.0), (0.11, 1.0), (0.17, 0.935)], (0.26, 0.26, 0.29), (0.10, 0.10, 0.12))
    c.line(-0.11, 0.995, 0.11, 0.995, 0.006, (0.65, 0.66, 0.72), 0.6)
    _rr(c, -0.06, 0.995, 0.06, 1.015, (0.45, 0.46, 0.5), (0.16, 0.16, 0.18), 0.005)
    c.ellipse(-0.26, 0.945, 0.055, 0.016, (0.40, 0.41, 0.46), lift=0.25)
    for k in range(10):
        c.line(-0.30 + k * 0.011, 0.934, -0.30 + k * 0.011, 0.952, 0.003, (0.1, 0.1, 0.12), 0.6)
    c.ellipse(0.25, 0.945, 0.032, 0.012, (0.86, 0.14, 0.12), lift=0.3)                                          # shutter button
    c.ellipse(0.0, 0.855, 0.016, 0.012, (0.8, 0.8, 0.84), lift=0.2)
    _rr(c, -0.31, 0.85, -0.22, 0.885, scale(acc, 0.9), scale(acc, 0.45), 0.01)                                  # brand tab in the accent colour
    # lens: barrel rings, focus ring with ribs, glass
    lv = 0.775
    c.ellipse(0.0, lv, 0.215, 0.215, (0.03, 0.03, 0.04), lift=0.0)
    c.ellipse(0.0, lv + 0.005, 0.205, 0.205, (0.20, 0.20, 0.23), lift=0.35)
    c.ellipse(0.0, lv, 0.18, 0.18, (0.06, 0.06, 0.07), lift=0.0)
    for k in range(40):
        a = math.radians(k * 9)
        c.line(math.cos(a) * 0.150, lv + math.sin(a) * 0.150, math.cos(a) * 0.178, lv + math.sin(a) * 0.178, 0.006, (0.28, 0.28, 0.32), 0.9)
    c.ellipse(0.0, lv, 0.145, 0.145, (0.12, 0.12, 0.14), lift=0.3)
    craft.arc(c, 0.0, lv, 0.125, 0.125, 30, 150, 0.006, (0.9, 0.2, 0.15), 0.95, steps=8)
    _glass(c, 0.0, lv, 0.115, mix(acc, (0.2, 0.3, 0.7), 0.4))
    soft_disc(c, -0.08, 0.86, 0.22, 0.10, WHITE, 0.14, 1.2, 30, True)
    gloss(c, -0.30, 0.87, 0.05, 0.012, 0, 0.5)


@sprop("auto_softbox", aspect=0.80, fill=1.0)
def auto_softbox(c, color):
    """Studio softbox on a light stand: glowing diffuser panel in a black frame, boom and tripod base."""
    rng = c.rng
    acc = color or (0.56, 0.27, 0.68)
    ao(c, 0.0, 0.0, 0.7, 0.10, 0.5)
    c.glow(0.0, 0.72, 2.0, (1.0, 0.95, 0.9), 0.22)
    # stand: three splayed legs, a column with a collar
    for sgn in (-1, 1):
        c.line(0.0, 0.14, sgn * 0.33, 0.02, 0.022, (0.10, 0.10, 0.12))
        c.ellipse(sgn * 0.33, 0.016, 0.022, 0.014, (0.05, 0.05, 0.05), lift=0.1)
    c.line(0.02, 0.14, 0.05, 0.03, 0.016, (0.08, 0.08, 0.09))
    _hfill(c, -0.016, 0.13, 0.016, 0.48, _cyl_fn((0.80, 0.83, 0.88), (0.25, 0.27, 0.32), 0.5))
    _rr(c, -0.03, 0.30, 0.03, 0.34, (0.12, 0.12, 0.14), (0.04, 0.04, 0.05), 0.01)
    c.ellipse(0.0, 0.14, 0.05, 0.03, (0.1, 0.1, 0.12), lift=0.3)
    # bracket and the box (side depth first)
    c.line(0.0, 0.48, 0.0, 0.56, 0.03, (0.1, 0.1, 0.12))
    _rr(c, -0.50, 0.53, 0.30, 0.95, (0.16, 0.16, 0.19), (0.05, 0.05, 0.06), 0.04)                            # the deep box behind the panel
    for k in range(5):
        c.line(-0.47 + k * 0.016, 0.57, -0.47 + k * 0.016, 0.91, 0.004, (0.3, 0.3, 0.34), 0.35)
    _rr(c, -0.42, 0.50, 0.42, 1.00, (0.10, 0.10, 0.12), (0.03, 0.03, 0.04), 0.03)                                # frame
    _rr(c, -0.385, 0.535, 0.385, 0.965, (1.0, 0.99, 0.95), (0.93, 0.92, 0.9), 0.015)                              # diffuser
    soft_disc(c, 0.0, 0.75, 0.40, 0.25, (1.0, 1.0, 1.0), 0.65, 0.8, 0, True)
    soft_disc(c, -0.10, 0.88, 0.25, 0.08, acc, 0.10, 1.0, 0, True)
    for k in (-1, 1):                                                                                           # internal rods seen through the fabric
        c.line(k * 0.19, 0.545, k * 0.19, 0.955, 0.004, (0.78, 0.76, 0.74), 0.4)
    c.line(-0.38, 0.75, 0.38, 0.75, 0.004, (0.78, 0.76, 0.74), 0.35)
    c.line(-0.41, 0.99, 0.41, 0.99, 0.005, (0.55, 0.56, 0.6), 0.6)
    c.ellipse(0.0, 0.50, 0.07, 0.03, (0.22, 0.22, 0.25), lift=0.3)


@sprop("auto_reflector", aspect=0.78, fill=1.0)
def auto_reflector(c, color):
    """Round 5-in-1 reflector on a stand: gold and silver halves inside a fabric ring."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.6, 0.10, 0.5)
    for sgn in (-1, 1):
        c.line(0.0, 0.12, sgn * 0.28, 0.015, 0.02, (0.10, 0.10, 0.12))
    c.line(0.02, 0.12, 0.04, 0.03, 0.015, (0.08, 0.08, 0.09))
    _hfill(c, -0.014, 0.10, 0.014, 0.52, _cyl_fn((0.80, 0.83, 0.88), (0.25, 0.27, 0.32), 0.5))
    c.line(0.0, 0.50, 0.0, 0.60, 0.025, (0.1, 0.1, 0.12))
    # the disc: dark fabric ring, gold half and silver half with soft sheen
    cx, cy, rr = 0.0, 0.76, 0.36
    c.ellipse(cx, cy, rr, rr * 0.97, (0.06, 0.06, 0.07), lift=0.0)
    c.ellipse(cx, cy, rr * 0.94, rr * 0.91, (0.95, 0.74, 0.28), lift=0.25)
    _poly(c, [(cx - rr * 0.94, cy), (cx + rr * 0.94, cy), (cx + rr * 0.86, cy - rr * 0.38), (cx + rr * 0.55, cy - rr * 0.78), (cx, cy - rr * 0.91),
              (cx - rr * 0.55, cy - rr * 0.78), (cx - rr * 0.86, cy - rr * 0.38)], (0.92, 0.94, 0.98), (0.62, 0.65, 0.72))
    soft_disc(c, -0.1, 0.9, 0.25, 0.13, WHITE, 0.55, 1.1, 20, True)
    soft_disc(c, 0.12, 0.62, 0.20, 0.10, (1.0, 0.95, 0.8), 0.3, 1.1, 0, True)
    craft.arc(c, cx, cy, rr * 0.99, rr * 0.96, 120, 200, 0.012, (0.4, 0.4, 0.45), 0.7, steps=8)
    _rr(c, 0.05, 0.50, 0.14, 0.56, (0.2, 0.2, 0.22), (0.07, 0.07, 0.08), 0.01)


@sprop("auto_lens", aspect=1.60, fill=0.75)
def auto_lens(c, color):
    """A telephoto lens lying on an apple box: ribbed focus ring, hood, glowing front element."""
    rng = c.rng
    acc = color or (0.56, 0.27, 0.68)
    ao(c, 0.0, 0.0, 1.5, 0.22, 0.5)
    _rr(c, -0.78, 0.0, 0.78, 0.30, (0.74, 0.56, 0.33), (0.46, 0.33, 0.18), 0.015)
    for _ in range(10):
        v = rng.uniform(0.02, 0.28)
        c.line(rng.uniform(-0.7, 0.2), v, rng.uniform(0.2, 0.7), v + rng.uniform(-0.005, 0.005), 0.003, (0.4, 0.28, 0.16), 0.5)
    _rr(c, -0.70, 0.07, 0.70, 0.23, (0.5, 0.37, 0.2), (0.4, 0.28, 0.15), 0.03, 0.5)
    _rr(c, -0.80, 0.29, 0.80, 0.33, (0.88, 0.70, 0.46), (0.66, 0.50, 0.28), 0.01)
    c = c.sub(0.0, 0.10, 1.0)
    # barrel (side view), shaded top to bottom in bands
    def band(u0, u1, v0, v1, base, rings=0):
        n = 7
        for i in range(n):
            t0, t1 = i / float(n), (i + 1) / float(n)
            k = 1.28 - 0.95 * ((t0 + t1) / 2) ** 0.8
            _rr(c, u0, v0 + (v1 - v0) * t0, u1, v0 + (v1 - v0) * t1 + 0.002, scale(base, k), scale(base, k - 0.1), 0.0)
        for j in range(rings):
            uu = u0 + (u1 - u0) * (j + 0.5) / rings
            c.line(uu, v0 + 0.01, uu, v1 - 0.01, 0.006, (0.04, 0.04, 0.05), 0.8)
    band(-0.62, -0.46, 0.34, 0.60, (0.35, 0.36, 0.40))                 # mount side
    band(-0.50, 0.12, 0.28, 0.66, (0.30, 0.31, 0.35))
    band(0.12, 0.38, 0.28, 0.66, (0.15, 0.15, 0.17), rings=14)            # focus ring
    _rr(c, -0.20, 0.51, -0.04, 0.54, scale(acc, 0.9), scale(acc, 0.5), 0.005)
    c.line(-0.45, 0.58, 0.1, 0.58, 0.004, (0.85, 0.85, 0.9), 0.4)
    band(0.38, 0.52, 0.24, 0.70, (0.22, 0.23, 0.26))
    _poly(c, [(0.52, 0.24), (0.52, 0.70), (0.62, 0.78), (0.62, 0.16)], (0.18, 0.18, 0.20), (0.05, 0.05, 0.06))       # hood
    c.ellipse(0.62, 0.47, 0.075, 0.31, (0.03, 0.03, 0.04), lift=0.1)
    c.ellipse(0.62, 0.47, 0.05, 0.24, mix(acc, (0.1, 0.2, 0.5), 0.5), lift=0.3)
    soft_disc(c, 0.615, 0.56, 0.03, 0.15, WHITE, 0.55, 1.1, 0, True)
    gloss(c, -0.2, 0.62, 0.30, 0.025, 0, 0.5)


def _cables(S, rng, pts, col):
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        S.line(u0, v0, u1, v1, 0.011, BLACK, 0.35)
        S.line(u0, v0 - 0.003, u1, v1 - 0.003, 0.008, col)


@niche("photography", "Photography studio", subjects=("auto_camera_tripod",),
       strong=("photography", "photographer", "photo studio", "photoshoot", "camera", "wedding photographer", "photo shoot", "portrait studio",
               "studio photography", "videography", "फोटोग्राफी", "फोटोग्राफर", "फोटो स्टूडियो", "photographer ki studio"),
       weak=("photo", "lens", "portrait", "pre wedding", "album", "shoot", "candid", "video shoot"), accent="#8e44ad", mood="dark", group="events")
def photography(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    paper_hi = mix(P.accent, WHITE, 0.15 if dk else 0.5)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.66)
        S.rect(1.0, 0.33, 6.0, 0.70, scale(P.wall_bot, 0.75), lift=0.0, alpha=0.5)
        # ceiling rail with small studio lamps and bokeh
        for ul in (0.2, 0.7, 1.2, 1.7, 2.2):
            S.rect(ul, 0.02, 0.05, 0.03, (0.14, 0.14, 0.16), lift=0.0)
            S.glow(ul, 0.06, 0.18, (1.0, 0.95, 0.85), 0.4 if dk else 0.15)
        S.bokeh(7, 0.1, 0.08, 2.0, 0.4, [P.accent_light, (1.0, 0.95, 0.85)], 0.01, 0.03, 0.25)
        # seamless backdrop paper: crossbar, two stands, roll and a long sweep into the floor
        S.gradient_rect(0.46, 0.11, 1.78, 0.74, scale(paper_hi, 0.45 if dk else 0.85), scale(paper_hi, 0.95), r=0.0)
        S.glow(1.12, 0.42, 0.75, mix(paper_hi, WHITE, 0.2), 0.45 if dk else 0.25)
        S.rect(1.12, 0.105, 1.40, 0.03, (0.08, 0.08, 0.1) if dk else (0.3, 0.3, 0.34), lift=0.1)
        S.rect(1.12, 0.12, 1.34, 0.045, mix(paper_hi, WHITE, 0.3), r=0.02, lift=0.1)
        for pu in (0.40, 1.84):
            S.rect(pu, 0.42, 0.016, 0.68, (0.08, 0.08, 0.1) if dk else (0.3, 0.3, 0.34), lift=0.0)
        S.floor(0.70, P.floor_top, P.floor_bot)
        S.gradient_rect(0.46, 0.66, 1.78, 0.76, scale(paper_hi, 0.95), scale(paper_hi, 0.85))
        S.soft(1.12, 0.78, 1.1, 0.14, paper_hi, 0.55 if dk else 0.30, 1.3, add=True)
        S.soft(0.64, 0.86, 0.5, 0.2, (1.0, 0.96, 0.9), 0.30 if dk else 0.18, 1.4, add=True)
    # floor sheen and cables
    S.soft(1.12, 0.92, 0.95, 0.12, paper_hi, 0.20 if dk else 0.10, 1.3, add=True)
    for vv in (0.80, 0.98, 1.2):
        _shair(S, -2, vv, 4, vv, (1.0, 1.0, 1.0) if dk else (0.2, 0.2, 0.25), 0.07)
    _cables(S, rng, [(0.64, 0.95), (0.75, 1.0), (0.95, 1.02), (1.15, 0.99), (1.3, 0.985)], (0.07, 0.07, 0.09))
    S.rect(0.9, 1.04, 0.06, 0.012, (0.9, 0.85, 0.2), lift=0.0, alpha=0.8)
    S.glow(0.64, 0.58, 0.55, (1.0, 0.96, 0.9), 0.30 if dk else 0.15)
    S.soft(0.72, 0.93, 0.60, 0.07, (1.0, 0.96, 0.9), 0.28 if dk else 0.12, 1.3, add=True)
    S.put("auto_softbox", 0.62, 0.92, 0.50, color=P.accent, shadow_alpha=0.45)
    S.put("auto_camera_tripod", 1.12, 0.97, 0.52, color=P.accent, subject=True, shadow_alpha=0.45)
    S.put("auto_reflector", 1.56, 0.94, 0.40, shadow_alpha=0.4)
    S.put("auto_lens", 1.40, 1.05, 0.16, color=P.accent, shadow_alpha=0.4)
    S.focus("detail", 1.12, 0.64)
    with S.near(blur=16):
        S.soft(0.45, 0.30, 0.20, 0.30, (1.0, 0.95, 0.85), 0.20, 1.2, add=True)
        S.soft(1.75, 1.02, 0.25, 0.10, P.accent, 0.30, 1.2, add=True)


# ====================================================================================== wedding mandap
MARI = ((0.98, 0.52, 0.05), (1.0, 0.66, 0.08), (0.95, 0.40, 0.04), (1.0, 0.78, 0.18))
ROSE = ((0.80, 0.08, 0.16), (0.70, 0.05, 0.14), (0.88, 0.20, 0.28))
GOLD = (0.88, 0.68, 0.22)
CRIMSON = (0.62, 0.07, 0.10)


def _bead(c, u, v, r, rng, rose=False):
    if rose:
        col = ROSE[rng.randrange(3)]
        c.ellipse(u, v, r, r, scale(col, 0.7), lift=0.0)
        c.ellipse(u - r * 0.05, v + r * 0.06, r * 0.82, r * 0.80, col, lift=0.25)
        c.ellipse(u, v, r * 0.40, r * 0.36, scale(col, 0.62), lift=0.0, alpha=0.8)
        c.ellipse(u - r * 0.3, v + r * 0.35, r * 0.22, r * 0.14, mix(col, WHITE, 0.6), lift=0.0, alpha=0.8)
    else:
        col = MARI[rng.randrange(4)]
        c.ellipse(u, v, r, r * 0.95, scale(col, 0.66), lift=0.0)
        c.ellipse(u - r * 0.04, v + r * 0.05, r * 0.86, r * 0.82, col, lift=0.25)
        c.ellipse(u, v, r * 0.36, r * 0.34, mix(col, (0.7, 0.25, 0.0), 0.5), lift=0.0, alpha=0.75)
        c.ellipse(u - r * 0.3, v + r * 0.3, r * 0.22, r * 0.14, mix(col, WHITE, 0.55), lift=0.0, alpha=0.8)


def _strand_beads(c, rng, pts, r, rose_every=0):
    """Beads of a flower garland along a polyline of (u, v) points, with a few leaves."""
    for i, (u, v) in enumerate(pts):
        if i % 4 == 2:
            craft.leaf(c, u, v, r * 2.3, rng.uniform(0, 360), (0.16, 0.42, 0.18), 0.5)
        _bead(c, u, v, r * rng.uniform(0.9, 1.1), rng, rose=bool(rose_every and i % rose_every == 0))


def _sag(u0, v0, u1, v1, depth, n):
    return [(u0 + (u1 - u0) * k / float(n), v0 + (v1 - v0) * k / float(n) - math.sin(math.pi * k / float(n)) * depth) for k in range(n + 1)]


def _flame(c, u, v, h, glow=True):
    if glow:
        c.glow(u, v + h * 0.45, h * 3.2, (1.0, 0.62, 0.22), 0.34)
        c.glow(u, v + h * 0.5, h * 1.6, (1.0, 0.85, 0.5), 0.6)
    w = h * 0.30
    _poly(c, [(u, v), (u + w * 0.85, v + h * 0.25), (u + w * 0.55, v + h * 0.62), (u, v + h), (u - w * 0.55, v + h * 0.62), (u - w * 0.85, v + h * 0.25)],
          (1.0, 0.55, 0.10), (1.0, 0.86, 0.35), 0.95)
    _poly(c, [(u, v + h * 0.04), (u + w * 0.38, v + h * 0.25), (u, v + h * 0.66), (u - w * 0.38, v + h * 0.25)], (1.0, 0.95, 0.7), (1.0, 1.0, 0.92), 0.95)


@sprop("auto_mandap", aspect=1.95, fill=1.0)
def auto_mandap(c, color):
    """Wedding mandap: raised stage, four pillars wrapped in marigold, a stepped canopy with scalloped valance, hanging strings, havan kund."""
    rng = c.rng
    acc = color or (0.9, 0.5, 0.1)
    c.glow(0.0, 0.45, 1.05, (1.0, 0.7, 0.35), 0.24)
    # stage platform with steps and carpet
    ao(c, 0.0, 0.0, 2.0, 0.18, 0.5)
    _rr(c, -0.99, 0.0, 0.99, 0.075, (0.95, 0.88, 0.78), (0.70, 0.60, 0.50), 0.01)
    _rr(c, -0.93, 0.075, 0.93, 0.13, (0.98, 0.92, 0.84), (0.78, 0.68, 0.56), 0.01)
    _rr(c, -0.93, 0.125, 0.93, 0.138, mix(GOLD, WHITE, 0.2), scale(GOLD, 0.6), 0.0)
    _rr(c, -0.30, 0.0, 0.30, 0.13, CRIMSON, scale(CRIMSON, 0.55), 0.0, 0.95)                       # carpet on the steps
    c.line(-0.30, 0.0, -0.30, 0.13, 0.008, GOLD)
    c.line(0.30, 0.0, 0.30, 0.13, 0.008, GOLD)
    # back pillars (smaller, deeper), then back drape
    for pu in (-0.58, 0.58):
        _hfill(c, pu - 0.028, 0.138, pu + 0.028, 0.66, _cyl_fn(mix(GOLD, WHITE, 0.4), scale(GOLD, 0.45), 0.35))
        _rr(c, pu - 0.05, 0.138, pu + 0.05, 0.17, mix(GOLD, WHITE, 0.2), scale(GOLD, 0.5), 0.01)
    _rr(c, -0.60, 0.17, 0.60, 0.66, scale(CRIMSON, 0.6), scale(CRIMSON, 0.30), 0.0, 0.85)
    c.glow(0.0, 0.42, 0.55, (1.0, 0.7, 0.3), 0.25)
    # havan kund with flame and a kalash
    _rr(c, -0.12, 0.138, 0.12, 0.215, mix(GOLD, (0.6, 0.15, 0.1), 0.4), scale(GOLD, 0.5), 0.01)
    _rr(c, -0.09, 0.215, 0.09, 0.235, (0.2, 0.1, 0.06), (0.1, 0.05, 0.03), 0.01)
    _flame(c, 0.0, 0.235, 0.20)
    craft.hshade_box(c, 0.30, 0.205, 0.075, 0.12, mix(GOLD, (0.8, 0.4, 0.2), 0.3), scale(GOLD, 0.4), r=0.03)
    c.ellipse(0.30, 0.27, 0.045, 0.045, (0.55, 0.38, 0.2), lift=0.3)
    for k in range(5):
        craft.leaf(c, 0.30, 0.28, 0.12, 60 + k * 15, (0.16, 0.45, 0.2), 0.4)
    # front pillars
    for pu in (-0.86, 0.86):
        _rr(c, pu - 0.085, 0.138, pu + 0.085, 0.20, mix(GOLD, WHITE, 0.2), scale(GOLD, 0.45), 0.015)
        _hfill(c, pu - 0.05, 0.20, pu + 0.05, 0.70, _cyl_fn(mix((0.98, 0.94, 0.86), GOLD, 0.2), scale(GOLD, 0.40), 0.4))
        for k in range(4):
            c.line(pu - 0.05, 0.28 + k * 0.14, pu + 0.05, 0.28 + k * 0.14, 0.012, scale(GOLD, 0.55), 0.8)
        _rr(c, pu - 0.075, 0.68, pu + 0.075, 0.74, mix(GOLD, WHITE, 0.2), scale(GOLD, 0.45), 0.012)
        pts = [(pu + math.sin(k * 0.9 + (1 if pu < 0 else 0)) * 0.058, 0.22 + k * 0.047) for k in range(10)]          # marigold wrapped round the pillar
        _strand_beads(c, rng, pts, 0.022)
    # canopy: beam, stepped roof with gold stripes, finial
    _rr(c, -1.00, 0.72, 1.00, 0.785, mix(GOLD, WHITE, 0.25), scale(GOLD, 0.5), 0.012)
    _poly(c, [(-0.98, 0.785), (0.98, 0.785), (0.72, 0.88), (-0.72, 0.88)], mix(CRIMSON, WHITE, 0.08), scale(CRIMSON, 0.55))
    _poly(c, [(-0.72, 0.88), (0.72, 0.88), (0.40, 0.945), (-0.40, 0.945)], mix(CRIMSON, WHITE, 0.14), scale(CRIMSON, 0.6))
    for k in range(-4, 5):
        c.line(k * 0.2, 0.788, k * 0.2 * 0.72, 0.95, 0.01, GOLD, 0.8)
    _poly(c, [(-0.12, 0.945), (0.12, 0.945), (0.0, 1.02)], GOLD, scale(GOLD, 0.6))
    # scalloped valance along the beam with tassels
    for k in range(-9, 10):
        u = k * 0.105
        col = CRIMSON if k % 2 else GOLD
        c.ellipse(u, 0.72, 0.055, 0.065, scale(col, 0.62), lift=0.0)
        c.ellipse(u, 0.723, 0.050, 0.058, col, lift=0.2)
        c.ellipse(u, 0.690, 0.012, 0.012, mix(GOLD, WHITE, 0.3), lift=0.3)
    # hanging marigold strings
    for k in range(-8, 9):
        u = k * 0.115 + rng.uniform(-0.01, 0.01)
        ln = rng.uniform(0.10, 0.30)
        n = 3 + int(ln * 14)
        _strand_beads(c, rng, [(u + math.sin(i * 0.8) * 0.004, 0.68 - i * ln / n) for i in range(n)], 0.017, rose_every=0)
    # swag garlands between the front pillars
    _strand_beads(c, rng, _sag(-0.86, 0.64, 0.86, 0.64, 0.11, 22), 0.024, rose_every=5)
    soft_disc(c, -0.5, 0.55, 0.9, 0.25, (1.0, 0.8, 0.4), 0.06, 1.2, 0, True)


@sprop("auto_diyas", aspect=4.6, fill=0.30)
def auto_diyas(c, color):
    """Three clay diyas with live flames and scattered marigold petals."""
    rng = c.rng
    for u, v, r in ((-0.38, 0.06, 0.20), (0.02, 0.025, 0.24), (0.42, 0.065, 0.19)):
        c.ellipse(u + 0.01, v - 0.005, r * 1.0, r * 0.45, BLACK, lift=0.0, alpha=0.35)
        c.ellipse(u, v + 0.03, r, r * 0.55, (0.55, 0.20, 0.10), lift=0.0)
        c.ellipse(u, v + 0.06, r * 0.98, r * 0.52, (0.80, 0.38, 0.18), lift=0.2)
        c.ellipse(u, v + 0.085, r * 0.78, r * 0.34, (0.30, 0.12, 0.06), lift=0.0)
        c.ellipse(u, v + 0.075, r * 0.7, r * 0.28, (0.98, 0.78, 0.30), lift=0.0, alpha=0.7)
        _flame(c, u + r * 0.1, v + 0.09, 0.19)
        for k in range(10):
            gloss(c, u - r * 0.5, v + 0.07, r * 0.2, r * 0.07, 0, 0.3)
    for _ in range(12):
        _bead(c, rng.uniform(-0.65, 0.65), rng.uniform(-0.02, 0.12), 0.034, rng, rose=rng.random() < 0.3)


@sprop("auto_thali", aspect=3.2, fill=0.34)
def auto_thali(c, color):
    """Brass puja thali heaped with rose petals and marigolds."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.14, 0.4)
    c.ellipse(0.0, 0.05, 0.54, 0.54 * TILT, scale(GOLD, 0.5), lift=0.0)
    c.ellipse(0.0, 0.09, 0.54, 0.54 * TILT, mix(GOLD, WHITE, 0.15), lift=0.25)
    c.ellipse(0.0, 0.10, 0.46, 0.46 * TILT, scale(GOLD, 0.7), lift=0.15)
    c.ellipse(0.0, 0.105, 0.40, 0.40 * TILT, mix(GOLD, WHITE, 0.1), lift=0.1)
    for i in range(34):
        a = rng.uniform(0, 2 * math.pi)
        rr_ = math.sqrt(rng.random()) * 0.34
        _bead(c, math.cos(a) * rr_, 0.13 + math.sin(a) * rr_ * TILT + (1 - rr_ / 0.34) * 0.05, rng.uniform(0.045, 0.075), rng, rose=(i % 3 == 0))
    _flame(c, 0.0, 0.2, 0.16)
    craft.arc(c, 0.0, 0.10, 0.50, 0.50 * TILT, 200, 340, 0.01, (1.0, 0.95, 0.7), 0.7, steps=10)


@sprop("auto_rangoli", aspect=6.1, fill=0.30)
def auto_rangoli(c, color):
    """Floor rangoli: concentric petal rings in bright powder colours."""
    rng = c.rng
    cols = [(0.95, 0.30, 0.10), (1.0, 0.75, 0.10), (0.85, 0.10, 0.35), (0.98, 0.95, 0.85), (0.25, 0.60, 0.30)]
    c.ellipse(0.0, 0.0, 0.92, 0.92 * 0.30, (0.15, 0.05, 0.03), lift=0.0, alpha=0.25)
    for i, (r, col) in enumerate(((0.88, cols[0]), (0.78, cols[1]), (0.66, cols[2]), (0.52, cols[3]), (0.36, cols[0]), (0.2, cols[1]))):
        c.ellipse(0.0, 0.0, r, r * 0.30, col, lift=0.1)
        for k in range(10):
            a = math.radians(k * 360 / 10 + i * 9)
            c.ellipse(math.cos(a) * r * 0.80, math.sin(a) * r * 0.80 * 0.30, r * 0.11, r * 0.08, cols[(i + k) % 5], lift=0.1)
    c.ellipse(0.0, 0.0, 0.07, 0.025, (1.0, 0.95, 0.8), lift=0.1)
    soft_disc(c, -0.2, 0.05, 0.6, 0.12, WHITE, 0.15, 1.2, 0, True)


@niche("wedding", "Wedding mandap and banquet", subjects=("auto_mandap",),
       strong=("wedding", "mandap", "shaadi", "marriage", "bride", "groom", "banquet", "wedding planner", "marriage hall", "vivah",
               "शादी", "मंडप", "विवाह", "बैंक्वेट", "शादी का हॉल"),
       weak=("decoration", "flower decoration", "sangeet", "reception", "baraat", "haldi", "mehendi", "engagement"), accent="#e67e22", mood="warm",
       group="events", avoid=("photographer", "photography", "photo studio", "birthday"))
def wedding(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    drape = mix(P.accent_dark, CRIMSON, 0.65)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.66)
        for k in range(-12, 28):                                                        # pleated drapes
            col = scale(drape, 0.9 + 0.35 * (k % 2)) if not dk else scale(drape, 0.55 + 0.3 * (k % 2))
            S.gradient_rect(-1.3 + k * 0.2, 0.0, -1.3 + k * 0.2 + 0.2, 0.68, mix(col, WHITE, 0.15), scale(col, 0.55))
        S.rect(1.0, 0.04, 6, 0.09, scale(GOLD, 0.7 if dk else 0.9), lift=0.1)                                # pelmet
        for k in range(-12, 28):
            S.circle(-1.3 + k * 0.2 + 0.1, 0.09, 0.042, GOLD if k % 2 else mix(GOLD, CRIMSON, 0.4), lift=0.1)
        for ul in (0.3, 1.1, 1.9):                                                      # chandeliers
            S.glow(ul, 0.22, 0.55, (1.0, 0.78, 0.4), 0.75 if dk else 0.45)
            S.circle(ul, 0.20, 0.025, (1.0, 0.9, 0.6), lift=0.0)
            for k in range(-3, 4):
                S.circle(ul + k * 0.025, 0.26 + abs(k) * 0.01, 0.007, (1.0, 0.92, 0.7), lift=0.0)
        S.bokeh(34, -0.2, 0.12, 2.3, 0.62, [(1.0, 0.78, 0.40), (1.0, 0.62, 0.25), (1.0, 0.9, 0.65)], 0.007, 0.026, 0.55 if dk else 0.4)
        for k in range(18):                                                             # marigold curtain strings at the far left / right
            u = rng.choice([rng.uniform(-0.4, 0.5), rng.uniform(1.8, 2.4)])
            for j in range(rng.randint(5, 10)):
                S.circle(u, 0.1 + j * 0.04, 0.014, MARI[(k + j) % 4], lift=0.15)
        S.floor(0.66, scale(mix(P.floor_top, (0.78, 0.62, 0.42), 0.35), 0.78), scale(mix(P.floor_bot, (0.50, 0.35, 0.22), 0.35), 0.7))
        S.soft(1.1, 0.78, 1.1, 0.18, (1.0, 0.75, 0.40), 0.55 if dk else 0.35, 1.3, add=True)
    for k in range(-8, 12):
        _shair(S, 0.2 + k * 0.4, 0.67, 0.2 + k * 0.4 - 1.2 + k * 0.28, 1.4, (0.0, 0.0, 0.0), 0.10)
    for vv in (0.74, 0.86, 1.02, 1.25):
        _shair(S, -2, vv, 4, vv, (0.0, 0.0, 0.0), 0.10)
    # red carpet runner in perspective with a gold border, rangoli, scattered petals
    _spoly(S, [(0.95, 0.80), (1.25, 0.80), (1.95, 1.4), (0.25, 1.4)], mix(CRIMSON, WHITE, 0.08), scale(CRIMSON, 0.55))
    _spoly(S, [(0.93, 0.80), (0.96, 0.80), (0.30, 1.4), (0.22, 1.4)], mix(GOLD, WHITE, 0.2), scale(GOLD, 0.6))
    _spoly(S, [(1.24, 0.80), (1.27, 0.80), (1.98, 1.4), (1.90, 1.4)], mix(GOLD, WHITE, 0.2), scale(GOLD, 0.6))
    S.soft(1.1, 0.92, 0.6, 0.12, (1.0, 0.7, 0.35), 0.45 if dk else 0.30, 1.4, add=True)
    S.put("auto_mandap", 1.10, 0.84, 0.64, color=P.accent, shadow_alpha=0.40)
    S.mark_subject("auto_mandap", 0.82, 0.38, 1.38, 0.84)
    S.put("auto_rangoli", 1.10, 0.96, 0.15, shadow=False, shadow_alpha=0.0)
    S.put("auto_diyas", 0.66, 1.0, 0.10, shadow=False)
    S.put("auto_thali", 1.58, 1.0, 0.10, shadow_alpha=0.3)
    for _ in range(26):
        u, v = rng.uniform(0.55, 1.7), rng.uniform(0.92, 1.05)
        S.ellipse(u, v, 0.012, 0.007, MARI[rng.randrange(4)] if rng.random() < 0.7 else ROSE[rng.randrange(3)], lift=0.15, alpha=0.9)
    S.focus("detail", 1.10, 0.56)
    with S.near(blur=16):
        S.glow(0.5, 1.02, 0.22, (1.0, 0.7, 0.3), 0.4)
        S.soft(1.78, 0.22, 0.22, 0.2, (1.0, 0.65, 0.2), 0.30, 1.2, add=True)
        for k in range(5):
            S.soft(0.5 + k * 0.07, 0.10 + (k % 2) * 0.06, 0.05, 0.05, MARI[k % 4], 0.5, 1.0)


# ====================================================================================== party / event
PARTY = ((0.96, 0.78, 0.22), (0.20, 0.72, 0.74), (0.55, 0.36, 0.85), (0.98, 0.45, 0.30), (0.45, 0.78, 0.35), (0.98, 0.96, 0.92))


def _balloon(c, u, v, a, b, col, rng):
    """A glossy balloon: body, darker rim crescent, specular highlight, knot and curly string."""
    c.ellipse(u + a * 0.07, v - b * 0.05, a, b, scale(col, 0.62), lift=0.0)
    c.ellipse(u - a * 0.03, v + b * 0.03, a * 0.95, b * 0.96, col, lift=0.28)
    soft_disc(c, u + a * 0.35, v - b * 0.35, a * 0.7, b * 0.6, scale(col, 0.4), 0.35, 1.2)
    soft_disc(c, u - a * 0.38, v + b * 0.40, a * 0.35, b * 0.22, WHITE, 0.85, 1.0, 40, True)
    c.ellipse(u - a * 0.44, v + b * 0.44, a * 0.10, b * 0.06, WHITE, lift=0.0, alpha=0.95)
    _poly(c, [(u - a * 0.07, v - b * 0.98), (u + a * 0.07, v - b * 0.98), (u + a * 0.02, v - b * 1.1), (u - a * 0.02, v - b * 1.1)], scale(col, 0.7), scale(col, 0.55))


@sprop("auto_balloons", aspect=0.80, fill=1.0)
def auto_balloons(c, color):
    """A bouquet of balloons tied to a small weight with ribbons."""
    rng = c.rng
    acc = color or (0.91, 0.26, 0.58)
    cols = [acc, PARTY[0], PARTY[1], mix(acc, WHITE, 0.55), PARTY[2], mix(acc, (0.6, 0.1, 0.4), 0.5), PARTY[5], PARTY[1]]
    spots = [(-0.08, 0.80, 0.0), (0.22, 0.72, 0.0), (-0.28, 0.62, 1.0), (0.36, 0.52, 1.0), (0.04, 0.56, 1.0), (-0.40, 0.42, 2.0), (0.18, 0.36, 2.0)]
    rng2 = rng
    # ribbons first (they gather at a point), then the balloons from back to front
    gather = (0.0, 0.10)
    for i, (u, v, z) in enumerate(spots):
        c.line(u, v - 0.20, gather[0] + (u - gather[0]) * 0.3, gather[1] + 0.12, 0.004, mix(cols[i], WHITE, 0.3), 0.85)
    _rr(c, -0.07, 0.0, 0.07, 0.10, (0.85, 0.72, 0.30), (0.55, 0.42, 0.12), 0.012)
    ao(c, 0.0, 0.0, 0.2, 0.05, 0.4)
    order = sorted(range(len(spots)), key=lambda k: -spots[k][2])
    for k in order:
        u, v, z = spots[k]
        _balloon(c, u, v, 0.17, 0.205, cols[k], rng2)


@sprop("auto_cake", aspect=1.0, fill=1.0)
def auto_cake(c, color):
    """Three tier party cake on a stand: frosting drips, sprinkles, gold trim, candles with flames and berries on top."""
    rng = c.rng
    acc = color or (0.91, 0.26, 0.58)
    cream = (0.99, 0.93, 0.90)
    pinkA = mix(acc, WHITE, 0.45)
    ao(c, 0.0, 0.0, 1.0, 0.16, 0.45)
    # stand: foot, stem and plate
    c.ellipse(0.0, 0.015, 0.20, 0.20 * TILT, (0.85, 0.86, 0.9), lift=0.2)
    _hfill(c, -0.035, 0.02, 0.035, 0.12, _cyl_fn((0.98, 0.98, 1.0), (0.60, 0.62, 0.68), 0.5))
    c.ellipse(0.0, 0.13, 0.52, 0.52 * TILT, (0.78, 0.80, 0.86), lift=0.1)
    c.ellipse(0.0, 0.145, 0.50, 0.50 * TILT, (0.97, 0.97, 0.99), lift=0.2)
    tiers = [(0.0, 0.44, 0.17, 0.26, pinkA), (1.0, 0.33, 0.43, 0.23, mix(acc, WHITE, 0.3)), (2.0, 0.22, 0.66, 0.20, mix(acc, WHITE, 0.65))]
    for idx, w, v0, h, col in tiers:
        soft_disc(c, 0.03, v0 + 0.01, w * 1.08, w * TILT * 0.9, BLACK, 0.30, 1.4)
        c.ellipse(0.0, v0, w, w * TILT, scale(col, 0.80), lift=0.0)
        _hfill(c, -w, v0, w, v0 + h, _cyl_fn(mix(col, WHITE, 0.25), scale(col, 0.82), 0.35))
        for _ in range(int(14 + w * 30)):                                                  # sprinkles on the side
            u = rng.uniform(-w * 0.92, w * 0.92)
            c.line(u, v0 + rng.uniform(0.03, h * 0.75), u + rng.uniform(-0.012, 0.012), v0 + rng.uniform(0.02, h * 0.78), 0.007, PARTY[rng.randrange(6)], 0.95)
        c.line(-w, v0 + 0.012, w, v0 + 0.012, 0.012, (0.92, 0.75, 0.30), 0.0)
        # frosting top and scalloped drips along the upper edge
        c.ellipse(0.0, v0 + h, w * 1.01, w * 1.01 * TILT, cream, lift=0.12)
        c.ellipse(0.0, v0 + h - 0.005, w * 1.01, w * 1.01 * TILT, scale(cream, 0.85), lift=0.0, alpha=0.0)
        n = int(w * 14)
        for k in range(n + 1):
            u = -w + 2 * w * k / float(n)
            dl = rng.uniform(0.025, 0.075)
            ex = math.sqrt(max(0.0, 1.0 - (u / (w * 1.0)) ** 2))
            vv = v0 + h - w * TILT * (1 - ex) * 0.0 - w * TILT * ex
            c.ellipse(u, v0 + h - w * TILT * ex * 0.0 - 0.012 - w * TILT * 0.0, 0.026, dl, cream, lift=0.1, alpha=0.95)
        c.ellipse(0.0, v0 + h + 0.004, w * 0.93, w * 0.93 * TILT * 0.92, mix(cream, acc, 0.12), lift=0.08)
        gloss(c, -w * 0.4, v0 + h + 0.03, w * 0.35, w * 0.08, 5, 0.35)
    # strawberries / cherries and candles on the top tier
    top = 0.66 + 0.20
    for u in (-0.10, 0.10):
        c.ellipse(u, top + 0.025, 0.055, 0.05, (0.75, 0.05, 0.12), lift=0.2)
        gloss(c, u - 0.02, top + 0.045, 0.015, 0.012, 0, 0.9)
        craft.leaf(c, u, top + 0.07, 0.05, 80, (0.2, 0.55, 0.22), 0.5)
    for k, u in enumerate((-0.05, 0.0, 0.05)):
        h = 0.14 + (k % 2) * 0.02
        _rr(c, u - 0.011, top + 0.01, u + 0.011, top + 0.01 + h, PARTY[1] if k % 2 else PARTY[0], scale(PARTY[1] if k % 2 else PARTY[0], 0.6), 0.004)
        c.line(u, top + 0.01 + h, u, top + 0.025 + h, 0.003, (0.1, 0.1, 0.1), 0.9)
        _flame(c, u, top + 0.025 + h, 0.06)


@sprop("auto_gifts", aspect=1.3, fill=0.55)
def auto_gifts(c, color):
    """Wrapped gift boxes with ribbons and a bow."""
    rng = c.rng
    acc = color or (0.91, 0.26, 0.58)
    ao(c, 0.0, 0.0, 1.2, 0.2, 0.4)
    for u, v, w, h, col, rib in ((-0.30, 0.0, 0.40, 0.34, mix(PARTY[1], WHITE, 0.05), (0.98, 0.90, 0.5)), (0.28, 0.0, 0.34, 0.26, acc, WHITE),
                                 (0.02, 0.0, 0.30, 0.20, PARTY[0], mix(acc, WHITE, 0.2))):
        z = 0.0 if u != 0.02 else 0.34
        v0 = v + (0.0 if u != 0.02 else 0.30)
        w2 = w / 2
        _hfill(c, u - w2, v0, u + w2, v0 + h, lambda t, col=col: mix(mix(col, WHITE, 0.2), scale(col, 0.62), t ** 1.2), strips=8)
        c.ellipse(u, v0 + h, w2, w2 * TILT * 0.9, mix(col, WHITE, 0.30), lift=0.1)
        _rr(c, u - 0.022, v0, u + 0.022, v0 + h, rib, scale(rib, 0.75), 0.0, 0.95)
        c.line(u - w2 * 0.9, v0 + h, u + w2 * 0.9, v0 + h, 0.04 * 0.0 + 0.0001, rib, 0.0)
        c.ellipse(u, v0 + h, 0.022, w2 * TILT * 0.9, rib, lift=0.1)
        for sgn in (-1, 1):                                                   # bow
            c.ellipse(u + sgn * 0.055, v0 + h + 0.04, 0.05, 0.035, rib, lift=0.2, angle=sgn * 25)
            c.ellipse(u + sgn * 0.055, v0 + h + 0.04, 0.025, 0.017, scale(rib, 0.65), lift=0.0, angle=sgn * 25, alpha=0.8)
        c.ellipse(u, v0 + h + 0.03, 0.02, 0.02, scale(rib, 0.9), lift=0.2)


@sprop("auto_cupcakes", aspect=2.2, fill=0.45)
def auto_cupcakes(c, color):
    """Three frosted cupcakes with sprinkles."""
    rng = c.rng
    acc = color or (0.91, 0.26, 0.58)
    for u, col in ((-0.50, PARTY[1]), (0.0, acc), (0.50, PARTY[0])):
        ao(c, u, 0.0, 0.40, 0.08, 0.4)
        _poly(c, [(u - 0.19, 0.20), (u + 0.19, 0.20), (u + 0.145, 0.0), (u - 0.145, 0.0)], mix(col, WHITE, 0.2), scale(col, 0.55))
        for k in range(-4, 5):
            c.line(u + k * 0.04, 0.02, u + k * 0.05, 0.19, 0.005, scale(col, 0.45), 0.5)
        for j, w in enumerate((0.21, 0.17, 0.12)):                                # swirl of frosting
            v = 0.20 + j * 0.07
            c.ellipse(u, v + 0.03, w, 0.055, mix((0.99, 0.92, 0.90), acc, 0.0 if j else 0.2), lift=0.25)
        for _ in range(9):
            uu, vv = u + rng.uniform(-0.15, 0.15), rng.uniform(0.22, 0.38)
            c.line(uu, vv, uu + rng.uniform(-0.015, 0.015), vv + rng.uniform(-0.01, 0.01), 0.008, PARTY[rng.randrange(6)])
        c.ellipse(u, 0.43, 0.035, 0.03, (0.75, 0.05, 0.12), lift=0.25)
        gloss(c, u - 0.01, 0.44, 0.012, 0.009, 0, 0.9)


@sprop("auto_party_hat", aspect=0.65, fill=1.0)
def auto_party_hat(c, color):
    acc = color or (0.91, 0.26, 0.58)
    ao(c, 0.0, 0.0, 0.7, 0.10, 0.4)
    _poly(c, [(-0.33, 0.0), (0.33, 0.0), (0.0, 0.95)], mix(acc, WHITE, 0.15), scale(acc, 0.65))
    for k in range(4):
        v = 0.12 + k * 0.17
        w = 0.33 * (1 - v / 0.95)
        c.line(-w, v, w, v + 0.04, 0.035, PARTY[0] if k % 2 else WHITE, 0.95)
    c.ellipse(0.0, 0.0, 0.33, 0.065, scale(acc, 0.5), lift=0.0)
    c.ellipse(0.0, 0.97, 0.07, 0.07, PARTY[0], lift=0.25)
    soft_disc(c, -0.10, 0.50, 0.08, 0.30, WHITE, 0.25, 1.1, 8, True)


def _confetti(S, rng, n, u0, v0, u1, v1, size=0.012, alpha=0.95):
    for _ in range(n):
        col = PARTY[rng.randrange(6)] if rng.random() < 0.65 else mix(S.pal.accent, WHITE, rng.uniform(0.0, 0.4))
        S.ellipse(rng.uniform(u0, u1), rng.uniform(v0, v1), size * rng.uniform(0.7, 1.3), size * rng.uniform(0.3, 0.6), col, angle=rng.uniform(0, 180),
                  lift=0.0, alpha=alpha)


@niche("event-party", "Party and event planner", subjects=("auto_cake",),
       strong=("party", "birthday", "event planner", "decoration", "celebration", "balloons", "birthday party", "party planner", "balloon decoration",
               "event management", "पार्टी", "जन्मदिन", "बर्थडे", "इवेंट", "सजावट", "birthday decoration"),
       weak=("event", "events", "cake", "anniversary", "kids party", "catering", "surprise"), accent="#e84393", mood="light", group="events",
       avoid=("wedding", "mandap", "marriage"))
def event_party(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # streamer curtain on both sides and bunting across
        for k in range(26):
            u = -1.0 + k * 0.045 if k < 13 else 1.65 + (k - 13) * 0.045
            col = [P.accent, PARTY[0], PARTY[1], PARTY[2], mix(P.accent, WHITE, 0.5), PARTY[3]][k % 6]
            S.rect(u, 0.20 + (k % 3) * 0.04, 0.03, 0.42 + (k % 3) * 0.08, col if not dk else scale(col, 0.7), lift=0.15)
        n = 24
        for k in range(n):
            t = k / float(n - 1)
            u = 0.1 + t * 1.9
            v = 0.12 + math.sin(t * math.pi) * 0.09
            col = [P.accent, PARTY[0], PARTY[1], PARTY[2], PARTY[3]][k % 5]
            S.poly([(u - 0.03, v), (u + 0.03, v), (u, v + 0.075)], col if not dk else scale(col, 0.8))
        S.line(0.1, 0.12, 2.0, 0.12, 0.004, scale(P.wall_bot, 0.5))
        # fairy lights and a balloon arch of soft discs
        for k in range(26):
            t = k / 25.0
            u = -0.2 + t * 2.5
            v = 0.34 + math.sin(t * 3 * math.pi) * 0.05 + t * 0.02
            col = [(1.0, 0.85, 0.5), (1.0, 0.6, 0.7), (0.7, 0.9, 1.0)][k % 3]
            S.glow(u, v, 0.07, col, 0.9 if dk else 0.55)
            S.circle(u, v, 0.006, mix(col, WHITE, 0.5), lift=0.0)
        for k in range(14):
            col = [P.accent, PARTY[0], PARTY[1], PARTY[2], mix(P.accent, WHITE, 0.5)][k % 5]
            S.circle(rng.uniform(-0.2, 2.2), rng.uniform(0.25, 0.55), rng.uniform(0.05, 0.11), col, alpha=0.35 if not dk else 0.3, lift=0.2)
        if dk:
            for ug, cg in ((0.3, P.accent), (1.0, PARTY[1]), (1.7, PARTY[2])):
                S.glow(ug, 0.25, 0.6, cg, 0.5)
        # table cloth: soft folds, a lighter top and a scalloped drop
        S.floor(0.60, mix(P.accent_light, WHITE, 0.55 if not dk else 0.0) if not dk else scale(P.accent_dark, 0.9), mix(P.accent, WHITE, 0.35) if not dk else scale(P.accent_dark, 0.55))
        S.soft(1.1, 0.80, 1.0, 0.22, (1.0, 0.98, 0.95), 0.35 if not dk else 0.35, 1.3, add=True)
    for k in range(-6, 14):                                                         # cloth folds
        _shair(S, 0.2 + k * 0.28, 0.61, 0.2 + k * 0.28 - 0.5 + k * 0.1, 1.4, (0.0, 0.0, 0.0), 0.05)
    for k in range(9):
        S.soft(rng.uniform(0.3, 2.0), rng.uniform(0.7, 1.1), rng.uniform(0.15, 0.3), rng.uniform(0.02, 0.05), mix(P.accent_dark, BLACK, 0.3), 0.10, 1.4)
    _spoly(S, [(0.80, 0.62), (1.44, 0.62), (1.92, 1.4), (0.32, 1.4)], mix(WHITE, P.accent_light, 0.15), mix(WHITE, P.accent_light, 0.35), 0.75)
    _spoly(S, [(0.82, 0.62), (0.84, 0.62), (0.36, 1.4), (0.31, 1.4)], mix(P.accent, WHITE, 0.2), None, 0.8)
    _spoly(S, [(1.40, 0.62), (1.42, 0.62), (1.93, 1.4), (1.88, 1.4)], mix(P.accent, WHITE, 0.2), None, 0.8)
    _confetti(S, rng, 50, 0.4, 0.68, 1.9, 1.06, 0.012)
    S.put("auto_balloons", 0.62, 0.90, 0.64, color=P.accent, shadow_alpha=0.3)
    S.put("auto_cake", 1.12, 0.86, 0.50, color=P.accent, subject=True, shadow_alpha=0.4)
    S.put("auto_gifts", 1.56, 0.90, 0.15, color=P.accent, shadow_alpha=0.3)
    S.put("auto_cupcakes", 0.88, 1.0, 0.12, color=P.accent, shadow_alpha=0.3)
    S.put("auto_party_hat", 1.43, 1.0, 0.16, color=P.accent, shadow_alpha=0.3)
    S.focus("detail", 1.12, 0.60)
    with S.near(blur=18):
        for k in range(8):
            u, v, r = rng.uniform(0.45, 1.8), rng.uniform(0.2, 1.0), rng.uniform(0.03, 0.07)
            S.soft(u, v, r, r, [P.accent, PARTY[0], PARTY[1], PARTY[2]][k % 4], 0.55, 1.0)
        _confetti(S, rng, 8, 0.4, 0.2, 1.9, 1.05, 0.02, 0.6)


# ====================================================================================== travel agency
BRASS = (0.86, 0.66, 0.28)


@sprop("auto_globe", aspect=0.88, fill=1.0)
def auto_globe(c, color):
    """Desk globe on a brass meridian: ocean, continents, graticule, soft shading and a specular highlight."""
    rng = c.rng
    ocean = (0.16, 0.50, 0.72)
    ao(c, 0.0, 0.0, 0.6, 0.10, 0.45)
    c.ellipse(0.0, 0.02, 0.26, 0.26 * TILT, scale(BRASS, 0.5), lift=0.0)
    c.ellipse(0.0, 0.045, 0.255, 0.255 * TILT, mix(BRASS, WHITE, 0.15), lift=0.25)
    _hfill(c, -0.03, 0.05, 0.03, 0.22, _cyl_fn(mix(BRASS, WHITE, 0.4), scale(BRASS, 0.4), 0.5))
    gv, r = 0.62, 0.37
    craft.arc(c, 0.0, gv, r * 1.09, r * 1.09, -65, 115, 0.022, scale(BRASS, 0.55), 0.95, steps=14)
    craft.arc(c, 0.0, gv, r * 1.09, r * 1.09, -63, 113, 0.012, mix(BRASS, WHITE, 0.45), 0.9, steps=14)
    # sphere
    c.ellipse(0.0, gv, r, r, scale(ocean, 0.62), lift=0.0)
    c.ellipse(-0.012, gv + 0.012, r * 0.97, r * 0.97, ocean, lift=0.30)
    soft_disc(c, -0.10, gv + 0.10, r * 0.75, r * 0.65, mix(ocean, WHITE, 0.45), 0.55, 1.3)
    for (u, v, a, b, ang, col) in ((-0.12, 0.10, 0.12, 0.17, 25, (0.38, 0.66, 0.34)), (-0.10, -0.12, 0.07, 0.14, -15, (0.40, 0.68, 0.36)),
                                   (0.12, 0.04, 0.09, 0.16, -20, (0.86, 0.74, 0.46)), (0.15, -0.14, 0.07, 0.08, 30, (0.42, 0.66, 0.36)),
                                   (0.20, 0.17, 0.10, 0.06, 10, (0.82, 0.78, 0.55)), (-0.2, -0.04, 0.05, 0.07, 40, (0.38, 0.66, 0.34))):
        c.ellipse(u, gv + v, a, b, scale(col, 0.82), lift=0.0, angle=ang, alpha=0.95)
        c.ellipse(u - 0.006, gv + v + 0.008, a * 0.88, b * 0.88, col, lift=0.2, angle=ang)
    for k in (-0.25, 0.25, 0.7):                                       # meridians
        craft.arc(c, 0.0, gv, r * abs(math.sin(math.acos(max(-1, min(1, k))))) if False else r * (1 - abs(k)) * 0.95 + 0.01, r * 0.98, -90, 90, 0.003, WHITE, 0.30, steps=10)
        craft.arc(c, 0.0, gv, r * (1 - abs(k)) * 0.95 + 0.01, r * 0.98, 90, 270, 0.003, WHITE, 0.30, steps=10)
    for lat in (-0.5, -0.15, 0.2, 0.55):                               # parallels
        wv = math.sqrt(1 - lat * lat) * r
        craft.arc(c, 0.0, gv + lat * r, wv, wv * 0.16, 180, 360, 0.003, WHITE, 0.30, steps=10)
    soft_disc(c, 0.17, gv - 0.15, r * 0.95, r * 0.85, (0.02, 0.05, 0.15), 0.62, 1.1)
    soft_disc(c, -0.13, gv + 0.15, r * 0.30, r * 0.16, WHITE, 0.85, 1.0, 40, True)
    c.ellipse(-0.19, gv + 0.21, 0.025, 0.014, WHITE, lift=0.0, alpha=0.9, angle=40)


@sprop("auto_suitcase", aspect=1.05, fill=1.0)
def auto_suitcase(c, color):
    """Hard shell travel suitcase with ribs, gold corners and latches, a strap, handle, wheels and stickers."""
    rng = c.rng
    col = color or (0.09, 0.63, 0.52)
    ao(c, 0.0, 0.0, 1.0, 0.14, 0.45)
    for su in (-0.38, 0.38):
        c.ellipse(su, 0.035, 0.05, 0.035, (0.07, 0.07, 0.08), lift=0.3)
        c.ellipse(su, 0.03, 0.02, 0.018, (0.5, 0.5, 0.55), lift=0.3)
    # handle
    craft.arc(c, 0.0, 0.82, 0.19, 0.12, 0, 180, 0.04, (0.08, 0.08, 0.09), 1.0, steps=10)
    craft.arc(c, 0.0, 0.822, 0.19, 0.12, 40, 140, 0.012, (0.45, 0.45, 0.5), 0.8, steps=6)
    _rr(c, -0.50, 0.07, 0.50, 0.82, mix(col, WHITE, 0.30), scale(col, 0.52), 0.07)
    _rr(c, -0.50, 0.77, 0.50, 0.82, mix(col, WHITE, 0.50), mix(col, WHITE, 0.3), 0.03, 0.8)
    for ru in (-0.34, -0.17, 0.0, 0.17, 0.34):                          # vertical ribs
        c.line(ru, 0.13, ru, 0.74, 0.016, scale(col, 0.62), 0.8)
        c.line(ru - 0.008, 0.13, ru - 0.008, 0.74, 0.004, mix(col, WHITE, 0.5), 0.7)
    _hfill(c, -0.50, 0.40, 0.50, 0.47, lambda t: mix(scale((0.50, 0.30, 0.16), 1.15), scale((0.35, 0.2, 0.1), 0.8), t), strips=4)
    for cu in (-0.50, 0.50):                                            # corner guards
        for cv_ in (0.07, 0.82):
            c.ellipse(cu * 0.97, cv_ + (0.03 if cv_ < 0.5 else -0.03), 0.06, 0.06, mix(BRASS, WHITE, 0.15), lift=0.25)
    _rr(c, -0.07, 0.395, 0.07, 0.475, BRASS, scale(BRASS, 0.6), 0.015)
    _rr(c, -0.045, 0.41, 0.045, 0.46, (0.2, 0.12, 0.06), (0.1, 0.06, 0.03), 0.01)
    for lu in (-0.26, 0.26):                                            # latches
        _rr(c, lu - 0.05, 0.60, lu + 0.05, 0.69, mix(BRASS, WHITE, 0.2), scale(BRASS, 0.55), 0.015)
        c.ellipse(lu, 0.645, 0.012, 0.012, (0.2, 0.15, 0.1), lift=0.2)
    # stickers
    for (u, v, sc, k) in ((-0.30, 0.58, 0.055, 0), (0.28, 0.25, 0.05, 1), (-0.20, 0.25, 0.045, 2), (0.38, 0.55, 0.04, 3)):
        stc = [(0.98, 0.78, 0.2), (0.95, 0.35, 0.35), (0.98, 0.98, 0.95), (0.3, 0.55, 0.9)][k]
        c.ellipse(u, v, sc, sc, stc, lift=0.1)
        c.ellipse(u, v, sc * 0.65, sc * 0.65, mix(stc, (0.1, 0.1, 0.2), 0.45), lift=0.0, alpha=0.8)
        c.line(u - sc * 0.5, v - sc * 0.2, u + sc * 0.5, v + sc * 0.2, sc * 0.18, WHITE, 0.9)
    gloss(c, -0.28, 0.66, 0.10, 0.28, 90, 0.35)
    soft_disc(c, 0.32, 0.30, 0.25, 0.40, BLACK, 0.18, 1.2)


@sprop("auto_toy_plane", aspect=1.6, fill=0.62)
def auto_toy_plane(c, color):
    """Model airliner on a desk stand: white fuselage, accent tail and stripe, swept wing with an engine."""
    rng = c.rng
    acc = color or (0.09, 0.63, 0.52)
    ao(c, 0.0, 0.0, 0.8, 0.10, 0.4)
    c.ellipse(0.0, 0.015, 0.20, 0.20 * TILT, (0.18, 0.18, 0.2), lift=0.2)
    c.line(0.0, 0.03, 0.0, 0.30, 0.03, (0.75, 0.77, 0.82))
    fv = 0.46
    # far wing, fuselage, tail
    _poly(c, [(-0.05, fv + 0.04), (0.24, fv + 0.20), (0.32, fv + 0.20), (0.12, fv + 0.02)], (0.78, 0.80, 0.85), (0.6, 0.62, 0.68))
    _poly(c, [(-0.62, fv + 0.04), (-0.78, fv + 0.30), (-0.66, fv + 0.30), (-0.44, fv + 0.08)], mix(acc, WHITE, 0.2), scale(acc, 0.6))     # tail fin
    c.ellipse(-0.02, fv, 0.78, 0.115, (0.78, 0.80, 0.86), lift=0.0)
    c.ellipse(-0.02, fv + 0.008, 0.77, 0.105, (0.99, 0.99, 1.0), lift=0.22)
    _poly(c, [(-0.76, fv - 0.01), (0.70, fv - 0.03), (0.74, fv - 0.06), (-0.70, fv - 0.04)], acc, scale(acc, 0.7))                         # cheat line
    c.ellipse(0.64, fv + 0.012, 0.15, 0.085, (0.98, 0.98, 1.0), lift=0.1)
    c.ellipse(0.69, fv + 0.045, 0.06, 0.035, (0.25, 0.4, 0.55), lift=0.3)                                                          # cockpit
    for k in range(13):
        c.ellipse(0.50 - k * 0.075, fv + 0.025, 0.015, 0.018, (0.20, 0.30, 0.42), lift=0.2)
    # near wing with an engine, towards the viewer
    _poly(c, [(-0.15, fv - 0.03), (0.18, fv - 0.04), (-0.18, fv - 0.30), (-0.34, fv - 0.30)], (0.93, 0.94, 0.97), (0.68, 0.70, 0.76))
    c.ellipse(0.0, fv - 0.17, 0.085, 0.045, (0.80, 0.82, 0.88), lift=0.2)
    c.ellipse(0.062, fv - 0.17, 0.016, 0.036, (0.22, 0.24, 0.3), lift=0.0)
    gloss(c, -0.2, fv + 0.07, 0.4, 0.02, 0, 0.6)


@sprop("auto_travel_map", aspect=2.6, fill=0.36)
def auto_travel_map(c, color):
    """Folded paper map lying on the desk with continents, a dashed route and a standing pin."""
    rng = c.rng
    acc = color or (0.09, 0.63, 0.52)
    quad = [(-0.95, 0.04), (0.88, 0.0), (0.97, 0.30), (-0.88, 0.34)]
    ao(c, 0.0, 0.14, 1.9, 0.30, 0.25)
    _poly(c, [(u, v - 0.015) for u, v in quad], (0.55, 0.55, 0.55), None, 0.5)
    _poly(c, quad, (0.82, 0.92, 0.95), (0.62, 0.80, 0.88))
    for (u, v, a, b, col) in ((-0.55, 0.20, 0.30, 0.07, (0.78, 0.84, 0.58)), (-0.12, 0.16, 0.20, 0.06, (0.84, 0.80, 0.60)),
                              (0.30, 0.20, 0.30, 0.07, (0.72, 0.84, 0.58)), (0.70, 0.12, 0.12, 0.05, (0.80, 0.84, 0.62))):
        c.ellipse(u, v, a, b, col, lift=0.1, angle=rng.uniform(-8, 8))
    for k in (-1, 0, 1):                                                      # folds
        c.line(k * 0.62 - 0.03, 0.03 + (0.01 if k else 0.0), k * 0.62 + 0.0, 0.33, 0.006, (0.25, 0.35, 0.4), 0.30)
        c.line(k * 0.62 - 0.015, 0.03, k * 0.62 + 0.015, 0.33, 0.005, WHITE, 0.35)
    for u in (-0.35, -0.2, -0.05, 0.1, 0.25, 0.4, 0.55):                       # dashed route
        w = 0.08
        v = 0.17 + math.sin(u * 4.0) * 0.045
        c.line(u, v, u + w, v + math.cos(u * 4.0) * 0.018, 0.012, (0.88, 0.22, 0.20), 0.95)
    c.ellipse(-0.42, 0.19, 0.022, 0.012, (0.88, 0.22, 0.20), lift=0.1)
    # standing pin
    c.ellipse(0.63, 0.15, 0.03, 0.012, BLACK, lift=0.0, alpha=0.35)
    c.line(0.63, 0.15, 0.63, 0.25, 0.008, (0.7, 0.7, 0.72))
    c.ellipse(0.63, 0.30, 0.06, 0.06, acc, lift=0.25)
    c.ellipse(0.63, 0.30, 0.026, 0.026, WHITE, lift=0.0, alpha=0.95)
    gloss(c, 0.61, 0.32, 0.03, 0.02, 40, 0.8)


@sprop("auto_passport", aspect=2.2, fill=0.28)
def auto_passport(c, color):
    """A passport with a boarding pass tucked in: foreshortened as they lie on the desk."""
    rng = c.rng
    acc = color or (0.09, 0.63, 0.52)
    ao(c, 0.0, 0.0, 1.6, 0.20, 0.3)
    # boarding pass behind (tilted)
    bp = [(0.05, 0.02), (0.95, 0.06), (0.92, 0.21), (0.0, 0.17)]
    _poly(c, [(u, v - 0.012) for u, v in bp], (0.4, 0.4, 0.4), None, 0.4)
    _poly(c, bp, (0.99, 0.99, 0.98), (0.88, 0.89, 0.9))
    _poly(c, [(0.05, 0.145), (0.94, 0.19), (0.92, 0.21), (0.0, 0.17)], acc, scale(acc, 0.8))
    for k in range(6):
        c.line(0.12 + k * 0.01, 0.10 - k * 0.012 + 0.012, 0.52 + (k % 2) * 0.1, 0.12 - k * 0.012 + 0.015, 0.008, (0.55, 0.57, 0.62), 0.7)
    for k in range(18):
        c.line(0.64 + k * 0.012, 0.045 + k * 0.001, 0.64 + k * 0.012, 0.115 + k * 0.001, 0.004 + (k % 3) * 0.002, (0.1, 0.1, 0.12), 0.9)
    # passport
    q = [(-0.85, 0.01), (-0.05, 0.0), (0.0, 0.27), (-0.9, 0.29)]
    _poly(c, [(u, v - 0.02) for u, v in q], (0.9, 0.88, 0.8), (0.75, 0.73, 0.66))
    _poly(c, q, mix(acc, WHITE, 0.1), scale(acc, 0.55))
    c.ellipse(-0.47, 0.145, 0.095, 0.075, GOLD, lift=0.2, alpha=0.9)
    c.ellipse(-0.47, 0.145, 0.075, 0.058, mix(acc, (0, 0, 0), 0.3), lift=0.0)
    craft.arc(c, -0.47, 0.145, 0.045, 0.034, 20, 340, 0.008, GOLD, 0.95, steps=10)
    c.line(-0.80, 0.26, -0.15, 0.25, 0.012, GOLD, 0.8)
    gloss(c, -0.6, 0.24, 0.2, 0.02, 3, 0.4)


def _cloud(S, u, v, s, alpha=0.9):
    for du, dv, r in ((0.0, 0.0, 1.0), (0.9, 0.12, 0.8), (-0.9, 0.1, 0.75), (0.4, -0.2, 0.9), (-0.4, -0.15, 0.85)):
        S.circle(u + du * s * 0.5, v + dv * s * 0.3, r * s * 0.3, (1.0, 1.0, 1.0), alpha=alpha, lift=0.03)


@niche("travel-agency", "Travel agency", subjects=("auto_globe", "auto_suitcase"),
       strong=("travel agency", "tour", "holiday", "vacation", "tourism", "flights", "trip", "tour operator", "travel agent", "tour packages",
               "visa and tickets", "holiday packages", "plane tickets", "tourists", "यात्रा", "टूर", "ट्रैवल एजेंसी", "टूर एंड ट्रैवल्स", "ghumne"),
       weak=("travel", "ticket", "visa", "passport", "hotel booking", "cruise", "honeymoon", "itinerary", "sightseeing", "suitcases", "पर्यटक"), accent="#16a085", mood="light", group="travel")
def travel(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        # world map poster
        S.rect(0.55, 0.28, 0.80, 0.46, (0.97, 0.97, 0.95) if not dk else (0.2, 0.2, 0.22), lift=0.05)
        S.rect(0.55, 0.28, 0.74, 0.40, mix(P.accent_light, (0.7, 0.88, 0.95), 0.5) if not dk else (0.12, 0.3, 0.35), lift=0.0)
        for (u, v, a, b, ang) in ((0.38, 0.22, 0.12, 0.07, 20), (0.50, 0.38, 0.06, 0.10, -10), (0.62, 0.24, 0.10, 0.08, 0), (0.78, 0.30, 0.07, 0.06, 30),
                                  (0.33, 0.34, 0.05, 0.08, 10), (0.70, 0.40, 0.05, 0.04, 0)):
            S.ellipse(u, v, a, b, mix(P.accent, WHITE, 0.62) if not dk else scale(P.accent, 0.5), angle=ang, lift=0.0)
        # window with sky, clouds and a distant palm
        S.window(1.75, 0.25, 0.60, 0.36, bars=True)
        _cloud(S, 1.62, 0.20, 0.22)
        _cloud(S, 1.88, 0.30, 0.18)
        S.rect(1.45, 0.25, 0.012, 0.30, (0.4, 0.3, 0.2), lift=0.0)
        # shelf with a small plant and bokeh
        S.rect(1.15, 0.40, 0.34, 0.012, scale(P.wall_bot, 0.55), lift=0.0)
        S.pendant(1.0, -0.1, 0.12, color=mix(P.accent_light, (1.0, 0.85, 0.5), 0.5))
        S.bokeh(8, 0.1, 0.08, 2.0, 0.45, [(1.0, 1.0, 1.0), P.accent_light], 0.01, 0.03, 0.25)
        S.wood(-3.0, 0.58, 5.0, 2.6, mix(P.surface, (0.95, 0.88, 0.76), 0.35), plank=0.18, grain=0.0)
        S.soft(1.1, 0.74, 1.2, 0.2, (1.0, 0.97, 0.9), 0.45, 1.3, add=True)
    S.wood(-1.6, 0.60, 3.6, 2.6, mix(P.surface, (0.95, 0.88, 0.76), 0.35), plank=0.14, grain=0.25)
    S.rect(1.0, 0.60, 3.2, 0.008, scale(P.surface, 0.5), lift=0.0)
    S.soft(1.1, 0.80, 0.9, 0.16, (1.0, 0.97, 0.88), 0.30, 1.4, add=True)
    S.put("auto_suitcase", 1.30, 0.84, 0.40, color=P.accent, subject=True, shadow_alpha=0.35)
    S.put("auto_globe", 0.80, 0.86, 0.46, subject=True, shadow_alpha=0.35)
    S.put("auto_toy_plane", 1.74, 0.89, 0.20, color=P.accent, shadow_alpha=0.3)
    S.put("auto_travel_map", 1.20, 1.02, 0.20, color=P.accent, shadow_alpha=0.25)
    S.put("auto_passport", 0.70, 1.05, 0.13, color=P.accent, shadow=False)
    S.focus("detail", 0.85, 0.66)
    with S.near(blur=18):
        for k in range(7):                                                                   # blurred palm frond in the top corner
            ang = 200 + k * 18
            S.soft(1.78 + math.cos(math.radians(ang)) * 0.12 * (k % 3 + 1) * 0.5, 0.06 + math.sin(math.radians(ang)) * 0.06 * (k + 1) * 0.4, 0.22, 0.032,
                   (0.13, 0.45, 0.25), 0.75, 1.0, angle=ang - 180)
        S.soft(0.45, 1.02, 0.18, 0.08, P.accent, 0.35, 1.1)


# ====================================================================================== logistics
CARD = (0.80, 0.60, 0.36)


def _box(c, rng, u0, v0, u1, v1, dx=0.085, dy=0.055, tone=1.0, label=True, tape=True, fragile=False):
    """A cardboard box in oblique view: front face, lit top and darker right side, tape, label with barcode, scuffs."""
    col = scale(CARD, tone)
    w, h = u1 - u0, v1 - v0
    _poly(c, [(u1, v0), (u1 + dx, v0 + dy), (u1 + dx, v1 + dy), (u1, v1)], scale(col, 0.74), scale(col, 0.58))                     # side
    _poly(c, [(u0, v1), (u1, v1), (u1 + dx, v1 + dy), (u0 + dx, v1 + dy)], mix(col, WHITE, 0.30), mix(col, WHITE, 0.12))             # top
    _rr(c, u0, v0, u1, v1, mix(col, WHITE, 0.10), scale(col, 0.80), 0.0)                                                           # front
    if tape:
        tu = (u0 + u1) / 2
        _rr(c, tu - 0.028, v0, tu + 0.028, v1, mix(col, (0.9, 0.75, 0.45), 0.5), mix(col, (0.9, 0.75, 0.45), 0.3), 0.0, 0.9)
        _poly(c, [(tu - 0.028, v1), (tu + 0.028, v1), (tu + 0.028 + dx, v1 + dy), (tu - 0.028 + dx, v1 + dy)], mix(col, (1.0, 0.9, 0.6), 0.55), None, 0.9)
        c.line(tu - 0.026, v0 + 0.01, tu - 0.026, v1 - 0.01, 0.004, WHITE, 0.35)
    if label and w > 0.3:
        lu = u0 + w * 0.18
        _rr(c, lu, v0 + h * 0.52, lu + 0.17, v0 + h * 0.80, (0.98, 0.98, 0.96), (0.88, 0.88, 0.86), 0.006)
        for k in range(16):
            c.line(lu + 0.012 + k * 0.0095, v0 + h * 0.54, lu + 0.012 + k * 0.0095, v0 + h * 0.62, 0.003 + (k % 3) * 0.002, (0.1, 0.1, 0.12), 0.9)
        c.line(lu + 0.012, v0 + h * 0.72, lu + 0.13, v0 + h * 0.72, 0.006, (0.45, 0.45, 0.5), 0.8)
        c.line(lu + 0.012, v0 + h * 0.67, lu + 0.09, v0 + h * 0.67, 0.005, (0.55, 0.55, 0.6), 0.8)
    if fragile:
        fu = u1 - w * 0.22
        c.ellipse(fu, v0 + h * 0.40, 0.04, 0.04, (0.85, 0.15, 0.12), lift=0.15)
        c.line(fu - 0.014, v0 + h * 0.40 - 0.012, fu + 0.014, v0 + h * 0.40 + 0.015, 0.008, WHITE, 0.95)
        c.line(fu + 0.014, v0 + h * 0.40 - 0.012, fu - 0.014, v0 + h * 0.40 + 0.015, 0.008, WHITE, 0.95)
    else:
        au = u1 - w * 0.2
        c.line(au, v0 + h * 0.18, au, v0 + h * 0.40, 0.007, (0.3, 0.2, 0.12), 0.7)
        c.line(au - 0.025, v0 + h * 0.34, au, v0 + h * 0.42, 0.007, (0.3, 0.2, 0.12), 0.7)
        c.line(au + 0.025, v0 + h * 0.34, au, v0 + h * 0.42, 0.007, (0.3, 0.2, 0.12), 0.7)
    for _ in range(3):                                                              # scuffs
        u = rng.uniform(u0 + 0.03, u1 - 0.03)
        v = rng.uniform(v0 + 0.02, v1 - 0.02)
        c.line(u, v, u + rng.uniform(0.02, 0.07), v + rng.uniform(-0.01, 0.01), 0.004, scale(col, 0.55), 0.35)
    c.line(u0 + 0.005, v1 - 0.004, u1 - 0.005, v1 - 0.004, 0.005, WHITE, 0.30)


@sprop("auto_pallet_boxes", aspect=1.15, fill=1.0)
def auto_pallet_boxes(c, color):
    """Cardboard cartons stacked on a wooden pallet and half wrapped in stretch film."""
    rng = c.rng
    ao(c, 0.04, 0.0, 1.2, 0.18, 0.5)
    wood = (0.66, 0.50, 0.30)
    for bu in (-0.50, 0.0, 0.50):                                      # pallet blocks and slats
        _rr(c, bu - 0.06, 0.012, bu + 0.06, 0.075, scale(wood, 0.8), scale(wood, 0.5), 0.005)
    _rr(c, -0.56, 0.005, 0.56, 0.02, scale(wood, 0.9), scale(wood, 0.5), 0.0)
    _rr(c, -0.56, 0.07, 0.56, 0.115, mix(wood, WHITE, 0.15), scale(wood, 0.7), 0.0)
    for k in range(8):
        c.line(-0.56 + k * 0.16, 0.072, -0.56 + k * 0.16, 0.112, 0.004, scale(wood, 0.45), 0.7)
    c.line(-0.56, 0.113, 0.56, 0.113, 0.004, mix(wood, WHITE, 0.5), 0.6)
    _box(c, rng, -0.54, 0.115, 0.04, 0.435, tone=1.0, fragile=False)
    _box(c, rng, 0.04, 0.115, 0.50, 0.375, tone=0.92, fragile=True)
    _box(c, rng, -0.46, 0.435, 0.06, 0.700, tone=1.05, fragile=True)
    _box(c, rng, 0.06, 0.375, 0.46, 0.585, tone=0.96)
    _box(c, rng, -0.34, 0.700, 0.12, 0.905, tone=0.98, label=False)
    # stretch film sheen on the lower layers
    _poly(c, [(-0.55, 0.12), (-0.30, 0.12), (-0.05, 0.62), (-0.30, 0.62)], WHITE, None, 0.10)
    _poly(c, [(0.12, 0.12), (0.22, 0.12), (0.42, 0.50), (0.32, 0.50)], WHITE, None, 0.12)
    soft_disc(c, -0.25, 0.30, 0.30, 0.20, WHITE, 0.10, 1.2, 0, True)


@sprop("auto_hand_truck", aspect=0.80, fill=1.0)
def auto_hand_truck(c, color):
    """Hand truck with a carton strapped on: slanted rails, toe plate, pneumatic wheel and a loop handle."""
    rng = c.rng
    acc = color or (0.83, 0.33, 0.0)
    ao(c, 0.1, 0.0, 0.8, 0.12, 0.45)
    lean = -0.17

    def at(v):
        return lean * (v - 0.12) / 0.8

    c.ellipse(0.02, 0.115, 0.115, 0.115, (0.04, 0.04, 0.05), lift=0.1)
    c.ellipse(0.02, 0.115, 0.075, 0.075, (0.5, 0.52, 0.58), lift=0.3)
    c.ellipse(0.02, 0.115, 0.03, 0.03, (0.15, 0.15, 0.18), lift=0.2)
    _poly(c, [(0.0, 0.07), (0.40, 0.065), (0.40, 0.095), (0.0, 0.12)], (0.65, 0.67, 0.72), (0.30, 0.31, 0.35))                        # toe plate
    # a carton leaning on the rails
    sh = lambda v: at(v) * 0.9                                           # noqa: E731
    box = [(0.05 + sh(0.12), 0.12), (0.40 + sh(0.12), 0.115), (0.40 + sh(0.46), 0.46), (0.05 + sh(0.46), 0.46)]
    _poly(c, box, mix(CARD, WHITE, 0.1), scale(CARD, 0.78))
    _poly(c, [(0.40 + sh(0.12), 0.115), (0.46 + sh(0.12), 0.15), (0.46 + sh(0.46), 0.50), (0.40 + sh(0.46), 0.46)], scale(CARD, 0.7), scale(CARD, 0.55))
    _poly(c, [(0.05 + sh(0.46), 0.46), (0.40 + sh(0.46), 0.46), (0.46 + sh(0.46), 0.50), (0.11 + sh(0.46), 0.50)], mix(CARD, WHITE, 0.3))
    _rr(c, 0.15 + sh(0.3), 0.26, 0.28 + sh(0.3), 0.37, (0.98, 0.98, 0.96), (0.88, 0.88, 0.86), 0.005)
    for k in range(9):
        c.line(0.165 + sh(0.3) + k * 0.011, 0.275, 0.165 + sh(0.3) + k * 0.011, 0.32, 0.004, (0.1, 0.1, 0.12), 0.9)
    # rails
    for off, tone in ((0.0, 0.8), (0.045, 1.0)):
        c.line(0.0 + off, 0.115, lean + off, 0.97, 0.028, scale(acc, tone * 0.7))
        c.line(0.0 + off - 0.007, 0.115, lean + off - 0.007, 0.97, 0.008, mix(acc, WHITE, 0.45), 0.7)
    for v in (0.50, 0.74):
        c.line(at(v) + 0.0, v, at(v) + 0.045, v, 0.02, scale(acc, 0.8))
    craft.arc(c, lean + 0.0225, 0.935, 0.0225, 0.07, 0, 180, 0.03, scale(acc, 0.7), 1.0, steps=6)
    c.line(lean - 0.10, 0.97, lean + 0.14, 0.97, 0.04, (0.09, 0.09, 0.10))
    c.line(lean - 0.095, 0.975, lean + 0.12, 0.975, 0.009, (0.5, 0.5, 0.55), 0.7)
    # strap
    c.line(0.04 + sh(0.38), 0.38, 0.38 + sh(0.38), 0.38, 0.014, (0.1, 0.1, 0.12), 0.95)
    _rr(c, 0.17 + sh(0.38), 0.37, 0.21 + sh(0.38), 0.395, mix(STEEL, WHITE, 0.3), scale(STEEL, 0.6), 0.004)


def _van_poly():
    return _smooth([(-1.20, 0.22), (-1.22, 0.40), (-1.22, 0.92), (-1.18, 0.98), (0.30, 0.99), (0.60, 0.97), (0.82, 0.70), (1.02, 0.62), (1.20, 0.55),
                    (1.24, 0.42), (1.22, 0.24), (1.05, 0.20), (-1.05, 0.20)], 3)


@sprop("auto_van", aspect=2.45, fill=1.0)
def auto_van(c, color):
    """Delivery van, side view: white cargo box with an accent stripe, cab, sliding door, wheels."""
    rng = c.rng
    acc = color or (0.83, 0.33, 0.0)
    white = (0.97, 0.97, 0.98)
    poly = _van_poly()
    for wu in (-0.78, 0.84):
        soft_disc(c, wu + 0.04, 0.0, 0.32, 0.06, BLACK, 0.7, 1.4)
    _poly(c, poly, white, (0.64, 0.66, 0.72))
    _poly(c, [(-1.22, 0.90), (0.60, 0.97), (0.60, 0.90), (-1.22, 0.84)], WHITE, None, 0.35, 0.0)
    for wu in (-0.78, 0.84):
        ar = 0.255
        pts = [(wu + ar * math.cos(math.radians(a)), 0.235 + ar * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        _poly(c, [(wu - ar, 0.18)] + pts + [(wu + ar, 0.18)], (0.05, 0.05, 0.06))
    # accent stripe and a parcel logo
    _poly(c, [(-1.22, 0.46), (0.62, 0.46), (0.74, 0.38), (1.14, 0.38), (1.14, 0.32), (0.76, 0.32), (0.66, 0.40), (-1.22, 0.40)], acc, scale(acc, 0.8))
    _rr(c, -1.22, 0.495, 0.50, 0.505, mix(acc, WHITE, 0.4), None, 0.0, 0.8)
    c.ellipse(-0.62, 0.70, 0.17, 0.17, acc, lift=0.2)
    _rr(c, -0.69, 0.64, -0.55, 0.75, (0.98, 0.9, 0.7), (0.85, 0.7, 0.45), 0.006)
    c.line(-0.62, 0.64, -0.62, 0.75, 0.01, acc, 0.8)
    _poly(c, [(-0.48, 0.68), (-0.40, 0.68), (-0.40, 0.72), (-0.48, 0.72)], WHITE, None, 0.0)
    # cab window, doors, handles
    _poly(c, [(0.40, 0.90), (0.60, 0.90), (0.78, 0.70), (0.40, 0.70)], (0.20, 0.30, 0.42), (0.08, 0.12, 0.20))
    _poly(c, [(0.46, 0.88), (0.54, 0.88), (0.62, 0.76), (0.50, 0.76)], WHITE, None, 0.16)
    c.line(0.33, 0.22, 0.33, 0.97, 0.007, (0.5, 0.52, 0.58), 0.8)
    c.line(-0.18, 0.22, -0.18, 0.97, 0.006, (0.5, 0.52, 0.58), 0.6)
    c.line(-1.20, 0.22, -1.20, 0.97, 0.007, (0.5, 0.52, 0.58), 0.5)
    _rr(c, 0.38, 0.62, 0.50, 0.645, (0.5, 0.52, 0.58), (0.3, 0.3, 0.34), 0.008)
    _rr(c, -0.12, 0.62, 0.0, 0.645, (0.5, 0.52, 0.58), (0.3, 0.3, 0.34), 0.008)
    _rr(c, 0.74, 0.74, 0.86, 0.84, (0.15, 0.16, 0.18), (0.08, 0.08, 0.1), 0.02)                      # mirror
    c.glow(1.22, 0.50, 0.28, (1.0, 0.96, 0.8), 0.35)
    _poly(c, [(1.10, 0.48), (1.24, 0.46), (1.22, 0.54), (1.10, 0.56)], (1.0, 0.98, 0.9), (0.85, 0.85, 0.88))
    _rr(c, -1.23, 0.55, -1.19, 0.72, (0.9, 0.1, 0.1), (0.6, 0.05, 0.05), 0.005)
    _rr(c, -1.18, 0.30, 1.14, 0.34, (0.2, 0.2, 0.22), (0.1, 0.1, 0.12), 0.01, 0.5)                    # bumpers / sill
    gloss(c, -0.2, 0.93, 0.7, 0.02, 0, 0.5)
    for wu in (-0.78, 0.84):
        _wheel(c, wu, 0.235, 0.215, rim=(0.75, 0.77, 0.82), spokes=6)


@sprop("auto_tape_gun", aspect=1.25, fill=0.42)
def auto_tape_gun(c, color):
    """Packing tape gun with a tape roll and the cutting blade."""
    acc = color or (0.83, 0.33, 0.0)
    ao(c, 0.0, 0.0, 1.0, 0.12, 0.4)
    _poly(c, [(0.05, 0.10), (0.30, 0.0), (0.42, 0.02), (0.22, 0.18)], (0.12, 0.12, 0.14), (0.05, 0.05, 0.06))
    c.ellipse(0.0, 0.24, 0.27, 0.27, scale(CARD, 0.5), lift=0.0)
    c.ellipse(0.0, 0.25, 0.26, 0.26, (0.90, 0.76, 0.48), lift=0.25)
    c.ellipse(0.0, 0.25, 0.20, 0.20, (0.80, 0.64, 0.38), lift=0.1)
    c.ellipse(0.0, 0.25, 0.10, 0.10, (0.28, 0.20, 0.12), lift=0.2)
    c.ellipse(0.0, 0.25, 0.062, 0.062, (0.08, 0.06, 0.04), lift=0.0)
    gloss(c, -0.1, 0.35, 0.12, 0.05, 30, 0.5)
    craft.arc(c, 0.0, 0.25, 0.30, 0.30, 100, 330, 0.05, acc, 1.0, steps=14)
    craft.arc(c, 0.0, 0.255, 0.30, 0.30, 110, 200, 0.012, mix(acc, WHITE, 0.5), 0.8, steps=6)
    _poly(c, [(0.26, 0.20), (0.62, 0.17), (0.62, 0.23), (0.28, 0.30)], mix(acc, WHITE, 0.1), scale(acc, 0.6))
    for k in range(7):
        c.line(0.60 + 0.0, 0.17 + k * 0.01, 0.66, 0.17 + k * 0.01, 0.006, (0.75, 0.77, 0.82), 0.9)


@sprop("auto_scanner", aspect=1.35, fill=0.55)
def auto_scanner(c, color):
    """Handheld barcode scanner with a red laser line pointing left."""
    rng = c.rng
    ao(c, 0.1, 0.0, 0.7, 0.10, 0.4)
    yel = (0.98, 0.78, 0.10)
    _poly(c, [(0.08, 0.20), (0.34, 0.20), (0.30, 0.02), (0.14, 0.02)], (0.20, 0.20, 0.22), (0.07, 0.07, 0.08))                       # grip
    c.line(0.20, 0.10, 0.26, 0.10, 0.012, (0.35, 0.35, 0.38), 0.7)
    _rr(c, -0.04, 0.20, 0.52, 0.46, mix(yel, WHITE, 0.15), scale(yel, 0.65), 0.07)                                                    # head
    _rr(c, -0.04, 0.20, 0.52, 0.28, (0.16, 0.16, 0.18), (0.07, 0.07, 0.08), 0.04, 0.9)
    _rr(c, -0.07, 0.27, 0.02, 0.43, (0.08, 0.04, 0.05), (0.04, 0.02, 0.03), 0.02)                                                     # window
    c.glow(-0.06, 0.35, 0.30, (1.0, 0.1, 0.08), 0.7)
    _poly(c, [(-0.07, 0.34), (-0.07, 0.36), (-0.90, 0.40), (-0.90, 0.30)], (1.0, 0.2, 0.15), None, 0.28, 0.02)
    c.line(-0.07, 0.35, -0.90, 0.35, 0.012, (1.0, 0.35, 0.3), 0.95)
    _rr(c, 0.18, 0.33, 0.30, 0.39, (0.3, 0.3, 0.34), (0.12, 0.12, 0.14), 0.01)
    gloss(c, 0.25, 0.44, 0.2, 0.02, 0, 0.5)


def _hazard_quad(S, u0, v0, u1, v1, u2, v2, u3, v3, col, alpha=0.85):
    """Painted floor outline: four thin quads along the edges of a perspective rectangle."""
    pts = [(u0, v0), (u1, v1), (u2, v2), (u3, v3)]
    for i in range(4):
        (a, b), (c_, d) = pts[i], pts[(i + 1) % 4]
        t = 0.010
        _spoly(S, [(a, b), (c_, d), (c_, d + t), (a, b + t)], col, None, alpha)


def _rack(S, u0, u1, v_top, v_bot, levels, col_beam, rng, boxes):
    for k in range(levels + 1):
        v = v_bot - (v_bot - v_top) * k / float(levels)
        S.rect((u0 + u1) / 2, v, u1 - u0, 0.012, col_beam, lift=0.0)
    for u in (u0, u1):
        S.rect(u, (v_top + v_bot) / 2, 0.014, v_bot - v_top, scale(col_beam, 0.8), lift=0.0)
    seg = (v_bot - v_top) / levels
    for k in range(levels):
        vb = v_bot - seg * k - 0.008
        uu = u0 + 0.02
        while uu < u1 - 0.05:
            wd = rng.uniform(0.04, 0.09)
            ht = rng.uniform(seg * 0.45, seg * 0.85)
            if rng.random() < 0.85:
                col = scale(CARD, rng.uniform(0.75, 1.12)) if rng.random() < 0.8 else rng.choice([(0.95, 0.95, 0.96), (0.35, 0.5, 0.75)])
                S.rect(uu + wd / 2, vb - ht / 2, wd, ht, col, lift=0.1)
            uu += wd + rng.uniform(0.005, 0.03)


@niche("logistics", "Logistics and courier", subjects=("auto_pallet_boxes", "auto_van"),
       strong=("logistics", "courier", "delivery", "cargo", "shipping", "warehouse", "transport", "freight", "packers and movers", "courier service",
               "parcel", "supply chain", "लॉजिस्टिक्स", "कूरियर", "ट्रांसपोर्ट", "गोदाम", "पैकर्स एंड मूवर्स"),
       weak=("goods", "dispatch", "fleet", "truck", "moving", "storage", "e commerce"), accent="#d35400", mood="light", group="auto")
def logistics(S):
    P = S.pal
    dk = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.64)
        S.rect(1.0, 0.08, 7.0, 0.16, scale(P.wall_top, 0.82), lift=0.0, alpha=0.5)
        # tall storage racks full of cartons, an open roller door with daylight, hanging lamps
        _rack(S, 0.0, 0.62, 0.10, 0.62, 3, P.accent, rng, True)
        _rack(S, 1.62, 2.30, 0.10, 0.62, 3, P.accent, rng, True)
        _rack(S, -0.90, -0.30, 0.10, 0.62, 3, P.accent, rng, True)
        S.gradient_rect(0.78, 0.14, 1.46, 0.62, (0.55, 0.62, 0.70) if not dk else (0.06, 0.08, 0.12), (0.95, 0.97, 1.0) if not dk else (0.3, 0.34, 0.4))
        for k in range(5):
            S.rect(1.12, 0.10 + k * 0.04, 0.68, 0.006, scale(P.wall_bot, 0.65), lift=0.0, alpha=0.8)
        S.glow(1.12, 0.40, 0.7, (1.0, 0.98, 0.9), 0.4 if not dk else 0.35)
        S.rect(1.12, 0.63, 0.74, 0.016, scale(P.accent, 0.85), lift=0.0)
        for ul in (0.3, 0.9, 1.5, 2.1):
            S.line(ul, -0.1, ul, 0.07, 0.003, scale(P.wall_bot, 0.4))
            S.poly([(ul - 0.07, 0.12), (ul + 0.07, 0.12), (ul + 0.03, 0.06), (ul - 0.03, 0.06)], P.accent if not dk else scale(P.accent, 0.9))
            S.glow(ul, 0.13, 0.36, (1.0, 0.95, 0.82), 0.65 if dk else 0.30)
        S.bokeh(6, 0.1, 0.1, 2.0, 0.5, [(1.0, 1.0, 1.0)], 0.01, 0.03, 0.2)
        S.floor(0.64, mix(P.floor_top, (0.66, 0.66, 0.68), 0.7), mix(P.floor_bot, (0.46, 0.46, 0.5), 0.7))
        S.rect(1.0, 0.655, 7, 0.012, (0.95, 0.76, 0.1), lift=0.0, alpha=0.9)
        S.soft(1.12, 0.82, 1.1, 0.2, (1.0, 0.97, 0.9), 0.45 if not dk else 0.5, 1.3, add=True)
    for k in range(-5, 12):
        _shair(S, 0.2 + k * 0.40, 0.66, 0.2 + k * 0.40 - 0.9 + k * 0.15, 1.5, (0.0, 0.0, 0.0), 0.08)
    for vv in (0.74, 0.90, 1.10, 1.35):
        _shair(S, -2, vv, 4, vv, (0.0, 0.0, 0.0), 0.08)
    _hazard_quad(S, 0.64, 0.97, 1.30, 0.97, 1.38, 1.07, 0.54, 1.07, (0.96, 0.78, 0.10))
    S.put("auto_van", 1.52, 0.78, 0.30, color=P.accent, shadow_alpha=0.3)
    S.mark_subject("auto_van", 1.22, 0.48, 1.82, 0.78)
    S.put("auto_pallet_boxes", 0.88, 1.00, 0.46, shadow_alpha=0.4)
    S.mark_subject("auto_pallet_boxes", 0.60, 0.54, 1.15, 1.0)
    S.put("auto_hand_truck", 1.30, 1.04, 0.34, color=P.accent, shadow_alpha=0.35)
    S.put("auto_scanner", 1.56, 1.06, 0.10, shadow_alpha=0.3)
    S.put("auto_tape_gun", 1.70, 1.04, 0.09, color=P.accent, shadow_alpha=0.3)
    S.focus("detail", 0.88, 0.76)
    with S.near(blur=18):
        S.soft(0.50, 1.04, 0.16, 0.08, P.accent, 0.30, 1.1)
        S.soft(1.78, 0.25, 0.22, 0.18, (1.0, 0.95, 0.8), 0.20, 1.2, add=True)
