"""Hindi page writer: same shape as writer.write_page, built from voice_hi banks and lang_hi blocks."""
import re

from . import lang_hi
from . import voice_hi as VH
from .writer import fmt, items_ctx, pick, usable

FILLER_LINES = dict(lang_hi.GENERIC_FEATURES)


def oxford_hi(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return "%s और %s" % (", ".join(items[:-1]), items[-1])


def write_page_hi(*, kind, label, facts, name, rng, extra_cards=(), type_id=None):
    voice = dict(VH.VOICE[kind])
    if type_id in lang_hi.TYPE_ACT:
        voice["act"], voice["act_online"] = lang_hi.TYPE_ACT[type_id]
    items = [i for i in facts.get("items", []) if i]
    offers = facts.get("offers") or []
    key = lang_hi.KIND_KEY[kind]
    city = facts.get("city") or ""
    n_items = len(items)
    flags = set()
    if city:
        flags.add("city")
    if name:
        flags.add("name")
    if facts.get("hours"):
        flags.add("hours")
    if offers:
        flags.add("offer")
    if facts.get("phone"):
        flags.add("phone")
    if not n_items:
        flags.add("noitems")
    online = any(o["id"] == "online_booking" for o in offers)
    a1, a2 = voice["act_online"] if online else voice["act"]
    texts = [o["text_hi"] for o in offers]
    ctx = {"name": name or "", "Name": name or "", "label": label, "Label": label, "city": city, "place": (" — %s में" % city) if city else "",
           "who": voice["who"], "hours": facts.get("hours") or "", "phone": facts.get("phone") or "", "act1": a1, "act2": a2, "act1_l": a1,
           "book_how": voice["book_how"], "offers_list_l": oxford_hi(texts), "tail": pick(rng, voice["tails"])}
    if texts:
        ctx["Offers_sentence"] = VH.OFFER_SENTENCE.format(oxford_hi(texts), "है" if len(texts) == 1 else "हैं")
    ctx.update(items_ctx(items))
    for k in ("list", "list2", "rest_list"):
        if k in ctx:
            src = items[:3] if k == "list" else (items[:2] if k == "list2" else items[1:3])
            ctx[k] = oxford_hi(src)
    closers = list(voice["closers"])
    rng.shuffle(closers)
    invites = list(voice["invites"])
    rng.shuffle(invites)

    def render(tpl, extra=None):
        c = dict(ctx)
        c.update(extra or {})
        return fmt(tpl, c)

    hero_tpls = usable(VH.HERO_TITLE, n_items, flags)
    if n_items >= 2:
        hero_tpls = hero_tpls + [t for t in hero_tpls if t.startswith("{i1} और {i2}")] * 3
    hero_tpl = rng.choice(hero_tpls)
    hero = render(hero_tpl)
    used = max([int(x) for x in re.findall(r"\{[iI](\d)\}", hero_tpl)] or [0])
    rest = items[used:] if n_items > used else []
    sub_flags = set(flags)
    sub_flags.discard("noitems")
    if not rest:
        sub_flags.add("norest")
    sub_ctx = {"closer": closers.pop()}
    sub_ctx.update(items_ctx(rest))
    if rest:
        sub_ctx["list"] = oxford_hi(rest[:3])
    sub = render(rng.choice(usable(VH.HERO_SUB, len(rest), sub_flags)), sub_ctx)
    a1_text = render(rng.choice(usable(VH.ABOUT_A, n_items, flags)), {"closer": closers.pop()})
    b_pool = usable(VH.ABOUT_B, n_items, flags)
    if "city" in flags:
        b_pool = [t for t in b_pool if "{city}" in t] or b_pool
    b_text = render(rng.choice(b_pool), {"closer2": closers.pop(), "invite": invites.pop()})
    if n_items > 6:
        b_text += " और भी: %s." % oxford_hi(items[6:])

    cards = list(items[:6]) + [c for c in extra_cards if c not in items][:max(0, 6 - len(items[:6]))]
    lines = list(voice["feat"])
    rng.shuffle(lines)
    feats = []
    for n, raw in enumerate(cards):
        text = FILLER_LINES[raw] if raw in extra_cards and raw in FILLER_LINES else lines[n % len(lines)].format(i=raw)
        feats.append({"title": raw if not raw.isascii() else " ".join(w[:1].upper() + w[1:] for w in raw.split(" ")), "text": text})

    hl = []
    hl_texts = ["विवरण के लिए संपर्क करें.", "इसके बारे में हमसे पूछिए.", "ज़्यादा जानकारी के लिए संदेश भेजिए.", "कैसे मिलेगा, यह हमसे पूछ लीजिए."]
    rng.shuffle(hl_texts)
    for n, o in enumerate(offers[:3]):
        hl.append({"title": o["text_hi"], "text": hl_texts[n % len(hl_texts)]})
    if facts.get("hours") and len(hl) < 4:
        hl.append({"title": "खुलने का समय", "text": "समय: %s. आइए या संदेश भेजिए." % facts["hours"]})
    base_hl = list(lang_hi.HIGHLIGHTS.get(key) or lang_hi.HIGHLIGHTS["pro"])
    rng.shuffle(base_hl)
    while len(hl) < 3 and base_hl:
        t, x = base_hl.pop()
        hl.append({"title": t, "text": x})

    steps_pool = [lang_hi.STEPS.get(key) or lang_hi.STEPS["pro"]] + ([lang_hi.STEPS_ALT[key]] if key in lang_hi.STEPS_ALT else [])
    steps = [{"title": t, "text": x} for t, x in rng.choice(steps_pool)]

    faq = [lang_hi.FAQ_COMMON[0], lang_hi.FAQ_COMMON[1]]
    if items:
        q, a = lang_hi.FAQ_ITEM_GOODS if kind in ("retail", "food") else lang_hi.FAQ_ITEM
        faq.append((q.format(item=items[0]), a.format(item=items[0])))
    faq.append(lang_hi.FAQ_THIRD.get(key, lang_hi.FAQ_THIRD["pro"]))
    if facts.get("hours"):
        faq.append((lang_hi.FAQ_HOURS[0], lang_hi.FAQ_HOURS[1].format(hours=facts["hours"])))
    if city:
        faq.append((lang_hi.FAQ_CITY[0], lang_hi.FAQ_CITY[1].format(city=city)))
    faq.append(lang_hi.FAQ_LAST)

    blog = []
    pool = list(voice["blog"])
    rng.shuffle(pool)
    for t, e in pool:
        if ("{i2}" in t or "{i2}" in e) and n_items < 2:
            continue
        if ("{i1}" in t or "{i1}" in e) and n_items < 1:
            continue
        blog.append({"title": render(t), "excerpt": render(e)})
        if len(blog) == 3:
            break
    cta_pool = [c for c in voice["cta_text"] if "{i1}" not in c or n_items]
    return {
        "hero_heading": hero, "tagline": sub, "about": [a1_text, b_text], "features": feats, "highlights": hl[:4], "steps": steps,
        "faq": [{"q": q, "a": a} for q, a in faq], "blog": blog,
        "cta_primary": a1, "cta_secondary": a2, "cta_text": render(rng.choice(cta_pool)), "cta_title": rng.choice(VH.CTA_TITLES),
        "stats_title": rng.choice(VH.STATS_TITLES), "steps_title": lang_hi.UI["steps_title"], "faq_title": lang_hi.UI["faq_title"],
        "blog_title": rng.choice(VH.BLOG_TITLES), "features_title": lang_hi.UI["features_title"], "used_typical": [],
    }
