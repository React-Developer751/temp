"""The picture bridge: a site gets its own niche pictures, files, alt text and a readable hero; unknown business falls back; no engine = SVG art."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from corecraft import photo_engine, pipeline


class PhotoTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.pop("CORECRAFT_NO_PHOTOS", None)
        if photo_engine.find_engine() is None:
            self.skipTest("PixelMath engine not found (install pixelmath, or keep it at ../image/pixelmath next to this repo)")

    def tearDown(self):
        if self._old is not None:
            os.environ["CORECRAFT_NO_PHOTOS"] = self._old

    def test_dental_site_gets_pictures_files_and_a_readable_hero(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run("dental clinic in Pune", d, 2, photo_count=3)
            self.assertEqual((r["photos"]["niche"], r["photos"]["fallback"]), ("dental", False))
            site = Path(r["out_dir"]) if "out_dir" in r else next(Path(d).iterdir())
            info = json.loads((site / "images" / "images.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(info["images"]["hero"]["contrast"], 4.5)
            for img in [info["images"]["hero"], info["images"]["about"]] + info["images"]["tiles"]:
                self.assertTrue((site / img["src"]).is_file(), img["src"])
            html = (site / "preview.html").read_text(encoding="utf-8")
            self.assertIn("hero-photo", html)
            self.assertIn("images/hero.jpg", html)
            self.assertNotIn("data:image/jpeg", html)                     # no base64 pictures inside the page (the favicon is a small SVG)

    def test_switch_off_keeps_the_svg_art(self):
        os.environ["CORECRAFT_NO_PHOTOS"] = "1"
        try:
            with tempfile.TemporaryDirectory() as d:
                r = pipeline.run("dental clinic in Pune", d, 2)
                self.assertIsNone(r["photos"])
                self.assertNotIn("hero-photo", (next(Path(d).iterdir()) / "preview.html").read_text(encoding="utf-8"))
        finally:
            del os.environ["CORECRAFT_NO_PHOTOS"]


if __name__ == "__main__":
    unittest.main()
