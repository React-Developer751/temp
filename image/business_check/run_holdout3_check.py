"""Third holdout set (emergency, dental, winter, Hindi/Chinese text, crowded scenes): python3 business_check/run_holdout3_check.py"""
import json
import os
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(P, "business_check")
sys.path.insert(0, P)
from pixelmath import encode_png, render          # noqa: E402
from pixelmath.tokenizer import parse             # noqa: E402

PROMPTS = [
    # emergency, dental and medical, winter sports
    "fire station with fire truck and firefighters", "ambulance rushing to hospital", "police patrol car on the road",
    "fire safety training extinguisher", "dentist clinic with a happy tooth", "dental chair and toothbrush",
    "pharmacy pills and syringe", "doctor with stethoscope and thermometer", "ski resort with a skier on the mountain",
    "ice skating rink with a skater", "snowman in winter", "snowboard shop", "ice hockey match", "sledding on a snowy hill",
    # Hindi and Chinese text
    'tea shop sign "\u091a\u093e\u092f \u0915\u0940 \u0926\u0941\u0915\u093e\u0928"', 'poster "\u0938\u094d\u0935\u093e\u0917\u0924 \u0939\u0948" welcome',
    'banner "\u0928\u092e\u0938\u094d\u0924\u0947" with flowers', 'sale poster "\u0938\u0947\u0932" "50% \u091b\u0942\u091f"',
    'chinese restaurant sign "\u6b22\u8fce\u5149\u4e34"', 'tea shop "\u8336" sign', 'poster "\u7279\u4ef7" red background',
    'coffee shop "\u5496\u5561 COFFEE"',
    # crowded scenes and mixed subjects
    "car mechanic garage with tools", "farm with tractor cows and sheep", "construction workers with crane and excavator",
    "online shop with phone laptop and shopping cart", "school with students books and playground", "hospital with doctor nurse and ambulance",
    # deliberately outside the vocabulary
    "submarine under the sea", "astronaut on the moon", "pizza delivery scooter", "robot",
]
W, H, GAP = 512, 320, 6
out = os.path.join(S, "holdout3_images")
os.makedirs(out, exist_ok=True)
rows, tiles = [], []
for n, prompt in enumerate(PROMPTS, 1):
    cv, parsed, mode = render(prompt, W, H)
    rgb = cv.to_rgb_bytes()
    with open(os.path.join(out, "%02d.png" % n), "wb") as fh:
        fh.write(encode_png(W, H, rgb))
    ents = [e.name for e in parsed.entities]
    rows.append({"n": n, "prompt": prompt, "mode": mode, "time": parsed.time, "flags": sorted(parsed.flags),
                 "recognised": ents, "ignored": parsed.unknown_words, "texts": parsed.texts})
    w2, h2 = W // 2, H // 2
    t = bytearray(w2 * h2 * 3)
    for y in range(h2):
        for x in range(w2):
            for c in range(3):
                i = ((2 * y) * W + 2 * x) * 3 + c
                t[(y * w2 + x) * 3 + c] = (rgb[i] + rgb[i + 3] + rgb[i + W * 3] + rgb[i + W * 3 + 3]) // 4
    tiles.append(bytes(t))
with open(os.path.join(S, "holdout3_results.json"), "w") as fh:
    json.dump(rows, fh, indent=1)
w2, h2 = W // 2, H // 2
per = 16
for sheet in range((len(tiles) + per - 1) // per):
    chunk = tiles[sheet * per:(sheet + 1) * per]
    nrows = (len(chunk) + 3) // 4
    SW, SH = 4 * w2 + 5 * GAP, nrows * h2 + (nrows + 1) * GAP
    buf = bytearray(b"\xf0\xf0\xf0" * (SW * SH))
    for k, t in enumerate(chunk):
        r, c = divmod(k, 4)
        for y in range(h2):
            o = ((GAP + r * (h2 + GAP) + y) * SW + GAP + c * (w2 + GAP)) * 3
            buf[o:o + w2 * 3] = t[y * w2 * 3:(y + 1) * w2 * 3]
    with open(os.path.join(S, "holdout3_sheet%d_%02d-%02d.png" % (sheet + 1, sheet * per + 1, sheet * per + len(chunk))), "wb") as fh:
        fh.write(encode_png(SW, SH, bytes(buf)))
for r in rows:
    print("%2d | %-58s | %-9s | %-44s | ignored: %s" % (r["n"], r["prompt"][:58], r["mode"], ", ".join(dict.fromkeys(r["recognised"])) or "-", ", ".join(r["ignored"]) or "-"))
