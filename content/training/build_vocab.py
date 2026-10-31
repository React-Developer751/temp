"""Build corecraft/data/vocab.json: the English words the typo fixer knows (corpus words seen 3+ times, plus every business-type keyword and lexicon word).
Run: python3 training/build_vocab.py"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from corecraft.business_types import T   # noqa: E402
from corecraft import lexicon   # noqa: E402

WORD = re.compile(r"[a-z]{3,20}")


def strings(x, out):
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            out.append(k) if isinstance(k, str) else None
            strings(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            strings(v, out)


def main():
    cnt = Counter()
    for name in ("corpus.json", "corpus_small.json", "corpus_v2.json", "profile_corpus.json"):
        out = []
        strings(json.loads((ROOT / "data" / name).read_text(encoding="utf-8")), out)
        for t in out:
            cnt.update(WORD.findall(t.lower()))
    words = {w: c for w, c in cnt.items() if c >= 3}
    known = []
    for t in T.values():
        strings([t["keys"], t["label"], t["offers"]], known)
    strings(lexicon.LEX, known)
    for t in known:
        for w in WORD.findall(t.lower().replace("~", "")):
            words[w] = max(words.get(w, 0), 50)
    out = ROOT / "corecraft" / "data" / "vocab.json"
    out.write_text(json.dumps(words, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print("vocab words:", len(words), "| bytes:", out.stat().st_size)
    # words that usually END a phrase in real site text ("dog FOOD,", "aquarium FISH"), for cutting a list typed without commas
    seen, ended = Counter(), Counter()
    for name in ("corpus.json", "corpus_small.json", "corpus_v2.json", "profile_corpus.json"):
        texts = []
        strings(json.loads((ROOT / "data" / name).read_text(encoding="utf-8")), texts)
        for t in texts:
            toks = re.findall(r"[a-z]{3,20}|[,.;:|/\n&]", t.lower())
            for i, w in enumerate(toks):
                if w in ",.;:|/\n&":
                    continue
                seen[w] += 1
                if i + 1 == len(toks) or toks[i + 1] in ",.;:|/\n&":
                    ended[w] += 1
    heads = sorted(w for w, c in seen.items() if c >= 8 and ended[w] / c >= 0.5 and w not in ("and", "the", "for", "with", "our", "your", "you", "all", "new", "more", "best", "free", "now", "here", "that", "this"))
    hp = ROOT / "data" / "heads.json"
    hp.write_text(json.dumps(heads, separators=(",", ":")), encoding="utf-8")
    print("phrase-ending words:", len(heads), "| bytes:", hp.stat().st_size)


if __name__ == "__main__":
    main()
