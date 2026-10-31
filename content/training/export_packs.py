"""Write every niche pack: batch-1.json ... (arrays of niche packs, 10 niches each) and type-packs.json (the general packs), then check them.
Run: python3 training/export_packs.py [out_dir]            the default list: the spec's 99 niches + 20 types (corecraft/data/niches.json), default out_dir output/niche_packs
     python3 training/export_packs.py --author [out_dir]   the author's 77 business types + 16 general packs (corecraft/data/author_niches.json), default output/author_packs"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from corecraft import pack_check, pack_writer as W   # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if a not in ("--author", "--spec")]
    author = "--author" in sys.argv
    W.use_niche_file(W.AUTHOR_FILE if author else W.NICHE_FILE)
    out = Path(args[0]) if args else ROOT / "output" / ("author_packs" if author else "niche_packs")
    out.mkdir(parents=True, exist_ok=True)
    packs = [W.build_pack(n) for n in W.spec()["niches"]]
    types = W.build_type_packs()
    foods = {n["id"] for n in W.spec()["niches"] if n.get("menu")} | {"type_" + t["theme"] for t in W.spec()["types"] if t.get("menu")}
    problems = pack_check.check_batch(packs + types, foods=foods)
    for i in range(0, len(packs), 10):
        (out / ("batch-%d.json" % (i // 10 + 1))).write_text(json.dumps(packs[i:i + 10], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "type-packs.json").write_text(json.dumps(types, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("%s | niche packs: %d in %d files | business-type packs: %d | %d problems" % (W.niche_file().name, len(packs), (len(packs) + 9) // 10, len(types), len(problems)))
    for p in problems[:20]:
        print("  ", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
