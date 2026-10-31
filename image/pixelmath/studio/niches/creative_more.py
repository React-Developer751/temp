"""More creative / cultural niches: dj-sound, video-editing, drone-photography, temple.

Props are prefixed ``crt_``. Shared fast fills (``_crect`` scanline rectangles, ``_fill_quad`` translucent quads, ``_G`` rotated frame,
``box3d``) come from digital_edu; everything else is drawn here with the stage / craft helpers.
No text, letters or numbers anywhere: signs and screens are plain bars and shapes.
"""
import math

from .. import craft
from ..craft import BLACK, WHITE, ao, gloss, soft_disc
from ..niches import niche
from ..palette import make_palette
from ..stage import sprop
from ...raster import mix, scale
from .digital_edu import _G, _crect, _fill_quad, box3d

STEEL = (0.62, 0.65, 0.70)
BRASS = (0.84, 0.60, 0.20)
GOLD = (0.90, 0.72, 0.30)
MARI = ((0.98, 0.52, 0.05), (1.0, 0.66, 0.08), (0.95, 0.40, 0.04), (1.0, 0.78, 0.18))
_DEFAULT = {}


def _pal(color, accent, mood):
    """Props are drawn with color=S.pal; when called without a palette fall back to a default one."""
    if color is not None and hasattr(color, "accent"):
        return color
    key = (accent, mood)
    if key not in _DEFAULT:
        _DEFAULT[key] = make_palette(accent, mood)
    return _DEFAULT[key]


def _fq(c, pts, col, alpha):
    """Translucent un-antialiased quad in prop units (light beams, sheens)."""
    _fill_quad(c.cv, [(c.X(u), c.Y(v)) for u, v in pts], col, alpha)


# ====================================================================================================== DJ AND SOUND
@sprop("crt_speaker", aspect=0.62, fill=0.98)
def speaker(c, color):
    P = _pal(color, "#c0607a", "light")
    ao(c, 0.0, 0.0, 0.62, 0.16, 0.45)
    for s in (-1, 1):                                                         # tripod legs and pole
        c.line(s * 0.03, 0.30, s * 0.27, 0.0, 0.026, (0.12, 0.12, 0.14))
    c.line(0.0, 0.30, 0.0, 0.0, 0.026, (0.18, 0.18, 0.21))
    _crect(c, 0.0, 0.34, 0.05, 0.16, STEEL, lift=0.3)
    body = (0.09, 0.09, 0.11)
    _crect(c, 0.0, 0.67, 0.50, 0.64, scale(body, 0.7), r=0.05, lift=0.0)
    _crect(c, 0.0, 0.67, 0.485, 0.625, body, r=0.045, lift=0.22)
    c.line(-0.235, 0.40, -0.235, 0.94, 0.012, mix(body, WHITE, 0.45), 0.55)
    c.line(-0.215, 0.975, 0.215, 0.975, 0.008, mix(body, WHITE, 0.4), 0.55)
    c.line(-0.18, 0.36, 0.18, 0.36, 0.01, P.accent, 0.9)                     # accent trim along the foot of the cabinet
    # tweeter horn slot at the top
    _crect(c, 0.0, 0.89, 0.30, 0.075, (0.03, 0.03, 0.04), r=0.02, lift=0.0)
    _crect(c, 0.0, 0.885, 0.26, 0.04, mix(STEEL, BLACK, 0.55), r=0.015, lift=0.35)
    # two woofers: silver rim, black cone, dust cap, gloss
    for v, r in ((0.725, 0.145), (0.505, 0.125)):
        c.ellipse(0.0, v, r + 0.014, r + 0.014, mix(STEEL, BLACK, 0.4), lift=0.25)
        c.ellipse(0.0, v, r, r, (0.05, 0.05, 0.06), lift=0.0)
        c.ellipse(0.0, v, r * 0.78, r * 0.78, (0.13, 0.13, 0.15), lift=0.3)
        c.ellipse(0.0, v, r * 0.40, r * 0.40, (0.20, 0.20, 0.23), lift=0.35)
        c.ellipse(0.0, v, r * 0.16, r * 0.16, mix(STEEL, WHITE, 0.2), lift=0.3)
        craft.arc(c, 0.0, v, r * 0.9, r * 0.9, 110, 165, 0.012, WHITE, 0.30, 5)
    gloss(c, -0.12, 0.90, 0.10, 0.05, 15, 0.25)


@sprop("crt_sub", aspect=1.05, fill=0.98)
def subwoofer(c, color):
    P = _pal(color, "#c0607a", "light")
    ao(c, 0.0, 0.0, 1.1, 0.30, 0.5)
    body = (0.08, 0.08, 0.10)
    box3d(c, 0.0, 0.02, 0.88, 0.90, 0.22, body, mix(body, WHITE, 0.14), scale(body, 0.6), lift=0.18)
    for s in (-1, 1):                                                         # metal corners and handles
        c.rect(s * 0.40, 0.05, 0.07, 0.07, mix(STEEL, BLACK, 0.5), lift=0.3)
        _crect(c, s * 0.34, 0.50, 0.02, 0.22, (0.03, 0.03, 0.04), r=0.01)
    c.ellipse(0.0, 0.50, 0.37, 0.37, mix(STEEL, BLACK, 0.4), lift=0.25)
    c.ellipse(0.0, 0.50, 0.345, 0.345, (0.04, 0.04, 0.05), lift=0.0)
    c.ellipse(0.0, 0.50, 0.27, 0.27, (0.12, 0.12, 0.14), lift=0.3)
    c.ellipse(0.0, 0.50, 0.12, 0.12, (0.20, 0.20, 0.23), lift=0.3)
    c.ellipse(0.0, 0.50, 0.055, 0.055, P.accent, lift=0.3)
    craft.arc(c, 0.0, 0.50, 0.30, 0.30, 100, 160, 0.02, WHITE, 0.25, 6)
    c.line(-0.30, 0.89, 0.30, 0.89, 0.012, P.accent, 0.85)


@sprop("crt_mic_stand", aspect=0.42, fill=0.98)
def mic_stand(c, color):
    P = _pal(color, "#c0607a", "light")
    ao(c, 0.0, 0.0, 0.42, 0.12, 0.45)
    c.ellipse(0.0, 0.025, 0.19, 0.045, (0.10, 0.10, 0.12), lift=0.25)
    _crect(c, 0.0, 0.50, 0.026, 0.95, (0.15, 0.15, 0.18), lift=0.3)
    c.line(-0.0, 0.50, 0.0, 0.50, 0.03, STEEL, 0.9)
    c.line(0.0, 0.90, 0.0, 0.88, 0.05, (0.10, 0.10, 0.12))
    # wireless handheld: mesh ball head, grip, accent ring
    c.poly([(-0.045, 0.88), (0.045, 0.88), (0.036, 0.62), (-0.036, 0.62)], (0.10, 0.10, 0.12), lift=0.35)
    c.ellipse(0.0, 0.96, 0.075, 0.075, mix(STEEL, BLACK, 0.3), lift=0.30)
    for k in range(5):
        c.line(-0.06 + k * 0.03, 0.915, -0.06 + k * 0.03, 1.0, 0.004, mix(STEEL, BLACK, 0.55), 0.7)
    c.ellipse(0.0, 0.89, 0.052, 0.014, P.accent, lift=0.25)
    c.line(-0.020, 0.86, -0.018, 0.66, 0.008, WHITE, 0.25)


def _beam(c, u, v, ang, length, w0, w1, col, alpha):
    """A soft light beam: three nested translucent quads from (u, v) at ang degrees (90 = straight up)."""
    a = math.radians(ang)
    du, dv = math.cos(a), math.sin(a)
    pu, pv = -dv, du
    for k, (f, al) in enumerate(((1.0, 0.45), (0.62, 0.55), (0.30, 0.7))):
        eu, ev = u + du * length, v + dv * length
        _fq(c, [(u + pu * w0 * f, v + pv * w0 * f), (eu + pu * w1 * f, ev + pv * w1 * f), (eu - pu * w1 * f, ev - pv * w1 * f), (u - pu * w0 * f, v - pv * w0 * f)],
            col, alpha * al)


@sprop("crt_head", aspect=0.5, fill=0.98)
def moving_head(c, color):
    """A moving-head light on a small base plate; it throws a soft beam up and across."""
    P = _pal(color, "#c0607a", "light")
    dark = P.mood == "dark"
    tone = mix(P.accent_light, WHITE, 0.25)
    _beam(c, 0.0, 0.80, 100, 3.2, 0.06, 0.62 if dark else 0.42, tone, 0.40 if dark else 0.20)
    ao(c, 0.0, 0.0, 0.6, 0.18, 0.4)
    _crect(c, 0.0, 0.05, 0.72, 0.10, (0.10, 0.10, 0.12), r=0.03, lift=0.3)
    _crect(c, 0.0, 0.22, 0.20, 0.26, (0.14, 0.14, 0.17), r=0.04, lift=0.3)
    for s in (-1, 1):
        c.poly([(s * 0.32, 0.12), (s * 0.40, 0.70), (s * 0.28, 0.70), (s * 0.22, 0.12)], (0.11, 0.11, 0.13), lift=0.3)
    c.ellipse(0.0, 0.60, 0.30, 0.34, (0.16, 0.16, 0.19), lift=0.35, angle=-10)
    c.ellipse(-0.04, 0.82, 0.24, 0.10, mix(tone, WHITE, 0.55), lift=0.0, angle=-10)
    c.glow(-0.04, 0.86, 0.60, tone, 0.60)


@sprop("crt_dhol", aspect=1.45, fill=0.98)
def dhol(c, color):
    P = _pal(color, "#c0607a", "light")
    ao(c, 0.0, 0.0, 1.5, 0.30, 0.5)
    wood = (0.50, 0.29, 0.14)
    cloth = P.accent
    # barrel lying on the floor, left head towards us
    c.poly([(-0.55, 0.12), (-0.20, 0.0), (0.30, 0.0), (0.58, 0.07), (0.58, 0.63), (0.30, 0.68), (-0.20, 0.69), (-0.55, 0.88)], wood, lift=0.30)
    c.poly([(-0.20, 0.0), (0.30, 0.0), (0.30, 0.68), (-0.20, 0.69)], cloth, lift=0.28)
    for v in (0.06, 0.62):
        c.line(-0.20, v, 0.30, v, 0.014, GOLD, 0.9)
    for k in range(7):
        c.line(-0.14 + k * 0.07, 0.02, -0.10 + k * 0.07, 0.66, 0.008, mix(cloth, WHITE, 0.4), 0.28)
    c.ellipse(0.58, 0.35, 0.075, 0.29, scale(wood, 0.62), lift=0.2)
    c.ellipse(0.585, 0.35, 0.055, 0.265, (0.88, 0.80, 0.64), lift=0.1)
    # near head: skin, hoop, lacing
    c.ellipse(-0.55, 0.50, 0.12, 0.40, scale(wood, 0.55), lift=0.2)
    c.ellipse(-0.56, 0.50, 0.095, 0.37, (0.93, 0.88, 0.74), lift=0.12)
    c.ellipse(-0.56, 0.50, 0.06, 0.27, (0.88, 0.82, 0.68), lift=0.0, alpha=0.6)
    c.ellipse(-0.585, 0.58, 0.022, 0.12, WHITE, lift=0.0, alpha=0.45)
    for k in range(10):                                                       # rope lacing zig-zag
        v0 = 0.12 + k * 0.073
        c.line(-0.50, v0, -0.36, v0 + 0.073 * (1 if k % 2 == 0 else -1) * 0.9, 0.012, (0.88, 0.80, 0.62), 0.95)
    # two sticks crossed in front
    c.line(-0.30, 0.03, 0.22, 0.15, 0.016, (0.80, 0.62, 0.34), 1.0)
    c.line(-0.30, 0.15, 0.22, 0.04, 0.012, (0.70, 0.52, 0.26), 1.0)
    c.ellipse(0.22, 0.15, 0.03, 0.03, scale(cloth, 0.8), lift=0.2)
    gloss(c, -0.1, 0.55, 0.30, 0.08, 0, 0.22)


@sprop("crt_spark", aspect=0.9, fill=0.98)
def cold_spark(c, color):
    P = _pal(color, "#c0607a", "light")
    dark = P.mood == "dark"
    rng = c.rng
    ao(c, 0.0, 0.0, 0.30, 0.10, 0.4)
    _crect(c, 0.0, 0.07, 0.10, 0.14, (0.10, 0.10, 0.12), r=0.012, lift=0.3)
    c.line(-0.04, 0.10, -0.04, 0.02, 0.01, STEEL, 0.5)
    c.glow(0.0, 0.22, 0.26, (1.0, 0.82, 0.45), 0.5 if dark else 0.30)
    for k in range(34):
        a = math.radians(90 + rng.uniform(-38, 38))
        L = rng.uniform(0.35, 0.95)
        w = 0.012 * (1.0 - L * 0.4)
        c.line(0.0, 0.15, math.cos(a) * L * 0.55, 0.15 + math.sin(a) * L, w, (1.0, 0.92, 0.65) if k % 3 else WHITE, 0.9 if dark else 0.7)
    for k in range(12):
        c.circle(rng.uniform(-0.28, 0.28), rng.uniform(0.35, 0.98), 0.012, WHITE, lift=0.0, alpha=0.9)


@sprop("crt_dj_booth", aspect=1.95, fill=0.97)
def dj_booth(c, color):
    P = _pal(color, "#c0607a", "light")
    dark = P.mood == "dark"
    rng = c.rng
    ao(c, 0.0, 0.0, 1.9, 0.35, 0.5)
    c.glow(0.0, 0.03, 0.9, P.accent_light, 0.42 if dark else 0.14)
    # draped table front in accent fabric with gold trim and pleats
    cloth = mix(P.accent, P.ink, 0.30) if dark else P.accent
    _crect(c, 0.0, 0.26, 1.64, 0.52, cloth, lift=0.18)
    for k in range(17):
        x = -0.78 + k * 0.0975
        c.line(x, 0.01, x + 0.01, 0.50, 0.020 if k % 2 else 0.012, scale(cloth, 0.78 if k % 2 else 1.18), 0.55)
    c.line(-0.82, 0.015, 0.82, 0.015, 0.014, GOLD, 0.95)
    c.line(-0.82, 0.49, 0.82, 0.49, 0.012, GOLD, 0.95)
    _crect(c, 0.0, 0.535, 1.70, 0.05, (0.96, 0.94, 0.90) if not dark else (0.22, 0.22, 0.26), r=0.012, lift=0.15)
    c.line(-0.84, 0.56, 0.84, 0.56, 0.006, WHITE, 0.4)
    # controller deck (trapezoid), two jog platters, central mixer
    body = (0.08, 0.08, 0.10)
    c.poly([(-0.58, 0.56), (0.58, 0.56), (0.52, 0.76), (-0.52, 0.76)], body, lift=0.25)
    c.line(-0.58, 0.565, 0.58, 0.565, 0.008, mix(body, WHITE, 0.4), 0.7)
    for s in (-1, 1):
        u = s * 0.33
        c.ellipse(u, 0.655, 0.20, 0.072, (0.02, 0.02, 0.03), lift=0.0)
        c.ellipse(u, 0.662, 0.185, 0.066, (0.14, 0.14, 0.17), lift=0.35)
        c.ellipse(u, 0.664, 0.155, 0.055, (0.07, 0.07, 0.09), lift=0.2)
        c.ellipse(u, 0.664, 0.075, 0.026, P.accent, lift=0.3)
        c.ellipse(u, 0.666, 0.020, 0.008, WHITE, lift=0.0, alpha=0.8)
        craft.arc(c, u, 0.664, 0.17, 0.060, 20, 75, 0.008, WHITE, 0.35, 5)
        for k in range(4):                                                     # performance pads
            _crect(c, u - 0.12 + k * 0.08, 0.575, 0.06, 0.022, [P.accent_light, (1.0, 0.8, 0.4), P.accent, (0.5, 0.8, 1.0)][k], r=0.006, lift=0.2)
    c.poly([(-0.14, 0.58), (0.14, 0.58), (0.12, 0.745), (-0.12, 0.745)], (0.12, 0.12, 0.15), lift=0.3)
    for k in range(4):
        _crect(c, -0.09 + k * 0.06, 0.64, 0.016, 0.07, (0.03, 0.03, 0.04), r=0.005, lift=0.0)
        _crect(c, -0.09 + k * 0.06, 0.62 + 0.03 * (k % 3), 0.034, 0.016, WHITE if k % 2 else P.accent_light, r=0.004, lift=0.2)
    for k in range(3):
        c.circle(-0.06 + k * 0.06, 0.725, 0.014, mix(STEEL, WHITE, 0.2), lift=0.3)
    # laptop at the far left: lid with waveform screen, glowing
    _crect(c, -0.70, 0.815, 0.34, 0.215, (0.58, 0.60, 0.65), r=0.012, lift=0.2)
    _crect(c, -0.70, 0.815, 0.31, 0.19, (0.04, 0.05, 0.08), r=0.008, lift=0.0)
    for k in range(18):
        h = 0.018 + 0.075 * abs(math.sin(k * 0.8 + 1.0)) * (0.6 + 0.4 * ((k * 7) % 5) / 4.0)
        _crect(c, -0.835 + k * 0.0155, 0.80, 0.009, h, P.accent_light if k % 3 else mix(P.accent_light, WHITE, 0.5), lift=0.0)
    _crect(c, -0.70, 0.745, 0.29, 0.012, (0.30, 0.8, 0.9), lift=0.0, alpha=0.8)
    c.line(-0.86, 0.765, -0.54, 0.765, 0.01, (0.55, 0.57, 0.62), 0.9)
    c.glow(-0.70, 0.80, 0.30, P.accent_light, 0.18 if not dark else 0.34)
    # headphones resting on the right of the table
    hu, hv = 0.72, 0.60
    craft.arc(c, hu, hv + 0.06, 0.15, 0.17, 5, 175, 0.032, (0.12, 0.12, 0.14), 1.0, 12)
    craft.arc(c, hu, hv + 0.06, 0.15, 0.17, 40, 140, 0.014, P.accent, 0.9, 8)
    for s in (-1, 1):
        c.ellipse(hu + s * 0.155, hv + 0.035, 0.046, 0.075, (0.10, 0.10, 0.12), lift=0.35)
        c.ellipse(hu + s * 0.155, hv + 0.035, 0.026, 0.050, P.accent, lift=0.3)
    gloss(c, -0.2, 0.70, 0.3, 0.05, 0, 0.18)


@niche("dj-sound", "Wedding DJ and sound", subjects=("crt_dj_booth",),
       strong=("wedding dj", "dj service", "dj and sound", "dj sound", "wedding dj and sound", "dj booking", "dj party", "dj for wedding", "sangeet dj",
               "dj sound and light", "baraat dj", "dj ki booking", "dj wala", "dj sound system", "वेडिंग डीजे", "डीजे वाला", "डीजे और साउंड", "साउंड सिस्टम",
               "डीजे बुकिंग"),
       weak=("dj", "sound", "speakers", "mixer", "music system", "dance floor", "laser light", "baraat", "dhol", "party music", "संगीत", "साउंड"),
       avoid=("music academy", "music classes", "learn music", "guitar class", "singing class", "event planner", "wedding planner", "banquet", "photographer",
              "संगीत सिखाएं", "म्यूजिक क्लास"),
       accent="#c0607a", mood="light", group="events")
def dj_sound(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    gold_l = (1.0, 0.86, 0.55)
    u0, u1 = S.visible_u()
    u0, u1 = u0 - 0.2, u1 + 0.2
    mid = (u0 + u1) / 2
    floor_a = mix(P.paper, P.accent_light, 0.18) if not dark else mix(P.accent_dark, P.ink, 0.5)
    floor_b = mix(P.paper, P.accent_light, 0.50) if not dark else mix(P.accent_dark, P.ink, 0.15)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.58)
        # ivory reception hall: pleated drapes, a pelmet, fairy lights and a big soft stage glow behind the booth
        drape = mix(P.accent_light, P.wall_top, 0.45) if not dark else mix(P.accent_dark, P.wall_top, 0.4)
        n = int((u1 - u0) / 0.125) + 1
        for k in range(n):
            S.rect(u0 + k * 0.125, 0.28, 0.13, 0.62, scale(drape, 1.08 if k % 2 else 0.88), lift=0.0)
        S.rect(mid, 0.00, u1 - u0, 0.10, scale(drape, 0.70), lift=0.0)
        S.glow(1.05, 0.45, 0.95, mix(P.accent_light, WHITE, 0.3), 0.50 if dark else 0.24)
        for k in range(int((u1 - u0) / 0.088)):
            S.circle(u0 + k * 0.088, 0.10 + 0.03 * math.sin(k * 0.8), 0.011, gold_l, alpha=0.95 if dark else 0.7, lift=0, soft=2.0)
        S.bokeh(12, u0, 0.12, u1, 0.55, [gold_l, P.accent_light, (1.0, 0.95, 0.85)], 0.012, 0.04, 0.30 if dark else 0.22)
        # tall flower arrangements in gold urns either side
        for u in (0.30, 1.90):
            S.poly([(u - 0.05, 0.58), (u + 0.05, 0.58), (u + 0.035, 0.46), (u - 0.035, 0.46)], GOLD)
            S.ellipse(u, 0.33, 0.10, 0.11, mix((0.30, 0.52, 0.30), P.wall_top, 0.3), alpha=0.6, lift=0.1)
            for k in range(14):
                a = rng.uniform(0, 6.28)
                r = rng.uniform(0.0, 0.11)
                S.circle(u + math.cos(a) * r, 0.32 + math.sin(a) * r * 0.95, rng.uniform(0.022, 0.04),
                         rng.choice([P.accent_light, (1.0, 0.95, 0.92), gold_l, P.accent]), alpha=0.95, lift=0.1, soft=2.0)
        # dance floor: glossy ivory marble checker with a bright pool of light
        S.floor(0.58, floor_a, scale(floor_a, 0.8))
        S.tiles(u0, 0.58, u1, 1.1, floor_a, floor_b, 0.16)
        S.soft(1.05, 0.86, 1.1, 0.30, mix(P.accent_light, WHITE, 0.3), 0.40 if dark else 0.22, 1.4, add=True)
        S.rect(mid, 0.585, u1 - u0, 0.012, scale(P.wall_bot, 0.6), lift=0.0, alpha=0.6)
    # laser fans through the air behind the cluster (strongest in the dark mood)
    for k, (ua, va, ub, vb) in enumerate(((0.80, 0.34, 0.05, 0.0), (0.84, 0.34, 0.45, 0.0), (1.30, 0.34, 1.7, 0.0), (1.34, 0.34, 2.0, 0.12), (1.26, 0.34, 1.9, 0.5))):
        S.line(ua, va, ub, vb, 0.004, mix(P.accent_light, WHITE, 0.25) if k % 2 else (0.55, 1.0, 0.8), 0.60 if dark else 0.25)
    # the cluster: speakers with moving heads on top, booth in front, sub / dhol / spark fountain / mic at its feet
    S.put("crt_speaker", 0.72, 0.80, 0.46, color=P, shadow=False)
    S.put("crt_speaker", 1.38, 0.80, 0.46, color=P, shadow=False)
    S.put("crt_head", 0.72, 0.345, 0.13, color=P, shadow=False)
    S.put("crt_head", 1.38, 0.345, 0.13, color=P, shadow=False)
    S.put("crt_dj_booth", 1.05, 0.92, 0.45, color=P, subject=True, shadow=False)
    S.put("crt_sub", 0.66, 1.0, 0.21, color=P, shadow=False)
    S.put("crt_dhol", 1.32, 1.01, 0.20, color=P, shadow=False)
    S.put("crt_spark", 0.92, 1.02, 0.30, color=P, shadow=False)
    S.put("crt_mic_stand", 1.50, 1.01, 0.46, color=P, shadow=False)
    S.focus("detail", 0.95, 0.70)
    with S.near(blur=16):
        S.soft(0.45, 1.0, 0.25, 0.10, P.accent, 0.28, 1.2, add=True)
        S.circle(1.70, 0.42, 0.04, gold_l, alpha=0.30 if dark else 0.20, lift=0)


# ====================================================================================================== VIDEO EDITING
def _pic(g, u, v, w, h, P, rng, kind=0):
    """A little 'frame of footage' (plain shapes, no text): sky, sun, ridges. Used for thumbnails, the preview and the camera monitor."""
    skies = ((0.95, 0.62, 0.40), (0.45, 0.65, 0.88), (0.98, 0.82, 0.55), (0.50, 0.38, 0.62))
    sky = skies[kind % 4]
    g.rect(u, v, w, h, sky, lift=0.25)
    g.rect(u, v - h * 0.20, w, h * 0.55, mix(sky, WHITE, 0.35), alpha=0.4)
    g.circle(u + w * (0.18 - 0.12 * (kind % 3)), v + h * 0.12, h * 0.17, (1.0, 0.95, 0.75), lift=0.0)
    ridge = scale(sky, 0.42)
    g.poly([(u - w / 2, v - h / 2), (u - w / 2, v - h * 0.12), (u - w * 0.22, v + h * 0.04), (u + w * 0.02, v - h * 0.14), (u + w * 0.28, v + h * 0.02),
            (u + w / 2, v - h * 0.18), (u + w / 2, v - h / 2)], ridge)
    g.poly([(u - w / 2, v - h / 2), (u - w / 2, v - h * 0.32), (u - w * 0.1, v - h * 0.22), (u + w * 0.3, v - h * 0.36), (u + w / 2, v - h * 0.28), (u + w / 2, v - h / 2)],
           scale(ridge, 0.6))


@sprop("crt_edit_monitor", aspect=1.72, fill=0.98)
def edit_monitor(c, color):
    P = _pal(color, "#e4572e", "light")
    dark = P.mood == "dark"
    rng = c.rng
    ao(c, 0.0, 0.0, 1.0, 0.18, 0.45)
    c.ellipse(0.0, 0.025, 0.36, 0.035, (0.20, 0.21, 0.24), lift=0.3)
    _crect(c, 0.0, 0.12, 0.10, 0.20, (0.28, 0.29, 0.33), lift=0.3)
    _crect(c, 0.0, 0.195, 0.30, 0.04, (0.22, 0.23, 0.26), r=0.012, lift=0.3)
    _crect(c, 0.0, 0.60, 1.68, 0.82, (0.07, 0.07, 0.09), r=0.028, lift=0.2)               # bezel
    c.line(-0.82, 1.005, 0.82, 1.005, 0.006, WHITE, 0.30)
    g = _G(c, 0.0, 0.605)
    bg = (0.085, 0.09, 0.115)
    g.rect(0, 0, 1.60, 0.75, bg)
    panel = (0.125, 0.13, 0.16)
    acc, acc2 = P.accent, P.accent_light
    # media bin: grid of thumbnails
    g.rect(-0.60, 0.13, 0.38, 0.47, panel, r=0.01)
    for i in range(3):
        for j in range(3):
            _pic(g, -0.73 + i * 0.125, 0.27 - j * 0.105, 0.11, 0.085, P, rng, i + j * 3)
    # preview monitor with transport controls
    g.rect(0.0, 0.13, 0.74, 0.47, panel, r=0.01)
    _pic(g, 0.0, 0.16, 0.66, 0.37, P, rng, 0)
    g.rect(0.0, 0.16 - 0.185, 0.66, 0.006, mix(acc, WHITE, 0.2), alpha=0.9)
    for k, uu in enumerate((-0.07, 0.0, 0.07)):
        g.circle(uu, -0.065, 0.016 if k == 1 else 0.011, WHITE, alpha=0.8)
    # inspector: sliders, colour wheel, histogram
    g.rect(0.60, 0.13, 0.38, 0.47, panel, r=0.01)
    for k in range(4):
        y = 0.28 - k * 0.055
        g.rect(0.60, y, 0.30, 0.008, (0.30, 0.31, 0.36), r=0.004)
        g.rect(0.46 + 0.05 * k + 0.02, y, 0.10 + 0.05 * k, 0.008, acc, r=0.004)
        g.circle(0.51 + 0.05 * k + 0.06, y, 0.014, WHITE)
    g.circle(0.52, 0.00, 0.075, (0.2, 0.2, 0.24))
    for k, col in enumerate(((1.0, 0.35, 0.3), (1.0, 0.8, 0.3), (0.4, 0.9, 0.5), (0.3, 0.7, 1.0), (0.6, 0.4, 1.0), (1.0, 0.4, 0.7))):
        a = math.radians(k * 60 + 15)
        g.circle(0.52 + math.cos(a) * 0.05, 0.00 + math.sin(a) * 0.05, 0.022, col, alpha=0.95)
    for k in range(9):
        g.rect(0.66 + k * 0.016, -0.04 + 0.01 * abs(math.sin(k * 1.3)) * 3, 0.011, 0.02 + 0.07 * abs(math.sin(k * 1.3 + 0.5)), acc2, alpha=0.85)
    # timeline: ruler, video clips with thumbnails, b-roll, audio waveform, playhead
    g.rect(0.0, -0.265, 1.56, 0.20, (0.10, 0.105, 0.13))
    for k in range(40):
        g.rect(-0.76 + k * 0.039, -0.175, 0.003, 0.014 if k % 5 else 0.026, (0.45, 0.47, 0.52), alpha=0.8)
    clips = ((-0.72, 0.30, 0), (-0.38, 0.24, 1), (-0.11, 0.36, 2), (0.29, 0.20, 3), (0.52, 0.27, 1))
    for u0, wd, kind in clips:
        g.rect(u0 + wd / 2, -0.22, wd, 0.05, mix(acc, P.ink, 0.15 + 0.12 * (kind % 2)), r=0.006)
        _pic(g, u0 + 0.03, -0.22, 0.045, 0.036, P, rng, kind)
        g.rect(u0 + wd / 2, -0.205, wd - 0.01, 0.006, WHITE, alpha=0.25)
    for u0, wd in ((-0.60, 0.20), (-0.16, 0.16), (0.14, 0.26), (0.46, 0.18)):
        g.rect(u0 + wd / 2, -0.275, wd, 0.035, mix(acc2, (0.3, 0.5, 0.8), 0.5), r=0.006)
    for k in range(70):
        hh = 0.008 + 0.022 * abs(math.sin(k * 0.37 + math.sin(k * 0.11) * 3.0))
        g.rect(-0.76 + k * 0.0222, -0.325, 0.012, hh, mix(acc2, WHITE, 0.2), alpha=0.9)
    g.rect(0.02, -0.255, 0.004, 0.21, acc, alpha=1.0)
    g.poly([(-0.003, -0.152), (0.043, -0.152), (0.02, -0.176)], acc)
    # screen glow
    c.glow(0.0, 0.60, 1.0, mix(acc2, WHITE, 0.3), 0.20 if dark else 0.10)
    soft_disc(c, 0.0, 0.02, 0.75, 0.05, mix(acc2, WHITE, 0.4), 0.22 if dark else 0.10, 1.3, add=True)
    _fq(c, [(-0.80, 0.98), (-0.20, 0.98), (-0.50, 0.22), (-0.80, 0.22)], WHITE, 0.05)


@sprop("crt_cinema_cam", aspect=0.95, fill=0.98)
def cinema_cam(c, color):
    P = _pal(color, "#e4572e", "light")
    dark = P.mood == "dark"
    rng = c.rng
    ao(c, 0.0, 0.0, 0.95, 0.22, 0.5)
    for s in (-1, 1):                                                         # tripod
        c.line(s * 0.03, 0.40, s * 0.40, 0.0, 0.026, (0.10, 0.10, 0.12))
    c.line(0.02, 0.40, 0.0, 0.03, 0.026, (0.16, 0.16, 0.19))
    _crect(c, 0.0, 0.42, 0.08, 0.05, STEEL, lift=0.3)
    _crect(c, 0.0, 0.47, 0.50, 0.04, (0.12, 0.12, 0.14), r=0.01, lift=0.3)       # plate and rails
    for v in (0.495, 0.515):
        c.line(-0.30, v, 0.40, v, 0.012, mix(STEEL, BLACK, 0.35), 1.0)
    body = (0.13, 0.13, 0.15)
    box3d(c, -0.05, 0.53, 0.64, 0.38, 0.30, body, mix(body, WHITE, 0.14), scale(body, 0.6), lift=0.2, dx=0.5, dy=0.45)
    # top handle with a record button
    c.path([(-0.22, 0.91), (-0.22, 0.99), (0.08, 0.99), (0.08, 0.91)], 0.032, (0.10, 0.10, 0.12), smooth=False)
    c.ellipse(0.20, 0.985, 0.025, 0.012, P.accent, lift=0.3)
    # lens: matte box, barrel rings, coated glass
    c.ellipse(-0.12, 0.70, 0.215, 0.215, scale(body, 0.5), lift=0.2)
    _crect(c, -0.12, 0.70, 0.40, 0.40, (0.05, 0.05, 0.06), r=0.04, lift=0.15)
    c.ellipse(-0.12, 0.70, 0.17, 0.17, (0.17, 0.17, 0.20), lift=0.35)
    c.ellipse(-0.12, 0.70, 0.145, 0.145, (0.07, 0.07, 0.09), lift=0.0)
    c.ellipse(-0.12, 0.70, 0.115, 0.115, mix(P.accent_dark, (0.10, 0.08, 0.30), 0.55), lift=0.35)
    c.ellipse(-0.12, 0.70, 0.075, 0.075, (0.06, 0.05, 0.14), lift=0.3)
    c.ellipse(-0.15, 0.73, 0.035, 0.022, WHITE, lift=0.0, alpha=0.65, angle=30)
    c.ellipse(-0.09, 0.665, 0.018, 0.012, mix(P.accent_light, WHITE, 0.5), lift=0.0, alpha=0.7)
    craft.arc(c, -0.12, 0.70, 0.155, 0.155, 200, 280, 0.012, WHITE, 0.30, 6)
    # flip-out monitor on the right side showing footage
    _crect(c, 0.40, 0.66, 0.17, 0.25, (0.07, 0.07, 0.09), r=0.015, lift=0.2)
    g = _G(c, 0.40, 0.66)
    _pic(g, 0.0, 0.0, 0.14, 0.21, P, rng, 2)
    c.glow(0.40, 0.66, 0.26, mix(P.accent_light, WHITE, 0.4), 0.20 if dark else 0.08)
    gloss(c, -0.15, 0.80, 0.20, 0.06, 0, 0.2)


@sprop("crt_console", aspect=3.2, fill=0.98)
def edit_console(c, color):
    """Keyboard with a jog dial plus a colour-grading panel with three trackballs, seen from the front-top."""
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 3.2, 0.5, 0.5)
    body = (0.11, 0.11, 0.13)
    c.poly([(-1.55, 0.0), (1.55, 0.0), (1.55, 0.16), (-1.55, 0.16)], scale(body, 0.7), lift=0.1)
    c.poly([(-1.55, 0.16), (1.55, 0.16), (1.42, 0.60), (-1.42, 0.60)], body, lift=0.18)
    # keyboard rows (left), jog dial, grading panel (right)
    for row in range(4):
        v = 0.22 + row * 0.095
        sh = 1.0 - row * 0.03
        for k in range(15):
            u = -1.30 + k * 0.095 * sh + row * 0.01
            _crect(c, u * sh, v, 0.078 * sh, 0.066, (0.20, 0.20, 0.24) if (k + row) % 5 else mix(P.accent, scale(body, 2.0), 0.4), r=0.012, lift=0.25)
    c.ellipse(0.40, 0.36, 0.20, 0.075, (0.04, 0.04, 0.05), lift=0.0)
    c.ellipse(0.40, 0.375, 0.18, 0.066, (0.20, 0.20, 0.24), lift=0.35)
    c.ellipse(0.40, 0.378, 0.12, 0.044, (0.10, 0.10, 0.12), lift=0.2)
    c.ellipse(0.40, 0.380, 0.04, 0.015, P.accent, lift=0.3)
    for k, u in enumerate((0.88, 1.10, 1.32)):                                   # trackballs with accent rings
        c.ellipse(u, 0.34, 0.095, 0.065, (0.03, 0.03, 0.04), lift=0.0)
        c.ellipse(u, 0.345, 0.082, 0.056, [P.accent, mix(P.accent, WHITE, 0.4), P.accent_dark][k], lift=0.3)
        c.ellipse(u, 0.350, 0.054, 0.036, (0.14, 0.14, 0.17), lift=0.35)
        c.ellipse(u - 0.015, 0.36, 0.018, 0.010, WHITE, lift=0.0, alpha=0.5)
        for j in range(3):
            c.circle(u - 0.06 + j * 0.06, 0.47 + 0.02 * (j % 2), 0.016, mix(STEEL, WHITE, 0.2), lift=0.35)
    gloss(c, -0.6, 0.55, 0.9, 0.04, 0, 0.14)


@sprop("crt_headphones", aspect=0.95, fill=0.98)
def headphones(c, color):
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 0.9, 0.2, 0.45)
    _crect(c, 0.0, 0.03, 0.34, 0.05, (0.20, 0.20, 0.24), r=0.02, lift=0.3)       # little stand
    _crect(c, 0.0, 0.30, 0.04, 0.55, (0.28, 0.29, 0.33), lift=0.3)
    craft.arc(c, 0.0, 0.55, 0.40, 0.42, 0, 180, 0.075, (0.10, 0.10, 0.12), 1.0, 14)
    craft.arc(c, 0.0, 0.55, 0.40, 0.42, 45, 135, 0.036, P.accent, 0.95, 8)
    for s in (-1, 1):
        c.ellipse(s * 0.41, 0.46, 0.115, 0.215, scale((0.12, 0.12, 0.14), 0.7), lift=0.3)
        c.ellipse(s * 0.42, 0.46, 0.085, 0.185, (0.16, 0.16, 0.19), lift=0.35)
        c.ellipse(s * 0.425, 0.46, 0.045, 0.10, P.accent, lift=0.3)
        c.ellipse(s * 0.40, 0.55, 0.020, 0.06, WHITE, lift=0.0, alpha=0.35)
    gloss(c, -0.2, 0.93, 0.15, 0.04, 10, 0.3)


@sprop("crt_clapper", aspect=1.05, fill=0.98)
def clapper(c, color):
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 1.0, 0.2, 0.4)
    _crect(c, 0.0, 0.34, 1.0, 0.64, (0.08, 0.08, 0.10), r=0.02, lift=0.2)           # board
    for k in range(3):                                                                # blank lines: no writing
        _crect(c, -0.05 + 0.0, 0.50 - k * 0.15, 0.80 - 0.2 * (k % 2), 0.018, (0.90, 0.90, 0.92), r=0.009, lift=0.0, alpha=0.9)
    # hinged striped arm raised a little
    gg = _G(c, -0.50, 0.68, 10.0)
    gg.rect(0.5, 0.075, 1.0, 0.15, (0.09, 0.09, 0.11), lift=0.2)
    for k in range(6):
        gg.poly([(k * 0.17, 0.0), (k * 0.17 + 0.09, 0.0), (k * 0.17 + 0.17, 0.15), (k * 0.17 + 0.08, 0.15)], (0.94, 0.94, 0.95) if k % 2 == 0 else mix(P.accent, WHITE, 0.1))
    arm = _G(c, -0.50, 0.66, 0.0)
    arm.rect(0.5, -0.03, 1.0, 0.13, (0.09, 0.09, 0.11), lift=0.2)
    for k in range(6):
        arm.poly([(k * 0.17, -0.095), (k * 0.17 + 0.08, -0.095), (k * 0.17 + 0.15, 0.035), (k * 0.17 + 0.07, 0.035)], mix(P.accent, WHITE, 0.1) if k % 2 == 0 else (0.94, 0.94, 0.95))
    c.line(-0.50, 0.68, -0.50, 0.66, 0.05, STEEL, 1.0)


@sprop("crt_reel", aspect=1.0, fill=0.98)
def film_reel(c, color):
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 0.9, 0.18, 0.4)
    c.ellipse(0.0, 0.50, 0.48, 0.48, (0.10, 0.10, 0.12), lift=0.25)
    c.ellipse(0.0, 0.50, 0.42, 0.42, (0.16, 0.16, 0.19), lift=0.35)
    c.ellipse(0.0, 0.50, 0.30, 0.30, (0.09, 0.09, 0.11), lift=0.0)                  # dark film wound on the core
    for k in range(6):
        a = math.radians(k * 60 + 30)
        c.ellipse(math.cos(a) * 0.28, 0.5 + math.sin(a) * 0.28, 0.07, 0.07, (0.04, 0.04, 0.05), lift=0.0)
    c.ellipse(0.0, 0.50, 0.10, 0.10, mix(STEEL, WHITE, 0.2), lift=0.35)
    c.ellipse(0.0, 0.50, 0.035, 0.035, (0.08, 0.08, 0.10), lift=0.0)
    craft.arc(c, 0.0, 0.50, 0.44, 0.44, 100, 160, 0.015, WHITE, 0.30, 6)
    # a strip of film curling out onto the floor with perforations and tiny frames
    c.path([(0.05, 0.03), (0.30, 0.0), (0.60, 0.03), (0.86, 0.01)], 0.11, (0.07, 0.07, 0.08), smooth=True)
    for k in range(8):
        u = 0.10 + k * 0.095
        c.rect(u, 0.065 - 0.015 * math.sin(k * 0.5), 0.018, 0.014, (0.85, 0.85, 0.88), r=0.004, lift=0.0)


@sprop("crt_phone_reel", aspect=0.52, fill=0.98)
def phone_reel(c, color):
    P = _pal(color, "#e4572e", "light")
    rng = c.rng
    ao(c, 0.0, 0.0, 0.5, 0.12, 0.4)
    _crect(c, 0.0, 0.02, 0.34, 0.04, (0.20, 0.20, 0.24), r=0.015, lift=0.3)
    _crect(c, 0.0, 0.52, 0.50, 0.96, (0.05, 0.05, 0.06), r=0.07, lift=0.25)
    g = _G(c, 0.0, 0.52)
    g.rect(0.0, 0.0, 0.45, 0.90, (0.90, 0.5, 0.35), r=0.05)
    _pic(g, 0.0, 0.12, 0.45, 0.66, P, rng, 0)
    g.rect(0.0, 0.12, 0.45, 0.66, P.accent, alpha=0.18)
    g.rect(0.0, -0.30, 0.45, 0.30, (0.08, 0.08, 0.10), alpha=0.65)
    for k, wd in enumerate((0.30, 0.22)):                                           # caption bars (no letters)
        g.rect(-0.18 + wd / 2 - 0.0, -0.20 - k * 0.08, wd, 0.045, WHITE if k == 0 else mix(P.accent, WHITE, 0.3), r=0.022)
    g.circle(0.0, 0.14, 0.055, WHITE, alpha=0.55)
    g.poly([(-0.015, 0.17), (-0.015, 0.11), (0.03, 0.14)], (0.1, 0.1, 0.12))
    for k in range(3):
        g.circle(0.17, -0.02 - k * 0.07, 0.022, WHITE, alpha=0.8)
    _crect(c, 0.0, 0.96, 0.12, 0.014, (0.02, 0.02, 0.03), r=0.007, lift=0.0)
    _fq(c, [(-0.22, 0.95), (-0.05, 0.95), (-0.18, 0.12), (-0.22, 0.12)], WHITE, 0.07)


@niche("video-editing", "Video editing studio", subjects=("crt_edit_monitor",),
       strong=("video editing", "video editor", "video editing studio", "video editing service", "youtube video editing", "reels editing", "reel editing",
               "wedding video editing", "video edit", "video editing company", "post production", "post-production studio", "video editing agency", "video ka editing",
               "वीडियो एडिटिंग", "वीडियो एडिटर", "वीडियो एडिटिंग स्टूडियो", "रील एडिटिंग", "यूट्यूब वीडियो एडिटिंग"),
       weak=("editing", "premiere", "final cut", "davinci", "timeline", "subtitles", "color grading", "colour grading", "motion graphics", "b-roll", "shorts", "cut",
             "एडिटिंग"),
       avoid=("graphic design", "logo design", "design studio", "photography", "photographer", "photo studio", "photo editing", "film production", "shooting",
              "ग्राफिक डिजाइन", "फोटोग्राफर"),
       accent="#e4572e", mood="light", group="creative")
def video_editing(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    u0, u1 = S.visible_u()
    u0, u1 = u0 - 0.2, u1 + 0.2
    mid = (u0 + u1) / 2
    foam = mix(P.wall_bot, P.ink, 0.25) if not dark else mix(P.wall_bot, P.ink, 0.35)
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 0.72)
        # acoustic foam wall: grid of alternating wedge tiles, a warm LED bar and a shelf with film tins
        nx = int((u1 - u0) / 0.16) + 1
        for i in range(nx):
            for j in range(4):
                tone = 0.80 + 0.22 * (((i + j) % 2) + 0.3 * ((i * 3 + j * 5) % 3) / 2.0)
                S.rect(u0 + i * 0.16, 0.10 + j * 0.16, 0.15, 0.15, scale(foam, tone if not dark else tone * 1.25), lift=0.0, alpha=0.9 if not dark else 1.0)
        S.rect(mid, 0.03, u1 - u0, 0.035, mix(P.accent_light, WHITE, 0.4), lift=0.0, alpha=0.95 if dark else 0.7)
        S.glow(mid, 0.05, 1.4, P.accent_light, 0.45 if dark else 0.20)
        S.rect(1.05, 0.30, 0.012, 0.50, mix(P.accent, WHITE, 0.35), lift=0.0, alpha=0.9 if dark else 0.7)
        S.glow(1.05, 0.30, 0.38, P.accent_light, 0.40 if dark else 0.15)
        for k in range(5):                                                            # film tins on a shelf
            S.rect(0.34 + k * 0.075, 0.455, 0.06, 0.035, mix(P.accent, P.ink, 0.2 + 0.1 * (k % 3)), r=0.01, lift=0.2)
        S.rect(0.50, 0.485, 0.50, 0.012, scale(P.floor_top, 0.8), lift=0.0)
        S.bokeh(7, u0, 0.1, u1, 0.6, [P.accent_light, (1.0, 0.92, 0.8)], 0.010, 0.034, 0.22 if dark else 0.14)
        S.floor(0.72, scale(P.floor_top, 0.9), scale(P.floor_bot, 0.8))
        S.soft(1.1, 0.90, 1.1, 0.28, mix(P.accent_light, WHITE, 0.3), 0.30 if dark else 0.14, 1.4, add=True)
    # a deep desk across the picture: lit top, front edge, shadowed panel
    dk = scale(P.surface, 0.78 if not dark else 0.85)
    S.rect(mid, 0.795, u1 - u0, 0.012, mix(dk, WHITE, 0.25), lift=0.0)
    S.gradient_rect(u0, 0.80, u1, 1.0, mix(dk, WHITE, 0.08), scale(dk, 0.90))
    S.rect(mid, 1.012, u1 - u0, 0.026, scale(dk, 0.62), lift=0.0)
    S.rect(mid, 1.1, u1 - u0, 0.2, scale(dk, 0.38), lift=0.0)
    S.soft(1.05, 0.90, 0.7, 0.07, mix(P.accent_light, WHITE, 0.4), 0.22 if dark else 0.10, 1.4, add=True)
    # cluster: monitor with the console in front, headphones and the camera on a tripod overlapping it; clapper / phone / reel are loose decor
    S.put("crt_phone_reel", 0.47, 0.90, 0.22, color=P, shadow_alpha=0.3, framed=False)
    S.put("crt_clapper", 0.58, 0.985, 0.14, color=P, shadow_alpha=0.35, framed=False)
    S.put("crt_reel", 1.63, 0.95, 0.15, color=P, shadow_alpha=0.35, framed=False)
    S.put("crt_edit_monitor", 1.0, 0.89, 0.50, color=P, subject=True, shadow=False)
    S.put("crt_headphones", 0.68, 0.955, 0.17, color=P, shadow=False)
    S.put("crt_console", 1.00, 0.985, 0.13, color=P, shadow=False)
    S.put("crt_cinema_cam", 1.40, 1.07, 0.42, color=P, shadow=False)
    S.focus("detail", 1.0, 0.66)
    with S.near(blur=16):
        S.soft(0.45, 1.02, 0.25, 0.09, P.accent, 0.26, 1.2, add=True)
        S.circle(1.72, 0.50, 0.05, P.accent_light, alpha=0.22, lift=0)


# ====================================================================================================== DRONE PHOTOGRAPHY
def _aerial(g, u, v, w, h, kind, rng):
    """A top-down 'aerial photo' made of plain shapes: 0 river bend and fields, 1 construction site, 2 farmhouse and pool, 3 crowd and stage."""
    if kind == 0:
        g.rect(u, v, w, h, (0.55, 0.70, 0.36))
        for k in range(4):
            g.rect(u - w * 0.3 + k * w * 0.2, v + h * 0.28, w * 0.18, h * 0.3, (0.62 + 0.06 * k, 0.74 - 0.03 * k, 0.38), alpha=0.9)
        g.path([(u - w * 0.5, v - h * 0.30), (u - w * 0.2, v - h * 0.05), (u + w * 0.05, v - h * 0.35), (u + w * 0.22, v - h * 0.02), (u + w * 0.5, v - h * 0.12)], h * 0.14, (0.35, 0.60, 0.78))
        g.path([(u - w * 0.5, v - h * 0.30), (u - w * 0.2, v - h * 0.05), (u + w * 0.05, v - h * 0.35), (u + w * 0.22, v - h * 0.02), (u + w * 0.5, v - h * 0.12)], h * 0.05, (0.70, 0.86, 0.92))
        for k in range(3):
            g.rect(u - w * 0.30 + k * 0.17 * w, v + h * 0.04, w * 0.05, h * 0.05, (0.80, 0.35, 0.25))
    elif kind == 1:
        g.rect(u, v, w, h, (0.80, 0.70, 0.52))
        g.rect(u - w * 0.12, v, w * 0.50, h * 0.60, (0.62, 0.62, 0.65))
        g.rect(u - w * 0.12, v, w * 0.44, h * 0.50, (0.74, 0.74, 0.77))
        for k in range(3):
            g.rect(u - w * 0.30 + k * w * 0.17, v, w * 0.012, h * 0.50, (0.55, 0.55, 0.58))
        g.line(u + w * 0.20, v - h * 0.35, u + w * 0.20, v + h * 0.42, w * 0.07, (0.62, 0.50, 0.38))
        g.rect(u + w * 0.34, v + h * 0.1, w * 0.10, h * 0.2, (0.95, 0.75, 0.15))
    elif kind == 2:
        g.rect(u, v, w, h, (0.45, 0.66, 0.34))
        for k in range(5):
            g.rect(u - w * 0.45 + k * w * 0.22, v + h * 0.3, w * 0.14, h * 0.35, (0.55 + 0.05 * k, 0.72, 0.36))
        g.rect(u - w * 0.10, v - h * 0.12, w * 0.30, h * 0.26, (0.78, 0.40, 0.28), r=w * 0.01)
        g.rect(u - w * 0.10, v - h * 0.10, w * 0.30, h * 0.04, (0.62, 0.28, 0.20))
        g.rect(u + w * 0.26, v - h * 0.14, w * 0.18, h * 0.16, (0.32, 0.72, 0.88), r=w * 0.02)
    else:
        g.rect(u, v, w, h, (0.68, 0.64, 0.56))
        g.rect(u, v - h * 0.34, w * 0.56, h * 0.18, (0.35, 0.30, 0.40))
        for k in range(26):
            g.circle(u - w * 0.42 + (k % 9) * w * 0.105, v - h * 0.05 + (k // 9) * h * 0.2 + rng.uniform(-0.02, 0.02) * h, w * 0.022,
                     rng.choice([(0.90, 0.45, 0.20), (0.95, 0.80, 0.25), (0.85, 0.30, 0.45), (0.30, 0.55, 0.85)]))


@sprop("crt_drone", aspect=1.9, fill=0.98)
def drone(c, color):
    P = _pal(color, "#e4572e", "light")
    dark = P.mood == "dark"
    rng = c.rng
    arm = (0.20, 0.21, 0.24)
    white = (0.93, 0.94, 0.96)
    # rear arms and propellers (smaller, higher)
    for s in (-1, 1):
        c.poly([(s * 0.10, 0.56), (s * 0.60, 0.66), (s * 0.60, 0.61), (s * 0.10, 0.50)], arm, lift=0.2)
        _crect(c, s * 0.60, 0.64, 0.07, 0.07, (0.12, 0.12, 0.14), r=0.02, lift=0.3)
        c.ellipse(s * 0.60, 0.70, 0.37, 0.085, (0.88, 0.89, 0.92), lift=0.0, alpha=0.20)
        c.line(s * 0.60 - 0.34, 0.70, s * 0.60 + 0.34, 0.70, 0.014, (0.12, 0.12, 0.14), 0.45)
        c.circle(s * 0.60, 0.69, 0.022, (0.07, 0.07, 0.09), lift=0.3)
    # body: grey underside, white shell, accent stripe, battery bump, vents
    c.ellipse(0.0, 0.40, 0.30, 0.07, scale(arm, 0.6), lift=0.0)
    c.poly([(-0.34, 0.50), (-0.28, 0.36), (0.28, 0.36), (0.34, 0.50)], scale(arm, 0.8), lift=0.2)
    _crect(c, 0.0, 0.57, 0.68, 0.26, white, r=0.10, lift=0.22)
    c.ellipse(0.0, 0.66, 0.26, 0.08, mix(white, WHITE, 0.6), lift=0.0, alpha=0.8)
    _crect(c, 0.0, 0.50, 0.66, 0.035, P.accent, r=0.01, lift=0.2)
    for k in range(5):
        c.line(-0.14 + k * 0.07, 0.62, -0.14 + k * 0.07, 0.68, 0.012, scale(white, 0.72), 0.8)
    c.circle(-0.20, 0.55, 0.018, (1.0, 0.25, 0.20), lift=0.0)
    c.circle(0.20, 0.55, 0.018, (0.25, 1.0, 0.45), lift=0.0)
    c.glow(0.0, 0.55, 0.20, mix(P.accent_light, WHITE, 0.4), 0.15)
    # front arms and propellers (closer, lower, larger)
    for s in (-1, 1):
        c.poly([(s * 0.12, 0.50), (s * 0.76, 0.43), (s * 0.76, 0.375), (s * 0.12, 0.43)], arm, lift=0.25)
        c.poly([(s * 0.74, 0.40), (s * 0.80, 0.20), (s * 0.77, 0.20), (s * 0.70, 0.40)], (0.10, 0.10, 0.12), lift=0.2)              # landing leg
        c.ellipse(s * 0.785, 0.19, 0.05, 0.014, (0.10, 0.10, 0.12), lift=0.0)
        _crect(c, s * 0.76, 0.44, 0.085, 0.10, (0.12, 0.12, 0.14), r=0.025, lift=0.35)
        c.ellipse(s * 0.76, 0.52, 0.45, 0.10, (0.90, 0.91, 0.94), lift=0.0, alpha=0.20)
        c.line(s * 0.76 - 0.40, 0.52, s * 0.76 + 0.40, 0.52, 0.016, (0.10, 0.10, 0.12), 0.45)
        c.eoutline(s * 0.76, 0.52, 0.45, 0.10, 0.007, (0.97, 0.97, 0.99), 0.40)
        c.circle(s * 0.76, 0.515, 0.026, (0.06, 0.06, 0.08), lift=0.35)
        c.ellipse(s * 0.76 - s * 0.14, 0.545, 0.10, 0.018, WHITE, lift=0.0, alpha=0.25)
    # camera gimbal hanging under the nose
    c.line(0.0, 0.38, 0.0, 0.30, 0.07, (0.14, 0.14, 0.17), 1.0)
    c.ellipse(0.0, 0.22, 0.125, 0.125, (0.08, 0.08, 0.10), lift=0.35)
    c.ellipse(0.0, 0.215, 0.085, 0.085, (0.15, 0.15, 0.19), lift=0.3)
    c.ellipse(0.0, 0.21, 0.055, 0.055, mix(P.accent_dark, (0.08, 0.06, 0.28), 0.6), lift=0.3)
    c.ellipse(-0.015, 0.23, 0.02, 0.013, WHITE, lift=0.0, alpha=0.7, angle=30)
    craft.arc(c, 0.0, 0.22, 0.11, 0.11, 110, 170, 0.012, WHITE, 0.35, 5)


@sprop("crt_controller", aspect=1.45, fill=0.98)
def controller(c, color):
    P = _pal(color, "#e4572e", "light")
    rng = c.rng
    ao(c, 0.0, 0.0, 1.45, 0.34, 0.5)
    body = (0.15, 0.16, 0.19)
    for s in (-1, 1):                                                                       # antennas
        c.poly([(s * 0.42, 0.62), (s * 0.60, 0.99), (s * 0.55, 1.0), (s * 0.37, 0.64)], (0.10, 0.10, 0.12), lift=0.2)
    c.poly([(-0.70, 0.12), (-0.72, 0.52), (-0.50, 0.66), (0.50, 0.66), (0.72, 0.52), (0.70, 0.12), (0.52, 0.0), (0.30, 0.10), (-0.30, 0.10), (-0.52, 0.0)], body, lift=0.25)
    c.poly([(-0.66, 0.30), (-0.66, 0.52), (-0.48, 0.62), (0.48, 0.62), (0.66, 0.52), (0.66, 0.30)], mix(body, WHITE, 0.07), lift=0.1)
    # phone clamped in the middle, showing an aerial photo
    _crect(c, 0.0, 0.48, 0.60, 0.40, (0.06, 0.06, 0.08), r=0.035, lift=0.2)
    g = _G(c, 0.0, 0.48)
    _aerial(g, 0.0, 0.0, 0.56, 0.36, 0, rng)
    g.rect(0.0, -0.14, 0.56, 0.07, (0.05, 0.05, 0.07), alpha=0.55)
    for k in range(3):
        g.circle(-0.08 + k * 0.08, -0.14, 0.014, WHITE if k == 1 else (0.7, 0.7, 0.75))
    c.glow(0.0, 0.48, 0.5, mix(P.accent_light, WHITE, 0.4), 0.12)
    # thumbsticks with accent caps, buttons
    for s in (-1, 1):
        c.ellipse(s * 0.50, 0.30, 0.085, 0.040, (0.05, 0.05, 0.06), lift=0.0)
        c.line(s * 0.50, 0.31, s * 0.50, 0.40, 0.035, (0.20, 0.20, 0.24), 1.0)
        c.ellipse(s * 0.50, 0.42, 0.058, 0.028, P.accent, lift=0.35)
        c.ellipse(s * 0.50, 0.428, 0.030, 0.014, mix(P.accent, WHITE, 0.5), lift=0.0, alpha=0.8)
    for k in range(3):
        c.circle(-0.12 + k * 0.12, 0.22, 0.020, mix(STEEL, WHITE, 0.2) if k != 1 else P.accent, lift=0.35)
    gloss(c, -0.4, 0.62, 0.3, 0.05, 0, 0.25)


@sprop("crt_pad", aspect=3.2, fill=0.98)
def landing_pad(c, color):
    P = _pal(color, "#e4572e", "light")
    c.ellipse(0.0, 0.52, 1.55, 0.47, P.accent, lift=0.18)
    c.ellipse(0.0, 0.53, 1.18, 0.36, mix(WHITE, P.accent_light, 0.25), lift=0.1)
    c.ellipse(0.0, 0.54, 0.86, 0.265, P.accent, lift=0.12)
    craft.arc(c, 0.0, 0.58, 1.40, 0.42, 160, 205, 0.05, WHITE, 0.35, 6)


@sprop("crt_prints", aspect=1.35, fill=0.98)
def prints(c, color):
    P = _pal(color, "#e4572e", "light")
    rng = c.rng
    ao(c, 0.0, 0.0, 1.35, 0.4, 0.45)
    for k, (u, v, ang, kind) in enumerate(((0.10, 0.50, 6.0, 1), (-0.12, 0.40, -9.0, 2), (0.0, 0.30, 2.0, 0))):
        g = _G(c, u, v, ang)
        g.rect(0.0, 0.0, 0.84, 0.62, (0.97, 0.96, 0.93), lift=0.0)
        g.rect(0.0, -0.31, 0.84, 0.012, (0.0, 0.0, 0.0), alpha=0.18)
        _aerial(g, 0.0, 0.03, 0.76, 0.50, kind, rng)
        g.rect(0.0, 0.03 + 0.25, 0.76, 0.01, WHITE, alpha=0.25)
    c.circle(0.40, 0.55, 0.05, P.accent, lift=0.3)                                         # a pushpin / clip


@sprop("crt_battery", aspect=1.2, fill=0.98)
def battery(c, color):
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 1.2, 0.4, 0.45)
    for k, (u, v) in enumerate(((-0.12, 0.12), (0.10, 0.52))):
        box3d(c, u, v - 0.12, 0.80, 0.34, 0.26, (0.20, 0.21, 0.25), (0.34, 0.35, 0.40), (0.12, 0.12, 0.15), lift=0.2)
        _crect(c, u - 0.2, v + 0.06, 0.20, 0.07, P.accent, r=0.02, lift=0.2)
        for j in range(4):
            c.circle(u + 0.04 + j * 0.07, v + 0.06, 0.018, (0.4, 1.0, 0.5) if j < 3 else (0.25, 0.28, 0.25), lift=0.0)


@sprop("crt_dslr", aspect=1.1, fill=0.98)
def dslr(c, color):
    P = _pal(color, "#e4572e", "light")
    ao(c, 0.0, 0.0, 1.1, 0.35, 0.45)
    body = (0.12, 0.12, 0.14)
    box3d(c, 0.0, 0.0, 0.92, 0.55, 0.20, body, mix(body, WHITE, 0.16), scale(body, 0.6), lift=0.2)
    c.poly([(-0.14, 0.55), (-0.02, 0.76), (0.18, 0.76), (0.22, 0.55)], scale(body, 1.2), lift=0.2)
    _crect(c, 0.34, 0.60, 0.20, 0.07, P.accent, r=0.02, lift=0.3)
    _crect(c, -0.34, 0.42, 0.16, 0.13, (0.30, 0.30, 0.34), r=0.02, lift=0.3)
    c.ellipse(0.0, 0.30, 0.31, 0.31, (0.05, 0.05, 0.06), lift=0.2)
    c.ellipse(0.0, 0.30, 0.26, 0.26, (0.16, 0.16, 0.19), lift=0.35)
    c.ellipse(0.0, 0.30, 0.19, 0.19, (0.06, 0.06, 0.08), lift=0.0)
    c.ellipse(0.0, 0.30, 0.13, 0.13, mix(P.accent_dark, (0.08, 0.06, 0.28), 0.6), lift=0.35)
    c.ellipse(-0.04, 0.34, 0.04, 0.026, WHITE, lift=0.0, alpha=0.65, angle=30)
    craft.arc(c, 0.0, 0.30, 0.22, 0.22, 100, 170, 0.014, WHITE, 0.3, 5)


def _sunrise_sky(P):
    dark = P.mood == "dark"
    if dark:
        return (0.04, 0.05, 0.14), mix(P.accent_dark, (0.22, 0.14, 0.34), 0.5)
    top = mix(P.wall_top, (0.55, 0.70, 0.92), 0.65)
    hor = mix(P.accent_light, (1.0, 0.88, 0.66), 0.55)
    return top, hor


def _ridge(S, rng, u0, u1, base_v, amp, col, rough, n=44, sharp=0.5, col2=None):
    """A mountain ridge line filled down to the bottom, drawn column by column (far cheaper than a many-sided polygon)."""
    ph = [rng.uniform(0, 6.28) for _ in range(4)]

    def top(u):
        t = math.sin(u * rough + ph[0]) * 0.55 + math.sin(u * rough * 2.3 + ph[1]) * 0.28 + math.sin(u * rough * 5.1 + ph[2]) * 0.12
        t = (1 - sharp) * t + sharp * (abs(t) * 1.4 - 0.4)
        return base_v - amp * (0.55 + 0.45 * t)
    if S.dry:
        return
    S._ensure_mid() if S._layer is S.main else None
    cv, k = S.cv, S._layer.k
    x0, ybase = S.px(0.0, 0.0)[0], S.px(0.0, base_v + 0.4)[1]
    sgn = -1.0 if S.cam.flip else 1.0
    k_u = S._sc * k * sgn
    tops = [S.px(0.0, top((x + 0.5 - x0) / k_u))[1] for x in range(cv.w)]
    y_hi = min(tops)
    span = max(1.0, ybase - y_hi)
    c2 = col2 or scale(col, 0.82)
    cv.terrain(tops, ybase, lambda x, y, d: mix(col, c2, min(1.0, (y - y_hi) / span)))


@niche("drone-photography", "Drone photography", subjects=("crt_drone",),
       strong=("drone photography", "drone photographer", "drone shoot", "drone videography", "drone service", "aerial photography", "drone camera service",
               "drone wedding shoot", "aerial videography", "drone shooting", "drone operator", "drone video", "ड्रोन फोटोग्राफी", "ड्रोन शूट", "ड्रोन कैमरा", "ड्रोन वीडियो",
               "ड्रोन फोटोग्राफर", "drone se shooting", "drone wala"),
       weak=("drone", "aerial", "quadcopter", "4k aerial", "from above", "sky view", "ड्रोन", "ऊपर से", "bird's eye", "real estate aerial", "survey"),
       avoid=("photography studio", "wedding photographer", "photo studio", "portrait", "photo album", "pre wedding", "videography studio", "video editing",
              "फोटो स्टूडियो"),
       accent="#e4572e", mood="light", group="creative")
def drone_photography(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    u0, u1 = S.visible_u()
    u0, u1 = u0 - 0.3, u1 + 0.3
    mid = (u0 + u1) / 2
    sky_t, sky_h = _sunrise_sky(P)
    sun_u = 1.62
    with S.far():
        S.gradient_rect(u0, -0.3, u1, 0.60, sky_t, sky_h)
        S.glow(sun_u, 0.46, 0.95, mix(P.accent_light, (1.0, 0.92, 0.7), 0.5), 0.75 if not dark else 0.55)
        if dark:
            for k in range(60):
                S.circle(rng.uniform(u0, u1), rng.uniform(-0.1, 0.40), rng.uniform(0.003, 0.008), (1.0, 0.96, 0.85), alpha=rng.uniform(0.4, 1.0), lift=0)
            S.circle(0.55, 0.16, 0.05, (1.0, 0.96, 0.85), lift=0)
        else:
            S.circle(sun_u, 0.47, 0.065, (1.0, 0.97, 0.80), lift=0)
            for k in range(3):                                                         # a few thin high clouds
                S.ellipse(0.5 + k * 0.7, 0.14 + 0.05 * k, 0.30, 0.018, mix(P.accent_light, WHITE, 0.6), alpha=0.5, lift=0)
        far_c = mix(sky_h, (0.45, 0.50, 0.72), 0.55) if not dark else mix(sky_h, (0.08, 0.09, 0.22), 0.7)
        mid_c = mix(far_c, P.accent_dark, 0.30) if not dark else (0.06, 0.07, 0.17)
        near_c = mix(mid_c, (0.18, 0.30, 0.24), 0.55) if not dark else (0.04, 0.06, 0.12)
        _ridge(S, rng, u0, u1, 0.56, 0.30, far_c, 5.0, 60, 0.7)
        _ridge(S, rng, u0, u1, 0.60, 0.20, mid_c, 7.0, 60, 0.4)
        # lake with the sun's reflection and ripples
        S.gradient_rect(u0, 0.58, u1, 0.76, mix(sky_h, (0.55, 0.75, 0.85), 0.3) if not dark else (0.07, 0.09, 0.20), scale(mid_c, 0.9))
        for k in range(9):
            S.rect(sun_u + rng.uniform(-0.08, 0.08), 0.60 + k * 0.018, 0.30 - k * 0.020, 0.006, mix(P.accent_light, WHITE, 0.6), lift=0, alpha=0.6 if not dark else 0.22)
        for k in range(14):
            S.rect(rng.uniform(u0, u1), rng.uniform(0.60, 0.75), rng.uniform(0.06, 0.2), 0.004, WHITE, lift=0, alpha=0.18 if not dark else 0.06)
        _ridge(S, rng, u0, u1, 0.78, 0.10, near_c, 11.0, 50, 0.2)
        for k in range(int((u1 - u0) / 0.07)):                                          # pine silhouettes on the far shore
            tu = u0 + k * 0.07 + rng.uniform(-0.02, 0.02)
            th = rng.uniform(0.05, 0.10)
            S.poly([(tu, 0.72), (tu + th * 0.22, 0.72), (tu, 0.72 - th)], scale(near_c, 0.8))
        S.floor(0.76, mix(near_c, (0.30, 0.50, 0.28), 0.5) if not dark else (0.05, 0.08, 0.10), scale(near_c, 0.55) if not dark else (0.02, 0.03, 0.05))
        S.soft(sun_u - 0.5, 0.88, 1.2, 0.20, mix(P.accent_light, (1.0, 0.9, 0.6), 0.5), 0.30 if not dark else 0.18, 1.4, add=True)
    # mown stripes on the meadow, a warm rim of light, then the drone hovering above its landing pad with a soft shadow on the pad
    for k in range(5):
        uu = u0 + (k + 0.5) * (u1 - u0) / 5.0
        S.poly([(uu - 0.05, 0.78), (uu + 0.05, 0.78), (uu + 0.40 * (uu - mid) / (u1 - u0) * 2 + 0.22, 1.2), (uu + 0.40 * (uu - mid) / (u1 - u0) * 2 - 0.22, 1.2)],
               (0.0, 0.0, 0.0) if k % 2 else WHITE, alpha=0.06)
    S.rect(mid, 0.772, u1 - u0, 0.008, mix(P.accent_light, WHITE, 0.4), lift=0.0, alpha=0.35 if not dark else 0.18)
    S.put("crt_pad", 1.02, 1.01, 0.22, color=P, shadow=False, framed=False)
    S.soft(1.04, 0.915, 0.34, 0.040, (0.0, 0.0, 0.0), 0.35, 1.6)
    S.put("crt_prints", 0.66, 1.05, 0.17, color=P, shadow=False)
    S.put("crt_drone", 1.02, 0.70, 0.46, color=P, subject=True, shadow=False)
    S.put("crt_battery", 0.86, 1.06, 0.08, color=P, shadow=False)
    S.put("crt_dslr", 1.54, 0.99, 0.17, color=P, shadow=False)
    S.put("crt_controller", 1.38, 1.06, 0.24, color=P, shadow=False)
    S.focus("detail", 1.02, 0.50)
    with S.near(blur=16):
        S.soft(0.40, 1.0, 0.25, 0.10, P.accent, 0.20, 1.2, add=True)
        S.circle(1.74, 0.92, 0.04, mix(P.accent_light, WHITE, 0.4), alpha=0.25, lift=0)


# ====================================================================================================== TEMPLE
SANDSTONE = (0.88, 0.70, 0.48)
KUMKUM = (0.80, 0.10, 0.10)


def _spoly(c, pts, col, lift=0.10, alpha=1.0, hlit=0.0):
    """Scanline polygon fill (any outline, exact left / right edge coverage, vertical shade, optional left-to-right shade): fast big shapes."""
    cv = c.cv
    w, h, px = cv.w, cv.h, cv.px
    P = [(c.X(u), c.Y(v)) for u, v in pts]
    ys = [p[1] for p in P]
    ytop, ybot = min(ys), max(ys)
    span = max(1.0, ybot - ytop)
    xs_all = [p[0] for p in P]
    xl, xr = min(xs_all), max(xs_all)
    xspan = max(1.0, xr - xl)
    n = len(P)
    for y in range(max(0, int(ytop)), min(h, int(ybot) + 1)):
        yy = y + 0.5
        xs = []
        for i in range(n):
            xa, ya = P[i]
            xb, yb = P[(i + 1) % n]
            if (ya <= yy < yb) or (yb <= yy < ya):
                xs.append(xa + (xb - xa) * (yy - ya) / (yb - ya))
        xs.sort()
        t = (y - ytop) / span
        base = mix(scale(col, 1 + lift), scale(col, 1 - lift * 1.2), t) if lift else col
        for i in range(0, len(xs) - 1, 2):
            xa, xb = xs[i], xs[i + 1]
            ia, ib = max(0, int(math.ceil(xa))), min(w, int(math.floor(xb)))
            if hlit:
                for x in range(max(0, int(xa)), min(w, int(xb) + 1)):
                    cc = scale(base, 1.0 + hlit * (0.5 - (x - xl) / xspan) * 2.0)
                    cov = min(x + 1.0, xb) - max(float(x), xa)
                    if cov <= 0:
                        continue
                    a = min(1.0, cov) * alpha
                    j = (y * w + x) * 3
                    px[j] = px[j] * (1 - a) + cc[0] * a
                    px[j + 1] = px[j + 1] * (1 - a) + cc[1] * a
                    px[j + 2] = px[j + 2] * (1 - a) + cc[2] * a
                continue
            if ib > ia:
                if alpha >= 0.999:
                    px[(y * w + ia) * 3:(y * w + ib) * 3] = [base[0], base[1], base[2]] * (ib - ia)
                else:
                    seg = px[(y * w + ia) * 3:(y * w + ib) * 3]
                    ina = 1.0 - alpha
                    k3 = (base[0] * alpha, base[1] * alpha, base[2] * alpha)
                    px[(y * w + ia) * 3:(y * w + ib) * 3] = [seg[j] * ina + k3[j % 3] for j in range(len(seg))]
            for x, cov in ((ia - 1, ia - xa), (ib, xb - ib)):
                if 0 <= x < w and 0 < cov < 1.0 and (ib >= ia):
                    a = cov * alpha
                    j = (y * w + x) * 3
                    px[j] = px[j] * (1 - a) + base[0] * a
                    px[j + 1] = px[j + 1] * (1 - a) + base[1] * a
                    px[j + 2] = px[j + 2] * (1 - a) + base[2] * a


def _petal(c, u, v, L, ang, wd, col, lift=0.15, alpha=1.0):
    """A pointed petal from (u, v) outwards at ang degrees (90 = up)."""
    pts = []
    for k in range(7):
        t = k / 6.0
        pts.append((t * L, math.sin(math.pi * t) ** 0.8 * wd))
    pts = pts + [(x, -y) for x, y in reversed(pts[1:-1])]
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    c.poly([(u + x * ca - y * sa, v + x * sa + y * ca) for x, y in pts], col, lift=lift, alpha=alpha)


def _flame2(c, u, v, h, rich=True):
    if rich:
        soft_disc(c, u, v + h * 0.5, h * 1.5, h * 1.3, (1.0, 0.62, 0.20), 0.55, 1.7, add=True)
    w = h * 0.34
    c.poly([(u, v), (u + w * 0.9, v + h * 0.28), (u + w * 0.55, v + h * 0.66), (u, v + h), (u - w * 0.55, v + h * 0.66), (u - w * 0.9, v + h * 0.28)], (1.0, 0.55, 0.12), lift=0.0, alpha=0.95)
    c.poly([(u, v + h * 0.04), (u + w * 0.5, v + h * 0.28), (u, v + h * 0.72), (u - w * 0.5, v + h * 0.28)], (1.0, 0.86, 0.35), lift=0.0)
    c.poly([(u, v + h * 0.06), (u + w * 0.22, v + h * 0.22), (u, v + h * 0.40), (u - w * 0.22, v + h * 0.22)], (1.0, 1.0, 0.90), lift=0.0)


def _marigold(c, u, v, r, rng):
    col = MARI[rng.randrange(4)]
    c.ellipse(u, v, r, r * 0.95, scale(col, 0.66), lift=0.0)
    c.ellipse(u - r * 0.04, v + r * 0.05, r * 0.86, r * 0.82, col, lift=0.25)
    c.ellipse(u, v, r * 0.38, r * 0.34, mix(col, (0.7, 0.25, 0.0), 0.5), lift=0.0, alpha=0.75)
    c.ellipse(u - r * 0.3, v + r * 0.3, r * 0.22, r * 0.14, mix(col, WHITE, 0.55), lift=0.0, alpha=0.8)


def _stone(P):
    if P.mood == "dark":
        return mix(SANDSTONE, P.accent_dark, 0.25), 0.42
    return mix(SANDSTONE, P.paper, 0.08), 1.0


@sprop("crt_shikhar", aspect=0.88, fill=0.98)
def shikhar(c, color):
    """A north-Indian temple: stepped plinth, sanctum with arched doorway and a lit lamp, stepped porch roof, curved ribbed shikhar, amalaka, kalash and flag."""
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    stone, lv = _stone(P)
    ao(c, 0.0, 0.0, 0.95, 0.20, 0.45)
    sh = scale(stone, 0.74)
    saffron = P.accent
    # plinth steps
    _crect(c, 0.0, 0.02, 0.86, 0.045, scale(stone, 0.80), lift=0.1)
    _crect(c, 0.0, 0.065, 0.78, 0.045, scale(stone, 0.90), lift=0.1)
    _crect(c, 0.0, 0.108, 0.70, 0.04, stone, lift=0.1)
    # sanctum wall with pilasters
    _crect(c, 0.0, 0.30, 0.60, 0.31, stone, lift=0.10)
    _crect(c, 0.31, 0.30, 0.03, 0.31, sh, lift=0.0)
    for u in (-0.27, -0.19, 0.19, 0.27):
        _crect(c, u, 0.30, 0.022, 0.29, scale(stone, 0.88), lift=0.1)
        c.line(u - 0.011, 0.15, u - 0.011, 0.44, 0.004, mix(stone, WHITE, 0.5), 0.5)
    # arched doorway with a warm glow and lamp points inside
    _crect(c, 0.0, 0.265, 0.25, 0.23, scale(stone, 0.68), r=0.005, lift=0.0)
    c.ellipse(0.0, 0.375, 0.125, 0.115, scale(stone, 0.68), lift=0.0)
    _crect(c, 0.0, 0.255, 0.20, 0.21, (0.16, 0.08, 0.05), lift=0.0)
    c.ellipse(0.0, 0.360, 0.10, 0.095, (0.16, 0.08, 0.05), lift=0.0)
    soft_disc(c, 0.0, 0.26, 0.15, 0.17, (1.0, 0.66, 0.24), 0.70 if not dark else 0.95, 1.2, add=True)
    soft_disc(c, 0.0, 0.21, 0.07, 0.10, (1.0, 0.90, 0.60), 0.55, 1.2, add=True)
    for k in range(3):
        c.circle(-0.07 + k * 0.07, 0.17, 0.012, (1.0, 0.85, 0.45), lift=0.0, alpha=0.9)
    # painted cornice band and dentils
    _crect(c, 0.0, 0.468, 0.64, 0.030, saffron, lift=0.15)
    _crect(c, 0.0, 0.492, 0.66, 0.018, scale(stone, 0.85), lift=0.1)
    for k in range(15):
        _crect(c, -0.28 + k * 0.04, 0.448, 0.020, 0.018, scale(stone, 0.66), lift=0.0)
    # ribbed curved shikhar
    y0, y1 = 0.50, 0.83
    prof = []
    for k in range(17):
        t = k / 16.0
        prof.append((0.285 * math.cos(t * 0.86 * math.pi / 2) ** 0.95, y0 + t * (y1 - y0)))
    outline = [(-x, y) for x, y in prof] + [(x, y) for x, y in reversed(prof)]
    _spoly(c, outline, stone, lift=0.10, hlit=0.30)
    _spoly(c, [(x * 0.14, y) for x, y in prof] + [(-x * 0.14, y) for x, y in reversed(prof)], mix(stone, WHITE, 0.45), lift=0.0, alpha=0.5)
    for x, y in prof[1:-1:2]:
        c.line(-x * 0.99, y, x * 0.99, y, 0.007, scale(stone, 0.55), 0.55)
        c.line(-x * 0.99, y + 0.006, x * 0.99, y + 0.006, 0.003, mix(stone, WHITE, 0.6), 0.5)
    for f in (-0.62, -0.30, 0.30, 0.62):
        c.line(f * prof[0][0], y0 + 0.01, f * prof[-1][0], prof[-1][1], 0.004, scale(stone, 0.60), 0.45)
    c.line(-0.285, y0, -prof[-1][0], prof[-1][1], 0.006, mix(stone, WHITE, 0.6), 0.55)
    for x, y in prof[2:-1:3]:                                                     # tiny saffron markers up the central ridge
        c.circle(0.0, y + 0.012, 0.009, saffron, lift=0.2)
    # stepped porch roof in front of the shikhar base
    for k, (wd, v) in enumerate(((0.58, 0.535), (0.45, 0.572), (0.32, 0.609))):
        _crect(c, 0.0, v, wd, 0.037, scale(stone, 0.98 - 0.05 * (k % 2)), lift=0.12)
        c.line(-wd / 2, v - 0.017, wd / 2, v - 0.017, 0.004, scale(stone, 0.55), 0.6)
        c.circle(0.0, v, 0.008, saffron, lift=0.2)
    c.ellipse(0.0, 0.640, 0.040, 0.024, brass_tone(dark), lift=0.3)
    # amalaka (ribbed disc), kalash, finial and a saffron pennant on a pole
    c.ellipse(0.0, 0.845, 0.115, 0.034, scale(stone, 0.82), lift=0.1)
    c.ellipse(0.0, 0.855, 0.106, 0.030, stone, lift=0.15)
    for k in range(7):
        c.line(-0.090 + k * 0.030, 0.838, -0.084 + k * 0.030, 0.872, 0.004, scale(stone, 0.6), 0.5)
    c.ellipse(0.0, 0.890, 0.036, 0.034, brass_tone(dark), lift=0.3)
    c.poly([(-0.014, 0.915), (0.0, 0.950), (0.014, 0.915)], brass_tone(dark), lift=0.2)
    c.line(0.0, 0.94, 0.0, 1.0, 0.007, scale(brass_tone(dark), 0.8), 1.0)
    c.poly([(0.004, 0.995), (0.12, 0.975), (0.004, 0.955)], saffron, lift=0.1)
    gloss(c, -0.12, 0.70, 0.04, 0.12, 82, 0.20)


def brass_tone(dark):
    return scale(BRASS, 0.78) if dark else BRASS


def _diya(c, u, v, s, dark, flame=True):
    """A brass diya of width ~0.30*s standing at (u, v): boat-shaped bowl, oil, wick and a flame."""
    br = brass_tone(dark)
    c.ellipse(u, v + 0.03 * s, 0.15 * s, 0.040 * s, scale(br, 0.45), lift=0.0)
    c.poly([(u - 0.15 * s, v + 0.075 * s), (u + 0.15 * s, v + 0.075 * s), (u + 0.08 * s, v + 0.012 * s), (u - 0.08 * s, v + 0.012 * s)], br, lift=0.30)
    c.poly([(u + 0.14 * s, v + 0.075 * s), (u + 0.225 * s, v + 0.10 * s), (u + 0.13 * s, v + 0.045 * s)], mix(br, WHITE, 0.15), lift=0.15)
    c.ellipse(u, v + 0.078 * s, 0.15 * s, 0.042 * s, mix(br, WHITE, 0.25), lift=0.1)
    c.ellipse(u, v + 0.080 * s, 0.12 * s, 0.032 * s, (0.62, 0.36, 0.08), lift=0.0)
    c.ellipse(u + 0.01 * s, v + 0.083 * s, 0.07 * s, 0.014 * s, (1.0, 0.78, 0.30), lift=0.0, alpha=0.7)
    c.line(u, v + 0.09 * s, u + 0.03 * s, v + 0.14 * s, 0.012 * s, (0.2, 0.12, 0.08), 1.0)
    if flame:
        _flame2(c, u + 0.03 * s, v + 0.13 * s, 0.26 * s)


@sprop("crt_diya_set", aspect=1.55, fill=0.98)
def diya_set(c, color):
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    rng = c.rng
    ao(c, 0.0, 0.0, 1.5, 0.34, 0.5)
    cop = scale((0.80, 0.45, 0.28), 0.8 if dark else 1.0)
    c.ellipse(0.0, 0.13, 0.74, 0.20, scale(cop, 0.6), lift=0.0)
    c.ellipse(0.0, 0.15, 0.72, 0.19, cop, lift=0.3)
    c.ellipse(0.0, 0.16, 0.60, 0.145, mix(cop, WHITE, 0.15), lift=0.1)
    c.ellipse(0.0, 0.165, 0.54, 0.125, mix(cop, BLACK, 0.2), lift=0.0, alpha=0.5)
    for k in range(10):                                                              # marigold petals scattered on the tray
        a = k * 0.63
        _marigold(c, math.cos(a) * 0.52, 0.16 + math.sin(a) * 0.11, 0.045, rng)
    soft_disc(c, 0.0, 0.40, 1.1, 0.45, (1.0, 0.60, 0.22), 0.30 if not dark else 0.55, 1.6, add=True)
    for u, v, s in ((-0.34, 0.14, 1.05), (0.34, 0.14, 1.05), (0.0, 0.17, 1.25)):
        _diya(c, u, v, s, dark)
    gloss(c, -0.25, 0.27, 0.35, 0.04, 0, 0.30)


@sprop("crt_bell", aspect=0.78, fill=0.98)
def temple_bell(c, color):
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    stone, lv = _stone(P)
    br = brass_tone(dark)
    ao(c, -0.28, 0.0, 0.44, 0.12, 0.45)
    _crect(c, -0.28, 0.45, 0.13, 0.90, stone, lift=0.12)                           # carved stone post
    _crect(c, -0.28, 0.03, 0.20, 0.06, scale(stone, 0.85), lift=0.1)
    _crect(c, -0.28, 0.93, 0.18, 0.05, scale(stone, 0.9), lift=0.1)
    for v in (0.25, 0.55):
        _crect(c, -0.28, v, 0.15, 0.025, scale(stone, 0.78), lift=0.1)
    _crect(c, 0.02, 0.84, 0.64, 0.035, scale((0.45, 0.28, 0.16), lv), lift=0.2)    # wooden arm
    c.poly([(-0.22, 0.82), (-0.10, 0.82), (-0.22, 0.68)], scale((0.45, 0.28, 0.16), lv), lift=0.2)
    c.line(0.22, 0.82, 0.22, 0.70, 0.016, scale(br, 0.7), 1.0)                       # chain and ring
    c.ellipse(0.22, 0.685, 0.035, 0.035, br, lift=0.3)
    c.ellipse(0.22, 0.685, 0.020, 0.020, (0.1, 0.07, 0.05), lift=0.0)
    body = [(0.15, 0.66), (0.29, 0.66), (0.33, 0.55), (0.35, 0.44), (0.40, 0.30), (0.04, 0.30), (0.09, 0.44), (0.11, 0.55)]
    c.ellipse(0.22, 0.66, 0.075, 0.05, br, lift=0.3)
    _spoly(c, body, br, lift=0.22, hlit=0.32)
    for v, wd in ((0.52, 0.215), (0.44, 0.27), (0.36, 0.31)):                          # engraved bands
        c.line(0.22 - wd / 2, v, 0.22 + wd / 2, v, 0.010, scale(br, 0.62), 0.9)
        c.line(0.22 - wd / 2, v + 0.011, 0.22 + wd / 2, v + 0.011, 0.005, mix(br, WHITE, 0.45), 0.6)
    c.ellipse(0.22, 0.30, 0.18, 0.040, scale(br, 0.55), lift=0.0)
    c.ellipse(0.22, 0.298, 0.15, 0.030, (0.10, 0.06, 0.04), lift=0.0)
    c.ellipse(0.22, 0.275, 0.032, 0.032, br, lift=0.3)
    c.line(0.22, 0.30, 0.22, 0.12, 0.012, (0.62, 0.50, 0.30), 1.0)                  # clapper rope
    c.ellipse(0.22, 0.11, 0.02, 0.02, (0.62, 0.50, 0.30), lift=0.2)
    craft.arc(c, 0.22, 0.48, 0.09, 0.20, 105, 160, 0.014, WHITE, 0.45, 5)
    c.glow(0.22, 0.46, 0.34, (1.0, 0.75, 0.35), 0.15)


@sprop("crt_garland", aspect=1.7, fill=0.98)
def garland(c, color):
    """A marigold garland swag between two hooks with leaf sprays and a few hanging strands."""
    P = _pal(color, "#e07a1f", "warm")
    rng = c.rng
    ends = ((-0.84, 0.90), (0.84, 0.90))
    n = 22
    pts = []
    for k in range(n + 1):
        t = k / float(n)
        pts.append((ends[0][0] + (ends[1][0] - ends[0][0]) * t, ends[0][1] - math.sin(math.pi * t) * 0.72))
    for p_, q_ in zip(pts, pts[1:]):
        c.line(p_[0], p_[1], q_[0], q_[1], 0.016, (0.30, 0.20, 0.10), 1.0)
    for i, (u, v) in enumerate(pts):
        if i % 3 == 1:
            craft.leaf(c, u, v, 0.11, rng.uniform(200, 340), (0.20, 0.45, 0.20), 0.5)
        _marigold(c, u, v, 0.062 * rng.uniform(0.9, 1.08), rng)
    for u in (-0.84, 0.84):
        c.circle(u, 0.92, 0.022, brass_tone(P.mood == "dark"), lift=0.3)
    for k, u in enumerate((-0.40, 0.0, 0.40)):                                         # short hanging strands
        base_v = pts[int((u + 0.84) / 1.68 * n)][1]
        for j in range(3):
            _marigold(c, u, base_v - 0.07 - j * 0.085, 0.042, rng)
        c.line(u, base_v, u, base_v - 0.27, 0.010, (0.30, 0.20, 0.10), 0.8)


@sprop("crt_thali", aspect=1.45, fill=0.98)
def prasad_thali(c, color):
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    rng = c.rng
    br = brass_tone(dark)
    ao(c, 0.0, 0.0, 1.45, 0.36, 0.5)
    c.ellipse(0.0, 0.13, 0.70, 0.19, scale(br, 0.5), lift=0.0)
    c.ellipse(0.0, 0.15, 0.68, 0.18, br, lift=0.3)
    c.ellipse(0.0, 0.16, 0.57, 0.145, mix(br, WHITE, 0.22), lift=0.12)
    c.ellipse(0.0, 0.165, 0.48, 0.12, scale(br, 0.82), lift=0.0)
    craft.arc(c, 0.0, 0.15, 0.62, 0.16, 190, 260, 0.020, WHITE, 0.4, 6)
    # laddus in a little pile, each with a lit side and sugar speckle
    spots = ((-0.26, 0.21), (-0.10, 0.19), (0.07, 0.21), (-0.18, 0.31), (0.0, 0.33), (-0.08, 0.44))
    for u, v in spots:
        r = 0.095
        c.ellipse(u, v, r, r * 0.94, (0.78, 0.45, 0.08), lift=0.0)
        c.ellipse(u - r * 0.05, v + r * 0.06, r * 0.9, r * 0.86, (0.98, 0.70, 0.18), lift=0.30)
        for _ in range(5):
            c.circle(u + rng.uniform(-r, r) * 0.6, v + rng.uniform(-r, r) * 0.55, 0.011, (1.0, 0.88, 0.45) if rng.random() < 0.6 else (0.75, 0.42, 0.08), lift=0.0, alpha=0.9)
        c.ellipse(u - r * 0.35, v + r * 0.4, r * 0.28, r * 0.15, (1.0, 0.95, 0.75), lift=0.0, alpha=0.7)
    # steel bowl of kumkum, marigolds, a coconut
    c.ellipse(0.34, 0.16, 0.14, 0.050, scale(STEEL, 0.6), lift=0.0)
    c.ellipse(0.34, 0.185, 0.14, 0.050, mix(STEEL, WHITE, 0.2), lift=0.2)
    c.ellipse(0.34, 0.192, 0.11, 0.034, KUMKUM, lift=0.1)
    c.ellipse(0.55, 0.24, 0.085, 0.085, (0.35, 0.22, 0.12), lift=0.3)
    for dx in (-0.025, 0.025, 0.0):
        c.circle(0.55 + dx, 0.25 - (0.03 if dx == 0 else 0.0), 0.010, (0.15, 0.09, 0.05), lift=0.0)
    for k, (u, v) in enumerate(((0.18, 0.12), (-0.50, 0.22), (0.45, 0.10), (-0.40, 0.11))):
        _marigold(c, u, v, 0.055, rng)
    soft_disc(c, 0.0, 0.40, 0.8, 0.4, (1.0, 0.7, 0.3), 0.18 if not dark else 0.30, 1.6, add=True)


@sprop("crt_lotus", aspect=1.15, fill=0.98)
def lotus_urli(c, color):
    """A brass bowl of water with a lotus flower, floating leaves and a small floating candle."""
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    br = brass_tone(dark)
    ao(c, 0.0, 0.0, 1.15, 0.30, 0.5)
    c.ellipse(0.0, 0.14, 0.52, 0.14, scale(br, 0.5), lift=0.0)
    c.poly([(-0.52, 0.18), (0.52, 0.18), (0.38, 0.03), (-0.38, 0.03)], br, lift=0.28)
    c.ellipse(0.0, 0.18, 0.52, 0.13, mix(br, WHITE, 0.2), lift=0.1)
    c.ellipse(0.0, 0.185, 0.46, 0.105, (0.20, 0.38, 0.42) if not dark else (0.07, 0.14, 0.20), lift=0.1)
    c.ellipse(-0.20, 0.19, 0.20, 0.050, (0.20, 0.50, 0.28), lift=0.2)
    c.ellipse(0.28, 0.20, 0.14, 0.036, (0.22, 0.52, 0.30), lift=0.2)
    pink = (0.96, 0.52, 0.66) if not dark else (0.80, 0.42, 0.56)
    for ang, L, col in ((18, 0.46, mix(pink, WHITE, 0.15)), (162, 0.46, mix(pink, WHITE, 0.15)), (44, 0.52, pink), (136, 0.52, pink), (68, 0.55, mix(pink, WHITE, 0.2)),
                        (112, 0.55, mix(pink, WHITE, 0.2))):
        _petal(c, 0.0, 0.24, L, ang, 0.115, col, lift=0.22)
    for ang in (28, 152, 56, 124):
        _petal(c, 0.0, 0.24, 0.34, ang, 0.095, mix(pink, WHITE, 0.45), lift=0.2)
    _petal(c, 0.0, 0.24, 0.50, 90, 0.10, mix(pink, WHITE, 0.30), lift=0.2)
    c.ellipse(0.0, 0.40, 0.06, 0.036, (0.98, 0.84, 0.30), lift=0.2)
    for k in range(5):
        c.circle(-0.04 + k * 0.02, 0.405, 0.007, (0.80, 0.50, 0.08), lift=0.0)
    c.ellipse(0.36, 0.215, 0.04, 0.010, (0.95, 0.92, 0.85), lift=0.1)                # little floating candle
    _flame2(c, 0.36, 0.225, 0.11)
    gloss(c, -0.30, 0.14, 0.20, 0.04, 0, 0.30)


@sprop("crt_rangoli", aspect=3.0, fill=0.98)
def rangoli(c, color):
    """A floor rangoli seen at a low angle: layered rings, petals, dots."""
    P = _pal(color, "#e07a1f", "warm")
    dark = P.mood == "dark"
    rng = c.rng
    tilt = 0.30
    R = 1.40
    k = 0.8 if dark else 1.0
    red, org, yel, wht, grn = scale(KUMKUM, k), scale((0.98, 0.52, 0.08), k), scale((1.0, 0.82, 0.18), k), scale((0.97, 0.95, 0.90), k), scale((0.25, 0.55, 0.28), k)
    c.ellipse(0.0, 0.50, R * 1.02, R * tilt * 1.02, scale(red, 0.55), lift=0.0, alpha=0.9)
    c.ellipse(0.0, 0.51, R, R * tilt, red, lift=0.1)
    for j in range(28):                                                          # white dots on the rim
        a = j * 2 * math.pi / 28
        c.circle(math.cos(a) * R * 0.93, 0.51 + math.sin(a) * R * tilt * 0.93, 0.030, wht, lift=0.0)
    c.ellipse(0.0, 0.52, R * 0.84, R * 0.84 * tilt, org, lift=0.1)
    for j in range(16):                                                          # petals
        a = j * 2 * math.pi / 16
        ca, sa = math.cos(a), math.sin(a)
        p0 = (ca * R * 0.28, 0.52 + sa * R * 0.28 * tilt)
        p1 = (ca * R * 0.80, 0.52 + sa * R * 0.80 * tilt)
        side = (-sa * 0.09, ca * 0.09 * tilt)
        c.poly([p0, (p0[0] * 0.5 + p1[0] * 0.5 + side[0], p0[1] * 0.5 + p1[1] * 0.5 + side[1]), p1, (p0[0] * 0.5 + p1[0] * 0.5 - side[0], p0[1] * 0.5 + p1[1] * 0.5 - side[1])],
               yel if j % 2 == 0 else wht, lift=0.05)
    c.ellipse(0.0, 0.53, R * 0.40, R * 0.40 * tilt, grn, lift=0.1)
    for j in range(12):
        a = j * 2 * math.pi / 12 + 0.26
        c.circle(math.cos(a) * R * 0.30, 0.53 + math.sin(a) * R * 0.30 * tilt, 0.040, org if j % 2 else yel, lift=0.1)
    c.ellipse(0.0, 0.54, R * 0.13, R * 0.13 * tilt, red, lift=0.1)
    c.ellipse(0.0, 0.545, R * 0.06, R * 0.06 * tilt, yel, lift=0.1)


@niche("temple", "Temple trust", subjects=("crt_shikhar",),
       strong=("temple trust", "mandir trust", "mandir", "temple committee", "temple donation", "temple seva", "dharamshala", "annadaan", "aarti darshan",
               "pooja booking", "mandir samiti", "temple trust donation", "hindu temple", "मंदिर", "मंदिर ट्रस्ट", "मंदिर समिति", "धर्मशाला", "अन्नदान", "आरती दर्शन",
               "पूजा बुकिंग", "मंदिर दान"),
       weak=("temple", "aarti", "darshan", "pooja", "puja", "havan", "prasad", "bhajan", "diya", "seva", "devotees", "pilgrims", "donation", "आरती", "दर्शन", "प्रसाद", "भजन", "सेवा",
             "श्रद्धालु"),
       avoid=("astrologer", "astrology", "kundli", "horoscope", "jyotish", "tarot", "vastu", "ज्योतिष", "कुंडली", "राशिफल", "ngo", "charity trust", "church", "mosque"),
       accent="#e07a1f", mood="warm", group="community")
def temple(S):
    P = S.pal
    dark = P.mood == "dark"
    rng = S.rng
    u0, u1 = S.visible_u()
    u0, u1 = u0 - 0.3, u1 + 0.3
    mid = (u0 + u1) / 2
    gold_l = (1.0, 0.82, 0.45)
    cu = 1.28
    with S.far():
        top = (0.07, 0.05, 0.16) if dark else mix(P.accent_light, (1.0, 0.80, 0.55), 0.55)
        hor = mix(P.accent_dark, (0.55, 0.20, 0.10), 0.5) if dark else (1.0, 0.93, 0.76)
        S.gradient_rect(u0, -0.3, u1, 0.80, top, hor)
        S.glow(cu, 0.42, 0.9, (1.0, 0.82, 0.50), 0.45 if dark else 0.50)
        S.glow(cu + 0.45, 0.34, 0.5, (1.0, 0.85, 0.55), 0.6)
        S.circle(cu + 0.45, 0.34, 0.09, (1.0, 0.93, 0.70) if not dark else (1.0, 0.78, 0.45), lift=0, alpha=0.95)
        # a big faint mandala behind the temple: ring of petals, ring of dots, ring of small petals
        for ring, (R, n, a_, b_, col) in enumerate(((0.36, 16, 0.050, 0.018, KUMKUM), (0.28, 24, 0.030, 0.012, GOLD), (0.44, 32, 0.012, 0.012, GOLD), (0.21, 12, 0.040, 0.014, KUMKUM))):
            for j in range(n):
                a = j * 2 * math.pi / n + ring * 0.1
                S.ellipse(cu + math.cos(a) * R, 0.42 + math.sin(a) * R, a_, b_, col, angle=math.degrees(a), alpha=0.24 if not dark else 0.40, lift=0)
        # distant shikhars and trees in haze
        haze = mix(hor, (0.6, 0.35, 0.25), 0.45) if not dark else (0.10, 0.07, 0.18)
        for uu, hh in ((0.25, 0.30), (0.62, 0.20), (1.95, 0.26), (2.35, 0.18), (-0.1, 0.22)):
            S.poly([(uu - 0.10, 0.70), (uu - 0.06, 0.70 - hh * 0.55), (uu - 0.02, 0.70 - hh * 0.90), (uu, 0.70 - hh), (uu + 0.02, 0.70 - hh * 0.90), (uu + 0.06, 0.70 - hh * 0.55), (uu + 0.10, 0.70)], haze)
        tree = mix(haze, (0.2, 0.3, 0.2), 0.3)
        for k in range(int((u1 - u0) / 0.22)):
            S.ellipse(u0 + k * 0.22 + rng.uniform(0, 0.1), 0.70, rng.uniform(0.10, 0.17), rng.uniform(0.07, 0.12), tree, lift=0, alpha=0.9)
        S.rect(mid, 0.74, u1 - u0, 0.10, scale(haze, 0.9), lift=0)
        # strings of marigolds and lamps across the top
        for a_u in (u0, mid - 0.2, u1 - 0.9):
            pts = [(a_u + 0.9 * t, 0.00 + math.sin(math.pi * t) * 0.10) for t in [i / 10.0 for i in range(11)]]
            for u, v in pts:
                S.circle(u, v, 0.022, MARI[rng.randrange(4)], lift=0.1, soft=2.0, alpha=0.9)
        S.bokeh(12, u0, 0.08, u1, 0.60, [gold_l, (1.0, 0.65, 0.3), P.accent_light], 0.010, 0.04, 0.35 if dark else 0.25)
        # sandstone courtyard with perspective joints
        fl_t = mix(SANDSTONE, P.paper, 0.2) if not dark else mix(SANDSTONE, P.ink, 0.65)
        S.floor(0.78, fl_t, scale(fl_t, 0.78))
        for j in range(6):
            v = 0.80 + 0.30 * (j / 5.0) ** 1.5
            S.rect(mid, v, u1 - u0, 0.004 + 0.003 * j, scale(fl_t, 0.7), lift=0, alpha=0.55)
        for j in range(-8, 9):
            S.line(cu + j * 0.12, 0.78, cu + j * 0.40, 1.15, 0.004, scale(fl_t, 0.7), 0.45)
        S.soft(cu, 0.93, 1.1, 0.28, (1.0, 0.75, 0.38), 0.30 if not dark else 0.34, 1.4, add=True)
    S.put("crt_shikhar", cu, 0.88, 0.58, color=P, subject=True, shadow=False)
    S.put("crt_bell", 0.96, 0.93, 0.44, color=P, shadow=False)
    S.put("crt_garland", 1.24, 0.80, 0.26, color=P, shadow=False)
    S.put("crt_rangoli", 1.30, 1.01, 0.17, color=P, shadow=False)
    S.put("crt_lotus", 0.90, 1.02, 0.19, color=P, shadow=False)
    S.put("crt_diya_set", 1.16, 1.03, 0.16, color=P, shadow=False)
    S.put("crt_thali", 1.52, 1.02, 0.18, color=P, shadow=False)
    S.focus("detail", 1.22, 0.80)
    with S.near(blur=16):
        S.soft(0.45, 1.0, 0.25, 0.10, (1.0, 0.65, 0.3), 0.26, 1.2, add=True)
        for k in range(5):
            S.circle(1.7 + rng.uniform(-0.1, 0.2), 0.95 + rng.uniform(0, 0.1), rng.uniform(0.02, 0.04), MARI[k % 4], alpha=0.45, lift=0)
