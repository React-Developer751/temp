"""Software rasteriser: float RGB canvas, SDF shapes, noise (pure Python)."""
import math


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def scale(c, k):
    return (c[0] * k, c[1] * k, c[2] * k)


def tint(c, t):
    return (c[0] * t[0], c[1] * t[1], c[2] * t[2])


def lerp_stops(stops, t):
    if t <= stops[0][0]:
        return stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0) if p1 > p0 else 0.0)
    return stops[-1][1]


# ------------------------------------------------------------------ noise
class Noise:
    def __init__(self, seed):
        self.seed = seed & 0xFFFFFFFF

    def _h(self, i, j=0):
        n = (i * 374761393 + j * 668265263 + self.seed * 1442695041) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n ^ (n >> 16)) / 4294967295.0

    def v1(self, x):
        i = math.floor(x)
        f = x - i
        f = f * f * (3 - 2 * f)
        return self._h(i) * (1 - f) + self._h(i + 1) * f

    def v2(self, x, y):
        i, j = math.floor(x), math.floor(y)
        fx, fy = x - i, y - j
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        top = self._h(i, j) * (1 - fx) + self._h(i + 1, j) * fx
        bot = self._h(i, j + 1) * (1 - fx) + self._h(i + 1, j + 1) * fx
        return top * (1 - fy) + bot * fy

    def perlin2(self, x, y):
        """Gradient (Perlin) noise, about -0.7..0.7: smooth, no grid-aligned blockiness like value noise."""
        i, j = math.floor(x), math.floor(y)
        fx, fy = x - i, y - j
        u, v = fx * fx * fx * (fx * (fx * 6 - 15) + 10), fy * fy * fy * (fy * (fy * 6 - 15) + 10)

        def g(ix, iy, dx, dy):
            a = self._h(ix, iy + 7919) * 6.283185307179586
            return math.cos(a) * dx + math.sin(a) * dy
        n00, n10 = g(i, j, fx, fy), g(i + 1, j, fx - 1, fy)
        n01, n11 = g(i, j + 1, fx, fy - 1), g(i + 1, j + 1, fx - 1, fy - 1)
        top, bot = n00 + (n10 - n00) * u, n01 + (n11 - n01) * u
        return top + (bot - top) * v

    def fbm2(self, x, y, octaves=4):
        """Layered Perlin noise normalised to roughly 0..1 (clouds, terrain, flow directions)."""
        total = norm = 0.0
        amp, freq = 0.5, 1.0
        for o in range(octaves):
            total += amp * self.perlin2(x * freq + o * 31.7, y * freq - o * 17.3)
            norm += amp
            amp *= 0.5
            freq *= 2.0
        return 0.5 + 0.7 * total / norm

    def fbm1(self, x, octaves=4):
        total = norm = 0.0
        amp = 0.5
        for o in range(octaves):
            total += amp * self.v1(x * (2 ** o) + o * 17.3)
            norm += amp
            amp *= 0.5
        return total / norm


# ------------------------------------------------------------------ SDFs
def sdf_circle(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) - r


def sdf_box(cx, cy, hw, hh, rad=0.0):
    def f(x, y):
        qx = abs(x - cx) - hw + rad
        qy = abs(y - cy) - hh + rad
        return math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - rad
    return f


def sdf_ellipse(cx, cy, a, b, angle=0.0):
    ca, sa = math.cos(angle), math.sin(angle)
    m = min(a, b)

    def f(x, y):
        dx, dy = x - cx, y - cy
        lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
        return (math.hypot(lx / a, ly / b) - 1.0) * m
    return f


def sdf_capsule(ax, ay, bx, by, r):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy or 1e-9

    def f(x, y):
        t = clamp(((x - ax) * dx + (y - ay) * dy) / l2)
        return math.hypot(x - ax - dx * t, y - ay - dy * t) - r
    return f


def sdf_polygon(pts):
    n = len(pts)
    edges = []
    j = n - 1
    for i in range(n):
        ex, ey = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
        edges.append((pts[i][0], pts[i][1], pts[j][1], ex, ey, ex * ex + ey * ey or 1e-9))
        j = i
    x0, y0 = pts[0]

    def f(px, py):
        d = (px - x0) ** 2 + (py - y0) ** 2
        s = 1.0
        for ix, iy, jy, ex, ey, l2 in edges:
            wx, wy = px - ix, py - iy
            t = (wx * ex + wy * ey) / l2
            t = 0.0 if t < 0 else 1.0 if t > 1 else t
            bx, by = wx - ex * t, wy - ey * t
            dd = bx * bx + by * by
            if dd < d:
                d = dd
            c1, c2, c3 = py >= iy, py < jy, ex * wy > ey * wx
            if (c1 and c2 and c3) or (not c1 and not c2 and not c3):
                s = -s
        return s * math.sqrt(d)
    return f


def regular_polygon(cx, cy, r, n, rot=-math.pi / 2):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n),
             cy + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def star_points(cx, cy, r, inner=0.42, n=5):
    pts = []
    for k in range(2 * n):
        rad = r if k % 2 == 0 else r * inner
        a = -math.pi / 2 + math.pi * k / n
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


def heart_points(cx, cy, r, steps=48):
    pts = []
    for k in range(steps):
        t = 2 * math.pi * k / steps
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 17.0, cy + y * r / 17.0 + r * 0.05))
    return pts


def bbox_of(pts, pad=1.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, color=(0.0, 0.0, 0.0)):
        self.w, self.h = w, h
        self.px = list(color) * (w * h)
        self.solid_soft = False       # True: shapes with soft > 1 are fully opaque inside and fade only at the edge (blurred foreground)

    # --- fills
    def gradient_v(self, stops, y0=0, y1=None):
        y1 = self.h if y1 is None else y1
        span = max(1.0, y1 - y0)
        px, w = self.px, self.w
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            c = lerp_stops(stops, (y - y0) / span)
            row = [c[0], c[1], c[2]] * w
            px[y * w * 3:(y + 1) * w * 3] = row

    def fill_rect(self, x0, y0, x1, y1, color, alpha=1.0):
        x0, x1 = max(0, int(x0)), min(self.w, int(x1))
        y0, y1 = max(0, int(y0)), min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        px, w = self.px, self.w
        n = x1 - x0
        if alpha >= 0.999:
            span = [color[0], color[1], color[2]] * n               # whole row at once (C speed)
            for y in range(y0, y1):
                i = (y * w + x0) * 3
                px[i:i + n * 3] = span
            return
        ia = 1.0 - alpha
        add = [color[0] * alpha, color[1] * alpha, color[2] * alpha] * n
        for y in range(y0, y1):
            i = (y * w + x0) * 3
            px[i:i + n * 3] = [a * ia + b for a, b in zip(px[i:i + n * 3], add)]

    def blend(self, x, y, color, alpha=1.0):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            p, ia = self.px, 1.0 - alpha
            p[i] = p[i] * ia + color[0] * alpha
            p[i + 1] = p[i + 1] * ia + color[1] * alpha
            p[i + 2] = p[i + 2] * ia + color[2] * alpha

    # --- anti-aliased SDF shapes
    def shape(self, bbox, sdf, color, alpha=1.0, shade=None, soft=1.0):
        x0, y0, x1, y1 = bbox
        ix0, iy0 = max(0, int(math.floor(x0))), max(0, int(math.floor(y0)))
        ix1, iy1 = min(self.w, int(math.ceil(x1)) + 1), min(self.h, int(math.ceil(y1)) + 1)
        px, w = self.px, self.w
        half = 0.5 * soft
        for y in range(iy0, iy1):
            fy = y + 0.5
            for x in range(ix0, ix1):
                d = sdf(x + 0.5, fy)
                if d >= half:
                    continue
                if soft == 1.0:
                    a = 1.0 if d <= -0.5 else 0.5 - d
                elif self.solid_soft:
                    a = 1.0 if d <= -half else (half - d) / soft
                else:
                    a = (1.0 if d <= -half else half - d) / soft
                if a > 1.0:
                    a = 1.0
                a *= alpha
                c = shade(x, y) if shade else color
                i = (y * w + x) * 3
                if a >= 0.999:
                    px[i], px[i + 1], px[i + 2] = c
                else:
                    ia = 1.0 - a
                    px[i] = px[i] * ia + c[0] * a
                    px[i + 1] = px[i + 1] * ia + c[1] * a
                    px[i + 2] = px[i + 2] * ia + c[2] * a

    def circle(self, cx, cy, r, color, alpha=1.0, shade=None, soft=1.0):
        pad = 1 + soft
        self.shape((cx - r - pad, cy - r - pad, cx + r + pad, cy + r + pad),
                   sdf_circle(cx, cy, r), color, alpha, shade, soft)

    def box(self, cx, cy, hw, hh, color, rad=0.0, alpha=1.0, shade=None, soft=1.0):
        pad = 1 + soft
        self.shape((cx - hw - pad, cy - hh - pad, cx + hw + pad, cy + hh + pad),
                   sdf_box(cx, cy, hw, hh, rad), color, alpha, shade, soft)

    def ellipse(self, cx, cy, a, b, color, angle=0.0, alpha=1.0, shade=None, soft=1.0):
        r = max(a, b) + 1 + soft
        self.shape((cx - r, cy - r, cx + r, cy + r), sdf_ellipse(cx, cy, a, b, angle),
                   color, alpha, shade, soft)

    def polygon(self, pts, color, alpha=1.0, shade=None, soft=1.0):
        self.shape(bbox_of(pts, 1 + soft), sdf_polygon(pts), color, alpha, shade, soft)

    def capsule(self, ax, ay, bx, by, r, color, alpha=1.0):
        pad = r + 2
        self.shape((min(ax, bx) - pad, min(ay, by) - pad, max(ax, bx) + pad, max(ay, by) + pad),
                   sdf_capsule(ax, ay, bx, by, r), color, alpha)

    def glow(self, cx, cy, r, color, strength=1.0, power=2.0):
        px, w = self.px, self.w
        for y in range(max(0, int(cy - r)), min(self.h, int(cy + r) + 1)):
            dy = y + 0.5 - cy
            for x in range(max(0, int(cx - r)), min(w, int(cx + r) + 1)):
                d = math.hypot(x + 0.5 - cx, dy) / r
                if d < 1.0:
                    a = strength * (1.0 - d) ** power
                    i = (y * w + x) * 3
                    px[i] = min(1.0, px[i] + color[0] * a)
                    px[i + 1] = min(1.0, px[i + 1] + color[1] * a)
                    px[i + 2] = min(1.0, px[i + 2] + color[2] * a)

    def terrain(self, tops, base, shade, alpha=1.0):
        """Fill under a height-field. tops[x] = y of the ridge (float)."""
        px, w = self.px, self.w
        base = min(self.h, int(base))
        for x in range(w):
            t = tops[x]
            for y in range(max(0, int(math.floor(t))), base):
                a = min(1.0, y + 1 - t) * alpha
                if a <= 0:
                    continue
                c = shade(x, y, y - t)
                i = (y * w + x) * 3
                if a >= 0.999:
                    px[i], px[i + 1], px[i + 2] = c
                else:
                    ia = 1.0 - a
                    px[i] = px[i] * ia + c[0] * a
                    px[i + 1] = px[i + 1] * ia + c[1] * a
                    px[i + 2] = px[i + 2] * ia + c[2] * a

    # --- post processing
    def vignette(self, strength=0.25):
        px, w, h = self.px, self.w, self.h
        cx, cy = w / 2.0, h / 2.0
        maxd = math.hypot(cx, cy)
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy) / maxd
                k = 1.0 - strength * d * d
                i = (y * w + x) * 3
                px[i] *= k
                px[i + 1] *= k
                px[i + 2] *= k

    def grain(self, rng, amount):
        px = self.px
        for i in range(len(px)):
            px[i] += (rng.random() - 0.5) * amount

    def to_rgb_bytes(self):
        return bytes(int(clamp(v) * 255.0 + 0.5) for v in self.px)
