"""Small-business niches driven by the client's picture spec: car-rental, bike-garage, mobile-repair, gift-shop, loan-finance.

Props are prefixed ``biz_``. Big shaded shapes use the scan-line fillers of auto_events (``_poly`` / ``_rr`` / ``_oval``) so scenes stay fast.
No text, letters, numbers or logos anywhere: signs, labels and documents are drawn as plain bars and shapes.
Scene layout never depends on ``S.rng`` (the dry pass does not consume it): decor uses a local Random.
"""
import math
import random

from .. import craft
from ..craft import BLACK, WHITE, ao, gloss, soft_disc
from ..niches import niche
from ..stage import sprop
from ...raster import mix, scale
from .auto_events import CARS, _car, _hfill, _cyl_fn, _oval, _poly, _rr, _rrpts, _shair, _spoly, _sfill

STEEL = (0.62, 0.65, 0.70)
CHROME = (0.84, 0.86, 0.90)
DARKM = (0.10, 0.10, 0.12)
RED = (0.86, 0.18, 0.16)
GOLD = (0.96, 0.76, 0.22)
CREAM = (0.99, 0.96, 0.90)


# ====================================================================================== shared helpers
def _dk(P):
    return P.mood == "dark"


def _tn(P, col, k=0.4):
    """Natural colour dimmed in the dark mood."""
    return scale(col, k) if _dk(P) else col


def _box3(c, u, v, w, h, d, front, top=None, right=None, r=0.0, tilt=(0.34, 0.30)):
    """Cuboid in raised 3/4 view, base-front centre at (u, v): lit top, front, shaded right side."""
    dx, dy = d * tilt[0], d * tilt[1]
    top = top or mix(front, WHITE, 0.28)
    right = right or scale(front, 0.66)
    x0, x1 = u - w / 2, u + w / 2
    _poly(c, [(x1, v), (x1 + dx, v + dy), (x1 + dx, v + h + dy), (x1, v + h)], right, scale(right, 0.88))
    _poly(c, [(x0, v + h), (x1, v + h), (x1 + dx, v + h + dy), (x0 + dx, v + h + dy)], top, scale(top, 0.94))
    _rr(c, x0, v, x1, v + h, scale(front, 1.07), scale(front, 0.93), r)


def _pool(S, u, v, a, b, col, alpha=0.3, power=1.4, add=True):
    """Wide light pool made of a few overlapping soft discs (cheaper than one wide disc)."""
    n = max(1, int(round(a / max(0.05, b * 2.2))))
    if n == 1:
        S.soft(u, v, a, b, col, alpha, power, add=add)
        return
    for i in range(n):
        uu = u + (i - (n - 1) / 2.0) * (2.0 * a / n) * 0.78
        S.soft(uu, v, a / n * 1.45, b, col, alpha * 0.78, power, add=add)


def _boards(S, u0, v0, u1, v1, base, plank=0.08, seed=3, grain=6):
    """Fast wooden boards running left to right: flat tone strips, dark seams and a few grain lines (cheaper than Stage.wood)."""
    rng = random.Random(seed)
    n = max(1, int(round((v1 - v0) / plank)))
    for i in range(n):
        a, b = v0 + (v1 - v0) * i / n, v0 + (v1 - v0) * (i + 1) / n
        _sfill(S, u0, a, u1, b + 0.002, scale(base, 1.0 + rng.uniform(-0.07, 0.07)))
        _shair(S, u0, b, u1, b, scale(base, 0.55), 0.7)
        for _ in range(grain):
            x = rng.uniform(u0, u1)
            y = rng.uniform(a, b)
            _shair(S, x, y, min(u1, x + rng.uniform(0.15, 0.5)), y + rng.uniform(-0.004, 0.004), scale(base, rng.uniform(0.72, 0.88)), 0.35)


def _sky(P, sunset=False):
    if _dk(P):
        return scale(P.wall_top, 0.8), mix(scale(P.wall_bot, 1.5), P.accent_dark, 0.35)
    if sunset or P.mood == "warm":
        return mix(P.wall_top, (0.98, 0.70, 0.52), 0.45), mix(P.wall_bot, (1.0, 0.88, 0.66), 0.7)
    return mix(P.wall_top, (0.55, 0.78, 0.97), 0.75), mix(P.wall_bot, (0.90, 0.96, 1.0), 0.7)


def _lines(c, u0, u1, v, n, step, col, w=0.006, alpha=0.8, jitter=None):
    """n horizontal text-like bars (placeholder lines of a document): the last one is shorter."""
    for k in range(n):
        end = u1 if k < n - 1 else u0 + (u1 - u0) * 0.55
        if jitter:
            end -= jitter[k % len(jitter)] * (u1 - u0)
        c.line(u0, v - k * step, end, v - k * step, w, col, alpha)


def _spoke_wheel(c, u, v, r, rim=STEEL, tyre=(0.06, 0.06, 0.07), n=12, disc=None):
    """Side view wheel: tyre, rim, spokes, hub (and a brake disc)."""
    _oval(c, u, v, r, r, mix(tyre, WHITE, 0.10), scale(tyre, 0.55))
    _oval(c, u, v, r * 0.80, r * 0.80, scale(rim, 0.55), scale(rim, 0.35))
    _oval(c, u - r * 0.01, v + r * 0.01, r * 0.74, r * 0.74, (0.15, 0.15, 0.17), (0.09, 0.09, 0.10))
    for k in range(n):
        a = math.radians(360.0 * k / n + 7)
        c.line(u + math.cos(a) * r * 0.10, v + math.sin(a) * r * 0.10, u + math.cos(a) * r * 0.76, v + math.sin(a) * r * 0.76, r * 0.020, mix(rim, WHITE, 0.2), 0.75)
    if disc is not None:
        _oval(c, u, v, r * 0.46, r * 0.46, mix(disc, WHITE, 0.15), scale(disc, 0.7), 0.95)
        _oval(c, u, v, r * 0.30, r * 0.30, (0.14, 0.14, 0.16), (0.10, 0.10, 0.12))
    _oval(c, u, v, r * 0.12, r * 0.12, mix(rim, WHITE, 0.35), scale(rim, 0.8))
    craft.arc(c, u, v, r * 0.93, r * 0.93, 95, 170, r * 0.05, WHITE, 0.22, steps=6)


# ====================================================================================== car rental
@sprop("biz_rental_suv", aspect=2.42, fill=1.20)
def biz_rental_suv(c, color):
    body = color or (0.86, 0.17, 0.14)
    _car(c, "suv", body, caliper=(0.10, 0.10, 0.12), sheen=1.1)
    k = CARS["suv"]
    rv = k["roof"]
    # roof rails with a strapped travel bag and a soft duffel
    for u0, u1 in ((-1.18, 0.30),):
        c.line(u0, rv + 0.015, u1, rv + 0.015, 0.016, (0.12, 0.12, 0.14), 0.95)
        for uu in (u0 + 0.05, (u0 + u1) / 2, u1 - 0.05):
            c.line(uu, rv - 0.01, uu, rv + 0.02, 0.016, (0.12, 0.12, 0.14), 0.95)
    bag = mix((0.78, 0.60, 0.38), body, 0.12)
    _rr(c, -1.05, rv + 0.025, -0.28, rv + 0.19, mix(bag, WHITE, 0.14), scale(bag, 0.70), 0.05)
    _rr(c, -0.98, rv + 0.15, -0.34, rv + 0.205, scale(bag, 0.62), scale(bag, 0.50), 0.03)
    for uu in (-0.85, -0.50):
        _rr(c, uu - 0.016, rv + 0.025, uu + 0.016, rv + 0.19, (0.10, 0.10, 0.12), (0.06, 0.06, 0.07), 0.0, 0.9)
    _rr(c, -0.20, rv + 0.025, 0.22, rv + 0.135, (0.20, 0.22, 0.28), (0.12, 0.13, 0.17), 0.04)
    gloss(c, -0.55, rv + 0.15, 0.20, 0.018, 0, 0.35)
    # a plain accent band on the doors (rental livery) without any lettering
    _poly(c, [(-0.88, 0.30), (0.62, 0.30), (0.62, 0.345), (-0.88, 0.345)], mix(body, WHITE, 0.82), None, 0.7)


@sprop("biz_rental_sedan", aspect=3.1, fill=1.0)
def biz_rental_sedan(c, color):
    _car(c, "sedan", color or (0.92, 0.93, 0.95), caliper=(0.10, 0.10, 0.12))


@sprop("biz_map_pin", aspect=0.55, fill=0.98)
def biz_map_pin(c, color):
    acc = color or (0.88, 0.18, 0.16)
    for i, (a, b, al) in enumerate(((0.26, 0.09, 0.28), (0.18, 0.062, 0.45), (0.10, 0.035, 0.7))):       # target rings on the ground
        c.ellipse(0.0, 0.0, a, b, mix(acc, WHITE, 0.2 * i), lift=0, alpha=al)
    ao(c, 0.0, 0.0, 0.18, 0.03, 0.6)
    r, cy = 0.215, 0.72
    pts = [(r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-52, 233, 12)]
    _poly(c, pts + [(0.0, 0.09)], mix(acc, WHITE, 0.14), scale(acc, 0.68))
    # lit left edge and shaded right
    _poly(c, [(-0.17, 0.66), (-0.20, 0.74), (-0.14, 0.88), (-0.10, 0.83), (-0.13, 0.72)], WHITE, None, 0.32)
    _poly(c, [(0.14, 0.60), (0.20, 0.70), (0.16, 0.83), (0.06, 0.34)], BLACK, None, 0.12)
    _oval(c, 0.0, cy, r * 0.42, r * 0.42, (0.97, 0.97, 0.97), (0.86, 0.86, 0.88))
    gloss(c, -0.08, 0.86, 0.07, 0.04, 30, 0.45)


@sprop("biz_car_keys", aspect=3.9, fill=0.20)
def biz_car_keys(c, color):
    acc = color or (0.88, 0.18, 0.16)
    ao(c, 0.0, 0.0, 0.34, 0.05, 0.5)
    c.ellipse(0.02, 0.07, 0.07, 0.035, (0.74, 0.76, 0.80), lift=0.15)           # ring
    c.ellipse(0.02, 0.07, 0.048, 0.02, (0.35, 0.36, 0.40), lift=0, alpha=0.8)
    _poly(c, [(-0.12, 0.02), (-0.03, 0.02), (0.00, 0.11), (-0.10, 0.12)], (0.74, 0.76, 0.80), (0.42, 0.44, 0.48))
    for i in range(4):                                                              # key blade and teeth
        _poly(c, [(-0.42 + i * 0.07, 0.04), (-0.38 + i * 0.07, 0.04), (-0.37 + i * 0.07, 0.075), (-0.41 + i * 0.07, 0.075)], (0.62, 0.64, 0.68), None)
    _rr(c, -0.44, 0.075, -0.10, 0.115, mix(STEEL, WHITE, 0.2), scale(STEEL, 0.65), 0.012)
    _rr(c, 0.10, 0.02, 0.34, 0.20, (0.14, 0.15, 0.18), (0.05, 0.05, 0.07), 0.05)   # fob
    _rr(c, 0.14, 0.095, 0.30, 0.165, acc, scale(acc, 0.72), 0.03)
    c.ellipse(0.22, 0.062, 0.022, 0.012, (0.6, 0.62, 0.66), lift=0.1)
    gloss(c, 0.17, 0.185, 0.05, 0.01, 0, 0.4)


@sprop("biz_cone", aspect=0.78, fill=0.5)
def biz_cone(c, color):
    ao(c, 0.0, 0.0, 0.30, 0.05, 0.5)
    _rr(c, -0.20, 0.0, 0.20, 0.035, (0.22, 0.22, 0.25), (0.12, 0.12, 0.14), 0.01)
    _poly(c, [(-0.16, 0.035), (0.16, 0.035), (0.04, 0.50), (-0.04, 0.50)], (1.0, 0.52, 0.12), (0.88, 0.34, 0.06))
    _poly(c, [(-0.10, 0.19), (0.10, 0.19), (0.075, 0.30), (-0.075, 0.30)], (0.97, 0.97, 0.97), (0.84, 0.84, 0.86))
    _poly(c, [(-0.15, 0.04), (-0.10, 0.04), (-0.025, 0.48), (-0.04, 0.48)], WHITE, None, 0.28)


@niche("car-rental", "Car rental and self-drive hire", subjects=("biz_rental_suv",),
       strong=("car rental", "car rentals", "rent a car", "self drive car", "self drive cars", "self drive rental", "car hire", "car on rent", "cars on rent",
               "car rental service", "rental cars", "chauffeur driven car", "car with driver", "airport pickup and drop", "किराये की कार", "कार किराये पर", "कार रेंटल",
               "गाड़ी किराये पर", "रेंट ए कार", "किराए की गाड़ी", "kiraye ki gaadi", "kiraye par gaadi", "gaadi kiraye par", "car kiraye par", "rent a car service"),
       weak=("rental", "rent", "hire", "self drive", "outstation", "chauffeur", "rent a cab", "सेल्फ ड्राइव", "किराये", "पर्यटन गाड़ी", "wedding car"),
       accent="#ff6a1a", mood="dark", group="auto",
       avoid=("taxi service", "cab booking", "ola", "uber", "car showroom", "car dealer", "dealership", "new cars", "used cars", "second hand car", "car wash",
              "car repair", "driving school", "बाइक", "टैक्सी", "कार शोरूम"))
def car_rental(S):
    P = S.pal
    dk = _dk(P)
    sk_t, sk_b = _sky(P, sunset=True)
    rng = random.Random(31)
    asph = _tn(P, (0.34, 0.34, 0.37), 0.5)
    with S.far():
        S.wall(sk_t, sk_b, 0.62)
        S.glow(0.55, 0.52, 0.9, (1.0, 0.72, 0.45) if not dk else (0.6, 0.5, 0.9), 0.55 if not dk else 0.35)
        for k in range(14):                                                           # tree line in two depths
            u = -0.4 + k * 0.19
            h = 0.10 + rng.random() * 0.10
            S.circle(u, 0.62 - h * 0.5, h * 0.8, _tn(P, mix((0.28, 0.42, 0.28), P.accent_dark, 0.12), 0.35), lift=0.08, soft=3.0)
        # rental office: low building with glass and a long accent canopy
        S.rect(1.55, 0.50, 0.95, 0.20, _tn(P, (0.90, 0.90, 0.92), 0.30), lift=0.04)
        S.rect(1.50, 0.51, 0.80, 0.11, _tn(P, (0.55, 0.72, 0.85), 0.28), lift=0.12)
        S.glow(1.50, 0.51, 0.7, (1.0, 0.85, 0.55), 0.55 if dk else 0.15)
        for k in range(5):
            S.rect(1.15 + k * 0.17, 0.51, 0.008, 0.11, _tn(P, (0.9, 0.9, 0.92), 0.3), lift=0.0)
        S.rect(1.55, 0.395, 1.0, 0.03, P.accent, r=0.008, lift=0.08)
        for u in (1.12, 1.98):
            S.rect(u, 0.50, 0.012, 0.22, _tn(P, (0.8, 0.8, 0.82), 0.3), lift=0.0)
        # lamp posts with warm bokeh and distant cars in a row
        for u in (0.10, 1.05, 1.95):
            S.rect(u, 0.34, 0.010, 0.52, _tn(P, (0.25, 0.27, 0.3), 0.5), lift=0.0)
            S.rect(u + 0.03, 0.09, 0.07, 0.012, _tn(P, (0.25, 0.27, 0.3), 0.5), lift=0.0)
            S.glow(u + 0.06, 0.11, 0.34, (1.0, 0.88, 0.6), 0.7 if dk else 0.22)
        for i, (u, col) in enumerate(((0.35, (0.85, 0.86, 0.88)), (0.60, (0.15, 0.2, 0.4)), (1.75, (0.9, 0.9, 0.92)), (1.98, mix(P.accent, WHITE, 0.2)))):
            S.put("biz_rental_sedan", u, 0.665, 0.11, color=_tn(P, col, 0.55), shadow=False, framed=False)
        S.bokeh(8, 0.0, 0.2, 2.0, 0.58, [(1.0, 0.8, 0.45), (1.0, 0.6, 0.35), (0.95, 0.95, 1.0)], 0.01, 0.026, 0.38 if dk else 0.16)
        S.rect(1.0, 0.628, 14.0, 0.03, _tn(P, (0.62, 0.62, 0.62), 0.4), lift=0.0)             # kerb
        S.floor(0.645, asph, scale(asph, 0.62))
        S.soft(1.1, 0.88, 1.4, 0.24, P.light, 0.32 if not dk else 0.46, 1.4, add=True)
    # parking bays in perspective, a dashed lane line, wet-look light streaks
    line_c = _tn(P, WHITE, 0.62)
    for k in range(-5, 9):
        u = 1.2 + k * 0.30
        _spoly(S, [(u, 0.70), (u + 0.012, 0.70), (u + 0.012 + (u - 1.2) * 0.38, 1.60), (u + (u - 1.2) * 0.38, 1.60)], line_c, None, 0.55)
    S.rect(1.0, 0.70, 14.0, 0.007, line_c, alpha=0.7, lift=0.0)
    for k in range(-4, 10):
        u = 1.0 + k * 0.42
        _spoly(S, [(u, 1.095), (u + 0.26, 1.095), (u + 0.28, 1.14), (u - 0.02, 1.14)], line_c, None, 0.5)
    S.put("biz_rental_sedan", 0.45, 0.86, 0.17, color=_tn(P, mix((0.86, 0.88, 0.92), P.accent, 0.1), 0.7), shadow_alpha=0.3, framed=False)
    S.put("biz_rental_suv", 1.22, 0.99, 0.40, color=(P.accent if not dk else mix(P.accent, WHITE, 0.08)), subject=True, shadow_w=1.0, shadow_alpha=0.4)
    S.put("biz_map_pin", 0.78, 1.04, 0.33, color=(P.accent if dk else (0.88, 0.16, 0.14)), shadow_w=0.25)
    S.put("biz_car_keys", 1.60, 1.05, 0.07, color=P.accent, shadow=False)
    S.put("biz_cone", 1.74, 1.00, 0.08, shadow_w=0.14, framed=False)
    S.focus("detail", 0.95, 0.90)
    with S.near(blur=18):
        S.soft(0.25, 1.06, 0.32, 0.10, P.accent_light, 0.20, 1.2, add=True)
        S.circle(1.92, 1.06, 0.075, mix(P.accent, WHITE, 0.15) if not dk else scale(P.accent, 0.5), lift=0.1, alpha=0.8)


# ====================================================================================== bike and scooter garage
@sprop("biz_motorcycle", aspect=1.95, fill=1.0)
def biz_motorcycle(c, color):
    body = color or (0.88, 0.30, 0.10)
    R = 0.29
    rx, fx, cy = -0.63, 0.64, 0.29
    _spoke_wheel(c, rx, cy, R, n=14)
    _spoke_wheel(c, fx, cy, R, n=14, disc=(0.70, 0.72, 0.76))
    # swingarm, rear shock with a coloured spring
    _poly(c, [(rx, cy + 0.045), (-0.12, 0.395), (-0.12, 0.33), (rx, cy - 0.045)], mix(STEEL, WHITE, 0.15), scale(STEEL, 0.55))
    c.line(-0.33, 0.66, -0.43, 0.36, 0.035, scale(body, 0.8), 0.95)
    for k in range(5):
        c.line(-0.345 - k * 0.019, 0.62 - k * 0.058, -0.395 - k * 0.019, 0.60 - k * 0.058, 0.012, mix(body, WHITE, 0.3), 0.95)
    # exhaust: header pipe, chrome muffler
    for (a, b) in (((0.20, 0.50), (0.16, 0.27)), ((0.16, 0.27), (-0.10, 0.22)), ((-0.10, 0.22), (-0.32, 0.27))):
        c.line(a[0], a[1], b[0], b[1], 0.042, scale(CHROME, 0.78), 1.0)
        c.line(a[0] - 0.008, a[1] + 0.008, b[0] - 0.008, b[1] + 0.008, 0.012, WHITE, 0.55)
    _poly(c, [(-0.94, 0.49), (-0.32, 0.34), (-0.32, 0.20), (-0.94, 0.36)], mix(CHROME, WHITE, 0.2), scale(CHROME, 0.55))
    _poly(c, [(-0.90, 0.455), (-0.36, 0.325), (-0.36, 0.30), (-0.90, 0.43)], WHITE, None, 0.45)
    _oval(c, -0.945, 0.425, 0.022, 0.07, (0.08, 0.08, 0.09), (0.04, 0.04, 0.05))
    # engine: crankcase, finned cylinder, head cover
    _oval(c, 0.0, 0.40, 0.27, 0.17, mix((0.32, 0.33, 0.37), WHITE, 0.08), (0.12, 0.12, 0.15))
    _oval(c, -0.12, 0.38, 0.09, 0.09, (0.55, 0.57, 0.62), (0.28, 0.29, 0.33))
    _oval(c, -0.12, 0.38, 0.045, 0.045, (0.18, 0.18, 0.20), (0.12, 0.12, 0.14))
    _poly(c, [(-0.03, 0.46), (0.20, 0.47), (0.34, 0.72), (0.12, 0.74)], (0.30, 0.31, 0.35), (0.11, 0.11, 0.14))
    for k in range(7):
        t = k / 6.0
        du = 0.15 * t
        c.line(-0.04 + du, 0.495 + 0.22 * t, 0.205 + du + 0.01, 0.505 + 0.22 * t, 0.017, (0.62, 0.64, 0.70), 0.85)
    _rr(c, 0.08, 0.72, 0.38, 0.795, (0.26, 0.27, 0.31), (0.12, 0.12, 0.14), 0.02)
    _rr(c, 0.14, 0.60, 0.27, 0.69, (0.62, 0.64, 0.70), (0.40, 0.42, 0.46), 0.01, 0.0)
    # frame tubes
    c.line(0.48, 0.86, 0.17, 0.43, 0.040, scale(STEEL, 0.55), 1.0)
    c.line(-0.30, 0.70, -0.10, 0.56, 0.036, scale(STEEL, 0.55), 1.0)
    # chain run between the sprockets
    c.line(rx, cy + 0.07, -0.12, 0.425, 0.010, (0.12, 0.12, 0.13), 0.95)
    c.line(rx, cy - 0.07, -0.12, 0.335, 0.010, (0.12, 0.12, 0.13), 0.95)
    _oval(c, rx, cy, 0.075, 0.075, (0.58, 0.60, 0.64), (0.34, 0.35, 0.40))
    # tail section, seat, fuel tank
    _poly(c, [(-1.00, 0.69), (-0.84, 0.78), (-0.58, 0.76), (-0.66, 0.60)], mix(body, WHITE, 0.08), scale(body, 0.62))
    c.glow(-0.99, 0.69, 0.10, (1.0, 0.12, 0.10), 0.55)
    _poly(c, [(-0.99, 0.70), (-0.95, 0.74), (-0.93, 0.68)], (1.0, 0.15, 0.12), None)
    _poly(c, [(-0.86, 0.75), (-0.78, 0.805), (-0.38, 0.805), (-0.26, 0.755), (-0.34, 0.69), (-0.80, 0.69)], (0.17, 0.17, 0.19), (0.05, 0.05, 0.06))
    _poly(c, [(-0.80, 0.795), (-0.40, 0.795), (-0.42, 0.785), (-0.78, 0.785)], WHITE, None, 0.22)
    _poly(c, [(-0.28, 0.74), (-0.20, 0.87), (0.10, 0.935), (0.38, 0.925), (0.50, 0.855), (0.40, 0.775), (0.08, 0.725)], mix(body, WHITE, 0.16), scale(body, 0.56))
    _poly(c, [(-0.20, 0.84), (0.08, 0.915), (0.32, 0.912), (0.10, 0.88), (-0.14, 0.80)], WHITE, None, 0.40)
    soft_disc(c, 0.12, 0.84, 0.20, 0.035, WHITE, 0.30, 1.1, 8, True)
    # front end: fork, mudguard, headlamp, bars
    c.line(fx, cy + 0.01, 0.49, 0.92, 0.050, scale(CHROME, 0.74), 1.0)
    c.line(fx - 0.012, cy + 0.03, 0.478, 0.90, 0.016, WHITE, 0.5)
    c.line(fx + 0.025, cy + 0.01, 0.52, 0.90, 0.020, scale(STEEL, 0.5), 0.9)
    arcp = [(fx + 0.35 * math.cos(math.radians(a)), cy + 0.35 * math.sin(math.radians(a))) for a in range(28, 152, 12)]
    arci = [(fx + 0.315 * math.cos(math.radians(a)), cy + 0.315 * math.sin(math.radians(a))) for a in range(150, 29, -12)]
    _poly(c, arcp + arci, mix(body, WHITE, 0.14), scale(body, 0.62))
    _oval(c, 0.60, 0.885, 0.080, 0.085, mix(CHROME, WHITE, 0.2), scale(CHROME, 0.5))
    _oval(c, 0.625, 0.885, 0.058, 0.066, (0.98, 0.95, 0.80), (0.86, 0.80, 0.55))
    c.glow(0.66, 0.885, 0.28, (1.0, 0.95, 0.75), 0.45)
    c.line(0.49, 0.93, 0.38, 1.00, 0.026, (0.09, 0.09, 0.10), 1.0)
    c.line(0.38, 1.00, 0.30, 0.995, 0.034, (0.05, 0.05, 0.06), 1.0)
    c.line(0.45, 0.955, 0.49, 0.985, 0.012, scale(CHROME, 0.7), 1.0)
    _oval(c, 0.455, 0.945, 0.032, 0.026, (0.12, 0.13, 0.16), (0.05, 0.05, 0.07))
    c.line(0.215, 0.33, 0.30, 0.30, 0.020, (0.1, 0.1, 0.11), 1.0)         # footrest


@sprop("biz_scooter", aspect=1.65, fill=0.95)
def biz_scooter(c, color):
    body = color or (0.30, 0.55, 0.85)
    R = 0.19
    _spoke_wheel(c, -0.52, R, R, n=8)
    _spoke_wheel(c, 0.58, R, R, n=8, disc=(0.7, 0.72, 0.76))
    _poly(c, [(-0.78, 0.42), (-0.72, 0.72), (-0.35, 0.74), (-0.05, 0.50), (0.18, 0.30), (0.28, 0.21), (-0.60, 0.18)], mix(body, WHITE, 0.10), scale(body, 0.55))
    _poly(c, [(-0.72, 0.70), (-0.60, 0.76), (-0.10, 0.76), (-0.12, 0.72), (-0.60, 0.70)], (0.16, 0.16, 0.18), (0.05, 0.05, 0.06))
    _poly(c, [(0.22, 0.28), (0.36, 0.86), (0.46, 0.86), (0.42, 0.28)], mix(body, WHITE, 0.14), scale(body, 0.6))
    c.line(0.58, 0.20, 0.44, 0.78, 0.04, scale(CHROME, 0.8), 1.0)
    c.line(0.42, 0.90, 0.28, 0.95, 0.03, (0.1, 0.1, 0.11), 1.0)
    _oval(c, 0.50, 0.83, 0.07, 0.07, mix(CHROME, WHITE, 0.3), scale(CHROME, 0.5))
    c.glow(0.55, 0.83, 0.24, (1.0, 0.95, 0.75), 0.4)
    _poly(c, [(0.30, 0.34), (0.60, 0.40), (0.62, 0.30), (0.30, 0.23)], mix(body, WHITE, 0.1), scale(body, 0.6))
    gloss(c, -0.3, 0.70, 0.20, 0.03, 8, 0.35)


@sprop("biz_spanners", aspect=4.0, fill=0.30)
def biz_spanners(c, color):
    ao(c, 0.0, 0.02, 0.9, 0.14, 0.45)
    steel = (0.66, 0.68, 0.73)
    for ang, off, ln, ring in ((-14, 0.07, 0.55, False), (3, 0.14, 0.62, True), (21, 0.205, 0.5, False)):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        u0, v0 = -0.55 * ca, off - 0.55 * sa * 0.6
        v0 = 0.035 + (off - 0.07) * 0.9
        x0, y0 = -ln * ca, v0 - ln * sa * 0.55
        x1, y1 = ln * ca, v0 + ln * sa * 0.55
        c.line(x0, y0, x1, y1, 0.038, scale(steel, 0.55), 1.0)
        c.line(x0, y0 + 0.006, x1, y1 + 0.006, 0.030, mix(steel, WHITE, 0.18), 1.0)
        c.line(x0 + 0.04 * ca, y0 + 0.014, x1 - 0.04 * ca, y1 + 0.014, 0.008, WHITE, 0.55)
        c.ellipse(x1, y1, 0.062, 0.048, mix(steel, WHITE, 0.12), lift=0.1)
        c.ellipse(x1 + 0.012, y1, 0.026, 0.019, (0.16, 0.16, 0.18), lift=0, alpha=0.95)
        if ring:
            c.ellipse(x0, y0, 0.056, 0.044, mix(steel, WHITE, 0.12), lift=0.1)
            c.ellipse(x0, y0, 0.028, 0.020, (0.18, 0.18, 0.20), lift=0, alpha=0.95)
        else:
            c.ellipse(x0, y0, 0.056, 0.044, mix(steel, WHITE, 0.12), lift=0.1)
            c.ellipse(x0 - 0.012, y0, 0.024, 0.017, (0.16, 0.16, 0.18), lift=0, alpha=0.95)


@sprop("biz_tyre", aspect=1.18, fill=1.0)
def biz_tyre(c, color):
    ao(c, 0.04, 0.0, 0.85, 0.12, 0.5)
    _spoke_wheel(c, 0.15, 0.48, 0.47, tyre=(0.11, 0.11, 0.12), n=10)
    _spoke_wheel(c, -0.04, 0.50, 0.50, tyre=(0.07, 0.07, 0.08), rim=(0.72, 0.74, 0.78), n=12, disc=(0.7, 0.72, 0.76))
    craft.arc(c, -0.04, 0.50, 0.46, 0.46, 20, 160, 0.012, WHITE, 0.16, steps=8)


@sprop("biz_oil_can", aspect=0.72, fill=0.9)
def biz_oil_can(c, color):
    acc = color or (0.95, 0.65, 0.12)
    ao(c, 0.0, 0.0, 0.50, 0.08, 0.5)
    _hfill(c, -0.26, 0.0, 0.26, 0.60, _cyl_fn(mix(acc, WHITE, 0.15), scale(acc, 0.55), 0.35))
    _poly(c, [(-0.26, 0.60), (0.26, 0.60), (0.18, 0.72), (-0.18, 0.72)], mix(acc, WHITE, 0.25), scale(acc, 0.7))
    _rr(c, -0.07, 0.72, 0.07, 0.80, scale(acc, 0.65), scale(acc, 0.45), 0.01)
    c.line(0.04, 0.78, 0.30, 0.86, 0.045, (0.80, 0.82, 0.86), 1.0)
    c.line(0.30, 0.86, 0.34, 0.80, 0.03, (0.80, 0.82, 0.86), 1.0)
    _rr(c, -0.26, 0.21, 0.26, 0.45, (0.10, 0.10, 0.12), (0.05, 0.05, 0.06), 0.0, 0.88)
    _rr(c, -0.18, 0.30, 0.18, 0.37, mix(acc, WHITE, 0.4), mix(acc, WHITE, 0.2), 0.02)
    c.ellipse(0.0, 0.40, 0.08, 0.04, WHITE, lift=0, alpha=0.8)
    c.ellipse(0.34, 0.76, 0.018, 0.012, acc, lift=0.2, alpha=0.9)
    _poly(c, [(-0.22, 0.04), (-0.17, 0.04), (-0.17, 0.58), (-0.22, 0.58)], WHITE, None, 0.26)


@sprop("biz_toolcart", aspect=1.05, fill=0.98)
def biz_toolcart(c, color):
    col = color or (0.78, 0.12, 0.12)
    ao(c, 0.04, 0.0, 1.05, 0.16, 0.5)
    for uu in (-0.34, 0.32):
        c.ellipse(uu, 0.035, 0.05, 0.035, (0.08, 0.08, 0.09), lift=0.05)
    _box3(c, -0.07, 0.07, 0.82, 0.74, 0.52, col, top=mix(col, WHITE, 0.2), right=scale(col, 0.62), r=0.015)
    # drawers on the front face, chrome handles, a lock
    for k in range(5):
        v0 = 0.10 + k * 0.145
        c.line(-0.47, v0 + 0.145, 0.33, v0 + 0.145, 0.008, scale(col, 0.45), 0.9)
        _rr(c, -0.24, v0 + 0.050, 0.10, v0 + 0.078, CHROME, scale(CHROME, 0.6), 0.012)
        c.line(-0.46, v0 + 0.14, 0.32, v0 + 0.14, 0.004, mix(col, WHITE, 0.5), 0.5)
    c.ellipse(0.24, 0.77, 0.014, 0.014, (0.9, 0.8, 0.3), lift=0.1)
    # open top tray: spanners and a screwdriver laid in it
    _poly(c, [(-0.44, 0.835), (0.32, 0.835), (0.46, 0.90), (-0.30, 0.90)], (0.12, 0.12, 0.14), (0.20, 0.20, 0.23))
    c.line(-0.30, 0.86, 0.14, 0.87, 0.022, (0.7, 0.72, 0.76), 1.0)
    c.line(-0.26, 0.885, 0.20, 0.89, 0.018, (0.62, 0.64, 0.68), 1.0)
    c.line(-0.10, 0.865, 0.30, 0.875, 0.026, mix((0.95, 0.65, 0.12), WHITE, 0.1), 1.0)
    c.ellipse(0.30, 0.876, 0.02, 0.014, (0.72, 0.74, 0.78), lift=0.1)
    _poly(c, [(-0.46, 0.76), (-0.44, 0.76), (-0.44, 0.15), (-0.46, 0.15)], WHITE, None, 0.22)


@sprop("biz_bicycle", aspect=2.2, fill=0.80)
def biz_bicycle(c, color):
    acc = color or (0.25, 0.55, 0.85)
    for u in (-0.55, 0.55):
        c.ring(u, 0.33, 0.325, 0.034, (0.07, 0.07, 0.08))
        c.ring(u, 0.33, 0.285, 0.010, (0.7, 0.72, 0.76))
        for k in range(8):
            a = math.radians(k * 45 + 5)
            c.line(u, 0.33, u + 0.28 * math.cos(a), 0.33 + 0.28 * math.sin(a), 0.004, (0.66, 0.68, 0.72), 0.75)
    for a_, b_ in (((-0.55, 0.33), (-0.05, 0.25)), ((-0.55, 0.33), (-0.15, 0.70)), ((-0.15, 0.68), (0.42, 0.66)), ((-0.05, 0.25), (0.42, 0.64)),
                   ((-0.05, 0.25), (-0.15, 0.70))):
        c.line(a_[0], a_[1], b_[0], b_[1], 0.032, acc, 1.0)
        c.line(a_[0], a_[1] + 0.008, b_[0], b_[1] + 0.008, 0.008, mix(acc, WHITE, 0.5), 0.55)
    c.line(0.42, 0.66, 0.55, 0.33, 0.026, scale(STEEL, 0.7), 1.0)
    c.line(0.42, 0.72, 0.33, 0.77, 0.022, (0.1, 0.1, 0.11), 1.0)
    c.line(0.42, 0.62, 0.42, 0.74, 0.026, scale(STEEL, 0.7), 1.0)
    c.line(-0.24, 0.73, -0.02, 0.735, 0.044, (0.08, 0.08, 0.09), 1.0)
    c.ring(-0.05, 0.25, 0.07, 0.014, (0.55, 0.57, 0.6))
    c.line(-0.05, 0.25, 0.04, 0.17, 0.016, (0.12, 0.12, 0.14), 1.0)


def _pegboard(S, u0, v0, u1, v1, base, tool, rng, rows=3):
    """A wall panel with silhouettes of hanging tools (spanners, pliers, hammers) as plain shapes."""
    S.rect((u0 + u1) / 2, (v0 + v1) / 2, u1 - u0, v1 - v0, base, r=0.006, lift=0.05)
    n = int((u1 - u0) / 0.045)
    for r in range(rows):
        v = v0 + 0.05 + r * (v1 - v0 - 0.08) / max(1, rows - 1) * 0.92
        u = u0 + 0.04
        while u < u1 - 0.06:
            kind = rng.randrange(4)
            if kind == 0:                                           # spanner
                ln = rng.uniform(0.07, 0.11)
                S.line(u, v, u, v + ln, 0.012, tool, 0.95)
                S.circle(u, v + ln + 0.006, 0.014, tool, lift=0, alpha=0.95, soft=1.0)
                u += 0.04
            elif kind == 1:                                         # hammer
                S.line(u, v, u, v + 0.10, 0.011, mix(tool, (0.6, 0.4, 0.2), 0.35), 0.95)
                S.rect(u, v - 0.005, 0.05, 0.022, tool, lift=0, alpha=0.95)
                u += 0.07
            elif kind == 2:                                         # pliers
                S.line(u - 0.008, v, u + 0.01, v + 0.08, 0.010, tool, 0.95)
                S.line(u + 0.008, v, u - 0.01, v + 0.08, 0.010, tool, 0.95)
                u += 0.05
            else:                                                   # screwdriver
                S.line(u, v + 0.015, u, v + 0.11, 0.006, tool, 0.9)
                S.rect(u, v + 0.0, 0.016, 0.04, mix(tool, (0.9, 0.5, 0.1), 0.4), r=0.004, lift=0, alpha=0.95)
                u += 0.03
    S.rect((u0 + u1) / 2, v0, u1 - u0, 0.008, scale(base, 0.6), lift=0.0)


@niche("bike-garage", "Bike and scooter repair garage", subjects=("biz_motorcycle",),
       strong=("bike garage", "bike repair", "bike repair shop", "bike service centre", "bike service center", "motorcycle repair", "motorcycle garage", "scooter repair",
               "scooter garage", "two wheeler garage", "two wheeler repair", "two wheeler service", "bike mechanic", "bike servicing", "bike workshop", "bike and scooter garage", "bike puncture repair",
               "बाइक गैरेज", "बाइक रिपेयर", "बाइक सर्विस सेंटर", "बाइक मैकेनिक", "स्कूटर रिपेयर", "मोटरसाइकिल मरम्मत", "स्कूटर गैराज", "bike garage wala", "bike ki repairing",
               "cycle repair shop"),
       weak=("garage", "bike", "scooter", "motorcycle", "mechanic", "puncture", "chain", "tuning", "service centre", "गैरेज", "मैकेनिक", "रिपेयर"),
       accent="#ff6a1a", mood="dark", group="auto",
       avoid=("bike showroom", "motorcycle showroom", "two wheeler showroom", "bike dealer", "bike dealership", "car repair", "car garage", "car service", "car wash", "tyre shop",
              "car showroom", "बाइक शोरूम", "कार रिपेयर"))
def bike_garage(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(47)
    wall_c = _tn(P, mix(P.wall_top, (0.62, 0.63, 0.66), 0.35), 1.0) if not dk else mix(scale(P.wall_top, 1.1), (0.14, 0.15, 0.18), 0.5)
    conc = mix(P.floor_top, (0.50, 0.50, 0.52), 0.6) if not dk else (0.19, 0.19, 0.22)
    tool_c = (0.10, 0.10, 0.12) if not dk else (0.62, 0.64, 0.68)
    with S.far():
        S.wall(wall_c, scale(wall_c, 0.84), 0.62)
        for k in range(-2, 16):                                                       # vertical corrugation / panel seams
            S.rect(-0.2 + k * 0.17, 0.30, 0.006, 0.60, scale(wall_c, 0.80), lift=0.0)
        # roller shutter door at the right with a bright street gap below
        S.rect(1.78, 0.30, 0.50, 0.58, scale(wall_c, 0.9), lift=0.04)
        for k in range(14):
            S.rect(1.78, 0.045 + k * 0.042, 0.50, 0.006, scale(wall_c, 0.62), lift=0.0)
        # pegboard of tools above a workbench, shelf with oil cans and tyres at the left
        _pegboard(S, 0.02, 0.10, 0.80, 0.44, scale(P.accent_dark, 0.6) if dk else mix(P.accent_light, (0.7, 0.7, 0.72), 0.5), tool_c, rng)
        S.rect(0.42, 0.50, 0.80, 0.05, _tn(P, (0.52, 0.36, 0.22), 0.5), lift=0.06)
        S.rect(0.42, 0.56, 0.74, 0.09, scale(wall_c, 0.6), lift=0.0)
        for k in range(3):
            S.rect(0.12 + k * 0.30, 0.575, 0.22, 0.05, scale(P.accent, 0.8), r=0.01, lift=0.12)
        for k in range(2):
            S.circle(1.12 + k * 0.20, 0.545, 0.075, (0.05, 0.05, 0.06), lift=0.05)
            S.circle(1.12 + k * 0.20, 0.545, 0.033, (0.55, 0.57, 0.62) if not dk else (0.30, 0.31, 0.34), lift=0.05)
        # bicycle hung on the wall rail, a hanging worklight, a warning stripe near the floor
        S.put("biz_bicycle", 1.30, 0.42, 0.26, color=_tn(P, (0.25, 0.55, 0.85), 0.55), shadow=False, framed=False)
        S.line(0.9, 0.12, 1.7, 0.12, 0.008, scale(wall_c, 0.45), 0.9)
        for u in (0.55, 1.20, 1.70):
            S.line(u, 0.0, u, 0.07, 0.004, (0.1, 0.1, 0.1), 0.9)
            S.poly([(u - 0.07, 0.12), (u + 0.07, 0.12), (u + 0.03, 0.065), (u - 0.03, 0.065)], (0.18, 0.19, 0.22))
            S.glow(u, 0.14, 0.60, (1.0, 0.92, 0.75), 0.65 if dk else 0.32)
            S.ellipse(u, 0.122, 0.05, 0.012, (1.0, 0.96, 0.85), lift=0)
        S.glow(1.05, 0.40, 0.9, P.accent, 0.12 if dk else 0.05)
        S.floor(0.62, conc, scale(conc, 0.66))
        S.rect(1.0, 0.625, 14.0, 0.02, scale(conc, 0.5), lift=0.0)
        S.soft(1.15, 0.86, 1.2, 0.20, P.light, 0.40 if dk else 0.22, 1.4, add=True)
        S.soft(0.55, 0.95, 0.3, 0.12, BLACK, 0.35, 1.5)                               # oil stain
    for k in range(-9, 11):                                                            # floor slab seams in perspective
        _shair(S, 1.1 + k * 0.10, 0.63, 1.1 + k * 0.62, 1.6, scale(conc, 0.55), 0.55)
    for vv in (0.70, 0.80, 0.96, 1.20):
        _shair(S, -2, vv, 4, vv, scale(conc, 0.55), 0.5)
    # hazard stripe marking the work bay
    for k in range(14):
        u = 0.55 + k * 0.095
        _spoly(S, [(u, 1.10), (u + 0.05, 1.10), (u + 0.025, 1.14), (u - 0.025, 1.14)], (0.95, 0.75, 0.10) if k % 2 == 0 else (0.10, 0.10, 0.12), None, 0.9)
    # the hero bike on a steel lift ramp, tool cart behind it, spanners and a tyre in front
    S.put("biz_toolcart", 0.78, 1.00, 0.30, color=mix(P.accent, (0.7, 0.12, 0.12), 0.4) if dk else (0.78, 0.14, 0.12), shadow_w=0.5, shadow_alpha=0.4)
    S.rect(1.20, 1.0, 1.05, 0.030, (0.48, 0.50, 0.55) if not dk else (0.30, 0.31, 0.34), lift=0.1)
    S.rect(1.20, 1.026, 1.05, 0.026, (0.95, 0.75, 0.10), lift=0.0)
    S.soft(1.20, 1.03, 0.55, 0.05, BLACK, 0.42, 1.4)
    S.soft(1.20, 0.96, 0.7, 0.14, (1.0, 0.9, 0.72), 0.30 if dk else 0.10, 1.4, add=True)
    S.put("biz_motorcycle", 1.20, 0.995, 0.50, color=P.accent if not dk else mix(P.accent, WHITE, 0.05), subject=True, shadow_w=0.8, shadow_alpha=0.35)
    S.put("biz_tyre", 1.55, 1.07, 0.22, shadow_w=0.25, shadow_alpha=0.4)
    S.put("biz_spanners", 1.02, 1.13, 0.070, shadow=False)
    S.put("biz_oil_can", 0.43, 1.12, 0.10, color=(0.95, 0.65, 0.12), shadow_w=0.1, framed=False)
    S.focus("detail", 1.25, 0.82)
    with S.near(blur=16):
        S.soft(0.25, 1.05, 0.3, 0.10, P.accent_light, 0.22, 1.2, add=True)
        S.circle(1.92, 0.20, 0.06, (1.0, 0.9, 0.7), alpha=0.22, lift=0, soft=6.0)


# ====================================================================================== mobile phone repair
def _wallpaper(c, x0, y0, x1, y1, acc, dark=False):
    """Phone / tablet screen content: a gradient with soft shapes, no text."""
    top, bot = mix(acc, WHITE, 0.45), scale(acc, 0.42)
    _rr(c, x0, y0, x1, y1, top, bot, 0.03)
    w, h = x1 - x0, y1 - y0
    soft_disc(c, x0 + w * 0.7, y0 + h * 0.72, w * 0.5, h * 0.18, mix(acc, WHITE, 0.8), 0.55, 1.3, 0)
    soft_disc(c, x0 + w * 0.25, y0 + h * 0.3, w * 0.55, h * 0.14, scale(acc, 0.3), 0.45, 1.3, 20)


@sprop("biz_phone_cracked", aspect=0.56, fill=1.0)
def biz_phone_cracked(c, color):
    acc = color or (0.95, 0.45, 0.12)
    rng = random.Random(7)
    ao(c, 0.0, 0.0, 0.60, 0.09, 0.55)
    _rr(c, -0.20, 0.0, 0.20, 0.07, (0.18, 0.18, 0.21), (0.08, 0.08, 0.09), 0.02)          # little stand
    _poly(c, [(0.265, 0.09), (0.295, 0.10), (0.295, 0.97), (0.265, 0.99)], (0.55, 0.57, 0.62), (0.28, 0.29, 0.33))   # thickness edge
    _rr(c, -0.27, 0.07, 0.27, 1.0, (0.28, 0.29, 0.33), (0.07, 0.07, 0.09), 0.07)
    _rr(c, -0.252, 0.09, 0.252, 0.982, (0.03, 0.03, 0.04), (0.02, 0.02, 0.03), 0.055)
    _wallpaper(c, -0.238, 0.10, 0.238, 0.97, acc)
    # dead patch of the display (black, bleeding in from the bottom left) where the glass took the hit
    _poly(c, [(-0.238, 0.10), (-0.02, 0.10), (-0.07, 0.24), (-0.14, 0.34), (-0.238, 0.40)], (0.02, 0.02, 0.03), (0.04, 0.04, 0.05), 0.93)
    c.ellipse(0.0, 0.945, 0.016, 0.016, (0.02, 0.02, 0.03), lift=0)
    cu, cv_ = 0.04, 0.50
    rays = []
    for k in range(11):
        a = math.radians(k * 32.7 + rng.uniform(-8, 8))
        pts = [(cu, cv_)]
        ang, d = a, 0.0
        for _ in range(4):
            d += rng.uniform(0.07, 0.13)
            ang += rng.uniform(-0.18, 0.18)
            pts.append((cu + d * math.cos(ang), cv_ + d * math.sin(ang) * 1.0))
        rays.append(pts)
        for p, q in zip(pts, pts[1:]):
            if abs(q[0]) < 0.24 and 0.10 < q[1] < 0.97:
                c.line(p[0], p[1], q[0], q[1], 0.0075, (1.0, 1.0, 1.0), 0.85)
                c.line(p[0] + 0.004, p[1] - 0.004, q[0] + 0.004, q[1] - 0.004, 0.003, (0.0, 0.0, 0.0), 0.6)
    for ring in (1, 2, 3):                                           # web rings between neighbouring rays
        for k in range(11):
            p, q = rays[k][ring], rays[(k + 1) % 11][ring]
            if abs(p[0]) < 0.24 and abs(q[0]) < 0.24 and 0.10 < p[1] < 0.97 and 0.10 < q[1] < 0.97:
                c.line(p[0], p[1], q[0], q[1], 0.0042, (1.0, 1.0, 1.0), 0.55)
    c.glow(cu, cv_, 0.10, WHITE, 0.45)
    _poly(c, [(-0.22, 0.95), (-0.10, 0.95), (0.14, 0.12), (0.03, 0.12)], WHITE, None, 0.07)       # glass sheen
    _rr(c, 0.275, 0.62, 0.30, 0.76, mix(acc, WHITE, 0.2), scale(acc, 0.6), 0.01)              # power key


@sprop("biz_phone_open", aspect=2.55, fill=0.42)
def biz_phone_open(c, color):
    acc = color or (0.95, 0.45, 0.12)
    ao(c, 0.0, 0.0, 1.05, 0.20, 0.5)
    K0, K1 = 0.04, 0.40
    _poly(c, _rrpts(-0.50, 0.0, 0.50, K1 - 0.03, 0.05), (0.14, 0.14, 0.16), (0.06, 0.06, 0.07))                 # thickness
    _poly(c, _rrpts(-0.50, K0, 0.50, K1, 0.05), (0.62, 0.64, 0.69), (0.34, 0.35, 0.40))                          # metal frame
    _poly(c, _rrpts(-0.47, K0 + 0.02, 0.47, K1 - 0.02, 0.04), (0.07, 0.07, 0.09), (0.04, 0.04, 0.05))
    _poly(c, _rrpts(-0.42, 0.075, 0.03, 0.355, 0.015), (0.78, 0.80, 0.84), (0.50, 0.52, 0.57))                   # battery
    _poly(c, [(-0.40, 0.255), (0.02, 0.255), (0.02, 0.265), (-0.40, 0.265)], BLACK, None, 0.30)
    _poly(c, [(-0.30, 0.34), (-0.18, 0.34), (-0.18, 0.355), (-0.30, 0.355)], mix(acc, WHITE, 0.2), scale(acc, 0.7))
    _poly(c, _rrpts(0.08, 0.07, 0.44, 0.36, 0.015), (0.10, 0.52, 0.34), (0.05, 0.30, 0.20))                       # circuit board
    for (x0, y0, x1, y1, col) in ((0.12, 0.10, 0.22, 0.20, (0.70, 0.72, 0.76)), (0.25, 0.12, 0.33, 0.20, (0.82, 0.68, 0.30)), (0.12, 0.24, 0.20, 0.32, (0.78, 0.80, 0.84)),
                                  (0.35, 0.10, 0.42, 0.17, (0.12, 0.12, 0.14)), (0.24, 0.25, 0.34, 0.33, (0.70, 0.72, 0.76))):
        _rr(c, x0, y0, x1, y1, mix(col, WHITE, 0.15), scale(col, 0.7), 0.005)
    c.ellipse(0.38, 0.29, 0.045, 0.035, (0.12, 0.12, 0.14), lift=0.1)                                             # camera module
    c.ellipse(0.38, 0.29, 0.022, 0.016, (0.15, 0.20, 0.35), lift=0.3)
    c.line(0.03, 0.15, 0.10, 0.17, 0.016, (0.95, 0.60, 0.20), 0.95)                                               # flex cable
    for (x, y) in ((-0.44, 0.09), (0.46, 0.09), (-0.44, 0.34), (0.46, 0.35), (0.05, 0.09), (0.05, 0.345)):       # screws
        c.ellipse(x, y, 0.012, 0.008, (0.78, 0.80, 0.84), lift=0.2)
    _poly(c, [(-0.46, 0.06), (-0.14, 0.05), (-0.10, 0.10), (-0.44, 0.095)], WHITE, None, 0.07)


@sprop("biz_screwdriver", aspect=11.0, fill=0.14)
def biz_screwdriver(c, color):
    acc = color or (0.95, 0.45, 0.12)
    ao(c, 0.0, 0.0, 1.5, 0.30, 0.45)
    c.line(-0.80, 0.075, -0.26, 0.085, 0.100, scale(acc, 0.6), 1.0)
    c.line(-0.80, 0.085, -0.26, 0.095, 0.078, mix(acc, WHITE, 0.12), 1.0)
    for k in range(7):
        c.line(-0.74 + k * 0.075, 0.12, -0.74 + k * 0.075, 0.04, 0.014, scale(acc, 0.55), 0.55)
    c.line(-0.80, 0.113, -0.30, 0.121, 0.014, WHITE, 0.35)
    c.line(-0.26, 0.09, -0.12, 0.092, 0.060, scale(STEEL, 0.75), 1.0)
    c.line(-0.12, 0.092, 0.78, 0.100, 0.024, mix(STEEL, WHITE, 0.2), 1.0)
    c.line(-0.10, 0.100, 0.70, 0.107, 0.007, WHITE, 0.6)


@sprop("biz_solder_iron", aspect=2.7, fill=0.55)
def biz_solder_iron(c, color):
    acc = color or (0.95, 0.45, 0.12)
    ao(c, -0.10, 0.0, 0.85, 0.12, 0.5)
    _oval(c, -0.28, 0.035, 0.30, 0.07, (0.26, 0.27, 0.30), (0.10, 0.10, 0.12))
    _oval(c, -0.28, 0.05, 0.26, 0.052, (0.34, 0.35, 0.38), (0.18, 0.18, 0.21))
    c.line(-0.28, 0.06, -0.28, 0.34, 0.034, scale(STEEL, 0.6), 1.0)
    for k in range(7):                                                             # spring cradle
        c.line(-0.34, 0.14 + k * 0.040, -0.22, 0.155 + k * 0.040, 0.010, mix(STEEL, WHITE, 0.2), 1.0)
    c.line(0.62, 0.15, 0.10, 0.33, 0.085, scale(acc, 0.55), 1.0)                  # insulated grip, ridged
    c.line(0.62, 0.162, 0.12, 0.341, 0.060, mix(acc, WHITE, 0.1), 1.0)
    c.line(0.10, 0.33, -0.02, 0.37, 0.055, scale(STEEL, 0.8), 1.0)
    c.line(-0.02, 0.37, -0.20, 0.435, 0.020, (0.82, 0.62, 0.40), 1.0)
    c.glow(-0.20, 0.435, 0.20, (1.0, 0.55, 0.15), 0.8)
    c.line(0.62, 0.15, 0.80, 0.10, 0.020, (0.10, 0.10, 0.11), 1.0)
    craft.steam(c, -0.22, 0.46, 0.26, 0.025, 1, 0.28)


@sprop("biz_lamp_loupe", aspect=0.92, fill=1.0)
def biz_lamp_loupe(c, color):
    ao(c, -0.10, 0.0, 0.5, 0.07, 0.5)
    _oval(c, -0.10, 0.03, 0.22, 0.05, (0.30, 0.31, 0.34), (0.08, 0.08, 0.10))
    c.line(-0.10, 0.04, -0.14, 0.44, 0.034, scale(STEEL, 0.55), 1.0)
    c.line(-0.14, 0.44, 0.20, 0.80, 0.030, scale(STEEL, 0.55), 1.0)
    c.line(-0.145, 0.45, 0.19, 0.81, 0.008, WHITE, 0.4)
    for (u, v) in ((-0.14, 0.44), (0.20, 0.80)):
        c.ellipse(u, v, 0.04, 0.04, (0.20, 0.21, 0.24), lift=0.2)
    c.glow(0.40, 0.70, 0.55, (1.0, 0.96, 0.85), 0.65)
    _oval(c, 0.40, 0.70, 0.22, 0.22, (0.16, 0.17, 0.20), (0.05, 0.05, 0.07))
    _oval(c, 0.40, 0.70, 0.19, 0.19, (0.90, 0.95, 1.0), (0.62, 0.72, 0.85), 0.9)
    for k in range(16):                                                              # ring of LEDs
        a = math.radians(k * 22.5)
        c.ellipse(0.40 + 0.20 * math.cos(a), 0.70 + 0.20 * math.sin(a), 0.009, 0.009, (1.0, 0.99, 0.9), lift=0)
    soft_disc(c, 0.34, 0.76, 0.12, 0.05, WHITE, 0.55, 1.1, 40, True)
    craft.arc(c, 0.40, 0.70, 0.15, 0.15, 200, 250, 0.014, WHITE, 0.55, steps=5)


@sprop("biz_screw_mat", aspect=3.5, fill=0.30)
def biz_screw_mat(c, color):
    acc = color or (0.95, 0.45, 0.12)
    rng = random.Random(11)
    ao(c, 0.0, 0.0, 1.1, 0.16, 0.45)
    _poly(c, _rrpts(-0.52, 0.0, 0.52, 0.30, 0.04), (0.24, 0.25, 0.28), (0.10, 0.10, 0.12))
    _poly(c, _rrpts(-0.50, 0.03, 0.50, 0.30, 0.04), mix((0.52, 0.55, 0.60), acc, 0.12), (0.30, 0.32, 0.36))
    for k in range(4):                                                              # compartments
        x = -0.50 + k * 0.25
        _poly(c, [(x + 0.01, 0.05), (x + 0.24, 0.05), (x + 0.24, 0.28), (x + 0.01, 0.28)], (0.10, 0.10, 0.12), (0.18, 0.18, 0.21), 0.78)
    for k, col in enumerate(((0.80, 0.82, 0.86), (0.88, 0.72, 0.30), (0.62, 0.64, 0.68), (0.20, 0.20, 0.23))):          # screw piles
        x0 = -0.50 + k * 0.25
        for _ in range(9):
            c.ellipse(x0 + rng.uniform(0.04, 0.21), rng.uniform(0.08, 0.24), 0.011, 0.008, col, lift=0.2)
    _rr(c, -0.42, 0.18, -0.30, 0.27, (0.78, 0.80, 0.84), (0.50, 0.52, 0.57), 0.01)            # a loose battery cell
    _rr(c, 0.15, 0.17, 0.33, 0.24, mix(acc, WHITE, 0.1), scale(acc, 0.6), 0.01)               # replacement flex
    _poly(c, [(-0.50, 0.03), (0.50, 0.03), (0.50, 0.06), (-0.50, 0.06)], WHITE, None, 0.12)


@sprop("biz_tablet", aspect=0.78, fill=1.0)
def biz_tablet(c, color):
    acc = color or (0.95, 0.45, 0.12)
    ao(c, 0.0, 0.0, 0.7, 0.10, 0.5)
    c.line(0.20, 0.08, 0.30, 0.0, 0.03, (0.10, 0.10, 0.12), 1.0)                       # kickstand legs behind
    c.line(-0.20, 0.08, -0.30, 0.0, 0.03, (0.10, 0.10, 0.12), 1.0)
    _poly(c, [(0.385, 0.07), (0.415, 0.09), (0.415, 0.97), (0.385, 0.98)], (0.60, 0.62, 0.67), (0.30, 0.31, 0.35))
    _rr(c, -0.39, 0.05, 0.39, 1.0, (0.62, 0.64, 0.69), (0.32, 0.33, 0.37), 0.045)
    _rr(c, -0.37, 0.07, 0.37, 0.98, (0.04, 0.04, 0.05), (0.03, 0.03, 0.04), 0.035)
    _wallpaper(c, -0.335, 0.11, 0.335, 0.94, mix(acc, (0.2, 0.45, 0.8), 0.45))
    cols = ((0.95, 0.35, 0.30), (0.30, 0.70, 0.95), (0.40, 0.85, 0.50), (0.98, 0.78, 0.20), (0.70, 0.45, 0.95), (0.95, 0.55, 0.15))
    for r in range(3):
        for k in range(4):
            _rr(c, -0.27 + k * 0.145, 0.71 - r * 0.15, -0.27 + k * 0.145 + 0.10, 0.71 - r * 0.15 + 0.10, mix(cols[(r * 4 + k) % 6], WHITE, 0.15),
                scale(cols[(r * 4 + k) % 6], 0.75), 0.025)
    _rr(c, -0.24, 0.13, 0.24, 0.20, WHITE, (0.85, 0.86, 0.9), 0.03, 0.55)
    _poly(c, [(-0.32, 0.93), (-0.12, 0.93), (0.12, 0.11), (-0.06, 0.11)], WHITE, None, 0.07)


def _drawers(S, u0, v0, u1, v1, base, acc, rng, cols=6, rows=7):
    """A small-parts cabinet: a grid of drawers with pulls and plain label bars."""
    S.rect((u0 + u1) / 2, (v0 + v1) / 2, u1 - u0, v1 - v0, base, r=0.006, lift=0.06)
    dw, dh = (u1 - u0) / cols, (v1 - v0) / rows
    for r in range(rows):
        for k in range(cols):
            x, y = u0 + (k + 0.5) * dw, v0 + (r + 0.5) * dh
            S.rect(x, y, dw * 0.88, dh * 0.82, mix(base, WHITE, 0.10 + 0.04 * ((r + k) % 3)), r=0.002, lift=0.10)
            S.rect(x, y - dh * 0.12, dw * 0.34, dh * 0.10, scale(base, 0.45), lift=0.0)
            if (r * 3 + k) % 4 == 0:
                S.rect(x, y + dh * 0.15, dw * 0.42, dh * 0.10, acc, lift=0.0, alpha=0.9)


@niche("mobile-repair", "Mobile phone repair shop", subjects=("biz_phone_cracked",),
       strong=("mobile repair", "mobile phone repair", "phone repair", "phone repair shop", "mobile repair shop", "mobile repairing", "smartphone repair",
               "screen replacement", "cracked screen repair", "phone screen repair", "mobile service centre", "mobile service center", "tablet repair",
               "mobile repairing shop", "फोन रिपेयर", "मोबाइल रिपेयर", "मोबाइल रिपेयरिंग", "मोबाइल मरम्मत", "फोन की मरम्मत", "मोबाइल रिपेयर शॉप", "मोबाइल सर्विस सेंटर",
               "phone ki repairing", "mobile ki repairing", "mobile repair wala", "टूटी स्क्रीन"),
       weak=("repair", "repairing", "screen", "battery replacement", "charging port", "water damage", "technician", "display", "tempered", "रिपेयर", "मरम्मत", "स्क्रीन"),
       accent="#ff6a1a", mood="dark", group="trades",
       avoid=("mobile store", "mobile shop", "mobile showroom", "mobile accessories", "electronics store", "phone store", "mobile app", "app development", "mobile recharge",
              "tv repair", "ac repair", "laptop store", "मोबाइल की दुकान", "मोबाइल शोरूम", "मोबाइल ऐप"))
def mobile_repair(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(53)
    wall_c = mix(P.wall_top, (0.30, 0.32, 0.36), 0.45) if dk else mix(P.wall_top, (0.82, 0.85, 0.90), 0.5)
    bench = mix(P.floor_top, (0.20, 0.17, 0.15), 0.4) if dk else mix((0.70, 0.55, 0.40), P.wall_bot, 0.15)
    mat = (0.09, 0.27, 0.25) if dk else (0.20, 0.50, 0.46)
    with S.far():
        S.wall(wall_c, scale(wall_c, 0.80), 0.66)
        S.rect(0.42, 0.14, 0.78, 0.014, scale(P.accent, 1.0 if dk else 0.9), lift=0.0)                 # accent light strip with glow
        S.glow(0.42, 0.15, 0.7, P.accent, 0.35 if dk else 0.12)
        # parts cabinet (left) and shelves of phones (right) on the wall
        _drawers(S, 0.02, 0.22, 0.62, 0.58, scale(wall_c, 0.55) if dk else mix(wall_c, (0.5, 0.52, 0.56), 0.4), P.accent, rng)
        for r_, v in enumerate((0.26, 0.46)):
            S.rect(1.40, v + 0.055, 1.10, 0.012, scale(wall_c, 0.45), lift=0.0)
            for k in range(11):
                col = mix((0.25, 0.45, 0.85), P.accent, (k % 4) / 3.0)
                S.rect(0.90 + k * 0.095, v, 0.045, 0.095 if r_ == 0 else 0.085, (0.08, 0.08, 0.10), r=0.006, lift=0.04)
                S.rect(0.90 + k * 0.095, v, 0.036, 0.080 if r_ == 0 else 0.07, mix(col, WHITE, 0.2 if not dk else 0.0), r=0.004, lift=0.12, alpha=0.92)
        S.glow(1.40, 0.36, 0.9, P.accent_light, 0.10 if dk else 0.05)
        S.floor(0.70, bench, scale(bench, 0.62))                                                         # bench top
        S.rect(1.0, 0.705, 14.0, 0.02, scale(bench, 1.25), lift=0.0)
        S.soft(1.1, 0.85, 1.3, 0.22, P.light, 0.36 if dk else 0.20, 1.4, add=True)
    # anti-static mat on the bench in perspective with a faint grid and a highlight edge
    _spoly(S, [(0.30, 0.80), (2.05, 0.80), (2.30, 1.30), (0.05, 1.30)], mat, scale(mat, 0.75), 1.0)
    for k in range(11):
        u = 0.30 + k * 0.175
        _shair(S, u, 0.80, u + (u - 1.17) * 0.14, 1.30, scale(mat, 1.5), 0.35)
    for vv in (0.86, 0.95, 1.06, 1.18):
        _shair(S, 0.30 - (vv - 0.8) * 0.5, vv, 2.05 + (vv - 0.8) * 0.5, vv, scale(mat, 1.5), 0.30)
    S.rect(1.17, 0.80, 1.75, 0.012, mix(mat, WHITE, 0.4), lift=0.0, alpha=0.6)
    S.soft(1.15, 0.98, 0.8, 0.20, mix(P.accent_light, WHITE, 0.3), 0.28 if dk else 0.12, 1.4, add=True)
    # props: loupe lamp and tablet behind, the cracked phone in front, open phone, screwdriver, soldering iron
    S.put("biz_lamp_loupe", 0.86, 0.96, 0.46, shadow_w=0.3, shadow_alpha=0.4)
    S.put("biz_tablet", 1.30, 0.96, 0.38, color=P.accent, shadow_w=0.3, shadow_alpha=0.4)
    S.put("biz_phone_cracked", 1.05, 1.05, 0.52, color=P.accent, subject=True, shadow_w=0.3, shadow_alpha=0.45)
    S.put("biz_phone_open", 1.40, 1.14, 0.17, color=P.accent, shadow=False)
    S.put("biz_solder_iron", 1.52, 0.99, 0.17, color=P.accent, shadow=False)
    S.put("biz_screwdriver", 1.00, 1.19, 0.045, color=P.accent, shadow=False)
    S.put("biz_screw_mat", 0.62, 1.17, 0.12, color=P.accent, shadow=False, framed=False)
    S.focus("detail", 1.18, 1.06)
    with S.near(blur=16):
        S.soft(0.22, 1.0, 0.3, 0.10, P.accent_light, 0.18, 1.2, add=True)
        S.circle(1.95, 1.08, 0.07, mix(P.accent, WHITE, 0.2) if not dk else scale(P.accent, 0.5), alpha=0.7, lift=0.1)


# ====================================================================================== gift shop
PASTEL = ((0.96, 0.80, 0.80), (0.80, 0.90, 0.88), (0.98, 0.90, 0.70), (0.80, 0.82, 0.95), (0.93, 0.84, 0.75), (0.90, 0.78, 0.90))
KRAFT = (0.80, 0.62, 0.42)


def _rib(P_or_col):
    """Ribbon colour from an accent that may be nearly black: keep it readable (gold-tinted)."""
    col = P_or_col
    lum = 0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]
    return mix(col, GOLD, 0.45) if lum < 0.16 else col


def _bow(c, u, v, s, col):
    """A ribbon bow: two loops, a knot and two tails; (u, v) is the knot, s the loop size."""
    for sgn in (-1, 1):
        _poly(c, [(u + sgn * s * 0.12, v - s * 0.02), (u + sgn * s * 0.55, v - s * 0.55), (u + sgn * s * 0.78, v - s * 0.50), (u + sgn * s * 0.30, v + s * 0.02)],
              mix(col, WHITE, 0.08), scale(col, 0.62))
    for sgn in (-1, 1):
        c.ellipse(u + sgn * s * 0.52, v + s * 0.22, s * 0.52, s * 0.28, col, angle=sgn * -24, lift=0.18)
        c.ellipse(u + sgn * s * 0.52, v + s * 0.22, s * 0.28, s * 0.13, scale(col, 0.55), angle=sgn * -24, lift=0.0, alpha=0.85)
    c.ellipse(u, v + s * 0.06, s * 0.17, s * 0.15, mix(col, WHITE, 0.1), lift=0.25)
    soft_disc(c, u - s * 0.3, v + s * 0.34, s * 0.22, s * 0.07, WHITE, 0.45, 1.2, 20, True)


def _gbox(c, u, v, w, h, d, col, rib, kind="cross"):
    """A lidded gift box (3/4 view) with a ribbon band over the lid and down the front."""
    _box3(c, u, v, w, h, d, col, top=mix(col, WHITE, 0.30), right=scale(col, 0.70), r=0.006)
    dx, dy = d * 0.34, d * 0.30
    x0, x1 = u - w / 2, u + w / 2
    _rr(c, x0 - 0.008, v + h * 0.78, x1 + 0.008, v + h, mix(col, WHITE, 0.10), scale(col, 0.90), 0.006)           # lid
    c.line(x0 - 0.008, v + h * 0.78, x1 + 0.008, v + h * 0.78, 0.004, scale(col, 0.55), 0.7)
    bw = max(0.03, w * 0.13)
    _rr(c, u - bw / 2, v, u + bw / 2, v + h, mix(rib, WHITE, 0.10), scale(rib, 0.78), 0.0)
    _poly(c, [(u - bw / 2, v + h), (u + bw / 2, v + h), (u + bw / 2 + dx, v + h + dy), (u - bw / 2 + dx, v + h + dy)], mix(rib, WHITE, 0.2), scale(rib, 0.86))
    if kind == "cross":
        _poly(c, [(x1, v + h * 0.52), (x1 + dx, v + h * 0.52 + dy), (x1 + dx, v + h * 0.52 + dy + bw * 0.8), (x1, v + h * 0.52 + bw * 0.8)], scale(rib, 0.62), None)
    return dx, dy


@sprop("biz_gift_stack", aspect=0.78, fill=1.0)
def biz_gift_stack(c, color):
    acc = _rib(color or (0.55, 0.12, 0.25))
    ao(c, 0.04, 0.0, 0.92, 0.17, 0.5)
    _gbox(c, -0.02, 0.0, 0.62, 0.34, 0.46, (0.97, 0.93, 0.86), acc)
    _gbox(c, 0.0, 0.34, 0.46, 0.25, 0.34, KRAFT, (0.97, 0.95, 0.9))
    _gbox(c, 0.01, 0.59, 0.32, 0.19, 0.24, mix((0.95, 0.80, 0.80), acc, 0.12), GOLD)
    _bow(c, 0.035, 0.80, 0.17, GOLD)
    # tag on a string hanging over the lower box (plain card, no writing)
    c.line(0.20, 0.30, 0.24, 0.19, 0.004, scale(acc, 0.7), 0.9)
    _poly(c, [(0.20, 0.19), (0.29, 0.17), (0.30, 0.09), (0.21, 0.11)], mix(CREAM, WHITE, 0.3), scale(CREAM, 0.82))
    c.line(0.215, 0.14, 0.28, 0.125, 0.006, (0.6, 0.55, 0.5), 0.6)
    c.ellipse(0.215, 0.175, 0.008, 0.008, (0.35, 0.3, 0.28), lift=0)


@sprop("biz_hamper", aspect=1.05, fill=1.0)
def biz_hamper(c, color):
    acc = _rib(color or (0.55, 0.12, 0.25))
    rng = random.Random(5)
    ao(c, 0.0, 0.0, 0.95, 0.15, 0.5)
    wick = (0.78, 0.58, 0.34)
    # items poking out: bottle, chocolate box, candle jar, dry-fruit pouch, a sprig of dried flowers
    _hfill(c, -0.23, 0.38, -0.12, 0.88, _cyl_fn((0.55, 0.20, 0.25), (0.16, 0.05, 0.08), 0.35), strips=5)
    _hfill(c, -0.20, 0.88, -0.15, 1.00, _cyl_fn((0.55, 0.20, 0.25), (0.16, 0.05, 0.08), 0.35), strips=3)
    _rr(c, -0.215, 0.55, -0.135, 0.70, (0.97, 0.93, 0.84), (0.85, 0.80, 0.72), 0.01)
    _box3(c, 0.13, 0.40, 0.30, 0.34, 0.2, (0.46, 0.26, 0.16), r=0.01)
    _rr(c, 0.115, 0.40, 0.145, 0.74, GOLD, scale(GOLD, 0.7), 0.0)
    _hfill(c, -0.07, 0.40, 0.07, 0.62, _cyl_fn((0.97, 0.94, 0.88), (0.74, 0.68, 0.60), 0.3), strips=5)
    c.ellipse(0.0, 0.62, 0.07, 0.025, (0.98, 0.90, 0.6), lift=0)
    c.glow(0.0, 0.63, 0.10, (1.0, 0.85, 0.5), 0.3)
    _poly(c, [(0.26, 0.45), (0.46, 0.45), (0.50, 0.70), (0.42, 0.78), (0.30, 0.78), (0.22, 0.70)], (0.92, 0.78, 0.55), (0.70, 0.52, 0.30))
    _rr(c, 0.29, 0.52, 0.43, 0.62, mix(acc, WHITE, 0.3), acc, 0.01)
    for k in range(7):                                                                           # dried flower sprigs
        a = math.radians(70 + k * 6)
        c.line(-0.02 + k * 0.012, 0.55, -0.02 + k * 0.05 + math.cos(a) * 0.1, 0.95 + (k % 3) * 0.015, 0.006, (0.55, 0.45, 0.25), 0.9)
    for k in range(7):
        c.ellipse(-0.02 + k * 0.05 + 0.04, 0.95 + (k % 3) * 0.015, 0.022, 0.018, mix((0.96, 0.78, 0.62), acc, 0.08 * (k % 3)), lift=0.15)
    # basket: tapered woven body with horizontal bands and a rim
    _poly(c, [(-0.50, 0.40), (0.50, 0.40), (0.42, 0.04), (-0.42, 0.04)], mix(wick, WHITE, 0.14), scale(wick, 0.62))
    for k in range(7):
        v = 0.07 + k * 0.047
        c.line(-0.46 + k * 0.012, v, 0.46 - k * 0.012, v, 0.012, scale(wick, 0.50), 0.45)
    for k in range(18):
        u = -0.46 + k * 0.054
        c.line(u, 0.38, u * 0.85, 0.05, 0.006, scale(wick, 0.74), 0.40)
    _rr(c, -0.53, 0.38, 0.53, 0.44, mix(wick, WHITE, 0.2), scale(wick, 0.72), 0.02)
    # cellophane sheen over the contents, handle arch and bow
    _poly(c, [(-0.48, 0.45), (0.48, 0.45), (0.40, 0.92), (-0.34, 0.95)], WHITE, None, 0.10, 0.04)
    _poly(c, [(-0.46, 0.46), (-0.38, 0.46), (-0.28, 0.93), (-0.33, 0.93)], WHITE, None, 0.22, 0.05)
    craft.arc(c, 0.0, 0.44, 0.50, 0.50, 20, 160, 0.035, mix(wick, WHITE, 0.1), 1.0, steps=14)
    craft.arc(c, 0.0, 0.44, 0.50, 0.50, 40, 150, 0.010, WHITE, 0.4, steps=10)
    _bow(c, 0.0, 0.40, 0.17, acc)
    c.line(0.0, 0.36, -0.06, 0.18, 0.02, acc, 0.9)
    c.line(0.0, 0.36, 0.07, 0.17, 0.02, acc, 0.9)


@sprop("biz_photo_mug", aspect=1.25, fill=0.62)
def biz_photo_mug(c, color):
    acc = color or (0.55, 0.12, 0.25)
    ao(c, 0.02, 0.0, 0.62, 0.10, 0.5)
    c.ring(0.31, 0.30, 0.15, 0.055, (0.92, 0.92, 0.94), 1.0)                                          # handle
    c.ring(0.31, 0.30, 0.15, 0.012, (0.62, 0.62, 0.68), 0.4)
    _hfill(c, -0.28, 0.0, 0.28, 0.56, _cyl_fn((1.0, 1.0, 1.0), (0.66, 0.68, 0.74), 0.30))
    c.ellipse(0.0, 0.0, 0.28, 0.07, (0.72, 0.74, 0.80), lift=0)
    _hfill(c, -0.28, 0.0, 0.28, 0.56, _cyl_fn((1.0, 1.0, 1.0), (0.66, 0.68, 0.74), 0.30))
    c.ellipse(0.0, 0.56, 0.28, 0.07, (0.80, 0.82, 0.86), lift=0)
    c.ellipse(0.0, 0.56, 0.245, 0.055, (0.26, 0.14, 0.09), lift=0.1)
    # the printed photo panel: sky, sun, hills and a heart
    x0, x1, y0, y1 = -0.16, 0.16, 0.14, 0.44
    _rr(c, x0 - 0.012, y0 - 0.012, x1 + 0.012, y1 + 0.012, (1.0, 1.0, 1.0), (0.9, 0.9, 0.92), 0.02)
    _rr(c, x0, y0, x1, y1, mix(acc, (0.7, 0.85, 1.0), 0.55), mix(acc, (1.0, 0.9, 0.8), 0.7), 0.012)
    c.ellipse(0.07, 0.35, 0.036, 0.036, (1.0, 0.88, 0.4), lift=0.1)
    _poly(c, [(x0, y0), (x1, y0), (x1, 0.24), (0.06, 0.30), (-0.04, 0.22), (x0, 0.28)], (0.30, 0.55, 0.35), (0.18, 0.38, 0.24))
    _poly(c, [(x0, y0), (x1, y0), (x1, 0.19), (0.02, 0.24), (x0, 0.20)], (0.22, 0.45, 0.30), (0.12, 0.30, 0.20))
    c.ellipse(-0.06, 0.34, 0.016, 0.014, (0.95, 0.35, 0.40), lift=0.1)
    c.ellipse(-0.035, 0.34, 0.016, 0.014, (0.95, 0.35, 0.40), lift=0.1)
    _poly(c, [(-0.077, 0.335), (-0.019, 0.335), (-0.048, 0.30)], (0.95, 0.35, 0.40), None)
    _poly(c, [(-0.27, 0.54), (-0.22, 0.54), (-0.22, 0.05), (-0.27, 0.05)], WHITE, None, 0.30)


@sprop("biz_cushion", aspect=1.15, fill=0.80)
def biz_cushion(c, color):
    col = color or (0.90, 0.72, 0.72)
    ao(c, 0.0, 0.0, 1.0, 0.14, 0.45)
    pts = []
    for k in range(40):                                                                 # pillow outline: pinched corners, soft bulge on each edge
        a = math.radians(k * 9)
        sq = 1.0 / (abs(math.cos(a)) ** 3 + abs(math.sin(a)) ** 3) ** (1 / 3.0)
        pts.append((0.46 * sq * math.cos(a), 0.40 + 0.37 * sq * math.sin(a) * 0.96))
    _poly(c, pts, mix(col, WHITE, 0.18), scale(col, 0.72))
    _poly(c, [(-0.42, 0.52), (-0.28, 0.72), (0.0, 0.76), (0.28, 0.72), (0.42, 0.52)], WHITE, None, 0.16, 0.0)       # soft highlight on top edge
    for sgn in (-1, 1):                                                                   # corner creases
        soft_disc(c, sgn * 0.42, 0.40, 0.05, 0.16, BLACK, 0.14, 1.2, 0)
    # hand-stitched name panel: a wide embroidery band built from plain stitches and a heart (no letters)
    _rr(c, -0.32, 0.22, 0.32, 0.38, mix(col, WHITE, 0.55), mix(col, WHITE, 0.35), 0.03)
    for k in range(7):
        c.line(-0.26 + k * 0.075, 0.30, -0.22 + k * 0.075, 0.32 if k % 2 == 0 else 0.28, 0.012, scale(col, 0.45), 0.9)
    c.ellipse(-0.025, 0.55, 0.026, 0.024, (0.85, 0.2, 0.3), lift=0.1)
    c.ellipse(0.025, 0.55, 0.026, 0.024, (0.85, 0.2, 0.3), lift=0.1)
    _poly(c, [(-0.048, 0.545), (0.048, 0.545), (0.0, 0.495)], (0.85, 0.2, 0.3), None)
    c.glow(0.0, 0.40, 0.6, WHITE, 0.08)


def _bag(c, u, v, w, h, col, tissue, rope):
    _poly(c, [(u - w / 2, v), (u + w / 2, v), (u + w / 2, v + h), (u - w / 2, v + h)], mix(col, WHITE, 0.14), scale(col, 0.80))
    _poly(c, [(u + w / 2, v), (u + w / 2 + w * 0.16, v + h * 0.04), (u + w / 2 + w * 0.16, v + h * 1.0), (u + w / 2, v + h)], scale(col, 0.62), scale(col, 0.50))
    _poly(c, [(u - w / 2, v + h * 0.78), (u + w / 2, v + h * 0.78), (u + w / 2, v + h), (u - w / 2, v + h)], mix(col, WHITE, 0.2), scale(col, 0.92))
    _poly(c, [(u - w * 0.42, v + h), (u - w * 0.30, v + h * 1.22), (u - w * 0.12, v + h * 1.10), (u, v + h * 1.28), (u + w * 0.14, v + h * 1.12),
              (u + w * 0.32, v + h * 1.24), (u + w * 0.42, v + h)], tissue, scale(tissue, 0.82))
    for k in (-1, 1):
        craft.arc(c, u + k * w * 0.20, v + h, w * 0.16, h * 0.55, 0, 180, 0.012, rope, 1.0, steps=8)
    _poly(c, [(u - w * 0.22, v + h * 0.44), (u + w * 0.22, v + h * 0.44), (u + w * 0.22, v + h * 0.64), (u - w * 0.22, v + h * 0.64)], mix(col, WHITE, 0.6), mix(col, WHITE, 0.4))
    c.ellipse(u, v + h * 0.54, w * 0.07, w * 0.07, scale(col, 0.7), lift=0.1)
    _poly(c, [(u - w / 2 + 0.01, v + 0.01), (u - w / 2 + 0.05, v + 0.01), (u - w / 2 + 0.05, v + h * 0.75), (u - w / 2 + 0.01, v + h * 0.75)], WHITE, None, 0.22)


@sprop("biz_gift_bags", aspect=1.28, fill=0.78)
def biz_gift_bags(c, color):
    acc = _rib(color or (0.55, 0.12, 0.25))
    ao(c, 0.0, 0.0, 1.15, 0.15, 0.5)
    _bag(c, -0.36, 0.0, 0.34, 0.50, (0.96, 0.80, 0.82), (0.99, 0.95, 0.85), (0.9, 0.75, 0.5))
    _bag(c, 0.06, 0.0, 0.34, 0.58, mix((0.90, 0.88, 0.80), acc, 0.12), (0.80, 0.92, 0.90), acc)
    _bag(c, 0.46, 0.0, 0.30, 0.42, (0.80, 0.86, 0.96), (0.98, 0.88, 0.70), (0.9, 0.75, 0.5))


@sprop("biz_balloons", aspect=0.90, fill=1.0)
def biz_balloons(c, color):
    acc = color or (0.55, 0.12, 0.25)
    cols = ((0.96, 0.78, 0.80), (0.98, 0.88, 0.62), mix((0.85, 0.75, 0.95), acc, 0.1), (0.86, 0.94, 0.92))
    for (u, v, a, b, col, bu) in ((-0.20, 0.80, 0.19, 0.22, cols[0], 0.0), (0.12, 0.88, 0.18, 0.21, cols[1], 0.0), (0.02, 0.62, 0.17, 0.20, cols[2], 0.0)):
        c.line(u, v - b, 0.0, 0.0, 0.006, (0.6, 0.55, 0.5), 0.8)
    for (u, v, a, b, col) in ((-0.20, 0.80, 0.19, 0.22, cols[0]), (0.12, 0.88, 0.18, 0.21, cols[1]), (0.02, 0.62, 0.17, 0.20, cols[2])):
        c.ellipse(u, v, a, b, col, lift=0.22)
        _poly(c, [(u - 0.02, v - b), (u + 0.02, v - b), (u, v - b - 0.025)], scale(col, 0.78))
        soft_disc(c, u - a * 0.35, v + b * 0.35, a * 0.28, b * 0.20, WHITE, 0.55, 1.2, 30, True)
    # a foil heart balloon
    hp = []
    for k in range(32):
        t = k / 32.0 * 2 * math.pi
        hp.append((0.30 + 0.0105 * 16 * math.sin(t) ** 3 * 0.9, 0.62 + 0.0105 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * 0.9 + 0.15))
    c.line(0.30, 0.66, 0.0, 0.0, 0.006, (0.6, 0.55, 0.5), 0.8)
    _poly(c, hp, mix(GOLD, WHITE, 0.2), scale(GOLD, 0.72))
    soft_disc(c, 0.26, 0.86, 0.04, 0.025, WHITE, 0.6, 1.2, 40, True)
    c.ellipse(0.0, 0.015, 0.045, 0.02, (0.2, 0.2, 0.22), lift=0.1)


@sprop("biz_bouquet", aspect=0.80, fill=1.0)
def biz_bouquet(c, color):
    acc = color or (0.55, 0.12, 0.25)
    rng = random.Random(9)
    ao(c, 0.0, 0.0, 0.5, 0.07, 0.45)
    for k in range(5):
        a = math.radians(90 + (k - 2) * 12)
        c.line(0.0, 0.18, math.cos(a) * 0.5 * 0.7, 0.18 + math.sin(a) * 0.5, 0.012, (0.30, 0.50, 0.28), 1.0)
    for (u, v, ang) in ((-0.30, 0.66, 160), (0.30, 0.68, 20), (-0.16, 0.54, 120), (0.17, 0.55, 60)):
        craft.leaf(c, u * 0.55, v - 0.12, 0.30, ang, (0.28, 0.52, 0.30), 0.5)
    for (u, v, r, col) in ((-0.22, 0.78, 0.115, mix(acc, WHITE, 0.15)), (0.0, 0.88, 0.13, (0.97, 0.88, 0.70)), (0.22, 0.78, 0.115, mix((0.96, 0.78, 0.80), acc, 0.1)),
                           (-0.08, 0.72, 0.10, (0.98, 0.94, 0.90)), (0.12, 0.70, 0.10, mix(acc, WHITE, 0.45))):
        for k in range(6):
            a = math.radians(k * 60 + 10)
            c.ellipse(u + math.cos(a) * r * 0.55, v + math.sin(a) * r * 0.55, r * 0.55, r * 0.45, col, angle=math.degrees(a), lift=0.15)
        c.ellipse(u, v, r * 0.38, r * 0.36, scale(col, 0.78), lift=0.1)
        c.ellipse(u, v, r * 0.17, r * 0.15, (0.98, 0.82, 0.35), lift=0.1)
    # kraft paper wrap, a ribbon and a bow
    _poly(c, [(-0.34, 0.60), (0.34, 0.60), (0.06, 0.06), (-0.06, 0.06)], mix(KRAFT, WHITE, 0.24), scale(KRAFT, 0.66))
    _poly(c, [(-0.34, 0.60), (-0.15, 0.60), (-0.02, 0.07), (-0.06, 0.06)], WHITE, None, 0.18)
    _poly(c, [(-0.36, 0.58), (0.36, 0.58), (0.38, 0.64), (-0.38, 0.64)], mix(KRAFT, WHITE, 0.38), scale(KRAFT, 0.8))
    _poly(c, [(-0.17, 0.30), (0.17, 0.30), (0.14, 0.25), (-0.14, 0.25)], acc, scale(acc, 0.7))
    _bow(c, 0.0, 0.27, 0.12, acc)


@sprop("biz_ribbon_spools", aspect=2.1, fill=0.30)
def biz_ribbon_spools(c, color):
    acc = _rib(color or (0.55, 0.12, 0.25))
    ao(c, 0.0, 0.0, 1.2, 0.16, 0.45)
    for (u, col, h) in ((-0.62, acc, 0.24), (-0.20, GOLD, 0.30), (0.20, (0.97, 0.93, 0.86), 0.24), (0.58, mix(acc, WHITE, 0.5), 0.28)):
        _hfill(c, u - 0.16, 0.0, u + 0.16, h, _cyl_fn(mix(col, WHITE, 0.18), scale(col, 0.58), 0.4), strips=6)
        c.ellipse(u, h, 0.16, 0.05, mix(col, WHITE, 0.3), lift=0)
        c.ellipse(u, h, 0.05, 0.018, (0.25, 0.22, 0.2), lift=0)
        _rr(c, u - 0.18, 0.0, u + 0.18, 0.02, (0.55, 0.45, 0.35), (0.35, 0.28, 0.22), 0.0)
        _rr(c, u - 0.18, h - 0.015, u + 0.18, h + 0.005, (0.55, 0.45, 0.35), (0.35, 0.28, 0.22), 0.0)
    # scissors lying in front
    c.line(-0.5, -0.0, -0.1, 0.045, 0.014, (0.80, 0.82, 0.86), 1.0)
    c.line(-0.5, 0.03, -0.1, 0.02, 0.014, (0.70, 0.72, 0.76), 1.0)
    c.ring(-0.12, 0.03, 0.04, 0.014, acc, 1.0)
    c.ring(-0.10, 0.065, 0.04, 0.014, acc, 1.0)


def _wood_shelf(S, u0, u1, v, base, items_rng, P, dk, n_items=9):
    """A wall shelf loaded with small gifts: boxes with ribbons, mugs, a teddy; plain shapes only."""
    S.rect((u0 + u1) / 2, v + 0.012, u1 - u0, 0.022, base, lift=0.1)
    u = u0 + 0.05
    while u < u1 - 0.07:
        kind = items_rng.randrange(5)
        col = mix(PASTEL[items_rng.randrange(len(PASTEL))], P.accent, 0.08)
        col = _tn(P, col, 0.55)
        if kind in (0, 1):
            w, h = items_rng.uniform(0.06, 0.09), items_rng.uniform(0.06, 0.10)
            S.rect(u + w / 2, v - h / 2, w, h, col, lift=0.12)
            S.rect(u + w / 2, v - h / 2, w * 0.16, h, _tn(P, _rib(P.accent), 0.6), lift=0.0)
            S.rect(u + w / 2, v - h - 0.006, w * 0.30, 0.012, _tn(P, _rib(P.accent), 0.6), lift=0.0)
            u += w + 0.02
        elif kind == 2:
            S.rect(u + 0.025, v - 0.022, 0.05, 0.044, _tn(P, (0.97, 0.97, 0.97), 0.55), r=0.005, lift=0.12)
            S.circle(u + 0.056, v - 0.022, 0.014, _tn(P, (0.97, 0.97, 0.97), 0.55), lift=0.0)
            u += 0.08
        elif kind == 3:
            tb = _tn(P, (0.78, 0.58, 0.40), 0.55)
            S.circle(u + 0.04, v - 0.034, 0.034, tb, lift=0.15)
            S.circle(u + 0.04, v - 0.083, 0.026, tb, lift=0.15)
            S.circle(u + 0.018, v - 0.103, 0.011, tb, lift=0.0)
            S.circle(u + 0.062, v - 0.103, 0.011, tb, lift=0.0)
            u += 0.09
        else:
            S.rect(u + 0.025, v - 0.045, 0.040, 0.09, col, r=0.012, lift=0.15)
            S.rect(u + 0.025, v - 0.095, 0.022, 0.014, _tn(P, GOLD, 0.6), lift=0.0)
            u += 0.07


@niche("gift-shop", "Gift shop and personalised gifts", subjects=("biz_gift_stack",),
       strong=("gift shop", "gift store", "gift shop near me", "gift boxes", "gift hampers", "gift hamper", "personalised gifts", "personalized gifts", "return gifts",
               "corporate gifts", "corporate gifting", "photo mugs", "customised gifts", "customized gifts", "gift wrapping", "gift items", "gifting store",
               "गिफ्ट शॉप", "गिफ्ट की दुकान", "उपहार की दुकान", "उपहार", "गिफ्ट हैम्पर", "रिटर्न गिफ्ट", "कस्टमाइज्ड गिफ्ट", "gift ki dukaan", "return gift shop", "gift wala"),
       weak=("gift", "gifts", "hamper", "hampers", "wrapping", "ribbon", "present", "presents", "mug", "keychain", "गिफ्ट", "तोहफा", "बैलून", "greeting card"),
       accent="#8b1e3f", mood="warm", group="retail",
       avoid=("florist", "flower shop", "bouquet shop", "toy store", "toys", "bakery", "cake shop", "sweet shop", "mithai", "event planner", "party planner", "balloon decoration",
              "jewellery", "bookstore", "stationery", "फूल की दुकान", "मिठाई की दुकान", "खिलौने"))
def gift_shop(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(61)
    wall_t = mix(P.wall_top, (0.96, 0.90, 0.86), 0.3) if not dk else P.wall_top
    wood = _tn(P, (0.62, 0.45, 0.30), 0.55)
    with S.far():
        S.wall(wall_t, P.wall_bot, 0.66)
        for k in range(7):                                                                 # soft vertical panelling
            S.rect(-0.1 + k * 0.34, 0.33, 0.006, 0.66, scale(wall_t, 0.92 if not dk else 0.7), lift=0.0)
        # wall shelves full of small gifts, a hanging garland of bokeh lights
        _wood_shelf(S, 0.00, 0.96, 0.28, wood, random.Random(3), P, dk)
        _wood_shelf(S, 0.00, 0.96, 0.46, wood, random.Random(8), P, dk)
        _wood_shelf(S, 1.18, 2.10, 0.30, wood, random.Random(14), P, dk)
        _wood_shelf(S, 1.18, 2.10, 0.50, wood, random.Random(19), P, dk)
        S.bokeh(14, 0.0, 0.06, 2.0, 0.20, [(1.0, 0.85, 0.55), (1.0, 0.7, 0.5), (1.0, 0.95, 0.85)], 0.008, 0.022, 0.55 if dk else 0.32)
        S.line(-0.1, 0.08, 1.0, 0.13, 0.003, _tn(P, (0.45, 0.35, 0.28), 0.5), 0.8)
        S.line(1.0, 0.13, 2.1, 0.08, 0.003, _tn(P, (0.45, 0.35, 0.28), 0.5), 0.8)
        for u in (0.40, 1.60):
            S.pendant(u, 0.0, 0.22, color=(1.0, 0.82, 0.55), shade_w=0.10)
        S.glow(1.05, 0.40, 0.9, P.light, 0.16 if not dk else 0.10)
        S.floor(0.68, mix(wood, wall_t, 0.1), scale(wood, 0.55))                           # counter top surface across the picture
        S.rect(1.0, 0.685, 14.0, 0.022, scale(wood, 1.25), lift=0.0)
        S.soft(1.15, 0.90, 1.3, 0.22, mix(P.light, (1.0, 0.9, 0.78), 0.4), 0.38 if not dk else 0.40, 1.4, add=True)
    _boards(S, -0.5, 0.70, 2.7, 1.6, wood, 0.07, 4)
    for vv in (0.74, 0.82, 0.94, 1.12):
        _shair(S, -2, vv, 4, vv, scale(wood, 0.55), 0.35)
    # a soft cloth runner under the display
    _spoly(S, [(0.62, 0.84), (1.78, 0.84), (1.92, 1.30), (0.48, 1.30)], mix(P.paper, P.accent_light, 0.25) if not dk else scale(P.accent, 0.5), None, 0.92)
    S.soft(1.15, 1.00, 0.8, 0.18, (1.0, 0.92, 0.80), 0.28 if not dk else 0.24, 1.4, add=True)
    rib = _rib(P.accent)
    S.put("biz_balloons", 1.50, 0.99, 0.52, color=P.accent, shadow=False)
    S.put("biz_hamper", 0.82, 1.06, 0.30, color=rib, shadow_w=0.34, shadow_alpha=0.4)
    S.put("biz_gift_stack", 1.15, 1.02, 0.50, color=rib, subject=True, shadow_w=0.42, shadow_alpha=0.42)
    S.put("biz_photo_mug", 1.40, 1.13, 0.11, color=P.accent, shadow_w=0.14)
    S.put("biz_cushion", 0.56, 1.10, 0.20, color=mix(P.accent_light, (0.95, 0.80, 0.78), 0.4), shadow_w=0.2, framed=False)
    S.put("biz_gift_bags", 1.78, 1.04, 0.20, color=P.accent, shadow_w=0.3, framed=False)
    S.put("biz_ribbon_spools", 0.98, 1.20, 0.07, color=P.accent, shadow=False, framed=False)
    S.focus("detail", 1.12, 0.86)
    with S.near(blur=16):
        S.soft(0.25, 1.05, 0.3, 0.10, P.accent_light, 0.18, 1.2, add=True)
        S.circle(1.92, 1.06, 0.06, mix(P.accent, WHITE, 0.4), alpha=0.5, lift=0.1)


# ====================================================================================== loan and finance agent
@sprop("biz_house_model", aspect=1.28, fill=1.0)
def biz_house_model(c, color):
    acc = color or (0.12, 0.21, 0.34)
    roof = mix(acc, (0.62, 0.30, 0.22), 0.30)
    wall = (0.97, 0.93, 0.85)
    ao(c, 0.0, 0.0, 1.35, 0.20, 0.45)
    # lawn slab with a path and two shrubs
    _poly(c, [(-0.64, 0.02), (0.60, 0.02), (0.64, 0.075), (-0.62, 0.075)], (0.20, 0.44, 0.24), (0.12, 0.30, 0.18))
    _rr(c, -0.64, 0.0, 0.60, 0.03, mix((0.24, 0.50, 0.28), WHITE, 0.1), (0.14, 0.34, 0.20), 0.004)
    _poly(c, [(-0.23, 0.03), (-0.05, 0.03), (-0.03, 0.075), (-0.21, 0.075)], (0.86, 0.80, 0.70), (0.70, 0.64, 0.56))
    # walls: pentagon front, shaded side
    _poly(c, [(0.20, 0.075), (0.48, 0.12), (0.48, 0.47), (0.20, 0.52)], scale(wall, 0.72), scale(wall, 0.56))
    _poly(c, [(-0.46, 0.075), (0.20, 0.075), (0.20, 0.52), (-0.13, 0.76), (-0.46, 0.52)], mix(wall, WHITE, 0.10), scale(wall, 0.86))
    # roof: lit slope behind the gable, bargeboards, chimney
    _poly(c, [(-0.13, 0.76), (0.34, 0.80), (0.54, 0.47), (0.20, 0.52)], mix(roof, WHITE, 0.10), scale(roof, 0.60))
    for k in range(5):
        t = k / 5.0
        c.line(0.20 + 0.34 * t, 0.52 - 0.05 * t + 0.0, -0.13 + 0.47 * t, 0.76 + 0.04 * t, 0.004, scale(roof, 0.45), 0.5)
    _rr(c, 0.22, 0.62, 0.31, 0.86, (0.72, 0.38, 0.30), (0.50, 0.24, 0.20), 0.004)
    _rr(c, 0.21, 0.845, 0.32, 0.875, (0.60, 0.30, 0.24), (0.40, 0.18, 0.16), 0.004)
    c.line(-0.50, 0.485, -0.13, 0.79, 0.042, mix(roof, WHITE, 0.14), 1.0)
    c.line(-0.13, 0.79, 0.23, 0.50, 0.042, mix(roof, WHITE, 0.08), 1.0)
    c.line(-0.50, 0.50, -0.13, 0.80, 0.008, WHITE, 0.35)
    # round attic window, two windows and the door with a small step and lamp
    c.ellipse(-0.13, 0.56, 0.058, 0.058, (1.0, 1.0, 1.0), lift=0)
    c.ellipse(-0.13, 0.56, 0.044, 0.044, (0.60, 0.78, 0.92), lift=0.25)
    for (x0, x1) in ((-0.40, -0.28), (0.00, 0.14)):
        _rr(c, x0 - 0.012, 0.250, x1 + 0.012, 0.442, (1.0, 1.0, 1.0), (0.88, 0.88, 0.9), 0.004)
        _rr(c, x0, 0.262, x1, 0.430, (0.64, 0.80, 0.94), (0.40, 0.60, 0.82), 0.002)
        c.line((x0 + x1) / 2, 0.262, (x0 + x1) / 2, 0.430, 0.006, WHITE, 0.95)
        c.line(x0, 0.346, x1, 0.346, 0.006, WHITE, 0.95)
        _poly(c, [(x0 + 0.01, 0.428), (x0 + 0.04, 0.428), (x0 + 0.0, 0.27), (x0 - 0.01, 0.27)], WHITE, None, 0.3)
        _rr(c, x0 - 0.02, 0.236, x1 + 0.02, 0.252, (0.92, 0.88, 0.80), (0.74, 0.70, 0.62), 0.003)
    door = mix(acc, (0.56, 0.36, 0.22), 0.5)
    _rr(c, -0.215, 0.075, -0.065, 0.36, mix(door, WHITE, 0.14), scale(door, 0.7), 0.04)
    _rr(c, -0.195, 0.10, -0.085, 0.33, scale(door, 1.1), scale(door, 0.8), 0.03)
    c.ellipse(-0.092, 0.20, 0.008, 0.008, (0.95, 0.80, 0.35), lift=0.2)
    c.ellipse(-0.04, 0.30, 0.012, 0.016, (1.0, 0.92, 0.6), lift=0.1)
    c.glow(-0.04, 0.30, 0.10, (1.0, 0.9, 0.6), 0.3)
    for (u, r) in ((-0.40, 0.065), (0.42, 0.055)):
        c.ellipse(u, 0.115, r, r * 0.8, (0.22, 0.48, 0.26), lift=0.25)
        c.ellipse(u - r * 0.3, 0.135, r * 0.4, r * 0.3, (0.40, 0.66, 0.40), lift=0.1)
    _poly(c, [(-0.45, 0.50), (-0.40, 0.50), (-0.40, 0.08), (-0.45, 0.08)], WHITE, None, 0.18)


@sprop("biz_coin_stacks", aspect=4.0, fill=0.30)
def biz_coin_stacks(c, color):
    ao(c, 0.0, 0.0, 1.30, 0.18, 0.45)
    r, t = 0.085, 0.026
    gold, gdark = (0.97, 0.80, 0.28), (0.66, 0.46, 0.12)
    # stacks drawn back to front
    for (u, v0, n) in ((0.22, 0.05, 6), (-0.10, 0.045, 9), (-0.40, 0.03, 5), (0.50, 0.0, 3)):
        h = n * t
        c.ellipse(u, v0, r, r * 0.40, gdark, lift=0)
        _hfill(c, u - r, v0, u + r, v0 + h, _cyl_fn(mix(gold, WHITE, 0.15), gdark, 0.35), strips=8)
        for i in range(1, n):
            craft.arc(c, u, v0 + i * t, r * 0.985, r * 0.40, 190, 350, 0.0032, scale(gdark, 0.7), 0.7, steps=6)
        c.ellipse(u, v0 + h, r, r * 0.40, mix(gold, WHITE, 0.10), lift=0.08)
        c.ellipse(u, v0 + h, r * 0.76, r * 0.30, scale(gold, 0.82), lift=0, alpha=0.8)
        c.ellipse(u, v0 + h, r * 0.62, r * 0.24, mix(gold, WHITE, 0.2), lift=0.0, alpha=0.8)
        soft_disc(c, u - r * 0.3, v0 + h + 0.005, r * 0.4, r * 0.12, WHITE, 0.5, 1.2, 0, True)
    # a coin standing on its edge and two loose flat coins
    cx0, cy0 = 0.34, 0.100
    c.ellipse(cx0, cy0, 0.106, 0.108, scale(gdark, 0.9), lift=0)
    c.ellipse(cx0 - 0.005, cy0 + 0.004, 0.098, 0.100, gold, lift=0.25)
    c.ellipse(cx0 - 0.005, cy0 + 0.004, 0.074, 0.076, scale(gold, 0.85), lift=0, alpha=0.85)
    c.ellipse(cx0 - 0.005, cy0 + 0.004, 0.058, 0.060, mix(gold, WHITE, 0.2), lift=0.1, alpha=0.9)
    c.ellipse(cx0 - 0.005, cy0 + 0.004, 0.020, 0.020, scale(gold, 0.8), lift=0)
    soft_disc(c, cx0 - 0.04, cy0 + 0.04, 0.04, 0.025, WHITE, 0.6, 1.2, 30, True)
    for (u, v0) in ((-0.64, 0.0), (-0.54, -0.0)):
        c.ellipse(u, v0 + 0.012, r, r * 0.40, gdark, lift=0)
        c.ellipse(u, v0 + 0.030, r, r * 0.40, mix(gold, WHITE, 0.10), lift=0.1)
        c.ellipse(u, v0 + 0.030, r * 0.62, r * 0.24, scale(gold, 0.85), lift=0, alpha=0.7)


@sprop("biz_doc_clipboard", aspect=0.74, fill=1.0)
def biz_doc_clipboard(c, color):
    acc = color or (0.12, 0.21, 0.34)
    ao(c, 0.04, 0.0, 0.80, 0.09, 0.4)
    _rr(c, -0.37, 0.0, 0.37, 0.96, mix((0.62, 0.44, 0.28), WHITE, 0.1), (0.40, 0.27, 0.16), 0.03)
    _rr(c, -0.31, 0.04, 0.31, 0.88, (1.0, 0.99, 0.96), (0.90, 0.90, 0.88), 0.008)
    _rr(c, -0.25, 0.76, -0.04, 0.82, acc, scale(acc, 0.7), 0.01)
    c.ellipse(0.19, 0.79, 0.045, 0.045, mix(acc, GOLD, 0.35), lift=0.2)                    # letterhead mark: plain disc and bars
    ink = (0.55, 0.57, 0.62)
    _lines(c, -0.25, 0.25, 0.70, 4, 0.045, ink, 0.008, 0.75, jitter=(0.0, 0.03, 0.0))
    _rr(c, -0.25, 0.28, 0.25, 0.48, (0.94, 0.95, 0.97), (0.90, 0.92, 0.95), 0.0)          # schedule table with striped rows
    for k in range(4):
        _rr(c, -0.25, 0.28 + k * 0.05, 0.25, 0.28 + k * 0.05 + 0.025, mix(acc, WHITE, 0.82), mix(acc, WHITE, 0.74), 0.0)
        for j in range(3):
            c.line(-0.21 + j * 0.17, 0.2925 + k * 0.05, -0.12 + j * 0.17, 0.2925 + k * 0.05, 0.007, ink, 0.7)
    c.line(-0.25, 0.28, 0.25, 0.28, 0.004, ink, 0.8)
    craft.strand(c, -0.22, 0.17, 0.20, 12, 0.007, (0.10, 0.12, 0.40), 0.9, 0.9)             # signature squiggle
    c.line(-0.24, 0.14, 0.0, 0.14, 0.004, ink, 0.7)
    # gold seal with two ribbon tails
    _poly(c, [(0.12, 0.14), (0.18, 0.14), (0.15, 0.06)], mix(acc, WHITE, 0.1), None)
    _poly(c, [(0.17, 0.14), (0.23, 0.14), (0.22, 0.06)], scale(acc, 0.8), None)
    for k in range(10):
        a = math.radians(k * 36)
        c.ellipse(0.17 + 0.05 * math.cos(a), 0.19 + 0.05 * math.sin(a), 0.017, 0.017, GOLD, lift=0.1)
    c.ellipse(0.17, 0.19, 0.045, 0.045, mix(GOLD, WHITE, 0.15), lift=0.2)
    c.ellipse(0.17, 0.19, 0.025, 0.025, scale(GOLD, 0.8), lift=0, alpha=0.8)
    _rr(c, -0.10, 0.90, 0.10, 1.00, mix(CHROME, WHITE, 0.2), scale(CHROME, 0.55), 0.025)       # clip
    _rr(c, -0.06, 0.86, 0.06, 0.93, scale(CHROME, 0.65), scale(CHROME, 0.4), 0.01)
    _poly(c, [(-0.36, 0.94), (-0.33, 0.94), (-0.33, 0.04), (-0.36, 0.04)], WHITE, None, 0.18)


def _sheet(c, cx, y0, y1, w0, w1, sh, top, bot, lines=True, ink=(0.6, 0.62, 0.68), seed=0):
    """A sheet lying flat in perspective: front edge w0 wide at y0, back edge w1 at y1, back edge shifted by sh (a slight fan)."""
    pts = [(cx - w0 / 2, y0), (cx + w0 / 2, y0), (cx + w1 / 2 + sh, y1), (cx - w1 / 2 + sh, y1)]
    _poly(c, pts, top, bot)
    if lines:
        for k in range(6):
            t = 0.16 + k * 0.125
            y = y0 + (y1 - y0) * t
            xl = cx - w0 / 2 + (-w1 / 2 + sh + w0 / 2) * t
            xr = cx + w0 / 2 + (w1 / 2 + sh - w0 / 2) * t
            wd = xr - xl
            c.line(xl + wd * 0.10, y, xr - wd * (0.10 if k % 3 else 0.34), y, 0.006, ink, 0.7)


@sprop("biz_loan_docs", aspect=2.7, fill=0.46)
def biz_loan_docs(c, color):
    acc = color or (0.12, 0.21, 0.34)
    ao(c, 0.0, 0.0, 1.3, 0.22, 0.45)
    # folder under the papers (with a tab), three sheets fanned, a seal, a pen
    _poly(c, [(-0.60, 0.0), (0.56, 0.0), (0.50, 0.40), (-0.54, 0.40)], mix(acc, WHITE, 0.10), scale(acc, 0.62))
    _poly(c, [(-0.54, 0.40), (-0.30, 0.40), (-0.27, 0.45), (-0.50, 0.45)], mix(acc, WHITE, 0.12), scale(acc, 0.72))
    _poly(c, [(-0.60, 0.0), (0.56, 0.0), (0.56, 0.025), (-0.60, 0.025)], BLACK, None, 0.35)
    _sheet(c, -0.12, 0.035, 0.38, 0.90, 0.80, -0.03, (0.98, 0.98, 0.96), (0.90, 0.90, 0.88), lines=False)
    _sheet(c, 0.02, 0.040, 0.36, 0.90, 0.80, 0.05, (0.99, 0.99, 0.97), (0.92, 0.92, 0.90), lines=False)
    _sheet(c, -0.04, 0.050, 0.34, 0.86, 0.76, 0.0, (1.0, 1.0, 0.99), (0.95, 0.95, 0.93))
    c.ellipse(0.26, 0.095, 0.045, 0.020, (0.80, 0.16, 0.16), lift=0.2)
    c.ellipse(0.26, 0.098, 0.022, 0.009, (0.55, 0.08, 0.08), lift=0, alpha=0.8)
    c.line(-0.38, 0.115, -0.12, 0.115, 0.004, (0.1, 0.1, 0.4), 0.6)
    c.line(0.15, 0.06, 0.66, 0.16, 0.026, (0.10, 0.11, 0.14), 1.0)                        # pen
    c.line(0.20, 0.07, 0.40, 0.11, 0.008, GOLD, 1.0)
    c.line(0.64, 0.158, 0.70, 0.17, 0.008, GOLD, 1.0)


@sprop("biz_calculator", aspect=0.66, fill=0.85)
def biz_calculator(c, color):
    acc = color or (0.12, 0.21, 0.34)
    ao(c, 0.03, 0.0, 0.70, 0.09, 0.5)
    _poly(c, [(0.27, 0.02), (0.31, 0.05), (0.31, 0.82), (0.27, 0.85)], scale((0.20, 0.21, 0.24), 0.8), scale((0.12, 0.12, 0.14), 0.6))
    _rr(c, -0.28, 0.0, 0.28, 0.85, (0.30, 0.31, 0.35), (0.10, 0.10, 0.12), 0.04)
    _rr(c, -0.24, 0.72, 0.24, 0.81, (0.12, 0.20, 0.34), (0.06, 0.10, 0.18), 0.01)         # solar strip
    for k in range(1, 6):
        c.line(-0.24 + k * 0.08, 0.72, -0.24 + k * 0.08, 0.81, 0.003, (0.35, 0.45, 0.6), 0.6)
    _rr(c, -0.23, 0.56, 0.23, 0.69, (0.66, 0.78, 0.62), (0.52, 0.66, 0.50), 0.01)         # display with a blank bar, no digits
    _rr(c, 0.12, 0.60, 0.20, 0.65, scale((0.55, 0.68, 0.52), 0.7), scale((0.55, 0.68, 0.52), 0.55), 0.004)
    soft_disc(c, -0.1, 0.665, 0.15, 0.02, WHITE, 0.4, 1.1, 0, True)
    for r in range(5):
        for k in range(4):
            x0 = -0.215 + k * 0.112
            y0 = 0.04 + r * 0.098
            if k == 3:
                col = mix(acc, WHITE, 0.15) if r != 0 else (0.80, 0.30, 0.20)
            elif r == 4 and k == 0:
                col = (0.86, 0.87, 0.90)
            else:
                col = (0.86, 0.87, 0.90) if (r + k) % 2 else (0.74, 0.76, 0.80)
            if r == 0 and k == 2:
                col = (0.97, 0.78, 0.30)
            _rr(c, x0, y0, x0 + 0.095, y0 + 0.078, mix(col, WHITE, 0.2), scale(col, 0.72), 0.014)
    _poly(c, [(-0.27, 0.80), (-0.22, 0.80), (-0.22, 0.04), (-0.27, 0.04)], WHITE, None, 0.15)


@sprop("biz_bar_chart", aspect=1.1, fill=0.98)
def biz_bar_chart(c, color):
    acc = color or (0.12, 0.21, 0.34)
    ao(c, 0.05, 0.0, 1.1, 0.14, 0.45)
    _box3(c, 0.0, 0.0, 1.0, 0.04, 0.34, (0.95, 0.95, 0.96), r=0.004)
    tops = []
    for k, hh in enumerate((0.16, 0.26, 0.36, 0.50, 0.66)):
        u = -0.40 + k * 0.20
        col = mix(mix(acc, WHITE, 0.55), acc, k / 4.0)
        _box3(c, u, 0.05, 0.14, hh, 0.14, col, r=0.004)
        tops.append((u + 0.02, 0.05 + hh + 0.05))
    pts = [(tops[0][0] - 0.05, tops[0][1] + 0.04)] + tops
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], 0.022, (0.95, 0.74, 0.20), 1.0)
        c.line(a[0], a[1] + 0.008, b[0], b[1] + 0.008, 0.006, WHITE, 0.45)
    ex, ey = tops[-1][0] + 0.02, tops[-1][1] + 0.04
    _poly(c, [(ex - 0.10, ey - 0.07), (ex + 0.10, ey + 0.04), (ex - 0.07, ey + 0.10)], (0.98, 0.78, 0.24), (0.82, 0.58, 0.10))
    for (u, v) in tops:
        c.ellipse(u, v, 0.022, 0.022, (0.98, 0.80, 0.30), lift=0.2)


@sprop("biz_banker_lamp", aspect=0.86, fill=0.8)
def biz_banker_lamp(c, color):
    ao(c, 0.0, 0.0, 0.5, 0.08, 0.45)
    _oval(c, 0.0, 0.03, 0.17, 0.05, (0.62, 0.50, 0.24), (0.30, 0.22, 0.08))
    c.line(0.0, 0.05, 0.0, 0.45, 0.028, (0.78, 0.62, 0.28), 1.0)
    c.line(0.0, 0.05, 0.0, 0.45, 0.008, WHITE, 0.4)
    c.glow(-0.05, 0.46, 0.7, (1.0, 0.88, 0.55), 0.55)
    pts = [(-0.34 + 0.68 * k / 14.0, 0.50 + 0.26 * math.sin(math.pi * k / 14.0) ** 0.7) for k in range(15)]
    _poly(c, pts, (0.18, 0.50, 0.34), (0.06, 0.24, 0.16))
    _poly(c, [(-0.26, 0.60), (-0.10, 0.74), (-0.14, 0.56)], WHITE, None, 0.25)
    _rr(c, -0.35, 0.48, 0.35, 0.52, (0.80, 0.66, 0.30), (0.50, 0.38, 0.14), 0.01)
    _oval(c, 0.0, 0.48, 0.28, 0.025, (1.0, 0.95, 0.75), (0.95, 0.80, 0.45), 0.9)


@niche("loan-finance", "Loan and finance agent", subjects=("biz_house_model",),
       strong=("loan agent", "loan consultant", "loan and finance", "loan finance", "home loan", "home loans", "personal loan", "business loan", "loan against property",
               "vehicle loan", "loan documentation", "finance agent", "loan services", "mortgage agent", "mortgage broker", "loan advisor", "credit report guidance",
               "लोन एजेंट", "लोन कंसल्टेंट", "होम लोन", "पर्सनल लोन", "बिज़नेस लोन", "लोन सलाहकार", "फाइनेंस एजेंट", "लोन और फाइनेंस", "loan lene ke liye", "loan wala",
               "loan dilane wale", "finance wala"),
       weak=("loan", "loans", "emi", "mortgage", "sanction", "credit score", "cibil", "finance", "lender", "down payment", "tenure", "लोन", "फाइनेंस", "ईएमआई", "कर्ज"),
       accent="#1d3557", mood="light", group="professional",
       avoid=("accounting", "accountant", "chartered accountant", "tax", "gst return filing", "bookkeeping", "audit", "insurance", "insurance agent", "bank branch", "atm",
              "mutual fund", "stock broker", "share market", "law firm", "lawyer", "real estate agent", "property dealer", "लेखाकार", "बीमा", "टैक्स"))
def loan_finance(S):
    P = S.pal
    dk = _dk(P)
    rng = random.Random(71)
    wall_c = mix(P.wall_top, (0.90, 0.88, 0.82), 0.4) if not dk else P.wall_top
    desk = _tn(P, (0.46, 0.31, 0.20), 0.55)
    book_cols = ((0.45, 0.20, 0.22), (0.18, 0.30, 0.45), (0.22, 0.40, 0.30), (0.55, 0.42, 0.22), (0.30, 0.26, 0.40), (0.62, 0.55, 0.45))
    with S.far():
        S.wall(wall_c, scale(wall_c, 0.90), 0.66)
        # wainscot panelling on the lower wall and a built-in bookcase of ledgers
        S.rect(1.0, 0.585, 6.0, 0.15, scale(wall_c, 0.84 if not dk else 0.7), lift=0.04)
        for k in range(14):
            S.rect(-0.2 + k * 0.17, 0.585, 0.006, 0.13, scale(wall_c, 0.66), lift=0.0)
        S.rect(0.42, 0.34, 0.80, 0.52, scale(wall_c, 0.62 if not dk else 0.5), lift=0.0)
        for row in range(4):
            v = 0.12 + row * 0.12
            S.rect(0.42, v + 0.062, 0.76, 0.014, scale(desk, 1.1), lift=0.08)
            u = 0.05
            while u < 0.78:
                w = rng.uniform(0.022, 0.042)
                h = rng.uniform(0.07, 0.105)
                col = _tn(P, book_cols[rng.randrange(len(book_cols))], 0.6)
                S.rect(u + w / 2, v + 0.055 - h / 2, w, h, col, lift=0.10)
                S.rect(u + w / 2, v + 0.055 - h * 0.62, w * 0.9, 0.007, _tn(P, GOLD, 0.65), lift=0.0)
                u += w + 0.004
        # framed certificates on the right wall (plain bars inside), a window with cool light
        for k, (u, v, w, h) in enumerate(((1.16, 0.26, 0.17, 0.22), (1.40, 0.28, 0.24, 0.17), (1.66, 0.26, 0.17, 0.22))):
            S.rect(u, v, w + 0.02, h + 0.02, _tn(P, (0.55, 0.40, 0.24), 0.6), lift=0.08)
            S.rect(u, v, w, h, _tn(P, (0.97, 0.96, 0.92), 0.6), lift=0.04)
            for j in range(4):
                S.rect(u, v - h * 0.28 + j * h * 0.18, w * (0.7 if j < 3 else 0.4), 0.007, _tn(P, (0.55, 0.57, 0.62), 0.6), lift=0.0)
            S.circle(u + w * 0.28, v + h * 0.30, 0.016, _tn(P, GOLD, 0.65), lift=0.1)
        S.glow(1.05, 0.30, 1.1, P.light, 0.18 if not dk else 0.12)
        S.floor(0.665, desk, scale(desk, 0.58))                                                           # the desk top
        S.rect(1.0, 0.672, 14.0, 0.016, scale(desk, 1.3), lift=0.0)
        S.soft(1.15, 0.92, 1.3, 0.22, mix(P.light, (1.0, 0.92, 0.80), 0.4), 0.36 if not dk else 0.40, 1.4, add=True)
    _boards(S, -0.5, 0.68, 2.7, 1.6, desk, 0.12, 5, 4)
    for vv in (0.72, 0.80, 0.94, 1.14):
        _shair(S, -2, vv, 4, vv, scale(desk, 0.55), 0.35)
    # leather desk blotter in the accent colour with a stitched edge
    leather = mix(P.accent_dark, (0.15, 0.20, 0.18), 0.2) if not dk else scale(P.accent, 0.6)
    _spoly(S, [(0.52, 0.80), (1.86, 0.80), (2.04, 1.32), (0.34, 1.32)], mix(leather, WHITE, 0.05), scale(leather, 0.8), 1.0)
    _shair(S, 0.56, 0.83, 1.83, 0.83, mix(leather, WHITE, 0.45), 0.5)
    S.soft(1.15, 1.02, 0.8, 0.18, (1.0, 0.92, 0.8), 0.28 if not dk else 0.24, 1.4, add=True)
    S.put("biz_banker_lamp", 1.80, 0.96, 0.34, shadow_w=0.2, framed=False)
    S.put("biz_doc_clipboard", 0.82, 0.97, 0.40, color=P.accent, shadow_w=0.3, shadow_alpha=0.4)
    S.put("biz_bar_chart", 1.48, 0.99, 0.33, color=P.accent, shadow_w=0.4, shadow_alpha=0.4)
    S.put("biz_house_model", 1.10, 1.04, 0.50, color=P.accent, subject=True, shadow_w=0.62, shadow_alpha=0.42)
    S.put("biz_loan_docs", 0.90, 1.17, 0.15, color=P.accent, shadow=False)
    S.put("biz_coin_stacks", 1.46, 1.13, 0.16, shadow=False)
    S.put("biz_calculator", 1.22, 1.19, 0.14, color=P.accent, shadow_w=0.1)
    S.focus("detail", 1.22, 0.90)
    with S.near(blur=16):
        S.soft(0.25, 1.05, 0.3, 0.10, P.accent_light, 0.18, 1.2, add=True)
        S.circle(1.94, 1.06, 0.06, mix(GOLD, P.accent, 0.3), alpha=0.5, lift=0.1)
