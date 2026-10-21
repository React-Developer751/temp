"""Frame-based copy generator.

Frames are hand-written grammar. What fills them is learned from real websites (data/fillers.json, built by
training/train_templates.py): per-niche plural nouns ranked by how characteristic they are of the niche, and
co-occurrence statistics that tie prompt words (e.g. "jewellery") to the nouns that appear next to them.
A small hand-written SEED list tops up niches the crawl covered thinly.

One PageContext is shared by every slot of a page, so a noun is not reused until the pool is exhausted.
"""
import json
import re
from pathlib import Path

FILLERS_PATH = Path(__file__).resolve().parent.parent / "data" / "fillers.json"
POOL_SIZE = 45
SEED_AT = 28

EXCLUDE = set("years lives ways reasons values steps matters makes starts answers details releases awards reviews results dimensions wells hills janes dozens millions atlas postgres devops faqs contents sports kids friends methods cases issues payments pots tips verbs functions phrases algorithms tags costs shapes areas cities items ideas connections minutes channels models arrays seconds quotes principles notifications subscriptions capabilities needs types nouns always".split())

EXCLUDE |= set("""thanks twins belongings canvas calls monitors supports plays credits practices happens ones possibilities animals positions states trees components fits thousands milions
fears interests aspects complexities commitments priorities insects nutrients lawntrepreneurs saas sounds nights gaps differences mistakes problems failures errors greetings scenarios countries examples
fields words letters builds startups docs clusters actions flows labels edits bots impressions clicks keywords forms downloads commissions tests devices accounts goods boxes sets
points emails shoes weights hoops rooms james rows opens centuries dialects directions trademarks salaries arts studies views fingertips promotions windows providers audiences recommendations communications versions releases foams blades""".split())
# tech-flavoured words that leak into other niches through the crawl (e.g. data-science course pages)
NICHE_EXCLUDE = {
    "education": set("applications queries databases datasets frameworks libraries pipelines dashboards workflows platforms solutions systems modules insights apps conversations tasks jobs sessions classes".split()),
    "shop": set("deals trends systems problems stores".split()),
    "portfolio": set("workflows tasks automations leads discounts coupons orders packages courses programs memberships classes".split()),
    "business": set("enterprises posts platforms systems blogs images apps programs elements lessons".split()),
    "fitness": set("skills programs".split()),
}

SEED = {
    "restaurant": "breakfasts lunches dinners desserts pastries pizzas noodles tacos soups smoothies juices cakes cookies muffins bagels curries kebabs snacks platters combos brews".split(),
    "fitness": "sessions routines exercises plans machines bootcamps drills circuits stretches dumbbells kettlebells treadmills intervals lifts".split(),
    "shop": "dresses jackets bags necklaces bracelets earrings pendants scarves wallets candles cushions towels sandals".split(),
    "business": "repairs installations inspections upgrades cleanups appointments estimates jobs projects packages".split(),
    "portfolio": "shoots sessions albums prints sketches illustrations logos brands".split(),
    "education": "lectures quizzes exams workshops tutorials assignments".split(),
    "tech": "dashboards endpoints deployments".split(),
}
# prompt-word -> nouns, for common prompts the corpus cannot link on its own
TOPICS = {
    "jewel": ["rings", "necklaces", "bracelets", "earrings", "pendants", "diamonds"],
    "coffee": ["brews", "pastries", "muffins", "bagels", "drinks", "cakes"],
    "tea": ["brews", "pastries", "snacks", "cookies", "drinks"],
    "bakery": ["pastries", "cakes", "cookies", "muffins", "bagels"],
    "pizza": ["pizzas", "toppings", "sides", "combos"],
    "yoga": ["sessions", "classes", "stretches", "routines"],
    "plumb": ["repairs", "installations", "inspections", "technicians"],
    "photograph": ["photos", "galleries", "albums", "prints", "shoots"],
    "wedding": ["photos", "albums", "galleries", "shoots"],
    "cloth": ["jackets", "dresses", "scarves", "sandals", "bags"],
    "fashion": ["jackets", "dresses", "scarves", "bags", "sandals"],
}

PERSON_WORDS = set("""engineers programmers parents investors individuals stakeholders admins employees humans educators teams members clients pros experts creatives learners beginners agents companies businesses customers users developers
friends guests students people partners owners photographers instructors creators builders sellers professionals specialists technicians
freelancers plumbers tutors coaches trainers teachers athletes riders designers leaders employers visitors graduates mentors firms organizations
suppliers readers peers reps teammates competitors evaluators subscribers""".split())
PERSON = re.compile(r"(ists|ians|ants)$")


def is_person(w):
    return w in PERSON_WORDS or bool(PERSON.search(w))


HERO = [
    "Where {a} come first", "{A} done right", "Great {a}, every day", "Built around your {a}", "Better {a} start here",
    "Made for {a} you will love", "{A} you can trust", "Simply better {a}", "Fresh {a}, every single day", "Your {a}, your way",
    "The home of great {a}", "Where {a} meet {b}", "{A} and {b}, made easy", "Good {a} start here",
]
TAGLINE = [
    "{A}, {b}, and everything in between.", "All your {a} in one place.", "Better {a}, made simple.", "Where great {a} come together.",
    "Simple {a} for everyday life.", "Discover {a} you will love.", "Everything you need, from {a} to {b}.", "Thoughtful {a} and honest {b}.",
    "From {a} to {b}, done properly.", "Honest {a}. Real {b}. No fuss.", "Great {a} start with the little things.",
    "Your go-to place for {a} and {b}.", "More {a}, less hassle.", "Quality {a}, delivered with care.", "Find the {a} that fit your life.",
    "Good {a} should be easy to find.", "We take {a} seriously, so you do not have to.", "{A} and {b}, all under one roof.",
]
FEATURE = [
    "Explore our {a} and find what fits you.", "Simple {a} that work the way you do.", "Everything you need to get more from your {a}.",
    "Thoughtful {a}, made with care.", "Browse our {a} any time, wherever you are.", "Better {a}, built around your {b}.",
    "Quality {a} you can count on.", "Fresh ideas for your {a}, every week.", "Hand-picked {a} for every occasion.",
    "Made to make your {a} a little easier.", "Everything about {a}, in plain language.", "We put {a} first, every single time.",
    "Learn more about our {a} whenever you like.", "Reliable {a} with real support behind them.", "Get the most out of your {a} with less effort.",
    "Straightforward {a}, no surprises.", "{A} that fit right into your day.", "See how our {a} can help with your {b}.",
    "A closer look at our {a}.", "Our {a} are chosen with care and checked twice.",
]
ABOUT_OPEN = [
    "We bring {a}, {b}, and {c} together in one place.", "From {a} to {b}, we focus on what matters most.",
    "Our {a} are made with care and our {b} are built to last.", "Everything we do starts with good {a} and honest {b}.",
    "People come to us for {a}, and stay for the {b}.", "We started with a simple idea: better {a} for everyone.",
    "{A}, {b}, and {c} are at the heart of what we do.", "Whether you need {a} or {b}, you are in the right place.",
]
ABOUT_CLOSE = [
    "Every detail is built to make your {d} simpler and better.", "Our approach to {c} is simple: listen first, then do the work properly.",
    "We keep {c} honest, so you can enjoy {d} with confidence.", "Ask us anything about {d}; we are always happy to help.",
    "That is why so many people trust us with their {c}.", "Small touches, like our {c}, make a big difference.",
    "And we are always working on better {c} for you.", "We stand behind every one of our {d}.",
]
PEOPLE_TAGLINE = ["Made for {p} and {q}, with {a} at the heart.", "Trusted by {p} and {q} everywhere.", "Built for {p}, {q}, and everyone who loves {a}."]


def _stem_match(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n >= 5 or a == b


class PageContext:
    """Remembers which nouns a page already used so slots do not repeat them."""

    def __init__(self):
        self.used = set()


class TemplateModel:
    def __init__(self, data):
        self.d = data
        self._pool = {}

    @classmethod
    def load(cls, path=FILLERS_PATH):
        p = Path(path)
        return cls(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None

    # ---- lexicon -------------------------------------------------------------------------------
    def _ranked(self, niche):
        pl = self.d["niches"].get(niche, {}).get("PL", {})
        learned = [w for w, _ in sorted(pl.items(), key=lambda kv: (-kv[1], kv[0])) if w not in EXCLUDE and w.isalpha()]
        learned = [w for w in learned if w not in NICHE_EXCLUDE.get(niche, ())]
        seeds = [w for w in SEED.get(niche, []) if w not in learned]
        return learned[:SEED_AT] + seeds + learned[SEED_AT:]   # seeds sit ahead of the noisy tail of the learned list

    def nouns(self, niche):
        """Characteristic thing/service nouns (people nouns are kept apart)."""
        if niche not in self._pool:
            self._pool[niche] = [w for w in self._ranked(niche) if not is_person(w)][:POOL_SIZE]
        return self._pool[niche]

    def people(self, niche):
        return [w for w in self._ranked(niche) if is_person(w)][:10]

    def usable(self, niche, minimum=20):
        return len(self.nouns(niche)) >= minimum

    def related(self, niche, want):
        """Nouns tied to the prompt words, from corpus co-occurrence plus the small topic map."""
        co = self.d["niches"].get(niche, {}).get("cooc", {})
        pool = set(self.nouns(niche))
        score = {}
        for kw in want:
            if len(kw) < 4:
                continue
            for key, nouns in co.items():
                if _stem_match(kw, key):
                    for n, c in nouns.items():
                        if n in pool:
                            score[n] = score.get(n, 0) + c
            for t, nouns in TOPICS.items():
                if kw.startswith(t) or kw == t:
                    for n in nouns:
                        if n in pool:
                            score[n] = score.get(n, 0) + 5
        return [n for n, _ in sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))]

    def focus(self, niche, want):
        """A prompt keyword the niche vocabulary itself knows as a noun (e.g. 'coffee' for a cafe)."""
        d = self.d["niches"].get(niche, {})
        known = set(d.get("PL", {})) | set(SEED.get(niche, []))
        return [w for w in want if w.isalpha() and len(w) >= 4 and (w in known or w + "s" in known) and w not in EXCLUDE]

    # ---- picking -------------------------------------------------------------------------------
    def _take(self, niche, rng, ctx, k, rel):
        pool = self.nouns(niche)
        fresh = [w for w in pool if w not in ctx.used]
        if len(fresh) < k:
            ctx.used.clear()
            fresh = list(pool)
        out = [w for w in rel if w in fresh][:max(0, k - 1)] if rel and rng.random() < 0.7 else []
        weights = lambda ws: [1.0 / (1 + i / 12) for i in range(len(ws))]
        while len(out) < k:
            cand = [w for w in fresh if w not in out]
            out.append(rng.choices(cand, weights(cand))[0])
        ctx.used.update(out)
        return out

    def _fill(self, frame, niche, rng, ctx, rel):
        letters = sorted({m.lower() for m in re.findall(r"\{([a-dA-D])\}", frame)})
        ns = self._take(niche, rng, ctx, len(letters), rel)
        m = dict(zip(letters, ns))
        return frame.format(**{**m, **{l.upper(): w.capitalize() for l, w in m.items()}})

    # ---- slots ---------------------------------------------------------------------------------
    def hero(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        f = self.focus(niche, want)
        if f and rng.random() < 0.75:
            w = rng.choice(f)   # f keeps prompt order, so the same seed always gives the same page
            ctx.used.add(w)
            return rng.choice(["{A} done right", "Made around {a}", "Your {a}, our passion", "{A} you can trust"]).format(a=w, A=w.capitalize())
        return self._fill(rng.choice(HERO), niche, rng, ctx, self.related(niche, want))

    def tagline(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        ppl = self.people(niche)
        if len(ppl) > 1 and rng.random() < 0.2:
            p, q = rng.sample(ppl, 2)
            a = self._take(niche, rng, ctx, 1, [])[0]
            return rng.choice(PEOPLE_TAGLINE).format(p=p, q=q, a=a)
        return self._fill(rng.choice(TAGLINE), niche, rng, ctx, self.related(niche, want))

    def about(self, niche, rng, want=(), ctx=None):
        ctx = ctx or PageContext()
        rel = self.related(niche, want)
        paras = []
        ops, cls = rng.sample(ABOUT_OPEN, 2), rng.sample(ABOUT_CLOSE, 2)
        for i in range(2):
            ns = self._take(niche, rng, ctx, 4, rel)
            a, b, c, d = ns
            op, cl = ops[i], cls[i]
            m = {"a": a, "b": b, "c": c, "d": d, "A": a.capitalize(), "B": b.capitalize(), "C": c.capitalize()}
            paras.append(op.format(**m) + " " + cl.format(**m))
        return paras

    def features(self, niche, rng, count=6, want=(), ctx=None):
        ctx = ctx or PageContext()
        heads = self._take(niche, rng, ctx, count, self.related(niche, want))
        frames = rng.sample(FEATURE, min(count, len(FEATURE)))
        feats = []
        for i, h in enumerate(heads):
            frame = frames[i % len(frames)]
            if "{b}" in frame:
                other = self._take(niche, rng, ctx, 1, [])[0]
                text = frame.format(a=h, A=h.capitalize(), b=other)
            else:
                text = frame.format(a=h, A=h.capitalize())
            feats.append({"title": h.capitalize(), "text": text})
        return feats

    def page(self, niche, rng, want=()):
        """All templated slots for one page with a shared no-repeat context."""
        ctx = PageContext()
        tag = self.tagline(niche, rng, want, ctx)
        cta = tag
        for _ in range(8):
            cta = self.tagline(niche, rng, want, ctx)
            if cta != tag:
                break
        return {
            "hero_heading": self.hero(niche, rng, want, ctx),
            "tagline": tag,
            "cta_text": cta,
            "about": self.about(niche, rng, want, ctx),
            "features": self.features(niche, rng, 6, want, ctx),
        }
