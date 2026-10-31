"""Wellness niches: dental, doctor, pharmacy, gym, yoga, spa, salon, barber, pet clinic."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...props.core import _catmull
from ...raster import mix, scale


# ====================================================================================== shared helpers
def ao(c, u, v, w, depth=None, alpha=0.42):
    """Cheaper single-blob ambient occlusion under a prop of footprint w."""
    d = w * TILT * 0.5 if depth is None else depth
    soft_disc(c, u + w * 0.04, v - d * 0.05, w * 0.56, d * 1.05, BLACK, min(0.9, alpha * 1.25), 1.6)


def _vgrad(S, u0, u1, v0, v1, top, bottom, n=10):
    """Vertical gradient from flat strips (much cheaper than a shaded box)."""
    h = (v1 - v0) / n
    for i in range(n):
        S.rect((u0 + u1) / 2, v0 + h * (i + 0.5), u1 - u0, h + 0.002, mix(top, bottom, (i + 0.5) / n), lift=0.0)


def _hb(c, u, v, w, h, base, r=0.0, kl=1.12, kr=0.68, alpha=1.0):
    """Rounded box shaded left (lit) to right (shadow)."""
    craft.hshade_box(c, u, v, w, h, scale(base, kl), scale(base, kr), r, alpha)


def _metal(c, u, v, w, h, tone=1.0, r=0.0):
    craft.hshade_box(c, u, v, w, h, scale((0.90, 0.92, 0.95), tone), scale((0.40, 0.42, 0.47), tone), r)
    c.rect(u - w * 0.22, v, max(0.004, w * 0.12), h * 0.9, WHITE, alpha=0.55, lift=0)


def _ball(c, u, v, r, color, spec=0.6):
    """A shaded sphere: dark core, lit disc, shadow side, specular."""
    c.ellipse(u, v, r, r, scale(color, 0.62), lift=0)
    c.ellipse(u - r * 0.05, v + r * 0.06, r * 0.94, r * 0.94, color, lift=0.2)
    soft_disc(c, u + r * 0.28, v - r * 0.30, r * 0.66, r * 0.60, BLACK, 0.34, 1.3)
    gloss(c, u - r * 0.34, v + r * 0.38, r * 0.30, r * 0.17, 28, spec)


def _smooth(c, pts, color, lift=0.12, alpha=1.0, n=5):
    c.poly(_catmull(pts, n, True), color, lift=lift, alpha=alpha)


def _is_dark(P):
    return P.mood == "dark"


def _tone(P, k, tint=0.0):
    """A wall-derived neutral (clinical floors, counters): follows mood and accent."""
    return scale(mix(P.wall_bot, P.accent_light, tint), k)


def _persp_checker(S, v0, v1, c1, c2, rows=7, cols=16, uc=1.05, vh=-0.9, span=7.0, seam=None):
    """Checker floor in one-point perspective from stage v0 (far) to v1 (near)."""
    vs = [v0 + (v1 - v0) * (i / float(rows)) ** 1.55 for i in range(rows + 1)]
    S.rect(1.0, (v0 + v1) / 2, 8.0, v1 - v0 + 0.01, c2, lift=0.0)                  # dark squares are the base, only light ones are drawn
    for r in range(rows):
        for k in range(cols):
            if (r + k) % 2:
                continue
            col = c1
            pts = []
            for v, ua in ((vs[r], k), (vs[r], k + 1), (vs[r + 1], k + 1), (vs[r + 1], k)):
                f = (v - vh) / (1.0 - vh)
                pts.append((uc + (ua / cols - 0.5) * span * f, v))
            if max(p[0] for p in pts) < -1.0 or min(p[0] for p in pts) > 3.2:
                continue                                                         # never visible: skip the (slow) polygon
            S.poly(pts, col, soft=0.6)
    if seam:
        for v in vs[1:-1]:
            S.line(-3, v, 5, v, 0.0025, seam, 0.5)


def _persp_lines(S, v0, v1, color, alpha=0.35, rows=8, cols=22, uc=1.05, vh=-0.9, span=8.0):
    """Tile seams / floorboards converging to a vanishing point."""
    for i in range(1, rows):
        v = v0 + (v1 - v0) * (i / float(rows)) ** 1.55
        S.line(-3, v, 5, v, 0.0022, color, alpha)
    for k in range(cols + 1):
        ub = uc + (k / float(cols) - 0.5) * span
        f0 = (v0 - vh) / (1.0 - vh)
        S.line(uc + (ub - uc) * f0, v0, ub, v1 if v1 < 1.0 else 1.0, 0.0022, color, alpha)


def _blotches(S, n, u0, v0, u1, v1, color, alpha, rmin, rmax):
    """Mottled wall / concrete texture from big soft blobs."""
    rng = S.rng
    for _ in range(n):
        r = rng.uniform(rmin, rmax)
        S.soft(rng.uniform(u0, u1), rng.uniform(v0, v1), r * rng.uniform(1.0, 1.8), r, color, alpha * rng.uniform(0.4, 1.0), 1.2)


def _near_leaves(S, u, v, col, mirror=False, n=5):
    """Out-of-focus foreground plant leaves (depth of field in front of the subject)."""
    sg = -1 if mirror else 1
    with S.near(20.0):
        for i in range(n):
            a = math.radians(40 + i * 24)
            ln = 0.34 - 0.03 * i
            tip = (u + sg * math.cos(a) * ln, v - math.sin(a) * ln)
            mid = ((u + tip[0]) / 2, (v + tip[1]) / 2)
            px_, py_ = -math.sin(a) * sg, -math.cos(a)
            w = ln * 0.2
            S.poly([(u, v), (mid[0] + px_ * w, mid[1] + py_ * w), tip, (mid[0] - px_ * w, mid[1] - py_ * w)], scale(col, 0.8 + 0.1 * (i % 3)), 0.95)


# ====================================================================================== GYM
@sprop("wellness_dumbbell_rack", aspect=2.4, fill=0.62)
def gym_rack(c, color):
    """Two-tier steel rack, six hex dumbbells per tier, seen from the front at a slight angle (heads face us)."""
    rng = c.rng
    steel = (0.20, 0.21, 0.24)
    ao(c, 0.0, 0.0, 1.6, 0.26)
    # rear shelf bars, uprights
    for v0, vt in ((0.0, 0.0),):
        pass
    for u in (-0.72, 0.0, 0.72):
        _hb(c, u, 0.30, 0.045, 0.60, steel, kl=1.5, kr=0.7)
    # two cradle shelves
    for vs in (0.14, 0.40):
        c.poly([(-0.79, vs), (0.79, vs), (0.76, vs - 0.035), (-0.76, vs - 0.035)], scale(steel, 1.5), lift=0.15)
        c.rect(0.0, vs - 0.045, 1.56, 0.025, scale(steel, 0.8), lift=0.2)
        c.rect(0.0, vs + 0.002, 1.54, 0.006, WHITE, alpha=0.18, lift=0)
        sizes = [0.082, 0.098, 0.114, 0.130, 0.146]
        if vs > 0.3:
            sizes = [0.076, 0.090, 0.105, 0.120, 0.136]
        for i, r in enumerate(sizes):
            u = -0.60 + i * 0.30
            _dumbbell_end(c, u, vs, r, rng)
    # frame top rail + feet
    c.rect(0.0, 0.595, 1.6, 0.035, scale(steel, 1.25), r=0.012, lift=0.3)
    c.rect(0.0, 0.600, 1.5, 0.006, WHITE, alpha=0.3, lift=0)
    for u in (-0.72, 0.72):
        c.rect(u, 0.012, 0.16, 0.026, scale(steel, 0.7), r=0.01)


def _dumbbell_end(c, u, vs, r, rng):
    """Dumbbell with its axis towards the viewer: hexagonal head face in front, handle and back head offset up-right."""
    rub = (0.19, 0.19, 0.21)
    cx, cy = u, vs + r + 0.012
    ox, oy = 0.05, 0.035
    # back head (partially hidden) and handle
    hex_b = [(cx + ox + r * math.cos(math.radians(a + 30)), cy + oy + r * math.sin(math.radians(a + 30))) for a in range(0, 360, 60)]
    c.poly(hex_b, scale(rub, 0.8), lift=0.1)
    c.rect(cx + ox * 0.55, cy + oy * 0.55, r * 0.44, r * 0.38, (0.62, 0.64, 0.68), lift=0.35)
    # side wall of the head (extrusion): quad joining front and back hexagon on the upper edge
    pf = [(cx + r * math.cos(math.radians(a + 30)), cy + r * math.sin(math.radians(a + 30))) for a in range(0, 360, 60)]
    c.poly([pf[1], pf[2], (pf[2][0] + ox, pf[2][1] + oy), (pf[1][0] + ox, pf[1][1] + oy)], (0.30, 0.30, 0.33), lift=0.2)
    # front face
    c.poly(pf, rub, lift=0.28)
    c.ellipse(cx, cy, r * 0.74, r * 0.74, (0.15, 0.15, 0.17), lift=0.1, alpha=0.7)
    c.ellipse(cx, cy, r * 0.30, r * 0.30, (0.82, 0.84, 0.88), lift=0.3)
    c.ellipse(cx - r * 0.04, cy + r * 0.04, r * 0.18, r * 0.18, (0.36, 0.37, 0.41), lift=0.1)
    c.line(cx - r * 0.55, cy + r * 0.82, cx + r * 0.55, cy + r * 0.82, 0.004, WHITE, 0.4)
    c.line(pf[2][0] + 0.004, pf[2][1], pf[1][0] - 0.004, pf[1][1], 0.006, (1.0, 0.45, 0.35), 0.8)
    c.line(pf[1][0] + 0.004, pf[1][1], pf[0][0] - 0.004, pf[0][1], 0.004, (1.0, 0.6, 0.5), 0.5)
    soft_disc(c, cx - r * 0.3, cy + r * 0.5, r * 0.5, r * 0.3, WHITE, 0.16, 1.2, add=True)


@sprop("wellness_kettlebell", aspect=0.95, fill=1.0)
def gym_kettlebell(c, color):
    iron = color or (0.13, 0.13, 0.15)
    ao(c, 0.0, 0.0, 0.8, 0.13)
    # handle: thick tube (arcs of capsules) with a dark inner opening
    craft.arc(c, 0.0, 0.52, 0.21, 0.40, 0, 180, 0.105, scale(iron, 0.55), 1.0, steps=9)
    c.line(-0.21, 0.52, -0.21, 0.46, 0.105, scale(iron, 0.55))
    c.line(0.21, 0.52, 0.21, 0.46, 0.105, scale(iron, 0.55))
    craft.arc(c, 0.0, 0.53, 0.21, 0.40, 10, 170, 0.075, scale(iron, 1.5), 1.0, steps=8)
    craft.arc(c, -0.01, 0.55, 0.19, 0.38, 100, 165, 0.018, scale(iron, 3.4), 0.6, steps=5)
    # body: heavy sphere with a flat foot
    c.ellipse(0.0, 0.07, 0.30, 0.30 * TILT * 0.8, scale(iron, 0.4), lift=0)
    c.ellipse(0.0, 0.31, 0.43, 0.38, scale(iron, 0.5), lift=0)
    c.ellipse(-0.01, 0.32, 0.415, 0.365, iron, lift=0.35)
    soft_disc(c, 0.20, 0.17, 0.30, 0.26, BLACK, 0.55, 1.2)
    soft_disc(c, -0.16, 0.42, 0.20, 0.17, WHITE, 0.28, 1.3, add=True)
    gloss(c, -0.20, 0.50, 0.075, 0.045, 38, 0.8)
    # painted weight window and cast-iron speckle
    c.ellipse(0.0, 0.27, 0.15, 0.12, (0.85, 0.15, 0.12), lift=0.2, alpha=0.95)
    c.ellipse(0.0, 0.27, 0.15 * 0.78, 0.12 * 0.78, scale(iron, 0.9), lift=0.1)
    c.text("16", 0.0, 0.27, 0.07, (0.95, 0.95, 0.95), 0.18)
    rng = c.rng
    for _ in range(26):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.36
        c.ellipse(math.cos(a) * r, 0.32 + math.sin(a) * r * 0.9, rng.uniform(0.004, 0.009), rng.uniform(0.003, 0.007), WHITE, alpha=rng.uniform(0.06, 0.15), lift=0)


@sprop("wellness_plate_stack", aspect=2.5, fill=0.55)
def gym_plates(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.4, 0.26)
    rub = (0.14, 0.14, 0.16)
    v = 0.03
    for i, (r, h) in enumerate(((0.70, 0.075), (0.62, 0.07), (0.56, 0.07), (0.45, 0.06))):
        side = scale(rub, 0.8 + 0.1 * (i % 2))
        craft.hshade_box(c, 0.0, v + h / 2, 2 * r, h, scale(side, 1.7), scale(side, 0.6), r=0.012)
        c.ellipse(0.0, v, r, r * TILT, scale(side, 0.5), lift=0)
        craft.hshade_box(c, 0.0, v + h / 2, 2 * r, h, scale(side, 1.7), scale(side, 0.6), r=0.012)
        v += h
        disc(c, 0.0, v, r, scale(rub, 1.3), TILT, 0.25, rim=True)
        craft.arc(c, 0.0, v, r * 0.87, r * 0.87 * TILT, 195, 345, 0.004, (0.9, 0.9, 0.9), 0.3, steps=12)
        c.ellipse(0.0, v, r * 0.13, r * 0.13 * TILT, (0.04, 0.04, 0.05), lift=0)
        c.line(-r * 0.86, v - 0.002, -r * 0.5, v - r * 0.62 * 0.9 * TILT * 0.62, 0.006, WHITE, 0.2)
        if i == 0:
            c.text("20 KG", 0.0, v - r * 0.55 * TILT, 0.06, (0.9, 0.9, 0.92), 0.15)
    # bar sleeve on top
    _metal(c, 0.0, v + 0.06, 0.07, 0.12)
    soft_disc(c, -0.25, v - 0.02, 0.4, 0.09, WHITE, 0.16, 1.2, add=True)


@sprop("wellness_dumbbell", aspect=3.0, fill=0.5)
def gym_dumbbell(c, color):
    """A single dumbbell lying on the floor, seen from the side."""
    rng = c.rng
    rub = (0.12, 0.12, 0.13)
    ao(c, 0.0, 0.0, 1.5, 0.12, alpha=0.5)
    c.rect(0.0, 0.17, 0.78, 0.065, (0.60, 0.62, 0.66), lift=0.4)
    c.rect(0.0, 0.195, 0.76, 0.012, WHITE, alpha=0.55, lift=0)
    for i in range(18):
        x = -0.33 + i * 0.037
        c.line(x, 0.14, x + 0.012, 0.20, 0.004, (0.34, 0.35, 0.38), 0.7)
    for s in (-1, 1):
        for k, (w, h) in enumerate(((0.07, 0.22), (0.17, 0.36))):
            x = s * (0.42 + (0.07 if k else 0.0) + (0.12 if k else 0.0))
            craft.hshade_box(c, x, 0.17, w, h, scale(rub, 2.0), scale(rub, 0.6), r=0.02)
        xm = s * 0.66
        c.rect(xm - s * 0.01, 0.17, 0.14, 0.32, rub, r=0.035, lift=0.3)
        c.rect(xm, 0.315, 0.12, 0.012, WHITE, alpha=0.35, lift=0)
        c.rect(xm + s * 0.05, 0.17, 0.02, 0.28, (0.85, 0.15, 0.12), alpha=0.9, lift=0.1)
    gloss(c, -0.45, 0.30, 0.06, 0.02, 0, 0.35)


@niche("gym", "Gym / fitness studio", subjects=("wellness_dumbbell_rack", "wellness_kettlebell"),
       strong=("gym", "fitness", "dumbbell", "kettlebell", "workout", "bodybuilding", "fitness center", "gym trainer", "jim", "kasrat",
               "जिम", "कसरत", "व्यायाम", "फिटनेस"),
       weak=("exercise", "weights", "muscle", "crossfit", "trainer", "strength"),
       accent="#e74c3c", mood="dark", group="wellness")
def gym(S):
    P = S.pal
    dark = _is_dark(P)
    red = (1.0, 0.18, 0.12)
    conc = mix((0.55, 0.55, 0.57), P.wall_bot, 0.35 if not dark else 0.7)
    with S.far():
        S.wall(mix(P.wall_top, conc, 0.5), scale(mix(P.wall_bot, conc, 0.6), 0.9), 0.60)
        _blotches(S, 26, -1.0, 0.0, 3.0, 0.62, scale(conc, 0.6), 0.28, 0.12, 0.35)
        _blotches(S, 16, -1.0, 0.0, 3.0, 0.62, scale(conc, 1.5), 0.20, 0.10, 0.30)
        # a mirror wall on the right and a neon strip across the wall
        S.rect(1.95, 0.30, 0.9, 0.38, scale(conc, 0.55), r=0.01, lift=0.0)
        S.gradient_rect(1.52, 0.12, 2.38, 0.48, scale(P.accent_dark, 0.45), scale(P.wall_bot, 0.6))
        S.soft(1.9, 0.30, 0.5, 0.2, red, 0.25, 1.4, add=True)
        S.rect(0.9, 0.15, 3.2, 0.012, (1.0, 0.45, 0.35), lift=0.0)
        S.glow(0.9, 0.15, 1.6, red, 0.55 if dark else 0.28, 1.6)
        S.glow(0.3, 0.15, 0.7, red, 0.45 if dark else 0.2, 1.8)
        S.glow(1.8, 0.15, 0.7, red, 0.45 if dark else 0.2, 1.8)
        # poster frames / cage bars far away
        for u in (0.12, 0.62):                                        # steel columns with a red edge light
            S.rect(u, 0.30, 0.07, 0.62, scale(conc, 0.5), lift=0.0)
            S.rect(u + 0.035, 0.30, 0.012, 0.62, (1.0, 0.4, 0.3), alpha=0.6, lift=0.0)
        S.bokeh(8, 0.0, 0.1, 2.0, 0.55, [(1.0, 0.3, 0.2), (1.0, 0.55, 0.4)], 0.012, 0.04, 0.3)
        S.floor(0.60, scale(conc, 0.72), scale(conc, 0.34))
    S.soft(1.1, 0.80, 1.0, 0.18, red, 0.22 if dark else 0.10, 1.5, add=True)
    # rubber floor mats with seams and a sheen
    S.rect(1.0, 1.0, 6.0, 0.8, scale(conc, 0.62), lift=0.0)
    S.rect(1.0, 0.60, 6.0, 0.012, scale(conc, 0.3), lift=0.0)
    for u in (-1.6, -0.5, 0.6, 1.7, 2.8):
        S.line(u, 0.62, u * 1.8 - 0.8, 1.6, 0.003, (0.0, 0.0, 0.0), 0.5)
    S.line(-3, 0.82, 5, 0.82, 0.003, (0, 0, 0), 0.4)
    S.soft(1.1, 0.88, 1.1, 0.16, (1.0, 0.95, 0.9), 0.12, 1.3, add=True)
    S.put("wellness_plate_stack", 0.70, 0.97, 0.20, shadow_w=0.5)
    S.put("wellness_dumbbell_rack", 1.12, 0.80, 0.46, subject=True, shadow_w=0.8)
    S.put("wellness_kettlebell", 1.58, 0.95, 0.25, color=(0.15, 0.15, 0.17), subject=True, shadow_w=0.26)
    S.put("wellness_kettlebell", 1.38, 0.94, 0.17, color=(0.52, 0.10, 0.09), shadow_w=0.18)
    S.put("wellness_dumbbell", 1.05, 0.985, 0.12, shadow_w=0.5)
    S.focus("detail", 1.36, 0.80)
    # rim light: hot red edge lighting from behind
    S.soft(1.15, 0.50, 0.55, 0.22, red, 0.30 if dark else 0.14, 1.6, add=True)
    S.soft(1.55, 0.70, 0.18, 0.2, red, 0.22 if dark else 0.10, 1.6, add=True)
    with S.near():
        S.soft(0.50, 1.12, 0.38, 0.14, BLACK, 0.75, 1.0)
        S.circle(1.88, 0.62, 0.05, (1.0, 0.3, 0.22), alpha=0.35, lift=0)


# ====================================================================================== DENTAL
@sprop("wellness_dental_chair", aspect=1.62, fill=1.0)
def dental_chair(c, color):
    """Dental chair in side view with an articulated overhead lamp (head of the patient on the right)."""
    up = color or (0.20, 0.52, 0.86)
    steel = (0.30, 0.32, 0.36)
    ao(c, 0.0, 0.0, 1.1, 0.18)
    # lamp pole first (it stands behind the chair)
    _metal(c, 0.82, 0.42, 0.06, 0.84, 0.9)
    c.ellipse(0.82, 0.02, 0.13, 0.034, steel, lift=0.2)
    # base plate and hydraulic column
    c.ellipse(-0.10, 0.025, 0.34, 0.06, steel, lift=0.2)
    c.ellipse(-0.10, 0.04, 0.29, 0.045, (0.55, 0.57, 0.62), lift=0.3)
    _metal(c, -0.10, 0.17, 0.12, 0.26, 1.0)
    c.rect(-0.08, 0.30, 0.20, 0.045, steel, r=0.02, lift=0.3)
    # leg rest slopes down, seat, steep back rest, head rest
    c.poly([(-0.17, 0.46), (-0.62, 0.34), (-0.64, 0.25), (-0.17, 0.36)], scale(up, 0.82), lift=0.2)
    c.poly([(-0.19, 0.455), (-0.60, 0.345), (-0.60, 0.365), (-0.19, 0.465)], scale(up, 1.3), lift=0.0, alpha=0.6)
    c.rect(-0.68, 0.22, 0.10, 0.045, steel, r=0.015, lift=0.3)
    c.rect(-0.01, 0.405, 0.44, 0.11, scale(up, 0.9), r=0.05, lift=0.22)
    ax0, ay0, ax1, ay1 = 0.14, 0.42, 0.45, 0.80
    d = math.hypot(ax1 - ax0, ay1 - ay0)
    nx, ny = -(ay1 - ay0) / d * 0.095, (ax1 - ax0) / d * 0.095
    c.poly([(ax0 + nx, ay0 + ny), (ax1 + nx, ay1 + ny), (ax1 - nx, ay1 - ny), (ax0 - nx, ay0 - ny)], scale(up, 0.78), lift=0.2)
    c.poly([(ax0 + nx * 0.9, ay0 + ny * 0.9), (ax1 + nx * 0.9, ay1 + ny * 0.9), (ax1 + nx * 0.45, ay1 + ny * 0.45), (ax0 + nx * 0.45, ay0 + ny * 0.45)],
           scale(up, 1.35), lift=0.0, alpha=0.55)
    c.ellipse(0.50, 0.88, 0.075, 0.105, scale(up, 0.95), angle=-35, lift=0.2)
    c.ellipse(0.48, 0.895, 0.052, 0.082, scale(up, 1.35), angle=-35, lift=0.0, alpha=0.6)
    for k in range(4):                                            # stitched seams
        t = 0.2 + k * 0.2
        c.line(ax0 + (ax1 - ax0) * t + nx * 0.9, ay0 + (ay1 - ay0) * t + ny * 0.9, ax0 + (ax1 - ax0) * t - nx * 0.8,
               ay0 + (ay1 - ay0) * t - ny * 0.8, 0.003, scale(up, 0.6), 0.6)
    c.line(0.0, 0.455, 0.0, 0.36, 0.003, scale(up, 0.6), 0.5)
    soft_disc(c, 0.20, 0.42, 0.18, 0.05, BLACK, 0.3, 1.3)
    gloss(c, -0.25, 0.475, 0.16, 0.018, 3, 0.45)
    gloss(c, 0.22, 0.66, 0.025, 0.13, -36, 0.5)
    c.rect(0.02, 0.55, 0.26, 0.035, steel, r=0.016, lift=0.3)                     # arm rest
    c.rect(0.02, 0.56, 0.24, 0.007, WHITE, alpha=0.4, lift=0)
    # overhead lamp: two arms and a big round head with a bright lens
    c.line(0.82, 0.80, 0.62, 0.95, 0.040, (0.78, 0.80, 0.84), 1.0)
    c.line(0.80, 0.815, 0.61, 0.962, 0.010, WHITE, 0.6)
    c.line(0.62, 0.95, 0.34, 0.95, 0.034, (0.74, 0.76, 0.80), 1.0)
    c.line(0.62, 0.962, 0.34, 0.962, 0.008, WHITE, 0.6)
    c.ellipse(0.62, 0.95, 0.032, 0.032, steel, lift=0.3)
    c.ellipse(0.82, 0.80, 0.032, 0.032, steel, lift=0.3)
    c.ellipse(0.30, 0.945, 0.175, 0.078, (0.30, 0.33, 0.38), angle=-12, lift=0.2)       # dark rim so the lamp reads on a bright wall
    c.ellipse(0.30, 0.955, 0.16, 0.065, (0.90, 0.92, 0.95), angle=-12, lift=0.25)       # white housing
    c.ellipse(0.29, 0.94, 0.15, 0.052, scale(up, 1.0), angle=-12, lift=0.0, alpha=0.9)   # accent ring
    c.ellipse(0.28, 0.915, 0.14, 0.045, (0.98, 0.99, 1.0), angle=-12, lift=0.0)      # lit lens
    c.ellipse(0.28, 0.91, 0.11, 0.028, (1.0, 1.0, 0.90), angle=-12, lift=0.0)
    soft_disc(c, 0.28, 0.90, 0.34, 0.11, (1.0, 1.0, 0.96), 0.5, 1.6, add=True)
    soft_disc(c, 0.33, 0.62, 0.34, 0.30, (1.0, 1.0, 0.96), 0.16, 1.8, add=True)       # cone of light on the patient


@sprop("wellness_tooth_model", aspect=0.95, fill=1.0)
def dental_tooth(c, color):
    """A big molar model: white enamel crown on a pink gum block."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.78, 0.13)
    pink = (0.90, 0.48, 0.50)
    c.ellipse(0.0, 0.02, 0.38, 0.38 * TILT * 0.8, scale(pink, 0.5), lift=0)
    _hb(c, 0.0, 0.12, 0.76, 0.20, pink, r=0.05, kl=1.15, kr=0.62)
    c.ellipse(0.0, 0.23, 0.38, 0.38 * TILT * 0.85, scale(pink, 1.08), lift=0.1)
    soft_disc(c, 0.0, 0.225, 0.2, 0.07, BLACK, 0.28, 1.2)
    gloss(c, -0.18, 0.26, 0.09, 0.025, 10, 0.5)
    crown = [(-0.20, 0.26), (-0.27, 0.42), (-0.30, 0.62), (-0.26, 0.80), (-0.15, 0.93), (-0.05, 0.86), (0.03, 0.88), (0.13, 0.95),
             (0.24, 0.84), (0.30, 0.64), (0.28, 0.43), (0.21, 0.26), (0.0, 0.22)]
    _smooth(c, crown, scale((0.95, 0.93, 0.86), 0.7), 0.0)
    _smooth(c, [(x * 0.96 - 0.005, y * 0.985 + 0.004) for x, y in crown], (0.97, 0.96, 0.91), 0.16)
    soft_disc(c, 0.22, 0.52, 0.10, 0.30, (0.45, 0.35, 0.22), 0.28, 1.3)
    soft_disc(c, -0.14, 0.68, 0.10, 0.20, WHITE, 0.4, 1.2, add=True)
    soft_disc(c, 0.0, 0.30, 0.2, 0.06, (0.4, 0.3, 0.2), 0.25, 1.4)
    craft.strand(c, -0.01, 0.89, 0.22, -90, 0.014, (0.68, 0.62, 0.46), 0.55, 0.25)     # fissure between the cusps
    craft.strand(c, -0.05, 0.84, 0.2, -105, 0.008, (0.72, 0.66, 0.52), 0.4, -0.3)
    gloss(c, -0.17, 0.82, 0.05, 0.04, 40, 0.8)
    gloss(c, -0.20, 0.55, 0.025, 0.1, 0, 0.45)
    for _ in range(18):
        c.ellipse(rng.uniform(-0.22, 0.24), rng.uniform(0.32, 0.8), rng.uniform(0.004, 0.012), rng.uniform(0.003, 0.008), (0.62, 0.58, 0.45),
                  alpha=rng.uniform(0.06, 0.16), lift=0)


@sprop("wellness_jaw_model", aspect=2.4, fill=0.52)
def dental_jaw(c, color):
    """Upper jaw teaching model: pink gum arch with a ring of teeth on a clear stand."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.2, 0.22)
    pink = (0.88, 0.46, 0.48)
    c.ellipse(0.0, 0.03, 0.62, 0.62 * TILT, (0.25, 0.28, 0.32), lift=0)
    c.ellipse(0.0, 0.055, 0.62, 0.62 * TILT, (0.60, 0.64, 0.70), lift=0.2)
    a, b, v0 = 0.46, 0.46 * TILT * 1.05, 0.15
    c.ellipse(0.0, v0 - 0.02, a * 1.1, b * 1.14, scale(pink, 0.55), lift=0)
    c.ellipse(0.0, v0, a * 1.1, b * 1.14, pink, lift=0.18)
    c.ellipse(0.0, v0 + 0.012, a * 0.58, b * 0.60, (0.60, 0.64, 0.70), lift=0.1)              # opening of the arch
    c.ellipse(0.0, v0 + 0.05, a * 0.48, b * 0.50, (0.52, 0.55, 0.62), lift=0.1)
    c.rect(0.0, v0 + b * 0.75, a * 1.0, b * 0.8, (0.60, 0.64, 0.70), lift=0.0)
    teeth = []
    for k in range(13):
        th = math.radians(184 + k * 172.0 / 12)
        teeth.append((a * math.cos(th), v0 + b * math.sin(th) + 0.05, k))
    teeth.sort(key=lambda t: -t[1])
    for x, y, k in teeth:
        m = 1.0 - abs(k - 6) / 6.0                                  # front teeth are narrower, back molars wider
        w = 0.085 + 0.045 * (1 - m)
        hh = 0.115
        c.ellipse(x + 0.004, y - hh * 0.35, w * 0.55, hh * 0.28, scale(pink, 0.6), alpha=0.6, lift=0)
        _hb(c, x, y, w, hh, (0.96, 0.94, 0.88), r=0.03, kl=1.05, kr=0.78)
        c.ellipse(x, y + hh * 0.46, w * 0.46, hh * 0.15, (0.99, 0.98, 0.94), lift=0)
        gloss(c, x - w * 0.18, y + hh * 0.12, w * 0.10, hh * 0.28, 0, 0.5)
    soft_disc(c, -0.1, 0.34, 0.4, 0.07, WHITE, 0.18, 1.2, add=True)


@sprop("wellness_instrument_cart", aspect=0.84, fill=1.0)
def dental_cart(c, color):
    """Mobile dental cabinet: cream body, two drawers, a steel tray with instruments."""
    ao(c, 0.0, 0.0, 0.8, 0.12)
    body = color or (0.93, 0.95, 0.97)
    for u in (-0.30, 0.30):
        c.ellipse(u, 0.03, 0.045, 0.045, (0.2, 0.2, 0.22), lift=0.2)
    _hb(c, 0.0, 0.46, 0.80, 0.82, body, r=0.03, kl=1.04, kr=0.80)
    c.rect(0.0, 0.88, 0.84, 0.045, scale(body, 1.03), r=0.012, lift=0.15)
    c.rect(-0.05, 0.905, 0.76, 0.008, WHITE, alpha=0.7, lift=0)
    for vv in (0.64, 0.30):
        c.rect(0.0, vv, 0.70, 0.30, scale(body, 0.96), r=0.02, lift=0.1)
        c.rect(0.0, vv + 0.145, 0.70, 0.004, scale(body, 0.7), lift=0, alpha=0.7)
        c.rect(0.0, vv + 0.07, 0.26, 0.022, (0.55, 0.58, 0.64), r=0.01, lift=0.4)
        c.rect(0.0, vv + 0.077, 0.24, 0.005, WHITE, alpha=0.7, lift=0)
    # steel tray and instruments
    c.rect(0.0, 0.935, 0.66, 0.03, (0.70, 0.73, 0.78), r=0.008, lift=0.3)
    c.rect(-0.03, 0.948, 0.60, 0.005, WHITE, alpha=0.7, lift=0)
    for u, ang, ln in ((-0.20, 12, 0.34), (0.02, 6, 0.30), (0.2, 14, 0.26)):
        a = math.radians(ang)
        c.line(u, 0.958, u + math.cos(a) * ln * 0.5, 0.958 + math.sin(a) * ln * 0.5 * 0.1, 0.012, (0.62, 0.64, 0.68), 1.0)
        c.line(u, 0.962, u + math.cos(a) * ln * 0.5, 0.962, 0.004, WHITE, 0.8)
    c.ellipse(0.22, 0.975, 0.03, 0.012, (0.88, 0.92, 0.96), lift=0.2)


@niche("dental", "Dental clinic", subjects=("wellness_dental_chair", "wellness_tooth_model"),
       strong=("dentist", "dental", "dental clinic", "teeth", "tooth", "orthodontist", "braces", "smile", "dant ka doctor", "daant",
               "daant ka doctor", "dentist clinic", "दंत", "दांत", "दंत चिकित्सक", "डेंटल"),
       weak=("whitening", "implant", "oral", "root canal", "cavity", "mouth"),
       accent="#2e86de", mood="cool", group="wellness")
def dental(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    cab = mix(P.paper, P.accent_light, 0.15)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.64)
        S.glow(1.2, -0.08, 1.1, P.light, 0.35 * gl, 1.5)                             # ceiling light panel
        S.rect(1.2, 0.0, 1.1, 0.05, mix(WHITE, P.light, 0.5), lift=0.0)
        S.window(0.38, 0.30, 0.46, 0.40, bars=False)                                 # window with blinds
        for i in range(9):
            S.rect(0.38, 0.12 + i * 0.043, 0.46, 0.016, scale(mix(P.paper, P.light, 0.4), 0.9 - 0.02 * (i % 2)), lift=0.0, alpha=0.9)
        door = mix(P.accent, P.paper, 0.78 if not dark else 0.55)
        for u in (1.50, 1.86, 2.22):                                                 # wall cabinets
            S.rect(u, 0.20, 0.33, 0.26, door, r=0.01, lift=0.06)
            S.rect(u, 0.20, 0.004, 0.26, scale(door, 0.6), lift=0.0)
            S.rect(u - 0.03, 0.32, 0.05, 0.01, scale(P.paper, 0.9), lift=0.0)
        S.rect(0.92, 0.27, 0.34, 0.24, mix(WHITE, P.light, 0.5), r=0.008, lift=0.0)   # x-ray light box
        S.glow(0.92, 0.27, 0.45, mix(WHITE, P.light, 0.5), 0.35 * gl, 1.6)
        for k in range(9):
            x = 0.92 + (k - 4) * 0.033
            S.rect(x, 0.235, 0.022, 0.05 - abs(k - 4) * 0.002, scale(P.accent_dark, 0.9), r=0.006, lift=0.0, alpha=0.7)
            S.rect(x, 0.30, 0.022, 0.055 - abs(k - 4) * 0.002, scale(P.accent_dark, 0.9), r=0.006, lift=0.0, alpha=0.7)
        S.rect(1.86, 0.62, 1.2, 0.05, scale(cab, 0.95), lift=0.1)                    # worktop
        S.rect(1.86, 0.52, 0.28, 0.12, P.accent_light, r=0.02, lift=0.0, alpha=0.6)  # framed poster
        S.glow(0.38, 0.30, 0.6, P.light, 0.3 * gl, 1.5)
        S.floor(0.64, _tone(P, 1.12, 0.1), _tone(P, 0.72, 0.1))
    S.rect(1.0, 0.64, 7.0, 0.012, scale(_tone(P, 0.8), 0.9), lift=0.0)
    _persp_lines(S, 0.65, 1.3, scale(_tone(P, 0.5), 0.7), 0.4, rows=6, cols=18, uc=1.1)
    S.soft(1.0, 0.86, 1.1, 0.2, P.light, 0.22 * gl, 1.5, add=True)                   # light pool from the lamp
    S.put("wellness_dental_chair", 0.98, 0.95, 0.62, color=P.accent, subject=True, shadow_w=1.0)
    S.put("wellness_instrument_cart", 1.56, 0.95, 0.30, shadow_w=0.32)
    ct = 0.95 - 0.30 * 0.97
    S.put("wellness_tooth_model", 1.51, ct, 0.20, subject=True, shadow=False)
    S.put("wellness_jaw_model", 1.63, ct, 0.07, shadow=False, framed=False)
    S.focus("detail", 1.40, 0.70)
    S.glow(0.97, 0.38, 0.5, P.light, 0.20 * gl, 1.6)
    _near_leaves(S, 0.46, 1.10, (0.20, 0.45, 0.28))


# ====================================================================================== shared props
def _box3d(c, u, v, w, h, dx, dy, face, k_side=0.70, k_top=1.14):
    """Box in a raised 3/4 view: front face centred on u standing on v, extruded right and back by (dx, dy)."""
    x0, x1 = u - w / 2, u + w / 2
    c.poly([(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], scale(face, k_side), lift=0.12)
    c.poly([(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], scale(face, k_top), lift=0.0)
    c.rect(u, v + h / 2, w, h, face, lift=0.10)


def _cross(c, u, v, r, color, alpha=1.0):
    c.rect(u, v, r * 2.0, r * 0.68, color, r=r * 0.08, lift=0.15, alpha=alpha)
    c.rect(u, v, r * 0.68, r * 2.0, color, r=r * 0.08, lift=0.15, alpha=alpha)


@sprop("wellness_med_cross", aspect=0.86, fill=1.0)
def med_cross(c, color):
    """A standing sign block with a big medical cross (colour = the accent)."""
    col = color or (0.1, 0.62, 0.45)
    ao(c, 0.0, 0.0, 0.9, 0.16)
    _box3d(c, -0.03, 0.06, 0.78, 0.82, 0.14, 0.09, (0.96, 0.97, 0.98))
    c.rect(-0.03, 0.025, 0.46, 0.05, (0.35, 0.38, 0.42), r=0.02, lift=0.3)
    _cross(c, -0.03, 0.47, 0.28, scale(col, 0.78))
    _cross(c, -0.03, 0.475, 0.265, col)
    c.rect(-0.03, 0.62, 0.20, 0.05, WHITE, alpha=0.18, lift=0)
    soft_disc(c, -0.2, 0.70, 0.22, 0.2, WHITE, 0.32, 1.2, add=True)
    soft_disc(c, 0.28, 0.25, 0.12, 0.28, BLACK, 0.12, 1.3)
    gloss(c, -0.30, 0.78, 0.07, 0.05, 40, 0.5)
    c.rect(0.0, 0.89, 0.4, 0.01, WHITE, alpha=0.4, lift=0)


@sprop("wellness_plant", aspect=0.9, fill=1.0)
def wellness_plant(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.52, 0.10)
    pot = color or (0.88, 0.86, 0.82)
    _hb(c, 0.0, 0.14, 0.38, 0.26, pot, r=0.04)
    c.ellipse(0.0, 0.27, 0.19, 0.19 * TILT, scale(pot, 0.62), lift=0)
    c.ellipse(0.0, 0.27, 0.165, 0.165 * TILT * 0.9, (0.25, 0.17, 0.12), lift=0)
    gloss(c, -0.10, 0.18, 0.025, 0.08, 0, 0.35)
    for i in range(16):
        a = rng.uniform(25, 155)
        L = rng.uniform(0.34, 0.60)
        g = rng.uniform(0.0, 0.12)
        craft.leaf(c, rng.uniform(-0.07, 0.07), 0.28, L, a, (0.16 + g, 0.42 + g * 1.4, 0.2 + g * 0.3), 0.42)


@sprop("wellness_rx_pad", aspect=2.6, fill=0.38)
def rx_pad(c, color):
    ao(c, 0.0, 0.0, 0.9, 0.2)
    c.poly([(-0.46, 0.04), (0.46, 0.04), (0.40, 0.34), (-0.40, 0.34)], (0.86, 0.88, 0.90), lift=0.1)
    c.poly([(-0.46, 0.04), (0.46, 0.04), (0.46, 0.075), (-0.46, 0.075)], (0.75, 0.77, 0.80), lift=0.1)
    c.poly([(-0.455, 0.075), (0.455, 0.075), (0.405, 0.36), (-0.405, 0.36)], (0.98, 0.98, 0.97), lift=0.1)
    c.poly([(-0.40, 0.36), (0.40, 0.36), (0.405, 0.325), (-0.405, 0.325)], color or (0.1, 0.55, 0.45), lift=0.1)
    c.text("Rx", -0.22, 0.20, 0.09, color or (0.1, 0.55, 0.45), 0.22)
    for k in range(4):
        c.line(-0.04, 0.265 - k * 0.045, 0.30 - k * 0.012, 0.265 - k * 0.045, 0.006, (0.65, 0.68, 0.72), 0.7)
    c.line(0.32, 0.10, 0.58, 0.22, 0.026, (0.15, 0.17, 0.22), 1.0)                  # pen
    c.line(0.325, 0.108, 0.56, 0.22, 0.006, (0.9, 0.9, 0.95), 0.7)
    soft_disc(c, -0.2, 0.30, 0.3, 0.07, WHITE, 0.4, 1.2, add=True)


# ====================================================================================== CLINIC / DOCTOR
@sprop("wellness_stethoscope", aspect=1.85, fill=0.62)
def doc_stethoscope(c, color):
    """Stethoscope coiled on a desk: tubing loop, Y junction, binaural tubes with ear tips and a chrome chest piece."""
    tube = color or (0.12, 0.17, 0.22)
    ao(c, 0.04, 0.0, 1.35, 0.3, 0.32)
    cu, cv = -0.05, 0.22
    for k, (w, col, dv, al) in enumerate(((0.050, scale(tube, 0.5), -0.012, 1.0), (0.040, tube, 0.0, 1.0), (0.014, scale(tube, 3.4), 0.011, 0.7))):
        craft.arc(c, cu, cv + dv, 0.43, 0.22, 38, 322, w, col, al, steps=18)
    # Y junction and metal binaural tubes with ear tips
    c.ellipse(0.30, 0.36, 0.034, 0.03, (0.78, 0.80, 0.84), lift=0.3)
    for ex, ey in ((0.08, 0.60), (0.27, 0.64)):
        c.line(0.30, 0.37, ex, ey, 0.020, (0.50, 0.53, 0.58), 1.0)
        c.line(0.30 - 0.003, 0.378, ex - 0.003, ey + 0.004, 0.006, WHITE, 0.75)
        c.ellipse(ex, ey + 0.012, 0.030, 0.022, tube, lift=0.3)
        c.ellipse(ex - 0.006, ey + 0.02, 0.012, 0.007, WHITE, alpha=0.5, lift=0)
    # chest piece
    cu2, cv2 = 0.52, 0.10
    c.line(0.29, 0.085, 0.46, 0.105, 0.040, scale(tube, 0.5))
    c.line(0.29, 0.092, 0.46, 0.112, 0.032, tube)
    c.ellipse(cu2, cv2 - 0.02, 0.15, 0.15 * 0.55, (0.38, 0.40, 0.45), lift=0)
    c.ellipse(cu2, cv2, 0.15, 0.15 * 0.55, (0.84, 0.86, 0.90), lift=0.3)
    c.ellipse(cu2, cv2 + 0.004, 0.115, 0.115 * 0.55, (0.20, 0.22, 0.26), lift=0.15)
    c.ellipse(cu2, cv2 + 0.006, 0.09, 0.09 * 0.55, (0.58, 0.60, 0.66), lift=0.25)
    soft_disc(c, cu2 - 0.05, cv2 + 0.04, 0.1, 0.03, WHITE, 0.6, 1.2, add=True)
    gloss(c, -0.28, 0.40, 0.09, 0.015, 40, 0.5)


@sprop("wellness_clipboard", aspect=1.6, fill=0.6)
def doc_clipboard(c, color):
    rng = c.rng
    ac = color or (0.1, 0.62, 0.5)
    ao(c, 0.0, 0.0, 1.0, 0.24, 0.3)
    c.poly([(-0.42, 0.04), (0.42, 0.04), (0.37, 0.64), (-0.37, 0.64)], (0.34, 0.24, 0.16), lift=0.12)
    c.poly([(-0.42, 0.04), (0.42, 0.04), (0.42, 0.07), (-0.42, 0.07)], (0.22, 0.15, 0.10), lift=0.1)
    c.poly([(-0.37, 0.09), (0.36, 0.09), (0.32, 0.60), (-0.33, 0.60)], (0.98, 0.98, 0.96), lift=0.08)
    soft_disc(c, 0.20, 0.30, 0.2, 0.3, (0.5, 0.5, 0.45), 0.10, 1.3)
    c.rect(-0.12, 0.54, 0.40, 0.045, ac, r=0.01, lift=0.1)
    c.text("PATIENT CHART", -0.12, 0.535, 0.032, WHITE, 0.14)
    for k in range(6):
        y = 0.45 - k * 0.062
        x0, x1 = -0.27 + k * 0.010, 0.22 - k * 0.012
        c.rect(x0 - 0.02, y, 0.035, 0.025, (0.85, 0.88, 0.9), r=0.004, lift=0)
        if k % 3 != 1:
            c.line(x0 - 0.03, y, x0 - 0.018, y - 0.014, 0.007, ac, 1.0)
            c.line(x0 - 0.018, y - 0.014, x0 - 0.0, y + 0.012, 0.007, ac, 1.0)
        c.line(x0 + 0.03, y, x1 - rng.uniform(0.0, 0.08), y, 0.007, (0.55, 0.58, 0.64), 0.8)
    c.rect(0.0, 0.66, 0.20, 0.07, (0.72, 0.74, 0.78), r=0.02, lift=0.4)                       # clip
    c.rect(0.0, 0.675, 0.14, 0.015, WHITE, alpha=0.7, lift=0)
    c.ellipse(0.0, 0.70, 0.04, 0.02, (0.45, 0.47, 0.52), lift=0.3)
    c.line(0.30, 0.15, 0.58, 0.40, 0.026, (0.12, 0.35, 0.65), 1.0)                            # pen
    c.line(0.30, 0.157, 0.57, 0.405, 0.006, WHITE, 0.6)
    soft_disc(c, -0.2, 0.50, 0.3, 0.14, WHITE, 0.18, 1.2, add=True)


@niche("clinic-doctor", "Doctor's clinic", subjects=("wellness_stethoscope",),
       strong=("doctor", "physician", "hospital", "general physician", "medical clinic", "healthcare", "stethoscope",
               "daktar", "doctor sahab", "aspatal", "डॉक्टर", "अस्पताल", "चिकित्सक"),
       weak=("clinic", "क्लिनिक", "health", "patient", "consultation", "medical", "nurse", "treatment"),
       accent="#16a085", mood="light", group="wellness", avoid=("dental", "dentist", "teeth"))
def clinic_doctor(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.7 if dark else 1.0
    top = mix(P.surface, P.paper, 0.38) if not dark else scale(P.surface, 0.8)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.56)
        S.rect(1.0, 0.47, 7.0, 0.18, mix(P.wall_bot, P.accent_light, 0.45), lift=0.0)           # accent wainscot
        S.rect(1.0, 0.375, 7.0, 0.012, scale(P.paper, 0.97), lift=0.0)
        S.window(0.30, 0.22, 0.34, 0.34)
        S.glow(0.3, 0.22, 0.8, P.light, 0.3 * gl, 1.5)
        # anatomy poster: a body figure on a pale sheet
        S.rect(1.55, 0.22, 0.30, 0.38, mix(WHITE, P.light, 0.4), r=0.006, lift=0.0)
        S.circle(1.55, 0.10, 0.028, (0.88, 0.55, 0.45), lift=0.0)
        S.rect(1.55, 0.21, 0.08, 0.15, (0.82, 0.30, 0.28), r=0.02, lift=0.0)
        S.rect(1.55, 0.21, 0.04, 0.12, (0.28, 0.45, 0.72), r=0.01, lift=0.0, alpha=0.8)
        for sg in (-1, 1):
            S.line(1.55 + sg * 0.05, 0.15, 1.55 + sg * 0.12, 0.26, 0.022, (0.86, 0.45, 0.38))
            S.line(1.55 + sg * 0.03, 0.30, 1.55 + sg * 0.05, 0.38, 0.026, (0.80, 0.30, 0.28))
        # diplomas and a wall shelf
        for u, w in ((1.98, 0.17), (2.22, 0.17)):
            S.rect(u, 0.20, w, 0.22, scale(P.paper, 1.02), r=0.004, lift=0.0)
            S.rect(u, 0.20, w * 0.8, 0.16, mix(P.paper, P.accent_light, 0.4), lift=0.0)
        S.rect(0.85, 0.30, 0.45, 0.012, scale(P.surface, 0.7), lift=0.0)
        for k, col in enumerate(((0.75, 0.3, 0.25), (0.25, 0.45, 0.7), P.accent, (0.9, 0.75, 0.3))):
            S.rect(0.70 + k * 0.05, 0.255, 0.035, 0.07 + 0.01 * (k % 2), col, lift=0.1)
        S.pendant(1.0, -0.1, 0.10, (1.0, 0.95, 0.85), 0.07)
        S.pendant(1.9, -0.1, 0.08, (1.0, 0.95, 0.85), 0.07)
        S.floor(0.56, P.floor_top, P.floor_bot)
    S.rect(1.0, 0.56, 7.0, 0.008, scale(top, 0.5), lift=0.0)
    S.wood(-3.0, 0.56, 5.0, 1.3, top, plank=0.10, grain=0.2)
    S.soft(1.1, 0.74, 1.0, 0.2, P.light, 0.16 * gl, 1.5, add=True)
    S.put("wellness_plant", 0.66, 0.70, 0.30, shadow_w=0.3, framed=False)
    S.put("wellness_med_cross", 1.50, 0.76, 0.28, color=P.accent, shadow_w=0.3)
    S.put("wellness_clipboard", 0.82, 0.85, 0.24, color=P.accent, shadow_w=0.4)
    S.put("wellness_stethoscope", 1.15, 0.97, 0.30, subject=True, shadow_w=0.5)
    S.put("wellness_rx_pad", 1.72, 1.0, 0.13, color=P.accent_dark, shadow_w=0.3)
    S.focus("detail", 1.36, 0.82)
    _near_leaves(S, 0.46, 1.10, (0.22, 0.48, 0.3))


# ====================================================================================== PHARMACY
def _pill(c, u, v, ang, col1, col2, ln=0.06, w=0.026):
    a = math.radians(ang)
    dx, dy = math.cos(a) * ln / 2, math.sin(a) * ln / 2 * 0.7
    c.line(u - dx, v - dy, u + dx, v + dy, w, col1, 1.0)
    c.line(u, v, u + dx, v + dy, w, col2, 1.0)
    c.line(u - dx * 0.6, v - dy * 0.6 + w * 0.25, u + dx * 0.5, v + dy * 0.5 + w * 0.25, w * 0.22, WHITE, 0.5)


def _bottle(c, u, v, r, h, amber, accent):
    craft.cylinder(c, u, v, r, h, scale(amber, 1.25), scale(amber, 0.50), scale(amber, 0.8), lip=False)
    # label wrapped around the body
    c.rect(u, v + h * 0.46, r * 2.0 * 0.98, h * 0.5, (0.97, 0.97, 0.95), lift=0.0)
    craft.hshade_box(c, u, v + h * 0.46, r * 1.96, h * 0.5, (1.0, 1.0, 1.0), (0.72, 0.72, 0.72), 0.0, 0.5)
    c.rect(u, v + h * 0.64, r * 1.96, h * 0.09, accent, lift=0.1)
    _cross(c, u - r * 0.35, v + h * 0.44, r * 0.20, accent)
    for k in range(3):
        c.line(u - r * 0.05, v + h * 0.50 - k * h * 0.07, u + r * (0.7 - 0.12 * k), v + h * 0.50 - k * h * 0.07, 0.006, (0.45, 0.47, 0.52), 0.8)
    soft_disc(c, u - r * 0.62, v + h * 0.5, r * 0.10, h * 0.40, WHITE, 0.45, 1.1, add=True)
    # child-proof cap with ribs
    craft.cylinder(c, u, v + h, r * 1.05, h * 0.2, (0.97, 0.97, 0.98), (0.62, 0.64, 0.68), (0.95, 0.95, 0.96))
    for k in range(7):
        x = u - r * 0.95 + k * r * 0.317
        c.line(x, v + h + 0.004, x, v + h * 1.2 - 0.004, 0.004, (0.5, 0.52, 0.56), 0.35)
    gloss(c, u - r * 0.3, v + h * 1.2 + 0.01, r * 0.4, r * 0.1, 0, 0.5)


@sprop("wellness_pill_bottles", aspect=1.9, fill=0.62)
def pharm_bottles(c, color):
    rng = c.rng
    ac = color or (0.15, 0.68, 0.38)
    amber = (0.80, 0.42, 0.10)
    ao(c, 0.0, 0.0, 1.5, 0.28)
    _bottle(c, 0.34, 0.07, 0.115, 0.34, mix(amber, (0.9, 0.55, 0.15), 0.3), ac)
    _bottle(c, -0.36, 0.10, 0.16, 0.42, amber, ac)
    _bottle(c, 0.0, 0.04, 0.14, 0.50, scale(amber, 0.92), scale(ac, 0.9))
    cols = [((0.95, 0.3, 0.3), (0.98, 0.98, 0.98)), ((0.2, 0.5, 0.9), (0.98, 0.98, 0.98)), ((0.98, 0.8, 0.2), (0.98, 0.55, 0.15)),
            ((0.2, 0.7, 0.4), (0.97, 0.97, 0.9))]
    for i in range(9):                                                   # spilled capsules and tablets
        u, v = rng.uniform(-0.1, 0.62) + 0.4, rng.uniform(-0.01, 0.07)
        k1, k2 = cols[rng.randrange(4)]
        if i % 3 == 2:
            c.ellipse(u, v, 0.03, 0.02, (0.97, 0.96, 0.9), lift=0.15)
            c.ellipse(u - 0.006, v + 0.006, 0.01, 0.006, WHITE, alpha=0.7, lift=0)
        else:
            _pill(c, u, v, rng.uniform(-30, 30), k1, k2)


@sprop("wellness_mortar", aspect=1.45, fill=0.58)
def pharm_mortar(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.2)
    stone = (0.90, 0.88, 0.84)
    c.poly([(-0.34, 0.50), (0.34, 0.50), (0.22, 0.10), (-0.22, 0.10)], scale(stone, 0.7), lift=0.0)
    craft.hshade_box(c, 0.0, 0.30, 0.52, 0.12, scale(stone, 1.0), scale(stone, 0.55), 0.04)
    c.ellipse(0.0, 0.07, 0.22, 0.22 * 0.35, scale(stone, 0.5), lift=0)
    c.poly([(-0.34, 0.50), (0.34, 0.50), (0.23, 0.12), (-0.23, 0.12)], scale(stone, 0.9), lift=0.12)
    soft_disc(c, 0.22, 0.30, 0.16, 0.20, BLACK, 0.32, 1.3)
    soft_disc(c, -0.20, 0.30, 0.08, 0.17, WHITE, 0.5, 1.2, add=True)
    c.ellipse(0.0, 0.07, 0.24, 0.24 * 0.3, scale(stone, 0.6), lift=0)
    craft.arc(c, 0.0, 0.07, 0.24, 0.07, 195, 345, 0.012, scale(stone, 0.8), 1.0, steps=8)
    disc(c, 0.0, 0.50, 0.36, scale(stone, 1.02), 0.38, 0.06, rim=True)
    c.ellipse(0.0, 0.505, 0.30, 0.30 * 0.38, scale(stone, 0.5), lift=0.0)                     # inside
    c.ellipse(0.0, 0.50, 0.28, 0.28 * 0.36, (0.36, 0.30, 0.20), lift=0.1)
    soft_disc(c, 0.06, 0.52, 0.24, 0.07, (0.25, 0.20, 0.12), 0.5, 1.1)
    for _ in range(22):                                                 # herbs and powder in the bowl
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.22
        c.ellipse(math.cos(a) * r, 0.50 + math.sin(a) * r * 0.30, rng.uniform(0.008, 0.02), rng.uniform(0.005, 0.01),
                  rng.choice([(0.30, 0.50, 0.22), (0.72, 0.68, 0.40), (0.88, 0.85, 0.7)]), lift=0.1)
    for _ in range(18):
        a = rng.uniform(0, 6.28)
        c.ellipse(math.cos(a) * 0.30, 0.325 + math.sin(a) * 0.01, rng.uniform(0.004, 0.012), rng.uniform(0.003, 0.006), scale(stone, rng.uniform(0.55, 0.8)), alpha=0.5, lift=0)
    # pestle leaning on the rim
    c.line(0.04, 0.54, 0.42, 0.96, 0.085, scale(stone, 0.75), 1.0)
    c.line(0.03, 0.55, 0.405, 0.95, 0.06, scale(stone, 1.0), 1.0)
    c.line(0.01, 0.56, 0.38, 0.95, 0.014, WHITE, 0.55)
    c.ellipse(0.44, 0.99, 0.065, 0.06, scale(stone, 0.95), lift=0.2)
    c.ellipse(0.425, 1.005, 0.026, 0.02, WHITE, alpha=0.55, lift=0)
    c.ellipse(0.02, 0.54, 0.06, 0.04, scale(stone, 0.85), lift=0.1)
    c.ellipse(0.0, 0.2, 0.0001, 0.0001, stone, lift=0)


@sprop("wellness_pill_tray", aspect=4.4, fill=0.34)
def pharm_tray(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.30, 0.35)
    st = (0.78, 0.80, 0.84)
    c.poly([(-0.74, 0.02), (0.74, 0.02), (0.70, 0.075), (-0.70, 0.075)], scale(st, 0.55), lift=0.1)
    c.poly([(-0.72, 0.07), (0.72, 0.07), (0.60, 0.34), (-0.60, 0.34)], scale(st, 0.65), lift=0.1)
    c.poly([(-0.66, 0.085), (0.66, 0.085), (0.56, 0.31), (-0.56, 0.31)], st, lift=0.25)
    c.poly([(-0.66, 0.085), (0.66, 0.085), (0.58, 0.14), (-0.58, 0.14)], scale(st, 0.78), lift=0.0, alpha=0.5)
    soft_disc(c, -0.25, 0.22, 0.5, 0.07, WHITE, 0.5, 1.2, add=True)
    cols = [((0.95, 0.3, 0.3), (0.98, 0.98, 0.98)), ((0.2, 0.5, 0.9), (0.98, 0.98, 0.98)), ((0.98, 0.8, 0.2), (0.98, 0.55, 0.15)),
            ((0.2, 0.7, 0.4), (0.97, 0.97, 0.9)), ((0.9, 0.4, 0.7), (0.98, 0.98, 0.98))]
    for i in range(34):
        u, v = rng.uniform(-0.42, 0.42) * (1 + (0.3 - 0.0)), rng.uniform(0.11, 0.28)
        u *= 0.95
        k1, k2 = cols[rng.randrange(5)]
        if i % 3 == 0:
            r = rng.uniform(0.022, 0.03)
            c.ellipse(u, v, r, r * 0.75, k1 if i % 2 else (0.97, 0.96, 0.92), lift=0.18)
            c.ellipse(u - r * 0.3, v + r * 0.25, r * 0.4, r * 0.2, WHITE, alpha=0.7, lift=0)
        else:
            _pill(c, u, v, rng.uniform(-60, 60), k1, k2, 0.07, 0.03)
    c.line(0.50, 0.12, 0.82, 0.26, 0.03, (0.68, 0.70, 0.74), 1.0)                       # counting spatula
    c.line(0.50, 0.125, 0.80, 0.262, 0.007, WHITE, 0.6)
    c.ellipse(0.80, 0.265, 0.07, 0.035, (0.80, 0.82, 0.86), angle=28, lift=0.3)


@sprop("wellness_med_boxes", aspect=1.4, fill=0.7)
def pharm_boxes(c, color):
    ac = color or (0.15, 0.68, 0.38)
    ao(c, 0.0, 0.0, 1.0, 0.2)
    spec = ((-0.28, 0.02, 0.36, 0.50, (0.96, 0.97, 0.98), ac), (0.14, 0.02, 0.32, 0.38, (0.98, 0.92, 0.80), (0.9, 0.45, 0.2)),
            (0.45, 0.02, 0.24, 0.30, (0.88, 0.94, 0.99), (0.2, 0.45, 0.85)))
    for u, v, w, h, face, band in spec:
        _box3d(c, u, v, w, h, 0.11, 0.07, face)
        c.rect(u, v + h * 0.78, w, h * 0.17, band, lift=0.15)
        c.poly([(u + w / 2, v + h * 0.695), (u + w / 2 + 0.11, v + h * 0.765), (u + w / 2 + 0.11, v + h * 0.935), (u + w / 2, v + h * 0.865)],
               scale(band, 0.7), lift=0.1)
        _cross(c, u - w * 0.18, v + h * 0.40, w * 0.16, band)
        for k in range(3):
            c.line(u - w * 0.02, v + h * (0.46 - k * 0.1), u + w * (0.36 - 0.07 * k), v + h * (0.46 - k * 0.1), 0.006, (0.5, 0.52, 0.58), 0.8)
        soft_disc(c, u - w * 0.3, v + h * 0.5, w * 0.1, h * 0.4, WHITE, 0.3, 1.1, add=True)


@niche("pharmacy", "Pharmacy / chemist", subjects=("wellness_pill_bottles", "wellness_mortar"),
       strong=("pharmacy", "chemist", "medicine", "medical store", "drugstore", "pharmacist", "dawai", "dawaai", "medical shop",
               "दवाई", "फार्मेसी", "दवा", "मेडिकल स्टोर", "केमिस्ट"),
       weak=("clinic", "क्लिनिक", "pills", "tablets", "prescription", "capsule", "health store", "drugs"),
       accent="#27ae60", mood="light", group="wellness")
def pharmacy(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.7 if dark else 1.0
    counter = scale(mix(P.wall_bot, P.accent_light, 0.10), 0.98)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # a wall of shelves full of medicine boxes
        pal_cols = [P.accent, P.accent_light, WHITE, P.accent_dark, (0.95, 0.75, 0.25), (0.3, 0.5, 0.85), (0.9, 0.9, 0.92), P.accent2]
        for row, v in enumerate((0.14, 0.31, 0.48)):
            u = -0.5
            while u < 2.6:
                w = S.rng.uniform(0.07, 0.15)
                h = S.rng.uniform(0.08, 0.135)
                col = pal_cols[S.rng.randrange(len(pal_cols))]
                if dark:
                    col = scale(col, 0.45)
                S.rect(u + w / 2, v - h / 2 + 0.018, w - 0.006, h, col, lift=0.08)
                S.rect(u + w / 2, v - h * 0.45 + 0.018, w - 0.006, h * 0.18, pal_cols[S.rng.randrange(len(pal_cols))], lift=0.0, alpha=0.7)
                u += w
            S.rect(1.0, v + 0.025, 6.0, 0.016, scale(P.paper, 0.85), lift=0.0)
            S.rect(1.0, v + 0.045, 6.0, 0.03, BLACK, lift=0.0, alpha=0.10)
            S.rect(1.0, v + 0.014, 6.0, 0.006, mix(WHITE, P.light, 0.5), lift=0.0)           # LED strip under the shelf
            S.glow(1.0, v + 0.03, 1.7, mix(WHITE, P.light, 0.4), 0.18 * gl, 1.8)
        # neon green cross sign
        S.glow(1.30, 0.28, 0.34, P.accent, 0.55 * gl, 1.6)
        S.rect(1.30, 0.28, 0.19, 0.19, (0.96, 0.98, 0.97), r=0.02, lift=0.0)
        _cross_stage(S, 1.30, 0.28, 0.075, P.accent)
        S.floor(0.60, scale(counter, 0.9), scale(counter, 0.7))
    # counter top: pale laminate with a darker back edge and glossy reflections
    _vgrad(S, -3, 5, 0.60, 1.4, scale(mix(counter, P.accent_light, 0.12), 1.02), scale(counter, 0.82), 12)
    S.rect(1.0, 0.605, 7.0, 0.018, scale(counter, 0.62), lift=0.0)
    S.rect(1.0, 0.622, 7.0, 0.006, WHITE, alpha=0.5, lift=0.0)
    for u, col in ((0.70, P.accent), (1.30, P.accent), (1.00, (0.95, 0.75, 0.25)), (1.62, (0.3, 0.5, 0.85))):       # reflections on the glossy counter
        S.soft(u, 0.70, 0.04, 0.10, col, 0.16 if not dark else 0.28, 1.2)
    S.soft(1.1, 0.80, 0.8, 0.10, WHITE, 0.40 if not dark else 0.10, 1.4, add=True)
    S.put("wellness_pill_tray", 0.90, 0.95, 0.16, shadow_w=0.6, framed=True)
    S.put("wellness_med_boxes", 1.56, 0.85, 0.28, color=P.accent, shadow_w=0.4)
    S.put("wellness_pill_bottles", 1.20, 0.95, 0.38, color=P.accent, subject=True, shadow_w=0.6)
    S.put("wellness_mortar", 1.04, 0.79, 0.23, subject=True, shadow_w=0.3)
    S.focus("detail", 1.08, 0.84)
    with S.near(18.0):
        pass
    for u, v, r, col in ((0.62, 1.02, 0.07, WHITE), (0.76, 1.08, 0.045, P.accent_light), (1.86, 1.0, 0.06, (0.98, 0.8, 0.3))):
        S.soft(u, v, r, r, col, 0.45, 0.5)


def _cross_stage(S, u, v, r, color):
    S.rect(u, v, r * 2.0, r * 0.68, color, r=r * 0.08, lift=0.1)
    S.rect(u, v, r * 0.68, r * 2.0, color, r=r * 0.08, lift=0.1)


# ====================================================================================== YOGA + SPA shared props
@sprop("wellness_candle", aspect=0.55, fill=0.85)
def wellness_candle(c, color):
    """Candle in a glass jar with a lit flame and a warm glow."""
    wax = color or (0.97, 0.93, 0.84)
    ao(c, 0.0, 0.0, 0.5, 0.09)
    craft.cylinder(c, 0.0, 0.04, 0.22, 0.40, scale(wax, 1.0), scale(wax, 0.66), scale(wax, 1.04), lip=False)
    c.rect(0.0, 0.25, 0.44, 0.36, WHITE, alpha=0.0, lift=0)
    craft.hshade_box(c, 0.0, 0.23, 0.46, 0.38, (1.0, 1.0, 1.0), (0.7, 0.75, 0.8), 0.03, 0.22)            # glass sheen
    c.ellipse(0.0, 0.44, 0.22, 0.22 * TILT, scale(wax, 0.8), lift=0)
    c.ellipse(0.0, 0.445, 0.19, 0.19 * TILT * 0.9, scale(wax, 1.08), lift=0.1)
    soft_disc(c, 0.0, 0.46, 0.13, 0.05, (1.0, 0.78, 0.4), 0.7, 1.2, add=True)
    c.line(0.0, 0.45, 0.0, 0.50, 0.012, (0.18, 0.12, 0.10), 1.0)
    c.poly([(0.0, 0.50), (-0.05, 0.58), (-0.035, 0.68), (0.0, 0.78), (0.035, 0.68), (0.05, 0.58)], (1.0, 0.62, 0.15), lift=0.0, alpha=0.95)
    c.poly([(0.0, 0.51), (-0.025, 0.58), (-0.015, 0.66), (0.0, 0.72), (0.015, 0.66), (0.025, 0.58)], (1.0, 0.95, 0.7), lift=0.0)
    c.ellipse(0.0, 0.54, 0.014, 0.03, (0.35, 0.55, 0.95), lift=0, alpha=0.6)
    soft_disc(c, 0.0, 0.62, 0.30, 0.34, (1.0, 0.72, 0.35), 0.40, 1.5, add=True)
    gloss(c, -0.15, 0.25, 0.015, 0.14, 0, 0.5)


# ====================================================================================== YOGA
@sprop("wellness_yoga_mat", aspect=3.9, fill=0.42)
def yoga_mat(c, color):
    """An unrolled yoga mat in perspective with a thickness edge, grip texture and a rolled end."""
    rng = c.rng
    col = color or (0.42, 0.62, 0.42)
    ao(c, 0.0, 0.0, 1.6, 0.26, 0.4)
    c.poly([(-0.82, 0.045), (0.82, 0.045), (0.82, 0.010), (-0.82, 0.010)], scale(col, 0.45), lift=0.1)            # thickness
    c.poly([(-0.82, 0.045), (0.82, 0.045), (0.58, 0.30), (-0.58, 0.30)], col, lift=0.16)
    c.poly([(-0.82, 0.045), (-0.58, 0.30), (-0.52, 0.30), (-0.76, 0.045)], scale(col, 1.2), lift=0.0, alpha=0.6)
    soft_disc(c, -0.2, 0.17, 0.55, 0.08, WHITE, 0.28, 1.3, add=True)
    soft_disc(c, 0.55, 0.14, 0.3, 0.1, BLACK, 0.18, 1.4)
    for k in range(-3, 4):                                                       # converging grip lines
        if k:
            c.line(k * 0.20, 0.05, k * 0.145, 0.295, 0.0035, scale(col, 0.78), 0.55)
    for _ in range(40):
        t = rng.uniform(0.05, 0.95)
        w = 0.82 - 0.24 * t
        c.ellipse(rng.uniform(-w, w) * 0.95, 0.045 + 0.25 * t, 0.006, 0.0025, scale(col, rng.choice((0.7, 1.3))), alpha=0.5, lift=0)
    # rolled-up end lying across the back
    ru, rv, rr = 0.0, 0.34, 0.075
    craft.hshade_box(c, ru, rv, 1.16, rr * 2, scale(col, 0.8), scale(col, 0.8), 0.0, 0.0)
    c.rect(ru, rv, 1.12, rr * 2, col, r=rr, lift=0.38)
    c.rect(ru, rv + rr * 0.45, 1.06, 0.012, WHITE, alpha=0.4, lift=0)
    c.ellipse(0.56, rv, rr * 0.55, rr, scale(col, 0.7), lift=0.1)
    for k in range(3):
        c.ellipse(0.56, rv, rr * (0.5 - k * 0.15), rr * (0.92 - k * 0.27), scale(col, 0.85 + 0.12 * k), lift=0.1, alpha=0.9)


@sprop("wellness_yoga_block", aspect=2.2, fill=0.37)
def yoga_blocks(c, color):
    """Two cork yoga blocks, one stacked on the other, with a strap."""
    rng = c.rng
    cork = (0.80, 0.60, 0.38)
    ao(c, 0.0, 0.0, 0.9, 0.16)
    for (u, v, w, h, sk) in ((-0.05, 0.02, 0.62, 0.18, 1.0), (0.04, 0.20, 0.50, 0.17, 1.06)):
        _box3d(c, u, v, w, h, 0.14, 0.10, scale(cork, sk), 0.68, 1.12)
        for _ in range(26):
            x = u + rng.uniform(-w / 2, w / 2 + 0.12)
            y = v + rng.uniform(0.0, h)
            c.ellipse(x, y, rng.uniform(0.004, 0.012), rng.uniform(0.003, 0.007), scale(cork, rng.choice((0.62, 1.25))), alpha=0.6, lift=0)
        c.rect(u, v + h * 0.5, w, 0.006, scale(cork, 0.6), alpha=0.5, lift=0)
    soft_disc(c, -0.2, 0.34, 0.2, 0.05, WHITE, 0.3, 1.2, add=True)


@sprop("wellness_bolster", aspect=4.2, fill=0.31)
def yoga_bolster(c, color):
    """Round bolster cushion lying on its side, with gathered ends."""
    col = color or (0.92, 0.84, 0.74)
    ao(c, 0.0, 0.0, 1.35, 0.22)
    c.rect(0.0, 0.16, 1.18, 0.30, col, r=0.15, lift=0.38)
    soft_disc(c, 0.1, 0.06, 0.55, 0.06, BLACK, 0.25, 1.3)
    soft_disc(c, -0.15, 0.25, 0.5, 0.05, WHITE, 0.4, 1.2, add=True)
    for k in range(7):
        x = -0.45 + k * 0.15
        c.line(x, 0.03, x + 0.015, 0.29, 0.003, scale(col, 0.78), 0.35)
    c.ellipse(0.55, 0.16, 0.10, 0.16, scale(col, 0.74), lift=0.1)                       # gathered end caps
    c.ellipse(0.55, 0.16, 0.05, 0.085, scale(col, 0.62), lift=0.1)
    c.ellipse(-0.57, 0.16, 0.09, 0.15, scale(col, 0.86), lift=0.1)
    c.ellipse(0.55, 0.16, 0.013, 0.02, scale(col, 0.4), lift=0)
    for a in range(0, 360, 40):
        c.line(0.55 + math.cos(math.radians(a)) * 0.015, 0.16 + math.sin(math.radians(a)) * 0.02, 0.55 + math.cos(math.radians(a)) * 0.092,
               0.16 + math.sin(math.radians(a)) * 0.15, 0.003, scale(col, 0.55), 0.55)
    c.rect(0.0, 0.21, 0.5, 0.013, scale(col, 0.7), r=0.006, lift=0, alpha=0.4)


@sprop("wellness_mat_roll", aspect=0.5, fill=1.0)
def yoga_roll(c, color):
    """Standing rolled yoga mat: a spiral top, tied with a strap."""
    col = color or (0.42, 0.62, 0.42)
    ao(c, 0.0, 0.0, 0.5, 0.10)
    craft.cylinder(c, 0.0, 0.05, 0.22, 0.86, scale(col, 1.18), scale(col, 0.58), scale(col, 0.9))
    for k in range(5):
        c.line(-0.21, 0.10 + k * 0.19, 0.21, 0.10 + k * 0.19 - 0.02, 0.003, scale(col, 0.7), 0.0)
    for k, r in enumerate((0.215, 0.17, 0.125, 0.085, 0.045)):
        c.ellipse(0.0, 0.91, r, r * TILT, scale(col, (0.80, 1.05, 0.78, 1.05, 0.75)[k]), lift=0.1)
    c.rect(0.0, 0.34, 0.45, 0.075, (0.92, 0.88, 0.80), lift=0.25, alpha=0.95)                 # strap
    c.rect(-0.04, 0.34, 0.12, 0.085, (0.4, 0.35, 0.3), r=0.01, lift=0.2)
    soft_disc(c, -0.14, 0.50, 0.05, 0.38, WHITE, 0.42, 1.1, add=True)


@niche("yoga", "Yoga studio", subjects=("wellness_yoga_mat",),
       strong=("yoga", "meditation", "asana", "pilates", "yoga studio", "yoga class", "yoga mat", "mindfulness", "pranayama",
               "योग", "ध्यान", "योगा", "आसन", "yog"),
       weak=("stretching", "flexibility", "zen", "breathing", "calm", "retreat"),
       accent="#6c9a6b", mood="light", group="wellness")
def yoga(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    floor = mix(P.surface, P.paper, 0.50) if not dark else scale(P.surface, 0.9)
    warm = (1.0, 0.86, 0.60)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        _blotches(S, 12, -1.0, 0.0, 3.0, 0.58, scale(P.wall_bot, 0.92), 0.25, 0.14, 0.3)
        # tall arched window with a soft bloom, hanging plant and a lantern
        S.glow(0.40, 0.25, 0.7, P.light, 0.55 * gl, 1.3)
        S.gradient_rect(0.22, 0.04, 0.58, 0.55, (0.72, 0.88, 0.98) if not dark else (0.25, 0.3, 0.45), (0.96, 0.98, 1.0) if not dark else (0.45, 0.5, 0.65), r=0.16)
        S.rect(0.40, 0.30, 0.008, 0.52, scale(P.paper, 1.0), lift=0.0)
        S.rect(0.40, 0.19, 0.36, 0.008, scale(P.paper, 1.0), lift=0.0)
        S.rect(0.40, 0.56, 0.42, 0.016, scale(P.paper, 1.0), r=0.004, lift=0.0)
        for k in range(7):                                                     # trailing plant on the wall
            S.ellipse(1.92 + (k % 3) * 0.04, 0.12 + k * 0.045, 0.07, 0.025, (0.22 + 0.02 * k, 0.5, 0.28), angle=-30 + 20 * (k % 2), lift=0.1)
        S.line(1.95, -0.1, 1.95, 0.10, 0.004, (0.5, 0.4, 0.3))
        S.rect(1.55, 0.30, 0.3, 0.38, scale(P.accent_light, 1.0), r=0.01, lift=0.0, alpha=0.5)      # a soft art print
        S.circle(1.55, 0.30, 0.09, scale(P.accent, 1.0), lift=0.0, alpha=0.6)
        S.glow(1.0, 0.45, 0.8, warm, 0.16 * gl, 1.5)
        S.floor(0.58, floor, scale(floor, 0.78))
    S.rect(1.0, 0.585, 7.0, 0.012, scale(floor, 0.62), lift=0.0)
    S.wood(-3.0, 0.58, 5.0, 1.3, floor, plank=0.09, grain=0.2)
    # window light falling over the floor
    S.soft(0.95, 0.80, 0.85, 0.16, warm, 0.36 * gl, 1.3, angle=-12, add=True)
    S.soft(1.35, 0.92, 0.5, 0.10, (1.0, 0.95, 0.8), 0.25 * gl, 1.3, angle=-12, add=True)
    S.put("wellness_plant", 0.58, 0.72, 0.34, color=(0.78, 0.66, 0.55), shadow_w=0.3, framed=False)
    S.put("wellness_mat_roll", 1.60, 0.86, 0.34, color=P.accent_dark, shadow_w=0.3)
    S.put("wellness_yoga_block", 1.42, 0.85, 0.14, shadow_w=0.3)
    S.put("wellness_yoga_mat", 1.02, 0.96, 0.22, color=P.accent, subject=True, shadow_w=0.9)
    S.put("wellness_bolster", 0.70, 0.99, 0.10, color=mix((0.92, 0.84, 0.74), P.accent_light, 0.25), shadow_w=0.5)
    S.put("wellness_candle", 1.35, 0.72, 0.15, shadow_w=0.15, framed=False)
    S.focus("detail", 1.10, 0.86)
    _near_leaves(S, 0.46, 1.10, (0.25, 0.5, 0.3))


# ====================================================================================== SPA
@sprop("wellness_stone_stack", aspect=0.85, fill=1.0)
def spa_stones(c, color):
    """A balanced stack of smooth river stones."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.14)
    stones = ((0.0, 0.10, 0.40, 0.095, (0.33, 0.31, 0.31)), (-0.02, 0.27, 0.31, 0.078, (0.62, 0.55, 0.47)), (0.02, 0.42, 0.24, 0.062, (0.29, 0.29, 0.31)),
              (-0.01, 0.54, 0.17, 0.05, (0.72, 0.66, 0.58)), (0.0, 0.63, 0.105, 0.04, (0.40, 0.37, 0.35)))
    for u, v, a, b, col in stones:
        c.ellipse(u + 0.01, v - b * 0.25, a * 0.98, b * 0.9, scale(col, 0.45), lift=0)
        c.ellipse(u, v, a, b * 1.05, scale(col, 0.78), lift=0.16)
        c.ellipse(u - a * 0.06, v + b * 0.2, a * 0.9, b * 0.84, col, lift=0.22)
        soft_disc(c, u + a * 0.35, v - b * 0.3, a * 0.55, b * 0.6, BLACK, 0.30, 1.3)
        gloss(c, u - a * 0.32, v + b * 0.45, a * 0.30, b * 0.22, 8, 0.55)
        for _ in range(9):
            x = u + rng.uniform(-a * 0.7, a * 0.7)
            y = v + rng.uniform(-b * 0.5, b * 0.7)
            c.ellipse(x, y, rng.uniform(0.003, 0.008), rng.uniform(0.002, 0.005), scale(col, rng.choice((0.55, 1.4))), alpha=0.45, lift=0)
        c.line(u - a * 0.5, v + b * 0.1, u + a * 0.2, v + b * 0.35, 0.003, scale(col, 1.5), 0.25)
    soft_disc(c, 0.0, 0.0, 0.3, 0.02, WHITE, 0.0, 1.0)


@sprop("wellness_towel_roll", aspect=4.2, fill=0.36)
def spa_towels(c, color):
    """Rolled and folded white towels: terry weave, spiral ends, a tied ribbon."""
    rng = c.rng
    col = color or (0.97, 0.95, 0.92)
    ao(c, 0.0, 0.0, 1.15, 0.2)
    # folded stack at the back
    for k, (w, sk) in enumerate(((0.80, 0.96), (0.78, 1.02), (0.76, 0.97), (0.74, 1.03))):
        c.rect(0.12, 0.05 + k * 0.065, w, 0.07, scale(col, sk), r=0.025, lift=0.15)
        c.rect(0.12 - w / 2 + 0.01, 0.05 + k * 0.065, 0.025, 0.065, scale(col, 0.84), r=0.01, lift=0)
        c.rect(0.12, 0.075 + k * 0.065, w - 0.04, 0.008, WHITE, alpha=0.7, lift=0)
    c.rect(0.12, 0.34, 0.5, 0.03, (0.40, 0.65, 0.58), r=0.01, lift=0.1, alpha=0.8)
    # rolls in front, the nearer one tied with a ribbon
    for u, v, r in ((-0.38, 0.0, 0.13), (0.50, 0.0, 0.12)):
        c.rect(u, v + r, 0.50, r * 2, col, r=r, lift=0.32)
        c.rect(u - 0.03, v + r * 1.6, 0.44, 0.012, WHITE, alpha=0.7, lift=0)
        c.ellipse(u + 0.25, v + r, r * 0.55, r, scale(col, 0.82), lift=0.1)
        for k, f in enumerate((0.8, 0.55, 0.3)):
            c.ellipse(u + 0.25, v + r, r * 0.55 * f, r * f, scale(col, 0.95 - 0.08 * k), lift=0.1, alpha=0.9)
        for k in range(5):
            x = u - 0.2 + k * 0.1
            c.line(x, v + 0.02, x + 0.01, v + r * 2 - 0.02, 0.003, scale(col, 0.88), 0.4)
        c.rect(u - 0.05, v + r, 0.04, r * 2.05, (0.5, 0.7, 0.64), lift=0.12)
    for _ in range(40):
        x, y = rng.uniform(-0.6, 0.7), rng.uniform(0.02, 0.28)
        c.ellipse(x, y, rng.uniform(0.004, 0.009), rng.uniform(0.002, 0.004), scale(col, rng.choice((0.9, 1.08))), alpha=0.5, lift=0)


@sprop("wellness_orchid", aspect=0.62, fill=1.0)
def spa_orchid(c, color):
    """Phalaenopsis orchid in a white pot: broad leaves, arching stem, white blossoms with magenta throats."""
    rng = c.rng
    ao(c, 0.0, 0.0, 0.55, 0.10)
    pot = (0.94, 0.93, 0.90)
    _hb(c, 0.0, 0.11, 0.34, 0.22, pot, r=0.04, kl=1.06, kr=0.7)
    c.ellipse(0.0, 0.22, 0.17, 0.17 * TILT, scale(pot, 0.7), lift=0)
    c.ellipse(0.0, 0.22, 0.14, 0.14 * TILT * 0.9, (0.38, 0.30, 0.22), lift=0)
    gloss(c, -0.09, 0.12, 0.02, 0.07, 0, 0.5)
    for ang, ln in ((20, 0.34), (160, 0.34), (45, 0.30), (135, 0.30), (100, 0.2)):
        craft.leaf(c, 0.0, 0.22, ln, ang, (0.20, 0.44, 0.24), 0.5)
    # arching stem
    pts = [(0.02, 0.24), (0.03, 0.45), (0.0, 0.62), (-0.06, 0.78), (-0.02, 0.9), (0.06, 0.95)]
    for p0, p1 in zip(pts, pts[1:]):
        c.line(p0[0], p0[1], p1[0], p1[1], 0.014, (0.30, 0.45, 0.24), 1.0)
    pink = color or (0.86, 0.22, 0.52)
    for k, (u, v, sz) in enumerate(((0.04, 0.50, 0.10), (-0.05, 0.62, 0.115), (0.07, 0.69, 0.11), (-0.07, 0.80, 0.105), (0.05, 0.86, 0.095),
                                    (-0.01, 0.95, 0.075))):
        for a, wd in ((0, 0.9), (72, 0.8), (144, 0.7), (216, 0.7), (288, 0.8)):
            ang = math.radians(a + 90 + k * 17)
            pu, pv = u + math.cos(ang) * sz * 0.5, v + math.sin(ang) * sz * 0.5
            c.ellipse(pu, pv, sz * 0.5 * wd * 0.8, sz * 0.36, (0.99, 0.97, 0.98), angle=math.degrees(ang), lift=0.12)
            c.ellipse(pu - 0.003, pv + 0.003, sz * 0.42 * wd * 0.7, sz * 0.27, (1.0, 1.0, 1.0), angle=math.degrees(ang), lift=0.0, alpha=0.6)
        c.ellipse(u, v, sz * 0.22, sz * 0.2, mix(pink, WHITE, 0.2), lift=0.1)
        c.ellipse(u, v - sz * 0.05, sz * 0.12, sz * 0.12, scale(pink, 0.8), lift=0.1)
        c.ellipse(u, v + sz * 0.02, sz * 0.05, sz * 0.05, (1.0, 0.85, 0.3), lift=0)
    soft_disc(c, 0.0, 0.7, 0.2, 0.3, WHITE, 0.10, 1.4, add=True)


@sprop("wellness_spa_bowl", aspect=2.0, fill=0.45)
def spa_bowl(c, color):
    """Ceramic bowl of water with floating petals and a frangipani."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.2)
    cer = (0.85, 0.88, 0.84)
    c.poly([(-0.46, 0.34), (0.46, 0.34), (0.26, 0.04), (-0.26, 0.04)], scale(cer, 0.7), lift=0.0)
    craft.hshade_box(c, 0.0, 0.2, 0.9, 0.2, cer, scale(cer, 0.5), 0.06)
    disc(c, 0.0, 0.34, 0.46, scale(cer, 1.05), 0.4, 0.05, rim=True)
    c.ellipse(0.0, 0.335, 0.41, 0.41 * 0.38, (0.52, 0.72, 0.72), lift=0.1)
    c.ellipse(0.02, 0.33, 0.36, 0.36 * 0.36, (0.70, 0.88, 0.86), lift=0.1)
    soft_disc(c, 0.0, 0.36, 0.34, 0.07, (0.3, 0.5, 0.52), 0.5, 1.2)
    soft_disc(c, -0.14, 0.31, 0.2, 0.035, WHITE, 0.5, 1.2, add=True)
    for _ in range(16):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.33
        c.ellipse(math.cos(a) * r, 0.335 + math.sin(a) * r * 0.36, rng.uniform(0.022, 0.04), rng.uniform(0.01, 0.017),
                  rng.choice([(0.98, 0.70, 0.78), (0.95, 0.55, 0.68), (0.99, 0.85, 0.88)]), angle=rng.uniform(-40, 40), lift=0.12)
    for k in range(5):
        a = math.radians(k * 72 + 20)
        c.ellipse(0.05 + math.cos(a) * 0.045, 0.37 + math.sin(a) * 0.022, 0.05, 0.022, (1.0, 0.98, 0.93), angle=math.degrees(a), lift=0.1)
    c.ellipse(0.05, 0.37, 0.018, 0.01, (1.0, 0.82, 0.3), lift=0)


@niche("spa", "Spa / wellness", subjects=("wellness_stone_stack",),
       strong=("spa", "massage", "aromatherapy", "wellness", "relax", "wellness center", "day spa", "massage therapy", "ayurveda",
               "स्पा", "मालिश", "मसाज", "वेलनेस", "malish", "spa center"),
       weak=("facial", "relaxation", "therapy", "essential oils", "sauna", "serenity"),
       accent="#7fb3a6", mood="warm", group="wellness")
def spa(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    warm = (1.0, 0.82, 0.55)
    teak = mix(P.surface, (0.55, 0.38, 0.24), 0.45)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # bamboo slats on the wall: vertical bars with soft node lines
        for i in range(30):
            u = -0.8 + i * 0.1
            S.rect(u, 0.30, 0.085, 0.76, scale(mix(P.wall_bot, (0.70, 0.62, 0.38), 0.45 if not dark else 0.25), 0.92 + 0.08 * (i % 3)), lift=0.0)
            S.rect(u + 0.045, 0.30, 0.006, 0.76, scale(P.wall_bot, 0.5), lift=0.0, alpha=0.5)
        for v in (0.12, 0.34, 0.54):
            S.rect(1.0, v, 5.0, 0.014, scale(P.wall_bot, 0.55), lift=0.0, alpha=0.5)
        S.glow(0.7, 0.25, 1.0, warm, 0.35 * gl, 1.5)
        S.glow(1.9, 0.30, 0.9, warm, 0.30 * gl, 1.5)
        S.bokeh(10, 0.0, 0.08, 2.0, 0.56, [(1.0, 0.85, 0.55), (1.0, 0.7, 0.4)], 0.015, 0.05, 0.35)
        S.floor(0.62, teak, scale(teak, 0.7))
    S.rect(1.0, 0.62, 7.0, 0.012, scale(teak, 0.45), lift=0.0)
    S.wood(-3.0, 0.62, 5.0, 1.3, teak, plank=0.075, grain=0.2)
    S.soft(1.1, 0.78, 1.0, 0.16, warm, 0.22 * gl, 1.5, add=True)
    S.put("wellness_orchid", 1.52, 0.80, 0.40, shadow_w=0.26)
    S.put("wellness_towel_roll", 0.80, 0.86, 0.16, color=mix((0.97, 0.95, 0.92), P.accent_light, 0.12), shadow_w=0.6)
    S.put("wellness_stone_stack", 1.12, 0.94, 0.40, subject=True, shadow_w=0.4)
    S.put("wellness_candle", 0.62, 0.74, 0.13, shadow_w=0.12, framed=False)
    S.put("wellness_candle", 1.38, 0.98, 0.15, color=(0.95, 0.90, 0.80), shadow_w=0.14)
    S.put("wellness_spa_bowl", 1.62, 0.98, 0.20, shadow_w=0.5)
    S.focus("detail", 1.20, 0.80)
    _near_leaves(S, 1.80, 1.10, (0.24, 0.5, 0.3), mirror=True)


# ====================================================================================== chairs (salon + barber)
def _chair(c, col, barber):
    """Hydraulic chair in side view (seat to the left, back to the right). barber=True: heavy tufted red leather with chrome arms and footrest."""
    chrome_l, chrome_d = (0.93, 0.94, 0.97), (0.40, 0.42, 0.48)
    ao(c, -0.05, 0.0, 1.0, 0.16)
    # base
    if barber:
        c.ellipse(0.0, 0.03, 0.34, 0.07, (0.12, 0.12, 0.14), lift=0.3)
        c.ellipse(0.0, 0.065, 0.30, 0.055, (0.30, 0.31, 0.35), lift=0.3)
        c.poly([(-0.17, 0.07), (0.17, 0.07), (0.09, 0.24), (-0.09, 0.24)], (0.15, 0.15, 0.17), lift=0.3)
        _metal(c, 0.0, 0.29, 0.11, 0.12, 1.0)
    else:
        for a in (200, 240, 270, 300, 340):
            x = 0.30 * math.cos(math.radians(a))
            c.line(0.0, 0.06, x, 0.03 + 0.03 * math.sin(math.radians(a)), 0.03, (0.55, 0.57, 0.62), 1.0)
            c.ellipse(x * 1.07, 0.025, 0.025, 0.02, (0.12, 0.12, 0.14), lift=0.2)
        c.ellipse(0.0, 0.06, 0.07, 0.03, (0.75, 0.77, 0.82), lift=0.3)
        _metal(c, 0.0, 0.20, 0.09, 0.28, 1.0)
        c.rect(0.0, 0.34, 0.16, 0.04, (0.20, 0.21, 0.24), r=0.015, lift=0.3)
    # footrest
    if barber:
        c.line(-0.06, 0.20, -0.46, 0.17, 0.045, scale(chrome_d, 1.2), 1.0)
        c.line(-0.06, 0.208, -0.45, 0.18, 0.012, WHITE, 0.6)
        c.poly([(-0.34, 0.205), (-0.64, 0.205), (-0.62, 0.17), (-0.36, 0.17)], (0.74, 0.76, 0.80), lift=0.25)
        c.rect(-0.49, 0.202, 0.26, 0.008, WHITE, alpha=0.6, lift=0)
    # seat and back
    sx0, sx1 = (-0.34, 0.30) if barber else (-0.30, 0.26)
    c.rect((sx0 + sx1) / 2, 0.41, sx1 - sx0, 0.125 if barber else 0.10, scale(col, 0.82), r=0.05, lift=0.22)
    c.rect((sx0 + sx1) / 2 - 0.01, 0.435, sx1 - sx0 - 0.04, 0.05, scale(col, 1.18), r=0.025, lift=0.0, alpha=0.7)
    bw = 0.19 if barber else 0.15
    top = 0.96 if barber else 0.94
    bx0, bx1 = 0.26, 0.34 if barber else 0.38
    c.poly([(bx0 - bw / 2, 0.40), (bx0 + bw / 2, 0.40), (bx1 + bw / 2 - 0.02, top - 0.07), (bx1 - bw / 2 + 0.02, top - 0.07)], scale(col, 0.82), lift=0.2)
    c.ellipse(bx1, top - 0.06, bw / 2 + 0.01, 0.075, scale(col, 0.9), lift=0.2)
    c.poly([(bx0 - bw / 2 + 0.03, 0.43), (bx0 - 0.005, 0.43), (bx1 - 0.005, top - 0.08), (bx1 - bw / 2 + 0.04, top - 0.08)], scale(col, 1.28), lift=0.0, alpha=0.55)
    if barber:
        for k in range(4):                                       # button tufting
            y = 0.50 + k * 0.11
            x = bx0 + (bx1 - bx0) * (y - 0.4) / (top - 0.47) - 0.01
            c.ellipse(x, y, 0.014, 0.014, scale(col, 0.45), lift=0.2)
            c.line(x - 0.05, y + 0.055, x, y, 0.003, scale(col, 0.55), 0.6)
            c.line(x + 0.05, y + 0.055, x, y, 0.003, scale(col, 0.55), 0.6)
        c.line(bx1 - 0.05, top - 0.14, bx1 + 0.0, top - 0.24, 0.0, WHITE, 0.0)
        c.rect(0.12, 0.60, 0.40, 0.04, scale(chrome_d, 1.2), r=0.018, lift=0.4)                  # chrome arm
        c.rect(0.10, 0.608, 0.36, 0.008, WHITE, alpha=0.7, lift=0)
        c.line(0.28, 0.58, 0.30, 0.44, 0.03, scale(chrome_d, 1.1), 1.0)
        c.rect(bx1 + 0.02, top + 0.04, 0.06, 0.05, scale(chrome_d, 1.2), lift=0.4)            # headrest stem
        c.rect(bx1 + 0.02, top + 0.10, 0.24, 0.085, scale(col, 0.9), r=0.04, lift=0.25)
        c.rect(bx1 + 0.0, top + 0.12, 0.2, 0.025, scale(col, 1.3), r=0.012, lift=0.0, alpha=0.6)
    else:
        c.rect(0.10, 0.56, 0.36, 0.03, scale(chrome_d, 1.2), r=0.014, lift=0.4)
        c.line(0.28, 0.55, 0.28, 0.44, 0.022, scale(chrome_d, 1.1), 1.0)
    soft_disc(c, 0.0, 0.38, 0.3, 0.05, BLACK, 0.25, 1.3)
    gloss(c, bx1 - 0.03, top - 0.25, 0.022, 0.2, 8, 0.65)
    gloss(c, -0.05, 0.455, 0.2, 0.014, 0, 0.55)
    soft_disc(c, 0.28, 0.4, 0.08, 0.3, BLACK, 0.20, 1.3)


@sprop("wellness_salon_chair", aspect=0.95, fill=1.05)
def salon_chair(c, color):
    _chair(c, color or (0.75, 0.22, 0.50), False)


@sprop("wellness_barber_chair", aspect=1.4, fill=1.12)
def barber_chair(c, color):
    _chair(c, color or (0.60, 0.10, 0.10), True)


# ====================================================================================== SALON
@sprop("wellness_salon_mirror", aspect=1.52, fill=0.82)
def salon_mirror(c, color):
    """Hollywood mirror: glass with glare, a dark frame and a ring of glowing bulbs."""
    rng = c.rng
    frame = color or (0.30, 0.16, 0.24)
    w, h = 1.26, 0.80
    c.rect(0.0, h / 2, w, h, scale(frame, 0.8), r=0.07, lift=0.2)
    c.rect(0.0, h / 2, w - 0.16, h - 0.16, scale(frame, 0.5), r=0.04, lift=0.0)
    gw, gh = w - 0.20, h - 0.20
    c.rect(0.0, h / 2, gw, gh, (0.74, 0.82, 0.88), r=0.03, lift=0.25)
    c.poly([(-gw / 2 + 0.02, 0.10 + 0.02), (-gw / 2 + 0.25, 0.10 + 0.02), (gw / 2 - 0.5, h - 0.10 - 0.02), (gw / 2 - 0.73, h - 0.10 - 0.02)],
           WHITE, lift=0.0, alpha=0.20)
    c.poly([(gw / 2 - 0.32, 0.12), (gw / 2 - 0.20, 0.12), (gw / 2 - 0.02, h - 0.12), (gw / 2 - 0.14, h - 0.12)], WHITE, lift=0.0, alpha=0.14)
    # a hint of the room reflected in the glass
    soft_disc(c, -0.3, 0.55, 0.3, 0.2, (0.95, 0.80, 0.85), 0.35, 1.2)
    soft_disc(c, 0.3, 0.30, 0.3, 0.14, (0.55, 0.62, 0.70), 0.3, 1.2)
    soft_disc(c, 0.28, 0.40, 0.14, 0.26, (0.78, 0.28, 0.52), 0.30, 1.1)          # soft reflection of the chair
    soft_disc(c, -0.38, 0.32, 0.16, 0.18, (1.0, 0.86, 0.62), 0.25, 1.2)
    # bulbs
    bulbs = []
    for i in range(9):
        bulbs.append((-w / 2 + 0.065 + i * (w - 0.13) / 8, h - 0.045))
        bulbs.append((-w / 2 + 0.065 + i * (w - 0.13) / 8, 0.045))
    for j in range(1, 5):
        bulbs.append((-w / 2 + 0.045, 0.045 + j * (h - 0.09) / 5))
        bulbs.append((w / 2 - 0.045, 0.045 + j * (h - 0.09) / 5))
    for x, y in bulbs:
        soft_disc(c, x, y, 0.065, 0.065, (1.0, 0.82, 0.5), 0.55, 1.5, add=True)
        c.ellipse(x, y, 0.021, 0.021, (1.0, 0.97, 0.88), lift=0.0)
        c.ellipse(x - 0.004, y + 0.004, 0.009, 0.009, WHITE, lift=0.0)
    c.rect(0.0, 0.0, 0.5, 0.025, scale(frame, 0.6), r=0.01, lift=0.2)


@sprop("wellness_salon_tools", aspect=3.2, fill=0.36)
def salon_tools(c, color):
    """Scissors, a comb and a round brush laid on the counter."""
    rng = c.rng
    rose = color or (0.80, 0.45, 0.50)
    ao(c, 0.0, 0.0, 1.8, 0.28, 0.3)
    # round brush
    c.line(-0.80, 0.07, -0.26, 0.10, 0.05, (0.20, 0.14, 0.12), 1.0)
    c.line(-0.80, 0.085, -0.28, 0.115, 0.012, WHITE, 0.4)
    c.ellipse(-0.18, 0.11, 0.17, 0.085, (0.26, 0.20, 0.18), lift=0.25)
    for k in range(34):
        a = rng.uniform(0, 6.28)
        c.line(-0.18 + math.cos(a) * 0.03, 0.11 + math.sin(a) * 0.015, -0.18 + math.cos(a) * 0.155, 0.11 + math.sin(a) * 0.08, 0.006,
               scale(rose, rng.uniform(0.5, 1.1)) if k % 2 else (0.14, 0.11, 0.10), 0.85)
    # comb
    c.poly([(0.05, 0.03), (0.60, 0.03), (0.58, 0.11), (0.07, 0.11)], (0.12, 0.12, 0.14), lift=0.3)
    for k in range(22):
        x = 0.10 + k * 0.022
        c.line(x, 0.032, x - 0.004, 0.0, 0.006, (0.10, 0.10, 0.12), 1.0)
    c.line(0.08, 0.105, 0.56, 0.105, 0.006, WHITE, 0.5)
    # scissors, open
    pu, pv = 0.80, 0.17
    for sgn in (1, -1):
        ex, ey = pu + 0.62, pv + sgn * 0.075
        c.poly([(pu - 0.05, pv - sgn * 0.006), (pu + 0.62, ey - sgn * 0.003), (pu + 0.62, ey + sgn * 0.004), (pu - 0.05, pv + sgn * 0.012)],
               (0.82, 0.85, 0.90), lift=0.4)
        c.line(pu, pv, pu + 0.60, pv + sgn * 0.073, 0.004, WHITE, 0.8)
        cx, cy = pu - 0.17, pv - sgn * 0.075
        craft.arc(c, cx, cy, 0.10, 0.052, 0, 360, 0.022, scale(rose, 0.8), 1.0, steps=14)
        craft.arc(c, cx, cy + 0.004, 0.10, 0.052, 20, 160, 0.008, scale(rose, 1.5), 0.8, steps=6)
        c.line(pu - 0.06, pv, cx + 0.09, cy + sgn * 0.018, 0.02, (0.78, 0.80, 0.85), 1.0)
    c.ellipse(pu, pv, 0.02, 0.016, (0.96, 0.8, 0.5), lift=0.3)


@sprop("wellness_hair_dryer", aspect=0.95, fill=1.0)
def salon_dryer(c, color):
    col = color or (0.75, 0.22, 0.50)
    ao(c, 0.0, 0.0, 0.4, 0.08)
    _hb(c, 0.1, 0.20, 0.17, 0.40, (0.16, 0.16, 0.18), r=0.05, kl=1.5, kr=0.7)              # handle
    c.rect(0.1, 0.03, 0.14, 0.04, (0.9, 0.9, 0.95), r=0.012, lift=0.3)
    c.rect(0.1, 0.32, 0.17, 0.02, col, lift=0.1)
    c.ellipse(0.0, 0.64, 0.42, 0.19, scale(col, 0.7), lift=0.1)
    c.rect(-0.04, 0.64, 0.74, 0.34, col, r=0.15, lift=0.32)
    c.ellipse(-0.46, 0.64, 0.07, 0.17, (0.14, 0.14, 0.16), lift=0.2)                          # nozzle
    c.rect(-0.38, 0.64, 0.16, 0.30, (0.20, 0.20, 0.23), r=0.04, lift=0.3)
    c.ellipse(-0.465, 0.64, 0.035, 0.12, (0.05, 0.05, 0.06), lift=0)
    for k in range(7):                                                                         # rear grille
        c.line(0.28, 0.52 + k * 0.035, 0.34, 0.52 + k * 0.035, 0.006, (0.12, 0.12, 0.14), 0.85)
    soft_disc(c, 0.28, 0.58, 0.1, 0.2, BLACK, 0.28, 1.3)
    gloss(c, -0.12, 0.74, 0.30, 0.035, 0, 0.7)
    craft.arc(c, 0.04, 0.0, 0.10, 0.05, 180, 330, 0.014, (0.10, 0.10, 0.12), 1.0, steps=6)


@sprop("wellness_product_bottles", aspect=1.1, fill=1.0)
def salon_bottles(c, color):
    rng = c.rng
    col = color or (0.75, 0.22, 0.50)
    ao(c, 0.0, 0.0, 0.8, 0.14)
    # tall shampoo bottle with a pump
    _hb(c, -0.22, 0.34, 0.24, 0.62, col, r=0.07, kl=1.3, kr=0.55)
    c.rect(-0.22, 0.38, 0.23, 0.26, (0.97, 0.96, 0.95), r=0.02, lift=0.0)
    c.rect(-0.22, 0.38, 0.23, 0.26, (1, 1, 1), r=0.02, lift=0.0, alpha=0.0)
    c.text("HAIR", -0.22, 0.42, 0.06, scale(col, 0.7), 0.2)
    c.line(-0.30, 0.34, -0.15, 0.34, 0.006, (0.6, 0.6, 0.65), 0.7)
    c.rect(-0.22, 0.69, 0.08, 0.06, (0.94, 0.94, 0.97), lift=0.2)
    c.rect(-0.22, 0.74, 0.012, 0.06, (0.9, 0.9, 0.93), lift=0.2)
    c.rect(-0.16, 0.79, 0.15, 0.035, (0.94, 0.94, 0.97), r=0.012, lift=0.3)
    gloss(c, -0.30, 0.46, 0.012, 0.18, 0, 0.7)
    # jar
    craft.cylinder(c, 0.10, 0.04, 0.17, 0.24, (1.0, 0.97, 0.95), (0.74, 0.72, 0.72), (0.98, 0.96, 0.94), lip=False)
    craft.cylinder(c, 0.10, 0.28, 0.18, 0.07, (0.92, 0.76, 0.45), (0.55, 0.40, 0.2), (0.96, 0.82, 0.55))
    c.rect(0.10, 0.15, 0.30, 0.08, scale(col, 1.1), lift=0.1)
    gloss(c, 0.0, 0.18, 0.012, 0.09, 0, 0.7)
    # spray bottle
    _hb(c, 0.40, 0.25, 0.17, 0.46, (0.97, 0.97, 0.98), r=0.05, kl=1.0, kr=0.62)
    c.rect(0.40, 0.2, 0.17, 0.2, scale(col, 0.95), lift=0.1, alpha=0.9)
    c.rect(0.40, 0.52, 0.09, 0.06, (0.2, 0.2, 0.24), lift=0.3)
    c.rect(0.37, 0.58, 0.16, 0.045, (0.2, 0.2, 0.24), r=0.02, lift=0.3)
    c.rect(0.31, 0.56, 0.05, 0.02, (0.2, 0.2, 0.24), lift=0.3)
    gloss(c, 0.35, 0.30, 0.01, 0.15, 0, 0.7)


@niche("salon", "Hair & beauty salon", subjects=("wellness_salon_mirror", "wellness_salon_chair"),
       strong=("salon", "hair salon", "hairdresser", "beauty parlour", "beauty parlor", "haircut", "hair stylist", "beauty salon",
               "hairstyle", "makeup artist", "सैलून", "ब्यूटी पार्लर", "बाल कटाई", "parlour", "beauty parlor", "hair cut"),
       weak=("hair", "styling", "manicure", "bridal makeup", "nails", "beauty"),
       accent="#c0397f", mood="warm", group="wellness")
def salon(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    warm = (1.0, 0.84, 0.58)
    wood = mix(P.surface, P.paper, 0.4) if not dark else scale(P.surface, 0.6)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.66)
        for i in range(12):                                                         # wall panel moulding
            S.rect(-0.2 + i * 0.28, 0.28, 0.20, 0.50, scale(P.wall_top, 0.97 if i % 2 else 1.02), r=0.006, lift=0.0)
        S.rect(1.0, 0.04, 6.0, 0.02, scale(P.wall_bot, 0.8), lift=0.0)
        S.pendant(0.75, -0.1, 0.13, warm, 0.10)
        S.pendant(1.8, -0.1, 0.11, warm, 0.10)
        S.glow(1.2, 0.30, 1.2, warm, 0.22 * gl, 1.5)
        S.bokeh(10, 0.0, 0.06, 2.0, 0.50, [(1.0, 0.85, 0.6), (1.0, 0.7, 0.55), (1.0, 0.6, 0.7)], 0.012, 0.04, 0.3)
        S.floor(0.66, scale(wood, 0.95), scale(wood, 0.6))
    # vanity: counter top edge, dark cabinet front, plank floor
    S.wood(-3.0, 0.66, 5.0, 1.3, wood, plank=0.11, grain=0.15)
    S.rect(1.0, 0.66, 7.0, 0.008, scale(wood, 0.5), lift=0.0)
    cab = scale(mix(P.accent_dark, P.wall_bot, 0.45), 0.9)
    S.rect(1.0, 0.82, 7.0, 0.26, cab, lift=0.0)
    S.rect(1.0, 0.695, 7.0, 0.045, mix(WHITE, P.accent_light, 0.1) if not dark else scale(P.accent_light, 0.4), lift=0.0)
    S.rect(1.0, 0.715, 7.0, 0.008, scale(cab, 0.4), lift=0.0)
    for u in (-0.2, 0.5, 1.2, 1.9, 2.6):
        S.rect(u, 0.82, 0.60, 0.20, scale(cab, 1.08), r=0.01, lift=0.0)
        S.rect(u, 0.78, 0.10, 0.012, (0.85, 0.75, 0.55), lift=0.0)
    S.soft(1.1, 0.94, 1.1, 0.15, warm, 0.18 * gl, 1.5, add=True)
    S.put("wellness_salon_mirror", 1.00, 0.69, 0.46, color=scale(mix(P.accent_dark, (0.2, 0.1, 0.15), 0.5), 1.0), subject=True, shadow=False)
    S.put("wellness_salon_tools", 1.00, 0.70, 0.13, shadow=False, framed=False)
    S.put("wellness_product_bottles", 0.64, 0.70, 0.17, color=P.accent, shadow=False)
    S.put("wellness_hair_dryer", 1.58, 0.70, 0.19, color=P.accent_light if not dark else P.accent, shadow=False)
    S.put("wellness_salon_chair", 1.35, 0.99, 0.50, color=P.accent, subject=True, shadow_w=0.5)
    S.focus("detail", 1.0, 0.70)
    # glow of the mirror bulbs onto the counter
    S.soft(1.0, 0.72, 0.6, 0.06, warm, 0.45 * gl, 1.3, add=True)
    _near_leaves(S, 0.46, 1.10, (0.28, 0.5, 0.34))


# ====================================================================================== BARBER
def _clip_v(pts, lo, hi):
    """Clip a polygon to lo <= v <= hi (Sutherland-Hodgman against two horizontal lines)."""
    def clip(poly, inside, edge):
        out = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            pin, qin = inside(p), inside(q)
            if pin:
                out.append(p)
            if pin != qin and q[1] != p[1]:
                t = (edge - p[1]) / (q[1] - p[1])
                out.append((p[0] + (q[0] - p[0]) * t, edge))
        return out
    a = clip(list(pts), lambda p: p[1] >= lo, lo)
    return clip(a, lambda p: p[1] <= hi, hi) if a else []


@sprop("wellness_barber_pole", aspect=0.30, fill=1.0)
def barber_pole(c, color):
    """Classic barber pole: glass cylinder with red / white / blue spiral stripes, chrome caps, soft inner glow."""
    r, v0, v1 = 0.13, 0.16, 0.86
    ao(c, 0.0, 0.0, 0.46, 0.08)
    # chrome base and wall bracket
    craft.cylinder(c, 0.0, 0.02, 0.19, 0.08, (0.92, 0.93, 0.96), (0.38, 0.40, 0.46), (0.88, 0.90, 0.94))
    craft.cylinder(c, 0.0, 0.10, 0.15, 0.06, (0.92, 0.93, 0.96), (0.38, 0.40, 0.46), (0.88, 0.90, 0.94), lip=False)
    c.rect(0.0, (v0 + v1) / 2, r * 2, v1 - v0, (0.96, 0.96, 0.97), lift=0.0)
    cols = [(0.82, 0.10, 0.12), (0.97, 0.97, 0.98), (0.14, 0.27, 0.66)]
    pitch, slant = 0.20, 0.17
    k = -2
    while k * pitch < v1 - v0 + pitch:
        y0 = v0 + k * pitch
        for j, col in enumerate(cols):
            if j == 1:
                continue
            ya = y0 + j * pitch / 3.0
            band = [(-r, ya), (r, ya + slant), (r, ya + slant + pitch / 3.2), (-r, ya + pitch / 3.2)]
            poly = _clip_v(band, v0, v1)
            if len(poly) >= 3:
                c.poly(poly, col, lift=0.0)
        k += 1
    craft.hshade_box(c, 0.0, (v0 + v1) / 2, r * 2, v1 - v0, (1, 1, 1), (0, 0, 0), 0.0, 0.0)
    soft_disc(c, r * 0.35, (v0 + v1) / 2, r * 0.7, (v1 - v0) / 2 * 0.98, BLACK, 0.36, 1.0)
    soft_disc(c, -r * 0.45, (v0 + v1) / 2, r * 0.22, (v1 - v0) / 2 * 0.94, WHITE, 0.55, 1.1, add=True)
    soft_disc(c, 0.0, (v0 + v1) / 2, r * 1.5, (v1 - v0) / 2 * 1.05, (1.0, 0.9, 0.7), 0.16, 1.5, add=True)
    for v, up in ((v0, False), (v1, True)):
        craft.cylinder(c, 0.0, v - (0.0 if up else 0.05), r * 1.12, 0.05, (0.94, 0.95, 0.98), (0.40, 0.42, 0.48), (0.90, 0.92, 0.96), lip=True)
    c.ellipse(0.0, v1 + 0.095, 0.095, 0.095, (0.82, 0.10, 0.12), lift=0.3)                       # red finial
    c.ellipse(0.0, v1 + 0.075, 0.06, 0.05, (0.9, 0.92, 0.96), lift=0.3)
    gloss(c, -0.04, v1 + 0.12, 0.03, 0.02, 20, 0.8)


@sprop("wellness_shave_kit", aspect=1.7, fill=0.55)
def barber_kit(c, color):
    """Shaving mug with foam and brush, an open straight razor and an aftershave bottle."""
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.26, 0.35)
    # razor lying open
    c.poly([(-0.78, 0.06), (-0.30, 0.095), (-0.31, 0.118), (-0.78, 0.082)], (0.20, 0.13, 0.09), lift=0.3)
    c.poly([(-0.30, 0.092), (0.10, 0.07), (0.10, 0.105), (-0.30, 0.118)], (0.86, 0.88, 0.92), lift=0.45)
    c.line(-0.29, 0.109, 0.09, 0.098, 0.006, WHITE, 0.9)
    c.ellipse(-0.30, 0.105, 0.016, 0.014, (0.8, 0.7, 0.4), lift=0.3)
    # mug with foam
    craft.cylinder(c, 0.28, 0.04, 0.17, 0.26, (0.96, 0.94, 0.88), (0.62, 0.58, 0.52), (0.92, 0.90, 0.85), lip=True)
    c.rect(0.28, 0.17, 0.33, 0.035, (0.62, 0.12, 0.12), lift=0.1)
    c.ellipse(0.28, 0.305, 0.15, 0.15 * TILT, (0.98, 0.98, 1.0), lift=0.1)
    for _ in range(18):
        a, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.13
        c.ellipse(0.28 + math.cos(a) * rr, 0.305 + math.sin(a) * rr * 0.4, rng.uniform(0.012, 0.028), rng.uniform(0.008, 0.015), WHITE, lift=0.1)
    c.ellipse(0.28, 0.33, 0.1, 0.04, (0.96, 0.97, 1.0), lift=0.1)
    gloss(c, 0.19, 0.17, 0.012, 0.09, 0, 0.6)
    # brush leaning in the mug
    c.line(0.30, 0.34, 0.42, 0.62, 0.045, (0.30, 0.18, 0.10), 1.0)
    c.line(0.295, 0.35, 0.415, 0.62, 0.01, (0.8, 0.6, 0.4), 0.55)
    c.ellipse(0.44, 0.66, 0.07, 0.065, (0.78, 0.66, 0.50), lift=0.15)
    for _ in range(30):
        a = rng.uniform(0, 6.28)
        c.line(0.44 + math.cos(a) * 0.02, 0.66 + math.sin(a) * 0.02, 0.44 + math.cos(a) * 0.075, 0.67 + math.sin(a) * 0.07, 0.006,
               (rng.uniform(0.55, 0.9), rng.uniform(0.45, 0.75), rng.uniform(0.3, 0.55)), 0.9)
    # aftershave bottle
    _hb(c, 0.70, 0.17, 0.17, 0.34, (0.20, 0.35, 0.50), r=0.03, kl=1.3, kr=0.55)
    c.rect(0.70, 0.18, 0.16, 0.14, (0.95, 0.9, 0.78), lift=0.0)
    c.rect(0.70, 0.18, 0.10, 0.012, (0.5, 0.4, 0.2), lift=0)
    c.rect(0.70, 0.365, 0.07, 0.05, (0.15, 0.15, 0.17), lift=0.3)
    gloss(c, 0.64, 0.20, 0.01, 0.12, 0, 0.7)


@niche("barber", "Barber shop", subjects=("wellness_barber_pole", "wellness_barber_chair"),
       strong=("barber", "barbershop", "barber shop", "shave", "beard", "beard trim", "gents salon", "men's grooming", "hair cutting saloon",
               "नाई", "नाई की दुकान", "दाढ़ी", "hajam", "nai ki dukan", "बार्बर"),
       weak=("grooming", "razor", "haircut for men", "fade", "moustache", "mens salon"),
       accent="#34495e", mood="dark", group="wellness")
def barber(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    warm = (1.0, 0.80, 0.50)
    wood = scale(mix((0.45, 0.27, 0.15), P.wall_bot, 0.3), 0.8 if dark else 1.05)
    tile = mix(P.paper, P.wall_top, 0.3) if not dark else scale(mix(P.accent_light, P.wall_top, 0.4), 0.50)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # dark wood panelling above, subway tiles below
        S.rect(1.0, 0.18, 6.0, 0.40, wood, lift=0.0)
        for i in range(34):
            S.rect(-0.8 + i * 0.1, 0.18, 0.004, 0.40, scale(wood, 0.55), lift=0.0, alpha=0.7)
        S.rect(1.0, 0.42, 6.0, 0.028, scale(wood, 1.3), lift=0.0)
        S.rect(1.0, 0.52, 6.0, 0.20, tile, lift=0.0)
        for k in range(4):
            S.rect(1.0, 0.44 + k * 0.05, 6.0, 0.003, scale(tile, 0.6), lift=0.0, alpha=0.7)
        for i in range(24):
            S.rect(-0.6 + i * 0.15 + (0.075 if i % 2 else 0), 0.50, 0.003, 0.05, scale(tile, 0.62), lift=0.0, alpha=0.7)
        # framed mirror on the wall and vintage pendant lamps
        S.rect(0.55, 0.22, 0.26, 0.34, (0.60, 0.72, 0.78) if not dark else (0.30, 0.38, 0.45), r=0.012, lift=0.0)
        S.rect(0.55, 0.22, 0.30, 0.38, scale(wood, 1.5), r=0.012, lift=0.0, alpha=0.9)
        S.rect(0.55, 0.22, 0.25, 0.33, (0.60, 0.72, 0.78) if not dark else (0.30, 0.38, 0.45), r=0.01, lift=0.1)
        S.pendant(1.30, -0.1, 0.16, warm, 0.08)
        S.pendant(1.90, -0.1, 0.12, warm, 0.08)
        S.pendant(0.90, -0.1, 0.10, warm, 0.07)
        S.glow(1.3, 0.20, 0.8, warm, 0.18 * gl, 1.5)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.40, [(1.0, 0.8, 0.5), (1.0, 0.65, 0.35)], 0.012, 0.04, 0.3)
        S.floor(0.60, scale(tile, 0.8), scale(tile, 0.5))
    # black and white checker floor in perspective
    _persp_checker(S, 0.60, 1.30, scale(tile, 0.95), scale(mix(P.ink, P.wall_bot, 0.4), 0.9), rows=6, cols=12, uc=1.2, vh=-0.9, span=8.0)
    S.rect(1.0, 0.60, 7.0, 0.01, scale(wood, 0.5), lift=0.0)
    S.soft(1.2, 0.85, 1.0, 0.2, warm, 0.20 * gl, 1.5, add=True)
    S.put("wellness_barber_chair", 0.98, 0.98, 0.62, color=(0.62, 0.10, 0.12) if not dark else (0.70, 0.14, 0.14), subject=True, shadow_w=0.9)
    S.put("wellness_barber_pole", 1.50, 0.99, 0.66, subject=True, shadow_w=0.3)
    S.put("wellness_shave_kit", 0.60, 0.72, 0.18, shadow=False, framed=False)
    S.focus("detail", 1.50, 0.62)
    S.soft(1.50, 0.62, 0.18, 0.36, warm, 0.10 * gl, 1.5, add=True)
    S.soft(0.50, 1.10, 0.30, 0.10, warm, 0.14 * gl, 1.3, add=True)


# ====================================================================================== PET CLINIC
def _fur(c, n, boxes, colors, ln=0.05, w=0.006, alpha=0.35, ang=-90):
    """Short seeded fur strokes scattered inside ellipses (u, v, a, b)."""
    rng = c.rng
    for _ in range(n):
        u0, v0, a, b = boxes[rng.randrange(len(boxes))]
        t = rng.uniform(0, 6.28)
        r = math.sqrt(rng.random())
        x, y = u0 + math.cos(t) * a * r, v0 + math.sin(t) * b * r
        an = math.radians(ang + rng.uniform(-35, 35))
        c.line(x, y, x + math.cos(an) * ln * rng.uniform(0.6, 1.2), y + math.sin(an) * ln * rng.uniform(0.6, 1.2), w, colors[rng.randrange(len(colors))], alpha)


@sprop("wellness_dog", aspect=0.78, fill=1.0)
def pet_dog(c, color):
    """A sitting golden retriever puppy facing us: haunches, chest, floppy ears, wet nose, collar with a tag."""
    fur = color or (0.82, 0.58, 0.30)
    dk, lt = scale(fur, 0.62), mix(fur, (1.0, 0.94, 0.82), 0.55)
    ao(c, 0.0, 0.0, 0.8, 0.14, 0.5)
    # tail wagging behind
    c.line(0.26, 0.12, 0.44, 0.26, 0.075, scale(fur, 0.85), 1.0)
    c.line(0.44, 0.26, 0.46, 0.38, 0.06, scale(fur, 0.9), 1.0)
    # haunches and hind paws
    for sg in (-1, 1):
        c.ellipse(sg * 0.25, 0.20, 0.17, 0.18, scale(fur, 0.8), lift=0.2)
        c.ellipse(sg * 0.22, 0.035, 0.08, 0.04, lt, lift=0.15)
        c.ellipse(sg * 0.22, 0.016, 0.085, 0.026, scale(lt, 0.7), lift=0, alpha=0.7)
    # chest and belly
    c.ellipse(0.0, 0.40, 0.27, 0.34, fur, lift=0.22)
    # front legs and paws
    for sg in (-1, 1):
        c.rect(sg * 0.105, 0.20, 0.13, 0.40, scale(fur, 0.96), r=0.06, lift=0.2)
        c.ellipse(sg * 0.105, 0.035, 0.085, 0.05, lt, lift=0.2)
        for k in (-1, 0, 1):
            c.line(sg * 0.105 + k * 0.03, 0.045, sg * 0.105 + k * 0.03, 0.02, 0.004, scale(lt, 0.6), 0.7)
    c.ellipse(0.0, 0.42, 0.15, 0.26, lt, lift=0.2, alpha=0.95)                           # chest patch
    soft_disc(c, 0.17, 0.30, 0.12, 0.28, BLACK, 0.16, 1.3)
    soft_disc(c, -0.14, 0.52, 0.12, 0.2, WHITE, 0.18, 1.2, add=True)
    soft_disc(c, 0.0, 0.64, 0.2, 0.09, BLACK, 0.26, 1.3)                                  # shadow of the head on the chest
    _fur(c, 55, [(0.0, 0.40, 0.25, 0.30), (-0.25, 0.20, 0.15, 0.15), (0.25, 0.20, 0.15, 0.15)], [dk, scale(fur, 1.25), lt], 0.05, 0.005, 0.32)
    # collar and tag
    c.ellipse(0.0, 0.645, 0.145, 0.045, (0.80, 0.20, 0.25), lift=0.25)
    c.ellipse(0.0, 0.655, 0.14, 0.032, scale((0.80, 0.20, 0.25), 1.2), lift=0.0, alpha=0.6)
    c.ellipse(0.02, 0.585, 0.032, 0.032, (0.98, 0.80, 0.30), lift=0.3)
    gloss(c, 0.012, 0.595, 0.012, 0.008, 20, 0.9)
    # head
    c.ellipse(0.0, 0.80, 0.215, 0.19, fur, lift=0.25)
    soft_disc(c, 0.13, 0.76, 0.10, 0.14, BLACK, 0.2, 1.3)
    soft_disc(c, -0.08, 0.88, 0.14, 0.08, WHITE, 0.3, 1.2, add=True)
    c.ellipse(0.0, 0.73, 0.12, 0.095, lt, lift=0.2)                                      # muzzle
    c.ellipse(0.0, 0.67, 0.07, 0.04, (0.92, 0.45, 0.50), lift=0.15)                      # tongue
    c.line(0.0, 0.74, 0.0, 0.70, 0.005, scale(dk, 0.6), 0.8)
    craft.arc(c, -0.045, 0.705, 0.045, 0.03, 200, 350, 0.006, scale(dk, 0.6), 0.9, steps=4)
    craft.arc(c, 0.045, 0.705, 0.045, 0.03, 190, 340, 0.006, scale(dk, 0.6), 0.9, steps=4)
    c.ellipse(0.0, 0.762, 0.048, 0.032, (0.10, 0.08, 0.08), lift=0.3)                    # nose
    gloss(c, -0.015, 0.772, 0.018, 0.009, 10, 0.9)
    for sg in (-1, 1):
        c.ellipse(sg * 0.085, 0.835, 0.037, 0.034, (0.97, 0.95, 0.9), lift=0.0)           # eyes
        c.ellipse(sg * 0.085, 0.835, 0.03, 0.03, (0.20, 0.11, 0.06), lift=0.1)
        c.ellipse(sg * 0.085, 0.835, 0.016, 0.016, (0.03, 0.02, 0.02), lift=0)
        c.ellipse(sg * 0.085 - 0.01, 0.845, 0.009, 0.009, WHITE, lift=0)
        c.ellipse(sg * 0.075, 0.875, 0.04, 0.014, dk, angle=sg * -12, lift=0, alpha=0.55)
        # floppy ears
        c.ellipse(sg * 0.215, 0.80, 0.075, 0.165, dk, angle=sg * 14, lift=0.25)
        c.ellipse(sg * 0.205, 0.82, 0.04, 0.10, scale(dk, 1.3), angle=sg * 14, lift=0, alpha=0.5)
    _fur(c, 18, [(0.0, 0.82, 0.18, 0.14)], [scale(fur, 1.3), dk], 0.04, 0.005, 0.3)


@sprop("wellness_cat", aspect=0.62, fill=1.0)
def pet_cat(c, color):
    """A sitting grey tabby cat with green eyes, pink nose, striped coat, whiskers and a curled tail."""
    fur = color or (0.64, 0.64, 0.69)
    dk, lt = scale(fur, 0.48), (0.94, 0.92, 0.90)
    ao(c, 0.0, 0.0, 0.7, 0.12, 0.5)
    # tail curled around the front of the paws
    craft.arc(c, 0.0, 0.05, 0.30, 0.07, 195, 345, 0.075, scale(fur, 0.85), 1.0, steps=8)
    craft.arc(c, 0.0, 0.05, 0.30, 0.07, 250, 335, 0.075, dk, 0.55, steps=5)
    # body: pear shape with haunches
    for sg in (-1, 1):
        c.ellipse(sg * 0.20, 0.17, 0.15, 0.16, scale(fur, 0.85), lift=0.2)
    c.ellipse(0.0, 0.33, 0.23, 0.31, fur, lift=0.22)
    for sg in (-1, 1):
        c.rect(sg * 0.075, 0.18, 0.10, 0.34, scale(fur, 0.96), r=0.05, lift=0.2)
        c.ellipse(sg * 0.075, 0.035, 0.065, 0.04, lt, lift=0.2)
    c.ellipse(0.0, 0.36, 0.12, 0.22, lt, lift=0.2, alpha=0.95)
    soft_disc(c, 0.15, 0.28, 0.1, 0.25, BLACK, 0.18, 1.3)
    soft_disc(c, -0.12, 0.46, 0.10, 0.16, WHITE, 0.2, 1.2, add=True)
    for k in range(6):                                                              # tabby stripes on the flanks
        y = 0.16 + k * 0.045
        craft.arc(c, 0.0, y, 0.22 - k * 0.003, 0.05, 20, 160, 0.012, dk, 0.45, steps=5)
    for sg in (-1, 1):
        for k in range(3):
            c.line(sg * 0.2, 0.08 + k * 0.05, sg * 0.13, 0.10 + k * 0.05, 0.012, dk, 0.5)
    _fur(c, 30, [(0.0, 0.33, 0.2, 0.28)], [dk, scale(fur, 1.2)], 0.04, 0.004, 0.28)
    # head with pointed ears
    for sg in (-1, 1):
        c.poly([(sg * 0.07, 0.80), (sg * 0.19, 0.78), (sg * 0.17, 0.97)], scale(fur, 0.9), lift=0.2)
        c.poly([(sg * 0.095, 0.81), (sg * 0.172, 0.795), (sg * 0.162, 0.925)], (0.92, 0.62, 0.66), lift=0.1)
    c.ellipse(0.0, 0.72, 0.205, 0.17, fur, lift=0.25)
    soft_disc(c, 0.11, 0.70, 0.1, 0.14, BLACK, 0.18, 1.3)
    soft_disc(c, -0.08, 0.80, 0.14, 0.08, WHITE, 0.3, 1.2, add=True)
    for k in (-1, 0, 1):                                                           # forehead stripes
        c.line(k * 0.035, 0.84, k * 0.04, 0.78, 0.012, dk, 0.55)
    c.ellipse(0.0, 0.665, 0.085, 0.055, lt, lift=0.15)                              # muzzle
    c.poly([(-0.025, 0.69), (0.025, 0.69), (0.0, 0.665)], (0.90, 0.50, 0.55), lift=0.1)
    c.line(0.0, 0.665, 0.0, 0.645, 0.005, scale(dk, 0.7), 0.8)
    craft.arc(c, -0.025, 0.645, 0.025, 0.018, 190, 350, 0.005, scale(dk, 0.7), 0.9, steps=4)
    craft.arc(c, 0.025, 0.645, 0.025, 0.018, 190, 350, 0.005, scale(dk, 0.7), 0.9, steps=4)
    for sg in (-1, 1):
        c.ellipse(sg * 0.075, 0.74, 0.050, 0.042, (0.72, 0.84, 0.35), lift=0.1, angle=sg * 12)
        c.ellipse(sg * 0.075, 0.74, 0.050, 0.042, (0.30, 0.62, 0.30), lift=0.0, alpha=0.4, angle=sg * 12)
        c.ellipse(sg * 0.075, 0.74, 0.012, 0.036, (0.03, 0.03, 0.03), lift=0)
        c.ellipse(sg * 0.065, 0.752, 0.01, 0.01, WHITE, lift=0)
        c.line(sg * 0.12, 0.74, sg * 0.165, 0.76, 0.01, dk, 0.45)
        for k in range(3):                                                         # whiskers
            c.line(sg * 0.07, 0.655 - k * 0.012, sg * (0.24 + k * 0.01), 0.675 - k * 0.04, 0.0035, WHITE, 0.8)
    # collar with a little bell
    c.ellipse(0.0, 0.585, 0.115, 0.034, (0.15, 0.55, 0.75), lift=0.25)
    c.ellipse(0.0, 0.54, 0.024, 0.024, (0.98, 0.80, 0.30), lift=0.3)
    gloss(c, -0.006, 0.548, 0.01, 0.006, 20, 0.9)


@sprop("wellness_vet_table", aspect=2.35, fill=0.76)
def pet_table(c, color):
    """Stainless-steel examination table: brushed top with a rolled edge, pedestal and base."""
    rng = c.rng
    st = (0.80, 0.82, 0.86)
    ao(c, 0.0, 0.0, 1.5, 0.28, 0.45)
    c.ellipse(0.0, 0.03, 0.55, 0.075, scale(st, 0.45), lift=0.2)
    c.ellipse(0.0, 0.05, 0.48, 0.06, scale(st, 0.9), lift=0.3)
    _metal(c, 0.0, 0.32, 0.28, 0.52, 1.0)
    c.rect(0.0, 0.57, 0.52, 0.05, scale(st, 0.5), r=0.02, lift=0.3)
    # tabletop: front rolled edge, top face in perspective
    c.rect(0.0, 0.62, 1.84, 0.075, scale(st, 0.86), r=0.03, lift=0.3)
    c.rect(0.0, 0.635, 1.80, 0.012, WHITE, alpha=0.7, lift=0)
    c.poly([(-0.92, 0.655), (0.92, 0.655), (0.78, 0.76), (-0.78, 0.76)], scale(st, 1.04), lift=0.12)
    c.poly([(-0.92, 0.655), (0.92, 0.655), (0.90, 0.67), (-0.90, 0.67)], WHITE, lift=0.0, alpha=0.5)
    soft_disc(c, -0.3, 0.71, 0.55, 0.035, WHITE, 0.65, 1.2, add=True)
    soft_disc(c, 0.55, 0.70, 0.30, 0.03, (0.55, 0.65, 0.8), 0.25, 1.2)
    for _ in range(26):                                                              # brushed-steel streaks
        y = rng.uniform(0.665, 0.75)
        x = rng.uniform(-0.7, 0.4)
        c.line(x, y, x + rng.uniform(0.1, 0.4), y, 0.0025, WHITE if rng.random() < 0.5 else scale(st, 0.7), 0.25)


@sprop("wellness_treat_jar", aspect=0.62, fill=1.0)
def pet_jar(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.6, 0.10)
    craft.hshade_box(c, 0.0, 0.34, 0.5, 0.62, (0.88, 0.94, 0.98), (0.60, 0.70, 0.78), 0.1, 0.5)
    for k in range(8):                                                               # bone-shaped biscuits
        u, v = rng.uniform(-0.15, 0.15), 0.10 + k * 0.055
        a = math.radians(rng.uniform(-25, 25))
        dx, dy = math.cos(a) * 0.09, math.sin(a) * 0.09
        c.line(u - dx, v - dy, u + dx, v + dy, 0.035, (0.85, 0.62, 0.34), 1.0)
        c.ellipse(u - dx, v - dy, 0.03, 0.03, (0.88, 0.66, 0.38), lift=0.15)
        c.ellipse(u + dx, v + dy, 0.03, 0.03, (0.88, 0.66, 0.38), lift=0.15)
    craft.hshade_box(c, 0.0, 0.34, 0.5, 0.62, (1.0, 1.0, 1.0), (0.7, 0.8, 0.9), 0.1, 0.25)
    gloss(c, -0.17, 0.38, 0.014, 0.22, 0, 0.7)
    craft.cylinder(c, 0.0, 0.62, 0.27, 0.08, (0.88, 0.25, 0.25), (0.52, 0.10, 0.12), (0.92, 0.35, 0.34))
    c.ellipse(0.0, 0.43, 0.06, 0.06, (0.98, 0.95, 0.9), lift=0, alpha=0.9)
    for k in range(4):
        a = math.radians(k * 90 + 20)
        c.ellipse(math.cos(a) * 0.045, 0.40 + math.sin(a) * 0.028, 0.018, 0.016, (0.4, 0.25, 0.2), lift=0)
    c.ellipse(0.0, 0.395, 0.032, 0.024, (0.4, 0.25, 0.2), lift=0)


@niche("pet-clinic", "Veterinary clinic", subjects=("wellness_dog", "wellness_cat"),
       strong=("vet", "veterinary", "pet clinic", "animal doctor", "veterinarian", "pet care", "animal hospital", "dog clinic",
               "pashu chikitsak", "पशु चिकित्सक", "पशु अस्पताल", "पशु चिकित्सा", "pet doctor", "vet clinic"),
       weak=("pet", "dog", "cat", "puppy", "kitten", "animal"),
       accent="#3498db", mood="light", group="wellness")
def pet_clinic(S):
    P = S.pal
    dark = _is_dark(P)
    gl = 1.8 if dark else 1.0
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        S.rect(1.0, 0.52, 7.0, 0.22, mix(P.wall_bot, P.accent_light, 0.5), lift=0.0)           # soft accent wainscot
        S.rect(1.0, 0.41, 7.0, 0.012, scale(P.paper, 1.0), lift=0.0)
        S.window(0.38, 0.22, 0.34, 0.30, bars=False)
        for i in range(7):
            S.rect(0.38, 0.09 + i * 0.043, 0.34, 0.015, scale(mix(P.paper, P.light, 0.4), 0.92), lift=0.0)
        S.glow(0.38, 0.22, 0.7, P.light, 0.3 * gl, 1.5)
        # paw-print poster and a wall cabinet
        S.rect(1.60, 0.22, 0.30, 0.36, scale(P.paper, 1.0), r=0.008, lift=0.0)
        S.ellipse(1.60, 0.27, 0.05, 0.042, P.accent, lift=0.0)
        for k, (dx, dy) in enumerate(((-0.07, 0.17), (-0.03, 0.12), (0.03, 0.12), (0.07, 0.17))):
            S.ellipse(1.60 + dx, 0.22 - dy + 0.12, 0.016, 0.02, P.accent, lift=0.0)
        S.rect(2.10, 0.22, 0.34, 0.30, mix(P.accent, P.paper, 0.78), r=0.01, lift=0.04)
        S.rect(2.10, 0.22, 0.004, 0.30, scale(P.accent_light, 0.6), lift=0.0)
        S.pendant(1.1, -0.1, 0.10, (1.0, 0.96, 0.88), 0.07)
        S.pendant(1.8, -0.1, 0.08, (1.0, 0.96, 0.88), 0.07)
        S.floor(0.62, _tone(P, 1.05, 0.15), _tone(P, 0.7, 0.15))
    S.rect(1.0, 0.62, 7.0, 0.01, scale(_tone(P, 0.7, 0.1), 0.8), lift=0.0)
    _persp_lines(S, 0.63, 1.3, scale(_tone(P, 0.55, 0.1), 0.7), 0.45, rows=6, cols=18, uc=1.1)
    S.soft(1.1, 0.88, 1.0, 0.2, P.light, 0.22 * gl, 1.5, add=True)
    th = 0.46
    tu, tv = 1.08, 0.98
    top = tv - th * 0.70 / 0.76 + 0.012
    S.put("wellness_vet_table", tu, tv, th, shadow_w=1.0)
    S.put("wellness_dog", tu - 0.23, top, 0.36, subject=True, shadow_w=0.26, shadow_alpha=0.22)
    S.put("wellness_cat", tu + 0.19, top, 0.30, subject=True, shadow_w=0.2, shadow_alpha=0.22)
    S.put("wellness_treat_jar", tu + 0.42, top + 0.004, 0.12, shadow_w=0.1, shadow_alpha=0.2)
    S.focus("detail", tu - 0.02, top - 0.12)
    S.soft(tu, top - 0.12, 0.5, 0.25, P.light, 0.12 * gl, 1.5, add=True)
    _near_leaves(S, 0.46, 1.10, (0.24, 0.5, 0.32))
