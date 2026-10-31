"""PixelMath Engine - text-to-image from pure maths, zero third-party dependencies."""
from .compose import MAX_SIZE, MIN_SIZE, render
from .imagefile import encode_bmp, encode_png, save

__version__ = "1.6.0"
__all__ = ["render", "generate", "encode_png", "encode_bmp", "save", "MIN_SIZE", "MAX_SIZE",
           "__version__"]


def generate(prompt, path="output.png", width=512, height=512, seed=0, model=None, learned="auto"):
    """Render `prompt` and write it to `path` (.png or .bmp). Returns the parsed prompt."""
    canvas, parsed, _ = render(prompt, width, height, seed, model, learned)
    save(path, width, height, canvas.to_rgb_bytes())
    return parsed
