"""Digital, professional-services and education niches: saas, mobile-app, ecommerce, digital-agency, accounting-finance,
law-firm, school, coaching-tuition.

Props are prefixed ``digedu_``. Shared building blocks: ``_G`` (a rotated local frame so UI screens can be drawn on tilted
phones), ``box3d`` (a box in raised 3/4 view), and a few UI widgets (cards, charts, text bars) that are drawn with plain shapes.
"""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale


# ---------------------------------------------------------------------------------------------- fast fills
def _ivl(a, b, dy, ca, sa):
    """x-interval (relative to the centre) of the row at offset dy inside a rotated centred rectangle with half sizes a, b."""
    lo, hi = -1e18, 1e18
    if abs(ca) > 1e-6:
        l1, l2 = (-a + dy * sa) / ca, (a + dy * sa) / ca
        if l1 > l2:
            l1, l2 = l2, l1
        lo, hi = max(lo, l1), min(hi, l2)
    elif abs(dy * sa) > a:
        return None
    if abs(sa) > 1e-6:
        l1, l2 = (-b - dy * ca) / sa, (b - dy * ca) / sa
        if l1 > l2:
            l1, l2 = l2, l1
        lo, hi = max(lo, l1), min(hi, l2)
    elif abs(dy * ca) > b:
        return None
    return (lo, hi) if lo < hi else None


def _fill_rrect(cv, cx, cy, hw, hh, rad, ca, sa, col, alpha=1.0, lift=0.0):
    """Anti-aliased (rotated) rounded rectangle: the interior of every row is one slice assignment, only the edges use an SDF.
    Much faster than Canvas.box / polygon for the many UI rectangles; the vertical lift gradient matches Ctx.rect."""
    w, h, px = cv.w, cv.h, cv.px
    rad = max(0.0, min(rad, hw, hh))
    ex, ey = hw * abs(ca) + hh * abs(sa), hw * abs(sa) + hh * abs(ca)
    y0, y1 = max(0, int(cy - ey - 1)), min(h, int(cy + ey + 2))
    ytop, span = cy - ey, max(1.0, 2 * ey)
    top, bot = (scale(col, 1 + lift), scale(col, 1 - lift * 1.2)) if lift else (col, col)
    hwi, hhi = hw - 1.5, hh - 1.5
    radi = max(rad - 1.5, 0.0)
    has_in = hwi - radi > 0 and hhi > 0 and hwi > 0 and hhi - radi > 0
    hyp, mn, mx = math.hypot, min, max
    for y in range(y0, y1):
        dy = y + 0.5 - cy
        o = _ivl(hw + 1, hh + 1, dy, ca, sa)
        if o is None:
            continue
        xo0, xo1 = max(0, int(cx + o[0] - 1)), mn(w, int(cx + o[1] + 2))
        if xo1 <= xo0:
            continue
        if lift:
            t = (y - ytop) / span
            t = 0.0 if t < 0 else 1.0 if t > 1 else t
            c = (top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t, top[2] + (bot[2] - top[2]) * t)
        else:
            c = col
        xi0 = xi1 = xo0
        if has_in:
            ia = _ivl(hwi - radi, hhi, dy, ca, sa)
            ib = _ivl(hwi, hhi - radi, dy, ca, sa)
            if ia and ib:
                il, ir = (mn(ia[0], ib[0]), mx(ia[1], ib[1])) if (ia[0] <= ib[1] and ib[0] <= ia[1]) else (ia if ia[1] - ia[0] > ib[1] - ib[0] else ib)
            else:
                il, ir = ia or ib or (0.0, -1.0)
            if ir > il:
                xi0 = mx(xo0, int(math.ceil(cx + il - 0.5)))
                xi1 = mn(xo1, int(math.floor(cx + ir - 0.5)) + 1)
                if xi1 <= xi0:
                    xi0 = xi1 = xo0
        ncore = xi1 - xi0
        if ncore > 0:
            if alpha >= 0.999:
                px[(y * w + xi0) * 3:(y * w + xi1) * 3] = [c[0], c[1], c[2]] * ncore
            else:
                seg = px[(y * w + xi0) * 3:(y * w + xi1) * 3]
                ia_ = 1.0 - alpha
                a0, a1, a2 = c[0] * alpha, c[1] * alpha, c[2] * alpha
                px[(y * w + xi0) * 3:(y * w + xi1) * 3] = [seg[k] * ia_ + (a0, a1, a2)[k % 3] for k in range(len(seg))]
        else:
            xi0 = xi1 = xo1
        for x in list(range(xo0, xi0)) + list(range(xi1, xo1)):
            dx = x + 0.5 - cx
            qx = abs(dx * ca - dy * sa) - hw + rad
            qy = abs(-dx * sa - dy * ca) - hh + rad
            d = hyp(qx if qx > 0 else 0.0, qy if qy > 0 else 0.0) + mn(mx(qx, qy), 0.0) - rad
            if d >= 0.5:
                continue
            a = (1.0 if d <= -0.5 else 0.5 - d) * alpha
            i = (y * w + x) * 3
            ia_ = 1.0 - a
            px[i] = px[i] * ia_ + c[0] * a
            px[i + 1] = px[i + 1] * ia_ + c[1] * a
            px[i + 2] = px[i + 2] * ia_ + c[2] * a


def _crect(c, u, v, w, h, col, r=0.0, lift=0.10, alpha=1.0):
    """Drop-in for Ctx.rect built on the fast scanline fill."""
    s = c.s
    _fill_rrect(c.cv, c.X(u), c.Y(v), w * s / 2, h * s / 2, r * s, 1.0, 0.0, col, alpha, lift)


def sorted_quad(pts):
    """Order four points of a parallelogram-like quad around their centre (so scanline filling works for any flip)."""
    cx = sum(p[0] for p in pts) / 4.0
    cy = sum(p[1] for p in pts) / 4.0
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _srect(S, u, v, w, h, col, r=0.0, lift=0.0, alpha=1.0):
    """Stage-level rounded rectangle on the fast scanline fill (S.rect goes through the slower SDF box)."""
    if S.dry:
        return
    S._ensure_mid() if S._layer is S.main else None
    x, y = S.px(u, v)
    _fill_rrect(S.cv, x, y, S.length(w) / 2, S.length(h) / 2, S.length(r), 1.0, 0.0, col, alpha, lift)


def _fill_quad(cv, pts, col, alpha):
    """Un-antialiased convex polygon with constant alpha, by scanlines (for soft sheens / light shafts only)."""
    w, h, px = cv.w, cv.h, cv.px
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(max(0, int(min(ys))), min(h, int(max(ys)) + 1)):
        yy = y + 0.5
        xs = []
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            if (ya <= yy < yb) or (yb <= yy < ya):
                xs.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
        if len(xs) < 2:
            continue
        x0, x1 = max(0, int(min(xs) + 0.5)), min(w, int(max(xs) + 0.5))
        if x1 <= x0:
            continue
        seg = px[(y * w + x0) * 3:(y * w + x1) * 3]
        ia = 1.0 - alpha
        a0, a1, a2 = col[0] * alpha, col[1] * alpha, col[2] * alpha
        k = (a0, a1, a2)
        px[(y * w + x0) * 3:(y * w + x1) * 3] = [seg[j] * ia + k[j % 3] for j in range(len(seg))]


# ====================================================================================================== shared helpers
class _G:
    """A local drawing frame inside a prop: origin (ou, ov), rotation `ang` (degrees, ccw) and scale `k`."""

    def __init__(self, c, ou=0.0, ov=0.0, ang=0.0, k=1.0):
        self.c, self.ou, self.ov, self.k, self.ang = c, ou, ov, k, ang
        a = math.radians(ang)
        self.ca, self.sa = math.cos(a), math.sin(a)

    def pt(self, u, v):
        u, v = u * self.k, v * self.k
        return (self.ou + u * self.ca - v * self.sa, self.ov + u * self.sa + v * self.ca)

    def poly(self, pts, col, lift=0.0, alpha=1.0):
        self.c.poly([self.pt(u, v) for u, v in pts], col, lift=lift, alpha=alpha)

    def rect(self, u, v, w, h, col, r=0.0, lift=0.0, alpha=1.0):
        c = self.c
        cu, cv_ = self.pt(u, v)
        sc = c.s * self.k
        _fill_rrect(c.cv, c.X(cu), c.Y(cv_), w / 2.0 * sc, h / 2.0 * sc, r * sc, self.ca, self.sa, col, alpha, lift)

    def circle(self, u, v, r, col, lift=0.0, alpha=1.0):
        x, y = self.pt(u, v)
        self.c.ellipse(x, y, r * self.k, r * self.k, col, 0.0, lift=lift, alpha=alpha)

    def line(self, u0, v0, u1, v1, w, col, alpha=1.0):
        a, b = self.pt(u0, v0), self.pt(u1, v1)
        self.c.line(a[0], a[1], b[0], b[1], w * self.k, col, alpha)

    def path(self, pts, w, col, alpha=1.0, smooth=True):
        self.c.path([self.pt(u, v) for u, v in pts], w * self.k, col, alpha, smooth=smooth)

    def arc(self, u, v, r, a0, a1, th, col, alpha=1.0):
        x, y = self.pt(u, v)
        self.c.arc(x, y, r * self.k, a0 + self.ang, a1 + self.ang, th * self.k, col, alpha)


def box3d(c, u, v, w, h, d, front, top=None, side=None, lift=0.08, dx=0.55, dy=0.42):
    """A box seen from the front, slightly right and above: front face centred on (u, v) (its bottom middle), depth d."""
    top = top or mix(front, WHITE, 0.22)
    side = side or scale(front, 0.66)
    x0, x1 = u - w / 2, u + w / 2
    ox, oy = d * dx, d * dy
    c.poly([(x1, v), (x1 + ox, v + oy), (x1 + ox, v + h + oy), (x1, v + h)], side, lift=0.06)
    c.poly([(x0, v + h), (x1, v + h), (x1 + ox, v + h + oy), (x0 + ox, v + h + oy)], top, lift=0.0)
    _crect(c, u, v + h / 2, w, h, front, lift=lift)
    c.line(x0, v + h, x1, v + h, 0.004, mix(top, WHITE, 0.5), 0.55)                  # lit top edge


def _contact(c, u, v, w, depth=None, alpha=0.4):
    ao(c, u, v, w, depth, alpha)


def _bars(g, u0, v0, u1, v1, col, rng, n=7, col2=None, hi=None):
    """Bar chart inside a rectangle (v0 bottom, v1 top)."""
    w = (u1 - u0) / n
    for i in range(n):
        h = (v1 - v0) * rng.uniform(0.28, 1.0)
        if hi is not None and i == hi:
            h = (v1 - v0) * 0.95
        cc = col2 if (hi is not None and i == hi and col2) else col
        g.rect(u0 + w * (i + 0.5), v0 + h / 2, w * 0.58, h, cc, r=w * 0.12, lift=0.1)


def _area(g, u0, v0, u1, v1, col, rng, n=8, dots=True):
    """Smooth area chart with a line, soft fill and end dot."""
    pts = []
    y = 0.4
    for i in range(n):
        y = min(0.95, max(0.1, y + rng.uniform(-0.22, 0.30)))
        pts.append((u0 + (u1 - u0) * i / (n - 1.0), v0 + (v1 - v0) * y))
    g.poly(pts + [(u1, v0), (u0, v0)], col, alpha=0.20)
    g.path(pts, (v1 - v0) * 0.035, col, 1.0)
    if dots:
        g.circle(pts[-1][0], pts[-1][1], (v1 - v0) * 0.06, WHITE)
        g.circle(pts[-1][0], pts[-1][1], (v1 - v0) * 0.035, col)


def _donut(g, u, v, r, th, cols, fracs):
    a = 90.0
    for col, f in zip(cols, fracs):
        g.arc(u, v, r, a, a + 360.0 * f - 6.0, th, col, 1.0)
        a += 360.0 * f


def _textbars(g, u0, v, w, col, n=2, gap=0.03, h=0.014, alpha=0.8):
    for i in range(n):
        ww = w * (1.0 if i == 0 else 0.62 + 0.2 * (i % 2))
        g.rect(u0 + ww / 2, v - gap * i, ww, h, col, r=h / 2, alpha=alpha)


def _ui_card(g, u, v, w, h, bg=WHITE, r=0.014, edge=None):
    g.rect(u, v - 0.004, w + 0.004, h + 0.004, edge or (0.0, 0.0, 0.15), r=r + 0.002, alpha=0.10)
    g.rect(u, v, w, h, bg, r=r)


def _sheen(g, u, v, w, h, alpha=0.10):
    c = g.c
    pts = [g.pt(u - w / 2, v + h / 2), g.pt(u - w * 0.05, v + h / 2), g.pt(u - w * 0.45, v - h / 2), g.pt(u - w / 2, v - h / 2)]
    _fill_quad(c.cv, [(c.X(a), c.Y(b)) for a, b in pts], WHITE, alpha)


ALU = (0.78, 0.80, 0.84)


def _laptop(c, ui, acc, body=ALU, dark_ui=False):
    """A laptop (aspect 1.5, height ~0.9): lid with screen drawn by ui(g, acc), keyboard deck, trackpad, screen glow."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.55, 0.2)
    # keyboard deck (a trapezoid: the far edge is narrower) plus the front lip
    c.poly([(-0.78, 0.0), (0.78, 0.0), (0.78, 0.035), (-0.78, 0.035)], scale(body, 0.62), lift=0.05)
    c.poly([(-0.78, 0.035), (0.78, 0.035), (0.70, 0.150), (-0.70, 0.150)], mix(body, WHITE, 0.08), lift=0.1)
    c.poly([(-0.64, 0.062), (0.64, 0.062), (0.60, 0.132), (-0.60, 0.132)], scale(body, 0.52), alpha=0.95)
    for row in range(3):
        v = 0.078 + row * 0.022
        sh = 1.0 - row * 0.030
        n = 15
        for k in range(n):
            u = (k - (n - 1) / 2.0) * 0.080 * sh
            _crect(c, u, v, 0.062 * sh, 0.014, scale(body, 0.88), r=0.004, lift=0.2)
    _crect(c, 0.0, 0.0485, 0.30, 0.014, scale(body, 0.94), r=0.004, lift=0.1)
    # lid: aluminium back edge, bezel, screen
    _crect(c, 0.0, 0.52, 1.34, 0.76, scale(body, 0.55), r=0.03, lift=0.12)
    _crect(c, 0.0, 0.525, 1.31, 0.73, (0.05, 0.055, 0.07), r=0.025, lift=0.0)
    g = _G(c, 0.0, 0.525)
    ui(g, acc)
    _sheen(g, -0.2, 0.0, 1.0, 0.7, 0.07)
    c.line(-0.62, 0.89, 0.62, 0.89, 0.004, WHITE, 0.25)
    c.glow(0.0, 0.52, 0.7, mix(acc, WHITE, 0.55), 0.06)
    soft_disc(c, 0.0, 0.10, 0.62, 0.05, mix(acc, WHITE, 0.7), 0.16, 1.3, add=True)


# ====================================================================================================== SAAS
def _dashboard_ui(g, acc):
    rng = g.c.rng
    ink = (0.16, 0.18, 0.28)
    g.rect(0, 0, 1.26, 0.70, (0.945, 0.953, 0.985))
    # sidebar
    dk = mix(acc, (0.04, 0.03, 0.14), 0.62)
    g.rect(-0.54, 0, 0.18, 0.70, dk)
    g.circle(-0.54, 0.28, 0.034, mix(acc, WHITE, 0.55))
    g.circle(-0.54, 0.28, 0.018, dk)
    for i in range(6):
        y = 0.16 - i * 0.075
        if i == 1:
            g.rect(-0.54, y, 0.15, 0.052, acc, r=0.016)
        g.circle(-0.595, y, 0.014, WHITE, alpha=0.9 if i == 1 else 0.45)
        g.rect(-0.525, y, 0.07 + 0.012 * (i % 3), 0.014, WHITE, r=0.007, alpha=0.85 if i == 1 else 0.38)
    # top bar
    g.rect(0.09, 0.315, 1.08, 0.07, WHITE)
    g.rect(-0.18, 0.315, 0.34, 0.034, (0.92, 0.93, 0.97), r=0.017)
    g.circle(-0.33, 0.315, 0.009, (0.7, 0.72, 0.8))
    g.circle(0.58, 0.315, 0.026, mix(acc, WHITE, 0.3))
    g.circle(0.50, 0.315, 0.013, (0.72, 0.74, 0.82))
    g.circle(0.512, 0.325, 0.006, (0.95, 0.35, 0.35))
    # KPI cards
    for i, (cx, tint) in enumerate(((-0.265, acc), (0.075, (0.16, 0.7, 0.45)), (0.415, (0.97, 0.62, 0.15)))):
        _ui_card(g, cx, 0.185, 0.31, 0.15)
        g.circle(cx - 0.105, 0.21, 0.032, tint, alpha=0.18)
        g.circle(cx - 0.105, 0.21, 0.015, tint)
        g.rect(cx + 0.02, 0.22, 0.13, 0.014, (0.7, 0.72, 0.8), r=0.007)
        g.rect(cx - 0.045, 0.172, 0.17 + 0.03 * i, 0.04, ink, r=0.012)
        g.rect(cx + 0.095, 0.140, 0.07, 0.024, (0.18, 0.72, 0.45), r=0.012, alpha=0.22)
        g.rect(cx + 0.095, 0.140, 0.04, 0.010, (0.16, 0.62, 0.40), r=0.005)
        g.rect(cx - 0.09, 0.140, 0.10, 0.010, (0.74, 0.76, 0.84), r=0.005)
    # main area chart
    _ui_card(g, -0.20, -0.135, 0.56, 0.31)
    g.rect(-0.38, -0.025, 0.14, 0.016, ink, r=0.008, alpha=0.8)
    for k in range(4):
        g.line(-0.44, -0.075 - k * 0.058, 0.04, -0.075 - k * 0.058, 0.002, (0.88, 0.89, 0.94))
    _area(g, -0.43, -0.245, 0.03, -0.065, acc, rng, 9)
    # bar chart
    _ui_card(g, 0.255, -0.135, 0.31, 0.31)
    g.rect(0.18, -0.025, 0.10, 0.016, ink, r=0.008, alpha=0.8)
    _bars(g, 0.13, -0.245, 0.38, -0.07, mix(acc, WHITE, 0.55), rng, 8, acc, hi=5)
    # donut
    _ui_card(g, 0.51, -0.135, 0.20, 0.31)
    _donut(g, 0.51, -0.105, 0.055, 0.020, (acc, (0.97, 0.62, 0.15), (0.16, 0.7, 0.45)), (0.5, 0.28, 0.22))
    g.rect(0.51, -0.19, 0.12, 0.012, (0.74, 0.76, 0.84), r=0.006)
    g.rect(0.51, -0.22, 0.09, 0.012, (0.84, 0.85, 0.9), r=0.006)


@sprop("digedu_laptop_dash", aspect=1.7, fill=0.92)
def laptop_dash(c, color):
    _laptop(c, _dashboard_ui, color or (0.31, 0.27, 0.9))


@sprop("digedu_float_chart", aspect=1.35, fill=1.0)
def float_chart(c, color):
    rng = c.rng
    acc = color or (0.31, 0.27, 0.9)
    soft_disc(c, 0.03, -0.04, 0.78, 0.12, (0.05, 0.04, 0.2), 0.35, 1.3)
    g = _G(c, 0, 0.5)
    g.rect(0.0, 0.0, 1.30, 0.96, (0.0, 0.0, 0.1), r=0.1, alpha=0.18)
    g.rect(0.0, 0.01, 1.28, 0.95, WHITE, r=0.1, lift=0.03)
    g.rect(-0.38, 0.30, 0.34, 0.07, (0.18, 0.2, 0.3), r=0.035, alpha=0.9)
    g.rect(0.34, 0.30, 0.20, 0.07, mix(acc, WHITE, 0.7), r=0.035)
    _area(g, -0.52, -0.38, 0.52, 0.18, acc, rng, 8)
    _sheen(g, 0, 0.0, 1.2, 0.9, 0.05)


@sprop("digedu_float_kpi", aspect=1.1, fill=1.0)
def float_kpi(c, color):
    acc = color or (0.31, 0.27, 0.9)
    soft_disc(c, 0.03, -0.04, 0.6, 0.12, (0.05, 0.04, 0.2), 0.35, 1.3)
    g = _G(c, 0, 0.5)
    g.rect(0.0, 0.0, 1.10, 0.96, (0.0, 0.0, 0.1), r=0.12, alpha=0.18)
    g.rect(0.0, 0.01, 1.08, 0.95, WHITE, r=0.12, lift=0.03)
    g.circle(-0.32, 0.26, 0.15, acc, alpha=0.18)
    g.circle(-0.32, 0.26, 0.07, acc)
    g.rect(0.18, 0.28, 0.40, 0.07, (0.72, 0.74, 0.82), r=0.035)
    g.rect(-0.05, -0.03, 0.70, 0.22, (0.16, 0.18, 0.28), r=0.07)
    g.rect(-0.25, -0.30, 0.30, 0.10, (0.18, 0.72, 0.45), r=0.05, alpha=0.25)
    g.rect(-0.25, -0.30, 0.18, 0.045, (0.16, 0.62, 0.40), r=0.022)
    _sheen(g, 0, 0.0, 1.0, 0.9, 0.05)


@sprop("digedu_float_notify", aspect=2.4, fill=1.0)
def float_notify(c, color):
    acc = color or (0.31, 0.27, 0.9)
    soft_disc(c, 0.04, -0.06, 1.15, 0.22, (0.05, 0.04, 0.2), 0.32, 1.3)
    g = _G(c, 0, 0.5)
    g.rect(0.0, 0.0, 2.35, 0.96, (0.0, 0.0, 0.1), r=0.48, alpha=0.18)
    g.rect(0.0, 0.01, 2.32, 0.95, WHITE, r=0.47, lift=0.03)
    g.circle(-0.84, 0.0, 0.34, acc)
    g.circle(-0.84, 0.0, 0.14, WHITE)
    g.rect(0.18, 0.15, 1.10, 0.14, (0.16, 0.18, 0.28), r=0.07)
    g.rect(0.02, -0.15, 0.80, 0.11, (0.74, 0.76, 0.84), r=0.055)
    g.circle(0.94, 0.0, 0.17, (0.18, 0.72, 0.45))
    g.line(0.87, 0.0, 0.93, -0.06, 0.05, WHITE)
    g.line(0.93, -0.06, 1.02, 0.07, 0.05, WHITE)


@sprop("digedu_mug", aspect=0.95, fill=1.0)
def mug(c, color):
    col = color or (0.95, 0.95, 0.96)
    ao(c, 0.0, 0.0, 0.8, 0.2)
    craft.arc(c, 0.36, 0.42, 0.20, 0.24, -80, 80, 0.07, scale(col, 0.78), 1.0, 10)
    craft.arc(c, 0.36, 0.42, 0.20, 0.24, -80, 80, 0.035, scale(col, 0.95), 1.0, 10)
    c.ellipse(0.0, 0.03, 0.38, 0.38 * TILT, scale(col, 0.7), lift=0)
    craft.hshade_box(c, 0.0, 0.40, 0.76, 0.76, col, scale(col, 0.62), r=0.04)
    disc(c, 0.0, 0.78, 0.38, col, TILT, 0.04, rim=True)
    c.ellipse(0.0, 0.775, 0.31, 0.31 * TILT, (0.30, 0.17, 0.10), lift=0.1)
    gloss(c, -0.1, 0.80, 0.14, 0.04, 6, 0.30)
    gloss(c, -0.2, 0.40, 0.04, 0.3, 0, 0.5)
    craft.steam(c, 0.0, 0.88, 0.5, 0.07, 2, 0.12)


@sprop("digedu_plant", aspect=0.9, fill=1.0)
def plant(c, color):
    rng = c.rng
    pot = color or (0.88, 0.86, 0.82)
    ao(c, 0.0, 0.0, 0.7, 0.16)
    for i in range(10):
        a = rng.uniform(25, 155)
        craft.leaf(c, rng.uniform(-0.08, 0.08), 0.34, rng.uniform(0.40, 0.62), a + rng.uniform(-10, 10),
                   (0.14 + rng.random() * 0.08, 0.42 + rng.random() * 0.16, 0.22), 0.34)
    craft.hshade_box(c, 0.0, 0.17, 0.52, 0.34, pot, scale(pot, 0.62), r=0.05)
    disc(c, 0.0, 0.34, 0.26, scale(pot, 0.9), TILT, 0.0)
    c.ellipse(0.0, 0.335, 0.21, 0.21 * TILT, (0.22, 0.15, 0.1), lift=0)
    gloss(c, -0.12, 0.2, 0.03, 0.12, 0, 0.35)
    for i in range(4):
        craft.leaf(c, rng.uniform(-0.08, 0.08), 0.35, rng.uniform(0.2, 0.34), rng.uniform(40, 140), (0.2, 0.55, 0.28), 0.4)


@sprop("digedu_notebook", aspect=3.0, fill=0.5)
def notebook(c, color):
    col = color or (0.2, 0.22, 0.3)
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.28)
    box3d(c, -0.1, 0.0, 1.20, 0.14, 0.7, col, mix(col, WHITE, 0.14), scale(col, 0.62), dx=0.5, dy=0.5)
    _crect(c, 0.28, 0.07, 0.04, 0.14, mix(col, (0.9, 0.7, 0.3), 0.5), lift=0.0)
    c.line(-0.62, 0.075, 0.58, 0.075, 0.006, mix(col, WHITE, 0.3), 0.5)
    # a pen lying on the cover
    c.line(-0.45, 0.23, 0.55, 0.30, 0.050, (0.12, 0.12, 0.16), 1.0)
    c.line(-0.45, 0.235, 0.55, 0.305, 0.015, (0.9, 0.9, 0.95), 0.6)
    gloss(c, -0.3, 0.19, 0.2, 0.025, 4, 0.30)


@sprop("digedu_mouse", aspect=0.9, fill=0.34)
def mouse(c, color):
    ao(c, 0.0, 0.0, 0.7, 0.15)
    c.ellipse(0.0, 0.14, 0.30, 0.34, (0.84, 0.85, 0.88), lift=0.18)
    c.line(0.0, 0.17, 0.0, 0.46, 0.012, (0.62, 0.64, 0.68), 0.9)
    gloss(c, -0.1, 0.36, 0.1, 0.10, 0, 0.7)


@niche("saas", "SaaS / software company", subjects=("digedu_laptop_dash",),
       strong=("saas", "software company", "software", "dashboard", "analytics", "startup", "web app", "crm", "platform",
               "सॉफ्टवेयर", "software company", "सास", "साफ्टवेयर"),
       weak=("app", "cloud", "tech", "it company", "technology", "data", "automation", "api"),
       accent="#4f46e5", mood="light", group="digital")
def saas(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        S.glow(0.45, 0.22, 0.9, P.accent, 0.28)
        S.glow(1.75, 0.18, 0.8, P.accent2, 0.22)
        # big window with a blurred skyline
        sky_t, sky_b = ((0.20, 0.22, 0.45), (0.45, 0.35, 0.62)) if dark else ((0.62, 0.78, 0.97), (0.93, 0.96, 1.0))
        S.gradient_rect(1.0, 0.04, 2.0, 0.56, sky_t, sky_b)
        rng = S.rng
        u = 1.0
        while u < 2.0:
            w = rng.uniform(0.04, 0.09)
            h = rng.uniform(0.08, 0.30)
            S.rect(u + w / 2, 0.56 - h / 2, w, h, mix(sky_b, P.ink, rng.uniform(0.15, 0.35)), lift=0.0)
            u += w + 0.004
        for k in range(5):
            S.rect(1.0 + k * 0.25, 0.30, 0.012, 0.52, mix(P.wall_top, WHITE, 0.4), lift=0.0)
        S.rect(1.5, 0.585, 1.1, 0.025, mix(P.wall_bot, WHITE, 0.5), lift=0.0)
        S.pendant(0.55, -0.1, 0.20, mix(WHITE, P.accent_light, 0.3), 0.10)
        S.pendant(0.95, -0.1, 0.14, mix(WHITE, P.accent_light, 0.3), 0.09)
        S.bokeh(10, 0.0, 0.05, 2.0, 0.55, [mix(P.accent_light, WHITE, 0.4), (1.0, 0.95, 0.85)], 0.012, 0.04, 0.35)
        desk_t = mix(mix(P.wall_bot, P.accent, 0.12), P.ink, 0.10 if not dark else 0.0)
        S.floor(0.62, desk_t, scale(desk_t, 0.80))
    desk_t = mix(mix(P.wall_bot, P.accent, 0.12), P.ink, 0.10 if not dark else 0.0)
    S.rect(1.0, 0.622, 6.0, 0.012, scale(desk_t, 1.14), lift=0.0)
    S.soft(1.05, 0.80, 0.85, 0.20, mix(P.accent_light, WHITE, 0.5), 0.30 if not dark else 0.22, 1.5, add=True)
    S.put("digedu_plant", 0.62, 0.82, 0.19, shadow_alpha=0.30)
    S.put("digedu_laptop_dash", 1.05, 0.82, 0.56, color=P.accent, shadow_alpha=0.33)
    S.mark_subject("digedu_laptop_dash", 0.85, 0.45, 1.25, 0.63)                  # the dashboard screen: what must stay visible
    S.put("digedu_mug", 1.50, 0.92, 0.11, color=mix(P.accent_light, WHITE, 0.5))
    S.put("digedu_mouse", 1.38, 0.95, 0.04, shadow_alpha=0.3)
    S.put("digedu_notebook", 0.80, 0.96, 0.10, color=mix(P.accent, P.ink, 0.5))
    S.put("digedu_float_chart", 0.64, 0.47, 0.17, color=P.accent, shadow=False)
    S.put("digedu_float_kpi", 1.47, 0.44, 0.13, color=P.accent2, shadow=False)
    S.put("digedu_float_notify", 1.40, 0.72, 0.055, color=P.accent, shadow=False)
    S.focus("detail", 1.05, 0.54)
    with S.near():
        S.circle(0.50, 0.94, 0.035, mix(P.accent_light, WHITE, 0.3), alpha=0.5, lift=0)
        S.circle(1.62, 0.97, 0.05, P.accent, alpha=0.30, lift=0)


# ====================================================================================================== MOBILE APP
def _topbar(g, h, col):
    g.rect(0, 0.91 - h / 2, 0.42, h, col, r=0.055)
    g.rect(0, 0.91 - h * 0.75, 0.42, h * 0.5, col)


def _botbar(g, h, col):
    g.rect(0, 0.03 + h / 2, 0.42, h, col, r=0.055)
    g.rect(0, 0.03 + h * 0.75, 0.42, h * 0.5, col)


def _screen_feed(g, acc, rng):
    g.rect(0, 0.47, 0.42, 0.88, (0.955, 0.96, 0.985), r=0.055)
    _topbar(g, 0.12, acc)
    g.circle(-0.14, 0.855, 0.026, WHITE, alpha=0.9)
    g.rect(0.02, 0.855, 0.16, 0.022, WHITE, r=0.011, alpha=0.9)
    g.circle(0.16, 0.855, 0.018, WHITE, alpha=0.5)
    tops = ((0.70, (0.98, 0.72, 0.45), (0.95, 0.45, 0.45)), (0.36, (0.45, 0.78, 0.95), (0.5, 0.55, 0.95)))
    for v, c1, c2 in tops:
        _ui_card(g, 0, v, 0.38, 0.25, WHITE, 0.02)
        g.circle(-0.14, v + 0.095, 0.017, acc)
        g.rect(-0.02, v + 0.097, 0.12, 0.012, (0.55, 0.57, 0.66), r=0.006)
        g.rect(0, v + 0.007, 0.35, 0.115, c1, r=0.014)
        g.poly([(-0.175, v - 0.05), (-0.06, v + 0.03), (0.05, v - 0.05)], c2, alpha=0.8)
        g.poly([(-0.02, v - 0.05), (0.09, v + 0.015), (0.175, v - 0.05)], mix(c2, c1, 0.5), alpha=0.85)
        g.circle(0.11, v + 0.045, 0.022, WHITE, alpha=0.85)
        g.circle(-0.15, v - 0.082, 0.014, (0.95, 0.35, 0.45))
        g.rect(-0.07, v - 0.082, 0.13, 0.011, (0.7, 0.72, 0.8), r=0.005)
        g.rect(0.12, v - 0.082, 0.08, 0.011, (0.8, 0.82, 0.88), r=0.005)
    _ui_card(g, 0, 0.115, 0.38, 0.06, WHITE, 0.02)
    _botbar(g, 0.065, WHITE)
    for k in range(4):
        g.circle(-0.15 + k * 0.10, 0.065, 0.018, acc if k == 0 else (0.72, 0.74, 0.82))


def _screen_chart(g, acc, rng):
    top, bot = mix(acc, (0.03, 0.02, 0.15), 0.6), mix(acc, (0.03, 0.02, 0.12), 0.82)
    g.rect(0, 0.47, 0.42, 0.88, bot, r=0.055)
    _topbar(g, 0.44, mix(top, bot, 0.35))
    g.rect(-0.07, 0.83, 0.14, 0.014, WHITE, r=0.007, alpha=0.55)
    g.rect(-0.03, 0.765, 0.22, 0.062, WHITE, r=0.02, alpha=0.95)
    g.rect(0.14, 0.765, 0.07, 0.028, (0.3, 0.9, 0.6), r=0.014, alpha=0.9)
    pts = []
    y = 0.35
    for i in range(8):
        y = min(0.95, max(0.1, y + rng.uniform(-0.15, 0.28)))
        pts.append((-0.18 + 0.36 * i / 7.0, 0.39 + 0.26 * y))
    g.poly(pts + [(0.18, 0.39), (-0.18, 0.39)], (0.5, 0.8, 1.0), alpha=0.22)
    g.path(pts, 0.011, (0.65, 0.9, 1.0), 1.0)
    g.circle(pts[-1][0], pts[-1][1], 0.02, WHITE)
    for k in range(3):
        g.rect(-0.125 + k * 0.125, 0.17, 0.11, 0.12, WHITE, r=0.02, alpha=0.12)
        g.rect(-0.125 + k * 0.125, 0.19, 0.06, 0.016, WHITE, r=0.008, alpha=0.8)
        g.rect(-0.125 + k * 0.125, 0.145, 0.08, 0.010, WHITE, r=0.005, alpha=0.4)
    _botbar(g, 0.065, scale(bot, 0.6))
    for k in range(4):
        g.circle(-0.15 + k * 0.10, 0.065, 0.016, WHITE, alpha=0.9 if k == 1 else 0.4)


def _screen_map(g, acc, rng):
    g.rect(0, 0.47, 0.42, 0.88, (0.90, 0.93, 0.89), r=0.055)
    for (u, v, w, h) in ((-0.12, 0.74, 0.14, 0.10), (0.1, 0.78, 0.15, 0.09), (-0.1, 0.55, 0.12, 0.12), (0.13, 0.50, 0.12, 0.14),
                          (-0.15, 0.33, 0.10, 0.10), (0.10, 0.30, 0.16, 0.08)):
        g.rect(u, v, w, h, (0.96, 0.95, 0.91), r=0.01)
    g.rect(0.10, 0.62, 0.12, 0.10, (0.74, 0.88, 0.72), r=0.015)
    g.path([(-0.24, 0.46), (-0.05, 0.50), (0.08, 0.40), (0.24, 0.43)], 0.045, (0.68, 0.84, 0.95), 1.0)
    for (a, b, c_, d, w) in ((-0.22, 0.65, 0.22, 0.66, 0.026), (0.0, 0.92, 0.0, 0.2, 0.022), (-0.22, 0.88, 0.22, 0.40, 0.014),
                              (-0.22, 0.20, 0.22, 0.60, 0.014)):
        g.line(a, b, c_, d, w, WHITE, 1.0)
    g.path([(-0.2, 0.30), (-0.05, 0.45), (0.04, 0.60), (0.10, 0.77)], 0.012, acc, 1.0, smooth=False)
    g.circle(0.10, 0.80, 0.075, acc, alpha=0.18)
    g.poly([(0.10, 0.725), (0.062, 0.80), (0.138, 0.80)], acc)
    g.circle(0.10, 0.815, 0.040, acc, lift=0.1)
    g.circle(0.10, 0.815, 0.016, WHITE)
    g.circle(-0.17, 0.32, 0.022, (0.2, 0.55, 0.95))
    g.circle(-0.17, 0.32, 0.01, WHITE)
    _ui_card(g, 0, 0.20, 0.38, 0.24, WHITE, 0.025)
    g.rect(-0.04, 0.265, 0.22, 0.020, (0.18, 0.2, 0.3), r=0.01)
    g.rect(-0.07, 0.225, 0.16, 0.012, (0.7, 0.72, 0.8), r=0.006)
    g.rect(0, 0.135, 0.32, 0.055, acc, r=0.026)
    g.rect(0, 0.135, 0.12, 0.014, WHITE, r=0.007, alpha=0.9)


def _phone(c, ou, ov, ang, screen, acc, body=(0.10, 0.10, 0.13), k=1.0):
    rng = c.rng
    g = _G(c, ou, ov, ang, k)
    # floor contact / soft cast shadow behind the leaning phone
    soft_disc(c, ou + 0.03, ov + 0.01, 0.20 * k, 0.04 * k, BLACK, 0.45, 1.5)
    g.rect(0, 0.47, 0.47, 0.94, body, r=0.075, lift=0.10)
    g.line(-0.232, 0.12, -0.232, 0.82, 0.006, mix(body, WHITE, 0.55), 0.7)          # lit metal edge
    g.rect(0.2375, 0.62, 0.008, 0.10, scale(body, 1.5), r=0.004)
    g.rect(-0.2375, 0.70, 0.008, 0.06, scale(body, 1.5), r=0.004)
    screen(g, acc, rng)
    g.rect(0, 0.905, 0.12, 0.028, (0.02, 0.02, 0.03), r=0.014)
    g.circle(0.04, 0.905, 0.007, (0.1, 0.12, 0.25))
    g.poly([(-0.2, 0.91), (-0.02, 0.91), (-0.17, 0.05), (-0.2, 0.05)], WHITE, alpha=0.06)


@sprop("digedu_phones", aspect=1.5, fill=0.97)
def phones(c, color):
    acc = color or (0.42, 0.36, 0.9)
    _phone(c, -0.42, 0.01, 13, _screen_chart, acc, k=0.90)
    _phone(c, 0.44, 0.0, -11, _screen_map, acc, k=0.92)
    _phone(c, 0.0, 0.0, 0.0, _screen_feed, acc, k=1.0)
    c.glow(0.0, 0.5, 1.1, mix(acc, WHITE, 0.6), 0.05)


def _icon(c, color, kind):
    soft_disc(c, 0.04, -0.06, 0.62, 0.14, (0.05, 0.04, 0.2), 0.30, 1.3)
    g = _G(c, 0.0, 0.5)
    g.rect(0.0, -0.01, 0.98, 0.98, scale(color, 0.62), r=0.24)
    g.rect(0.0, 0.0, 0.96, 0.96, color, r=0.23, lift=0.18)
    g.poly([(-0.46, 0.46), (0.1, 0.46), (-0.46, -0.1)], WHITE, alpha=0.14)
    if kind == "chat":
        g.rect(0.0, 0.05, 0.56, 0.38, WHITE, r=0.14)
        g.poly([(-0.14, -0.12), (0.0, -0.12), (-0.18, -0.28)], WHITE)
        for k in range(3):
            g.circle(-0.14 + k * 0.14, 0.05, 0.035, color)
    elif kind == "chart":
        for k, h in enumerate((0.20, 0.34, 0.52)):
            g.rect(-0.18 + k * 0.18, -0.24 + h / 2, 0.11, h, WHITE, r=0.03)
    else:
        g.circle(0.0, 0.10, 0.20, WHITE)
        g.poly([(-0.17, 0.03), (0.17, 0.03), (0.0, -0.28)], WHITE)
        g.circle(0.0, 0.10, 0.075, color)


@sprop("digedu_icon_chat", aspect=1.0, fill=1.0)
def icon_chat(c, color):
    _icon(c, color or (0.42, 0.36, 0.9), "chat")


@sprop("digedu_icon_chart", aspect=1.0, fill=1.0)
def icon_chart(c, color):
    _icon(c, color or (0.3, 0.7, 0.9), "chart")


@sprop("digedu_icon_pin", aspect=1.0, fill=1.0)
def icon_pin(c, color):
    _icon(c, color or (0.95, 0.4, 0.5), "pin")


@sprop("digedu_podium", aspect=1.22, fill=0.84)
def podium(c, color):
    col = color or (0.9, 0.9, 0.95)
    ao(c, 0.0, 0.0, 1.15, 0.32)
    craft.cylinder(c, 0.0, 0.0, 0.5, 0.64, mix(col, WHITE, 0.15), scale(col, 0.60), mix(col, WHITE, 0.30))
    c.ellipse(0.0, 0.645, 0.40, 0.40 * TILT * 0.95, scale(col, 0.92), lift=0.05)
    gloss(c, -0.25, 0.70, 0.18, 0.06, 5, 0.45)
    gloss(c, -0.30, 0.32, 0.04, 0.26, 0, 0.30)


@niche("mobile-app", "Mobile app development", subjects=("digedu_phones",),
       strong=("mobile app", "app development", "android app", "ios app", "smartphone app", "app developer", "mobile application",
               "ऐप", "मोबाइल ऐप", "एप्प", "mobile app banwana", "app banane wale"),
       weak=("android", "ios", "iphone", "play store", "app store", "flutter", "react native"),
       accent="#6c5ce7", mood="cool", group="digital", avoid=("ecommerce", "e-commerce", "online store"))
def mobile_app(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.66)
        S.glow(0.4, 0.30, 1.1, P.accent, 0.34)
        S.glow(1.6, 0.25, 1.0, P.accent2, 0.30)
        S.glow(1.05, 0.50, 0.7, mix(P.accent_light, WHITE, 0.5), 0.20)
        S.bokeh(14, 0.0, 0.05, 2.0, 0.60, [mix(P.accent_light, WHITE, 0.4), mix(P.accent2, WHITE, 0.5)], 0.015, 0.05, 0.28)
        fl_t = mix(P.wall_bot, P.accent, 0.10 if not dark else 0.0)
        S.floor(0.66, scale(fl_t, 0.96) if not dark else scale(P.floor_top, 0.6), scale(fl_t, 0.74) if not dark else scale(P.floor_bot, 0.5))
    S.soft(1.05, 0.88, 1.1, 0.22, mix(P.accent_light, WHITE, 0.5), 0.34 if not dark else 0.30, 1.5, add=True)
    pod = mix(P.wall_top, P.accent_light, 0.3) if not dark else mix(P.accent, P.ink, 0.5)
    S.put("digedu_podium", 0.62, 0.95, 0.14, color=pod, shadow_alpha=0.34)
    S.put("digedu_podium", 1.50, 0.97, 0.10, color=pod, shadow_alpha=0.34)
    S.put("digedu_phones", 1.05, 0.90, 0.60, color=P.accent, shadow_alpha=0.30)
    S.mark_subject("digedu_phones", 0.93, 0.50, 1.17, 0.72)                        # the centre phone screen
    S.put("digedu_icon_chat", 0.62, 0.79, 0.12, color=P.accent2, shadow=False)
    S.put("digedu_icon_chart", 1.50, 0.80, 0.10, color=mix(P.accent, (0.2, 0.7, 0.9), 0.5), shadow=False)
    S.put("digedu_icon_pin", 1.30, 0.34, 0.09, color=mix(P.accent, (0.95, 0.4, 0.5), 0.6), shadow=False)
    S.focus("detail", 1.05, 0.60)
    with S.near():
        S.circle(0.58, 0.40, 0.04, mix(P.accent_light, WHITE, 0.4), alpha=0.5, lift=0)
        S.circle(1.62, 0.98, 0.06, P.accent2, alpha=0.30, lift=0)


# ====================================================================================================== ECOMMERCE
KRAFT = (0.80, 0.62, 0.40)


def _product_pic(g, u, v, w, h, kind, col, rng):
    bg = mix(col, WHITE, 0.72)
    g.rect(u, v, w, h, bg, r=0.012)
    if kind == 0:                               # ball / pot
        g.circle(u, v - h * 0.04, h * 0.34, col, lift=0.2)
        g.circle(u - h * 0.1, v + h * 0.08, h * 0.09, WHITE, alpha=0.5)
    elif kind == 1:                             # bag
        g.rect(u, v - h * 0.06, w * 0.5, h * 0.55, col, r=0.01, lift=0.15)
        g.arc(u, v + h * 0.2, w * 0.14, 0, 180, 0.008, scale(col, 0.7))
    elif kind == 2:                             # sneaker
        g.poly([(u - w * 0.3, v - h * 0.22), (u + w * 0.32, v - h * 0.22), (u + w * 0.32, v - h * 0.05), (u + w * 0.1, v + h * 0.0),
                (u - w * 0.05, v + h * 0.2), (u - w * 0.3, v + h * 0.18)], col, lift=0.12)
        g.rect(u + 0.0, v - h * 0.25, w * 0.64, h * 0.07, WHITE, r=0.004)
    elif kind == 3:                             # bottle
        g.rect(u, v - h * 0.06, w * 0.28, h * 0.5, col, r=0.02, lift=0.15)
        g.rect(u, v + h * 0.28, w * 0.12, h * 0.14, scale(col, 0.7), r=0.004)
        g.rect(u, v - h * 0.08, w * 0.28, h * 0.16, WHITE, alpha=0.8)
    else:                                       # watch
        g.rect(u, v, w * 0.16, h * 0.7, scale(col, 0.75), r=0.01)
        g.circle(u, v, h * 0.22, mix(col, WHITE, 0.2), lift=0.1)
        g.circle(u, v, h * 0.16, WHITE)
        g.line(u, v, u, v + h * 0.1, 0.006, (0.2, 0.2, 0.25))
        g.line(u, v, u + h * 0.07, v, 0.006, (0.2, 0.2, 0.25))


def _shop_ui(g, acc):
    rng = g.c.rng
    ink = (0.16, 0.18, 0.28)
    g.rect(0, 0, 1.26, 0.70, (0.975, 0.97, 0.965))
    g.rect(0, 0.315, 1.26, 0.07, WHITE)
    g.circle(-0.56, 0.315, 0.022, acc)
    g.rect(-0.47, 0.315, 0.10, 0.016, ink, r=0.008)
    for k in range(3):
        g.rect(-0.30 + k * 0.10, 0.315, 0.07, 0.012, (0.72, 0.74, 0.8), r=0.006)
    g.rect(0.22, 0.315, 0.30, 0.032, (0.93, 0.93, 0.95), r=0.016)
    g.circle(0.55, 0.315, 0.017, ink)
    g.circle(0.585, 0.33, 0.012, acc)
    # banner
    g.rect(0.0, 0.155, 1.20, 0.19, acc, r=0.018, lift=0.12)
    g.circle(0.40, 0.155, 0.17, mix(acc, WHITE, 0.25), alpha=0.8)
    g.circle(0.46, 0.14, 0.11, mix(acc, WHITE, 0.55), alpha=0.9)
    g.rect(0.38, 0.14, 0.12, 0.075, WHITE, r=0.012, alpha=0.9)
    g.rect(-0.30, 0.20, 0.44, 0.032, WHITE, r=0.012)
    g.rect(-0.36, 0.15, 0.30, 0.016, WHITE, r=0.008, alpha=0.7)
    g.rect(-0.42, 0.095, 0.15, 0.04, ink, r=0.02)
    # product grid
    cols = (acc, (0.25, 0.65, 0.9), (0.95, 0.75, 0.2), (0.3, 0.75, 0.5), (0.8, 0.4, 0.75))
    for i in range(5):
        u = -0.48 + i * 0.24
        _ui_card(g, u, -0.185, 0.215, 0.30, WHITE, 0.012)
        _product_pic(g, u, -0.12, 0.19, 0.17, (i + 1) % 5, cols[(i + 2) % 5], rng)
        g.rect(u - 0.01, -0.245, 0.13, 0.013, ink, r=0.006, alpha=0.8)
        g.rect(u - 0.04, -0.28, 0.07, 0.013, acc, r=0.006)
        g.circle(u + 0.075, -0.28, 0.011, (0.9, 0.4, 0.5))


@sprop("digedu_laptop_shop", aspect=1.7, fill=0.92)
def laptop_shop(c, color):
    _laptop(c, _shop_ui, color or (1.0, 0.5, 0.31))


@sprop("digedu_parcel", aspect=1.55, fill=0.76)
def parcel(c, color):
    rng = c.rng
    k = color or KRAFT
    ao(c, 0.0, 0.0, 1.2, 0.34)
    u, w, h, d = -0.04, 0.90, 0.55, 0.5
    box3d(c, u, 0.0, w, h, d, k, mix(k, WHITE, 0.24), scale(k, 0.64), lift=0.10)
    ox, oy = d * 0.55, d * 0.42
    tape = (0.88, 0.76, 0.55)
    c.poly([(u - 0.06, h), (u + 0.06, h), (u + 0.06 + ox, h + oy), (u - 0.06 + ox, h + oy)], tape, alpha=0.95)
    _crect(c, u, h * 0.5, 0.12, h, tape, lift=0.05, alpha=0.9)
    # shipping label with a barcode
    _crect(c, u - 0.26, 0.20, 0.30, 0.22, (0.98, 0.98, 0.97), r=0.01, lift=0.0)
    for i in range(14):
        _crect(c, u - 0.38 + i * 0.016, 0.145, 0.006 + (i % 3) * 0.004, 0.07, (0.15, 0.15, 0.18), lift=0.0)
    _crect(c, u - 0.30, 0.255, 0.18, 0.018, (0.4, 0.4, 0.45), r=0.008, lift=0.0)
    _crect(c, u - 0.32, 0.225, 0.12, 0.014, (0.6, 0.6, 0.65), r=0.007, lift=0.0)
    _crect(c, u + 0.28, 0.12, 0.17, 0.12, mix(k, (0.15, 0.1, 0.05), 0.3), r=0.01, lift=0.0, alpha=0.5)       # fragile mark
    for _ in range(30):                                                                                   # cardboard fibre
        x, y = rng.uniform(u - 0.44, u + 0.44), rng.uniform(0.03, h - 0.03)
        c.line(x, y, x + rng.uniform(0.02, 0.08), y + rng.uniform(-0.004, 0.004), 0.003, scale(k, rng.uniform(0.78, 0.92)), 0.35)
    soft_disc(c, u - 0.2, h - 0.05, 0.4, 0.2, WHITE, 0.14, 1.2, add=True)
    soft_disc(c, u + w / 2 - 0.04, 0.1, 0.12, 0.3, BLACK, 0.18, 1.2)


@sprop("digedu_bag", aspect=0.95, fill=1.0)
def shopping_bag(c, color):
    rng = c.rng
    acc = color or (1.0, 0.5, 0.31)
    ao(c, 0.0, 0.0, 0.95, 0.28)
    w, h, d = 0.58, 0.66, 0.34
    u = -0.1
    string = (0.97, 0.93, 0.86)
    craft.arc(c, u, h - 0.03, 0.15, 0.30, 0, 180, 0.022, scale(string, 0.7), 1.0, 12)        # back handle
    box3d(c, u, 0.0, w, h, d, acc, mix(acc, WHITE, 0.32), scale(acc, 0.60), lift=0.14)
    ox = d * 0.55
    c.poly([(u + w / 2, h), (u + w / 2 + ox, h + d * 0.42), (u + w / 2 + ox, h + d * 0.42 - 0.06), (u + w / 2, h - 0.06)], mix(acc, WHITE, 0.15), alpha=0.5)
    _crect(c, u, h - 0.03, w, 0.06, mix(acc, WHITE, 0.2), lift=0.0, alpha=0.55)                                # folded cuff
    _crect(c, u, 0.02, w, 0.03, scale(acc, 0.7), lift=0.0, alpha=0.6)
    soft_disc(c, u - 0.12, h * 0.6, 0.16, 0.34, WHITE, 0.16, 1.2, add=True)
    soft_disc(c, u + w * 0.5 - 0.05, h * 0.5, 0.12, 0.34, BLACK, 0.20, 1.2)
    # logo: a ring with a heart
    c.ellipse(u, 0.36, 0.13, 0.13, mix(acc, WHITE, 0.88), lift=0.05)
    c.ellipse(u, 0.36, 0.105, 0.105, acc, lift=0.0)
    c.circle(u - 0.027, 0.378, 0.03, WHITE, lift=0)
    c.circle(u + 0.027, 0.378, 0.03, WHITE, lift=0)
    c.poly([(u - 0.056, 0.368), (u + 0.056, 0.368), (u, 0.31)], WHITE)
    craft.arc(c, u + 0.02, h + 0.0, 0.12, 0.26, 0, 180, 0.022, string, 1.0, 12)                    # front handle
    craft.arc(c, u + 0.02, h + 0.0, 0.12, 0.26, 20, 120, 0.008, WHITE, 0.6, 8)
    c.circle(u - 0.1, h - 0.03, 0.012, scale(string, 0.6), lift=0)
    c.circle(u + 0.14, h - 0.03, 0.012, scale(string, 0.6), lift=0)


@sprop("digedu_cart", aspect=1.0, fill=1.0)
def cart(c, color):
    acc = color or (1.0, 0.5, 0.31)
    steel = (0.78, 0.8, 0.84)
    ao(c, 0.0, 0.0, 0.95, 0.20)
    c.line(-0.46, 0.76, -0.36, 0.45, 0.04, scale(steel, 0.8))
    c.line(-0.62, 0.88, -0.46, 0.76, 0.04, scale(steel, 0.8))
    _crect(c, -0.66, 0.9, 0.12, 0.045, (0.12, 0.12, 0.16), r=0.02)
    c.line(-0.30, 0.17, 0.42, 0.17, 0.035, scale(steel, 0.75))
    for u in (-0.24, 0.30):
        c.line(u, 0.17, u, 0.27, 0.03, scale(steel, 0.7))
        c.circle(u, 0.09, 0.085, (0.12, 0.12, 0.15))
        c.circle(u, 0.09, 0.035, steel)
    # basket
    c.poly([(-0.46, 0.80), (0.58, 0.80), (0.46, 0.30), (-0.34, 0.30)], mix(acc, WHITE, 0.0), lift=0.14)
    c.poly([(-0.46, 0.80), (0.58, 0.80), (0.66, 0.74), (-0.38, 0.74)], mix(acc, WHITE, 0.2), alpha=0.7)
    c.poly([(0.58, 0.80), (0.66, 0.74), (0.54, 0.26), (0.46, 0.30)], scale(acc, 0.65))
    for k in range(5):
        x0 = -0.34 + k * 0.2
        c.line(-0.46 + k * 0.26, 0.78, -0.34 + k * 0.2, 0.32, 0.012, mix(acc, WHITE, 0.55), 0.85)
    for k in range(3):
        y = 0.42 + k * 0.14
        t = (y - 0.30) / 0.50
        c.line(-0.34 - 0.12 * t, y, 0.46 + 0.12 * t, y, 0.012, mix(acc, WHITE, 0.55), 0.85)
    _crect(c, -0.18, 0.88, 0.26, 0.14, (0.97, 0.97, 0.98), r=0.015, lift=0.1)          # a little parcel in the cart
    _crect(c, -0.18, 0.88, 0.04, 0.14, (0.8, 0.7, 0.5), lift=0)
    soft_disc(c, -0.2, 0.7, 0.24, 0.12, WHITE, 0.22, 1.2, add=True)


@niche("ecommerce", "E-commerce / online store", subjects=("digedu_laptop_shop",),
       strong=("ecommerce", "e-commerce", "online store", "online shop", "online shopping", "webshop", "shopify", "ecommerce website",
               "ऑनलाइन दुकान", "ऑनलाइन स्टोर", "online dukan", "online selling", "ई-कॉमर्स", "ऑनलाइन शॉपिंग"),
       weak=("cart", "checkout", "dropshipping", "delivery", "orders", "marketplace", "woocommerce"),
       accent="#ff7f50", mood="light", group="digital", avoid=("mobile app",))
def ecommerce(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.glow(0.5, 0.25, 1.0, P.accent_light, 0.22)
        S.glow(1.9, 0.2, 0.9, P.accent2, 0.16)
        # blurred shelving with stock boxes
        for row, v in enumerate((0.16, 0.34, 0.52)):
            S.rect(1.2, v + 0.012, 2.6, 0.014, mix(P.wall_bot, P.ink, 0.45), lift=0.0)
            u = 0.0
            while u < 2.2:
                w, hh = rng.uniform(0.07, 0.14), rng.uniform(0.07, 0.15)
                col = rng.choice([KRAFT, mix(KRAFT, WHITE, 0.4), P.accent, mix(P.accent, WHITE, 0.5), (0.95, 0.95, 0.96)])
                S.rect(u + w / 2, v - hh / 2, w, hh, scale(col, 0.7 if dark else 1.0), lift=0.0)
                u += w + rng.uniform(0.004, 0.03)
        if dark:
            S.window(0.18, 0.28, 0.2, 0.3, (0.10, 0.12, 0.28), (0.22, 0.20, 0.42), (0.35, 0.33, 0.42))
        else:
            S.window(0.18, 0.28, 0.2, 0.3)
        S.pendant(1.0, -0.1, 0.12, (1.0, 0.9, 0.72), 0.08)
        S.pendant(1.6, -0.1, 0.14, (1.0, 0.9, 0.72), 0.08)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.soft(1.1, 0.66, 0.95, 0.15, (1.0, 0.92, 0.75), 0.24, 1.5, add=True)
    S.wood(-1.6, 0.60, 4.0, 1.8, P.surface, plank=0.12, grain=0.25)
    S.rect(1.0, 0.60, 7.0, 0.008, scale(P.surface, 0.5), lift=0.0)
    S.put("digedu_laptop_shop", 1.06, 0.80, 0.44, color=P.accent)
    S.mark_subject("digedu_laptop_shop", 0.9, 0.47, 1.22, 0.65)                    # the storefront screen
    S.put("digedu_bag", 0.72, 0.93, 0.36, color=P.accent, shadow_alpha=0.32)
    S.put("digedu_parcel", 1.44, 0.92, 0.21)
    S.put("digedu_parcel", 1.41, 0.765, 0.12, color=mix(KRAFT, WHITE, 0.25))
    S.put("digedu_cart", 0.97, 0.99, 0.17, color=P.accent)
    S.focus("detail", 1.06, 0.56)
    with S.near():
        S.circle(0.52, 0.38, 0.04, P.accent_light, alpha=0.5, lift=0)
        S.circle(1.62, 0.97, 0.05, P.accent, alpha=0.30, lift=0)


# ====================================================================================================== DIGITAL AGENCY
def _design_ui(g, acc, hi=(0.35, 0.65, 1.0)):
    rng = g.c.rng
    g.rect(0, 0, 1.26, 0.70, (0.115, 0.115, 0.15))
    g.rect(0, 0.33, 1.26, 0.04, (0.16, 0.16, 0.21))
    for k in range(6):
        g.circle(-0.58 + k * 0.05, 0.33, 0.009, (0.75, 0.75, 0.85) if k != 2 else acc)
    g.circle(0.58, 0.33, 0.014, acc)
    # layers panel
    g.rect(-0.54, -0.02, 0.18, 0.64, (0.15, 0.15, 0.19))
    for k in range(7):
        y = 0.24 - k * 0.08
        if k == 2:
            g.rect(-0.54, y, 0.17, 0.05, mix(acc, (0.1, 0.1, 0.15), 0.55), r=0.01)
        g.rect(-0.58, y, 0.02, 0.02, (0.7, 0.7, 0.8), r=0.004, alpha=0.8)
        g.rect(-0.515, y, 0.07 + 0.01 * (k % 3), 0.013, (0.8, 0.8, 0.9), r=0.006, alpha=0.6)
    # properties panel with colour swatches
    g.rect(0.54, -0.02, 0.18, 0.64, (0.15, 0.15, 0.19))
    sw = (acc, mix(acc, (0.4, 0.3, 1.0), 0.6), (1.0, 0.75, 0.2), (0.25, 0.8, 0.8), (1.0, 1.0, 1.0), (0.2, 0.2, 0.28))
    for k, cc in enumerate(sw):
        g.rect(0.49 + (k % 3) * 0.055, 0.24 - (k // 3) * 0.055, 0.042, 0.042, cc, r=0.008, lift=0.1)
    for k in range(4):
        y = 0.07 - k * 0.07
        g.rect(0.54, y, 0.15, 0.011, (0.3, 0.3, 0.38), r=0.005)
        g.rect(0.50 + 0.03 * (k % 3), y, 0.07 + 0.03 * (k % 3), 0.011, acc if k % 2 == 0 else hi, r=0.005)
        g.circle(0.50 + 0.07 + 0.03 * (k % 3) + 0.0, y, 0.014, WHITE)
    # canvas with a web page mock
    g.rect(0.0, -0.02, 0.88, 0.62, (0.22, 0.22, 0.27))
    g.rect(0.02, -0.02, 0.62, 0.56, (0.97, 0.97, 0.98), r=0.008)
    g.rect(0.02, 0.215, 0.62, 0.04, WHITE)
    g.circle(-0.26, 0.215, 0.012, acc)
    for k in range(3):
        g.rect(0.14 + k * 0.07, 0.215, 0.05, 0.010, (0.55, 0.55, 0.62), r=0.005)
    g.rect(0.02, 0.10, 0.60, 0.20, mix(acc, (0.35, 0.2, 0.9), 0.5), r=0.006, lift=0.12)
    g.circle(0.28, 0.10, 0.12, mix(acc, WHITE, 0.3), alpha=0.7)
    g.circle(0.22, 0.12, 0.07, (1.0, 0.8, 0.35), alpha=0.9)
    g.rect(-0.14, 0.14, 0.22, 0.026, WHITE, r=0.01)
    g.rect(-0.17, 0.095, 0.16, 0.014, WHITE, r=0.006, alpha=0.7)
    g.rect(-0.2, 0.045, 0.09, 0.03, WHITE, r=0.015)
    for k, cc in enumerate((acc, (1.0, 0.75, 0.2), (0.25, 0.8, 0.8))):
        u = -0.15 + k * 0.2
        g.rect(u, -0.06, 0.17, 0.12, mix(cc, WHITE, 0.55), r=0.006)
        g.circle(u, -0.05, 0.03, cc)
        g.rect(u, -0.15, 0.15, 0.012, (0.5, 0.5, 0.58), r=0.006)
        g.rect(u - 0.03, -0.18, 0.09, 0.010, (0.75, 0.75, 0.8), r=0.005)
    # selection box with handles around the hero
    for (a, b, c_, d) in ((-0.28, 0.20, 0.32, 0.20), (-0.28, 0.0, 0.32, 0.0), (-0.28, 0.20, -0.28, 0.0), (0.32, 0.20, 0.32, 0.0)):
        g.line(a, b, c_, d, 0.004, hi, 1.0)
    for (a, b) in ((-0.28, 0.20), (0.32, 0.20), (-0.28, 0.0), (0.32, 0.0), (0.02, 0.20), (0.02, 0.0)):
        g.rect(a, b, 0.016, 0.016, WHITE, lift=0.0)
        g.rect(a, b, 0.010, 0.010, hi, lift=0.0)
    # pen tool bezier with handles
    pts = [(-0.60 + 0.0, 0.0)]
    g.path([(0.36, -0.22), (0.45, -0.10), (0.38, 0.02), (0.30, 0.10)], 0.007, acc, 1.0)
    for (a, b, c_, d) in ((0.36, -0.22, 0.30, -0.19), (0.38, 0.02, 0.43, 0.07), (0.30, 0.10, 0.27, 0.14)):
        g.line(a, b, c_, d, 0.003, (0.8, 0.8, 0.9), 0.8)
        g.circle(c_, d, 0.008, WHITE)
    for (a, b) in ((0.36, -0.22), (0.38, 0.02), (0.30, 0.10)):
        g.rect(a, b, 0.016, 0.016, hi, lift=0.0)


@sprop("digedu_monitor_design", aspect=1.34, fill=1.0)
def monitor_design(c, color):
    acc = color or (0.91, 0.26, 0.58)
    steel = (0.30, 0.31, 0.35)
    ao(c, 0.0, 0.0, 0.8, 0.14)
    c.ellipse(0.0, 0.03, 0.34, 0.05, scale(steel, 0.7), lift=0.1)
    c.ellipse(0.0, 0.04, 0.32, 0.04, steel, lift=0.15)
    craft.hshade_box(c, 0.0, 0.14, 0.11, 0.18, mix(steel, WHITE, 0.25), scale(steel, 0.55))
    _crect(c, 0.0, 0.61, 1.34, 0.78, (0.06, 0.06, 0.08), r=0.025, lift=0.12)
    _crect(c, 0.0, 0.61, 1.30, 0.74, (0.02, 0.02, 0.03), r=0.02, lift=0.0)
    g = _G(c, 0.0, 0.61)
    _design_ui(g, acc)
    _sheen(g, -0.2, 0.0, 1.0, 0.7, 0.06)
    c.line(-0.6, 0.985, 0.6, 0.985, 0.004, WHITE, 0.2)
    c.glow(0.0, 0.6, 0.75, mix(acc, WHITE, 0.4), 0.08)


@sprop("digedu_swatches", aspect=1.25, fill=0.90)
def swatches(c, color):
    acc = color or (0.91, 0.26, 0.58)
    ao(c, 0.1, 0.0, 1.0, 0.2)
    cols = (acc, (0.55, 0.38, 0.95), (1.0, 0.75, 0.2), (0.25, 0.8, 0.8), (0.30, 0.85, 0.5))
    for i, col in enumerate(cols):
        ang = 4 + i * 17
        g = _G(c, -0.38, 0.04, ang)
        g.rect(0.012, 0.40, 0.25, 0.82, (0.0, 0.0, 0.0), r=0.02, alpha=0.22)
        g.rect(0.0, 0.41, 0.24, 0.82, (0.97, 0.97, 0.96), r=0.018, lift=0.04)
        g.rect(0.0, 0.58, 0.20, 0.44, col, r=0.01, lift=0.12)
        g.poly([(-0.10, 0.80), (0.06, 0.80), (-0.10, 0.60)], WHITE, alpha=0.15)
        g.rect(-0.02, 0.22, 0.14, 0.018, (0.35, 0.35, 0.4), r=0.009, alpha=0.8)
        g.rect(-0.04, 0.17, 0.10, 0.013, (0.65, 0.65, 0.7), r=0.006, alpha=0.8)
    c.circle(-0.38, 0.06, 0.035, (0.75, 0.76, 0.8), lift=0.2)
    c.circle(-0.38, 0.06, 0.012, (0.4, 0.4, 0.45), lift=0)


@sprop("digedu_tablet", aspect=3.4, fill=0.38)
def pen_tablet(c, color):
    acc = color or (0.91, 0.26, 0.58)
    ao(c, 0.0, 0.0, 1.3, 0.42)
    body = (0.13, 0.13, 0.16)
    w, h, d = 1.1, 0.045, 0.62
    box3d(c, -0.12, 0.0, w, h, d, body, mix(body, WHITE, 0.10), scale(body, 0.5), lift=0.06, dx=0.35, dy=0.5)
    ox, oy = d * 0.35, d * 0.5
    x0, x1, v = -0.12 - w / 2, -0.12 + w / 2, h
    # active area on the top face (parallelogram) with a sketch on it
    def pp(a, b):          # a, b in 0..1 across / into the top face
        return (x0 + a * w + b * ox, v + b * oy)
    c.poly([pp(0.20, 0.12), pp(0.95, 0.12), pp(0.95, 0.88), pp(0.20, 0.88)], (0.20, 0.20, 0.25), lift=0.0)
    c.path([pp(0.28, 0.30), pp(0.42, 0.62), pp(0.58, 0.36), pp(0.74, 0.70), pp(0.88, 0.45)], 0.018, acc, 1.0)
    for k in range(3):
        a, b = pp(0.07, 0.26 + k * 0.2)
        c.ellipse(a, b, 0.022, 0.012, (0.4, 0.4, 0.46), lift=0.1)
    # stylus
    c.line(0.30, 0.17, 0.50, 0.30, 0.040, (0.08, 0.08, 0.10), 1.0)
    c.line(0.29, 0.168, 0.37, 0.218, 0.040, acc, 1.0)
    c.line(0.285, 0.165, 0.265, 0.152, 0.012, (0.9, 0.9, 0.95), 1.0)
    c.line(0.30, 0.185, 0.50, 0.318, 0.008, WHITE, 0.4)
    soft_disc(c, -0.3, 0.15, 0.4, 0.15, WHITE, 0.12, 1.3, add=True)


@sprop("digedu_sticky", aspect=1.0, fill=0.62)
def sticky(c, color):
    rng = c.rng
    col = color or (1.0, 0.85, 0.3)
    g = _G(c, 0.0, 0.32, 6)
    g.rect(0.02, -0.015, 0.78, 0.74, (0.0, 0.0, 0.0), r=0.01, alpha=0.20)
    g.rect(0.0, 0.0, 0.76, 0.72, col, r=0.01, lift=0.06)
    g.rect(0.0, -0.31, 0.76, 0.1, scale(col, 0.92), r=0.01, alpha=0.7)
    g.poly([(0.38, 0.36), (0.30, 0.36), (0.38, 0.28)], scale(col, 0.78), alpha=0.9)
    for k in range(3):
        g.rect(-0.04 - 0.04 * (k % 2), 0.16 - k * 0.14, 0.42 + 0.1 * (k % 3), 0.035, scale(col, 0.62), r=0.015, alpha=0.7)
    g.path([(-0.25, -0.2), (-0.1, -0.12), (0.05, -0.22), (0.2, -0.12)], 0.025, scale(col, 0.55), 0.8)


@sprop("digedu_moodboard", aspect=1.35, fill=1.0)
def moodboard(c, color):
    rng = c.rng
    felt = color or (0.20, 0.17, 0.2)
    ao(c, 0.0, 0.0, 1.5, 0.2, 0.2)
    _crect(c, 0.0, 0.5, 1.38, 1.02, scale(felt, 1.35), r=0.02, lift=0.08)
    _crect(c, 0.0, 0.5, 1.32, 0.96, felt, r=0.015, lift=0.0)
    for _ in range(40):                                              # felt fibres
        x, y = rng.uniform(-0.64, 0.64), rng.uniform(0.04, 0.96)
        c.line(x, y, x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), 0.004, scale(felt, rng.uniform(0.8, 1.35)), 0.35)
    photos = ((-0.38, 0.68, 0.50, 0.36, -5, ((0.98, 0.72, 0.5), (0.9, 0.35, 0.5))), (0.12, 0.74, 0.40, 0.30, 4, ((0.5, 0.78, 0.95), (0.3, 0.45, 0.8))),
              (0.50, 0.62, 0.30, 0.44, -3, ((0.4, 0.85, 0.7), (0.15, 0.5, 0.5))), (-0.40, 0.28, 0.34, 0.40, 3, ((0.95, 0.85, 0.5), (0.9, 0.55, 0.2))),
              (0.04, 0.35, 0.46, 0.30, -4, ((0.75, 0.6, 0.95), (0.45, 0.3, 0.8))))
    for (u, v, w, h, ang, (c1, c2)) in photos:
        g = _G(c, u, v, ang)
        g.rect(0.012, -0.012, w + 0.03, h + 0.03, (0.0, 0.0, 0.0), r=0.004, alpha=0.30)
        g.rect(0.0, 0.0, w + 0.03, h + 0.03, (0.97, 0.97, 0.95), r=0.004)
        g.rect(0.0, 0.0, w, h, c1, r=0.002, lift=0.12)
        g.poly([(-w / 2, -h / 2), (-w * 0.1, h * 0.2), (w * 0.2, -h / 2)], c2, alpha=0.9)
        g.poly([(-w * 0.1, -h / 2), (w * 0.3, h * 0.05), (w / 2, -h / 2)], mix(c2, c1, 0.4), alpha=0.9)
        g.circle(w * 0.22, h * 0.24, h * 0.11, WHITE, alpha=0.9)
    for k, (u, v, col, ang) in enumerate(((0.42, 0.25, (1.0, 0.85, 0.3), 7), (0.25, 0.12, (1.0, 0.55, 0.7), -6), (-0.1, 0.1, (0.6, 0.9, 0.7), 4))):
        g = _G(c, u, v, ang)
        g.rect(0.012, -0.012, 0.19, 0.19, (0, 0, 0), alpha=0.28)
        g.rect(0.0, 0.0, 0.19, 0.19, col, lift=0.06)
        g.rect(-0.01, 0.03, 0.12, 0.012, scale(col, 0.6), r=0.006, alpha=0.7)
        g.rect(0.0, -0.01, 0.10, 0.012, scale(col, 0.6), r=0.006, alpha=0.7)
    for k, (u, v, col) in enumerate(((0.64, 0.30, (0.91, 0.26, 0.58)), (0.62, 0.17, (0.25, 0.8, 0.8)), (0.56, 0.08, (1.0, 0.75, 0.2)))):
        _crect(c, u, v, 0.09, 0.09, col, r=0.008, lift=0.12)
    c.path([(-0.38, 0.78), (-0.1, 0.55), (0.14, 0.5), (0.42, 0.28)], 0.006, (0.85, 0.2, 0.25), 0.9)
    for (u, v) in ((-0.38, 0.78), (0.14, 0.5), (0.42, 0.28), (0.12, 0.88), (-0.40, 0.46)):
        c.circle(u, v, 0.018, (0.9, 0.2, 0.25), lift=0.2)
        soft_disc(c, u - 0.006, v + 0.006, 0.008, 0.006, WHITE, 0.8, 1.0, add=True)


@sprop("digedu_lamp", aspect=0.85, fill=1.0)
def desk_lamp(c, color):
    col = color or (0.95, 0.95, 0.96)
    ao(c, 0.0, 0.0, 0.7, 0.18)
    c.ellipse(0.0, 0.025, 0.24, 0.24 * TILT, scale(col, 0.6), lift=0)
    c.ellipse(0.0, 0.04, 0.23, 0.23 * TILT, col, lift=0.14)
    c.line(0.0, 0.05, -0.12, 0.46, 0.035, scale(col, 0.8))
    c.line(-0.12, 0.46, 0.20, 0.78, 0.030, scale(col, 0.85))
    c.circle(-0.12, 0.46, 0.035, scale(col, 0.6))
    c.circle(0.0, 0.07, 0.03, scale(col, 0.65))
    # lamp head: a dome shade pointing down-right with a bright opening
    c.ellipse(0.30, 0.80, 0.25, 0.115, scale(col, 0.78), angle=-40, lift=0.3)
    c.ellipse(0.28, 0.835, 0.20, 0.05, mix(col, WHITE, 0.45), angle=-40, lift=0.0, alpha=0.7)
    c.ellipse(0.455, 0.675, 0.052, 0.115, (1.0, 0.93, 0.74), angle=-40, lift=0.0)
    c.ellipse(0.455, 0.675, 0.032, 0.08, WHITE, angle=-40, lift=0.0, alpha=0.9)
    c.circle(0.17, 0.80, 0.03, scale(col, 0.6), lift=0.2)
    c.glow(0.50, 0.62, 0.34, (1.0, 0.85, 0.55), 0.6)
    c.glow(0.50, 0.62, 0.12, WHITE, 0.4)


@niche("digital-agency", "Digital / creative agency", subjects=("digedu_monitor_design", "digedu_moodboard"),
       strong=("digital agency", "marketing agency", "branding", "seo", "social media", "creative agency", "advertising agency",
               "digital marketing", "डिजिटल मार्केटिंग", "डिजिटल एजेंसी", "branding agency", "seo company", "social media marketing", "ब्रांडिंग"),
       weak=("marketing", "design studio", "graphic design", "ads", "campaign", "content", "creative"),
       accent="#e84393", mood="dark", group="digital")
def digital_agency(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.glow(0.55, 0.30, 0.9, P.accent, 0.38 if dark else 0.22)
        S.glow(1.9, 0.25, 0.9, mix(P.accent, (0.3, 0.4, 1.0), 0.6), 0.30 if dark else 0.16)
        # neon strip and blurred frames on the wall
        S.glow(0.80, 0.55, 0.5, (1.0, 0.85, 0.55), 0.30 if dark else 0.10)
        S.rect(1.0, 0.07, 3.0, 0.012, mix(P.accent, WHITE, 0.4), lift=0.0)
        S.glow(1.0, 0.07, 1.2, P.accent, 0.20)
        for (u, v, w, h, col) in ((0.15, 0.30, 0.20, 0.26, P.accent2), (0.40, 0.25, 0.14, 0.17, (0.3, 0.75, 0.9)), (1.95, 0.28, 0.2, 0.24, (1.0, 0.75, 0.3))):
            S.rect(u, v, w, h, mix(col, P.wall_bot, 0.35 if dark else 0.0), lift=0.0, alpha=0.85)
        S.bokeh(10, 0.0, 0.05, 2.0, 0.55, [P.accent_light, mix(P.accent2, WHITE, 0.4), (0.5, 0.7, 1.0)], 0.012, 0.045, 0.30)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.soft(1.1, 0.66, 1.0, 0.16, P.accent_light, 0.18 if dark else 0.14, 1.5, add=True)
    S.wood(-1.6, 0.60, 4.0, 1.8, scale(P.surface, 0.85) if not dark else P.surface, plank=0.14, grain=0.25)
    S.rect(1.0, 0.60, 7.0, 0.008, scale(P.surface, 0.4), lift=0.0)
    S.put("digedu_moodboard", 0.92, 0.62, 0.40, color=mix(P.wall_bot, P.ink, 0.3) if dark else (0.78, 0.62, 0.46), subject=True, shadow=False)
    S.put("digedu_lamp", 0.62, 0.88, 0.42, color=(0.72, 0.73, 0.80) if dark else (0.92, 0.93, 0.96), shadow_alpha=0.3)
    S.put("digedu_monitor_design", 1.26, 0.80, 0.47, color=P.accent, subject=True, shadow_alpha=0.34)
    S.put("digedu_tablet", 0.98, 0.96, 0.12, color=P.accent, shadow_alpha=0.32)
    S.put("digedu_swatches", 1.36, 0.98, 0.15, color=P.accent, shadow_alpha=0.30)
    S.put("digedu_sticky", 0.80, 0.84, 0.07, color=(1.0, 0.85, 0.3), shadow_alpha=0.25)
    S.put("digedu_mug", 1.52, 0.98, 0.09, color=P.accent_light if not dark else (0.2, 0.2, 0.26))
    S.soft(0.95, 0.92, 0.5, 0.10, (1.0, 0.85, 0.55), 0.22 if dark else 0.10, 1.4, add=True)
    S.focus("detail", 1.24, 0.57)
    with S.near():
        S.circle(0.55, 0.97, 0.05, P.accent, alpha=0.35, lift=0)
        S.circle(1.64, 0.36, 0.035, mix(P.accent_light, WHITE, 0.3), alpha=0.4, lift=0)


# ====================================================================================================== ACCOUNTING / FINANCE
GOLD = (0.95, 0.76, 0.26)
PAPER = (0.97, 0.965, 0.945)


class _Flat:
    """A flat surface lying on the desk, seen from above at an angle: (a, b) in 0..1 maps onto a parallelogram."""

    def __init__(self, c, ox, oy, ex, ey, fx, fy):
        self.c, self.o, self.e, self.f = c, (ox, oy), (ex, ey), (fx, fy)

    def p(self, a, b):
        return (self.o[0] + a * self.e[0] + b * self.f[0], self.o[1] + a * self.e[1] + b * self.f[1])

    def quad(self, a0, b0, a1, b1, col, lift=0.0, alpha=1.0):
        self.c.poly([self.p(a0, b0), self.p(a1, b0), self.p(a1, b1), self.p(a0, b1)], col, lift=lift, alpha=alpha)

    def line(self, a0, b0, a1, b1, w, col, alpha=1.0):
        p, q = self.p(a0, b0), self.p(a1, b1)
        self.c.line(p[0], p[1], q[0], q[1], w, col, alpha)

    def tint(self, a0, b0, a1, b1, col, alpha):
        c = self.c
        pts = [self.p(a0, b0), self.p(a1, b0), self.p(a1, b1), self.p(a0, b1)]
        _fill_quad(c.cv, sorted_quad([(c.X(x), c.Y(y)) for x, y in pts]), col, alpha)

    def bar(self, a, b, wa, wb, col, alpha=1.0):
        c = self.c
        pts = [self.p(a, b - wb / 2), self.p(a + wa, b - wb / 2), self.p(a + wa, b + wb / 2), self.p(a, b + wb / 2)]
        _fill_quad(c.cv, sorted_quad([(c.X(x), c.Y(y)) for x, y in pts]), col, alpha)


def _seg_digit(c, u, v, w, h, digit, on, off):
    t = h * 0.14
    segs = {"a": (0, 1, 1, t), "b": (1, 0.5, t, 1), "c": (1, -0.5, t, 1), "d": (0, -1, 1, t), "e": (-1, -0.5, t, 1), "f": (-1, 0.5, t, 1), "g": (0, 0, 1, t)}
    lit = {0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg", 5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg"}[digit]
    for k, (sx, sy, sw, sh) in segs.items():
        ww = w * 0.9 * sw if sw == 1 else t
        hh = t if sw == 1 else h * 0.46
        _crect(c, u + sx * w * 0.45, v + sy * h * 0.46, ww, hh, on if k in lit else off, lift=0.0)


@sprop("digedu_calculator", aspect=0.78, fill=1.0)
def calculator(c, color):
    rng = c.rng
    acc = color or (0.12, 0.52, 0.28)
    body = (0.17, 0.18, 0.20)
    ao(c, 0.04, 0.0, 0.85, 0.2)
    # thick right side and the leaning, slightly tapering front
    c.poly([(0.36, 0.01), (0.44, 0.06), (0.40, 0.94), (0.33, 0.99)], scale(body, 0.55))
    c.poly([(-0.38, 0.0), (0.38, 0.0), (0.33, 1.0), (-0.33, 1.0)], body, lift=0.12)
    c.line(-0.38, 0.0, -0.33, 1.0, 0.012, mix(body, WHITE, 0.4), 0.7)
    c.line(-0.33, 1.0, 0.33, 1.0, 0.010, mix(body, WHITE, 0.45), 0.7)
    # display
    _crect(c, 0.0, 0.86, 0.60, 0.15, (0.52, 0.62, 0.50), r=0.015, lift=0.0)
    _crect(c, 0.0, 0.86, 0.58, 0.13, (0.66, 0.76, 0.62), r=0.012, lift=0.0)
    for i, d in enumerate((1, 2, 4, 8, 0)):
        _seg_digit(c, -0.225 + i * 0.112, 0.86, 0.072, 0.10, d, (0.12, 0.20, 0.12), (0.62, 0.72, 0.58))
    # keys
    for r in range(5):
        v = 0.70 - r * 0.135
        t = 1.0 - (0.70 - v) * 0.07
        for k in range(4):
            u = (-0.225 + k * 0.15) * t
            last = k == 3
            col = acc if last else ((0.30, 0.31, 0.34) if k < 3 else body)
            if r == 4 and k == 3:
                col = (0.9, 0.55, 0.2)
            _crect(c, u + 0.01, v - 0.005, 0.125 * t, 0.095, scale(col, 0.55), r=0.02, lift=0.0)
            _crect(c, u, v, 0.125 * t, 0.095, col, r=0.02, lift=0.20)
            c.line(u - 0.04, v + 0.035, u + 0.04, v + 0.035, 0.008, WHITE, 0.22)
    soft_disc(c, -0.15, 0.7, 0.2, 0.5, WHITE, 0.10, 1.2, add=True)


@sprop("digedu_ledger", aspect=3.9, fill=0.5)
def ledger(c, color):
    rng = c.rng
    cover = color or (0.12, 0.40, 0.25)
    ao(c, 0.0, 0.0, 1.9, 0.5)
    # cover, page block, pages
    c.poly([(-0.92, 0.0), (0.92, 0.0), (0.98, 0.06), (-0.98, 0.06)], scale(cover, 0.6), lift=0.0)
    c.poly([(-0.98, 0.06), (0.98, 0.06), (0.86, 0.46), (-0.86, 0.46)], cover, lift=0.10)
    for i in range(5):
        y = 0.075 + i * 0.012
        c.line(-0.90 + i * 0.01, y, 0.90 - i * 0.01, y, 0.006, (0.88, 0.86, 0.80), 0.9)
    L = _Flat(c, -0.90, 0.13, 0.88, 0.0, 0.04, 0.30)
    R = _Flat(c, 0.02, 0.13, 0.88, 0.0, -0.04, 0.30)
    for F, sgn in ((L, 1), (R, -1)):
        F.quad(0.0, 0.0, 1.0, 1.0, PAPER, 0.0)
        F.tint(0.0, 0.0, 1.0, 0.07, scale(PAPER, 0.94), 0.6)
        for k in range(11):
            F.line(0.02, 0.12 + k * 0.075, 0.98, 0.12 + k * 0.075, 0.005, (0.62, 0.74, 0.86), 0.7)
        for a in (0.52, 0.72, 0.87):
            F.line(a, 0.04, a, 0.97, 0.005, (0.82, 0.45, 0.45), 0.55)
        F.line(0.17, 0.04, 0.17, 0.97, 0.005, (0.82, 0.45, 0.45), 0.55)
        for k in range(8):                                         # handwritten figures
            b = 0.17 + k * 0.095
            F.bar(0.06, b, rng.uniform(0.07, 0.10), 0.028, (0.2, 0.25, 0.45), 0.8)
            F.bar(0.22, b, rng.uniform(0.15, 0.28), 0.028, (0.2, 0.25, 0.45), 0.7)
            for a in (0.56, 0.76, 0.90):
                if rng.random() < 0.85:
                    F.bar(a, b, rng.uniform(0.05, 0.09), 0.028, (0.18, 0.22, 0.4), 0.8)
    soft_disc(c, 0.0, 0.30, 0.07, 0.15, BLACK, 0.34, 1.3)           # gutter
    soft_disc(c, -0.4, 0.28, 0.5, 0.08, WHITE, 0.14, 1.3, add=True)
    # a pen resting across the right page
    c.line(0.12, 0.17, 0.82, 0.40, 0.030, (0.08, 0.1, 0.18), 1.0)
    c.line(0.12, 0.17, 0.30, 0.23, 0.031, GOLD, 1.0)
    c.line(0.70, 0.36, 0.86, 0.42, 0.012, (0.8, 0.8, 0.85), 1.0)
    c.line(0.14, 0.19, 0.78, 0.40, 0.006, WHITE, 0.4)


@sprop("digedu_coins", aspect=1.85, fill=0.65)
def coins(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.15, 0.30)

    def stack(u, n, r):
        th = 0.045
        base = 0.0
        top_v = base + th * n
        c.ellipse(u, base + 0.006, r, r * TILT, scale(GOLD, 0.55), lift=0)
        craft.hshade_box(c, u, base + (th * n) / 2 + 0.005, 2 * r, th * n, mix(GOLD, WHITE, 0.25), scale(GOLD, 0.52))
        for k in range(n):
            y = base + 0.005 + k * th
            c.line(u - r, y + th, u + r, y + th, 0.004, scale(GOLD, 0.55), 0.6)
            c.ellipse(u, y + th, r, r * TILT * 0.5, scale(GOLD, 0.72), lift=0.0, alpha=0.45)
        c.ellipse(u, top_v + 0.006, r, r * TILT, scale(GOLD, 0.7), lift=0)
        c.ellipse(u, top_v + 0.011, r * 0.97, r * TILT * 0.96, mix(GOLD, WHITE, 0.15), lift=0.15)
        c.ellipse(u, top_v + 0.012, r * 0.72, r * TILT * 0.70, scale(GOLD, 0.88), lift=0.0)
        c.ellipse(u, top_v + 0.013, r * 0.64, r * TILT * 0.62, mix(GOLD, WHITE, 0.18), lift=0.12)
        gloss(c, u - r * 0.35, top_v + 0.03, r * 0.35, r * 0.1, 8, 0.5)
        gloss(c, u - r * 0.62, base + (th * n) * 0.5, r * 0.08, th * n * 0.45, 0, 0.4)
    stack(0.40, 12, 0.19)
    stack(-0.05, 7, 0.20)
    stack(-0.46, 4, 0.19)
    # loose coins
    for (u, v, a) in ((0.22, -0.01, 0), (0.62, 0.0, 0)):
        c.ellipse(u, v + 0.02, 0.15, 0.15 * TILT, scale(GOLD, 0.6), lift=0)
        c.ellipse(u, v + 0.03, 0.15, 0.15 * TILT, mix(GOLD, WHITE, 0.1), lift=0.15)
        c.ellipse(u, v + 0.03, 0.11, 0.11 * TILT, scale(GOLD, 0.9), lift=0.0)
        gloss(c, u - 0.05, v + 0.045, 0.05, 0.015, 8, 0.5)


@sprop("digedu_barblocks", aspect=1.3, fill=1.1)
def barblocks(c, color):
    rng = c.rng
    g1 = color or (0.12, 0.52, 0.28)
    ao(c, 0.0, 0.0, 1.35, 0.34)
    items = ((-0.45, 0.28, mix(g1, WHITE, 0.45)), (-0.12, 0.46, mix(g1, WHITE, 0.2)), (0.21, 0.66, g1), (0.54, 0.88, scale(g1, 0.8)))
    for u, h, col in items:
        box3d(c, u, 0.0, 0.26, h, 0.26, col, mix(col, WHITE, 0.3), scale(col, 0.58), lift=0.16)
        soft_disc(c, u - 0.08, h * 0.55, 0.05, h * 0.5, WHITE, 0.16, 1.2, add=True)
    # rising arrow over the bars
    arrow = (0.95, 0.76, 0.26)
    c.path([(-0.55, 0.40), (-0.18, 0.60), (0.12, 0.76), (0.50, 1.02)], 0.045, scale(arrow, 0.7), 1.0)
    c.path([(-0.55, 0.42), (-0.18, 0.62), (0.12, 0.78), (0.50, 1.04)], 0.035, arrow, 1.0)
    c.poly([(0.46, 1.12), (0.68, 1.06), (0.58, 0.90)], arrow, lift=0.1)
    gloss(c, -0.1, 0.62, 0.2, 0.012, 28, 0.5)


@sprop("digedu_forms", aspect=1.67, fill=0.72)
def tax_forms(c, color):
    rng = c.rng
    acc = color or (0.12, 0.52, 0.28)
    ao(c, 0.0, 0.0, 1.3, 0.5)
    for k, (dx, dy, tilt) in enumerate(((0.0, 0.0, 0.0), (0.04, 0.03, 0.05), (-0.05, 0.06, -0.06))):
        F = _Flat(c, -0.50 + dx, 0.0 + dy, 1.0, tilt, 0.12, 0.62)
        F.quad(0.0, 0.0, 1.0, 1.0, scale(PAPER, 0.96 - 0.02 * (2 - k)), 0.0)
    top = F
    top.quad(0.0, 0.0, 1.0, 1.0, PAPER, 0.0)
    top.quad(0.06, 0.82, 0.60, 0.92, acc, 0.0, 0.9)
    top.bar(0.06, 0.70, 0.40, 0.04, (0.35, 0.37, 0.45), 0.8)
    for k in range(7):
        top.line(0.06, 0.58 - k * 0.075, 0.94, 0.58 - k * 0.075, 0.005, (0.7, 0.72, 0.8), 0.8)
        for j in range(3):
            if rng.random() < 0.7:
                top.bar(0.10 + j * 0.28, 0.585 - k * 0.075, rng.uniform(0.08, 0.2), 0.03, (0.25, 0.3, 0.5), 0.6)
    for j in range(3):
        top.quad(0.72 + j * 0.08, 0.10, 0.76 + j * 0.08, 0.24, (0.95, 0.95, 0.95), 0.0)
    # green approval stamp
    p = top.p(0.76, 0.40)
    c.ellipse(p[0], p[1], 0.14, 0.07, scale(acc, 0.8), lift=0, alpha=0.65, angle=8)
    c.ellipse(p[0], p[1], 0.11, 0.052, PAPER, lift=0, alpha=0.9, angle=8)
    c.ellipse(p[0], p[1], 0.095, 0.042, acc, lift=0, alpha=0.55, angle=8)
    # paper clip
    q = top.p(0.12, 0.98)
    c.arc(q[0], q[1], 0.03, 0, 180, 0.008, (0.75, 0.77, 0.8), ry=0.06)
    c.arc(q[0] + 0.008, q[1] - 0.01, 0.02, 0, 180, 0.008, (0.75, 0.77, 0.8), ry=0.05)


@niche("accounting-finance", "Accounting / tax / finance firm", subjects=("digedu_calculator", "digedu_ledger"),
       strong=("accounting", "accountant", "tax consultant", "bookkeeping", "ca firm", "chartered accountant", "gst", "tax filing",
               "लेखा", "कर सलाहकार", "सीए", "लेखाकार", "income tax", "audit", "gst filing", "tax advisor", "financial advisor"),
       weak=("finance", "tax", "payroll", "invoice", "accounts", "balance sheet", "itr", "financial planning", "financial documents", "spreadsheet", "finance office", "ledger", "financial reports", "वित्त"),
       accent="#1e8449", mood="light", group="professional")
def accounting_finance(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        S.glow(0.4, 0.28, 0.9, P.accent_light, 0.20)
        S.rect(1.2, 0.46, 3.4, 0.2, scale(P.wall_bot, 0.95), lift=0.0)                            # wainscot
        if dark:
            S.window(0.35, 0.26, 0.28, 0.34, (0.10, 0.14, 0.26), (0.22, 0.26, 0.40), (0.35, 0.36, 0.42))
        else:
            S.window(0.35, 0.26, 0.28, 0.34)
        # shelves of binders
        S.rect(1.55, 0.30, 1.0, 0.014, mix(P.wall_bot, P.ink, 0.4), lift=0.0)
        u = 1.06
        while u < 2.05:
            w, hh = rng.uniform(0.03, 0.05), rng.uniform(0.11, 0.16)
            S.rect(u + w / 2, 0.30 - 0.007 - hh / 2, w, hh, mix(rng.choice([P.accent, P.accent_dark, (0.18, 0.28, 0.5), (0.9, 0.9, 0.9)]), P.wall_bot, 0.15 if not dark else 0.5), lift=0.0)
            u += w + 0.003
        S.rect(1.55, 0.12, 1.0, 0.014, mix(P.wall_bot, P.ink, 0.4), lift=0.0)
        u = 1.06
        while u < 2.05:
            w, hh = rng.uniform(0.03, 0.05), rng.uniform(0.07, 0.10)
            S.rect(u + w / 2, 0.12 - 0.007 - hh / 2, w, hh, mix(rng.choice([(0.8, 0.7, 0.5), P.accent_light, (0.3, 0.4, 0.6)]), P.wall_bot, 0.2 if not dark else 0.5), lift=0.0)
            u += w + 0.003
        S.pendant(0.9, -0.1, 0.16, (1.0, 0.92, 0.72), 0.09)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.soft(1.1, 0.68, 0.7, 0.12, (1.0, 0.95, 0.8), 0.24, 1.5, add=True)
    S.wood(-1.6, 0.58, 4.0, 1.8, P.surface, plank=0.13, grain=0.25)
    S.rect(1.0, 0.58, 7.0, 0.008, scale(P.surface, 0.5), lift=0.0)
    mat = mix(P.accent_dark, P.ink, 0.35)
    S.soft(1.07, 0.97, 0.62, 0.14, BLACK_, 0.18, 1.6)
    _srect(S, 1.07, 0.915, 1.0, 0.17, mat, 0.015, 0.06)
    _srect(S, 1.07, 0.915, 0.97, 0.15, scale(mat, 1.08), 0.012, 0.0, 0.6)
    S.put("digedu_plant", 0.60, 0.77, 0.19, color=(0.88, 0.86, 0.80))
    S.put("digedu_barblocks", 1.12, 0.78, 0.40, color=P.accent)
    S.put("digedu_calculator", 0.78, 0.90, 0.30, color=P.accent, subject=True, shadow_alpha=0.30)
    S.put("digedu_coins", 1.48, 0.91, 0.20, shadow_alpha=0.30)
    S.put("digedu_ledger", 1.14, 0.995, 0.145, color=mix(P.accent_dark, P.accent, 0.5), subject=True, shadow_alpha=0.34)
    S.put("digedu_forms", 0.70, 1.0, 0.13, color=P.accent, shadow_alpha=0.28)
    S.focus("detail", 0.95, 0.88)
    with S.near():
        S.circle(0.52, 0.98, 0.04, P.accent_light, alpha=0.4, lift=0)
        S.circle(1.64, 0.40, 0.05, P.accent, alpha=0.22, lift=0)


BLACK_ = (0.0, 0.0, 0.0)


# ====================================================================================================== LAW FIRM / BOOKS
BRASS = (0.80, 0.57, 0.21)
LEATHERS = ((0.45, 0.10, 0.12), (0.12, 0.20, 0.40), (0.14, 0.30, 0.20), (0.50, 0.30, 0.14), (0.16, 0.12, 0.12), (0.35, 0.12, 0.22))


def _brass_cyl(c, u, v, w, h):
    craft.hshade_box(c, u, v + h / 2, w, h, mix(BRASS, WHITE, 0.22), scale(BRASS, 0.42))
    c.line(u - w * 0.22, v + h * 0.05, u - w * 0.22, v + h * 0.95, w * 0.08, WHITE, 0.30)


@sprop("digedu_scales", aspect=1.34, fill=1.0)
def scales(c, color):
    br = color or BRASS
    ao(c, 0.0, 0.0, 0.75, 0.22)
    # stepped base
    c.ellipse(0.0, 0.02, 0.32, 0.32 * TILT, scale(br, 0.45), lift=0)
    craft.hshade_box(c, 0.0, 0.05, 0.62, 0.07, mix(br, WHITE, 0.2), scale(br, 0.45))
    disc(c, 0.0, 0.085, 0.31, mix(br, WHITE, 0.12), TILT, 0.15)
    craft.hshade_box(c, 0.0, 0.12, 0.46, 0.06, mix(br, WHITE, 0.25), scale(br, 0.5))
    disc(c, 0.0, 0.15, 0.23, mix(br, WHITE, 0.2), TILT, 0.15)
    # pillar with rings
    _brass_cyl(c, 0.0, 0.15, 0.075, 0.60)
    for v in (0.22, 0.45, 0.62):
        c.ellipse(0.0, v, 0.062, 0.020, mix(br, WHITE, 0.3), lift=0.2)
        c.ellipse(0.0, v - 0.012, 0.062, 0.018, scale(br, 0.5), lift=0)
    c.circle(0.0, 0.77, 0.055, br, lift=0.25)
    gloss(c, -0.02, 0.79, 0.03, 0.02, 0, 0.9)
    # beam, tipped slightly so the left pan hangs lower
    lu, lv, ru, rv = -0.66, 0.74, 0.66, 0.79
    c.line(lu, lv, ru, rv, 0.036, scale(br, 0.6))
    c.line(lu, lv + 0.006, ru, rv + 0.006, 0.024, mix(br, WHITE, 0.3))
    c.line(lu, lv + 0.012, ru, rv + 0.012, 0.008, WHITE, 0.5)
    for (u, v) in ((lu, lv), (ru, rv)):
        c.circle(u, v, 0.032, br, lift=0.25)
        c.circle(u, v + 0.036, 0.016, mix(br, WHITE, 0.3), lift=0.2)
    # pans on chains
    for (u, v, drop) in ((lu, lv, 0.36), (ru, rv, 0.47)):
        pv = v - drop
        for du in (-0.19, 0.0, 0.19):
            c.line(u, v - 0.01, u + du, pv + 0.01, 0.007, scale(br, 0.8), 0.9)
        c.ellipse(u, pv - 0.035, 0.20, 0.20 * TILT, scale(br, 0.45), lift=0)
        c.ellipse(u, pv - 0.02, 0.21, 0.21 * TILT, br, lift=0.15)
        c.ellipse(u, pv - 0.005, 0.21, 0.21 * TILT, mix(br, WHITE, 0.3), lift=0.1)
        c.ellipse(u, pv - 0.012, 0.185, 0.185 * TILT * 0.9, scale(br, 0.62), lift=0.1)
        gloss(c, u - 0.07, pv + 0.0, 0.06, 0.012, 4, 0.8)
    c.glow(0.0, 0.5, 0.5, (1.0, 0.8, 0.45), 0.10)


@sprop("digedu_gavel", aspect=1.6, fill=0.45)
def gavel(c, color):
    wood = color or (0.40, 0.22, 0.12)
    ao(c, 0.1, 0.0, 1.6, 0.3)
    # sound block
    c.ellipse(-0.40, 0.012, 0.30, 0.30 * TILT, scale(wood, 0.5), lift=0)
    craft.hshade_box(c, -0.40, 0.06, 0.58, 0.10, mix(wood, WHITE, 0.14), scale(wood, 0.45))
    disc(c, -0.40, 0.11, 0.29, mix(wood, WHITE, 0.08), TILT, 0.12)
    c.ellipse(-0.40, 0.108, 0.20, 0.20 * TILT, scale(wood, 1.12), lift=0.0, alpha=0.7)
    for k in range(3):
        craft.arc(c, -0.40, 0.112, 0.25 - k * 0.06, (0.25 - k * 0.06) * TILT, 20, 200, 0.004, scale(wood, 0.7), 0.5)
    # gavel lying on the desk: head and handle along a slightly tilted axis
    g = _G(c, 0.18, 0.14, 8)
    g.rect(0.46, 0.0, 0.70, 0.075, mix(wood, WHITE, 0.08), r=0.03, lift=0.35)
    g.circle(0.82, 0.0, 0.052, scale(wood, 0.6), lift=0.1)
    g.rect(-0.12, 0.0, 0.40, 0.19, mix(wood, WHITE, 0.10), r=0.04, lift=0.35)
    g.rect(-0.12, 0.06, 0.40, 0.03, WHITE, r=0.012, alpha=0.20)
    g.rect(-0.30, 0.0, 0.035, 0.20, scale(wood, 0.5), r=0.012, lift=0.2)
    for uu in (-0.25, 0.0):
        g.rect(uu, 0.0, 0.035, 0.20, BRASS, r=0.01, lift=0.35)
    g.rect(-0.325, 0.0, 0.02, 0.17, scale(wood, 0.55))
    ex, ey = g.pt(0.08, 0.0)
    c.ellipse(ex + 0.025, ey, 0.032, 0.095, scale(wood, 0.45), lift=0.0, alpha=0.9)
    gloss(c, 0.0, 0.205, 0.17, 0.018, 7, 0.6)


def _bookstack(c, cols, w=0.9, h=0.15, d=0.55, n=4, seed_shift=0.0):
    rng = c.rng
    ao(c, 0.0, 0.0, w * 1.2, 0.34)
    v = 0.0
    for i in range(n):
        ww = w * rng.uniform(0.86, 1.0)
        hh = h * rng.uniform(0.82, 1.1)
        u = rng.uniform(-0.05, 0.05)
        col = cols[(i + int(seed_shift)) % len(cols)]
        # right end: cover edges and the page block
        ox, oy = d * 0.55, d * 0.42
        x1 = u + ww / 2
        c.poly([(x1, v), (x1 + ox, v + oy), (x1 + ox, v + hh + oy), (x1, v + hh)], scale(col, 0.62))
        c.poly([(x1 + 0.004, v + hh * 0.18), (x1 + ox - 0.004, v + oy + hh * 0.18), (x1 + ox - 0.004, v + oy + hh * 0.82), (x1 + 0.004, v + hh * 0.82)], (0.93, 0.89, 0.78))
        c.poly([(u - ww / 2, v + hh), (x1, v + hh), (x1 + ox, v + hh + oy), (u - ww / 2 + ox, v + hh + oy)], mix(col, WHITE, 0.18))
        _crect(c, u, v + hh / 2, ww, hh, col, lift=0.18)
        c.line(u - ww / 2, v + hh, x1, v + hh, 0.004, mix(col, WHITE, 0.55), 0.6)
        for bu in (-0.30, 0.30):                                                # gold spine bands
            _crect(c, u + bu * ww, v + hh / 2, 0.014, hh * 0.96, BRASS, lift=0.1, alpha=0.9)
        _crect(c, u, v + hh / 2, ww * 0.30, hh * 0.46, mix(col, BRASS, 0.7), r=0.008, lift=0.1, alpha=0.95)
        for _ in range(4):                                                      # leather scuffs
            x, y = rng.uniform(u - ww / 2, x1), rng.uniform(v, v + hh)
            c.line(x, y, x + rng.uniform(0.03, 0.09), y + rng.uniform(-0.01, 0.01), 0.004, scale(col, rng.uniform(0.7, 1.4)), 0.3)
        soft_disc(c, u - ww * 0.25, v + hh * 0.7, ww * 0.3, hh * 0.3, WHITE, 0.14, 1.2, add=True)
        v += hh + 0.002


@sprop("digedu_books_leather", aspect=1.45, fill=0.8)
def books_leather(c, color):
    _bookstack(c, LEATHERS, 0.9, 0.17, 0.55, 4)


@sprop("digedu_books_row", aspect=1.1, fill=1.0)
def books_row(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.16)
    u = -0.5
    for i in range(7):
        w = rng.uniform(0.09, 0.15)
        h = rng.uniform(0.72, 1.0)
        col = LEATHERS[i % len(LEATHERS)]
        if i == 5:
            continue
        _crect(c, u + w / 2, h / 2, w, h, col, lift=0.18)
        _crect(c, u + w * 0.15, h / 2, 0.012, h, mix(col, WHITE, 0.3), lift=0, alpha=0.5)
        _crect(c, u + w / 2, h * 0.86, w, 0.018, BRASS, lift=0.1, alpha=0.9)
        _crect(c, u + w / 2, h * 0.70, w, 0.012, BRASS, lift=0.1, alpha=0.8)
        _crect(c, u + w / 2, h * 0.26, w, 0.018, BRASS, lift=0.1, alpha=0.9)
        _crect(c, u + w / 2, h * 0.48, w * 0.7, h * 0.14, mix(col, BRASS, 0.7), r=0.006, lift=0.1)
        c.line(u + w, 0.0, u + w, h, 0.004, scale(col, 0.45), 0.8)
        u += w + 0.004
    # a leaning book at the end
    g = _G(c, u + 0.20, 0.0, -14)
    g.rect(0.0, 0.43, 0.14, 0.86, LEATHERS[3], lift=0.18, r=0.005)
    g.rect(0.0, 0.70, 0.14, 0.016, BRASS, lift=0.1)
    g.rect(0.0, 0.25, 0.14, 0.016, BRASS, lift=0.1)


@sprop("digedu_banker_lamp", aspect=0.95, fill=1.0)
def banker_lamp(c, color):
    glass = color or (0.12, 0.45, 0.26)
    ao(c, 0.0, 0.0, 0.7, 0.2)
    c.ellipse(0.0, 0.02, 0.30, 0.30 * TILT, scale(BRASS, 0.45), lift=0)
    disc(c, 0.0, 0.05, 0.28, mix(BRASS, WHITE, 0.1), TILT, 0.15)
    _brass_cyl(c, 0.0, 0.07, 0.07, 0.52)
    c.ellipse(0.0, 0.30, 0.055, 0.02, mix(BRASS, WHITE, 0.4), lift=0.2)
    # shade: a half cylinder seen from the side, glowing along its lower edge
    c.glow(0.0, 0.40, 0.55, (1.0, 0.78, 0.42), 0.55)
    craft.hshade_box(c, 0.0, 0.66, 0.92, 0.22, mix(glass, WHITE, 0.25), scale(glass, 0.35), r=0.10)
    _crect(c, 0.0, 0.575, 0.88, 0.05, (1.0, 0.86, 0.5), r=0.02, lift=0.0, alpha=0.9)
    _crect(c, 0.0, 0.74, 0.88, 0.04, mix(glass, WHITE, 0.45), r=0.02, lift=0.0, alpha=0.5)
    c.line(-0.38, 0.69, 0.36, 0.69, 0.012, mix(glass, WHITE, 0.6), 0.5)
    c.circle(-0.46, 0.66, 0.03, BRASS, lift=0.25)
    c.circle(0.46, 0.66, 0.03, BRASS, lift=0.25)
    gloss(c, -0.2, 0.74, 0.18, 0.025, 0, 0.6)
    c.line(0.28, 0.5, 0.28, 0.28, 0.01, scale(BRASS, 0.7), 0.9)                                          # pull chain
    c.circle(0.28, 0.27, 0.014, BRASS)


@niche("law-firm", "Law firm / lawyer", subjects=("digedu_scales",),
       strong=("lawyer", "law firm", "advocate", "attorney", "legal", "court", "legal services", "वकील", "कानून", "अधिवक्ता",
               "vakil", "advocate office", "legal advisor", "कानूनी", "law office", "solicitor", "barrister", "लॉ फर्म"),
       weak=("justice", "litigation", "notary", "legal advice", "case", "judge", "contract"),
       accent="#7b4b2a", mood="dark", group="professional")
def law_firm(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.glow(0.8, 0.30, 0.9, (1.0, 0.72, 0.4), 0.30 if dark else 0.14)
        # wood panelling and a bookcase full of leather spines
        for k in range(10):
            S.rect(-0.2 + k * 0.28, 0.30, 0.012, 0.62, scale(P.wall_bot, 0.7), lift=0.0, alpha=0.7)
        S.rect(1.0, 0.04, 3.2, 0.03, mix(P.wall_top, BRASS, 0.2), lift=0.0)
        for (v, hmax) in ((0.18, 0.15), (0.38, 0.16)):
            S.rect(1.55, v + 0.012, 1.2, 0.016, mix(P.wall_bot, P.ink, 0.3), lift=0.0)
            u = 0.95
            while u < 2.15:
                w, hh = rng.uniform(0.03, 0.055), rng.uniform(0.09, hmax)
                col = LEATHERS[rng.randrange(len(LEATHERS))]
                S.rect(u + w / 2, v - hh / 2, w, hh, scale(col, 0.62 if dark else 0.95), lift=0.0)
                S.rect(u + w / 2, v - hh * 0.8, w, 0.008, scale(BRASS, 0.6 if dark else 1.0), lift=0.0, alpha=0.8)
                u += w + 0.003
        S.pendant(0.55, -0.1, 0.19, (1.0, 0.82, 0.5), 0.10)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.50, [(1.0, 0.82, 0.5), (1.0, 0.7, 0.4)], 0.01, 0.04, 0.30)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.soft(1.1, 0.70, 1.0, 0.15, (1.0, 0.82, 0.5), 0.22 if dark else 0.16, 1.5, add=True)
    S.wood(-1.6, 0.60, 4.0, 1.8, scale(P.surface, 0.78) if dark else P.surface, plank=0.2, grain=0.3)
    S.rect(1.0, 0.60, 7.0, 0.01, scale(P.surface, 0.35), lift=0.0)
    leather = mix(scale(P.accent_dark, 0.6), P.ink, 0.5)
    S.soft(1.07, 0.98, 0.60, 0.14, BLACK_, 0.20, 1.6)
    _srect(S, 1.07, 0.90, 0.98, 0.19, leather, 0.014, 0.08)
    _srect(S, 1.07, 0.90, 0.93, 0.15, scale(leather, 1.10), 0.010, 0.0, 0.7)
    for dv in (-0.083, 0.083):
        S.line(0.60, 0.90 + dv, 1.54, 0.90 + dv, 0.003, scale(BRASS, 0.8), 0.7)
    S.put("digedu_banker_lamp", 1.52, 0.80, 0.30, shadow_alpha=0.34)
    S.put("digedu_books_leather", 0.66, 0.97, 0.17, shadow_alpha=0.34)
    S.put("digedu_scales", 1.06, 0.88, 0.52, subject=True, shadow_alpha=0.34)
    S.put("digedu_gavel", 1.28, 1.0, 0.16, shadow_alpha=0.34)
    S.focus("detail", 1.0, 0.60)
    with S.near():
        S.circle(0.52, 0.98, 0.04, (1.0, 0.75, 0.4), alpha=0.35, lift=0)
        S.circle(1.64, 0.38, 0.05, (1.0, 0.7, 0.35), alpha=0.25, lift=0)


# ====================================================================================================== SCHOOL
CHALK = (0.95, 0.96, 0.93)


@sprop("digedu_board", aspect=2.04, fill=0.98)
def blackboard(c, color):
    rng = c.rng
    col = color or (0.15, 0.33, 0.27)
    wood = (0.70, 0.52, 0.32)
    _crect(c, 0.02, 0.535, 2.04, 0.88, (0.0, 0.0, 0.0), r=0.02, alpha=0.18)
    _crect(c, 0.0, 0.55, 2.04, 0.88, wood, r=0.02, lift=0.18)
    _crect(c, 0.0, 0.55, 1.94, 0.78, scale(col, 0.62), r=0.012, lift=0.0)
    _crect(c, 0.0, 0.555, 1.90, 0.745, col, r=0.01, lift=0.10)
    # eraser smudges and chalk dust
    for (u, v, a, b, ang) in ((-0.55, 0.62, 0.45, 0.14, 8), (0.30, 0.38, 0.55, 0.12, -6), (0.7, 0.75, 0.3, 0.1, 10), (-0.1, 0.5, 0.7, 0.2, 3)):
        soft_disc(c, u, v, a, b, WHITE, 0.07, 1.2, ang)
    W = lambda a: a                                                          # noqa: E731
    ch = 0.013
    # sun with rays, house
    for k in range(9):
        a = math.radians(k * 40)
        c.line(-0.72 + math.cos(a) * 0.13, 0.82 + math.sin(a) * 0.13, -0.72 + math.cos(a) * 0.20, 0.82 + math.sin(a) * 0.20, ch, (1.0, 0.9, 0.5), 0.85)
    craft.arc(c, -0.72, 0.82, 0.095, 0.095, 0, 360, ch, (1.0, 0.9, 0.5), 0.9, 18)
    for (a, b, c_, d) in ((-0.88, 0.30, -0.88, 0.50), (-0.88, 0.50, -0.58, 0.50), (-0.58, 0.50, -0.58, 0.30), (-0.58, 0.30, -0.88, 0.30),
                          (-0.92, 0.50, -0.73, 0.64), (-0.73, 0.64, -0.54, 0.50), (-0.78, 0.30, -0.78, 0.40), (-0.78, 0.40, -0.70, 0.40), (-0.70, 0.40, -0.70, 0.30)):
        c.line(a, b, c_, d, ch, CHALK, 0.85)
    # right triangle with squares, arrows
    for (a, b, c_, d) in ((-0.25, 0.30, 0.15, 0.30), (0.15, 0.30, 0.15, 0.62), (0.15, 0.62, -0.25, 0.30), (-0.25, 0.30, -0.25, 0.20), (-0.25, 0.20, 0.15, 0.20),
                          (0.15, 0.30, 0.25, 0.30), (0.25, 0.30, 0.25, 0.62), (0.25, 0.62, 0.15, 0.62)):
        c.line(a, b, c_, d, ch, CHALK, 0.8)
    c.path([(-0.18, 0.80), (-0.02, 0.86), (0.2, 0.78)], 0.012, (0.55, 0.85, 1.0), 0.9)
    c.poly([(0.22, 0.78), (0.14, 0.81), (0.16, 0.74)], (0.55, 0.85, 1.0), alpha=0.9)
    # bar chart and a sprout
    for k, hh in enumerate((0.12, 0.2, 0.3, 0.38)):
        c.line(0.44 + k * 0.10, 0.22, 0.44 + k * 0.10, 0.22 + hh, ch, (1.0, 0.85, 0.45), 0.85)
        c.line(0.44 + k * 0.10, 0.22 + hh, 0.52 + k * 0.10, 0.22 + hh, ch, (1.0, 0.85, 0.45), 0.85)
        c.line(0.52 + k * 0.10, 0.22 + hh, 0.52 + k * 0.10, 0.22, ch, (1.0, 0.85, 0.45), 0.85)
    c.line(0.40, 0.21, 0.88, 0.21, ch, CHALK, 0.8)
    c.path([(0.72, 0.60), (0.73, 0.70), (0.72, 0.80)], 0.012, (0.6, 1.0, 0.6), 0.9)
    craft.leaf(c, 0.72, 0.72, 0.12, 30, (0.6, 1.0, 0.65), 0.5)
    craft.leaf(c, 0.72, 0.78, 0.12, 150, (0.6, 1.0, 0.65), 0.5)
    craft.arc(c, 0.55, 0.80, 0.045, 0.045, 0, 360, ch, (1.0, 0.6, 0.65), 0.85, 12)
    # chalk tray with chalk and an eraser
    _crect(c, 0.0, 0.085, 1.96, 0.045, scale(wood, 0.85), r=0.008, lift=0.2)
    _crect(c, 0.0, 0.108, 1.96, 0.012, mix(wood, WHITE, 0.2), lift=0.0)
    for k, cc in enumerate((CHALK, (1.0, 0.85, 0.5), (0.7, 0.9, 1.0), CHALK)):
        _crect(c, -0.45 + k * 0.07, 0.122, 0.05, 0.014, cc, r=0.006, lift=0.1)
    _crect(c, 0.55, 0.128, 0.16, 0.03, (0.35, 0.3, 0.28), r=0.006, lift=0.1)
    _crect(c, 0.55, 0.14, 0.16, 0.012, (0.85, 0.8, 0.55), r=0.004, lift=0.0)
    soft_disc(c, -0.3, 0.78, 0.9, 0.12, WHITE, 0.07, 1.3, add=True)


@sprop("digedu_school_desk", aspect=1.1, fill=1.0)
def school_desk(c, color):
    rng = c.rng
    plastic = color or (0.17, 0.42, 0.87)
    wood = (0.80, 0.60, 0.36)
    steel = (0.62, 0.64, 0.68)
    ao(c, 0.0, 0.0, 1.1, 0.34)
    # chair behind: backrest, back legs
    for u in (-0.32, 0.32):
        c.line(u, 0.0, u, 0.5, 0.030, scale(steel, 0.75))
    _crect(c, 0.0, 0.80, 0.78, 0.30, plastic, r=0.08, lift=0.20)
    _crect(c, 0.0, 0.84, 0.70, 0.05, WHITE, r=0.02, alpha=0.15)
    c.line(-0.34, 0.66, 0.34, 0.66, 0.012, scale(plastic, 0.7), 0.6)
    soft_disc(c, -0.2, 0.86, 0.22, 0.12, WHITE, 0.18, 1.2, add=True)
    # desk legs
    for u in (-0.43, 0.43):
        c.line(u, 0.0, u, 0.46, 0.032, scale(steel, 0.8))
        c.line(u - 0.012, 0.0, u - 0.012, 0.46, 0.010, WHITE, 0.4)
        c.ellipse(u, 0.01, 0.045, 0.02, (0.15, 0.15, 0.17), lift=0)
    c.line(-0.43, 0.14, 0.43, 0.14, 0.022, scale(steel, 0.75))
    # top: front lip + top surface with grain; a book, a pencil and an eraser on it
    box3d(c, 0.0, 0.44, 1.0, 0.06, 0.52, scale(wood, 0.85), mix(wood, WHITE, 0.10), scale(wood, 0.55), lift=0.12, dx=0.55, dy=0.45)
    ox, oy = 0.52 * 0.55, 0.52 * 0.45
    for _ in range(10):
        t = rng.uniform(0.1, 0.9)
        x0 = -0.5 + t * ox
        y0 = 0.5 + t * oy
        c.line(x0 + rng.uniform(0.0, 0.3), y0, x0 + rng.uniform(0.35, 0.9), y0 + rng.uniform(-0.004, 0.004), 0.003, scale(wood, rng.uniform(0.78, 0.9)), 0.4)
    soft_disc(c, -0.1, 0.60, 0.5, 0.08, WHITE, 0.14, 1.2, add=True)
    box3d(c, -0.12, 0.505, 0.44, 0.05, 0.3, (0.90, 0.35, 0.30), (0.96, 0.9, 0.8), scale((0.9, 0.35, 0.3), 0.6), lift=0.12)
    box3d(c, -0.06, 0.555, 0.40, 0.045, 0.28, plastic, (0.96, 0.9, 0.8), scale(plastic, 0.6), lift=0.12)
    c.line(0.22, 0.54, 0.46, 0.62, 0.030, (1.0, 0.8, 0.2), 1.0)
    c.line(0.43, 0.607, 0.50, 0.634, 0.030, (0.95, 0.75, 0.62), 1.0)
    c.line(0.22, 0.54, 0.20, 0.53, 0.030, (0.3, 0.3, 0.35), 1.0)


@sprop("digedu_globe", aspect=0.8, fill=1.0)
def globe(c, color):
    rng = c.rng
    brass = (0.78, 0.60, 0.28)
    ao(c, 0.0, 0.0, 0.62, 0.18)
    c.ellipse(0.0, 0.03, 0.26, 0.26 * TILT, scale(brass, 0.45), lift=0)
    disc(c, 0.0, 0.05, 0.25, brass, TILT, 0.15)
    craft.hshade_box(c, 0.0, 0.14, 0.05, 0.2, mix(brass, WHITE, 0.2), scale(brass, 0.5))
    cx, cy, R = 0.0, 0.64, 0.34
    ocean = (0.20, 0.50, 0.82)
    c.circle(cx, cy, R, scale(ocean, 0.8), lift=0.1)
    c.circle(cx, cy, R * 0.99, ocean, lift=0.12)
    land = ((-0.12, 0.74, 0.12, 0.09, 20, (0.45, 0.72, 0.36)), (-0.02, 0.58, 0.08, 0.13, -8, (0.82, 0.68, 0.38)), (0.15, 0.74, 0.12, 0.07, -10, (0.45, 0.72, 0.36)),
            (-0.18, 0.54, 0.05, 0.1, 15, (0.4, 0.68, 0.34)), (0.14, 0.52, 0.06, 0.05, 0, (0.85, 0.72, 0.42)), (0.0, 0.90, 0.1, 0.03, 0, (0.95, 0.97, 1.0)),
            (-0.05, 0.40, 0.08, 0.03, 0, (0.95, 0.97, 1.0)))
    for (u, v, a, b, ang, col) in land:
        c.ellipse(u, v, a, b, col, angle=ang, lift=0.1)
        c.ellipse(u + 0.01, v - 0.01, a * 0.6, b * 0.5, scale(col, 0.8), lift=0, alpha=0.5, angle=ang)
    for k in range(-2, 3):                                                     # meridians and parallels
        craft.arc(c, cx, cy, R * 0.99 * abs(math.cos(k * 0.5)), R * 0.99, -90, 90, 0.004, (0.85, 0.93, 1.0), 0.35, 12)
    for v in (-0.15, 0.0, 0.15):
        c.line(cx - math.sqrt(R * R - v * v) * 0.97, cy + v, cx + math.sqrt(R * R - v * v) * 0.97, cy + v, 0.003, (0.85, 0.93, 1.0), 0.3)
    soft_disc(c, cx + 0.12, cy - 0.14, R * 0.8, R * 0.8, (0.0, 0.02, 0.12), 0.50, 1.6)
    soft_disc(c, cx - 0.12, cy + 0.12, R * 0.42, R * 0.34, WHITE, 0.45, 1.2, 30, add=True)
    # brass ring (tilted meridian) and axis pins
    craft.arc(c, cx, cy, R * 1.08, R * 1.08, 100, 300, 0.022, scale(brass, 0.6), 1.0, 20)
    craft.arc(c, cx, cy, R * 1.08, R * 1.08, 100, 300, 0.010, mix(brass, WHITE, 0.3), 1.0, 20)
    c.line(0.0, 0.18, 0.0, 0.30, 0.03, brass)


@sprop("digedu_books_school", aspect=1.45, fill=0.8)
def books_school(c, color):
    acc = color or (0.17, 0.42, 0.87)
    cols = (acc, (0.95, 0.55, 0.20), (0.25, 0.65, 0.45), (0.85, 0.30, 0.35), mix(acc, WHITE, 0.4))
    _bookstack(c, cols, 0.9, 0.16, 0.55, 4)


def _school_back(S, P, dark):
    rng = S.rng
    S.wall(P.wall_top, P.wall_bot, 0.62)
    S.glow(0.30, 0.25, 0.9, P.light, 0.30)
    S.rect(1.2, 0.50, 9.0, 0.24, scale(mix(P.wall_bot, P.accent_light, 0.45), 0.95 if not dark else 0.8), lift=0.0)     # painted dado
    for k in range(4):
        S.rect(1.55 + k * 0.17, 0.30, 0.10, 0.12, mix(P.accent_light, (1.0, 0.9, 0.5), 0.5 * (k % 2)), lift=0.0, alpha=0.8)       # pinned kids' art
    if dark:
        S.window(0.30, 0.26, 0.30, 0.34, (0.10, 0.12, 0.30), (0.25, 0.25, 0.45), (0.45, 0.45, 0.52))
    else:
        S.window(0.30, 0.26, 0.30, 0.34)
    S.pendant(0.95, -0.1, 0.10, (1.0, 0.92, 0.75), 0.10)
    S.pendant(1.55, -0.1, 0.10, (1.0, 0.92, 0.75), 0.10)


@niche("school", "School / classroom", subjects=("digedu_board", "digedu_school_desk"),
       strong=("school", "classroom", "students", "teacher", "kindergarten", "स्कूल", "विद्यालय", "कक्षा", "playschool", "primary school",
               "high school", "pathshala", "पाठशाला", "शिक्षक", "विद्यार्थी", "nursery school"),
       weak=("education", "learning", "kids", "children", "curriculum", "admission", "campus", "शिक्षा"),
       accent="#2d6cdf", mood="light", group="education", avoid=("coaching", "tuition", "ias", "jee", "neet", "scuba", "diving", "driving", "dance", "dancing", "music", "swimming", "flying", "aviation", "cooking", "martial", "karate", "language", "drama", "riding", "ballet", "chess", "fashion", "film", "ड्राइविंग", "नृत्य", "संगीत", "तैराकी"))
def school(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        _school_back(S, P, dark)
        S.floor(0.62, P.floor_top, P.floor_bot)
    fl = mix(mix(P.floor_top, P.surface, 0.5), WHITE, 0.18 if not dark else 0.0)
    S.wood(-1.6, 0.62, 4.0, 1.9, fl, plank=0.10, grain=0.25)
    S.rect(1.0, 0.62, 7.0, 0.012, scale(fl, 0.55), lift=0.0)
    S.rect(1.0, 0.64, 7.0, 0.03, scale(mix(P.wall_bot, P.accent_light, 0.3), 0.8), lift=0.0)                          # skirting
    # window light falling across the floor
    S.light_shaft(0.18, 0.64, 0.50, 0.64, 1.30, 1.15, 0.52, 1.15, color=P.light, alpha=0.12 if not dark else 0.09)
    S.soft(1.1, 0.78, 0.9, 0.14, P.light, 0.16, 1.5, add=True)
    bcol = (0.14, 0.32, 0.26) if not dark else (0.10, 0.22, 0.20)
    S.put("digedu_board", 1.05, 0.58, 0.44, color=bcol, subject=True, shadow=False)
    S.put("digedu_plant", 0.62, 0.72, 0.13, color=(0.9, 0.55, 0.3), shadow_alpha=0.2)
    S.put("digedu_school_desk", 0.84, 0.96, 0.37, color=P.accent, subject=True, shadow_alpha=0.20)
    S.put("digedu_school_desk", 1.35, 1.0, 0.37, color=mix(P.accent, (0.95, 0.55, 0.2), 0.8), shadow_alpha=0.20)
    S.put("digedu_globe", 0.84, 0.80, 0.17, shadow_alpha=0.22)
    S.put("digedu_books_school", 1.34, 0.835, 0.085, color=P.accent, shadow_alpha=0.2)
    S.focus("detail", 1.05, 0.40)
    with S.near():
        S.circle(0.55, 0.98, 0.04, P.accent_light, alpha=0.45, lift=0)
        S.circle(1.64, 0.42, 0.05, P.accent, alpha=0.20, lift=0)


# ====================================================================================================== COACHING / TUITION
def _face(g, u, v, r, skin, hair, shirt):
    g.circle(u, v - r * 2.2, r * 2.1, shirt, lift=0.1)                               # shoulders
    g.rect(u, v - r * 1.15, r * 0.7, r * 0.7, scale(skin, 0.9))
    g.circle(u, v, r, skin, lift=0.12)
    g.circle(u, v + r * 0.35, r * 1.02, hair, alpha=0.95)
    g.circle(u, v - r * 0.05, r * 0.88, skin, lift=0.1)


def _class_ui(g, acc):
    rng = g.c.rng
    skins = ((0.95, 0.76, 0.62), (0.80, 0.58, 0.42), (0.62, 0.42, 0.30), (0.90, 0.70, 0.55))
    g.rect(0, 0, 1.26, 0.70, (0.09, 0.10, 0.14))
    g.rect(-0.16, 0.035, 0.84, 0.56, mix(acc, (0.1, 0.06, 0.04), 0.55), r=0.012, lift=0.12)
    # a whiteboard behind the teacher and the teacher
    g.rect(-0.30, 0.13, 0.36, 0.20, (0.94, 0.95, 0.96), r=0.008)
    g.line(-0.44, 0.17, -0.20, 0.17, 0.010, acc, 0.9)
    g.line(-0.44, 0.12, -0.28, 0.12, 0.008, (0.5, 0.5, 0.6), 0.8)
    g.path([(-0.22, 0.08), (-0.16, 0.14), (-0.12, 0.09)], 0.008, (0.3, 0.6, 0.9), 0.9)
    _face(g, 0.02, 0.07, 0.07, skins[0], (0.18, 0.1, 0.08), mix(acc, WHITE, 0.2))
    g.rect(-0.30, -0.19, 0.18, 0.04, (0.0, 0.0, 0.0), r=0.02, alpha=0.5)
    g.circle(-0.37, -0.19, 0.012, (0.95, 0.25, 0.25))
    g.rect(0.16, 0.30, 0.09, 0.040, (0.9, 0.2, 0.2), r=0.02)
    g.rect(0.16, 0.30, 0.04, 0.012, WHITE, r=0.006)
    # participants strip
    for k in range(3):
        v = 0.17 - k * 0.19
        g.rect(0.46, v, 0.28, 0.17, mix(acc, (0.2, 0.2, 0.3), 0.3 + 0.2 * k), r=0.01, lift=0.1)
        _face(g, 0.46, v + 0.015, 0.035, skins[(k + 1) % 4], (0.1, 0.08, 0.07), (0.3 + 0.15 * k, 0.5, 0.8 - 0.2 * k))
    # control bar
    g.rect(-0.16, -0.30, 0.84, 0.07, (0.14, 0.15, 0.20), r=0.012)
    for k in range(5):
        g.circle(-0.34 + k * 0.09, -0.30, 0.021, (0.30, 0.31, 0.38) if k != 4 else (0.9, 0.25, 0.25))
    g.rect(0.12, -0.30, 0.16, 0.032, acc, r=0.016)
    g.rect(0.46, -0.30, 0.28, 0.07, (0.14, 0.15, 0.20), r=0.012)


@sprop("digedu_laptop_class", aspect=1.7, fill=0.92)
def laptop_class(c, color):
    _laptop(c, _class_ui, color or (0.95, 0.61, 0.07))


@sprop("digedu_open_book", aspect=3.3, fill=0.6)
def open_book(c, color):
    rng = c.rng
    cover = color or (0.55, 0.22, 0.14)
    ao(c, 0.0, 0.0, 2.0, 0.6)
    c.poly([(-0.94, 0.0), (0.94, 0.0), (1.0, 0.06), (-1.0, 0.06)], scale(cover, 0.6))
    c.poly([(-1.0, 0.06), (1.0, 0.06), (0.92, 0.46), (-0.92, 0.46)], cover, lift=0.10)
    for i in range(7):                                         # stack of page edges
        y = 0.075 + i * 0.011
        c.line(-0.94 + i * 0.005, y, 0.94 - i * 0.005, y, 0.006, (0.90, 0.87, 0.78), 0.9)
    L = _Flat(c, -0.93, 0.15, 0.91, 0.02, 0.05, 0.40)
    R = _Flat(c, 0.02, 0.15, 0.91, -0.02, -0.05, 0.40)
    for F, side in ((L, 0), (R, 1)):
        F.quad(0.0, 0.0, 1.0, 1.0, (0.985, 0.97, 0.93), 0.0)
        F.tint(0.0 if side else 0.9, 0.0, 0.1 if side else 1.0, 1.0, (0.88, 0.85, 0.78), 0.35)
        for k in range(10):                                    # paragraphs
            b = 0.88 - k * 0.075
            if side == 0 and k < 3:
                continue
            a0 = 0.10
            F.bar(a0, b, rng.uniform(0.55, 0.78), 0.022, (0.30, 0.28, 0.30), 0.75)
    # figure on the left page, heading on the right
    L.quad(0.12, 0.68, 0.85, 0.96, (0.55, 0.78, 0.95), 0.0, 0.9)
    L.quad(0.12, 0.68, 0.85, 0.77, (0.35, 0.60, 0.80), 0.0, 0.9)
    p = L.p(0.7, 0.86)
    c.ellipse(p[0], p[1], 0.035, 0.02, (1.0, 0.9, 0.5), lift=0)
    R.bar(0.10, 0.93, 0.5, 0.040, (0.2, 0.2, 0.25), 0.9)
    # yellow highlighter strokes
    R.tint(0.08, 0.60, 0.64, 0.655, (1.0, 0.92, 0.25), 0.55)
    R.tint(0.08, 0.525, 0.50, 0.58, (1.0, 0.92, 0.25), 0.55)
    R.tint(0.08, 0.375, 0.7, 0.43, (0.5, 0.95, 0.5), 0.5)
    soft_disc(c, 0.0, 0.33, 0.07, 0.17, BLACK, 0.30, 1.3)
    soft_disc(c, -0.4, 0.36, 0.6, 0.1, WHITE, 0.14, 1.3, add=True)
    _crect(c, 0.60, 0.04, 0.035, 0.12, (0.85, 0.2, 0.25), lift=0.05)                    # bookmark ribbon


@sprop("digedu_gradcap", aspect=1.5, fill=0.8)
def grad_cap(c, color):
    ink = (0.10, 0.11, 0.17)
    ao(c, 0.0, 0.0, 1.2, 0.34)
    # skull cap
    c.poly([(-0.30, 0.20), (0.30, 0.20), (0.34, 0.04), (0.0, -0.02), (-0.34, 0.04)], scale(ink, 1.5), lift=0.18)
    c.ellipse(0.0, 0.05, 0.34, 0.07, scale(ink, 0.8), lift=0, alpha=0.9)
    soft_disc(c, 0.18, 0.12, 0.2, 0.1, BLACK, 0.35, 1.4)
    # mortarboard: a flattened square
    top = [(-0.66, 0.35), (0.0, 0.62), (0.66, 0.35), (0.0, 0.14)]
    c.poly([(-0.66, 0.35), (0.0, 0.14), (0.66, 0.35), (0.66, 0.31), (0.0, 0.10), (-0.66, 0.31)], scale(ink, 0.6))
    c.poly(top, mix(ink, WHITE, 0.10), lift=0.22)
    c.poly([(-0.6, 0.35), (-0.05, 0.58), (-0.05, 0.50), (-0.5, 0.33)], WHITE, alpha=0.10)
    c.line(-0.66, 0.35, 0.0, 0.14, 0.006, mix(ink, WHITE, 0.4), 0.6)
    c.line(0.0, 0.14, 0.66, 0.35, 0.004, mix(ink, WHITE, 0.25), 0.5)
    # button and tassel
    c.circle(0.0, 0.38, 0.032, GOLD, lift=0.25)
    c.path([(0.0, 0.38), (0.30, 0.40), (0.55, 0.34), (0.60, 0.20)], 0.016, scale(GOLD, 0.85), 1.0)
    c.path([(0.0, 0.385), (0.30, 0.405), (0.55, 0.345), (0.60, 0.21)], 0.006, mix(GOLD, WHITE, 0.5), 0.8)
    c.circle(0.60, 0.21, 0.025, GOLD, lift=0.2)
    for k in range(9):
        x = 0.60 + (k - 4) * 0.012
        c.line(x, 0.20, x + (k - 4) * 0.004, 0.05, 0.010, scale(GOLD, 0.8 + 0.05 * (k % 3)), 0.95)
    gloss(c, -0.2, 0.40, 0.2, 0.03, 20, 0.30)


@sprop("digedu_highlighters", aspect=1.7, fill=0.34)
def highlighters(c, color):
    ao(c, 0.0, 0.0, 1.5, 0.30)
    _hl(c, -0.05, 0.10, 8, (0.98, 0.88, 0.20))
    _hl(c, 0.05, 0.19, 14, (0.95, 0.40, 0.62))
    _hl(c, -0.02, 0.28, 3, (0.35, 0.82, 0.50))


def _hl(c, u, v, ang, col):
    g = _G(c, u, v, ang)
    g.rect(0.0, 0.0, 0.62, 0.075, mix(col, WHITE, 0.1), r=0.03, lift=0.35)
    g.rect(0.28, 0.0, 0.20, 0.08, scale(col, 0.7), r=0.02, lift=0.3)
    g.rect(-0.35, 0.0, 0.10, 0.045, scale(col, 0.85), r=0.015, lift=0.2)
    g.rect(-0.06, 0.016, 0.34, 0.018, WHITE, r=0.008, alpha=0.5)
    g.rect(0.02, -0.0, 0.14, 0.05, WHITE, r=0.01, alpha=0.65)


@niche("coaching-tuition", "Coaching institute / tuition", subjects=("digedu_open_book", "digedu_gradcap"),
       strong=("coaching", "tuition", "tutor", "exam preparation", "ias", "jee", "neet", "कोचिंग", "ट्यूशन", "coaching institute",
               "coaching classes", "tuition classes", "upsc", "competitive exams", "test series", "होम ट्यूशन", "परीक्षा की तैयारी", "इंस्टिट्यूट"),
       weak=("classes", "study", "exam", "mentor", "online classes", "batch", "course", "preparation"),
       accent="#f39c12", mood="warm", group="education", avoid=("school", "kindergarten"))
def coaching(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.glow(0.7, 0.35, 1.0, (1.0, 0.75, 0.4), 0.30)
        # a wall of bookshelves, blurred, with warm window / string lights
        for (v, hm) in ((0.12, 0.10), (0.27, 0.12), (0.42, 0.12)):
            S.rect(1.2, v + 0.012, 3.2, 0.014, mix(P.wall_bot, P.ink, 0.45), lift=0.0)
            u = -0.3
            while u < 2.4:
                w, hh = rng.uniform(0.025, 0.055), rng.uniform(0.07, hm + 0.04)
                col = rng.choice([P.accent, P.accent_dark, (0.25, 0.4, 0.7), (0.8, 0.3, 0.3), (0.3, 0.6, 0.45), (0.92, 0.88, 0.78), mix(P.accent2, WHITE, 0.3)])
                S.rect(u + w / 2, v - hh / 2, w, hh, scale(col, 0.62 if dark else 0.95), lift=0.0)
                u += w + 0.003
        S.bokeh(10, 0.0, 0.05, 2.0, 0.55, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.35)], 0.012, 0.04, 0.35)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.soft(1.0, 0.70, 1.0, 0.16, (1.0, 0.8, 0.5), 0.26 if dark else 0.18, 1.5, add=True)
    S.wood(-1.6, 0.60, 4.0, 1.8, P.surface, plank=0.15, grain=0.3)
    S.rect(1.0, 0.60, 7.0, 0.010, scale(P.surface, 0.45), lift=0.0)
    S.put("digedu_lamp", 0.70, 0.84, 0.44, color=mix(P.accent, WHITE, 0.15), shadow_alpha=0.32)
    S.put("digedu_laptop_class", 1.20, 0.82, 0.38, color=P.accent, shadow_alpha=0.32)
    S.put("digedu_books_school", 1.50, 0.97, 0.12, color=P.accent, shadow_alpha=0.30)
    S.put("digedu_gradcap", 1.50, 0.835, 0.13, subject=True, shadow_alpha=0.2)
    S.put("digedu_open_book", 0.98, 1.0, 0.20, color=mix(P.accent_dark, (0.5, 0.2, 0.12), 0.5), subject=True, shadow_alpha=0.34)
    S.put("digedu_mug", 0.68, 0.98, 0.07, color=mix(P.accent_light, WHITE, 0.3))
    S.put("digedu_highlighters", 1.28, 1.0, 0.075, shadow_alpha=0.28)
    S.soft(0.92, 0.88, 0.32, 0.09, (1.0, 0.85, 0.5), 0.30 if dark else 0.18, 1.4, add=True)
    S.focus("detail", 0.98, 0.90)
    with S.near():
        S.circle(0.52, 0.40, 0.04, (1.0, 0.85, 0.5), alpha=0.45, lift=0)
        S.circle(1.64, 0.98, 0.05, P.accent, alpha=0.28, lift=0)
