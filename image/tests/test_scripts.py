import math
import os
import random
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath import devanagari, hanzi, render                      # noqa: E402
from pixelmath.compose import text_warnings                          # noqa: E402
from pixelmath.raster import Canvas                                  # noqa: E402
from pixelmath.text import clean, draw_text, measure                 # noqa: E402
from pixelmath.tokenizer import parse                                # noqa: E402

HINDI_WORDS = ["नमस्ते", "स्वागत", "चाय", "की", "दुकान", "मिठाई", "खाना", "होटल", "अस्पताल", "छूट", "ऑफर", "कृपया", "विद्यालय",
               "दूध", "बाज़ार", "ज्ञान", "क्षमा", "प्रेम", "श्री", "राष्ट्र", "धन्यवाद", "कर्म", "सूर्य", "पुस्तकालय", "भारत",
               "महिला", "बच्चे", "सेवा", "दवाइयाँ", "ज़िंदगी", "९९९"]


def ink(cv, thresh=0.5):
    return sum(1 for i in range(0, len(cv.px), 3) if cv.px[i] < thresh)


class DevanagariTests(unittest.TestCase):
    def test_specimen_words_lay_out_with_a_headline(self):
        for word in HINDI_WORDS:
            self.assertTrue(all(devanagari.supports(ch) for ch in word), word)
            width, strokes = devanagari.layout_word(word)
            self.assertGreater(width, 2.0, word)
            pts = [pt for st in strokes for pt in st]
            self.assertTrue(all(math.isfinite(x) and math.isfinite(y) for x, y in pts), word)
            self.assertTrue(all(-0.2 <= x <= width + 0.2 for x, _ in pts), word)
            self.assertTrue(all(-3.0 <= y <= 9.2 for _, y in pts), word)
            if not word.isdigit():
                head = [st for st in strokes if len(st) >= 2 and all(abs(y - 6.0) < 0.05 for _, y in st)]
                span = max((max(x for x, _ in st) - min(x for x, _ in st)) for st in head) if head else 0
                self.assertGreater(span, 0.75 * width, "no continuous headline in %s" % word)

    def test_layout_is_deterministic_and_never_crashes(self):
        chars = [chr(c) for c in range(0x0900, 0x0980) if devanagari.supports(chr(c))]
        self.assertGreater(len(chars), 80)
        rng = random.Random(3)
        for _ in range(1500):
            word = "".join(rng.choice(chars) for _ in range(rng.randint(1, 9)))
            a = devanagari.layout_word(word)
            self.assertEqual(a, devanagari.layout_word(word))

    def test_drawn_inside_text_and_mixed_with_latin(self):
        cv = Canvas(400, 100, (1, 1, 1))
        draw_text(cv, "SALE सेल 50%", 200, 50, 50, (0, 0, 0), 0.13, max_width=380)
        self.assertGreater(ink(cv), 600)
        self.assertEqual(clean("namaste नमस्ते"), "NAMASTE नमस्ते")
        self.assertGreater(measure("नमस्ते"), measure("NA"))
        for word in HINDI_WORDS:
            c = Canvas(300, 120, (1, 1, 1))
            draw_text(c, word, 150, 60, 60, (0, 0, 0), 0.13, max_width=280)
            self.assertGreater(ink(c), 200, word)


class HanziTests(unittest.TestCase):
    def test_every_character_is_inside_its_box_and_draws(self):
        self.assertGreaterEqual(len(hanzi.GLYPHS), 80)
        for ch, strokes in hanzi.GLYPHS.items():
            pts = [pt for st in strokes for pt in st]
            self.assertTrue(all(-0.45 <= x <= 6.45 and -0.45 <= y <= 6.45 for x, y in pts), ch)
            c = Canvas(90, 90, (1, 1, 1))
            draw_text(c, ch, 45, 45, 60, (0, 0, 0), 0.14)
            self.assertGreater(ink(c), 90, ch)

    def test_withheld_characters_are_dropped_not_drawn_wrong(self):
        for ch in hanzi.WITHHELD:
            self.assertFalse(hanzi.supports(ch), ch)
        self.assertEqual(clean("咖啡 COFFEE"), "咖啡 COFFEE")
        self.assertEqual(clean("欢迎光临"), "欢迎")                                            # 光/临 are not available


class WarningTests(unittest.TestCase):
    def test_honest_notes_for_approximate_scripts(self):
        self.assertEqual(text_warnings(parse('sign "BEAN"')), [])
        self.assertIn("Devanagari", text_warnings(parse('sign "चाय"'))[0])
        self.assertIn("Chinese", text_warnings(parse('sign "咖啡"'))[0])

    def test_cli_prints_the_note(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, "-m", "pixelmath", 'tea shop "चाय"', "-o", os.path.join(d, "o.png"), "--size", "64"],
                               cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertIn("note: Devanagari", r.stderr)


if __name__ == "__main__":
    unittest.main()
