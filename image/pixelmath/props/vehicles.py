"""Vehicles (side view, facing right)."""
import math

from .core import WHITE, mix, prop, scale


def _wheel(c, u, v, r, rim=None):
    c.circle(u, v, r * 1.12, c.col((0.10, 0.10, 0.12)), lift=0)
    c.circle(u, v, r, c.col((0.16, 0.16, 0.19)), lift=0.1)
    c.circle(u, v, r * 0.62, rim or c.col((0.82, 0.84, 0.88)), lift=0.15)
    for k in range(5):
        a = math.radians(k * 72 + 18)
        c.line(u, v, u + r * 0.58 * math.cos(a), v + r * 0.58 * math.sin(a), r * 0.12, c.col((0.55, 0.57, 0.63)))
    c.circle(u, v, r * 0.16, c.col((0.45, 0.47, 0.53)), lift=0)


@prop("car", aspect=2.3, place="ground", nominal=0.2, fill=0.55, category="vehicles",
      words=("cars", "automobile", "sedan", "taxi", "cab", "gaadi", "vehicle", "vehicles", "auto", "drive", "driving", "dealership", "rental", "driver", "motor"))
def car(c, color):
    c.shadow(0.0, 0.02, 2.2, 0.10, alpha=0.30)
    body = c.pick(color, (0.88, 0.22, 0.22))
    # cabin first, then lower body over its base
    c.poly([(-0.62, 0.50), (-0.38, 0.88), (0.30, 0.88), (0.62, 0.50)], body, lift=0.14)
    glass = c.col((0.68, 0.84, 0.95))
    c.poly([(-0.52, 0.52), (-0.34, 0.82), (-0.02, 0.82), (-0.02, 0.52)], glass, lift=0.18)
    c.poly([(0.03, 0.52), (0.03, 0.82), (0.27, 0.82), (0.52, 0.52)], glass, lift=0.18)
    c.rect(0, 0.36, 2.10, 0.34, body, r=0.14, lift=0.12)
    c.rect(0.0, 0.30, 2.0, 0.015, scale(body, 0.7), lift=0)
    c.rect(-0.02, 0.50, 0.03, 0.34, scale(body, 0.8), lift=0)
    c.rect(0.08, 0.40, 0.14, 0.03, scale(body, 0.65), r=0.012, lift=0)
    c.rect(1.00, 0.40, 0.09, 0.07, c.col((1.0, 0.92, 0.55)), r=0.03, lift=0.1)
    c.rect(-1.02, 0.42, 0.07, 0.09, c.col((0.85, 0.12, 0.15)), r=0.025, lift=0.1)
    c.rect(1.03, 0.25, 0.08, 0.08, c.col((0.8, 0.82, 0.86)), r=0.02, lift=0)
    c.ellipse(-0.20, 0.50, 0.40, 0.05, WHITE, lift=0, alpha=0.18)
    for u in (-0.66, 0.66):
        c.circle(u, 0.20, 0.265, c.col((0.12, 0.12, 0.15)), lift=0)
        _wheel(c, u, 0.20, 0.225)


@prop("truck", aspect=2.1, place="ground", nominal=0.24, fill=0.7, category="vehicles",
      words=("van", "lorry", "delivery", "cargo", "shipping", "logistics", "courier", "transport", "trucks", "freight", "moving", "packers", "movers", "transportation", "parcel"))
def truck(c, color):
    c.shadow(0.0, 0.02, 2.1, 0.10, alpha=0.30)
    box = c.pick(color, (0.97, 0.97, 0.98))
    cab = c.col((0.20, 0.45, 0.85))
    c.rect(-0.30, 0.56, 1.30, 0.74, box, r=0.04, lift=0.08)
    c.rect(-0.30, 0.40, 1.30, 0.07, c.col((0.95, 0.60, 0.15)), lift=0)
    c.rect(-0.30, 0.28, 1.30, 0.03, scale(box, 0.8), lift=0)
    c.poly([(0.36, 0.20), (0.36, 0.86), (0.76, 0.86), (0.98, 0.52), (1.02, 0.20)], cab, lift=0.14)
    c.poly([(0.44, 0.52), (0.44, 0.78), (0.72, 0.78), (0.88, 0.52)], c.col((0.70, 0.86, 0.96)), lift=0.18)
    c.rect(0.55, 0.44, 0.10, 0.025, scale(cab, 0.7), lift=0)
    c.rect(0.96, 0.32, 0.08, 0.07, c.col((1.0, 0.92, 0.55)), r=0.02, lift=0.1)
    c.rect(1.0, 0.22, 0.07, 0.07, c.col((0.8, 0.82, 0.86)), r=0.02, lift=0)
    c.circle(-0.28, 0.58, 0.14, c.col((0.20, 0.45, 0.85)), lift=0.1)
    c.circle(-0.28, 0.58, 0.07, c.col((1, 1, 1)), lift=0)
    for u in (-0.62, 0.0, 0.70):
        c.circle(u, 0.18, 0.205, c.col((0.12, 0.12, 0.15)), lift=0)
        _wheel(c, u, 0.18, 0.17)


@prop("bus", aspect=2.9, place="ground", nominal=0.24, fill=0.74, category="vehicles",
      words=("buses", "coach", "transit", "shuttle", "minibus", "tour", "tours", "tourism", "commute"))
def bus(c, color):
    c.shadow(0.0, 0.02, 2.9, 0.10, alpha=0.30)
    body = c.pick(color, (0.97, 0.75, 0.15))
    c.rect(0, 0.54, 2.8, 0.88, body, r=0.12, lift=0.12)
    c.rect(0, 0.28, 2.8, 0.06, scale(body, 0.7), lift=0)
    glass = c.col((0.68, 0.84, 0.95))
    for k in range(6):
        c.rect(-1.05 + k * 0.40, 0.68, 0.32, 0.30, glass, r=0.03, lift=0.2)
    c.poly([(1.00, 0.40), (1.00, 0.84), (1.34, 0.84), (1.34, 0.40)], glass, lift=0.2)
    c.line(1.17, 0.40, 1.17, 0.84, 0.014, scale(body, 0.6))
    c.poly([(1.36, 0.86), (1.38, 0.50), (1.20, 0.50)], scale(glass, 0.9), lift=0.1)
    c.rect(1.38, 0.34, 0.07, 0.10, c.col((1.0, 0.95, 0.6)), r=0.03, lift=0.1)
    c.rect(-1.38, 0.36, 0.06, 0.12, c.col((0.85, 0.12, 0.15)), r=0.02, lift=0.1)
    c.rect(0.0, 0.93, 2.5, 0.05, c.col((0.15, 0.17, 0.25)), r=0.02, lift=0)
    for u in (-0.85, 0.85):
        c.circle(u, 0.18, 0.25, c.col((0.12, 0.12, 0.15)), lift=0)
        _wheel(c, u, 0.18, 0.21)


@prop("bicycle", aspect=1.9, place="ground", nominal=0.2, fill=0.8, category="vehicles",
      words=("bike", "bikes", "bicycles", "cycling", "cycle", "cyclist", "scooter", "pedal"))
def bicycle(c, color):
    c.shadow(0.0, 0.02, 1.8, 0.08)
    frame = c.pick(color, (0.25, 0.60, 0.85))
    dark = c.col((0.18, 0.19, 0.24))
    for u in (-0.60, 0.60):
        c.ring(u, 0.30, 0.30, 0.04, dark)
        for k in range(8):
            a = math.radians(k * 45)
            c.line(u, 0.30, u + 0.29 * math.cos(a), 0.30 + 0.29 * math.sin(a), 0.008, c.col((0.7, 0.72, 0.78)))
        c.circle(u, 0.30, 0.03, c.col((0.7, 0.72, 0.78)), lift=0)
    A, B, S, H, W = (-0.60, 0.30), (-0.06, 0.28), (-0.22, 0.74), (0.34, 0.76), (0.60, 0.30)
    for p, q in ((A, B), (A, S), (S, B), (S, H), (B, (0.30, 0.64)), (H, W)):
        c.line(p[0], p[1], q[0], q[1], 0.045, frame)
    c.path([(H[0], H[1]), (0.30, 0.90), (0.42, 0.92)], 0.035, dark)
    c.rect(-0.26, 0.80, 0.20, 0.04, dark, r=0.02)
    c.circle(B[0], B[1], 0.085, c.col((0.7, 0.72, 0.78)), lift=0.1)
    c.line(B[0], B[1], B[0] + 0.10, B[1] - 0.12, 0.03, dark)
    c.rect(B[0] + 0.12, B[1] - 0.13, 0.10, 0.03, dark, r=0.01)


@prop("airplane", aspect=3.2, place="sky", nominal=0.14, fill=0.5, category="vehicles",
      words=("plane", "flight", "flights", "airline", "aeroplane", "aircraft", "airport", "jet", "airplanes", "planes", "aviation", "ticket", "tickets", "booking", "holiday", "vacation", "tourist"))
def airplane(c, color):
    stripe = c.pick(color, (0.20, 0.45, 0.90))
    white = c.col((0.98, 0.98, 1.0))
    c.poly([(-1.30, 0.55), (-1.55, 1.05), (-1.30, 1.05), (-0.90, 0.58)], stripe, lift=0.1)                # tail fin
    c.poly([(-1.25, 0.48), (-1.55, 0.62), (-1.35, 0.66), (-0.9, 0.52)], scale(stripe, 0.8), lift=0.05)      # tailplane
    c.poly([(-0.25, 0.46), (-0.60, 0.05), (-0.25, 0.05), (0.35, 0.44)], scale(white, 0.82), lift=0.0)        # far wing
    c.ellipse(0, 0.5, 1.55, 0.20, white, lift=0.12)
    c.poly([(1.35, 0.52), (1.62, 0.46), (1.35, 0.38)], white, lift=0.1)
    c.rect(0, 0.45, 2.9, 0.035, stripe, lift=0)
    for k in range(10):
        c.circle(-0.95 + k * 0.17, 0.55, 0.028, c.col((0.45, 0.65, 0.88)), lift=0.1)
    c.poly([(1.02, 0.60), (1.28, 0.55), (1.05, 0.52)], c.col((0.45, 0.65, 0.88)), lift=0.1)
    c.poly([(0.0, 0.46), (-0.45, 0.0), (-0.05, 0.0), (0.60, 0.44)], white, lift=0.1)                         # near wing
    c.poly([(0.0, 0.46), (-0.45, 0.0), (-0.25, 0.0), (0.2, 0.45)], scale(white, 0.9), lift=0.0)
    c.ellipse(0.18, 0.18, 0.16, 0.07, c.col((0.7, 0.72, 0.78)), lift=0.1)
