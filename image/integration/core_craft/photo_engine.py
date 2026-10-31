"""Photo AI: real pictures for the page (hero, about, gallery) from the PixelMath image engine.

The image engine (pure Python, offline) is a separate project. Core-Craft finds it through the PIXELMATH_HOME environment variable or
a sibling folder named `image` / `pixelmath`. If it is not there, `generate_photos` returns None and the page keeps its built-in SVG
artwork, so Core-Craft never depends on it.
"""
import importlib
import os
import sys

_CANDIDATES = ("image", "pixelmath", "pixelmath-engine")


def find_engine():
    """Folder that contains the `pixelmath` package, or None (also None when CORECRAFT_NO_PHOTOS is set: the content tests do not need pictures)."""
    if os.environ.get("CORECRAFT_NO_PHOTOS"):
        return None
    env = os.environ.get("PIXELMATH_HOME")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [env] if env else []
    paths += [os.path.join(os.path.dirname(here), name) for name in _CANDIDATES]
    for p in paths:
        if p and os.path.isdir(os.path.join(p, "pixelmath", "studio")):
            return p
    return None


def _business(content):
    return {"business_type": content.get("business_type"), "profile": content.get("profile"), "brand": content.get("brand"),
            "mood": content.get("mood"), "type_label": content.get("type_label")}


def _text(content):
    """The words that say what the business really is (brand, type, what it sells): used to pick the exact picture style."""
    parts = [content.get("brand", ""), content.get("type_label", "")] + list(content.get("keywords", []))
    parts += [f.get("title", "") for f in content.get("features", [])]
    return " ".join(p for p in parts if p)


def generate_photos(content, assets, out_dir, seed=None, count=6):
    """Write images/ into `out_dir` and return {"images": {...}, "niche", "fallback", "mood", "report"}; None if the engine is not available."""
    home = find_engine()
    if home is None:
        return None
    if home not in sys.path:
        sys.path.insert(0, home)
    try:                                                          # loaded at run time: the engine is an optional add-on, not an import of Core-Craft
        site_pictures = importlib.import_module("pixelmath.studio.site").site_pictures
    except ImportError:
        return None
    pal = assets["palette"]
    return site_pictures(_business(content), {"primary": pal["primary"], "dark": pal.get("dark")}, seed=seed or 0, count=count, text_zone="left",
                         out_dir=os.path.join(str(out_dir), "images"), text=_text(content), subdir="images")
