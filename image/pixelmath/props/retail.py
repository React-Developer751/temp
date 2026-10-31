"""Retail and product props."""
import math

from .core import WHITE, mix, prop, scale


@prop("shoe", aspect=2.1, place="table", nominal=0.25, fill=0.6, category="retail", words=("shoes", "sneaker", "sneakers", "footwear", "boot", "boots"))
def shoe(c, color):
    c.shadow(0.0, 0.02, 1.15, 0.10)
    upper = c.pick(color, (0.88, 0.22, 0.25))
    sole = c.col((0.97, 0.97, 0.98))
    c.poly([(-0.52, 0.10), (-0.50, 0.0), (0.46, 0.0), (0.58, 0.04), (0.60, 0.10), (-0.52, 0.12)], sole, lift=0.04)
    c.poly([(-0.52, 0.10), (0.58, 0.10), (0.60, 0.14), (-0.52, 0.16)], c.col((0.80, 0.82, 0.86)), lift=0)
    # upper: heel, collar, tongue, toe box
    c.poly([(-0.50, 0.14), (-0.52, 0.46), (-0.40, 0.52), (-0.22, 0.50), (-0.08, 0.44), (0.06, 0.38), (0.30, 0.30),
            (0.50, 0.20), (0.57, 0.14)], upper, lift=0.14)
    c.poly([(-0.22, 0.50), (-0.10, 0.56), (0.0, 0.46), (-0.08, 0.40)], scale(upper, 0.82), lift=0.05)        # tongue
    c.poly([(0.30, 0.30), (0.50, 0.20), (0.57, 0.14), (0.2, 0.14)], scale(upper, 1.12), lift=0.05)         # toe cap
    c.poly([(-0.34, 0.30), (-0.14, 0.24), (0.10, 0.14), (0.0, 0.14), (-0.30, 0.20)], c.col((0.99, 0.99, 1.0)), lift=0.0)   # side stripe
    for k in range(4):                                                                                      # laces
        t = k / 3.0
        u, v = -0.12 + 0.2 * t, 0.43 - 0.10 * t
        c.line(u - 0.05, v + 0.03, u + 0.04, v - 0.03, 0.022, c.col((0.97, 0.97, 0.99)))
    c.circle(-0.46, 0.34, 0.03, c.col((0.97, 0.97, 0.99)), lift=0)


@prop("shoppingbag", aspect=0.8, place="table", nominal=0.38, category="retail", words=("bag", "bags", "shopping", "handbag", "shoppingbags"))
def shoppingbag(c, color):
    c.shadow(0.02, 0.01, 0.75, 0.07)
    body = c.pick(color, (0.96, 0.45, 0.50))
    c.ring(0, 0.80, 0.17, 0.035, scale(body, 0.7))
    c.poly([(-0.34, 0.78), (0.34, 0.78), (0.31, 0.0), (-0.31, 0.0)], body, lift=0.12)
    c.poly([(0.34, 0.78), (0.31, 0.0), (0.12, 0.0), (0.18, 0.78)], scale(body, 0.88), lift=0.0, alpha=0.5)
    c.rect(0, 0.74, 0.68, 0.08, scale(body, 0.85), lift=0.05)
    c.circle(0, 0.40, 0.13, c.col((1.0, 1.0, 1.0)), lift=0.04)
    c.poly([(0, 0.325), (-0.07, 0.40), (-0.035, 0.455), (0, 0.425), (0.035, 0.455), (0.07, 0.40)], scale(body, 0.95), lift=0.0)
    c.circle(-0.035, 0.425, 0.035, scale(body, 0.95), lift=0)
    c.circle(0.035, 0.425, 0.035, scale(body, 0.95), lift=0)
    c.circle(-0.12, 0.78, 0.014, scale(body, 0.6), lift=0)
    c.circle(0.12, 0.78, 0.014, scale(body, 0.6), lift=0)


@prop("giftbox", aspect=1.0, place="table", nominal=0.36, category="retail", words=("gift", "present", "gifts", "giftboxes", "parcel"))
def giftbox(c, color):
    c.shadow(0.02, 0.01, 0.9, 0.08)
    box = c.pick(color, (0.88, 0.20, 0.28))
    gold = c.col((0.98, 0.82, 0.25))
    c.rect(0, 0.27, 0.80, 0.54, box, r=0.02, lift=0.10)
    c.rect(0, 0.60, 0.90, 0.15, scale(box, 0.9), r=0.02, lift=0.12)
    c.rect(0, 0.27, 0.13, 0.54, gold, lift=0.08)
    c.rect(0, 0.60, 0.13, 0.15, gold, lift=0.08)
    c.poly([(0.0, 0.70), (-0.05, 0.60), (-0.2, 0.62), (-0.3, 0.52), (-0.04, 0.70)], gold, lift=0)  # tails (hidden by bow)
    for sgn in (-1, 1):
        c.ellipse(sgn * 0.14, 0.78, 0.15, 0.075, gold, angle=sgn * 28, lift=0.12)
        c.ellipse(sgn * 0.14, 0.78, 0.09, 0.035, scale(gold, 0.82), angle=sgn * 28, lift=0)
    c.circle(0, 0.74, 0.055, scale(gold, 0.92), lift=0.15)
    c.rect(0.26, 0.27, 0.06, 0.54, WHITE, lift=0, alpha=0.12)


@prop("tshirt", aspect=1.0, place="table", nominal=0.36, category="retail", words=("shirt", "tshirts", "clothes", "clothing", "apparel", "shirts", "tee"))
def tshirt(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.07)
    col = c.pick(color, (0.25, 0.55, 0.90))
    c.poly([(-0.14, 0.92), (-0.30, 0.88), (-0.52, 0.72), (-0.42, 0.52), (-0.30, 0.60), (-0.30, 0.0), (0.30, 0.0),
            (0.30, 0.60), (0.42, 0.52), (0.52, 0.72), (0.30, 0.88), (0.14, 0.92)], col, lift=0.12)
    c.ellipse(0, 0.915, 0.14, 0.06, scale(col, 0.62), lift=0)
    c.ellipse(0, 0.90, 0.115, 0.045, scale(col, 0.42), lift=0)
    c.line(-0.30, 0.60, -0.41, 0.53, 0.012, scale(col, 0.78))
    c.line(0.30, 0.60, 0.41, 0.53, 0.012, scale(col, 0.78))
    c.circle(0, 0.58, 0.07, mix(col, WHITE, 0.7), lift=0.05)
    c.rect(0.15, 0.3, 0.05, 0.55, WHITE, lift=0, alpha=0.08)


@prop("watch", aspect=0.6, place="table", nominal=0.4, category="retail", words=("watches", "wristwatch", "clock", "clocks", "timepiece"))
def watch(c, color):
    c.shadow(0.0, 0.01, 0.5, 0.05)
    strap = c.pick(color, (0.20, 0.17, 0.16))
    c.rect(0, 0.84, 0.30, 0.34, strap, r=0.06, lift=0.12)
    c.rect(0, 0.16, 0.30, 0.34, strap, r=0.06, lift=0.12)
    for v in (0.07, 0.11, 0.89, 0.93):
        c.circle(0, v, 0.012, scale(strap, 1.8), lift=0)
    metal = c.col((0.86, 0.86, 0.90))
    c.rect(0.30, 0.5, 0.05, 0.1, scale(metal, 0.9), r=0.015)
    c.circle(0, 0.5, 0.30, metal, lift=0.15)
    c.circle(0, 0.5, 0.26, c.col((0.10, 0.12, 0.18)), lift=0.04)
    c.circle(0, 0.5, 0.235, c.col((0.97, 0.97, 0.99)), lift=0.04)
    for k in range(12):
        a = math.radians(k * 30)
        c.line(0.20 * math.sin(a), 0.5 + 0.20 * math.cos(a), 0.225 * math.sin(a), 0.5 + 0.225 * math.cos(a), 0.012, c.col((0.15, 0.15, 0.2)))
    c.line(0, 0.5, 0.0, 0.66, 0.02, c.col((0.12, 0.12, 0.16)))
    c.line(0, 0.5, 0.11, 0.45, 0.016, c.col((0.12, 0.12, 0.16)))
    c.line(0, 0.5, -0.08, 0.57, 0.008, c.col((0.85, 0.15, 0.15)))
    c.circle(0, 0.5, 0.02, c.col((0.12, 0.12, 0.16)), lift=0)


@prop("tag", aspect=0.7, place="table", nominal=0.36, category="retail", words=("sale", "discount", "offer", "price", "tags", "deal", "deals", "coupon"))
def tag(c, color):
    c.shadow(0.02, 0.0, 0.6, 0.06)
    col = c.pick(color, (0.90, 0.17, 0.22))
    c.path([(-0.06, 0.90), (-0.18, 1.0), (0.0, 1.08), (0.18, 1.0), (0.06, 0.90)], 0.018, c.col((0.35, 0.35, 0.4)))
    c.poly([(-0.28, 0.78), (-0.16, 0.90), (0.16, 0.90), (0.28, 0.78), (0.28, 0.0), (-0.28, 0.0)], col, lift=0.12)
    c.circle(0, 0.80, 0.045, c.col((0.96, 0.96, 0.98)), lift=0)
    white = c.col((1.0, 1.0, 1.0))
    word = c.p.sign_text if c.p.sign_text and len(c.p.sign_text) <= 9 else None
    if word:
        c.text(word, 0.0, 0.42, 0.16, white, 0.2, max_w=0.46)
        c.p.sign_used = True
    else:
        c.ring(-0.10, 0.52, 0.065, 0.035, white)
        c.ring(0.10, 0.26, 0.065, 0.035, white)
        c.line(0.13, 0.58, -0.13, 0.20, 0.04, white)
    c.rect(0.14, 0.4, 0.05, 0.7, WHITE, lift=0, alpha=0.08)


@prop("cart", aspect=1.3, place="ground", nominal=0.3, category="retail", words=("trolley", "carts", "basket", "checkout", "ecommerce"))
def cart(c, color):
    c.shadow(0.0, 0.01, 1.1, 0.07)
    col = c.pick(color, (0.15, 0.62, 0.70))
    dark = c.col((0.22, 0.24, 0.30))
    c.path([(-0.62, 0.92), (-0.50, 0.92), (-0.38, 0.62)], 0.035, dark, smooth=False)
    c.path([(-0.36, 0.30), (-0.30, 0.14), (0.40, 0.14)], 0.03, dark, smooth=False)
    c.poly([(-0.46, 0.68), (0.56, 0.68), (0.46, 0.30), (-0.34, 0.30)], col, lift=0.10)
    for k in range(-3, 4):
        c.line(k * 0.13 + 0.05, 0.66, k * 0.11 + 0.06, 0.32, 0.014, scale(col, 0.7))
    c.line(-0.40, 0.49, 0.51, 0.49, 0.014, scale(col, 0.7))
    c.circle(-0.18, 0.08, 0.07, dark, lift=0.05)
    c.circle(0.30, 0.08, 0.07, dark, lift=0.05)
    c.circle(-0.18, 0.08, 0.025, c.col((0.8, 0.82, 0.86)), lift=0)
    c.circle(0.30, 0.08, 0.025, c.col((0.8, 0.82, 0.86)), lift=0)
    c.circle(0.12, 0.60, 0.05, c.col((0.98, 0.78, 0.22)), lift=0.1)
    c.circle(0.26, 0.62, 0.05, c.col((0.88, 0.25, 0.25)), lift=0.1)
