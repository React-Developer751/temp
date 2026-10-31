"""Food and drink props."""
import math

from .core import WHITE, prop, scale, mix


@prop("pizza", aspect=1.0, place="table", nominal=0.5, category="food", words=("pizzas",))
def pizza(c, color):
    c.shadow(0.03, 0.02, 1.0, 0.12)
    crust = c.pick(color, (0.89, 0.64, 0.30))
    c.circle(0, 0.5, 0.5, crust, lift=0.12)
    c.circle(0, 0.5, 0.465, scale(crust, 1.12), lift=0.05)
    c.circle(0, 0.5, 0.43, c.col((0.80, 0.22, 0.12)), lift=0.05)
    c.circle(0, 0.5, 0.405, c.col((0.98, 0.80, 0.36)), lift=0.06)
    for a, r, k in ((20, 0.30, 1.1), (80, 0.27, 0.8), (140, 0.31, 1.0), (200, 0.28, 0.9), (260, 0.30, 1.1), (320, 0.27, 0.9)):
        c.circle(0.0 + r * math.cos(math.radians(a)) * 0.95, 0.5 + r * math.sin(math.radians(a)) * 0.95, 0.07 * k,
                 c.col((0.76, 0.16, 0.12)), lift=0.12)
    for u, v in ((0.0, 0.5), (-0.08, 0.57), (0.1, 0.43)):
        c.circle(u, v, 0.06, c.col((0.78, 0.17, 0.12)), lift=0.12)
    for u, v, ang in ((-0.12, 0.34, 40), (0.14, 0.6, -30), (-0.2, 0.62, 70)):
        c.ellipse(u, v, 0.055, 0.028, c.col((0.20, 0.58, 0.22)), angle=ang)
    for u, v in ((0.2, 0.36), (-0.22, 0.44), (0.05, 0.66)):
        c.ring(u, v, 0.022, 0.014, c.col((0.12, 0.12, 0.12)))
    for a in (0, 45, 90, 135):                              # slice cuts
        d = math.radians(a)
        c.line(-0.41 * math.cos(d), 0.5 - 0.41 * math.sin(d), 0.41 * math.cos(d), 0.5 + 0.41 * math.sin(d), 0.008,
               c.col((0.62, 0.40, 0.12)), alpha=0.55)


@prop("coffee_cup", aspect=1.1, place="table", nominal=0.38, category="food",
      words=("coffee", "cup", "mug", "chai", "tea", "cappuccino", "latte", "espresso", "cups", "mugs"))
def coffee_cup(c, color):
    c.shadow(0.02, 0.02, 0.95, 0.09)
    c.ellipse(0, 0.05, 0.46, 0.06, c.col((0.93, 0.93, 0.95)), lift=0.05)               # saucer
    c.ellipse(0, 0.07, 0.34, 0.035, c.col((0.82, 0.83, 0.88)), lift=0)
    body = c.pick(color, (0.98, 0.98, 0.99))
    c.ring(0.34, 0.27, 0.10, 0.04, body)                                              # handle
    c.poly([(-0.30, 0.46), (0.30, 0.46), (0.21, 0.09), (-0.21, 0.09)], body, lift=0.08)
    c.ellipse(0, 0.10, 0.21, 0.045, scale(body, 0.93), lift=0.05)
    c.ellipse(0, 0.46, 0.30, 0.07, scale(body, 0.88), lift=0.05)                      # rim
    c.ellipse(0, 0.46, 0.265, 0.055, c.col((0.36, 0.20, 0.10)), lift=0.1)             # coffee
    c.circle(0, 0.465, 0.04, c.col((0.93, 0.78, 0.58)), lift=0)                       # latte heart
    c.ellipse(-0.02, 0.466, 0.07, 0.022, c.col((0.93, 0.78, 0.58)), lift=0)
    for u, ph in ((-0.12, 0.0), (0.0, 1.5), (0.12, 3.0)):                             # steam
        pts = [(u + 0.035 * math.sin(ph + t * 4.0), 0.58 + t * 0.38) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        c.path(pts, 0.03, c.col((1.0, 1.0, 1.0)), alpha=0.55)


@prop("croissant", aspect=1.4, place="table", nominal=0.2, fill=0.62, category="food", words=("croissants",))
def croissant(c, color):
    c.shadow(0.0, 0.02, 1.2, 0.10)
    base = c.pick(color, (0.86, 0.56, 0.22))
    n = 7
    order = sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2.0))
    for i in order:
        t = i / (n - 1.0)
        th = math.radians(190 - t * 200)
        f = max(0.0, 1.0 - abs(t - 0.5) * 1.75)
        u, v = 0.44 * math.cos(th), 0.10 + 0.40 * math.sin(th)
        shade = 1.0 + (0.07 if i % 2 else -0.05)
        a, b = 0.075 + 0.17 * f, 0.05 + 0.13 * f
        c.ellipse(u, v, a, b, scale(base, shade), angle=math.degrees(th) - 90, lift=0.16)
        c.ellipse(u - 0.01, v + 0.03 * f, a * 0.55, b * 0.35, scale(base, 1.28), angle=math.degrees(th) - 90, lift=0.0, alpha=0.55)


@prop("bread", aspect=1.5, place="table", nominal=0.18, fill=0.62, category="food", words=("loaf", "baguette", "toast", "loaves"))
def bread(c, color):
    c.shadow(0.0, 0.02, 1.15, 0.10)
    base = c.pick(color, (0.80, 0.50, 0.20))
    c.ellipse(0, 0.32, 0.5, 0.30, base, lift=0.16)
    c.ellipse(-0.05, 0.42, 0.36, 0.14, scale(base, 1.18), lift=0.0, alpha=0.5)
    for u in (-0.27, -0.09, 0.09, 0.27):
        c.ellipse(u, 0.40, 0.095, 0.02, c.col((0.96, 0.82, 0.55)), angle=62, lift=0.0)
    c.ellipse(0, 0.04, 0.46, 0.05, scale(base, 0.7), lift=0.0, alpha=0.4)


@prop("burger", aspect=1.0, place="table", nominal=0.4, category="food", words=("hamburger", "cheeseburger", "burgers", "sandwich"))
def burger(c, color):
    c.shadow(0.0, 0.02, 1.0, 0.10)
    bun = c.pick(color, (0.88, 0.62, 0.28))
    c.ellipse(0, 0.60, 0.5, 0.38, bun, lift=0.16)
    for u, v, a in ((-0.2, 0.78, 20), (0.0, 0.86, 0), (0.2, 0.78, -20), (-0.1, 0.70, 40), (0.12, 0.69, -30), (0.3, 0.62, -50), (-0.3, 0.63, 50)):
        c.ellipse(u, v, 0.03, 0.016, c.col((0.99, 0.94, 0.8)), angle=a, lift=0)
    c.rect(0, 0.52, 0.78, 0.07, c.col((0.86, 0.20, 0.15)), r=0.03)                    # tomato
    for k in range(9):
        c.ellipse(-0.44 + k * 0.11, 0.47, 0.07, 0.045, c.col((0.35, 0.70, 0.25)), lift=0.12)
    c.rect(0, 0.42, 0.86, 0.04, c.col((1.0, 0.78, 0.18)), r=0.015, lift=0.05)         # cheese
    c.poly([(0.30, 0.41), (0.46, 0.41), (0.38, 0.33)], c.col((1.0, 0.78, 0.18)), lift=0.05)
    c.rect(0, 0.30, 0.9, 0.17, c.col((0.40, 0.22, 0.12)), r=0.08, lift=0.18)          # patty
    c.rect(0, 0.12, 0.88, 0.17, scale(bun, 0.95), r=0.08, lift=0.16)                  # bottom bun


@prop("cake", aspect=0.95, place="table", nominal=0.42, category="food", words=("birthday", "cakes", "pastry", "dessert"))
def cake(c, color):
    c.shadow(0.0, 0.02, 1.15, 0.10)
    c.ellipse(0, 0.04, 0.56, 0.06, c.col((0.93, 0.93, 0.96)), lift=0.05)
    pink = c.pick(color, (0.96, 0.60, 0.72))
    c.rect(0, 0.23, 0.92, 0.34, pink, r=0.05, lift=0.12)
    c.rect(0, 0.52, 0.62, 0.26, mix(pink, WHITE, 0.25), r=0.05, lift=0.12)
    cream = c.col((1.0, 0.98, 0.97))
    for tier_v, half, n in ((0.385, 0.46, 9), (0.64, 0.31, 6)):
        c.rect(0, tier_v, half * 2, 0.045, cream, r=0.02, lift=0.04)
        for k in range(n):
            c.circle(-half + 0.04 + k * (half * 2 - 0.08) / (n - 1), tier_v - 0.015, 0.032, cream, lift=0.04)
    for u, v, col in ((-0.3, 0.2, (0.3, 0.7, 0.9)), (0.1, 0.12, (1, 0.85, 0.2)), (0.32, 0.27, (0.6, 0.9, 0.5)), (-0.1, 0.30, (0.9, 0.3, 0.4)),
                      (0.2, 0.5, (0.3, 0.7, 0.9)), (-0.15, 0.55, (1, 0.85, 0.2))):
        c.circle(u, v, 0.016, c.col(col), lift=0)
    c.circle(0, 0.72, 0.06, c.col((0.82, 0.10, 0.18)), lift=0.2)                      # cherry
    for u, col in ((-0.17, (0.35, 0.65, 0.95)), (0.0, (1.0, 0.8, 0.2)), (0.17, (0.4, 0.8, 0.4))):
        c.rect(u, 0.80, 0.035, 0.15, c.col(col), r=0.012)
        c.ellipse(u, 0.93, 0.03, 0.05, c.col((1.0, 0.72, 0.15)), lift=0.0)
        c.ellipse(u, 0.92, 0.015, 0.03, c.col((1.0, 0.95, 0.6)), lift=0.0)
    c.glow(0, 0.92, 0.6, (1.0, 0.7, 0.3), 0.12)


@prop("cupcake", aspect=0.8, place="table", nominal=0.3, category="food", words=("cupcakes", "muffin", "muffins"))
def cupcake(c, color):
    c.shadow(0.0, 0.02, 0.8, 0.09)
    wrap = c.pick(color, (0.90, 0.45, 0.55))
    c.poly([(-0.34, 0.45), (0.34, 0.45), (0.25, 0.04), (-0.25, 0.04)], wrap, lift=0.1)
    for k in range(-2, 3):
        c.line(k * 0.12, 0.44, k * 0.09, 0.06, 0.02, scale(wrap, 0.78), alpha=0.8)
    cream = c.col((1.0, 0.92, 0.85))
    for v, a, b in ((0.52, 0.37, 0.12), (0.66, 0.29, 0.11), (0.79, 0.20, 0.10)):
        c.ellipse(0, v, a, b, cream, lift=0.1)
    c.circle(0, 0.92, 0.07, c.col((0.82, 0.10, 0.18)), lift=0.2)
    for u, v, col in ((-0.15, 0.55, (0.3, 0.7, 0.9)), (0.12, 0.6, (1, 0.85, 0.2)), (0.0, 0.7, (0.6, 0.9, 0.5)), (-0.07, 0.8, (0.9, 0.3, 0.4))):
        c.circle(u, v, 0.014, c.col(col), lift=0)


@prop("icecream", aspect=0.6, place="ground", nominal=0.4, category="food", words=("icecream", "gelato", "cone", "icecreams"))
def icecream(c, color):
    c.shadow(0.0, 0.01, 0.5, 0.06)
    cone = c.col((0.90, 0.67, 0.34))
    A, TL, TR = (0.0, 0.0), (-0.21, 0.52), (0.21, 0.52)
    c.poly([A, TL, TR], cone, lift=0.1)
    ed = lambda p, q, f: (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)       # noqa: E731
    for f in (0.2, 0.4, 0.6, 0.8):
        for g in (0.18,):
            a1, b1 = ed(A, TL, f), ed(A, TR, min(1.0, f + g))
            a2, b2 = ed(A, TL, min(1.0, f + g)), ed(A, TR, f)
            c.line(a1[0], a1[1], b1[0], b1[1], 0.012, c.col((0.66, 0.44, 0.16)))
            c.line(a2[0], a2[1], b2[0], b2[1], 0.012, c.col((0.66, 0.44, 0.16)))
    s1 = c.pick(color, (0.97, 0.62, 0.74))
    c.circle(0, 0.62, 0.23, s1, lift=0.12)
    for k in range(5):
        c.circle(-0.18 + k * 0.09, 0.50, 0.06, s1, lift=0.12)
    c.circle(0, 0.82, 0.19, c.col((0.45, 0.27, 0.16)), lift=0.14)
    c.circle(-0.05, 0.88, 0.05, c.col((0.7, 0.5, 0.35)), lift=0, alpha=0.5)
    c.circle(0.02, 0.98, 0.055, c.col((0.82, 0.10, 0.18)), lift=0.2)


@prop("plate", aspect=2.2, place="table", nominal=0.13, fill=0.38, category="food", words=("pasta", "meal", "dish", "plates", "food", "dinner", "lunch"))
def plate(c, color):
    c.shadow(0.0, 0.03, 1.15, 0.10)
    c.ellipse(0, 0.14, 0.48, 0.14, c.col((0.96, 0.96, 0.98)), lift=0.05)
    c.ellipse(0, 0.15, 0.36, 0.10, c.col((0.88, 0.89, 0.93)), lift=0.0)
    pasta = c.pick(color, (0.97, 0.80, 0.40))
    c.ellipse(0, 0.22, 0.24, 0.10, pasta, lift=0.1)
    for k, ang in enumerate((10, -15, 25, -35)):
        c.ellipse(-0.1 + k * 0.07, 0.25, 0.10, 0.03, scale(pasta, 1.08), angle=ang, lift=0.0, alpha=0.8)
    c.ellipse(0.0, 0.29, 0.12, 0.05, c.col((0.80, 0.20, 0.12)), lift=0.1)
    c.ellipse(0.05, 0.33, 0.045, 0.025, c.col((0.22, 0.60, 0.24)), angle=30)
    c.ellipse(-0.04, 0.32, 0.04, 0.022, c.col((0.22, 0.60, 0.24)), angle=-30)
    metal = c.col((0.80, 0.82, 0.86))                                                   # fork and knife
    c.rect(-0.62, 0.16, 0.035, 0.34, metal, r=0.015)
    for k in (-1, 0, 1):
        c.rect(-0.62 + k * 0.012, 0.36, 0.008, 0.10, metal, r=0.004, lift=0)
    c.rect(0.62, 0.16, 0.05, 0.34, metal, r=0.02)


@prop("glass", aspect=0.45, place="table", nominal=0.3, category="food", words=("wine", "glasses", "drink", "juice", "beverage"))
def glass(c, color):
    c.shadow(0.0, 0.01, 0.4, 0.05)
    c.ellipse(0, 0.03, 0.17, 0.03, c.col((0.85, 0.9, 0.95)), lift=0)
    c.rect(0, 0.28, 0.025, 0.5, c.col((0.85, 0.9, 0.95)), lift=0)
    wine = c.pick(color, (0.60, 0.08, 0.20))
    c.poly([(-0.2, 0.98), (0.2, 0.98), (0.17, 0.62), (0.08, 0.5), (-0.08, 0.5), (-0.17, 0.62)], c.col((0.88, 0.94, 0.98)), lift=0.0, alpha=0.55)
    c.poly([(-0.185, 0.78), (0.185, 0.78), (0.165, 0.62), (0.08, 0.52), (-0.08, 0.52), (-0.165, 0.62)], wine, lift=0.1)
    c.line(-0.13, 0.94, -0.12, 0.72, 0.02, WHITE, alpha=0.5)
