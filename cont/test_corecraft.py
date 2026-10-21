import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

from corecraft import asset_engine, content_engine, design_engine, pipeline

ROOT = Path(__file__).parent
PROMPTS = {
    "A cozy cafe called 'Chai Point' serving coffee and bakery items": "restaurant",
    "gym and fitness trainer website": "fitness",
    "mujhe ek software startup ka website banana hai": "tech",
    "portfolio for a freelance photographer": "portfolio",
    "coaching institute for school students": "education",
    "online boutique for handmade jewellery": "shop",
    "plumbing repairs": "business",
}


class Tests(unittest.TestCase):
    def test_niche_detection(self):
        for p, n in PROMPTS.items():
            self.assertEqual(content_engine.generate_content(p, 1)["niche"], n, p)

    def test_brand_extraction(self):
        self.assertEqual(content_engine.generate_content("cafe called 'Chai Point'", 1)["brand"], "Chai Point")
        self.assertEqual(content_engine.generate_content("gym named Iron Forge please", 1)["brand"], "Iron Forge")

    def test_deterministic_and_varied(self):
        p = "restaurant website"
        self.assertEqual(content_engine.generate_content(p, 5), content_engine.generate_content(p, 5))
        outs = {json.dumps(content_engine.generate_content(p, s)) for s in range(30)}
        self.assertGreater(len(outs), 15)

    def test_validation_rejects_bad(self):
        c = content_engine.generate_content("gym", 1)
        c["features"] = c["features"][:2]
        with self.assertRaises(ValueError):
            content_engine.validate_content(c)
        c = content_engine.generate_content("gym", 1)
        c["tagline"] = "lorem ipsum"
        with self.assertRaises(ValueError):
            content_engine.validate_content(c)

    def test_palette_contrast_many_seeds(self):
        for mood in asset_engine.MOOD_HUES:
            for s in range(200):
                c = {"mood": mood, "niche": "x", "brand": "B&B <x>", "features": [1] * 6}
                a = asset_engine.generate_assets(c, s)
                asset_engine.validate_assets(a)

    def test_full_pipeline_all_prompts(self):
        with tempfile.TemporaryDirectory() as d:
            for i, p in enumerate(PROMPTS):
                for seed in (1, 2, 3, 4):
                    r = pipeline.run(p, d, seed * 10 + i)
                    out = Path(r["dir"])
                    for f in ("App.jsx", "styles.css", "index.html", "preview.html", "content.json", "assets/hero.svg", "assets/logo.svg"):
                        self.assertTrue((out / f).stat().st_size > 50, f)
                    self.assertTrue(design_engine.validate_jsx((out / "App.jsx").read_text()))
                    self.assertNotIn("$", (out / "styles.css").read_text())

    def test_html_escaping(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run("cafe called \"A<b>&Co\"", d, 3)
            pre = (Path(r["dir"]) / "preview.html").read_text()
            self.assertNotIn("<b>&Co", pre)
            design_engine.validate_jsx((Path(r["dir"]) / "App.jsx").read_text())

    def test_jsx_validator_catches_errors(self):
        with tempfile.TemporaryDirectory() as d:
            r = pipeline.run("gym", d, 1)
            jsx = (Path(r["dir"]) / "App.jsx").read_text()
        with self.assertRaises(ValueError):
            design_engine.validate_jsx(jsx.replace("</footer>", "", 1))
        with self.assertRaises(ValueError):
            design_engine.validate_jsx(jsx.replace("</section>", "</div>", 1))
        with self.assertRaises(ValueError):
            design_engine.validate_jsx(jsx.rstrip()[:-3])

    def test_empty_prompt(self):
        with self.assertRaises(ValueError):
            pipeline.run("   ")

    def test_only_stdlib_imports(self):
        std = sys.stdlib_module_names
        own = {'corecraft', 'test_corecraft'}
        files = list((ROOT / "corecraft").glob("*.py")) + [ROOT / "main.py"]
        for f in files:
            for node in ast.walk(ast.parse(f.read_text())):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    mods = [node.module.split(".")[0]]
                for m in mods:
                    if m in own:
                        continue
                    self.assertIn(m, std, "%s imports non-stdlib %s" % (f.name, m))


if __name__ == "__main__":
    unittest.main()
