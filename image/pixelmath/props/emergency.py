"""Props: emergency services (ambulance, fire engine, police car, firefighter, police officer, hydrant, extinguisher)."""
import math  # noqa: F401

from .core import WHITE, mix, prop, scale  # noqa: F401
from .people import HAIR, SKIN, _face, _figure  # noqa: F401
from .vehicles import _wheel

RED_LIGHT = (0.95, 0.12, 0.14)
BLUE_LIGHT = (0.15, 0.40, 0.98)


def _arch_wheels(c, us, v, r_wheel, r_arch):
    for u in us:
        c.circle(u, v, r_arch, c.col((0.12, 0.12, 0.15)), lift=0)
        _wheel(c, u, v, r_wheel)


def _beacon(c, u, v, w, h, color, glow_r=0.22):
    """A dome of a siren light with a halo."""
    col = c.col(color)
    c.glow(u, v + h * 0.4, glow_r, col, 0.55)
    c.ellipse(u, v + h * 0.35, w / 2, h * 0.85, col, lift=0.20)
    c.rect(u, v + h * 0.05, w, h * 0.30, scale(col, 0.75), r=0.01, lift=0.0)
    c.ellipse(u - w * 0.15, v + h * 0.60, w * 0.14, h * 0.20, WHITE, lift=0, alpha=0.55)


def _cross(c, u, v, s, color):
    c.rect(u, v, s, s * 0.34, color, lift=0.05)
    c.rect(u, v, s * 0.34, s, color, lift=0.05)


def _star(c, u, v, r, color, inner=0.45, lift=0.1):
    pts = []
    for k in range(10):
        a = math.radians(90 + k * 36)
        rr = r if k % 2 == 0 else r * inner
        pts.append((u + rr * math.cos(a), v + rr * math.sin(a)))
    c.poly(pts, color, lift=lift)


# --------------------------------------------------------------------------------- vehicles
@prop("ambulance", aspect=2.4, place="ground", nominal=0.24, fill=0.78, category="vehicles",
      words=("paramedic", "hospitalvan", "medicalvan", "ambulances"))
def ambulance(c, color):
    c.shadow(0.0, 0.02, 2.4, 0.10, alpha=0.30)
    accent = c.pick(color, (0.88, 0.14, 0.18))
    white = c.col((0.97, 0.97, 0.99))
    glass = c.col((0.62, 0.80, 0.93))
    dark = c.col((0.12, 0.12, 0.15))
    # box and cab
    c.rect(-0.35, 0.60, 1.60, 0.78, white, r=0.05, lift=0.08)
    c.poly([(0.40, 0.21), (0.40, 0.99), (0.66, 0.99), (0.96, 0.58), (1.17, 0.50), (1.20, 0.21)], white, lift=0.10)
    # windows
    c.poly([(0.50, 0.58), (0.50, 0.90), (0.66, 0.90), (0.90, 0.58)], glass, lift=0.18)
    c.line(0.45, 0.20, 0.45, 0.96, 0.02, scale(white, 0.74))                       # cab/box seam
    # stripes (accent colour)
    c.rect(-0.35, 0.40, 1.60, 0.07, accent, lift=0.08)
    c.poly([(0.40, 0.365), (0.40, 0.435), (1.02, 0.435), (1.12, 0.365)], accent, lift=0.08)
    c.rect(-0.35, 0.31, 1.60, 0.025, c.col((0.20, 0.45, 0.85)), lift=0)
    # side cross and lettering
    c.circle(-0.88, 0.74, 0.17, white, lift=0.0)
    _cross(c, -0.88, 0.74, 0.30, accent)
    c.text("AMBULANCE", -0.14, 0.75, 0.16, accent, 0.20, max_w=0.95)
    c.rect(-0.14, 0.595, 0.95, 0.012, scale(white, 0.82), lift=0)
    # rear doors, handles
    c.line(-1.02, 0.25, -1.02, 0.96, 0.014, scale(white, 0.68))
    c.rect(-1.06, 0.50, 0.025, 0.07, dark, r=0.008, lift=0)
    c.rect(-0.45, 0.50, 0.12, 0.025, scale(white, 0.6), r=0.01, lift=0)
    c.rect(0.60, 0.50, 0.10, 0.025, scale(white, 0.6), r=0.01, lift=0)
    # roof lights
    c.rect(0.15, 1.00, 0.52, 0.035, scale(white, 0.7), r=0.01, lift=0)
    _beacon(c, 0.06, 1.01, 0.20, 0.09, BLUE_LIGHT)
    _beacon(c, 0.26, 1.01, 0.20, 0.09, RED_LIGHT)
    c.rect(-0.80, 1.00, 0.06, 0.04, scale(white, 0.7), lift=0)
    # lamps, bumpers
    c.rect(1.18, 0.40, 0.07, 0.09, c.col((1.0, 0.93, 0.55)), r=0.025, lift=0.1)
    c.rect(-1.14, 0.45, 0.06, 0.12, c.col((0.85, 0.12, 0.15)), r=0.02, lift=0.1)
    c.rect(1.18, 0.26, 0.10, 0.07, c.col((0.78, 0.80, 0.84)), r=0.02, lift=0)
    c.rect(-1.13, 0.26, 0.10, 0.07, c.col((0.78, 0.80, 0.84)), r=0.02, lift=0)
    c.ellipse(-0.4, 0.95, 0.6, 0.03, WHITE, lift=0, alpha=0.20)
    _arch_wheels(c, (-0.72, 0.72), 0.20, 0.215, 0.255)


@prop("firetruck", aspect=2.7, place="ground", nominal=0.26, fill=0.78, category="vehicles",
      words=("fireengine", "firebrigade", "firetender", "dumkal", "firetrucks"))
def firetruck(c, color):
    c.shadow(0.0, 0.02, 2.7, 0.10, alpha=0.30)
    body = c.pick(color, (0.85, 0.12, 0.12))
    silver = c.col((0.82, 0.85, 0.90))
    yellow = c.col((0.98, 0.82, 0.15))
    glass = c.col((0.66, 0.84, 0.95))
    dark = c.col((0.14, 0.14, 0.17))
    # ladder on the roof (drawn first, sits on supports)
    for u in (-1.05, -0.45, 0.15):
        c.rect(u, 0.89, 0.05, 0.09, scale(silver, 0.7), lift=0)
    c.poly([(-1.28, 0.96), (0.62, 0.96), (0.62, 1.00), (-1.28, 1.00)], silver, lift=0.1)
    c.poly([(-1.28, 1.06), (0.62, 1.06), (0.62, 1.10), (-1.28, 1.10)], silver, lift=0.1)
    for k in range(25):
        c.line(-1.24 + k * 0.077, 0.98, -1.24 + k * 0.077, 1.08, 0.016, scale(silver, 0.85))
    # rear body and cab
    c.rect(-0.38, 0.58, 1.84, 0.68, body, r=0.04, lift=0.10)
    c.poly([(0.52, 0.22), (0.52, 0.93), (0.98, 0.93), (1.18, 0.62), (1.34, 0.56), (1.34, 0.22)], body, lift=0.12)
    c.poly([(0.60, 0.60), (0.60, 0.85), (0.96, 0.85), (1.10, 0.60)], glass, lift=0.18)
    c.line(0.80, 0.60, 0.80, 0.85, 0.014, scale(body, 0.6))
    c.rect(0.56, 0.50, 0.12, 0.025, silver, r=0.01, lift=0)                      # door handle
    # equipment lockers with silver roller shutters
    for k in range(3):
        c.rect(-0.95 + k * 0.40, 0.46, 0.34, 0.34, scale(silver, 0.9), r=0.02, lift=0.12)
        for j in range(5):
            c.rect(-0.95 + k * 0.40, 0.60 - j * 0.07, 0.34, 0.012, scale(silver, 0.65), lift=0)
    # hose reel on the rear
    c.circle(-1.14, 0.54, 0.12, silver, lift=0.15)
    c.circle(-1.14, 0.54, 0.075, scale(body, 0.8), lift=0.1)
    c.circle(-1.14, 0.54, 0.03, silver, lift=0)
    c.arc(-1.14, 0.54, 0.10, 20, 330, 0.02, yellow)
    # pump panel
    c.rect(0.30, 0.48, 0.16, 0.20, c.col((0.20, 0.21, 0.26)), r=0.01, lift=0.1)
    c.circle(0.30, 0.52, 0.04, WHITE, lift=0)
    c.circle(0.30, 0.43, 0.03, silver, lift=0)
    # lettering and stripes
    c.rect(-0.38, 0.84, 1.84, 0.025, yellow, lift=0)
    c.rect(-0.38, 0.29, 1.84, 0.035, yellow, lift=0)
    c.rect(0.0, 0.265, 2.65, 0.03, silver, lift=0.1)                             # silver running board
    # cab roof lights, grille and lamps
    c.rect(0.76, 0.95, 0.40, 0.03, scale(silver, 0.75), r=0.01, lift=0)
    _beacon(c, 0.68, 0.96, 0.17, 0.09, RED_LIGHT, 0.26)
    _beacon(c, 0.88, 0.96, 0.17, 0.09, BLUE_LIGHT, 0.26)
    c.rect(1.02, 0.96, 0.17, 0.09, c.col(RED_LIGHT), r=0.04, lift=0.15)
    c.rect(1.34, 0.38, 0.06, 0.12, c.col((1.0, 0.93, 0.55)), r=0.03, lift=0.1)
    c.rect(1.36, 0.27, 0.10, 0.07, silver, r=0.02, lift=0)
    c.rect(-1.30, 0.27, 0.10, 0.07, silver, r=0.02, lift=0)
    c.rect(-1.32, 0.46, 0.05, 0.10, c.col((0.95, 0.55, 0.12)), r=0.02, lift=0.1)
    c.ellipse(-0.3, 0.88, 0.9, 0.03, WHITE, lift=0, alpha=0.18)
    _arch_wheels(c, (-0.88, -0.18, 0.92), 0.20, 0.225, 0.265)


@prop("policecar", aspect=2.3, place="ground", nominal=0.2, fill=0.55, category="vehicles",
      words=("patrolcar", "squadcar", "policevan", "cruiser", "policecars"))
def policecar(c, color):
    c.shadow(0.0, 0.02, 2.2, 0.10, alpha=0.30)
    body = c.pick(color, (0.16, 0.30, 0.68))
    white = c.col((0.97, 0.97, 0.99))
    glass = c.col((0.55, 0.72, 0.85))
    # cabin (white roof), lower body
    c.poly([(-0.62, 0.50), (-0.38, 0.88), (0.30, 0.88), (0.62, 0.50)], white, lift=0.12)
    c.poly([(-0.52, 0.52), (-0.34, 0.82), (-0.02, 0.82), (-0.02, 0.52)], glass, lift=0.18)
    c.poly([(0.03, 0.52), (0.03, 0.82), (0.27, 0.82), (0.52, 0.52)], glass, lift=0.18)
    c.rect(0, 0.36, 2.10, 0.34, body, r=0.14, lift=0.12)
    c.rect(-0.02, 0.50, 0.03, 0.34, scale(white, 0.8), lift=0)
    # white door panels with lettering and badge
    c.rect(0.0, 0.375, 0.84, 0.22, white, r=0.04, lift=0.08)
    c.circle(-0.29, 0.375, 0.065, c.col((0.96, 0.78, 0.18)), lift=0.1)
    _star(c, -0.29, 0.375, 0.05, c.col((0.20, 0.30, 0.65)), 0.5, lift=0)
    c.text("POLICE", 0.09, 0.375, 0.095, body, 0.22, max_w=0.48)
    c.rect(1.00, 0.40, 0.09, 0.07, c.col((1.0, 0.92, 0.55)), r=0.03, lift=0.1)
    c.rect(-1.02, 0.42, 0.07, 0.09, c.col((0.85, 0.12, 0.15)), r=0.025, lift=0.1)
    c.rect(1.03, 0.25, 0.08, 0.08, c.col((0.8, 0.82, 0.86)), r=0.02, lift=0)
    c.ellipse(-0.20, 0.50, 0.40, 0.05, WHITE, lift=0, alpha=0.18)
    # light bar
    c.rect(-0.02, 0.905, 0.46, 0.035, c.col((0.20, 0.21, 0.26)), r=0.01, lift=0)
    _beacon(c, -0.14, 0.915, 0.20, 0.09, BLUE_LIGHT, 0.26)
    _beacon(c, 0.10, 0.915, 0.20, 0.09, RED_LIGHT, 0.26)
    for u in (-0.66, 0.66):
        c.circle(u, 0.20, 0.265, c.col((0.12, 0.12, 0.15)), lift=0)
        _wheel(c, u, 0.20, 0.225)


# --------------------------------------------------------------------------------- people
@prop("firefighter", aspect=0.6, place="ground", nominal=0.5, category="rescue",
      words=("fireman", "firewoman", "fireservice", "firefighters"))
def firefighter(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    coat = c.pick(color, (0.96, 0.76, 0.12))
    pants = c.col((0.26, 0.25, 0.27))
    silver = c.col((0.88, 0.90, 0.93))
    black = c.col((0.10, 0.10, 0.12))
    skin = c.col(c.rng.choice(SKIN))
    hair = c.col(c.rng.choice(HAIR))
    # axe sits behind the near hand
    wood = c.col((0.62, 0.40, 0.20))
    c.line(0.215, 0.20, 0.215, 0.74, 0.024, wood)
    c.poly([(0.215, 0.72), (0.31, 0.77), (0.31, 0.60), (0.215, 0.64)], c.col((0.72, 0.74, 0.80)), lift=0.15)
    c.poly([(0.215, 0.72), (0.255, 0.74), (0.255, 0.62), (0.215, 0.64)], c.col((0.85, 0.15, 0.15)), lift=0.1)
    _figure(c, coat, pants, skin=skin, hair=hair, style="short")
    # boots
    for sgn in (-1, 1):
        c.rect(sgn * 0.067, 0.07, 0.125, 0.15, black, r=0.03, lift=0.1)
        c.ellipse(sgn * 0.075, 0.025, 0.09, 0.034, black, lift=0.1)
    # coat longer than the torso, black collar and reflective stripes
    c.poly([(-0.165, 0.46), (0.165, 0.46), (0.17, 0.33), (-0.17, 0.33)], coat, lift=0.12)
    c.poly([(-0.07, 0.785), (0.07, 0.785), (0.0, 0.66)], black, lift=0.0)
    c.rect(0.0, 0.40, 0.31, 0.03, silver, lift=0.1)
    c.rect(0.0, 0.52, 0.28, 0.03, silver, lift=0.1)
    c.line(0.0, 0.66, 0.0, 0.33, 0.012, black)
    for sgn in (-1, 1):
        c.rect(sgn * 0.19, 0.60, 0.065, 0.025, silver, lift=0.1)
        c.rect(sgn * 0.065, 0.14, 0.115, 0.025, silver, lift=0.1)
        c.circle(sgn * 0.205, 0.49, 0.036, c.col((0.20, 0.20, 0.22)), lift=0.05)     # gloves
    c.circle(0.205, 0.49, 0.038, c.col((0.20, 0.20, 0.22)), lift=0.05)
    # helmet with brim, crest and badge
    red = c.col((0.85, 0.13, 0.13))
    c.poly([(-0.115, 0.952), (0.115, 0.952), (0.135, 0.934), (0.0, 0.924), (-0.135, 0.934)], scale(red, 0.85), lift=0.0)
    c.ellipse(0.0, 0.966, 0.125, 0.026, red, lift=0.10)
    c.ellipse(0.0, 0.993, 0.105, 0.075, red, lift=0.15)
    c.rect(0.0, 1.053, 0.03, 0.025, red, lift=0.1)
    c.ellipse(0.0, 1.033, 0.012, 0.04, scale(red, 0.7), lift=0)
    c.poly([(-0.032, 1.008), (0.032, 1.008), (0.032, 0.968), (0.0, 0.948), (-0.032, 0.968)], c.col((0.98, 0.82, 0.20)), lift=0.1)
    c.circle(0.0, 0.983, 0.010, red, lift=0)


@prop("police", aspect=0.5, place="ground", nominal=0.5, category="rescue",
      words=("policeman", "policewoman", "cop", "constable", "sheriff", "officer", "thana"))
def police(c, color):
    c.shadow(0.0, 0.01, 0.5, 0.06)
    shirt = c.pick(color, (0.30, 0.50, 0.85))
    navy = c.col((0.12, 0.17, 0.34))
    black = c.col((0.10, 0.10, 0.12))
    gold = c.col((0.97, 0.80, 0.22))
    skin = c.col(c.rng.choice(SKIN))
    hair = c.col(c.rng.choice(HAIR))
    # baton held at the right hand
    c.line(0.20, 0.50, 0.30, 0.34, 0.030, black)
    _figure(c, shirt, navy, skin=skin, hair=hair, style="short")
    c.circle(0.205, 0.49, 0.036, skin, lift=0.05)
    # collar, tie, belt
    c.poly([(-0.07, 0.785), (0.0, 0.76), (0.0, 0.70)], scale(shirt, 1.12), lift=0.0)
    c.poly([(0.07, 0.785), (0.0, 0.76), (0.0, 0.70)], scale(shirt, 1.12), lift=0.0)
    c.poly([(-0.02, 0.765), (0.02, 0.765), (0.028, 0.58), (0.0, 0.54), (-0.028, 0.58)], black, lift=0.1)
    c.rect(0.0, 0.47, 0.285, 0.04, black, lift=0.1)
    c.rect(0.0, 0.47, 0.04, 0.03, c.col((0.72, 0.74, 0.80)), lift=0.1)
    c.rect(-0.11, 0.43, 0.04, 0.05, black, r=0.01, lift=0)                          # holster / pouch
    # chest badge, pocket, shoulder radio
    _star(c, 0.075, 0.64, 0.035, gold, 0.5, lift=0.1)
    c.rect(-0.07, 0.63, 0.07, 0.065, scale(shirt, 0.88), r=0.006, lift=0)
    c.rect(-0.07, 0.655, 0.07, 0.012, scale(shirt, 0.75), lift=0)
    c.rect(-0.105, 0.73, 0.055, 0.04, black, r=0.01, lift=0.1)
    c.line(-0.12, 0.75, -0.13, 0.82, 0.008, black)
    c.rect(-0.185, 0.66, 0.02, 0.05, navy, lift=0)                                  # sleeve patch
    # peaked cap
    c.ellipse(0.0, 0.945, 0.115, 0.032, black, lift=0.12)                           # visor
    c.ellipse(0.0, 0.975, 0.112, 0.060, navy, lift=0.15)
    c.rect(0.0, 0.952, 0.18, 0.026, black, r=0.006, lift=0.05)
    c.circle(0.0, 0.975, 0.028, gold, lift=0.1)
    _star(c, 0.0, 0.975, 0.020, navy, 0.5, lift=0)


# --------------------------------------------------------------------------------- objects
@prop("hydrant", aspect=0.75, place="ground", nominal=0.30, fill=0.92, category="rescue",
      words=("firehydrant", "hydrants"))
def hydrant(c, color):
    c.shadow(0.0, 0.01, 0.75, 0.07)
    # little puddle
    c.ellipse(0.12, 0.012, 0.36, 0.035, c.col((0.45, 0.68, 0.90)), lift=0.1, alpha=0.7)
    body = c.pick(color, (0.88, 0.14, 0.14))
    cap = c.col((0.98, 0.82, 0.18))
    dark = scale(body, 0.7)
    silver = c.col((0.78, 0.80, 0.86))
    # side outlets (behind barrel)
    for sgn in (-1, 1):
        c.rect(sgn * 0.25, 0.50, 0.20, 0.14, body, r=0.03, lift=0.12)
        c.rect(sgn * 0.215, 0.50, 0.03, 0.15, dark, lift=0)
        c.rect(sgn * 0.355, 0.50, 0.07, 0.19, cap, r=0.025, lift=0.15)             # cap nut
        c.rect(sgn * 0.362, 0.50, 0.025, 0.10, scale(cap, 0.75), lift=0)
    # base flange, barrel, bonnet
    c.rect(0, 0.07, 0.40, 0.09, body, r=0.03, lift=0.12)
    c.rect(0, 0.13, 0.32, 0.06, dark, r=0.02, lift=0.0)
    c.rect(0, 0.40, 0.28, 0.54, body, r=0.04, lift=0.14)
    c.rect(-0.07, 0.40, 0.05, 0.50, WHITE, lift=0, alpha=0.18)
    c.rect(0, 0.70, 0.34, 0.06, body, r=0.025, lift=0.10)
    c.rect(0, 0.66, 0.34, 0.012, dark, lift=0)
    c.ellipse(0, 0.74, 0.17, 0.12, cap, lift=0.18)                                  # dome
    c.rect(0, 0.84, 0.07, 0.07, cap, r=0.01, lift=0.1)                              # top nut
    c.rect(0, 0.90, 0.11, 0.04, scale(cap, 0.85), r=0.01, lift=0.1)
    c.rect(0, 0.47, 0.20, 0.10, cap, r=0.03, lift=0.15)                             # front nozzle
    c.circle(0, 0.47, 0.055, scale(cap, 0.75), lift=0.1)
    c.circle(0, 0.47, 0.022, silver, lift=0.1)
    # chain from side cap to barrel
    c.path([(0.355, 0.43), (0.31, 0.32), (0.20, 0.28), (0.14, 0.36)], 0.012, c.col((0.45, 0.47, 0.53)), smooth=True)


@prop("extinguisher", aspect=0.62, place="ground", nominal=0.30, fill=1.0, category="rescue",
      words=("fireextinguisher", "firesafety", "extinguishers"))
def extinguisher(c, color):
    c.shadow(0.0, 0.01, 0.50, 0.06)
    body = c.pick(color, (0.88, 0.13, 0.13))
    black = c.col((0.12, 0.12, 0.14))
    silver = c.col((0.78, 0.80, 0.86))
    gold = c.col((0.98, 0.82, 0.20))
    # hose (behind), from the valve down to the side
    c.path([(0.10, 0.875), (0.25, 0.86), (0.31, 0.62), (0.24, 0.43)], 0.038, black, smooth=True)
    c.poly([(0.215, 0.44), (0.265, 0.44), (0.255, 0.35), (0.225, 0.35)], black, lift=0.1)
    # cylinder
    c.rect(0, 0.40, 0.34, 0.74, body, r=0.12, lift=0.14)
    c.ellipse(0, 0.72, 0.17, 0.06, body, lift=0.12)
    c.rect(-0.085, 0.40, 0.045, 0.62, WHITE, r=0.02, lift=0, alpha=0.20)
    c.rect(0, 0.04, 0.30, 0.04, black, r=0.02, lift=0.1)                            # base ring
    c.rect(0, 0.755, 0.20, 0.03, scale(body, 0.75), lift=0)                         # shoulder
    # neck and valve head
    c.rect(0, 0.82, 0.12, 0.08, silver, r=0.02, lift=0.15)
    c.rect(0.0, 0.875, 0.20, 0.07, black, r=0.025, lift=0.12)
    c.rect(0.0, 0.935, 0.26, 0.026, scale(black, 1.6), r=0.012, lift=0.1)            # fixed handle
    c.poly([(-0.10, 0.915), (0.12, 0.905), (0.12, 0.885), (-0.10, 0.895)], black, lift=0.1)   # lever
    # gauge and safety pin
    c.circle(-0.13, 0.86, 0.042, silver, lift=0.1)
    c.circle(-0.13, 0.86, 0.032, WHITE, lift=0)
    c.arc(-0.13, 0.86, 0.024, 20, 120, 0.013, c.col((0.20, 0.70, 0.30)))
    c.line(-0.13, 0.86, -0.115, 0.882, 0.008, black)
    c.ring(-0.04, 0.955, 0.02, 0.008, gold)
    c.line(-0.04, 0.935, -0.04, 0.905, 0.008, gold)
    # label with flame
    c.rect(0, 0.40, 0.24, 0.30, c.col((0.97, 0.96, 0.92)), r=0.02, lift=0.04)
    flame = c.col((0.92, 0.35, 0.10))
    c.poly([(0.0, 0.54), (0.055, 0.44), (0.045, 0.37), (0.0, 0.33), (-0.045, 0.37), (-0.05, 0.44), (-0.015, 0.47)], flame, lift=0.1)
    c.poly([(0.005, 0.46), (0.03, 0.40), (0.02, 0.36), (0.0, 0.345), (-0.02, 0.37), (-0.015, 0.42)], c.col((1.0, 0.82, 0.25)), lift=0)
    c.rect(0, 0.285, 0.18, 0.018, black, lift=0)
    c.rect(0, 0.255, 0.14, 0.012, scale(black, 1.8), lift=0)
