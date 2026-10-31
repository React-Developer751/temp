#!/usr/bin/env python3
"""Render a contact sheet of studio niches (hero / about / close / detail / wide / dark) with timings and subject checks.

    python3 examples/check_niches.py sheet.png restaurant-italian gym        # named niches
    python3 examples/check_niches.py sheet.png --module food                 # every niche of one module
    python3 examples/check_niches.py --list
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pixelmath.studio.niches import NICHES, load_all  # noqa: E402
from pixelmath.studio.sheet import niche_sheet  # noqa: E402


def main(argv):
    load_all()
    if "--list" in argv:
        for n in NICHES.values():
            print("%-24s %-8s %s" % (n.id, n.group, n.title))
        return 0
    out = argv[0]
    rest = argv[1:]
    if rest[:1] == ["--module"]:
        ids = [n.id for n in NICHES.values() if n.fn.__module__.endswith("." + rest[1])]
    else:
        ids = rest
    if not ids:
        print("no niches selected")
        return 1
    niche_sheet(ids, out)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
