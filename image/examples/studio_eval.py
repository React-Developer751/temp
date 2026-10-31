#!/usr/bin/env python3
"""Measure the studio: prompt understanding (before / after training), wrong-subject rate, set consistency, file sizes, time.

    python3 examples/studio_eval.py                          # keyword matcher only (before training)
    python3 examples/studio_eval.py --model studio_model.json  # also with the trained model (after training)
    python3 examples/studio_eval.py --sheets                 # also write the per-niche proof sheets to samples/

The hold-out prompts (studio_data/holdout_prompts.json) were written blind and are never used for training.
"""
import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.learn import LearnedModel, label_tokens  # noqa: E402
from pixelmath.imageread import load_thumbnail  # noqa: E402
from pixelmath.studio.api import PHASH_MIN, make_set, scene  # noqa: E402
from pixelmath.studio.classifier import as_classifier  # noqa: E402
from pixelmath.studio.match import match_niche  # noqa: E402
from pixelmath.studio.niches import NICHES, load_all  # noqa: E402
from pixelmath.studio.sheet import set_sheet  # noqa: E402

PROOF = ("restaurant-italian", "gym", "dental", "saas", "kurti-store", "salon", "bakery", "yoga", "real-estate", "school")


def pct(n, d):
    return "%5.1f%%" % (100.0 * n / max(1, d))


def matching(hold, clf, label):
    """Prompt -> niche on all hold-out prompts: correct / fallback / wrong (picture of another niche)."""
    c = f = w = 0
    wrong = []
    for nid, prompts in hold["in_niche"].items():
        for p in prompts:
            got, _ = match_niche(p, clf)
            if got == nid:
                c += 1
            elif got is None:
                f += 1
            else:
                w += 1
                wrong.append((p, nid, got))
    off_w = 0
    for p in hold["off_niche"]:
        got, _ = match_niche(p, clf)
        off_w += got is not None
    n = c + f + w
    print("  %-22s in-niche %3d prompts: correct %s  fallback %s  wrong %s | off-niche %2d prompts: wrongly matched %d" % (
        label, n, pct(c, n), pct(f, n), pct(w, n), len(hold["off_niche"]), off_w))
    return {"correct": c, "fallback": f, "wrong": w, "total": n, "off_niche_wrong": off_w, "wrong_examples": wrong[:8]}


def render_acceptance(hold, model, seeds=(1, 2, 3), size=(256, 160)):
    """Draw one descriptive prompt per niche x 3 seeds (+ the off-niche prompts) and count what the pictures show."""
    ok = fb = bad = 0
    off_ok = off_bad = 0
    clf = as_classifier(model) if model else None
    bad_list = []
    t0 = time.time()
    for nid in NICHES:
        p = hold["in_niche"][nid][2]
        for s in seeds:
            r = scene(p, size[0], size[1], s, classifier=clf).report
            if r["niche"] == nid and not r["fallback"]:
                ok += 1
            elif r["fallback"]:
                fb += 1
            else:
                bad += 1
                bad_list.append((p, nid, r["niche"]))
    for p in hold["off_niche"]:
        for s in seeds:
            r = scene(p, size[0], size[1], s, classifier=clf).report
            if r["fallback"]:
                off_ok += 1
            else:
                off_bad += 1
                bad_list.append((p, None, r["niche"]))
    n = ok + fb + bad
    print("  pictures: %d niche prompts x %d seeds: right subject %s (%d)  fallback %s (%d)  WRONG subject %d | off-niche %d pictures: fallback %d, wrong %d | %.0fs" % (
        len(NICHES), len(seeds), pct(ok, n), ok, pct(fb, n), fb, bad, off_ok + off_bad, off_ok, off_bad, time.time() - t0))
    return {"right": ok, "fallback": fb, "wrong": bad, "total": n, "off_niche_fallback": off_ok, "off_niche_wrong": off_bad, "wrong_examples": bad_list[:8]}


def set_metrics(model, sheets):
    print("  site sets (6 pictures each, real sizes):")
    rows = []
    for nid in PROOF:
        if nid not in NICHES:
            continue
        res, rep = make_set(NICHES[nid].title, 6, 7, niche=nid, fmt="jpeg", model=model)
        hero = res[0].report["bytes"]
        tiles = max(r.report["bytes"] for r in res[2:])
        row = {"niche": nid, "seconds": rep["seconds"], "min_distance": rep["min_distance"], "palette_family": rep["palette_family"],
               "hero_contrast": rep["hero_contrast"], "hero_bytes": hero, "max_tile_bytes": tiles, "redrawn": rep["redrawn"],
               "judge_ok": all(r.report["judge_ok"] for r in res)}
        rows.append(row)
        print("   %-18s %5.1fs  min dist %2d (>= %d)  family %.2f  hero contrast %.2f  hero %5d B  max tile %5d B  redrawn %d  judge ok %s" % (
            nid, row["seconds"], row["min_distance"], PHASH_MIN, row["palette_family"], row["hero_contrast"] or 0, hero, tiles, row["redrawn"], row["judge_ok"]))
        if sheets:
            os.makedirs(os.path.join(ROOT, "samples"), exist_ok=True)
            set_sheet(res, rep, os.path.join(ROOT, "samples", "studio-%s.jpg" % nid))
    return rows


def regressor_holdout(model, root):
    """Colour error (0-255 RGB) of the trained model on pictures it never saw, against knowing nothing."""
    path = os.path.join(root, "studio_data", "holdout")
    if model is None or not os.path.isdir(path):
        return None
    with open(os.path.join(path, "manifest.jsonl"), encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh if line.strip()]
    mean = [sum(b for b in col) / len(model.samples) / 255.0 for col in zip(*[s.thumb for s in model.samples])]
    err = base = grey = 0.0
    for r in recs:
        target = load_thumbnail(os.path.join(path, r["image"]), model.grid)
        text = r["caption"] + " " + " ".join(label_tokens(r["niche"], r["mood"]))
        pred = model.predict(text)
        err += sum((a - b) ** 2 for a, b in zip(pred, target)) / len(target)
        base += sum((a - b) ** 2 for a, b in zip(mean, target)) / len(target)
        grey += sum((0.5 - b) ** 2 for b in target) / len(target)
    n = len(recs)
    out = {"images": n, "trained_rmse": round(math.sqrt(err / n) * 255, 1), "average_image_rmse": round(math.sqrt(base / n) * 255, 1),
           "untrained_rmse": round(math.sqrt(grey / n) * 255, 1)}
    print("  colour prediction on %d hold-out pictures: untrained %.1f -> average picture %.1f -> trained %.1f (RMSE, lower is better)" % (
        n, out["untrained_rmse"], out["average_image_rmse"], out["trained_rmse"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--sheets", action="store_true")
    ap.add_argument("--skip-sets", action="store_true")
    ap.add_argument("--sheets-only", action="store_true", help="only (re)draw the per-niche proof sheets in samples/")
    ap.add_argument("--out", default=os.path.join(ROOT, "samples", "studio_eval.json"))
    args = ap.parse_args()
    load_all()
    if args.sheets_only:
        set_metrics(None, True)
        return
    with open(os.path.join(ROOT, "studio_data", "holdout_prompts.json"), encoding="utf-8") as fh:
        hold = json.load(fh)
    model = LearnedModel.load(args.model) if args.model else None
    result = {"niches": len(NICHES)}
    print("%d niches registered" % len(NICHES))
    print("PROMPT UNDERSTANDING (hold-out prompts written blind):")
    result["matching_keywords_only"] = matching(hold, None, "before training")
    if model:
        clf = as_classifier(model)
        result["matching_with_model"] = matching(hold, clf, "after training")
    print("PICTURES:")
    result["pictures"] = render_acceptance(hold, model)
    if model:
        result["colour_holdout"] = regressor_holdout(model, ROOT)
    if not args.skip_sets:
        print("SETS:")
        result["sets"] = set_metrics(model, args.sheets)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
