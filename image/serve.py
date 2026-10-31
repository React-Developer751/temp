#!/usr/bin/env python3
"""Start the PixelMath HTTP API:  python3 serve.py --model my_model.json"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelmath.server import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
