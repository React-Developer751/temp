"""Pipeline: Content AI -> Image/Asset AI -> Design AI."""
import json
import re
from pathlib import Path

from . import asset_engine, content_engine, design_engine


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "site"


def run(prompt, out_root="output", seed=None):
    if not prompt or not prompt.strip():
        raise ValueError("prompt is empty")
    content = content_engine.generate_content(prompt, seed)
    assets = asset_engine.generate_assets(content, seed)
    asset_engine.validate_assets(assets)
    out_dir = Path(out_root) / slugify(content["brand"])
    result = design_engine.generate_site(content, assets, out_dir, seed)
    asset_engine.write_assets(assets, out_dir)
    pal = {k: v for k, v in assets["palette"].items() if k != "rgb"}
    (out_dir / "content.json").write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "palette.json").write_text(json.dumps(pal, indent=2), encoding="utf-8")
    result.update({"brand": content["brand"], "niche": content["niche"], "palette": pal})
    return result
