#!/usr/bin/env python3
"""Turn the client's picture spec into training captions for the niche classifier.

    python3 examples/make_spec_training.py

Writes studio_data/spec_train.json and spec_holdout.json ({niche_id: [captions]}). Every business of the spec maps to a niche
(studio_data/spec/biz_niche.json). The subject of each picture prompt (the text before ", for a <business> website") is a caption of that niche.
Held out per business and never trained on: hero-3, gallery-5, gallery-6, card-5, card-6 (about 25% of the prompts). Team portraits and
background textures carry no business subject (only a role / "soft abstract texture"), so they are not captions.
Niches that had no hold-out prompts at all (the ones added for the spec) also get theirs in holdout_prompts.json, which the dataset builder needs.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "studio_data")
HOLD = {"hero-3", "gallery-5", "gallery-6", "card-5", "card-6"}


def subject_of(prompt):
    ms = list(re.finditer(r"for an? ((?:(?!for an? ).)+?) website\b", prompt))
    return (prompt[:ms[-1].start()] if ms else prompt).strip().rstrip(",").strip()


def main():
    spec = json.load(open(os.path.join(DATA, "spec", "image_ai_spec.json"), encoding="utf-8"))
    mp = json.load(open(os.path.join(DATA, "spec", "biz_niche.json"), encoding="utf-8"))
    niche_of = dict(mp["existing"], **mp["new"])
    train, hold = {}, {}
    for b in spec["businesses"]:
        nid = niche_of[b["id"]]
        name = b["name"].lower()
        train.setdefault(nid, []).extend([name, "%s website" % name, "for a %s website" % name, "pictures for a %s business" % name])
        for it in b["items"]:
            if it["slot"].startswith(("team", "background")):
                continue
            cap = subject_of(it["prompt"])
            (hold if it["slot"] in HOLD else train).setdefault(nid, []).append(cap)
    for p in spec["packs"]:
        nid = mp["packs"].get(p["name"])
        if not nid:
            continue
        for it in p["items"]:
            cap = subject_of(it["prompt"])
            (hold if it["slot"] in HOLD else train).setdefault(nid, []).append(cap)
    for name, obj in (("spec_train.json", train), ("spec_holdout.json", hold)):
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
    hp_path = os.path.join(DATA, "holdout_prompts.json")
    hp = json.load(open(hp_path, encoding="utf-8"))
    added = []
    for nid, caps in hold.items():
        if len(hp["in_niche"].get(nid, [])) < 3:
            hp["in_niche"][nid] = list(hp["in_niche"].get(nid, [])) + caps[:max(3, 6 - len(hp["in_niche"].get(nid, [])))]
            added.append(nid)
    with open(hp_path, "w", encoding="utf-8") as fh:
        json.dump(hp, fh, ensure_ascii=False, indent=1)
    print("train: %d niches, %d captions | hold-out: %d niches, %d captions | holdout_prompts.json got %d new niches" % (
        len(train), sum(map(len, train.values())), len(hold), sum(map(len, hold.values())), len(added)))


if __name__ == "__main__":
    sys.exit(main())
