"""REPO ONLY. How well does the content AI understand what people type? Uses the spec document's own requests (corecraft/data/niches.json): 99 niches x 6 ways of
asking (594) and the 20 business types x 3 (60).
Run: python3 training/eval_requests.py [-v]          against the default list (the spec's 99 niches)
     python3 training/eval_requests.py --fresh       hand-written requests, default list
     python3 training/eval_requests.py --author      the same requests against the author's 77-type list (corecraft/data/author_niches.json), only for spec niches that
                                                     have an equivalent business type (corecraft/pack_spec.py AUTHOR_EQUIV), plus how many spec niches have none
1. all requests, full keyword lists
2. hold-out: for every niche, the exact words used in its own requests are taken OUT of its keywords, label and services before it is asked
   (so "termite treatment" must be understood from the other words: cockroach, pest, fumigation ...)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from corecraft import pack_request as R   # noqa: E402
from corecraft import pack_writer as W   # noqa: E402

SPEC_FILE = W.NICHE_FILE
if "--author" not in sys.argv:
    W.use_niche_file(SPEC_FILE)

VERBOSE = "-v" in sys.argv


def niche_requests():
    out = []
    for n in W.spec()["niches"]:
        x, x2, y, z, x5, x6 = n["requests"]
        reqs = ["%s website" % x, "Create a website for a %s in Jaipur" % x2, "mujhe %s ki website banakar do" % y, "meri %s ki dukaan ke liye website banao, with online contact and WhatsApp" % z,
                "modern %s website with animation, premium colours and a gallery" % x5, "%s landing page, short, with pricing and FAQ" % x6]
        out += [(r, n["id"], {x, x2, y, z, x5, x6}) for r in reqs]
    return out


def type_requests():
    out = []
    for t in W.spec()["types"]:
        reqs = re.findall(r"(?:[a-z ,]+ website|Create a modern website for [^m]+?(?= mujhe)|mujhe .+? ki website chahiye)", t["requests"])
        parts = t["requests"].split(" Create a modern website for ")
        first = parts[0]
        rest = parts[1].split(" mujhe ")
        out += [(first, t["theme"]), ("Create a modern website for " + rest[0], t["theme"]), ("mujhe " + rest[1], t["theme"])]
    return out


def run(label, reqs, drop=None):
    R.rebuild(drop)
    ok = 0
    bad = []
    for r, nid, *_ in reqs:
        u = R.understand(r, drop=drop)
        got = u["niche"]
        if got == nid:
            ok += 1
        else:
            bad.append((r, nid, got, u["scores"][:2]))
    print("%-58s %d/%d = %.1f%%" % (label, ok, len(reqs), 100 * ok / len(reqs)))
    if VERBOSE:
        for b in bad[:25]:
            print("     miss:", b)
    return ok, len(reqs)


def main():
    nr = niche_requests()
    print("niche requests: %d (99 niches x 6 styles)" % len(nr))
    run("1. niche requests, all keywords known", nr)
    drop = {}
    for r, nid, words in nr:
        d = drop.setdefault(nid, set())
        for w in words:
            d.add(R._norm(w))
    run("2. HOLD-OUT: the words used in the request are removed", nr, drop)
    by = {}
    for r, nid, words in nr:
        by.setdefault(nr.index((r, nid, words)) % 6, []).append((r, nid, words))
    print("   by way of asking (hold-out):")
    for i, name in enumerate(["X website", "Create a website for a X in Jaipur", "mujhe Y ki website banakar do", "meri Z ki dukaan ke liye ...", "modern X website ...", "X landing page ..."]):
        sub = [x for x in nr if nr.index(x) % 6 == i]
        R.rebuild(drop)
        ok = sum(R.understand(r, drop=drop)["niche"] == nid for r, nid, _ in sub)
        print("      %-40s %d/%d" % (name, ok, len(sub)))
    R.rebuild()
    tr = type_requests()
    exact = [(r, th) for r, th in tr if r.startswith("Create a modern website for")]
    short = [(r, th) for r, th in tr if not r.startswith("Create a modern website for")]
    ok = sum(R.understand(r)["niche"] is None and R.understand(r)["type_theme"] == th for r, th in exact)
    print("%-58s %d/%d" % ("3. 'Create a modern website for <business type>' -> type pack", ok, len(exact)))
    ok = 0
    for r, th in short:
        u = R.understand(r)
        right = (u["niche"] is None and u["type_theme"] == th) or (u["niche"] is not None and W.entry(u["niche"])["theme"] == th)
        ok += right
        if VERBOSE and not right:
            print("     short type miss:", r, "->", u["niche"], u["type_theme"], "expected theme", th)
    print("%-58s %d/%d" % ("4. a bare type word ('gym website') -> a niche or pack of that type", ok, len(short)))
    R.rebuild()


if __name__ == "__main__" and "--fresh" not in sys.argv and "--author" not in sys.argv:
    main()


# requests written by hand AFTER the index was built (not from the PDF): the honest test
FRESH = [
    ("I need a website for my chai tapri in Pune", {"chai_tea_stall"}), ("dukaan ke liye website: kirana store in Lucknow", {"kirana_grocery"}), ("website for my kids tuition classes in Delhi", {"tuition_centre"}),
    ("yoga teacher training in Rishikesh website", {"yoga_retreat"}), ("mujhe AC repair ki website chahiye Noida mein", {"ac_repair"}), ("website banao meri bakery ke liye, name Cake Walk, Indore", {"bakery_cakes"}),
    ("need a site for our law firm", {"law_firm_advocate"}), ("wedding photographer portfolio website", {"photography_studio"}), ("online coaching for UPSC website", {"online_coach_courses", "tuition_centre"}),
    ("physiotherapy clinic landing page", {"physiotherapy"}), ("pet shop and grooming website", {"pet_grooming_vet"}), ("website for a plumber in Jaipur", {"plumber_electrician"}),
    ("mujhe gym ki website banani hai", {"gym_fitness_studio"}), ("farm stay website in Coorg", {"farm_stay_homestay"}), ("sweet shop website with online order", {"sweet_shop_mithai"}),
    ("CA firm website for GST and ITR filing", {"chartered_accountant"}), ("mobile repair shop website Mumbai", {"mobile_repair"}), ("scrap dealer website", {"scrap_recycling"}),
    ("wedding DJ booking website", {"wedding_dj_sound"}), ("NGO for stray dogs website", {"animal_welfare"}), ("SaaS startup landing page for invoicing software", {"saas_startup"}),
    ("interior designer website for modular kitchens", {"interior_designer"}), ("tiffin service in Bangalore", {"tiffin_service"}), ("mujhe jewellery shop ki website banakar do", {"jewellery_shop"}),
    ("dental clinic website in Pune", {"dental_clinic"}), ("bridal makeup artist website", {"bridal_makeup"}), ("pg for girls website near college", {"pg_hostel"}),
    ("car wash and detailing website", {"car_wash_detailing"}), ("digital marketing agency website", {"digital_marketing_agency"}), ("temple trust website for donations", {"temple_trust"}),
    ("driving school website Hyderabad", {"driving_school"}), ("mujhe ek hotel ki website chahiye", {"hotel_guesthouse"}), ("ice cream parlour website", {"ice_cream_parlour"}),
    ("cloud kitchen website for biryani", {"cloud_kitchen"}), ("solar panel installation company website", {"solar_installer"}), ("diagnostic lab website with home sample collection", {"diagnostic_lab"}),
    ("toy shop website", {"toy_store"}), ("cafe website with menu", {"cafe_coffee_tea"}), ("banquet hall website for weddings", {"banquet_hall_venue"}), ("astrologer website", {"astrologer_vastu"}),
    ("pest controll website for flats", {"pest_control"}), ("meri tatoo studio ki website banao", {"tattoo_studio"}), ("dukan ke liye dental clinc ki website", {"dental_clinic"}),
    ("website for my carpenter business in Surat", {"carpentry_furniture"}), ("coworking space website Bengaluru", {"coworking_space"}), ("florist website with bouquets", {"florist"}),
    ("hair salon and spa website", {"hair_salon_spa"}), ("barber shop website for men", {"barber_shop"}), ("restaurant website with table booking", {"restaurant_dining"}),
    ("general physician clinic website", {"general_physician_clinic"}), ("real estate agent website for flats and plots", {"real_estate_agent"}), ("immigration consultant website for study visa", {"immigration_consultant"}),
]


def fresh():
    R.rebuild()
    ok, bad = 0, []
    for r, ok_ids in FRESH:
        u = R.understand(r)
        if u["niche"] in ok_ids:
            ok += 1
        else:
            bad.append((r, u["niche"], u["type_theme"], sorted(ok_ids)))
    print("5. FRESH hand-written requests (not from the PDF)            %d/%d = %.1f%%" % (ok, len(FRESH), 100 * ok / len(FRESH)))
    for b in bad:
        print("     miss:", b)


if __name__ == "__main__" and "--fresh" in sys.argv:
    fresh()


def spec_requests():
    """The spec's 594 niche requests (six ways of asking per niche), read from corecraft/data/niches.json whatever list is in use."""
    spec = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    out = []
    for n in spec["niches"]:
        x, x2, y, z, x5, x6 = n["requests"]
        out += [(r, n["id"]) for r in ("%s website" % x, "Create a website for a %s in Jaipur" % x2, "mujhe %s ki website banakar do" % y,
                                        "meri %s ki dukaan ke liye website banao, with online contact and WhatsApp" % z,
                                        "modern %s website with animation, premium colours and a gallery" % x5, "%s landing page, short, with pricing and FAQ" % x6)]
    return out


def author():
    """Author list: a request for a spec niche is right when it lands on one of the business types that is the same business."""
    from corecraft.pack_spec import AUTHOR_EQUIV
    W.use_niche_file(W.AUTHOR_FILE)
    R.rebuild()
    none = sorted(k for k, v in AUTHOR_EQUIV.items() if not v)
    print("author list: %d niches | spec niches with no equivalent business type: %d of %d (%s)" % (len(W.niches()), len(none), len(AUTHOR_EQUIV), ", ".join(none)))
    reqs = [(r, nid) for r, nid in spec_requests() if AUTHOR_EQUIV[nid]]
    ok, bad = 0, []
    for r, nid in reqs:
        got = R.understand(r)["niche"]
        if got in AUTHOR_EQUIV[nid]:
            ok += 1
        else:
            bad.append((r, nid, got))
    print("%-58s %d/%d = %.1f%%" % ("spec requests, niches with an equivalent", ok, len(reqs), 100 * ok / len(reqs)))
    fr = [(r, {t for i in ids for t in AUTHOR_EQUIV[i]}) for r, ids in FRESH]
    fr = [(r, ids) for r, ids in fr if ids]
    okf = sum(R.understand(r)["niche"] in ids for r, ids in fr)
    print("%-58s %d/%d = %.1f%%" % ("FRESH hand-written requests, niches with an equivalent", okf, len(fr), 100 * okf / len(fr)))
    if VERBOSE:
        for b in bad:
            print("     miss:", b)
        for r, ids in fr:
            got = R.understand(r)["niche"]
            if got not in ids:
                print("     fresh miss:", r, got, sorted(ids))


if __name__ == "__main__" and "--author" in sys.argv:
    author()
