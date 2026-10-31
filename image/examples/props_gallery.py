#!/usr/bin/env python3
"""Render every business prop into one contact sheet.

    python3 examples/props_gallery.py gallery.png                # all props
    python3 examples/props_gallery.py food.png --category food   # one category
    python3 examples/props_gallery.py x.png --names pizza,laptop --color red --dark
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import encode_png  # noqa: E402
from pixelmath.neural import Style  # noqa: E402
from pixelmath.painter import Painter  # noqa: E402
from pixelmath.props import REGISTRY, draw_prop  # noqa: E402
from pixelmath.raster import Noise  # noqa: E402
from pixelmath.tokenizer import COLORS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("--names")
    ap.add_argument("--category")
    ap.add_argument("--cell", type=int, default=200)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--color", help="recolour every prop, e.g. red")
    ap.add_argument("--dark", action="store_true")
    args = ap.parse_args()
    names = args.names.split(",") if args.names else sorted(
        n for n, p in REGISTRY.items() if not args.category or p.category == args.category)
    cell, cols = args.cell, args.cols
    rows = -(-len(names) // cols)
    W, H = cols * cell, rows * cell
    style = Style(0, 1, 1, 0.01, 0.5, 1, 0.5, 0)
    p = Painter(W, H, random.Random(1), Noise(1), style)
    bg = (0.13, 0.14, 0.18) if args.dark else (0.92, 0.93, 0.95)
    p.cv.gradient_v([(0, bg), (1, tuple(v * 0.93 for v in bg))])
    color = COLORS[args.color] if args.color else None
    for i, name in enumerate(names):
        r, cc = divmod(i, cols)
        pr = REGISTRY[name]
        s = min(cell * 0.62 / max(1.0, pr.aspect * 0.75), cell * 0.75) / max(0.3, pr.fill) * (0.8 if pr.fill < 0.8 else 1.0)
        draw_prop(p, name, cc * cell + cell / 2, r * cell + cell * 0.80, s, color)
    open(args.output, "wb").write(encode_png(W, H, p.cv.to_rgb_bytes()))
    print("wrote %s: %s" % (args.output, ", ".join(names)))


if __name__ == "__main__":
    main()
