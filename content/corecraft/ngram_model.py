"""Trained n-gram text generator (order-2 with backoff). Pure stdlib: json, random, re, hashlib."""
import hashlib
import json
import random
import re
from pathlib import Path

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’&%+-]*|[.,!?;:]")
START, END = "<s>", "</s>"
ORIGINALITY_N = 6
FUNCTION_END = {"a", "an", "the", "and", "or", "of", "to", "in", "on", "with", "for", "your", "our", "you", "we", "is", "are", "that", "at", "by", "from", "as", "it", "its", "their", "but", "can", "will", "this", "be", "into"}
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "model.json"


def tokens(text):
    return TOKEN.findall(text)


def detok(toks):
    out = ""
    for t in toks:
        out += t if (not out or t in ".,!?;:") else " " + t
    return out


def gram_hash(words):
    return hashlib.md5(" ".join(w.lower() for w in words).encode()).hexdigest()[:10]


def sentence_ok_proper(sent):
    """True when the sentence has no mid-sentence capitalised word (brand/proper noun)."""
    ws = tokens(sent)
    return all(not (w[0].isupper() and w != "I") for w in ws[1:] if w[0].isalpha())


def train_chain(texts):
    """texts -> {'o2': {'a|b': {next: n}}, 'n': count}; repeated texts count more."""
    o2 = {}
    for t in texts:
        toks = [START, START] + tokens(t) + [END]
        for i in range(2, len(toks)):
            o2.setdefault(toks[i - 2] + "|" + toks[i - 1], {}).setdefault(toks[i], 0)
            o2[toks[i - 2] + "|" + toks[i - 1]][toks[i]] += 1
    return {"o2": o2, "n": len(texts)}


def _pick(table, rng):
    items = list(table.items())
    total = sum(c for _, c in items)
    r = rng.uniform(0, total)
    for w, c in items:
        r -= c
        if r <= 0:
            return w
    return items[-1][0]


def sample(chain, rng, max_tokens=60):
    """Order-2 only (no backoff): output is stitched from real 3-word overlaps, so it stays locally grammatical."""
    a, b, out = START, START, []
    for _ in range(max_tokens):
        tbl = chain["o2"].get(a + "|" + b)
        if not tbl:
            return None
        nxt = _pick(tbl, rng)
        if nxt == END:
            return out
        out.append(nxt)
        a, b = b, nxt
    return None


class Model:
    def __init__(self, data):
        self.d = data
        self.brands = set(data.get("brands", []))
        self.common = set(data.get("common", []))

    _cache = {}

    @classmethod
    def load(cls, path=MODEL_PATH):
        p = Path(path)
        if not p.exists():
            return None
        key = (str(p), p.stat().st_mtime)
        if key not in cls._cache:
            cls._cache = {key: cls(json.loads(p.read_text(encoding="utf-8")))}
        return cls._cache[key]

    def foreign(self, niche):
        """Words that strongly mark another niche but never this one: used to reject off-topic text."""
        cache = self.__dict__.setdefault("_foreign", {})
        if niche not in cache:
            own = self.d["niches"][niche]["vocab"]
            bad = set()
            for n, nd in self.d["niches"].items():
                if n != niche:
                    top = sorted(nd["vocab"].items(), key=lambda kv: -kv[1])[:80]
                    bad |= {w for w, _ in top if w not in own}
            cache[niche] = bad
        return cache[niche]

    def has(self, niche, slot):
        return slot in self.d["niches"].get(niche, {}).get("slots", {})

    def niche_scores(self, toks):
        s = {}
        for n, nd in self.d["niches"].items():
            w = nd["vocab"]
            s[n] = sum(w.get(t, 0.0) for t in set(toks))
        return s

    def pick_ctas(self, niche, rng, k=2, pool=8):
        """Two distinct CTAs from the most common learned ones for this niche, topped up with CTAs common to other niches."""
        vocab = self.d["niches"][niche]["vocab"]
        known = lambda x: all(w.lower() in self.common or w.lower() in vocab for w in x.split() if w.isalpha())
        ok = lambda x: x.lower() not in ("learn more", "read more") and not any(w.lower() in self.brands for w in x.split())
        top = [x for x in self.top_ctas(niche, 60) if ok(x) and known(x)][:pool]
        if len(top) < pool:
            shared = {}
            for n, nd in self.d["niches"].items():
                for c, v in nd["ctas"].items():
                    if n != niche and ok(c) and all(w.lower() in self.common for w in c.split() if w.isalpha()):
                        shared[c] = shared.get(c, 0) + v
            extra = [c for c, _ in sorted(shared.items(), key=lambda kv: (-kv[1], kv[0])) if c not in top]
            top += extra[:pool - len(top)]
        if len(top) < k:
            return []
        return rng.sample(top, k)

    def top_ctas(self, niche, k=2):
        c = self.d["niches"].get(niche, {}).get("ctas", {})
        return [x for x, _ in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))][:k]

    def _valid(self, text, words, niche, kind, lo, hi):
        if not (lo <= len(words) <= hi):
            return False
        if kind != "heading" and not text.endswith((".", "!")):
            return False
        if words[-1].lower() in FUNCTION_END:
            return False
        low = [w.lower() for w in words]
        if any(low[i] == low[i + 1] for i in range(len(low) - 1)):
            return False
        if len(set(low)) < max(2, len(low) * 0.6):
            return False
        if re.search(r"[.,!?;:]\s*[.,!?;:]", text) or text.count("(") != text.count(")"):
            return False
        grams = self.d["niches"][niche]["grams"]
        gl = set(grams)
        if len(words) >= ORIGINALITY_N:
            for i in range(len(words) - ORIGINALITY_N + 1):
                if gram_hash(words[i:i + ORIGINALITY_N]) in gl:
                    return False
        return True

    def generate(self, niche, slot, rng, lo, hi, kind="sentence", want=(), tries=400, banned=(), strict=False):
        nd = self.d["niches"][niche]
        chain = nd["slots"][slot]
        vocab = nd["vocab"]
        foreign = self.foreign(niche)
        best, best_score = None, -1e9
        found = 0
        for _ in range(tries):
            toks = sample(chain, rng, hi * 2 + 6)
            if not toks:
                continue
            text = detok(toks)
            words = [t for t in toks if t[0].isalnum()]
            if not self._valid(text, words, niche, kind, lo, hi) or text in banned or text.lower() in banned:
                continue
            if any(w.lower() in foreign or w.lower() in self.brands for w in words):
                continue
            if vocab and not any(w.lower() in vocab for w in words):
                continue
            if strict:
                own_top = set(sorted(vocab, key=lambda k: -vocab[k])[:150])
                if any(len(w) > 3 and w.isalpha() and w.lower() not in self.common and w.lower() not in own_top for w in words):
                    continue
            found += 1
            score = sum(vocab.get(w.lower(), 0.0) for w in words) / len(words)
            score += 2.0 * sum(1 for w in words if w.lower() in want)
            score += rng.random() * 0.5
            if score > best_score:
                best, best_score = text, score
            if found >= 25:
                break
        return best
