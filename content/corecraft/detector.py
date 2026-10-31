"""Business-type detector: keyword rules fused with a small learned Naive Bayes model (stdlib only).

The rules know the taxonomy; the model (corecraft/data/detector.json, trained by training/train_detector.py on labelled prompts and the
keywords themselves) adds word, word-pair and character-trigram evidence, which carries over to Hinglish spellings
("dukaan"/"dukan") and to words no rule lists. When the evidence is thin the answer carries low confidence, and the caller
puts a needs_review note on the page instead of guessing quietly.
"""
import json
import math
import re
from pathlib import Path

from .business_types import T, type_scores

MODEL_PATH = Path(__file__).resolve().parent / "data" / "detector.json"
TOKEN = re.compile(r"[a-zऀ-ॿ0-9]+")
_cache = {}


def features(prompt):
    """Words, word pairs and character trigrams (the last help spelling variants of Roman Hindi)."""
    toks = TOKEN.findall(prompt.lower())
    feats = list(toks)
    feats += [a + "_" + b for a, b in zip(toks, toks[1:])]
    for t in toks:
        if len(t) >= 4:
            p = "#" + t + "#"
            feats += ["c:" + p[i:i + 3] for i in range(len(p) - 2)]
    return feats


def build_model(docs, alpha=0.3):
    """docs: [(prompt, type id)] -> model dict with per-feature class counts."""
    counts, class_tot, class_docs = {}, {}, {}
    for prompt, tid in docs:
        class_docs[tid] = class_docs.get(tid, 0) + 1
        for f in features(prompt):
            counts.setdefault(f, {})
            counts[f][tid] = counts[f].get(tid, 0) + 1
            class_tot[tid] = class_tot.get(tid, 0) + 1
    return {"counts": counts, "class_tot": class_tot, "class_docs": class_docs, "alpha": alpha}


def nb_probs(model, prompt):
    """Posterior over types from the Naive Bayes model (softmax of summed log-likelihoods)."""
    types = list(T)
    V = len(model["counts"]) or 1
    a = model["alpha"]
    total_docs = sum(model["class_docs"].values()) or 1
    feats = features(prompt)
    logp = {}
    for tid in types:
        lp = math.log((model["class_docs"].get(tid, 0) + 1) / (total_docs + len(types)))
        ct = model["class_tot"].get(tid, 0)
        for f in feats:
            c = model["counts"].get(f)
            if c is None:
                continue   # a feature never seen in training says nothing
            lp += math.log((c.get(tid, 0) + a) / (ct + a * V))
        logp[tid] = lp
    m = max(logp.values())
    exp = {t: math.exp((v - m) / max(len(feats) ** 0.5, 1.0)) for t, v in logp.items()}   # flattened so long prompts do not become 100% sure
    z = sum(exp.values())
    return {t: v / z for t, v in exp.items()}


def load():
    if "m" not in _cache:
        _cache["m"] = json.loads(MODEL_PATH.read_text(encoding="utf-8")) if MODEL_PATH.exists() else None
    return _cache["m"]


def fuse(rule, nb, weight):
    top = max(rule.values()) or 1.0
    return {t: min(rule[t] / top, 1.0) * (1.0 if rule[t] > 0 else 0.0) + weight * nb.get(t, 0.0) for t in rule}


def decide(rule, nb, w):
    """Pure decision from precomputed rule scores and NB posteriors -> (type or None, confidence, details)."""
    rmax = max(rule.values())
    fused = fuse(rule, nb, w)
    order = sorted(fused, key=lambda t: (-fused[t], t))
    best, second = order[0], order[1]
    margin = fused[best] - fused[second]
    top_nb = nb[best]
    if rmax <= 0 and top_nb < 0.35:
        return None, "low", {"rule": 0.0, "nb": top_nb}
    if rmax <= 0:
        conf = "low"
    elif rmax >= 2.0 and margin >= 0.25:
        conf = "high"
    elif margin >= 0.12:
        conf = "medium"
    else:
        conf = "low"
    # a guess made from the learned model alone (no keyword hit) is only used for the page when it is strong; otherwise the page is general
    use = rule[best] > 0 or top_nb >= 0.75
    return best, conf, {"rule": rule[best], "nb": top_nb, "margin": round(margin, 3), "runner_up": second, "use": use}


def detect(prompt, model=None, weight=None):
    """-> (type id or None, confidence label, details). Confidence: 'high', 'medium' or 'low'."""
    model = model if model is not None else load()
    rule = type_scores(prompt)
    rmax = max(rule.values())
    if model is None:
        best = max(rule, key=lambda t: rule[t]) if rmax > 0 else None
        srt = sorted(rule.values(), reverse=True)
        conf = "high" if rmax >= 3 and srt[0] - srt[1] >= 1 else ("medium" if rmax > 0 else "low")
        return best, conf, {"rule": rmax}
    return decide(rule, nb_probs(model, prompt), weight if weight is not None else model.get("weight", 1.0))
