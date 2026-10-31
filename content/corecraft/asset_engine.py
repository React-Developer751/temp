"""Image/Asset AI Engine: palettes, SVG graphics, data URIs. Uses colorsys, os, base64 (+ math, random)."""
import base64
import colorsys
import math
import os
import random

MOOD_HUES = {
    "warm": (8, 40), "bold": (0, 20), "cool": (200, 260), "elegant": (260, 330),
    "friendly": (140, 200), "playful": (300, 360), "calm": (170, 220),
}
MOOD_DARK = {"warm": 0.3, "bold": 0.8, "cool": 0.7, "elegant": 0.6, "friendly": 0.1, "playful": 0.15, "calm": 0.2}


def hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, min(max(l, 0), 1), min(max(s, 0), 1))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def hex_rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def luminance(hx):
    def ch(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = hex_rgb(hx)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _readable_on(bg, light="#f8fafc", dark="#0f172a"):
    return light if contrast(bg, light) >= contrast(bg, dark) else dark


def _fix_contrast(fg, bg, minimum=4.5):
    """Nudge fg lightness until it reaches the minimum contrast against bg."""
    r, g, b = (v / 255.0 for v in hex_rgb(fg))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    step = -0.03 if luminance(bg) > 0.4 else 0.03
    for _ in range(40):
        if contrast(hsl_hex(h * 360, s, l), bg) >= minimum:
            break
        l = min(max(l + step, 0.0), 1.0)
    return hsl_hex(h * 360, s, l)


def _pick_brand(h, sat, bg):
    """Lightness closest to 0.5 where the colour stands out from bg (>=3) and its label text reaches 4.5."""
    best = None
    for i in range(10, 91):
        l = i / 100.0
        c = hsl_hex(h, sat, l)
        if contrast(c, bg) >= 3.0 and contrast(c, _readable_on(c)) >= 4.5:
            if best is None or abs(l - 0.5) < abs(best[0] - 0.5):
                best = (l, c)
    if best is None:
        raise ValueError("no usable brand colour for hue %.0f" % h)
    return best[1]


def make_palette(mood, rng):
    lo, hi = MOOD_HUES.get(mood, (170, 220))
    base = rng.uniform(lo, hi)
    accent = base + rng.choice([30, 150, 180, 210])
    dark = rng.random() < MOOD_DARK.get(mood, 0.3)
    if dark:
        bg, surface = hsl_hex(base, 0.35, 0.08), hsl_hex(base, 0.30, 0.13)
    else:
        bg, surface = hsl_hex(base, 0.45, 0.97), hsl_hex(base, 0.30, 0.92)
    text = _readable_on(bg)
    muted = _fix_contrast(hsl_hex(base, 0.12, 0.55), bg, 4.5)
    primary = _pick_brand(base, rng.uniform(0.6, 0.85), bg)
    accent_c = _pick_brand(accent, rng.uniform(0.6, 0.85), bg)
    return {
        "dark": dark, "bg": bg, "surface": surface, "text": text, "muted": muted,
        "primary": primary, "primary_text": _readable_on(primary),
        "accent": accent_c, "accent_text": _readable_on(accent_c),
        "rgb": {"primary": hex_rgb(primary), "accent": hex_rgb(accent_c)},
    }


def _blob(cx, cy, r, rng, pts=7):
    ang = [2 * math.pi * i / pts for i in range(pts)]
    p = [(cx + r * rng.uniform(0.7, 1.15) * math.cos(a), cy + r * rng.uniform(0.7, 1.15) * math.sin(a)) for a in ang]
    d = "M %.1f %.1f " % ((p[0][0] + p[-1][0]) / 2, (p[0][1] + p[-1][1]) / 2)
    for i, pt in enumerate(p):
        nx = p[(i + 1) % pts]
        d += "Q %.1f %.1f %.1f %.1f " % (pt[0], pt[1], (pt[0] + nx[0]) / 2, (pt[1] + nx[1]) / 2)
    return d + "Z"


def hero_svg(pal, rng, seed_label=""):
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" role="img" aria-label="Decorative artwork %s">' % seed_label,
        '<defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>' % (pal["primary"], pal["accent"]),
        '<rect width="800" height="600" rx="36" fill="%s"/>' % pal["surface"],
    ]
    for i in range(rng.randint(3, 5)):
        fill = "url(#g1)" if i == 0 else (pal["primary"] if i % 2 else pal["accent"])
        parts.append('<path d="%s" fill="%s" opacity="%.2f"/>' % (_blob(rng.uniform(150, 650), rng.uniform(130, 470), rng.uniform(90, 210), rng), fill, 0.9 if i == 0 else rng.uniform(0.25, 0.55)))
    for _ in range(rng.randint(8, 16)):
        parts.append('<circle cx="%d" cy="%d" r="%d" fill="%s" opacity="0.7"/>' % (rng.randint(30, 770), rng.randint(30, 570), rng.randint(3, 12), pal["text"]))
    return "".join(parts) + "</svg>"


def _icon_shape(kind, c, col):
    if kind == 0:
        return '<circle cx="24" cy="24" r="14" fill="none" stroke="%s" stroke-width="4"/><circle cx="24" cy="24" r="5" fill="%s"/>' % (col, col)
    if kind == 1:
        pts = " ".join("%.1f,%.1f" % (24 + (18 if i % 2 == 0 else 8) * math.sin(i * math.pi / 5), 24 - (18 if i % 2 == 0 else 8) * math.cos(i * math.pi / 5)) for i in range(10))
        return '<polygon points="%s" fill="%s"/>' % (pts, col)
    if kind == 2:
        pts = " ".join("%.1f,%.1f" % (24 + 17 * math.cos(i * math.pi / 3), 24 + 17 * math.sin(i * math.pi / 3)) for i in range(6))
        return '<polygon points="%s" fill="none" stroke="%s" stroke-width="4"/>' % (pts, col)
    if kind == 3:
        return '<path d="M4 28 Q14 8 24 24 T44 20" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % col
    if kind == 4:
        return "".join('<circle cx="%d" cy="%d" r="4" fill="%s"/>' % (x, y, col) for x in (12, 24, 36) for y in (12, 24, 36))
    return '<polygon points="24,6 42,40 6,40" fill="%s"/>' % col


def icon_svg(index, pal):
    col = pal["primary"] if index % 2 == 0 else pal["accent"]
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" aria-hidden="true">%s</svg>' % _icon_shape(index % 6, pal, col)


def logo_svg(brand, pal):
    letter = (brand.strip()[:1] or "C").upper().replace("&", "&amp;")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="%s logo">'
            '<rect width="64" height="64" rx="16" fill="%s"/>'
            '<text x="32" y="43" font-family="Georgia,serif" font-size="34" font-weight="700" text-anchor="middle" fill="%s">%s</text></svg>'
            % (brand.replace('"', "").replace("&", "&amp;").replace("<", ""), pal["primary"], pal["primary_text"], letter))


def data_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def generate_assets(content, seed=None):
    rng = random.Random(None if seed is None else seed + 1)
    pal = make_palette(content["mood"], rng)
    return {
        "palette": pal,
        "hero": hero_svg(pal, rng, content["niche"]),
        "logo": logo_svg(content["brand"], pal),
        "icons": [icon_svg(i, pal) for i in range(len(content["features"]))],
    }


def validate_assets(a):
    pal = a["palette"]
    for fg, bg, mn in [("text", "bg", 4.5), ("muted", "bg", 4.5), ("primary_text", "primary", 4.5), ("accent_text", "accent", 4.5), ("text", "surface", 4.5)]:
        if contrast(pal[fg], pal[bg]) < mn:
            raise ValueError("low contrast %s on %s: %.2f" % (fg, bg, contrast(pal[fg], pal[bg])))
    for svg in [a["hero"], a["logo"]] + a["icons"]:
        if not (svg.startswith("<svg") and svg.endswith("</svg>")):
            raise ValueError("malformed svg")
    return True


def write_assets(assets, out_dir):
    d = os.path.join(out_dir, "assets")
    os.makedirs(d, exist_ok=True)
    paths = {}
    for name in ("hero", "logo"):
        p = os.path.join(d, name + ".svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(assets[name])
        paths[name] = "assets/%s.svg" % name
    return paths
