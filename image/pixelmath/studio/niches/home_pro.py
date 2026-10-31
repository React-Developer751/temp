"""Home and trade niches: real estate, interior design, construction, plumbing, electrician, cleaning, solar, farm."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, arc, disc, gloss, hshade_box, leaf, soft_disc, speckle, strand
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, mix, scale

CREAM = (0.96, 0.94, 0.89)
BRASS = (0.80, 0.62, 0.26)
STEEL = (0.74, 0.77, 0.80)
LEAF_G = ((0.20, 0.46, 0.20), (0.26, 0.55, 0.24), (0.32, 0.60, 0.26), (0.16, 0.38, 0.18))


def _prism(c, u, v, w, h, dx, dy, front, top=None, side=None, lift=0.07, r=0.0):
    """Oblique box: front face w x h with its base centre at (u, v); depth goes right and up by (dx, dy)."""
    x0, x1 = u - w / 2, u + w / 2
    top = top or mix(front, WHITE, 0.22)
    side = side or scale(front, 0.68)
    c.poly([(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], side, lift=lift)
    c.poly([(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, lift=0.04)
    c.rect(u, v + h / 2, w, h, front, lift=lift, r=r)


def _pipe(c, u0, v0, u1, v1, w, base, hl=0.7):
    """A shiny tube between two points: dark body, lit core shifted to the key light, thin highlight."""
    c.line(u0, v0, u1, v1, w, scale(base, 0.58))
    c.line(u0 - w * 0.10, v0 + w * 0.12, u1 - w * 0.10, v1 + w * 0.12, w * 0.66, base)
    c.line(u0 - w * 0.20, v0 + w * 0.24, u1 - w * 0.20, v1 + w * 0.24, w * 0.18, mix(base, WHITE, hl), 0.85)


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _rot(pts, ang, ox=0.0, oy=0.0, sv=1.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(ox + x * ca - y * sa, oy + (x * sa + y * ca) * sv) for x, y in pts]


def _sparkle(c, u, v, r, color=WHITE, alpha=0.9):
    soft_disc(c, u, v, r * 1.1, r * 1.1, color, alpha * 0.5, 1.6, add=True)
    c.line(u - r, v, u + r, v, r * 0.07, color, alpha)
    c.line(u, v - r, u, v + r, r * 0.07, color, alpha)
    c.line(u - r * 0.45, v - r * 0.45, u + r * 0.45, v + r * 0.45, r * 0.04, color, alpha * 0.7)
    c.line(u - r * 0.45, v + r * 0.45, u + r * 0.45, v - r * 0.45, r * 0.04, color, alpha * 0.7)


def _bush(c, u, v, r, rng, cols=LEAF_G, n=7):
    """A soft rounded tree crown / bush from overlapping shaded blobs with light on the upper left."""
    for k in range(n):
        a = rng.uniform(0, 6.28)
        d = rng.uniform(0.0, r * 0.55)
        rr = r * rng.uniform(0.45, 0.7)
        c.ellipse(u + math.cos(a) * d, v + math.sin(a) * d * 0.8, rr, rr * 0.92, cols[k % len(cols)], lift=0.22)
    soft_disc(c, u - r * 0.3, v + r * 0.35, r * 0.55, r * 0.4, (0.8, 0.95, 0.5), 0.35, 1.2, add=True)
    soft_disc(c, u + r * 0.3, v - r * 0.3, r * 0.7, r * 0.45, BLACK, 0.2, 1.4)


def _sky(P, light_top=(0.50, 0.74, 0.96), light_bot=(0.90, 0.95, 1.0)):
    if P.mood == "dark":
        return (0.10, 0.16, 0.34), (0.88, 0.55, 0.42)
    if P.mood == "warm":
        return (0.60, 0.78, 0.95), (1.0, 0.92, 0.80)
    return light_top, light_bot


def _span(S, pad=0.3):
    a, b = S.visible_u()
    return a - pad, b + pad


def _hash(i):
    return (math.sin(i * 12.9898) * 43758.5453) % 1.0




def _crane(S, u, v_base, h, col, jib=0.9):
    """Lattice tower crane silhouette (use in the far layer)."""
    w = h * 0.06
    S.line(u - w, v_base, u - w, v_base - h, 0.008, col)
    S.line(u + w, v_base, u + w, v_base - h, 0.008, col)
    n = 14
    for k in range(n):
        y0, y1 = v_base - h * k / n, v_base - h * (k + 1) / n
        S.line(u - w, y0, u + w, y1, 0.004, col)
        S.line(u + w, y0, u - w, y1, 0.004, col)
    top = v_base - h
    S.rect(u, top - 0.01, w * 3.2, 0.03, col, lift=0.0)
    S.line(u - jib * 0.25, top - 0.02, u + jib, top - 0.02, 0.010, col)
    S.line(u - jib * 0.25, top - 0.05, u + jib, top - 0.02, 0.004, col)
    for k in range(10):
        x0, x1 = u + jib * k / 10.0, u + jib * (k + 1) / 10.0
        S.line(x0, top - 0.02, x1, top - 0.045, 0.004, col)
    S.rect(u - jib * 0.2, top - 0.005, jib * 0.10, 0.045, scale(col, 1.4), lift=0.0)           # counterweight
    S.line(u, top - 0.08, u + jib * 0.55, top - 0.02, 0.003, col)
    S.line(u, top - 0.08, u - jib * 0.2, top - 0.02, 0.003, col)
    S.line(u + jib * 0.7, top - 0.02, u + jib * 0.7, top + 0.24, 0.003, col)
    S.rect(u + jib * 0.7, top + 0.26, 0.03, 0.025, col, lift=0.0)


# ====================================================================================================== real estate
@sprop("hp_house_model", aspect=2.2, fill=0.70)
def hp_house_model(c, P):
    rng = c.rng
    wood = (0.78, 0.60, 0.40)
    wall = (0.97, 0.95, 0.91)
    roof = scale(P.accent_dark, 0.9)
    # model board with thickness and a green base
    _prism(c, 0.0, 0.0, 1.46, 0.045, 0.16, 0.085, scale(wood, 0.85), top=wood, side=scale(wood, 0.6))
    c.poly([(-0.69, 0.045), (0.69, 0.045), (0.85, 0.125), (-0.53, 0.125)], (0.56, 0.70, 0.40), lift=0.10)
    for _ in range(40):                                                      # tiny turf blades
        uu, vv = rng.uniform(-0.6, 0.78), rng.uniform(0.055, 0.12)
        c.line(uu, vv, uu + rng.uniform(-0.01, 0.01), vv + rng.uniform(0.012, 0.03), 0.004, (0.38, 0.58, 0.28), 0.6)
    c.poly([(0.0, 0.052), (0.12, 0.052), (0.18, 0.118), (0.16, 0.118)], (0.90, 0.86, 0.78), lift=0.05)      # path
    # low wing (garage) at the left
    v0 = 0.085
    _prism(c, -0.58, v0, 0.34, 0.19, 0.20, 0.09, wall, lift=0.06)
    c.poly([(-0.77, v0 + 0.19), (-0.39, v0 + 0.19), (-0.17, v0 + 0.285), (-0.55, v0 + 0.285)], scale(roof, 0.85), lift=0.1)
    c.rect(-0.58, v0 + 0.205, 0.40, 0.014, scale(roof, 0.7), lift=0.05)
    c.rect(-0.58, v0 + 0.09, 0.22, 0.13, (0.88, 0.88, 0.86), lift=0.1)                # garage door
    for k in range(4):
        c.line(-0.69, v0 + 0.045 + k * 0.03, -0.47, v0 + 0.045 + k * 0.03, 0.003, (0.7, 0.7, 0.68), 0.7)
    # main gabled volume
    x0, x1, um = -0.40, 0.20, -0.10
    wh, rh, dx, dy = 0.30, 0.17, 0.30, 0.13
    c.poly([(x1, v0), (x1 + dx, v0 + dy), (x1 + dx, v0 + wh + dy), (x1, v0 + wh)], scale(wall, 0.70), lift=0.08)
    soft_disc(c, x1 + 0.02, v0 + 0.03, 0.08, 0.09, BLACK, 0.18, 1.3)
    c.poly([(x1 + dx * 0.55, v0 + 0.04 + dy * 0.55), (x1 + dx * 0.85, v0 + 0.04 + dy * 0.85), (x1 + dx * 0.85, v0 + 0.20 + dy * 0.85),
            (x1 + dx * 0.55, v0 + 0.20 + dy * 0.55)], (0.62, 0.84, 0.94), lift=0.2)         # side window
    # roof right slope
    A, B = (x1 + 0.045, v0 + wh - 0.015), (x1 + dx + 0.045, v0 + wh + dy - 0.015)
    C, D = (um + dx, v0 + wh + rh + dy), (um, v0 + wh + rh)
    c.poly([A, B, C, D], roof, lift=0.14)
    for k in range(1, 9):
        t = k / 9.0
        p, q = _lerp(A, D, t), _lerp(B, C, t)
        c.line(p[0], p[1], q[0], q[1], 0.0035, scale(roof, 0.72), 0.55)
    c.line(D[0], D[1], C[0], C[1], 0.012, mix(roof, WHITE, 0.45), 0.8)
    soft_disc(c, 0.02, v0 + wh + 0.10, 0.12, 0.05, WHITE, 0.14, 1.3, add=True)
    # chimney
    _prism(c, 0.10, v0 + wh + 0.07, 0.05, 0.12, 0.03, 0.015, (0.78, 0.45, 0.36), lift=0.1)
    # front gable face
    c.poly([(x0, v0), (x1, v0), (x1, v0 + wh), (um, v0 + wh + rh), (x0, v0 + wh)], wall, lift=0.06)
    soft_disc(c, x0 + 0.05, v0 + 0.22, 0.3, 0.2, WHITE, 0.25, 1.3, add=True)
    c.line(x0 - 0.035, v0 + wh - 0.025, um, v0 + wh + rh + 0.02, 0.018, scale(roof, 0.8))
    c.line(um, v0 + wh + rh + 0.02, x1 + 0.045, v0 + wh - 0.015, 0.018, scale(roof, 0.8))
    # big glass window with warm interior
    wc = (-0.235, v0 + 0.17)
    c.rect(wc[0], wc[1], 0.22, 0.17, (1.0, 0.80, 0.50), lift=0.2)
    c.glow(wc[0], wc[1], 0.22, (1.0, 0.78, 0.45), 0.35)
    c.rect(wc[0] - 0.03, wc[1] - 0.01, 0.10, 0.12, (0.99, 0.92, 0.72), lift=0.1, alpha=0.7)           # lamp / interior
    c.poly([(-0.34, wc[1] + 0.085), (-0.26, wc[1] + 0.085), (-0.31, wc[1] - 0.085), (-0.345, wc[1] - 0.085)], WHITE, alpha=0.25)
    c.rect(wc[0], wc[1], 0.006, 0.17, (0.2, 0.2, 0.22), lift=0)
    c.rect(wc[0], wc[1] + 0.02, 0.22, 0.006, (0.2, 0.2, 0.22), lift=0)
    c.rect(wc[0], wc[1], 0.235, 0.18, (0.2, 0.2, 0.22), alpha=0.0, lift=0)
    for sx in (-1, 1):
        c.rect(wc[0] + sx * 0.113, wc[1], 0.007, 0.178, (0.22, 0.22, 0.24), lift=0)
    c.rect(wc[0], wc[1] + 0.089, 0.235, 0.007, (0.22, 0.22, 0.24), lift=0)
    c.rect(wc[0], wc[1] - 0.089, 0.235, 0.007, (0.22, 0.22, 0.24), lift=0)
    # door, small round window in the gable
    c.rect(0.06, v0 + 0.095, 0.095, 0.19, (0.55, 0.36, 0.22), lift=0.15)
    c.rect(0.06, v0 + 0.095, 0.075, 0.17, (0.66, 0.45, 0.28), lift=0.12)
    c.circle(0.085, v0 + 0.09, 0.006, BRASS, lift=0.1)
    c.ellipse(-0.10, v0 + wh + 0.065, 0.032, 0.032, (1.0, 0.82, 0.52), lift=0.1)
    c.glow(-0.10, v0 + wh + 0.065, 0.1, (1.0, 0.8, 0.5), 0.3)
    c.rect(0.06, v0 + 0.205, 0.13, 0.01, scale(roof, 0.9), lift=0.0)                      # canopy
    # trees and shrubs on the board
    for (u, v, r) in ((0.62, 0.13, 0.10), (0.74, 0.12, 0.08), (-0.74, 0.105, 0.07)):
        c.line(u, v - 0.02, u, v + r * 0.5, 0.012, (0.42, 0.28, 0.18))
        _bush(c, u, v + r * 0.95, r, rng, n=6)
    for u in (-0.30, -0.14, 0.17):
        _bush(c, u, 0.115, 0.032, rng, n=3)


@sprop("hp_key_tag", aspect=2.6, fill=0.46)
def hp_key_tag(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.22)
    ox, oy = -0.18, 0.15
    k = 0.52                                                             # keys lie flat: v is squashed
    # two keys fanned out under the ring
    for ang, ln, col in ((-168, 0.50, BRASS), (-205, 0.44, (0.84, 0.86, 0.88))):
        pts = [(0.0, -0.022), (ln, -0.022), (ln, 0.0), (ln - 0.03, 0.0), (ln - 0.03, 0.026), (ln - 0.075, 0.026),
               (ln - 0.075, 0.0), (ln - 0.12, 0.0), (ln - 0.12, 0.026), (ln - 0.16, 0.026), (ln - 0.16, 0.022), (0.0, 0.022)]
        P_ = _rot(pts, ang, ox, oy, k)
        shift = [(x + 0.012, y - 0.03) for x, y in P_]
        c.poly(shift, BLACK, alpha=0.22)
        c.poly(P_, col, lift=0.2)
        bu, bv = ox + math.cos(math.radians(ang)) * -0.06, oy + math.sin(math.radians(ang)) * -0.06 * k
        bu, bv = _rot([(-0.07, 0.0)], ang, ox, oy, k)[0]
        c.ellipse(bu + 0.012, bv - 0.025, 0.075, 0.075 * k, BLACK, alpha=0.2, lift=0)
        c.ellipse(bu, bv, 0.075, 0.075 * k, col, lift=0.25)
        c.ellipse(bu, bv + 0.004, 0.032, 0.032 * k, scale(col, 0.45), lift=0)
        gloss(c, bu - 0.025, bv + 0.012, 0.03, 0.012, 0, 0.7)
        s0 = _rot([(0.1, 0.0)], ang, ox, oy, k)[0]
        s1 = _rot([(ln - 0.02, 0.0)], ang, ox, oy, k)[0]
        c.line(s0[0], s0[1] + 0.006, s1[0], s1[1] + 0.006, 0.006, mix(col, WHITE, 0.6), 0.7)
    # label tag
    tag = [(0.0, -0.075), (0.42, -0.075), (0.42, 0.075), (0.0, 0.075)]
    TP = _rot([(x - 0.07, y) for x, y in tag], 24, ox + 0.50, oy + 0.02, 0.58)
    c.poly([(x + 0.012, y - 0.03) for x, y in TP], BLACK, alpha=0.25)
    c.poly(TP, P.accent, lift=0.15)
    edge = _rot([(0.35, -0.075), (0.35, 0.075)], 24, ox + 0.50, oy + 0.02, 0.58)
    c.line(TP[0][0], TP[0][1] + 0.0, TP[3][0], TP[3][1], 0.012, scale(P.accent, 0.7), 0.6)
    lab = _rot([(0.12, -0.04), (0.40, -0.04), (0.40, 0.04), (0.12, 0.04)], 24, ox + 0.50 - 0.07, oy + 0.02, 0.58)
    c.poly(lab, (0.98, 0.97, 0.94), lift=0.05)
    for j in range(2):
        a_ = _rot([(0.15, -0.015 + j * 0.03), (0.35 - j * 0.07, -0.015 + j * 0.03)], 24, ox + 0.50 - 0.07, oy + 0.02, 0.58)
        c.line(a_[0][0], a_[0][1], a_[1][0], a_[1][1], 0.007, scale(P.accent_dark, 0.8), 0.8)
    hole = _rot([(0.03, 0.0)], 24, ox + 0.50 - 0.07, oy + 0.02, 0.58)[0]
    c.ellipse(hole[0], hole[1], 0.016, 0.01, (0.30, 0.28, 0.26), lift=0)
    c.line(ox, oy, hole[0], hole[1], 0.008, (0.80, 0.82, 0.85))
    # steel ring
    c.ellipse(ox + 0.005, oy - 0.012, 0.085, 0.085 * k, BLACK, alpha=0.22, lift=0)
    arc(c, ox, oy, 0.085, 0.085 * k, 0, 360, 0.016, (0.58, 0.60, 0.63), steps=18)
    arc(c, ox - 0.003, oy + 0.004, 0.085, 0.085 * k, 40, 200, 0.008, (0.95, 0.96, 0.98), 0.9, steps=10)
    soft_disc(c, 0.15, 0.20, 0.5, 0.12, WHITE, 0.10, 1.4, add=True)


@sprop("hp_blueprint", aspect=4.0, fill=0.42)
def hp_blueprint(c, P):
    rng = c.rng
    
    paper = (0.14, 0.34, 0.58)
    line = (0.80, 0.90, 0.98)

    def pt(x, y):
        return (x * (0.84 - 0.20 * y), 0.015 + 0.36 * y)
    S4 = [pt(-1, 0), pt(1, 0), pt(1, 1), pt(-1, 1)]
    c.poly(S4, paper, lift=0.14)
    soft_disc(c, -0.3, 0.30, 0.7, 0.14, (0.5, 0.7, 1.0), 0.25, 1.3, add=True)
    for i in range(-5, 6):                                               # fine grid
        a, b = pt(i / 5.0, 0), pt(i / 5.0, 1)
        c.line(a[0], a[1], b[0], b[1], 0.0025, line, 0.18)
    for j in range(0, 6):
        a, b = pt(-1, j / 5.0), pt(1, j / 5.0)
        c.line(a[0], a[1], b[0], b[1], 0.0025, line, 0.18)
    # floor plan drawn in the sheet
    def seg(x0, y0, x1, y1, w=0.005, al=0.9):
        a, b = pt(x0, y0), pt(x1, y1)
        c.line(a[0], a[1], b[0], b[1], w, line, al)
    for (a, b, c_, d) in ((-0.62, 0.12, 0.28, 0.12), (0.28, 0.12, 0.28, 0.88), (0.28, 0.88, -0.62, 0.88), (-0.62, 0.88, -0.62, 0.12),
                          (-0.10, 0.12, -0.10, 0.55), (-0.62, 0.55, 0.05, 0.55), (-0.30, 0.55, -0.30, 0.88)):
        seg(a, b, c_, d, 0.007)
    for (a, b, c_, d) in ((0.36, 0.2, 0.84, 0.2), (0.36, 0.45, 0.84, 0.45), (0.36, 0.7, 0.84, 0.7), (0.36, 0.2, 0.36, 0.7), (0.84, 0.2, 0.84, 0.7)):
        seg(a, b, c_, d, 0.004, 0.7)
    arcp = [pt(-0.10 + 0.14 * math.cos(math.radians(t)), 0.55 + 0.20 * math.sin(math.radians(t))) for t in range(0, 91, 15)]
    for p, q in zip(arcp, arcp[1:]):
        c.line(p[0], p[1], q[0], q[1], 0.004, line, 0.8)
    # rolled blueprints on the sheet
    for (u, v, ln, ang, rr) in ((-0.15, 0.36, 0.95, 4, 0.05), (0.15, 0.31, 0.80, -9, 0.042)):
        a0 = math.radians(ang)
        du, dv = math.cos(a0) * ln / 2, math.sin(a0) * ln / 2
        c.line(u - du, v - dv, u + du, v + dv, rr * 2.0, (0.80, 0.82, 0.80))
        c.line(u - du, v - dv + rr * 0.1, u + du, v + dv + rr * 0.1, rr * 1.4, (0.93, 0.94, 0.92))
        c.line(u - du, v - dv + rr * 0.55, u + du, v + dv + rr * 0.55, rr * 0.35, (0.70, 0.74, 0.78), 0.7)
        eu, ev = u + du, v + dv                                          # open end with spiral
        c.ellipse(eu, ev, rr * 0.55, rr, (0.88, 0.89, 0.86), lift=0.1)
        c.ellipse(eu + 0.002, ev, rr * 0.36, rr * 0.62, (0.55, 0.62, 0.70), lift=0)
        c.ellipse(eu + 0.003, ev, rr * 0.18, rr * 0.30, (0.15, 0.22, 0.34), lift=0)
        for fr in (0.25, 0.6):                                           # rubber bands
            bu, bv = u - du + 2 * du * fr, v - dv + 2 * dv * fr
            c.rect(bu, bv, 0.014, rr * 2.05, P.accent, lift=0.2, alpha=0.95)
    soft_disc(c, -0.1, 0.40, 0.9, 0.12, WHITE, 0.10, 1.4, add=True)


@sprop("hp_sold_sign", aspect=0.78, fill=1.0)
def hp_sold_sign(c, P):
    ao(c, 0.0, 0.0, 0.50, 0.10)
    wood = (0.62, 0.43, 0.26)
    _prism(c, 0.0, 0.0, 0.34, 0.05, 0.08, 0.04, scale(wood, 0.9), top=wood, side=scale(wood, 0.6))
    hshade_box(c, 0.0, 0.50, 0.035, 0.90, mix(wood, WHITE, 0.25), scale(wood, 0.6))
    c.rect(0.15, 0.93, 0.38, 0.03, scale(wood, 0.8), lift=0.1)
    c.line(0.0, 0.80, 0.14, 0.93, 0.02, scale(wood, 0.8))
    c.rect(0.15, 0.80, 0.025, 0.07, (0.5, 0.5, 0.5), lift=0)
    c.rect(0.14, 0.64, 0.58, 0.28, (0.98, 0.97, 0.95), lift=0.08, r=0.02)
    c.rect(0.14, 0.655, 0.52, 0.18, (0.93, 0.28, 0.22), lift=0.14, r=0.012)
    c.rect(0.14, 0.545, 0.52, 0.05, P.accent, lift=0.12)
    soft_disc(c, -0.06, 0.74, 0.22, 0.08, WHITE, 0.30, 1.2, add=True)
    c.text("SOLD", 0.14, 0.655, 0.13, (1.0, 0.97, 0.94), 0.22)
    c.ellipse(0.0, 0.88, 0.016, 0.016, (0.4, 0.4, 0.4), lift=0.2)


@niche("real-estate", "Real estate", subjects=("hp_house_model",),
       strong=("real estate", "property dealer", "realtor", "real estate agent", "apartments", "flats for sale", "builder", "property",
               "makaan", "makan", "plots", "ghar bechna", "प्रॉपर्टी", "मकान", "जमीन", "रियल एस्टेट", "फ्लैट"),
       weak=("rent", "house", "flat", "sale", "broker", "villa", "home", "kiraya"),
       accent="#1f6f8b", mood="light", group="home", avoid=("interior",))
def real_estate(S):
    P = S.pal
    u0, u1 = _span(S)
    sk_top, sk_bot = _sky(P)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # wood slat panel left and right, glass wall between
        slat = mix(P.surface, WHITE, 0.15)
        S.rect(-0.45, 0.30, 1.9, 1.2, scale(slat, 0.92), lift=0.0)
        S.rect(2.40, 0.30, 1.6, 1.2, scale(slat, 0.92), lift=0.0)
        for i in range(0, 40):
            uu = -1.4 + i * 0.075
            if uu < 0.28 or uu > 1.7:
                S.rect(uu, 0.3, 0.007, 1.2, scale(slat, 0.72), lift=0.0, alpha=0.5)
        for i in range(3):
            ux = 0.52 + i * 0.52
            S.gradient_rect(ux - 0.245, 0.02, ux + 0.245, 0.60, sk_top, sk_bot)
            S.glow(ux, 0.3, 0.55, P.light, 0.2)
        # view: city blocks and trees seen through the glass (blurred)
        for k, (x, w, h) in enumerate(((0.35, 0.10, 0.22), (0.50, 0.07, 0.30), (0.66, 0.12, 0.18), (0.90, 0.09, 0.26), (1.10, 0.13, 0.20),
                                       (1.30, 0.08, 0.32), (1.48, 0.12, 0.17), (1.66, 0.10, 0.24))):
            S.rect(x, 0.60 - h / 2, w, h, mix(sk_bot, scale(P.wall_bot, 0.8), 0.55 + 0.05 * (k % 3)), lift=0.0)
        for x in (0.30, 0.78, 1.20, 1.56, 1.75):
            S.ellipse(x, 0.55, 0.09, 0.07, (0.30, 0.50, 0.30) if P.mood != "dark" else (0.10, 0.18, 0.16), lift=0.1)
        # frames
        dark = scale(P.ink, 1.6)
        for i in range(4):
            S.rect(0.265 + i * 0.52, 0.30, 0.016, 0.62, dark, lift=0.0)
        S.rect(1.0, 0.012, 1.60, 0.03, dark, lift=0.0)
        S.rect(1.0, 0.602, 1.60, 0.025, dark, lift=0.0)
        S.pendant(0.55, -0.1, 0.17, (1.0, 0.86, 0.6), 0.08)
        S.pendant(1.55, -0.1, 0.13, (1.0, 0.86, 0.6), 0.08)
        S.rect(1.0, 0.64, 4.0, 0.06, scale(P.wall_bot, 0.78), lift=0.0)              # skirting / ledge
        S.floor(0.62, P.floor_top, P.floor_bot)
    S.wood(u0, 0.62, u1, 1.65, mix(P.surface, WHITE, 0.22) if P.mood != 'dark' else P.surface, plank=0.12, grain=0.6)
    S.soft(1.05, 0.82, 0.8, 0.16, P.light, 0.26, 1.4, add=True)
    S.rect(1.0, 0.62, 5.0, 0.007, scale(P.surface, 0.5), lift=0.0)
    if P.mood == "dark":
        S.soft(1.14, 0.80, 0.7, 0.14, (1.0, 0.78, 0.45), 0.35, 1.4, add=True)
    S.put("hp_blueprint", 0.92, 0.89, 0.20, color=P, shadow=False)
    S.put("hp_sold_sign", 1.56, 0.80, 0.24, color=P)
    S.put("hp_house_model", 1.14, 0.92, 0.40, color=P, subject=True, shadow_w=1.0)
    S.put("hp_key_tag", 1.28, 1.01, 0.20, color=P)
    S.focus("detail", 1.16, 0.74)
    with S.near():
        S.soft(1.66, 1.06, 0.08, 0.08, mix(P.accent, WHITE, 0.5), 0.45, 0.6, add=True)


# ====================================================================================================== interior design
@sprop("hp_sofa", aspect=2.9, fill=0.80)
def hp_sofa(c, P):
    rng = c.rng
    fab = mix(P.accent_dark, P.accent, 0.55)
    fab = mix(fab, (0.55, 0.50, 0.46), 0.25)
    lo, hi, deep = scale(fab, 0.78), scale(fab, 1.12), scale(fab, 0.55)
    wood = (0.55, 0.38, 0.24)
    # tapered wooden legs
    for u in (-1.02, 1.02):
        c.poly([(u - 0.04, 0.115), (u + 0.04, 0.115), (u + 0.022, 0.0), (u - 0.022, 0.0)], wood, lift=0.2)
        c.line(u - 0.02, 0.10, u - 0.012, 0.01, 0.006, mix(wood, WHITE, 0.4), 0.6)
    for u in (-0.9, 0.9):
        c.poly([(u - 0.03, 0.12), (u + 0.03, 0.12), (u + 0.018, 0.03), (u - 0.018, 0.03)], scale(wood, 0.7), lift=0.15)
    # frame and back
    c.rect(0.0, 0.215, 2.26, 0.20, lo, r=0.05, lift=0.10)
    c.rect(0.0, 0.57, 2.06, 0.46, fab, r=0.09, lift=0.14)
    for k, u in enumerate((-0.68, 0.0, 0.68)):                                  # back cushions
        c.rect(u, 0.57, 0.66, 0.42, mix(fab, WHITE, 0.05 + 0.03 * (k % 2)), r=0.10, lift=0.2)
        soft_disc(c, u + 0.10, 0.40, 0.34, 0.07, BLACK, 0.25, 1.3)
        soft_disc(c, u - 0.12, 0.66, 0.26, 0.10, WHITE, 0.16, 1.2, add=True)
        c.line(u - 0.31, 0.74, u + 0.31, 0.74, 0.007, mix(fab, WHITE, 0.3), 0.4)
        for bx in (-0.14, 0.14):
            c.circle(u + bx, 0.60, 0.014, scale(fab, 0.7), lift=0.1)
    # arms
    c.rect(-1.03, 0.36, 0.28, 0.46, lo, r=0.11, lift=0.2)
    c.rect(1.03, 0.36, 0.28, 0.46, scale(lo, 0.8), r=0.11, lift=0.2)
    c.rect(-1.03, 0.55, 0.30, 0.10, mix(lo, WHITE, 0.10), r=0.05, lift=0.15)
    c.rect(1.03, 0.55, 0.30, 0.10, scale(lo, 0.85), r=0.05, lift=0.15)
    soft_disc(c, -1.08, 0.45, 0.08, 0.2, WHITE, 0.2, 1.2, add=True)
    # seat cushions
    for k, u in enumerate((-0.64, 0.0, 0.64)):
        c.rect(u, 0.355, 0.62, 0.115, deep, r=0.04, lift=0.0, alpha=0.8)
        c.rect(u, 0.395, 0.62, 0.15, mix(fab, WHITE, 0.07), r=0.06, lift=0.22)
        c.rect(u, 0.455, 0.60, 0.035, mix(fab, WHITE, 0.2), r=0.018, lift=0.0, alpha=0.8)
        soft_disc(c, u - 0.10, 0.45, 0.24, 0.04, WHITE, 0.25, 1.2, add=True)
    for u in (-0.32, 0.32):
        c.line(u, 0.32, u, 0.47, 0.008, deep, 0.7)
    # throw pillows
    for (u, v, w, ang, col) in ((-0.62, 0.62, 0.30, 14, mix(P.accent_light, fab, 0.35)), (-0.43, 0.58, 0.28, -10, mix(CREAM, fab, 0.25)), (0.78, 0.60, 0.30, -12, mix(P.accent2, fab, 0.45))):
        pts = _rot([(-w / 2, -w / 2), (w / 2, -w / 2), (w / 2 + 0.01, w / 2), (-w / 2 - 0.01, w / 2)], ang, u, v)
        c.poly([(x + 0.012, y - 0.02) for x, y in pts], BLACK, alpha=0.22)
        c.poly(pts, col, lift=0.16)
        mid = _rot([(0.0, -w / 2 + 0.01), (0.0, w / 2 - 0.01)], ang, u, v)
        c.line(mid[0][0], mid[0][1], mid[1][0], mid[1][1], 0.012, mix(col, BLACK, 0.12), 0.35)
        c.circle(u, v, 0.012, scale(col, 0.7), lift=0)
    # blanket on the right arm with stripes
    c.poly([(0.88, 0.62), (1.18, 0.60), (1.20, 0.30), (0.92, 0.34)], mix(CREAM, fab, 0.2), lift=0.14)
    for k in range(5):
        y = 0.58 - k * 0.055
        c.line(0.92 + k * 0.005, y, 1.18, y - 0.02, 0.012, P.accent, 0.8)
    # fabric weave
    for _ in range(46):
        u, v = rng.uniform(-1.0, 1.0), rng.uniform(0.15, 0.78)
        c.line(u, v, u + rng.uniform(0.02, 0.06), v + rng.uniform(-0.01, 0.01), 0.003, mix(fab, rng.choice((WHITE, BLACK)), 0.2), 0.35)


@sprop("hp_floor_lamp", aspect=0.42, fill=1.0)
def hp_floor_lamp(c, P):
    ao(c, 0.0, 0.0, 0.36, 0.07)
    br = (0.82, 0.66, 0.36)
    c.glow(0.0, 0.88, 0.75, (1.0, 0.82, 0.52), 0.40)
    disc(c, 0.0, 0.02, 0.15, scale(br, 0.7), TILT, 0.2)
    c.rect(0.0, 0.40, 0.022, 0.74, br, lift=0.25)
    c.line(-0.007, 0.05, -0.007, 0.74, 0.006, mix(br, WHITE, 0.7), 0.7)
    c.poly([(-0.19, 0.78), (0.19, 0.78), (0.14, 1.0), (-0.14, 1.0)], (1.0, 0.92, 0.74), lift=0.05)       # lit drum shade
    c.rect(0.0, 0.89, 0.34, 0.20, (1.0, 0.90, 0.68), alpha=0.5, lift=0.0)
    c.ellipse(0.0, 1.0, 0.14, 0.04, (0.85, 0.70, 0.46), lift=0)
    c.ellipse(0.0, 0.78, 0.19, 0.045, (1.0, 0.96, 0.82), lift=0.1)
    soft_disc(c, 0.07, 0.89, 0.1, 0.12, (0.85, 0.55, 0.25), 0.3, 1.2)
    c.ellipse(0.0, 0.78, 0.12, 0.028, (1.0, 0.99, 0.9), lift=0, alpha=0.9)


@sprop("hp_plant", aspect=0.9, fill=1.0)
def hp_plant(c, P):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.50, 0.09)
    pot = (0.92, 0.88, 0.80)
    hshade_box(c, 0.0, 0.14, 0.40, 0.28, pot, scale(pot, 0.62), r=0.05)
    c.ellipse(0.0, 0.01, 0.20, 0.20 * TILT, scale(pot, 0.62), lift=0)
    hshade_box(c, 0.0, 0.14, 0.40, 0.28, pot, scale(pot, 0.62), r=0.05)
    disc(c, 0.0, 0.28, 0.205, mix(pot, WHITE, 0.2), TILT, 0.0, rim=True)
    c.ellipse(0.0, 0.285, 0.17, 0.17 * TILT, (0.26, 0.17, 0.12), lift=0)
    c.rect(0.0, 0.05, 0.40, 0.012, P.accent, alpha=0.7, lift=0)
    gloss(c, -0.12, 0.17, 0.02, 0.10, 0, 0.5)
    # stems and big leaves fanning out
    cols = ((0.14, 0.40, 0.20), (0.20, 0.50, 0.24), (0.12, 0.34, 0.17), (0.26, 0.56, 0.28))
    for i in range(11):
        a = 90 + (i - 5) * 14 + rng.uniform(-5, 5)
        ln = rng.uniform(0.34, 0.62)
        base = (rng.uniform(-0.05, 0.05), 0.29)
        tip = (base[0] + math.cos(math.radians(a)) * ln, base[1] + math.sin(math.radians(a)) * ln)
        c.line(base[0], base[1], tip[0], tip[1], 0.012, (0.22, 0.38, 0.18), 0.9)
        leaf(c, tip[0] - math.cos(math.radians(a + 25)) * 0.02, tip[1], 0.26, a + rng.uniform(-30, 30), cols[i % 4], 0.62)
    soft_disc(c, -0.1, 0.75, 0.28, 0.16, (0.8, 1.0, 0.5), 0.22, 1.3, add=True)


@sprop("hp_framed_art", aspect=0.78, fill=1.0)
def hp_framed_art(c, P):
    frame = (0.20, 0.17, 0.15)
    c.rect(0.02, -0.015, 0.78, 1.0, BLACK, alpha=0.22, lift=0)
    c.rect(0.0, 0.5, 0.78, 1.0, frame, lift=0.12)
    c.rect(0.0, 0.5, 0.72, 0.94, (0.98, 0.97, 0.94), lift=0.03)
    c.rect(0.0, 0.5, 0.60, 0.80, mix(P.accent_light, WHITE, 0.4), lift=0.06)
    c.circle(0.04, 0.62, 0.17, P.accent, lift=0.18)
    c.ellipse(-0.14, 0.26, 0.28, 0.16, mix(P.accent_dark, P.ink, 0.1), lift=0.15, angle=14)
    c.ellipse(0.12, 0.20, 0.24, 0.12, mix(P.accent2, WHITE, 0.2), lift=0.1, angle=-8)
    c.rect(0.0, 0.14, 0.60, 0.055, scale(P.accent_dark, 0.8), lift=0.05)
    soft_disc(c, -0.2, 0.85, 0.4, 0.3, WHITE, 0.20, 1.2, add=True)
    c.line(-0.38, 0.99, 0.30, 0.82, 0.012, WHITE, 0.15)


@sprop("hp_swatches", aspect=1.35, fill=0.62)
def hp_swatches(c, P):
    rng = c.rng
    # fabric / material fan pinned at the bottom
    cols = (P.accent, P.accent_light, (0.30, 0.38, 0.36), (0.88, 0.80, 0.66), (0.55, 0.36, 0.24), (0.93, 0.92, 0.88), P.accent2)
    px_, py_ = -0.28, 0.06
    for i in range(7):
        ang = 100 - i * 11
        pts = _rot([(-0.075, 0.0), (0.075, 0.0), (0.082, 0.82), (-0.082, 0.82)], ang - 90, px_, py_)
        c.poly([(x + 0.01, y - 0.015) for x, y in pts], BLACK, alpha=0.20)
        c.poly(pts, cols[i], lift=0.12)
        for k in range(6):                                              # weave texture
            a = _rot([(-0.07, 0.15 + k * 0.1), (0.07, 0.15 + k * 0.1)], ang - 90, px_, py_)
            c.line(a[0][0], a[0][1], a[1][0], a[1][1], 0.004, mix(cols[i], BLACK if k % 2 else WHITE, 0.25), 0.28)
        e = _rot([(-0.075, 0.82), (0.082, 0.82)], ang - 90, px_, py_)
        c.line(e[0][0], e[0][1], e[1][0], e[1][1], 0.008, mix(cols[i], WHITE, 0.4), 0.8)
    c.circle(px_, py_ + 0.03, 0.035, (0.75, 0.75, 0.78), lift=0.3)
    c.circle(px_, py_ + 0.03, 0.012, (0.35, 0.35, 0.38), lift=0)
    # material tiles: wood, marble, linen
    for i, (u, v, w, col) in enumerate(((0.36, 0.06, 0.34, (0.66, 0.46, 0.28)), (0.40, 0.14, 0.30, (0.92, 0.92, 0.9)), (0.33, 0.22, 0.30, P.accent_light))):
        c.rect(u + 0.012, v + 0.015, w, 0.055, BLACK, alpha=0.2, lift=0)
        c.rect(u, v + 0.02, w, 0.055, col, lift=0.2)
        c.rect(u, v + 0.047, w, 0.01, mix(col, WHITE, 0.5), alpha=0.7, lift=0)
    for k in range(6):
        c.line(0.24 + k * 0.04, 0.045, 0.27 + k * 0.04, 0.10, 0.003, (0.5, 0.33, 0.2), 0.5)
    for _ in range(4):
        u = rng.uniform(0.32, 0.48)
        c.line(u, 0.16, u + 0.08, 0.20, 0.003, (0.6, 0.6, 0.62), 0.6)


@sprop("hp_coffee_table", aspect=1.6, fill=0.62)
def hp_coffee_table(c, P):
    wood = (0.64, 0.44, 0.28)
    for u in (-0.55, 0.55):
        c.line(u * 0.95, 0.0, u * 0.72, 0.32, 0.03, scale(wood, 0.55))
        c.line(u * 0.95 - 0.01, 0.02, u * 0.72 - 0.01, 0.30, 0.01, mix(wood, WHITE, 0.3), 0.6)
    c.ellipse(0.0, 0.34, 0.80, 0.80 * 0.30, scale(wood, 0.55), lift=0)
    disc(c, 0.0, 0.38, 0.80, wood, 0.30, 0.15)
    for k in range(7):
        arc(c, 0.0, 0.38, 0.2 + k * 0.1, (0.2 + k * 0.1) * 0.30, 190 + k * 5, 340 - k * 7, 0.004, scale(wood, 0.85), 0.35, steps=8)
    soft_disc(c, -0.25, 0.44, 0.45, 0.07, WHITE, 0.22, 1.2, add=True)


@sprop("hp_vase_stems", aspect=0.45, fill=1.0)
def hp_vase_stems(c, P):
    rng = c.rng
    for i in range(5):
        a = 90 + (i - 2) * 17
        ln = rng.uniform(0.6, 0.85)
        c.line(0.0, 0.25, math.cos(math.radians(a)) * ln * 0.5, 0.25 + math.sin(math.radians(a)) * ln, 0.01, (0.35, 0.5, 0.25), 0.9)
        tx, ty = math.cos(math.radians(a)) * ln * 0.5, 0.25 + math.sin(math.radians(a)) * ln
        for k in range(5):
            c.ellipse(tx + math.cos(k * 1.26) * 0.03, ty + math.sin(k * 1.26) * 0.03, 0.03, 0.04, mix((0.96, 0.93, 0.85), P.accent_light, 0.3), lift=0.15)
        c.circle(tx, ty, 0.016, (0.85, 0.7, 0.3), lift=0.1)
    hshade_box(c, 0.0, 0.14, 0.26, 0.26, (0.95, 0.94, 0.90), (0.62, 0.60, 0.56), r=0.08)
    c.ellipse(0.0, 0.27, 0.10, 0.04, (0.45, 0.43, 0.40), lift=0)
    gloss(c, -0.07, 0.16, 0.014, 0.08, 0, 0.6)


@niche("interior-design", "Interior design", subjects=("hp_sofa",),
       strong=("interior design", "interior designer", "interior designers", "home decor", "home interiors", "furniture", "living room",
               "modular kitchen", "interior decorator", "इंटीरियर", "इंटीरियर डिज़ाइन", "फर्नीचर", "होम डेकोर", "interiors"),
       weak=("decor", "sofa", "wardrobe", "renovation", "curtains", "decorator"),
       accent="#b08968", mood="warm", group="home", avoid=("construction",))
def interior_design(S):
    P = S.pal
    u0, u1 = _span(S)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        S.rect(1.0, 0.34, 6.0, 0.60, mix(P.wall_top, P.accent_light, 0.18), lift=0.0, alpha=0.5)
        # tall window with sheer curtains at the left, bookshelf at the right
        S.gradient_rect(0.30, 0.05, 0.78, 0.56, (0.72, 0.85, 0.96), (0.96, 0.97, 0.98), r=0.01)
        S.glow(0.54, 0.30, 0.8, P.light, 0.30)
        for k in range(6):
            S.rect(0.18 + k * 0.045, 0.30, 0.04, 0.60, mix(CREAM, P.accent_light, 0.25 + 0.1 * (k % 2)), lift=0.0, alpha=0.8)
            S.rect(0.90 - k * 0.045, 0.30, 0.04, 0.60, mix(CREAM, P.accent_light, 0.25 + 0.1 * (k % 2)), lift=0.0, alpha=0.8)
        S.rect(1.78, 0.28, 0.34, 0.52, scale(P.surface, 0.9), lift=0.0)
        for k in range(3):
            S.rect(1.78, 0.10 + k * 0.17, 0.32, 0.012, scale(P.surface, 0.65), lift=0.0)
            for j in range(7):
                S.rect(1.66 + j * 0.037, 0.19 + k * 0.17 - 0.03, 0.026, 0.06 + 0.02 * ((j * 3 + k) % 3),
                       (P.accent, P.accent_light, P.paper, P.accent2, P.accent_dark)[(j + k * 2) % 5], lift=0.0, alpha=0.9)
        for k in range(4):                                                                   # wall panelling and a round mirror
            S.rect(-0.2 + k * 0.5, 0.32, 0.38, 0.46, mix(P.wall_top, P.wall_bot, 0.5), lift=0.0, alpha=0.5)
            S.rect(-0.2 + k * 0.5, 0.32, 0.38, 0.46, scale(P.wall_bot, 0.8), lift=0.0, alpha=0.12)
        S.circle(1.42, 0.22, 0.16, scale(P.accent, 0.7), lift=0.05)
        S.circle(1.42, 0.22, 0.14, (0.86, 0.92, 0.95), lift=0.2)
        S.pendant(1.30, -0.1, 0.22, (1.0, 0.86, 0.6), 0.10)
        S.rect(1.0, 0.615, 6.0, 0.035, mix(P.wall_bot, WHITE, 0.4), lift=0.0)              # skirting
        S.floor(0.63, P.floor_top, P.floor_bot)
    S.wood(u0, 0.63, u1, 1.65, mix(P.floor_top, WHITE, 0.10), plank=0.10, grain=0.5)
    S.soft(0.62, 0.84, 0.30, 0.18, P.light, 0.22, 1.5, add=True)
    # rug under sofa and table (perspective trapezoid with border and stripes)
    rug = mix(P.accent_light, CREAM, 0.5)
    S.rect(1.06, 0.87, 1.20, 0.30, rug, lift=0.0)
    S.rect(1.06, 0.87, 1.14, 0.26, mix(P.accent_light, P.accent, 0.3), lift=0.0)
    S.rect(1.06, 0.87, 1.04, 0.22, rug, lift=0.0)
    for k in range(7):
        S.rect(1.06, 0.78 + k * 0.026, 1.0, 0.004, P.accent, lift=0.0, alpha=1.0)
    S.rect(1.06, 0.87, 0.006, 0.22, scale(P.accent_light, 0.9), lift=0.0)
    S.rect(1.06, 0.725, 1.2, 0.012, scale(rug, 0.7), lift=0.0)
    S.put("hp_framed_art", 1.00, 0.52, 0.28, color=P, shadow=False, framed=True)
    S.put("hp_framed_art", 1.46, 0.46, 0.17, color=P, shadow=False, framed=False)
    S.put("hp_sofa", 1.04, 0.83, 0.43, color=P, subject=True, shadow_w=0.9)
    S.put("hp_plant", 0.52, 0.90, 0.44, color=P)
    S.put("hp_floor_lamp", 1.60, 0.80, 0.66, color=P)
    S.soft(1.42, 0.90, 0.30, 0.10, (1.0, 0.82, 0.5), 0.22, 1.5, add=True)
    S.put("hp_coffee_table", 1.08, 1.03, 0.21, color=P, shadow_w=0.4)
    S.put("hp_swatches", 1.00, 0.935, 0.17, color=P, shadow=False)
    S.put("hp_vase_stems", 1.30, 0.945, 0.14, color=P, framed=False, shadow=False)
    S.focus("detail", 1.05, 0.69)
    with S.near():
        S.soft(1.66, 1.07, 0.09, 0.09, mix(P.accent, WHITE, 0.5), 0.40, 0.6, add=True)


# ====================================================================================================== construction
@sprop("hp_hard_hat", aspect=1.7, fill=0.80)
def hp_hard_hat(c, P):
    rng = c.rng
    hat = P.accent
    # brim (wide at the front) and shaded underside
    c.ellipse(0.0, 0.065, 0.69, 0.20, scale(hat, 0.55), lift=0)
    c.ellipse(0.0, 0.10, 0.68, 0.19, mix(hat, WHITE, 0.06), lift=0.16)
    c.ellipse(0.02, 0.07, 0.60, 0.10, scale(hat, 0.62), lift=0, alpha=0.45)
    # dome
    pts = [(0.52 * math.cos(math.radians(t)), 0.13 + 0.56 * math.sin(math.radians(t)) ** 0.85) for t in range(0, 181, 10)]
    c.poly(pts, hat, lift=0.24)
    soft_disc(c, 0.28, 0.40, 0.30, 0.36, scale(hat, 0.45), 0.55, 1.2)                      # shaded right flank
    soft_disc(c, -0.20, 0.52, 0.22, 0.25, WHITE, 0.45, 1.3, add=True)
    # centre ridge and side ridges
    c.poly([(-0.075, 0.18), (0.075, 0.18), (0.06, 0.69), (-0.06, 0.69)], mix(hat, WHITE, 0.10), lift=0.2)
    c.line(-0.075, 0.20, -0.06, 0.68, 0.006, mix(hat, WHITE, 0.55), 0.8)
    c.line(0.075, 0.20, 0.06, 0.68, 0.008, scale(hat, 0.55), 0.7)
    for sgn in (-1, 1):
        for k, (x0, x1) in enumerate(((0.27, 0.21), (0.44, 0.36))):
            c.line(sgn * x0, 0.18, sgn * x1, 0.55 - k * 0.11, 0.008, scale(hat, 0.6), 0.5)
            c.line(sgn * x0 - 0.01 * sgn, 0.19, sgn * x1 - 0.01 * sgn, 0.54 - k * 0.11, 0.004, mix(hat, WHITE, 0.4), 0.4)
    c.ellipse(0.0, 0.13, 0.52, 0.065, scale(hat, 0.8), lift=0.1)                            # band at the base of the dome
    gloss(c, -0.22, 0.60, 0.07, 0.025, 28, 0.85)
    gloss(c, -0.33, 0.37, 0.025, 0.09, 20, 0.5)
    # small badge on the front
    c.rect(0.0, 0.30, 0.16, 0.10, (0.98, 0.97, 0.94), lift=0.1, r=0.02)
    c.rect(0.0, 0.30, 0.12, 0.012, scale(hat, 0.55), lift=0)
    c.rect(0.0, 0.325, 0.07, 0.012, scale(hat, 0.55), lift=0)
    for _ in range(14):                                                                     # scuffs and dust
        u = rng.uniform(-0.4, 0.4)
        c.line(u, 0.2 + rng.uniform(0, 0.4), u + 0.03, 0.2 + rng.uniform(0, 0.4), 0.004, mix(hat, WHITE, 0.4), 0.18)


@sprop("hp_hi_vis_vest", aspect=0.95, fill=1.0)
def hp_hi_vis_vest(c, P):
    rng = c.rng
    fab = (0.92, 0.80, 0.10) if P.mood != "dark" else (0.88, 0.72, 0.08)
    fab = mix(fab, P.accent, 0.12)
    sil = (0.88, 0.90, 0.91)
    # hanger
    c.line(0.0, 1.03, 0.0, 0.99, 0.012, (0.75, 0.75, 0.78))
    arc(c, 0.02, 1.07, 0.04, 0.05, 220, 500, 0.012, (0.75, 0.75, 0.78), steps=8)
    c.line(0.0, 0.99, -0.34, 0.90, 0.014, (0.72, 0.72, 0.75))
    c.line(0.0, 0.99, 0.34, 0.90, 0.014, (0.72, 0.72, 0.75))
    # back panel seen through the neck
    c.poly([(-0.16, 0.97), (0.16, 0.97), (0.10, 0.62), (-0.10, 0.62)], scale(fab, 0.55), lift=0.1)
    L = [(-0.17, 0.97), (-0.44, 0.91), (-0.48, 0.71), (-0.39, 0.63), (-0.42, 0.02), (-0.02, 0.02), (-0.02, 0.60)]
    R = [(0.17, 0.97), (0.44, 0.91), (0.48, 0.71), (0.39, 0.63), (0.42, 0.02), (0.02, 0.02), (0.02, 0.60)]
    c.poly(L, fab, lift=0.20)
    c.poly(R, scale(fab, 0.84), lift=0.20)
    soft_disc(c, -0.22, 0.60, 0.20, 0.35, WHITE, 0.22, 1.2, add=True)
    soft_disc(c, 0.27, 0.40, 0.18, 0.4, BLACK, 0.18, 1.3)
    # mesh texture
    for _ in range(46):
        u, v = rng.uniform(-0.38, 0.38), rng.uniform(0.06, 0.85)
        if abs(u) > 0.03:
            c.ellipse(u, v, 0.008, 0.006, scale(fab, rng.uniform(0.7, 0.92)), lift=0, alpha=0.6)
    # reflective stripes: two bands and shoulder-to-hem straps
    for (v0, v1) in ((0.30, 0.37), (0.45, 0.52)):
        for sg in (-1, 1):
            c.poly([(sg * 0.02, v0), (sg * 0.415, v0 - 0.004), (sg * 0.41, v1 - 0.004), (sg * 0.02, v1)], sil if sg < 0 else scale(sil, 0.82), lift=0.15)
    for sg in (-1, 1):
        c.poly([(sg * 0.27, 0.935), (sg * 0.215, 0.955), (sg * 0.20, 0.02), (sg * 0.26, 0.02)], sil if sg < 0 else scale(sil, 0.82), lift=0.12)
        c.line(sg * 0.255, 0.92, sg * 0.235, 0.03, 0.006, WHITE, 0.5 if sg < 0 else 0.25)
    soft_disc(c, -0.30, 0.41, 0.12, 0.05, WHITE, 0.5, 1.2, add=True)
    # zip, pocket flaps, seams
    c.line(0.0, 0.58, 0.0, 0.03, 0.012, scale(fab, 0.5))
    for k in range(12):
        c.line(-0.007, 0.56 - k * 0.045, 0.007, 0.56 - k * 0.045, 0.004, (0.75, 0.75, 0.78), 0.9)
    c.rect(-0.30, 0.17, 0.16, 0.012, scale(fab, 0.6), lift=0)
    c.rect(0.30, 0.17, 0.16, 0.012, scale(fab, 0.5), lift=0)
    c.line(-0.46, 0.70, -0.40, 0.64, 0.01, scale(fab, 0.7), 0.7)
    c.line(0.46, 0.70, 0.40, 0.64, 0.01, scale(fab, 0.6), 0.7)
    c.ellipse(0.0, 0.015, 0.40, 0.02, scale(fab, 0.5), lift=0, alpha=0.5)


@sprop("hp_hammer", aspect=3.0, fill=0.40)
def hp_hammer(c, P):
    wood, steel = (0.70, 0.48, 0.28), (0.60, 0.63, 0.67)
    sv, ang, ox, oy = 0.52, 14, -0.60, 0.20
    hd = _rot([(0.0, -0.040), (0.95, -0.028), (0.95, 0.028), (0.0, 0.040)], ang, ox, oy, sv)
    c.poly([(x + 0.02, y - 0.04) for x, y in hd], BLACK, alpha=0.25)
    c.poly(hd, wood, lift=0.3)
    a, b = _rot([(0.02, 0.022), (0.93, 0.014)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.008, mix(wood, WHITE, 0.45), 0.7)
    # grip bands
    for t in (0.06, 0.12, 0.18, 0.24):
        a, b = _rot([(t, -0.04), (t, 0.04)], ang, ox, oy, sv)
        c.line(a[0], a[1], b[0], b[1], 0.006, scale(wood, 0.55), 0.55)
    hx = _rot([(0.9, 0.0)], ang, ox, oy, sv)[0]
    hp_ = _rot([(0.90, -0.15), (1.08, -0.15), (1.08, 0.15), (0.90, 0.15)], ang, ox, oy, sv)
    c.poly([(x + 0.02, y - 0.04) for x, y in hp_], BLACK, alpha=0.25)
    c.poly(hp_, steel, lift=0.35)
    claw = _rot([(0.90, -0.15), (0.90, 0.15), (0.72, 0.19), (0.66, 0.15), (0.80, 0.0), (0.66, -0.15), (0.72, -0.19)], ang, ox, oy, sv)
    face = _rot([(1.08, -0.15), (1.17, -0.12), (1.17, 0.12), (1.08, 0.15)], ang, ox, oy, sv)
    c.poly(face, scale(steel, 0.8), lift=0.3)
    a, b = _rot([(0.92, 0.13), (1.07, 0.13)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.012, WHITE, 0.55)
    soft_disc(c, hx[0] + 0.05, hx[1] + 0.02, 0.07, 0.04, WHITE, 0.45, 1.2, add=True)


@sprop("hp_level", aspect=7.0, fill=0.20)
def hp_level(c, P):
    ang, ox, oy, sv = -3, -0.70, 0.07, 0.5
    top = _rot([(0.0, -0.075), (1.4, -0.075), (1.4, 0.075), (0.0, 0.075)], ang, ox, oy + 0.03, sv)
    front = _rot([(0.0, -0.075), (1.4, -0.075), (1.4, -0.075), (0.0, -0.075)], ang, ox, oy, sv)
    c.poly([(x + 0.01, y - 0.03) for x, y in top], BLACK, alpha=0.25)
    c.poly([top[0], top[1], (top[1][0], top[1][1] - 0.04), (top[0][0], top[0][1] - 0.04)], scale(P.accent, 0.6), lift=0.1)
    c.poly(top, P.accent, lift=0.3)
    for t in (0.35, 0.70, 1.05):
        w = 0.20 if t == 0.70 else 0.14
        v = _rot([(t, 0.0)], ang, ox, oy + 0.03, sv)[0]
        c.ellipse(v[0], v[1], w * 0.45, 0.030, (0.96, 0.98, 0.92), lift=0.1)
        c.ellipse(v[0], v[1], w * 0.22, 0.018, (0.55, 0.85, 0.35), lift=0.2)
        c.ellipse(v[0] - 0.01, v[1] + 0.004, w * 0.12, 0.008, WHITE, lift=0, alpha=0.8)
    for k in range(10):
        a, b = _rot([(0.05 + k * 0.14, 0.066), (0.05 + k * 0.14, 0.075)], ang, ox, oy + 0.03, sv)
        c.line(a[0], a[1], b[0], b[1], 0.004, scale(P.accent, 0.35), 0.8)
    a, b = _rot([(0.0, 0.07), (1.4, 0.07)], ang, ox, oy + 0.03, sv)
    c.line(a[0], a[1], b[0], b[1], 0.01, mix(P.accent, WHITE, 0.55), 0.8)
    for e in (0.0, 1.4):
        p = _rot([(e, 0.0)], ang, ox, oy + 0.03, sv)[0]
        c.ellipse(p[0], p[1], 0.015, 0.045, (0.12, 0.12, 0.13), lift=0.2)


@sprop("hp_tape_measure", aspect=2.1, fill=0.45)
def hp_tape_measure(c, P):
    case = mix(P.accent, (1.0, 0.85, 0.1), 0.4)
    # extended tape curling to the right
    c.poly([(0.10, 0.08), (0.78, 0.06), (0.80, 0.115), (0.12, 0.135)], (0.97, 0.90, 0.35), lift=0.2)
    for k in range(18):
        x = 0.16 + k * 0.035
        c.line(x, 0.10 + 0.002 * k - 0.0, x, 0.12 + (0.012 if k % 5 == 0 else 0.0), 0.003, (0.15, 0.12, 0.08), 0.8)
    c.line(0.80, 0.06, 0.80, 0.115, 0.012, (0.6, 0.6, 0.62))
    craft.cylinder(c, -0.15, 0.04, 0.27, 0.22, scale(case, 1.05), scale(case, 0.62), scale(case, 1.08), tilt=0.5)
    c.ellipse(-0.15, 0.31, 0.19, 0.095, scale(case, 0.80), lift=0.0)
    c.ellipse(-0.15, 0.315, 0.09, 0.045, (0.14, 0.14, 0.15), lift=0.3)
    c.rect(-0.10, 0.12, 0.06, 0.07, (0.12, 0.12, 0.13), lift=0.2, r=0.01)
    gloss(c, -0.30, 0.26, 0.05, 0.02, 10, 0.7)
    gloss(c, -0.38, 0.14, 0.012, 0.07, 0, 0.45)
    c.line(-0.38, 0.17, -0.38, 0.07, 0.012, (0.1, 0.1, 0.1), 0.4)


@niche("construction", "Construction", subjects=("hp_hard_hat",),
       strong=("construction", "contractor", "civil engineer", "civil contractor", "builders", "building contractor", "cement", "crane",
               "nirman", "thekedar", "निर्माण", "ठेकेदार", "सिविल", "इमारत", "construction company"),
       weak=("builder", "site", "concrete", "scaffolding", "infrastructure", "bricks", "labour"),
       accent="#f39c12", mood="light", group="home", avoid=("interior", "real estate"))
def construction(S):
    P = S.pal
    u0, u1 = _span(S)
    sk_top, sk_bot = _sky(P, (0.62, 0.78, 0.92), (0.96, 0.93, 0.84))
    steel = mix(scale(P.ink, 2.0), sk_bot, 0.35)
    conc = mix((0.70, 0.70, 0.68), P.wall_bot, 0.22)
    with S.far():
        S.rect((u0 + u1) / 2, -1.0, u1 - u0, 1.6, sk_top, lift=0.0)                                                  # sky above the gradient (wide crops show more of it)
        S.gradient_rect(u0, -0.2, u1, 0.64, sk_top, sk_bot)
        S.glow(1.9, 0.30, 0.9, P.light, 0.30)
        # concrete frame of a building going up: columns and slabs, with rebar sticking out of the top
        for fl in range(4):
            S.rect(1.30, 0.58 - fl * 0.12, 1.4, 0.022, scale(conc, 0.9), lift=0.0)
        for k in range(6):
            S.rect(0.70 + k * 0.28, 0.40, 0.035, 0.45, scale(conc, 0.82), lift=0.0)
            S.line(0.70 + k * 0.28, 0.17, 0.70 + k * 0.28, 0.08, 0.004, (0.45, 0.30, 0.25))
        S.rect(1.55, 0.42, 0.7, 0.32, scale(conc, 1.05), lift=0.0, alpha=0.65)
        _crane(S, 0.52, 0.64, 0.62, steel, 0.95)
        _crane(S, 1.98, 0.64, 0.52, scale(steel, 1.1), 0.7)
        S.rect(1.0, 0.64, 6.0, 0.03, scale(conc, 0.7), lift=0.0)
        S.floor(0.64, P.floor_top, P.floor_bot)
    # plywood hoarding wall behind the table
    ply = mix((0.80, 0.66, 0.46), P.wall_bot, 0.12)
    S.rect(0.9, 0.60, 1.9, 0.20, scale(ply, 1.0), lift=0.0)
    for k in range(16):
        S.rect(-0.1 + k * 0.125, 0.60, 0.004, 0.2, scale(ply, 0.7), lift=0.0, alpha=0.7)
    S.rect(0.9, 0.505, 1.9, 0.012, P.accent_dark, lift=0.0)
    for k in range(14):                                                                     # hazard stripes on the top rail
        S.poly([(-0.1 + k * 0.14, 0.52), (-0.0 + k * 0.14, 0.52), (0.04 + k * 0.14, 0.50), (-0.06 + k * 0.14, 0.50)], P.accent, soft=0.5)
    # concrete slab table
    S.gradient_rect(u0, 0.70, u1, 1.8, scale(conc, 1.06), scale(conc, 0.80))
    for k in range(4):
        S.line(0.45 + k * 0.50, 0.70, -0.4 + k * 1.1, 1.8, 0.004, scale(conc, 0.6), 0.5)
    S.rect(1.0, 0.70, 6.0, 0.015, scale(conc, 0.55), lift=0.0)
    for _ in range(26):
        S.rect(S.rng.uniform(0.2, 2.0), S.rng.uniform(0.72, 1.4), S.rng.uniform(0.006, 0.02), S.rng.uniform(0.003, 0.008),
               scale(conc, S.rng.choice((0.7, 1.2))), lift=0.0, alpha=0.4)
    S.soft(1.1, 0.88, 0.8, 0.16, P.light, 0.22, 1.4, add=True)
    S.line(0.30, 0.185, 1.10, 0.185, 0.016, (0.55, 0.57, 0.60))
    S.line(0.30, 0.178, 1.10, 0.178, 0.005, (0.85, 0.87, 0.9), 0.8)
    S.put("hp_hi_vis_vest", 0.70, 0.68, 0.42, color=P, subject=True, shadow=False)
    S.put("hp_blueprint", 1.30, 0.86, 0.16, color=P, shadow=False)
    S.put("hp_hard_hat", 1.02, 0.91, 0.36, color=P, subject=True, shadow_w=0.5)
    S.put("hp_level", 0.96, 1.03, 0.07, color=P, framed=False, shadow=False)
    S.put("hp_hammer", 1.28, 1.00, 0.17, color=P, shadow=False)
    S.put("hp_tape_measure", 0.58, 0.93, 0.15, color=P, shadow_w=0.3)
    S.focus("detail", 0.98, 0.78)
    with S.near():
        S.soft(1.66, 1.07, 0.09, 0.09, mix(P.accent, WHITE, 0.4), 0.40, 0.6, add=True)


# ====================================================================================================== plumbing
COPPER = (0.82, 0.47, 0.28)
CHROME = (0.80, 0.83, 0.87)


@sprop("hp_tap_basin", aspect=1.25, fill=1.0)
def hp_tap_basin(c, P):
    rng = c.rng
    wh = (0.96, 0.96, 0.95)
    # white ceramic basin
    c.poly([(-0.58, 0.20), (0.58, 0.20), (0.50, 0.04), (-0.50, 0.04)], scale(wh, 0.80), lift=0.0)
    hshade_box(c, 0.0, 0.12, 1.14, 0.16, wh, (0.72, 0.73, 0.74), r=0.05)
    c.ellipse(0.0, 0.05, 0.50, 0.05, scale(wh, 0.62), lift=0)
    disc(c, 0.0, 0.20, 0.58, wh, 0.30, 0.04, rim=True)
    c.ellipse(0.0, 0.205, 0.50, 0.50 * 0.27, (0.80, 0.82, 0.83), lift=0)
    soft_disc(c, 0.05, 0.19, 0.42, 0.10, (0.35, 0.40, 0.45), 0.35, 1.1)
    c.ellipse(0.04, 0.19, 0.40, 0.40 * 0.24, (0.62, 0.84, 0.95), lift=0.1, alpha=0.8)           # water
    for k in range(3):
        arc(c, 0.28, 0.19, 0.06 + k * 0.05, (0.06 + k * 0.05) * 0.3, 0, 360, 0.004, WHITE, 0.55 - k * 0.15, steps=10)
    c.ellipse(-0.35, 0.215, 0.012, 0.007, (0.4, 0.42, 0.44), lift=0)
    # tap body, base, lever, curved spout
    c.ellipse(0.0, 0.215, 0.09, 0.03, scale(CHROME, 0.6), lift=0)
    hshade_box(c, 0.0, 0.30, 0.10, 0.20, CHROME, scale(CHROME, 0.55), r=0.012)
    hshade_box(c, 0.0, 0.62, 0.075, 0.55, (0.93, 0.95, 0.97), scale(CHROME, 0.5), r=0.02)
    c.ellipse(0.0, 0.90, 0.037, 0.016, (0.95, 0.96, 0.98), lift=0)
    pts = [(0.0, 0.66), (0.0, 0.84), (0.10, 0.93), (0.26, 0.93), (0.36, 0.86), (0.40, 0.74)]
    for p0, p1 in zip(pts, pts[1:]):
        _pipe(c, p0[0], p0[1], p1[0], p1[1], 0.06, CHROME, 0.8)
    c.rect(0.40, 0.725, 0.07, 0.04, scale(CHROME, 0.5), lift=0.1, r=0.01)
    _pipe(c, -0.05, 0.44, -0.20, 0.52, 0.045, CHROME, 0.8)                                       # lever
    c.circle(-0.215, 0.525, 0.028, (0.95, 0.96, 0.98), lift=0.15)
    gloss(c, -0.012, 0.70, 0.012, 0.18, 0, 0.8)
    # falling water: translucent stream with a bright core, splash and drops
    c.poly([(0.375, 0.705), (0.435, 0.705), (0.425, 0.215), (0.385, 0.215)], (0.72, 0.88, 0.98), lift=0.1, alpha=0.62)
    c.line(0.395, 0.70, 0.392, 0.24, 0.012, WHITE, 0.8)
    soft_disc(c, 0.41, 0.215, 0.13, 0.04, WHITE, 0.5, 1.3, add=True)
    for k, (du, dv, r) in enumerate(((0.02, 0.36, 0.022), (-0.03, 0.50, 0.017), (0.04, 0.60, 0.014))):
        craft.drip(c, 0.41 + du + 0.08 * (k - 1), dv - 0.12, r, (0.62, 0.84, 0.98))
    for _ in range(10):                                                                           # splash droplets
        a = rng.uniform(0.2, 2.9)
        c.circle(0.41 + math.cos(a) * rng.uniform(0.04, 0.12), 0.23 + math.sin(a) * rng.uniform(0.03, 0.10), rng.uniform(0.005, 0.01),
                 (0.88, 0.96, 1.0), lift=0, alpha=0.9)
    gloss(c, -0.38, 0.24, 0.10, 0.012, 0, 0.6)


@sprop("hp_copper_pipes", aspect=2.6, fill=0.70)
def hp_copper_pipes(c, P):
    rng = c.rng
    # standing PVC pipes (open ends facing us)
    for i, (u, h) in enumerate(((-0.78, 0.60), (-0.60, 0.44), (-0.46, 0.52))):
        hshade_box(c, u, h / 2, 0.15, h, (0.96, 0.97, 0.98), (0.66, 0.68, 0.72))
        c.ellipse(u, 0.0, 0.075, 0.03, (0.62, 0.64, 0.68), lift=0)
        hshade_box(c, u, h / 2 + 0.001, 0.15, h, (0.96, 0.97, 0.98), (0.66, 0.68, 0.72))
        c.ellipse(u, h, 0.075, 0.032, (0.97, 0.98, 1.0), lift=0)
        c.ellipse(u, h, 0.056, 0.022, (0.25, 0.28, 0.32), lift=0)
        c.rect(u, h * 0.22, 0.15, 0.045, P.accent, lift=0.2, alpha=0.9)
        gloss(c, u - 0.035, h * 0.55, 0.012, h * 0.35, 0, 0.5)
    # copper pipe run: horizontal, elbow, vertical stub with couplings and a ball valve
    runs = [((-0.25, 0.14), (0.62, 0.14)), ((0.62, 0.14), (0.62, 0.62))]
    for (a, b) in runs:
        _pipe(c, a[0], a[1], b[0], b[1], 0.11, COPPER, 0.8)
    c.circle(0.62, 0.14, 0.075, scale(COPPER, 0.9), lift=0.3)                                     # elbow
    gloss(c, 0.60, 0.16, 0.03, 0.02, 20, 0.7)
    for (u, v, hz) in ((-0.10, 0.14, 1), (0.30, 0.14, 1), (0.62, 0.40, 0)):
        if hz:
            c.rect(u, v, 0.045, 0.14, scale(COPPER, 0.78), r=0.012, lift=0.25)
            c.line(u - 0.01, v + 0.05, u - 0.01, v - 0.05, 0.007, mix(COPPER, WHITE, 0.6), 0.7)
        else:
            c.rect(u, v, 0.14, 0.045, scale(COPPER, 0.78), r=0.012, lift=0.25)
    # tee outlet and brass ball valve with red lever
    c.rect(0.30, 0.14, 0.12, 0.14, scale(COPPER, 0.95), lift=0.3, r=0.02)
    hshade_box(c, 0.30, 0.30, 0.09, 0.22, scale(COPPER, 1.05), scale(COPPER, 0.6), r=0.01)
    c.ellipse(0.30, 0.47, 0.115, 0.115 * 0.55, BRASS, lift=0.3)
    c.ellipse(0.30, 0.47, 0.06, 0.035, scale(BRASS, 0.55), lift=0)
    c.rect(0.30, 0.52, 0.015, 0.09, STEEL, lift=0.2)
    c.rect(0.20, 0.57, 0.28, 0.035, (0.82, 0.14, 0.12), lift=0.3, r=0.015)
    gloss(c, 0.15, 0.58, 0.07, 0.008, 0, 0.7)
    for k in range(10):                                                                            # patina / flux specks
        c.circle(rng.uniform(-0.2, 0.55), 0.14 + rng.uniform(-0.04, 0.04), rng.uniform(0.003, 0.007), scale(COPPER, 0.6), lift=0, alpha=0.5)
    for k in range(3):
        c.ellipse(0.88 + k * 0.05, 0.28 - k * 0.04, 0.02, 0.026, (0.62, 0.84, 0.98), lift=0.1, alpha=0.7)


@sprop("hp_wrench", aspect=4.6, fill=0.34)
def hp_wrench(c, P):
    sv, ang, ox, oy = 0.50, 12, -0.62, 0.16
    grip = P.accent
    hd = _rot([(0.0, -0.05), (1.02, -0.07), (1.02, 0.07), (0.0, 0.05)], ang, ox, oy, sv)
    c.poly([(x + 0.02, y - 0.05) for x, y in hd], BLACK, alpha=0.26)
    c.poly(hd, CHROME, lift=0.35)
    gp = _rot([(0.0, -0.05), (0.40, -0.058), (0.40, 0.058), (0.0, 0.05)], ang, ox, oy, sv)
    c.poly(gp, grip, lift=0.3)
    a, b = _rot([(0.0, 0.035), (0.40, 0.045)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.012, mix(grip, WHITE, 0.45), 0.7)
    a, b = _rot([(0.42, 0.055), (1.0, 0.063)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.010, WHITE, 0.7)
    head = _rot([(1.0, -0.14), (1.18, -0.17), (1.36, -0.13), (1.40, -0.04), (1.22, -0.035), (1.22, 0.04), (1.40, 0.045),
                 (1.36, 0.14), (1.18, 0.18), (1.0, 0.14)], ang, ox, oy, sv)
    c.poly([(x + 0.02, y - 0.05) for x, y in head], BLACK, alpha=0.26)
    c.poly(head, scale(CHROME, 0.92), lift=0.4)
    jaw = _rot([(1.22, 0.04), (1.40, 0.045), (1.38, 0.10), (1.22, 0.10)], ang, ox, oy, sv)
    c.poly(jaw, scale(CHROME, 0.7), lift=0.2)
    w = _rot([(1.10, 0.0)], ang, ox, oy, sv)[0]
    c.ellipse(w[0], w[1], 0.055, 0.045, scale(CHROME, 0.7), lift=0.3)
    c.ellipse(w[0] - 0.005, w[1] + 0.008, 0.04, 0.03, mix(CHROME, WHITE, 0.4), lift=0.1)
    for k in range(7):
        wa = _rot([(1.07 + k * 0.01, -0.03 + k * 0.01)], ang, ox, oy, sv)[0]
        c.circle(wa[0], wa[1], 0.004, scale(CHROME, 0.5), lift=0)
    soft_disc(c, w[0] - 0.05, w[1] + 0.03, 0.12, 0.05, WHITE, 0.5, 1.2, add=True)


@sprop("hp_toolbox", aspect=1.35, fill=0.95)
def hp_toolbox(c, P):
    rng = c.rng
    body = mix(P.accent, (0.2, 0.3, 0.6), 0.1)
    # open lid standing at the back
    c.poly([(-0.52, 0.52), (0.52, 0.52), (0.50, 0.95), (-0.50, 0.95)], scale(body, 0.7), lift=0.15)
    c.rect(0.0, 0.74, 0.90, 0.30, scale(body, 0.8), r=0.03, lift=0.1)
    # tray with tools
    c.rect(0.0, 0.52, 1.04, 0.05, (0.12, 0.12, 0.13), lift=0, alpha=0.5)
    for k, (u, h_, col) in enumerate(((-0.36, 0.55, (0.95, 0.80, 0.12)), (-0.24, 0.50, (0.9, 0.2, 0.15)), (-0.10, 0.60, (0.95, 0.80, 0.12)),
                                      (0.06, 0.52, (0.2, 0.2, 0.22)))):
        c.rect(u, 0.36 + h_ * 0.30, 0.075, h_ * 0.52, col, r=0.03, lift=0.25)
        c.line(u, 0.36 + h_ * 0.56, u, 0.36 + h_ * 0.86, 0.016, (0.78, 0.8, 0.84))
    for sg, col in ((-1, (0.85, 0.15, 0.12)), (1, (0.85, 0.15, 0.12))):                           # pliers
        c.line(0.30 + sg * 0.03, 0.40, 0.33 + sg * 0.085, 0.69, 0.045, col)
        c.line(0.30 + sg * 0.012, 0.65, 0.295 + sg * 0.005, 0.80, 0.03, STEEL)
    c.circle(0.30, 0.64, 0.025, (0.5, 0.52, 0.55), lift=0.3)
    # front box
    c.poly([(-0.55, 0.40), (0.55, 0.40), (0.61, 0.46), (-0.49, 0.46)], mix(body, WHITE, 0.2), lift=0.1)
    c.rect(0.0, 0.215, 1.10, 0.38, body, r=0.04, lift=0.20)
    c.rect(0.0, 0.40, 1.12, 0.03, scale(body, 0.7), lift=0.1, r=0.01)
    soft_disc(c, -0.30, 0.30, 0.45, 0.10, WHITE, 0.25, 1.2, add=True)
    soft_disc(c, 0.52, 0.2, 0.18, 0.2, BLACK, 0.22, 1.3)
    for u in (-0.34, 0.34):                                                                         # latches
        c.rect(u, 0.38, 0.09, 0.09, STEEL, r=0.012, lift=0.3)
        c.rect(u, 0.36, 0.045, 0.03, scale(STEEL, 0.5), lift=0)
    c.rect(0.0, 0.25, 0.24, 0.07, (0.15, 0.15, 0.16), r=0.02, lift=0.2)                           # grip recess
    c.line(-0.50, 0.12, 0.50, 0.12, 0.012, scale(body, 0.7), 0.5)
    for _ in range(18):
        u, v = rng.uniform(-0.5, 0.5), rng.uniform(0.04, 0.38)
        c.circle(u, v, rng.uniform(0.004, 0.008), mix(body, WHITE, 0.4), lift=0, alpha=0.35)
    _pipe(c, -0.28, 0.99, 0.28, 0.99, 0.045, STEEL, 0.75)                                            # carry handle
    c.line(-0.28, 0.96, -0.28, 0.93, 0.03, scale(STEEL, 0.6))
    c.line(0.28, 0.96, 0.28, 0.93, 0.03, scale(STEEL, 0.6))


@niche("plumbing", "Plumbing", subjects=("hp_tap_basin",),
       strong=("plumber", "plumbing", "plumbing services", "pipe fitting", "leak repair", "water tap", "pipe leakage", "bathroom fitting",
               "nal", "plamber", "नल", "प्लंबर", "पाइप", "लीकेज"),
       weak=("pipe", "tap", "leak", "drain", "water", "sanitary", "geyser"),
       accent="#2980b9", mood="light", group="home", avoid=("electrician",))
def plumbing(S):
    P = S.pal
    u0, u1 = _span(S)
    tile = mix(P.paper, P.wall_top, 0.5)
    stone = mix((0.30, 0.34, 0.38), P.wall_bot, 0.12)
    if P.mood == "dark":
        stone = scale(stone, 0.6)
    with S.far():
        S.wall(tile, scale(tile, 0.90), 0.58)
        # subway tiles: staggered grout lines
        grout = scale(tile, 0.80)
        for r in range(9):
            y = r * 0.07
            S.rect(1.0, y, 6.0, 0.004, grout, lift=0.0, alpha=0.8)
            off = 0.0 if r % 2 == 0 else 0.07
            u = u0 - (u0 % 0.14) + off
            while u < u1:
                S.rect(u, y + 0.035, 0.004, 0.07, grout, lift=0.0, alpha=0.7)
                u += 0.14
        # accent mosaic band
        S.rect(1.0, 0.33, 6.0, 0.085, scale(P.accent, 1.0), lift=0.0)
        for k in range(int((u1 - u0) / 0.05) + 1):
            for j in range(2):
                S.rect(u0 + k * 0.05, 0.31 + j * 0.04, 0.046, 0.036, (P.accent, P.accent_light, P.accent2, P.accent_dark)[(k * 3 + j * 5 + (k // 3)) % 4],
                       lift=0.0)
        # a copper pipe run along the wall with brackets, a pipe valve and a window light
        S.glow(0.30, 0.20, 0.8, P.light, 0.26)
        S.rect(1.0, 0.145, 6.0, 0.025, COPPER, lift=0.25)
        for k in range(8):
            S.rect(-0.2 + k * 0.45, 0.145, 0.03, 0.05, scale(STEEL, 0.8), lift=0.0)
        S.circle(1.72, 0.145, 0.05, (0.8, 0.15, 0.12), lift=0.2)
        S.rect(1.72, 0.145, 0.10, 0.012, scale((0.8, 0.15, 0.12), 0.7), lift=0.0)
        S.rect(1.0, 0.585, 6.0, 0.025, scale(stone, 1.25), lift=0.0)
        S.floor(0.60, stone, scale(stone, 0.78))
    S.gradient_rect(u0, 0.60, u1, 1.8, scale(stone, 1.08), scale(stone, 0.72))
    S.rect(1.0, 0.60, 6.0, 0.012, scale(stone, 1.35), lift=0.0)
    for _ in range(60):
        S.rect(S.rng.uniform(0.2, 2.0), S.rng.uniform(0.62, 1.4), S.rng.uniform(0.004, 0.012), S.rng.uniform(0.002, 0.005),
               scale(stone, S.rng.choice((0.7, 1.3))), lift=0.0, alpha=0.45)
    S.soft(1.1, 0.80, 0.7, 0.12, P.light, 0.30, 1.4, add=True)
    S.rect(1.06, 0.97, 0.9, 0.0, WHITE, lift=0.0)
    S.put("hp_toolbox", 0.72, 0.84, 0.26, color=P)
    S.put("hp_copper_pipes", 1.44, 0.85, 0.24, color=P)
    S.put("hp_tap_basin", 1.06, 0.93, 0.50, color=P, subject=True, shadow_w=1.1)
    S.put("hp_wrench", 1.22, 1.02, 0.16, color=P, shadow=False)
    S.focus("detail", 1.20, 0.72)
    with S.near():
        S.soft(1.66, 1.07, 0.09, 0.09, mix(P.accent, WHITE, 0.5), 0.40, 0.6, add=True)


# ====================================================================================================== electrician
def _bulb(c, u, v, s, lit, rng):
    """One bulb standing on its screw cap at (u, v); s = overall height."""
    glass_r = s * 0.30
    gv = v + s * 0.64
    # brass screw cap with thread ridges
    base = scale(BRASS, 0.9)
    hshade_box(c, u, v + s * 0.10, s * 0.26, s * 0.20, mix(base, WHITE, 0.25), scale(base, 0.5), r=s * 0.02)
    for k in range(4):
        c.line(u - s * 0.12, v + s * (0.03 + k * 0.045), u + s * 0.12, v + s * (0.045 + k * 0.045), s * 0.012, scale(base, 0.5), 0.8)
    c.rect(u, v + s * 0.015, s * 0.10, s * 0.03, (0.18, 0.18, 0.2), lift=0.1)
    c.rect(u, v + s * 0.215, s * 0.27, s * 0.035, (0.82, 0.84, 0.86), lift=0.2, r=s * 0.01)
    # glass: neck + globe
    glass = (0.95, 0.97, 1.0)
    c.poly([(u - s * 0.12, v + s * 0.23), (u + s * 0.12, v + s * 0.23), (u + s * 0.22, v + s * 0.40), (u - s * 0.22, v + s * 0.40)], glass,
           lift=0.0, alpha=0.5 if not lit else 0.75)
    c.ellipse(u, gv, glass_r, glass_r * 1.04, (1.0, 0.93, 0.74) if lit else (0.82, 0.88, 0.94), lift=0.0, alpha=0.78 if lit else 0.42)
    if lit:
        soft_disc(c, u, gv, glass_r * 1.05, glass_r * 1.05, (1.0, 0.90, 0.55), 0.85, 0.8, add=True)
        soft_disc(c, u, gv, glass_r * 0.55, glass_r * 0.55, (1.0, 1.0, 0.9), 0.9, 1.0, add=True)
    # filament
    fc = (1.0, 0.98, 0.85) if lit else (0.55, 0.50, 0.42)
    c.line(u - s * 0.025, v + s * 0.25, u - s * 0.07, gv - s * 0.03, s * 0.008, scale(fc, 0.8))
    c.line(u + s * 0.025, v + s * 0.25, u + s * 0.07, gv - s * 0.03, s * 0.008, scale(fc, 0.8))
    pts = [(u - s * 0.07, gv - s * 0.03)]
    for k in range(7):
        pts.append((u - s * 0.07 + s * 0.02 * (k + 1), gv - s * 0.03 + (s * 0.07 if k % 2 == 0 else s * 0.0)))
    pts.append((u + s * 0.07, gv - s * 0.03))
    for p, q in zip(pts, pts[1:]):
        c.line(p[0], p[1], q[0], q[1], s * 0.012, fc, 1.0)
    # reflections on the glass
    c.line(u - glass_r * 0.62, gv + glass_r * 0.45, u - glass_r * 0.35, gv + glass_r * 0.78, s * 0.018, WHITE, 0.8 if lit else 0.6)
    c.ellipse(u - glass_r * 0.5, gv + glass_r * 0.2, s * 0.015, glass_r * 0.35, WHITE, lift=0, alpha=0.55)
    if not lit:
        arc(c, u, gv, glass_r * 0.95, glass_r * 0.98, 200, 340, s * 0.012, (0.6, 0.66, 0.72), 0.5, steps=8)


@sprop("hp_bulbs", aspect=1.95, fill=1.0)
def hp_bulbs(c, P):
    rng = c.rng
    glow = mix((1.0, 0.82, 0.45), P.accent_light, 0.25)
    c.glow(0.15, 0.55, 1.1, glow, 0.38)
    _bulb(c, -0.62, 0.0, 0.72, False, rng)
    _bulb(c, 0.62, 0.0, 0.78, False, rng)
    _bulb(c, 0.0, 0.0, 1.0, True, rng)
    c.glow(0.0, 0.62, 0.55, (1.0, 0.88, 0.55), 0.5, )


@sprop("hp_switchboard", aspect=1.05, fill=1.0)
def hp_switchboard(c, P):
    rng = c.rng
    ply = (0.45, 0.30, 0.19)
    # plywood backing board standing up, with a front lip
    c.rect(0.0, 0.50, 1.0, 1.0, ply, lift=0.14, r=0.015)
    c.rect(0.0, 0.50, 0.97, 0.97, scale(ply, 1.12), lift=0.1, r=0.01)
    for k in range(5):
        c.line(-0.46, 0.12 + k * 0.2, 0.46, 0.14 + k * 0.2, 0.004, scale(ply, 0.7), 0.4)
    soft_disc(c, -0.25, 0.78, 0.5, 0.28, (1.0, 0.8, 0.45), 0.25, 1.3, add=True)
    # white modular plate: 2 x 2 rocker switches with LEDs
    plate = (0.95, 0.95, 0.93)
    c.rect(0.02, 0.69, 0.60, 0.40, scale(plate, 0.6), r=0.03, lift=0.0, alpha=0.5)
    c.rect(0.0, 0.70, 0.60, 0.40, plate, r=0.03, lift=0.12)
    for i in range(2):
        for j in range(2):
            u, v = -0.14 + i * 0.28, 0.78 - j * 0.17
            c.rect(u, v, 0.20, 0.13, scale(plate, 0.80), r=0.02, lift=0.0)
            on = (i + j) % 2 == 0
            c.rect(u, v + (0.016 if on else -0.016), 0.16, 0.085, (0.99, 0.99, 0.98) if on else scale(plate, 0.9), r=0.014, lift=0.25)
            c.rect(u, v + (0.05 if on else -0.05), 0.15, 0.012, scale(plate, 0.65), lift=0)
            c.circle(u + 0.075, v + 0.052, 0.009, (0.3, 1.0, 0.45) if on else (0.5, 0.15, 0.12), lift=0)
            if on:
                c.glow(u + 0.075, v + 0.052, 0.05, (0.3, 1.0, 0.5), 0.4)
    for (u, v) in ((-0.27, 0.90), (0.27, 0.90), (-0.27, 0.51), (0.27, 0.51)):
        c.circle(u, v, 0.012, (0.62, 0.62, 0.62), lift=0.3)
        c.line(u - 0.008, v, u + 0.008, v, 0.004, (0.3, 0.3, 0.3))
    # 3-pin socket
    c.rect(-0.10, 0.37, 0.28, 0.20, plate, r=0.02, lift=0.1)
    c.circle(-0.10, 0.37, 0.07, scale(plate, 0.9), lift=0.2)
    c.rect(-0.10, 0.395, 0.012, 0.03, (0.1, 0.1, 0.1), lift=0)
    c.rect(-0.14, 0.34, 0.03, 0.012, (0.1, 0.1, 0.1), lift=0)
    c.rect(-0.06, 0.34, 0.03, 0.012, (0.1, 0.1, 0.1), lift=0)
    # miniature circuit breakers with orange toggles
    for k in range(4):
        u = 0.20 + k * 0.095 - 0.04
        c.rect(u, 0.36, 0.085, 0.23, (0.88, 0.89, 0.9), lift=0.12, r=0.008)
        c.rect(u, 0.40, 0.04, 0.06, (0.15, 0.15, 0.16), lift=0.2, r=0.006)
        c.rect(u, 0.42 if k % 3 else 0.385, 0.03, 0.03, (0.98, 0.55, 0.10), lift=0.2)
        c.rect(u, 0.28, 0.06, 0.02, scale(plate, 0.65), lift=0)
    c.rect(0.0, 0.22, 0.60, 0.018, STEEL, lift=0.3)                                                # din rail
    # exposed wires with clips
    for k, col in enumerate(((0.85, 0.14, 0.12), (0.12, 0.12, 0.14), (0.15, 0.35, 0.80), (0.95, 0.80, 0.15))):
        x = -0.36 + k * 0.045
        pts = [(x, 1.02), (x + 0.01, 0.86), (x - 0.02, 0.72), (x + 0.012, 0.58), (x - 0.01, 0.46), (x + 0.02 + k * 0.03, 0.15), (x + 0.20 + k * 0.1, 0.05)]
        for a, b in zip(pts, pts[1:]):
            c.line(a[0], a[1], b[0], b[1], 0.022, col)
            c.line(a[0] - 0.006, a[1], b[0] - 0.006, b[1], 0.006, mix(col, WHITE, 0.45), 0.7)
        for cv in (0.66, 0.40):
            c.rect(x, cv, 0.04, 0.02, (0.7, 0.72, 0.74), lift=0.2)
    for k in range(18):
        c.circle(rng.uniform(-0.45, 0.45), rng.uniform(0.04, 0.96), rng.uniform(0.004, 0.009), scale(ply, 0.6), lift=0, alpha=0.4)


@sprop("hp_wire_coil", aspect=4.2, fill=0.45)
def hp_wire_coil(c, P):
    rng = c.rng
    for (ox, oy, col, n) in ((0.34, 0.06, (0.10, 0.10, 0.12), 4), (-0.25, 0.0, (0.82, 0.14, 0.12), 6)):
        a, b = 0.46, 0.46 * 0.40
        c.ellipse(ox + 0.03, oy - 0.02, a + 0.04, b + 0.03, BLACK, lift=0, alpha=0.25)
        for k in range(n):
            vv = oy + 0.05 + k * 0.045
            arc(c, ox, vv, a, b, 180, 360, 0.075, scale(col, 0.62), steps=12)                      # back-lower half darker
            arc(c, ox, vv, a, b, 0, 180, 0.075, col, steps=12)
            arc(c, ox - 0.02, vv + 0.016, a - 0.01, b - 0.01, 90, 200, 0.017, mix(col, WHITE, 0.45), 0.85, steps=8)
        for t in range(14):                                                                          # insulation ridges
            ang = math.radians(rng.uniform(190, 350))
            vv = oy + 0.05 + (n - 1) * 0.045
            c.circle(ox + math.cos(ang) * a, vv + math.sin(ang) * b - 0.02, 0.012, scale(col, 0.6), lift=0, alpha=0.3)
    # bare copper ends
    c.line(-0.25 + 0.46, 0.20, 0.82, 0.12, 0.05, (0.82, 0.14, 0.12))
    c.line(0.80, 0.115, 0.96, 0.10, 0.026, COPPER)
    for k in range(5):
        c.line(0.94, 0.10, 1.00 + k * 0.01, 0.12 + (k - 2) * 0.02, 0.006, mix(COPPER, WHITE, 0.3), 0.9)
    c.line(0.78, 0.13, 0.80, 0.115, 0.006, WHITE, 0.4)


@sprop("hp_tester", aspect=7.5, fill=0.2)
def hp_tester(c, P):
    sv, ang, ox, oy = 0.5, -8, -0.70, 0.08
    sh = _rot([(0.0, -0.02), (0.62, -0.02), (0.62, 0.02), (0.0, 0.02)], ang, ox + 0.78, oy, sv)
    c.poly([(x + 0.015, y - 0.03) for x, y in sh], BLACK, alpha=0.25)
    c.poly(sh, STEEL, lift=0.35)
    hd = _rot([(0.0, -0.065), (0.80, -0.075), (0.80, 0.075), (0.0, 0.065)], ang, ox, oy, sv)
    c.poly([(x + 0.015, y - 0.03) for x, y in hd], BLACK, alpha=0.25)
    c.poly(hd, (0.96, 0.78, 0.10), lift=0.3)
    win = _rot([(0.50, -0.025), (0.68, -0.025), (0.68, 0.025), (0.50, 0.025)], ang, ox, oy, sv)
    c.poly(win, (1.0, 0.45, 0.20), lift=0.1)
    w = _rot([(0.59, 0.0)], ang, ox, oy, sv)[0]
    c.glow(w[0], w[1], 0.14, (1.0, 0.5, 0.2), 0.55)
    a, b = _rot([(0.02, 0.05), (0.78, 0.055)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.012, (1.0, 0.95, 0.65), 0.8)
    cl = _rot([(0.30, 0.05), (0.62, 0.05), (0.62, 0.10), (0.30, 0.10)], ang, ox, oy, sv)
    c.poly(cl, scale(STEEL, 0.8), lift=0.3)
    cap = _rot([(0.0, -0.065), (-0.02, -0.04), (-0.02, 0.04), (0.0, 0.065)], ang, ox, oy, sv)
    c.poly(cap, (0.12, 0.12, 0.14), lift=0.2)


@sprop("hp_pliers", aspect=3.4, fill=0.38)
def hp_pliers(c, P):
    sv, ang, ox, oy = 0.52, 18, -0.50, 0.12
    red, steel = (0.82, 0.14, 0.12), scale(STEEL, 0.95)
    hand1 = _rot([(0.0, -0.02), (0.6, -0.002), (0.62, 0.05), (0.0, 0.06)], ang, ox, oy, sv)
    hand2 = _rot([(0.0, -0.07), (0.6, -0.052), (0.62, 0.0), (0.0, 0.02)], ang, ox, oy, sv)
    for h in (hand1, hand2):
        c.poly([(x + 0.015, y - 0.04) for x, y in h], BLACK, alpha=0.25)
    c.poly(hand2, scale(red, 0.82), lift=0.3)
    c.poly(hand1, red, lift=0.3)
    a, b = _rot([(0.03, 0.045), (0.58, 0.040)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.01, mix(red, WHITE, 0.5), 0.8)
    jaw1 = _rot([(0.6, 0.0), (0.82, 0.01), (1.06, 0.002), (1.04, 0.045), (0.82, 0.075), (0.6, 0.06)], ang, ox, oy, sv)
    jaw2 = _rot([(0.6, -0.065), (0.82, -0.05), (1.06, -0.038), (1.04, 0.0), (0.82, 0.005), (0.6, -0.005)], ang, ox, oy, sv)
    c.poly(jaw2, scale(steel, 0.75), lift=0.35)
    c.poly(jaw1, steel, lift=0.4)
    p = _rot([(0.78, 0.0)], ang, ox, oy, sv)[0]
    c.circle(p[0], p[1], 0.032, mix(steel, WHITE, 0.2), lift=0.3)
    c.circle(p[0], p[1], 0.012, scale(steel, 0.5), lift=0)
    a, b = _rot([(0.82, 0.07), (1.03, 0.04)], ang, ox, oy, sv)
    c.line(a[0], a[1], b[0], b[1], 0.01, WHITE, 0.6)


@niche("electrician", "Electrician", subjects=("hp_switchboard",),
       strong=("electrician", "electrical", "electrical services", "wiring", "switchboard", "electrical contractor", "bijli", "bijli mistri",
               "इलेक्ट्रीशियन", "बिजली", "वायरिंग", "electrical repair"),
       weak=("wire", "voltage", "bulb", "switch", "power", "lighting", "inverter"),
       accent="#f1c40f", mood="dark", group="home", avoid=("solar",))
def electrician(S):
    P = S.pal
    u0, u1 = _span(S)
    wall_a = P.wall_top if P.mood == "dark" else mix(P.wall_top, P.ink, 0.55)
    wall_b = P.wall_bot if P.mood == "dark" else mix(P.wall_bot, P.ink, 0.65)
    glow_c = mix((1.0, 0.82, 0.40), P.accent_light, 0.35)
    with S.far():
        S.wall(wall_a, wall_b, 0.60)
        # pegboard dots and brick-like panels
        for r in range(7):
            for k in range(int((u1 - u0) / 0.09) + 1):
                S.rect(u0 + k * 0.09, 0.05 + r * 0.075, 0.012, 0.012, scale(wall_b, 0.55), lift=0.0)
        # neon lightning bolt sign with big glow
        bx, by, bs = 0.52, 0.28, 0.24
        bolt = [(0.15, -0.5), (-0.35, 0.08), (-0.02, 0.08), (-0.18, 0.5), (0.35, -0.12), (0.03, -0.12), (0.22, -0.5)]
        S.glow(bx, by, 0.7, P.accent, 0.35)
        S.poly([(bx + x * bs, by - y * bs) for x, y in bolt], mix(P.accent_light, WHITE, 0.3))
        S.glow(bx, by, 0.28, WHITE, 0.25)
        # hanging bare bulbs
        for (u, vt, vl) in ((1.20, -0.1, 0.20), (1.72, -0.1, 0.30), (0.90, -0.1, 0.12)):
            S.line(u, vt, u, vl, 0.004, scale(P.ink, 1.5))
            S.circle(u, vl + 0.02, 0.022, mix(glow_c, WHITE, 0.6), lift=0)
            S.glow(u, vl + 0.02, 0.45, glow_c, 0.55)
        S.line(0.5, 0.02, 2.0, 0.06, 0.008, scale(P.ink, 1.8))                                      # ceiling cable run
        S.rect(1.0, 0.605, 6.0, 0.03, scale(wall_b, 0.6), lift=0.0)
        S.floor(0.62, scale(P.floor_top, 0.8), scale(P.floor_bot, 0.8))
    bench = scale(P.surface, 0.75) if P.mood != "dark" else P.surface
    S.wood(u0, 0.62, u1, 1.7, bench, plank=0.13, grain=0.5)
    S.soft(1.1, 0.78, 0.9, 0.16, glow_c, 0.34, 1.4, add=True)
    S.soft(1.22, 0.92, 0.5, 0.10, glow_c, 0.25, 1.4, add=True)
    S.put("hp_switchboard", 0.80, 0.88, 0.46, color=P, subject=True, shadow_w=0.42)
    S.put("hp_bulbs", 1.34, 0.92, 0.27, color=P, shadow_w=0.5)
    S.put("hp_wire_coil", 0.98, 1.02, 0.11, color=P, shadow_w=0.3)
    S.put("hp_pliers", 1.36, 1.06, 0.10, color=P, shadow=False)
    S.put("hp_tester", 1.12, 1.10, 0.10, color=P, shadow=False)
    S.focus("detail", 0.95, 0.74)
    with S.near():
        S.soft(0.46, 1.10, 0.10, 0.10, glow_c, 0.45, 0.6, add=True)
        S.soft(1.68, 1.04, 0.12, 0.12, glow_c, 0.35, 0.6, add=True)


# ====================================================================================================== cleaning
def _bubble(S, u, v, r, alpha=0.30):
    """A floating soap bubble: translucent disc, bright rim and a spot of light (stage level)."""
    S.circle(u, v, r, (0.85, 0.95, 1.0), alpha=alpha * 0.5, lift=0, soft=2.0)
    S.circle(u + r * 0.2, v + r * 0.2, r * 0.8, (1.0, 0.85, 0.95), alpha=alpha * 0.25, lift=0, soft=2.0)
    S.glow(u - r * 0.35, v - r * 0.40, r * 0.45, WHITE, 0.55)


def _sparkle_s(S, u, v, r, alpha=0.9):
    S.glow(u, v, r * 1.3, WHITE, 0.45)
    S.line(u - r, v, u + r, v, r * 0.09, WHITE, alpha)
    S.line(u, v - r, u, v + r, r * 0.09, WHITE, alpha)
    S.line(u - r * 0.4, v - r * 0.4, u + r * 0.4, v + r * 0.4, r * 0.05, WHITE, alpha * 0.6)
    S.line(u - r * 0.4, v + r * 0.4, u + r * 0.4, v - r * 0.4, r * 0.05, WHITE, alpha * 0.6)


@sprop("hp_bucket_mop", aspect=0.98, fill=1.0)
def hp_bucket_mop(c, P):
    rng = c.rng
    bk = P.accent
    # aluminium mop pole leaning out of the bucket, with a grip
    c.line(0.04, 0.34, 0.40, 1.28, 0.040, (0.40, 0.42, 0.45))
    c.line(0.025, 0.34, 0.385, 1.28, 0.026, (0.78, 0.80, 0.83))
    c.line(0.017, 0.36, 0.375, 1.27, 0.008, WHITE, 0.8)
    c.line(0.36, 1.18, 0.425, 1.34, 0.062, scale(bk, 0.85))
    c.line(0.358, 1.19, 0.405, 1.31, 0.026, mix(bk, WHITE, 0.45), 0.8)
    # bucket body
    c.poly([(-0.36, 0.40), (0.36, 0.40), (0.27, 0.0), (-0.27, 0.0)], bk, lift=0.22)
    soft_disc(c, 0.26, 0.20, 0.14, 0.26, BLACK, 0.32, 1.3)
    soft_disc(c, -0.22, 0.22, 0.10, 0.22, WHITE, 0.30, 1.2, add=True)
    c.ellipse(0.0, 0.0, 0.27, 0.27 * 0.3, scale(bk, 0.6), lift=0)
    c.poly([(-0.36, 0.40), (0.36, 0.40), (0.352, 0.365), (-0.352, 0.365)], mix(bk, WHITE, 0.15), lift=0.1)
    for k in range(3):                                                                         # moulded ribs and a measuring scale
        y = 0.12 + k * 0.095
        c.line(-0.30 + k * 0.016, y, 0.30 - k * 0.016, y, 0.007, scale(bk, 0.72), 0.5)
    for k in range(4):
        c.line(-0.04, 0.12 + k * 0.06, 0.04 + (k % 2) * 0.04, 0.12 + k * 0.06, 0.006, WHITE, 0.7)
    # rim and soapy water
    c.ellipse(0.0, 0.40, 0.37, 0.37 * 0.34, scale(bk, 0.65), lift=0)
    c.ellipse(0.0, 0.405, 0.345, 0.345 * 0.31, (0.62, 0.84, 0.95), lift=0.08)
    soft_disc(c, 0.05, 0.395, 0.30, 0.09, (0.30, 0.55, 0.75), 0.3, 1.0)
    for _ in range(34):                                                                         # foam bubbles
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.30
        rr = rng.uniform(0.012, 0.034)
        bx, by = math.cos(a) * r, 0.41 + math.sin(a) * r * 0.30
        c.circle(bx, by, rr, (0.96, 0.99, 1.0), lift=0.15, alpha=0.95)
        c.circle(bx - rr * 0.3, by + rr * 0.3, rr * 0.3, WHITE, lift=0, alpha=0.9)
    # mop strings draped over the rim
    for k in range(11):
        u = -0.22 + k * 0.044 + rng.uniform(-0.008, 0.008)
        craft.strand(c, u, 0.375, rng.uniform(0.14, 0.24), -90 + (u * 40) + rng.uniform(-8, 8), 0.026,
                     rng.choice(((0.95, 0.94, 0.90), (0.88, 0.89, 0.90), (0.80, 0.84, 0.88))), 1.0, rng.uniform(-0.12, 0.12))
    c.line(-0.30, 0.43, 0.30, 0.43, 0.012, scale(bk, 0.7), 0.35)
    # bail handle
    arc(c, 0.0, 0.40, 0.38, 0.40, 20, 160, 0.012, (0.7, 0.72, 0.75), steps=12)


@sprop("hp_spray_bottle", aspect=0.52, fill=1.0)
def hp_spray_bottle(c, P):
    rng = c.rng
    liquid = mix(P.accent_light, (0.7, 1.0, 0.9), 0.4)
    # body: clear plastic with coloured liquid
    c.poly([(-0.20, 0.52), (0.20, 0.52), (0.22, 0.04), (0.19, 0.0), (-0.19, 0.0), (-0.22, 0.04)], (0.90, 0.95, 0.98), lift=0.1, alpha=0.9)
    c.poly([(-0.17, 0.50), (0.17, 0.50), (0.20, 0.06), (0.17, 0.02), (-0.17, 0.02), (-0.20, 0.06)], scale(liquid, 0.92), lift=0.2)
    c.ellipse(0.0, 0.50, 0.17, 0.035, mix(liquid, WHITE, 0.4), lift=0.1)
    soft_disc(c, 0.14, 0.26, 0.10, 0.28, scale(liquid, 0.4), 0.55, 1.2)
    soft_disc(c, -0.13, 0.30, 0.05, 0.22, WHITE, 0.55, 1.1, add=True)
    for _ in range(14):
        c.circle(rng.uniform(-0.14, 0.14), rng.uniform(0.06, 0.48), rng.uniform(0.004, 0.009), WHITE, lift=0, alpha=0.5)
    # label
    c.rect(0.0, 0.26, 0.34, 0.20, (0.98, 0.98, 0.97), lift=0.08, r=0.02)
    c.rect(0.0, 0.335, 0.34, 0.04, P.accent, lift=0.1)
    c.ellipse(0.0, 0.235, 0.05, 0.065, P.accent_light, lift=0.2)
    c.poly([(0.0, 0.31), (0.05, 0.22), (-0.05, 0.22)], P.accent_light, lift=0.2)
    c.rect(0.0, 0.17, 0.24, 0.014, scale(P.accent_dark, 0.9), lift=0)
    # shoulder, neck, collar
    c.poly([(-0.20, 0.52), (0.20, 0.52), (0.09, 0.62), (-0.09, 0.62)], (0.90, 0.95, 0.98), lift=0.1, alpha=0.9)
    c.rect(0.0, 0.66, 0.20, 0.06, (0.96, 0.96, 0.96), lift=0.15, r=0.01)
    for k in range(5):
        c.line(-0.09 + k * 0.045, 0.635, -0.09 + k * 0.045, 0.69, 0.006, (0.7, 0.72, 0.75), 0.6)
    # sprayer head: body, trigger, nozzle
    hd = P.accent_dark
    c.rect(0.0, 0.74, 0.22, 0.12, hd, lift=0.3, r=0.03)
    c.poly([(0.08, 0.80), (0.34, 0.80), (0.38, 0.75), (0.38, 0.69), (0.28, 0.69), (0.22, 0.74), (0.08, 0.74)], mix(hd, WHITE, 0.08), lift=0.3)
    c.rect(0.36, 0.72, 0.06, 0.05, scale(hd, 0.6), lift=0.2, r=0.01)
    c.poly([(0.0, 0.70), (0.11, 0.70), (0.15, 0.55), (0.11, 0.53), (0.04, 0.62)], mix(hd, WHITE, 0.15), lift=0.3)           # trigger
    c.line(-0.08, 0.76, 0.12, 0.79, 0.012, mix(hd, WHITE, 0.55), 0.7)
    c.rect(0.0, 0.79, 0.06, 0.04, P.accent, lift=0.2, r=0.01)
    c.line(-0.05, 0.60, -0.05, 0.04, 0.01, mix(liquid, WHITE, 0.3), 0.7)                                                       # dip tube
    gloss(c, -0.12, 0.60, 0.012, 0.06, 0, 0.6)
    # a few spray droplets from the nozzle
    for k in range(5):
        c.circle(0.46 + k * 0.05, 0.72 + (k % 3 - 1) * 0.03, 0.008 - k * 0.001, (0.88, 0.96, 1.0), lift=0, alpha=0.8 - k * 0.12)


@sprop("hp_sponges", aspect=1.5, fill=0.55)
def hp_sponges(c, P):
    rng = c.rng
    for i, (u, v, w, ang, sc, hl) in enumerate(((0.0, 0.0, 0.62, 0, (0.98, 0.84, 0.18), (0.20, 0.55, 0.28)), (0.05, 0.19, 0.58, 5, (0.98, 0.78, 0.16),
                                                                                                          (0.20, 0.5, 0.26)), (-0.02, 0.36, 0.52, -6, (0.99, 0.86, 0.22), (0.18, 0.45, 0.24)))):
        top = mix(sc, WHITE, 0.2)
        c.poly([(u - w / 2 + 0.01, v + 0.03), (u + w / 2 - 0.01, v + 0.03), (u + w / 2 + 0.07, v + 0.10), (u - w / 2 + 0.09, v + 0.10)], scale(hl, 0.9), lift=0.1)
        c.rect(u, v + 0.075, w, 0.07, scale(hl, 0.95), r=0.012, lift=0.2)
        c.rect(u, v + 0.13, w, 0.11, sc, r=0.02, lift=0.2)
        c.poly([(u - w / 2, v + 0.185), (u + w / 2, v + 0.185), (u + w / 2 + 0.07, v + 0.24), (u - w / 2 + 0.07, v + 0.24)], top, lift=0.1)
        c.poly([(u + w / 2, v + 0.075), (u + w / 2 + 0.07, v + 0.12), (u + w / 2 + 0.07, v + 0.24), (u + w / 2, v + 0.185)], scale(sc, 0.78), lift=0.1)
        for _ in range(11):
            x, y = rng.uniform(u - w / 2 + 0.03, u + w / 2 - 0.03), rng.uniform(v + 0.09, v + 0.17)
            c.ellipse(x, y, rng.uniform(0.008, 0.016), rng.uniform(0.006, 0.01), scale(sc, 0.62), lift=0, alpha=0.8)
        for _ in range(7):
            x, y = rng.uniform(u - w / 2 + 0.08, u + w / 2 + 0.03), rng.uniform(v + 0.2, v + 0.23)
            c.ellipse(x, y, rng.uniform(0.008, 0.014), 0.004, scale(sc, 0.6), lift=0, alpha=0.7)
    for _ in range(30):                                                                              # suds
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.20
        rr = rng.uniform(0.014, 0.034)
        bx, by = math.cos(a) * r + 0.04, 0.60 + math.sin(a) * r * 0.5
        c.circle(bx, by, rr, (0.97, 0.99, 1.0), lift=0.15, alpha=0.96)
        c.circle(bx - rr * 0.3, by + rr * 0.3, rr * 0.28, WHITE, lift=0, alpha=0.95)


@sprop("hp_gloves", aspect=1.2, fill=1.0)
def hp_gloves(c, P):
    rng = c.rng
    for (ox, ang, tone) in ((-0.20, 8, 0.0), (0.22, -9, -0.10)):
        yel = (0.99, 0.82, 0.12) if tone == 0 else (0.94, 0.74, 0.10)
        cu = P.accent_light
        def T(pts, ox=ox, ang=ang):
            return _rot(pts, ang, ox, 0.0)
        c.poly([(x + 0.015, y - 0.015) for x, y in T([(-0.17, 0.30), (0.17, 0.30), (0.19, 0.56), (-0.19, 0.56)])], BLACK, alpha=0.22)
        c.poly(T([(-0.19, 0.0), (0.19, 0.0), (0.17, 0.25), (-0.17, 0.25)]), cu, lift=0.2)                                   # cuff
        c.poly(T([(-0.20, 0.20), (0.20, 0.20), (0.205, 0.26), (-0.205, 0.26)]), scale(cu, 0.85), lift=0.2)
        c.poly(T([(-0.18, 0.26), (0.18, 0.26), (0.19, 0.56), (-0.19, 0.56)]), yel, lift=0.25)                                 # palm
        for k, (fx, fl) in enumerate(((-0.145, 0.40), (-0.05, 0.47), (0.05, 0.45), (0.145, 0.36))):                         # fingers
            base = T([(fx, 0.52)])[0]
            tip = T([(fx * 1.06, 0.52 + fl)])[0]
            c.line(base[0], base[1], tip[0], tip[1], 0.092, scale(yel, 0.78))
            c.line(base[0] - 0.006, base[1], tip[0] - 0.006, tip[1], 0.075, yel)
            c.line(base[0] - 0.02, base[1], tip[0] - 0.02, tip[1] - 0.01, 0.018, mix(yel, WHITE, 0.55), 0.8)
            c.circle(tip[0], tip[1], 0.046, yel, lift=0.2)
        base, tip = T([(-0.17, 0.38)])[0], T([(-0.36, 0.60)])[0]
        c.line(base[0], base[1], tip[0], tip[1], 0.10, scale(yel, 0.78))
        c.line(base[0], base[1], tip[0], tip[1], 0.082, yel)
        c.circle(tip[0], tip[1], 0.046, yel, lift=0.2)
        soft_disc(c, T([(-0.08, 0.40)])[0][0], T([(-0.08, 0.40)])[0][1], 0.08, 0.14, WHITE, 0.35, 1.2, add=True)
        for k in range(5):
            a, b = T([(-0.16 + k * 0.08, 0.04), (-0.15 + k * 0.08, 0.18)])
            c.line(a[0], a[1], b[0], b[1], 0.006, scale(cu, 0.8), 0.5)


@niche("cleaning", "Cleaning services", subjects=("hp_bucket_mop",),
       strong=("cleaning", "cleaning services", "housekeeping", "maid", "janitorial", "sanitation", "house cleaning", "deep cleaning",
               "safai", "safai wala", "सफाई", "सफाई सेवा", "हाउसकीपिंग", "मेड", "क्लीनिंग"),
       weak=("mop", "sanitize", "dust", "hygiene", "laundry", "polish", "wash"),
       accent="#1abc9c", mood="light", group="home", avoid=())
def cleaning(S):
    P = S.pal
    u0, u1 = _span(S)
    tile = mix(P.paper, P.accent_light, 0.22) if P.mood != "dark" else scale(mix(P.accent_dark, P.floor_top, 0.4), 0.9)
    wall_a, wall_b = P.wall_top, P.wall_bot
    with S.far():
        S.wall(wall_a, wall_b, 0.58)
        # window with daylight, sink-side shelf and towels (blurred)
        S.glow(0.32, 0.28, 1.0, P.light, 0.35)
        S.gradient_rect(0.14, 0.06, 0.50, 0.46, (0.78, 0.90, 0.98), (0.98, 0.99, 1.0), r=0.01)
        S.rect(0.32, 0.26, 0.012, 0.40, WHITE, lift=0.0)
        S.rect(0.32, 0.20, 0.36, 0.012, WHITE, lift=0.0)
        S.rect(1.55, 0.30, 0.46, 0.05, mix(P.paper, P.wall_bot, 0.4), lift=0.0)
        for k, col in enumerate((P.accent, P.accent_light, P.paper)):
            S.rect(1.40 + k * 0.14, 0.23, 0.11, 0.10, col, r=0.01)
        S.circle(1.00, 0.20, 0.08, scale(P.accent, 1.0), alpha=0.35, lift=0)
        # floating bubbles
        for (u, v, r) in ((0.80, 0.18, 0.05), (1.10, 0.32, 0.03), (1.90, 0.20, 0.06), (0.62, 0.40, 0.03), (1.30, 0.12, 0.04)):
            _bubble(S, u, v, r)
        S.rect(1.0, 0.50, 6.0, 0.045, mix(P.accent_light, wall_b, 0.4), lift=0.0)
        S.rect(1.0, 0.585, 6.0, 0.028, mix(wall_b, WHITE, 0.4), lift=0.0)
        S.floor(0.60, tile, scale(tile, 0.85))
    S.floor(0.60, tile, scale(tile, 0.84))
    # large staggered tiles, spacing grows towards the camera (rows are cheap, no long diagonals)
    grout = scale(tile, 0.78)
    v, h = 0.60, 0.055
    row = 0
    while v < 1.75:
        S.rect(1.0, v, 6.0, 0.003 + h * 0.03, grout, lift=0.0, alpha=0.6)
        w = h * 2.6
        off = 0.0 if row % 2 == 0 else w / 2
        u = u0 - (u0 % w) + off
        while u < u1:
            S.rect(u, v + h / 2, 0.003 + h * 0.02, h, grout, lift=0.0, alpha=0.55)
            u += w
        v += h
        h *= 1.17
        row += 1
    # glossy light: a bright pool and window reflection on the floor
    S.soft(0.90, 0.80, 1.0, 0.16, WHITE, 0.55 if P.mood != "dark" else 0.22, 1.2, add=True)
    S.soft(1.05, 0.98, 0.9, 0.22, P.light, 0.30, 1.4, add=True)
    S.put("hp_bucket_mop", 0.74, 0.90, 0.56, color=P, subject=True, shadow_w=0.5)
    S.put("hp_gloves", 1.00, 0.86, 0.26, color=P)
    S.put("hp_spray_bottle", 1.27, 0.98, 0.34, color=P, shadow_w=0.22)
    S.put("hp_sponges", 1.49, 1.04, 0.13, color=P, shadow_w=0.3)
    # reflections of the props in the polished floor
    S.soft(0.74, 0.99, 0.26, 0.09, P.accent, 0.40, 1.1)
    S.soft(1.27, 1.04, 0.10, 0.05, WHITE, 0.30, 1.3, add=True)
    for (u, v, r) in ((0.52, 1.02, 0.045), (1.12, 0.78, 0.035), (1.58, 0.92, 0.05), (0.90, 1.10, 0.03), (0.60, 0.66, 0.025), (1.40, 0.66, 0.028)):
        _sparkle_s(S, u, v, r)
    S.focus("detail", 0.78, 0.74)
    with S.near():
        _bubble(S, 0.50, 1.10, 0.10, 0.45)
        _bubble(S, 1.68, 1.04, 0.07, 0.4)


# ====================================================================================================== solar energy
@sprop("hp_solar_array", aspect=1.95, fill=0.88)
def hp_solar_array(c, P):
    rng = c.rng
    frame = (0.80, 0.82, 0.85)
    hgt = 0.84

    def pt(x, y):
        return (x * (1.0 - 0.13 * y / hgt), y)
    # mounting rails and feet on the roof
    for x in (-0.55, 0.0, 0.55):
        a, b = pt(x, 0.0), pt(x, 0.08)
        c.line(a[0], a[1], b[0], b[1], 0.03, (0.30, 0.32, 0.35))
    sky = _sky(P)[1] if P.mood == "dark" else (0.55, 0.78, 1.0)
    for r in range(2):
        y0 = 0.06 + r * 0.40
        y1 = y0 + 0.38
        for i in range(3):
            x0 = -0.76 + i * 0.51
            x1 = x0 + 0.49
            quad = [pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1)]
            c.poly(quad, frame, lift=0.3)
            ins = 0.014
            iq = [pt(x0 + ins, y0 + ins), pt(x1 - ins, y0 + ins), pt(x1 - ins, y1 - ins), pt(x0 + ins, y1 - ins)]
            c.poly(iq, (0.12, 0.27, 0.52), lift=0.45)
            for k in range(1, 6):                                                                      # cell grid
                xa, xb = x0 + ins + (x1 - x0 - 2 * ins) * k / 6.0, 0
                a, b = pt(xa, y0 + ins), pt(xa, y1 - ins)
                c.line(a[0], a[1], b[0], b[1], 0.0035, (0.62, 0.78, 0.95), 0.30 if k % 2 else 0.18)
            for k in range(1, 4):
                ya = y0 + ins + (y1 - y0 - 2 * ins) * k / 4.0
                a, b = pt(x0 + ins, ya), pt(x1 - ins, ya)
                c.line(a[0], a[1], b[0], b[1], 0.0035, (0.62, 0.78, 0.95), 0.26)
            for k in (2, 4):                                                                           # silver busbars
                xa = x0 + ins + (x1 - x0 - 2 * ins) * k / 6.0
                a, b = pt(xa, y0 + ins), pt(xa, y1 - ins)
                c.line(a[0] + 0.004, a[1], b[0] + 0.004, b[1], 0.003, (0.86, 0.9, 0.95), 0.35)
            sky_ref = mix(sky, WHITE, 0.4)
            c.poly([pt(x0 + ins, y1 - ins), pt(x0 + ins + 0.24, y1 - ins), pt(x0 + ins + 0.02, y0 + ins + 0.2), pt(x0 + ins, y0 + ins + 0.2)], sky_ref, alpha=0.16)
            a, b = pt(x0, y1 - 0.005), pt(x1, y1 - 0.005)
            c.line(a[0], a[1], b[0], b[1], 0.009, WHITE, 0.45)                                           # lit upper edge
    # sun streak across the glass and a hot spot
    c.poly([pt(-0.5, 0.06), pt(-0.15, 0.06), pt(0.30, 0.84), pt(-0.05, 0.84)], WHITE, alpha=0.10)
    soft_disc(c, -0.45, 0.70, 0.40, 0.26, (1.0, 0.97, 0.85), 0.40, 1.3, add=True)
    soft_disc(c, -0.62, 0.78, 0.12, 0.08, WHITE, 0.55, 1.2, add=True)


@sprop("hp_inverter", aspect=0.78, fill=1.0)
def hp_inverter(c, P):
    rng = c.rng
    body = (0.93, 0.94, 0.95)
    # wall bracket legs
    c.rect(-0.28, 0.04, 0.05, 0.10, (0.30, 0.32, 0.35), lift=0.1)
    c.rect(0.28, 0.04, 0.05, 0.10, (0.30, 0.32, 0.35), lift=0.1)
    _prism(c, 0.0, 0.09, 0.78, 0.86, 0.10, 0.04, body, top=mix(body, WHITE, 0.4), side=scale(body, 0.66), lift=0.06, r=0.04)
    for k in range(9):                                                                                   # heat-sink fins on the side
        a = 0.39 + 0.012
        c.line(a, 0.15 + k * 0.085, a + 0.09, 0.185 + k * 0.085, 0.012, scale(body, 0.5), 0.8)
    soft_disc(c, -0.20, 0.70, 0.30, 0.30, WHITE, 0.45, 1.2, add=True)
    # accent brand band and display
    c.rect(0.0, 0.88, 0.74, 0.07, P.accent, lift=0.2, r=0.01)
    c.circle(-0.28, 0.88, 0.022, WHITE, lift=0, alpha=0.9)
    c.rect(0.06, 0.88, 0.30, 0.012, WHITE, lift=0, alpha=0.8)
    c.rect(0.0, 0.66, 0.50, 0.22, (0.06, 0.09, 0.12), lift=0.1, r=0.02)
    c.rect(0.0, 0.66, 0.46, 0.18, (0.10, 0.28, 0.20), lift=0.15, r=0.012)
    c.glow(0.0, 0.66, 0.35, (0.4, 1.0, 0.6), 0.3)
    c.text("3.2 kW", 0.0, 0.69, 0.07, (0.7, 1.0, 0.8), 0.20)
    for k in range(7):
        c.rect(-0.18 + k * 0.06, 0.62 - (k % 3) * 0.004, 0.035, 0.02 + 0.01 * ((k * 2) % 4), (0.5, 1.0, 0.65), lift=0, alpha=0.9)
    for k, col in enumerate(((0.3, 1.0, 0.4), (1.0, 0.8, 0.2), (0.4, 0.8, 1.0))):
        c.circle(-0.24 + k * 0.1, 0.50, 0.016, col, lift=0)
        c.glow(-0.24 + k * 0.1, 0.50, 0.06, col, 0.5)
    # DC isolator switch (red on yellow) and cable glands with black cables
    c.rect(0.20, 0.40, 0.20, 0.20, (0.98, 0.80, 0.10), lift=0.2, r=0.02)
    c.circle(0.20, 0.40, 0.065, (0.82, 0.12, 0.10), lift=0.3)
    c.rect(0.20, 0.40, 0.11, 0.025, scale((0.82, 0.12, 0.10), 0.6), lift=0)
    c.rect(-0.18, 0.36, 0.30, 0.12, scale(body, 0.88), lift=0.1, r=0.015)
    c.text("SOLAR", -0.18, 0.37, 0.06, scale(P.accent_dark, 0.9), 0.20)
    for k, u in enumerate((-0.24, -0.08, 0.08, 0.24)):
        c.rect(u, 0.10, 0.07, 0.07, (0.14, 0.14, 0.16), lift=0.2, r=0.01)
        c.line(u, 0.06, u + (k - 1.5) * 0.04, -0.05, 0.035, (0.08, 0.08, 0.09))
    for _ in range(14):
        c.circle(rng.uniform(-0.35, 0.35), rng.uniform(0.15, 0.82), rng.uniform(0.004, 0.008), scale(body, 0.8), lift=0, alpha=0.3)


@niche("solar-energy", "Solar energy", subjects=("hp_solar_array",),
       strong=("solar", "solar panel", "solar panels", "solar energy", "renewable energy", "green energy", "photovoltaic", "rooftop solar",
               "solar installation", "सोलर", "सौर ऊर्जा", "सोलर पैनल", "solar system", "saur urja"),
       weak=("renewable", "sun", "inverter", "net metering", "clean energy", "sustainable"),
       accent="#f5b041", mood="light", group="home", avoid=("electrician",))
def solar_energy(S):
    P = S.pal
    u0, u1 = _span(S)
    dk = 0.55 if P.mood == "dark" else 1.0
    sk_top, sk_bot = _sky(P, (0.30, 0.58, 0.92), (0.80, 0.92, 1.0))
    sun = (1.0, 0.86, 0.5) if P.mood == "dark" else (1.0, 0.96, 0.82)
    tile = scale(mix((0.62, 0.30, 0.20), P.wall_bot, 0.06), dk)
    with S.far():
        S.gradient_rect(u0, -0.3, u1, 0.60, sk_top, sk_bot)
        # sun with flare discs along a line across the picture
        S.glow(0.45, 0.16, 1.1, sun, 0.70, 1.6)
        S.glow(0.45, 0.16, 0.30, WHITE, 0.9, 1.2)
        for k, (t, r, a) in enumerate(((0.35, 0.05, 0.25), (0.6, 0.09, 0.14), (0.85, 0.04, 0.2), (1.15, 0.12, 0.10))):
            S.circle(0.45 + t * 0.9, 0.16 + t * 0.4, r, mix(sun, P.accent_light, 0.5), alpha=a, lift=0, soft=3.0)
        for (u, v, w) in ((0.9, 0.12, 0.22), (1.5, 0.22, 0.30), (1.8, 0.08, 0.18), (0.2, 0.30, 0.26)):             # soft clouds
            for j in range(4):
                S.ellipse(u + (j - 1.5) * w * 0.35, v + (0.01 if j % 2 else -0.01), w * 0.35, w * 0.16, mix(sk_bot, WHITE, 0.85), alpha=0.7, lift=0.1)
        # distant hills, trees, a small house and a wind turbine
        S.ellipse(0.4, 0.62, 0.9, 0.10, mix((0.45, 0.62, 0.42), sk_bot, 0.4 + (0.3 if P.mood == "dark" else 0)) if P.mood != "dark" else (0.12, 0.15, 0.20), lift=0)
        S.ellipse(1.7, 0.63, 1.1, 0.09, (0.40, 0.58, 0.38) if P.mood != "dark" else (0.10, 0.13, 0.17), lift=0)
        for x in (0.8, 0.95, 1.30, 1.45, 2.0):
            S.ellipse(x, 0.545, 0.035, 0.045, (0.25, 0.45, 0.28) if P.mood != "dark" else (0.07, 0.10, 0.13), lift=0.1)
        S.rect(1.12, 0.52, 0.09, 0.05, scale((0.95, 0.92, 0.85), dk), lift=0.0)
        S.poly([(1.06, 0.495), (1.18, 0.495), (1.12, 0.45)], scale((0.55, 0.28, 0.20), dk))
        S.rect(1.13, 0.468, 0.04, 0.014, (0.1, 0.2, 0.4), lift=0.0)
        S.line(1.75, 0.56, 1.75, 0.30, 0.006, scale((0.9, 0.92, 0.94), dk))
        for ang in (80, 200, 320):
            a = math.radians(ang)
            S.line(1.75, 0.30, 1.75 + math.cos(a) * 0.14, 0.30 - math.sin(a) * 0.14, 0.006, scale((0.9, 0.92, 0.94), dk))
        S.rect(1.0, 0.60, 6.0, 0.02, scale(tile, 0.6), lift=0.0)
        S.floor(0.60, tile, scale(tile, 0.8))
    # terracotta roof: gradient, staggered tile courses, ridge cap, a bright sun pool
    S.floor(0.60, tile, scale(tile, 0.78))
    v, h, row = 0.60, 0.045, 0
    while v < 1.8:
        S.rect(1.0, v + h * 0.5, 6.0, h, scale(tile, (1.12, 1.0, 1.06)[row % 3] - 0.02 * row * 0.3), lift=0.0)
        S.rect(1.0, v + h * 0.80, 6.0, h * 0.40, scale(tile, 0.78), lift=0.0)
        S.rect(1.0, v, 6.0, 0.004 + h * 0.06, scale(tile, 0.5), lift=0.0)
        w = h * 2.2
        off = 0.0 if row % 2 == 0 else w / 2
        u = u0 - (u0 % w) + off
        while u < u1:
            S.rect(u, v + h / 2, 0.004 + h * 0.03, h, scale(tile, 0.62), lift=0.0, alpha=0.7)
            u += w
        S.rect(1.0, v + 0.006, 6.0, 0.003 + h * 0.04, mix(tile, WHITE, 0.2), lift=0.0)
        v += h
        h *= 1.12
        row += 1
    S.rect(1.0, 0.615, 6.0, 0.03, scale(tile, 1.15), lift=0.0)
    S.soft(0.90, 0.78, 0.9, 0.16, sun, 0.28, 1.4, add=True)
    # cables from the array to the inverter
    S.line(1.18, 0.96, 1.40, 1.01, 0.014, (0.08, 0.08, 0.09))
    S.line(1.22, 0.97, 1.44, 1.01, 0.012, (0.55, 0.12, 0.10))
    S.put("hp_solar_array", 0.96, 0.95, 0.46, color=P, subject=True, shadow_w=1.1)
    S.put("hp_inverter", 1.56, 0.95, 0.34, color=P, shadow_w=0.3)
    S.focus("detail", 0.98, 0.74)
    with S.near():
        S.soft(0.50, 1.10, 0.12, 0.12, sun, 0.4, 0.6, add=True)
        S.soft(1.70, 0.36, 0.14, 0.14, sun, 0.3, 0.6, add=True)


# ====================================================================================================== agriculture / farm
HAY = (0.88, 0.72, 0.30)
WHEAT = (0.90, 0.72, 0.28)


@sprop("hp_tractor", aspect=1.42, fill=0.96)
def hp_tractor(c, P):
    rng = c.rng
    body = P.accent
    dark = scale(body, 0.55)
    tyre = (0.10, 0.10, 0.11)
    # big rear wheel with lugs, hub in accent colour
    def wheel(u, v, r, hub):
        c.circle(u + 0.012, v - 0.012, r, BLACK, alpha=0.20, lift=0)
        c.circle(u, v, r, tyre, lift=0.18)
        for k in range(24):                                                                      # tread lugs
            a = math.radians(k * 15 + 4)
            x0, y0 = u + math.cos(a) * r * 0.80, v + math.sin(a) * r * 0.80
            x1, y1 = u + math.cos(a) * r * 1.0, v + math.sin(a) * r * 1.0
            c.line(x0, y0, x1, y1, r * 0.11, (0.24, 0.24, 0.26), 0.9)
        c.circle(u, v, r * 0.70, (0.15, 0.15, 0.17), lift=0.15)
        c.circle(u, v, r * 0.52, scale(hub, 0.9), lift=0.3)
        for k in range(6):
            a = math.radians(k * 60 + 15)
            c.line(u, v, u + math.cos(a) * r * 0.5, v + math.sin(a) * r * 0.5, r * 0.07, scale(hub, 0.6), 0.7)
        c.circle(u, v, r * 0.16, STEEL, lift=0.3)
        soft_disc(c, u - r * 0.35, v + r * 0.45, r * 0.4, r * 0.18, WHITE, 0.14, 1.3, add=True)
    # chassis / rear fender / hood / cab
    c.rect(0.05, 0.40, 1.05, 0.14, scale(body, 0.7), r=0.04, lift=0.15)                       # chassis between wheels
    wheel(-0.52, 0.34, 0.36, body)
    # engine hood
    c.poly([(0.20, 0.38), (0.88, 0.38), (0.90, 0.60), (0.80, 0.70), (0.24, 0.70)], body, lift=0.28)
    c.poly([(0.20, 0.70), (0.80, 0.70), (0.84, 0.66), (0.24, 0.66)], mix(body, WHITE, 0.30), lift=0.1)
    soft_disc(c, 0.45, 0.62, 0.30, 0.09, WHITE, 0.28, 1.2, add=True)
    soft_disc(c, 0.80, 0.50, 0.14, 0.16, BLACK, 0.25, 1.3)
    for k in range(6):                                                                       # grille slats
        c.line(0.84, 0.43 + k * 0.035, 0.89, 0.43 + k * 0.035, 0.012, dark, 0.9)
    c.rect(0.88, 0.50, 0.04, 0.22, (0.15, 0.15, 0.17), lift=0.2, r=0.01)
    c.circle(0.86, 0.60, 0.032, (1.0, 0.95, 0.7), lift=0.1)
    c.glow(0.86, 0.60, 0.12, (1.0, 0.9, 0.55), 0.35)
    c.rect(0.50, 0.66, 0.16, 0.012, scale(body, 0.5), lift=0)
    # exhaust stack and air intake
    c.rect(0.58, 0.88, 0.032, 0.40, (0.20, 0.20, 0.22), lift=0.2)
    c.ellipse(0.58, 1.07, 0.028, 0.014, (0.10, 0.10, 0.11), lift=0)
    c.rect(0.28, 0.84, 0.04, 0.26, (0.20, 0.20, 0.22), lift=0.2)
    # cab: glass with frame, roof
    c.rect(-0.08, 0.60, 0.70, 0.64, scale(body, 0.8), lift=0.2, r=0.03, alpha=0.0)
    c.poly([(-0.34, 0.50), (0.18, 0.50), (0.14, 0.96), (-0.30, 0.96)], (0.62, 0.80, 0.88), lift=0.22, alpha=0.88)
    c.poly([(-0.34, 0.50), (0.18, 0.50), (0.15, 0.72), (-0.33, 0.62)], mix((0.62, 0.80, 0.88), WHITE, 0.35), alpha=0.35)
    for (x0, x1) in ((-0.34, -0.30), (0.14, 0.18)):
        c.poly([(x0, 0.50), (x1, 0.50), (x1 - 0.02, 0.96), (x0 - 0.0, 0.96)], dark, lift=0.2)
    c.rect(-0.08, 0.98, 0.58, 0.05, body, lift=0.3, r=0.02)
    c.rect(-0.08, 0.99, 0.58, 0.012, mix(body, WHITE, 0.5), lift=0, alpha=0.8)
    c.rect(-0.08, 0.50, 0.50, 0.03, dark, lift=0.1)
    c.poly([(-0.22, 0.56), (-0.04, 0.56), (-0.06, 0.76), (-0.20, 0.76)], scale(dark, 0.7), lift=0.1, alpha=0.8)            # seat inside the cab
    c.line(-0.30, 0.82, -0.12, 0.90, 0.05, WHITE, 0.14)
    # front wheel, small
    wheel(0.76, 0.19, 0.19, body)
    # mudguard over the rear wheel
    arc(c, -0.52, 0.34, 0.40, 0.40, 5, 175, 0.05, scale(body, 0.8), steps=14)
    arc(c, -0.52, 0.34, 0.40, 0.40, 60, 150, 0.012, mix(body, WHITE, 0.6), 0.8, steps=8)
    # mud speckle
    for _ in range(14):
        c.circle(rng.uniform(-0.8, 0.9), rng.uniform(0.04, 0.3), rng.uniform(0.004, 0.01), (0.30, 0.20, 0.12), lift=0, alpha=0.5)
    c.rect(0.62, 0.52, 0.12, 0.03, WHITE, lift=0, alpha=0.8)


@sprop("hp_hay_bale", aspect=1.05, fill=0.85)
def hp_hay_bale(c, P):
    rng = c.rng
    # round bale seen from its flat face with a spiral of straw
    c.circle(0.012, 0.50, 0.46, BLACK, alpha=0.2, lift=0)
    c.circle(0.0, 0.50, 0.46, scale(HAY, 0.62), lift=0.1)
    c.circle(0.0, 0.50, 0.42, HAY, lift=0.2)
    for k in range(9):
        r = 0.04 + k * 0.045
        arc(c, 0.0, 0.50, r, r, 20 + k * 40, 300 + k * 40, 0.010, scale(HAY, 0.74 if k % 2 else 1.14), 0.9, steps=10)
    for _ in range(40):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(0.0, 0.40)
        x, y = math.cos(a) * rr, 0.5 + math.sin(a) * rr
        c.line(x, y, x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.03, 0.03), 0.005, mix(HAY, rng.choice((WHITE, BLACK)), 0.25), 0.5)
    c.circle(0.0, 0.50, 0.46, (0.9, 0.9, 0.9), alpha=0.0, lift=0)
    soft_disc(c, 0.20, 0.30, 0.30, 0.30, BLACK, 0.28, 1.2)
    soft_disc(c, -0.18, 0.72, 0.26, 0.20, (1.0, 0.92, 0.6), 0.30, 1.2, add=True)
    for k in range(3):                                                                           # twine
        arc(c, 0.0, 0.50, 0.44, 0.44, 30 + k * 110, 70 + k * 110, 0.006, (0.2, 0.3, 0.2), 0.6, steps=4)
    for _ in range(12):
        a = rng.uniform(0, 6.28)
        c.line(math.cos(a) * 0.44, 0.5 + math.sin(a) * 0.44, math.cos(a) * 0.52, 0.5 + math.sin(a) * 0.52, 0.006, HAY, 0.9)


@sprop("hp_wheat_bundle", aspect=0.8, fill=1.0)
def hp_wheat_bundle(c, P):
    rng = c.rng
    for i in range(22):
        a = 90 + (i - 11) * 3.2 + rng.uniform(-2, 2)
        ln = rng.uniform(0.80, 1.0)
        x1, y1 = math.cos(math.radians(a)) * ln * 0.5, math.sin(math.radians(a)) * ln
        c.line(0.0, 0.0, x1 * 0.9, y1 * 0.9, 0.012, (0.74, 0.60, 0.26), 0.9)
        for k in range(9):                                                                     # grain ear
            t = 0.74 + k * 0.03
            ex, ey = math.cos(math.radians(a)) * ln * 0.5 * t / ln * 1.0 * ln + 0.0, math.sin(math.radians(a)) * ln * t
            ex = x1 * t
            for sg in (-1, 1):
                c.ellipse(ex + sg * 0.013, ey, 0.016, 0.03, WHEAT if k % 2 else scale(WHEAT, 1.1), angle=sg * -25 + a - 90, lift=0.2)
        c.line(x1, y1 * 0.98, x1 * 1.05, y1 * 1.10, 0.004, (0.9, 0.78, 0.4), 0.8)
    c.rect(0.0, 0.18, 0.28, 0.035, (0.45, 0.32, 0.16), lift=0.2, r=0.01)               # twine tie


@sprop("hp_barn", aspect=1.3, fill=1.0)
def hp_barn(c, P):
    red = (0.62, 0.17, 0.13)
    c.rect(0.0, 0.30, 1.1, 0.60, red, lift=0.12)
    for k in range(14):
        c.line(-0.52 + k * 0.08, 0.02, -0.52 + k * 0.08, 0.58, 0.004, scale(red, 0.7), 0.6)
    c.poly([(-0.58, 0.58), (0.58, 0.58), (0.35, 0.92), (-0.35, 0.92)], scale(red, 0.9), lift=0.15)
    c.poly([(-0.62, 0.58), (-0.36, 0.94), (-0.32, 0.92), (-0.58, 0.58)], (0.9, 0.9, 0.9), lift=0.1)
    c.poly([(0.62, 0.58), (0.36, 0.94), (0.32, 0.92), (0.58, 0.58)], (0.9, 0.9, 0.9), lift=0.1)
    c.rect(0.0, 0.26, 0.40, 0.46, scale(red, 0.7), lift=0.1)
    c.line(-0.20, 0.03, 0.20, 0.49, 0.025, (0.92, 0.92, 0.9))
    c.line(0.20, 0.03, -0.20, 0.49, 0.025, (0.92, 0.92, 0.9))
    c.rect(0.0, 0.26, 0.42, 0.48, (0.92, 0.92, 0.9), alpha=0.0, lift=0)
    c.rect(0.0, 0.74, 0.14, 0.10, (0.95, 0.9, 0.75), lift=0.1)


@niche("agriculture-farm", "Agriculture and farm", subjects=("hp_tractor",),
       strong=("farm", "farming", "agriculture", "tractor", "crops", "kisan", "organic farm", "organic farming", "खेती", "किसान",
               "कृषि", "ट्रैक्टर", "फसल", "kheti", "krishi"),
       weak=("organic", "harvest", "wheat", "dairy", "seeds", "fertilizer", "irrigation"),
       accent="#5d9c3a", mood="warm", group="home", avoid=())
def agriculture_farm(S):
    P = S.pal
    u0, u1 = _span(S)
    dk = 0.5 if P.mood == "dark" else 1.0
    if P.mood == "dark":
        sk_top, sk_bot = (0.10, 0.14, 0.30), (0.95, 0.55, 0.30)
    else:
        sk_top, sk_bot = (0.52, 0.72, 0.92), (1.0, 0.86, 0.62)
    sun = (1.0, 0.80, 0.45)
    field = mix((0.52, 0.66, 0.26), P.accent, 0.3)
    field_f = scale(mix((0.80, 0.64, 0.24), P.accent, 0.08), dk)
    with S.far():
        S.gradient_rect(u0, -0.3, u1, 0.66, sk_top, sk_bot)
        S.rect(1.0, 0.70, 6.0, 0.12, scale(field_f, 0.9), lift=0.0)
        S.glow(1.75, 0.46, 1.3, sun, 0.80, 1.5)
        S.glow(1.75, 0.50, 0.30, (1.0, 0.95, 0.8), 0.8, 1.2)
        for (u, v, w) in ((0.7, 0.16, 0.30), (1.3, 0.28, 0.24), (0.2, 0.30, 0.2)):
            for j in range(4):
                S.ellipse(u + (j - 1.5) * w * 0.35, v, w * 0.35, w * 0.12, mix(sk_bot, (1.0, 0.8, 0.7), 0.5), alpha=0.55, lift=0.1)
        # rolling hills, a tree line, a barn and a silo in the distance
        S.ellipse(0.5, 0.66, 1.2, 0.14, scale(mix(field, sk_bot, 0.35), dk), lift=0)
        S.ellipse(1.9, 0.66, 1.3, 0.12, scale(mix(field, sk_bot, 0.45), dk), lift=0)
        for k in range(18):
            S.ellipse(-0.1 + k * 0.14, 0.58, 0.05, 0.05 + 0.01 * (k % 3), scale((0.22, 0.38, 0.2), dk), lift=0.1)
        S.rect(0.62, 0.55, 0.14, 0.08, scale((0.62, 0.22, 0.18), dk), lift=0.0)
        S.poly([(0.54, 0.51), (0.70, 0.51), (0.66, 0.46), (0.58, 0.46)], scale((0.5, 0.2, 0.16), dk))
        S.rect(0.74, 0.52, 0.04, 0.12, scale((0.80, 0.82, 0.84), dk), lift=0.0)
        S.rect(1.0, 0.64, 6.0, 0.03, scale(field_f, 0.7), lift=0.0)
    # field: gradient, converging crop rows (cheap steep lines drawn only below the horizon), wheat tufts
    S.floor(0.62, scale(field, 0.95 * dk), scale(field_f, 0.80))
    S.gradient_rect(u0, 0.62, u1, 1.8, scale(mix(field_f, field, 0.35), dk if dk < 1 else 1.0), scale(field_f, 0.78))
    # soft furrow bands (perspective: they grow towards the camera) and wheat tufts along converging rays
    v, h, row = 0.62, 0.030, 0
    while v < 1.8:
        S.rect(1.0, v + h / 2, 6.0, h, scale(field_f, 0.90 if row % 2 else 1.02), lift=0.0, alpha=1.0)
        v += h
        h *= 1.20
        row += 1
    rng = S.rng
    wcols = [scale(c_, dk) for c_ in ((0.86, 0.66, 0.24), (0.94, 0.78, 0.32), (0.78, 0.58, 0.20))]
    for row in range(11):
        v = 0.645 + 0.36 * ((row / 11.0) ** 1.7) * 1.9
        scl = v / 0.645
        step = 0.034 * scl
        n = int((u1 - u0) / step) + 3
        for i in range(n):
            x = u0 - 0.1 + i * step + rng.uniform(-0.35, 0.35) * step
            xx = 1.05 + (x - 1.05) * 1.0
            h_ = (0.020 + rng.uniform(0, 0.008)) * scl
            col = wcols[rng.randrange(3)]
            S.line(xx, v, xx + rng.uniform(-0.01, 0.01) * scl, v - h_, 0.0026 * scl, scale(col, 0.85), 0.9)
            S.ellipse(xx, v - h_ - 0.003 * scl, 0.0034 * scl, 0.011 * scl, col, lift=0.1)
    S.soft(1.30, 0.74, 1.0, 0.18, sun, 0.35, 1.4, add=True)
    S.put("hp_hay_bale", 0.58, 0.88, 0.17, color=P, shadow_w=0.17)
    S.put("hp_hay_bale", 0.72, 0.93, 0.15, color=P, shadow_w=0.15)
    S.put("hp_tractor", 1.18, 0.93, 0.44, color=P, subject=True, shadow_w=0.62)
    S.put("hp_wheat_bundle", 0.84, 1.03, 0.22, color=P, shadow_w=0.14)
    S.focus("detail", 1.18, 0.74)
    with S.near():
        for (u, h_) in ((0.40, 0.36), (0.50, 0.44), (0.58, 0.32), (1.62, 0.34), (1.70, 0.42)):
            S.soft(u, 1.10 - h_ * 0.1, 0.03, h_ * 0.5, scale((0.86, 0.68, 0.26), dk), 0.7, 0.5)
        S.soft(1.66, 0.30, 0.14, 0.14, sun, 0.3, 0.6, add=True)
