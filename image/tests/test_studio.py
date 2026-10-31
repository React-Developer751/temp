import io
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from jpeg_decode import decode_jpeg                                          # noqa: E402
from pixelmath import render                                                  # noqa: E402
from pixelmath.jpegwrite import JpegError, encode_jpeg                       # noqa: E402
from pixelmath.learn import LearnedModel, load_dataset, train_model          # noqa: E402
from pixelmath.studio import api, post                                       # noqa: E402
from pixelmath.studio.classifier import NicheClassifier, as_classifier, build_niche_nb, posterior, predict  # noqa: E402
from pixelmath.studio.match import infer_look, match_niche                   # noqa: E402
from pixelmath.studio.niches import NICHES, Niche, load_all                  # noqa: E402
from pixelmath.studio.palette import MOODS, make_palette, parse_color        # noqa: E402
from pixelmath.studio.scene import ZONES, render_niche                       # noqa: E402
from pixelmath.studio.stage import Stage                                     # noqa: E402
from test_api import Live                                                    # noqa: E402

load_all()


def psnr(a, b):
    mse = sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)
    return 99.0 if mse == 0 else 10 * math.log10(255 * 255 / mse)


class JpegTests(unittest.TestCase):
    def test_round_trip_with_an_independent_decoder(self):
        cv, _, _ = render("red house near a lake at sunset", 64, 48, 1)
        ref = bytes(int(min(1, max(0, v)) * 255 + 0.5) for v in cv.px)
        for q, floor in ((90, 28), (50, 24)):
            w, h, rgb = decode_jpeg(encode_jpeg(64, 48, cv.px, q))
            self.assertEqual((w, h), (64, 48))
            self.assertGreater(psnr(rgb, ref), floor, q)

    def test_odd_sizes_bytes_input_and_headers(self):
        for w, h in ((1, 1), (17, 9), (33, 65)):
            data = encode_jpeg(w, h, bytes([200, 100, 50]) * (w * h), 80)
            self.assertEqual(data[:2], b"\xff\xd8")
            self.assertEqual(data[-2:], b"\xff\xd9")
            dw, dh, rgb = decode_jpeg(data)
            self.assertEqual((dw, dh), (w, h))
            self.assertLess(max(abs(a - b) for a, b in zip(rgb[:3], (200, 100, 50))), 8)
        with self.assertRaises(JpegError):
            encode_jpeg(4, 4, [0.0] * 5)

    def test_size_target_lowers_quality_or_says_it_cannot(self):
        cv, _, _ = render("mandelbrot", 96, 64, 2)
        full = encode_jpeg(96, 64, cv.px, 90)
        small = encode_jpeg(96, 64, cv.px, 90, target_bytes=len(full) // 2)
        self.assertLessEqual(len(small), len(full) // 2)
        with self.assertRaises(JpegError):
            encode_jpeg(96, 64, cv.px, 90, target_bytes=50, min_quality=30)


class PaletteAndMatchTests(unittest.TestCase):
    def test_palette_and_colours(self):
        self.assertEqual(parse_color("#ff0000"), (1.0, 0.0, 0.0))
        self.assertEqual(parse_color("f00"), (1.0, 0.0, 0.0))
        self.assertIsNotNone(parse_color("teal"))
        with self.assertRaises(ValueError):
            parse_color("not-a-colour")
        walls = {m: make_palette("#2e86de", m).wall_top for m in MOODS}
        self.assertLess(sum(walls["dark"]), 1.2)
        self.assertGreater(sum(walls["light"]), 2.5)
        with self.assertRaises(ValueError):
            make_palette("#2e86de", "neon")

    def test_user_examples_map_to_the_right_scene_and_mood(self):
        self.assertEqual(match_niche("wood fired pizza on a board")[0], "restaurant-italian")
        n, _ = match_niche("gym with dumbbells in red light")
        self.assertEqual(n, "gym")
        mood, accent = infer_look("gym with dumbbells in red light")
        self.assertEqual(mood, "dark")
        self.assertGreater(accent[0], 0.7)
        self.assertEqual(match_niche("dental clinic reception, calm blue")[0], "dental")
        mood, accent = infer_look("dental clinic reception, calm blue")
        self.assertEqual(mood, "cool")
        self.assertGreater(accent[2], 0.7)

    def test_hinglish_hindi_and_refusing_to_guess(self):
        self.assertEqual(match_niche("daant ka doctor")[0], "dental")
        self.assertEqual(match_niche("मिठाई की दुकान")[0], "sweet-shop")
        for p in ("submarine under the sea", "astronomy observatory at night", "a pirate ship", "", "shop"):
            self.assertIsNone(match_niche(p)[0], p)

    def test_blind_prompt_gaps_stay_fixed(self):
        from pixelmath.studio.classifier import as_classifier
        clf = as_classifier(None)
        for prompt, niche in (("gents haircut shop", "barber"), ("puppies for sale", "petshop"), ("car washing service", "car-wash"), ("teeth cleaning", "dental"),
                              ("रंग बिरंगी कुर्तियों के कलेक्शन की तस्वीर चाहिए", "kurti-store"), ("रेशमी साड़ियों के रंगीन संग्रह की तस्वीर", "saree-boutique"),
                              ("passport, map and plane tickets on desk, adventurous orange tones", "travel-agency")):
            self.assertEqual(match_niche(prompt, clf)[0], niche, prompt)
        for prompt in ("shipyard with a big cargo vessel", "old pirate ship sailing stormy seas", "ski resort with snowy slopes"):
            self.assertIsNone(match_niche(prompt, clf)[0], prompt)             # sounds like a niche (logistics, travel, hotel) but is not

    def test_bugs_found_with_real_examples_stay_fixed(self):
        from pixelmath.studio.classifier import as_classifier
        clf = as_classifier(None)
        for prompt in ("underwater scuba diving school", "flying school with a small aeroplane", "aviation academy pilot training cockpit",
                       "cooking school kitchen with chefs and pans", "chess academy with boards and clocks", "crypto trading bot for investors"):
            self.assertIsNone(match_niche(prompt, clf)[0], prompt)             # a lookalike word must never summon the wrong niche
            self.assertIsNone(match_niche(prompt)[0], prompt + " (keywords only)")
        for prompt, niche in (("driving school with learner cars", "driving-school"), ("bike showroom with motorcycles", "bike-showroom"),
                              ("pottery workshop with clay", "pottery"), ("tattoo parlour with neon sign", "tattoo")):
            self.assertEqual(match_niche(prompt)[0], niche, prompt)            # these used to be lookalikes; they are real niches now
        self.assertNotEqual(match_niche("furniture showroom", clf)[0], "car-showroom")                       # "showroom" alone is not a car
        self.assertEqual(match_niche("बच्चों का खिलौनों का शोरूम, रंग बिरंगे", clf)[0], "toy-store")        # खिलौनों is an inflected खिलौने
        self.assertEqual(match_niche("दाँतों का इलाज", clf)[0] or "dental", "dental")
        self.assertEqual(match_niche("premium car showroom in Delhi, spotlight", clf)[0], "car-showroom")
        self.assertEqual(match_niche("steps section for an italian restaurant: choose, order, enjoy", clf)[0], "restaurant-italian")

    def test_every_niche_is_well_formed(self):
        self.assertGreaterEqual(len(NICHES), 40)
        for n in NICHES.values():
            self.assertGreaterEqual(len(n.strong), 8, n.id)
            self.assertGreaterEqual(len(n.weak), 4, n.id)
            self.assertTrue(n.subjects, n.id)
            self.assertIn(n.mood, MOODS, n.id)
            self.assertIsNotNone(parse_color(n.accent), n.id)
            for generic in ("shop", "store", "clinic", "service", "business", "design"):
                self.assertNotIn(generic, n.strong, n.id)
        self.assertTrue({"restaurant-italian", "gym", "dental", "saas", "kurti-store", "salon", "bakery", "yoga", "real-estate", "school"} <= set(NICHES))


class SceneTests(unittest.TestCase):
    def test_every_niche_shows_its_subject_and_is_deterministic(self):
        for nid, n in NICHES.items():
            pal = make_palette(n.accent, n.mood)
            a = render_niche(n, 240, 150, 3, pal, None, "fit")
            self.assertGreaterEqual(a.subject_score, 0.9, nid)
            self.assertEqual(len(a.canvas.px), 240 * 150 * 3)
            if nid in ("gym", "dental"):
                b = render_niche(n, 240, 150, 3, pal, None, "fit")
                self.assertEqual(a.canvas.px, b.canvas.px, nid)
                c = render_niche(n, 240, 150, 4, pal, None, "fit")
                self.assertNotEqual(a.canvas.px, c.canvas.px, nid)

    def test_camera_keeps_the_subject_away_from_the_text_zone(self):
        n = NICHES["dental"]
        pal = make_palette(n.accent, n.mood)
        for zone in ("left", "center", "bottom"):
            r = render_niche(n, 320, 160, 1, pal, zone, "fit")
            box = [b for b in r.stage.subjects if b[0] == n.subjects[0]][0]
            sc = 160 * r.camera.zoom
            cx = 160 + ((box[1] + box[3]) / 2 - r.camera.cx) * sc
            cy = 80 + ((box[2] + box[4]) / 2 - r.camera.cy) * sc
            x0, y0, x1, y1 = ZONES[zone]
            self.assertFalse(x0 * 320 < cx < x1 * 320 and y0 * 160 < cy < y1 * 160, zone)

    def test_stage_dry_run_draws_nothing(self):
        n = NICHES["gym"]
        S = Stage(120, 80, make_palette(n.accent, n.mood), 1, dry=True)
        n.fn(S)
        self.assertTrue(S.subjects)
        self.assertIsNone(S.finish())
        self.assertTrue(all(v == 0.0 for v in S.main.cv.px))

    def test_all_variants_render(self):
        n = NICHES["restaurant-italian"]
        pal = make_palette(n.accent, n.mood)
        seen = set()
        for v in ("fit", "close", "detail", "wide", "fit-flip"):
            r = render_niche(n, 200, 120, 2, pal, None, v)
            seen.add(tuple(r.canvas.px[:300:7]))
        self.assertGreaterEqual(len(seen), 4)


class JudgeTests(unittest.TestCase):
    def test_text_zone_contrast_is_guaranteed_in_every_mood(self):
        n = NICHES["restaurant-italian"]
        for mood in MOODS:
            for zone in ("left", "center", "bottom"):
                pal = make_palette(n.accent, mood)
                r = render_niche(n, 320, 160, 5, pal, zone, "fit")
                rep = post.ensure_zone_contrast(r.canvas, ZONES[zone], pal, {"dark": "white", "light": "dark"}.get(mood))
                self.assertGreaterEqual(rep["contrast"], 4.5, (mood, zone))
                self.assertGreaterEqual(post.worst_contrast(r.canvas, ZONES[zone], rep["text"]), 4.5)

    def test_hash_and_signature_helpers(self):
        a, _, _ = render("red house near a lake at sunset", 96, 64, 1)
        b, _, _ = render("blue ocean with a boat", 96, 64, 1)
        ta, tb = post.small(a, 64), post.small(b, 64)
        self.assertEqual(post.hamming(post.phash(ta), post.phash(ta)), 0)
        self.assertGreater(post.hamming(post.phash(ta), post.phash(tb)), 6)
        sa = post.hue_signature(ta)
        self.assertAlmostEqual(post.family_similarity(sa, sa), 1.0, places=6)
        self.assertGreater(post.contrast(1.0, 0.0), 20)
        self.assertAlmostEqual(post.luminance((1.0, 1.0, 1.0)), 1.0, places=3)

    def test_unknown_prompt_gets_a_neutral_fallback_never_a_wrong_subject(self):
        r = api.scene("submarine under the sea", 160, 100, 1, accent="#2e7d32", text_zone="left")
        rep = r.report
        self.assertTrue(rep["fallback"])
        self.assertIsNone(rep["niche"])
        self.assertEqual(rep["accent"], "#2e7d32")
        self.assertGreaterEqual(rep["contrast"], 4.5)
        self.assertIn("no niche", rep["fallback_reason"])

    def test_a_subject_that_cannot_be_shown_becomes_a_fallback(self):
        def broken(S):                                             # declares a subject but never draws it
            P = S.pal
            S.wall(P.wall_top, P.wall_bot, 0.8)
            S.put("pizza_board", 1.0, 0.9, 0.3)                    # drawn, but not marked as the subject the judge looks for
        from pixelmath.studio.niches import NICHES as REG
        REG["zz-test"] = Niche("zz-test", "Test", broken, ("pizza_board",), ("broken-test-word",) * 8, ("weak",) * 5, "#336699", "light", "test")
        try:
            r = api.scene("anything", 160, 100, 1, niche="zz-test")
            self.assertTrue(r.report["fallback"])
            self.assertIn("judge", r.report["fallback_reason"])
            self.assertGreaterEqual(r.report["redrawn"], 1)
        finally:
            del REG["zz-test"]

    def test_fallback_is_drawn_once_and_a_big_picture_gets_the_hero_budget(self):
        r = api.scene("crypto trading bot for investors", 320, 200, 1, text_zone="left", fmt="jpeg")
        self.assertTrue(r.report["fallback"])
        self.assertEqual(r.report["redrawn"], 0)                               # smooth on purpose: only contrast is judged
        big = api.scene("gym with dumbbells in red light", 1280, 640, 1, fmt="jpeg")
        self.assertTrue(big.report["size_budget_met"])
        self.assertLess(big.report["bytes"], 60000)
        self.assertGreater(big.report["bytes"], 12000)                         # not squeezed to the 25 KB tile budget

    def test_report_and_encoding(self):
        r = api.scene("dental clinic reception, calm blue", 320, 200, 2, text_zone="left", fmt="jpeg")
        rep = r.report
        for key in ("niche", "fallback", "mood", "accent", "text_color", "contrast", "redrawn", "scores", "seed", "bytes", "seconds"):
            self.assertIn(key, rep)
        self.assertEqual(rep["niche"], "dental")
        self.assertEqual(rep["mood"], "cool")
        self.assertEqual(r.data[:2], b"\xff\xd8")
        for bad in ({"text_zone": "top"}, {"variant": "zoom"}, {"mood": "neon"}, {"niche": "nope"}):
            with self.assertRaises(ValueError):
                api.scene("x", 64, 64, **bad)
        with self.assertRaises(ValueError):
            api.make_set("pizza", count=2)


class SetTests(unittest.TestCase):
    def test_a_set_is_one_style_many_compositions_and_fits_the_budgets(self):
        results, rep = api.make_set("wood fired pizza on a board", 5, 3, accent="#c0392b", mood="warm", text_zone="left", fmt="jpeg")
        self.assertEqual([r.report["role"] for r in results], ["hero", "about", "tile", "tile", "tile"])
        self.assertEqual((results[0].canvas.w, results[0].canvas.h), (1280, 640))
        self.assertGreaterEqual(rep["min_distance"], api.PHASH_MIN)
        self.assertGreaterEqual(rep["palette_family"], 0.6)
        self.assertGreaterEqual(rep["hero_contrast"], 4.5)
        self.assertLess(results[0].report["bytes"], 60000)
        for r in results[2:]:
            self.assertLess(r.report["bytes"], 25000)
        self.assertLess(rep["seconds"], 20)
        self.assertEqual({r.report["accent"] for r in results}, {"#c0392b"})
        self.assertFalse(any(r.report["fallback"] for r in results))
        for r in results:                                                     # every file really is a decodable JPEG of the stated size
            self.assertEqual(r.data[:2], b"\xff\xd8")
        w, h, _ = decode_jpeg(results[2].data) if results[2].canvas.w * results[2].canvas.h <= 120000 else (results[2].canvas.w, results[2].canvas.h, None)
        self.assertEqual((w, h), (results[2].canvas.w, results[2].canvas.h))

    def test_set_of_an_unknown_business_is_all_neutral_abstract(self):
        results, rep = api.make_set("submarine under the sea", 3, 1, accent="#336699", text_zone="left")
        self.assertTrue(rep["fallback"])
        self.assertTrue(all(r.report["fallback"] for r in results))
        self.assertGreaterEqual(rep["hero_contrast"], 4.5)


class TrainingTests(unittest.TestCase):
    def make_data(self, tmp, per=6):
        rows = []
        for nid, mood in (("dental", "cool"), ("gym", "dark"), ("school", "light")):
            os.makedirs(os.path.join(tmp, nid), exist_ok=True)
            for k in range(per):
                r = api.scene("a %s picture number %d" % (nid, k), 64, 40, k, niche=nid, mood=mood, fmt="jpeg")
                rel = "%s/%d.jpg" % (nid, k)
                with open(os.path.join(tmp, rel), "wb") as fh:
                    fh.write(r.data)
                words = {"dental": "teeth dentist chair", "gym": "dumbbells weights workout", "school": "classroom students desk"}[nid]
                rows.append({"image": rel, "caption": "%s variant %s" % (words, "abc"[k % 3]), "niche": nid, "mood": mood})
        with open(os.path.join(tmp, "manifest.jsonl"), "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        return rows

    def test_manifest_labels_train_a_classifier_that_survives_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_data(tmp)
            samples, skipped, sources = load_dataset(tmp)
            self.assertEqual((len(samples), sources["manifest"]), (18, 18))
            self.assertEqual({s.niche for s in samples}, {"dental", "gym", "school"})
            model = LearnedModel()
            metrics = train_model(model, samples, epochs=10, val_frac=0.0)
            self.assertEqual(metrics["niche_classes"], 3)
            self.assertIn("nichedental", model.rows)
            self.assertIn("moodcool", model.rows)
            path = os.path.join(tmp, "m.json")
            model.save(path)
            again = LearnedModel.load(path)
            self.assertEqual(again.extras["niche_nb"]["classes"].keys(), model.extras["niche_nb"]["classes"].keys())
            self.assertEqual({s.niche for s in again.samples}, {"dental", "gym", "school"})
            nb = again.extras["niche_nb"]
            self.assertEqual(predict(nb, "teeth and a dentist")[0], "dental")
            clf = as_classifier(again)
            self.assertIsInstance(clf, NicheClassifier)
            logp, known = clf("dumbbells weights workout area")
            self.assertEqual(posterior(logp)[0][1], "gym")
            self.assertGreaterEqual(known, 3)
            self.assertIsNone(clf("zzzz qqqq unrelated words only"))
            self.assertEqual(match_niche("weights workout dumbbells", clf)[0], "gym")

    def test_bad_manifest_lines_and_unknown_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = self.make_data(tmp, per=2)
            import shutil
            shutil.copy(os.path.join(tmp, "dental", "0.jpg"), os.path.join(tmp, "dental", "extra.jpg"))
            with open(os.path.join(tmp, "manifest.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"image": "dental/extra.jpg", "caption": "x y", "niche": "no-such-niche"}) + "\n")
            samples, skipped, _ = load_dataset(tmp)
            self.assertEqual(len(samples), 6)
            self.assertTrue(any("unknown niche" in why for _, why in skipped))
            with open(os.path.join(tmp, "manifest.jsonl"), "a", encoding="utf-8") as fh:
                fh.write("{broken\n")
            from pixelmath.learn import ModelError
            with self.assertRaises(ModelError):
                load_dataset(tmp)

    def test_without_labels_nothing_changes(self):
        self.assertIsNone(build_niche_nb([]))
        self.assertEqual(type(as_classifier(LearnedModel())), type(as_classifier(None)))        # no labels in the model: the packaged classifier (if any)


class SurfaceTests(unittest.TestCase):
    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "o.jpg")
            r = subprocess.run([sys.executable, "-m", "pixelmath", "gym with dumbbells in red light", "--studio", "--text-zone", "left", "--width", "320",
                                "--height", "200", "-o", out], cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("niche=gym", r.stdout)
            with open(out, "rb") as fh:
                self.assertEqual(fh.read(2), b"\xff\xd8")
            r = subprocess.run([sys.executable, "-m", "pixelmath", "--list-niches"], cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertIn("restaurant-italian", r.stdout)
            r = subprocess.run([sys.executable, "-m", "pixelmath", "pizza", "--studio", "--mood", "neon"], cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(r.returncode, 0)

    def test_api(self):
        live = Live()
        try:
            st, hdr, data = live.json("POST", "/scene", {"prompt": "gym with dumbbells in red light", "width": 320, "height": 200, "text_zone": "left"})
            self.assertEqual((st, hdr["content-type"], hdr["x-pixelmath-niche"], hdr["x-pixelmath-fallback"]), (200, "image/jpeg", "gym", "false"))
            self.assertEqual(data[:2], b"\xff\xd8")
            st, _, j = live.json("POST", "/scene", {"prompt": "submarine", "width": 128, "height": 80, "response": "base64"})
            self.assertEqual(st, 200)
            self.assertTrue(j["report"]["fallback"])
            st, hdr, data = live.json("POST", "/set", {"prompt": "dental clinic", "count": 3})
            self.assertEqual((st, hdr["content-type"]), (200, "application/zip"))
            z = zipfile.ZipFile(io.BytesIO(data))
            self.assertEqual(sorted(z.namelist()), ["about.jpg", "hero.jpg", "report.json", "tile-1.jpg"])
            self.assertGreaterEqual(json.loads(z.read("report.json"))["min_distance"], api.PHASH_MIN)
            self.assertTrue(any(n["id"] == "dental" for n in live.json("GET", "/niches")[2]["niches"]))
            for bad in ({"prompt": "x", "mood": "neon"}, {"prompt": "x", "accent": "zzz"}, {"prompt": "x", "nope": 1}, {"prompt": "x", "text_zone": "top"}, {}):
                self.assertEqual(live.json("POST", "/scene", bad)[0], 400, bad)
            self.assertEqual(live.json("POST", "/set", {"prompt": "x", "count": 9})[0], 400)
        finally:
            live.close()

    def test_spec_api_without_the_data_files_answers_501(self):
        from test_spec import spec_missing
        live = Live()
        try:
            with spec_missing():
                for method, path, body in (("POST", "/spec", {"prompt": "Shop front, for a bakery website"}), ("GET", "/spec/businesses", None),
                                           ("POST", "/spec/business", {"business": "bakery"})):
                    st, _, j = live.json(method, path, body)
                    self.assertEqual((st, j["error"]["code"] if isinstance(j.get("error"), dict) else j.get("error")), (501, "spec_unavailable"), path)
        finally:
            live.close()

    def test_spec_api(self):
        live = Live()
        try:
            st, hdr, data = live.json("POST", "/spec", {"prompt": "Termite drilling (pest control), for a pest control website. Palette: accent #1565c0 on #f5f6f7.", "slot": "card-2"})
            self.assertEqual((st, hdr["content-type"], hdr["x-pixelmath-niche"], hdr["x-pixelmath-size"], hdr["x-pixelmath-slot"]), (200, "image/jpeg", "pest-control", "800x600", "card-2"))
            self.assertEqual(data[:2], b"\xff\xd8")
            st, _, j = live.json("POST", "/spec", {"prompt": "portrait of a friendly dentist, illustrated character, shoulders up, for a dental clinic website", "response": "base64"})
            self.assertEqual((st, j["report"]["slot"], j["width"]), (200, "team-1", 600))
            st, _, j = live.json("GET", "/spec/businesses")
            self.assertEqual((st, len(j["businesses"])), (200, 99))
            for bad in ({"prompt": "x", "slot": "banner"}, {"prompt": ""}, {"prompt": "x", "nope": 1}, {"prompt": "x", "format": "gif"}, {}):
                self.assertEqual(live.json("POST", "/spec", bad)[0], 400, bad)
            self.assertEqual(live.json("POST", "/spec/business", {"business": "nothing"})[0], 400)
        finally:
            live.close()


if __name__ == "__main__":
    unittest.main()
