#!/usr/bin/env python3
"""Draw every picture of the client's spec: 99 businesses x 20 pictures (+ the 20 generic business types x 10) into samples/spec_run/.

    python3 examples/spec_render_all.py [--out samples/spec_run] [--workers 6] [--only pest_control,dental_clinic] [--palette 0] [--seed 1]

<out>/<business>/<slot>.jpg, manifest.json and sheet.jpg per business; <out>/summary.json with the checks (sizes, bytes, niche, fallback, contrast).
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.studio.spec import businesses, render_business  # noqa: E402


def one(args):
    kind, key, out, pal_i, seed = args
    t0 = time.time()
    if kind == "biz":
        d = os.path.join(out, key)
        m = render_business(key, d, palette_index=pal_i, seed=seed, sheet=os.path.join(d, "sheet.jpg"))
    else:
        d = os.path.join(out, "_types", key["slug"])
        m = render_pack(key, d, seed)
    m["seconds"] = round(time.time() - t0, 1)
    return m


def render_pack(pack, d, seed):
    """A generic business-type pack (10 pictures): same pipeline, the pack's niche, a neutral palette."""
    from pixelmath.studio.spec import SLOT_SIZES, render, full_request  # noqa: F401
    os.makedirs(d, exist_ok=True)
    pal = {"name": "type default", "accent": pack.get("accent") or "#2f5bd2", "bg": "#f7f9ff"}
    items = []
    for it in pack["items"]:
        res = render(full_request(it["prompt"], pal), slot=it["slot"], seed=seed, accent=pal["accent"], bg=pal["bg"], niche=pack["niche"] or "none", fmt="jpeg")
        fn = it["slot"] + ".jpg"
        with open(os.path.join(d, fn), "wb") as fh:
            fh.write(res.data)
        items.append(dict(res.report, prompt=it["prompt"], file=fn))
    return {"pack": pack["name"], "niche": pack["niche"], "palette": pal, "items": items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "samples", "spec_run"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--palette", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-types", action="store_true")
    a = ap.parse_args()
    only = [x for x in a.only.split(",") if x]
    jobs = [("biz", b["id"], a.out, a.palette, a.seed) for b in businesses() if not only or b["id"] in only]
    if not a.no_types and not only:
        spec = json.load(open(os.path.join(ROOT, "studio_data", "spec", "image_ai_spec.json"), encoding="utf-8"))
        mp = json.load(open(os.path.join(ROOT, "studio_data", "spec", "biz_niche.json"), encoding="utf-8"))["packs"]
        for k, p in enumerate(spec["packs"]):
            p = dict(p, niche=mp.get(p["name"]), slug="%02d_%s" % (k + 1, "".join(c if c.isalnum() else "_" for c in p["name"].lower())[:32]))
            jobs.append(("pack", p, a.out, 0, a.seed))
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    manifests = []
    with Pool(a.workers) as pool:
        for m in pool.imap_unordered(one, jobs):
            manifests.append(m)
            print("%-30s %-18s %2d pictures %5.0fs  (%d/%d done, %.0f min)" % (m.get("business") or m.get("pack"), m["niche"], len(m["items"]), m["seconds"], len(manifests), len(jobs),
                                                                         (time.time() - t0) / 60), flush=True)
    summary = {"seconds": round(time.time() - t0), "businesses": len([m for m in manifests if "business" in m]), "types": len([m for m in manifests if "pack" in m]),
               "pictures": sum(len(m["items"]) for m in manifests), "manifests": [{k: v for k, v in m.items() if k != "items"} | {"items": len(m["items"])} for m in manifests]}
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "all": manifests}, fh, ensure_ascii=False)
    print("done: %d pictures in %.1f min" % (summary["pictures"], summary["seconds"] / 60))


if __name__ == "__main__":
    main()
