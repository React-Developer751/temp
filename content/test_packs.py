"""Niche packs: the 99 niches + 20 business types of the Content AI training spec (the default list, corecraft/data/niches.json), the request understanding,
the checker and the pack-to-site path; the author's 77 business types (corecraft/data/author_niches.json) as a whole list and as the fallback for trades the spec does not have."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from corecraft import pack_check, pack_request, pack_spec, pack_writer as W
from corecraft.business_types import T
from corecraft.pack_api import generate_pack

ROOT = Path(__file__).parent
W.use_niche_file(None)   # these tests are about the default list, whatever $CORECRAFT_NICHE_FILE says
NICHES = W.niches()
PACKS = {n: W.build_pack(v) for n, v in NICHES.items()}
TYPE_PACKS = W.build_type_packs()
MENUS = {n for n, v in NICHES.items() if v["menu"]}
FOODS = MENUS | {"type_food_dining"}
ENV = dict(os.environ, CORECRAFT_NICHE_FILE="")


def build_script():
    sys.path.insert(0, str(ROOT / "training"))
    try:
        import build_niches
    finally:
        sys.path.pop(0)
    return build_niches


class Spec(unittest.TestCase):
    def test_the_spec_was_read_completely(self):
        self.assertEqual(W.niche_file(), W.NICHE_FILE)
        self.assertEqual((len(W.spec()["niches"]), len(W.spec()["types"])), (99, 20))
        self.assertTrue(all(len(n["services"]) == 6 and len(n["requests"]) == 6 for n in W.spec()["niches"]))
        self.assertEqual(len({n["id"] for n in W.spec()["niches"]}), 99)

    def test_every_niche_has_its_hand_written_layer(self):
        for nid in NICHES:
            self.assertIn(nid, pack_spec.FAMILY_OF, nid)
            self.assertIn(nid, pack_spec.PRICES, nid)
            self.assertEqual(len(pack_spec.HI_KEYS[nid]), 2, nid)
            self.assertEqual(len(pack_spec.PRICES[nid]), 3, nid)
        self.assertEqual(set(pack_spec.SPEC_TYPES), {t["theme"] for t in W.spec()["types"]})

    def test_food_niches_have_a_menu(self):
        for nid in ("cafe_coffee_tea", "restaurant_dining", "bakery_cakes", "german_cafe", "chai_tea_stall"):   # the five the spec names
            self.assertIn(nid, MENUS)
            self.assertIn("menu", PACKS[nid])

    def test_the_files_are_what_the_build_script_writes(self):
        b = build_script()
        self.assertEqual(json.loads(W.NICHE_FILE.read_text(encoding="utf-8")), json.loads(json.dumps(b.spec_list(), ensure_ascii=False)))
        self.assertEqual(json.loads(W.AUTHOR_FILE.read_text(encoding="utf-8")), json.loads(json.dumps(b.author(), ensure_ascii=False)))


class Packs(unittest.TestCase):
    def test_every_niche_pack_passes_the_spec_rules(self):
        for nid, p in PACKS.items():
            self.assertEqual(pack_check.check_pack(p, food=nid in MENUS), [], nid)

    def test_every_type_pack_passes_the_spec_rules(self):
        for p in TYPE_PACKS:
            self.assertEqual(pack_check.check_pack(p, food=p["id"] in FOODS), [], p["id"])

    def test_no_text_repeats_across_the_whole_batch(self):
        self.assertEqual(pack_check.check_batch(list(PACKS.values()) + TYPE_PACKS, foods=FOODS), [])

    def test_counts_and_shape(self):
        p = PACKS["pest_control"]
        self.assertEqual([len(p[k]) for k in ("heroTitles", "heroSubtitles", "features", "stats", "faq", "testimonials", "marquee")], [3, 3, 6, 3, 5, 3, 8])
        self.assertEqual((len(p["steps"]["items"]), len(p["about"]["paragraphs"]), len(p["about"]["points"]), len(p["pricing"]["plans"]), len(p["gallery"]["captions"]),
                          len(p["team"]["roles"]), len(p["blog"]["posts"])), (4, 2, 3, 3, 6, 3, 3))
        self.assertTrue(6 <= len(p["keywords"]) <= 14)
        self.assertEqual(p["cta"]["button"], p["button"])
        self.assertTrue(p["cta"]["title"].endswith("?"))

    def test_the_services_of_the_spec_are_the_features(self):
        for nid, n in NICHES.items():
            self.assertEqual([f["title"] for f in PACKS[nid]["features"]], [s if len(s) <= 30 else s[:30].rsplit(" ", 1)[0] for s in n["services"]], nid)

    def test_a_pest_control_page_never_talks_about_leaks_or_wiring(self):
        blob = json.dumps(PACKS["pest_control"]).lower()
        for w in ("leak", "wiring", "pipe", "bake", "menu"):
            self.assertNotIn(w, blob)

    def test_no_invented_claims(self):
        for nid, p in PACKS.items():
            blob = json.dumps(p).lower()
            for rx in (r"award", r"guarantee", r"100%", r"#1", r"best in", r"years of", r"customers served", r"\bcure[sd]?\b"):
                self.assertIsNone(re.search(rx, blob), (nid, rx))

    def test_prices_are_plain_usd_strings_that_do_not_fall(self):
        for nid, p in list(PACKS.items()) + [(p["id"], p) for p in TYPE_PACKS]:
            prices = [float(x["price"][1:]) for x in p["pricing"]["plans"]]
            self.assertEqual(prices, sorted(prices), nid)
            self.assertTrue(all(x["price"].startswith("$") for x in p["pricing"]["plans"]), nid)

    def test_a_menu_has_no_prices(self):
        for nid in MENUS:
            for cat in PACKS[nid]["menu"]["categories"]:
                self.assertTrue(5 <= len(cat["items"]) <= 6, (nid, cat["name"]))
                self.assertFalse([i for i in cat["items"] if "$" in i or "rs " in i.lower()], nid)

    def test_the_city_goes_into_the_hero_subtitle_once(self):
        p = W.build_pack(NICHES["dental_clinic"], city="Jaipur")
        self.assertEqual(sum("Jaipur" in s for s in p["heroSubtitles"]), 3)
        self.assertNotIn("Jaipur", p["contactText"])
        self.assertEqual(pack_check.check_pack(p), [])

    def test_the_checker_catches_what_the_spec_forbids(self):
        bad = json.loads(json.dumps(PACKS["pest_control"]))
        bad["features"][0]["text"] = "Over 500+ customers trust our award-winning team and we guarantee results every time you call us!"
        bad["heroTitles"][0] = "lower case title"
        bad["pricing"]["plans"][0]["price"] = "free"
        bad["theme"] = "not_a_theme"
        problems = " ".join(pack_check.check_pack(bad))
        for needle in ("forbid", "exclamation", "Title Case", "plain USD", "unknown theme"):
            self.assertIn(needle, problems)


class Requests(unittest.TestCase):
    def test_the_six_ways_of_asking_in_the_spec(self):
        for nid, n in list(NICHES.items())[:25]:
            x, x2, y, z, x5, x6 = n["requests"]
            for r in ("%s website" % x, "Create a website for a %s in Jaipur" % x2, "mujhe %s ki website banakar do" % y,
                      "meri %s ki dukaan ke liye website banao, with online contact and WhatsApp" % z, "modern %s website with animation, premium colours and a gallery" % x5,
                      "%s landing page, short, with pricing and FAQ" % x6):
                self.assertEqual(pack_request.understand(r)["niche"], nid, r)

    def test_all_requests_of_the_spec_are_understood(self):
        wrong = []
        for nid, n in NICHES.items():
            x, x2, y, z, x5, x6 = n["requests"]
            for r in ("%s website" % x, "Create a website for a %s in Jaipur" % x2, "mujhe %s ki website banakar do" % y, "meri %s ki dukaan ke liye website banao, with online contact and WhatsApp" % z):
                if pack_request.understand(r)["niche"] != nid:
                    wrong.append(r)
        self.assertEqual(wrong, [])

    def test_hold_out_keeps_most_of_the_accuracy(self):
        drop, reqs = {}, []
        for nid, n in NICHES.items():
            x, x2, y, z, x5, x6 = n["requests"]
            d = drop.setdefault(nid, set())
            d.update(pack_request._norm(w) for w in n["requests"])
            reqs += [("mujhe %s ki website banakar do" % y, nid), ("meri %s ki dukaan ke liye website banao, with online contact and WhatsApp" % z, nid)]
        pack_request.rebuild(drop)
        try:
            ok = sum(pack_request.understand(r, drop=drop)["niche"] == nid for r, nid in reqs)
        finally:
            pack_request.rebuild()
        self.assertGreaterEqual(ok / len(reqs), 0.9)

    def test_a_business_type_request_gets_the_type_pack(self):
        for t in W.spec()["types"]:
            out = generate_pack("Create a modern website for %s" % t["text"])
            self.assertEqual((out["source"], out["understood"]["type_theme"]), ("business-type pack", t["theme"]))

    def test_vague_requests_get_the_general_pack_and_say_so(self):
        for r in ("unique website", "business website", "I want a website", "something modern with animation"):
            out = generate_pack(r)
            self.assertEqual(out["understood"]["type_theme"], "general_business", r)
            self.assertTrue([n for n in out["notes"] if "does not name a trade" in n], r)

    def test_an_unknown_trade_gets_neutral_text_and_a_clear_note(self):
        out = generate_pack("Create a website for a taxidermy studio")
        self.assertEqual((out["source"], out["understood"]["niche"], out["understood"]["type_theme"], out["problems"]), ("business-type pack", None, "general_business", []))
        self.assertTrue([n for n in out["notes"] if "taxidermy" in n and "general local business pack" in n])
        self.assertNotIn("taxidermy", json.dumps(out["pack"]).lower())

    def test_typos(self):
        for r, nid in (("pest controll website", "pest_control"), ("tatoo studio website", "tattoo_studio"), ("Create a website for a plumbar in Pune", "plumber_electrician"),
                       ("dental clinc website", "dental_clinic"), ("mujhe termite treatmnt ki website banakar do", "pest_control")):
            self.assertEqual(pack_request.understand(r)["niche"], nid, r)

    def test_fresh_requests(self):
        for r, nid in (("I need a website for my chai tapri in Pune", "chai_tea_stall"), ("yoga teacher training in Rishikesh website", "yoga_retreat"), ("mujhe gym ki website banani hai", "gym_fitness_studio"),
                       ("CA firm website for GST and ITR filing", "chartered_accountant"), ("NGO for stray dogs website", "animal_welfare"), ("scrap dealer website", "scrap_recycling"),
                       ("Create a website for a funeral services company", "funeral_services")):
            self.assertEqual(pack_request.understand(r)["niche"], nid, r)

    def test_brand_and_city_are_read(self):
        out = generate_pack("Create a website for a bakery called Sweet Crumbs in Pune")
        self.assertEqual((out["understood"]["niche"], out["understood"]["brand"], out["understood"]["city"]), ("bakery_cakes", "Sweet Crumbs", "Pune"))
        self.assertEqual(out["problems"], [])
        blob = json.dumps(out["pack"])
        self.assertIn("Sweet Crumbs", blob)
        self.assertNotIn("{brand}", blob)
        self.assertIn("menu", out["pack"])

    def test_without_a_brand_the_placeholder_stays(self):
        self.assertIn("{brand}", json.dumps(generate_pack("pest control website")["pack"]))

    def test_hindi_is_flagged_not_faked(self):
        out = generate_pack("मुझे दीमक का इलाज की वेबसाइट चाहिए")
        self.assertEqual(out["understood"]["niche"], "pest_control")
        self.assertTrue([n for n in out["notes"] if "Devanagari" in n])

    def test_empty_request(self):
        with self.assertRaises(ValueError):
            generate_pack("  ")


class AuthorFallback(unittest.TestCase):
    """Trades no spec niche covers are answered from the author's business types; the spec's own requests never are."""

    def test_the_fallback_types_are_exactly_the_uncovered_ones(self):
        covered = {t for v in pack_spec.AUTHOR_EQUIV.values() for t in v}
        self.assertEqual(set(W.fallback_niches()), set(T) - covered)
        self.assertEqual(set(W.fallback_niches()), set(pack_spec.FALLBACK_THEME))
        self.assertTrue(all(n["theme"] in W.types() for n in W.fallback_niches().values()))

    def test_uncovered_trades(self):
        for r, nid in (("optical shop website", "optical"), ("pottery classes website", "pottery"), ("tyre shop website", "tyres"), ("welding workshop website", "welding"),
                       ("graphic design studio website", "design"), ("business consultant website", "consulting"), ("mujhe chashme ki dukaan ki website chahiye", "optical")):
            out = generate_pack(r)
            self.assertEqual((out["source"], out["understood"]["niche"], out["problems"]), ("niche pack", nid, []), r)
            self.assertTrue([n for n in out["notes"] if "author's" in n], r)
            self.assertIn(out["pack"]["theme"], W.types())

    def test_the_spec_requests_never_reach_the_fallback(self):
        hits = []
        for nid, n in NICHES.items():
            for x in n["requests"]:
                for r in ("%s website" % x, "Create a website for a %s in Jaipur" % x, "mujhe %s ki website banakar do" % x):
                    if pack_request.understand(r).get("niche_list"):
                        hits.append(r)
        self.assertEqual(hits, [])

    def test_a_fallback_pack_becomes_a_site(self):
        from corecraft import pipeline
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run_pack("Create a website for an optical shop in Pune", d, 1, photos=False)
            self.assertTrue((Path(r["dir"]) / "preview.html").exists())


class AuthorList(unittest.TestCase):
    """CORECRAFT_NICHE_FILE=author: the author's 77 business types + 16 general packs, through the same code."""

    @classmethod
    def setUpClass(cls):
        W.use_niche_file("author")
        cls.niches = W.niches()
        cls.packs = {n: W.build_pack(v) for n, v in cls.niches.items()}
        cls.types = W.build_type_packs()
        cls.foods = {n for n, v in cls.niches.items() if v["food"]} | {"type_" + t for t, v in W.types().items() if v.get("menu")}

    @classmethod
    def tearDownClass(cls):
        W.use_niche_file(None)

    def test_one_niche_per_business_type(self):
        self.assertEqual(W.niche_file(), W.AUTHOR_FILE)
        self.assertEqual(list(self.niches), list(T))
        for nid, n in self.niches.items():
            self.assertEqual(len(n["services"]), 6, nid)
            self.assertEqual(len({s.lower() for s in n["services"]}), 6, nid)
            self.assertEqual(n["food"], bool(n["menu"]), nid)
            self.assertIn(n["family"], W.FAMILIES, nid)
        self.assertEqual(set(W.types()), set(W.FAMILIES) | {"general"})
        self.assertEqual(W.fallback_niches(), {})

    def test_every_pack_passes_the_rules(self):
        self.assertEqual(pack_check.check_batch(list(self.packs.values()) + self.types, foods=self.foods), [])

    def test_every_niche_is_found_by_its_own_names(self):
        wrong = []
        for nid, n in self.niches.items():
            for x in n["requests"]:
                for r in ("%s website" % x, "mujhe %s ki website banakar do" % x):
                    if pack_request.understand(r)["niche"] != nid:
                        wrong.append(r)
        self.assertEqual(wrong, [])

    def test_requests(self):
        for r, nid in (("pest control website for flats", "cleaning"), ("gaming cafe with ps5 website", "gaming"), ("eye hospital website for cataract surgery", "eye"),
                       ("Create a website for a bakery called Sweet Crumbs in Pune", "bakery")):
            self.assertEqual(generate_pack(r)["understood"]["niche"], nid, r)
        self.assertEqual(generate_pack("unique website")["understood"]["type_theme"], "general")


class Site(unittest.TestCase):
    def test_a_site_from_a_request(self):
        from corecraft import pipeline
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run_pack("Create a website for a pest control in Jaipur", d, 1)
            page = (Path(r["dir"]) / "preview.html").read_text(encoding="utf-8")
            self.assertIn("Pest Control", page)
            self.assertNotIn("{brand}", page)
            self.assertNotIn("Sample Customer", page)
            self.assertTrue((Path(r["dir"]) / "pack.json").exists())

    def test_a_site_for_an_unknown_trade(self):
        from corecraft import pipeline
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run_pack("Create a website for a taxidermy studio", d, 1, photos=False)
            self.assertTrue((Path(r["dir"]) / "preview.html").exists())
            self.assertTrue([n for n in r["needs_review"] if "taxidermy" in n])

    def test_cli_prints_a_pack(self):
        r = subprocess.run([sys.executable, str(ROOT / "main.py"), "--pack", "mujhe termite treatment ki website banakar do"], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           cwd=tempfile.gettempdir(), env=ENV)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["id"], "pest_control")

    def test_cli_with_the_author_list(self):
        r = subprocess.run([sys.executable, str(ROOT / "main.py"), "--pack", "mujhe termite treatment ki website banakar do"], capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           cwd=tempfile.gettempdir(), env=dict(os.environ, CORECRAFT_NICHE_FILE="author"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["id"], "cleaning")


class Production(unittest.TestCase):
    """What must hold when the pack path is used by other programs and by many people at once."""

    def test_every_niche_with_every_kind_of_city(self):
        cities = (None, "Pune", "Ahmedabad", "Thiruvananthapuram", "Visakhapatnam", "Sri Ganganagar", "Navi Mumbai Thane", "Bhubaneswar Odisha India")
        for nid, n in list(NICHES.items()) + list(W.fallback_niches().items()):
            for c in cities:
                p = W.build_pack(n, city=c)
                self.assertEqual(pack_check.check_pack(p, food=bool(n["menu"])), [], (nid, c))
                if c:
                    self.assertIn(c, json.dumps(p), (nid, c))
        for t in W.spec()["types"]:
            for c in cities:
                self.assertEqual(pack_check.check_pack(W.build_type_pack(t["theme"], c), food=t["theme"] == "food_dining"), [], (t["theme"], c))

    def test_names_and_cities_from_a_request_are_cleaned(self):
        for r in ('pest control called "{brand}"', "pest control called <b>Bad</b> in <i>Jaipur</i>", 'dental clinic called https://evil.example', "Create a website for a plumber in 12345",
                  "bakery called {{x}} ${y}", "Create a website for a bakery called A\"B in Delhi"):
            out = generate_pack(r)
            blob = json.dumps(out["pack"])
            for bad in ("<b>", "<i>", "http", "${", "{{"):
                self.assertNotIn(bad, blob, r)
            self.assertEqual(out["problems"], [], r)
        self.assertEqual(pack_request.clean_name("Sharma Brothers And"), "Sharma Brothers")
        self.assertIsNone(pack_request.clean_name("<b>x</b>"))
        self.assertIsNone(pack_request.clean_name("a" * 80))
        self.assertIsNone(pack_request.clean_name("Pune 411001", "city"))

    def test_hostile_requests_never_crash(self):
        for r in ("x" * 5000, "😀😀😀", "\x00\x01 pest control ‮", "a " * 3000, "website\n\nfor\npest\ncontrol", "'; DROP TABLE users;--", "123456", "called \\ pest control",
                  "zzqx blorf website", "Create a website for a taxidermy studio", "optical"):
            out = generate_pack(r)
            self.assertEqual(out["problems"], [], r[:20])
        for bad in (None, 5, ["x"], "", "   "):
            with self.assertRaises(ValueError):
                generate_pack(bad)

    def test_same_request_same_pack(self):
        r = "Create a website for a bakery called Sweet Crumbs in Pune"
        self.assertEqual(generate_pack(r), generate_pack(r))

    def test_many_threads_get_the_same_answers(self):
        import threading
        want = {r: generate_pack(r)["pack"] for r in ("pest control website", "mujhe gym ki website banani hai", "Create a website for a bakery in Pune", "optical shop website")}
        pack_request.rebuild()   # the next callers build the index at the same moment
        errors = []

        def work():
            try:
                for _ in range(20):
                    for r, p in want.items():
                        if generate_pack(r)["pack"] != p:
                            errors.append(r)
            except Exception as e:   # noqa: BLE001
                errors.append(repr(e))
        threads = [threading.Thread(target=work) for _ in range(12)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(errors, [])

    def test_a_pack_that_fails_the_checker_is_never_handed_out(self):
        from corecraft import pack_api
        real = pack_check.check_pack
        pack_check.check_pack = lambda *a, **k: ["forced problem"]
        try:
            with self.assertRaises(pack_api.PackError):
                generate_pack("pest control website")
        finally:
            pack_check.check_pack = real

    def test_the_checker_runs_on_the_placeholder_not_on_the_name(self):
        out = generate_pack("Create a website for a pest control called Sharma Brothers Pest Control Services in Thiruvananthapuram")
        self.assertEqual(out["problems"], [])
        self.assertIn("Sharma Brothers Pest Control Services", out["pack"]["about"]["paragraphs"][0])

    def test_a_missing_or_wrong_niche_file_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "x.json"
            bad.write_text('{"niches": [{"id": "x"}], "types": [{"theme": "y"}]}', encoding="utf-8")
            for path in (bad, Path(d) / "missing.json"):
                W.use_niche_file(path)
                try:
                    with self.assertRaises(RuntimeError):
                        W.niches()
                finally:
                    W.use_niche_file(None)
        self.assertEqual(len(W.niches()), 99)

    def test_pictures_failing_do_not_break_the_site(self):
        from corecraft import photo_engine, pipeline
        real = photo_engine.generate_photos

        def boom(*a, **k):
            raise RuntimeError("image engine down")
        photo_engine.generate_photos = boom
        try:
            with tempfile.TemporaryDirectory() as d:
                r = pipeline.run_pack("pest control website in Jaipur", d, 1, photos=True)
                self.assertTrue((Path(r["dir"]) / "preview.html").exists())
                self.assertTrue([n for n in r["needs_review"] if "pictures could not be made" in n])
        finally:
            photo_engine.generate_photos = real

    def test_cli_errors_are_one_clear_line(self):
        def run(*a):
            return subprocess.run([sys.executable, str(ROOT / "main.py"), *a], capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir(), env=ENV)
        r = run("--pack", "pest control", "--out", "/proc/nope/x.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("cannot write", r.stderr)
        with tempfile.TemporaryDirectory() as d:
            r = run("--pack", "pest control website", "--out", d + "/p/pest.json")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(Path(d + "/p/pest.json").read_text())["id"], "pest_control")


if __name__ == "__main__":
    unittest.main()
