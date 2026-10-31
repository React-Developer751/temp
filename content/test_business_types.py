import os
import re
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("CORECRAFT_NO_PHOTOS", "1")        # content tests do not need pictures (test_photos.py does)
from corecraft import design_engine, pipeline
from corecraft.business_types import T, detect_type, parse_prompt
from corecraft.content_engine import generate_content

CASES = {
    "dental clinic in Pune offering teeth whitening, braces and root canal": "dental",
    "law firm for property and family disputes in Delhi": "law",
    "real estate agency selling flats and villas in Gurgaon": "realestate",
    "hair salon and beauty parlour for women": "salon",
    "travel agency for Kerala and Goa tour packages": "travel",
    "wedding planner and decorator in Jaipur": "events",
    "car repair garage and car wash": "garage",
    "yoga and meditation retreat in Rishikesh": "yoga",
    "NGO working for child education and food donation": "ngo",
    "interior designer for homes and offices": "interior",
    "digital marketing agency for small businesses, SEO and social media": "marketing",
    "CA firm for GST filing, income tax and company registration": "accounting",
    "pet shop and dog grooming": "petshop",
    "mobile phone repair and accessories shop": "mobile",
    "boutique hotel with rooms, spa and restaurant in Udaipur": "hotel",
    "mithai dukaan aur catering service": "catering",
    "courier and logistics company for e-commerce sellers": "courier",
    "construction company for residential buildings": "construction",
    "photography studio for weddings and pre-wedding shoots": "photography",
    "kids play school and daycare": "playschool",
    "organic farm selling vegetables and milk": "grocery",
    "cleaning and pest control services for homes": "cleaning",
    "architect firm": "architect",
    "event management and DJ service": "events",
    "taxi and cab booking service": "taxi",
    "ayurvedic clinic and panchakarma": "ayurveda",
    "physiotherapy centre": "physio",
    "electrician and home wiring services": "electrician",
    "furniture showroom with sofas and beds": "furniture",
    "सैलून और ब्यूटी पार्लर": "salon",
    "mera kapde ka showroom hai men and women wear": "clothing",
    "IT consulting and custom software development company": "software",
    "tuition classes for class 10 and 12 maths science": "school",
    "spa and massage center": "spa",
    "bakery for custom cakes and birthday parties": "bakery",
    "driving school": "driving",
    "solar panel installation company": "solar",
    "coworking space for startups": "coworking",
    "optician shop with eyeglasses and contact lenses": "optical",
    "plumbing repairs": "plumbing",
    "bike repair shop": "garage",
    "hr consultancy for hiring": "recruitment",
    "logo and branding studio": "design",
    "tattoo studio": "tattoo",
    "tailor shop": "tailor",
    "visa consultant": "visa",
    "CCTV camera installation": "security",
    "welding and fabrication workshop": "welding",
    "astrologer in Delhi": "astrology",
    "mobile app development studio": "software",
    "school uniform supplier": "clothing",
    "cricket coaching academy": "sports",
    "auto rickshaw rental": "taxi",
    "yoga teacher training institute": "yoga",
    "mobile phone shop": "mobile",
    "ice cream parlour with shakes and sundaes": "icecream",
    "gaming cafe with PS5": "gaming",
    "hostel and PG accommodation in Kota": "hotel",
    "Ayurvedic skin care products online store": "shop",
    "website for my kirana store": "grocery",
    "cozy cafe called 'Chai Point' serving coffee": "cafe",
}


class Detection(unittest.TestCase):
    def test_business_types_are_recognised(self):
        wrong = {p: detect_type(p)[0] for p, t in CASES.items() if detect_type(p)[0] != t}
        self.assertEqual(wrong, {})

    def test_unknown_type_is_reported_not_guessed(self):
        c = generate_content("event tickets", 1)
        self.assertEqual(c["business_type"], "general")
        self.assertTrue(any("not recognised" in n or "not in the list" in n for n in c["needs_review"]))

    def test_hindi_and_hinglish_keywords(self):
        self.assertEqual(generate_content("सैलून और ब्यूटी पार्लर", 1)["business_type"], "salon")
        self.assertEqual(generate_content("mithai dukaan", 1)["business_type"], "sweets")

    def test_many_types_defined(self):
        self.assertGreaterEqual(len(T), 55)


class HeldOut(unittest.TestCase):
    def test_unlisted_business_falls_back_safely(self):
        c = generate_content("water tanker supply", 1)
        self.assertEqual(c["business_type"], "general")
        self.assertEqual(c["features"][0]["title"], "Water Tanker Supply")   # the user's own words lead
        self.assertTrue(any("not recognised" in n for n in c["needs_review"]))

    def test_listed_services_stop_at_contact_words(self):
        c = generate_content("tattoo studio in Mumbai offering custom tattoos, piercing and aftercare", 1)
        self.assertEqual([f["title"] for f in c["features"][:3]], ["Custom Tattoos", "Piercing", "Aftercare"])


class ParsingFacts(unittest.TestCase):
    def test_services_place_audience(self):
        f = parse_prompt("dental clinic in Pune offering teeth whitening, braces and root canal")
        self.assertEqual(f["items"], ["teeth whitening", "braces", "root canal"])
        self.assertEqual(f["place"], "Pune")
        self.assertEqual(parse_prompt("hair salon for women")["audience"], "women")
        self.assertEqual(parse_prompt("interior designer for homes and offices")["items"], [])

    def test_items_stop_at_the_sentence_and_contact_words(self):
        f = parse_prompt("dental clinic in Pune offering teeth whitening, braces and root canal. call 9876543210")
        self.assertEqual(f["items"], ["teeth whitening", "braces", "root canal"])
        self.assertEqual(parse_prompt("law firm for property cases, family law and wills, email a@b.com")["items"], ["property cases", "family law", "wills"])

    def test_contact_and_years(self):
        f = parse_prompt("architect firm call 9876543210 mail info@studio.in since 2012")
        self.assertEqual((f["phone"], f["email"], f["years"]), ("9876543210", "info@studio.in", "since 2012"))


class Content(unittest.TestCase):
    def test_no_invented_numbers(self):
        for p in list(CASES)[:20]:
            c = generate_content(p, 2)
            for s in c["stats"]:   # stats exist only for facts the user gave: a place or years
                self.assertTrue(s["label"] in ("Where we work", "Years of experience", "Serving since"), s)
            blob = " ".join([c["hero_heading"], c["tagline"], c["cta_text"]] + c["about"] + [f["text"] for f in c["features"]])
            self.assertNotRegex(blob, r"\d")
        c = generate_content("plumber with 12 years experience in Pune", 1)
        self.assertEqual(c["stats"][0], {"value": "12+", "label": "Years of experience"})

    def test_user_services_come_first_and_reach_faq(self):
        c = generate_content("dental clinic in Pune offering teeth whitening, braces and root canal", 4)
        self.assertEqual([f["title"] for f in c["features"][:3]], ["Teeth Whitening", "Braces", "Root Canal"])
        self.assertTrue(any("teeth whitening" in x["q"].lower() for x in c["faq"]))
        self.assertIn("Pune", c["eyebrow"])
        self.assertIn("Pune", " ".join(c["about"]))

    def test_user_phrases_do_not_repeat_in_headlines(self):
        for seed in range(30):
            c = generate_content("dental clinic offering teeth whitening, braces and root canal", seed)
            heads = [c["hero_heading"].lower(), c["tagline"].lower()]
            for item in ("teeth whitening", "braces", "root canal"):
                self.assertLessEqual(sum(item in h for h in heads), 1, (seed, heads))

    def test_review_notes_are_honest(self):
        c = generate_content("dental clinic", 1)
        notes = " ".join(c["needs_review"])
        self.assertIn("No business name was given", notes)
        self.assertIn("Typical dental clinic offerings", notes)
        named = generate_content("dental clinic called 'Smile Hub' in Pune offering braces", 1)
        self.assertEqual(named["brand"], "Smile Hub")
        self.assertNotIn("No business name", " ".join(named["needs_review"]))

    def test_every_type_gives_valid_complete_content(self):
        for tid, t in T.items():
            c = generate_content(t["keys"][0] + " " + t["label"], 5)
            self.assertEqual(c["business_type"], tid, (tid, c["business_type"]))
            self.assertGreaterEqual(len(c["features"]), 3, tid)
            self.assertEqual(len(c["steps"]), 3)
            self.assertGreaterEqual(len(c["faq"]), 4)
            self.assertEqual(len(c["highlights"]), 3)
            self.assertTrue(c["cta_primary"] and c["cta_secondary"])
            self.assertEqual(c, generate_content(t["keys"][0] + " " + t["label"], 5))


class SiteOutput(unittest.TestCase):
    def test_sites_build_for_every_type_with_new_sections(self):
        with tempfile.TemporaryDirectory() as d:
            for i, (tid, t) in enumerate(T.items()):
                r = pipeline.run(t["keys"][0] + " " + t["label"] + " in Pune call 9876543210", d, i)
                out = Path(r["dir"])
                self.assertTrue(design_engine.validate_jsx((out / "App.jsx").read_text()))
                pre = (out / "preview.html").read_text()
                for needle in ('id="faq"', 'class="section steps"', 'class="section highlights"', "tel:9876543210", "Pune"):
                    self.assertIn(needle, pre, (tid, needle))
                self.assertNotRegex(pre, r"\{\{|\$\{")

    def test_no_numeric_stats_block_without_facts(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run("dental clinic", d, 1)
            pre = (Path(r["dir"]) / "preview.html").read_text()
            self.assertNotIn('class="stats"', pre)


if __name__ == "__main__":
    unittest.main()


class RealFacts(unittest.TestCase):
    FACTS = {"name": "Smile Hub", "city": "Pune", "services": ["braces", "implants", "teeth whitening"], "phone": "9876543210", "email": "hi@smile.in",
             "address": "12 MG Road", "hours": ["Mon-Sat 10am-7pm"], "whatsapp": "9876543210", "years": "12 years",
             "prices": [{"name": "Check-up", "price": "Rs 500"}], "testimonials": [{"name": "A. Shah", "text": "Great care."}],
             "team": [{"name": "Dr. Rao", "role": "Orthodontist"}]}

    def test_services_of_three_or_more_replace_typical_offerings(self):
        c = generate_content("dental clinic", 3, facts=self.FACTS)
        self.assertEqual([f["title"] for f in c["features"]], ["Braces", "Implants", "Teeth Whitening"])
        self.assertEqual(c["brand"], "Smile Hub")
        self.assertFalse(any("Typical" in n or "No business name" in n for n in c["needs_review"]))
        self.assertEqual(c["generated_by"]["mode"], "strict (your phrases only)")

    def test_user_sections_are_verbatim_and_rendered(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run("dental clinic", d, 3, self.FACTS)
            out = Path(r["dir"])
            pre = (out / "preview.html").read_text()
            for needle in ("Rs 500", "Great care.", "Dr. Rao", "Orthodontist", "12 MG Road", "Mon-Sat 10am-7pm", "WhatsApp: 9876543210", "hi@smile.in", "12+"):
                self.assertIn(needle, pre, needle)
            self.assertTrue(design_engine.validate_jsx((out / "App.jsx").read_text()))

    def test_nothing_is_invented_when_no_facts_given(self):
        c = generate_content("dental clinic", 3)
        for k in ("pricing", "testimonials", "team"):
            self.assertNotIn(k, c)

    def test_incomplete_entries_are_reported(self):
        c = generate_content("dental clinic", 1, facts={"prices": [{"name": "Check-up"}], "testimonials": [{"text": "Nice"}]})
        self.assertNotIn("pricing", c)
        self.assertEqual(sum("skipped" in n for n in c["needs_review"]), 2)


class Unlisted(unittest.TestCase):
    def test_family_is_inferred_from_the_head_noun(self):
        for p, fam in [("bike accessories dealer in Pune", "shop"), ("juice bar in Surat", "restaurant"), ("scrap collection service", "business"),
                       ("quilling art classes", "education"), ("astro vastu advisor", "pro"), ("soil testing laboratory", None)]:
            c = generate_content(p, 1)
            if fam:
                self.assertEqual(c["niche"], fam, p)
            self.assertGreaterEqual(len(c["features"]), 3)
            self.assertTrue(c["needs_review"])

    def test_no_typical_offerings_for_unlisted_types(self):
        c = generate_content("water tanker supply in Jaipur", 2)
        self.assertEqual([f["title"] for f in c["features"]], ["Water Tanker Supply", "Expert Advice", "Reliable Service"])
        self.assertEqual(generate_content("bike accessories dealer in Pune", 2)["features"][0]["title"], "Bike Accessories")
        self.assertTrue(any("neutral" in n for n in c["needs_review"]))

    def test_new_types_exist(self):
        for tid in ("security", "mehendi", "tailor", "astrology", "visa", "tenthouse", "welding", "tyres", "tattoo", "gaming", "icecream"):
            self.assertIn(tid, T)


class Hindi(unittest.TestCase):
    P = "दिल्ली में दांतों का क्लिनिक, डेंटल इम्प्लांट, ब्रेसेज़ और रूट कैनाल"

    def test_hindi_page_uses_only_hindi_and_user_phrases(self):
        c = generate_content(self.P, 2)
        self.assertEqual((c["lang"], c["business_type"], c["location"]), ("hi", "dental", "दिल्ली"))
        self.assertEqual([f["title"] for f in c["features"][:3]], ["डेंटल इम्प्लांट", "ब्रेसेज़", "रूट कैनाल"])
        blob = " ".join([c["hero_heading"], c["tagline"], c["cta_primary"], c["steps_title"]] + c["about"] + [f["text"] for f in c["features"]])
        self.assertFalse(re.search(r"[A-Za-z]", blob), blob)
        self.assertEqual(c["cta_primary"], "अपॉइंटमेंट बुक करें")

    def test_hindi_site_builds_with_lang_and_labels(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run(self.P, d, 2)
            out = Path(r["dir"])
            pre = (out / "preview.html").read_text()
            self.assertIn('lang="hi"', pre)
            for needle in ("हमारे बारे में", "अक्सर पूछे जाने वाले सवाल", "कैसे काम करता है"):
                self.assertIn(needle, pre)
            self.assertTrue(design_engine.validate_jsx((out / "App.jsx").read_text()))

    def test_lang_flag_forces_hindi_for_roman_prompt(self):
        c = generate_content("dental clinic in Pune offering braces, implants and whitening", 1, lang="hi")
        self.assertEqual(c["lang"], "hi")
        self.assertEqual(c["steps_title"], "कैसे काम करता है")

    def test_all_kinds_have_hindi_blocks(self):
        from corecraft import lang_hi
        from corecraft.template_data import NICHE
        for k in NICHE:
            for table in (lang_hi.STEPS, lang_hi.HIGHLIGHTS, lang_hi.FAQ_THIRD, lang_hi.CTAS):
                self.assertIn(k, table, k)


class HindiDetails(unittest.TestCase):
    def test_items_stop_at_the_danda_and_phone_is_kept_apart(self):
        c = generate_content("जयपुर में रेस्टोरेंट: बिरयानी, कबाब, मिठाई और चाय। फोन 9811122233", 2)
        self.assertEqual([f["title"] for f in c["features"]], ["बिरयानी", "कबाब", "मिठाई", "चाय"])
        self.assertEqual(c["contact"]["phone"], "9811122233")
        self.assertEqual(c["business_type"], "restaurant")
        self.assertTrue(any("मिलता है" in x["q"] for x in c["faq"]))
        self.assertFalse(any("9811122233" in f["text"] for f in c["features"]))
