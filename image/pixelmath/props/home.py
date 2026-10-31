"""Furniture and interior props."""
import math

from .core import WHITE, mix, prop, scale


@prop("sofa", aspect=1.7, place="ground", nominal=0.26, fill=0.66, category="home",
      words=("couch", "sofas", "furniture", "livingroom", "lounge", "upholstery"))
def sofa(c, color):
    c.shadow(0.0, 0.02, 1.7, 0.09)
    col = c.pick(color, (0.30, 0.50, 0.62))
    c.rect(0, 0.56, 1.30, 0.50, scale(col, 0.88), r=0.12, lift=0.12)                      # back
    c.rect(0, 0.32, 1.12, 0.22, col, r=0.07, lift=0.14)                                   # seat
    c.line(0, 0.44, 0, 0.20, 0.012, scale(col, 0.7))
    for sgn in (-1, 1):
        c.rect(sgn * 0.62, 0.36, 0.20, 0.44, scale(col, 0.95), r=0.09, lift=0.12)         # arms
        c.rect(sgn * 0.52, 0.04, 0.05, 0.08, c.col((0.40, 0.28, 0.18)), lift=0)           # feet
    c.rect(-0.30, 0.58, 0.42, 0.26, mix(col, WHITE, 0.25), r=0.07, lift=0.1)              # cushions
    c.rect(0.30, 0.58, 0.42, 0.26, c.col((0.95, 0.75, 0.30)), r=0.07, lift=0.1)


@prop("lamp", aspect=0.5, place="ground", nominal=0.4, category="home", words=("lamps", "lighting", "light", "lights", "chandelier", "lantern"))
def lamp(c, color):
    shade = c.pick(color, (0.98, 0.84, 0.50))
    c.glow(0, 0.78, 0.9, c.col((1.0, 0.85, 0.5)), 0.28)
    c.ellipse(0, 0.015, 0.20, 0.025, c.col((0.28, 0.28, 0.33)), lift=0.1)
    c.rect(0, 0.40, 0.025, 0.78, c.col((0.35, 0.35, 0.40)), lift=0.1)
    c.poly([(-0.14, 0.98), (0.14, 0.98), (0.24, 0.66), (-0.24, 0.66)], shade, lift=0.14)
    c.ellipse(0, 0.66, 0.24, 0.03, scale(shade, 0.85), lift=0.0)


@prop("plant", aspect=0.8, place="ground", nominal=0.3, category="home", words=("plants", "houseplant", "pot", "nature", "leaf", "leaves", "greenery", "eco", "organic", "natural", "herbal", "ayurveda", "garden"))
def plant(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    leaf = c.pick(color, (0.22, 0.62, 0.34))
    for ang, u, v, a, b, k in ((70, -0.02, 0.62, 0.28, 0.085, 0.9), (110, 0.02, 0.62, 0.28, 0.085, 1.0), (30, 0.12, 0.54, 0.26, 0.08, 0.85), (150, -0.12, 0.54, 0.26, 0.08, 0.95),
                               (90, 0.0, 0.76, 0.26, 0.08, 1.1), (15, 0.18, 0.44, 0.2, 0.07, 0.8), (165, -0.18, 0.44, 0.2, 0.07, 0.9)):
        du, dv = a * math.cos(math.radians(ang)), a * math.sin(math.radians(ang))
        c.line(0, 0.30, u * 0.5, 0.40, 0.012, scale(leaf, 0.6))
        c.ellipse(u + du * 0.55, v + dv * 0.55 - 0.02, a, b, scale(leaf, k), angle=ang, lift=0.14)
    pot = c.col((0.82, 0.45, 0.30))
    c.poly([(-0.20, 0.32), (0.20, 0.32), (0.14, 0.02), (-0.14, 0.02)], pot, lift=0.14)
    c.rect(0, 0.325, 0.44, 0.06, scale(pot, 1.1), r=0.015, lift=0.1)


@prop("bed", aspect=1.8, place="ground", nominal=0.24, fill=0.62, category="home", words=("bedroom", "beds", "mattress", "sleep", "hotelroom", "room", "rooms", "bedding", "pillow"))
def bed(c, color):
    c.shadow(0.0, 0.02, 1.8, 0.08)
    blanket = c.pick(color, (0.40, 0.62, 0.85))
    wood = c.col((0.55, 0.38, 0.25))
    c.rect(-0.82, 0.38, 0.10, 0.76, wood, r=0.03, lift=0.12)
    c.rect(0.82, 0.22, 0.08, 0.44, wood, r=0.02, lift=0.12)
    c.rect(0, 0.32, 1.64, 0.26, c.col((0.97, 0.97, 0.99)), r=0.05, lift=0.08)
    c.rect(0.12, 0.38, 1.36, 0.20, blanket, r=0.05, lift=0.12)
    c.rect(0.36, 0.38, 0.06, 0.20, mix(blanket, WHITE, 0.4), lift=0)
    c.ellipse(-0.58, 0.52, 0.24, 0.10, c.col((1.0, 1.0, 1.0)), lift=0.1)
    c.ellipse(-0.58, 0.52, 0.16, 0.05, c.col((0.9, 0.92, 0.96)), lift=0)
    c.rect(0, 0.10, 1.64, 0.06, wood, lift=0.1)


@prop("chair", aspect=0.62, place="ground", nominal=0.3, category="home", words=("chairs", "seat", "seating", "stool", "armchair", "furnishing"))
def chair(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    col = c.pick(color, (0.88, 0.58, 0.25))
    wood = c.col((0.45, 0.30, 0.20))
    for u in (-0.20, 0.20):
        c.rect(u, 0.20, 0.04, 0.38, wood, lift=0.1)
    c.rect(-0.20, 0.64, 0.04, 0.60, wood, lift=0.1)
    c.rect(0, 0.42, 0.50, 0.08, col, r=0.03, lift=0.14)
    c.rect(-0.15, 0.72, 0.26, 0.32, col, r=0.05, lift=0.14)
    c.rect(-0.15, 0.72, 0.18, 0.20, scale(col, 0.88), r=0.04, lift=0.05)


@prop("bookshelf", aspect=0.85, place="ground", nominal=0.4, category="home", words=("shelf", "shelves", "bookcase", "storage", "cupboard", "wardrobe", "cabinet"))
def bookshelf(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.06)
    wood = c.pick(color, (0.55, 0.38, 0.25))
    c.rect(0, 0.5, 0.80, 0.98, scale(wood, 0.7), r=0.02, lift=0.05)
    c.rect(0, 0.5, 0.72, 0.90, scale(wood, 0.5), lift=0.0)
    cols = [(0.85, 0.25, 0.30), (0.25, 0.50, 0.85), (0.95, 0.75, 0.25), (0.30, 0.70, 0.45), (0.60, 0.35, 0.75), (0.95, 0.5, 0.25)]
    for row in range(3):
        v0 = 0.08 + row * 0.30
        c.rect(0, v0, 0.76, 0.03, wood, lift=0.1)
        u = -0.32
        k = row * 2
        while u < 0.30:
            wd = 0.05 + 0.025 * ((k * 7) % 3)
            ht = 0.18 + 0.05 * ((k * 5) % 4)
            c.rect(u + wd / 2, v0 + 0.015 + ht / 2, wd, ht, c.col(cols[k % len(cols)]), r=0.004, lift=0.12)
            u += wd + 0.006
            k += 1
    c.rect(0, 0.985, 0.84, 0.03, wood, lift=0.1)
