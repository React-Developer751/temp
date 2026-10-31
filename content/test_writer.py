"""Tests for the facts reader, the per-kind voice, the sub-niche vocabulary, the page validators and the detector."""
import json
import os
import random
import re
import sys
import unittest
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "training"))

os.environ.setdefault("CORECRAFT_NO_PHOTOS", "1")        # content tests do not need pictures (test_photos.py does)
from corecraft import detector, validators, voice_data
from corecraft.business_types import T, detect_type
from corecraft.content_engine import generate_content
from corecraft.facts import extract_facts, hours_for_english
from corecraft.profiles import FOREIGN, KINDS, SERVICE_KINDS, TYPE_KIND
from corecraft.validators import leaves_of, validate_page
from corecraft.voice_data import VOICE

ITALIAN = "Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu, weekend brunch, open 12pm to 11pm, online booking"
BANNED = ["lunch thali", "home style curry", "starter or soup", "your main dishes", "sample customer", "john snow", "123 sample street", "example.com", "(555)",
          "results that speak for themselves", "lorem"]


def facts_for(prompt):
    tid = detect_type(prompt)[0]
    t = T.get(tid)
    return extract_facts(prompt, type_keys=t["keys"] if t else (), type_label=t["label"] if t else "")


def page_text(c):
    return " ".join(t for _, t, _ in leaves_of(c)).lower()


class FactsReader(unittest.TestCase):
    def test_italian_example(self):
        f = facts_for(ITALIAN)
        self.assertEqual((f["name"], f["city"], f["hours"]), ("Forno Rosso", "Mumbai", "12pm to 11pm"))
        self.assertEqual(f["items"], ["wood fired pizza", "fresh pasta", "tiramisu", "weekend brunch"])
        self.assertEqual([o["id"] for o in f["offers"]], ["online_booking"])

    def test_hinglish_fillers_do_not_leak_into_name_or_items(self):
        f = facts_for("mujhe ek Italian restaurant ki website chahiye, naam Forno Rosso, Mumbai mein, wood fired pizza, pasta aur tiramisu, dopahar 12 se raat 11 tak")
        self.assertEqual((f["name"], f["city"]), ("Forno Rosso", "Mumbai"))
        self.assertEqual(f["items"], ["wood fired pizza", "pasta", "tiramisu"])
        c = generate_content("mujhe ek bike showroom ki website chahiye Jaipur mein", 1)
        blob = page_text(c) + c["brand"].lower()
        for w in ("mujhe", "chahiye", "website"):
            self.assertNotIn(w, blob)
        self.assertEqual(c["business_type"], "autosales")

    def test_hindi_list(self):
        f = facts_for("जयपुर में रेस्टोरेंट: बिरयानी, कबाब, मिठाई और चाय। फोन 9811122233")
        self.assertEqual(f["items"], ["बिरयानी", "कबाब", "मिठाई", "चाय"])
        self.assertEqual((f["city"], f["phone"]), ("जयपुर", "9811122233"))

    def test_offers_hours_prices(self):
        f = facts_for("ladies kurti boutique Rani Boutique Jaipur, free shipping, COD, easy returns, kurtis starting Rs 599, sarees from Rs 1,999")
        self.assertEqual({o["id"] for o in f["offers"]}, {"free_shipping", "cod", "returns"})
        self.assertEqual(f["prices"], [{"name": "Kurtis", "price": "from Rs 599"}, {"name": "Sarees", "price": "from Rs 1,999"}])
        self.assertEqual(f["name"], "Rani Boutique")
        self.assertEqual(hours_for_english("dopahar 12 se raat 11 baje tak"), "12pm to 11pm")

    def test_services_that_are_also_type_words_are_kept(self):
        f = facts_for("लखनऊ में बेकरी: केक, पेस्ट्री, ब्राउनी और कुकीज़")
        self.assertEqual(f["items"], ["केक", "पेस्ट्री", "ब्राउनी", "कुकीज़"])
        f = facts_for("Dentist in Chandigarh for kids dentistry, aligners, crowns and wisdom tooth removal")
        self.assertEqual(f["items"][0], "kids dentistry")
        f = facts_for("SaaS startup InvoiceFlow, Bangalore, invoicing, payment reminders, expense tracking and reports, free trial")
        self.assertIn("payment reminders", f["items"])   # "reminders" must not be read as the EMI offer


class ItalianPage(unittest.TestCase):
    def test_every_named_thing_and_nothing_foreign(self):
        heroes = set()
        for seed in range(40):
            c = generate_content(ITALIAN, seed)
            heroes.add(c["hero_heading"])
            blob = page_text(c)
            for s in ("wood fired pizza", "fresh pasta", "tiramisu", "weekend brunch"):
                self.assertIn(s.replace(" fired", "-fired") if "wood" in s else s, blob.replace("wood fired", "wood-fired"), (seed, s))
            for bad in BANNED + ["thali", "curry", "dosa", "idli", "naan", "biryani", "help people"]:
                self.assertNotIn(bad, blob, (seed, bad))
            self.assertEqual(c["profile"], "italian")
            self.assertEqual(c["kind"], "food")
            self.assertIn("Mumbai", c["about"][0] + c["about"][1])
        self.assertIn("Wood-fired pizza and fresh pasta in Mumbai", heroes)
        self.assertGreaterEqual(len(heroes), 6)

    def test_cards_steps_and_facts(self):
        c = generate_content(ITALIAN, 3)
        self.assertEqual([f["title"] for f in c["features"]], ["Wood-fired Pizza", "Fresh Pasta", "Tiramisu", "Weekend Brunch"])
        self.assertTrue(all(len(f["text"]) > 30 for f in c["features"]))
        self.assertEqual(len({f["text"] for f in c["features"]}), 4)
        steps = " ".join(s["title"] for s in c["steps"]).lower()
        self.assertTrue(any(k in steps for k in ("book", "reserve")))
        titles = {s["title"] for seed in range(30) for s in generate_content(ITALIAN, seed)["steps"]}
        self.assertIn("Choose your pizza", titles)
        self.assertIn("Book a table", titles)
        self.assertEqual(c["hours"], "12pm to 11pm")
        self.assertEqual(c["offers"], [{"id": "online_booking", "text": "Online booking"}])
        self.assertEqual(c["cta_primary"], "Book a table online")
        self.assertEqual(c["missing"], ["prices", "phone", "email", "address"])
        self.assertEqual(c["facts_used"]["city"], {"value": "Mumbai", "source": "prompt"})
        self.assertEqual(c["needs_review"], [])

    def test_cuisines_never_mix(self):
        for prompt, bad in (("South Indian restaurant Udupi Bhavan, Chennai, masala dosa, idli, vada, filter coffee", ["pasta", "pizza", "naan", "biryani", "tandoori", "noodles"]),
                            ("Chinese restaurant Golden Wok in Kolkata, hakka noodles, manchurian, momos", ["pasta", "pizza", "thali", "dosa", "naan", "biryani"]),
                            ("bakery Sweet Crumbs in Pune, custom cakes, cupcakes, brownies", ["thali", "curry", "dosa", "biryani", "noodles"])):
            for seed in range(15):
                blob = page_text(generate_content(prompt, seed))
                for b in bad:
                    self.assertNotIn(b, blob, (prompt[:20], seed, b))


class NoInvention(unittest.TestCase):
    def test_empty_fields_stay_empty_and_are_listed(self):
        c = generate_content("dental clinic in Pune offering braces, implants and whitening", 2)
        self.assertEqual((c["hours"], c["prices"], c["offers"]), ("", [], []))
        self.assertIn("phone", c["missing"])
        self.assertIn("hours", c["missing"])
        self.assertNotIn("pricing", c)
        self.assertFalse(re.search(r"\d", " ".join([c["hero_heading"], c["tagline"]] + c["about"] + [f["text"] for f in c["features"]])))

    def test_no_placeholder_text_anywhere(self):
        for prompt in ("dental clinic", "gym", "cafe in Pune", "plumbing repairs", ITALIAN, "boutique hotel with rooms, spa and restaurant in Udaipur"):
            for seed in range(8):
                blob = page_text(generate_content(prompt, seed)) + json.dumps(generate_content(prompt, seed)["contact"]).lower()
                for b in BANNED:
                    self.assertNotIn(b, blob)
                self.assertNotRegex(blob, r"\bsample\b|\bjohn\b|\bjane\b|\b555\b|\b123\b")


class Validators(unittest.TestCase):
    def page(self, **kw):
        base = {"hero_heading": "Wood-fired pizza in Mumbai", "tagline": "Forno Rosso serves pizza.", "about": ["A good place to eat.", "Open daily."], "features": [{"title": "Pizza", "text": "Baked hot."}],
                "highlights": [], "steps": [], "faq": [], "blog": []}
        base.update(kw)
        return base

    def test_placeholders_are_rejected_unless_in_the_prompt(self):
        for bad in ("Sample Customer loves it", "call +1 (555) 000-0000", "hello@example.com", "Lorem ipsum dolor", "Your main dishes", "Starter or soup", "John snow said so", "123 Sample Street"):
            self.assertTrue(validators.check_placeholders([("about.0", bad, False)], "pizza in Mumbai"), bad)
        self.assertFalse(validators.check_placeholders([("about.0", "Sample menu", False)], "we offer a sample menu"))

    def test_repeats_are_rejected(self):
        a = [("about.0", "Slowly baked in a wood fired oven for a blistered crust.", False), ("features.0.text", "Baked in a wood fired oven for a blistered crust every time.", False)]
        self.assertTrue(validators.check_repeats(a))
        self.assertFalse(validators.check_repeats([("a", "Wood fired pizza.", False), ("b", "Fresh pasta daily.", False)]))

    def test_other_niches_words_are_rejected(self):
        leaves = [("about.0", "Try the butter chicken with naan.", False)]
        self.assertTrue(validators.check_wrong_niche(leaves, "food", "italian", "pizza and pasta"))
        self.assertFalse(validators.check_wrong_niche(leaves, "food", "italian", "pizza, naan and butter chicken"))
        self.assertTrue(validators.check_wrong_niche([("a", "Book an appointment with the patient.", False)], "food", "italian", "pizza"))

    def test_help_frames_only_for_service_kinds(self):
        leaves = [("about.0", "We help people with pizza.", False)]
        self.assertTrue(validators.check_help_frames(leaves, "food"))
        self.assertFalse(validators.check_help_frames(leaves, "pro"))

    def test_missing_service_is_reported(self):
        self.assertTrue(validators.check_services([("a", "We bake bread.", False)], ["tiramisu"]))
        self.assertFalse(validators.check_services([("a", "Tiramisu and bread.", False)], ["tiramisu"]))


class Kinds(unittest.TestCase):
    def test_every_type_has_a_kind_and_there_are_enough_types(self):
        self.assertGreaterEqual(len(T), 72)
        self.assertEqual(set(TYPE_KIND), set(T))
        self.assertEqual(set(TYPE_KIND.values()), set(KINDS))
        self.assertEqual(len(KINDS), 14)

    def test_each_kind_has_enough_alternatives_per_slot(self):
        for kind, v in VOICE.items():
            self.assertGreaterEqual(len(v["closers"]) + len(voice_data.GENERIC["closers"]), 8, kind)
            self.assertGreaterEqual(len(v["closers"]), 8, kind)
            self.assertGreaterEqual(len(v["invites"]), 8, kind)
            self.assertGreaterEqual(len(v["feat"]), 8, kind)
            self.assertGreaterEqual(len(v["blog"]), 8, kind)
            self.assertGreaterEqual(len(v["cta_text"]), 8, kind)
            self.assertGreaterEqual(len(v["faq"]), 8, kind)
            self.assertGreaterEqual(len(v["highlights"]), 6, kind)
            self.assertGreaterEqual(len(v["steps"]), 3, kind)
        for slot in (voice_data.HERO_TITLE, voice_data.HERO_SUB, voice_data.ABOUT_A, voice_data.ABOUT_B):
            self.assertGreaterEqual(len(slot), 8)
        self.assertGreaterEqual(len(voice_data.STATS_TITLES), 8)

    def test_kinds_speak_their_own_verbs(self):
        self.assertIn("serves", VOICE["food"]["does"])
        self.assertIn("treats", VOICE["health"]["does"])
        self.assertIn("trains", VOICE["fitness"]["does"])
        self.assertIn("stocks", VOICE["retail"]["does"])
        self.assertIn("automates", VOICE["software"]["does"])

    def test_help_frames_never_appear_on_other_kinds(self):
        for tid, t in T.items():
            c = generate_content(t["keys"][0] + " " + t["label"] + " in Pune", 4)
            if TYPE_KIND[tid] not in SERVICE_KINDS:
                self.assertNotRegex(page_text(c), r"help(?:s)? (?:people|you|clients|customers) with|whatever you need from", tid)
            self.assertEqual(c["kind"], TYPE_KIND[tid])

    def test_a_dish_page_never_uses_service_words_of_another_kind(self):
        self.assertTrue(FOREIGN["italian"])
        self.assertNotIn("pizza", FOREIGN["italian"])
        self.assertIn("thali", FOREIGN["italian"] | {"thali"})


class Variety(unittest.TestCase):
    def test_same_prompt_same_page_and_seed_changes_it(self):
        self.assertEqual(generate_content(ITALIAN), generate_content(ITALIAN))
        self.assertNotEqual(generate_content(ITALIAN, 1)["about"], generate_content(ITALIAN, 2)["about"])

    def test_same_seed_never_makes_two_businesses_read_alike(self):
        a = generate_content("Italian restaurant Forno Rosso, Mumbai, pizza, pasta, tiramisu", 7)
        b = generate_content("Italian restaurant Casa Verde, Delhi, risotto, lasagna, gelato", 7)
        sa = {x.lower() for t in [a["tagline"]] + a["about"] for x in re.split(r"(?<=[.!?])\s+", t)}
        sb = {x.lower() for t in [b["tagline"]] + b["about"] for x in re.split(r"(?<=[.!?])\s+", t)}
        self.assertLess(len(sa & sb), 2)

    def test_two_pages_of_a_niche_share_few_sentences(self):
        from evaluate import sentences
        from eval_prompts import EVAL
        by = {}
        for niche, lang, prompt, _ in EVAL:
            by.setdefault(niche, []).append(sentences(generate_content(prompt)))
        worst = 0.0
        for sets in by.values():
            for a, b in combinations(sets, 2):
                worst = max(worst, len(a & b) / len(a), len(a & b) / len(b))
        self.assertLess(worst, 0.30)

    def test_no_six_word_span_twice_on_a_page(self):
        for prompt in (ITALIAN, "dental clinic called Smile Hub in Pune offering braces, implants and whitening", "gym", "cozy cafe serving coffee"):
            for seed in range(25):
                self.assertEqual([i for i in validators.check_repeats(leaves_of(generate_content(prompt, seed))) if "repeated" in i or "sentence" in i], [], (prompt, seed))


class Detection(unittest.TestCase):
    def test_holdout_accuracy_and_silent_errors(self):
        from labelled import HOLDOUT
        ok = silent = 0
        for p, t in HOLDOUT:
            got, conf, det = detector.detect(p)
            ok += got == t
            silent += (got != t and conf != "low" and det.get("use", True))
        self.assertGreaterEqual(ok / len(HOLDOUT), 0.90)
        self.assertLessEqual(silent / len(HOLDOUT), 0.05)

    def test_hard_cases(self):
        for p, t in (("mujhe ek bike showroom ki website chahiye", "autosales"), ("robotics lab for school kids", "robotics"), ("pottery studio with weekend workshops", "pottery"),
                     ("tyre shop and wheel alignment", "tyres"), ("packers and movers in Pune", "movers"), ("kirana store near me", "grocery")):
            self.assertEqual(detector.detect(p)[0], t, p)
            self.assertEqual(generate_content(p, 1)["business_type"], t, p)

    def test_unknown_business_is_flagged_not_guessed(self):
        c = generate_content("water tanker supply in Jaipur", 1)
        self.assertEqual(c["business_type"], "general")
        self.assertTrue(any("not recognised" in n or "not in the list" in n for n in c["needs_review"]))

    def test_model_is_trained_and_saved(self):
        m = json.loads((ROOT / "corecraft" / "data" / "detector.json").read_text())
        self.assertGreater(m["trained_on"]["train_prompts"], 100)


class Languages(unittest.TestCase):
    def test_hindi_page_stays_hindi_and_names_the_services(self):
        c = generate_content("बेंगलुरु में इटैलियन रेस्टोरेंट: पिज़्ज़ा, पास्ता, तिरामिसू और गार्लिक ब्रेड", 1)
        self.assertEqual(c["lang"], "hi")
        self.assertEqual([f["title"] for f in c["features"]][:4], ["पिज़्ज़ा", "पास्ता", "तिरामिसू", "गार्लिक ब्रेड"])
        self.assertIn("बेंगलुरु", c["hero_heading"] + c["tagline"] + " ".join(c["about"]))
        self.assertFalse(re.search(r"[A-Za-z]{3,}", c["hero_heading"] + c["tagline"] + " ".join(c["about"])))

    def test_hindi_has_frames_for_every_kind(self):
        from corecraft import voice_hi
        self.assertEqual(set(voice_hi.VOICE), set(KINDS))
        for kind, v in voice_hi.VOICE.items():
            for slot in ("closers", "invites", "feat", "blog", "cta_text", "tails"):
                self.assertGreaterEqual(len(v[slot]), 4, (kind, slot))

    def test_hindi_hours_stay_hindi_and_hinglish_hours_become_english(self):
        c = generate_content("बिरयानी, कबाब, चाय वाला रेस्टोरेंट जयपुर में, रात 9 बजे तक खुला, होम डिलीवरी", 2)
        self.assertEqual(c["lang"], "hi")
        self.assertIn("रात 9 बजे तक", c["hours"])
        e = generate_content("mera restaurant Taste of Delhi hai Noida mein, butter chicken, naan aur dal makhani, subah 9 se raat 9 tak", 2)
        self.assertEqual((e["lang"], e["hours"], e["brand"]), ("en", "9am to 9pm", "Taste of Delhi"))


class Site(unittest.TestCase):
    def test_site_shows_stats_heading_and_blog(self):
        import tempfile
        from corecraft import pipeline
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run(ITALIAN, d, 2)
            pre = (Path(r["dir"]) / "preview.html").read_text()
            for needle in ('class="stats-title"', 'id="journal"', "Forno Rosso", "Wood-fired Pizza"):
                self.assertIn(needle, pre)
            self.assertEqual(r["missing"], ["prices", "phone", "email", "address"])


class CopyCheck(unittest.TestCase):
    def test_static_text_shares_no_six_word_span_with_public_pages(self):
        import check_copy
        src, files = check_copy.source_shingles()
        if not files:
            self.skipTest("no corpus files")
        static = []
        from corecraft import lexicon, voice_a, voice_b, voice_c, voice_profile
        for mod in (voice_a, voice_b, voice_c, voice_profile):
            for name in dir(mod):
                if name.isupper():
                    check_copy.strings_of(getattr(mod, name), static)
        check_copy.strings_of(voice_data.GENERIC, static)
        check_copy.strings_of(lexicon.LEX, static)
        self.assertEqual(sorted({s for t in static for s in check_copy.shingles(t) if s in src}), [])


REAL = {   # prompts modelled on real business pages and on how people type (names and phone numbers invented); name, city, items, hours as a reader would expect them
    "dental": ("Brookvale Neighborhood Dental in Brookvale, Ohio. General dental care, emergency services, cosmetic dentistry, teeth whitening, dental implants, preventative treatments. "
               "New patients welcome, walk-ins welcome, same-day emergency treatment. Mon-Wed 8am-5pm, Thu 8am-3pm. Phone 937-555-0148",
               "Brookvale Neighborhood Dental", "Brookvale", ["general dental care", "emergency services", "cosmetic dentistry", "teeth whitening", "dental implants", "preventative treatments"],
               "Mon-Wed 8am-5pm, Thu 8am-3pm"),
    "yoga": ("Stillwater, a yoga studio in Northgate: vinyasa flow, hatha foundations, restorative, breathwork & pranayama, private sessions. First class free. Open daily 6am to 9pm. 14 Linden Walk",
             "Stillwater", "Northgate", ["vinyasa flow", "hatha foundations", "restorative", "breathwork", "pranayama", "private sessions"], "6am to 9pm"),
    "bakery": ("PoppyCakes Fairview bakery in Los Angeles. Custom cakes, wedding cakes, birthday cakes, cupcakes, cookies, pies. Order online, pickup, local delivery. Open daily 11am-8pm. 323-555-0162",
               "PoppyCakes Fairview", "Los Angeles", ["custom cakes", "wedding cakes", "birthday cakes", "cupcakes", "cookies", "pies"], "11am-8pm"),
    "plumber": ("Drain-Rite Plumbing & Water Cleanup in Waikele, HI: drain cleaning, emergency plumbing, water heaters, water damage, pipe restoration. Open 24/7, 7 days a week. Special financing available. 808-555-0177",
                "Drain-Rite Plumbing & Water Cleanup", "Waikele", ["drain cleaning", "emergency plumbing", "water heaters", "water damage", "pipe restoration"], "24/7"),
    "sweets": ("Sharma Sweets & Namkeen, Karol Bagh, Delhi. Desi ghee mithai, kaju katli, samosa, kachori, gift boxes. Home delivery available. 9am-10pm. Call 9811012345",
               "Sharma Sweets & Namkeen", "Delhi", ["desi ghee mithai", "kaju katli", "samosa", "kachori", "gift boxes"], "9am-10pm"),
    "coaching": ("Mujhe ek coaching institute ki website chahiye: Pragati Classes, Kota. IIT JEE aur NEET coaching, foundation batch, test series. Free demo class. Subah 7 se shaam 8 tak",
                 "Pragati Classes", "Kota", ["IIT JEE", "NEET coaching", "foundation batch", "test series"], "7am to 8pm"),
    "skin": ("Dr. Meera Iyer's skin clinic in Koramangala, Bengaluru. Acne treatment, laser hair removal, hydrafacial, PRP. Appointments online. Mon-Sat 10am-7pm",
             None, "Bengaluru", ["acne treatment", "laser hair removal", "hydrafacial", "PRP"], "Mon-Sat 10am-7pm"),
    "law": ("Anand & Co. Advocates, family law, property disputes, divorce, wills. Chandigarh. First consultation free. +91 98765 43210",
            "Anand & Co Advocates", "Chandigarh", ["family law", "property disputes", "divorce", "wills"], None),
    "agency": ("PixelForge, a web design agency in Pune. Website design, mobile apps, SEO, branding. Free quote. hello@pixelforge.in",
               "PixelForge", "Pune", ["website design", "mobile apps", "SEO", "branding"], None),
    "vet": ("Happy Paws Pet Clinic, Austin, TX. Vaccinations, dental cleaning, spay and neuter, boarding, grooming. Open Mon-Fri 8am-6pm, Sat 9am-1pm. (512) 555-0143",
            "Happy Paws Pet Clinic", "Austin", ["vaccinations", "dental cleaning", "spay and neuter", "boarding", "grooming"], "Mon-Fri 8am-6pm, Sat 9am-1pm"),
    "boutique": ("Urban Threads boutique - women's kurtis, sarees, lehengas, dupattas. Jaipur. Free shipping, easy returns, COD",
                 "Urban Threads", "Jaipur", ["women's kurtis", "sarees", "lehengas", "dupattas"], None),
    "roaster": ("FreshBrew coffee roasters in Portland. Single origin beans, cold brew, espresso, pastries. Order online, free shipping over $40. Open daily 7am-5pm",
                "FreshBrew", "Portland", ["single origin beans", "cold brew", "espresso", "pastries"], "7am-5pm"),
    "school": ("Greenfield Public School, Indore - nursery to class 12, CBSE, sports, science labs, school bus. Admissions open",
               "Greenfield Public School", "Indore", ["nursery to class 12", "CBSE", "sports", "science labs", "school bus"], None),
    "restaurant": ("Tandoori Nights, North Indian restaurant in Gurgaon. Butter chicken, dal makhani, naan, biryani, kebabs. Table booking, home delivery, open 12pm to 11:30pm",
                   "Tandoori Nights", "Gurgaon", ["butter chicken", "dal makhani", "naan", "biryani", "kebabs"], "12pm to 11:30pm"),
    "electrician": ("Shree Ram Electricals in Nagpur: wiring, inverter installation, AC repair, fan repair. 24x7 service, home visit",
                    "Shree Ram Electricals", "Nagpur", ["wiring", "inverter installation", "AC repair", "fan repair"], "24x7"),
}


class RealPrompts(unittest.TestCase):
    def test_facts_read_as_a_person_would(self):
        for key, (prompt, name, city, items, hours) in REAL.items():
            f = facts_for(prompt)
            self.assertEqual(f["items"], items, key)
            self.assertEqual(f["city"], city, key)
            if name:
                self.assertEqual(f["name"], name, key)
            self.assertEqual(hours_for_english(f["hours"]), hours, key)

    def test_state_and_locality_are_not_services(self):
        for key in ("dental", "plumber", "vet", "sweets", "skin"):
            f = facts_for(REAL[key][0])
            self.assertFalse({"ohio", "hi", "tx", "karol bagh", "koramangala", "austin"} & {i.lower() for i in f["items"]}, key)
        self.assertEqual(facts_for(REAL["sweets"][0])["address"], "Karol Bagh")
        self.assertEqual(facts_for(REAL["yoga"][0])["address"], "14 Linden Walk")

    def test_contact_details(self):
        self.assertEqual(facts_for(REAL["dental"][0])["phone"], "937-555-0148")
        self.assertEqual(facts_for(REAL["vet"][0])["phone"], "(512) 555-0143")
        self.assertEqual(facts_for(REAL["agency"][0])["email"], "hello@pixelforge.in")

    def test_new_offers_are_read(self):
        ids = lambda k: {o["id"] for o in facts_for(REAL[k][0])["offers"]}   # noqa: E731
        self.assertTrue({"new_patients", "walk_in", "same_day"} <= ids("dental"))
        self.assertIn("free_trial", ids("yoga"))
        self.assertTrue({"online_order", "pickup", "home_delivery"} <= ids("bakery"))
        self.assertIn("financing", ids("plumber"))
        self.assertIn("admissions", ids("school"))
        self.assertIn("free_consult", ids("law"))
        self.assertIn("online_booking", ids("skin"))

    def test_pages_are_clean_and_keep_every_service(self):
        for key, (prompt, name, city, items, hours) in REAL.items():
            for seed in (None, 3):
                c = generate_content(prompt, seed)
                blob = " ".join(t for _, t, _ in leaves_of(c)).lower() + " " + " ".join(f["title"] for f in c["features"]).lower()
                for it in items:
                    self.assertIn(it.lower().replace("-", " "), blob.replace("-", " "), (key, it))
                for banned in BANNED:
                    self.assertNotIn(banned, blob, key)
                self.assertFalse([n for n in c["needs_review"] if "quality check" in n], (key, c["needs_review"]))
                self.assertNotRegex(blob, r"\.:|\.,|\bhi\b's|ohio and ", key)
                self.assertEqual(c["location"], city, key)

    def test_address_reaches_the_contact_block(self):
        self.assertEqual(generate_content(REAL["yoga"][0])["contact"]["address"], "14 Linden Walk")

    def test_bakery_and_sweets_do_not_speak_like_a_restaurant(self):
        for key in ("bakery", "sweets"):
            c = generate_content(REAL[key][0])
            blob = " ".join(t for _, t, _ in leaves_of(c)).lower()
            self.assertNotIn("book a table", blob, key)
            self.assertNotIn("hungry", blob, key)
            self.assertNotIn("the menu", c["cta_secondary"].lower(), key)

    def test_yoga_does_not_speak_like_a_gym(self):
        blob = " ".join(t for _, t, _ in leaves_of(generate_content(REAL["yoga"][0]))).lower()
        for w in ("rep", "numbers that show", "coach"):
            self.assertNotRegex(blob, r"\b" + w + r"\b", w)

    def test_school_and_agency_use_their_own_words(self):
        school = generate_content(REAL["school"][0])
        self.assertNotIn("demo", " ".join(t for _, t, _ in leaves_of(school)).lower())
        agency = generate_content(REAL["agency"][0])
        self.assertEqual(agency["business_type"], "design")
        self.assertNotIn("automates", " ".join(t for _, t, _ in leaves_of(agency)).lower())

    def test_hours_typed_by_the_person_may_repeat_but_nothing_else_may(self):
        c = generate_content(REAL["dental"][0])
        self.assertEqual(c["hours"], "Mon-Wed 8am-5pm, Thu 8am-3pm")
        self.assertFalse([n for n in c["needs_review"] if "6-word" in n])

    def test_hindi_name_after_naam(self):
        f = extract_facts("मुझे अपने फिटनेस जिम की वेबसाइट चाहिए, नाम पावर फिट, लखनऊ, वेट ट्रेनिंग, कार्डियो, ज़ुम्बा, सुबह 5 से रात 10 बजे तक")
        self.assertEqual(f["name"], "पावर फिट")
        self.assertEqual(f["items"], ["वेट ट्रेनिंग", "कार्डियो", "ज़ुम्बा"])

    def test_a_promoted_typical_offering_never_repeats_what_was_said(self):
        for key in ("plumber", "yoga", "school", "bakery"):
            items = generate_content(REAL[key][0])["generated_by"]["items_from_prompt"]
            self.assertEqual(len(items), len(REAL[key][3]), (key, items))


REAL2 = {   # a second round of prompts: names with a type word in them, localities, thresholds, contact fragments, Hindi names
    "salon": ("Glow Studio salon in Andheri, Mumbai: haircut, hair colour, keratin, bridal makeup, facial, waxing. Open Tue-Sun 10am-8pm. Book on WhatsApp 98200 11223",
              "Glow Studio", "Mumbai", ["haircut", "hair colour", "keratin", "bridal makeup", "facial", "waxing"]),
    "hotel": ("Hotel Sea Breeze, Goa - 24 AC rooms, sea view, free breakfast, airport pickup, swimming pool, free wifi. Booking: 0832-2456789",
              "Hotel Sea Breeze", "Goa", ["24 AC rooms", "sea view", "free breakfast", "swimming pool"]),
    "tours": ("Wanderlust Tours, Manali. Himachal trekking, Kullu honeymoon packages, paragliding, camping, taxi service. Call 9418012345",
              "Wanderlust Tours", "Manali", ["Himachal trekking", "Kullu honeymoon packages", "paragliding", "camping", "taxi service"]),
    "photo": ("Lens & Light photography studio in Hyderabad - wedding photography, pre-wedding shoots, baby shoots, product photography. Prices from Rs 15000",
              "Lens & Light", "Hyderabad", ["wedding photography", "pre-wedding shoots", "baby shoots", "product photography"]),
    "hospital": ("City Care Hospital, Nagpur. 24x7 emergency, ICU, cardiology, orthopaedics, maternity, pathology lab, ambulance. Cashless insurance",
                 "City Care Hospital", "Nagpur", ["emergency", "ICU", "cardiology", "orthopaedics", "maternity", "pathology lab", "ambulance"]),
    "medical": ("Apna Medical Store, Lucknow: medicines, home delivery, baby care, surgical items, diabetic care. Open 8am-11pm",
                "Apna Medical Store", "Lucknow", ["medicines", "baby care", "surgical items", "diabetic care"]),
    "mobile": ("Mobile Mania, Surat - iPhone, Samsung, Vivo, accessories, repair, EMI available, 1 year warranty",
               "Mobile Mania", "Surat", ["iPhone", "Samsung", "Vivo", "accessories", "repair"]),
    "jeweller": ("Kapoor Jewellers, Chandni Chowk Delhi. Gold, diamond, silver jewellery, bridal sets, hallmark, old gold exchange",
                 "Kapoor Jewellers", "Delhi", ["gold", "diamond", "silver jewellery", "bridal sets", "hallmark", "old gold exchange"]),
    "preschool": ("Happy Feet Preschool, Pune: playgroup, nursery, kindergarten, daycare, activity classes. Admissions open",
                  "Happy Feet Preschool", "Pune", ["playgroup", "nursery", "kindergarten", "daycare", "activity classes"]),
    "software": ("TechNova, a software company in Bengaluru. Custom software, mobile apps, cloud, AI chatbots, free consultation. hello@technova.io",
                 "TechNova", "Bengaluru", ["custom software", "mobile apps", "cloud", "AI chatbots"]),
    "ngo": ("Harmony Care NGO, Jaipur - girl child education, food drive, health camps, donate online",
            "Harmony Care NGO", "Jaipur", ["girl child education", "food drive", "health camps"]),
    "cars": ("Speedy Motors, Gurgaon - used cars, car service, insurance, finance, exchange offers, free test drive",
             "Speedy Motors", "Gurgaon", ["used cars", "car service", "insurance", "finance", "exchange offers", "free test drive"]),
    "kirana": ("मेरी दुकान का नाम शर्मा किराना स्टोर है, जयपुर में, आटा, दाल, चावल, तेल, मसाले, होम डिलीवरी, सुबह 8 से रात 9 बजे तक",
               "शर्मा किराना स्टोर", "जयपुर", ["आटा", "दाल", "चावल", "तेल", "मसाले"]),
    "parlour": ("mujhe apne beauty parlour ki website chahiye, naam Priya Beauty Parlour, Kanpur, facial, threading, bridal makeup, hair spa, mehendi",
                "Priya Beauty Parlour", "Kanpur", ["facial", "threading", "bridal makeup", "hair spa", "mehendi"]),
    "ca": ("Rao & Associates, chartered accountants, Hyderabad. GST filing, income tax, audit, company registration, bookkeeping. First consultation free",
           "Rao & Associates", "Hyderabad", ["GST filing", "income tax", "audit", "company registration", "bookkeeping"]),
    "spa": ("Zen Spa & Wellness, Bangalore. Swedish massage, aromatherapy, body scrub, couples spa, steam. Open 10am to 10pm. Online booking",
            "Zen Spa & Wellness", "Bangalore", ["Swedish massage", "aromatherapy", "body scrub", "couples spa", "steam"]),
    "toys": ("Kids Zone toy shop, Ahmedabad. Educational toys, board games, soft toys, return gifts. COD, free shipping above Rs 999",
             "Kids Zone", "Ahmedabad", ["educational toys", "board games", "soft toys", "return gifts"]),
}


class RealPrompts2(unittest.TestCase):
    def test_facts(self):
        for key, (prompt, name, city, items) in REAL2.items():
            f = facts_for(prompt)
            self.assertEqual((f["name"], f["city"], f["items"]), (name, city, items), key)

    def test_pages_are_clean(self):
        for key, (prompt, name, city, items) in REAL2.items():
            c = generate_content(prompt)
            blob = " ".join(t for _, t, _ in leaves_of(c)).lower() + " " + " ".join(f["title"] for f in c["features"]).lower()
            for it in items:
                self.assertIn(it.lower(), blob, (key, it))
            for banned in BANNED:
                self.assertNotIn(banned, blob, key)
            self.assertFalse([n for n in c["needs_review"] if "quality check" in n or "placeholder" in n], (key, c["needs_review"]))
            self.assertEqual((c["brand"], c["location"]), (name, city), key)

    def test_offers_and_conditions(self):
        ids = lambda k: {o["id"] for o in facts_for(REAL2[k][0])["offers"]}   # noqa: E731
        self.assertIn("cashless", ids("hospital"))
        self.assertIn("donate", ids("ngo"))
        self.assertIn("pickup", ids("hotel"))
        toys = {o["text"] for o in facts_for(REAL2["toys"][0])["offers"]}
        self.assertIn("Free shipping above Rs 999", toys)
        self.assertEqual(facts_for(REAL2["toys"][0])["prices"], [])
        self.assertEqual(facts_for(REAL2["photo"][0])["prices"], [{"name": "Starting price", "price": "from Rs 15000"}])

    def test_localities(self):
        self.assertEqual(facts_for(REAL2["jeweller"][0])["address"], "Chandni Chowk")
        self.assertEqual(facts_for(REAL2["salon"][0])["address"], "Andheri")

    def test_hotel_pharmacy_and_preschool_speak_their_own_words(self):
        hotel = " ".join(t for _, t, _ in leaves_of(generate_content(REAL2["hotel"][0]))).lower()
        self.assertNotIn("trip", hotel)
        self.assertIn("room", hotel)
        pharm = generate_content(REAL2["medical"][0])
        self.assertNotIn("appointment", pharm["cta_primary"].lower())
        pre = generate_content(REAL2["preschool"][0])
        self.assertNotIn("demo", " ".join(t for _, t, _ in leaves_of(pre)).lower())
        self.assertNotIn("batch", " ".join(t for _, t, _ in leaves_of(pre)).lower())
        self.assertNotIn("automates", " ".join(t for _, t, _ in leaves_of(generate_content(REAL2["software"][0]))).lower())

    def test_request_words_do_not_eat_a_name(self):
        from corecraft.facts import strip_request
        self.assertTrue(strip_request("Apna Medical Store, Lucknow: medicines").startswith("Apna Medical Store"))
        self.assertEqual(strip_request("apna cafe chahiye Pune"), "cafe chahiye Pune")


SENTENCES = {   # people often write whole sentences instead of a list
    "bakery": ("We are a family-run bakery in Jaipur since 1998. We make fresh cakes, cookies, bread and pastries every morning, and we also take custom orders for birthdays and weddings. We are open from 8am to 9pm and you can order on WhatsApp.",
               "Jaipur", ["fresh cakes", "cookies", "bread", "pastries", "custom orders"], "8am to 9pm"),
    "dentist": ("I run a small dental clinic in Indore. I am a dentist with 12 years of experience and we do root canals, braces, teeth whitening and kids dentistry. Appointments are available online.",
                "Indore", ["root canals", "braces", "teeth whitening", "kids dentistry"], None),
    "gym": ("Hi, I need a website for my gym. It is called Iron Temple and it is in Chandigarh. We offer weight training, cardio, crossfit, personal training and diet plans. Timings are 5am to 10pm.",
            "Chandigarh", ["weight training", "cardio", "crossfit", "personal training", "diet plans"], "5am to 10pm"),
    "security": ("Our company provides CCTV installation, biometric attendance systems, networking and AMC services for offices in Pune. Free site survey available.",
                 "Pune", ["CCTV installation", "biometric attendance systems", "networking", "AMC services"], None),
    "tuition": ("Mera naam Rahul hai aur main Delhi mein ek tuition center chalata hoon. Maths, science aur English ki classes 6th se 12th tak. Demo class free hai.",
                "Delhi", ["maths", "science", "English classes"], None),
    "designer": ("I am a freelance graphic designer from Mumbai. I design logos, brochures, social media posts and packaging. Contact me at ankita@design.in",
                 "Mumbai", ["logos", "brochures", "social media posts", "packaging"], None),
    "restaurant": ("Looking for a website for our restaurant called Spice Garden, we serve Chinese and Thai food, momos, noodles, fried rice and manchurian. Located in Siliguri. Home delivery available.",
                   "Siliguri", ["momos", "noodles", "fried rice", "manchurian"], None),
    "garage": ("A car repair garage in Hyderabad offering engine repair, denting and painting, AC service, wheel alignment and car wash. Open all days.",
               "Hyderabad", ["engine repair", "denting", "painting", "AC service", "wheel alignment", "car wash"], "all days"),
    "yoga": ("Priya Sharma, yoga teacher in Rishikesh, offering 200 hour teacher training, morning classes, retreats and online sessions",
             "Rishikesh", ["200 hour teacher training", "morning classes", "retreats", "online sessions"], None),
    "candles": ("We sell handmade candles, soaps and gift hampers online. Based in Kochi. Free shipping over Rs 500 and cash on delivery available.",
                "Kochi", ["handmade candles", "soaps", "gift hampers"], None),
}


class SentencePrompts(unittest.TestCase):
    def test_facts_from_sentences(self):
        for key, (prompt, city, items, hours) in SENTENCES.items():
            f = facts_for(prompt)
            self.assertEqual((f["city"], f["items"]), (city, items), key)
            self.assertEqual(f["hours"], hours, key)

    def test_names_and_offers_from_sentences(self):
        self.assertEqual(facts_for(SENTENCES["gym"][0])["name"], "Iron Temple")
        self.assertEqual(facts_for(SENTENCES["restaurant"][0])["name"], "Spice Garden")
        self.assertEqual(facts_for(SENTENCES["yoga"][0])["name"], "Priya Sharma")
        self.assertEqual(facts_for(SENTENCES["designer"][0])["email"], "ankita@design.in")
        ids = lambda k: {o["id"] for o in facts_for(SENTENCES[k][0])["offers"]}   # noqa: E731
        self.assertIn("online_booking", ids("dentist"))
        self.assertIn("free_consult", ids("security"))
        self.assertIn("free_trial", ids("tuition"))
        self.assertIn("home_delivery", ids("restaurant"))
        self.assertEqual(ids("candles"), {"cod", "free_shipping"})   # "cash on delivery" is not home delivery
        self.assertEqual(facts_for(SENTENCES["dentist"][0])["years"], "12 years of experience")

    def test_no_sentence_fragments_become_services(self):
        bad = {"we are", "it is", "hi", "my gym", "you can order on", "located in siliguri", "based in kochi", "website for our restaurant", "we do root canals", "dentist"}
        for key, (prompt, *_rest) in SENTENCES.items():
            self.assertFalse(bad & {i.lower() for i in facts_for(prompt)["items"]}, key)

    def test_pages_keep_every_service_and_the_name(self):
        for key, (prompt, city, items, hours) in SENTENCES.items():
            c = generate_content(prompt)
            blob = " ".join(t for _, t, _ in leaves_of(c)).lower() + " " + " ".join(f["title"] for f in c["features"]).lower()
            for it in items:
                self.assertIn(it.lower(), blob, (key, it))
            self.assertEqual(c["location"], city, key)
            self.assertFalse([n for n in c["needs_review"] if "quality check" in n], (key, c["needs_review"]))
            self.assertNotRegex(blob, r"\b(?:we are|it is)\b\s+and\b|in chandigarh in chandigarh|siliguri home", key)


class Typos(unittest.TestCase):
    def test_business_words_are_corrected(self):
        from corecraft import typos
        for wrong, right in (("resturant in pune, pizza", "restaurant"), ("denatl clinic in nagpur", "dental"), ("beauty salun in jaipur", "salon"), ("gim in delhi, cardio", "gym")):
            text, changes, _ = typos.fix(wrong)
            self.assertIn(right, text)
            self.assertTrue(changes, wrong)

    def test_real_words_and_names_are_never_rewritten(self):
        from corecraft import typos
        for text in ("Kaju katli, himachal trekking, water tanker supply", "mujhe ek dental clinic chahiye Pune mein, braces, implants", "Forno Rosso, tiramisu, risotto, aligners, invoicing",
                     "dukaan mein kapde saree kurti lehenga wala", "hello@pixelforge.in www.pixelforge.in", "मुझे एक रेस्टोरेंट चाहिए"):
            self.assertEqual(typos.fix(text)[0], text)

    def test_typo_prompts_make_the_right_page(self):
        c = generate_content("resturant in pune, pizza, burger, pasta, cold coffee")
        self.assertEqual((c["business_type"], c["location"]), ("restaurant", "Pune"))
        self.assertEqual(c["generated_by"]["items_from_prompt"], ["pizza", "burger", "pasta", "cold coffee"])
        self.assertTrue([n for n in c["needs_review"] if "resturant" in n and "typing" in n])
        c = generate_content("gim in delhi, weight traning, cardeo, zumba")
        self.assertEqual((c["business_type"], c["location"]), ("gym", "Delhi"))
        self.assertEqual(c["generated_by"]["items_from_prompt"][0], "weight training")

    def test_a_clean_prompt_gets_no_typo_note(self):
        c = generate_content(ITALIAN)
        self.assertFalse([n for n in c["needs_review"] if "typing" in n or "as typed" in n])


class ScatteredServices(unittest.TestCase):
    def test_services_spread_over_sentences(self):
        f = facts_for("we have a bakery in Mumbai. We make cakes and cookies. We also do bread and brownies. We also have custom cakes for weddings. Along with that we sell gift boxes.")
        self.assertEqual(f["items"], ["cakes", "cookies", "bread", "brownies", "custom cakes", "gift boxes"])
        f = facts_for("Our clinic is in Pune. Services include root canal. Services include braces. We also provide teeth whitening and implants.")
        self.assertEqual(f["items"], ["root canal", "braces", "teeth whitening", "implants"])

    def test_a_run_of_words_without_commas(self):
        f = facts_for("pet shop in bangalore dog food cat food aquarium fish toys")
        self.assertEqual((f["city"], f["items"]), ("Bangalore", ["dog food", "cat food", "aquarium fish", "toys"]))

    def test_selling_and_area_names(self):
        self.assertEqual(facts_for("shoe shop in kolkata selling sports shoes, formal shoes, sandals")["items"], ["sports shoes", "formal shoes", "sandals"])
        f = facts_for("laptop repair shop in Delhi Nehru Place. screen replacement, battery, data recovery, windows install. Call 9999999999")
        self.assertEqual((f["city"], f["address"], f["name"]), ("Delhi", "Nehru Place", None))
        self.assertEqual(generate_content("laptop repair shop in Delhi Nehru Place. screen replacement, battery, data recovery, windows install")["generated_by"]["items_from_prompt"],
                         ["screen replacement", "battery", "data recovery", "windows install"])


class NoMadeUpName(unittest.TestCase):
    def test_heading_says_what_the_business_is_not_a_fake_name(self):
        c = generate_content("dental clinic in Pune, braces, implants, crowns")
        self.assertEqual(c["brand"], "Dental Clinic, Pune")
        self.assertEqual(c["about_title"], "About us")
        self.assertTrue([n for n in c["needs_review"] if "not a name" in n])
        self.assertEqual(generate_content("bakery, cakes, cookies, bread")["brand"], "Bakery")

    def test_a_given_name_is_used_and_not_flagged(self):
        c = generate_content("Smile Hub dental clinic in Pune, braces, implants, crowns")
        self.assertEqual(c["brand"], "Smile Hub")
        self.assertFalse([n for n in c["needs_review"] if "No business name" in n])

    def test_email_domain_is_only_a_suggestion(self):
        c = generate_content("software company in Pune, apps, cloud, chatbots. hello@technova.io")
        self.assertNotEqual(c["brand"], "Technova")
        self.assertTrue([n for n in c["needs_review"] if "suggests 'Technova'" in n])
        c = generate_content("software company in Pune, apps, cloud, chatbots. someone@gmail.com")
        self.assertFalse([n for n in c["needs_review"] if "suggests" in n])


NO_COMMAS = [   # lists typed with no separators; these were used to tune the cutter, so they guard against regressions (the fresh-set score is in the README)
    ("pet shop in bangalore dog food cat food aquarium fish toys", ["dog food", "cat food", "aquarium fish", "toys"]),
    ("beauty salon in Jaipur haircut facial bridal makeup waxing threading", ["haircut", "facial", "bridal makeup", "waxing", "threading"]),
    ("gym in Delhi weight training cardio zumba personal training", ["weight training", "cardio", "zumba", "personal training"]),
    ("bakery in Mumbai chocolate cake cupcakes brownies fresh bread", ["chocolate cake", "cupcakes", "brownies", "fresh bread"]),
    ("dental clinic in Pune root canal braces teeth whitening implants", ["root canal", "braces", "teeth whitening", "implants"]),
    ("mobile shop in Surat iPhone Samsung accessories screen guard repair", ["iPhone", "Samsung", "accessories", "screen guard", "repair"]),
    ("restaurant in Goa fish curry prawn fry crab masala sol kadi", ["fish curry", "prawn fry", "crab masala", "sol kadi"]),
    ("electrician in Pune house wiring fan repair inverter installation switch board", ["house wiring", "fan repair", "inverter installation", "switch board"]),
    ("clothing store in Jaipur kurtis sarees lehengas dupattas", ["kurtis", "sarees", "lehengas", "dupattas"]),
    ("car wash in Hyderabad interior cleaning exterior polish engine wash ceramic coating", ["interior cleaning", "exterior polish", "engine wash", "ceramic coating"]),
    ("optical shop in Surat eye test spectacles contact lenses sunglasses", ["eye test", "spectacles", "contact lenses", "sunglasses"]),
    ("computer institute in Lucknow tally course python course web design course", ["tally course", "python course", "web design course"]),
]


class NoCommaLists(unittest.TestCase):
    def test_lists_without_separators(self):
        for prompt, items in NO_COMMAS:
            self.assertEqual(facts_for(prompt)["items"], items, prompt)

    def test_a_cut_list_is_reported(self):
        c = generate_content("pet shop in bangalore dog food cat food aquarium fish toys")
        self.assertTrue([n for n in c["needs_review"] if "without commas" in n and "dog food | cat food" in n], c["needs_review"])

    def test_a_normal_list_is_never_cut_or_reported(self):
        for p in ("dental clinic in Pune, teeth whitening, root canal, hair spa", "Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu"):
            self.assertFalse([n for n in generate_content(p)["needs_review"] if "without commas" in n], p)

    def test_known_phrases_and_names_stay_whole(self):
        self.assertEqual(facts_for("salon in Pune, hair spa, bridal makeup, Swedish massage")["items"], ["hair spa", "bridal makeup", "Swedish massage"])
        self.assertEqual(facts_for("dental clinic in Pune, General dental care, teeth whitening")["items"], ["general dental care", "teeth whitening"])

    def test_an_unlisted_town_before_the_services(self):
        f = facts_for("dairy in Anand fresh milk paneer butter ghee curd")
        self.assertEqual(f["city"], "Anand")
        self.assertTrue(f["items"])


FINAL = {   # the last mixed batch: clean list, typos, sentences, no name, Hinglish, Hindi, unlisted town, "a gym with ..."
    "dosa": ("Spice Route Kitchen, South Indian restaurant in Chennai: masala dosa, idli sambar, filter coffee, pongal, meals. Open 7am to 10pm. Table booking, home delivery. 044 2345 6789",
             "Spice Route Kitchen", "Chennai", ["masala dosa", "idli sambar", "filter coffee", "pongal", "meals"]),
    "typo": ("denatl clinic in Nagpur root canal braces teeth whitening implants kids dentistry. Open Mon-Sat 10am-7pm",
             None, "Nagpur", ["root canal", "braces", "teeth whitening", "implants", "kids dentistry"]),
    "sweets": ("We are a family-run sweet shop in Udaipur since 1985. We make kaju katli, motichoor ladoo, jalebi and namkeen. We also take orders for weddings and festivals. Open 8am to 10pm, home delivery available. Call 9414012345",
               None, "Udaipur", ["kaju katli", "motichoor ladoo", "jalebi", "namkeen"]),
    "hinglish": ("mujhe apne tuition center ki website chahiye, naam Gyan Deep Classes, Patna, maths, science, english, 9th se 12th, demo class free, shaam 4 se raat 8 tak",
                 "Gyan Deep Classes", "Patna", ["maths", "science", "english"]),
    "hindi": ("मेरी दुकान का नाम गुप्ता मेडिकल स्टोर है, कानपुर में, दवाइयाँ, बेबी केयर, सर्जिकल सामान, होम डिलीवरी, सुबह 8 से रात 10 बजे तक",
              "गुप्ता मेडिकल स्टोर", "कानपुर", ["दवाइयाँ", "बेबी केयर", "सर्जिकल सामान"]),
    "hardware": ("hardware store in Anand cement paint pipes tools bulbs locks", None, "Anand", ["cement", "paint", "pipes", "tools", "bulbs", "locks"]),
    "gym": ("Nova Fitness Club in Gurgaon, a gym with weight training, cardio, crossfit, zumba and personal training. Free trial class. Open 5am to 11pm. nova@novafit.in",
            "Nova Fitness Club", "Gurgaon", ["weight training", "cardio", "crossfit", "zumba", "personal training"]),
}


class FinalBatch(unittest.TestCase):
    def test_facts(self):
        for key, (prompt, name, city, items) in FINAL.items():
            f = facts_for(prompt)
            self.assertEqual((f["city"], f["items"]), (city, items), key)
            self.assertEqual(f["name"], name, key)

    def test_comma_separated_names_are_not_cut(self):
        self.assertFalse([n for n in generate_content(FINAL["dosa"][0])["needs_review"] if "without commas" in n])
        self.assertEqual(generate_content(FINAL["hinglish"][0])["generated_by"]["items_from_prompt"], ["maths", "science", "english"])

    def test_headings_when_there_is_no_name(self):
        self.assertEqual(generate_content(FINAL["hardware"][0])["brand"], "Store, Anand")
        self.assertEqual(generate_content("We sell handmade candles, soaps and gift hampers online. Based in Kochi.")["brand"], "Online Store, Kochi")
        self.assertEqual(generate_content(FINAL["typo"][0])["brand"], "Dental Clinic, Nagpur")

    def test_hindi_medical_store(self):
        c = generate_content(FINAL["hindi"][0])
        self.assertEqual(c["type_label"], "मेडिकल स्टोर")
        self.assertNotIn("अपॉइंटमेंट", c["cta_primary"])
        self.assertEqual(c["cta_primary"], "दवाई ऑर्डर करें")

    def test_every_type_has_a_hindi_label(self):
        from corecraft import lang_hi
        self.assertEqual([k for k in T if k not in lang_hi.LABELS], [])

    def test_pages_keep_every_service(self):
        for key, (prompt, name, city, items) in FINAL.items():
            c = generate_content(prompt)
            blob = " ".join(t for _, t, _ in leaves_of(c)).lower() + " " + " ".join(f["title"] for f in c["features"]).lower()
            for it in items:
                self.assertIn(it.lower(), blob, (key, it))
            self.assertFalse([n for n in c["needs_review"] if "quality check" in n], (key, c["needs_review"]))


if __name__ == "__main__":
    unittest.main()
