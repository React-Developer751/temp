"""Prints the numbers that decide whether the writer is good enough. Run: python3 training/evaluate.py [-v]

1. named services on the page        (60 fresh prompts: 15 niches x 4, English / Hinglish / Hindi)   target >= 95%
2. placeholders, wrong-niche words, repeated 6-word spans over 300 pages                               target 0
3. sentences shared by two pages of one niche                                                           target < 30%
4. business-type detection on the HOLDOUT prompts (never trained on), before and after                 target >= 90%
The checks here are written separately from corecraft/validators.py so the writer is not only grading itself.
"""
import json
import re
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corecraft import detector as D   # noqa: E402
from corecraft.business_types import T, detect_type   # noqa: E402
from corecraft.content_engine import generate_content   # noqa: E402
from corecraft.validators import leaves_of   # noqa: E402
from eval_prompts import EVAL, FRESH   # noqa: E402
from labelled import HOLDOUT, TRAIN   # noqa: E402

VERBOSE = "-v" in sys.argv
PLACEHOLDER = [r"\bsample\b", r"lorem", r"ipsum", r"example\.(?:com|org)", r"\b555\b", r"\bjohn\b", r"\bjane\b", r"\b123\b", r"your main dishes", r"starter or soup", r"\bplaceholder\b",
               r"lunch thali", r"home style curry", r"results that speak for themselves"]
CUISINE_X = "thali curry dosa idli vada sambar naan biryani tandoori paneer tikka momos noodles manchurian chaat samosa kebab lassi pasta pizza tiramisu risotto lasagna lasagne bruschetta gelato dim sum".split()
OTHER_KINDS = "patients patient menu dish dishes braces acne dentist teeth tooth cataract lasik workout workouts kurti saree laptop smartphone appointment diagnosis".split()
WRONG = {
    "italian": set(CUISINE_X) - set("pizza pasta tiramisu risotto lasagna lasagne bruschetta gelato".split()) | {"patients", "braces", "acne", "workout"},
    "north_indian": set("pasta pizza tiramisu risotto lasagna dosa idli sambar noodles momos manchurian bruschetta gelato".split()) | {"patients", "braces", "acne"},
    "south_indian": set("pasta pizza tiramisu naan biryani tandoori noodles momos manchurian kebab chaat bruschetta".split()) | {"patients", "braces", "acne"},
    "chinese": set("pasta pizza tiramisu thali curry dosa idli naan biryani tandoori chaat samosa lasagna".split()) | {"patients", "braces", "acne"},
    "bakery": set("thali curry dosa idli biryani noodles momos naan tandoori manchurian".split()) | {"patients", "braces", "acne"},
    "tea_cafe": set("thali curry dosa idli biryani noodles momos pizza pasta manchurian".split()) | {"patients", "braces", "acne"},
    "dental": {"menu", "dish", "dishes", "pizza", "thali", "workout", "acne", "pigmentation", "cataract", "lasik", "shipping"},
    "skin": {"dentist", "braces", "teeth", "tooth", "cataract", "lasik", "menu", "dish", "dishes", "workout", "shipping"},
    "gym": {"patients", "menu", "dishes", "braces", "acne", "diagnosis", "shipping"},
    "yoga": {"patients", "menu", "dishes", "braces", "acne", "diagnosis", "shipping"},
    "kurti": {"patients", "menu", "dishes", "laptop", "smartphone", "braces", "workout"},
    "electronics": {"kurti", "saree", "patients", "menu", "dishes", "braces", "workout"},
    "software": {"patients", "menu", "dishes", "braces", "kurti", "workout", "diagnosis"},
    "education": {"patients", "menu", "dishes", "braces", "kurti", "workout", "diagnosis"},
    "plumbing": {"patients", "menu", "dishes", "braces", "kurti", "workout", "curry", "pizza", "diagnosis"},
}
WORD = re.compile(r"[a-zऀ-ॿ0-9]+")


def norm(s):
    return " ".join(WORD.findall(s.lower().replace("-", " ")))


def texts(content):
    """Every sentence-bearing string on the page (titles of cards included)."""
    return [t for _, t, _ in leaves_of(content)] + [f["title"] for f in content["features"]]


def sentences(content):
    out = set()
    for t in texts(content):
        for s in re.split(r"(?<=[.!?])\s+", t):
            n = norm(s)
            if len(n.split()) >= 4:   # a sentence has at least four words ("Book a table" is a button label)
                out.add(n)
    return out


def repeated_span(content, n=6):
    seen = {}
    for path, t, _ in leaves_of(content):
        ws = WORD.findall(t.lower().replace("-", " "))
        spans = {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}
        for sp in spans:
            if sp in seen and seen[sp] != path:
                return True
        for sp in spans:
            seen.setdefault(sp, path)
    return False


def main():
    rows = []
    for niche, lang, prompt, services in EVAL:
        c = generate_content(prompt)
        rows.append((niche, lang, prompt, services, c))
    # 1. named services -----------------------------------------------------------------------------------
    total = hit = pages_ok = 0
    misses = []
    for niche, lang, prompt, services, c in rows:
        blob = " " + " ".join(norm(t) for t in texts(c)) + " "
        ok = 0
        for s in services:
            total += 1
            if " " + norm(s) + " " in blob:
                hit += 1
                ok += 1
            else:
                misses.append((prompt[:50], s))
        pages_ok += ok == len(services)
    print("1. named services on the page: %d/%d = %.1f%%   (pages with every service: %d/%d)   target >= 95%%" % (hit, total, 100 * hit / total, pages_ok, len(rows)))
    if VERBOSE:
        for m in misses:
            print("     missing:", m)
    # 2. placeholders / wrong niche / repeats over 5 seeds ---------------------------------------------------
    ph = wn = rp = pages = 0
    bad = []
    for niche, lang, prompt, services, _ in rows:
        for seed in range(5):
            c = generate_content(prompt, seed)
            pages += 1
            blob = " ".join(texts(c)).lower()
            low_prompt = prompt.lower()
            if any((m := re.search(rx, blob)) and m.group(0) not in low_prompt for rx in PLACEHOLDER):
                ph += 1
                bad.append(("placeholder", prompt[:40]))
            words = set(WORD.findall(blob.replace("-", " ")))
            allowed = set(WORD.findall(low_prompt.replace("-", " ")))
            if lang != "hi" and (WRONG[niche] & words) - allowed:
                wn += 1
                bad.append(("wrong-niche", prompt[:40], sorted((WRONG[niche] & words) - allowed)))
            if repeated_span(c):
                rp += 1
                bad.append(("repeat", prompt[:40]))
            if lang == "hi":
                latin = re.findall(r"[A-Za-z]{3,}", " ".join(t for _, t, _ in leaves_of(c)))
                latin = [w for w in latin if w.lower() not in low_prompt]
                if latin:
                    wn += 1
                    bad.append(("latin in hindi page", prompt[:30], latin[:4]))
    print("2. over %d pages: placeholders %d | wrong-niche words %d | repeated 6-word spans %d   target 0 / 0 / 0" % (pages, ph, wn, rp))
    if VERBOSE:
        for b in bad[:20]:
            print("     ", b)
    # 2b. a second, smaller set written after the fixes ------------------------------------------------------------
    total = hit = bad_pages = 0
    detail = []
    for niche, lang, prompt, services in FRESH:
        pages_bad = False
        for seed in (None, 1, 2):
            c = generate_content(prompt, seed)
            blob = " " + " ".join(norm(t) for t in texts(c)) + " "
            if seed is None:
                for sv in services:
                    total += 1
                    ok_ = " " + norm(sv) + " " in blob
                    hit += ok_
                    if not ok_:
                        detail.append((prompt[:40], sv))
            low = " ".join(texts(c)).lower()
            if any((m := re.search(rx, low)) and m.group(0) not in prompt.lower() for rx in PLACEHOLDER) or repeated_span(c):
                pages_bad = True
            if niche in WRONG and lang != "hi" and (WRONG[niche] & set(WORD.findall(low.replace("-", " ")))) - set(WORD.findall(prompt.lower().replace("-", " "))):
                pages_bad = True
        bad_pages += pages_bad
    print("2b. fresh set of %d prompts (3 seeds each): named services %d/%d = %.1f%% | pages with a placeholder, wrong-niche word or repeated span: %d"
          % (len(FRESH), hit, total, 100 * hit / total, bad_pages))
    if VERBOSE:
        for d in detail:
            print("     missing:", d)
    # 3. sentence overlap inside a niche ------------------------------------------------------------------------
    by = {}
    for niche, lang, prompt, services, c in rows:
        by.setdefault(niche, []).append(sentences(c))
    overlaps = []
    for niche, sets in by.items():
        for a, b in combinations(sets, 2):
            overlaps.append(max(len(a & b) / max(len(a), 1), len(a & b) / max(len(b), 1)))
    print("3. sentences shared by two pages of one niche (%d pairs): mean %.1f%%, max %.1f%%   target < 30%%" % (len(overlaps), 100 * sum(overlaps) / len(overlaps), 100 * max(overlaps)))
    # 4. detection -----------------------------------------------------------------------------------------------
    base = json.loads((ROOT / "data" / "baseline_detection.json").read_text())

    def score(rows_):
        ok = silent = lowflag = 0
        for p, t in rows_:
            got, conf, det = D.detect(p)
            if got == t:
                ok += 1
            elif conf != "low" and det.get("use", True):
                silent += 1
            else:
                lowflag += 1
        return ok, silent, lowflag
    for name, rows_ in (("TRAIN (used for fitting/tuning)", TRAIN), ("HOLDOUT (never trained or tuned on)", HOLDOUT)):
        ok, silent, low = score(rows_)
        b = base["train" if name.startswith("TRAIN") else "holdout"]
        print("4. %-36s before: %d/%d = %.1f%% | after: %d/%d = %.1f%% | wrong answers flagged low-confidence: %d, silent wrong: %d"
              % (name, b[0], b[1], 100 * b[0] / b[1], ok, len(rows_), 100 * ok / len(rows_), low, silent))
    langs = {"en": [0, 0], "hinglish": [0, 0], "hi": [0, 0]}
    for p, t in HOLDOUT:
        k = "hi" if any("ऀ" <= ch <= "ॿ" for ch in p) else ("hinglish" if re.search(r"\b(ka|ki|ke|hai|mera|mujhe|chahiye|dukaan|mein|aur|wala|banani|ko|bijli|daanton|kapdon|kitab|netra|bima|lohe|rangai|makaan)\b", p.lower()) else "en")
        langs[k][1] += 1
        langs[k][0] += D.detect(p)[0] == t
    print("   hold-out by language:", {k: "%d/%d" % tuple(v) for k, v in langs.items()}, "| hold-out baseline by language:", base.get("holdout_by_lang"))


if __name__ == "__main__":
    main()
