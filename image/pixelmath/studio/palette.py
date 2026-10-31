"""Mood + accent -> one palette that every picture of a site shares."""
import colorsys
from dataclasses import dataclass

from ..raster import clamp, mix, scale
from ..tokenizer import COLORS

WHITE = (1.0, 1.0, 1.0)
MOODS = ("warm", "cool", "dark", "light")
# global grading per mood: channel gains, contrast, light colour, how much the accent tints the walls
MOOD_STYLE = {
    "warm": {"gain": (1.04, 0.995, 0.93), "contrast": 0.10, "light": (1.0, 0.93, 0.82), "wall_sat": 0.22, "wall_val": 0.94},
    "cool": {"gain": (0.95, 0.995, 1.05), "contrast": 0.08, "light": (0.88, 0.94, 1.0), "wall_sat": 0.20, "wall_val": 0.94},
    "dark": {"gain": (0.97, 0.98, 1.03), "contrast": 0.18, "light": (0.85, 0.86, 1.0), "wall_sat": 0.55, "wall_val": 0.20},
    "light": {"gain": (1.0, 1.0, 1.0), "contrast": 0.04, "light": (1.0, 0.99, 0.97), "wall_sat": 0.07, "wall_val": 0.98},
}


def parse_color(value):
    """'#c0392b', 'c0392b', 'teal' or an (r, g, b) tuple in 0..1 -> rgb tuple."""
    if value is None:
        return None
    if isinstance(value, (tuple, list)):
        return tuple(float(v) for v in value[:3])
    s = str(value).strip().lower()
    if s in COLORS:
        return COLORS[s]
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) == 6:
        try:
            return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        except ValueError:
            pass
    raise ValueError("accent must be a colour name or #rrggbb (got %r)" % (value,))


def hsv(h, s, v):
    return colorsys.hsv_to_rgb(h % 1.0, clamp(s), clamp(v))


@dataclass
class Palette:
    accent: tuple
    mood: str
    hue: float
    wall_top: tuple
    wall_bot: tuple
    floor_top: tuple
    floor_bot: tuple
    surface: tuple          # table / counter top
    accent2: tuple          # analogous neighbour of the accent
    accent_dark: tuple
    accent_light: tuple
    ink: tuple              # darkest tone
    paper: tuple            # lightest tone
    light: tuple            # colour of the key light
    gain: tuple
    contrast: float

    def mixed(self, name_a, name_b, t):
        return mix(getattr(self, name_a), getattr(self, name_b), t)


def make_palette(accent, mood):
    accent = parse_color(accent) or (0.75, 0.25, 0.2)
    if mood not in MOODS:
        raise ValueError("mood must be one of %s" % ", ".join(MOODS))
    ms = MOOD_STYLE[mood]
    h, s, v = colorsys.rgb_to_hsv(*accent)
    s = max(s, 0.35)                                    # a grey accent still gets a usable hue
    accent_light = mix(accent, WHITE, 0.62)
    if mood == "warm":
        wall_base = mix((0.97, 0.91, 0.82), accent_light, 0.22)
    elif mood == "cool":
        wall_base = mix((0.88, 0.93, 0.97), accent_light, 0.20)
    elif mood == "light":
        wall_base = mix((0.98, 0.98, 0.98), accent_light, 0.10)
    else:
        wall_base = hsv(h, 0.5, 0.22)
    wall_h = wall_base
    wall_top = mix(wall_h, WHITE, 0.16) if mood != "dark" else hsv(h, 0.55, 0.26)
    wall_bot = scale(wall_h, 0.92) if mood != "dark" else hsv(h, 0.6, 0.12)
    warm_wood = (0.62, 0.42, 0.26)
    floor_top = mix(warm_wood, wall_h, 0.25 if mood != "dark" else 0.55)
    floor_bot = scale(floor_top, 0.78)
    if mood == "dark":
        floor_top, floor_bot = scale(floor_top, 0.45), scale(floor_top, 0.25)
    surface = mix(warm_wood, (0.9, 0.8, 0.66), 0.25) if mood != "dark" else scale(warm_wood, 0.55)
    ink = hsv(h, 0.35, 0.10)
    return Palette(
        accent=accent, mood=mood, hue=h, wall_top=wall_top, wall_bot=wall_bot, floor_top=floor_top, floor_bot=floor_bot,
        surface=surface, accent2=hsv(h + 0.08, s * 0.9, min(1.0, v + 0.05)), accent_dark=scale(accent, 0.55),
        accent_light=mix(accent, WHITE, 0.55), ink=ink, paper=mix(WHITE, wall_h, 0.12), light=ms["light"], gain=ms["gain"],
        contrast=ms["contrast"])
