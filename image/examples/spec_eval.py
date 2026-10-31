#!/usr/bin/env python3
"""Measure how well the studio understands the client's picture spec (Image-AI-training.pdf).

    python3 examples/spec_eval.py

1. Production requests: every prompt of the spec (99 businesses x 20 + 20 business types x 10) goes through spec.parse_request / resolve_niche: is the
   business found, and is it the niche the mapping says? (the request always names its business: "... for a <business> website")
2. Subject only: the held-out prompts (hero-3, gallery-5/6, card-5/6 of every business; never trained on) without the business suffix go through the
   trained prompt matcher alone: right niche / refused (neutral) / wrong niche. This is the harder test: no business name in the text.
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.studio.classifier import as_classifier  # noqa: E402
from pixelmath.studio.match import match_niche  # noqa: E402
from pixelmath.studio.niches import NICHES, load_all  # noqa: E402
from pixelmath.studio.spec import parse_request, resolve_niche  # noqa: E402


def main():
    load_all()
    spec = json.load(open(os.path.join(ROOT, "studio_data", "spec", "image_ai_spec.json"), encoding="utf-8"))
    mp = json.load(open(os.path.join(ROOT, "studio_data", "spec", "biz_niche.json"), encoding="utf-8"))
    niche_of = dict(mp["existing"], **mp["new"])
    ok = bad = missing = 0
    for b in spec["businesses"]:
        exp = niche_of[b["id"]]
        for it in b["items"]:
            nid, how = resolve_niche(parse_request(it["prompt"])["business"], it["prompt"])
            ok += nid == exp
            bad += nid != exp and nid is not None
            missing += nid is None
    for p in spec["packs"]:
        exp = mp["packs"].get(p["name"])
        for it in p["items"]:
            nid, _ = resolve_niche(parse_request(it["prompt"])["business"], it["prompt"])
            ok += nid == exp
            bad += nid != exp and nid is not None
            missing += nid is None and exp is not None
    n = ok + bad + missing
    print("1. production requests (business named in the text): %d prompts: right niche %.1f%%, wrong %d, no niche %d" % (n, 100.0 * ok / n, bad, missing))
    missing_niches = sorted({v for v in niche_of.values() if v not in NICHES})
    print("   niches the spec needs that do not exist yet: %s" % (missing_niches or "none"))
    hold = json.load(open(os.path.join(ROOT, "studio_data", "spec_holdout.json"), encoding="utf-8"))
    clf = as_classifier(None)
    c = f = w = 0
    wrong = collections.Counter()
    for nid, caps in hold.items():
        for cap in caps:
            got, _ = match_niche(cap, clf)
            if got == nid:
                c += 1
            elif got is None:
                f += 1
            else:
                w += 1
                wrong[(nid, got)] += 1
    t = c + f + w
    print("2. subject only, no business name (%d held-out prompts): right %.1f%%, refused %.1f%%, wrong %.1f%%" % (t, 100.0 * c / t, 100.0 * f / t, 100.0 * w / t))
    print("   most frequent wrong pairs:", wrong.most_common(8))


if __name__ == "__main__":
    main()
