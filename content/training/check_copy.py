"""Copy check: no 6-word span of any public source page (training or hold-out) may appear in a generated page or in the writer's own
static text (frames, lexicon, voice banks). Run: python3 training/check_copy.py  -> prints counts and exits 1 on any hit."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from corecraft import lexicon, pack_families_a, pack_families_b, pack_niches, template_data, voice_a, voice_b, voice_c, voice_data, voice_profile, writer   # noqa: E402
from corecraft.content_engine import generate_content   # noqa: E402
from corecraft.validators import leaves_of   # noqa: E402

N = 6
WORD = re.compile(r"[a-z0-9]+")


def shingles(text, n=N):
    ws = WORD.findall(text.lower().replace("-", " "))
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def source_shingles():
    sh, files = set(), []
    for name in ("profile_corpus.json", "profile_holdout.json", "corpus.json", "corpus_small.json", "corpus_v2.json"):
        path = ROOT / "data" / name
        if not path.exists():
            continue
        files.append(name)
        for entry in json.loads(path.read_text()).values():
            for key in ("heading", "para", "title", "cta"):
                for t in entry.get(key, []):
                    sh |= shingles(t)
    return sh, files


def strings_of(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings_of(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            strings_of(v, out)


def main():
    src, files = source_shingles()
    print("sources read:", ", ".join(files), "|", len(src), "distinct 6-word spans")
    static = []
    for mod in (voice_a, voice_b, voice_c, voice_profile, pack_families_a, pack_families_b, pack_niches):
        for name in dir(mod):
            if name.isupper():
                strings_of(getattr(mod, name), static)
    for name in ("GENERIC", "HERO_TITLE", "HERO_SUB", "ABOUT_A", "ABOUT_B", "FEATURE_TITLES"):
        strings_of(getattr(voice_data, name), static)
    strings_of(lexicon.LEX, static)
    strings_of(writer.PROFILE_STEPS, static)
    strings_of(writer.OFFER_HIGHLIGHT, static)
    static_hits = sorted({s for t in static for s in shingles(t) if s in src})
    print("static text checked: %d strings, spans found in sources: %d" % (len(static), len(static_hits)))
    from eval_prompts import EVAL
    pages = hits = 0
    found = []
    for _, _, prompt, _ in EVAL:
        for seed in (None, 1, 2):
            c = generate_content(prompt, seed)
            pages += 1
            for _, t, user in leaves_of(c):
                if user:
                    continue
                bad = shingles(t) & src
                if bad:
                    hits += 1
                    found.append((prompt[:40], sorted(bad)[:2]))
    print("generated pages checked: %d, pages containing a source span: %d" % (pages, hits))
    for f in (static_hits[:10] or []) + found[:10]:
        print("   ", f)
    return 1 if (static_hits or hits) else 0


if __name__ == "__main__":
    sys.exit(main())
