import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath import render                                           # noqa: E402
from pixelmath.raster import Canvas                                    # noqa: E402
from pixelmath.text import GLYPHS, clean, draw_headline, draw_text, measure   # noqa: E402
from pixelmath.tokenizer import extract_texts, parse                   # noqa: E402


def lit(cv, box, thresh=0.5):
    x0, y0, x1, y1 = [int(v) for v in box]
    n = 0
    for y in range(max(0, y0), min(cv.h, y1)):
        for x in range(max(0, x0), min(cv.w, x1)):
            i = (y * cv.w + x) * 3
            if cv.px[i] < thresh:
                n += 1
    return n


class FontTests(unittest.TestCase):
    def test_every_glyph_draws_something_inside_its_cell(self):
        for ch in GLYPHS:
            if ch == " ":
                continue
            cv = Canvas(100, 100, (1, 1, 1))
            box = draw_text(cv, ch, 50, 50, 60, (0, 0, 0))
            self.assertIsNotNone(box, ch)
            self.assertGreater(lit(cv, (0, 0, 100, 100)), 12, "glyph %r is invisible" % ch)
            self.assertGreaterEqual(box[0], 0, ch)
            self.assertLessEqual(box[2], 100, ch)

    def test_clean_measure_and_shrink_to_fit(self):
        self.assertEqual(clean("bean & brew"), "BEAN & BREW")
        self.assertEqual(clean("  a   b  "), "A B")
        self.assertEqual(clean("namaste مرحبا สวัสดี"), "NAMASTE")      # unsupported scripts (Arabic, Thai) are dropped
        self.assertEqual(clean("x" * 100), "X" * 40)
        self.assertGreater(measure("WIDE"), measure("I"))
        cv = Canvas(300, 80, (1, 1, 1))
        box = draw_text(cv, "A VERY LONG HEADLINE THAT WOULD NOT FIT", 150, 40, 60, (0, 0, 0), max_width=280)
        self.assertLessEqual(box[2] - box[0], 290)
        self.assertGreater(lit(cv, (0, 0, 300, 80)), 200)

    def test_headline_picks_contrasting_colour(self):
        dark, light = Canvas(200, 60, (0.05, 0.05, 0.1)), Canvas(200, 60, (0.95, 0.95, 0.9))
        for cv in (dark, light):
            draw_headline(cv, "HELLO", 100, 30, 36, 180)
        centre = lambda cv: [cv.px[(30 * 200 + x) * 3] for x in range(60, 140)]            # noqa: E731
        self.assertGreater(max(centre(dark)), 0.8)                                       # light text on a dark ground
        self.assertLess(min(centre(light)), 0.3)                                         # dark text on a light ground


class QuotedTextTests(unittest.TestCase):
    def test_extraction(self):
        self.assertEqual(extract_texts('coffee shop sign "bean & brew"')[1], ["BEAN & BREW"])
        self.assertEqual(extract_texts("logo 'acme' on white")[1], ["ACME"])
        self.assertEqual(extract_texts("kids' park and dog's bowl")[1], [])                # apostrophes are not quotes
        self.assertEqual(extract_texts('poster "SUMMER SALE" "50% OFF"')[1], ["SUMMER SALE", "50% OFF"])
        self.assertEqual(extract_texts('“CURLY QUOTES”')[1], ["CURLY QUOTES"])
        self.assertEqual(extract_texts('"مرحبا"')[1], [])
        p = parse('red car "FAST CARS"')
        self.assertEqual([e.name for e in p.entities], ["car"])                           # words inside quotes never summon props
        self.assertEqual(p.texts, ["FAST CARS"])

    def test_text_goes_where_it_belongs(self):
        w, h = 200, 120
        plain = render("coffee shop", w, h)[0]
        signed, parsed, _ = render('coffee shop "BEAN & BREW"', w, h)
        self.assertTrue(signed.sign_used)                                               # written on the shop sign
        self.assertFalse(getattr(plain, "sign_used", False))
        self.assertNotEqual(plain.to_rgb_bytes(), signed.to_rgb_bytes())
        cv, _, _ = render('red background poster "HELLO WORLD"', w, h)
        self.assertFalse(getattr(cv, "sign_used", False))                                # no sign: becomes a headline
        base = render("red background poster", w, h)[0]
        self.assertNotEqual(cv.to_rgb_bytes(), base.to_rgb_bytes())
        def top(c):
            px = c.to_rgb_bytes()
            return sum(px[(y * w + x) * 3 + 1] for y in range(10, 40) for x in range(w))
        self.assertGreater(top(cv), top(base))                                           # white-ish headline raised the green channel
        logo = render('blue circle logo "AB"', w, h)[0]
        nolabel = render("blue circle logo", w, h)[0]
        def mid(c):
            px = c.to_rgb_bytes()
            return [px[((h // 2) * w + x) * 3] for x in range(w // 2 - 20, w // 2 + 20)]
        self.assertGreater(max(mid(logo)), max(mid(nolabel)) + 100)                      # white letters on the blue circle

    def test_random_text_never_crashes(self):
        rng = random.Random(8)
        alphabet = "abcXYZ 0189.,!?&%+:'/()$₹न你 -"
        for _ in range(12):
            t = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 90)))
            for prompt in ('shop "%s"' % t, 'blue circle "%s"' % t, 'poster "%s" "%s"' % (t, t[:5])):
                cv = render(prompt, 64, 48)[0]
                self.assertEqual(len(cv.to_rgb_bytes()), 64 * 48 * 3)


if __name__ == "__main__":
    unittest.main()
