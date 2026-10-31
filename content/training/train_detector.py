"""Train the business-type detector (Naive Bayes on words, word pairs and character trigrams) and tune how much to trust it.

Training documents: every labelled TRAIN prompt (training/labelled.py) and every keyword of every type (the taxonomy itself).
The HOLDOUT prompts are never read here. The fusion weight is chosen by 5-fold cross-validation on TRAIN only.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corecraft import detector as D   # noqa: E402
from corecraft.business_types import T, type_scores   # noqa: E402
from labelled import TRAIN as LABELLED   # noqa: E402
from corecraft import feedback   # noqa: E402

TRAIN = LABELLED + feedback.pairs()   # the shipped labels plus what the owner corrected in the web UI

FOLDS = 5
WEIGHTS = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]


def keyword_docs():
    return [(k.rstrip("~"), tid) for tid, t in T.items() for k in t["keys"] if k.strip("~")] + [(t["label"], tid) for tid, t in T.items()]


def main(verbose=True):
    rules = {p: type_scores(p) for p, _ in TRAIN}   # rule scores do not depend on the fold: compute once
    folds = [TRAIN[i::FOLDS] for i in range(FOLDS)]
    base = keyword_docs()
    held = []   # (type, rule scores, NB posterior) for every prompt, from a model that never saw it
    for i in range(FOLDS):
        model = D.build_model(base + [x for j, f in enumerate(folds) if j != i for x in f])
        for prompt, tid in folds[i]:
            held.append((tid, rules[prompt], D.nb_probs(model, prompt)))
    results = {}
    for w in WEIGHTS:
        hits = 0
        conf = {"high": [0, 0], "medium": [0, 0], "low": [0, 0]}
        for tid, rule, nb in held:
            got, c, _ = D.decide(rule, nb, w)
            hits += got == tid
            conf[c][0] += got == tid
            conf[c][1] += 1
        results[w] = (hits / len(held), conf)
    rules_only = sum(1 for tid, rule, _ in held if max(rule.values()) > 0 and max(rule, key=lambda x: rule[x]) == tid) / len(held)
    nb_only = sum(1 for tid, _, nb in held if max(nb, key=lambda x: nb[x]) == tid) / len(held)
    best_w = max(WEIGHTS, key=lambda w: (results[w][0], -abs(w - 1.0)))
    final = D.build_model(base + TRAIN)
    final["weight"] = best_w
    final["trained_on"] = {"train_prompts": len(TRAIN), "keyword_docs": len(base), "folds": FOLDS}
    out = D.MODEL_PATH   # corecraft/data/detector.json: where the engine reads it
    out.write_text(json.dumps(final, ensure_ascii=False), encoding="utf-8")
    D._cache.pop("m", None)
    if verbose:
        print("detector (5-fold CV on TRAIN, each prompt scored by a model that never saw it):")
        print("  rules only: %.1f%% | Naive Bayes only: %.1f%%" % (100 * rules_only, 100 * nb_only))
        for w in WEIGHTS:
            acc, conf = results[w]
            print("  fused, NB weight %.2f: %.1f%%   confidence buckets (right/total) %s" % (w, 100 * acc, {k: "%d/%d" % tuple(v) for k, v in conf.items()}))
        print("  chosen weight:", best_w, "| model bytes:", out.stat().st_size)
    return best_w, results


if __name__ == "__main__":
    main()
