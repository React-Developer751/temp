"""A small trained niche classifier (multinomial naive Bayes over caption words), stored inside the model file.

It learns from the `niche` label of a {image, caption, niche, mood} manifest. The special label "none" holds captions of things that are
NOT any niche (so the classifier can say "not one of mine"). The studio combines it with the keyword matcher (see match.py) so that a
wrong guess becomes "fallback", not a wrong picture.
"""
import json
import math
import os

from ..learn import caption_words

NONE = "none"
MIN_WORDS = 2
_DEFAULT = None


def features(text):
    """Caption words plus, for Devanagari words, the word without its last character (handles Hindi inflections: दांत / दांतों)."""
    out = []
    from .match import normalise
    for w in caption_words(normalise(text)):
        out.append(w)
        if any("ऀ" <= ch <= "ॿ" for ch in w) and len(w) > 3:
            out.append("~" + w[:-1])
    return out


def build_niche_nb(samples):
    classes = {}
    for s in samples:
        if not s.niche:
            continue
        c = classes.setdefault(s.niche, {"n": 0, "words": {}})
        c["n"] += 1
        for w in set(features(s.caption)):
            c["words"][w] = c["words"].get(w, 0) + 1
    if len([k for k in classes if k != NONE]) < 2:
        return None
    vocab = {w for c in classes.values() for w in c["words"]}
    # how distinctive each word is: the share of its captions that belong to its most common niche (generic words like "clean" or "kids"
    # spread over many niches and get a low purity, so a keyword list cannot make them decisive)
    purity = {}
    for w in vocab:
        counts = [c["words"].get(w, 0) for k, c in classes.items() if k != NONE]
        tot = sum(counts)
        nones = sum(c["words"].get(w, 0) for k, c in classes.items() if k == NONE)
        if tot + nones >= 3:
            purity[w] = [round(max(counts) / float(tot + 3 * nones), 2), tot + nones]       # a use in a "not a niche" caption counts triple
    return {"classes": classes, "vocab": len(vocab), "purity": purity}


def log_scores(nb, text):
    """-> ({niche_or_none: log-probability}, n_known_words), or None when no word of the text was ever seen."""
    if not nb:
        return None
    classes, v = nb["classes"], max(1, nb["vocab"])
    words = list(dict.fromkeys(features(text)))
    known = [w for w in words if any(w in c["words"] for c in classes.values())]
    if not known:
        return None
    logp = {}
    for nid, c in classes.items():
        total = sum(c["words"].values())
        logp[nid] = sum(math.log((c["words"].get(w, 0) + 0.1) / (total + 0.1 * v)) for w in known)
    return logp, len(known)


def posterior(logp):
    top = max(logp.values())
    exp = {k: math.exp(x - top) for k, x in logp.items()}
    z = sum(exp.values())
    return sorted(((e / z, k) for k, e in exp.items()), reverse=True)


def predict(nb, text):
    """-> (niche_id, probability, n_known_words, margin_to_second) or None when no word of the text was ever seen."""
    r = log_scores(nb, text)
    if r is None:
        return None
    ranked = posterior(r[0])
    p1 = ranked[0][0]
    return ranked[0][1], p1, r[1], p1 - (ranked[1][0] if len(ranked) > 1 else 0.0)


def default_nb():
    """The classifier shipped with the package (trained on studio_data/ by train.py, exported with tools/export_niche_nb.py)."""
    global _DEFAULT
    if _DEFAULT is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niche_nb.json")
        try:
            with open(path, encoding="utf-8") as fh:
                _DEFAULT = json.load(fh)
        except (OSError, ValueError):
            _DEFAULT = {}
    return _DEFAULT or None


def as_classifier(model=None):
    """Callable prompt -> log_scores() result. Uses the model's own niche classifier if it has one, else the packaged one."""
    nb = getattr(model, "extras", {}).get("niche_nb") if model is not None else None
    nb = nb or default_nb()
    if not nb:
        return None
    return NicheClassifier(nb)


class NicheClassifier:
    """Callable prompt -> log_scores(); also tells how distinctive a keyword is (`purity`)."""

    def __init__(self, nb):
        self.nb = nb
        self._purity = nb.get("purity", {})

    def __call__(self, prompt):
        return log_scores(self.nb, prompt)

    def purity(self, term):
        """Share of the captions containing this word that belong to its main niche (1.0 when the word is rare or unseen)."""
        e = self._purity.get(term)
        return 1.0 if e is None else e[0]
