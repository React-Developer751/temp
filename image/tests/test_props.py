import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from pixelmath import props, render, tokenizer as T                      # noqa: E402
from pixelmath.compose import choose_mode                                # noqa: E402
from pixelmath.learn import LearnedModel, make_sample, train_model       # noqa: E402
from pixelmath.neural import Style                                       # noqa: E402
from pixelmath.painter import Painter                                    # noqa: E402
from pixelmath.props import REGISTRY, draw_prop                          # noqa: E402
from pixelmath.raster import Noise                                       # noqa: E402

BG = (0.5, 0.5, 0.5)


def draw_alone(name, color=None, size=100, canvas=300, seed=1):
    p = Painter(canvas, canvas, random.Random(seed), Noise(seed), Style(0, 1, 1, 0.01, 0.5, 1, 0.5, 0))
    p.cv.px = list(BG) * (canvas * canvas)
    draw_prop(p, name, canvas / 2, canvas * 0.8, size, color)
    px, xs, ys, cols = p.cv.px, [], [], []
    for y in range(canvas):
        for x in range(canvas):
            i = (y * canvas + x) * 3
            if abs(px[i] - BG[0]) + abs(px[i + 1] - BG[1]) + abs(px[i + 2] - BG[2]) > 0.22:      # solid shapes, not soft glows
                xs.append(x)
                ys.append(y)
                cols.append((px[i], px[i + 1], px[i + 2]))
    return xs, ys, cols, p.cv.px


class PropTests(unittest.TestCase):
    def test_registry_is_large_and_covers_the_business_verticals(self):
        self.assertGreaterEqual(len(REGISTRY), 110)
        cats = {p.category for p in REGISTRY.values()}
        for need in ("food", "retail", "tech", "office", "people", "vehicles", "home", "buildings", "wellness", "web", "travel", "events",
                     "pets", "farm", "machinery", "tools", "playground", "sports"):
            self.assertIn(need, cats)

    def test_every_prop_draws_within_its_declared_box(self):
        for name, pr in REGISTRY.items():
            xs, ys, _, _ = draw_alone(name)
            self.assertTrue(len(xs) > 200, "%s drew almost nothing" % name)
            width, height = max(xs) - min(xs), max(ys) - min(ys)
            self.assertLessEqual(width, pr.aspect * 100 * 1.45 + 12, "%s is wider than declared (%d px)" % (name, width))
            self.assertLessEqual(height, 100 * 1.45 + 12, "%s is taller than declared (%d px)" % (name, height))
            centre = (max(xs) + min(xs)) / 2.0
            self.assertLess(abs(centre - 150), 0.45 * 100 * max(1.0, pr.aspect), "%s is not centred on its base" % name)
            self.assertLessEqual(max(ys), 300 * 0.8 + 18, "%s hangs below its base line" % name)

    def test_props_are_deterministic(self):
        for name in ("person", "team", "plant", "pizza", "car"):
            self.assertEqual(draw_alone(name, seed=3)[3], draw_alone(name, seed=3)[3], name)

    def test_user_colour_recolours_the_main_body(self):
        red = (0.86, 0.12, 0.12)
        for name in ("shoe", "car", "tshirt", "giftbox", "shoppingbag", "sofa", "tent", "truck", "dog", "tractor", "toolbox", "child", "worker", "swing"):
            _, _, cols, _ = draw_alone(name, color=red)
            r = sum(c[0] for c in cols) / len(cols)
            b = sum(c[2] for c in cols) / len(cols)
            self.assertGreater(r, b + 0.06, "%s ignored the requested colour" % name)

    def test_lexicon_has_no_clashes_and_every_prop_is_reachable(self):
        self.assertEqual(props.DUPLICATES, [])
        for w in props.WORDS:
            for table in ("COLORS", "SHAPES", "REGION_WORDS", "TIMES", "FLAGS", "SIZES", "POSITIONS", "COUNTS", "STOPWORDS"):
                self.assertNotIn(w, getattr(T, table), "%r clashes with %s" % (w, table))
        reachable = set()
        for target in props.WORDS.values():
            reachable |= set(props.CONCEPTS[target[1:]][1]) if target.startswith("@") else {target}
        self.assertEqual(set(REGISTRY) - reachable, set(), "props nobody can ask for")

    def test_phrases_concepts_and_plurals(self):
        names = lambda text: [(e.name, e.count) for e in T.parse(text).entities]          # noqa: E731
        self.assertEqual(names("coffee shop"), [("cafe", 1)])
        self.assertEqual(names("ice cream"), [("icecream", 1)])
        self.assertEqual(names("gift box"), [("giftbox", 1)])
        self.assertEqual([n for n, _ in names("translation services")], ["globe", "document", "chat"])
        self.assertEqual(names("three cars"), [("car", 3)])
        self.assertEqual(names("red shoes")[0][0], "shoe")
        self.assertEqual(T.parse("red shoes").entities[0].color, T.COLORS["red"])
        self.assertEqual([n for n, _ in names("ek laal kitab")], ["book"])
        self.assertEqual([n for n, _ in names("graduation cap")], ["gradcap"])
        self.assertEqual(T.parse("business photo").entities, [])                          # generic words stay inert
        self.assertEqual(sorted({n for n, _ in names("plumber fixing a leaking tap")}), ["faucet", "toolbox", "worker", "wrench"])
        self.assertEqual([n for n, _ in names("farm")], ["tractor", "cow", "sheep"])
        self.assertEqual([n for n, _ in names("pet shop")], ["shop", "dog", "cat"])
        self.assertEqual([n for n, _ in names("house painting services")], ["paintroller", "bucket", "ladder", "house"])
        self.assertEqual([n for n, _ in names("hair salon")], ["scissors", "comb", "plant"])
        self.assertEqual(names("kids")[0][0], "child")                                    # moved off the generic person
        self.assertEqual(names("two dogs"), [("dog", 2)])

    def test_routing_between_scene_landscape_and_old_modes(self):
        mode = lambda text: choose_mode(T.parse(text))                                      # noqa: E731
        self.assertEqual(mode("fresh pizza"), "scene")
        self.assertEqual(mode("laptop on a desk"), "scene")
        self.assertEqual(mode("restaurant dining table"), "scene")           # indoor cue turns a venue into its interior
        self.assertEqual(mode("coffee shop"), "landscape")
        self.assertEqual(mode("car driving on a road at sunset"), "landscape")
        self.assertEqual(mode("coffee cup on the beach"), "landscape")
        self.assertEqual(mode("red house with a tree"), "landscape")
        self.assertEqual(mode("dairy farm with cows"), "landscape")                        # farm animals and machinery live outdoors
        self.assertEqual(mode("construction site with a crane"), "landscape")
        self.assertEqual(mode("kids playground with swings"), "landscape")
        self.assertEqual(mode("plumber fixing a tap"), "scene")                           # tools go on a workbench
        self.assertEqual(mode("dog"), "scene")                                            # pets indoors
        self.assertEqual(mode("red square"), "shapes")
        self.assertEqual(mode("mandala"), "mandala")

    def test_emergency_dental_winter_concepts_and_routing(self):
        names = lambda text: [e.name for e in T.parse(text).entities]                        # noqa: E731
        self.assertEqual(names("dental"), ["dentist", "tooth", "toothbrush", "dentalchair"])
        self.assertEqual(names("pharmacy"), ["pills", "syringe", "medicalcross"])
        self.assertEqual(names("fire"), ["firetruck", "firefighter", "hydrant"])
        self.assertEqual(names("ice skating rink"), ["skater", "iceskate"])
        self.assertIn("snow", T.parse("ice skating rink").flags)                              # concepts can imply a flag
        self.assertIn("snow", T.parse("ski resort").flags)
        self.assertEqual(names("fire station"), ["firetruck", "firefighter", "hydrant"])      # phrase -> concept
        mode = lambda text: choose_mode(T.parse(text))                                        # noqa: E731
        for text in ("ambulance", "fire station", "police car", "skier", "ice hockey", "snowman"):
            self.assertEqual(mode(text), "landscape", text)                                    # rescue/winter live outdoors
        for text in ("dentist with a tooth", "dentist clinic with a happy tooth", "pharmacy pills", "doctor"):
            self.assertEqual(mode(text), "scene", text)
        w, h = 96, 64
        px = render("snowman in winter", w, h)[0].to_rgb_bytes()
        ground = [px[(y * w + x) * 3] for y in range(int(h * 0.85), h) for x in range(w)]
        self.assertGreater(sum(ground) / len(ground), 170)                                   # snowy ground is bright
        self.assertGreater(len(set(ground)), 3)

    def test_crowded_concepts_mark_extras_as_secondary(self):
        flags = [e.secondary for e in T.parse("repair").entities]
        self.assertEqual(flags, [False, False, True, True, True])                            # first two props are primary
        self.assertEqual([e.secondary for e in T.parse("red car").entities], [False])
        for text in ("car repair garage", "farm with tractor cows and sheep", "hospital with doctor nurse and ambulance"):
            cv, _, _ = render(text, 160, 100)
            self.assertEqual(len(cv.to_rgb_bytes()), 160 * 100 * 3)

    def test_every_prop_scene_renders_in_all_sizes(self):
        for name in sorted(REGISTRY):
            word = next((w for w, n in T.OBJECTS.items() if n == name), None)
            if word is None:                                   # only reachable through a concept word, covered elsewhere
                continue
            for size in ((64, 64), (96, 48)):
                cv, parsed, mode = render(word, *size)
                self.assertIn(name, [e.name for e in parsed.entities])
                self.assertEqual(len(cv.to_rgb_bytes()), size[0] * size[1] * 3)

    def test_scene_content_is_really_there(self):
        """Pixel checks that the right thing was drawn, not just that nothing crashed."""
        w, h = 160, 100
        cv, _, _ = render("red car driving on a road at sunset", w, h)
        px = cv.to_rgb_bytes()
        reds = sum(1 for y in range(int(h * 0.6), h) for x in range(w)
                   if px[(y * w + x) * 3] > 170 and px[(y * w + x) * 3 + 1] < 90 and px[(y * w + x) * 3 + 2] < 90)
        self.assertGreater(reds, 120)                                         # a red car body is on the road
        cv, _, _ = render("blue sofa", w, h)
        px = cv.to_rgb_bytes()
        blues = sum(1 for i in range(0, len(px), 3) if px[i + 2] > px[i] + 40)
        self.assertGreater(blues, 300)


class LearnedStyleTests(unittest.TestCase):
    def test_trained_palette_tints_prop_scene_backdrops_only(self):
        # a model that has only seen orange images for the words "birthday cake"
        orange = bytes([240, 140, 20] * 64)
        m = LearnedModel(8)
        train_model(m, [make_sample("birthday cake candles", [v / 255.0 for v in orange]) for _ in range(1)] +
                    [make_sample("birthday cake party", [v / 255.0 for v in bytes([235, 135, 25] * 64)])], epochs=40)
        hint = m.palette_hint("birthday cake")
        self.assertTrue(hint["top"][0] > hint["top"][2] + 0.4)               # orange: red >> blue
        self.assertIsNone(m.palette_hint("zzz qqq"))

        def wall(model, learned="auto"):
            cv, _, mode = render("birthday cake", 64, 64, model=model, learned=learned)
            px = cv.to_rgb_bytes()
            i = (14 * 64 + 8) * 3                                             # wall area, away from props
            return mode, px[i:i + 3]
        plain_mode, plain = wall(None)
        styled_mode, styled = wall(m)
        self.assertEqual((plain_mode, styled_mode), ("scene", "scene+style"))
        self.assertGreater(styled[0] - styled[2], plain[0] - plain[2] + 25)  # warmer than the untrained scene
        self.assertEqual(wall(m, "off")[0], "scene")
        self.assertEqual(wall(m, "blend")[0], "scene+style")
        # landscapes are never recoloured by the model
        a = render("red house with a tree", 48, 48)[0].to_rgb_bytes()
        b = render("red house with a tree", 48, 48, model=m)[0].to_rgb_bytes()
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
