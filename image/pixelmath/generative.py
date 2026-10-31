"""Generative mathematics: fractals, L-systems, Perlin flow fields and noise textures.

These pictures are not drawn from a list of known objects: they come out of equations iterated many times, so a different
seed gives a genuinely different picture. They are painted with colour-theory palettes (`palette.py`).

    fractal   Mandelbrot and Julia sets (smooth escape-time colouring, a hand-picked list of interesting regions)
    lsystem   fractal tree, Barnsley fern (IFS), Koch snowflake, dragon curve, Sierpinski triangle
    flow      thousands of strokes that follow a Perlin-noise vector field
    texture   domain-warped Perlin noise: plasma / clouds / marble veins

Fractals and textures are computed on a grid of at most 320 / 160 pixels and smoothly enlarged (pure Python: a full-size
Mandelbrot would take minutes); L-systems and flow fields are drawn at the real resolution.
"""
import math

from .palette import gradient, harmonic_palette
from .raster import Canvas, clamp, mix, scale

WHITE = (1.0, 1.0, 1.0)
MODES = ("fractal", "lsystem", "flow", "texture")
FRACTAL_RES, TEXTURE_RES = 320, 160

MANDEL_VIEWS = (                       # (centre re, centre im, width) of regions that are known to be rich
    (-0.5, 0.0, 3.0), (-0.743643887037151, 0.131825904205330, 0.012), (-0.7269, 0.1889, 0.03), (0.275, 0.0, 0.25),
    (-0.1011, 0.9563, 0.03), (-1.25066, 0.02012, 0.02), (-1.7497, 0.0, 0.06), (-0.16, 1.0405, 0.05),
    (-0.8, 0.156, 0.4), (0.3, 0.02, 0.1),
)
JULIA_CONSTANTS = ((-0.8, 0.156), (0.285, 0.01), (-0.4, 0.6), (-0.70176, -0.3842), (0.355, 0.355), (-0.835, -0.2321),
                   (-0.74543, 0.11301), (0.37, -0.1), (-0.12, 0.74), (-0.162, 1.04))


def _upscale(cv, buf, bw, bh):
    """Bilinear enlargement of a bw x bh grid of (r, g, b) tuples into the whole canvas."""
    w, h = cv.w, cv.h
    xs = []
    for x in range(w):
        sx = min(max((x + 0.5) * bw / w - 0.5, 0.0), bw - 1.001)
        xs.append((int(sx), sx - int(sx)))
    px = cv.px
    for y in range(h):
        sy = min(max((y + 0.5) * bh / h - 0.5, 0.0), bh - 1.001)
        y0, fy = int(sy), sy - int(sy)
        r0, r1 = buf[y0], buf[min(bh - 1, y0 + 1)]
        i = y * w * 3
        for x0, fx in xs:
            a, b, c, d = r0[x0], r0[min(bw - 1, x0 + 1)], r1[x0], r1[min(bw - 1, x0 + 1)]
            for k in range(3):
                top = a[k] + (b[k] - a[k]) * fx
                bot = c[k] + (d[k] - c[k]) * fx
                px[i] = top + (bot - top) * fy
                i += 1


def _lut(pal, n=512):
    return [gradient(pal, k / float(n)) for k in range(n)]


# ------------------------------------------------------------------------------------------------ fractals
def fractal_scene(parsed, w, h, rng, noise, vec):
    pal = harmonic_palette(parsed, vec, 5)
    flags = parsed.flags
    kind = "julia" if "julia" in flags else "mandelbrot" if "mandelbrot" in flags else rng.choice(("mandelbrot", "julia", "mandelbrot"))
    scale_ = min(1.0, FRACTAL_RES / float(max(w, h)))
    bw, bh = max(8, int(w * scale_)), max(8, int(h * scale_))
    if kind == "mandelbrot":
        cx, cy, span = MANDEL_VIEWS[rng.randrange(len(MANDEL_VIEWS))]
        span *= rng.uniform(0.7, 1.3)
        cx += rng.uniform(-0.15, 0.15) * span
        cy += rng.uniform(-0.15, 0.15) * span
        jc = None
    else:
        jc = JULIA_CONSTANTS[rng.randrange(len(JULIA_CONSTANTS))]
        jc = (jc[0] + rng.uniform(-0.01, 0.01), jc[1] + rng.uniform(-0.01, 0.01))
        cx, cy, span = rng.uniform(-0.15, 0.15), rng.uniform(-0.1, 0.1), rng.uniform(2.2, 3.2)
    maxit = int(80 + 28 * math.log2(max(1.0, 3.0 / span)))
    lut = _lut(pal)
    nlut = len(lut)
    phase = rng.random()
    freq = rng.uniform(0.025, 0.06)
    inside = scale(pal[0], 0.07)
    ln2 = math.log(2.0)
    height_c = span * bh / bw
    buf = []
    for py in range(bh):
        row = []
        im0 = cy + (py / (bh - 1.0) - 0.5) * height_c
        for px_ in range(bw):
            re0 = cx + (px_ / (bw - 1.0) - 0.5) * span
            if jc is None:
                c_re, c_im, zr, zi = re0, im0, 0.0, 0.0
                q = (re0 - 0.25) ** 2 + im0 * im0
                if q * (q + re0 - 0.25) <= 0.25 * im0 * im0 or (re0 + 1.0) ** 2 + im0 * im0 <= 0.0625:
                    row.append(inside)
                    continue
            else:
                c_re, c_im = jc
                zr, zi = re0, im0
            n = 0
            zr2, zi2 = zr * zr, zi * zi
            while zr2 + zi2 <= 256.0 and n < maxit:
                zi = 2.0 * zr * zi + c_im
                zr = zr2 - zi2 + c_re
                zr2, zi2 = zr * zr, zi * zi
                n += 1
            if n >= maxit:
                row.append(inside)
            else:
                mu = n + 1.0 - math.log(max(1e-12, math.log(zr2 + zi2) / 2.0)) / ln2
                row.append(lut[int(((mu * freq + phase) % 1.0) * nlut) % nlut])
        buf.append(row)
    cv = Canvas(w, h)
    _upscale(cv, buf, bw, bh)
    return cv


# ------------------------------------------------------------------------------------------------ L-systems
def _fit(points, w, h, margin=0.08):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = min(w * (1 - 2 * margin) / max(1e-9, x1 - x0), h * (1 - 2 * margin) / max(1e-9, y1 - y0))
    ox = w / 2 - (x0 + x1) / 2 * sc
    oy = h / 2 - (y0 + y1) / 2 * sc
    return lambda x, y: (x * sc + ox, y * sc + oy), sc


def _turtle(s, angle, step=1.0, start=0.0):
    x = y = 0.0
    a = math.radians(start)
    segs = []
    for ch in s:
        if ch in "FAB":
            nx, ny = x + step * math.cos(a), y - step * math.sin(a)
            segs.append((x, y, nx, ny))
            x, y = nx, ny
        elif ch == "+":
            a += math.radians(angle)
        elif ch == "-":
            a -= math.radians(angle)
    return segs


def _rewrite(axiom, rules, n):
    s = axiom
    for _ in range(n):
        s = "".join(rules.get(c, c) for c in s)
    return s


def _fill_polygon(cv, pts, color, alpha):
    """Even-odd scanline fill (the SDF polygon fill is far too slow for a 768-point outline)."""
    ia = 1.0 - alpha
    n = len(pts)
    for y in range(max(0, int(min(p[1] for p in pts))), min(cv.h, int(max(p[1] for p in pts)) + 1)):
        yc = y + 0.5
        xs = []
        for k in range(n):
            (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % n]
            if (y0 <= yc < y1) or (y1 <= yc < y0):
                xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, int(a + 0.5)), min(cv.w, int(b + 0.5))):
                i = (y * cv.w + x) * 3
                px = cv.px
                px[i] = px[i] * ia + color[0] * alpha
                px[i + 1] = px[i + 1] * ia + color[1] * alpha
                px[i + 2] = px[i + 2] * ia + color[2] * alpha


def _background(cv, pal, dark=0.10):
    cv.gradient_v([(0, scale(pal[0], dark * 1.6)), (1, scale(pal[1 % len(pal)], dark))])


def _stroke(cv, segs, to_px, radius, color_at, alpha=0.95):
    n = len(segs)
    for k, seg in enumerate(segs):
        ax, ay = to_px(seg[0], seg[1])
        bx, by = to_px(seg[2], seg[3])
        r = radius(k, n, seg)
        cv.capsule(ax, ay, bx, by, max(0.5, r), color_at(k, n, seg), alpha)


def lsystem_scene(parsed, w, h, rng, noise, vec):
    pal = harmonic_palette(parsed, vec, 5)
    flags = parsed.flags
    names = {e.name for e in parsed.entities}
    kinds = [k for k in ("koch", "fern", "dragon", "sierpinski") if k in flags]
    kind = kinds[0] if kinds else ("tree" if "tree" in names else rng.choice(("tree", "fern", "dragon", "koch", "sierpinski", "tree")))
    cv = Canvas(w, h)
    s = min(w, h)
    if kind == "koch":
        pal = harmonic_palette(parsed, vec, 5) if parsed.loose_colors or parsed.entities else [(0.55, 0.8, 1.0), (0.8, 0.92, 1.0), (0.4, 0.6, 0.95), (0.9, 0.95, 1.0), (0.3, 0.45, 0.85)]
        _background(cv, [scale(pal[2], 0.45), scale(pal[0], 0.25)])
        segs = _turtle(_rewrite("F--F--F", {"F": "F+F--F+F"}, 4), 60, 1.0, 0.0)
        pts = [(sg[0], sg[1]) for sg in segs]
        to_px, sc = _fit(pts, w, h, 0.1)
        cv.glow(w / 2, h / 2, s * 0.55, pal[0], 0.28, 2.0)
        _fill_polygon(cv, [to_px(*p) for p in pts], mix(pal[1], WHITE, 0.3), 0.28)
        _stroke(cv, segs, to_px, lambda k, n, sg: 0.0035 * s + 0.002 * s, lambda k, n, sg: gradient(pal, k / float(n) * 2.0))
    elif kind == "dragon":
        _background(cv, pal)
        turns = [1]
        for _ in range(12):
            turns = turns + [1] + [-t for t in reversed(turns)]
        x = y = 0.0
        a = 0.0
        segs = []
        for t in [0] + turns:
            a += t * math.pi / 2
            nx, ny = x + math.cos(a), y - math.sin(a)
            segs.append((x, y, nx, ny))
            x, y = nx, ny
        to_px, sc = _fit([(sg[0], sg[1]) for sg in segs] + [(segs[-1][2], segs[-1][3])], w, h, 0.1)
        _stroke(cv, segs, to_px, lambda k, n, sg: 0.0009 * s + 0.35, lambda k, n, sg: gradient(pal, k / float(n)))
    elif kind == "sierpinski":
        _background(cv, pal)
        segs = _turtle(_rewrite("A", {"A": "B-A-B", "B": "A+B+A"}, 6), 60, 1.0, 0.0)
        to_px, sc = _fit([(sg[0], sg[1]) for sg in segs] + [(segs[-1][2], segs[-1][3])], w, h, 0.1)
        _stroke(cv, segs, to_px, lambda k, n, sg: 0.0022 * s + 0.4, lambda k, n, sg: gradient(pal, k / float(n)))
    elif kind == "fern":
        pal = harmonic_palette(parsed, vec, 5) if parsed.loose_colors or parsed.entities else [(0.12, 0.55, 0.18), (0.45, 0.8, 0.25), (0.75, 0.9, 0.35), (0.2, 0.65, 0.45)]
        _background(cv, [scale(pal[0], 0.6), scale(pal[1], 0.3)], 0.12)
        maps = ((0.0, 0.0, 0.0, 0.16, 0.0, 0.0, 0.01), (0.85, 0.04, -0.04, 0.85, 0.0, 1.6, 0.85),
                (0.2, -0.26, 0.23, 0.22, 0.0, 1.6, 0.07), (-0.15, 0.28, 0.26, 0.24, 0.0, 0.44, 0.07))
        x = y = 0.0
        pts = []
        jitter = rng.uniform(-0.02, 0.02)
        for k in range(int(min(70000, max(12000, w * h / 5)))):
            r = rng.random()
            acc = 0.0
            for a, b, c, d, e, f, p in maps:
                acc += p
                if r <= acc:
                    x, y = a * x + b * y + e + jitter * y, c * x + d * y + f
                    break
            if k > 20:
                pts.append((x, y))
        to_px, sc = _fit(pts, w, h, 0.07)
        ymax = max(p[1] for p in pts)
        for px_, py_ in pts:
            x_, y_ = to_px(px_, py_)
            x_, y_ = int(x_), int(y_)
            col = gradient(pal, py_ / ymax * 0.8, loop=False)
            cv.blend(x_, y_, col, 0.75)
            cv.blend(x_ + 1, y_, col, 0.4)
        cv.glow(w / 2, h * 0.55, s * 0.5, pal[1], 0.12, 2.0)
    else:                                                                  # fractal tree
        pal = harmonic_palette(parsed, vec, 5)
        _background(cv, pal, 0.14)
        depth = rng.choice((9, 10))
        segs = []
        spread0 = rng.uniform(0.25, 0.42)

        def grow(x, y, ang, ln, d):
            if len(segs) > 5000:
                return
            x1, y1 = x + ln * math.sin(ang), y - ln * math.cos(ang)
            segs.append((x, y, x1, y1, d))
            if d >= depth:
                return
            k = 3 if rng.random() < 0.1 else 2
            for j in range(k):
                a = ang + spread0 * 2.0 * (j - (k - 1) / 2.0) + rng.uniform(-0.15, 0.15)
                grow(x1, y1, a, ln * rng.uniform(0.67, 0.80), d + 1)
        grow(0.0, 0.0, rng.uniform(-0.05, 0.05), 1.0, 0)
        to_px, sc = _fit([(sg[0], sg[1]) for sg in segs] + [(sg[2], sg[3]) for sg in segs], w, h, 0.07)
        for sg in sorted(segs, key=lambda t: t[4]):
            d = sg[4]
            ax, ay = to_px(sg[0], sg[1])
            bx, by = to_px(sg[2], sg[3])
            t = d / float(depth)
            col = mix(scale(pal[0], 0.55), pal[1 + (d % 3) % (len(pal) - 1)], t ** 0.8)
            cv.capsule(ax, ay, bx, by, max(0.5, 0.009 * s * (0.74 ** d)), col, 0.95)
            if d == depth:
                cv.circle(bx, by, 0.006 * s, mix(pal[2], WHITE, 0.4), alpha=0.8, soft=1.5)
    return cv


# ------------------------------------------------------------------------------------------------ flow field + textures
def flow_scene(parsed, w, h, rng, noise, vec):
    pal = harmonic_palette(parsed, vec, 5)
    cv = Canvas(w, h)
    _background(cv, [scale(pal[0], 0.9), scale(pal[1], 0.8)], 0.22)
    s = min(w, h)
    freq = rng.uniform(1.4, 3.0)
    swirl = rng.uniform(1.6, 3.2)
    spacing = max(6.0, s / 34.0)
    step = 0.010 * s
    ox, oy = rng.uniform(0, 100), rng.uniform(0, 100)

    def angle(x, y):
        return (noise.fbm2(x / s * freq + ox, y / s * freq + oy, 3) - 0.5) * 2.0 * math.pi * swirl

    gy = -spacing
    while gy < h + spacing:
        gx = -spacing
        while gx < w + spacing:
            x, y = gx + rng.uniform(-0.5, 0.5) * spacing, gy + rng.uniform(-0.5, 0.5) * spacing
            n = rng.randint(24, 64)
            width = rng.uniform(0.5, 1.5) * (s / 512.0 + 0.4)
            tcol = noise.fbm2(x / s * 1.3 + 50, y / s * 1.3 + 50, 2)
            col = gradient(pal, tcol * 1.4, loop=True)
            for k in range(n):
                a = angle(x, y)
                nx, ny = x + step * math.cos(a), y + step * math.sin(a)
                fade = math.sin(math.pi * k / n)
                cv.capsule(x, y, nx, ny, width * (0.4 + 0.6 * fade), col, 0.55 * (0.3 + 0.7 * fade))
                x, y = nx, ny
            gx += spacing
        gy += spacing
    return cv


def texture_scene(parsed, w, h, rng, noise, vec):
    pal = harmonic_palette(parsed, vec, 5)
    marble = "marble" in parsed.flags
    scale_ = min(1.0, TEXTURE_RES / float(max(w, h)))
    bw, bh = max(8, int(w * scale_)), max(8, int(h * scale_))
    lut = _lut(pal, 256)
    f = rng.uniform(1.6, 3.0)
    ox, oy = rng.uniform(0, 100), rng.uniform(0, 100)
    warp = rng.uniform(1.2, 2.4)
    buf = []
    for y in range(bh):
        row = []
        ny = y / float(bh) * f * (bh / float(max(bw, bh))) + oy
        for x in range(bw):
            nx = x / float(bw) * f * (bw / float(max(bw, bh))) + ox
            qx = noise.fbm2(nx, ny, 3)
            qy = noise.fbm2(nx + 5.2, ny + 1.3, 3)
            v = noise.fbm2(nx + warp * qx * 2.0, ny + warp * qy * 2.0, 4)
            if marble:
                v = 0.5 + 0.5 * math.sin((nx * 2.0 + v * 6.0) * math.pi)
                v = v * v * (3 - 2 * v)
            row.append(lut[int(clamp(v) * 255)])
        buf.append(row)
    cv = Canvas(w, h)
    _upscale(cv, buf, bw, bh)
    return cv


def render_generative(mode, parsed, w, h, rng, noise, vec):
    return {"fractal": fractal_scene, "lsystem": lsystem_scene, "flow": flow_scene, "texture": texture_scene}[mode](
        parsed, w, h, rng, noise, vec)
