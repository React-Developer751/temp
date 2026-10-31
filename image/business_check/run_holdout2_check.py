"""Second holdout set (animals, machinery, trades, playground, text): python3 business_check/run_holdout2_check.py"""
import json
import os
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(P, "business_check")
sys.path.insert(0, P)
from pixelmath import encode_png, render          # noqa: E402
from pixelmath.tokenizer import parse             # noqa: E402

PROMPTS = [
    # pets and farm
    "veterinary clinic with a dog and a cat", "goldfish aquarium shop", "horse riding school", "dairy farm with cows",
    "sheep grazing on a green hill", "safari wildlife elephant",
    # machinery and industry
    "construction site with a crane and excavator", "tractor ploughing a field", "solar energy company with solar panels",
    "wind turbines on a hill at sunset", "warehouse forklift logistics", "factory manufacturing",
    # trades and tools
    "plumber fixing a leaking tap", "carpenter workshop with saw and hammer", "electrician wiring a house", "house painting services",
    "tailor shop with sewing machine", "hair salon scissors and comb", "home cleaning service", "car repair garage",
    # playground and sports
    "kids playground with swings and slide", "cricket academy", "football tournament trophy", "kindergarten children playing",
    # readable text
    'coffee shop sign "COFFEE HOUSE"', 'grand opening poster "GRAND OPENING" "FREE COFFEE FOR ALL"', 'logo for "GREEN LEAF" organic store',
    'sale banner "FLAT 50% OFF" red background', 'bakery "FRESH BREAD DAILY" sign', 'price tag "₹499"',
    'hotel "SEA VIEW RESORT" beach', 'birthday party "HAPPY BIRTHDAY"',
    # deliberately outside the vocabulary
    "fire fighters rescue", "ambulance", "dentist tooth", "ice skating rink",
]
W, H, GAP = 512, 320, 6
out = os.path.join(S, "holdout2_images")
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
with open(os.path.join(S, "holdout2_results.json"), "w") as fh:
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
    with open(os.path.join(S, "holdout2_sheet%d_%02d-%02d.png" % (sheet + 1, sheet * per + 1, sheet * per + len(chunk))), "wb") as fh:
        fh.write(encode_png(SW, SH, bytes(buf)))
for r in rows:
    print("%2d | %-58s | %-9s | %-44s | ignored: %s" % (r["n"], r["prompt"][:58], r["mode"], ", ".join(dict.fromkeys(r["recognised"])) or "-", ", ".join(r["ignored"]) or "-"))
