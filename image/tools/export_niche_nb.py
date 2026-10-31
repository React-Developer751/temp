#!/usr/bin/env python3
"""Write the niche classifier shipped inside the package (pixelmath/studio/niche_nb.json), so the studio understands prompts without any model file.

    python3 tools/export_niche_nb.py --captions                 # straight from the caption files in studio_data/ (no pictures needed)
    python3 tools/export_niche_nb.py studio_model.json          # or copy it out of a model trained with train.py

The classifier is naive Bayes over caption words, so it only needs the captions and their niche: --captions gives exactly the classifier that
`make_studio_dataset.py` + `train.py` would store in the model, without drawing the 7000 pictures. It reads captions_train.json, prompts_train.json
and captions_negative.json (all written by the project author). The client's spec captions (spec_train.json) are never part of the published
classifier; PIXELMATH_CLIENT_SPEC=1 adds them for repo / client use, and the file written then must not be shipped.
"""
import json
import os
import sys
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "examples"))

from pixelmath.learn import LearnedModel  # noqa: E402
from pixelmath.studio.classifier import NONE, build_niche_nb  # noqa: E402
from make_studio_dataset import caption_files  # noqa: E402


def from_captions(data=os.path.join(ROOT, "studio_data")):
    train = {}
    for name in ("captions_train.json",) + caption_files():
        path = os.path.join(data, name)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for nid, caps in json.load(fh).items():
                    train[nid] = train.get(nid, []) + caps
    neg_path = os.path.join(data, "captions_negative.json")
    negatives = json.load(open(neg_path, encoding="utf-8")) if os.path.exists(neg_path) else []
    rows = [SimpleNamespace(caption=c, niche=nid) for nid, caps in train.items() for c in caps]
    rows += [SimpleNamespace(caption=c, niche=NONE) for c in negatives]
    return build_niche_nb(rows)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    if argv[0] == "--captions":
        nb = from_captions()
    else:
        nb = LearnedModel.load(argv[0]).extras.get("niche_nb")
    if not nb:
        sys.exit("no niche classifier (train on a manifest with niche labels first)")
    out = os.path.join(ROOT, "pixelmath", "studio", "niche_nb.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(nb, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print("wrote %s (%d classes, %d words, %d bytes)" % (out, len(nb["classes"]), nb["vocab"], os.path.getsize(out)))


if __name__ == "__main__":
    main(sys.argv[1:])
