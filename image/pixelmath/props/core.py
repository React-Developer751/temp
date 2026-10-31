"""Drawing context and registry for business props (food, devices, people, vehicles ...).

Every prop is a function ``fn(c, color)`` that draws in *unit space*: origin at the middle of the
prop's base, +u to the right, +v up, nominal height 1.0. ``c`` is a `Ctx` that converts to pixels.
``color`` is the colour the user asked for ("red shoes") or None.

Style: flat illustration with a soft top-to-bottom shade and a drop shadow, light from the top left.
"""
import math
from dataclasses import dataclass

from ..raster import (clamp, mix, scale, sdf_capsule, sdf_circle, sdf_ellipse, sdf_polygon, bbox_of)

WHITE = (1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0)

REGISTRY = {}


@dataclass
class Prop:
    name: str
    fn: object
    aspect: float          # drawn width / height
    place: str             # ground | table | sky | wall
    nominal: float         # typical drawn height as a fraction of the canvas height
    fill: float            # how much of the unit height the drawing really uses (flat props < 1)
    words: tuple
    category: str


def prop(name, aspect=1.0, place="ground", nominal=0.3, words=(), category="misc", fill=1.0):
    def deco(fn):
        REGISTRY[name] = Prop(name, fn, aspect, place, nominal, fill, tuple(words) + (name,), category)
        return fn
    return deco


def rgb(hex_or_tuple):
    if isinstance(hex_or_tuple, str):
        h = hex_or_tuple.lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return hex_or_tuple


class Ctx:
    def __init__(self, painter, x, y, s):
        self.p, self.cv, self.rng = painter, painter.cv, painter.rng
        self.x, self.y, self.s = x, y, s

    # ---- coordinates and colour
    def X(self, u):
        return self.x + u * self.s

    def Y(self, v):
        return self.y - v * self.s

    def col(self, base, explicit=False):
        return self.p.col(rgb(base), explicit)

    def pick(self, color, default):
        """The user's colour if given, else a default palette colour (both lit by the scene)."""
        return self.col(color, True) if color is not None else self.col(default)

    def _shade(self, color, y0, y1, lift):
        if not lift:
            return None
        top, bot = scale(color, 1.0 + lift), scale(color, 1.0 - lift * 1.2)
        span = max(1.0, y1 - y0)
        return lambda px, py: mix(top, bot, clamp((py - y0) / span))

    # ---- shapes (unit coordinates)
    def rect(self, u, v, w, h, color, r=0.0, lift=0.10, alpha=1.0):
        cx, cy, hw, hh = self.X(u), self.Y(v), w * self.s / 2, h * self.s / 2
        self.cv.box(cx, cy, hw, hh, color, rad=min(r * self.s, hw, hh), alpha=alpha,
                    shade=self._shade(color, cy - hh, cy + hh, lift))

    def circle(self, u, v, r, color, lift=0.10, alpha=1.0, soft=1.0):
        cx, cy, rr = self.X(u), self.Y(v), r * self.s
        self.cv.circle(cx, cy, rr, color, alpha=alpha, soft=soft, shade=self._shade(color, cy - rr, cy + rr, lift))

    def ellipse(self, u, v, a, b, color, angle=0.0, lift=0.10, alpha=1.0, soft=1.0):
        cx, cy = self.X(u), self.Y(v)
        ext = max(a, b) * self.s
        self.cv.ellipse(cx, cy, a * self.s, b * self.s, color, angle=-math.radians(angle), alpha=alpha, soft=soft,
                        shade=self._shade(color, cy - ext, cy + ext, lift))

    def poly(self, pts, color, lift=0.10, alpha=1.0, angle=0.0, pivot=(0.0, 0.0)):
        if angle:
            a = math.radians(angle)
            ca, sa = math.cos(a), math.sin(a)
            pts = [(pivot[0] + (u - pivot[0]) * ca - (v - pivot[1]) * sa,
                    pivot[1] + (u - pivot[0]) * sa + (v - pivot[1]) * ca) for u, v in pts]
        px = [(self.X(u), self.Y(v)) for u, v in pts]
        ys = [p[1] for p in px]
        self.cv.polygon(px, color, alpha=alpha, shade=self._shade(color, min(ys), max(ys), lift))

    def path(self, pts, w, color, alpha=1.0, smooth=True, closed=False):
        """A stroke of width w (unit) through the points; one anti-aliased shape (no overlap darkening)."""
        pts = list(pts)
        if smooth and len(pts) > 2:
            pts = _catmull(pts, 6, closed)
        elif closed:
            pts.append(pts[0])
        px = [(self.X(u), self.Y(v)) for u, v in pts]
        r = w * self.s / 2
        segs = [(a[0], a[1], b[0], b[1]) for a, b in zip(px, px[1:])]
        if not segs:
            return
        fns = [sdf_capsule(ax, ay, bx, by, r) for ax, ay, bx, by in segs]
        sdf = lambda x, y: min(f(x, y) for f in fns)                     # noqa: E731
        self.cv.shape(bbox_of(px, r + 2), sdf, color, alpha)

    def line(self, u0, v0, u1, v1, w, color, alpha=1.0):
        self.cv.capsule(self.X(u0), self.Y(v0), self.X(u1), self.Y(v1), max(0.7, w * self.s / 2), color, alpha)

    def ring(self, u, v, r, thick, color, alpha=1.0):
        cx, cy, rr, th = self.X(u), self.Y(v), r * self.s, thick * self.s / 2
        self.cv.shape((cx - rr - th - 2, cy - rr - th - 2, cx + rr + th + 2, cy + rr + th + 2),
                      lambda x, y: abs(math.hypot(x - cx, y - cy) - rr) - th, color, alpha)

    def eoutline(self, u, v, a, b, thick, color, alpha=1.0, angle=0.0):
        """Ellipse outline (e.g. globe meridians)."""
        cx, cy = self.X(u), self.Y(v)
        f = sdf_ellipse(cx, cy, a * self.s, b * self.s, -math.radians(angle))
        th, ext = thick * self.s / 2, max(a, b) * self.s + thick * self.s + 2
        self.cv.shape((cx - ext, cy - ext, cx + ext, cy + ext), lambda x, y: abs(f(x, y)) - th, color, alpha)

    def arc(self, u, v, r, a0, a1, thick, color, alpha=1.0, ry=None):
        """Arc of a circle (degrees, ccw from +u)."""
        ry = r if ry is None else ry
        n = max(8, int(abs(a1 - a0) / 8))
        pts = [(u + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), v + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
        self.path(pts, thick, color, alpha, smooth=False)

    def text(self, txt, u, v, h, color, weight=0.16, max_w=None):
        """Write text (unit coordinates, h = cap height); returns its pixel box."""
        if getattr(self, "no_text", False):             # studio pictures carry no letters or numbers (see studio/stage.py NO_TEXT)
            return None
        from ..text import draw_text
        return draw_text(self.cv, txt, self.X(u), self.Y(v), h * self.s, color, weight, "center",
                         None if max_w is None else max_w * self.s)

    def shadow(self, u, v, w, h=0.10, alpha=0.26):
        self.cv.ellipse(self.X(u), self.Y(v), w * self.s / 2, h * self.s / 2, BLACK, alpha=alpha, soft=max(3.0, 0.04 * self.s))

    def glow(self, u, v, r, color, strength=0.5):
        self.cv.glow(self.X(u), self.Y(v), r * self.s, color, strength, 2.0)

    def sub(self, du, dv, scale_):
        """A child context moved by (du, dv) and scaled: lets one prop be built from others."""
        child = Ctx(self.p, self.X(du), self.Y(dv), self.s * scale_)
        child.no_text = getattr(self, "no_text", False)
        return child


def _catmull(pts, n, closed):
    out = []
    m = len(pts)
    rng_ = range(m) if closed else range(m - 1)
    for i in rng_:
        p0 = pts[(i - 1) % m] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if (closed or i + 2 < m) else pts[-1]
        for k in range(n):
            t = k / float(n)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[0] if closed else pts[-1])
    return out


def draw_prop(painter, name, x, y, s, color=None):
    """Draw prop `name` with its base centre at pixel (x, y) and nominal height s pixels."""
    REGISTRY[name].fn(Ctx(painter, x, y, s), color)
    drawn = getattr(painter.cv, "drawn", None)                 # lets the creative critic check that requested props really appear
    if drawn is None:
        drawn = painter.cv.drawn = []
    drawn.append(name)
