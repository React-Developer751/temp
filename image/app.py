#!/usr/bin/env python3
"""Start PixelMath Studio (web interface + API):  python3 app.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelmath.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
