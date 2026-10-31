import json, os, sys
"""Re-render the 32 business prompts: python3 business_check/run_business_check.py"""
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(P, "business_check")
sys.path.insert(0, P)
from pixelmath import render, encode_png
from pixelmath.tokenizer import parse

CATS = [
 ("Hospitality & travel", ["luxury beach resort at sunset", "hotel in the mountains at night", "tropical island with palm trees and blue sea", "camping tent in the forest"]),
 ("Food", ["fresh pizza", "coffee shop", "bakery with fresh bread", "restaurant dining table"]),
 ("Real estate", ["modern house with a garden", "city apartment buildings at dusk", "red house with a tree", "villa near the sea"]),
 ("Tech / SaaS", ["software company dashboard", "futuristic cyberpunk city at night", "blue abstract technology background", "laptop on a desk"]),
 ("Wellness", ["yoga studio", "green nature meditation", "mandala pattern", "doctor and medical clinic"]),
 ("Education / translation", ["students studying with books", "certified translation documents", "graduation cap", "university campus"]),
 ("Retail", ["red shoes product photo", "gift box", "shopping bag sale", "red heart"]),
 ("Auto / events / logo", ["car driving on a road at sunset", "wedding celebration", "birthday balloons", "blue circle logo on white background"]),
]
W, H = 512, 320
out = os.path.join(S, "images"); os.makedirs(out, exist_ok=True)
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
json.dump(rows, open(os.path.join(S, "results.json"), "w"), indent=1)
# contact sheets: 2 sheets x (4 rows x 4 cols), 4px gaps
w2, h2, gap = W // 2, H // 2, 6
for sheet in range(2):
    SW, SH = 4 * w2 + 5 * gap, 4 * h2 + 5 * gap
    buf = bytearray(b"\xf0\xf0\xf0" * (SW * SH))
    for r in range(4):
        for c in range(4):
            t = tiles[(sheet * 4 + r) * 4 + c]
            for y in range(h2):
                o = ((gap + r * (h2 + gap) + y) * SW + gap + c * (w2 + gap)) * 3
                buf[o:o + w2 * 3] = t[y * w2 * 3:(y + 1) * w2 * 3]
    open(os.path.join(S, ("sheet1_prompts_01-16.png", "sheet2_prompts_17-32.png")[sheet]), "wb").write(encode_png(SW, SH, bytes(buf)))
for r in rows:
    print("%2d | %-47s | %-9s | recognised: %-34s | ignored: %s" % (r["n"], r["prompt"], r["mode"], ", ".join(r["recognised"] + ([r["time"]] if r["time"] else []) + r["flags"]) or "-", ", ".join(r["ignored"]) or "-"))
