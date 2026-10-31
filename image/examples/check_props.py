#!/usr/bin/env python3
"""Check and preview the props of one module while you are writing them.

    python3 examples/check_props.py animals gallery_animals.png

Runs the same checks as tests/test_props.py, but only for the props defined in pixelmath/props/<module>.py:
draws inside its declared box, deterministic, not tiny, words do not clash, colour parameter changes the picture.
Then renders a contact sheet of those props (open the PNG to judge the drawing).
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))

from pixelmath import encode_png, props, tokenizer as T   # noqa: E402
from pixelmath.neural import Style                         # noqa: E402
from pixelmath.painter import Painter                      # noqa: E402
from pixelmath.props import REGISTRY, draw_prop            # noqa: E402
from pixelmath.raster import Noise                         # noqa: E402

BG = (0.5, 0.5, 0.5)


def draw_alone(name, color=None, size=120, canvas=360, seed=1):
    p = Painter(canvas, canvas, random.Random(seed), Noise(seed), Style(0, 1, 1, 0.01, 0.5, 1, 0.5, 0))
    p.cv.px = list(BG) * (canvas * canvas)
    draw_prop(p, name, canvas / 2, canvas * 0.8, size, color)
    px, xs, ys = p.cv.px, [], []
    for y in range(canvas):
        for x in range(canvas):
            i = (y * canvas + x) * 3
            if abs(px[i] - BG[0]) + abs(px[i + 1] - BG[1]) + abs(px[i + 2] - BG[2]) > 0.22:
                xs.append(x)
                ys.append(y)
    return xs, ys, list(p.cv.px)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    module = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else module + "_gallery.png"
    mine = [n for n, pr in REGISTRY.items() if pr.fn.__module__.endswith("." + module)]
    if not mine:
        sys.exit("no props registered from pixelmath/props/%s.py" % module)
    bad = 0
    for name in sorted(mine):
        pr = REGISTRY[name]
        problems = []
        xs, ys, px = draw_alone(name)
        if len(xs) <= 200:
            problems.append("draws almost nothing (%d px)" % len(xs))
        else:
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if w > pr.aspect * 120 * 1.45 + 12:
                problems.append("wider than declared: %d px vs aspect*120=%d" % (w, pr.aspect * 120))
            if h > 120 * 1.45 + 12:
                problems.append("taller than declared: %d px" % h)
            if abs((max(xs) + min(xs)) / 2.0 - 180) >= 0.45 * 120 * max(1.0, pr.aspect):
                problems.append("not centred on its base")
            if max(ys) > 360 * 0.8 + 18:
                problems.append("hangs below its base line")
        if px != draw_alone(name)[2]:
            problems.append("not deterministic")
        if draw_alone(name, color=(0.9, 0.1, 0.1))[2] == px:
            problems.append("colour parameter changes nothing (ok only if the prop has no single main colour)")
        for w in pr.words:
            for table in ("COLORS", "SHAPES", "REGION_WORDS", "TIMES", "FLAGS", "SIZES", "POSITIONS", "COUNTS", "STOPWORDS"):
                if w in getattr(T, table):
                    problems.append("word %r clashes with the lexicon table %s" % (w, table))
        for w, a, b in props.DUPLICATES:
            if name in (a, b):
                problems.append("word %r is claimed by both %s and %s" % (w, a, b))
        print("%-14s %s" % (name, "ok" if not problems else "; ".join(problems)))
        bad += bool(problems)
    # contact sheet
    cell, cols = 230, 5
    rows = -(-len(mine) // cols)
    W, H = cols * cell, rows * cell
    p = Painter(W, H, random.Random(1), Noise(1), Style(0, 1, 1, 0.01, 0.5, 1, 0.5, 0))
    p.cv.gradient_v([(0, (0.92, 0.93, 0.95)), (1, (0.86, 0.87, 0.90))])
    for i, name in enumerate(sorted(mine)):
        r, c = divmod(i, cols)
        pr = REGISTRY[name]
        s = min(cell * 0.62 / max(1.0, pr.aspect * 0.75), cell * 0.75) / max(0.3, pr.fill) * (0.8 if pr.fill < 0.8 else 1.0)
        draw_prop(p, name, c * cell + cell / 2, r * cell + cell * 0.80, s, None)
    with open(out, "wb") as fh:
        fh.write(encode_png(W, H, p.cv.to_rgb_bytes()))
    print("gallery: %s (order: %s)" % (out, ", ".join(sorted(mine))))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
