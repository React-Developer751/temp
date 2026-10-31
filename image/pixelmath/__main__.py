"""Command line: python3 -m pixelmath "red house near a lake at sunset" -o scene.png"""
import argparse
import os
import sys
import time

from . import __version__
from .compose import MAX_SIZE, MIN_SIZE, render
from .imagefile import save
from .learn import LearnedModel, ModelError
from .tokenizer import MAX_PROMPT_CHARS


def main(argv=None):
    try:
        return _main(argv)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="pixelmath", description="Text to image, pure maths.")
    ap.add_argument("prompt", nargs="*", help="what to draw (English, Hinglish or Devanagari)")
    ap.add_argument("-o", "--output", default="output.png", help=".png or .bmp (default output.png)")
    ap.add_argument("--size", type=int, default=512, help="square size in pixels (default 512)")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--seed", type=int, default=0, help="change for a different variation")
    ap.add_argument("--model", help="trained model file made by train.py")
    ap.add_argument("--learned", choices=("auto", "always", "blend", "off"), default="auto",
                    help="auto: use the model only for prompts the built-in lexicon cannot understand")
    ap.add_argument("--explain", action="store_true", help="show how the prompt was understood")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="0..1. 0 = plain render. Above 0 the engine proposes variations, a critic judges them and a "
                         "genetic search keeps the best (higher = bolder)")
    ap.add_argument("--population", type=int, default=8, help="candidates per generation in creative mode (default 8)")
    ap.add_argument("--generations", type=int, default=3, help="breeding rounds in creative mode (default 3)")
    ap.add_argument("--explore", type=int, default=0,
                    help="creative mode: judge this many extra random ideas at thumbnail size first and breed from the best "
                         "(for example 300; costs about 10 ms each)")
    ap.add_argument("--studio", action="store_true",
                    help="premium niche picture for a website (restaurant, gym, dental, saas ...); implied by --accent/--mood/--text-zone/--set")
    ap.add_argument("--accent", help="studio: accent colour, name or #rrggbb (the picture follows it)")
    ap.add_argument("--mood", choices=("warm", "cool", "dark", "light"), help="studio: overall mood")
    ap.add_argument("--text-zone", choices=("left", "center", "bottom"), help="studio: keep this area calm so text on it has contrast >= 4.5:1")
    ap.add_argument("--niche", help="studio: force a niche id instead of reading it from the prompt (see --list-niches)")
    ap.add_argument("--set", type=int, metavar="N", help="studio: make a set of N pictures (3-8) for one site in the folder given by -o (a directory)")
    ap.add_argument("--list-niches", action="store_true", help="list the studio niches and exit")
    ap.add_argument("--imagine", action="store_true",
                    help="mash two random ideas together (the prompt, if given, is kept as one of them)")
    ap.add_argument("--attempts", type=int, default=12, help="mash-up tries before giving up (default 12)")
    ap.add_argument("--version", action="version", version="pixelmath " + __version__)
    args = ap.parse_args(argv)

    if args.list_niches:
        from .studio.api import list_niches
        for n in list_niches():
            print("%-20s %-8s %-6s %-8s %s" % (n["id"], n["group"], n["mood"], n["accent"], n["title"]))
        return 0
    if args.studio or args.accent or args.mood or args.text_zone or args.set or args.niche:
        return _studio(ap, args)
    if not 0.0 <= args.temperature <= 1.0:
        ap.error("--temperature must be between 0.0 and 1.0")
    try:
        prompt = " ".join(args.prompt).strip()
        if not prompt and not args.imagine:
            prompt = input("Prompt: ").strip()
    except EOFError:
        prompt = ""
    if not prompt and not args.imagine:
        ap.error("empty prompt")
    if len(prompt) > MAX_PROMPT_CHARS:
        ap.error("prompt too long (max %d characters)" % MAX_PROMPT_CHARS)
    width, height = args.width or args.size, args.height or args.size
    if not (MIN_SIZE <= width <= MAX_SIZE and MIN_SIZE <= height <= MAX_SIZE):
        ap.error("dimensions must be between %d and %d" % (MIN_SIZE, MAX_SIZE))
    ext = os.path.splitext(args.output)[1].lower()
    if ext not in (".png", ".bmp"):
        ap.error("output must end in .png or .bmp (got %r)" % (ext or args.output))

    model = None
    if args.model:
        try:
            model = LearnedModel.load(args.model)
        except ModelError as exc:
            print("pixelmath: error: %s" % exc, file=sys.stderr)
            return 1

    t0 = time.time()
    if args.imagine or args.temperature > 0:
        from . import creative
        try:
            if args.imagine:
                made, _ = creative.imagine(args.temperature or 0.8, args.seed, args.attempts, final_size=width, final_height=height,
                                           anchor=prompt or None, model=model, learned=args.learned,
                                           population=args.population, generations=args.generations)
            else:
                made = creative.evolve(prompt, args.temperature, args.population, args.generations, args.seed, final_size=width,
                                       final_height=height, model=model, learned=args.learned, explore=max(0, args.explore))
        except ValueError as exc:
            print("pixelmath: error: %s" % exc, file=sys.stderr)
            return 1
        canvas, parsed, mode = made.canvas, made.parsed, made.mode
        print("thinking:")
        for line in made.notes:
            print("  " + line)
        print("rendered prompt: %r  seed=%d  (reproduce: pixelmath %r --seed %d)" % (made.prompt, made.seed, made.prompt, made.seed))
        for alt in made.alternatives:
            print("  also good (%.3f): %r --seed %d" % (alt["score"], alt["prompt"], alt["seed"]))
        prompt = made.prompt
    else:
        canvas, parsed, mode = render(prompt, width, height, args.seed, model, args.learned)
    try:
        nbytes = save(args.output, width, height, canvas.to_rgb_bytes())
    except OSError as exc:
        print("pixelmath: error: cannot write %s: %s" % (args.output, exc.strerror or exc), file=sys.stderr)
        return 1
    print("saved %s (%dx%d, %d bytes, mode=%s) in %.1fs" % (
        args.output, width, height, nbytes, mode, time.time() - t0))

    from .compose import text_warnings
    for note in text_warnings(parsed):
        print("note: " + note, file=sys.stderr)
    if args.explain:
        print("time:", parsed.time, "| flags:", sorted(parsed.flags))
        for e in parsed.entities:
            print("  %-6s %-10s count=%d size=%.2f color=%s pos=%s" % (
                e.kind, e.name, e.count, e.size,
                tuple(round(c, 2) for c in e.color) if e.color else None, e.position))
        if parsed.unknown_words:
            print("not in lexicon:", ", ".join(parsed.unknown_words))
        if model is not None:
            print("model knows:", ", ".join(model.known_words(prompt)) or "(none of these words)")
    if mode == "abstract" and not parsed.entities and not parsed.flags:
        hint = "" if model else " (train a model with train.py to teach it new words)"
        print("note: no known objects in this prompt, so abstract art was generated.%s" % hint,
              file=sys.stderr)
    return 0


def _studio(ap, args):
    """Premium niche pictures: one scene (-o file.jpg|png) or a whole site set (--set N -o folder/)."""
    import json
    from .studio.api import make_set, scene
    prompt = " ".join(args.prompt).strip()
    if not prompt and not args.niche:
        ap.error("describe the business, e.g. \"wood fired pizza on a board\"")
    model = None
    if args.model:
        try:
            model = LearnedModel.load(args.model)
        except ModelError as exc:
            print("pixelmath: error: %s" % exc, file=sys.stderr)
            return 1
    try:
        if args.set:
            out = args.output if args.output != "output.png" else "site_pictures"
            os.makedirs(out, exist_ok=True)
            results, rep = make_set(prompt or args.niche, args.set, args.seed, args.accent, args.mood, args.text_zone or "left", args.niche,
                                    fmt="jpeg", model=model)
            names = {"hero": "hero", "about": "about"}
            tile = 0
            for r in results:
                role = r.report["role"]
                if role == "tile":
                    tile += 1
                name = names.get(role) or "tile-%d" % tile
                path = os.path.join(out, name + ".jpg")
                with open(path, "wb") as fh:
                    fh.write(r.data)
                r.report["file"] = name + ".jpg"
            with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as fh:
                json.dump(rep, fh, indent=2, ensure_ascii=False)
            print("%s: %d pictures in %s/ (%.1fs)  niche=%s fallback=%s mood=%s accent=%s" % (
                rep["title"], args.set, out, rep["seconds"], rep["niche"], rep["fallback"], rep["mood"], rep["accent"]))
            print("  judge: min distance %d bits, palette family %.2f, hero text contrast %s, redrawn %d" % (
                rep["min_distance"], rep["palette_family"], rep["hero_contrast"], rep["redrawn"]))
            for r in results:
                print("  %-9s %4dx%-4d %6d bytes  %s" % (r.report["file"], r.report["size"][0], r.report["size"][1], r.report["bytes"], r.report["scores"]))
            return 0
        width, height = args.width or (args.size if args.size != 512 else 640), args.height or (args.size if args.size != 512 else 400)
        ext = os.path.splitext(args.output)[1].lower()
        fmt = "jpeg" if ext in (".jpg", ".jpeg") else "png"
        if ext not in (".jpg", ".jpeg", ".png"):
            ap.error("studio output must end in .jpg, .jpeg or .png")
        res = scene(prompt, width, height, args.seed, args.accent, args.mood, args.text_zone, niche=args.niche, fmt=fmt, model=model)
    except ValueError as exc:
        print("pixelmath: error: %s" % exc, file=sys.stderr)
        return 1
    with open(args.output, "wb") as fh:
        fh.write(res.data)
    rep = res.report
    print("saved %s (%dx%d, %d bytes) niche=%s fallback=%s mood=%s accent=%s in %.1fs" % (
        args.output, width, height, rep["bytes"], rep["niche"], rep["fallback"], rep["mood"], rep["accent"], rep["seconds"]))
    print("  judge:", json.dumps({k: rep[k] for k in ("scores", "redrawn", "contrast", "text_color")}, ensure_ascii=False))
    if rep["fallback"]:
        print("note: no niche fits this prompt (%s): drew a neutral abstract in the accent colour" % rep["fallback_reason"], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
