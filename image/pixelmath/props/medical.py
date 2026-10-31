"""Props: dental and medical (tooth, toothbrush, dental chair, dentist, pills, stethoscope, syringe, thermometer)."""
import math

from .core import WHITE, _catmull, mix, prop, scale
from .people import HAIR, SKIN, _face, _figure


class _T:
    """Draws upright shapes through a rotation (about piv) followed by a shift, so a prop can lie diagonally."""

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

    def rrect(self, u, v, w, h, col, lift=0.10, alpha=1.0, r=0.03):
        """Rounded rectangle as a polygon (so it can rotate)."""
        r = min(r, w / 2, h / 2)
        pts = []
        for cu, cv, a0 in ((u + w / 2 - r, v + h / 2 - r, 0), (u - w / 2 + r, v + h / 2 - r, 90),
                           (u - w / 2 + r, v - h / 2 + r, 180), (u + w / 2 - r, v - h / 2 + r, 270)):
            for k in range(7):
                a = math.radians(a0 + 90.0 * k / 6)
                pts.append((cu + r * math.cos(a), cv + r * math.sin(a)))
        self.poly(pts, col, lift, alpha)

    def bar(self, a, b, w0, w1, col, lift=0.10, alpha=1.0):
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


def _steel(c, k=1.0):
    return scale(c.col((0.70, 0.74, 0.82)), k)


def _star(c, u, v, r, col, alpha=1.0):
    """A four-point sparkle."""
    pts = []
    for k in range(8):
        a = math.radians(90 + 45 * k)
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((u + rr * math.cos(a), v + rr * math.sin(a)))
    c.poly(pts, col, lift=0.0, alpha=alpha)


def _capsule(c, a, b, w, col1, col2):
    """Two-colour pill capsule from point a to point b."""
    c.path([a, b], w, col2, smooth=False)
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln * w / 2, dx / ln * w / 2
    c.circle(a[0], a[1], w / 2, col1, lift=0.10)
    c.poly([(a[0] + nx, a[1] + ny), (mid[0] + nx, mid[1] + ny), (mid[0] - nx, mid[1] - ny), (a[0] - nx, a[1] - ny)], col1, lift=0.10)
    c.line(mid[0] - dx / ln * 0.004, mid[1] - dy / ln * 0.004, mid[0] + dx / ln * 0.004, mid[1] + dy / ln * 0.004, w * 0.95, scale(col2, 0.7), alpha=0.6)
    # glossy highlight along the upper side
    hx, hy = -dy / ln, dx / ln
    if hy < 0:
        hx, hy = -hx, -hy
    off = w * 0.22
    c.line(a[0] + hx * off + dx * 0.10, a[1] + hy * off + dy * 0.10, b[0] + hx * off - dx * 0.10, b[1] + hy * off - dy * 0.10, w * 0.14, WHITE, alpha=0.5)


def _tablet(c, u, v, r, col, ang=0.0, groove=True):
    c.circle(u, v, r, col, lift=0.12)
    if groove:
        a = math.radians(ang)
        c.line(u - r * 0.8 * math.cos(a), v - r * 0.8 * math.sin(a), u + r * 0.8 * math.cos(a), v + r * 0.8 * math.sin(a), r * 0.13, scale(col, 0.72), alpha=0.8)
    c.ellipse(u - r * 0.35, v + r * 0.38, r * 0.30, r * 0.16, WHITE, angle=30, lift=0, alpha=0.5)


# ---------------------------------------------------------------- tooth

@prop("tooth", aspect=0.95, place="table", nominal=0.34, category="dental", words=("molar", "teeth", "enamel", "toothache", "incisor"))
def tooth(c, color):
    c.shadow(0.0, 0.015, 0.62, 0.07)
    base = c.pick(color, (0.99, 0.99, 0.97))
    right = [(0.0, 0.85), (0.14, 0.93), (0.27, 0.955), (0.38, 0.89), (0.435, 0.75), (0.415, 0.58), (0.345, 0.44),
             (0.29, 0.30), (0.255, 0.15), (0.20, 0.035), (0.125, 0.04), (0.095, 0.19), (0.055, 0.32), (0.0, 0.36)]
    left = [(-u, v) for u, v in reversed(right[1:-1])]
    outline = _catmull(right + left, 6, True)
    edge = scale(mix(base, c.col((0.45, 0.60, 0.82)), 0.45), 0.92)
    c.poly(outline, edge, lift=0.0)
    inner = [(u * 0.93, 0.50 + (v - 0.50) * 0.95 + (0.0 if v > 0.4 else 0.0)) for u, v in outline]
    c.poly(inner, base, lift=0.10)
    # roots a touch warmer, crown line, fissures
    c.path([(-0.34, 0.43), (-0.16, 0.39), (0.0, 0.41), (0.16, 0.39), (0.34, 0.43)], 0.014, scale(mix(base, c.col((0.8, 0.7, 0.5)), 0.4), 0.9), alpha=0.7)
    c.path([(-0.21, 0.88), (-0.14, 0.76), (0.0, 0.70), (0.16, 0.76), (0.22, 0.88)], 0.014, scale(base, 0.80), alpha=0.8, smooth=True)
    c.path([(0.0, 0.70), (0.0, 0.58)], 0.014, scale(base, 0.80), alpha=0.8, smooth=False)
    # gloss
    c.ellipse(-0.25, 0.72, 0.055, 0.17, WHITE, angle=14, lift=0, alpha=0.85)
    c.circle(-0.20, 0.52, 0.026, WHITE, lift=0, alpha=0.8)
    c.ellipse(0.28, 0.62, 0.03, 0.10, scale(base, 0.86), angle=-10, lift=0, alpha=0.5)
    _star(c, 0.44, 0.98, 0.11, c.col((0.55, 0.86, 1.0)))
    _star(c, 0.44, 0.98, 0.075, WHITE)
    _star(c, 0.30, 1.0, 0.04, c.col((0.55, 0.86, 1.0)))


# ---------------------------------------------------------------- toothbrush

def _draw_paste_tube(R, c):
    white = c.col((0.97, 0.98, 1.0))
    band = c.col((0.88, 0.22, 0.28))
    teal = c.col((0.20, 0.62, 0.80))
    R.rrect(0.0, 0.32, 0.22, 0.56, white, lift=0.10, r=0.03)             # body
    R.rect(0.0, 0.14, 0.222, 0.12, teal, lift=0.08)
    R.rect(0.0, 0.40, 0.222, 0.10, band, lift=0.08)
    R.circle(0.0, 0.40, 0.03, WHITE, lift=0)
    R.poly([(-0.11, 0.60), (0.11, 0.60), (0.09, 0.64), (-0.09, 0.64)], scale(white, 0.9), lift=0.08)
    R.rect(0.0, 0.665, 0.19, 0.045, scale(white, 0.82), lift=0.05)         # crimped end
    for k in range(5):
        R.line(-0.08 + k * 0.04, 0.645, -0.08 + k * 0.04, 0.685, 0.008, scale(white, 0.62), alpha=0.8)
    R.poly([(-0.07, 0.02), (0.07, 0.02), (0.09, -0.03), (-0.09, -0.03)], scale(white, 0.9), lift=0.0)   # cap
    R.line(-0.07, 0.55, -0.07, 0.20, 0.022, WHITE, alpha=0.5)


@prop("toothbrush", aspect=1.25, place="table", nominal=0.3, category="dental", words=("toothpaste", "oralcare", "brushing", "toothbrushes"))
def toothbrush(c, color):
    c.shadow(0.0, 0.02, 1.05, 0.06)
    # toothpaste tube lying behind, nozzle end to the left
    _draw_paste_tube(_T(c, 84, (0, 0), (0.07, 0.15)), c)
    # brush lying diagonally
    R = _T(c, -40, (0, 0), (-0.10, 0.00))
    body = c.pick(color, (0.22, 0.52, 0.92))
    white = c.col((0.97, 0.98, 1.0))
    R.poly([(-0.058, 0.06), (-0.04, 0.0), (0.04, 0.0), (0.058, 0.06), (0.068, 0.30), (0.060, 0.55), (0.040, 0.72),
            (-0.040, 0.72), (-0.060, 0.55), (-0.068, 0.30)], body, lift=0.14)
    R.rrect(0.0, 0.32, 0.085, 0.30, white, lift=0.06, r=0.03)
    for k in range(5):
        R.line(-0.036, 0.22 + k * 0.05, 0.036, 0.22 + k * 0.05, 0.010, scale(body, 0.82), alpha=0.7)
    R.circle(0.0, 0.045, 0.016, scale(body, 0.55), lift=0)
    R.line(-0.050, 0.10, -0.043, 0.62, 0.014, WHITE, alpha=0.35)
    R.poly([(-0.038, 0.70), (0.038, 0.70), (0.050, 0.78), (-0.050, 0.78)], scale(body, 0.95), lift=0.10)
    R.rrect(0.0, 0.93, 0.20, 0.30, scale(body, 0.88), lift=0.08, r=0.06)
    R.rrect(0.0, 0.93, 0.165, 0.265, scale(body, 0.62), lift=0.0, r=0.05)
    for row in range(6):
        for col in range(3):
            u, v = -0.05 + col * 0.05, 0.825 + row * 0.042
            tc = white if (row + col) % 2 == 0 else c.col((0.36, 0.72, 1.0))
            R.rrect(u, v, 0.043, 0.036, tc, lift=0.1, r=0.012)
    paste = [(-0.07, 0.84), (0.05, 0.92), (-0.04, 1.00), (0.04, 1.06)]
    R.path(paste, 0.060, c.col((0.2, 0.55, 0.85)), smooth=True)
    R.path(paste, 0.048, white, smooth=True)
    R.path([(u - 0.01, v + 0.012) for u, v in paste], 0.010, c.col((0.55, 0.80, 1.0)), smooth=True, alpha=0.9)


# ---------------------------------------------------------------- dental chair

@prop("dentalchair", aspect=1.6, place="ground", nominal=0.4, fill=1.0, category="dental", words=("dentalchair",))
def dentalchair(c, color):
    c = c.sub(0.05, 0.0, 1.0)
    c.shadow(-0.02, 0.01, 1.55, 0.06)
    pad = c.pick(color, (0.20, 0.62, 0.78))
    dark = c.col((0.27, 0.30, 0.38))
    steel = _steel(c)
    metal = c.col((0.86, 0.88, 0.93))
    # lamp pole, articulated arm and lamp head
    c.ellipse(0.72, 0.025, 0.12, 0.03, dark, lift=0.1)
    c.rect(0.72, 0.46, 0.05, 0.88, metal, r=0.02, lift=0.14)
    arm = [(0.72, 0.90), (0.40, 0.985), (0.05, 0.965), (-0.30, 0.95)]
    c.path(arm, 0.04, steel, smooth=True)
    c.path([(u, v + 0.008) for u, v in arm], 0.012, WHITE, alpha=0.4, smooth=True)
    for q in arm:
        c.circle(q[0], q[1], 0.030, dark, lift=0.1)
    # lamp: yoke, dish and light cone
    c.poly([(-0.30, 0.93), (-0.40, 0.88), (-0.20, 0.88)], c.col((1.0, 0.97, 0.72)), lift=0.0, alpha=0.0)
    c.poly([(-0.50, 0.86), (-0.12, 0.86), (-0.20, 0.58), (-0.42, 0.58)], c.col((1.0, 0.97, 0.72)), lift=0.0, alpha=0.18)
    c.glow(-0.31, 0.76, 0.34, c.col((1.0, 0.96, 0.7)), 0.28)
    c.line(-0.30, 0.95, -0.31, 0.90, 0.025, dark)
    c.ellipse(-0.31, 0.875, 0.17, 0.055, metal, lift=0.14)
    c.ellipse(-0.31, 0.862, 0.14, 0.036, c.col((1.0, 0.97, 0.72)), lift=0.0)
    c.ellipse(-0.31, 0.862, 0.075, 0.018, WHITE, lift=0.0, alpha=0.8)
    # instrument tray on a swing arm
    c.path([(0.72, 0.60), (0.62, 0.62)], 0.03, steel, smooth=False)
    c.rect(0.55, 0.635, 0.36, 0.035, metal, r=0.01, lift=0.12)
    c.rect(0.55, 0.610, 0.32, 0.025, dark, lift=0.05)
    for k, (du, ln) in enumerate(((-0.11, 0.17), (-0.04, 0.15), (0.03, 0.18))):
        a_ = math.radians((-6, 4, -2)[k])
        c.line(0.55 + du, 0.655, 0.55 + du + ln * math.sin(a_), 0.655 + ln * math.cos(a_), 0.012, steel)
    c.circle(0.55 - 0.11 + 0.17 * math.sin(math.radians(-6)), 0.655 + 0.17 * math.cos(math.radians(-6)), 0.025, metal, lift=0.1)
    c.rect(0.64, 0.675, 0.065, 0.065, c.col((0.88, 0.45, 0.45)), r=0.01, lift=0.08)
    # base, column and hydraulic cylinder
    c.rect(-0.05, 0.04, 0.60, 0.07, dark, r=0.03, lift=0.12)
    c.rect(-0.05, 0.075, 0.30, 0.045, scale(dark, 1.25), r=0.02, lift=0.1)
    c.rect(-0.05, 0.20, 0.13, 0.24, steel, r=0.015, lift=0.14)
    c.rect(-0.05, 0.31, 0.085, 0.15, metal, r=0.012, lift=0.12)
    c.line(-0.075, 0.12, -0.075, 0.38, 0.014, WHITE, alpha=0.5)
    c.rect(-0.04, 0.37, 0.56, 0.05, dark, r=0.015, lift=0.1)
    # footrest, seat, backrest (thick padded cushions)
    c.path([(0.20, 0.45), (0.54, 0.35)], 0.14, scale(pad, 0.88), smooth=False)
    c.path([(0.20, 0.50), (0.54, 0.40)], 0.020, WHITE, alpha=0.25, smooth=False)
    c.path([(0.575, 0.37), (0.60, 0.28)], 0.075, scale(dark, 1.1), smooth=False)
    c.path([(-0.26, 0.485), (0.24, 0.46)], 0.20, pad, smooth=False)
    c.line(-0.24, 0.565, 0.20, 0.545, 0.018, WHITE, alpha=0.30)
    c.line(-0.22, 0.395, 0.22, 0.375, 0.012, scale(pad, 0.65), alpha=0.5)
    c.path([(-0.10, 0.65), (0.14, 0.64)], 0.05, scale(dark, 1.15), smooth=False)       # arm rest
    c.line(0.0, 0.625, 0.0, 0.54, 0.03, dark)
    c.path([(-0.20, 0.50), (-0.58, 0.72)], 0.25, pad, smooth=False)
    c.path([(-0.20, 0.625), (-0.57, 0.835)], 0.018, WHITE, alpha=0.30, smooth=False)
    c.path([(-0.22, 0.385), (-0.58, 0.595)], 0.012, scale(pad, 0.65), alpha=0.5, smooth=False)
    for k in range(3):
        t = 0.28 + k * 0.24
        pu, pv = -0.20 - 0.38 * t, 0.50 + 0.22 * t
        c.line(pu - 0.045, pv - 0.075, pu + 0.045, pv + 0.075, 0.010, scale(pad, 0.70), alpha=0.6)
    # headrest
    c.line(-0.60, 0.74, -0.66, 0.77, 0.06, dark)
    c.path([(-0.70, 0.69), (-0.77, 0.83)], 0.14, scale(pad, 1.10), smooth=False)
    c.path([(-0.73, 0.82), (-0.765, 0.865)], 0.02, WHITE, alpha=0.35, smooth=False)


# ---------------------------------------------------------------- dentist

@prop("dentist", aspect=0.6, place="ground", nominal=0.5, category="people", words=("orthodontist", "dentistry", "dantvaid"))
def dentist(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    scrub = c.pick(color, (0.55, 0.78, 0.92))
    coat = c.col((0.98, 0.99, 1.0))
    skin = c.col(c.rng.choice(SKIN))
    hair = c.col(c.rng.choice(HAIR))
    _figure(c, coat, scale(scrub, 0.92), skin=skin, hair=hair, style="short", arms="up")
    # open white coat: scrubs top shows in the centre
    c.poly([(-0.07, 0.785), (0.07, 0.785), (0.055, 0.46), (-0.055, 0.46)], scrub, lift=0.10)
    c.poly([(-0.065, 0.785), (0.0, 0.70), (0.065, 0.785)], scale(scrub, 0.8), lift=0.0)
    c.line(-0.07, 0.785, -0.055, 0.46, 0.008, c.col((0.80, 0.84, 0.92)))
    c.line(0.07, 0.785, 0.055, 0.46, 0.008, c.col((0.80, 0.84, 0.92)))
    c.rect(0.10, 0.60, 0.055, 0.045, c.col((0.88, 0.91, 0.96)), r=0.008, lift=0)                # pocket
    c.line(0.10, 0.62, 0.10, 0.66, 0.010, c.col((0.85, 0.25, 0.28)))
    c.circle(-0.10, 0.64, 0.03, c.col((0.30, 0.62, 0.90)), lift=0.1)                            # tooth badge
    c.circle(-0.10, 0.64, 0.016, WHITE, lift=0)
    # right hand holds a dental mirror, raised
    hu, hv = 0.12, 0.605
    c.circle(hu, hv, 0.036, skin, lift=0.05)
    c.line(hu + 0.01, hv + 0.02, hu + 0.10, hv + 0.17, 0.014, c.col((0.72, 0.75, 0.82)))
    c.circle(hu + 0.115, hv + 0.195, 0.035, c.col((0.72, 0.76, 0.84)), lift=0.1)
    c.circle(hu + 0.115, hv + 0.195, 0.026, c.col((0.85, 0.94, 1.0)), lift=0.1)
    c.ellipse(hu + 0.105, hv + 0.205, 0.008, 0.014, WHITE, angle=40, lift=0, alpha=0.9)
    # head: cap, loupes, headlamp, mask
    c.ellipse(0, 0.955, 0.093, 0.052, scrub, lift=0.10)
    c.rect(0, 0.93, 0.182, 0.020, scale(scrub, 0.85), lift=0.05)
    c.circle(0.0, 0.945, 0.019, c.col((0.30, 0.32, 0.40)), lift=0.1)
    c.circle(0.0, 0.945, 0.011, c.col((1.0, 0.96, 0.60)), lift=0)
    c.glow(0.0, 0.945, 0.07, c.col((1.0, 0.95, 0.6)), 0.5)
    mask = c.col((0.74, 0.90, 0.92))
    c.poly([(-0.075, 0.862), (0.075, 0.862), (0.068, 0.82), (0.04, 0.795), (-0.04, 0.795), (-0.068, 0.82)], mask, lift=0.06)
    for k in range(3):
        c.line(-0.060, 0.846 - k * 0.016, 0.060, 0.846 - k * 0.016, 0.005, scale(mask, 0.80), alpha=0.8)
    c.line(-0.075, 0.855, -0.093, 0.885, 0.005, c.col((0.80, 0.90, 0.92)))
    c.line(0.075, 0.855, 0.093, 0.885, 0.005, c.col((0.80, 0.90, 0.92)))
    frame = c.col((0.18, 0.22, 0.30))
    for sgn in (-1, 1):
        c.circle(sgn * 0.036, 0.885, 0.027, c.col((0.60, 0.82, 1.0)), lift=0.0, alpha=0.45)
        c.ring(sgn * 0.036, 0.885, 0.027, 0.008, frame)
    c.line(-0.009, 0.89, 0.009, 0.89, 0.007, frame)


# ---------------------------------------------------------------- pills

@prop("pills", aspect=1.4, place="table", nominal=0.28, fill=0.92, category="health", words=("capsule", "medication", "drugs", "dawai", "goli", "pill"))
def pills(c, color):
    c.shadow(0.0, 0.02, 1.35, 0.07)
    amber = c.pick(color, (0.96, 0.55, 0.12))
    white = c.col((0.98, 0.98, 1.0))
    # blister pack behind
    R = _T(c, 8, (0.45, 0.45), (0.04, 0.12))
    R.rrect(0.45, 0.46, 0.42, 0.56, c.col((0.80, 0.83, 0.90)), lift=0.12, r=0.03)
    R.rrect(0.45, 0.46, 0.38, 0.52, c.col((0.90, 0.92, 0.97)), lift=0.12, r=0.02)
    cols = [(0.92, 0.28, 0.30), (0.98, 0.78, 0.22), (0.30, 0.65, 0.95)]
    for row in range(4):
        for col in range(2):
            u, v = 0.37 + col * 0.16, 0.28 + row * 0.13
            R.ellipse(u, v, 0.056, 0.047, c.col((0.74, 0.88, 1.0)), lift=0.15, alpha=0.9)
            R.ellipse(u, v, 0.038, 0.030, c.col(cols[(row + col) % 3]), lift=0.1)
            R.ellipse(u - 0.02, v + 0.02, 0.014, 0.009, WHITE, lift=0, alpha=0.8)
    # open bottle
    c.rect(-0.46, 0.585, 0.20, 0.10, scale(amber, 0.95), r=0.02, lift=0.12)
    c.rect(-0.46, 0.29, 0.36, 0.56, amber, r=0.06, lift=0.14)
    c.ellipse(-0.46, 0.66, 0.115, 0.035, scale(amber, 1.12), lift=0.1)
    c.ellipse(-0.46, 0.66, 0.085, 0.022, c.col((0.30, 0.15, 0.06)), lift=0)
    c.ellipse(-0.46, 0.66, 0.100, 0.028, scale(amber, 0.82), lift=0, alpha=0.0)
    c.rect(-0.46, 0.30, 0.375, 0.30, white, r=0.02, lift=0.04)
    c.rect(-0.46, 0.40, 0.375, 0.035, c.col((0.85, 0.18, 0.22)), lift=0)
    c.rect(-0.46, 0.345, 0.07, 0.07, c.col((0.20, 0.62, 0.45)), r=0.01, lift=0)
    c.rect(-0.46, 0.345, 0.044, 0.014, WHITE, lift=0)
    c.rect(-0.46, 0.345, 0.014, 0.044, WHITE, lift=0)
    for k in range(3):
        c.line(-0.60 + 0.0, 0.24 - k * 0.04, -0.60 + (0.25 if k < 2 else 0.17), 0.24 - k * 0.04, 0.012, c.col((0.55, 0.58, 0.68)))
    c.line(-0.60, 0.20, -0.575, 0.52, 0.03, WHITE, alpha=0.30)
    # cap, lying on its side in front of the bottle
    capc = c.col((0.97, 0.97, 0.99))
    R2 = _T(c, 12, (-0.20, 0.08), (0.0, 0.0))
    R2.rrect(-0.22, 0.10, 0.20, 0.17, capc, lift=0.12, r=0.03)
    R2.ellipse(-0.12, 0.10, 0.032, 0.085, scale(capc, 0.80), lift=0.05)
    R2.ellipse(-0.12, 0.10, 0.020, 0.062, c.col((0.62, 0.66, 0.76)), lift=0.0)
    for k in range(4):
        R2.line(-0.29 + k * 0.045, 0.03, -0.29 + k * 0.045, 0.17, 0.006, scale(capc, 0.82), alpha=0.7)
    # spilled capsules and tablets
    white2 = white
    _capsule(c, (0.02, 0.14), (0.17, 0.09), 0.09, c.col((0.90, 0.22, 0.26)), white2)
    _capsule(c, (0.26, 0.07), (0.41, 0.12), 0.085, c.col((0.25, 0.66, 0.92)), c.col((0.98, 0.84, 0.25)))
    _capsule(c, (0.30, 0.22), (0.44, 0.17), 0.085, c.col((0.30, 0.75, 0.45)), white2)
    _capsule(c, (0.50, 0.075), (0.65, 0.045), 0.08, c.col((0.95, 0.60, 0.15)), c.col((0.95, 0.60, 0.15)))
    _tablet(c, 0.52, 0.19, 0.045, c.col((0.98, 0.84, 0.30)), 0)
    _tablet(c, 0.67, 0.14, 0.045, c.col((0.96, 0.50, 0.60)), -30)
    _tablet(c, 0.20, 0.04, 0.04, c.col((0.45, 0.78, 0.95)), 60)
    _tablet(c, 0.62, 0.30, 0.04, c.col((0.80, 0.55, 0.92)), 10)


# ---------------------------------------------------------------- stethoscope

@prop("stethoscope", aspect=1.0, place="table", nominal=0.3, fill=0.95, category="health", words=("steth",))
def stethoscope(c, color):
    c = c.sub(0.07, 0.0, 0.9)
    c.shadow(-0.03, 0.015, 1.05, 0.06)
    tube = c.pick(color, (0.20, 0.24, 0.36))
    steel = _steel(c, 1.0)
    dark_steel = _steel(c, 0.72)
    # binaural springs and ear tubes
    for sgn in (-1, 1):
        left = [(0.0, 0.58), (sgn * 0.07, 0.68), (sgn * 0.20, 0.78), (sgn * 0.30, 0.89), (sgn * 0.31, 0.99)]
        c.path(left, 0.040, dark_steel, smooth=True)
        c.path(left, 0.030, steel, smooth=True)
        c.path([(u - 0.008 * sgn, v + 0.005) for u, v in left], 0.008, WHITE, alpha=0.6, smooth=True)
        c.ellipse(sgn * 0.31, 1.0, 0.032, 0.026, c.col((0.15, 0.17, 0.22)), lift=0.1)               # ear tip
    # Y junction
    c.circle(0.0, 0.57, 0.052, steel, lift=0.14)
    c.circle(0.0, 0.57, 0.020, dark_steel, lift=0.0)
    # tubing in a big loop
    loop = [(0.0, 0.55), (0.12, 0.46), (0.36, 0.40), (0.50, 0.26), (0.42, 0.10), (0.20, 0.035), (-0.08, 0.05),
            (-0.30, 0.14), (-0.40, 0.30), (-0.33, 0.44), (-0.40, 0.42)]
    loop = [(0.0, 0.55), (0.14, 0.44), (0.40, 0.36), (0.52, 0.22), (0.42, 0.07), (0.16, 0.03), (-0.14, 0.06),
            (-0.36, 0.17), (-0.46, 0.34)]
    c.path(loop, 0.055, scale(tube, 0.75), smooth=True)
    c.path(loop, 0.046, tube, smooth=True)
    c.path([(u - 0.012, v + 0.010) for u, v in loop], 0.011, WHITE, alpha=0.35, smooth=True)
    # chest piece
    cu, cv = -0.52, 0.42
    c.path([(-0.46, 0.34), (cu, cv)], 0.050, scale(steel, 0.8), smooth=False)
    c.circle(cu, cv, 0.17, c.col((0.45, 0.50, 0.60)), lift=0.14)
    c.circle(cu, cv, 0.145, steel, lift=0.16)
    c.circle(cu, cv, 0.112, c.col((0.30, 0.34, 0.42)), lift=0.12)
    c.circle(cu, cv, 0.096, c.col((0.78, 0.82, 0.90)), lift=0.14)
    c.ellipse(cu - 0.04, cv + 0.05, 0.03, 0.016, WHITE, angle=40, lift=0, alpha=0.7)


# ---------------------------------------------------------------- syringe

@prop("syringe", aspect=1.0, place="table", nominal=0.3, fill=0.95, category="health", words=("injection", "vaccine", "vaccination", "teeka", "vial", "jab"))
def syringe(c, color):
    c.shadow(0.0, 0.02, 1.0, 0.06)
    c0 = c
    liquid = c.pick(color, (0.20, 0.72, 0.80))
    steel = _steel(c)
    glass = c.col((0.88, 0.95, 1.0))
    # vial beside the syringe
    vu = 0.46
    c.rect(vu, 0.20, 0.25, 0.34, c.col((0.80, 0.92, 0.98)), r=0.04, lift=0.12, alpha=0.95)
    c.rect(vu, 0.13, 0.215, 0.18, liquid, r=0.03, lift=0.14)
    c.rect(vu, 0.24, 0.25, 0.14, c.col((0.97, 0.97, 0.99)), lift=0.04)
    c.rect(vu, 0.24, 0.25, 0.012, c.col((0.85, 0.22, 0.25)), lift=0)
    c.rect(vu, 0.395, 0.17, 0.06, c.col((0.22, 0.26, 0.34)), r=0.012, lift=0.1)
    c.rect(vu, 0.437, 0.19, 0.035, c.col((0.88, 0.20, 0.25)), r=0.01, lift=0.12)
    c.line(vu - 0.095, 0.10, vu - 0.095, 0.34, 0.016, WHITE, alpha=0.5)
    # syringe lying diagonally
    c = c0.sub(-0.14, 0.05, 0.86)
    R = _T(c, 44, (0, 0.5), (-0.14, 0.02))
    R.rect(0, 0.15, 0.036, 0.46, steel, lift=0.18)                                              # plunger rod
    R.rect(0, 0.15, 0.10, 0.012, scale(steel, 0.85), lift=0.1)                                  # plunger cross rib
    R.rect(0, 0.15, 0.012, 0.46, scale(steel, 0.80), lift=0.1)
    R.ellipse(0, -0.09, 0.075, 0.025, c.col((0.82, 0.87, 0.95)), lift=0.10)                     # thumb rest
    R.rrect(0, 0.40, 0.098, 0.060, c.col((0.20, 0.22, 0.28)), lift=0.10, r=0.02)                # stopper
    R.rrect(0, 0.62, 0.115, 0.52, glass, lift=0.10, r=0.03)                                     # barrel
    R.rrect(0, 0.575, 0.092, 0.34, liquid, lift=0.16, r=0.02)                                   # liquid
    R.rrect(0, 0.63, 0.115, 0.52, glass, lift=0.0, r=0.03, alpha=0.18)
    R.rect(0, 0.88, 0.17, 0.028, c.col((0.82, 0.87, 0.95)), lift=0.10)                          # finger flange
    R.rect(0, 0.365, 0.18, 0.028, c.col((0.82, 0.87, 0.95)), lift=0.10)
    for k in range(9):
        ln = 0.04 if k % 2 == 0 else 0.026
        R.line(0.058 - ln, 0.44 + k * 0.045, 0.058, 0.44 + k * 0.045, 0.007, c.col((0.20, 0.24, 0.34)))
    R.line(-0.040, 0.40, -0.040, 0.84, 0.016, WHITE, alpha=0.55)
    R.poly([(-0.04, 0.88), (0.04, 0.88), (0.022, 0.96), (-0.022, 0.96)], glass, lift=0.10)       # tip cone
    R.rect(0, 0.99, 0.060, 0.050, c.col((0.30, 0.55, 0.90)), lift=0.12)                        # needle hub
    R.rect(0, 1.14, 0.014, 0.28, c.col((0.92, 0.94, 0.98)), lift=0.1)                           # needle
    R.poly([(-0.007, 1.28), (0.007, 1.28), (0.0, 1.34)], c.col((0.92, 0.94, 0.98)), lift=0.1)
    dx, dy = R.p(0.0, 1.38)
    c.poly([(dx - 0.025, dy - 0.012), (dx + 0.025, dy - 0.012), (dx, dy + 0.05)], liquid, lift=0.0, alpha=0.0)
    c.poly([(dx - 0.012, dy - 0.014), (dx + 0.012, dy - 0.014), (dx + 0.002, dy + 0.022)], liquid, lift=0.0)
    c.circle(dx, dy - 0.03, 0.017, liquid, lift=0.1)


# ---------------------------------------------------------------- thermometer

@prop("thermometer", aspect=0.75, place="table", nominal=0.3, fill=0.92, category="health", words=("fever", "temperature", "thermo"))
def thermometer(c, color):
    c.shadow(0.0, 0.02, 0.85, 0.06)
    merc = c.pick(color, (0.90, 0.16, 0.20))
    glass = c.col((0.93, 0.97, 1.0))
    R = _T(c, -40, (0, 0.5), (0.02, -0.02))
    R.rrect(0, 0.5, 0.165, 1.06, c.col((0.60, 0.70, 0.84)), lift=0.12, r=0.06)               # rim
    R.rrect(0, 0.5, 0.145, 1.04, glass, lift=0.10, r=0.055)
    R.circle(0, 0.04, 0.095, c.col((0.60, 0.70, 0.84)), lift=0.1)
    R.circle(0, 0.04, 0.080, glass, lift=0.1)
    R.rrect(0.0, 0.70, 0.036, 0.70, c.col((0.80, 0.85, 0.92)), lift=0.0, r=0.012)           # capillary
    R.circle(0, 0.04, 0.060, merc, lift=0.14)                                                   # bulb of mercury
    R.rrect(0.0, 0.35, 0.036, 0.66, merc, lift=0.12, r=0.012)
    for k in range(13):
        v = 0.50 + k * 0.034
        long_ = k % 2 == 0
        R.line(0.034, v, 0.034 + (0.034 if long_ else 0.018), v, 0.007, c.col((0.20, 0.24, 0.34)))
    for k in range(4):
        R.line(-0.025, 0.55 + k * 0.10, -0.050, 0.55 + k * 0.10, 0.007, c.col((0.20, 0.24, 0.34)), alpha=0.6)
    R.line(-0.055, 0.20, -0.055, 0.95, 0.016, WHITE, alpha=0.85)
    R.circle(0.0, 0.98, 0.012, c.col((0.60, 0.70, 0.84)), lift=0.0, alpha=0.7)
