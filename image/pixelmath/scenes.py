"""Indoor and studio scenes built from props (business concepts: desk, cafe table, party, wellness, ...)."""
import math

from .painter import Painter
from .props import REGISTRY, draw_prop
from .raster import clamp, mix, scale

WHITE = (1.0, 1.0, 1.0)
GROUP_PROPS = {"swing", "slide", "seesaw", "football", "cricket", "balloons", "team", "candle", "coins", "bouquet", "weddingcouple", "yogi", "bookshelf", "icecream", "airplane", "globe", "shield", "chat", "review", "lotus", "tent"}
# complementary props added when the prompt names only one or two things
AUTO_DECOR = {
    "yogi": ("plant", "candle"), "doctor": ("medicalcross",), "student": ("book",),
    "laptop": ("coffee_cup", "plant"), "monitor": ("plant", "coffee_cup"), "document": ("pencil", "globe"),
    "globe": ("document", "book"), "pizza": ("glass", "plate"), "cake": ("balloons", "giftbox"),
    "coffee_cup": ("croissant", "book"), "croissant": ("coffee_cup",), "shoe": ("tag",),
    "giftbox": ("balloons",), "phone": ("chat",), "chef": ("bread", "plate"), "weddingcouple": ("bouquet",),
    "businessman": ("laptop", "chart"), "team": ("chart",), "lightbulb": ("book",), "burger": ("glass",),
    "tshirt": ("tag",), "chart": ("laptop",), "book": ("pencil", "lightbulb"), "plant": ("lamp",),
    "bread": ("croissant", "coffee_cup"), "icecream": ("cupcake",), "pencil": ("book", "document"),
    "dog": ("plant",), "cat": ("plant", "lamp"), "rabbit": ("plant",), "fish": ("plant",), "parrot": ("plant",),
    "wrench": ("hammer", "toolbox"), "hammer": ("wrench", "screwdriver"), "screwdriver": ("wrench",), "drill": ("toolbox", "hardhat"),
    "saw": ("hammer",), "paintroller": ("bucket",), "faucet": ("wrench",), "toolbox": ("hardhat", "wrench"), "hardhat": ("toolbox",),
    "scissors": ("comb",), "sewingmachine": ("spool", "scissors"), "spool": ("scissors",), "plug": ("lightbulb",), "gear": ("wrench",),
    "comb": ("scissors",), "broom": ("bucket",), "bucket": ("broom",),
}
THEMES = {   # wall (top, bottom) and surface colours per scene theme
    "food": ((0.99, 0.94, 0.85), (0.95, 0.85, 0.72), (0.72, 0.50, 0.32)),
    "desk": ((0.86, 0.91, 0.97), (0.78, 0.85, 0.94), (0.88, 0.80, 0.68)),
    "workshop": ((0.80, 0.84, 0.88), (0.70, 0.76, 0.82), (0.58, 0.42, 0.28)),
    "room": ((0.94, 0.92, 0.88), (0.90, 0.86, 0.80), (0.72, 0.55, 0.38)),
    "wellness": ((0.88, 0.94, 0.88), (0.80, 0.90, 0.82), (0.78, 0.62, 0.45)),
    "clinic": ((0.88, 0.96, 0.96), (0.80, 0.92, 0.93), (0.93, 0.95, 0.97)),
    "studio": ((0.97, 0.93, 0.96), (0.90, 0.88, 0.95), (0.95, 0.94, 0.97)),
    "party": ((0.99, 0.86, 0.90), (0.98, 0.78, 0.84), (0.95, 0.88, 0.80)),
    "garden": ((0.99, 0.91, 0.93), (0.96, 0.86, 0.90), (0.62, 0.80, 0.55)),
}


# a venue seen from the inside is drawn as the things you would find in it
VENUE_INTERIOR = {
    "cafe": ("coffee_cup", "croissant"), "bakery": ("bread", "croissant", "cupcake"), "restaurant": ("plate", "glass", "candle"),
    "shop": ("shoppingbag", "tshirt", "giftbox"), "hotel": ("bed", "lamp"), "hospital": ("doctor", "medicalcross"),
    "university": ("student", "book", "bookshelf"), "villa": ("sofa", "plant", "lamp"), "apartment": ("sofa", "plant"),
    "tent": ("candle",),
}


def collect(parsed):
    """Prop entities from the prompt, merged by name: [(name, color, size, count, position)]."""
    merged = {}

    def add(name, color, size, count, position, secondary=False):
        cur = merged.get(name)
        if cur is None:
            merged[name] = [name, color, size, count, position, secondary]
        else:
            cur[1] = cur[1] or color
            cur[2] = max(cur[2], size)
            cur[3] = max(cur[3], count)
            cur[5] = cur[5] and secondary

    for e in parsed.entities:
        if e.name not in REGISTRY:
            continue
        if REGISTRY[e.name].category in ("buildings",) or e.name == "tent":
            inside = VENUE_INTERIOR.get(e.name, ())
            if e.name == "hospital" and any(x.name in ("dentist", "tooth", "dentalchair") for x in parsed.entities):
                inside = ("medicalcross",)                      # the dentist is already there: no second doctor
            for k, nm in enumerate(inside):
                add(nm, e.color if k == 0 and REGISTRY[nm].category != "people" else None, e.size, 1, e.position, k >= 2)
            if e.name in VENUE_INTERIOR:
                continue
        add(e.name, e.color, e.size, e.count, e.position, e.secondary)
    return [tuple(v) for v in merged.values()]


def _grad_box(p, x0, y0, x1, y1, top, bot, rad=0.0, alpha=1.0):
    span = max(1.0, y1 - y0)
    p.cv.box((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, top, rad=rad, alpha=alpha,
             shade=lambda x, y: mix(top, bot, clamp((y - y0) / span)))


def _window(p, cx, cy, ww, wh, sky_top=(0.55, 0.78, 0.96), sky_bot=(0.86, 0.94, 0.99), frame=(0.97, 0.97, 0.98)):
    cv = p.cv
    fr = p.col(frame)
    cv.box(cx, cy, ww / 2 + 7, wh / 2 + 7, scale(fr, 0.82), rad=4)
    _grad_box(p, cx - ww / 2, cy - wh / 2, cx + ww / 2, cy + wh / 2, sky_top, sky_bot)
    for u, v, r in ((-0.22, -0.10, 0.12), (0.18, -0.25, 0.09), (0.0, 0.05, 0.1)):
        cv.ellipse(cx + u * ww, cy + v * wh, r * ww * 1.3, r * wh * 0.55, WHITE, alpha=0.75, soft=2.0)
    cv.fill_rect(cx - 2, cy - wh / 2, cx + 2, cy + wh / 2, fr)
    cv.fill_rect(cx - ww / 2, cy - 2, cx + ww / 2, cy + 2, fr)
    cv.box(cx, cy + wh / 2 + 8, ww / 2 + 14, 6, fr, rad=3)
    # light shaft on the wall / floor
    p.cv.glow(cx, cy, ww * 1.4, (1.0, 0.97, 0.88), 0.16, 2.0)


def _floor(p, y0, base):
    w, h, cv = p.w, p.h, p.cv
    top, bot = p.col(scale(base, 1.06)), p.col(scale(base, 0.86))
    _grad_box(p, 0, y0, w, h, top, bot)
    for k in range(-8, 9):
        x_top = w / 2 + k * w * 0.05
        x_bot = w / 2 + k * w * 0.18
        cv.capsule(x_top, y0, x_bot, h, 0.7, scale(base, 0.6), 0.28)
    cv.fill_rect(0, y0, w, y0 + 3, scale(base, 0.55), 0.5)


def _table(p, y_top, base):
    w, h, cv = p.w, p.h, p.cv
    depth = (h - y_top) * 0.30
    _grad_box(p, 0, y_top, w, y_top + depth, p.col(scale(base, 1.12)), p.col(scale(base, 1.0)))
    for k in range(1, 4):
        cv.fill_rect(0, y_top + depth * k / 4.0, w, y_top + depth * k / 4.0 + 1.2, scale(base, 0.7), 0.35)
    _grad_box(p, 0, y_top + depth, w, h, p.col(scale(base, 0.82)), p.col(scale(base, 0.64)))
    cv.fill_rect(0, y_top + depth, w, y_top + depth + 3, scale(base, 0.5), 0.6)
    return y_top + depth * 0.62                                          # where objects stand


def _bokeh(p, n, colors, ymax=None):
    rng = p.rng
    for _ in range(n):
        r = rng.uniform(0.02, 0.07) * p.s
        p.cv.circle(rng.uniform(0, p.w), rng.uniform(0, ymax or p.h), r, rng.choice(colors), alpha=rng.uniform(0.10, 0.28), soft=r * 0.5)


def _bunting(p, y0, colors):
    w, cv = p.w, p.cv
    n = 12
    pts = [(w * k / (n - 1.0), y0 + math.sin(math.pi * k / (n - 1.0)) * p.h * 0.06) for k in range(n)]
    for a, b in zip(pts, pts[1:]):
        cv.capsule(a[0], a[1], b[0], b[1], 1.2, (0.4, 0.4, 0.45))
    for k, (x, y) in enumerate(pts[:-1]):
        sx = w / (n - 1.0) * 0.42
        col = p.col(colors[k % len(colors)])
        cv.polygon([(x + sx * 0.2, y), (x + sx * 1.8, y + 0.2), (x + sx, y + sx * 2.1)], col, shade=lambda px, py, c=col: scale(c, 1.1 - 0.25 * ((py - y) / (sx * 2.1))))


def _confetti(p, n):
    rng, cv = p.rng, p.cv
    cols = [(0.95, 0.35, 0.45), (0.98, 0.8, 0.25), (0.3, 0.7, 0.95), (0.45, 0.85, 0.5), (0.75, 0.45, 0.9)]
    for _ in range(n):
        x, y, r = rng.uniform(0, p.w), rng.uniform(0, p.h * 0.8), rng.uniform(2, 5)
        a = rng.uniform(0, math.pi)
        cv.ellipse(x, y, r * 1.6, r * 0.6, rng.choice(cols), angle=a, alpha=0.9)


def _arch(p, cx, base_y, ww, hh):
    """Floral wedding arch."""
    rng, cv = p.rng, p.cv
    cols = [(0.98, 0.72, 0.80), (1.0, 0.92, 0.94), (0.90, 0.45, 0.60), (0.40, 0.70, 0.45), (0.98, 0.85, 0.55)]
    for sgn in (-1, 1):
        cv.box(cx + sgn * ww / 2, base_y - hh / 2, 5, hh / 2, p.col((0.85, 0.80, 0.72)))
    for k in range(60):
        t = k / 59.0
        ang = math.pi * t
        x = cx - (ww / 2) * math.cos(ang)
        y = base_y - hh - (ww / 2) * 0.55 * math.sin(ang)
        for _ in range(2):
            c = cols[rng.randrange(len(cols))]
            r = rng.uniform(0.014, 0.03) * p.s
            cv.circle(x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), r, p.col(c))
    for sgn in (-1, 1):
        for k in range(14):
            y = base_y - hh + hh * k / 14.0 * 0.8
            c = cols[rng.randrange(len(cols))]
            cv.circle(cx + sgn * ww / 2 + rng.uniform(-8, 8), y, rng.uniform(0.012, 0.024) * p.s, p.col(c))


def _theme(items):
    cats = {REGISTRY[n[0]].category for n in items}
    names = {n[0] for n in items}
    if "weddingcouple" in names:
        return "garden"
    if "balloons" in names:
        return "party"
    if "yogi" in names or "lotus" in names or ("candle" in names and not cats & {"food", "tech"}):
        return "wellness"
    if names & {"doctor", "medicalcross", "dentist"} or cats & {"dental", "health"}:
        return "clinic"
    if "tools" in cats:
        return "workshop"
    if "people" in cats and not cats & {"food"}:
        return "desk" if cats & {"tech", "office"} else "room"
    if "food" in cats or "chef" in names:
        return "food"
    if cats & {"tech", "office", "web"}:
        return "desk"
    if cats & {"home"}:
        return "room"
    return "studio"


def scene(parsed, w, h, rng, noise, style, hint=None):
    items = collect(parsed)
    if not items:
        raise ValueError("scene() needs at least one prop")
    names = [n[0] for n in items]
    # complementary decor for sparse prompts
    if len(items) <= 2:
        for extra in AUTO_DECOR.get(names[0], ()):
            if extra not in names and len(items) < 4:
                items.append((extra, None, 1.0, 1, None, True))
                names.append(extra)
    theme = _theme(items)
    p = Painter(w, h, rng, noise, style, light=(1.0, 0.98, 0.95))
    p.sign_text = parsed.texts[0] if parsed.texts else None
    cv, s = p.cv, p.s
    wall_top, wall_bot, surf = THEMES[theme]
    if parsed.background:
        wall_top, wall_bot = mix(parsed.background, WHITE, 0.25), parsed.background
    elif hint:
        wall_top, wall_bot = mix(wall_top, hint["top"], hint["strength"]), mix(wall_bot, hint["bottom"], hint["strength"])
    cats = {REGISTRY[n].category for n in names}
    has_people = "people" in cats and "weddingcouple" not in names
    tableish = [n for n in items if REGISTRY[n[0]].place in ("table",)]
    peopleish = [n for n in items if REGISTRY[n[0]].category == "people"]
    ground = [n for n in items if REGISTRY[n[0]].place in ("ground",) and REGISTRY[n[0]].category != "people"]
    sky = [n for n in items if REGISTRY[n[0]].place == "sky"]

    # ---------------------------------------------------------------- backdrop
    if theme in ("studio", "party"):
        floor_y = h * 0.78
        cv.gradient_v([(0, p.col(wall_top)), (1, p.col(wall_bot))], 0, h)
        _bokeh(p, 14, [WHITE, mix(wall_top, WHITE, 0.5), (1.0, 0.9, 0.7)], h * 0.75)
        if theme == "party":
            _bunting(p, h * 0.07, [(0.95, 0.35, 0.45), (0.98, 0.8, 0.25), (0.3, 0.7, 0.95), (0.45, 0.85, 0.5)])
            _confetti(p, 70)
            table_y = h * 0.74
            base_y = _table(p, table_y, surf)
        else:
            _grad_box(p, 0, floor_y, w, h, p.col(scale(wall_bot, 1.05)), p.col(scale(wall_bot, 0.88)))
            cv.glow(w / 2, floor_y + 6, w * 0.55, (1.0, 1.0, 1.0), 0.28, 2.0)
            base_y = h * 0.84
    elif theme == "garden":
        cv.gradient_v([(0, p.col(wall_top)), (0.7, p.col(wall_bot))], 0, h * 0.74)
        _bokeh(p, 16, [WHITE, (1.0, 0.85, 0.9), (1.0, 0.92, 0.7)], h * 0.7)
        _grad_box(p, 0, h * 0.74, w, h, p.col(surf), p.col(scale(surf, 0.78)))
        for k in range(40):
            x, y = rng.uniform(0, w), rng.uniform(h * 0.76, h)
            cv.ellipse(x, y, 2.5, 1.4, p.col((1.0, 0.85, 0.9)), angle=rng.uniform(0, 3), alpha=0.8)
        _arch(p, w / 2, h * 0.76, w * 0.60, h * 0.45)
        base_y = h * 0.90
    elif theme in ("desk", "food", "workshop"):
        win_x = w * (0.80 if theme == "desk" else 0.22)
        cv.gradient_v([(0, p.col(wall_top)), (1, p.col(wall_bot))], 0, h * 0.7)
        if theme == "workshop":                                              # pegboard wall with a shelf and a hanging lamp
            step = max(8, int(0.035 * s))
            for yy in range(int(h * 0.05), int(h * 0.62), step):
                for xx in range(step // 2, w, step):
                    cv.blend(xx, yy, (0.25, 0.28, 0.33), 0.35)
            cv.fill_rect(0, h * 0.60, w, h * 0.615, scale(wall_bot, 0.7))
            cv.capsule(w * 0.5, 0, w * 0.5, h * 0.10, 1.5, (0.3, 0.3, 0.33))
            cv.polygon([(w * 0.5 - 0.06 * s, h * 0.16), (w * 0.5 + 0.06 * s, h * 0.16), (w * 0.5 + 0.03 * s, h * 0.10), (w * 0.5 - 0.03 * s, h * 0.10)], p.col((0.95, 0.75, 0.2)))
            cv.glow(w * 0.5, h * 0.18, 0.35 * s, (1.0, 0.9, 0.6), 0.28, 2.0)
        else:
            _window(p, win_x, h * 0.27, w * 0.24, h * 0.30)
        if theme == "food":
            for k in range(3):
                cv.fill_rect(w * 0.45 + k * w * 0.16, h * 0.10, w * 0.45 + k * w * 0.16 + 3, h * 0.20, (0.35, 0.3, 0.3))
                cv.circle(w * 0.45 + k * w * 0.16 + 1.5, h * 0.215, 0.04 * s, p.col((1.0, 0.85, 0.5)), soft=2)
                cv.glow(w * 0.45 + k * w * 0.16 + 1.5, h * 0.215, 0.14 * s, (1.0, 0.85, 0.5), 0.5, 2.0)
        table_y = h * (0.66 if has_people else 0.68)
        top_for_people = table_y
        base_y = None  # computed after people are drawn
    else:                                                       # room, wellness, clinic
        floor_y = h * 0.72
        cv.gradient_v([(0, p.col(wall_top)), (1, p.col(wall_bot))], 0, floor_y)
        if theme == "clinic":
            for k in range(1, 10):
                cv.fill_rect(w * k / 10.0, 0, w * k / 10.0 + 1, floor_y, (0.7, 0.85, 0.86), 0.25)
        else:
            _window(p, w * 0.78, h * 0.30, w * 0.22, h * 0.34)
            if theme == "wellness":
                cv.glow(w * 0.5, h * 0.55, w * 0.7, (1.0, 0.95, 0.8), 0.12, 2.0)
        cv.fill_rect(0, floor_y - 6, w, floor_y, scale(wall_bot, 0.88))
        _floor(p, floor_y, surf if theme != "clinic" else (0.82, 0.88, 0.90))
        base_y = floor_y + (h - floor_y) * 0.42

    # ---------------------------------------------------------------- placement
    hero = 1.45 if len(items) == 1 else 1.2 if len(items) == 2 else 1.0

    def size_of(it):
        pr = REGISTRY[it[0]]
        sz = pr.nominal * h * it[2] * hero / max(0.3, pr.fill)
        sz = min(sz, 0.80 * h / max(0.3, pr.fill), 0.70 * w / max(0.5, pr.aspect))
        return sz

    def expand(its):
        out = []
        for it in its:
            n = 1 if it[0] in GROUP_PROPS else min(it[3], 3)
            if it[0] == "shoe" and it[3] > 1:
                n = 2
            out += [it] * n
        return out

    def arrange(its, y_base, scale_f=1.0):
        its = expand(its)
        if not its:
            return []
        while len(its) > 3 and sum(REGISTRY[a[0]].aspect * size_of(a) for a in its) > 1.3 * w and any(a[5] for a in its):
            drop = min((a for a in its if a[5]), key=lambda a: REGISTRY[a[0]].nominal)       # crowded: drop secondary props first
            its.remove(drop)
        its = sorted(its, key=lambda a: -REGISTRY[a[0]].nominal)
        order = []
        for k, it in enumerate(its):
            order.insert(0, it) if k % 2 else order.append(it)
        sizes = [size_of(it) * scale_f for it in order]
        widths = [REGISTRY[it[0]].aspect * sz for it, sz in zip(order, sizes)]
        gap = 0.04 * w
        total = sum(widths) + gap * (len(order) - 1)
        f = min(1.0, 0.88 * w / total)
        x = w / 2 - total * f / 2
        placed = []
        for it, sz, wd in zip(order, sizes, widths):
            placed.append((it, x + wd * f / 2, y_base, sz * f))
            x += (wd + gap) * f
        return placed

    if theme in ("desk", "food", "workshop"):
        back = [it for it in items if REGISTRY[it[0]].place != "table" and REGISTRY[it[0]].place != "sky"]
        drawn = []
        for it, x, _, sz in arrange(back, table_y):
            # people stand behind the desk: the desk front hides their lower body
            drop = 0.30 * sz if REGISTRY[it[0]].category == "people" else 0.0
            drawn.append((it, x, table_y - 0.01 * h + drop, sz))
        for it, x, y, sz in drawn:
            draw_prop(p, it[0], x, y, sz, it[1])
        base_y = _table(p, table_y, surf)
        front = [it for it in items if REGISTRY[it[0]].place == "table"]
        for it, x, y, sz in arrange(front, base_y, 0.55 if back else 1.0):
            draw_prop(p, it[0], x, y, sz, it[1])
        for it, x, _, sz in arrange(sky, h * 0.30):
            draw_prop(p, it[0], x, h * 0.30 + sz * 0.5, sz, it[1])
        p.cv.sign_used = p.sign_used
        return p.cv
    row = [it for it in items if REGISTRY[it[0]].place != "sky"]
    placed = arrange(row, base_y, 0.9 if len(row) > 3 else 1.0)
    placed += [(it, x, h * 0.36 + sz * 0.5, sz) for it, x, _, sz in arrange(sky, h * 0.36)]
    for it, x, y, sz in sorted(placed, key=lambda t: (REGISTRY[t[0][0]].place != "sky", t[2])):
        draw_prop(p, it[0], x, y, sz, it[1])
    p.cv.sign_used = p.sign_used
    return p.cv
