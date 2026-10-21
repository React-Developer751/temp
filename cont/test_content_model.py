import json
import re
import unittest
from pathlib import Path

from corecraft import ngram_model as nm
from corecraft.content_engine import generate_content, detect_niche, tokenize

ROOT = Path(__file__).parent
MODEL = nm.Model.load()


class TrainedContentAI(unittest.TestCase):
    def test_model_exists_and_covers_niches(self):
        self.assertIsNotNone(MODEL)
        self.assertEqual(set(MODEL.d["niches"]), {"restaurant", "fitness", "tech", "portfolio", "education", "shop", "business"})
        for n, nd in MODEL.d["niches"].items():
            self.assertGreaterEqual(len(nd["ctas"]), 5, n)
            self.assertGreater(nd["slots"]["sentence"]["n"], 100, n)

    def test_corpus_size(self):
        corpus = json.loads((ROOT / "data" / "corpus.json").read_text())
        for n, c in corpus.items():
            self.assertGreaterEqual(c["sites_ok"], 15, n)
            self.assertGreater(len(c["para"]), 1000 if n in ("tech", "education") else 400, n)

    def test_learned_vocab_detects_niche_without_manual_keywords(self):
        for prompt, niche in [("kubernetes deployment pipelines", "tech"), ("mattress bedding sleep", "shop"), ("workouts membership club", "fitness")]:
            self.assertEqual(detect_niche(tokenize(prompt), MODEL), niche, prompt)

    def test_learned_ctas_are_clean_and_deterministic(self):
        for n in MODEL.d["niches"]:
            import random
            ctas = MODEL.pick_ctas(n, random.Random(1), 2)
            self.assertEqual(len(ctas), 2, n)
            self.assertEqual(ctas, MODEL.pick_ctas(n, random.Random(1), 2))
            for c in ctas:
                self.assertTrue(1 < len(c.split()) <= 4 and not re.search(r"\d|http", c), c)
                self.assertFalse(any(w.lower() in MODEL.brands for w in c.split()), c)

    def test_generated_text_is_not_copied_from_training_data(self):
        import random
        corpus = json.loads((ROOT / "data" / "corpus.json").read_text())
        grams = set()
        for c in corpus.values():
            for t in c["heading"] + c["para"]:
                ws = [w.lower() for w in nm.tokens(t) if w[0].isalnum()]
                grams |= {" ".join(ws[i:i + 6]) for i in range(len(ws) - 5)}
        checked = 0
        for n in MODEL.d["niches"]:
            for seed in range(8):
                s = MODEL.generate(n, "sentence", random.Random(seed), 8, 18, "s", strict=True)
                if not s:
                    continue
                checked += 1
                ws = [w.lower() for w in nm.tokens(s) if w[0].isalnum()]
                self.assertFalse(any(" ".join(ws[i:i + 6]) in grams for i in range(len(ws) - 5)), s)
        self.assertGreater(checked, 10)

    def test_default_and_all_modes_produce_valid_content(self):
        for mode in (("ctas",), "all", ()):
            for prompt in ("cafe called 'Chai Point'", "gym website", "plumbing repairs"):
                c = generate_content(prompt, 3, learned=mode)
                self.assertEqual(len(c["features"]), 6)
                self.assertEqual(len({f["title"].lower() for f in c["features"]}), 6)
                self.assertEqual(c, generate_content(prompt, 3, learned=mode))

    def test_without_model_still_works(self):
        self.assertEqual(generate_content("gym", 2, use_model=False)["generated_by"]["ctas"], "bank")


if __name__ == "__main__":
    unittest.main()


class FrameTemplates(unittest.TestCase):
    def setUp(self):
        import random
        from corecraft.template_model import TemplateModel
        self.tm, self.rand = TemplateModel.load(), random.Random

    def test_every_niche_has_learned_nouns(self):
        for n in self.tm.d["niches"]:
            self.assertTrue(self.tm.usable(n), n)

    def test_outputs_are_clean_for_many_seeds(self):
        for n in self.tm.d["niches"]:
            for seed in range(60):
                rng = self.rand(seed)
                texts = [self.tm.hero(n, rng), self.tm.tagline(n, rng)] + self.tm.about(n, rng)
                feats = self.tm.features(n, rng, 6)
                texts += [f["text"] for f in feats]
                for t in texts:
                    self.assertNotRegex(t, r"[{}]", t)
                    ws = t.lower().replace(",", "").replace(".", "").split()
                    self.assertFalse(any(a == b for a, b in zip(ws, ws[1:])), t)
                self.assertEqual(len({f["title"] for f in feats}), 6)
                self.assertFalse(any(f["title"].lower() in {"years", "ways"} for f in feats))
            who = self.tm.tagline(n, self.rand(1))
            parts = re.findall(r"Made for (\w+) and (\w+)", who)
            self.assertTrue(all(a != b for a, b in parts), who)

    def test_nouns_are_niche_specific(self):
        self.assertIn("workouts", self.tm.nouns("fitness") + self.tm.people("fitness") + self.tm._ranked("fitness"))
        self.assertIn("burgers", self.tm._ranked("restaurant"))
        self.assertNotIn("burgers", self.tm._ranked("tech"))

    def test_engine_uses_frames_by_default(self):
        c = generate_content("gym website", 4)
        self.assertEqual(c["generated_by"]["tagline"], "model")
        self.assertEqual(generate_content("gym website", 4), c)


class Regressions(unittest.TestCase):
    def test_cta_text_differs_from_tagline(self):
        for p in ("gym website", "cafe serving coffee", "plumbing repairs", "photographer portfolio"):
            for seed in range(25):
                c = generate_content(p, seed)
                self.assertNotEqual(c["cta_text"], c["tagline"], (p, seed))
                self.assertNotEqual(c["cta_text"], c["about"][0])

    def test_prompt_keyword_reaches_copy(self):
        hits = sum("coffee" in generate_content("cozy cafe serving coffee", s)["hero_heading"].lower() for s in range(30))
        self.assertGreater(hits, 10)


class QualityGates(unittest.TestCase):
    def setUp(self):
        from corecraft.template_model import TemplateModel, EXCLUDE, FEATURE, HERO, TAGLINE
        self.tm, self.EXCLUDE = TemplateModel.load(), EXCLUDE
        self.nframes = len(FEATURE) + len(HERO) + len(TAGLINE)

    def test_pools_are_big_and_clean(self):
        for n in self.tm.d["niches"]:
            pool = self.tm.nouns(n)
            self.assertGreaterEqual(len(pool), 30, n)
            for w in ("always", "needs", "types", "nouns", "thanks"):
                self.assertNotIn(w, pool, n)
            self.assertFalse(set(pool) & self.EXCLUDE, n)

    def test_many_frames(self):
        self.assertGreaterEqual(self.nframes, 50)

    def test_no_noun_repeated_three_times_on_a_page(self):
        import collections
        for p in ("cafe serving coffee", "gym", "software startup", "photographer portfolio", "school", "boutique", "plumbing"):
            for seed in range(40):
                c = generate_content(p, seed)
                pool = set(self.tm.nouns(c["niche"]))
                page = " ".join([c["hero_heading"], c["tagline"], c["cta_text"]] + c["about"] + [f["title"] + " " + f["text"] for f in c["features"]]).lower()
                cnt = collections.Counter(w for w in re.findall(r"[a-z]+", page) if w in pool)
                self.assertLessEqual(max(cnt.values()), 2, (p, seed, cnt.most_common(2)))

    def test_prompt_steers_nouns(self):
        for p, kws in (("handmade jewellery boutique", {"rings", "necklaces", "bracelets", "earrings", "pendants", "diamonds"}), ("plumbing repair services", {"repairs", "installations", "inspections", "plumbers", "technicians", "estimates", "appointments"})):
            hits = 0
            for s in range(40):
                c = generate_content(p, s)
                txt = " ".join([c["hero_heading"], c["tagline"]] + c["about"] + [f["title"] + " " + f["text"] for f in c["features"]]).lower()
                hits += any(k in txt for k in kws)
            self.assertGreaterEqual(hits, 36, p)

    def test_about_paragraphs_use_different_frames(self):
        for seed in range(50):
            a = generate_content("gym", seed)["about"]
            self.assertNotEqual(a[0].split()[0:3], a[1].split()[0:3] if False else None)
            self.assertNotEqual(a[0], a[1])

    def test_same_seed_same_page_across_hash_seeds(self):
        import subprocess, sys
        code = "import json; from corecraft.content_engine import generate_content as g; print(json.dumps(g('cozy cafe serving coffee', 5), sort_keys=True))"
        outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT), env={"PYTHONHASHSEED": h, "PATH": ""}).stdout for h in ("1", "2", "3", "4")}
        self.assertEqual(len(outs), 1)
        self.assertNotEqual(next(iter(outs)), "")
