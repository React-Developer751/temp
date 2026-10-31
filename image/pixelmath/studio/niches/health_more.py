"""More health niches: diagnostic lab, counselling practice, dietitian / nutritionist, animal welfare and rescue, bridal makeup."""
import math

from .. import craft
from ..craft import BLACK, WHITE, ao, gloss, soft_disc
from ..niches import niche
from ..stage import sprop
from ...props.core import _catmull
from ...raster import clamp, mix, scale
from .care_more import _blobs, _hpoly, _leaf, _lathe, _pal, _spoly_stage, _vpoly


class _Fast:
    """Cheaper drawing for props: axis-aligned rectangles become flat strips, polygons use the scanline fill, paths are short capsules."""
    def __init__(self, c):
        self._c = c

    def __getattr__(self, name):
        return getattr(self._c, name)

    def rect(self, u, v, w, h, color, r=0.0, lift=0.10, alpha=1.0):
        c = self._c
        s = c.s
        cx, cy, hw, hh = c.X(u), c.Y(v), w * s / 2, h * s / 2
        if min(r * s, hw, hh) > 2.2 and min(hw, hh) > 3.0:                      # rounded: scanline polygon with arc corners
            rr = min(r, w / 2, h / 2)
            pts = []
            for (qx, qy, a0) in ((u + w / 2 - rr, v + h / 2 - rr, 0), (u - w / 2 + rr, v + h / 2 - rr, 90), (u - w / 2 + rr, v - h / 2 + rr, 180),
                                 (u + w / 2 - rr, v - h / 2 + rr, 270)):
                for k in range(5):
                    t = math.radians(a0 + 90 * k / 4.0)
                    pts.append((qx + rr * math.cos(t), qy + rr * math.sin(t)))
            return _vpoly(c, pts, scale(color, 1 + lift), scale(color, 1 - lift * 1.2), alpha=alpha)
        x0, x1 = int(round(cx - hw)), max(int(round(cx - hw)) + 1, int(round(cx + hw)))
        y0, y1 = cy - hh, cy + hh
        n = 1 if not lift else int(clamp((y1 - y0) / 5.0, 1, 6))
        top, bot = scale(color, 1 + lift), scale(color, 1 - lift * 1.2)
        for i in range(n):
            ya, yb = int(round(y0 + (y1 - y0) * i / n)), int(round(y0 + (y1 - y0) * (i + 1) / n))
            c.cv.fill_rect(x0, ya, x1, max(yb, ya + 1), mix(top, bot, (i + 0.5) / n) if n > 1 else color, alpha)

    def ellipse(self, u, v, a, b, color, angle=0.0, lift=0.10, alpha=1.0, soft=1.0):
        c = self._c
        if max(a, b) * c.s < 26 or soft != 1.0:
            return c.ellipse(u, v, a, b, color, angle=angle, lift=lift, alpha=alpha, soft=soft)
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        pts = []
        for k in range(40):
            t = 2 * math.pi * k / 40.0
            x, y = a * math.cos(t), b * math.sin(t)
            pts.append((u + x * ca - y * sa, v + x * sa + y * ca))
        _vpoly(c, pts, scale(color, 1 + lift), scale(color, 1 - lift * 1.2), alpha=alpha)

    def circle(self, u, v, r, color, lift=0.10, alpha=1.0, soft=1.0):
        self.ellipse(u, v, r, r, color, 0.0, lift, alpha, soft)

    def poly(self, pts, color, lift=0.10, alpha=1.0, angle=0.0, pivot=(0.0, 0.0)):
        _vpoly(self._c, pts, scale(color, 1 + lift), scale(color, 1 - lift * 1.2), alpha=alpha)

    def path(self, pts, w, color, alpha=1.0, smooth=True, closed=False):
        pts = list(pts)
        if smooth and len(pts) > 2:
            pts = _catmull(pts, 3, closed)
        for a, b in zip(pts, pts[1:]):
            self._c.line(a[0], a[1], b[0], b[1], w, color, alpha)


def _sell(S, u, v, a, b, col, alpha=1.0):
    """Big flat ellipse on the stage (rug, pool of light) as a scanline polygon: much cheaper than an SDF ellipse."""
    _spoly_stage(S, [(u + a * math.cos(2 * math.pi * k / 48.0), v + b * math.sin(2 * math.pi * k / 48.0)) for k in range(48)], col, alpha)


def _hb(c, u, v, w, h, left, right, r=0.0, alpha=1.0):
    """Cheap left-to-right shaded box (vertical strips): cylinders, bottles, tubes. `left` is the lit side."""
    cx, cy, hw, hh = c.X(u), c.Y(v), w * c.s / 2, h * c.s / 2
    x0, x1 = cx - hw, cx + hw
    n = int(clamp((x1 - x0) / 3.0, 2, 9))
    for i in range(n):
        t = (i + 0.5) / n
        xa, xb = int(round(x0 + (x1 - x0) * i / n)), int(round(x0 + (x1 - x0) * (i + 1) / n))
        c.cv.fill_rect(xa, cy - hh, max(xb, xa + 1), cy + hh, mix(left, right, t ** 1.3), alpha)


def _sp(name, aspect=1.0, fill=1.0):
    """Register a studio prop that draws through the cheaper _Fast context."""
    def deco(fn):
        sprop(name, aspect, fill)(lambda c, color, _fn=fn: _fn(_Fast(c), color))
        return fn
    return deco


# ------------------------------------------------------------------------------------------------ shared helpers
def _dark(S):
    return S.pal.mood == "dark"


def _box3d(c, u, v, w, h, d, front, top, side, k=0.10):
    """A box seen from the upper right: front face (shaded left to right), top face and right side face. Base centre (u, v)."""
    ox, oy = d * 0.55, d * 0.36
    x0, x1 = u - w / 2, u + w / 2
    c.poly([(x1, v), (x1 + ox, v + oy), (x1 + ox, v + h + oy), (x1, v + h)], side, lift=0.08)
    c.poly([(x0, v + h), (x1, v + h), (x1 + ox, v + h + oy), (x0 + ox, v + h + oy)], top, lift=0.10)
    _hb(c, u, v + h / 2, w, h, scale(front, 1.06), scale(front, 0.84))
    return ox, oy


def _tube(c, u, v0, v1, w, liquid, cap, fill=0.7, capk=0.12, glass=(0.86, 0.93, 0.96)):
    """A capped sample tube standing on v0 with its cap top at v1."""
    r = w / 2
    capH = (v1 - v0) * capk
    vt = v1 - capH                                           # top of the glass
    c.ellipse(u, v0 + r, r, r, scale(glass, 0.6), lift=0.0)
    _hb(c, u, (v0 + r + vt) / 2, w, vt - v0 - r, scale(glass, 1.05), scale(glass, 0.62), alpha=0.9)
    lv = v0 + r + (vt - v0 - r) * fill
    c.ellipse(u, v0 + r, r * 0.9, r * 0.9, scale(liquid, 0.62), lift=0.0)
    _hb(c, u, (v0 + r + lv) / 2, w * 0.9, lv - v0 - r, scale(liquid, 1.25), scale(liquid, 0.58), alpha=1.0)
    c.ellipse(u, lv, r * 0.9, r * 0.2, scale(liquid, 1.35), lift=0.0, alpha=0.9)
    _hb(c, u, vt + capH * 0.45, w * 1.12, capH * 0.9, scale(cap, 1.25), scale(cap, 0.58), r=0.004)
    c.ellipse(u, vt + capH * 0.92, w * 0.56, w * 0.15, scale(cap, 1.35), lift=0.0)
    c.rect(u - r * 0.55, (v0 + vt) / 2 + r * 0.3, r * 0.22, (vt - v0) * 0.72, WHITE, r=r * 0.1, lift=0.0, alpha=0.55)
    c.rect(u, v0 + r * 2.0 + (vt - v0) * 0.1, w * 0.98, (vt - v0) * 0.12, (0.97, 0.97, 0.96), lift=0.0, alpha=0.9)


# ====================================================================================== DIAGNOSTIC LAB
BLOOD = (0.62, 0.06, 0.10)
URINE = (0.96, 0.80, 0.22)
SERUM = (0.95, 0.70, 0.30)
CAPS = ((0.55, 0.30, 0.70), (0.80, 0.14, 0.16), (0.96, 0.78, 0.18), (0.25, 0.50, 0.85), (0.30, 0.68, 0.40), (0.70, 0.72, 0.76))


@_sp("hlth_lab_rack", aspect=1.55, fill=1.0)
def lab_rack(c, color):
    """A rack of capped sample tubes (red blood, purple EDTA, yellow serum, blue, green) in two staggered rows on a white plastic frame."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.45, 0.20, 0.5)
    frame = (0.93, 0.95, 0.96)
    # bottom tray
    c.poly([(-0.72, 0.075), (0.72, 0.075), (0.78, 0.13), (-0.66, 0.13)], scale(frame, 0.9), lift=0.0)
    _hpoly(c, [(-0.72, 0.0), (0.72, 0.0), (0.72, 0.075), (-0.72, 0.075)], scale(frame, 1.02), scale(frame, 0.66), 0.05)
    cols = [(BLOOD, CAPS[1]), (BLOOD, CAPS[0]), (URINE, CAPS[2]), (SERUM, CAPS[3]), (BLOOD, CAPS[0]), (URINE, CAPS[4]), (BLOOD, CAPS[1]), (SERUM, CAPS[5])]
    back = [(-0.58 + 0.165 * i, 0.19) for i in range(8)]
    for i, (u, v0) in enumerate(back):                       # back row: paler and slightly higher
        liq, cap = cols[(i * 3 + 1) % 8]
        _tube(c, u + 0.02, v0, 0.88 - 0.03 * (i % 2), 0.13, mix(liq, (0.95, 0.95, 0.95), 0.12), mix(cap, (0.3, 0.3, 0.35), 0.18), fill=0.62 + 0.05 * (i % 3))
    # top plate (its upper face with holes) and the front lip
    c.poly([(-0.76, 0.48), (0.76, 0.48), (0.82, 0.56), (-0.70, 0.56)], scale(frame, 1.06), lift=0.0)
    for i in range(8):
        c.ellipse(back[i][0] + 0.02, 0.525, 0.058, 0.015, scale(frame, 0.45), lift=0.0)
    for i in range(7):
        u = -0.50 + 0.165 * i
        liq, cap = cols[(i * 5 + 2) % 8]
        _tube(c, u, 0.14, 0.82 + 0.03 * (i % 2), 0.14, liq, cap, fill=0.66 + 0.06 * ((i + 1) % 3))
    _hpoly(c, [(-0.76, 0.40), (0.76, 0.40), (0.76, 0.49), (-0.76, 0.49)], scale(frame, 1.04), scale(frame, 0.72), 0.06)
    c.rect(0.0, 0.485, 1.52, 0.012, WHITE, lift=0.0, alpha=0.7)
    # rack feet / side rails and an accent band
    for sg in (-1, 1):
        _hpoly(c, [(sg * 0.74 - 0.03, 0.02), (sg * 0.74 + 0.03, 0.02), (sg * 0.74 + 0.03, 0.48), (sg * 0.74 - 0.03, 0.48)], scale(frame, 1.0), scale(frame, 0.7), 0.0)
    c.rect(0.0, 0.43, 1.40, 0.022, acc, lift=0.1)
    for i in range(7):
        c.circle(-0.50 + 0.165 * i, 0.445, 0.004, scale(frame, 0.5), lift=0.0, alpha=0.6)
    soft_disc(c, 0.05, 0.22, 0.65, 0.07, WHITE, 0.16, 1.3, add=True)


@_sp("hlth_lab_analyser", aspect=1.34, fill=0.80)
def lab_analyser(c, color):
    """A benchtop blood analyser: white body, tinted lid over a carousel of tubes, a lit screen with a curve, buttons and a sample drawer."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.0, 0.24, 0.5)
    body = (0.95, 0.96, 0.97)
    w, h, d = 0.86, 0.60, 0.30
    ox, oy = _box3d(c, -0.04, 0.03, w, h, d, body, scale(body, 1.03), scale(body, 0.66))
    x0, x1 = -0.04 - w / 2, -0.04 + w / 2
    top = 0.03 + h
    # carousel under a smoked lid on the top face
    cu, cv_ = -0.04 + ox * 0.5, top + oy * 0.5
    c.ellipse(cu, cv_, 0.31, 0.083, (0.30, 0.34, 0.38), lift=0.0)
    c.ellipse(cu, cv_ + 0.004, 0.28, 0.072, (0.62, 0.68, 0.72), lift=0.0)
    for i in range(14):
        t = i / 14.0 * 2 * math.pi
        tx, ty = cu + math.cos(t) * 0.215, cv_ + math.sin(t) * 0.050
        c.circle(tx, ty + 0.01, 0.017, CAPS[i % 6], lift=0.12)
        c.rect(tx, ty - 0.004, 0.026, 0.026, mix(CAPS[i % 6], WHITE, 0.55), lift=0.0, alpha=0.9)
    c.ellipse(cu, cv_ + 0.004, 0.29, 0.076, (0.55, 0.78, 0.85), lift=0.0, alpha=0.30)
    soft_disc(c, cu - 0.1, cv_ + 0.03, 0.17, 0.028, WHITE, 0.55, 1.2, add=True)
    # front: dark panel with the screen and an accent bar
    c.rect(-0.04, 0.03 + h * 0.52, w * 0.92, h * 0.74, scale(body, 0.78), r=0.02, lift=0.0)
    c.rect(-0.04, 0.03 + h * 0.52, w * 0.90, h * 0.72, (0.12, 0.17, 0.21), r=0.02, lift=0.0)
    sx, sy = x0 + w * 0.34, 0.03 + h * 0.60
    c.rect(sx, sy, w * 0.52, h * 0.46, (0.03, 0.10, 0.13), r=0.012, lift=0.0)
    c.rect(sx, sy, w * 0.50, h * 0.43, mix((0.06, 0.28, 0.32), acc, 0.25), r=0.010, lift=0.0)
    pts = [(sx - w * 0.22 + w * 0.44 * t / 9.0, sy - h * 0.12 + h * 0.2 * (math.sin(t * 0.9) * 0.5 + 0.5) * (0.4 + 0.6 * math.sin(t / 9.0 * 3.1))) for t in range(10)]
    c.path(pts, 0.011, (0.55, 1.0, 0.92), 0.95)
    for k in range(5):
        c.rect(sx - w * 0.2 + k * w * 0.1, sy - h * 0.17, w * 0.06, 0.012 + 0.012 * ((k * 5) % 4), mix(acc, WHITE, 0.45), lift=0.0, alpha=0.85)
    c.glow(sx, sy, 0.17, acc, 0.20)
    # drawer, buttons, status lights
    c.rect(x0 + w * 0.76, 0.03 + h * 0.34, w * 0.34, h * 0.20, scale(body, 0.92), r=0.012, lift=0.12)
    c.rect(x0 + w * 0.76, 0.03 + h * 0.34 + h * 0.07, w * 0.34, 0.008, scale(body, 0.55), lift=0.0)
    c.rect(x0 + w * 0.76, 0.03 + h * 0.34, w * 0.14, 0.012, scale(body, 0.5), r=0.004, lift=0.0)
    for k, col in enumerate(((0.3, 0.9, 0.5), (0.95, 0.75, 0.2), acc)):
        c.circle(x0 + w * (0.64 + k * 0.1), 0.03 + h * 0.70, 0.012, col, lift=0.2)
        c.glow(x0 + w * (0.64 + k * 0.1), 0.03 + h * 0.70, 0.04, col, 0.22)
    c.rect(x0 + w * 0.76, 0.03 + h * 0.58, w * 0.30, 0.016, mix(acc, WHITE, 0.2), r=0.006, lift=0.1)
    c.rect(-0.04, 0.03 + h * 0.07, w * 0.98, 0.012, acc, lift=0.1)
    # feet, tubing and a waste bottle behind
    for sg in (-1, 1):
        c.rect(-0.04 + sg * w * 0.42, 0.015, 0.06, 0.03, (0.18, 0.2, 0.22), r=0.006, lift=0.0)
    c.path([(x1 + 0.10, 0.20), (x1 + 0.12, 0.32), (x1 + 0.07, 0.42), (x1 + 0.02, 0.50)], 0.012, mix(acc, WHITE, 0.55), 0.9)
    gloss(c, x0 + 0.12, 0.03 + h * 0.9, 0.18, 0.02, 0, 0.3)


@_sp("hlth_lab_scope", aspect=0.78, fill=1.0)
def lab_scope(c, color):
    """A compound microscope with a glass slide on the stage, objectives on a turret, focus knobs and a lit base."""
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 0.72, 0.14, 0.5)
    metal = (0.90, 0.92, 0.94)
    dark = (0.16, 0.18, 0.21)
    # base
    _hpoly(c, [(-0.34, 0.0), (0.30, 0.0), (0.27, 0.075), (-0.31, 0.075)], scale(metal, 1.08), scale(metal, 0.62), 0.05)
    c.ellipse(-0.02, 0.078, 0.29, 0.035, scale(metal, 1.12), lift=0.0)
    c.glow(-0.02, 0.10, 0.20, (1.0, 0.95, 0.8), 0.32)
    c.ellipse(-0.04, 0.095, 0.09, 0.02, (1.0, 0.97, 0.85), lift=0.0)
    # arm: a C-shaped limb rising behind the stage
    arm = [(0.14, 0.06), (0.30, 0.06), (0.31, 0.36), (0.28, 0.62), (0.20, 0.78), (0.06, 0.88), (-0.03, 0.80), (0.06, 0.72), (0.12, 0.58), (0.14, 0.34)]
    _hpoly(c, arm, scale(metal, 1.10), scale(metal, 0.60), 0.04, smooth=2)
    c.path([(0.20, 0.10), (0.215, 0.40), (0.19, 0.64), (0.10, 0.80)], 0.016, WHITE, 0.45)
    # stage, slide and clips
    c.rect(-0.04, 0.37, 0.48, 0.032, scale(dark, 1.2), r=0.01, lift=0.1)
    c.poly([(-0.26, 0.386), (0.18, 0.386), (0.22, 0.405), (-0.22, 0.405)], scale(dark, 1.9), lift=0.0)
    c.poly([(-0.18, 0.402), (0.06, 0.402), (0.10, 0.418), (-0.14, 0.418)], (0.84, 0.92, 0.95), lift=0.0, alpha=0.85)
    c.ellipse(-0.06, 0.409, 0.045, 0.007, (0.85, 0.35, 0.55), lift=0.0, alpha=0.9)
    c.rect(-0.04, 0.345, 0.14, 0.02, scale(dark, 1.5), lift=0.0)
    # tube, turret and objectives
    c.path([(0.07, 0.86), (-0.07, 0.99)], 0.12, scale(metal, 0.62), 1.0, smooth=False)
    c.path([(0.065, 0.87), (-0.075, 1.0)], 0.09, scale(metal, 1.02), 1.0, smooth=False)
    c.path([(-0.06, 0.99), (-0.11, 1.03)], 0.06, dark, 1.0, smooth=False)
    c.ellipse(-0.115, 1.03, 0.035, 0.012, scale(dark, 2.0), angle=-45, lift=0.0)
    c.poly([(0.00, 0.80), (0.12, 0.80), (0.10, 0.68), (-0.02, 0.68)], scale(dark, 1.6), lift=0.14)
    c.ellipse(0.05, 0.795, 0.07, 0.016, scale(dark, 2.4), lift=0.0)
    for k, (uu, hh) in enumerate(((-0.01, 0.15), (0.05, 0.19), (0.11, 0.13))):
        c.poly([(uu - 0.02, 0.69), (uu + 0.02, 0.69), (uu + 0.016, 0.69 - hh * 0.5), (uu - 0.016, 0.69 - hh * 0.5)], scale(metal, 0.7 + 0.1 * k), lift=0.2)
        c.rect(uu, 0.69 - hh * 0.5 - 0.02, 0.02, 0.04, scale(dark, 1.0), lift=0.1)
        c.rect(uu, 0.69 - hh * 0.2, 0.034, 0.016, [acc, (0.9, 0.7, 0.2), (0.85, 0.3, 0.3)][k], lift=0.1)
    # focus knobs
    c.circle(0.24, 0.32, 0.075, scale(dark, 1.4), lift=0.12)
    c.circle(0.24, 0.32, 0.045, scale(metal, 0.95), lift=0.12)
    c.circle(0.24, 0.32, 0.016, scale(dark, 1.5), lift=0.0)
    c.circle(0.24, 0.18, 0.05, scale(dark, 1.3), lift=0.12)
    c.circle(0.24, 0.18, 0.028, scale(metal, 0.9), lift=0.12)
    gloss(c, -0.02, 0.94, 0.05, 0.02, 30, 0.5)


@_sp("hlth_lab_kit", aspect=1.75, fill=0.50)
def lab_kit(c, color):
    """A home-collection kit: a white case with a teal band, a tourniquet, capped tubes, swab sachets, cotton and gloves lying in front."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.6, 0.22, 0.5)
    # the case (behind, left)
    case = (0.95, 0.96, 0.97)
    ox, oy = _box3d(c, -0.40, 0.04, 0.62, 0.34, 0.2, case, scale(case, 1.03), scale(case, 0.68))
    c.rect(-0.40, 0.04 + 0.34 * 0.55, 0.62, 0.05, acc, lift=0.10)
    for sg in (-1, 1):
        c.rect(-0.40 + sg * 0.20, 0.04 + 0.34 * 0.55, 0.045, 0.085, (0.78, 0.8, 0.84), r=0.008, lift=0.2)
    c.path([(-0.55, 0.38 + oy), (-0.52, 0.47 + oy), (-0.26, 0.47 + oy), (-0.23, 0.38 + oy)], 0.022, (0.30, 0.33, 0.37), 1.0)
    cu, cv_ = -0.40, 0.04 + 0.34 * 0.18
    c.rect(cu, cv_ + 0.20, 0.17, 0.17, WHITE, r=0.02, lift=0.0, alpha=0.85)
    c.rect(cu, cv_ + 0.20, 0.17 * 0.34, 0.17 * 0.74, (0.86, 0.2, 0.22), r=0.008, lift=0.0)
    c.rect(cu, cv_ + 0.20, 0.17 * 0.74, 0.17 * 0.34, (0.86, 0.2, 0.22), r=0.008, lift=0.0)
    # tubes lying down in a sealed bag
    c.rect(0.28, 0.10, 0.62, 0.17, (0.88, 0.94, 0.96), r=0.02, lift=0.0, alpha=0.55)
    c.rect(0.28, 0.168, 0.62, 0.02, mix(acc, WHITE, 0.4), lift=0.0, alpha=0.8)
    for i, cap in enumerate((CAPS[1], CAPS[0], CAPS[2])):
        v = 0.07 + 0.045 * i
        liq = (BLOOD, BLOOD, URINE)[i]
        _hb(c, 0.22, v + 0.03, 0.40, 0.050, (0.95, 0.98, 1.0), (0.62, 0.7, 0.74), r=0.025, alpha=0.9)
        _hb(c, 0.18, v + 0.03, 0.30, 0.036, scale(liq, 1.2), scale(liq, 0.55), r=0.018)
        _hb(c, 0.43, v + 0.03, 0.065, 0.062, scale(cap, 1.2), scale(cap, 0.6), r=0.012)
    # tourniquet: a folded blue strap with a buckle
    c.poly([(-0.02, 0.01), (0.20, 0.01), (0.18, 0.05), (-0.04, 0.05)], (0.22, 0.45, 0.82), lift=0.18)
    c.rect(0.08, 0.03, 0.22, 0.012, (0.55, 0.72, 0.95), lift=0.0, alpha=0.6)
    c.rect(0.19, 0.03, 0.03, 0.045, (0.82, 0.84, 0.88), r=0.006, lift=0.2)
    # swabs, cotton and a glove
    for k, uu in enumerate((0.55, 0.64)):
        c.rect(uu, 0.035 + 0.01 * k, 0.075, 0.05, (0.94, 0.94, 0.96), r=0.006, lift=0.12)
        c.circle(uu, 0.037 + 0.01 * k, 0.014, acc, lift=0.0, alpha=0.8)
    for uu, vv in ((-0.12, 0.03), (-0.07, 0.03), (-0.095, 0.05)):
        c.circle(uu, vv, 0.026, (0.98, 0.98, 0.97), lift=0.25)
        soft_disc(c, uu + 0.01, vv - 0.005, 0.02, 0.012, BLACK, 0.12, 1.2)


@_sp("hlth_lab_report", aspect=1.02, fill=1.0)
def lab_report(c, color):
    """A clipboard with a printed report (header band, result rows with ticks, a small chart) leaning on a teal folder, a pen in the clip."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 0.95, 0.12, 0.45)
    # folder behind, tilted
    fold = mix(acc, (0.1, 0.35, 0.45), 0.35)
    c.poly([(-0.46, 0.03), (0.50, 0.05), (0.52, 0.80), (-0.42, 0.78)], scale(fold, 0.72), lift=0.1)
    c.poly([(0.36, 0.80), (0.44, 0.85), (0.52, 0.80), (0.50, 0.05)], scale(fold, 0.6), lift=0.0, alpha=0.0)
    c.poly([(-0.42, 0.78), (0.52, 0.80), (0.50, 0.84), (-0.40, 0.82)], scale(fold, 1.2), lift=0.1)
    # clipboard
    wood = (0.78, 0.60, 0.40)
    c.poly([(-0.30, 0.02), (0.34, 0.02), (0.34, 0.97), (-0.30, 0.97)], scale(wood, 0.62), lift=0.0)
    _hb(c, 0.02, 0.495, 0.64, 0.95, scale(wood, 1.12), scale(wood, 0.8), r=0.02)
    # paper
    c.rect(0.02, 0.47, 0.54, 0.84, (0.99, 0.99, 0.98), r=0.006, lift=0.04)
    c.rect(0.02 + 0.27, 0.47, 0.012, 0.84, scale(WHITE, 0.82), lift=0.0, alpha=0.5)
    c.rect(0.02, 0.80, 0.50, 0.075, acc, r=0.008, lift=0.08)
    c.circle(-0.18, 0.80, 0.026, WHITE, lift=0.0, alpha=0.9)
    c.circle(-0.18, 0.80, 0.014, acc, lift=0.0)
    c.rect(0.09, 0.805, 0.22, 0.010, WHITE, lift=0.0, alpha=0.8)
    c.rect(0.07, 0.784, 0.17, 0.007, WHITE, lift=0.0, alpha=0.55)
    for i in range(7):
        v = 0.70 - i * 0.062
        if i % 2 == 0:
            c.rect(0.02, v, 0.50, 0.05, mix(acc, WHITE, 0.90), lift=0.0)
        c.rect(-0.10 + 0.0, v, 0.20 + 0.10 * ((i * 3) % 3) * 0.5, 0.012, (0.50, 0.54, 0.58), lift=0.0, alpha=0.8)
        c.rect(0.12, v, 0.07, 0.012, (0.62, 0.66, 0.7), lift=0.0, alpha=0.7)
        ok = (i % 3 != 1)
        c.circle(0.235, v, 0.014, (0.25, 0.70, 0.40) if ok else (0.92, 0.55, 0.15), lift=0.15)
    # chart at the bottom
    c.rect(0.02, 0.19, 0.50, 0.17, (0.96, 0.98, 0.98), r=0.006, lift=0.0)
    for k in range(6):
        hh = 0.03 + 0.09 * (0.5 + 0.5 * math.sin(k * 1.3 + 0.5))
        c.rect(-0.16 + k * 0.075, 0.115 + hh / 2, 0.045, hh, mix(acc, WHITE, 0.15 + 0.1 * (k % 2)), lift=0.1)
    c.path([(-0.20, 0.17), (-0.08, 0.22), (0.04, 0.19), (0.16, 0.26), (0.26, 0.23)], 0.008, (0.9, 0.35, 0.3), 0.9)
    # clip and pen
    c.rect(0.02, 0.965, 0.26, 0.055, (0.80, 0.82, 0.86), r=0.012, lift=0.28)
    c.rect(0.02, 0.985, 0.15, 0.022, (0.58, 0.6, 0.65), r=0.006, lift=0.0)
    c.poly([(0.20, 0.50), (0.215, 0.50), (0.27, 0.93), (0.255, 0.93)], (0.12, 0.2, 0.45), lift=0.3)
    gloss(c, -0.20, 0.55, 0.012, 0.25, 0, 0.35)


@niche("diagnostic-lab", "Diagnostic / pathology lab", subjects=("hlth_lab_rack",),
       strong=("diagnostic lab", "diagnostic centre", "diagnostic center", "pathology lab", "pathology laboratory", "blood test", "blood tests", "lab test", "lab tests",
               "sample collection", "home sample collection", "health checkup", "full body checkup", "medical laboratory", "path lab", "thyroid test", "blood sample",
               "डायग्नोस्टिक", "पैथोलॉजी", "पैथ लैब", "ब्लड टेस्ट", "खून की जांच", "जांच केंद्र", "लैब टेस्ट", "sample collection ghar par", "khoon ki jaanch", "health checkup package"),
       weak=("pathology", "diagnostics", "phlebotomist", "lab report", "test report", "test tube", "microscope", "analyser", "analyzer", "cbc", "lipid profile", "reports",
             "जांच", "रिपोर्ट", "लैब", "jaanch"),
       accent="#0f8a8f", mood="light", group="wellness",
       avoid=("doctor", "clinic", "डॉक्टर", "dental", "dentist", "chemist", "pharmacy", "science lab", "robotics", "stem lab"))
def diagnostic_lab(S):
    P = S.pal
    dark = _dark(S)
    rng = S.rng
    gl = 1.6 if dark else 1.0
    tile = mix(P.wall_top, WHITE, 0.45) if not dark else scale(P.wall_top, 1.5)
    with S.far():
        S.wall(P.wall_top, mix(P.wall_bot, P.accent_light, 0.18), 0.54)
        # glass partition with the lab behind it, a window with a blind, wall cabinets
        S.rect(0.34, 0.27, 0.62, 0.40, mix(P.accent_light, P.wall_top, 0.55), lift=0.0, alpha=0.9)
        S.window(0.34, 0.27, 0.54, 0.34, sky_top=(0.72, 0.88, 0.95), sky_bot=(0.93, 0.98, 1.0), frame=scale(P.paper, 0.92), bars=False)
        for k in range(8):
            S.rect(0.34, 0.12 + k * 0.040, 0.54, 0.014, mix(P.paper, P.accent_light, 0.3), lift=0.0, alpha=0.65)
        S.rect(1.60, 0.12, 0.90, 0.20, scale(P.paper, 0.98), r=0.008, lift=0.0)
        for k in range(4):
            S.rect(1.28 + k * 0.22, 0.12, 0.20, 0.18, mix(P.paper, P.accent_light, 0.2), r=0.006, lift=0.0)
            S.circle(1.37 + k * 0.22, 0.13, 0.008, scale(P.paper, 0.6), lift=0.0)
        # shelf with reagent bottles (blurred)
        S.rect(1.55, 0.38, 1.0, 0.012, scale(P.paper, 0.8), lift=0.0)
        for k in range(9):
            col = [P.accent, (0.9, 0.75, 0.3), (0.75, 0.3, 0.3), mix(P.accent_light, WHITE, 0.3), (0.35, 0.55, 0.8)][k % 5]
            hh = 0.05 + 0.025 * ((k * 7) % 3)
            S.ellipse(1.12 + k * 0.105, 0.38 - hh * 0.55, 0.036, hh * 0.55, col, lift=0.12)         # round flasks with necks
            S.rect(1.12 + k * 0.105, 0.38 - hh * 1.25, 0.016, hh * 0.7, mix(col, WHITE, 0.45), lift=0.0, alpha=0.8)
        # tiled splash-back with grid lines and an accent stripe
        S.rect(1.0, 0.495, 7.0, 0.11, tile, lift=0.0)
        for k in range(40):
            S.rect(-1.0 + k * 0.12, 0.495, 0.004, 0.11, scale(tile, 0.9), lift=0.0)
        S.rect(1.0, 0.44, 7.0, 0.012, P.accent, lift=0.0, alpha=0.8)
        S.glow(1.0, 0.0, 1.3, P.light, 0.38 * gl, 1.5)
        S.bokeh(7, 0.0, 0.10, 2.0, 0.45, [P.accent_light, WHITE, (0.8, 0.95, 1.0)], 0.012, 0.04, 0.3 * gl)
        S.floor(0.54, mix(P.paper, P.accent_light, 0.3) if not dark else scale(P.floor_top, 1.1), P.floor_bot)
    # the bench: white top with a glossy edge and a teal cabinet front below
    top = mix(P.paper, P.accent_light, 0.12) if not dark else scale(P.paper, 0.45)
    S.floor(0.545, scale(top, 1.02), scale(top, 0.80))
    S.rect(1.0, 0.549, 7.0, 0.008, scale(top, 0.80), lift=0.0, alpha=0.8)
    S.rect(1.0, 0.540, 7.0, 0.006, WHITE, lift=0.0, alpha=0.7)
    S.put("hlth_lab_scope", 0.92, 0.80, 0.50, color=P, shadow_w=0.34)
    S.put("hlth_lab_analyser", 1.50, 0.79, 0.40, color=P, shadow_w=0.5)
    S.put("hlth_lab_rack", 1.16, 0.93, 0.48, color=P, subject=True, shadow_w=0.8)
    S.put("hlth_lab_report", 0.70, 1.01, 0.32, color=P, shadow_w=0.4)
    S.put("hlth_lab_kit", 1.40, 1.04, 0.19, color=P, shadow_w=0.5)
    S.focus("detail", 1.16, 0.80)
    with S.near():
        S.circle(0.45, 1.08, 0.06, mix(P.accent_light, WHITE, 0.3), alpha=0.30, lift=0)
        S.circle(1.95, 0.60, 0.05, P.accent_light, alpha=0.24, lift=0)


# ====================================================================================== COUNSELLING PRACTICE
def _quad(c, u, v, w, h, ang, col, lift=0.14, rnd=1, alpha=1.0):
    """A rotated rounded rectangle (cushion, notebook, pillow) as a smoothed polygon."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    pts = [(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in pts]
    _vpoly(c._c if isinstance(c, _Fast) else c, pts, scale(col, 1 + lift), scale(col, 1 - lift * 1.2), smooth=rnd, alpha=alpha)
    return pts


@_sp("hlth_couns_sofa", aspect=1.95, fill=1.0)
def couns_sofa(c, color):
    """A two-seat therapy sofa in soft fabric: two back cushions, two seat cushions, rolled arms, a throw pillow on each side,
    a knitted blanket over one arm and wooden legs."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    fab = mix(acc, (0.78, 0.80, 0.78), 0.55)
    wood = (0.62, 0.44, 0.28)
    ao(c, 0.0, 0.0, 1.9, 0.22, 0.55)
    for sx in (-0.78, 0.78):                                  # legs
        c.poly([(sx - 0.035, 0.10), (sx + 0.035, 0.10), (sx + 0.025, 0.0), (sx - 0.025, 0.0)], wood, lift=0.2)
    _hb(c, 0.0, 0.21, 1.86, 0.22, scale(fab, 0.95), scale(fab, 0.66), r=0.05)                       # base
    c.rect(0.0, 0.64, 1.50, 0.66, scale(fab, 0.74), r=0.10, lift=0.10)                              # back frame
    for sx in (-0.37, 0.37):                                   # back cushions
        c.rect(sx, 0.63, 0.72, 0.52, fab, r=0.11, lift=0.16)
        c.rect(sx, 0.86, 0.66, 0.05, mix(fab, WHITE, 0.25), r=0.02, lift=0.0, alpha=0.5)
        soft_disc(c, sx + 0.10, 0.55, 0.32, 0.18, BLACK, 0.12, 1.2)
    c.rect(0.0, 0.62, 0.012, 0.50, scale(fab, 0.45), lift=0.0, alpha=0.8)
    for sx in (-0.37, 0.37):                                   # seat cushions
        c.rect(sx, 0.39, 0.74, 0.19, mix(fab, WHITE, 0.06), r=0.07, lift=0.14)
        c.rect(sx, 0.465, 0.70, 0.022, mix(fab, WHITE, 0.30), r=0.01, lift=0.0, alpha=0.55)
        c.rect(sx, 0.285, 0.74, 0.012, scale(fab, 0.45), lift=0.0, alpha=0.6)
        for k in range(-1, 2):
            c.rect(sx + k * 0.19, 0.34, 0.004, 0.07, scale(fab, 0.62), lift=0.0, alpha=0.35)
    for sx in (-0.84, 0.84):                                   # rolled arms
        _hb(c, sx, 0.34, 0.24, 0.50, scale(fab, 0.92) if sx < 0 else scale(fab, 0.84), scale(fab, 0.66) if sx < 0 else scale(fab, 0.58), r=0.06)
        c.ellipse(sx, 0.595, 0.12, 0.05, mix(fab, WHITE, 0.14), lift=0.0)
        c.rect(sx - 0.03 if sx < 0 else sx + 0.03, 0.50, 0.03, 0.36, WHITE, lift=0.0, alpha=0.12)
    # throw pillows: one warm mustard, one cream with a stripe band
    pts = _quad(c, -0.55, 0.62, 0.36, 0.34, 11, (0.93, 0.72, 0.36), 0.2, 2)
    for k in range(4):
        c.line(-0.67 + k * 0.08, 0.52 + k * 0.012, -0.64 + k * 0.08, 0.72 + k * 0.012, 0.012, (0.95, 0.80, 0.50), 0.7)
    _quad(c, 0.43, 0.60, 0.36, 0.32, -9, (0.96, 0.93, 0.86), 0.18, 2)
    c.line(0.26, 0.60, 0.60, 0.55, 0.05, mix(acc, WHITE, 0.15), 0.9)
    # knitted blanket over the right arm: a draped panel with stripes and fringe
    bl = (0.93, 0.80, 0.62)
    _vpoly(c._c, [(0.74, 0.60), (0.96, 0.60), (1.03, 0.38), (0.96, 0.16), (0.72, 0.20), (0.76, 0.42)], scale(bl, 1.05), scale(bl, 0.74), smooth=1)
    for k in range(5):
        v = 0.55 - k * 0.075
        c.line(0.75 - k * 0.006, v, 1.01 - k * 0.01, v - 0.005, 0.016, mix(acc, bl, 0.35) if k % 2 == 0 else (0.98, 0.95, 0.88), 0.8)
    for k in range(9):
        c.line(0.73 + k * 0.03, 0.19, 0.73 + k * 0.03 + 0.003, 0.14, 0.006, scale(bl, 0.95), 0.9)
    soft_disc(c, -0.1, 0.90, 0.6, 0.06, WHITE, 0.14, 1.3, add=True)


@_sp("hlth_couns_table", aspect=0.92, fill=1.0)
def couns_table(c, color):
    """A small round side table with a cup of tea (steam), a closed notebook with a pen, and a tissue box."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    wood = (0.66, 0.48, 0.30)
    ao(c, 0.0, 0.0, 0.84, 0.16, 0.5)
    for sx, tilt in ((-0.28, -0.07), (0.28, 0.07), (0.0, 0.0)):
        c.poly([(sx * 0.9 - 0.02, 0.46), (sx * 0.9 + 0.02, 0.46), (sx + tilt + 0.012, 0.0), (sx + tilt - 0.012, 0.0)], scale(wood, 0.8 if sx else 0.6), lift=0.15)
    c.ellipse(0.0, 0.455, 0.46, 0.085, scale(wood, 0.62), lift=0.0)
    c.ellipse(0.0, 0.475, 0.46, 0.085, wood, lift=0.16)
    c.ellipse(0.0, 0.478, 0.40, 0.072, scale(wood, 1.08), lift=0.0)
    for k in range(4):
        c.line(-0.30 + k * 0.05, 0.47 + k * 0.004, 0.06 + k * 0.08, 0.485 - k * 0.004, 0.004, scale(wood, 0.85), 0.4)
    soft_disc(c, -0.1, 0.5, 0.28, 0.035, WHITE, 0.30, 1.3, add=True)
    # notebook
    nb = mix(acc, (0.9, 0.9, 0.9), 0.1)
    _quad(c, -0.14, 0.495, 0.40, 0.11, 0, scale(nb, 0.75), 0.0, 0)
    c.poly([(-0.34, 0.49), (0.06, 0.49), (0.08, 0.535), (-0.32, 0.535)], nb, lift=0.12)
    c.poly([(-0.34, 0.49), (0.06, 0.49), (0.06, 0.478), (-0.34, 0.478)], (0.96, 0.94, 0.88), lift=0.0)
    c.line(-0.04, 0.488, -0.04, 0.536, 0.012, scale(nb, 0.55), 0.8)
    c.line(-0.30, 0.52, 0.04, 0.52, 0.008, mix(nb, WHITE, 0.35), 0.5)
    c.line(-0.30, 0.50, 0.03, 0.55, 0.012, (0.15, 0.17, 0.25), 1.0)                 # pen
    # tea cup on a saucer with steam
    c.ellipse(0.22, 0.48, 0.17, 0.040, (0.97, 0.96, 0.93), lift=0.0)
    c.ellipse(0.22, 0.487, 0.12, 0.025, scale((0.97, 0.96, 0.93), 0.8), lift=0.0)
    _hb(c, 0.22, 0.545, 0.17, 0.11, (1.0, 1.0, 0.98), (0.78, 0.78, 0.76))
    c.ellipse(0.22, 0.49, 0.085, 0.022, (0.88, 0.88, 0.86), lift=0.0)
    c.ellipse(0.22, 0.60, 0.085, 0.024, (0.99, 0.99, 0.98), lift=0.0)
    c.ellipse(0.22, 0.598, 0.068, 0.018, (0.55, 0.32, 0.14), lift=0.0)
    c.ring(0.315, 0.55, 0.030, 0.014, (0.96, 0.96, 0.94), 1.0)
    craft.steam(c, 0.22, 0.63, 0.20, w=0.04, n=1, alpha=0.2)
    # tissue box
    tb = mix(acc, WHITE, 0.5)
    ox, oy = _box3d(c, 0.02, 0.50, 0.22, 0.12, 0.14, tb, mix(tb, WHITE, 0.4), scale(tb, 0.72))
    c.poly([(0.02 - 0.06, 0.62 + oy * 0.5), (0.02 + 0.07, 0.62 + oy * 0.5), (0.02 + 0.12, 0.74), (0.02 + 0.02, 0.70), (0.02 - 0.05, 0.75)], (0.99, 0.99, 0.98), lift=0.05)
    c.ellipse(0.02 + ox * 0.5, 0.62 + oy * 0.5, 0.075, 0.016, scale(tb, 0.5), lift=0.0, alpha=0.7)
    c.ellipse(0.02, 0.56, 0.05, 0.03, mix(acc, WHITE, 0.2), lift=0.0, alpha=0.9)


@_sp("hlth_couns_lamp", aspect=0.45, fill=1.0)
def couns_lamp(c, color):
    """A floor lamp with a cream drum shade that glows warm, a slim brass stem and a round foot."""
    ao(c, 0.0, 0.0, 0.42, 0.10, 0.45)
    brass = (0.78, 0.60, 0.30)
    c.ellipse(0.0, 0.02, 0.17, 0.035, scale(brass, 0.7), lift=0.0)
    c.ellipse(0.0, 0.035, 0.17, 0.032, brass, lift=0.12)
    c.rect(0.0, 0.40, 0.022, 0.72, brass, lift=0.0)
    c.rect(-0.006, 0.40, 0.006, 0.70, mix(brass, WHITE, 0.5), lift=0.0, alpha=0.7)
    c.glow(0.0, 0.84, 0.55, (1.0, 0.82, 0.5), 0.30)
    _vpoly(c._c, [(-0.20, 0.97), (0.20, 0.97), (0.24, 0.69), (-0.24, 0.69)], (1.0, 0.95, 0.80), (0.96, 0.78, 0.50), alpha=1.0)
    c.ellipse(0.0, 0.97, 0.20, 0.032, (1.0, 0.99, 0.92), lift=0.0)
    c.ellipse(0.0, 0.97, 0.17, 0.024, (1.0, 0.88, 0.55), lift=0.0)
    c.ellipse(0.0, 0.69, 0.24, 0.032, (0.98, 0.78, 0.46), lift=0.0, alpha=0.9)
    c.rect(-0.12, 0.83, 0.02, 0.26, WHITE, lift=0.0, alpha=0.25)


@_sp("hlth_couns_plant", aspect=1.25, fill=1.0)
def couns_plant(c, color):
    """A tall indoor plant (large paddle leaves on arching stems) in a cream ceramic pot on a small wooden stand."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.62, 0.12, 0.45)
    wood = (0.64, 0.46, 0.28)
    for sx in (-0.17, 0.17):
        c.line(sx, 0.16, sx * 1.3, 0.0, 0.026, wood, 1.0)
    c.rect(0.0, 0.17, 0.44, 0.03, wood, r=0.01, lift=0.15)
    prof = [(0.17, 0.0), (0.21, 0.05), (0.235, 0.16), (0.24, 0.27)]
    _lathe(c._c, 0.0, 0.19, prof, (0.93, 0.90, 0.84), 1.08, 0.66, inner=(0.18, 0.12, 0.08))
    c.rect(0.0, 0.325, 0.50, 0.025, (0.96, 0.93, 0.87), r=0.01, lift=0.1)
    cols = ((0.18, 0.46, 0.28), (0.24, 0.55, 0.32), (0.14, 0.38, 0.24), (0.30, 0.60, 0.36))
    stems = [(-72, 0.62), (-40, 0.78), (-12, 0.92), (14, 0.84), (42, 0.74), (70, 0.60), (-26, 0.50), (30, 0.50)]
    for ang, ln in stems:
        a = math.radians(90 + ang * 0.62)
        tx, ty = 0.0 + math.cos(a) * ln * 0.55, 0.34 + math.sin(a) * ln
        c.line(0.0, 0.34, tx * 0.8, ty * 0.9, 0.012, (0.28, 0.40, 0.20), 1.0)
        _leaf(c._c, tx * 0.8, ty * 0.9, 0.20 + 0.08 * ln, 90 + ang * 0.95, cols[rng.randrange(4)], 0.62)
    for k in range(6):
        _leaf(c._c, rng.uniform(-0.1, 0.1), 0.35, rng.uniform(0.18, 0.28), rng.uniform(40, 140), cols[rng.randrange(4)], 0.6)


@_sp("hlth_couns_bubbles", aspect=1.5, fill=1.0)
def couns_bubbles(c, color):
    """Two overlapping speech bubbles (one solid accent with three dots, one pale with two text-free lines), floating."""
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    acc2 = _pal(color, "accent_light", mix(acc, WHITE, 0.55))
    soft_disc(c, 0.04, 0.12, 0.62, 0.10, BLACK, 0.10, 1.3)
    # back bubble (pale, bottom right)
    c.poly([(0.40, 0.18), (0.55, 0.06), (0.62, 0.22)], mix(acc2, WHITE, 0.5), lift=0.05)
    c.rect(0.30, 0.38, 0.70, 0.40, mix(acc2, WHITE, 0.5), r=0.16, lift=0.10)
    c.rect(0.18, 0.40, 0.30, 0.025, mix(acc, WHITE, 0.3), r=0.01, lift=0.0, alpha=0.8)
    c.rect(0.24, 0.34, 0.42, 0.025, mix(acc, WHITE, 0.45), r=0.01, lift=0.0, alpha=0.7)
    # front bubble (solid accent, top left)
    c.poly([(-0.46, 0.50), (-0.30, 0.64), (-0.52, 0.76)], acc, lift=0.1)
    c.rect(-0.22, 0.88, 0.76, 0.46, acc, r=0.18, lift=0.14)
    for k in range(3):
        c.circle(-0.38 + k * 0.16, 0.88, 0.04, WHITE, lift=0.0, alpha=0.95)
    c.rect(-0.22, 1.06, 0.60, 0.014, WHITE, r=0.007, lift=0.0, alpha=0.35)
    c.glow(-0.2, 0.9, 0.5, acc2, 0.14)


@niche("counselling", "Counselling and therapy practice", subjects=("hlth_couns_sofa",),
       strong=("counselling", "counseling", "counselling centre", "therapy practice", "psychologist", "psychotherapy", "psychotherapist", "mental health",
               "therapist", "couple counselling", "marriage counselling", "online therapy", "mental wellness", "काउंसलिंग", "काउंसलर", "मनोवैज्ञानिक",
               "मानसिक स्वास्थ्य", "थेरेपी", "counsellor", "counselor", "kaunsiling", "manovaigyanik", "therapy session"),
       weak=("stress", "anxiety", "depression", "emotional", "wellbeing", "well-being", "self care", "mindfulness", "session", "tanav", "तनाव", "सलाह", "chat bubbles"),
       accent="#0f8a8f", mood="light", group="wellness",
       avoid=("clinic", "doctor", "dentist", "dental", "hospital", "yoga studio", "spa", "gym", "ayurveda", "physiotherapy", "career coaching"))
def counselling(S):
    P = S.pal
    dark = _dark(S)
    rng = S.rng
    gl = 1.7 if dark else 1.0
    cream = mix(P.wall_top, (0.98, 0.93, 0.84), 0.5) if not dark else P.wall_top
    with S.far():
        S.wall(cream, mix(P.wall_bot, (0.95, 0.88, 0.78), 0.4) if not dark else P.wall_bot, 0.60)
        _blobs(S, 14, -1.0, 0.0, 3.0, 0.60, scale(cream, 0.9), 0.14, 0.14, 0.34)
        # tall window with sheer curtains on the left, a soft daylight bloom
        S.window(0.40, 0.27, 0.40, 0.46, sky_top=(0.80, 0.92, 0.98), sky_bot=(0.97, 0.99, 1.0), frame=scale(P.paper, 0.96), bars=True)
        for sx, w in ((0.14, 0.12), (0.66, 0.12)):
            S.gradient_rect(sx - w / 2, 0.0, sx + w / 2, 0.52, mix(P.paper, P.accent_light, 0.25), mix(P.paper, P.accent_light, 0.05), alpha=0.95)
        S.glow(0.45, 0.28, 0.85, P.light, 0.32 * gl, 1.6)
        # framed abstract art (arcs and circles only) above the sofa, and a floating shelf with a vase
        S.rect(1.38, 0.22, 0.56, 0.34, mix(WHITE, P.wall_top, 0.2) if not dark else scale(P.wall_top, 1.8), r=0.004, lift=0.0)
        S.circle(1.30, 0.26, 0.08, mix(P.accent, WHITE, 0.30), lift=0.0)
        S.circle(1.50, 0.20, 0.10, (0.93, 0.72, 0.42), lift=0.0, alpha=0.9)
        S.rect(1.40, 0.31, 0.46, 0.02, mix(P.accent_dark, P.paper, 0.4), lift=0.0, alpha=0.85)
        S.rect(1.95, 0.30, 0.34, 0.014, scale(P.surface, 0.9), lift=0.0)
        S.ellipse(1.90, 0.255, 0.028, 0.045, (0.88, 0.78, 0.66), lift=0.1)
        S.ellipse(2.00, 0.268, 0.022, 0.032, mix(P.accent, WHITE, 0.4), lift=0.1)
        S.bokeh(8, 0.0, 0.08, 2.0, 0.5, [(1.0, 0.88, 0.6), (1.0, 0.95, 0.8), P.accent_light], 0.012, 0.04, 0.28 * gl)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # floor: pale boards, a window light patch, a round rug under the seating
    S.rect(1.0, 0.60, 7.0, 0.008, scale(P.floor_top, 0.55), lift=0.0)
    for k in range(7):
        S.rect(1.0, 0.66 + k * 0.07, 7.0, 0.003, scale(P.floor_top, 0.78), lift=0.0, alpha=0.5)
    _spoly_stage(S, [(0.18, 0.64), (0.62, 0.64), (1.30, 1.4), (0.40, 1.4)], P.light, 0.10 * gl)
    rug = mix(P.accent_light, (0.96, 0.90, 0.80), 0.4)
    _sell(S, 1.22, 0.99, 0.86, 0.17, scale(rug, 0.72))
    _sell(S, 1.22, 0.985, 0.82, 0.155, rug)
    _sell(S, 1.22, 0.985, 0.62, 0.115, mix(rug, P.accent, 0.18), 0.65)
    _sell(S, 1.22, 0.985, 0.40, 0.07, rug, 0.7)
    S.put("hlth_couns_lamp", 0.76, 0.86, 0.62, color=P, shadow_w=0.26)
    S.put("hlth_couns_plant", 1.52, 0.84, 0.54, color=P, shadow_w=0.4)
    S.put("hlth_couns_sofa", 1.14, 0.96, 0.48, color=P, subject=True, shadow_w=0.7, shadow_alpha=0.12)
    S.put("hlth_couns_table", 1.50, 1.05, 0.36, color=P, shadow_w=0.34)
    S.put("hlth_couns_bubbles", 1.00, 0.36, 0.17, color=P, shadow=False)
    S.focus("detail", 1.45, 0.90)
    if dark:
        S.glow(0.76, 0.40, 0.6, (1.0, 0.7, 0.35), 0.35, 1.8)
    with S.near():
        S.circle(0.40, 1.08, 0.06, (1.0, 0.85, 0.5), alpha=0.30, lift=0)
        S.circle(0.66, 0.36, 0.03, (1.0, 0.9, 0.6), alpha=0.25, lift=0)


# ====================================================================================== DIETITIAN / NUTRITIONIST
def _fruit(c, u, v, r, col, leaf=None):
    """A round fruit / tomato: dark base, lit body, small highlight, optional green calyx."""
    c.ellipse(u, v, r, r * 0.94, scale(col, 0.70), lift=0.0)
    c.ellipse(u - r * 0.10, v + r * 0.08, r * 0.84, r * 0.80, col, lift=0.14)
    c.ellipse(u - r * 0.36, v + r * 0.36, r * 0.26, r * 0.15, mix(col, WHITE, 0.65), lift=0.0, alpha=0.8, angle=30)
    if leaf:
        c.ellipse(u, v + r * 0.86, r * 0.30, r * 0.10, leaf, lift=0.0)


def _broc(c, u, v, s, rng):
    """A broccoli floret: pale stalk and a crown of dark green bumps with lighter flecks."""
    c.poly([(u - s * 0.10, v), (u + s * 0.10, v), (u + s * 0.06, v + s * 0.50), (u - s * 0.06, v + s * 0.50)], (0.60, 0.74, 0.40), lift=0.2)
    for dx, dy, rr in ((-0.30, 0.62, 0.30), (0.30, 0.62, 0.30), (0.0, 0.84, 0.36), (-0.12, 0.60, 0.30), (0.14, 0.70, 0.30)):
        c.ellipse(u + dx * s, v + dy * s, rr * s, rr * s * 0.90, (0.13 + 0.05 * rng.random(), 0.42 + 0.06 * rng.random(), 0.18), lift=0.2)
    for _ in range(7):
        c.circle(u + rng.uniform(-0.4, 0.4) * s, v + rng.uniform(0.55, 1.05) * s, s * 0.04, (0.40, 0.68, 0.30), lift=0.0, alpha=0.8)


def _carrot(c, u, v, ln, ang, w=0.05):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(u, v + w), (u + ln * ca, v + ln * sa), (u, v - w)]
    c.poly([(u + x * 1.0, v + y) for x, y in ((0, w), (ln * ca, ln * sa + 0.002), (0, -w))], (0.94, 0.50, 0.12), lift=0.2)
    for k in (0.25, 0.5, 0.7):
        c.line(u + ln * ca * k, v + ln * sa * k - w * (1 - k) * 0.7, u + ln * ca * k, v + ln * sa * k + w * (1 - k) * 0.7, 0.006, (0.74, 0.34, 0.06), 0.7)
    for k in range(3):
        c.line(u, v, u - 0.05 - k * 0.012, v + (k - 1) * 0.05, 0.012, (0.30, 0.58, 0.22), 1.0)


@_sp("hlth_nut_plate", aspect=2.6, fill=0.58)
def nut_plate(c, color):
    """A balanced plate in the plate-method layout: half colourful vegetables (broccoli, carrot, tomato), a quarter whole-wheat rotis,
    a quarter grilled paneer cubes, with a small bowl of dal and a fork and spoon."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.6, 0.30, 0.5)
    cx, cy, a, b = 0.0, 0.24, 0.74, 0.30
    # plate: rim thickness, rim, well
    c.ellipse(cx, cy - 0.04, a, b, (0.80, 0.82, 0.84), lift=0.0)
    c.ellipse(cx, cy, a, b, (0.98, 0.98, 0.97), lift=0.10)
    c.ellipse(cx, cy + 0.006, a * 0.97, b * 0.97, (0.93, 0.94, 0.94), lift=0.0)
    c.ellipse(cx, cy + 0.01, a * 0.78, b * 0.76, (0.99, 0.99, 0.98), lift=0.08)
    c.ellipse(cx, cy + 0.014, a * 0.78, b * 0.76, mix(acc, WHITE, 0.55), lift=0.0, alpha=0.10)

    def sector(a0, a1, rr, col, lift=0.1, alpha=1.0):
        pts = [(cx, cy + 0.012)]
        for k in range(15):
            t = math.radians(a0 + (a1 - a0) * k / 14.0)
            pts.append((cx + a * rr * math.cos(t), cy + 0.012 + b * rr * 0.98 * math.sin(t)))
        c.poly(pts, col, lift=lift, alpha=alpha)
    # vegetables: left half. a base of leafy greens then florets, carrot rounds and tomato
    sector(92, 268, 0.70, (0.30, 0.55, 0.22), 0.14)
    for _ in range(11):
        t = rng.uniform(math.radians(100), math.radians(260))
        rr = math.sqrt(rng.random()) * 0.60
        _leaf(c._c, cx + a * rr * math.cos(t), cy + 0.03 + b * rr * math.sin(t), 0.10, rng.uniform(0, 360), (0.22 + 0.15 * rng.random(), 0.50 + 0.10 * rng.random(), 0.20), 0.5, vein=False)
    for (dx, dy, sc_) in ((-0.40, 0.13, 0.20), (-0.18, 0.18, 0.18), (-0.54, 0.20, 0.16)):
        _broc(c, cx + dx, cy + dy - 0.07, sc_, rng)
    for k in range(7):
        t = math.radians(150 + k * 14)
        u_, v_ = cx + a * 0.40 * math.cos(t) - 0.10, cy + 0.02 + b * 0.40 * math.sin(t)
        c.ellipse(u_, v_, 0.044, 0.020, (0.95, 0.52, 0.12), lift=0.2)
        c.ellipse(u_, v_ + 0.003, 0.020, 0.009, (0.99, 0.74, 0.34), lift=0.0)
    for (dx, dy) in ((-0.20, -0.02), (-0.32, -0.06)):
        _fruit(c, cx + dx, cy + dy + 0.02, 0.048, (0.88, 0.16, 0.12), (0.30, 0.55, 0.22))
    # whole-wheat rotis (top right quarter), stacked
    sector(268, 358, 0.70, (0.97, 0.97, 0.96), 0.0, 0.0)
    for k, (dx, dy) in enumerate(((0.28, 0.16), (0.30, 0.20))):
        c.ellipse(dx, cy + dy - 0.07 + k * 0.025, 0.21, 0.080, (0.82, 0.62, 0.32) if k == 0 else (0.94, 0.78, 0.46), lift=0.18)
    for _ in range(9):
        c.circle(0.28 + rng.uniform(-0.14, 0.14), cy + 0.19 + rng.uniform(-0.02, 0.025), rng.uniform(0.008, 0.016), (0.50, 0.30, 0.12), lift=0.0, alpha=0.6)
    c.ellipse(0.26, cy + 0.205, 0.12, 0.034, (1.0, 0.90, 0.62), lift=0.0, alpha=0.35)
    # grilled paneer cubes (bottom right quarter)
    for (dx, dy) in ((0.22, -0.10), (0.42, -0.06), (0.34, -0.15)):
        u_, v_ = cx + dx, cy + dy + 0.03
        c.poly([(u_ - 0.07, v_), (u_ + 0.07, v_), (u_ + 0.07, v_ + 0.07), (u_ - 0.07, v_ + 0.07)], (0.95, 0.84, 0.58), lift=0.16)
        c.poly([(u_ - 0.07, v_ + 0.07), (u_ + 0.07, v_ + 0.07), (u_ + 0.10, v_ + 0.10), (u_ - 0.04, v_ + 0.10)], (1.0, 0.93, 0.72), lift=0.1)
        c.poly([(u_ + 0.07, v_), (u_ + 0.10, v_ + 0.03), (u_ + 0.10, v_ + 0.10), (u_ + 0.07, v_ + 0.07)], (0.78, 0.62, 0.38), lift=0.0)
        for k in range(3):
            c.line(u_ - 0.05, v_ + 0.015 + k * 0.022, u_ + 0.05, v_ + 0.015 + k * 0.022, 0.006, (0.45, 0.26, 0.10), 0.7)
    for _ in range(6):
        _leaf(c._c, 0.30 + rng.uniform(-0.10, 0.18), cy - 0.02 + rng.uniform(-0.05, 0.05), 0.05, rng.uniform(0, 360), (0.28, 0.56, 0.24), 0.5, vein=False)
    # dividers and rim light
    c.ellipse(cx, cy + 0.012, a * 0.78, b * 0.76, WHITE, lift=0.0, alpha=0.0)
    soft_disc(c._c, -0.30, cy + 0.20, 0.30, 0.05, WHITE, 0.30, 1.2, add=True)
    # dal bowl and cutlery at the right
    _lathe(c._c, 0.80, 0.03, [(0.07, 0.0), (0.12, 0.03), (0.14, 0.09)], (0.97, 0.97, 0.95), 1.05, 0.66, inner=(0.94, 0.74, 0.24), rim=True, rimcol=(0.99, 0.99, 0.98))
    c.ellipse(0.80, 0.125, 0.115, 0.034, (0.96, 0.76, 0.22), lift=0.1)
    c.ellipse(0.78, 0.13, 0.05, 0.012, (1.0, 0.90, 0.55), lift=0.0, alpha=0.6)
    c.line(-0.86, 0.07, -0.74, 0.27, 0.014, (0.80, 0.82, 0.86), 1.0)
    c.ellipse(-0.73, 0.30, 0.025, 0.045, (0.88, 0.90, 0.94), lift=0.1, angle=-20)


@_sp("hlth_nut_basket", aspect=1.34, fill=1.0)
def nut_basket(c, color):
    """A wicker basket heaped with fresh vegetables: carrots with green tops, tomatoes, a yellow pepper, broccoli, leafy greens."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.2, 0.20, 0.5)
    wick = (0.72, 0.52, 0.30)
    # back greens and carrots first
    for k in range(9):
        _leaf(c._c, rng.uniform(-0.3, 0.3), 0.40, rng.uniform(0.28, 0.42), rng.uniform(55, 125), (0.20 + 0.12 * rng.random(), 0.52 + 0.10 * rng.random(), 0.22), 0.55)
    for k, (u_, ang) in enumerate(((-0.32, 112), (-0.14, 100), (0.06, 84), (0.28, 70))):
        _carrot(c, u_, 0.44, 0.50, ang, 0.055)
    _broc(c, 0.42, 0.40, 0.30, rng)
    # basket body: rounded trapezoid with a weave, a rim and a handle
    body = [(-0.52, 0.42), (0.52, 0.42), (0.44, 0.02), (-0.44, 0.02)]
    _vpoly(c._c, body, scale(wick, 1.1), scale(wick, 0.70), smooth=0)
    for k in range(6):
        v = 0.07 + k * 0.058
        c.rect(0.0, v, 0.98 - k * 0.0, 0.012, scale(wick, 0.62), lift=0.0, alpha=0.55)
    for k in range(13):
        u_ = -0.46 + k * 0.077
        c.line(u_, 0.04, u_ * 1.07, 0.40, 0.012, scale(wick, 0.70 if k % 2 else 1.18), 0.55)
    c.rect(0.0, 0.43, 1.10, 0.05, scale(wick, 1.12), r=0.02, lift=0.15)
    c.rect(0.0, 0.452, 1.10, 0.012, WHITE, lift=0.0, alpha=0.25)
    # front produce sitting on the rim
    _fruit(c, -0.30, 0.52, 0.12, (0.86, 0.14, 0.10), (0.28, 0.56, 0.22))
    _fruit(c, -0.06, 0.50, 0.11, (0.92, 0.22, 0.12), (0.28, 0.56, 0.22))
    _fruit(c, 0.20, 0.52, 0.12, (0.97, 0.78, 0.14))
    c.rect(0.20, 0.66, 0.02, 0.05, (0.40, 0.58, 0.20), lift=0.0)
    _fruit(c, 0.44, 0.50, 0.10, (0.82, 0.22, 0.14), (0.28, 0.56, 0.22))
    c.ellipse(-0.45, 0.56, 0.05, 0.12, (0.30, 0.55, 0.22), lift=0.18, angle=60)                 # a cucumber
    c.poly([(-0.52, 0.50), (-0.34, 0.52), (-0.38, 0.58), (-0.50, 0.57)], (0.38, 0.62, 0.26), lift=0.1)


@_sp("hlth_nut_prep", aspect=2.75, fill=0.66)
def nut_prep(c, color):
    """Three glass meal-prep boxes packed with coloured meals (rice and beans, chicken and greens, fruit) with a lid leaning behind."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.6, 0.30, 0.5)
    glass = (0.82, 0.92, 0.95)
    # lid leaning at the back
    c.rect(0.50, 0.40, 0.66, 0.50, glass, r=0.05, lift=0.06, alpha=0.5)
    c.rect(0.50, 0.40, 0.58, 0.42, scale(glass, 1.1), r=0.04, lift=0.0, alpha=0.30)
    c.rect(0.50, 0.66, 0.66, 0.05, acc, r=0.02, lift=0.1)
    c.rect(0.28, 0.40, 0.03, 0.4, WHITE, lift=0.0, alpha=0.5)
    menus = (((0.98, 0.96, 0.90), (0.50, 0.28, 0.14), (0.30, 0.58, 0.22)), ((0.92, 0.72, 0.38), (0.30, 0.58, 0.22), (0.90, 0.30, 0.16)), ((0.92, 0.22, 0.30), (0.98, 0.84, 0.30), (0.52, 0.32, 0.64)))
    for i, (u_, w) in enumerate(((-0.52, 0.56), (0.02, 0.56), (0.56, 0.56))):
        v0, h, d = 0.04, 0.26, 0.20
        ox, oy = d * 0.5, d * 0.34
        # glass walls, open top showing the food
        c.poly([(u_ - w / 2, v0), (u_ + w / 2, v0), (u_ + w / 2, v0 + h), (u_ - w / 2, v0 + h)], scale(glass, 1.0), lift=0.05, alpha=0.78)
        c.poly([(u_ + w / 2, v0), (u_ + w / 2 + ox, v0 + oy), (u_ + w / 2 + ox, v0 + h + oy), (u_ + w / 2, v0 + h)], scale(glass, 0.82), lift=0.0, alpha=0.8)
        c.poly([(u_ - w / 2, v0 + h), (u_ + w / 2, v0 + h), (u_ + w / 2 + ox, v0 + h + oy), (u_ - w / 2 + ox, v0 + h + oy)], (0.96, 0.98, 0.98), lift=0.0, alpha=0.9)
        m1, m2, m3 = menus[i]
        fx, fy = u_ + ox * 0.5, v0 + h + oy * 0.5
        c.ellipse(fx - 0.10, fy + 0.002, 0.13, 0.060, m1, lift=0.2)
        c.ellipse(fx + 0.10, fy + 0.006, 0.12, 0.056, m2, lift=0.2)
        c.ellipse(fx + 0.0, fy + 0.028, 0.10, 0.042, m3, lift=0.2)
        for _ in range(8):
            c.circle(fx + rng.uniform(-0.2, 0.2), fy + rng.uniform(-0.01, 0.05), 0.012, mix(m3, WHITE, 0.3), lift=0.1)
        c.rect(u_, v0 + 0.07, w * 0.96, h * 0.52, mix(m1, m2, 0.4), lift=0.0, alpha=0.42)
        c.rect(u_ - w * 0.40, v0 + h * 0.5, 0.025, h * 0.86, WHITE, lift=0.0, alpha=0.55)
        c.rect(u_, v0 + 0.003, w, 0.012, scale(glass, 0.55), lift=0.0)
        c.rect(u_, v0 + h + 0.004, w, 0.016, (0.55, 0.62, 0.66), lift=0.0, alpha=0.8)
        c.rect(u_, v0 + h * 0.48, 0.11, 0.07, acc, r=0.01, lift=0.1, alpha=0.9)


@_sp("hlth_nut_scale", aspect=3.0, fill=0.46)
def nut_scale(c, color):
    """A kitchen scale carrying a glass bowl of almonds, a coiled measuring tape and an apple: the portion-guide corner."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 1.2, 0.24, 0.5)
    body = (0.96, 0.96, 0.95)
    # scale base with a dark display and bars instead of digits, a platform on top
    ox, oy = _box3d(c, -0.18, 0.02, 0.78, 0.17, 0.28, body, scale(body, 1.03), scale(body, 0.68))
    c.rect(-0.18, 0.10, 0.34, 0.07, (0.10, 0.15, 0.18), r=0.012, lift=0.0)
    for k in range(5):
        c.rect(-0.28 + k * 0.05, 0.10, 0.026, 0.040, (0.45, 1.0, 0.75), lift=0.0, alpha=0.9)
    c.circle(0.07, 0.10, 0.017, acc, lift=0.2)
    c.circle(0.13, 0.10, 0.017, (0.85, 0.85, 0.88), lift=0.2)
    c.ellipse(-0.18 + ox * 0.5, 0.19 + oy * 0.5 + 0.006, 0.34, 0.082, scale(body, 0.78), lift=0.0)
    c.ellipse(-0.18 + ox * 0.5, 0.19 + oy * 0.5 + 0.014, 0.33, 0.076, (0.82, 0.86, 0.88), lift=0.12)
    # glass bowl of almonds on the platform
    bu, bv = -0.18 + ox * 0.5, 0.22 + oy * 0.5
    _lathe(c._c, bu, bv, [(0.08, 0.0), (0.16, 0.05), (0.21, 0.13)], (0.86, 0.94, 0.96), 1.1, 0.66, inner=(0.60, 0.48, 0.34), rimcol=(0.94, 0.98, 0.99))
    for k in range(13):
        c.ellipse(bu + rng.uniform(-0.15, 0.15), bv + 0.14 + rng.uniform(-0.01, 0.045), 0.026, 0.018, (0.66 + 0.1 * rng.random(), 0.42, 0.22), lift=0.2, angle=rng.uniform(-40, 40))
    c.rect(bu - 0.13, bv + 0.07, 0.012, 0.07, WHITE, lift=0.0, alpha=0.5)
    # coiled tape in front
    tape = (0.98, 0.86, 0.30)
    c.ellipse(0.34, 0.06, 0.20, 0.060, scale(tape, 0.66), lift=0.0)
    c.ellipse(0.34, 0.085, 0.20, 0.060, tape, lift=0.16)
    c.ellipse(0.34, 0.088, 0.13, 0.038, scale(tape, 0.55), lift=0.0)
    c.ellipse(0.34, 0.094, 0.095, 0.026, (0.92, 0.90, 0.86), lift=0.0)
    for k in range(18):
        t = math.radians(10 + k * 20)
        c.line(0.34 + 0.15 * math.cos(t), 0.085 + 0.045 * math.sin(t), 0.34 + 0.19 * math.cos(t), 0.085 + 0.057 * math.sin(t), 0.005, scale(tape, 0.35), 0.8)
    c.poly([(0.52, 0.07), (0.66, 0.04), (0.67, 0.07), (0.53, 0.10)], tape, lift=0.1)
    # an apple
    _fruit(c, 0.64, 0.13, 0.11, (0.84, 0.16, 0.16), (0.32, 0.56, 0.22))


@_sp("hlth_nut_card", aspect=0.78, fill=1.0)
def nut_card(c, color):
    """A folded desk card (portion guide) standing like a tent: a header band, a round plate diagram split into vegetable / grain /
    protein wedges, and a row of icon dots, with no writing."""
    rng = c.rng
    acc = _pal(color, "accent", (0.06, 0.54, 0.56))
    ao(c, 0.0, 0.0, 0.8, 0.12, 0.45)
    paper = (0.99, 0.98, 0.95)
    # back panel visible at the right, front panel in the middle
    c.poly([(0.40, 0.02), (0.52, 0.06), (0.50, 0.96), (0.38, 0.99)], scale(paper, 0.76), lift=0.0)
    _vpoly(c._c, [(-0.44, 0.02), (0.40, 0.02), (0.38, 0.99), (-0.44, 0.97)], paper, scale(paper, 0.90), alpha=1.0)
    c.rect(-0.02, 0.88, 0.80, 0.14, acc, lift=0.08)
    c.circle(-0.30, 0.88, 0.035, WHITE, lift=0.0, alpha=0.9)
    c.rect(0.12, 0.90, 0.36, 0.022, WHITE, r=0.01, lift=0.0, alpha=0.8)
    c.rect(0.06, 0.86, 0.24, 0.015, WHITE, r=0.007, lift=0.0, alpha=0.5)
    # plate diagram
    pu, pv, pr = -0.02, 0.52, 0.30
    c.circle(pu, pv, pr + 0.02, (0.93, 0.93, 0.92), lift=0.0)
    for (a0, a1, col) in ((90, 270, (0.33, 0.66, 0.30)), (270, 360, (0.93, 0.76, 0.40)), (0, 90, (0.82, 0.38, 0.22))):
        pts = [(pu, pv)] + [(pu + pr * math.cos(math.radians(a0 + (a1 - a0) * k / 14.0)), pv + pr * math.sin(math.radians(a0 + (a1 - a0) * k / 14.0))) for k in range(15)]
        c.poly(pts, col, lift=0.12)
    for ang in (90, 270, 0):
        c.line(pu, pv, pu + pr * math.cos(math.radians(ang)), pv + pr * math.sin(math.radians(ang)), 0.012, WHITE, 0.95)
    c.circle(pu - 0.12, pv + 0.04, 0.045, (0.2, 0.52, 0.2), lift=0.2, alpha=0.9)
    c.circle(pu - 0.14, pv - 0.10, 0.04, (0.95, 0.5, 0.15), lift=0.2, alpha=0.9)
    c.circle(pu + 0.14, pv + 0.14, 0.045, (0.98, 0.84, 0.5), lift=0.2, alpha=0.9)
    # icon row: water drop, apple, bowl (shapes only)
    for k, col in enumerate(((0.25, 0.55, 0.85), (0.86, 0.18, 0.16), (0.94, 0.72, 0.30))):
        c.circle(-0.26 + k * 0.24, 0.16, 0.052, col, lift=0.2)
        c.rect(-0.26 + k * 0.24, 0.06, 0.12, 0.012, scale(paper, 0.7), lift=0.0, alpha=0.9)
    soft_disc(c, -0.30, 0.55, 0.05, 0.4, WHITE, 0.12, 1.2, add=True)


@niche("nutritionist", "Dietitian and nutritionist", subjects=("hlth_nut_plate",),
       strong=("dietitian", "dietician", "nutritionist", "diet clinic", "diet consultant", "nutrition clinic", "diet plan", "weight loss diet", "diet counselling",
               "clinical nutrition", "meal planning", "sports nutrition", "diet consultation", "डाइटिशियन", "आहार विशेषज्ञ", "न्यूट्रिशनिस्ट", "डाइट प्लान", "पोषण विशेषज्ञ",
               "diet chart", "dietitian ke pass", "aahar", "vajan ghatane ka diet"),
       weak=("diet", "nutrition", "healthy eating", "calories", "balanced meal", "weight management", "portion", "pcos diet", "meal prep", "wellness coaching", "आहार", "पोषण", "डाइट"),
       accent="#0f8a8f", mood="light", group="wellness",
       avoid=("doctor", "clinic", "dental", "dentist", "hospital", "डॉक्टर", "ayurveda", "restaurant", "cafe", "catering", "tiffin", "juice bar", "gym", "yoga"))
def nutritionist(S):
    P = S.pal
    dark = _dark(S)
    rng = S.rng
    gl = 1.7 if dark else 1.0
    sage = mix(P.accent_light, (0.90, 0.95, 0.86), 0.45)
    with S.far():
        S.wall(mix(P.wall_top, sage, 0.30) if not dark else P.wall_top, mix(P.wall_bot, sage, 0.45) if not dark else P.wall_bot, 0.56)
        # soft sage subway tiles up to the counter, open shelves with jars of pulses and grains, a window on the left
        S.rect(1.0, 0.45, 7.0, 0.22, mix(sage, WHITE, 0.45) if not dark else scale(P.wall_bot, 1.4), lift=0.0)
        for k in range(22):
            S.rect(-0.9 + k * 0.17, 0.45, 0.004, 0.22, scale(sage, 0.86), lift=0.0, alpha=0.7)
        for k in range(3):
            S.rect(1.0, 0.36 + k * 0.07, 7.0, 0.004, scale(sage, 0.86), lift=0.0, alpha=0.7)
        S.window(0.36, 0.22, 0.42, 0.36, sky_top=(0.80, 0.93, 0.98), sky_bot=(0.97, 1.0, 1.0), frame=scale(P.paper, 0.97))
        S.glow(0.40, 0.22, 0.9, P.light, 0.30 * gl, 1.6)
        S.rect(1.50, 0.26, 1.15, 0.016, scale(P.surface, 0.85), lift=0.0)
        S.rect(1.50, 0.12, 1.15, 0.016, scale(P.surface, 0.85), lift=0.0)
        jar = [(0.94, 0.78, 0.32), (0.97, 0.95, 0.88), (0.78, 0.28, 0.20), (0.62, 0.42, 0.22), (0.45, 0.62, 0.32), (0.95, 0.60, 0.20)]
        for row, vb in ((0, 0.255), (1, 0.115)):
            for k in range(6):
                hh = 0.09 + 0.02 * ((k + row) % 3)
                S.rect(1.04 + k * 0.19, vb - hh / 2, 0.12, hh, jar[(k + row * 2) % 6], r=0.016, lift=0.14)
                S.rect(1.04 + k * 0.19, vb - hh - 0.012, 0.13, 0.024, scale(P.surface, 0.9), r=0.006, lift=0.1)
        # herbs hanging in the window
        for u_, ln in ((0.20, 0.15), (0.52, 0.12)):
            S.line(u_, 0.0, u_, ln, 0.004, (0.3, 0.4, 0.25), 0.8)
            S.ellipse(u_, ln + 0.03, 0.04, 0.05, (0.30, 0.55, 0.28), lift=0.1)
        S.bokeh(8, 0.0, 0.08, 2.0, 0.5, [(0.55, 0.85, 0.40), (1.0, 0.85, 0.35), (1.0, 0.95, 0.8)], 0.012, 0.04, 0.28 * gl)
        S.floor(0.56, P.floor_top, P.floor_bot)
    # counter: pale wood with a white linen runner under the plates
    top = mix(P.surface, (0.96, 0.90, 0.78), 0.55) if not dark else P.surface
    S.floor(0.56, scale(top, 1.04), scale(top, 0.80))
    S.rect(1.0, 0.56, 7.0, 0.012, scale(top, 0.55), lift=0.0)
    for k in range(6):
        S.rect(1.0, 0.64 + k * 0.08, 7.0, 0.003, scale(top, 0.82), lift=0.0, alpha=0.5)
    linen = (0.97, 0.95, 0.90) if not dark else (0.55, 0.55, 0.52)
    _spoly_stage(S, [(0.55, 0.72), (1.85, 0.72), (2.10, 1.16), (0.30, 1.16)], linen, 0.96)
    S.put("hlth_nut_card", 0.86, 0.74, 0.42, color=P, shadow_w=0.3)
    S.put("hlth_nut_basket", 1.56, 0.74, 0.34, color=P, shadow_w=0.5)
    S.put("hlth_nut_plate", 1.20, 0.97, 0.36, color=P, subject=True, shadow_w=0.8)
    S.put("hlth_nut_prep", 0.82, 1.08, 0.18, color=P, shadow_w=0.46)
    S.put("hlth_nut_scale", 1.56, 1.08, 0.15, color=P, shadow_w=0.4)
    S.focus("detail", 1.16, 0.88)
    with S.near():
        S.circle(0.45, 1.08, 0.06, (0.7, 0.9, 0.5), alpha=0.28, lift=0)
        S.circle(1.95, 0.62, 0.05, (1.0, 0.85, 0.4), alpha=0.24, lift=0)


# ====================================================================================== ANIMAL WELFARE AND RESCUE
FUR = (0.86, 0.62, 0.36)
FUR_DK = (0.56, 0.35, 0.19)
FUR_LT = (0.98, 0.90, 0.76)


@_sp("hlth_aw_pup", aspect=1.0, fill=1.0)
def aw_pup(c, color):
    """A rescued puppy sitting on a folded blanket: floppy ears, white chest, bright eyes, a red collar with a gold tag
    and a blue vet bandage wrapped round one front leg."""
    rng = c.rng
    acc = _pal(color, "accent", (0.88, 0.48, 0.12))
    acc2 = _pal(color, "accent_light", mix(acc, WHITE, 0.55))
    ao(c, 0.0, 0.0, 1.0, 0.16, 0.5)
    # folded blanket under the pup
    blk = mix(acc2, (0.95, 0.90, 0.82), 0.3)
    c.ellipse(0.0, 0.040, 0.52, 0.092, scale(blk, 0.66), lift=0.0)
    c.ellipse(0.0, 0.058, 0.50, 0.082, blk, lift=0.10)
    for k in range(5):
        c.line(-0.38 + k * 0.19, 0.03, -0.34 + k * 0.19, 0.095, 0.020, mix(acc, blk, 0.2) if k % 2 == 0 else (0.98, 0.95, 0.88), 0.85)
    # haunches, body, chest
    c.ellipse(-0.24, 0.18, 0.18, 0.15, scale(FUR, 0.86), lift=0.12)
    c.ellipse(0.25, 0.18, 0.18, 0.15, scale(FUR, 0.78), lift=0.12)
    c.line(0.30, 0.15, 0.44, 0.10, 0.07, scale(FUR, 0.8), 1.0)                                  # tail
    _vpoly(c._c, [(-0.25, 0.12), (-0.27, 0.40), (-0.19, 0.64), (0.19, 0.64), (0.27, 0.40), (0.25, 0.12)], scale(FUR, 1.05), scale(FUR, 0.78), smooth=2)
    c.ellipse(0.0, 0.38, 0.125, 0.21, FUR_LT, lift=0.10)
    soft_disc(c._c, 0.19, 0.26, 0.14, 0.24, BLACK, 0.18, 1.3)
    # front legs, paws; bandage on the right leg
    for sx in (-0.11, 0.11):
        c.rect(sx, 0.20, 0.105, 0.33, scale(FUR_LT, 0.97) if sx < 0 else FUR_LT, r=0.045, lift=0.10)
        c.ellipse(sx, 0.050, 0.068, 0.040, FUR_LT, lift=0.08)
        for k in range(3):
            c.line(sx - 0.03 + k * 0.03, 0.035, sx - 0.03 + k * 0.03, 0.055, 0.004, scale(FUR_DK, 0.9), 0.6)
    for k in range(5):
        v = 0.12 + k * 0.045
        c.rect(0.11, v, 0.122, 0.040, (0.58, 0.78, 0.92) if k % 2 == 0 else (0.94, 0.96, 0.98), r=0.01, lift=0.12)
    c.rect(0.11, 0.33, 0.130, 0.018, (0.96, 0.96, 0.98), lift=0.0)
    # head
    c.ellipse(-0.205, 0.78, 0.085, 0.165, FUR_DK, lift=0.12, angle=-14)
    c.ellipse(0.205, 0.78, 0.085, 0.165, scale(FUR_DK, 0.9), lift=0.12, angle=14)
    c.circle(0.0, 0.79, 0.215, scale(FUR, 1.08), lift=0.14)
    c.ellipse(0.0, 0.84, 0.10, 0.05, FUR_LT, lift=0.0, alpha=0.35)
    c.ellipse(0.0, 0.715, 0.125, 0.095, FUR_LT, lift=0.10)
    c.ellipse(0.0, 0.752, 0.042, 0.027, (0.10, 0.08, 0.08), lift=0.2)
    c.ellipse(-0.012, 0.760, 0.014, 0.007, WHITE, lift=0.0, alpha=0.8)
    c.line(0.0, 0.738, 0.0, 0.705, 0.008, (0.30, 0.20, 0.16), 0.8)
    c.line(0.0, 0.705, -0.04, 0.688, 0.007, (0.30, 0.20, 0.16), 0.8)
    c.line(0.0, 0.705, 0.04, 0.688, 0.007, (0.30, 0.20, 0.16), 0.8)
    c.ellipse(0.012, 0.665, 0.027, 0.034, (0.92, 0.42, 0.46), lift=0.12)
    for sx in (-0.085, 0.085):
        c.ellipse(sx, 0.83, 0.034, 0.038, (0.09, 0.06, 0.05), lift=0.0)
        c.circle(sx - 0.011, 0.842, 0.011, WHITE, lift=0.0)
        c.ellipse(sx, 0.878, 0.034, 0.016, FUR_LT, lift=0.0, alpha=0.8)
    # collar and tag
    c.ellipse(0.0, 0.595, 0.165, 0.040, mix(acc, (0.8, 0.1, 0.1), 0.5), lift=0.14)
    c.circle(0.0, 0.545, 0.030, (0.94, 0.76, 0.28), lift=0.2)
    soft_disc(c._c, 0.0, 0.60, 0.20, 0.05, BLACK, 0.22, 1.3)
    soft_disc(c._c, -0.08, 0.90, 0.13, 0.06, WHITE, 0.22, 1.2, add=True)


@_sp("hlth_aw_bowls", aspect=4.2, fill=0.40)
def aw_bowls(c, color):
    """Two steel feeding bowls: one heaped with kibble, one with clean water."""
    rng = c.rng
    steel = (0.78, 0.80, 0.84)
    ao(c, 0.0, 0.0, 1.9, 0.32, 0.5)
    for u, kind in ((-0.46, "food"), (0.44, "water")):
        prof = [(0.17, 0.0), (0.28, 0.06), (0.38, 0.19), (0.40, 0.24)]
        _lathe(c._c, u, 0.04, prof, steel, 1.15, 0.58, inner=(0.30, 0.32, 0.36), rimcol=scale(steel, 1.18), kind="metal")
        if kind == "food":
            c.ellipse(u, 0.295, 0.34, 0.10, (0.50, 0.32, 0.16), lift=0.12)
            for _ in range(26):
                c.ellipse(u + rng.uniform(-0.28, 0.28), 0.30 + rng.uniform(-0.01, 0.07), 0.026, 0.018, (0.46 + 0.18 * rng.random(), 0.28 + 0.1 * rng.random(), 0.12), lift=0.2, angle=rng.uniform(0, 180))
        else:
            c.ellipse(u, 0.285, 0.34, 0.094, (0.52, 0.72, 0.86), lift=0.1)
            c.ellipse(u - 0.07, 0.295, 0.14, 0.03, (0.88, 0.96, 1.0), lift=0.0, alpha=0.6)
            c.line(u + 0.10, 0.30, u + 0.20, 0.285, 0.008, WHITE, 0.6)
        c.rect(u - 0.30, 0.17, 0.02, 0.12, WHITE, lift=0.0, alpha=0.45)
    # a few kibble bits spilled
    for k in range(5):
        c.ellipse(-0.05 + k * 0.025 + rng.uniform(-0.02, 0.02), 0.035 + rng.uniform(0, 0.03), 0.018, 0.012, (0.5, 0.3, 0.14), lift=0.2)


@_sp("hlth_aw_vetkit", aspect=2.9, fill=0.50)
def aw_vetkit(c, color):
    """A rescue first-aid kit: an open white case with an orange band, a bandage roll, a vaccine vial and a syringe laid in front."""
    rng = c.rng
    acc = _pal(color, "accent", (0.88, 0.48, 0.12))
    ao(c, 0.0, 0.0, 1.7, 0.30, 0.5)
    case = (0.96, 0.96, 0.94)
    ox, oy = _box3d(c, -0.30, 0.04, 0.78, 0.26, 0.30, case, scale(case, 1.02), scale(case, 0.68))
    c.rect(-0.30, 0.04 + 0.26 * 0.52, 0.78, 0.055, acc, lift=0.10)
    c.rect(-0.30, 0.04 + 0.26 * 0.52, 0.18, 0.18, WHITE, r=0.03, lift=0.0)
    c.rect(-0.30, 0.04 + 0.26 * 0.52, 0.05, 0.14, (0.86, 0.2, 0.2), lift=0.0)
    c.rect(-0.30, 0.04 + 0.26 * 0.52, 0.14, 0.05, (0.86, 0.2, 0.2), lift=0.0)
    c.path([(-0.46, 0.30 + oy), (-0.44, 0.38 + oy), (-0.16, 0.38 + oy), (-0.14, 0.30 + oy)], 0.020, (0.30, 0.32, 0.36), 1.0)
    # open top shows rolled bandages and gauze
    tu, tv = -0.30 + ox * 0.5, 0.30 + oy * 0.5
    c.ellipse(tu, tv, 0.33, 0.070, (0.30, 0.30, 0.32), lift=0.0)
    for k in range(3):
        c.ellipse(tu - 0.18 + k * 0.18, tv + 0.012, 0.075, 0.034, (0.96, 0.94, 0.88), lift=0.12)
    # loose items: bandage roll standing, vial, syringe
    _hb(c, 0.42, 0.10, 0.17, 0.14, (0.99, 0.97, 0.92), (0.78, 0.74, 0.66))
    c.ellipse(0.42, 0.17, 0.085, 0.026, (1.0, 0.99, 0.95), lift=0.0)
    c.ellipse(0.42, 0.172, 0.03, 0.009, (0.55, 0.52, 0.46), lift=0.0)
    c.rect(0.42, 0.075, 0.17, 0.012, acc, lift=0.0, alpha=0.9)
    _hb(c, 0.66, 0.08, 0.075, 0.13, (0.92, 0.97, 0.99), (0.62, 0.72, 0.78), alpha=0.95)                 # vial
    _hb(c, 0.66, 0.088, 0.06, 0.07, (0.96, 0.88, 0.60), (0.80, 0.62, 0.28))
    _hb(c, 0.66, 0.155, 0.082, 0.04, scale(acc, 1.1), scale(acc, 0.6))
    c.line(0.20, 0.035, 0.56, 0.06, 0.036, (0.90, 0.95, 0.98), 0.9)                                        # syringe barrel
    c.line(0.30, 0.040, 0.45, 0.049, 0.026, (0.55, 0.78, 0.90), 0.9)
    c.line(0.56, 0.062, 0.62, 0.067, 0.008, (0.78, 0.80, 0.84), 1.0)
    c.line(0.20, 0.035, 0.12, 0.030, 0.030, acc, 1.0)
    c.line(0.12, 0.030, 0.10, 0.029, 0.060, scale(acc, 0.8), 1.0)


@_sp("hlth_aw_carrier", aspect=1.30, fill=1.0)
def aw_carrier(c, color):
    """A plastic pet carrier with a barred door; a rescued cat peeks out from the dark inside."""
    rng = c.rng
    acc = _pal(color, "accent", (0.88, 0.48, 0.12))
    ao(c, 0.0, 0.0, 1.3, 0.22, 0.5)
    shell = mix((0.52, 0.60, 0.68), acc, 0.12)
    # top shell with handle, then the body
    c.path([(-0.20, 0.88), (-0.16, 0.99), (0.16, 0.99), (0.20, 0.88)], 0.045, scale(shell, 0.8), 1.0)
    _vpoly(c._c, [(-0.60, 0.04), (0.60, 0.04), (0.60, 0.82), (0.50, 0.88), (-0.50, 0.88), (-0.60, 0.82)], scale(shell, 1.12), scale(shell, 0.78), smooth=1)
    c.rect(0.0, 0.86, 1.10, 0.04, mix(shell, WHITE, 0.3), r=0.02, lift=0.1)
    # vents on the side and door opening
    for k in range(4):
        c.rect(-0.45 + k * 0.055, 0.56, 0.028, 0.20, scale(shell, 0.45), r=0.012, lift=0.0)
    c.rect(0.14, 0.45, 0.80, 0.70, scale(shell, 0.45), r=0.07, lift=0.0)
    c.rect(0.14, 0.45, 0.74, 0.64, (0.08, 0.09, 0.11), r=0.05, lift=0.0)
    # the cat in the doorway: ears, face, eyes, nose, whiskers
    cu, cv_ = 0.14, 0.44
    c.poly([(cu - 0.20, cv_ + 0.12), (cu - 0.17, cv_ + 0.30), (cu - 0.05, cv_ + 0.18)], (0.60, 0.42, 0.30), lift=0.1)
    c.poly([(cu + 0.20, cv_ + 0.12), (cu + 0.17, cv_ + 0.30), (cu + 0.05, cv_ + 0.18)], (0.55, 0.38, 0.27), lift=0.1)
    c.ellipse(cu, cv_ + 0.03, 0.23, 0.19, (0.66, 0.48, 0.34), lift=0.14)
    c.ellipse(cu, cv_ - 0.04, 0.10, 0.075, (0.95, 0.88, 0.78), lift=0.08)
    for sx in (-0.085, 0.085):
        c.ellipse(cu + sx, cv_ + 0.07, 0.042, 0.036, (0.78, 0.86, 0.34), lift=0.0)
        c.ellipse(cu + sx, cv_ + 0.07, 0.012, 0.030, (0.05, 0.05, 0.05), lift=0.0)
        c.circle(cu + sx - 0.012, cv_ + 0.082, 0.009, WHITE, lift=0.0)
    c.poly([(cu - 0.022, cv_ + 0.0), (cu + 0.022, cv_ + 0.0), (cu, cv_ - 0.022)], (0.90, 0.52, 0.54), lift=0.0)
    for sg in (-1, 1):
        for k in range(2):
            c.line(cu + sg * 0.06, cv_ - 0.025 - k * 0.012, cu + sg * 0.28, cv_ - 0.03 - k * 0.04 + 0.01, 0.004, (0.9, 0.9, 0.92), 0.8)
    # door bars
    for k in range(8):
        c.rect(0.14 - 0.34 + k * 0.097, 0.45, 0.018, 0.62, (0.82, 0.84, 0.88), lift=0.15)
    c.rect(0.14, 0.77, 0.76, 0.018, (0.82, 0.84, 0.88), lift=0.1)
    c.rect(0.14, 0.14, 0.76, 0.018, (0.82, 0.84, 0.88), lift=0.1)
    c.circle(0.56, 0.45, 0.022, acc, lift=0.2)
    c.rect(-0.45, 0.30, 0.04, 0.2, WHITE, lift=0.0, alpha=0.22)
    # a folded towel on top
    tw = mix(acc, WHITE, 0.55)
    c.rect(-0.34, 0.915, 0.42, 0.07, tw, r=0.03, lift=0.14)
    c.rect(-0.34, 0.915, 0.42, 0.016, mix(acc, WHITE, 0.2), lift=0.0, alpha=0.9)


@_sp("hlth_aw_leash", aspect=7.4, fill=0.24)
def aw_leash(c, color):
    """A coiled red leash, a collar with a gold paw tag and a rubber bone toy: adoption-day basics lying on the ground."""
    rng = c.rng
    acc = _pal(color, "accent", (0.88, 0.48, 0.12))
    red = mix(acc, (0.78, 0.12, 0.12), 0.65)
    ao(c, 0.0, 0.0, 2.0, 0.20, 0.5)
    # leash coil: nested ellipse rings
    for k in range(4):
        r = 0.30 - k * 0.045
        c.ellipse(-0.56, 0.07 + k * 0.012, r, r * 0.34, scale(red, 0.62), lift=0.0)
        c.ellipse(-0.56, 0.085 + k * 0.012, r * 0.93, r * 0.30, scale(red, 0.92 + 0.05 * k), lift=0.0)
        c.ellipse(-0.56, 0.095 + k * 0.012, r * 0.80, r * 0.24, scale(red, 0.35), lift=0.0, alpha=0.0)
    c.ellipse(-0.56, 0.14, 0.15, 0.040, (0.2, 0.15, 0.12), lift=0.0)
    c.line(-0.30, 0.08, -0.05, 0.05, 0.034, red, 1.0)
    c.rect(-0.04, 0.05, 0.035, 0.07, (0.76, 0.76, 0.80), r=0.01, lift=0.2)
    # collar ring with the tag
    c.ellipse(0.28, 0.07, 0.25, 0.075, scale(acc, 0.6), lift=0.0)
    c.ellipse(0.28, 0.085, 0.24, 0.070, mix(acc, (0.95, 0.9, 0.7), 0.2), lift=0.1)
    c.ellipse(0.28, 0.092, 0.20, 0.052, (0.22, 0.2, 0.2), lift=0.0, alpha=0.8)
    c.ellipse(0.40, 0.018, 0.045, 0.030, (0.94, 0.78, 0.30), lift=0.2)
    c.ellipse(0.40, 0.024, 0.014, 0.010, (0.78, 0.60, 0.18), lift=0.0)
    for dx in (-0.014, 0.0, 0.014):
        c.circle(0.40 + dx, 0.034, 0.006, (0.78, 0.60, 0.18), lift=0.0)
    # rubber bone
    bone = (0.96, 0.90, 0.78)
    c.line(0.66, 0.06, 0.92, 0.07, 0.07, scale(bone, 0.86), 1.0)
    c.line(0.66, 0.068, 0.92, 0.078, 0.05, bone, 1.0)
    for (x, y) in ((0.64, 0.05), (0.64, 0.10), (0.94, 0.055), (0.94, 0.105)):
        c.circle(x, y, 0.040, bone, lift=0.16)


@niche("animal-welfare", "Animal welfare and rescue", subjects=("hlth_aw_pup",),
       strong=("animal welfare", "animal rescue", "animal shelter", "stray dogs", "street dogs", "dog rescue", "rescue shelter", "animal ngo", "dog adoption", "pet adoption",
               "animal ambulance", "stray animals", "gaushala", "animal care trust", "पशु कल्याण", "एनिमल शेल्टर", "आवारा कुत्ते", "बेसहारा जानवर", "पशु बचाव",
               "जानवरों की सेवा", "animal welfare society", "rescued dogs", "street animals", "pashu seva", "pashu seva trust", "animal seva", "feeding drives for street dogs", "kutte ka rescue", "adopt a dog", "puppy adoption"),
       weak=("rescue", "shelter", "adoption", "vaccination drive", "sterilisation", "feeding drive", "strays", "volunteer walk", "donate", "dog", "cat", "puppy", "animals", "कुत्ता", "पशु"),
       accent="#e07a1f", mood="warm", group="professional",
       avoid=("vet clinic", "veterinary", "pet clinic", "pet shop", "pet store", "pet grooming", "grooming", "aquarium", "puppies for sale", "dog training", "boarding"))
def animal_welfare(S):
    P = S.pal
    dark = _dark(S)
    rng = S.rng
    gl = 1.7 if dark else 1.0
    warm = mix(P.wall_top, (1.0, 0.86, 0.62), 0.35)
    with S.far():
        S.wall(mix(warm, (1.0, 0.82, 0.55), 0.25), mix(P.wall_bot, (0.98, 0.70, 0.45), 0.25), 0.60)
        # sunrise glow over distant trees and a low shelter building with kennel arches
        S.glow(0.55, 0.52, 1.1, (1.0, 0.82, 0.45), 0.55 * gl, 1.6)
        S.circle(0.55, 0.50, 0.11, (1.0, 0.93, 0.70), lift=0.0, alpha=0.95)
        for u_, r_, hh in ((0.15, 0.14, 0.18), (0.98, 0.18, 0.22), (1.30, 0.13, 0.16), (1.75, 0.20, 0.24), (2.05, 0.15, 0.18)):
            S.ellipse(u_, 0.52 - hh * 0.5, r_, hh * 0.9, mix(P.accent_dark, P.wall_bot, 0.55) if not dark else scale(P.wall_bot, 0.8), lift=0.0, alpha=0.9)
        S.rect(1.70, 0.43, 0.95, 0.20, mix(warm, (0.86, 0.60, 0.40), 0.5), lift=0.0)
        for k in range(4):
            S.rect(1.38 + k * 0.22, 0.45, 0.13, 0.15, scale(P.wall_bot, 0.30 if dark else 0.42), r=0.05, lift=0.0)
            S.circle(1.38 + k * 0.22, 0.375, 0.065, scale(P.wall_bot, 0.30 if dark else 0.42), lift=0.0)
        S.rect(1.70, 0.325, 1.0, 0.025, scale(P.accent_dark, 1.1), lift=0.0)
        # bunting across the top (adoption day): plain flags in the palette colours
        cols = (P.accent, (1.0, 0.82, 0.35), mix(P.accent, WHITE, 0.45), (0.45, 0.70, 0.45), (0.95, 0.55, 0.45))
        S.line(0.0, 0.08, 2.0, 0.14, 0.004, (0.4, 0.32, 0.25), 0.9)
        for k in range(17):
            u_ = 0.05 + k * 0.12
            v_ = 0.08 + 0.06 * u_ / 2.0
            S.poly([(u_ - 0.035, v_), (u_ + 0.035, v_ + 0.003), (u_, v_ + 0.075)], mix(cols[k % 5], P.wall_bot, 0.4 if dark else 0.0))
        S.bokeh(6, 0.0, 0.1, 2.0, 0.5, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.4)], 0.012, 0.04, 0.3 * gl)
        S.rect(1.0, 0.585, 7.0, 0.05, mix((0.50, 0.66, 0.30), P.wall_bot, 0.5 if dark else 0.0) if not dark else (0.12, 0.2, 0.1), lift=0.0)
        S.floor(0.61, mix(P.floor_top, (0.92, 0.82, 0.66), 0.55) if not dark else scale(P.floor_top, 1.2), mix(P.floor_bot, (0.76, 0.64, 0.48), 0.5) if not dark else P.floor_bot)
    # chain-link fence in the mid ground: a thin diamond mesh and posts
    for k in range(22):
        u_ = -0.2 + k * 0.11
        S.line(u_, 0.38, u_ + 0.22, 0.60, 0.0035, (0.45, 0.40, 0.36), 0.28)
        S.line(u_ + 0.22, 0.38, u_, 0.60, 0.0035, (0.45, 0.40, 0.36), 0.28)
    for u_ in (0.10, 0.90, 1.70):
        S.rect(u_, 0.49, 0.020, 0.24, scale(P.accent_dark, 0.8), lift=0.0, alpha=0.8)
    S.rect(1.0, 0.60, 7.0, 0.008, scale(P.floor_top, 0.55), lift=0.0)
    # packed earth: warm light patch, scattered straw
    _sell(S, 1.20, 0.92, 0.95, 0.24, mix(P.light, (1.0, 0.85, 0.5), 0.5), 0.20 * gl)
    for _ in range(26):
        u_, v_ = rng.uniform(0.55, 1.85), rng.uniform(0.90, 1.08)
        S.line(u_, v_, u_ + rng.uniform(-0.06, 0.06), v_ + rng.uniform(-0.012, 0.012), 0.004, (0.90, 0.76, 0.40), 0.7)
    S.put("hlth_aw_carrier", 1.58, 0.86, 0.34, color=P, shadow_w=0.5)
    S.put("hlth_aw_pup", 1.14, 0.99, 0.52, color=P, subject=True, shadow_w=0.5)
    S.put("hlth_aw_bowls", 0.80, 1.06, 0.085, color=P, shadow_w=0.36)
    S.put("hlth_aw_vetkit", 1.56, 1.08, 0.22, color=P, shadow_w=0.5)
    S.put("hlth_aw_leash", 1.02, 1.12, 0.055, color=P, shadow_w=0.4)
    S.focus("detail", 1.14, 0.80)
    with S.near():
        S.circle(0.40, 1.08, 0.06, (1.0, 0.8, 0.4), alpha=0.28, lift=0)
        S.circle(1.95, 0.70, 0.05, (1.0, 0.75, 0.4), alpha=0.24, lift=0)


# ====================================================================================== BRIDAL MAKEUP
GOLD = (0.86, 0.68, 0.34)
ROSE = (0.90, 0.60, 0.62)


def _rose(c, u, v, r, col, rng):
    """A rose seen from the front: layered petals, a darker swirl at the heart and a soft highlight."""
    c.ellipse(u, v, r, r * 0.94, scale(col, 0.72), lift=0.0)
    c.ellipse(u, v + r * 0.04, r * 0.88, r * 0.82, col, lift=0.12)
    c.ellipse(u - r * 0.06, v + r * 0.04, r * 0.60, r * 0.56, scale(col, 0.88), lift=0.0)
    c.ellipse(u, v, r * 0.40, r * 0.38, mix(col, WHITE, 0.18), lift=0.0)
    c.ellipse(u + r * 0.04, v - r * 0.02, r * 0.22, r * 0.20, scale(col, 0.78), lift=0.0)
    c.ellipse(u - r * 0.35, v + r * 0.40, r * 0.26, r * 0.12, mix(col, WHITE, 0.75), lift=0.0, alpha=0.7, angle=25)


@_sp("hlth_bm_mirror", aspect=0.78, fill=1.05)
def bm_mirror(c, color):
    """A vanity mirror: oval gold frame ringed with warm round bulbs on a slim stem, the glass reflecting a blur of flowers and light."""
    rng = c.rng
    acc = _pal(color, "accent", (0.42, 0.56, 0.44))
    ao(c, 0.0, 0.0, 0.62, 0.12, 0.45)
    # stem and foot
    c.ellipse(0.0, 0.02, 0.22, 0.04, scale(GOLD, 0.7), lift=0.0)
    c.ellipse(0.0, 0.035, 0.22, 0.036, GOLD, lift=0.14)
    c.rect(0.0, 0.14, 0.04, 0.22, GOLD, lift=0.0)
    c.rect(-0.01, 0.14, 0.01, 0.2, WHITE, lift=0.0, alpha=0.45)
    c.glow(0.0, 0.62, 0.62, (1.0, 0.86, 0.58), 0.26)
    # frame, glass
    c.ellipse(0.0, 0.62, 0.395, 0.435, scale(GOLD, 0.62), lift=0.0)
    c.ellipse(0.0, 0.625, 0.375, 0.415, GOLD, lift=0.16)
    c.ellipse(0.0, 0.625, 0.31, 0.35, scale(GOLD, 0.7), lift=0.0)
    glass_top, glass_bot = (0.88, 0.93, 0.95), (0.98, 0.93, 0.90)
    c.ellipse(0.0, 0.625, 0.295, 0.335, mix(glass_top, glass_bot, 0.5), lift=0.16)
    # reflection: pale window light, a blurred bouquet of blush and sage, a white veil shape
    c.ellipse(-0.05, 0.80, 0.18, 0.12, (0.99, 0.99, 0.97), lift=0.0, alpha=0.7)
    for (dx, dy, rr, col) in ((-0.10, 0.44, 0.10, (0.94, 0.72, 0.74)), (0.06, 0.40, 0.09, (0.98, 0.90, 0.88)), (0.14, 0.52, 0.08, (0.90, 0.56, 0.60)),
                              (-0.18, 0.52, 0.07, (0.60, 0.74, 0.58)), (0.0, 0.50, 0.08, (0.97, 0.80, 0.80))):
        c.circle(dx, dy, rr, col, lift=0.0, alpha=0.62, soft=3.0)
    c.poly([(-0.20, 0.30), (0.22, 0.30), (0.26, 0.60), (-0.2, 0.60)], (0.82, 0.72, 0.66), lift=0.0, alpha=0.16)
    c.poly([(-0.20, 0.50), (-0.08, 0.50), (0.12, 0.92), (0.0, 0.92)], WHITE, lift=0.0, alpha=0.26)
    c.poly([(0.06, 0.40), (0.12, 0.40), (0.22, 0.80), (0.16, 0.80)], WHITE, lift=0.0, alpha=0.18)
    # bulbs round the frame
    n = 16
    for k in range(n):
        t = 2 * math.pi * (k + 0.5) / n
        bu, bv = 0.34 * math.cos(t) * 1.0, 0.625 + 0.385 * math.sin(t)
        if bv < 0.22:
            continue
        c.circle(bu, bv, 0.034, (1.0, 0.95, 0.80), lift=0.0)
        c.circle(bu - 0.006, bv + 0.008, 0.016, WHITE, lift=0.0, alpha=0.9)


@_sp("hlth_bm_lips", aspect=1.55, fill=0.80)
def bm_lips(c, color):
    """Four lipsticks standing in gold cases with twisted-up bullets (classic red, rose, coral, plum) and a creamy swatch smear in front."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.4, 0.2, 0.5)
    shades = ((0.80, 0.08, 0.14), (0.88, 0.42, 0.50), (0.94, 0.48, 0.34), (0.52, 0.16, 0.30))
    for i, (u, hh) in enumerate(((-0.45, 0.50), (-0.15, 0.64), (0.15, 0.56), (0.45, 0.46))):
        col = shades[i]
        w = 0.19
        _hb(c, u, 0.14, w, 0.26, scale(GOLD, 1.18), scale(GOLD, 0.60))                      # base case
        c.rect(u, 0.275, w * 1.04, 0.025, scale(GOLD, 0.7), lift=0.0)
        _hb(c, u, 0.34 + 0.04, w * 0.92, 0.08, (0.20, 0.20, 0.22), (0.07, 0.07, 0.08))      # black collar
        top = 0.30 + hh * 0.45
        _hb(c, u, 0.42 + (top - 0.42) / 2, w * 0.80, top - 0.42, scale(GOLD, 1.12), scale(GOLD, 0.62))
        # the bullet, slanted tip
        bt = top + hh * 0.28
        c.poly([(u - w * 0.36, top), (u + w * 0.36, top), (u + w * 0.36, bt - 0.05), (u - w * 0.30, bt + 0.03), (u - w * 0.36, bt - 0.02)], col, lift=0.2)
        c.poly([(u - w * 0.36, top), (u - w * 0.16, top), (u - w * 0.16, bt), (u - w * 0.36, bt - 0.02)], mix(col, WHITE, 0.3), lift=0.0, alpha=0.45)
        c.rect(u - w * 0.30, 0.18, 0.018, 0.20, WHITE, lift=0.0, alpha=0.55)
    c.ellipse(0.12, 0.020, 0.30, 0.018, shades[0], lift=0.1, alpha=0.8, angle=-4)
    c.ellipse(0.40, 0.012, 0.16, 0.014, shades[1], lift=0.1, alpha=0.8, angle=6)
    c.ellipse(-0.20, 0.016, 0.18, 0.015, shades[2], lift=0.1, alpha=0.8, angle=-8)


@_sp("hlth_bm_palette", aspect=1.45, fill=0.66)
def bm_palette(c, color):
    """An open eyeshadow palette: a mirror lid standing up behind a tray of twelve shimmering pans, with a fluffy brush laid across."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.26, 0.5)
    case = (0.34, 0.20, 0.22)
    # lid with a mirror
    c.poly([(-0.46, 0.34), (0.46, 0.34), (0.42, 0.64), (-0.42, 0.64)], scale(case, 0.9), lift=0.12)
    c.poly([(-0.40, 0.37), (0.40, 0.37), (0.37, 0.61), (-0.37, 0.61)], (0.82, 0.88, 0.90), lift=0.14)
    c.poly([(-0.30, 0.37), (-0.18, 0.37), (-0.02, 0.61), (-0.14, 0.61)], WHITE, lift=0.0, alpha=0.35)
    c.poly([(0.10, 0.37), (0.15, 0.37), (0.26, 0.61), (0.21, 0.61)], WHITE, lift=0.0, alpha=0.22)
    # tray
    c.poly([(-0.46, 0.04), (0.46, 0.04), (0.46, 0.09), (-0.46, 0.09)], scale(case, 0.62), lift=0.0)
    c.poly([(-0.46, 0.09), (0.46, 0.09), (0.46, 0.34), (-0.46, 0.34)], case, lift=0.12)
    pans = ((0.96, 0.84, 0.72), (0.90, 0.68, 0.52), (0.78, 0.52, 0.38), (0.62, 0.38, 0.30), (0.88, 0.62, 0.62), (0.98, 0.90, 0.80),
            (0.92, 0.74, 0.34), (0.74, 0.52, 0.24), (0.50, 0.28, 0.30), (0.72, 0.42, 0.50), (0.96, 0.82, 0.60), (0.40, 0.30, 0.38))
    for i, col in enumerate(pans):
        row, colm = divmod(i, 6)
        pu, pv = -0.35 + colm * 0.14, 0.27 - row * 0.10
        c.ellipse(pu, pv, 0.062, 0.040, scale(case, 0.5), lift=0.0)
        c.ellipse(pu, pv + 0.004, 0.056, 0.036, col, lift=0.16)
        c.ellipse(pu - 0.018, pv + 0.016, 0.022, 0.010, mix(col, WHITE, 0.7), lift=0.0, alpha=0.7)
    c.rect(0.0, 0.335, 0.92, 0.012, (0.94, 0.78, 0.50), lift=0.0, alpha=0.8)
    # a brush across the front
    c.line(-0.38, 0.02, 0.30, 0.055, 0.020, scale(GOLD, 0.9), 1.0)
    c.line(0.30, 0.055, 0.52, 0.065, 0.036, (0.94, 0.86, 0.80), 1.0)
    c.line(0.52, 0.065, 0.62, 0.07, 0.044, (0.98, 0.94, 0.90), 1.0)
    c.line(0.30, 0.055, 0.36, 0.058, 0.04, (0.7, 0.7, 0.74), 1.0)


@_sp("hlth_bm_brushes", aspect=0.95, fill=1.0)
def bm_brushes(c, color):
    """A gold brush pot holding seven makeup brushes of different sizes (fluffy powder, blush, contour and fine eye brushes)."""
    rng = c.rng
    acc = _pal(color, "accent", (0.42, 0.56, 0.44))
    ao(c, 0.0, 0.0, 0.50, 0.10, 0.45)
    heads = ((0.97, 0.90, 0.88, 0.17), (0.82, 0.62, 0.60, 0.13), (0.20, 0.18, 0.20, 0.12), (0.92, 0.78, 0.68, 0.14), (0.62, 0.50, 0.46, 0.10),
             (0.96, 0.94, 0.92, 0.09), (0.80, 0.56, 0.52, 0.11))
    angs = (112, 100, 92, 86, 78, 70, 120)
    for k in range(7):
        r_, g_, b_, hl = heads[k]
        a = math.radians(angs[k])
        bx, by = (k - 3) * 0.035, 0.28
        ln = 0.64 + 0.08 * ((k * 3) % 3)
        tx, ty = bx + math.cos(a) * ln * 0.55, by + math.sin(a) * ln
        hand = [GOLD, (0.96, 0.94, 0.90), (0.15, 0.15, 0.17)][k % 3]
        c.line(bx, by, tx, ty, 0.022, hand, 1.0)
        c.line(bx, by, tx, ty, 0.006, mix(hand, WHITE, 0.55), 0.6)
        mx, my = tx + math.cos(a) * 0.02, ty + math.sin(a) * 0.02
        c.line(tx, ty, mx, my, 0.035, (0.78, 0.78, 0.82), 1.0)
        c.ellipse(mx + math.cos(a) * hl * 0.45, my + math.sin(a) * hl * 0.45, hl * 0.42, hl * 0.62, (r_, g_, b_), lift=0.18, angle=angs[k] - 90)
        c.ellipse(mx + math.cos(a) * hl * 0.65, my + math.sin(a) * hl * 0.65, hl * 0.28, hl * 0.30, mix((r_, g_, b_), WHITE, 0.4), lift=0.0, alpha=0.7)
    _hb(c, 0.0, 0.21, 0.30, 0.38, scale(GOLD, 1.22), scale(GOLD, 0.55))
    c.ellipse(0.0, 0.40, 0.15, 0.036, scale(GOLD, 1.12), lift=0.0)
    c.ellipse(0.0, 0.40, 0.125, 0.026, (0.20, 0.14, 0.10), lift=0.0)
    c.rect(-0.09, 0.21, 0.018, 0.30, WHITE, lift=0.0, alpha=0.5)
    c.rect(0.0, 0.10, 0.30, 0.012, scale(GOLD, 0.6), lift=0.0, alpha=0.7)


@_sp("hlth_bm_bouquet", aspect=1.0, fill=1.0)
def bm_bouquet(c, color):
    """A hand-tied bridal bouquet: blush and ivory roses with sage eucalyptus leaves, baby's breath and a ribbon-wrapped stem."""
    rng = c.rng
    acc = _pal(color, "accent", (0.42, 0.56, 0.44))
    ao(c, 0.0, 0.0, 0.46, 0.09, 0.4)
    # stems + ribbon wrap
    c.poly([(-0.12, 0.62), (0.12, 0.62), (0.05, 0.02), (-0.05, 0.02)], (0.42, 0.56, 0.30), lift=0.15)
    c.poly([(-0.13, 0.40), (0.13, 0.40), (0.09, 0.22), (-0.09, 0.22)], mix(acc, WHITE, 0.2), lift=0.1)
    c.line(-0.12, 0.30, 0.12, 0.36, 0.014, WHITE, 0.8)
    c.line(-0.10, 0.25, 0.10, 0.31, 0.012, WHITE, 0.6)
    c.path([(0.0, 0.26), (-0.05, 0.14), (-0.10, 0.04)], 0.016, mix(acc, WHITE, 0.3), 1.0)
    c.path([(0.0, 0.26), (0.06, 0.12), (0.12, 0.06)], 0.016, mix(acc, WHITE, 0.3), 1.0)
    # foliage ring
    for k in range(14):
        a = 8 + k * (164 / 13.0)
        _leaf(c._c, 0.0, 0.70, 0.50 + 0.08 * rng.random(), a + rng.uniform(-8, 8), (0.42 + 0.14 * rng.random(), 0.58 + 0.1 * rng.random(), 0.48), 0.50, vein=False)
    # roses: back ring, front ring, centre
    pal = ((0.96, 0.82, 0.80), (0.99, 0.95, 0.90), (0.90, 0.62, 0.64), (0.97, 0.88, 0.84), (0.99, 0.97, 0.94))
    spots = ((-0.30, 0.80, 0.14), (0.30, 0.80, 0.14), (0.0, 0.96, 0.15), (-0.40, 0.64, 0.12), (0.40, 0.64, 0.12), (-0.16, 0.70, 0.16), (0.17, 0.72, 0.16),
             (0.0, 0.83, 0.17), (-0.26, 0.58, 0.13), (0.27, 0.58, 0.13), (0.0, 0.60, 0.14))
    for i, (du, dv, rr) in enumerate(spots):
        _rose(c, du, dv, rr, pal[(i * 2 + 1) % 5], rng)
    for _ in range(26):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(0.22, 0.46)
        c.circle(math.cos(a) * rr, 0.76 + math.sin(a) * rr * 0.62, rng.uniform(0.008, 0.016), WHITE, lift=0.0, alpha=0.9)


@_sp("hlth_bm_bangles", aspect=2.1, fill=0.34)
def bm_bangles(c, color):
    """Bridal jewellery: two stacks of red lacquer and gold bangles and a pair of gold jhumka earrings with pearl drops."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.6, 0.24, 0.5)
    red = (0.76, 0.10, 0.16)
    for su, n in ((-0.52, 6), (0.04, 5)):
        for k in range(n):
            col = red if k % 2 == 0 else GOLD
            v = 0.06 + k * 0.038
            c.ellipse(su, v, 0.25, 0.082, scale(col, 0.55), lift=0.0)
            c.ellipse(su, v + 0.012, 0.25, 0.080, col, lift=0.14)
            c.ellipse(su, v + 0.020, 0.205, 0.058, scale(col, 0.38), lift=0.0)
            c.line(su - 0.18, v + 0.05, su - 0.05, v + 0.075, 0.007, mix(col, WHITE, 0.55), 0.7)
    # jhumkas
    for ju in (0.46, 0.70):
        c.ellipse(ju, 0.12, 0.060, 0.062, scale(GOLD, 0.7), lift=0.0)
        c.poly([(ju - 0.06, 0.12), (ju + 0.06, 0.12), (ju + 0.04, 0.028), (ju - 0.04, 0.028)], GOLD, lift=0.2)
        for k in range(5):
            c.circle(ju - 0.04 + k * 0.02, 0.026, 0.011, (0.98, 0.94, 0.88), lift=0.2)
        c.line(ju, 0.155, ju, 0.20, 0.008, GOLD, 1.0)
        c.circle(ju, 0.215, 0.018, (0.98, 0.94, 0.88), lift=0.2)
        c.rect(ju - 0.018, 0.075, 0.012, 0.07, WHITE, lift=0.0, alpha=0.4)


@niche("bridal-makeup", "Bridal makeup artist", subjects=("hlth_bm_mirror",),
       strong=("bridal makeup", "bridal makeup artist", "bridal make up", "wedding makeup", "bride makeup", "makeup artist", "bridal look", "airbrush makeup", "hd makeup",
               "bridal hairstyling", "bridal studio", "dulhan makeup", "bridal makeover", "bridal beauty", "ब्राइडल मेकअप", "दुल्हन का मेकअप", "मेकअप आर्टिस्ट", "वेडिंग मेकअप",
               "dulhan ka makeup", "bridal makeup artist in", "bridal trial", "reception makeup"),
       weak=("bride", "bridal", "makeup", "make up", "haldi look", "sangeet look", "lipstick", "eyeshadow", "dulhan", "wedding look", "दुल्हन", "मेकअप", "hairstyling and draping"),
       accent="#6b8f71", mood="warm", group="wellness",
       avoid=("salon", "hair salon", "barber", "mehendi", "henna", "spa", "parlour", "beauty parlour", "wedding planner", "wedding venue", "banquet", "photographer", "photography", "jewellery"))
def bridal_makeup(S):
    P = S.pal
    dark = _dark(S)
    rng = S.rng
    gl = 1.7 if dark else 1.0
    blush = mix(P.wall_top, (0.99, 0.90, 0.86), 0.35)
    with S.far():
        S.wall(blush if not dark else P.wall_top, mix(P.wall_bot, (0.96, 0.84, 0.78), 0.3) if not dark else P.wall_bot, 0.62)
        _blobs(S, 12, -1.0, 0.0, 3.0, 0.62, scale(blush, 0.92), 0.14, 0.14, 0.34)
        # draped curtains in the accent on both sides with soft folds, a bridal garment hanging (red with a gold border)
        curt = mix(P.accent, (0.85, 0.88, 0.82), 0.35) if not dark else scale(P.accent, 0.5)
        for u_, w_ in ((0.34, 0.50), (0.75, 0.34)):
            S.gradient_rect(u_ - w_ / 2, 0.0, u_ + w_ / 2, 0.64, scale(curt, 1.05), scale(curt, 0.86))
            for k in range(5):
                S.rect(u_ - w_ / 2 + w_ * (k + 0.5) / 5.0, 0.32, 0.018, 0.64, scale(curt, 0.72), lift=0.0, alpha=0.55)
        S.line(0.05, 0.02, 1.1, 0.02, 0.012, scale(GOLD, 0.9), 1.0)
        lehenga = (0.78, 0.10, 0.16) if not dark else (0.55, 0.08, 0.12)
        S.line(1.72, 0.02, 1.72, 0.06, 0.006, scale(GOLD, 0.8), 1.0)
        S.poly([(1.58, 0.07), (1.86, 0.07), (1.96, 0.62), (1.48, 0.62)], lehenga, alpha=1.0)
        S.poly([(1.58, 0.07), (1.66, 0.07), (1.58, 0.62), (1.48, 0.62)], scale(lehenga, 0.72), alpha=0.7)
        S.rect(1.72, 0.60, 0.50, 0.035, GOLD, lift=0.0)
        for k in range(6):
            S.rect(1.50 + k * 0.08, 0.50, 0.02, 0.18, mix(GOLD, lehenga, 0.2), lift=0.0, alpha=0.55)
        S.glow(1.0, 0.18, 1.0, P.light, 0.28 * gl, 1.6)
        # fairy lights along the top
        for k in range(24):
            S.circle(0.05 + k * 0.083, 0.045 + 0.02 * math.sin(k * 0.8), 0.014, (1.0, 0.88, 0.58), lift=0.0, alpha=0.9)
            S.glow(0.05 + k * 0.083, 0.045 + 0.02 * math.sin(k * 0.8), 0.06, (1.0, 0.85, 0.5), 0.45 * gl)
        S.bokeh(7, 0.0, 0.1, 2.0, 0.55, [(1.0, 0.88, 0.6), P.accent_light, (1.0, 0.8, 0.75)], 0.012, 0.04, 0.26 * gl)
        S.floor(0.62, mix(P.floor_top, P.paper, 0.4), P.floor_bot)
    # dressing table: pale wood top with a white lace runner
    top = mix(P.surface, (0.97, 0.92, 0.84), 0.5) if not dark else P.surface
    S.floor(0.62, scale(top, 1.04), scale(top, 0.78))
    S.rect(1.0, 0.62, 7.0, 0.010, scale(top, 0.55), lift=0.0)
    for k in range(5):
        S.rect(1.0, 0.70 + k * 0.09, 7.0, 0.003, scale(top, 0.82), lift=0.0, alpha=0.5)
    lace = (0.99, 0.97, 0.94) if not dark else (0.58, 0.56, 0.54)
    _spoly_stage(S, [(0.52, 0.74), (1.92, 0.74), (2.14, 1.16), (0.30, 1.16)], lace, 0.95)
    for k in range(14):
        S.circle(0.40 + k * 0.125, 1.145, 0.024, scale(lace, 0.93), lift=0.0)
    S.put("hlth_bm_brushes", 1.58, 0.88, 0.32, color=P, shadow_w=0.26)
    S.put("hlth_bm_mirror", 1.14, 0.90, 0.58, color=P, subject=True, shadow_w=0.4)
    S.put("hlth_bm_bouquet", 0.76, 1.00, 0.34, color=P, shadow_w=0.34)
    S.put("hlth_bm_palette", 1.18, 1.10, 0.19, color=P, shadow_w=0.5)
    S.put("hlth_bm_lips", 1.52, 1.07, 0.21, color=P, shadow_w=0.4)
    S.put("hlth_bm_bangles", 0.98, 1.14, 0.13, color=P, shadow_w=0.4)
    S.focus("detail", 1.16, 0.70)
    with S.near():
        S.circle(0.45, 1.08, 0.06, (1.0, 0.85, 0.55), alpha=0.28, lift=0)
        S.circle(1.95, 0.62, 0.05, (1.0, 0.8, 0.7), alpha=0.24, lift=0)
