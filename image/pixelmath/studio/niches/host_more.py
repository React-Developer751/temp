"""Hospitality and stay niches: cloud kitchen, tiffin service, chai stall, banquet hall, farm stay, PG and hostel (props prefixed host_)."""
import math

from .. import craft
from ..craft import BLACK, TILT, WHITE, ao, arc, disc, gloss, hshade_box, leaf, soft_disc, speckle, steam
from ..niches import niche
from ..stage import sprop
from ...raster import clamp, mix, scale

STEEL = (0.76, 0.79, 0.82)
KRAFT = (0.80, 0.62, 0.40)
BRASS = (0.86, 0.62, 0.24)


# ---------------------------------------------------------------------------------------------- shared helpers
def _span(S, pad=0.3):
    a, b = S.visible_u()
    return a - pad, b + pad


def _prism(c, u, v, w, h, dx, dy, front, top=None, side=None, lift=0.07, r=0.0):
    """Oblique box: front face w x h with its base centre at (u, v); the depth goes right and up by (dx, dy)."""
    x0, x1 = u - w / 2, u + w / 2
    top = top or mix(front, WHITE, 0.24)
    side = side or scale(front, 0.68)
    c.poly([(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], side, lift=lift)
    c.poly([(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, lift=0.04)
    c.rect(u, v + h / 2, w, h, front, lift=lift, r=r)


def _sphere(c, u, v, r, col, tilt=1.0, rim=0.62, hl=0.4):
    c.ellipse(u, v, r, r * tilt, scale(col, rim), lift=0)
    c.ellipse(u - r * 0.05, v + r * 0.06 * tilt, r * 0.94, r * 0.92 * tilt, col, lift=0.16)
    soft_disc(c, u + r * 0.28, v - r * 0.3 * tilt, r * 0.62, r * 0.5 * tilt, scale(col, 0.4), 0.40, 1.3)
    if hl:
        soft_disc(c, u - r * 0.34, v + r * 0.36 * tilt, r * 0.34, r * 0.22 * tilt, WHITE, hl, 1.1, add=True)


def _steel_surface(S, u0, u1, v0, v1, base=STEEL, front=None):
    """A brushed stainless counter top (v0 back edge, v1 front edge) with a lip and a front face running down to the bottom."""
    n = 5
    for k in range(n):                                                                                              # the top as a few flat bands (a cheap gradient)
        S.rect((u0 + u1) / 2, v0 + (k + 0.5) * (v1 - v0) / n, u1 - u0, (v1 - v0) / n + 0.002, scale(base, 1.07 - 0.26 * k / (n - 1)), lift=0.0)
    S.floor(v1 + 0.014, scale(front or base, 0.80), scale(front or base, 0.50))
    S.rect((u0 + u1) / 2, v1 + 0.007, u1 - u0, 0.016, scale(base, 1.12), lift=0.0)
    S.soft((u0 + u1) / 2 - 0.2, (v0 + v1) / 2, 0.55, (v1 - v0) * 0.45, WHITE, 0.26, 1.4, add=True)


# ================================================================================================ CLOUD KITCHEN
def _meal_box(c, u, v, w, h, d, band, kraft=KRAFT, lidh=0.30):
    """A sealed takeaway box: kraft body, a pressed lid with a seal strip and a coloured sleeve band."""
    _prism(c, u, v, w, h, d * 0.55, d * 0.42, kraft, top=mix(kraft, WHITE, 0.30), side=scale(kraft, 0.66), lift=0.06, r=0.006)
    c.rect(u, v + h - h * lidh / 2, w * 1.03, h * lidh, mix(kraft, WHITE, 0.14), lift=0.06, r=0.008)         # lid skirt
    c.line(u - w * 0.5, v + h * (1 - lidh), u + w * 0.5, v + h * (1 - lidh), 0.006, scale(kraft, 0.6), 0.7)
    sw = w * 0.20
    c.rect(u, v + h / 2, sw, h * 1.0, band, lift=0.1)                                                             # sleeve band
    c.poly([(u - sw / 2, v + h), (u + sw / 2, v + h), (u + sw / 2 + d * 0.55, v + h + d * 0.42), (u - sw / 2 + d * 0.55, v + h + d * 0.42)], scale(band, 1.1), lift=0)
    c.line(u - w * 0.5 + d * 0.25, v + h + d * 0.2, u + w * 0.5 + d * 0.25, v + h + d * 0.2, 0.004, mix(kraft, WHITE, 0.6), 0.6)
    c.ellipse(u - w * 0.30, v + h * 0.40, h * 0.12, h * 0.12, WHITE, lift=0.04, alpha=0.9)                        # seal sticker (plain disc)


@sprop("host_meal_boxes", aspect=1.72, fill=0.64)
def host_meal_boxes(c, color):
    band = color or (0.72, 0.20, 0.12)
    ao(c, -0.05, 0.0, 1.15, 0.30)
    # left stack of three, right stack of two, one lying box in front
    for i, (du, w) in enumerate(((-0.24, 0.50), (-0.21, 0.48), (-0.25, 0.46))):
        _meal_box(c, du, i * 0.185, w, 0.175, 0.30, band)
    for i, (du, w) in enumerate(((0.25, 0.46), (0.22, 0.44))):
        _meal_box(c, du, i * 0.185, w, 0.175, 0.30, scale(band, 0.92))
    _meal_box(c, 0.0, 0.0, 0.40, 0.12, 0.24, mix(band, (0.9, 0.7, 0.2), 0.45))
    # a clear lid window on the top box and a steam mark
    c.ellipse(-0.30, 0.575, 0.10, 0.02, (0.9, 0.95, 1.0), lift=0, alpha=0.4)


@sprop("host_handi", aspect=1.6, fill=0.66)
def host_handi(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.30)
    c.ellipse(0.0, 0.27, 0.46, 0.27, scale(BRASS, 0.55), lift=0)                                                   # body
    c.ellipse(-0.01, 0.285, 0.44, 0.255, BRASS, lift=0.2)
    soft_disc(c, 0.18, 0.12, 0.36, 0.14, (0.35, 0.18, 0.04), 0.5, 1.3)
    soft_disc(c, -0.22, 0.34, 0.14, 0.10, (1.0, 0.92, 0.6), 0.5, 1.1, add=True)
    for sgn in (-1, 1):                                                                                           # side handles
        c.ellipse(sgn * 0.47, 0.37, 0.05, 0.035, scale(BRASS, 0.6), lift=0)
        c.ellipse(sgn * 0.47, 0.375, 0.032, 0.02, (0.2, 0.12, 0.05), lift=0)
    disc(c, 0.0, 0.50, 0.33, mix(BRASS, WHITE, 0.1), TILT, 0.12)                                                  # neck rim
    c.ellipse(0.0, 0.505, 0.30, 0.30 * TILT, (0.93, 0.85, 0.66), lift=0.05)                                       # dough seal
    c.ellipse(0.0, 0.512, 0.265, 0.265 * TILT, (0.28, 0.17, 0.07), lift=0)
    c.ellipse(0.0, 0.506, 0.25, 0.25 * TILT, (0.97, 0.94, 0.84), lift=0.1)                                         # rice
    for _ in range(26):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        col = [(1.0, 0.66, 0.18), (0.95, 0.5, 0.15), (0.98, 0.93, 0.8), (0.55, 0.30, 0.12)][rng.randrange(4)]
        c.ellipse(math.cos(a) * 0.20 * q, 0.506 + math.sin(a) * 0.08 * q, 0.022, 0.011, col, lift=0.1, angle=rng.uniform(0, 180))
    c.ellipse(0.06, 0.53, 0.035, 0.02, (0.4, 0.2, 0.08), lift=0.1)
    # the lid leaning on the pot
    c.ellipse(0.40, 0.30, 0.11, 0.26, scale(BRASS, 0.55), angle=-14, lift=0)
    c.ellipse(0.395, 0.31, 0.095, 0.24, mix(BRASS, WHITE, 0.08), angle=-14, lift=0.18)
    c.ellipse(0.425, 0.31, 0.022, 0.022, scale(BRASS, 0.6), lift=0.1)
    steam(c, -0.02, 0.58, 0.36, 0.06, 1, 0.17)


@sprop("host_dessert_cups", aspect=1.55, fill=0.38)
def host_dessert_cups(c, color):
    acc = color or (0.72, 0.20, 0.12)
    ao(c, 0.0, 0.0, 0.95, 0.20)
    for i, du in enumerate((-0.30, 0.0, 0.30)):
        top = [(0.86, 0.30, 0.34), (0.95, 0.74, 0.30), mix(acc, WHITE, 0.15)][i]
        c.ellipse(du, 0.012, 0.085, 0.085 * TILT, (0.55, 0.62, 0.66), lift=0)
        c.poly([(du - 0.12, 0.34), (du + 0.12, 0.34), (du + 0.085, 0.015), (du - 0.085, 0.015)], (0.90, 0.95, 0.97), lift=0.06, alpha=0.9)
        c.poly([(du - 0.115, 0.27), (du + 0.115, 0.27), (du + 0.10, 0.20), (du - 0.10, 0.20)], (0.97, 0.94, 0.88), lift=0.05)                  # cream layer
        c.poly([(du - 0.10, 0.20), (du + 0.10, 0.20), (du + 0.085, 0.015), (du - 0.085, 0.015)], [(0.38, 0.20, 0.10), (0.45, 0.30, 0.16), scale(acc, 0.8)][i], lift=0.06)
        c.poly([(du - 0.118, 0.325), (du + 0.118, 0.325), (du + 0.115, 0.27), (du - 0.115, 0.27)], top, lift=0.08)
        c.poly([(du + 0.03, 0.34), (du + 0.12, 0.34), (du + 0.085, 0.015), (du + 0.02, 0.015)], BLACK, lift=0, alpha=0.12)
        c.poly([(du - 0.10, 0.33), (du - 0.07, 0.33), (du - 0.05, 0.03), (du - 0.07, 0.03)], WHITE, lift=0, alpha=0.5)
        c.ellipse(du, 0.34, 0.12, 0.12 * TILT, (0.82, 0.88, 0.9), lift=0, alpha=0.8)
        c.ellipse(du, 0.335, 0.105, 0.105 * TILT, top, lift=0.12)
        _sphere(c, du, 0.375, 0.03, (0.7, 0.08, 0.1), 0.95, hl=0.6)
    for k in range(3):                                                                                            # spare lids
        c.ellipse(0.62 - k * 0.0, 0.03 + k * 0.012, 0.13, 0.13 * TILT, (0.88, 0.93, 0.95), lift=0.08, alpha=0.8)


@sprop("host_delivery_bag", aspect=1.4, fill=0.66)
def host_delivery_bag(c, color):
    acc = color or (0.72, 0.20, 0.12)
    ao(c, 0.0, 0.0, 0.9, 0.30)
    _prism(c, 0.0, 0.0, 0.62, 0.50, 0.26, 0.16, acc, lift=0.1, r=0.03)
    c.rect(0.0, 0.47, 0.64, 0.12, scale(acc, 0.86), lift=0.08, r=0.03)                                            # flap
    c.line(-0.30, 0.41, 0.30, 0.41, 0.012, scale(acc, 0.55), 0.8)
    c.rect(0.0, 0.20, 0.64, 0.05, (0.92, 0.92, 0.88), lift=0.05)                                                  # reflective stripe
    c.rect(0.0, 0.20, 0.64, 0.008, (1.0, 1.0, 0.95), lift=0, alpha=0.8)
    c.ellipse(0.0, 0.32, 0.07, 0.04, mix(acc, WHITE, 0.7), lift=0.05)                                              # plain emblem disc
    craft.arc(c, 0.0, 0.58, 0.20, 0.12, 15, 165, 0.035, scale(acc, 0.5))                                          # carry handle
    soft_disc(c, -0.22, 0.30, 0.07, 0.3, WHITE, 0.25, 1.2, add=True)


@niche("cloud-kitchen", "Cloud kitchen", subjects=("host_meal_boxes",),
       strong=("cloud kitchen", "cloud kitchens", "ghost kitchen", "dark kitchen", "delivery only kitchen", "delivery kitchen", "virtual kitchen",
               "online food delivery kitchen", "cloud kitchen delivery", "meal boxes", "kitchen for delivery", "क्लाउड किचन", "घोस्ट किचन",
               "डार्क किचन", "डिलीवरी किचन", "cloud kitchen service", "cloud kitchen business"),
       weak=("delivery only", "food delivery", "sealed boxes", "order online", "kitchen", "multiple brands", "office lunch orders", "swiggy", "zomato",
             "डिलीवरी", "ऑनलाइन खाना", "meal box"),
       accent="#b8321f", mood="light", group="food",
       avoid=("dine in", "fine dining", "restaurant", "cafe", "catering", "tiffin", "dhaba", "banquet", "bakery", "sit down", "कैटरिंग"))
def cloud_kitchen(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.70)
        tile = mix(P.wall_top, WHITE, 0.4) if not dark else scale(P.wall_top, 1.25)
        S.rect((u0 + u1) / 2, 0.30, u1 - u0, 0.52, tile, lift=0.0)                                                  # subway tiles
        grout = scale(tile, 0.78 if not dark else 0.6)
        for r in range(0, 11):
            S.rect((u0 + u1) / 2, 0.06 + r * 0.052, u1 - u0, 0.004, grout, lift=0.0)
        for r in range(0, 11):
            for k in range(int((u1 - u0) / 0.14) + 2):
                S.rect(u0 + k * 0.14 + (0.07 if r % 2 else 0.0), 0.06 + r * 0.052 + 0.026, 0.004, 0.05, grout, lift=0.0)
        S.rect((u0 + u1) / 2, 0.58, u1 - u0, 0.05, P.accent, lift=0.04)                                              # accent band
        S.poly([(0.25, -0.1), (1.55, -0.1), (1.40, 0.14), (0.40, 0.14)], scale(STEEL, 0.8 if not dark else 0.5))     # extractor hood
        S.rect(0.9, 0.15, 1.2, 0.025, scale(STEEL, 0.55), lift=0.0)
        for k in range(5):
            S.glow(0.55 + k * 0.2, 0.17, 0.10, (1.0, 0.95, 0.8), 0.5)
        S.rect(1.55, 0.30, 0.80, 0.014, scale(STEEL, 0.9), lift=0.0)                                                # steel shelf with pots
        for k, uu in enumerate((1.30, 1.48, 1.66, 1.82)):
            S.rect(uu, 0.25, 0.12, 0.08 + 0.015 * (k % 2), scale(STEEL, 0.85 - 0.05 * k), r=0.01)
            S.rect(uu, 0.205, 0.13, 0.012, scale(STEEL, 1.1), lift=0.0)
        for k in range(6):                                                                                       # hanging ticket strips (plain bars)
            S.rect(0.30 + k * 0.07, 0.42, 0.045, 0.10 + 0.02 * (k % 3), (0.97, 0.95, 0.9), lift=0.0)
            S.rect(0.30 + k * 0.07, 0.40, 0.045, 0.012, P.accent_light, lift=0.0)
        S.rect(0.50, 0.365, 0.52, 0.010, scale(STEEL, 0.7), lift=0.0)
    _steel_surface(S, u0, u1, 0.70, 0.88, STEEL)
    for k in range(int((u1 - u0) / 0.5) + 1):
        S.rect(u0 + k * 0.5, 1.3, 0.006, 1.0, scale(STEEL, 0.5), lift=0.0, alpha=0.7)
        S.rect(u0 + k * 0.5 + 0.25, 1.02, 0.14, 0.014, scale(STEEL, 1.1), r=0.006, lift=0.0)
    S.put("host_handi", 0.93, 0.86, 0.26, shadow=False)
    S.put("host_meal_boxes", 1.30, 0.88, 0.43, color=P.accent, subject=True, shadow=False)
    S.put("host_delivery_bag", 1.66, 0.93, 0.23, color=P.accent, shadow=False)
    S.put("host_dessert_cups", 1.02, 1.00, 0.12, shadow=False)
    S.put("fastfood_burger", 1.36, 1.02, 0.12)
    S.focus("detail", 1.30, 0.74)
    with S.near(16.0):
        S.soft(0.70, 1.06, 0.14, 0.05, mix(STEEL, P.ink, 0.5), 0.55, 1.0)
        S.soft(1.86, 1.05, 0.10, 0.05, mix(P.accent, WHITE, 0.4), 0.35, 1.0)


# ================================================================================================ TIFFIN SERVICE
def _tiffin(c, u, v, w, h, n=3, tilt=0.0, warm=0.0):
    """A stainless steel tiffin carrier: n stacked bowls, rim bands, side clamp bars, a lid knob and a carry handle."""
    L = mix((0.95, 0.96, 0.97), (1.0, 0.85, 0.7), warm)
    R = mix((0.50, 0.54, 0.60), (0.7, 0.42, 0.30), warm)
    th = h * 0.80 / n
    base = v + h * 0.03
    for i in range(n):
        y = base + i * th
        hshade_box(c, u, y + th / 2, w * 0.90, th, L, R, r=0.012)
        c.rect(u - w * 0.30, y + th * 0.52, w * 0.035, th * 0.76, WHITE, lift=0, alpha=0.55)                          # vertical highlight
        c.rect(u + w * 0.34, y + th * 0.50, w * 0.05, th * 0.80, BLACK, lift=0, alpha=0.14)
        hshade_box(c, u, y + th * 0.06, w, th * 0.13, mix(L, WHITE, 0.2), scale(R, 1.1), r=0.006)                     # lower rim
        hshade_box(c, u, y + th * 0.96, w, th * 0.12, mix(L, WHITE, 0.3), scale(R, 1.15), r=0.006)                    # upper rim
        c.ellipse(u, y + th * 0.02, w * 0.5, w * 0.5 * TILT * 0.30, scale(R, 0.7), lift=0, alpha=0.7)
    top = base + n * th
    c.ellipse(u, top + h * 0.01, w * 0.46, w * 0.46 * TILT * 0.8, scale(R, 0.85), lift=0)                              # lid dome
    c.ellipse(u - w * 0.02, top + h * 0.02, w * 0.44, w * 0.44 * TILT * 0.8, mix(L, WHITE, 0.2), lift=0.16)
    soft_disc(c, u - w * 0.14, top + h * 0.03, w * 0.22, w * 0.05, WHITE, 0.55, 1.1, add=True)
    c.ellipse(u, top + h * 0.045, w * 0.07, w * 0.05, scale(R, 0.9), lift=0.12)                                        # knob
    for sgn in (-1, 1):                                                                                               # clamp bars + the handle
        c.line(u + sgn * w * 0.485, base, u + sgn * w * 0.485, top + h * 0.01, w * 0.035, scale(R, 0.85))
        c.line(u + sgn * w * 0.49, base, u + sgn * w * 0.49, top, w * 0.012, mix(L, WHITE, 0.4), 0.8)
        c.line(u + sgn * w * 0.485, top + h * 0.01, u + sgn * w * 0.20, top + h * 0.115, w * 0.03, scale(R, 0.9))
    c.line(u - w * 0.20, top + h * 0.115, u + w * 0.20, top + h * 0.115, w * 0.05, scale(R, 0.8))
    c.line(u - w * 0.20, top + h * 0.12, u + w * 0.20, top + h * 0.12, w * 0.016, mix(L, WHITE, 0.5), 0.9)


@sprop("host_tiffin_stack", aspect=1.05, fill=0.98)
def host_tiffin_stack(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.3)
    _tiffin(c, 0.14, 0.0, 0.50, 0.98, 3, warm=0.10)                                                                   # the big carrier
    _tiffin(c, -0.30, 0.0, 0.34, 0.66, 2, warm=0.10)                                                                  # a smaller one beside it
    for u in (-0.30, 0.14):
        pass


@sprop("host_steel_thali", aspect=2.3, fill=0.40)
def host_steel_thali(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.24)
    c.ellipse(0.0, 0.14, 0.48, 0.19, scale(STEEL, 0.55), lift=0)
    c.ellipse(0.0, 0.165, 0.47, 0.185, mix(STEEL, WHITE, 0.15), lift=0.18)
    c.ellipse(0.0, 0.17, 0.41, 0.158, scale(STEEL, 0.92), lift=0.1)
    soft_disc(c, 0.14, 0.12, 0.38, 0.10, (0.25, 0.28, 0.3), 0.35, 1.3)
    soft_disc(c, -0.20, 0.25, 0.22, 0.05, WHITE, 0.5, 1.1, add=True)
    for u, v, r, col, kind in ((-0.30, 0.22, 0.085, (0.96, 0.78, 0.18), "dal"), (-0.08, 0.27, 0.08, (0.35, 0.58, 0.2), "veg"),
                               (0.17, 0.26, 0.08, (0.95, 0.5, 0.2), "veg"), (0.36, 0.20, 0.07, (0.97, 0.96, 0.92), "curd")):
        c.ellipse(u, v - 0.012, r * 1.03, r * 0.50, scale(STEEL, 0.6), lift=0)
        c.ellipse(u, v, r, r * 0.46, mix(STEEL, WHITE, 0.25), lift=0.15)
        c.ellipse(u, v + 0.004, r * 0.82, r * 0.36, scale(col, 0.7), lift=0)
        c.ellipse(u, v + 0.012, r * 0.76, r * 0.32, col, lift=0.14)
        if kind == "veg":
            for _ in range(6):
                c.ellipse(u + rng.uniform(-r * 0.5, r * 0.5), v + 0.014 + rng.uniform(-r * 0.12, r * 0.15), r * 0.14, r * 0.07, scale(col, rng.uniform(0.7, 1.15)), lift=0.1)
        soft_disc(c, u - r * 0.3, v + r * 0.2, r * 0.4, r * 0.12, WHITE, 0.45, 1.1, add=True)
    # rice mound and a folded roti
    c.ellipse(-0.01, 0.15, 0.13, 0.055, (0.88, 0.86, 0.80), lift=0)
    c.ellipse(-0.02, 0.18, 0.115, 0.06, (0.99, 0.98, 0.94), lift=0.12)
    for _ in range(18):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        c.ellipse(-0.02 + math.cos(a) * 0.09 * q, 0.19 + math.sin(a) * 0.035 * q, 0.012, 0.005, (0.9, 0.88, 0.8), lift=0, alpha=0.7, angle=rng.uniform(0, 180))
    for k in range(3):
        c.poly([(0.20 + k * 0.01, 0.135 + k * 0.012), (0.34 + k * 0.01, 0.135 + k * 0.012), (0.37 + k * 0.01, 0.17 + k * 0.012), (0.17 + k * 0.01, 0.17 + k * 0.012)],
               (0.93, 0.76, 0.46), lift=0.12)
        c.line(0.18 + k * 0.01, 0.168 + k * 0.012, 0.36 + k * 0.01, 0.168 + k * 0.012, 0.006, (0.68, 0.45, 0.2), 0.6)
    c.ellipse(-0.20, 0.12, 0.05, 0.026, (0.97, 0.88, 0.25), lift=0.12)                                               # lemon
    c.ellipse(-0.20, 0.123, 0.034, 0.016, (1.0, 0.96, 0.6), lift=0)
    for k in range(3):
        c.ellipse(0.04 + k * 0.05, 0.095 + 0.01 * (k % 2), 0.028, 0.012, (0.88, 0.42, 0.55), lift=0.1)                # onion rings
    c.line(-0.46, 0.13, -0.36, 0.17, 0.014, (0.2, 0.55, 0.18))
    c.ellipse(0.0, 0.17, 0.455, 0.18, WHITE, lift=0, alpha=0.0)
    steam(c, -0.30, 0.30, 0.22, 0.035, 1, 0.14)
    steam(c, 0.17, 0.33, 0.22, 0.035, 1, 0.12)


@sprop("host_roti_tawa", aspect=2.0, fill=0.40)
def host_roti_tawa(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.24)
    # wooden chakla with the dough disc and a belan
    c.ellipse(-0.24, 0.09, 0.26, 0.105, (0.46, 0.30, 0.15), lift=0)
    c.ellipse(-0.24, 0.115, 0.26, 0.10, (0.78, 0.55, 0.30), lift=0.16)
    soft_disc(c, -0.2, 0.11, 0.2, 0.06, (0.5, 0.3, 0.1), 0.3, 1.3)
    c.ellipse(-0.24, 0.13, 0.19, 0.075, (0.95, 0.88, 0.72), lift=0.12)
    soft_disc(c, -0.3, 0.14, 0.1, 0.03, WHITE, 0.5, 1.1, add=True)
    c.line(-0.46, 0.20, -0.06, 0.17, 0.045, (0.55, 0.36, 0.18))
    c.line(-0.46, 0.205, -0.06, 0.175, 0.02, (0.88, 0.66, 0.40), 0.9)
    c.ellipse(-0.47, 0.20, 0.02, 0.026, (0.44, 0.27, 0.12), lift=0.1)
    c.ellipse(-0.05, 0.17, 0.02, 0.026, (0.44, 0.27, 0.12), lift=0.1)
    for _ in range(10):                                                                                               # flour dust
        c.ellipse(-0.24 + rng.uniform(-0.28, 0.28), 0.10 + rng.uniform(-0.01, 0.07), 0.01, 0.005, WHITE, lift=0, alpha=0.7)
    # the tawa with a puffed roti
    c.ellipse(0.25, 0.075, 0.30, 0.115, (0.07, 0.07, 0.08), lift=0)
    c.ellipse(0.25, 0.095, 0.29, 0.108, (0.20, 0.20, 0.22), lift=0.2)
    c.ellipse(0.25, 0.10, 0.25, 0.09, (0.11, 0.11, 0.12), lift=0.1)
    c.line(0.52, 0.11, 0.78, 0.17, 0.035, (0.16, 0.16, 0.18))
    c.ellipse(0.80, 0.17, 0.022, 0.02, (0.55, 0.55, 0.58), lift=0.1)
    c.ellipse(0.25, 0.14, 0.22, 0.09, (0.74, 0.48, 0.22), lift=0)
    c.ellipse(0.24, 0.16, 0.21, 0.09, (0.97, 0.80, 0.46), lift=0.2)
    soft_disc(c, 0.24, 0.20, 0.14, 0.04, (1.0, 0.95, 0.75), 0.5, 1.1, add=True)
    for _ in range(11):
        c.ellipse(0.24 + rng.uniform(-0.17, 0.17), 0.16 + rng.uniform(-0.05, 0.06), rng.uniform(0.012, 0.026), rng.uniform(0.007, 0.014), (0.55, 0.30, 0.1), lift=0, alpha=0.7)
    steam(c, 0.25, 0.26, 0.20, 0.04, 1, 0.14)


@sprop("host_veg_board", aspect=1.9, fill=0.34)
def host_veg_board(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.22)
    c.poly([(-0.44, 0.04), (0.44, 0.04), (0.50, 0.0), (-0.50, 0.0)], (0.40, 0.26, 0.12), lift=0)
    c.poly([(-0.40, 0.17), (0.40, 0.17), (0.46, 0.04), (-0.46, 0.04)], (0.80, 0.58, 0.32), lift=0.12)
    for k in range(5):
        c.line(-0.40 + k * 0.02 - 0.03, 0.15 - k * 0.025, 0.40 - k * 0.0 + 0.03, 0.15 - k * 0.025, 0.004, (0.62, 0.42, 0.2), 0.55)
    for k in range(4):                                                                                                # tomato slices
        c.ellipse(-0.30 + k * 0.05, 0.10 + 0.008 * (k % 2), 0.04, 0.02, (0.78, 0.12, 0.08), lift=0.1)
        c.ellipse(-0.30 + k * 0.05, 0.105 + 0.008 * (k % 2), 0.028, 0.012, (0.95, 0.4, 0.3), lift=0)
    for k in range(5):                                                                                                # onion rings
        c.ellipse(-0.02 + k * 0.045, 0.11 + 0.01 * (k % 2), 0.032, 0.015, (0.85, 0.45, 0.6), lift=0.1)
        c.ellipse(-0.02 + k * 0.045, 0.114 + 0.01 * (k % 2), 0.02, 0.008, (0.97, 0.9, 0.93), lift=0)
    for k in range(5):                                                                                                # carrot coins
        c.ellipse(0.22 + k * 0.035, 0.085 + 0.012 * (k % 2), 0.02, 0.011, (0.95, 0.5, 0.1), lift=0.1)
    for k in range(4):
        leaf(c, 0.12 + k * 0.05, 0.12, 0.14, 40 + k * 30, (0.20 + 0.05 * k, 0.55, 0.2), 0.45)
    _sphere(c, 0.34, 0.20, 0.07, (0.80, 0.14, 0.08), 0.92, hl=0.5)                                                    # whole tomato
    _sphere(c, 0.22, 0.20, 0.06, (0.80, 0.55, 0.65), 0.92, hl=0.4)                                                    # whole onion
    c.poly([(-0.42, 0.20), (-0.20, 0.19), (-0.20, 0.17), (-0.42, 0.17)], (0.8, 0.82, 0.86), lift=0.1)                 # knife blade
    c.rect(-0.46, 0.185, 0.10, 0.03, (0.35, 0.20, 0.10), lift=0.1, r=0.01)


@sprop("host_dabba_bag", aspect=1.1, fill=0.75)
def host_dabba_bag(c, color):
    acc = color or (0.72, 0.20, 0.12)
    ao(c, 0.0, 0.0, 0.8, 0.26)
    _tiffin(c, -0.14, 0.12, 0.30, 0.62, 2, warm=0.1)
    _tiffin(c, 0.14, 0.12, 0.28, 0.54, 2, warm=0.1)
    c.poly([(-0.34, 0.02), (0.34, 0.02), (0.38, 0.40), (-0.38, 0.40)], acc, lift=0.1)                                 # cloth bag
    c.poly([(0.06, 0.40), (0.38, 0.40), (0.34, 0.02), (0.04, 0.02)], BLACK, lift=0, alpha=0.18)
    c.rect(0.0, 0.17, 0.74, 0.04, mix(acc, (1.0, 0.9, 0.5), 0.45), lift=0.05)
    c.rect(0.0, 0.26, 0.76, 0.012, mix(acc, WHITE, 0.5), lift=0, alpha=0.8)
    c.ellipse(0.0, 0.40, 0.38, 0.04, scale(acc, 0.8), lift=0.1)
    for sgn in (-1, 1):
        craft.arc(c, sgn * 0.20, 0.40, 0.16, 0.18, 20, 160, 0.03, scale(acc, 0.62))
    soft_disc(c, -0.25, 0.22, 0.06, 0.2, WHITE, 0.25, 1.2, add=True)


@niche("tiffin-service", "Tiffin service", subjects=("host_tiffin_stack",),
       strong=("tiffin service", "tiffin services", "tiffin centre", "tiffin center", "dabba service", "dabbawala", "dabba wala", "home food delivery",
               "meal subscription", "lunch tiffin", "home style tiffin", "ghar ka khana", "टिफिन सर्विस", "डब्बा सर्विस", "डब्बावाला",
               "घर का खाना", "टिफिन सेवा", "monthly tiffin", "tiffin plan", "veg tiffin", "tiffin delivery", "tiffin box service", "office tiffin", "tiffin wala"),
       weak=("lunch box", "steel dabba", "home cooked", "ghar ka", "roti sabzi", "daily menu", "jain food", "डब्बा", "मेस", "mess", "thali delivery"),
       accent="#b8321f", mood="warm", group="food",
       avoid=("cloud kitchen", "ghost kitchen", "restaurant", "fine dining", "catering", "banquet", "cafe", "event catering", "बैंक्वेट", "कैटरिंग"))
def tiffin_service(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.60)
        for k in range(int((u1 - u0) / 0.16) + 2):                                                                    # warm plaster with a painted dado
            S.rect(u0 + k * 0.16, 0.44, 0.07, 0.30, mix(P.wall_bot, P.accent, 0.06), lift=0.0, alpha=0.5)
        S.rect((u0 + u1) / 2, 0.50, u1 - u0, 0.12, mix(P.wall_bot, P.accent, 0.35 if not dark else 0.55), lift=0.0)
        S.rect(0.55, 0.22, 0.46, 0.50, scale(P.ink, 2.0 if not dark else 1.0), r=0.01, lift=0.0)                     # window with a garden outside
        S.gradient_rect(0.35, 0.0, 0.75, 0.43, (0.60, 0.80, 0.95) if not dark else (0.15, 0.2, 0.4), (0.86, 0.94, 0.7) if not dark else (0.4, 0.4, 0.5))
        S.ellipse(0.45, 0.42, 0.16, 0.09, (0.25, 0.5, 0.2), lift=0.1)
        S.ellipse(0.65, 0.42, 0.14, 0.08, (0.32, 0.58, 0.24), lift=0.1)
        S.rect(0.55, 0.22, 0.01, 0.43, scale(P.ink, 2.0), lift=0.0)
        S.glow(0.55, 0.22, 0.9, P.light, 0.45)
        S.rect(1.55, 0.16, 0.9, 0.012, scale(P.surface, 0.8), lift=0.0)                                              # open shelves with steel containers
        S.rect(1.55, 0.36, 0.9, 0.012, scale(P.surface, 0.8), lift=0.0)
        for k, uu in enumerate((1.26, 1.42, 1.58, 1.74, 1.88)):
            S.rect(uu, 0.115, 0.10, 0.08, scale(STEEL, 0.8 + 0.06 * (k % 2)), r=0.01)
            S.rect(uu, 0.075, 0.108, 0.012, scale(STEEL, 1.1), lift=0.0)
            S.ellipse(uu, 0.30, 0.055, 0.05, [(0.9, 0.7, 0.3), (0.85, 0.3, 0.2), (0.9, 0.85, 0.7), (0.3, 0.55, 0.3), (0.9, 0.6, 0.2)][k], lift=0.12)
            S.rect(uu, 0.335, 0.05, 0.012, scale(STEEL, 0.7), lift=0.0)
        S.pendant(1.12, -0.1, 0.10, (1.0, 0.78, 0.45), 0.09)
        S.bokeh(8, 0.9, 0.02, 2.0, 0.55, [(1.0, 0.85, 0.55), (1.0, 0.72, 0.45), (0.5, 0.75, 0.4)], 0.012, 0.04)
    S.wood(u0, 0.60, u1, 2.8, scale(P.surface, 0.95), plank=0.16, grain=0.10)
    S.rect((u0 + u1) / 2, 0.60, u1 - u0, 0.010, scale(P.surface, 0.4), lift=0.0)
    cloth = mix(P.accent, P.paper, 0.2) if not dark else scale(P.accent, 0.7)                                         # checked table cloth
    S.rect(1.20, 0.90, 1.45, 0.66, cloth, lift=0.0)
    for k in range(0, 24):
        S.rect(0.48 + k * 0.062, 0.90, 0.016 if k % 2 else 0.03, 0.66, mix(cloth, WHITE, 0.55) if k % 2 else scale(cloth, 0.78), lift=0.0, alpha=0.55)
    for k in range(0, 12):
        S.rect(1.20, 0.60 + k * 0.06, 1.45, 0.016 if k % 2 else 0.03, mix(cloth, WHITE, 0.55) if k % 2 else scale(cloth, 0.78), lift=0.0, alpha=0.40)
    S.put("host_dabba_bag", 1.68, 0.84, 0.24, color=P.accent, shadow=False)
    S.put("host_roti_tawa", 0.94, 0.84, 0.20, shadow=False)
    S.put("host_tiffin_stack", 1.34, 0.93, 0.46, subject=True, shadow=False)
    S.put("host_steel_thali", 1.02, 1.02, 0.17, shadow=False)
    S.put("host_veg_board", 1.58, 1.04, 0.14, shadow=False)
    S.focus("detail", 1.30, 0.74)
    with S.near(16.0):
        S.soft(0.66, 1.06, 0.13, 0.06, (0.25, 0.5, 0.2), 0.45, 1.0)
        S.soft(1.86, 1.04, 0.10, 0.06, mix(P.accent, WHITE, 0.3), 0.40, 1.0)


# ================================================================================================ CHAI STALL
def _chai_glass(c, u, v, h, tea=(0.74, 0.42, 0.15), foam=True):
    tw, bw = h * 0.58, h * 0.40
    c.ellipse(u, v, bw * 0.55, bw * 0.55 * 0.3, (0.5, 0.55, 0.58), lift=0, alpha=0.8)
    c.poly([(u - tw / 2, v + h), (u + tw / 2, v + h), (u + bw / 2, v), (u - bw / 2, v)], (0.90, 0.94, 0.96), lift=0.04, alpha=0.75)
    ty = v + h * 0.80
    c.poly([(u - tw * 0.47, ty), (u + tw * 0.47, ty), (u + bw * 0.46, v + h * 0.04), (u - bw * 0.46, v + h * 0.04)], scale(tea, 0.8), lift=0.1)
    c.poly([(u - tw * 0.47, ty), (u + tw * 0.47, ty), (u + tw * 0.40, v + h * 0.45), (u - tw * 0.40, v + h * 0.45)], tea, lift=0.14)
    c.poly([(u + tw * 0.12, ty), (u + tw * 0.47, ty), (u + bw * 0.46, v + h * 0.04), (u + bw * 0.14, v + h * 0.04)], BLACK, lift=0, alpha=0.16)
    if foam:
        c.ellipse(u, ty, tw * 0.47, tw * 0.47 * 0.28, (0.93, 0.80, 0.60), lift=0.1)
        c.ellipse(u - tw * 0.03, ty + h * 0.008, tw * 0.36, tw * 0.36 * 0.24, (0.98, 0.9, 0.75), lift=0.1)
    c.poly([(u - tw * 0.40, v + h * 0.95), (u - tw * 0.30, v + h * 0.95), (u - bw * 0.28, v + h * 0.1), (u - bw * 0.38, v + h * 0.1)], WHITE, lift=0, alpha=0.55)
    c.ellipse(u, v + h, tw / 2, tw / 2 * 0.28, WHITE, lift=0, alpha=0.5)


@sprop("host_chai_kettle", aspect=1.30, fill=0.80)
def host_chai_kettle(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.32)
    c.poly([(-0.48, 0.0), (0.48, 0.0), (0.44, 0.13), (-0.44, 0.13)], (0.11, 0.11, 0.12), lift=0.14)                    # gas stove
    c.poly([(0.10, 0.13), (0.48, 0.0), (0.44, 0.13)], BLACK, lift=0, alpha=0.25)
    c.rect(-0.18, 0.06, 0.05, 0.05, (0.35, 0.36, 0.40), lift=0.2, r=0.012)                                                # knobs
    c.rect(0.02, 0.06, 0.05, 0.05, (0.35, 0.36, 0.40), lift=0.2, r=0.012)
    soft_disc(c, 0.0, 0.16, 0.50, 0.16, (1.0, 0.55, 0.18), 0.55, 1.3, add=True)
    for k in range(7):                                                                                                      # blue flames
        x = -0.21 + k * 0.07
        c.poly([(x - 0.022, 0.10), (x + 0.022, 0.10), (x + 0.004 * (k - 3), 0.19)], (0.30, 0.50, 1.0), lift=0, alpha=0.95)
        c.poly([(x - 0.01, 0.10), (x + 0.01, 0.10), (x, 0.15)], (0.85, 0.92, 1.0), lift=0, alpha=0.9)
    c.rect(0.0, 0.135, 0.84, 0.014, (0.28, 0.28, 0.30), lift=0.1)
    # the kettle: steel body with a soot-blackened bottom, spout, wooden handle, lid and knob
    L, R = (0.92, 0.93, 0.94), (0.46, 0.48, 0.52)
    hshade_box(c, 0.0, 0.34, 0.60, 0.40, L, R, r=0.07)
    hshade_box(c, 0.0, 0.195, 0.60, 0.10, (0.16, 0.12, 0.09), (0.05, 0.04, 0.03), r=0.05, alpha=0.78)                   # soot on the bottom
    c.poly([(-0.26, 0.50), (-0.20, 0.50), (-0.19, 0.18), (-0.24, 0.20)], WHITE, lift=0, alpha=0.55)
    c.line(-0.30, 0.40, 0.30, 0.40, 0.008, (0.3, 0.3, 0.34), 0.4)
    c.poly([(-0.27, 0.46), (-0.45, 0.62), (-0.485, 0.60), (-0.30, 0.36)], mix(L, R, 0.35), lift=0.1)                      # spout
    c.line(-0.46, 0.612, -0.30, 0.45, 0.008, WHITE, 0.5)
    c.ellipse(-0.47, 0.614, 0.02, 0.012, (0.15, 0.12, 0.1), lift=0)
    c.ellipse(0.0, 0.54, 0.30, 0.055, scale(R, 0.7), lift=0)                                                              # lid
    c.ellipse(0.0, 0.552, 0.27, 0.05, mix(L, R, 0.2), lift=0.16)
    c.ellipse(0.0, 0.575, 0.085, 0.032, mix(L, R, 0.3), lift=0.1)
    c.circle(0.0, 0.62, 0.032, (0.12, 0.09, 0.07), lift=0.2)
    c.poly([(0.28, 0.46), (0.54, 0.60), (0.52, 0.645), (0.27, 0.52)], (0.28, 0.17, 0.09), lift=0.12)                      # wooden handle
    c.line(0.30, 0.52, 0.52, 0.635, 0.008, (0.7, 0.5, 0.3), 0.6)
    c.line(0.28, 0.49, 0.32, 0.49, 0.03, (0.5, 0.5, 0.54))
    steam(c, -0.47, 0.66, 0.26, 0.05, 1, 0.17)


@sprop("host_chai_glasses", aspect=1.55, fill=0.34)
def host_chai_glasses(c, color):
    ao(c, 0.0, 0.0, 1.0, 0.24)
    c.ellipse(0.0, 0.035, 0.50, 0.12, (0.55, 0.58, 0.62), lift=0)                                                         # steel tray
    c.ellipse(0.0, 0.05, 0.49, 0.115, (0.80, 0.83, 0.86), lift=0.16)
    c.ellipse(0.0, 0.055, 0.42, 0.09, (0.68, 0.71, 0.75), lift=0.1)
    soft_disc(c, -0.2, 0.09, 0.2, 0.03, WHITE, 0.5, 1.1, add=True)
    for k, (du, dv, th) in enumerate(((-0.27, 0.035, 0.27), (0.0, 0.01, 0.30), (0.27, 0.035, 0.27))):
        _chai_glass(c, du, 0.04 + dv, th, tea=[(0.74, 0.42, 0.15), (0.70, 0.36, 0.12), (0.78, 0.46, 0.18)][k])


@sprop("host_bun_maska", aspect=1.8, fill=0.26)
def host_bun_maska(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.22)
    c.ellipse(0.0, 0.03, 0.46, 0.14, (0.84, 0.85, 0.86), lift=0)
    c.ellipse(0.0, 0.045, 0.45, 0.13, (0.97, 0.97, 0.96), lift=0.1)
    c.ellipse(0.0, 0.05, 0.36, 0.095, (0.88, 0.89, 0.9), lift=0)
    for k, (du, sh) in enumerate(((-0.17, 1.0), (0.16, 0.95))):                                                           # buns, one cut open
        c.ellipse(du, 0.10, 0.16, 0.06, (0.55, 0.30, 0.10), lift=0)
        c.ellipse(du, 0.14, 0.15 * sh, 0.09 * sh, (0.80, 0.50, 0.20), lift=0.18)
        c.ellipse(du - 0.03, 0.17, 0.10, 0.04, (0.96, 0.74, 0.40), lift=0.1)
        soft_disc(c, du - 0.05, 0.19, 0.06, 0.022, WHITE, 0.5, 1.1, add=True)
    c.ellipse(-0.17, 0.115, 0.14, 0.035, (0.98, 0.9, 0.66), lift=0.05)                                                    # cut face + butter
    c.rect(-0.17, 0.135, 0.12, 0.035, (1.0, 0.88, 0.35), lift=0.14, r=0.008)
    c.rect(-0.185, 0.145, 0.05, 0.012, (1.0, 0.96, 0.7), lift=0, alpha=0.8)
    for k in range(2):                                                                                                    # toast
        c.poly([(0.30 + k * 0.03, 0.13), (0.42 + k * 0.03, 0.13), (0.38 + k * 0.03, 0.20), (0.26 + k * 0.03, 0.20)], (0.85, 0.60, 0.28), lift=0.12)
        c.poly([(0.30 + k * 0.03, 0.135), (0.40 + k * 0.03, 0.135), (0.37 + k * 0.03, 0.19), (0.28 + k * 0.03, 0.19)], (0.96, 0.80, 0.5), lift=0.05)
    for _ in range(6):
        c.ellipse(rng.uniform(-0.35, 0.35), 0.05 + rng.uniform(-0.01, 0.03), 0.008, 0.004, (0.85, 0.6, 0.3), lift=0, alpha=0.8)


@sprop("host_pakoda_cone", aspect=1.45, fill=0.50)
def host_pakoda_cone(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.26)
    # a steel plate of samosas on the right, a paper cone of pakodas on the left
    c.ellipse(0.26, 0.04, 0.34, 0.10, (0.55, 0.58, 0.62), lift=0)
    c.ellipse(0.26, 0.055, 0.33, 0.095, (0.82, 0.85, 0.88), lift=0.15)
    c.ellipse(0.26, 0.06, 0.26, 0.07, (0.70, 0.73, 0.77), lift=0.1)
    for k, du in enumerate((0.12, 0.28, 0.20)):
        dv = 0.10 + (0.05 if k == 2 else 0.0)
        c.poly([(0.08 + k * 0.14 - (0.07 if k == 2 else 0.0), 0.07 + (0.04 if k == 2 else 0)), (0.30 + k * 0.14 - (0.07 if k == 2 else 0.0) - 0.0, 0.07 + (0.04 if k == 2 else 0)),
                (0.19 + k * 0.14 - (0.07 if k == 2 else 0.0), 0.20 + (0.04 if k == 2 else 0))], (0.78, 0.48, 0.18), lift=0.1)
        c.poly([(0.10 + k * 0.14 - (0.07 if k == 2 else 0.0), 0.08 + (0.04 if k == 2 else 0)), (0.27 + k * 0.14 - (0.07 if k == 2 else 0.0), 0.08 + (0.04 if k == 2 else 0)),
                (0.19 + k * 0.14 - (0.07 if k == 2 else 0.0), 0.185 + (0.04 if k == 2 else 0))], (0.93, 0.68, 0.30), lift=0.12)
    c.poly([(-0.52, 0.34), (-0.05, 0.46), (-0.03, 0.30), (-0.30, 0.02)], (0.93, 0.89, 0.78), lift=0.1)                       # paper cone
    c.poly([(-0.52, 0.34), (-0.30, 0.02), (-0.34, 0.02), (-0.52, 0.30)], BLACK, lift=0, alpha=0.12)
    c.poly([(-0.30, 0.02), (-0.03, 0.30), (-0.05, 0.31), (-0.28, 0.06)], scale((0.93, 0.89, 0.78), 0.78), lift=0, alpha=0.9)
    for k in range(5):
        c.line(-0.46 + k * 0.07, 0.31 - k * 0.04, -0.40 + k * 0.07, 0.25 - k * 0.04, 0.005, (0.75, 0.70, 0.60), 0.5)
    for _ in range(16):                                                                                                   # pakodas
        u, v = rng.uniform(-0.52, -0.05), rng.uniform(0.33, 0.44)
        if u > -0.28 and v > 0.40:
            continue
        r = rng.uniform(0.032, 0.055)
        _sphere(c, u, v - (u + 0.5) * 0.05 + 0.04, r, mix((0.72, 0.45, 0.16), (0.90, 0.62, 0.22), rng.random()), 0.85, hl=0.25)
    c.ellipse(0.55, 0.05, 0.07, 0.03, (0.3, 0.55, 0.2), lift=0.1)                                                         # chutney
    c.ellipse(0.55, 0.06, 0.05, 0.02, (0.4, 0.7, 0.25), lift=0.1)


@sprop("host_paper_cups", aspect=1.0, fill=0.52)
def host_paper_cups(c, color):
    acc = color or (0.71, 0.32, 0.11)
    ao(c, 0.0, 0.0, 0.9, 0.26)
    for u, h, n in ((-0.20, 0.50, 5), (0.20, 0.34, 3)):
        tw, bw = 0.34, 0.24
        c.ellipse(u, 0.0, bw / 2, bw / 2 * TILT * 0.8, scale((0.9, 0.9, 0.88), 0.7), lift=0)
        c.poly([(u - tw / 2, h), (u + tw / 2, h), (u + bw / 2, 0.01), (u - bw / 2, 0.01)], (0.96, 0.95, 0.92), lift=0.06)
        c.poly([(u - tw * 0.47, h * 0.78), (u + tw * 0.47, h * 0.78), (u + bw * 0.55, h * 0.52), (u - bw * 0.55, h * 0.52)], acc, lift=0.1)
        c.poly([(u + tw * 0.12, h), (u + tw / 2, h), (u + bw / 2, 0.01), (u + bw * 0.14, 0.01)], BLACK, lift=0, alpha=0.14)
        c.poly([(u - tw * 0.4, h * 0.96), (u - tw * 0.3, h * 0.96), (u - bw * 0.28, 0.04), (u - bw * 0.38, 0.04)], WHITE, lift=0, alpha=0.55)
        for k in range(n):                                                                                                  # rims of the stacked cups
            y = h + k * 0.012 * 0 + (k * 0.02)
            c.ellipse(u, y, tw / 2 + 0.005, tw / 2 * 0.22, (0.82, 0.8, 0.76), lift=0, alpha=1.0 if k == n - 1 else 0.7)
        c.ellipse(u, h + (n - 1) * 0.02 + 0.004, tw / 2 - 0.012, tw / 2 * 0.17, (0.3, 0.2, 0.12), lift=0)
    c.ellipse(0.0, 0.03, 0.40, 0.10, (0.9, 0.9, 0.9), lift=0, alpha=0.0)


@sprop("host_biscuit_jar", aspect=1.05, fill=0.55)
def host_biscuit_jar(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.22)
    for u, h, col, kind in ((-0.22, 0.52, (0.86, 0.62, 0.30), "rusk"), (0.24, 0.42, (0.93, 0.78, 0.45), "biscuit")):
        c.rect(u, h / 2, 0.38, h, (0.88, 0.93, 0.95), lift=0.04, r=0.05, alpha=0.7)
        c.rect(u, h * 0.4, 0.34, h * 0.76, scale(col, 0.78), lift=0.06, r=0.04)
        for _ in range(9):
            c.rect(u + rng.uniform(-0.13, 0.13), rng.uniform(0.06, h * 0.72), 0.10 if kind == "rusk" else 0.07, 0.045 if kind == "rusk" else 0.07, col, lift=0.2, r=0.012)
        c.rect(u + 0.12, h / 2, 0.06, h, BLACK, lift=0, alpha=0.12)
        c.rect(u - 0.12, h * 0.55, 0.03, h * 0.8, WHITE, lift=0, alpha=0.5)
        c.rect(u, h + 0.03, 0.40, 0.05, scale((0.75, 0.55, 0.2), 0.9), lift=0.15, r=0.02)
        c.circle(u, h + 0.07, 0.03, (0.45, 0.30, 0.12), lift=0.12)


@niche("chai-stall", "Chai stall / tea stall", subjects=("host_chai_kettle",),
       strong=("chai stall", "tea stall", "chai tapri", "chai ki tapri", "chai wala", "chaiwala", "chai shop", "tea stall", "cutting chai", "tapri",
               "chai point", "chai corner", "masala chai stall", "चाय की टपरी", "चाय टपरी", "चाय वाला", "चायवाला", "चाय की दुकान", "कटिंग चाय", "चाय स्टॉल",
               "tea shop", "tea vendor"),
       weak=("kadak chai", "bun maska", "pakoda", "samosa", "masala chai", "kulhad", "lemon tea", "cold coffee", "चाय", "पकोड़ा", "समोसा", "बन मस्का", "adrak chai"),
       accent="#b5521b", mood="warm", group="food",
       avoid=("cafe", "coffee shop", "espresso", "barista", "street food", "chaat", "golgappa", "restaurant", "bakery", "tea estate", "tea garden", "tea plantation",
              "चाट", "गोलगप्पे", "कैफे"))
def chai_stall(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    rng = S.rng
    with S.far():
        sky_t = (0.98, 0.78, 0.50) if not dark else (0.10, 0.12, 0.26)
        sky_b = (1.0, 0.92, 0.72) if not dark else (0.42, 0.30, 0.36)
        S.gradient_rect(u0, -0.3, u1, 0.66, sky_t, sky_b)
        S.glow(0.70, 0.46, 0.9, (1.0, 0.8, 0.45), 0.55)
        for k in range(14):                                                                                           # lane buildings
            bw = rng.uniform(0.16, 0.30)
            bh = rng.uniform(0.20, 0.45)
            bu = u0 + k * 0.22 + rng.uniform(-0.04, 0.04)
            col = mix(mix(P.wall_bot, P.accent, 0.2), (0.35, 0.30, 0.35), 0.3 if not dark else 0.7)
            S.rect(bu, 0.62 - bh / 2, bw, bh, scale(col, rng.uniform(0.85, 1.05)), lift=0.04)
            for j in range(3):
                S.rect(bu + rng.uniform(-bw * 0.3, bw * 0.3), 0.62 - bh * rng.uniform(0.3, 0.8), 0.03, 0.04, (1.0, 0.85, 0.5) if (j + k) % 2 else scale(col, 0.7), lift=0.0)
        S.ellipse(0.35, 0.40, 0.18, 0.22, (0.25, 0.45, 0.22) if not dark else (0.10, 0.2, 0.15), lift=0.1)               # a street tree
        S.rect(0.35, 0.55, 0.03, 0.12, (0.3, 0.2, 0.12), lift=0.0)
        S.bokeh(18, u0, 0.05, u1, 0.62, [(1.0, 0.85, 0.5), (1.0, 0.6, 0.3), (1.0, 0.95, 0.75)], 0.012, 0.05, 0.5)
        S.rect(1.55, 0.44, 1.95, 0.56, scale(mix(P.wall_bot, (0.5, 0.3, 0.2), 0.6), 0.75 if not dark else 0.5), lift=0.0)
        S.rect(1.55, 0.40, 1.95, 0.016, scale(P.surface, 0.7), lift=0.05)
        S.rect(0.575, 0.40, 0.05, 0.64, scale(P.surface, 0.55), lift=0.06)                                               # wooden post
        for k, uu in enumerate((0.90, 1.10, 1.30, 1.50, 1.70, 1.90)):                                                    # tins and jars on the back shelf
            col = [(0.85, 0.75, 0.55), (0.78, 0.30, 0.18), (0.9, 0.85, 0.7), (0.4, 0.55, 0.3), (0.85, 0.62, 0.3), (0.8, 0.8, 0.82)][k]
            S.rect(uu, 0.36, 0.09, 0.07 + 0.02 * (k % 2), scale(col, 0.85), r=0.012)
            S.rect(uu, 0.31 - 0.02 * (k % 2), 0.096, 0.012, scale(col, 0.6), lift=0.0)
        S.glow(1.3, 0.35, 0.8, (1.0, 0.8, 0.45), 0.30)
    # stall: striped awning at the top, string lights, shelf with jars, wooden counter
    S.rect((u0 + u1) / 2, 0.02, u1 - u0, 0.24, scale(P.accent, 0.82 if dark else 1.0), lift=0.0)                       # striped awning: flat bands + scallops
    for k in range(int((u1 - u0) / 0.32) + 2):
        uu = u0 + k * 0.32
        S.rect(uu + 0.16, 0.02, 0.16, 0.24, scale((0.97, 0.93, 0.84), 0.62 if dark else 1.0), lift=0.0)
        S.poly([(uu, 0.14), (uu + 0.16, 0.14), (uu + 0.08, 0.185)], scale(P.accent, 0.82 if dark else 1.0))
        S.poly([(uu + 0.16, 0.14), (uu + 0.32, 0.14), (uu + 0.24, 0.185)], scale((0.97, 0.93, 0.84), 0.62 if dark else 1.0))
    S.rect((u0 + u1) / 2, 0.135, u1 - u0, 0.012, scale(P.accent_dark, 0.9), lift=0.0)
    for k in range(6):
        uu = 0.50 + k * 0.26
        S.glow(uu + 0.085, 0.215, 0.075, (1.0, 0.82, 0.45), 0.55)
        S.circle(uu + 0.085, 0.205, 0.012, (1.0, 0.95, 0.75), lift=0, soft=1.5)
    S.wood(u0, 0.66, u1, 2.8, scale(mix(P.surface, P.accent, 0.25), 0.92), plank=0.18, grain=0.10)
    S.rect((u0 + u1) / 2, 0.655, u1 - u0, 0.03, scale(P.surface, 0.5), lift=0.0)
    S.soft(1.2, 0.84, 0.9, 0.16, (1.0, 0.8, 0.45), 0.30 if not dark else 0.42, 1.5, add=True)
    S.put("host_paper_cups", 0.86, 0.84, 0.20, color=P.accent, shadow=False)
    S.put("host_pakoda_cone", 1.62, 0.84, 0.19, shadow=False)
    S.put("host_chai_kettle", 1.25, 0.90, 0.46, subject=True, shadow=False)
    S.put("host_chai_glasses", 0.98, 1.00, 0.17, shadow=False)
    S.put("host_bun_maska", 1.56, 1.02, 0.12, shadow=False)
    S.focus("detail", 1.20, 0.76)
    with S.near(16.0):
        S.soft(0.66, 1.06, 0.12, 0.06, (0.9, 0.6, 0.2), 0.45, 1.0)
        S.soft(1.88, 1.05, 0.10, 0.06, mix(P.accent, WHITE, 0.3), 0.40, 1.0)


# ================================================================================================ BANQUET HALL
GOLD = (0.86, 0.68, 0.30)
IVORY = (0.97, 0.94, 0.88)


def _bloom(c, u, v, r, col, rng):
    """One flower seen from the front: a few petals around a bright centre."""
    for k in range(4):
        a = k * 1.571 + rng.uniform(0, 0.6)
        c.ellipse(u + math.cos(a) * r * 0.5, v + math.sin(a) * r * 0.5, r * 0.6, r * 0.55, mix(col, WHITE, 0.12 * (k % 2)), lift=0.12)
    c.ellipse(u, v, r * 0.35, r * 0.32, mix(col, (1.0, 0.85, 0.4), 0.55), lift=0.0)


def _bouquet(c, u, v, h, w, cols, n, rng, leafy=True):
    """A dome of flowers on stems: leaves first, then blooms packed into an ellipse."""
    if leafy:
        for k in range(4):
            leaf(c, u, v, h * 0.45, 35 + k * 36 + rng.uniform(-6, 6), (0.18 + rng.random() * 0.08, 0.46, 0.22), 0.34)
    for i in range(n):
        a, q = rng.uniform(0, 6.28), math.sqrt(rng.random())
        _bloom(c, u + math.cos(a) * w * q, v + h * 0.45 + math.sin(a) * h * 0.40 * q + h * 0.1, h * 0.085, cols[i % len(cols)], rng)


@sprop("host_stage_set", aspect=1.78, fill=0.62)
def host_stage_set(c, color):
    rng = c.rng
    acc = color or (0.75, 0.38, 0.48)
    ao(c, 0.0, 0.0, 1.3, 0.3)
    c.rect(0.0, 0.035, 1.12, 0.07, scale(IVORY, 0.9), lift=0.08, r=0.01)                                             # stepped dais
    c.rect(0.0, 0.07, 1.14, 0.012, GOLD, lift=0.1)
    c.poly([(-0.56, 0.075), (0.56, 0.075), (0.50, 0.145), (-0.50, 0.145)], mix(IVORY, acc, 0.18), lift=0.06)
    c.poly([(-0.10, 0.075), (0.10, 0.075), (0.08, 0.145), (-0.08, 0.145)], scale(acc, 0.8), lift=0.04)
    # the flower-wall backdrop with gold frame and drapes
    c.rect(0.0, 0.38, 0.88, 0.48, mix(IVORY, acc, 0.10), lift=0.1, r=0.02)
    c.ellipse(0.0, 0.62, 0.44, 0.075, mix(IVORY, acc, 0.10), lift=0.05)
    for k in range(-3, 4):
        c.line(k * 0.12, 0.15, k * 0.12 + 0.004, 0.60, 0.012, scale(IVORY, 0.80 + 0.06 * (k % 2)), 0.5)
    for sgn in (-1, 1):
        c.rect(sgn * 0.44, 0.38, 0.016, 0.48, GOLD, lift=0.12)
    c.rect(0.0, 0.625, 0.90, 0.016, GOLD, lift=0.12)
    c.ellipse(0.0, 0.40, 0.17, 0.17, scale(GOLD, 0.85), lift=0.1)                                                     # gold medallion (plain rings)
    c.ellipse(0.0, 0.40, 0.145, 0.145, mix(IVORY, acc, 0.2), lift=0.05)
    for k in range(8):
        a = k * 0.785
        c.ellipse(math.cos(a) * 0.085, 0.40 + math.sin(a) * 0.085, 0.045, 0.022, GOLD, angle=math.degrees(a), lift=0.1, alpha=0.9)
    c.ellipse(0.0, 0.40, 0.04, 0.04, acc, lift=0.1)
    for k in range(0, 12):                                                                                            # floral border down both sides and along the top
        t = k / 11.0
        for u, v in ((-0.44, 0.15 + t * 0.47), (0.44, 0.15 + t * 0.47)):
            _bloom(c, u, v, 0.034, [acc, mix(acc, WHITE, 0.55), (0.98, 0.9, 0.92)][k % 3], rng)
    for k in range(0, 8):
        _bloom(c, -0.44 + k * 0.125, 0.62 + 0.02 * math.sin(k), 0.032, [acc, mix(acc, WHITE, 0.55), (0.98, 0.9, 0.92)][k % 3], rng)
    # two velvet sofas on the dais
    for u in (-0.20, 0.21):
        c.rect(u, 0.32, 0.30, 0.21, scale(acc, 0.9), lift=0.12, r=0.045)
        c.rect(u - 0.12, 0.33, 0.04, 0.17, mix(acc, WHITE, 0.2), lift=0, alpha=0.5, r=0.02)
        c.rect(u, 0.215, 0.34, 0.09, acc, lift=0.14, r=0.03)
        c.rect(u, 0.18, 0.37, 0.03, scale(acc, 0.7), lift=0.1, r=0.01)
        for sgn in (-1, 1):
            c.rect(u + sgn * 0.185, 0.225, 0.045, 0.12, scale(acc, 0.85), lift=0.12, r=0.02)
            c.rect(u + sgn * 0.16, 0.155, 0.014, 0.025, GOLD, lift=0.1)
        for k in range(3):
            c.circle(u - 0.10 + k * 0.10, 0.29 + 0.01 * (k % 2), 0.007, GOLD, lift=0.1)
    # flower urns at the edges
    for sgn in (-1, 1):
        u = sgn * 0.53
        c.poly([(u - 0.045, 0.145), (u + 0.045, 0.145), (u + 0.06, 0.26), (u - 0.06, 0.26)], GOLD, lift=0.12)
        c.ellipse(u, 0.26, 0.06, 0.02, scale(GOLD, 0.8), lift=0)
        _bouquet(c, u, 0.26, 0.38, 0.10, [acc, mix(acc, WHITE, 0.5), (0.98, 0.92, 0.9)], 6, rng)


@sprop("host_round_table", aspect=1.9, fill=0.34)
def host_round_table(c, color):
    rng = c.rng
    acc = color or (0.75, 0.38, 0.48)
    ao(c, 0.0, 0.0, 1.1, 0.30)
    for u in (-0.20, 0.20):                                                                                           # chairs behind the table, with covers and sashes
        c.rect(u, 0.20, 0.17, 0.16, IVORY, lift=0.0, r=0.04)
        c.rect(u, 0.14, 0.17, 0.035, acc, lift=0.0)
    for sgn in (-1, 1):                                                                                               # chairs at the sides
        u = sgn * 0.48
        c.rect(u, 0.16, 0.13, 0.30, IVORY, lift=0.0, r=0.04)
        c.rect(u, 0.14, 0.13, 0.04, acc, lift=0.0)
    c.poly([(-0.40, 0.17), (0.40, 0.17), (0.43, 0.0), (-0.43, 0.0)], IVORY, lift=0.08)                              # cloth to the floor
    for k in range(-2, 3):
        c.line(k * 0.15, 0.165, k * 0.165, 0.01, 0.014, scale(IVORY, 0.80), 0.45)
    c.poly([(0.10, 0.17), (0.40, 0.17), (0.43, 0.0), (0.12, 0.0)], BLACK, lift=0, alpha=0.12)
    c.ellipse(0.0, 0.01, 0.43, 0.06, scale(IVORY, 0.8), lift=0)
    c.ellipse(0.0, 0.17, 0.41, 0.115, scale(IVORY, 0.86), lift=0)                                                    # table top
    c.ellipse(0.0, 0.175, 0.39, 0.105, WHITE, lift=0.1)
    c.ellipse(0.0, 0.175, 0.15, 0.04, acc, lift=0.1, alpha=0.9)                                                      # table runner disc
    for u, v in ((-0.25, 0.155), (0.25, 0.155), (-0.14, 0.12), (0.14, 0.12)):                                       # plates and napkins
        c.ellipse(u, v, 0.075, 0.026, (0.82, 0.82, 0.84), lift=0)
        c.ellipse(u, v + 0.004, 0.07, 0.023, WHITE, lift=0.1)
        c.ellipse(u, v + 0.005, 0.046, 0.014, (0.95, 0.9, 0.78), lift=0, alpha=0.7)
        c.poly([(u - 0.02, v + 0.015), (u + 0.02, v + 0.015), (u, v + 0.05)], mix(acc, WHITE, 0.2), lift=0.1)
    c.line(0.0, 0.18, 0.0, 0.38, 0.012, GOLD)                                                                         # tall centrepiece
    c.poly([(-0.045, 0.37), (0.045, 0.37), (0.02, 0.18), (-0.02, 0.18)], mix(GOLD, WHITE, 0.2), lift=0.1, alpha=0.8)
    _bouquet(c, 0.0, 0.34, 0.17, 0.07, [acc, mix(acc, WHITE, 0.5), (0.98, 0.92, 0.9)], 7, rng, leafy=False)
    soft_disc(c, -0.12, 0.17, 0.2, 0.04, WHITE, 0.4, 1.1, add=True)


@sprop("host_flower_pedestal", aspect=0.5, fill=1.0)
def host_flower_pedestal(c, color):
    rng = c.rng
    acc = color or (0.75, 0.38, 0.48)
    ao(c, 0.0, 0.0, 0.5, 0.16)
    c.ellipse(0.0, 0.02, 0.17, 0.045, scale(GOLD, 0.7), lift=0)
    c.ellipse(0.0, 0.035, 0.16, 0.04, GOLD, lift=0.2)
    c.poly([(-0.04, 0.04), (0.04, 0.04), (0.025, 0.40), (-0.025, 0.40)], GOLD, lift=0.14)
    c.poly([(0.01, 0.04), (0.04, 0.04), (0.025, 0.40), (0.012, 0.40)], BLACK, lift=0, alpha=0.2)
    c.ellipse(0.0, 0.20, 0.06, 0.022, GOLD, lift=0.2)
    c.poly([(-0.12, 0.50), (0.12, 0.50), (0.05, 0.38), (-0.05, 0.38)], scale(GOLD, 0.95), lift=0.14)
    c.ellipse(0.0, 0.50, 0.12, 0.03, scale(GOLD, 0.75), lift=0)
    _bouquet(c, 0.0, 0.50, 0.50, 0.14, [acc, mix(acc, WHITE, 0.5), (0.98, 0.92, 0.9), mix(acc, (0.9, 0.5, 0.3), 0.4)], 13, rng)


def _chandelier(S, u, v, w, dark):
    """A hanging crystal chandelier for the far layer: chain, tiers, glowing crystals."""
    S.line(u, -0.2, u, v - 0.05, 0.004, scale(GOLD, 0.7))
    S.glow(u, v + 0.02, w * 1.7, (1.0, 0.88, 0.6), 0.55 if dark else 0.38)
    S.ellipse(u, v - 0.02, w * 0.16, w * 0.07, GOLD, lift=0.12)
    S.ellipse(u, v + 0.02, w * 0.50, w * 0.11, mix(GOLD, WHITE, 0.15), lift=0.1)
    S.ellipse(u, v + 0.055, w * 0.34, w * 0.09, mix(GOLD, WHITE, 0.30), lift=0.1)
    for k in range(9):
        x = u + (k - 4) * w * 0.115
        S.rect(x, v + 0.08 + 0.012 * abs(k - 4), 0.006, 0.05, (1.0, 0.97, 0.85), lift=0.0)
        S.circle(x, v + 0.11 + 0.012 * abs(k - 4), 0.012, (1.0, 0.98, 0.9), lift=0, soft=1.5)


@niche("banquet-hall", "Banquet hall and venue", subjects=("host_stage_set",),
       strong=("banquet hall", "banquet halls", "banquet and lawn", "wedding venue", "marriage hall", "marriage garden", "function hall", "party hall", "venue hire",
               "event venue", "wedding lawn", "reception hall", "marriage lawn", "community hall", "banquet and lawn", "बैंक्वेट हॉल", "मैरिज हॉल",
               "मैरिज गार्डन", "शादी हॉल", "शादी का हॉल", "विवाह भवन", "विवाह स्थल", "पार्टी हॉल", "मैरिज लॉन"),
       weak=("stage setup", "bridal room", "open lawn", "guest rooms", "parking", "air conditioned hall", "reception", "engagement", "haldi", "sangeet",
             "hall booking", "लॉन", "हॉल", "स्टेज"),
       accent="#c0607a", mood="light", group="events",
       avoid=("event planner", "event management", "decorator", "party planner", "tent house", "tent rental", "mandap rental", "wedding photographer", "caterer",
              "catering service", "mehendi", "bridal makeup", "wedding planner", "टेंट हाउस", "इवेंट प्लानर", "कैटरर"))
def banquet_hall(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    wall = mix(IVORY, P.accent, 0.10) if not dark else scale(mix(P.accent, (0.2, 0.1, 0.15), 0.5), 0.5)
    with S.far():
        S.wall(mix(wall, WHITE, 0.2 if not dark else 0.0), scale(wall, 0.9), 0.66)
        for k in range(int((u1 - u0) / 0.55) + 2):                                                                   # tall drapes between gilded columns
            x = u0 + k * 0.55
            S.rect(x, 0.30, 0.07, 0.75, scale(GOLD, 0.8 if dark else 1.0), lift=0.1)
            for j in range(4):
                S.rect(x + 0.095 + j * 0.09, 0.30, 0.075, 0.70, mix(P.accent_light, wall, 0.35 + 0.1 * (j % 2)) if not dark else scale(P.accent, 0.5 - 0.06 * (j % 2)), lift=0.0)
            S.ellipse(x + 0.275, 0.62, 0.30, 0.05, scale(GOLD, 0.8), lift=0.0, alpha=0.0)
            S.rect(x + 0.275, 0.18, 0.44, 0.016, scale(GOLD, 0.8), lift=0.0)
        for uu, vv, ww in ((0.55, 0.12, 0.30), (1.25, 0.06, 0.38), (1.95, 0.12, 0.30)):
            _chandelier(S, uu, vv, ww, dark)
        S.bokeh(10, u0, 0.1, u1, 0.6, [(1.0, 0.9, 0.65), (1.0, 0.78, 0.55)], 0.012, 0.04, 0.35)
        S.floor(0.66, mix(P.floor_top, (0.85, 0.78, 0.7), 0.5) if not dark else scale(P.floor_top, 0.8), scale(P.floor_bot, 0.9))
        for k in range(-5, 6):                                                                                        # floor joints running to the vanishing point (blurred in the far layer)
            S.line(1.5 + k * 0.05, 0.70, 1.5 + k * 0.42, 1.6, 0.006, scale(P.floor_bot, 0.8), 0.45)
        for k in range(5):
            S.rect(1.5, 0.76 + k * k * 0.04, u1 - u0, 0.006, scale(P.floor_bot, 0.8), lift=0.0, alpha=0.4)
    S.rect((u0 + u1) / 2, 0.665, u1 - u0, 0.02, scale(GOLD, 0.7 if dark else 0.9), lift=0.0)
    S.poly([(1.41, 0.86), (1.59, 0.86), (1.93, 1.36), (1.07, 1.36)], scale(P.accent, 0.78))                          # aisle carpet in perspective
    S.rect(1.5, 0.862, 0.18, 0.012, GOLD, lift=0.0)
    S.soft(1.5, 0.88, 0.6, 0.10, (1.0, 0.9, 0.7), 0.30 if not dark else 0.40, 1.5, add=True)
    S.put("host_stage_set", 1.50, 0.88, 0.48, color=P.accent, subject=True, shadow=False)
    S.put("host_flower_pedestal", 1.92, 0.98, 0.34, color=P.accent, shadow=False)
    S.put("host_round_table", 1.14, 1.04, 0.26, color=P.accent, shadow=False)
    S.focus("detail", 1.50, 0.62)
    with S.near(16.0):
        S.soft(0.66, 1.08, 0.12, 0.06, mix(P.accent, WHITE, 0.4), 0.40, 1.0)
        S.soft(1.9, 1.10, 0.10, 0.06, GOLD, 0.35, 1.0)


# ================================================================================================ FARM STAY
def _tiles(c, pts_rows, col):
    for (x0, x1, y) in pts_rows:
        c.line(x0, y, x1, y, 0.006, col, 0.55)


@sprop("host_cottage", aspect=1.42, fill=0.96)
def host_cottage(c, color):
    rng = c.rng
    acc = color or (0.05, 0.49, 0.58)
    wall, roof = (0.97, 0.93, 0.84), (0.72, 0.34, 0.20)
    ao(c, 0.0, 0.0, 1.5, 0.36)
    c.rect(0.0, 0.025, 1.14, 0.05, (0.62, 0.58, 0.52), lift=0.08)                                                     # plinth
    c.rect(0.0, 0.30, 1.04, 0.52, wall, lift=0.06)                                                                    # whitewashed wall
    c.rect(0.0, 0.10, 1.04, 0.10, scale(wall, 0.86), lift=0.0)
    c.rect(0.48, 0.30, 0.10, 0.52, BLACK, lift=0, alpha=0.12)
    for _ in range(40):                                                                                               # plaster texture
        c.ellipse(rng.uniform(-0.5, 0.5), rng.uniform(0.06, 0.54), rng.uniform(0.01, 0.03), rng.uniform(0.004, 0.012), scale(wall, rng.uniform(0.84, 0.94)), lift=0, alpha=0.5)
    # the hip roof with tile courses, a ridge and a chimney
    c.rect(0.28, 0.80, 0.09, 0.20, (0.55, 0.28, 0.2), lift=0.1)
    c.poly([(-0.66, 0.50), (0.66, 0.50), (0.38, 0.93), (-0.38, 0.93)], roof, lift=0.1)
    c.poly([(0.20, 0.93), (0.66, 0.50), (0.38, 0.93)], BLACK, lift=0, alpha=0.16)
    for k in range(1, 7):
        t = k / 7.0
        xl, xr = -0.66 + 0.28 * t, 0.66 - 0.28 * t
        c.line(xl, 0.50 + 0.43 * t, xr, 0.50 + 0.43 * t, 0.007, scale(roof, 0.70), 0.7)
    for k in range(-7, 8):
        c.line(k * 0.085, 0.50, k * 0.045, 0.93, 0.004, scale(roof, 0.84), 0.5)
    c.rect(0.0, 0.935, 0.78, 0.022, scale(roof, 0.62), lift=0.1, r=0.01)
    c.rect(0.0, 0.495, 1.34, 0.03, scale(roof, 0.55), lift=0.08)
    soft_disc(c, 0.0, 0.46, 0.55, 0.05, BLACK, 0.35, 1.3)                                                             # shade under the eaves
    # veranda posts and a lower roof over the door
    c.poly([(-0.30, 0.46), (0.30, 0.46), (0.36, 0.40), (-0.36, 0.40)], scale(roof, 0.85), lift=0.1)
    for u in (-0.33, 0.33):
        c.rect(u, 0.20, 0.035, 0.40, (0.45, 0.28, 0.14), lift=0.1)
        c.rect(u - 0.006, 0.20, 0.008, 0.40, (0.75, 0.55, 0.32), lift=0, alpha=0.7)
    # door
    c.rect(0.0, 0.17, 0.22, 0.30, scale(acc, 0.7), lift=0.12, r=0.03)
    c.ellipse(0.0, 0.32, 0.11, 0.05, scale(acc, 0.7), lift=0.12)
    c.rect(0.0, 0.17, 0.008, 0.30, scale(acc, 0.45), lift=0, alpha=0.7)
    c.circle(0.06, 0.17, 0.012, GOLD, lift=0.2)
    c.rect(0.0, 0.025, 0.30, 0.03, (0.74, 0.70, 0.64), lift=0.1)
    # lantern with a glow
    c.line(0.20, 0.44, 0.20, 0.38, 0.004, (0.1, 0.1, 0.1))
    c.rect(0.20, 0.35, 0.03, 0.05, (0.2, 0.15, 0.1), lift=0.1)
    c.glow(0.20, 0.35, 0.16, (1.0, 0.78, 0.4), 0.6)
    # shuttered windows with flower boxes
    for u in (-0.40, 0.40):
        c.rect(u, 0.30, 0.17, 0.20, (0.45, 0.62, 0.78) if True else acc, lift=0.1)
        c.rect(u, 0.30, 0.17, 0.20, WHITE, lift=0, alpha=0.0)
        c.rect(u, 0.30, 0.008, 0.20, (0.95, 0.95, 0.95), lift=0)
        c.rect(u, 0.30, 0.17, 0.008, (0.95, 0.95, 0.95), lift=0)
        soft_disc(c, u - 0.04, 0.34, 0.07, 0.06, WHITE, 0.45, 1.2, add=True)
        for sgn in (-1, 1):
            c.rect(u + sgn * 0.115, 0.30, 0.06, 0.21, acc, lift=0.12)
            for k in range(3):
                c.line(u + sgn * 0.115 - 0.02, 0.22 + k * 0.06, u + sgn * 0.115 + 0.02, 0.22 + k * 0.06, 0.005, scale(acc, 0.6), 0.7)
        c.rect(u, 0.185, 0.22, 0.04, (0.45, 0.28, 0.14), lift=0.1)
        for k in range(5):
            leaf(c, u - 0.08 + k * 0.04, 0.20, 0.07, 80 + rng.uniform(-30, 30), (0.22, 0.52, 0.22), 0.4)
        for k in range(5):
            c.circle(u - 0.08 + k * 0.04, 0.255 + 0.01 * (k % 2), 0.015, [(0.98, 0.45, 0.5), (1.0, 0.85, 0.2), (0.95, 0.95, 0.95)][k % 3], lift=0.1)


@sprop("host_bullock_cart", aspect=3.1, fill=0.52)
def host_bullock_cart(c, color):
    acc = color or (0.05, 0.49, 0.58)
    wood, ox = (0.58, 0.38, 0.20), (0.93, 0.89, 0.82)
    ao(c, 0.0, 0.0, 1.0, 0.18)
    # the ox (left), the yoke pole, then the cart (right)
    for u in (-0.84, -0.60):                                                                                          # legs
        c.rect(u, 0.10, 0.05, 0.20, scale(ox, 0.82), lift=0.1, r=0.012)
        c.rect(u, 0.01, 0.055, 0.03, (0.25, 0.2, 0.15), lift=0.1)
    for u in (-0.78, -0.54):
        c.rect(u, 0.10, 0.05, 0.20, ox, lift=0.1, r=0.012)
        c.rect(u, 0.01, 0.055, 0.03, (0.3, 0.24, 0.18), lift=0.1)
    c.ellipse(-0.67, 0.28, 0.27, 0.13, scale(ox, 0.78), lift=0)
    c.ellipse(-0.68, 0.295, 0.26, 0.125, ox, lift=0.14)
    soft_disc(c, -0.55, 0.22, 0.2, 0.06, (0.5, 0.4, 0.3), 0.3, 1.3)
    c.ellipse(-0.82, 0.39, 0.08, 0.07, ox, lift=0.12)                                                                 # hump
    c.poly([(-0.90, 0.30), (-0.96, 0.40), (-0.88, 0.42), (-0.80, 0.34)], ox, lift=0.1)                                # neck and head
    c.ellipse(-0.99, 0.36, 0.065, 0.045, scale(ox, 0.95), lift=0.1, angle=40)
    c.ellipse(-1.03, 0.335, 0.02, 0.014, (0.35, 0.25, 0.22), lift=0.1)
    craft.arc(c, -0.94, 0.43, 0.055, 0.045, 10, 170, 0.015, (0.4, 0.3, 0.2))
    c.line(-0.94, 0.45, -0.88, 0.50, 0.018, (0.85, 0.82, 0.74))
    c.line(-0.98, 0.45, -1.02, 0.52, 0.018, (0.85, 0.82, 0.74))
    c.line(-0.56, 0.33, -0.05, 0.22, 0.022, wood)                                                                      # pole
    c.rect(-0.80, 0.38, 0.04, 0.10, acc, lift=0.1)                                                                    # yoke
    # cart bed, rails and wheel
    c.rect(0.28, 0.25, 0.62, 0.05, wood, lift=0.12)
    c.poly([(-0.05, 0.28), (0.60, 0.28), (0.62, 0.42), (-0.07, 0.42)], scale(wood, 1.1), lift=0.1)
    for k in range(7):
        c.line(-0.04 + k * 0.10, 0.285, -0.05 + k * 0.10, 0.415, 0.012, scale(wood, 0.7), 0.8)
    c.rect(0.28, 0.42, 0.68, 0.025, scale(wood, 0.8), lift=0.1)
    c.ellipse(0.0, 0.30, 0.04, 0.05, acc, lift=0.1)
    # hay load
    for k in range(7):
        c.ellipse(0.04 + k * 0.08, 0.45 + 0.012 * (k % 3), 0.10, 0.06, (0.90 - 0.02 * (k % 2), 0.74, 0.30), lift=0.14)
    wcx, wcy, wr = 0.28, 0.21, 0.21
    c.ring(wcx, wcy, wr, 0.030, scale(wood, 0.85))
    c.ring(wcx, wcy, wr - 0.025, 0.012, (0.55, 0.55, 0.58))
    for k in range(10):
        a = k * 0.628
        c.line(wcx, wcy, wcx + math.cos(a) * wr, wcy + math.sin(a) * wr, 0.014, wood)
    c.circle(wcx, wcy, 0.04, scale(wood, 0.65), lift=0.14)
    c.circle(wcx, wcy, 0.015, (0.7, 0.7, 0.72), lift=0.1)


@sprop("host_charpai", aspect=2.0, fill=0.40)
def host_charpai(c, color):
    rng = c.rng
    acc = color or (0.05, 0.49, 0.58)
    wood = (0.50, 0.32, 0.16)
    ao(c, 0.0, 0.0, 1.0, 0.24)
    for u, h in ((-0.36, 0.14), (0.36, 0.14), (-0.28, 0.12), (0.30, 0.12)):                                          # legs
        c.rect(u, h / 2, 0.04, h, scale(wood, 0.8 if abs(u) < 0.33 else 1.0), lift=0.1)
    c.poly([(-0.44, 0.22), (0.44, 0.22), (0.50, 0.14), (-0.50, 0.14)], scale(wood, 1.05), lift=0.1)
    c.poly([(-0.38, 0.19), (0.38, 0.19), (0.44, 0.15), (-0.44, 0.15)], mix((0.75, 0.62, 0.40), acc, 0.1), lift=0.06)
    for k in range(-9, 10):                                                                                           # woven rope
        c.line(k * 0.04, 0.19, k * 0.046, 0.15, 0.004, (0.55, 0.45, 0.28), 0.8)
    for k in range(4):
        c.line(-0.42 + k * 0.01, 0.152 + k * 0.012, 0.42 + k * 0.01, 0.152 + k * 0.012, 0.004, (0.55, 0.45, 0.28), 0.7)
    c.rect(0.0, 0.215, 0.88, 0.02, wood, lift=0.1)
    # breakfast on a steel tray: tea glasses, a paratha plate and a clay cup
    c.ellipse(0.0, 0.22, 0.30, 0.05, (0.60, 0.63, 0.67), lift=0)
    c.ellipse(0.0, 0.228, 0.29, 0.046, (0.84, 0.86, 0.88), lift=0.15)
    c.ellipse(-0.08, 0.245, 0.12, 0.035, WHITE, lift=0.1)
    c.ellipse(-0.08, 0.255, 0.085, 0.024, (0.93, 0.72, 0.38), lift=0.14)
    c.ellipse(-0.075, 0.262, 0.03, 0.01, (1.0, 0.95, 0.6), lift=0)
    for u in (0.12, 0.22):
        _chai_glass(c, u, 0.24, 0.14)
    c.poly([(-0.22, 0.285), (-0.14, 0.285), (-0.15, 0.24), (-0.21, 0.24)], (0.72, 0.38, 0.22), lift=0.12)
    c.ellipse(-0.18, 0.285, 0.04, 0.012, (0.3, 0.16, 0.1), lift=0)
    c.rect(-0.42, 0.24, 0.20, 0.07, acc, lift=0.1, r=0.02)                                                           # folded blanket
    c.rect(-0.42, 0.275, 0.20, 0.012, mix(acc, WHITE, 0.5), lift=0, alpha=0.8)
    steam(c, 0.17, 0.40, 0.10, 0.025, 1, 0.10)


@sprop("host_bonfire", aspect=1.35, fill=0.54)
def host_bonfire(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.2)
    soft_disc(c, 0.0, 0.18, 1.0, 0.7, (1.0, 0.55, 0.15), 0.5, 1.6, add=True)
    for k in range(9):                                                                                                # ring of stones
        a = k * 0.7
        c.ellipse(math.cos(a) * 0.40, 0.05 + math.sin(a) * 0.08, 0.06, 0.04, (0.50 + 0.05 * (k % 3), 0.48, 0.46), lift=0.15)
    c.line(-0.30, 0.07, 0.30, 0.15, 0.07, (0.26, 0.15, 0.08))                                                          # logs
    c.line(-0.30, 0.15, 0.30, 0.07, 0.07, (0.32, 0.18, 0.09))
    c.line(-0.30, 0.15, 0.30, 0.07, 0.025, (0.55, 0.32, 0.14), 0.7)
    for (u, h, w, col) in ((-0.14, 0.36, 0.14, (1.0, 0.45, 0.10)), (0.12, 0.42, 0.15, (1.0, 0.52, 0.10)), (0.0, 0.50, 0.17, (1.0, 0.60, 0.12))):
        c.poly([(u - w, 0.12), (u + w, 0.12), (u + w * 0.5, 0.12 + h * 0.5), (u + w * 0.1, 0.12 + h), (u - w * 0.3, 0.12 + h * 0.55)], col, lift=0.1, alpha=0.95)
        c.poly([(u - w * 0.55, 0.12), (u + w * 0.55, 0.12), (u + w * 0.15, 0.12 + h * 0.6), (u - w * 0.1, 0.12 + h * 0.4)], (1.0, 0.85, 0.3), lift=0.05)
        c.poly([(u - w * 0.25, 0.12), (u + w * 0.25, 0.12), (u, 0.12 + h * 0.33)], (1.0, 0.97, 0.7), lift=0, alpha=0.9)
    for _ in range(8):
        c.circle(rng.uniform(-0.2, 0.2), rng.uniform(0.4, 0.8), 0.008, (1.0, 0.7, 0.2), lift=0, alpha=0.8)


@sprop("host_haystack", aspect=0.95, fill=0.80)
def host_haystack(c, color):
    rng = c.rng
    ao(c, 0.0, 0.0, 0.9, 0.2)
    c.poly([(-0.46, 0.0), (0.46, 0.0), (0.38, 0.30), (0.20, 0.62), (0.0, 0.80), (-0.20, 0.62), (-0.38, 0.30)], (0.86, 0.68, 0.28), lift=0.12)
    c.poly([(0.0, 0.80), (0.20, 0.62), (0.38, 0.30), (0.46, 0.0), (0.12, 0.0), (0.10, 0.4)], (0.62, 0.45, 0.14), lift=0.05, alpha=0.5)
    for _ in range(34):
        x = rng.uniform(-0.40, 0.40)
        y = rng.uniform(0.04, 0.60 * (1 - abs(x) / 0.5))
        c.line(x, y, x + rng.uniform(-0.05, 0.05), y + rng.uniform(0.04, 0.09), 0.007, scale((0.92, 0.76, 0.34), rng.uniform(0.7, 1.1)), 0.7)
    c.line(-0.18, 0.76, 0.06, 0.92, 0.012, (0.92, 0.76, 0.34))
    c.line(0.0, 0.80, 0.0, 0.96, 0.012, (0.92, 0.76, 0.34))


def _farm_tree(S, u, v, h, tint=1.0, dark=False):
    k = 0.45 if dark else 1.0
    S.rect(u, v - h * 0.22, h * 0.07, h * 0.45, scale((0.34, 0.22, 0.12), k), lift=0.1)
    S.line(u, v - h * 0.40, u - h * 0.16, v - h * 0.58, h * 0.035, scale((0.34, 0.22, 0.12), k))
    S.line(u, v - h * 0.40, u + h * 0.16, v - h * 0.60, h * 0.035, scale((0.34, 0.22, 0.12), k))
    for du, dv, rr, sh in ((0, -0.72, 0.34, 1.0), (-0.22, -0.60, 0.26, 0.9), (0.24, -0.62, 0.27, 0.95), (0.0, -0.55, 0.30, 0.85)):
        S.ellipse(u + du * h, v + dv * h, rr * h, rr * h * 0.88, scale((0.26 * tint, 0.50, 0.22), sh * k), lift=0.1)
    for du, dv, rr in ((-0.10, -0.80, 0.14), (0.14, -0.74, 0.12)):
        S.ellipse(u + du * h, v + dv * h, rr * h, rr * h * 0.8, scale((0.42 * tint, 0.66, 0.28), k), lift=0.08, alpha=0.8)


@niche("farm-stay", "Farm stay and homestay", subjects=("host_cottage",),
       strong=("farm stay", "farmstay", "farm stays", "homestay", "home stay", "farmhouse stay", "village stay", "agri tourism", "agritourism",
               "rural stay", "farm resort", "farm house stay", "farm holiday", "village homestay", "rural homestay", "agro tourism", "stay on a farm", "फार्म स्टे", "होमस्टे", "फार्मस्टे", "गांव में ठहराव", "फार्महाउस स्टे",
               "होम स्टे", "ग्रामीण पर्यटन", "कृषि पर्यटन", "farm homestay", "bullock cart ride"),
       weak=("bonfire", "village walk", "bullock cart", "farm fresh", "cottage", "courtyard", "stargazing", "farm activities", "countryside", "बैलगाड़ी",
             "अलाव", "गांव", "कॉटेज"),
       accent="#0b7c93", mood="light", group="travel",
       avoid=("hotel", "resort", "five star", "hostel", "dairy farm", "poultry", "farm equipment", "tractor dealer", "crop", "seeds", "fertilizer", "hospital",
              "ट्रैक्टर", "खाद", "बीज", "डेयरी", "मुर्गी पालन"))
def farm_stay(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    rng = S.rng
    k = 0.45 if dark else 1.0
    with S.far():
        sk_t = (0.46, 0.72, 0.92) if not dark else (0.08, 0.10, 0.26)
        sk_b = (0.97, 0.92, 0.78) if not dark else (0.85, 0.48, 0.30)
        S.gradient_rect(u0, -0.3, u1, 0.62, sk_t, sk_b)
        S.glow(0.55, 0.40, 1.1, (1.0, 0.85, 0.5), 0.55)
        for (u, v, w) in ((0.4, 0.14, 0.30), (1.1, 0.22, 0.26), (1.8, 0.10, 0.30)):
            for j in range(4):
                S.ellipse(u + (j - 1.5) * w * 0.32, v + 0.02 * (j % 2), w * 0.34, w * 0.12, mix(sk_b, WHITE, 0.6), alpha=0.7 if not dark else 0.2, lift=0.05)
        S.ellipse(0.6, 0.64, 1.3, 0.16, scale(mix((0.42, 0.62, 0.40), sk_b, 0.35), k), lift=0)                       # distant hills
        S.ellipse(1.9, 0.66, 1.4, 0.13, scale(mix((0.50, 0.68, 0.40), sk_b, 0.45), k), lift=0)
        for j in range(24):
            S.ellipse(u0 + j * 0.13, 0.62, 0.06, 0.06 + 0.012 * (j % 3), scale((0.24, 0.42, 0.22), k), lift=0.1)
        S.rect(0.26, 0.58, 0.20, 0.10, scale((0.9, 0.86, 0.78), k), lift=0.0)                                         # a far-off farmhouse
        S.poly([(0.14, 0.53), (0.38, 0.53), (0.32, 0.47), (0.20, 0.47)], scale((0.70, 0.34, 0.22), k))
        _farm_tree(S, 0.68, 0.70, 0.62, 1.0, dark)
        _farm_tree(S, 1.98, 0.70, 0.50, 0.9, dark)
        S.floor(0.66, scale((0.55, 0.76, 0.32), k), scale((0.36, 0.58, 0.22), k))
        S.rect(1.0, 0.66, u1 - u0 + 1, 0.012, scale((0.30, 0.5, 0.2), k), lift=0.0)
        for r in range(8):                                                                                           # mown stripes growing towards the camera
            v0 = 0.70 + r * r * 0.012 + r * 0.04
            S.rect((u0 + u1) / 2, v0, u1 - u0, 0.03 + r * 0.008, scale((0.60, 0.80, 0.34), 0.97 if r % 2 else 1.04) if not dark else scale((0.6, 0.8, 0.34), 0.45), lift=0.0, alpha=0.45)
        S.poly([(1.42, 0.86), (1.58, 0.86), (1.80, 1.5), (1.05, 1.5)], scale((0.82, 0.68, 0.46), k), alpha=0.9)      # earth path from the door
    S.soft(1.5, 0.84, 0.8, 0.12, (1.0, 0.9, 0.6), 0.3 if not dark else 0.18, 1.5, add=True)
    for j in range(12):                                                                                               # split-rail fence
        S.rect(0.45 + j * 0.13, 0.755 + 0.0, 0.012, 0.07, scale((0.5, 0.34, 0.2), k), lift=0.0)
    S.rect(1.0, 0.745, 1.6, 0.010, scale((0.55, 0.38, 0.22), k), lift=0.0)
    S.put("host_haystack", 1.88, 0.88, 0.19, shadow=False)
    S.put("host_cottage", 1.50, 0.88, 0.50, color=P.accent, subject=True, shadow=False)
    S.put("host_bullock_cart", 1.27, 1.00, 0.19, color=P.accent, shadow=False)
    S.put("host_charpai", 1.71, 1.01, 0.165, color=P.accent, shadow=False)
    S.put("host_bonfire", 1.43, 1.09, 0.13, shadow=False)
    S.focus("detail", 1.45, 0.66)
    with S.near(16.0):
        S.soft(0.62, 1.08, 0.12, 0.06, (0.3, 0.6, 0.2), 0.5, 1.0)
        for j in range(5):
            S.circle(1.86 + 0.03 * j, 1.08 + 0.02 * (j % 2), 0.018, [(1.0, 0.85, 0.2), (0.95, 0.4, 0.5), (1.0, 1.0, 1.0)][j % 3], lift=0.05, soft=3.0)


# ================================================================================================ PG AND HOSTEL
def _pg_blanket(c, u0, u1, v, dx, dy, col):
    """A blanket lying on a mattress whose top face runs back by (dx, dy) from its front edge at height v."""
    c.poly([(u0, v), (u1, v), (u1 + dx, v + dy), (u0 + dx, v + dy)], col, lift=0.1)
    for k in range(1, 4):
        t = k / 4.0
        c.line(u0 + dx * t, v + dy * t, u1 + dx * t, v + dy * t, 0.012, mix(col, WHITE, 0.5), 0.6)
    c.poly([(u1, v), (u1 + dx, v + dy), (u1 + dx, v + dy - 0.03), (u1, v - 0.03)], scale(col, 0.7), lift=0)
    c.rect((u0 + u1) / 2, v - 0.015, u1 - u0, 0.03, scale(col, 0.84), lift=0.1)


@sprop("host_bunk_bed", aspect=1.02, fill=0.98)
def host_bunk_bed(c, color):
    acc = color or (0.12, 0.44, 0.47)
    steel, steel_d = (0.38, 0.42, 0.48), (0.22, 0.25, 0.30)
    ao(c, 0.0, 0.0, 1.0, 0.30)
    dx, dy = 0.19, 0.15
    for u in (-0.30 + dx, 0.30 + dx):                                                                                # back posts
        c.rect(u, 0.5 + dy, 0.03, 0.98, steel_d, lift=0.05)
    for vb, col, pl in ((0.20, acc, -1), (0.66, mix(acc, (0.95, 0.65, 0.25), 0.6), 1)):                              # lower and upper bunk
        c.poly([(-0.30, vb), (0.30, vb), (0.30 + dx, vb + dy), (-0.30 + dx, vb + dy)], scale(steel, 0.8), lift=0.04)
        c.rect(0.0, vb + 0.03, 0.60, 0.06, (0.90, 0.92, 0.94), lift=0.08, r=0.01)                                    # mattress edge
        c.poly([(-0.30, vb + 0.06), (0.30, vb + 0.06), (0.30 + dx, vb + 0.06 + dy), (-0.30 + dx, vb + 0.06 + dy)], (0.93, 0.93, 0.96), lift=0.05)
        c.poly([(0.30, vb), (0.30 + dx, vb + dy), (0.30 + dx, vb + dy + 0.06), (0.30, vb + 0.06)], scale((0.90, 0.92, 0.94), 0.7), lift=0)
        _pg_blanket(c, -0.30, 0.30, vb + 0.06, dx * 0.62, dy * 0.80, col) if False else None
        c.poly([(-0.30 + 0.20, vb + 0.06), (0.30, vb + 0.06), (0.30 + dx * 0.9, vb + 0.06 + dy * 0.9), (-0.30 + 0.20 + dx * 0.9, vb + 0.06 + dy * 0.9)], col, lift=0.1)
        for k in range(1, 4):
            t = k / 4.0
            c.line(-0.10 + dx * 0.9 * t, vb + 0.06 + dy * 0.9 * t, 0.30 + dx * 0.9 * t, vb + 0.06 + dy * 0.9 * t, 0.010, mix(col, WHITE, 0.5), 0.6)
        c.rect(0.10, vb + 0.045, 0.40, 0.03, scale(col, 0.82), lift=0.1)                                              # blanket hanging over the front edge
        pu = -0.17 if pl < 0 else -0.17
        c.ellipse(pu + dx * 0.5, vb + 0.09 + dy * 0.5, 0.10, 0.04 + 0.02, (0.97, 0.97, 0.95), lift=0.12)               # pillow
        c.ellipse(pu + dx * 0.5 - 0.02, vb + 0.105 + dy * 0.5, 0.06, 0.022, WHITE, lift=0, alpha=0.7)
    # front posts, guard rail, ladder
    for u in (-0.30, 0.30):
        c.rect(u, 0.49, 0.036, 0.98, steel, lift=0.12)
        c.rect(u - 0.008, 0.49, 0.008, 0.96, mix(steel, WHITE, 0.5), lift=0, alpha=0.6)
        c.circle(u, 0.985, 0.022, scale(steel, 0.9), lift=0.15)
    for v in (0.82, 0.90):
        c.line(-0.30, v, 0.30, v, 0.018, steel)
        c.line(-0.30 + dx, v + dy, -0.30, v, 0.012, steel_d)
    for u in (-0.30, 0.30):                                                                                          # slat bars between the posts below each bunk
        c.line(u, 0.20, u + dx, 0.30, 0.012, steel_d, 0.8)
    for u in (0.40, 0.52):
        c.line(u, 0.02, u, 0.78, 0.022, scale(steel, 1.1))
    for k in range(7):
        c.line(0.40, 0.08 + k * 0.105, 0.52, 0.08 + k * 0.105, 0.016, scale(steel, 1.2))
    c.line(0.30, 0.75, 0.40, 0.78, 0.014, steel)
    c.rect(0.0, 0.10, 0.50, 0.12, scale(acc, 0.7), lift=0.1, r=0.01, alpha=0.0)
    # trunk under the bed
    c.rect(-0.05, 0.08, 0.34, 0.10, scale(acc, 0.8), lift=0.1, r=0.012)
    c.rect(-0.05, 0.13, 0.34, 0.012, mix(acc, WHITE, 0.4), lift=0, alpha=0.8)
    c.rect(-0.05, 0.09, 0.03, 0.03, GOLD, lift=0.15)


@sprop("host_study_desk", aspect=1.5, fill=0.62)
def host_study_desk(c, color):
    acc = color or (0.12, 0.44, 0.47)
    wood = (0.80, 0.62, 0.40)
    ao(c, 0.0, 0.0, 1.1, 0.28)
    # chair behind, desk with a drawer pedestal, then the lamp, laptop and books
    c.rect(0.26, 0.40, 0.17, 0.30, scale(acc, 0.85), lift=0.12, r=0.04)
    c.rect(0.26, 0.18, 0.05, 0.14, (0.3, 0.3, 0.33), lift=0.1)
    _prism(c, -0.05, 0.0, 0.84, 0.30, 0.16, 0.08, wood, lift=0.08)
    c.rect(-0.44, 0.15, 0.015, 0.30, scale(wood, 0.62), lift=0, alpha=0.0)
    c.rect(-0.30, 0.14, 0.22, 0.24, scale(wood, 0.82), lift=0.1)                                                     # drawer pedestal
    for k in range(3):
        c.rect(-0.30, 0.05 + k * 0.075, 0.20, 0.012, scale(wood, 0.55), lift=0, alpha=0.8)
        c.rect(-0.30, 0.075 + k * 0.075, 0.05, 0.012, (0.75, 0.75, 0.78), lift=0.15)
    c.poly([(-0.47, 0.30), (0.37, 0.30), (0.37, 0.325), (-0.47, 0.325)], mix(wood, WHITE, 0.15), lift=0.1)
    c.poly([(-0.47, 0.325), (0.37, 0.325), (0.53, 0.405), (-0.31, 0.405)], mix(wood, WHITE, 0.25), lift=0.06)           # desk top
    soft_disc(c, -0.1, 0.37, 0.4, 0.04, WHITE, 0.4, 1.2, add=True)
    c.rect(0.30, 0.15, 0.04, 0.30, scale(wood, 0.7), lift=0.1)
    # laptop
    c.poly([(0.0, 0.38), (0.30, 0.38), (0.34, 0.40), (0.04, 0.40)], (0.72, 0.74, 0.77), lift=0.1)
    c.poly([(0.04, 0.40), (0.34, 0.40), (0.34, 0.60), (0.05, 0.60)], (0.12, 0.13, 0.16), lift=0.08)
    c.poly([(0.06, 0.415), (0.32, 0.415), (0.32, 0.585), (0.07, 0.585)], mix(acc, WHITE, 0.55), lift=0.1)
    c.rect(0.15, 0.50, 0.12, 0.06, WHITE, lift=0, alpha=0.7)
    c.rect(0.15, 0.545, 0.16, 0.012, acc, lift=0, alpha=0.8)
    # books and a pen cup
    for k, (w, h, col) in enumerate(((0.24, 0.035, (0.85, 0.35, 0.25)), (0.22, 0.03, (0.95, 0.78, 0.3)), (0.20, 0.035, acc))):
        c.rect(-0.18, 0.35 + 0.035 + sum(((0.035, 0.03, 0.035)[j]) for j in range(k)) + h / 2 - 0.035, w, h, col, lift=0.1, r=0.005)
        c.rect(-0.18 + w / 2 - 0.01, 0.35 + 0.035 + sum(((0.035, 0.03, 0.035)[j]) for j in range(k)) + h / 2 - 0.035, 0.012, h * 0.7, (0.96, 0.94, 0.88), lift=0)
    c.rect(-0.42, 0.405, 0.05, 0.07, (0.85, 0.85, 0.88), lift=0.1, r=0.01)
    for k in range(3):
        c.line(-0.43 + k * 0.012, 0.44, -0.45 + k * 0.025, 0.52, 0.007, [(0.2, 0.4, 0.8), (0.85, 0.2, 0.2), (0.2, 0.6, 0.3)][k])
    # adjustable desk lamp with a warm glow
    c.ellipse(-0.05, 0.385, 0.06, 0.018, (0.25, 0.25, 0.28), lift=0.1)
    c.line(-0.05, 0.39, -0.12, 0.55, 0.014, (0.30, 0.32, 0.36))
    c.line(-0.12, 0.55, -0.02, 0.66, 0.014, (0.30, 0.32, 0.36))
    c.poly([(-0.07, 0.69), (0.03, 0.69), (0.07, 0.62), (-0.11, 0.62)], acc, lift=0.12)
    c.glow(-0.02, 0.60, 0.30, (1.0, 0.88, 0.55), 0.5)
    c.ellipse(-0.02, 0.62, 0.075, 0.015, (1.0, 0.95, 0.7), lift=0)


@sprop("host_locker", aspect=0.62, fill=0.98)
def host_locker(c, color):
    acc = color or (0.12, 0.44, 0.47)
    ao(c, 0.0, 0.0, 0.7, 0.2)
    _prism(c, 0.0, 0.03, 0.44, 0.94, 0.10, 0.05, mix(acc, (0.7, 0.74, 0.78), 0.55), lift=0.06, r=0.006)
    for u in (-0.11, 0.11):                                                                                          # two doors with vent slits and handles
        c.rect(u, 0.52, 0.205, 0.86, mix(acc, (0.72, 0.76, 0.80), 0.5), lift=0.1, r=0.008)
        for k in range(6):
            c.rect(u, 0.78 + k * 0.025, 0.12, 0.008, scale(acc, 0.45), lift=0, alpha=0.9)
        c.rect(u, 0.52 + 0.06, 0.150, 0.015, scale(acc, 0.6), lift=0, alpha=0.5)
    c.rect(0.0, 0.52, 0.006, 0.86, scale(acc, 0.4), lift=0)
    for u in (-0.03, 0.03):
        c.rect(u, 0.50, 0.014, 0.10, (0.85, 0.86, 0.88), lift=0.2, r=0.006)
    c.rect(-0.11, 0.20, 0.06, 0.03, (0.92, 0.82, 0.3), lift=0.15, r=0.006)                                           # padlock
    c.rect(-0.18, 0.55, 0.012, 0.80, WHITE, lift=0, alpha=0.4)
    c.rect(0.0, 0.025, 0.46, 0.03, scale(acc, 0.4), lift=0.05)


@sprop("host_water_dispenser", aspect=0.52, fill=1.0)
def host_water_dispenser(c, color):
    ao(c, 0.0, 0.0, 0.6, 0.18)
    c.rect(0.0, 0.30, 0.34, 0.60, (0.94, 0.95, 0.97), lift=0.08, r=0.02)                                             # body
    c.rect(0.12, 0.30, 0.10, 0.60, BLACK, lift=0, alpha=0.12)
    c.rect(-0.12, 0.34, 0.03, 0.50, WHITE, lift=0, alpha=0.6)
    c.rect(0.0, 0.62, 0.34, 0.03, (0.80, 0.84, 0.88), lift=0)
    c.ellipse(0.0, 0.60, 0.17, 0.05, (0.8, 0.84, 0.88), lift=0)
    c.rect(0.0, 0.82, 0.24, 0.34, (0.55, 0.78, 0.95), lift=0.16, r=0.05, alpha=0.85)                                 # the water bottle
    c.rect(0.0, 0.76, 0.22, 0.22, (0.68, 0.87, 1.0), lift=0.1, r=0.04, alpha=0.9)
    c.rect(0.0, 0.99, 0.10, 0.04, (0.45, 0.70, 0.9), lift=0.1, r=0.01)
    soft_disc(c, -0.06, 0.85, 0.03, 0.14, WHITE, 0.55, 1.2, add=True)
    for u, col in ((-0.07, (0.25, 0.55, 0.95)), (0.07, (0.95, 0.30, 0.25))):                                         # taps
        c.rect(u, 0.50, 0.06, 0.07, col, lift=0.15, r=0.012)
        c.rect(u, 0.44, 0.015, 0.05, (0.7, 0.72, 0.75), lift=0.1)
    c.rect(0.0, 0.34, 0.26, 0.025, (0.45, 0.47, 0.52), lift=0.05)
    c.rect(0.0, 0.07, 0.30, 0.04, (0.5, 0.52, 0.56), lift=0.1, r=0.008)


@niche("pg-hostel", "PG and hostel", subjects=("host_bunk_bed",),
       strong=("pg hostel", "paying guest", "pg accommodation", "boys hostel", "girls hostel", "ladies hostel", "gents hostel", "student hostel", "working professionals hostel",
               "pg for boys", "pg for girls", "pg and hostel", "hostel and pg", "co living", "coliving", "co-living", "पीजी हॉस्टल", "पेइंग गेस्ट", "पीजी",
               "बॉयज हॉस्टल", "गर्ल्स हॉस्टल", "छात्रावास", "लड़कों का हॉस्टल", "लड़कियों का हॉस्टल", "hostel accommodation", "pg rooms", "sharing rooms"),
       weak=("sharing room", "double sharing", "triple sharing", "mess", "warden", "wifi", "single room", "students", "hostel", "रूम शेयरिंग", "हॉस्टल", "मेस", "वार्डन"),
       accent="#1f6f78", mood="light", group="travel",
       avoid=("hotel", "resort", "five star", "boutique hotel", "guest house", "homestay", "farm stay", "coworking", "co working", "school", "playschool", "boarding school",
              "real estate agent", "property dealer", "होटल", "रिसॉर्ट", "गेस्ट हाउस", "प्रॉपर्टी डीलर"))
def pg_hostel(S):
    P = S.pal
    dark = P.mood == "dark"
    u0, u1 = _span(S)
    wall = mix((0.95, 0.96, 0.97), P.accent_light, 0.18) if not dark else P.wall_top
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.70)
        S.rect((u0 + u1) / 2, 0.52, u1 - u0, 0.34, mix(P.wall_bot, P.accent, 0.22 if not dark else 0.4), lift=0.0)            # painted dado
        S.rect((u0 + u1) / 2, 0.355, u1 - u0, 0.012, scale(P.paper, 0.9 if not dark else 0.4), lift=0.0)
        S.rect(0.55, 0.26, 0.62, 0.46, scale(P.ink, 2.0 if not dark else 1.0), lift=0.0)                                       # window
        S.gradient_rect(0.30, 0.04, 0.80, 0.48, (0.62, 0.80, 0.96) if not dark else (0.12, 0.16, 0.34), (0.92, 0.96, 1.0) if not dark else (0.3, 0.34, 0.5))
        S.rect(0.55, 0.26, 0.012, 0.44, (0.97, 0.97, 0.98), lift=0.0)
        S.rect(0.55, 0.22, 0.52, 0.012, (0.97, 0.97, 0.98), lift=0.0)
        S.glow(0.55, 0.26, 1.0, P.light, 0.45)
        S.poly([(0.20, 0.0), (0.34, 0.0), (0.32, 0.50), (0.19, 0.50)], mix(P.accent, WHITE, 0.2), alpha=0.95)             # curtain
        S.poly([(0.78, 0.0), (0.92, 0.0), (0.93, 0.50), (0.80, 0.50)], mix(P.accent, WHITE, 0.2), alpha=0.95)
        S.rect(1.55, 0.20, 0.62, 0.30, mix(P.paper, (0.75, 0.6, 0.4), 0.25), lift=0.0)                                         # notice board with pinned sheets (plain bars)
        for k, col in enumerate(((1.0, 1.0, 0.8), (0.8, 0.95, 1.0), (1.0, 0.85, 0.85), (0.9, 1.0, 0.85), (1.0, 0.95, 0.7))):
            S.rect(1.32 + k * 0.11, 0.20 + 0.025 * (k % 2), 0.08, 0.13 + 0.02 * (k % 3), col, lift=0.0)
            S.circle(1.32 + k * 0.11, 0.14 + 0.025 * (k % 2), 0.008, P.accent, lift=0, soft=1.5)
        S.rect(1.55, 0.05, 0.14, 0.14, scale(P.ink, 2.4), lift=0.0, alpha=0.0)
        S.circle(1.1, 0.12, 0.07, mix(P.paper, P.accent, 0.1), lift=0.1)                                                       # wall clock (plain dial with hands)
        S.line(1.1, 0.12, 1.1, 0.07, 0.006, P.ink)
        S.line(1.1, 0.12, 1.14, 0.14, 0.006, P.ink)
        S.pendant(1.35, -0.1, 0.07, (1.0, 0.95, 0.8), 0.09)
        S.floor(0.70, scale(mix(P.floor_top, (0.85, 0.82, 0.78), 0.55), 1.0 if not dark else 0.8), scale(P.floor_bot, 0.9))
        for k in range(-6, 8):                                                                                       # floor tile joints in perspective (blurred in the far layer)
            S.line(1.3 + k * 0.1, 0.72, 1.3 + k * 0.40, 1.6, 0.006, scale(P.floor_bot, 0.78), 0.45)
        for k in range(5):
            S.rect(1.3, 0.78 + k * k * 0.035, u1 - u0, 0.006, scale(P.floor_bot, 0.78), lift=0.0, alpha=0.4)
    S.rect((u0 + u1) / 2, 0.705, u1 - u0, 0.028, scale(P.paper, 0.8 if not dark else 0.3), lift=0.0)                          # skirting
    S.poly([(0.90, 0.92), (1.80, 0.92), (1.95, 1.4), (0.75, 1.4)], mix(P.accent, WHITE, 0.55 if not dark else 0.0), alpha=0.6 if not dark else 0.4)   # rug
    S.soft(1.3, 0.80, 0.9, 0.14, P.light, 0.28 if not dark else 0.4, 1.5, add=True)
    S.put("host_locker", 1.78, 0.88, 0.44, color=P.accent, shadow=False)
    S.put("host_bunk_bed", 1.40, 0.90, 0.52, color=P.accent, subject=True, shadow=False)
    S.put("host_water_dispenser", 1.88, 1.00, 0.27, shadow=False)
    S.put("host_study_desk", 1.02, 1.00, 0.31, color=P.accent, shadow=False)
    S.focus("detail", 1.40, 0.74)
    with S.near(16.0):
        S.soft(0.66, 1.08, 0.12, 0.06, mix(P.accent, WHITE, 0.3), 0.40, 1.0)
        S.soft(1.9, 1.08, 0.10, 0.06, (0.9, 0.8, 0.6), 0.35, 1.0)
