"""Module 2a - Weight-matrix calculator (tiny MLP in pure Python).

The weights are generated from a fixed seed, so the network is a deterministic
mixing function: it turns the text vector into a "style latent" (hue drift,
saturation, brightness, grain, ...). It is NOT trained - meaning comes from the
tokenizer's lexicon; this network only gives every prompt its own look.
"""
import colorsys
import math
import random
from dataclasses import dataclass

from .raster import clamp


def matvec(matrix, vector, bias):
    return [sum(w * x for w, x in zip(row, vector)) + b for row, b in zip(matrix, bias)]


class ParamNet:
    LAYERS = (32, 24, 16, 8)

    def __init__(self, seed=20240601):
        rng = random.Random(seed)
        self.weights, self.biases = [], []
        for fan_in, fan_out in zip(self.LAYERS, self.LAYERS[1:]):
            limit = math.sqrt(6.0 / (fan_in + fan_out))          # Xavier init
            self.weights.append([[rng.uniform(-limit, limit) for _ in range(fan_in)]
                                 for _ in range(fan_out)])
            self.biases.append([rng.uniform(-0.1, 0.1) for _ in range(fan_out)])

    def forward(self, x):
        x = [v * 3.0 for v in x]          # unit vectors are tiny; widen the range
        for w, b in zip(self.weights, self.biases):
            x = [math.tanh(v) for v in matvec(w, x, b)]
        return x

    def style(self, text_vector):
        z = self.forward(text_vector)
        return Style(
            hue_shift=z[0] * 0.05,
            sat=1.0 + z[1] * 0.12,
            bright=1.0 + z[2] * 0.06,
            grain=0.012 + (z[3] * 0.5 + 0.5) * 0.02,
            light_x=0.5 + z[4] * 0.3,
            texture=1.0 + z[5] * 0.25,
            jitter=(z[6] * 0.5 + 0.5),
            warmth=z[7],
        )


@dataclass
class Style:
    hue_shift: float
    sat: float
    bright: float
    grain: float
    light_x: float
    texture: float
    jitter: float
    warmth: float

    def tint(self, color):
        """Nudge a default palette colour; user-specified colours skip this."""
        h, s, v = colorsys.rgb_to_hsv(*color)
        return colorsys.hsv_to_rgb((h + self.hue_shift) % 1.0, clamp(s * self.sat),
                                   clamp(v * self.bright))
