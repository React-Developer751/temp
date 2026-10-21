import argparse
import sys

from corecraft import pipeline


def main():
    ap = argparse.ArgumentParser(description="Core-Craft AI: one prompt -> React static website (stdlib only)")
    ap.add_argument("prompt", nargs="?", help="website description")
    ap.add_argument("--seed", type=int, default=None, help="repeatable output")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    prompt = a.prompt or input("Describe your website: ")
    try:
        r = pipeline.run(prompt, a.out, a.seed)
    except ValueError as e:
        sys.exit("error: %s" % e)
    print("Brand: %s | niche: %s | layout: %s" % (r["brand"], r["niche"], r["layout"]))
    print("Generated in %s: %s" % (r["dir"], ", ".join(r["files"])))
    print("Open preview.html directly, or run: cd %s && python3 -m http.server  (for the React index.html)" % r["dir"])


if __name__ == "__main__":
    main()
