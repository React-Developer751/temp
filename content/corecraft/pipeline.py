"""Pipeline: Content AI -> Image/Asset AI -> Design AI."""
import json
import re
from pathlib import Path

from . import asset_engine, content_engine, design_engine, photo_engine


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "site"


def run(prompt, out_root="output", seed=None, facts=None, lang=None, photos=True, photo_count=6):
    if not prompt or not prompt.strip():
        raise ValueError("prompt is empty")
    content = content_engine.generate_content(prompt, seed, facts=facts, lang=lang)
    assets = asset_engine.generate_assets(content, seed)
    asset_engine.validate_assets(assets)
    out_dir = Path(out_root) / slugify(content["brand"])
    pics = photo_engine.generate_photos(content, assets, out_dir, seed, photo_count) if photos else None
    if pics is not None and pics["fallback"]:
        content["needs_review"] = list(content.get("needs_review", [])) + [
            "No picture style fits this kind of business (%s): the pictures are a neutral abstract in the brand colour, not a wrong scene." % pics["reason"]]
    result = design_engine.generate_site(content, assets, out_dir, seed, pics)
    asset_engine.write_assets(assets, out_dir)
    pal = {k: v for k, v in assets["palette"].items() if k != "rgb"}
    (out_dir / "content.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "palette.json").write_text(json.dumps(pal, indent=2), encoding="utf-8")
    result.update({"photos": None if pics is None else {k: pics[k] for k in ("niche", "fallback", "reason", "mood", "report")},
                   "brand": content["brand"], "niche": content["niche"], "business_type": content["business_type"], "needs_review": content["needs_review"], "missing": content.get("missing", []), "palette": pal})
    return result


def run_pack(request, out_root="output", seed=None, photos=True, photo_count=6):
    """request -> niche pack -> website (App.jsx, preview.html ...). Returns the same dict as run(), plus the pack and what was understood."""
    from . import pack_api, pack_site
    out = pack_api.generate_pack(request)
    u = out["understood"]
    content = pack_site.content_from_pack(out["pack"], brand=u["brand"], city=u["city"])
    assets = asset_engine.generate_assets(content, seed)
    asset_engine.validate_assets(assets)
    out_dir = Path(out_root) / slugify(content["brand"])
    pics = None
    if photos:
        try:
            pics = photo_engine.generate_photos(content, assets, out_dir, seed, photo_count)
        except Exception as e:   # pictures are a bonus: a page without them is still a good page
            content["needs_review"] = list(content.get("needs_review", [])) + ["The pictures could not be made (%s); the page uses the built-in artwork." % type(e).__name__]
        else:
            if pics is not None and pics["fallback"]:
                content["needs_review"] = list(content.get("needs_review", [])) + [
                    "No picture style fits this kind of business (%s): the pictures are a neutral abstract in the brand colour, not a wrong scene." % pics["reason"]]
    result = design_engine.generate_site(content, assets, out_dir, seed, pics)
    asset_engine.write_assets(assets, out_dir)
    (out_dir / "content.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "pack.json").write_text(json.dumps(out["pack"], indent=2, ensure_ascii=False), encoding="utf-8")
    result.update({"brand": content["brand"], "business_type": content["business_type"], "needs_review": content["needs_review"] + out["notes"], "missing": content["missing"], "pack": out,
                   "photos": None if pics is None else {k: pics[k] for k in ("niche", "fallback", "reason", "mood", "report")}})
    return result
