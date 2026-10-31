"""Training command: teach the engine new words from your own (image, caption) data.

    python3 train.py my_data --model my_model.json
"""
import argparse
import math
import os
import sys
import time

from .imagefile import save
from .learn import (DEFAULT_GRID, LearnedModel, ModelError, load_dataset, render_learned,
                    train_model)


def _rmse255(mse):
    return math.sqrt(mse) * 255.0


def _check_model_path(path):
    """Fail before a long training run if the model file could not be saved afterwards."""
    full = os.path.abspath(path)
    folder = os.path.dirname(full)
    if os.path.isdir(full):
        raise ModelError("--model must be a file path, but %s is a folder" % path)
    if not os.path.isdir(folder):
        raise ModelError("the folder for --model does not exist: %s" % folder)
    if not os.access(folder, os.W_OK) or (os.path.exists(full) and not os.access(full, os.W_OK)):
        raise ModelError("cannot write to %s (no permission)" % path)


def main(argv=None):
    try:
        return _main(argv)
    except KeyboardInterrupt:
        print("\ninterrupted: model file left unchanged", file=sys.stderr)
        return 130


def _main(argv=None):
    ap = argparse.ArgumentParser(
        prog="train.py",
        description="Train the PixelMath learned model on a folder of images + captions. "
                    "Re-run with new images any time: old data is kept inside the model file.")
    ap.add_argument("data", help="folder with images (png/jpg/bmp) and captions")
    ap.add_argument("--model", default="pixelmath_model.json", help="model file to create/update")
    ap.add_argument("--fresh", action="store_true", help="ignore an existing model, start from scratch")
    ap.add_argument("--grid", type=int, default=DEFAULT_GRID, help="colour-grid size, new models only (default 16)")
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--lr", type=float, default=0.3)
    ap.add_argument("--l2", type=float, default=1e-4)
    ap.add_argument("--val-frac", type=float, default=0.15, help="held-out share used to measure real learning")
    ap.add_argument("--patience", type=int, default=8, help="stop after this many epochs without improvement")
    ap.add_argument("--no-refit", action="store_true", help="skip the final retrain on all data")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--words", type=int, default=12, help="show this many most frequent learned words")
    ap.add_argument("--preview", metavar="DIR", help="save preview images of what the model predicts")
    args = ap.parse_args(argv)
    if not 0 <= args.val_frac < 0.5 or args.epochs < 1 or args.lr <= 0:
        ap.error("need 0 <= val-frac < 0.5, epochs >= 1, lr > 0")

    try:
        _check_model_path(args.model)
        if os.path.exists(args.model) and not args.fresh:
            try:
                model = LearnedModel.load(args.model)
            except ModelError as exc:
                raise ModelError("%s\n  (use --fresh to ignore this file and start a new model; "
                                 "the old file is kept as %s.bak)" % (exc, args.model))
            print("loaded %s: %d stored samples, %d words" % (args.model, len(model.samples), len(model.rows)))
        else:
            if not 4 <= args.grid <= 64:
                ap.error("grid must be between 4 and 64")
            model = LearnedModel(args.grid)
            print("starting a new model (grid %dx%d)" % (model.grid, model.grid))
        t0 = time.time()
        samples, skipped, sources = load_dataset(args.data, model.grid)
    except ModelError as exc:
        print("train.py: error: %s" % exc, file=sys.stderr)
        return 1

    print("read %d images in %.1fs  (captions from: manifest %d, table %d, sidecar .txt %d, file/folder name %d)" % (
        len(samples), time.time() - t0, sources["manifest"], sources["table"], sources["sidecar"], sources["filename"]))
    for rel, why in skipped[:10]:
        print("  skipped %s: %s" % (rel, why))
    if len(skipped) > 10:
        print("  ... and %d more skipped" % (len(skipped) - 10))
    if not samples and not model.samples:
        print("train.py: error: no usable (image, caption) pairs found in %r" % args.data, file=sys.stderr)
        return 1
    if sources["filename"] > 0.5 * max(1, len(samples)):
        print("note: most captions come from file/folder names. Descriptive captions "
              "(captions.csv or a .txt next to each image) train much better.")

    total = len({s.id for s in model.samples} | {s.id for s in samples})
    if total < 10:
        print("warning: only %d samples. Training works, but no held-out check is possible and the "
              "model will mostly memorise. Aim for 50+ varied examples." % total)

    def log(ep, tr, va):
        if ep == 0:
            print("refitting on all data for the best epoch count ...")
        elif ep == 1 or ep % 5 == 0:
            print("  epoch %3d  train rmse %5.1f%s" % (
                ep, _rmse255(tr), "" if va is None else "   val rmse %5.1f" % _rmse255(va)))

    t0 = time.time()
    try:
        m = train_model(model, samples, args.epochs, args.lr, args.l2, args.val_frac, args.seed,
                        args.patience, not args.no_refit, log)
        model.save(args.model)
    except (ModelError, OSError) as exc:
        print("train.py: error: %s" % exc, file=sys.stderr)
        return 1

    print("\ntrained on %d samples (%d new) in %.1fs; vocabulary %d words; saved %s" % (
        m["samples"], m["added"], time.time() - t0, len(model.rows), args.model))
    if m["val_mse"] is not None:
        gain = 100.0 * (1 - m["val_mse"] / m["baseline_val"]) if m["baseline_val"] else 0.0
        print("held-out check (%d images never trained on): rmse %.1f vs %.1f for the 'average image' "
              "baseline  ->  %.0f%% lower error (best epoch %d)" % (
                  m["val_samples"], _rmse255(m["val_mse"]), _rmse255(m["baseline_val"]), gain, m["best_epoch"]))
        if gain < 10:
            print("warning: the model barely beats the average image on unseen data. Add more, "
                  "more varied images with descriptive captions.")
    if model.extras.get("niche_nb"):
        print("niche classifier trained on %d niches (used by the studio when keywords are not enough)" % len(model.extras["niche_nb"]["classes"]))
    if args.words and model.rows:
        top = sorted(model.rows, key=lambda w: (-model.doc_freq.get(w, 0), w))[:args.words]
        print("most frequent words and the average colour each one learned:")
        for w in top:
            r, g, b = model.word_color(w)
            print("  %-14s seen in %3d captions   #%02x%02x%02x" % (w, model.doc_freq.get(w, 0), r, g, b))

    if args.preview:
        os.makedirs(args.preview, exist_ok=True)
        seen = []
        for s in model.samples:
            if s.caption not in seen:
                seen.append(s.caption)
            if len(seen) >= 8:
                break
        for k, caption in enumerate(seen):
            cv = render_learned(model, caption, 192, 192)
            save(os.path.join(args.preview, "preview_%02d.png" % k), 192, 192, cv.to_rgb_bytes())
        print("saved %d preview images in %s" % (len(seen), args.preview))

    print('\ntry it:  python3 -m pixelmath "your prompt" --model %s --learned always -o out.png' % args.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
