"""Creativity layer: propose, judge, evolve.

The renderer itself is deterministic: one prompt -> one picture. This module wraps it in a loop that *thinks before it
draws*. It proposes many variations, lets a critic reject the ones that break the request or look poor, and keeps
improving the survivors with a small genetic search. Nothing here is a neural network and nothing leaves the machine.

    temperature   0.0 .. 1.0   0 = always the safest choice (identical to a plain render); higher = bolder choices
    chain         a co-occurrence Markov chain of props ("laptop" is often followed by "coffee cup")
    genome        the "rules" of one candidate: extra props, scene settings (time / weather / background / palette), seed
    critic        hard gates (never break what the user asked for) + soft scores (clarity, balance, colour harmony, novelty)
    evolve()      population -> critic -> elites + crossover + mutation, a few generations -> best candidate
    imagine()     random mash-ups of two unrelated concepts; the critic rejects the ones that do not work

Honest limits: this recombines the props, scenes and colours the engine already knows. It can surprise you with a good
combination, it cannot invent a new drawing; and the critic measures structure and colour, not taste.
"""
import math
import random
import time
from dataclasses import dataclass, field

from .compose import GENERATIVE_MODES, choose_mode, render
from .props import CONCEPTS, REGISTRY, WORDS
from .scenes import AUTO_DECOR, VENUE_INTERIOR
from .tokenizer import COLORS, fnv1a, parse

# categories that make a prompt an outdoor scene: adding one of these to an indoor prompt would change its whole look
OUTDOOR_CATEGORIES = {"buildings", "vehicles", "machinery", "farm", "playground", "sports", "winter", "rescue"}
SETTINGS = {
    "landscape": {
        "time": ("at night", "at sunset", "at sunrise", "in the morning", "at noon"),
        "weather": ("on a foggy day", "on a rainy day", "on a snowy day"),
        "sky": ("under a pink sky", "under an orange sky", "under a purple sky", "under a teal sky"),
    },
    "scene": {
        "bg": tuple("on a %s background" % c for c in ("beige", "pink", "teal", "navy", "gold", "white", "violet", "lime", "cyan")),
    },
    "generative": {
        "scheme": tuple("in %s tones" % n for n in ("analogous", "complementary", "triadic", "tetradic", "monochrome", "split complementary")),
        "hue": tuple("in %s tones" % c for c in ("gold", "teal", "violet", "crimson", "cyan", "orange", "lime", "pink")),
    },
    "palette": {
        "palette": tuple("in %s and %s tones" % pair for pair in (("gold", "teal"), ("pink", "navy"), ("orange", "purple"),
                                                                 ("cyan", "magenta"), ("lime", "indigo"), ("crimson", "gold"),
                                                                 ("teal", "beige"), ("violet", "yellow"))),
    },
}
SLOT_PRIOR = {"scheme": 1.0, "hue": 0.8, "time": 1.0, "weather": 0.35, "sky": 0.5, "bg": 1.0, "palette": 1.0}
FILLER_WORDS = {"tones"}                    # words the settings use that are intentionally not in the lexicon


# ---------------------------------------------------------------------------------------------- sampling
def top_k_sample(rng, scored, temperature, k=3):
    """Pick one item from [(item, score)]. Temperature 0 -> the best; higher -> one of the best k, still favouring the top."""
    ranked = sorted(scored, key=lambda t: -t[1])[:max(1, k)]
    if not ranked:
        return None
    if temperature <= 0 or len(ranked) == 1:
        return ranked[0][0]
    top = max(ranked[0][1], 1e-9)
    power = 1.0 / max(temperature, 0.05)
    weights = [max(s, 1e-9) / top for _, s in ranked]
    weights = [w ** power for w in weights]
    r = rng.random() * sum(weights)
    for (item, _), w in zip(ranked, weights):
        r -= w
        if r <= 0:
            return item
    return ranked[-1][0]


# ---------------------------------------------------------------------------------------------- prop chain (Markov)
_WORD_CACHE = {}


def prop_word(name):
    """A plain word that makes the parser produce prop `name` (None if there is none)."""
    if name in _WORD_CACHE:
        return _WORD_CACHE[name]
    found = None
    candidates = [name] + list(REGISTRY[name].words) if name in REGISTRY else []     # the prop's own name and first-listed words first
    for w in candidates:
        if w.isalpha() and w.isascii() and WORDS.get(w) == name and any(e.name == name for e in parse(w).entities):
            found = w
            break
    _WORD_CACHE[name] = found
    return found


class Chain:
    """Which prop tends to appear with which: transitions[a][b] = weight. Built in, and extendable from your own captions."""

    def __init__(self):
        self.t = {}

    def add(self, a, b, w=1.0, both=True):
        if a == b or a not in REGISTRY or b not in REGISTRY:
            return
        self.t.setdefault(a, {})
        self.t[a][b] = self.t[a].get(b, 0.0) + w
        if both:
            self.t.setdefault(b, {})
            self.t[b][a] = self.t[b].get(a, 0.0) + w * 0.6

    @classmethod
    def builtin(cls):
        c = cls()
        for val in CONCEPTS.values():
            props = [p for p in val[1] if p in REGISTRY]
            for a in props:
                for b in props:
                    c.add(a, b, 2.0, both=False)
        for a, bs in AUTO_DECOR.items():
            for k, b in enumerate(bs):
                c.add(a, b, 3.0 - 0.5 * k)
        for venue, bs in VENUE_INTERIOR.items():
            for b in bs:
                c.add(venue, b, 1.5)
                for a in bs:
                    c.add(a, b, 1.0, both=False)
        by_cat = {}
        for p in REGISTRY.values():
            by_cat.setdefault(p.category, []).append(p.name)
        for names in by_cat.values():                       # same family: weak link so every prop has some neighbours
            for a in names:
                for b in names:
                    c.add(a, b, 0.25, both=False)
        return c

    def learn_captions(self, captions, weight=1.0):
        """Add what *your* data pairs together: every two props named in one caption become neighbours."""
        n = 0
        for cap in captions:
            names = list(dict.fromkeys(e.name for e in parse(str(cap)).entities if e.name in REGISTRY))
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    self.add(a, b, weight)
                    n += 1
        return n

    def weight(self, a, b):
        return self.t.get(a, {}).get(b, 0.0)

    def affinity(self, names):
        """0..1: how well a set of props go together (mean pair link, a weight of 2 counts as a perfect pair)."""
        names = list(dict.fromkeys(n for n in names if n in REGISTRY))
        if len(names) < 2:
            return 0.6
        vals = [min(1.0, max(self.weight(a, b), self.weight(b, a)) / 2.0) for i, a in enumerate(names) for b in names[i + 1:]]
        return sum(vals) / len(vals)

    def suggest(self, rng, current, temperature, exclude=(), allow=None):
        """The next prop to add next to `current`, sampled from the top 3 candidates (best one at temperature 0)."""
        score = {}
        for a in current:
            for b, w in self.t.get(a, {}).items():
                if b in current or b in exclude or (allow is not None and not allow(b)) or prop_word(b) is None:
                    continue
                score[b] = score.get(b, 0.0) + w
        if not score:
            return None
        return top_k_sample(rng, sorted(score.items()), temperature, 3)


_BUILTIN = None


def default_chain(model=None):
    """The built-in chain, plus anything a trained model's captions pair together."""
    global _BUILTIN
    if _BUILTIN is None:
        _BUILTIN = Chain.builtin()
    if model is None or not getattr(model, "samples", None):
        return _BUILTIN
    c = Chain()
    c.t = {a: dict(bs) for a, bs in _BUILTIN.t.items()}
    c.learn_captions([s.caption for s in model.samples], 1.5)
    return c


# ---------------------------------------------------------------------------------------------- genome
@dataclass(frozen=True)
class Genome:
    base: str
    extras: tuple = ()
    slots: tuple = ()          # ((slot, phrase), ...) sorted
    seed: int = 0

    def prompt(self):
        parts = [self.base]
        words = [prop_word(e) for e in self.extras]
        if words:
            parts.append("with " + " and ".join(words))
        parts += [ph for _, ph in self.slots]
        return " ".join(parts)

    def describe(self):
        bits = []
        if self.extras:
            bits.append("extras: " + ", ".join(self.extras))
        bits += ["%s: %s" % (k, v) for k, v in self.slots]
        return "; ".join(bits) or "plain (no changes)"


class Context:
    """Everything about the request that does not change while searching."""

    def __init__(self, prompt, temperature, model, learned, chain):
        self.prompt = prompt
        self.base = parse(prompt)
        self.mode = choose_mode(self.base)
        self.temperature = temperature
        self.model, self.learned = model, learned
        self.chain = chain
        self.prop_names = list(dict.fromkeys(e.name for e in self.base.entities if e.name in REGISTRY))
        self.has_colors = bool(self.base.loose_colors or any(e.color for e in self.base.entities))
        self.slot_pool = self._slot_pool()
        self.max_extras = self._max_extras()

    def _slot_pool(self):
        if self.mode == "landscape":
            pool = dict(SETTINGS["landscape"])
            if self.base.time or "space" in self.base.flags:
                pool.pop("time", None)
            if self.base.flags & {"snow", "rain", "fog", "space", "cyberpunk"}:
                pool.pop("weather", None)
            if self.base.sky_color:
                pool.pop("sky", None)
            return pool
        if self.mode == "scene":
            return {} if self.base.background else dict(SETTINGS["scene"])
        if self.mode in GENERATIVE_MODES:
            pool = dict(SETTINGS["generative"])
            if any(f.startswith("scheme_") for f in self.base.flags):
                pool.pop("scheme")
            if self.has_colors or self.base.background:
                pool.pop("hue")
            return pool
        if self.has_colors or self.base.background:
            return {}
        return dict(SETTINGS["palette"])

    def _max_extras(self):
        if self.mode not in ("scene", "landscape") or not self.prop_names:
            return 0
        n = sum(min(e.count, 3) for e in self.base.entities if e.name in REGISTRY)
        return max(0, min(3, 4 - n))

    def allowed_extra(self, name):
        p = REGISTRY[name]
        if self.mode == "scene" and p.category in OUTDOOR_CATEGORIES:
            return False
        return p.place != "wall" or self.mode == "scene"


# ---------------------------------------------------------------------------------------------- genome operators
def random_genome(ctx, rng, seed=None):
    t = ctx.temperature
    extras = []
    n_extra = 0
    if ctx.max_extras:
        n_extra = min(ctx.max_extras, int(top_k_sample(rng, [(0, 1.0), (1, 1.0 + 2 * t), (2, 0.5 + 2.5 * t), (3, 0.2 + 1.5 * t)], t, 4)))
    current = list(ctx.prop_names)
    for _ in range(n_extra):
        nxt = ctx.chain.suggest(rng, current + extras, t, extras, ctx.allowed_extra)
        if nxt:
            extras.append(nxt)
    slots = {}
    for slot, phrases in ctx.slot_pool.items():
        if rng.random() < min(0.95, SLOT_PRIOR.get(slot, 0.5) * (0.35 + 0.65 * t)):
            slots[slot] = rng.choice(phrases)
    return Genome(ctx.prompt, tuple(extras), tuple(sorted(slots.items())), rng.randrange(1 << 30) if seed is None else seed)


def crossover(ctx, rng, a, b):
    """Child takes each gene from one parent: the extras are drawn from the union, every setting slot from either."""
    union = list(dict.fromkeys(list(a.extras) + list(b.extras)))
    rng.shuffle(union)
    k = min(ctx.max_extras, max(len(a.extras), len(b.extras)) if rng.random() < 0.7 else (len(union) + 1) // 2)
    extras = tuple(union[:k])
    da, db = dict(a.slots), dict(b.slots)
    slots = {}
    for slot in set(da) | set(db):
        pick = da if rng.random() < 0.5 else db
        if slot in pick:
            slots[slot] = pick[slot]
    return Genome(ctx.prompt, extras, tuple(sorted(slots.items())), a.seed if rng.random() < 0.5 else b.seed)


def mutate(ctx, rng, g, rate):
    extras, slots, seed = list(g.extras), dict(g.slots), g.seed
    t = ctx.temperature
    if ctx.max_extras and rng.random() < rate:
        op = rng.choice(("add", "remove", "swap"))
        if op == "add" and len(extras) < ctx.max_extras:
            nxt = ctx.chain.suggest(rng, list(ctx.prop_names) + extras, t, extras, ctx.allowed_extra)
            if nxt:
                extras.append(nxt)
        elif op == "remove" and extras:
            extras.pop(rng.randrange(len(extras)))
        elif op == "swap" and extras:
            i = rng.randrange(len(extras))
            rest = extras[:i] + extras[i + 1:]
            nxt = ctx.chain.suggest(rng, list(ctx.prop_names) + rest, min(1.0, t + 0.2), rest + [extras[i]], ctx.allowed_extra)
            if nxt:
                extras[i] = nxt
    for slot, phrases in ctx.slot_pool.items():
        if rng.random() < rate * 0.7:
            if slot in slots and rng.random() < 0.3:
                del slots[slot]
            else:
                slots[slot] = rng.choice(phrases)
    if rng.random() < rate:
        seed = rng.randrange(1 << 30)
    return Genome(ctx.prompt, tuple(extras), tuple(sorted(slots.items())), seed)


# ---------------------------------------------------------------------------------------------- critic
@dataclass
class Verdict:
    ok: bool
    score: float
    parts: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)        # why it failed a hard gate
    notes: list = field(default_factory=list)          # soft remarks on a candidate that passed


def _rgb_stats(cv):
    data = cv.to_rgb_bytes()
    n = cv.w * cv.h
    r, g, b = data[0::3], data[1::3], data[2::3]
    lum = [(0.299 * r[i] + 0.587 * g[i] + 0.114 * b[i]) / 255.0 for i in range(n)]
    return r, g, b, lum


def _tri(x, lo, peak, hi):
    if x <= lo or x >= hi:
        return 0.0
    return (x - lo) / (peak - lo) if x < peak else (hi - x) / (hi - peak)


def _hue_deg(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0, 0.0, mx
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60.0, d / mx, mx


def thumb(cv, n=12):
    """n x n mean-colour thumbnail (flat list) used to measure how different two candidates look."""
    data = cv.to_rgb_bytes()
    w, h = cv.w, cv.h
    out = []
    for ty in range(n):
        y0, y1 = ty * h // n, max(ty * h // n + 1, (ty + 1) * h // n)
        for tx in range(n):
            x0, x1 = tx * w // n, max(tx * w // n + 1, (tx + 1) * w // n)
            acc = [0, 0, 0]
            cnt = 0
            for y in range(y0, y1, max(1, (y1 - y0) // 3)):
                base = y * w * 3
                for x in range(x0, x1, max(1, (x1 - x0) // 3)):
                    i = base + x * 3
                    acc[0] += data[i]
                    acc[1] += data[i + 1]
                    acc[2] += data[i + 2]
                    cnt += 1
            out += [a / (255.0 * cnt) for a in acc]
    return out


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def critique(ctx, genome, cv, parsed, mode, archive_thumbs):
    """Judge one rendered candidate. Hard gates first (what the user asked must survive), then soft quality scores."""
    reasons = []
    base = ctx.base
    # ---- gates ------------------------------------------------------------------------------------------
    if mode != ctx.mode:
        reasons.append("changed the picture type (%s -> %s)" % (ctx.mode, mode))
    cand = list(parsed.entities)
    for b in base.entities:
        hit = next((c for c in cand if c.kind == b.kind and c.name == b.name and c.color == b.color and c.count >= b.count), None)
        if hit is None:
            reasons.append("lost or altered %s" % b.name)
    if list(parsed.texts) != list(base.texts):
        reasons.append("changed the quoted text")
    new_unknown = [w for w in parsed.unknown_words if w not in base.unknown_words and w not in FILLER_WORDS]
    if new_unknown:
        reasons.append("unknown words: " + ", ".join(new_unknown[:3]))
    drawn = getattr(cv, "drawn", None)
    for name in ctx.prop_names:
        if drawn is None or name not in drawn:
            reasons.append("%s was not drawn" % name)
    r, g, b, lum = _rgb_stats(cv)
    n = len(lum)
    mean = sum(lum) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in lum) / n)
    if std < 0.03:
        reasons.append("almost blank")
    reasons = list(dict.fromkeys(reasons))
    # ---- soft scores ------------------------------------------------------------------------------------
    w, h = cv.w, cv.h
    edges = 0
    for y in range(0, h, 2):
        row = y * w
        for x in range(w - 1):
            if abs(lum[row + x] - lum[row + x + 1]) > 0.07:
                edges += 1
    edge_density = edges / max(1, (h // 2 + 1) * (w - 1))
    clarity = 0.6 * min(1.0, std / 0.20) + 0.4 * _tri(edge_density, 0.005, 0.07, 0.32)
    hist = [0.0] * 12
    sat_mass = 0.0
    for i in range(0, n, 3):
        hue, sat, val = _hue_deg(r[i] / 255.0, g[i] / 255.0, b[i] / 255.0)
        if sat > 0.22 and val > 0.18:
            hist[int(hue // 30) % 12] += 1
            sat_mass += 1
    total = sum(hist)
    if total > 0:
        probs = [v / total for v in hist if v]
        eff = math.exp(-sum(p * math.log(p) for p in probs))
        richness = _tri(eff, 1.0, 4.0, 9.5)
        top = sorted(range(12), key=lambda k: -hist[k])[:3]
        hues = [k * 30 + 15 for k in top if hist[k] / total > 0.12]
        if len(hues) < 2:
            harmony = 0.7
        else:
            best = 0.0
            for i in range(len(hues)):
                for j in range(i + 1, len(hues)):
                    d = abs(hues[i] - hues[j])
                    d = min(d, 360 - d)
                    best += max(_tri(d, -1, 0, 45), _tri(d, 135, 180, 215), _tri(d, 90, 120, 150), 0.3)
            harmony = min(1.0, best / (len(hues) * (len(hues) - 1) / 2))
    else:
        richness, harmony = 0.2, 0.5
    # balance: where the "interesting" pixels (different from the border colour) sit
    ring = []
    for x in range(0, w, max(1, w // 16)):
        ring += [(r[x], g[x], b[x]), (r[(h - 1) * w + x], g[(h - 1) * w + x], b[(h - 1) * w + x])]
    ref = tuple(sorted(c[k] for c in ring)[len(ring) // 2] for k in range(3))
    sx = sy = sm = 0.0
    inter = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            i = y * w + x
            d = (abs(r[i] - ref[0]) + abs(g[i] - ref[1]) + abs(b[i] - ref[2])) / 765.0
            if d > 0.12:
                inter += 1
                sx += d * x
                sy += d * y
                sm += d
    cells = ((h + 1) // 2) * ((w + 1) // 2)
    if sm > 0:
        off = math.hypot(sx / sm / w - 0.5, sy / sm / h - 0.5)
        balance = 0.65 * max(0.0, 1.0 - off / 0.25) + 0.35 * _tri(inter / cells, 0.05, 0.40, 0.95)
    else:
        balance = 0.0
    names = [x for x in (drawn or []) if x in REGISTRY]
    affinity = ctx.chain.affinity(names)
    cur = thumb(cv)
    nov = min(1.0, min((_dist(cur, t) for t in archive_thumbs), default=0.10) / 0.12)
    wasted = sum(1 for e in genome.extras if drawn is not None and e not in drawn)
    t = ctx.temperature
    wn = 0.10 + 0.45 * t
    weights = {"clarity": 0.25, "richness": 0.10, "balance": 0.15, "harmony": 0.15, "affinity": 0.15, "novelty": wn}
    parts = {"clarity": clarity, "richness": richness, "balance": balance, "harmony": harmony, "affinity": affinity, "novelty": nov}
    score = sum(weights[k] * parts[k] for k in weights) / sum(weights.values()) - 0.08 * wasted - 0.02 * len(genome.extras)
    notes = ["%d added prop(s) were dropped by the layout" % wasted] if wasted else []
    return Verdict(ok=not reasons, score=score, parts={k: round(v, 3) for k, v in parts.items()}, reasons=reasons, notes=notes), cur


# ---------------------------------------------------------------------------------------------- the search
@dataclass
class Creation:
    canvas: object
    parsed: object
    mode: str
    prompt: str                  # the prompt that was actually rendered (reproduce with render(prompt, ..., seed=seed))
    seed: int
    score: float
    parts: dict
    notes: list
    history: list
    rejected: dict
    evaluated: int
    alternatives: list
    base_score: float = 0.0

    def to_dict(self):
        return {"prompt_used": self.prompt, "seed": self.seed, "mode": self.mode, "score": round(self.score, 3),
                "baseline_score": round(self.base_score, 3), "scores": self.parts, "thinking": self.notes,
                "generations": self.history, "rejected_by_critic": self.rejected, "evaluated": self.evaluated,
                "alternatives": self.alternatives}


class _Evaluator:
    def __init__(self, ctx, size, deadline):
        self.ctx, self.size, self.deadline = ctx, size, deadline
        self.cache = {}
        self.max_archive = 48
        self.archive = []
        self.rejected = {}
        self.count = 0
        self.explored = 0

    def expired(self):
        return self.deadline is not None and time.time() > self.deadline

    def key(self, g):
        return (g.extras, g.slots, g.seed)

    def evaluate(self, g, commit=True):
        k = self.key(g)
        if k in self.cache:
            return self.cache[k]
        ctx = self.ctx
        cv, parsed, mode = render(g.prompt(), self.size, self.size, g.seed, ctx.model, ctx.learned)
        verdict, th = critique(ctx, g, cv, parsed, mode, self.archive)
        self.count += 1
        if not verdict.ok:
            for r in verdict.reasons:
                self.rejected[r] = self.rejected.get(r, 0) + 1
        else:
            self.archive.append(th)
            del self.archive[:-self.max_archive]                 # novelty is measured against the most recent candidates only
        self.cache[k] = verdict
        return verdict


def _select(rng, ranked, k=3):
    """Tournament pick from an already-ranked list [(genome, verdict)]."""
    group = [ranked[rng.randrange(len(ranked))] for _ in range(max(2, min(k, len(ranked))))]
    return max(group, key=lambda t: t[1].score)[0]


def _explain(ctx, g, v, base_v, ev, history):
    notes = ["understood the request as a %s picture of: %s" % (ctx.mode, ", ".join(ctx.prop_names) or "(no props)")]
    if ctx.temperature <= 0:
        notes.append("temperature 0: kept the single safest rendering, no variations were tried")
        return notes
    if ev.explored:
        notes.append("first screened %d random ideas at thumbnail size and kept the best few" % ev.explored)
    notes.append("tried %d candidates over %d generation(s); the critic rejected %d" % (ev.count, max(0, len(history) - 1), sum(ev.rejected.values())))
    for reason, n in sorted(ev.rejected.items(), key=lambda t: -t[1])[:3]:
        notes.append("  rejected %dx: %s" % (n, reason))
    notes.append("chosen genome -> " + g.describe())
    if g.extras:
        aff = ctx.chain.affinity(list(ctx.prop_names) + list(g.extras))
        notes.append("added %s because they usually go with %s (fit %.2f)" % (" and ".join(g.extras), " + ".join(ctx.prop_names), aff))
    strong = sorted(v.parts.items(), key=lambda t: -t[1])[:2]
    weak = sorted(v.parts.items(), key=lambda t: t[1])[0]
    notes.append("strongest: %s; weakest: %s" % (", ".join("%s %.2f" % kv for kv in strong), "%s %.2f" % weak))
    if base_v is not None:
        notes.append("score %.3f vs plain render %.3f" % (v.score, base_v.score))
    return notes


def evolve(prompt, temperature=0.7, population=8, generations=3, seed=0, size=128, final_size=512, model=None,
           learned="auto", chain=None, max_seconds=None, alternatives=3, final_height=None, explore=0):
    """Create a picture for `prompt` by proposing variations, judging them, and breeding the best ones.

    Returns a `Creation`. The user's request is protected by the critic's gates: a variation that drops, recolours or
    shrinks anything the prompt asked for, changes the picture type, or leaves a requested prop undrawn is thrown away.
    temperature 0 returns the plain render (no search at all).
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")
    if not 0.0 <= temperature <= 1.0:
        raise ValueError("temperature must be between 0.0 and 1.0")
    population = max(2, min(int(population), 24))
    generations = max(0, min(int(generations), 8))
    chain = chain or default_chain(model)
    ctx = Context(prompt, temperature, model, learned, chain)
    rng = random.Random(fnv1a(prompt) ^ ((seed * 2654435761) & 0xFFFFFFFF) ^ 0x5EED)
    deadline = None if max_seconds is None else time.time() + max_seconds
    ev = _Evaluator(ctx, size, deadline)
    baseline = Genome(prompt, (), (), seed)
    base_v = ev.evaluate(baseline)
    pool = [baseline]
    history = []

    def rank(genomes):
        scored = [(g, ev.evaluate(g)) for g in genomes]
        valid = [(g, v) for g, v in scored if v.ok]
        return sorted(valid, key=lambda t: -t[1].score)

    ranked = rank(pool)
    if temperature > 0:
        screened = []
        if explore > 0:
            # broad first pass: many random ideas judged by the critic at a tiny size; only the best few enter the real search
            quick = _Evaluator(ctx, 48, deadline)
            seen = {ev.key(baseline)}
            tries = 0
            while len(seen) < explore + 1 and tries < explore * 3 and not quick.expired():
                tries += 1
                g = random_genome(ctx, rng)
                if ev.key(g) in seen:
                    continue
                seen.add(ev.key(g))
                v = quick.evaluate(g)
                if v.ok:
                    screened.append((v.score, g))
            screened.sort(key=lambda t: -t[0])
            ev.explored = len(seen) - 1
            for k, c in quick.rejected.items():
                ev.rejected[k] = ev.rejected.get(k, 0) + c
        pool += [g for _, g in screened[:population - 1]]
        pool += [random_genome(ctx, rng) for _ in range(population - len(pool))]
        ranked = rank(pool)
        history.append({"generation": 0, "best": round(ranked[0][1].score, 3) if ranked else None,
                        "mean": round(sum(v.score for _, v in ranked) / max(1, len(ranked)), 3), "valid": len(ranked), "size": len(pool)})
        rate = 0.25 + 0.55 * temperature
        for gen in range(1, generations + 1):
            if ev.expired() or not ranked:
                break
            elite_n = 2 if population < 10 else 3
            nxt = [g for g, _ in ranked[:elite_n]]
            attempts = 0
            while len(nxt) < population - 1 and attempts < population * 6:
                attempts += 1
                if len(ranked) >= 2 and rng.random() < 0.75:
                    child = crossover(ctx, rng, _select(rng, ranked), _select(rng, ranked))
                else:
                    child = _select(rng, ranked) if ranked else baseline
                child = mutate(ctx, rng, child, rate)
                if ev.key(child) in [ev.key(x) for x in nxt]:
                    continue
                nxt.append(child)
            nxt.append(random_genome(ctx, rng))                           # one fresh immigrant keeps the pool diverse
            pool = nxt
            ranked = rank(pool)
            if ranked:
                history.append({"generation": gen, "best": round(ranked[0][1].score, 3),
                                "mean": round(sum(v.score for _, v in ranked) / len(ranked), 3), "valid": len(ranked), "size": len(pool)})
    else:
        history.append({"generation": 0, "best": round(base_v.score, 3), "mean": round(base_v.score, 3), "valid": 1 if base_v.ok else 0, "size": 1})
    everyone = sorted(((g, v) for g, v in ((g, ev.cache[ev.key(g)]) for g in _unique_genomes(ev, pool, baseline)) if v.ok), key=lambda t: -t[1].score)
    if not everyone:                                                      # nothing passed (even the plain render): return it anyway
        everyone = [(baseline, base_v)]
    picked = None
    if temperature > 0 and len(everyone) > 1:
        # not always the single top scorer: sample among the best three (never below the plain render), so seeds give variety
        floor = base_v.score - 1e-9 if base_v.ok else -1e9
        shortlist = [(i, v.score) for i, (_, v) in enumerate(everyone) if v.score >= floor]
        pick = top_k_sample(rng, shortlist, temperature, 3) if shortlist else 0
        top_score = everyone[0][1].score
        everyone.insert(0, everyone.pop(pick))
        picked = (pick + 1, everyone[0][1].score, top_score) if pick else None
    fh = final_height or final_size
    cv = parsed = mode = None
    chosen = everyone[0]
    for g, v in everyone[:6]:                                             # re-check at full size; fall back down the list
        cv, parsed, mode = render(g.prompt(), final_size, fh, g.seed, model, learned)
        v2, _ = critique(ctx, g, cv, parsed, mode, [])
        chosen = (g, v)
        if v2.ok or g is baseline:
            break
    g, v = chosen
    why = _explain(ctx, g, v, base_v, ev, history)
    if picked and g is everyone[0][0]:
        why.append("temperature chose #%d of the best three for variety (score %.3f; the top scorer had %.3f)" % picked)
    if not v.ok:
        why.insert(0, "warning: no candidate passed the critic (%s); returned the plain render" % "; ".join(v.reasons[:3]))
    alts = [{"prompt": a.prompt(), "seed": a.seed, "score": round(av.score, 3), "genome": a.describe()}
            for a, av in everyone[1:1 + max(0, alternatives)] if a is not g]
    return Creation(cv, parsed, mode, g.prompt(), g.seed, v.score, v.parts, why, history,
                    ev.rejected, ev.count, alts, base_v.score)


def _unique_genomes(ev, pool, baseline):
    seen, out = set(), []
    for g in [baseline] + list(pool):
        k = ev.key(g)
        if k in seen:
            continue
        seen.add(k)
        out.append(g)
    # genomes from earlier generations are in the cache but not in `pool`: recover them from the cache keys
    for k in list(ev.cache):
        if k not in seen:
            seen.add(k)
            out.append(Genome(baseline.base, k[0], k[1], k[2]))
    return out


# ---------------------------------------------------------------------------------------------- mash-ups
def _concept_word(name):
    words = [w for w in CONCEPTS[name][0] if w.isalpha() and w.isascii()]
    for w in words:
        if any(e.name in REGISTRY for e in parse(w).entities):
            return w
    return None


WORLDS = ("space", "night", "snow", "beach", "city", "sea", "forest", "desert", "mountain", "rain", "sunset", "island")


def _pool():
    props = sorted(n for n in REGISTRY if prop_word(n))
    concepts = sorted(c for c in CONCEPTS if _concept_word(c))
    return props, concepts


def mashup_prompt(rng, temperature, chain, anchor=None):
    """Two ideas that rarely meet. Higher temperature -> more distant pairs. Returns (prompt, explanation)."""
    props, concepts = _pool()
    kind = rng.random()
    if anchor:
        a_word, a_prop = anchor, None
        parsed = parse(anchor)
        names = [e.name for e in parsed.entities if e.name in REGISTRY]
        a_prop = names[0] if names else None
    else:
        a_prop = rng.choice(props)
        a_word = prop_word(a_prop)
    if kind < 0.25 and not anchor:
        world = rng.choice(WORLDS)
        return "%s in %s" % (a_word, world), "a world + a subject: %s + %s" % (a_word, world)
    pool = [p for p in props if p != a_prop and (a_prop is None or REGISTRY[p].category != REGISTRY[a_prop].category)]
    scored = [(p, (1.0 - chain.affinity([a_prop, p]) if a_prop else 1.0) + 0.05) for p in pool]
    if temperature < 0.5:
        scored = [(p, 1.0 - s + 0.05) for p, s in scored]      # cool: lean towards pairs that are not wildly unrelated
    rng.shuffle(scored)
    b = top_k_sample(rng, scored[:12], temperature, 3)
    return "%s and %s" % (a_word, prop_word(b)), "two subjects: %s + %s" % (a_word, prop_word(b))


def imagine(temperature=0.8, seed=0, attempts=12, size=128, final_size=512, anchor=None, polish=True, model=None, learned="auto",
            population=6, generations=2, min_score=0.45, max_seconds=None, final_height=None):
    """Mash two concepts together at random. Every attempt is judged by the critic (all parts must be drawn, nothing ignored);
    most random pairs fail, and the first good one is then polished with a short evolve()."""
    rng = random.Random(0xC0FFEE ^ ((seed * 2654435761) & 0xFFFFFFFF))
    chain = default_chain(model)
    deadline = None if max_seconds is None else time.time() + max_seconds
    log, rejected = [], {}
    best = None
    for k in range(1, max(1, int(attempts)) + 1):
        if deadline is not None and time.time() > deadline:
            break
        prompt, why = mashup_prompt(rng, temperature, chain, anchor)
        ctx = Context(prompt, 0.0, model, learned, chain)
        cv, parsed, mode = render(prompt, size, size, seed + k, model, learned)
        wanted = len(ctx.prop_names)
        v, _ = critique(ctx, Genome(prompt, (), (), seed + k), cv, parsed, mode, [])
        if wanted < 2 and not anchor:
            v.ok = False
            v.reasons.append("the two ideas did not both become props")
        if parsed.unknown_words and not anchor:
            v.ok = False
            v.reasons.append("unknown words: " + ", ".join(parsed.unknown_words[:3]))
        entry = {"attempt": k, "prompt": prompt, "idea": why, "accepted": False, "score": round(v.score, 3)}
        if not v.ok:
            entry["rejected"] = v.reasons
            for r in v.reasons:
                rejected[r] = rejected.get(r, 0) + 1
        elif v.score >= min_score:
            entry["accepted"] = True
        log.append(entry)
        if v.ok and (best is None or v.score > best[1]):
            best = (prompt, v.score, seed + k)
        if entry["accepted"]:
            break
    if best is None:
        raise ValueError("no mash-up passed the critic in %d attempts; raise `attempts` or lower the temperature" % len(log))
    prompt, score, sd = best
    if polish:
        left = None if deadline is None else max(0.5, deadline - time.time())
        c = evolve(prompt, temperature=min(1.0, temperature), population=population, generations=generations, seed=sd, size=size,
                   final_size=final_size, model=model, learned=learned, chain=chain, max_seconds=left, final_height=final_height)
    else:
        c = evolve(prompt, temperature=0.0, seed=sd, size=size, final_size=final_size, model=model, learned=learned, chain=chain,
                   final_height=final_height)
    thrown = sum(1 for e in log if not e["accepted"])
    c.notes = (["imagined %d idea(s); %d did not make it" % (len(log), thrown)]
               + ["  attempt %d: %s -> %s" % (e["attempt"], e["prompt"], "accepted" if e["accepted"] else
                                                 ("rejected: " + "; ".join(e.get("rejected", ["too plain"])))) for e in log[-6:]]
               + c.notes)
    c.rejected = {**rejected, **c.rejected}
    return c, log
