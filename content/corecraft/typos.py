"""Typo fixer for English words in a prompt ("resturant", "salun", "bridal makup"). Stdlib difflib against corecraft/data/vocab.json.
Only lowercase words of 4+ letters that the vocabulary does not know are touched, and only when one known word is very close;
names, cities and Hinglish words are left alone. Every change is reported so the page can say what was assumed."""
import difflib
import json
import re
from pathlib import Path

VOCAB_PATH = Path(__file__).resolve().parent / "data" / "vocab.json"
SHORT = {"gim": "gym", "jym": "gym", "salun": "salon", "saloon": "salon", "hotal": "hotel", "bakry": "bakery", "clinc": "clinic", "resturant": "restaurant", "restaurent": "restaurant",
         "restraunt": "restaurant", "resturent": "restaurant", "hospitel": "hospital", "pharmcy": "pharmacy", "phramacy": "pharmacy"}
_cache = {}


def _load():
    if "v" not in _cache:
        try:
            words = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            words = {}
        by = {}
        for w in words:
            by.setdefault((w[0], len(w)), []).append(w)
        _cache["v"] = (words, by)
    return _cache["v"]


def _protected():
    from .facts import ALL_CITIES, FILLER_WORDS
    return ALL_CITIES | FILLER_WORDS | {"hai", "hain", "kiya", "karo", "karna", "chalata", "chalati", "chalate", "hoon", "hun", "bhi", "sabhi", "yahan", "wahan", "dukaan", "dukan", "kaam", "naam"}


def _dist(a, b):
    """Edit distance counting a swap of two neighbouring letters as one edit."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[len(a)][len(b)]


def _inflection_of_known(w, words):
    for suf in ("s", "es", "ed", "ing", "ly", "er", "ers", "ment", "ments", "ist", "ists"):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and (w[:-len(suf)] in words or w[:-len(suf)] + "e" in words):
            return True
    return False


def _keywords():
    """Words that define a kind of business ("restaurant", "dental", "salon"): a typo in one of these changes the whole page, so it is corrected."""
    if "k" not in _cache:
        from .business_types import T
        out = set()
        for t in T.values():
            for k in list(t["keys"]) + [t["label"]]:
                for w in re.findall(r"[a-z]{4,20}", k.lower().replace("~", "")):
                    out.add(w)
        _cache["k"] = out - {"shop", "store", "service", "services", "centre", "center", "studio", "company", "online", "home", "best"}
    return _cache["k"]


def scope_words(tid, text=""):
    """The vocabulary of one kind of business (its keywords, typical offerings, sub-niche triggers and dish/service names): inside it a
    one-letter slip in an unknown word is safe to fix, because a close word of the same trade is by far the likelier meaning."""
    from .profiles import PROFILES, TYPE_KIND, pick_profile
    profile = pick_profile(tid, text, []) if text else None   # the sub-niche, when the text says it: a bakery's scope does not hold street-food names
    if ("s", tid, profile) not in _cache:
        from .business_types import T
        from . import lexicon
        kind, out, texts = TYPE_KIND.get(tid), set(), []
        t = T.get(tid)
        if t:
            texts += list(t["keys"]) + list(t.get("offers") or []) + [t["label"]]
        for name, p in PROFILES.items():
            if p.get("kind") == kind and (name == profile if kind == "food" else True):   # food names cross cuisines ("katli" is not "kathi"), so a food scope is only the sub-niche's own
                texts.append(p.get("triggers", ""))
                texts += list(lexicon.LEX.get(name, {}))
        for x in texts:
            out.update(re.findall(r"[a-z]{4,20}", x.lower().replace("~", "")))
        _cache[("s", tid, profile)] = out
    return _cache[("s", tid, profile)]


def fix(text, scope=None):
    """-> (text with business-type words corrected, [(wrong, right)], [(wrong, maybe)]).
    Only words that name the kind of business are rewritten. Any other unknown word is left exactly as typed (it may be a real name or dish);
    a close known word is offered as a hint instead."""
    words, by = _load()
    if not words or any("\u0900" <= ch <= "\u097f" for ch in text):
        return text, [], []
    prot, keys = _protected(), _keywords()
    changes, hints = [], []

    def one(m):
        w = m.group(0)
        if w in words or w in prot or _inflection_of_known(w, words):
            return w
        if w in SHORT:
            changes.append((w, SHORT[w]))
            return SHORT[w]
        if len(w) < 5:
            return w
        limit = 1 if len(w) <= 8 else 2   # one slip; two only in long words
        pool = [c for n in (len(w) - 1, len(w), len(w) + 1) for c in by.get((w[0], n), [])]
        near = sorted(((c, _dist(w, c)) for c in pool if _dist(w, c) <= limit), key=lambda cd: (cd[1], cd[0] not in (scope or ()), -words[cd[0]]))
        if not near:
            return w
        kw = [(c, d) for c, d in near if c in keys or (scope and c in scope)]
        if kw:
            changes.append((w, kw[0][0]))
            return kw[0][0]
        if near[0][1] == 1 and len(w) >= 6 and words[near[0][0]] >= 50:
            hints.append((w, near[0][0]))
        return w

    out = re.sub(r"(?<![A-Za-z'@.\-/])[a-z]{3,20}(?![A-Za-z'@.\-/])", one, text)   # lowercase words only: names, emails and URLs are not touched
    return out, changes, hints
