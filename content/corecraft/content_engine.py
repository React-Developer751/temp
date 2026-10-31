"""Content AI Engine: prompt -> niche, keywords, validated copy. Uses json, random, re only."""
import json
import random
import re

from .ngram_model import Model, tokens as _model_tokens
from .template_model import TemplateModel
from . import lang_hi as hi_mod
from . import detector as detector_mod
from . import typos
from .facts import OFFER_RE, extract_facts, find_offers, hours_for_english
from .profiles import PROFILE_LABEL, TYPE_KIND, pick_profile
from .writer import write_page, title_case as card_title
from .validators import validate_page
from .writer_hi import write_page_hi
import zlib
from .business_types import T as TYPES, detect_type, fallback_items, infer_kind, parse_hindi, parse_prompt
from .kind_content import (ANY, FAQ_COMMON, FAQ_LAST, FAQ_THIRD, HIGHLIGHTS, KIND_COMMON, KIND_NEUTRAL, NAME_BANK, STEPS)

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
    return [w for w in re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower()) if w not in STOPWORDS and len(w) > 1]


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
    required = ["brand", "niche", "keywords", "hero_heading", "tagline", "about", "features", "cta_primary", "cta_secondary", "cta_text", "footer",
                "highlights", "steps", "faq", "eyebrow"]
    for k in required:
        if not c.get(k):
            raise ValueError(f"missing content field: {k}")
    if len(c["features"]) < 3:
        raise ValueError("need at least 3 features")
    if len({f["title"] for f in c["features"]}) != len(c["features"]):
        raise ValueError("duplicate feature titles")
    if len(c["hero_heading"]) > 80:
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
    walk({k: v for k, v in c.items() if k not in ("generated_by", "needs_review", "ui")})
    blob = " ".join(leaves)
    if re.search(r"\{\{|\}\}|\$\{|\bTODO\b|lorem|[{}]", blob, re.I):
        raise ValueError("placeholder text found")
    for leaf in leaves:
        if c.get("lang") != "hi" and re.search(r"\b(\w+) \1\b", leaf, re.I):
            raise ValueError("repeated word found in %r" % leaf)
    for st in c.get("stats", []):
        if not st.get("value") or not st.get("label"):
            raise ValueError("incomplete stat")
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
DEFAULT_LEARNED = ("ctas", "hero_heading", "tagline", "about", "features")
NGRAM_SLOTS = ("ctas",)   # the n-gram generator is only trusted for CTAs; see ngram_model.py
GENERAL_POOL = "services solutions packages options consultations plans assessments support".split()
OWN_NAME_BANK = {"restaurant", "gym", "software", "photography", "school", "shop"}   # types that keep the original name banks


def _name(prompt, t, niche, rng):
    m = re.search(r"[\"“'‘]([^\"”'’]{2,40})[\"”'’]", prompt)
    if m:
        return m.group(1).strip(), False
    m = re.search(r"(?:called|named|name is|naam)\s+([A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*){0,3})", prompt)
    if m:
        return m.group(1).strip(), False
    if t and t["id"] not in OWN_NAME_BANK:
        bank = NICHES[niche]["name_a"] if niche in NICHES else NAME_BANK.get(niche, NAME_BANK["pro"])
        return f"{rng.choice(bank)} {t['label'].split('&')[-1].strip()}", True
    if niche in NICHES:
        d = NICHES[niche]
        return f"{rng.choice(d['name_a'])} {rng.choice(d['name_b'])}", True
    return f"{rng.choice(NAME_BANK['pro'])} Co", True


UI_EN = {
    "lang": "en", "about": "About", "gallery": "Gallery", "faq": "FAQ", "contact": "Contact", "call": "Call", "email": "Email", "based_in": "Based in",
    "pricing": "Pricing", "testimonials": "What customers say", "team": "Our team", "hours": "Opening hours", "address": "Address",
    "where": "Where we work", "years": "Years of experience", "since": "Serving since", "features_title": "What We Offer",
    "steps_title": "How It Works", "faq_title": "Frequently Asked Questions", "rights": "All rights reserved.", "about_title": "About %s", "about_us": "About us",
}
HI_FILLERS = ["विशेषज्ञ सलाह", "साफ़ जानकारी", "आसान संपर्क"]
EN_FILLERS = ["expert advice", "reliable service", "easy contact"]


def _lang_of(prompt, lang):
    if lang in ("en", "hi"):
        return lang
    letters = [c for c in prompt if c.isalpha()]
    dev = [c for c in letters if "\u0900" <= c <= "\u097f"]
    return "hi" if letters and len(dev) / len(letters) > 0.3 else "en"


def _faq(niche, items, hi=False):
    common, third, last = (hi_mod.FAQ_COMMON, hi_mod.FAQ_THIRD, hi_mod.FAQ_LAST) if hi else (FAQ_COMMON, FAQ_THIRD, FAQ_LAST)
    faq = list(common)
    if items:
        goods = niche in ("shop", "store", "restaurant")
        q, a = (hi_mod.FAQ_ITEM_GOODS if goods else hi_mod.FAQ_ITEM) if hi else ("Do you offer {item}?", "Yes, {item} is one of the things we do. Get in touch for details.")
        faq.append((q.format(item=items[0]), a.format(item=items[0])))
    faq += [third.get(niche, third["pro"]), last]
    return [{"q": q, "a": a} for q, a in faq]


def _clean_user_sections(facts):
    """Sections the user supplied (prices, reviews, team, hours, address): kept verbatim, never invented."""
    out, issues = {}, []
    for key, fields in (("prices", ("name", "price")), ("testimonials", ("name", "text")), ("team", ("name", "role"))):
        rows = facts.get(key) or []
        good = [{f: str(r[f]).strip() for f in fields if r.get(f)} for r in rows if isinstance(r, dict)]
        good = [r for r in good if len(r) == len(fields)]
        if rows and len(good) != len(rows):
            issues.append("Some '%s' entries were skipped: each needs %s." % (key, " and ".join(fields)))
        if good:
            out[key] = good
    hours = facts.get("hours")
    if isinstance(hours, (list, tuple)):
        hours = [str(h).strip() for h in hours if str(h).strip()]
    elif hours:
        hours = [str(hours).strip()]
    if hours:
        out["hours"] = hours
    for key in ("address", "whatsapp"):
        if facts.get(key):
            out[key] = str(facts[key]).strip()
    return out, issues


def title_case(w):
    return " ".join(x if x.isupper() else x[:1].upper() + x[1:] for x in w.split())


from .template_data import NICHE as _NICHE_FRAMES   # noqa: E402

NICHE_KEYS = set(_NICHE_FRAMES)


# ---------------------------------------------------------------------------------------------------------------------
# The writer path: facts -> kind (voice) + profile (vocabulary) -> text that passes the page validators
# ---------------------------------------------------------------------------------------------------------------------
NICHE_KIND = {"restaurant": "food", "fitness": "fitness", "tech": "software", "portfolio": "creative", "education": "education", "shop": "retail", "store": "retail",
              "business": "home", "care": "health", "pro": "pro", "hosting": "travel", "org": "org"}
TYPE_TYPICAL = {   # what a business of this type usually offers, used (and flagged) only when the person listed no services
    "restaurant": ["Starters", "Mains", "Desserts", "Drinks"], "cafe": ["Coffee", "Tea", "Snacks", "Desserts"], "bakery": ["Cakes", "Pastries", "Bread", "Cookies"],
    "clothing": ["Kurtis", "Sarees", "Dresses", "Accessories"], "jewellery": ["Rings", "Necklaces", "Earrings", "Bracelets"],
    "school": ["Classes", "Doubt sessions", "Practice tests", "Study material"], "photography": ["Portraits", "Weddings", "Events", "Albums"],
    "design": ["Logos", "Posters", "Brand identity", "Social media"], "gym": ["Group classes", "Personal training", "Strength training", "Cardio"],
    "software": ["Automation", "Reporting", "Integrations", "Team workspace"], "shop": ["Collections", "Gift ideas", "New arrivals", "Bestsellers"],
}
FILLER_LINES = {"expert advice": "Ask your questions and get a straight answer.", "reliable service": "Tell us what you need and when, and we'll confirm what's possible.",
                "easy contact": "Call or message us and we'll reply."}
MAX_ATTEMPTS = 80


def stable_seed(prompt, facts):
    return zlib.crc32(json.dumps([prompt.strip().lower(), facts or {}], sort_keys=True, ensure_ascii=False, default=str).encode("utf-8"))


def _typical_for(t, tid, rng):
    pool = (t["offers"] if t and t["offers"] else None) or TYPE_TYPICAL.get(tid) or []
    pool = [card_title(x) if x.islower() else x for x in pool]
    if len(pool) > 5:
        pool = rng.sample(pool, 5)
    return pool


MAX_PROMPT = 1500
FREE_MAIL = {"gmail", "yahoo", "hotmail", "outlook", "rediffmail", "icloud", "proton", "protonmail", "live", "aol", "ymail", "zoho"}


def clean_text(x, limit=MAX_PROMPT):
    """What a person types is data: no markup or template characters, one tidy line, bounded length."""
    x = re.sub(r"<[^>]*>", " ", str(x))
    x = re.sub(r"\b(in|at|near|from|for|with|and|aur|ya|or)\s*\n\s*", r"\1 ", x, flags=re.I)   # "bakery\nin\nDelhi"
    x = re.sub(r"\s*\n\s*(in|at|near)\b", r" \1", x, flags=re.I)
    x = re.sub(r"\s*\n\s*", ", ", x.strip())
    x = re.sub(r"[{}\[\]\\`$<>^~]+", " ", x)
    x = "".join(ch for ch in x if ch.isprintable() or ch == " ")
    x = re.sub(r"\b(\w{30})\w+", r"\1", x)   # one endless word cannot break a heading
    x = re.sub(r"[ \t]+", " ", x).strip(" ,")
    return x[:limit].rsplit(" ", 1)[0] if len(x) > limit else x


def _clean_facts(v):
    if isinstance(v, str):
        return clean_text(v, 300)
    if isinstance(v, list):
        return [_clean_facts(i) for i in v]
    if isinstance(v, dict):
        return {k: _clean_facts(i) for k, i in v.items()}
    return v


def _normalize_facts(facts):
    """Facts from a JSON file or a form may have the wrong shape: keep what is usable, drop the rest."""
    if not isinstance(facts, dict):
        return None
    out = dict(facts)
    if isinstance(out.get("services"), str):
        out["services"] = [x.strip() for x in out["services"].split(",") if x.strip()]
    for k in ("services", "offers", "prices", "testimonials", "team"):
        if k in out and not isinstance(out[k], list):
            out.pop(k)
    for k in ("name", "city", "phone", "email", "address", "whatsapp", "years", "audience", "tagline"):
        if k in out and not isinstance(out[k], (str, int)):
            out.pop(k)
    return out


def generate_content(prompt, seed=None, use_model=True, learned=DEFAULT_LEARNED, facts=None, lang=None):
    """prompt (+ optional facts) -> page content for any small business. Always returns a valid page or raises ValueError("prompt is empty").
    Input is cleaned first (markup, braces, newlines, endless words); if a page still cannot pass the validators the writer retries
    on the plain words of the prompt and says so in needs_review."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt is empty")
    cleaned = clean_text(prompt)
    if not cleaned:
        raise ValueError("prompt is empty")
    facts = _normalize_facts(_clean_facts(facts)) if facts else None
    cleaned, typos_fixed, typos_hints = typos.fix(cleaned)
    guess = detector_mod.detect(cleaned)[0]
    if guess:   # second pass, inside the vocabulary of the detected trade ("bridal makup" in a salon, "cardeo" in a gym)
        cleaned, more_fixed, typos_hints = typos.fix(cleaned, typos.scope_words(guess, cleaned))
        typos_fixed += more_fixed
    try:
        c = _generate_once(cleaned, seed, use_model, learned, facts, lang)
        if typos_fixed:
            c["needs_review"] = list(c.get("needs_review", [])) + ["Corrected likely typing mistakes: %s. Check these are right." % ", ".join("'%s' to '%s'" % wr for wr in typos_fixed[:8])]
        if typos_hints:
            c["needs_review"] = list(c.get("needs_review", [])) + ["Left as typed, in case they are real names: %s." % ", ".join("'%s' (maybe '%s')" % wr for wr in typos_hints[:6])]
        return c
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        plain = " ".join(re.findall(r"[A-Za-z\u0900-\u097F]{2,20}", cleaned)[:12])
        if not plain:
            plain = "small business"
        c = _generate_once(plain, seed, use_model, learned, None, lang)
        c["needs_review"] = list(c.get("needs_review", [])) + ["The prompt could not be read cleanly, so only its plain words were used. Rewrite it with the business type, name, city and services."]
        return c


def _generate_once(prompt, seed=None, use_model=True, learned=DEFAULT_LEARNED, facts=None, lang=None):
    """prompt (+ optional facts) -> page content for any small business, English, Hinglish or Hindi.

    Reads the facts the person wrote (name, city, services/dishes, offers, hours, prices, phone), finds the business type and the
    sub-niche (Italian, dental, kurti ...), writes the copy in the voice of that kind of business, and only returns a page whose text
    passes the validators (no placeholders, no repeated 6-word spans, no other niche's words, every named service present).
    Nothing is invented: what was not given is listed in `missing`."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt is empty")
    facts = facts or {}
    lang = _lang_of(prompt, lang)
    hi = lang == "hi"
    base = stable_seed(prompt, facts)   # the prompt itself picks the wording, so two businesses never read alike even with the same explicit seed
    seed = base if seed is None else zlib.crc32(("%d:%s" % (base, seed)).encode())
    tid, conf_label, det = detector_mod.detect(prompt)
    review = []
    if tid and not det.get("use", True):   # no keyword evidence and a weak model guess: do not write a niche page on a guess
        review.append("The business type could not be read from your words; the closest guess was '%s' (low confidence) and was not used." % TYPES[tid]["label"])
        tid = None
    t = TYPES.get(tid)
    inferred_label = None
    if t:
        niche = t["niche"]
    else:
        niche, inferred_label, _ = infer_kind(prompt)
        if niche:
            review.append("Business type is not in the list; the '%s' copy family was inferred from your words. Say the type (e.g. 'dental clinic') for better copy." % niche)
        else:
            niche = "pro"
            review.append("Business type was not recognised, so the copy is general. Add the type (e.g. 'dental clinic') or list your services.")
    kind = TYPE_KIND.get(tid) or NICHE_KIND.get(niche, "pro")
    F = extract_facts(prompt, facts, t["keys"] if t else (), t["label"] if t else (inferred_label or ""))
    if not hi and F.get("hours"):
        F["hours"] = hours_for_english(F["hours"])
    items = list(F["items"])
    for segs in F.get("cut") or []:
        review.append("Services typed without commas were read as: %s. If that is wrong, put a comma between your services." % " | ".join(segs))
    place = F["city"]
    profile = pick_profile(tid, prompt + " " + " ".join(items), items) if t else None
    label = (hi_mod.LABELS.get(tid, hi_mod.DEFAULT_LABEL) if hi else (PROFILE_LABEL.get(profile) or (t["label"] if t else (inferred_label or "Business"))))
    if tid == "shop" and not hi and not re.search(r"\bonline|e-?commerce|d2c|web\s*store|website", prompt, re.I):
        label = "Store"   # a hardware or toy shop is not an \"Online Store\"
    rng0 = random.Random(seed)
    invented = not F["name"]
    brand = F["name"] if not invented else label + (", " + place if place else "")   # no made-up name: the heading just says what the business is and where
    if invented:
        guess = ""
        dom = re.search(r"@([\w-]+)\.", F.get("email") or "")
        if dom and dom.group(1).lower() not in FREE_MAIL:
            guess = " Your email address suggests '%s'." % dom.group(1).capitalize()
        review.append("No business name was given, so the heading is '%s' (not a name). Add your business name to replace it.%s" % (brand, guess))
    if t and conf_label != "high":
        review.append("Business type '%s' was detected with %s confidence. If it is wrong, say what kind of business it is (e.g. 'dental clinic')." % (t["label"], conf_label))

    # promote a typical offering that the prompt itself names ("... repair and accessories shop")
    if t and t["offers"] and not facts.get("services") and len(items) < 3:
        plain_prompt = prompt.lower()
        for _, rx, _, _ in OFFER_RE:
            plain_prompt = rx.sub(" ", plain_prompt)   # "first class free" is an offer, not the service "classes"
        said = set(re.findall(r"[a-z]+", plain_prompt)) - set(re.findall(r"[a-z]+", (F["name"] or "").lower()))
        stem = lambda x: x if x.endswith("ss") else (x[:-2] if x.endswith("es") and len(x) > 4 else (x[:-1] if x.endswith("s") else x))   # noqa: E731
        given = {stem(x) for i in items for x in re.findall(r"[a-z]+", i.lower())}
        for w in t["offers"]:
            head = w.split()[-1]
            if re.search(r"\b(?:i|we|to|will|can)\s+(?:also\s+)?" + re.escape(stem(head)), plain_prompt):
                continue   # "I design logos": "design" is what they do, not a service called "designs"
            if stem(head) in given or head.rstrip("s") in given:
                continue   # the person already named it ("pipe restoration" gives no extra "pipes")
            if (head in said or stem(head) in said or head[:-1] in said) and w not in items and not any(w in i or i in w for i in items):
                items.append(w)
        items = items[:8]
    if not t and not items:
        items = fallback_items(prompt, place)
    real_items = list(items)
    fillers, typical = [], []
    if hi and len(real_items) < 3:   # Hindi pages never mix in English offerings: neutral Hindi service names fill the gap
        fillers = [x for x in HI_FILLERS if x not in real_items][:3 - len(real_items)]
        review.append("Few services were given, so neutral Hindi service names were added. List your own services for a better page.")
    elif t is None and len(real_items) < 3:
        fillers = [x for x in EN_FILLERS if x not in real_items][:3 - len(real_items)]
        review.append("Only %d service(s) were given, so neutral service names were added. List 3 or more of your own services for a better page." % len(real_items))
    elif len(real_items) < 3 and not hi:
        typical = [x for x in _typical_for(t, tid, rng0) if x.lower() not in {i.lower() for i in real_items}][:max(3, 5 - len(real_items))]
    F2 = dict(F)
    F2["items"] = real_items
    allowed_text = prompt + " " + json.dumps(facts, ensure_ascii=False, default=str)
    best, best_issues = None, None
    for attempt in range(MAX_ATTEMPTS):
        rng = random.Random(seed * 1000003 + attempt)
        if hi:
            page = write_page_hi(kind=kind, label=label, facts=F2, name=None if invented else brand, rng=rng, extra_cards=fillers, type_id=tid)
        else:
            page = write_page(kind=kind, label=label, type_id=tid, profile=profile, facts=F2, name=None if invented else brand, rng=rng, typical=typical or None,
                              extra_cards=fillers, filler_lines=FILLER_LINES)
        issues = validate_page(dict(page), kind, profile, allowed_text, real_items,
                               exempt=" ".join([str(F.get(k) or "") for k in ("hours", "address", "phone", "email", "name")] + [str(facts.get("hours") or ""), str(facts.get("address") or "")]))
        if best is None or len(issues) < len(best_issues):
            best, best_issues = page, issues
        if not issues:
            break
    page = best
    if best_issues:
        review.append("Text quality check not fully satisfied after %d tries: %s" % (MAX_ATTEMPTS, "; ".join(best_issues[:3])))
    if typical and page.get("used_typical"):
        review.append("Typical %s offerings were used for: %s. List your real services (3 or more) to replace them." % (label.lower(), ", ".join(page["used_typical"])))
    if place is None:
        review.append("No location was given; add a city to make the copy local.")

    ui = hi_mod.UI if hi else UI_EN
    stats = []
    if F["years"]:
        m = re.search(r"\d+", F["years"])
        stats.append({"value": (m.group(0) + "+") if m and len(m.group(0)) <= 2 else (m.group(0) if m else F["years"]), "label": ui["years"] if m and len(m.group(0)) <= 2 else ui["since"]})
    if place:
        stats.append({"value": place, "label": ui["where"]})
    if F["hours"]:
        stats.append({"value": F["hours"], "label": "खुलने का समय" if hi else "Open"})
    contact = {k: F[k] for k in ("phone", "email") if F.get(k)}
    if place:
        contact["place"] = place
    user_sections, issues = _clean_user_sections(facts)
    review += issues
    if F.get("address") and not user_sections.get("address"):
        user_sections["address"] = F["address"]
    for k in ("address", "whatsapp"):
        if user_sections.get(k):
            contact[k] = user_sections[k]
    hours_lines = user_sections.get("hours") or ([F["hours"]] if F["hours"] else [])
    if hours_lines:
        contact["hours"] = hours_lines
    prices = F["prices"] or user_sections.get("prices") or []
    brand_tokens = set(tokenize(brand))
    keywords = [w for w in dict.fromkeys(tokenize(prompt)) if w not in brand_tokens][:6] or [niche]
    mood = t["mood"] if t else (NICHES[niche]["mood"] if niche in NICHES else "calm")
    used = {k: v for k, v in {"name": F["name"], "city": place, "services": real_items, "offers": [o["text"] for o in F["offers"]], "hours": F["hours"], "prices": prices,
                              "phone": F["phone"], "email": F["email"], "years": F["years"]}.items() if v}
    facts_used = {k: {"value": v, "source": F["source"].get({"services": "items"}.get(k, k), "prompt")} for k, v in used.items()}
    missing = [k for k in ("name", "city", "services", "offers", "hours", "prices", "phone", "email", "address") if k not in used and not (k == "address" and user_sections.get("address"))]
    content = {
        "brand": brand, "niche": niche, "kind": kind, "profile": profile or "", "business_type": tid or "general", "type_label": label,
        "lang": lang, "ui": ui, "mood": mood, "keywords": keywords,
        "eyebrow": label + (" \u00b7 " + place if place else ""), "location": place or "", "audience": F["audience"] or "",
        "hero_heading": page["hero_heading"], "tagline": page["tagline"], "about_title": (ui["about_title"] % brand) if not invented else ui["about_us"], "about": page["about"],
        "features_title": page["features_title"], "features": page["features"], "highlights": page["highlights"],
        "stats_title": page["stats_title"], "stats": stats, "steps_title": page["steps_title"], "steps": page["steps"],
        "faq_title": page["faq_title"], "faq": page["faq"], "blog_title": page["blog_title"], "blog": page["blog"], "contact": contact,
        "cta_primary": page["cta_primary"], "cta_secondary": page["cta_secondary"], "cta_text": page["cta_text"], "cta_title": page["cta_title"],
        "footer": "\u00a9 %s. %s" % (brand, ui["rights"]),
        "offers": [{"id": o["id"], "text": o["text"]} for o in F["offers"]], "hours": F["hours"] or "", "prices": prices,
        "facts_used": facts_used, "missing": missing,
        "generated_by": {"business_type": ("%s (confidence %s)" % (tid, conf_label)) if tid else ("inferred: %s" % niche if inferred_label else "not recognised"),
                         "items_from_prompt": real_items, "place": place or "", "mode": "strict (your phrases only)" if (len(real_items) >= 3 or not t) else "typical offerings fill gaps",
                         "copy": "frames + user phrases" + (" + n-gram" if learned == "all" else ""), "profile": profile or "", "kind": kind},
        "needs_review": review,
    }
    if user_sections.get("prices") or prices:
        content["pricing"] = user_sections.get("prices") or [{"name": p["name"], "price": p["price"]} for p in prices]
    if user_sections.get("testimonials"):
        content["testimonials"] = user_sections["testimonials"]
    if user_sections.get("team"):
        content["team"] = user_sections["team"]
    validate_content(content)
    return content
