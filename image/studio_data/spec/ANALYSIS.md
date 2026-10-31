# Analysis of Image-AI-training.pdf (62 pages)

## What it is
The training spec for the image AI ("PixelMath") of a website generator: how every website asks for its pictures.

1. **System prompt**: one clear subject, calm space for a headline, no text / letters / numbers / logos / watermarks / real brands, no recognisable real people (simple
   illustrated characters, side or back view when possible), one drawing style, one lighting, one palette for all pictures of a site.
2. **STYLE LINE** added to every request: "friendly flat illustration, clean vector shapes, soft shading, one clear subject, rich but harmonious colours, no text ...".
3. **25 design styles** (minimal, cyberpunk, glass, luxe dark, trust navy, ...): page styles that mean "light background, airy, soft shadows" (18) or "dark background, glowing
   accents, deep shadows" (7).
4. **99 businesses x 20 pictures = 1980 prompts**: hero-1..3 (1600x900, subject right or centre, empty left), about (1200x900), gallery-1..6 (900x900), card-1..6 (800x600,
   service name + one-line description), team-1..3 (600x600, "portrait of a friendly <role>, illustrated character, shoulders up"), background (1600x900, "soft abstract
   background texture in the mood of <business>, no subject"). 95 businesses have two palettes, 4 have one (accent + background hex, named: Trades, Workwear, Chambers ...).
5. **20 generic business types x 10 pictures = 200 prompts** (hero x3, about, gallery x6) for businesses without a pack of their own.
Every prompt ends with ", for a <business name in lower case> website" (all 2180 verified).

## Findings
* **Business coverage.** 73 of the 99 businesses already had a picture niche in the studio; 26 had none (pest control, laundry, water purifier, car rental, gift shop, diagnostic lab,
  counselling, notary, DJ, video editing, funeral, scrap, farm stay, PG hostel, temple, nutritionist, animal welfare, chai stall, cloud kitchen, tiffin, mobile repair, bike garage,
  bridal makeup, drone, banquet hall, loan agent). Several others were approximate (school vs preschool, plumber and electrician share one business).
* **The subject text alone does not identify the business.** 212 of 297 hero prompts share no word with the business name ("shield and house" for pest control,
  "sea at dusk with a moon" for funeral services, "futuristic cyberpunk city at night" for a SaaS startup); 85 subject strings are reused by several businesses ("chef in a
  kitchen" x7). Only the 594 gallery prompts carry the business in brackets ("Termite drilling (pest control)"). So the business named in "for a <business> website" must
  decide the scene, and the subject can only steer it (this is how `pixelmath/studio/spec.py` works).
* **Baseline before this work:** matching the 1460 prompts of the 73 covered businesses by their text: 77.9% right niche, 14.9% refused, 7.2% wrong (worst: school vs playschool,
  digital agency vs mobile app, sports academy vs gym, plumber vs electrician).
* **Picture counts per business are fixed (16 scene pictures + 3 portraits + 1 texture)** from one scene, so scene pictures must differ by camera / crop, not by object.
* **Rules the old studio broke:** scenes drew letters and numbers ("STOP", "40", "TAXI", "GAME ON", "FRESH BREAD", ...), against "no text, letters, numbers or logos".
* **Things the spec leaves open** (decided in the implementation): what a team portrait of each role wears, which styles map to dark / light, what to do with a style the engine cannot
  draw (photo-like, 3D, sketch: the flat illustration is used and the report says so), and the picture of a business with no pack (`a general local business` -> neutral abstract).

## What was built from it
26 new niches (123 in total), the spec parser and renderer (`pixelmath/studio/spec.py`), the portrait renderer, the background texture, the no-text rule, the classifier training from
the spec's captions (1618 train / 552 held out), the `/spec` API, and a full render of all 2180 pictures (`samples/spec_run/`, checked by `examples/spec_check.py`).

## Spec mode in detail (README.md, "Picture spec", has the summary)

The PDF is the training spec of the image AI: a system prompt, one STYLE LINE, 25 design styles, **99 businesses x 20 pictures** (3 hero, about, 6 gallery,
6 card, 3 team portraits, 1 background) and **20 generic business types x 10 pictures**: 2180 prompts, each `"<subject>, for a <business> website"` plus the
style line and `Palette: accent #x on #y`. Rules: one clear subject with calm space for a headline, **no text, letters, numbers or logos**, simple illustrated
characters instead of real faces, one palette and style per site, sizes hero 1600x900 (subject right or centre, empty left), about 1200x900, gallery 900x900,
card 800x600, team 600x600, background texture 1600x900 (no subject).

```python
from pixelmath.studio.spec import render, render_business
res = render("Termite drilling (pest control), for a pest control website. Palette: accent #1565c0 on #f5f6f7.", slot="gallery-2", fmt="jpeg")
res.data, res.report                       # JPEG bytes (900x900) and the report: niche, how it was found, palette, mood, camera, bytes
render_business("pest_control", "out/pest_control", sheet="out/pest_control/sheet.jpg")     # all 20 pictures + manifest.json + contact sheet
```
```bash
python3 examples/spec_render_all.py                    # all 99 businesses + 20 types -> samples/spec_run/ (about 17 min with 9 workers)
python3 examples/spec_check.py                         # checks every picture against the spec, writes samples/spec_run/index.html
python3 examples/spec_eval.py                          # how well the studio understands the spec's prompts
curl -s localhost:8000/spec -H 'Content-Type: application/json' -d '{"prompt":"... for a dental clinic website","slot":"hero-1"}' -o hero.jpg
curl -s localhost:8000/spec/business -H 'Content-Type: application/json' -d '{"business":"dental_clinic"}' -o dental.zip     # GET /spec/businesses lists the ids
```

What was done with the spec:

* **Parsed and analysed** (`studio_data/spec/image_ai_spec.json`, `biz_niche.json`; `tools/build_spec_data.py` packs it into `pixelmath/studio/spec_data.json` + `spec_prompts.json`, which ship in the package).
  Of the 99 businesses, 73 had a picture niche; **26 had none** (pest control, laundry, water purifier, funeral, notary, temple, DJ, video editing, drone,
  PG hostel, farm stay, cloud kitchen, tiffin, chai stall, banquet hall, bridal makeup, car rental, bike garage, mobile repair, gift shop, loan agent, diagnostic lab,
  counselling, nutritionist, animal welfare, scrap): they were drawn as new niches from the spec's own gallery / card subjects (123 niches now). Baseline before:
  77.9% of the spec's prompts reached the right niche, 7.2% a wrong one.
* **The business decides the scene.** `"for a <business> website"` is looked up (exact spec name or business type); the subject text is not used to guess the niche.
  All 2180 prompts resolve to the mapped niche (100%). The slot decides size, camera and text zone: hero-1/2 fit (text zone left, headline contrast >= 4.5:1),
  hero-3 close, about, gallery and card use different crops (zoom, pan, mirror) so no two pictures of a site are alike (min perceptual distance 8 of 63 bits).
* **Palette:** accent from the prompt; a dark background gives a dark picture, a light one the niche's own mood. Design styles map to dark / light. A style the engine cannot draw
  (photo-like, 3D, sketch) is reported in `report.style_note` and the default flat illustration is used (honest, not silent).
* **Team portraits** (`pixelmath/studio/portrait.py`): illustrated character, shoulders up, hair / skin / glasses varied, outfit from the role and the business
  (doctor coat, hard hat and hi-vis, chef jacket, headset, cap, apron, tie, whistle; a software "engineer" does not get a hard hat).
* **Background texture:** palette-coloured soft light plus one quiet motif (dots, waves, rings, grid, diagonals), no subject.
* **No text anywhere:** the studio (`stage.NO_TEXT`) never draws letters or numbers (older scenes drew "STOP", "TAXI", "GAME ON", "FRESH BREAD"); a test renders every niche with
  the text drawer watched.
* **Training:** the spec's prompts are classifier captions (`examples/make_spec_training.py`: 1618 train, 552 held out = hero-3, gallery-5/6, card-5/6 of every business).

Measured (`examples/spec_eval.py`, `examples/spec_check.py`):

| Check | Result |
|---|---|
| Production requests (business named in the text): right niche | **2180 of 2180** |
| Rendered: 99 businesses x 20 + 20 types x 10 | **2180 pictures, 0 problems** (size = slot size, file size within budget, hero contrast >= 4.5, no neutral fallback, judge ok) |
| File size (average / largest) | hero 64 / 100 KB, about 61 / 70, gallery 47 / 56, card 34 / 38, team 14 / 19, background 23 / 39 |
| Subject only, no business name (552 held-out prompts) | right 48%, refused 36%, wrong 16% |
| ... by slot | gallery 92% right (the caption says "(pest control)"); card 29% right, 22% wrong; hero 21% right, 25% wrong ("shield and house" names no business) |

Read the last two rows as a limit, not a result: a hero or card caption without its business ("Loaded Sundaes ...") cannot be told apart reliably, so the studio
relies on the business named in the request, as the spec guarantees. The studio draws one illustrated scene per business, so a gallery picture shows the business's props
from another camera, not the exact object in the caption ("Termite drilling" shows the pest-control scene with its drill, sprayer and trap).
