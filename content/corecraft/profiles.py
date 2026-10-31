"""Kinds of business (the voice) and sub-niches (the vocabulary).

kind    : food, health, beauty, fitness, retail, software, education, home, trades, travel, events, creative, pro, org
profile : a sub-niche inside a kind: Italian / North Indian / South Indian / Chinese / street food / bakery / tea cafe / bar,
          dental / skin / eye / physio, crossfit / yoga / zumba, kurti / saree / electronics / books ...
A profile carries its own dishes (lexicon.py), steps and FAQ, and a list of words that must never appear on its pages.
"""
import re

from .lexicon import LEX, describe
from .profile_vocab import learned_score

TYPE_KIND = {
    # food
    "restaurant": "food", "cafe": "food", "bakery": "food", "sweets": "food", "catering": "food", "icecream": "food",
    # health
    "dental": "health", "clinic": "health", "ayurveda": "health", "physio": "health", "vet": "health", "pharmacy": "health", "skin": "health", "eye": "health",
    # beauty
    "salon": "beauty", "spa": "beauty", "mehendi": "beauty", "tattoo": "beauty",
    # fitness
    "gym": "fitness", "yoga": "fitness", "sports": "fitness",
    # retail
    "clothing": "retail", "jewellery": "retail", "furniture": "retail", "mobile": "retail", "grocery": "retail", "books": "retail", "gifts": "retail",
    "petshop": "retail", "optical": "retail", "shop": "retail", "autosales": "retail",
    # software
    "software": "software",
    # education
    "school": "education", "playschool": "education", "driving": "education", "music": "education", "robotics": "education",
    # home services and trades
    "cleaning": "home", "movers": "home", "landscape": "home", "courier": "home", "security": "home",
    "plumbing": "trades", "electrician": "trades", "painting": "trades", "carpentry": "trades", "ac": "trades", "construction": "trades", "solar": "trades",
    "welding": "trades", "tyres": "trades", "garage": "trades", "tailor": "trades",
    # travel, events, creative
    "travel": "travel", "hotel": "travel", "taxi": "travel",
    "events": "events", "tenthouse": "events", "gaming": "events",
    "photography": "creative", "design": "creative", "printing": "creative", "pottery": "creative",
    # professional services and community
    "law": "pro", "accounting": "pro", "architect": "pro", "interior": "pro", "realestate": "pro", "insurance": "pro", "marketing": "pro",
    "consulting": "pro", "recruitment": "pro", "coworking": "pro", "astrology": "pro", "visa": "pro",
    "ngo": "org",
}
KINDS = ["food", "health", "beauty", "fitness", "retail", "software", "education", "home", "trades", "travel", "events", "creative", "pro", "org"]
SERVICE_KINDS = {"pro", "home", "org"}   # only these may say "we help people with ..."

# profile id -> dict(kind, types, triggers, mains, main_default, label)
PROFILES = {
    "italian": {"kind": "food", "types": ["restaurant"], "triggers": "italian pizza pizzeria pasta ristorante trattoria tiramisu risotto lasagna lasagne gelato wood-fired fired calzone focaccia", "mains": ["pizza", "pasta", "risotto"], "main_default": "dish"},
    "north_indian": {"kind": "food", "types": ["restaurant"], "triggers": "north punjabi mughlai tandoori butter paneer naan makhani biryani dhaba kebab thali dal rajma chole bhature", "mains": ["curry", "biryani", "thali"], "main_default": "dish"},
    "south_indian": {"kind": "food", "types": ["restaurant"], "triggers": "south dosa idli vada sambar uttapam udupi rasam appam pongal upma filter", "mains": ["dosa", "idli", "meals"], "main_default": "tiffin"},
    "chinese": {"kind": "food", "types": ["restaurant"], "triggers": "chinese indo hakka manchurian momos schezwan noodles dumplings dim sum wok", "mains": ["noodles", "momos", "rice"], "main_default": "dish"},
    "street_food": {"kind": "food", "types": ["restaurant"], "triggers": "street chaat puri golgappa pani bhaji vada pav bhel samosa kachori dabeli stall", "mains": ["chaat", "puri", "pav"], "main_default": "chaat"},
    "bar": {"kind": "food", "types": ["restaurant"], "triggers": "bar pub lounge cocktails cocktail mocktails beer brewery taproom whisky wine", "mains": ["cocktail", "beer", "drink"], "main_default": "drink"},
    "bakery": {"kind": "food", "types": ["bakery"], "triggers": "bakery cake cakes cupcakes pastry pastries bread brownies cookies sourdough", "mains": ["cake", "bread", "pastry"], "main_default": "bake"},
    "tea_cafe": {"kind": "food", "types": ["cafe"], "triggers": "chai tea coffee cafe café latte cappuccino maska", "mains": ["chai", "coffee"], "main_default": "brew"},
    "dental": {"kind": "health", "types": ["dental"], "triggers": "dental dentist teeth tooth braces implants root canal whitening", "mains": ["treatment"], "main_default": "treatment"},
    "skin": {"kind": "health", "types": ["skin"], "triggers": "skin dermatologist acne pigmentation derma hair fall", "mains": ["treatment"], "main_default": "treatment"},
    "eye": {"kind": "health", "types": ["eye"], "triggers": "eye eyes cataract lasik retina glaucoma ophthalmology", "mains": ["eye test"], "main_default": "eye test"},
    "physio": {"kind": "health", "types": ["physio"], "triggers": "physio physiotherapy rehab rehabilitation pain", "mains": ["session"], "main_default": "session"},
    "crossfit": {"kind": "fitness", "types": ["gym"], "triggers": "crossfit wod wods olympic lifting box", "mains": ["class"], "main_default": "class"},
    "yoga": {"kind": "fitness", "types": ["yoga"], "triggers": "yoga meditation pranayama hatha vinyasa", "mains": ["class"], "main_default": "class"},
    "zumba": {"kind": "fitness", "types": ["gym", "music"], "triggers": "zumba aerobics dance fitness hip hop bollywood", "mains": ["class"], "main_default": "class"},
    "kurti": {"kind": "retail", "types": ["clothing"], "triggers": "kurti kurtis kurta anarkali palazzo chikankari dupatta", "mains": ["kurti"], "main_default": "piece"},
    "saree": {"kind": "retail", "types": ["clothing"], "triggers": "saree sarees sari banarasi kanjivaram bandhani georgette", "mains": ["saree"], "main_default": "piece"},
    "electronics": {"kind": "retail", "types": ["mobile"], "triggers": "electronics laptop laptops television tv tvs smartphone smartphones headphones speakers smartwatch appliances", "mains": ["phone", "laptop"], "main_default": "product"},
    "books": {"kind": "retail", "types": ["books"], "triggers": "book books stationery textbooks novels comics notebooks", "mains": ["book"], "main_default": "book"},
    "autosales": {"kind": "retail", "types": ["autosales"], "triggers": "bike bikes motorcycle motorcycles scooter scooters showroom dealer", "mains": ["bike"], "main_default": "bike"},
    "tyres": {"kind": "trades", "types": ["tyres"], "triggers": "tyre tyres alignment balancing puncture wheel", "mains": ["tyre"], "main_default": "job"},
    "robotics": {"kind": "education", "types": ["robotics"], "triggers": "robotics robot arduino coding drone stem", "mains": ["workshop"], "main_default": "workshop"},
    "pottery": {"kind": "creative", "types": ["pottery"], "triggers": "pottery ceramic ceramics clay wheel kiln glazing", "mains": ["piece"], "main_default": "piece"},
}
PROFILE_LABEL = {
    "italian": "Italian restaurant", "north_indian": "North Indian restaurant", "south_indian": "South Indian restaurant", "chinese": "Chinese restaurant",
    "street_food": "Street food", "bar": "Bar", "bakery": "Bakery", "tea_cafe": "Tea and coffee cafe",
}
FOOD_ALL = ["italian", "north_indian", "south_indian", "chinese", "street_food", "bar", "bakery", "tea_cafe"]


def _tok(s):
    return {t for t in re.findall(r"[a-z]+", s.lower()) if len(t) > 2}


def _profile_vocab(pid):
    toks = set()
    for k in LEX.get(pid, {}):
        toks |= _tok(k)
    return toks


def _profile_desc_vocab(pid):
    toks = set()
    for v in LEX.get(pid, {}).values():
        toks |= _tok(v)
    return toks


GENERIC_OK = set("birthday custom weekend live happy hour music kids open gym strong small plates bar snacks wine beer cakes cake bread sandwiches coffee tea eggless egg"
                 " classes class plans session sessions lunch dinner breakfast brunch dessert desserts sweet sweets drinks drink veg vegetarian".split())


_VOCAB = {pid: _profile_vocab(pid) for pid in PROFILES}


def foreign_words(pid):
    """Dish and product words that belong only to OTHER profiles of the same kind (never to this one)."""
    kind = PROFILES[pid]["kind"]
    own = _VOCAB.get(pid, set()) | _tok(PROFILES[pid]["triggers"]) | _profile_desc_vocab(pid) | GENERIC_OK
    others = set()
    for q, p in PROFILES.items():
        if q != pid and p["kind"] == kind:
            others |= _VOCAB.get(q, set()) | {t for t in _tok(p["triggers"]) if t in _VOCAB.get(q, set())}
    shared = set()
    for q in PROFILES:
        if q != pid and PROFILES[q]["kind"] == kind and _VOCAB.get(q, set()) & _VOCAB.get(pid, set()):
            shared |= _VOCAB[q] & _VOCAB[pid]
    # a word that two profiles share (rice, paneer, cake, chicken, coffee) is not foreign to either
    common = {t for t in others if sum(1 for q in PROFILES if PROFILES[q]["kind"] == kind and t in _VOCAB.get(q, set())) >= 2}
    generic = set("with and the for fresh hot cold sweet spicy crisp soft served made small plates fried baked steamed grilled sauce spiced sweet rice milk butter cream cheese".split())
    return {t for t in others if t not in own and t not in common and t not in generic and t not in shared}


FOREIGN = {pid: foreign_words(pid) for pid in PROFILES}


def pick_profile(type_id, prompt_text, items):
    """Sub-niche for this business: trigger words in the prompt, plus items that the profile's lexicon knows."""
    words = _tok(prompt_text) | {w for w in re.findall(r"[a-z]+", prompt_text.lower())}
    best, best_score = None, 0.0
    for pid, p in PROFILES.items():
        if type_id not in p["types"]:
            continue
        trig = set(p["triggers"].split())
        score = 1.5 * len(words & trig)
        score += 2.0 * sum(1 for it in items if describe(it, pid))
        score += learned_score(pid, words)   # words that real pages of this sub-niche use (learned from the crawl)
        # a prompt that names a kind ("bakery", "bar") but also other cuisines keeps its own profile only if it hits clearly
        if score > best_score:
            best, best_score = pid, score
    return best


def signature(profile, items):
    """The noun used in step titles such as "Choose your pizza": from the user's items when possible."""
    if not profile:
        return None
    p = PROFILES[profile]
    low = " ".join(items).lower()
    for m in p["mains"]:
        if m in low:
            return m
    return p["main_default"]
