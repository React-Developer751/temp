import os
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from pixelmath import creative, render                       # noqa: E402
from pixelmath.compose import choose_mode                    # noqa: E402
from pixelmath.tokenizer import parse                        # noqa: E402
from test_api import Live                                    # noqa: E402


class SamplingTests(unittest.TestCase):
    def test_temperature_zero_is_the_best_and_higher_explores_the_top_three(self):
        scored = [("a", 1.0), ("b", 0.9), ("c", 0.8), ("d", 0.1)]
        rng = random.Random(1)
        self.assertEqual({creative.top_k_sample(rng, scored, 0.0) for _ in range(30)}, {"a"})
        picks = {creative.top_k_sample(rng, scored, 0.9) for _ in range(300)}
        self.assertEqual(picks, {"a", "b", "c"})                    # never the 4th, but not only the first either
        self.assertIsNone(creative.top_k_sample(rng, [], 0.5))


class ChainTests(unittest.TestCase):
    def test_builtin_links_and_own_captions(self):
        chain = creative.Chain.builtin()
        self.assertGreater(chain.affinity(["laptop", "coffee_cup"]), chain.affinity(["laptop", "tractor"]))
        rng = random.Random(0)
        self.assertEqual(chain.suggest(rng, ["dog"], 0.0), chain.suggest(rng, ["dog"], 0.0))
        self.assertNotIn("dog", [chain.suggest(rng, ["dog"], 0.9) for _ in range(20)])
        own = creative.Chain.builtin()
        before = own.affinity(["tractor", "lamp"])
        own.learn_captions(["tractor beside a lamp"] * 4)
        self.assertGreater(own.affinity(["tractor", "lamp"]), before)

    def test_every_suggested_word_parses_back_to_its_prop(self):
        for name in ("cow", "plant", "coffee_cup", "firetruck", "dentalchair", "laptop"):
            word = creative.prop_word(name)
            self.assertTrue(word and any(e.name == name for e in parse(word).entities), name)


class CriticTests(unittest.TestCase):
    def verdict(self, prompt, genome):
        ctx = creative.Context(prompt, 0.8, None, "auto", creative.default_chain())
        cv, parsed, mode = render(genome.prompt(), 96, 96, genome.seed)
        return creative.critique(ctx, genome, cv, parsed, mode, [])[0]

    def test_plain_render_passes_and_scores(self):
        v = self.verdict("laptop and coffee cup", creative.Genome("laptop and coffee cup"))
        self.assertTrue(v.ok, v.reasons)
        self.assertTrue(0.0 < v.score <= 1.2)

    def test_variation_that_changes_the_picture_type_is_rejected(self):
        g = creative.Genome("laptop and coffee cup", ("tractor",))
        v = self.verdict("laptop and coffee cup", g)
        self.assertFalse(v.ok)
        self.assertTrue(any("picture type" in r for r in v.reasons), v.reasons)

    def test_variation_that_recolours_the_request_is_rejected(self):
        g = creative.Genome("red circle", (), (("palette", "in gold and teal tones"),))
        ctx = creative.Context("red circle", 0.8, None, "auto", creative.default_chain())
        self.assertEqual(ctx.slot_pool, {})                          # explicit colours: no palette ideas at all
        cv, parsed, mode = render("blue circle", 96, 96, 0)                 # a variation that turned the red circle blue
        v = creative.critique(ctx, g, cv, parsed, mode, [])[0]
        self.assertFalse(v.ok)
        self.assertTrue(any("circle" in r for r in v.reasons), v.reasons)

    def test_blank_image_is_rejected(self):
        ctx = creative.Context("tractor", 0.8, None, "auto", creative.default_chain())
        cv, parsed, mode = render("tractor", 64, 64, 0)
        cv.px = [0.5] * len(cv.px)
        v = creative.critique(ctx, creative.Genome("tractor"), cv, parsed, mode, [])[0]
        self.assertFalse(v.ok)
        self.assertTrue(any("blank" in r for r in v.reasons))


class EvolveTests(unittest.TestCase):
    def test_temperature_zero_equals_the_plain_render(self):
        made = creative.evolve("laptop and coffee cup", 0.0, seed=4, final_size=96)
        cv, _, _ = render("laptop and coffee cup", 96, 96, 4)
        self.assertEqual(made.canvas.to_rgb_bytes(), cv.to_rgb_bytes())
        self.assertEqual(made.prompt, "laptop and coffee cup")

    def test_creative_result_keeps_the_request_and_never_scores_below_the_plain_render(self):
        base = "red tractor and dog"
        made = creative.evolve(base, 0.9, population=6, generations=2, seed=2, final_size=96)
        want = {(e.name, e.color) for e in parse(base).entities}
        got = {(e.name, e.color) for e in parse(made.prompt).entities}
        self.assertTrue(want <= got, (want, got))
        self.assertGreaterEqual(made.score, made.base_score - 1e-9)
        self.assertEqual(choose_mode(parse(made.prompt)), "landscape")
        self.assertTrue(any("thinking" in n or "tried" in n or "candidates" in n for n in made.notes))
        self.assertIn("generations", made.to_dict())

    def test_same_arguments_same_result_and_seeds_give_variety(self):
        a = creative.evolve("laptop", 0.8, population=5, generations=2, seed=7, final_size=64)
        b = creative.evolve("laptop", 0.8, population=5, generations=2, seed=7, final_size=64)
        self.assertEqual((a.prompt, a.seed, a.score), (b.prompt, b.seed, b.score))
        results = {(creative.evolve("laptop", 0.8, population=5, generations=1, seed=s, final_size=48).prompt) for s in range(5)}
        self.assertGreaterEqual(len(results), 3)

    def test_creative_picture_reproducible_through_a_plain_render(self):
        made = creative.evolve("cake", 0.8, population=5, generations=1, seed=3, final_size=80)
        cv, _, _ = render(made.prompt, 80, 80, made.seed)
        self.assertEqual(made.canvas.to_rgb_bytes(), cv.to_rgb_bytes())

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            creative.evolve("cake", 1.5)
        with self.assertRaises(ValueError):
            creative.evolve("   ", 0.5)

    def test_shapes_only_vary_the_layout_seed(self):
        made = creative.evolve("red circle and blue square", 0.8, population=5, generations=1, seed=1, final_size=64)
        self.assertEqual(made.prompt, "red circle and blue square")

    def test_time_budget_stops_the_search(self):
        made = creative.evolve("cake", 0.8, population=16, generations=8, seed=1, final_size=64, max_seconds=0.01)
        self.assertLess(made.evaluated, 16 * 9)


class ImagineTests(unittest.TestCase):
    def test_mashup_has_two_ideas_is_judged_and_reproducible(self):
        made, log = creative.imagine(0.9, seed=3, attempts=10, final_size=80, population=4, generations=1)
        self.assertGreaterEqual(len([e for e in parse(made.prompt).entities]), 2)
        self.assertTrue(log and log[-1]["accepted"])
        again, _ = creative.imagine(0.9, seed=3, attempts=10, final_size=80, population=4, generations=1)
        self.assertEqual(made.prompt, again.prompt)

    def test_anchor_is_kept(self):
        made, _ = creative.imagine(0.9, seed=1, attempts=10, final_size=64, anchor="cat", population=3, generations=1)
        self.assertIn("cat", [e.name for e in parse(made.prompt).entities])

    def test_cat_in_space_now_draws_the_cat(self):
        cv, parsed, mode = render("cat in space", 96, 96, 0)
        self.assertIn("cat", getattr(cv, "drawn", []))


class SurfaceTests(unittest.TestCase):
    def test_cli_creative_and_imagine(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.png")
            r = subprocess.run([sys.executable, "-m", "pixelmath", "cake", "--temperature", "0.7", "--population", "4", "--generations", "1",
                                "--size", "64", "-o", out], cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("thinking:", r.stdout)
            self.assertTrue(os.path.getsize(out) > 200)
            r = subprocess.run([sys.executable, "-m", "pixelmath", "--imagine", "--seed", "2", "--size", "64", "-o", out,
                                "--population", "3", "--generations", "1"], cwd=ROOT, capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            bad = subprocess.run([sys.executable, "-m", "pixelmath", "cake", "--temperature", "2", "-o", out], cwd=ROOT,
                                 capture_output=True, text=True, timeout=60)
            self.assertNotEqual(bad.returncode, 0)

    def test_api_create_and_imagine(self):
        live = Live()
        try:
            st, hdr, data = live.json("POST", "/create", {"prompt": "laptop", "temperature": 0.7, "population": 4, "generations": 1,
                                                         "size": 96})
            self.assertEqual(st, 200)
            self.assertEqual(hdr["content-type"], "image/png")
            self.assertTrue(data.startswith(b"\x89PNG"))
            self.assertIn("x-pixelmath-prompt", hdr)
            st, _, j = live.json("POST", "/create", {"prompt": "cake", "temperature": 0.8, "population": 4, "generations": 1,
                                                     "size": 64, "response": "base64", "alternatives": 2})
            self.assertEqual(st, 200)
            self.assertIn("thinking", j["creation"])
            self.assertLessEqual(len(j["creation"]["alternatives"]), 2)
            st, _, j = live.json("POST", "/imagine", {"anchor": "dog", "size": 64, "response": "base64", "population": 3,
                                                      "generations": 1, "attempts": 8})
            self.assertEqual(st, 200)
            self.assertIn("dog", j["creation"]["prompt_used"])
            for bad in ({"prompt": "x", "temperature": 3}, {"prompt": "x", "population": 99}, {"prompt": "x", "nope": 1}, {}):
                st, _, e = live.json("POST", "/create", bad)
                self.assertEqual(st, 400, bad)
            st, _, e = live.json("POST", "/imagine", {"attempts": 0})
            self.assertEqual(st, 400)
        finally:
            live.close()


if __name__ == "__main__":
    unittest.main()
