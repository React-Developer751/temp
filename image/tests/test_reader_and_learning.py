import base64
import contextlib
import csv
import io
import json
import os
import random
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pixelmath import encode_bmp, encode_png, render                       # noqa: E402
from pixelmath import tokenizer as T                                       # noqa: E402
from pixelmath.imageread import ImageError, decode_bmp, decode_image, decode_png, to_thumbnail  # noqa: E402
from pixelmath.learn import (LearnedModel, ModelError, caption_words, load_dataset, make_sample,  # noqa: E402
                             train_model)
from pixelmath.trainer import main as train_main                           # noqa: E402

# 32x32 baseline JPEG (made by macOS sips, 4:2:0): 16px blocks red | green / blue | gray(128)
JPEG_BLOCKS = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAASABIAAD/4QBMRXhpZgAATU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQA"
    "AAABAAAAIKADAAQAAAABAAAAIAAAAAD/7QA4UGhvdG9zaG9wIDMuMAA4QklNBAQAAAAAAAA4QklNBCUAAAAAABDUHYzZjwCyBOmA"
    "CZjs+EJ+/8AAEQgAIAAgAwEiAAIRAQMRAf/EAB8AAAEFAQEBAQEBAAAAAAAAAAABAgMEBQYHCAkKC//EALUQAAIBAwMCBAMFBQQE"
    "AAABfQECAwAEEQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZHSElKU1RVVldY"
    "WVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk"
    "5ebn6Onq8fLz9PX29/j5+v/EAB8BAAMBAQEBAQEBAQEAAAAAAAABAgMEBQYHCAkKC//EALURAAIBAgQEAwQHBQQEAAECdwABAgMR"
    "BAUhMQYSQVEHYXETIjKBCBRCkaGxwQkjM1LwFWJy0QoWJDThJfEXGBkaJicoKSo1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdo"
    "aWpzdHV2d3h5eoKDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uLj5OXm5+jp6vLz"
    "9PX29/j5+v/bAEMAAQEBAQEBAgEBAgICAgICAwICAgIDBAMDAwMDBAUEBAQEBAQFBQUFBQUFBQYGBgYGBgcHBwcHCAgICAgICAgI"
    "CP/bAEMBAQEBAgICAwICAwgFBQUICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICP/dAAQA"
    "Av/aAAwDAQACEQMRAD8A/Leiiiv8/wA/6+D9WKKKK/j8/wDLPP/Q/mfooor/AK+D8HP6YKKKK/5Bz94P/9k=")


def put(path, data):
    with open(path, "wb" if isinstance(data, bytes) else "w") as fh:
        fh.write(data)


# ----------------------------------------------------------------- test PNG encoder
def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def _filter(ft, row, prev, bpp):
    out = bytearray()
    for i, x in enumerate(row):
        a = row[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        pred = (0, a, b, (a + b) >> 1, _paeth(a, b, c))[ft]
        out.append((x - pred) & 255)
    return bytes(out)


def _pack(samples, depth):
    if depth == 8:
        return bytes(samples)
    if depth == 16:
        return b"".join(s.to_bytes(2, "big") for s in samples)
    bits = "".join(format(s, "0%db" % depth) for s in samples)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


_CH = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
_PASSES = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))


def build_png(w, h, ctype, depth, sample, interlace=False, plte=None, trns=None):
    ch = _CH[ctype]
    bpp = max(1, ch * depth // 8)
    raw = bytearray()
    for xs, ys, dx, dy in (_PASSES if interlace else ((0, 0, 1, 1),)):
        pw, ph = (w - xs + dx - 1) // dx, (h - ys + dy - 1) // dy
        if pw <= 0 or ph <= 0:
            continue
        prev = bytes((pw * ch * depth + 7) // 8)
        for j in range(ph):
            y = ys + j * dy
            samples = [v for i in range(pw) for v in sample(xs + i * dx, y)]
            row = _pack(samples, depth)
            ft = j % 5
            raw.append(ft)
            raw += _filter(ft, row, prev, bpp)
            prev = row

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, int(interlace)))
    if plte:
        out += chunk(b"PLTE", plte)
    if trns:
        out += chunk(b"tRNS", trns)
    return out + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")


def _white(c, a):
    return (c * a + 255 * (255 - a)) // 255


class PngDecoderTests(unittest.TestCase):
    W, H = 13, 11

    def check(self, ctype, depth, interlace):
        maxv = (1 << depth) - 1
        ch = _CH[ctype]
        npal = min(maxv + 1, 256)
        plte = bytes((i * 53 + c * 29) % 256 for i in range(npal) for c in range(3)) if ctype == 3 else None
        trns = bytes([40, 200]) if ctype == 3 else None

        def sample(x, y):
            if ctype == 3:
                return [(x * 3 + y * 5) % npal]
            return [(x * 37 + y * 91 + c * 53) % (maxv + 1) for c in range(ch)]

        def to8(v):
            return v >> 8 if depth == 16 else (v * 255 // maxv if depth < 8 else v)

        data = build_png(self.W, self.H, ctype, depth, sample, interlace, plte, trns)
        w, h, rgb = decode_png(data)
        self.assertEqual((w, h), (self.W, self.H))
        for y in range(self.H):
            for x in range(self.W):
                s = sample(x, y)
                if ctype == 0:
                    exp = (to8(s[0]),) * 3
                elif ctype == 2:
                    exp = tuple(to8(v) for v in s)
                elif ctype == 3:
                    a = trns[s[0]] if s[0] < len(trns) else 255
                    exp = tuple(_white(plte[s[0] * 3 + c], a) for c in range(3))
                elif ctype == 4:
                    exp = (_white(to8(s[0]), to8(s[1])),) * 3
                else:
                    exp = tuple(_white(to8(s[c]), to8(s[3])) for c in range(3))
                got = tuple(rgb[(y * w + x) * 3:(y * w + x) * 3 + 3])
                self.assertEqual(got, exp, "type %d depth %d interlace %s at (%d,%d)" % (ctype, depth, interlace, x, y))

    def test_all_colour_types_filters_and_adam7(self):
        for ctype, depth in ((0, 1), (0, 4), (0, 8), (0, 16), (2, 8), (2, 16), (3, 2), (3, 8),
                             (4, 8), (4, 16), (6, 8), (6, 16)):
            for interlace in (False, True):
                self.check(ctype, depth, interlace)

    def test_corrupt_inputs_raise_image_error(self):
        good = encode_png(8, 8, bytes(range(192)))
        for bad in (b"", b"hello world", good[:20], good[:60], good[: len(good) // 2], b"\x89PNG\r\n\x1a\n" + b"\x00" * 30):
            with self.assertRaises(ImageError):
                decode_image(bad)

    def test_decompression_bomb_rejected(self):
        evil = bytearray(build_png(4, 4, 2, 8, lambda x, y: [0, 0, 0]))
        # claim a huge image in IHDR while keeping a tiny IDAT
        evil[16:24] = struct.pack(">II", 60000, 60000)
        with self.assertRaises(ImageError):
            decode_image(bytes(evil))

    def test_pixel_cap_is_checked_before_decoding(self):
        big = encode_png(64, 64, bytes(64 * 64 * 3))
        self.assertEqual(decode_image(big)[:2], (64, 64))
        with self.assertRaises(ImageError) as cm:
            decode_image(big, max_pixels=4000)
        self.assertIn("too large", str(cm.exception))
        for data in (encode_bmp(64, 64, bytes(64 * 64 * 3)),):
            with self.assertRaises(ImageError):
                decode_image(data, max_pixels=4000)
        huge = bytearray(build_png(4, 4, 2, 16, lambda x, y: [0, 0, 0]))
        huge[16:24] = struct.pack(">II", 10000, 10000)                                # 100 MP: refused by the default cap
        with self.assertRaises(ImageError) as cm:
            decode_image(bytes(huge))
        self.assertIn("limit 40 MP", str(cm.exception))


class OtherFormatTests(unittest.TestCase):
    def test_bmp_roundtrip_and_top_down(self):
        rgb = bytes((i * 7) % 256 for i in range(5 * 3 * 3))
        bmp = encode_bmp(5, 3, rgb)
        self.assertEqual(decode_bmp(bmp)[2], rgb)
        td = bytearray(bmp)
        rows = [bytes(bmp[54 + k * 16:54 + (k + 1) * 16]) for k in range(3)]
        td[54:] = b"".join(reversed(rows))
        td[22:26] = struct.pack("<i", -3)
        self.assertEqual(decode_bmp(bytes(td))[2], rgb)

    def test_bmp_8bit_palette_and_32bit(self):
        pal = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (9, 9, 9)]
        row = bytes([0, 1, 2]) + b"\x00"
        data = (b"BM" + struct.pack("<IHHI", 54 + 16 + 4, 0, 0, 54 + 16)
                + struct.pack("<IiiHHIIiiII", 40, 3, 1, 1, 8, 0, 4, 2835, 2835, 4, 0)
                + b"".join(bytes((b, g, r, 0)) for r, g, b in pal) + row)
        self.assertEqual(decode_bmp(data)[2], bytes([255, 0, 0, 0, 255, 0, 0, 0, 255]))
        data32 = (b"BM" + struct.pack("<IHHI", 54 + 8, 0, 0, 54)
                  + struct.pack("<IiiHHIIiiII", 40, 2, 1, 1, 32, 0, 8, 2835, 2835, 0, 0)
                  + bytes([30, 20, 10, 0, 60, 50, 40, 0]))                  # BGRA, BGRA
        self.assertEqual(decode_bmp(data32)[2], bytes([10, 20, 30, 40, 50, 60]))

    def test_jpeg_block_means_are_exact(self):
        w, h, rgb = decode_image(JPEG_BLOCKS)
        self.assertEqual((w, h), (4, 4))
        want = {(0, 0): (220, 30, 30), (1, 0): (30, 200, 30), (0, 1): (30, 30, 220), (1, 1): (128, 128, 128)}
        for y in range(4):
            for x in range(4):
                got = rgb[(y * 4 + x) * 3:(y * 4 + x) * 3 + 3]
                for a, b in zip(got, want[(x // 2, y // 2)]):
                    self.assertLessEqual(abs(a - b), 3)

    def test_jpeg_unsupported_and_truncated(self):
        progressive = b"\xff\xd8\xff\xc2\x00\x0b\x08\x00\x08\x00\x08\x01\x01\x11\x00\xff\xd9"
        with self.assertRaisesRegex(ImageError, "progressive"):
            decode_image(progressive)
        sos = JPEG_BLOCKS.index(b"\xff\xda")
        for cut in (2, 30, 200, sos + 20, sos + 30, len(JPEG_BLOCKS) - 40):
            with self.assertRaises(ImageError, msg="cut at %d" % cut):   # cut-short files must be rejected, not guessed
                decode_image(JPEG_BLOCKS[:cut])

    def test_thumbnail_crops_to_square_and_averages(self):
        w, h = 8, 4                                    # left half red, right half blue, cropped to 4x4 centre
        rgb = b"".join(bytes((255, 0, 0)) if x < 4 else bytes((0, 0, 255)) for y in range(h) for x in range(w))
        t = to_thumbnail(w, h, rgb, 2)
        self.assertEqual([round(v) for v in t[:6]], [1, 0, 0, 0, 0, 1])


# ----------------------------------------------------------------- learning
def write_png(path, color, rng, n=16, noise=10):
    px = bytearray()
    for _ in range(n * n):
        px += bytes(max(0, min(255, int(c + rng.gauss(0, noise)))) for c in color)
    with open(path, "wb") as fh:
        fh.write(encode_png(n, n, bytes(px)))


def write_split_png(path, top, bottom, rng, n=16):
    px = bytearray()
    for y in range(n):
        for _ in range(n):
            px += bytes(max(0, min(255, int(c + rng.gauss(0, 10)))) for c in (top if y < n // 2 else bottom))
    with open(path, "wb") as fh:
        fh.write(encode_png(n, n, bytes(px)))


TOP = {"aqua": (0, 200, 200), "coral": (250, 110, 90), "olive": (110, 120, 30), "plum": (140, 60, 140)}
BOT = {"mossy": (60, 110, 50), "sandy": (220, 190, 130), "muddy": (100, 70, 40)}


def make_split_dataset(folder, held):
    rng = random.Random(3)
    rows = []
    for t in TOP:
        for b in BOT:
            if (t, b) in held:
                continue
            for v in range(3):
                name = "%s_%s_%d.png" % (t, b, v)
                write_split_png(os.path.join(folder, name), TOP[t], BOT[b], rng)
                rows.append((name, "%s %s" % (t, b)))
    with open(os.path.join(folder, "captions.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["filename", "text"])
        w.writerows(rows)


def expected_grid(t, b, g):
    return [v / 255.0 for y in range(g) for _ in range(g) for v in (TOP[t] if y < g // 2 else BOT[b])]


def rmse(a, b):
    return (sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)) ** 0.5 * 255


class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.held = {("aqua", "muddy"), ("coral", "mossy"), ("plum", "sandy")}
        cls.data = os.path.join(cls.tmp.name, "data")
        os.makedirs(cls.data)
        make_split_dataset(cls.data, cls.held)
        samples, skipped, sources = load_dataset(cls.data, grid=8)
        cls.samples, cls.skipped, cls.sources = samples, skipped, sources
        cls.model = LearnedModel(8)
        cls.metrics = train_model(cls.model, samples, epochs=60, seed=0)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_caption_words(self):
        self.assertEqual(caption_words("A red houses on the left, 3 trees"), ["red", "house", "left", "tree"])

    def test_dataset_read_from_csv(self):
        self.assertEqual(len(self.samples), 27)
        self.assertEqual(self.sources["table"], 27)
        self.assertEqual(self.skipped, [])

    def test_model_beats_baseline_on_validation(self):
        m = self.metrics
        self.assertGreater(m["val_samples"], 0)
        self.assertLess(m["val_mse"], 0.2 * m["baseline_val"])

    def test_composes_word_pairs_it_never_saw_together(self):
        errs, base = [], []
        for t, b in self.held:
            want = expected_grid(t, b, 8)
            errs.append(rmse(self.model.predict("%s %s" % (t, b)), want))
            base.append(rmse(self.model.bias, want))
        self.assertLess(sum(errs) / 3, 14.0)
        self.assertLess(sum(errs) / 3, sum(base) / 3 / 4)

    def test_save_load_roundtrip(self):
        path = os.path.join(self.tmp.name, "rt.json")
        self.model.save(path)
        loaded = LearnedModel.load(path)
        a, b = self.model.predict("aqua mossy"), loaded.predict("aqua mossy")
        self.assertLess(max(abs(x - y) for x, y in zip(a, b)), 1e-3)
        self.assertEqual(len(loaded.samples), len(self.model.samples))

    def test_corrupt_model_files_are_rejected(self):
        d = self.tmp.name
        good = os.path.join(d, "good.json")
        self.model.save(good)
        with open(good) as fh:
            data = json.load(fh)
        cases = {"notjson": "{not json", "empty": "", "list": "[]"}
        for name, text in cases.items():
            p = os.path.join(d, name + ".json")
            put(p, text)
            with self.assertRaises(ModelError):
                LearnedModel.load(p)
        for name, mutate in (("fmt", lambda x: x.update(format="other")),
                             ("bias", lambda x: x.update(bias=[0.1] * 5)),
                             ("grid", lambda x: x.update(grid=3)),
                             ("nan", lambda x: x["bias"].__setitem__(0, float("nan"))),
                             ("thumb", lambda x: x["samples"][0].update(thumb="abcd"))):
            bad = json.loads(json.dumps(data))
            mutate(bad)
            p = os.path.join(d, name + ".json")
            with open(p, "w") as fh:
                json.dump(bad, fh)
            with self.assertRaises(ModelError, msg=name):
                LearnedModel.load(p)
        with self.assertRaises(ModelError):
            LearnedModel.load(os.path.join(d, "missing.json"))

    def test_incremental_training_keeps_old_and_learns_new(self):
        m = LearnedModel(8)
        train_model(m, self.samples, epochs=40)
        old_vocab = set(m.rows)
        rng = random.Random(9)
        extra = []
        with tempfile.TemporaryDirectory() as d:
            for v in range(6):
                write_png(os.path.join(d, "lagoon_%d.png" % v), (20, 120, 160), rng)
            new, _, src = load_dataset(d, grid=8)
        self.assertEqual(src["filename"], 6)
        extra = new
        metrics = train_model(m, extra, epochs=40)
        self.assertEqual(metrics["added"], 6)
        self.assertEqual(metrics["samples"], len(self.samples) + 6)
        self.assertTrue(old_vocab <= set(m.rows) and "lagoon" in m.rows)
        r, g, b = m.word_color("lagoon")
        self.assertLess(abs(r - 20) + abs(g - 120) + abs(b - 160), 45)
        self.assertEqual(train_model(m, extra, epochs=5)["added"], 0)         # re-adding is a no-op

    def test_dataset_sources_and_bad_files(self):
        with tempfile.TemporaryDirectory() as d:
            rng = random.Random(1)
            write_png(os.path.join(d, "a.png"), (200, 0, 0), rng)
            write_png(os.path.join(d, "b.png"), (0, 200, 0), rng)
            os.makedirs(os.path.join(d, "sunset"))
            write_png(os.path.join(d, "sunset", "c_001.png"), (250, 120, 30), rng)
            write_png(os.path.join(d, "123.png"), (1, 2, 3), rng)
            put(os.path.join(d, "broken.png"), b"\x89PNG\r\n\x1a\ngarbage")
            put(os.path.join(d, "captions.json"), json.dumps({"a.png": "crimson desert"}))
            put(os.path.join(d, "b.txt"), "emerald forest")
            samples, skipped, sources = load_dataset(d, grid=8)
            caps = sorted(s.caption.strip() for s in samples)
            self.assertEqual(caps, ["crimson desert", "emerald forest", "sunset c"])
            self.assertEqual(sources, {"table": 1, "sidecar": 1, "filename": 1, "manifest": 0})
            reasons = dict(skipped)
            self.assertIn("123.png", reasons)
            self.assertIn("broken.png", reasons)
        with self.assertRaises(ModelError):
            load_dataset(os.path.join(self.tmp.name, "nope"))

    def test_captions_in_subfolders_and_unsupported_formats(self):
        with tempfile.TemporaryDirectory() as d:
            rng = random.Random(2)
            os.makedirs(os.path.join(d, "photos"))
            write_png(os.path.join(d, "photos", "p1.png"), (200, 0, 0), rng)
            write_png(os.path.join(d, "photos", "p2.png"), (0, 0, 200), rng)
            put(os.path.join(d, "photos", "captions.csv"), "file,caption\np1.png,red balloons\np2.png,blue lake\n")
            put(os.path.join(d, "shot.webp"), b"RIFF....WEBP")
            put(os.path.join(d, "pic.HEIC"), b"x")
            samples, skipped, sources = load_dataset(d, grid=8)
            self.assertEqual(sorted(s.caption for s in samples), ["blue lake", "red balloons"])
            self.assertEqual(sources["table"], 2)
            reasons = dict(skipped)
            self.assertIn("unsupported image format .webp", reasons["shot.webp"])
            self.assertIn("unsupported image format .heic", reasons["pic.HEIC"])

    def test_malformed_caption_files_give_model_error(self):
        for name, text in (("captions.json", "{oops"), ("captions.csv", "a,b\n1,2\n")):
            with tempfile.TemporaryDirectory() as d:
                write_png(os.path.join(d, "a.png"), (1, 2, 3), random.Random(0))
                put(os.path.join(d, name), text)
                with self.assertRaises(ModelError, msg=name):
                    load_dataset(d, grid=8)

    def test_trainer_interrupt_and_unwritable_model_path(self):
        from unittest import mock
        import pixelmath.trainer as trainer
        model_path = os.path.join(self.tmp.name, "intr.json")
        put(model_path, "sentinel")
        err = io.StringIO()
        with mock.patch.object(trainer, "train_model", side_effect=KeyboardInterrupt), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = train_main([self.data, "--model", model_path, "--fresh", "--grid", "8"])
        self.assertEqual(code, 130)
        with open(model_path) as fh:
            self.assertEqual(fh.read(), "sentinel")                              # existing file untouched
        self.assertIn("interrupted", err.getvalue())
        for bad_path, word in ((os.path.join(self.tmp.name, "no_such_dir", "m.json"), "does not exist"),
                               (self.tmp.name, "folder")):
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                self.assertEqual(train_main([self.data, "--model", bad_path]), 1)
            self.assertIn(word, err.getvalue())                                  # fails before any training
        put(os.path.join(self.tmp.name, "corrupt.json"), "{bad")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(train_main([self.data, "--model", os.path.join(self.tmp.name, "corrupt.json")]), 1)
        self.assertIn("--fresh", err.getvalue())

    def test_render_uses_model_only_when_appropriate(self):
        px = lambda *a, **k: render(*a, **k)
        cv, _, mode = px("aqua mossy", 48, 48, model=self.model)
        self.assertEqual(mode, "learned")
        cv2, _, _ = px("aqua mossy", 48, 48, model=self.model)
        self.assertEqual(cv.to_rgb_bytes(), cv2.to_rgb_bytes())                 # deterministic
        self.assertEqual(px("red house", 48, 48, model=self.model)[2], "landscape")
        self.assertEqual(px("aqua mossy", 48, 48, model=self.model, learned="off")[2], "abstract")
        self.assertEqual(px("aqua red house", 48, 48, model=self.model, learned="always")[2], "learned")
        self.assertEqual(px("zzz qqq", 48, 48, model=self.model)[2], "abstract")  # no known word
        with self.assertRaises(ValueError):
            px("x", 48, 48, learned="sometimes")
        top = cv.to_rgb_bytes()[(4 * 48 + 24) * 3:(4 * 48 + 24) * 3 + 3]
        self.assertGreater(top[1], top[0] + 60)                                  # aqua sky: green/blue high, red low

    def test_trainer_cli(self):
        model_path = os.path.join(self.tmp.name, "cli_model.json")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = train_main([self.data, "--model", model_path, "--grid", "8", "--epochs", "25", "--preview",
                               os.path.join(self.tmp.name, "prev")])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("held-out check", out.getvalue())
        self.assertTrue(os.path.getsize(model_path) > 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmp.name, "prev", "preview_00.png")))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = train_main([self.data, "--model", model_path, "--epochs", "5"])
        self.assertEqual(code, 0)
        self.assertIn("(0 new)", out.getvalue())                                 # same data again: nothing added
        with tempfile.TemporaryDirectory() as empty, contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(train_main([empty, "--model", os.path.join(empty, "m.json")]), 1)


# ----------------------------------------------------------------- robustness / CLI
def run_cli(*args, stdin=""):
    return subprocess.run([sys.executable, "-m", "pixelmath", *args], cwd=ROOT, input=stdin,
                          capture_output=True, text=True, timeout=120)


class RobustnessTests(unittest.TestCase):
    def test_devanagari_prompt(self):
        p = T.parse("लाल घर")
        self.assertEqual([(e.name, e.color) for e in p.entities], [("house", T.COLORS["red"])])
        self.assertEqual(T.parse("रात सूरज").time, "night")

    def test_brand_colours_without_an_object_colour_abstract_backgrounds(self):
        mean = lambda px: [sum(px[c::3]) / (len(px) // 3) for c in range(3)]            # noqa: E731
        r, g, b = mean(render("blue abstract technology background", 48, 32)[0].to_rgb_bytes())
        self.assertGreater(b, r + 25)
        r, g, b = mean(render("green abstract background", 48, 32)[0].to_rgb_bytes())
        self.assertGreater(g, r + 20)
        self.assertGreater(g, b + 10)
        q = T.parse("a house with a red door")
        self.assertIsNone(q.entities[0].color)                                           # a door colour must not recolour the house
        self.assertEqual(len(q.loose_colors), 1)
        _, _, mode = render("red zorbl widget", 32, 32)            # unknown nouns: palette only, abstract art
        self.assertEqual(mode, "abstract")
        self.assertEqual(render("red shoes product photo", 32, 32)[2], "scene")      # a known noun now draws the product

    def test_absurd_numbers_and_long_prompts(self):
        self.assertEqual(T.parse("9" * 6000 + " trees").entities[0].count, 24)
        with self.assertRaises(ValueError):
            render("a" * (T.MAX_PROMPT_CHARS + 1), 32, 32)
        for w, h in ((8, 32), (32, 5000)):
            with self.assertRaises(ValueError):
                render("sun", w, h)

    def test_fuzz_never_crashes(self):
        vocab = sorted(set(list(T.COLORS) + list(T.SHAPES) + list(T.OBJECTS) + list(T.REGION_WORDS) + list(T.TIMES)
                           + list(T.FLAGS) + list(T.SIZES) + list(T.POSITIONS) + list(T.COUNTS) + list(T.STOPWORDS)))
        rng = random.Random(11)
        prompts = ["", " ", "!!!", "\x00", "हिंदी लाल घर", "left right top", "100 birds", "tiny tiny tiny sun"]
        prompts += [" ".join(rng.choice(vocab) for _ in range(rng.randint(1, 7))) for _ in range(120)]
        for p in prompts:
            for size in ((16, 16), (33, 17)):
                canvas, _, _ = render(p, *size)
                self.assertEqual(len(canvas.to_rgb_bytes()), size[0] * size[1] * 3, repr(p))

    def test_mutated_files_never_crash_readers_or_loader(self):
        bases = [JPEG_BLOCKS,
                 build_png(23, 17, 2, 8, lambda x, y: [x * 5 % 256, y * 7 % 256, (x + y) % 256]),
                 build_png(23, 17, 6, 8, lambda x, y: [x * 5 % 256, 9, 9, 200], interlace=True),
                 build_png(23, 17, 3, 2, lambda x, y: [(x + y) % 4], plte=bytes(range(12))),
                 encode_bmp(11, 7, bytes(i % 251 for i in range(11 * 7 * 3)))]
        rng = random.Random(5)
        for base in bases:
            for _ in range(250):
                d = bytearray(base)
                k = rng.randrange(4)
                if k == 0:
                    for _ in range(rng.randint(1, 6)):
                        d[rng.randrange(len(d))] = rng.randrange(256)
                elif k == 1:
                    d = d[:rng.randrange(1, len(d))]
                elif k == 2:
                    i = rng.randrange(max(1, min(len(d) - 4, 60)))
                    d[i:i + 4] = struct.pack(">I", rng.choice([0, 65535, 2 ** 31, 2 ** 32 - 1, 100000000]))
                else:
                    i = rng.randrange(len(d))
                    del d[i:i + rng.randint(1, 15)]
                try:
                    w, h, rgb = decode_image(bytes(d))
                    self.assertEqual(len(rgb), w * h * 3)
                except ImageError:
                    pass
        with tempfile.TemporaryDirectory() as tmp:
            m = LearnedModel(8)
            train_model(m, [make_sample("red sun", [0.5] * 192), make_sample("blue sea", [0.2] * 192)], epochs=3)
            path = os.path.join(tmp, "m.json")
            m.save(path)
            with open(path, "rb") as fh:
                raw = fh.read()
            for _ in range(200):
                d = bytearray(raw)
                for _ in range(rng.randint(1, 5)):
                    d[rng.randrange(len(d))] = rng.randrange(256)
                put(path, bytes(d))
                try:
                    LearnedModel.load(path)
                except ModelError:
                    pass

    def test_cli_friendly_errors(self):
        r = run_cli("red", "-o", "x.jpg")
        self.assertEqual(r.returncode, 2)
        self.assertIn(".png or .bmp", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        r = run_cli("red", "-o", "/no/such/dir/x.png", "--size", "32")
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot write", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(run_cli("red", "--size", "100000").returncode, 2)
        r = run_cli("red", "--model", "/no/such/model.json", "--size", "32")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(run_cli(stdin="").returncode, 2)
        r = run_cli("--version")
        self.assertIn("pixelmath", r.stdout)

    def test_version_matches_pyproject(self):
        import re
        import pixelmath
        with open(os.path.join(ROOT, "pyproject.toml")) as fh:
            self.assertEqual(re.search(r'^version = "([^"]+)"', fh.read(), re.M).group(1), pixelmath.__version__)

    def test_cli_writes_file_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.png")
            r = run_cli("red", "square", "-o", out, "--size", "32")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(os.listdir(d), ["o.png"])                           # no temp files left behind


if __name__ == "__main__":
    unittest.main()
