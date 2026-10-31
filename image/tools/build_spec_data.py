#!/usr/bin/env python3
"""Build the package's picture-spec data from the owner's spec (studio_data/spec/image_ai_spec.json + biz_niche.json + the design styles).

    python3 tools/build_spec_data.py
writes pixelmath/studio/spec_data.json (businesses, niches, palettes, packs, design styles, style line) and pixelmath/studio/spec_prompts.json
(the 20 [{slot, prompt}] of every business and the 10 of every business type: only what pixelmath/studio/spec.py reads; the sizes follow from the slot).
Both ship in the package; the source files stay in studio_data/spec/.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "studio_data", "spec")
OUT = os.path.join(ROOT, "pixelmath", "studio")
sys.path.insert(0, ROOT)

from pixelmath.studio.spec import STYLE_LINE           # noqa: E402  the spec's STYLE LINE (section 2), added to every request

# design styles of the spec (section 3): id -> dark? ("Dark background, glowing accents, deep shadows" vs "Light background, airy, soft shadows")
DARK_STYLES = ("minimal-dark", "cyberpunk", "glass", "luxe-dark", "techno-black", "noir-lab", "neon-arcade")
LIGHT_STYLES = ("minimal-light", "soft-neo", "retro", "bold-contrast", "editorial", "playful-pop", "clinic-mesh", "plum-ivory", "trust-navy", "violet-glow", "cream-coral",
                "maison-noir", "film-editorial", "atelier-3d", "apple-tile", "showroom-white", "blush-serif", "studio-index")


def lum(hexcol):
    r, g, b = (int(hexcol[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main():
    spec = json.load(open(os.path.join(SPEC, "image_ai_spec.json"), encoding="utf-8"))
    mp = json.load(open(os.path.join(SPEC, "biz_niche.json"), encoding="utf-8"))
    niche_of = dict(mp["existing"], **mp["new"])
    out = {"businesses": [], "packs": [], "styles": {"dark": list(DARK_STYLES), "light": list(LIGHT_STYLES)},
           "style_line": STYLE_LINE}
    for b in spec["businesses"]:
        out["businesses"].append({"id": b["id"], "name": b["name"], "niche": niche_of[b["id"]],
                                  "palettes": [{"name": n.strip(), "accent": a, "bg": bg, "dark": lum(bg) < 0.35} for n, a, bg in b["palettes"]]})
    for p in spec["packs"]:
        out["packs"].append({"name": p["name"], "niche": mp["packs"].get(p["name"])})
    dst = os.path.join(OUT, "spec_data.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s: %d businesses, %d packs, %d bytes" % (dst, len(out["businesses"]), len(out["packs"]), os.path.getsize(dst)))
    items = lambda x: [{"slot": it["slot"], "prompt": it["prompt"]} for it in x["items"]]          # noqa: E731
    prompts = {"businesses": [{"id": b["id"], "items": items(b)} for b in spec["businesses"]],
               "packs": [{"name": p["name"], "items": items(p)} for p in spec["packs"]]}
    dst = os.path.join(OUT, "spec_prompts.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(prompts, fh, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s: %d prompts, %d bytes" % (dst, sum(len(x["items"]) for x in prompts["businesses"] + prompts["packs"]), os.path.getsize(dst)))


if __name__ == "__main__":
    sys.exit(main())
