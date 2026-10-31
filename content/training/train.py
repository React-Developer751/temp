"""Train the Content AI: learns n-gram chains + niche vocabulary + CTA stats from data/corpus.json."""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corecraft import ngram_model as nm

STOP = set("a an the and or of to in on with for your our you we is are that at by from as it its their but can will this be into i not all any more most how what who why when where".split())
NAV = re.compile(r"log ?in|sign ?(in|up)|cart|account|search|menu|skip|cookie|privacy|terms|careers|language|close|back|next|previous|accept|reject|english|español|\d|statement|investment|franchise|suppliers", re.I)
ASSET = re.compile(r"https?|www|\.com|@|app store|google play|download|password|click here|login|©|\d", re.I)
NICHE_WEIGHT = 4   # a niche's own examples count this many times in its chain
MIN_VERB_SUPPORT = 15
MIN_VERB_NICHES = 5


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def n_words(s):
    return len([t for t in nm.tokens(s) if t[0].isalnum()])


def camel(s):
    return bool(re.search(r"[a-z][A-Z]", s))


def good_sentence(s, lo, hi):
    return lo <= n_words(s) <= hi and s[0].isupper() and s.endswith((".", "!")) and not ASSET.search(s) \
        and nm.sentence_ok_proper(s) and "?" not in s and not s.isupper() and not camel(s)


def good_heading(h, lo, hi):
    return lo <= n_words(h) <= hi and "?" not in h and not h.isupper() and not ASSET.search(h) and not h.endswith(":") and not camel(h)


def slots_for(c, freq, ctaset):
    s = {"title": [], "feat_title": [], "sentence": []}
    rare = lambda x: any(freq.get(w.lower(), 0) < 3 and len(w) >= 4 and w.isalpha() for w in nm.tokens(x))
    for h in c["heading"]:
        h = h.strip(" .")
        if h.lower() in ctaset or rare(h):
            continue
        if good_heading(h, 2, 7):
            s["title"].append(h)
        if good_heading(h, 2, 4):
            s["feat_title"].append(h)
    for p in c["para"]:
        for x in sentences(p):
            if good_sentence(x, 5, 20) and not rare(x):
                s["sentence"].append(x)
    return {k: list(dict.fromkeys(v)) for k, v in s.items()}


def learn_verbs(corpus):
    """Imperative CTA verbs = first words seen in many CTAs across at least 3 niches."""
    cnt, spread, anywhere = {}, {}, {}
    for n, c in corpus.items():
        for t in c["cta"]:
            ws = t.split()
            for w in ws:
                anywhere[w.lower()] = anywhere.get(w.lower(), 0) + 1
            if 2 <= len(ws) <= 4 and not NAV.search(t):
                w = ws[0].lower()
                cnt[w] = cnt.get(w, 0) + 1
                spread.setdefault(w, set()).add(n)
    # a verb opens CTAs (high first/anywhere ratio); nouns like "data" or "business" appear in other positions too
    return {w for w, k in cnt.items() if k >= MIN_VERB_SUPPORT and len(spread[w]) >= MIN_VERB_NICHES and w not in STOP and k / anywhere[w] >= 0.7}


def main():
    corpus = json.loads((ROOT / "data" / "corpus.json").read_text())
    freq = {}
    for c in corpus.values():
        for t in nm.tokens(" ".join(c["heading"] + c["para"])):
            freq[t.lower()] = freq.get(t.lower(), 0) + 1
    ctaset = {t.lower().strip(" .") for c in corpus.values() for t in c["cta"]}
    per = {n: slots_for(c, freq, ctaset) for n, c in corpus.items()}
    verbs = learn_verbs(corpus)
    print("learned CTA verbs:", sorted(verbs))
    doc_freq, tot = {}, {}
    for n, c in corpus.items():
        tot[n] = {}
        for t in nm.tokens(" ".join(c["heading"] + c["para"])):
            w = t.lower()
            if t[0].isalpha() and w not in STOP and len(w) > 2:
                tot[n][w] = tot[n].get(w, 0) + 1
        for w in tot[n]:
            doc_freq[w] = doc_freq.get(w, 0) + 1
    N = len(corpus)
    niches = {}
    for n, c in corpus.items():
        size = sum(tot[n].values()) or 1
        vocab = {w: round(cnt / size * 100 * math.log(N / doc_freq[w]), 4) for w, cnt in tot[n].items() if cnt >= 3 and doc_freq[w] < N}
        vocab = dict(sorted(vocab.items(), key=lambda kv: -kv[1])[:400])
        ctas = {}
        for t in c["cta"]:
            t = t.strip(" .")
            ws = t.split()
            if 2 <= len(ws) <= 4 and ws[:len(ws) // 2] != ws[len(ws) // 2:] and ws[0].lower() in verbs and not NAV.search(t) and not camel(t):
                k = " ".join(w.capitalize() if w.lower() not in STOP or i == 0 else w.lower() for i, w in enumerate(ws))
                ctas[k] = ctas.get(k, 0) + 1
        ctas = {k: v for k, v in ctas.items() if v >= 2 and "|" not in k}   # reused phrases only, not one-off product names
        slots, grams = {}, set()
        for slot in ("title", "feat_title", "sentence"):
            texts = []
            for m, sl in per.items():
                texts += sl[slot] * (NICHE_WEIGHT if m == n else 1)
            slots[slot] = nm.train_chain(texts)
            for tx in per[n][slot]:
                ws = [t for t in nm.tokens(tx) if t[0].isalnum()]
                for i in range(len(ws) - nm.ORIGINALITY_N + 1):
                    grams.add(nm.gram_hash(ws[i:i + nm.ORIGINALITY_N]))
        # originality guard must cover every niche's text, since chains pool them
        for m, sl in per.items():
            for slot, texts in sl.items():
                for tx in texts:
                    ws = [t for t in nm.tokens(tx) if t[0].isalnum()]
                    for i in range(len(ws) - nm.ORIGINALITY_N + 1):
                        grams.add(nm.gram_hash(ws[i:i + nm.ORIGINALITY_N]))
        niches[n] = {"vocab": vocab, "ctas": ctas, "slots": slots, "grams": sorted(grams), "sizes": {k: len(v) for k, v in per[n].items()}}
        print(n, niches[n]["sizes"], "ctas", len(ctas), "top", sorted(ctas, key=lambda k: -ctas[k])[:5])
    from sources import SOURCES
    from fetch_corpus import brand_of
    brands = sorted({brand_of(u) for urls in SOURCES.values() for u in urls if len(brand_of(u)) >= 4})
    out = ROOT / "data" / "model.json"
    out.write_text(json.dumps({"niches": niches, "brands": brands, "common": sorted(w for w, k in doc_freq.items() if k >= 3), "version": 4}, ensure_ascii=False), encoding="utf-8")
    print("model.json bytes:", out.stat().st_size)


def train_detector_and_report():
    """Also (re)train the business-type detector and print its accuracy before and after."""
    import json
    sys.path.insert(0, str(ROOT / "training"))
    import train_detector
    from corecraft import detector
    from labelled import HOLDOUT, TRAIN
    train_detector.main()
    base = json.loads((ROOT / "data" / "baseline_detection.json").read_text())
    for name, rows in (("TRAIN", TRAIN), ("HOLDOUT", HOLDOUT)):
        ok = sum(detector.detect(p)[0] == t for p, t in rows)
        b = base[name.lower()]
        print("  %-8s business-type accuracy: before %d/%d = %.1f%% -> after %d/%d = %.1f%%" % (name, b[0], b[1], 100 * b[0] / b[1], ok, len(rows), 100 * ok / len(rows)))


if __name__ == "__main__":
    main()
    train_detector_and_report()
