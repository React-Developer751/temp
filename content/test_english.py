"""English of the output: the agreement helper (is/are, was/were, it/them) and regression checks on packs and pages."""
import json
import re
import unittest

from corecraft import pack_writer as W
from corecraft.content_engine import generate_content
from corecraft.grammar import a_an, agree, forms, is_plural


def page_text(c):
    out = []

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in ("ui", "needs_review", "missing", "generated_by", "facts_used", "keywords"):
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(c)
    return "\n".join(out)


class Agreement(unittest.TestCase):
    def test_plural_and_singular_phrases(self):
        for p in ("Custom Cakes", "desserts", "Breads And Cookies", "Sedans And SUVs", "groceries", "braces", "Kitchen Cabinets", "sweets", "Dairy, Bread And Eggs"):
            self.assertTrue(is_plural(p), p)
        for p in ("Home Delivery", "Root Canal Treatment", "fitness", "Dry Cleaning", "Hair Spa", "AC", "Wash And Fold", "bridal makeup", "Aerobics", "glass", "Children's Dentistry"):
            self.assertFalse(is_plural(p), p)

    def test_forms(self):
        self.assertEqual([forms("desserts")[k] for k in ("is", "was", "it", "this", "has")], ["are", "were", "them", "these", "have"])
        self.assertEqual([forms("home delivery")[k] for k in ("is", "was", "it", "this", "has")], ["is", "was", "it", "this", "has"])
        self.assertEqual(agree("cookies", "is", "are"), "are")
        self.assertEqual([a_an(w) for w in ("AC visit", "hour", "used car", "event", "bakery", "NGO")], ["an", "an", "a", "an", "a", "an"])


class PackEnglish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        W.use_niche_file(None)
        cls.blobs = {n: json.dumps(W.build_pack(v)) for n, v in W.niches().items()}

    def test_plural_services_take_plural_words(self):
        blob = self.blobs["bakery_cakes"]
        self.assertIn("what goes into them", blob)
        self.assertNotRegex(blob, r"(?i)(pastries and cupcakes|breads and cookies|custom cakes|eggless options) (is|was)\b")
        self.assertNotIn("so it reaches you", blob)

    def test_no_stiff_label_or_title_case_inside_sentences(self):
        for nid, blob in self.blobs.items():
            self.assertNotIn("Looking for help with", blob, nid)
            self.assertNotRegex(blob, r"(shop|clinic|studio|store|parlour|kitchen|cafe|restaurant|bakery|service) (place|business|practice|centre|space)\.", nid)
            self.assertNotIn("Craving home delivery", blob, nid)
        self.assertIn("Eggless options on offer today", self.blobs["bakery_cakes"])

    def test_plan_names_match_the_price_period(self):
        plans = W.build_pack(W.niches()["gym_fitness_studio"])["pricing"]["plans"]
        self.assertEqual([(p["name"], p["period"]) for p in plans][0], ("Monthly Plan", "/month"))
        for nid, n in W.niches().items():
            for p in W.build_pack(n)["pricing"]["plans"]:
                self.assertFalse(p["name"].startswith("Single") and re.search(r"month|quarter|year|week", p["period"]), (nid, p))

    def test_general_pack_does_not_use_trade_lines(self):
        blob = json.dumps(W.build_type_pack("general_business"))
        self.assertNotIn("short check at the end", blob)
        self.assertIn("as a local business", blob)

    def test_author_list_has_no_stiff_service_names(self):
        W.use_niche_file("author")
        try:
            names = [s for n in W.niches().values() for s in n["services"]]
        finally:
            W.use_niche_file(None)
        for bad in ("Bakery Cakes", "Festive Boxes", "Gym Classes"):
            self.assertNotIn(bad, names)


class PageEnglish(unittest.TestCase):
    def test_plural_items_on_a_page(self):
        for seed in range(1, 9):
            t = page_text(generate_content("bakery in Jaipur, cakes, cookies, desserts, breads", seed=seed))
            self.assertNotRegex(t, r"(?i)(?<!about )\b(desserts|cakes|cookies|breads) (is|was|works)\b", seed)
            self.assertNotRegex(t, r"(?i)about (desserts|cakes|cookies|breads)\?[^.]*through it\b", seed)
            self.assertNotRegex(t, r"(?i)(desserts|cakes|cookies|breads)[^.;?]*(goes into|order|with) it\b", seed)


if __name__ == "__main__":
    unittest.main()
