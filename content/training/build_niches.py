"""Write the two niche lists the pack writer reads (both ship in the pip package):

corecraft/data/niches.json (the default): the 99 niches + 20 business types of the owner's spec document (corecraft/data/niche_spec.json, from training/import_niches.py)
with the hand-written layer of corecraft/pack_spec.py (text bank, prices, Devanagari keywords, button, team, menu per niche).

corecraft/data/author_niches.json: the author's 77 business types of corecraft/business_types.py (label, keywords, typical offerings, buttons, mood), the families and
prices of corecraft/pack_niches.py and the general packs of corecraft/pack_types.py; where a business type is clearly the same business as a spec niche, that niche's
prices, button, team and menu (pack_spec.SPEC_OF). Each niche records the spec niches that are the same business ("spec_equiv"); a type no spec niche covers is
the fallback for requests the default list does not know. Use the whole list with CORECRAFT_NICHE_FILE=author.
Run: python3 training/build_niches.py   (rerunnable; the output only changes when the inputs do)"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from corecraft import pack_spec as C   # noqa: E402
from corecraft.business_types import _NOT_OFFERINGS, T   # noqa: E402
from corecraft.content_engine import TYPE_TYPICAL   # noqa: E402
from corecraft.kind_content import KIND_COMMON, KIND_NEUTRAL   # noqa: E402
from corecraft.pack_niches import FAMILY, FAMILY_MOOD, FAMILY_PRICES, PRICES, QUALIFIER   # noqa: E402
from corecraft.pack_types import GENERAL_KEYWORDS, TYPE_MENUS, TYPES   # noqa: E402

AUTHOR_OUT = ROOT / "corecraft" / "data" / "author_niches.json"
VOCAB = set(json.loads((ROOT / "corecraft" / "data" / "vocab.json").read_text(encoding="utf-8")))
SPEC = ROOT / "corecraft" / "data" / "niche_spec.json"
SPEC_OUT = ROOT / "corecraft" / "data" / "niches.json"
WEAK = {"packages", "services", "plans", "systems", "upgrades", "options", "events", "projects", "programs", "essentials", "favourites", "supplies"}
GENERIC = {"services", "service", "shop", "company", "store", "studio", "agency", "centre", "center", "clinic", "business", "website", "app", "tech", "api", "platform", "cloud",
           "pet", "hair", "beauty", "trust", "foundation", "store", "showroom", "rental", "trip", "classes", "study", "tour", "paint", "electric", "steel", "gold", "farm", "milk"}
STEMS = {"orthodont", "ayurved", "chiropract", "plumb", "landscap", "sanitiz", "photograph", "videograph", "illustrat", "jewel", "pre-wedding"}


def tc(s):
    return " ".join(w[:1].upper() + w[1:] if w[:1].isalpha() else w for w in s.split())


def clean_label(s):
    return s.replace(" & ", " and ").replace("Café", "Cafe").replace("é", "e")


def offer_name(x):
    x = x if re.search(r"-ups?$", x) else x.replace("-", " ")
    return tc(x)


OFFER_COUNT = {}
for _t in T.values():
    for _x in set(_t["offers"] or []):
        OFFER_COUNT[_x] = OFFER_COUNT.get(_x, 0) + 1


def services(tid, t):
    """Six service names: the type's own offerings first (process words and weak words last), then the type's and its group's typical items."""
    own = [x for x in (t["offers"] or []) if x not in _NOT_OFFERINGS]
    own = sorted(own, key=lambda x: (x in WEAK, OFFER_COUNT[x] >= 3))   # what only this trade offers first: "pipes" before "repairs", so two trades do not read alike
    pool = [x for x in own if x not in WEAK] + TYPE_TYPICAL.get(tid, []) + [x for x in own if x in WEAK] + KIND_COMMON.get(t["niche"], []) + KIND_NEUTRAL.get(t["niche"], [])
    out, seen, qualified = [], set(), set()
    shared = {x for x in own if OFFER_COUNT[x] >= 2} | {x for x in pool if x not in own and x not in TYPE_TYPICAL.get(tid, [])}
    for x in pool:
        name = offer_name(x)
        q = QUALIFIER[tid]
        if x in shared and q.lower() not in name.lower() and len(name.split()) == 1:
            name = "%s %s" % (q, name)   # "Repairs" is every trade's word; "AC Repairs" is this one's
            qualified.add(name)
        if any(o.split()[-1].lower() == name.split()[-1].lower() and (o in qualified or name in qualified) for o in out):
            continue   # "Festive Boxes" next to "Festival Boxes", "Gym Classes" next to "Group Classes": one is enough
        if name.lower() in seen or len(name) > 30:
            continue
        seen.add(name.lower())
        out.append(name)
        if len(out) == 6:
            break
    assert len(out) == 6, (tid, out)
    return out


def keywords(t):
    keys = [k.strip().lower() for k in t["keys"] if k.strip() and "~" not in k]
    out, seen = [], set()
    for k in keys:
        if k in seen or k in GENERIC or k in STEMS:
            continue
        if k.isascii() and " " not in k and k not in VOCAB and any(w != k and w.startswith(k) for o in keys if o.isascii() for w in o.split()):
            continue   # a word stem used for matching ("orthodont"), not a word people type
        seen.add(k)
        out.append(k)
    return out


def requests(label, kws, shared=()):
    """Six ways to name the business (for tests and the request checks): the label, then keywords no other type has, one in Devanagari."""
    out = [label.lower()]
    kws = [k for k in kws if k not in shared]
    for k in [k for k in kws if k.isascii()] + [k for k in kws if not k.isascii()][:1]:
        if k not in out and len(out) < 6:
            out.append(k)
    deva = [k for k in kws if not k.isascii()]
    if deva and not any(not k.isascii() for k in out):
        out[-1] = deva[0]
    return out


def menu_json(m):
    if not m:
        return None
    title, lead, cats = m
    return {"title": title, "lead": lead, "categories": [{"name": n, "items": list(i)} for n, i in cats]}


def reuse(table, tid, what):
    """The value of the spec niche that is the same business, unless it echoes the spec's own service words (pack_spec.REUSE_SKIP)."""
    cid = C.SPEC_OF.get(tid)
    return None if not cid or tid in C.REUSE_SKIP[what] else table.get(cid)


def author():
    seen = {}
    for t in T.values():
        for k in keywords(t):
            seen[k] = seen.get(k, 0) + 1
    shared = {k for k, c in seen.items() if c > 1}
    niches = []
    for tid, t in T.items():
        fam = FAMILY[tid]
        cid = C.SPEC_OF.get(tid)
        label = clean_label(t["label"])
        kws = keywords(t)
        menu = menu_json(C.MENUS.get(cid)) if cid else None
        niches.append({
            "id": tid, "label": label, "theme": fam, "family": fam, "mood": t["mood"], "services": services(tid, t), "keywords": kws, "requests": requests(label, kws, shared),
            "food": bool(menu), "prices": [list(p) for p in (PRICES.get(tid) or reuse(C.PRICES, tid, "prices") or FAMILY_PRICES[fam])],
            "button": reuse(C.BUTTON, tid, "button") or tc(t["ctas"][0]), "team": reuse(C.TEAM, tid, "team"), "menu": menu,
            "spec_equiv": sorted(i for i, v in C.AUTHOR_EQUIV.items() if tid in v),
        })
        if not niches[-1]["spec_equiv"]:
            niches[-1]["spec_theme"] = C.FALLBACK_THEME[tid]   # the theme its pack gets when it answers a request in the default list
    types = []
    for theme, (label, fam, items, prices, button) in TYPES.items():
        members = [tid for tid, f in FAMILY.items() if f == fam] if theme != "general" else []
        kws = []
        for i in range(8):   # the first keywords of each business type of the family, round robin, so every type is represented
            for tid in members:
                k = [k for k in keywords(T[tid]) if k.isascii()]
                if i < len(k) and k[i] not in kws and len(kws) < 12:
                    kws.append(k[i])
        types.append({"theme": theme, "label": label, "family": fam, "mood": FAMILY_MOOD[fam], "items": items, "keywords": kws or GENERAL_KEYWORDS,
                      "prices": [list(p) for p in prices], "button": button, "menu": menu_json(TYPE_MENUS.get(theme)), "members": members})
    return {"source": "author: corecraft/business_types.py + corecraft/pack_niches.py + corecraft/pack_types.py (training/build_niches.py)", "general": "general", "niches": niches, "types": types}


def spec_list():
    """The default list: the spec's 99 niches + 20 types with the layer of corecraft/pack_spec.py."""
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    niches = []
    for n in spec["niches"]:
        nid = n["id"]
        fam = C.FAMILY_OF[nid]
        menu = menu_json(C.MENUS.get(nid))
        niches.append(dict(n, family=fam, mood=C.SPEC_MOOD.get(n["theme"], "friendly"), keywords=n["keywords"] + C.HI_KEYS.get(nid, []), food=bool(menu),
                           prices=[list(p) for p in C.PRICES[nid]], button=C.BUTTON.get(nid), team=C.TEAM.get(nid), menu=menu))
    types = []
    for t in spec["types"]:
        short, fam, items, kws, prices, button = C.SPEC_TYPES[t["theme"]]
        types.append({"theme": t["theme"], "label": t["type_text"][:1].upper() + t["type_text"][1:], "text": t["type_text"], "short": short, "family": fam,
                      "mood": C.SPEC_MOOD.get(t["theme"], "friendly"), "items": items, "keywords": kws, "prices": [list(p) for p in prices], "button": button,
                      "menu": menu_json(C.SPEC_TYPE_MENU) if t["theme"] == "food_dining" else None, "requests": t["requests"]})
    return {"source": "spec: corecraft/data/niche_spec.json + corecraft/pack_spec.py (training/build_niches.py)", "general": "general_business", "niches": niches, "types": types}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("%s: %d niches, %d types" % (path.relative_to(ROOT), len(data["niches"]), len(data["types"])))


def main():
    write(SPEC_OUT, spec_list())
    write(AUTHOR_OUT, author())


if __name__ == "__main__":
    main()
