#!/usr/bin/env python3
"""Contact sheet: the plain render next to what creative mode makes from the same prompt (and a few random mash-ups).

    python3 examples/creative_gallery.py creative_gallery.png [temperature]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import creative, encode_png, render  # noqa: E402
from pixelmath.raster import Canvas  # noqa: E402
from pixelmath.text import draw_text  # noqa: E402

PROMPTS = ["laptop and coffee cup", "tractor", "doctor and stethoscope", "pizza", "dog and ball", "cake"]
CELL, PAD, LABEL = 220, 8, 22


def paste(sheet, cv, x0, y0):
    for y in range(cv.h):
        for x in range(cv.w):
            i, j = (y * cv.w + x) * 3, ((y0 + y) * sheet.w + x0 + x) * 3
            sheet.px[j:j + 3] = cv.px[i:i + 3]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "creative_gallery.png"
    temp = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
    rows = len(PROMPTS) + 3
    w, h = 4 * CELL + 5 * PAD, rows * (CELL + LABEL + PAD) + PAD
    sheet = Canvas(w, h, (0.95, 0.95, 0.95))
    row = 0

    def label(text, col, y):
        draw_text(sheet, text.upper()[:34], PAD + col * (CELL + PAD) + CELL / 2, y + LABEL / 2, 11, (0.1, 0.1, 0.2), 0.12, max_width=CELL)

    for prompt in PROMPTS:
        y = PAD + row * (CELL + LABEL + PAD)
        plain, _, _ = render(prompt, CELL, CELL, 1)
        paste(sheet, plain, PAD, y + LABEL)
        label("plain: " + prompt, 0, y)
        for col, seed in enumerate((1, 2, 3), 1):
            made = creative.evolve(prompt, temp, 8, 3, seed, final_size=CELL)
            paste(sheet, made.canvas, PAD + col * (CELL + PAD), y + LABEL)
            label(made.prompt.replace(prompt, "~", 1), col, y)
        row += 1
    for k in range(3):
        y = PAD + row * (CELL + LABEL + PAD)
        for col in range(4):
            made, _ = creative.imagine(0.9, seed=10 * k + col, final_size=CELL)
            paste(sheet, made.canvas, PAD + col * (CELL + PAD), y + LABEL)
            label(made.prompt, col, y)
        row += 1
    with open(out, "wb") as fh:
        fh.write(encode_png(w, h, sheet.to_rgb_bytes()))
    print("wrote", out)


if __name__ == "__main__":
    main()
