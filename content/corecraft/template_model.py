"""Frame-based copy generator.

Frames are hand-written grammar: a few shared ones plus a set written for each niche (template_data.py).
The nouns that fill them come from a hand-curated taxonomy per niche, ranked by how characteristic each noun is
of the niche in the real-website crawl (corecraft/data/fillers.json, built by training/train_templates.py). Prompt words
steer the choice through sub-topics ("jewellery" -> rings, necklaces) and corpus co-occurrence.

One PageContext is shared by every slot of a page, so a noun is not reused until the pool is exhausted.
"""
import json
import re
from pathlib import Path

from . import kind_content   # noqa: F401  (registers the care/pro/hosting/org frame families)
from .kind_content import ANY
from .template_data import NICHE, SUBTOPICS

FILLERS_PATH = Path(__file__).resolve().parent / "data" / "fillers.json"
MIN_SUB_POOL = 26
LEAN_BELOW = 20
NICHE_FRAME_SHARE = 0.7
SERVICE_KINDS = {"care", "pro", "hosting", "org", "business"}   # share of slots written with a frame made for the niche; the rest use shared frames

GENERIC = {
    "hero": ["Where {a} come first", "Great {a}, every day", "Good {a} start here", "Built around your {a}", "Better {a} start here", "Your {a}, your way", "The home of great {a}", "Where {a} meet {b}"],
    "tagline": [
        "{A}, {b}, and everything in between.", "All your {a} in one place.", "Better {a}, made simple.", "Where great {a} come together.",
        "Discover {a} you will love.", "Everything you need, from {a} to {b}.", "Thoughtful {a} and honest {b}.", "From {a} to {b}, done properly.",
        "Your go-to place for {a} and {b}.", "Quality {a}, delivered with care.", "{A} and {b}, all under one roof.", "More {a}, less hassle.", "Simple {a} for everyday life.",
    ],
    "feature": [
        "Explore our {a} and find what fits you.", "Thoughtful {a}, made with care.", "Quality {a} you can count on.", "Hand-picked {a} for every occasion.",
        "Everything about {a}, in plain language.", "We put {a} first, every single time.", "Learn more about our {a} whenever you like.",
        "Reliable {a} with real support behind them.", "Our {a} are chosen with care and checked twice.", "See how our {a} can help with your {b}.", "Made to make your {a} a little easier.",
    ],
    "open": [
        "We bring {a}, {b}, and {c} together in one place.", "From {a} to {b}, we care about the details.", "Our {a} are made with care and our {b} are built to last.",
        "People come to us for {a}, and stay for the {b}.", "We started with a simple idea: better {a} for everyone.", "{A}, {b}, and {c} are at the heart of what we do.",
    ],
    "close": [
        "Every detail is built to make your {d} simpler and better.", "Our approach to {c} is simple: listen first, then do the work properly.",
        "Ask us anything about {d}; we are always happy to help.",
        "That is why so many people trust us with their {c}.", "We stand behind every one of our {d}.",
    ],
}
FOCUS_HERO = ["Your {a}, our passion", "Made around {a}", "All about {a}"]
NOUN_SLOT = re.compile(r"\{([a-dA-D])\}")
ADJ_SLOT = re.compile(r"\{([jJ])\}")


# generic nouns that read fine as a feature title but poorly inside a headline ("Friendly experts for packages")
WEAK = set("packages plans reviews options follow-ups solutions support quotes bookings appointments upgrades estimates assessments consultations programs sessions".split())
PLACE_LINES = ["Serving {p} and nearby areas.", "Proudly based in {p}.", "Find us in {p}.", "Your local team in {p}."]


def cap(w):
    """Capitalise the first letter only, so acronyms and typed casing survive ("GST filing" -> "GST filing")."""
    return w[:1].upper() + w[1:]


def title(w):
    return " ".join(x if x.isupper() else cap(x) for x in w.split())


class PageContext:
    """Remembers which nouns a page already used so slots do not repeat them.
    pool: offerings of the business type (overrides the niche pool); items: phrases the user typed; place: city."""

    def __init__(self, pool=None, items=(), place=None, strict=False, lang=None, hero_items=None):
        self.used = set()
        gone = [i.lower() for i in items]
        # drop offerings the user already named (a typed "teeth whitening" makes "whitening" redundant)
        keep = [w for w in pool if not any(w.rstrip("s") in g or g in w for g in gone)] if pool else None
        if keep:   # near-duplicates ("classes" / "theory classes") would read as repetition: one entry per head noun
            seen, uniq = set(), []
            for w in keep:
                if w.split()[-1] not in seen:
                    seen.add(w.split()[-1])
                    uniq.append(w)
            keep = uniq
        self.pool = keep
        self.items = list(items)
        self.hero_items = list(hero_items) if hero_items else None   # headline phrases when some items are neutral fillers
        self.used_items = set()   # items already named in a headline, so each slot mentions a different one
        self.place = place
        lang = lang or {}
        self.any = lang.get("ANY", ANY)   # frames for the user's own phrases, in the page language
        self.place_lines = lang.get("PLACE_LINES", PLACE_LINES)
        self.place_sentence = lang.get("PLACE_SENTENCE", " We are based in %s and happy to help.")
        self.strict = strict and len(items) >= 1   # strict: write only about the user's own phrases, never typical offerings
        self.lean = bool(self.pool) and len(self.pool) < LEAN_BELOW   # small noun pool: use frames that need fewer nouns


class TemplateModel:
    def __init__(self, data):
        self.d = data
        self._cache = {}

    @classmethod
    def load(cls, path=FILLERS_PATH):
        p = Path(path)
        return cls(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None

    # ---- lexicon -------------------------------------------------------------------------------
    def _rank(self, niche, words):
        score = self.d["niches"].get(niche, {}).get("PL", {})
        order = {w: i for i, w in enumerate(words)}
        return sorted(words, key=lambda w: (-score.get(w, 0), order[w]))   # crawl-characteristic nouns first

    def main(self, niche):
        if ("main", niche) not in self._cache:
            words = list(dict.fromkeys(NICHE[niche]["main"])) if niche in NICHE else []
            words = list(dict.fromkeys(words + [w for _, nouns in SUBTOPICS.get(niche, []) for w in nouns]))   # sub-topic nouns are valid page nouns
            self._cache[("main", niche)] = self._rank(niche, words)
        return self._cache[("main", niche)]

    def nouns(self, niche):
        return self.main(niche) + [w for w in NICHE.get(niche, {}).get("extra", []) if w not in self.main(niche)]

    def usable(self, niche, minimum=20):
        return niche in NICHE and (len(self.nouns(niche)) >= minimum or not NICHE[niche]["main"])

    def sub(self, niche, want):
        """Nouns for the sub-topic the prompt names ("jewellery" -> rings, necklaces ...), else []."""
        out = []
        for triggers, nouns in SUBTOPICS.get(niche, []):
            if any(k.startswith(t) for k in want for t in triggers):
                out += [w for w in nouns if w not in out]
        return out

    def focus(self, niche, want):
        """Prompt words that are themselves nouns of this niche (e.g. 'coffee' for a cafe), in prompt order."""
        allowed = set(self.nouns(niche))
        return [w for w in want if w.isalpha() and len(w) >= 4 and (w in allowed or w + "s" in allowed)]

    # ---- picking -------------------------------------------------------------------------------
    def _take(self, niche, rng, ctx, k, sub, main_only=False, strong=False):
        pool = ctx.pool or (self.main(niche) if main_only else self.nouns(niche))
        if strong:
            keep = [w for w in pool if w not in WEAK]
            pool = keep if len(keep) >= max(k, 6) else pool
        if sub and not ctx.pool:   # a sub-topic was named: nouns that belong only to *other* sub-topics stay off the page
            other = {w for _, nouns in SUBTOPICS.get(niche, []) for w in nouns} - set(sub)
            kept = [w for w in pool if w not in other]
            if len(kept) >= MIN_SUB_POOL:   # small niches keep their full pool, otherwise nouns would repeat
                pool = kept
        fresh = [w for w in pool if w not in ctx.used]
        if len(fresh) < k:
            ctx.used.clear()
            fresh = list(pool)
        if len(fresh) < k:   # a very small pool: cycle through it rather than fail
            return (fresh * k)[:k]
        out = []
        sub_fresh = [w for w in sub if w in fresh]
        while len(out) < k and sub_fresh:
            w = rng.choice(sub_fresh)
            out.append(w)
            sub_fresh.remove(w)
        while len(out) < k:
            cand = [w for w in fresh if w not in out]
            out.append(rng.choices(cand, [1.0 / (1 + i / 10) for i in range(len(cand))])[0])
        ctx.used.update(out)
        return out

    def _adjs(self, niche, rng, n):
        adj = list(NICHE[niche]["adj"])
        rng.shuffle(adj)
        return (adj * 2)[:n]

    @staticmethod
    def _letters(frame):
        return len({m.lower() for m in NOUN_SLOT.findall(frame)})

    def _frame(self, niche, rng, kind, ctx=None):
        niche_frames, shared = NICHE[niche][kind], GENERIC[kind]
        if ctx is not None and ctx.lean:   # small pool: prefer frames that use one noun, so nouns are not repeated
            niche_frames = [f for f in niche_frames if self._letters(f) <= 1] or niche_frames
            shared = [f for f in shared if self._letters(f) <= 1] or shared
        share = 0.97 if niche in SERVICE_KINDS and kind in ("hero", "tagline") else NICHE_FRAME_SHARE   # shared product-style frames ("The home of great check-ups") do not suit services
        if rng.random() < share:
            return rng.choice(niche_frames), True
        return rng.choice(shared), False

    def _fill(self, frame, niche, rng, ctx, sub, own):
        letters = sorted({m.lower() for m in NOUN_SLOT.findall(frame)})
        ns = self._take(niche, rng, ctx, len(letters), sub, main_only=own, strong=True) if letters else []
        m = dict(zip(letters, ns))
        adjs = iter(self._adjs(niche, rng, 4))
        frame = ADJ_SLOT.sub(lambda mo: "{%s}" % ("ADJ_U" if mo.group(1) == "J" else "ADJ_L"), frame)
        vals = {**m, **{l.upper(): w.capitalize() for l, w in m.items()}}
        out = frame
        for key in ("ADJ_U", "ADJ_L"):
            while "{%s}" % key in out:
                a = next(adjs)
                out = out.replace("{%s}" % key, a.capitalize() if key == "ADJ_U" else a, 1)
        return out.format(**vals)

    def _fill_any(self, frame, niche, rng, ctx, items):
        """Fill a frame with the user's own phrases; letters beyond the phrases given come from the type's offerings."""
        letters = sorted({m.lower() for m in NOUN_SLOT.findall(frame)})
        words = list(items[:len(letters)])
        if len(words) < len(letters) and ctx.strict:
            words += [w for w in (ctx.items * 3) if w not in words][:len(letters) - len(words)] or ctx.items[:1] * (len(letters) - len(words))
        elif len(words) < len(letters):
            words += self._take(niche, rng, ctx, len(letters) - len(words), [], main_only=True, strong=True)
        m = dict(zip(letters, words))
        return frame.format(**{**m, **{l.upper(): cap(w) for l, w in m.items()}})

    def _any_frames(self, kind, n_items, ctx):
        return [f for f in ctx.any[kind] if len({m.lower() for m in NOUN_SLOT.findall(f)}) <= max(1, n_items)] or ctx.any[kind]

    # ---- slots ---------------------------------------------------------------------------------
    def hero(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        src = ctx.hero_items or ctx.items
        fresh = [i for i in src if i not in ctx.used_items] or (src if ctx.strict else [])
        if fresh and (ctx.strict or rng.random() < 0.8):
            item = rng.choice(fresh)
            ctx.used_items.add(item)
            return self._fill_any(rng.choice(self._any_frames("hero", 1, ctx)), niche, rng, ctx, [item])
        f = [] if ctx.pool else self.focus(niche, want)
        if f and rng.random() < 0.75:
            w = rng.choice(f)   # f keeps prompt order, so the same seed always gives the same page
            ctx.used.update({w, w + "s"})
            return rng.choice(FOCUS_HERO).format(a=w)
        frame, own = self._frame(niche, rng, "hero", ctx)
        return self._fill(frame, niche, rng, ctx, self.sub(niche, want), own)

    def tagline(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        fresh = [i for i in ctx.items if i not in ctx.used_items]
        if ctx.strict:
            pool_items = fresh if len(fresh) >= 2 else ctx.items
            frame = rng.choice(self._any_frames("tagline", len(pool_items), ctx))
            need = len({m.lower() for m in NOUN_SLOT.findall(frame)})
            pick = rng.sample(pool_items, min(need, len(pool_items)))
            ctx.used_items.update(pick)
            return self._fill_any(frame, niche, rng, ctx, pick)
        if len(fresh) >= 2 and rng.random() < 0.6:
            pair = rng.sample(fresh, 2)
            ctx.used_items.update(pair)
            return self._fill_any(rng.choice(self._any_frames("tagline", 2, ctx)), niche, rng, ctx, pair)
        frame, own = self._frame(niche, rng, "tagline", ctx)
        return self._fill(frame, niche, rng, ctx, self.sub(niche, want), own)

    def about(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        sub = self.sub(niche, want)
        lim = (lambda fs, n: ([f for f in fs if self._letters(f) <= n] if len([f for f in fs if self._letters(f) <= n]) >= 2 else fs)) if ctx.lean else (lambda fs, n: fs)
        opens = rng.sample(lim(NICHE[niche]["open"], 2), 2) if rng.random() < NICHE_FRAME_SHARE else rng.sample(lim(GENERIC["open"], 2), 2)
        closes = rng.sample(lim(NICHE[niche]["close"], 1), 2) if rng.random() < NICHE_FRAME_SHARE else rng.sample(lim(GENERIC["close"], 1), 2)
        paras, paras_close, used_open, para_items = [], [], [], set()
        for i, (op, cl) in enumerate(zip(opens, closes)):
            if (i == 0 or ctx.strict) and ctx.items:   # first paragraph (all of them in strict mode) is about what the user said they do
                op = rng.choice([f for f in self._any_frames("open", len(ctx.items), ctx) if f not in used_open] or self._any_frames("open", len(ctx.items), ctx))
                used_open.append(op)
                taken = set(closes) | set(paras_close)
                cl = rng.choice([c for c in ctx.any["close"] if c not in taken] or ctx.any["close"])
                paras_close.append(cl)
                letters = len({m.lower() for m in NOUN_SLOT.findall(op)})
                fresh = [i for i in ctx.items if i not in ctx.used_items and i not in para_items] or [i for i in ctx.items if i not in para_items] or ctx.items
                pick = rng.sample(fresh, min(letters, len(fresh)))
                para_items.update(pick)
                text = self._fill_any(op, niche, rng, ctx, pick)
                paras.append(text + " " + cl)
                continue
            letters = sorted({m.lower() for m in NOUN_SLOT.findall(op + " " + cl)})   # take only what the two frames use, one noun per letter
            nouns = self._take(niche, rng, ctx, len(letters), sub, main_only=True, strong=True) if letters else []
            adjs = self._adjs(niche, rng, 2)
            vals = {**dict(zip(letters, nouns)), **{l.upper(): w.capitalize() for l, w in zip(letters, nouns)}}
            text = []
            for fr in (op, cl):
                fr = fr.replace("{J}", adjs[0].capitalize()).replace("{j}", adjs[1])
                text.append(fr.format(**vals))
            paras.append(" ".join(text))
        if ctx.place:
            paras[-1] += ctx.place_sentence % ctx.place
        return paras

    def features(self, niche, rng, count=6, want=(), ctx=None):
        ctx = ctx or PageContext()
        sub = self.sub(niche, want)
        feats = []
        item_frames = rng.sample(ctx.any["feature"], len(ctx.any["feature"]))
        for i, item in enumerate(ctx.items[:count]):   # what the user said they offer comes first
            feats.append({"title": title(item), "text": item_frames[i % len(item_frames)].format(a=item, A=cap(item))})
        rest = count - len(feats)
        heads = self._take(niche, rng, ctx, rest, sub, main_only=True, strong=True) if rest else []
        nb = (lambda fs: [f for f in fs if "{b}" not in f] or fs) if ctx.lean else (lambda fs: fs)
        own = rng.sample(nb(NICHE[niche]["feature"]), min(max(rest, 1), len(nb(NICHE[niche]["feature"]))))
        gen = rng.sample(nb(GENERIC["feature"]), min(max(rest, 1), len(nb(GENERIC["feature"]))))
        for i, h in enumerate(heads):
            frame = own[i % len(own)] if rng.random() < NICHE_FRAME_SHARE else gen[i % len(gen)]
            adjs = self._adjs(niche, rng, 1)
            frame = frame.replace("{J}", adjs[0].capitalize()).replace("{j}", adjs[0])
            other = self._take(niche, rng, ctx, 1, sub, main_only=True)[0] if "{b}" in frame else ""
            feats.append({"title": h.capitalize(), "text": frame.format(a=h, A=h.capitalize(), b=other)})
        return feats

    def page(self, niche, rng, want=(), offers=None, items=(), place=None, strict=False, lang=None, hero_items=None):
        """All templated slots for one page with a shared no-repeat context.
        offers: the business type's typical offerings; items: phrases the user typed; place: the user's city."""
        ctx = PageContext(offers, items, place, strict, lang, hero_items)
        hero = self.hero(niche, rng, want, ctx)   # first, so the headline gets first pick of the user's phrases
        tag = self.tagline(niche, rng, want, ctx)
        cta = tag
        if place and rng.random() < 0.6:
            cta = rng.choice(ctx.place_lines).format(p=place)
        else:
            for _ in range(8):
                cta = self.tagline(niche, rng, want, ctx)
                if cta != tag:
                    break
        return {
            "hero_heading": hero,
            "tagline": tag,
            "cta_text": cta,
            "about": self.about(niche, rng, want, ctx),
            "features": self.features(niche, rng, (min(6, len(ctx.items)) if ctx.strict else 6 if not ctx.pool else min(6, max(3, len(ctx.pool) + len(ctx.items) - 7))), want, ctx),
        }
