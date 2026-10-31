"""Photo AI: real pictures for the page (hero, about, gallery) from the PixelMath image engine.

The image engine (pure Python, offline) is a separate project. Core-Craft uses it when `import pixelmath` works (it is installed).
In a repo checkout only, it also finds the engine in the sibling folder `../image/pixelmath` next to this `content` folder: that folder is
loaded by its exact path, never by adding anything to sys.path, and never when Core-Craft runs from site-packages. If neither is there,
`generate_photos` returns None and the page keeps its built-in SVG artwork, so Core-Craft never depends on it.
"""
import importlib
import importlib.util
import os
import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parent


def _repo_sibling():
    """`<repo>/../image/pixelmath` when this is the repo checkout (main.py next to corecraft/), else None."""
    if {"site-packages", "dist-packages"} & set(_PKG.parts) or not (_PKG.parent / "main.py").is_file():
        return None
    init = _PKG.parent.parent / "image" / "pixelmath" / "__init__.py"
    return init if (init.parent / "studio").is_dir() else None


def find_engine():
    """Where the `pixelmath` package comes from ("installed" or the repo sibling's __init__.py), or None
    (also None when CORECRAFT_NO_PHOTOS is set: the content tests do not need pictures)."""
    if os.environ.get("CORECRAFT_NO_PHOTOS"):
        return None
    if "pixelmath" in sys.modules or importlib.util.find_spec("pixelmath") is not None:
        return "installed"
    return _repo_sibling()


def _load_engine(home):
    """Import `pixelmath` (installed, or the repo sibling by its exact path) and return its site_pictures, or None."""
    if home != "installed" and "pixelmath" not in sys.modules:
        spec = importlib.util.spec_from_file_location("pixelmath", home, submodule_search_locations=[str(Path(home).parent)])
        module = importlib.util.module_from_spec(spec)
        sys.modules["pixelmath"] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop("pixelmath", None)
            raise ImportError("pixelmath could not be loaded from %s" % home)
    return importlib.import_module("pixelmath.studio.site").site_pictures


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
    try:                                                          # loaded at run time: the engine is an optional add-on, not an import of Core-Craft
        site_pictures = _load_engine(home)
    except ImportError:
        return None
    pal = assets["palette"]
    return site_pictures(_business(content), {"primary": pal["primary"], "dark": pal.get("dark")}, seed=seed or 0, count=count, text_zone="left",
                         out_dir=os.path.join(str(out_dir), "images"), text=_text(content), subdir="images")
