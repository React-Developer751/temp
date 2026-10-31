"""More service niches: pest control, laundry and dry cleaning, water purifier service, scrap and recycling, funeral services, notary."""
import math

from ..craft import BLACK, TILT, WHITE, arc, disc, gloss, hshade_box, soft_disc
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale

METAL = (0.76, 0.78, 0.81)
STEEL = (0.66, 0.69, 0.74)
WOOD = (0.72, 0.52, 0.32)
YELLOW = (0.97, 0.76, 0.16)
BRASS = (0.84, 0.64, 0.26)


# ====================================================================================================== shared helpers
def _rot(pts, ang, ox=0.0, oy=0.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(ox + x * ca - y * sa, oy + x * sa + y * ca) for x, y in pts]


def _tube(c, u0, v0, u1, v1, w, base, hl=0.6):
    """A shiny tube between two points: dark body, lit core shifted to the key light, thin highlight."""
    c.line(u0, v0, u1, v1, w, scale(base, 0.58))
    c.line(u0 - w * 0.10, v0 + w * 0.12, u1 - w * 0.10, v1 + w * 0.12, w * 0.66, base)
    c.line(u0 - w * 0.20, v0 + w * 0.24, u1 - w * 0.20, v1 + w * 0.24, w * 0.18, mix(base, WHITE, hl), 0.85)


def _bead(c, u, v, r, col):
    c.ellipse(u, v, r, r * 0.95, col, lift=0.18)
    soft_disc(c, u - r * 0.3, v + r * 0.3, r * 0.45, r * 0.35, WHITE, 0.7, 1.0, add=True)


def _prism(c, u, v, w, h, dx, dy, front, top=None, side=None, lift=0.07, r=0.0):
    """Oblique box: front face w x h with its base centre at (u, v); depth goes right and up by (dx, dy)."""
    x0, x1 = u - w / 2, u + w / 2
    top = top or mix(front, WHITE, 0.22)
    side = side or scale(front, 0.66)
    _qpoly(c, [(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], side, lift)
    _qpoly(c, [(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, 0.04)
    c.rect(u, v + h / 2, w, h, front, lift=lift, r=r)


def _cyl(c, u, v, r, h, base, top=None, dark=0.55, lip=True):
    """Upright cylinder: lit left side, dark right side, top ellipse, highlight."""
    c.ellipse(u, v, r, r * TILT, scale(base, dark * 0.8), lift=0)
    hshade_box(c, u, v + h / 2, 2 * r, h, mix(base, WHITE, 0.14), scale(base, dark))
    disc(c, u, v + h, r, top or scale(base, 1.06), TILT, 0.06, rim=lip)
    gloss(c, u - r * 0.52, v + h * 0.5, r * 0.07, h * 0.40, 0, 0.45)


# ---- cheap curve and scan-line polygon helpers (the stage's SDF path / polygon grow with the bounding box)
def _catmull(pts, n=5):
    out = []
    m = len(pts)
    for i in range(m - 1):
        p0, p1, p2 = pts[max(0, i - 1)], pts[i], pts[i + 1]
        p3 = pts[min(m - 1, i + 2)]
        for k in range(n):
            t = k / float(n)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                             for j in (0, 1)))
    out.append(pts[-1])
    return out


def _path(c, pts, w, col, alpha=1.0):
    """A smooth stroke of width w drawn as short capsules (cheap, unlike Ctx.path)."""
    pts = _catmull(list(pts)) if len(pts) > 2 else list(pts)
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], w, col, alpha)


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


def _scan(cv, pts, top, bot, alpha=1.0):
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
        for k in range(0, len(xs) - 1, 2):
            _span(cv.px, cv.w, y, xs[k], xs[k + 1], col, alpha)


def _qpoly(c, pts, color, lift=0.10, alpha=1.0):
    """Polygon in unit coordinates, scan-line filled with a vertical shade (fast for rotated sheets and long faces)."""
    _scan(c.cv, [(c.X(u), c.Y(v)) for u, v in pts], scale(color, 1 + lift), scale(color, 1 - lift * 1.2), alpha)


def _leaf(c, u, v, length, angle, color, width=0.45):
    """A pointed leaf / petal with a midrib (scan-line filled); angle in degrees, 0 = pointing right."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = [(t * length, math.sin(math.pi * t) ** 0.8 * wd) for t in (i / 6.0 for i in range(7))]
    outline = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    _qpoly(c, [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in outline], color, 0.15)
    c.line(u, v, u + length * 0.9 * ca, v + length * 0.9 * sa, length * 0.04, scale(color, 0.72), 0.6)


def _hue_shift(P, base, amount):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*base)
    return colorsys.hsv_to_rgb((h + amount) % 1.0, s, v)


def _bars(c, u, v, w, n, col, gap=0.028, th=0.009, alpha=0.5):
    """Plain grey bars standing in for printed lines (never text)."""
    for k in range(n):
        ww = w * (0.55 + 0.45 * ((k * 7) % 5) / 4.0) if k < n - 1 else w * 0.5
        c.rect(u - (w - ww) / 2, v - k * gap, ww, th, col, lift=0, alpha=alpha)


# ====================================================================================================== pest control
@sprop("svc_pest_sprayer", aspect=1.28, fill=0.99)
def svc_pest_sprayer(c, P):
    """Pressure sprayer: blue tank with a level window, pump handle, hose, trigger grip and lance with a misting nozzle."""
    c = c.sub(-0.05, 0.0, 1.0)
    rng = c.rng
    acc = P.accent
    T = -0.25                                                    # tank centre
    # tank
    c.ellipse(T, 0.02, 0.29, 0.29 * TILT, scale(acc, 0.40), lift=0)
    hshade_box(c, T, 0.35, 0.58, 0.66, mix(acc, WHITE, 0.22), scale(acc, 0.46), r=0.04)
    c.rect(T - 0.20, 0.36, 0.05, 0.60, mix(acc, WHITE, 0.55), lift=0, alpha=0.5, r=0.02)           # broad highlight
    c.rect(T, 0.045, 0.58, 0.05, scale(acc, 0.50), lift=0, alpha=0.55)                             # foot ring
    # level window and a plain label band (bars, no text)
    c.rect(T + 0.10, 0.35, 0.075, 0.50, (0.94, 0.97, 1.0), r=0.03, lift=0.05, alpha=0.9)
    c.rect(T + 0.10, 0.26, 0.075, 0.28, mix(acc, (0.45, 0.8, 0.95), 0.55), r=0.02, lift=0.1)
    for k in range(7):
        c.rect(T + 0.065, 0.12 + k * 0.07, 0.030, 0.007, scale(acc, 0.45), lift=0, alpha=0.8)
    c.rect(T - 0.08, 0.43, 0.30, 0.20, (0.95, 0.96, 0.97), r=0.02, lift=0.04)
    c.rect(T - 0.08, 0.50, 0.30, 0.05, YELLOW, lift=0.1)
    _bars(c, T - 0.08, 0.44, 0.24, 3, (0.35, 0.38, 0.45), gap=0.045, th=0.014, alpha=0.7)
    soft_disc(c, T + 0.26, 0.35, 0.12, 0.40, BLACK, 0.24, 1.3)
    # shoulder, neck and the pump
    c.ellipse(T, 0.68, 0.29, 0.29 * TILT, scale(acc, 0.70), lift=0)
    c.rect(T, 0.675, 0.58, 0.02, scale(acc, 0.72), lift=0)
    disc(c, T, 0.69, 0.285, mix(acc, WHITE, 0.16), TILT, 0.10, rim=False)
    c.ellipse(T, 0.70, 0.16, 0.16 * TILT, scale(acc, 0.55), lift=0)
    _cyl(c, T, 0.70, 0.115, 0.12, (0.14, 0.15, 0.18), dark=0.5)
    c.rect(T, 0.88, 0.05, 0.16, METAL, lift=0.2)                                                   # piston rod
    c.line(T - 0.01, 0.80, T - 0.01, 0.95, 0.008, WHITE, 0.6)
    c.rect(T, 0.965, 0.46, 0.05, YELLOW, r=0.025, lift=0.18)                                       # T handle
    c.rect(T - 0.05, 0.978, 0.30, 0.012, mix(YELLOW, WHITE, 0.55), lift=0, alpha=0.8)
    # shoulder strap loop
    arc(c, T - 0.27, 0.55, 0.06, 0.20, 90, 270, 0.020, (0.14, 0.15, 0.18), 1.0, 8)
    # hose, trigger grip and the lance leaning against the tank with its nozzle on the floor
    hose = (0.08, 0.10, 0.12)
    pts = [(T + 0.28, 0.20), (T + 0.46, 0.09), (T + 0.60, 0.20), (T + 0.56, 0.42), (T + 0.50, 0.56)]
    _path(c, pts, 0.034, scale(hose, 0.6), 1.0)
    _path(c, [(x - 0.004, y + 0.005) for x, y in pts], 0.022, hose, 1.0)
    _path(c, [(x - 0.009, y + 0.010) for x, y in pts], 0.006, mix(hose, WHITE, 0.4), 0.8)
    gx, gy = T + 0.50, 0.56
    c.poly([(gx - 0.05, gy + 0.03), (gx + 0.07, gy + 0.04), (gx + 0.09, gy - 0.03), (gx + 0.03, gy - 0.13), (gx - 0.04, gy - 0.10)], (0.17, 0.18, 0.22), lift=0.2)
    c.poly([(gx - 0.02, gy + 0.02), (gx + 0.06, gy + 0.03), (gx + 0.06, gy - 0.01), (gx - 0.01, gy - 0.01)], YELLOW, lift=0.15)
    c.line(gx + 0.03, gy - 0.07, gx, gy - 0.13, 0.014, YELLOW)                                      # trigger
    nx, ny = T + 0.74, 0.07
    _tube(c, gx + 0.06, gy + 0.02, nx, ny + 0.03, 0.028, METAL, 0.75)
    c.poly(_rot([(0.0, -0.032), (0.0, 0.032), (0.06, 0.02), (0.06, -0.02)], -80, nx, ny + 0.05), (0.15, 0.16, 0.19), lift=0.2)
    for k in range(7):                                                                              # mist
        t = k / 6.0
        soft_disc(c, nx + 0.02 + t * 0.10, ny - 0.015 + t * 0.01, 0.03 + t * 0.06, 0.02 + t * 0.04, mix(WHITE, P.accent_light, 0.3), 0.55 * (1 - t) ** 0.8 + 0.06, 1.2)
    for _ in range(10):
        c.circle(nx + 0.04 + rng.uniform(0.0, 0.16), ny + rng.uniform(-0.05, 0.03), rng.uniform(0.003, 0.006), mix(WHITE, P.accent_light, 0.4), lift=0, alpha=0.85)


@sprop("svc_pest_fogger", aspect=1.84, fill=0.79)
def svc_pest_fogger(c, P):
    """Thermal fogging machine on a frame: yellow tank, dark engine, long barrel and a drifting cloud of fog."""
    c = c.sub(-0.27, 0.0, 1.0)
    rng = c.rng
    dark = (0.13, 0.14, 0.17)
    # frame with feet
    c.rect(-0.05, 0.02, 0.80, 0.03, dark, r=0.012, lift=0.2)
    for x in (-0.38, 0.28):
        c.rect(x, 0.12, 0.035, 0.22, dark, lift=0.2)
        c.rect(x, 0.015, 0.09, 0.03, (0.07, 0.07, 0.09), r=0.012, lift=0)
    # yellow tank, engine and the barrel
    c.rect(-0.14, 0.38, 0.56, 0.32, scale(YELLOW, 0.60), r=0.10, lift=0.1)
    c.rect(-0.16, 0.395, 0.54, 0.30, YELLOW, r=0.095, lift=0.20)
    c.rect(-0.18, 0.50, 0.44, 0.04, mix(YELLOW, WHITE, 0.6), lift=0, alpha=0.75, r=0.02)
    c.rect(-0.14, 0.27, 0.52, 0.025, scale(YELLOW, 0.60), lift=0, alpha=0.7)
    c.rect(-0.28, 0.40, 0.18, 0.12, dark, r=0.012, lift=0.1)
    _bars(c, -0.28, 0.43, 0.12, 3, mix(dark, WHITE, 0.55), gap=0.032, th=0.012, alpha=0.9)
    c.circle(-0.37, 0.58, 0.04, (0.86, 0.2, 0.14), lift=0.25)
    c.circle(-0.38, 0.595, 0.014, WHITE, lift=0, alpha=0.7)
    c.rect(0.28, 0.40, 0.24, 0.26, scale(P.accent_dark, 0.7), r=0.04, lift=0.22)
    for k in range(5):
        c.rect(0.28, 0.30 + k * 0.045, 0.20, 0.010, scale(P.accent_dark, 1.3), lift=0, alpha=0.8)
    _tube(c, 0.38, 0.45, 0.78, 0.56, 0.085, (0.30, 0.32, 0.38), 0.55)
    c.ellipse(0.80, 0.565, 0.028, 0.050, (0.05, 0.05, 0.07), lift=0)
    arc(c, -0.14, 0.62, 0.22, 0.15, 20, 160, 0.034, dark, 1.0, 12)                                  # carrying handle
    # fog
    for k in range(20):
        t = k / 19.0
        x = 0.84 + t * 0.55 + rng.uniform(-0.03, 0.03)
        y = 0.58 + t * 0.20 + math.sin(t * 5.0) * 0.04 + rng.uniform(-0.03, 0.03)
        r = 0.05 + t * 0.15
        soft_disc(c, x, y - r * 0.2, r, r * 0.85, (0.74, 0.78, 0.84), 0.40 * (1 - t * 0.6), 1.1)
        soft_disc(c, x - r * 0.12, y + r * 0.12, r * 0.8, r * 0.7, WHITE, 0.62 * (1 - t) + 0.10, 1.2)


@sprop("svc_pest_trap", aspect=3.54, fill=0.37)
def svc_pest_trap(c, P):
    """A wooden snap trap with its spring and bait next to a black bait station box."""
    c = c.sub(-0.04, 0.0, 1.0)
    rng = c.rng
    # bait station (back right)
    _prism(c, 0.34, 0.02, 0.50, 0.22, 0.10, 0.07, (0.16, 0.17, 0.20), top=(0.26, 0.28, 0.32), r=0.012)
    c.ellipse(0.34, 0.10, 0.065, 0.075, (0.02, 0.02, 0.03), lift=0)
    c.arc(0.34, 0.10, 0.07, 20, 160, 0.012, (0.4, 0.42, 0.48), 0.8, 0.08)
    c.rect(0.34, 0.205, 0.40, 0.012, (0.40, 0.42, 0.48), lift=0, alpha=0.8)
    c.rect(0.34, 0.2, 0.50, 0.02, YELLOW, lift=0.1, alpha=0.9)
    # trap base plate
    _prism(c, -0.30, 0.0, 0.62, 0.05, 0.08, 0.05, WOOD, r=0.006)
    for k in range(10):
        c.line(-0.58 + rng.uniform(0, 0.55), 0.02 + rng.uniform(0, 0.02), -0.50 + rng.uniform(0, 0.55), 0.03, 0.002, scale(WOOD, 0.7), 0.5)
    # spring coil and the hammer wire
    for k in range(4):
        c.ellipse(-0.50 + k * 0.022, 0.095, 0.022, 0.032, STEEL, lift=0.2)
        c.ellipse(-0.50 + k * 0.022, 0.097, 0.012, 0.02, scale(WOOD, 0.6), lift=0, alpha=0.8)
    c.line(-0.46, 0.10, -0.46, 0.34, 0.012, STEEL)
    c.line(-0.46, 0.34, -0.12, 0.36, 0.012, STEEL)
    c.line(-0.12, 0.36, -0.12, 0.10, 0.012, STEEL)
    c.line(-0.47, 0.20, -0.47, 0.32, 0.004, WHITE, 0.6)
    c.line(-0.12, 0.07, -0.08, 0.07, 0.010, STEEL)
    # bait pad with a piece of cheese
    c.ellipse(-0.14, 0.055, 0.045, 0.02, (0.8, 0.8, 0.82), lift=0.12)
    c.poly([(-0.17, 0.06), (-0.09, 0.06), (-0.09, 0.095), (-0.17, 0.085)], (0.98, 0.80, 0.30), lift=0.18)
    c.poly([(-0.17, 0.085), (-0.09, 0.095), (-0.11, 0.11), (-0.16, 0.10)], (1.0, 0.9, 0.5), lift=0.1)
    for u, v in ((-0.14, 0.075), (-0.115, 0.082)):
        c.circle(u, v, 0.007, scale((0.98, 0.8, 0.3), 0.7), lift=0)


@sprop("svc_pest_gel", aspect=5.5, fill=0.28)
def svc_pest_gel(c, P):
    """A gel syringe lying on the floor with dots of gel bait and a tube of gel."""
    c = c.sub(-0.23, 0.0, 1.0)
    rng = c.rng
    gel = (0.93, 0.50, 0.12)
    ang = 8

    def R(pts):
        return _rot(pts, ang, -0.2, 0.08)
    c.poly(R([(0.0, -0.05), (0.78, -0.05), (0.78, 0.06), (0.0, 0.06)]), (0.86, 0.93, 0.97), lift=0.2, alpha=0.8)
    c.poly(R([(0.04, -0.035), (0.50, -0.035), (0.50, 0.032), (0.04, 0.032)]), gel, lift=0.2)
    c.poly(R([(0.04, 0.012), (0.50, 0.012), (0.50, 0.03), (0.04, 0.03)]), mix(gel, WHITE, 0.45), lift=0, alpha=0.6)
    for k in range(8):
        a, b = R([(0.06 + k * 0.1, 0.06), (0.06 + k * 0.1, 0.045 - (k % 2) * 0.02)])
        c.line(a[0], a[1], b[0], b[1], 0.005, (0.35, 0.4, 0.5), 0.6)
    c.poly(R([(0.78, -0.07), (0.86, -0.07), (0.86, 0.08), (0.78, 0.08)]), (0.96, 0.97, 0.98), lift=0.1)
    c.poly(R([(-0.28, -0.015), (0.0, -0.015), (0.0, 0.015), (-0.28, 0.015)]), (0.93, 0.94, 0.96), lift=0.2)
    c.poly(R([(-0.34, -0.05), (-0.28, -0.05), (-0.28, 0.05), (-0.34, 0.05)]), (0.96, 0.97, 0.98), lift=0.1)
    c.poly(R([(0.86, -0.02), (1.0, -0.008), (1.0, 0.008), (0.86, 0.02)]), (0.55, 0.58, 0.64), lift=0.2)
    p = R([(1.0, 0.0)])[0]
    for k in range(5):
        _bead(c, p[0] + 0.05 + k * 0.06 + rng.uniform(-0.01, 0.01), p[1] - 0.04 + rng.uniform(-0.015, 0.015), rng.uniform(0.012, 0.02), gel)
    gloss(c, 0.2, 0.16, 0.22, 0.012, ang, 0.7)


@sprop("svc_pest_drill", aspect=2.14, fill=0.70)
def svc_pest_drill(c, P):
    """A cordless drill boring into a wooden beam: drilled holes, mud tunnels, sawdust and an injection nozzle."""
    c = c.sub(-0.10, 0.0, 1.0)
    rng = c.rng
    acc = P.accent
    # wooden beam with the end face turned to the key light
    _prism(c, 0.50, 0.0, 0.50, 0.62, 0.10, 0.08, WOOD, top=mix(WOOD, WHITE, 0.25), side=scale(WOOD, 0.55), lift=0.1)
    for k in range(18):
        x = 0.28 + rng.uniform(0, 0.44)
        c.line(x, 0.03, x + rng.uniform(-0.01, 0.01), rng.uniform(0.2, 0.6), 0.003, scale(WOOD, rng.uniform(0.66, 0.84)), 0.45)
    for (u, v) in ((0.36, 0.22), (0.62, 0.30), (0.42, 0.50)):                                       # drilled holes
        c.ellipse(u, v, 0.028, 0.028 * 0.8, (0.10, 0.07, 0.05), lift=0)
        c.arc(u, v, 0.028, 25, 200, 0.006, mix(WOOD, WHITE, 0.4), 0.8, 0.022)
    mud = (0.50, 0.34, 0.22)
    for pts in (((0.30, 0.02), (0.31, 0.2), (0.27, 0.38), (0.30, 0.55)), ((0.70, 0.02), (0.68, 0.16), (0.72, 0.28))):
        _path(c, pts, 0.035, scale(mud, 0.7), 1.0)
        _path(c, [(x - 0.006, y + 0.004) for x, y in pts], 0.022, mud, 1.0)
    for _ in range(26):                                                                              # sawdust at the foot
        c.circle(rng.uniform(0.0, 0.8), rng.uniform(-0.01, 0.05), rng.uniform(0.004, 0.010), mix(WOOD, WHITE, rng.uniform(0.2, 0.5)), lift=0)
    # the drill, pointing at the beam
    dx, dy = -0.60, 0.46
    c.line(dx + 0.52, dy, dx + 0.84, dy + 0.01, 0.014, (0.80, 0.82, 0.86))                          # bit
    c.rect(dx + 0.46, dy, 0.10, 0.075, (0.52, 0.55, 0.60), r=0.015, lift=0.25)                      # chuck
    c.rect(dx + 0.46, dy + 0.02, 0.09, 0.012, WHITE, lift=0, alpha=0.6)
    c.rect(dx + 0.20, dy + 0.01, 0.44, 0.19, acc, r=0.07, lift=0.25)                                # housing
    c.rect(dx + 0.20, dy + 0.07, 0.40, 0.03, mix(acc, WHITE, 0.55), r=0.015, lift=0, alpha=0.7)
    c.rect(dx + 0.32, dy - 0.01, 0.14, 0.16, (0.15, 0.16, 0.20), r=0.02, lift=0.2)
    c.rect(dx + 0.02, dy + 0.03, 0.14, 0.15, (0.15, 0.16, 0.20), r=0.05, lift=0.2)                  # motor cap
    for k in range(4):
        c.rect(dx + 0.30, dy - 0.045 + k * 0.025, 0.05, 0.008, mix(acc, WHITE, 0.3), lift=0, alpha=0.9)
    c.poly([(dx + 0.14, dy - 0.07), (dx + 0.30, dy - 0.07), (dx + 0.24, dy - 0.33), (dx + 0.10, dy - 0.33)], (0.15, 0.16, 0.20), lift=0.25)     # grip
    c.poly([(dx + 0.14, dy - 0.10), (dx + 0.22, dy - 0.10), (dx + 0.18, dy - 0.28), (dx + 0.12, dy - 0.28)], YELLOW, lift=0.1, alpha=0.9)
    c.rect(dx + 0.15, dy - 0.38, 0.30, 0.10, scale(acc, 0.55), r=0.02, lift=0.2)                    # battery
    c.rect(dx + 0.15, dy - 0.40, 0.24, 0.014, YELLOW, lift=0)
    gloss(c, dx + 0.14, dy + 0.14, 0.18, 0.016, 0, 0.6)


@sprop("svc_pest_bucket", aspect=0.59, fill=1.27)
def svc_pest_bucket(c, P):
    """A work bucket with a stirring stick, a scoop and a pair of rubber gloves hanging over the rim."""
    c = c.sub(0.07, 0.0, 1.0)
    rng = c.rng
    col = (0.97, 0.78, 0.18)
    # handle
    arc(c, 0.0, 0.80, 0.36, 0.34, 0, 180, 0.020, (0.45, 0.47, 0.52), 1.0, 14)
    # tapered body
    c.ellipse(0.0, 0.02, 0.28, 0.28 * TILT, scale(col, 0.58), lift=0)
    c.poly([(-0.30, 0.88), (0.30, 0.88), (0.25, 0.02), (-0.25, 0.02)], col, lift=0.14)
    soft_disc(c, 0.26, 0.45, 0.14, 0.50, BLACK, 0.30, 1.3)
    c.poly([(-0.27, 0.80), (-0.21, 0.80), (-0.17, 0.08), (-0.20, 0.08)], mix(col, WHITE, 0.55), alpha=0.55, lift=0)
    c.rect(0.0, 0.62, 0.55, 0.012, scale(col, 0.7), lift=0, alpha=0.6)
    c.rect(0.0, 0.28, 0.48, 0.012, scale(col, 0.7), lift=0, alpha=0.6)
    for lv in (0.55, 0.45, 0.35):                                                                    # measure marks (plain ticks)
        c.rect(-0.04, lv, 0.07, 0.007, scale(col, 0.45), lift=0, alpha=0.7)
    c.ellipse(0.0, 0.88, 0.31, 0.31 * TILT, scale(col, 1.08), lift=0.1)
    c.ellipse(0.0, 0.885, 0.27, 0.27 * TILT, (0.34, 0.20, 0.10), lift=0)
    c.ellipse(0.0, 0.885, 0.255, 0.255 * TILT, (0.55, 0.78, 0.9), lift=0.1, alpha=0.9)               # liquid
    gloss(c, -0.09, 0.90, 0.10, 0.015, 0, 0.7)
    # stirring stick
    c.line(0.10, 0.88, 0.24, 1.25, 0.034, scale(WOOD, 1.05))
    c.line(0.09, 0.90, 0.22, 1.22, 0.008, mix(WOOD, WHITE, 0.55), 0.7)
    # rubber gloves over the rim
    gl = (0.93, 0.35, 0.18) if P.mood != "light" else (0.95, 0.42, 0.22)
    c.poly([(-0.30, 0.90), (-0.40, 0.90), (-0.44, 0.60), (-0.34, 0.58)], gl, lift=0.2)
    for k, (du, dh) in enumerate(((-0.40, 0.14), (-0.35, 0.16), (-0.30, 0.15), (-0.255, 0.12))):
        c.line(du - 0.01, 0.62 - k * 0.002, du - 0.015 + 0.01 * k, 0.62 - dh, 0.040, gl)
    c.line(-0.40, 0.84, -0.40, 0.64, 0.010, mix(gl, WHITE, 0.55), 0.7)
    c.rect(-0.35, 0.90, 0.12, 0.06, scale(gl, 0.7), lift=0.15, r=0.02)


@niche("pest-control", "Pest control", subjects=("svc_pest_sprayer",),
       strong=("pest control", "pest control service", "pest control services", "pest management", "termite control", "termite treatment", "cockroach control",
               "bed bug removal", "bed bug treatment", "rodent control", "fumigation", "deemak", "deemak ilaj", "keede makode", "cockroach", "termites", "termite", "pest",
               "mosquito control", "anti termite", "pre construction treatment", "pest controller", "pest control technician", "bed bugs", "khatmal",
               "पेस्ट कंट्रोल", "दीमक", "दीमक का इलाज", "कीट नियंत्रण", "कॉकरोच", "खटमल", "चूहे मारने", "फ्यूमिगेशन", "कीड़े मकोड़े"),
       weak=("insects", "rodents", "bugs", "mosquito", "ants", "spray", "fogging", "bait", "infestation", "larvae", "कीट", "मच्छर"),
       accent="#1565c0", mood="light", group="services",
       avoid=("house cleaning", "deep cleaning", "maid", "housekeeping", "cleaning services", "pet shop", "veterinary", "agriculture", "pesticide shop", "seeds"))
def pest_control(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    tile = mix(P.wall_top, P.accent_light, 0.30) if not dk else scale(mix(P.accent, (0.35, 0.4, 0.45), 0.5), 0.30)
    cab = mix(P.paper, P.accent_light, 0.18) if not dk else scale(mix(P.accent_dark, P.floor_top, 0.5), 0.8)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # kitchen: tiled splash-back, wall cabinets, a window with a light shaft
        S.gradient_rect(-5.0, 0.20, 7.0, 0.60, scale(tile, 1.04), scale(tile, 0.90))
        for k in range(38):
            S.rect(-4.9 + k * 0.30, 0.40, 0.004, 0.40, scale(tile, 0.72), lift=0.0, alpha=0.5)
        for j in range(5):
            S.rect(1.0, 0.24 + j * 0.10, 12.0, 0.004, scale(tile, 0.72), lift=0.0, alpha=0.5)
        for k in range(4):
            S.rect(1.15 + k * 0.50, 0.08, 0.46, 0.34, cab, r=0.01, lift=0.08)
            S.rect(1.15 + k * 0.50, 0.08, 0.40, 0.28, scale(cab, 0.95), r=0.008, lift=0.0, alpha=0.6)
            S.rect(1.15 + k * 0.50 + 0.17, 0.19, 0.012, 0.06, scale(P.ink, 2.0), lift=0)
        S.window(0.22, 0.30, 0.36, 0.40)
        S.glow(0.5, 0.35, 1.0, P.light, 0.20)
        S.glow(1.5, 0.30, 0.9, mix(P.accent_light, WHITE, 0.4), 0.14 if not dk else 0.24)
        S.rect(1.0, 0.615, 14.0, 0.032, mix(P.paper, WHITE, 0.4), lift=0.0)                       # skirting
        S.floor(0.63, scale(P.floor_top, 1.0), scale(P.floor_bot, 0.9))
    S.wood(-1.4, 0.64, 3.6, 2.6, mix(P.surface, (0.62, 0.46, 0.30), 0.35) if not dk else scale(P.surface, 0.8), plank=0.15, vertical=True, grain=0.5)
    S.rect(1.0, 0.64, 14.0, 0.006, scale(P.floor_top, 0.55), lift=0.0, alpha=0.8)
    S.soft(1.12, 0.86, 0.55, 0.13, P.light, 0.30 if not dk else 0.22, 1.4, add=True)
    S.put("svc_pest_fogger", 1.12, 0.77, 0.27, color=P)
    S.put("svc_pest_sprayer", 0.90, 0.92, 0.54, color=P, subject=True)
    S.put("svc_pest_bucket", 0.60, 0.98, 0.21, color=P)
    S.put("svc_pest_trap", 1.02, 0.98, 0.12, color=P)
    S.put("svc_pest_drill", 1.40, 0.98, 0.24, color=P)
    S.put("svc_pest_gel", 0.82, 1.00, 0.07, color=P, framed=False)
    S.focus("detail", 1.06, 0.80)
    with S.near():
        S.circle(0.38, 1.16, 0.10, YELLOW, 0.5)
        S.ellipse(1.86, 1.20, 0.12, 0.05, mix(P.accent, WHITE, 0.3), -10, 0.5)


# ====================================================================================================== laundry and dry cleaning
def _fold(c, u, v, w, h, col, stripe=None, collar=False, tone=None):
    """One folded shirt in a stack: front face, lit top edge, fold crease, optional pinstripes and a collar."""
    tone = tone or scale(col, 0.62)
    c.rect(u, v + h / 2, w, h, col, r=0.022, lift=0.10)
    c.rect(u, v + h * 0.90, w * 0.96, h * 0.14, mix(col, WHITE, 0.30), r=0.01, lift=0, alpha=0.7)                 # lit top edge
    c.rect(u - w * 0.45, v + h / 2, w * 0.10, h * 0.92, scale(col, 0.86), lift=0, alpha=0.7, r=0.02)             # the folded side
    c.rect(u + w * 0.485, v + h / 2, w * 0.03, h * 0.96, tone, lift=0, alpha=0.5)
    if stripe:
        k = 0
        x = u - w * 0.36
        while x < u + w * 0.46:
            c.rect(x, v + h / 2, 0.006, h * 0.88, stripe, lift=0, alpha=0.75)
            x += 0.045
            k += 1
    soft_disc(c, u, v + h * 0.12, w * 0.55, h * 0.30, BLACK, 0.16, 1.2)                                         # shade near the shirt below
    if collar:
        cx = u + w * 0.12
        c.poly([(cx - 0.12, v + h), (cx - 0.01, v + h), (cx - 0.05, v + h - 0.10)], mix(col, WHITE, 0.45), lift=0.15)
        c.poly([(cx + 0.12, v + h), (cx + 0.01, v + h), (cx + 0.05, v + h - 0.10)], mix(col, WHITE, 0.30), lift=0.15)
        c.rect(cx, v + h - 0.045, 0.012, 0.08, scale(col, 0.82), lift=0, alpha=0.7)
        for k in range(3):
            c.circle(cx, v + h - 0.05 - k * 0.032 if False else v + h - 0.08 - k * 0.0, 0.0, col)       # placeholder (no-op)
        for k in range(2):
            c.circle(cx + 0.003, v + h * 0.6 - k * 0.05, 0.008, mix(col, WHITE, 0.8), lift=0.2)


@sprop("svc_ln_folded", aspect=1.13, fill=0.86)
def svc_ln_folded(c, P):
    """The signature stack: five neatly folded shirts in different colours and weaves with a cloth tag on the string."""
    c = c.sub(-0.09, 0.0, 1.0)
    rng = c.rng
    cols = ((0.96, 0.96, 0.97), mix(P.accent, WHITE, 0.55), (0.93, 0.78, 0.72), P.accent, (0.97, 0.95, 0.88))
    layers = ((0.0, 0.17, cols[3], None, False), (0.17, 0.17, cols[0], mix(P.accent, WHITE, 0.2), False), (0.34, 0.16, cols[2], None, False),
              (0.50, 0.17, cols[1], mix(P.accent, WHITE, 0.15), False), (0.67, 0.19, cols[4], None, True))
    for k, (v, h, col, stripe, collar) in enumerate(layers):
        w = 0.80 - 0.012 * k + rng.uniform(-0.01, 0.01)
        _fold(c, rng.uniform(-0.015, 0.015), v, w, h, col, stripe, collar)
    # hang tag on a string
    c.line(0.30, 0.60, 0.46, 0.50, 0.005, (0.85, 0.80, 0.70), 0.9)
    c.poly([(0.42, 0.52), (0.55, 0.50), (0.57, 0.34), (0.44, 0.35)], (0.98, 0.96, 0.90), lift=0.08)
    c.circle(0.50, 0.50, 0.012, (0.5, 0.45, 0.4), lift=0)
    c.rect(0.50, 0.42, 0.09, 0.012, P.accent, lift=0)
    c.rect(0.50, 0.38, 0.07, 0.010, (0.55, 0.57, 0.62), lift=0, alpha=0.8)
    # a soft highlight sweep on the top shirt
    gloss(c, -0.20, 0.82, 0.22, 0.03, 0, 0.35)


@sprop("svc_ln_iron", aspect=1.85, fill=0.71)
def svc_ln_iron(c, P):
    """A steam iron standing on its heel, with the water window, steam vents and a puff of steam."""
    c = c.sub(-0.06, 0.0, 1.0)
    rng = c.rng
    acc = P.accent
    sole = (0.80, 0.82, 0.86)
    c.poly([(-0.52, 0.0), (0.42, 0.0), (0.42, 0.07), (-0.34, 0.07), (-0.46, 0.04)], scale(sole, 0.7), lift=0.2)
    c.rect(-0.02, 0.012, 0.86, 0.012, WHITE, lift=0, alpha=0.6)
    c.poly([(-0.46, 0.07), (0.42, 0.07), (0.42, 0.30), (0.20, 0.42), (-0.12, 0.38), (-0.38, 0.20)], acc, lift=0.20)
    c.poly([(-0.40, 0.10), (0.40, 0.10), (0.40, 0.14), (-0.36, 0.14)], scale(acc, 0.66), lift=0, alpha=0.6)
    c.poly([(-0.30, 0.20), (-0.10, 0.34), (0.16, 0.38), (0.20, 0.42), (-0.12, 0.38), (-0.38, 0.20)], mix(acc, WHITE, 0.42), lift=0, alpha=0.6)
    # water window and dial
    c.ellipse(0.14, 0.24, 0.10, 0.075, (0.92, 0.96, 1.0), lift=0.06, alpha=0.9)
    c.ellipse(0.14, 0.215, 0.092, 0.045, mix((0.45, 0.78, 0.95), acc, 0.2), lift=0.1)
    c.circle(-0.12, 0.26, 0.05, (0.92, 0.93, 0.95), lift=0.2)
    c.line(-0.12, 0.26, -0.10, 0.30, 0.008, scale(acc, 0.5))
    for k in range(5):
        c.circle(-0.30 + k * 0.05, 0.10 + 0.01 * (k % 2), 0.007, scale(acc, 0.4), lift=0)
    # handle
    _path(c, [(-0.06, 0.40), (0.04, 0.62), (0.30, 0.66), (0.40, 0.44)], 0.085, scale(acc, 0.55), 1.0)
    _path(c, [(-0.07, 0.41), (0.03, 0.60), (0.29, 0.645), (0.385, 0.45)], 0.05, scale(acc, 0.95), 1.0)
    _path(c, [(-0.065, 0.43), (0.02, 0.60), (0.20, 0.64)], 0.012, mix(acc, WHITE, 0.6), 0.8)
    c.rect(0.42, 0.18, 0.04, 0.06, (0.12, 0.13, 0.16), lift=0.2)                                           # cord boot
    _path(c, [(0.44, 0.17), (0.54, 0.11), (0.64, 0.05), (0.72, 0.06)], 0.014, (0.10, 0.11, 0.14), 1.0)
    # steam
    for k in range(10):
        t = k / 9.0
        x = -0.52 - t * 0.04 + rng.uniform(-0.03, 0.03)
        y = 0.12 + t * 0.55
        r = 0.06 + t * 0.10
        soft_disc(c, x, y, r, r * 0.9, (0.80, 0.85, 0.92), 0.34 * (1 - t * 0.7), 1.1)
        soft_disc(c, x - r * 0.1, y + r * 0.1, r * 0.75, r * 0.65, WHITE, 0.55 * (1 - t) + 0.05, 1.2)
    gloss(c, -0.18, 0.37, 0.18, 0.016, 12, 0.6)


@sprop("svc_ln_valet", aspect=1.06, fill=0.98)
def svc_ln_valet(c, P):
    """A garment stand holding a dry-cleaned shirt on a wooden hanger inside a clear plastic cover with a tag."""
    rng = c.rng
    steel = (0.72, 0.74, 0.78)
    c.ellipse(0.0, 0.02, 0.22, 0.22 * TILT, scale(steel, 0.5), lift=0)
    c.ellipse(0.0, 0.035, 0.21, 0.21 * TILT, steel, lift=0.15)
    gloss(c, -0.08, 0.045, 0.09, 0.015, 0, 0.6)
    c.line(0.0, 0.04, 0.0, 0.98, 0.030, scale(steel, 0.6))
    c.line(-0.007, 0.04, -0.007, 0.98, 0.010, mix(steel, WHITE, 0.6), 0.9)
    _path(c, [(0.0, 0.97), (0.0, 1.02), (0.05, 1.05), (0.08, 1.02)], 0.020, scale(steel, 0.8), 1.0)
    # hanger
    wood = (0.62, 0.44, 0.28)
    c.line(-0.30, 0.76, 0.0, 0.88, 0.022, wood)
    c.line(0.30, 0.76, 0.0, 0.88, 0.022, wood)
    c.line(-0.30, 0.76, 0.30, 0.76, 0.016, scale(wood, 0.8))
    # the shirt: body and sleeves
    white = mix(P.accent, WHITE, 0.78)
    c.poly([(-0.30, 0.76), (-0.52, 0.52), (-0.44, 0.44), (-0.28, 0.62)], scale(white, 0.9), lift=0.1)
    c.poly([(0.30, 0.76), (0.52, 0.52), (0.44, 0.44), (0.28, 0.62)], scale(white, 0.80), lift=0.1)
    c.poly([(-0.30, 0.76), (-0.10, 0.80), (0.10, 0.80), (0.30, 0.76), (0.30, 0.20), (-0.30, 0.20)], white, lift=0.1)
    c.poly([(-0.10, 0.80), (0.0, 0.70), (0.10, 0.80), (0.06, 0.82), (0.0, 0.76), (-0.06, 0.82)], mix(white, P.accent_light, 0.3), lift=0.15)     # collar
    c.rect(0.0, 0.48, 0.012, 0.50, scale(white, 0.82), lift=0, alpha=0.7)
    for k in range(5):
        c.circle(0.0, 0.70 - k * 0.1, 0.009, (0.82, 0.84, 0.88), lift=0.2)
    # pocket and a pale accent shadow stripe so the white shirt reads on a light wall
    c.rect(-0.14, 0.60, 0.12, 0.10, scale(white, 0.93), lift=0, alpha=0.9, r=0.008)
    soft_disc(c, 0.26, 0.5, 0.10, 0.34, mix(P.accent, (0.5, 0.55, 0.65), 0.4), 0.30, 1.3)
    # transparent plastic cover with highlights and a gathered bottom
    c.poly([(-0.36, 0.84), (0.36, 0.84), (0.36, 0.16), (0.0, 0.10), (-0.36, 0.16)], (0.86, 0.92, 0.97), alpha=0.28, lift=0.2)
    c.line(-0.30, 0.82, -0.30, 0.20, 0.030, WHITE, 0.50)
    c.line(0.30, 0.80, 0.30, 0.22, 0.014, WHITE, 0.35)
    c.line(-0.28, 0.12, 0.28, 0.12, 0.014, (0.85, 0.9, 0.95), 0.6)
    for _ in range(6):
        x = rng.uniform(-0.30, 0.30)
        c.line(x, rng.uniform(0.30, 0.70), x + rng.uniform(-0.03, 0.03), rng.uniform(0.15, 0.30), 0.004, WHITE, 0.4)
    # tag
    c.line(0.10, 0.84, 0.30, 0.60, 0.004, (0.9, 0.85, 0.7), 0.9)
    c.poly([(0.26, 0.62), (0.40, 0.58), (0.36, 0.44), (0.22, 0.48)], P.accent, lift=0.15)
    c.rect(0.31, 0.53, 0.09, 0.010, WHITE, lift=0, alpha=0.9)


@sprop("svc_ln_basket", aspect=1.07, fill=0.97)
def svc_ln_basket(c, P):
    """A wicker laundry basket heaped with towels, a saree with a golden border and a folded tee."""
    rng = c.rng
    wick = (0.78, 0.58, 0.36)
    c.ellipse(0.0, 0.03, 0.385, 0.385 * TILT, scale(wick, 0.6), lift=0)
    # heap of cloth behind the rim
    cl = (P.accent, mix(P.accent, WHITE, 0.55), (0.96, 0.95, 0.93), (0.90, 0.42, 0.40), (0.98, 0.80, 0.30))
    for k, (u, v, a, b, ang, ci) in enumerate(((-0.20, 0.62, 0.26, 0.15, 10, 0), (0.12, 0.70, 0.28, 0.16, -8, 2), (0.0, 0.84, 0.22, 0.12, 14, 1),
                                               (-0.28, 0.76, 0.16, 0.10, -20, 3), (0.26, 0.60, 0.18, 0.12, 28, 4))):
        c.ellipse(u, v, a, b, scale(cl[ci], 0.8), ang, lift=0.1)
        c.ellipse(u - 0.01, v + 0.01, a * 0.94, b * 0.9, cl[ci], ang, lift=0.2)
        c.line(u - a * 0.7, v + b * 0.2, u + a * 0.6, v - b * 0.1, 0.006, scale(cl[ci], 0.7), 0.5)
        soft_disc(c, u - a * 0.2, v + b * 0.4, a * 0.6, b * 0.3, WHITE, 0.3, 1.3, add=True)
    _path(c, [(-0.34, 0.66), (-0.05, 0.60), (0.20, 0.72), (0.34, 0.80)], 0.028, (0.92, 0.72, 0.22), 1.0)               # saree border
    _path(c, [(-0.34, 0.675), (-0.05, 0.615), (0.20, 0.735), (0.34, 0.815)], 0.008, (1.0, 0.92, 0.55), 0.9)
    _path(c, [(0.16, 0.86), (0.34, 0.92)], 0.060, (0.97, 0.97, 0.98), 1.0)
    # basket body: slightly flared with a woven pattern
    c.poly([(-0.46, 0.55), (0.46, 0.55), (0.38, 0.05), (-0.38, 0.05)], wick, lift=0.14)
    for k in range(7):
        v = 0.09 + k * 0.07
        c.rect(0.0, v, 0.84 - (6 - k) * 0.012 * 0.0, 0.012, scale(wick, 0.72), lift=0, alpha=0.6)
        for j in range(9):
            x = -0.42 + j * 0.105 + (0.05 if k % 2 else 0.0)
            c.rect(x * (0.84 + 0.02 * k / 6.0) * 0.0 + x, v + 0.035, 0.010, 0.050, scale(wick, 0.78 if (j + k) % 2 else 1.1), lift=0, alpha=0.7)
    soft_disc(c, 0.28, 0.30, 0.16, 0.30, BLACK, 0.26, 1.3)
    c.ellipse(0.0, 0.55, 0.48, 0.48 * TILT * 0.9, scale(wick, 1.12), lift=0.1)
    c.ellipse(0.0, 0.56, 0.46, 0.46 * TILT * 0.9, scale(wick, 0.9), lift=0.0, alpha=0.0)
    c.rect(0.0, 0.54, 0.90, 0.030, scale(wick, 0.8), r=0.014, lift=0.1, alpha=0.9)
    # clothes in front of the rim: overlapping edge
    c.ellipse(-0.10, 0.60, 0.20, 0.07, cl[1], 4, lift=0.2)
    c.ellipse(0.20, 0.585, 0.16, 0.06, cl[2], -6, lift=0.2)
    gloss(c, -0.28, 0.35, 0.03, 0.18, 0, 0.35)
    # handles
    arc(c, -0.47, 0.50, 0.04, 0.05, 90, 270, 0.018, scale(wick, 0.6), 1.0, 6)
    arc(c, 0.47, 0.50, 0.04, 0.05, -90, 90, 0.018, scale(wick, 0.6), 1.0, 6)


@sprop("svc_ln_bottle", aspect=1.03, fill=0.98)
def svc_ln_bottle(c, P):
    """Two detergent bottles with plain label bars, a measuring cap and a drift of soap bubbles."""
    c = c.sub(-0.04, 0.0, 1.0)
    rng = c.rng
    acc = P.accent
    bub = []
    for (u, h, w, col, cap) in ((-0.15, 0.78, 0.30, acc, (0.96, 0.96, 0.98)), (0.18, 0.54, 0.26, mix(acc, (0.35, 0.8, 0.7), 0.7), acc)):
        r = w / 2
        c.ellipse(u, 0.02, r, r * TILT, scale(col, 0.5), lift=0)
        c.poly([(u - r, 0.02), (u + r, 0.02), (u + r, h * 0.66), (u + r * 0.30, h * 0.84), (u - r * 0.30, h * 0.84), (u - r, h * 0.66)], col, lift=0.12)
        hshade_box(c, u, h * 0.43, w * 0.99, h * 0.84, mix(col, WHITE, 0.2), scale(col, 0.5), r=0.03, alpha=0.55)
        c.rect(u, h * 0.40, w * 0.98, h * 0.34, (0.97, 0.97, 0.98), lift=0.04, alpha=0.95)
        c.rect(u, h * 0.46, w * 0.72, h * 0.05, scale(col, 0.9), lift=0.1)
        _bars(c, u, h * 0.36, w * 0.66, 3, (0.5, 0.54, 0.62), gap=0.032, th=0.012, alpha=0.7)
        c.rect(u - r * 0.55, h * 0.40, 0.020, h * 0.58, WHITE, lift=0, alpha=0.30)
        c.ellipse(u, h * 0.86, r * 0.33, r * 0.33 * TILT, scale(col, 0.7), lift=0.1)
        _cyl(c, u, h * 0.84, r * 0.34, h * 0.14, cap, dark=0.6)
        c.rect(u + r * 0.78, h * 0.55, 0.05, h * 0.2, scale(col, 0.7), lift=0.1, r=0.02)            # handle grip
    # bubbles
    for _ in range(22):
        x, y = rng.uniform(-0.42, 0.52), rng.uniform(0.05, 0.95)
        r = rng.uniform(0.012, 0.045)
        c.ellipse(x, y, r, r, mix(P.accent_light, WHITE, 0.6), lift=0, alpha=0.35)
        c.arc(x, y, r, 20, 130, 0.006, WHITE, 0.9)
        soft_disc(c, x - r * 0.3, y + r * 0.35, r * 0.25, r * 0.18, WHITE, 0.8, 1.0, add=True)


@niche("laundry", "Laundry and dry cleaning", subjects=("svc_ln_folded",),
       strong=("laundry", "laundry service", "laundry services", "laundry and dry cleaning", "dry cleaning", "dry cleaner", "dry cleaners", "dry clean", "washing and ironing",
               "steam ironing", "wash and fold", "laundromat", "dhobi", "dhobi ghat", "kapde dhulai", "iron wala", "press wala", "dry cleaning specialist", "garment care",
               "laundry shop", "लॉन्ड्री", "ड्राई क्लीनिंग", "ड्राई क्लीन",
               "धोबी", "कपड़े धुलाई", "प्रेस वाला", "इस्त्री"),
       weak=("laundry", "ironing", "pressing", "clothes", "shirts", "garments", "fabric", "detergent", "washing machine", "folded", "कपड़े", "धुलाई"),
       accent="#1565c0", mood="light", group="services",
       avoid=("house cleaning", "deep cleaning", "car wash", "maid", "washing machine repair", "ac repair", "tailor", "stitching", "pest control"))
def laundry(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    body = (0.95, 0.96, 0.97) if not dk else (0.30, 0.33, 0.38)
    glass = mix(P.accent, (0.4, 0.75, 0.95), 0.4)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.64)
        S.gradient_rect(-5.0, 0.52, 7.0, 0.64, scale(P.wall_bot, 0.86), scale(P.wall_bot, 0.78))
        # a row of front-loading washers with round glass doors and control strips
        for k in range(9):
            u = -0.50 + k * 0.40
            S.rect(u, 0.36, 0.36, 0.50, body, r=0.02, lift=0.10)
            S.rect(u, 0.17, 0.36, 0.07, scale(body, 0.92), r=0.01, lift=0.0)
            for j in range(3):
                S.circle(u - 0.09 + j * 0.09, 0.17, 0.012, P.accent if j == 1 else scale(body, 0.6), lift=0.1)
            S.circle(u, 0.40, 0.125, scale(body, 0.78), lift=0.0)
            S.circle(u, 0.40, 0.105, glass, lift=0.25)
            S.circle(u, 0.40, 0.06, scale(glass, 0.7), lift=0.1, alpha=0.8)
            if dk:
                S.glow(u, 0.40, 0.22, mix(glass, WHITE, 0.3), 0.40)
            S.glow(u - 0.04, 0.37, 0.05, WHITE, 0.30)
        S.glow(1.1, 0.10, 1.1, P.light, 0.22)
        S.rect(1.0, 0.64, 14.0, 0.02, scale(P.wall_bot, 0.55), lift=0.0)
        S.floor(0.64, scale(P.floor_top, 0.9), scale(P.floor_bot, 0.8))
    # folding counter: light boards running left to right with a lit front edge
    top = mix(P.paper, P.surface, 0.45) if not dk else scale(P.surface, 0.75)
    S.wood(-1.4, 0.68, 3.6, 2.6, top, plank=0.20, grain=0.5)
    S.rect(1.0, 0.668, 14.0, 0.026, scale(top, 0.62), lift=0.0)
    S.rect(1.0, 0.682, 14.0, 0.008, mix(top, WHITE, 0.55), lift=0.0, alpha=0.85)
    S.soft(1.02, 0.88, 0.60, 0.13, P.light, 0.34 if not dk else 0.26, 1.4, add=True)
    S.put("svc_ln_valet", 0.70, 0.79, 0.56, color=P)
    S.put("svc_ln_basket", 1.35, 0.82, 0.27, color=P)
    S.put("svc_ln_folded", 1.00, 0.92, 0.50, color=P, subject=True, shadow_alpha=0.22)
    S.put("svc_ln_iron", 1.31, 0.98, 0.22, color=P)
    S.put("svc_ln_bottle", 0.63, 0.98, 0.22, color=P)
    S.focus("detail", 1.18, 0.86)
    with S.near():
        for u, v, r in ((0.40, 1.15, 0.08), (0.52, 1.07, 0.045), (1.82, 1.14, 0.07)):
            S.circle(u, v, r, mix(P.accent_light, WHITE, 0.6), 0.4)


# ====================================================================================================== water purifier service
@sprop("svc_wp_unit", aspect=0.57, fill=1.09)
def svc_wp_unit(c, P):
    """A wall-mounted RO purifier: glossy white body, accent cap, a window onto three filter stages, LED ring and a spout."""
    rng = c.rng
    acc = P.accent
    body = (0.96, 0.97, 0.98)
    # inlet and drain pipes rising to the wall
    _tube(c, -0.14, 0.99, -0.14, 1.07, 0.040, (0.55, 0.78, 0.95), 0.5)
    _tube(c, 0.12, 0.99, 0.12, 1.07, 0.036, (0.92, 0.93, 0.95), 0.5)
    # body: soft contact shadow on the wall first
    soft_disc(c, 0.07, 0.46, 0.40, 0.58, BLACK, 0.20, 1.5)
    c.rect(0.0, 0.54, 0.62, 0.90, scale(body, 0.78), r=0.07, lift=0.0)
    c.rect(-0.01, 0.545, 0.60, 0.89, body, r=0.07, lift=0.10)
    c.rect(0.25, 0.54, 0.09, 0.84, scale(body, 0.80), r=0.04, lift=0, alpha=0.45)               # shaded right edge
    c.rect(-0.25, 0.54, 0.035, 0.80, WHITE, r=0.015, lift=0, alpha=0.8)                          # lit left edge
    # accent cap
    c.rect(-0.01, 0.90, 0.60, 0.17, acc, r=0.06, lift=0.22)
    c.rect(-0.01, 0.84, 0.60, 0.04, scale(acc, 0.7), r=0.0, lift=0, alpha=0.6)
    c.rect(-0.02, 0.945, 0.40, 0.014, mix(acc, WHITE, 0.55), r=0.007, lift=0, alpha=0.8)
    # window with three filter cartridges
    c.rect(-0.01, 0.62, 0.42, 0.34, (0.16, 0.19, 0.25), r=0.04, lift=0.10)
    c.rect(-0.01, 0.62, 0.395, 0.315, (0.74, 0.86, 0.95), r=0.03, lift=0.18, alpha=0.85)
    for u, col, h, kind in ((-0.12, (0.97, 0.97, 0.98), 0.24, "sed"), (0.0, (0.25, 0.27, 0.31), 0.27, "carbon"), (0.12, (0.30, 0.55, 0.88), 0.25, "ro")):
        hshade_box(c, u, 0.60, 0.085, h, mix(col, WHITE, 0.2), scale(col, 0.62), r=0.01)
        c.ellipse(u, 0.60 + h / 2, 0.0425, 0.014, scale(col, 0.7), lift=0.1)
        c.rect(u, 0.60 + h / 2 + 0.01, 0.065, 0.012, (0.85, 0.87, 0.90), lift=0.2, r=0.004)
        c.rect(u, 0.60 - h / 2 - 0.01, 0.07, 0.012, (0.85, 0.87, 0.90), lift=0.2, r=0.004)
    c.rect(-0.01, 0.52, 0.395, 0.07, mix((0.4, 0.7, 0.95), acc, 0.4), lift=0.1, alpha=0.4)         # water tint
    gloss(c, -0.12, 0.72, 0.02, 0.14, 0, 0.50)
    # control: LED ring and bar segments (no numerals)
    c.circle(0.0, 0.32, 0.075, scale(body, 0.88), lift=0.0)
    c.circle(0.0, 0.32, 0.060, (0.12, 0.15, 0.20), lift=0.1)
    arc(c, 0.0, 0.32, 0.048, 0.048, 40, 340, 0.014, mix(acc, (0.6, 0.9, 1.0), 0.6), 1.0, 14)
    soft_disc(c, 0.0, 0.32, 0.11, 0.11, mix(acc, (0.6, 0.9, 1.0), 0.5), 0.45, 1.3, add=True)
    for k in range(5):
        c.rect(-0.15 + k * 0.075, 0.18, 0.050, 0.018, mix(acc, WHITE, 0.2) if k < 4 else (0.8, 0.84, 0.9), lift=0, r=0.005)
    # spout at the bottom
    c.rect(0.0, 0.14, 0.18, 0.045, scale(body, 0.8), r=0.012, lift=0.1)
    c.rect(0.0, 0.105, 0.075, 0.07, (0.78, 0.80, 0.84), r=0.012, lift=0.2)
    c.rect(0.0, 0.07, 0.045, 0.03, (0.18, 0.20, 0.24), lift=0.1)


@sprop("svc_wp_filters", aspect=1.55, fill=0.66)
def svc_wp_filters(c, P):
    """Replacement cartridges standing in a row: spun sediment filter, carbon block and a slim RO membrane."""
    c = c.sub(-0.08, 0.0, 1.0)
    rng = c.rng
    # sediment: white spun-fibre cartridge
    u, h, r = -0.30, 0.46, 0.13
    c.ellipse(u, 0.02, r, r * TILT, (0.55, 0.57, 0.6), lift=0)
    hshade_box(c, u, 0.02 + h / 2, 2 * r, h, (1.0, 1.0, 1.0), (0.66, 0.70, 0.76))
    for k in range(18):
        c.rect(u, 0.04 + k * h / 18.0, 2 * r * 0.98, 0.006, (0.62, 0.66, 0.72), lift=0, alpha=0.30 + 0.1 * (k % 2))
    disc(c, u, 0.02 + h, r, (0.94, 0.95, 0.97), TILT, 0.06)
    c.ellipse(u, 0.02 + h, r * 0.38, r * 0.38 * TILT, (0.45, 0.50, 0.56), lift=0)
    # carbon block: black granular
    u, h, r = 0.0, 0.58, 0.14
    c.ellipse(u, 0.02, r, r * TILT, (0.06, 0.06, 0.08), lift=0)
    hshade_box(c, u, 0.02 + h / 2, 2 * r, h, (0.34, 0.35, 0.39), (0.08, 0.08, 0.10))
    for _ in range(55):
        c.circle(u + rng.uniform(-r * 0.9, r * 0.9), rng.uniform(0.04, 0.02 + h - 0.02), rng.uniform(0.003, 0.006), (0.5, 0.52, 0.56), lift=0, alpha=0.45)
    c.rect(u, 0.02 + h * 0.55, 2 * r, 0.03, mix(P.accent, WHITE, 0.1), lift=0.1)
    disc(c, u, 0.02 + h, r, (0.22, 0.23, 0.27), TILT, 0.06)
    c.ellipse(u, 0.02 + h, r * 0.35, r * 0.35 * TILT, (0.03, 0.03, 0.04), lift=0)
    gloss(c, -0.08, 0.38, 0.012, 0.18, 0, 0.35)
    # RO membrane: slim steel and blue
    u, h, r = 0.30, 0.50, 0.075
    c.ellipse(u, 0.02, r, r * TILT, (0.4, 0.45, 0.52), lift=0)
    hshade_box(c, u, 0.02 + h / 2, 2 * r, h, (0.85, 0.90, 0.96), (0.40, 0.48, 0.58))
    c.rect(u, 0.02 + h * 0.5, 2 * r, h * 0.42, P.accent, lift=0.18)
    c.rect(u, 0.02 + h * 0.5, 2 * r * 0.98, 0.010, mix(P.accent, WHITE, 0.55), lift=0, alpha=0.8)
    for z in (0.04, h - 0.01):
        c.rect(u, 0.02 + z, 2 * r * 1.12, 0.035, (0.20, 0.22, 0.26), lift=0.2, r=0.01)
    disc(c, u, 0.02 + h + 0.02, r * 1.1, (0.30, 0.34, 0.40), TILT, 0.08)
    gloss(c, u - 0.04, 0.30, 0.008, 0.18, 0, 0.55)
    # spare O-ring and a filter in plastic wrap lying in front
    c.ellipse(0.52, 0.04, 0.07, 0.07 * TILT, (0.10, 0.10, 0.13), lift=0.1)
    c.ellipse(0.52, 0.045, 0.045, 0.045 * TILT, (0.4, 0.42, 0.46), lift=0.0, alpha=0.0)
    c.ellipse(0.52, 0.05, 0.035, 0.035 * TILT, (0.7, 0.72, 0.76), lift=0)


@sprop("svc_wp_tds", aspect=0.79, fill=1.06)
def svc_wp_tds(c, P):
    """A glass of tap water with a digital TDS pen standing in it (a plain bar display) next to a test-strip card."""
    c = c.sub(-0.22, 0.0, 1.0)
    rng = c.rng
    r, h = 0.20, 0.52
    # glass back, water, pen, glass front
    c.ellipse(0.0, 0.02, r, r * TILT, (0.55, 0.65, 0.72), lift=0, alpha=0.8)
    hshade_box(c, 0.0, 0.02 + h / 2, 2 * r, h, (0.92, 0.97, 1.0), (0.60, 0.72, 0.80), alpha=0.40)
    c.rect(0.0, 0.02 + h * 0.36, 2 * r * 0.96, h * 0.70, mix((0.5, 0.78, 0.95), P.accent, 0.25), lift=0.1, alpha=0.55)
    c.ellipse(0.0, 0.02 + h * 0.71, r * 0.95, r * 0.95 * TILT, mix((0.7, 0.88, 1.0), P.accent_light, 0.3), lift=0.1, alpha=0.8)
    pen = (0.93, 0.94, 0.96)
    c.poly(_rot([(-0.045, 0.0), (0.045, 0.0), (0.045, 0.92), (-0.045, 0.92)], -9, 0.02, 0.08), pen, lift=0.12)
    c.poly(_rot([(-0.045, 0.64), (0.045, 0.64), (0.045, 0.74), (-0.045, 0.74)], -9, 0.02, 0.08), scale(P.accent, 0.8), lift=0.1)
    c.poly(_rot([(-0.034, 0.70), (0.034, 0.70), (0.034, 0.86), (-0.034, 0.86)], -9, 0.02, 0.08), (0.55, 0.72, 0.60), lift=0.08)              # display
    for k in range(4):
        a, b = _rot([(-0.02, 0.74 + k * 0.03), (0.016, 0.74 + k * 0.03)], -9, 0.02, 0.08)
        c.line(a[0], a[1], b[0], b[1], 0.012, (0.13, 0.20, 0.15), 0.75)
    c.circle(0.075, 0.16 + 0.02, 0.0, WHITE)
    c.poly(_rot([(-0.045, 0.92), (0.045, 0.92), (0.04, 0.99), (-0.04, 0.99)], -9, 0.02, 0.08), scale(pen, 0.78), lift=0.12)
    c.ellipse(0.0, 0.02 + h, r, r * TILT, (0.90, 0.96, 1.0), lift=0, alpha=0.30)
    arc(c, 0.0, 0.02 + h, r, r * TILT, 0, 360, 0.010, (0.95, 0.99, 1.0), 0.9, 16)
    c.rect(-0.14, 0.02 + h * 0.5, 0.020, h * 0.80, WHITE, lift=0, alpha=0.55, r=0.01)
    for k in range(3):
        c.rect(0.12, 0.14 + k * 0.10, 0.05, 0.007, scale(P.accent, 0.5), lift=0, alpha=0.7)
    for _ in range(9):
        c.circle(rng.uniform(-0.12, 0.12), rng.uniform(0.08, 0.3), rng.uniform(0.005, 0.012), WHITE, lift=0, alpha=0.5)
    # test-strip card
    c.poly([(0.30, 0.06), (0.62, 0.02), (0.64, 0.10), (0.33, 0.14)], (0.97, 0.96, 0.92), lift=0.08)
    for k, col in enumerate(((0.35, 0.8, 0.4), (0.9, 0.85, 0.3), (0.95, 0.55, 0.2), (0.85, 0.3, 0.2))):
        c.rect(0.36 + k * 0.065, 0.085 - k * 0.012, 0.045, 0.045, col, lift=0.1, r=0.006)


@sprop("svc_wp_tap", aspect=0.94, fill=0.97)
def svc_wp_tap(c, P):
    """A chrome tap with a lever handle pouring a thin stream into a steel bowl."""
    rng = c.rng
    chrome = (0.82, 0.85, 0.90)
    # bowl
    c.ellipse(0.05, 0.03, 0.40, 0.40 * TILT, scale(chrome, 0.5), lift=0)
    c.poly([(-0.36, 0.20), (0.46, 0.20), (0.32, 0.03), (-0.22, 0.03)], scale(chrome, 0.85), lift=0.2)
    hshade_box(c, 0.05, 0.115, 0.82, 0.17, mix(chrome, WHITE, 0.2), scale(chrome, 0.45), r=0.02, alpha=0.55)
    c.ellipse(0.05, 0.20, 0.41, 0.41 * TILT, scale(chrome, 1.08), lift=0.1)
    c.ellipse(0.05, 0.205, 0.37, 0.37 * TILT, scale(chrome, 0.55), lift=0.0)
    c.ellipse(0.05, 0.20, 0.34, 0.34 * TILT, mix((0.55, 0.78, 0.95), P.accent, 0.3), lift=0.12, alpha=0.9)
    for k in range(3):
        arc(c, 0.05 - 0.1, 0.20, 0.06 + k * 0.07, (0.06 + k * 0.07) * TILT, 10, 350, 0.005, WHITE, 0.55 - k * 0.12, 14)
    # faucet
    c.ellipse(-0.40, 0.03, 0.10, 0.04, scale(chrome, 0.55), lift=0)
    hshade_box(c, -0.40, 0.38, 0.11, 0.70, mix(chrome, WHITE, 0.3), scale(chrome, 0.5), r=0.02)
    arc(c, -0.20, 0.72, 0.22, 0.22, 0, 180, 0.100, scale(chrome, 0.55), 1.0, 14)
    arc(c, -0.20, 0.72, 0.22, 0.22, 20, 180, 0.070, chrome, 1.0, 14)
    arc(c, -0.20, 0.745, 0.215, 0.20, 40, 170, 0.014, WHITE, 0.9, 12)
    c.rect(-0.02, 0.675, 0.075, 0.070, scale(chrome, 0.6), lift=0.2, r=0.01)                      # aerator
    c.line(-0.40, 0.80, -0.30, 0.92, 0.035, chrome)                                                # lever
    c.circle(-0.30, 0.92, 0.030, scale(P.accent, 1.0), lift=0.25)
    # water stream with highlights and splash
    c.rect(-0.015, 0.40, 0.034, 0.26, (0.65, 0.84, 0.97), lift=0.1, alpha=0.85)
    c.rect(-0.025, 0.40, 0.008, 0.25, WHITE, lift=0, alpha=0.85)
    for _ in range(8):
        c.circle(-0.015 + rng.uniform(-0.12, 0.14), 0.22 + rng.uniform(0.0, 0.10), rng.uniform(0.006, 0.014), (0.75, 0.90, 1.0), lift=0.1, alpha=0.85)
    soft_disc(c, -0.015, 0.215, 0.10, 0.03, WHITE, 0.7, 1.2, add=True)


@sprop("svc_wp_wrench", aspect=5.88, fill=0.27)
def svc_wp_wrench(c, P):
    """An adjustable spanner, a coil of blue RO tubing and a white elbow joint: the installer's small kit."""
    c = c.sub(0.10, 0.0, 1.0)
    rng = c.rng
    steel = (0.74, 0.77, 0.82)
    # coil of tubing (stacked rings)
    for k in range(4):
        c.ellipse(0.50, 0.06 + k * 0.032, 0.20, 0.20 * TILT, scale((0.30, 0.55, 0.90), 0.65), lift=0)
        c.ellipse(0.50, 0.066 + k * 0.032, 0.20, 0.20 * TILT, (0.30, 0.58, 0.92), lift=0.2)
        c.ellipse(0.50, 0.072 + k * 0.032, 0.14, 0.14 * TILT, scale((0.30, 0.55, 0.90), 0.55), lift=0, alpha=0.9)
    c.ellipse(0.50, 0.185, 0.20, 0.20 * TILT, (0.30, 0.58, 0.92), lift=0.2)
    c.ellipse(0.50, 0.185, 0.13, 0.13 * TILT, scale((0.30, 0.55, 0.90), 0.45), lift=0)
    gloss(c, 0.40, 0.215, 0.07, 0.012, 0, 0.6)
    # spanner at an angle
    ang = 8
    def R(pts):
        return _rot(pts, ang, -0.20, 0.10)
    c.poly([(x + 0.01, y - 0.012) for x, y in R([(-0.70, -0.045), (0.28, -0.045), (0.28, 0.045), (-0.70, 0.045)])], BLACK, alpha=0.18)
    c.poly(R([(-0.70, -0.045), (0.28, -0.035), (0.28, 0.035), (-0.70, 0.045)]), steel, lift=0.22)
    c.poly(R([(-0.70, 0.02), (0.28, 0.02), (0.28, 0.034), (-0.70, 0.044)]), WHITE, alpha=0.55, lift=0)
    c.poly(R([(0.26, -0.11), (0.52, -0.11), (0.52, 0.02), (0.38, 0.02), (0.38, 0.12), (0.26, 0.12)]), scale(steel, 0.92), lift=0.22)
    c.poly(R([(0.40, 0.02), (0.52, 0.02), (0.52, 0.045), (0.40, 0.045)]), (0.1, 0.1, 0.12), lift=0)
    c.poly(R([(-0.70, -0.045), (-0.64, -0.045), (-0.64, 0.045), (-0.70, 0.045)]), P.accent, lift=0.1)
    p = R([(0.31, 0.0)])[0]
    c.circle(p[0], p[1], 0.032, scale(steel, 0.7), lift=0.3)
    c.circle(p[0] - 0.008, p[1] + 0.008, 0.010, WHITE, lift=0, alpha=0.9)
    # white elbow joint
    hshade_box(c, -0.55, 0.20, 0.09, 0.07, (0.98, 0.98, 0.99), (0.7, 0.72, 0.76), r=0.01)
    hshade_box(c, -0.50, 0.17, 0.07, 0.09, (0.98, 0.98, 0.99), (0.7, 0.72, 0.76), r=0.01)


@niche("water-purifier", "Water purifier service", subjects=("svc_wp_unit",),
       strong=("water purifier", "water purifier service", "ro service", "ro water purifier", "ro repair", "ro installation", "ro membrane", "ro filter", "water filter service", "purifier service", "purifier installation", "purifier", "ro service and cleaning",
               "aquaguard", "tds meter", "water filter installation", "ro plant", "pani ka filter", "ro wala", "वाटर प्यूरीफायर", "आरओ सर्विस", "आरओ", "वॉटर फिल्टर",
               "पानी का फिल्टर", "आरओ मरम्मत", "प्यूरीफायर"),
       weak=("purifier", "tds", "filter", "membrane", "uv", "drinking water", "cartridge", "pure water", "water quality", "पानी"),
       accent="#1565c0", mood="light", group="services",
       avoid=("air purifier", "plumber", "plumbing", "pipe fitting", "swimming pool", "drainage", "sanitary ware", "water tanker", "bottled water", "bore well", "borewell"))
def water_purifier(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    tile = mix(P.wall_top, P.accent_light, 0.38) if not dk else scale(mix(P.accent, (0.4, 0.45, 0.5), 0.5), 0.38)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.64)
        S.gradient_rect(-5.0, -0.5, 7.0, 0.64, scale(tile, 1.05), scale(tile, 0.88))
        for j in range(8):
            S.rect(1.0, 0.04 + j * 0.085, 12.0, 0.004, scale(tile, 0.72), lift=0.0, alpha=0.55)
        for j in range(8):
            for k in range(30):
                S.rect(-4.5 + k * 0.34 + (0.17 if j % 2 else 0.0), 0.04 + j * 0.085 - 0.04, 0.004, 0.085, scale(tile, 0.72), lift=0.0, alpha=0.45)
        S.rect(1.0, 0.50, 12.0, 0.04, mix(P.accent, WHITE, 0.35), lift=0.0, alpha=0.55)               # accent border tile row
        S.window(0.20, 0.26, 0.30, 0.34)
        S.glow(1.05, 0.30, 1.0, mix(P.accent_light, WHITE, 0.4), 0.18 if not dk else 0.34)
        S.rect(1.0, 0.64, 14.0, 0.03, scale(P.wall_bot, 0.55), lift=0.0)
        S.floor(0.64, scale(P.floor_top, 0.9), scale(P.floor_bot, 0.8))
    # granite counter: dark slate speckled with light crystals, lit front edge
    slate = scale(mix(P.accent_dark, (0.42, 0.45, 0.50), 0.55), 0.82 if not dk else 0.55)
    S.floor(0.67, scale(slate, 1.12), scale(slate, 0.72))
    S.rect(1.0, 0.668, 14.0, 0.016, scale(slate, 0.55), lift=0.0)
    S.rect(1.0, 0.678, 14.0, 0.007, mix(slate, WHITE, 0.45), lift=0.0, alpha=0.8)
    for _ in range(170):
        S.circle(rng.uniform(-0.2, 2.2), rng.uniform(0.70, 1.35), rng.uniform(0.0015, 0.004), mix(slate, WHITE, rng.uniform(0.35, 0.8)), lift=0, alpha=rng.uniform(0.4, 0.9))
    for _ in range(80):
        S.circle(rng.uniform(-0.2, 2.2), rng.uniform(0.70, 1.35), rng.uniform(0.002, 0.005), scale(slate, 0.5), lift=0, alpha=0.5)
    S.soft(1.05, 0.88, 0.60, 0.13, mix(P.light, P.accent_light, 0.4), 0.30 if not dk else 0.28, 1.4, add=True)
    # unit on the wall: cast shadow first, then the unit itself (mounted: no floor shadow)
    S.soft(1.07, 0.40, 0.30, 0.32, BLACK, 0.18, 1.6)
    S.put("svc_wp_unit", 1.06, 0.64, 0.47, color=P, subject=True, shadow=False)
    S.put("svc_wp_filters", 0.78, 0.83, 0.28, color=P)
    S.put("svc_wp_tap", 1.34, 0.88, 0.36, color=P)
    S.put("svc_wp_tds", 1.02, 0.98, 0.28, color=P)
    S.put("svc_wp_wrench", 1.22, 0.99, 0.07, color=P, framed=False)
    S.focus("detail", 1.06, 0.44)
    with S.near():
        for u, v, r in ((0.42, 1.14, 0.07), (0.30, 1.06, 0.04), (1.84, 1.15, 0.06)):
            S.circle(u, v, r, mix(P.accent_light, WHITE, 0.55), 0.45)


# ====================================================================================================== scrap and recycling
CARD_C = (0.70, 0.52, 0.34)


def _bale(c, u, v, w, h, dx, dy, base, rng, straps=4, scraps=True):
    """A strapped bale of compressed cardboard: layered strips on the front, lit top and a darker side, steel bands."""
    _prism(c, u, v, w, h, dx, dy, base, top=mix(base, WHITE, 0.20), side=scale(base, 0.58), lift=0.05)
    n = max(8, int(h / 0.011))
    for k in range(n):
        y = v + (k + 0.5) * h / n
        tone = rng.uniform(0.80, 1.12)
        a = rng.uniform(0.0, 0.12) * w
        b = rng.uniform(0.0, 0.12) * w
        col = scale(base, tone) if k % 3 else mix(scale(base, tone), (0.88, 0.86, 0.80), 0.5)
        c.rect(u + (a - b) / 2, y, w - a - b, h / n * 0.62, col, lift=0.0, alpha=0.85)
        c.rect(u, v + k * h / n, w, 0.003, scale(base, 0.50), lift=0, alpha=0.30)
    for k in range(5):                                                                                   # print patches (plain colour blocks)
        c.rect(u + rng.uniform(-w * 0.4, w * 0.4), v + rng.uniform(0.15, 0.85) * h, rng.uniform(0.03, 0.07), 0.012, rng.choice(((0.30, 0.45, 0.70), (0.85, 0.80, 0.70), (0.75, 0.3, 0.25))), lift=0, alpha=0.7)
    for k in range(straps):                                                                              # steel straps over front and top
        x = u - w * 0.42 + k * (w * 0.84 / max(1, straps - 1))
        c.rect(x, v + h / 2, 0.013, h * 1.0, (0.16, 0.17, 0.20), lift=0.1)
        c.line(x - 0.004, v + h * 0.1, x - 0.004, v + h * 0.95, 0.003, (0.55, 0.58, 0.64), 0.8)
        c.poly([(x - 0.0065, v + h), (x + 0.0065, v + h), (x + 0.0065 + dx, v + h + dy), (x - 0.0065 + dx, v + h + dy)], (0.16, 0.17, 0.20), lift=0)
    if scraps:
        for _ in range(4):
            x = u + rng.uniform(-w * 0.5, w * 0.5)
            y = v + rng.uniform(0.2, 0.9) * h
            c.poly([(x, y), (x + 0.04, y + 0.008), (x + 0.05, y - 0.008), (x + 0.005, y - 0.012)], (0.94, 0.93, 0.90), lift=0.1)
    soft_disc(c, u + w * 0.35, v + h * 0.5, w * 0.30, h * 0.65, BLACK, 0.12, 1.3)


@sprop("svc_scrap_bales", aspect=1.72, fill=0.63)
def svc_scrap_bales(c, P):
    """Three bales of pressed cardboard stacked two and one, tied with steel straps, a loose sheet on the ground."""
    rng = c.rng
    c = c.sub(-0.10, 0.0, 1.0)
    base = mix(CARD_C, P.accent, 0.05)
    _bale(c, -0.23, 0.0, 0.43, 0.28, 0.09, 0.07, scale(base, 0.96), rng, straps=3)
    _bale(c, 0.23, 0.0, 0.43, 0.28, 0.09, 0.07, scale(base, 1.04), rng, straps=3)
    _bale(c, -0.0, 0.28, 0.45, 0.28, 0.09, 0.07, scale(base, 1.0), rng, straps=3)
    c.poly([(0.52, 0.0), (0.64, 0.012), (0.60, 0.04), (0.50, 0.03)], (0.93, 0.92, 0.88), lift=0.1)


@sprop("svc_scrap_scale", aspect=1.59, fill=0.80)
def svc_scrap_scale(c, P):
    """A platform weighing scale with a diamond-plate deck, a post with a display unit (bars only) and a bundle of copper pipe on it."""
    c = c.sub(-0.13, 0.0, 1.0)
    rng = c.rng
    steel = (0.60, 0.63, 0.68)
    _prism(c, -0.05, 0.0, 0.90, 0.07, 0.13, 0.12, scale(steel, 0.9), top=scale(steel, 1.15), side=scale(steel, 0.55), lift=0.1)
    for k in range(14):                                                                                    # diamond plate on the deck
        x = -0.48 + k * 0.066
        c.line(x, 0.072, x + 0.03, 0.188, 0.006, scale(steel, 1.35), 0.5)
        c.line(x + 0.03, 0.072, x, 0.188, 0.004, scale(steel, 0.85), 0.4)
    c.rect(-0.05, 0.015, 0.90, 0.012, scale(steel, 0.6), lift=0, alpha=0.7)
    c.rect(-0.05, 0.065, 0.90, 0.010, mix(steel, WHITE, 0.55), lift=0, alpha=0.8)
    for x in (-0.45, 0.35):
        c.circle(x, 0.035, 0.013, (0.15, 0.16, 0.19), lift=0.2)
    # post and the display
    c.rect(0.60, 0.18, 0.04, 0.34, scale(steel, 0.8), lift=0.1)
    _path(c, [(0.60, 0.34), (0.63, 0.36), (0.66, 0.40)], 0.020, scale(steel, 0.65), 1.0)
    c.rect(0.62, 0.70, 0.30, 0.20, (0.13, 0.15, 0.18), r=0.02, lift=0.14)
    c.rect(0.62, 0.74, 0.24, 0.075, (0.55, 0.78, 0.60), r=0.01, lift=0.1)
    for k in range(4):
        c.rect(0.55 + k * 0.045, 0.74, 0.030, 0.045, (0.12, 0.25, 0.15), lift=0, alpha=0.85)               # bar-style readout
    for k in range(4):
        c.circle(0.52 + k * 0.060, 0.65, 0.012, (0.75, 0.8, 0.85) if k != 1 else YELLOW, lift=0.2)
    c.line(0.52, 0.80 + 0.0, 0.52, 0.80, 0.0, WHITE)
    soft_disc(c, 0.62, 0.74, 0.20, 0.14, (0.6, 0.9, 0.7), 0.20, 1.4, add=True)
    # copper pipe bundle on the deck
    cu = (0.88, 0.50, 0.28)
    for k, (u, v) in enumerate(((-0.34, 0.20), (-0.20, 0.20), (-0.06, 0.20), (-0.27, 0.27), (-0.13, 0.27), (-0.20, 0.34))):
        _tube(c, u - 0.14, v, u + 0.30, v + 0.01, 0.052, scale(cu, 0.92 + 0.05 * (k % 3)), 0.5)
        c.ellipse(u + 0.30, v + 0.01, 0.014, 0.026, scale(cu, 0.45), lift=0)
    c.rect(-0.02, 0.28, 0.018, 0.17, (0.14, 0.15, 0.18), lift=0, alpha=0.9)                              # strap
    # a steel drum behind
    _cyl(c, 0.30, 0.19, 0.12, 0.22, (0.30, 0.45, 0.62), dark=0.5)
    c.rect(0.30, 0.32, 0.24, 0.012, scale((0.30, 0.45, 0.62), 0.6), lift=0, alpha=0.8)


@sprop("svc_scrap_metal", aspect=2.96, fill=0.50)
def svc_scrap_metal(c, P):
    """Sorted metal scrap: a copper coil, brass fittings, aluminium sheet, a steel beam, a rusty gear and pipes."""
    rng = c.rng
    rust = (0.62, 0.34, 0.20)
    alu = (0.80, 0.83, 0.87)
    # aluminium sheet leaning
    c.poly([(0.38, 0.0), (0.76, 0.02), (0.66, 0.46), (0.36, 0.50)], alu, lift=0.20)
    c.poly([(0.38, 0.0), (0.46, 0.0), (0.40, 0.49), (0.36, 0.50)], WHITE, alpha=0.5, lift=0)
    c.line(0.52, 0.04, 0.50, 0.46, 0.006, scale(alu, 0.75), 0.6)
    # steel beam lying and a rusty pipe
    c.poly([(-0.72, 0.0), (-0.10, 0.0), (-0.10, 0.045), (-0.72, 0.045)], scale((0.52, 0.55, 0.60), 0.8), lift=0.2)
    c.poly([(-0.72, 0.045), (-0.10, 0.045), (-0.14, 0.06), (-0.68, 0.06)], scale((0.55, 0.58, 0.64), 1.2), lift=0.1)
    c.rect(-0.41, 0.025, 0.62, 0.008, rust, lift=0, alpha=0.5)
    _tube(c, -0.60, 0.11, 0.00, 0.14, 0.075, rust, 0.35)
    c.ellipse(0.0, 0.14, 0.022, 0.042, (0.12, 0.08, 0.06), lift=0)
    for _ in range(18):
        c.circle(rng.uniform(-0.60, 0.0), rng.uniform(0.09, 0.17), rng.uniform(0.004, 0.010), scale(rust, rng.uniform(0.7, 1.2)), lift=0, alpha=0.7)
    # copper coil
    cu = (0.90, 0.52, 0.30)
    for k in range(5):
        c.ellipse(-0.12, 0.10 + k * 0.034, 0.21, 0.21 * TILT, scale(cu, 0.55), lift=0)
        c.ellipse(-0.12, 0.106 + k * 0.034, 0.21, 0.21 * TILT, cu, lift=0.2)
        c.ellipse(-0.12, 0.116 + k * 0.034, 0.15, 0.15 * TILT, scale(cu, 0.5), lift=0, alpha=0.9)
    c.ellipse(-0.12, 0.27, 0.21, 0.21 * TILT, mix(cu, WHITE, 0.1), lift=0.2)
    c.ellipse(-0.12, 0.275, 0.14, 0.14 * TILT, scale(cu, 0.4), lift=0)
    gloss(c, -0.22, 0.30, 0.08, 0.012, 0, 0.7)
    # brass fittings
    for (u, v, a) in ((0.12, 0.05, 20), (0.22, 0.12, -30), (0.14, 0.18, 70)):
        _tube(c, u, v, u + 0.14 * math.cos(math.radians(a)), v + 0.14 * math.sin(math.radians(a)), 0.045, BRASS, 0.55)
        c.circle(u, v, 0.032, scale(BRASS, 0.8), lift=0.25)
        c.circle(u, v, 0.014, (0.2, 0.15, 0.1), lift=0)
    # rusty gear
    gu, gv, gr = 0.58, 0.10, 0.12
    for k in range(10):
        ang = math.radians(k * 36)
        c.poly(_rot([(-0.02, gr * 0.85), (0.02, gr * 0.85), (0.017, gr * 1.18), (-0.017, gr * 1.18)], math.degrees(ang) - 90 + 90, gu, gv), scale(rust, 0.9), lift=0.15) if False else None
        x, y = gu + math.cos(ang) * gr * 1.02, gv + math.sin(ang) * gr * 1.02 * 1.0
        c.circle(x, y, 0.026, scale(rust, 0.85), lift=0.2)
    c.circle(gu, gv, gr, rust, lift=0.22)
    c.circle(gu, gv, gr * 0.62, scale(rust, 0.55), lift=0.1)
    c.circle(gu, gv, gr * 0.20, (0.18, 0.14, 0.12), lift=0)
    for _ in range(10):
        c.circle(gu + rng.uniform(-gr, gr) * 0.8, gv + rng.uniform(-gr, gr) * 0.8, rng.uniform(0.004, 0.010), scale(rust, rng.uniform(0.6, 1.3)), lift=0, alpha=0.6)


@sprop("svc_scrap_ewaste", aspect=1.93, fill=0.81)
def svc_scrap_ewaste(c, P):
    """Old electronics for recycling: a beige PC tower, a keyboard, a circuit board, loose cells and tangled cables."""
    rng = c.rng
    beige = (0.84, 0.81, 0.72)
    c = c.sub(-0.14, 0.0, 1.0)
    # tower
    _prism(c, -0.10, 0.0, 0.36, 0.72, 0.11, 0.09, beige, top=mix(beige, WHITE, 0.3), side=scale(beige, 0.68), lift=0.07, r=0.01)
    for k in range(2):
        c.rect(-0.10, 0.58 - k * 0.10, 0.28, 0.065, scale(beige, 0.78), lift=0.1, r=0.006)
        c.rect(-0.10, 0.585 - k * 0.10, 0.22, 0.012, (0.10, 0.10, 0.12), lift=0, alpha=0.85)
    c.rect(-0.10, 0.36, 0.28, 0.07, scale(beige, 0.9), lift=0.1, r=0.006)
    c.circle(-0.22, 0.36, 0.016, (0.3, 0.7, 0.4), lift=0.2)
    c.circle(0.02, 0.36, 0.022, scale(beige, 0.7), lift=0.2)
    for k in range(7):
        c.rect(-0.10, 0.20 - k * 0.018, 0.22, 0.007, scale(beige, 0.6), lift=0, alpha=0.8)
    # cracked monitor-ish panel leaning on the tower: dark glass
    c.poly([(0.16, 0.02), (0.62, 0.02), (0.62, 0.40), (0.16, 0.44)], (0.15, 0.17, 0.20), lift=0.18)
    c.poly([(0.20, 0.06), (0.58, 0.06), (0.58, 0.36), (0.20, 0.40)], (0.22, 0.28, 0.33), lift=0.1)
    c.line(0.30, 0.38, 0.46, 0.12, 0.004, WHITE, 0.55)
    c.line(0.46, 0.12, 0.54, 0.14, 0.003, WHITE, 0.4)
    c.poly([(0.20, 0.06), (0.30, 0.06), (0.36, 0.38), (0.20, 0.40)], WHITE, alpha=0.12, lift=0)
    # keyboard
    c.poly([(-0.52, 0.0), (0.06, 0.0), (0.12, 0.05), (-0.46, 0.05)], (0.80, 0.80, 0.78), lift=0.1)
    for r in range(3):
        for k in range(11):
            x0 = -0.50 + k * 0.050 + r * 0.012
            y0 = 0.008 + r * 0.013
            c.rect(x0, y0 + 0.01, 0.036, 0.009, scale((0.8, 0.8, 0.78), 0.62), lift=0, alpha=0.8)
    # circuit board
    c.poly([(0.40, 0.02), (0.88, 0.0), (0.92, 0.14), (0.44, 0.17)], (0.12, 0.45, 0.28), lift=0.15)
    for k in range(6):
        c.line(0.46 + k * 0.07, 0.06 + 0.004 * k, 0.54 + k * 0.07, 0.12, 0.004, (0.92, 0.78, 0.35), 0.8)
    for (x, y, w) in ((0.52, 0.10, 0.07), (0.70, 0.08, 0.09), (0.82, 0.10, 0.05)):
        c.rect(x, y, w, w * 0.8, (0.08, 0.08, 0.10), lift=0.2, r=0.004)
        c.rect(x, y + w * 0.3, w * 0.8, 0.004, (0.5, 0.5, 0.55), lift=0, alpha=0.7)
    # loose cells and cables
    for k, col in enumerate(((0.92, 0.80, 0.20), (0.25, 0.60, 0.30), (0.75, 0.77, 0.80))):
        _cyl(c, -0.62 + k * 0.07, 0.015 + 0.012 * k, 0.026, 0.09, col, dark=0.55, lip=False)
    _path(c, [(-0.55, 0.02), (-0.30, -0.02), (-0.12, 0.05), (0.18, 0.0), (0.30, 0.05)], 0.014, (0.08, 0.08, 0.10), 1.0)
    _path(c, [(-0.50, 0.01), (-0.36, 0.06), (-0.22, 0.01)], 0.012, (0.55, 0.15, 0.12), 1.0)


@sprop("svc_scrap_plastic", aspect=2.08, fill=0.53)
def svc_scrap_plastic(c, P):
    """A pressed bale of plastic bottles in mixed colours, tied with wire, and a few loose bottles."""
    c = c.sub(-0.11, 0.0, 1.0)
    rng = c.rng
    w, h, dx, dy = 0.78, 0.44, 0.12, 0.09
    _prism(c, -0.05, 0.0, w, h, dx, dy, (0.78, 0.86, 0.92), top=(0.90, 0.95, 0.98), side=(0.42, 0.52, 0.62), lift=0.04)
    cols = ((0.45, 0.72, 0.92), (0.96, 0.96, 0.97), (0.40, 0.78, 0.52), (0.95, 0.72, 0.30), (0.62, 0.86, 0.94), (0.85, 0.45, 0.42))
    x0, y0 = -0.05 - w / 2, 0.0
    for r in range(8):
        for k in range(12):
            u = x0 + (k + 0.5) * w / 12.0 + rng.uniform(-0.006, 0.006)
            v = y0 + (r + 0.5) * h / 8.0 + rng.uniform(-0.004, 0.004)
            col = cols[rng.randrange(len(cols))]
            ang = rng.uniform(-14, 14)
            c.poly(_rot([(-0.025, -0.022), (0.022, -0.022), (0.024, 0.022), (-0.025, 0.022)], ang, u, v), scale(col, rng.uniform(0.85, 1.05)), lift=0.2, alpha=0.95)
            c.poly(_rot([(0.020, -0.012), (0.038, -0.008), (0.038, 0.008), (0.020, 0.012)], ang, u, v), scale(col, 0.75), lift=0.1)
    soft_disc(c, 0.28, 0.22, 0.12, 0.30, BLACK, 0.18, 1.3)
    for k in range(3):                                                                                     # wire ties
        x = -0.35 + k * 0.30
        c.rect(x, h / 2, 0.010, h, (0.16, 0.17, 0.2), lift=0.1)
        c.poly([(x - 0.005, h), (x + 0.005, h), (x + 0.005 + dx, h + dy), (x - 0.005 + dx, h + dy)], (0.16, 0.17, 0.2), lift=0)
    # loose bottles in front
    for u, col, a in ((0.50, cols[0], 80), (0.62, cols[2], 70), (0.56, cols[1], 98)):
        p = _rot([(0.0, 0.0)], a, u, 0.04)[0]
        c.poly(_rot([(-0.07, -0.026), (0.06, -0.026), (0.075, -0.012), (0.075, 0.012), (0.06, 0.026), (-0.07, 0.026)], a - 90 + 90, u, 0.04 + 0.0), col, lift=0.25, alpha=0.95)
        c.circle(u + 0.075 * math.cos(math.radians(a - 90 + 90)), 0.04, 0.012, scale(col, 0.6), lift=0.1)


@sprop("svc_scrap_truck", aspect=2.1, fill=0.95)
def svc_scrap_truck(c, P):
    """A pickup truck in side view, heaped with bales, metal and a crate, tied down with rope."""
    rng = c.rng
    body = P.accent
    dark = (0.12, 0.13, 0.16)
    # load first (behind the bed side): bales and scrap
    _bale(c, -0.52, 0.34, 0.34, 0.22, 0.0, 0.0, CARD_C, rng, straps=3, scraps=False)
    _bale(c, -0.17, 0.34, 0.34, 0.22, 0.0, 0.0, scale(CARD_C, 1.05), rng, straps=3, scraps=False)
    _bale(c, -0.35, 0.56, 0.34, 0.22, 0.0, 0.0, scale(CARD_C, 0.95), rng, straps=3, scraps=False)
    c.poly([(-0.78, 0.40), (-0.60, 0.52), (-0.74, 0.62)], (0.62, 0.65, 0.70), lift=0.2)                    # sheet metal
    for k in range(4):
        _tube(c, -0.02 + k * 0.0, 0.40 + k * 0.045, 0.14, 0.43 + k * 0.045, 0.045, (0.88, 0.50, 0.28), 0.5)
    c.rect(0.0, 0.69, 0.0, 0.0, WHITE)
    _path(c, [(-0.80, 0.50), (-0.35, 0.80), (0.10, 0.52)], 0.010, (0.78, 0.66, 0.42), 1.0)                  # rope over the load
    _path(c, [(-0.55, 0.40), (-0.30, 0.80), (0.0, 0.42)], 0.008, (0.78, 0.66, 0.42), 0.9)
    # chassis, bed side and cab
    c.rect(0.0, 0.18, 1.78, 0.10, dark, r=0.03, lift=0.1)
    c.poly([(-0.88, 0.20), (0.14, 0.20), (0.14, 0.46), (-0.88, 0.46)], scale(body, 0.92), lift=0.18)
    c.rect(-0.37, 0.455, 1.02, 0.025, scale(body, 1.18), lift=0.1)
    c.rect(-0.37, 0.30, 1.0, 0.012, scale(body, 0.58), lift=0, alpha=0.7)
    c.poly([(0.14, 0.20), (0.14, 0.62), (0.30, 0.78), (0.58, 0.78), (0.70, 0.54), (0.90, 0.50), (0.92, 0.20)], body, lift=0.22)
    c.poly([(0.30, 0.70), (0.56, 0.70), (0.63, 0.54), (0.22, 0.54)], (0.58, 0.78, 0.92), lift=0.25, alpha=0.95)
    c.poly([(0.30, 0.70), (0.38, 0.70), (0.30, 0.54), (0.22, 0.54)], WHITE, alpha=0.40, lift=0)
    c.line(0.40, 0.52, 0.40, 0.24, 0.006, scale(body, 0.55), 0.8)
    c.rect(0.36, 0.45, 0.05, 0.012, scale(body, 0.5), lift=0)
    c.rect(0.55, 0.40, 0.55, 0.012, mix(body, WHITE, 0.4), lift=0, alpha=0.6)
    c.rect(0.80, 0.28, 0.18, 0.07, scale(dark, 1.2), lift=0.2, r=0.01)                                    # grille
    c.rect(0.84, 0.44, 0.07, 0.05, (1.0, 0.96, 0.8), lift=0.2)
    c.glow(0.90, 0.44, 0.16, (1.0, 0.92, 0.7), 0.5)
    c.rect(0.94, 0.20, 0.10, 0.05, scale(dark, 1.6), lift=0.2, r=0.01)                                    # bumper
    # wheels
    for x in (-0.55, 0.52):
        c.circle(x, 0.14, 0.16, (0.06, 0.06, 0.08), lift=0)
        c.circle(x, 0.14, 0.125, (0.10, 0.10, 0.12), lift=0.1)
        c.circle(x, 0.14, 0.072, (0.72, 0.75, 0.80), lift=0.25)
        c.circle(x, 0.14, 0.028, (0.3, 0.32, 0.36), lift=0.1)
        for k in range(5):
            a = math.radians(k * 72 + 18)
            c.circle(x + math.cos(a) * 0.045, 0.14 + math.sin(a) * 0.045, 0.008, (0.3, 0.32, 0.36), lift=0)
        gloss(c, x - 0.04, 0.19, 0.04, 0.012, 20, 0.5)
    gloss(c, 0.40, 0.76, 0.14, 0.014, -10, 0.5)
    soft_disc(c, 0.0, 0.32, 0.9, 0.10, BLACK, 0.10, 1.4)


@niche("scrap-recycling", "Scrap and recycling", subjects=("svc_scrap_bales",),
       strong=("scrap dealer", "scrap yard", "scrap and recycling", "scrap recycling", "scrap metal", "metal scrap", "recycling centre", "recycling center", "recycling plant", "kabadi",
               "kabadiwala", "kabadi wala", "scrap", "raddi", "raddiwala", "old newspaper", "waste paper", "paper and cardboard", "electronic waste", "industrial scrap",
               "metal recycling", "plastic recycling", "bhangar", "bhangar wala", "junkyard", "junk yard", "old iron buyer", "e waste", "e-waste", "कबाड़ी", "कबाड़ीवाला",
               "रद्दी", "भंगार", "कबाड़", "स्क्रैप", "रीसाइक्लिंग", "ई-वेस्ट", "ई वेस्ट"),
       weak=("recycling", "recycle", "metal", "bales", "cardboard", "plastic", "waste", "junk", "e waste", "कचरा"),
       accent="#4a7c2b", mood="warm", group="services",
       avoid=("packers and movers", "courier", "waste management software", "garbage truck", "taxi", "agriculture", "farm", "furniture shop", "car showroom"))
def scrap_recycling(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    sheet = mix(P.wall_bot, (0.62, 0.66, 0.68), 0.45) if not dk else scale(mix(P.accent_dark, (0.4, 0.42, 0.45), 0.5), 0.55)
    dirt = mix(P.floor_top, (0.62, 0.58, 0.50), 0.55) if not dk else scale(P.floor_top, 0.9)
    with S.far():
        S.wall(P.wall_top, mix(P.wall_bot, WHITE, 0.2), 0.70)
        # corrugated warehouse: ribbed sheet wall, a sliding door, a roof line and a chimney / crane silhouette
        S.gradient_rect(-5.0, 0.20, 7.0, 0.66, scale(sheet, 1.12), scale(sheet, 0.86))
        for k in range(70):
            S.rect(-4.9 + k * 0.10, 0.43, 0.012, 0.46, scale(sheet, 0.72), lift=0.0, alpha=0.45)
            S.rect(-4.86 + k * 0.10, 0.43, 0.006, 0.46, mix(sheet, WHITE, 0.4), lift=0.0, alpha=0.35)
        S.rect(0.55, 0.45, 0.62, 0.44, scale(sheet, 0.48), r=0.01, lift=0.0)
        S.rect(0.55, 0.45, 0.60, 0.015, mix(sheet, WHITE, 0.4), lift=0.0, alpha=0.6)
        S.rect(1.0, 0.20, 12.0, 0.04, scale(sheet, 0.6), lift=0.0)
        S.rect(1.85, 0.08, 0.05, 0.30, scale(sheet, 0.60), lift=0.0)
        S.rect(1.85, -0.07, 0.30, 0.03, scale(sheet, 0.60), lift=0.0)
        S.glow(1.2, 0.20, 1.2, P.light, 0.24 if not dk else 0.36)
        S.rect(1.0, 0.665, 14.0, 0.03, scale(sheet, 0.45), lift=0.0)
        S.floor(0.68, dirt, scale(dirt, 0.78))
    # packed earth / concrete yard: stains, gravel and tyre tracks
    S.floor(0.68, mix(dirt, WHITE, 0.06), scale(dirt, 0.66))
    for _ in range(5):
        S.rect(rng.uniform(-0.2, 2.2), rng.uniform(0.74, 1.3), rng.uniform(0.3, 0.7), rng.uniform(0.03, 0.07), scale(dirt, 0.6), r=0.03, alpha=0.25, lift=0, soft=18)
    for _ in range(130):
        S.circle(rng.uniform(-0.2, 2.2), rng.uniform(0.70, 1.35), rng.uniform(0.002, 0.006), scale(dirt, rng.uniform(0.6, 1.3)), lift=0, alpha=0.7)
    S.line(-0.2, 1.05, 2.2, 1.0, 0.03, scale(dirt, 0.8), 0.25)
    S.line(-0.2, 1.14, 2.2, 1.10, 0.03, scale(dirt, 0.8), 0.22)
    S.soft(1.10, 0.90, 0.60, 0.14, P.light, 0.32 if not dk else 0.26, 1.4, add=True)
    S.put("svc_scrap_truck", 1.29, 0.75, 0.33, color=P)
    S.put("svc_scrap_ewaste", 1.12, 0.84, 0.25, color=P)
    S.put("svc_scrap_bales", 0.85, 0.92, 0.38, color=P, subject=True)
    S.put("svc_scrap_scale", 1.36, 0.98, 0.27, color=P)
    S.put("svc_scrap_metal", 0.62, 0.99, 0.14, color=P)
    S.put("svc_scrap_plastic", 1.06, 1.00, 0.14, color=P, framed=False)
    S.focus("detail", 1.10, 0.88)
    with S.near():
        S.ellipse(0.38, 1.18, 0.14, 0.05, scale(dirt, 0.7), -8, 0.5)
        S.circle(1.88, 1.12, 0.08, mix(P.accent, WHITE, 0.2), 0.5)


# ====================================================================================================== funeral services
MARI = (0.98, 0.62, 0.10)


def _bloom(c, u, v, r, col, n=9, tilt=0.62, core=(0.98, 0.82, 0.30), width=0.30):
    """A flower seen from a raised angle: petals around a centre, back petals first."""
    ang = [k * 360.0 / n for k in range(n)]
    for th in sorted(ang, key=lambda a: -math.sin(math.radians(a))):
        t = math.radians(th)
        d = r * 0.52
        pu, pv = u + math.cos(t) * d, v + math.sin(t) * d * tilt
        rot = math.degrees(math.atan2(math.sin(t) * tilt, math.cos(t)))
        shade = 0.88 + 0.14 * math.sin(t)
        c.ellipse(pu, pv, r * 0.52, r * width * (0.7 + 0.3 * abs(math.cos(t))) * 1.0, scale(col, shade), rot, lift=0.12)
    c.ellipse(u, v, r * 0.20, r * 0.20 * tilt, core, lift=0.2)


def _flame(c, u, v, h, glow=0.6):
    """A candle / lamp flame with a warm glow around it."""
    soft_disc(c, u, v + h * 0.4, h * 2.6, h * 2.6, (1.0, 0.78, 0.38), 0.42 * glow, 1.6, add=True)
    soft_disc(c, u, v + h * 0.45, h * 1.0, h * 1.2, (1.0, 0.86, 0.5), 0.55 * glow, 1.4, add=True)
    c.poly([(u - h * 0.20, v), (u + h * 0.20, v), (u + h * 0.16, v + h * 0.45), (u, v + h), (u - h * 0.16, v + h * 0.45)], (1.0, 0.62, 0.16), lift=0.1, alpha=0.95)
    c.poly([(u - h * 0.11, v + h * 0.04), (u + h * 0.11, v + h * 0.04), (u + h * 0.08, v + h * 0.42), (u, v + h * 0.70), (u - h * 0.08, v + h * 0.42)], (1.0, 0.92, 0.62), lift=0.1)
    c.circle(u, v + h * 0.10, h * 0.11, (0.55, 0.75, 0.98), lift=0, alpha=0.8)


@sprop("svc_fn_urn", aspect=0.71, fill=1.0)
def svc_fn_urn(c, P):
    """A brass ashes urn (kalash) with a wide lip and lid, a white cloth tied at the neck and a marigold garland on the shoulder."""
    rng = c.rng
    br = BRASS
    # foot and body
    c.ellipse(0.0, 0.03, 0.17, 0.17 * TILT, scale(br, 0.5), lift=0)
    c.rect(0.0, 0.05, 0.30, 0.07, scale(br, 0.80), lift=0.2, r=0.02)
    c.ellipse(0.0, 0.36, 0.35, 0.31, scale(br, 0.55), lift=0)
    c.ellipse(-0.03, 0.385, 0.315, 0.285, br, lift=0.20)
    soft_disc(c, 0.20, 0.30, 0.20, 0.32, BLACK, 0.34, 1.3)
    soft_disc(c, -0.14, 0.50, 0.14, 0.12, WHITE, 0.55, 1.3, add=True)
    for k, (lat, a) in enumerate(((-0.55, 0.60), (-0.15, 0.80), (0.28, 0.80))):                                # engraved bands that follow the curve
        rx = 0.32 * math.cos(math.asin(max(-0.95, min(0.95, lat))))
        arc(c, 0.0, 0.36 + lat * 0.30, rx, rx * 0.30, 200, 340, 0.007, scale(br, 0.55), 0.8, 12)
        arc(c, 0.0, 0.36 + lat * 0.30 + 0.012, rx, rx * 0.30, 200, 340, 0.004, mix(br, WHITE, 0.55), 0.6, 12)
    # neck, lip and lid
    hshade_box(c, 0.0, 0.73, 0.19, 0.16, mix(br, WHITE, 0.15), scale(br, 0.55))
    c.ellipse(0.0, 0.82, 0.22, 0.22 * TILT, scale(br, 0.6), lift=0)
    hshade_box(c, 0.0, 0.84, 0.44, 0.04, mix(br, WHITE, 0.1), scale(br, 0.6), r=0.012)
    disc(c, 0.0, 0.86, 0.22, mix(br, WHITE, 0.08), TILT, 0.1)
    c.ellipse(0.0, 0.875, 0.14, 0.14 * TILT, scale(br, 0.9), lift=0.1)
    c.circle(0.0, 0.90, 0.060, scale(br, 1.05), lift=0.25)
    c.line(0.0, 0.94, 0.0, 0.985, 0.014, scale(br, 0.85))
    c.circle(0.0, 0.99, 0.014, mix(br, WHITE, 0.4), lift=0.2)
    # white cloth wrapped on the neck with a navy ribbon
    c.poly([(-0.12, 0.80), (0.12, 0.80), (0.20, 0.62), (0.08, 0.60), (0.0, 0.64), (-0.08, 0.60), (-0.20, 0.62)], (0.97, 0.97, 0.98), lift=0.12)
    c.poly([(-0.20, 0.62), (-0.12, 0.80), (-0.05, 0.64)], (0.86, 0.87, 0.9), lift=0, alpha=0.6)
    c.rect(0.0, 0.73, 0.26, 0.030, P.accent, lift=0.2, r=0.008)
    c.poly([(0.0, 0.725), (0.07, 0.62), (0.10, 0.64), (0.04, 0.73)], scale(P.accent, 1.1), lift=0.15)
    # garland across the shoulder
    for k in range(15):
        t = k / 14.0
        u = -0.30 + 0.60 * t
        v = 0.55 - 0.15 * math.sin(math.pi * t) + 0.12 * (abs(t - 0.5) * 2) ** 2 * 0.0
        r = 0.042
        c.circle(u, v - 0.012, r, scale(MARI, 0.72), lift=0, alpha=0.9)
        _bloom(c, u, v, r * 1.35, MARI if k % 3 else (0.99, 0.74, 0.18), n=7, tilt=0.75, core=(0.85, 0.40, 0.08))
    c.rect(-0.22, 0.44, 0.0, 0.0, WHITE)


@sprop("svc_fn_flowers", aspect=0.86, fill=1.09)
def svc_fn_flowers(c, P):
    """A white ceramic vase with white chrysanthemums, lilies, marigolds and green leaves."""
    c = c.sub(0.02, 0.0, 1.0)
    rng = c.rng
    ceramic = (0.95, 0.95, 0.93)
    # leaves behind
    for ang, ln, u in ((150, 0.40, -0.08), (115, 0.46, -0.02), (60, 0.44, 0.06), (30, 0.38, 0.12), (172, 0.30, -0.12), (8, 0.30, 0.14)):
        _leaf(c, u, 0.46, ln, ang, (0.22, 0.48, 0.28), 0.34)
    # vase
    c.ellipse(0.0, 0.03, 0.16, 0.16 * TILT, scale(ceramic, 0.6), lift=0)
    c.poly([(-0.16, 0.03), (0.16, 0.03), (0.23, 0.22), (0.19, 0.38), (0.12, 0.46), (-0.12, 0.46), (-0.19, 0.38), (-0.23, 0.22)], ceramic, lift=0.12)
    soft_disc(c, 0.15, 0.22, 0.10, 0.22, BLACK, 0.26, 1.3)
    c.rect(0.0, 0.30, 0.42, 0.030, P.accent, lift=0.15, alpha=0.9)
    c.rect(0.0, 0.26, 0.42, 0.008, mix(P.accent, WHITE, 0.4), lift=0, alpha=0.8)
    gloss(c, -0.12, 0.26, 0.02, 0.15, 0, 0.6)
    c.ellipse(0.0, 0.46, 0.13, 0.13 * TILT, scale(ceramic, 0.7), lift=0)
    # blooms: white chrysanthemums (many petals), marigolds and a couple of lilies
    spots = ((-0.20, 0.64, 0.16, "w"), (0.0, 0.76, 0.18, "w"), (0.22, 0.62, 0.16, "w"), (-0.05, 0.58, 0.14, "m"), (0.14, 0.82, 0.12, "m"),
             (-0.24, 0.80, 0.12, "m"), (0.30, 0.76, 0.11, "w"), (-0.34, 0.60, 0.10, "w"), (0.08, 0.96, 0.10, "w"), (-0.14, 0.92, 0.11, "m"))
    for (u, v, r, kind) in spots:
        if kind == "w":
            _bloom(c, u, v, r, (0.98, 0.98, 0.97), n=9, tilt=0.8, core=(0.96, 0.88, 0.45), width=0.26)
            _bloom(c, u, v + 0.005, r * 0.62, (0.93, 0.94, 0.96), n=7, tilt=0.8, core=(0.96, 0.85, 0.40), width=0.28)
        else:
            _bloom(c, u, v, r, MARI, n=12, tilt=0.8, core=(0.80, 0.35, 0.06), width=0.24)
    # a lily with long pointed petals
    for k, a in enumerate((20, 75, 130, 190, 245, 300)):
        _leaf(c, -0.30, 0.90, 0.20, a, (0.99, 0.95, 0.96) if k % 2 else (0.96, 0.90, 0.94), 0.55)
    c.circle(-0.30, 0.90, 0.020, (0.95, 0.72, 0.2), lift=0.2)


@sprop("svc_fn_thali", aspect=1.64, fill=0.75)
def svc_fn_thali(c, P):
    """A brass puja plate: a lit clay lamp, bowls of rice and red kumkum, flower petals, camphor and incense sticks with a thread of smoke."""
    rng = c.rng
    br = BRASS
    # plate
    c.ellipse(0.0, 0.03, 0.62, 0.62 * 0.36, scale(br, 0.5), lift=0)
    c.ellipse(0.0, 0.055, 0.60, 0.60 * 0.34, br, lift=0.16)
    c.ellipse(0.0, 0.065, 0.50, 0.50 * 0.34, scale(br, 0.78), lift=0)
    c.ellipse(0.0, 0.07, 0.48, 0.48 * 0.34, mix(br, WHITE, 0.08), lift=0.12)
    arc(c, 0.0, 0.06, 0.55, 0.55 * 0.34, 195, 345, 0.008, mix(br, WHITE, 0.6), 0.7, 14)
    # bowls: rice and kumkum
    for u, v, r, col, inner in ((-0.28, 0.08, 0.095, br, (0.98, 0.97, 0.94)), (0.28, 0.07, 0.085, br, (0.82, 0.15, 0.12))):
        c.ellipse(u, v, r, r * 0.45, scale(br, 0.5), lift=0)
        hshade_box(c, u, v + 0.035, 2 * r, 0.07, mix(br, WHITE, 0.14), scale(br, 0.55), r=0.012)
        disc(c, u, v + 0.07, r, scale(br, 0.9), 0.45, 0.1)
        c.ellipse(u, v + 0.085, r * 0.82, r * 0.82 * 0.45, inner, lift=0.12)
        if inner[0] > 0.9:
            for _ in range(10):
                c.ellipse(u + rng.uniform(-r * 0.6, r * 0.6), v + 0.085 + rng.uniform(-0.01, 0.015), 0.011, 0.005, (0.88, 0.86, 0.80), lift=0)
        gloss(c, u - r * 0.5, v + 0.04, r * 0.06, 0.025, 0, 0.5)
    # clay lamp with flame in the middle
    c.ellipse(0.0, 0.08, 0.13, 0.05, scale((0.72, 0.38, 0.20), 0.6), lift=0)
    c.poly([(-0.13, 0.11), (0.13, 0.11), (0.09, 0.07), (0.0, 0.055), (-0.09, 0.07)], (0.78, 0.42, 0.22), lift=0.2)
    c.ellipse(0.0, 0.115, 0.125, 0.045, (0.86, 0.50, 0.28), lift=0.2)
    c.ellipse(0.0, 0.118, 0.095, 0.032, (0.98, 0.78, 0.35), lift=0.1)
    c.line(0.04, 0.125, 0.07, 0.15, 0.010, (0.2, 0.15, 0.1))
    _flame(c, 0.07, 0.15, 0.16)
    # petals scattered
    for _ in range(18):
        u, v = rng.uniform(-0.48, 0.48), rng.uniform(0.04, 0.11)
        c.ellipse(u, v, rng.uniform(0.014, 0.024), 0.009, rng.choice((MARI, (0.96, 0.60, 0.70), (0.99, 0.97, 0.94), (0.95, 0.75, 0.20))), rng.uniform(-30, 30), lift=0.15)
    # incense holder with three sticks and smoke
    c.ellipse(-0.02, 0.11, 0.05, 0.02, scale(br, 0.5), lift=0)
    hshade_box(c, -0.02, 0.14, 0.10, 0.05, mix(br, WHITE, 0.14), scale(br, 0.55), r=0.01)
    c.ellipse(-0.02, 0.17, 0.05, 0.02, scale(br, 0.9), lift=0.1)
    for a in (-12, 2, 14):
        ex, ey = -0.02 + math.sin(math.radians(a)) * 0.40, 0.17 + math.cos(math.radians(a)) * 0.40
        c.line(-0.02, 0.17, ex, ey, 0.008, (0.55, 0.33, 0.18))
        c.circle(ex, ey, 0.007, (1.0, 0.45, 0.15), lift=0.3)
    ex = -0.02 + math.sin(math.radians(2)) * 0.40
    for k in range(10):
        t = k / 9.0
        soft_disc(c, ex + math.sin(t * 5.0) * 0.04 * (0.3 + t), 0.58 + t * 0.30, 0.025 + t * 0.045, 0.03 + t * 0.05, (0.86, 0.87, 0.90), 0.26 * (1 - t) ** 0.9, 1.2)
        soft_disc(c, ex + math.sin(t * 5.0) * 0.04 * (0.3 + t), 0.58 + t * 0.30, 0.015 + t * 0.03, 0.02 + t * 0.04, WHITE, 0.30 * (1 - t) ** 0.9, 1.2)


@sprop("svc_fn_candles", aspect=0.93, fill=0.99)
def svc_fn_candles(c, P):
    """Three cream pillar candles of different heights on a brass tray, with wax drips and warm flames."""
    rng = c.rng
    br = BRASS
    c.ellipse(0.0, 0.03, 0.46, 0.46 * 0.34, scale(br, 0.5), lift=0)
    c.ellipse(0.0, 0.05, 0.44, 0.44 * 0.33, br, lift=0.16)
    c.ellipse(0.0, 0.056, 0.38, 0.38 * 0.33, scale(br, 0.8), lift=0.0)
    wax = (0.98, 0.95, 0.88)
    for u, h, r in ((-0.20, 0.52, 0.095), (0.12, 0.72, 0.105), (0.30, 0.38, 0.080)):
        v0 = 0.07
        c.ellipse(u, v0, r, r * TILT, scale(wax, 0.6), lift=0)
        hshade_box(c, u, v0 + h / 2, 2 * r, h, wax, scale(wax, 0.60))
        c.ellipse(u, v0 + h, r, r * TILT, mix(wax, WHITE, 0.2), lift=0.1)
        c.ellipse(u, v0 + h + 0.004, r * 0.8, r * 0.8 * TILT, (1.0, 0.86, 0.55), lift=0.1, alpha=0.9)
        for k in range(3):                                                                                    # wax drips
            du = rng.uniform(-r * 0.8, r * 0.8)
            ln = rng.uniform(0.04, 0.10)
            c.rect(u + du, v0 + h - ln / 2 - 0.01, 0.020, ln, scale(wax, 1.0), r=0.010, lift=0.1, alpha=0.95)
            c.circle(u + du, v0 + h - ln - 0.005, 0.012, scale(wax, 0.98), lift=0.1)
        c.rect(u - r * 0.6, v0 + h * 0.5, 0.012, h * 0.88, WHITE, lift=0, alpha=0.4)
        c.line(u, v0 + h, u, v0 + h + 0.035, 0.006, (0.15, 0.12, 0.10))
        _flame(c, u, v0 + h + 0.03, 0.12 if h > 0.5 else 0.10)
        soft_disc(c, u, v0 + h * 0.5, r * 1.5, h * 0.5, (1.0, 0.82, 0.5), 0.22, 1.5, add=True)
    for _ in range(10):
        u, v = rng.uniform(-0.40, 0.40), rng.uniform(0.04, 0.09)
        c.ellipse(u, v, 0.016, 0.008, rng.choice((MARI, (0.99, 0.97, 0.94))), rng.uniform(-30, 30), lift=0.15)


@sprop("svc_fn_lotus", aspect=1.90, fill=0.54)
def svc_fn_lotus(c, P):
    """A lotus floating in a shallow brass bowl of water with lily pads and loose petals."""
    rng = c.rng
    br = BRASS
    c.ellipse(0.0, 0.03, 0.50, 0.50 * 0.36, scale(br, 0.5), lift=0)
    c.poly([(-0.50, 0.12), (0.50, 0.12), (0.36, 0.03), (-0.36, 0.03)], mix(br, WHITE, 0.05), lift=0.2)
    hshade_box(c, 0.0, 0.075, 1.0, 0.09, mix(br, WHITE, 0.15), scale(br, 0.5), r=0.02, alpha=0.55)
    c.ellipse(0.0, 0.12, 0.51, 0.51 * 0.36, mix(br, WHITE, 0.1), lift=0.1)
    c.ellipse(0.0, 0.125, 0.47, 0.47 * 0.34, scale(br, 0.5), lift=0)
    c.ellipse(0.0, 0.13, 0.45, 0.45 * 0.33, mix((0.40, 0.62, 0.72), P.accent, 0.3), lift=0.15, alpha=0.95)
    for k in range(3):
        arc(c, -0.12, 0.13, 0.12 + 0.12 * k, (0.12 + 0.12 * k) * 0.33, 15, 345, 0.004, WHITE, 0.45 - 0.1 * k, 12)
    for (u, v, r) in ((-0.30, 0.16, 0.10), (0.30, 0.13, 0.09), (0.18, 0.20, 0.07)):                              # lily pads
        c.ellipse(u, v, r, r * 0.34, (0.20, 0.45, 0.28), lift=0.2)
        c.poly([(u, v), (u + r * 0.9, v + r * 0.10), (u + r * 0.9, v - r * 0.10)], mix((0.40, 0.62, 0.72), WHITE, 0.0), alpha=0.0)
    # lotus: back petals, front petals, golden centre
    pink, pale = (0.96, 0.62, 0.74), (0.99, 0.90, 0.93)
    for k, a in enumerate((100, 70, 130, 40, 160, 20, 175)):
        _leaf(c, -0.02, 0.20, 0.34 - 0.03 * (k % 2), a, scale(pink, 0.86 + 0.04 * (k % 3)), 0.46)
    for k, a in enumerate((110, 85, 60, 135, 160)):
        _leaf(c, -0.02, 0.19, 0.30, a, mix(pink, pale, 0.5 + 0.1 * (k % 3)), 0.48)
    for k, a in enumerate((95, 75, 115)):
        _leaf(c, -0.02, 0.19, 0.22, a, pale, 0.52)
    c.ellipse(-0.02, 0.27, 0.04, 0.025, (0.98, 0.82, 0.25), lift=0.2)
    for _ in range(8):
        c.circle(rng.uniform(-0.05, 0.02), rng.uniform(0.26, 0.29), 0.006, (0.9, 0.62, 0.15), lift=0)
    for _ in range(6):
        c.ellipse(rng.uniform(-0.40, 0.40), rng.uniform(0.11, 0.17), 0.020, 0.008, rng.choice((pink, pale, MARI)), rng.uniform(-30, 30), lift=0.12)


@niche("funeral-services", "Funeral services", subjects=("svc_fn_urn",),
       strong=("funeral services", "funeral service", "funeral home", "funeral directors", "funeral director", "cremation services", "cremation service", "antim sanskar",
               "antyeshti", "last rites", "final rites", "shav vahan", "shav yatra", "shamshan", "cemetery services", "ashes immersion", "funeral", "cremation", "ashes", "death certificate", "last rites", "burial", "mourning family", "अंतिम संस्कार", "अंत्येष्टि",
               "श्मशान", "शव वाहन", "अस्थि विसर्जन", "क्रिया कर्म", "अंतिम संस्कार सेवा", "दाह संस्कार", "दफन"),
       weak=("condolence", "obituary", "pandit", "ghat", "tribute", "memorial", "departed", "ceremony", "prayer"),
       accent="#1d3557", mood="light", group="services",
       avoid=("wedding", "banquet", "event planner", "florist", "flower shop", "temple", "astrology", "ngo", "funeral home loan", "insurance", "life insurance"))
def funeral_services(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    cloth = mix(P.paper, P.accent_light, 0.16) if not dk else scale(mix(P.paper, P.accent, 0.4), 0.30)
    sky_t = mix(P.accent_light, P.accent, 0.30) if not dk else scale(P.wall_top, 0.9)
    sky_b = mix(P.accent_light, (1.0, 0.88, 0.74), 0.55) if not dk else mix(P.wall_bot, P.accent, 0.35)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # a calm horizon: dusk sky, a large pale moon, layered misty ridges and soft haze
        S.gradient_rect(-5.0, -0.6, 7.0, 0.66, sky_t, sky_b)
        S.glow(1.35, 0.24, 1.0, mix(P.light, WHITE, 0.4), 0.40 if not dk else 0.50)
        S.circle(1.35, 0.26, 0.13, (1.0, 0.96, 0.82), 0.04)
        for layer, (base, amp, tint, al) in enumerate(((0.50, 0.08, 0.50, 0.55), (0.56, 0.07, 0.70, 0.70), (0.62, 0.04, 0.88, 0.88))):
            col = mix(P.accent_light, P.accent, tint) if not dk else scale(mix(P.accent, P.wall_bot, 0.3), 0.55 - 0.1 * layer)
            pts = [(-4.0, 0.70)]
            u = -4.0
            while u < 6.0:
                pts.append((u, base - rng.uniform(0.0, amp)))
                u += 0.30 + 0.2 * rng.random()
            pts += [(6.0, 0.70)]
            S.poly(pts, col, al)
        for k in range(7):
            S.soft(-0.8 + k * 0.7, 0.60, 0.55, 0.05, mix(P.paper, WHITE, 0.5), 0.40, 1.3, 0, add=True)
        S.floor(0.62, scale(cloth, 0.95), scale(cloth, 0.80))
    # white cloth on the table: smooth folds and a hem line along the back edge
    S.floor(0.66, mix(cloth, WHITE, 0.10), scale(cloth, 0.70))
    S.rect(1.0, 0.655, 14.0, 0.016, scale(cloth, 0.62), lift=0.0)
    S.rect(1.0, 0.670, 14.0, 0.006, mix(cloth, WHITE, 0.6), lift=0.0, alpha=0.9)
    S.rect(1.0, 0.695, 14.0, 0.010, P.accent, lift=0.0, alpha=0.85)
    for k in range(6):
        w = rng.uniform(0.5, 1.2)
        u, v = rng.uniform(-0.2, 2.2), rng.uniform(0.80, 1.30)
        S.rect(u, v, w, 0.03, WHITE, r=0.015, alpha=0.28, lift=0, soft=14)
        S.rect(u + 0.05, v + 0.035, w, 0.022, BLACK, r=0.011, alpha=0.08, lift=0, soft=14)
    S.soft(1.05, 0.88, 0.60, 0.14, P.light, 0.30 if not dk else 0.16, 1.4, add=True)
    S.put("svc_fn_flowers", 0.68, 0.82, 0.42, color=P)
    S.put("svc_fn_candles", 1.37, 0.82, 0.36, color=P)
    S.put("svc_fn_urn", 1.05, 0.92, 0.50, color=P, subject=True)
    S.put("svc_fn_thali", 0.80, 0.98, 0.26, color=P)
    S.put("svc_fn_lotus", 1.30, 0.98, 0.17, color=P)
    S.focus("detail", 1.22, 0.76)
    with S.near():
        S.circle(0.38, 1.16, 0.08, (0.99, 0.78, 0.30), 0.5)
        S.ellipse(1.84, 1.12, 0.12, 0.05, (0.97, 0.97, 0.98), 20, 0.5)


# ====================================================================================================== notary and documentation
INK = (0.18, 0.24, 0.55)
WALNUT = (0.42, 0.25, 0.14)


def _tp(u, v, x, y, ang):
    """Point on a sheet lying flat on a desk, seen from a raised angle: sheet coordinates (x, y) -> picture unit coordinates."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return (u + x * ca - y * sa, v + (x * sa + y * ca) * 0.42)


def _sheet(c, u, v, w, d, ang, col, edge=None):
    """A flat sheet of paper: surface plus a thin darker edge below it for thickness."""
    pts = [_tp(u, v, x, y, ang) for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
    _qpoly(c, [(x, y - 0.008) for x, y in pts], edge or scale(col, 0.70), 0.0)
    _qpoly(c, pts, col, 0.05)


@sprop("svc_nt_stamp", aspect=1.29, fill=0.94)
def svc_nt_stamp(c, P):
    """A wooden rubber stamp with a turned knob, standing next to an open ink pad tin, with a ring-shaped seal impression on a slip."""
    rng = c.rng
    c = c.sub(-0.17, 0.0, 1.0)
    wood = scale(WALNUT, 1.25)
    # ink pad tin (round) with inked felt
    _cyl(c, 0.30, 0.0, 0.30, 0.09, (0.20, 0.22, 0.28), top=(0.28, 0.30, 0.36), dark=0.5)
    c.ellipse(0.30, 0.10, 0.25, 0.25 * TILT, INK, lift=0.15)
    c.ellipse(0.30, 0.105, 0.22, 0.22 * TILT, mix(INK, (0.5, 0.55, 0.9), 0.35), lift=0.12)
    gloss(c, 0.22, 0.12, 0.10, 0.015, 0, 0.7)
    for _ in range(14):
        c.circle(0.30 + rng.uniform(-0.2, 0.2), 0.105 + rng.uniform(-0.04, 0.05), rng.uniform(0.003, 0.006), mix(INK, WHITE, rng.uniform(0.2, 0.5)), lift=0, alpha=0.5)
    # the stamp: block, flared neck, handle, knob
    c.ellipse(-0.20, 0.02, 0.24, 0.24 * TILT, BLACK, alpha=0.3, lift=0)
    _prism(c, -0.20, 0.0, 0.40, 0.11, 0.06, 0.05, scale(wood, 0.9), top=mix(wood, WHITE, 0.22), side=scale(wood, 0.55), lift=0.1, r=0.008)
    c.rect(-0.20, 0.098, 0.40, 0.014, scale(wood, 0.55), lift=0, alpha=0.8)
    c.poly([(-0.30, 0.11), (-0.10, 0.11), (-0.14, 0.20), (-0.26, 0.20)], wood, lift=0.18)
    hshade_box(c, -0.20, 0.50, 0.14, 0.60, mix(wood, WHITE, 0.15), scale(wood, 0.50), r=0.03)
    hshade_box(c, -0.20, 0.55, 0.20, 0.025, mix(WALNUT, WHITE, 0.3), scale(wood, 0.55), r=0.01)
    c.ellipse(-0.20, 0.80, 0.13, 0.13, scale(wood, 0.55), lift=0)
    c.ellipse(-0.215, 0.815, 0.12, 0.12, wood, lift=0.28)
    c.circle(-0.26, 0.86, 0.04, mix(wood, WHITE, 0.45), lift=0.0, alpha=0.7)
    gloss(c, -0.25, 0.45, 0.014, 0.22, 0, 0.55)
    for k in range(3):
        c.rect(-0.20, 0.32 + k * 0.01, 0.15, 0.004, scale(wood, 0.5), lift=0, alpha=0.5)
    # brass band on the handle
    c.rect(-0.20, 0.72, 0.145, 0.03, BRASS, lift=0.3)
    # seal impression on a slip in front: rings and a star, no letters
    _sheet(c, 0.52, -0.04, 0.46, 0.34, -8, (0.98, 0.97, 0.94))
    px_, py_ = _tp(0.52, -0.04, 0.0, 0.0, -8)
    for r, th, a in ((0.15, 0.010, 0.9), (0.115, 0.006, 0.8)):
        arc(c, px_, py_, r, r * 0.42, 0, 360, th, INK, a, 22)
    for k in range(5):
        a0 = math.radians(k * 72 + 90)
        a1 = math.radians(((k + 2) % 5) * 72 + 90)
        c.line(px_ + math.cos(a0) * 0.07, py_ + math.sin(a0) * 0.07 * 0.42, px_ + math.cos(a1) * 0.07, py_ + math.sin(a1) * 0.07 * 0.42, 0.006, INK, 0.85)


@sprop("svc_nt_papers", aspect=4.09, fill=0.23)
def svc_nt_papers(c, P):
    """A stack of agreements on green stamp paper with a certificate on top (navy border, grey lines, signature) and a red wax seal with ribbon."""
    rng = c.rng
    paper = (0.98, 0.97, 0.94)
    stamp_green = (0.78, 0.88, 0.74)
    layers = ((0.0, stamp_green, -4), (0.018, paper, 3), (0.036, (0.95, 0.94, 0.90), -2), (0.054, stamp_green, 2), (0.072, paper, -1))
    for dv, col, ang in layers:
        _sheet(c, 0.0, dv, 0.92, 0.66, ang, col)
    # top sheet: certificate
    top_v = 0.092
    ang = 1
    _sheet(c, 0.0, top_v, 0.92, 0.66, ang, (1.0, 0.99, 0.96))
    def L(x, y):
        return _tp(0.0, top_v, x, y, ang)
    # navy double border
    for inset, th in ((0.03, 0.010), (0.055, 0.004)):
        pts = [L(-0.46 + inset, -0.33 + inset), L(0.46 - inset, -0.33 + inset), L(0.46 - inset, 0.33 - inset), L(-0.46 + inset, 0.33 - inset)]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            c.line(a[0], a[1], b[0], b[1], th, P.accent, 0.9)
    # heading bar and text bars
    a, b = L(-0.20, 0.20), L(0.20, 0.20)
    c.line(a[0], a[1], b[0], b[1], 0.018, scale(P.accent, 1.0), 0.9)
    for k in range(5):
        wl = 0.52 - (0.14 if k == 4 else 0.0) - 0.04 * (k % 2)
        a, b = L(-0.30, 0.08 - k * 0.075), L(-0.30 + wl, 0.08 - k * 0.075)
        c.line(a[0], a[1], b[0], b[1], 0.007, (0.55, 0.58, 0.66), 0.8)
    # signature squiggle
    sig = [L(-0.30 + t * 0.06, -0.21 + (0.03 if k % 2 else -0.0)) for k, t in enumerate(range(8))]
    _path(c, sig, 0.006, (0.10, 0.12, 0.40), 0.95)
    a, b = L(-0.32, -0.245), L(-0.04, -0.245)
    c.line(a[0], a[1], b[0], b[1], 0.004, (0.4, 0.42, 0.5), 0.8)
    # wax seal with ribbon tails
    sx, sy = L(0.26, -0.15)
    c.poly([(sx - 0.03, sy), (sx - 0.075, sy - 0.09), (sx - 0.045, sy - 0.075), (sx - 0.02, sy - 0.10), (sx + 0.0, sy)], P.accent, lift=0.2)
    c.poly([(sx + 0.01, sy), (sx + 0.06, sy - 0.10), (sx + 0.075, sy - 0.07), (sx + 0.045, sy - 0.02)], scale(P.accent, 0.75), lift=0.2)
    c.ellipse(sx, sy + 0.01, 0.085, 0.085 * 0.55, scale((0.62, 0.08, 0.10), 0.7), lift=0)
    c.ellipse(sx, sy + 0.02, 0.082, 0.082 * 0.55, (0.78, 0.12, 0.14), lift=0.22)
    c.ellipse(sx, sy + 0.022, 0.050, 0.050 * 0.55, scale((0.78, 0.12, 0.14), 0.80), lift=0)
    arc(c, sx, sy + 0.022, 0.040, 0.040 * 0.55, 0, 360, 0.005, (0.95, 0.50, 0.45), 0.8, 16)
    soft_disc(c, sx - 0.03, sy + 0.04, 0.025, 0.012, WHITE, 0.6, 1.0, add=True)


@sprop("svc_nt_folders", aspect=1.61, fill=0.88)
def svc_nt_folders(c, P):
    """Legal files: three ring binders standing on a shelf of manila folders, with blank label panels and coloured spines."""
    c = c.sub(-0.13, 0.0, 1.0)
    rng = c.rng
    cols = (P.accent, (0.72, 0.18, 0.20), (0.22, 0.46, 0.34), (0.82, 0.62, 0.30))
    xs = (-0.36, -0.14, 0.09, 0.30)
    hs = (0.74, 0.66, 0.78, 0.60)
    # manila folders lying under
    for k in range(3):
        c.poly([(-0.58, 0.0 + k * 0.03), (0.52, 0.0 + k * 0.03), (0.56, 0.05 + k * 0.03), (-0.54, 0.05 + k * 0.03)], mix((0.92, 0.80, 0.52), WHITE, 0.05 * k), lift=0.1) if False else None
    for k, (x, h, col) in enumerate(zip(xs, hs, cols)):
        w = 0.20
        _prism(c, x, 0.05, w, h, 0.07, 0.05, col, top=mix(col, WHITE, 0.28), side=scale(col, 0.58), lift=0.14, r=0.008)
        c.rect(x, 0.05 + h * 0.62, w * 0.62, h * 0.22, (0.97, 0.96, 0.92), lift=0.04, r=0.006)                  # blank label panel
        c.rect(x, 0.05 + h * 0.62, w * 0.46, 0.008, (0.55, 0.58, 0.66), lift=0, alpha=0.7)
        c.circle(x, 0.05 + h * 0.86, 0.022, (0.80, 0.82, 0.86), lift=0.25)
        c.circle(x, 0.05 + h * 0.86, 0.010, scale(col, 0.4), lift=0)
        c.rect(x - w * 0.42, 0.05 + h * 0.5, 0.012, h * 0.9, WHITE, lift=0, alpha=0.30)
        c.rect(x, 0.05 + h * 0.18, w * 0.9, 0.010, scale(col, 0.62), lift=0, alpha=0.7)
    # a shelf slab and a stack of manila folders with tabs leaning against it
    c.poly([(-0.58, 0.02), (0.52, 0.02), (0.58, 0.07), (-0.52, 0.07)], scale(WALNUT, 1.3), lift=0.1)
    c.rect(-0.03, 0.025, 1.1, 0.045, scale(WALNUT, 1.0), lift=0.1)
    for k in range(4):
        c.poly([(0.40 + 0.01 * k, 0.04 + 0.032 * k), (0.78 + 0.01 * k, 0.05 + 0.032 * k), (0.80 + 0.01 * k, 0.085 + 0.032 * k), (0.42 + 0.01 * k, 0.075 + 0.032 * k)],
               mix((0.92, 0.80, 0.52), (0.85, 0.70, 0.42), k % 2 * 0.6), lift=0.12)
        c.rect(0.50 + 0.1 * k, 0.095 + 0.032 * k, 0.07, 0.016, mix((0.92, 0.80, 0.52), (0.80, 0.62, 0.34), 0.5), lift=0.1)


@sprop("svc_nt_pen", aspect=1.32, fill=0.71)
def svc_nt_pen(c, P):
    """A bottle of navy ink, a fountain pen in a brass-topped wooden stand and a loose pencil."""
    c = c.sub(-0.02, 0.0, 1.0)
    rng = c.rng
    # wooden stand with pen
    _prism(c, -0.28, 0.0, 0.34, 0.10, 0.07, 0.05, scale(WALNUT, 1.2), side=scale(WALNUT, 0.7), lift=0.12, r=0.01)
    c.ellipse(-0.28, 0.105, 0.04, 0.02, (0.06, 0.05, 0.05), lift=0)
    pen = (0.08, 0.10, 0.18)
    c.poly(_rot([(-0.026, 0.0), (0.026, 0.0), (0.020, 0.52), (-0.020, 0.52)], -13, -0.28, 0.10), pen, lift=0.25)
    c.poly(_rot([(-0.026, 0.40), (0.026, 0.40), (0.024, 0.46), (-0.024, 0.46)], -13, -0.28, 0.10), BRASS, lift=0.3)
    c.poly(_rot([(0.018, 0.50), (0.026, 0.50), (0.026, 0.28), (0.020, 0.28)], -13, -0.28, 0.10), scale(BRASS, 1.1), lift=0.2)
    c.poly(_rot([(-0.020, 0.52), (0.020, 0.52), (0.0, 0.64)], -13, -0.28, 0.10), (0.88, 0.80, 0.55), lift=0.25) if False else None
    p = _rot([(0.0, 0.52)], -13, -0.28, 0.10)[0]
    c.poly([(p[0] - 0.022, p[1]), (p[0] + 0.022, p[1]), (p[0] + 0.002, p[1] + 0.10)], (0.90, 0.78, 0.45), lift=0.25)
    c.line(p[0] - 0.012, p[1] + 0.01, p[0] - 0.001, p[1] + 0.085, 0.004, WHITE, 0.6)
    q = _rot([(0.0, 0.30)], -13, -0.28, 0.10)[0]
    c.line(q[0] - 0.012, q[1], q[0] - 0.012 - 0.010, q[1] + 0.20, 0.006, WHITE, 0.55)
    # ink bottle
    ix = 0.22
    _prism(c, ix, 0.0, 0.22, 0.22, 0.05, 0.04, (0.80, 0.86, 0.92), top=(0.9, 0.95, 1.0), side=(0.40, 0.48, 0.58), lift=0.1, r=0.02)
    c.rect(ix, 0.09, 0.19, 0.15, INK, lift=0.12, r=0.015, alpha=0.95)
    c.rect(ix, 0.24, 0.10, 0.045, (0.80, 0.86, 0.92), lift=0.15, r=0.01)
    _cyl(c, ix, 0.26, 0.055, 0.07, (0.10, 0.11, 0.16), dark=0.6)
    c.rect(ix - 0.07, 0.12, 0.018, 0.16, WHITE, lift=0, alpha=0.55, r=0.008)
    c.rect(ix, 0.16, 0.12, 0.03, (0.97, 0.96, 0.92), lift=0.04)
    # a pencil lying
    c.poly(_rot([(-0.30, -0.012), (0.34, -0.012), (0.34, 0.012), (-0.30, 0.012)], 5, 0.05, 0.0), (0.92, 0.62, 0.15), lift=0.25)
    c.poly(_rot([(0.34, -0.012), (0.43, 0.0), (0.34, 0.012)], 5, 0.05, 0.0), (0.92, 0.84, 0.66), lift=0.15)
    c.poly(_rot([(0.41, -0.004), (0.44, 0.0), (0.41, 0.004)], 5, 0.05, 0.0), (0.1, 0.1, 0.12), lift=0)


@sprop("svc_nt_embosser", aspect=1.71, fill=0.73)
def svc_nt_embosser(c, P):
    """A brass hand embosser (seal press): lever arms, pivot, rubber grips and the die plate over an embossed page."""
    rng = c.rng
    br = BRASS
    _sheet(c, 0.10, 0.0, 0.70, 0.46, -5, (0.98, 0.97, 0.94))
    c.rect(0.0, 0.0, 0.0, 0.0, WHITE)
    # lower jaw with the die
    c.poly([(-0.36, 0.04), (0.32, 0.04), (0.32, 0.12), (-0.36, 0.12)], scale(br, 0.85), lift=0.25)
    c.poly([(-0.36, 0.12), (0.32, 0.12), (0.36, 0.14), (-0.32, 0.14)], mix(br, WHITE, 0.3), lift=0.1)
    c.ellipse(0.20, 0.145, 0.13, 0.13 * 0.4, scale(br, 0.6), lift=0)
    c.ellipse(0.20, 0.15, 0.115, 0.115 * 0.4, br, lift=0.22)
    arc(c, 0.20, 0.152, 0.085, 0.085 * 0.4, 0, 360, 0.008, scale(br, 0.55), 0.9, 18)
    # back column and upper arm
    _path(c, [(-0.30, 0.10), (-0.34, 0.30), (-0.28, 0.52), (-0.10, 0.62), (0.12, 0.60)], 0.095, scale(br, 0.62), 1.0)
    _path(c, [(-0.30, 0.11), (-0.345, 0.30), (-0.285, 0.53), (-0.11, 0.625), (0.11, 0.61)], 0.060, br, 1.0)
    _path(c, [(-0.315, 0.14), (-0.355, 0.30), (-0.30, 0.52), (-0.13, 0.64)], 0.012, mix(br, WHITE, 0.6), 0.8)
    c.poly([(0.06, 0.52), (0.34, 0.50), (0.34, 0.40), (0.06, 0.38)], scale(br, 0.95), lift=0.25)
    c.ellipse(0.20, 0.35, 0.13, 0.13 * 0.4, scale(br, 0.6), lift=0)
    c.rect(0.20, 0.34, 0.20, 0.02, (0.25, 0.20, 0.12), lift=0, alpha=0.6)
    c.circle(-0.26, 0.54, 0.035, mix(br, WHITE, 0.2), lift=0.35)                                       # pivot
    c.circle(-0.27, 0.55, 0.012, WHITE, lift=0, alpha=0.8)
    # lever handle with rubber grip sticking out to the left
    c.line(-0.32, 0.46, -0.52, 0.62, 0.05, scale(br, 0.7))
    c.line(-0.33, 0.47, -0.53, 0.63, 0.030, br)
    c.line(-0.42, 0.55, -0.60, 0.70, 0.065, (0.10, 0.11, 0.14))
    c.line(-0.43, 0.56, -0.61, 0.71, 0.014, (0.45, 0.47, 0.52), 0.8)
    # embossed circle (shown as a light ring) on the page next to the die
    arc(c, 0.52, -0.02, 0.10, 0.10 * 0.42, 0, 360, 0.010, (0.80, 0.78, 0.72), 0.9, 20)
    arc(c, 0.52, -0.02 - 0.006, 0.10, 0.10 * 0.42, 190, 350, 0.006, WHITE, 0.9, 12)


@niche("notary-documents", "Notary and documentation service", subjects=("svc_nt_stamp",),
       strong=("notary", "notary public", "notary services", "notary service", "notary and documentation", "notary documents", "notary advocate", "affidavit", "affidavits",
               "rent agreement", "stamp paper", "power of attorney", "document attestation", "notarisation", "notarization", "notary office", "notary wala", "stamp paper wala",
               "नोटरी", "एफिडेविट", "शपथ पत्र", "स्टांप पेपर", "रेंट एग्रीमेंट", "नोटरी पब्लिक", "हलफनामा", "किरायानामा", "पावर ऑफ अटॉर्नी"),
       weak=("attestation", "agreement", "documentation", "legal documents", "seal", "stamp", "oath", "sworn", "drafting", "registry", "दस्तावेज"),
       accent="#1d3557", mood="warm", group="services",
       avoid=("law firm", "advocate office", "court case", "lawyer", "accounting", "ca firm", "visa", "immigration", "translation", "printing", "insurance"))
def notary_documents(S):
    P = S.pal
    rng = S.rng
    dk = P.mood == "dark"
    desk = scale(mix(P.surface, WALNUT, 0.70), 0.80 if not dk else 0.55)
    panel = mix(P.wall_bot, WALNUT, 0.35) if not dk else scale(mix(P.wall_bot, WALNUT, 0.4), 0.8)
    spines = (P.accent, (0.62, 0.16, 0.18), (0.22, 0.42, 0.32), (0.78, 0.62, 0.34), (0.86, 0.82, 0.72), scale(P.accent, 0.6), (0.45, 0.30, 0.20))
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        S.gradient_rect(-5.0, 0.36, 7.0, 0.64, scale(panel, 1.05), scale(panel, 0.80))                 # wood-panelled lower wall
        for k in range(40):
            S.rect(-4.8 + k * 0.26, 0.50, 0.005, 0.28, scale(panel, 0.65), lift=0.0, alpha=0.5)
        S.rect(1.0, 0.365, 14.0, 0.02, scale(panel, 0.6), lift=0.0)
        # bookcase with rows of legal volumes
        S.rect(0.50, 0.20, 2.2, 0.50, scale(panel, 0.55), lift=0.0)
        for row in range(3):
            vb = 0.10 + row * 0.15
            u = -0.50
            while u < 1.55:
                bw = rng.uniform(0.025, 0.055)
                bh = rng.uniform(0.09, 0.125)
                S.rect(u + bw / 2, vb - bh / 2 + 0.07, bw, bh, spines[rng.randrange(len(spines))], lift=0.12)
                S.rect(u + bw / 2, vb + 0.045, bw * 0.7, 0.008, (0.9, 0.8, 0.5), lift=0.0, alpha=0.7)
                u += bw + 0.003
            S.rect(0.50, vb + 0.075, 2.2, 0.012, scale(panel, 0.4), lift=0.0)
        # framed blank certificate and a banker's lamp glow
        S.rect(1.80, 0.20, 0.30, 0.38, scale(BRASS, 0.8), r=0.008, lift=0.1)
        S.rect(1.80, 0.20, 0.26, 0.34, (0.96, 0.94, 0.88), lift=0.02)
        S.rect(1.80, 0.20, 0.20, 0.028, P.accent, lift=0, alpha=0.7)
        S.rect(1.80, 0.25, 0.16, 0.008, (0.6, 0.6, 0.66), lift=0, alpha=0.7)
        S.rect(1.80, 0.28, 0.16, 0.008, (0.6, 0.6, 0.66), lift=0, alpha=0.7)
        S.glow(1.35, 0.46, 0.5, (1.0, 0.86, 0.55), 0.28 if not dk else 0.50)
        S.pendant(0.30, -0.1, 0.0, (1.0, 0.84, 0.52), 0.10)
        S.glow(1.0, 0.25, 1.0, P.light, 0.16)
        S.floor(0.62, scale(desk, 0.9), scale(desk, 0.8))
    # polished walnut desk with a navy leather blotter and stitching
    S.wood(-1.4, 0.66, 3.6, 2.6, desk, plank=0.22, grain=0.8)
    S.rect(1.0, 0.655, 14.0, 0.026, scale(desk, 0.60), lift=0.0)
    S.rect(1.0, 0.670, 14.0, 0.007, mix(desk, WHITE, 0.45), lift=0.0, alpha=0.7)
    S.rect(1.02, 0.94, 1.10, 0.44, scale(P.accent, 0.72), r=0.018, lift=0.14)
    S.rect(1.02, 0.94, 1.04, 0.38, scale(P.accent, 0.62), r=0.012, lift=0.0, alpha=0.5)
    for k in range(27):
        x = 0.50 + k * 0.0385
        S.rect(x, 0.737, 0.012, 0.004, mix(P.accent, WHITE, 0.45), lift=0, alpha=0.6)
        S.rect(x, 1.143, 0.012, 0.004, mix(P.accent, WHITE, 0.45), lift=0, alpha=0.6)
    S.soft(1.05, 0.88, 0.60, 0.14, (1.0, 0.88, 0.62), 0.34 if not dk else 0.40, 1.4, add=True)
    S.put("svc_nt_folders", 0.76, 0.80, 0.30, color=P)
    S.put("svc_nt_embosser", 1.33, 0.80, 0.26, color=P)
    S.put("svc_nt_stamp", 1.04, 0.92, 0.46, color=P, subject=True)
    S.put("svc_nt_papers", 1.32, 0.99, 0.12, color=P)
    S.put("svc_nt_pen", 0.70, 0.99, 0.21, color=P)
    S.focus("detail", 1.20, 0.84)
    with S.near():
        S.ellipse(0.40, 1.18, 0.14, 0.04, (0.12, 0.08, 0.05), 0.0, 0.5)
        S.circle(1.86, 1.14, 0.08, BRASS, 0.5)
