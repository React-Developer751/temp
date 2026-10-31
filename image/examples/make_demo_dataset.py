#!/usr/bin/env python3
"""Create a tiny demo training set so you can try train.py end to end.

    python3 examples/make_demo_dataset.py demo_data
    python3 train.py demo_data --model demo_model.json
    python3 -m pixelmath "aqua mossy" --model demo_model.json -o demo.png

The images are synthetic: the top half has one colour word (aqua, coral, ...), the bottom half
another (mossy, sandy, ...). None of these words exist in the built-in lexicon, so the model has
to learn them from the images. Two combinations are held back so you can check that it
composes words it never saw together.
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import encode_png  # noqa: E402

TOP = {"aqua": (0, 200, 200), "coral": (250, 110, 90), "olive": (110, 120, 30),
       "plum": (140, 60, 140), "amber": (250, 180, 20), "mint": (140, 230, 170)}
BOTTOM = {"mossy": (60, 110, 50), "sandy": (220, 190, 130), "muddy": (100, 70, 40), "icy": (210, 235, 250)}
HELD_OUT = {("aqua", "mossy"), ("coral", "icy")}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_data"
    os.makedirs(out, exist_ok=True)
    rng = random.Random(1)
    rows = []
    for top, tc in TOP.items():
        for bottom, bc in BOTTOM.items():
            if (top, bottom) in HELD_OUT:
                continue
            for v in range(3):
                n, px = 32, bytearray()
                for y in range(n):
                    base = tc if y < n // 2 else bc
                    for _ in range(n):
                        px += bytes(max(0, min(255, int(c + rng.gauss(0, 12)))) for c in base)
                name = "%s_%s_%d.png" % (top, bottom, v)
                with open(os.path.join(out, name), "wb") as fh:
                    fh.write(encode_png(n, n, bytes(px)))
                rows.append((name, "%s %s" % (top, bottom)))
    with open(os.path.join(out, "captions.csv"), "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["file", "caption"])
        writer.writerows(rows)
    print("wrote %d images + captions.csv in %s" % (len(rows), out))
    print("held-out pairs to try after training:", ", ".join("%s %s" % p for p in sorted(HELD_OUT)))


if __name__ == "__main__":
    main()
