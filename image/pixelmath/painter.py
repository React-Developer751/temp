"""Object painters: every drawable concept (sun, tree, city, ...) as pure maths."""
import math

from .raster import Canvas, clamp, mix, scale, sdf_ellipse, tint

WHITE = (1.0, 1.0, 1.0)


class Painter:
    def __init__(self, w, h, rng, noise, style, light=WHITE):
        self.cv = Canvas(w, h)
        self.w, self.h, self.s = w, h, min(w, h)
        self.rng, self.noise, self.style, self.light = rng, noise, style, light
        self.horizon = h * 0.62
        self.glint = None          # (x, radius, colour) of the sun/moon, for water reflections
        self.night = False
        self.sign_text = None      # first "quoted text" of the prompt: written on a shop sign / tag if there is one
        self.sign_used = False
        self.sky_stops = [(0, (0, 0, 0)), (1, (0, 0, 0))]

    # ------------------------------------------------------------ colour
    def col(self, base, explicit=False):
        """Default palette colours get the style tint; every colour gets scene light."""
        if not explicit:
            base = self.style.tint(base)
        lt = mix(WHITE, self.light, 0.45) if explicit else self.light
        return tint(base, lt)

    # ------------------------------------------------------------ sky
    def sky(self, stops):
        self.sky_stops = stops
        self.cv.gradient_v(stops, 0, self.horizon)

    def horizon_color(self):
        return self.sky_stops[-1][1]

    def stars(self, n, ymax):
        cv, rng = self.cv, self.rng
        for _ in range(n):
            x, y = rng.uniform(0, self.w), rng.uniform(0, ymax)
            b = rng.random() ** 2
            cv.blend(int(x), int(y), (1.0, 1.0, 0.95), 0.25 + 0.75 * b)
            if b > 0.8:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv.blend(int(x) + dx, int(y) + dy, WHITE, 0.35 * b)

    def sun(self, x, y, r, color):
        cv = self.cv
        cv.glow(x, y, r * 7, color, 0.30, 2.0)
        cv.glow(x, y, r * 2.6, color, 0.55, 2.0)
        core = mix(color, WHITE, 0.7)
        cv.circle(x, y, r, color,
                  shade=lambda px, py: mix(core, color, clamp(math.hypot(px - x, py - y) / r)))
        self.glint = (x, r, color)

    def moon(self, x, y, r, color):
        cv = self.cv
        cv.glow(x, y, r * 5, (0.55, 0.65, 1.0), 0.28, 2.0)
        cv.circle(x, y, r, color)
        for dx, dy, cr in ((-0.3, -0.2, 0.22), (0.28, 0.15, 0.27), (-0.1, 0.5, 0.14),
                           (0.35, -0.4, 0.12)):
            cv.circle(x + dx * r, y + dy * r, cr * r, scale(color, 0.82), alpha=0.55)
        self.glint = (x, r, (0.75, 0.82, 1.0))

    def cloud(self, x, y, sc, alpha=0.95):
        cv = self.cv
        top, bot = self.col(WHITE), self.col((0.78, 0.83, 0.92))
        puffs = ((-0.32, 0.05, 0.16), (-0.14, -0.05, 0.22), (0.08, -0.10, 0.25),
                 (0.30, -0.01, 0.19), (0.45, 0.06, 0.12))
        for dx, dy, r in puffs:
            cx, cy, rr = x + dx * sc, y + dy * sc, r * sc
            cv.circle(cx, cy, rr, top, alpha,
                      shade=lambda px, py: mix(top, bot, clamp((py - cy + rr) / (2 * rr))))
        cv.box(x + 0.07 * sc, y + 0.1 * sc, 0.5 * sc, 0.07 * sc, bot, rad=0.07 * sc, alpha=alpha)

    def rainbow(self, cx, cy, r):
        bands = [(0.9, 0.1, 0.1), (1.0, 0.5, 0.05), (1.0, 0.9, 0.1), (0.2, 0.75, 0.25),
                 (0.2, 0.5, 0.95), (0.35, 0.25, 0.75), (0.6, 0.25, 0.7)]
        bw = r * 0.045
        for k, c in enumerate(bands):
            rr = r - k * bw
            ring = lambda x, y, rr=rr: abs(math.hypot(x - cx, y - cy) - rr) - bw * 0.5
            self.cv.shape((cx - rr - bw, cy - rr - bw, cx + rr + bw, cy), ring,
                          self.col(c), alpha=0.5)

    def planet(self, x, y, r, color, ring=False):
        cv = self.cv
        lx, ly = -0.6, -0.8
        dark = scale(color, 0.12)

        def shade(px, py):
            nx, ny = (px - x) / r, (py - y) / r
            nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
            lam = clamp(nx * lx + ny * ly + 0.5 * nz)
            band = 0.93 + 0.07 * math.sin(ny * 14 + self.noise.v1(ny * 3) * 4)
            return mix(dark, scale(color, band), lam ** 0.8)

        cv.glow(x, y, r * 2.2, color, 0.18, 2.0)
        ring_c = mix(color, WHITE, 0.4)
        if ring:
            ring_sdf = sdf_ellipse(x, y, r * 2.0, r * 0.55)
            rs = lambda px, py: abs(ring_sdf(px, py)) - r * 0.1
            cv.shape((x - r * 2.4, y - r * 1.4, x + r * 2.4, y + r * 1.4), rs, ring_c, alpha=0.5)
        cv.circle(x, y, r, color, shade=shade)
        if ring:
            front = lambda px, py: max(rs(px, py), y - py)        # lower half of the ring
            cv.shape((x - r * 2.4, y, x + r * 2.4, y + r * 1.4), front, ring_c, alpha=0.7)

    def nebula(self, n=9):
        rng, s = self.rng, self.s
        palette = [(0.5, 0.1, 0.6), (0.1, 0.3, 0.8), (0.8, 0.2, 0.4), (0.1, 0.6, 0.7)]
        for _ in range(n):
            c = palette[rng.randrange(len(palette))]
            self.cv.glow(rng.uniform(0, self.w), rng.uniform(0, self.h),
                         rng.uniform(0.25, 0.5) * s, self.style.tint(c), rng.uniform(0.12, 0.25), 1.6)

    def galaxy(self, cx, cy, r, color):
        rng, cv = self.rng, self.cv
        cv.glow(cx, cy, r * 0.9, mix(color, WHITE, 0.5), 0.55, 2.0)
        for arm in range(2):
            for k in range(1100):
                t = k / 1100.0
                ang = t * 5.5 + arm * math.pi
                rad = r * (0.08 + 0.92 * t)
                x = cx + rad * math.cos(ang) + rng.gauss(0, r * 0.035 * (1 + t))
                y = cy + rad * 0.45 * math.sin(ang) + rng.gauss(0, r * 0.02 * (1 + t))
                cv.blend(int(x), int(y), mix(WHITE, color, t), 0.55 * (1 - 0.6 * t))

    # ------------------------------------------------------------ terrain
    def mountains(self, base, amp, freq, c_top, c_bot, snow=False, seed=0.0, alpha=1.0):
        n, w = self.noise, self.w
        tops = []
        for x in range(w):
            v = n.fbm1(x * freq / self.s + seed, 5)
            ridge = 1.0 - abs(2.0 * v - 1.0)
            tops.append(base - amp * (0.18 + 0.82 * ridge ** 1.4))
        lo = min(tops)
        snow_line = base - amp * 0.62
        snow_depth = [max(0.0, snow_line - t) * 1.5 for t in tops]
        slopes = [(tops[min(w - 1, x + 5)] - tops[max(0, x - 5)]) / 10.0 for x in range(w)]
        side = 1.0 if self.style.light_x >= 0.5 else -1.0
        c_top, c_bot = self.col(c_top), self.col(c_bot)
        snow_c = self.col((0.95, 0.97, 1.0)) if snow else None

        def shade(x, y, depth):
            f = 1.0 + clamp(slopes[x] * 0.2 * side, -0.3, 0.3) * clamp(1.0 - depth / (amp * 0.45))
            if snow_c and depth < snow_depth[x] + 3 * n.v2(x * 0.1, y * 0.1):
                return scale(snow_c, clamp(f, 0.75, 1.05))
            return scale(mix(c_top, c_bot, clamp((y - lo) / max(1.0, base - lo))), f)

        self.cv.terrain(tops, base + 2, shade, alpha)

    def hills(self, base, amp, c_top, c_bot, seed=0.0, freq=2.0):
        n = self.noise
        tops = [base - amp * n.fbm1(x * freq / self.s + seed, 3) for x in range(self.w)]
        c_top, c_bot = self.col(c_top), self.col(c_bot)
        lo = min(tops)
        span = max(1.0, self.h - lo)
        tex = self.style.texture

        def shade(x, y, depth):
            k = 0.94 + 0.12 * n.v2(x * 0.06 * tex, y * 0.12)
            return scale(mix(c_top, c_bot, clamp((y - lo) / span)), k)

        self.cv.terrain(tops, self.h, shade)

    def ground(self, c_far, c_near, top=None, rough=2.5):
        n = self.noise
        hz = self.horizon if top is None else top
        tops = [hz + rough * n.fbm1(x * 3.0 / self.s, 3) for x in range(self.w)]
        c_far, c_near = self.col(c_far), self.col(c_near)
        span = max(1.0, self.h - hz)
        tex = self.style.texture

        def shade(x, y, depth):
            t = (y - hz) / span
            k = 0.92 + 0.16 * n.v2(x * 0.05 * tex / (0.2 + t), y * 0.09 * tex)
            return scale(mix(c_far, c_near, t), k)

        self.cv.terrain(tops, self.h, shade)

    def sea(self, deep, bottom=None):
        cv, n, hz = self.cv, self.noise, self.horizon
        bottom = self.h if bottom is None else min(self.h, int(bottom))
        near = self.col(deep)
        far = mix(self.horizon_color(), near, 0.3)
        span = max(1.0, bottom - hz)
        px, w = cv.px, self.w
        glint = self.glint
        for y in range(int(hz), int(bottom)):
            t = max(0.0, (y - hz) / span)
            base = mix(far, near, t ** 0.7)
            for x in range(w):
                phase = 2.4 / (0.07 + t) + n.v2(x * 0.012 / (0.2 + t), y * 0.04) * 7
                broken = n.v2(x * 0.03 / (0.2 + t), y * 0.25)
                hl = max(0.0, math.sin(phase)) ** 6 * (0.06 + 0.16 * t) * (1.0 if broken > 0.45 else 0.0)
                c = (base[0] + hl, base[1] + hl, base[2] + hl)
                if glint:
                    gx, gr, gc = glint
                    width = gr * (0.6 + 2.4 * t)
                    g = math.exp(-((x - gx) / width) ** 2)
                    if g > 0.02:
                        g *= (0.35 + 0.65 * n.v2(x * 0.15, y * 0.9)) * (1 - 0.5 * t)
                        c = (c[0] + gc[0] * g, c[1] + gc[1] * g, c[2] + gc[2] * g)
                i = (y * w + x) * 3
                px[i], px[i + 1], px[i + 2] = c

    def shore(self, top, c_far, c_near):
        """Sand/grass strip along the bottom with a foam line (used by beach scenes)."""
        n, w = self.noise, self.w
        tops = [top + 7 * math.sin(x * 0.02) + 4 * n.fbm1(x * 4.0 / self.s, 3) for x in range(w)]
        c_far, c_near = self.col(c_far), self.col(c_near)
        span = max(1.0, self.h - top)

        def shade(x, y, depth):
            k = 0.95 + 0.1 * n.v2(x * 0.2, y * 0.2)
            wet = clamp(1.0 - depth / 10.0)
            return scale(mix(mix(c_far, c_near, (y - top) / span), (0.5, 0.45, 0.35), wet * 0.5), k)

        self.cv.terrain(tops, self.h, shade)
        for x in range(w):
            self.cv.blend(x, int(tops[x]) - 1, WHITE, 0.55)

    # ------------------------------------------------------------ props
    def shadow(self, x, y, w):
        self.cv.ellipse(x, y, w, w * 0.22, (0, 0, 0), alpha=0.28, soft=3.0)

    def tree(self, x, yb, h, leaf=None, conifer=False, snowy=False):
        cv = self.cv
        trunk = self.col((0.38, 0.25, 0.14))
        self.shadow(x, yb, h * 0.28)
        snow_c = self.col((0.95, 0.97, 1.0))
        if conifer:
            leaf_c = self.col(leaf or (0.10, 0.36, 0.22), explicit=leaf is not None)
            cv.box(x, yb - h * 0.08, h * 0.035, h * 0.08, trunk)
            for k in range(3):
                top_y = yb - h * (0.18 + 0.27 * k + 0.35 * (1 - k * 0.15))
                base_y = yb - h * (0.10 + 0.26 * k)
                half = h * (0.26 - 0.055 * k)
                kk = 1.0 - 0.12 * (2 - k)
                tri = [(x, top_y), (x + half, base_y), (x - half, base_y)]
                cv.polygon(tri, leaf_c,
                           shade=lambda px, py: scale(leaf_c, kk * (1.1 - 0.35 * ((px - x) / half * 0.5 + 0.5))))
                if snowy:
                    my = top_y + (base_y - top_y) * 0.55
                    cv.polygon([(x, top_y), (x + half * 0.55, my), (x - half * 0.55, my)], snow_c, alpha=0.9)
            return
        leaf_c = self.col(leaf or (0.20, 0.55, 0.22), explicit=leaf is not None)
        cv.box(x, yb - h * 0.2, h * 0.04, h * 0.2, trunk)
        blobs = ((0, -0.62, 0.27), (-0.2, -0.5, 0.2), (0.21, -0.5, 0.2), (0.02, -0.82, 0.19),
                 (-0.12, -0.7, 0.17), (0.15, -0.72, 0.17))
        for dx, dy, r in blobs:
            cx, cy, rr = x + dx * h, yb + dy * h, r * h
            cv.circle(cx, cy, rr, leaf_c,
                      shade=lambda px, py: scale(
                          leaf_c, clamp(1.15 - 0.55 * ((py - cy) / rr * 0.5 + 0.5), 0.55, 1.2)))
        if snowy:
            cv.circle(x, yb - h * 0.82, h * 0.15, snow_c, alpha=0.8)

    def palm(self, x, yb, h, leaf=None):
        cv, rng = self.cv, self.rng
        trunk = self.col((0.55, 0.38, 0.22))
        lean = rng.choice((-1, 1)) * 0.16 * h
        self.shadow(x, yb, h * 0.30)
        left, right, pts = [], [], []
        for k in range(13):
            t = k / 12.0
            cx, cy, hw = x + lean * t ** 1.6, yb - h * 0.82 * t, h * 0.028 * (1 - 0.35 * t)
            left.append((cx - hw, cy))
            right.append((cx + hw, cy))
            pts.append((cx, cy))
        cv.polygon(left + right[::-1], trunk, shade=lambda px, py: scale(trunk, 1.1 - 0.35 * ((py - (yb - h * 0.82)) / (h * 0.82))))
        for k in range(1, 12):
            cv.capsule(pts[k][0] - h * 0.024, pts[k][1], pts[k][0] + h * 0.024, pts[k][1] - 2, 0.9, scale(trunk, 0.7), 0.7)
        tx, ty = pts[-1]
        green = self.col(leaf or (0.20, 0.58, 0.28), explicit=leaf is not None)
        for dx, rise, k in ((-1, 0.25, 0.9), (-0.8, 0.55, 1.0), (-0.4, 0.8, 1.05), (0.4, 0.8, 0.95), (0.8, 0.55, 1.0), (1, 0.25, 0.9), (0.0, 1.0, 1.1)):
            ln = h * 0.5
            cl = []
            for j in range(11):
                s_ = j / 10.0
                cl.append((tx + dx * ln * s_, ty - rise * ln * s_ * (1 - s_ * 0.55) + ln * 0.55 * s_ * s_ * (abs(dx) + 0.35)))
            lft, rgt = [], []
            for j, (px, py) in enumerate(cl):
                nx, ny = (cl[min(j + 1, 10)][0] - cl[max(j - 1, 0)][0], cl[min(j + 1, 10)][1] - cl[max(j - 1, 0)][1])
                ln_ = math.hypot(nx, ny) or 1.0
                hw = h * 0.065 * math.sin(math.pi * (j + 0.5) / 11.0) ** 0.7
                lft.append((px - ny / ln_ * hw, py + nx / ln_ * hw))
                rgt.append((px + ny / ln_ * hw, py - nx / ln_ * hw))
            cv.polygon(lft + rgt[::-1], scale(green, k), shade=lambda px, py, g=green, kk=k: scale(g, kk * (1.1 - 0.4 * clamp((py - (ty - ln)) / ln))))
        for dx in (-0.025, 0.03):
            cv.circle(tx + dx * h, ty + h * 0.03, h * 0.028, self.col((0.40, 0.26, 0.15)))

    def house(self, x, yb, w, wall=None, roof=None):
        cv = self.cv
        hgt = w * 0.62
        wall_c = self.col(wall or (0.93, 0.85, 0.70), explicit=wall is not None)
        roof_c = self.col(roof or (0.66, 0.22, 0.18), explicit=roof is not None)
        self.shadow(x + w * 0.1, yb, w * 0.65)
        cv.box(x, yb - hgt / 2, w / 2, hgt / 2, wall_c,
               shade=lambda px, py: scale(wall_c, 1.04 - 0.14 * ((py - (yb - hgt)) / hgt)))
        cv.box(x + w * 0.28, yb - hgt - w * 0.17, w * 0.06, w * 0.15, scale(roof_c, 0.8))   # chimney
        peak = yb - hgt - w * 0.38
        cv.polygon([(x - w * 0.62, yb - hgt + 2), (x + w * 0.62, yb - hgt + 2), (x, peak)],
                   roof_c, shade=lambda px, py: scale(roof_c, 1.1 - 0.35 * ((py - peak) / (w * 0.4))))
        cv.box(x, yb - hgt * 0.3, w * 0.09, hgt * 0.3, self.col((0.40, 0.24, 0.14)))
        glass = (1.0, 0.85, 0.45) if self.night else self.col((0.62, 0.80, 0.95))
        for dx in (-0.3, 0.3):
            wx, wy = x + dx * w, yb - hgt * 0.58
            cv.box(wx, wy, w * 0.075, w * 0.075, glass)
            if self.night:
                cv.glow(wx, wy, w * 0.3, (1.0, 0.75, 0.3), 0.35)
            cv.box(wx, wy, w * 0.075, w * 0.008, scale(wall_c, 0.7))

    def flower(self, x, yb, size, color):
        cv = self.cv
        stem = self.col((0.18, 0.5, 0.2))
        cv.capsule(x, yb, x + size * 0.05, yb - size, max(1.0, size * 0.04), stem)
        cv.ellipse(x + size * 0.18, yb - size * 0.4, size * 0.2, size * 0.07, stem, angle=-0.5)
        cx, cy = x + size * 0.05, yb - size
        petal = self.col(color, explicit=True)
        for k in range(6):
            a = k * math.pi / 3
            cv.circle(cx + math.cos(a) * size * 0.2, cy + math.sin(a) * size * 0.2, size * 0.16, petal)
        cv.circle(cx, cy, size * 0.12, self.col((1.0, 0.8, 0.15)))

    def bird(self, x, y, size, color=(0.1, 0.1, 0.12)):
        pts = [(x - size, y - size * 0.1), (x - size * 0.5, y - size * 0.4), (x, y),
               (x + size * 0.5, y - size * 0.4), (x + size, y - size * 0.1)]
        r = max(0.9, size * 0.07)
        for a, b in zip(pts, pts[1:]):
            self.cv.capsule(a[0], a[1], b[0], b[1], r, color)

    def boat(self, x, yb, size, hull=None, sail=None):
        cv = self.cv
        hull_c = self.col(hull or (0.45, 0.25, 0.14), explicit=hull is not None)
        sail_c = self.col(sail or (0.97, 0.97, 0.95), explicit=sail is not None)
        cv.ellipse(x, yb + size * 0.1, size * 0.7, size * 0.05, WHITE, alpha=0.25, soft=2.0)
        cv.capsule(x, yb - size * 0.1, x, yb - size * 1.15, max(1.2, size * 0.025), scale(hull_c, 0.7))
        cv.polygon([(x + size * 0.04, yb - size * 1.1), (x + size * 0.55, yb - size * 0.18),
                    (x + size * 0.04, yb - size * 0.18)], sail_c)
        cv.polygon([(x - size * 0.04, yb - size * 0.95), (x - size * 0.4, yb - size * 0.18),
                    (x - size * 0.04, yb - size * 0.18)], scale(sail_c, 0.88))
        cv.polygon([(x - size * 0.6, yb - size * 0.14), (x + size * 0.65, yb - size * 0.14),
                    (x + size * 0.45, yb + size * 0.06), (x - size * 0.45, yb + size * 0.06)], hull_c)

    def road(self, color=(0.17, 0.17, 0.2)):
        cv, hz, w, h = self.cv, self.horizon, self.w, self.h
        asphalt = self.col(color)
        pts = [(w * 0.5 - 3, hz), (w * 0.5 + 3, hz), (w * 0.93, h), (w * 0.07, h)]
        cv.polygon(pts, asphalt, shade=lambda px, py: scale(asphalt, 0.8 + 0.4 * (py - hz) / (h - hz)))
        stripe = self.col((0.95, 0.9, 0.5))
        for k in range(9):
            t0, t1 = (k / 9.0) ** 2, ((k + 0.5) / 9.0) ** 2
            y0, y1 = hz + t0 * (h - hz), hz + t1 * (h - hz)
            w0, w1 = 0.4 + 7.2 * t0, 0.4 + 7.2 * t1
            cv.polygon([(w * 0.5 - w0, y0), (w * 0.5 + w0, y0), (w * 0.5 + w1, y1), (w * 0.5 - w1, y1)], stripe)

    def skyline(self, base, layers, neon=False, window_prob=0.4):
        cv, rng, w, h = self.cv, self.rng, self.w, self.h
        neon_cols = [(1.0, 0.2, 0.7), (0.1, 0.9, 1.0), (0.6, 0.3, 1.0), (1.0, 0.9, 0.2)]
        for layer in range(layers):
            depth = layer / max(1, layers - 1)               # 0 far .. 1 near
            fade = 0.35 + 0.65 * depth
            body = mix(self.horizon_color(), (0.03, 0.03, 0.07) if neon else (0.12, 0.13, 0.2), fade)
            x = -rng.uniform(0, 30)
            while x < w:
                bw = rng.uniform(0.045, 0.11) * self.s * (0.7 + 0.5 * depth)
                bh = rng.uniform(0.12, 0.42) * h * (0.6 + 0.5 * (1 - depth)) * 0.8
                x0, x1, y0 = x, x + bw, base - bh
                cv.fill_rect(x0, y0, x1, base + 2, body)
                if neon:
                    edge = neon_cols[rng.randrange(len(neon_cols))]
                    cv.fill_rect(x0, y0, x1, y0 + 1.5, edge, 0.9)
                    cv.fill_rect(x0, y0, x0 + 1, base, edge, 0.35)
                    if depth > 0.5 and rng.random() < 0.3:
                        cv.glow((x0 + x1) / 2, y0 + bh * 0.3, bw * 1.4, edge, 0.25)
                if rng.random() < 0.3:
                    cv.fill_rect((x0 + x1) / 2 - 1, y0 - bh * 0.18, (x0 + x1) / 2 + 1, y0, body)
                step = max(4, int(self.s * 0.018))
                wsize = max(1, step // 2)
                for wy in range(int(y0) + step, int(base) - step, step):
                    for wx in range(int(x0) + step // 2, int(x1) - wsize, step):
                        if rng.random() < window_prob:
                            if neon:
                                wc = neon_cols[rng.randrange(len(neon_cols))]
                            else:
                                wc = (1.0, 0.85, 0.5) if self.night else self.col((0.75, 0.85, 0.95))
                            cv.fill_rect(wx, wy, wx + wsize, wy + wsize, wc, 0.5 + 0.5 * depth)
                x = x1 + rng.uniform(0, 6)

    def neon_grid(self, color):
        cv, hz, w, h = self.cv, self.horizon, self.w, self.h
        floor = mix((0.03, 0.0, 0.08), color, 0.08)
        cv.gradient_v([(0, mix(floor, color, 0.3)), (0.12, floor), (1, (0.02, 0.0, 0.05))], hz, h)
        for k in range(-12, 13):
            cv.capsule(w * 0.5 + k * 3, hz, w * 0.5 + k * w * 0.16, h, 0.7, color, 0.7)
        for k in range(1, 12):
            y = hz + ((k / 12.0) ** 2.2) * (h - hz)
            cv.fill_rect(0, y, w, y + 1.4, color, 0.65)
        cv.glow(w * 0.5, hz, w * 0.6, color, 0.22, 2.0)

    def precipitation(self, kind, n):
        cv, rng = self.cv, self.rng
        for _ in range(n):
            x, y = rng.uniform(0, self.w), rng.uniform(0, self.h)
            if kind == "snow":
                cv.circle(x, y, rng.uniform(1.0, 2.6), WHITE, alpha=0.85)
            else:
                ln = rng.uniform(0.02, 0.05) * self.h
                cv.capsule(x, y, x - ln * 0.3, y + ln, 0.6, (0.75, 0.8, 0.9), 0.45)

    def haze(self, color, y0, y1, amount):
        mid, half = (y0 + y1) / 2.0, (y1 - y0) / 2.0
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            self.cv.fill_rect(0, y, self.w, y + 1, color, amount * clamp(1 - abs(y - mid) / half))
