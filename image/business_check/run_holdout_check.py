import json, os, sys
"""Holdout set: 28 prompts never used while developing the props. python3 business_check/run_holdout_check.py"""
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(P, "business_check")
sys.path.insert(0, P)
from pixelmath import render, encode_png
from pixelmath.tokenizer import parse

CATS = [
 ("Healthcare / food", ["dental clinic with friendly dentist", "italian pasta restaurant interior", "pharmacy medicine", "freshly baked croissants and coffee"]),
 ("Tech / education", ["online learning platform on laptop", "mobile app on smartphone", "digital marketing analytics report", "security shield insurance"]),
 ("Retail / events", ["luxury watch product shot", "ecommerce shopping cart", "birthday party cake and balloons", "flower shop bouquet"]),
 ("Fitness / wellness / legal", ["gym with dumbbells", "spa lotus candles relaxation", "law firm documents and lawyer", "customer reviews five stars"]),
 ("Travel / transport", ["school bus on the road", "travel agency airplane tickets", "car dealership red car", "bicycle shop"]),
 ("Property / outdoors", ["real estate villa with swimming pool", "mountain hiking adventure with tent", "wedding photography", "kids playground"]),
 ("Deliberately unsupported", ["pet shop with dogs", "farm tractor in wheat field", "plumber fixing pipes", "tailor shop sewing machine"]),
]
W, H = 512, 320
out = os.path.join(S, "holdout_images"); os.makedirs(out, exist_ok=True)
rows = []; tiles = []
for ci, (cat, prompts) in enumerate(CATS):
    for pi, p in enumerate(prompts):
        cv, parsed, mode = render(p, W, H)
        rgb = cv.to_rgb_bytes()
        n = ci * 4 + pi + 1
        open(os.path.join(out, "%02d.png" % n), "wb").write(encode_png(W, H, rgb))
        ents = ["%s%s%s" % ((("%d " % e.count) if e.count > 1 else ""), ("%s " % "/".join("%02x" % int(c * 255) for c in e.color) if e.color else ""), e.name) for e in parsed.entities]
        rows.append({"n": n, "cat": cat, "prompt": p, "mode": mode, "time": parsed.time, "flags": sorted(parsed.flags),
                     "recognised": ents, "ignored": parsed.unknown_words})
        # 2x2 box downscale for the contact sheet
        w2, h2 = W // 2, H // 2; t = bytearray(w2 * h2 * 3)
        for y in range(h2):
            for x in range(w2):
                for c in range(3):
                    i = ((2 * y) * W + 2 * x) * 3 + c
                    t[(y * w2 + x) * 3 + c] = (rgb[i] + rgb[i + 3] + rgb[i + W * 3] + rgb[i + W * 3 + 3]) // 4
        tiles.append(bytes(t))
json.dump(rows, open(os.path.join(S, "holdout_results.json"), "w"), indent=1)
# contact sheets: 2 sheets x (4 rows x 4 cols), 4px gaps
w2, h2, gap = W // 2, H // 2, 6
for sheet in range(2):
    if sheet * 16 >= len(tiles):
        break
    rows_in = min(4, (len(tiles) - sheet * 16 + 3) // 4)
    SW, SH = 4 * w2 + 5 * gap, rows_in * h2 + (rows_in + 1) * gap
    buf = bytearray(b"\xf0\xf0\xf0" * (SW * SH))
    for r in range(rows_in):
        for c in range(4):
            t = tiles[(sheet * 4 + r) * 4 + c]
            for y in range(h2):
                o = ((gap + r * (h2 + gap) + y) * SW + gap + c * (w2 + gap)) * 3
                buf[o:o + w2 * 3] = t[y * w2 * 3:(y + 1) * w2 * 3]
    open(os.path.join(S, ("holdout_sheet1_01-16.png", "holdout_sheet2_17-28.png")[sheet]), "wb").write(encode_png(SW, SH, bytes(buf)))
for r in rows:
    print("%2d | %-47s | %-9s | recognised: %-34s | ignored: %s" % (r["n"], r["prompt"], r["mode"], ", ".join(r["recognised"] + ([r["time"]] if r["time"] else []) + r["flags"]) or "-", ", ".join(r["ignored"]) or "-"))
