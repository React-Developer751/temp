import os
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath import encode_bmp, encode_png, generate, render          # noqa: E402
from pixelmath.compose import choose_mode                               # noqa: E402
from pixelmath.tokenizer import COLORS, parse, vectorize                # noqa: E402


def decode_png(data):
    """Minimal independent PNG decoder (filter 0 only) used to verify our encoder."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        assert crc == zlib.crc32(tag + body) & 0xFFFFFFFF, "bad CRC in %r" % tag
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat += body
        pos += 12 + length
    w, h = ihdr[0], ihdr[1]
    raw = zlib.decompress(idat)
    rows = [raw[y * (w * 3 + 1) + 1:(y + 1) * (w * 3 + 1)] for y in range(h)]
    assert all(raw[y * (w * 3 + 1)] == 0 for y in range(h))
    return w, h, b"".join(rows)


class TokenizerTests(unittest.TestCase):
    def test_colour_binds_to_following_noun(self):
        p = parse("red square")
        self.assertEqual(len(p.entities), 1)
        self.assertEqual(p.entities[0].name, "square")
        self.assertEqual(p.entities[0].color, COLORS["red"])

    def test_hinglish(self):
        p = parse("ek laal dil aur neela circle")
        self.assertEqual([(e.name, e.color) for e in p.entities],
                         [("heart", COLORS["red"]), ("circle", COLORS["blue"])])

    def test_plural_count_and_size(self):
        p = parse("three big trees")
        e = p.entities[0]
        self.assertEqual((e.name, e.count), ("tree", 3))
        self.assertGreater(e.size, 1.0)

    def test_background_colour_is_not_an_entity(self):
        p = parse("white circle on black background")
        self.assertEqual(len(p.entities), 1)
        self.assertEqual(p.background, COLORS["black"])

    def test_unknown_noun_drops_colour(self):
        p = parse("a house with a red door")
        self.assertIsNone(p.entities[0].color)

    def test_pine_trees_is_one_entity(self):
        p = parse("pine trees")
        self.assertEqual(len(p.entities), 1)
        self.assertIn("conifer", p.flags)

    def test_vector_is_deterministic_and_unit_length(self):
        a, b = vectorize("red house"), vectorize("red house")
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(v * v for v in a), 1.0, places=6)
        self.assertNotEqual(a, vectorize("blue ocean"))

    def test_modes(self):
        self.assertEqual(choose_mode(parse("red square")), "shapes")
        self.assertEqual(choose_mode(parse("sunset over the sea")), "landscape")
        self.assertEqual(choose_mode(parse("mandala")), "mandala")
        self.assertEqual(choose_mode(parse("xyzzy")), "abstract")


class FileFormatTests(unittest.TestCase):
    def test_png_roundtrip(self):
        pixels = bytes((x * 7 + y * 3 + c) % 256 for y in range(5) for x in range(7) for c in range(3))
        w, h, out = decode_png(encode_png(7, 5, pixels))
        self.assertEqual((w, h, out), (7, 5, pixels))

    def test_bmp_header_padding_and_bgr_order(self):
        w, h = 5, 2                                  # 15 bytes/row -> needs 1 pad byte
        rgb = bytes([255, 0, 0] * (w * h))           # pure red
        bmp = encode_bmp(w, h, rgb)
        self.assertEqual(bmp[:2], b"BM")
        size, _, _, offset = struct.unpack("<IHHI", bmp[2:14])
        self.assertEqual(offset, 54)
        self.assertEqual(size, len(bmp))
        self.assertEqual(len(bmp), 54 + (w * 3 + 1) * h)
        self.assertEqual(bmp[54:57], bytes([0, 0, 255]))   # BGR
        self.assertEqual(struct.unpack("<II", bmp[18:26]), (w, h))

    def test_size_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            encode_png(4, 4, b"\x00" * 10)


class RenderTests(unittest.TestCase):
    def pixels(self, prompt, size=64, seed=0):
        canvas, _, _ = render(prompt, size, size, seed)
        return canvas.to_rgb_bytes()

    def test_deterministic(self):
        self.assertEqual(self.pixels("red house"), self.pixels("red house"))

    def test_seed_changes_output(self):
        self.assertNotEqual(self.pixels("red house", seed=0), self.pixels("red house", seed=1))

    def test_prompts_differ(self):
        self.assertNotEqual(self.pixels("red square"), self.pixels("blue ocean"))

    def test_red_square_is_red_in_the_middle(self):
        px = self.pixels("red square", 64)
        i = (32 * 64 + 32) * 3
        r, g, b = px[i:i + 3]
        self.assertGreater(r, 150)
        self.assertLess(g, 80)
        self.assertLess(b, 80)

    def test_non_square_and_all_modes_render(self):
        for prompt in ("red square", "sunset sea boat", "cyberpunk city", "snowy forest", "galaxy planet",
                       "mandala", "geometric pattern", "abstract art", "forest river birds dawn"):
            canvas, _, _ = render(prompt, 96, 64)
            self.assertEqual(len(canvas.to_rgb_bytes()), 96 * 64 * 3, prompt)

    def test_generate_writes_valid_files(self):
        with tempfile.TemporaryDirectory() as d:
            png, bmp = os.path.join(d, "a.png"), os.path.join(d, "a.bmp")
            generate("green hexagon", png, 48, 48)
            generate("green hexagon", bmp, 48, 48)
            with open(png, "rb") as fh:
                self.assertEqual(decode_png(fh.read())[:2], (48, 48))
            with open(bmp, "rb") as fh:
                self.assertEqual(fh.read(2), b"BM")


if __name__ == "__main__":
    unittest.main()
