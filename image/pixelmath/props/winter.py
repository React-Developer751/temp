"""Props: winter sports (skier, skater, snowboard, skis, ice skate, snowman, sled, hockey sticks)."""
import math

from .core import WHITE, _catmull, mix, prop, scale  # noqa: F401
from .people import HAIR, SKIN, _face

SNOW = (0.98, 0.99, 1.0)
SNOW_SH = (0.76, 0.84, 0.95)
SNOW_ED = (0.52, 0.62, 0.80)
ICE = (0.80, 0.91, 0.98)
ICE_ED = (0.52, 0.70, 0.88)
STEEL = (0.80, 0.84, 0.90)
STEEL_ED = (0.36, 0.41, 0.52)
DARK = (0.13, 0.14, 0.19)


# ------------------------------------------------------------------------------------------------ helpers
def _xf(pts, org=(0.0, 0.0), ang=0.0, k=1.0):
    """Local points -> unit space: scale by k, rotate ccw by ang degrees, move to org."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(org[0] + (u * ca - v * sa) * k, org[1] + (u * sa + v * ca) * k) for u, v in pts]


def _box(u, v, w, h):
    return [(u - w / 2, v - h / 2), (u + w / 2, v - h / 2), (u + w / 2, v + h / 2), (u - w / 2, v + h / 2)]


def _pill(hw, v0, v1, cap, hw_top=None, n=10):
    """Outline of a board / ski: straight sides with elliptic ends."""
    hw_top = hw if hw_top is None else hw_top
    pts = []
    for i in range(n + 1):                                        # top cap, left to right
        t = math.pi - math.pi * i / n
        pts.append((hw_top * math.cos(t), v1 - cap + cap * math.sin(t)))
    for i in range(n + 1):                                        # bottom cap, right to left
        t = -math.pi * i / n
        pts.append((hw * math.cos(t), v0 + cap + cap * math.sin(t)))
    return pts


def _limb(c, pts, w, col, edge=None, smooth=False):
    if edge is not None:
        c.path(pts, w + 0.014, edge, smooth=smooth)
    c.path(pts, w, col, smooth=smooth)


def _mound(c, u, v, w, h, snow=SNOW):
    """A soft heap of snow that reads on a white background."""
    c.ellipse(u, v, w / 2 + 0.008, h / 2 + 0.008, c.col(SNOW_ED), lift=0.0)
    c.ellipse(u, v, w / 2, h / 2, c.col(SNOW_SH), lift=0.0)
    c.ellipse(u - w * 0.04, v + h * 0.10, w / 2 * 0.90, h / 2 * 0.80, c.col(snow), lift=0.04)
    c.ellipse(u - w * 0.22, v + h * 0.22, w * 0.12, h * 0.10, WHITE, lift=0.0, alpha=0.9)


def _sparkle(c, u, v, r, col=WHITE, alpha=0.9):
    c.poly([(u, v + r), (u + r * 0.22, v + r * 0.22), (u + r, v), (u + r * 0.22, v - r * 0.22),
            (u, v - r), (u - r * 0.22, v - r * 0.22), (u - r, v), (u - r * 0.22, v + r * 0.22)], col, lift=0.0, alpha=alpha)


def _ice_patch(c, u, v, w, h):
    c.ellipse(u, v, w / 2 + 0.008, h / 2 + 0.008, c.col(ICE_ED), lift=0.0)
    c.ellipse(u, v, w / 2, h / 2, c.col(ICE), lift=0.10)
    c.ellipse(u - w * 0.12, v + h * 0.12, w * 0.30, h * 0.20, WHITE, lift=0.0, alpha=0.55)


def _skate_boot(c, u, v, ang, k, boot):
    """Small figure skate; (u, v) is the ankle, the blade hangs about 0.13*k below."""
    def T(pts):
        return _xf(pts, (u, v), ang, k)
    edge = c.col(STEEL_ED)
    steel = c.col(STEEL)
    body = [(-0.050, 0.050), (0.048, 0.050), (0.052, -0.005), (0.115, -0.040), (0.128, -0.070), (0.105, -0.088),
            (-0.062, -0.088), (-0.062, -0.01)]
    c.poly(T([(a * 1.18, b * 1.18 + 0.004) for a, b in body]), edge, lift=0.0)
    c.poly(T([(-0.040, -0.088), (-0.020, -0.088), (-0.024, -0.118), (-0.044, -0.118)]), edge, lift=0.0)
    c.poly(T([(0.075, -0.088), (0.100, -0.088), (0.096, -0.118), (0.078, -0.118)]), edge, lift=0.0)
    c.path(T([(-0.100, -0.126), (0.140, -0.126), (0.176, -0.110), (0.182, -0.080)]), 0.034 * k, edge, smooth=False)
    c.path(T([(-0.100, -0.126), (0.140, -0.126), (0.176, -0.110), (0.182, -0.080)]), 0.018 * k, steel, smooth=False)
    c.poly(T(body), boot, lift=0.12)
    c.rect(*_xf([(0.0, 0.040)], (u, v), ang, k)[0], 0.12 * k, 0.026 * k, scale(boot, 0.82), r=0.01, lift=0.0)
    c.path(T([(0.02, 0.025), (0.085, -0.040)]), 0.012 * k, c.col((0.95, 0.95, 0.90)), smooth=False)
    c.path(T([(-0.05, -0.080), (0.11, -0.080)]), 0.016 * k, c.col((0.45, 0.30, 0.22)), smooth=False)


# ------------------------------------------------------------------------------------------------- skier
@prop("skier", aspect=1.25, place="ground", nominal=0.45, fill=1.0, category="winter",
      words=("skiing", "snowskiing", "slope", "downhill", "skiers"))
def skier(c, color):
    jacket = c.pick(color, (0.90, 0.25, 0.22))
    pants = c.col((0.16, 0.19, 0.32))
    dark = c.col(DARK)
    ski_a, ski_b = c.col((0.12, 0.30, 0.55)), c.col((0.22, 0.42, 0.68))
    skin = c.col(SKIN[1])
    yellow = c.col((0.99, 0.80, 0.16))
    c.shadow(0.0, 0.015, 1.25, 0.07, alpha=0.22)
    # snow spray behind the skis
    for (u, v, r, a) in ((-0.62, 0.07, 0.07, 0.95), (-0.72, 0.13, 0.05, 0.9), (-0.55, 0.14, 0.04, 0.9), (-0.80, 0.07, 0.035, 0.8)):
        c.circle(u, v, r + 0.008, c.col(SNOW_ED), lift=0.0, alpha=0.5 * a)
        c.circle(u, v, r, c.col(SNOW), lift=0.04, alpha=a)
    # skis
    for (dy, dx, col) in ((0.045, 0.045, ski_b), (0.0, 0.0, ski_a)):
        pts = [(-0.58 + dx, 0.034 + dy), (0.36 + dx, 0.034 + dy), (0.50 + dx, 0.044 + dy), (0.60 + dx, 0.095 + dy)]
        c.path(pts, 0.052, scale(col, 0.55))
        c.path(pts, 0.040, col)
        c.path([(-0.46 + dx, 0.046 + dy), (0.30 + dx, 0.046 + dy)], 0.010, WHITE, alpha=0.85, smooth=False)
    # poles: far one first (behind the body)
    pole = c.col((0.30, 0.33, 0.40))

    def pole_line(h, tip, col, w):
        c.line(h[0], h[1], tip[0], tip[1], w, col)
        t = 0.08 / math.hypot(h[0] - tip[0], h[1] - tip[1])
        bu, bv = tip[0] + (h[0] - tip[0]) * t, tip[1] + (h[1] - tip[1]) * t
        c.ellipse(bu, bv, 0.016, 0.040, c.col((0.8, 0.82, 0.88)), angle=-70, lift=0.0)
        c.circle(tip[0], tip[1], 0.010, dark, lift=0.0)
    pole_line((0.36, 0.70), (-0.60, 0.40), scale(pole, 0.85), 0.016)
    # boots and legs
    for (bu, bv, shade) in ((0.075, 0.185, 0.80), (0.0, 0.125, 1.0)):
        c.rect(bu, bv - 0.045, 0.20, 0.060, scale(dark, shade), r=0.02, lift=0.1)       # binding on the ski
        c.poly([(bu - 0.075, bv - 0.050), (bu + 0.085, bv - 0.050), (bu + 0.090, bv - 0.01), (bu + 0.03, bv + 0.03),
                (bu - 0.04, bv + 0.075), (bu - 0.075, bv + 0.075)], scale(dark, shade * 1.1), lift=0.1)
    _limb(c, [(0.075, 0.20), (0.26, 0.43), (-0.06, 0.59)], 0.115, scale(pants, 0.82), smooth=False)
    _limb(c, [(0.0, 0.15), (0.20, 0.40), (-0.12, 0.56)], 0.125, pants, smooth=False)
    c.circle(0.20, 0.40, 0.06, pants, lift=0.1)
    c.ellipse(0.215, 0.42, 0.028, 0.014, mix(pants, WHITE, 0.25), angle=50, lift=0.0, alpha=0.8)
    # far arm
    far = scale(jacket, 0.78)
    _limb(c, [(0.08, 0.79), (0.20, 0.68), (0.36, 0.70)], 0.072, far, smooth=False)
    c.circle(0.375, 0.70, 0.038, scale(dark, 1.0), lift=0.1)
    # torso: leaning forward in a tuck
    c.circle(-0.12, 0.58, 0.085, pants, lift=0.1)
    c.path([(-0.12, 0.60), (0.10, 0.79)], 0.215, jacket)
    c.path([(-0.07, 0.755), (0.06, 0.62)], 0.032, WHITE, alpha=0.88, smooth=False)
    c.path([(-0.145, 0.65), (0.03, 0.835)], 0.028, mix(jacket, WHITE, 0.45), alpha=0.7, smooth=False)
    # near pole, in front of the body, then the near arm
    pole_line((0.41, 0.65), (-0.62, 0.27), pole, 0.020)
    _limb(c, [(0.09, 0.80), (0.25, 0.65), (0.40, 0.65)], 0.082, jacket, smooth=False)
    c.circle(0.42, 0.65, 0.045, dark, lift=0.12)
    c.circle(0.405, 0.67, 0.016, mix(dark, WHITE, 0.25), lift=0.0)
    # neck gaiter and head
    c.ellipse(0.19, 0.845, 0.085, 0.05, jacket, angle=15, lift=0.05)
    c.ellipse(0.205, 0.945, 0.108, 0.098, yellow, lift=0.14)                                  # helmet
    c.ellipse(0.262, 0.905, 0.062, 0.074, skin, lift=0.06)                                    # face
    c.ellipse(0.215, 0.848, 0.065, 0.026, c.col((0.96, 0.96, 0.98)), lift=0.05)
    c.path([(0.285, 0.935), (0.14, 0.95), (0.105, 0.94)], 0.035, c.col((0.10, 0.12, 0.18)), smooth=False)   # strap
    c.ellipse(0.292, 0.934, 0.060, 0.050, c.col((0.12, 0.14, 0.20)), lift=0.0)                # goggle frame
    c.ellipse(0.296, 0.934, 0.050, 0.039, c.col((0.98, 0.62, 0.20)), lift=0.18)               # lens
    c.ellipse(0.285, 0.945, 0.020, 0.008, WHITE, angle=15, lift=0.0, alpha=0.7)
    c.arc(0.205, 0.945, 0.098, 110, 160, 0.014, mix(yellow, WHITE, 0.6), alpha=0.9)
    c.circle(0.225, 1.025, 0.018, c.col((0.96, 0.96, 0.98)), lift=0.05)                      # bobble


# ------------------------------------------------------------------------------------------------ skater
@prop("skater", aspect=1.05, place="ground", nominal=0.45, fill=1.0, category="winter",
      words=("skating", "iceskating", "figureskating", "skaterink", "skaters", "ballerina"))
def skater(c, color):
    rng = c.rng
    dress = c.pick(color, (0.88, 0.26, 0.48))
    skin = c.col(rng.choice(SKIN[:3]))
    hair = c.col(rng.choice(HAIR[:4]))
    tights = c.col((0.93, 0.78, 0.70))
    boot = c.col((0.98, 0.97, 0.97))
    scarf = c.col((0.98, 0.84, 0.22))
    hat = c.col((0.30, 0.52, 0.86))
    c.shadow(0.0, 0.02, 0.95, 0.07, alpha=0.18)
    _ice_patch(c, 0.0, 0.04, 1.0, 0.11)
    c.arc(-0.16, 0.05, 0.28, 195, 245, 0.008, c.col((0.60, 0.76, 0.90)), alpha=0.8, ry=0.03)
    c.arc(0.20, 0.035, 0.26, 285, 345, 0.008, c.col((0.60, 0.76, 0.90)), alpha=0.8, ry=0.03)
    # scarf tail flowing behind
    c.path([(0.0, 0.80), (-0.17, 0.72), (-0.33, 0.64)], 0.05, scale(scarf, 0.88))
    c.poly([(-0.33, 0.66), (-0.40, 0.60), (-0.34, 0.585), (-0.30, 0.62)], scale(scarf, 0.88), lift=0.0)
    # free leg (behind the standing one) and its skate
    _limb(c, [(0.06, 0.47), (0.22, 0.34), (0.35, 0.25)], 0.082, scale(tights, 0.9), smooth=False)
    _skate_boot(c, 0.375, 0.24, -30, 1.0, boot)
    # standing leg and skate
    _limb(c, [(0.01, 0.47), (-0.02, 0.32), (-0.05, 0.19)], 0.092, tights, smooth=False)
    _skate_boot(c, -0.06, 0.145, 0, 1.0, boot)
    # skirt and bodice
    c.poly([(-0.095, 0.585), (0.095, 0.585), (0.235, 0.40), (-0.235, 0.40)], dress, lift=0.12)
    c.ellipse(0.0, 0.405, 0.235, 0.034, scale(dress, 0.92), lift=0.1)
    for k in range(-2, 3):
        c.line(k * 0.045, 0.56, k * 0.075, 0.41, 0.006, scale(dress, 0.82), alpha=0.8)
    c.arc(0.0, 0.402, 0.235, 190, 350, 0.012, mix(dress, WHITE, 0.55), ry=0.034)
    c.poly([(-0.108, 0.805), (0.108, 0.805), (0.088, 0.565), (-0.088, 0.565)], dress, lift=0.12)
    c.rect(0.0, 0.58, 0.19, 0.03, mix(dress, WHITE, 0.55), r=0.01, lift=0.05)
    c.poly([(-0.045, 0.805), (0.045, 0.805), (0.0, 0.745)], skin, lift=0.0)
    # arms outstretched, long sleeves
    c.circle(-0.105, 0.775, 0.05, dress, lift=0.1)
    c.circle(0.105, 0.775, 0.05, dress, lift=0.1)
    c.path([(-0.10, 0.775), (-0.28, 0.77), (-0.42, 0.835)], 0.058, dress)
    c.path([(0.10, 0.775), (0.28, 0.805), (0.43, 0.885)], 0.058, dress)
    c.circle(-0.455, 0.85, 0.034, skin, lift=0.05)
    c.circle(0.465, 0.905, 0.034, skin, lift=0.05)
    # neck, head, hat, scarf
    c.rect(0.0, 0.82, 0.05, 0.05, scale(skin, 0.92), lift=0)
    _face(c, 0.0, 0.905, 0.085, skin, hair, rng.choice(("long", "bun")))
    c.ellipse(0.0, 0.998, 0.098, 0.060, hat, lift=0.14)
    c.rect(0.0, 0.972, 0.205, 0.032, mix(hat, WHITE, 0.8), r=0.016, lift=0.06)
    c.circle(0.0, 1.058, 0.028, c.col((0.98, 0.98, 1.0)), lift=0.1)
    c.ellipse(0.0, 0.812, 0.078, 0.028, scarf, lift=0.12)


# --------------------------------------------------------------------------------------------- snowboard
@prop("snowboard", aspect=0.48, place="ground", nominal=0.40, fill=1.0, category="winter",
      words=("snowboarding", "snowboarder", "snowboards"))
def snowboard(c, color):
    board = c.pick(color, (0.20, 0.55, 0.88))
    white = c.col((0.98, 0.98, 1.0))
    accent = c.col((0.99, 0.80, 0.18))
    ink = c.col((0.14, 0.17, 0.30))
    org, ang = (-0.05, 0.05), -8.0

    def T(pts):
        return _xf(pts, org, ang)
    c.shadow(0.02, 0.012, 0.50, 0.06, alpha=0.2)
    hw = 0.15
    # board: edge, thickness, deck
    c.poly(T(_pill(hw + 0.014, -0.05, 0.95, 0.12, hw_top=hw * 0.96 + 0.014)), scale(board, 0.45), lift=0.0)
    c.poly(T([(u + 0.014, v - 0.008) for u, v in _pill(hw, -0.05, 0.95, 0.12, hw_top=hw * 0.96)]), scale(board, 0.62), lift=0.0)
    c.poly(T(_pill(hw, -0.05, 0.95, 0.12, hw_top=hw * 0.96)), board, lift=0.16)
    # graphics: chevrons and a sun / mountain logo in the upper half
    for k, (col, dv) in enumerate(((white, 0.0), (accent, 0.062), (ink, 0.124))):
        v = 0.66 + dv
        c.poly(T([(-hw * 0.96, v), (0.0, v + 0.07), (hw * 0.96, v), (hw * 0.96, v + 0.045), (0.0, v + 0.115), (-hw * 0.96, v + 0.045)]),
               col, lift=0.0)
    c.poly(T([(-hw * 0.96, 0.08), (0.0, 0.17), (hw * 0.96, 0.08), (hw * 0.96, 0.03), (-hw * 0.96, 0.03)]), ink, lift=0.0)
    c.poly(T([(-hw * 0.96, 0.18), (0.0, 0.26), (hw * 0.96, 0.18), (hw * 0.96, 0.15), (0.0, 0.225), (-hw * 0.96, 0.15)]), accent, lift=0.0)
    c.path(T([(-hw * 0.78, 0.02), (-hw * 0.78, 0.88)]), 0.018, WHITE, alpha=0.28, smooth=False)
    # bindings
    for v in (0.36, 0.55):
        c.poly(T(_box(0.0, v, 0.27, 0.052)), c.col((0.16, 0.17, 0.22)), lift=0.1)
        for dv, w in ((-0.004, 0.040), (0.022, 0.034)):
            c.poly(T(_box(0.0, v + dv, 0.26, w)), c.col((0.30, 0.33, 0.40)), lift=0.14)
        for s in (-1, 1):
            pu, pv = T([(s * 0.118, v + 0.012)])[0]
            c.circle(pu, pv, 0.016, accent, lift=0.1)
        c.poly(T(_box(0.0, v - 0.010, 0.11, 0.010)), c.col((0.65, 0.70, 0.78)), lift=0.0)
    _mound(c, 0.0, 0.065, 0.46, 0.15)
    _sparkle(c, 0.20, 0.34, 0.035)


# ---------------------------------------------------------------------------------------------------- ski
@prop("ski", aspect=0.62, place="ground", nominal=0.42, fill=1.0, category="winter",
      words=("skis", "skipoles", "skipole", "skiset"))
def ski(c, color):
    body = c.pick(color, (0.88, 0.22, 0.24))
    body2 = c.pick(color, (0.96, 0.52, 0.18))
    pole_c = c.col((0.28, 0.31, 0.38))
    grip = c.col((0.20, 0.45, 0.78))
    dark = c.col((0.14, 0.15, 0.20))
    c.shadow(0.0, 0.012, 0.62, 0.06, alpha=0.2)
    # poles flanking the skis, leaning outwards
    for s in (-1, 1):
        base, top = (s * 0.16, 0.06), (s * 0.30, 0.93)
        c.line(base[0], base[1], top[0], top[1], 0.020, scale(pole_c, 0.7 if s < 0 else 0.9))
        d = (top[0] - base[0], top[1] - base[1])
        ln = math.hypot(*d)
        d = (d[0] / ln, d[1] / ln)
        g0, g1 = (top[0] - d[0] * 0.15, top[1] - d[1] * 0.15), (top[0] + d[0] * 0.012, top[1] + d[1] * 0.012)
        c.line(g0[0], g0[1], g1[0], g1[1], 0.050, scale(grip, 0.85))
        c.line(g0[0], g0[1], g1[0], g1[1], 0.040, grip)
        c.path([(top[0] - d[0] * 0.17 + s * 0.015, top[1] - d[1] * 0.17), (top[0] - d[0] * 0.28 + s * 0.060, top[1] - d[1] * 0.28 - 0.01),
                (top[0] - d[0] * 0.25 + s * 0.050, top[1] - d[1] * 0.25 + 0.04)], 0.010, dark, smooth=True)
        bu, bv = base[0] + (top[0] - base[0]) * 0.07, base[1] + (top[1] - base[1]) * 0.07 + 0.04
        c.ellipse(bu, bv, 0.062, 0.020, c.col((0.78, 0.80, 0.86)), lift=0.1)
        c.ellipse(bu, bv, 0.062, 0.020, c.col((0.45, 0.48, 0.58)), lift=0.0, alpha=0.35)
    # the two skis, standing side by side, tipped apart a little
    for s, col, a in ((-1, body, 4.0), (1, body2, -4.0)):
        org = (s * 0.088 - s * 0.0, 0.05)

        def T(pts, org=org, a=a):
            return _xf(pts, org, a)
        hw = 0.047
        outl = [(-hw, 0.0), (-hw, 0.74), (-hw * 0.92, 0.84), (-hw * 0.6, 0.915), (-hw * 0.22, 0.955), (0.0, 0.962),
                (hw * 0.22, 0.955), (hw * 0.6, 0.915), (hw * 0.92, 0.84), (hw, 0.74), (hw, 0.0)]
        c.poly(T([(u * 1.22, v + (0.012 if v > 0.5 else -0.012)) for u, v in outl]), scale(col, 0.45), lift=0.0)
        c.poly(T(outl), col, lift=0.16)
        c.poly(T([(-hw, 0.74), (-hw * 0.92, 0.84), (-hw * 0.6, 0.915), (-hw * 0.22, 0.955), (0.0, 0.962),
                  (hw * 0.22, 0.955), (hw * 0.6, 0.915), (hw * 0.92, 0.84), (hw, 0.74)]), WHITE, lift=0.0, alpha=0.9)
        c.path(T([(-hw * 0.3, 0.74), (-hw * 0.3, 0.12)]), 0.012, WHITE, alpha=0.85, smooth=False)
        c.path(T([(hw * 0.4, 0.70), (hw * 0.4, 0.12)]), 0.008, scale(col, 0.7), alpha=0.8, smooth=False)
        c.poly(T(_box(0.0, 0.40, 0.088, 0.112)), c.col((0.18, 0.19, 0.25)), lift=0.12)
        c.poly(T(_box(0.0, 0.43, 0.074, 0.035)), c.col((0.55, 0.58, 0.66)), lift=0.1)
        c.poly(T(_box(0.0, 0.31, 0.070, 0.050)), c.col((0.22, 0.24, 0.30)), lift=0.1)
    _mound(c, 0.0, 0.06, 0.60, 0.17)
    _sparkle(c, 0.18, 0.15, 0.03)


# ----------------------------------------------------------------------------------------------- iceskate
@prop("iceskate", aspect=1.05, place="ground", nominal=0.25, fill=1.0, category="winter",
      words=("skate", "skates", "blade", "iceskates", "figureskate"))
def iceskate(c, color):
    leather = c.pick(color, (0.97, 0.96, 0.95))
    edge = scale(leather, 0.52)
    steel = c.col(STEEL)
    steel_ed = c.col(STEEL_ED)
    c.shadow(0.0, 0.025, 1.0, 0.06, alpha=0.18)
    _ice_patch(c, 0.02, 0.045, 1.02, 0.12)
    # blade, holder
    for u in (-0.20, 0.30):
        c.poly([(u - 0.04, 0.36), (u + 0.045, 0.36), (u + 0.035, 0.17), (u - 0.035, 0.17)], steel_ed, lift=0.0)
        c.poly([(u - 0.028, 0.35), (u + 0.034, 0.35), (u + 0.026, 0.18), (u - 0.024, 0.18)], steel, lift=0.12)
    blade = [(-0.50, 0.150), (-0.50, 0.095), (-0.46, 0.065), (-0.30, 0.058), (0.40, 0.058), (0.50, 0.075), (0.56, 0.115),
             (0.60, 0.185), (0.575, 0.205), (0.54, 0.17), (0.50, 0.14), (0.44, 0.128), (0.30, 0.128), (-0.40, 0.128), (-0.46, 0.150)]
    c.poly([(u * 1.0, v) for u, v in blade], steel_ed, lift=0.0)
    inner = [(-0.485, 0.138), (-0.47, 0.098), (-0.44, 0.080), (0.40, 0.078), (0.50, 0.095), (0.545, 0.14), (0.52, 0.152), (0.47, 0.128),
             (-0.40, 0.118), (-0.46, 0.140)]
    c.poly(inner, steel, lift=0.18)
    c.line(-0.30, 0.095, 0.40, 0.095, 0.010, WHITE, alpha=0.8)
    for k in range(3):                                                                 # toe pick teeth
        c.line(0.578 - 0.016 * k, 0.205 - 0.006 * k, 0.60 - 0.012 * k, 0.15 - 0.012 * k, 0.012, steel_ed)
    # boot sole and heel
    c.poly([(-0.42, 0.36), (0.52, 0.36), (0.50, 0.425), (-0.42, 0.425)], c.col((0.32, 0.22, 0.17)), lift=0.12)
    # boot body
    body = [(-0.40, 0.42), (-0.38, 0.62), (-0.35, 0.82), (-0.33, 0.92), (-0.04, 0.94), (0.06, 0.92), (0.10, 0.80),
            (0.18, 0.66), (0.32, 0.56), (0.50, 0.52), (0.58, 0.46), (0.56, 0.41), (0.48, 0.375), (-0.38, 0.37)]
    sm = _catmull(body, 5, True)
    c.poly([(1.0 * u, v) for u, v in sm], edge, lift=0.0)
    inner_b = [(u, v) for u, v in sm]
    cx, cy = 0.07, 0.65
    c.poly([(cx + (u - cx) * 0.96, cy + (v - cy) * 0.96) for u, v in inner_b], leather, lift=0.10)
    # padded collar and tongue with criss-cross laces
    c.path([(-0.33, 0.89), (-0.18, 0.915), (-0.03, 0.915)], 0.064, scale(leather, 0.62))
    c.path([(-0.33, 0.89), (-0.18, 0.915), (-0.03, 0.915)], 0.044, mix(leather, c.col((0.78, 0.66, 0.58)), 0.35))
    cream = c.col((1.0, 0.97, 0.88))
    cl = [(-0.03, 0.955), (0.035, 0.86), (0.105, 0.745), (0.225, 0.625), (0.40, 0.568)]
    c.path(cl, 0.130, scale(cream, 0.55))
    c.path(cl, 0.115, cream)
    sm_t = _catmull(cl, 4, False)
    lace = c.col((0.99, 0.99, 0.97))
    for k in range(3, len(sm_t) - 1, 3):
        a_u, a_v = sm_t[k]
        b_u, b_v = sm_t[k + 1]
        du, dv = b_u - a_u, b_v - a_v
        ln = math.hypot(du, dv) or 1.0
        nu, nv = -dv / ln, du / ln
        for sg in (-1, 1):
            c.circle(a_u + sg * nu * 0.052, a_v + sg * nv * 0.052, 0.0135, c.col((0.86, 0.72, 0.30)), lift=0.12)
        c.line(a_u - nu * 0.052, a_v - nv * 0.052, a_u + nu * 0.052 + du / ln * 0.04, a_v + nv * 0.052 + dv / ln * 0.04, 0.020, scale(lace, 0.55))
        c.line(a_u - nu * 0.052, a_v - nv * 0.052, a_u + nu * 0.052 + du / ln * 0.04, a_v + nv * 0.052 + dv / ln * 0.04, 0.012, lace)
        c.line(a_u + nu * 0.052, a_v + nv * 0.052, a_u - nu * 0.052 + du / ln * 0.04, a_v - nv * 0.052 + dv / ln * 0.04, 0.020, scale(lace, 0.55))
        c.line(a_u + nu * 0.052, a_v + nv * 0.052, a_u - nu * 0.052 + du / ln * 0.04, a_v - nv * 0.052 + dv / ln * 0.04, 0.012, lace)
    c.path([(0.0, 0.975), (-0.06, 1.03), (0.02, 1.05)], 0.026, scale(lace, 0.55))
    c.path([(0.0, 0.975), (-0.06, 1.03), (0.02, 1.05)], 0.016, lace)
    c.path([(0.0, 0.975), (0.075, 1.02), (0.03, 1.06)], 0.026, scale(lace, 0.55))
    c.path([(0.0, 0.975), (0.075, 1.02), (0.03, 1.06)], 0.016, lace)
    c.rect(-0.30, 0.42, 0.22, 0.05, c.col((0.32, 0.22, 0.17)), r=0.01, lift=0.1)
    c.arc(-0.08, 0.50, 0.30, 205, 255, 0.016, scale(leather, 0.78), ry=0.12)
    # ice shavings
    for (u, v, a) in ((0.70, 0.07, 20), (0.80, 0.045, -10), (0.62, 0.05, 40), (-0.62, 0.05, 160)):
        c.poly(_xf([(0, 0), (0.07, 0.015), (0.05, 0.035), (0.0, 0.025)], (u, v), a), c.col((0.93, 0.97, 1.0)), lift=0.0)
    _sparkle(c, 0.78, 0.15, 0.035)


# ----------------------------------------------------------------------------------------------- snowman
def _snowball(c, u, v, r):
    c.circle(u, v, r + 0.010, c.col(SNOW_ED), lift=0.0)
    c.circle(u, v, r, c.col(SNOW_SH), lift=0.0)
    c.circle(u - 0.018 * r / 0.2, v + 0.018 * r / 0.2, r - 0.036 * r / 0.2 * 1.3, c.col(SNOW), lift=0.05)
    c.ellipse(u - r * 0.42, v + r * 0.42, r * 0.22, r * 0.12, WHITE, angle=40, lift=0.0, alpha=0.9)


@prop("snowman", aspect=0.9, place="ground", nominal=0.40, fill=1.0, category="winter",
      words=("frosty", "snowmen", "snowball"))
def snowman(c, color):
    accent = c.pick(color, (0.88, 0.22, 0.26))
    coal = c.col((0.12, 0.12, 0.15))
    twig = c.col((0.45, 0.30, 0.18))
    c.shadow(0.0, 0.015, 0.78, 0.07, alpha=0.2)
    c.ellipse(0.04, 0.012, 0.32, 0.035, c.col(SNOW_SH), lift=0.0, alpha=0.85)
    _snowball(c, 0.0, 0.215, 0.215)
    # stick arms (behind the middle ball)
    for s in (-1, 1):
        a = [(s * 0.12, 0.52), (s * 0.28, 0.58), (s * 0.43, 0.68)]
        c.path(a, 0.026, scale(twig, 0.7))
        c.path(a, 0.017, twig)
        for (t, d, ln) in ((0.34, 52, 0.11), (0.40, 20, 0.09)):
            bu, bv = s * 0.36, 0.63 if t < 0.4 else 0.66
            ang = math.radians(d)
            c.line(s * 0.35, 0.63, s * 0.35 + s * ln * math.cos(ang), 0.63 + ln * math.sin(ang), 0.014, twig)
        c.line(s * 0.40, 0.66, s * 0.47, 0.76, 0.013, twig)
        c.line(s * 0.40, 0.66, s * 0.50, 0.69, 0.013, twig)
    _snowball(c, 0.0, 0.50, 0.172)
    # buttons
    for v in (0.575, 0.505, 0.435):
        c.circle(0.0, v, 0.021, coal, lift=0.15)
        c.circle(-0.006, v + 0.007, 0.006, WHITE, lift=0.0, alpha=0.5)
    _snowball(c, 0.0, 0.74, 0.128)
    # scarf with a hanging tail
    c.ellipse(0.0, 0.625, 0.15, 0.040, accent, lift=0.16)
    c.poly([(0.05, 0.63), (0.14, 0.62), (0.15, 0.42), (0.065, 0.43)], accent, lift=0.12)
    c.poly([(0.065, 0.43), (0.15, 0.42), (0.152, 0.385), (0.062, 0.395)], scale(accent, 0.84), lift=0.0)
    for k in range(4):
        c.line(0.075 + k * 0.025, 0.40, 0.073 + k * 0.025, 0.36, 0.012, scale(accent, 0.8))
    for u0 in (-0.10, -0.03, 0.04, 0.11):
        c.line(u0 - 0.014, 0.655, u0 + 0.014, 0.600, 0.020, mix(accent, WHITE, 0.75), alpha=0.85)
    # face
    for s in (-1, 1):
        c.circle(s * 0.047, 0.765, 0.0175, coal, lift=0.12)
        c.circle(s * 0.047 - 0.005, 0.771, 0.005, WHITE, lift=0.0, alpha=0.7)
        c.circle(s * 0.085, 0.725, 0.020, c.col((1.0, 0.62, 0.66)), lift=0.0, alpha=0.30)
    c.poly([(-0.03, 0.752), (0.03, 0.752), (0.17, 0.700)], c.col((0.96, 0.50, 0.10)), lift=0.14)
    c.poly([(-0.03, 0.752), (0.17, 0.700), (0.03, 0.724)], c.col((0.76, 0.32, 0.08)), lift=0.0)
    for k in range(5):
        t = math.radians(205 + k * 32.5)
        c.circle(0.062 * math.cos(t), 0.715 + 0.052 * math.sin(t) + 0.014, 0.0105, coal, lift=0.0)
    # top hat
    hatc = c.col((0.14, 0.14, 0.19))
    c.ellipse(0.0, 0.855, 0.185, 0.036, hatc, lift=0.1)
    c.rect(0.0, 0.92, 0.17, 0.115, hatc, lift=0.14)
    c.ellipse(0.0, 0.978, 0.085, 0.018, mix(hatc, WHITE, 0.15), lift=0.0)
    c.rect(0.0, 0.884, 0.172, 0.036, accent, lift=0.12)
    c.rect(-0.04, 0.925, 0.016, 0.07, WHITE, lift=0.0, alpha=0.22)
    # snow flecks
    _sparkle(c, 0.34, 0.30, 0.035)
    _sparkle(c, -0.38, 0.40, 0.025)


# -------------------------------------------------------------------------------------------------- sled
@prop("sled", aspect=1.6, place="ground", nominal=0.28, fill=0.52, category="winter",
      words=("sledge", "sledding", "toboggan", "sleigh", "sleds"))
def sled(c, color):
    plank = c.pick(color, (0.86, 0.24, 0.22))
    wood = c.col((0.90, 0.66, 0.38))
    wood_d = c.col((0.55, 0.36, 0.20))
    steel = c.col((0.74, 0.78, 0.86))
    steel_ed = c.col((0.30, 0.34, 0.44))
    rope = c.col((0.90, 0.76, 0.46))
    c = c.sub(-0.07, 0.0, 0.86)
    d = (0.22, 0.19)                                      # depth offset of the far side
    c.shadow(0.10, 0.02, 1.70, 0.09, alpha=0.22)
    c.ellipse(0.10, 0.015, 0.88, 0.05, c.col(SNOW_SH), lift=0.0, alpha=0.85)

    def runner(off, col_main, col_edge):
        pts = [(-0.84, 0.07), (0.50, 0.07), (0.66, 0.095), (0.76, 0.20), (0.76, 0.33), (0.68, 0.40), (0.60, 0.37)]
        pts = [(u + off[0], v + off[1]) for u, v in pts]
        c.path(pts, 0.056, col_edge)
        c.path(pts, 0.038, col_main)
        c.path([(-0.78 + off[0], 0.085 + off[1]), (0.44 + off[0], 0.085 + off[1])], 0.009, WHITE, alpha=0.7, smooth=False)
    # far runner and posts
    runner(d, scale(steel, 0.80), scale(steel_ed, 0.9))
    for u in (-0.68, 0.30):
        c.rect(u + d[0], 0.145 + d[1], 0.05, 0.12, scale(wood_d, 0.78), lift=0.1)
    # deck: top surface in painted slats
    n = 5
    x0, x1, v0 = -0.80, 0.44, 0.27
    # end faces first
    c.poly([(x0, v0), (x0 + d[0], v0 + d[1]), (x0 + d[0], v0 - 0.07 + d[1]), (x0, v0 - 0.07)], scale(wood, 0.72), lift=0.0)
    for i in range(n):
        t0, t1 = i / float(n), (i + 1) / float(n)
        a0 = (x0 + d[0] * t0, v0 + d[1] * t0)
        a1 = (x1 + d[0] * t0, v0 + d[1] * t0)
        b0 = (x1 + d[0] * t1, v0 + d[1] * t1)
        b1 = (x0 + d[0] * t1, v0 + d[1] * t1)
        col = plank if i % 2 == 0 else wood
        c.poly([a0, a1, b0, b1], col, lift=0.10)
        c.line(a0[0], a0[1], a1[0], a1[1], 0.008, scale(col, 0.60), alpha=0.9)
    c.line(x0 + d[0], v0 + d[1], x1 + d[0], v0 + d[1], 0.010, scale(wood_d, 0.9))
    c.line(x0, v0, x0 + d[0], v0 + d[1], 0.010, scale(wood_d, 0.9))
    c.line(x1, v0, x1 + d[0], v0 + d[1], 0.010, scale(wood_d, 0.9))
    # two cross bars on the deck
    for t in (0.0,):
        pass
    for u in (-0.50, 0.12):
        c.poly([(u, v0 + 0.012), (u + 0.07, v0 + 0.012), (u + 0.07 + d[0], v0 + 0.012 + d[1]), (u + d[0], v0 + 0.012 + d[1])],
               scale(wood_d, 1.15), lift=0.06, alpha=0.9)
    # front face (near edge)
    c.poly([(x0, v0), (x1, v0), (x1, v0 - 0.075), (x0, v0 - 0.075)], scale(wood, 0.92), lift=0.16)
    c.rect(0.0, v0 - 0.060, x1 - x0, 0.026, scale(wood_d, 1.0), lift=0.0)
    c.line(x0, v0 - 0.002, x1, v0 - 0.002, 0.012, mix(wood, WHITE, 0.4), alpha=0.8)
    for u in (-0.62, -0.20, 0.22):                                       # painted dots
        c.circle(u, v0 - 0.028, 0.013, plank, lift=0.1)
    # near posts and near runner
    for u in (-0.68, 0.30):
        c.rect(u, 0.13, 0.058, 0.115, wood_d, lift=0.14)
    runner((0.0, 0.0), steel, steel_ed)
    # front bow with the pull rope tied to it
    c.line(0.62, 0.37, 0.62 + d[0], 0.37 + d[1], 0.040, scale(wood_d, 0.8))
    c.line(0.62, 0.37, 0.62 + d[0], 0.37 + d[1], 0.030, wood_d)
    mu, mv = 0.62 + d[0] * 0.5, 0.37 + d[1] * 0.5
    rp = [(mu, mv), (mu + 0.20, mv - 0.02), (mu + 0.30, mv - 0.14), (mu + 0.22, mv - 0.30), (mu + 0.08, mv - 0.31), (mu + 0.02, mv - 0.22)]
    c.path(rp, 0.034, scale(rope, 0.55))
    c.path(rp, 0.022, rope)
    for t in range(1, 5):
        q = rp[min(t, len(rp) - 1)]
    c.circle(mu, mv, 0.026, scale(rope, 0.85), lift=0.1)
    _sparkle(c, -0.60, 0.68, 0.045)


# ------------------------------------------------------------------------------------------------ hockey
@prop("hockey", aspect=1.0, place="ground", nominal=0.38, fill=1.0, category="winter",
      words=("icehockey", "puck", "hockeystick", "hockeysticks"))
def hockey(c, color):
    tape = c.pick(color, (0.86, 0.20, 0.22))
    shaft_a = c.col((0.18, 0.20, 0.26))
    shaft_b = c.col((0.86, 0.62, 0.32))
    c.shadow(0.0, 0.02, 1.0, 0.06, alpha=0.18)
    _ice_patch(c, 0.0, 0.05, 1.0, 0.14)
    c.arc(0.0, 0.03, 0.42, 200, 255, 0.008, c.col((0.60, 0.76, 0.90)), alpha=0.8, ry=0.04)

    def stick(s, shaft, blade_col, tp):
        """s = -1: bottom-left to top-right, blade pointing left; s = 1 mirrored."""
        top, bot = (s * -0.30, 0.97), (s * 0.22, 0.215)
        d = (top[0] - bot[0], top[1] - bot[1])
        ln = math.hypot(*d)
        dd = (d[0] / ln, d[1] / ln)
        c.line(top[0], top[1], bot[0], bot[1], 0.058, scale(shaft, 0.5))
        c.line(top[0], top[1], bot[0], bot[1], 0.044, shaft)
        c.line(top[0] - 0.012 * s * -1, top[1], bot[0] - 0.012 * s * -1, bot[1], 0.010, mix(shaft, WHITE, 0.4), alpha=0.7)
        # knob tape
        g0 = (top[0] - dd[0] * 0.24, top[1] - dd[1] * 0.24)
        c.line(g0[0], g0[1], top[0], top[1], 0.052, scale(tp, 0.8))
        c.line(g0[0], g0[1], top[0], top[1], 0.044, tp)
        for k in range(4):
            q = (g0[0] + (top[0] - g0[0]) * (k + 0.5) / 4.0, g0[1] + (top[1] - g0[1]) * (k + 0.5) / 4.0)
            c.line(q[0] - 0.026, q[1] - 0.010, q[0] + 0.026, q[1] + 0.010, 0.008, scale(tp, 0.65), alpha=0.8)
        # blade
        bl_pts = [(s * u, v) for u, v in [(-0.255, 0.25), (-0.185, 0.25), (-0.165, 0.15), (-0.125, 0.04), (-0.455, 0.04),
                                         (-0.47, 0.115), (-0.285, 0.145)]]
        c.poly(bl_pts, blade_col, lift=0.14)
        # outline pass (stroke) and tape wrap on the blade
        c.path(bl_pts, 0.012, scale(blade_col, 0.45), closed=True, smooth=False)
        c.path([(s * -0.46, 0.075), (s * -0.13, 0.075)], 0.020, tp, smooth=False)
    stick(-1, shaft_a, c.col((0.20, 0.23, 0.30)), tape)
    stick(1, shaft_b, c.col((0.78, 0.54, 0.26)), tape)
    # the puck between the blades
    c.ellipse(0.0, 0.065, 0.100, 0.034, c.col((0.05, 0.05, 0.07)), lift=0.0)
    c.rect(0.0, 0.095, 0.2, 0.060, c.col((0.10, 0.10, 0.13)), lift=0.2)
    c.ellipse(0.0, 0.125, 0.100, 0.034, c.col((0.20, 0.21, 0.26)), lift=0.1)
    c.ellipse(-0.03, 0.132, 0.045, 0.010, WHITE, lift=0.0, alpha=0.35)
    _sparkle(c, 0.40, 0.30, 0.035)
