#!/usr/bin/env python3
"""Build the studio training set: our own pictures (drawn by the engine's niche generators) with {image, caption, niche, mood} labels.

    python3 examples/make_studio_dataset.py                      # writes studio_data/train/ and studio_data/holdout/

train/    one picture per (niche, training caption): the caption's mood / colour words steer the drawing (so "calm blue" really is cool and blue);
          manifest.jsonl lines look like {"image": "dental/003.jpg", "caption": "...", "niche": "dental", "mood": "cool"}
holdout/  separate pictures (other seeds, other prompts, never trained on) used only to measure the trained model.
Captions come from studio_data/captions_train.json (24 per niche), prompts_train.json (more phrasings, Hinglish and Hindi) and
holdout_prompts.json (6 per niche), all written by the project author without looking at the engine's keyword lists.
The client's picture spec captions (spec_train.json, made by make_spec_training.py) are NOT used unless you ask for them:

    PIXELMATH_CLIENT_SPEC=1 python3 examples/make_studio_dataset.py      # opt-in; the shipped classifier is trained on the author's captions only
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath.studio.api import scene  # noqa: E402
from pixelmath.studio.match import infer_look  # noqa: E402
from pixelmath.studio.niches import NICHES, load_all  # noqa: E402

MOODS = ("warm", "cool", "dark", "light")
VARIANTS = ("fit", "close", "wide", "fit-flip")


def pick_mood(niche, caption, k):
    mood, _ = infer_look(caption)
    if mood:
        return mood
    return niche.mood if k % 3 else MOODS[(k // 3 + len(niche.id)) % 4]             # two thirds in the niche's own mood, the rest varied


def draw(niche, caption, seed, k, size):
    mood, accent = infer_look(caption)
    res = scene(caption, size[0], size[1], seed, accent=accent, mood=pick_mood(niche, caption, k), niche=niche.id, variant=VARIANTS[k % 4], fmt="jpeg", quality=70)
    return res


def client_spec_wanted():
    """The picture spec's captions are opt-in (PIXELMATH_CLIENT_SPEC=1): the shipped classifier is trained on the author's captions only."""
    return os.environ.get("PIXELMATH_CLIENT_SPEC", "").strip().lower() in ("1", "true", "yes")


def caption_files(with_spec=None):
    """Extra caption files besides captions_train.json: the author's prompts, plus the client's spec captions only on request."""
    with_spec = client_spec_wanted() if with_spec is None else with_spec
    return ("prompts_train.json",) + (("spec_train.json",) if with_spec else ())


def build(root, size=(128, 80), log=print, with_spec=None):
    load_all()
    with open(os.path.join(root, "captions_train.json"), encoding="utf-8") as fh:
        train = json.load(fh)
    for extra in caption_files(with_spec):                                 # the author's extra prompts (and the spec's captions only if asked for), if present
        path = os.path.join(root, extra)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                more = json.load(fh)
            for nid, caps in more.items():
                train[nid] = list(train.get(nid, [])) + caps
    neg_path = os.path.join(root, "captions_negative.json")
    negatives = json.load(open(neg_path, encoding="utf-8")) if os.path.exists(neg_path) else []
    with open(os.path.join(root, "holdout_prompts.json"), encoding="utf-8") as fh:
        hold = json.load(fh)["in_niche"]
    missing = [n for n in NICHES if n not in train]
    if missing:
        raise SystemExit("no training captions for: %s" % ", ".join(missing))
    t0 = time.time()
    for part, source, seed0, per in (("train", train, 100, None), ("holdout", hold, 50000, 1)):
        folder = os.path.join(root, part)
        rows, n = [], 0
        for nid, niche in NICHES.items():
            caps = source[nid] if per is None else [source[nid][2]]               # one descriptive hold-out prompt per niche
            os.makedirs(os.path.join(folder, nid), exist_ok=True)
            for k, cap in enumerate(caps):
                res = draw(niche, cap, seed0 + k * 31, k, size)
                rel = "%s/%03d.jpg" % (nid, k)
                with open(os.path.join(folder, rel), "wb") as fh:
                    fh.write(res.data)
                rows.append({"image": rel, "caption": cap, "niche": nid, "mood": res.report["mood"]})
                n += 1
        if part == "train" and negatives:                                   # things that are NOT a niche: the model learns "none" = neutral abstract
            os.makedirs(os.path.join(folder, "none"), exist_ok=True)
            for k, cap in enumerate(negatives):
                mood, accent = infer_look(cap)
                res = scene(cap, size[0], size[1], seed0 + k, accent=accent, mood=mood or MOODS[k % 4], niche="none", fmt="jpeg", quality=70)
                rel = "none/%03d.jpg" % k
                with open(os.path.join(folder, rel), "wb") as fh:
                    fh.write(res.data)
                rows.append({"image": rel, "caption": cap, "niche": "none", "mood": res.report["mood"]})
                n += 1
        with open(os.path.join(folder, "manifest.jsonl"), "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        log("%s: %d pictures, manifest.jsonl (%.0fs so far)" % (part, n, time.time() - t0))


if __name__ == "__main__":
    build(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "studio_data"))
