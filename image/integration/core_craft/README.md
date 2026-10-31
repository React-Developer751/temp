# Core-Craft AI + PixelMath pictures

Makes Core-Craft websites use real pictures (hero, about, gallery) from this engine instead of the built-in SVG art.

    python3 integration/core_craft/apply_photos.py /path/to/core-craft      # edits design_engine, content_engine, lang_hi, pipeline, main
    cp integration/core_craft/photo_engine.py /path/to/core-craft/corecraft/
    export PIXELMATH_HOME=/path/to/this/repo                                  # or keep Core-Craft in a folder next to `image/`
    python3 main.py "dental clinic in Pune"                                   # --no-photos keeps the old SVG art, --photo-count 3..8

Without the engine on disk Core-Craft behaves as before (pictures are optional). Apply it to a clean checkout or a copy first: the script stops
with "anchor not found" if the code it expects has changed. See `samples/website_examples/` for 24 generated sites (open `<site>/preview.html`).

`CORECRAFT_NO_PHOTOS=1` switches pictures off (the Core-Craft content tests set it, because drawing pictures for every business type takes ~7 s each;
`test_photos.py` in Core-Craft clears it and checks one real site). Applied to the real `content/` repo on 2026-10-28: the edits are uncommitted next to your own.
