"""HTTP API for PixelMath (standard library only).

    python3 serve.py --model my_model.json            # http://127.0.0.1:8000

Endpoints (JSON errors everywhere, see /openapi.json):
    GET  /health            liveness, no auth
    GET  /                  endpoint index
    GET  /openapi.json      OpenAPI 3 description (importable into Postman)
    GET  /generate?prompt=  image (browser friendly)
    POST /generate          JSON -> PNG/BMP bytes, or JSON with base64
    POST /parse             how a prompt is understood
    GET  /model             info about the loaded trained model
    POST /train             upload a zip of images + captions (async job, needs --model)
    GET  /jobs/<id>         training progress and result

Safety defaults: binds to 127.0.0.1; refuses a non-loopback address without an API key;
Host-header check against DNS rebinding; cross-site browser requests (foreign Origin or
Sec-Fetch-Site: cross-site) cannot change state or render through GET /generate; request body, image size, unzip size and concurrency
limits; zip-slip / zip-bomb / symlink protection; no tracebacks in responses.
"""
import argparse
import base64
import copy
import hashlib
import hmac
import json
import mmap
import os
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
import traceback
import uuid
import zipfile
import zlib
from collections import OrderedDict
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .compose import MAX_SIZE, MIN_SIZE, choose_mode, render, text_warnings
from .imagefile import encode_bmp, encode_png
from .learn import (DEFAULT_GRID, IMAGE_EXTS, UNSUPPORTED_EXTS, LearnedModel, ModelError, Sample,
                    caption_words, load_dataset, train_model)
from .store import Store, grid_png, thumb_png
from .tokenizer import MAX_PROMPT_CHARS, parse

MB = 1024 * 1024
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")
STATE_CHANGING = ("POST", "PUT", "PATCH", "DELETE")
DEFAULT_PORTS = {"http": 80, "https": 443}


class ApiError(Exception):
    def __init__(self, status, code, message, headers=None):
        super().__init__(message)
        self.status, self.code, self.message, self.headers = status, code, message, headers or {}


@dataclass
class Config:
    host: str = "127.0.0.1"
    port: int = 8000
    model_path: str = None
    api_key: str = None
    max_size: int = 1024
    max_concurrent: int = 2
    queue_wait: float = 10.0          # seconds a request may wait for a render slot before 503
    max_json_bytes: int = 64 * 1024
    max_upload_bytes: int = 100 * MB
    max_unzipped_bytes: int = 300 * MB
    max_file_bytes: int = 64 * MB
    max_files: int = 20000
    max_image_pixels: int = 16_000_000  # per uploaded image: bounds decode RAM/time (a 4K or 12 MP photo fits)
    cors_origin: str = None
    quiet: bool = False
    db_path: str = None               # SQLite file for gallery / job history / dataset previews (None = off)
    gallery_max: int = 300            # pictures kept in the gallery (favourites are never dropped)


def is_loopback(host):
    return host in LOOPBACK_HOSTS or host.startswith("127.")


# ------------------------------------------------------------------ parameters
GEN_FIELDS = {"prompt", "size", "width", "height", "seed", "format", "learned", "response", "save"}
CREATE_FIELDS = GEN_FIELDS | {"temperature", "population", "generations", "alternatives", "max_seconds", "explore"}
IMAGINE_FIELDS = (GEN_FIELDS - {"prompt"}) | {"anchor", "temperature", "attempts", "population", "generations", "max_seconds"}
SCENE_FIELDS = {"prompt", "width", "height", "size", "seed", "accent", "mood", "text_zone", "variant", "niche", "format", "response", "quality", "use_model"}
SET_FIELDS = {"prompt", "count", "seed", "accent", "mood", "text_zone", "niche", "format", "response", "quality", "use_model"}
TRAIN_FIELDS = {"epochs", "lr", "l2", "val_frac", "seed", "fresh", "grid", "refit"}


def _int(src, name, default, lo, hi, from_text):
    v = src.get(name)
    if v is None:
        return default
    if from_text:
        try:
            v = int(str(v).strip())
        except ValueError:
            raise ApiError(400, "bad_parameter", "%s must be an integer" % name)
    elif type(v) is not int:
        raise ApiError(400, "bad_parameter", "%s must be an integer" % name)
    if not lo <= v <= hi:
        raise ApiError(400, "bad_parameter", "%s must be between %d and %d" % (name, lo, hi))
    return v


def _float(src, name, default, lo, hi, lo_open=False):
    v = src.get(name)
    if v is None:
        return default
    try:
        v = float(str(v).strip())
    except ValueError:
        raise ApiError(400, "bad_parameter", "%s must be a number" % name)
    if not (v == v) or v < lo or v > hi or (lo_open and v == lo):
        raise ApiError(400, "bad_parameter", "%s is out of range" % name)
    return v


def _bool(src, name, default):
    v = src.get(name)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    raise ApiError(400, "bad_parameter", "%s must be true or false" % name)


def parse_gen_params(src, cfg, from_text):
    unknown = sorted(set(src) - GEN_FIELDS)
    if unknown:
        raise ApiError(400, "unknown_field", "unknown field(s): %s (allowed: %s)" % (
            ", ".join(unknown), ", ".join(sorted(GEN_FIELDS))))
    prompt = src.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ApiError(400, "bad_parameter", "prompt is required (a non-empty string)")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ApiError(400, "bad_parameter", "prompt too long (max %d characters)" % MAX_PROMPT_CHARS)
    hi = min(cfg.max_size, MAX_SIZE)
    size = _int(src, "size", 512, MIN_SIZE, hi, from_text)
    out = {
        "prompt": prompt.strip(),
        "width": _int(src, "width", size, MIN_SIZE, hi, from_text),
        "height": _int(src, "height", size, MIN_SIZE, hi, from_text),
        "seed": _int(src, "seed", 0, 0, 2 ** 31 - 1, from_text),
        "format": str(src.get("format", "png")).lower(),
        "learned": str(src.get("learned", "auto")).lower(),
        "response": str(src.get("response", "binary")).lower(),
        "save": _bool(src, "save", False),
    }
    for key, allowed in (("format", ("png", "bmp")), ("learned", ("auto", "always", "blend", "off")),
                         ("response", ("binary", "base64"))):
        if out[key] not in allowed:
            raise ApiError(400, "bad_parameter", "%s must be one of: %s" % (key, ", ".join(allowed)))
    return out


def parse_creative_params(src, cfg, from_text, imagine):
    """Fields of POST /create (a prompt to improve) and POST /imagine (random mash-up, optional `anchor`)."""
    fields = IMAGINE_FIELDS if imagine else CREATE_FIELDS
    unknown = sorted(set(src) - fields)
    if unknown:
        raise ApiError(400, "unknown_field", "unknown field(s): %s (allowed: %s)" % (", ".join(unknown), ", ".join(sorted(fields))))
    base = dict(src)
    anchor = base.pop("anchor", None)
    if imagine:
        if anchor is not None and (not isinstance(anchor, str) or len(anchor) > 200):
            raise ApiError(400, "bad_parameter", "anchor must be a short string (max 200 characters)")
        base["prompt"] = (anchor or "").strip() or "x"          # validated by parse_gen_params, replaced below
    keys = {k: base.pop(k) for k in ("temperature", "population", "generations", "alternatives", "max_seconds", "attempts", "explore") if k in base}
    out = parse_gen_params(base, cfg, from_text)
    out.update(
        temperature=_float(keys, "temperature", 0.8 if imagine else 0.7, 0.0, 1.0),
        population=_int(keys, "population", 8 if not imagine else 6, 2, 16, from_text),
        generations=_int(keys, "generations", 3 if not imagine else 2, 0, 6, from_text),
        max_seconds=_float(keys, "max_seconds", 20.0, 0.5, 60.0))
    if imagine:
        out["anchor"] = (anchor or "").strip() or None
        out["attempts"] = _int(keys, "attempts", 12, 1, 30, from_text)
    else:
        out["alternatives"] = _int(keys, "alternatives", 3, 0, 5, from_text)
        out["explore"] = _int(keys, "explore", 0, 0, 500, from_text)
    return out


def _choice(src, name, default, allowed):
    v = src.get(name, default)
    if v is None:
        return default
    v = str(v).strip().lower()
    if v not in allowed:
        raise ApiError(400, "bad_parameter", "%s must be one of: %s" % (name, ", ".join(allowed)))
    return v


def parse_studio_params(src, cfg, from_text, is_set):
    """Fields of POST /scene (one premium niche picture) and POST /set (3-8 pictures for one site)."""
    fields = SET_FIELDS if is_set else SCENE_FIELDS
    unknown = sorted(set(src) - fields)
    if unknown:
        raise ApiError(400, "unknown_field", "unknown field(s): %s (allowed: %s)" % (", ".join(unknown), ", ".join(sorted(fields))))
    prompt = src.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ApiError(400, "bad_parameter", "prompt is required (a non-empty string)")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ApiError(400, "bad_parameter", "prompt too long (max %d characters)" % MAX_PROMPT_CHARS)
    out = {"prompt": prompt.strip(), "seed": _int(src, "seed", 0, 0, 2 ** 31 - 1, from_text),
           "mood": _choice(src, "mood", None, ("warm", "cool", "dark", "light")),
           "text_zone": _choice(src, "text_zone", "left" if is_set else None, ("left", "center", "bottom", "none")),
           "format": _choice(src, "format", "jpeg", ("jpeg", "png")), "quality": _int(src, "quality", 72, 20, 95, from_text),
           "use_model": _bool(src, "use_model", True)}
    if out["text_zone"] == "none":
        out["text_zone"] = None
    acc, niche = src.get("accent"), src.get("niche")
    for name, v in (("accent", acc), ("niche", niche)):
        if v is not None and (not isinstance(v, str) or len(v) > 60):
            raise ApiError(400, "bad_parameter", "%s must be a short string" % name)
    if acc:
        from .studio.palette import parse_color
        try:
            parse_color(acc)
        except ValueError as exc:
            raise ApiError(400, "bad_parameter", str(exc))
    out["accent"], out["niche"] = acc or None, niche or None
    if is_set:
        out["count"] = _int(src, "count", 6, 3, 8, from_text)
        out["response"] = _choice(src, "response", "zip", ("zip", "base64"))
    else:
        hi = max(cfg.max_size, 1600)
        size = _int(src, "size", 640, MIN_SIZE, hi, from_text)
        out["width"] = _int(src, "width", size, MIN_SIZE, hi, from_text)
        out["height"] = _int(src, "height", int(size * 0.625) if "width" not in src and "size" not in src else size, MIN_SIZE, hi, from_text)
        out["variant"] = _choice(src, "variant", "fit", ("fit", "close", "detail", "wide", "fit-flip", "close-flip", "detail-flip", "wide-flip"))
        out["response"] = _choice(src, "response", "binary", ("binary", "base64"))
    return out


def parse_train_params(src):
    unknown = sorted(set(src) - TRAIN_FIELDS - {"data"})
    if unknown:
        raise ApiError(400, "unknown_field", "unknown field(s): %s (allowed: data, %s)" % (
            ", ".join(unknown), ", ".join(sorted(TRAIN_FIELDS))))
    return {
        "epochs": _int(src, "epochs", 80, 1, 500, True),
        "lr": _float(src, "lr", 0.3, 0.0, 5.0, lo_open=True),
        "l2": _float(src, "l2", 1e-4, 0.0, 1.0),
        "val_frac": _float(src, "val_frac", 0.15, 0.0, 0.499),
        "seed": _int(src, "seed", 0, 0, 2 ** 31 - 1, True),
        "fresh": _bool(src, "fresh", False),
        "grid": _int(src, "grid", DEFAULT_GRID, 4, 64, True),
        "refit": _bool(src, "refit", True),
    }


# ------------------------------------------------------------------ uploads
def parse_multipart(path, boundary, workdir, max_parts=16, max_field=4096):
    """Parse a multipart/form-data body stored in `path`. Returns (fields, files)."""
    if not boundary or len(boundary) > 200:
        raise ApiError(400, "bad_multipart", "missing or invalid multipart boundary")
    delim = b"--" + boundary.encode("latin-1", "replace")
    fields, files = {}, {}
    with open(path, "rb") as fh:
        if os.fstat(fh.fileno()).st_size == 0:
            raise ApiError(400, "bad_multipart", "empty request body")
        mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            pos = mm.find(delim)
            if pos < 0:
                raise ApiError(400, "bad_multipart", "multipart boundary not found in body")
            parts = 0
            while True:
                pos += len(delim)
                if mm[pos:pos + 2] == b"--":
                    break
                if mm[pos:pos + 2] != b"\r\n":
                    raise ApiError(400, "bad_multipart", "malformed multipart body")
                pos += 2
                hdr_end = mm.find(b"\r\n\r\n", pos)
                if hdr_end < 0 or hdr_end - pos > 8192:
                    raise ApiError(400, "bad_multipart", "malformed multipart headers")
                raw_header = mm[pos:hdr_end]
                if delim in raw_header:
                    raise ApiError(400, "bad_multipart", "malformed multipart headers")
                header = raw_header.decode("utf-8", "replace")
                body_start = hdr_end + 4
                nxt = mm.find(b"\r\n" + delim, body_start)
                if nxt < 0:
                    raise ApiError(400, "bad_multipart", "multipart body is incomplete")
                parts += 1
                if parts > max_parts:
                    raise ApiError(400, "bad_multipart", "too many form parts")
                disp = next((ln for ln in header.split("\r\n") if ln.lower().startswith("content-disposition")), "")
                m_name = re.search(r'\bname="([^"]*)"', disp)
                m_file = re.search(r'\bfilename="([^"]*)"', disp)
                if not m_name:
                    raise ApiError(400, "bad_multipart", "form part without a name")
                if m_file is not None:
                    dest = os.path.join(workdir, "part%d" % parts)
                    with open(dest, "wb") as out:
                        for off in range(body_start, nxt, MB):
                            out.write(mm[off:min(nxt, off + MB)])
                    files[m_name.group(1)] = dest
                else:
                    if nxt - body_start > max_field:
                        raise ApiError(400, "bad_multipart", "form field too large")
                    fields[m_name.group(1)] = mm[body_start:nxt].decode("utf-8", "replace")
                pos = nxt + 2
        finally:
            mm.close()
    return fields, files


def _size_text(n):
    return "%d MB" % (n // MB) if n >= MB else "%d bytes" % n


def safe_extract(zip_path, dest, cfg):
    """Extract only images / caption files from an untrusted zip. Returns `dest`."""
    allowed = IMAGE_EXTS | UNSUPPORTED_EXTS | {".csv", ".json", ".txt"}
    try:
        zf = zipfile.ZipFile(zip_path)
    except (zipfile.BadZipFile, OSError):
        raise ApiError(400, "bad_zip", "the upload is not a valid zip file")
    real_dest = os.path.realpath(dest)
    with zf:
        entries = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            parts = [p for p in name.split("/") if p not in ("", ".")]
            if (not parts or name.startswith("/") or ".." in parts or re.match(r"^[A-Za-z]:", parts[0])
                    or "\x00" in name):
                raise ApiError(400, "unsafe_zip", "the zip contains an unsafe path: %r" % info.filename[:80])
            if parts[0] == "__MACOSX" or parts[-1].startswith("._") or parts[-1] == ".DS_Store":
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:      # symlink entry
                continue
            if info.flag_bits & 0x1:
                raise ApiError(400, "bad_zip", "encrypted zip files are not supported")
            entries.append((info, parts))
        if len(entries) > cfg.max_files:
            raise ApiError(413, "too_many_files", "the zip has more than %d files" % cfg.max_files)
        if entries and all(len(p) > 1 for _, p in entries) and len({p[0] for _, p in entries}) == 1:
            entries = [(i, p[1:]) for i, p in entries]                  # single wrapper folder: drop it
        total = 0
        for info, parts in entries:
            if os.path.splitext(parts[-1])[1].lower() not in allowed:
                continue
            out = os.path.realpath(os.path.join(real_dest, *parts))
            if not out.startswith(real_dest + os.sep):
                raise ApiError(400, "unsafe_zip", "the zip contains an unsafe path")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            written = 0
            try:
                with zf.open(info) as src, open(out, "wb") as dst:
                    while True:
                        chunk = src.read(MB)
                        if not chunk:
                            break
                        written += len(chunk)
                        total += len(chunk)
                        if written > cfg.max_file_bytes:
                            raise ApiError(413, "zip_too_large", "%r expands to more than the allowed %s per file" % (
                                info.filename[:80], _size_text(cfg.max_file_bytes)))
                        if total > cfg.max_unzipped_bytes:
                            raise ApiError(413, "zip_too_large", "the zip expands to more than the allowed %s in total" % (
                                _size_text(cfg.max_unzipped_bytes)))
                        dst.write(chunk)
            except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError, OSError) as exc:
                raise ApiError(400, "bad_zip", "the zip is corrupt or uses an unsupported feature (%s)" % type(exc).__name__)
    return dest


def _metrics(model, m):
    gain = None
    if m["val_mse"] is not None and m["baseline_val"]:
        gain = round(100.0 * (1 - m["val_mse"] / m["baseline_val"]), 1)
    return {"samples": m["samples"], "added": m["added"], "vocabulary": len(model.rows),
            "val_samples": m["val_samples"], "best_epoch": m["best_epoch"],
            "val_rmse": None if m["val_mse"] is None else round(m["val_mse"] ** 0.5 * 255, 2),
            "baseline_rmse": None if m["baseline_val"] is None else round(m["baseline_val"] ** 0.5 * 255, 2),
            "improvement_percent": gain}


# ------------------------------------------------------------------ training jobs
class Job:
    def __init__(self, params):
        self.id = uuid.uuid4().hex[:12]
        self.lock = threading.Lock()
        self.data = {"id": self.id, "status": "queued", "message": "", "epoch": 0, "epochs": params["epochs"],
                     "train_rmse": None, "val_rmse": None, "images_read": 0, "skipped_count": 0,
                     "skipped": [], "metrics": None, "error": None, "created": time.time(), "finished": None}

    def update(self, **kw):
        with self.lock:
            self.data.update(kw)

    def snapshot(self):
        with self.lock:
            d = copy.deepcopy(self.data)
        d["skipped"] = d["skipped"][:100]
        return d


class App:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()
        self.model = None
        self.render_slots = threading.BoundedSemaphore(cfg.max_concurrent)
        self.train_lock = threading.Lock()
        self.jobs = OrderedDict()
        self.host_check = is_loopback(cfg.host) and not cfg.api_key
        if cfg.model_path and os.path.exists(cfg.model_path):
            self.model = LearnedModel.load(cfg.model_path)
        self.store = Store(cfg.db_path, cfg.gallery_max) if cfg.db_path else None

    def log(self, msg):
        if not self.cfg.quiet:
            print("[pixelmath] " + msg, file=sys.stderr, flush=True)

    def get_model(self):
        with self.lock:
            return self.model

    def set_model(self, model):
        with self.lock:
            self.model = model

    def new_job(self, params, kind="train"):
        job = Job(params)
        job.kind, job.params = kind, {k: v for k, v in params.items() if k in TRAIN_FIELDS}
        with self.lock:
            self.jobs[job.id] = job
            while len(self.jobs) > 20:
                self.jobs.popitem(last=False)
        self.persist(job)
        return job

    def persist(self, job):
        """Remember a job in the database (never lets a database problem break training)."""
        if self.store is None:
            return
        try:
            self.store.save_job(job.snapshot(), job.kind, job.params)
        except Exception:
            self.log("could not save job %s to the database:\n%s" % (job.id, traceback.format_exc()))

    def start_training(self, tmpdir, zip_path, params):
        if not self.train_lock.acquire(blocking=False):
            running = next((j.id for j in reversed(self.jobs.values())
                            if j.snapshot()["status"] not in ("done", "error")), None)
            raise ApiError(409, "training_busy", "a training job is already running%s" % (
                " (job %s)" % running if running else ""))
        job = self.new_job(params)
        threading.Thread(target=self._run_job, args=(job, tmpdir, zip_path, params), daemon=True).start()
        return job

    def _run_job(self, job, tmpdir, zip_path, p):
        def fail(code, message):
            job.update(status="error", message=message, error={"code": code, "message": message},
                       finished=time.time())
        try:
            job.update(status="extracting", message="unpacking the zip")
            data_dir = safe_extract(zip_path, os.path.join(tmpdir, "data"), self.cfg)
            job.update(status="reading", message="reading images")
            current = self.get_model()
            model = LearnedModel(p["grid"]) if (p["fresh"] or current is None) else copy.deepcopy(current)
            extras = {} if self.store is not None else None
            samples, skipped, _sources = load_dataset(data_dir, model.grid, extras, self.cfg.max_image_pixels)
            job.update(images_read=len(samples), skipped_count=len(skipped),
                       skipped=[{"file": r, "reason": w} for r, w in skipped[:100]])
            if not samples and not (model.samples and not p["fresh"]):
                return fail("no_usable_data", "no usable (image, caption) pairs found in the zip")

            def log(ep, tr, va):
                if ep == 0:
                    job.update(status="training", message="refitting on all data")
                else:
                    job.update(epoch=ep, train_rmse=round(tr ** 0.5 * 255, 2),
                               val_rmse=None if va is None else round(va ** 0.5 * 255, 2))

            job.update(status="training", message="training")
            m = train_model(model, samples, p["epochs"], p["lr"], p["l2"], p["val_frac"], p["seed"], 8,
                            p["refit"], log)
            model.save(self.cfg.model_path)
            self.set_model(model)
            job.update(status="done", message="finished", finished=time.time(), metrics=_metrics(model, m))
            if extras is not None:
                self._remember_samples(job.id, model, extras)
        except ApiError as exc:
            fail(exc.code, exc.message)
        except (ModelError, OSError, ValueError) as exc:
            fail("training_failed", str(exc))
        except Exception:                                               # never kill the server thread silently
            self.log("training job %s crashed:\n%s" % (job.id, traceback.format_exc()))
            fail("internal_error", "internal error while training (see server log)")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            self.persist(job)
            self.train_lock.release()

    def _remember_samples(self, job_id, model, extras):
        keep = {s.id for s in model.samples}
        try:
            for sid, (name, prev) in extras.items():
                if sid in keep:
                    caption = next(s.caption for s in model.samples if s.id == sid)
                    self.store.add_dataset(sid, caption, job_id, name, encode_png(64, 64, prev))
        except Exception:
            self.log("could not save dataset previews:\n%s" % traceback.format_exc())

    # ---- dataset edits (delete images / change captions) = retrain on what is left
    def start_rebuild(self, remove, edits):
        if not self.train_lock.acquire(blocking=False):
            raise ApiError(409, "training_busy", "a training job is already running; wait for it to finish")
        params = parse_train_params({})
        job = self.new_job(params, "rebuild")
        threading.Thread(target=self._run_rebuild, args=(job, params, set(remove), dict(edits)), daemon=True).start()
        return job

    def _run_rebuild(self, job, p, remove, edits):
        try:
            current = self.get_model()
            if current is None:
                raise ModelError("there is no trained model to change")
            job.update(status="training", message="retraining on the remaining images")
            model = copy.deepcopy(current)
            kept, renamed, seen = [], {}, set()
            for smp in model.samples:
                if smp.id in remove:
                    continue
                if smp.id in edits:
                    new = Sample(hashlib.md5(edits[smp.id].encode("utf-8") + smp.thumb).hexdigest()[:12], edits[smp.id], smp.thumb)
                    renamed[smp.id] = new
                    smp = new
                if smp.id not in seen:
                    seen.add(smp.id)
                    kept.append(smp)
            if not kept:                                              # everything removed: the model is empty again
                self.set_model(None)
                if self.cfg.model_path and os.path.exists(self.cfg.model_path):
                    os.replace(self.cfg.model_path, self.cfg.model_path + ".bak")
                job.update(status="done", message="all images removed; the model was reset (old file kept as .bak)",
                           finished=time.time(), metrics={"samples": 0, "added": 0, "vocabulary": 0})
            else:
                model.samples = kept

                def log(ep, tr, va):
                    if ep:
                        job.update(epoch=ep, train_rmse=round(tr ** 0.5 * 255, 2), val_rmse=None if va is None else round(va ** 0.5 * 255, 2))
                m = train_model(model, [], p["epochs"], p["lr"], p["l2"], p["val_frac"], p["seed"], 8, p["refit"], log)
                model.save(self.cfg.model_path)
                self.set_model(model)
                job.update(status="done", message="finished", finished=time.time(), metrics=_metrics(model, m))
            if self.store is not None:
                self.store.remove_dataset(remove)
                for old, new in renamed.items():
                    self.store.rename_dataset(old, new.id, new.caption)
        except (ModelError, OSError, ValueError) as exc:
            job.update(status="error", message=str(exc), error={"code": "rebuild_failed", "message": str(exc)}, finished=time.time())
        except Exception:
            self.log("rebuild job %s crashed:\n%s" % (job.id, traceback.format_exc()))
            job.update(status="error", message="internal error (see server log)", finished=time.time(),
                       error={"code": "internal_error", "message": "internal error while retraining"})
        finally:
            self.persist(job)
            self.train_lock.release()


# ------------------------------------------------------------------ HTTP handler
ROUTES = {
    "/": {"GET": "get_index"},
    "/ui": {"GET": "get_ui"},
    "/ui/app.js": {"GET": "get_ui"},
    "/ui/style.css": {"GET": "get_ui"},
    "/health": {"GET": "get_health"},
    "/openapi.json": {"GET": "get_openapi"},
    "/generate": {"GET": "get_generate", "POST": "post_generate"},
    "/create": {"POST": "post_create"},
    "/imagine": {"POST": "post_imagine"},
    "/scene": {"POST": "post_scene"},
    "/set": {"POST": "post_set"},
    "/spec": {"POST": "post_spec"},
    "/spec/business": {"POST": "post_spec_business"},
    "/spec/businesses": {"GET": "get_spec_businesses"},
    "/niches": {"GET": "get_niches"},
    "/parse": {"POST": "post_parse"},
    "/model": {"GET": "get_model_info"},
    "/train": {"POST": "post_train"},
    "/jobs": {"GET": "get_jobs"},
    "/gallery": {"GET": "get_gallery", "DELETE": "delete_gallery"},
    "/dataset": {"GET": "get_dataset"},
    "/dataset/delete": {"POST": "post_dataset_delete"},
}
# paths with an id in them: (regex, {method: handler}, name used for the auth check)
DYNAMIC = (
    (re.compile(r"^/jobs/([A-Za-z0-9]{1,32})$"), {"GET": "get_job"}, "/jobs/<id>"),
    (re.compile(r"^/gallery/(\d{1,12})$"), {"GET": "get_gallery_item", "DELETE": "delete_gallery_item"}, "/gallery/<id>"),
    (re.compile(r"^/gallery/(\d{1,12})/(image|thumb)$"), {"GET": "get_gallery_blob"}, "/gallery/<id>/image"),
    (re.compile(r"^/gallery/(\d{1,12})/favourite$"), {"POST": "post_gallery_favourite"}, "/gallery/<id>/favourite"),
    (re.compile(r"^/dataset/([0-9a-f]{12})$"), {"DELETE": "delete_dataset_item"}, "/dataset/<id>"),
    (re.compile(r"^/dataset/([0-9a-f]{12})/image$"), {"GET": "get_dataset_image"}, "/dataset/<id>/image"),
    (re.compile(r"^/dataset/([0-9a-f]{12})/caption$"), {"POST": "post_dataset_caption"}, "/dataset/<id>/caption"),
)
OPEN_ROUTES = {"/health", "/openapi.json", "/", "/ui", "/ui/app.js", "/ui/style.css"}
IMAGE_MIME = {"png": "image/png", "bmp": "image/bmp"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PixelMath/" + __version__
    sys_version = ""
    timeout = 60

    def log_message(self, fmt, *args):          # replaced by our own one-line log
        pass

    def send_error(self, code, message=None, explain=None):
        """Malformed HTTP detected by the base class: answer in JSON like everything else."""
        self.close_connection = True
        try:
            from http import HTTPStatus
            msg = message or HTTPStatus(code).phrase
            self._json({"error": {"code": "http_%d" % code, "message": str(msg)[:200]}}, code)
        except OSError:
            pass

    # ---- plumbing
    @property
    def app(self):
        return self.server.app

    def _cors_headers(self):
        origin = self.app.cfg.cors_origin
        if not origin:
            return {}
        return {"Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Expose-Headers": "X-PixelMath-Mode, X-PixelMath-Seed, X-Render-Seconds",
                "Vary": "Origin"}

    def _send(self, status, body=b"", ctype="application/json", headers=None):
        self._status = status
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in {**self._cors_headers(), **(headers or {})}.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def _json(self, obj, status=200, headers=None):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", headers)

    def _error(self, exc):
        self._drain()
        self._json({"error": {"code": exc.code, "message": exc.message}}, exc.status, exc.headers)

    def _drain(self):
        """Read (a bounded amount of) an unread request body so the client can see our reply."""
        if getattr(self, "_body_read", True) or self.command != "POST":
            return
        try:
            left = min(int(self.headers.get("Content-Length") or 0), 2 * MB)
            self.connection.settimeout(2)
            while left > 0:
                data = self.rfile.read(min(65536, left))
                if not data:
                    break
                left -= len(data)
        except (OSError, ValueError):
            pass

    def _read_body(self, limit):
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise ApiError(411, "length_required", "Content-Length header is required")
        try:
            n = int(raw)
        except ValueError:
            raise ApiError(400, "bad_request", "invalid Content-Length")
        if n < 0:
            raise ApiError(400, "bad_request", "invalid Content-Length")
        if n > limit:
            raise ApiError(413, "body_too_large", "request body too large (max %d bytes)" % limit)
        data = self.rfile.read(n)
        self._body_read = True
        if len(data) != n:
            raise ApiError(400, "bad_request", "request body ended early")
        return data

    def _stream_body(self, path, limit):
        raw = self.headers.get("Content-Length")
        if raw is None:
            raise ApiError(411, "length_required", "Content-Length header is required")
        try:
            n = int(raw)
        except ValueError:
            raise ApiError(400, "bad_request", "invalid Content-Length")
        if n <= 0:
            raise ApiError(400, "bad_request", "empty request body")
        if n > limit:
            raise ApiError(413, "body_too_large", "upload too large (max %d MB)" % (limit // MB))
        left = n
        with open(path, "wb") as fh:
            while left > 0:
                chunk = self.rfile.read(min(MB, left))
                if not chunk:
                    raise ApiError(400, "bad_request", "request body ended early")
                fh.write(chunk)
                left -= len(chunk)
        self._body_read = True

    def _json_body(self):
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json" and not ctype.endswith("+json"):
            raise ApiError(415, "unsupported_media_type", "Content-Type must be application/json")
        raw = self._read_body(self.app.cfg.max_json_bytes)
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "invalid_json", "request body is not valid JSON")
        if not isinstance(obj, dict):
            raise ApiError(400, "invalid_json", "request body must be a JSON object")
        return obj

    def _check_host(self):
        if not self.app.host_check:
            return
        host = self.headers.get("Host")
        if not host:
            return
        m = re.match(r"^(\[[^\]]+\]|[^:]+)(?::\d+)?$", host.strip())
        name = m.group(1).strip("[]").lower() if m else ""
        if name not in LOOPBACK_HOSTS:
            raise ApiError(403, "bad_host", "unexpected Host header (protecting against DNS rebinding)")

    def _own_origin(self, origin):
        """True when an Origin header names this server as the browser reached it (same host and port as Host;
        http or https, so a TLS reverse proxy in front still counts as same-origin)."""
        try:
            o = urlsplit(origin.strip())
            o_port = o.port or DEFAULT_PORTS.get(o.scheme)
        except ValueError:
            return False
        if o.scheme not in DEFAULT_PORTS or not o.hostname or o.path not in ("", "/"):
            return False
        host = (self.headers.get("Host") or "").strip()
        if host:
            try:
                h = urlsplit("//" + host)
                return h.hostname == o.hostname and (h.port or DEFAULT_PORTS[o.scheme]) == o_port
            except ValueError:
                return False
        name, port = self.server.server_address[:2]
        return o_port == port and (o.hostname == name or (is_loopback(name) and o.hostname in LOOPBACK_HOSTS))

    def _check_origin(self, method, handler_path):
        """CSRF protection. A page on another site can make the browser POST here (a multipart form needs no
        preflight) or load GET /generate from <img src>. Browsers label such requests with Origin and/or
        Sec-Fetch-Site; requests without either (curl, Postman, other backends) are not affected."""
        cors = self.app.cfg.cors_origin
        origin = self.headers.get("Origin")
        cross = (self.headers.get("Sec-Fetch-Site") or "").strip().lower() == "cross-site"
        if method in STATE_CHANGING:
            if origin is not None:
                if self._own_origin(origin) or (cors and (cors == "*" or origin.strip().rstrip("/").lower()
                                                          == cors.strip().rstrip("/").lower())):
                    return
                raise ApiError(403, "cross_origin", "requests from another site are refused (Origin %r); "
                               "start the server with --cors-origin to allow one" % origin[:80])
            if cross:
                raise ApiError(403, "cross_origin", "cross-site requests are refused (Sec-Fetch-Site: cross-site)")
        elif method == "GET" and handler_path == "/generate" and cross and not cors:
            raise ApiError(403, "cross_origin", "cross-site image requests are refused; start the server with --cors-origin to allow them")

    def _check_auth(self):
        key = self.app.cfg.api_key
        if not key:
            return
        supplied = self.headers.get("X-API-Key")
        auth = self.headers.get("Authorization") or ""
        if not supplied and auth.lower().startswith("bearer "):
            supplied = auth[7:].strip()
        if not supplied or not hmac.compare_digest(supplied.encode("utf-8"), key.encode("utf-8")):
            raise ApiError(401, "unauthorized", "missing or invalid API key (send X-API-Key or Authorization: Bearer)",
                           {"WWW-Authenticate": 'Bearer realm="pixelmath"'})

    # ---- dispatch
    def _dispatch(self, method):
        t0 = time.time()
        self._status = 500
        self._body_read = method != "POST"
        parts = urlsplit(self.path)
        path = parts.path.rstrip("/") or "/"
        try:
            self._check_host()
            routes, handler_path = ROUTES.get(path), path
            self._args = ()
            if routes is None:
                for rx, table, name in DYNAMIC:
                    m = rx.match(path)
                    if m:
                        routes, handler_path, self._args = table, name, m.groups()
                        break
            if routes is None:
                raise ApiError(404, "not_found", "no such endpoint: %s" % path[:80])
            if method == "OPTIONS":
                self._send(204, b"", "text/plain", {"Allow": ", ".join(sorted(set(routes) | {"OPTIONS"}))})
                return
            if method not in routes:
                raise ApiError(405, "method_not_allowed", "%s is not allowed on %s" % (method, path),
                               {"Allow": ", ".join(sorted(routes))})
            self._check_origin(method, handler_path)
            if handler_path not in OPEN_ROUTES:
                self._check_auth()
            getattr(self, routes[method])(parts, path)
        except ApiError as exc:
            self._error(exc)
        except (BrokenPipeError, ConnectionResetError, socket.timeout, TimeoutError):
            self.close_connection = True
        except Exception:
            self.app.log("unhandled error on %s %s:\n%s" % (method, path, traceback.format_exc()))
            try:
                self._error(ApiError(500, "internal_error", "internal server error"))
            except OSError:
                pass
        finally:
            self.app.log("%s %s %s -> %s (%.0f ms)" % (self.client_address[0], method, path[:60], self._status,
                                                       (time.time() - t0) * 1000))

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_OPTIONS(self):
        self._dispatch("OPTIONS")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_HEAD(self):
        self._dispatch("HEAD")

    # ---- endpoints
    UI_FILES = {"/ui": ("index.html", "text/html; charset=utf-8"), "/ui/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/ui/style.css": ("style.css", "text/css; charset=utf-8")}
    UI_CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; "
              "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

    def get_ui(self, parts, path):
        """The bundled web interface (pixelmath/web). Static files only, no secrets: the API itself still checks the key."""
        name, ctype = self.UI_FILES[path]
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", name), "rb") as fh:
                body = fh.read()
        except OSError:
            raise ApiError(404, "not_found", "the web interface files are missing from this installation")
        self._send(200, body, ctype, {"Content-Security-Policy": self.UI_CSP, "Referrer-Policy": "no-referrer"})

    def get_index(self, parts, path):
        if "text/html" in (self.headers.get("Accept") or ""):          # a browser: show the interface
            self._send(302, b"", "text/plain", {"Location": "/ui"})
            return
        self._json({"name": "PixelMath", "version": __version__, "docs": "/openapi.json", "endpoints": {
            "GET /health": "liveness", "GET|POST /generate": "make an image", "POST /create": "creative mode (variations + critic + genetic search)",
            "POST /imagine": "random concept mash-up judged by the critic", "POST /parse": "explain a prompt",
            "GET /model": "trained model info", "POST /train": "upload zip to train (needs --model)",
            "GET /jobs/<id>": "training progress"}})

    def get_health(self, parts, path):
        m = self.app.get_model()
        self._json({"status": "ok", "version": __version__, "model_loaded": m is not None,
                    "training_enabled": bool(self.app.cfg.model_path), "auth_required": bool(self.app.cfg.api_key),
                    "database": self.app.store is not None})

    def get_openapi(self, parts, path):
        from .apidocs import openapi
        self._json(openapi(self.app.cfg))

    def get_generate(self, parts, path):
        q = {k: v[0] for k, v in parse_qs(parts.query, keep_blank_values=True, max_num_fields=20).items()}
        self._generate(parse_gen_params(q, self.app.cfg, True))

    def post_generate(self, parts, path):
        self._generate(parse_gen_params(self._json_body(), self.app.cfg, False))

    def _generate(self, p):
        app = self.app
        if not app.render_slots.acquire(timeout=app.cfg.queue_wait):
            raise ApiError(503, "busy", "the server is still busy after waiting %g s, retry shortly" % app.cfg.queue_wait,
                           {"Retry-After": "2"})
        try:
            model = app.get_model()
            t0 = time.time()
            try:
                canvas, parsed, mode = render(p["prompt"], p["width"], p["height"], p["seed"], model, p["learned"])
            except ValueError as exc:
                raise ApiError(400, "bad_parameter", str(exc))
            secs = round(time.time() - t0, 3)
        finally:
            app.render_slots.release()
        self._deliver(canvas, p, mode, secs, text_warnings(parsed),
                      {"known_words": model.known_words(p["prompt"]) if model else []},
                      record={"kind": "plain", "prompt": p["prompt"], "prompt_used": None})

    def _deliver(self, canvas, p, mode, secs, warn, extra_json, extra_headers=None, seed=None, record=None):
        rgb = canvas.to_rgb_bytes()
        data = (encode_png if p["format"] == "png" else encode_bmp)(p["width"], p["height"], rgb)
        mime = IMAGE_MIME[p["format"]]
        seed = p["seed"] if seed is None else seed
        gallery_id = None
        if p.get("save") and self.app.store is not None and record is not None:
            try:
                params = {k: p[k] for k in ("size", "width", "height", "learned", "temperature", "population", "generations", "explore",
                                           "attempts", "anchor") if k in p}
                creation = extra_json.get("creation")
                gallery_id = self.app.store.add_image(record["kind"], record["prompt"], record.get("prompt_used"), seed, mode,
                                                      p["width"], p["height"], params, creation, mime, data,
                                                      thumb_png(p["width"], p["height"], rgb))
            except Exception:
                self.app.log("could not save to the gallery:\n%s" % traceback.format_exc())
        if p["response"] == "base64":
            self._json({"image_base64": base64.b64encode(data).decode("ascii"), "mime": mime,
                        "width": p["width"], "height": p["height"], "seed": seed, "mode": mode,
                        "render_seconds": secs, "warnings": warn, **({"gallery_id": gallery_id} if gallery_id else {}), **extra_json})
            return
        self._send(200, data, mime, {"X-PixelMath-Mode": mode, "X-PixelMath-Seed": str(seed),
                                     "X-Render-Seconds": str(secs), **({"X-PixelMath-Warning": warn[0]} if warn else {}),
                                     **({"X-PixelMath-Gallery-Id": str(gallery_id)} if gallery_id else {}),
                                     **(extra_headers or {}),
                                     "Content-Disposition": 'inline; filename="pixelmath.%s"' % p["format"]})

    def get_niches(self, parts, path):
        from .studio.api import list_niches
        self._json({"niches": list_niches()})

    def _studio_slot(self):
        app = self.app
        if not app.render_slots.acquire(timeout=app.cfg.queue_wait):
            raise ApiError(503, "busy", "the server is still busy after waiting %g s, retry shortly" % app.cfg.queue_wait, {"Retry-After": "2"})

    def post_scene(self, parts, path):
        from .studio.api import scene
        p = parse_studio_params(self._json_body(), self.app.cfg, False, False)
        self._studio_slot()
        try:
            t0 = time.time()
            try:
                res = scene(p["prompt"], p["width"], p["height"], p["seed"], p["accent"], p["mood"], p["text_zone"], p["variant"], p["niche"],
                            fmt=p["format"], quality=p["quality"], model=self.app.get_model() if p["use_model"] else None)
            except ValueError as exc:
                raise ApiError(400, "bad_parameter", str(exc))
            secs = round(time.time() - t0, 3)
        finally:
            self.app.render_slots.release()
        rep, mime = res.report, "image/jpeg" if p["format"] == "jpeg" else "image/png"
        if p["response"] == "base64":
            self._json({"image_base64": base64.b64encode(res.data).decode("ascii"), "mime": mime, "width": p["width"], "height": p["height"],
                        "render_seconds": secs, "report": rep})
            return
        self._send(200, res.data, mime, {"X-PixelMath-Niche": str(rep["niche"]), "X-PixelMath-Fallback": str(rep["fallback"]).lower(),
                                         "X-PixelMath-Redrawn": str(rep["redrawn"]), "X-PixelMath-Seed": str(rep["seed"]),
                                         "X-PixelMath-Text-Color": str(rep["text_color"]), "X-Render-Seconds": str(secs),
                                         "Content-Disposition": 'inline; filename="scene.%s"' % ("jpg" if p["format"] == "jpeg" else "png")})

    def post_set(self, parts, path):
        import io
        from .studio.api import make_set
        p = parse_studio_params(self._json_body(), self.app.cfg, False, True)
        self._studio_slot()
        try:
            t0 = time.time()
            try:
                results, rep = make_set(p["prompt"], p["count"], p["seed"], p["accent"], p["mood"], p["text_zone"], p["niche"], fmt=p["format"],
                                        quality=p["quality"], model=self.app.get_model() if p["use_model"] else None)
            except ValueError as exc:
                raise ApiError(400, "bad_parameter", str(exc))
            secs = round(time.time() - t0, 3)
        finally:
            self.app.render_slots.release()
        ext = "jpg" if p["format"] == "jpeg" else "png"
        tile = 0
        names = []
        for r in results:
            role = r.report["role"]
            tile += role == "tile"
            names.append({"hero": "hero", "about": "about"}.get(role) or "tile-%d" % tile)
            r.report["file"] = "%s.%s" % (names[-1], ext)
        if p["response"] == "base64":
            self._json({"report": rep, "images": [{"file": r.report["file"], "role": r.report["role"], "width": r.canvas.w, "height": r.canvas.h,
                                                   "mime": "image/jpeg" if ext == "jpg" else "image/png",
                                                   "image_base64": base64.b64encode(r.data).decode("ascii")} for r in results]})
            return
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
            for r in results:
                z.writestr(r.report["file"], r.data)
            z.writestr("report.json", json.dumps(rep, indent=2, ensure_ascii=False))
        self._send(200, buf.getvalue(), "application/zip", {"X-PixelMath-Niche": str(rep["niche"]), "X-PixelMath-Fallback": str(rep["fallback"]).lower(),
                                                              "X-PixelMath-Redrawn": str(rep["redrawn"]), "X-Render-Seconds": str(secs),
                                                              "Content-Disposition": 'attachment; filename="site-pictures.zip"'})

    def _spec_available(self):
        from .studio.spec import available
        if not available():
            raise ApiError(501, "spec_unavailable", "the picture spec's data file (spec_data.json) is missing from this installation: reinstall "
                           "the package or set PIXELMATH_SPEC_DIR to a folder with spec_data.json; use POST /scene or POST /set")

    def get_spec_businesses(self, parts, path):
        from .studio.spec import businesses
        self._spec_available()
        self._json({"businesses": [{"id": b["id"], "name": b["name"], "niche": b["niche"], "palettes": b["palettes"]} for b in businesses()]})

    def _spec_fields(self, body, allowed):
        extra = sorted(set(body) - allowed)
        if extra:
            raise ApiError(400, "bad_parameter", "unknown field(s): %s" % ", ".join(extra))
        fmt = body.get("format", "jpeg")
        if fmt not in ("jpeg", "png"):
            raise ApiError(400, "bad_parameter", "format must be jpeg or png")
        seed = body.get("seed", 0)
        if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2 ** 31:
            raise ApiError(400, "bad_parameter", "seed must be an integer 0..2147483647")
        return fmt, seed

    def post_spec(self, parts, path):
        """One picture from the picture spec: {prompt, slot?, seed?, accent?, bg?, format?, response?}."""
        from .studio.spec import render
        body = self._json_body()
        self._spec_available()
        fmt, seed = self._spec_fields(body, {"prompt", "slot", "seed", "accent", "bg", "format", "response", "niche", "design_style"})
        prompt = body.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
            raise ApiError(400, "bad_parameter", "prompt must be a non-empty string (max 2000 characters)")
        self._studio_slot()
        try:
            t0 = time.time()
            try:
                res = render(prompt, slot=body.get("slot"), seed=seed, accent=body.get("accent"), bg=body.get("bg"), fmt=fmt, niche=body.get("niche"),
                             design_style=body.get("design_style"))
            except ValueError as exc:
                raise ApiError(400, "bad_parameter", str(exc))
            secs = round(time.time() - t0, 3)
        finally:
            self.app.render_slots.release()
        rep, mime = res.report, "image/jpeg" if fmt == "jpeg" else "image/png"
        if body.get("response") == "base64":
            self._json({"image_base64": base64.b64encode(res.data).decode("ascii"), "mime": mime, "width": rep["size"][0], "height": rep["size"][1],
                        "render_seconds": secs, "report": rep})
            return
        self._send(200, res.data, mime, {"X-PixelMath-Niche": str(rep.get("niche")), "X-PixelMath-Slot": str(rep["slot"]), "X-PixelMath-Size": "%dx%d" % tuple(rep["size"]),
                                         "X-PixelMath-Fallback": str(bool(rep.get("fallback"))).lower(), "X-Render-Seconds": str(secs),
                                         "Content-Disposition": 'inline; filename="%s.%s"' % (rep["slot"], "jpg" if fmt == "jpeg" else "png")})

    def post_spec_business(self, parts, path):
        """All 20 pictures of one spec business as a zip: {business: id, palette?: 0|1, seed?}. Takes about a minute."""
        import io
        import tempfile
        from .studio.spec import businesses, render_business, spec_prompts
        body = self._json_body()
        self._spec_available()
        fmt, seed = self._spec_fields(body, {"business", "palette", "seed", "format"})
        ids = {b["id"] for b in businesses()}
        if body.get("business") not in ids:
            raise ApiError(400, "bad_parameter", "business must be one of the spec's ids (GET /spec/businesses)")
        pal = body.get("palette", 0)
        if not isinstance(pal, int) or isinstance(pal, bool) or not 0 <= pal <= 5:
            raise ApiError(400, "bad_parameter", "palette must be an integer 0..5")
        try:
            prompts = spec_prompts(body["business"])
        except FileNotFoundError:
            raise ApiError(501, "spec_prompts_missing", "this installation has no spec prompt list (spec_prompts.json next to "
                           "spec_data.json); use POST /spec per picture")
        self._studio_slot()
        try:
            t0 = time.time()
            with tempfile.TemporaryDirectory() as d:
                man = render_business(body["business"], d, palette_index=pal, seed=seed, fmt=fmt, prompts=prompts)
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
                    for it in man["items"]:
                        with open(os.path.join(d, it["file"]), "rb") as fh:
                            z.writestr(it["file"], fh.read())
                    z.writestr("manifest.json", json.dumps(man, indent=2, ensure_ascii=False))
            secs = round(time.time() - t0, 3)
        finally:
            self.app.render_slots.release()
        self._send(200, buf.getvalue(), "application/zip", {"X-PixelMath-Niche": str(man["niche"]), "X-Render-Seconds": str(secs),
                                                              "Content-Disposition": 'attachment; filename="%s.zip"' % body["business"]})

    def post_create(self, parts, path):
        self._creative(parse_creative_params(self._json_body(), self.app.cfg, False, False), False)

    def post_imagine(self, parts, path):
        self._creative(parse_creative_params(self._json_body(), self.app.cfg, True, True), True)

    def _creative(self, p, imagine):
        """Several renders plus a critic and a genetic search: one request holds one render slot for up to max_seconds."""
        from urllib.parse import quote
        from . import creative
        app = self.app
        if not app.render_slots.acquire(timeout=app.cfg.queue_wait):
            raise ApiError(503, "busy", "the server is still busy after waiting %g s, retry shortly" % app.cfg.queue_wait,
                           {"Retry-After": "2"})
        try:
            model = app.get_model()
            t0 = time.time()
            small = min(160, max(32, min(p["width"], p["height"]) // 2))
            try:
                if imagine:
                    made, _ = creative.imagine(p["temperature"], p["seed"], p["attempts"], small, p["width"], p["anchor"], True, model,
                                               p["learned"], p["population"], p["generations"], max_seconds=p["max_seconds"],
                                               final_height=p["height"])
                else:
                    made = creative.evolve(p["prompt"], p["temperature"], p["population"], p["generations"], p["seed"], small,
                                           p["width"], model, p["learned"], max_seconds=p["max_seconds"],
                                           alternatives=p["alternatives"], final_height=p["height"], explore=p["explore"])
            except ValueError as exc:
                raise ApiError(400, "bad_parameter", str(exc))
            secs = round(time.time() - t0, 3)
        finally:
            app.render_slots.release()
        self._deliver(made.canvas, p, made.mode, secs, text_warnings(made.parsed), {"creation": made.to_dict()},
                      {"X-PixelMath-Prompt": quote(made.prompt, safe=" ,")[:400], "X-PixelMath-Score": "%.3f" % made.score},
                      seed=made.seed, record={"kind": "imagine" if imagine else "creative",
                                              "prompt": p.get("anchor") or "" if imagine else p["prompt"], "prompt_used": made.prompt})

    def post_parse(self, parts, path):
        body = self._json_body()
        unknown = sorted(set(body) - {"prompt"})
        if unknown:
            raise ApiError(400, "unknown_field", "unknown field(s): %s (allowed: prompt)" % ", ".join(unknown))
        prompt = body.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ApiError(400, "bad_parameter", "prompt is required (a non-empty string)")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise ApiError(400, "bad_parameter", "prompt too long (max %d characters)" % MAX_PROMPT_CHARS)
        parsed = parse(prompt)
        model = self.app.get_model()
        self._json({
            "mode": choose_mode(parsed), "time": parsed.time, "flags": sorted(parsed.flags),
            "entities": [{"kind": e.kind, "name": e.name, "count": e.count, "size": e.size, "position": e.position,
                          "color": None if e.color is None else "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in e.color)}
                         for e in parsed.entities],
            "not_in_lexicon": parsed.unknown_words,
            "model_knows": model.known_words(prompt) if model else []})

    def get_model_info(self, parts, path):
        m = self.app.get_model()
        if m is None:
            self._json({"loaded": False, "training_enabled": bool(self.app.cfg.model_path)})
            return
        top = sorted(m.rows, key=lambda w: (-m.doc_freq.get(w, 0), w))[:20]
        self._json({"loaded": True, "grid": m.grid, "samples": len(m.samples), "vocabulary": len(m.rows),
                    "meta": m.meta, "training_enabled": bool(self.app.cfg.model_path),
                    "top_words": [{"word": w, "captions": m.doc_freq.get(w, 0),
                                   "color": "#%02x%02x%02x" % m.word_color(w)} for w in top]})

    def post_train(self, parts, path):
        app = self.app
        if not app.cfg.model_path:
            raise ApiError(403, "training_disabled", "training is disabled: start the server with --model PATH")
        ctype_header = self.headers.get("Content-Type") or ""
        ctype = ctype_header.split(";")[0].strip().lower()
        params = {k: v[0] for k, v in parse_qs(parts.query, keep_blank_values=True, max_num_fields=20).items()}
        if ctype not in ("multipart/form-data", "application/zip", "application/x-zip-compressed",
                         "application/octet-stream"):
            raise ApiError(415, "unsupported_media_type",
                           "send multipart/form-data (field 'data' = zip file) or a raw application/zip body")
        tmpdir = tempfile.mkdtemp(prefix="pixelmath-upload-")
        handed_over = False
        try:
            body_path = os.path.join(tmpdir, "body")
            self._stream_body(body_path, app.cfg.max_upload_bytes)
            if ctype == "multipart/form-data":
                m = re.search(r'boundary=(?:"([^"]+)"|([^;\s]+))', ctype_header, re.I)
                boundary = (m.group(1) or m.group(2)) if m else None
                fields, files = parse_multipart(body_path, boundary, tmpdir)
                if "data" not in files:
                    raise ApiError(400, "missing_file", "multipart field 'data' (the zip file) is required")
                params.update(fields)
                zip_path = files["data"]
            else:
                zip_path = body_path
            p = parse_train_params(params)
            if not zipfile.is_zipfile(zip_path):
                raise ApiError(400, "bad_zip", "the upload is not a valid zip file")
            job = app.start_training(tmpdir, zip_path, p)
            handed_over = True
        finally:
            if not handed_over:
                shutil.rmtree(tmpdir, ignore_errors=True)
        self._json({"job_id": job.id, "status": "queued", "status_url": "/jobs/%s" % job.id}, 202,
                   {"Location": "/jobs/%s" % job.id})

    # ---- jobs (live ones from memory, older ones from the database)
    def get_job(self, parts, path):
        jid = self._args[0]
        job = self.app.jobs.get(jid)
        if job is not None:
            self._json(job.snapshot())
            return
        old = self.app.store.get_job(jid) if self.app.store else None
        if old is None:
            raise ApiError(404, "not_found", "no such job (without a database the server only keeps the last 20)")
        self._json(old)

    def get_jobs(self, parts, path):
        with self.app.lock:
            live = {j.id: j.snapshot() for j in self.app.jobs.values()}
        rows = []
        if self.app.store:
            rows = [r for r in self.app.store.list_jobs(30) if r["id"] not in live]
        mem = [dict(v, kind=self.app.jobs[k].kind) for k, v in live.items()]
        jobs = sorted(mem + rows, key=lambda j: -(j.get("created") or 0))
        for j in jobs:
            j["skipped"] = (j.get("skipped") or [])[:20]
        self._json({"jobs": jobs})

    # ---- gallery
    def _need_store(self):
        if self.app.store is None:
            raise ApiError(404, "no_database", "this server was started without a database (use --db PATH, or python3 app.py)")
        return self.app.store

    def _query(self, parts):
        return {k: v[0] for k, v in parse_qs(parts.query, keep_blank_values=True, max_num_fields=20).items()}

    def get_gallery(self, parts, path):
        store, q = self._need_store(), self._query(parts)
        text = q.get("q", "").strip()
        if len(text) > 100:
            raise ApiError(400, "bad_parameter", "q is too long")
        items, total = store.list_images(_int(q, "limit", 48, 1, 200, True), _int(q, "offset", 0, 0, 10 ** 9, True),
                                         _bool(q, "favourites", False), text or None)
        self._json({"items": items, "total": total})

    def get_gallery_item(self, parts, path):
        item = self._need_store().get_image(int(self._args[0]))
        if item is None:
            raise ApiError(404, "not_found", "no such picture")
        self._json(item)

    def get_gallery_blob(self, parts, path):
        got = self._need_store().get_blob(int(self._args[0]), "image" if self._args[1] == "image" else "thumb")
        if got is None:
            raise ApiError(404, "not_found", "no such picture")
        self._send(200, got[1], got[0])

    def post_gallery_favourite(self, parts, path):
        body = self._json_body()
        if set(body) - {"favourite"} or not isinstance(body.get("favourite"), bool):
            raise ApiError(400, "bad_parameter", 'send {"favourite": true or false}')
        if not self._need_store().set_favourite(int(self._args[0]), body["favourite"]):
            raise ApiError(404, "not_found", "no such picture")
        self._json({"id": int(self._args[0]), "favourite": body["favourite"]})

    def delete_gallery_item(self, parts, path):
        if not self._need_store().delete_image(int(self._args[0])):
            raise ApiError(404, "not_found", "no such picture")
        self._json({"deleted": 1})

    def delete_gallery(self, parts, path):
        q = self._query(parts)
        n = self._need_store().clear_gallery(_bool(q, "keep_favourites", True))
        self._json({"deleted": n})

    # ---- dataset manager: what the model was trained on
    def get_dataset(self, parts, path):
        q = self._query(parts)
        text = q.get("q", "").strip().lower()
        limit, offset = _int(q, "limit", 60, 1, 200, True), _int(q, "offset", 0, 0, 10 ** 9, True)
        model = self.app.get_model()
        if model is None:
            self._json({"total": 0, "items": [], "grid": None})
            return
        rows = self.app.store.dataset_rows() if self.app.store else {}
        items = []
        for smp in model.samples:
            r = rows.get(smp.id) or {}
            if text and text not in smp.caption.lower() and text not in (r.get("source_name") or "").lower():
                continue
            items.append({"id": smp.id, "caption": smp.caption, "added": r.get("added"), "file": r.get("source_name"),
                          "job_id": r.get("job_id"), "original_preview": bool(r.get("has_preview"))})
        items.sort(key=lambda i: (-(i["added"] or 0), i["caption"], i["id"]))
        self._json({"total": len(items), "items": items[offset:offset + limit], "grid": model.grid})

    def get_dataset_image(self, parts, path):
        sid = self._args[0]
        png = self.app.store.dataset_preview(sid) if self.app.store else None
        if png is None:
            model = self.app.get_model()
            smp = next((x for x in model.samples if x.id == sid), None) if model else None
            if smp is None:
                raise ApiError(404, "not_found", "no such trained image")
            png = grid_png(smp.thumb, model.grid, 8)            # only the model's own coarse colour grid is known
        self._send(200, png, "image/png")

    def _rebuild(self, remove, edits):
        model = self.app.get_model()
        if model is None:
            raise ApiError(404, "no_model", "there is no trained model")
        have = {smp.id for smp in model.samples}
        remove, edits = {i for i in remove if i in have}, {i: c for i, c in edits.items() if i in have}
        if not remove and not edits:
            raise ApiError(404, "not_found", "none of those images are in the trained model")
        job = self.app.start_rebuild(remove, edits)
        self._json({"job_id": job.id, "status": "queued", "status_url": "/jobs/%s" % job.id, "removed": len(remove),
                    "edited": len(edits), "remaining": len(have) - len(remove)}, 202, {"Location": "/jobs/%s" % job.id})

    def delete_dataset_item(self, parts, path):
        self._rebuild({self._args[0]}, {})

    def post_dataset_delete(self, parts, path):
        body = self._json_body()
        ids = body.get("ids")
        if set(body) - {"ids"} or not isinstance(ids, list) or not ids or len(ids) > 20000 or not all(
                isinstance(i, str) and re.fullmatch(r"[0-9a-f]{12}", i) for i in ids):
            raise ApiError(400, "bad_parameter", '"ids" must be a non-empty list of image ids (from GET /dataset)')
        self._rebuild(set(ids), {})

    def post_dataset_caption(self, parts, path):
        body = self._json_body()
        cap = body.get("caption")
        if set(body) - {"caption"} or not isinstance(cap, str) or not caption_words(cap) or len(cap) > 200:
            raise ApiError(400, "bad_parameter", '"caption" must be 1-200 characters with at least one real word')
        self._rebuild(set(), {self._args[0]: cap.strip()})


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 32

    def handle_error(self, request, client_address):      # drop noisy socket tracebacks
        pass

    def server_close(self):
        super().server_close()
        store = getattr(getattr(self, "app", None), "store", None)
        if store is not None:
            store.close()


class _Server6(_Server):
    address_family = socket.AF_INET6


def create_server(cfg):
    """Build (but do not start) the HTTP server. `server.app` holds the shared state."""
    if not is_loopback(cfg.host) and not cfg.api_key:
        raise ValueError("refusing to listen on %s without an API key (use --api-key or PIXELMATH_API_KEY)" % cfg.host)
    if cfg.max_size < MIN_SIZE or cfg.max_size > MAX_SIZE:
        raise ValueError("max_size must be between %d and %d" % (MIN_SIZE, MAX_SIZE))
    app = App(cfg)
    cls = _Server6 if ":" in cfg.host else _Server
    httpd = cls((cfg.host, cfg.port), Handler)
    httpd.app = app
    return httpd


def main(argv=None):
    ap = argparse.ArgumentParser(prog="serve.py", description="PixelMath HTTP API (stdlib only).")
    ap.add_argument("--host", default="127.0.0.1", help="default 127.0.0.1 (this machine only)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", help="model file to load; also enables POST /train (created on first training)")
    ap.add_argument("--api-key", default=os.environ.get("PIXELMATH_API_KEY"),
                    help="require this key (X-API-Key header). Prefer the PIXELMATH_API_KEY env var")
    ap.add_argument("--max-size", type=int, default=1024, help="largest width/height accepted (default 1024, hard max 2048)")
    ap.add_argument("--max-concurrent", type=int, default=2, help="simultaneous renders; others wait in a queue")
    ap.add_argument("--queue-wait", type=float, default=10.0, help="seconds a request waits for a free slot before 503")
    ap.add_argument("--max-upload-mb", type=int, default=100)
    ap.add_argument("--max-unzipped-mb", type=int, default=300)
    ap.add_argument("--db", help="SQLite file for the gallery, training history and dataset previews (default: off)")
    ap.add_argument("--gallery-max", type=int, default=300, help="pictures kept in the gallery (favourites are kept)")
    ap.add_argument("--cors-origin", help="allow browser calls from this origin (or *)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    cfg = Config(host=args.host, port=args.port, model_path=args.model, api_key=args.api_key or None,
                 max_size=args.max_size, max_concurrent=max(1, args.max_concurrent), queue_wait=max(0.0, args.queue_wait),
                 max_upload_bytes=args.max_upload_mb * MB, max_unzipped_bytes=args.max_unzipped_mb * MB,
                 cors_origin=args.cors_origin, quiet=args.quiet, db_path=args.db, gallery_max=args.gallery_max)
    try:
        httpd = create_server(cfg)
    except (ValueError, ModelError) as exc:
        print("serve.py: error: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("serve.py: error: cannot listen on %s:%d (%s)" % (cfg.host, cfg.port, exc.strerror or exc), file=sys.stderr)
        return 1
    host, port = httpd.server_address[:2]
    model = httpd.app.model
    print("PixelMath API %s on http://%s:%d" % (__version__, "[%s]" % host if ":" in host else host, port))
    print("  auth:     %s" % ("API key required (X-API-Key)" if cfg.api_key else "none (local use only)"))
    print("  model:    %s" % (("%s (%d samples, %d words)" % (cfg.model_path, len(model.samples), len(model.rows)))
                              if model else (cfg.model_path + " (will be created by /train)" if cfg.model_path else "none")))
    print("  training: %s" % ("enabled (POST /train)" if cfg.model_path else "disabled (start with --model PATH)"))
    print("  limits:   image <= %d px, %d concurrent renders (others queue up to %g s), upload <= %d MB" % (
        cfg.max_size, cfg.max_concurrent, cfg.queue_wait, cfg.max_upload_bytes // MB))
    print("  database: %s" % (cfg.db_path or "none (gallery and job history are off)"))
    print("  docs:     http://%s:%d/openapi.json   (Ctrl-C to stop)" % (host, port), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
