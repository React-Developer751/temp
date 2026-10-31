"""Module 2b - Scene composer: ParsedPrompt + Style -> pixel canvas.

Decides *what* to draw from the parsed prompt (lexicon driven) and calls the
painters in back-to-front order. Everything is deterministic: the same prompt
(and seed) always yields the same image.
"""
import colorsys
import math
import random

from .neural import ParamNet
from .painter import Painter, WHITE
from .raster import (Canvas, Noise, clamp, heart_points, mix, regular_polygon, scale,
                     sdf_box, sdf_circle, sdf_ellipse, sdf_polygon, star_points)
from .props import REGISTRY as PROPS, draw_prop
from .text import draw_headline
from .scenes import scene
from .generative import MODES as GENERATIVE_MODES, render_generative
from .palette import SCHEME_NAMES, harmonic_palette, scheme_palette
from .tokenizer import MAX_PROMPT_CHARS, Entity, fnv1a, parse, vectorize

_NET = ParamNet()

# key -> (sky gradient stops, scene light colour)
SKIES = {
    "day": ([(0, (0.20, 0.50, 0.88)), (0.7, (0.52, 0.78, 0.96)), (1, (0.82, 0.92, 0.98))], (1.0, 1.0, 1.0)),
    "sunset": ([(0, (0.12, 0.12, 0.38)), (0.5, (0.70, 0.28, 0.38)), (0.85, (1.0, 0.60, 0.25)),
                (1, (1.0, 0.82, 0.45))], (1.0, 0.72, 0.55)),
    "dawn": ([(0, (0.30, 0.40, 0.70)), (0.6, (0.85, 0.65, 0.75)), (1, (1.0, 0.84, 0.62))], (1.0, 0.86, 0.78)),
    "night": ([(0, (0.01, 0.02, 0.09)), (0.7, (0.05, 0.08, 0.22)), (1, (0.14, 0.18, 0.38))], (0.38, 0.44, 0.72)),
    "cyber": ([(0, (0.04, 0.0, 0.12)), (0.55, (0.35, 0.02, 0.45)), (0.85, (0.95, 0.15, 0.55)),
               (1, (1.0, 0.45, 0.4))], (0.7, 0.6, 1.0)),
    "snow": ([(0, (0.55, 0.65, 0.78)), (1, (0.88, 0.92, 0.96))], (0.95, 0.97, 1.0)),
    "rain": ([(0, (0.22, 0.25, 0.32)), (1, (0.55, 0.59, 0.65))], (0.75, 0.78, 0.85)),
    "fog": ([(0, (0.62, 0.66, 0.70)), (1, (0.85, 0.87, 0.89))], (0.9, 0.92, 0.94)),
}
MIN_SIZE, MAX_SIZE = 16, 2048          # 2048^2 needs ~600 MB of RAM in pure Python
SCENE_FLAGS = {"cyberpunk", "snow", "rain", "fog", "space", "galaxy", "conifer"}
ANCHOR_X = {"left": 0.2, "right": 0.8, "center": 0.5}


# ---------------------------------------------------------------- helpers
def user_colors(parsed):
    """Colours the user asked for, widened into a usable palette when there are only one or two."""
    cols = [e.color for e in parsed.entities if e.color] + ([parsed.background] if parsed.background else [])
    cols += list(parsed.loose_colors)
    if not cols:
        return cols
    out = list(dict.fromkeys(cols))
    scheme = next((f[7:] for f in sorted(parsed.flags) if f.startswith("scheme_")), None)
    if scheme:                            # "complementary" / "triadic" ...: widen the first colour by that rule
        out += scheme_palette(colorsys.rgb_to_hsv(*out[0])[0], scheme, 4)
    elif len(out) < 4:                    # one brand colour -> light, dark and neighbouring-hue variants
        for c in list(out):
            h, s, v = colorsys.rgb_to_hsv(*c)
            out += [mix(c, WHITE, 0.4), scale(c, 0.6), colorsys.hsv_to_rgb((h + 0.07) % 1.0, s, v),
                    colorsys.hsv_to_rgb((h - 0.07) % 1.0, s, clamp(v * 0.9))]
    return out


def palette_from_vec(vec, n):
    base = vec[0] * 0.5 + 0.5
    out = []
    for i in range(n):
        h = (base + i * 0.618 + vec[(i + 1) % len(vec)] * 0.08) % 1.0
        s = clamp(0.55 + 0.4 * abs(vec[(i + 7) % len(vec)]) * 3, 0.5, 0.9)
        out.append(colorsys.hsv_to_rgb(h, s, 0.9))
    return out


def spread(n, margin=0.18):
    return [] if n <= 0 else [0.5] if n == 1 else [margin + (1 - 2 * margin) * k / (n - 1) for k in range(n)]


OUTDOOR = {"sun", "moon", "stars", "cloud", "mountain", "hill", "tree", "forest", "sea", "beach", "desert", "grass",
           "bird", "rainbow", "road", "planet", "boat", "flower", "house", "city"}
PAVEMENT = {"cafe", "bakery", "restaurant", "shop", "apartment", "hospital", "factory"}
INDOOR_CUES = {"interior", "inside", "indoor", "indoors", "dining", "table", "desk", "counter", "menu"}


def choose_mode(parsed):
    flags = parsed.flags
    if "mandala" not in flags:
        if flags & {"mandelbrot", "julia"}:
            return "fractal"
        if flags & {"lsystem", "koch", "fern", "dragon", "sierpinski"} or ("fractal" in flags and any(e.name == "tree" for e in parsed.entities)):
            return "lsystem"
        if "fractal" in flags:
            return "fractal"
        if "flow" in flags:
            return "flow"
        if flags & {"texture", "marble"}:
            return "texture"
    names = {e.name for e in parsed.entities if e.kind == "object"}
    props = names & set(PROPS)
    if props and "mandala" not in flags:
        indoor = bool({t.word for t in parsed.tokens} & INDOOR_CUES) and not (names & OUTDOOR)
        if "hospital" in names and names & {"tooth", "dentist", "dentalchair", "toothbrush", "pills", "syringe", "stethoscope", "thermometer"}:
            indoor = True                                      # a clinic with a dentist or medical kit is drawn from the inside
        outdoor = (names & OUTDOOR) or parsed.time or (flags & SCENE_FLAGS) or any(
            PROPS[n].category in ("buildings", "vehicles", "machinery", "farm", "playground", "sports", "winter", "rescue") for n in props)
        return "landscape" if outdoor and not indoor else "scene"
    has_object = any(e.kind == "object" for e in parsed.entities)
    has_shape = any(e.kind == "shape" for e in parsed.entities)
    if "mandala" in flags:
        return "mandala"
    if has_object or parsed.time or flags & SCENE_FLAGS:
        return "landscape"
    if "tiles" in flags:
        return "tiles"
    if has_shape:
        return "shapes"
    return "abstract"


# ---------------------------------------------------------------- landscape
def landscape(parsed, w, h, rng, noise, style):
    names, flags = parsed.by_name(), parsed.flags
    if "conifer" in flags and not set(names) & {"tree", "forest"}:
        names["tree"] = [Entity("object", "tree")]
    if any(n in PROPS and PROPS[n].category == "winter" for n in names):
        flags = flags | {"snow"}                                    # winter props imply a snowy scene
    ice = bool(set(names) & {"skater", "iceskate", "hockey"})
    time = parsed.time or ("night" if "cyberpunk" in flags else "day")
    space = bool(flags & {"space", "galaxy"}) or (
        "planet" in names and not set(names) & {"tree", "house", "sea", "beach", "city", "grass",
                                                "mountain", "forest", "flower", "road", "boat"})
    if space:
        return space_scene(parsed, w, h, rng, noise, style)

    if "cyberpunk" in flags:
        key = "cyber"
    elif "rain" in flags:
        key = "rain"
    elif "fog" in flags:
        key = "fog"
    elif "snow" in flags and time == "day":
        key = "snow"
    else:
        key = time
    stops, light = SKIES[key]
    override = parsed.sky_color or parsed.background
    if override:
        stops = [(0, scale(override, 0.6)), (1, mix(override, WHITE, 0.45))]

    p = Painter(w, h, rng, noise, style, light)
    p.sign_text = parsed.texts[0] if parsed.texts else None
    p.night = key in ("night", "cyber")
    s = p.s
    has_sea = "sea" in names or "beach" in names or "island" in names
    city = "city" in names or "cyberpunk" in flags
    wants_shore = "beach" in names or (has_sea and "island" not in names and bool(
        set(names) & {"house", "tree", "palm", "flower", "forest"} or any(
            PROPS[n].category in ("buildings", "people", "home", "travel") for n in names if n in PROPS)))
    p.horizon = h * (0.58 if has_sea else 0.70 if city else 0.64)
    hz = p.horizon
    p.sky(stops)

    # --- sky bodies
    if p.night or "stars" in names:
        p.stars(150 if key == "cyber" else 380, hz * 0.9)
    if "sun" in names or key in ("day", "sunset", "dawn", "snow"):
        ent = names.get("sun", [None])[0]
        r = 0.07 * s * (ent.size if ent else 1.0)
        x = ANCHOR_X.get(ent.position if ent else None, style.light_x) * w
        low = key in ("sunset", "dawn")
        y = hz - r * 0.7 if low else h * (0.12 if ent and ent.position == "top" else 0.2)
        default = {"sunset": (1.0, 0.55, 0.2), "dawn": (1.0, 0.75, 0.5)}.get(key, (1.0, 0.93, 0.6))
        p.sun(x, y, r, ent.color if ent and ent.color else default)
    if "moon" in names or p.night:
        ent = names.get("moon", [None])[0]
        r = 0.06 * s * (ent.size if ent else 1.0)
        x = ANCHOR_X.get(ent.position if ent else None, 1 - style.light_x) * w
        p.moon(x, h * 0.2, r, ent.color if ent and ent.color else (0.93, 0.93, 0.85))
    if "rainbow" in names:
        ent = names["rainbow"][0]
        p.rainbow(ANCHOR_X.get(ent.position, 0.5) * w, hz + 0.05 * h, 0.5 * w * ent.size)
    cloud_ents = names.get("cloud", [])
    n_clouds = sum(e.count for e in cloud_ents) or (0 if p.night else 3)
    for k, cx in enumerate(spread(n_clouds, 0.15)):
        size = cloud_ents[0].size if cloud_ents else 1.0
        p.cloud(cx * w + rng.uniform(-0.05, 0.05) * w, h * rng.uniform(0.08, 0.34),
                rng.uniform(0.18, 0.3) * w * size)

    # --- far terrain
    desert = "desert" in names
    if "mountain" in names:
        ent = names["mountain"][0]
        amp = 0.30 * h * ent.size
        snowy = "snow" in flags
        p.mountains(hz, amp, 2.2, (0.55, 0.62, 0.78), (0.62, 0.70, 0.82), snow=True, seed=1.3, alpha=1.0)
        p.mountains(hz, amp * 0.66, 3.0, (0.38, 0.48, 0.55), (0.45, 0.58, 0.55), snow=snowy, seed=7.1)
        p.mountains(hz, amp * 0.36, 4.0, (0.22, 0.38, 0.30), (0.28, 0.45, 0.32), seed=13.7)
    elif desert:
        p.hills(hz, 0.10 * h, (0.90, 0.72, 0.45), (0.85, 0.65, 0.40), seed=3.1, freq=1.5)
    elif not has_sea and not city:
        green = ((0.30, 0.52, 0.34), (0.26, 0.46, 0.30)) if "hill" in names else ((0.34, 0.50, 0.50), (0.30, 0.46, 0.44))
        p.hills(hz + 4, 0.10 * h, green[0], green[1], seed=5.5, freq=1.2)
    if city:
        p.skyline(hz, 3 if "cyberpunk" in flags else 2, neon="cyberpunk" in flags,
                  window_prob=0.5 if p.night else 0.3)

    # --- ground
    gcol = parsed.ground_color
    grass = names.get("grass", [None])[0]
    gcol = gcol or (grass.color if grass else None)
    shore_top = h * 0.84
    neon = (1.0, 0.2, 0.7)
    if has_sea:
        sea_ent = names.get("sea", [None])[0]
        deep = (sea_ent.color if sea_ent and sea_ent.color else
                (0.03, 0.12, 0.28) if p.night else (0.05, 0.32, 0.58))
        p.sea(deep, bottom=shore_top + 0.03 * h if wants_shore else None)
        if wants_shore:
            if "beach" in names:
                p.shore(shore_top, (0.93, 0.85, 0.65), (0.85, 0.74, 0.52))
            else:
                p.shore(shore_top, (0.45, 0.68, 0.30), (0.20, 0.45, 0.15))
    elif "cyberpunk" in flags:
        p.neon_grid(neon)
    elif desert:
        p.ground((0.93, 0.78, 0.5), (0.82, 0.62, 0.35))
    elif ice:
        p.ground((0.84, 0.92, 0.98), (0.62, 0.80, 0.93), rough=0.6)
    elif "snow" in flags:
        p.ground((0.93, 0.95, 0.98), (0.82, 0.88, 0.95))
    elif city:
        p.ground((0.28, 0.29, 0.33), (0.18, 0.19, 0.22))
    elif set(names) & PAVEMENT:
        p.ground((0.66, 0.66, 0.70), (0.50, 0.50, 0.55))
    elif gcol:
        p.ground(mix(gcol, WHITE, 0.15), scale(gcol, 0.75))
    else:
        p.ground((0.45, 0.68, 0.30), (0.20, 0.45, 0.15))
    if "road" in names or (city and "cyberpunk" not in flags):
        p.road()

    # --- props, drawn far -> near
    props = []
    top = shore_top if wants_shore else hz
    bottom = h * 0.97

    def ground_y(t):
        return top + t * (bottom - top) * (0.9 if not wants_shore else 0.7)

    subjects = []
    for kind in ("house", "tree", "boat"):
        for ent in names.get(kind, []):
            subjects += [(kind, ent)] * ent.count
    free = [sub for sub in subjects if sub[1].position is None]
    slots = iter(spread(len(free)))
    snowy = "snow" in flags
    pine = snowy or "conifer" in flags
    for kind, ent in subjects:
        x = (next(slots) if ent.position is None else ANCHOR_X.get(ent.position, 0.5)) * w
        x += rng.uniform(-0.03, 0.03) * w
        t = 0.3 + 0.35 * rng.random()
        if kind == "boat":
            yb = hz + (0.15 + 0.5 * t) * ((shore_top if wants_shore else h) - hz)
            props.append((yb, lambda x=x, yb=yb, e=ent, t=t: p.boat(
                x, yb, 0.12 * s * (0.6 + t) * e.size, hull=e.color)))
            continue
        yb = ground_y(t)
        if kind == "house":
            props.append((yb, lambda x=x, yb=yb, e=ent, t=t: p.house(
                x, yb, 0.24 * s * (0.65 + 0.7 * t) * e.size, wall=e.color)))
        else:
            props.append((yb, lambda x=x, yb=yb, e=ent, t=t: p.tree(
                x, yb, 0.34 * h * (0.55 + 0.9 * t) * e.size, leaf=e.color, conifer=pine,
                snowy=snowy)))
    for ent in names.get("palm", []):
        n_palm = max(1, min(ent.count, 5))
        for k in range(n_palm):
            x = (ANCHOR_X[ent.position] if ent.position in ANCHOR_X else spread(n_palm)[k]) * w
            yb = ground_y(0.35 + 0.35 * rng.random()) if not (has_sea and "island" in names) else hz + (h - hz) * 0.17
            props.append((yb, lambda x=x, yb=yb, e=ent: p.palm(x, yb, 0.40 * h * e.size, leaf=e.color)))
    if "island" in names:
        ent = names["island"][0]
        cx, cy, rx = w * (0.5 if ent.position is None else ANCHOR_X.get(ent.position, 0.5)), hz + (h - hz) * 0.19, 0.20 * w * ent.size
        sand = p.col((0.93, 0.84, 0.62))
        p.cv.ellipse(cx, cy + 4, rx * 1.1, 0.025 * h, (1, 1, 1), alpha=0.35, soft=4.0)
        p.cv.ellipse(cx, cy, rx, 0.04 * h, sand, shade=lambda x_, y_: scale(sand, 1.08 - 0.3 * ((y_ - (cy - 0.04 * h)) / (0.08 * h))))
        p.cv.ellipse(cx, cy - 0.008 * h, rx * 0.55, 0.022 * h, p.col((0.38, 0.66, 0.34)))
        if "palm" not in names:
            for off in (-0.45, 0.2):
                props.append((cy + 1, lambda x=cx + off * rx, yb=cy - 0.005 * h: p.palm(x, yb, 0.30 * h)))
    for ent in names.get("forest", []):
        for _ in range(18 if ent.count <= 1 else ent.count * 6):
            x, t = rng.uniform(0, w), rng.random() ** 1.3
            yb = ground_y(0.02 + 0.98 * t)
            conif = pine or rng.random() < 0.4
            props.append((yb, lambda x=x, yb=yb, t=t, c=conif, e=ent: p.tree(
                x, yb, 0.30 * h * (0.45 + 0.9 * t) * e.size, leaf=e.color, conifer=c, snowy=snowy)))
    palette = [(0.95, 0.25, 0.3), (1.0, 0.75, 0.2), (0.95, 0.4, 0.75), (0.7, 0.4, 0.95), (1.0, 1.0, 1.0)]
    for ent in names.get("flower", []):
        if ent.count <= 1:
            props.append((bottom, lambda e=ent: p.flower(
                w * ANCHOR_X.get(e.position, 0.5), h * 0.95, 0.38 * h * e.size, e.color or palette[0])))
            continue
        for _ in range(ent.count):
            x, t = rng.uniform(0.03, 0.97) * w, rng.uniform(0.1, 1.0)
            yb = ground_y(t)
            props.append((yb, lambda x=x, yb=yb, t=t, e=ent: p.flower(
                x, yb, 0.12 * h * (0.4 + t) * e.size, e.color or palette[rng.randrange(len(palette))])))
    for ent in names.get("bird", []):
        for _ in range(ent.count):
            x, y = rng.uniform(0.1, 0.9) * w, rng.uniform(0.1, 0.4) * h
            props.append((9999, lambda x=x, y=y, e=ent: p.bird(
                x, y, rng.uniform(0.015, 0.035) * w * e.size, e.color or (0.1, 0.1, 0.12))))
    # business props (buildings, vehicles, people, objects) placed on the ground / in the sky
    merged = {}
    for nm, ents in names.items():
        if nm in PROPS:
            for e in ents:
                cur = merged.setdefault(nm, [e.color, e.size, e.count, e.position, e.secondary])
                cur[0], cur[1], cur[2] = cur[0] or e.color, max(cur[1], e.size), max(cur[2], e.count)
                cur[4] = cur[4] and e.secondary                 # secondary only if every mention of it was
    groups = {}
    ground_cats = ("buildings", "vehicles", "people", "machinery", "farm", "playground", "winter", "rescue")
    for nm, (col, size, count, pos, sec) in merged.items():
        pr = PROPS[nm]
        n = 1 if nm in ("balloons", "team", "candle", "coins", "bouquet", "weddingcouple", "yogi", "bookshelf", "airplane", "globe", "shield", "chat", "review", "lotus", "tent") else min(count, 2 if len(merged) > 2 else 3)
        groups.setdefault(pr.category if pr.category in ground_cats else pr.place, []).extend([(nm, col, size, pos, sec)] * n)
    # visual budget: when the row would be wider than the picture, drop secondary props (smallest first), then shrink everything
    def row_width():
        return sum(PROPS[i[0]].aspect * PROPS[i[0]].nominal * h * i[2] / max(0.3, PROPS[i[0]].fill)
                   for k, v in groups.items() if k not in ("buildings", "sky", "table") for i in v)
    while row_width() > 1.25 * w:
        cands = [(PROPS[i[0]].nominal, k, i) for k, v in groups.items() if k not in ("buildings", "sky", "table") for i in v if i[4]]
        if not cands:
            break
        _, k, i = min(cands, key=lambda t: t[0])
        groups[k].remove(i)
    fit = min(1.0, 1.25 * w / max(1.0, row_width()))
    shared_kinds = [k for k in groups if k not in ("buildings", "sky", "table")]
    shared_xs = iter(spread(sum(len(groups[k]) for k in shared_kinds), 0.18))    # one set of slots: animals, machines, people do not overlap
    slot_no = [0]
    for kind, insts in groups.items():
        xs = shared_xs if kind in shared_kinds else iter(spread(len(insts), 0.22 if kind == "buildings" else 0.2))
        for nm, col, size, pos, _sec in insts:
            pr = PROPS[nm]
            size = size * (fit if kind in shared_kinds else 1.0)
            x = (ANCHOR_X[pos] if pos in ANCHOR_X else next(xs)) * w
            row_shift = 0.0
            if kind in shared_kinds:
                row_shift = 0.10 if slot_no[0] % 2 else -0.06            # alternate front / back rows so neighbours overlap less
                slot_no[0] += 1
            base = pr.nominal * h * size / max(0.3, pr.fill)
            if kind == "buildings":
                yb, sz = ground_y(0.10 + 0.12 * rng.random()), base * 0.95
            elif kind == "vehicles" and pr.place != "sky":
                on_road = "road" in names
                yb, sz = ground_y(0.78 if on_road else 0.55), base * (1.25 if on_road else 1.0)
                x = (0.5 + (0.12 if on_road else 0.0) * (1 if rng.random() < 0.5 else -1)) * w if on_road and pos is None else x
            elif kind == "machinery":
                yb, sz = ground_y(0.62 + row_shift + 0.06 * rng.random()), base
            elif kind in ("farm", "winter", "rescue"):
                yb, sz = ground_y(0.74 + row_shift + 0.06 * rng.random()), base * 0.95
            elif kind == "playground":
                yb, sz = ground_y(0.58 + row_shift + 0.06 * rng.random()), base
            elif kind == "people":
                yb, sz = ground_y(0.88), base * 0.9
            elif pr.place == "sky":
                yb, sz = h * 0.30 + base * 0.4, base * (0.8 if nm == "airplane" else 1.0)
            else:                                                 # small things (tools, cups...): a foreground row of their own
                yb, sz = ground_y(0.97), min(base * 0.75, 0.22 * h / max(0.3, pr.fill))
            if kind not in ("buildings", "sky") and pr.place != "sky":
                half = pr.aspect * sz / 2.0
                x = min(max(x, 0.02 * w + half), 0.98 * w - half) if half < 0.48 * w else w / 2    # keep it inside the picture
            props.append((yb, lambda nm=nm, x=x, yb=yb, sz=sz, col=col: draw_prop(p, nm, x, yb, sz, col)))
    for _, draw in sorted(props, key=lambda item: item[0]):
        draw()

    # --- atmosphere
    if key == "fog":
        p.haze(mix(p.horizon_color(), WHITE, 0.5), hz - 0.3 * h, hz + 0.2 * h, 0.6)
    if "rain" in flags:
        p.precipitation("rain", 260)
    elif snowy:
        p.precipitation("snow", 160)
    p.cv.sign_used = p.sign_used
    return p.cv


def space_scene(parsed, w, h, rng, noise, style):
    names, flags = parsed.by_name(), parsed.flags
    p = Painter(w, h, rng, noise, style)
    p.horizon = h
    p.night = True
    p.sky([(0, (0.0, 0.0, 0.03)), (1, (0.04, 0.02, 0.10))])
    p.nebula()
    p.stars(650, h)
    s = p.s
    if "galaxy" in flags:
        col = parsed.entities[0].color if parsed.entities and parsed.entities[0].color else (0.6, 0.5, 1.0)
        beside = "planet" in names
        p.galaxy(w * (0.72 if beside else 0.5), h * (0.3 if beside else 0.5),
                 (0.26 if beside else 0.45) * s, col)
    planets = names.get("planet", [])
    if not planets and "galaxy" not in flags:
        planets = [Entity("object", "planet")]
    floaters = [e for e in parsed.entities if e.name in PROPS][:4]       # props float in space ("cat in space")
    free = sum(e.count for e in planets)
    xs = iter(x * (0.6 if "galaxy" in flags else 1.0) for x in spread(free, 0.3))
    for ent in planets:
        for _ in range(ent.count):
            cx = ANCHOR_X.get(ent.position, next(xs)) * w if ent.position else next(xs) * w
            col = ent.color or (0.85, 0.55, 0.35)
            if len(floaters) == 1 and free == 1 and not ent.position:
                cx = 0.80 * w                                   # a single floating prop keeps the centre
            cy = 0.26 * h if floaters else h * (0.5 if free == 1 else rng.uniform(0.35, 0.65))
            p.planet(cx, cy, (0.11 if floaters else 0.16) * s * ent.size, col, ring=rng.random() < 0.6)
    if "moon" in names:
        p.moon(w * 0.8, h * 0.2, 0.05 * s, (0.93, 0.93, 0.85))
    if "sun" in names:
        p.sun(w * 0.15, h * 0.18, 0.06 * s, (1.0, 0.9, 0.5))
    for k, (ent, x) in enumerate(zip(floaters, spread(len(floaters), 0.25))):
        pr = PROPS[ent.name]
        size = min(pr.nominal * h * ent.size * (1.5 if len(floaters) == 1 else 1.1) / max(0.3, pr.fill),
                   0.55 * h / max(0.3, pr.fill), 0.8 * w / (len(floaters) * max(0.5, pr.aspect)))
        cx, base = x * w, h * (0.80 if len(floaters) > 1 else 0.78) + (0.04 * h if k % 2 else 0)
        p.cv.glow(cx, base - size * 0.5, size * 0.9, (0.5, 0.45, 0.9), 0.25, 2.0)
        draw_prop(p, ent.name, cx, base, size, ent.color)
    return p.cv


# ---------------------------------------------------------------- shapes
def _shape_sdf(name, cx, cy, r):
    if name == "circle":
        return sdf_circle(cx, cy, r)
    if name == "square":
        return sdf_box(cx, cy, r * 0.85, r * 0.85, r * 0.06)
    if name == "rectangle":
        return sdf_box(cx, cy, r * 1.15, r * 0.7, r * 0.06)
    if name == "ring":
        return lambda x, y: abs(math.hypot(x - cx, y - cy) - r * 0.82) - r * 0.18
    pts = {
        "triangle": lambda: regular_polygon(cx, cy + r * 0.12, r * 1.05, 3),
        "star": lambda: star_points(cx, cy, r * 1.05),
        "heart": lambda: heart_points(cx, cy, r * 1.1),
        "diamond": lambda: regular_polygon(cx, cy, r * 1.1, 4),
        "pentagon": lambda: regular_polygon(cx, cy, r, 5),
        "hexagon": lambda: regular_polygon(cx, cy, r, 6, 0.0),
        "octagon": lambda: regular_polygon(cx, cy, r, 8, math.pi / 8),
    }[name]()
    return sdf_polygon(pts)


def draw_shape(cv, name, cx, cy, r, color):
    box = (cx - r * 1.4, cy - r * 1.4, cx + r * 1.4, cy + r * 1.4)
    soft = max(2.0, r * 0.14)
    shadow_box = (box[0], box[1], box[2] + r * 0.3, box[3] + r * 0.3)
    cv.shape(shadow_box, _shape_sdf(name, cx + r * 0.05, cy + r * 0.1, r), (0, 0, 0),
             alpha=0.38, soft=soft)
    cv.shape(box, _shape_sdf(name, cx, cy, r), color,
             shade=lambda x, y: scale(color, clamp(1.1 - 0.3 * (y - (cy - r)) / (2 * r), 0.6, 1.15)))


def shapes_scene(parsed, w, h, rng, noise, style, vec):
    cv = Canvas(w, h)
    bg = parsed.background
    if bg:
        cv.gradient_v([(0, mix(bg, WHITE, 0.12)), (1, scale(bg, 0.85))])
    else:
        cv.gradient_v([(0, (0.16, 0.18, 0.26)), (1, (0.07, 0.08, 0.13))])
    instances = []
    for e in parsed.entities:
        if e.kind == "shape":
            instances += [e] * e.count
    pal = harmonic_palette(parsed, vec, 6)
    s = min(w, h)
    free = [e for e in instances if e.position is None]
    n = len(free)
    cols = max(1, math.ceil(math.sqrt(n * w / h))) if n else 1
    rows = max(1, math.ceil(n / cols)) if n else 1
    cell = min(w / cols, h / rows)
    grid_iter = iter(range(n))
    for idx, e in enumerate(instances):
        color = e.color or pal[idx % len(pal)]
        if e.position:
            ax = ANCHOR_X.get(e.position, 0.5)
            ay = {"top": 0.25, "bottom": 0.75}.get(e.position, 0.5)
            cx, cy, r = ax * w, ay * h, 0.3 * s * e.size * (0.7 if len(instances) > 1 else 1)
        elif n == 1:
            cx, cy, r = w / 2, h / 2, 0.3 * s * e.size
        else:
            g = next(grid_iter)
            row, col = divmod(g, cols)
            in_row = min(cols, n - row * cols)
            cx = w / 2 + (col - (in_row - 1) / 2) * cell
            cy = h / 2 + (row - (rows - 1) / 2) * cell
            r = 0.36 * cell * e.size
        draw_shape(cv, e.name, cx, cy, r, color)
    return cv


# ---------------------------------------------------------------- patterns
def mandala_scene(parsed, w, h, rng, noise, style, vec):
    cv = Canvas(w, h)
    bg = parsed.background or (0.05, 0.04, 0.12)
    cv.gradient_v([(0, scale(bg, 1.2)), (1, scale(bg, 0.7))])
    cols = user_colors(parsed) or harmonic_palette(parsed, vec, 5)
    s, cx, cy = min(w, h), w / 2, h / 2
    cv.glow(cx, cy, s * 0.55, cols[0], 0.35, 2.0)
    rings = 6
    for k in range(rings):
        rad = s * 0.47 * (1 - k / (rings + 0.6))
        petals = 18 - 2 * k
        d = rad * 0.62
        a = rad * 0.38
        b = max(2.0, min(a * 0.6, d * math.sin(math.pi / petals) * 0.95))
        color = cols[k % len(cols)]
        inner = mix(cols[(k + 1) % len(cols)], WHITE, 0.25)
        for j in range(petals):
            th = 2 * math.pi * j / petals + (k % 2) * math.pi / petals
            px, py = cx + d * math.cos(th), cy + d * math.sin(th)
            cv.ellipse(px, py, a, b, color, angle=th, alpha=0.9)
            cv.ellipse(px, py, a * 0.55, b * 0.5, inner, angle=th, alpha=0.9)
    cv.circle(cx, cy, s * 0.05, mix(cols[0], WHITE, 0.6))
    cv.circle(cx, cy, s * 0.028, cols[1 % len(cols)])
    return cv


def tiles_scene(parsed, w, h, rng, noise, style, vec):
    cv = Canvas(w, h)
    cols = user_colors(parsed) or harmonic_palette(parsed, vec, 4)
    dark = parsed.background or (0.07, 0.08, 0.13)
    cols = cols + [dark]
    n = rng.choice([6, 8, 10])
    cw, ch = w / n, h / n
    for gy in range(n):
        for gx in range(n):
            x0, y0 = gx * cw, gy * ch
            cx, cy = x0 + cw / 2, y0 + ch / 2
            cell = (x0 - 1, y0 - 1, x0 + cw + 1, y0 + ch + 1)
            c1 = cols[rng.randrange(len(cols))]
            c2 = cols[rng.randrange(len(cols))]
            if c2 == c1:
                c2 = cols[(cols.index(c1) + 1) % len(cols)]
            cv.fill_rect(x0, y0, x0 + cw + 1, y0 + ch + 1, c1)
            kind = rng.randrange(5)
            if kind == 0:
                cv.circle(cx, cy, cw * 0.36, c2)
            elif kind == 1:
                for corner in ((x0, y0), (x0 + cw, y0 + ch)):
                    cv.shape(cell, sdf_circle(corner[0], corner[1], cw / 2), c2)
            elif kind == 2:
                cv.polygon([(cx, y0 + ch * 0.1), (x0 + cw * 0.9, cy), (cx, y0 + ch * 0.9),
                            (x0 + cw * 0.1, cy)], c2)
            elif kind == 3:
                cv.polygon([(x0, y0), (x0 + cw, y0), (x0, y0 + ch)] if rng.random() < 0.5 else
                           [(x0 + cw, y0), (x0 + cw, y0 + ch), (x0, y0 + ch)], c2)
            else:
                cv.circle(cx, cy, cw * 0.4, c2)
                cv.circle(cx, cy, cw * 0.2, c1)
    return cv


def abstract_scene(parsed, w, h, rng, noise, style, vec):
    cv = Canvas(w, h)
    cols = user_colors(parsed) or harmonic_palette(parsed, vec, 5)
    bg = parsed.background or scale(cols[0], 0.22)
    cv.gradient_v([(0, scale(mix(bg, cols[1 % len(cols)], 0.25), 1.0)), (1, scale(bg, 0.6))])
    s = min(w, h)
    for _ in range(12):
        cv.glow(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.2, 0.45) * s,
                cols[rng.randrange(len(cols))], rng.uniform(0.15, 0.3), 1.6)
    for _ in range(26):
        c = cols[rng.randrange(len(cols))]
        x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.03, 0.18) * s
        if rng.random() < 0.65:
            cv.circle(x, y, r, c, alpha=rng.uniform(0.3, 0.6), soft=2.0)
        else:
            cv.ellipse(x, y, r * 1.6, r * 0.6, c, angle=rng.uniform(0, math.pi),
                       alpha=rng.uniform(0.3, 0.6), soft=2.0)
    for _ in range(60):
        cv.circle(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1, 3.2), WHITE,
                  alpha=rng.uniform(0.3, 0.8))
    return cv


def text_warnings(parsed):
    """Honest notes about text the fonts only approximate (shown by the CLI and returned by the API)."""
    out = []
    joined = "".join(parsed.texts)
    if any("\u0900" <= ch <= "\u097f" for ch in joined):
        out.append("Devanagari is drawn with an experimental stroke font: letter shapes are approximate, please proof-read the result.")
    if any(ord(ch) > 0x2e80 for ch in joined):
        out.append("Chinese is limited to a small set of simple characters (others are dropped); proof-read the result.")
    return out


def apply_text(cv, parsed, mode, w, h):
    """Write the prompt's "quoted text" into the finished picture (headline / logo text)."""
    texts = list(parsed.texts)
    if getattr(cv, "sign_used", False):
        texts = texts[1:]                                    # the first text already went on a sign
    if not texts:
        return
    s = min(w, h)
    shapes = [e for e in parsed.entities if e.kind == "shape"]
    if mode == "shapes" and len(shapes) == 1:
        draw_headline(cv, texts[0], w / 2, h / 2, 0.11 * s, 0.50 * s)
        if len(texts) > 1:
            draw_headline(cv, texts[1], w / 2, h * 0.88, 0.05 * s, 0.8 * w)
        return
    y = 0.17 * h if mode != "shapes" else 0.88 * h
    draw_headline(cv, texts[0], w / 2, y, min(0.13 * h, 0.2 * w), 0.88 * w)
    if len(texts) > 1:
        draw_headline(cv, texts[1], w / 2, y + 0.115 * h, min(0.055 * h, 0.1 * w), 0.8 * w)


# ---------------------------------------------------------------- entry point
def render(prompt, width=512, height=512, seed=0, model=None, learned="auto"):
    """Return (canvas, parsed_prompt, mode) for a text prompt.

    model:   optional trained `learn.LearnedModel`.
    learned: "auto"   - the model draws prompts the built-in lexicon understood nothing of; for prop scenes
                        it only lends its learned backdrop colours (mode "scene+style"),
             "always" - prefer the model's own image whenever it knows a word of the prompt,
             "blend"  - never use the model's own image, only its backdrop colours for prop scenes,
             "off"    - ignore the model.
    """
    if learned not in ("auto", "always", "off", "blend"):
        raise ValueError("learned must be 'auto', 'always', 'blend' or 'off'")
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a string")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError("prompt too long (max %d characters)" % MAX_PROMPT_CHARS)
    if not (MIN_SIZE <= width <= MAX_SIZE and MIN_SIZE <= height <= MAX_SIZE):
        raise ValueError("width/height must be between %d and %d" % (MIN_SIZE, MAX_SIZE))
    parsed = parse(prompt)
    vec = vectorize(prompt)
    style = _NET.style(vec)
    rng = random.Random(fnv1a(prompt) ^ ((seed * 2654435761) & 0xFFFFFFFF))
    noise = Noise(rng.getrandbits(32))
    mode = choose_mode(parsed)
    if (model is not None and learned != "off" and model.known_words(prompt)
            and learned != "blend" and (learned == "always" or mode == "abstract")):
        from .learn import render_learned
        cv = render_learned(model, prompt, width, height, rng.getrandbits(32))
        mode = "learned"
    elif mode == "landscape":
        cv = landscape(parsed, width, height, rng, noise, style)
    elif mode == "scene":
        hint = model.palette_hint(prompt) if (model is not None and learned in ("auto", "blend", "always")) else None
        cv = scene(parsed, width, height, rng, noise, style, hint)
        if hint:
            mode = "scene+style"
    elif mode == "shapes":
        cv = shapes_scene(parsed, width, height, rng, noise, style, vec)
    elif mode in GENERATIVE_MODES:
        cv = render_generative(mode, parsed, width, height, rng, noise, vec)
    elif mode == "mandala":
        cv = mandala_scene(parsed, width, height, rng, noise, style, vec)
    elif mode == "tiles":
        cv = tiles_scene(parsed, width, height, rng, noise, style, vec)
    else:
        cv = abstract_scene(parsed, width, height, rng, noise, style, vec)
    cv.vignette(0.22)
    cv.grain(rng, style.grain)
    apply_text(cv, parsed, mode, width, height)
    return cv, parsed, mode
