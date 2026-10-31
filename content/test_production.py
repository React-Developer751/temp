"""Run-time safety: whatever a person types, the engine returns a valid page or a clear error, never a traceback."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

os.environ.setdefault("CORECRAFT_NO_PHOTOS", "1")        # content tests do not need pictures (test_photos.py does)
from corecraft import pipeline
from corecraft.content_engine import clean_text, generate_content
from corecraft.validators import leaves_of

ROOT = Path(__file__).parent
HOSTILE = ["a", "x" * 5000, "😀😀😀", "<script>alert(1)</script> bakery in Delhi", "bakery\nin\nDelhi\n\ncakes", "cakes {{name}} ${x} bakery Delhi", "a " * 3000,
           "\x00\x01 bakery ‮ Delhi", "'; DROP TABLE users;--", "123456", "Restaurant " * 300, "<b>x</b> bakery {a} in Delhi", "मुझे ज्योतिषी चाहिए"]


class Balanced(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], 0

    def handle_starttag(self, tag, attrs):
        if tag not in ("meta", "link", "br", "img", "input", "hr", "source"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors += 1


class Hostile(unittest.TestCase):
    def test_every_input_gives_a_valid_page(self):
        for p in HOSTILE:
            c = generate_content(p)
            self.assertTrue(c["hero_heading"] and len(c["hero_heading"]) <= 80, p[:20])
            blob = " ".join(t for _, t, _ in leaves_of(c))
            self.assertNotRegex(blob, r"[{}<>]", p[:20])

    def test_empty_prompt_is_a_clear_error(self):
        for p in ("", "   ", "\n\n", None):
            with self.assertRaises(ValueError):
                generate_content(p)

    def test_newlines_are_read_as_a_list(self):
        c = generate_content("dental clinic\nbraces\nimplants\nPune")
        self.assertEqual(c["location"], "Pune")
        self.assertEqual(c["generated_by"]["items_from_prompt"], ["braces", "implants"])
        self.assertEqual(generate_content("bakery\nin\nDelhi\n\ncakes")["location"], "Delhi")

    def test_clean_text(self):
        self.assertEqual(clean_text("<b>x</b> {y}"), "x y")
        self.assertLessEqual(len(clean_text("word " * 2000)), 1500)

    def test_wrong_shaped_facts_do_not_crash(self):
        c = generate_content("x cafe", facts={"prices": "oops", "team": 5, "services": "espresso, cake", "name": ["a"]})
        self.assertEqual(c["generated_by"]["items_from_prompt"], ["espresso", "cake"])
        self.assertTrue(generate_content("cafe", facts=["not", "a", "dict"]))

    def test_same_input_same_page(self):
        p = "dental clinic in Pune, braces, implants"
        self.assertEqual(generate_content(p, 1), generate_content(p, 1))


class Site(unittest.TestCase):
    def test_hostile_prompts_build_clean_sites(self):
        with tempfile.TemporaryDirectory() as d:
            for i, p in enumerate(HOSTILE[3:6] + ["'\"quote\" cafe & bar in Pune, \"Mom's\" pizza"]):
                r = pipeline.run(p, d + "/%d" % i)
                page = (Path(r["dir"]) / "preview.html").read_text(encoding="utf-8")
                jsx = (Path(r["dir"]) / "App.jsx").read_text(encoding="utf-8")
                b = Balanced()
                b.feed(page)
                self.assertEqual((b.errors, b.stack), (0, []), p)
                self.assertNotIn("<script>alert", page + jsx)
                self.assertEqual((jsx.count("{"), jsx.count("(")), (jsx.count("}"), jsx.count(")")), p)
                json.loads((Path(r["dir"]) / "content.json").read_text(encoding="utf-8"))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "main.py"), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir())

    def test_builds_a_site_from_any_folder(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("dental clinic in Pune, braces, implants", "--out", d, "--seed", "1")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(list(Path(d).glob("*/preview.html")))

    def test_errors_are_one_clear_line(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text("{bad")
            arr = Path(d) / "arr.json"
            arr.write_text("[1]")
            for args, word in ((("",), "error"), (("cafe", "--facts", d + "/none.json"), "cannot read"), (("cafe", "--facts", str(bad)), "not valid JSON"), (("cafe", "--facts", str(arr)), "JSON object")):
                r = self.run_cli(*args)
                self.assertNotEqual(r.returncode, 0)
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn(word, r.stderr)


if __name__ == "__main__":
    unittest.main()
