#!/usr/bin/env python3
"""Render a Hindi (Devanagari) specimen sheet with the built-in stroke font.

    python3 examples/devanagari_specimen.py specimen.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import encode_png  # noqa: E402
from pixelmath.raster import Canvas  # noqa: E402
from pixelmath.text import draw_text  # noqa: E402

WORDS = ["नमस्ते", "स्वागत है", "चाय की दुकान", "मिठाई", "खाना", "होटल", "अस्पताल", "छूट", "ऑफर", "कृपया",
         "विद्यालय", "दूध", "बाज़ार", "ज्ञान", "क्षमा", "प्रेम", "श्री", "राष्ट्र", "धन्यवाद", "कर्म", "सूर्य",
         "पुस्तकालय", "भारत", "महिला", "बच्चे", "सेवा", "दवाइयाँ", "ज़िंदगी", "९९९"]
SMALL = "नमस्ते स्वागत है चाय की दुकान मिठाई खाना होटल अस्पताल छूट ऑफर कृपया विद्यालय दूध बाज़ार"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "devanagari_specimen.png"
    cols, cw, rh, h = 3, 520, 130, 64
    rows = (len(WORDS) + cols - 1) // cols
    width, height = cols * cw + 40, rows * rh + 160
    cv = Canvas(width, height, (0.97, 0.96, 0.93))
    ink = (0.1, 0.1, 0.2)
    for i, word in enumerate(WORDS):
        cx = 20 + (i % cols) * cw + cw / 2
        cy = 40 + (i // cols) * rh + rh / 2
        draw_text(cv, word, cx, cy, h, ink, 0.16, max_width=cw - 40)
    draw_text(cv, SMALL, width / 2, height - 90, 30, ink, 0.12, max_width=width - 60)
    draw_text(cv, "० १ २ ३ ४ ५ ६ ७ ८ ९ । ॥", width / 2, height - 35, 30, ink, 0.12, max_width=width - 60)
    with open(out, "wb") as f:
        f.write(encode_png(width, height, cv.to_rgb_bytes()))
    print("wrote", out)


if __name__ == "__main__":
    main()
