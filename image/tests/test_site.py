import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.studio.niches import NICHES, load_all                                  # noqa: E402
from pixelmath.studio.site import (MOOD_MAP, PROFILE_TO_NICHE, TYPE_TO_NICHE, alt_text, mood_for, niche_for,  # noqa: E402
                                   site_pictures)

load_all()


class MappingTests(unittest.TestCase):
    def test_every_business_type_has_a_picture_niche(self):
        self.assertGreaterEqual(len(TYPE_TO_NICHE), 77)                      # every Core-Craft business type
        for t, n in TYPE_TO_NICHE.items():
            self.assertIn(n, NICHES, "%s -> %s" % (t, n))
        for p, n in PROFILE_TO_NICHE.items():
            self.assertIn(n, NICHES, "%s -> %s" % (p, n))

    def test_sub_niche_beats_type_and_words_refine_the_type(self):
        self.assertEqual(niche_for({"business_type": "restaurant", "profile": "italian"})[0], "restaurant-italian")
        self.assertEqual(niche_for({"business_type": "restaurant", "profile": "south_indian"})[0], "south-indian")
        self.assertEqual(niche_for({"business_type": "restaurant"})[0], "restaurant")
        self.assertEqual(niche_for({"business_type": "clothing", "profile": "saree"})[0], "saree-boutique")
        self.assertEqual(niche_for({"business_type": "clothing"})[0], "fashion-boutique")
        self.assertEqual(niche_for({"business_type": "school"}, "tuition classes for JEE")[0], "coaching-tuition")
        self.assertEqual(niche_for({"business_type": "school"}, "Sunrise Public School, classrooms")[0], "school")
        self.assertEqual(niche_for({"business_type": "clinic"}, "skin care clinic")[0], "skin-clinic")
        self.assertEqual(niche_for({"business_type": "clinic"}, "family doctor clinic")[0], "clinic-doctor")
        self.assertEqual(niche_for({"business_type": "garage"}, "car detailing and car wash")[0], "car-wash")
        self.assertEqual(niche_for({"business_type": "garage"}, "bike service and repair")[0], "bike-garage")
        self.assertEqual(niche_for({"business_type": "garage"}, "car service and repair")[0], "car-repair")
        self.assertEqual(niche_for({"business_type": "taxi"}, "self drive car rental")[0], "car-rental")
        self.assertEqual(niche_for({"business_type": "hotel"}, "farm stay and homestay")[0], "farm-stay")
        self.assertEqual(niche_for({"business_type": "insurance"}, "home loan and personal loan agent")[0], "loan-finance")
        self.assertEqual(niche_for({"business_type": "cleaning"}, "Cleaning & Pest Control")[0], "cleaning")
        self.assertEqual(niche_for({"business_type": "events"}, "wedding mandap decoration")[0], "wedding")
        self.assertEqual(niche_for({"business_type": "events"}, "birthday party decoration")[0], "event-party")
        self.assertEqual(niche_for({"business_type": "autosales"}, "bike showroom")[0], "bike-showroom")
        self.assertEqual(niche_for({"business_type": "autosales", "profile": "autosales"}, "premium car showroom")[0], "car-showroom")

    def test_unknown_types_are_not_guessed(self):
        nid, why = niche_for({"business_type": "teleportation"})
        self.assertIsNone(nid)
        self.assertIn("no picture niche", why)
        self.assertIsNone(niche_for({})[0])

    def test_mood_follows_the_site_palette(self):
        self.assertEqual(mood_for({"mood": "bold"}, {"dark": True}, "gym"), "dark")           # a dark site gets a dark picture
        self.assertEqual(mood_for({"mood": "calm"}, {"dark": False}, "dental"), "cool")
        self.assertEqual(mood_for({"mood": "warm"}, {}, "bakery"), "warm")
        self.assertEqual(mood_for({"mood": "bold"}, {}, "gym"), NICHES["gym"].mood)           # bold = keep the niche's own mood
        self.assertTrue(set(MOOD_MAP.values()) <= {None, "warm", "cool", "dark", "light"})

    def test_alt_text_names_the_brand_and_the_kind(self):
        self.assertIn("Harmony", alt_text({"brand": "Harmony Dental"}, "dental", "hero"))
        self.assertIn("Dental", alt_text({"brand": "Harmony Dental"}, "dental", "hero"))
        self.assertTrue(alt_text({"brand": ""}, None, "tile"))


class SitePictureTests(unittest.TestCase):
    def test_a_site_gets_files_sizes_alt_text_and_a_readable_headline_colour(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = site_pictures({"business_type": "dental", "brand": "Harmony Dental", "mood": "calm"}, {"primary": "#0e7490", "dark": False}, seed=1,
                                count=4, out_dir=os.path.join(tmp, "images"), text="Harmony Dental braces implants", subdir="images")
            self.assertEqual((out["niche"], out["fallback"]), ("dental", False))
            self.assertEqual(out["accent"], "#0e7490")
            hero, about, tiles = out["images"]["hero"], out["images"]["about"], out["images"]["tiles"]
            self.assertEqual((hero["width"], hero["height"]), (1280, 640))
            self.assertEqual(len(tiles), 2)
            self.assertGreaterEqual(hero["contrast"], 4.5)
            self.assertIn(hero["text_color"], ("#ffffff", "#0d0d14"))
            self.assertLess(hero["bytes"], 60000)
            for t in tiles:
                self.assertLess(t["bytes"], 25000)
            for it in [hero, about] + tiles:
                self.assertTrue(it["src"].startswith("images/"))
                self.assertTrue(os.path.isfile(os.path.join(tmp, it["src"])), it["src"])
                self.assertEqual(os.path.getsize(os.path.join(tmp, it["src"])), it["bytes"])
                self.assertTrue(it["alt"])
            with open(os.path.join(tmp, "images", "images.json"), encoding="utf-8") as fh:
                saved = json.load(fh)
            self.assertEqual(saved["images"]["hero"]["src"], "images/hero.jpg")
            self.assertNotIn("_data", json.dumps(saved))

    def test_unknown_business_gets_a_neutral_abstract_in_the_brand_colour(self):
        out = site_pictures({"business_type": "teleportation", "brand": "Beam Co"}, {"primary": "#aa3377"}, seed=1, count=3)
        self.assertTrue(out["fallback"])
        self.assertIsNone(out["niche"])
        self.assertEqual(out["accent"], "#aa3377")
        self.assertGreaterEqual(out["images"]["hero"]["contrast"], 4.5)

    def test_same_input_same_pictures_and_different_seed_differs(self):
        a = site_pictures({"business_type": "gym", "brand": "Iron"}, {"primary": "#db2e1f", "dark": True}, seed=3, count=3)
        b = site_pictures({"business_type": "gym", "brand": "Iron"}, {"primary": "#db2e1f", "dark": True}, seed=3, count=3)
        c = site_pictures({"business_type": "gym", "brand": "Iron"}, {"primary": "#db2e1f", "dark": True}, seed=4, count=3)
        self.assertEqual(a["images"]["hero"]["bytes"], b["images"]["hero"]["bytes"])
        self.assertEqual(a["mood"], "dark")
        self.assertNotEqual((a["images"]["hero"]["bytes"], a["images"]["about"]["bytes"]), (c["images"]["hero"]["bytes"], c["images"]["about"]["bytes"]))


if __name__ == "__main__":
    unittest.main()
