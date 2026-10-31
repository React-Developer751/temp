"""Niche packs: the text of ONE kind of business in the shape the "Content AI" spec asks for (heroTitles, features, steps, faq, pricing, menu ...).
build_pack(niche) -> dict in the spec's shape, with the literal {brand} placeholder. render_pack(pack, brand, city) fills the placeholder for a page.
Everything is written from the niche's own services and the hand-written text banks in pack_families_*.py. No numbers of customers, years, ratings or awards are
ever written; pack_check.py enforces that.

Niche lists (both in the package, built by training/build_niches.py):
- corecraft/data/niches.json, the default: the 99 niches + 20 business types of the owner's spec document ("Content AI: training prompts").
- corecraft/data/author_niches.json: the author's 77 business types. Its types that no spec niche covers (optical shop, tyre shop, pottery classes ...) answer the
  requests the default list does not know (see fallback_niches()).
CORECRAFT_NICHE_FILE=author (or a path to a file in the same format), or use_niche_file(...), switches the list for the whole process."""
import json
import os
import re
import threading
import zlib
from pathlib import Path

from . import pack_families_a as FA
from . import pack_families_b as FB
from .grammar import a_an, forms
from .pack_niches import FAMILY_PRICES

NICHE_FILE = Path(__file__).resolve().parent / "data" / "niches.json"   # the default: the spec's 99 niches + 20 types
AUTHOR_FILE = NICHE_FILE.with_name("author_niches.json")   # the author's 77 business types
NAMED = {"author": AUTHOR_FILE, "spec": NICHE_FILE, "default": NICHE_FILE}
_override = []
_lock = threading.Lock()
FAMILIES = {"home": FA.HOME, "auto": FA.AUTO, "project": FA.PROJECT, "retail": FA.RETAIL, "food": FA.FOOD, "food_order": FA.FOOD_ORDER, "clinic": FA.CLINIC, "session": FA.SESSION,
            "pro": FB.PRO, "edu": FB.EDU, "events": FB.EVENTS, "stay": FB.STAY, "property": FB.PROPERTY, "nonprofit": FB.NONPROFIT, "software": FB.SOFTWARE}
_cache = {}
FAQ_TAILS = ["This applies to {s1}, {s2} and everything else we offer.", "It is the same for {s2} as it is for {s1}.", "That goes for {s3} and {s4} too.",
             "Ask us about {s5} or {s6} and the answer is the same.", "The same approach applies to {s1} and {s6}."]
PERIOD_PLAN = {"/month": "Monthly Plan", "/quarter": "Quarterly Plan", "/year": "Yearly Plan", "/week": "Weekly Plan", "/term": "Term Plan"}
# feature text of a business-type pack: its six items are ways of working ("Clear Quotes", "Friendly Local Service"), not services
TYPE_FEAT = ["{Sc} {is} part of how we work as {a_l}, from your first message onwards.", "You can count on {s} from us as {a_l}, whatever you need.",
             "As {a_l}, we keep {s} simple and the same for everyone.", "{Sc} matter{vs} to us as {a_l}, because {they} make{vs} things easier for you.",
             "Ask how {s} work{vs} at {a_l} like ours; we are happy to explain.", "{Sc} come{vs} as standard here, as at any good {l_noun}."]
HERO_FALLBACK = ["{L} Made Simple And Clear", "Your Local {L} Team Nearby", "Friendly {L} Help Without The Fuss", "Clear {L} Help When You Need It"]
FEATURE_FALLBACK = ["What Our {L} Offers You", "What You Get From Our {L}", "Everything Our {L} Offers"]
SUB_FALLBACK = ["{brand} offers {s1} and {s2}. Tell us what you need and we will reply with a clear plan and a fair price{city_in}.",
                "Looking for {l}? {brand} listens first, explains the options in plain words and keeps you informed{city_in}.",
                "{brand} is here for {s1} and {s3}. Ask us anything and we will answer simply and without pressure{city_in}."]


def niche_file():
    """The niche list in use: use_niche_file(), else $CORECRAFT_NICHE_FILE ("author", "spec" or a path), else the packaged default (the spec list)."""
    got = str(_override[-1] if _override else os.environ.get("CORECRAFT_NICHE_FILE") or "").strip()
    return NAMED.get(got.lower(), Path(got) if got else NICHE_FILE)


def use_niche_file(path=None):
    """Switch the niche list for this process: "author", "spec", a path, or None (back to the default). The request index is rebuilt on the next call."""
    with _lock:
        _override.clear()
        if path:
            _override.append(str(path))
        _cache.clear()


def spec():
    """The niche list in use: {"niches": [...], "types": [...], "general": theme of the general pack}."""
    return load(niche_file())


def load(path):
    """A niche file, read once per path."""
    path = Path(path)
    got = _cache.get(("s", path))
    if got:
        return got
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise RuntimeError("cannot read the niche file %s: %s" % (path, e)) from None
    if not data.get("niches") or not data.get("types") or any("family" not in n or "services" not in n for n in data["niches"]):
        raise RuntimeError("%s is not a niche file (build one with training/build_niches.py)" % path)
    _cache[("s", path)] = data
    return data


def niches():
    return {n["id"]: n for n in spec()["niches"]}


def types():
    return {t["theme"]: t for t in spec()["types"]}


def general_theme():
    return spec().get("general", "general")


def fallback_niches():
    """The author's business types that no niche of the default list covers ({id: niche}): used only with the default list, for requests it does not know."""
    if niche_file().resolve() != NICHE_FILE.resolve():
        return {}
    return {n["id"]: dict(n, theme=n["spec_theme"]) for n in load(AUTHOR_FILE)["niches"] if not n.get("spec_equiv")}


def entry(pack_id):
    """The niche or business type behind a pack id ("dental_clinic", "type_healthcare", or a fallback niche such as "optical")."""
    if pack_id.startswith("type_") and pack_id[5:] in types():
        return types()[pack_id[5:]]
    return niches().get(pack_id) or fallback_niches().get(pack_id, {})


def tc(s):
    """Title Case the way the spec does it: every word starts with a capital (even "And" and "A")."""
    return " ".join(w[:1].upper() + w[1:] if w[:1].isalpha() else w for w in s.split())


def low(s):
    """Lower case, but keep acronyms and names with inner capitals (AC, CCTV, SUVs, iPhone). "Single-Use" is two plain words, so it goes lower case."""
    out = []
    for w in s.split():
        parts = []
        for part in w.split("-"):
            core = re.sub(r"[^A-Za-z]", "", part)
            parts.append(part if len(core) > 1 and (core.isupper() or re.search(r"[a-z][A-Z]", core)) else part.lower())
        out.append("-".join(parts))
    return " ".join(out)


def _h(*parts):
    return zlib.crc32("|".join(str(p) for p in parts).encode("utf-8"))


def _rotate(items, key):
    if not items:
        return []
    k = _h(key) % len(items)
    return items[k:] + items[:k]


def _fmt(pattern, tok):
    return pattern.format(**tok)


def _pick(patterns, tok, ok, key, used=(), fallback=()):
    """The first pattern (in a niche specific order, then the fallbacks) whose result passes ok() and was not used yet."""
    for p in _rotate(patterns, key) + list(fallback):
        t = _fmt(p, tok)
        if ok(t) and t not in used:
            return t
    raise ValueError("no pattern fits %r for %s" % (patterns[:2], key))


BUSINESS_HEADS = set("""shop store clinic studio school preschool centre agency parlour bar kitchen cafe house hall venue space retreat hostel stall showroom press garage
practice lab pharmacy florist bookstore restaurant boutique firm agent consultant accountant designer installer contractor dealer electrician plumber trust company charity
homestay startup taproom service advocate business bakery salon spa academy zone artist nutritionist dietitian organisation daycare vet""".split())
NOUNS = {   # what the business is called with an article, where the label is not a plain noun ("pest control" -> "a pest control service")
    "packers_movers": "a packers and movers company", "architect_construction": "an architect and builder", "cafe_coffee_tea": "a cafe", "pet_grooming_vet": "a pet care and vet clinic",
    "funeral_services": "a funeral service", "music_dance_classes": "a music and dance school", "online_coach_courses": "an online coach", "school_preschool": "a school and preschool",
    "ielts_language_coaching": "an IELTS and language coaching centre", "sweet_shop_mithai": "a sweet shop", "fitness_martial_arts_dance": "a martial arts and dance fitness studio",
    "animal_welfare": "an animal welfare and rescue group", "ngo_charity": "an NGO", "hair_salon_spa": "a hair salon and spa", "nutritionist_dietitian": "a dietitian and nutritionist",
    "scrap_recycling": "a scrap and recycling service", "type_modern_tech": "a software company", "type_organic_nature": "an organic and farm business", "type_bold_fitness": "a gym",
    "type_luxury_minimal": "a luxury brand", "type_playful_vibrant": "a kids and toys brand", "type_professional_services": "a consulting and legal practice",
    "type_healthcare": "a clinic", "type_education": "a school or coaching centre", "type_creative_studio": "a design and creative studio", "type_real_estate": "a property business",
    "type_travel_tourism": "a travel business", "type_automotive": "a car and bike business", "type_beauty_wellness": "a salon or wellness studio", "type_events_wedding": "a wedding and event team",
    "type_pets_animals": "a pet and vet business", "type_nonprofit": "a nonprofit", "type_food_order": "a bakery or sweet shop", "type_clinic": "a clinic", "type_edu": "a coaching centre",
    "type_events": "an events team", "type_stay": "a travel and stay business", "type_property": "a property business", "type_software": "a software and IT business",
    "type_fashion_retail": "a clothing boutique", "type_home_services": "a home services team", "type_general_business": "a local business", "ngo": "a non-profit organisation", "hotel": "a hotel", "events": "an event planner", "salon": "a hair and beauty salon",
    "mehendi": "a mehendi and bridal artist", "music": "a music and dance academy", "playschool": "a play school and daycare", "visa": "a visa and immigration consultant",
    "astrology": "an astrologer", "insurance": "an insurance and finance advisor", "books": "a bookstore", "gaming": "a gaming zone", "sports": "a sports academy",
}


def a_label(label, nid=""):
    """The business named as a noun with its article: "a dental clinic", "a pest control service", "an IELTS and language coaching centre"."""
    if nid in NOUNS:
        return NOUNS[nid]
    lab = low(re.sub(r"\s*\(.*?\)", "", label))
    head = re.sub(r"[^a-z]", "", lab.split()[-1].lower())
    noun = lab if head in BUSINESS_HEADS else lab + " service"
    return "%s %s" % (a_an(noun), noun)


def _commas(text, services):
    """"pastries and cupcakes and breads and cookies" -> "pastries and cupcakes, and breads and cookies": a comma before "and" when a service name has its own "and"."""
    for sv in services:
        sv = low(sv)
        if " and " in sv:
            text = re.sub(r"(?<!,) and " + re.escape(sv) + r"\b", ", and " + sv, text)
            text = re.sub(r"\b" + re.escape(sv) + r" and (?!" + "|".join(re.escape(low(o)) for o in services if low(o) == sv) + r")", sv + ", and ", text)
    return text


def sentence_cap(s):
    return s[:1].upper() + s[1:]


def _agree(phrase, n=""):
    """Words that agree with a service name, suffixed with its number: {is2} are/is, {was2}, {it2} them/it, {they2} they/it, {vs2} "" or "s" (verb ending)."""
    f = forms(phrase)
    out = {k + n: v for k, v in f.items() if k in ("it", "is", "was", "this", "they", "its", "does")}
    out["Is" + n] = sentence_cap(f["is"])
    out["vs" + n] = "" if f["is"] == "are" else "s"
    return out


def _tokens(label, services, city=None, nid=""):
    a = a_label(label, nid)
    tok = {"L": tc(label), "l": low(label), "city_in": (" in %s" % city) if city else "", "brand": "{brand}", "a_l": a,
           "a_local_l": "a local " + a.split(" ", 1)[1] if not a.split(" ", 1)[1].startswith("local ") else a}
    for i, s in enumerate(services, 1):
        tok["S%d" % i] = tc(s)
        tok["s%d" % i] = low(s)
        tok["Sc%d" % i] = sentence_cap(low(s))
        tok.update(_agree(s, str(i)))
    return tok


JOINERS = {"and", "for", "of", "with", "in", "on", "at", "to", "a", "an", "the", "or"}


def _short_service(s):
    w = [x.rstrip(",") for x in s.split()]
    for cand in (s, " ".join(w[:2]), " ".join(w[-2:]), w[0], w[-1]):
        c = cand.split()
        if len(cand) <= 16 and len(c) <= 2 and c[0].lower() not in JOINERS and c[-1].lower() not in JOINERS:
            return cand
    return w[0][:16]


def _caption(s):
    w = s.replace(",", "").split()
    if len(w) > 4:
        w = w[:4]
    if len(w) < 2:
        w = w + ["Work"]
    return " ".join(w)


def _price(v):
    return "$%d" % v if float(v).is_integer() else "$%.2f" % v


def _keywords(n):
    if n.get("_keywords_only"):
        return list(n["keywords"])[:14]
    kws, seen = [], set()
    generic = {"services", "service", "shop", "company", "store", "studio", "agency", "centre", "center", "clinic", "tapri"}
    for k in n["keywords"]:
        k = k.strip().lower()
        if not k or k in seen or k in generic:
            continue
        seen.add(k)
        kws.append(k)
    latin = [k for k in kws if k.isascii()][:12]
    deva = [k for k in kws if not k.isascii()][:2]
    return (latin + deva)[:14]


def build_pack(niche, city=None):
    nid = niche["id"]
    fam = FAMILIES[niche["family"]]
    label = niche["label"]
    services = list(niche["services"])
    tok = _tokens(label, services, city, nid)
    key = nid
    rot = _h(nid)
    L = tok["L"]

    def title_ok(lo, hi):
        return lambda t: lo <= len(t) <= hi
    hero = []
    hero_patterns = [p for p in fam["hero"] if "{S" not in p] if niche.get("_keywords_only") else fam["hero"]
    for p in _rotate(hero_patterns, key + "h") + HERO_FALLBACK:
        t = _fmt(p, tok)
        if 25 <= len(t) <= 58 and t not in hero:
            hero.append(t)
        if len(hero) == 3:
            break
    def _subtitles(tk):
        out = []
        for p in _rotate(fam["sub"], key + "s") + SUB_FALLBACK:
            t = _commas(_fmt(p, tk), services)
            if 80 <= len(t) <= 150 and t not in out:
                out.append(t)
            if len(out) == 3:
                break
        return out
    subs = _subtitles(tok)
    city_in_contact = False
    if len(subs) < 3 and city:   # a long city name pushes the subtitles over 150 characters: say the city once, in the contact text, as the spec allows
        subs = _subtitles(dict(tok, city_in=""))
        city_in_contact = True
    features = []
    frames = TYPE_FEAT if niche.get("_keywords_only") else fam["feat"]
    used_text = set()
    for i, s in enumerate(services):
        title = s if len(s) <= 30 else s[:30].rsplit(" ", 1)[0]
        done = None
        for j in range(len(frames)):
            t = frames[(rot + i + j) % len(frames)].format(s=low(s), S=tc(s), Sc=sentence_cap(low(s)), L=L, l=tok["l"], a_l=tok["a_l"],
                                                          l_noun=tok["a_l"].split(" ", 1)[1], **_agree(s))
            t = _commas(t, services)
            if 50 <= len(t) <= 115 and t not in used_text:
                done = t
                break
        if done is None:
            raise ValueError("%s: no feature text fits %r" % (nid, s))
        used_text.add(done)
        features.append({"title": title, "text": done})
    stats = [{"value": v, "label": l} for v, l in _rotate(fam["stats"], key + "t")[0]]
    steps_title = _pick(fam["steps_title"], tok, lambda t: True, key + "st")
    steps = [{"title": t, "text": _fmt(x, tok)} for t, x in fam["steps"]]
    faq_pool = _rotate(fam["faq"], key + "q")[:5]
    faq = []
    tails = _rotate(FAQ_TAILS, key + "ft")
    for i, (q, ans) in enumerate(faq_pool):
        ans = _fmt(ans, tok)
        if not any(w in ans.lower() for w in [tok["l"]] + [tok["s%d" % k] for k in range(1, 7)]):
            ans = ans + " " + _fmt(tails[i % len(tails)], tok)   # the same answer must not appear on the page of another niche
        faq.append({"q": _fmt(q, tok), "a": ans})
    button = niche.get("button") or fam["button"]
    cta_patterns = [p for p in fam["cta_title"] if "{S" not in p] or ["Ready To Get Started With {L}?"] if niche.get("_keywords_only") else fam["cta_title"]
    cta_title = _pick(cta_patterns, tok, lambda t: len(t) <= 60, key + "c")
    about_title = _pick(fam["about_title"], tok, lambda t: True, key + "a")
    ab = _rotate(fam["about"][0], key + "p1")[0], _rotate(fam["about"][1], key + "p2")[0]
    price_rows = niche.get("prices") or FAMILY_PRICES[niche["family"]]
    plans = []
    for (name, perks), (price, period) in zip(fam["plans"], price_rows):
        if name.startswith("Single") and period in PERIOD_PLAN:   # "Single Session" is not a price per month
            name = PERIOD_PLAN[period]
        plans.append({"name": name, "price": _price(price), "period": period, "perks": [_fmt(x, tok) for x in perks]})
    captions = []
    for s in services:
        c = _caption(s)
        captions.append(c)
    if len(set(captions)) < 6:
        captions = [_caption(s) + ("" if i == 0 else "") for i, s in enumerate(services)]
    roles = niche.get("team") or [_fmt(r, tok) for r in fam["roles"]]
    tests = [{"quote": _fmt(q, tok), "role": r} for q, r in _rotate(fam["testimonials"], key + "x")[:3]]
    posts = [{"tag": t, "title": _fmt(p, tok)} for t, p in _rotate(fam["blog"], key + "b")[:3]]
    marquee, seen = [], set()
    for m in [_short_service(s) for s in services[:5]] + [tc(w) for w in fam["marquee_extra"]] + [_short_service(s) for s in services[5:]]:
        if m.lower() not in seen and len(m) <= 16 and len(m.split()) <= 2:
            seen.add(m.lower())
            marquee.append(m)
        if len(marquee) == 8:
            break
    for kw in niche["keywords"]:   # fewer than 8 short words so far: top up from the words people use
        m = tc(kw)
        if len(marquee) < 8 and m.isascii() and m.lower() not in seen and len(m) <= 16 and len(m.split()) <= 2:
            seen.add(m.lower())
            marquee.append(m)
    contact = _pick(fam["contact"], tok, lambda t: True, key + "k")
    if city_in_contact:
        contact = contact.rstrip(".") + " in %s." % city
    pack = {
        "id": nid, "label": label, "theme": niche["theme"], "keywords": _keywords(niche), "heroTitles": hero, "heroSubtitles": subs, "button": button,
        "featureTitle": _pick(fam["feature_title"], tok, title_ok(20, 60), key + "f", fallback=FEATURE_FALLBACK), "features": features, "stats": stats,
        "steps": {"title": steps_title, "items": steps}, "faq": faq, "cta": {"title": cta_title, "button": button},
        "about": {"title": about_title, "paragraphs": [_fmt(ab[0], tok), _fmt(ab[1], tok)], "points": list(_rotate(fam["points"], key + "pt")[0])},
        "pricing": {"title": _pick(fam["pricing_title"], tok, lambda t: True, key + "pr"), "plans": plans},
        "gallery": {"title": _pick(fam["gallery_title"], tok, lambda t: True, key + "g"), "captions": captions},
        "team": {"title": fam["team_title"], "roles": roles},
        "testimonials": tests, "blog": {"title": _pick(fam["blog_title"], tok, lambda t: True, key + "bt"), "posts": posts}, "marquee": marquee, "contactText": contact,
    }
    for f in faq:
        f["a"] = _commas(f["a"], services)
    pack["about"]["paragraphs"] = [_commas(x, services) for x in pack["about"]["paragraphs"]]
    for x in pack["steps"]["items"]:
        x["text"] = _commas(x["text"], services)
    for x in pack["testimonials"]:
        x["quote"] = _commas(x["quote"], services)
    pack["contactText"] = _commas(pack["contactText"], services)
    if niche.get("menu"):
        pack["menu"] = json.loads(json.dumps(niche["menu"]))
    return pack


def build_type_pack(theme, city=None):
    """The general pack of one business type (a family of the niche file, or "general" for any local business)."""
    t = types()[theme]
    short = t.get("short") or t["label"]
    niche = {"id": "type_" + theme, "label": short[:1].upper() + short[1:], "theme": theme, "services": t["items"], "keywords": t["keywords"], "family": t["family"],
             "prices": t["prices"], "button": t["button"], "menu": t.get("menu"), "_keywords_only": True}
    p = build_pack(niche, city)
    p["label"] = t["label"]
    return p


def build_type_packs():
    """One general pack per business type of the niche file."""
    return [build_type_pack(t["theme"]) for t in spec()["types"]]


def render_pack(pack, brand=None, city=None):
    """The pack with {brand} replaced (for a preview or a page). The city, when given and not already in the text, goes once into the contact text."""
    text = json.dumps(pack, ensure_ascii=False)
    if brand:
        text = text.replace("{brand}", brand.replace("\\", "").replace('"', "'"))
    out = json.loads(text)
    if city and city not in json.dumps(out, ensure_ascii=False):
        out["contactText"] = out["contactText"].rstrip(".") + " in %s." % city
    return out
