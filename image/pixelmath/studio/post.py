"""The judge's tools: text-zone contrast (with an automatic scrim), perceptual hash, detail density, palette signature."""
import colorsys
import math

from ..raster import Canvas, clamp, mix

# sRGB byte -> linear light (WCAG relative luminance)
_LIN = [((i / 255.0 + 0.055) / 1.055) ** 2.4 if i / 255.0 > 0.04045 else i / 255.0 / 12.92 for i in range(256)]
TEXT = {"white": (1.0, 1.0, 1.0), "dark": (0.05, 0.05, 0.08)}
TEXT_LUM = {"white": 1.0, "dark": 0.0011 * 0 + 0.0030}
CONTRAST_TARGET = 4.5


def luminance(rgb):
    r, g, b = (_LIN[int(clamp(v) * 255 + 0.5)] for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(l1, l2):
    hi, lo = (l1, l2) if l1 >= l2 else (l2, l1)
    return (hi + 0.05) / (lo + 0.05)


def zone_box(cv, zone):
    x0, y0, x1, y1 = zone
    return int(x0 * cv.w), int(y0 * cv.h), int(x1 * cv.w), int(y1 * cv.h)


def zone_luminances(cv, zone, step=1):
    """Relative luminance of every `step`-th pixel in the zone as rows of floats."""
    x0, y0, x1, y1 = zone_box(cv, zone)
    px, w = cv.px, cv.w
    rows = []
    for y in range(y0, y1, step):
        base = y * w * 3
        seg = px[base + x0 * 3:base + x1 * 3]
        b = bytes(int(min(1.0, max(0.0, v)) * 255.0 + 0.5) for v in seg)
        r, g, bl = b[0::3][::step], b[1::3][::step], b[2::3][::step]
        rows.append([0.2126 * _LIN[a] + 0.7152 * _LIN[c] + 0.0722 * _LIN[d] for a, c, d in zip(r, g, bl)])
    return rows


def worst_contrast(cv, zone, text):
    """Lowest contrast ratio between the text colour and any pixel of the zone (exact, every pixel)."""
    lt = TEXT_LUM[text]
    worst = 99.0
    for row in zone_luminances(cv, zone, 1):
        if text == "white":
            c = (1.0 + 0.05) / (max(row) + 0.05)
        else:
            c = (min(row) + 0.05) / (lt + 0.05)
        worst = min(worst, c)
    return worst


def _extremes(cv, zone):
    """Brightest and darkest pixel (as colours) inside the zone, by luminance."""
    x0, y0, x1, y1 = zone_box(cv, zone)
    px, w = cv.px, cv.w
    best = worst = None
    bl, wl = -1.0, 2.0
    for y in range(y0, y1, 2):
        base = y * w * 3
        for x in range(x0, x1, 2):
            i = base + x * 3
            r, g, b = px[i], px[i + 1], px[i + 2]
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if lum > bl:
                bl, best = lum, (r, g, b)
            if lum < wl:
                wl, worst = lum, (r, g, b)
    return best, worst


def _alpha_for(color, text, scrim, target):
    """Smallest scrim alpha that moves `color` to a luminance with the wanted contrast against the text colour."""
    lt = TEXT_LUM[text]
    for k in range(0, 101):
        a = k / 100.0
        lum = luminance(mix(color, scrim, a))
        if (text == "white" and contrast(1.0, lum) >= target) or (text == "dark" and contrast(lum, lt) >= target):
            return a
    return 1.0


def apply_panel(cv, zone, color, alpha, feather=0.12):
    """A soft panel: `alpha` of `color` over the whole zone, fading to nothing over `feather` (fraction of the picture) outside it."""
    x0, y0, x1, y1 = zone_box(cv, zone)
    w, h, px = cv.w, cv.h, cv.px
    fx, fy = max(2, int(feather * w)), max(2, int(feather * h))
    ex0, ex1, ey0, ey1 = max(0, x0 - fx), min(w, x1 + fx), max(0, y0 - fy), min(h, y1 + fy)

    def ramp(v, lo, hi, f):
        if lo <= v < hi:
            return 1.0
        d = (lo - v) if v < lo else (v - hi + 1)
        t = max(0.0, 1.0 - d / float(f))
        return t * t * (3 - 2 * t)
    wx = [ramp(x, x0, x1, fx) for x in range(ex0, ex1)]
    cr, cg, cb = color
    for y in range(ey0, ey1):
        a_row = alpha * ramp(y, y0, y1, fy)
        if a_row <= 0.0005:
            continue
        base = y * w * 3 + ex0 * 3
        seg = px[base:base + (ex1 - ex0) * 3]
        out = []
        for k, wxv in enumerate(wx):
            a = a_row * wxv
            ia = 1.0 - a
            j = k * 3
            out += (seg[j] * ia + cr * a, seg[j + 1] * ia + cg * a, seg[j + 2] * ia + cb * a)
        px[base:base + (ex1 - ex0) * 3] = out


def ensure_zone_contrast(cv, zone, pal, prefer=None):
    """Choose the text colour needing the gentlest panel, apply it, and verify every pixel reaches 4.5:1. Returns a report dict."""
    target = CONTRAST_TARGET + 0.3
    bright, dark = _extremes(cv, zone)
    scrim_dark = pal.ink
    scrim_light = mix(pal.paper, (1.0, 1.0, 1.0), 0.6)
    a_white = _alpha_for(bright, "white", scrim_dark, target)
    a_dark = _alpha_for(dark, "dark", scrim_light, target)
    if prefer in ("white", "dark"):
        text = prefer
    else:
        rows = zone_luminances(cv, zone, 4)
        flat = sorted(v for r in rows for v in r)
        p98, p02 = flat[len(flat) * 98 // 100], flat[len(flat) * 2 // 100]
        text = "white" if max(0.0, p98 - 0.17) <= max(0.0, 0.23 - p02) else "dark"
    alpha = a_white if text == "white" else a_dark
    scrim = scrim_dark if text == "white" else scrim_light
    x0, y0, x1, y1 = zone_box(cv, zone)
    backup = None
    if alpha > 0:
        fx, fy = max(2, int(0.12 * cv.w)), max(2, int(0.12 * cv.h))
        ey0, ey1 = max(0, y0 - fy), min(cv.h, y1 + fy)
        backup = (ey0, ey1, cv.px[ey0 * cv.w * 3:ey1 * cv.w * 3])
    worst = worst_contrast(cv, zone, text)
    rounds = 0
    while worst < CONTRAST_TARGET and rounds < 6:
        alpha = min(1.0, max(alpha, 0.05) + (0.06 if rounds else 0.0))
        if backup is None:
            fx, fy = max(2, int(0.12 * cv.w)), max(2, int(0.12 * cv.h))
            ey0, ey1 = max(0, y0 - fy), min(cv.h, y1 + fy)
            backup = (ey0, ey1, cv.px[ey0 * cv.w * 3:ey1 * cv.w * 3])
        cv.px[backup[0] * cv.w * 3:backup[1] * cv.w * 3] = backup[2]
        apply_panel(cv, zone, scrim, alpha)
        worst = worst_contrast(cv, zone, text)
        rounds += 1
    return {"text_color": "#%02x%02x%02x" % tuple(int(c * 255 + 0.5) for c in TEXT[text]), "text": text,
            "contrast": round(worst, 2), "scrim": round(alpha, 2), "zone": [round(v, 3) for v in zone]}


# ---------------------------------------------------------------------------------------------- analysis
def small(cv, n=64):
    """n x n-ish thumbnail (list of rows of (r, g, b)) for the other metrics."""
    tw = n
    th = max(2, int(round(n * cv.h / float(cv.w))))
    fx, fy = cv.w / float(tw), cv.h / float(th)
    px, w = cv.px, cv.w
    rows = []
    for y in range(th):
        ya = int(y * fy)
        yb = max(ya + 1, int((y + 1) * fy))
        sy = max(1, (yb - ya) // 3)
        row = []
        for x in range(tw):
            xa = int(x * fx)
            xb = max(xa + 1, int((x + 1) * fx))
            sx = max(1, (xb - xa) // 3)
            r = g = b = c = 0.0
            for yy in range(ya, min(cv.h, yb), sy):
                base = yy * w * 3
                for xx in range(xa, min(w, xb), sx):
                    i = base + xx * 3
                    r += px[i]
                    g += px[i + 1]
                    b += px[i + 2]
                    c += 1
            row.append((clamp(r / c), clamp(g / c), clamp(b / c)))
        rows.append(row)
    return rows


def _gray32(thumb):
    th, tw = len(thumb), len(thumb[0])
    out = []
    for y in range(32):
        row = []
        for x in range(32):
            r, g, b = thumb[min(th - 1, y * th // 32)][min(tw - 1, x * tw // 32)]
            row.append(0.299 * r + 0.587 * g + 0.114 * b)
        out.append(row)
    return out


_COS = [[math.cos((2 * x + 1) * u * math.pi / 64.0) for x in range(32)] for u in range(8)]


def phash(thumb):
    """64-bit perceptual hash (DCT of a 32x32 grey thumbnail, top-left 8x8 against its median)."""
    g = _gray32(thumb)
    tmp = [[sum(g[y][x] * _COS[u][x] for x in range(32)) for u in range(8)] for y in range(32)]
    coef = [sum(tmp[y][u] * _COS[v][y] for y in range(32)) for v in range(8) for u in range(8)]
    rest = sorted(coef[1:])
    med = rest[len(rest) // 2]
    bits = 0
    for c in coef[1:]:
        bits = (bits << 1) | (1 if c > med else 0)
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


def detail_density(thumb, zone=None):
    """Share of the picture (outside the text zone) that has visible structure, and how many distinct colours it uses."""
    th, tw = len(thumb), len(thumb[0])
    lum = [[0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in row] for row in thumb]
    busy = total = 0
    colours = set()
    for y in range(1, th - 1):
        for x in range(1, tw - 1):
            if zone and zone[0] * tw <= x < zone[2] * tw and zone[1] * th <= y < zone[3] * th:
                continue
            total += 1
            gx = abs(lum[y][x + 1] - lum[y][x - 1])
            gy = abs(lum[y + 1][x] - lum[y - 1][x])
            if gx + gy > 0.035:
                busy += 1
            p = thumb[y][x]
            colours.add((int(p[0] * 7.99), int(p[1] * 7.99), int(p[2] * 7.99)))
    return busy / max(1, total), len(colours)


def hue_signature(thumb):
    """12-bin hue histogram weighted by saturation x value (greys count for nothing), normalised."""
    hist = [0.0] * 12
    for row in thumb:
        for r, g, b in row:
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            hist[int(h * 12) % 12] += s * s * v
    tot = sum(hist) or 1.0
    return [v / tot for v in hist]


def family_similarity(sig_a, sig_b):
    """0..1 overlap of two hue signatures, forgiving a one-bin shift (neighbouring hues are one family)."""
    def smooth(sig):
        return [0.25 * sig[(i - 1) % 12] + 0.5 * sig[i] + 0.25 * sig[(i + 1) % 12] for i in range(12)]
    a, b = smooth(sig_a), smooth(sig_b)
    return sum(min(x, y) for x, y in zip(a, b))
