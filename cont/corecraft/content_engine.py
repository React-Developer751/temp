"""Content AI Engine: prompt -> niche, keywords, validated copy. Uses json, random, re only."""
import json
import random
import re

from .ngram_model import Model, tokens as _model_tokens
from .template_model import TemplateModel

STOPWORDS = set(
    "a an the and or for of to in on with my our your is are be that this it i we want need make build create "
    "website site web page banao banana chahiye mujhe ek ka ki ke se me mein hai hain called named name please "
    "simple modern good best new unique attractive".split()
)

# niche -> trigger keywords, mood, copy bank
NICHES = {
    "restaurant": {
        "keys": ["restaurant", "cafe", "coffee", "bakery", "food", "pizza", "dining", "kitchen", "chef", "dhaba", "menu", "bistro"],
        "mood": "warm",
        "name_a": ["Saffron", "Ember", "Basil", "Maple", "Copper", "Olive"],
        "name_b": ["Table", "Kitchen", "House", "Bistro", "Hearth"],
        "headings": ["Taste the Tradition", "Fresh From Our Kitchen", "Where Every Meal Is a Story", "Flavours Worth Coming Back For"],
        "taglines": ["Seasonal ingredients, cooked with care.", "Good food, warm company, zero rush."],
        "paras": [
            "Every dish begins with ingredients sourced from growers we know by name, then built slowly into plates that feel like home.",
            "From the first sip in the morning to the last course at night, our kitchen cooks what is in season and nothing less.",
            "We believe a table is the best place to slow down, so we set ours with care and keep the menu honest.",
        ],
        "features": [("Seasonal Menu", "Dishes change with the harvest so everything tastes fresh."), ("Local Sourcing", "We buy from nearby farms and bakers."), ("Private Dining", "Host birthdays and meetings in a quiet corner."), ("Takeaway", "Our favourites, packed to travel well."), ("Chef Specials", "A new creation every week."), ("Family Friendly", "Space and plates for every age.")],
        "ctas": ["Reserve a Table", "View the Menu", "Order Now"],
    },
    "fitness": {
        "keys": ["gym", "fitness", "yoga", "workout", "trainer", "training", "health", "crossfit", "sports", "wellness"],
        "mood": "bold",
        "name_a": ["Iron", "Pulse", "Apex", "Titan", "Vigor", "Surge"],
        "name_b": ["Fitness", "Lab", "Club", "Studio", "Athletics"],
        "headings": ["Stronger Every Single Day", "Train Hard. Recover Smart.", "Your Best Shape Starts Here", "Built on Discipline"],
        "taglines": ["Coaching that meets you where you are.", "Real plans, real results."],
        "paras": [
            "Our coaches build programs around your goals, your schedule and your body, then track progress so effort never goes unseen.",
            "Whether you lift, run or stretch, you get equipment that works, trainers who care and a crew that pushes you forward.",
            "Small habits compound. We help you make showing up the easy part and results the natural outcome.",
        ],
        "features": [("Personal Coaching", "One-on-one plans that adapt every week."), ("Group Classes", "High-energy sessions all day long."), ("Nutrition Guidance", "Simple meal plans that fit real life."), ("Progress Tracking", "Measure strength, stamina and habits."), ("Open Floor", "Modern machines and free weights."), ("Recovery Zone", "Stretch, foam roll and reset.")],
        "ctas": ["Start Free Trial", "Join Today", "Book a Session"],
    },
    "tech": {
        "keys": ["software", "saas", "app", "startup", "tech", "ai", "platform", "developer", "cloud", "api", "digital", "agency", "it"],
        "mood": "cool",
        "name_a": ["Nova", "Pixel", "Orbit", "Flux", "Quanta", "Helix"],
        "name_b": ["Labs", "Works", "Cloud", "Systems", "Stack"],
        "headings": ["Build Faster. Ship Smarter.", "Software That Gets Out of Your Way", "Turn Ideas Into Products", "Technology With a Human Touch"],
        "taglines": ["Reliable tools for ambitious teams.", "From first line of code to launch day."],
        "paras": [
            "We combine clean engineering with thoughtful design so your product feels fast, simple and dependable from day one.",
            "Our team replaces busywork with automation, giving you dashboards that answer questions before you ask them.",
            "Security, speed and clarity are built in, not bolted on, so you can focus on customers instead of infrastructure.",
        ],
        "features": [("Lightning Fast", "Optimised for speed at every layer."), ("Secure by Default", "Encryption and access control built in."), ("Smart Automation", "Remove repetitive tasks in minutes."), ("Live Analytics", "Clear numbers, updated in real time."), ("Easy Integrations", "Connect the tools you already use."), ("Friendly Support", "Real people who reply quickly.")],
        "ctas": ["Get Started", "Request a Demo", "Try It Free"],
    },
    "portfolio": {
        "keys": ["portfolio", "designer", "photographer", "photography", "artist", "freelancer", "creative", "personal", "resume", "illustrator", "filmmaker"],
        "mood": "elegant",
        "name_a": ["Studio", "Atelier", "Frame", "Canvas", "Mono", "Lumen"],
        "name_b": ["Creative", "Works", "Visuals", "Collective", "Folio"],
        "headings": ["Work That Speaks for Itself", "Stories Told Through Design", "Crafting Images With Intent", "Selected Work, Thoughtfully Made"],
        "taglines": ["Independent creative for brands with a point of view.", "Quietly bold, carefully made."],
        "paras": [
            "Each project starts with listening, then moves through sketches and drafts until the result feels inevitable.",
            "I partner with founders, magazines and local businesses to give ideas a clear, memorable shape.",
            "Detail matters. From typography to timing, every choice serves the story you want people to remember.",
        ],
        "features": [("Brand Identity", "Logos and systems that stay consistent."), ("Photography", "Natural light, honest moments."), ("Web Design", "Clean layouts that load fast."), ("Illustration", "Custom artwork with personality."), ("Art Direction", "A single vision across every touchpoint."), ("Motion", "Short animations that bring ideas alive.")],
        "ctas": ["See My Work", "Start a Project", "Say Hello"],
    },
    "education": {
        "keys": ["school", "course", "academy", "coaching", "tutor", "learning", "education", "college", "institute", "classes", "study", "university"],
        "mood": "friendly",
        "name_a": ["Bright", "Scholar", "Kiran", "Lumina", "Insight", "Gyan"],
        "name_b": ["Academy", "Institute", "Learning", "School", "Hub"],
        "headings": ["Learn Today, Lead Tomorrow", "Where Curiosity Grows", "Knowledge Made Simple", "Guided Learning That Works"],
        "taglines": ["Patient teachers, practical lessons.", "Every learner gets a path."],
        "paras": [
            "Our teachers break big ideas into small steps and check understanding often, so no student is left behind.",
            "Lessons mix clear explanations with practice and feedback, building confidence along with marks.",
            "From first-time learners to exam toppers, we adapt the pace and make progress easy to see.",
        ],
        "features": [("Expert Teachers", "Experienced mentors who love teaching."), ("Small Batches", "More attention for every student."), ("Practice Tests", "Prepare with real exam patterns."), ("Doubt Support", "Ask anything, anytime."), ("Flexible Timings", "Morning, evening and weekend slots."), ("Progress Reports", "Parents stay informed each month.")],
        "ctas": ["Enroll Now", "Book a Free Class", "View Courses"],
    },
    "shop": {
        "keys": ["shop", "store", "ecommerce", "fashion", "clothing", "jewellery", "jewelry", "boutique", "handmade", "dukaan", "products", "gifts", "furniture"],
        "mood": "playful",
        "name_a": ["Willow", "Indigo", "Marigold", "Thread", "Juniper", "Kora"],
        "name_b": ["Market", "Boutique", "Goods", "Collective", "Supply"],
        "headings": ["Find Something You'll Love", "Made Well, Meant to Last", "Little Luxuries for Everyday", "New Arrivals, Just for You"],
        "taglines": ["Curated pieces with honest prices.", "Delivered with care to your door."],
        "paras": [
            "Each product is chosen for quality, comfort and character, so you buy less and enjoy it more.",
            "We work directly with makers to keep prices fair and materials responsible, then ship quickly and carefully.",
            "Not happy? Send it back. We want every order to feel like a small celebration.",
        ],
        "features": [("Free Shipping", "On every order above a small minimum."), ("Easy Returns", "Change your mind within 30 days."), ("Secure Checkout", "Pay with confidence."), ("Gift Wrapping", "Ready to give, beautifully packed."), ("Handpicked Quality", "We test before we stock."), ("Member Offers", "Early access to new drops.")],
        "ctas": ["Shop Now", "Browse Collection", "Get 10% Off"],
    },
    "business": {
        "keys": [],
        "mood": "calm",
        "name_a": ["Prime", "Summit", "Clarity", "Anchor", "Meridian", "Vertex"],
        "name_b": ["Partners", "Group", "Solutions", "Services", "Co"],
        "headings": ["Solutions You Can Rely On", "Growing Together, Step by Step", "Quality Service, Every Time", "Built on Trust"],
        "taglines": ["Straightforward service and honest advice.", "Your success is our standard."],
        "paras": [
            "We listen first, then deliver clear plans, fair pricing and steady communication from start to finish.",
            "Our team brings years of experience and a simple promise: do the work properly and stand behind it.",
            "Customers return because we make things easy, keep our word and care about the outcome.",
        ],
        "features": [("Experienced Team", "Skilled people who know the details."), ("Transparent Pricing", "No surprises, ever."), ("Fast Response", "We reply the same day."), ("Custom Plans", "Solutions that fit your needs."), ("Quality Guarantee", "We fix it if it falls short."), ("Ongoing Support", "We stay with you after delivery.")],
        "ctas": ["Contact Us", "Get a Quote", "Learn More"],
    },
}

_STEM = re.compile(r"(ing|ers|er|es|s)$")


def tokenize(text):
    return [w for w in re.findall(r"[a-zA-Z]+", text.lower()) if w not in STOPWORDS and len(w) > 1]


def _stem(w):
    s = _STEM.sub("", w)
    return s if len(s) >= 3 else w


def detect_niche(tokens, model=None):
    scores = {}
    stems = {_stem(t) for t in tokens} | set(tokens)
    for name, data in NICHES.items():
        hit = sum(1 for k in data["keys"] if k in stems or _stem(k) in stems)
        if hit:
            scores[name] = hit
    if not scores and model:
        learned = model.niche_scores([t for t in tokens])
        best = max(sorted(learned), key=lambda n: learned[n])
        return best if learned[best] > 0 else "business"
    if not scores:
        return "business"
    return max(sorted(scores), key=lambda n: scores[n])


def extract_name(prompt, niche, rng):
    m = re.search(r"[\"“'‘]([^\"”'’]{2,40})[\"”'’]", prompt)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?:called|named|name is|naam)\s+([A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*){0,3})", prompt)
    if m:
        return m.group(1).strip()
    d = NICHES[niche]
    return f"{rng.choice(d['name_a'])} {rng.choice(d['name_b'])}"


def validate_content(c):
    """Raise ValueError if the generated content is unusable."""
    required = ["brand", "niche", "keywords", "hero_heading", "tagline", "about", "features", "cta_primary", "cta_secondary", "cta_text", "footer"]
    for k in required:
        if not c.get(k):
            raise ValueError(f"missing content field: {k}")
    if len(c["features"]) < 3:
        raise ValueError("need at least 3 features")
    if len({f["title"] for f in c["features"]}) != len(c["features"]):
        raise ValueError("duplicate feature titles")
    if len(c["hero_heading"]) > 70:
        raise ValueError("hero heading too long")
    leaves = []

    def walk(x):
        if isinstance(x, str):
            leaves.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk({k: v for k, v in c.items() if k != "generated_by"})
    if re.search(r"\{\{|\}\}|\$\{|\bTODO\b|lorem", " ".join(leaves), re.I):
        raise ValueError("placeholder text found")
    return True


def _templated(tm, niche, rng, want, slots):
    """Slots written from learned niche nouns inside grammatical frames (see template_model.py)."""
    if not tm or not tm.usable(niche):
        return {}
    page = tm.page(niche, rng, want)
    keep = {"hero_heading": ("hero_heading",), "tagline": ("tagline", "cta_text"), "about": ("about",), "features": ("features",)}
    return {k: page[k] for slot in slots if slot in keep for k in keep[slot]}


def _learned(model, niche, rng, want, slots):
    """Slots written by the trained n-gram model; any slot it cannot fill acceptably is left out."""
    if not model or niche not in model.d["niches"]:
        return {}
    out, used = {}, []

    def gen(slot, lo, hi, kind):
        # sentences must use only general or niche-core words; headings/CTAs are looser
        t = model.generate(niche, slot, rng, lo, hi, kind, want, banned=used, strict=(kind != "heading"))
        if t:
            used.append(t)
        return t

    if "hero_heading" in slots:
        out["hero_heading"] = gen("title", 2, 6, "heading")
    if "tagline" in slots:
        out["tagline"] = gen("sentence", 5, 12, "s")
    if "about" in slots:
        out["about"] = [" ".join(p) for p in ([gen("sentence", 8, 18, "s"), gen("sentence", 8, 18, "s")] for _ in range(2)) if all(p)]
    if "features" in slots:
        feats = []
        for _ in range(6):
            t, x = gen("feat_title", 2, 3, "heading"), gen("sentence", 6, 12, "s")
            if t and x:
                feats.append({"title": t, "text": x})
        out["features"] = feats
    if "ctas" in slots:
        out["ctas"] = model.pick_ctas(niche, rng, 2)
    return out


ALL_SLOTS = ("hero_heading", "tagline", "about", "features", "ctas")
# Measured on the current ~6k-sentence corpus: CTAs are good, other slots are not yet reliable.
DEFAULT_LEARNED = ("ctas", "hero_heading", "tagline", "about", "features")
NGRAM_SLOTS = ("ctas",)   # the n-gram generator is only trusted for CTAs; see ngram_model.py


def generate_content(prompt, seed=None, use_model=True, learned=DEFAULT_LEARNED):
    """learned: slots written by the trained model ("all" = every slot, experimental); the rest come from the bank."""
    rng = random.Random(seed)
    model = Model.load() if use_model else None
    tokens = tokenize(prompt)
    niche = detect_niche(tokens, model)
    d = NICHES[niche]
    brand = extract_name(prompt, niche, rng)
    brand_tokens = set(tokenize(brand))
    keywords = []
    for t in tokens:
        if t not in brand_tokens and t not in keywords:
            keywords.append(t)
    keywords = keywords[:6] or [niche]
    chosen = ALL_SLOTS if learned == "all" else learned
    L = _learned(model, niche, rng, set(keywords), chosen if learned == "all" else [x for x in chosen if x in NGRAM_SLOTS])
    if learned != "all":   # frame-based slots (default); "all" keeps the experimental n-gram text instead
        L.update(_templated(TemplateModel.load() if use_model else None, niche, rng, keywords, chosen))

    # bank fallbacks (always drawn so the rng stream stays aligned per seed)
    bank_feats = [{"title": t, "text": x} for t, x in rng.sample(d["features"], 6)]
    bank_about = rng.sample(d["paras"], 2)
    bank_ctas = rng.sample(d["ctas"], 2)
    bank_head, bank_tag = rng.choice(d["headings"]), rng.choice(d["taglines"])
    feats = list(L.get("features") or [])
    titles = {f["title"].lower() for f in feats}
    for f in bank_feats:
        if len(feats) >= 6:
            break
        if f["title"].lower() not in titles:
            feats.append(f)
    sources = {
        "hero_heading": "model" if L.get("hero_heading") else "bank",
        "tagline": "model" if L.get("tagline") else "bank",
        "about": "model" if len(L.get("about") or []) == 2 else "bank",
        "features": "%d/6 model" % len(L.get("features") or []),
        "niche_detection": "keywords + learned vocabulary" if model else "keywords",
        "ctas": "model" if L.get("ctas") else "bank",
    }
    content = {
        "brand": brand,
        "niche": niche,
        "mood": d["mood"],
        "keywords": keywords,
        "hero_heading": L.get("hero_heading") or bank_head,
        "tagline": L.get("tagline") or bank_tag,
        "about_title": f"About {brand}",
        "about": L["about"] if len(L.get("about") or []) == 2 else bank_about,
        "features_title": rng.choice(["What We Offer", "Why Choose Us", "What You Get"]),
        "features": feats,
        "stats": [{"value": f"{rng.randint(2, 15)}+", "label": "Years of experience"},
                  {"value": f"{rng.randint(5, 90) * 100}+", "label": "Happy customers"},
                  {"value": f"{rng.randint(94, 99)}%", "label": "Satisfaction rate"}],
        "cta_primary": (L.get("ctas") or bank_ctas)[0],
        "cta_secondary": (L.get("ctas") or bank_ctas)[1],
        "cta_text": L.get("cta_text") or next((t for t in d["taglines"] if t != (L.get("tagline") or bank_tag)), bank_tag),
        "cta_title": rng.choice(["Ready when you are", "Let's get started", "Your next step is one click away"]),
        "footer": f"© {brand}. All rights reserved.",
        "generated_by": sources,
    }
    validate_content(content)
    return content
