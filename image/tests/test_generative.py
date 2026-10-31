import colorsys
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from pixelmath import creative, render                                  # noqa: E402
from pixelmath.compose import choose_mode, user_colors                  # noqa: E402
from pixelmath.palette import SCHEME_NAMES, gradient, harmonic_palette, scheme_palette  # noqa: E402
from pixelmath.raster import Noise                                      # noqa: E402
from pixelmath.tokenizer import parse, vectorize                        # noqa: E402
from test_api import Live                                               # noqa: E402

KINDS = {"mandelbrot": "fractal", "julia set": "fractal", "fractal": "fractal", "fractal tree": "lsystem", "l-system": "lsystem",
         "snowflake": "lsystem", "koch curve": "lsystem", "fern": "lsystem", "dragon curve": "lsystem", "sierpinski triangle": "lsystem",
         "flow field": "flow", "swirl": "flow", "marble": "texture", "plasma": "texture", "perlin noise": "texture"}


def hue(c):
    return colorsys.rgb_to_hsv(*c)[0] * 360.0


def hue_gap(a, b):
    d = abs(hue(a) - hue(b)) % 360
    return min(d, 360 - d)


class NoiseTests(unittest.TestCase):
    def test_perlin_is_smooth_bounded_and_seeded(self):
        n = Noise(5)
        vals = [n.fbm2(x * 0.05, y * 0.05) for x in range(60) for y in range(60)]
        self.assertTrue(all(0.0 <= v <= 1.0 for v in vals))
        self.assertGreater(max(vals) - min(vals), 0.3)                       # it really varies
        steps = [abs(n.perlin2(x * 0.02, 0.4) - n.perlin2((x + 1) * 0.02, 0.4)) for x in range(100)]
        self.assertLess(max(steps), 0.08)                                     # neighbouring samples are close: no digital noise
        self.assertEqual(Noise(5).fbm2(1.3, 2.1), n.fbm2(1.3, 2.1))
        self.assertNotEqual(Noise(6).fbm2(1.3, 2.1), n.fbm2(1.3, 2.1))


class PaletteTests(unittest.TestCase):
    def test_rules_hold(self):
        base = 0.1
        comp = scheme_palette(base, "complementary", 2)
        self.assertAlmostEqual(hue_gap(comp[0], comp[1]), 180, delta=3)
        tri = scheme_palette(base, "triadic", 3)
        self.assertAlmostEqual(hue_gap(tri[0], tri[1]), 120, delta=3)
        ana = scheme_palette(base, "analogous", 3)
        self.assertLess(max(hue_gap(ana[0], c) for c in ana), 40)
        mono = scheme_palette(base, "monochrome", 5)
        self.assertLess(max(hue_gap(mono[0], c) for c in mono), 3)
        self.assertEqual(len({round(colorsys.rgb_to_hsv(*c)[2], 2) for c in mono}), 5)         # many lightnesses
        for name in SCHEME_NAMES:
            for c in scheme_palette(0.9, name, 7):
                self.assertTrue(all(0.0 <= v <= 1.0 for v in c))

    def test_user_colour_anchors_the_palette_and_words_pick_the_rule(self):
        p = parse("red mandelbrot complementary")
        pal = harmonic_palette(p, vectorize("x"), 4)
        self.assertLess(hue_gap(pal[0], (0.86, 0.15, 0.15)), 8)
        self.assertAlmostEqual(hue_gap(pal[0], pal[1]), 180, delta=4)
        self.assertEqual(len(user_colors(parse("red circle triadic"))), 1 + 4)
        a, b = harmonic_palette(parse("abstract"), vectorize("abstract"), 5), harmonic_palette(parse("abstract"), vectorize("abstract"), 5)
        self.assertEqual(a, b)

    def test_gradient(self):
        pal = [(0, 0, 0), (1, 1, 1)]
        self.assertEqual(gradient(pal, 0.0, loop=False), (0, 0, 0))
        self.assertEqual(gradient(pal, 1.0, loop=False), (1, 1, 1))
        self.assertEqual(gradient(pal, 0.25), (0.5, 0.5, 0.5))


class ModeTests(unittest.TestCase):
    def test_routing(self):
        for prompt, mode in KINDS.items():
            self.assertEqual(choose_mode(parse(prompt)), mode, prompt)
        self.assertEqual(choose_mode(parse("snowy mountain")), "landscape")           # snow is still weather
        self.assertEqual(choose_mode(parse("golden mandala fractal")), "mandala")
        self.assertEqual(choose_mode(parse("red tree")), "landscape")

    def test_every_kind_draws_something_deterministic_and_seed_dependent(self):
        for prompt in KINDS:
            cv, _, mode = render(prompt, 80, 80, 1)
            data = cv.to_rgb_bytes()
            self.assertEqual(mode, KINDS[prompt])
            self.assertGreater(len(set(data[::7])), 25, prompt)                      # not flat
            self.assertEqual(data, render(prompt, 80, 80, 1)[0].to_rgb_bytes(), prompt)
        for prompt in ("mandelbrot", "fractal tree", "flow field", "marble"):
            self.assertNotEqual(render(prompt, 64, 64, 1)[0].to_rgb_bytes(), render(prompt, 64, 64, 2)[0].to_rgb_bytes(), prompt)

    def test_colour_rule_changes_the_picture_and_text_is_written(self):
        a = render("flow field", 64, 64, 1)[0].to_rgb_bytes()
        b = render("flow field triadic", 64, 64, 1)[0].to_rgb_bytes()
        self.assertNotEqual(a, b)
        plain = render("mandelbrot", 96, 96, 1)[0].to_rgb_bytes()
        titled = render('mandelbrot "SALE"', 96, 96, 1)[0].to_rgb_bytes()
        self.assertNotEqual(plain, titled)

    def test_odd_sizes(self):
        for prompt in ("mandelbrot", "fern", "flow field", "marble", "snowflake"):
            for size in ((16, 16), (97, 41), (41, 97)):
                cv, _, _ = render(prompt, size[0], size[1], 0)
                self.assertEqual(len(cv.px), size[0] * size[1] * 3)


class CreativeGenerativeTests(unittest.TestCase):
    def test_colour_rule_and_hue_are_genes_and_gates_hold(self):
        ctx = creative.Context("mandelbrot", 0.8, None, "auto", creative.default_chain())
        self.assertEqual(set(ctx.slot_pool), {"scheme", "hue"})
        self.assertNotIn("scheme", creative.Context("mandelbrot triadic", 0.8, None, "auto", creative.default_chain()).slot_pool)
        self.assertNotIn("hue", creative.Context("red fractal tree", 0.8, None, "auto", creative.default_chain()).slot_pool)
        made = creative.evolve("flow field", 0.8, population=5, generations=1, seed=2, final_size=64)
        self.assertEqual(made.mode, "flow")
        self.assertGreaterEqual(made.score, made.base_score - 1e-9)

    def test_explore_screens_many_ideas(self):
        made = creative.evolve("mandelbrot", 0.8, population=4, generations=1, seed=1, final_size=64, explore=40)
        self.assertTrue(any("screened" in n for n in made.notes))
        none = creative.evolve("mandelbrot", 0.8, population=4, generations=1, seed=1, final_size=64, explore=0)
        self.assertFalse(any("screened" in n for n in none.notes))

    def test_api_explore_and_generative_prompt(self):
        live = Live()
        try:
            st, _, j = live.json("POST", "/create", {"prompt": "fern", "size": 64, "temperature": 0.7, "population": 3,
                                                     "generations": 1, "explore": 20, "response": "base64"})
            self.assertEqual(st, 200)
            self.assertEqual(j["mode"], "lsystem")
            self.assertEqual(live.json("POST", "/create", {"prompt": "fern", "explore": 501})[0], 400)
            st, _, j = live.json("POST", "/generate", {"prompt": "julia fractal analogous", "size": 64, "response": "base64"})
            self.assertEqual((st, j["mode"]), (200, "fractal"))
        finally:
            live.close()


if __name__ == "__main__":
    unittest.main()
