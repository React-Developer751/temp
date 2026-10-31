"""Food and drink niches."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, drip, gloss, leaf, soft_disc, speckle, steam
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale

WOOD = (0.64, 0.43, 0.25)


@sprop("pizza_board", aspect=2.7, fill=0.5)
def pizza_board(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.35, 0.30)
    # wooden board with thickness, handle and grain
    c.rect(0.74, 0.07, 0.34, 0.075, scale(WOOD, 0.80), r=0.035, lift=0.05)
    c.ellipse(0.0, 0.035, 0.68, 0.68 * TILT, scale(WOOD, 0.62), lift=0)
    disc(c, 0.0, 0.085, 0.68, WOOD, TILT, 0.10, rim=True)
    for _ in range(14):
        a = rng.uniform(0.15, 0.62)
        craft.arc(c, rng.uniform(-0.15, 0.15), 0.085, a, a * TILT, rng.uniform(0, 200), rng.uniform(220, 340), 0.003, scale(WOOD, rng.uniform(0.80, 0.9)), 0.4)
    # pizza
    disc(c, 0.0, 0.135, 0.53, (0.86, 0.60, 0.28), TILT, 0.14)
    for k in range(26):                                                    # blistered crust
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.485, 0.52)
        c.ellipse(math.cos(a) * r, 0.14 + math.sin(a) * r * TILT, rng.uniform(0.012, 0.03), rng.uniform(0.006, 0.014),
                  (0.55, 0.30, 0.12) if k % 3 else (0.93, 0.72, 0.38), alpha=0.75, lift=0)
    c.ellipse(0.0, 0.15, 0.45, 0.45 * TILT, (0.78, 0.18, 0.10), lift=0.1)                # sauce edge
    c.ellipse(0.0, 0.155, 0.425, 0.425 * TILT, (0.99, 0.84, 0.47), lift=0.10)             # cheese
    soft_disc(c, -0.1, 0.19, 0.32, 0.11, WHITE, 0.30, 1.0, add=True)
    for _ in range(14):                                                    # melted cheese patches
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.38
        c.ellipse(math.cos(a) * r, 0.155 + math.sin(a) * r * TILT, rng.uniform(0.03, 0.07), rng.uniform(0.012, 0.03),
                  rng.choice([(0.95, 0.72, 0.30), (1.0, 0.92, 0.62), (0.9, 0.62, 0.25)]), alpha=0.6, lift=0)
    for a0 in range(0, 360, 60):                                           # slice cuts
        a = math.radians(a0 + 20)
        c.line(0.0, 0.155, math.cos(a) * 0.43, 0.155 + math.sin(a) * 0.43 * TILT, 0.006, (0.62, 0.38, 0.14), 0.6)
    for i in range(6):                                                     # tomato slices
        a = 2 * math.pi * i / 6 + 0.4
        u, v = math.cos(a) * 0.26 + rng.uniform(-0.03, 0.03), 0.16 + math.sin(a) * 0.26 * TILT
        c.ellipse(u, v, 0.075, 0.075 * 0.62, (0.62, 0.10, 0.08), lift=0)
        c.ellipse(u, v + 0.004, 0.066, 0.066 * 0.6, (0.88, 0.17, 0.12), lift=0.12)
        c.ellipse(u, v + 0.006, 0.03, 0.02, (0.97, 0.45, 0.32), alpha=0.7, lift=0)
        gloss(c, u - 0.02, v + 0.015, 0.025, 0.012, 0, 0.5)
    for i in range(5):                                                     # mozzarella
        a = 2 * math.pi * i / 5 + 1.1
        u, v = math.cos(a) * 0.12 + rng.uniform(-0.05, 0.05), 0.16 + math.sin(a) * 0.12 * TILT
        c.ellipse(u, v, 0.05, 0.028, (0.99, 0.97, 0.9), lift=0.1)
        c.ellipse(u + 0.01, v + 0.005, 0.03, 0.014, (1.0, 1.0, 0.97), alpha=0.8, lift=0)
    for i in range(6):                                                     # basil
        a = 2 * math.pi * i / 6 + 0.9
        u, v = math.cos(a) * rng.uniform(0.12, 0.34), 0.17 + math.sin(a) * rng.uniform(0.12, 0.34) * TILT
        leaf(c, u, v, rng.uniform(0.12, 0.17), rng.uniform(0, 360), (0.18, 0.52, 0.20) if i % 2 else (0.25, 0.62, 0.25), 0.5)
    soft_disc(c, 0.05, 0.20, 0.46, 0.14, (1.0, 0.95, 0.8), 0.14, 1.3, add=True)


@sprop("tomato_vine", aspect=1.1, fill=0.55)
def tomato_vine(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.14)
    for u, v, r in ((-0.22, 0.13, 0.13), (0.16, 0.12, 0.14), (-0.02, 0.28, 0.12), (0.34, 0.1, 0.09)):
        c.ellipse(u, v, r, r * 0.92, (0.62, 0.08, 0.06), lift=0)
        c.ellipse(u - 0.005, v + 0.008, r * 0.96, r * 0.88, (0.86, 0.14, 0.10), lift=0.15)
        soft_disc(c, u + r * 0.25, v - r * 0.35, r * 0.7, r * 0.45, (0.4, 0.04, 0.03), 0.45, 1.2)
        gloss(c, u - r * 0.35, v + r * 0.4, r * 0.28, r * 0.15, 25, 0.8)
        for k in range(5):
            leaf(c, u, v + r * 0.85, r * 0.55, 90 + (k - 2) * 34, (0.20, 0.5, 0.2), 0.3)
    for k in range(3):
        leaf(c, 0.05, 0.12, 0.28, 30 + k * 55, (0.2, 0.55, 0.22), 0.45)


@sprop("basil_pot", aspect=0.9, fill=1.0)
def basil_pot(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.55, 0.10)
    craft.hshade_box(c, 0.0, 0.14, 0.40, 0.28, (0.80, 0.42, 0.28), (0.52, 0.22, 0.14), r=0.04)
    disc(c, 0.0, 0.28, 0.21, (0.40, 0.25, 0.16), TILT, 0.0)
    for i in range(22):
        a = rng.uniform(30, 150)
        leaf(c, rng.uniform(-0.1, 0.1), 0.30, rng.uniform(0.20, 0.34), a + rng.uniform(-18, 18),
             (0.16 + rng.random() * 0.1, 0.5 + rng.random() * 0.14, 0.2), 0.55)


@sprop("pasta_bowl", aspect=1.45, fill=0.62)
def pasta_bowl(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.05, 0.22)
    white = (0.97, 0.96, 0.93)
    # bowl: shaded body that narrows to a foot, then rim, inner wall, food
    c.poly([(-0.50, 0.30), (0.50, 0.30), (0.36, 0.06), (-0.36, 0.06)], scale(white, 0.8), lift=0)
    craft.hshade_box(c, 0.0, 0.17, 0.96, 0.22, white, (0.70, 0.68, 0.65), r=0.05)
    c.ellipse(0.0, 0.065, 0.36, 0.36 * 0.36, (0.66, 0.64, 0.61), lift=0)
    c.ellipse(0.0, 0.065, 0.3, 0.3 * 0.3, (0.78, 0.76, 0.72), lift=0)
    disc(c, 0.0, 0.30, 0.50, white, 0.42, 0.04, rim=True)
    c.ellipse(0.0, 0.305, 0.43, 0.43 * 0.42, (0.86, 0.84, 0.80), lift=0)
    soft_disc(c, 0.04, 0.29, 0.40, 0.14, BLACK, 0.18, 1.2)
    c.ellipse(0.0, 0.33, 0.38, 0.38 * 0.40, (0.93, 0.74, 0.34), lift=0.1)
    for _ in range(46):
        a, r = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.30
        craft.strand(c, math.cos(a) * r - 0.06, 0.34 + math.sin(a) * r * 0.40, rng.uniform(0.10, 0.2), rng.uniform(0, 360), 0.014,
                     rng.choice([(0.97, 0.82, 0.42), (0.88, 0.66, 0.28), (0.99, 0.9, 0.58)]), 0.95, 0.9)
    c.ellipse(0.0, 0.40, 0.19, 0.075, (0.72, 0.14, 0.08), lift=0.1)
    for _ in range(14):
        c.ellipse(rng.uniform(-0.15, 0.15), 0.40 + rng.uniform(-0.04, 0.04), rng.uniform(0.012, 0.025), rng.uniform(0.010, 0.02),
                  rng.choice([(0.82, 0.18, 0.1), (0.62, 0.10, 0.06)]), lift=0.1)
    for i in range(4):
        leaf(c, rng.uniform(-0.1, 0.1), 0.42, 0.11, rng.uniform(30, 150), (0.2, 0.58, 0.24), 0.5)
    gloss(c, -0.12, 0.43, 0.10, 0.03, 8, 0.45)
    steam(c, 0.0, 0.48, 0.5, 0.07, 3, 0.2)


@sprop("wine_glass", aspect=0.38, fill=1.0)
def wine_glass(c, color):
    ao(c, 0.0, 0.0, 0.32, 0.06)
    c.ellipse(0.0, 0.015, 0.14, 0.14 * TILT, (0.85, 0.88, 0.9), alpha=0.7, lift=0)
    c.rect(0.0, 0.2, 0.018, 0.38, (0.88, 0.92, 0.95), alpha=0.8, lift=0)
    c.poly([(-0.17, 0.95), (0.17, 0.95), (0.19, 0.62), (0.1, 0.4), (-0.1, 0.4), (-0.19, 0.62)], (0.9, 0.94, 0.97), alpha=0.35)
    c.poly([(-0.185, 0.64), (0.185, 0.64), (0.10, 0.41), (-0.10, 0.41)], (0.50, 0.06, 0.12), alpha=0.92)
    c.ellipse(0.0, 0.64, 0.185, 0.185 * 0.28, (0.62, 0.1, 0.16), lift=0.2)
    c.line(-0.12, 0.9, -0.15, 0.66, 0.018, WHITE, 0.55)
    gloss(c, -0.1, 0.78, 0.018, 0.1, 12, 0.7)


@niche("restaurant-italian", "Italian restaurant", subjects=("pizza_board",),
       strong=("italian restaurant", "pizzeria", "wood fired pizza", "pizza", "trattoria", "pasta", "spaghetti", "lasagna", "risotto", "tiramisu",
               "italian food", "pizza wali", "pizza ki dukaan", "पिज़्ज़ा", "पिज्जा", "पास्ता", "इटालियन"),
       weak=("italian", "wood fired", "wine", "margherita", "mozzarella", "carbonara", "oven baked", "trattoria style"),
       accent="#c0392b", mood="warm", group="food")
def italian(S):
    P = S.pal
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.56)
        S.rect(1.0, 0.45, 12.0, 0.2, scale(P.wall_bot, 0.84), lift=0.0)                       # darker wainscot band
        S.window(0.30, 0.26, 0.30, 0.30)
        S.pendant(1.20, -0.1, 0.20)
        S.pendant(1.70, -0.1, 0.15)
        S.pendant(0.78, -0.1, 0.13)
        S.bokeh(12, 0.0, 0.06, 2.0, 0.46, [(1.0, 0.88, 0.58), (1.0, 0.72, 0.42)], 0.012, 0.045)
        S.floor(0.56, P.floor_top, P.floor_bot)
    S.soft(1.15, 0.60, 0.9, 0.16, (1.0, 0.85, 0.55), 0.22, 1.5, add=True)
    S.wood(-5.0, 0.56, 7.0, 2.6, P.surface, plank=0.11)
    S.rect(1.0, 0.56, 14.0, 0.008, scale(P.surface, 0.45), lift=0.0)
    S.put("basil_pot", 0.72, 0.70, 0.19)
    S.put("tomato_vine", 1.62, 0.74, 0.17)
    S.put("wine_glass", 1.80, 0.70, 0.30)
    S.put("pizza_board", 1.18, 0.86, 0.30, subject=True)
    S.put("pasta_bowl", 0.80, 0.96, 0.20)
    S.focus("detail", 1.18, 0.74)
