"""Drawing craft for studio props: perspective ellipses, soft light, gloss, speckle, leaves, steam.

Everything takes a `Ctx` ``c`` (unit space: origin at the middle of the prop's base, +u right, +v up, nominal height 1.0;
see props/core.py) and draws with soft, layered shading instead of flat fills: a contact shadow, a base colour with a
gradient away from the key light, a darker core / rim, a highlight, and texture made of many small seeded details.
Light comes from the top left (u -, v +) unless a function says otherwise.
"""
import math

from ..raster import clamp, mix, scale

WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
TILT = 0.40                       # vertical squash of a circle seen from a raised 3/4 viewpoint


def soft_disc(c, u, v, a, b, color, alpha=0.5, power=1.7, angle=0.0, add=False):
    """Radial-falloff ellipse: a smooth blob of colour (contact shadows, ambient occlusion, bloom, soft highlights)."""
    cv = c.cv
    cx, cy = c.X(u), c.Y(v)
    ra, rb = max(0.8, a * c.s), max(0.8, b * c.s)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    ext = max(ra, rb) + 1
    px, w = cv.px, cv.w
    x0, x1 = max(0, int(cx - ext)), min(cv.w, int(cx + ext) + 1)
    y0, y1 = max(0, int(cy - ext)), min(cv.h, int(cy + ext) + 1)
    for y in range(y0, y1):
        dy = y + 0.5 - cy
        for x in range(x0, x1):
            dx = x + 0.5 - cx
            rx = (dx * ca + dy * sa) / ra
            ry = (-dx * sa + dy * ca) / rb
            d2 = rx * rx + ry * ry
            if d2 >= 1.0:
                continue
            t = alpha * (1.0 - math.sqrt(d2)) ** power
            i = (y * w + x) * 3
            if add:
                px[i] = min(1.0, px[i] + color[0] * t)
                px[i + 1] = min(1.0, px[i + 1] + color[1] * t)
                px[i + 2] = min(1.0, px[i + 2] + color[2] * t)
            else:
                it = 1.0 - t
                px[i] = px[i] * it + color[0] * t
                px[i + 1] = px[i + 1] * it + color[1] * t
                px[i + 2] = px[i + 2] * it + color[2] * t


def ao(c, u, v, w, depth=None, alpha=0.42):
    """Ambient-occlusion contact shadow under an object whose footprint is w wide, centred at (u, v)."""
    d = w * TILT * 0.5 if depth is None else depth
    soft_disc(c, u + w * 0.05, v - d * 0.1, w * 0.62, d * 1.25, BLACK, alpha * 0.55, 1.4)
    soft_disc(c, u + w * 0.03, v, w * 0.50, d * 0.8, BLACK, alpha, 2.0)


def disc(c, u, v, r, color, tilt=TILT, lift=0.12, alpha=1.0, rim=True):
    """A circle seen from above at an angle, shaded top-to-bottom, with a darker rim line."""
    if rim:
        c.ellipse(u, v, r, r * tilt, scale(color, 0.74), lift=0, alpha=alpha)
        c.ellipse(u, v + r * 0.015, r * 0.975, r * tilt * 0.965, color, lift=lift, alpha=alpha)
    else:
        c.ellipse(u, v, r, r * tilt, color, lift=lift, alpha=alpha)


def hshade_box(c, u, v, w, h, left, right, r=0.0, alpha=1.0, lift=0.0):
    """Rectangle shaded left-to-right (cylinders, bottles, cups): `left` is the lit side."""
    cx, cy = c.X(u), c.Y(v)
    hw, hh = w * c.s / 2, h * c.s / 2
    x0, span = cx - hw, max(1.0, 2 * hw)
    c.cv.box(cx, cy, hw, hh, left, rad=min(r * c.s, hw, hh), alpha=alpha,
             shade=lambda px, py: mix(left, right, clamp((px - x0) / span) ** 1.3))


def cylinder(c, u, v, r, h, side_l, side_r, top, tilt=TILT, lip=True):
    """Upright cylinder standing at (u, v): lit side, top ellipse, optional rim."""
    hshade_box(c, u, v + h / 2, 2 * r, h, side_l, side_r)
    c.ellipse(u, v, r, r * tilt, side_r, lift=0)                       # rounded bottom edge
    hshade_box(c, u, v + h / 2 + 0.001, 2 * r, h, side_l, side_r)
    disc(c, u, v + h, r, top, tilt, 0.06, rim=lip)


def gloss(c, u, v, a, b, angle=0.0, alpha=0.55):
    """A soft specular highlight."""
    soft_disc(c, u, v, a, b, WHITE, alpha, 1.2, angle, add=True)


def speckle(c, n, u, v, a, b, colors, rmin=0.006, rmax=0.016, tilt=1.0, alpha=1.0, flat=False):
    """n small blobs scattered inside an ellipse (cheese, seeds, sprinkles, crumbs, bubbles), seeded."""
    rng = c.rng
    for _ in range(n):
        ang = rng.random() * 2 * math.pi
        rr = math.sqrt(rng.random())
        uu, vv = u + math.cos(ang) * a * rr, v + math.sin(ang) * b * rr * tilt
        r = rng.uniform(rmin, rmax)
        col = colors[rng.randrange(len(colors))]
        c.ellipse(uu, vv, r, r * (0.55 if flat else 1.0), col, lift=0.1 if not flat else 0, alpha=alpha)


def leaf(c, u, v, length, angle, color, width=0.45):
    """A pointed leaf (basil, mint) with a midrib; angle in degrees, 0 = pointing right."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = []
    for t in [i / 8.0 for i in range(9)]:
        s = math.sin(math.pi * t) ** 0.8 * wd
        pts.append((t * length, s))
    outline = pts + [(x, -y) for x, y in reversed(pts)]
    poly = [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in outline]
    c.poly(poly, color, lift=0.15)
    c.poly([(u + x * ca - y * sa * 0.2, v + x * sa + y * ca * 0.2) for x, y in [(0.05 * length, 0.0), (0.5 * length, wd * 0.5), (0.92 * length, 0.0)]],
           mix(color, WHITE, 0.2), alpha=0.35)
    c.line(u, v, u + length * 0.9 * ca, v + length * 0.9 * sa, length * 0.04, scale(color, 0.7), 0.7)


def steam(c, u, v, h, w=0.06, n=3, alpha=0.18):
    """Rising steam: stacks of soft translucent discs that drift sideways."""
    rng = c.rng
    for k in range(n):
        x = u + (k - (n - 1) / 2.0) * w * 1.4
        for i in range(9):
            t = i / 8.0
            soft_disc(c, x + math.sin(t * 3.0 + k * 1.7) * w * 0.7 + rng.uniform(-0.01, 0.01), v + t * h, w * (0.55 + t * 0.9),
                      w * (0.55 + t * 0.9), WHITE, alpha * (1 - t) ** 0.8, 1.3)


def drip(c, u, v, r, color):
    """A small glossy droplet / bead of sauce."""
    c.ellipse(u, v, r, r * 0.9, color, lift=0.15)
    soft_disc(c, u - r * 0.3, v + r * 0.3, r * 0.45, r * 0.35, WHITE, 0.7, 1.0, add=True)


def arc(c, u, v, a, b, a0, a1, w, color, alpha=1.0, steps=10, angle=0.0):
    """A thin elliptical arc drawn with capsules (much cheaper than an outline shape); degrees, ccw from +u."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    pts = []
    for k in range(steps + 1):
        t = math.radians(a0 + (a1 - a0) * k / steps)
        x, y = a * math.cos(t), b * math.sin(t)
        pts.append((u + x * ca - y * sa, v + x * sa + y * ca))
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], w, color, alpha)


def strand(c, u, v, length, angle, w, color, alpha=1.0, curl=0.5):
    """A curved noodle / hair / grass blade: a short bent polyline."""
    a = math.radians(angle)
    pts = []
    for k in range(7):
        t = k / 6.0
        bend = math.sin(t * math.pi) * curl * length * 0.5
        pts.append((u + math.cos(a) * length * t - math.sin(a) * bend, v + math.sin(a) * length * t + math.cos(a) * bend))
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], w, color, alpha)
