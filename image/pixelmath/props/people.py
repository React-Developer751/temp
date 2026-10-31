"""Flat-illustration people: customers, students, doctors, chefs, teams, yoga, couples."""
import math

from .core import WHITE, mix, prop, scale

SKIN = [(0.99, 0.84, 0.70), (0.93, 0.74, 0.58), (0.80, 0.59, 0.42), (0.62, 0.42, 0.28), (0.45, 0.30, 0.20)]
HAIR = [(0.12, 0.09, 0.08), (0.30, 0.18, 0.10), (0.55, 0.35, 0.15), (0.85, 0.70, 0.35), (0.45, 0.45, 0.50)]


def _face(c, u, v, r, skin, hair, style, eyes_closed=False):
    if style == "long":
        c.ellipse(u, v - 0.035, r * 1.28, r * 1.55, hair, lift=0.1)
    c.circle(u, v, r, skin, lift=0.08)
    if style == "bun":
        c.circle(u, v + r * 1.15, r * 0.45, hair, lift=0.1)
    c.ellipse(u, v + r * 0.45, r * 1.08, r * 0.62, hair, lift=0.1)               # hair cap
    if style in ("long", "short"):
        c.ellipse(u - r * 0.95, v + r * 0.05, r * 0.25, r * 0.65, hair, lift=0.0)
        c.ellipse(u + r * 0.95, v + r * 0.05, r * 0.25, r * 0.65, hair, lift=0.0)
    dark = c.col((0.16, 0.12, 0.12))
    for sgn in (-1, 1):
        if eyes_closed:
            c.arc(u + sgn * r * 0.38, v - r * 0.02, r * 0.17, 200, 340, r * 0.07, dark)
        else:
            c.circle(u + sgn * r * 0.38, v - r * 0.02, r * 0.10, dark, lift=0)
    c.arc(u, v - r * 0.22, r * 0.30, 205, 335, r * 0.08, c.col((0.7, 0.25, 0.25)))


def _figure(c, shirt, pants, skin=None, hair=None, style="short", arms="down", extras=()):
    rng = c.rng
    skin = skin or c.col(rng.choice(SKIN))
    hair = hair or c.col(rng.choice(HAIR))
    # legs and shoes
    for sgn in (-1, 1):
        c.rect(sgn * 0.065, 0.25, 0.115, 0.50, pants, r=0.04, lift=0.12)
        c.ellipse(sgn * 0.075, 0.025, 0.085, 0.032, c.col((0.18, 0.18, 0.22)), lift=0.1)
    # torso and arms
    c.poly([(-0.16, 0.78), (0.16, 0.78), (0.135, 0.46), (-0.135, 0.46)], shirt, lift=0.12)
    c.circle(-0.155, 0.745, 0.05, shirt, lift=0.1)
    c.circle(0.155, 0.745, 0.05, shirt, lift=0.1)
    for sgn in (-1, 1):
        end = (sgn * 0.205, 0.50) if arms == "down" else (sgn * 0.12, 0.60)
        c.path([(sgn * 0.17, 0.74), (sgn * 0.19, 0.62), end], 0.062, shirt, smooth=False)
        c.circle(end[0], end[1] - 0.01, 0.034, skin, lift=0.05)
    c.rect(0, 0.80, 0.055, 0.06, scale(skin, 0.92), lift=0)                       # neck
    _face(c, 0, 0.885, 0.088, skin, hair, style)
    return skin, hair


@prop("person", aspect=0.5, place="ground", nominal=0.5, category="people",
      words=("man", "woman", "people", "customer", "customers", "client", "clients", "employee", "user", "users", "human", "lady", "guy", "men", "women", "persons", "visitor", "buyer", "shopper", "family"))
def person(c, color):
    c.shadow(0.0, 0.01, 0.5, 0.06)
    shirt = c.pick(color, (0.22, 0.62, 0.78))
    _figure(c, shirt, c.col((0.25, 0.30, 0.45)), style=c.rng.choice(("short", "long", "bun")))


@prop("student", aspect=0.6, place="ground", nominal=0.5, category="people",
      words=("students", "learner", "learners", "pupil", "pupils", "graduate", "scholar", "undergraduate", "tutor", "tutoring", "teacher", "coaching", "classroom", "exam", "exams", "school", "college"))
def student(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    shirt = c.pick(color, (0.93, 0.55, 0.25))
    skin, hair = _figure(c, shirt, c.col((0.25, 0.30, 0.45)), style="short", arms="down")
    navy = c.col((0.12, 0.15, 0.30))
    c.ellipse(0, 0.955, 0.075, 0.03, navy, lift=0.05)
    c.poly([(-0.17, 0.985), (0.0, 1.03), (0.17, 0.985), (0.0, 0.945)], scale(navy, 1.1), lift=0.1)
    c.path([(0.14, 0.985), (0.17, 0.93), (0.165, 0.89)], 0.012, c.col((0.95, 0.78, 0.2)), smooth=False)
    c.circle(0.165, 0.885, 0.015, c.col((0.95, 0.78, 0.2)), lift=0)
    bk = c.col((0.25, 0.50, 0.85))
    c.rect(-0.215, 0.50, 0.11, 0.15, bk, r=0.01, lift=0.1, alpha=1.0)
    c.rect(-0.18, 0.50, 0.015, 0.14, c.col((0.97, 0.94, 0.86)), lift=0)
    c.rect(-0.215, 0.52, 0.06, 0.02, c.col((1, 0.92, 0.55)), lift=0)


@prop("doctor", aspect=0.55, place="ground", nominal=0.5, category="people",
      words=("physician", "nurse", "surgeon", "medic", "therapist", "therapy", "counselling", "counseling", "psychologist"))
def doctor(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    scrub = c.pick(color, (0.20, 0.66, 0.74))
    coat = c.col((0.97, 0.98, 1.0))
    skin = c.col(c.rng.choice(SKIN))
    for sgn in (-1, 1):
        c.rect(sgn * 0.065, 0.25, 0.115, 0.50, c.col((0.30, 0.45, 0.62)), r=0.04, lift=0.12)
        c.ellipse(sgn * 0.075, 0.025, 0.085, 0.032, c.col((0.95, 0.95, 0.97)), lift=0.1)
    c.poly([(-0.17, 0.78), (0.17, 0.78), (0.15, 0.30), (-0.15, 0.30)], coat, lift=0.06)
    c.poly([(-0.06, 0.78), (0.06, 0.78), (0.0, 0.62)], scrub, lift=0.1)
    for sgn in (-1, 1):
        c.circle(sgn * 0.17, 0.745, 0.05, coat, lift=0.05)
        c.path([(sgn * 0.18, 0.74), (sgn * 0.20, 0.62), (sgn * 0.215, 0.50)], 0.065, coat, smooth=False)
        c.circle(sgn * 0.215, 0.485, 0.034, skin, lift=0.05)
    c.line(0, 0.62, 0, 0.30, 0.008, c.col((0.78, 0.8, 0.86)))
    c.rect(0.09, 0.45, 0.07, 0.05, c.col((0.88, 0.9, 0.95)), r=0.01, lift=0)
    c.path([(-0.07, 0.76), (-0.08, 0.60), (0.0, 0.54), (0.08, 0.60), (0.07, 0.76)], 0.014, c.col((0.25, 0.27, 0.32)))
    c.circle(0.0, 0.52, 0.025, c.col((0.7, 0.72, 0.78)), lift=0.1)
    c.rect(-0.09, 0.62, 0.06, 0.06, c.col((0.88, 0.18, 0.22)), r=0.01, lift=0)
    c.rect(-0.09, 0.62, 0.035, 0.012, WHITE, lift=0)
    c.rect(-0.09, 0.62, 0.012, 0.035, WHITE, lift=0)
    c.rect(0, 0.80, 0.055, 0.06, scale(skin, 0.92), lift=0)
    _face(c, 0, 0.885, 0.088, skin, c.col(c.rng.choice(HAIR)), c.rng.choice(("short", "bun")))


@prop("chef", aspect=0.6, place="ground", nominal=0.5, category="people",
      words=("cook", "baker", "barista", "chefs", "kitchen", "cooking", "waiter", "waitress", "catering", "caterer", "bartender"))
def chef(c, color):
    c.shadow(0.0, 0.01, 0.55, 0.06)
    shirt = c.pick(color, (0.97, 0.97, 0.98))
    skin = c.col(c.rng.choice(SKIN))
    _figure(c, shirt, c.col((0.30, 0.30, 0.36)), skin=skin, style="short")
    c.poly([(-0.10, 0.62), (0.10, 0.62), (0.13, 0.28), (-0.13, 0.28)], c.col((0.25, 0.28, 0.38)), lift=0.08)
    c.rect(0, 0.46, 0.20, 0.014, c.col((0.7, 0.72, 0.8)), lift=0)
    c.poly([(-0.05, 0.78), (0.05, 0.78), (0.0, 0.70)], c.col((0.88, 0.2, 0.22)), lift=0)
    white = c.col((1.0, 1.0, 1.0))
    c.rect(0, 0.945, 0.17, 0.06, white, r=0.01, lift=0.04)
    for u, v, r in ((-0.075, 1.0, 0.055), (0.0, 1.03, 0.065), (0.075, 1.0, 0.055)):
        c.circle(u, v, r, white, lift=0.05)


@prop("businessman", aspect=0.5, place="ground", nominal=0.5, category="people",
      words=("businesswoman", "manager", "ceo", "consultant", "lawyer", "advocate", "agent", "executive", "professional", "entrepreneur", "founder", "boss", "broker", "accountant", "banker", "seller", "realtor", "owner"))
def businessman(c, color):
    c.shadow(0.0, 0.01, 0.5, 0.06)
    suit = c.pick(color, (0.17, 0.22, 0.40))
    skin = c.col(c.rng.choice(SKIN))
    _figure(c, suit, scale(suit, 0.9), skin=skin, style=c.rng.choice(("short", "long")))
    c.poly([(-0.06, 0.78), (0.06, 0.78), (0.0, 0.60)], c.col((0.98, 0.98, 1.0)), lift=0)
    c.poly([(-0.018, 0.77), (0.018, 0.77), (0.03, 0.55), (0.0, 0.50), (-0.03, 0.55)], c.col((0.85, 0.18, 0.22)), lift=0.1)
    c.line(0, 0.78, 0, 0.46, 0.01, scale(suit, 0.6))
    c.rect(0.235, 0.40, 0.13, 0.10, c.col((0.45, 0.28, 0.16)), r=0.015, lift=0.12)
    c.path([(0.205, 0.45), (0.235, 0.485), (0.265, 0.45)], 0.014, c.col((0.3, 0.2, 0.12)), smooth=False)


@prop("team", aspect=1.4, place="ground", nominal=0.5, category="people",
      words=("staff", "group", "meeting", "colleagues", "teamwork", "crowd", "employees", "teams", "audience", "community", "workers", "crew", "company", "agency", "firm"))
def team(c, color):
    c.shadow(0.0, 0.01, 1.3, 0.07)
    cols = [(0.22, 0.62, 0.78), (0.93, 0.55, 0.25), (0.55, 0.40, 0.80), (0.30, 0.72, 0.45)]
    order = [(-0.52, 0.88, 0), (0.52, 0.88, 1), (0.0, 1.0, 2)]
    for du, sc, k in order:
        sub = c.sub(du, 0.0, sc)
        _figure(sub, sub.pick(color, cols[k]) if k == 2 or color is None else sub.col(cols[k]), sub.col((0.25, 0.30, 0.45)), style=("short", "long", "bun")[k])


@prop("yogi", aspect=1.1, place="ground", nominal=0.4, fill=0.9, category="people",
      words=("yoga", "meditation", "meditate", "meditating", "mindfulness", "zen", "relax", "relaxation", "wellness", "calm", "peace", "spiritual", "pilates", "stretching"))
def yogi(c, color):
    c.glow(0, 0.50, 0.75, c.col((1.0, 0.85, 0.55)), 0.35)
    c.ring(0, 0.50, 0.52, 0.015, c.col((1.0, 0.95, 0.8)), alpha=0.45)
    mat = c.pick(color, (0.25, 0.66, 0.62))
    c.rect(0, 0.035, 1.05, 0.06, mat, r=0.03, lift=0.12)
    pants = c.col((0.35, 0.38, 0.62))
    skin = c.col(c.rng.choice(SKIN))
    c.ellipse(-0.20, 0.13, 0.33, 0.085, scale(pants, 0.9), angle=8, lift=0.12)
    c.ellipse(0.20, 0.13, 0.33, 0.085, pants, angle=-8, lift=0.12)
    c.circle(-0.43, 0.10, 0.05, skin, lift=0.05)
    c.circle(0.43, 0.10, 0.05, skin, lift=0.05)
    top = c.col((0.95, 0.55, 0.40))
    c.poly([(-0.17, 0.58), (0.17, 0.58), (0.20, 0.16), (-0.20, 0.16)], top, lift=0.12)
    c.circle(0, 0.60, 0.17, top, lift=0.05)
    for sgn in (-1, 1):
        c.path([(sgn * 0.17, 0.57), (sgn * 0.27, 0.38), (sgn * 0.34, 0.20)], 0.07, top, smooth=False)
        c.circle(sgn * 0.34, 0.18, 0.04, skin, lift=0.05)
    c.rect(0, 0.64, 0.06, 0.06, scale(skin, 0.92), lift=0)
    _face(c, 0, 0.74, 0.095, skin, c.col(c.rng.choice(HAIR)), "bun", eyes_closed=True)


@prop("weddingcouple", aspect=0.95, place="ground", nominal=0.5, category="people",
      words=("wedding", "bride", "groom", "marriage", "bridal", "engagement", "married", "newlyweds", "romance", "romantic", "honeymoon", "valentine", "weddings", "love"))
def weddingcouple(c, color):
    c.shadow(0.0, 0.01, 0.95, 0.06)
    skin1, skin2 = c.col(SKIN[1]), c.col(SKIN[2])
    white = c.col((1.0, 0.99, 0.99))
    # bride (left)
    bu = -0.20
    c.ellipse(bu - 0.02, 0.80, 0.16, 0.22, mix(white, c.col((0.8, 0.85, 1.0)), 0.3), lift=0.0, alpha=0.5)     # veil
    c.poly([(bu - 0.11, 0.56), (bu + 0.11, 0.56), (bu + 0.30, 0.0), (bu - 0.30, 0.0)], white, lift=0.10)
    c.poly([(bu - 0.11, 0.78), (bu + 0.11, 0.78), (bu + 0.10, 0.56), (bu - 0.10, 0.56)], white, lift=0.06)
    c.line(bu - 0.20, 0.10, bu - 0.12, 0.54, 0.008, c.col((0.85, 0.86, 0.92)))
    c.line(bu + 0.20, 0.10, bu + 0.12, 0.54, 0.008, c.col((0.85, 0.86, 0.92)))
    c.rect(bu, 0.58, 0.22, 0.03, c.col((0.95, 0.60, 0.72)), lift=0)
    c.rect(bu, 0.80, 0.045, 0.05, scale(skin1, 0.92), lift=0)
    _face(c, bu, 0.875, 0.08, skin1, c.col((0.30, 0.18, 0.10)), "long")
    for k in range(3):
        c.circle(bu + 0.17 + k * 0.025, 0.50 + (k % 2) * 0.03, 0.035, c.col(((0.95, 0.4, 0.55), (1.0, 0.7, 0.8), (0.9, 0.3, 0.45))[k]), lift=0.1)
    # groom (right)
    gu = 0.24
    suit = c.pick(color, (0.14, 0.15, 0.22))
    for sgn in (-1, 1):
        c.rect(gu + sgn * 0.055, 0.24, 0.10, 0.48, scale(suit, 0.9), r=0.03, lift=0.1)
        c.ellipse(gu + sgn * 0.065, 0.025, 0.075, 0.03, c.col((0.08, 0.08, 0.10)), lift=0.1)
    c.poly([(gu - 0.14, 0.76), (gu + 0.14, 0.76), (gu + 0.12, 0.44), (gu - 0.12, 0.44)], suit, lift=0.12)
    c.poly([(gu - 0.05, 0.76), (gu + 0.05, 0.76), (gu, 0.58)], c.col((0.98, 0.98, 1.0)), lift=0)
    c.poly([(gu - 0.03, 0.74), (gu + 0.03, 0.74), (gu + 0.015, 0.70), (gu - 0.015, 0.70)], c.col((0.85, 0.18, 0.22)), lift=0)
    c.circle(gu + 0.08, 0.66, 0.015, c.col((0.95, 0.4, 0.55)), lift=0)
    for sgn in (-1, 1):
        c.path([(gu + sgn * 0.15, 0.73), (gu + sgn * 0.17, 0.60), (gu + sgn * 0.18, 0.48)], 0.055, suit, smooth=False)
        c.circle(gu + sgn * 0.18, 0.465, 0.03, skin2, lift=0.05)
    c.rect(gu, 0.79, 0.05, 0.05, scale(skin2, 0.92), lift=0)
    _face(c, gu, 0.865, 0.08, skin2, c.col((0.10, 0.08, 0.08)), "short")
    c.poly([(0, 0.98), (-0.045, 1.02), (-0.025, 1.05), (0, 1.03), (0.025, 1.05), (0.045, 1.02)], c.col((0.95, 0.3, 0.45)), lift=0.1)
