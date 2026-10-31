#!/usr/bin/env python3
"""Check a run of examples/spec_render_all.py against the client's spec and write <run>/index.html.

    python3 examples/spec_check.py [samples/spec_run]

Checks per picture: the file exists, JPEG header, size = the slot's size from the spec, bytes within the slot budget, hero text contrast >= 4.5:1,
not a neutral fallback (unless the business has no niche), judge ok; per business: 20 pictures, hero/about/gallery/card/team/background counts, the
minimum perceptual distance between scene pictures. Also counts how many distinct niches were used.
"""
import collections
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = {"hero": (1600, 900), "about": (1200, 900), "gallery": (900, 900), "card": (800, 600), "team": (600, 600), "background": (1600, 900)}
BUDGET = {"hero": 105000, "about": 70000, "gallery": 56000, "card": 38000, "team": 30000, "background": 40000}


def main(run):
    data = json.load(open(os.path.join(run, "summary.json"), encoding="utf-8"))["all"]
    probs = collections.defaultdict(list)
    kinds = collections.Counter()
    total = 0
    niches = set()
    byt = collections.defaultdict(list)
    for m in data:
        key = m.get("business") or "_types/" + m.get("pack", "?")
        d = os.path.join(run, key if "business" in m else os.path.join("_types", next((x for x in os.listdir(os.path.join(run, "_types")) if x.endswith("".join(c if c.isalnum() else "_" for c in m["pack"].lower())[:32])), "")))
        if m.get("niche"):
            niches.add(m["niche"])
        for it in m["items"]:
            total += 1
            kind = it["slot"].split("-")[0]
            kinds[kind] += 1
            fn = os.path.join(d, it["file"])
            ok = os.path.isfile(fn)
            if not ok:
                probs[key].append("%s: file missing" % it["slot"]); continue
            raw = open(fn, "rb").read(2)
            if raw != b"\xff\xd8":
                probs[key].append("%s: not a JPEG" % it["slot"])
            if tuple(it["size"]) != SIZES[kind]:
                probs[key].append("%s: size %s != %s" % (it["slot"], it["size"], SIZES[kind]))
            nb = os.path.getsize(fn)
            byt[kind].append(nb)
            if nb > BUDGET[kind] * 1.02:
                probs[key].append("%s: %d bytes > budget %d" % (it["slot"], nb, BUDGET[kind]))
            if kind == "hero" and (it.get("contrast") or 0) < 4.5:
                probs[key].append("%s: hero contrast %s" % (it["slot"], it.get("contrast")))
            if it.get("fallback") and m.get("niche"):
                probs[key].append("%s: neutral fallback although niche %s" % (it["slot"], m["niche"]))
            if kind in ("hero", "about", "gallery", "card") and it.get("judge_ok") is False:
                probs[key].append("%s: judge not ok" % it["slot"])
        if "business" in m and len(m["items"]) != 20:
            probs[key].append("%d pictures instead of 20" % len(m["items"]))
    print("%d pictures, %d businesses + %d types, %d distinct niches used" % (total, len([m for m in data if "business" in m]), len([m for m in data if "pack" in m]), len(niches)))
    print("by kind:", dict(kinds))
    print("avg bytes:", {k: sum(v) // len(v) for k, v in byt.items()}, "| max:", {k: max(v) for k, v in byt.items()})
    nprob = sum(len(v) for v in probs.values())
    print("problems: %d in %d businesses" % (nprob, len(probs)))
    for k, v in list(probs.items())[:25]:
        print("  ", k, v[:4])
    mind = [it["min_distance"] for m in data for it in m["items"] if it.get("min_distance") is not None]
    if mind:
        print("perceptual distance of scene pictures within a business: min %d, <8 in %d of %d" % (min(mind), sum(1 for x in mind if x < 8), len(mind)))
    rows = []
    for m in data:
        if "business" not in m:
            continue
        probs_n = len(probs.get(m["business"], []))
        rows.append('<figure><a href="%s/sheet.jpg"><img src="%s/sheet.jpg" loading="lazy" alt="%s"></a><figcaption><b>%s</b> (%s) niche <code>%s</code> %s</figcaption></figure>' % (
            m["business"], m["business"], html.escape(m["name"]), html.escape(m["name"]), m["business"], m["niche"], "" if not probs_n else "&#9888; %d issue(s)" % probs_n))
    page = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Image AI spec run</title>'
            '<style>body{font:14px system-ui;margin:16px;background:#f4f4f6;color:#111}figure{margin:0 0 20px;background:#fff;padding:8px;border-radius:8px}img{width:100%%;height:auto}h1{font-size:20px}</style>'
            '<h1>Image AI: %d pictures for %d businesses (spec Image-AI-training.pdf)</h1><p>Each sheet: 3 hero, about, 6 gallery, 6 card, 3 team, background. Files: &lt;business&gt;/&lt;slot&gt;.jpg, manifest.json. Generic business types: _types/.</p>%s' % (
                total, len(rows), "".join(rows)))
    with open(os.path.join(run, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)
    return 1 if nprob else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "samples", "spec_run")))
