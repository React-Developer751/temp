"""Learn the fillers for sentence frames from the real-site corpus, per niche:
 - plural nouns (checked to really behave as nouns), scored by how characteristic they are of the niche
 - co-occurrence: which nouns appear together with which prompt words (so "jewellery" pulls in rings, not sweaters)
Frames (grammar) live in corecraft/template_model.py; this script learns what goes in the slots."""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corecraft import ngram_model as nm
import train as tr

DETS = {"a", "an", "the", "your", "our", "every", "each", "any", "all", "more"}
NOUN_PREV = DETS | {"many", "these", "those", "best", "top", "new", "great", "free", "other", "some", "few", "several", "popular", "custom", "fresh", "quality", "favorite", "favourite", "local", "online", "digital", "modern", "classic", "premium", "daily", "weekly", "personal", "professional", "unlimited", "exclusive", "latest", "different", "more", "most"}
PREPS = set("in on for with of to by at from about like into over under as than and or but if so not no is are be was were it its this that these those you we they i he she them us his her their my me up out off per via always never often just also still even only very much ever here there then now soon".split())
BAD_ADJ = re.compile(r"(ing|ly|ness|ment|tion)$")
MASS_PL = re.compile(r"(ss|us|ics|is|news|sales|series)$")
VERBISH = re.compile(r"(ing|ly|ed|ment|tion|ness)$")
BLOCK = set("always needs types nouns tales managers essentials fundamentals foundations pants razors years lives ways reasons values steps matters makes starts answers details releases awards reviews results dimensions wells hills janes dozens millions atlas postgres devops faqs contents sports kids friends moves seekers methods cases issues payments pots tips verbs functions phrases algorithms tags costs shapes areas cities items ideas connections minutes channels models arrays seconds materials flashcards expressions moons disputes limits scales quotes principles notifications subscriptions capabilities terms rights conditions policies cookies settings preferences sources stories updates himalayas hips shoulders legs muscles joints comes runs weeks months thoughts barriers heights dogs strips handles woods walls spaces spans requests logs signals emissions prompts claims demands perspectives fonts hospitals patients franchisees requirements fees factors icons parts levels ages subscribers savings returns dreams favorites favourites notes moments partnerships tables concepts roles taskers sleepers weeds pests risks checks guidelines decisions strategies investments industries treatments challenges opportunities resources processes interactions resolutions permissions evaluations workloads spans ingredients allergens cravings specials contours springs layers handles colors scents slides prerequisites paths patterns structures operations".split())
TOP_PER_NICHE = 90
MIN_COUNT = 4
MAX_SPREAD = 4


def kind_of(w):
    return "PL" if w.endswith("s") and not MASS_PL.search(w) else "SG"


def texts(c):
    return c["heading"] * 2 + c["para"]   # headings carry more weight than body copy


def main():
    corpus = json.loads((ROOT / "data" / "corpus.json").read_text())
    model = json.loads((ROOT / "data" / "model.json").read_text())
    common = set(model["common"])
    brands = set(model["brands"])
    cta_verbs = tr.learn_verbs(corpus)
    N = len(corpus)

    # --- noun-ness: how often does a word follow a determiner/adjective-like word, over the whole corpus?
    total, after_det, before_det = {}, {}, {}
    for c in corpus.values():
        for t in c["heading"] + c["para"]:
            tk = [x.lower() for x in nm.tokens(t)]
            for i, w in enumerate(tk):
                total[w] = total.get(w, 0) + 1
                if i and tk[i - 1] in NOUN_PREV:
                    after_det[w] = after_det.get(w, 0) + 1
                if i + 1 < len(tk) and tk[i + 1] in DETS:
                    before_det[w] = before_det.get(w, 0) + 1
    verbs = {w for w, k in before_det.items() if k >= 12 and w in common and not w.endswith("s")} | (cta_verbs - {"new", "custom", "google", "go", "show"})
    is_noun = lambda w: after_det.get(w, 0) >= 1   # negative test only: adverbs/verbs like "always" never follow a determiner

    # --- per-niche counts of candidate plural nouns
    cnt = {}
    for n, c in corpus.items():
        cnt[n] = {}
        for t in texts(c):
            for tok in nm.tokens(t):
                w = tok.lower()
                if tok[0].isalpha() and w.isalpha() and len(w) >= 4 and kind_of(w) == "PL" and w not in tr.STOP and w not in verbs and not VERBISH.search(w) \
                        and w not in brands and w not in PREPS and w not in BLOCK and is_noun(w):
                    cnt[n][w] = cnt[n].get(w, 0) + 1
    spread = {}
    for n in cnt:
        for w, k in cnt[n].items():
            if k >= MIN_COUNT:
                spread[w] = spread.get(w, 0) + 1

    out = {"verbs": sorted(verbs), "niches": {}}
    for n, c in corpus.items():
        scored = {w: k * math.log(N / spread[w] + 1) for w, k in cnt[n].items() if k >= MIN_COUNT and spread[w] <= MAX_SPREAD}
        top = sorted(scored, key=lambda w: -scored[w])[:TOP_PER_NICHE]
        nouns = set(top)
        # co-occurrence of prompt-like words with those nouns inside the same heading/sentence
        word_freq = {}
        co = {}
        for t in c["heading"] + [s for p in c["para"] for s in re.split(r"(?<=[.!?])\s+", p)]:
            ws = {x.lower() for x in nm.tokens(t) if x[0].isalpha() and x.isalpha() and len(x) >= 4}
            ns = ws & nouns
            for w in ws - tr.STOP:
                word_freq[w] = word_freq.get(w, 0) + 1
                if ns:
                    d = co.setdefault(w, {})
                    for x in ns:
                        if x != w:
                            d[x] = d.get(x, 0) + 1
        cooc = {}
        for w, d in co.items():
            if word_freq[w] >= 3 and w not in nouns:
                best = sorted(((x, k) for x, k in d.items() if k >= 2), key=lambda kv: -kv[1])[:10]
                if best:
                    cooc[w] = dict(best)
        out["niches"][n] = {"PL": {w: round(scored[w], 2) for w in top}, "cooc": cooc}
        print(n, "nouns", len(top), "cooc keys", len(cooc))
        print("   ", top[:45])
    (ROOT / "corecraft" / "data" / "fillers.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
    import train_profiles
    train_profiles.main()
