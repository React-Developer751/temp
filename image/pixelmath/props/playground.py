"""Props: playground equipment, sports balls, a child and a construction worker."""
import math

from .core import WHITE, mix, prop, scale  # noqa: F401
from .people import HAIR, SKIN, _face


def _dots(c, u0, v0, u1, v1, color, n=9, r=0.010):
    """Chain links: small alternating beads along a line."""
    for k in range(n + 1):
        t = k / float(n)
        c.circle(u0 + (u1 - u0) * t, v0 + (v1 - v0) * t, r, color if k % 2 else scale(color, 0.78), lift=0.05)


# ----------------------------------------------------------------------------------------------------- swing
@prop("swing", aspect=1.3, place="ground", nominal=0.40, category="playground",
      words=("swings", "jhoola", "jhula", "swingset"))
def swing(c, color):
    frame = c.pick(color, (0.88, 0.30, 0.26))
    back = scale(frame, 0.78)
    chain = c.col((0.62, 0.65, 0.72))
    c.shadow(0.0, 0.015, 1.30, 0.07)
    # two A-frames (the back leg of each is darker)
    for sgn in (-1, 1):
        u = sgn * 0.52
        c.line(u, 0.92, u - 0.13, 0.01, 0.036, back)
        c.line(u, 0.92, u + 0.13, 0.01, 0.036, frame)
        c.line(u - 0.075, 0.38, u + 0.075, 0.38, 0.022, scale(frame, 0.9))
        c.ellipse(u - 0.13, 0.012, 0.045, 0.014, c.col((0.25, 0.25, 0.3)), lift=0.05)
        c.ellipse(u + 0.13, 0.012, 0.045, 0.014, c.col((0.25, 0.25, 0.3)), lift=0.05)
    # top bar
    c.rect(0, 0.925, 1.18, 0.055, frame, r=0.027, lift=0.14)
    for sgn in (-1, 1):
        c.circle(sgn * 0.52, 0.925, 0.036, scale(frame, 0.92), lift=0.1)
    # swings: the right one swung a little
    seat_cols = (c.col((0.20, 0.38, 0.72)), c.col((0.98, 0.78, 0.20)))
    for k, (cu, sway) in enumerate(((-0.20, 0.0), (0.21, 0.07))):
        sv = 0.30 - sway * 0.2
        su = cu + sway
        for sgn in (-1, 1):
            tu, bu = cu + sgn * 0.085, su + sgn * 0.095
            c.line(tu, 0.90, bu, sv + 0.02, 0.012, chain)
            _dots(c, tu, 0.89, bu, sv + 0.025, chain, n=12, r=0.009)
        ang = -math.degrees(math.atan2(sway, 0.60)) * 0.9
        h = 0.045
        c.poly([(su - 0.125, sv - h / 2), (su + 0.125, sv - h / 2), (su + 0.125, sv + h / 2), (su - 0.125, sv + h / 2)],
               seat_cols[k], lift=0.2, angle=ang, pivot=(su, sv))
        c.line(su - 0.11, sv + 0.012, su + 0.11, sv + 0.012, 0.008, mix(seat_cols[k], WHITE, 0.4))


# ----------------------------------------------------------------------------------------------------- slide
@prop("slide", aspect=1.4, place="ground", nominal=0.35, category="playground",
      words=("slides", "fisalpatti", "chute"))
def slide(c, color):
    body = c.pick(color, (0.96, 0.74, 0.18))
    frame = c.col((0.22, 0.45, 0.82))
    dark = scale(frame, 0.75)
    steel = c.col((0.72, 0.75, 0.82))
    c.shadow(0.0, 0.015, 1.40, 0.07)
    # back rail of the ladder and the platform posts
    c.line(-0.57, 0.01, -0.45, 0.70, 0.032, dark)
    c.rect(-0.18, 0.35, 0.04, 0.70, dark, lift=0.1)
    # slide support strut
    c.line(0.27, 0.42, 0.36, 0.01, 0.03, dark)
    c.line(0.27, 0.42, 0.14, 0.01, 0.03, frame)
    c.ellipse(0.36, 0.012, 0.05, 0.014, c.col((0.25, 0.25, 0.3)), lift=0.05)
    c.ellipse(0.14, 0.012, 0.05, 0.014, c.col((0.25, 0.25, 0.3)), lift=0.05)
    # ladder front rail and rungs
    for k in range(1, 7):
        t = k / 7.0
        c.line(-0.57 + 0.12 * t * 1.0 + 0.0, 0.01 + 0.69 * t, -0.67 + 0.20 * t, 0.01 + 0.69 * t, 0.026, steel)
    c.line(-0.68, 0.01, -0.50, 0.70, 0.04, frame)
    c.ellipse(-0.68, 0.012, 0.05, 0.014, c.col((0.25, 0.25, 0.3)), lift=0.05)
    # platform and hand rails
    c.rect(-0.32, 0.70, 0.40, 0.05, dark, r=0.012, lift=0.12)
    c.rect(-0.50, 0.85, 0.035, 0.30, frame, lift=0.1)
    c.rect(-0.16, 0.86, 0.035, 0.32, frame, lift=0.1)
    c.rect(-0.33, 0.99, 0.40, 0.04, frame, r=0.018, lift=0.14)
    c.rect(-0.33, 0.85, 0.34, 0.022, frame, lift=0.1)
    # chute: wall in the main colour with a light running surface
    pts = [(-0.17, 0.69), (-0.02, 0.665), (0.20, 0.48), (0.45, 0.25), (0.60, 0.15), (0.71, 0.135)]
    c.path(pts, 0.11, scale(body, 0.88))
    c.path([(u, v + 0.012) for u, v in pts], 0.085, body)
    c.path([(u, v + 0.030) for u, v in pts], 0.026, mix(body, WHITE, 0.5), alpha=0.9)
    c.circle(-0.17, 0.69, 0.045, scale(body, 0.88), lift=0.1)


# ---------------------------------------------------------------------------------------------------- seesaw
@prop("seesaw", aspect=1.8, place="ground", nominal=0.2, fill=0.6, category="playground",
      words=("teeter", "totter", "seesaws"))
def seesaw(c, color):
    plank = c.pick(color, (0.96, 0.62, 0.18))
    grey = c.col((0.34, 0.40, 0.55))
    dark = c.col((0.20, 0.22, 0.28))
    c.shadow(0.0, 0.015, 1.75, 0.07)
    ang, piv = 11.0, (0.0, 0.265)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def W(s, h):
        return (piv[0] + s * ca - h * sa, piv[1] + s * sa + h * ca)

    # fulcrum
    c.poly([(-0.17, 0.02), (0.17, 0.02), (0.045, 0.255), (-0.045, 0.255)], grey, lift=0.16)
    c.rect(0, 0.025, 0.40, 0.04, scale(grey, 0.8), r=0.015, lift=0.1)
    # ground bumper under the low end
    c.ellipse(-0.80, 0.05, 0.07, 0.04, dark, lift=0.1)
    # plank
    c.poly([W(-0.86, -0.036), W(0.86, -0.036), W(0.86, 0.036), W(-0.86, 0.036)], plank, lift=0.16)
    c.poly([W(-0.86, 0.018), W(0.86, 0.018), W(0.86, 0.036), W(-0.86, 0.036)], mix(plank, WHITE, 0.35), lift=0.0, alpha=0.7)
    # seats pads and handles
    for sgn in (-1, 1):
        c.poly([W(sgn * 0.44, 0.036), W(sgn * 0.82, 0.036), W(sgn * 0.82, 0.05), W(sgn * 0.44, 0.05)], scale(plank, 0.8), lift=0.0)
        s0, s1 = sgn * 0.52, sgn * 0.68
        c.path([W(s0, 0.04), W(s0, 0.17), W(s1, 0.17), W(s1, 0.04)], 0.024, dark, smooth=False)
        for (s, h) in ((s0, 0.17), (s1, 0.17)):
            pu, pv = W(s, h)
            c.circle(pu, pv, 0.0125, dark, lift=0.0)
    # pivot bolt
    c.circle(piv[0], piv[1], 0.032, c.col((0.78, 0.80, 0.86)), lift=0.2)
    c.circle(piv[0], piv[1], 0.012, dark, lift=0.0)


# --------------------------------------------------------------------------------------------------- football
def _norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return tuple(x / m for x in v)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _ball_geometry():
    """Pentagon centres of a soccer ball (icosahedron vertices) turned towards the viewer, with their corners."""
    phi = (1 + 5 ** 0.5) / 2
    raw = []
    for a in (1, -1):
        for b in (phi, -phi):
            raw += [(0, a, b), (a, b, 0), (b, 0, a)]
    ay, ax = 0.55, 0.42
    cy, sy, cx, sx = math.cos(ay), math.sin(ay), math.cos(ax), math.sin(ax)
    cen = []
    for x, y, z in raw:
        x, y, z = _norm((x, y, z))
        x, z = x * cy + z * sy, -x * sy + z * cy                    # about the vertical axis
        y, z = y * cx - z * sx, y * sx + z * cx                     # about the horizontal axis
        cen.append((x, y, z))
    ang = math.radians(20.0)
    pents = []
    for n in cen:
        nbs = [m for m in cen if abs(_dot(n, m) - 1 / 5 ** 0.5) < 0.05]
        t1 = _norm(tuple(m - n[i] * _dot(n, nbs[0]) for i, m in enumerate(nbs[0])))
        t2 = _cross(n, t1)
        corners = []
        for k in range(5):
            th = math.radians(72 * k)
            corners.append(tuple(math.cos(ang) * n[i] + math.sin(ang) * (math.cos(th) * t1[i] + math.sin(th) * t2[i]) for i in range(3)))
        pents.append((n, corners))
    seams = []
    for i, (n1, c1) in enumerate(pents):
        for j, (n2, c2) in enumerate(pents):
            if j > i and abs(_dot(n1, n2) - 1 / 5 ** 0.5) < 0.05:
                best = max(((_dot(a, b), a, b) for a in c1 for b in c2), key=lambda t: t[0])
                seams.append((best[1], best[2]))
    return pents, seams


_BALL = _ball_geometry()


@prop("football", aspect=1.0, place="ground", nominal=0.14, category="sports",
      words=("soccer", "footy", "fifa"))
def football(c, color):
    pents, seams = _BALL
    R, cu, cv = 0.46, 0.0, 0.50
    ink = c.pick(color, (0.11, 0.11, 0.14))
    c.shadow(0.0, 0.025, 0.85, 0.12)
    c.circle(cu, cv, R, c.col((0.97, 0.97, 0.98)), lift=0.10)

    def proj(p):
        x, y, z = p
        if z < 0:                                        # behind the limb: slide it onto the rim
            m = math.hypot(x, y) or 1.0
            x, y = x / m * 0.995, y / m * 0.995
        return (cu + R * x, cv + R * y)

    for a, b in seams:
        pts = []
        for k in range(5):
            t = k / 4.0
            q = _norm(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))
            pts.append(q)
        if all(q[2] > 0.05 for q in pts):
            c.path([proj(q) for q in pts], 0.014, ink, smooth=False)
        elif sum(q[2] > 0.05 for q in pts) >= 2:
            ok = [q for q in pts if q[2] > 0.05]
            c.path([proj(q) for q in ok], 0.014, ink, smooth=False)
    for n, corners in pents:
        if n[2] < -0.25:
            continue
        c.poly([proj(q) for q in corners], ink, lift=0.10)
    # roundness: soft shade at the lower right and a highlight at the upper left
    c.ring(cu, cv, R - 0.012, 0.03, c.col((0.30, 0.34, 0.50)), alpha=0.12)


# ---------------------------------------------------------------------------------------------------- cricket
@prop("cricket", aspect=0.8, place="ground", nominal=0.3, fill=0.85, category="sports",
      words=("bat", "wicket", "stumps", "stump", "bails", "willow", "innings"))
def cricket(c, color):
    wood = c.col((0.93, 0.82, 0.58))
    willow = c.col((0.90, 0.73, 0.44))
    grip = c.pick(color, (0.20, 0.45, 0.76))
    ball = c.pick(color, (0.80, 0.12, 0.14))
    c.shadow(0.02, 0.012, 0.85, 0.06)
    # stumps and bails (behind)
    wood = c.col((0.90, 0.76, 0.46))
    for k, u in enumerate((0.10, 0.19, 0.28)):
        c.rect(u, 0.33, 0.040, 0.66, scale(wood, 0.96 - 0.03 * k), r=0.014, lift=0.16)
        c.rect(u - 0.009, 0.33, 0.008, 0.62, WHITE, lift=0.0, alpha=0.35)
    for u in (0.145, 0.235):
        c.rect(u, 0.675, 0.088, 0.020, mix(wood, WHITE, 0.25), r=0.008, lift=0.1)
        c.circle(u - 0.040, 0.675, 0.012, scale(wood, 0.92), lift=0.1)
        c.circle(u + 0.040, 0.675, 0.012, scale(wood, 0.92), lift=0.1)
    # bat leaning on the stumps: drawn upright then turned about the bottom corner
    ang, piv = -13.0, (-0.20, 0.0)
    bu = -0.20
    def bat(pts, col, lift=0.0, alpha=1.0):
        c.poly([(bu + a, v) for a, v in pts], col, lift=lift, alpha=alpha, angle=ang, pivot=piv)

    blade = [(-0.068, 0.0), (0.068, 0.0), (0.072, 0.40), (0.062, 0.50), (0.035, 0.57), (-0.035, 0.57), (-0.062, 0.50), (-0.072, 0.40)]
    bat(blade, willow, 0.14)
    bat([(0.040, 0.0), (0.068, 0.0), (0.072, 0.40), (0.062, 0.50), (0.035, 0.57), (0.020, 0.57), (0.030, 0.40)], scale(willow, 0.86))
    bat([(-0.068, 0.0), (0.068, 0.0), (0.068, 0.028), (-0.068, 0.028)], scale(willow, 0.76))
    bat([(-0.060, 0.30), (0.030, 0.30), (0.030, 0.315), (-0.060, 0.315)], scale(willow, 0.85))
    bat([(-0.026, 0.56), (0.026, 0.56), (0.024, 0.62), (-0.024, 0.62)], willow, 0.1)
    bat([(-0.026, 0.61), (0.026, 0.61), (0.026, 0.88), (-0.026, 0.88)], grip, 0.14)
    for k in range(6):
        v = 0.64 + 0.04 * k
        bat([(-0.026, v), (0.026, v + 0.012), (0.026, v + 0.02), (-0.026, v + 0.008)], scale(grip, 0.72))
    bat([(-0.033, 0.88), (0.033, 0.88), (0.033, 0.905), (-0.033, 0.905)], scale(grip, 0.8), 0.1)
    # ball in front
    c.shadow(0.20, 0.015, 0.20, 0.05, alpha=0.3)
    c.circle(0.20, 0.075, 0.07, ball, lift=0.18)
    c.arc(0.20, 0.075, 0.07, 120, 240, 0.008, WHITE, alpha=0.9, ry=0.07)
    c.path([(0.165, 0.115), (0.185, 0.085), (0.19, 0.055), (0.175, 0.03)], 0.007, mix(ball, WHITE, 0.8), alpha=0.9)
    c.ellipse(0.175, 0.10, 0.02, 0.012, WHITE, angle=40, alpha=0.4, lift=0.0)


# ------------------------------------------------------------------------------------------------------ child
@prop("child", aspect=0.52, place="ground", nominal=0.30, category="people",
      words=("kid", "children", "boy", "girl", "toddler", "infant", "bachcha", "baccha", "preschool", "nursery", "daycare"))
def child(c, color):
    rng = c.rng
    shirt = c.pick(color, (0.30, 0.72, 0.38))
    skin = c.col(rng.choice(SKIN))
    hair = c.col(rng.choice(HAIR[:4]))
    shorts = c.col((0.25, 0.40, 0.70))
    bag = c.col((0.88, 0.28, 0.25))
    c.shadow(0.0, 0.01, 0.50, 0.05)
    # backpack peeks out behind the body
    c.rect(0, 0.545, 0.38, 0.29, bag, r=0.05, lift=0.14)
    c.rect(0, 0.64, 0.12, 0.05, scale(bag, 0.8), r=0.02, lift=0.0)
    # legs, socks, shoes
    for sgn in (-1, 1):
        c.rect(sgn * 0.058, 0.20, 0.075, 0.26, skin, r=0.02, lift=0.1)
        c.rect(sgn * 0.058, 0.095, 0.080, 0.095, WHITE, r=0.02, lift=0.05)
        c.ellipse(sgn * 0.066, 0.032, 0.085, 0.036, c.col((0.88, 0.25, 0.25)) if sgn > 0 else c.col((0.88, 0.25, 0.25)), lift=0.12)
        c.rect(sgn * 0.066, 0.012, 0.15, 0.014, WHITE, r=0.006, lift=0.0)
    # shorts
    c.poly([(-0.15, 0.44), (0.15, 0.44), (0.16, 0.27), (0.01, 0.27), (0.0, 0.31), (-0.01, 0.27), (-0.16, 0.27)], shorts, lift=0.12)
    # torso
    c.poly([(-0.15, 0.72), (0.15, 0.72), (0.15, 0.40), (-0.15, 0.40)], shirt, lift=0.12)
    c.rect(0, 0.425, 0.31, 0.035, scale(shirt, 0.88), r=0.01, lift=0.0)
    # backpack straps
    for sgn in (-1, 1):
        c.poly([(sgn * 0.075, 0.72), (sgn * 0.105, 0.72), (sgn * 0.105, 0.46), (sgn * 0.08, 0.46)], scale(bag, 0.85), lift=0.1)
    # arms: left hangs, right waves
    c.circle(-0.16, 0.68, 0.058, shirt, lift=0.1)
    c.circle(0.16, 0.68, 0.058, shirt, lift=0.1)
    c.path([(-0.17, 0.64), (-0.19, 0.54), (-0.20, 0.47)], 0.050, skin, smooth=False)
    c.circle(-0.20, 0.455, 0.036, skin, lift=0.05)
    c.path([(0.17, 0.66), (0.23, 0.72), (0.24, 0.82)], 0.050, skin, smooth=False)
    c.circle(0.24, 0.845, 0.038, skin, lift=0.05)
    # neck and head
    c.rect(0, 0.735, 0.07, 0.06, scale(skin, 0.9), lift=0)
    hv, r = 0.865, 0.125
    c.circle(-r * 0.98, hv - 0.01, 0.028, scale(skin, 0.95), lift=0.05)
    c.circle(r * 0.98, hv - 0.01, 0.028, scale(skin, 0.95), lift=0.05)
    c.circle(0, hv, r, skin, lift=0.08)
    c.ellipse(0, hv + r * 0.58, r * 1.06, r * 0.52, hair, lift=0.1)
    dark = c.col((0.16, 0.12, 0.12))
    for sgn in (-1, 1):
        c.circle(sgn * r * 0.42, hv - r * 0.04, r * 0.17, dark, lift=0)
        c.circle(sgn * r * 0.42 - r * 0.05, hv + r * 0.02, r * 0.06, WHITE, lift=0)
        c.circle(sgn * r * 0.62, hv - r * 0.32, r * 0.16, c.col((0.98, 0.50, 0.50)), lift=0, alpha=0.45)
    # big open smile
    mw, md, mv = r * 0.42, r * 0.34, hv - r * 0.30
    mouth = [(-mw, mv), (mw, mv)] + [(mw * math.cos(math.radians(t)), mv - md * math.sin(math.radians(t))) for t in range(0, 181, 15)]
    c.poly(mouth, c.col((0.62, 0.16, 0.20)), lift=0)
    teeth = [(-mw * 0.92, mv), (mw * 0.92, mv), (mw * 0.8, mv - md * 0.30), (-mw * 0.8, mv - md * 0.30)]
    c.poly(teeth, WHITE, lift=0)


# ----------------------------------------------------------------------------------------------------- worker
@prop("worker", aspect=0.55, place="ground", nominal=0.5, category="people",
      words=("labourer", "laborer", "labour", "mazdoor", "engineer", "contractor", "foreman"))
def worker(c, color):
    rng = c.rng
    vest = c.pick(color, (1.0, 0.50, 0.08))
    skin = c.col(rng.choice(SKIN))
    hair = c.col(rng.choice(HAIR))
    denim = c.col((0.22, 0.40, 0.70))
    shirt = c.col((0.78, 0.80, 0.84))
    boot = c.col((0.50, 0.33, 0.18))
    silver = c.col((0.93, 0.94, 0.86))
    yellow = c.col((0.99, 0.80, 0.10))
    c.shadow(0.0, 0.01, 0.55, 0.06)
    # legs and work boots
    for sgn in (-1, 1):
        c.rect(sgn * 0.067, 0.26, 0.122, 0.50, denim, r=0.04, lift=0.12)
        c.ellipse(sgn * 0.08, 0.036, 0.098, 0.042, boot, lift=0.14)
        c.rect(sgn * 0.08, 0.012, 0.19, 0.016, c.col((0.18, 0.15, 0.13)), r=0.006, lift=0.0)
    c.rect(-0.067, 0.34, 0.07, 0.05, scale(denim, 0.82), r=0.01, lift=0.0)             # knee pad / pocket
    # torso (shirt), sleeves
    c.poly([(-0.165, 0.78), (0.165, 0.78), (0.14, 0.45), (-0.14, 0.45)], shirt, lift=0.10)
    for sgn in (-1, 1):
        c.circle(sgn * 0.16, 0.745, 0.052, shirt, lift=0.1)
    c.path([(-0.17, 0.74), (-0.19, 0.62), (-0.205, 0.50)], 0.064, shirt, smooth=False)
    c.circle(-0.205, 0.487, 0.036, skin, lift=0.05)
    # hi-vis vest: two panels, V neck, reflective stripes
    for sgn in (-1, 1):
        c.poly([(sgn * 0.165, 0.78), (sgn * 0.05, 0.78), (0.0, 0.62), (0.0, 0.45), (sgn * 0.14, 0.45)], vest, lift=0.12)
        c.poly([(sgn * 0.085, 0.78), (sgn * 0.12, 0.78), (sgn * 0.12, 0.45), (sgn * 0.085, 0.45)], silver, lift=0.05)
    c.rect(0, 0.545, 0.285, 0.032, silver, lift=0.05)
    c.line(0, 0.62, 0, 0.45, 0.008, scale(vest, 0.7))
    # belt with a tool pouch
    c.rect(0, 0.455, 0.29, 0.032, c.col((0.30, 0.20, 0.13)), r=0.006, lift=0.1)
    c.rect(0, 0.455, 0.032, 0.026, c.col((0.85, 0.80, 0.5)), lift=0.1)
    # right arm bent, holding a wrench
    c.circle(0.165, 0.745, 0.052, shirt, lift=0.1)
    c.path([(0.17, 0.74), (0.225, 0.62), (0.245, 0.52)], 0.064, shirt, smooth=False)
    wr = c.col((0.62, 0.66, 0.74))
    ang, piv = -10.0, (0.245, 0.50)
    c.poly([(0.233, 0.34), (0.257, 0.34), (0.257, 0.66), (0.233, 0.66)], wr, lift=0.2, angle=ang, pivot=piv)
    c.circle(*_rot(0.245, 0.70, piv, ang), 0.050, wr, lift=0.2)
    c.poly([(0.229, 0.70), (0.261, 0.70), (0.261, 0.76), (0.229, 0.76)], c.col((0.50, 0.52, 0.6)), lift=0.0,
           angle=ang, pivot=piv)
    c.circle(0.245, 0.50, 0.036, skin, lift=0.05)
    c.circle(*_rot(0.245, 0.355, piv, ang), 0.03, wr, lift=0.2)
    # neck, head, hard hat
    c.rect(0, 0.80, 0.058, 0.06, scale(skin, 0.92), lift=0)
    _face(c, 0, 0.885, 0.088, skin, scale(skin, 0.78), "short")          # hair hidden under the hard hat
    c.rect(0, 0.938, 0.27, 0.026, scale(yellow, 0.92), r=0.012, lift=0.12)
    dome = [(0.108 * math.cos(math.radians(t)), 0.94 + 0.098 * math.sin(math.radians(t))) for t in range(0, 181, 10)]
    c.poly(dome, yellow, lift=0.16)
    c.rect(0, 1.0, 0.026, 0.07, scale(yellow, 0.88), r=0.01, lift=0.0)
    c.ellipse(-0.045, 0.995, 0.03, 0.018, WHITE, angle=35, alpha=0.4, lift=0.0)


def _rot(u, v, piv, ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return (piv[0] + (u - piv[0]) * ca - (v - piv[1]) * sa, piv[1] + (u - piv[0]) * sa + (v - piv[1]) * ca)
