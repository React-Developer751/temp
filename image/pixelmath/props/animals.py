"""Props: animals (pets and farm animals), flat illustration, side view facing right unless noted."""
import math

from .core import WHITE, mix, prop, scale  # noqa: F401

INK = (0.14, 0.11, 0.11)


def _eye(c, u, v, r, white=True):
    if white:
        c.circle(u, v, r, c.col((1.0, 1.0, 1.0)), lift=0)
    c.circle(u + r * 0.12, v, r * 0.66, c.col(INK), lift=0)
    c.circle(u + r * 0.30, v + r * 0.30, r * 0.22, c.col((1.0, 1.0, 1.0)), lift=0)


def _leg(c, u, v0, v1, w, color, hoof=None, hoof_h=0.05):
    """Rounded leg from base v0 to top v1, with an optional hoof."""
    c.rect(u, (v0 + v1) / 2.0, w, v1 - v0, color, r=w * 0.42)
    if hoof is not None:
        c.rect(u, v0 + hoof_h / 2.0, w * 1.02, hoof_h, hoof, r=hoof_h * 0.45, lift=0.05)


# ------------------------------------------------------------------ pets
@prop("dog", aspect=1.5, place="ground", nominal=0.34, fill=0.85, category="pets",
      words=("puppy", "doggy", "pooch", "hound", "kutta"))
def dog(c, color):
    c = c.sub(-0.10, 0.0, 1.0)
    c.shadow(0.02, 0.01, 1.2, 0.09)
    fur = c.pick(color, (0.80, 0.54, 0.29))
    dark = scale(fur, 0.74)
    light = c.col((0.99, 0.91, 0.78))
    ear = scale(fur, 0.62)
    # curled tail behind the body
    c.path([(-0.36, 0.56), (-0.50, 0.64), (-0.55, 0.79), (-0.46, 0.90), (-0.37, 0.84)], 0.085, fur)
    # far legs
    for u in (-0.20, 0.34):
        _leg(c, u, 0.03, 0.46, 0.115, dark)
        c.ellipse(u + 0.015, 0.03, 0.075, 0.035, scale(dark, 1.25), lift=0.05)
    # body
    c.ellipse(-0.03, 0.51, 0.43, 0.21, fur, lift=0.14)
    c.ellipse(-0.30, 0.49, 0.17, 0.19, scale(fur, 1.05), lift=0.1)
    c.ellipse(0.02, 0.40, 0.30, 0.09, light, lift=0.05, alpha=0.9)               # belly
    # near legs
    for u in (-0.33, 0.22):
        _leg(c, u, 0.03, 0.48, 0.125, fur)
        c.ellipse(u + 0.015, 0.03, 0.08, 0.037, light, lift=0.05)
    # neck and head
    c.ellipse(0.29, 0.62, 0.13, 0.19, fur, angle=-25, lift=0.1)
    c.circle(0.42, 0.74, 0.19, fur, lift=0.12)
    c.ellipse(0.60, 0.67, 0.145, 0.095, light, angle=-8, lift=0.08)                # snout
    c.ellipse(0.59, 0.61, 0.07, 0.022, c.col((0.93, 0.45, 0.50)), lift=0)      # tongue
    c.ellipse(0.61, 0.63, 0.10, 0.012, c.col(INK), lift=0, alpha=0.8)           # mouth
    c.circle(0.725, 0.71, 0.045, c.col((0.12, 0.10, 0.10)), lift=0.2)            # nose
    c.circle(0.715, 0.725, 0.012, c.col((1.0, 1.0, 1.0)), lift=0, alpha=0.7)
    # collar with tag
    c.path([(0.20, 0.58), (0.29, 0.555), (0.37, 0.60)], 0.06, c.col((0.85, 0.18, 0.20)), smooth=False)
    c.circle(0.29, 0.51, 0.03, c.col((0.98, 0.80, 0.22)), lift=0.1)
    # floppy ear and eye
    c.ellipse(0.33, 0.69, 0.075, 0.16, ear, angle=14, lift=0.12)
    _eye(c, 0.50, 0.775, 0.04)
    c.path([(0.46, 0.83), (0.52, 0.845)], 0.015, scale(fur, 0.6), smooth=False)


@prop("cat", aspect=0.9, place="ground", nominal=0.32, fill=1.0, category="pets",
      words=("kitten", "kitty", "kitties", "feline", "billi", "meow"))
def cat(c, color):
    c.shadow(0.03, 0.01, 0.95, 0.09)
    fur = c.pick(color, (0.93, 0.62, 0.28))
    dark = scale(fur, 0.72)
    white = c.col((0.99, 0.96, 0.92))
    pink = c.col((0.96, 0.60, 0.65))
    # curled tail
    c.path([(0.17, 0.09), (0.38, 0.05), (0.53, 0.16), (0.53, 0.34), (0.43, 0.43)], 0.095, fur)
    c.circle(0.43, 0.43, 0.047, white, lift=0.05)
    for v in (0.20, 0.30):
        c.line(0.485, v, 0.575, v + 0.02, 0.025, dark, alpha=0.75)
    # body, belly, haunch
    c.ellipse(0.0, 0.31, 0.29, 0.31, fur, lift=0.14)
    c.ellipse(0.0, 0.27, 0.15, 0.21, white, lift=0.04)
    c.ellipse(-0.20, 0.14, 0.12, 0.13, scale(fur, 1.06), lift=0.1)
    # front legs and paws
    for s in (-1, 1):
        c.rect(s * 0.085, 0.16, 0.105, 0.30, fur, r=0.05)
        c.ellipse(s * 0.085, 0.03, 0.065, 0.034, white, lift=0.05)
    # head
    c.poly([(-0.215, 0.76), (-0.235, 1.0), (-0.065, 0.89)], fur, lift=0.1)
    c.poly([(0.215, 0.76), (0.235, 1.0), (0.065, 0.89)], fur, lift=0.1)
    c.poly([(-0.19, 0.80), (-0.205, 0.94), (-0.09, 0.87)], pink, lift=0.05)
    c.poly([(0.19, 0.80), (0.205, 0.94), (0.09, 0.87)], pink, lift=0.05)
    c.ellipse(0.0, 0.69, 0.255, 0.215, fur, lift=0.14)
    for dx in (-0.06, 0.0, 0.06):                                              # forehead stripes
        c.line(dx, 0.87, dx * 1.1, 0.80, 0.022, dark, alpha=0.8)
    c.ellipse(0.0, 0.62, 0.13, 0.085, white, lift=0.03)                        # muzzle
    for s in (-1, 1):
        c.ellipse(s * 0.105, 0.725, 0.058, 0.062, c.col((0.55, 0.82, 0.35)), lift=0.1)
        c.ellipse(s * 0.105, 0.725, 0.016, 0.052, c.col(INK), lift=0)
        c.circle(s * 0.12, 0.745, 0.012, c.col((1, 1, 1)), lift=0)
    c.poly([(-0.032, 0.655), (0.032, 0.655), (0.0, 0.62)], pink, lift=0.05)    # nose
    c.arc(-0.03, 0.62, 0.03, 200, 340, 0.012, c.col(INK))
    c.arc(0.03, 0.62, 0.03, 200, 340, 0.012, c.col(INK))
    for s in (-1, 1):                                                          # whiskers
        for dv, dv2 in ((0.015, 0.045), (-0.005, -0.005), (-0.025, -0.05)):
            c.line(s * 0.10, 0.625 + dv, s * 0.30, 0.625 + dv2, 0.009, c.col((0.30, 0.25, 0.25)), alpha=0.9)


@prop("rabbit", aspect=0.9, place="ground", nominal=0.30, fill=1.0, category="pets",
      words=("bunny", "hare", "rabbits", "khargosh"))
def rabbit(c, color):
    c.shadow(0.0, 0.01, 0.95, 0.08)
    fur = c.pick(color, (0.80, 0.70, 0.60))
    white = c.col((0.99, 0.97, 0.95))
    pink = c.col((0.96, 0.66, 0.70))
    # fluffy tail
    for du, dv, r in ((-0.37, 0.24, 0.085), (-0.40, 0.29, 0.06), (-0.34, 0.30, 0.06), (-0.40, 0.20, 0.05)):
        c.circle(du, dv, r, white, lift=0.08)
    # far ear, body, haunch
    c.ellipse(0.25, 0.83, 0.058, 0.20, scale(fur, 0.85), angle=-14, lift=0.1)
    c.ellipse(-0.02, 0.29, 0.31, 0.27, fur, lift=0.14)
    c.ellipse(-0.10, 0.20, 0.22, 0.17, scale(fur, 1.06), lift=0.1)
    c.ellipse(0.12, 0.31, 0.13, 0.18, white, angle=-10, lift=0.05, alpha=0.9)   # chest
    # feet
    c.ellipse(-0.02, 0.035, 0.17, 0.045, white, lift=0.05)
    c.ellipse(0.19, 0.035, 0.085, 0.04, white, lift=0.05)
    c.path([(0.17, 0.07), (0.19, 0.18)], 0.07, fur, smooth=False)
    # head, near ear
    c.ellipse(0.20, 0.57, 0.18, 0.165, fur, lift=0.12)
    c.ellipse(0.17, 0.87, 0.06, 0.22, fur, angle=8, lift=0.1)
    c.ellipse(0.175, 0.87, 0.03, 0.17, pink, angle=8, lift=0.03)
    c.ellipse(0.31, 0.52, 0.11, 0.085, white, lift=0.04)                         # muzzle
    c.circle(0.405, 0.555, 0.022, pink, lift=0.05)
    c.line(0.405, 0.535, 0.395, 0.505, 0.01, c.col((0.45, 0.3, 0.3)))
    c.arc(0.375, 0.505, 0.03, 200, 330, 0.01, c.col((0.45, 0.3, 0.3)))
    _eye(c, 0.27, 0.62, 0.037, white=False)
    c.ellipse(0.22, 0.52, 0.04, 0.025, pink, lift=0, alpha=0.5)                  # blush


@prop("fish", aspect=1.1, place="ground", nominal=0.28, fill=1.0, category="pets",
      words=("goldfish", "aquarium", "fishes", "machhli", "tropical"))
def fish(c, color):
    c.shadow(0.0, 0.03, 0.85, 0.07, alpha=0.18)
    body = c.pick(color, (0.97, 0.55, 0.16))
    fin = scale(body, 0.88)
    hi = scale(body, 1.18)
    cy = 0.50
    # tail, dorsal and lower fins
    c.poly([(-0.20, cy), (-0.55, cy + 0.27), (-0.49, cy + 0.04), (-0.58, cy - 0.04), (-0.50, cy - 0.06),
            (-0.55, cy - 0.28)], fin, lift=0.12)
    c.poly([(-0.16, cy + 0.17), (-0.02, cy + 0.40), (0.14, cy + 0.34), (0.20, cy + 0.20)], fin, lift=0.12)
    c.poly([(-0.02, cy - 0.20), (0.04, cy - 0.37), (0.17, cy - 0.20)], fin, lift=0.12)
    # body
    c.ellipse(0.03, cy, 0.40, 0.27, body, lift=0.16)
    c.ellipse(0.0, cy - 0.12, 0.30, 0.10, hi, lift=0.0, alpha=0.5)              # belly
    # scales
    sc = scale(body, 0.80)
    for row, v in enumerate((cy + 0.10, cy, cy - 0.10)):
        for k in range(4):
            u = -0.20 + k * 0.10 + (0.05 if row % 2 else 0.0)
            if u < 0.10:
                c.arc(u, v, 0.05, -80, 80, 0.013, sc, alpha=0.9)
    # side fin, gill, mouth, eye
    c.ellipse(0.02, cy - 0.07, 0.10, 0.045, fin, angle=-25, lift=0.08)
    c.arc(0.30, cy, 0.14, 120, 240, 0.016, scale(body, 0.7), ry=0.21)
    c.arc(0.405, cy - 0.04, 0.035, 200, 320, 0.014, c.col((0.45, 0.18, 0.1)))
    _eye(c, 0.27, cy + 0.07, 0.055)
    # bubbles
    for u, v, r in ((0.50, 0.90, 0.04), (0.58, 1.03, 0.028), (0.46, 1.08, 0.022)):
        c.circle(u, v, r, c.col((0.75, 0.90, 1.0)), lift=0, alpha=0.45)
        c.ring(u, v, r, 0.012, c.col((0.95, 0.99, 1.0)), alpha=0.9)
        c.circle(u - r * 0.3, v + r * 0.3, r * 0.2, c.col((1, 1, 1)), lift=0, alpha=0.9)


@prop("parrot", aspect=0.85, place="ground", nominal=0.34, fill=1.0, category="pets",
      words=("macaw", "parakeet", "cockatoo", "tota", "budgie"))
def parrot(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.07)
    body = c.pick(color, (0.88, 0.20, 0.17))
    blue = c.col((0.18, 0.45, 0.85))
    yellow = c.col((0.98, 0.80, 0.20))
    wood = c.col((0.50, 0.33, 0.20))
    # branch with leaves
    c.path([(-0.42, 0.115), (-0.1, 0.105), (0.25, 0.12), (0.46, 0.15)], 0.075, wood)
    c.ellipse(0.38, 0.22, 0.08, 0.035, c.col((0.30, 0.65, 0.28)), angle=35, lift=0.1)
    c.ellipse(-0.36, 0.19, 0.08, 0.035, c.col((0.30, 0.65, 0.28)), angle=-30, lift=0.1)
    # long tail
    c.ellipse(-0.08, 0.20, 0.052, 0.27, blue, angle=-9, lift=0.1)
    c.ellipse(-0.16, 0.22, 0.05, 0.25, c.col((0.93, 0.35, 0.12)), angle=-14, lift=0.1)
    c.ellipse(-0.01, 0.22, 0.05, 0.24, yellow, angle=-3, lift=0.1)
    # feet
    for u in (0.0, 0.08):
        c.line(u, 0.20, u, 0.14, 0.03, c.col((0.78, 0.60, 0.40)))
        c.ellipse(u + 0.01, 0.145, 0.04, 0.02, c.col((0.78, 0.60, 0.40)), lift=0)
    # body, belly, wing
    c.ellipse(0.02, 0.52, 0.22, 0.34, body, angle=-8, lift=0.14)
    c.ellipse(0.10, 0.48, 0.10, 0.22, scale(body, 1.12), angle=-8, lift=0.04, alpha=0.8)
    c.ellipse(-0.07, 0.48, 0.13, 0.27, blue, angle=-8, lift=0.12)
    c.ellipse(-0.045, 0.40, 0.085, 0.10, yellow, angle=-8, lift=0.05)
    c.ellipse(-0.08, 0.60, 0.07, 0.10, c.col((0.12, 0.55, 0.40)), angle=-8, lift=0.05)
    # head and face
    c.circle(0.08, 0.80, 0.16, body, lift=0.12)
    c.ellipse(0.14, 0.795, 0.095, 0.085, c.col((0.99, 0.96, 0.92)), lift=0.03)
    _eye(c, 0.13, 0.81, 0.04, white=False)
    # curved beak
    beak = c.col((0.98, 0.84, 0.50))
    c.poly([(0.17, 0.90), (0.27, 0.895), (0.34, 0.83), (0.325, 0.73), (0.285, 0.69), (0.28, 0.76), (0.235, 0.80),
            (0.17, 0.80)], beak, lift=0.1)
    c.poly([(0.235, 0.795), (0.285, 0.76), (0.28, 0.69), (0.255, 0.70), (0.215, 0.75)], c.col((0.20, 0.17, 0.17)), lift=0.1)
    c.ellipse(0.04, 0.92, 0.055, 0.03, scale(body, 1.1), angle=40, lift=0.0)


# ------------------------------------------------------------------ farm
@prop("cow", aspect=1.45, place="ground", nominal=0.38, fill=0.92, category="farm",
      words=("cattle", "dairy", "calf", "bull", "gaay", "moo"))
def cow(c, color):
    c = c.sub(-0.06, 0.0, 1.0)
    c.shadow(0.02, 0.01, 1.35, 0.09)
    hide = c.pick(color, (0.97, 0.96, 0.94))
    patch = c.col((0.20, 0.17, 0.17))
    pink = c.col((0.97, 0.70, 0.72))
    hoof = c.col((0.25, 0.20, 0.20))
    far = scale(hide, 0.82)
    # tail
    c.path([(-0.52, 0.70), (-0.60, 0.58), (-0.60, 0.40)], 0.035, patch, smooth=False)
    c.ellipse(-0.60, 0.33, 0.045, 0.085, patch, lift=0.1)
    # far legs
    for u in (-0.24, 0.34):
        _leg(c, u, 0.02, 0.45, 0.14, far, hoof)
    # udder
    c.ellipse(-0.13, 0.35, 0.10, 0.07, pink, lift=0.08)
    for u in (-0.17, -0.09):
        c.rect(u, 0.295, 0.03, 0.05, pink, r=0.015, lift=0.05)
    # body
    c.rect(-0.04, 0.58, 1.02, 0.44, hide, r=0.20, lift=0.14)
    c.ellipse(-0.30, 0.64, 0.13, 0.10, patch, angle=12, lift=0.08)
    c.ellipse(0.02, 0.50, 0.11, 0.09, patch, angle=-10, lift=0.08)
    c.ellipse(-0.08, 0.72, 0.09, 0.055, patch, lift=0.08)
    c.ellipse(0.24, 0.62, 0.08, 0.10, patch, angle=-20, lift=0.08)
    # near legs
    for u in (-0.36, 0.22):
        _leg(c, u, 0.02, 0.47, 0.15, hide, hoof)
    # head and neck
    c.ellipse(0.38, 0.68, 0.20, 0.22, hide, angle=-30, lift=0.1)
    c.ellipse(0.58, 0.66, 0.17, 0.155, hide, angle=-28, lift=0.12)
    c.ellipse(0.69, 0.58, 0.12, 0.10, pink, angle=-25, lift=0.08)                # muzzle
    for du in (-0.04, 0.05):
        c.ellipse(0.70 + du, 0.595 - du * 0.4, 0.014, 0.022, scale(pink, 0.6), lift=0, angle=-20)
    c.ellipse(0.575, 0.745, 0.075, 0.06, patch, angle=-20, lift=0.06)             # eye patch
    _eye(c, 0.595, 0.745, 0.033)
    cream = c.col((0.98, 0.93, 0.78))
    c.poly([(0.455, 0.78), (0.43, 0.95), (0.53, 0.82)], cream, lift=0.1)           # horns
    c.poly([(0.58, 0.80), (0.63, 0.95), (0.69, 0.80)], cream, lift=0.1)
    c.ellipse(0.40, 0.76, 0.115, 0.05, patch, angle=25, lift=0.08)                # ear
    c.ellipse(0.40, 0.76, 0.07, 0.025, pink, angle=25, lift=0, alpha=0.7)


@prop("sheep", aspect=1.05, place="ground", nominal=0.30, fill=0.82, category="farm",
      words=("lamb", "ram", "mutton", "wool", "bhed", "baa"))
def sheep(c, color):
    c.shadow(0.0, 0.01, 1.0, 0.08)
    wool = c.pick(color, (0.96, 0.94, 0.90))
    face = c.col((0.30, 0.26, 0.25))
    dark = c.col((0.24, 0.21, 0.21))
    # legs
    for u in (-0.26, -0.14, 0.10, 0.22):
        c.rect(u, 0.14, 0.075, 0.28, dark if u in (-0.26, 0.10) else face, r=0.03, lift=0.1)
        c.rect(u, 0.03, 0.085, 0.045, scale(face, 0.7), r=0.02, lift=0.0)
    # fluffy wool: overlapping circles, back to front
    blobs = [(-0.30, 0.52, 0.17), (-0.18, 0.64, 0.19), (0.0, 0.69, 0.20), (0.17, 0.64, 0.18), (0.27, 0.52, 0.16),
             (-0.34, 0.40, 0.15), (-0.20, 0.34, 0.17), (0.0, 0.32, 0.18), (0.18, 0.34, 0.16), (0.28, 0.40, 0.14),
             (-0.12, 0.52, 0.22), (0.08, 0.52, 0.22)]
    for u, v, r in blobs:
        c.circle(u, v, r, wool, lift=0.12)
    for u, v, r in ((-0.22, 0.60, 0.08), (0.04, 0.62, 0.09), (0.18, 0.47, 0.08), (-0.1, 0.40, 0.08)):
        c.circle(u, v, r, scale(wool, 1.04), lift=0.06, alpha=0.6)
    # head
    c.ellipse(0.40, 0.55, 0.14, 0.165, face, angle=-15, lift=0.12)
    c.circle(0.34, 0.69, 0.10, wool, lift=0.1)
    c.circle(0.42, 0.72, 0.075, wool, lift=0.1)
    c.ellipse(0.27, 0.58, 0.10, 0.045, face, angle=-25, lift=0.1)                # ear
    _eye(c, 0.43, 0.59, 0.034)
    c.ellipse(0.50, 0.47, 0.045, 0.03, scale(face, 1.25), lift=0.05)            # nose
    c.arc(0.47, 0.47, 0.03, 200, 330, 0.01, scale(face, 0.6))


@prop("horse", aspect=1.35, place="ground", nominal=0.42, fill=1.0, category="farm",
      words=("pony", "stallion", "mare", "foal", "ghoda", "ghora", "neigh"))
def horse(c, color):
    c.shadow(0.0, 0.01, 1.3, 0.09)
    coat = c.pick(color, (0.62, 0.38, 0.20))
    mane = scale(coat, 0.45)
    hoof = c.col((0.22, 0.18, 0.17))
    far = scale(coat, 0.80)
    # tail
    c.path([(-0.46, 0.62), (-0.60, 0.56), (-0.66, 0.38), (-0.60, 0.20)], 0.11, mane)
    # far legs
    for u in (-0.26, 0.26):
        _leg(c, u, 0.0, 0.46, 0.10, far, hoof, 0.06)
    # body
    c.ellipse(-0.10, 0.52, 0.45, 0.21, coat, lift=0.14)
    c.circle(-0.38, 0.52, 0.19, coat, lift=0.12)
    # neck
    c.poly([(0.03, 0.36), (0.36, 0.45), (0.58, 0.88), (0.30, 0.96), (-0.02, 0.66)], coat, lift=0.12)
    # near legs
    for u in (-0.36, 0.17):
        _leg(c, u, 0.0, 0.46, 0.11, coat, hoof, 0.06)
    # mane
    c.path([(0.36, 0.99), (0.22, 0.88), (0.10, 0.76), (0.0, 0.64)], 0.085, mane)
    # head
    c.ellipse(0.57, 0.83, 0.21, 0.105, coat, angle=-38, lift=0.12)
    c.ellipse(0.71, 0.73, 0.09, 0.075, scale(coat, 0.72), angle=-38, lift=0.1)  # muzzle
    c.poly([(0.40, 0.92), (0.43, 1.05), (0.51, 0.94)], coat, lift=0.1)           # ears
    c.poly([(0.455, 0.93), (0.475, 1.01), (0.51, 0.94)], scale(coat, 0.8), lift=0.1)
    c.ellipse(0.585, 0.78, 0.012, 0.016, c.col(INK), lift=0)
    c.path([(0.48, 0.96), (0.44, 0.90)], 0.05, mane)                              # forelock
    _eye(c, 0.52, 0.865, 0.03, white=False)
    c.ellipse(0.715, 0.70, 0.012, 0.018, c.col(INK), lift=0, angle=-30)


@prop("chicken", aspect=0.95, place="ground", nominal=0.28, fill=0.95, category="farm",
      words=("hen", "rooster", "cock", "poultry", "chick", "murgi", "murga"))
def chicken(c, color):
    c.shadow(0.0, 0.01, 0.8, 0.07)
    body = c.pick(color, (0.98, 0.96, 0.92))
    red = c.col((0.90, 0.17, 0.17))
    orange = c.col((0.98, 0.65, 0.12))
    feather = c.col((0.22, 0.42, 0.40))
    # legs
    for u in (-0.04, 0.10):
        c.line(u, 0.17, u, 0.04, 0.03, orange)
        for du in (-0.07, 0.0, 0.07):
            c.line(u, 0.04, u + du + 0.03, 0.01, 0.022, orange)
    # tail feathers
    for ang, u, v, col in ((55, -0.37, 0.60, feather), (35, -0.40, 0.52, scale(feather, 1.2)),
                           (18, -0.40, 0.42, c.col((0.30, 0.5, 0.35)))):
        c.ellipse(u, v, 0.055, 0.20, col, angle=ang - 0, lift=0.1)
    # body, wing
    c.ellipse(-0.02, 0.38, 0.33, 0.25, body, angle=12, lift=0.14)
    c.ellipse(0.17, 0.52, 0.17, 0.22, body, angle=-8, lift=0.1)                   # chest and neck
    c.ellipse(-0.08, 0.40, 0.19, 0.125, scale(body, 0.90), angle=8, lift=0.12)
    c.arc(-0.08, 0.40, 0.14, 190, 330, 0.014, scale(body, 0.72), ry=0.08)
    c.arc(-0.06, 0.42, 0.08, 190, 330, 0.012, scale(body, 0.72), ry=0.05)
    # head
    c.circle(0.24, 0.73, 0.125, body, lift=0.12)
    for u, v, r in ((0.17, 0.85, 0.045), (0.235, 0.88, 0.055), (0.30, 0.85, 0.045)):  # comb
        c.circle(u, v, r, red, lift=0.1)
    c.ellipse(0.33, 0.625, 0.04, 0.065, red, lift=0.1)                            # wattle
    c.poly([(0.335, 0.765), (0.335, 0.695), (0.45, 0.725)], orange, lift=0.1)     # beak
    _eye(c, 0.285, 0.755, 0.032, white=False)


@prop("elephant", aspect=1.65, place="ground", nominal=0.42, fill=0.95, category="farm",
      words=("tusker", "jumbo", "hathi", "pachyderm"))
def elephant(c, color):
    c = c.sub(-0.14, 0.0, 1.0)
    c.shadow(0.0, 0.01, 1.4, 0.10)
    skin = c.pick(color, (0.63, 0.67, 0.74))
    far = scale(skin, 0.82)
    nail = c.col((0.93, 0.90, 0.85))
    # tail
    c.path([(-0.46, 0.62), (-0.56, 0.52), (-0.55, 0.38)], 0.035, scale(skin, 0.75), smooth=False)
    c.ellipse(-0.55, 0.34, 0.03, 0.05, scale(skin, 0.6), lift=0)
    # far legs
    for u in (-0.26, 0.26):
        _leg(c, u, 0.0, 0.50, 0.20, far)
        c.rect(u, 0.03, 0.18, 0.045, nail, r=0.02, lift=0.0)
    # body
    c.ellipse(-0.05, 0.62, 0.47, 0.33, skin, lift=0.15)
    # near legs
    for u in (-0.34, 0.16):
        _leg(c, u, 0.0, 0.52, 0.22, skin)
        c.rect(u, 0.03, 0.19, 0.045, nail, r=0.02, lift=0.0)
    # head, trunk
    c.circle(0.46, 0.68, 0.26, skin, lift=0.14)
    c.path([(0.62, 0.66), (0.72, 0.46), (0.73, 0.24), (0.80, 0.12), (0.90, 0.19)], 0.13, skin)
    for dv in (0.52, 0.40, 0.28):
        c.line(0.69, dv, 0.78, dv - 0.01, 0.012, scale(skin, 0.78), alpha=0.7)
    # tusk
    c.path([(0.60, 0.58), (0.68, 0.47), (0.77, 0.45)], 0.04, c.col((0.99, 0.97, 0.90)))
    # ear and eye
    c.ellipse(0.30, 0.70, 0.17, 0.25, scale(skin, 0.92), angle=8, lift=0.12)
    c.ellipse(0.31, 0.69, 0.115, 0.195, c.col((0.88, 0.66, 0.68)), angle=8, lift=0.05)
    _eye(c, 0.55, 0.74, 0.028, white=False)
