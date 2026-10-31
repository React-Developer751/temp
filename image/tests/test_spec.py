import contextlib
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath.studio.niches import NICHES, load_all                                           # noqa: E402
from pixelmath.studio.portrait import outfit_for                                               # noqa: E402
from pixelmath.studio import spec as spec_mod                                                   # noqa: E402
from pixelmath.studio.spec import (SLOT_SIZES, STYLE_LINE, SpecUnavailable, available, businesses, data, full_request, parse_request,   # noqa: E402
                                   render, resolve_niche, spec_dir, spec_prompts, split_slot)

load_all()
STUDIO = os.path.join(ROOT, "pixelmath", "studio")
SOURCE = os.path.join(ROOT, "studio_data", "spec", "image_ai_spec.json")          # the owner's full spec (source checkout only)
with open(os.path.join(STUDIO, "spec_prompts.json"), encoding="utf-8") as fh:
    SPEC = json.load(fh)


@contextlib.contextmanager
def spec_missing():
    """Behave like a broken installation: no $PIXELMATH_SPEC_DIR and no spec data files next to the module."""
    saved = (spec_mod._DATA, spec_mod.SPEC_DIR, os.environ.pop("PIXELMATH_SPEC_DIR", None))
    with tempfile.TemporaryDirectory() as empty:
        spec_mod._DATA, spec_mod.SPEC_DIR = None, empty
        try:
            yield
        finally:
            spec_mod._DATA, spec_mod.SPEC_DIR = saved[0], saved[1]
            if saved[2] is not None:
                os.environ["PIXELMATH_SPEC_DIR"] = saved[2]


class PackageData(unittest.TestCase):
    def test_the_package_ships_the_spec_data_files(self):
        for fn in ("spec_data.json", "spec_prompts.json"):
            self.assertTrue(os.path.isfile(os.path.join(STUDIO, fn)), fn)
        if not os.environ.get("PIXELMATH_SPEC_DIR"):
            self.assertEqual(spec_dir(), spec_mod.SPEC_DIR)
        self.assertTrue(available())
        self.assertEqual(data()["style_line"], STYLE_LINE)
        self.assertEqual(full_request("Cake", {"accent": "#111111", "bg": "#eeeeee"}), "Cake. %s. Palette: accent #111111 on #eeeeee." % STYLE_LINE)

    @unittest.skipUnless(os.path.isfile(SOURCE), "the source spec (studio_data/spec/) is not present")
    def test_the_compact_prompt_list_matches_the_source_spec(self):
        with open(SOURCE, encoding="utf-8") as fh:
            src = json.load(fh)
        strip = lambda x: [{"slot": it["slot"], "prompt": it["prompt"]} for it in x["items"]]          # noqa: E731
        self.assertEqual(SPEC["businesses"], [{"id": b["id"], "items": strip(b)} for b in src["businesses"]])
        self.assertEqual(SPEC["packs"], [{"name": p["name"], "items": strip(p)} for p in src["packs"]])
        self.assertTrue(all((it["w"], it["h"]) == SLOT_SIZES[it["slot"].split("-")[0]] for b in src["businesses"] + src["packs"] for it in b["items"]))
        with spec_missing():
            os.environ["PIXELMATH_SPEC_DIR"] = os.path.dirname(SOURCE)           # the full image_ai_spec.json gives the same prompts
            try:
                self.assertEqual(spec_prompts("pest_control"), strip(src["businesses"][0]))
            finally:
                del os.environ["PIXELMATH_SPEC_DIR"]

    def test_without_the_data_files_the_spec_says_not_available(self):
        with spec_missing():
            self.assertFalse(available())
            with self.assertRaises(SpecUnavailable) as cm:
                businesses()
            self.assertIn("missing from this installation", str(cm.exception))
            with self.assertRaises(SpecUnavailable):
                render("Shop front at dusk, for a bakery website", slot="hero-1", size=(160, 90), fmt=None)
            with self.assertRaises(FileNotFoundError):
                spec_prompts("pest_control")
            self.assertIsNone(parse_request("Shop front at dusk, for a bakery website")["style_unsupported"])     # parsing alone needs no data

    def test_the_spec_folder_can_be_given_by_environment(self):
        d = spec_mod.SPEC_DIR
        with spec_missing():
            os.environ["PIXELMATH_SPEC_DIR"] = d
            try:
                self.assertTrue(available())
                self.assertEqual(len(businesses()), 99)
                self.assertEqual(len(spec_prompts("dental_clinic")), 20)
            finally:
                del os.environ["PIXELMATH_SPEC_DIR"]


class SpecParsing(unittest.TestCase):
    def test_spec_has_99_businesses_with_20_pictures_and_20_types(self):
        self.assertEqual(len(SPEC["businesses"]), 99)
        self.assertTrue(all(len(b["items"]) == 20 for b in SPEC["businesses"]))
        self.assertEqual(len(SPEC["packs"]), 20)
        self.assertEqual(len(businesses()), 99)

    def test_every_prompt_names_its_business(self):
        for b in SPEC["businesses"]:
            for it in b["items"]:
                self.assertEqual(parse_request(it["prompt"])["business"], data()["by_id"][b["id"]]["name"].lower(), (b["id"], it["slot"]))
        for p in SPEC["packs"]:
            for it in p["items"]:
                self.assertEqual(parse_request(it["prompt"])["business"], p["name"].lower())

    def test_a_caption_that_says_for_a_something_does_not_confuse_the_business(self):
        r = parse_request("Reduces stains for a brighter smile, for a dental clinic website. %s. Palette: accent #0f8a8f on #f3f9f9." % STYLE_LINE)
        self.assertEqual((r["business"], r["accent"], r["bg"]), ("dental clinic", "#0f8a8f", "#f3f9f9"))
        self.assertEqual(r["subject"], "Reduces stains for a brighter smile")

    def test_team_and_background_requests_are_recognised(self):
        t = parse_request("portrait of a friendly senior technician, illustrated character, shoulders up, for a pest control website")
        self.assertEqual((t["slot_hint"], t["role"]), ("team", "senior technician"))
        b = parse_request("soft abstract background texture in the mood of a pest control, no subject, for a pest control website")
        self.assertEqual(b["slot_hint"], "background")

    def test_every_business_resolves_to_a_niche_that_exists(self):
        for b in businesses():
            nid, how = resolve_niche(b["name"].lower())
            self.assertTrue(nid in NICHES, "%s -> %s: niche does not exist" % (b["id"], b["niche"]))
            self.assertEqual(nid, b["niche"])

    def test_slots(self):
        self.assertEqual(split_slot("gallery-3"), ("gallery", 2))
        self.assertEqual(split_slot("about"), ("about", 0))
        with self.assertRaises(ValueError):
            split_slot("banner")
        self.assertEqual(SLOT_SIZES["hero"], (1600, 900))


class SpecRendering(unittest.TestCase):
    P = "Termite drilling (pest control), for a pest control website"

    def test_each_slot_has_its_size_a_small_file_and_no_wrong_scene(self):
        for slot, size in (("hero-1", (320, 180)), ("gallery-2", (200, 200)), ("card-3", (240, 180)), ("team-1", (150, 150)), ("background", (320, 180)), ("about", (240, 180))):
            r = render(full_request(self.P, {"accent": "#1565c0", "bg": "#f5f6f7"}), slot=slot, seed=2, size=size, fmt="jpeg")
            self.assertEqual(r.report["size"], list(size), slot)
            self.assertEqual((r.canvas.w, r.canvas.h), size)
            self.assertGreater(len(r.data), 500)
            self.assertEqual(r.data[:2], b"\xff\xd8")
            if slot not in ("team-1", "background"):
                self.assertEqual(r.report["niche"], "pest-control")

    def test_hero_keeps_the_headline_readable(self):
        r = render(full_request(self.P, {"accent": "#1565c0", "bg": "#f5f6f7"}), slot="hero-1", seed=1, size=(400, 225), fmt=None)
        self.assertGreaterEqual(r.report["contrast"], 4.5)
        self.assertIn(r.report["text_color"], ("#ffffff", "#0d0d14"))

    def test_same_request_same_picture_and_slots_differ(self):
        req = full_request(self.P, {"accent": "#1565c0", "bg": "#f5f6f7"})
        a = render(req, slot="gallery-1", seed=4, size=(160, 160), fmt=None)
        b = render(req, slot="gallery-1", seed=4, size=(160, 160), fmt=None)
        c = render(req, slot="card-1", seed=4, size=(160, 160), fmt=None)
        self.assertEqual(a.hash, b.hash)
        self.assertEqual(a.canvas.px, b.canvas.px)
        self.assertNotEqual(a.canvas.px, c.canvas.px)

    def test_dark_background_gives_a_dark_picture_and_an_unsupported_style_is_reported(self):
        r = render("Cabin, for a farm stay and homestay website. photo-like, 3d render. Palette: accent #c8a45a on #14161a.", slot="card-1", seed=1, size=(160, 120), fmt=None)
        self.assertEqual(r.report["mood"], "dark")
        self.assertIn("not drawn", r.report["style_note"])

    def test_an_unknown_business_gets_a_neutral_picture(self):
        r = render("Beaming people up, for a teleportation booth website. Palette: accent #aa3377 on #ffffff.", slot="hero-1", seed=1, size=(320, 180), fmt=None)
        self.assertTrue(r.report["fallback"])
        self.assertIsNone(r.report["niche"])


class Portraits(unittest.TestCase):
    def test_outfit_follows_the_role_then_the_business(self):
        self.assertEqual(outfit_for("consultant dentist", "dental"), "medical")
        self.assertEqual(outfit_for("head chef", None), "chef")
        self.assertEqual(outfit_for("site engineer", "construction"), "hardhat")
        self.assertEqual(outfit_for("customer support lead", None), "headset")
        self.assertEqual(outfit_for("advocate", "law-firm"), "suit")
        self.assertEqual(outfit_for("greeter", "dental"), "medical")
        self.assertEqual(outfit_for("greeter", None), "shirt")
        self.assertEqual(outfit_for("lead engineer", "saas"), "glasses")             # an engineer of a software team is not on a building site
        self.assertEqual(outfit_for("sound engineer", "dj-sound"), "glasses")
        self.assertEqual(outfit_for("dental assistant", "dental"), "medical")
        self.assertEqual(outfit_for("nursery supervisor", "landscape"), "hardhat")      # "nursery" is not "nurse"
        self.assertEqual(outfit_for("security supervisor", "security"), "cap")


class NoText(unittest.TestCase):
    def test_no_niche_scene_draws_letters_or_numbers(self):
        """The spec's rule: no text, letters, numbers or logos in any picture (signs and screens are plain shapes)."""
        import pixelmath.text as T
        from pixelmath.studio.palette import make_palette
        from pixelmath.studio.scene import render_niche
        calls, orig = [], T.draw_text
        T.draw_text = lambda *a, **k: calls.append(a[1]) or orig(*a, **k)
        try:
            for nid, n in NICHES.items():
                before = len(calls)
                render_niche(n, 200, 100, 1, make_palette(n.accent, n.mood), "left", "fit")
                self.assertEqual(calls[before:], [], nid)
        finally:
            T.draw_text = orig


class NoUndrawnEdges(unittest.TestCase):
    def test_wide_and_square_crops_never_show_an_undrawn_black_edge(self):
        """A wide camera (zoomed out) shows more floor / sky than the scene's main view: every niche must draw far enough (found in tiffin-service, chai-stall, construction)."""
        from pixelmath.studio.palette import make_palette
        from pixelmath.studio.scene import render_niche

        def black(cv, frac=0.85):
            w, h, px = cv.w, cv.h, cv.px
            lum = lambda x, y: sum(px[(y * w + x) * 3:(y * w + x) * 3 + 3]) / 3.0            # noqa: E731
            edges = {"bottom": [(x, h - 2) for x in range(0, w, 3)], "top": [(x, 1) for x in range(0, w, 3)],
                     "left": [(1, y) for y in range(0, h, 3)], "right": [(w - 2, y) for y in range(0, h, 3)]}
            return [k for k, pts in edges.items() if sum(1 for x, y in pts if lum(x, y) < 0.025) >= frac * len(pts)]
        bad = []
        for nid, n in NICHES.items():
            pal = make_palette(n.accent, n.mood)
            for (w, h, zone) in ((120, 120, None), (160, 90, "left")):
                for v in ("wide", "wide-flip"):
                    e = black(render_niche(n, w, h, 1, pal, zone, v).canvas)
                    if e:
                        bad.append((nid, v, w, e))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
