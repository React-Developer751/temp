"""More food and drink niches: cafe, bakery, indian thali, fast food, ice cream, juice bar, sweet shop, sushi."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, drip, gloss, leaf, soft_disc, speckle, steam
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale

BRASS = (0.86, 0.62, 0.24)


# ---------------------------------------------------------------------------------------------- shared helpers
def _ball(c, u, v, r, col, tilt=1.0, rim=0.62, hl=0.4):
    """A shaded sphere (laddu, scoop, fruit): dark rim, lit body, shade low right, soft highlight upper left."""
    c.ellipse(u, v, r, r * tilt, scale(col, rim), lift=0)
    c.ellipse(u - r * 0.05, v + r * 0.06 * tilt, r * 0.94, r * 0.92 * tilt, col, lift=0.16)
    soft_disc(c, u + r * 0.28, v - r * 0.3 * tilt, r * 0.62, r * 0.5 * tilt, scale(col, 0.4), 0.42, 1.3)
    if hl:
        soft_disc(c, u - r * 0.34, v + r * 0.36 * tilt, r * 0.34, r * 0.22 * tilt, WHITE, hl, 1.1, add=True)


def _vlines(c, u0, v0, u1, v1, n, col, alpha, w=0.004):
    """n seeded short strokes inside a box (grain, weave, crumb texture)."""
    rng = c.rng
    for _ in range(n):
        x = rng.uniform(u0, u1)
        y = rng.uniform(v0, v1)
        c.line(x, y, x + rng.uniform(-0.02, 0.02), y + rng.uniform(0.02, 0.06), w, col, alpha)


def _near_leaf(S, u, v, length, angle, color, width=0.4):
    """A soft foreground leaf drawn with a polygon (use inside `with S.near()`)."""
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    wd = length * width / 2
    pts = []
    for k in range(9):
        t = k / 8.0
        pts.append((t * length, math.sin(math.pi * t) ** 0.8 * wd))
    ring = pts + [(x, -y) for x, y in reversed(pts)]
    S.poly([(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in ring], color)


def _croissant(c, u, v, k, col=None):
    """A croissant lying on a surface: seven fat segments along an arch, darker grooves, flaky sheen."""
    rng = c.rng
    soft_disc(c, u + 0.02 * k, v + 0.02 * k, 0.46 * k, 0.10 * k, BLACK, 0.38, 1.4)
    for i in sorted(range(7), key=lambda j: -abs(j - 3)):
        t = (i - 3) / 3.0
        x = u + 0.40 * k * t
        arch = 0.10 + 0.12 * (1 - t * t)
        ang = -t * 38
        b = (0.05 + 0.095 * (1 - t * t) ** 0.7) * k
        a = (0.075 + 0.02 * (1 - abs(t))) * k
        y = v + arch * k
        c.ellipse(x, y, a * 1.12, b * 1.1, (0.50, 0.26, 0.09), angle=ang, lift=0)
        c.ellipse(x - 0.006 * k, y + 0.012 * k, a, b * 0.96, mix((0.88, 0.58, 0.24), col or (0.88, 0.58, 0.24), 0.0), angle=ang, lift=0.2)
        soft_disc(c, x - 0.03 * k, y + b * 0.35, a * 0.55, b * 0.55, (1.0, 0.86, 0.55), 0.35, 1.2, ang, add=True)
        soft_disc(c, x + a * 0.55, y - b * 0.2, a * 0.5, b * 0.7, (0.35, 0.16, 0.05), 0.35, 1.3, ang)
    for _ in range(12):
        t = rng.uniform(-0.9, 0.9)
        x = u + 0.40 * k * t + rng.uniform(-0.04, 0.04) * k
        y = v + (0.10 + 0.22 * (1 - t * t)) * k + rng.uniform(-0.03, 0.05) * k
        c.ellipse(x, y, 0.012 * k, 0.006 * k, (0.97, 0.80, 0.48), lift=0, alpha=0.7, angle=rng.uniform(0, 180))


# ---------------------------------------------------------------------------------------------- cafe
@sprop("cafe_latte_cup", aspect=1.25, fill=0.8)
def cafe_latte_cup(c, color):
    rng = c.rng
    cer = color or (0.97, 0.95, 0.91)
    ao(c, 0.0, 0.0, 1.0, 0.36)
    disc(c, 0.0, 0.04, 0.54, scale(cer, 0.93), TILT, 0.08)                       # saucer
    c.ellipse(0.0, 0.055, 0.36, 0.36 * TILT, scale(cer, 0.84), lift=0)
    c.ellipse(0.0, 0.06, 0.33, 0.33 * TILT, scale(cer, 0.97), lift=0.05)
    soft_disc(c, 0.07, 0.045, 0.34, 0.09, BLACK, 0.28, 1.4)                        # cup shadow on the saucer
    c.line(0.20, 0.03, 0.50, 0.075, 0.024, (0.80, 0.80, 0.82))                       # teaspoon
    c.ellipse(0.52, 0.08, 0.05, 0.03, (0.84, 0.84, 0.86), angle=12, lift=0.1)
    craft.arc(c, 0.30, 0.235, 0.12, 0.105, -90, 90, 0.05, scale(cer, 0.88))             # handle
    craft.arc(c, 0.30, 0.245, 0.12, 0.105, -60, 70, 0.012, WHITE, 0.55)
    c.ellipse(0.0, 0.10, 0.215, 0.215 * TILT, scale(cer, 0.76), lift=0)               # body
    c.poly([(-0.30, 0.35), (0.30, 0.35), (0.215, 0.10), (-0.215, 0.10)], cer, lift=0.05)
    c.ellipse(0.0, 0.10, 0.212, 0.212 * TILT, scale(cer, 0.93), lift=0.0)
    for x0, al in ((0.10, 0.10), (0.15, 0.10), (0.20, 0.12), (0.245, 0.14)):
        c.poly([(x0, 0.35), (0.30, 0.35), (0.215, 0.10), (x0 * 0.72, 0.10)], (0.40, 0.34, 0.30), lift=0, alpha=al)
    c.poly([(-0.26, 0.335), (-0.19, 0.335), (-0.135, 0.13), (-0.17, 0.13)], WHITE, lift=0, alpha=0.55)
    c.ellipse(0.0, 0.35, 0.30, 0.30 * TILT, scale(cer, 0.80), lift=0)                  # rim
    c.ellipse(0.0, 0.353, 0.296, 0.296 * TILT, cer, lift=0.06)
    c.ellipse(0.0, 0.347, 0.262, 0.262 * TILT, (0.28, 0.16, 0.09), lift=0)             # coffee
    c.ellipse(0.0, 0.344, 0.248, 0.248 * TILT, (0.60, 0.38, 0.19), lift=0.12)
    soft_disc(c, 0.0, 0.372, 0.26, 0.05, (0.2, 0.1, 0.05), 0.55, 1.2)
    c.ellipse(0.0, 0.343, 0.20, 0.20 * TILT, (0.96, 0.89, 0.76), lift=0.08, alpha=0.95)    # foam
    for i, w in enumerate((0.17, 0.15, 0.125, 0.10, 0.065)):                          # rosetta layers
        y = 0.318 + i * 0.0225
        c.ellipse(0.0, y, w + 0.011, 0.0285, (0.55, 0.33, 0.16), lift=0, alpha=0.8)
        c.ellipse(0.0, y + 0.002, w, 0.0215, (0.99, 0.95, 0.86), lift=0.1)
    c.line(0.0, 0.31, 0.0, 0.385, 0.007, (0.5, 0.3, 0.14), 0.7)
    gloss(c, -0.09, 0.352, 0.11, 0.03, 8, 0.38)
    gloss(c, -0.20, 0.24, 0.018, 0.09, 0, 0.30)
    for k in range(6):                                                               # coffee beans on the table
        x, y = -0.62 + k * 0.045 + rng.uniform(-0.03, 0.03), 0.02 + rng.uniform(-0.01, 0.045)
        c.ellipse(x, y - 0.006, 0.036, 0.024, (0.14, 0.07, 0.04), lift=0, angle=rng.uniform(0, 180))
        c.ellipse(x, y, 0.034, 0.022, (0.30, 0.17, 0.09), lift=0.2, angle=rng.uniform(0, 180))
        c.ellipse(x - 0.004, y + 0.006, 0.012, 0.005, (0.6, 0.4, 0.25), lift=0, alpha=0.6)
    steam(c, 0.0, 0.40, 0.38, 0.05, 2, 0.16)


@sprop("cafe_croissant", aspect=2.1, fill=0.5)
def cafe_croissant(c, color):
    ao(c, 0.0, 0.0, 1.05, 0.32)
    disc(c, 0.0, 0.04, 0.52, (0.96, 0.95, 0.92), TILT, 0.08)
    c.ellipse(0.0, 0.055, 0.40, 0.40 * TILT, (0.86, 0.85, 0.82), lift=0)
    c.ellipse(0.0, 0.06, 0.38, 0.38 * TILT, (0.95, 0.94, 0.91), lift=0.06)
    _croissant(c, 0.0, 0.04, 1.0)
    for _ in range(6):                                                               # crumbs
        c.ellipse(c.rng.uniform(-0.45, 0.45), c.rng.uniform(0.02, 0.08), 0.01, 0.006, (0.8, 0.55, 0.28), lift=0, alpha=0.8)


@sprop("cafe_laptop", aspect=1.75, fill=0.62)
def cafe_laptop(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.18)
    c.poly([(-0.55, 0.075), (0.55, 0.075), (0.60, 0.0), (-0.60, 0.0)], (0.55, 0.56, 0.58), lift=0.1)
    c.poly([(-0.52, 0.60), (0.52, 0.60), (0.54, 0.07), (-0.54, 0.07)], (0.72, 0.73, 0.75), lift=0.12)    # lid back
    c.poly([(0.0, 0.60), (0.52, 0.60), (0.54, 0.07), (0.0, 0.07)], (0.45, 0.46, 0.5), lift=0, alpha=0.30)
    c.poly([(-0.50, 0.58), (-0.42, 0.58), (-0.44, 0.09), (-0.52, 0.09)], WHITE, lift=0, alpha=0.35)
    soft_disc(c, -0.1, 0.40, 0.45, 0.22, WHITE, 0.22, 1.3, add=True)
    c.circle(0.0, 0.33, 0.07, (0.92, 0.92, 0.94), lift=0.1)
    soft_disc(c, 0.0, 0.33, 0.17, 0.17, WHITE, 0.28, 1.2, add=True)
    for u, v, w, h, col in ((-0.30, 0.46, 0.15, 0.10, (0.9, 0.35, 0.3)), (0.28, 0.20, 0.13, 0.13, (0.3, 0.6, 0.85)),
                            (-0.22, 0.18, 0.12, 0.08, (0.95, 0.8, 0.3)), (0.30, 0.48, 0.11, 0.07, (0.3, 0.7, 0.5))):
        c.rect(u, v, w, h, col, r=0.025, lift=0.1)
        c.rect(u - w * 0.15, v + h * 0.2, w * 0.4, h * 0.25, WHITE, r=0.01, lift=0, alpha=0.5)


@sprop("cafe_plant", aspect=0.8, fill=1.0)
def cafe_plant(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.55, 0.10)
    craft.hshade_box(c, 0.0, 0.15, 0.40, 0.30, (0.96, 0.95, 0.92), (0.66, 0.64, 0.60), r=0.05)
    disc(c, 0.0, 0.30, 0.20, (0.30, 0.20, 0.13), TILT, 0.0)
    for i in range(18):
        a = rng.uniform(25, 155)
        leaf(c, rng.uniform(-0.08, 0.08), 0.31, rng.uniform(0.28, 0.5), a + rng.uniform(-10, 10),
             (0.14 + rng.random() * 0.1, 0.42 + rng.random() * 0.16, 0.2), 0.42)


@niche("cafe", "Cafe", subjects=("cafe_latte_cup",),
       strong=("cafe", "café", "coffee shop", "coffeehouse", "latte", "cappuccino", "espresso bar", "barista", "chai cafe",
               "coffee house", "कैफे", "कॉफी शॉप", "कॉफ़ी", "चाय कैफे"),
       weak=("coffee", "tea", "brunch", "croissant", "chai", "कॉफी", "pastry"),
       accent="#8b5a2b", mood="warm", group="food", avoid=("coffee machine factory",))
def cafe(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        mortar = scale(P.wall_top, 0.9)
        S.rect(1.0, 0.25, 8.0, 0.95, mortar, lift=0.0)
        brick = mix(P.wall_bot, P.accent, 0.22)
        rng = S.rng
        for row in range(0, 15):
            vv = -0.18 + row * 0.056
            off = 0.0 if row % 2 else 0.07
            for i in range(-30, 40):
                S.rect(-3.0 + i * 0.14 + off, vv, 0.132, 0.05, scale(brick, rng.uniform(0.86, 1.06)), lift=0.0)
        S.rect(0.36, 0.28, 0.50, 0.42, scale(P.ink, 2.2 if not dark else 1.2), lift=0.0)           # window frame
        S.gradient_rect(0.14, 0.09, 0.58, 0.47, (0.62, 0.78, 0.74), (0.97, 0.93, 0.80))
        S.bokeh(7, 0.14, 0.12, 0.58, 0.44, [(0.45, 0.65, 0.35), (1.0, 0.95, 0.75), (0.8, 0.5, 0.35)], 0.02, 0.05, 0.5)
        S.rect(0.36, 0.28, 0.012, 0.40, scale(P.ink, 2.2 if not dark else 1.2), lift=0.0)
        S.rect(0.36, 0.2, 0.44, 0.012, scale(P.ink, 2.2 if not dark else 1.2), lift=0.0)
        S.glow(0.36, 0.28, 0.7, P.light, 0.35)
        S.rect(1.55, 0.31, 0.62, 0.016, scale(P.surface, 0.8), lift=0.05)                          # shelf
        for i, u in enumerate((1.30, 1.43, 1.56, 1.69, 1.80)):
            S.rect(u, 0.275, 0.07, 0.055, (0.93, 0.92, 0.88) if i % 2 else mix(P.accent, WHITE, 0.3), r=0.01, lift=0.08)
        S.pendant(1.12, -0.1, 0.13, (1.0, 0.8, 0.5), 0.10)
        S.pendant(1.62, -0.1, 0.10, (1.0, 0.8, 0.5), 0.08)
        S.bokeh(8, 0.6, 0.02, 2.0, 0.30, [(1.0, 0.85, 0.55), (1.0, 0.72, 0.45)], 0.012, 0.04)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.58, 5.0, 1.4, scale(P.surface, 0.78), plank=0.13, grain=0.5)
    S.rect(1.0, 0.58, 8.0, 0.009, scale(P.surface, 0.4), lift=0.0)
    S.soft(1.1, 0.80, 0.95, 0.20, P.light, 0.32 if not dark else 0.45, 1.5, add=True)
    S.put("cafe_laptop", 0.66, 0.67, 0.20)
    S.put("cafe_plant", 1.58, 0.68, 0.17)
    S.put("cafe_latte_cup", 1.05, 0.88, 0.50, subject=True)
    S.put("cafe_croissant", 1.50, 0.98, 0.17)
    S.focus("detail", 1.05, 0.74)
    with S.near(18.0):
        S.soft(0.62, 1.02, 0.14, 0.06, (0.35, 0.5, 0.25), 0.45, 1.0, 40)
        S.soft(1.7, 1.0, 0.08, 0.08, mix(P.accent, WHITE, 0.4), 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- bakery
def _baguette(c, u0, v0, u1, v1, w):
    """A baguette as a stack of capsules (shaded like a cylinder) with diagonal scoring cuts."""
    rng = c.rng
    c.line(u0, v0, u1, v1, w * 1.08, (0.48, 0.27, 0.10))
    c.line(u0, v0, u1, v1, w * 0.92, (0.80, 0.52, 0.22))
    c.line(u0 - w * 0.12, v0 + w * 0.12, u1 - w * 0.12, v1 + w * 0.10, w * 0.52, (0.93, 0.68, 0.34), 0.9)
    c.line(u0 - w * 0.20, v0 + w * 0.2, u1 - w * 0.2, v1 + w * 0.18, w * 0.16, (1.0, 0.86, 0.55), 0.6)
    for k in range(5):
        t = 0.30 + k * 0.13
        x, y = u0 + (u1 - u0) * t, v0 + (v1 - v0) * t
        c.line(x - w * 0.28, y - w * 0.16, x + w * 0.22, y + w * 0.22, w * 0.18, (0.98, 0.84, 0.55), 0.85)
        c.line(x - w * 0.2, y - w * 0.1, x + w * 0.18, y + w * 0.16, w * 0.07, (0.66, 0.38, 0.14), 0.7)
    for _ in range(9):
        t = rng.uniform(0.1, 0.95)
        c.ellipse(u0 + (u1 - u0) * t + rng.uniform(-w, w) * 0.3, v0 + (v1 - v0) * t + rng.uniform(-w, w) * 0.3, 0.01, 0.006, (1.0, 0.96, 0.88),
                  lift=0, alpha=0.55)


@sprop("bakery_basket", aspect=1.35, fill=1.0)
def bakery_basket(c, color):
    rng = c.rng
    wick = (0.76, 0.54, 0.29)
    ao(c, 0.0, 0.0, 1.0, 0.24)
    c.poly([(-0.48, 0.34), (0.48, 0.34), (0.40, 0.04), (-0.40, 0.04)], wick, lift=0.08)
    c.ellipse(0.0, 0.05, 0.40, 0.40 * 0.32, scale(wick, 0.8), lift=0)
    c.poly([(-0.47, 0.335), (0.47, 0.335), (0.395, 0.06), (-0.395, 0.06)], wick, lift=0.08)
    c.ellipse(0.0, 0.34, 0.48, 0.48 * 0.34, scale(wick, 0.72), lift=0)                 # rim back and dark interior
    c.ellipse(0.0, 0.345, 0.44, 0.44 * 0.32, (0.25, 0.14, 0.07), lift=0)
    for u0, u1, v1 in ((-0.30, -0.62, 0.80), (-0.08, -0.22, 0.90), (0.12, 0.22, 0.86), (0.30, 0.58, 0.78)):
        _baguette(c, u0, 0.30, u1, v1, 0.12)
    c.ellipse(0.0, 0.25, 0.50, 0.12, (0.15, 0.08, 0.04), alpha=0.5, lift=0)             # baguette feet vanish into the basket
    soft_disc(c, 0.0, 0.31, 0.48, 0.10, (0.12, 0.06, 0.03), 0.6, 1.0)
    # front wall: weave bands + rim
    c.poly([(-0.47, 0.335), (-0.44, 0.335), (-0.37, 0.06), (-0.40, 0.06)], wick, lift=0, alpha=0.0)
    for j in range(5):
        y0 = 0.07 + j * 0.052
        half = 0.405 + (y0 - 0.04) * 0.25
        tone = 1.0 + (0.07 if j % 2 else -0.06)
        c.rect(0.0, y0 + 0.026, 2 * half - 0.01, 0.045, scale(wick, tone), r=0.02, lift=0.12)
        for i in range(-9, 10, 1):
            x = i * 0.049 + (0.024 if j % 2 else 0.0)
            if abs(x) < half - 0.03:
                c.line(x, y0 + 0.005, x + 0.004, y0 + 0.048, 0.007, scale(wick, 0.66), 0.55)
    c.ellipse(0.0, 0.34, 0.48, 0.48 * 0.34, wick, lift=0, alpha=0.0)
    craft.arc(c, 0.0, 0.34, 0.48, 0.48 * 0.34, 180, 360, 0.04, scale(wick, 1.08), steps=14)
    craft.arc(c, 0.0, 0.343, 0.47, 0.47 * 0.34, 195, 345, 0.012, (1.0, 0.9, 0.7), 0.5, steps=12)
    soft_disc(c, 0.3, 0.14, 0.3, 0.14, BLACK, 0.22, 1.4)
    soft_disc(c, -0.25, 0.7, 0.45, 0.3, (1.0, 0.95, 0.85), 0.14, 1.3, add=True)


@sprop("bakery_loaves", aspect=1.7, fill=0.5)
def bakery_loaves(c, color):
    rng = c.rng
    board = (0.80, 0.60, 0.36)
    ao(c, 0.0, 0.0, 1.5, 0.26)
    c.ellipse(0.0, 0.03, 0.82, 0.82 * 0.34, scale(board, 0.7), lift=0)               # round board
    disc(c, 0.0, 0.055, 0.82, board, 0.34, 0.1)
    for _ in range(8):
        a = rng.uniform(0.3, 0.75)
        craft.arc(c, rng.uniform(-0.1, 0.1), 0.055, a, a * 0.34, rng.uniform(0, 200), rng.uniform(220, 340), 0.004, scale(board, 0.84), 0.4)
    # sourdough boule (back left)
    bu, bv = -0.28, 0.17
    soft_disc(c, bu + 0.04, bv - 0.07, 0.36, 0.075, BLACK, 0.4, 1.3)
    c.ellipse(bu, bv + 0.12, 0.33, 0.21, (0.52, 0.28, 0.10), lift=0)
    c.ellipse(bu - 0.01, bv + 0.14, 0.32, 0.20, (0.80, 0.50, 0.22), lift=0.22)
    soft_disc(c, bu + 0.12, bv + 0.06, 0.26, 0.12, (0.30, 0.13, 0.04), 0.5, 1.3)
    soft_disc(c, bu - 0.10, bv + 0.25, 0.2, 0.08, (1.0, 0.88, 0.6), 0.45, 1.1, add=True)
    craft.arc(c, bu - 0.02, bv + 0.12, 0.25, 0.14, 25, 150, 0.05, (0.97, 0.84, 0.58), 0.95, 9)           # scored ear
    craft.arc(c, bu - 0.02, bv + 0.10, 0.25, 0.14, 30, 150, 0.014, (0.55, 0.30, 0.12), 0.7, 9)
    for _ in range(40):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random())
        c.ellipse(bu + math.cos(a) * 0.28 * r, bv + 0.16 + math.sin(a) * 0.13 * r, rng.uniform(0.004, 0.011), rng.uniform(0.003, 0.007),
                  (1.0, 0.97, 0.92), lift=0, alpha=rng.uniform(0.25, 0.7))
    # batard with slices (right)
    pu, pv = 0.38, 0.10
    soft_disc(c, pu + 0.04, pv - 0.04, 0.42, 0.07, BLACK, 0.4, 1.3)
    c.ellipse(pu, pv + 0.09, 0.38, 0.15, (0.50, 0.27, 0.10), lift=0)
    c.ellipse(pu - 0.01, pv + 0.105, 0.37, 0.14, (0.82, 0.53, 0.24), lift=0.2)
    soft_disc(c, pu - 0.08, pv + 0.17, 0.25, 0.05, (1.0, 0.88, 0.6), 0.4, 1.1, add=True)
    for k in range(4):
        x = pu - 0.2 + k * 0.12
        c.line(x - 0.03, pv + 0.07, x + 0.05, pv + 0.17, 0.035, (0.98, 0.86, 0.6), 0.9)
    for i in range(2):                                                               # cut slices
        sx, sy = 0.16 + i * 0.30, 0.02 + i * 0.01
        c.rect(sx, sy + 0.10, 0.20, 0.17, (0.70, 0.42, 0.17), r=0.07, lift=0.08)
        c.rect(sx, sy + 0.105, 0.175, 0.145, (0.98, 0.91, 0.72), r=0.06, lift=0.12)
        for _ in range(16):
            c.ellipse(sx + rng.uniform(-0.07, 0.07), sy + 0.105 + rng.uniform(-0.055, 0.055), rng.uniform(0.004, 0.012), rng.uniform(0.003, 0.008),
                      (0.85, 0.72, 0.48), lift=0, alpha=0.7)
    for _ in range(14):
        c.ellipse(rng.uniform(-0.75, 0.7), rng.uniform(0.0, 0.09), rng.uniform(0.006, 0.012), 0.005, (1.0, 0.97, 0.9), lift=0, alpha=0.7)


@sprop("bakery_cloche", aspect=0.95, fill=1.0)
def bakery_cloche(c, color):
    ao(c, 0.0, 0.0, 0.9, 0.2)
    c.rect(0.0, 0.07, 0.10, 0.12, (0.90, 0.88, 0.84), lift=0.1)                       # cake stand foot
    disc(c, 0.0, 0.14, 0.46, (0.96, 0.95, 0.92), TILT, 0.1)
    c.ellipse(0.0, 0.13, 0.46, 0.46 * TILT, (0.75, 0.74, 0.72), lift=0, alpha=0.8)
    disc(c, 0.0, 0.15, 0.44, (0.97, 0.96, 0.93), TILT, 0.08, rim=False)
    soft_disc(c, 0.0, 0.16, 0.42, 0.10, BLACK, 0.12, 1.3)
    _croissant(c, -0.17, 0.12, 0.60)
    _croissant(c, 0.19, 0.17, 0.52)
    # glass dome
    c.ellipse(0.0, 0.62, 0.46, 0.47, (0.88, 0.95, 0.97), alpha=0.16, lift=0)
    c.rect(0.0, 0.40, 0.92, 0.5, (0.88, 0.95, 0.97), alpha=0.0, lift=0)
    c.poly([(-0.46, 0.17), (0.46, 0.17), (0.46, 0.60), (-0.46, 0.60)], (0.88, 0.95, 0.97), alpha=0.13, lift=0)
    craft.arc(c, 0.0, 0.60, 0.46, 0.46, 0, 180, 0.014, (1.0, 1.0, 1.0), 0.55, steps=14)
    craft.arc(c, 0.0, 0.60, 0.40, 0.40, 105, 160, 0.03, (1.0, 1.0, 1.0), 0.55, steps=6)
    c.line(-0.455, 0.17, -0.455, 0.60, 0.014, (1.0, 1.0, 1.0), 0.5)
    c.line(0.455, 0.17, 0.455, 0.60, 0.012, (0.85, 0.92, 0.95), 0.45)
    craft.arc(c, 0.0, 0.17, 0.46, 0.46 * TILT, 180, 360, 0.012, (1.0, 1.0, 1.0), 0.5, steps=12)
    c.circle(0.0, 1.10, 0.035, (0.92, 0.92, 0.94), lift=0.2)
    soft_disc(c, -0.2, 0.55, 0.12, 0.22, WHITE, 0.30, 1.2, 12, add=True)


@niche("bakery", "Bakery", subjects=("bakery_basket",),
       strong=("bakery", "bakeshop", "baker", "bread shop", "sourdough", "baguette", "patisserie", "bake house", "bekri", "bakri ki dukan",
               "बेकरी", "ब्रेड", "पाव", "बेकरी शॉप"),
       weak=("bread", "loaf", "croissant", "pastry", "cake", "flour", "bun", "rolls", "बेक"),
       accent="#d98e32", mood="warm", group="food")
def bakery(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.50, 8.0, 0.4, scale(P.wall_bot, 0.88), lift=0.0)                              # wainscot
        S.rect(1.0, 0.31, 8.0, 0.012, scale(P.wall_bot, 0.6), lift=0.0)
        wood = scale(P.surface, 0.9)
        for sv in (0.18, 0.36):                                                                   # shelves with bread
            S.rect(1.0, sv, 8.0, 0.02, wood, lift=0.05)
            u = -1.0
            while u < 3.2:
                kind = S.rng.random()
                if kind < 0.45:
                    S.ellipse(u, sv - 0.04, 0.08, 0.055, (0.80, 0.52, 0.24), lift=0.1)
                    u += 0.20
                elif kind < 0.8:
                    S.line(u - 0.1, sv - 0.018, u + 0.1, sv - 0.06, 0.04, (0.84, 0.58, 0.28))
                    u += 0.24
                else:
                    S.rect(u, sv - 0.04, 0.12, 0.07, mix(P.accent, WHITE, 0.45), r=0.012, lift=0.1)
                    u += 0.19
        S.rect(0.32, 0.12, 0.52, 0.2, scale(P.ink, 2.0 if not dark else 1.2), lift=0.0)           # chalkboard
        S.text("FRESH BREAD", 0.32, 0.12, 0.05, (0.92, 0.92, 0.9), 0.1)
        S.pendant(0.95, -0.1, 0.09, (1.0, 0.8, 0.5), 0.09)
        S.pendant(1.55, -0.1, 0.09, (1.0, 0.8, 0.5), 0.09)
        S.glow(1.0, 0.25, 1.3, (1.0, 0.85, 0.55), 0.22)
        S.floor(0.60, P.floor_top, P.floor_bot)
    top = scale(mix(P.paper, P.surface, 0.28), 0.72 if dark else 1.0)
    S.rect(1.0, 1.0, 8.0, 0.8, top, lift=0.0)                                                       # marble counter top
    S.rect(1.0, 0.66, 8.0, 0.12, scale(top, 0.93), lift=0.0)
    S.rect(1.0, 1.28, 8.0, 0.2, scale(top, 0.93), lift=0.0)
    S.rect(1.0, 0.60, 8.0, 0.012, scale(top, 0.6), lift=0.0)
    for _ in range(26):
        u = S.rng.uniform(-1, 3.2)
        v = S.rng.uniform(0.62, 1.35)
        S.line(u, v, u + S.rng.uniform(0.1, 0.5), v + S.rng.uniform(-0.1, 0.1), 0.003, scale(top, 0.72), 0.22)
    S.rect(1.15, 0.80, 1.35, 0.30, mix(P.accent, WHITE, 0.55), r=0.01, alpha=0.5, lift=0.0)          # linen runner
    for k in range(10):
        S.rect(0.5 + k * 0.14, 0.80, 0.012, 0.30, mix(P.accent, WHITE, 0.2), alpha=0.35, lift=0.0)
    S.soft(1.1, 0.80, 0.95, 0.22, P.light, 0.26 if not dark else 0.4, 1.5, add=True)
    S.put("bakery_cloche", 0.66, 0.72, 0.36)
    S.put("bakery_basket", 1.24, 0.80, 0.40, subject=True)
    S.put("bakery_loaves", 1.12, 0.97, 0.26)
    S.focus("detail", 1.22, 0.62)
    with S.near(16.0):
        S.soft(1.58, 1.02, 0.12, 0.06, (0.96, 0.9, 0.78), 0.8, 1.0, -12)
        S.soft(0.58, 1.02, 0.06, 0.06, (0.9, 0.7, 0.4), 0.6, 1.0)


# ---------------------------------------------------------------------------------------------- indian thali
def _katori(c, u, v, r, kind):
    """A small steel/brass bowl seen from above with food in it; kind picks the food."""
    rng = c.rng
    tl = 0.46
    soft_disc(c, u + r * 0.25, v - r * 0.18, r * 1.2, r * 0.6, BLACK, 0.40, 1.4)
    c.ellipse(u, v - r * 0.20, r, r * tl, (0.55, 0.40, 0.17), lift=0)                       # outer wall (front)
    c.ellipse(u, v - r * 0.05, r, r * tl, (0.78, 0.58, 0.28), lift=0.1)
    c.ellipse(u, v, r * 0.97, r * tl * 0.96, (0.94, 0.80, 0.50), lift=0.18)                 # rim
    c.ellipse(u, v + r * 0.03, r * 0.84, r * tl * 0.82, (0.36, 0.25, 0.10), lift=0)         # inside
    f = {"dal": ((0.90, 0.68, 0.14), (0.78, 0.40, 0.08)), "paneer": ((0.36, 0.52, 0.16), (0.85, 0.80, 0.55)),
         "curry": ((0.72, 0.22, 0.08), (0.98, 0.85, 0.62)), "raita": ((0.97, 0.96, 0.92), (0.55, 0.7, 0.3)),
         "sweet": ((0.45, 0.20, 0.07), (0.9, 0.6, 0.2))}[kind]
    c.ellipse(u, v + r * 0.07, r * 0.78, r * tl * 0.76, f[0], lift=0.12)
    soft_disc(c, u + r * 0.2, v + r * 0.0, r * 0.7, r * 0.3, scale(f[0], 0.4), 0.32, 1.2)
    if kind == "dal":
        for _ in range(7):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.6
            c.ellipse(u + math.cos(a) * r * q, v + r * 0.07 + math.sin(a) * r * q * tl, r * 0.09, r * 0.045, f[1], lift=0, alpha=0.8)
        c.ellipse(u + r * 0.1, v + r * 0.07, r * 0.07, r * 0.035, (0.5, 0.15, 0.05), lift=0)
    elif kind == "paneer":
        for _ in range(5):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.5
            c.rect(u + math.cos(a) * r * q, v + r * 0.09 + math.sin(a) * r * q * tl, r * 0.3, r * 0.17, f[1], r=r * 0.04, lift=0.15)
        c.ellipse(u, v + r * 0.1, r * 0.3, r * 0.1, (0.18, 0.38, 0.1), lift=0, alpha=0.5)
    elif kind == "curry":
        craft.arc(c, u, v + r * 0.08, r * 0.4, r * 0.4 * tl, 10, 330, r * 0.09, f[1], 0.9, 8)
        for _ in range(6):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.6
            c.ellipse(u + math.cos(a) * r * q, v + r * 0.08 + math.sin(a) * r * q * tl, r * 0.1, r * 0.06, (0.5, 0.1, 0.04), lift=0.1)
    elif kind == "raita":
        for _ in range(8):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.65
            c.ellipse(u + math.cos(a) * r * q, v + r * 0.08 + math.sin(a) * r * q * tl, r * 0.05, r * 0.03, f[1], lift=0, alpha=0.8)
        c.ellipse(u, v + r * 0.09, r * 0.12, r * 0.05, (0.9, 0.55, 0.25), lift=0, alpha=0.5)
    else:                                                                              # gulab jamun in syrup
        for i, (dx, dy) in enumerate(((-0.28, 0.0), (0.22, 0.05), (0.0, 0.22))):
            _ball(c, u + dx * r, v + r * 0.1 + dy * r * 0.7, r * 0.32, (0.50, 0.22, 0.08), 0.8, hl=0.5)
    soft_disc(c, u - r * 0.3, v + r * 0.15, r * 0.35, r * 0.1, WHITE, 0.55, 1.1, add=True)


@sprop("indian_thali", aspect=2.6, fill=0.7)
def indian_thali(c, color):
    rng = c.rng
    cu, cv = 0.0, 0.31
    ao(c, 0.0, 0.0, 1.9, 0.5)
    c.ellipse(cu, cv - 0.05, 0.93, 0.375, (0.42, 0.28, 0.10), lift=0)                       # plate thickness
    c.ellipse(cu, cv, 0.93, 0.375, (0.50, 0.33, 0.10), lift=0.14)                           # rim, outer
    c.ellipse(cu, cv + 0.01, 0.90, 0.36, (0.95, 0.72, 0.30), lift=0.2)                      # rim lit
    craft.arc(c, cu, cv + 0.012, 0.865, 0.345, 110, 200, 0.03, (1.0, 0.95, 0.72), 0.75, 10)
    craft.arc(c, cu, cv + 0.012, 0.865, 0.345, 330, 380, 0.02, (0.4, 0.24, 0.06), 0.6, 8)
    c.ellipse(cu, cv + 0.02, 0.80, 0.318, (0.72, 0.52, 0.22), lift=0.14)                    # inner dish
    c.ellipse(cu, cv + 0.015, 0.76, 0.30, (0.84, 0.63, 0.28), lift=0.1)
    soft_disc(c, 0.25, cv - 0.04, 0.8, 0.25, (0.35, 0.2, 0.05), 0.45, 1.3)
    soft_disc(c, -0.35, cv + 0.12, 0.6, 0.15, (1.0, 0.9, 0.6), 0.45, 1.1, add=True)
    for rr, al in ((0.86, 0.5), (0.7, 0.35)):                                               # engraved rings
        craft.arc(c, cu, cv + 0.015, rr, rr * 0.395, 190, 350, 0.006, (1.0, 0.92, 0.65), al, 12)
        craft.arc(c, cu, cv + 0.012, rr, rr * 0.395, 10, 170, 0.006, (0.4, 0.25, 0.07), al, 12)
    # papad, roti, rice
    c.ellipse(0.50, 0.19, 0.25, 0.10, (0.78, 0.60, 0.30), lift=0)
    c.ellipse(0.50, 0.205, 0.245, 0.095, (0.96, 0.84, 0.55), lift=0.14)
    for _ in range(9):
        c.ellipse(0.50 + rng.uniform(-0.2, 0.2), 0.205 + rng.uniform(-0.06, 0.06), 0.012, 0.007, (0.55, 0.38, 0.14), lift=0, alpha=0.6)
    for k, (dx, dy) in enumerate(((-0.55, 0.14), (-0.50, 0.185))):
        c.ellipse(dx, dy, 0.26, 0.105, (0.72, 0.48, 0.22), lift=0)
        c.ellipse(dx, dy + 0.012, 0.25, 0.097, (0.96, 0.78, 0.45), lift=0.14)
        for _ in range(8):
            c.ellipse(dx + rng.uniform(-0.2, 0.2), dy + 0.012 + rng.uniform(-0.06, 0.06), 0.017, 0.008, (0.55, 0.30, 0.1), lift=0, alpha=0.7)
    soft_disc(c, -0.52, 0.22, 0.14, 0.03, WHITE, 0.4, 1.1, add=True)
    # katoris
    _katori(c, -0.60, 0.42, 0.17, "dal")
    _katori(c, -0.22, 0.52, 0.16, "paneer")
    _katori(c, 0.20, 0.52, 0.15, "curry")
    _katori(c, 0.60, 0.42, 0.15, "raita")
    _katori(c, 0.05, 0.18, 0.14, "sweet")
    # rice mound
    ru, rv = -0.12, 0.34
    soft_disc(c, ru + 0.03, rv - 0.03, 0.25, 0.07, (0.2, 0.15, 0.1), 0.35, 1.3)
    c.ellipse(ru, rv, 0.20, 0.10, (0.88, 0.86, 0.80), lift=0)
    c.ellipse(ru - 0.01, rv + 0.05, 0.175, 0.095, (0.99, 0.98, 0.94), lift=0.12)
    for _ in range(40):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        c.ellipse(ru + math.cos(a) * 0.16 * q, rv + 0.05 + math.sin(a) * 0.07 * q, 0.012, 0.0045, (0.92, 0.9, 0.84), lift=0, alpha=0.7, angle=rng.uniform(0, 180))
    soft_disc(c, ru - 0.06, rv + 0.09, 0.09, 0.03, WHITE, 0.5, 1.1, add=True)
    # salad: onion rings, lemon, chilli
    for k in range(3):
        c.ellipse(0.33 + k * 0.07, 0.10 + (k % 2) * 0.018, 0.035, 0.016, (0.88, 0.45, 0.62), lift=0.1)
        c.ellipse(0.33 + k * 0.07, 0.108 + (k % 2) * 0.018, 0.022, 0.009, (0.97, 0.88, 0.92), lift=0)
    c.ellipse(0.60, 0.115, 0.05, 0.032, (0.98, 0.88, 0.25), lift=0.12)
    c.ellipse(0.60, 0.117, 0.035, 0.02, (1.0, 0.95, 0.6), lift=0)
    c.line(0.25, 0.085, 0.42, 0.075, 0.016, (0.2, 0.5, 0.15))
    steam(c, -0.60, 0.50, 0.30, 0.04, 1, 0.14)
    steam(c, -0.12, 0.50, 0.34, 0.05, 1, 0.14)


@sprop("indian_tumbler", aspect=0.62, fill=1.0)
def indian_tumbler(c, color):
    ao(c, 0.0, 0.0, 0.5, 0.1)
    left, right = (0.95, 0.74, 0.36), (0.55, 0.36, 0.12)
    c.ellipse(0.0, 0.02, 0.19, 0.19 * TILT, scale(right, 0.8), lift=0)
    c.poly([(-0.27, 0.95), (0.27, 0.95), (0.19, 0.03), (-0.19, 0.03)], mix(left, right, 0.4), lift=0.06)
    for x0, al in ((0.0, 0.10), (0.07, 0.12), (0.13, 0.14), (0.19, 0.16)):
        c.poly([(x0, 0.95), (0.27, 0.95), (0.19, 0.03), (x0 * 0.7, 0.03)], (0.25, 0.14, 0.04), lift=0, alpha=al)
    c.poly([(-0.23, 0.9), (-0.16, 0.9), (-0.11, 0.1), (-0.15, 0.1)], (1.0, 0.95, 0.75), lift=0, alpha=0.55)
    for v in (0.18, 0.45, 0.72):
        c.line(-0.24 + (v - 0.45) * 0.08, v, 0.24 - (v - 0.45) * 0.08, v, 0.012, (0.4, 0.25, 0.07), 0.45)
    c.ellipse(0.0, 0.95, 0.27, 0.27 * TILT, (0.55, 0.38, 0.14), lift=0)
    c.ellipse(0.0, 0.955, 0.255, 0.255 * TILT, (0.30, 0.20, 0.08), lift=0)
    c.ellipse(0.0, 0.94, 0.22, 0.22 * TILT, (0.72, 0.85, 0.9), lift=0.1, alpha=0.85)
    gloss(c, -0.1, 0.96, 0.1, 0.025, 6, 0.4)


@sprop("indian_diya", aspect=1.0, fill=0.45)
def indian_diya(c, color):
    ao(c, 0.0, 0.0, 0.5, 0.1, 0.3)
    c.ellipse(0.0, 0.05, 0.22, 0.09, (0.46, 0.20, 0.08), lift=0)
    c.ellipse(0.0, 0.085, 0.22, 0.095, (0.76, 0.40, 0.18), lift=0.15)
    c.ellipse(0.0, 0.115, 0.17, 0.065, (0.28, 0.12, 0.04), lift=0)
    c.ellipse(0.0, 0.10, 0.12, 0.04, (0.95, 0.75, 0.3), lift=0, alpha=0.8)
    soft_disc(c, 0.0, 0.25, 0.6, 0.6, (1.0, 0.7, 0.25), 0.5, 2.2, add=True)
    c.poly([(-0.035, 0.12), (0.035, 0.12), (0.0, 0.31)], (1.0, 0.72, 0.2), lift=0.1)
    c.poly([(-0.018, 0.125), (0.018, 0.125), (0.0, 0.22)], (1.0, 0.97, 0.7), lift=0, alpha=0.9)


@sprop("indian_marigold", aspect=1.0, fill=0.4)
def indian_marigold(c, color):
    rng = c.rng
    for u, v, r in ((-0.30, 0.10, 0.17), (0.10, 0.12, 0.2), (0.38, 0.07, 0.15), (-0.05, 0.05, 0.13)):
        c.ellipse(u + 0.02, v - 0.02, r, r * 0.8, (0.62, 0.30, 0.05), lift=0, alpha=0.7)
        for k in range(18):
            a = k * 0.35 + rng.uniform(0, 0.2)
            rr = r * rng.uniform(0.45, 0.85)
            c.ellipse(u + math.cos(a) * rr, v + math.sin(a) * rr * 0.8, r * 0.34, r * 0.26, mix((0.98, 0.58, 0.10), (1.0, 0.75, 0.18), rng.random()), lift=0.15,
                      angle=math.degrees(a))
        c.ellipse(u, v, r * 0.4, r * 0.32, (0.90, 0.42, 0.05), lift=0.12)
    for k in range(5):
        leaf(c, 0.0, 0.05, 0.22, 20 + k * 36, (0.18, 0.48, 0.18), 0.4)


@niche("indian-thali", "Indian thali / dhaba", subjects=("indian_thali",),
       strong=("thali", "indian thali", "dhaba", "khana", "bhojan", "indian restaurant", "tiffin", "bhojnalay", "punjabi dhaba", "dal roti",
               "भोजन", "थाली", "ढाबा", "खाना", "भोजनालय"),
       weak=("dal", "roti", "paneer", "curry", "sabzi", "naan", "tandoor", "masala", "बिरयानी", "रोटी", "दाल"),
       accent="#e67e22", mood="warm", group="food")
def indian_thali_scene(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        S.rect(1.0, 0.50, 8.0, 0.22, scale(P.wall_bot, 0.78), lift=0.0)
        for k in range(-30, 40):                                                               # painted border band
            u = -3.0 + k * 0.10
            S.poly([(u, 0.40), (u + 0.05, 0.34), (u + 0.10, 0.40), (u + 0.05, 0.46)], mix(P.accent, P.wall_top, 0.2 if dark else 0.0))
        S.rect(1.0, 0.40, 8.0, 0.012, scale(P.accent_dark, 1.0), lift=0.0)
        for u in (0.25, 0.9, 1.55):                                                           # arched niches with brass vessels
            S.rect(u, 0.18, 0.34, 0.34, scale(P.wall_bot, 0.55), r=0.17, lift=0.0)
            S.glow(u, 0.22, 0.3, (1.0, 0.7, 0.3), 0.3)
            S.ellipse(u, 0.27, 0.09, 0.07, (0.95, 0.7, 0.28), lift=0.15)
            S.ellipse(u + 0.01, 0.22, 0.05, 0.04, (1.0, 0.85, 0.5), lift=0.15, alpha=0.8)
        S.pendant(1.22, -0.1, 0.12, (1.0, 0.7, 0.3), 0.1)
        S.pendant(0.62, -0.1, 0.08, (1.0, 0.7, 0.3), 0.09)
        S.bokeh(12, -0.2, 0.05, 2.2, 0.52, [(1.0, 0.8, 0.4), (1.0, 0.6, 0.25), (1.0, 0.9, 0.6)], 0.012, 0.04, 0.4)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.58, 5.0, 1.4, scale(P.surface, 0.9), plank=0.12, grain=0.4)
    S.rect(1.0, 0.58, 8.0, 0.009, scale(P.surface, 0.4), lift=0.0)
    cloth = mix(P.accent, P.paper, 0.15) if not dark else scale(P.accent, 0.6)
    S.rect(1.05, 0.92, 1.45, 0.50, cloth, lift=0.0)
    for k in range(0, 24):
        S.rect(0.35 + k * 0.0625, 0.92, 0.012 if k % 3 else 0.026, 0.50, mix(cloth, WHITE, 0.45) if k % 3 else scale(cloth, 0.7), lift=0.0, alpha=0.8)
    S.rect(1.05, 1.17, 1.45, 0.012, scale(cloth, 0.6), lift=0.0)
    S.soft(1.05, 0.82, 0.95, 0.25, (1.0, 0.8, 0.5), 0.30 if not dark else 0.45, 1.5, add=True)
    S.put("indian_tumbler", 0.52, 0.80, 0.22)
    S.put("indian_diya", 1.62, 0.77, 0.10)
    S.put("indian_thali", 1.07, 0.98, 0.40, subject=True)
    S.put("indian_marigold", 1.57, 0.97, 0.10)
    S.focus("detail", 1.0, 0.80)
    with S.near(16.0):
        S.soft(0.62, 1.03, 0.14, 0.06, (0.98, 0.55, 0.1), 0.8, 1.0, 10)
        S.soft(1.72, 1.0, 0.10, 0.10, (0.95, 0.6, 0.15), 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- fast food
@sprop("fastfood_burger", aspect=1.0, fill=0.85)
def fastfood_burger(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.16)
    # top bun dome (flat underside at v = 0.42)
    pts = []
    for k in range(17):
        t = math.pi * k / 16.0
        pts.append((0.49 * math.cos(t), 0.40 + 0.40 * math.sin(t) ** 0.85))
    c.poly(pts, (0.80, 0.46, 0.16), lift=0.22)
    soft_disc(c, 0.26, 0.55, 0.28, 0.22, (0.35, 0.15, 0.04), 0.35, 1.2)
    soft_disc(c, -0.14, 0.72, 0.28, 0.10, (1.0, 0.82, 0.5), 0.55, 1.2, 12, add=True)
    soft_disc(c, 0.0, 0.44, 0.5, 0.05, (0.3, 0.12, 0.03), 0.4, 1.4)
    for _ in range(26):                                                                # sesame seeds
        a = rng.uniform(0.25, math.pi - 0.25)
        r = rng.uniform(0.25, 0.9)
        x, y = 0.45 * r * math.cos(a), 0.42 + 0.34 * r * math.sin(a) ** 0.9
        c.ellipse(x, y, 0.017, 0.009, (0.99, 0.93, 0.74), lift=0.1, angle=rng.uniform(0, 180))
    for k in range(18):                                                                # lettuce frills
        x = -0.50 + k * 0.058
        c.ellipse(x, 0.395 + (0.012 if k % 2 else -0.004), 0.06, 0.035, (0.30, 0.62, 0.18) if k % 2 else (0.42, 0.74, 0.24), lift=0.18)
    c.rect(0.0, 0.365, 0.92, 0.04, (0.26, 0.55, 0.15), r=0.02, lift=0.1)
    for x in (-0.22, 0.2):                                                             # tomato
        c.ellipse(x, 0.335, 0.20, 0.034, (0.74, 0.12, 0.08), lift=0.15)
        c.ellipse(x - 0.03, 0.342, 0.15, 0.012, (0.95, 0.40, 0.30), lift=0, alpha=0.6)
    c.rect(0.0, 0.30, 0.90, 0.034, (0.99, 0.80, 0.14), r=0.012, lift=0.12)            # cheese
    c.poly([(-0.44, 0.30), (-0.34, 0.30), (-0.43, 0.215)], (0.99, 0.78, 0.12), lift=0.1)
    c.poly([(0.34, 0.30), (0.45, 0.30), (0.40, 0.2)], (0.99, 0.78, 0.12), lift=0.1)
    c.rect(0.0, 0.225, 0.98, 0.115, (0.34, 0.16, 0.08), r=0.05, lift=0.2)              # patty
    for _ in range(26):
        c.ellipse(rng.uniform(-0.45, 0.45), rng.uniform(0.18, 0.27), rng.uniform(0.012, 0.03), rng.uniform(0.006, 0.012),
                  (0.22, 0.09, 0.04) if rng.random() < 0.6 else (0.5, 0.28, 0.14), lift=0, alpha=0.7)
    c.rect(0.0, 0.16, 0.86, 0.05, (0.75, 0.15, 0.1), r=0.02, lift=0.1, alpha=0.8)      # sauce
    c.rect(0.0, 0.07, 0.94, 0.14, (0.80, 0.47, 0.17), r=0.07, lift=0.2)                # bottom bun
    soft_disc(c, 0.3, 0.05, 0.3, 0.06, (0.35, 0.15, 0.04), 0.3, 1.2)
    drip(c, 0.30, 0.16, 0.018, (0.78, 0.15, 0.1))


@sprop("fastfood_fries", aspect=0.9, fill=0.95)
def fastfood_fries(c, color):
    rng = c.rng
    red = color or (0.84, 0.16, 0.12)
    ao(c, 0.0, 0.0, 0.7, 0.14)
    for k in range(22):
        x = -0.28 + k * 0.026 + rng.uniform(-0.02, 0.02)
        tip = rng.uniform(0.62, 0.92)
        lean = (x * 0.9) + rng.uniform(-0.1, 0.1)
        base = 0.40
        w = 0.052
        shade = rng.uniform(0.9, 1.05)
        col = (0.98 * shade, 0.80 * shade, 0.28 * shade)
        c.line(x, base, x + lean * 0.35, tip, w, scale(col, 0.74))
        c.line(x - 0.006, base, x + lean * 0.35 - 0.006, tip, w * 0.66, col)
        c.line(x - 0.014, base + 0.02, x + lean * 0.35 - 0.012, tip - 0.015, w * 0.2, (1.0, 0.93, 0.6), 0.7)
        c.ellipse(x + lean * 0.35, tip, w * 0.4, w * 0.33, (0.86, 0.58, 0.16), lift=0.1)
    # carton
    c.poly([(-0.36, 0.46), (0.36, 0.46), (0.27, 0.02), (-0.27, 0.02)], red, lift=0.12)
    c.poly([(0.05, 0.46), (0.36, 0.46), (0.27, 0.02), (0.03, 0.02)], (0.3, 0.02, 0.02), lift=0, alpha=0.30)
    c.poly([(-0.33, 0.44), (-0.26, 0.44), (-0.2, 0.05), (-0.25, 0.05)], WHITE, lift=0, alpha=0.30)
    c.poly([(-0.34, 0.30), (0.34, 0.30), (0.31, 0.20), (-0.31, 0.20)], (1.0, 0.86, 0.25), lift=0.1, alpha=0.95)
    c.ellipse(0.0, 0.25, 0.05, 0.035, red, lift=0.1)
    c.ellipse(0.0, 0.46, 0.36, 0.05, scale(red, 0.75), lift=0, alpha=0.9)
    c.ellipse(0.0, 0.465, 0.35, 0.04, scale(red, 1.12), lift=0.1)
    soft_disc(c, 0.0, 0.40, 0.4, 0.07, (0.3, 0.02, 0.02), 0.4, 1.3)
    gloss(c, -0.2, 0.36, 0.015, 0.1, 5, 0.3)


@sprop("fastfood_cola", aspect=0.5, fill=1.0)
def fastfood_cola(c, color):
    rng = c.rng
    red = color or (0.84, 0.16, 0.12)
    ao(c, 0.0, 0.0, 0.5, 0.1)
    c.ellipse(0.0, 0.03, 0.17, 0.17 * TILT, scale(red, 0.5), lift=0)
    c.poly([(-0.24, 0.80), (0.24, 0.80), (0.17, 0.03), (-0.17, 0.03)], (0.97, 0.96, 0.94), lift=0.05)
    c.poly([(-0.22, 0.60), (0.22, 0.60), (0.195, 0.28), (-0.195, 0.28)], red, lift=0.1)
    for x0, al in ((0.02, 0.12), (0.08, 0.14), (0.14, 0.16), (0.19, 0.18)):
        c.poly([(x0, 0.80), (0.24, 0.80), (0.17, 0.03), (x0 * 0.75, 0.03)], (0.15, 0.08, 0.05), lift=0, alpha=al)
    craft.arc(c, 0.0, 0.46, 0.17, 0.08, 200, 340, 0.04, (1.0, 0.9, 0.9), 0.7, 8)
    c.ellipse(0.0, 0.46, 0.04, 0.04, (1.0, 0.86, 0.3), lift=0.1)
    c.poly([(-0.20, 0.76), (-0.15, 0.76), (-0.10, 0.08), (-0.13, 0.08)], WHITE, lift=0, alpha=0.5)
    for _ in range(12):                                                                # condensation
        x, y = rng.uniform(-0.17, 0.17), rng.uniform(0.1, 0.55)
        c.ellipse(x, y, 0.007, 0.011, (1.0, 1.0, 1.0), alpha=0.55, lift=0)
    # lid and straw
    c.ellipse(0.0, 0.80, 0.265, 0.265 * TILT, (0.30, 0.08, 0.06), lift=0)
    c.ellipse(0.0, 0.83, 0.25, 0.25 * 0.38, scale(red, 0.85), lift=0.2)
    c.ellipse(0.0, 0.85, 0.20, 0.07, scale(red, 1.0), lift=0.2)
    soft_disc(c, -0.1, 0.86, 0.12, 0.025, WHITE, 0.5, 1.1, add=True)
    for k in range(8):
        t0, t1 = k / 8.0, (k + 1) / 8.0
        c.line(0.04 + 0.18 * t0, 0.86 + 0.40 * t0, 0.04 + 0.18 * t1, 0.86 + 0.40 * t1, 0.032, WHITE if k % 2 else red)


@sprop("fastfood_tray", aspect=5.4, fill=0.2)
def fastfood_tray(c, color):
    rng = c.rng
    red = color or (0.84, 0.16, 0.12)
    ao(c, 0.0, 0.0, 1.0, 0.2)
    c.poly([(-0.50, 0.06), (0.50, 0.06), (0.49, 0.0), (-0.49, 0.0)], scale(red, 0.5), lift=0)
    c.poly([(-0.47, 0.20), (0.47, 0.20), (0.50, 0.06), (-0.50, 0.06)], red, lift=0.1)
    c.poly([(-0.43, 0.185), (0.43, 0.185), (0.46, 0.075), (-0.46, 0.075)], (0.97, 0.94, 0.86), lift=0.05)
    for k in range(-6, 7):                                                             # paper liner pattern
        c.line(k * 0.07, 0.185, k * 0.074, 0.08, 0.006, mix(red, WHITE, 0.4), 0.45)
    for _ in range(10):
        c.ellipse(rng.uniform(-0.4, 0.4), rng.uniform(0.09, 0.17), rng.uniform(0.015, 0.03), 0.01, (0.85, 0.7, 0.4), lift=0, alpha=0.3)
    soft_disc(c, -0.3, 0.19, 0.4, 0.03, WHITE, 0.4, 1.2, add=True)


@niche("fast-food", "Fast food / burger joint", subjects=("fastfood_burger",),
       strong=("burger", "fast food", "burger joint", "fries", "diner", "cheeseburger", "quick service restaurant", "burger point",
               "बर्गर", "फास्ट फूड", "फास्टफूड", "बर्गर शॉप", "फ्राइज़"),
       weak=("cola", "takeaway", "drive thru", "nuggets", "sandwich", "hot dog", "combo meal", "सैंडविच"),
       accent="#e74c3c", mood="light", group="food")
def fast_food(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        for k in range(-18, 30):                                                            # stripes
            S.rect(-3.0 + k * 0.26, 0.20, 0.13, 0.80, mix(P.wall_top, P.accent, 0.12 if not dark else 0.25), lift=0.0, alpha=0.6)
        S.tiles(-3.0, 0.43, 5.0, 0.58, scale(P.paper, 0.4 if dark else 1.0), scale(P.ink, 1.5 if not dark else 3.0), 0.075)
        S.rect(1.0, 0.43, 8.0, 0.012, (0.8, 0.82, 0.85), lift=0.0)                          # chrome rail
        S.rect(0.62, 0.20, 0.66, 0.20, scale(P.ink, 1.2), r=0.03, lift=0.0)                  # neon sign
        S.glow(0.62, 0.20, 0.55, P.accent, 0.55)
        S.text("DINER", 0.62, 0.20, 0.10, mix(P.accent_light, WHITE, 0.35), 0.16)
        S.glow(0.62, 0.20, 0.25, P.accent_light, 0.30)
        S.rect(1.55, 0.16, 0.36, 0.22, scale(P.ink, 1.4), r=0.01, lift=0.0)                  # menu board
        for k in range(4):
            S.rect(1.55, 0.09 + k * 0.045, 0.28, 0.014, mix(P.accent_light, WHITE, 0.4) if k % 2 else (1.0, 0.85, 0.35), lift=0.0, alpha=0.9)
        S.pendant(1.05, -0.1, 0.10, (1.0, 0.85, 0.6), 0.09)
        S.pendant(1.95, -0.1, 0.12, (1.0, 0.85, 0.6), 0.09)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.40, [(1.0, 0.4, 0.3), (1.0, 0.85, 0.4), (1.0, 1.0, 0.9)], 0.015, 0.04, 0.35)
        S.floor(0.58, P.floor_top, P.floor_bot)
    top = scale(mix(P.paper, P.accent_light, 0.18), 0.45 if dark else 1.0)
    S.rect(1.0, 1.0, 8.0, 0.84, top, lift=0.0)
    S.rect(1.0, 0.66, 8.0, 0.12, scale(top, 0.94), lift=0.0)
    S.rect(1.0, 0.585, 8.0, 0.014, (0.78, 0.80, 0.84), lift=0.0)                           # chrome edge
    S.soft(1.1, 0.80, 1.1, 0.24, (1.0, 0.95, 0.85), 0.28 if not dark else 0.4, 1.5, add=True)
    S.put("fastfood_tray", 1.07, 1.0, 0.20, color=P.accent, framed=True, shadow_alpha=0.35)
    S.put("fastfood_cola", 1.58, 0.90, 0.36, color=P.accent)
    S.put("fastfood_fries", 0.66, 0.90, 0.30, color=P.accent)
    S.put("fastfood_burger", 1.07, 0.94, 0.34, subject=True, shadow_alpha=0.18)
    S.focus("detail", 1.07, 0.77)
    with S.near(18.0):
        S.soft(0.55, 1.02, 0.12, 0.10, (0.99, 0.82, 0.2), 0.7, 1.0)
        S.soft(1.72, 1.0, 0.10, 0.08, P.accent, 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- ice cream
SCOOPS = {"pink": (0.98, 0.62, 0.75), "vanilla": (0.99, 0.93, 0.74), "choc": (0.45, 0.24, 0.13), "mint": (0.62, 0.92, 0.78),
          "mango": (1.0, 0.76, 0.25)}


def _scoop(c, u, v, r, col, rng):
    """A scoop of ice cream with a scalloped skirt, shading, speckles and a gloss."""
    for k in range(9):                                                                 # skirt
        a = math.pi + math.pi * k / 8.0 * 1.0
        c.ellipse(u + math.cos(a) * r * 0.95, v + r * 0.10 + math.sin(a) * r * 0.05, r * 0.19, r * 0.15, scale(col, 0.86), lift=0.1)
    c.ellipse(u, v + r * 0.1, r * 0.98, r * 0.12, scale(col, 0.8), lift=0)
    c.ellipse(u, v + r * 0.62, r, r * 0.86, scale(col, 0.74), lift=0)
    c.ellipse(u - r * 0.03, v + r * 0.66, r * 0.95, r * 0.82, col, lift=0.18)
    soft_disc(c, u + r * 0.3, v + r * 0.35, r * 0.62, r * 0.5, scale(col, 0.4), 0.38, 1.3)
    for _ in range(12):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.7
        c.ellipse(u + math.cos(a) * r * q, v + r * 0.66 + math.sin(a) * r * q * 0.8, r * 0.05, r * 0.03, scale(col, rng.uniform(0.85, 1.12)), lift=0, alpha=0.7)
    soft_disc(c, u - r * 0.35, v + r * 0.95, r * 0.34, r * 0.2, WHITE, 0.55, 1.1, 20, add=True)


@sprop("icecream_sundae", aspect=0.72, fill=1.1)
def icecream_sundae(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.14)
    c.ellipse(0.0, 0.025, 0.24, 0.24 * TILT, (0.82, 0.88, 0.92), alpha=0.8, lift=0.1)
    c.ellipse(0.0, 0.035, 0.18, 0.18 * TILT, (0.95, 0.98, 1.0), alpha=0.7, lift=0)
    c.rect(0.0, 0.14, 0.035, 0.2, (0.88, 0.93, 0.96), lift=0, alpha=0.85)
    # glass body and layered contents (clipped to the taper)
    for v0, v1, col in ((0.20, 0.36, (0.36, 0.17, 0.09)), (0.36, 0.50, (0.98, 0.58, 0.72)), (0.50, 0.64, (0.99, 0.94, 0.78))):
        w0 = 0.17 + (v0 - 0.20) * 0.23
        w1 = 0.17 + (v1 - 0.20) * 0.23
        c.poly([(-w0, v0), (w0, v0), (w1, v1), (-w1, v1)], col, lift=0.1)
        c.ellipse(0.0, v1, w1, w1 * 0.3, scale(col, 1.06), lift=0.1)
    c.ellipse(0.0, 0.20, 0.17, 0.17 * 0.4, (0.34, 0.16, 0.08), lift=0)
    c.poly([(0.05, 0.64), (0.28, 0.64), (0.17, 0.20), (0.03, 0.20)], (0.15, 0.1, 0.1), lift=0, alpha=0.18)
    c.poly([(-0.27, 0.64), (-0.22, 0.64), (-0.14, 0.22), (-0.17, 0.22)], WHITE, lift=0, alpha=0.5)
    c.poly([(-0.28, 0.66), (0.28, 0.66), (0.18, 0.20), (-0.18, 0.20)], (0.85, 0.93, 0.97), lift=0, alpha=0.14)
    craft.arc(c, 0.0, 0.66, 0.28, 0.28 * 0.34, 180, 360, 0.01, WHITE, 0.55, 8)
    for _ in range(9):                                                                 # trapped bubbles
        c.ellipse(rng.uniform(-0.14, 0.14), rng.uniform(0.38, 0.6), 0.008, 0.008, WHITE, alpha=0.35, lift=0)
    c.ellipse(0.0, 0.66, 0.285, 0.285 * 0.34, (0.88, 0.95, 0.98), lift=0, alpha=0.6)
    c.ellipse(0.0, 0.665, 0.25, 0.25 * 0.3, (0.99, 0.94, 0.80), lift=0.1)
    # wafer
    c.poly([(0.10, 0.70), (0.17, 0.74), (0.40, 1.12), (0.32, 1.13)], (0.90, 0.70, 0.38), lift=0.15)
    for k in range(5):
        t = 0.2 + k * 0.17
        c.line(0.12 + 0.2 * t, 0.72 + 0.4 * t, 0.2 + 0.2 * t, 0.74 + 0.4 * t, 0.012, (0.62, 0.40, 0.16), 0.6)
    # scoops, cream, cherry
    _scoop(c, -0.11, 0.66, 0.17, SCOOPS["pink"], rng)
    _scoop(c, 0.11, 0.68, 0.16, SCOOPS["choc"], rng)
    _scoop(c, 0.0, 0.80, 0.17, SCOOPS["vanilla"], rng)
    for k in range(4):                                                                 # whipped cream swirl
        w = 0.14 - k * 0.025
        c.ellipse(0.0, 0.96 + k * 0.055, w, 0.045, scale((1.0, 0.99, 0.97), 0.9), lift=0)
        c.ellipse(-0.005, 0.965 + k * 0.055, w * 0.95, 0.04, (1.0, 0.99, 0.97), lift=0.12)
    c.poly([(-0.02, 1.15), (0.02, 1.15), (0.0, 1.21)], (1.0, 0.99, 0.97), lift=0.1)
    c.line(0.0, 1.14, 0.04, 1.27, 0.008, (0.3, 0.45, 0.15))
    _ball(c, 0.0, 1.14, 0.065, (0.72, 0.06, 0.1), 0.95, hl=0.7)
    craft.arc(c, 0.0, 0.92, 0.17, 0.06, 190, 330, 0.014, (0.30, 0.14, 0.07), 0.85, 8)    # chocolate drizzle
    for _ in range(22):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        x, y = math.cos(a) * 0.24 * q, 0.84 + math.sin(a) * 0.26 * q
        c.line(x, y, x + rng.uniform(-0.01, 0.01), y + rng.uniform(0.012, 0.024), 0.008,
               [(1.0, 0.4, 0.5), (0.4, 0.8, 1.0), (1.0, 0.9, 0.3), (0.6, 0.9, 0.5)][rng.randrange(4)])


@sprop("icecream_cone", aspect=0.55, fill=1.0)
def icecream_cone(c, color):
    rng = c.rng
    top = color or SCOOPS["mint"]
    ao(c, 0.0, 0.0, 0.3, 0.06)
    c.poly([(-0.19, 0.60), (0.19, 0.60), (0.0, 0.02)], (0.86, 0.62, 0.30), lift=0.12)
    c.poly([(0.02, 0.60), (0.19, 0.60), (0.0, 0.02)], (0.45, 0.26, 0.08), lift=0, alpha=0.3)
    for k in range(6):                                                                 # waffle grid
        y = 0.12 + k * 0.08
        hw = 0.19 * (y - 0.02) / 0.58
        c.line(-hw, y, hw * 0.9, y - 0.09, 0.008, (0.6, 0.38, 0.14), 0.7)
        c.line(hw, y, -hw * 0.9, y - 0.09, 0.008, (0.6, 0.38, 0.14), 0.7)
    c.line(-0.14, 0.55, -0.01, 0.1, 0.012, (1.0, 0.88, 0.6), 0.5)
    _scoop(c, 0.0, 0.52, 0.22, scale(SCOOPS["vanilla"], 1.0) if color is not None else SCOOPS["pink"], rng)
    _scoop(c, 0.0, 0.72, 0.20, top, rng)
    for _ in range(14):
        a, q = rng.uniform(0.3, 2.8), rng.uniform(0.3, 0.95)
        x, y = math.cos(a) * 0.17 * q, 0.9 + math.sin(a) * 0.12 * q
        c.line(x, y, x + 0.012, y + 0.01, 0.009, [(1.0, 0.4, 0.5), (0.4, 0.8, 1.0), (1.0, 0.9, 0.3), (0.9, 0.9, 0.95)][rng.randrange(4)])
    _ball(c, 0.0, 0.98, 0.05, (0.72, 0.06, 0.1), 0.95, hl=0.7)


@niche("ice-cream", "Ice cream parlour", subjects=("icecream_sundae",),
       strong=("ice cream", "icecream", "ice cream parlour", "ice cream shop", "gelato", "kulfi", "sundae", "frozen dessert", "ice cream parlor",
               "आइसक्रीम", "आइस क्रीम", "कुल्फी", "जेलेटो", "आइसक्रीम पार्लर"),
       weak=("sweets", "dessert", "scoop", "cone", "frozen yogurt", "milkshake", "falooda", "कोन", "डेज़र्ट"),
       accent="#ff6fa5", mood="light", group="food")
def ice_cream(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for k in range(-20, 32):
            S.rect(-3.0 + k * 0.2, 0.28, 0.1, 0.9, mix(P.wall_top, P.accent, 0.20 if not dark else 0.35), lift=0.0, alpha=0.7)
        for k in range(-16, 24):                                                            # scalloped awning
            u = -3.0 + k * 0.25
            S.rect(u + 0.125, 0.03, 0.25, 0.12, mix(P.accent, WHITE, 0.15) if k % 2 else mix(P.paper, P.accent_light, 0.1), lift=0.0)
            S.circle(u + 0.125, 0.09, 0.125, mix(P.accent, WHITE, 0.15) if k % 2 else mix(P.paper, P.accent_light, 0.1), lift=0.1)
        S.rect(0.38, 0.30, 0.46, 0.36, scale(P.wall_bot, 0.8), r=0.02, lift=0.0)                # menu / shelf
        for k in range(3):
            S.rect(0.38, 0.19 + k * 0.1, 0.40, 0.014, scale(P.surface, 1.0), lift=0.0)
            for j in range(4):
                S.circle(0.24 + j * 0.095, 0.17 + k * 0.1, 0.035, [SCOOPS["pink"], SCOOPS["mint"], SCOOPS["vanilla"], SCOOPS["mango"]][(j + k) % 4], lift=0.1)
        S.pendant(1.12, -0.1, 0.20, (1.0, 0.85, 0.7), 0.10)
        S.pendant(1.62, -0.1, 0.16, (1.0, 0.85, 0.7), 0.09)
        S.bokeh(10, 0.0, 0.2, 2.0, 0.55, [mix(P.accent_light, WHITE, 0.4), (0.7, 0.95, 0.85), (1.0, 0.95, 0.7)], 0.015, 0.045, 0.4)
        S.floor(0.60, P.floor_top, P.floor_bot)
    top = scale(mix(P.paper, P.accent_light, 0.30), 0.5 if dark else 1.0)
    S.rect(1.0, 1.0, 8.0, 0.80, top, lift=0.0)
    S.rect(1.0, 0.66, 8.0, 0.12, scale(top, 0.95), lift=0.0)
    S.rect(1.0, 0.605, 8.0, 0.012, mix(P.accent, WHITE, 0.2), lift=0.0)
    S.soft(1.1, 0.78, 1.0, 0.22, (1.0, 0.97, 0.92), 0.30 if not dark else 0.4, 1.5, add=True)
    S.put("icecream_cone", 0.66, 0.90, 0.40, color=SCOOPS["mint"])
    S.put("icecream_cone", 1.50, 0.91, 0.36, color=SCOOPS["choc"])
    S.put("icecream_sundae", 1.07, 0.96, 0.54, subject=True)
    S.focus("detail", 1.07, 0.60)
    with S.near(18.0):
        S.soft(0.52, 1.02, 0.12, 0.08, SCOOPS["pink"], 0.8, 1.0)
        S.soft(1.7, 1.0, 0.10, 0.08, SCOOPS["mint"], 0.6, 1.0)


# ---------------------------------------------------------------------------------------------- juice bar
def _orange_half(c, u, v, r, col=(0.98, 0.58, 0.10), pith=(1.0, 0.92, 0.7)):
    """A cut citrus half seen from above: rind, pith, radial segments, juicy sheen."""
    c.ellipse(u, v - 0.012, r, r * 0.8, scale(col, 0.6), lift=0)
    c.ellipse(u, v, r * 0.97, r * 0.77, pith, lift=0.1)
    c.ellipse(u, v, r * 0.88, r * 0.69, col, lift=0.16)
    for k in range(9):
        a = k * math.pi * 2 / 9
        c.line(u, v, u + math.cos(a) * r * 0.86, v + math.sin(a) * r * 0.68, r * 0.045, mix(col, pith, 0.8), 0.9)
    c.ellipse(u, v, r * 0.09, r * 0.07, pith, lift=0)
    soft_disc(c, u - r * 0.3, v + r * 0.25, r * 0.4, r * 0.18, WHITE, 0.5, 1.1, 10, add=True)


@sprop("juice_glass", aspect=0.5, fill=1.15)
def juice_glass(c, color):
    rng = c.rng
    col = color or (0.45, 0.80, 0.22)
    light = mix(col, WHITE, 0.45)
    ao(c, 0.0, 0.0, 0.55, 0.11)
    c.ellipse(0.0, 0.035, 0.19, 0.19 * TILT, (0.78, 0.84, 0.86), lift=0, alpha=0.9)
    c.poly([(-0.25, 0.80), (0.25, 0.80), (0.19, 0.04), (-0.19, 0.04)], mix(col, WHITE, 0.15), lift=0.04)     # liquid body
    c.poly([(-0.25, 0.80), (0.25, 0.80), (0.22, 0.45), (-0.22, 0.45)], light, lift=0.1)
    c.ellipse(0.0, 0.45, 0.22, 0.07, mix(col, light, 0.5), lift=0.1)
    for x0, al in ((0.02, 0.10), (0.08, 0.12), (0.14, 0.14), (0.20, 0.16)):
        c.poly([(x0, 0.80), (0.25, 0.80), (0.19, 0.04), (x0 * 0.75, 0.04)], scale(col, 0.4), lift=0, alpha=al)
    c.poly([(-0.215, 0.76), (-0.15, 0.76), (-0.10, 0.1), (-0.145, 0.1)], WHITE, lift=0, alpha=0.5)
    c.ellipse(0.0, 0.04, 0.19, 0.19 * 0.4, scale(col, 0.7), lift=0)
    for _ in range(14):                                                                # seeds / bubbles
        c.ellipse(rng.uniform(-0.18, 0.18), rng.uniform(0.1, 0.72), rng.uniform(0.006, 0.014), rng.uniform(0.006, 0.012),
                  mix(col, WHITE, 0.6) if rng.random() < 0.6 else scale(col, 0.55), alpha=0.5, lift=0)
    c.ellipse(0.0, 0.80, 0.25, 0.25 * 0.36, (0.86, 0.93, 0.95), lift=0, alpha=0.85)        # rim
    c.ellipse(0.0, 0.795, 0.225, 0.225 * 0.33, light, lift=0.1)
    gloss(c, -0.08, 0.80, 0.09, 0.02, 4, 0.5)
    for k in range(9):                                                                 # striped straw
        t0, t1 = k / 9.0, (k + 1) / 9.0
        c.line(0.05 + 0.17 * t0, 0.70 + 0.44 * t0, 0.05 + 0.17 * t1, 0.70 + 0.44 * t1, 0.036, (1.0, 1.0, 1.0) if k % 2 else scale(col, 0.7))
    for _ in range(10):
        c.ellipse(rng.uniform(-0.2, 0.2), rng.uniform(0.15, 0.7), 0.006, 0.01, WHITE, alpha=0.5, lift=0)


@sprop("juice_blender", aspect=0.62, fill=1.15)
def juice_blender(c, color):
    rng = c.rng
    col = color or (0.45, 0.80, 0.22)
    ao(c, 0.0, 0.0, 0.6, 0.12)
    craft.hshade_box(c, 0.0, 0.14, 0.52, 0.26, (0.60, 0.64, 0.68), (0.24, 0.27, 0.30), r=0.05)       # base
    c.rect(0.0, 0.27, 0.46, 0.03, (0.80, 0.83, 0.86), r=0.012, lift=0.1)
    for k, cc in enumerate(((0.9, 0.3, 0.25), (0.95, 0.8, 0.2), (0.4, 0.75, 0.3))):
        c.circle(-0.13 + k * 0.13, 0.15, 0.032, cc, lift=0.2)
    c.rect(0.0, 0.07, 0.36, 0.03, (0.08, 0.08, 0.1), lift=0, alpha=0.4)
    # jar
    c.poly([(-0.24, 1.05), (0.24, 1.05), (0.15, 0.30), (-0.15, 0.30)], (0.86, 0.93, 0.96), lift=0, alpha=0.5)
    c.poly([(-0.235, 0.78), (0.235, 0.78), (0.15, 0.31), (-0.15, 0.31)], col, lift=0.12)
    c.ellipse(0.0, 0.78, 0.235, 0.075, mix(col, WHITE, 0.45), lift=0.1)
    for _ in range(10):
        c.ellipse(rng.uniform(-0.18, 0.18), rng.uniform(0.36, 0.76), rng.uniform(0.01, 0.02), rng.uniform(0.01, 0.02), mix(col, WHITE, 0.5), alpha=0.5, lift=0)
    c.poly([(0.05, 1.05), (0.24, 1.05), (0.15, 0.30), (0.04, 0.30)], scale(col, 0.4), lift=0, alpha=0.28)
    c.poly([(-0.20, 1.0), (-0.14, 1.0), (-0.09, 0.4), (-0.12, 0.4)], WHITE, lift=0, alpha=0.5)
    c.rect(0.28, 0.72, 0.04, 0.5, (0.12, 0.13, 0.15), r=0.02, lift=0.1)                    # handle
    c.rect(0.0, 1.08, 0.52, 0.055, (0.10, 0.11, 0.13), r=0.02, lift=0.2)                    # lid
    c.rect(0.0, 1.13, 0.20, 0.05, (0.15, 0.16, 0.18), r=0.02, lift=0.2)
    c.rect(0.0, 0.30, 0.34, 0.035, (0.15, 0.16, 0.18), r=0.015, lift=0.2)


@sprop("juice_fruits", aspect=1.7, fill=0.5)
def juice_fruits(c, color):
    rng = c.rng
    wood = (0.78, 0.58, 0.34)
    ao(c, 0.0, 0.0, 1.4, 0.3)
    c.ellipse(0.0, 0.035, 0.84, 0.84 * 0.3, scale(wood, 0.65), lift=0)                    # board
    disc(c, 0.0, 0.06, 0.84, wood, 0.3, 0.1)
    for _ in range(7):
        a = rng.uniform(0.3, 0.7)
        craft.arc(c, rng.uniform(-0.1, 0.1), 0.06, a, a * 0.3, rng.uniform(0, 200), rng.uniform(220, 340), 0.004, scale(wood, 0.82), 0.4)
    _orange_half(c, -0.42, 0.13, 0.20)
    _orange_half(c, -0.08, 0.19, 0.17, (0.98, 0.42, 0.20), (1.0, 0.88, 0.75))
    for i, (x, y) in enumerate(((0.24, 0.13), (0.42, 0.20))):                             # kiwi slices
        c.ellipse(x, y - 0.01, 0.12, 0.085, (0.42, 0.30, 0.12), lift=0)
        c.ellipse(x, y, 0.115, 0.08, (0.50, 0.80, 0.22), lift=0.15)
        c.ellipse(x, y, 0.04, 0.028, (0.96, 0.98, 0.8), lift=0)
        for k in range(14):
            a = k * 0.45
            c.ellipse(x + math.cos(a) * 0.065, y + math.sin(a) * 0.045, 0.006, 0.004, (0.1, 0.12, 0.05), lift=0)
    for u, v in ((0.62, 0.12), (0.52, 0.06), (0.70, 0.19)):                              # strawberries
        c.ellipse(u, v, 0.075, 0.06, (0.65, 0.05, 0.08), lift=0)
        c.ellipse(u - 0.005, v + 0.008, 0.07, 0.055, (0.88, 0.12, 0.16), lift=0.16)
        for _ in range(9):
            c.ellipse(u + rng.uniform(-0.05, 0.05), v + rng.uniform(-0.035, 0.04), 0.004, 0.005, (1.0, 0.9, 0.5), lift=0)
        for k in range(4):
            leaf(c, u, v + 0.045, 0.045, 60 + k * 40, (0.2, 0.55, 0.2), 0.5)
        gloss(c, u - 0.025, v + 0.02, 0.02, 0.012, 20, 0.6)


@niche("juice-bar", "Juice bar / smoothies", subjects=("juice_glass",),
       strong=("juice bar", "smoothie", "juice shop", "fresh juice", "smoothie bar", "cold pressed juice", "juice centre", "juice corner",
               "ganne ka ras", "फ्रूट जूस", "जूस सेंटर", "जूस बार", "स्मूदी", "ताज़ा जूस"),
       weak=("juice", "fruit", "shake", "detox", "protein shake", "mocktail", "lassi", "जूस", "फल"),
       accent="#2ecc71", mood="light", group="food")
def juice_bar(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        S.tiles(-3.0, -0.2, 5.0, 0.58, P.wall_top, scale(P.wall_top, 0.965 if not dark else 1.18), 0.11)
        S.rect(1.0, 0.2, 8.0, 0.012, scale(P.wall_bot, 0.85), lift=0.0)
        for u, v, r, a in ((0.3, 0.3, 0.30, 30), (0.52, 0.12, 0.22, -50), (1.95, 0.30, 0.28, -20), (1.75, 0.10, 0.2, 70)):       # tropical leaves
            S.ellipse(u, v, r, r * 0.45, mix(P.accent, (0.2, 0.5, 0.2), 0.5), angle=a, lift=0.1)
        S.rect(0.95, 0.30, 0.8, 0.22, mix(P.accent_dark, P.ink, 0.4) if not dark else scale(P.accent_dark, 0.6), r=0.02, lift=0.0)    # sign
        S.glow(0.95, 0.30, 0.6, P.accent, 0.28)
        S.text("FRESH JUICE", 0.95, 0.30, 0.07, mix(P.accent_light, WHITE, 0.5), 0.14)
        S.rect(1.55, 0.42, 0.8, 0.014, scale(P.surface, 1.0), lift=0.05)                    # shelf with fruit
        for k in range(8):
            S.circle(1.25 + k * 0.09, 0.40, 0.034, [(0.98, 0.6, 0.12), (0.8, 0.15, 0.15), (0.6, 0.8, 0.25)][k % 3], lift=0.1)
        S.pendant(1.35, -0.1, 0.12, (1.0, 0.92, 0.7), 0.09)
        S.pendant(0.55, -0.1, 0.10, (1.0, 0.92, 0.7), 0.09)
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [(1.0, 0.95, 0.7), (0.8, 1.0, 0.8)], 0.015, 0.04, 0.3)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.58, 5.0, 1.4, scale(P.surface, 1.15 if not dark else 0.9), plank=0.16, grain=0.35)
    S.rect(1.0, 0.585, 8.0, 0.012, scale(P.surface, 0.55), lift=0.0)
    S.soft(1.1, 0.80, 1.0, 0.24, (1.0, 0.98, 0.9), 0.28 if not dark else 0.42, 1.5, add=True)
    S.put("juice_blender", 0.60, 0.72, 0.38)
    S.put("juice_fruits", 1.28, 0.97, 0.24)
    S.put("juice_glass", 1.42, 0.80, 0.40, color=(0.96, 0.52, 0.18))
    S.put("juice_glass", 0.98, 0.88, 0.52, subject=True, color=mix(P.accent, (0.5, 0.85, 0.25), 0.4))
    S.focus("detail", 1.0, 0.62)
    with S.near(18.0):
        S.soft(0.52, 1.02, 0.12, 0.08, (0.98, 0.6, 0.12), 0.8, 1.0)
        S.soft(1.72, 0.98, 0.10, 0.08, (0.4, 0.75, 0.3), 0.6, 1.0)


# ---------------------------------------------------------------------------------------------- sweet shop
def _barfi(c, u, v, w, col, leaf_on=True):
    """A diamond-cut mithai piece with thickness and optional silver leaf."""
    h = w * 0.55
    c.poly([(u - w, v), (u, v - h * 0.5), (u + w, v), (u + w, v - h * 0.32), (u, v - h * 0.82), (u - w, v - h * 0.32)], scale(col, 0.62), lift=0)
    c.poly([(u - w, v), (u, v + h * 0.5), (u + w, v), (u, v - h * 0.5)], col, lift=0.18)
    c.poly([(u - w, v - h * 0.32), (u - w, v), (u, v - h * 0.5), (u, v - h * 0.82)], scale(col, 0.78), lift=0, alpha=0.0)
    if leaf_on:
        c.poly([(u - w * 0.7, v), (u - w * 0.1, v + h * 0.28), (u + w * 0.45, v + h * 0.02), (u - w * 0.1, v - h * 0.22)], (0.9, 0.92, 0.96), lift=0.2, alpha=0.85)
        soft_disc(c, u - w * 0.3, v + h * 0.1, w * 0.3, h * 0.12, WHITE, 0.7, 1.1, add=True)


def _laddu(c, u, v, r, rng, col=(0.97, 0.66, 0.10)):
    _ball(c, u, v, r, col, 0.95, hl=0.35)
    for _ in range(18):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.85
        c.ellipse(u + math.cos(a) * r * q, v + r * 0.05 + math.sin(a) * r * q * 0.85, r * 0.075, r * 0.07, scale(col, rng.uniform(0.82, 1.15)), lift=0.15, alpha=0.9)
    c.ellipse(u + r * 0.12, v + r * 0.5, r * 0.12, r * 0.045, (0.55, 0.72, 0.30), lift=0, angle=20)


def _jalebi(c, u, v, r):
    for k in range(3):
        rr = r * (1.0 - k * 0.33)
        craft.arc(c, u, v - 0.005, rr, rr * 0.7, 0, 340, r * 0.13, (0.78, 0.32, 0.03), 1.0, 12)
        craft.arc(c, u, v, rr, rr * 0.7, 0, 340, r * 0.1, (1.0, 0.58, 0.06), 1.0, 12, 0)
        craft.arc(c, u - r * 0.02, v + r * 0.03, rr, rr * 0.7, 80, 210, r * 0.035, (1.0, 0.88, 0.45), 0.8, 8)
    c.ellipse(u, v, r * 0.13, r * 0.09, (1.0, 0.6, 0.1), lift=0.1)


@sprop("sweet_tray", aspect=2.6, fill=0.7)
def sweet_tray(c, color):
    rng = c.rng
    cu, cv = 0.0, 0.31
    ao(c, 0.0, 0.0, 1.9, 0.5)
    c.ellipse(cu, cv - 0.05, 0.93, 0.375, (0.42, 0.28, 0.10), lift=0)
    c.ellipse(cu, cv, 0.93, 0.375, (0.50, 0.33, 0.10), lift=0.14)
    c.ellipse(cu, cv + 0.01, 0.90, 0.36, (0.95, 0.72, 0.30), lift=0.2)
    craft.arc(c, cu, cv + 0.012, 0.865, 0.345, 110, 200, 0.03, (1.0, 0.95, 0.72), 0.75, 10)
    c.ellipse(cu, cv + 0.02, 0.80, 0.318, (0.74, 0.54, 0.22), lift=0.14)
    c.ellipse(cu, cv + 0.015, 0.76, 0.30, (0.86, 0.65, 0.29), lift=0.1)
    soft_disc(c, 0.25, cv - 0.04, 0.8, 0.25, (0.35, 0.2, 0.05), 0.4, 1.3)
    # back row: kaju katli / pista barfi diamonds
    cols = [(0.98, 0.93, 0.72), (0.66, 0.80, 0.40), (0.97, 0.90, 0.68), (0.45, 0.25, 0.12), (0.99, 0.82, 0.6)]
    for i in range(7):
        x = -0.58 + i * 0.19
        _barfi(c, x, 0.48 - 0.04 * abs(i - 3) * 0.6, 0.10, cols[i % 5], i % 2 == 0)
    # jalebi on the left
    _jalebi(c, -0.58, 0.28, 0.13)
    _jalebi(c, -0.36, 0.20, 0.12)
    # laddu pile centre
    for dx, dy in ((-0.08, 0.30), (0.10, 0.31), (0.01, 0.23)):
        _laddu(c, dx + 0.02, dy, 0.10, rng)
    _laddu(c, 0.02, 0.42, 0.095, rng)
    # gulab jamun / rasgulla right
    for dx, dy, col in ((0.38, 0.30, (0.45, 0.20, 0.07)), (0.50, 0.23, (0.50, 0.23, 0.08)), (0.60, 0.33, (0.45, 0.20, 0.07)), (0.46, 0.38, (0.5, 0.22, 0.08))):
        _ball(c, dx, dy, 0.09, col, 0.9, hl=0.6)
    for i in range(4):
        _barfi(c, 0.20 + i * 0.15, 0.13 - 0.01 * i, 0.07, (0.99, 0.82, 0.55) if i % 2 else (0.95, 0.5, 0.35), i % 2 == 1)
    for _ in range(18):                                                                # pistachio / almond bits
        c.ellipse(rng.uniform(-0.6, 0.65), rng.uniform(0.12, 0.45), rng.uniform(0.008, 0.016), 0.005, (0.55, 0.72, 0.28), lift=0, alpha=0.9, angle=rng.uniform(0, 180))
    soft_disc(c, -0.35, cv + 0.12, 0.5, 0.12, (1.0, 0.9, 0.6), 0.35, 1.1, add=True)


@sprop("sweet_jamun_bowl", aspect=1.0, fill=0.55)
def sweet_jamun_bowl(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.2)
    c.ellipse(0.0, 0.06, 0.36, 0.36 * 0.45, (0.55, 0.40, 0.17), lift=0)
    c.poly([(-0.42, 0.28), (0.42, 0.28), (0.30, 0.06), (-0.30, 0.06)], (0.82, 0.62, 0.30), lift=0.12)
    c.poly([(0.05, 0.28), (0.42, 0.28), (0.30, 0.06), (0.03, 0.06)], (0.35, 0.2, 0.05), lift=0, alpha=0.3)
    c.poly([(-0.39, 0.26), (-0.32, 0.26), (-0.25, 0.09), (-0.29, 0.09)], (1.0, 0.95, 0.75), lift=0, alpha=0.5)
    c.ellipse(0.0, 0.28, 0.42, 0.42 * 0.42, (0.62, 0.45, 0.18), lift=0)
    c.ellipse(0.0, 0.285, 0.40, 0.40 * 0.40, (0.95, 0.80, 0.50), lift=0.16)
    c.ellipse(0.0, 0.28, 0.34, 0.34 * 0.40, (0.38, 0.16, 0.05), lift=0)
    c.ellipse(0.0, 0.29, 0.33, 0.33 * 0.4, (0.72, 0.38, 0.10), lift=0.1)
    for k, (dx, dy) in enumerate(((-0.17, 0.31), (0.04, 0.33), (0.2, 0.30), (-0.07, 0.25), (0.12, 0.25), (-0.2, 0.26), (0.0, 0.40), (-0.12, 0.38), (0.15, 0.38))):
        _ball(c, dx, dy, 0.1, (0.46, 0.20, 0.07) if k % 2 else (0.52, 0.24, 0.08), 0.92, hl=0.75)
    for _ in range(14):
        c.ellipse(rng.uniform(-0.25, 0.25), rng.uniform(0.28, 0.46), rng.uniform(0.01, 0.018), 0.005, (0.6, 0.78, 0.3), lift=0, angle=rng.uniform(0, 180))
    steam(c, 0.0, 0.48, 0.26, 0.04, 2, 0.14)


@sprop("sweet_laddu_stand", aspect=0.9, fill=0.62)
def sweet_laddu_stand(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.16)
    c.rect(0.0, 0.09, 0.14, 0.18, (0.72, 0.52, 0.2), lift=0.1)
    c.ellipse(0.0, 0.03, 0.22, 0.22 * TILT, (0.70, 0.48, 0.18), lift=0)
    c.ellipse(0.0, 0.18, 0.40, 0.40 * 0.4, (0.55, 0.38, 0.14), lift=0)
    c.ellipse(0.0, 0.195, 0.38, 0.38 * 0.38, (0.95, 0.72, 0.30), lift=0.2)
    c.ellipse(0.0, 0.2, 0.31, 0.31 * 0.36, (0.80, 0.58, 0.24), lift=0.1)
    for row, (n, y, sp) in enumerate(((5, 0.25, 0.14), (4, 0.33, 0.13), (2, 0.42, 0.12))):
        for i in range(n):
            _laddu(c, (i - (n - 1) / 2.0) * sp * 1.1, y + (0.02 if i % 2 else 0.0), 0.075, rng)
    _laddu(c, 0.0, 0.50, 0.072, rng, (0.99, 0.72, 0.12))
    c.poly([(-0.02, 0.60), (0.02, 0.60), (0.0, 0.66)], (0.9, 0.92, 0.96), lift=0.2)


@niche("sweet-shop", "Sweet shop / mithai", subjects=("sweet_tray",),
       strong=("sweet shop", "mithai", "halwai", "sweets", "mithai shop", "indian sweets", "laddu", "barfi", "jalebi", "gulab jamun", "sweet mart",
               "मिठाई", "हलवाई", "मिठाई की दुकान", "मिठाई शॉप", "लड्डू", "जलेबी"),
       weak=("sweet", "dessert", "festival sweets", "dry fruits", "namkeen", "diwali", "mawa", "मावा", "मीठा"),
       accent="#f39c12", mood="warm", group="food")
def sweet_shop(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.45, 8.0, 0.30, scale(P.wall_bot, 0.8), lift=0.0)
        for sv in (0.16, 0.34):                                                              # shelves with boxes
            S.rect(1.0, sv, 8.0, 0.016, scale(P.surface, 0.85), lift=0.04)
            u = -1.2
            k = 0
            while u < 3.4:
                w = 0.14 + 0.05 * (k % 3)
                S.rect(u, sv - 0.05, w, 0.09, [P.accent, (0.75, 0.15, 0.12), (0.95, 0.85, 0.5), P.accent_dark][k % 4], r=0.008, lift=0.1)
                S.rect(u, sv - 0.075, w, 0.012, (1.0, 0.85, 0.45), lift=0.0, alpha=0.8)
                u += w + 0.03
                k += 1
        S.rect(0.35, 0.50, 0.6, 0.12, mix(P.accent, (0.7, 0.1, 0.1), 0.4), r=0.01, lift=0.0)    # signboard
        S.rect(0.35, 0.50, 0.56, 0.012, (1.0, 0.85, 0.4), lift=0.0)
        S.pendant(1.0, -0.1, 0.12, (1.0, 0.78, 0.4), 0.11)
        S.pendant(1.6, -0.1, 0.09, (1.0, 0.78, 0.4), 0.10)
        S.pendant(0.5, -0.1, 0.07, (1.0, 0.78, 0.4), 0.10)
        S.glow(1.0, 0.25, 1.4, (1.0, 0.8, 0.45), 0.25)
        S.bokeh(10, 0.0, 0.04, 2.0, 0.55, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.3)], 0.012, 0.04, 0.4)
        S.floor(0.60, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.60, 5.0, 1.4, scale(P.surface, 0.72), plank=0.14, grain=0.4)
    S.rect(1.0, 0.60, 8.0, 0.01, scale(P.surface, 0.35), lift=0.0)
    cloth = mix((0.72, 0.1, 0.1), P.accent, 0.25) if not dark else (0.45, 0.06, 0.06)
    S.rect(1.07, 0.88, 1.45, 0.62, cloth, lift=0.0)
    S.rect(1.07, 0.575 + 0.31 * 2 - 0.62 + 0.62 * 0.0, 1.45, 0.012, (1.0, 0.82, 0.35), lift=0.0, alpha=0.0)
    for k in range(0, 24):
        S.rect(0.36 + k * 0.0625, 0.88, 0.006, 0.60, (1.0, 0.82, 0.35), lift=0.0, alpha=0.25)
    S.rect(1.07, 0.58 + 0.015, 1.45, 0.014, (1.0, 0.82, 0.35), lift=0.0, alpha=0.8)
    S.rect(1.07, 1.185, 1.45, 0.016, (1.0, 0.82, 0.35), lift=0.0, alpha=0.8)
    S.soft(1.07, 0.84, 0.95, 0.24, (1.0, 0.82, 0.5), 0.32 if not dark else 0.45, 1.5, add=True)
    S.put("sweet_laddu_stand", 0.60, 0.80, 0.32)
    S.put("sweet_jamun_bowl", 1.60, 0.80, 0.24)
    S.put("sweet_tray", 1.08, 0.98, 0.40, subject=True)
    S.focus("detail", 1.08, 0.82)
    with S.near(18.0):
        S.soft(0.52, 1.02, 0.12, 0.08, (0.98, 0.6, 0.12), 0.8, 1.0)
        S.soft(1.72, 1.0, 0.10, 0.08, (1.0, 0.8, 0.3), 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- sushi
def _maki(c, u, v, r, fill, outside=False):
    """A cut maki roll standing on the board: nori side, rice ring, coloured filling (uramaki: rice outside with sesame)."""
    rng = c.rng
    h = r * 0.95
    tl = 0.62
    soft_disc(c, u + r * 0.2, v - r * 0.05, r * 1.15, r * 0.5, BLACK, 0.4, 1.4)
    if outside:
        craft.cylinder(c, u, v, r, h, (0.98, 0.97, 0.94), (0.72, 0.70, 0.66), (0.96, 0.95, 0.92), tl, lip=False)
        for _ in range(16):
            c.ellipse(u + rng.uniform(-r, r) * 0.9, v + rng.uniform(0.1, 0.9) * h, r * 0.05, r * 0.03, (0.15, 0.12, 0.1), lift=0, alpha=0.85)
        c.ellipse(u, v + h, r * 0.78, r * 0.78 * tl, (0.09, 0.11, 0.1), lift=0)
        c.ellipse(u, v + h + 0.003, r * 0.66, r * 0.66 * tl, (0.97, 0.96, 0.92), lift=0.1)
    else:
        craft.cylinder(c, u, v, r, h, (0.18, 0.22, 0.20), (0.03, 0.04, 0.04), (0.10, 0.13, 0.11), tl, lip=True)
        c.ellipse(u - r * 0.5, v + h * 0.55, r * 0.07, h * 0.4, (0.5, 0.6, 0.55), lift=0, alpha=0.35)
        c.ellipse(u, v + h + 0.002, r * 0.88, r * 0.88 * tl, (0.97, 0.96, 0.92), lift=0.1)
    for _ in range(14):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.85
        c.ellipse(u + math.cos(a) * r * q, v + h + math.sin(a) * r * q * tl, r * 0.05, r * 0.025, (0.88, 0.87, 0.82), lift=0, alpha=0.7)
    c.ellipse(u, v + h + 0.004, r * 0.42, r * 0.42 * tl, scale(fill, 0.7), lift=0)
    c.ellipse(u - r * 0.02, v + h + 0.008, r * 0.38, r * 0.38 * tl, fill, lift=0.15)
    gloss(c, u - r * 0.3, v + h + 0.01, r * 0.2, r * 0.07, 0, 0.5)


def _nigiri(c, u, v, k, top, kind):
    """Nigiri: rice oval with a draped slice of fish, shrimp or egg."""
    rng = c.rng
    soft_disc(c, u + 0.02 * k, v - 0.005, 0.15 * k, 0.05 * k, BLACK, 0.4, 1.4)
    c.ellipse(u, v + 0.03 * k, 0.115 * k, 0.062 * k, (0.80, 0.79, 0.75), lift=0)
    c.ellipse(u, v + 0.05 * k, 0.11 * k, 0.058 * k, (0.99, 0.98, 0.95), lift=0.12)
    for _ in range(10):
        c.ellipse(u + rng.uniform(-0.1, 0.1) * k, v + 0.045 * k + rng.uniform(-0.03, 0.03) * k, 0.012 * k, 0.005 * k, (0.9, 0.89, 0.84), lift=0, alpha=0.7,
                  angle=rng.uniform(0, 180))
    c.ellipse(u, v + 0.085 * k, 0.13 * k, 0.065 * k, scale(top, 0.62), lift=0)
    c.ellipse(u - 0.004 * k, v + 0.095 * k, 0.125 * k, 0.058 * k, top, lift=0.2)
    soft_disc(c, u + 0.05 * k, v + 0.08 * k, 0.1 * k, 0.04 * k, scale(top, 0.45), 0.35, 1.2)
    if kind == "salmon":
        for i in range(5):
            x = u + (-0.08 + i * 0.04) * k
            c.line(x, v + 0.075 * k, x + 0.025 * k, v + 0.115 * k, 0.012 * k, (1.0, 0.9, 0.82), 0.7)
    elif kind == "ebi":
        for i in range(5):
            x = u + (-0.09 + i * 0.045) * k
            c.line(x, v + 0.07 * k, x + 0.01 * k, v + 0.12 * k, 0.014 * k, (0.95, 0.42, 0.25), 0.8)
    elif kind == "egg":
        c.rect(u, v + 0.075 * k, 0.04 * k, 0.12 * k, (0.08, 0.1, 0.09), lift=0.1)
    gloss(c, u - 0.04 * k, v + 0.11 * k, 0.06 * k, 0.015 * k, 6, 0.65)


@sprop("sushi_board", aspect=2.7, fill=0.5)
def sushi_board(c, color):
    rng = c.rng
    slate = (0.21, 0.24, 0.26)
    ao(c, 0.0, 0.0, 1.4, 0.2)
    c.rect(-0.46, 0.015, 0.10, 0.03, (0.12, 0.10, 0.08), lift=0)                            # feet
    c.rect(0.46, 0.015, 0.10, 0.03, (0.12, 0.10, 0.08), lift=0)
    c.poly([(-0.69, 0.10), (0.69, 0.10), (0.68, 0.035), (-0.68, 0.035)], scale(slate, 0.5), lift=0)
    c.poly([(-0.64, 0.31), (0.64, 0.31), (0.69, 0.10), (-0.69, 0.10)], slate, lift=0.12)
    c.poly([(-0.62, 0.30), (0.62, 0.30), (0.66, 0.11), (-0.66, 0.11)], scale(slate, 1.12), lift=0.08)
    soft_disc(c, -0.35, 0.24, 0.55, 0.07, (0.8, 0.9, 1.0), 0.18, 1.2, add=True)
    for _ in range(26):
        c.ellipse(rng.uniform(-0.6, 0.6), rng.uniform(0.12, 0.29), rng.uniform(0.01, 0.03), 0.003, (0.5, 0.55, 0.58), lift=0, alpha=0.28)
    # back row of rolls then front
    _maki(c, -0.50, 0.22, 0.072, (0.98, 0.52, 0.30))
    _maki(c, -0.35, 0.235, 0.072, (0.55, 0.78, 0.30), True)
    _maki(c, -0.20, 0.22, 0.072, (0.82, 0.16, 0.18))
    _maki(c, -0.43, 0.14, 0.075, (0.98, 0.78, 0.25), True)
    _maki(c, -0.27, 0.135, 0.075, (0.55, 0.78, 0.30))
    # nigiri
    _nigiri(c, 0.02, 0.15, 1.0, (0.98, 0.52, 0.38), "salmon")
    _nigiri(c, 0.27, 0.235, 0.88, (0.78, 0.13, 0.17), "tuna")
    _nigiri(c, 0.44, 0.145, 1.0, (0.98, 0.78, 0.66), "ebi")
    # tobiko / ginger / wasabi
    for k in range(5):
        a = k * 1.25
        c.ellipse(0.57 + math.cos(a) * 0.045, 0.25 + math.sin(a) * 0.022, 0.04, 0.025, mix((0.97, 0.62, 0.7), WHITE, 0.2 + 0.1 * (k % 3)), lift=0.15, angle=k * 30)
    c.ellipse(0.57, 0.252, 0.05, 0.03, (0.98, 0.7, 0.75), lift=0.1, alpha=0.8)
    for k in range(4):
        c.ellipse(0.15 + k * 0.012, 0.275 + k * 0.004, 0.034, 0.02, (0.45 + k * 0.04, 0.75, 0.30), lift=0.15)
    c.ellipse(0.13, 0.272, 0.014, 0.008, (0.8, 0.95, 0.6), lift=0, alpha=0.8)
    for _ in range(14):
        c.ellipse(rng.uniform(-0.6, 0.6), rng.uniform(0.12, 0.28), 0.007, 0.004, (0.96, 0.94, 0.85), lift=0, alpha=0.7)
    soft_disc(c, 0.0, 0.18, 0.6, 0.08, (1.0, 0.95, 0.85), 0.10, 1.4, add=True)


@sprop("sushi_dish", aspect=2.0, fill=0.3)
def sushi_dish(c, color):
    ao(c, 0.0, 0.0, 0.6, 0.12)
    c.ellipse(0.0, 0.05, 0.29, 0.13, (0.06, 0.07, 0.09), lift=0)
    c.ellipse(0.0, 0.085, 0.29, 0.13, (0.20, 0.22, 0.27), lift=0.2)
    c.ellipse(0.0, 0.095, 0.24, 0.105, (0.07, 0.08, 0.10), lift=0)
    c.ellipse(0.0, 0.09, 0.225, 0.095, (0.16, 0.07, 0.03), lift=0.1)
    soft_disc(c, -0.08, 0.11, 0.11, 0.03, (1.0, 0.85, 0.7), 0.5, 1.1, add=True)
    craft.arc(c, 0.0, 0.09, 0.285, 0.125, 120, 190, 0.012, (0.8, 0.85, 1.0), 0.45, 6)


@sprop("sushi_chopsticks", aspect=3.0, fill=0.2)
def sushi_chopsticks(c, color):
    ao(c, 0.0, 0.0, 0.65, 0.1, 0.3)
    for (x0, y0, x1, y1) in ((-0.31, 0.05, 0.31, 0.12), (-0.30, 0.095, 0.31, 0.15)):
        c.line(x0, y0 - 0.004, x1, y1 - 0.004, 0.026, (0.28, 0.14, 0.06))
        c.line(x0, y0, x1, y1, 0.018, (0.62, 0.38, 0.17))
        c.line(x0 + 0.005, y0 + 0.004, x1 - 0.1, y1 + 0.004 - 0.07 * 0.1, 0.006, (0.95, 0.75, 0.45), 0.7)
        c.line(x1 - 0.12, y1 - 0.01, x1, y1, 0.02, (0.55, 0.08, 0.08))
        c.line(x0, y0, x0 + 0.04, y0 + 0.004, 0.013, (0.15, 0.08, 0.04))


@sprop("sushi_tea", aspect=0.55, fill=0.9)
def sushi_tea(c, color):
    ao(c, 0.0, 0.0, 0.4, 0.1)
    glaze = (0.82, 0.86, 0.80)
    c.ellipse(0.0, 0.03, 0.14, 0.14 * 0.45, scale(glaze, 0.6), lift=0)
    c.poly([(-0.19, 0.30), (0.19, 0.30), (0.14, 0.03), (-0.14, 0.03)], glaze, lift=0.08)
    for x0, al in ((0.0, 0.10), (0.06, 0.12), (0.12, 0.16)):
        c.poly([(x0, 0.30), (0.19, 0.30), (0.14, 0.03), (x0 * 0.75, 0.03)], (0.15, 0.2, 0.15), lift=0, alpha=al)
    c.poly([(-0.16, 0.28), (-0.11, 0.28), (-0.08, 0.06), (-0.11, 0.06)], WHITE, lift=0, alpha=0.5)
    c.poly([(-0.19, 0.22), (0.19, 0.22), (0.18, 0.18), (-0.18, 0.18)], (0.2, 0.3, 0.25), lift=0, alpha=0.35)
    c.ellipse(0.0, 0.30, 0.19, 0.19 * 0.4, scale(glaze, 0.8), lift=0)
    c.ellipse(0.0, 0.295, 0.165, 0.165 * 0.38, (0.38, 0.52, 0.18), lift=0.15)
    gloss(c, -0.05, 0.31, 0.07, 0.015, 5, 0.5)
    steam(c, 0.0, 0.36, 0.34, 0.035, 2, 0.14)


@niche("sushi", "Sushi bar / Japanese restaurant", subjects=("sushi_board",),
       strong=("sushi", "sushi bar", "japanese restaurant", "nigiri", "maki", "sashimi", "omakase", "izakaya", "ramen and sushi", "sushi restaurant",
               "सुशी", "जापानी रेस्टोरेंट", "सुशी बार", "जापानी खाना"),
       weak=("japanese", "japan", "ramen", "tempura", "wasabi", "bento", "teppanyaki", "जापान", "सशिमी"),
       accent="#c0392b", mood="dark", group="food")
def sushi(S):
    P = S.pal
    dark = P.mood == "dark"
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        S.wood(-3.0, -0.3, 5.0, 0.58, scale(P.wall_bot, 0.8 if not dark else 1.3), plank=0.12, vertical=True, grain=0.2)
        pane = mix(P.light, P.paper, 0.4)
        S.glow(0.55, 0.2, 0.9, P.light, 0.35)
        for i in range(5):                                                                 # shoji screen
            for j in range(3):
                S.rect(0.12 + i * 0.17, 0.02 + j * 0.17, 0.16, 0.16, scale(pane, 0.85 if not dark else 0.6), lift=0.0)
        S.rect(0.55, 0.19, 0.9, 0.012, scale(P.ink, 3.0), lift=0.0)
        S.rect(0.55, 0.36, 0.9, 0.014, scale(P.ink, 3.0), lift=0.0)
        for i in range(6):
            S.rect(0.12 - 0.085 + i * 0.17, 0.19, 0.012, 0.6, scale(P.ink, 3.0), lift=0.0)
        S.glow(1.52, 0.22, 0.5, (1.0, 0.55, 0.3), 0.5)                                       # lantern
        S.line(1.52, -0.1, 1.52, 0.10, 0.004, (0.15, 0.1, 0.08))
        S.ellipse(1.52, 0.22, 0.10, 0.12, mix(P.accent, (1.0, 0.5, 0.3), 0.4), lift=0.2)
        S.ellipse(1.50, 0.20, 0.05, 0.08, (1.0, 0.8, 0.55), lift=0.0, alpha=0.5)
        S.pendant(1.12, -0.1, 0.08, (1.0, 0.75, 0.4), 0.08)
        for k in range(4):
            S.line(1.88 + k * 0.07, -0.1, 1.88 + k * 0.07 + 0.01, 0.55, 0.035, (0.40, 0.55, 0.28) if k % 2 else (0.30, 0.45, 0.22))
        S.bokeh(8, 0.0, 0.05, 2.0, 0.5, [(1.0, 0.7, 0.4), (1.0, 0.5, 0.3)], 0.012, 0.035, 0.35)
        S.floor(0.58, P.floor_top, P.floor_bot)
    S.wood(-3.0, 0.58, 5.0, 1.4, scale(P.surface, 0.62 if not dark else 0.8), plank=0.16, grain=0.3)
    S.rect(1.0, 0.58, 8.0, 0.012, scale(P.ink, 3.0), lift=0.0)
    S.rect(1.0, 0.60, 8.0, 0.012, scale(P.surface, 1.2), lift=0.0, alpha=0.7)
    S.soft(1.1, 0.80, 1.0, 0.22, (1.0, 0.82, 0.6), 0.30 if not dark else 0.45, 1.5, add=True)
    S.soft(1.55, 0.72, 0.4, 0.12, (1.0, 0.5, 0.3), 0.18, 1.5, add=True)
    S.put("sushi_tea", 0.64, 0.74, 0.22)
    S.put("sushi_dish", 1.58, 0.84, 0.15)
    S.put("sushi_chopsticks", 1.05, 1.0, 0.20)
    S.put("sushi_board", 1.05, 0.93, 0.36, subject=True)
    S.focus("detail", 1.0, 0.82)
    with S.near(18.0):
        S.soft(0.52, 1.02, 0.12, 0.08, P.accent, 0.5, 1.0)
        S.soft(1.72, 1.0, 0.10, 0.08, (1.0, 0.7, 0.4), 0.45, 1.0)
