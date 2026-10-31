"""Public entry points: scene() for one picture, make_set() for a whole site, both with a built-in judge and a report."""
import time
from dataclasses import dataclass, field

from ..imagefile import encode_png
from ..jpegwrite import JpegError, encode_jpeg
from . import post
from .match import infer_look, match_niche
from .niches import NICHES, load_all
from .palette import MOODS, make_palette, parse_color
from .scene import VARIANTS, ZONES, render_niche
from .stage import Camera, Stage

SIZES = {"hero": (1280, 640), "about": (640, 600)}
TILE_SIZES = ((640, 400), (480, 480), (640, 400), (560, 420), (640, 400), (480, 360))
BYTE_BUDGET = {"hero": 60000, "about": 40000, "tile": 25000}
PHASH_MIN = 14                 # minimum Hamming distance (of 63 bits) between two pictures of a set
ATTEMPTS = 4
SUBJECT_MIN = {"fit": 0.9, "wide": 0.9, "close": 0.8, "detail": 0.35}
DENSITY_MIN = 0.03


@dataclass
class SceneResult:
    canvas: object
    report: dict
    data: bytes = None
    thumb: list = field(default=None, repr=False)
    hash: int = 0


def fallback_scene(S):
    """No niche fits: a calm abstract in the accent colour (soft light pools and rings), nothing that could be the wrong subject."""
    P = S.pal
    rng = S.rng
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 3.0)
        for k in range(7):
            col = P.accent if k % 3 == 0 else P.accent2 if k % 3 == 1 else P.accent_light
            S.soft(rng.uniform(-0.2, 2.2), rng.uniform(0.0, 1.1), rng.uniform(0.35, 0.8), rng.uniform(0.25, 0.55), col, rng.uniform(0.25, 0.5), 1.1)
        S.bokeh(14, -0.2, 0.0, 2.2, 1.1, [P.accent_light, P.light], 0.02, 0.07, 0.22)
    for k in range(4):
        S.circle(rng.uniform(0.2, 1.8), rng.uniform(0.2, 0.9), rng.uniform(0.25, 0.6), P.accent_light, alpha=0.07, lift=0, soft=3.0)
    S.poly([(0.9, -0.2), (1.25, -0.2), (0.7, 1.3), (0.35, 1.3)], P.light, alpha=0.06, soft=40.0)


@dataclass
class _Fallback:
    id: str = "fallback"
    title: str = "Abstract"
    fn: object = staticmethod(fallback_scene)
    subjects: tuple = ()
    accent: str = "#4f6bed"
    mood: str = "light"


def _resolve(prompt, accent, mood, niche_id, classifier, model=None):
    load_all()
    info = {}
    if classifier is None:
        from .classifier import as_classifier
        classifier = as_classifier(model)
    if niche_id == "none":
        nid, info = None, {"reason": "niche none: neutral abstract requested"}
    elif niche_id:
        if niche_id not in NICHES:
            raise ValueError("unknown niche %r (see list_niches())" % niche_id)
        nid, info = niche_id, {"reason": "niche given"}
    else:
        nid, info = match_niche(prompt, classifier)
    p_mood, p_accent = infer_look(prompt)
    n = NICHES.get(nid) if nid else None
    use_mood = mood or p_mood or (n.mood if n else "light")
    if use_mood not in MOODS:
        raise ValueError("mood must be one of %s" % ", ".join(MOODS))
    acc, source = parse_color(accent), "argument"
    if acc is None:
        acc, source = p_accent, "prompt"
    if acc is None and n and model is not None:
        # the accent the trained model associates with this niche + mood (it learned it from the user's own pictures)
        from ..learn import label_tokens
        hint = model.palette_hint(" ".join(label_tokens(nid, use_mood)))
        if hint:
            import colorsys
            cand = max((hint["top"], hint["bottom"]), key=lambda c: colorsys.rgb_to_hsv(*c)[1])
            if colorsys.rgb_to_hsv(*cand)[1] > 0.3:
                acc, source = cand, "trained model"
    if acc is None:
        acc, source = parse_color(n.accent if n else "#4f6bed"), "niche default"
    info = dict(info, accent_source=source)
    return nid, n, info, use_mood, acc


def _judge(rd, n, zone_name, variant, pal):
    """Scores for one render (all 0..1 where 1 is perfect) plus the text-zone work. Returns (scores, zone_report, ok)."""
    cv = rd.canvas
    zone_rep = None
    prefer = {"dark": "white", "light": "dark"}.get(pal.mood)
    if rd.zone:
        zone_rep = post.ensure_zone_contrast(cv, rd.zone, pal, prefer)
    thumb = post.small(cv, 64)
    busy, colours = post.detail_density(thumb, rd.zone)
    kind = variant.replace("-flip", "")
    subject_need = SUBJECT_MIN.get(kind, 0.8)
    subject = rd.subject_score if n.subjects else 1.0
    scores = {"subject": round(min(1.0, subject / subject_need), 3), "text_contrast": 1.0 if not zone_rep else round(min(1.0, zone_rep["contrast"] / 4.5), 3),
              "detail": round(min(1.0, busy / 0.12), 3), "colors": round(min(1.0, colours / 30.0), 3)}
    if n.id == "fallback":                                       # a calm abstract is meant to be smooth: only the text contrast matters
        return scores, zone_rep, scores["text_contrast"] >= 1.0, thumb
    ok = scores["subject"] >= 1.0 and scores["text_contrast"] >= 1.0 and busy >= DENSITY_MIN and colours >= 14
    return scores, zone_rep, ok, thumb


def scene(prompt, width=640, height=400, seed=0, accent=None, mood=None, text_zone=None, variant="fit", niche=None, classifier=None,
          attempts=ATTEMPTS, role=None, fmt=None, quality=None, model=None, _resolved=None, byte_budget=None, view=None):
    """One picture for `prompt`. Returns SceneResult(canvas, report[, data if fmt is 'jpeg'|'png']).

    report: niche, title, fallback (+ why), mood, accent, text zone and text colour, redrawn (extra tries the judge asked for),
    scores (subject / text_contrast / detail / colors, 1.0 = fine), seed used, size and time.
    """
    t0 = time.time()
    if text_zone not in (None, "left", "center", "bottom"):
        raise ValueError("text_zone must be left, center or bottom")
    if variant not in VARIANTS:
        raise ValueError("variant must be one of %s" % ", ".join(VARIANTS))
    nid, n, info, use_mood, acc = _resolved or _resolve(prompt, accent, mood, niche, classifier, model)
    is_fallback = n is None
    n = n or _Fallback()
    pal = make_palette(acc, use_mood)
    redrawn, best, why = 0, None, info.get("reason", "")
    for k in range(max(1, attempts)):
        s = seed + k * 7919
        v = variant if k < 2 else ("fit-flip" if variant.endswith("flip") else "fit")      # a crop that hides the subject falls back to the full view
        rd = render_niche(n, width, height, s, pal, text_zone, v, view=view if k < 2 else None)
        scores, zone_rep, ok, thumb = _judge(rd, n, text_zone, v, pal)
        if best is None or sum(scores.values()) > best[0]:
            best = (sum(scores.values()), rd, scores, zone_rep, thumb, s, ok)
        if ok:
            break
        redrawn += 1
        if k + 1 < attempts:                                     # the failed canvas is discarded; draw again with a new seed
            continue
    total, rd, scores, zone_rep, thumb, used_seed, ok = best
    if not ok and not is_fallback and scores["subject"] < 1.0:
        # the subject could not be shown: never ship a picture that may be about the wrong thing
        is_fallback, why = True, "judge: subject not visible after %d tries" % max(1, attempts)
        n = _Fallback()
        rd = render_niche(n, width, height, seed, pal, text_zone, "fit")
        scores, zone_rep, ok, thumb = _judge(rd, n, text_zone, "fit", pal)
        used_seed = seed
    report = {"niche": None if is_fallback else nid, "title": n.title, "fallback": is_fallback, "fallback_reason": why if is_fallback else None,
              "match": info, "mood": use_mood, "accent": "#%02x%02x%02x" % tuple(int(c * 255 + 0.5) for c in acc), "text_zone": text_zone,
              "text_color": zone_rep["text_color"] if zone_rep else None, "contrast": zone_rep["contrast"] if zone_rep else None,
              "scrim": zone_rep["scrim"] if zone_rep else None, "redrawn": redrawn, "scores": scores, "judge_ok": bool(ok), "seed": used_seed,
              "variant": variant if not is_fallback else "fit", "role": role, "size": [width, height]}
    res = SceneResult(rd.canvas, report, None, thumb, post.phash(thumb))
    if fmt:
        _encode(res, fmt, quality, role, byte_budget)
    report["seconds"] = round(time.time() - t0, 2)
    return res


def _encode(res, fmt, quality, role, byte_budget=None):
    cv = res.canvas
    if fmt == "png":
        res.data = encode_png(cv.w, cv.h, cv.to_rgb_bytes())
    elif fmt == "jpeg":
        px = cv.w * cv.h
        kind = role if role in ("hero", "about") else ("hero" if px > 400000 else "about" if px > 300000 else "tile")     # budget by size when no role is given
        budget = byte_budget or BYTE_BUDGET[kind]
        try:
            res.data = encode_jpeg(cv.w, cv.h, cv.px, quality or 72, target_bytes=budget, min_quality=22)
            res.report["size_budget_met"] = True
        except JpegError:
            res.data = encode_jpeg(cv.w, cv.h, cv.px, 22)
            res.report["size_budget_met"] = False
    else:
        raise ValueError("fmt must be 'jpeg' or 'png'")
    res.report["format"] = fmt
    res.report["bytes"] = len(res.data)


def list_niches():
    load_all()
    return [{"id": n.id, "title": n.title, "group": n.group, "accent": n.accent, "mood": n.mood} for n in NICHES.values()]


# ---------------------------------------------------------------------------------------------- sets
ROLE_PLAN = (("hero", "fit"), ("about", "fit"), ("tile", "close"), ("tile", "detail-flip"), ("tile", "wide"), ("tile", "fit-flip"),
             ("tile", "close-flip"), ("tile", "detail"))


def make_set(prompt, count=6, seed=0, accent=None, mood=None, text_zone="left", niche=None, classifier=None, fmt=None, quality=None, model=None):
    """3 to 8 pictures for one site in one style: hero (wide, with a text zone), about (squarish), gallery tiles (different crops).

    Same niche, accent, mood, palette and light for all; different camera and seed per picture. Any two pictures must differ by at least
    PHASH_MIN bits of a perceptual hash, otherwise the later one is drawn again. Returns (list[SceneResult], report).
    """
    if not 3 <= count <= 8:
        raise ValueError("count must be between 3 and 8")
    t0 = time.time()
    resolved = _resolve(prompt, accent, mood, niche, classifier, model)
    results, redrawn_total = [], 0
    for i in range(count):
        role, variant = ROLE_PLAN[i]
        if role == "hero":
            w, h = SIZES["hero"]
        elif role == "about":
            w, h = SIZES["about"]
        else:
            w, h = TILE_SIZES[(i - 2) % len(TILE_SIZES)]
        zone = text_zone if role == "hero" else None
        tries, res = 0, None
        for tries in range(5):
            v = variant if tries == 0 else VARIANTS[(VARIANTS.index(variant) + tries * 3) % len(VARIANTS)] if role != "hero" else variant
            res = scene(prompt, w, h, seed + 1013 * i + 4999 * tries, text_zone=zone, variant=v, role=role, _resolved=resolved)
            dist = min((post.hamming(res.hash, r.hash) for r in results), default=64)
            if res.report["fallback"] and resolved[1] is not None:
                continue                                         # the niche is known but this crop failed the judge: try another crop
            if dist >= PHASH_MIN:
                break
        res.report["duplicate_distance"] = dist
        res.report["redrawn"] += tries
        res.report["scores"]["duplicate"] = round(min(1.0, dist / PHASH_MIN), 3)
        redrawn_total += res.report["redrawn"]
        results.append(res)
    sigs = [post.hue_signature(r.thumb) for r in results]
    mean = [sum(s[k] for s in sigs) / len(sigs) for k in range(12)]
    fam = [post.family_similarity(s, mean) for s in sigs]
    for r, f in zip(results, fam):
        r.report["palette_family"] = round(f, 3)
    if fmt:
        for r in results:
            _encode(r, fmt, quality, r.report["role"])
    dists = [min(post.hamming(a.hash, b.hash) for b in results if b is not a) for a in results]
    rep = {"prompt": prompt, "niche": results[0].report["niche"], "title": results[0].report["title"], "fallback": results[0].report["fallback"],
           "mood": results[0].report["mood"], "accent": results[0].report["accent"], "count": count, "redrawn": redrawn_total,
           "min_distance": min(dists), "palette_family": round(min(fam), 3), "text_zone": text_zone,
           "hero_contrast": results[0].report["contrast"], "seconds": round(time.time() - t0, 2),
           "scores": {"subject": min(r.report["scores"]["subject"] for r in results),
                      "text_contrast": results[0].report["scores"]["text_contrast"],
                      "duplicate": round(min(1.0, min(dists) / PHASH_MIN), 3), "palette_family": round(min(fam), 3)},
           "images": [r.report for r in results]}
    return results, rep
