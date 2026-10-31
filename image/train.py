#!/usr/bin/env python3
"""Train PixelMath on your own images:  python3 train.py my_data --model my_model.json"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelmath.trainer import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
