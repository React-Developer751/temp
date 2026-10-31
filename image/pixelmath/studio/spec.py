"""The owner's picture spec: "<subject>, for a <business> website. <STYLE LINE>. Palette: accent #x on #y." -> a picture of the right size for its slot.

The spec (Image-AI-training.pdf, shipped as spec_data.json + spec_prompts.json next to this module) lists 99 businesses and 20 generic business types,
with the pictures every website asks for: hero 1600x900 (subject right or centre, empty left for the headline), about 1200x900, gallery 900x900,
card 800x600, team portrait 600x600 (illustrated character, shoulders up) and a background texture 1600x900 (no subject), all with no text, letters,
numbers or logos and one palette (accent on background). $PIXELMATH_SPEC_DIR (a folder with spec_data.json, and spec_prompts.json or
image_ai_spec.json) replaces the shipped data; when the data files are missing every function here raises SpecUnavailable (the server answers 501).

    from pixelmath.studio.spec import render, render_business
    res = render("Termite drilling (pest control), for a pest control website. Palette: accent #1565c0 on #f5f6f7.", slot="gallery-2", fmt="jpeg")
    res.data, res.report              # JPEG bytes and the report (niche, how it was found, palette, mood, variant, bytes ...)
    render_business("pest_control", "out/pest_control")      # all 20 pictures of a business + manifest.json

The subject text picks nothing by itself: the business named in "for a <business> website" decides the scene (an exact name from the spec, else the
trained prompt matcher), and the slot decides size, camera and text zone. The studio draws one illustrated scene per business, so a gallery picture
shows the business's real props from a different camera, not the exact object named in the caption.
"""
import json
import os
import re
import time
from dataclasses import dataclass

from . import post
from .api import SceneResult, _encode, scene
from .match import match_niche
from .niches import NICHES, load_all
from .palette import make_palette, parse_color
from .portrait import render_portrait
from .stage import Stage

SLOT_SIZES = {"hero": (1600, 900), "about": (1200, 900), "gallery": (900, 900), "card": (800, 600), "team": (600, 600), "background": (1600, 900)}
SLOT_BYTES = {"hero": 105000, "about": 70000, "gallery": 56000, "card": 38000, "team": 30000, "background": 40000}
HERO_VARIANTS = ("fit", "fit", "close")
GALLERY_VARIANTS = ("close", "detail", "wide", "fit-flip", "close-flip", "detail-flip")
# the same business needs 16 different scene pictures from 8 camera variants: repeats get another zoom / pan (view) so no two crops are alike
CARD_VARIANTS = ("wide-flip", "close", "detail-flip", "fit-flip", "fit", "close-flip")
VIEWS = {"hero-2": (1.10, 0.03, 0.0), "about": (1.10, 0.06, 0.0), "card-2": (0.90, 0.12, 0.0), "card-3": (0.85, -0.10, 0.03), "card-4": (1.12, -0.10, 0.0), "card-5": (1.18, 0.14, 0.02),
         "card-6": (0.88, -0.12, 0.0), "gallery-5": (0.90, 0.10, 0.0), "gallery-6": (1.15, -0.06, 0.0)}
RETRY_VIEWS = ((1.0, 0.0, 0.0), (1.14, 0.08, 0.0), (0.88, -0.08, 0.03), (1.22, 0.12, -0.03))
STYLE_LINE = ("friendly flat illustration, clean vector shapes, soft shading, one clear subject, rich but harmonious colours, no text, no letters, "
              "no logo, no watermark, no real brand, no real person's face")
UNSUPPORTED_STYLES = ("photo", "photorealistic", "3d render", "3d ", "sketch", "line art", "watercolor", "watercolour", "oil painting")
KIND_SEED = {"hero": 0, "about": 1000, "gallery": 2000, "card": 3000, "team": 4000, "background": 5000}
MOTIFS = ("dots", "waves", "rings", "grid", "diagonals")
_DATA = None
SPEC_DIR = os.path.dirname(os.path.abspath(__file__))            # spec_data.json and spec_prompts.json ship next to this module


class SpecUnavailable(FileNotFoundError):
    """The spec's data files (spec_data.json) are missing from this installation."""


def spec_dir():
    """Folder of the spec: $PIXELMATH_SPEC_DIR, else the package's own (None when neither has spec_data.json)."""
    for d in (os.environ.get("PIXELMATH_SPEC_DIR"), SPEC_DIR):
        if d and os.path.isfile(os.path.join(d, "spec_data.json")):
            return d
    return None


def available():
    return spec_dir() is not None


def data():
    global _DATA
    if _DATA is None:
        d = spec_dir()
        if d is None:
            raise SpecUnavailable("the picture spec's data file (spec_data.json) is missing from this installation; reinstall the package "
                                  "or set PIXELMATH_SPEC_DIR to a folder with spec_data.json")
        with open(os.path.join(d, "spec_data.json"), encoding="utf-8") as fh:
            _DATA = json.load(fh)
        _DATA["by_name"] = {b["name"].lower(): b for b in _DATA["businesses"]}
        _DATA["by_id"] = {b["id"]: b for b in _DATA["businesses"]}
        _DATA["pack_by_name"] = {p["name"].lower(): p for p in _DATA["packs"]}
    return _DATA


def businesses():
    return list(data()["businesses"])


def parse_request(text):
    """Split a spec prompt into subject, business phrase, palette (accent, background), style notes, slot hints and (team) role."""
    text = " ".join((text or "").split())
    ms = list(re.finditer(r"for an? ((?:(?!for an? ).)+?) website\b", text, re.I))          # the LAST "for a <business> website" (a caption may contain "for a ..." too)
    m = ms[-1] if ms else None
    subject = text[:m.start()].strip().rstrip(",").strip() if m else re.split(r"\.\s", text)[0].strip()
    business = m.group(1).strip().lower() if m else None
    pm = re.search(r"accent\s+(#[0-9a-fA-F]{6})(?:\s+on\s+(#[0-9a-fA-F]{6}))?", text)
    low = text.lower()
    style_unsupported = next((w.strip() for w in UNSUPPORTED_STYLES if w in low.replace(STYLE_LINE, "")), None)
    slot_hint = None
    role = None
    rm = re.search(r"portrait of an? (?:friendly )?(.+?)(?:,| illustrated|$)", subject, re.I)
    if rm and ("illustrated character" in low or "shoulders up" in low):
        slot_hint, role = "team", rm.group(1).strip()
    elif "background texture" in low or "abstract background texture" in low:
        slot_hint = "background"
    return {"subject": subject, "business": business, "accent": pm.group(1) if pm else None, "bg": pm.group(2) if pm and pm.group(2) else None,
            "style_unsupported": style_unsupported, "slot_hint": slot_hint, "role": role}


def resolve_niche(business, text="", classifier=None):
    """-> (niche id or None, how). An exact spec name wins; else a spec id spelled with spaces; else the trained prompt matcher."""
    load_all()
    d = data()
    if business:
        b = d["by_name"].get(business) or d["by_id"].get(business.replace(" ", "_"))
        if b:
            return (b["niche"] if b["niche"] in NICHES else None), "spec business %s" % b["id"]
        p = d["pack_by_name"].get(business)
        if p:
            return (p["niche"] if p["niche"] in NICHES else None), "spec business type %r" % p["name"]
        words = set(re.findall(r"[a-z]+", business))
        best = max(d["businesses"], key=lambda b: len(words & set(re.findall(r"[a-z]+", b["name"].lower()))) / (len(set(re.findall(r"[a-z]+", b["name"].lower()))) or 1))
        overlap = len(words & set(re.findall(r"[a-z]+", best["name"].lower()))) / (len(set(re.findall(r"[a-z]+", best["name"].lower()))) or 1)
        if overlap >= 0.99:
            return (best["niche"] if best["niche"] in NICHES else None), "spec business %s (all words)" % best["id"]
    from .classifier import as_classifier
    nid, info = match_niche(text or business or "", classifier or as_classifier(None))
    return nid, "prompt matcher: %s" % info.get("reason", "")


def split_slot(slot):
    """'gallery-3' -> ('gallery', 2); 'about' -> ('about', 0)."""
    m = re.match(r"^(hero|about|gallery|card|team|background)(?:-(\d+))?$", slot or "")
    if not m:
        raise ValueError("slot must be hero-1..3, about, gallery-1..6, card-1..6, team-1..3 or background (got %r)" % (slot,))
    return m.group(1), max(0, int(m.group(2) or 1) - 1)


def slot_for_size(width, height):
    for kind, (w, h) in SLOT_SIZES.items():
        if (w, h) == (width, height):
            return kind
    return "card" if width / float(height) < 1.6 else "hero"


@dataclass
class SpecResult:
    canvas: object
    report: dict
    data: bytes = None
    hash: int = 0


def _bg_dark(bg):
    c = parse_color(bg)
    return bool(c) and (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) < 0.35


def _texture(S, motif, bg, dark):
    """Soft abstract texture, no subject: the page background colour with calm accent light and one quiet motif."""
    import math
    P = S.pal
    rng = S.rng
    mixc = lambda a, b, t: tuple(x + (y - x) * t for x, y in zip(a, b))            # noqa: E731
    top = mixc(bg, P.accent_dark if dark else P.accent_light, 0.10)
    bot = mixc(bg, P.accent if dark else P.accent_light, 0.22 if dark else 0.30)
    S.wall(top, bot, 1.0)
    for k in range(6):
        col = (P.accent, P.accent2, P.accent_light)[k % 3]
        S.soft(rng.uniform(0.0, 2.0), rng.uniform(0.0, 1.0), rng.uniform(0.35, 0.7), rng.uniform(0.25, 0.5), col, rng.uniform(0.10, 0.22), 1.3)
    ink = P.accent_light if dark else P.accent
    if motif == "dots":
        for i in range(26):
            for j in range(11):
                S.circle(0.04 + i * 0.078 + (0.039 if j % 2 else 0), 0.05 + j * 0.092, 0.011, ink, alpha=0.10, lift=0, soft=1.0)
    elif motif == "waves":
        for w in range(7):
            pts = [(u / 20.0, 0.18 + w * 0.12 + 0.05 * math.sin(u / 20.0 * 5.5 + w * 0.8)) for u in range(0, 41)]
            for a, b in zip(pts, pts[1:]):
                S.line(a[0], a[1], b[0], b[1], 0.012, ink, alpha=0.10)
    elif motif == "rings":
        for k in range(7):
            S.circle(1.45, 0.45, 0.16 + 0.15 * k, ink, alpha=0.035, lift=0, soft=2.0)
    elif motif == "grid":
        for i in range(0, 41):
            S.line(i * 0.05, 0.0, i * 0.05, 1.0, 0.003, ink, alpha=0.07)
        for j in range(0, 21):
            S.line(0.0, j * 0.05, 2.0, j * 0.05, 0.003, ink, alpha=0.07)
    else:
        for k in range(5):
            S.light_shaft(0.2 + k * 0.38, -0.1, 0.45 + k * 0.38, -0.1, 0.05 + k * 0.38, 1.1, -0.2 + k * 0.38, 1.1, ink, alpha=0.05)
    S.glow(0.35, 0.3, 0.7, P.light, 0.08)


def _finish(canvas, report, fmt, kind, quality=None):
    thumb = post.small(canvas, 64)
    res = SceneResult(canvas, report, None, thumb, post.phash(thumb))
    if fmt:
        _encode(res, fmt, quality, kind if kind in ("hero", "about") else None, SLOT_BYTES[kind])
    return res


def render(text, slot=None, seed=0, accent=None, bg=None, size=None, fmt="jpeg", niche=None, business=None, mood=None, design_style=None, quality=None,
           classifier=None, retry=0):
    """One spec picture. `text` is the request ("<subject>, for a <business> website[. style][. Palette: accent #x on #y.]").

    slot: hero-1..3, about, gallery-1..6, card-1..6, team-1..3 or background (inferred from the text or the size when omitted).
    accent / bg: override the palette in the text; niche / business: skip the lookup. Returns a result with .data (JPEG/PNG bytes) and .report.
    """
    t0 = time.time()
    req = parse_request(text)
    kind, idx = split_slot(slot) if slot else (None, 0)
    seed += 0 if kind is None else KIND_SEED.get(kind, 0)                          # the same camera on another slot must not repeat the same picture
    if kind is None:
        kind = req["slot_hint"] or (slot_for_size(*size) if size else "hero")
    w, h = size or SLOT_SIZES[kind]
    biz = business or req["business"]
    nid, how = ("none", "niche none") if niche == "none" else ((niche, "niche given") if niche else resolve_niche(biz, text, classifier))
    spec_biz = data()["by_name"].get((biz or "").lower())
    pal_in = (spec_biz["palettes"][0] if spec_biz else {})
    accent = accent or req["accent"] or pal_in.get("accent")
    bgc = bg or req["bg"] or pal_in.get("bg")
    dark = _bg_dark(bgc) if bgc else False
    if design_style:
        dark = design_style in data()["styles"]["dark"] or (dark and design_style not in data()["styles"]["light"])
    n = NICHES.get(nid) if nid and nid != "none" else None
    use_mood = mood or ("dark" if dark else (n.mood if n else "light"))
    note = None
    if req["style_unsupported"]:
        note = "style %r is not drawn by this engine: the default flat illustration is used" % req["style_unsupported"]
    base = {"slot": "%s%s" % (kind, "-%d" % (idx + 1) if kind in ("hero", "gallery", "card", "team") else ""), "size": [w, h], "business": biz, "niche": n.id if n else None,
            "how": how, "bg": bgc, "style_note": note, "no_text": True}
    if kind == "team":
        acc = parse_color(accent) or parse_color(n.accent if n else "#4f6bed")
        pal = make_palette(acc, use_mood)
        cv = render_portrait(req["role"] or req["subject"], w, h, seed + idx * 97 + 11, pal, n.id if n else None)
        rep = dict(base, mood=use_mood, accent="#%02x%02x%02x" % tuple(int(c * 255 + .5) for c in acc), variant="portrait", role=req["role"], fallback=False)
        res = _finish(cv, rep, fmt, kind, quality)
    elif kind == "background":
        acc = parse_color(accent) or parse_color(n.accent if n else "#4f6bed")
        pal = make_palette(acc, use_mood)
        bgcol = parse_color(bgc) if bgc else (pal.wall_top if not dark else pal.wall_bot)
        S = Stage(w, h, pal, seed + 5)
        motif = MOTIFS[sum(map(ord, nid or biz or "x")) % len(MOTIFS)]
        _texture(S, motif, bgcol, dark)
        cv = S.finish(grain=0.012, vignette=0.12)
        rep = dict(base, mood=use_mood, accent="#%02x%02x%02x" % tuple(int(c * 255 + .5) for c in acc), variant="texture:%s" % motif, fallback=False)
        res = _finish(cv, rep, fmt, kind, quality)
    else:
        variant = {"hero": HERO_VARIANTS, "about": ("fit",), "gallery": GALLERY_VARIANTS, "card": CARD_VARIANTS}[kind][idx % len({"hero": HERO_VARIANTS, "about": ("fit",),
                   "gallery": GALLERY_VARIANTS, "card": CARD_VARIANTS}[kind])]
        zone = "left" if kind == "hero" else None
        view = VIEWS.get(base["slot"])
        if retry:                                                                   # a too-similar picture: another crop of the same view
            rv = RETRY_VIEWS[min(retry, len(RETRY_VIEWS) - 1)]
            view = (rv[0] * (view[0] if view else 1.0), rv[1] + (view[1] if view else 0.0), rv[2] + (view[2] if view else 0.0))
        r = scene(text, w, h, seed + idx * 53, accent=accent, mood=use_mood, text_zone=zone, variant=variant, niche=nid or "none", fmt=None, model=None, view=view)
        rep = dict(base, mood=r.report["mood"], accent=r.report["accent"], variant=r.report["variant"], fallback=r.report["fallback"], text_zone=zone,
                   text_color=r.report["text_color"], contrast=r.report["contrast"], judge_ok=r.report["judge_ok"], redrawn=r.report["redrawn"], seed=r.report["seed"])
        res = _finish(r.canvas, rep, fmt, kind, quality)
    res.report["seconds"] = round(time.time() - t0, 2)
    if fmt:
        res.report["bytes"] = len(res.data)
    return res


def full_request(prompt, palette):
    """The spec's own recipe: <subject prompt>. <STYLE LINE>. Palette: accent #x on #y."""
    return "%s. %s. Palette: accent %s on %s." % (prompt, STYLE_LINE, palette["accent"], palette["bg"])


def spec_prompts(biz_id):
    """The spec's 20 [{slot, prompt}] of one business, from spec_prompts.json (or the full image_ai_spec.json) next to spec_data.json.
    Raises FileNotFoundError with a clear message when neither is there (pass `prompts` instead)."""
    d = spec_dir() or SPEC_DIR
    path = next((os.path.join(d, f) for f in ("spec_prompts.json", "image_ai_spec.json") if os.path.isfile(os.path.join(d, f))), None)
    if path is None:
        raise FileNotFoundError("the spec's prompt list (spec_prompts.json) is missing from this installation; pass prompts=[{slot, prompt}, ...] instead")
    with open(path, encoding="utf-8") as fh:
        return [{"slot": it["slot"], "prompt": it["prompt"]} for it in next(x for x in json.load(fh)["businesses"] if x["id"] == biz_id)["items"]]


def render_business(biz_id, out_dir=None, palette_index=0, seed=0, fmt="jpeg", prompts=None, log=None, min_distance=8, sheet=None, title=None):
    """All pictures of one business: the 20 prompts of the spec (or `prompts` = [{slot, prompt}]), one palette, one style.

    Writes <out_dir>/<slot>.jpg and manifest.json when out_dir is given. Pictures of the scene slots must differ by at least `min_distance` of 63 phash bits;
    a too-similar one is drawn again with another seed. Returns the manifest dict.
    """
    load_all()
    b = data()["by_id"][biz_id]
    pal = b["palettes"][palette_index % len(b["palettes"])]
    if prompts is None:
        prompts = spec_prompts(biz_id)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    seen, items, thumbs = [], [], []
    for it in prompts:
        req_text = full_request(it["prompt"], pal)
        tries = 0
        while True:
            res = render(req_text, slot=it["slot"], seed=seed + tries * 101, fmt=fmt, accent=pal["accent"], bg=pal["bg"], retry=tries)
            kind = it["slot"].split("-")[0]
            dists = [bin(res.hash ^ h).count("1") for h in seen] if kind in ("hero", "about", "gallery", "card") else []
            if not dists or min(dists) >= min_distance or tries >= 3:
                break
            tries += 1
        if kind in ("hero", "about", "gallery", "card"):
            seen.append(res.hash)
        rep = dict(res.report, prompt=it["prompt"], palette=pal["name"], min_distance=min(dists) if dists else None, tries=tries)
        if out_dir:
            fn = "%s.%s" % (it["slot"], "jpg" if fmt == "jpeg" else "png")
            with open(os.path.join(out_dir, fn), "wb") as fh:
                fh.write(res.data)
            rep["file"] = fn
        if sheet:
            from .sheet import shrink
            k = min(200.0 / res.canvas.w, 120.0 / res.canvas.h)                          # fit the thumbnail into a 200 x 120 cell
            tw, th = max(1, int(res.canvas.w * k)), max(1, int(res.canvas.h * k))
            thumbs.append((rep["slot"], rep["size"], rep.get("bytes", 0), shrink(res.canvas, tw, th)))
        items.append(rep)
        if log:
            log("  %-10s %-16s %5.1fs %6d B  %s" % (it["slot"], rep.get("niche"), rep["seconds"], rep.get("bytes", 0), rep.get("variant")))
    manifest = {"business": biz_id, "name": b["name"], "niche": b["niche"], "palette": pal, "items": items}
    if sheet:
        contact_sheet(thumbs, sheet, "%s | niche %s | palette %s %s on %s" % (title or b["name"], b["niche"], pal["name"], pal["accent"], pal["bg"]))
    if out_dir:
        with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
    return manifest


def contact_sheet(thumbs, path, head, cols=6):
    """All pictures of a business on one sheet: [(slot, [w, h], bytes, thumb canvas)] -> JPEG/PNG file."""
    from ..imagefile import encode_png
    from ..jpegwrite import encode_jpeg
    from ..raster import Canvas
    from ..text import draw_text
    cw, ch, pad, top = 212, 146, 6, 24
    rows = (len(thumbs) + cols - 1) // cols
    W, H = cols * (cw + pad) + pad, top + rows * (ch + pad) + pad
    sheet = Canvas(W, H, (0.93, 0.93, 0.94))
    draw_text(sheet, head.upper()[:160], W / 2, 12, 9, (0.1, 0.1, 0.2), 0.12, max_width=W - 20)
    for k, (slot, size, nbytes, th) in enumerate(thumbs):
        x0, y0 = pad + (k % cols) * (cw + pad), top + (k // cols) * (ch + pad)
        for yy in range(th.h):
            i, j = yy * th.w * 3, ((y0 + 14 + yy) * W + x0 + (cw - th.w) // 2) * 3
            sheet.px[j:j + th.w * 3] = th.px[i:i + th.w * 3]
        draw_text(sheet, ("%s %dx%d %dKB" % (slot, size[0], size[1], nbytes // 1024)).upper(), x0 + cw / 2, y0 + 6, 7, (0.1, 0.1, 0.2), 0.12, max_width=cw)
    with open(path, "wb") as fh:
        fh.write(encode_jpeg(W, H, sheet.px, 86) if path.lower().endswith((".jpg", ".jpeg")) else encode_png(W, H, sheet.to_rgb_bytes()))
    return path
