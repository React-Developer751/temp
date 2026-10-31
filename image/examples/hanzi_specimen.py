"""Render a specimen sheet of every character in pixelmath/hanzi.py (usage: python examples/hanzi_specimen.py out.png)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pixelmath import encode_png, hanzi, raster, text  # noqa: E402


def main(out="hanzi_specimen.png"):
    chars = "".join(hanzi.GLYPHS)
    rows = [(64, 20), (32, 40)]
    width = 1500
    cv = raster.Canvas(width, 20 + sum(((len(chars) + n - 1) // n) * int(h * 1.4) for h, n in rows), (0.96, 0.95, 0.92))
    y = 20
    for h, n in rows:
        for i in range(0, len(chars), n):
            text.draw_text(cv, chars[i:i + n], width / 2, y + h / 2, h, (0.1, 0.1, 0.2), 0.14)
            y += int(h * 1.4)
    data = bytes(int(max(0.0, min(1.0, v)) * 255 + 0.5) for v in cv.px)
    with open(out, "wb") as f:
        f.write(encode_png(cv.w, cv.h, data))


if __name__ == "__main__":
    main(*sys.argv[1:2])
