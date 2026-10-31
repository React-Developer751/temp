"""Props: tools and trades (spanner, hammer, drill, ladder, scissors, sewing machine ...)."""
import math

from .core import WHITE, mix, prop, scale


class _R:
    """Draws upright shapes through a rotation (about piv) followed by a shift, so a tool can lean."""

    def __init__(self, c, ang=0.0, piv=(0.0, 0.0), sh=(0.0, 0.0)):
        self.c, self.ang, self.piv, self.sh = c, ang, piv, sh
        a = math.radians(ang)
        self.ca, self.sa = math.cos(a), math.sin(a)

    def p(self, u, v):
        du, dv = u - self.piv[0], v - self.piv[1]
        return (self.piv[0] + du * self.ca - dv * self.sa + self.sh[0],
                self.piv[1] + du * self.sa + dv * self.ca + self.sh[1])

    def poly(self, pts, col, lift=0.10, alpha=1.0):
        self.c.poly([self.p(u, v) for u, v in pts], col, lift=lift, alpha=alpha)

    def rect(self, u, v, w, h, col, lift=0.10, alpha=1.0):
        self.poly([(u - w / 2, v - h / 2), (u + w / 2, v - h / 2), (u + w / 2, v + h / 2), (u - w / 2, v + h / 2)], col, lift, alpha)

    def bar(self, a, b, w0, w1, col, lift=0.10, alpha=1.0):
        """Tapered strip from point a to point b, width w0 at a and w1 at b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        self.poly([(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
                   (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)], col, lift, alpha)

    def circle(self, u, v, r, col, lift=0.10, alpha=1.0):
        pu, pv = self.p(u, v)
        self.c.circle(pu, pv, r, col, lift=lift, alpha=alpha)

    def ellipse(self, u, v, a, b, col, angle=0.0, lift=0.10, alpha=1.0):
        pu, pv = self.p(u, v)
        self.c.ellipse(pu, pv, a, b, col, angle=angle + self.ang, lift=lift, alpha=alpha)

    def line(self, u0, v0, u1, v1, w, col, alpha=1.0):
        a, b = self.p(u0, v0), self.p(u1, v1)
        self.c.line(a[0], a[1], b[0], b[1], w, col, alpha)

    def path(self, pts, w, col, alpha=1.0, smooth=True, closed=False):
        self.c.path([self.p(u, v) for u, v in pts], w, col, alpha, smooth=smooth, closed=closed)

    def ring(self, u, v, rx, ry, w, col, alpha=1.0):
        pts = [(u + rx * math.cos(t * math.pi / 12), v + ry * math.sin(t * math.pi / 12)) for t in range(24)]
        self.path(pts, w, col, alpha, smooth=False, closed=True)


def _steel(c, k=1.0):
    return scale(c.col((0.66, 0.70, 0.78)), k)


def _drop(c, u, v, r, col):
    c.poly([(u - r * 0.97, v + r * 0.25), (u, v + r * 2.3), (u + r * 0.97, v + r * 0.25)], col, lift=0.0)
    c.circle(u, v, r, col, lift=0.12)
    c.circle(u - r * 0.35, v + r * 0.3, r * 0.28, WHITE, lift=0, alpha=0.7)


# ---------------------------------------------------------------- wrench

def _jaw_head(R, cu, cv, rad, half, up, col):
    y = math.sqrt(rad * rad - half * half)
    th0 = math.atan2(y, half)
    sweep = math.pi + 2 * th0
    pts = [(half, -0.01), (half, y)]
    n = 26
    for k in range(n + 1):
        a = th0 - sweep * k / n
        pts.append((rad * math.cos(a), rad * math.sin(a)))
    pts += [(-half, y), (-half, -0.01)]
    out = [(cu + u, cv + (v if up else -v)) for u, v in pts]
    R.poly(out, col, lift=0.14)


def _draw_wrench(R, col):
    R.bar((0, 0.20), (0, 0.80), 0.17, 0.19, col, lift=0.14)
    _jaw_head(R, 0.0, 0.80, 0.23, 0.085, True, col)
    _jaw_head(R, 0.0, 0.20, 0.19, 0.07, False, col)
    R.line(-0.045, 0.30, -0.045, 0.72, 0.026, WHITE, alpha=0.35)
    R.circle(0.0, 0.5, 0.025, scale(col, 0.7), lift=0.0)
    R.ellipse(-0.08, 0.90, 0.04, 0.07, WHITE, angle=40, lift=0, alpha=0.35)


@prop("wrench", aspect=0.88, place="table", nominal=0.3, fill=0.92, category="tools", words=("spanner",))
def wrench(c, color):
    c.shadow(0.0, 0.01, 0.9, 0.06)
    _draw_wrench(_R(c, 35, (0, 0), (0.30, 0.02)), c.pick(color, (0.62, 0.67, 0.76)))


# ---------------------------------------------------------------- hammer

def _draw_hammer(R, c, wood):
    steel = _steel(c)
    R.bar((0, 0.02), (0, 0.80), 0.115, 0.085, wood, lift=0.15)
    R.bar((0, 0.02), (0, 0.32), 0.12, 0.10, scale(wood, 0.72), lift=0.1)
    R.line(-0.025, 0.36, -0.018, 0.76, 0.014, WHITE, alpha=0.25)
    R.poly([(-0.06, 0.98), (0.20, 0.98), (0.20, 0.71), (-0.06, 0.71)], steel, lift=0.16)
    R.poly([(-0.06, 0.98), (-0.20, 0.97), (-0.34, 0.91), (-0.43, 0.79), (-0.37, 0.77), (-0.28, 0.83), (-0.18, 0.80), (-0.06, 0.71)], steel, lift=0.16)
    R.line(-0.37, 0.80, -0.14, 0.85, 0.014, scale(steel, 0.55))
    R.poly([(0.20, 1.0), (0.27, 0.99), (0.27, 0.70), (0.20, 0.69)], scale(steel, 0.82), lift=0.12)
    R.rect(0.30, 0.845, 0.05, 0.25, mix(steel, WHITE, 0.3), lift=0.1)
    R.line(-0.02, 0.94, 0.17, 0.94, 0.02, WHITE, alpha=0.4)


@prop("hammer", aspect=0.97, place="table", nominal=0.3, fill=0.95, category="tools", words=("mallet", "sledgehammer"))
def hammer(c, color):
    c.shadow(0.0, 0.01, 0.9, 0.06)
    _draw_hammer(_R(c, -32, (0, 0), (-0.24, 0.02)), c, c.pick(color, (0.72, 0.48, 0.26)))


# ---------------------------------------------------------------- screwdriver

def _draw_screwdriver(R, c, col):
    steel = _steel(c)
    R.bar((0, 0.45), (0, 0.90), 0.036, 0.034, steel, lift=0.2)
    R.poly([(-0.017, 0.86), (0.017, 0.86), (0.042, 0.94), (0.042, 1.0), (-0.042, 1.0), (-0.042, 0.94)], steel, lift=0.15)
    R.rect(0, 0.465, 0.09, 0.08, scale(steel, 0.8), lift=0.1)
    R.rect(0, 0.21, 0.19, 0.44, col, lift=0.16)
    R.circle(0, 0.03, 0.095, scale(col, 0.78), lift=0.08)
    R.rect(0, 0.21, 0.19, 0.44, col, lift=0.16)
    R.circle(0, 0.40, 0.095, scale(col, 1.05), lift=0.12)
    R.rect(0, 0.14, 0.195, 0.24, scale(c.col((0.16, 0.17, 0.21)), 1.0), lift=0.1)
    for k in range(4):
        R.line(-0.09, 0.07 + k * 0.055, 0.09, 0.07 + k * 0.055, 0.012, c.col((0.34, 0.36, 0.42)), alpha=0.7)
    R.line(-0.045, 0.30, -0.045, 0.42, 0.022, WHITE, alpha=0.35)


@prop("screwdriver", aspect=0.83, place="table", nominal=0.3, fill=0.88, category="tools", words=())
def screwdriver(c, color):
    c.shadow(0.0, 0.01, 0.6, 0.05)
    _draw_screwdriver(_R(c, -38, (0, 0), (-0.31, 0.02)), c, c.pick(color, (0.96, 0.52, 0.14)))


# ---------------------------------------------------------------- drill

@prop("drill", aspect=1.57, place="table", nominal=0.28, fill=0.93, category="tools", words=("driller",))
def drill(c, color):
    c.shadow(0.0, 0.02, 1.2, 0.06)
    R = _R(c, 0, (0, 0), (-0.28, 0.0))
    body = c.pick(color, (0.95, 0.60, 0.12))
    dark = c.col((0.17, 0.18, 0.22))
    steel = _steel(c)
    R.rect(-0.12, 0.10, 0.46, 0.16, dark, lift=0.10)                                      # battery
    R.rect(-0.12, 0.155, 0.46, 0.025, scale(dark, 1.5), lift=0.0)
    R.circle(0.04, 0.10, 0.025, c.col((0.3, 0.9, 0.4)), lift=0)
    R.poly([(-0.25, 0.62), (0.02, 0.62), (-0.01, 0.17), (-0.28, 0.17)], dark, lift=0.12)      # handle grip
    for k in range(4):
        R.line(-0.27 + k * 0.001, 0.50 - k * 0.07, -0.01 + k * 0.001, 0.50 - k * 0.07, 0.014, scale(dark, 1.9), alpha=0.8)
    R.rect(-0.07, 0.76, 0.66, 0.34, body, lift=0.16)                                         # motor housing
    R.ellipse(-0.40, 0.76, 0.05, 0.17, scale(body, 0.88), lift=0.1)
    R.rect(0.20, 0.76, 0.14, 0.30, scale(body, 0.78), lift=0.12)                             # gear case
    for k in range(4):
        R.rect(-0.30 + k * 0.07, 0.85, 0.035, 0.07, scale(body, 0.55), lift=0.0)           # vents
    R.rect(0.08, 0.54, 0.075, 0.12, dark, lift=0.1)                                          # trigger
    R.rect(0.0, 0.64, 0.30, 0.03, scale(dark, 0.9), lift=0)
    R.poly([(0.28, 0.86), (0.50, 0.83), (0.50, 0.69), (0.28, 0.66)], steel, lift=0.2)         # chuck
    for k in range(4):
        R.line(0.33 + k * 0.045, 0.85 - k * 0.006, 0.33 + k * 0.045, 0.67 + k * 0.006, 0.014, scale(steel, 0.55))
    R.bar((0.50, 0.76), (1.02, 0.76), 0.055, 0.05, scale(steel, 0.85), lift=0.2)               # bit
    for k in range(7):
        R.line(0.56 + k * 0.065, 0.785, 0.60 + k * 0.065, 0.735, 0.014, scale(steel, 0.5))
    R.line(-0.40, 0.90, 0.10, 0.90, 0.02, WHITE, alpha=0.3)


# ---------------------------------------------------------------- saw

@prop("saw", aspect=1.7, place="table", nominal=0.3, fill=0.74, category="tools", words=("handsaw", "hacksaw"))
def saw(c, color):
    c.shadow(0.0, 0.02, 1.3, 0.06)
    R = _R(c, 16, (0.0, 0.5), (-0.38, -0.14))
    grip = c.pick(color, (0.80, 0.42, 0.18))
    steel = _steel(c)
    # blade
    R.poly([(0.02, 0.74), (0.90, 0.64), (1.0, 0.55), (1.0, 0.49), (0.02, 0.36)], steel, lift=0.18)
    n = 22
    for k in range(n):
        x0 = 0.12 + k * (0.88 / n)
        x1 = x0 + 0.88 / n

        def yb(x):
            return 0.37 + (0.49 - 0.37) * (x - 0.02) / 0.98
        R.poly([(x0, yb(x0) + 0.004), (x1, yb(x1) + 0.004), (x1, yb(x1) - 0.04)], scale(steel, 0.92), lift=0.1)
    R.line(0.14, 0.62, 0.92, 0.57, 0.012, WHITE, alpha=0.5)
    R.line(0.14, 0.52, 0.92, 0.51, 0.01, scale(steel, 0.65), alpha=0.8)
    # handle
    R.ring(-0.07, 0.50, 0.19, 0.25, 0.115, grip)
    R.ring(-0.07, 0.50, 0.19, 0.25, 0.04, mix(grip, WHITE, 0.25), alpha=0.5)
    R.bar((0.07, 0.44), (0.12, 0.44), 0.16, 0.16, scale(steel, 0.8), lift=0.1)
    R.circle(0.06, 0.62, 0.022, c.col((0.85, 0.65, 0.2)), lift=0.1)
    R.circle(0.06, 0.45, 0.022, c.col((0.85, 0.65, 0.2)), lift=0.1)


# ---------------------------------------------------------------- paint roller

@prop("paintroller", aspect=0.91, place="table", nominal=0.3, fill=0.96, category="tools", words=("roller",))
def paintroller(c, color):
    c.shadow(0.0, 0.02, 0.9, 0.06)
    R = _R(c, 0, (0, 0), (-0.04, 0.0))
    paint = c.pick(color, (0.30, 0.62, 0.92))
    steel = _steel(c, 0.9)
    handle = c.col((0.96, 0.58, 0.16))
    # puddle and falling drop
    c.ellipse(-0.34, 0.03, 0.15, 0.028, paint, lift=0.05, alpha=0.9)
    # frame
    R.path([(0.34, 0.84), (0.50, 0.84), (0.52, 0.62), (0.34, 0.57), (0.0, 0.54)], 0.04, scale(steel, 0.7), smooth=False)
    R.bar((0, 0.56), (0, 0.02), 0.10, 0.12, handle, lift=0.15)
    R.rect(0, 0.18, 0.12, 0.30, scale(c.col((0.2, 0.22, 0.28)), 1.0), lift=0.1)
    R.rect(0, 0.56, 0.06, 0.05, scale(steel, 0.8), lift=0.1)
    # roller
    R.rect(0, 0.84, 0.74, 0.26, paint, lift=0.2)
    R.rect(0, 0.84, 0.74, 0.26, paint, lift=0.2)
    R.circle(0.37, 0.84, 0.07, scale(paint, 0.8), lift=0.1)
    R.circle(-0.37, 0.84, 0.07, mix(paint, WHITE, 0.2), lift=0.1)
    R.line(-0.30, 0.91, 0.28, 0.91, 0.03, WHITE, alpha=0.3)
    for k in range(6):
        R.line(-0.28 + k * 0.11, 0.94, -0.24 + k * 0.11, 0.74, 0.012, scale(paint, 0.8), alpha=0.5)
    # drip
    R.poly([(-0.36, 0.72), (-0.31, 0.72), (-0.32, 0.50), (-0.35, 0.50)], paint, lift=0.1)
    R.circle(-0.335, 0.49, 0.032, paint, lift=0.1)
    _drop(c.sub(R.p(-0.335, 0.27)[0], R.p(-0.335, 0.27)[1], 1.0), 0.0, 0.0, 0.025, paint)


# ---------------------------------------------------------------- faucet

@prop("faucet", aspect=0.8, place="table", nominal=0.3, fill=1.0, category="tools", words=("tap", "nal", "spigot"))
def faucet(c, color):
    R = _R(c, 0, (0, 0), (0.03, 0.0))
    chrome = _steel(c, 1.0)
    wheel = c.pick(color, (0.88, 0.22, 0.24))
    water = c.col((0.35, 0.68, 0.98))
    c.shadow(0.0, 0.01, 0.9, 0.05)
    c.ellipse(0.21, 0.03, 0.17, 0.028, water, lift=0.05, alpha=0.8)
    R.rect(-0.30, 0.05, 0.32, 0.09, scale(chrome, 0.85), lift=0.12)
    R.rect(-0.30, 0.12, 0.16, 0.06, scale(chrome, 0.7), lift=0.1)
    arm = [(-0.30, 0.10), (-0.30, 0.56), (-0.27, 0.71), (-0.16, 0.78), (0.0, 0.79), (0.14, 0.75), (0.19, 0.64), (0.19, 0.58)]
    R.path(arm, 0.15, scale(chrome, 0.78), smooth=True)
    R.path([(-0.325, 0.12), (-0.325, 0.56), (-0.30, 0.72), (-0.18, 0.80), (0.0, 0.81), (0.13, 0.77)], 0.045, mix(chrome, WHITE, 0.55), smooth=True, alpha=0.7)
    R.rect(0.19, 0.55, 0.19, 0.07, scale(chrome, 0.65), lift=0.1)
    R.rect(-0.09, 0.80, 0.19, 0.10, scale(chrome, 0.9), lift=0.15)
    R.rect(-0.09, 0.89, 0.07, 0.12, scale(chrome, 0.75), lift=0.1)
    R.ellipse(-0.09, 0.97, 0.22, 0.055, wheel, lift=0.18)
    R.ellipse(-0.09, 0.945, 0.22, 0.04, scale(wheel, 0.7), lift=0.05)
    R.ellipse(-0.09, 0.97, 0.22, 0.055, wheel, lift=0.18)
    R.circle(-0.09, 0.98, 0.04, mix(wheel, WHITE, 0.4), lift=0.1)
    for k, (v, r) in enumerate(((0.43, 0.04), (0.27, 0.035), (0.13, 0.03))):
        _drop(c, R.p(0.19, v)[0], R.p(0.19, v)[1], r, water)


# ---------------------------------------------------------------- toolbox

@prop("toolbox", aspect=1.19, place="table", nominal=0.3, fill=1.0, category="tools", words=("toolkit",))
def toolbox(c, color):
    c.shadow(0.0, 0.01, 1.1, 0.07)
    red = c.pick(color, (0.85, 0.20, 0.20))
    steel = _steel(c)
    dark = c.col((0.16, 0.17, 0.21))
    # inside of the open box
    c.rect(0, 0.39, 0.92, 0.06, scale(red, 0.5), r=0.02, lift=0)
    # tools sticking out
    _draw_hammer(_R(c.sub(0.22, 0.20, 0.78), -16, (0, 0), (0, 0)), c, c.col((0.72, 0.48, 0.26)))
    _draw_screwdriver(_R(c.sub(-0.32, 0.20, 0.82), 14, (0, 0), (0, 0)), c, c.col((0.20, 0.45, 0.85)))
    # body
    c.rect(0, 0.20, 0.94, 0.38, red, r=0.04, lift=0.16)
    c.rect(0, 0.36, 0.94, 0.08, mix(red, WHITE, 0.15), r=0.03, lift=0.1)
    c.rect(0, 0.07, 0.94, 0.06, scale(red, 0.75), r=0.02, lift=0.05)
    c.rect(0, 0.21, 0.30, 0.10, c.col((1.0, 0.83, 0.25)), r=0.02, lift=0.1)
    c.rect(0, 0.21, 0.22, 0.02, scale(red, 0.9), lift=0)
    for sgn in (-1, 1):
        c.rect(sgn * 0.33, 0.33, 0.11, 0.17, steel, r=0.02, lift=0.15)
        c.rect(sgn * 0.33, 0.30, 0.07, 0.04, scale(steel, 0.6), r=0.01, lift=0)
        c.circle(sgn * 0.42, 0.10, 0.018, steel, lift=0.1)
    c.line(-0.43, 0.30, 0.43, 0.30, 0.012, WHITE, alpha=0.18)
    # carry handle
    c.path([(-0.15, 0.38), (-0.13, 0.54), (0.0, 0.57), (0.13, 0.54), (0.15, 0.38)], 0.045, dark, smooth=True)
    c.path([(-0.13, 0.44), (-0.11, 0.52), (0.0, 0.55)], 0.01, WHITE, alpha=0.3, smooth=True)


# ---------------------------------------------------------------- ladder

@prop("ladder", aspect=0.82, place="ground", nominal=0.5, fill=1.0, category="tools", words=("stepladder", "steps"))
def ladder(c, color):
    c.shadow(0.0, 0.015, 0.9, 0.07)
    rail = c.pick(color, (0.93, 0.62, 0.18))
    dark = c.col((0.18, 0.19, 0.23))
    hb, ht, wb, wt = 0.34, 0.22, 0.08, 0.06

    def hw(v):
        return hb + (ht - hb) * v

    for sgn in (-1, 1):
        c.rect(sgn * hb, 0.015, 0.11, 0.035, dark, r=0.012, lift=0.05)
    n = 8
    for k in range(n):
        v = 0.10 + k * (0.86 / (n - 1))
        h = hw(v) - 0.03
        c.rect(0, v - 0.026, 2 * h, 0.05, scale(rail, 0.55), lift=0.0, alpha=0.5)
        c.rect(0, v, 2 * h, 0.05, mix(rail, WHITE, 0.25), lift=0.18)
        c.line(-h, v + 0.015, h, v + 0.015, 0.012, WHITE, alpha=0.35)
    for sgn in (-1, 1):
        shade = 1.0 if sgn < 0 else 0.84
        c.poly([(sgn * hb - wb / 2, 0.03), (sgn * hb + wb / 2, 0.03), (sgn * ht + wt / 2, 1.0), (sgn * ht - wt / 2, 1.0)],
               scale(rail, shade), lift=0.14)
        c.poly([(sgn * hb - wb / 2, 0.03), (sgn * hb - wb * 0.12, 0.03), (sgn * ht - wt * 0.12, 1.0), (sgn * ht - wt / 2, 1.0)],
               mix(rail, WHITE, 0.25), lift=0.0, alpha=0.5)
    c.rect(0, 0.985, 2 * ht + wt, 0.025, scale(rail, 0.9), r=0.01, lift=0.1)


# ---------------------------------------------------------------- hard hat

@prop("hardhat", aspect=1.45, place="table", nominal=0.24, fill=0.85, category="tools", words=("helmet", "safetyhat"))
def hardhat(c, color):
    c.shadow(0.02, 0.06, 1.3, 0.09)
    y = c.pick(color, (1.0, 0.80, 0.12))
    cu, cv, a, b = 0.0, 0.26, 0.44, 0.62
    dome = [(cu + a * math.cos(t * math.pi / 30), cv + b * math.sin(t * math.pi / 30)) for t in range(31)]
    c.ellipse(0.06, 0.17, 0.62, 0.10, scale(y, 0.92), lift=0.1)                           # brim
    c.poly(dome + [(-0.44, 0.17), (0.44, 0.17)], y, lift=0.18)
    c.rect(0, 0.22, 0.88, 0.10, y, lift=0.1)
    c.ellipse(0.0, 0.17, 0.46, 0.07, scale(y, 0.86), lift=0.1)
    # ridge strips
    for du, w in ((0.0, 0.17), (-0.20, 0.05), (0.20, 0.05)):
        top = cv + b * math.sqrt(max(0.0, 1 - (du / a) ** 2)) - 0.015
        top0 = cv + b * math.sqrt(max(0.0, 1 - ((du - w / 2) / a) ** 2)) - 0.015
        top1 = cv + b * math.sqrt(max(0.0, 1 - ((du + w / 2) / a) ** 2)) - 0.015
        c.poly([(du - w / 2, 0.22), (du + w / 2, 0.22), (du + w / 2, top1), (du, top), (du - w / 2, top0)],
               scale(y, 1.0 if du == 0 else 0.9), lift=0.16)
    c.line(-0.07, 0.30, -0.07, 0.78, 0.015, WHITE, alpha=0.4)
    c.ellipse(-0.20, 0.62, 0.05, 0.12, WHITE, angle=25, lift=0, alpha=0.3)
    c.rect(0.0, 0.12, 0.22, 0.03, scale(y, 0.7), r=0.01, lift=0)


# ---------------------------------------------------------------- scissors

@prop("scissors", aspect=0.78, place="table", nominal=0.32, fill=1.0, category="tools", words=("scissor", "shears", "kainchi", "clippers"))
def scissors(c, color):
    c.shadow(0.05, 0.01, 0.9, 0.05)
    R = _R(c.sub(0, 0, 0.88), -22, (0, 0.2), (-0.04, 0.125))
    steel = _steel(c)
    h1 = c.pick(color, (0.90, 0.25, 0.35))
    h2 = scale(h1, 0.82)
    # handles
    R.ring(0.17, 0.15, 0.13, 0.17, 0.08, h1)
    R.ring(0.17, 0.15, 0.13, 0.17, 0.025, mix(h1, WHITE, 0.4), alpha=0.5)
    R.ring(-0.17, 0.15, 0.13, 0.17, 0.08, h2)
    R.ring(-0.17, 0.15, 0.13, 0.17, 0.025, mix(h2, WHITE, 0.4), alpha=0.5)
    # blade A: handle on the right, tip on the left
    R.bar((0.15, 0.30), (0.0, 0.48), 0.09, 0.09, scale(steel, 0.88), lift=0.1)
    R.poly([(0.06, 0.43), (-0.06, 0.50), (-0.24, 1.0), (-0.20, 1.0)], steel, lift=0.18)
    R.poly([(0.06, 0.43), (-0.06, 0.50), (-0.20, 1.0)], mix(steel, WHITE, 0.25), lift=0.1, alpha=0.6)
    # blade B on top
    R.bar((-0.15, 0.30), (0.0, 0.48), 0.09, 0.09, steel, lift=0.12)
    R.poly([(-0.06, 0.43), (0.06, 0.50), (0.24, 1.0), (0.20, 1.0)], steel, lift=0.18)
    R.poly([(-0.06, 0.43), (0.06, 0.50), (0.20, 1.0)], mix(steel, WHITE, 0.25), lift=0.1, alpha=0.6)
    R.circle(0.0, 0.47, 0.04, c.col((0.78, 0.55, 0.15)), lift=0.2)
    R.circle(0.0, 0.47, 0.015, scale(steel, 0.5), lift=0)


# ---------------------------------------------------------------- sewing machine

@prop("sewingmachine", aspect=1.21, place="table", nominal=0.3, fill=1.0, category="tools", words=("sewing", "stitching"))
def sewingmachine(c, color):
    c.shadow(0.0, 0.02, 1.3, 0.07)
    R = _R(c.sub(0, 0, 0.88), 0, (0, 0), (0.0, 0.0))
    body = c.pick(color, (0.80, 0.88, 0.90))
    dark = scale(body, 0.66)
    steel = _steel(c)
    red = c.col((0.88, 0.22, 0.28))
    fabric = c.col((0.98, 0.78, 0.84))
    R.rect(0.0, 0.07, 1.04, 0.12, dark, lift=0.12)                                 # base
    R.rect(0.0, 0.14, 1.04, 0.05, body, lift=0.12)
    R.rect(-0.30, 0.16, 0.30, 0.02, scale(steel, 0.8), lift=0.1)                   # throat plate
    R.rect(0.37, 0.52, 0.22, 0.85, body, lift=0.14)                                # pillar
    R.rect(0.0, 0.84, 1.04, 0.24, body, lift=0.16)                                 # arm
    R.rect(-0.40, 0.70, 0.22, 0.46, body, lift=0.16)                               # head
    R.rect(-0.40, 0.46, 0.05, 0.15, steel, lift=0.12)                              # needle bar
    R.line(-0.40, 0.40, -0.40, 0.19, 0.012, scale(steel, 0.7))
    R.rect(-0.40, 0.18, 0.12, 0.02, scale(steel, 0.85), lift=0.1)
    # fabric under the needle
    R.poly([(-0.62, 0.160), (-0.02, 0.160), (-0.02, 0.215), (-0.62, 0.215)], fabric, lift=0.12)
    R.poly([(-0.62, 0.160), (-0.52, 0.10), (-0.52, 0.140), (-0.62, 0.160)], scale(fabric, 0.8), lift=0)
    for k in range(5):
        R.circle(-0.57 + k * 0.11, 0.188, 0.012, c.col((0.88, 0.35, 0.45)), lift=0)
    R.line(-0.40, 0.19, -0.14, 0.19, 0.008, c.col((0.35, 0.2, 0.45)))
    # control dial and stitch panel
    R.circle(0.12, 0.84, 0.065, scale(body, 1.1), lift=0.18)
    R.circle(0.12, 0.84, 0.032, dark, lift=0.1)
    R.rect(-0.05, 0.84, 0.12, 0.05, c.col((0.15, 0.17, 0.2)), lift=0)
    R.line(-0.10, 0.84, 0.0, 0.84, 0.014, c.col((0.3, 0.9, 0.7)))
    # spool on top and thread
    R.rect(0.18, 0.99, 0.06, 0.04, scale(steel, 0.8), lift=0.1)
    R.rect(0.18, 1.04, 0.14, 0.03, c.col((0.7, 0.52, 0.3)), lift=0.1)
    R.rect(0.18, 1.12, 0.14, 0.03, c.col((0.7, 0.52, 0.3)), lift=0.1)
    R.rect(0.18, 1.08, 0.11, 0.07, red, lift=0.15)
    R.path([(0.12, 1.10), (-0.1, 1.14), (-0.33, 1.06), (-0.40, 0.94), (-0.40, 0.55)], 0.012, red, smooth=True)
    # hand wheel
    R.circle(0.58, 0.80, 0.14, scale(steel, 0.9), lift=0.2)
    R.circle(0.58, 0.80, 0.09, scale(steel, 0.65), lift=0.1)
    R.circle(0.58, 0.80, 0.03, steel, lift=0.2)
    R.rect(0.485, 0.80, 0.03, 0.16, dark, lift=0.1)


# ---------------------------------------------------------------- spool of thread

@prop("spool", aspect=0.91, place="table", nominal=0.28, fill=0.94, category="tools", words=("thread", "bobbin", "needle"))
def spool(c, color):
    c.shadow(0.05, 0.01, 0.9, 0.05)
    th = c.pick(color, (0.88, 0.22, 0.30))
    wood = c.col((0.82, 0.62, 0.36))
    steel = _steel(c)
    # needle
    nd = _R(c, 12, (0, 0), (0.25, 0.0))
    nd.bar((0.15, 0.02), (0.15, 0.92), 0.02, 0.03, steel, lift=0.2)
    nd.ellipse(0.15, 0.88, 0.011, 0.045, scale(steel, 0.4), lift=0)
    # spool
    c.ellipse(0, 0.04, 0.28, 0.05, scale(wood, 0.78), lift=0.1)
    c.rect(0, 0.065, 0.56, 0.07, wood, r=0.02, lift=0.18)
    c.rect(0, 0.40, 0.42, 0.62, th, lift=0.18)
    for k in range(9):
        y0 = 0.12 + k * 0.067
        c.poly([(-0.21, y0), (0.21, y0 + 0.04), (0.21, y0 + 0.07), (-0.21, y0 + 0.03)], scale(th, 0.82 if k % 2 else 1.1), lift=0.1)
    c.rect(-0.12, 0.40, 0.05, 0.60, WHITE, lift=0, alpha=0.18)
    c.rect(0, 0.735, 0.56, 0.07, wood, r=0.02, lift=0.18)
    c.ellipse(0, 0.77, 0.28, 0.045, mix(wood, WHITE, 0.2), lift=0.1)
    c.ellipse(0, 0.77, 0.07, 0.02, scale(wood, 0.5), lift=0.0)
    # thread to the needle eye
    p0 = nd.p(0.15, 0.88)
    c.path([(0.20, 0.30), (0.40, 0.18), (0.50, 0.40), (p0[0] - 0.01, p0[1] - 0.02)], 0.018, th, smooth=True)
    c.path([(p0[0], p0[1]), (p0[0] + 0.03, p0[1] - 0.08), (p0[0] + 0.12, p0[1] - 0.2)], 0.016, th, smooth=True)


# ---------------------------------------------------------------- plug

@prop("plug", aspect=1.24, place="table", nominal=0.28, fill=0.98, category="tools", words=("socket", "outlet"))
def plug(c, color):
    c.shadow(0.05, 0.01, 1.3, 0.06)
    R = _R(c, 0, (0, 0), (-0.34, 0.0))
    body = c.pick(color, (0.25, 0.45, 0.85))
    steel = _steel(c)
    cable = c.col((0.16, 0.17, 0.21))
    # cable first
    R.path([(0.0, 0.26), (0.0, 0.12), (0.16, 0.05), (0.42, 0.07), (0.54, 0.19), (0.44, 0.30), (0.32, 0.22), (0.38, 0.10), (0.6, 0.05), (0.85, 0.08)], 0.075, cable, smooth=True)
    R.path([(0.0, 0.26), (0.0, 0.14), (0.16, 0.075), (0.42, 0.095)], 0.014, scale(cable, 2.3), smooth=True, alpha=0.6)
    # pins
    for sgn in (-1, 1):
        R.rect(sgn * 0.12, 0.83, 0.075, 0.30, steel, lift=0.2)
        R.circle(sgn * 0.12, 0.95, 0.018, scale(steel, 0.4), lift=0)
    # body
    R.rect(0.0, 0.62, 0.52, 0.12, scale(body, 0.78), lift=0.1)
    R.rect(0.0, 0.46, 0.50, 0.40, body, lift=0.18)
    R.poly([(-0.18, 0.28), (0.18, 0.28), (0.12, 0.20), (-0.12, 0.20)], scale(body, 0.85), lift=0.1)
    for k in range(4):
        R.line(-0.19, 0.40 + k * 0.07, 0.19, 0.40 + k * 0.07, 0.013, scale(body, 0.65), alpha=0.8)
    R.line(-0.21, 0.30, -0.21, 0.62, 0.02, WHITE, alpha=0.3)
    R.bar((0.0, 0.22), (0.0, 0.14), 0.12, 0.09, scale(cable, 1.25), lift=0.1)


# ---------------------------------------------------------------- gear

def _gear_pts(cu, cv, r0, r1, n, rot, hole):
    pts = []
    step = 2 * math.pi / n
    for k in range(n):
        a = rot + k * step
        for da, r in ((-0.30, r0), (-0.17, r1), (0.17, r1), (0.30, r0)):
            pts.append((cu + r * math.cos(a + da * step * 1.0), cv + r * math.sin(a + da * step * 1.0)))
    first = pts[0]
    inner = [(cu + hole * math.cos(rot + t * math.pi / 14), cv + hole * math.sin(rot + t * math.pi / 14)) for t in range(28)]
    inner_rev = [inner[0]] + inner[:0:-1] + [inner[0]]
    return pts + [first] + [(cu + hole * math.cos(rot), cv + hole * math.sin(rot))] + inner_rev[1:]


@prop("gear", aspect=1.4, place="table", nominal=0.28, fill=0.93, category="tools", words=("cog", "cogwheel", "cogs"))
def gear(c, color):
    c.shadow(0.0, 0.03, 1.1, 0.07)
    big = c.pick(color, (0.55, 0.60, 0.72))
    small = c.col((0.96, 0.64, 0.18))
    # small gear behind-right
    sc, sv = 0.52, 0.30
    c.poly(_gear_pts(sc, sv, 0.15, 0.21, 8, 0.2, 0.06), small, lift=0.2)
    c.ring(sc, sv, 0.10, 0.03, mix(small, WHITE, 0.3), alpha=0.5)
    # big gear
    gu, gv = -0.15, 0.50
    c.poly(_gear_pts(gu, gv, 0.34, 0.45, 12, 0.12, 0.14), big, lift=0.2)
    c.ring(gu, gv, 0.25, 0.025, mix(big, WHITE, 0.4), alpha=0.6)
    c.ring(gu, gv, 0.17, 0.02, scale(big, 0.7), alpha=0.7)
    c.ellipse(gu - 0.13, gv + 0.17, 0.08, 0.04, WHITE, angle=40, lift=0, alpha=0.25)


# ---------------------------------------------------------------- comb

@prop("comb", aspect=1.33, place="table", nominal=0.24, fill=0.8, category="tools", words=("haircomb",))
def comb(c, color):
    c.shadow(0.0, 0.05, 1.1, 0.06)
    R = _R(c, -9, (0, 0.5), (0.0, -0.18))
    col = c.pick(color, (0.20, 0.23, 0.32))
    top = 0.72
    teeth = [(-0.455 + k * 0.052, 0.034) for k in range(10)] + [(0.10 + k * 0.10, 0.055) for k in range(4)] + [(0.46, 0.04)]
    for x, w in teeth:
        R.poly([(x - w / 2, top), (x + w / 2, top), (x + w * 0.2, 0.28), (x, 0.24), (x - w * 0.2, 0.28)], col, lift=0.14)
    R.rect(0.0, 0.80, 1.0, 0.20, col, lift=0.18)
    R.rect(0.0, 0.88, 0.98, 0.04, mix(col, WHITE, 0.2), lift=0.0, alpha=0.7)
    R.rect(0.0, 0.725, 1.0, 0.02, scale(col, 0.6), lift=0.0)
    for k in range(4):
        R.line(-0.30 + k * 0.2, 0.81, -0.22 + k * 0.2, 0.81, 0.02, mix(col, WHITE, 0.5), alpha=0.6)


# ---------------------------------------------------------------- broom

@prop("broom", aspect=0.5, place="ground", nominal=0.5, fill=1.0, category="tools", words=("sweep", "jhadu", "besom"))
def broom(c, color):
    c.shadow(0.06, 0.012, 0.7, 0.05)
    R = _R(c, 9, (0, 0), (-0.08, 0.0))
    wood = c.pick(color, (0.70, 0.46, 0.24))
    straw = c.col((0.92, 0.74, 0.30))
    dk = scale(straw, 0.74)
    R.bar((0, 0.30), (0, 1.0), 0.055, 0.05, wood, lift=0.2)
    R.line(-0.012, 0.50, -0.012, 0.98, 0.012, WHITE, alpha=0.3)
    R.circle(0, 0.985, 0.03, wood, lift=0.1)
    R.poly([(-0.07, 0.46), (0.07, 0.46), (0.25, 0.04), (0.13, 0.0), (0.0, 0.035), (-0.13, 0.0), (-0.25, 0.04)], straw, lift=0.2)
    for k in range(9):
        t = -1 + k * 0.25
        R.line(t * 0.05, 0.43, t * 0.22, 0.035, 0.012, dk, alpha=0.6)
    R.poly([(-0.25, 0.04), (-0.215, 0.0), (-0.20, 0.06), (-0.15, 0.01), (-0.12, 0.08)], dk, lift=0.0, alpha=0.5)
    R.poly([(-0.075, 0.47), (0.075, 0.47), (0.095, 0.37), (-0.095, 0.37)], scale(c.col((0.45, 0.42, 0.40)), 1.0), lift=0.2)
    R.line(-0.09, 0.425, 0.09, 0.425, 0.014, c.col((0.88, 0.25, 0.25)))
    R.line(-0.10, 0.39, 0.10, 0.39, 0.014, c.col((0.88, 0.25, 0.25)))


# ---------------------------------------------------------------- bucket

@prop("bucket", aspect=0.88, place="table", nominal=0.28, fill=0.92, category="tools", words=("pail", "balti"))
def bucket(c, color):
    c.shadow(0.0, 0.01, 0.85, 0.06)
    col = c.pick(color, (0.25, 0.58, 0.88))
    steel = _steel(c, 0.85)
    foam = c.col((0.96, 0.98, 1.0))
    c.arc(0, 0.62, 0.40, 8, 172, 0.035, scale(steel, 0.8), ry=0.34)                  # handle
    c.poly([(-0.38, 0.62), (0.38, 0.62), (0.28, 0.03), (-0.28, 0.03)], col, lift=0.2)
    c.ellipse(0, 0.03, 0.28, 0.035, scale(col, 0.8), lift=0.05)
    c.poly([(-0.345, 0.45), (0.345, 0.45), (0.335, 0.39), (-0.335, 0.39)], mix(col, WHITE, 0.25), lift=0.05, alpha=0.8)
    c.poly([(-0.31, 0.25), (0.31, 0.25), (0.30, 0.20), (-0.30, 0.20)], scale(col, 0.82), lift=0.0, alpha=0.9)
    c.line(-0.30, 0.56, -0.22, 0.10, 0.028, WHITE, alpha=0.25)
    c.ellipse(0, 0.62, 0.395, 0.075, mix(col, WHITE, 0.2), lift=0.1)                  # rim
    c.ellipse(0, 0.62, 0.35, 0.052, c.col((0.55, 0.82, 0.98)), lift=0.1)               # water
    for u, v, r in ((-0.22, 0.68, 0.075), (-0.08, 0.72, 0.09), (0.09, 0.70, 0.085), (0.23, 0.675, 0.07), (0.0, 0.79, 0.065), (-0.14, 0.78, 0.045), (0.16, 0.78, 0.05)):
        c.circle(u, v, r, foam, lift=0.1)
        c.circle(u - r * 0.3, v + r * 0.3, r * 0.25, WHITE, lift=0, alpha=0.8)
    c.circle(0.30, 0.86, 0.025, c.col((0.8, 0.92, 1.0)), lift=0.05)
    c.circle(-0.30, 0.82, 0.02, c.col((0.8, 0.92, 1.0)), lift=0.05)
