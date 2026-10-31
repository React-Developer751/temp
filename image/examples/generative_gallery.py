#!/usr/bin/env python3
"""Contact sheet of the generative maths pictures (fractals, L-systems, flow fields, textures, colour rules).

    python3 examples/generative_gallery.py generative_gallery.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import encode_png, render  # noqa: E402
from pixelmath.raster import Canvas  # noqa: E402
from pixelmath.text import draw_text  # noqa: E402

PROMPTS = ["mandelbrot", "julia fractal", "mandelbrot complementary", "fractal tree", "fern", "snowflake",
           "dragon curve", "sierpinski", "flow field", "flow field triadic", "marble", "plasma analogous"]
CELL, PAD, LABEL, COLS = 240, 8, 22, 4


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "generative_gallery.png"
    rows = (len(PROMPTS) + COLS - 1) // COLS
    w, h = COLS * CELL + (COLS + 1) * PAD, rows * (CELL + LABEL + PAD) + PAD
    sheet = Canvas(w, h, (0.95, 0.95, 0.95))
    for k, prompt in enumerate(PROMPTS):
        x0, y0 = PAD + (k % COLS) * (CELL + PAD), PAD + (k // COLS) * (CELL + LABEL + PAD)
        cv, _, mode = render(prompt, CELL, CELL, 3)
        for y in range(CELL):
            i, j = y * CELL * 3, ((y0 + LABEL + y) * w + x0) * 3
            sheet.px[j:j + CELL * 3] = cv.px[i:i + CELL * 3]
        draw_text(sheet, prompt.upper(), x0 + CELL / 2, y0 + LABEL / 2, 11, (0.1, 0.1, 0.2), 0.12, max_width=CELL)
    with open(out, "wb") as fh:
        fh.write(encode_png(w, h, sheet.to_rgb_bytes()))
    print("wrote", out)


if __name__ == "__main__":
    main()
