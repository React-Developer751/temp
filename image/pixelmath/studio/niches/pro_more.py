"""More professional-services niches: architect, insurance, consulting, recruitment, coworking, astrology, visa, ngo.

Props are prefixed ``pro_``. Shared building blocks come from digital_edu (``_crect`` fast rectangles, ``_G`` rotated frame,
``box3d``, ``_Flat`` flat sheet on a desk); everything else is drawn here with the stage / craft helpers.
"""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, gloss, soft_disc, speckle
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, mix, scale
from .digital_edu import _Flat, _G, _area, _bars, _crect, _donut, _fill_quad, _laptop, _srect, _textbars, _ui_card, box3d, sorted_quad
from .retail_fashion import _chaikin, _fillpoly, _hpoly, _leaf, _spoly

KRAFT = (0.78, 0.62, 0.42)
PAPER = (0.97, 0.96, 0.93)
STEELC = (0.70, 0.73, 0.78)
BRASS = (0.80, 0.57, 0.21)
GREEN = (0.27, 0.55, 0.30)


def _acc(color, name="accent", default=(0.35, 0.45, 0.55)):
    """Props get the palette through ``color=S.pal``; plain tuples (or None) fall back to the default."""
    if color is None or isinstance(color, tuple):
        return color or default
    return getattr(color, name, default)


def _sky(P):
    return ((0.07, 0.09, 0.20), (0.22, 0.26, 0.44)) if P.mood == "dark" else ((0.55, 0.78, 0.96), (0.89, 0.95, 1.0))


def _lamp_glow_mood(P, light, dark):
    return dark if P.mood == "dark" else light


def _tube(c, u, v, w, h, col, ang=0.0, hi=0.3):
    """A paper roll / pencil body seen from the side: rotated rectangle with lit top edge and a dark underside."""
    g = _G(c, u, v, ang)
    g.rect(0.0, 0.0, w, h, col, r=h * 0.5, lift=0.30)
    g.rect(0.0, h * 0.20, w * 0.96, h * 0.22, mix(col, WHITE, hi), r=h * 0.1, alpha=0.55)
    g.rect(0.0, -h * 0.30, w * 0.96, h * 0.3, scale(col, 0.7), r=h * 0.1, alpha=0.5)
    return g


# ====================================================================================================== ARCHITECT
def _model_block(c, u, v, w, h, d, floors, cols, front=(0.96, 0.96, 0.95), glass=(0.50, 0.60, 0.70), lit=0.0):
    box3d(c, u, v, w, h, d, front, mix(front, WHITE, 0.4), scale(front, 0.76), lift=0.05, dx=0.55, dy=0.42)
    ox, oy = d * 0.55, d * 0.42
    x0, x1 = u - w / 2, u + w / 2
    fh = h / floors
    cw = w / cols
    for i in range(floors):
        vv = v + fh * (i + 0.5)
        for j in range(cols):
            on = lit and c.rng.random() < lit
            _crect(c, x0 + cw * (j + 0.5), vv, cw * 0.62, fh * 0.56, (1.0, 0.86, 0.52) if on else glass, r=0.002, lift=0.0 if on else 0.25, alpha=0.95 if on else 0.9)
    c.line(x0, v + h * 0.98, x1, v + h * 0.98, 0.003, scale(front, 0.8), 0.7)
    for i in range(1, floors):                                           # floor plates run round the side too
        vv = v + fh * i
        c.line(x1, vv, x1 + ox, vv + oy, 0.0025, scale(front, 0.55), 0.55)
    for k in range(1, 3):
        t = k / 3.0
        c.line(x1 + ox * t, v + oy * t, x1 + ox * t, v + h + oy * t, 0.0025, scale(front, 0.55), 0.35)


@sprop("pro_arch_model", aspect=2.0, fill=0.96)
def arch_model(c, color):
    rng = c.rng
    lit = 0.45 if getattr(color, "mood", None) == "dark" else 0.0
    ao(c, 0.12, 0.0, 1.7, 0.42)
    bu, bw, bd = -0.10, 1.40, 0.62
    ox, oy = bd * 0.55, bd * 0.42

    def pos(xf, t):
        return (bu - bw / 2 + xf * bw + t * ox, 0.045 + t * oy)
    # presentation base: foam board, then a green lawn and a pale road
    box3d(c, bu, 0.0, bw, 0.045, bd, (0.92, 0.90, 0.86), (0.97, 0.96, 0.93), (0.70, 0.68, 0.64), lift=0.04)
    c.poly([pos(0.04, 0.05), pos(0.96, 0.05), pos(0.96, 0.95), pos(0.04, 0.95)], (0.62, 0.74, 0.58), lift=0.0, alpha=0.9)
    c.poly([pos(0.04, 0.05), pos(0.96, 0.05), pos(0.96, 0.22), pos(0.04, 0.22)], (0.86, 0.85, 0.82), lift=0.0)
    for k in range(9):
        a, b = pos(0.08 + k * 0.105, 0.135), pos(0.14 + k * 0.105, 0.135)
        c.line(a[0], a[1], b[0], b[1], 0.005, (0.97, 0.97, 0.95), 0.9)
    soft_disc(c, pos(0.68, 0.55)[0] + 0.12, pos(0.68, 0.55)[1] + 0.02, 0.42, 0.10, BLACK, 0.30, 1.4)
    # buildings back to front
    u, v = pos(0.32, 0.60)
    _model_block(c, u, v, 0.58, 0.20, 0.22, 2, 7, glass=(0.58, 0.66, 0.74), lit=lit)
    u, v = pos(0.70, 0.52)
    _model_block(c, u, v, 0.32, 0.62, 0.26, 10, 4, lit=lit)
    c.rect(u + 0.02, v + 0.62 + 0.14, 0.012, 0.07, (0.80, 0.80, 0.82), lift=0.0)           # mast
    u, v = pos(0.26, 0.28)
    _model_block(c, u, v, 0.50, 0.17, 0.20, 2, 6, lit=lit)
    u, v = pos(0.86, 0.30)
    _model_block(c, u, v, 0.20, 0.10, 0.16, 1, 3, lit=lit)
    # model trees (foam spheres on sticks)
    for xf, t, r in ((0.08, 0.40, 0.045), (0.10, 0.75, 0.04), (0.50, 0.30, 0.04), (0.92, 0.80, 0.04), (0.58, 0.82, 0.045), (0.05, 0.62, 0.035)):
        tu, tv = pos(xf, t)
        c.line(tu, tv, tu, tv + r * 1.6, 0.008, (0.55, 0.42, 0.30), 1.0)
        c.ellipse(tu, tv + r * 2.2, r, r * 1.05, (0.40, 0.62, 0.38), lift=0.18)
        c.ellipse(tu - r * 0.3, tv + r * 2.5, r * 0.4, r * 0.3, (0.75, 0.90, 0.70), lift=0.0, alpha=0.6)
        c.ellipse(tu + r * 0.45, tv + r * 1.9, r * 0.7, r * 0.5, scale((0.40, 0.62, 0.38), 0.6), lift=0.0, alpha=0.5)
    for _ in range(5):                                                   # parked cars
        a = pos(rng.uniform(0.1, 0.9), 0.135)
        c.rect(a[0], a[1] + 0.008, 0.045, 0.016, rng.choice([(0.8, 0.82, 0.86), (0.35, 0.40, 0.48)]), r=0.005, lift=0.2)
    gloss(c, -0.4, 0.60, 0.16, 0.12, 20, 0.22)


def _sheet_plan(c, f, bp, rng):
    """A blueprint drawn on a flat sheet: grid, walls with openings, dimension lines, title block."""
    line = (0.86, 0.93, 1.0)
    f.tint(0, 0, 1, 1, bp, 1.0)
    f.tint(0.0, 0.5, 1.0, 1.0, WHITE, 0.05)
    for i in range(1, 12):
        f.line(i / 12.0, 0.03, i / 12.0, 0.97, 0.0025, line, 0.14)
    for j in range(1, 6):
        f.line(0.02, j / 6.0, 0.98, j / 6.0, 0.0025, line, 0.14)
    walls = [(0.10, 0.18, 0.62, 0.18), (0.62, 0.18, 0.62, 0.82), (0.62, 0.82, 0.10, 0.82), (0.10, 0.82, 0.10, 0.18),
             (0.36, 0.18, 0.36, 0.52), (0.10, 0.52, 0.36, 0.52), (0.36, 0.66, 0.62, 0.66), (0.48, 0.66, 0.48, 0.82)]
    for a0, b0, a1, b1 in walls:
        f.line(a0, b0, a1, b1, 0.011, line, 0.95)
    for a0, b0, a1, b1 in ((0.20, 0.18, 0.28, 0.18), (0.62, 0.40, 0.62, 0.50), (0.36, 0.56, 0.36, 0.62), (0.52, 0.82, 0.58, 0.82)):
        f.line(a0, b0, a1, b1, 0.014, bp, 1.0)                              # openings
    for k in range(9):                                                      # a spiral stair
        a = 0.52 + 0.035 * math.cos(k * 0.7)
        f.line(0.20 + k * 0.012, 0.60, 0.20 + k * 0.012, 0.76, 0.003, line, 0.7)
    f.line(0.10, 0.08, 0.62, 0.08, 0.004, line, 0.8)                        # dimension line
    for a in (0.10, 0.62):
        f.line(a, 0.05, a, 0.11, 0.004, line, 0.8)
    f.line(0.70, 0.18, 0.95, 0.18, 0.004, line, 0.8)
    for k in range(5):
        f.line(0.70, 0.30 + k * 0.10, 0.70 + rng.uniform(0.12, 0.25), 0.30 + k * 0.10, 0.004, line, 0.6)
    f.tint(0.72, 0.74, 0.96, 0.90, mix(bp, WHITE, 0.15), 0.9)               # title block
    f.line(0.72, 0.82, 0.96, 0.82, 0.003, line, 0.8)
    f.line(0.80, 0.74, 0.80, 0.90, 0.003, line, 0.8)


@sprop("pro_arch_plans", aspect=3.1, fill=0.90)
def arch_plans(c, color):
    rng = c.rng
    bp = (0.13, 0.31, 0.56)
    ao(c, 0.12, 0.02, 2.5, 0.6, 0.30)
    # a stack of two loose sheets under the main blueprint, fanned a little
    for k, (du, dv, col) in enumerate(((0.05, -0.02, (0.94, 0.93, 0.89)), (-0.04, 0.0, (0.90, 0.90, 0.86)))):
        g = _Flat(c, -1.15 + du, 0.02 + dv, 2.3, 0.0, 0.34, 0.86)
        g.tint(0, 0, 1, 1, col, 1.0)
    f = _Flat(c, -1.15, 0.03, 2.3, 0.0, 0.34, 0.86)
    _sheet_plan(c, f, bp, rng)
    f.line(0.0, 0.0, 1.0, 0.0, 0.008, (0.7, 0.8, 0.95), 0.55)
    f.line(0.0, 1.0, 1.0, 1.0, 0.006, (0.05, 0.12, 0.26), 0.5)
    f.tint(0.0, 0.0, 1.0, 0.16, BLACK, 0.12)
    # pencil lying along the sheet with its sharpened tip and an eraser end
    g = _tube(c, -0.30, 0.22, 0.95, 0.050, (0.95, 0.78, 0.25), ang=11)
    t0, t1 = g.pt(-0.50, 0.0), g.pt(-0.43, 0.025)
    c.poly([g.pt(-0.50, 0.0), g.pt(-0.40, 0.025), g.pt(-0.40, -0.025)], (0.90, 0.74, 0.52), lift=0.0)
    c.poly([g.pt(-0.50, 0.0), g.pt(-0.45, 0.012), g.pt(-0.45, -0.012)], (0.18, 0.18, 0.20), lift=0.0)
    e0 = g.pt(0.47, 0.0)
    c.circle(e0[0], e0[1], 0.026, (0.93, 0.55, 0.55), lift=0.2)
    soft_disc(c, -0.33, 0.20, 0.5, 0.05, BLACK, 0.14, 1.4)


@sprop("pro_arch_rolls", aspect=0.95, fill=0.92)
def arch_rolls(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.6, 0.15)
    for ang, hi, col, du in ((-12, 0.62, (0.15, 0.34, 0.60), -0.08), (6, 0.78, (0.96, 0.95, 0.92), 0.02), (22, 0.70, (0.94, 0.93, 0.88), 0.12)):
        g = _G(c, du, 0.28, ang)
        g.rect(0.0, hi / 2 - 0.1, 0.13, hi, col, r=0.02, lift=0.28)
        g.rect(-0.03, hi / 2 - 0.1, 0.035, hi * 0.96, WHITE, alpha=0.30)
        top = g.pt(0.0, hi - 0.1)
        c.ellipse(top[0], top[1], 0.067, 0.03, scale(col, 0.66), lift=0.0)
        c.ellipse(top[0], top[1] + 0.003, 0.048, 0.019, scale(col, 0.88), lift=0.0)
        c.ellipse(top[0], top[1] + 0.003, 0.022, 0.009, scale(col, 0.55), lift=0.0)
        for _ in range(3):
            b = g.pt(rng.uniform(-0.04, 0.04), rng.uniform(0.1, hi * 0.7))
            c.line(b[0] - 0.03, b[1], b[0] + 0.03, b[1], 0.004, (0.86, 0.93, 1.0), 0.4)
    craft.hshade_box(c, 0.0, 0.16, 0.40, 0.32, mix(KRAFT, WHITE, 0.15), scale(KRAFT, 0.55), r=0.02)       # kraft tube holder
    disc(c, 0.0, 0.32, 0.20, (0.84, 0.70, 0.50), 0.36, 0.05)
    c.ellipse(0.0, 0.318, 0.165, 0.062, (0.20, 0.14, 0.10), lift=0.0, alpha=0.8)
    for k in range(3):
        craft.arc(c, 0.0, 0.16 + k * 0.05, 0.20, 0.07, 200, 340, 0.004, scale(KRAFT, 0.72), 0.5, 8)
    c.rect(-0.04, 0.18, 0.09, 0.07, (0.96, 0.95, 0.92), lift=0.0, alpha=0.9)
    gloss(c, -0.12, 0.2, 0.03, 0.12, 0, 0.30)


@sprop("pro_arch_tools", aspect=4.3, fill=0.45)
def arch_tools(c, color):
    ao(c, 0.0, 0.0, 2.2, 0.35)
    # triangular scale ruler: top face, front face with ticks
    g = _G(c, -0.1, 0.12, 4)
    g.rect(0.0, 0.0, 1.9, 0.11, (0.96, 0.95, 0.90), r=0.01, lift=0.12)
    g.rect(0.0, 0.058, 1.9, 0.03, WHITE, alpha=0.6)
    g.rect(0.0, -0.048, 1.9, 0.02, (0.60, 0.58, 0.52), alpha=0.7)
    for k in range(40):
        g.line(-0.93 + k * 0.0476, 0.0, -0.93 + k * 0.0476, 0.03 + (0.02 if k % 5 == 0 else 0.0), 0.004, (0.15, 0.16, 0.2), 0.85)
    g.rect(-0.5, 0.0, 0.05, 0.1, (0.90, 0.42, 0.20), alpha=0.9)
    # drafting compass: two legs from a hinge, steel needle and a pencil lead
    hu, hv = 0.72, 0.42
    c.line(hu, hv, 0.52, 0.10, 0.045, scale(STEELC, 0.7), 1.0)
    c.line(hu - 0.006, hv, 0.51, 0.10, 0.03, mix(STEELC, WHITE, 0.25), 1.0)
    c.line(hu, hv, 0.95, 0.12, 0.045, scale(STEELC, 0.7), 1.0)
    c.line(hu + 0.006, hv, 0.94, 0.12, 0.028, mix(STEELC, WHITE, 0.3), 1.0)
    c.line(0.52, 0.10, 0.50, 0.03, 0.014, (0.85, 0.87, 0.9), 1.0)
    c.line(0.95, 0.12, 0.96, 0.05, 0.034, (0.20, 0.20, 0.22), 1.0)
    c.line(0.96, 0.06, 0.96, 0.02, 0.016, (0.25, 0.25, 0.28), 1.0)
    c.circle(hu, hv, 0.05, BRASS, lift=0.30)
    c.rect(hu, hv + 0.09, 0.04, 0.10, scale(STEELC, 0.8), r=0.015)
    c.circle(hu, hv + 0.15, 0.035, mix(STEELC, WHITE, 0.2), lift=0.3)
    gloss(c, hu - 0.015, hv + 0.02, 0.02, 0.02, 0, 0.9)
    craft.arc(c, 0.52, 0.04, 0.44, 0.07, 10, 120, 0.004, (0.28, 0.28, 0.30), 0.18, 8)


@sprop("pro_arch_lamp", aspect=1.05, fill=1.0)
def arch_lamp(c, color):
    """Classic spring-arm drafting lamp: heavy round base, two arms reaching to the right, a cone shade angled down onto the work."""
    st = (0.84, 0.85, 0.87)
    ao(c, 0.0, 0.0, 0.70, 0.20)
    c.ellipse(0.0, 0.02, 0.30, 0.30 * TILT, scale(st, 0.45), lift=0)
    disc(c, 0.0, 0.05, 0.29, st, TILT, 0.12)
    c.ellipse(0.0, 0.085, 0.13, 0.13 * TILT, scale(st, 0.78), lift=0.1)
    j1, j2, head = (0.0, 0.12), (-0.16, 0.70), (0.40, 0.84)
    # lower arm (a doubled bar with a spring), upper arm to the head
    for off, wd, col in ((0.0, 0.040, scale(st, 0.52)), (0.045, 0.014, scale(st, 0.40))):
        c.line(j1[0] + off, j1[1], j2[0] + off, j2[1], wd, col, 1.0)
    c.line(j1[0] - 0.004, j1[1], j2[0] - 0.004, j2[1], 0.018, mix(st, WHITE, 0.4), 0.9)
    for k in range(10):                                                  # spring coils
        t = 0.12 + k * 0.078
        c.line(j1[0] + 0.03 + (j2[0] - j1[0]) * t - 0.012, j1[1] + (j2[1] - j1[1]) * t, j1[0] + 0.06 + (j2[0] - j1[0]) * t + 0.012, j1[1] + (j2[1] - j1[1]) * t + 0.02, 0.006, (0.30, 0.30, 0.33), 0.8)
    c.line(j2[0], j2[1], head[0], head[1], 0.034, scale(st, 0.52), 1.0)
    c.line(j2[0], j2[1] + 0.006, head[0], head[1] + 0.006, 0.014, mix(st, WHITE, 0.4), 0.9)
    for (u, v, r) in (j1 + (0.040,), j2 + (0.042,)):
        c.circle(u, v, r, scale(st, 0.58), lift=0.3)
        c.circle(u - 0.006, v + 0.006, r * 0.45, mix(st, WHITE, 0.55), lift=0.2)
    # cone shade, tilted down and to the right, hanging directly from the end of the arm
    hx, hy = head
    dx, dy = 0.60, -0.80
    nx, ny = 0.80, 0.60
    L, w0, w1 = 0.34, 0.045, 0.15
    ex, ey = hx + dx * L, hy + dy * L
    c.glow(ex + dx * 0.12, ey + dy * 0.16, 1.1, (1.0, 0.90, 0.66), 0.55)
    c.poly([(hx + nx * w0, hy + ny * w0), (ex + nx * w1, ey + ny * w1), (ex - nx * w1, ey - ny * w1), (hx - nx * w0, hy - ny * w0)], scale(st, 0.58), lift=0.2)
    c.poly([(hx + nx * w0 * 0.2, hy + ny * w0 * 0.2 + 0.012), (ex + nx * w1 * 0.45, ey + ny * w1 * 0.45 + 0.01), (ex - nx * w1 * 0.1, ey - ny * w1 * 0.1 + 0.01),
            (hx - nx * w0 * 0.7, hy - ny * w0 * 0.7 + 0.01)], mix(st, WHITE, 0.30), lift=0.1, alpha=0.75)
    c.ellipse(ex, ey, w1 * 1.0, w1 * 0.40, (1.0, 0.95, 0.80), angle=-37, lift=0.0)
    c.ellipse(ex, ey, w1 * 0.60, w1 * 0.22, WHITE, angle=-37, lift=0.0, alpha=0.9)
    c.circle(hx, hy, 0.034, scale(st, 0.50), lift=0.3)
    c.circle(hx - 0.006, hy + 0.006, 0.014, mix(st, WHITE, 0.55), lift=0.2)


@niche("architect", "Architecture firm", subjects=("pro_arch_model",),
       strong=("architect", "architecture firm", "architectural design", "building plans", "architects", "architecture studio", "floor plan",
               "house plan", "aarkitekt", "naksha", "नक्शा", "आर्किटेक्ट", "वास्तुकार", "भवन निर्माण डिजाइन", "ghar ka naksha"),
       weak=("blueprint", "drafting", "elevation", "planning", "3d model", "structural", "building design", "drawing"),
       accent="#546e7a", mood="light", group="professional")
def architect(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.55)
        # tall studio window with a blurred skyline
        st, sb = _sky(P)
        S.gradient_rect(0.0, 0.0, 0.62, 0.55, st, sb)
        u = 0.0
        while u < 0.62:
            w, h = rng.uniform(0.03, 0.07), rng.uniform(0.06, 0.24)
            S.rect(u + w / 2, 0.55 - h / 2, w, h, mix(sb, P.ink, rng.uniform(0.15, 0.35)), lift=0.0)
            u += w + 0.004
        for k in range(3):
            S.rect(0.10 + k * 0.20, 0.27, 0.010, 0.56, scale(P.wall_top, 0.92), lift=0.0)
        S.rect(0.31, 0.19, 0.64, 0.010, scale(P.wall_top, 0.92), lift=0.0)
        S.glow(0.30, 0.22, 0.9, P.light, 0.22 if not dark else 0.12)
        # pin board with blueprints and a shelf of white massing models
        S.rect(1.50, 0.22, 0.95, 0.34, mix(P.wall_bot, KRAFT, 0.55 if not dark else 0.25), lift=0.0)
        for (u, v, w, h) in ((1.18, 0.22, 0.20, 0.26), (1.43, 0.20, 0.22, 0.20), (1.68, 0.23, 0.18, 0.27), (1.86, 0.19, 0.12, 0.16)):
            S.rect(u, v, w, h, mix((0.15, 0.32, 0.58), P.wall_bot, 0.4 if dark else 0.0), lift=0.0, alpha=0.95)
            S.rect(u, v, w * 0.7, h * 0.012, (0.85, 0.92, 1.0), lift=0.0, alpha=0.6)
        S.rect(1.50, 0.455, 1.2, 0.014, mix(P.wall_bot, P.ink, 0.4), lift=0.0)
        u = 1.0
        while u < 2.0:
            w, h = rng.uniform(0.04, 0.09), rng.uniform(0.03, 0.08)
            S.rect(u + w / 2, 0.45 - h / 2, w, h, mix(WHITE, P.wall_top, 0.2), lift=0.0)
            u += w + 0.02
        S.pendant(0.95, -0.1, 0.16, (1.0, 0.92, 0.74), 0.09)
        S.pendant(1.35, -0.1, 0.12, (1.0, 0.92, 0.74), 0.08)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [(1.0, 0.92, 0.72), P.accent_light], 0.012, 0.04, 0.3)
        S.floor(0.55, P.floor_top, P.floor_bot)
    # honey-oak drafting table: strong plank contrast, a window pool of light and reflections, a darker front edge
    S.soft(1.10, 0.66, 1.1, 0.12, (1.0, 0.93, 0.78), 0.20 if not dark else 0.26, 1.5, add=True)
    desk = mix(P.surface, (0.80, 0.62, 0.42), 0.45) if not dark else scale(P.surface, 1.1)
    S.wood(-5.0, 0.55, 7.0, 2.6, desk, plank=0.13, grain=0.6)
    S.rect(1.0, 0.55, 14.0, 0.008, scale(desk, 0.45), lift=0.0)
    S.rect(1.0, 0.565, 14.0, 0.012, mix(desk, WHITE, 0.4), lift=0.0, alpha=0.5)
    S.put("pro_arch_rolls", 1.62, 0.84, 0.36, shadow=False, framed=False)
    S.put("pro_arch_plans", 1.10, 1.0, 0.36, shadow=False)
    S.put("pro_arch_lamp", 0.80, 0.80, 0.42, color=P, shadow_alpha=0.22)
    S.put("pro_arch_model", 1.17, 0.92, 0.54, color=P, subject=True, shadow_alpha=0.34)
    S.put("pro_arch_tools", 1.12, 1.03, 0.15, shadow=False)
    S.soft(0.92, 0.80, 0.55, 0.20, (1.0, 0.92, 0.72), 0.26 if not dark else 0.42, 1.6, add=True)
    S.focus("detail", 1.20, 0.66)
    with S.near():
        S.circle(0.55, 0.97, 0.04, P.accent_light, alpha=0.35, lift=0)
        S.circle(1.62, 0.36, 0.05, (1.0, 0.9, 0.7), alpha=0.25, lift=0)


# ====================================================================================================== INSURANCE / FINANCE ADVISOR
def _shield_pts(cu, cv_, k):
    half = [(0.0, 0.90), (0.20, 0.97), (0.40, 0.91), (0.42, 0.60), (0.33, 0.33), (0.14, 0.14), (0.0, 0.07)]
    pts = [(cu + x * k, cv_ + (y - 0.5) * k) for x, y in half]
    pts += [(cu - x * k, cv_ + (y - 0.5) * k) for x, y in reversed(half[1:-1])]
    return pts


@sprop("pro_ins_shield", aspect=0.95, fill=1.0)
def ins_shield(c, color):
    acc = _acc(color, "accent", (0.08, 0.40, 0.75))
    ao(c, 0.04, 0.0, 0.8, 0.22)
    # glass plinth
    c.ellipse(0.0, 0.025, 0.38, 0.38 * TILT, scale(acc, 0.35), lift=0, alpha=0.8)
    disc(c, 0.0, 0.05, 0.37, mix(acc, WHITE, 0.82), TILT, 0.1, alpha=0.95)
    c.ellipse(0.0, 0.06, 0.26, 0.26 * TILT, mix(acc, WHITE, 0.55), lift=0, alpha=0.6)
    soft_disc(c, 0.0, 0.07, 0.34, 0.12, mix(acc, WHITE, 0.4), 0.45, 1.2, add=True)
    cu, cv_, k = 0.0, 0.54, 0.86
    # thickness: a darker copy shifted down and to the right, then the lit face
    _hpoly(c, _shield_pts(cu + 0.035, cv_ - 0.03, k), scale(acc, 0.62), scale(acc, 0.32), 0.05, smooth=2)
    _hpoly(c, _shield_pts(cu, cv_, k), mix(acc, WHITE, 0.30), scale(acc, 0.62), 0.12, power=1.1, smooth=2)
    _hpoly(c, _shield_pts(cu, cv_ - 0.005, k * 0.86), mix(acc, WHITE, 0.05), scale(acc, 0.48), 0.10, power=1.0, smooth=2)
    _spoly(c, _shield_pts(cu, cv_ - 0.01, k * 0.80), mix(acc, WHITE, 0.15), 2, 0.28, 0.35)
    c.path([(-0.17, 0.52), (-0.04, 0.38), (0.19, 0.66)], 0.11, scale(acc, 0.35), 0.5, smooth=False)
    c.path([(-0.17, 0.545), (-0.04, 0.405), (0.19, 0.69)], 0.10, (0.97, 0.98, 1.0), 1.0, smooth=False)
    c.path([(-0.17, 0.555), (-0.04, 0.42), (0.19, 0.70)], 0.03, WHITE, 0.6, smooth=False)
    # glass sheen across the face, rim highlight
    _fill_quad(c.cv, [(c.X(-0.40), c.Y(0.96)), (c.X(-0.10), c.Y(1.0)), (c.X(-0.30), c.Y(0.36)), (c.X(-0.40), c.Y(0.50))], WHITE, 0.14)
    craft.arc(c, 0.0, 0.54, 0.40 * k, 0.40 * k, 100, 175, 0.012, WHITE, 0.55, 8)
    gloss(c, -0.22, 0.85, 0.12, 0.07, 20, 0.45)
    c.glow(0.0, 0.5, 0.8, mix(acc, WHITE, 0.5), 0.08)


def _figure(c, u, v, h, shirt, skin, hair, skirt=False):
    """A small family figurine: rounded body, head and hair."""
    w = h * 0.34
    ao(c, u, v, w * 1.5, w * 0.5, 0.35)
    if skirt:
        c.poly([(u - w * 0.30, v + h * 0.60), (u + w * 0.30, v + h * 0.60), (u + w * 0.62, v + h * 0.04), (u - w * 0.62, v + h * 0.04)], shirt, lift=0.25)
    else:
        _crect(c, u, v + h * 0.28, w * 0.95, h * 0.52, shirt, r=w * 0.28, lift=0.25)
        _crect(c, u - w * 0.18, v + h * 0.08, w * 0.30, h * 0.16, scale(shirt, 0.55), r=0.004, lift=0.1)
        _crect(c, u + w * 0.18, v + h * 0.08, w * 0.30, h * 0.16, scale(shirt, 0.55), r=0.004, lift=0.1)
    c.circle(u, v + h * 0.80, h * 0.19, skin, lift=0.2)
    c.ellipse(u, v + h * 0.86, h * 0.20, h * 0.12, hair, lift=0.15)
    soft_disc(c, u - h * 0.06, v + h * 0.85, h * 0.07, h * 0.05, WHITE, 0.45, 1.2, add=True)


@sprop("pro_ins_cover", aspect=1.35, fill=1.0)
def ins_cover(c, color):
    acc = _acc(color, "accent", (0.08, 0.40, 0.75))
    acc2 = _acc(color, "accent2", (0.95, 0.6, 0.2))
    ao(c, 0.0, 0.0, 1.0, 0.25)
    # a little house (right) and the family (left) on a green felt mat
    c.ellipse(0.02, 0.025, 0.58, 0.58 * 0.30, (0.45, 0.62, 0.40), lift=0.12)
    c.ellipse(0.02, 0.032, 0.52, 0.52 * 0.28, (0.52, 0.70, 0.45), lift=0.1)
    hu, hv, hw, hh, hd = 0.20, 0.04, 0.30, 0.17, 0.20
    box3d(c, hu, hv, hw, hh, hd, (0.97, 0.93, 0.85), (0.99, 0.97, 0.92), (0.72, 0.66, 0.58), lift=0.06)
    ox, oy = hd * 0.55, hd * 0.42
    top = hv + hh
    c.poly([(hu - hw / 2 - 0.02, top), (hu + hw / 2 + 0.02, top), (hu, top + 0.13)], (0.97, 0.93, 0.85), lift=0.06)
    c.poly([(hu + hw / 2 + 0.02, top), (hu, top + 0.13), (hu + ox, top + 0.13 + oy), (hu + hw / 2 + 0.02 + ox, top + oy)], scale(acc, 0.7), lift=0.15)
    c.poly([(hu - hw / 2 - 0.02, top), (hu, top + 0.13), (hu + 0.006, top + 0.13 + 0.01), (hu - hw / 2 - 0.02, top + 0.01)], mix(acc, WHITE, 0.4), lift=0.0, alpha=0.9)
    _crect(c, hu - 0.065, hv + 0.07, 0.075, 0.09, (0.98, 0.84, 0.50), r=0.004, lift=0.1)                     # lit windows
    _crect(c, hu - 0.065, hv + 0.07, 0.008, 0.09, (0.55, 0.42, 0.28), lift=0.0)
    _crect(c, hu + 0.07, hv + 0.065, 0.07, 0.10, (0.52, 0.30, 0.18), r=0.005, lift=0.2)                       # door
    c.circle(hu + 0.09, hv + 0.06, 0.006, BRASS, lift=0.3)
    c.circle(hu, top + 0.065, 0.016, (0.98, 0.84, 0.50), lift=0.1)
    _figure(c, -0.34, 0.01, 0.26, scale(acc, 0.9), (0.93, 0.74, 0.60), (0.18, 0.12, 0.10))                 # father
    _figure(c, -0.13, 0.02, 0.24, acc2, (0.88, 0.68, 0.54), (0.22, 0.12, 0.08), skirt=True)               # mother
    _figure(c, -0.23, -0.01, 0.15, (0.96, 0.78, 0.25), (0.94, 0.76, 0.62), (0.30, 0.18, 0.10))           # child
    # umbrella: pole behind, canopy of alternating wedges seen from the side, scalloped edge
    pu = 0.02
    c.rect(pu, 0.50, 0.026, 0.88, (0.78, 0.80, 0.84), lift=0.0)
    c.rect(pu - 0.006, 0.50, 0.008, 0.88, WHITE, lift=0.0, alpha=0.6)
    cu, cv_, R, Hc = pu, 0.80, 0.66, 0.30
    n = 6
    xs = [cu - R + 2 * R * i / n for i in range(n + 1)]
    for i in range(n):
        x0, x1 = xs[i], xs[i + 1]
        col = acc if i % 2 == 0 else mix(acc, WHITE, 0.86)
        mid = (x0 + x1) / 2
        pts = [(cu, cv_ + Hc)]
        h0 = math.sqrt(max(0.0, 1 - ((x0 - cu) / R) ** 2))
        h1 = math.sqrt(max(0.0, 1 - ((x1 - cu) / R) ** 2))
        edge0, edge1 = cv_ + Hc * h0 * 0.62 - 0.12 * 0.0, cv_ + Hc * h1 * 0.62
        ym = cv_ + Hc * 0.02
        poly = [(cu + (x0 - cu) * 0.06, cv_ + Hc), (x0, ym), (mid, ym - 0.045), (x1, ym), (cu + (x1 - cu) * 0.06, cv_ + Hc)]
        poly = [(cu + (x0 - cu) * 0.06, cv_ + Hc), (cu + (x0 - cu) * 0.55, cv_ + Hc * 0.80), (x0, ym)] + [(mid, ym - 0.05)] + \
               [(x1, ym), (cu + (x1 - cu) * 0.55, cv_ + Hc * 0.80), (cu + (x1 - cu) * 0.06, cv_ + Hc)]
        px = [(c.X(a), c.Y(b)) for a, b in poly]
        sh = 0.5 + 0.5 * (mid - cu) / R
        left, right = mix(col, WHITE, 0.14), scale(col, 0.62)
        _fillpoly(c, px, col, 1.0, lambda x, y, left=left, right=right, x0_=c.X(cu - R), sp=c.s * 2 * R: mix(left, right, clamp((x - x0_) / sp)))
    c.circle(cu, cv_ + Hc + 0.012, 0.018, BRASS, lift=0.3)
    craft.arc(c, cu, cv_ + Hc * 0.6, R * 0.98, Hc * 0.45, 20, 160, 0.006, WHITE, 0.30, 10)
    soft_disc(c, cu - 0.25, cv_ + Hc * 0.7, 0.2, 0.08, WHITE, 0.40, 1.2, add=True)
    soft_disc(c, 0.0, 0.40, 0.55, 0.20, BLACK, 0.20, 1.3)                                                   # canopy shadow on the family


@sprop("pro_ins_docs", aspect=2.3, fill=0.60)
def ins_docs(c, color):
    acc = _acc(color, "accent", (0.08, 0.40, 0.75))
    rng = c.rng
    ao(c, 0.1, 0.0, 1.6, 0.32, 0.38)
    # blue policy folder, then loose papers fanned on top, then the pen
    box3d(c, -0.15, 0.0, 1.05, 0.05, 0.60, scale(acc, 0.85), mix(acc, WHITE, 0.2), scale(acc, 0.55), lift=0.12, dx=0.5, dy=0.5)
    f = _Flat(c, -0.62, 0.05, 1.0, 0.0, 0.30, 0.31)
    f.quad(0.0, 0.0, 1.0, 1.0, mix(acc, WHITE, 0.25), lift=0.0)
    g = _Flat(c, -0.50, 0.075, 0.95, 0.0, 0.26, 0.30)
    g.quad(0.0, 0.0, 1.0, 1.0, PAPER, lift=0.0)
    g.line(0.0, 1.0, 1.0, 1.0, 0.004, WHITE, 0.8)
    f2 = _Flat(c, -0.42, 0.085, 0.90, 0.0, 0.24, 0.28)
    f2.quad(0.0, 0.0, 1.0, 1.0, (0.99, 0.985, 0.97), lift=0.0)
    f2.tint(0.0, 0.0, 1.0, 1.0, mix(acc, WHITE, 0.6), 0.04)
    for k in range(7):                                                                    # printed lines
        f2.line(0.08, 0.88 - k * 0.11, 0.92 - (0.3 if k % 3 == 2 else 0.0) * rng.random(), 0.88 - k * 0.11, 0.0045, (0.45, 0.48, 0.55), 0.8)
    f2.quad(0.08, 0.08, 0.38, 0.22, mix(acc, WHITE, 0.2), lift=0.0, alpha=0.9)            # logo block
    f2.line(0.58, 0.14, 0.90, 0.14, 0.004, (0.15, 0.15, 0.25), 0.9)                       # signature line
    p = f2.p
    sig = [(0.60, 0.20), (0.66, 0.28), (0.70, 0.16), (0.76, 0.27), (0.82, 0.18)]
    c.path([f2.p(a, b) for a, b in sig], 0.007, (0.15, 0.20, 0.55), 0.9, smooth=True)
    seal = f2.p(0.78, 0.36)
    c.ellipse(seal[0], seal[1], 0.035, 0.02, (0.78, 0.15, 0.15), lift=0.2)
    # fountain pen
    g2 = _G(c, 0.52, 0.28, 14)
    g2.rect(0.0, 0.0, 0.86, 0.05, (0.10, 0.11, 0.18), r=0.022, lift=0.4)
    g2.rect(-0.20, 0.014, 0.40, 0.012, WHITE, alpha=0.35)
    g2.rect(-0.46, 0.0, 0.06, 0.054, BRASS, lift=0.3)
    g2.line(0.44, 0.0, 0.50, 0.0, 0.03, (0.88, 0.72, 0.30), 1.0)
    soft_disc(c, 0.4, 0.31, 0.5, 0.05, BLACK, 0.12, 1.4)


@niche("insurance", "Insurance and finance advisor", subjects=("pro_ins_shield",),
       strong=("insurance", "life insurance", "health insurance", "insurance advisor", "mutual funds", "loan advisor", "insurance agent",
               "insurance company", "car insurance", "term plan", "बीमा", "bima", "जीवन बीमा", "एलआईसी", "lic agent", "policy advisor"),
       weak=("policy", "premium", "claim", "coverage", "investment", "sip", "loan", "protection", "wealth"),
       accent="#1565c0", mood="light", group="professional")
def insurance(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.56)
        S.glow(1.7, 0.22, 1.0, P.accent_light, 0.30 if dark else 0.16)
        # glass partition wall with soft blue city, framed photos of families and a pendant
        st, sb = _sky(P)
        S.gradient_rect(1.05, 0.0, 2.05, 0.56, st, sb)
        u = 1.05
        while u < 2.05:
            w, h = rng.uniform(0.04, 0.09), rng.uniform(0.08, 0.28)
            S.rect(u + w / 2, 0.56 - h / 2, w, h, mix(sb, P.accent, rng.uniform(0.12, 0.30)), lift=0.0)
            u += w + 0.004
        for k in range(4):
            S.rect(1.05 + k * 0.33, 0.28, 0.012, 0.56, mix(P.wall_top, WHITE, 0.5), lift=0.0)
        for (u, v, w, h) in ((0.22, 0.20, 0.20, 0.26), (0.50, 0.26, 0.15, 0.20), (0.70, 0.17, 0.12, 0.17)):
            S.rect(u, v, w + 0.02, h + 0.02, mix(WHITE, P.wall_top, 0.3) if not dark else scale(P.wall_top, 1.6), lift=0.0)
            S.rect(u, v, w, h, mix(P.accent_light, P.wall_bot, 0.4), lift=0.0, alpha=0.9)
            S.circle(u, v - h * 0.1, w * 0.18, (0.95, 0.80, 0.65), lift=0.0)
            S.rect(u, v + h * 0.22, w * 0.5, h * 0.3, scale(P.accent, 0.9), lift=0.0, r=0.01)
        S.pendant(0.85, -0.1, 0.16, (1.0, 0.94, 0.78), 0.09)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [P.accent_light, (1.0, 0.95, 0.8)], 0.012, 0.04, 0.3)
        S.floor(0.56, P.floor_top, P.floor_bot)
    # a glossy white desk: smooth gradient, no planks, soft reflections
    desk_t = mix(WHITE, P.accent_light, 0.18) if not dark else mix(P.accent_dark, P.ink, 0.45)
    desk_b = scale(desk_t, 0.82)
    S.gradient_rect(-5.0, 0.56, 7.0, 2.6, desk_t, desk_b)
    S.rect(1.0, 0.56, 14.0, 0.010, scale(desk_t, 0.60), lift=0.0)
    S.soft(1.15, 0.64, 1.1, 0.10, WHITE if not dark else P.accent_light, 0.45 if not dark else 0.30, 1.5, add=True)
    S.put("digedu_plant", 0.60, 0.80, 0.22, color=mix(P.accent_light, WHITE, 0.6), shadow_alpha=0.28)
    S.put("pro_ins_cover", 1.38, 0.88, 0.50, color=P, shadow_alpha=0.30)
    S.put("pro_ins_shield", 0.98, 0.94, 0.52, color=P, subject=True, shadow_alpha=0.34)
    S.put("pro_ins_docs", 0.72, 1.0, 0.17, color=P, shadow_alpha=0.28)
    S.soft(1.0, 0.70, 0.5, 0.25, mix(P.accent_light, WHITE, 0.5), 0.22 if not dark else 0.40, 1.6, add=True)
    S.focus("detail", 1.34, 0.72)
    with S.near():
        S.circle(0.55, 0.97, 0.04, P.accent_light, alpha=0.40, lift=0)
        S.circle(1.64, 0.40, 0.05, mix(P.accent, WHITE, 0.4), alpha=0.25, lift=0)


# ====================================================================================================== CONSULTING
def _con_ui(g, acc):
    rng = g.c.rng
    ink = (0.16, 0.18, 0.26)
    g.rect(0, 0, 1.26, 0.70, (0.96, 0.965, 0.98))
    g.rect(0, 0.30, 1.26, 0.10, mix(acc, (0.05, 0.08, 0.14), 0.6))
    g.rect(-0.45, 0.30, 0.22, 0.02, WHITE, r=0.01, alpha=0.9)
    g.rect(0.50, 0.30, 0.34, 0.018, mix(acc, WHITE, 0.6), r=0.009, alpha=0.8)
    g.rect(-0.38, 0.17, 0.42, 0.045, ink, r=0.012)
    _textbars(g, -0.57, 0.09, 0.64, (0.62, 0.65, 0.72), 3, 0.045, 0.016)
    _ui_card(g, 0.30, -0.03, 0.62, 0.50)
    _bars(g, 0.04, -0.21, 0.56, 0.12, mix(acc, WHITE, 0.5), rng, 7, acc, hi=5)
    g.path([(0.04, -0.14), (0.16, -0.10), (0.28, -0.12), (0.40, -0.02), (0.54, 0.08)], 0.012, (0.95, 0.55, 0.15), 1.0)
    g.circle(0.54, 0.08, 0.022, WHITE)
    g.circle(0.54, 0.08, 0.012, (0.95, 0.55, 0.15))
    _ui_card(g, -0.40, -0.19, 0.34, 0.24)
    _donut(g, -0.40, -0.18, 0.065, 0.024, (acc, (0.95, 0.55, 0.15), (0.65, 0.70, 0.78)), (0.55, 0.25, 0.20))
    g.rect(0.30, -0.255, 0.30, 0.012, (0.75, 0.78, 0.84), r=0.006)


@sprop("pro_con_laptop", aspect=1.7, fill=0.92)
def con_laptop(c, color):
    _laptop(c, _con_ui, _acc(color, "accent", (0.22, 0.35, 0.50)), body=(0.72, 0.75, 0.80))


def _note(g, u, v, w, col, ang=0.0):
    g.rect(u, v - w * 0.04, w, w, scale(col, 0.7), alpha=0.35)
    g.rect(u, v, w, w, col, lift=0.06)
    g.rect(u, v + w * 0.32, w * 0.8, w * 0.07, scale(col, 0.78), alpha=0.6)
    g.rect(u - w * 0.05, v - w * 0.02, w * 0.62, w * 0.06, scale(col, 0.78), alpha=0.5)


@sprop("pro_con_board", aspect=1.30, fill=1.0)
def con_board(c, color):
    acc = _acc(color, "accent", (0.22, 0.35, 0.50))
    rng = c.rng
    alu = (0.74, 0.76, 0.80)
    ao(c, 0.0, 0.0, 1.2, 0.20, 0.40)
    # wheeled stand
    for u in (-0.50, 0.50):
        c.rect(u, 0.18, 0.045, 0.40, scale(alu, 0.78), lift=0.2)
        c.rect(u - 0.012, 0.18, 0.012, 0.40, WHITE, alpha=0.5, lift=0)
        c.circle(u, 0.03, 0.03, (0.10, 0.10, 0.12), lift=0.2)
    c.rect(0.0, 0.05, 1.12, 0.035, scale(alu, 0.7), r=0.01, lift=0.2)
    # frame and the board surface
    c.rect(0.0, 0.68, 1.36, 0.66, scale(alu, 0.62), r=0.02, lift=0.18)
    c.rect(0.0, 0.68, 1.32, 0.62, (0.96, 0.97, 0.98), r=0.012, lift=0.03)
    c.rect(0.0, 0.40, 1.34, 0.045, alu, r=0.01, lift=0.25)                                    # marker tray
    for k, col in enumerate(((0.15, 0.30, 0.75), (0.80, 0.15, 0.15), (0.10, 0.10, 0.12))):
        c.rect(-0.40 + k * 0.10, 0.43, 0.075, 0.018, col, r=0.008, lift=0.3)
    # writing: title, 2x2 matrix with sticky notes, rising chart, process flow
    ink, red, grn = (0.12, 0.20, 0.55), (0.82, 0.16, 0.16), (0.12, 0.55, 0.30)
    c.text("STRATEGY 2026", -0.36, 0.93, 0.07, ink, 0.20)
    c.line(-0.62, 0.86, 0.02, 0.86, 0.008, red, 0.9)
    c.path([(-0.54, 0.54), (-0.54, 0.80)], 0.010, (0.15, 0.15, 0.2), 0.9, smooth=False)
    c.path([(-0.57, 0.57), (-0.16, 0.57)], 0.010, (0.15, 0.15, 0.2), 0.9, smooth=False)
    c.line(-0.35, 0.57, -0.35, 0.80, 0.007, (0.15, 0.15, 0.2), 0.8)
    c.line(-0.54, 0.69, -0.16, 0.69, 0.007, (0.15, 0.15, 0.2), 0.8)
    g = _G(c)
    _note(g, -0.45, 0.76, 0.095, (1.0, 0.85, 0.30))
    _note(g, -0.26, 0.76, 0.095, (1.0, 0.62, 0.70))
    _note(g, -0.44, 0.62, 0.095, mix(acc, WHITE, 0.55))
    _note(g, -0.25, 0.63, 0.095, (0.62, 0.90, 0.60))
    c.circle(-0.20, 0.78, 0.016, red, lift=0)
    for k in range(5):                                                                         # bars + arrow
        hh = 0.06 + k * 0.045
        c.rect(0.10 + k * 0.095, 0.57 + hh / 2, 0.06, hh, ink if k < 4 else grn, lift=0.1)
    c.path([(0.08, 0.66), (0.22, 0.72), (0.34, 0.70), (0.52, 0.82)], 0.012, red, 1.0, smooth=True)
    c.poly([(0.52, 0.86), (0.60, 0.80), (0.50, 0.78)], red, lift=0.0)
    c.text("+40%", 0.43, 0.92, 0.065, grn, 0.20)
    for k in range(3):                                                                         # flow boxes
        u = -0.46 + k * 0.40
        c.rect(u, 0.50, 0.22, 0.07, mix(acc, WHITE, 0.82), r=0.012, lift=0.0)
        c.line(u - 0.09, 0.50, u + 0.09 - 0.02 * k, 0.50, 0.010, ink, 0.55)
        if k < 2:
            c.path([(u + 0.12, 0.50), (u + 0.28, 0.50)], 0.008, red, 0.9, smooth=False)
            c.poly([(u + 0.29, 0.50), (u + 0.25, 0.53), (u + 0.25, 0.47)], red, lift=0.0)
    soft_disc(c, -0.3, 0.9, 0.5, 0.18, WHITE, 0.25, 1.3, add=True)
    _fill_quad(c.cv, [(c.X(-0.66), c.Y(0.99)), (c.X(-0.30), c.Y(0.99)), (c.X(-0.52), c.Y(0.40)), (c.X(-0.66), c.Y(0.40))], WHITE, 0.10)


@sprop("pro_con_chair", aspect=0.70, fill=1.0)
def con_chair(c, color):
    """Executive mesh chair seen from the front: light fabric and chrome so it reads as a chair (not a dark blob) against the floor."""
    acc = _acc(color, "accent", (0.22, 0.35, 0.50))
    fab = mix(acc, (0.80, 0.83, 0.88), 0.55)                 # light grey-blue upholstery
    frame = (0.20, 0.22, 0.26)
    chrome = (0.80, 0.82, 0.86)
    ao(c, 0.0, 0.0, 0.7, 0.18, 0.4)
    for k in range(5):                                                                         # chrome star base with casters
        a = math.radians(200 + k * 35)
        u, v = math.cos(a) * 0.32, 0.03 + (math.sin(a) + 1.0) * 0.015
        c.line(0.0, 0.10, u, v + 0.02, 0.030, scale(chrome, 0.55), 1.0)
        c.line(0.0, 0.11, u, v + 0.03, 0.010, WHITE, 0.6)
        c.circle(u, v, 0.028, (0.07, 0.07, 0.08), lift=0.2)
    c.rect(0.0, 0.22, 0.05, 0.22, scale(chrome, 0.7), lift=0.3)
    c.rect(-0.012, 0.22, 0.012, 0.22, WHITE, alpha=0.7, lift=0)
    # seat: thick cushion with a lit front edge
    c.ellipse(0.0, 0.43, 0.32, 0.32 * 0.36, scale(fab, 0.62), lift=0.0)
    craft.hshade_box(c, 0.0, 0.40, 0.62, 0.085, mix(fab, WHITE, 0.18), scale(fab, 0.62), r=0.035)
    c.ellipse(0.0, 0.452, 0.31, 0.31 * 0.34, mix(fab, WHITE, 0.14), lift=0.15)
    c.line(-0.26, 0.375, 0.26, 0.375, 0.008, WHITE, 0.45)
    # armrests: chrome post, dark pad
    for sgn in (-1, 1):
        c.rect(sgn * 0.335, 0.54, 0.028, 0.18, scale(chrome, 0.7), lift=0.3)
        c.rect(sgn * 0.335, 0.635, 0.075, 0.032, frame, r=0.014, lift=0.2)
        c.rect(sgn * 0.335 - 0.012, 0.642, 0.03, 0.008, WHITE, alpha=0.4, lift=0)
    # backrest: chrome-edged frame, light mesh with a woven highlight, headrest pad and a lumbar bar
    craft.hshade_box(c, 0.0, 0.80, 0.56, 0.62, mix(frame, WHITE, 0.15), scale(frame, 0.6), r=0.09)
    c.rect(0.0, 0.80, 0.49, 0.55, scale(fab, 0.78), r=0.06, lift=0.0)
    for k in range(10):
        c.line(-0.23, 0.55 + k * 0.052, 0.23, 0.55 + k * 0.052, 0.007, mix(fab, WHITE, 0.45), 0.55)
    for k in range(8):
        c.line(-0.21 + k * 0.06, 0.53, -0.21 + k * 0.06, 1.07, 0.004, scale(fab, 0.62), 0.45)
    c.rect(-0.14, 0.82, 0.05, 0.50, WHITE, r=0.025, alpha=0.20, lift=0)
    c.rect(0.0, 1.08, 0.30, 0.075, mix(fab, WHITE, 0.1), r=0.035, lift=0.2)                    # headrest
    c.rect(0.0, 0.58, 0.40, 0.035, scale(frame, 1.2), r=0.015, lift=0.2)                        # lumbar support
    c.line(-0.25, 1.1, 0.25, 1.1, 0.006, WHITE, 0.4)
    c.rect(0.0, 0.43, 0.60, 0.010, mix(acc, WHITE, 0.5), lift=0, alpha=0.8)


@sprop("pro_con_papers", aspect=2.9, fill=0.60)
def con_papers(c, color):
    """A printed report: a chart page on a short stack (edges visible), a bound report booklet beside it, a binder clip and a pen."""
    acc = _acc(color, "accent", (0.22, 0.35, 0.50))
    ink = (0.40, 0.43, 0.50)
    ao(c, 0.0, 0.0, 1.9, 0.38, 0.38)
    # booklet with a bound spine and a printed cover
    bk = _Flat(c, -0.84, 0.0, 0.64, 0.0, 0.12, 0.50)
    bk.tint(0, -0.05, 1, 0, scale(acc, 0.45), 1.0)                                     # front edge (thickness)
    bk.tint(0, 0, 1, 1, mix(acc, (0.05, 0.08, 0.14), 0.45), 1.0)
    bk.tint(0, 0, 0.06, 1, scale(acc, 0.5), 1.0)
    bk.tint(0.14, 0.52, 0.88, 0.60, WHITE, 0.9)
    bk.tint(0.14, 0.40, 0.66, 0.46, mix(acc, WHITE, 0.6), 0.9)
    bk.tint(0.14, 0.10, 0.34, 0.18, mix(acc, WHITE, 0.3), 0.8)
    lg = bk.p(0.76, 0.80)
    c.ellipse(lg[0], lg[1], 0.05, 0.035, (0.95, 0.62, 0.22), lift=0.1)
    c.ellipse(lg[0], lg[1], 0.024, 0.017, mix(acc, WHITE, 0.2), lift=0.0)
    # chart page on a short stack: three sheets with visible edges
    for k, (du, dv, col) in enumerate(((-0.05, 0.0, (0.90, 0.90, 0.87)), (0.02, 0.018, (0.94, 0.94, 0.91)), (0.06, 0.036, PAPER))):
        g = _Flat(c, 0.02 + du, dv, 0.80, 0.0, 0.16, 0.52)
        if k < 2:
            g.tint(0, -0.03, 1, 0, scale(col, 0.78), 1.0)
        g.tint(0, 0, 1, 1, col, 1.0)
    f = _Flat(c, 0.08, 0.036, 0.80, 0.0, 0.16, 0.52)
    f.tint(0.08, 0.84, 0.60, 0.91, mix(acc, (0.05, 0.08, 0.14), 0.4), 1.0)                      # headline bar
    for k in range(3):
        f.line(0.08, 0.76 - k * 0.07, 0.56 - 0.1 * (k % 2), 0.76 - k * 0.07, 0.006, ink, 0.75)
    f.tint(0.08, 0.14, 0.58, 0.54, (0.99, 0.99, 0.98), 1.0)                                    # chart panel
    for i, hh in enumerate((0.12, 0.20, 0.17, 0.28, 0.34)):
        f.tint(0.12 + i * 0.09, 0.17, 0.19 + i * 0.09, 0.17 + hh, acc if i < 4 else (0.95, 0.60, 0.20), 1.0)
    f.line(0.12, 0.23, 0.55, 0.48, 0.008, (0.95, 0.60, 0.20), 0.9)
    for k in range(6):                                                                          # table rows on the right
        f.line(0.64, 0.80 - k * 0.09, 0.93, 0.80 - k * 0.09, 0.005, ink, 0.6 if k % 2 else 0.9)
    f.tint(0.64, 0.14, 0.93, 0.30, mix(acc, WHITE, 0.7), 1.0)
    cl = f.p(0.50, 1.0)
    c.rect(cl[0], cl[1] + 0.005, 0.18, 0.05, scale(STEELC, 0.75), r=0.018, lift=0.3)           # binder clip
    c.rect(cl[0], cl[1] + 0.035, 0.12, 0.03, scale(STEELC, 0.55), r=0.012, lift=0.2)
    # pen lying diagonally across both
    g = _G(c, 0.05, 0.27, -14)
    g.rect(0.0, 0.0, 0.72, 0.034, (0.14, 0.15, 0.20), r=0.016, lift=0.35)
    g.rect(0.30, 0.0, 0.05, 0.036, BRASS, lift=0.3)
    g.rect(-0.2, 0.008, 0.3, 0.008, WHITE, alpha=0.35, lift=0)
    soft_disc(c, 0.05, 0.25, 0.4, 0.04, BLACK, 0.12, 1.4)


@niche("consulting", "Consulting firm", subjects=("pro_con_board",),
       strong=("consulting firm", "business consultant", "management consulting", "advisory", "strategy consulting", "business setup", "consultancy firm",
               "business consulting", "management consultant", "business advisory", "company registration", "consultancy", "बिज़नेस कंसल्टेंट",
               "कंसल्टिंग फर्म", "सलाहकार", "business salah", "corporate advisory"),
       weak=("strategy", "consulting", "advisor", "growth", "business plan", "startup", "corporate", "solutions"),
       accent="#37474f", mood="cool", group="professional")
def consulting(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # floor to ceiling window with a skyline, glass partition, recessed ceiling lights
        st, sb = _sky(P)
        S.gradient_rect(-0.05, 0.0, 0.95, 0.60, st, sb)
        u = -0.05
        while u < 0.95:
            w, h = rng.uniform(0.04, 0.09), rng.uniform(0.10, 0.40)
            S.rect(u + w / 2, 0.60 - h / 2, w, h, mix(sb, P.ink, rng.uniform(0.12, 0.40)), lift=0.0)
            if rng.random() < 0.5:
                S.rect(u + w / 2, 0.60 - h * 0.6, w * 0.5, 0.01, (1.0, 0.9, 0.6) if dark else WHITE, lift=0.0, alpha=0.6)
            u += w + 0.004
        for k in range(4):
            S.rect(-0.05 + k * 0.33, 0.30, 0.012, 0.60, scale(P.wall_top, 0.95), lift=0.0)
        S.glow(0.45, 0.25, 1.0, P.light, 0.20 if not dark else 0.12)
        S.rect(1.60, 0.30, 0.9, 0.58, mix(P.wall_bot, P.accent, 0.10), lift=0.0)             # wall art panels
        for (u, v, w, h, col) in ((1.30, 0.28, 0.20, 0.30, P.accent), (1.55, 0.26, 0.20, 0.24, P.accent2), (1.80, 0.30, 0.18, 0.32, P.accent_light)):
            S.rect(u, v, w, h, mix(col, P.wall_bot, 0.45 if dark else 0.15), lift=0.0, alpha=0.9)
        for u in (0.55, 0.95, 1.35, 1.75):
            S.glow(u, 0.0, 0.35, (1.0, 0.97, 0.88), 0.55)
        S.bokeh(6, 0.0, 0.05, 2.0, 0.45, [(1.0, 0.97, 0.88), P.accent_light], 0.012, 0.035, 0.28)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # light oak floor strip behind the table (sharp, so the chairs stand out against it), then the board and chairs
    floor = mix(P.floor_top, P.floor_bot, 0.45) if not dark else scale(mix(P.floor_top, P.floor_bot, 0.5), 1.25)
    S.wood(-5.0, 0.60, 7.0, 0.76, floor, plank=0.08, grain=0.5)
    S.soft(1.1, 0.76, 1.4, 0.07, BLACK, 0.34, 1.5)
    S.soft(1.14, 0.70, 0.9, 0.10, P.light, 0.16 if not dark else 0.10, 1.6, add=True)
    S.put("pro_con_chair", 0.68, 0.78, 0.40, color=P, shadow_alpha=0.34)
    S.put("pro_con_chair", 1.60, 0.78, 0.38, color=P, shadow_alpha=0.34)
    S.put("pro_con_board", 1.14, 0.77, 0.58, color=P, subject=True, shadow_alpha=0.30)
    # glossy slate boardroom table: veneer panels, a lit metal edge, window reflections
    top = mix(P.accent, WHITE, 0.40) if not dark else mix(P.accent_dark, P.ink, 0.45)
    for k in range(9):                                                    # stepped gradient: lit far edge, darker near the viewer
        t = k / 8.0
        S.rect(1.0, 0.77 + 0.1 + k * 0.205, 14.0, 0.215, mix(mix(top, WHITE, 0.07), scale(top, 0.62), t), lift=0.0, soft=0.4)
    for vv in (1.12, 1.58, 2.05):                                         # veneer seams
        S.line(-5.0, vv, 7.0, vv, 0.003, scale(top, 0.55), 0.35)
    S.rect(1.0, 0.77, 14.0, 0.012, mix(top, WHITE, 0.50), lift=0.0)
    S.rect(1.0, 0.785, 14.0, 0.006, scale(top, 0.50), lift=0.0, alpha=0.7)
    S.soft(0.55, 0.90, 0.6, 0.09, P.light, 0.26 if not dark else 0.18, 1.5, add=True, angle=-4)
    S.soft(1.50, 0.95, 0.7, 0.08, P.light, 0.20 if not dark else 0.14, 1.5, add=True, angle=-4)
    S.put("pro_con_laptop", 0.88, 0.95, 0.26, color=P, shadow_alpha=0.34)
    S.put("pro_con_laptop", 1.44, 0.95, 0.26, color=P, shadow_alpha=0.34)
    S.put("pro_con_papers", 1.14, 1.04, 0.22, color=P, shadow_alpha=0.30)
    S.put("digedu_mug", 0.72, 1.03, 0.08, color=(0.96, 0.96, 0.97), framed=False)
    S.put("digedu_mug", 1.60, 1.03, 0.08, color=mix(P.accent_light, WHITE, 0.5), framed=False)
    S.focus("detail", 1.12, 0.46)
    with S.near():
        S.circle(0.55, 0.98, 0.04, P.accent_light, alpha=0.35, lift=0)
        S.circle(1.66, 0.40, 0.05, mix(P.accent, WHITE, 0.4), alpha=0.22, lift=0)


# ====================================================================================================== RECRUITMENT
SKINS = ((0.93, 0.74, 0.60), (0.80, 0.58, 0.42), (0.66, 0.45, 0.32), (0.96, 0.80, 0.68))


def _resume_sheet(c, f, acc, rng, big=False):
    f.tint(0, 0, 1, 1, PAPER, 1.0)
    f.tint(0, 0, 0.32, 1, mix(acc, WHITE, 0.82), 1.0)
    f.tint(0, 0.78, 1, 1, mix(acc, (0.0, 0.1, 0.1), 0.15), 1.0)
    ph = f.p(0.16, 0.66)
    c.ellipse(ph[0], ph[1], 0.075, 0.07, mix(acc, WHITE, 0.55), lift=0.1)
    c.ellipse(ph[0], ph[1] + 0.02, 0.026, 0.026, SKINS[0], lift=0.2)
    c.ellipse(ph[0], ph[1] - 0.04, 0.05, 0.034, SKINS[0], lift=0.1)
    f.line(0.38, 0.89, 0.86, 0.89, 0.012, WHITE, 0.95)
    f.line(0.38, 0.83, 0.66, 0.83, 0.006, mix(acc, WHITE, 0.6), 0.9)
    for k in range(4):                                                                  # skill bars in the side column
        f.line(0.06, 0.48 - k * 0.09, 0.26, 0.48 - k * 0.09, 0.006, (0.75, 0.80, 0.82), 0.9)
        f.line(0.06, 0.48 - k * 0.09, 0.06 + 0.20 * (0.45 + 0.5 * rng.random()), 0.48 - k * 0.09, 0.008, acc, 1.0)
    for sec, (b0, n) in enumerate(((0.68, 3), (0.38, 4))):                              # sections with a heading and text lines
        f.line(0.38, b0, 0.58, b0, 0.010, acc, 1.0)
        for k in range(n):
            f.line(0.38, b0 - 0.07 - k * 0.065, 0.92 - (0.25 if k % 2 else 0.0) * rng.random() - 0.04, b0 - 0.07 - k * 0.065, 0.0045, (0.45, 0.48, 0.52), 0.75)


@sprop("pro_rec_resume", aspect=2.3, fill=0.72)
def rec_resume(c, color):
    acc = _acc(color, "accent", (0.0, 0.54, 0.48))
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.42, 0.34)
    # slim charcoal folder under the resume (not a big coloured mat), a thin accent spine, then the magnifier over it
    fol = mix(acc, (0.10, 0.12, 0.14), 0.80)
    mat = _Flat(c, -0.69, -0.022, 1.08, 0.0, 0.21, 0.66)
    mat.tint(0, 0, 1, 1, fol, 1.0)
    mat.tint(0, 0, 0.02, 1, mix(acc, WHITE, 0.15), 1.0)
    mat.line(0.0, 0.0, 1.0, 0.0, 0.006, mix(fol, WHITE, 0.3), 0.6)
    f = _Flat(c, -0.64, 0.05, 0.98, 0.0, 0.20, 0.54)
    _resume_sheet(c, f, acc, rng)
    f.line(0, 0, 1, 0, 0.004, (0.8, 0.8, 0.78), 0.8)
    # magnifier: brass ring, glass with enlarged detail, handle
    lu, lv, R = 0.12, 0.40, 0.255
    c.line(lu + 0.18, lv - 0.18, 0.58, 0.04, 0.060, (0.10, 0.10, 0.12), 1.0)
    c.line(lu + 0.18 - 0.012, lv - 0.17, 0.57, 0.05, 0.020, (0.45, 0.48, 0.55), 0.7)
    c.line(lu + 0.17, lv - 0.16, 0.28, lv - 0.26, 0.035, BRASS, 1.0)
    soft_disc(c, lu + 0.08, lv - 0.10, R * 1.0, R * 0.55, BLACK, 0.20, 1.4)
    c.ellipse(lu, lv, R * 1.0, R * 0.96, scale(BRASS, 0.55), lift=0)
    c.ellipse(lu, lv + 0.004, R * 0.98, R * 0.94, mix(BRASS, WHITE, 0.25), lift=0.2)
    c.ellipse(lu, lv, R * 0.86, R * 0.82, (0.97, 0.97, 0.95), lift=0.0)
    for k, (w, col) in enumerate(((0.36, acc), (0.22, mix(acc, WHITE, 0.55)), (0.40, (0.40, 0.44, 0.50)), (0.30, (0.40, 0.44, 0.50)), (0.36, (0.40, 0.44, 0.50)))):
        c.line(lu - 0.20, lv + 0.13 - k * 0.075, lu - 0.20 + w, lv + 0.13 - k * 0.075, 0.020 if k == 0 else 0.013, col, 0.95)
    c.ellipse(lu + 0.12, lv - 0.14, 0.07, 0.05, mix(acc, WHITE, 0.55), lift=0.1, alpha=0.7)
    c.glow(lu, lv, R * 1.2, WHITE, 0.10)
    soft_disc(c, lu - 0.09, lv + 0.10, 0.14, 0.07, WHITE, 0.55, 1.2, 25, add=True)
    craft.arc(c, lu, lv, R * 0.80, R * 0.76, 110, 170, 0.014, WHITE, 0.75, 8)


@sprop("pro_rec_cvs", aspect=1.3, fill=0.62)
def rec_cvs(c, color):
    acc = _acc(color, "accent", (0.0, 0.54, 0.48))
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.30, 0.38)
    v = 0.0
    for k in range(7):                                                                  # a stack of CVs with slightly shifted edges
        du = rng.uniform(-0.03, 0.03)
        side = (0.80, 0.80, 0.76) if k % 2 else (0.92, 0.91, 0.87)
        box3d(c, du, v, 0.66, 0.036, 0.40, mix(PAPER, side, 0.4), (0.99, 0.985, 0.97), (0.80, 0.78, 0.74), lift=0.03, dx=0.5, dy=0.5)
        v += 0.038
    for k, col in enumerate((acc, (0.95, 0.65, 0.2), mix(acc, WHITE, 0.4))):                # coloured section tabs
        _crect(c, 0.33 + 0.011 * k, 0.05 + k * 0.07, 0.04, 0.045, col, r=0.004, lift=0.1)
    ox, oy = 0.20, 0.20
    f = _Flat(c, -0.30 + 0.06, v, 0.58, 0.0, 0.16, 0.30)
    f.quad(0, 0, 1, 1, PAPER, lift=0.0)
    f.quad(0.0, 0.78, 1, 1, acc, lift=0.0)
    f.line(0.10, 0.60, 0.70, 0.60, 0.008, scale(acc, 0.6), 1.0)
    for k in range(3):
        f.line(0.10, 0.44 - k * 0.14, 0.90 - 0.2 * (k % 2), 0.44 - k * 0.14, 0.0045, (0.45, 0.48, 0.52), 0.8)
    ph = f.p(0.84, 0.66)
    c.ellipse(ph[0], ph[1], 0.03, 0.026, SKINS[1], lift=0.2)
    clip = f.p(0.12, 1.0)
    for dw in (0.0, 0.012):                                                              # paper clip
        c.rect(clip[0] + 0.02, clip[1] - 0.04 + dw, 0.026, 0.11, (0.78, 0.80, 0.84), r=0.012, lift=0.3, alpha=0.9)
    nt = f.p(0.72, 0.28)
    c.rect(nt[0], nt[1], 0.12, 0.10, (1.0, 0.86, 0.32), lift=0.08, r=0.004)                  # sticky note
    c.text("HIRE", nt[0], nt[1] - 0.004, 0.030, (0.75, 0.15, 0.15), 0.18)


def _badge(c, u, v, ang, acc, skin, wd=0.30):
    g = _G(c, u, v, ang)
    g.rect(0.0, 0.0, wd + 0.012, wd * 1.45, scale(acc, 0.55), r=0.03, alpha=0.5)
    g.rect(0.0, 0.0, wd, wd * 1.40, (0.97, 0.97, 0.95), r=0.03, lift=0.06)
    g.rect(0.0, wd * 0.48, wd, wd * 0.44, acc, r=0.03, lift=0.12)
    g.rect(0.0, wd * 0.36, wd, wd * 0.22, acc, lift=0.12)
    g.rect(0.0, wd * 0.60, wd * 0.34, 0.012, (0.0, 0.0, 0.0), r=0.006, alpha=0.30)              # lanyard slot
    g.circle(0.0, wd * 0.05, wd * 0.24, mix(acc, WHITE, 0.8), lift=0.1)
    g.circle(0.0, wd * 0.11, wd * 0.09, skin, lift=0.2)
    g.rect(0.0, -wd * 0.04, wd * 0.28, wd * 0.12, skin, r=0.02, lift=0.1)
    g.rect(0.0, -wd * 0.36, wd * 0.62, wd * 0.07, (0.2, 0.22, 0.28), r=0.01, alpha=0.9)
    g.rect(0.0, -wd * 0.48, wd * 0.42, wd * 0.045, (0.55, 0.58, 0.62), r=0.01, alpha=0.9)
    return g


@sprop("pro_rec_badges", aspect=1.15, fill=0.95)
def rec_badges(c, color):
    acc = _acc(color, "accent", (0.0, 0.54, 0.48))
    ao(c, 0.0, 0.0, 0.9, 0.22, 0.34)
    lan = mix(acc, (0.0, 0.08, 0.1), 0.35)
    for u, ang, skin, tone in ((-0.20, 8, SKINS[2], 0.0), (0.20, -7, SKINS[0], 0.25)):
        col = mix(acc, WHITE, tone) if tone else acc
        # strap runs from the back of the badge up out of the picture, lit edge on it
        c.line(u, 0.60, u + (0.05 if u < 0 else -0.05), 1.0, 0.040, lan, 1.0)
        c.line(u - 0.012, 0.62, u - 0.006 + (0.05 if u < 0 else -0.05), 1.0, 0.012, mix(lan, WHITE, 0.4), 0.6)
        _badge(c, u, 0.34, ang, col, skin)
        c.circle(u, 0.60, 0.014, STEELC, lift=0.3)
    # a coiled lanyard lying in front
    for k in range(4):
        craft.arc(c, 0.0, 0.035 + k * 0.004, 0.44 - k * 0.03, 0.10 - k * 0.006, 190, 350, 0.030, lan, 1.0, 10)
    craft.arc(c, 0.0, 0.04, 0.44, 0.10, 215, 330, 0.010, mix(lan, WHITE, 0.4), 0.6, 8)


@sprop("pro_rec_shake", aspect=0.85, fill=1.0)
def rec_shake(c, color):
    acc = _acc(color, "accent", (0.0, 0.54, 0.48))
    ao(c, 0.0, 0.0, 0.8, 0.20, 0.34)
    c.ellipse(0.0, 0.03, 0.40, 0.40 * 0.34, scale(KRAFT, 0.55), lift=0)
    craft.hshade_box(c, 0.0, 0.04, 0.78, 0.045, mix(KRAFT, WHITE, 0.2), scale(KRAFT, 0.55), r=0.015)
    disc(c, 0.0, 0.065, 0.39, mix(KRAFT, WHITE, 0.15), 0.34, 0.08)
    suit_a, suit_b = (0.16, 0.20, 0.34), mix(acc, (0.0, 0.05, 0.05), 0.2)
    for sign, suit, skin, hair, tie in ((-1, suit_a, SKINS[0], (0.15, 0.10, 0.08), acc), (1, suit_b, SKINS[2], (0.08, 0.06, 0.06), (0.95, 0.75, 0.2))):
        u = sign * 0.20
        for du in (-0.04, 0.04):
            c.rect(u + du, 0.20, 0.06, 0.26, scale(suit, 0.6), r=0.012, lift=0.15)           # legs
        c.rect(u, 0.55, 0.22, 0.40, suit, r=0.06, lift=0.22)                                  # torso
        c.poly([(u - 0.04, 0.72), (u + 0.04, 0.72), (u, 0.52)], (0.97, 0.97, 0.97), lift=0.0)
        c.poly([(u - 0.012, 0.69), (u + 0.012, 0.69), (u + 0.018, 0.55), (u, 0.50), (u - 0.018, 0.55)], tie, lift=0.1)
        c.circle(u, 0.84, 0.075, skin, lift=0.2)
        c.ellipse(u, 0.89, 0.078, 0.05, hair, lift=0.15)
        soft_disc(c, u - 0.02 * sign, 0.86, 0.03, 0.02, WHITE, 0.4, 1.2, add=True)
        c.line(u + sign * 0.09, 0.66, sign * 0.02, 0.52, 0.062, suit, 1.0)                    # arm reaching to the middle
        c.line(u - sign * 0.10, 0.68, u - sign * 0.13, 0.46, 0.058, scale(suit, 0.8), 1.0)    # other arm hanging
        c.circle(u - sign * 0.13, 0.43, 0.026, skin, lift=0.2)
    c.ellipse(0.0, 0.52, 0.06, 0.036, SKINS[1], lift=0.2)
    c.line(-0.05, 0.52, 0.05, 0.52, 0.006, scale(SKINS[1], 0.7), 0.8)


@niche("recruitment", "Recruitment / staffing agency", subjects=("pro_rec_resume",),
       strong=("recruitment agency", "staffing", "manpower", "hiring agency", "placement consultancy", "job placement", "recruitment consultancy",
               "staffing agency", "hr consultancy", "manpower consultancy", "job consultancy", "talent acquisition", "भर्ती", "रिक्रूटमेंट", "नौकरी दिलाने",
               "placement agency", "naukri"),
       weak=("hiring", "jobs", "resume", "cv", "interview", "candidate", "career", "hr"),
       accent="#00897b", mood="light", group="professional")
def recruitment(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.55)
        S.glow(1.2, 0.25, 1.0, P.accent_light, 0.24 if dark else 0.12)
        st, sb = _sky(P)
        S.window(-0.10, 0.22, 0.34, 0.42, st, sb, frame=mix(P.wall_top, WHITE, 0.4))
        # a lit "we are hiring" sign, and a deep accent feature wall with a job board that frames the pale paper in front of it
        S.rect(0.55, 0.22, 0.60, 0.20, P.accent if not dark else scale(P.accent, 0.8), r=0.01, lift=0.05)
        S.text("WE ARE HIRING", 0.55, 0.22, 0.06, WHITE, 0.2)
        S.glow(0.55, 0.22, 0.7, P.accent_light, 0.25 if dark else 0.10)
        deep = mix(P.accent_dark, P.ink, 0.25) if not dark else scale(P.accent_dark, 0.55)
        S.gradient_rect(1.02, -0.20, 2.40, 0.55, mix(deep, WHITE, 0.08), scale(deep, 0.78))
        S.rect(1.02, 0.20, 0.02, 0.75, mix(deep, WHITE, 0.30), lift=0.0, alpha=0.7)
        cols = (P.accent, P.accent2, P.accent_light, (0.96, 0.72, 0.25), (0.95, 0.5, 0.45), WHITE)
        for i in range(5):
            for j in range(3):
                col = cols[rng.randrange(len(cols))]
                cu, cv = 1.22 + i * 0.22 + rng.uniform(-0.012, 0.012), 0.02 + j * 0.17
                S.rect(cu, cv, 0.17, 0.13, mix(col, P.wall_bot, 0.30 if dark else 0.05), lift=0.0)
                S.circle(cu, cv - 0.02, 0.026, SKINS[rng.randrange(4)], lift=0.0)
                S.rect(cu, cv + 0.035, 0.12, 0.012, scale(col, 0.6), lift=0.0, alpha=0.7)
        S.pendant(0.30, -0.1, 0.17, (1.0, 0.94, 0.78), 0.09)
        S.pendant(1.0, -0.1, 0.12, (1.0, 0.94, 0.78), 0.08)
        if dark:                                                      # warm wall-washers and spot pools in the dark mood
            S.glow(1.55, 0.18, 0.8, (1.0, 0.86, 0.58), 0.30)
            S.glow(0.55, 0.30, 0.9, P.accent_light, 0.22)
            S.pendant(1.40, -0.1, 0.22, (1.0, 0.88, 0.62), 0.10)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [P.accent_light, (1.0, 0.95, 0.8)], 0.012, 0.04, 0.3)
        S.floor(0.55, P.floor_top, P.floor_bot)
    # dark walnut desk: the pale papers and the teal accents stand out against it
    S.soft(1.12, 0.66, 1.1, 0.12, (1.0, 0.95, 0.82), 0.16 if not dark else 0.26, 1.5, add=True)
    desk = mix(P.surface, (0.40, 0.27, 0.19), 0.72) if not dark else scale(P.surface, 0.72)
    S.wood(-5.0, 0.55, 7.0, 2.6, desk, plank=0.13, grain=0.7)
    S.rect(1.0, 0.55, 14.0, 0.008, scale(desk, 0.45), lift=0.0)
    S.rect(1.0, 0.565, 14.0, 0.012, mix(desk, WHITE, 0.35), lift=0.0, alpha=0.45)
    S.soft(0.55, 0.88, 0.45, 0.05, (1.0, 0.95, 0.82), 0.12 if not dark else 0.10, 1.5, add=True, angle=-4)
    S.put("digedu_plant", 0.52, 0.78, 0.22, color=mix(P.accent_light, WHITE, 0.6), shadow_alpha=0.28, framed=False)
    S.put("pro_rec_shake", 1.54, 0.79, 0.34, color=P, shadow_alpha=0.32)
    S.put("pro_rec_cvs", 0.76, 0.93, 0.25, color=P, shadow_alpha=0.30)
    S.put("pro_rec_resume", 1.08, 1.0, 0.42, color=P, subject=True, shadow_alpha=0.26)
    S.put("pro_rec_badges", 1.33, 1.08, 0.17, color=P, shadow_alpha=0.30)
    S.put("digedu_mug", 1.66, 0.98, 0.10, color=(0.96, 0.96, 0.97), shadow_alpha=0.28, framed=False)
    S.soft(1.12, 0.88, 0.6, 0.18, (1.0, 0.95, 0.8), 0.16 if not dark else 0.42, 1.6, add=True)
    S.focus("detail", 1.14, 0.86)
    with S.near():
        S.circle(0.55, 0.98, 0.04, P.accent_light, alpha=0.40, lift=0)
        S.circle(1.64, 0.42, 0.05, mix(P.accent, WHITE, 0.4), alpha=0.22, lift=0)


# ====================================================================================================== COWORKING
def _kan_ui(g, acc):
    rng = g.c.rng
    g.rect(0, 0, 1.26, 0.70, (0.94, 0.95, 0.96))
    g.rect(0, 0.315, 1.26, 0.07, mix(acc, (0.0, 0.1, 0.1), 0.2))
    g.circle(-0.57, 0.315, 0.018, WHITE)
    g.rect(-0.20, 0.315, 0.30, 0.016, WHITE, r=0.008, alpha=0.8)
    g.circle(0.55, 0.315, 0.022, mix(acc, WHITE, 0.5))
    g.circle(0.49, 0.315, 0.022, (0.95, 0.65, 0.25))
    tags = (acc, (0.95, 0.65, 0.25), (0.90, 0.36, 0.42), (0.40, 0.55, 0.90))
    for i in range(3):
        u = -0.40 + i * 0.40
        g.rect(u, -0.04, 0.36, 0.58, (0.89, 0.91, 0.93), r=0.014)
        g.rect(u - 0.08, 0.20, 0.14, 0.016, (0.45, 0.50, 0.56), r=0.008)
        for j in range(3 - (i == 2)):
            v = 0.10 - j * 0.155
            g.rect(u, v - 0.004, 0.32, 0.13, (0.0, 0.0, 0.1), r=0.014, alpha=0.08)
            g.rect(u, v, 0.32, 0.13, WHITE, r=0.014)
            g.rect(u - 0.04, v + 0.035, 0.18 + 0.06 * rng.random(), 0.014, (0.35, 0.38, 0.46), r=0.007)
            g.rect(u - 0.06, v + 0.005, 0.12, 0.012, (0.72, 0.75, 0.80), r=0.006)
            g.rect(u - 0.115, v - 0.04, 0.07, 0.022, tags[(i + j) % 4], r=0.011)
            g.circle(u + 0.125, v - 0.04, 0.017, tags[(i * 2 + j + 1) % 4])


@sprop("pro_cow_laptop", aspect=1.7, fill=0.92)
def cow_laptop(c, color):
    _laptop(c, _kan_ui, _acc(color, "accent", (0.15, 0.65, 0.60)), body=(0.80, 0.82, 0.85))


@sprop("pro_cow_planter", aspect=2.3, fill=0.62)
def cow_planter(c, color):
    rng = c.rng
    wood = (0.70, 0.52, 0.34)
    ao(c, 0.0, 0.0, 1.5, 0.22, 0.38)
    # leaves behind the box
    for k in range(16):
        u = rng.uniform(-0.62, 0.62)
        _leaf(c, u, 0.20, rng.uniform(0.22, 0.42), rng.uniform(40, 140) + (u * 20), (0.16 + rng.random() * 0.12, 0.44 + rng.random() * 0.18, 0.26), 0.5)
    craft.hshade_box(c, 0.0, 0.10, 1.40, 0.20, mix(wood, WHITE, 0.15), scale(wood, 0.55), r=0.015)
    for k in range(4):
        c.line(-0.69, 0.04 + k * 0.045, 0.69, 0.04 + k * 0.045, 0.0035, scale(wood, 0.6), 0.5)
    c.rect(0.0, 0.205, 1.42, 0.022, mix(wood, WHITE, 0.25), lift=0.2, r=0.006)
    for k in range(9):                                                                   # soil and succulents in front
        u = -0.60 + k * 0.15 + rng.uniform(-0.02, 0.02)
        cols = ((0.30, 0.58, 0.40), (0.44, 0.68, 0.50), (0.60, 0.74, 0.55))
        for j in range(7):
            a = 90 + (j - 3) * 26
            _leaf(c, u, 0.215, rng.uniform(0.08, 0.13), a, cols[(k + j) % 3], 0.42, vein=False)
    soft_disc(c, -0.25, 0.14, 0.5, 0.05, WHITE, 0.22, 1.3, add=True)


@sprop("pro_cow_booth", aspect=0.62, fill=1.0)
def cow_booth(c, color):
    acc = _acc(color, "accent", (0.15, 0.65, 0.60))
    ao(c, 0.04, 0.0, 0.66, 0.20, 0.36)
    W, H = 0.50, 0.96
    # interior: warm wood back wall, a small ledge table, stool and a pendant light
    c.rect(0.0, H / 2 + 0.02, W, H, scale(acc, 0.50), r=0.03, lift=0.12)
    c.rect(0.0, 0.50, W - 0.08, H - 0.14, mix((0.66, 0.46, 0.30), acc, 0.12), r=0.01, lift=0.18)
    for k in range(8):
        c.line(-0.21 + k * 0.06, 0.07, -0.21 + k * 0.06, 0.92, 0.003, (0.40, 0.26, 0.16), 0.4)
    c.glow(0.0, 0.62, 0.65, (1.0, 0.82, 0.50), 0.65)
    c.line(0.0, 0.93, 0.0, 0.76, 0.006, (0.2, 0.2, 0.2), 0.9)
    c.poly([(-0.07, 0.70), (0.07, 0.70), (0.035, 0.77), (-0.035, 0.77)], (0.95, 0.80, 0.45), lift=0.1)
    c.ellipse(0.0, 0.695, 0.05, 0.014, (1.0, 0.95, 0.75), lift=0.0)
    c.rect(0.0, 0.40, 0.36, 0.022, (0.88, 0.86, 0.82), lift=0.3)                               # ledge with a phone
    c.rect(-0.08, 0.425, 0.05, 0.03, (0.1, 0.1, 0.12), r=0.006, lift=0.1)
    c.ellipse(0.0, 0.14, 0.12, 0.12 * 0.4, scale(acc, 0.6), lift=0)                             # stool
    c.rect(0.0, 0.09, 0.03, 0.14, (0.6, 0.6, 0.64), lift=0.3)
    c.ellipse(0.0, 0.175, 0.13, 0.055, mix(acc, WHITE, 0.2), lift=0.2)
    # glass front: faint reflections, a vertical door frame and the steel posts
    _fill_quad(c.cv, [(c.X(-0.20), c.Y(0.92)), (c.X(0.02), c.Y(0.92)), (c.X(-0.14), c.Y(0.08)), (c.X(-0.22), c.Y(0.08))], WHITE, 0.13)
    _fill_quad(c.cv, [(c.X(0.10), c.Y(0.92)), (c.X(0.16), c.Y(0.92)), (c.X(0.08), c.Y(0.08)), (c.X(0.04), c.Y(0.08))], WHITE, 0.09)
    for u in (-W / 2 + 0.012, W / 2 - 0.012):
        c.rect(u, H / 2 + 0.02, 0.026, H, scale(acc, 0.65), lift=0.25)
        c.rect(u - 0.006, H / 2 + 0.02, 0.006, H, mix(acc, WHITE, 0.5), lift=0, alpha=0.6)
    c.rect(0.0, 0.985, W + 0.04, 0.05, scale(acc, 0.7), r=0.012, lift=0.25)
    c.rect(0.0, 0.016, W + 0.03, 0.03, scale(acc, 0.55), lift=0.2)
    c.rect(0.14, 0.50, 0.012, 0.88, scale(acc, 0.65), lift=0.1, alpha=0.8)
    c.rect(0.20, 0.52, 0.012, 0.10, WHITE, r=0.005)                                              # door handle
    c.rect(0.0, 1.0, 0.20, 0.036, (0.10, 0.12, 0.12), r=0.006, lift=0.1)
    c.text("CALL", 0.0, 1.0, 0.022, (1.0, 0.92, 0.7), 0.2)
    c.glow(0.0, 1.0, 0.4, (1.0, 0.85, 0.5), 0.12)


@niche("coworking", "Coworking space", subjects=("pro_cow_booth",),
       strong=("coworking space", "co-working", "shared office", "hot desk", "cowork", "coworking", "co working space", "shared workspace",
               "office space for rent", "flexible workspace", "को-वर्किंग", "कोवर्किंग", "शेयर्ड ऑफिस", "cowork space", "private cabin", "hot desks"),
       weak=("desk", "workspace", "freelancer", "startup", "community", "meeting room", "membership", "work cafe"),
       accent="#26a69a", mood="light", group="professional")
def coworking(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        # exposed brick wall
        brick = mix((0.72, 0.36, 0.26), P.wall_bot, 0.30 if not dark else 0.62)
        S.rect(1.0, 0.29, 8.0, 0.60, brick, lift=0.0)
        v = 0.0
        row = 0
        while v < 0.60:
            u = -1.0 - (0.04 if row % 2 else 0.0)
            while u < 3.0:
                S.rect(u + 0.035, v + 0.015, 0.068, 0.027, scale(brick, rng.uniform(0.82, 1.18)), lift=0.0)
                u += 0.074
            v += 0.031
            row += 1
        # steel-framed industrial window with sky
        st, sb = _sky(P)
        S.gradient_rect(0.05, 0.02, 0.85, 0.56, st, sb)
        S.glow(0.45, 0.28, 0.9, P.light, 0.35 if not dark else 0.14)
        for k in range(5):
            S.rect(0.05 + k * 0.20, 0.29, 0.010, 0.56, (0.10, 0.11, 0.12), lift=0.0)
        for k in range(4):
            S.rect(0.45, 0.02 + k * 0.18, 0.82, 0.010, (0.10, 0.11, 0.12), lift=0.0)
        # hanging plants and edison bulbs
        for (u, v) in ((1.10, 0.03), (1.34, 0.02), (1.95, 0.03)):
            S.circle(u, v + 0.05, 0.05, (0.20, 0.50, 0.28) if not dark else (0.10, 0.28, 0.16), lift=0.0)
            for k in range(4):
                S.line(u + (k - 1.5) * 0.03, v + 0.06, u + (k - 1.5) * 0.04, v + 0.20 + 0.04 * k, 0.012, (0.22, 0.52, 0.30) if not dark else (0.12, 0.30, 0.18))
        for u in (0.60, 0.95, 1.55, 1.80):
            S.pendant(u, -0.1, 0.12 + 0.05 * rng.random(), (1.0, 0.82, 0.50), 0.05)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [(1.0, 0.85, 0.55), P.accent_light], 0.012, 0.04, 0.3)
        S.floor(0.58, (0.62, 0.62, 0.64) if not dark else (0.14, 0.15, 0.17), (0.50, 0.50, 0.52) if not dark else (0.08, 0.09, 0.10))
    # polished concrete floor between the brick wall and the shared table
    S.soft(1.1, 0.70, 1.4, 0.10, WHITE if not dark else (1.0, 0.85, 0.55), 0.22, 1.5, add=True)
    S.put("digedu_plant", 0.62, 0.76, 0.32, color=mix(P.accent_light, WHITE, 0.4), shadow_alpha=0.28)
    S.put("pro_cow_booth", 1.44, 0.76, 0.60, color=P, subject=True, shadow_alpha=0.36)
    # one long shared table of pale oak
    oak = mix(P.surface, (0.95, 0.85, 0.68), 0.35) if not dark else scale(P.surface, 0.95)
    S.wood(-5.0, 0.78, 7.0, 2.6, oak, plank=0.30, grain=0.35)
    S.rect(1.0, 0.78, 14.0, 0.012, mix(oak, WHITE, 0.30), lift=0.0)
    S.rect(1.0, 0.792, 14.0, 0.014, scale(oak, 0.62), lift=0.0, alpha=0.8)
    S.soft(1.1, 0.95, 1.3, 0.18, (1.0, 0.9, 0.7), 0.14 if not dark else 0.30, 1.5, add=True)
    S.put("pro_cow_planter", 1.04, 0.87, 0.19, color=P, shadow_alpha=0.30)
    S.put("pro_cow_laptop", 0.74, 0.98, 0.25, color=P, shadow_alpha=0.34)
    S.put("pro_cow_laptop", 1.38, 0.98, 0.25, color=P, shadow_alpha=0.34)
    S.put("digedu_mug", 1.10, 0.97, 0.075, color=mix(P.accent_light, WHITE, 0.5))
    S.put("digedu_notebook", 0.98, 0.94, 0.07, color=mix(P.accent, P.ink, 0.5))
    S.focus("detail", 1.30, 0.66)
    with S.near():
        S.circle(0.56, 0.98, 0.04, P.accent_light, alpha=0.35, lift=0)
        S.circle(1.64, 0.40, 0.05, (1.0, 0.8, 0.5), alpha=0.22, lift=0)


# ====================================================================================================== ASTROLOGY
GOLD = (0.93, 0.74, 0.30)
NAVY = (0.07, 0.06, 0.20)
MAROON = (0.52, 0.10, 0.10)


def _glyph(c, k, u, v, r, col):
    """Twelve tiny sign-like marks (not real zodiac glyphs): dot, ring, bars, crescent, triangle, ..."""
    m = k % 6
    if m == 0:
        c.circle(u, v, r * 0.55, col, lift=0.1)
    elif m == 1:
        c.circle(u, v, r * 0.80, col, lift=0.1)
        c.circle(u, v, r * 0.45, NAVY, lift=0)
    elif m == 2:
        c.poly([(u - r * 0.8, v - r * 0.6), (u + r * 0.8, v - r * 0.6), (u, v + r * 0.9)], col, lift=0.1)
    elif m == 3:
        c.circle(u, v, r * 0.85, col, lift=0.1)
        c.circle(u + r * 0.45, v + r * 0.1, r * 0.75, mix(NAVY, (0.25, 0.15, 0.45), 0.3), lift=0)
    elif m == 4:
        c.line(u - r * 0.7, v + r * 0.6, u, v - r * 0.7, r * 0.28, col, 1.0)
        c.line(u + r * 0.7, v + r * 0.6, u, v - r * 0.7, r * 0.28, col, 1.0)
        c.line(u - r * 0.6, v - r * 0.1, u + r * 0.6, v - r * 0.1, r * 0.25, col, 1.0)
    else:
        c.line(u - r * 0.8, v, u + r * 0.8, v, r * 0.28, col, 1.0)
        c.line(u, v - r * 0.8, u, v + r * 0.8, r * 0.28, col, 1.0)
        c.circle(u, v, r * 0.35, col, lift=0.1)


@sprop("pro_astro_wheel", aspect=1.0, fill=1.0)
def astro_wheel(c, color):
    acc = _acc(color, "accent", (0.37, 0.21, 0.69))
    rng = c.rng
    cx, cy, R = 0.0, 0.57, 0.47
    ao(c, 0.0, 0.0, 0.8, 0.24, 0.40)
    for u, v2 in ((-0.26, 0.04), (0.26, 0.04)):                                              # brass easel legs and shelf
        c.line(u * 0.3, 0.20, u, v2, 0.030, scale(BRASS, 0.55), 1.0)
        c.line(u * 0.3 - 0.006, 0.20, u - 0.006, v2, 0.012, mix(BRASS, WHITE, 0.3), 0.8)
    c.rect(0.0, 0.07, 0.62, 0.035, mix(BRASS, WHITE, 0.1), r=0.01, lift=0.25)
    c.circle(cx, cy, R + 0.02, scale(GOLD, 0.40), lift=0.0)
    c.circle(cx, cy, R, GOLD, lift=0.26)
    c.circle(cx, cy, R * 0.955, scale(GOLD, 0.55), lift=0.2)
    c.circle(cx, cy, R * 0.93, mix(NAVY, acc, 0.18), lift=0.14)
    c.circle(cx, cy, R * 0.70, scale(GOLD, 0.9), lift=0.2)
    c.circle(cx, cy, R * 0.685, mix(NAVY, acc, 0.38), lift=0.10)
    # sign band: 12 segments with marks
    for k in range(12):
        a = math.radians(15 + k * 30)
        c.line(cx + math.cos(a) * R * 0.70, cy + math.sin(a) * R * 0.70, cx + math.cos(a) * R * 0.93, cy + math.sin(a) * R * 0.93, 0.008, GOLD, 0.95)
        am = math.radians(30 + k * 30)
        _glyph(c, k, cx + math.cos(am) * R * 0.815, cy + math.sin(am) * R * 0.815, 0.040, mix(GOLD, WHITE, 0.2))
    for k in range(72):                                                                       # degree ticks on the rim
        a = math.radians(k * 5)
        c.line(cx + math.cos(a) * R * 0.945, cy + math.sin(a) * R * 0.945, cx + math.cos(a) * R * 0.925, cy + math.sin(a) * R * 0.925, 0.0035, GOLD, 0.55)
    # inner chart: starry disc, hexagram, aspect lines, planets and a sun
    c.circle(cx, cy, R * 0.60, mix(NAVY, acc, 0.12), lift=0.0)
    soft_disc(c, cx, cy, R * 0.6, R * 0.6, mix(acc, WHITE, 0.2), 0.40, 1.3, add=True)
    for k in range(26):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * R * 0.58
        c.circle(cx + math.cos(a) * r, cy + math.sin(a) * r, rng.uniform(0.003, 0.007), WHITE, lift=0, alpha=rng.uniform(0.4, 0.9))
    for base in (90, 210, 330):
        pts = [(cx + math.cos(math.radians(base + i * 120)) * R * 0.54, cy + math.sin(math.radians(base + i * 120)) * R * 0.54) for i in range(4)]
        for p, q in zip(pts, pts[1:]):
            c.line(p[0], p[1], q[0], q[1], 0.007, GOLD, 0.9)
        if base == 90:
            break
    tri2 = [(cx + math.cos(math.radians(270 + i * 120)) * R * 0.54, cy + math.sin(math.radians(270 + i * 120)) * R * 0.54) for i in range(4)]
    for p, q in zip(tri2, tri2[1:]):
        c.line(p[0], p[1], q[0], q[1], 0.007, GOLD, 0.9)
    c.circle(cx, cy, R * 0.30, scale(GOLD, 0.55), lift=0.0)
    c.circle(cx, cy, R * 0.28, mix(NAVY, acc, 0.25), lift=0.1)
    for k in range(16):                                                                       # sun with rays
        a = math.radians(k * 22.5)
        c.line(cx + math.cos(a) * R * 0.10, cy + math.sin(a) * R * 0.10, cx + math.cos(a) * R * (0.22 if k % 2 == 0 else 0.17), cy + math.sin(a) * R * (0.22 if k % 2 == 0 else 0.17),
               0.007, GOLD, 0.95)
    c.circle(cx, cy, R * 0.10, mix(GOLD, WHITE, 0.2), lift=0.25)
    for ang, rad, col in ((40, 0.42, (0.95, 0.45, 0.55)), (160, 0.44, (0.45, 0.85, 0.80)), (250, 0.40, (0.98, 0.65, 0.25)), (320, 0.46, (0.55, 0.60, 1.0)), (110, 0.36, (0.9, 0.9, 0.6))):
        a = math.radians(ang)
        pu, pv = cx + math.cos(a) * R * rad, cy + math.sin(a) * R * rad
        c.glow(pu, pv, 0.07, col, 0.5)
        c.circle(pu, pv, 0.020, col, lift=0.2)
    craft.arc(c, cx, cy, R * 0.99, R * 0.99, 100, 165, 0.012, WHITE, 0.55, 10)
    soft_disc(c, cx - 0.16, cy + 0.18, 0.22, 0.12, WHITE, 0.13, 1.3, 30, add=True)
    c.glow(cx, cy, R * 1.5, GOLD, 0.10)


@sprop("pro_astro_ball", aspect=0.85, fill=1.0)
def astro_ball(c, color):
    acc = _acc(color, "accent", (0.37, 0.21, 0.69))
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.20, 0.42)
    # ornate brass stand: foot, stem with a ring, claw-like cup
    c.ellipse(0.0, 0.03, 0.30, 0.30 * TILT, scale(BRASS, 0.40), lift=0)
    disc(c, 0.0, 0.05, 0.29, BRASS, TILT, 0.2)
    craft.hshade_box(c, 0.0, 0.11, 0.14, 0.12, mix(BRASS, WHITE, 0.25), scale(BRASS, 0.40))
    c.ellipse(0.0, 0.11, 0.12, 0.04, mix(BRASS, WHITE, 0.3), lift=0.2)
    c.ellipse(0.0, 0.19, 0.22, 0.22 * 0.36, scale(BRASS, 0.55), lift=0.0)
    craft.hshade_box(c, 0.0, 0.21, 0.40, 0.05, mix(BRASS, WHITE, 0.2), scale(BRASS, 0.42), r=0.02)
    cx, cy, R = 0.0, 0.50, 0.29
    c.glow(cx, cy, R * 2.3, mix(acc, WHITE, 0.3), 0.42)
    c.circle(cx, cy, R, mix(acc, NAVY, 0.55), lift=0.12)
    c.circle(cx, cy, R * 0.97, mix(acc, (0.10, 0.04, 0.25), 0.35), lift=0.0)
    for col, du, dv, a, b, al, ang in (((0.20, 0.85, 0.90), -0.08, -0.04, 0.20, 0.10, 0.45, 30), ((0.95, 0.35, 0.75), 0.07, 0.06, 0.18, 0.09, 0.45, -35),
                                         ((0.60, 0.45, 1.0), 0.0, -0.10, 0.22, 0.10, 0.50, 5), ((1.0, 0.85, 0.5), 0.05, 0.10, 0.12, 0.06, 0.30, 60),
                                         ((0.35, 0.5, 1.0), -0.10, 0.08, 0.16, 0.08, 0.35, -60)):
        soft_disc(c, cx + du, cy + dv, a, b, col, al, 1.2, ang, add=True)
    for k in range(22):                                                                       # stars inside the ball
        ang, rr = rng.uniform(0, 6.28), math.sqrt(rng.random()) * R * 0.88
        sx, sy = cx + math.cos(ang) * rr, cy + math.sin(ang) * rr
        c.circle(sx, sy, rng.uniform(0.003, 0.0065), WHITE, lift=0, alpha=rng.uniform(0.5, 1.0))
        if k % 6 == 0:
            c.glow(sx, sy, 0.035, WHITE, 0.4)
    # refraction at the base, rim light and window reflection
    soft_disc(c, cx, cy - R * 0.72, R * 0.65, R * 0.20, (0.9, 0.8, 1.0), 0.55, 1.3, add=True)
    craft.arc(c, cx, cy, R * 0.96, R * 0.96, 195, 330, 0.014, mix(acc, WHITE, 0.6), 0.7, 10)
    soft_disc(c, cx - R * 0.42, cy + R * 0.45, R * 0.34, R * 0.20, WHITE, 0.55, 1.1, 35, add=True)
    c.rect(cx - R * 0.45, cy + R * 0.38, 0.06, 0.035, WHITE, r=0.01, alpha=0.40, lift=0)
    soft_disc(c, cx + R * 0.45, cy + R * 0.20, R * 0.12, R * 0.28, mix(acc, WHITE, 0.5), 0.25, 1.2, 0, add=True)


@sprop("pro_astro_tarot", aspect=1.35, fill=0.95)
def astro_tarot(c, color):
    acc = _acc(color, "accent", (0.37, 0.21, 0.69))
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.22, 0.36)
    for k, ang in enumerate((34, 17, 0, -17, -34)):
        g = _G(c, -0.02 * (k - 2) * 0.0, 0.04, ang)
        face = (k == 4)
        back = mix(NAVY, acc, 0.35 + 0.1 * (k % 2))
        g.rect(0.0, 0.46, 0.34, 0.56, scale(back, 0.4), r=0.02, alpha=0.55)
        g.rect(0.0, 0.47, 0.32, 0.54, (0.94, 0.88, 0.70) if face else GOLD, r=0.02, lift=0.15)
        g.rect(0.0, 0.47, 0.285, 0.50, (0.12, 0.10, 0.30) if face else back, r=0.012, lift=0.12)
        if face:                                                                             # a moon card
            g.circle(0.0, 0.52, 0.085, (0.97, 0.88, 0.55), lift=0.2)
            g.circle(0.04, 0.545, 0.075, (0.12, 0.10, 0.30), lift=0)
            for (su, sv) in ((-0.08, 0.64), (0.08, 0.68), (-0.09, 0.40), (0.07, 0.36), (0.0, 0.34)):
                g.circle(su, sv, 0.012, (1.0, 0.95, 0.7), lift=0)
            g.rect(0.0, 0.27, 0.18, 0.016, GOLD, r=0.008)
        else:
            g.poly([(0.0, 0.72), (0.09, 0.47), (0.0, 0.22), (-0.09, 0.47)], GOLD, lift=0.1, alpha=0.9)
            g.poly([(0.0, 0.66), (0.055, 0.47), (0.0, 0.28), (-0.055, 0.47)], mix(back, NAVY, 0.5), lift=0.0)
            g.circle(0.0, 0.47, 0.022, GOLD, lift=0.2)
            for su, sv in ((-0.10, 0.70), (0.10, 0.70), (-0.10, 0.24), (0.10, 0.24)):
                g.circle(su, sv, 0.012, GOLD, lift=0.1)
    c.glow(0.0, 0.5, 0.8, mix(acc, WHITE, 0.4), 0.10)


@sprop("pro_astro_kundli", aspect=2.4, fill=0.62)
def astro_kundli(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.36, 0.38)
    f = _Flat(c, -0.62, 0.0, 1.10, 0.0, 0.22, 0.62)
    f.quad(0, 0, 1, 1, (0.96, 0.89, 0.72), lift=0.0)
    f.quad(0.02, 0.03, 0.98, 0.97, (0.98, 0.93, 0.80), lift=0.0)
    for (a0, b0, a1, b1) in ((0.03, 0.04, 0.97, 0.04), (0.97, 0.04, 0.97, 0.96), (0.97, 0.96, 0.03, 0.96), (0.03, 0.96, 0.03, 0.04)):
        f.line(a0, b0, a1, b1, 0.007, MAROON, 0.9)
    # the chart: outer square, diagonals, inner diamond (North Indian style)

    def ch(x, y):
        return (0.27 + 0.46 * x, 0.12 + 0.76 * y)
    sq = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    for p, q in zip(sq, sq[1:]):
        a, b = ch(*p), ch(*q)
        f.line(a[0], a[1], b[0], b[1], 0.011, MAROON, 1.0)
    for p, q in (((0, 0), (1, 1)), ((0, 1), (1, 0)), ((0.5, 0), (1, 0.5)), ((1, 0.5), (0.5, 1)), ((0.5, 1), (0, 0.5)), ((0, 0.5), (0.5, 0))):
        a, b = ch(*p), ch(*q)
        f.line(a[0], a[1], b[0], b[1], 0.008, MAROON, 0.95)
    houses = ((0.5, 0.76), (0.25, 0.90), (0.10, 0.75), (0.25, 0.50), (0.10, 0.25), (0.25, 0.10), (0.5, 0.24), (0.75, 0.10), (0.90, 0.25), (0.75, 0.50), (0.90, 0.75), (0.75, 0.90))
    for k, (x, y) in enumerate(houses):
        a, b = ch(x, y)
        p = f.p(a, b)
        c.text(str(k + 1), p[0], p[1], 0.032, MAROON, 0.20)
    for k, (x, y) in enumerate(((0.55, 0.70), (0.45, 0.80), (0.20, 0.45), (0.78, 0.55), (0.26, 0.16))):    # planets as little coloured marks
        a, b = ch(x, y)
        p = f.p(a, b)
        c.circle(p[0], p[1], 0.012, (0.86, 0.40, 0.12) if k % 2 else (0.15, 0.40, 0.55), lift=0.1)
    # title and side notes
    t = f.p(0.5, 0.94)
    c.text("JANAM KUNDLI", t[0], t[1] - 0.005, 0.034, MAROON, 0.20)
    for side, a0 in ((0, 0.06), (1, 0.80)):
        for k in range(6):
            f.line(a0, 0.72 - k * 0.10, a0 + 0.13 - 0.03 * (k % 2), 0.72 - k * 0.10, 0.005, (0.55, 0.30, 0.22), 0.8)
    sl = f.p(0.5, 0.06)
    c.circle(sl[0] + 0.45, sl[1] + 0.04, 0.03, (0.80, 0.12, 0.12), lift=0.3)                      # red wax seal
    gloss(c, -0.2, 0.44, 0.4, 0.03, 5, 0.12)


@sprop("pro_astro_diya", aspect=1.1, fill=0.62)
def astro_diya(c, color):
    ao(c, 0.0, 0.0, 0.55, 0.16, 0.38)
    c.glow(0.0, 0.40, 1.1, (1.0, 0.65, 0.25), 0.80)
    c.glow(0.0, 0.34, 0.5, (1.0, 0.85, 0.5), 0.60)
    # brass lamp: boat-shaped bowl with a pointed spout, flame above the wick
    c.ellipse(0.0, 0.07, 0.27, 0.27 * 0.38, scale(BRASS, 0.45), lift=0)
    c.poly([(-0.27, 0.14), (0.27, 0.14), (0.15, 0.04), (-0.15, 0.04)], BRASS, lift=0.25)
    c.poly([(0.26, 0.14), (0.40, 0.19), (0.24, 0.10)], mix(BRASS, WHITE, 0.15), lift=0.15)
    c.ellipse(0.0, 0.15, 0.27, 0.27 * 0.36, mix(BRASS, WHITE, 0.25), lift=0.1)
    c.ellipse(0.0, 0.152, 0.22, 0.22 * 0.32, (0.78, 0.52, 0.12), lift=0.0)
    c.ellipse(0.0, 0.152, 0.17, 0.17 * 0.3, (0.95, 0.75, 0.30), lift=0.0, alpha=0.8)
    c.line(0.0, 0.16, 0.0, 0.24, 0.016, (0.30, 0.2, 0.12), 1.0)
    # flame: outer orange, inner yellow, white core
    c.poly([(-0.060, 0.24), (0.0, 0.50), (0.060, 0.24), (0.0, 0.20)], (1.0, 0.55, 0.12), lift=0.0, alpha=0.9)
    c.poly([(-0.038, 0.25), (0.0, 0.44), (0.038, 0.25), (0.0, 0.22)], (1.0, 0.86, 0.35), lift=0.0)
    c.poly([(-0.018, 0.255), (0.0, 0.34), (0.018, 0.255), (0.0, 0.235)], (1.0, 1.0, 0.92), lift=0.0)
    c.glow(0.0, 0.32, 0.20, (1.0, 0.9, 0.55), 0.5)
    craft.arc(c, 0.0, 0.10, 0.22, 0.07, 200, 340, 0.006, (1.0, 0.9, 0.6), 0.6, 8)
    for k, (u, col) in enumerate(((-0.34, (1.0, 0.62, 0.1)), (0.32, (0.95, 0.45, 0.1)), (-0.28, (1.0, 0.75, 0.2)))):   # marigold petals
        c.ellipse(u, 0.035 + 0.01 * k, 0.045, 0.022, col, lift=0.2)


@sprop("pro_astro_kalash", aspect=0.75, fill=1.0)
def astro_kalash(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.15, 0.38)
    for k in range(7):                                                                      # mango leaves behind the coconut
        _leaf(c, 0.0, 0.64, rng.uniform(0.22, 0.32), 90 + (k - 3) * 26, (0.18 + rng.random() * 0.08, 0.46 + rng.random() * 0.12, 0.22), 0.34)
    craft.hshade_box(c, 0.0, 0.03, 0.22, 0.04, mix(BRASS, WHITE, 0.2), scale(BRASS, 0.4))
    c.ellipse(0.0, 0.30, 0.20, 0.23, scale(BRASS, 0.48), lift=0.0)
    c.ellipse(-0.005, 0.305, 0.19, 0.22, BRASS, lift=0.2)
    soft_disc(c, 0.09, 0.22, 0.14, 0.18, BLACK, 0.45, 1.3)
    soft_disc(c, -0.09, 0.38, 0.06, 0.14, WHITE, 0.55, 1.1, 10, add=True)
    craft.hshade_box(c, 0.0, 0.55, 0.14, 0.12, mix(BRASS, WHITE, 0.2), scale(BRASS, 0.42))
    c.ellipse(0.0, 0.62, 0.10, 0.10 * 0.38, mix(BRASS, WHITE, 0.3), lift=0.2)
    c.ellipse(0.0, 0.40, 0.19, 0.022, (0.78, 0.12, 0.12), lift=0.2, alpha=0.9)               # red thread band
    craft.arc(c, 0.0, 0.30, 0.17, 0.20, 215, 330, 0.008, mix(BRASS, WHITE, 0.5), 0.5, 8)
    c.ellipse(0.0, 0.69, 0.075, 0.085, (0.40, 0.25, 0.14), lift=0.2)                          # coconut
    for k in range(8):
        a = rng.uniform(0, 6.28)
        c.line(math.cos(a) * 0.02, 0.69 + math.sin(a) * 0.02, math.cos(a) * 0.065, 0.69 + math.sin(a) * 0.075, 0.003, (0.25, 0.15, 0.08), 0.6)
    gloss(c, -0.03, 0.72, 0.025, 0.03, 0, 0.5)


@niche("astrology", "Astrologer", subjects=("pro_astro_wheel",),
       strong=("astrologer", "astrology", "horoscope", "kundli", "vastu consultant", "tarot", "numerology", "palmistry", "ज्योतिष", "ज्योतिषी",
               "कुंडली", "jyotish", "jyotishi", "tarot reader", "vastu shastra", "राशिफल", "पंडित जी", "astro"),
       weak=("zodiac", "vastu", "gemstone", "crystal", "spiritual", "mystic", "fortune", "prediction", "puja"),
       accent="#5e35b1", mood="dark", group="professional")
def astrology(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    gold = GOLD
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.56)
        S.glow(1.2, 0.20, 1.2, mix(P.accent, WHITE, 0.3), 0.28 if dark else 0.10)
        # a huge faint mandala ring, crescent moon and stars
        S.circle(1.05, 0.24, 0.40, mix(P.accent_light, P.wall_top, 0.55), alpha=0.22 if dark else 0.30, lift=0)
        S.circle(1.05, 0.24, 0.35, P.wall_top, alpha=0.40, lift=0)
        S.circle(1.05, 0.24, 0.22, mix(P.accent_light, P.wall_top, 0.55), alpha=0.18, lift=0)
        S.circle(1.05, 0.24, 0.20, P.wall_top, alpha=0.40, lift=0)
        S.circle(1.78, 0.14, 0.085, (1.0, 0.92, 0.65), lift=0)
        S.circle(1.82, 0.12, 0.078, P.wall_top, lift=0)
        S.glow(1.78, 0.14, 0.4, (1.0, 0.9, 0.6), 0.25 if dark else 0.10)
        for k in range(46):
            S.circle(rng.uniform(-0.2, 2.2), rng.uniform(0.0, 0.50), rng.uniform(0.004, 0.011), (1.0, 0.95, 0.8), alpha=rng.uniform(0.35, 0.9) if dark else 0.35, lift=0)
        # heavy velvet drapes either side and golden lantern light
        for (u0, u1, flip) in ((-0.2, 0.30, 1), (1.75, 2.25, -1)):
            for k in range(6):
                S.rect(u0 + (u1 - u0) * (k + 0.5) / 6, 0.28, (u1 - u0) / 6 + 0.004, 0.60, mix(P.accent_dark, P.ink, 0.25 + 0.2 * (k % 2)) if dark else mix(P.accent, P.wall_bot, 0.35 + 0.15 * (k % 2)), lift=0.0)
        S.pendant(0.70, -0.1, 0.16, (1.0, 0.72, 0.36), 0.08)
        S.pendant(1.45, -0.1, 0.12, (1.0, 0.72, 0.36), 0.07)
        S.bokeh(14, 0.0, 0.10, 2.0, 0.55, [(1.0, 0.78, 0.40), (1.0, 0.65, 0.30), mix(P.accent_light, WHITE, 0.3)], 0.010, 0.040, 0.32)
        S.floor(0.56, P.floor_top, P.floor_bot)
    # velvet table cloth with a gold-trimmed runner
    cloth_t = mix(P.accent_dark, P.ink, 0.25) if dark else mix(P.accent, P.ink, 0.15)
    S.gradient_rect(-5.0, 0.56, 7.0, 2.6, cloth_t, scale(cloth_t, 0.55))
    S.rect(1.0, 0.56, 14.0, 0.010, scale(cloth_t, 0.40), lift=0.0)
    S.rect(1.05, 0.88, 1.5, 0.30, scale(cloth_t, 1.12), lift=0.0, alpha=0.9, r=0.01)
    for dv in (-0.15, 0.15):
        S.rect(1.05, 0.88 + dv, 1.5, 0.006, gold, lift=0.0, alpha=0.85)
    S.soft(1.15, 0.82, 1.0, 0.22, (1.0, 0.72, 0.38), 0.30 if dark else 0.14, 1.5, add=True)
    S.put("pro_astro_kalash", 0.60, 0.80, 0.30, shadow_alpha=0.40)
    S.put("pro_astro_tarot", 0.80, 0.93, 0.28, color=P, shadow_alpha=0.40)
    S.put("pro_astro_wheel", 1.07, 0.84, 0.52, color=P, subject=True, shadow_alpha=0.40)
    S.put("pro_astro_ball", 1.44, 0.94, 0.30, color=P, shadow_alpha=0.40)
    S.put("pro_astro_kundli", 1.10, 1.0, 0.18, color=P, shadow_alpha=0.30, shadow_w=0.9)
    S.put("pro_astro_diya", 1.30, 1.0, 0.09, shadow_alpha=0.38)
    S.focus("detail", 1.26, 0.80)
    with S.near():
        S.circle(0.56, 0.98, 0.04, (1.0, 0.72, 0.36), alpha=0.40, lift=0)
        S.circle(1.64, 0.40, 0.05, mix(P.accent_light, WHITE, 0.3), alpha=0.22, lift=0)


# ====================================================================================================== VISA / IMMIGRATION
CONTINENTS = (
    [(0.05, 0.15), (0.12, 0.08), (0.25, 0.10), (0.31, 0.20), (0.27, 0.35), (0.22, 0.42), (0.18, 0.50), (0.14, 0.38), (0.08, 0.30)],
    [(0.22, 0.52), (0.30, 0.52), (0.34, 0.62), (0.30, 0.80), (0.25, 0.96), (0.22, 0.75), (0.20, 0.60)],
    [(0.44, 0.18), (0.52, 0.13), (0.57, 0.22), (0.52, 0.32), (0.45, 0.30)],
    [(0.46, 0.36), (0.56, 0.36), (0.62, 0.48), (0.57, 0.72), (0.52, 0.80), (0.48, 0.60), (0.44, 0.46)],
    [(0.56, 0.12), (0.70, 0.07), (0.88, 0.14), (0.93, 0.28), (0.84, 0.42), (0.76, 0.46), (0.73, 0.58), (0.69, 0.40), (0.60, 0.34), (0.57, 0.24)],
    [(0.78, 0.62), (0.90, 0.60), (0.94, 0.72), (0.83, 0.79), (0.77, 0.72)],
)


def _stamp(c, f, a, b, ra, rb, col, rng, kind=0):
    """A visa stamp on a flat page: double ring (kind 0), rectangle with text bars (1) or a triangle (2)."""
    p = f.p(a, b)
    if kind == 0:
        for k, sc in enumerate((1.0, 0.82)):
            craft.arc(c, p[0], p[1], ra * sc, rb * sc, 0, 360, 0.006, col, 0.70, 14)
        c.line(p[0] - ra * 0.6, p[1], p[0] + ra * 0.6, p[1], 0.008, col, 0.7)
        c.line(p[0] - ra * 0.45, p[1] - rb * 0.35, p[0] + ra * 0.45, p[1] - rb * 0.35, 0.005, col, 0.6)
        c.line(p[0] - ra * 0.45, p[1] + rb * 0.35, p[0] + ra * 0.45, p[1] + rb * 0.35, 0.005, col, 0.6)
    elif kind == 1:
        for (da, db, ea, eb) in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
            c.line(p[0] + da * ra, p[1] + db * rb, p[0] + ea * ra, p[1] + eb * rb, 0.006, col, 0.7)
        c.line(p[0] - ra * 0.7, p[1] + rb * 0.25, p[0] + ra * 0.7, p[1] + rb * 0.25, 0.008, col, 0.7)
        c.line(p[0] - ra * 0.5, p[1] - rb * 0.25, p[0] + ra * 0.6, p[1] - rb * 0.25, 0.005, col, 0.6)
    else:
        for k in range(3):
            q = [(p[0] - ra, p[1] - rb), (p[0] + ra, p[1] - rb), (p[0], p[1] + rb), (p[0] - ra, p[1] - rb)]
            for s, t in zip(q, q[1:]):
                c.line(s[0], s[1], t[0], t[1], 0.006, col, 0.7)
            break


def _passport_closed(c, ox, oy, cover, gold, rng, emblem=False, tilt=0.0):
    f = _Flat(c, ox, oy, 0.40, tilt, 0.10, 0.50)
    ex, ey = 0.40, tilt
    c.poly([(ox, oy), (ox + ex, oy + ey), (ox + ex, oy + ey - 0.032), (ox, oy - 0.032)], scale(cover, 0.55), lift=0.0)
    c.poly([(ox, oy), (ox + ex, oy + ey), (ox + ex, oy + ey - 0.012), (ox, oy - 0.012)], (0.93, 0.90, 0.82), lift=0.0)
    c.poly([(ox + ex, oy + ey), (ox + ex + 0.10, oy + ey + 0.50), (ox + ex + 0.10, oy + ey + 0.50 - 0.030), (ox + ex, oy + ey - 0.030)], scale(cover, 0.45), lift=0.0)
    f.quad(0, 0, 1, 1, cover, lift=0.0)
    f.tint(0, 0, 1, 1, WHITE, 0.05)
    f.line(0.05, 0.05, 0.95, 0.05, 0.004, gold, 0.5)
    f.line(0.05, 0.95, 0.95, 0.95, 0.004, gold, 0.5)
    f.line(0.0, 0.0, 0.0, 1.0, 0.010, scale(cover, 0.6), 0.9)
    if emblem:
        p = f.p(0.5, 0.58)
        c.ellipse(p[0], p[1], 0.075, 0.07, gold, lift=0.2)
        c.ellipse(p[0], p[1], 0.060, 0.056, cover, lift=0.0)
        c.ellipse(p[0], p[1], 0.036, 0.034, gold, lift=0.15)
        for k in range(8):
            a = math.radians(k * 45)
            c.line(p[0] + math.cos(a) * 0.04, p[1] + math.sin(a) * 0.038, p[0] + math.cos(a) * 0.056, p[1] + math.sin(a) * 0.053, 0.006, gold, 0.9)
        q = f.p(0.5, 0.26)
        c.text("PASSPORT", q[0], q[1], 0.026, gold, 0.2)
    return f


@sprop("pro_visa_passports", aspect=3.0, fill=0.66)
def visa_passports(c, color):
    rng = c.rng
    gold = (0.92, 0.76, 0.34)
    ao(c, 0.0, 0.0, 2.0, 0.40, 0.36)
    # three closed passports in a messy stack (left)
    for k, (dx, cover) in enumerate(((0.00, (0.45, 0.10, 0.15)), (0.05, (0.10, 0.34, 0.24)), (-0.03, (0.10, 0.20, 0.42)))):
        _passport_closed(c, -0.98 + dx, 0.05 + k * 0.040, cover, gold, rng, emblem=(k == 2), tilt=0.0)
    # open passport (right): photo page and stamped page
    ox, oy = -0.40, 0.02
    fl = _Flat(c, ox, oy, 0.55, 0.0, 0.12, 0.52)
    fr = _Flat(c, ox + 0.55, oy, 0.55, 0.0, 0.12, 0.52)
    c.poly([(ox, oy), (ox + 1.10, oy), (ox + 1.10, oy - 0.03), (ox, oy - 0.03)], (0.10, 0.20, 0.42), lift=0.0)
    for f, left in ((fl, True), (fr, False)):
        f.quad(0, 0, 1, 1, (0.96, 0.93, 0.84) if left else (0.97, 0.94, 0.86), lift=0.0)
        f.tint(0, 0, 1, 1, (0.55, 0.75, 0.90), 0.06)
        for k in range(14):                                                                # security guilloche lines
            f.line(0.04, 0.05 + k * 0.067, 0.96, 0.07 + k * 0.067, 0.0022, (0.60, 0.72, 0.85), 0.35)
    # photo page
    f = fl
    pp = f.p(0.28, 0.62)
    c.rect(pp[0], pp[1], 0.14, 0.16, (0.55, 0.70, 0.85), lift=0.1, r=0.006)
    c.ellipse(pp[0], pp[1] + 0.03, 0.032, 0.034, SKINS[1], lift=0.2)
    c.ellipse(pp[0], pp[1] - 0.04, 0.055, 0.035, (0.25, 0.30, 0.45), lift=0.1)
    for k in range(4):
        f.line(0.52, 0.80 - k * 0.12, 0.92 - 0.1 * (k % 2), 0.80 - k * 0.12, 0.005, (0.35, 0.38, 0.45), 0.8)
    for k in range(2):                                                                     # machine readable zone
        f.line(0.06, 0.18 - k * 0.07, 0.94, 0.18 - k * 0.07, 0.008, (0.25, 0.25, 0.30), 0.75)
    # stamped page
    f = fr
    _stamp(c, f, 0.32, 0.68, 0.085, 0.075, (0.15, 0.30, 0.75), rng, 0)
    _stamp(c, f, 0.72, 0.30, 0.10, 0.065, (0.75, 0.12, 0.15), rng, 1)
    _stamp(c, f, 0.64, 0.74, 0.07, 0.07, (0.10, 0.50, 0.30), rng, 2)
    _stamp(c, f, 0.28, 0.28, 0.07, 0.065, (0.55, 0.15, 0.55), rng, 0)
    v = f.p(0.5, 0.50)
    c.text("VISA", v[0], v[1], 0.030, (0.25, 0.35, 0.60), 0.18)
    c.line(ox + 0.55, oy, ox + 0.55 + 0.12, oy + 0.52, 0.006, scale((0.55, 0.50, 0.42), 0.8), 0.7)         # the fold
    gloss(c, ox + 0.2, oy + 0.28, 0.3, 0.02, 6, 0.10)


@sprop("pro_visa_globe", aspect=0.8, fill=1.0)
def visa_globe(c, color):
    acc = _acc(color, "accent", (0.10, 0.46, 0.82))
    ao(c, 0.0, 0.0, 0.66, 0.19, 0.38)
    c.ellipse(0.0, 0.03, 0.27, 0.27 * TILT, scale(BRASS, 0.42), lift=0)
    disc(c, 0.0, 0.05, 0.26, BRASS, TILT, 0.15)
    craft.hshade_box(c, 0.0, 0.12, 0.05, 0.16, mix(BRASS, WHITE, 0.2), scale(BRASS, 0.45))
    cx, cy, R = 0.0, 0.64, 0.35
    ocean = mix((0.16, 0.42, 0.80), acc, 0.4)
    c.circle(cx, cy, R, scale(ocean, 0.72), lift=0.10)
    c.circle(cx, cy, R * 0.985, ocean, lift=0.14)
    land = ((-0.10, 0.76, 0.14, 0.08, 18, (0.80, 0.78, 0.55)), (-0.20, 0.64, 0.06, 0.10, -10, (0.56, 0.74, 0.46)), (-0.10, 0.50, 0.07, 0.13, 12, (0.56, 0.74, 0.46)),
            (0.12, 0.74, 0.14, 0.09, -12, (0.80, 0.78, 0.55)), (0.10, 0.56, 0.07, 0.11, 6, (0.56, 0.74, 0.46)), (0.20, 0.50, 0.05, 0.05, 0, (0.86, 0.72, 0.45)),
            (0.0, 0.93, 0.12, 0.025, 0, (0.96, 0.98, 1.0)), (0.0, 0.36, 0.09, 0.03, 0, (0.96, 0.98, 1.0)))
    for (u, v, a, b, ang, col) in land:
        c.ellipse(u, v, a, b, col, angle=ang, lift=0.1)
        c.ellipse(u + 0.012, v - 0.012, a * 0.6, b * 0.5, scale(col, 0.8), lift=0, alpha=0.5, angle=ang)
    for k in range(-2, 3):
        craft.arc(c, cx, cy, R * 0.985 * abs(math.cos(k * 0.5)), R * 0.985, -90, 90, 0.003, (0.88, 0.95, 1.0), 0.28, 12)
    for v in (-0.17, 0.0, 0.17):
        c.line(cx - math.sqrt(R * R - v * v) * 0.97, cy + v, cx + math.sqrt(R * R - v * v) * 0.97, cy + v, 0.003, (0.88, 0.95, 1.0), 0.25)
    for (pu, pv) in ((0.14, 0.70), (-0.12, 0.74)):                                              # pins
        c.line(pu, pv, pu, pv + 0.07, 0.006, (0.85, 0.85, 0.88), 1.0)
        c.circle(pu, pv + 0.085, 0.020, (0.88, 0.16, 0.18), lift=0.3)
    soft_disc(c, cx + 0.14, cy - 0.15, R * 0.8, R * 0.8, (0.0, 0.04, 0.16), 0.50, 1.6)
    soft_disc(c, cx - 0.13, cy + 0.13, R * 0.42, R * 0.34, WHITE, 0.45, 1.2, 30, add=True)
    craft.arc(c, cx, cy, R * 1.09, R * 1.09, 105, 300, 0.022, scale(BRASS, 0.62), 1.0, 22)
    craft.arc(c, cx, cy, R * 1.09, R * 1.09, 105, 300, 0.010, mix(BRASS, WHITE, 0.3), 1.0, 22)
    c.line(0.0, 0.18, 0.0, 0.30, 0.03, BRASS)


@sprop("pro_visa_plane", aspect=1.35, fill=0.95)
def visa_plane(c, color):
    acc = _acc(color, "accent", (0.10, 0.46, 0.82))
    ao(c, 0.0, 0.0, 0.62, 0.16, 0.36)
    c.ellipse(0.0, 0.03, 0.26, 0.26 * TILT, scale(STEELC, 0.5), lift=0, alpha=0.9)
    disc(c, 0.0, 0.05, 0.25, mix(STEELC, WHITE, 0.3), TILT, 0.12, alpha=0.95)
    c.line(0.0, 0.06, 0.0, 0.42, 0.022, mix(STEELC, WHITE, 0.4), 0.8)
    g = _G(c, 0.0, 0.58, 9)
    body, shade = (0.97, 0.97, 0.98), (0.72, 0.74, 0.80)
    g.poly([(-0.02, 0.02), (0.14, 0.03), (-0.18, 0.28), (-0.30, 0.27)], scale(shade, 0.9), lift=0.1)                    # far wing
    g.poly([(-0.46, 0.04), (-0.34, 0.04), (-0.46, 0.34), (-0.60, 0.34)], acc, lift=0.2)                                     # tail fin
    g.poly([(-0.46, 0.0), (-0.34, 0.0), (-0.46, 0.12), (-0.56, 0.10)], scale(shade, 0.9), lift=0.1)                          # far tailplane
    c.ellipse(*g.pt(0.0, 0.0), 0.62, 0.095, body, angle=9, lift=0.30)
    c.ellipse(*g.pt(0.0, -0.025), 0.60, 0.060, shade, angle=9, lift=0.0, alpha=0.55)
    g.rect(0.0, -0.005, 0.90, 0.016, acc, lift=0.1, alpha=0.95)
    for k in range(11):
        g.circle(-0.30 + k * 0.045, 0.030, 0.011, (0.18, 0.22, 0.32), lift=0.2)
    g.poly([(0.42, 0.02), (0.52, 0.00), (0.44, 0.06)], (0.15, 0.20, 0.30), lift=0.1)                                         # cockpit
    g.poly([(-0.02, -0.03), (0.16, -0.03), (-0.22, -0.30), (-0.38, -0.28)], mix(body, shade, 0.4), lift=0.25)               # near wing
    g.circle(-0.06, -0.15, 0.046, scale(shade, 0.7), lift=0.3)                                                               # engine
    g.circle(-0.045, -0.145, 0.026, (0.20, 0.22, 0.28), lift=0.1)
    g.poly([(-0.46, -0.02), (-0.34, -0.02), (-0.52, -0.12), (-0.62, -0.11)], mix(body, shade, 0.5), lift=0.2)
    soft_disc(c, *g.pt(0.1, 0.06), 0.35, 0.03, WHITE, 0.45, 1.2, 9, add=True)


@sprop("pro_visa_tickets", aspect=2.1, fill=0.45)
def visa_tickets(c, color):
    acc = _acc(color, "accent", (0.10, 0.46, 0.82))
    rng = c.rng
    ao(c, 0.0, 0.0, 1.3, 0.30, 0.34)
    for (ox, oy, tilt, band) in ((-0.60, 0.04, 0.0, acc), (-0.30, -0.01, 0.0, mix(acc, (0.95, 0.60, 0.2), 0.7))):
        f = _Flat(c, ox, oy, 0.80, tilt, 0.10, 0.36)
        c.poly([(ox, oy), (ox + 0.80, oy + tilt), (ox + 0.80, oy + tilt - 0.014), (ox, oy - 0.014)], (0.75, 0.74, 0.70), lift=0.0)
        f.quad(0, 0, 1, 1, (0.98, 0.98, 0.97), lift=0.0)
        f.quad(0, 0.72, 1, 1, band, lift=0.0)
        f.line(0.72, 0.0, 0.72, 0.72, 0.004, (0.65, 0.65, 0.70), 0.8)                    # perforation
        t = f.p(0.30, 0.86)
        c.text("BOARDING PASS", t[0], t[1], 0.020, WHITE, 0.18)
        r = f.p(0.30, 0.46)
        c.text("DEL  LHR", r[0], r[1], 0.040, (0.12, 0.14, 0.24), 0.20)
        for k in range(2):
            f.line(0.08, 0.22 - k * 0.09, 0.52 - 0.12 * k, 0.22 - k * 0.09, 0.005, (0.55, 0.58, 0.65), 0.8)
        u = 0.77
        while u < 0.97:                                                                  # barcode on the stub
            w = 0.006 + 0.008 * rng.random()
            f.line(u, 0.12, u, 0.58, w, (0.10, 0.10, 0.14), 0.9)
            u += w + 0.018
        c.line(*f.p(0.62, 0.66), *f.p(0.66, 0.66), 0.012, band, 1.0)


@niche("visa", "Visa and immigration consultancy", subjects=("pro_visa_passports",),
       strong=("visa consultant", "immigration", "study abroad", "passport services", "overseas education", "visa consultancy", "visa services",
               "immigration consultant", "overseas consultant", "work permit", "pr visa", "वीज़ा", "वीजा", "इमिग्रेशन", "विदेश में पढ़ाई", "pasport", "visa agent"),
       weak=("abroad", "passport", "foreign", "tourist visa", "canada", "australia", "uk visa", "migration", "ielts"),
       accent="#1976d2", mood="light", group="professional",
       avoid=("plane tickets", "tourists", "holiday", "adventurous", "itinerary", "sightseeing"))
def visa(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.56)
        S.glow(1.3, 0.22, 1.0, P.accent_light, 0.22 if dark else 0.10)
        # big world map on the wall: ocean panel, cream continents, route dots
        mu, mv, mw, mh = 1.50, 0.26, 1.00, 0.46
        ocean = mix(P.accent, P.wall_bot, 0.55 if not dark else 0.30)
        S.rect(mu, mv, mw + 0.03, mh + 0.03, scale(ocean, 0.7), lift=0.0)
        S.rect(mu, mv, mw, mh, ocean, lift=0.0)
        for poly in CONTINENTS:
            pts = _chaikin([(mu - mw / 2 + x * mw, mv - mh / 2 + y * mh) for x, y in poly], 2)
            S.poly(pts, mix((0.95, 0.93, 0.84), ocean, 0.12 if not dark else 0.6))
        for (x, y) in ((0.20, 0.30), (0.50, 0.28), (0.72, 0.30), (0.85, 0.68), (0.30, 0.66)):
            S.circle(mu - mw / 2 + x * mw, mv - mh / 2 + y * mh, 0.012, (1.0, 0.45, 0.35), lift=0)
        S.line(mu - mw / 2 + 0.20 * mw, mv - mh / 2 + 0.30 * mh, mu - mw / 2 + 0.72 * mw, mv - mh / 2 + 0.30 * mh, 0.005, WHITE, 0.6)
        # a clock wall and sky window on the left, pendants
        st, sb = _sky(P)
        S.gradient_rect(0.05, 0.04, 0.60, 0.54, st, sb)
        for k in range(3):
            S.rect(0.05 + k * 0.275, 0.29, 0.010, 0.50, scale(P.wall_top, 0.95), lift=0.0)
        S.rect(0.325, 0.29, 0.55, 0.010, scale(P.wall_top, 0.95), lift=0.0)
        S.pendant(0.90, -0.1, 0.15, (1.0, 0.94, 0.78), 0.08)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [P.accent_light, (1.0, 0.95, 0.8)], 0.012, 0.04, 0.3)
        S.floor(0.56, P.floor_top, P.floor_bot)
    S.soft(1.15, 0.64, 1.0, 0.12, (1.0, 0.95, 0.82), 0.20 if not dark else 0.26, 1.5, add=True)
    desk = mix(P.surface, (0.95, 0.90, 0.80), 0.30) if not dark else scale(P.surface, 1.05)
    S.wood(-5.0, 0.56, 7.0, 2.6, desk, plank=0.13, grain=0.35)
    S.rect(1.0, 0.56, 14.0, 0.008, scale(desk, 0.5), lift=0.0)
    S.put("pro_visa_plane", 0.66, 0.84, 0.30, color=P, shadow_alpha=0.30)
    S.put("pro_visa_globe", 1.46, 0.82, 0.44, color=P, shadow_alpha=0.32)
    S.put("pro_visa_passports", 1.00, 0.98, 0.25, color=P, subject=True, shadow_alpha=0.30, shadow_w=1.1)
    S.put("pro_visa_tickets", 1.50, 1.0, 0.16, color=P, shadow_alpha=0.26)
    S.soft(1.1, 0.88, 0.6, 0.18, (1.0, 0.95, 0.8), 0.18 if not dark else 0.36, 1.6, add=True)
    S.focus("detail", 1.10, 0.82)
    with S.near():
        S.circle(0.55, 0.98, 0.04, P.accent_light, alpha=0.40, lift=0)
        S.circle(1.64, 0.40, 0.05, mix(P.accent, WHITE, 0.4), alpha=0.22, lift=0)


# ====================================================================================================== NGO / CHARITY
HEART = (0.90, 0.18, 0.28)


def _heart(c, u, v, s, col, lift=0.18, alpha=1.0):
    """A heart centred at (u, v), s = half width."""
    c.ellipse(u - s * 0.50, v + s * 0.26, s * 0.54, s * 0.54, col, lift=lift, alpha=alpha)
    c.ellipse(u + s * 0.50, v + s * 0.26, s * 0.54, s * 0.54, col, lift=lift, alpha=alpha)
    c.poly([(u - s * 0.97, v + s * 0.08), (u + s * 0.97, v + s * 0.08), (u, v - s * 0.92)], col, lift=lift, alpha=alpha)


@sprop("pro_ngo_box", aspect=0.78, fill=1.0)
def ngo_box(c, color):
    acc = _acc(color, "accent", (0.26, 0.63, 0.28))
    rng = c.rng
    ao(c, 0.04, 0.0, 0.70, 0.22, 0.40)
    W = 0.56
    # solid base with a white heart badge
    craft.hshade_box(c, 0.0, 0.11, W, 0.22, mix(acc, WHITE, 0.15), scale(acc, 0.58), r=0.02)
    c.rect(0.0, 0.215, W + 0.02, 0.026, mix(acc, WHITE, 0.3), r=0.008, lift=0.25)
    c.circle(0.0, 0.11, 0.075, WHITE, lift=0.05, alpha=0.95)
    _heart(c, 0.0, 0.115, 0.045, HEART)
    c.text("DONATE", 0.0, 0.035, 0.026, WHITE, 0.2)
    # acrylic cube full of notes, coins and paper hearts
    c.rect(0.0, 0.50, W - 0.04, 0.52, (0.70, 0.86, 0.90), r=0.01, lift=0.0, alpha=0.30)
    for k in range(10):
        g = _G(c, rng.uniform(-0.18, 0.18), 0.28 + rng.uniform(0, 0.05), rng.uniform(-30, 30))
        g.rect(0.0, 0.0, 0.14, 0.065, rng.choice([(0.55, 0.75, 0.55), (0.92, 0.72, 0.45), (0.65, 0.80, 0.92), (0.95, 0.85, 0.5)]), r=0.004, lift=0.15)
    for k in range(9):
        _heart(c, rng.uniform(-0.19, 0.19), rng.uniform(0.28, 0.40), rng.uniform(0.028, 0.040), rng.choice([HEART, (0.95, 0.40, 0.50), (0.85, 0.12, 0.22)]), 0.2)
    for k in range(12):
        cu, cv_ = rng.uniform(-0.2, 0.2), rng.uniform(0.265, 0.30)
        c.ellipse(cu, cv_, 0.030, 0.014, scale(GOLD, 0.7), lift=0)
        c.ellipse(cu, cv_ + 0.006, 0.030, 0.014, GOLD, lift=0.2)
    big = (0.0, 0.52)
    _heart(c, big[0], big[1], 0.105, scale(HEART, 0.75), 0.15, 0.40)                          # big heart sticker on the glass
    _heart(c, big[0], big[1] + 0.005, 0.095, HEART, 0.25)
    gloss(c, -0.04, 0.56, 0.04, 0.03, 40, 0.8)
    # acrylic edges, reflections and the lid with a coin slot
    for u in (-W / 2 + 0.02, W / 2 - 0.02):
        c.rect(u, 0.50, 0.012, 0.52, WHITE, lift=0, alpha=0.45)
    _fill_quad(c.cv, [(c.X(-0.25), c.Y(0.74)), (c.X(-0.10), c.Y(0.74)), (c.X(-0.20), c.Y(0.26)), (c.X(-0.25), c.Y(0.26))], WHITE, 0.22)
    _fill_quad(c.cv, [(c.X(0.07), c.Y(0.74)), (c.X(0.10), c.Y(0.74)), (c.X(0.02), c.Y(0.26)), (c.X(0.0), c.Y(0.26))], WHITE, 0.12)
    craft.hshade_box(c, 0.0, 0.77, W + 0.02, 0.055, mix(acc, WHITE, 0.2), scale(acc, 0.55), r=0.015)
    c.ellipse(0.0, 0.80, W / 2 + 0.01, 0.065, mix(acc, WHITE, 0.25), lift=0.15)
    c.ellipse(0.0, 0.80, 0.14, 0.018, (0.05, 0.08, 0.05), lift=0)
    c.glow(0.0, 0.5, 0.7, (1.0, 0.95, 0.8), 0.06)
    # a few coins resting in front
    for k, (u, v) in enumerate(((0.38, 0.03), (0.38, 0.045), (0.38, 0.060), (0.46, 0.03))):
        c.ellipse(u, v, 0.050, 0.020, scale(GOLD, 0.65), lift=0)
        c.ellipse(u, v + 0.008, 0.050, 0.020, GOLD, lift=0.25)
        c.ellipse(u, v + 0.008, 0.032, 0.012, mix(GOLD, WHITE, 0.25), lift=0, alpha=0.7)


@sprop("pro_ngo_hands", aspect=1.05, fill=1.0)
def ngo_hands(c, color):
    acc2 = _acc(color, "accent2", (0.50, 0.70, 0.30))
    rng = c.rng
    skin = (0.88, 0.66, 0.50)
    ao(c, 0.0, 0.0, 0.8, 0.20, 0.36)
    # sleeves and forearms coming in from both sides
    for sign in (-1, 1):
        c.line(sign * 0.50, 0.02, sign * 0.24, 0.16, 0.18, scale(skin, 0.82), 1.0)
        c.line(sign * 0.49, 0.025, sign * 0.25, 0.17, 0.12, skin, 1.0)
        c.line(sign * 0.60, -0.02, sign * 0.46, 0.04, 0.22, acc2, 1.0)
    # seedling growing out of a mound of soil, behind the fingers
    c.ellipse(0.0, 0.30, 0.20, 0.09, (0.30, 0.18, 0.10), lift=0.2)
    c.ellipse(0.0, 0.32, 0.17, 0.07, (0.40, 0.25, 0.14), lift=0.1)
    for k in range(10):
        c.circle(rng.uniform(-0.12, 0.12), 0.32 + rng.uniform(-0.03, 0.04), rng.uniform(0.006, 0.012), (0.25, 0.15, 0.08), lift=0)
    c.line(0.0, 0.34, 0.0, 0.64, 0.030, (0.30, 0.58, 0.25), 1.0)
    c.line(-0.008, 0.34, -0.008, 0.62, 0.010, (0.55, 0.80, 0.45), 0.7)
    _leaf(c, 0.0, 0.62, 0.30, 140, (0.30, 0.66, 0.30), 0.50)
    _leaf(c, 0.0, 0.58, 0.28, 38, (0.38, 0.74, 0.32), 0.50)
    _leaf(c, 0.0, 0.64, 0.14, 90, (0.55, 0.82, 0.42), 0.50)
    c.glow(0.0, 0.62, 0.7, (0.8, 1.0, 0.6), 0.18)
    # two cupped palms (back edge, lit palms, finger lip, thumbs)
    c.ellipse(0.0, 0.17, 0.36, 0.15, scale(skin, 0.68), lift=0.0)
    c.ellipse(-0.17, 0.15, 0.22, 0.12, scale(skin, 0.92), angle=8, lift=0.22)
    c.ellipse(0.17, 0.15, 0.22, 0.12, scale(skin, 0.86), angle=-8, lift=0.22)
    soft_disc(c, 0.0, 0.22, 0.20, 0.06, (0.2, 0.1, 0.05), 0.35, 1.4)
    for k in range(5):
        a = math.radians(205 + k * 32)
        fu, fv = math.cos(a) * 0.30, 0.17 + math.sin(a) * 0.12
        c.ellipse(fu, fv, 0.052, 0.034, mix(skin, WHITE, 0.08), lift=0.25, angle=(k - 2) * 12)
        c.ellipse(fu - 0.005, fv + 0.012, 0.030, 0.012, WHITE, lift=0, alpha=0.25)
    for sign in (-1, 1):
        c.ellipse(sign * 0.33, 0.20, 0.055, 0.032, mix(skin, WHITE, 0.05), lift=0.22, angle=sign * 40)
    soft_disc(c, -0.14, 0.20, 0.14, 0.05, WHITE, 0.28, 1.2, 8, add=True)


@sprop("pro_ngo_parcels", aspect=1.0, fill=1.0)
def ngo_parcels(c, color):
    acc = _acc(color, "accent", (0.26, 0.63, 0.28))
    rng = c.rng
    paper = (0.80, 0.64, 0.44)
    ao(c, 0.0, 0.0, 0.9, 0.26, 0.40)

    def bag(u, v, w, h, d, lbl):
        # produce sticking out of the open top
        for k in range(4):
            _leaf(c, u + rng.uniform(-w * 0.2, w * 0.2), v + h, rng.uniform(0.14, 0.22), 90 + rng.uniform(-40, 40), (0.2 + 0.1 * rng.random(), 0.55 + 0.12 * rng.random(), 0.22), 0.4, vein=False)
        c.ellipse(u + w * 0.18, v + h + 0.02, 0.055, 0.075, (0.85, 0.50, 0.15), angle=-12, lift=0.25)
        c.ellipse(u - w * 0.15, v + h + 0.03, 0.040, 0.040, (0.82, 0.14, 0.12), lift=0.3)
        gloss(c, u - w * 0.19, v + h + 0.045, 0.012, 0.010, 0, 0.8)
        box3d(c, u, v, w, h, d, paper, mix(paper, WHITE, 0.30), scale(paper, 0.68), lift=0.08, dx=0.55, dy=0.42)
        c.rect(u, v + h - 0.015, w, 0.03, scale(paper, 0.86), lift=0.1)                         # folded rim
        for k in range(3):
            c.line(u - w * 0.45, v + 0.05 + k * h * 0.28, u + w * 0.45, v + 0.05 + k * h * 0.28 + rng.uniform(-0.004, 0.004), 0.003, scale(paper, 0.82), 0.5)
        c.rect(u, v + h * 0.50, w * 0.52, h * 0.34, (0.98, 0.97, 0.93), r=0.01, lift=0.04)    # label
        _heart(c, u, v + h * 0.56, 0.038, HEART)
        c.rect(u, v + h * 0.38, w * 0.38, 0.012, acc, r=0.005, lift=0.1)
    bag(-0.24, 0.10, 0.34, 0.46, 0.22, "")
    bag(0.20, 0.05, 0.32, 0.38, 0.20, "")
    # bread, in front of the bags
    c.ellipse(-0.05, 0.05, 0.16, 0.05, (0.62, 0.38, 0.14), lift=0)
    c.ellipse(-0.05, 0.065, 0.16, 0.05, (0.86, 0.58, 0.26), lift=0.25)
    for k in range(4):
        c.line(-0.14 + k * 0.06, 0.07, -0.11 + k * 0.06, 0.09, 0.012, (0.70, 0.42, 0.16), 0.9)
    gloss(c, -0.10, 0.085, 0.06, 0.012, 3, 0.5)


@sprop("pro_ngo_books", aspect=1.7, fill=0.58)
def ngo_books(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.28, 0.38)
    v = 0.0
    for k, (col, w) in enumerate((((0.92, 0.30, 0.30), 0.62), ((0.98, 0.78, 0.20), 0.58), ((0.25, 0.60, 0.88), 0.60))):
        u = rng.uniform(-0.04, 0.04) - 0.2
        box3d(c, u, v, w, 0.075, 0.40, col, mix(col, WHITE, 0.22), scale(col, 0.62), lift=0.15, dx=0.5, dy=0.5)
        sx = u + w / 2 + 0.2
        c.poly([(sx - 0.01, v + 0.012), (sx + 0.185, v + 0.012 + 0.185), (sx + 0.185, v + 0.063 + 0.185), (sx - 0.01, v + 0.063)], (0.96, 0.94, 0.88), lift=0.0)       # page edge
        c.circle(u - w * 0.18, v + 0.04, 0.020, mix(col, WHITE, 0.6), lift=0.1)
        c.rect(u + w * 0.10, v + 0.04, w * 0.34, 0.016, mix(col, WHITE, 0.55), r=0.006, lift=0.1)
        v += 0.078
    # open picture book and crayons beside the stack
    f = _Flat(c, 0.28, 0.0, 0.52, 0.0, 0.12, 0.34)
    f.quad(0, 0, 0.5, 1, (0.98, 0.96, 0.90), lift=0.0)
    f.quad(0.5, 0, 1, 1, (0.99, 0.97, 0.92), lift=0.0)
    f.line(0.5, 0, 0.5, 1, 0.005, (0.70, 0.66, 0.58), 0.8)
    for (a, b, col) in ((0.25, 0.55, (0.98, 0.78, 0.20)), (0.72, 0.52, (0.55, 0.80, 0.40))):
        p = f.p(a, b)
        c.ellipse(p[0], p[1], 0.05, 0.034, col, lift=0.2)
    p = f.p(0.25, 0.25)
    c.rect(p[0], p[1], 0.10, 0.026, (0.25, 0.60, 0.88), r=0.006, lift=0.1)
    for k, col in enumerate(((0.9, 0.2, 0.2), (0.2, 0.6, 0.9), (0.98, 0.78, 0.2), (0.3, 0.7, 0.35))):
        g = _G(c, 0.62 + k * 0.045, 0.06 - k * 0.005, 8 - k * 4)
        g.rect(0.0, 0.0, 0.26, 0.032, col, r=0.012, lift=0.3)
        g.rect(0.0, 0.0, 0.14, 0.034, (0.96, 0.95, 0.92), lift=0.0, alpha=0.8)
        g.poly([(0.13, 0.016), (0.19, 0.0), (0.13, -0.016)], scale(col, 0.7), lift=0.0)


@sprop("pro_ngo_tote", aspect=0.85, fill=1.0)
def ngo_tote(c, color):
    acc = _acc(color, "accent", (0.26, 0.63, 0.28))
    rng = c.rng
    cloth = (0.96, 0.93, 0.84)
    ao(c, 0.0, 0.0, 0.7, 0.20, 0.38)
    # rolled poster and a leafy branch peeking out of the top
    g = _G(c, 0.10, 0.62, 12)
    g.rect(0.0, 0.12, 0.09, 0.50, (0.98, 0.98, 0.95), r=0.04, lift=0.25)
    g.rect(0.0, 0.34, 0.09, 0.06, acc, lift=0.1)
    for k in range(4):
        _leaf(c, -0.10 + k * 0.03, 0.64, rng.uniform(0.18, 0.26), 100 + (k - 1.5) * 24, (0.20 + 0.08 * rng.random(), 0.56, 0.24), 0.4, vein=False)
    # handles
    craft.arc(c, -0.12, 0.64, 0.12, 0.30, 0, 180, 0.030, scale(acc, 0.75), 1.0, 12)
    craft.arc(c, 0.12, 0.64, 0.12, 0.30, 0, 180, 0.030, acc, 1.0, 12)
    # canvas body, slightly tapered, shaded left to right, with printed heart and text
    craft.hshade_box(c, 0.0, 0.30, 0.64, 0.60, cloth, scale(cloth, 0.66), r=0.02)
    for k in range(24):                                                                         # fabric weave
        v = 0.04 + k * 0.024
        c.line(-0.31, v, 0.31, v, 0.0025, scale(cloth, 0.84), 0.35)
    c.rect(0.0, 0.55, 0.64, 0.045, acc, lift=0.12)
    c.rect(0.0, 0.07, 0.64, 0.03, scale(acc, 0.8), lift=0.1)
    _heart(c, 0.0, 0.33, 0.13, scale(HEART, 0.85), 0.2)
    c.text("VOLUNTEER", 0.0, 0.17, 0.040, scale(acc, 0.8), 0.20)
    for k in range(5):
        c.ellipse(-0.25 + k * 0.125, 0.55, 0.012, 0.012, WHITE, lift=0, alpha=0.8)
    soft_disc(c, 0.22, 0.28, 0.14, 0.30, BLACK, 0.26, 1.4)
    gloss(c, -0.22, 0.34, 0.04, 0.22, 0, 0.22)


@niche("ngo", "Non-profit / NGO", subjects=("pro_ngo_box",),
       strong=("ngo", "charity", "non profit", "foundation", "donation", "social work", "एनजीओ", "दान", "ngo trust", "charitable trust", "welfare society",
               "donate now", "non-profit", "seva", "सेवा संस्था", "trust foundation", "volunteer", "fundraising"),
       weak=("volunteers", "orphanage", "relief", "community", "welfare", "help", "cause", "needy", "awareness"),
       accent="#43a047", mood="warm", group="professional")
def ngo(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.55)
        S.glow(0.45, 0.22, 1.1, P.light, 0.35 if not dark else 0.16)
        # window with sunlight, tree outside; children's drawings; bunting
        st, sb = _sky(P)
        S.gradient_rect(0.10, 0.06, 0.62, 0.50, st, sb)
        S.circle(0.28, 0.20, 0.10, (0.28, 0.58, 0.28) if not dark else (0.10, 0.22, 0.14), lift=0.0, alpha=0.9)
        S.circle(0.46, 0.14, 0.12, (0.34, 0.64, 0.32) if not dark else (0.12, 0.26, 0.16), lift=0.0, alpha=0.9)
        S.rect(0.36, 0.50, 0.52, 0.05, scale(P.wall_top, 1.04), lift=0.0)
        S.rect(0.36, 0.28, 0.010, 0.44, scale(P.wall_top, 0.96), lift=0.0)
        S.rect(0.36, 0.22, 0.52, 0.010, scale(P.wall_top, 0.96), lift=0.0)
        for (u, v, w, h, col) in ((1.10, 0.28, 0.20, 0.26, (1.0, 0.8, 0.3)), (1.35, 0.24, 0.17, 0.20, (0.5, 0.78, 0.5)), (1.60, 0.30, 0.22, 0.28, (0.95, 0.55, 0.5)),
                                  (1.84, 0.25, 0.16, 0.20, P.accent_light)):
            S.rect(u, v, w + 0.02, h + 0.02, mix(WHITE, P.wall_top, 0.3) if not dark else scale(P.wall_top, 1.5), lift=0.0)
            S.rect(u, v, w, h, mix(col, P.wall_bot, 0.4 if dark else 0.0), lift=0.0)
            S.circle(u - w * 0.15, v - h * 0.15, w * 0.15, (1.0, 0.95, 0.6), lift=0.0)
            S.rect(u + w * 0.1, v + h * 0.2, w * 0.5, h * 0.35, mix(col, WHITE, 0.4), lift=0.0)
        S.line(0.0, 0.03, 2.0, 0.08, 0.004, (0.45, 0.40, 0.35), 0.9)
        cols = (P.accent, (1.0, 0.8, 0.3), (0.95, 0.5, 0.45), P.accent2, WHITE)
        for k in range(22):
            u = 0.04 + k * 0.092
            v = 0.03 + 0.05 * (u / 2.0)
            S.poly([(u - 0.035, v), (u + 0.035, v), (u, v + 0.075)], mix(cols[k % 5], P.wall_bot, 0.4 if dark else 0.0))
        S.pendant(0.95, -0.1, 0.16, (1.0, 0.88, 0.6), 0.08)
        S.bokeh(10, 0.0, 0.10, 2.0, 0.5, [(1.0, 0.85, 0.5), P.accent_light, (1.0, 0.7, 0.6)], 0.012, 0.04, 0.32)
        S.floor(0.55, P.floor_top, P.floor_bot)
    S.light_shaft(0.12, 0.30, 0.60, 0.30, 1.30, 1.4, 0.70, 1.4, P.light, 0.07 if not dark else 0.04)
    S.soft(1.15, 0.64, 1.0, 0.12, (1.0, 0.92, 0.72), 0.22 if not dark else 0.28, 1.5, add=True)
    S.wood(-5.0, 0.55, 7.0, 2.6, P.surface, plank=0.12, grain=0.45)
    S.rect(1.0, 0.55, 14.0, 0.008, scale(P.surface, 0.5), lift=0.0)
    # a woven runner under the display
    run = mix(P.accent, WHITE, 0.25)
    for k, col in enumerate((run, (1.0, 0.82, 0.35), WHITE, (0.95, 0.55, 0.45), run)):
        S.rect(1.10, 0.74 + k * 0.05, 1.50, 0.05, mix(col, P.surface, 0.1 if not dark else 0.5), lift=0.0, alpha=0.95)
    S.soft(1.05, 0.88, 0.7, 0.20, (1.0, 0.92, 0.72), 0.14 if not dark else 0.30, 1.5, add=True)
    S.put("pro_ngo_parcels", 0.66, 0.84, 0.34, color=P, shadow_alpha=0.34)
    S.put("pro_ngo_tote", 1.56, 0.84, 0.36, color=P, shadow_alpha=0.34)
    S.put("pro_ngo_box", 1.06, 0.92, 0.46, color=P, subject=True, shadow_alpha=0.36)
    S.put("pro_ngo_hands", 1.40, 1.0, 0.22, color=P, shadow_alpha=0.32)
    S.put("pro_ngo_books", 0.84, 1.0, 0.16, color=P, shadow_alpha=0.30)
    S.focus("detail", 1.20, 0.80)
    with S.near():
        S.circle(0.55, 0.98, 0.04, (1.0, 0.8, 0.4), alpha=0.40, lift=0)
        S.circle(1.66, 0.40, 0.05, P.accent_light, alpha=0.24, lift=0)
