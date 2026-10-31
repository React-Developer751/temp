"""Writes the text of a page from facts, a kind (voice) and a profile (vocabulary). English path; Hindi data lives in voice_hi.py.

Every sentence is built from the person's own words (name, city, services, offers, hours) plus the voice of the kind of business:
a restaurant serves and cooks, a clinic examines and treats, a gym trains, a shop stocks. Nothing is invented: a fact that
was not given leaves out the sentence that would have used it.
"""
import re

from .grammar import forms
from .lexicon import describe
from .profiles import PROFILES, signature
from . import voice_data as VD
from .voice_profile import profile_voice

HYPHENS = [("wood fired", "wood-fired"), ("stone baked", "stone-baked"), ("hand made", "handmade"), ("home made", "homemade"), ("hand crafted", "hand-crafted"),
           ("slow cooked", "slow-cooked"), ("gluten free", "gluten-free"), ("sugar free", "sugar-free"), ("check up", "check-up"), ("co working", "co-working")]
OFFER_HIGHLIGHT = {   # (title, [text variants])
    "online_booking": ("Online booking", ["Reserve or book in a few clicks, whenever it suits you.", "Book online at any hour; no phone call needed.", "Pick a slot online and you're done."]),
    "home_delivery": ("Home delivery", ["Ask us what's possible for your area.", "We bring it to you; message us your location.", "Delivery to your door; tell us where you are."]),
    "free_shipping": ("Free shipping", ["Message us your address and we'll confirm.", "Shipping costs nothing; send us your address.", "No shipping charge; tell us where to send it."]),
    "cod": ("Cash on delivery", ["Pay when your order arrives.", "Pay at the door when it reaches you.", "No advance payment needed; pay on delivery."]),
    "returns": ("Easy returns", ["Ask us how returns and exchanges work.", "Changed your mind? Ask how a return works.", "Returns are simple; ask for the details."]),
    "free_trial": ("Free trial", ["Try it first; ask us to book a time.", "Start with a trial before you commit.", "Come once for free and see if it suits you."]),
    "free_consult": ("Free consultation", ["Start with a conversation and no obligation.", "Talk it through first; no charge for the first chat.", "A first consultation at no cost."]),
    "takeaway": ("Takeaway", ["Order to take away; ask what's available.", "Pick it up and take it home.", "Take away what you like; ask for the options."]),
    "parties": ("Parties and groups", ["Tell us the date and numbers and we'll plan around you.", "Planning a get-together? Share the numbers.", "Groups are welcome; send the date and headcount."]),
    "vegetarian": ("Vegetarian options", ["Ask the team what's available for vegetarians.", "Vegetarian choices are available; ask what's on offer.", "Meat-free options are part of what we do."]),
    "emi": ("Easy EMI", ["Ask us what payment options are available.", "Spread the cost; ask about instalments.", "Instalment plans are available; ask for the terms."]),
    "warranty": ("Warranty", ["Ask us what comes with the item you choose.", "Warranty details are available on request.", "Ask what protection the item carries."]),
    "walk_in": ("Walk-ins welcome", ["Drop in whenever it suits you.", "No appointment needed; just come by.", "Turn up when you like."]),
    "wifi": ("Free Wi-Fi", ["Stay connected while you're here.", "Wi-Fi is free for visitors.", "Online while you wait or work."]),
    "parking": ("Parking", ["Ask us where to park when you visit.", "Parking is available; ask where.", "Ask about parking before you come."]),
    "new_patients": ("New patients welcome", ["Say hello and tell us what you need; first visits are welcome.", "New here? Get in touch and we'll find you a time.", "Starting fresh is fine; contact us to arrange a first visit."]),
    "online_order": ("Order online", ["Choose what you like and order from home.", "Place your order online, whenever it suits you.", "Order in a few clicks; no phone call needed."]),
    "pickup": ("Pickup", ["Tell us when and where, and we'll confirm the pickup.", "Message us the details and we'll arrange the pickup.", "Ask us how pickup works and when it suits you."]),
    "financing": ("Financing", ["Ask us about payment plans before you decide.", "Spread the cost; ask what financing is available.", "Financing is available; ask for the details."]),
    "same_day": ("Same-day help", ["Need it today? Contact us and we'll tell you what's possible.", "Same-day help is available; get in touch early.", "Urgent? Message us and see what can be done today."]),
    "home_visit": ("Home visits", ["Tell us where you are and we'll confirm.", "We can come to you; share your address.", "A visit at home; ask what's possible."]),
}
GENERIC_CARDS = {
    "food": [("Starters", "Small plates to open the meal; ask what's on offer today."), ("Mains", "The centre of the table; ask the team for a recommendation."),
             ("Desserts", "Something sweet to finish; ask what's on the list."), ("Drinks", "Something to sip alongside; ask what pairs well.")],
}


SYN = [   # drop-in wordings: the same sentence is printed one of several ways, so two pages of one niche read differently
    (r"\btell us\b", ["tell us", "let us know"]), (r"\bwe'll\b", ["we'll", "we will"]), (r"\bask us\b", ["ask us", "feel free to ask us"]),
    (r"\bcontact details\b", ["contact details", "contact information"]), (r"\bof course\b", ["of course", "certainly"]), (r"\byou'll\b", ["you'll", "you will"]),
    (r"\bquestions are welcome\b", ["questions are welcome", "questions are always welcome"]), (r"\bget in touch\b", ["get in touch", "reach out"]),
    (r"\bmessage us and\b", ["message us and", "send us a message and"]), (r"\bno pressure\b", ["no pressure", "no hard sell"]),
    (r"\bwhatever you like\b", ["whatever you like", "anything you like"]), (r"\bwhen you book\b", ["when you book", "at the time of booking"]),
    (r"\bwhichever is easier\b", ["whichever is easier", "whichever suits you"]), (r"\bdecide\b", ["decide", "make up your mind"]),
]


def vary(text, rng):
    """Replace a few common phrases by an equivalent wording, keeping capitalisation."""
    for rx, alts in SYN:
        def sub(m, alts=alts):
            pick_ = rng.choice(alts)
            return pick_[:1].upper() + pick_[1:] if m.group(0)[:1].isupper() else pick_
        text = re.sub(rx, sub, text, flags=re.I)
    return text


def sentence_case(s):
    return s[:1].upper() + s[1:] if s else s


def lower_first(s):
    return s[:1].lower() + s[1:] if s and not s[:2].isupper() else s


def tidy_item(item):
    s = item.strip()
    low = s.lower()
    for a, b in HYPHENS:
        if a in low:
            s = re.sub(re.escape(a), b, s, flags=re.I)
            low = s.lower()
    return s


def title_case(item):
    return " ".join(w if (w.isupper() and len(w) > 1) else (w[:1].upper() + w[1:]) for w in tidy_item(item).split(" "))


def oxford(items, conj="and"):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return "%s %s %s" % (items[0], conj, items[1])
    return "%s %s %s" % (", ".join(items[:-1]), conj, items[-1])


def fmt(template, ctx):
    """str.format that leaves unknown keys empty instead of raising, then tidies spaces and punctuation."""
    class D(dict):
        def __missing__(self, k):
            return ""
    out = template.format_map(D(ctx))
    out = re.sub(r"\s+([.,;:?!])", r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    out = re.sub(r"([.!?])\s*([.!?])", r"\1", out)
    return out


def pick(rng, seq, used=None):
    """Random element not yet used on this page; falls back to any when all are used."""
    pool = [x for x in seq if used is None or x not in used]
    choice = rng.choice(pool or list(seq))
    if used is not None:
        used.add(choice)
    return choice


def usable(patterns, n_items, flags):
    out = []
    for need_items, need_flags, text in patterns:
        if need_items <= n_items and all(f in flags for f in need_flags):
            out.append(text)
    return out


def items_ctx(items):
    """Item-related template variables for an ordered list of items."""
    it = [tidy_item(i) for i in items]
    c = {}
    for n, x in enumerate(it[:3], 1):
        c["i%d" % n] = x
        c["I%d" % n] = sentence_case(x)
        c.update({k + str(n): v for k, v in agreement(x).items()})
    if it:
        c["ilast"] = it[min(len(it), 3) - 1]
        c["list"] = oxford(it[:3])
        c["list2"] = oxford(it[:2])
        c["list2_or"] = oxford(it[:2], "or")
        c["rest_list"] = oxford(it[1:3]) if len(it) > 1 else ""
        c["i"], c["I"] = it[0], sentence_case(it[0])
        c.update(agreement(it[0]))
    return c


def agreement(item):
    """Words that agree with an item: {it} them/it, {is} are/is, {was}, {this}, {they}, {does}, and verbs in the 3rd person ({works}, {needs}, {keep})."""
    f = forms(item)
    plural = f["is"] == "are"
    f.update({"works": "work" if plural else "works", "needs": "need" if plural else "needs", "keep": "keep" if plural else "keeps", "fits": "fit" if plural else "fits"})
    return f


def build_ctx(*, voice, label, items, facts, name, rng, lang="en", type_id=None, kind=None):
    """The variables every template may use. Missing facts stay empty strings."""
    city = facts.get("city") or ""
    it = [tidy_item(i) for i in items]
    ctx = {
        "name": name or "", "Name": name or "", "label": label.lower() if label else "", "Label": sentence_case(label or ""),
        "subj": name or "We", "subj_obj": name or "us", "city": city, "city_s": (city + "'s") if city else "",
        "place": (" in " + city) if city else "", "who": voice["who"], "who_l": voice["who"], "label_l": (label or "").lower(),
        "hours": facts.get("hours") or "", "phone": facts.get("phone") or "",
    }
    does, do = voice["does"], voice["do"]
    if type_id in VD.TYPE_VERBS:
        does, do = VD.TYPE_VERBS[type_id]
    elif kind == "retail" and any(re.search(VD.SERVICE_LIKE, i.lower()) for i in items[:3]):
        does, do = ("offers",), ("offer",)   # a shop that lists a test ride or finance does not "sell" them
    k = rng.randrange(len(does))
    ctx["verb"] = does[k] if name else do[k]
    ctx["ing"] = voice["ing"][rng.randrange(len(voice["ing"]))]
    ctx["Ing"] = ctx["ing"]
    ctx["come"] = voice["come"]
    ctx.update(items_ctx(items))
    offers = facts.get("offers") or []
    texts = [o["text"] for o in offers]
    ctx["offers_list_l"] = oxford([lower_first(t) for t in texts])
    ctx["Offer1"] = texts[0] if texts else ""
    ctx["offer1_l"] = lower_first(texts[0]) if texts else ""
    if texts:
        verb = "is" if len(texts) == 1 else "are"
        ctx["Offers_sentence"] = "%s %s available." % (sentence_case(oxford([lower_first(t) for t in texts])), verb)
    online = any(o["id"] in ("online_booking", "online_order") for o in offers)
    ctx["online"] = online
    a1, a2 = (voice["act_online"] if online else voice["act"])
    ctx["act1"], ctx["act2"] = a1, a2
    ctx["act1_l"] = lower_first(a1)
    ctx["book_how"] = voice["book_how_online"] if online else voice["book_how"]
    ctx["tail"] = pick(rng, voice["tails"])
    return ctx


def flags_of(facts, name, offers, n_items=1):
    f = set()
    if not n_items:
        f.add("noitems")
    if facts.get("city"):
        f.add("city")
    if name:
        f.add("name")
    if facts.get("hours"):
        f.add("hours")
    if offers:
        f.add("offer")
    if facts.get("phone"):
        f.add("phone")
    return f


def write_page(*, kind, label, type_id, profile, facts, name, rng, voice=None, patterns=None, typical=None, extra_cards=(), filler_lines=None, lang="en"):
    """-> dict of page text. `name` is None when the business name was invented (then the copy says "we" and never prints it)."""
    voice = voice or profile_voice(kind, profile, type_id) or VD.VOICE[kind]
    P = patterns or {"hero": VD.HERO_TITLE, "sub": VD.HERO_SUB, "a": VD.ABOUT_A, "b": VD.ABOUT_B}
    items = [i for i in facts.get("items", []) if i]
    offers = facts.get("offers") or []
    used = set()
    ctx = build_ctx(voice=voice, label=label, items=items, facts=facts, name=name, rng=rng, lang=lang, type_id=type_id, kind=kind)
    n_items = len(items)
    flags = flags_of(facts, name, offers, n_items)
    closers = list(voice["closers"]) + (list(VD.GENERIC["closers"]) if (voice is VD.VOICE.get(kind) or voice.get("_generic")) else [])
    rng.shuffle(closers)
    invites = list(voice["invites"]) + (list(VD.GENERIC["invites"]) if (voice is VD.VOICE.get(kind) or voice.get("_generic")) else [])
    rng.shuffle(invites)
    use_generic = voice is VD.VOICE.get(kind) or bool(voice.get("_generic"))

    shift = rng.randrange(max(n_items, 1))
    offsets = {sec: (shift + k) % max(n_items, 1) for k, sec in enumerate(("hero", "sub", "a", "b", "steps", "blog", "faq", "cta"))}
    rotated = {sec: items_ctx(items[off:] + items[:off]) for sec, off in offsets.items()}
    rotated["hero"] = items_ctx(items)   # the headline leads with the first thing the person named

    def render(tpl, extra=None, sec=None):
        c = dict(ctx)
        if sec and items:
            c.update(rotated[sec])
        c.update(extra or {})
        return fmt(tpl, c)

    # --- hero --------------------------------------------------------------------------------------------------
    hero_tpls = usable(P["hero"], n_items, flags)
    if n_items >= 2:   # the two-item headline ("Wood-fired pizza and fresh pasta in Mumbai") is the clearest, so favour it
        hero_tpls = hero_tpls + [t for t in hero_tpls if t.startswith("{I1} and {i2}")] * 3
    hero_tpl = rng.choice(hero_tpls)
    hero = render(hero_tpl, sec="hero")
    used_in_hero = max([int(x) for x in re.findall(r"\{[iI](\d)\}", hero_tpl)] or [0])
    # the subtitle talks about the services the headline did not name, so the two never repeat each other
    rest_items = items[used_in_hero:] if n_items > used_in_hero else []
    sub_flags = set(flags)
    sub_flags.discard("noitems")
    if not rest_items:
        sub_flags.add("norest")
    sub_ctx = {"closer": closers.pop()}
    sub_ctx.update(items_ctx(rest_items))
    sub = render(rng.choice(usable(P["sub"], len(rest_items), sub_flags)), sub_ctx)
    # --- about -------------------------------------------------------------------------------------------------
    a1 = render(rng.choice(usable(P["a"], n_items, flags)), {"closer": closers.pop()}, "a")
    b_pool = usable(P["b"], n_items, flags)
    if "city" in flags:   # a page about a local business names the city in its "about"
        b_pool = [t for t in b_pool if "{city}" in t] or b_pool
    b_tpl = rng.choice(b_pool)
    b = render(b_tpl, {"closer2": closers.pop(), "invite": invites.pop()}, "b")
    if n_items > 6:
        b = b.rstrip() + " Also: %s." % oxford([tidy_item(i) for i in items[6:]])
    about = [a1, b]

    # --- feature cards -------------------------------------------------------------------------------------------
    feats = []
    feat_lines = list(voice["feat"]) + (list(VD.GENERIC["feat"]) if use_generic else [])
    rng.shuffle(feat_lines)
    cards = list(items[:6]) + [c for c in extra_cards if c not in items][:max(0, 6 - len(items[:6]))]
    used_typical = []
    if typical and len(cards) < 4:   # too few services named: fill with what this type usually offers (reported in needs_review)
        used_typical = [x for x in typical if x.lower() not in {c.lower() for c in cards}][:max(0, 5 - len(cards)) if cards else 5]
        cards += used_typical
    elif not cards and kind in GENERIC_CARDS:
        cards = [t for t, _ in GENERIC_CARDS[kind]]
    used_desc = set()
    for n, raw in enumerate(cards):
        it = tidy_item(raw)
        desc = describe(raw, profile) if profile else None
        if desc in used_desc:   # two services may map to one lexicon line ("bread" / "sourdough bread"): never print it twice
            desc = None
        if desc and rng.random() > 0.6:   # about two cards in five carries the definition; the rest use a warm line, so pages differ more
            used_desc.add(desc)
        else:
            desc = None
        if raw in extra_cards and filler_lines:
            desc = filler_lines.get(raw)
        if not items and kind in GENERIC_CARDS and not typical:
            desc, line = dict(GENERIC_CARDS[kind]).get(raw), None
        else:
            line = feat_lines[n % len(feat_lines)].format_map(dict(items_ctx([it]), i=it, I=sentence_case(it), i1=it))
        if desc and line and rng.random() < 0.5:
            text = desc + " " + line
        else:
            text = desc or line or ""
        feats.append({"title": title_case(raw), "text": text})

    # --- highlights ----------------------------------------------------------------------------------------------
    hl = []
    for o in offers[:3]:
        t = OFFER_HIGHLIGHT.get(o["id"])
        hl.append({"title": t[0], "text": rng.choice(t[1])} if t else {"title": o["text"], "text": "Ask us for the details."})
    if facts.get("hours") and len(hl) < 4:
        hl.append({"title": "Opening hours", "text": "Hours: %s. Drop by or send a message." % facts["hours"]})
    kind_hl = list(voice["highlights"]) + (list(VD.GENERIC["highlights"]) if use_generic else [])
    rng.shuffle(kind_hl)
    while len(hl) < 3 and kind_hl:
        t, x = kind_hl.pop()
        hl.append({"title": t, "text": x})

    # --- steps ---------------------------------------------------------------------------------------------------
    pool = list(voice["steps"])
    prof_steps = PROFILE_STEPS.get(profile)
    if prof_steps:
        pool = prof_steps + pool
    # mix step by step across the authored sequences (all "start" steps, all "middle" steps, all "end" steps), so two pages rarely share a step
    generic_steps = [[("Get in touch", "Send a message or call and tell us what you need."), ("Say hello", "Tell us what you have in mind."), ("Ask your questions", "We'll explain how it works."), ("Share the details", "A few lines is enough."), ("Contact us", "Call, message or visit; whichever suits you.")],
                     [("We talk it through", "We explain the options in plain words."), ("Agree the plan", "We confirm what happens and when."), ("Look at the options", "We suggest what suits you."), ("Confirm the details", "So nothing is a surprise."), ("Review together", "We go through the details and answer questions.")],
                     [("Get started", "We begin when you're ready."), ("Follow up", "We check in afterwards."), ("Enjoy the result", "Tell us how it went."), ("Come back anytime", "We're a message away."), ("Keep in touch", "We're here if you have more questions afterwards.")]]
    trip = []
    for pos in range(3):
        cands = [seq[pos] for seq in pool if len(seq) > pos]
        if use_generic:
            cands = cands + generic_steps[pos][:max(1, len(cands) // 2)]   # a third of the time a neutral step fits just as well
        trip.append(rng.choice(cands))
    main = signature(profile, items) or "choice"
    steps = [{"title": render(t, {"main": main}, "hero"), "text": render(x, {"main": main}, "hero")} for t, x in trip]   # steps use the person's own order: "Choose your pizza" then "pizza or pasta"

    # --- faq -----------------------------------------------------------------------------------------------------
    offer_ids = {o["id"] for o in offers}
    eligible = []
    for q, answers, cond, cond_answers in list(voice["faq"]) + (list(VD.GENERIC["faq"]) if use_generic else []):
        if cond == "hours" and not facts.get("hours"):
            continue
        if cond == "city" and not facts.get("city"):
            continue
        if cond == "item" and not items:
            continue
        if cond in ("hours", "city", "item"):
            eligible.append((q, answers, True))
        elif cond and cond in offer_ids and cond_answers:
            eligible.append((q, cond_answers, True))
        else:
            eligible.append((q, answers, False))
    fact_based = [e for e in eligible if e[2]]
    others = [e for e in eligible if not e[2]]
    rng.shuffle(others)
    chosen = fact_based[:3] + others
    chosen = chosen[:4]
    order = {q: n for n, (q, _, _, _) in enumerate(list(voice["faq"]) + (list(VD.GENERIC["faq"]) if use_generic else []))}
    chosen.sort(key=lambda e: order[e[0]])
    faq = [{"q": render(q, None, "hero"), "a": render(rng.choice(a), None, "hero")} for q, a, _ in chosen]   # FAQ items follow the person's own order

    # --- blog ----------------------------------------------------------------------------------------------------
    blog_pool = list(voice["blog"]) + (list(VD.GENERIC["blog"]) if use_generic else [])
    rng.shuffle(blog_pool)
    blog = []
    for t, e in blog_pool:
        needs2 = "{i2}" in t or "{i2}" in e or "{I2}" in t
        if needs2 and n_items < 2:
            continue
        if ("{i1}" in t or "{I1}" in t or "{i1}" in e) and n_items < 1:
            continue
        blog.append({"title": sentence_case(render(t, None, "blog")), "excerpt": render(e, None, "blog")})
        if len(blog) == 3:
            break

    # --- calls to action -----------------------------------------------------------------------------------------
    cta_text = render(rng.choice([c for c in voice["cta_text"] if ("{i1}" not in c or n_items)]), None, "cta")
    cta_title = rng.choice(VD.CTA_TITLES)
    sub = vary(sub, rng)
    about = [vary(x, rng) for x in about]
    for f in feats:
        f["text"] = vary(f["text"], rng)
    for h in hl:
        h["text"] = vary(h["text"], rng)
    for st in steps:
        st["text"] = vary(st["text"], rng)
    for q in faq:
        q["a"] = vary(q["a"], rng)
    for b in blog:
        b["excerpt"] = vary(b["excerpt"], rng)
    cta_text = vary(cta_text, rng)
    return {
        "hero_heading": hero, "tagline": sub, "about": about, "features": feats, "highlights": hl[:4], "steps": steps, "faq": faq, "blog": blog,
        "cta_primary": ctx["act1"], "cta_secondary": ctx["act2"], "cta_text": cta_text, "cta_title": cta_title,
        "stats_title": rng.choice(VD.STATS_TITLES), "steps_title": rng.choice(VD.STEPS_TITLES), "faq_title": rng.choice(VD.FAQ_TITLES), "blog_title": rng.choice(VD.BLOG_TITLES),
        "features_title": rng.choice(VD.FEATURE_TITLES[kind]), "used_typical": used_typical,
    }


# profile-specific steps (title, text) triplets; {main} is the signature noun: "Choose your pizza"
PROFILE_STEPS = {
    "italian": [[("Book a table", "{book_how}; say if it's a celebration."), ("Choose your {main}", "Start with {list2_or}, or ask the team what they'd pick."), ("Save room for dessert", "Something sweet is always worth the space.")],
                [("Reserve", "Tell us the day and the size of the group."), ("Order for the table", "Start with {i1}, then share."), ("Linger", "No rush; coffee is part of the meal.")]],
    "north_indian": [[("Book a table", "{book_how}, and tell us how many are coming."), ("Order for the table", "Mix {list2_or} with breads and a side."), ("Share and enjoy", "Dishes are better passed around.")],
                     [("Reserve", "Tell us the day and the group size."), ("Choose your {main}", "Start with {i1}; ask what goes well with {it1}."), ("Take your time", "Good food is not rushed.")]],
    "south_indian": [[("Pick a time", "Tell us when you're coming and how many."), ("Choose your {main}", "Start with {list2_or}; ask about sides."), ("Eat it fresh", "Dosas and idlis are best eaten straight away.")]],
    "chinese": [[("Reserve", "{book_how}."), ("Pick your {main}", "Choose {list2_or}, then add something to share."), ("Share the table", "Pass the plates around.")]],
    "street_food": [[("Walk up or message", "Tell us what you fancy."), ("Pick your {main}", "Try {list2_or}."), ("Add the sides", "Chutneys, sev and something cold to drink.")]],
    "bakery": [[("Share your idea", "Flavour, size, message and the date."), ("We plan the bake", "We confirm the details with you."), ("Collect and celebrate", "Pick it up and enjoy.")],
               [("Browse", "Start with {list2_or}."), ("Tell us the occasion", "Cakes for a set date need a message early."), ("Pick up", "{book_how}.")]],
    "tea_cafe": [[("Drop in", "Find a seat; there's no rush."), ("Order your {main}", "Start with {list2_or}."), ("Stay a while", "Tea tastes better with conversation.")]],
    "bar": [[("Reserve", "{book_how}."), ("Pick a drink", "Start with {list2_or}."), ("Stay for the evening", "Order slowly and enjoy the company.")]],
    "dental": [[("Book a check-up", "{book_how}, and tell us what you'd like help with."), ("Examination", "The dentist looks closely and explains what they see."), ("Plan your treatment", "Agree {list2_or} and the order of visits.")]],
    "skin": [[("Book a consultation", "{book_how}, and tell us your concern."), ("Skin assessment", "We look closely at your skin and history."), ("Start your plan", "We plan {list2_or}, then review how it's going.")]],
    "eye": [[("Book an eye test", "{book_how}."), ("Examination", "Vision and eye health are checked."), ("Discuss next steps", "Glasses, lenses or treatment: we explain the options.")]],
    "physio": [[("Book an assessment", "{book_how}, and tell us where it hurts."), ("Assessment", "We examine movement and look for the cause."), ("Exercise plan", "A plan you can follow, reviewed as you improve.")]],
    "crossfit": [[("Book an intro", "{book_how}."), ("Learn the movements", "The coach introduces the lifts and scales them."), ("Join the class", "Train together; coaches adjust as you go.")]],
    "yoga": [[("Pick a class", "Choose a time and a level."), ("Arrive and settle", "Mat, water, comfortable clothes."), ("Practise", "Follow the teacher; rest when you need to.")]],
    "zumba": [[("Pick a class", "Choose a time that suits you."), ("Learn the steps", "The instructor breaks the routine down."), ("Dance it out", "Follow along and enjoy the music.")]],
    "kurti": [[("Browse the collection", "Start with {list2_or}."), ("Check size and fabric", "Ask us about sizing and care."), ("Order or collect", "{book_how}.")]],
    "saree": [[("Browse the weaves", "Start with {list2_or}."), ("Ask about fabric and care", "We'll explain what to expect."), ("Pick your drape", "Choose the one you love.")]],
    "electronics": [[("Compare", "Look at {list2_or} side by side."), ("Ask", "We'll explain features in plain words."), ("Buy with confidence", "Check warranty details before you pay.")]],
    "books": [[("Browse", "Start with {list2_or}."), ("Ask", "Tell us what you're looking for."), ("Take it home", "{book_how}.")]],
    "autosales": [[("Look at the range", "Start with {list2_or}."), ("Book a test ride", "Ride before you decide."), ("Choose and finance", "Ask what payment options are available.")]],
    "tyres": [[("Tell us the vehicle", "Make, model and tyre size if you know."), ("Inspection", "We check the tyres and the alignment."), ("Fit and test", "We fit, balance and check the result.")]],
    "robotics": [[("Pick a workshop", "Choose from {list2_or}."), ("Build", "Hands-on making with guidance."), ("Test and improve", "Try it, fix it, try again.")]],
    "pottery": [[("Pick a session", "Choose from {list2_or}."), ("Make", "Shape clay at the wheel or by hand."), ("Glaze and collect", "Pieces are glazed and fired; collect when ready.")]],
}
