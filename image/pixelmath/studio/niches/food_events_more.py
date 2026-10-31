"""More food, drink and event niches: restaurant, south indian, chinese restaurant, street food, bar and lounge, catering, tent house."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, disc, drip, gloss, leaf, soft_disc, speckle, steam
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale

BRASS = (0.86, 0.64, 0.26)
STEEL = (0.80, 0.82, 0.85)


# ---------------------------------------------------------------------------------------------- shared helpers
def _ball(c, u, v, r, col, tilt=1.0, rim=0.62, hl=0.4):
    """A shaded sphere: dark rim, lit body, shade low right, soft highlight upper left."""
    c.ellipse(u, v, r, r * tilt, scale(col, rim), lift=0)
    c.ellipse(u - r * 0.05, v + r * 0.06 * tilt, r * 0.94, r * 0.92 * tilt, col, lift=0.16)
    soft_disc(c, u + r * 0.28, v - r * 0.3 * tilt, r * 0.62, r * 0.5 * tilt, scale(col, 0.4), 0.42, 1.3)
    if hl:
        soft_disc(c, u - r * 0.34, v + r * 0.36 * tilt, r * 0.34, r * 0.22 * tilt, WHITE, hl, 1.1, add=True)


def _cyl(c, u, v, r, h, left, right, top, tilt=TILT, rim=None):
    """Upright cylinder / pot: lit left, shaded right, a top ellipse and a rim line."""
    c.ellipse(u, v, r, r * tilt, scale(right, 0.75), lift=0)
    craft.hshade_box(c, u, v + h / 2, 2 * r, h, left, right)
    c.ellipse(u, v + h, r, r * tilt, scale(right, 0.8), lift=0)
    c.ellipse(u, v + h + 0.004, r * 0.975, r * tilt * 0.96, top, lift=0.06)
    if rim is not None:
        craft.arc(c, u, v + h, r * 0.985, r * tilt * 0.98, 190, 350, r * 0.05, rim, 0.8, 8)


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


def _frect(c, u0, v0, u1, v1, color, alpha=1.0):
    """A fast, hard-edged axis-aligned fill in prop units (v up) for big flat areas where an anti-aliased polygon would be slow."""
    c.cv.fill_rect(c.X(u0), c.Y(v1), c.X(u1), c.Y(v0), color, alpha)


def _dark(P):
    return P.mood == "dark"


def _cloth(P, k=1.0):
    """White linen that follows the mood (dimmed in dark mood so it does not glare)."""
    base = mix(P.paper, WHITE, 0.4)
    return scale(mix(base, P.accent, 0.25), 0.42 * k) if _dark(P) else scale(base, 0.97 * k)


def _hanging_bulbs(S, u0, u1, v_a, v_b, n, color=(1.0, 0.82, 0.5), r=0.016):
    """A sagging string of bulbs with glows (far layer)."""
    for i in range(n):
        t = i / (n - 1.0)
        u = u0 + (u1 - u0) * t
        v = v_a + (v_b - v_a) * t + 0.05 * math.sin(math.pi * t)
        S.glow(u, v, 0.15, color, 0.55)
        S.circle(u, v, r, mix(color, WHITE, 0.6), lift=0, soft=2.0)


# ---------------------------------------------------------------------------------------------- restaurant (fine dining)
@sprop("rest_setting", aspect=3.5, fill=0.47)
def rest_setting(c, color):
    rng = c.rng
    cu, cv = 0.0, 0.20
    soft_disc(c, 0.04, 0.0, 0.95, 0.20, BLACK, 0.40, 1.7)
    # napkin folded under the fork: a pale linen rectangle with a crease, a hem and a gold ring
    nc = mix(color or (0.80, 0.20, 0.16), WHITE, 0.45)
    c.poly([(-1.02, 0.06), (-0.76, 0.06), (-0.74, 0.25), (-1.00, 0.265)], scale(nc, 0.7), lift=0.1)
    c.poly([(-1.015, 0.072), (-0.765, 0.072), (-0.745, 0.245), (-0.995, 0.255)], nc, lift=0.18)
    c.poly([(-1.015, 0.072), (-0.765, 0.072), (-0.762, 0.10), (-1.012, 0.10)], scale(nc, 0.84), lift=0, alpha=0.6)
    c.line(-1.005, 0.165, -0.752, 0.158, 0.006, scale(nc, 0.65), 0.7)
    soft_disc(c, -0.92, 0.2, 0.1, 0.04, WHITE, 0.25, 1.2, add=True)
    # fork (left) and knife / spoon (right), lying along the table
    c.line(-0.90, 0.06, -0.90, 0.34, 0.032, scale(STEEL, 0.72))
    c.line(-0.905, 0.075, -0.905, 0.34, 0.020, STEEL)
    for dx in (-0.034, -0.011, 0.012, 0.035):
        c.line(-0.90 + dx, 0.34, -0.90 + dx, 0.44, 0.008, STEEL)
    c.line(-0.90, 0.34, -0.90, 0.385, 0.056, STEEL, 0.9)
    c.line(0.82, 0.04, 0.82, 0.30, 0.020, scale(STEEL, 0.78))
    c.poly([(0.795, 0.30), (0.845, 0.30), (0.852, 0.45), (0.82, 0.47), (0.795, 0.44)], STEEL, lift=0.12)
    c.line(0.802, 0.32, 0.806, 0.44, 0.008, WHITE, 0.7)
    c.ellipse(0.95, 0.09, 0.034, 0.075, STEEL, lift=0.14)
    c.line(0.95, 0.02, 0.95, 0.07, 0.014, scale(STEEL, 0.78))
    # charger plate + plate
    disc(c, cu, cv, 0.63, (0.86, 0.64, 0.30), TILT, 0.14)
    craft.arc(c, cu, cv + 0.01, 0.56, 0.56 * TILT, 120, 190, 0.03, (1.0, 0.94, 0.7), 0.7, 8)
    disc(c, cu, cv + 0.045, 0.52, (0.98, 0.98, 0.96), TILT, 0.06)
    c.ellipse(cu, cv + 0.057, 0.36, 0.36 * TILT, (0.94, 0.94, 0.92), lift=0.05)
    soft_disc(c, cu - 0.12, cv + 0.09, 0.3, 0.09, WHITE, 0.3, 1.2, add=True)
    # food: sauce swoosh, seared fillet, puree, beans, micro-herbs
    craft.arc(c, cu - 0.04, cv + 0.09, 0.27, 0.27 * TILT, 160, 340, 0.05, (0.36, 0.10, 0.07), 0.95, 10)
    craft.arc(c, cu - 0.04, cv + 0.095, 0.27, 0.27 * TILT, 180, 280, 0.012, (0.75, 0.30, 0.2), 0.6, 8)
    for _ in range(6):
        c.ellipse(rng.uniform(0.18, 0.34), cv + 0.07 + rng.uniform(-0.04, 0.05), 0.016, 0.010, (0.34, 0.09, 0.06), lift=0.1)
    for k in range(4):                                                                           # sliced roast, fanned
        x, y = -0.02 + k * 0.075, cv + 0.12 + k * 0.01
        c.ellipse(x, y, 0.075, 0.075, (0.36, 0.17, 0.08), angle=-20, lift=0)
        c.ellipse(x + 0.004, y + 0.006, 0.066, 0.066, (0.86, 0.50, 0.44), angle=-20, lift=0.2)
        c.ellipse(x + 0.006, y + 0.008, 0.036, 0.04, (0.93, 0.62, 0.56), angle=-20, lift=0, alpha=0.8)
    c.ellipse(0.08, cv + 0.205, 0.17, 0.02, (0.30, 0.13, 0.06), lift=0, alpha=0.85)
    gloss(c, 0.0, cv + 0.19, 0.08, 0.02, 8, 0.45)
    c.ellipse(-0.20, cv + 0.075, 0.095, 0.05, (0.90, 0.80, 0.56), lift=0)                      # puree
    c.ellipse(-0.205, cv + 0.098, 0.085, 0.052, (0.98, 0.92, 0.72), lift=0.16)
    gloss(c, -0.23, cv + 0.12, 0.04, 0.014, 0, 0.5)
    for k in range(6):                                                                           # green beans
        x = 0.20 + k * 0.012
        craft.strand(c, x + 0.02, cv + 0.07 + k * 0.006, 0.17, 20 + k * 3, 0.016, (0.22, 0.52, 0.18) if k % 2 else (0.30, 0.62, 0.22), 1.0, 0.25)
    for _ in range(9):
        leaf(c, rng.uniform(-0.08, 0.14), cv + 0.22 + rng.uniform(-0.01, 0.03), rng.uniform(0.05, 0.08), rng.uniform(20, 160), (0.28, 0.66, 0.26), 0.5)
    c.ellipse(0.1, cv + 0.20, 0.014, 0.01, (0.95, 0.85, 0.2), lift=0.1)


@sprop("rest_wine_glass", aspect=0.5, fill=1.0)
def rest_wine_glass(c, color):
    ao(c, 0.0, 0.0, 0.5, 0.09)
    wine = color or (0.46, 0.04, 0.12)
    c.ellipse(0.0, 0.015, 0.20, 0.20 * TILT, (0.82, 0.86, 0.9), alpha=0.65, lift=0)
    c.ellipse(0.0, 0.02, 0.17, 0.17 * TILT, (0.94, 0.96, 0.98), alpha=0.5, lift=0)
    c.rect(0.0, 0.22, 0.025, 0.40, (0.86, 0.9, 0.94), alpha=0.85, lift=0)
    c.rect(-0.006, 0.22, 0.008, 0.40, WHITE, alpha=0.6, lift=0)
    bowl = [(-0.22, 0.97), (0.22, 0.97), (0.27, 0.74), (0.17, 0.50), (0.0, 0.43), (-0.17, 0.50), (-0.27, 0.74)]
    c.poly(bowl, (0.88, 0.93, 0.97), alpha=0.30, lift=0)
    c.poly([(-0.265, 0.74), (0.265, 0.74), (0.17, 0.50), (0.0, 0.435), (-0.17, 0.50)], wine, alpha=0.95, lift=0.1)
    soft_disc(c, 0.1, 0.56, 0.2, 0.1, BLACK, 0.4, 1.2)
    c.ellipse(0.0, 0.74, 0.265, 0.265 * 0.30, mix(wine, WHITE, 0.15), lift=0.18)
    c.ellipse(-0.02, 0.742, 0.19, 0.045, mix(wine, (1, 0.6, 0.6), 0.4), lift=0, alpha=0.5)
    c.ellipse(0.0, 0.97, 0.22, 0.22 * 0.27, (0.9, 0.95, 1.0), lift=0, alpha=0.45)
    craft.arc(c, 0.0, 0.97, 0.22, 0.22 * 0.27, 0, 180, 0.012, WHITE, 0.7, 8)
    c.line(-0.18, 0.92, -0.235, 0.74, 0.022, WHITE, 0.6)
    gloss(c, -0.17, 0.62, 0.02, 0.09, 12, 0.7)
    c.line(0.20, 0.9, 0.245, 0.76, 0.01, WHITE, 0.35)


@sprop("rest_candle", aspect=0.75, fill=1.0)
def rest_candle(c, color):
    ao(c, 0.0, 0.0, 0.5, 0.09)
    c.ellipse(0.0, 0.03, 0.24, 0.24 * TILT, scale(BRASS, 0.5), lift=0)
    craft.hshade_box(c, 0.0, 0.09, 0.07, 0.12, (0.95, 0.76, 0.40), (0.52, 0.36, 0.14))
    c.ellipse(0.0, 0.07, 0.12, 0.05, (0.9, 0.7, 0.34), lift=0.1)
    c.ellipse(0.0, 0.17, 0.2, 0.2 * TILT, scale(BRASS, 0.5), lift=0)
    c.ellipse(0.0, 0.18, 0.19, 0.19 * TILT, (0.95, 0.76, 0.40), lift=0.14)
    craft.hshade_box(c, 0.0, 0.5, 0.15, 0.62, (1.0, 0.97, 0.9), (0.80, 0.74, 0.62))
    c.ellipse(0.0, 0.81, 0.075, 0.075 * TILT, (0.97, 0.92, 0.82), lift=0.04)
    c.ellipse(0.0, 0.80, 0.045, 0.02, (1.0, 0.88, 0.55), lift=0, alpha=0.8)
    soft_disc(c, 0.0, 0.93, 0.9, 0.9, (1.0, 0.7, 0.28), 0.5, 2.2, add=True)
    c.poly([(-0.032, 0.83), (0.032, 0.83), (0.0, 1.0)], (1.0, 0.70, 0.2), lift=0.1)
    c.poly([(-0.017, 0.835), (0.017, 0.835), (0.0, 0.93)], (1.0, 0.97, 0.75), lift=0, alpha=0.95)
    c.line(0.0, 0.81, 0.0, 0.84, 0.005, (0.15, 0.1, 0.1))


def _rose(c, u, v, r, col, bud=False):
    """A rose seen from the side: layered outer petals, a spiral heart, shaded lower right, lit upper left, a dew drop."""
    rng = c.rng
    dk = scale(col, 0.50)
    if bud:
        c.ellipse(u, v, r * 0.62, r * 0.9, dk, lift=0, angle=rng.uniform(-14, 14))
        c.ellipse(u - r * 0.04, v + r * 0.05, r * 0.5, r * 0.78, col, lift=0.16, angle=8)
        craft.arc(c, u, v + r * 0.1, r * 0.3, r * 0.5, 100, 300, r * 0.07, dk, 0.8, 6)
        c.poly([(u - r * 0.5, v - r * 0.5), (u, v - r * 0.9), (u + r * 0.5, v - r * 0.5), (u, v - r * 0.15)], (0.2, 0.5, 0.2), lift=0.05)
        return
    c.ellipse(u, v, r, r * 0.94, dk, lift=0)
    for k in range(6):                                                              # outer petals, a ring
        a = k * 1.047 + 0.3
        c.ellipse(u + math.cos(a) * r * 0.55, v + math.sin(a) * r * 0.5, r * 0.5, r * 0.44, scale(col, 0.84 + 0.07 * (k % 3)), lift=0.16, angle=math.degrees(a) + 90)
        craft.arc(c, u + math.cos(a) * r * 0.55, v + math.sin(a) * r * 0.5, r * 0.46, r * 0.4, 200 + k * 6, 330 + k * 6, r * 0.04, mix(col, WHITE, 0.4), 0.7, 5, angle=math.degrees(a) + 90)
    for k in range(4):                                                              # inner ring
        a = k * 1.571 + 0.9
        c.ellipse(u + math.cos(a) * r * 0.28, v + math.sin(a) * r * 0.26, r * 0.42, r * 0.36, scale(col, 1.0 + 0.08 * (k % 2)), lift=0.2, angle=math.degrees(a) + 90)
    c.ellipse(u, v, r * 0.3, r * 0.27, scale(col, 0.72), lift=0)                  # spiral heart
    craft.arc(c, u, v, r * 0.24, r * 0.21, 20, 330, r * 0.06, mix(col, WHITE, 0.2), 0.85, 8)
    craft.arc(c, u + r * 0.02, v + r * 0.01, r * 0.13, r * 0.11, 120, 420, r * 0.05, scale(col, 0.5), 0.9, 8)
    soft_disc(c, u - r * 0.34, v + r * 0.36, r * 0.4, r * 0.26, WHITE, 0.30, 1.2, add=True)
    c.ellipse(u - r * 0.5, v + r * 0.08, r * 0.045, r * 0.06, WHITE, lift=0, alpha=0.8)


@sprop("rest_vase", aspect=1.05, fill=1.0)
def rest_vase(c, color):
    rng = c.rng
    flower = color or (0.86, 0.18, 0.30)
    ao(c, 0.0, 0.0, 0.55, 0.10)
    # stems and leaves, seen through the water
    for k in range(7):
        a = 90 + (k - 3) * 14
        x = math.cos(math.radians(a)) * 0.34
        c.line((k - 3) * 0.02, 0.18, x, 0.26 + math.sin(math.radians(a)) * 0.34, 0.013, (0.20, 0.45, 0.18))
    for k in range(6):
        leaf(c, rng.uniform(-0.08, 0.08), 0.30 + rng.uniform(0, 0.1), rng.uniform(0.2, 0.32), 90 + (k - 2.5) * 30, (0.18 + rng.random() * 0.06, 0.48, 0.2), 0.42)
    # crystal bud vase with water
    c.poly([(-0.14, 0.5), (0.14, 0.5), (0.22, 0.26), (0.21, 0.08), (-0.21, 0.08), (-0.22, 0.26)], (0.82, 0.90, 0.92), alpha=0.7, lift=0)
    c.poly([(-0.15, 0.40), (0.15, 0.40), (0.215, 0.25), (0.205, 0.09), (-0.205, 0.09), (-0.215, 0.25)], (0.66, 0.82, 0.86), alpha=0.6, lift=0.05)
    for x0 in (-0.10, 0.0, 0.10):                                                    # stems showing in the water, refracted
        c.line(x0 * 0.6, 0.40, x0 * 1.4, 0.10, 0.012, (0.18, 0.42, 0.18), 0.85)
    for _ in range(5):
        c.ellipse(rng.uniform(-0.14, 0.14), rng.uniform(0.14, 0.36), 0.008, 0.008, WHITE, lift=0, alpha=0.7)
    c.ellipse(0.0, 0.07, 0.21, 0.21 * TILT, (0.55, 0.70, 0.72), lift=0, alpha=0.8)
    c.ellipse(0.0, 0.5, 0.14, 0.14 * TILT, (0.9, 0.96, 0.98), lift=0, alpha=0.55)
    craft.arc(c, 0.0, 0.5, 0.14, 0.14 * TILT, 0, 180, 0.01, WHITE, 0.7, 6)
    c.line(-0.14, 0.44, -0.19, 0.2, 0.018, WHITE, 0.6)
    gloss(c, -0.12, 0.3, 0.015, 0.09, 0, 0.5)
    # baby's breath behind the roses
    for _ in range(14):
        x, y = rng.uniform(-0.42, 0.42), rng.uniform(0.55, 0.92)
        c.ellipse(x, y, 0.014, 0.014, (0.98, 0.97, 0.95), lift=0.1)
    # roses: back row, then buds at the sides, the big one in front
    _rose(c, -0.31, 0.64, 0.14, scale(flower, 0.86))
    _rose(c, 0.31, 0.63, 0.14, scale(flower, 0.80))
    _rose(c, -0.04, 0.84, 0.17, mix(flower, (1.0, 0.5, 0.55), 0.3))
    _rose(c, -0.43, 0.46, 0.09, scale(flower, 0.8), bud=True)
    _rose(c, 0.42, 0.50, 0.09, scale(flower, 0.75), bud=True)
    _rose(c, 0.11, 0.62, 0.16, flower)
    _rose(c, -0.14, 0.60, 0.15, scale(flower, 1.08))


@sprop("rest_bread", aspect=1.4, fill=0.5)
def rest_bread(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.2)
    c.ellipse(0.0, 0.04, 0.45, 0.45 * TILT, (0.78, 0.76, 0.74), lift=0)
    disc(c, 0.0, 0.06, 0.45, (0.97, 0.97, 0.95), TILT, 0.06)
    for k, (dx, dy) in enumerate(((-0.12, 0.0), (0.12, 0.02), (0.0, 0.07))):
        _ball(c, dx, 0.16 + dy, 0.15, (0.80, 0.52, 0.22), 0.8, hl=0.3)
        c.line(dx - 0.06, 0.20 + dy, dx + 0.05, 0.215 + dy, 0.012, (0.55, 0.3, 0.1), 0.6)
    c.ellipse(0.36, 0.09, 0.07, 0.04, (0.98, 0.88, 0.4), lift=0.14)


@niche("restaurant", "Restaurant / fine dining", subjects=("rest_setting",),
       strong=("restaurant", "fine dining", "family restaurant", "multicuisine restaurant", "multi cuisine restaurant", "dine in", "dine-in",
               "casual dining", "restaurant and bar", "restaurant ka", "रेस्टोरेंट", "रेस्तरां", "रेस्टोरेन्ट", "फाइन डाइनिंग"),
       weak=("dining", "menu", "table booking", "reservation", "chef", "gourmet", "diners", "dinner"),
       accent="#b71c1c", mood="warm", group="food",
       avoid=("italian restaurant", "pizzeria", "sushi", "chinese restaurant", "south indian restaurant", "cloud kitchen"))
def restaurant(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.50, 14.0, 0.26, scale(mix(P.wall_bot, P.accent_dark, 0.3), 0.85), lift=0.0)           # wainscot
        S.rect(1.0, 0.375, 14.0, 0.010, scale(P.accent_light if not dark else P.accent, 0.9), lift=0.0)
        S.window(0.26, 0.24, 0.30, 0.34, (0.55, 0.72, 0.90), (0.95, 0.90, 0.78))
        S.bokeh(8, 0.14, 0.12, 0.40, 0.36, [(1.0, 0.9, 0.6), (1.0, 0.6, 0.4), (0.8, 0.9, 1.0)], 0.01, 0.03, 0.5)
        # leather booth with button tufting, on the right
        bk = mix(P.accent_dark, P.ink, 0.15) if not dark else scale(P.accent, 0.5)
        S.rect(1.55, 0.44, 1.36, 0.40, scale(bk, 0.9), r=0.05, lift=0.12)
        for i in range(8):
            for j in range(3):
                bu, bv = 0.97 + i * 0.165 + (0.08 if j % 2 else 0.0), 0.32 + j * 0.1
                S.circle(bu, bv, 0.012, scale(bk, 0.55), lift=0, soft=1.5)
                S.soft(bu, bv + 0.03, 0.07, 0.05, mix(bk, WHITE, 0.25), 0.3, 1.2, add=False)
        S.rect(1.55, 0.62, 1.40, 0.07, scale(bk, 0.7), r=0.03, lift=0.1)
        S.glow(0.6, 0.12, 0.7, P.light, 0.18)
        for tu, tv in ((0.62, 0.575), (0.05, 0.585)):                                                     # distant tables with candles and chairs
            S.rect(tu, tv + 0.02, 0.012, 0.05, scale(P.ink, 2.0), lift=0.0)
            S.ellipse(tu, tv, 0.11, 0.022, mix(_cloth(P), WHITE, 0.2), lift=0.0)
            S.glow(tu + 0.02, tv - 0.03, 0.10, (1.0, 0.75, 0.4), 0.6)
            for dx in (-0.14, 0.14):
                S.rect(tu + dx, tv - 0.05, 0.05, 0.12, scale(bk, 0.7), r=0.012, lift=0.05)
        S.pendant(1.20, -0.1, 0.12, (1.0, 0.78, 0.46), 0.10)
        S.pendant(1.72, -0.1, 0.09, (1.0, 0.78, 0.46), 0.09)
        S.pendant(0.72, -0.1, 0.07, (1.0, 0.78, 0.46), 0.08)
        S.bokeh(10, 0.0, 0.05, 2.0, 0.45, [(1.0, 0.85, 0.55), (1.0, 0.7, 0.42)], 0.012, 0.04)
        S.floor(0.60, P.floor_top, P.floor_bot)
    cloth = _cloth(P)
    S.floor(0.60, cloth, scale(cloth, 0.84))                                                   # tablecloth over the whole table
    S.rect(1.0, 0.606, 14.0, 0.012, scale(cloth, 0.78), lift=0.0)
    for k in range(8):                                                                          # ironed creases fanning out in perspective
        x0 = -0.2 + k * 0.38 + rng.uniform(-0.05, 0.05)
        x1 = 1.05 + (x0 - 1.05) * 1.5
        S.line(x0, 0.64, x1, 1.0, 0.004, scale(cloth, 0.9), 0.4)
        if not dark:
            S.line(x0 + 0.012, 0.64, x1 + 0.02, 1.0, 0.003, mix(cloth, WHITE, 0.7), 0.5)
    for row in range(4):                                                                        # tone-on-tone damask motifs, shrinking towards the back
        vv = 0.66 + row * 0.04 + row * row * 0.012
        sc = 0.5 + (vv - 0.62) * 2.0
        for col in range(-6, 12):
            ux = 1.05 + (col + (0.5 if row % 2 else 0.0)) * 0.26 * sc
            S.ellipse(ux, vv, 0.020 * sc, 0.010 * sc, scale(cloth, 0.88), lift=0.0, alpha=0.7)
            S.ellipse(ux, vv, 0.008 * sc, 0.016 * sc, scale(cloth, 0.88), lift=0.0, alpha=0.7)
    S.soft(1.1, 0.84, 1.0, 0.22, P.light, 0.30 if not dark else 0.40, 1.4, add=True)
    S.soft(1.1, 0.70, 1.2, 0.07, (0, 0, 0), 0.10, 1.4)
    for k in range(36):                                                                                  # linen weave: short threads
        x, y = rng.uniform(-0.4, 2.6), rng.uniform(0.66, 1.1)
        if k % 2:
            S.line(x, y, x + rng.uniform(0.05, 0.12), y, 0.0016, scale(cloth, 0.9), 0.35)
        else:
            S.line(x, y, x, y + rng.uniform(0.02, 0.05), 0.0016, scale(cloth, 0.9), 0.35)
    S.soft(1.5, 0.84, 0.35, 0.14, (1.0, 0.72, 0.35), 0.26 if not dark else 0.5, 1.4, add=True)         # candle glow on the linen
    S.put("rest_wine_glass", 0.24, 0.80, 0.22, framed=False)                                           # an empty place beyond the text zone
    S.put("rest_vase", 0.74, 0.78, 0.30, color=mix(P.accent, (0.96, 0.25, 0.34), 0.55))
    S.put("rest_candle", 1.52, 0.75, 0.17)
    S.put("rest_wine_glass", 1.28, 0.79, 0.27)
    S.put("rest_setting", 1.06, 0.97, 0.34, color=mix(P.accent, WHITE, 0.1), subject=True)
    S.put("rest_wine_glass", 1.43, 0.86, 0.29)
    S.put("rest_bread", 0.79, 0.99, 0.14)
    S.focus("detail", 1.04, 0.82)
    with S.near(16.0):
        for dx, dy, r in ((0.0, 0.0, 0.07), (0.07, 0.03, 0.06), (-0.05, 0.04, 0.05)):
            S.circle(1.68 + dx, 1.02 + dy, r, mix(P.accent, (0.95, 0.2, 0.3), 0.4), lift=0.1)
        _near_leaf(S, 1.60, 1.0, 0.22, 40, (0.2, 0.45, 0.2))


# ---------------------------------------------------------------------------------------------- south indian
def _steel_bowl(c, u, v, r, food, kind="chutney", tl=0.46):
    """A small steel katori seen from above with a chutney / sambar / curry in it."""
    rng = c.rng
    soft_disc(c, u + r * 0.25, v - r * 0.2, r * 1.15, r * 0.55, BLACK, 0.40, 1.4)
    c.ellipse(u, v - r * 0.20, r, r * tl, (0.50, 0.52, 0.56), lift=0)
    c.ellipse(u, v - r * 0.06, r, r * tl, (0.74, 0.76, 0.80), lift=0.12)
    c.ellipse(u, v, r * 0.98, r * tl * 0.97, (0.93, 0.94, 0.96), lift=0.15)
    c.ellipse(u, v + r * 0.03, r * 0.85, r * tl * 0.83, (0.40, 0.42, 0.46), lift=0)
    c.ellipse(u, v + r * 0.07, r * 0.79, r * tl * 0.77, food, lift=0.12)
    if kind == "chutney":
        for _ in range(5):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.6
            c.ellipse(u + math.cos(a) * r * q, v + r * 0.08 + math.sin(a) * r * q * tl, r * 0.06, r * 0.035, mix(food, WHITE, 0.3), lift=0, alpha=0.7)
        craft.arc(c, u, v + r * 0.08, r * 0.35, r * 0.35 * tl, 30, 300, r * 0.05, (0.55, 0.30, 0.08), 0.55, 6)       # tempering
        for _ in range(4):
            c.ellipse(u + rng.uniform(-0.4, 0.4) * r, v + r * 0.09 + rng.uniform(-0.1, 0.1) * r, r * 0.04, r * 0.03, (0.15, 0.1, 0.05), lift=0)
    else:                                                                                     # sambar with drumstick / veg bits
        for _ in range(7):
            a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.6
            c.ellipse(u + math.cos(a) * r * q, v + r * 0.08 + math.sin(a) * r * q * tl, r * 0.09, r * 0.05,
                      rng.choice([(0.95, 0.55, 0.15), (0.45, 0.62, 0.2), (0.7, 0.3, 0.1)]), lift=0.1, alpha=0.9)
        c.ellipse(u + r * 0.1, v + r * 0.07, r * 0.28, r * 0.08, (1.0, 0.8, 0.35), lift=0, alpha=0.5)
    soft_disc(c, u - r * 0.35, v + r * 0.12, r * 0.35, r * 0.1, WHITE, 0.5, 1.1, add=True)


def _dosa(c, u, v, length, h):
    """A rolled paper dosa: a crisp golden cone lying along u (tip left, open end right), lacy lines, burnt spots."""
    rng = c.rng
    a, b = u - length / 2, u + length / 2
    hl, hr = h * 0.30, h * 0.52                                          # half heights at the tip and at the open end
    ya, yb = v + h * 0.42, v + h * 0.25                                  # centre line (rises towards the tip)
    soft_disc(c, u + 0.02, v - h * 0.10, length * 0.58, h * 0.55, BLACK, 0.42, 1.4)
    c.poly([(a, ya - hl), (b, yb - hr), (b, yb + hr), (a, ya + hl)], (0.52, 0.27, 0.08), lift=0.1)
    c.poly([(a, ya - hl * 0.8), (b, yb - hr * 0.8), (b, yb + hr * 0.86), (a, ya + hl * 0.9)], (0.84, 0.54, 0.18), lift=0.22)
    c.poly([(a + 0.05, ya + hl * 0.1), (b, yb + hr * 0.05), (b, yb + hr * 0.7), (a + 0.05, ya + hl * 0.72)], (0.96, 0.72, 0.30), lift=0.0, alpha=0.8)
    c.poly([(a + 0.08, ya + hl * 0.55), (b - 0.05, yb + hr * 0.42), (b - 0.05, yb + hr * 0.62), (a + 0.08, ya + hl * 0.78)], (1.0, 0.9, 0.6), lift=0.0, alpha=0.7)
    for k in range(22):                                                  # lacy crisp lines along the roll
        t = rng.random()
        x = a + (b - a) * t
        cy = ya + (yb - ya) * t
        hh = hl + (hr - hl) * t
        y = cy + rng.uniform(-0.85, 0.85) * hh
        c.line(x, y, x + rng.uniform(0.04, 0.14), y + rng.uniform(-0.01, 0.01), h * 0.04, (0.48, 0.24, 0.07), 0.42)
    for _ in range(16):
        t = rng.random()
        cy = ya + (yb - ya) * t
        hh = hl + (hr - hl) * t
        c.ellipse(a + (b - a) * t, cy + rng.uniform(-0.8, 0.8) * hh, h * 0.04, h * 0.028, (0.36, 0.16, 0.05), lift=0, alpha=0.75)
    c.ellipse(b, yb, h * 0.16, hr, (0.42, 0.21, 0.06), lift=0)                  # open end: rim and hollow
    c.ellipse(b - 0.004, yb, h * 0.12, hr * 0.84, (0.96, 0.80, 0.50), lift=0.15)
    c.ellipse(b - 0.002, yb, h * 0.06, hr * 0.55, (0.55, 0.30, 0.10), lift=0)
    c.ellipse(a, ya, h * 0.07, hl, (0.62, 0.34, 0.12), lift=0)
    soft_disc(c, u - length * 0.15, ya + h * 0.18, length * 0.32, h * 0.12, (1.0, 0.95, 0.7), 0.5, 1.2, add=True)


@sprop("south_dosa_leaf", aspect=3.0, fill=0.58)
def south_dosa_leaf(c, color):
    rng = c.rng
    g = (0.23, 0.50, 0.16)
    # banana leaf: dark edge, lit body, central rib, side veins, sheen
    _frect(c, -0.88, 0.03, 0.88, 0.56, scale(g, 0.55))
    for k in range(5):                                                                            # leaf body, lighter towards the back
        _frect(c, -0.86, 0.055 + k * 0.097, 0.86, 0.055 + (k + 1) * 0.097, scale(g, 1.08 - 0.07 * k))
    for k in range(15):
        x = -0.80 + k * 0.115
        c.line(x, 0.30, x - 0.08, 0.055, 0.007, scale(g, 0.72), 0.38)
        c.line(x, 0.30, x - 0.07, 0.53, 0.007, scale(g, 0.72), 0.34)
    c.line(-0.86, 0.295, 0.86, 0.30, 0.016, mix(g, (0.75, 0.9, 0.45), 0.35), 0.8)
    soft_disc(c, -0.4, 0.42, 0.7, 0.14, (0.8, 1.0, 0.5), 0.22, 1.3, add=True)
    # steel bowls at the back
    _steel_bowl(c, -0.60, 0.55, 0.13, (0.97, 0.96, 0.90))                                       # coconut chutney
    _steel_bowl(c, -0.31, 0.58, 0.13, (0.86, 0.22, 0.12))                                       # tomato chutney
    _steel_bowl(c, -0.02, 0.60, 0.13, (0.40, 0.62, 0.18))                                       # mint chutney
    _steel_bowl(c, 0.40, 0.56, 0.19, (0.80, 0.36, 0.10), "sambar")
    # potato masala and the dosa
    ru, rv = 0.60, 0.20
    soft_disc(c, ru + 0.03, rv - 0.02, 0.24, 0.08, BLACK, 0.35, 1.3)
    c.ellipse(ru, rv, 0.20, 0.10, (0.72, 0.52, 0.10), lift=0)
    c.ellipse(ru - 0.01, rv + 0.04, 0.18, 0.09, (0.98, 0.80, 0.22), lift=0.15)
    for _ in range(18):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        c.ellipse(ru + math.cos(a) * 0.15 * q, rv + 0.05 + math.sin(a) * 0.06 * q, 0.02, 0.012,
                  rng.choice([(1.0, 0.88, 0.3), (0.85, 0.62, 0.12), (0.45, 0.62, 0.15)]), lift=0.1)
    soft_disc(c, ru - 0.06, rv + 0.08, 0.09, 0.03, WHITE, 0.4, 1.1, add=True)
    _dosa(c, -0.22, 0.10, 1.12, 0.32)
    steam(c, -0.4, 0.38, 0.28, 0.04, 1, 0.10)
    # a curry leaf sprig on the leaf
    for k in range(5):
        leaf(c, 0.80, 0.12, 0.12, 20 + k * 30, (0.16, 0.40, 0.13), 0.45)
    c.ellipse(-0.82, 0.12, 0.03, 0.02, (0.85, 0.12, 0.08), lift=0.1)                              # dried red chilli


@sprop("south_idli_plate", aspect=1.75, fill=0.55)
def south_idli_plate(c, color):
    """Steel plate with a banana-leaf square under three plump idlis (they now stand out against green), vadas, sambar and chutney."""
    rng = c.rng
    c.ellipse(0.0, 0.03, 0.56, 0.56 * TILT, (0.36, 0.38, 0.42), lift=0)
    disc(c, 0.0, 0.055, 0.56, (0.66, 0.68, 0.72), TILT, 0.14)
    c.ellipse(0.0, 0.065, 0.45, 0.45 * TILT, (0.46, 0.48, 0.52), lift=0)
    c.ellipse(0.0, 0.07, 0.43, 0.43 * TILT, (0.74, 0.75, 0.78), lift=0.10)
    craft.arc(c, 0.0, 0.065, 0.50, 0.50 * TILT, 110, 190, 0.025, WHITE, 0.7, 8)
    # banana-leaf square under the food
    g = (0.22, 0.50, 0.15)
    c.poly([(-0.34, 0.075), (0.34, 0.075), (0.30, 0.255), (-0.30, 0.255)], scale(g, 0.55), lift=0.04)
    c.poly([(-0.325, 0.085), (0.325, 0.085), (0.285, 0.245), (-0.285, 0.245)], g, lift=0.16)
    c.line(-0.31, 0.165, 0.31, 0.165, 0.008, mix(g, (0.75, 0.9, 0.45), 0.35), 0.8)
    for k in range(7):
        c.line(-0.27 + k * 0.09, 0.165, -0.30 + k * 0.09, 0.09, 0.004, scale(g, 0.7), 0.4)
    # three idlis, warm cream with a lit dome and a shaded side
    for x, y in ((-0.17, 0.13), (0.15, 0.13), (-0.01, 0.20)):
        soft_disc(c, x + 0.05, y - 0.01, 0.19, 0.05, BLACK, 0.38, 1.3)
        c.ellipse(x, y + 0.02, 0.15, 0.072, (0.70, 0.62, 0.46), lift=0)
        c.poly([(x - 0.14, y + 0.03), (x + 0.14, y + 0.03), (x + 0.10, y + 0.12), (x - 0.10, y + 0.12)], (0.95, 0.89, 0.74), lift=0.1)
        c.poly([(x + 0.03, y + 0.03), (x + 0.14, y + 0.03), (x + 0.10, y + 0.12), (x + 0.02, y + 0.12)], (0.62, 0.52, 0.36), lift=0, alpha=0.4)
        c.ellipse(x, y + 0.13, 0.10, 0.04, (1.0, 0.97, 0.88), lift=0.1)
        c.ellipse(x - 0.006, y + 0.127, 0.085, 0.032, (1.0, 0.99, 0.94), lift=0)
        soft_disc(c, x - 0.05, y + 0.14, 0.06, 0.02, WHITE, 0.6, 1.1, add=True)
        for _ in range(3):
            c.ellipse(x + rng.uniform(-0.07, 0.07), y + 0.125 + rng.uniform(-0.01, 0.015), 0.005, 0.003, (0.86, 0.78, 0.62), lift=0, alpha=0.8)
    # gunpowder (podi) and a ghee shine on the front idli
    c.ellipse(0.0, 0.158, 0.05, 0.016, (0.55, 0.14, 0.05), lift=0, alpha=0.85)
    c.ellipse(0.0, 0.160, 0.03, 0.009, (0.30, 0.07, 0.03), lift=0, alpha=0.8)
    c.ellipse(-0.01, 0.245, 0.06, 0.016, (1.0, 0.85, 0.35), lift=0.1, alpha=0.7)
    # medu vada on the plate
    for x, y in ((0.36, 0.10), (0.44, 0.15)):
        soft_disc(c, x + 0.03, y - 0.02, 0.12, 0.04, BLACK, 0.3, 1.3)
        c.ellipse(x, y, 0.12, 0.055, (0.45, 0.22, 0.06), lift=0)
        c.ellipse(x - 0.004, y + 0.016, 0.115, 0.05, (0.88, 0.58, 0.20), lift=0.2)
        c.ellipse(x, y + 0.02, 0.04, 0.018, (0.30, 0.14, 0.04), lift=0)
        c.ellipse(x, y + 0.023, 0.028, 0.012, (0.62, 0.32, 0.10), lift=0)
        for _ in range(5):
            c.ellipse(x + rng.uniform(-0.1, 0.1), y + 0.02 + rng.uniform(-0.02, 0.025), 0.007, 0.004, (0.55, 0.28, 0.08), lift=0, alpha=0.8)
        soft_disc(c, x - 0.04, y + 0.04, 0.05, 0.015, (1.0, 0.9, 0.55), 0.6, 1.1, add=True)
    _steel_bowl(c, -0.50, 0.25, 0.13, (0.82, 0.38, 0.10), "sambar")
    _steel_bowl(c, -0.36, 0.30, 0.09, (0.97, 0.96, 0.90))
    steam(c, 0.0, 0.32, 0.3, 0.04, 1, 0.14)


@sprop("south_coffee", aspect=1.0, fill=0.85)
def south_coffee(c, color):
    ao(c, 0.0, 0.0, 0.85, 0.22)
    # davara: wide shallow steel dish
    c.ellipse(0.0, 0.03, 0.46, 0.46 * TILT, (0.45, 0.47, 0.51), lift=0)
    disc(c, 0.0, 0.07, 0.46, (0.80, 0.82, 0.86), TILT, 0.14)
    c.ellipse(0.0, 0.09, 0.38, 0.38 * TILT, (0.52, 0.34, 0.20), lift=0)
    c.ellipse(0.0, 0.092, 0.355, 0.355 * TILT, (0.34, 0.18, 0.09), lift=0.1)
    # tumbler
    left, right = (0.96, 0.97, 0.99), (0.48, 0.50, 0.55)
    c.ellipse(0.0, 0.10, 0.215, 0.215 * TILT, scale(right, 0.8), lift=0)
    c.poly([(-0.29, 0.78), (0.29, 0.78), (0.215, 0.11), (-0.215, 0.11)], mix(left, right, 0.4), lift=0.05)
    for x0, al in ((0.02, 0.10), (0.08, 0.14), (0.14, 0.2), (0.20, 0.24)):
        c.poly([(x0, 0.78), (0.29, 0.78), (0.215, 0.11), (x0 * 0.72, 0.11)], (0.12, 0.13, 0.18), lift=0, alpha=al)
    c.poly([(-0.25, 0.75), (-0.17, 0.75), (-0.12, 0.14), (-0.17, 0.14)], WHITE, lift=0, alpha=0.7)
    c.poly([(-0.06, 0.75), (-0.03, 0.75), (-0.01, 0.14), (-0.04, 0.14)], WHITE, lift=0, alpha=0.22)
    for v in (0.30, 0.55):
        c.line(-0.26 + (v - 0.5) * 0.1, v, 0.26 - (v - 0.5) * 0.1, v, 0.01, (0.35, 0.37, 0.42), 0.4)
    c.ellipse(0.0, 0.78, 0.29, 0.29 * TILT, (0.55, 0.57, 0.62), lift=0)
    c.ellipse(0.0, 0.785, 0.275, 0.275 * TILT, (0.88, 0.90, 0.93), lift=0.1)
    c.ellipse(0.0, 0.78, 0.24, 0.24 * TILT, (0.30, 0.17, 0.08), lift=0)
    c.ellipse(0.0, 0.775, 0.225, 0.225 * TILT, (0.62, 0.40, 0.20), lift=0.1)
    c.ellipse(0.0, 0.775, 0.17, 0.17 * TILT, (0.88, 0.76, 0.58), lift=0.06, alpha=0.9)
    for _ in range(14):
        c.ellipse(c.rng.uniform(-0.17, 0.17), 0.775 + c.rng.uniform(-0.05, 0.05), 0.014, 0.009, (0.97, 0.9, 0.78), lift=0.1, alpha=0.8)
    gloss(c, -0.1, 0.8, 0.1, 0.02, 6, 0.5)
    steam(c, 0.0, 0.86, 0.34, 0.05, 1, 0.17)


@sprop("south_lamp", aspect=0.5, fill=1.0)
def south_lamp(c, color):
    """A brass kuthuvilakku (traditional lamp), lit."""
    ao(c, 0.0, 0.0, 0.45, 0.08)
    left, right = (1.0, 0.86, 0.42), (0.58, 0.38, 0.12)
    c.ellipse(0.0, 0.03, 0.2, 0.2 * TILT, scale(right, 0.8), lift=0)
    craft.hshade_box(c, 0.0, 0.10, 0.34, 0.12, left, right, r=0.04)
    craft.hshade_box(c, 0.0, 0.40, 0.07, 0.5, left, right)
    for v, r in ((0.22, 0.09), (0.38, 0.075), (0.55, 0.09), (0.70, 0.075)):
        c.ellipse(0.0, v, r, r * 0.55, left, lift=0.15)
        c.ellipse(0.0, v - 0.015, r, r * 0.5, scale(right, 0.9), lift=0, alpha=0.7)
    c.ellipse(0.0, 0.78, 0.26, 0.26 * 0.45, scale(right, 0.8), lift=0)
    c.ellipse(0.0, 0.795, 0.25, 0.25 * 0.42, left, lift=0.1)
    c.ellipse(0.0, 0.80, 0.19, 0.19 * 0.4, (0.35, 0.2, 0.06), lift=0)
    soft_disc(c, 0.0, 0.93, 0.7, 0.7, (1.0, 0.7, 0.25), 0.55, 2.2, add=True)
    c.poly([(-0.03, 0.82), (0.03, 0.82), (0.0, 0.96)], (1.0, 0.72, 0.2), lift=0.1)
    c.poly([(-0.015, 0.825), (0.015, 0.825), (0.0, 0.91)], (1.0, 0.97, 0.75), lift=0, alpha=0.9)


@niche("south-indian", "South Indian restaurant", subjects=("south_dosa_leaf",),
       strong=("south indian", "south indian restaurant", "dosa", "idli", "idly", "sambar", "udupi", "filter coffee", "vada", "uttapam", "masala dosa",
               "idli dosa", "डोसा", "इडली", "सांभर", "साउथ इंडियन", "उडुपी", "डोसा कॉर्नर"),
       weak=("chutney", "uttapam", "medu vada", "banana leaf", "tiffin", "filter kaapi", "madras", "kerala", "bhavan"),
       accent="#ef6c00", mood="warm", group="food", avoid=("pizza", "sushi", "chinese"))
def south_indian(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        S.rect(1.0, 0.50, 14.0, 0.25, mix(scale(P.wall_bot, 0.8), (0.36, 0.62, 0.34), 0.55 if not dark else 0.4), lift=0.0)   # painted dado
        S.rect(1.0, 0.375, 14.0, 0.014, scale(P.accent_light, 0.95 if not dark else 0.6), lift=0.0)
        for k in range(-20, 30):                                                                         # kolam-like border dots above the dado
            S.circle(-4.0 + k * 0.28, 0.355, 0.012, scale(P.accent_light, 0.9 if not dark else 0.6), lift=0, soft=1.5)
        # window with tropical greenery
        S.rect(0.40, 0.22, 0.52, 0.44, scale(P.ink, 2.4 if not dark else 1.4), lift=0.0)
        S.gradient_rect(0.16, 0.03, 0.64, 0.41, (0.45, 0.70, 0.30), (0.88, 0.95, 0.60))
        for _ in range(9):
            S.ellipse(rng.uniform(0.18, 0.62), rng.uniform(0.06, 0.38), 0.06, 0.02, (0.12, 0.36, 0.12), angle=rng.uniform(-60, 60), alpha=0.7)
        S.rect(0.40, 0.22, 0.012, 0.40, scale(P.ink, 2.4 if not dark else 1.4), lift=0.0)
        S.glow(0.40, 0.22, 0.8, P.light, 0.35)
        # hanging marigold garlands
        for u in (0.95, 1.30, 1.72):
            ln = 0.24 + 0.08 * ((int(u * 10)) % 3)
            for k in range(int(ln / 0.03)):
                S.circle(u, -0.02 + k * 0.03, 0.017, (0.98, 0.58 - 0.05 * (k % 2), 0.08), lift=0.1, soft=1.5)
        S.pendant(1.10, -0.1, 0.18, (1.0, 0.75, 0.4), 0.11)
        S.pendant(1.55, -0.1, 0.12, (1.0, 0.75, 0.4), 0.09)
        S.rect(1.50, 0.26, 0.45, 0.16, scale(P.ink, 2.2), r=0.01, lift=0.05)                              # menu board
        for k in range(5):
            S.rect(1.40 + (k % 2) * 0.02, 0.21 + k * 0.026, 0.20 - (k % 3) * 0.03, 0.007, (0.95, 0.92, 0.85), lift=0.0, alpha=0.7)
        S.bokeh(10, -0.2, 0.05, 2.2, 0.5, [(1.0, 0.85, 0.5), (1.0, 0.7, 0.3), (0.7, 0.9, 0.4)], 0.012, 0.04, 0.4)
        S.floor(0.60, P.floor_top, P.floor_bot)
    top = scale(mix(P.surface, (0.86, 0.60, 0.34), 0.35), 0.95) if not dark else scale(P.surface, 0.5)
    S.floor(1.35, scale(top, 0.84), scale(top, 0.62))
    S.wood(-1.6, 0.60, 3.8, 1.45, top, plank=0.10, grain=0.30)                                          # teak planks with seams and grain
    S.rect(1.0, 0.606, 14.0, 0.010, scale(top, 0.45), lift=0.0)
    S.soft(1.05, 0.84, 0.85, 0.22, (1.0, 0.82, 0.55), 0.30 if not dark else 0.46, 1.5, add=True)
    # madras-check cotton mat under the food: cream cloth, accent and green bands, a darker hem
    ml, mr, mv0, mv1 = 0.40, 2.00, 0.68, 1.12
    cream = scale((0.96, 0.90, 0.76), 1.0 if not dark else 0.5)
    band = scale(P.accent, 1.0 if not dark else 0.55)
    gre = scale((0.18, 0.46, 0.26), 1.0 if not dark else 0.6)
    S.rect((ml + mr) / 2, (mv0 + mv1) / 2 + 0.006, mr - ml + 0.02, mv1 - mv0 + 0.02, scale(cream, 0.55), lift=0.0, alpha=0.85)
    S.rect((ml + mr) / 2, (mv0 + mv1) / 2, mr - ml, mv1 - mv0, cream, lift=0.0)
    for i in range(16):
        x = ml + 0.05 + i * (mr - ml - 0.1) / 16.0
        if i % 3 == 0:
            S.rect(x, (mv0 + mv1) / 2, 0.05, mv1 - mv0, band, lift=0.0, alpha=0.55)
        elif i % 3 == 1:
            S.rect(x, (mv0 + mv1) / 2, 0.022, mv1 - mv0, gre, lift=0.0, alpha=0.45)
    for j in range(6):
        y = mv0 + 0.03 + j * (mv1 - mv0 - 0.04) / 6.0
        if j % 2 == 0:
            S.rect((ml + mr) / 2, y, mr - ml, 0.034, band, lift=0.0, alpha=0.5)
        else:
            S.rect((ml + mr) / 2, y, mr - ml, 0.014, gre, lift=0.0, alpha=0.42)
    S.rect((ml + mr) / 2, mv0 + 0.004, mr - ml, 0.008, scale(cream, 0.7), lift=0.0)
    S.put("south_lamp", 0.34, 0.80, 0.36, framed=False)
    S.put("south_coffee", 1.46, 0.85, 0.22)
    S.put("south_dosa_leaf", 1.02, 0.92, 0.31, subject=True)
    S.put("south_idli_plate", 1.31, 1.00, 0.25)
    S.focus("detail", 1.02, 0.76)
    with S.near(16.0):
        for k in range(2):
            _near_leaf(S, 1.64 + k * 0.05, 1.04, 0.28, 100 + k * 34, (0.18, 0.46, 0.16), 0.38)
        S.soft(0.42, 1.02, 0.08, 0.08, (0.98, 0.58, 0.10), 0.7, 1.0)


# ---------------------------------------------------------------------------------------------- chinese restaurant
def _noodle_strands(c, cu, cv, a, b, n, cols, lift_to=0.0, rng=None):
    rng = rng or c.rng
    for _ in range(n):
        ang, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        x, y = cu + math.cos(ang) * a * q, cv + math.sin(ang) * b * q + (1 - q) * lift_to
        craft.strand(c, x - 0.05, y, rng.uniform(0.12, 0.24), rng.uniform(-30, 210), 0.016, cols[rng.randrange(len(cols))], 0.97, 0.9)


@sprop("chinese_noodle_bowl", aspect=1.75, fill=0.90)
def chinese_noodle_bowl(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.1, 0.26)
    red = (0.78, 0.12, 0.10)
    white = (0.97, 0.95, 0.90)
    # porcelain bowl: foot, tapering body with a red band and gold dots, rim
    o = 0.10
    c.ellipse(0.0, 0.03, 0.25, 0.25 * 0.36, scale(white, 0.55), lift=0)
    c.rect(0.0, 0.07, 0.34, 0.07, scale(white, 0.8), r=0.02, lift=0.1)
    c.ellipse(0.0, 0.10, 0.36, 0.36 * 0.40, scale(white, 0.6), lift=0)
    body = [(-0.53, 0.35 + o), (0.53, 0.35 + o), (0.48, 0.28 + o * 0.4), (0.36, 0.17), (0.18, 0.10), (-0.18, 0.10), (-0.36, 0.17), (-0.48, 0.28 + o * 0.4)]
    c.poly(body, scale(white, 0.9), lift=0.12)
    c.poly([(0.10, 0.35 + o), (0.53, 0.35 + o), (0.48, 0.28 + o * 0.4), (0.36, 0.17), (0.18, 0.10), (0.04, 0.10)], (0.30, 0.22, 0.15), lift=0, alpha=0.30)
    c.poly([(0.30, 0.35 + o), (0.53, 0.35 + o), (0.48, 0.28 + o * 0.4), (0.36, 0.17), (0.26, 0.11)], (0.25, 0.15, 0.1), lift=0, alpha=0.25)
    c.poly([(-0.525, 0.36), (0.525, 0.36), (0.50, 0.29), (-0.50, 0.29)], red, lift=0.1, alpha=0.96)
    c.poly([(0.10, 0.36), (0.525, 0.36), (0.50, 0.29), (0.10, 0.29)], BLACK, lift=0, alpha=0.22)
    for k in range(10):
        x = -0.43 + k * 0.095
        c.ellipse(x, 0.325, 0.018, 0.012, (0.98, 0.80, 0.30), lift=0.12)
    for k in range(5):                                                                  # lotus petal pattern on the lower body
        x = -0.26 + k * 0.13
        c.ellipse(x, 0.20, 0.045, 0.06, red, lift=0, alpha=0.55)
    c.poly([(-0.50, 0.42), (-0.43, 0.42), (-0.33, 0.14), (-0.38, 0.17)], WHITE, lift=0, alpha=0.5)
    disc(c, 0.0, 0.35 + o, 0.53, white, 0.40, 0.04, rim=True)
    craft.arc(c, 0.0, 0.352 + o, 0.50, 0.50 * 0.40, 195, 345, 0.012, (0.95, 0.76, 0.3), 0.9, 8)
    c.ellipse(0.0, 0.355 + o, 0.46, 0.46 * 0.40, (0.40, 0.24, 0.08), lift=0)
    # heaped hakka noodles with vegetables
    c.ellipse(0.0, 0.40 + o, 0.43, 0.24, (0.56, 0.34, 0.11), lift=0)
    c.ellipse(0.0, 0.45 + o, 0.38, 0.24, (0.74, 0.50, 0.18), lift=0.1)
    c.ellipse(-0.01, 0.52 + o, 0.28, 0.17, (0.90, 0.66, 0.28), lift=0.1)
    _noodle_strands(c, -0.02, 0.47 + o, 0.34, 0.19, 105, [(0.96, 0.78, 0.34), (0.90, 0.66, 0.26), (0.80, 0.55, 0.20), (0.99, 0.88, 0.5), (0.88, 0.62, 0.22)], 0.10)
    for _ in range(11):                                                                     # capsicum / carrot strips
        x, y = rng.uniform(-0.30, 0.30), rng.uniform(0.44 + o, 0.64 + o)
        col = rng.choice([(0.82, 0.16, 0.10), (0.95, 0.5, 0.1), (0.25, 0.6, 0.18), (0.82, 0.16, 0.10)])
        a = rng.uniform(-60, 60)
        c.line(x, y, x + 0.07 * math.cos(math.radians(a)), y + 0.04 * math.sin(math.radians(a)), 0.026, scale(col, 0.7))
        c.line(x, y + 0.006, x + 0.07 * math.cos(math.radians(a)), y + 0.006 + 0.04 * math.sin(math.radians(a)), 0.018, col)
    for _ in range(16):                                                                     # spring onion rings
        x, y = rng.uniform(-0.28, 0.28), rng.uniform(0.44 + o, 0.68 + o)
        c.ellipse(x, y, 0.017, 0.011, (0.35, 0.68, 0.2), lift=0.1)
        c.ellipse(x, y, 0.008, 0.005, (0.85, 0.95, 0.6), lift=0)
    for _ in range(6):                                                                      # sesame
        c.ellipse(rng.uniform(-0.22, 0.22), rng.uniform(0.5 + o, 0.68 + o), 0.007, 0.004, (0.98, 0.95, 0.85), lift=0)
    gloss(c, -0.12, 0.64 + o, 0.12, 0.04, 8, 0.5)
    soft_disc(c, 0.14, 0.50 + o, 0.3, 0.12, (0.3, 0.12, 0.03), 0.28, 1.2)
    # chopsticks resting on the rim and lifting into the noodles
    for dx, dy, col in ((0.0, 0.0, (0.28, 0.10, 0.06)), (0.06, 0.012, (0.34, 0.12, 0.06))):
        c.line(0.18 + dx, 0.76 + dy, 0.78 + dx, 0.40 + dy, 0.024, scale(col, 0.6))
        c.line(0.18 + dx, 0.764 + dy, 0.78 + dx, 0.404 + dy, 0.017, col)
        c.line(0.60 + dx, 0.51 + dy, 0.78 + dx, 0.40 + dy, 0.0225, (0.85, 0.70, 0.28), 0.9)
    c.line(0.14, 0.79, 0.4, 0.645, 0.006, (0.75, 0.55, 0.45), 0.5)
    steam(c, -0.03, 0.82, 0.45, 0.07, 2, 0.20)


@sprop("chinese_steamer", aspect=1.02, fill=0.95)
def chinese_steamer(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.24)
    bam_l, bam_r = (0.90, 0.72, 0.42), (0.52, 0.36, 0.16)
    # saucer of chilli oil at the side
    # bottom tier
    c.ellipse(0.0, 0.03, 0.45, 0.45 * TILT, scale(bam_r, 0.7), lift=0)
    craft.hshade_box(c, 0.0, 0.17, 0.90, 0.30, bam_l, bam_r)
    for v in (0.07, 0.17, 0.27):
        c.line(-0.44, v, 0.44, v, 0.012, scale(bam_r, 0.8), 0.55)
    for k in range(10):
        x = -0.40 + k * 0.09
        c.line(x, 0.02, x + 0.01, 0.32, 0.005, scale(bam_r, 0.85), 0.3)
    c.poly([(-0.43, 0.31), (-0.36, 0.31), (-0.35, 0.04), (-0.40, 0.04)], WHITE, lift=0, alpha=0.30)
    c.ellipse(0.0, 0.32, 0.45, 0.45 * TILT, scale(bam_r, 0.75), lift=0)
    # middle tier
    craft.hshade_box(c, 0.0, 0.45, 0.90, 0.26, bam_l, bam_r)
    for v in (0.37, 0.46, 0.55):
        c.line(-0.44, v, 0.44, v, 0.012, scale(bam_r, 0.8), 0.55)
    c.poly([(-0.43, 0.57), (-0.36, 0.57), (-0.35, 0.34), (-0.40, 0.34)], WHITE, lift=0, alpha=0.30)
    c.ellipse(0.0, 0.58, 0.45, 0.45 * TILT, scale(bam_r, 0.75), lift=0)
    # open top tier with momos on a paper liner
    craft.hshade_box(c, 0.0, 0.69, 0.90, 0.22, bam_l, bam_r)
    for v in (0.62, 0.70, 0.78):
        c.line(-0.44, v, 0.44, v, 0.012, scale(bam_r, 0.8), 0.55)
    c.ellipse(0.0, 0.80, 0.45, 0.45 * TILT, scale(bam_r, 0.7), lift=0)
    c.ellipse(0.0, 0.803, 0.43, 0.43 * TILT, (0.96, 0.88, 0.70), lift=0.05)
    c.ellipse(0.0, 0.81, 0.37, 0.37 * TILT, (0.99, 0.97, 0.90), lift=0.05)
    for k, (x, y) in enumerate(((-0.17, 0.80), (0.03, 0.78), (0.20, 0.81), (-0.06, 0.88), (0.12, 0.89))):
        soft_disc(c, x + 0.03, y - 0.015, 0.10, 0.035, BLACK, 0.3, 1.3)
        c.ellipse(x, y, 0.095, 0.058, (0.84, 0.80, 0.72), lift=0)
        c.ellipse(x - 0.004, y + 0.018, 0.088, 0.05, (0.99, 0.97, 0.92), lift=0.1)
        for p in range(7):                                                                    # pleats
            a = -0.9 + p * 0.3
            c.line(x + math.sin(a) * 0.02, y + 0.012, x + math.sin(a) * 0.07, y + 0.05, 0.007, (0.80, 0.76, 0.68), 0.7)
        c.ellipse(x - 0.002, y + 0.052, 0.012, 0.008, (0.9, 0.86, 0.78), lift=0)
        soft_disc(c, x - 0.03, y + 0.04, 0.04, 0.014, WHITE, 0.6, 1.1, add=True)
    steam(c, 0.0, 0.93, 0.4, 0.07, 2, 0.20)


@sprop("chinese_wok", aspect=3.0, fill=0.52)
def chinese_wok(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.34)
    iron = (0.16, 0.16, 0.18)
    # wooden handle to the right, trivet
    c.line(0.50, 0.24, 1.18, 0.30, 0.07, (0.30, 0.18, 0.10))
    c.line(0.50, 0.255, 1.18, 0.315, 0.04, (0.62, 0.40, 0.22))
    c.line(0.56, 0.20, 0.50, 0.24, 0.12, scale(iron, 0.9))
    c.ellipse(0.0, 0.02, 0.50, 0.50 * 0.34, (0.30, 0.30, 0.33), lift=0)
    # outer wall: dark iron, shaded
    c.poly([(-0.78, 0.38), (0.78, 0.38), (0.55, 0.12), (0.2, 0.05), (-0.2, 0.05), (-0.55, 0.12)], iron, lift=0.1)
    c.poly([(0.0, 0.38), (0.78, 0.38), (0.55, 0.12), (0.2, 0.05), (0.0, 0.05)], BLACK, lift=0, alpha=0.35)
    c.poly([(-0.74, 0.34), (-0.60, 0.34), (-0.48, 0.13), (-0.56, 0.13)], WHITE, lift=0, alpha=0.18)
    disc(c, 0.0, 0.38, 0.78, (0.36, 0.36, 0.40), 0.40, 0.06, rim=True)
    c.ellipse(0.0, 0.385, 0.72, 0.72 * 0.40, (0.06, 0.05, 0.05), lift=0)
    c.ellipse(0.0, 0.395, 0.66, 0.66 * 0.38, (0.28, 0.12, 0.05), lift=0.1)
    # stir fry: gobi manchurian balls in glossy sauce, capsicum, onion, red chillies, spring onion
    for _ in range(11):
        x, y = rng.uniform(-0.50, 0.50), rng.uniform(0.34, 0.50)
        _ball(c, x, y, rng.uniform(0.06, 0.09), (0.50, 0.20, 0.07), 0.8, 0.5, 0.45)
    for _ in range(10):
        x, y = rng.uniform(-0.55, 0.55), rng.uniform(0.34, 0.5)
        col = rng.choice([(0.25, 0.6, 0.18), (0.85, 0.15, 0.1), (0.95, 0.55, 0.15), (0.92, 0.88, 0.6)])
        c.rect(x, y, 0.07, 0.04, col, r=0.01, lift=0.15)
    for _ in range(8):
        c.ellipse(rng.uniform(-0.5, 0.5), rng.uniform(0.35, 0.5), 0.016, 0.01, (0.35, 0.7, 0.2), lift=0.1)
    for _ in range(4):
        x, y = rng.uniform(-0.4, 0.4), rng.uniform(0.38, 0.5)
        c.line(x, y, x + 0.09, y + 0.02, 0.016, (0.75, 0.08, 0.06))
    soft_disc(c, -0.18, 0.5, 0.4, 0.08, (1.0, 0.8, 0.5), 0.35, 1.2, add=True)
    gloss(c, -0.12, 0.47, 0.06, 0.02, 8, 0.5)
    c.line(-0.70, 0.40, -0.80, 0.42, 0.05, iron)
    steam(c, 0.0, 0.58, 0.44, 0.09, 2, 0.18)


@sprop("chinese_tea", aspect=1.6, fill=0.62)
def chinese_tea(c, color):
    ao(c, 0.0, 0.0, 1.1, 0.30)
    # cups without handles
    for u, v in ((0.38, 0.06), (0.66, 0.02)):
        c.ellipse(u, v + 0.0, 0.17, 0.17 * TILT, (0.7, 0.68, 0.64), lift=0)
        c.poly([(u - 0.15, 0.20 + v), (u + 0.15, 0.20 + v), (u + 0.09, 0.05 + v), (u - 0.09, 0.05 + v)], (0.97, 0.96, 0.93), lift=0.08)
        c.poly([(u + 0.04, 0.20 + v), (u + 0.15, 0.20 + v), (u + 0.09, 0.05 + v), (u + 0.02, 0.05 + v)], BLACK, lift=0, alpha=0.2)
        c.poly([(u - 0.15, 0.20 + v), (u + 0.15, 0.20 + v), (u + 0.13, 0.16 + v), (u - 0.14, 0.16 + v)], (0.78, 0.12, 0.10), lift=0.1)
        c.ellipse(u, 0.205 + v, 0.15, 0.15 * 0.4, (0.9, 0.9, 0.86), lift=0)
        c.ellipse(u, 0.20 + v, 0.125, 0.125 * 0.4, (0.60, 0.40, 0.10), lift=0.1)
        gloss(c, u - 0.04, 0.215 + v, 0.04, 0.012, 0, 0.5)
    # teapot: round body, spout, lid with knob, bamboo-wrapped handle
    tp = (0.16, 0.14, 0.13)
    c.ellipse(-0.30, 0.03, 0.30, 0.30 * TILT, scale(tp, 0.7), lift=0)
    c.ellipse(-0.30, 0.30, 0.31, 0.27, scale(tp, 0.6), lift=0)
    c.ellipse(-0.31, 0.31, 0.29, 0.25, (0.30, 0.22, 0.20), lift=0.2)
    soft_disc(c, -0.20, 0.20, 0.25, 0.14, BLACK, 0.4, 1.3)
    soft_disc(c, -0.42, 0.40, 0.14, 0.09, (1.0, 0.85, 0.7), 0.45, 1.2, add=True)
    craft.arc(c, -0.30, 0.30, 0.22, 0.2, 20, 160, 0.015, BRASS, 0.8, 8)
    c.poly([(0.0, 0.25), (0.24, 0.40), (0.24, 0.43), (-0.01, 0.34)], scale(tp, 0.9), lift=0.1)
    c.ellipse(-0.30, 0.55, 0.15, 0.15 * 0.42, scale(tp, 0.8), lift=0)
    c.ellipse(-0.30, 0.555, 0.13, 0.13 * 0.4, (0.34, 0.24, 0.22), lift=0.12)
    c.circle(-0.30, 0.60, 0.04, BRASS, lift=0.2)
    craft.arc(c, -0.62, 0.32, 0.12, 0.2, 90, 270, 0.035, (0.7, 0.5, 0.25), 1.0, 8)
    craft.arc(c, -0.62, 0.32, 0.12, 0.2, 100, 260, 0.012, (0.95, 0.8, 0.5), 0.8, 8)
    steam(c, -0.30, 0.66, 0.22, 0.04, 1, 0.14)


def _lantern(S, u, v, r, red, cord_to=-0.12, h=None):
    """A red paper lantern with gold caps, ribs, a tassel and a warm glow (use in the far layer)."""
    h = h or r * 1.25
    S.line(u, cord_to, u, v - h, 0.0035, (0.35, 0.25, 0.12))
    S.glow(u, v, r * 3.4, (1.0, 0.45, 0.2), 0.55)
    S.ellipse(u, v, r, h, scale(red, 0.9), lift=0.1)
    S.soft(u, v, r * 0.62, h * 0.8, mix(red, (1.0, 0.7, 0.3), 0.55), 0.7, 1.2, add=True)
    for k in (-0.55, 0.0, 0.55):
        S.line(u + r * k * 0.95, v - h * 0.88, u + r * k * 0.7, v + h * 0.88, r * 0.035, scale(red, 0.55), 0.55)
    S.rect(u, v - h * 0.96, r * 0.7, r * 0.15, BRASS, lift=0.1)
    S.rect(u, v + h * 0.96, r * 0.7, r * 0.15, BRASS, lift=0.1)
    S.line(u, v + h, u, v + h + r * 0.9, r * 0.03, (0.95, 0.75, 0.25))
    S.ellipse(u, v + h + r * 0.95, r * 0.12, r * 0.2, (0.95, 0.75, 0.25), lift=0.1)


@niche("chinese-restaurant", "Chinese / Indo-Chinese restaurant", subjects=("chinese_noodle_bowl",),
       strong=("chinese restaurant", "indo chinese", "indo-chinese", "chinese food", "noodles", "momos", "manchurian", "hakka noodles", "dim sum",
               "chowmein", "chinese corner", "chinese cuisine", "चाइनीज़", "चाइनीज", "मोमोज", "नूडल्स", "मंचूरियन", "चाउमीन"),
       weak=("chopsticks", "wok", "fried rice", "schezwan", "hakka", "dumplings", "soup", "manchow", "chilli paneer"),
       accent="#c62828", mood="dark", group="food", avoid=("sushi", "japanese", "italian"))
def chinese_restaurant(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    gold = (0.95, 0.74, 0.30) if not dark else (0.85, 0.62, 0.22)
    red = mix(P.accent, (0.92, 0.12, 0.10), 0.35)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        panel = scale(P.accent_dark, 0.8) if not dark else scale(P.accent_dark, 0.7)
        S.rect(1.0, 0.30, 14.0, 0.62, panel, lift=0.0)                                                   # lacquered red wall panel
        S.rect(1.0, 0.015, 14.0, 0.02, gold, lift=0.0)
        S.rect(1.0, 0.585, 14.0, 0.03, gold, lift=0.0)
        # gold lattice window
        S.rect(0.55, 0.30, 0.72, 0.46, scale(panel, 0.5), lift=0.0)
        S.glow(0.55, 0.30, 0.9, (1.0, 0.7, 0.35), 0.25)
        for i in range(-4, 5):
            S.line(0.55 + i * 0.075, 0.08, 0.55 + i * 0.075, 0.52, 0.006, gold, 0.9)
        for j in range(-3, 4):
            S.line(0.19, 0.30 + j * 0.065, 0.91, 0.30 + j * 0.065, 0.006, gold, 0.9)
        S.rect(0.55, 0.30, 0.74, 0.012, gold, lift=0.0)
        # circular moon window on the right
        S.circle(1.78, 0.30, 0.20, gold, lift=0.0)
        S.circle(1.78, 0.30, 0.18, mix(P.accent_dark, (0.1, 0.05, 0.05), 0.5), lift=0.0)
        S.glow(1.78, 0.30, 0.5, (1.0, 0.7, 0.3), 0.3)
        for k in range(8):
            S.line(1.78 + 0.18 * math.cos(k * 0.785), 0.30 + 0.18 * math.sin(k * 0.785), 1.78 - 0.18 * math.cos(k * 0.785), 0.30 - 0.18 * math.sin(k * 0.785), 0.006, gold, 0.8)
        # lanterns
        for u, v, r in ((0.15, 0.10, 0.055), (0.95, 0.16, 0.075), (1.30, 0.07, 0.05), (1.55, 0.18, 0.085), (2.0, 0.08, 0.05), (0.38, 0.06, 0.04)):
            _lantern(S, u, v, r, red)
        S.bokeh(8, -0.2, 0.05, 2.2, 0.5, [(1.0, 0.7, 0.3), (1.0, 0.4, 0.2), (1.0, 0.85, 0.5)], 0.012, 0.04, 0.4)
        S.floor(0.60, P.floor_top, P.floor_bot)
    lac = mix(P.surface, P.accent_dark, 0.55) if not dark else mix(scale(P.surface, 0.5), P.accent_dark, 0.5)
    lac = scale(lac, 0.62 if not dark else 0.55)
    S.floor(0.60, lac, scale(lac, 0.55))
    S.rect(1.0, 0.606, 14.0, 0.012, gold, lift=0.0)
    S.soft(0.95, 0.80, 1.2, 0.2, (1.0, 0.5, 0.22), 0.30 if not dark else 0.5, 1.4, add=True)
    for k in range(40):                                                                               # lazy susan: a gold ring on the lacquer
        a0, a1 = k * 0.157, (k + 1) * 0.157
        S.line(1.04 + 0.78 * math.cos(a0), 0.93 + 0.26 * math.sin(a0), 1.04 + 0.78 * math.cos(a1), 0.93 + 0.26 * math.sin(a1), 0.007, gold, 0.8)
    S.soft(0.90, 0.88, 0.6, 0.1, (1.0, 0.8, 0.5), 0.28 if not dark else 0.4, 1.3, add=True)
    S.soft(1.05, 0.95, 1.0, 0.30, (1.0, 0.75, 0.45), 0.20, 1.4, add=True)
    for u in (0.95, 1.55):                                                                                # lantern reflections in the lacquer
        S.soft(u, 0.70, 0.07, 0.16, (1.0, 0.3, 0.15), 0.22, 1.6, add=True)
    S.put("chinese_steamer", 0.58, 0.82, 0.30)
    S.put("chinese_wok", 1.52, 0.84, 0.22)
    S.put("chinese_tea", 1.50, 0.99, 0.12)
    S.put("chinese_noodle_bowl", 1.02, 0.95, 0.40, subject=True)
    S.focus("detail", 1.0, 0.78)
    with S.near(18.0):
        S.ellipse(1.80, 0.06, 0.11, 0.14, red, lift=0.1)
        S.rect(1.80, -0.08, 0.02, 0.2, BRASS, lift=0)
        S.soft(1.74, 1.03, 0.07, 0.06, (1.0, 0.7, 0.3), 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- street food / chaat
def _puri(c, u, v, r, rng):
    """A golgappa: a golden hollow ball with a poked hole and tiny blisters."""
    soft_disc(c, u + r * 0.3, v - r * 0.35, r * 1.1, r * 0.5, BLACK, 0.35, 1.4)
    _ball(c, u, v + r * 0.55, r, (0.94, 0.72, 0.34), 0.92, 0.6, 0.5)
    for _ in range(5):
        c.ellipse(u + rng.uniform(-0.6, 0.6) * r, v + r * 0.55 + rng.uniform(-0.6, 0.6) * r, r * 0.07, r * 0.05, (0.70, 0.42, 0.14), lift=0, alpha=0.7)
    c.ellipse(u - r * 0.05, v + r * 1.32, r * 0.34, r * 0.18, (0.60, 0.34, 0.12), lift=0)
    c.ellipse(u - r * 0.05, v + r * 1.33, r * 0.24, r * 0.11, (0.16, 0.08, 0.04), lift=0)


@sprop("street_golgappa", aspect=2.1, fill=0.62)
def street_golgappa(c, color):
    rng = c.rng
    soft_disc(c, 0.04, 0.0, 1.05, 0.22, BLACK, 0.40, 1.7)
    # steel tray
    c.ellipse(0.0, 0.03, 0.92, 0.92 * TILT, (0.45, 0.47, 0.51), lift=0)
    disc(c, 0.0, 0.07, 0.92, (0.84, 0.86, 0.89), TILT, 0.14)
    c.ellipse(0.0, 0.09, 0.80, 0.80 * TILT, (0.60, 0.62, 0.66), lift=0)
    c.ellipse(0.0, 0.095, 0.77, 0.77 * TILT, (0.88, 0.89, 0.92), lift=0.1)
    craft.arc(c, 0.0, 0.09, 0.86, 0.86 * TILT, 110, 195, 0.03, WHITE, 0.7, 8)
    soft_disc(c, 0.25, 0.08, 0.8, 0.22, BLACK, 0.18, 1.3)
    # puris in two rows around the pani bowl
    pos = [(-0.62, 0.30), (-0.38, 0.22), (-0.14, 0.20), (0.62, 0.30), (0.40, 0.21), (0.16, 0.19)]
    for k, (x, y) in enumerate(pos):
        _puri(c, x, y - 0.12, 0.115, rng)
    # a bowl of green pani (mint water) in the middle, a tamarind katori, a potato-chickpea katori
    bu, bv = 0.0, 0.34
    soft_disc(c, bu + 0.04, bv - 0.04, 0.3, 0.12, BLACK, 0.4, 1.3)
    c.ellipse(bu, bv - 0.04, 0.24, 0.24 * 0.46, (0.50, 0.52, 0.56), lift=0)
    c.ellipse(bu, bv, 0.24, 0.24 * 0.46, (0.90, 0.92, 0.95), lift=0.15)
    c.ellipse(bu, bv + 0.012, 0.215, 0.215 * 0.44, (0.30, 0.32, 0.36), lift=0)
    c.ellipse(bu, bv + 0.02, 0.2, 0.2 * 0.42, (0.46, 0.68, 0.22), lift=0.12)
    soft_disc(c, bu + 0.05, bv + 0.02, 0.15, 0.05, (0.15, 0.3, 0.05), 0.4, 1.2)
    for _ in range(14):
        c.ellipse(bu + rng.uniform(-0.15, 0.15), bv + 0.02 + rng.uniform(-0.04, 0.05), 0.011, 0.006, (0.72, 0.9, 0.4), lift=0, alpha=0.8)
    leaf(c, bu - 0.05, bv + 0.03, 0.09, 40, (0.2, 0.55, 0.2), 0.5)
    leaf(c, bu + 0.03, bv + 0.02, 0.08, 150, (0.28, 0.62, 0.22), 0.5)
    soft_disc(c, bu - 0.07, bv + 0.045, 0.07, 0.014, WHITE, 0.5, 1.1, add=True)
    _steel_bowl(c, -0.40, 0.55, 0.15, (0.50, 0.24, 0.08))                                     # sweet tamarind chutney
    _steel_bowl(c, 0.38, 0.55, 0.15, (0.82, 0.66, 0.30))                                      # potato and chickpea filling
    for _ in range(5):
        c.ellipse(0.38 + rng.uniform(-0.08, 0.08), 0.575 + rng.uniform(-0.01, 0.02), 0.018, 0.012, (0.62, 0.40, 0.12), lift=0.1)
    # a stuffed puri in front, dripping green pani
    _puri(c, -0.02, 0.0, 0.10, rng)
    drip(c, -0.10, 0.17, 0.012, (0.5, 0.75, 0.2))


@sprop("street_pavbhaji", aspect=2.3, fill=0.55)
def street_pavbhaji(c, color):
    rng = c.rng
    soft_disc(c, 0.04, 0.0, 1.05, 0.2, BLACK, 0.40, 1.7)
    iron = (0.18, 0.17, 0.18)
    # long wooden masher handle, tava, bhaji mound
    c.line(0.30, 0.42, 0.95, 0.20, 0.03, (0.35, 0.2, 0.1))
    c.line(0.30, 0.425, 0.95, 0.205, 0.016, (0.65, 0.42, 0.22))
    c.ellipse(0.0, 0.03, 0.62, 0.62 * 0.36, scale(iron, 0.7), lift=0)
    disc(c, 0.0, 0.10, 0.66, (0.30, 0.30, 0.33), 0.40, 0.08, rim=True)
    c.ellipse(0.0, 0.105, 0.60, 0.60 * 0.38, (0.10, 0.09, 0.09), lift=0)
    craft.arc(c, 0.0, 0.105, 0.62, 0.62 * 0.4, 110, 190, 0.02, (0.7, 0.7, 0.75), 0.6, 8)
    for _ in range(26):                                                                   # oily sheen and burnt bits
        c.ellipse(rng.uniform(-0.5, 0.5), 0.11 + rng.uniform(-0.08, 0.08), rng.uniform(0.02, 0.05), rng.uniform(0.008, 0.016), (0.45, 0.18, 0.06), lift=0, alpha=0.35)
    mu, mv = 0.0, 0.17
    c.ellipse(mu, mv, 0.44, 0.17, (0.52, 0.12, 0.04), lift=0)
    c.ellipse(mu, mv + 0.05, 0.40, 0.17, (0.82, 0.26, 0.08), lift=0.12)
    c.ellipse(mu - 0.01, mv + 0.11, 0.30, 0.12, (0.94, 0.38, 0.12), lift=0.12)
    soft_disc(c, mu + 0.14, mv + 0.06, 0.32, 0.12, (0.3, 0.05, 0.02), 0.4, 1.2)
    for _ in range(34):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        c.ellipse(mu + math.cos(a) * 0.34 * q, mv + 0.11 + math.sin(a) * 0.13 * q, rng.uniform(0.012, 0.03), rng.uniform(0.008, 0.016),
                  rng.choice([(1.0, 0.55, 0.2), (0.6, 0.12, 0.04), (0.95, 0.35, 0.1), (0.45, 0.55, 0.12)]), lift=0.1, alpha=0.8)
    for _ in range(18):                                                                   # chopped onion and coriander on top
        c.ellipse(mu + rng.uniform(-0.25, 0.25), mv + rng.uniform(0.1, 0.19), 0.014, 0.008, rng.choice([(0.95, 0.9, 0.95), (0.3, 0.65, 0.22)]), lift=0.1)
    c.rect(0.02, mv + 0.20, 0.10, 0.06, (1.0, 0.88, 0.30), r=0.012, lift=0.15)           # butter
    c.rect(0.02, mv + 0.235, 0.10, 0.02, (1.0, 0.96, 0.6), r=0.01, lift=0)
    soft_disc(c, 0.02, mv + 0.17, 0.12, 0.05, (1.0, 0.85, 0.3), 0.4, 1.2, add=True)
    gloss(c, -0.12, mv + 0.18, 0.1, 0.03, 8, 0.45)
    # pav buns on a plate, lemon wedge
    px_, py_ = -0.86, 0.02
    c.ellipse(px_, py_ + 0.03, 0.3, 0.3 * TILT, (0.55, 0.57, 0.6), lift=0)
    disc(c, px_, py_ + 0.06, 0.3, (0.86, 0.88, 0.9), TILT, 0.1)
    for k, (dx, dy) in enumerate(((-0.12, 0.0), (0.08, 0.02), (-0.02, 0.08))):
        _ball(c, px_ + dx, py_ + 0.1 + dy, 0.115, (0.90, 0.62, 0.26), 0.70, 0.55, 0.35)
        c.ellipse(px_ + dx, py_ + 0.12 + dy, 0.08, 0.022, (1.0, 0.88, 0.40), lift=0, alpha=0.7)
        c.line(px_ + dx - 0.07, py_ + 0.105 + dy, px_ + dx + 0.07, py_ + 0.105 + dy, 0.006, (0.6, 0.35, 0.12), 0.5)
    c.ellipse(px_ + 0.24, py_ + 0.05, 0.06, 0.04, (0.98, 0.92, 0.25), lift=0.12)
    c.ellipse(px_ + 0.24, py_ + 0.055, 0.04, 0.025, (1.0, 0.98, 0.65), lift=0)
    steam(c, 0.0, 0.46, 0.4, 0.08, 2, 0.20)


@sprop("street_chaat", aspect=1.25, fill=0.62)
def street_chaat(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.26)
    leafc = (0.66, 0.50, 0.28)
    # dona: a pleated leaf plate
    c.ellipse(0.0, 0.03, 0.47, 0.47 * TILT, scale(leafc, 0.5), lift=0)
    disc(c, 0.0, 0.07, 0.47, leafc, TILT, 0.12)
    for k in range(18):
        a = k * 0.35
        c.line(math.cos(a) * 0.40, 0.07 + math.sin(a) * 0.40 * TILT, math.cos(a) * 0.46, 0.07 + math.sin(a) * 0.46 * TILT, 0.008, scale(leafc, 0.7), 0.6)
    c.ellipse(0.0, 0.085, 0.38, 0.38 * TILT, scale(leafc, 0.75), lift=0)
    c.ellipse(0.0, 0.10, 0.355, 0.355 * TILT, (0.88, 0.80, 0.55), lift=0.1)
    # papdi base, yoghurt, chutneys, sev, pomegranate, onion, coriander
    for _ in range(8):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.25
        c.ellipse(math.cos(a) * q, 0.14 + math.sin(a) * q * 0.4, 0.07, 0.035, (0.86, 0.62, 0.28), lift=0.1)
    c.ellipse(0.0, 0.19, 0.26, 0.10, (0.96, 0.95, 0.88), lift=0.1)
    craft.arc(c, 0.0, 0.20, 0.17, 0.07, 10, 340, 0.022, (0.55, 0.28, 0.1), 0.9, 10)
    craft.arc(c, 0.0, 0.205, 0.10, 0.04, 30, 300, 0.018, (0.35, 0.6, 0.18), 0.9, 8)
    for _ in range(46):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.26
        craft.strand(c, math.cos(a) * q - 0.03, 0.19 + math.sin(a) * q * 0.4, rng.uniform(0.04, 0.09), rng.uniform(0, 180), 0.008, (1.0, 0.84, 0.32), 0.95, 0.5)
    for _ in range(20):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.26
        c.ellipse(math.cos(a) * q, 0.2 + math.sin(a) * q * 0.4, 0.011, 0.009, (0.78, 0.08, 0.16), lift=0.15)
    for _ in range(9):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random()) * 0.24
        c.ellipse(math.cos(a) * q, 0.2 + math.sin(a) * q * 0.4, 0.02, 0.012, (0.93, 0.52, 0.72), lift=0.1)
        leaf(c, math.cos(a) * q * 0.9, 0.2 + math.sin(a) * q * 0.36, 0.05, rng.uniform(0, 360), (0.28, 0.62, 0.24), 0.5)
    gloss(c, -0.1, 0.24, 0.1, 0.03, 8, 0.4)
    # spoon
    c.line(0.30, 0.10, 0.62, 0.18, 0.02, (0.78, 0.8, 0.84))
    c.ellipse(0.28, 0.095, 0.05, 0.03, (0.86, 0.88, 0.92), angle=14, lift=0.1)


@sprop("street_vadapav", aspect=1.3, fill=0.48)
def street_vadapav(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.22)
    # newspaper wrap
    c.poly([(-0.45, 0.03), (0.45, 0.03), (0.40, 0.2), (-0.40, 0.2)], (0.90, 0.88, 0.80), lift=0.06)
    for k in range(9):
        c.line(-0.38 + (k % 3) * 0.02, 0.05 + k * 0.016, 0.36 - (k % 4) * 0.03, 0.05 + k * 0.016, 0.005, (0.45, 0.45, 0.45), 0.45)
    # pav: two bun halves with the vada in between
    c.ellipse(0.0, 0.12, 0.30, 0.13, (0.62, 0.38, 0.14), lift=0)
    c.ellipse(0.0, 0.15, 0.29, 0.12, (0.90, 0.66, 0.30), lift=0.14)
    _ball(c, 0.0, 0.26, 0.17, (0.84, 0.56, 0.16), 0.9, 0.55, 0.3)
    for _ in range(11):
        c.ellipse(rng.uniform(-0.13, 0.13), 0.26 + rng.uniform(-0.1, 0.1), 0.011, 0.007, (0.55, 0.30, 0.08), lift=0, alpha=0.8)
    c.ellipse(-0.20, 0.25, 0.14, 0.14, (0.98, 0.84, 0.50), lift=0.12)                    # the bun's top half, tilted open
    c.ellipse(0.0, 0.20, 0.25, 0.04, (0.78, 0.12, 0.08), lift=0, alpha=0.7)                # garlic chutney
    c.line(0.1, 0.17, 0.42, 0.22, 0.026, (0.35, 0.65, 0.18))                              # fried green chilli
    c.line(0.1, 0.176, 0.42, 0.226, 0.012, (0.55, 0.82, 0.3), 0.9)
    soft_disc(c, -0.06, 0.33, 0.11, 0.03, WHITE, 0.4, 1.1, add=True)


@sprop("street_matka", aspect=0.95, fill=1.0)
def street_matka(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.14)
    clay_l, clay_r = (0.86, 0.46, 0.24), (0.46, 0.20, 0.10)
    pts_l = [(0.0, 0.02), (0.18, 0.05), (0.30, 0.22), (0.38, 0.42), (0.33, 0.62), (0.22, 0.74), (0.20, 0.80)]
    poly = [(-x, y) for x, y in pts_l[::-1]] + pts_l
    c.poly(poly, clay_l, lift=0.1)
    c.poly([(0.04, 0.02)] + [(x * 0.9 + 0.02, y) for x, y in pts_l[1:]] + [(0.20, 0.80), (0.04, 0.80)], clay_r, lift=0, alpha=0.45)
    c.poly([(0.20, 0.05), (0.18, 0.05), (0.30, 0.22), (0.38, 0.42), (0.33, 0.62), (0.22, 0.74)], clay_r, lift=0, alpha=0.0)
    c.poly([(-0.30, 0.30), (-0.25, 0.30), (-0.24, 0.62), (-0.30, 0.55)], (1.0, 0.8, 0.6), lift=0, alpha=0.35)
    for k in range(7):                                                                    # painted white dots band
        x = -0.28 + k * 0.095
        c.ellipse(x, 0.50 + 0.02 * math.sin(k), 0.016, 0.014, (0.98, 0.92, 0.82), lift=0.0)
    craft.arc(c, 0.0, 0.34, 0.36, 0.05, 190, 350, 0.012, (0.98, 0.92, 0.82), 0.6, 8)
    c.ellipse(0.0, 0.80, 0.22, 0.22 * 0.38, scale(clay_r, 0.8), lift=0)
    c.ellipse(0.0, 0.805, 0.20, 0.20 * 0.36, (0.30, 0.16, 0.06), lift=0)
    c.ellipse(0.0, 0.80, 0.17, 0.17 * 0.34, (0.42, 0.66, 0.20), lift=0.1)
    c.ellipse(-0.04, 0.80, 0.07, 0.02, (0.7, 0.9, 0.4), lift=0, alpha=0.6)
    c.line(0.1, 0.82, 0.22, 0.95, 0.012, (0.75, 0.77, 0.82))                               # steel ladle


@niche("street-food", "Street food / chaat stall", subjects=("street_golgappa",),
       strong=("street food", "chaat", "pani puri", "golgappa", "pav bhaji", "vada pav", "chaat stall", "chaat corner", "food cart", "thela",
               "चाट", "गोलगप्पे", "पानी पूरी", "पाव भाजी", "वड़ा पाव", "चाट भंडार", "ठेला"),
       weak=("bhel", "sev puri", "dahi puri", "papdi", "samosa", "tikki", "food truck", "evening snacks", "stall"),
       accent="#e65100", mood="warm", group="food", avoid=("fast food", "burger"))
def street_food(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        # dusk street behind: building blocks with lit windows
        for i in range(-12, 22):
            u = -3.0 + i * 0.28
            hgt = 0.10 + 0.17 * ((i * 7) % 5) / 4.0
            S.rect(u, 0.50 - hgt / 2, 0.26, hgt, scale(P.wall_bot, 0.78 - 0.06 * (i % 3)), lift=0.0)
            if i % 2 == 0:
                S.rect(u, 0.50 - hgt * 0.6, 0.05, 0.04, (1.0, 0.82, 0.45), lift=0.0, alpha=0.8)
        S.bokeh(14, -0.2, 0.15, 2.3, 0.55, [(1.0, 0.85, 0.5), (1.0, 0.6, 0.3), (1.0, 0.95, 0.75), (0.7, 0.85, 1.0)], 0.012, 0.045, 0.45)
        # shelf with steel dabbas
        S.rect(0.55, 0.40, 0.72, 0.016, scale(P.surface, 0.6), lift=0.05)
        for k in range(6):
            S.rect(0.30 + k * 0.095, 0.36, 0.07, 0.07, (0.78, 0.80, 0.84), r=0.008, lift=0.12)
        # striped awning with a scalloped fringe and hanging bulbs
        for i in range(-30, 40):
            u = -3.0 + i * 0.12
            S.rect(u, -0.05, 0.12, 0.30, P.accent if i % 2 == 0 else mix(P.paper, P.accent_light, 0.3), lift=0.0)
            S.circle(u, 0.10, 0.06, P.accent if i % 2 == 0 else mix(P.paper, P.accent_light, 0.3), lift=0.0)
        S.rect(1.0, 0.115, 14.0, 0.03, scale(P.accent_dark, 0.8), lift=0.0, alpha=0.5)
        _hanging_bulbs(S, -0.2, 2.2, 0.20, 0.20, 14, (1.0, 0.80, 0.42), 0.018)
        for u in (0.5, 0.95, 1.4, 1.85):
            S.glow(u, 0.30, 0.3, (1.0, 0.7, 0.3), 0.25)
        S.floor(0.60, P.floor_top, P.floor_bot)
    steel = (0.60, 0.63, 0.68)
    top = scale(mix(steel, P.accent, 0.08), 0.55 if dark else 0.92)
    S.floor(0.60, scale(top, 1.12), scale(top, 0.62))
    for _ in range(30):                                                                          # brushed steel streaks
        x, y = rng.uniform(-4, 6), rng.uniform(0.64, 2.2)
        S.line(x, y, x + rng.uniform(0.3, 0.9), y, 0.004, scale(top, rng.uniform(1.08, 1.2)), 0.25)
    S.rect(1.0, 0.608, 14.0, 0.016, scale(top, 0.55), lift=0.0)
    cl1 = P.accent if not dark else scale(P.accent, 0.6)
    cl2 = WHITE if not dark else (0.55, 0.55, 0.52)
    S.tiles(0.36, 0.70, 1.80, 1.20, cl1, cl2, 0.072)                                              # red and white checked cloth
    S.rect(1.08, 1.205, 1.44, 0.012, scale(cl1, 0.55), lift=0.0)
    S.rect(1.08, 1.225, 1.44, 0.02, (0, 0, 0), lift=0.0, alpha=0.25)
    S.soft(1.08, 0.71, 0.8, 0.05, (0, 0, 0), 0.28, 1.4)
    S.soft(1.08, 1.14, 0.9, 0.12, (0, 0, 0), 0.12, 1.4)
    for u in (0.5, 0.95, 1.4, 1.85):                                                              # bulbs reflected in the steel
        S.soft(u, 0.78, 0.06, 0.20, (1.0, 0.75, 0.4), 0.22, 1.6, add=True)
    S.soft(1.05, 0.90, 1.0, 0.26, (1.0, 0.82, 0.5), 0.26 if not dark else 0.42, 1.5, add=True)
    S.put("street_matka", 1.58, 0.82, 0.27)
    S.put("street_pavbhaji", 0.74, 0.86, 0.21)
    S.put("street_chaat", 0.64, 0.99, 0.15)
    S.put("street_golgappa", 1.14, 0.98, 0.27, subject=True)
    S.put("street_vadapav", 1.50, 0.99, 0.13)
    S.focus("detail", 1.14, 0.84)
    with S.near(16.0):
        S.soft(1.88, 1.02, 0.08, 0.07, (1.0, 0.75, 0.3), 0.6, 1.0)
        for k in range(4):
            S.circle(1.78 + k * 0.045, 1.07, 0.03, (0.85, 0.12, 0.08), lift=0.1)


# ---------------------------------------------------------------------------------------------- bar and lounge
def _glass_tri(c, u, v, w, h, liquid, alpha=0.30):
    """A conical bowl (martini / coupe) with liquid in it."""
    c.poly([(u - w / 2, v + h), (u + w / 2, v + h), (u, v)], (0.88, 0.93, 0.98), alpha=alpha, lift=0)
    c.poly([(u - w * 0.44, v + h * 0.82), (u + w * 0.44, v + h * 0.82), (u, v + h * 0.06)], liquid, alpha=0.95, lift=0.1)
    c.ellipse(u, v + h * 0.82, w * 0.44, w * 0.44 * 0.28, mix(liquid, WHITE, 0.2), lift=0.15)
    c.ellipse(u, v + h, w / 2, w / 2 * 0.28, (0.9, 0.95, 1.0), lift=0, alpha=0.4)
    craft.arc(c, u, v + h, w / 2, w / 2 * 0.28, 0, 180, 0.01, WHITE, 0.75, 8)


@sprop("bar_cocktails", aspect=1.75, fill=0.95)
def bar_cocktails(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.8, 0.34)
    # a brass tray with a coaster look
    c.ellipse(0.0, 0.015, 0.95, 0.95 * 0.30, scale(BRASS, 0.4), lift=0)
    disc(c, 0.0, 0.04, 0.95, (0.30, 0.20, 0.34), 0.30, 0.1, rim=True)
    craft.arc(c, 0.0, 0.05, 0.9, 0.9 * 0.30, 200, 340, 0.015, (1.0, 0.8, 0.5), 0.5, 8)
    soft_disc(c, 0.0, 0.05, 0.9, 0.2, (1.0, 0.7, 0.9), 0.14, 1.3, add=True)
    # rocks glass with a big ice cube (left)
    ru = -0.55
    soft_disc(c, ru + 0.1, 0.05, 0.3, 0.07, BLACK, 0.4, 1.3)
    c.poly([(ru - 0.16, 0.38), (ru + 0.16, 0.38), (ru + 0.13, 0.07), (ru - 0.13, 0.07)], (0.90, 0.94, 0.98), alpha=0.35, lift=0)
    c.poly([(ru - 0.155, 0.30), (ru + 0.155, 0.30), (ru + 0.13, 0.08), (ru - 0.13, 0.08)], (0.86, 0.50, 0.12), alpha=0.95, lift=0.12)
    c.poly([(ru + 0.03, 0.30), (ru + 0.155, 0.30), (ru + 0.13, 0.08), (ru + 0.02, 0.08)], (0.4, 0.15, 0.02), lift=0, alpha=0.4)
    c.rect(ru - 0.02, 0.24, 0.12, 0.12, (0.90, 0.96, 1.0), r=0.02, lift=0.1, alpha=0.7)
    c.rect(ru - 0.04, 0.27, 0.05, 0.06, WHITE, r=0.01, lift=0, alpha=0.5)
    c.ellipse(ru, 0.38, 0.16, 0.16 * 0.3, (0.9, 0.95, 1.0), lift=0, alpha=0.4)
    craft.arc(c, ru, 0.38, 0.16, 0.16 * 0.3, 0, 180, 0.01, WHITE, 0.75, 8)
    c.line(ru - 0.11, 0.34, ru - 0.10, 0.11, 0.014, WHITE, 0.6)
    c.ellipse(ru + 0.13, 0.36, 0.06, 0.02, (1.0, 0.6, 0.1), angle=-18, lift=0.1)                # orange peel
    # tall highball with a mojito (right)
    hu = 0.56
    soft_disc(c, hu + 0.1, 0.05, 0.28, 0.07, BLACK, 0.4, 1.3)
    c.poly([(hu - 0.13, 0.86), (hu + 0.13, 0.86), (hu + 0.11, 0.07), (hu - 0.11, 0.07)], (0.90, 0.94, 0.98), alpha=0.30, lift=0)
    c.poly([(hu - 0.125, 0.74), (hu + 0.125, 0.74), (hu + 0.11, 0.08), (hu - 0.11, 0.08)], (0.62, 0.86, 0.36), alpha=0.92, lift=0.1)
    c.poly([(hu + 0.02, 0.74), (hu + 0.125, 0.74), (hu + 0.11, 0.08), (hu + 0.01, 0.08)], (0.1, 0.35, 0.1), lift=0, alpha=0.35)
    for k in range(7):
        c.rect(hu + rng.uniform(-0.07, 0.07), 0.15 + k * 0.085, rng.uniform(0.05, 0.08), rng.uniform(0.05, 0.07), (0.92, 0.98, 1.0), r=0.01, lift=0.1, alpha=0.6)
    for k in range(5):
        c.ellipse(hu + rng.uniform(-0.08, 0.08), 0.2 + k * 0.1, 0.012, 0.01, (0.2, 0.5, 0.15), lift=0, alpha=0.7)
    c.ellipse(hu, 0.74, 0.125, 0.125 * 0.28, (0.80, 0.95, 0.5), lift=0.12)
    for k in range(4):
        leaf(c, hu - 0.05 + k * 0.035, 0.76, 0.12, 60 + k * 22, (0.20, 0.62, 0.25), 0.45)
    c.ellipse(hu + 0.13, 0.85, 0.07, 0.07, (0.72, 0.9, 0.25), lift=0.1)                         # lime wheel on the rim
    c.ellipse(hu + 0.13, 0.85, 0.05, 0.05, (0.88, 0.97, 0.5), lift=0)
    c.line(hu + 0.05, 0.60, hu + 0.17, 1.0, 0.016, (0.96, 0.96, 0.96))                            # straw
    c.line(hu + 0.052, 0.62, hu + 0.172, 1.0, 0.007, (0.85, 0.2, 0.3), 0.8)
    c.ellipse(hu, 0.86, 0.13, 0.13 * 0.28, (0.9, 0.95, 1.0), lift=0, alpha=0.4)
    craft.arc(c, hu, 0.86, 0.13, 0.13 * 0.28, 0, 180, 0.01, WHITE, 0.75, 8)
    c.line(hu - 0.1, 0.80, hu - 0.09, 0.14, 0.014, WHITE, 0.6)
    # martini in the middle
    mu = 0.0
    soft_disc(c, mu + 0.08, 0.04, 0.26, 0.06, BLACK, 0.4, 1.3)
    c.ellipse(mu, 0.045, 0.14, 0.14 * 0.3, (0.82, 0.86, 0.9), lift=0, alpha=0.6)
    c.rect(mu, 0.26, 0.022, 0.43, (0.88, 0.92, 0.96), lift=0, alpha=0.9)
    c.rect(mu - 0.006, 0.26, 0.007, 0.42, WHITE, lift=0, alpha=0.6)
    _glass_tri(c, mu, 0.47, 0.44, 0.34, (0.88, 0.18, 0.46))
    soft_disc(c, mu + 0.06, 0.58, 0.14, 0.08, (0.4, 0.02, 0.2), 0.4, 1.2)
    c.line(mu - 0.20, 0.84, mu + 0.12, 0.74, 0.008, (0.7, 0.7, 0.7))                           # pick with a cherry
    _ball(c, mu + 0.08, 0.745, 0.035, (0.75, 0.05, 0.12), 1.0, 0.5, 0.6)
    c.line(mu - 0.15, 0.80, mu - 0.17, 0.52, 0.012, WHITE, 0.5)
    gloss(c, mu - 0.1, 0.72, 0.012, 0.06, 20, 0.7)


@sprop("bar_shaker", aspect=0.95, fill=1.0)
def bar_shaker(c, color):
    ao(c, 0.0, 0.0, 0.8, 0.16)
    left, right = (0.97, 0.98, 1.0), (0.46, 0.48, 0.54)
    # jigger at the side
    c.poly([(0.30, 0.30), (0.50, 0.30), (0.45, 0.20), (0.39, 0.12), (0.41, 0.06), (0.37, 0.06), (0.35, 0.12), (0.34, 0.20)], mix(left, right, 0.3), lift=0.1)
    c.poly([(0.42, 0.30), (0.50, 0.30), (0.45, 0.20), (0.41, 0.12)], (0.2, 0.2, 0.25), lift=0, alpha=0.3)
    c.ellipse(0.40, 0.045, 0.09, 0.03, mix(right, BLACK, 0.2), lift=0)
    # shaker: body, strainer cap, small cap
    c.ellipse(-0.12, 0.03, 0.21, 0.21 * TILT, scale(right, 0.75), lift=0)
    c.poly([(-0.32, 0.64), (0.08, 0.64), (0.0, 0.04), (-0.24, 0.04)], mix(left, right, 0.45), lift=0.06)
    for x0, al in ((-0.14, 0.12), (-0.08, 0.16), (-0.02, 0.2), (0.04, 0.26)):
        c.poly([(x0, 0.64), (0.08, 0.64), (0.0, 0.04), (x0 * 0.7 - 0.04, 0.04)], (0.1, 0.1, 0.18), lift=0, alpha=al)
    c.poly([(-0.29, 0.62), (-0.22, 0.62), (-0.185, 0.07), (-0.225, 0.07)], WHITE, lift=0, alpha=0.7)
    c.ellipse(-0.12, 0.64, 0.20, 0.20 * TILT, scale(right, 0.8), lift=0)
    c.poly([(-0.30, 0.66), (0.06, 0.66), (0.0, 0.84), (-0.24, 0.84)], mix(left, right, 0.4), lift=0.08)
    c.poly([(-0.28, 0.82), (-0.24, 0.82), (-0.20, 0.68), (-0.25, 0.68)], WHITE, lift=0, alpha=0.6)
    for k in range(3):
        c.ellipse(-0.20 + k * 0.08, 0.76, 0.014, 0.014, (0.15, 0.15, 0.2), lift=0)
    c.ellipse(-0.12, 0.85, 0.12, 0.12 * TILT, scale(right, 0.8), lift=0)
    c.poly([(-0.20, 0.86), (-0.04, 0.86), (-0.06, 0.94), (-0.18, 0.94)], mix(left, right, 0.35), lift=0.08)
    c.ellipse(-0.12, 0.94, 0.06, 0.06 * TILT, left, lift=0.1)
    gloss(c, -0.22, 0.5, 0.012, 0.12, 0, 0.5)


@sprop("bar_ice_bucket", aspect=0.85, fill=1.0)
def bar_ice_bucket(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.16)
    g_l, g_r = (0.12, 0.34, 0.18), (0.03, 0.12, 0.06)
    # bottle in the bucket
    craft.hshade_box(c, 0.0, 0.62, 0.17, 0.5, (0.18, 0.46, 0.24), g_r, r=0.02)
    c.poly([(-0.075, 0.86), (0.075, 0.86), (0.035, 1.02), (-0.035, 1.02)], (0.12, 0.34, 0.18), lift=0.1)
    c.poly([(0.0, 0.86), (0.075, 0.86), (0.035, 1.02), (0.0, 1.02)], BLACK, lift=0, alpha=0.3)
    c.rect(0.0, 1.0, 0.085, 0.10, (0.96, 0.76, 0.28), r=0.01, lift=0.15)                            # gold foil neck
    c.rect(0.0, 0.62, 0.15, 0.18, (0.96, 0.93, 0.82), lift=0.04)
    c.rect(0.0, 0.62, 0.10, 0.012, (0.6, 0.1, 0.1), lift=0)
    gloss(c, -0.05, 0.66, 0.012, 0.15, 0, 0.6)
    # steel bucket
    steel_l, steel_r = (0.93, 0.95, 0.98), (0.42, 0.45, 0.54)
    c.ellipse(0.0, 0.03, 0.30, 0.30 * TILT, scale(steel_r, 0.7), lift=0)
    c.poly([(-0.42, 0.56), (0.42, 0.56), (0.30, 0.04), (-0.30, 0.04)], mix(steel_l, steel_r, 0.4), lift=0.06)
    for x0, al in ((0.0, 0.10), (0.12, 0.16), (0.24, 0.22), (0.34, 0.28)):
        c.poly([(x0, 0.56), (0.42, 0.56), (0.30, 0.04), (x0 * 0.72, 0.04)], (0.05, 0.08, 0.2), lift=0, alpha=al)
    c.poly([(-0.38, 0.54), (-0.30, 0.54), (-0.22, 0.07), (-0.27, 0.07)], WHITE, lift=0, alpha=0.6)
    c.ellipse(0.0, 0.56, 0.42, 0.42 * TILT, scale(steel_r, 0.8), lift=0)
    c.ellipse(0.0, 0.565, 0.40, 0.40 * TILT, steel_l, lift=0.1)
    c.ellipse(0.0, 0.57, 0.35, 0.35 * TILT, (0.55, 0.78, 0.9), lift=0.1)
    for _ in range(18):                                                                             # ice cubes
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        x, y = math.cos(a) * 0.30 * q, 0.58 + math.sin(a) * 0.12 * q
        c.rect(x, y, rng.uniform(0.06, 0.09), rng.uniform(0.04, 0.06), (0.88, 0.96, 1.0), r=0.012, lift=0.12, alpha=0.95)
        c.rect(x - 0.01, y + 0.01, 0.03, 0.02, WHITE, r=0.006, lift=0, alpha=0.6)
    c.rect(0.0, 0.60, 0.17, 0.04, (0.2, 0.4, 0.2), lift=0, alpha=0.0)
    c.line(0.42, 0.52, 0.52, 0.45, 0.025, scale(steel_r, 1.0))                                      # handle
    c.line(-0.42, 0.52, -0.52, 0.45, 0.025, scale(steel_r, 1.0))


@sprop("bar_stool", aspect=0.5, fill=1.0)
def bar_stool(c, color):
    seat = color or (0.45, 0.10, 0.50)
    ao(c, 0.0, 0.0, 0.7, 0.12)
    for x in (-0.22, 0.22):
        c.line(x, 0.03, x * 0.55, 0.70, 0.03, (0.20, 0.17, 0.2))
    c.line(-0.18, 0.28, 0.18, 0.28, 0.02, BRASS)
    c.ellipse(0.0, 0.03, 0.26, 0.26 * TILT, (0.2, 0.17, 0.2), lift=0)
    c.rect(0.0, 0.74, 0.5, 0.10, scale(seat, 0.7), r=0.04, lift=0.1)
    c.ellipse(0.0, 0.79, 0.27, 0.27 * TILT, scale(seat, 0.7), lift=0)
    c.ellipse(0.0, 0.80, 0.26, 0.26 * TILT, seat, lift=0.14)
    gloss(c, -0.08, 0.82, 0.12, 0.03, 4, 0.4)


@niche("bar-lounge", "Bar and lounge", subjects=("bar_cocktails",),
       strong=("bar and lounge", "cocktail bar", "pub", "brewery", "taproom", "cocktails", "mocktails", "lounge bar", "sky bar", "craft beer",
               "bar and restaurant", "बार", "कॉकटेल", "मॉकटेल", "लाउंज", "पब", "बीयर बार", "शराब की दुकान"),
       weak=("whiskey", "beer", "nightlife", "happy hour", "drinks", "bartender", "wine bar", "लाउन्ज"),
       accent="#6a1b9a", mood="dark", group="food", avoid=("juice bar", "salad bar", "coffee"))
def bar_lounge(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        back = scale(P.accent_dark, 0.42) if not dark else scale(P.accent_dark, 0.5)
        S.rect(1.05, 0.30, 14.0, 0.62, back, lift=0.0)                                              # dark back-bar wall
        glowc = mix(P.accent_light, (1.0, 0.75, 0.45), 0.5)
        for v, bright in ((0.14, 1.0), (0.29, 0.9), (0.44, 0.8)):                                    # three lit shelves with bottles
            S.rect(1.05, v - 0.065, 14.0, 0.07, scale(glowc, 0.8), lift=0.0, alpha=0.5)
            S.glow(1.05, v - 0.04, 1.6, glowc, 0.18 * bright)
            S.rect(1.05, v + 0.012, 14.0, 0.014, scale(P.surface, 0.7), lift=0.05)
            u = -1.0
            while u < 3.2:
                bw = rng.uniform(0.04, 0.065)
                bh = rng.uniform(0.07, 0.12)
                col = rng.choice([(0.55, 0.30, 0.08), (0.12, 0.40, 0.20), (0.60, 0.12, 0.25), (0.85, 0.65, 0.2), (0.15, 0.25, 0.6), (0.7, 0.75, 0.8), (0.85, 0.4, 0.1)])
                S.rect(u, v - bh / 2, bw, bh, col, r=0.008, lift=0.15)
                S.rect(u, v - bh - 0.018, bw * 0.38, 0.04, scale(col, 0.85), lift=0.1)
                S.rect(u - bw * 0.2, v - bh * 0.5, bw * 0.15, bh * 0.7, WHITE, lift=0.0, alpha=0.3)
                S.glow(u, v - bh * 0.6, 0.06, mix(col, WHITE, 0.4), 0.3)
                u += bw + rng.uniform(0.012, 0.04)
        # neon ring sign
        S.glow(0.22, 0.18, 0.5, (1.0, 0.25, 0.7), 0.55)
        for k in range(28):                                                                          # neon ring tube
            a0, a1 = k * 0.2244, (k + 1) * 0.2244
            S.line(0.22 + 0.095 * math.cos(a0), 0.18 + 0.095 * math.sin(a0), 0.22 + 0.095 * math.cos(a1), 0.18 + 0.095 * math.sin(a1), 0.012, (1.0, 0.55, 0.88))
        S.pendant(1.30, -0.1, 0.12, (1.0, 0.72, 0.38), 0.07)
        S.pendant(1.78, -0.1, 0.10, (1.0, 0.72, 0.38), 0.07)
        S.pendant(0.78, -0.1, 0.09, (1.0, 0.72, 0.38), 0.07)
        S.bokeh(10, -0.2, 0.05, 2.3, 0.55, [(1.0, 0.5, 0.8), (1.0, 0.75, 0.4), (0.6, 0.5, 1.0)], 0.012, 0.04, 0.4)
        S.floor(0.60, P.floor_top, P.floor_bot)
    # bar counter: polished dark wood with a brass foot rail edge and reflections of the lit shelves
    top = scale(mix(P.surface, P.accent_dark, 0.25), 0.55 if not dark else 0.42)
    S.floor(0.60, scale(top, 1.10), scale(top, 0.55))
    for _ in range(26):
        x, y = rng.uniform(-4, 6), rng.uniform(0.66, 2.2)
        S.line(x, y, x + rng.uniform(0.3, 0.8), y + rng.uniform(-0.008, 0.008), 0.0035, scale(top, rng.uniform(1.15, 1.35)), 0.3)
    S.rect(1.0, 0.608, 14.0, 0.016, BRASS, lift=0.1)
    S.rect(1.0, 0.62, 14.0, 0.006, scale(BRASS, 0.5), lift=0.0)
    for u in (0.30, 0.7, 1.1, 1.5, 1.9):
        S.soft(u, 0.72, 0.09, 0.2, glowc, 0.22, 1.6, add=True)
    S.soft(1.1, 0.88, 1.2, 0.30, mix(P.accent_light, (1.0, 0.8, 0.6), 0.5), 0.24 if not dark else 0.42, 1.5, add=True)
    S.soft(1.1, 1.15, 1.6, 0.3, (0.8, 0.4, 1.0), 0.10, 1.3, add=True)
    S.put("bar_ice_bucket", 0.60, 0.84, 0.30)
    S.put("bar_shaker", 1.62, 0.86, 0.28)
    S.put("bar_cocktails", 1.08, 0.98, 0.34, subject=True)
    S.focus("detail", 1.08, 0.78)
    with S.near(18.0):
        S.soft(1.84, 1.02, 0.08, 0.08, (1.0, 0.5, 0.8), 0.5, 1.0)
        S.soft(0.34, 1.05, 0.10, 0.09, (0.8, 0.4, 1.0), 0.5, 1.0)


# ---------------------------------------------------------------------------------------------- catering
def _food_mound(c, u, v, a, b, kind):
    """Heaped buffet food seen in a pan: base ellipse, domed body, garnish. (u, v) is the centre of the pan opening, a/b its half sizes."""
    rng = c.rng
    fc = {"paneer": (0.93, 0.40, 0.08), "rice": (0.99, 0.95, 0.80), "dal": (0.42, 0.17, 0.06), "veg": (0.88, 0.62, 0.12)}[kind]
    c.ellipse(u, v - b * 0.1, a, b, scale(fc, 0.55), lift=0)
    c.ellipse(u, v + b * 0.35, a * 0.97, b * 1.18, fc, lift=0.14)
    soft_disc(c, u + a * 0.35, v + b * 0.1, a * 0.6, b * 0.9, scale(fc, 0.35), 0.38, 1.3)
    soft_disc(c, u - a * 0.35, v + b * 0.75, a * 0.5, b * 0.45, mix(fc, WHITE, 0.6), 0.5, 1.3, add=True)
    if kind == "paneer":
        for _ in range(10):                                                                  # paneer cubes, lit top and dark side
            x, y = u + rng.uniform(-0.8, 0.8) * a, v + b * rng.uniform(0.0, 1.2)
            sz = a * 0.11
            c.rect(x, y - sz * 0.35, sz * 2.0, sz * 1.2, (0.85, 0.72, 0.5), r=sz * 0.3, lift=0)
            c.rect(x, y, sz * 2.0, sz * 1.25, (1.0, 0.93, 0.72), r=sz * 0.3, lift=0.14)
            c.rect(x + sz * 0.5, y - sz * 0.1, sz * 0.7, sz * 0.9, (0.8, 0.5, 0.2), r=sz * 0.2, lift=0, alpha=0.4)
        craft.arc(c, u, v + b * 0.6, a * 0.5, b * 0.45, 10, 350, a * 0.07, (1.0, 0.96, 0.88), 0.9, 10)       # cream swirl
        craft.arc(c, u + a * 0.1, v + b * 0.6, a * 0.28, b * 0.25, 40, 300, a * 0.05, (1.0, 0.96, 0.88), 0.8, 8)
        for _ in range(12):
            leaf(c, u + rng.uniform(-0.7, 0.7) * a, v + b * rng.uniform(0.1, 1.2), a * 0.12, rng.uniform(0, 360), (0.2, 0.58, 0.2), 0.5)
    elif kind == "rice":
        for _ in range(46):
            x, y = u + rng.uniform(-0.85, 0.85) * a, v + b * rng.uniform(-0.1, 1.45)
            c.ellipse(x, y, a * 0.035, a * 0.012, rng.choice([(1.0, 1.0, 0.95), (0.96, 0.78, 0.3), (0.92, 0.9, 0.8)]), lift=0.05, angle=rng.uniform(-40, 40))
        for _ in range(14):                                                                  # carrot, peas
            c.ellipse(u + rng.uniform(-0.75, 0.75) * a, v + b * rng.uniform(0.0, 1.35), a * 0.045, a * 0.03, rng.choice([(0.95, 0.5, 0.1), (0.3, 0.65, 0.2)]), lift=0.1)
        for _ in range(8):                                                                   # fried onion crown
            craft.strand(c, u + rng.uniform(-0.3, 0.3) * a, v + b * rng.uniform(0.9, 1.4), a * 0.25, rng.uniform(0, 180), a * 0.03, (0.62, 0.36, 0.1), 0.9, 0.5)
    elif kind == "dal":
        craft.arc(c, u - a * 0.1, v + b * 0.7, a * 0.45, b * 0.5, 10, 350, a * 0.08, (0.98, 0.9, 0.78), 0.95, 10)
        c.ellipse(u + a * 0.35, v + b * 0.9, a * 0.11, b * 0.28, (1.0, 0.88, 0.45), lift=0.14)       # butter pat
        for _ in range(16):
            c.ellipse(u + rng.uniform(-0.8, 0.8) * a, v + b * rng.uniform(0.0, 1.3), a * 0.04, a * 0.025, (0.62, 0.28, 0.08), lift=0, alpha=0.6)
        for _ in range(5):
            c.ellipse(u + rng.uniform(-0.5, 0.5) * a, v + b * rng.uniform(0.3, 1.1), a * 0.035, a * 0.02, (0.8, 0.12, 0.08), lift=0.1)
        leaf(c, u - a * 0.25, v + b * 1.05, a * 0.15, 60, (0.2, 0.58, 0.2), 0.5)
    else:
        for _ in range(18):
            c.ellipse(u + rng.uniform(-0.8, 0.8) * a, v + b * rng.uniform(0.0, 1.3), a * 0.06, a * 0.04, rng.choice([(0.4, 0.62, 0.2), (0.95, 0.5, 0.1), (0.98, 0.9, 0.4)]), lift=0.1)


def _steel_lid_open(c, u, v, w, hgt, round_lid=False):
    """An opened lid standing up behind the pan, seen from the inside: steel with a warm reflection of the food and a brass rim."""
    sl, sr = (0.97, 0.98, 1.0), (0.48, 0.50, 0.56)
    if round_lid:
        a, b = w * 0.5, hgt * 0.5
        c.ellipse(u, v, a * 1.05, b * 1.04, scale(BRASS, 0.7), lift=0)
        c.ellipse(u, v - b * 0.02, a * 0.97, b * 0.96, mix(sl, sr, 0.45), lift=0.08)
        c.ellipse(u + a * 0.25, v - b * 0.05, a * 0.6, b * 0.85, sr, lift=0, alpha=0.4)
        soft_disc(c, u - a * 0.35, v + b * 0.3, a * 0.35, b * 0.6, WHITE, 0.55, 1.2, add=True)
        c.ellipse(u, v + b * 0.05, a * 0.12, b * 0.12, BRASS, lift=0.2)
        return
    hw = w * 0.45
    top = v + hgt
    pts = [(-hw, v), (hw, v)] + [(math.cos(math.radians(th)) * hw, v + hgt * 0.62 + math.sin(math.radians(th)) * hgt * 0.38) for th in range(0, 181, 20)]
    c.poly([(u + x * 1.06, y + (0.012 if y > v + 0.01 else -0.01)) for x, y in pts], scale(BRASS, 0.75), lift=0)
    c.poly([(u + x, y) for x, y in pts], mix(sl, sr, 0.35), lift=0.06)
    for k, (x0, x1, al, col) in enumerate(((-0.44, -0.32, 0.55, WHITE), (-0.18, -0.12, 0.22, WHITE), (0.10, 0.45, 0.30, (0.08, 0.1, 0.2)), (0.28, 0.34, 0.2, WHITE))):
        c.poly([(u + hw * x0 / 0.45, v + 0.01), (u + hw * x1 / 0.45, v + 0.01), (u + hw * x1 / 0.45, top - hgt * 0.1), (u + hw * x0 / 0.45, top - hgt * 0.1)], col, lift=0, alpha=al)
    soft_disc(c, u, v + hgt * 0.1, hw * 0.9, hgt * 0.35, (1.0, 0.62, 0.22), 0.42, 1.5, add=True)         # food glow in the steel
    c.rect(u, top + 0.012, 0.07, 0.03, BRASS, r=0.01, lift=0.18)                                           # brass knob handle
    c.rect(u, top + 0.012, 0.055, 0.012, mix(BRASS, WHITE, 0.5), r=0.005, lift=0, alpha=0.8)
    for sx in (-1, 1):
        c.ellipse(u + sx * hw * 0.97, v + 0.012, 0.014, 0.014, BRASS, lift=0.2)                           # hinges


def _chafer_rect(c, u, v, w, kind):
    """A roll-top chafing dish: lid opened behind, heaped food, brass-trimmed water pan, a rail frame with fuel cans and flames."""
    rng = c.rng
    sl, sr = (0.97, 0.98, 1.0), (0.42, 0.44, 0.50)
    top = v + 0.45
    d = 0.13
    _steel_lid_open(c, u, top + d - 0.01, w, 0.40)
    # stand: splayed legs, lower rail, fuel cans with flames
    for sx in (-1, 1):
        x0, x1 = u + sx * w * 0.44, u + sx * w * 0.50
        c.line(x0, v + 0.24, x1, v + 0.0, 0.026, scale(sr, 0.7))
        c.line(x0 - sx * 0.004, v + 0.24, x1 - sx * 0.004, v + 0.0, 0.010, mix(sl, sr, 0.3), 0.9)
    c.line(u - w * 0.47, v + 0.07, u + w * 0.47, v + 0.07, 0.016, scale(sr, 0.75))
    c.line(u - w * 0.47, v + 0.075, u + w * 0.47, v + 0.075, 0.006, sl, 0.8)
    soft_disc(c, u, v + 0.14, w * 0.45, 0.12, (1.0, 0.62, 0.18), 0.5, 1.7, add=True)
    for dx in (-0.2, 0.2):
        _cyl(c, u + dx * w, v + 0.075, 0.045, 0.05, (0.9, 0.7, 0.4), (0.4, 0.28, 0.14), (0.75, 0.55, 0.3))
        c.poly([(u + dx * w - 0.012, v + 0.135), (u + dx * w + 0.012, v + 0.135), (u + dx * w, v + 0.19)], (1.0, 0.62, 0.15), lift=0)
        c.poly([(u + dx * w - 0.006, v + 0.137), (u + dx * w + 0.006, v + 0.137), (u + dx * w, v + 0.165)], (0.5, 0.75, 1.0), lift=0, alpha=0.9)
    # water pan: front face
    y0, y1 = v + 0.23, top
    craft.hshade_box(c, u, (y0 + y1) / 2, w, y1 - y0, sl, sr)
    for x0, x1, al, col in ((-0.46, -0.38, 0.65, WHITE), (-0.10, -0.04, 0.22, WHITE), (0.22, 0.5, 0.22, (0.05, 0.05, 0.15))):
        c.rect(u + w * (x0 + x1) / 2, (y0 + y1) / 2, w * (x1 - x0), y1 - y0 - 0.01, col, lift=0, alpha=al)
    c.rect(u, y1 - 0.014, w, 0.026, mix(BRASS, WHITE, 0.15), lift=0.1)                                     # brass trim bands
    c.rect(u, y0 + 0.012, w, 0.022, scale(BRASS, 0.85), lift=0.06)
    c.rect(u, y1 - 0.0215, w, 0.006, scale(BRASS, 0.55), lift=0)
    c.rect(u, (y0 + y1) / 2 + 0.005, w * 0.2, 0.064, (0.98, 0.95, 0.88), r=0.006, lift=0.04)              # menu card
    c.rect(u, (y0 + y1) / 2 + 0.018, w * 0.14, 0.006, (0.4, 0.3, 0.25), lift=0, alpha=0.8)
    c.rect(u, (y0 + y1) / 2 - 0.004, w * 0.10, 0.005, (0.55, 0.45, 0.4), lift=0, alpha=0.7)
    for sx in (-1, 1):                                                                                     # side handles
        craft.arc(c, u + sx * w * 0.5, y0 + 0.07, 0.03, 0.05, -90 if sx > 0 else 90, 90 if sx > 0 else 270, 0.012, BRASS, 1.0, 8)
    # top face (rim) in perspective and the food heaped above the rim
    c.poly([(u - w * 0.50, top), (u + w * 0.50, top), (u + w * 0.45, top + d), (u - w * 0.45, top + d)], mix(sl, sr, 0.2), lift=0.1)
    c.poly([(u - w * 0.455, top + 0.012), (u + w * 0.455, top + 0.012), (u + w * 0.415, top + d - 0.012), (u - w * 0.415, top + d - 0.012)], (0.30, 0.32, 0.37), lift=0)
    _food_mound(c, u, top + d * 0.42, w * 0.41, d * 0.46, kind)
    c.poly([(u - w * 0.50, top), (u + w * 0.50, top), (u + w * 0.505, top + 0.012), (u - w * 0.505, top + 0.012)], WHITE, lift=0, alpha=0.55)
    # serving spoon with a long handle
    c.line(u - w * 0.05, top + d * 0.55, u + w * 0.5, top + d + 0.04, 0.012, (0.84, 0.86, 0.9))
    c.line(u - w * 0.05, top + d * 0.55 + 0.003, u + w * 0.5, top + d + 0.043, 0.004, WHITE, 0.8)
    c.ellipse(u - w * 0.06, top + d * 0.5, 0.032, 0.02, (0.9, 0.92, 0.96), angle=14, lift=0.14)
    steam(c, u, top + d * 0.9, 0.26, 0.035, 2, 0.13)


def _chafer_round(c, u, v, r, kind, metal):
    """A round chafing dish (handi style) with the lid propped open behind it, on a tripod ring stand."""
    sl, sr = metal
    top = v + 0.40
    _steel_lid_open(c, u, top + r * 0.75, r * 2.0, r * 1.4, round_lid=True)
    for sx in (-1, 0, 1):                                                                                   # tripod
        c.line(u + sx * r * 0.62, v + 0.20, u + sx * r * 0.78, v, 0.02 if sx else 0.014, scale(sr, 0.7))
    c.line(u - r * 0.66, v + 0.09, u + r * 0.66, v + 0.09, 0.012, scale(sr, 0.75))
    soft_disc(c, u, v + 0.15, r * 0.7, 0.10, (1.0, 0.62, 0.18), 0.55, 1.7, add=True)
    _cyl(c, u, v + 0.055, 0.045, 0.05, (0.9, 0.7, 0.4), (0.4, 0.28, 0.14), (0.75, 0.55, 0.3))
    c.poly([(u - 0.012, v + 0.11), (u + 0.012, v + 0.11), (u, v + 0.17)], (1.0, 0.62, 0.15), lift=0)
    # bowl body (curved sides, lit left)
    body = [(-r, top), (r, top), (r * 0.92, top - 0.07), (r * 0.74, top - 0.14), (r * 0.5, top - 0.19), (-r * 0.5, top - 0.19), (-r * 0.74, top - 0.14), (-r * 0.92, top - 0.07)]
    c.poly([(u + x, y) for x, y in body], mix(sl, sr, 0.45), lift=0.05)
    c.poly([(u + x * 0.98, y + 0.004) for x, y in [(-r, top), (-r * 0.3, top), (-r * 0.25, top - 0.19), (-r * 0.5, top - 0.19), (-r * 0.74, top - 0.14), (-r * 0.92, top - 0.07)]], sl, lift=0.1, alpha=0.8)
    c.poly([(u + x, y) for x, y in [(r * 0.35, top), (r, top), (r * 0.92, top - 0.07), (r * 0.74, top - 0.14), (r * 0.5, top - 0.19), (r * 0.3, top - 0.19)]], (0.08, 0.08, 0.15), lift=0, alpha=0.35)
    c.line(u - r * 0.8, top - 0.04, u - r * 0.62, top - 0.14, 0.011, WHITE, 0.6)
    c.rect(u, top - 0.095, r * 1.5, 0.008, scale(BRASS, 0.8), lift=0, alpha=0.85)
    for sx in (-1, 1):
        craft.arc(c, u + sx * r * 1.0, top - 0.04, 0.03, 0.04, -90 if sx > 0 else 90, 90 if sx > 0 else 270, 0.011, BRASS, 1.0, 8)
    # rim and food
    c.ellipse(u, top, r, r * TILT, scale(sr, 0.7), lift=0)
    c.ellipse(u, top + 0.004, r * 0.985, r * TILT * 0.97, mix(sl, sr, 0.15), lift=0.1)
    c.ellipse(u, top + 0.008, r * 0.88, r * TILT * 0.84, (0.28, 0.3, 0.35), lift=0)
    _food_mound(c, u, top + 0.012, r * 0.82, r * TILT * 0.8, kind)
    craft.arc(c, u, top + 0.004, r * 0.99, r * TILT * 0.97, 190, 350, r * 0.04, (1.0, 0.96, 0.8), 0.7, 8)
    steam(c, u, top + r * TILT * 0.9, 0.22, 0.03, 2, 0.12)


@sprop("cater_chafers", aspect=1.72, fill=0.97)
def cater_chafers(c, color):
    soft_disc(c, 0.0, 0.02, 0.95, 0.12, (1.0, 0.62, 0.2), 0.18, 1.7, add=True)                              # flame light on the cloth
    brass = ((0.96, 0.74, 0.34), (0.50, 0.34, 0.12))
    steel = ((0.97, 0.98, 1.0), (0.44, 0.46, 0.52))
    for dx, kind, metal in ((-0.50, "paneer", brass), (0.50, "dal", steel)):
        _chafer_round(c, dx, 0.05, 0.27, kind, metal)
    _chafer_rect(c, 0.0, 0.0, 0.62, "rice")


@sprop("cater_plates", aspect=0.95, fill=0.9)
def cater_plates(c, color):
    ao(c, 0.0, 0.0, 0.9, 0.22)
    # a stack of white plates with a gold rim: layered discs
    for k in range(9):
        y = 0.04 + k * 0.045
        c.ellipse(0.0, y, 0.40, 0.40 * TILT, scale((0.80, 0.80, 0.82), 0.9 - 0.01 * k), lift=0)
        c.ellipse(0.0, y + 0.012, 0.40, 0.40 * TILT, (0.98, 0.98, 0.97), lift=0.05)
    craft.arc(c, 0.0, 0.45, 0.39, 0.39 * TILT, 190, 350, 0.012, (0.92, 0.72, 0.3), 0.9, 10)
    c.ellipse(0.0, 0.46, 0.40, 0.40 * TILT, (0.82, 0.82, 0.84), lift=0)
    disc(c, 0.0, 0.47, 0.40, (0.99, 0.99, 0.98), TILT, 0.04, rim=False)
    c.ellipse(0.0, 0.475, 0.27, 0.27 * TILT, (0.92, 0.92, 0.92), lift=0)
    c.ellipse(0.0, 0.48, 0.255, 0.255 * TILT, (0.99, 0.99, 0.98), lift=0.04)
    craft.arc(c, 0.0, 0.475, 0.37, 0.37 * TILT, 0, 360, 0.01, (0.92, 0.72, 0.3), 0.9, 16)
    c.poly([(-0.37, 0.42), (-0.30, 0.42), (-0.28, 0.05), (-0.34, 0.05)], WHITE, lift=0, alpha=0.35)
    c.poly([(0.20, 0.42), (0.40, 0.42), (0.38, 0.05), (0.18, 0.05)], (0.3, 0.3, 0.35), lift=0, alpha=0.18)
    gloss(c, -0.1, 0.5, 0.14, 0.03, 8, 0.45)


@sprop("cater_dessert", aspect=0.95, fill=1.0)
def cater_dessert(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.8, 0.14)
    gold = (0.95, 0.76, 0.34)
    c.ellipse(0.0, 0.03, 0.18, 0.18 * TILT, scale(gold, 0.6), lift=0)
    craft.hshade_box(c, 0.0, 0.40, 0.035, 0.76, (1.0, 0.9, 0.6), (0.58, 0.40, 0.14))
    for v, r in ((0.12, 0.50), (0.43, 0.38), (0.71, 0.27)):
        c.ellipse(0.0, v - 0.025, r, r * 0.3, scale(gold, 0.55), lift=0)
        c.ellipse(0.0, v, r, r * 0.3, gold, lift=0.14)
        c.ellipse(0.0, v + 0.008, r * 0.95, r * 0.3 * 0.93, (0.98, 0.95, 0.9), lift=0.04)
    craft.arc(c, 0.0, 0.12, 0.47, 0.14, 200, 340, 0.01, (1.0, 0.9, 0.6), 0.7, 8)
    # bottom tier: gulab jamun, kaju katli diamonds; middle: cupcakes; top: strawberries
    for k in range(7):
        x = -0.38 + k * 0.126
        y = 0.13 + (0.035 if k % 2 else 0.0)
        _ball(c, x, y + 0.03, 0.045, (0.48, 0.20, 0.07), 0.9, 0.5, 0.5)
    for k in range(3):
        x = -0.15 + k * 0.15
        c.poly([(x - 0.045, 0.145), (x, 0.17), (x + 0.045, 0.145), (x, 0.12)], (0.92, 0.9, 0.72), lift=0.1)
        c.ellipse(x, 0.145, 0.012, 0.007, (0.8, 0.8, 0.8), lift=0)
    for k, x in enumerate((-0.25, -0.08, 0.1, 0.27)):
        y = 0.44 + (0.025 if k % 2 else 0.0)
        c.poly([(x - 0.04, y + 0.045), (x + 0.04, y + 0.045), (x + 0.03, y), (x - 0.03, y)], (0.85, 0.65, 0.35), lift=0.1)
        _ball(c, x, y + 0.075, 0.048, rng.choice([(0.96, 0.62, 0.74), (0.98, 0.9, 0.8), (0.6, 0.34, 0.2)]), 0.8, 0.6, 0.45)
        c.ellipse(x, y + 0.115, 0.011, 0.011, (0.8, 0.05, 0.1), lift=0.1)
    for k, x in enumerate((-0.12, 0.02, 0.14)):
        y = 0.72 + (0.02 if k == 1 else 0.0)
        _ball(c, x, y + 0.03, 0.04, (0.86, 0.12, 0.14), 0.95, 0.55, 0.5)
        leaf(c, x - 0.02, y + 0.07, 0.04, 60 + 40 * k, (0.2, 0.55, 0.2), 0.5)
    c.circle(0.0, 0.92, 0.03, gold, lift=0.2)


@sprop("cater_tiffin", aspect=0.72, fill=1.0)
def cater_tiffin(c, color):
    ao(c, 0.0, 0.0, 0.6, 0.12)
    left, right = (0.96, 0.97, 0.99), (0.44, 0.46, 0.52)
    c.ellipse(0.0, 0.03, 0.22, 0.22 * TILT, scale(right, 0.7), lift=0)
    for k in range(3):
        y0 = 0.03 + k * 0.28
        craft.hshade_box(c, 0.0, y0 + 0.13, 0.44, 0.24, left, right, r=0.015)
        c.poly([(-0.18, y0 + 0.22), (-0.13, y0 + 0.22), (-0.12, y0 + 0.04), (-0.17, y0 + 0.04)], WHITE, lift=0, alpha=0.65)
        c.ellipse(0.0, y0 + 0.255, 0.225, 0.225 * TILT, scale(right, 0.85), lift=0)
        c.ellipse(0.0, y0 + 0.27, 0.215, 0.215 * 0.32, mix(left, right, 0.2), lift=0.1)
        c.line(-0.22, y0 + 0.04, 0.22, y0 + 0.04, 0.012, scale(right, 0.8), 0.7)
    craft.arc(c, 0.0, 0.84, 0.25, 0.2, 0, 180, 0.018, scale(right, 0.8), 1.0, 10)           # carry handle
    craft.arc(c, 0.0, 0.84, 0.25, 0.2, 20, 120, 0.007, WHITE, 0.8, 8)
    c.rect(0.25, 0.30, 0.025, 0.58, scale(right, 0.8), lift=0.1)                               # side clips
    c.rect(-0.25, 0.30, 0.025, 0.58, mix(left, right, 0.3), lift=0.1)
    c.circle(0.0, 0.88, 0.03, scale(right, 0.8), lift=0.2)


@niche("catering", "Catering service", subjects=("cater_chafers",),
       strong=("catering service", "caterer", "caterers", "wedding catering", "party catering", "buffet", "tiffin service", "catering",
               "event catering", "outdoor catering", "केटरिंग", "कैटरिंग", "केटरर", "बफे", "टिफिन सर्विस", "खानसामा"),
       weak=("banquet food", "chafing dish", "live counter", "bulk food", "food for events", "halwai", "thali service", "hosting", "platters", "platter", "appetizers", "appetisers", "दावत", "रसोइये", "खाना बनाने"),
       accent="#ef6c00", mood="warm", group="food", avoid=("restaurant", "sweet shop"))
def catering(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.62)
        # draped curtain wall: irregular folds, each with a lit edge and a shadow edge, in the accent colour
        base = mix(P.accent, P.wall_bot, 0.5) if not dark else scale(P.accent, 0.5)
        u = -3.5
        while u < 6.5:
            wd = rng.uniform(0.09, 0.16)
            tone = rng.uniform(0.84, 1.08)
            S.rect(u + wd / 2, 0.32, wd, 0.74, scale(base, tone * 0.9), lift=0.0)
            S.rect(u + wd * 0.3, 0.32, wd * 0.28, 0.74, scale(mix(base, WHITE, 0.25), tone), lift=0.0, alpha=0.7)
            S.rect(u + wd * 0.88, 0.32, wd * 0.16, 0.74, scale(base, 0.55), lift=0.0, alpha=0.55)
            u += wd
        # gold-fringed swag valance with fairy lights
        for k in range(-8, 16):
            cu = -3.0 + k * 0.5
            S.ellipse(cu, 0.04, 0.27, 0.10, scale(base, 0.7), lift=0.0)
            S.ellipse(cu, 0.035, 0.24, 0.075, scale(mix(base, BRASS, 0.2), 1.05), lift=0.0, alpha=0.8)
            for j in range(9):
                S.circle(cu - 0.2 + j * 0.05, 0.135 - 0.02 * math.sin(j / 8.0 * math.pi), 0.008, BRASS, lift=0, soft=1.5)
            if dark or k % 2 == 0:
                S.glow(cu, 0.15, 0.10, (1.0, 0.85, 0.5), 0.5)
        S.rect(1.0, 0.0, 14.0, 0.05, scale(base, 0.55), lift=0.0)
        S.rect(1.0, 0.62, 14.0, 0.03, BRASS, lift=0.1)
        S.rect(1.0, 0.585, 14.0, 0.05, scale(BRASS, 0.5), lift=0.0, alpha=0.5)
        # tall flower stands at both sides (blurred colour)
        for u0 in (0.30, 1.92):
            S.rect(u0, 0.50, 0.03, 0.26, (0.7, 0.55, 0.3), lift=0)
            for k in range(12):
                S.circle(u0 + rng.uniform(-0.14, 0.14), 0.30 + rng.uniform(-0.09, 0.07), 0.055, rng.choice([(1.0, 0.8, 0.2), (0.95, 0.5, 0.2), (0.95, 0.9, 0.85), (0.9, 0.3, 0.4)]), lift=0.1)
        S.pendant(0.80, -0.1, 0.14, (1.0, 0.8, 0.5), 0.09)
        S.pendant(1.25, -0.1, 0.20, (1.0, 0.8, 0.5), 0.12)
        S.pendant(1.72, -0.1, 0.14, (1.0, 0.8, 0.5), 0.09)
        S.glow(1.25, 0.30, 0.9, (1.0, 0.8, 0.5), 0.22 if not dark else 0.34)
        S.bokeh(12, -0.2, 0.05, 2.3, 0.55, [(1.0, 0.85, 0.55), (1.0, 0.7, 0.4), (1.0, 0.95, 0.8)], 0.012, 0.04, 0.45)
        S.floor(0.62, P.floor_top, P.floor_bot)
    cloth = _cloth(P)
    S.floor(0.62, cloth, scale(cloth, 0.80))
    S.rect(1.0, 0.626, 14.0, 0.014, scale(cloth, 0.78), lift=0.0)
    # soft pleats of the cloth fanning out in perspective, with a faint woven motif that shrinks towards the back
    for k in range(-2, 8):
        x0 = -0.3 + k * 0.50 + rng.uniform(-0.08, 0.08)
        x1 = 1.05 + (x0 - 1.05) * 1.35
        S.line(x0, 0.65, x1, 0.92, 0.012, scale(cloth, 0.90), 0.20)
        S.line(x0 + 0.02, 0.65, x1 + 0.03, 0.92, 0.005, mix(cloth, WHITE, 0.6), 0.28)
    for row in range(4):
        vv = 0.655 + row * 0.022 + row * row * 0.012
        sc = 0.45 + (vv - 0.62) * 2.2
        for col in range(-6, 12):
            S.ellipse(1.05 + (col + (0.5 if row % 2 else 0.0)) * 0.30 * sc, vv, 0.022 * sc, 0.009 * sc, scale(cloth, 0.9), lift=0.0, alpha=0.35)
    run = P.accent if not dark else scale(P.accent, 0.55)
    S.rect(1.05, 0.835, 14.0, 0.29, mix(run, cloth, 0.15), lift=0.0)                                                # buffet runner in the accent
    for k in range(18):                                                                                           # runner weave
        x = rng.uniform(-0.2, 2.6)
        S.line(x, 0.72, x + rng.uniform(-0.03, 0.03), 0.97, 0.005, scale(run, rng.uniform(0.82, 1.15)), 0.3)
    for vy, wd2 in ((0.70, 0.008), (0.99, 0.008), (0.715, 0.004), (0.975, 0.004)):
        S.rect(1.05, vy, 14.0, wd2, BRASS, lift=0.0, alpha=0.9)
    for k in range(-1, 11):                                                                                       # gold motifs along the runner edge
        S.circle(-0.1 + k * 0.23, 0.742, 0.010, BRASS, lift=0, soft=1.5, alpha=0.8)
        S.circle(-0.1 + k * 0.23, 0.948, 0.010, BRASS, lift=0, soft=1.5, alpha=0.8)
    S.soft(1.1, 0.84, 1.2, 0.26, P.light, 0.30 if not dark else 0.46, 1.4, add=True)
    S.put("cater_dessert", 0.72, 0.88, 0.40)
    S.put("cater_plates", 1.46, 0.88, 0.20)
    S.put("cater_chafers", 1.10, 0.96, 0.46, subject=True)
    S.put("cater_tiffin", 1.64, 0.99, 0.18, framed=False)
    S.focus("detail", 1.10, 0.80)
    with S.near(16.0):
        S.soft(0.52, 1.03, 0.1, 0.07, (1.0, 0.8, 0.3), 0.7, 1.0)
        for k in range(3):
            _near_leaf(S, 1.78 + k * 0.04, 1.02, 0.26, 80 + k * 24, (0.2, 0.46, 0.18), 0.38)


# ---------------------------------------------------------------------------------------------- tent house / event rentals
@sprop("tent_mandap", aspect=1.6, fill=1.0)
def tent_mandap(c, color):
    rng = c.rng
    acc = color or (0.80, 0.12, 0.40)
    gold = (0.95, 0.74, 0.30)
    cloth = (0.98, 0.96, 0.93)
    ao(c, 0.0, 0.0, 1.7, 0.22)
    # platform: carpeted top, white front face with a gold edge, small steps
    c.poly([(-0.80, 0.12), (0.80, 0.12), (0.72, 0.30), (-0.72, 0.30)], scale(acc, 0.85), lift=0.1)
    soft_disc(c, 0.0, 0.2, 0.7, 0.06, WHITE, 0.12, 1.3, add=True)
    c.rect(0.0, 0.06, 1.60, 0.12, cloth, lift=0.06)
    c.rect(0.0, 0.123, 1.60, 0.016, gold, lift=0.1)
    for k in range(9):
        c.line(-0.72 + k * 0.18, 0.015, -0.72 + k * 0.18, 0.105, 0.005, scale(cloth, 0.8), 0.7)
    c.poly([(0.55, 0.0), (0.82, 0.0), (0.82, 0.04), (0.55, 0.04)], scale(cloth, 0.9), lift=0.05)
    # back panel with a flower motif
    c.poly([(-0.52, 0.31), (0.52, 0.31), (0.52, 0.86), (-0.52, 0.86)], mix(acc, WHITE, 0.15), lift=0.12)
    for k in range(7):
        c.line(-0.45 + k * 0.15, 0.31, -0.45 + k * 0.15, 0.86, 0.01, scale(acc, 0.8), 0.35)
    c.circle(0.0, 0.58, 0.20, scale(gold, 0.9), lift=0.12)
    c.circle(0.0, 0.58, 0.16, mix(acc, BLACK, 0.2), lift=0.1)
    for k in range(10):
        a = k * 0.63
        c.ellipse(math.cos(a) * 0.09, 0.58 + math.sin(a) * 0.09, 0.04, 0.03, (1.0, 0.82, 0.28), angle=math.degrees(a), lift=0.1)
    c.circle(0.0, 0.58, 0.035, (0.98, 0.5, 0.15), lift=0.1)
    # two royal chairs
    for x in (-0.20, 0.20):
        c.rect(x, 0.52, 0.17, 0.30, scale(acc, 0.55), r=0.04, lift=0.1)
        c.rect(x, 0.52, 0.13, 0.25, scale(acc, 0.95), r=0.03, lift=0.12)
        c.rect(x, 0.375, 0.20, 0.07, scale(acc, 0.7), r=0.02, lift=0.1)
        c.rect(x, 0.34, 0.22, 0.015, gold, lift=0.1)
    # back poles, front poles with spiral gold bands
    for x in (-0.50, 0.50):
        c.line(x, 0.30, x, 0.92, 0.018, scale(gold, 0.55))
    for x in (-0.74, 0.74):
        c.line(x, 0.12, x, 0.96, 0.034, scale(gold, 0.55))
        c.line(x - 0.005, 0.12, x - 0.005, 0.96, 0.022, gold)
        for k in range(14):
            c.line(x - 0.014, 0.14 + k * 0.058, x + 0.014, 0.17 + k * 0.058, 0.01, (1.0, 0.92, 0.6), 0.8)
        c.circle(x, 0.97, 0.03, gold, lift=0.2)
    # roof: white fabric canopy with tiered scalloped drapes and a gold trim
    c.poly([(-0.80, 0.90), (0.80, 0.90), (0.62, 1.05), (-0.62, 1.05)], scale(cloth, 0.93), lift=0.1)
    c.rect(0.0, 0.905, 1.62, 0.025, gold, lift=0.12)
    for k in range(8):                                                                       # scalloped swags
        x = -0.70 + k * 0.20
        c.ellipse(x, 0.87, 0.105, 0.08, cloth, lift=0.12)
        c.ellipse(x, 0.865, 0.10, 0.065, mix(cloth, acc, 0.12), lift=0.0, alpha=0.7)
        craft.arc(c, x, 0.87, 0.10, 0.075, 200, 340, 0.008, scale(cloth, 0.7), 0.7, 6)
    for k in range(18):                                                                      # marigold garlands hanging from the front edge
        x = -0.78 + k * 0.092
        for j in range(3):
            c.circle(x, 0.84 - j * 0.03, 0.017, (0.98, 0.58 - 0.08 * ((j + k) % 2), 0.08), lift=0.1)
    c.poly([(-0.10, 1.05), (0.10, 1.05), (0.0, 1.10)], gold, lift=0.15)
    soft_disc(c, -0.3, 0.97, 0.4, 0.06, WHITE, 0.3, 1.3, add=True)


@sprop("tent_chairs", aspect=1.9, fill=0.7)
def tent_chairs(c, color):
    rng = c.rng
    acc = color or (0.80, 0.12, 0.40)
    ao(c, 0.0, 0.0, 1.6, 0.30)

    def chair(u, v, k):
        soft_disc(c, u + 0.02 * k, v, 0.2 * k, 0.05 * k, BLACK, 0.3, 1.4)
        for x in (-0.07, 0.07):
            c.line(u + x * k, v + 0.01 * k, u + x * k, v + 0.17 * k, 0.015 * k, (0.78, 0.74, 0.62))
        c.poly([(u - 0.10 * k, v + 0.18 * k), (u + 0.10 * k, v + 0.18 * k), (u + 0.08 * k, v + 0.25 * k), (u - 0.08 * k, v + 0.25 * k)], (0.55, 0.52, 0.45), lift=0.05)
        c.rect(u, v + 0.38 * k, 0.17 * k, 0.28 * k, (0.98, 0.97, 0.95), r=0.04 * k, lift=0.10)           # fabric cover over the backrest
        c.rect(u + 0.055 * k, v + 0.38 * k, 0.05 * k, 0.28 * k, (0.5, 0.45, 0.4), r=0.0, lift=0, alpha=0.18)
        c.rect(u, v + 0.32 * k, 0.175 * k, 0.04 * k, acc, lift=0.12)                                      # sash
        c.ellipse(u, v + 0.325 * k, 0.04 * k, 0.03 * k, scale(acc, 0.9), lift=0.12)
        c.ellipse(u - 0.045 * k, v + 0.325 * k, 0.03 * k, 0.022 * k, scale(acc, 0.75), angle=25, lift=0.1)
        c.ellipse(u + 0.045 * k, v + 0.325 * k, 0.03 * k, 0.022 * k, scale(acc, 0.75), angle=-25, lift=0.1)
        soft_disc(c, u - 0.04 * k, v + 0.46 * k, 0.04 * k, 0.07 * k, WHITE, 0.3, 1.2, add=True)

    for i in range(4):
        chair(-0.50 + i * 0.33, 0.20, 0.82)                                                              # back row
    for i in range(4):
        chair(-0.54 + i * 0.36, 0.0, 1.0)                                                                # front row


@sprop("tent_speaker", aspect=0.62, fill=1.0)
def tent_speaker(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.7, 0.14)
    blk = (0.13, 0.13, 0.15)
    # tripod base, sub below and two tops on a pole
    for x in (-0.26, 0.0, 0.26):
        c.line(x * 0.2, 0.28, x, 0.03, 0.02, (0.25, 0.25, 0.28))
    def box(u, v, w, h):
        c.rect(u, v + h / 2, w, h, blk, r=0.02, lift=0.15)
        c.rect(u + w * 0.35, v + h / 2, w * 0.28, h * 0.96, BLACK, lift=0, alpha=0.30)
        c.rect(u - w / 2 + 0.01, v + h / 2, 0.012, h * 0.9, WHITE, lift=0, alpha=0.28)
        c.rect(u, v + h - 0.008, w, 0.014, (0.4, 0.4, 0.44), lift=0.0, alpha=0.8)
    box(0.0, 0.26, 0.46, 0.34)                                                       # subwoofer
    for r, col in ((0.14, (0.08, 0.08, 0.09)), (0.11, (0.22, 0.22, 0.25)), (0.06, (0.05, 0.05, 0.06))):
        c.circle(0.0, 0.43, r, col, lift=0.12)
    soft_disc(c, -0.04, 0.49, 0.06, 0.03, WHITE, 0.35, 1.2, add=True)
    c.line(0.0, 0.60, 0.0, 0.70, 0.025, (0.3, 0.3, 0.34))
    box(0.0, 0.69, 0.38, 0.30)                                                       # top cabinet
    c.circle(0.0, 0.80, 0.085, (0.2, 0.2, 0.23), lift=0.12)
    c.circle(0.0, 0.80, 0.05, (0.06, 0.06, 0.07), lift=0.1)
    c.circle(0.0, 0.93, 0.025, (0.75, 0.75, 0.8), lift=0.15)
    for k in range(5):
        c.circle(-0.12 + k * 0.06, 0.725, 0.006, (0.4, 0.4, 0.44), lift=0)


@sprop("tent_truss", aspect=4.0, fill=0.35)
def tent_truss(c, color):
    """A lighting truss with four spot lights (their beams are drawn by the scene)."""
    st = (0.74, 0.76, 0.80)
    c.line(-1.0, 0.18, 1.0, 0.18, 0.05, scale(st, 0.6))
    c.line(-1.0, 0.30, 1.0, 0.30, 0.05, scale(st, 0.85))
    for k in range(21):
        x = -1.0 + k * 0.1
        c.line(x, 0.18, x + 0.05, 0.30, 0.012, scale(st, 0.75))
        c.line(x + 0.05, 0.30, x + 0.1, 0.18, 0.012, scale(st, 0.75))
    for x in (-0.75, -0.25, 0.25, 0.75):
        c.line(x, 0.18, x, 0.10, 0.02, (0.25, 0.25, 0.28))
        c.poly([(x - 0.07, 0.10), (x + 0.07, 0.10), (x + 0.05, -0.04), (x - 0.05, -0.04)], (0.16, 0.16, 0.18), lift=0.15)
        c.ellipse(x, -0.04, 0.05, 0.02, (1.0, 0.96, 0.8), lift=0.1)
        soft_disc(c, x, -0.06, 0.12, 0.08, (1.0, 0.9, 0.6), 0.6, 1.6, add=True)


def _bunting(S, u0, u1, v, sag, n, cols, size=0.04):
    """A sagging string with pennant flags (works in any layer)."""
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        pts.append((u0 + (u1 - u0) * t, v + sag * 4 * t * (1 - t)))
    for a, b in zip(pts, pts[1:]):
        S.line(a[0], a[1], b[0], b[1], 0.003, (0.35, 0.28, 0.22))
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        mu, mv = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        S.poly([(mu - size * 0.5, mv), (mu + size * 0.5, mv + 0.002), (mu, mv + size * 1.25)], cols[i % len(cols)])


@niche("tent-house", "Tent house and event rentals", subjects=("tent_mandap",),
       strong=("tent house", "event rentals", "shamiana", "stage rental", "sound system rental", "chair rental", "tent and decoration", "pandal",
               "mandap decoration", "टेंट हाउस", "टेंट", "शामियाना", "पंडाल", "डीजे साउंड", "किराये पर", "कुर्सी किराये"),
       weak=("chairs", "tables on rent", "dj", "stage", "decoration", "wedding setup", "event equipment", "marquee"),
       accent="#ad1457", mood="light", group="events", avoid=("wedding planner", "photography"))
def tent_house(S):
    P = S.pal
    dark = _dark(P)
    rng = S.rng
    pen = [P.accent, (1.0, 0.78, 0.2), mix(P.accent, WHITE, 0.6), (0.2, 0.62, 0.5), (0.98, 0.5, 0.15)]
    with S.far():
        if dark:
            S.gradient_rect(-4.0, -0.4, 6.0, 0.62, (0.09, 0.09, 0.24), (0.46, 0.26, 0.38))
        else:
            S.gradient_rect(-4.0, -0.4, 6.0, 0.62, (0.60, 0.79, 0.95), (0.97, 0.93, 0.86))
        # tree line and a far tent
        for i in range(-12, 22):
            u = -3.0 + i * 0.26
            S.ellipse(u, 0.50, 0.22, 0.16 + 0.05 * ((i * 5) % 4) / 3.0, (0.20, 0.42, 0.22) if not dark else (0.05, 0.12, 0.1), lift=0.1)
        S.poly([(0.9, 0.50), (1.6, 0.50), (1.5, 0.34), (1.25, 0.24), (1.0, 0.34)], mix(P.paper, P.accent_light, 0.3), alpha=0.9)
        S.poly([(1.25, 0.24), (1.5, 0.34), (1.0, 0.34)], mix(P.accent, WHITE, 0.3), alpha=0.9)
        # the big tent canopy on top: white fabric with pole and swags
        cloth = _cloth(P)
        S.rect(1.0, -0.05, 14.0, 0.28, cloth, lift=0.0)
        for i in range(-30, 90):
            u = -3.0 + i * 0.16
            S.circle(u, 0.10, 0.10, cloth if i % 2 else mix(cloth, P.accent_light, 0.45), lift=0.05)
        S.rect(0.12, 0.40, 0.04, 0.8, (0.88, 0.86, 0.82) if not dark else (0.3, 0.3, 0.32), lift=0.05)
        S.rect(1.95, 0.40, 0.04, 0.8, (0.88, 0.86, 0.82) if not dark else (0.3, 0.3, 0.32), lift=0.05)
        _bunting(S, 0.12, 1.95, 0.16, 0.08, 14, pen, 0.06)
        for k in range(18):
            S.glow(0.2 + k * 0.1, 0.19 + 0.08 * 4 * (k / 18.0) * (1 - k / 18.0), 0.1, (1.0, 0.85, 0.5), 0.45 if not dark else 0.8)
        S.floor(0.56, P.floor_top, P.floor_bot)
    # lawn with mowing stripes
    gr = (0.50, 0.62, 0.36) if not dark else (0.09, 0.18, 0.10)
    if P.mood == "warm":
        gr = mix(gr, (0.6, 0.6, 0.25), 0.2)
    S.floor(0.56, scale(gr, 1.05), scale(gr, 0.74))
    for k in range(0, 14):
        S.rect(1.0, 0.60 + k * 0.14, 14.0, 0.07, scale(gr, 1.12 if not dark else 1.3), lift=0.0, alpha=0.30)
    S.rect(1.0, 0.56, 14.0, 0.006, scale(gr, 0.5), lift=0.0)
    carpet = mix(P.accent, (0.65, 0.05, 0.12), 0.35) if not dark else scale(P.accent, 0.6)
    S.poly([(0.99, 0.78), (1.11, 0.78), (1.30, 1.35), (0.80, 1.35)], carpet, alpha=1.0)                   # red-carpet aisle to the stage
    S.line(0.99, 0.78, 0.80, 1.35, 0.008, (1.0, 0.82, 0.35))
    S.line(1.11, 0.78, 1.30, 1.35, 0.008, (1.0, 0.82, 0.35))
    for _ in range(70):                                                                                # grass blades
        x, y = rng.uniform(-3.0, 5.0), rng.uniform(0.60, 1.8)
        S.line(x, y, x + rng.uniform(-0.01, 0.01), y - rng.uniform(0.01, 0.03), 0.003, scale(gr, rng.uniform(0.7, 1.25)), 0.5)
    S.soft(1.05, 0.90, 1.1, 0.24, P.light, 0.22 if not dark else 0.30, 1.5, add=True)
    # light truss above the stage with beams on the stage floor
    S.put("tent_truss", 1.05, 0.40, 0.14, shadow=False, framed=False)
    for x in (0.80, 0.95, 1.15, 1.30):
        S.light_shaft(x - 0.01, 0.38, x + 0.01, 0.38, x + 0.10 * (1 if x > 1.05 else -1) + 0.04, 0.78, x + 0.10 * (1 if x > 1.05 else -1) - 0.04, 0.78,
                      (1.0, 0.92, 0.7), 0.16 if not dark else 0.30)
    S.put("tent_speaker", 0.62, 0.84, 0.25)
    S.put("tent_speaker", 1.48, 0.84, 0.25)
    S.put("tent_mandap", 1.05, 0.82, 0.44, color=P.accent, subject=True)
    S.put("tent_chairs", 0.66, 1.00, 0.25, color=P.accent)
    S.put("tent_chairs", 1.44, 1.00, 0.25, color=P.accent)
    S.focus("detail", 1.05, 0.62)
    with S.near(16.0):
        _bunting(S, 1.35, 2.2, 0.0, 0.10, 6, pen, 0.14)
        S.soft(0.34, 1.04, 0.1, 0.08, (1.0, 0.8, 0.2), 0.7, 1.0)
