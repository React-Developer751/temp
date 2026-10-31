"""Buildings and storefronts (front view)."""
import math

from .core import REGISTRY, WHITE, mix, prop, scale


def _windows(c, u0, v0, cols, rows, du, dv, w, h, lit_seed, lit_prob=0.35, glass=None, lit=None):
    glass = glass or c.col((0.62, 0.80, 0.93))
    lit = lit or c.col((1.0, 0.85, 0.45))
    for r in range(rows):
        for k in range(cols):
            on = ((r * 7 + k * 13 + lit_seed) % 100) / 100.0 < lit_prob
            c.rect(u0 + k * du, v0 - r * dv, w, h, lit if on else glass, r=0.004, lift=0.18)


@prop("hotel", aspect=1.5, place="ground", nominal=0.5, fill=1.0, category="buildings", words=("resort", "motel", "inn", "lodge", "hostel", "guesthouse", "hospitality", "stay", "accommodation", "lodging"))
def hotel(c, color):
    c.shadow(0.0, 0.01, 1.7, 0.05)
    wall = c.pick(color, (0.93, 0.88, 0.80))
    c.rect(0.45, 0.22, 0.62, 0.42, scale(wall, 0.92), lift=0.1)                              # side wing
    c.rect(-0.10, 0.50, 0.95, 0.98, wall, lift=0.1)                                           # tower
    _windows(c, -0.46, 0.80, 6, 6, 0.145, 0.115, 0.075, 0.07, 3)
    c.rect(-0.10, 0.99, 1.0, 0.04, scale(wall, 0.75), lift=0)
    c.rect(-0.10, 0.93, 0.62, 0.11, c.col((0.14, 0.18, 0.32)), r=0.012, lift=0.1)             # sign
    if c.p.sign_text:
        c.text(c.p.sign_text, -0.10, 0.93, 0.055, c.col((1.0, 0.86, 0.35)), 0.17, max_w=0.56)
        c.p.sign_used = True
    for k in range(0 if c.p.sign_text else 5):
        pts = []
        for j in range(10):
            rad = 0.032 if j % 2 == 0 else 0.014
            a = math.radians(90 + 36 * j)
            pts.append((-0.34 + k * 0.12 + rad * math.cos(a), 0.93 + rad * math.sin(a)))
        c.poly(pts, c.col((1.0, 0.80, 0.22)), lift=0.05)
    c.rect(-0.10, 0.10, 0.50, 0.04, scale(wall, 0.7), lift=0.0)
    c.rect(-0.10, 0.045, 0.34, 0.09, c.col((0.35, 0.58, 0.78)), lift=0.2)                     # glass entrance
    c.rect(-0.10, 0.17, 0.52, 0.035, c.col((0.85, 0.25, 0.28)), lift=0.1)                     # canopy
    for u in (-0.32, 0.12):
        c.rect(u, 0.10, 0.02, 0.10, scale(wall, 0.8), lift=0)
    for k in range(3):
        c.rect(0.28 + k * 0.17, 0.30, 0.10, 0.12, c.col((0.62, 0.80, 0.93)), r=0.004, lift=0.18)
    c.rect(0.45, 0.46, 0.68, 0.03, scale(wall, 0.7), lift=0)


@prop("villa", aspect=1.8, place="ground", nominal=0.3, fill=0.62, category="buildings", words=("mansion", "bungalow", "penthouse", "realestate", "property", "estate", "properties", "residence", "homes", "cottage", "luxury", "architecture", "construction", "builder", "builders", "developer"))
def villa(c, color):
    c.shadow(0.0, 0.02, 1.9, 0.06)
    wall = c.pick(color, (0.97, 0.96, 0.94))
    wood = c.col((0.62, 0.42, 0.26))
    c.rect(-0.10, 0.22, 1.50, 0.40, wall, lift=0.08)
    c.rect(0.15, 0.52, 0.95, 0.30, scale(wall, 0.96), lift=0.08)
    c.rect(-0.10, 0.425, 1.62, 0.04, c.col((0.28, 0.30, 0.36)), lift=0.1)
    c.rect(0.15, 0.675, 1.05, 0.04, c.col((0.28, 0.30, 0.36)), lift=0.1)
    c.rect(0.25, 0.54, 0.70, 0.20, c.col((0.50, 0.75, 0.92)), lift=0.2)
    c.line(0.25, 0.44, 0.25, 0.64, 0.012, c.col((0.28, 0.30, 0.36)))
    c.line(0.60, 0.44, 0.60, 0.64, 0.012, c.col((0.28, 0.30, 0.36)))
    c.rect(-0.55, 0.22, 0.32, 0.24, c.col((0.50, 0.75, 0.92)), lift=0.2)
    c.rect(-0.15, 0.20, 0.20, 0.34, wood, lift=0.14)
    for k in range(5):
        c.rect(-0.15, 0.06 + k * 0.065, 0.20, 0.012, scale(wood, 0.7), lift=0)
    c.rect(0.50, 0.22, 0.52, 0.24, c.col((0.50, 0.75, 0.92)), lift=0.2)
    c.ellipse(0.30, 0.025, 0.58, 0.05, c.col((0.35, 0.78, 0.92)), lift=0.15)
    c.ellipse(0.30, 0.03, 0.50, 0.03, c.col((0.60, 0.90, 0.98)), lift=0)


@prop("apartment", aspect=0.75, place="ground", nominal=0.5, category="buildings", words=("flat", "flats", "condo", "tower", "residential", "highrise", "skyscraper", "society", "housing", "tenant", "rent", "rental"))
def apartment(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.05)
    wall = c.pick(color, (0.88, 0.62, 0.45))
    c.rect(0, 0.50, 0.70, 0.98, wall, lift=0.10)
    c.rect(0, 0.995, 0.76, 0.03, scale(wall, 0.65), lift=0)
    for r in range(8):
        for k in range(3):
            on = ((r * 5 + k * 11) % 9) < 3
            u, v = -0.22 + k * 0.22, 0.90 - r * 0.105
            c.rect(u, v, 0.13, 0.065, c.col((1.0, 0.85, 0.45)) if on else c.col((0.62, 0.80, 0.93)), lift=0.18)
            c.rect(u, v - 0.045, 0.17, 0.014, scale(wall, 0.6), lift=0)
    c.rect(0, 0.045, 0.16, 0.09, c.col((0.30, 0.22, 0.18)), lift=0.1)


@prop("university", aspect=2.0, place="ground", nominal=0.3, fill=0.6, category="buildings", words=("campus", "academy", "institute", "institution", "school", "college", "universities", "schools", "colleges", "varsity", "faculty", "iit"))
def university(c, color):
    c.shadow(0.0, 0.01, 2.1, 0.05)
    wall = c.pick(color, (0.94, 0.90, 0.82))
    brick = c.col((0.72, 0.40, 0.32))
    for sgn in (-1, 1):
        c.rect(sgn * 0.78, 0.28, 0.70, 0.52, brick, lift=0.1)
        for k in range(3):
            for r in range(2):
                c.rect(sgn * 0.78 + (k - 1) * 0.20, 0.38 - r * 0.20, 0.09, 0.12, c.col((0.62, 0.80, 0.93)), lift=0.18)
        c.rect(sgn * 0.78, 0.55, 0.74, 0.03, scale(brick, 0.7), lift=0)
    c.rect(0, 0.30, 0.92, 0.56, wall, lift=0.08)
    for k in range(6):
        c.rect(-0.35 + k * 0.14, 0.30, 0.055, 0.46, mix(wall, WHITE, 0.4), lift=0.14)
    c.rect(0, 0.58, 1.0, 0.05, scale(wall, 0.9), lift=0.1)
    c.poly([(-0.52, 0.60), (0.52, 0.60), (0.0, 0.90)], wall, lift=0.1)
    c.poly([(-0.40, 0.63), (0.40, 0.63), (0.0, 0.84)], scale(wall, 0.9), lift=0.0)
    c.circle(0, 0.70, 0.075, c.col((0.98, 0.98, 1.0)), lift=0.05)
    c.line(0, 0.70, 0, 0.745, 0.012, c.col((0.2, 0.2, 0.25)))
    c.line(0, 0.70, 0.03, 0.69, 0.012, c.col((0.2, 0.2, 0.25)))
    for k in range(4):
        c.rect(0, 0.015 + k * 0.014, 1.0 - k * 0.04, 0.014, scale(wall, 0.92 - 0.04 * k), lift=0)
    c.rect(0, 0.17, 0.12, 0.2, c.col((0.35, 0.25, 0.20)), lift=0.1)
    c.line(1.30, 0.04, 1.30, 0.80, 0.014, c.col((0.45, 0.47, 0.52)))
    c.poly([(1.30, 0.80), (1.52, 0.74), (1.30, 0.68)], c.col((0.88, 0.25, 0.25)), lift=0.1)


@prop("hospital", aspect=1.5, place="ground", nominal=0.4, category="buildings", words=("clinic", "polyclinic", "nursinghome", "dispensary", "diagnostic", "pathology", "lab", "laboratory"))
def hospital(c, color):
    c.shadow(0.0, 0.01, 1.7, 0.05)
    wall = c.pick(color, (0.96, 0.97, 0.99))
    c.rect(-0.45, 0.32, 0.62, 0.62, scale(wall, 0.96), lift=0.08)
    c.rect(0.28, 0.44, 0.95, 0.86, wall, lift=0.08)
    _windows(c, -0.62, 0.52, 3, 3, 0.17, 0.17, 0.09, 0.09, 5, 0.2)
    _windows(c, 0.02, 0.76, 5, 5, 0.17, 0.15, 0.09, 0.08, 9, 0.25)
    c.rect(0.28, 0.885, 0.97, 0.03, scale(wall, 0.75), lift=0)
    red = c.col((0.88, 0.20, 0.25))
    c.rect(0.28, 0.955, 0.2, 0.15, WHITE, r=0.015, lift=0.04)
    c.rect(0.28, 0.955, 0.12, 0.04, red, lift=0.05)
    c.rect(0.28, 0.955, 0.04, 0.10, red, lift=0.05)
    c.rect(0.28, 0.09, 0.32, 0.17, c.col((0.45, 0.72, 0.88)), lift=0.2)
    c.line(0.28, 0.005, 0.28, 0.175, 0.012, scale(wall, 0.6))
    c.rect(0.28, 0.19, 0.42, 0.03, red, lift=0.08)
    c.circle(-0.45, 0.38, 0.09, red, lift=0.1)
    c.rect(-0.45, 0.38, 0.11, 0.032, WHITE, lift=0)
    c.rect(-0.45, 0.38, 0.032, 0.11, WHITE, lift=0)


def _storefront(c, wall, awning_a, awning_b, icon, icon_color, display):
    c.shadow(0.0, 0.01, 1.4, 0.05)
    c.rect(0, 0.46, 1.2, 0.92, wall, lift=0.08)
    c.rect(0, 0.985, 1.26, 0.04, scale(wall, 0.7), lift=0)
    c.rect(0, 0.90, 0.78, 0.15, c.col((0.20, 0.22, 0.30)), r=0.02, lift=0.1)               # sign board
    sub = c.sub(-0.25, 0.83, 0.13)
    REGISTRY[icon].fn(sub, icon_color)
    if c.p.sign_text:
        c.text(c.p.sign_text, 0.12, 0.90, 0.07, c.col((0.98, 0.96, 0.9)), 0.17, max_w=0.44)
        c.p.sign_used = True
    else:
        for k, wd in enumerate((0.26, 0.20)):
            c.rect(0.10 + wd / 2 - 0.05, 0.92 - k * 0.06, wd, 0.03, c.col((0.96, 0.96, 0.98)), r=0.012, lift=0)
    n = 10
    for k in range(n):                                                                       # striped awning with scallops
        u = -0.60 + (k + 0.5) * 1.2 / n
        col = awning_a if k % 2 == 0 else awning_b
        c.rect(u, 0.66, 1.2 / n, 0.12, col, lift=0.12)
        c.ellipse(u, 0.60, 0.6 / n, 0.04, col, lift=0.12)
    c.rect(-0.15, 0.30, 0.78, 0.40, c.col((0.66, 0.84, 0.95)), r=0.02, lift=0.2)             # window
    c.rect(-0.15, 0.30, 0.82, 0.02, scale(wall, 0.6), lift=0)
    c.rect(-0.15, 0.12, 0.82, 0.05, scale(wall, 0.7), lift=0.1)
    display(c)
    c.rect(0.46, 0.27, 0.22, 0.46, c.col((0.60, 0.80, 0.92)), r=0.015, lift=0.2)             # door
    c.rect(0.46, 0.27, 0.26, 0.50, scale(wall, 0.6), r=0.015, lift=0.0, alpha=0.35)
    c.circle(0.54, 0.26, 0.013, c.col((0.9, 0.8, 0.3)), lift=0)
    c.rect(0.46, 0.38, 0.12, 0.05, c.col((0.96, 0.96, 0.98)), r=0.01, lift=0)
    c.rect(0.0, 0.015, 1.3, 0.03, c.col((0.60, 0.60, 0.66)), lift=0.1)


def _disp_cafe(c):
    for u in (-0.38, -0.12, 0.14):
        REGISTRY["coffee_cup"].fn(c.sub(u, 0.12, 0.17), None)


def _disp_bakery(c):
    REGISTRY["bread"].fn(c.sub(-0.38, 0.13, 0.22), None)
    REGISTRY["croissant"].fn(c.sub(-0.05, 0.13, 0.20), None)
    REGISTRY["cupcake"].fn(c.sub(0.22, 0.13, 0.20), None)


def _disp_restaurant(c):
    REGISTRY["glass"].fn(c.sub(-0.40, 0.13, 0.24), None)
    REGISTRY["plate"].fn(c.sub(-0.06, 0.13, 0.36), None)
    REGISTRY["candle"].fn(c.sub(0.28, 0.13, 0.16), None)


def _disp_shop(c):
    REGISTRY["tshirt"].fn(c.sub(-0.40, 0.13, 0.26), None)
    REGISTRY["shoppingbag"].fn(c.sub(-0.10, 0.13, 0.26), None)
    REGISTRY["giftbox"].fn(c.sub(0.18, 0.13, 0.20), None)


@prop("cafe", aspect=1.1, place="ground", nominal=0.64, category="buildings", words=("coffeeshop", "tearoom", "espressobar", "teashop", "chaishop", "cafeteria", "juicebar", "coffeehouse"))
def cafe(c, color):
    _storefront(c, c.col((0.96, 0.90, 0.80)), c.pick(color, (0.30, 0.55, 0.45)), c.col((0.97, 0.97, 0.95)), "coffee_cup", None, _disp_cafe)


@prop("bakery", aspect=1.1, place="ground", nominal=0.64, category="buildings", words=("bakeries", "patisserie", "confectionery", "sweets", "sweetshop", "pastries", "cakeshop", "dessertshop"))
def bakery(c, color):
    _storefront(c, c.col((0.99, 0.92, 0.88)), c.pick(color, (0.93, 0.45, 0.55)), c.col((0.98, 0.97, 0.95)), "bread", None, _disp_bakery)


@prop("restaurant", aspect=1.1, place="ground", nominal=0.64, category="buildings", words=("pizzeria", "diner", "bistro", "eatery", "dhaba", "brasserie", "steakhouse", "foodcourt", "takeaway", "canteen", "buffet"))
def restaurant(c, color):
    _storefront(c, c.col((0.86, 0.80, 0.72)), c.pick(color, (0.80, 0.22, 0.25)), c.col((0.98, 0.96, 0.92)), "plate", None, _disp_restaurant)


@prop("shop", aspect=1.1, place="ground", nominal=0.64, category="buildings", words=("store", "boutique", "mall", "supermarket", "market", "retail", "storefront", "shopfront", "showroom", "salon", "outlet", "kirana", "dukaan", "stall"))
def shop(c, color):
    _storefront(c, c.col((0.90, 0.92, 0.97)), c.pick(color, (0.25, 0.50, 0.90)), c.col((0.98, 0.98, 1.0)), "shoppingbag", None, _disp_shop)
