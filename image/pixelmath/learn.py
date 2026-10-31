"""Learnable text -> appearance model (pure Python, trained from your own images).

What it learns
--------------
Every training example is (caption, image). The image is reduced to a small colour grid
(16x16 by default). The model is a *bag-of-words linear regressor*: each word owns a learned
grid of colours, and a prompt's prediction is

        bias_grid + mean(word_grid for each known word in the prompt)

trained with AdaGrad on mean-squared error, with a held-out validation set and early stopping.
So it genuinely learns, from your data, what words like "aqua", "monsoon" or "diwali" *look like*
(palette, brightness, where light/dark areas sit) and combines words it has seen separately.

What it cannot learn
--------------------
Fine detail and object shapes. A 16x16 grid is a colour/lighting/composition prior: generated
images from this model are smooth colour fields with procedural texture, not drawings of objects.
Sharp objects come from the procedural painters in painter.py.

Training is incremental: samples are stored inside the model file, so adding new images later
retrains on old + new data together (no forgetting).
"""
import csv
import hashlib
import json
import math
import os
import random
import re
import shutil
from dataclasses import dataclass

from .imageread import MAX_PIXELS, load_thumbnail, load_thumbnails
from .raster import Canvas, Noise
from .tokenizer import STOPWORDS, _words

FORMAT = "pixelmath-learned"
VERSION = 1
DEFAULT_GRID = 16
IMAGE_EXTS = {".png", ".bmp", ".jpg", ".jpeg"}
UNSUPPORTED_EXTS = {".webp", ".heic", ".heif", ".gif", ".tif", ".tiff", ".avif", ".jp2", ".ico"}
MAX_MODEL_BYTES = 1024 * 1024 * 1024


class ModelError(ValueError):
    pass


# ------------------------------------------------------------------ words
def caption_words(text):
    """Distinct content words of a caption/prompt (lowercase, light plural stripping)."""
    out, seen = [], set()
    for w in _words(text):
        if (w.isascii() and w.isdigit()) or w in STOPWORDS:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


@dataclass
class Sample:
    id: str
    caption: str
    thumb: bytes            # grid*grid*3 bytes, row-major RGB
    niche: str = ""         # optional labels from a {image, caption, niche, mood} manifest
    mood: str = ""


def label_tokens(niche, mood):
    """Letters-only tokens that stand for a niche / mood inside the bag-of-words (e.g. 'nichedental', 'moodwarm')."""
    out = []
    if niche:
        out.append("niche" + "".join(ch for ch in niche.lower() if ch.isalpha()))
    if mood:
        out.append("mood" + "".join(ch for ch in mood.lower() if ch.isalpha()))
    return out


def make_sample(caption, thumb_floats, niche="", mood=""):
    thumb = bytes(min(255, max(0, int(round(v * 255)))) for v in thumb_floats)
    sid = hashlib.md5(caption.encode("utf-8") + thumb + (("|%s|%s" % (niche, mood)).encode("utf-8") if niche or mood else b"")).hexdigest()[:12]
    return Sample(sid, caption, thumb, niche, mood)


# ------------------------------------------------------------------ model
class LearnedModel:
    def __init__(self, grid=DEFAULT_GRID):
        self.grid = grid
        self.dim = grid * grid * 3
        self.bias = [0.5] * self.dim
        self.rows = {}               # word -> list[float] (dim)
        self.doc_freq = {}           # word -> number of training captions containing it
        self.samples = []            # list[Sample]; kept so training can be re-run on old + new data
        self.meta = {}
        self.extras = {}             # optional trained add-ons stored in the same file (e.g. the studio's niche classifier)

    # --- inference
    def known_words(self, text):
        return [w for w in caption_words(text) if w in self.rows]

    def predict(self, text):
        words = self.known_words(text)
        y = list(self.bias)
        if words:
            k = 1.0 / len(words)
            for w in words:
                y = [a + k * b for a, b in zip(y, self.rows[w])]
        return [0.0 if v < 0.0 else 1.0 if v > 1.0 else v for v in y]

    def palette_hint(self, text):
        """Backdrop colours this model associates with the prompt (top / bottom of the predicted grid).

        Returns None when the model knows none of the prompt's words. Used by prop scenes ("blend").
        """
        words = self.known_words(text)
        if not words:
            return None
        t = self.predict(text)
        g = self.grid
        band = max(1, g // 4)

        def mean_rows(r0, r1):
            cells = [(r, c) for r in range(r0, r1) for c in range(g)]
            return tuple(sum(t[(r * g + c) * 3 + ch] for r, c in cells) / len(cells) for ch in range(3))
        return {"top": mean_rows(0, band), "bottom": mean_rows(g - band, g), "words": words,
                "strength": min(0.85, 0.35 + 0.2 * len(words))}

    def word_color(self, word):
        """Average colour (0-255 RGB) this word contributes on its own, for reports."""
        row = self.rows[word]
        vals = [min(1.0, max(0.0, b + r)) for b, r in zip(self.bias, row)]
        return tuple(int(round(255 * sum(vals[c::3]) / (len(vals) / 3))) for c in range(3))

    # --- persistence
    def save(self, path):
        data = {
            "format": FORMAT, "version": VERSION, "grid": self.grid, "meta": self.meta,
            "bias": [round(v, 4) for v in self.bias],
            "vocab": {w: {"n": self.doc_freq.get(w, 0), "w": [round(v, 4) for v in row]}
                      for w, row in sorted(self.rows.items())},
            "samples": [dict({"id": s.id, "caption": s.caption, "thumb": s.thumb.hex()},
                             **({"niche": s.niche} if s.niche else {}), **({"mood": s.mood} if s.mood else {})) for s in self.samples],
        }
        if self.extras:
            data["extras"] = self.extras
        tmp = "%s.tmp%d" % (path, os.getpid())
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
            if os.path.exists(path):
                shutil.copy2(path, path + ".bak")
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    @classmethod
    def load(cls, path):
        try:
            if os.path.getsize(path) > MAX_MODEL_BYTES:
                raise ModelError("model file is too large")
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("format") != FORMAT or data.get("version") != VERSION:
                raise ModelError("not a pixelmath model file (format/version mismatch)")
            grid = data["grid"]
            if not isinstance(grid, int) or not 4 <= grid <= 64:
                raise ModelError("bad grid size in model")
            m = cls(grid)

            def numbers(seq):
                if not isinstance(seq, list) or len(seq) != m.dim:
                    raise ModelError("corrupt model (wrong vector length)")
                out = [float(v) for v in seq]
                if not all(math.isfinite(v) for v in out):
                    raise ModelError("corrupt model (non-finite number)")
                return out

            m.bias = numbers(data["bias"])
            for word, entry in data["vocab"].items():
                m.rows[str(word)] = numbers(entry["w"])
                m.doc_freq[str(word)] = int(entry["n"])
            for s in data["samples"]:
                thumb = bytes.fromhex(s["thumb"])
                if len(thumb) != m.dim:
                    raise ModelError("corrupt model (sample size)")
                m.samples.append(Sample(str(s["id"]), str(s["caption"]), thumb, str(s.get("niche", "")), str(s.get("mood", ""))))
            m.meta = dict(data.get("meta", {}))
            extras = data.get("extras", {})
            m.extras = extras if isinstance(extras, dict) else {}
            return m
        except ModelError:
            raise
        except (OSError, KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ModelError("cannot read model %r: %s" % (path, exc))


# ------------------------------------------------------------------ training
def _prepare(samples):
    return [(caption_words(s.caption) + label_tokens(s.niche, s.mood), [b / 255.0 for b in s.thumb]) for s in samples]


def _mse(pred, target):
    return sum((p - t) ** 2 for p, t in zip(pred, target)) / len(target)


def _predict(bias, rows, words):
    ws = [w for w in words if w in rows]
    y = list(bias)
    if ws:
        k = 1.0 / len(ws)
        for w in ws:
            y = [a + k * b for a, b in zip(y, rows[w])]
    return [0.0 if v < 0.0 else 1.0 if v > 1.0 else v for v in y]


def train_weights(train, val, dim, epochs, lr, l2, seed, patience, log=None):
    """AdaGrad on sparse bag-of-words rows. Returns (bias, rows, doc_freq, history)."""
    rng = random.Random(seed)
    data = _prepare(train)
    vdata = _prepare(val) if val else []
    doc_freq = {}
    for words, _ in data:
        for w in words:
            doc_freq[w] = doc_freq.get(w, 0) + 1
    rows = {w: [0.0] * dim for w in doc_freq}
    gsum = {w: 0.0 for w in doc_freq}
    n = len(data)
    bias = [sum(t[j] for _, t in data) / n for j in range(dim)]
    bias_g, bias_lr = 0.0, lr * 0.1
    baseline = sum(_mse(bias, t) for _, t in vdata) / len(vdata) if vdata else None
    hist = {"train": [], "val": [], "baseline_val": baseline, "best_epoch": epochs}
    best = (float("inf"), None, None, 0)
    stale = 0
    order = list(range(n))
    for ep in range(1, epochs + 1):
        rng.shuffle(order)
        total = 0.0
        for i in order:
            words, target = data[i]
            pred = _predict(bias, rows, words)
            err = [p - t for p, t in zip(pred, target)]
            total += sum(e * e for e in err) / dim
            if words:
                k = 1.0 / len(words)
                for w in words:
                    row = rows[w]
                    g = [k * e + l2 * r for e, r in zip(err, row)]
                    gsum[w] += sum(x * x for x in g) / dim
                    step = lr / (math.sqrt(gsum[w]) + 1e-8)
                    rows[w] = [r - step * x for r, x in zip(row, g)]
            bias_g += sum(e * e for e in err) / dim
            step = bias_lr / (math.sqrt(bias_g) + 1e-8)
            bias = [b - step * e for b, e in zip(bias, err)]
        tr = total / n
        hist["train"].append(tr)
        if vdata:
            va = sum(_mse(_predict(bias, rows, w), t) for w, t in vdata) / len(vdata)
            hist["val"].append(va)
            if va < best[0] - 1e-7:
                best = (va, list(bias), {w: list(r) for w, r in rows.items()}, ep)
                stale = 0
            else:
                stale += 1
        else:
            va = None
        if log:
            log(ep, tr, va)
        if vdata and stale >= patience:
            break
    if vdata and best[1] is not None:
        bias, rows = best[1], best[2]
        hist["best_epoch"] = best[3]
    else:
        hist["best_epoch"] = len(hist["train"])
    return bias, rows, doc_freq, hist


def train_model(model, new_samples, epochs=80, lr=0.3, l2=1e-4, val_frac=0.15, seed=0,
                patience=8, refit=True, log=None):
    """(Re)train `model` on its stored samples plus `new_samples`. Returns a metrics dict."""
    known = {s.id: s for s in model.samples}
    added = 0
    for s in new_samples:
        if len(s.thumb) != model.dim:
            raise ModelError("sample grid does not match model grid")
        if s.id not in known:
            known[s.id] = s
            added += 1
    samples = [known[k] for k in sorted(known)]
    if not samples:
        raise ModelError("no training samples")
    rng = random.Random(seed)
    shuffled = list(samples)
    rng.shuffle(shuffled)
    n_val = 0
    if len(samples) >= 10 and val_frac > 0:
        n_val = max(1, min(int(round(len(samples) * val_frac)), len(samples) // 3))
    val, train = shuffled[:n_val], shuffled[n_val:]

    bias, rows, doc_freq, hist = train_weights(train, val, model.dim, epochs, lr, l2, seed, patience, log)
    metrics = {"samples": len(samples), "added": added, "val_samples": n_val,
               "best_epoch": hist["best_epoch"], "baseline_val": hist["baseline_val"],
               "val_mse": min(hist["val"]) if hist["val"] else None,
               "train_mse": hist["train"][-1], "refit": False}
    if n_val and refit:
        if log:
            log(0, None, None)
        bias, rows, doc_freq, _ = train_weights(samples, [], model.dim, hist["best_epoch"], lr, l2,
                                                seed, patience)
        metrics["refit"] = True
    model.bias, model.rows, model.doc_freq, model.samples = bias, rows, doc_freq, samples
    model.meta = {"samples": len(samples), "vocab": len(rows), "epochs": metrics["best_epoch"],
                  "val_mse": metrics["val_mse"], "baseline_val": metrics["baseline_val"]}
    from .studio.classifier import build_niche_nb
    nb = build_niche_nb(samples)
    if nb:
        model.extras["niche_nb"] = nb
        metrics["niche_classes"] = len(nb["classes"])
    else:
        model.extras.pop("niche_nb", None)
    return metrics


# ------------------------------------------------------------------ dataset
_FILE_COLS = ("file", "filename", "image", "path", "name")
_CAP_COLS = ("caption", "text", "prompt", "description", "label")


def _norm_key(path):
    return path.replace("\\", "/").lower()


def _read_caption_tables(root):
    try:
        return _read_caption_tables_unchecked(root)
    except (ValueError, csv.Error, UnicodeDecodeError) as exc:
        if isinstance(exc, ModelError):
            raise
        raise ModelError("cannot read captions file in %s: %s" % (root, exc))


def _read_caption_tables_unchecked(root):
    table = {}
    csv_path = os.path.join(root, "captions.csv")
    if os.path.isfile(csv_path):
        with open(csv_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            cols = {(c or "").strip().lower(): c for c in (reader.fieldnames or [])}
            fcol = next((cols[c] for c in _FILE_COLS if c in cols), None)
            ccol = next((cols[c] for c in _CAP_COLS if c in cols), None)
            if fcol is None or ccol is None:
                raise ModelError("captions.csv needs a file column (%s) and a caption column (%s)"
                                 % ("/".join(_FILE_COLS), "/".join(_CAP_COLS)))
            for row in reader:
                if row.get(fcol) and row.get(ccol):
                    table[_norm_key(row[fcol].strip())] = row[ccol].strip()
    json_path = os.path.join(root, "captions.json")
    if os.path.isfile(json_path):
        with open(json_path, encoding="utf-8") as fh:
            obj = json.load(fh)
        items = obj.items() if isinstance(obj, dict) else (
            (e.get("file") or e.get("filename") or e.get("image"), e.get("caption") or e.get("text"))
            for e in obj if isinstance(e, dict))
        for f, c in items:
            if f and c:
                table[_norm_key(str(f).strip())] = str(c).strip()
    return table


MANIFEST_NAMES = ("manifest.jsonl", "dataset.jsonl")


def _read_manifest(root):
    """{image, caption, niche, mood} records, one JSON object per line: normalised image path -> (caption, niche, mood)."""
    out = {}
    for name in MANIFEST_NAMES:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8-sig") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    raise ModelError("%s line %d is not valid JSON" % (name, n))
                if not isinstance(rec, dict) or not isinstance(rec.get("image"), str) or not isinstance(rec.get("caption"), str):
                    raise ModelError('%s line %d needs "image" and "caption" strings (and optional "niche", "mood")' % (name, n))
                niche, mood = rec.get("niche") or "", rec.get("mood") or ""
                if not isinstance(niche, str) or not isinstance(mood, str):
                    raise ModelError("%s line %d: niche and mood must be strings" % (name, n))
                out[_norm_key(rec["image"].strip())] = (rec["caption"].strip(), niche.strip(), mood.strip().lower())
    return out


def _check_labels(niche, mood):
    """Reason a manifest label is unusable, or None. Niche ids come from the studio registry."""
    if mood:
        from .studio.palette import MOODS
        if mood not in MOODS:
            return "unknown mood %r (use %s)" % (mood, ", ".join(MOODS))
    if niche:
        from .studio.niches import NICHES, load_all
        load_all()
        if niche not in NICHES and niche != "none":
            return "unknown niche %r" % niche
    return None


def _filename_caption(rel):
    stem = os.path.splitext(os.path.basename(rel))[0]
    words = [w for w in re.split(r"[_\-.\s]+", stem) if w and not w.isdigit()]
    folders = [p for p in re.split(r"[\\/]", os.path.dirname(rel)) if p]
    return " ".join(re.sub(r"[_\-.]+", " ", f) for f in folders) + " " + " ".join(words)


def load_dataset(data_dir, grid=DEFAULT_GRID, extras=None, max_pixels=MAX_PIXELS):
    """Scan a folder for images + captions. Returns (samples, skipped, source_counts).

    Caption priority: captions.csv / captions.json (in the image's own folder, or the data root
    using the relative path)  >  sidecar <image>.txt  >  folder + file name.
    Image formats the readers cannot decode (webp, heic, ...) are reported in `skipped`.
    `extras`, if a dict, receives sample id -> (relative file name, 64x64 preview as RGB bytes) for the dataset manager.
    Images larger than `max_pixels` are skipped (the HTTP server passes a lower cap for uploads).
    """
    root = os.path.abspath(data_dir)
    if not os.path.isdir(root):
        raise ModelError("data folder not found: %s" % data_dir)
    root_table = _read_caption_tables(root)
    manifest = _read_manifest(root)
    samples, skipped, sources = [], [], {"table": 0, "sidecar": 0, "filename": 0, "manifest": 0}
    for dirpath, dirs, files in os.walk(root):
        dirs.sort()
        dir_table = root_table if dirpath == root else _read_caption_tables(dirpath)
        for fn in sorted(files):
            base, ext = os.path.splitext(fn)
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            if ext.lower() in UNSUPPORTED_EXTS:
                skipped.append((rel, "unsupported image format %s (convert to PNG or JPEG)" % ext.lower()))
                continue
            if ext.lower() not in IMAGE_EXTS:
                continue
            path = os.path.join(dirpath, fn)
            niche = mood = ""
            rec = manifest.get(_norm_key(rel))
            if rec:
                caption, niche, mood = rec
                bad = _check_labels(niche, mood)
                if bad:
                    skipped.append((rel, bad))
                    continue
            else:
                caption = (dir_table.get(_norm_key(fn)) or root_table.get(_norm_key(rel))
                           or root_table.get(_norm_key(fn)))
            source = "manifest" if rec else "table"
            if not caption:
                side = os.path.join(dirpath, base + ".txt")
                if os.path.isfile(side):
                    with open(side, encoding="utf-8", errors="replace") as fh:
                        caption, source = fh.read().strip(), "sidecar"
            if not caption:
                caption, source = _filename_caption(rel), "filename"
            if not caption_words(caption):
                skipped.append((rel, "no usable caption words"))
                continue
            try:
                if extras is None:
                    thumb = load_thumbnail(path, grid, max_pixels)
                else:
                    thumb, prev = load_thumbnails(path, (grid, 64), max_pixels)
            except Exception as exc:                       # one bad file must not stop a run
                skipped.append((rel, "%s: %s" % (type(exc).__name__, exc)))
                continue
            samples.append(make_sample(caption, thumb, niche, mood))
            if extras is not None:
                extras[samples[-1].id] = (rel.replace("\\", "/"), bytes(min(255, max(0, int(round(v * 255)))) for v in prev))
            sources[source] += 1
    return samples, skipped, sources


# ------------------------------------------------------------------ rendering
def render_learned(model, prompt, width, height, seed=0):
    """Upsample the predicted colour grid to a full image and add procedural texture."""
    g = model.grid
    t = model.predict(prompt)
    cv = Canvas(width, height)
    px = cv.px
    xs = []
    for x in range(width):
        gx = (x + 0.5) / width * g - 0.5
        x0 = math.floor(gx)
        f = gx - x0
        f = f * f * (3 - 2 * f)
        xs.append((min(g - 1, max(0, x0)) * 3, min(g - 1, max(0, x0 + 1)) * 3, f))
    noise = Noise(seed + 977)
    s = min(width, height)
    n1, n2 = s / 10.0, s / 40.0
    i = 0
    for y in range(height):
        gy = (y + 0.5) / height * g - 0.5
        y0 = math.floor(gy)
        fy = gy - y0
        fy = fy * fy * (3 - 2 * fy)
        r0 = min(g - 1, max(0, y0)) * g * 3
        r1 = min(g - 1, max(0, y0 + 1)) * g * 3
        for x in range(width):
            a, b, fx = xs[x]
            detail = (noise.v2(x / n1, y / n1) - 0.5) * 0.07 + (noise.v2(x / n2, y / n2) - 0.5) * 0.04
            for c in range(3):
                top = t[r0 + a + c] * (1 - fx) + t[r0 + b + c] * fx
                bot = t[r1 + a + c] * (1 - fx) + t[r1 + b + c] * fx
                px[i + c] = top * (1 - fy) + bot * fy + detail
            i += 3
    return cv
