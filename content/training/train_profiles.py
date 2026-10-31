"""Learn the vocabulary of every sub-niche (profile) from public pages and report how well it identifies held-out sites.

Reads data/profile_corpus.json (training sites) and data/profile_holdout.json (sites that are NEVER trained on), writes
corecraft/data/profile_vocab.json. The hold-out texts only appear in the evaluation at the bottom.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from corecraft.profiles import PROFILES   # noqa: E402

STOP = set("""a an the and or of to in on with for your our you we is are that at by from as it its their but can will this be into i not all any more most how what who why when where
have has had was were been about they them them his her him she he us out up over under also just only very new best get see use find make take per via one two three more less
please click here home page menu contact privacy terms cookies login sign shop order online delivery store service services products product view read learn buy cart""".split())
WORD = re.compile(r"[a-z]{3,}")


PROPER = set()   # words that are almost always capitalised inside a sentence: names of brands, people and places
CITY = set()


def find_proper(corpus):
    from corecraft.facts import ALL_CITIES
    cap, low = {}, {}
    for entry in corpus.values():
        for t in entry.get("heading", []) + entry.get("para", []) + entry.get("title", []):
            ws = re.findall(r"[A-Za-z]{3,}", t)
            for i, w in enumerate(ws):
                if i == 0:
                    continue
                (cap if w[0].isupper() else low)[w.lower()] = (cap if w[0].isupper() else low).get(w.lower(), 0) + 1
    PROPER.clear()
    PROPER.update(w for w, c in cap.items() if c >= 2 and c > 3 * low.get(w, 0))
    CITY.clear()
    CITY.update(c for c in ALL_CITIES if c.isascii())


def tokens(text):
    return [w for w in WORD.findall(text.lower()) if w not in STOP and w not in PROPER and w not in CITY]


def blob(entry):
    return " ".join(entry.get("heading", []) + entry.get("para", []) + entry.get("title", []))


def build_vocab(corpus, top=120, min_count=3):
    counts = {p: {} for p in corpus}
    for p, entry in corpus.items():
        for w in tokens(blob(entry)):
            counts[p][w] = counts[p].get(w, 0) + 1
    nprof = len(counts)
    df = {}
    for p in counts:
        for w, c in counts[p].items():
            if c >= min_count:
                df[w] = df.get(w, 0) + 1
    vocab = {}
    for p, c in counts.items():
        total = sum(c.values()) or 1
        sc = {w: (n / total) * math.log(1 + nprof / df[w]) for w, n in c.items() if n >= min_count and w in df}
        best = sorted(sc.items(), key=lambda kv: -kv[1])[:top]
        norm = best[0][1] if best else 1.0
        vocab[p] = {w: round(v / norm, 4) for w, v in best}
    return vocab


def classify(text, vocab, use_triggers=True, use_learned=True):
    ws = tokens(text)
    wset = set(ws)
    scores = {}
    for p in vocab:
        s = 0.0
        if use_triggers and p in PROFILES:
            s += 1.5 * len(wset & set(PROFILES[p]["triggers"].split()))
        if use_learned:
            s += min(3.0, sum(vocab[p].get(w, 0.0) for w in wset) * 4.0)
        scores[p] = s
    best = max(scores, key=lambda p: (scores[p], p))
    return best if scores[best] > 0 else None


def main(verbose=True):
    corpus = json.loads((ROOT / "data" / "profile_corpus.json").read_text())
    holdout_path = ROOT / "data" / "profile_holdout.json"
    holdout = json.loads(holdout_path.read_text()) if holdout_path.exists() else {}   # scoring only: never read during training
    find_proper(corpus)
    vocab = build_vocab({p: e for p, e in corpus.items() if blob(e).strip()})
    (ROOT / "corecraft" / "data" / "profile_vocab.json").write_text(json.dumps(vocab, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print("profile vocabulary learned from %d training profiles (%d sites)" % (len(vocab), sum(len(e.get("sites", [])) for e in corpus.values())))
        for p in ("italian", "south_indian", "dental", "yoga", "kurti"):
            if p in vocab:
                print("  %-13s top words: %s" % (p, ", ".join(list(vocab[p])[:10])))
    rows = [(p, blob(e)) for p, e in holdout.items() if len(blob(e).split()) >= 30]
    if verbose and rows:
        res = {}
        for name, kw in (("trigger words only", dict(use_triggers=True, use_learned=False)), ("learned vocabulary only", dict(use_triggers=False, use_learned=True)), ("both", dict())):
            ok = sum(1 for p, t in rows if classify(t, vocab, **kw) == p)
            res[name] = "%d/%d" % (ok, len(rows))
        print("  sub-niche identification on %d held-out profiles (sites never trained on): %s" % (len(rows), res))
    return vocab


if __name__ == "__main__":
    main()
