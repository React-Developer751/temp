"""Checker for niche packs: the rules of the "Content AI: training prompts" spec, written as code (a Python port of what the spec calls check-niches: counts, lengths,
Title Case, plain punctuation, no invented numbers or claims, USD prices).
check_pack(pack) -> list of problems (empty = "0 problems"). check_batch(packs) adds the cross-pack rules (unique ids, no repeated text)."""
import re


def themes():
    """The themes a pack may have: the business types of the niche list in use (the spec's 20 by default)."""
    from . import pack_writer
    return set(pack_writer.types())

COUNTS = {"heroTitles": 3, "heroSubtitles": 3, "features": 6, "stats": 3, "faq": 5, "testimonials": 3, "marquee": 8}
GENERIC_KEYWORDS = {"services", "service", "shop", "company", "store", "studio", "agency", "centre", "center", "clinic", "business", "website"}
# invented numbers, awards, rankings and promises the pack rules forbid
DISHONEST = [r"\d\s*\+", r"\b\d+\s*(?:years?|yrs)\b", r"\b\d\.\d\b", r"award", r"#\s?1\b", r"\bno\.?\s?1\b", r"best in\b", r"100\s?%", r"\bguarantee", r"\bcure[sd]?\b", r"top[- ]rated",
             r"\btrusted by\b", r"\bthousands?\b", r"\bhundreds\b", r"\bmillions?\b", r"\brated\b", r"\bleading\b", r"\bnumber one\b", r"\bsince \d{4}\b", r"\bcertified\b", r"\bnever fail"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆↔-↪]")
NON_ASCII_PUNCT = re.compile("[‘’“”–—… ]")


def _title_case(s):
    return all(w[:1].isupper() or not w[:1].isalpha() for w in re.split(r"\s+", s.strip()) if w)


def _len(path, s, lo, hi, out):
    if not isinstance(s, str) or not (lo <= len(s) <= hi):
        out.append("%s: %d characters, need %d-%d: %r" % (path, len(s) if isinstance(s, str) else -1, lo, hi, s))


def _texts(x, path=""):
    """(path, string) for every string leaf, except id, theme and keywords."""
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in ("id", "theme", "keywords"):
                continue
            yield from _texts(v, path + "." + k if path else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _texts(v, "%s[%d]" % (path, i))


def check_pack(p, food=False, fallback=False, brand=None):
    out = []
    for k in ("id", "label", "theme", "keywords", "heroTitles", "heroSubtitles", "button", "featureTitle", "features", "stats", "steps", "faq", "cta", "about", "pricing", "gallery", "team",
              "testimonials", "blog", "marquee", "contactText"):
        if k not in p:
            out.append("missing field: %s" % k)
    if out:
        return out
    if p["theme"] not in themes():
        out.append("unknown theme %r" % p["theme"])
    for k, n in COUNTS.items():
        if len(p[k]) != n:
            out.append("%s: %d items, need %d" % (k, len(p[k]), n))
    if not (6 <= len(p["keywords"]) <= 14):
        out.append("keywords: %d, need 6-14" % len(p["keywords"]))
    for kw in p["keywords"]:
        if kw != kw.lower():
            out.append("keyword not lower case: %r" % kw)
        if kw.strip() in GENERIC_KEYWORDS:
            out.append("keyword too generic: %r" % kw)
    if len(set(p["keywords"])) != len(p["keywords"]):
        out.append("keywords repeat")
    for i, t in enumerate(p["heroTitles"]):
        _len("heroTitles[%d]" % i, t, 25, 58, out)
    for i, t in enumerate(p["heroSubtitles"]):
        _len("heroSubtitles[%d]" % i, t, 80, 150, out)
    _len("featureTitle", p["featureTitle"], 20, 60, out)
    for i, f in enumerate(p["features"]):
        _len("features[%d].title" % i, f.get("title"), 1, 30, out)
        _len("features[%d].text" % i, f.get("text"), 50, 115, out)
        if isinstance(f.get("text"), str) and f["text"].count(". ") > 0:
            out.append("features[%d].text is more than one sentence" % i)
    if len(p["steps"].get("items", [])) != 4:
        out.append("steps.items: need 4")
    if len(p["about"].get("paragraphs", [])) != 2 or len(p["about"].get("points", [])) != 3:
        out.append("about: need 2 paragraphs and 3 points")
    elif (brand or "{brand}") not in p["about"]["paragraphs"][0]:
        out.append("about.paragraphs[0] must use the brand (%s)" % (brand or "{brand}"))
    if len(p["pricing"].get("plans", [])) != 3:
        out.append("pricing.plans: need 3")
    else:
        for i, pl in enumerate(p["pricing"]["plans"]):
            if not re.fullmatch(r"\$\d+(?:\.\d{1,2})?", pl.get("price", "")):
                out.append("pricing.plans[%d].price %r is not a plain USD string" % (i, pl.get("price")))
            if not str(pl.get("period", "")).startswith("/"):
                out.append("pricing.plans[%d].period must start with /" % i)
            if len(pl.get("perks", [])) != 3:
                out.append("pricing.plans[%d]: need 3 perks" % i)
            if pl.get("price") == "$0" and "consult" not in pl.get("period", "") and i != 0:
                out.append("$0 is only for a free first step")
        prices = [float(pl["price"][1:]) for pl in p["pricing"]["plans"] if re.fullmatch(r"\$\d+(?:\.\d{1,2})?", pl.get("price", ""))]
        if len(prices) == 3 and not (prices[0] <= prices[1] <= prices[2]):
            out.append("plan prices must not fall")
    if len(p["gallery"].get("captions", [])) != 6:
        out.append("gallery.captions: need 6")
    for i, c in enumerate(p["gallery"].get("captions", [])):
        if not (2 <= len(c.split()) <= 4):
            out.append("gallery caption needs 2-4 words: %r" % c)
    if len(p["team"].get("roles", [])) != 3:
        out.append("team.roles: need 3")
    if len(p["blog"].get("posts", [])) != 3:
        out.append("blog.posts: need 3")
    for i, m in enumerate(p["marquee"]):
        if len(m) > 16 or len(m.split()) > 2:
            out.append("marquee[%d] %r: max 16 characters and 2 words" % (i, m))
    if not p["cta"]["title"].endswith("?"):
        out.append("cta.title must end with ?")
    if p["cta"]["button"] != p["button"]:
        out.append("cta.button must match button")
    # style: title case, plain punctuation, no emoji, no exclamation marks
    titles = [("button", p["button"]), ("featureTitle", p["featureTitle"]), ("steps.title", p["steps"]["title"]), ("cta.title", p["cta"]["title"]), ("cta.button", p["cta"]["button"]),
              ("about.title", p["about"]["title"]), ("pricing.title", p["pricing"]["title"]), ("gallery.title", p["gallery"]["title"]), ("team.title", p["team"].get("title", "")),
              ("blog.title", p["blog"]["title"])]
    titles += [("heroTitles[%d]" % i, t) for i, t in enumerate(p["heroTitles"])] + [("features[%d].title" % i, f["title"]) for i, f in enumerate(p["features"])]
    titles += [("steps.items[%d].title" % i, s["title"]) for i, s in enumerate(p["steps"]["items"])]
    titles += [("blog.posts[%d].title" % i, s["title"]) for i, s in enumerate(p["blog"]["posts"])]
    titles += [("plan name", pl["name"]) for pl in p["pricing"]["plans"]] + [("gallery caption", c) for c in p["gallery"]["captions"]] + [("team role", r) for r in p["team"]["roles"]]
    for path, t in titles:
        if not _title_case(t):
            out.append("%s is not Title Case: %r" % (path, t))
    for path, t in _texts(p):
        if "!" in t:
            out.append("%s has an exclamation mark" % path)
        if EMOJI.search(t) or NON_ASCII_PUNCT.search(t):
            out.append("%s has an emoji or a non-ASCII punctuation mark: %r" % (path, t))
        low = t.lower()
        for rx in DISHONEST:
            if re.search(rx, low):
                out.append("%s makes a claim the pack rules forbid (%s): %r" % (path, rx, t))
                break
        if re.search(r"\bmy business\b|\blorem\b|\bsample customer\b|\{\{|\}\}|\{(?!brand\})", low):
            out.append("%s has placeholder text: %r" % (path, t))
        if any("ऀ" <= ch <= "ॿ" for ch in t):
            out.append("%s has Devanagari in an English pack" % path)
    # every text is different from every other text
    seen = {}
    for path, t in _texts({k: v for k, v in p.items() if k not in ("label",)}):
        key = re.sub(r"\s+", " ", t.strip().lower())
        if len(key) < 25 or path in ("button", "cta.button") or path.startswith(("marquee", "gallery.captions")) or path.endswith((".period", ".price")):
            continue   # short labels (a plan name, a caption, a stat) may repeat a service name; sentences and titles may not repeat
        if key in seen:
            out.append("repeated text in %s and %s: %r" % (seen[key], path, t))
        seen.setdefault(key, path)
    for i, t in enumerate(p["testimonials"]):
        if not t.get("quote") or not t.get("role"):
            out.append("testimonials[%d] needs quote and role" % i)
    if food:
        menu = p.get("menu")
        if not menu:
            out.append("a food business needs a menu block")
        else:
            cats = menu.get("categories", [])
            if not (3 <= len(cats) <= 4):
                out.append("menu: need 3-4 categories")
            for c in cats:
                if not (5 <= len(c.get("items", [])) <= 6):
                    out.append("menu category %r: need 5-6 items" % c.get("name"))
                for it in c.get("items", []):
                    if re.search(r"[$₹]|\brs\.?\s?\d|\d{2,}", it):
                        out.append("menu item has a price: %r" % it)
            if not menu.get("lead") or not menu.get("title"):
                out.append("menu needs title and lead")
    return out


def check_batch(packs, foods=()):
    out = []
    ids = [p["id"] for p in packs]
    for i in set(ids):
        if ids.count(i) > 1:
            out.append("id repeats: %s" % i)
    seen = {}
    for p in packs:
        out += ["%s: %s" % (p["id"], x) for x in check_pack(p, food=p["id"] in foods)]
        for path, t in _texts({k: v for k, v in p.items() if k not in ("label",)}):
            key = re.sub(r"\s+", " ", t.strip().lower())
            if len(key) < 25:
                continue
            if key in seen and seen[key] != p["id"]:
                out.append("%s: text also in %s: %r" % (p["id"], seen[key], t))
            seen.setdefault(key, p["id"])
    return out
