"""Wellness, events, trust and utility icons."""
import math

from .core import WHITE, mix, prop, scale


def _star(c, u, v, r, color, lift=0.12):
    pts = []
    for k in range(10):
        rad = r if k % 2 == 0 else r * 0.45
        a = math.radians(90 + 36 * k)
        pts.append((u + rad * math.cos(a), v + rad * math.sin(a)))
    c.poly(pts, color, lift=lift)


@prop("lotus", aspect=1.3, place="table", nominal=0.2, fill=0.6, category="wellness", words=("flowerpower", "spa", "ayurvedic", "aromatherapy", "massage", "petal", "petals", "bloom", "blossom"))
def lotus(c, color):
    c.shadow(0.0, 0.03, 1.2, 0.08)
    pad = c.col((0.25, 0.60, 0.40))
    c.ellipse(-0.35, 0.08, 0.34, 0.07, pad, lift=0.12)
    c.ellipse(0.38, 0.07, 0.30, 0.06, scale(pad, 0.9), lift=0.12)
    pink = c.pick(color, (0.97, 0.55, 0.72))
    for ang, k in ((150, 0.8), (30, 0.8), (125, 0.92), (55, 0.92)):
        a = math.radians(ang)
        c.ellipse(0.38 * math.cos(a) * 0.6, 0.24 + 0.2 * math.sin(a) * 0.6, 0.12, 0.30, scale(pink, 0.9 * k), angle=ang - 90, lift=0.14)
    for ang in (100, 80):
        c.ellipse(0.0 + 0.1 * math.cos(math.radians(ang)), 0.34, 0.12, 0.30, mix(pink, WHITE, 0.15), angle=ang - 90, lift=0.14)
    c.ellipse(0, 0.38, 0.11, 0.30, mix(pink, WHITE, 0.3), lift=0.14)
    c.ellipse(0, 0.12, 0.11, 0.025, c.col((1.0, 0.85, 0.3)), lift=0)


@prop("candle", aspect=0.9, place="table", nominal=0.24, category="wellness", words=("candles", "diya", "diwali", "aroma", "fragrance", "scented", "incense"))
def candle(c, color):
    c.shadow(0.02, 0.02, 0.85, 0.08)
    wax = c.pick(color, (0.97, 0.90, 0.80))
    for u, h, w in ((-0.28, 0.46, 0.2), (0.0, 0.66, 0.22), (0.30, 0.38, 0.18)):
        c.glow(u, h + 0.12, 0.35, c.col((1.0, 0.8, 0.4)), 0.30)
        c.rect(u, h / 2 + 0.02, w, h, wax, r=0.03, lift=0.14)
        c.ellipse(u, h + 0.02, w / 2, 0.025, scale(wax, 1.08), lift=0.0)
        c.line(u, h + 0.02, u, h + 0.06, 0.012, c.col((0.2, 0.15, 0.12)))
        c.ellipse(u, h + 0.12, 0.035, 0.07, c.col((1.0, 0.65, 0.15)), lift=0.0)
        c.ellipse(u, h + 0.11, 0.018, 0.04, c.col((1.0, 0.95, 0.65)), lift=0.0)


@prop("balloons", aspect=0.95, place="sky", nominal=0.5, category="events", words=("balloon", "party", "celebration", "celebrate", "festival", "carnival", "anniversary", "event", "events", "congratulations", "surprise", "decoration", "decorations"))
def balloons(c, color):
    cols = [(0.93, 0.25, 0.30), (0.25, 0.55, 0.92), (0.98, 0.78, 0.2), (0.35, 0.78, 0.45), (0.80, 0.40, 0.85)]
    if color is not None:
        cols[0] = color
    spots = [(-0.30, 0.78, 0.17), (0.0, 0.88, 0.19), (0.30, 0.78, 0.17), (-0.16, 0.60, 0.16), (0.17, 0.62, 0.16)]
    for k, (u, v, r) in enumerate(spots):
        col = c.pick(color, cols[k]) if (k == 0 and color is not None) else c.col(cols[k])
        c.path([(u, v - r * 1.15), (u * 0.5, 0.30), (0.0, 0.0)], 0.008, c.col((0.45, 0.45, 0.5)))
    for k in (3, 4, 0, 2, 1):
        u, v, r = spots[k]
        col = c.pick(color, cols[k]) if (k == 0 and color is not None) else c.col(cols[k])
        c.ellipse(u, v, r, r * 1.18, col, lift=0.16)
        c.poly([(u - 0.02, v - r * 1.16), (u + 0.02, v - r * 1.16), (u, v - r * 1.28)], scale(col, 0.85), lift=0)
        c.ellipse(u - r * 0.38, v + r * 0.4, r * 0.18, r * 0.30, WHITE, angle=25, lift=0, alpha=0.4)


@prop("trophy", aspect=0.75, place="table", nominal=0.34, category="events", words=("trophies", "winner", "winning", "champion", "award", "awards", "achievement", "success", "prize", "medal", "best", "top", "excellence"))
def trophy(c, color):
    c.shadow(0.0, 0.01, 0.6, 0.06)
    gold = c.pick(color, (0.98, 0.78, 0.22))
    for sgn in (-1, 1):
        c.ring(sgn * 0.27, 0.68, 0.11, 0.035, scale(gold, 0.85))
    c.poly([(-0.28, 0.92), (0.28, 0.92), (0.22, 0.62), (0.10, 0.50), (-0.10, 0.50), (-0.22, 0.62)], gold, lift=0.16)
    c.rect(0, 0.40, 0.07, 0.16, scale(gold, 0.9), lift=0.15)
    c.ellipse(0, 0.33, 0.14, 0.04, scale(gold, 0.85), lift=0.1)
    c.rect(0, 0.20, 0.34, 0.10, c.col((0.40, 0.28, 0.20)), r=0.02, lift=0.15)
    c.rect(0, 0.09, 0.48, 0.10, c.col((0.30, 0.20, 0.14)), r=0.02, lift=0.15)
    c.rect(0, 0.20, 0.16, 0.035, gold, r=0.01, lift=0)
    _star(c, 0, 0.74, 0.10, mix(gold, WHITE, 0.55), lift=0.05)
    c.line(-0.18, 0.88, -0.12, 0.66, 0.025, WHITE, alpha=0.45)


@prop("dumbbell", aspect=1.7, place="table", nominal=0.18, fill=0.5, category="wellness", words=("dumbbells", "weights", "gym", "fitness", "workout", "exercise", "crossfit", "muscle", "bodybuilding", "kettlebell"))
def dumbbell(c, color):
    c.shadow(0.0, 0.1, 1.5, 0.08)
    col = c.pick(color, (0.28, 0.30, 0.38))
    bar = c.col((0.78, 0.80, 0.86))
    ang, piv = 18, (0.0, 0.5)
    c.poly([(-0.70, 0.485), (0.70, 0.485), (0.70, 0.515), (-0.70, 0.515)], bar, lift=0.2, angle=ang, pivot=piv)
    for sgn in (-1, 1):
        for off, h, w in ((0.50, 0.50, 0.10), (0.40, 0.42, 0.10), (0.62, 0.30, 0.08)):
            a = math.radians(ang)
            u = sgn * off
            c.poly([(u - w / 2, 0.5 - h / 2), (u + w / 2, 0.5 - h / 2), (u + w / 2, 0.5 + h / 2), (u - w / 2, 0.5 + h / 2)],
                   scale(col, 1.0 if off < 0.6 else 0.8), lift=0.16, angle=ang, pivot=piv)


@prop("medicalcross", aspect=1.0, place="table", nominal=0.3, category="health", words=("medical", "health", "healthcare", "pharmacy", "medicine", "medicines", "first", "aid", "wellbeing", "cross", "care", "caring", "hygiene", "treatment", "healing"))
def medicalcross(c, color):
    c.shadow(0.02, 0.02, 0.9, 0.07)
    col = c.pick(color, (0.88, 0.20, 0.25))
    c.rect(0, 0.5, 0.92, 0.92, col, r=0.20, lift=0.14)
    wc = c.col((1.0, 1.0, 1.0))
    c.rect(0, 0.5, 0.52, 0.17, wc, r=0.03, lift=0.02)
    c.rect(0, 0.5, 0.17, 0.52, wc, r=0.03, lift=0.02)
    c.path([(-0.38, 0.22), (-0.22, 0.22), (-0.15, 0.32), (-0.05, 0.12), (0.05, 0.28), (0.12, 0.22), (0.38, 0.22)], 0.025, mix(col, WHITE, 0.55), smooth=False)


@prop("suitcase", aspect=1.0, place="ground", nominal=0.3, category="travel", words=("luggage", "suitcases", "trip", "trips", "journey", "baggage", "bag", "backpack", "packing", "tour", "adventure", "explore"))
def suitcase(c, color):
    c.shadow(0.0, 0.01, 0.95, 0.07)
    col = c.pick(color, (0.92, 0.45, 0.20))
    dark = c.col((0.25, 0.26, 0.32))
    c.path([(-0.16, 0.80), (-0.16, 0.92), (0.16, 0.92), (0.16, 0.80)], 0.04, dark, smooth=False)
    c.rect(0, 0.45, 0.92, 0.70, col, r=0.08, lift=0.14)
    for u in (-0.26, 0.26):
        c.rect(u, 0.45, 0.07, 0.70, scale(col, 0.75), lift=0.05)
    c.rect(0, 0.45, 0.92, 0.04, scale(col, 0.7), lift=0)
    c.rect(0, 0.62, 0.10, 0.07, c.col((0.88, 0.88, 0.5)), r=0.01, lift=0.1)
    for u in (-0.32, 0.32):
        c.circle(u, 0.06, 0.045, dark, lift=0.05)
    c.circle(0.0, 0.30, 0.07, c.col((0.98, 0.95, 0.85)), lift=0.05)
    c.circle(0.0, 0.30, 0.04, scale(col, 0.9), lift=0)


@prop("bouquet", aspect=0.9, place="table", nominal=0.4, category="events", words=("bouquets", "flowers", "floral", "florist", "rose", "roses", "gifting", "bunch"))
def bouquet(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    wrap = c.col((0.98, 0.88, 0.80))
    c.poly([(0, 0.0), (-0.30, 0.52), (0.30, 0.52)], wrap, lift=0.1)
    c.poly([(0, 0.0), (0.12, 0.52), (0.30, 0.52)], scale(wrap, 0.88), lift=0.0)
    cols = [(0.93, 0.30, 0.42), (0.98, 0.70, 0.20), (0.85, 0.40, 0.80), (1.0, 0.55, 0.65), (0.95, 0.25, 0.30)]
    pos = [(-0.22, 0.62), (0.0, 0.76), (0.22, 0.62), (-0.10, 0.84), (0.12, 0.88), (0.0, 0.56)]
    for k, (u, v) in enumerate(pos):
        col = c.pick(color, cols[k % len(cols)]) if (k == 0 and color is not None) else c.col(cols[k % len(cols)])
        for j in range(6):
            a = math.radians(j * 60 + 10 * k)
            c.circle(u + 0.075 * math.cos(a), v + 0.075 * math.sin(a), 0.062, col, lift=0.1)
        c.circle(u, v, 0.05, c.col((1.0, 0.85, 0.35)), lift=0.1)
    c.circle(-0.28, 0.54, 0.07, c.col((0.30, 0.65, 0.40)), lift=0.1)
    c.circle(0.30, 0.56, 0.07, c.col((0.30, 0.65, 0.40)), lift=0.1)
    c.poly([(0, 0.46), (-0.12, 0.40), (-0.14, 0.52), (0, 0.46), (0.12, 0.52), (0.14, 0.40)], c.col((0.92, 0.30, 0.45)), lift=0.1)


@prop("chat", aspect=1.3, place="table", nominal=0.28, fill=0.8, category="web", words=("message", "messages", "support", "helpdesk", "conversation", "contact", "feedback", "talk", "speak", "speaking", "communication", "enquiry", "inquiry", "query", "queries", "whatsapp", "telegram", "email", "mail"))
def chat(c, color):
    blue = c.pick(color, (0.25, 0.52, 0.95))
    c.shadow(0.03, 0.12, 1.1, 0.06)
    c.rect(0.12, 0.62, 0.86, 0.50, c.col((1.0, 1.0, 1.0)), r=0.12, lift=0.04)
    c.poly([(0.40, 0.38), (0.55, 0.38), (0.52, 0.22)], c.col((1.0, 1.0, 1.0)), lift=0.02)
    for k, wd in enumerate((0.55, 0.42)):
        c.rect(-0.02 + wd / 2 - 0.1 + 0.12, 0.70 - k * 0.14, wd, 0.045, c.col((0.72, 0.76, 0.86)), r=0.02, lift=0)
    c.rect(-0.14, 0.34, 0.74, 0.40, blue, r=0.11, lift=0.14)
    c.poly([(-0.40, 0.16), (-0.30, 0.16), (-0.34, 0.34)], blue, lift=0.1)
    for k in range(3):
        c.circle(-0.30 + k * 0.17, 0.34, 0.04, c.col((1, 1, 1)), lift=0)


@prop("review", aspect=1.5, place="table", nominal=0.28, fill=0.66, category="web", words=("reviews", "rating", "ratings", "testimonial", "testimonials", "stars", "trust", "trusted", "satisfaction", "happy", "customerreview"))
def review(c, color):
    c.shadow(0.02, 0.08, 1.35, 0.06)
    c.rect(0, 0.42, 1.30, 0.80, c.col((1.0, 1.0, 1.0)), r=0.07, lift=0.03)
    gold = c.pick(color, (1.0, 0.76, 0.18))
    for k in range(5):
        _star(c, -0.36 + k * 0.18, 0.60, 0.075, gold if k < 5 else c.col((0.85, 0.87, 0.9)))
    for k, wd in enumerate((0.95, 0.80, 0.55)):
        c.rect(-0.60 + wd / 2, 0.42 - k * 0.09, wd, 0.035, c.col((0.78, 0.8, 0.88)), r=0.015, lift=0)
    c.circle(-0.48, 0.18, 0.075, c.col((0.45, 0.62, 0.90)), lift=0.1)
    c.rect(-0.20, 0.20, 0.34, 0.035, c.col((0.55, 0.58, 0.68)), r=0.015, lift=0)
    c.rect(-0.26, 0.14, 0.22, 0.025, c.col((0.8, 0.82, 0.88)), r=0.012, lift=0)


@prop("shield", aspect=0.86, place="table", nominal=0.32, category="web", words=("security", "secure", "insurance", "protection", "protect", "safe", "safety", "privacy", "guarantee", "warranty", "antivirus", "verified", "quality", "secured", "reliable"))
def shield(c, color):
    c.shadow(0.02, 0.0, 0.7, 0.06)
    col = c.pick(color, (0.22, 0.50, 0.90))
    pts = [(-0.40, 0.88), (0.0, 0.98), (0.40, 0.88), (0.38, 0.50), (0.22, 0.24), (0.0, 0.08), (-0.22, 0.24), (-0.38, 0.50)]
    c.poly(pts, col, lift=0.16)
    c.poly([(0.0, 0.98), (0.40, 0.88), (0.38, 0.50), (0.22, 0.24), (0.0, 0.08)], scale(col, 0.88), lift=0.0, alpha=0.55)
    c.path([(-0.17, 0.52), (-0.05, 0.38), (0.19, 0.68)], 0.085, c.col((1.0, 1.0, 1.0)), smooth=False)


@prop("coins", aspect=1.3, place="table", nominal=0.24, fill=0.65, category="web", words=("money", "cash", "coin", "payment", "payments", "bank", "banking", "loan", "savings", "wallet", "budget", "dollar", "rupee", "euro", "pound", "pricing", "fees", "fee", "cost"))
def coins(c, color):
    c.shadow(0.0, 0.03, 1.3, 0.08)
    gold = c.pick(color, (0.98, 0.78, 0.22))
    for u, n in ((-0.38, 3), (0.0, 5), (0.38, 2)):
        for k in range(n):
            v = 0.06 + k * 0.085
            c.ellipse(u, v, 0.22, 0.065, scale(gold, 0.82), lift=0.12)
            c.rect(u, v + 0.03, 0.44, 0.06, scale(gold, 0.9), lift=0.12)
            c.ellipse(u, v + 0.06, 0.22, 0.065, gold, lift=0.14)
    c.ellipse(0.0, 0.06 + 5 * 0.085 + 0.01, 0.15, 0.04, scale(gold, 0.9), lift=0.0)
    c.ellipse(-0.38, 0.06 + 3 * 0.085, 0.15, 0.04, scale(gold, 0.9), lift=0.0)


@prop("pin", aspect=0.62, place="ground", nominal=0.32, category="web", words=("location", "map", "address", "locations", "directions", "gps", "nearby", "navigation", "pins", "visit", "branch", "branches", "near", "local"))
def pin(c, color):
    c.shadow(0.0, 0.01, 0.4, 0.06)
    col = c.pick(color, (0.92, 0.25, 0.30))
    c.poly([(-0.30, 0.66), (0.30, 0.66), (0.0, 0.04)], col, lift=0.14)
    c.circle(0, 0.68, 0.30, col, lift=0.14)
    c.circle(0, 0.68, 0.13, c.col((1.0, 1.0, 1.0)), lift=0.04)
    c.ellipse(-0.1, 0.80, 0.07, 0.04, WHITE, angle=30, lift=0, alpha=0.4)


@prop("tent", aspect=1.5, place="ground", nominal=0.3, fill=0.8, category="travel", words=("camping", "camp", "campsite", "campfire", "trekking", "hiking", "outdoors", "glamping", "adventure", "mountaineering"))
def tent(c, color):
    c.shadow(0.0, 0.01, 1.7, 0.07)
    col = c.pick(color, (0.95, 0.52, 0.20))
    c.poly([(-0.78, 0.02), (0.0, 0.88), (0.78, 0.02)], col, lift=0.14)
    c.poly([(0.0, 0.88), (0.78, 0.02), (0.30, 0.02)], scale(col, 0.82), lift=0.0, alpha=0.7)
    c.poly([(-0.24, 0.02), (0.0, 0.52), (0.24, 0.02)], c.col((0.20, 0.17, 0.22)), lift=0.0)
    c.poly([(-0.24, 0.02), (0.0, 0.52), (-0.04, 0.02)], scale(col, 1.12), lift=0.08)
    c.poly([(0.24, 0.02), (0.0, 0.52), (0.04, 0.02)], scale(col, 0.9), lift=0.08)
    c.line(0, 0.88, 0, 1.02, 0.014, c.col((0.45, 0.30, 0.20)))
    c.poly([(0.0, 1.02), (0.20, 0.97), (0.0, 0.92)], c.col((0.90, 0.2, 0.25)), lift=0.1)
    for sgn in (-1, 1):
        c.line(sgn * 0.60, 0.20, sgn * 0.92, 0.02, 0.008, c.col((0.85, 0.85, 0.88)))
        c.circle(sgn * 0.93, 0.02, 0.012, c.col((0.4, 0.4, 0.45)), lift=0)


@prop("gradcap", aspect=1.4, place="table", nominal=0.28, fill=0.75, category="education", words=("mortarboard", "convocation"))
def gradcap(c, color):
    c.shadow(0.0, 0.02, 1.3, 0.08)
    navy = c.pick(color, (0.13, 0.17, 0.34))
    c.poly([(-0.30, 0.42), (0.30, 0.42), (0.28, 0.20), (0.0, 0.12), (-0.28, 0.20)], scale(navy, 0.9), lift=0.12)
    c.poly([(-0.72, 0.50), (0.0, 0.78), (0.72, 0.50), (0.0, 0.30)], navy, lift=0.16)
    c.poly([(0.0, 0.78), (0.72, 0.50), (0.0, 0.30)], scale(navy, 0.82), lift=0.0, alpha=0.55)
    c.circle(0.0, 0.54, 0.035, c.col((0.95, 0.78, 0.2)), lift=0.1)
    c.path([(0.0, 0.54), (0.50, 0.52), (0.62, 0.40), (0.62, 0.20)], 0.015, c.col((0.95, 0.78, 0.2)))
    c.rect(0.62, 0.15, 0.04, 0.10, c.col((0.95, 0.78, 0.2)), r=0.01, lift=0.1)
