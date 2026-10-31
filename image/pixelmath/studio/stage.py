"""The Stage: a camera, layers, lighting and a post-process for premium-looking niche scenes.

A niche scene is a function ``scene(S)`` that draws on a *stage*: u runs left to right over 0..2.0, v runs top to bottom over
0..1.0 (one stage unit of height is the full picture height at zoom 1). The scene never thinks about pixels, aspect ratio or
the text zone. The studio calls it twice with the same random seed:

  1. a dry run (nothing is drawn) that records where the subjects are, then it chooses a camera: zoom, pan and mirroring,
     so the subject sits where the text zone is not (hero), fills a square (about), or is cropped differently (gallery tiles);
  2. the real run, which draws with that camera and then finishes the picture (mood grading, light, vignette, grain).

Order inside a scene: ``with S.far():`` (backdrop, drawn small and blurred = depth of field), then the middle layer (call
the drawing methods directly: sharp subjects and furniture), then ``with S.near():`` (soft foreground blobs). Use ``S.pal``
for colours, ``S.put(prop, u, v, h, subject=True)`` for props (a soft contact shadow is added), and ``S.rng`` for all randomness.
"""
import math
from contextlib import contextmanager
from dataclasses import dataclass, field

from ..neural import Style
from ..painter import Painter
from ..props.core import REGISTRY, Ctx
from ..raster import Canvas, Noise, clamp, mix, scale
from .palette import WHITE

NO_TEXT = True                # the client's rule: no text, letters, numbers or logos in any picture. Signs and screens stay as plain shapes.
ASPECT = 2.0                 # stage width / stage height
FAR_SCALE = 0.25             # the far layer is drawn at a quarter of the resolution and enlarged: free depth of field
STUDIO_PROPS = {}            # props made for the studio (kept apart from the older clip-art registry)
NEUTRAL = Style(hue_shift=0.0, sat=1.0, bright=1.0, grain=0.0, light_x=0.5, texture=1.0, jitter=0.5, warmth=0.0)


@dataclass
class StudioProp:
    name: str
    fn: object
    aspect: float
    fill: float = 1.0


def sprop(name, aspect=1.0, fill=1.0):
    """Register a studio prop: ``fn(c, color)`` drawing in unit space exactly like the older props (see props/core.py Ctx)."""
    def deco(fn):
        STUDIO_PROPS[name] = StudioProp(name, fn, aspect, fill)
        return fn
    return deco


def find_prop(name):
    if name in STUDIO_PROPS:
        return STUDIO_PROPS[name]
    p = REGISTRY[name]
    return StudioProp(name, p.fn, p.aspect, p.fill)


@dataclass
class Camera:
    cx: float = ASPECT / 2
    cy: float = 0.5
    zoom: float = 1.0
    flip: bool = False


class _Layer:
    def __init__(self, w, h, k, rng, noise, light):
        self.k = k
        self.painter = Painter(max(2, int(w * k)), max(2, int(h * k)), rng, noise, NEUTRAL, light)
        self.cv = self.painter.cv
        self.used = False


class Stage:
    def __init__(self, width, height, pal, seed, cam=None, dry=False, light_u=-0.6, variant=0):
        import random
        self.W, self.H = width, height
        self.pal = pal
        self.seed = seed
        self.rng = random.Random(seed * 7919 + 13)
        self.noise = Noise(seed * 31 + 5)
        self.cam = cam or Camera()
        self.dry = dry
        self.light_u = light_u            # -1 key light from the left ... +1 from the right
        self.variant = variant
        self.subjects = []                # [(name, u0, v0, u1, v1)] required subjects (the judge checks these)
        self.cluster = []                 # boxes of every framed prop: the camera keeps all of them in the picture
        self.focus_points = {}
        self.drawn = []
        self._light = tuple(pal.light)
        self.main = _Layer(width, height, 1.0, self.rng, self.noise, self._light)
        self._far = None
        self._layer = self.main
        self._far_done = False
        self._soft = 0.0
        self._sc = height * self.cam.zoom

    # ------------------------------------------------------------------ coordinates
    def px(self, u, v):
        k = self._layer.k
        sgn = -1.0 if self.cam.flip else 1.0
        return ((self.W / 2 + (u - self.cam.cx) * self._sc * sgn) * k, (self.H / 2 + (v - self.cam.cy) * self._sc) * k)

    def length(self, d):
        return d * self._sc * self._layer.k

    def visible_u(self):
        """Stage u-range currently in the picture (useful to stretch backgrounds)."""
        half = self.W / 2 / self._sc
        return self.cam.cx - half, self.cam.cx + half

    def visible_v(self):
        half = self.H / 2 / self._sc
        return self.cam.cy - half, self.cam.cy + half

    @property
    def cv(self):
        return self._layer.cv

    @property
    def painter(self):
        return self._layer.painter

    # ------------------------------------------------------------------ layers
    @contextmanager
    def far(self):
        """Backdrop layer: drawn at low resolution and enlarged, so it is soft like an out-of-focus background."""
        if self._far_done:
            raise RuntimeError("draw the far layer before anything else")
        if self._far is None and not self.dry:
            self._far = _Layer(self.W, self.H, FAR_SCALE, self.rng, self.noise, self._light)
        prev = self._layer
        if not self.dry:
            self._layer = self._far
            self._far.used = True
        try:
            yield self
        finally:
            self._layer = prev

    @contextmanager
    def near(self, blur=14.0):
        """Foreground layer: everything drawn inside has soft, blurred edges (depth of field in front of the subject)."""
        self._ensure_mid()
        old, old_solid = self._soft, self.main.cv.solid_soft
        self._soft = blur * self._sc / 400.0
        self.main.cv.solid_soft = True                       # blurred foreground shapes stay solid inside (Canvas.shape's default soft path is translucent)
        try:
            yield self
        finally:
            self._soft = old
            self.main.cv.solid_soft = old_solid

    def _ensure_mid(self):
        if self._far_done:
            return
        self._far_done = True
        if self.dry or self._far is None or not self._far.used:
            return
        _box_blur(self._far.cv, 1)
        _enlarge(self._far.cv, self.main.cv)

    # ------------------------------------------------------------------ primitives (stage units)
    def _soft_value(self, soft):
        return max(1.0, soft + self._soft)

    def fill(self, color):
        if self.dry:
            return
        cv = self.cv
        cv.px[:] = list(color) * (cv.w * cv.h)

    def wall(self, top, bottom, horizon=0.65):
        """Vertical gradient from the top of the picture down to stage v = horizon (everything above is wall)."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        k = self._layer.k
        y_top, y_h = self.px(0, 0)[1], self.px(0, horizon)[1]
        cv = self.cv
        cv.fill_rect(0, 0, cv.w, max(0, min(cv.h, y_top)), top)
        cv.gradient_v([(0, top), (1, bottom)], y_top, y_h)

    def floor(self, v0, top, bottom):
        """Gradient from stage v = v0 to the bottom of the picture."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        y0 = self.px(0, v0)[1]
        y1 = self.px(0, 2.0)[1]
        cv = self.cv
        cv.gradient_v([(0, top), (1, bottom)], y0, y1)

    def rect(self, u, v, w, h, color, r=0.0, alpha=1.0, lift=0.06, soft=1.0):
        """Centre (u, v), size w x h, optional corner radius r."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        x, y = self.px(u, v)
        hw, hh = self.length(w) / 2, self.length(h) / 2
        if r == 0.0 and lift == 0.0 and self._soft == 0.0:
            self.cv.fill_rect(x - hw, y - hh, x + hw, y + hh, color, alpha)           # axis-aligned and flat: fast path
            return
        shade = None
        if lift:
            top, bot = scale(color, 1 + lift), scale(color, 1 - lift * 1.2)
            y0, span = y - hh, max(1.0, 2 * hh)
            shade = lambda px_, py_: mix(top, bot, clamp((py_ - y0) / span))      # noqa: E731
        self.cv.box(x, y, hw, hh, color, rad=min(self.length(r), hw, hh), alpha=alpha, shade=shade, soft=self._soft_value(soft))

    def gradient_rect(self, u0, v0, u1, v1, top, bottom, alpha=1.0, r=0.0):
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        x0, y0 = self.px(u0, v0)
        x1, y1 = self.px(u1, v1)
        x0, x1 = min(x0, x1), max(x0, x1)
        span = max(1.0, y1 - y0)
        self.cv.box((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, span / 2, top, rad=min(self.length(r), (x1 - x0) / 2, span / 2),
                    alpha=alpha, shade=lambda px_, py_: mix(top, bottom, clamp((py_ - y0) / span)), soft=self._soft_value(1.0))

    def ellipse(self, u, v, a, b, color, angle=0.0, alpha=1.0, lift=0.06, soft=1.0):
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        x, y = self.px(u, v)
        ra, rb = self.length(a), self.length(b)
        ext = max(ra, rb)
        shade = None
        if lift:
            top, bot = scale(color, 1 + lift), scale(color, 1 - lift * 1.2)
            shade = lambda px_, py_: mix(top, bot, clamp((py_ - (y - ext)) / max(1.0, 2 * ext)))      # noqa: E731
        self.cv.ellipse(x, y, ra, rb, color, angle=-math.radians(angle) * (-1 if self.cam.flip else 1), alpha=alpha, shade=shade,
                        soft=self._soft_value(soft))

    def circle(self, u, v, r, color, alpha=1.0, lift=0.06, soft=1.0):
        self.ellipse(u, v, r, r, color, 0.0, alpha, lift, soft)

    def poly(self, pts, color, alpha=1.0, soft=1.0):
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        self.cv.polygon([self.px(u, v) for u, v in pts], color, alpha=alpha, soft=self._soft_value(soft))

    def line(self, u0, v0, u1, v1, w, color, alpha=1.0):
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        (x0, y0), (x1, y1) = self.px(u0, v0), self.px(u1, v1)
        self.cv.capsule(x0, y0, x1, y1, max(0.5, self.length(w) / 2), color, alpha)

    def glow(self, u, v, r, color, strength=0.5, power=2.0):
        """Additive light: lamps, windows, highlights."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        x, y = self.px(u, v)
        self.cv.glow(x, y, self.length(r), color, strength, power)

    def light_shaft(self, u0, v0, u1, v1, u2, v2, u3, v3, color=None, alpha=0.14):
        """A translucent beam (window light on the floor): a quad with soft edges."""
        self.poly([(u0, v0), (u1, v1), (u2, v2), (u3, v3)], color or self.pal.light, alpha, soft=self._shaft_soft())

    def _shaft_soft(self):
        return max(3.0, self.length(0.03))

    def soft(self, u, v, a, b, color, alpha=0.4, power=1.7, angle=0.0, add=False):
        """Radial-falloff blob (shadows, light pools, bloom) with half-axes a, b in stage units."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        from .craft import soft_disc
        x, y = self.px(u, v)
        soft_disc(_Pix(self.cv, x, y, self.length(1.0)), 0.0, 0.0, a, b, color, alpha, power, angle, add)

    def shadow(self, u, v, w, h=None, alpha=0.3):
        """Soft contact shadow under something standing at (u, v), pushed away from the key light."""
        h = w * 0.20 if h is None else h
        self.soft(u - self.light_u * w * 0.10, v, w * 0.58, h * 0.9, (0.0, 0.0, 0.0), alpha, 1.5)
        self.soft(u - self.light_u * w * 0.04, v - h * 0.05, w * 0.42, h * 0.45, (0.0, 0.0, 0.0), alpha * 0.9, 1.8)

    def bokeh(self, n, u0, v0, u1, v1, colors, rmin=0.012, rmax=0.045, alpha=0.35):
        """Out-of-focus light discs (lamps, street lights, fairy lights)."""
        if self.dry:
            return
        for _ in range(n):
            u, v = self.rng.uniform(u0, u1), self.rng.uniform(v0, v1)
            c = colors[self.rng.randrange(len(colors))]
            self.circle(u, v, self.rng.uniform(rmin, rmax), c, alpha=alpha * self.rng.uniform(0.5, 1.0), lift=0, soft=4.0)

    def text(self, txt, u, v, h, color, weight=0.14):
        if self.dry or NO_TEXT:
            return
        from ..text import draw_text
        x, y = self.px(u, v)
        draw_text(self.cv, txt, x, y, self.length(h), color, weight, "center", None)

    # ------------------------------------------------------------------ textures and set pieces
    def wood(self, u0, v0, u1, v1, base, plank=0.07, vertical=False, grain=0.5):
        """Wooden planks (table top, floor, board) with seams, tone variation and grain lines."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        rng = self.rng
        n = max(1, int(round(((u1 - u0) if vertical else (v1 - v0)) / plank)))
        for i in range(n):
            tone = 1.0 + rng.uniform(-0.07, 0.07)
            c = scale(base, tone)
            if vertical:
                a, b = u0 + (u1 - u0) * i / n, u0 + (u1 - u0) * (i + 1) / n
                self.rect((a + b) / 2, (v0 + v1) / 2, b - a, v1 - v0, c, lift=0.0)
                self.line(b, v0, b, v1, 0.003, scale(base, 0.62), 0.55)
            else:
                a, b = v0 + (v1 - v0) * i / n, v0 + (v1 - v0) * (i + 1) / n
                self.rect((u0 + u1) / 2, (a + b) / 2, u1 - u0, b - a, c, lift=0.0)
                self.line(u0, b, u1, b, 0.003, scale(base, 0.62), 0.55)
            for _ in range(int(4 * grain * (1 + (u1 - u0 if not vertical else v1 - v0)))):
                if vertical:
                    uu = rng.uniform(a, b)
                    y0 = rng.uniform(v0, v1)
                    self.line(uu, y0, uu + rng.uniform(-0.004, 0.004), min(v1, y0 + rng.uniform(0.05, 0.2)), 0.0016, scale(base, rng.uniform(0.7, 0.88)), 0.28)
                else:
                    vv = rng.uniform(a, b)
                    x0 = rng.uniform(u0, u1)
                    self.line(x0, vv, min(u1, x0 + rng.uniform(0.08, 0.35)), vv + rng.uniform(-0.004, 0.004), 0.0016,
                              scale(base, rng.uniform(0.7, 0.88)), 0.28)

    def tiles(self, u0, v0, u1, v1, c1, c2, size=0.08):
        """Checker / tile floor."""
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        nu, nv = max(1, int(round((u1 - u0) / size))), max(1, int(round((v1 - v0) / size)))
        for i in range(nu):
            for j in range(nv):
                self.rect(u0 + (i + 0.5) * (u1 - u0) / nu, v0 + (j + 0.5) * (v1 - v0) / nv, (u1 - u0) / nu + 0.002, (v1 - v0) / nv + 0.002,
                          c1 if (i + j) % 2 == 0 else c2, lift=0.0, soft=0.5)

    def window(self, u, v, w, h, sky_top=(0.55, 0.78, 0.96), sky_bot=(0.88, 0.95, 1.0), frame=(0.97, 0.97, 0.98), bars=True):
        """A window with sky, mullions and a soft light bloom."""
        self.glow(u, v, max(w, h) * 1.1, self.pal.light, 0.22)
        self.gradient_rect(u - w / 2, v - h / 2, u + w / 2, v + h / 2, sky_top, sky_bot, r=0.006)
        if bars:
            self.rect(u, v, 0.008, h, frame, lift=0.0)
            self.rect(u, v - h * 0.05, w, 0.008, frame, lift=0.0)
        self.rect(u, v + h / 2 + 0.006, w + 0.03, 0.014, frame, r=0.004, lift=0.04)

    def pendant(self, u, v_top, v_lamp, color=(1.0, 0.82, 0.5), shade_w=0.09):
        """Hanging lamp with a warm glow."""
        self.line(u, v_top, u, v_lamp - 0.04, 0.003, (0.25, 0.22, 0.2))
        self.poly([(u - shade_w / 2, v_lamp), (u + shade_w / 2, v_lamp), (u + shade_w * 0.22, v_lamp - 0.05), (u - shade_w * 0.22, v_lamp - 0.05)],
                  scale(color, 0.78))
        self.glow(u, v_lamp + 0.02, shade_w * 3.4, color, 0.42)
        self.ellipse(u, v_lamp + 0.004, shade_w * 0.36, 0.012, mix(color, WHITE, 0.6), lift=0)

    # ------------------------------------------------------------------ props
    def put(self, name, u, v, h, color=None, subject=False, shadow=True, shadow_alpha=0.28, shadow_w=None, framed=True):
        """Draw a prop with its base centre at (u, v) and a visible height of h stage units (1.0 = picture height at zoom 1)."""
        pr = find_prop(name)
        wd = pr.aspect * h
        if subject:
            self.subjects.append((name, u - wd / 2, v - h, u + wd / 2, v))
        if framed or subject:
            self.cluster.append((name, u - wd / 2, v - h, u + wd / 2, v))
        self.drawn.append(name)
        if self.dry:
            return
        self._ensure_mid() if self._layer is self.main else None
        if shadow:
            self.shadow(u, v, (shadow_w or wd) * 0.95, alpha=shadow_alpha)
        x, y = self.px(u, v)
        s = self.length(h) / max(0.3, pr.fill)
        c = Ctx(self._layer.painter, x, y, s)
        c.no_text = NO_TEXT
        pr.fn(c, color)

    def mark_subject(self, name, u0, v0, u1, v1):
        """Declare a subject you drew with primitives (so the judge can find it)."""
        self.subjects.append((name, u0, v0, u1, v1))
        self.cluster.append((name, u0, v0, u1, v1))
        self.drawn.append(name)

    def focus(self, name, u, v):
        """A point of interest for close-up / detail tiles."""
        self.focus_points[name] = (u, v)

    # ------------------------------------------------------------------ finish
    def finish(self, grain=0.016, vignette=0.28):
        self._ensure_mid()
        if self.dry:
            return None
        cv = self.main.cv
        _grade(cv, self.pal.gain, self.pal.contrast, vignette, grain, self.rng)
        return cv


class _Pix:
    """Minimal Ctx stand-in so craft helpers can draw at a pixel position on a canvas."""
    def __init__(self, cv, x, y, s):
        self.cv, self.x, self.y, self.s = cv, x, y, s

    def X(self, u):
        return self.x + u * self.s

    def Y(self, v):
        return self.y - v * self.s


# ---------------------------------------------------------------------------------------------- image helpers
def _box_blur(cv, r):
    """Separable box blur of radius r (pixels) with edge clamping."""
    w, h, px = cv.w, cv.h, cv.px
    n = 2 * r + 1
    for y in range(h):                                             # horizontal
        base = y * w * 3
        for c in range(3):
            row = px[base + c:base + w * 3:3]
            out = []
            pad = [row[0]] * r + row + [row[-1]] * r
            acc = sum(pad[:n])
            out.append(acc / n)
            for x in range(1, w):
                acc += pad[x + n - 1] - pad[x - 1]
                out.append(acc / n)
            px[base + c:base + w * 3:3] = out
    for x in range(w):                                             # vertical
        for c in range(3):
            col = px[x * 3 + c::w * 3]
            pad = [col[0]] * r + col + [col[-1]] * r
            acc = sum(pad[:n])
            out = [acc / n]
            for y in range(1, h):
                acc += pad[y + n - 1] - pad[y - 1]
                out.append(acc / n)
            px[x * 3 + c::w * 3] = out


def _enlarge(src, dst):
    """Bilinear enlargement of canvas `src` over the whole of canvas `dst`."""
    sw, sh, dw, dh = src.w, src.h, dst.w, dst.h
    sp, dp = src.px, dst.px
    xs = []
    for x in range(dw):
        fx = min(max((x + 0.5) * sw / dw - 0.5, 0.0), sw - 1.0001)
        x0 = int(fx)
        xs.append((x0 * 3, min(sw - 1, x0 + 1) * 3, fx - x0))
    for y in range(dh):
        fy = min(max((y + 0.5) * sh / dh - 0.5, 0.0), sh - 1.0001)
        y0 = int(fy)
        t = fy - y0
        r0, r1 = y0 * sw * 3, min(sh - 1, y0 + 1) * sw * 3
        row0, row1 = sp[r0:r0 + sw * 3], sp[r1:r1 + sw * 3]
        mixed = [a + (b - a) * t for a, b in zip(row0, row1)]
        out = []
        for a, b, f in xs:
            out += (mixed[a] + (mixed[b] - mixed[a]) * f, mixed[a + 1] + (mixed[b + 1] - mixed[a + 1]) * f,
                    mixed[a + 2] + (mixed[b + 2] - mixed[a + 2]) * f)
        dp[y * dw * 3:(y + 1) * dw * 3] = out


def _grade(cv, gain, contrast, vignette, grain, rng):
    """Mood tint, a gentle S-curve, a vignette and film grain, in one pass over the picture."""
    w, h, px = cv.w, cv.h, cv.px
    lut = []
    for i in range(1025):
        t = i / 1024.0
        lut.append(t + contrast * (t - 0.5) * (1 - abs(2 * t - 1)) * 2.0 * 0.5)
    fx = []
    for x in range(w):
        dx = (x - w / 2.0) / (w / 2.0)
        fx.append(1.0 - vignette * 0.5 * dx * dx)
    fx3 = []
    for x in range(w):
        fx3 += [fx[x] * gain[0], fx[x] * gain[1], fx[x] * gain[2]]
    tile = [(rng.random() - 0.5) * grain * 2 for _ in range(4096)]
    row_len = w * 3
    for y in range(h):
        dy = (y - h / 2.0) / (h / 2.0)
        fy = 1.0 - vignette * 0.5 * dy * dy
        off = (y * 797) % 3000
        noise = (tile[off:] + tile[:off])[:row_len] if row_len <= 4096 else (tile * (row_len // 4096 + 1))[off:off + row_len]
        base = y * row_len
        row = px[base:base + row_len]
        out = []
        for v, f, nz in zip(row, fx3, noise):
            v = v * f * fy + nz
            out.append(lut[1024 if v >= 1.0 else 0 if v <= 0.0 else int(v * 1024)])
        px[base:base + row_len] = out
