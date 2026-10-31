"""Match one blind prompt file against the niches: python3 examples/blind_eval.py studio_data/blind_v3.json [show]   (show = list every miss)"""
import json, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from pixelmath.studio.classifier import as_classifier
from pixelmath.studio.match import match_niche
from pixelmath.studio.niches import load_all
load_all(); clf = as_classifier(None)
f = sys.argv[1]; show = len(sys.argv) > 2
h = json.load(open(f, encoding="utf-8"))
c = fb = w = 0
bad = []
for n, ps in h["in_niche"].items():
    for p in ps:
        g, info = match_niche(p, clf)
        if g == n: c += 1
        elif g is None: fb += 1; bad.append(("fallback", n, p))
        else: w += 1; bad.append(("WRONG->" + g, n, p))
t = c + fb + w
offw = [(p, match_niche(p, clf)[0]) for p in h["off_niche"] if match_niche(p, clf)[0]]
print("%s: in-niche %d: correct %.1f%% fallback %.1f%% wrong %.1f%% (%d) | off-niche %d: wrongly matched %d" % (f.split("/")[-1], t, 100*c/t, 100*fb/t, 100*w/t, w, len(h["off_niche"]), len(offw)))
if show:
    for b in bad: print(*b, sep=" | ")
    for o in offw: print("OFF", *o, sep=" | ")
