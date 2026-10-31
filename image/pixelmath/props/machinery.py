"""Props: machinery and industry (tractor, excavator, tower crane, forklift, wind turbine, solar panels, factory).

All side / front elevations, flat illustration, light from the top left.
"""
import math

from .core import WHITE, mix, prop, scale  # noqa: F401

_TYRE = (0.12, 0.12, 0.14)
_STEEL = (0.52, 0.55, 0.61)
_DARK = (0.20, 0.21, 0.25)
_GLASS = (0.62, 0.82, 0.94)


def _tyre(c, u, v, r, rim, lugs=0):
    """A wheel with an optional ring of tread lugs, a coloured rim and a hub cap."""
    if lugs:
        for k in range(lugs):
            a = math.radians(k * 360.0 / lugs)
            ca, sa = math.cos(a), math.sin(a)
            c.line(u + r * 0.93 * ca, v + r * 0.93 * sa, u + r * 1.07 * ca, v + r * 1.07 * sa, r * 0.15, c.col(_TYRE))
    c.circle(u, v, r, c.col((0.15, 0.15, 0.18)), lift=0.12)
    c.circle(u, v, r * 0.56, rim, lift=0.15)
    c.circle(u, v, r * 0.40, scale(rim, 0.82), lift=0.0)
    c.circle(u, v, r * 0.14, c.col((0.35, 0.36, 0.41)), lift=0.1)


# --------------------------------------------------------------------------------------------- tractor
@prop("tractor", aspect=1.75, place="ground", nominal=0.30, fill=1.0, category="machinery",
      words=("harvester", "plough", "plow", "tiller"))
def tractor(c, color):
    c.shadow(0.0, 0.015, 1.80, 0.10, alpha=0.28)
    body = c.pick(color, (0.24, 0.62, 0.28))
    dark = c.col(_DARK)
    glass = c.col(_GLASS)
    yellow = c.col((0.96, 0.78, 0.20))
    # exhaust pipe
    c.rect(0.52, 0.72, 0.045, 0.40, c.col((0.30, 0.30, 0.34)), lift=0.1)
    c.poly([(0.49, 0.915), (0.575, 0.915), (0.565, 0.945), (0.505, 0.945)], c.col((0.22, 0.22, 0.26)), lift=0.1)
    # front axle + chassis
    c.rect(0.36, 0.24, 0.86, 0.10, dark, lift=0.05)
    # hood
    c.rect(0.40, 0.50, 0.84, 0.40, body, r=0.07, lift=0.14)
    c.rect(0.40, 0.61, 0.78, 0.04, scale(body, 1.18), r=0.02, lift=0)
    c.rect(0.40, 0.35, 0.84, 0.03, scale(body, 0.72), lift=0)
    c.rect(0.80, 0.47, 0.05, 0.24, c.col((0.18, 0.19, 0.22)), r=0.01, lift=0.05)       # grille
    for k in range(3):
        c.rect(0.80, 0.40 + k * 0.07, 0.05, 0.012, c.col((0.55, 0.57, 0.62)), lift=0)
    c.circle(0.795, 0.60, 0.04, c.col((1.0, 0.93, 0.55)), lift=0.1)                     # headlamp
    # front wheel
    _tyre(c, 0.62, 0.18, 0.18, yellow, lugs=14)
    # cab: lower body, pillars, glass, seat, roof
    c.rect(-0.38, 0.55, 0.64, 0.38, body, lift=0.12)
    c.rect(-0.38, 0.865, 0.56, 0.24, glass, r=0.01, lift=0.18)
    c.rect(-0.52, 0.80, 0.07, 0.17, dark, r=0.02, lift=0.0)                              # seat back
    c.rect(-0.45, 0.735, 0.20, 0.05, dark, r=0.02, lift=0.0)                             # seat base
    c.line(-0.22, 0.78, -0.17, 0.90, 0.025, c.col((0.15, 0.15, 0.18)))                    # steering column
    c.poly([(-0.30, 0.86), (-0.26, 0.86), (-0.21, 0.975), (-0.25, 0.975)], WHITE, lift=0, alpha=0.20)
    c.rect(-0.66, 0.86, 0.045, 0.26, body, lift=0.1)
    c.rect(-0.10, 0.86, 0.045, 0.26, body, lift=0.1)
    c.rect(-0.38, 0.995, 0.68, 0.055, scale(body, 1.08), r=0.02, lift=0.12)
    c.rect(-0.38, 0.968, 0.60, 0.012, scale(body, 0.65), lift=0)
    # big rear wheel with fender
    _tyre(c, -0.47, 0.36, 0.36, yellow, lugs=22)
    c.arc(-0.47, 0.36, 0.40, 8, 172, 0.06, body)
    c.arc(-0.47, 0.36, 0.40, 40, 150, 0.015, scale(body, 1.2))
    c.circle(-0.47, 0.36, 0.05, c.col((0.35, 0.36, 0.41)), lift=0.1)


# ------------------------------------------------------------------------------------------- excavator
@prop("excavator", aspect=2.2, place="ground", nominal=0.38, fill=1.0, category="machinery",
      words=("jcb", "digger", "bulldozer", "earthmover", "backhoe"))
def excavator(c, color):
    c = c.sub(-0.34, 0.0, 1.0)
    c.shadow(0.35, 0.015, 2.2, 0.10, alpha=0.28)
    body = c.pick(color, (0.98, 0.76, 0.14))
    dark = c.col(_DARK)
    steel = c.col((0.40, 0.42, 0.48))
    glass = c.col(_GLASS)
    # tracks
    c.rect(0.0, 0.125, 1.54, 0.25, c.col((0.14, 0.14, 0.17)), r=0.125, lift=0.08)
    c.rect(0.0, 0.125, 1.30, 0.17, c.col((0.24, 0.25, 0.29)), r=0.085, lift=0.1)
    for u in (-0.58, 0.58):
        c.circle(u, 0.125, 0.085, c.col((0.50, 0.52, 0.58)), lift=0.12)
        c.circle(u, 0.125, 0.03, dark, lift=0)
    for u in (-0.27, 0.0, 0.27):
        c.circle(u, 0.08, 0.038, c.col((0.50, 0.52, 0.58)), lift=0.1)
    for k in range(13):
        c.rect(-0.69 + k * 0.115, 0.248, 0.05, 0.02, c.col((0.10, 0.10, 0.12)), lift=0)
    # turntable + house
    c.rect(0.0, 0.285, 1.0, 0.07, dark, lift=0.05)
    c.rect(-0.18, 0.44, 1.02, 0.30, body, r=0.06, lift=0.14)
    c.rect(-0.18, 0.375, 1.02, 0.03, scale(body, 0.7), lift=0)
    c.rect(-0.62, 0.45, 0.20, 0.33, scale(body, 0.88), r=0.08, lift=0.1)                # counterweight
    c.rect(-0.62, 0.34, 0.20, 0.03, scale(body, 0.6), lift=0)
    for k in range(4):                                                                    # engine vents
        c.rect(-0.30 + k * 0.07, 0.56, 0.04, 0.012, scale(body, 0.62), lift=0)
    c.rect(-0.28, 0.625, 0.40, 0.07, scale(body, 1.06), r=0.03, lift=0.1)                # engine cover
    c.rect(-0.45, 0.80, 0.035, 0.12, c.col((0.30, 0.30, 0.34)), lift=0.1)               # exhaust
    # cab
    c.poly([(0.02, 0.59), (0.02, 0.93), (0.33, 0.93), (0.38, 0.59)], body, lift=0.14)
    c.poly([(0.06, 0.62), (0.06, 0.89), (0.30, 0.89), (0.345, 0.62)], glass, lift=0.20)
    c.poly([(0.10, 0.64), (0.15, 0.64), (0.21, 0.88), (0.16, 0.88)], WHITE, lift=0, alpha=0.22)
    c.rect(0.18, 0.935, 0.36, 0.03, scale(body, 0.72), r=0.01, lift=0)
    # hydraulic boom cylinder (behind boom)
    c.line(0.30, 0.50, 0.66, 0.78, 0.05, c.col((0.62, 0.64, 0.70)))
    c.line(0.30, 0.50, 0.50, 0.66, 0.065, c.col((0.34, 0.36, 0.42)))
    # boom
    c.path([(0.32, 0.54), (0.66, 0.90), (1.00, 0.98)], 0.125, body, smooth=True)
    c.path([(0.34, 0.585), (0.66, 0.935), (0.98, 1.0)], 0.02, scale(body, 1.15))
    # arm
    c.path([(1.00, 0.98), (1.15, 0.72), (1.24, 0.48)], 0.092, scale(body, 0.94), smooth=True)
    # arm cylinder
    c.line(0.72, 0.99, 1.10, 0.84, 0.045, c.col((0.62, 0.64, 0.70)))
    c.line(0.72, 0.99, 0.88, 0.935, 0.06, c.col((0.34, 0.36, 0.42)))
    c.circle(1.00, 0.98, 0.05, dark, lift=0.1)
    c.circle(1.00, 0.98, 0.02, c.col((0.7, 0.72, 0.78)), lift=0)
    # bucket + teeth
    c.line(1.12, 0.74, 1.34, 0.55, 0.035, c.col((0.62, 0.64, 0.70)))
    bucket = [(1.14, 0.52), (1.30, 0.57), (1.43, 0.40), (1.38, 0.25), (1.20, 0.21), (1.12, 0.33)]
    c.poly(bucket, steel, lift=0.16)
    c.poly([(1.16, 0.45), (1.26, 0.47), (1.30, 0.36), (1.18, 0.33)], scale(steel, 0.78), lift=0)
    for u0, v0, u1, v1 in ((1.20, 0.21, 1.27, 0.21), (1.28, 0.22, 1.34, 0.235), (1.35, 0.245, 1.39, 0.27)):
        mu, mv = (u0 + u1) / 2, (v0 + v1) / 2
        c.poly([(u0, v0), (u1, v1), (mu + 0.01, mv - 0.085)], c.col((0.78, 0.80, 0.85)), lift=0.1)
    c.circle(1.24, 0.48, 0.04, dark, lift=0.1)
    c.circle(0.32, 0.54, 0.045, dark, lift=0.1)


# ---------------------------------------------------------------------------------------------- crane
def _truss(c, u0, u1, v0, v1, pitch, w, color):
    """A horizontal lattice girder: top and bottom chords plus zig-zag diagonals."""
    c.line(u0, v1, u1, v1, w * 1.3, color)
    c.line(u0, v0, u1, v0, w * 1.3, color)
    n = max(1, int(round((u1 - u0) / pitch)))
    d = (u1 - u0) / n
    for k in range(n):
        a, b = u0 + k * d, u0 + (k + 1) * d
        if k % 2 == 0:
            c.line(a, v0, b, v1, w, color)
        else:
            c.line(a, v1, b, v0, w, color)
    c.line(u0, v0, u0, v1, w, color)
    c.line(u1, v0, u1, v1, w, color)


@prop("crane", aspect=0.95, place="ground", nominal=0.55, fill=1.0, category="machinery",
      words=("towercrane", "hoist", "derrick"))
def crane(c, color):
    c = c.sub(-0.15, 0.0, 1.0)
    c.shadow(0.0, 0.01, 0.62, 0.07, alpha=0.26)
    main = c.pick(color, (0.97, 0.76, 0.12))
    dark = c.col(_DARK)
    wire = c.col((0.15, 0.15, 0.18))
    # concrete base
    c.rect(0.0, 0.03, 0.30, 0.06, c.col((0.66, 0.67, 0.70)), r=0.01, lift=0.12)
    c.rect(0.0, 0.065, 0.20, 0.03, c.col((0.55, 0.56, 0.60)), lift=0.05)
    # lattice mast
    bot, top, n = 0.07, 0.82, 10
    step = (top - bot) / n
    c.line(-0.05, bot, -0.05, top, 0.024, main)
    c.line(0.05, bot, 0.05, top, 0.024, main)
    for k in range(n):
        v0, v1 = bot + k * step, bot + (k + 1) * step
        if k % 2 == 0:
            c.line(-0.05, v0, 0.05, v1, 0.014, main)
        else:
            c.line(0.05, v0, -0.05, v1, 0.014, main)
        c.line(-0.05, v1, 0.05, v1, 0.014, main)
    # counter-jib with counterweights
    _truss(c, -0.32, -0.04, 0.865, 0.925, 0.06, 0.011, main)
    c.rect(-0.26, 0.825, 0.10, 0.08, c.col((0.58, 0.59, 0.63)), lift=0.12)
    c.rect(-0.155, 0.83, 0.08, 0.07, c.col((0.50, 0.51, 0.56)), lift=0.12)
    # jib
    _truss(c, -0.04, 0.63, 0.865, 0.925, 0.062, 0.011, main)
    c.poly([(0.63, 0.865), (0.63, 0.925), (0.66, 0.865)], main, lift=0.05)
    # slewing unit and cab
    c.rect(0.0, 0.838, 0.15, 0.04, dark, lift=0.1)
    c.rect(0.11, 0.80, 0.11, 0.10, main, r=0.01, lift=0.14)
    c.rect(0.115, 0.805, 0.07, 0.065, c.col(_GLASS), lift=0.2)
    # apex and tie bars
    c.poly([(-0.05, 0.925), (0.05, 0.925), (0.0, 1.0)], main, lift=0.1)
    c.line(0.0, 1.0, 0.60, 0.925, 0.009, wire)
    c.line(0.0, 1.0, -0.30, 0.925, 0.009, wire)
    c.circle(0.0, 1.0, 0.012, c.col((0.85, 0.15, 0.15)), lift=0)
    # trolley, cable, hook, sling, load
    c.rect(0.42, 0.855, 0.06, 0.025, dark, lift=0.1)
    c.line(0.42, 0.85, 0.42, 0.50, 0.009, wire)
    c.rect(0.42, 0.485, 0.04, 0.035, c.col((0.85, 0.20, 0.20)), r=0.008, lift=0.1)
    c.arc(0.42, 0.455, 0.018, 180, 360, 0.01, wire)
    c.line(0.42, 0.45, 0.335, 0.375, 0.009, wire)
    c.line(0.42, 0.45, 0.505, 0.375, 0.009, wire)
    crate = c.col((0.86, 0.50, 0.20))
    c.rect(0.42, 0.32, 0.20, 0.11, crate, r=0.006, lift=0.16)
    for du in (-0.07, 0.0, 0.07):
        c.line(0.42 + du, 0.265, 0.42 + du, 0.375, 0.008, scale(crate, 0.65))
    c.line(0.32, 0.32, 0.52, 0.32, 0.008, scale(crate, 0.65))


# ------------------------------------------------------------------------------------------- forklift
@prop("forklift", aspect=1.65, place="ground", nominal=0.30, fill=1.0, category="machinery",
      words=("warehouse", "pallet", "godown"))
def forklift(c, color):
    c = c.sub(-0.25, 0.0, 1.0)
    c.shadow(0.25, 0.015, 1.70, 0.10, alpha=0.28)
    body = c.pick(color, (0.96, 0.58, 0.12))
    dark = c.col((0.21, 0.22, 0.26))
    steel = c.col((0.55, 0.57, 0.63))
    wood = c.col((0.78, 0.58, 0.34))
    # mast (behind everything at the front)
    for u in (0.46, 0.55):
        c.rect(u, 0.50, 0.035, 0.90, c.col((0.42, 0.44, 0.50)), lift=0.12)
    c.rect(0.505, 0.94, 0.14, 0.03, c.col((0.42, 0.44, 0.50)), lift=0.1)
    c.rect(0.505, 0.62, 0.11, 0.02, c.col((0.42, 0.44, 0.50)), lift=0.1)
    c.rect(0.505, 0.30, 0.11, 0.02, c.col((0.42, 0.44, 0.50)), lift=0.1)
    # lift chain
    c.line(0.505, 0.62, 0.505, 0.23, 0.01, c.col((0.25, 0.25, 0.28)))
    # carriage and fork
    c.rect(0.585, 0.20, 0.06, 0.28, dark, lift=0.1)
    c.rect(0.80, 0.15, 0.52, 0.045, steel, lift=0.15)
    c.poly([(1.06, 0.1725), (1.06, 0.1275), (1.10, 0.1275)], steel, lift=0.1)
    # pallet + boxes
    c.rect(0.80, 0.195, 0.50, 0.035, wood, lift=0.12)
    c.rect(0.80, 0.108, 0.50, 0.03, scale(wood, 0.9), lift=0.1)
    for u in (0.585, 0.80, 1.015):
        c.rect(u, 0.152, 0.075, 0.06, scale(wood, 0.75), lift=0.05)
    box1, box2 = c.col((0.84, 0.64, 0.40)), c.col((0.76, 0.56, 0.34))
    c.rect(0.70, 0.325, 0.22, 0.225, box1, lift=0.12)
    c.rect(0.70, 0.325, 0.03, 0.225, scale(box1, 0.78), lift=0)
    c.rect(0.935, 0.30, 0.20, 0.175, box2, lift=0.12)
    c.rect(0.935, 0.30, 0.03, 0.175, scale(box2, 0.78), lift=0)
    c.rect(0.70, 0.44, 0.22, 0.012, scale(box1, 0.8), lift=0)
    # overhead guard (rear post, seat, steering, roof)
    c.rect(-0.12, 0.495, 0.22, 0.05, dark, r=0.02, lift=0.0)                              # seat cushion
    c.rect(-0.22, 0.60, 0.06, 0.24, dark, r=0.02, lift=0.0)                               # seat back
    # body
    c.poly([(-0.58, 0.10), (-0.58, 0.64), (-0.34, 0.64), (-0.26, 0.44), (0.40, 0.44), (0.42, 0.10)], body, lift=0.14)
    c.rect(-0.46, 0.48, 0.20, 0.30, scale(body, 0.9), r=0.05, lift=0.08)
    c.rect(0.06, 0.35, 0.50, 0.025, scale(body, 0.7), lift=0)
    c.rect(-0.12, 0.395, 0.34, 0.03, scale(body, 1.15), lift=0)
    c.line(0.12, 0.47, 0.20, 0.68, 0.03, dark)                                             # steering column
    c.ellipse(0.19, 0.69, 0.065, 0.016, c.col((0.10, 0.10, 0.12)), angle=-15, lift=0)
    c.line(-0.34, 0.60, -0.34, 1.0, 0.03, dark)
    c.line(0.30, 0.44, 0.30, 1.0, 0.03, dark)
    c.rect(-0.02, 1.0, 0.70, 0.045, dark, r=0.015, lift=0.1)
    for k in range(5):
        c.line(-0.26 + k * 0.12, 0.985, -0.26 + k * 0.12, 0.945, 0.012, dark)
    c.circle(0.40, 0.30, 0.025, c.col((1.0, 0.93, 0.55)), lift=0.1)
    # wheels
    _tyre(c, 0.17, 0.17, 0.17, c.col((0.80, 0.82, 0.86)))
    _tyre(c, -0.40, 0.13, 0.13, c.col((0.80, 0.82, 0.86)))


# ------------------------------------------------------------------------------------------ windmill
@prop("windmill", aspect=0.70, place="ground", nominal=0.50, fill=1.0, category="machinery",
      words=("turbine", "windturbine", "wind"))
def windmill(c, color):
    hub = (0.0, 0.66)
    main = c.pick(color, (0.96, 0.97, 0.98))
    c.ellipse(0.0, 0.012, 0.30, 0.035, c.col((0.46, 0.68, 0.36)), lift=0.1)
    c.shadow(0.0, 0.01, 0.44, 0.04, alpha=0.20)
    # tower: lit left half, darker right half
    edge = c.col((0.62, 0.65, 0.72))
    c.poly([(-0.046, 0.01), (0.046, 0.01), (0.026, hub[1]), (-0.026, hub[1])], edge, lift=0.0)
    c.poly([(-0.040, 0.01), (0.040, 0.01), (0.021, hub[1]), (-0.021, hub[1])], main, lift=0.08)
    c.poly([(0.0, 0.01), (0.040, 0.01), (0.021, hub[1]), (0.0, hub[1])], scale(main, 0.86), lift=0.0, alpha=0.9)
    c.rect(0.0, 0.06, 0.092, 0.035, c.col((0.85, 0.25, 0.25)), lift=0)
    c.rect(0.0, 0.015, 0.13, 0.02, c.col((0.55, 0.56, 0.60)), lift=0.05)
    # blades (grey rim so white blades read on a light sky)
    blade = [(-0.028, 0.03), (-0.048, 0.10), (-0.030, 0.24), (0.0, 0.345), (0.024, 0.23), (0.034, 0.09), (0.022, 0.03)]
    for k in range(3):
        ang = 78 + 120 * k
        big = [(hub[0] + u * 1.22, hub[1] + v * 1.02 + 0.0) for u, v in blade]
        c.poly(big, edge, lift=0.0, angle=ang, pivot=hub)
        c.poly([(hub[0] + u, hub[1] + v) for u, v in blade], main, lift=0.10, angle=ang, pivot=hub)
        c.poly([(hub[0] + u * 0.25 + (0.012 if u > 0 else 0), hub[1] + v) for u, v in blade[:5]], scale(main, 0.84), lift=0, alpha=0.5,
               angle=ang, pivot=hub)
    # nacelle and hub
    c.rect(0.045, hub[1] + 0.002, 0.17, 0.07, c.col((0.88, 0.89, 0.92)), r=0.03, lift=0.14)
    c.rect(0.045, hub[1] - 0.025, 0.17, 0.012, c.col((0.60, 0.62, 0.68)), lift=0)
    c.circle(hub[0], hub[1], 0.058, c.col((0.76, 0.78, 0.84)), lift=0.18)
    c.circle(hub[0], hub[1], 0.022, c.col((0.50, 0.52, 0.58)), lift=0.1)


# ---------------------------------------------------------------------------------------- solar panel
def _panel(c, cu, wb, wt, v0, v1, cell):
    def pt(s, t):
        hw = wb + t * (wt - wb)
        return (cu + (2 * s - 1) * hw, v0 + t * (v1 - v0))
    frame = c.col((0.84, 0.86, 0.90))
    # panel thickness below the lower edge
    c.poly([pt(0, 0), pt(1, 0), (pt(1, 0)[0], v0 - 0.035), (pt(0, 0)[0], v0 - 0.035)], c.col((0.55, 0.57, 0.63)), lift=0.05)
    c.poly([pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)], frame, lift=0.10)
    a, b = 0.035, 0.045
    c.poly([pt(a, b), pt(1 - a, b), pt(1 - a, 1 - b), pt(a, 1 - b)], cell, lift=0.20)
    line = mix(cell, (0.75, 0.85, 1.0), 0.38)
    cols, rows = 6, 5
    for i in range(1, cols):
        s = a + (1 - 2 * a) * i / cols
        p, q = pt(s, b), pt(s, 1 - b)
        c.line(p[0], p[1], q[0], q[1], 0.007, line)
    for j in range(1, rows):
        t = b + (1 - 2 * b) * j / rows
        p, q = pt(a, t), pt(1 - a, t)
        c.line(p[0], p[1], q[0], q[1], 0.007, line)
    # sheen
    c.poly([pt(0.50, 1 - b), pt(0.70, 1 - b), pt(0.34, b), pt(0.14, b)], WHITE, lift=0, alpha=0.20)
    c.poly([pt(0.74, 1 - b), pt(0.80, 1 - b), pt(0.44, b), pt(0.38, b)], WHITE, lift=0, alpha=0.12)


@prop("solarpanel", aspect=1.65, place="ground", nominal=0.28, fill=0.92, category="machinery",
      words=("solar", "photovoltaic"))
def solarpanel(c, color):
    c.shadow(0.0, 0.012, 1.70, 0.08, alpha=0.26)
    cell = c.pick(color, (0.13, 0.28, 0.62))
    leg = c.col((0.50, 0.52, 0.58))
    # stand: posts and a rail
    for u in (-0.70, -0.12, 0.12, 0.70):
        c.rect(u, 0.14, 0.035, 0.28, leg, lift=0.1)
    c.rect(0.0, 0.17, 1.46, 0.025, scale(leg, 0.85), lift=0.05)
    c.line(-0.41, 0.30, -0.70, 0.06, 0.02, scale(leg, 0.8))
    c.line(0.41, 0.30, 0.70, 0.06, 0.02, scale(leg, 0.8))
    _panel(c, -0.41, 0.38, 0.32, 0.30, 0.88, cell)
    _panel(c, 0.41, 0.38, 0.32, 0.30, 0.88, cell)


# ------------------------------------------------------------------------------------------- factory
@prop("factory", aspect=2.05, place="ground", nominal=0.45, fill=1.0, category="buildings",
      words=("manufacturing", "industry", "industrial", "mill", "workshopfloor"))
def factory(c, color):
    c = c.sub(-0.02, 0.0, 1.0)
    c.shadow(0.0, 0.01, 2.15, 0.07, alpha=0.26)
    wall = c.pick(color, (0.80, 0.50, 0.38))
    roof = c.col((0.36, 0.40, 0.48))
    glass = c.col(_GLASS)
    dark = c.col(_DARK)
    smoke = c.col((0.84, 0.85, 0.88))
    # chimneys (behind the roof) with smoke
    for u in (-0.72, -0.50):
        c.poly([(u - 0.055, 0.45), (u + 0.055, 0.45), (u + 0.04, 0.80), (u - 0.04, 0.80)], c.col((0.72, 0.42, 0.32)), lift=0.12)
        c.rect(u, 0.745, 0.095, 0.035, c.col((0.93, 0.93, 0.95)), lift=0.05)
        c.rect(u, 0.80, 0.10, 0.025, dark, lift=0.1)
    for (u, v, r, a) in ((-0.70, 0.88, 0.055, 0.90), (-0.60, 0.94, 0.075, 0.85), (-0.45, 0.99, 0.08, 0.75),
                         (-0.52, 0.86, 0.045, 0.85), (-0.38, 0.91, 0.06, 0.7)):
        c.circle(u, v, r, smoke, lift=0.1, alpha=a)
    # silo
    c.rect(0.93, 0.36, 0.30, 0.64, c.col((0.70, 0.73, 0.79)), lift=0.14)
    c.ellipse(0.93, 0.68, 0.15, 0.07, c.col((0.78, 0.80, 0.86)), lift=0.12)
    c.rect(0.93, 0.33, 0.30, 0.02, c.col((0.52, 0.55, 0.62)), lift=0)
    c.rect(0.93, 0.50, 0.30, 0.02, c.col((0.52, 0.55, 0.62)), lift=0)
    c.rect(0.865, 0.36, 0.035, 0.62, WHITE, lift=0, alpha=0.25)
    # annex
    c.rect(0.52, 0.31, 0.38, 0.62, scale(wall, 0.94), lift=0.12)
    c.rect(0.52, 0.63, 0.42, 0.04, roof, lift=0.1)
    for r in range(2):
        for k in range(2):
            c.rect(0.42 + k * 0.20, 0.50 + r * 0.16, 0.11, 0.10, glass, r=0.004, lift=0.2)
    # main hall
    c.rect(-0.37, 0.19, 1.30 + 0.0, 0.38, wall, lift=0.12)
    c.rect(-0.37, 0.385, 1.34, 0.03, scale(wall, 0.65), lift=0)
    # sawtooth roof
    n, w = 4, 0.325
    x0 = -1.02
    for k in range(n):
        a = x0 + k * w
        c.poly([(a, 0.38), (a, 0.57), (a + w, 0.38)], roof, lift=0.12)
        c.poly([(a, 0.38), (a, 0.57), (a + 0.035, 0.57 - 0.035 * 0.58 * 1.0), (a + 0.035, 0.38)], glass, lift=0.15)
    # big door
    c.rect(-0.37, 0.14, 0.40, 0.28, c.col((0.96, 0.78, 0.18)), lift=0.12)
    c.rect(-0.37, 0.13, 0.34, 0.25, c.col((0.60, 0.64, 0.70)), lift=0.14)
    for k in range(6):
        c.rect(-0.37, 0.03 + k * 0.043, 0.34, 0.01, c.col((0.46, 0.50, 0.56)), lift=0)
    # windows
    for u in (-0.90, -0.74, -0.04, 0.12):
        c.rect(u, 0.23, 0.11, 0.10, glass, r=0.004, lift=0.2)
    # annex door
    c.rect(0.52, 0.10, 0.12, 0.20, dark, r=0.005, lift=0.1)
    # pipe from silo to hall roof line
    c.line(0.93, 0.69, 0.93, 0.74, 0.035, c.col((0.56, 0.59, 0.66)))
    c.line(0.72, 0.18, 0.90, 0.18, 0.04, c.col((0.56, 0.59, 0.66)))
    c.line(0.90, 0.18, 0.90, 0.02, 0.04, c.col((0.56, 0.59, 0.66)))
    c.rect(0.93, 0.015, 0.34, 0.03, scale(wall, 0.6), lift=0)
