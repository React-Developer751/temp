"""Copy that belongs to another kind of business must not leak: a tattoo studio is not a salon and does not talk about weddings, a spa is not a salon."""
import os
import re
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("CORECRAFT_NO_PHOTOS", "1")
from corecraft import pipeline


def page_text(prompt, seed=3):
    with tempfile.TemporaryDirectory() as d:
        pipeline.run(prompt, d, seed)
        html = next(Path(d).iterdir()).joinpath("preview.html").read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


class BeautyVoices(unittest.TestCase):
    def test_tattoo_studio_does_not_sound_like_a_salon(self):
        for seed in (1, 3, 7):
            t = page_text("tattoo studio in Mumbai", seed)
            for word in ("salon", "wedding", "bridal", "party", "the look and the occasion"):
                self.assertNotIn(word, t.lower(), "%s (seed %d)" % (word, seed))
            self.assertIn("Call the studio", t)

    def test_spa_calls_itself_a_spa(self):
        t = page_text("spa and massage centre in Goa")
        self.assertNotIn("salon", t.lower())
        self.assertIn("Call the spa", t)

    def test_salon_keeps_its_own_voice(self):
        self.assertIn("Call the salon", page_text("hair salon in Pune"))


if __name__ == "__main__":
    unittest.main()
