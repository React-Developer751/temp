#!/usr/bin/env python3
"""Tune the niche classifier thresholds on a DEV split of the training captions (never on the hold-out prompts).

    python3 examples/tune_niche_classifier.py
Splits each niche's 24 training captions into 18 train / 6 dev (and the negative captions 90 / 30), trains the naive Bayes on the train
part, and reports how keywords + classifier do on the dev part for a few threshold settings.
The client's spec captions (spec_train.json) are added only with PIXELMATH_CLIENT_SPEC=1 (see make_studio_dataset.py).
"""
import json
import os
import sys
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.studio import match  # noqa: E402
from pixelmath.studio.classifier import NicheClassifier, build_niche_nb  # noqa: E402
from pixelmath.studio.niches import load_all  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "examples"))
from make_studio_dataset import caption_files  # noqa: E402


def load():
    with open(os.path.join(ROOT, "studio_data", "captions_train.json"), encoding="utf-8") as fh:
        pos = json.load(fh)
    for name in caption_files():
        extra = os.path.join(ROOT, "studio_data", name)
        if os.path.exists(extra):
            for nid, caps in json.load(open(extra, encoding="utf-8")).items():
                pos[nid] = list(pos.get(nid, [])) + caps
    neg_path = os.path.join(ROOT, "studio_data", "captions_negative.json")
    neg = json.load(open(neg_path, encoding="utf-8")) if os.path.exists(neg_path) else []
    return pos, neg


def split(pos, neg):
    train, dev = [], []
    for nid, caps in pos.items():
        for k, c in enumerate(caps):
            (dev if k % 4 == 3 else train).append((c, nid))
    for k, c in enumerate(neg):
        (dev if k % 4 == 3 else train).append((c, "none"))
    return train, dev


def evaluate(nb, dev):
    clf = NicheClassifier(nb) if nb else None
    c = f = w = 0
    for cap, nid in dev:
        got, _ = match.match_niche(cap, clf)
        if nid == "none":
            f += got is None
            w += got is not None
        elif got == nid:
            c += 1
        elif got is None:
            f += 1
        else:
            w += 1
    return c, f, w


def main():
    load_all()
    pos, neg = load()
    train, dev = split(pos, neg)
    nb = build_niche_nb([SimpleNamespace(caption=c, niche=n) for c, n in train])
    print("train %d captions, dev %d captions (%d negatives)" % (len(train), len(dev), sum(1 for _, n in dev if n == "none")))
    c, f, w = evaluate(None, dev)
    print("keywords only:  correct %3d  fallback(ok for negatives) %3d  WRONG %3d" % (c, f, w))
    for sb in (2.0, 4.0, 6.0):
        for wb in (0.5, 1.0):
            for prob in (0.8, 0.9, 0.95):
                match.STRONG_BONUS, match.WEAK_BONUS, match.NB_MIN_PROB = sb, wb, prob
                c, f, w = evaluate(nb, dev)
                print("keywords + NB strong+%.0f weak+%.1f prob>=%.2f: correct %3d  fallback %3d  WRONG %3d" % (sb, wb, prob, c, f, w))


if __name__ == "__main__":
    main()
