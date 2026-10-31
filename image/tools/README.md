# tools

`ttf_outlines.py` is a development-only helper (standard library, not imported at runtime). It reads glyph outlines from a
TrueType font and derives single-stroke centrelines (fill, Zhang-Suen thinning, spur pruning, RDP simplification).

Regenerating the Devanagari skeletons: download Noto Sans Devanagari Regular (SIL OFL 1.1, not shipped here), run
`python3 -I tools/ttf_outlines.py NotoSansDevanagari-Regular.ttf U+0915 out.png` to see a glyph with its centreline, scale font units
so the headline centre is y=6 and the stem foot is y=0, drop the headline and stem (the layout adds them), and paste the polylines
into `pixelmath/devanagari.py`. The licence of the source font is in `LICENSES/OFL-NotoSansDevanagari.txt`.
