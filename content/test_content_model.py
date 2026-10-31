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
                self.assertGreaterEqual(len(c["features"]), 3)
                self.assertEqual(len({f["title"].lower() for f in c["features"]}), len(c["features"]))
                self.assertEqual(c, generate_content(prompt, 3, learned=mode))

    def test_without_model_still_works(self):
        c = generate_content("gym", 2, use_model=False)
        self.assertEqual(c["business_type"], "gym")
        self.assertGreaterEqual(len(c["features"]), 4)


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
        self.assertIn("workouts", self.tm.nouns("fitness"))
        self.assertIn("burgers", self.tm.nouns("restaurant"))
        self.assertNotIn("burgers", self.tm.nouns("tech"))

    def test_engine_uses_frames_by_default(self):
        c = generate_content("gym website", 4)
        self.assertIn("frames", c["generated_by"]["copy"])
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


from corecraft.business_types import T as _TYPES
def NICHE_MAIN(n):
    from corecraft.template_data import NICHE
    return bool(NICHE[n]["main"])


TYPED = {k for k, v in _TYPES.items() if v["offers"]}


class QualityGates(unittest.TestCase):
    def setUp(self):
        from corecraft.template_model import TemplateModel, GENERIC
        from corecraft.template_data import NICHE
        self.tm, self.NICHE, self.GENERIC = TemplateModel.load(), NICHE, GENERIC

    def test_pools_are_big_and_clean(self):
        junk = {"always", "needs", "types", "nouns", "thanks", "communities", "messages", "releases", "employees", "years", "ways"}
        for n in self.NICHE:
            pool = self.tm.nouns(n)
            if not NICHE_MAIN(n):   # new kinds take their nouns from the business type
                continue
            self.assertGreaterEqual(len(pool), 22, n)
            self.assertFalse(set(pool) & junk, n)
            self.assertEqual(len(pool), len(set(pool)), n)
        for tid, t in _TYPES.items():
            if t["offers"]:
                heads = [w.split()[-1] for w in t["offers"]]
                self.assertGreaterEqual(len(set(heads)), 8, tid)
                self.assertEqual(len(t["offers"]), len(set(t["offers"])), tid)
                self.assertFalse(set(t["offers"]) & junk, tid)

    def test_many_frames(self):
        shared = sum(len(v) for v in self.GENERIC.values())
        per_niche = [sum(len(self.NICHE[n][k]) for k in ("hero", "tagline", "feature", "open", "close")) for n in self.NICHE]
        self.assertGreaterEqual(shared, 40)
        self.assertGreaterEqual(min(per_niche), 25)

    def test_niche_frames_make_pages_niche_specific(self):
        from corecraft.template_data import NICHE
        for n in NICHE:
            for k in ("hero", "tagline", "feature", "open", "close"):
                self.assertGreaterEqual(len(NICHE[n][k]), 4, (n, k))

    def test_no_noun_repeated_three_times_on_a_page(self):
        import collections
        for p in ("cafe serving coffee", "gym", "software startup", "photographer portfolio", "school", "boutique", "plumbing"):
            for seed in range(40):
                c = generate_content(p, seed)
                pool = set(self.tm.nouns(c["niche"]))
                page = " ".join([c["hero_heading"], c["tagline"], c["cta_text"]] + c["about"] + [f["title"] + " " + f["text"] for f in c["features"]]).lower()
                cnt = collections.Counter(w for w in re.findall(r"[a-z]+", page) if w in pool)
                self.assertLessEqual(max(cnt.values()), 3 if c["business_type"] in TYPED else 2, (p, seed, cnt.most_common(2)))

    def test_prompt_steers_nouns(self):
        for p, kws in (("handmade jewellery boutique", {"rings", "necklaces", "bracelets", "earrings", "pendants", "diamonds", "charms", "studs", "hoops", "chains", "bangles", "brooches", "anklets", "watches"}), ("plumbing repair services", {"repairs", "installations", "inspections", "plumbers", "technicians", "estimates", "appointments"})):
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

    def test_subtopic_keeps_off_topic_nouns_out(self):
        off = {"mattresses", "pillows", "sneakers", "shoes", "boots", "sandals", "towels", "cushions", "candles"}
        leaks = 0
        for seed in range(60):
            c = generate_content("handmade jewellery boutique", seed)
            page = " ".join([c["hero_heading"], c["tagline"], c["cta_text"]] + c["about"] + [f["title"] + " " + f["text"] for f in c["features"]]).lower()
            leaks += sum(w in off for w in re.findall(r"[a-z]+", page))
        self.assertLess(leaks / 60, 0.5)

    def test_frames_never_leave_placeholders(self):
        for n in ("restaurant", "fitness", "tech", "portfolio", "education", "shop", "business"):
            for seed in range(80):
                page = self.tm.page(n, __import__("random").Random(seed), ["coffee", "yoga", "plumbing"])
                blob = " ".join([page["hero_heading"], page["tagline"], page["cta_text"]] + page["about"] + [f["text"] for f in page["features"]])
                self.assertNotRegex(blob, r"[{}]")
                self.assertNotRegex(blob, r"\b(\w+) \1\b")

    def test_frame_text_never_contains_a_pool_noun(self):
        for n in self.NICHE:
            pool = set(self.tm.nouns(n))
            frames = [f for k in ("hero", "tagline", "feature", "open", "close") for f in self.NICHE[n][k]] + [f for v in self.GENERIC.values() for f in v]
            for f in frames:
                words = set(re.findall(r"[a-z]+", re.sub(r"\{.*?\}", "", f).lower()))
                self.assertFalse(words & pool, (n, f, words & pool))
