# PixelMath Engine

Text-to-image generator written from scratch and **trainable on your own images**. No pre-trained
model, no API, no third-party package: Python standard library only (`math`, `random`, `struct`,
`zlib`, `json`, `csv`, `re`, `argparse`). Tested on Python 3.9, 3.13 and 3.14 with identical output
on all three.

**Quickest way (web interface for generating and training, backend included, one command):**

```bash
python3 app.py            # backend + web interface + database; opens http://127.0.0.1:8000/ui in your browser (next free port if 8000 is busy)
```

Details are in [PixelMath Studio](#pixelmath-studio-web-interface). The commands below are the same engine from the terminal.

```bash
# generate
python3 -m pixelmath "red house with a tree under a sunset sky" -o scene.png
python3 -m pixelmath "cyberpunk neo city at night" -o city.png --explain
python3 -m pixelmath "ek laal dil aur neela circle" -o shapes.bmp      # Hinglish works
python3 -m pixelmath "लाल घर और पेड़" -o hindi.png                        # so does Devanagari

# train on your own data, then use it
python3 train.py my_data --model my_model.json
python3 -m pixelmath "aqua mossy" --model my_model.json -o out.png

# studio: premium website pictures for 123 niches, hero/about/tiles with a judge (see "Studio")
python3 -m pixelmath "gym with dumbbells in red light" --studio --text-zone left --width 1280 --height 640 -o hero.jpg
python3 -m pixelmath "dental clinic reception, calm blue" --set 6 -o site_pictures/

# creative mode: propose, judge, evolve (see "Creative mode")
python3 -m pixelmath "laptop and coffee cup" --temperature 0.8 -o creative.png
python3 -m pixelmath --imagine --temperature 0.9 -o mashup.png
python3 -m pixelmath "mandelbrot complementary" --temperature 0.8 --explore 300 -o fractal.png   # screen 300 ideas, keep the best
python3 -m pixelmath "fractal tree" -o tree.png          # also: fern, snowflake, dragon curve, sierpinski, flow field, marble

python3 -m unittest discover -s tests          # 198 tests, about 3.5 minutes
```

## PixelMath Studio (web interface)

```bash
python3 app.py                                   # backend + web interface together, opens your browser
python3 app.py --port 9000 --model my_model.json --no-browser
python3 -m pixelmath.app                         # same thing; after `pip install .` the command is `pixelmath-app`
```

It starts the HTTP API and serves the interface from the same process (no Node, no build step, no internet: plain HTML, CSS and
JavaScript in `pixelmath/web/`). Your trained model is kept in `./pixelmath_model.json` (created on the first training; `--model`
changes it). Everything stays on your machine unless you pass `--host 0.0.0.0`, which requires `--api-key`.

| Tab | What you do |
|---|---|
| **Create** | Type a prompt, pick **Plain**, **Creative** (temperature, population, generations, explore) or **Mash-up**, size and seed, press Generate. You see the picture, how the prompt was understood, and in creative modes what the engine thought: critic scores, per-generation progress and "other good ones" you can click to draw. *Save pictures to the gallery* is on by default. *Download PNG*, *Use this prompt & seed* and *Copy API call* (a ready `curl` command for other projects) sit under the picture. |
| **Studio** | The website-picture studio in the browser: describe the business, pick *One picture* or *Site set*, niche (auto or one of 50), mood, accent colour and text area. It shows the picture with a **sample headline in the recommended text colour on the text area** (so you can see the contrast yourself), the judge's report (niche, fallback, scores, contrast, redraws), the set's checks, per-file downloads and *Download all (zip)*. A phrase that fits no business shows a clear fallback note. |
| **Gallery** | Every saved picture (newest first) with search, a favourites filter and "load more". Click one for the big image, its prompt, seed and, for creative pictures, what the engine thought. *Favourite* (kept forever), *Download*, *Use prompt & seed* (jumps to Create and redraws the same picture), *Delete*, or *Clear (keep favourites)*. |
| **Train** | *Pick images*, *Pick a folder* (captions are read from `captions.csv` or `.txt` files next to the images if there are any) or *Use a ready zip*. Each image gets a caption box prefilled from its file name; edit it. Press **Train**: the browser packs a zip, uploads it, and a progress bar follows the job (epochs, error, skipped files). Below it, the **training history** lists every earlier run, also after a restart. Identical image + caption pairs count once. |
| **Dataset** | Everything the model currently learns from, with a preview, caption and file name per image. Search, select (one or many) and **Delete selected**, or click *edit caption*: the model is retrained on what is left (a few seconds, with a progress bar). Removing everything resets the model (the old file is kept as `.bak`). |
| **Model** | What it learned: images, words, how much better than knowing nothing it is on unseen images, the most common words with their colours, and a box to check whether a prompt's words are known. |

### Database (SQLite)

`python3 app.py` keeps a SQLite file next to the model (`pixelmath_model.db`; `--db FILE` moves it, `--no-db` switches it off,
`--gallery-max N` caps the gallery, default 300 pictures, favourites are never dropped). Standard library only, nothing to install.

| Table | Holds | Why |
|---|---|---|
| `gallery` | the picture (PNG), a 160 px thumbnail, prompt, the prompt actually drawn, seed, mode, size, settings, the creative report, favourite flag | Gallery tab, reproducing a picture |
| `jobs` | every training / dataset-edit job with parameters, result, skipped files, error (a job that was running when the server stopped shows as `interrupted`) | training history that survives restarts |
| `dataset` | for each trained image: caption, file name, 64 px preview, which job added it | Dataset tab previews |

The trained model stays in its own JSON file and remains the single source of truth for what it knows, so deleting the `.db`
never breaks generating or training (you lose only the gallery, history and previews; the Dataset tab then shows colour-grid previews).
To back everything up copy `pixelmath_model.json` and `pixelmath_model.db` together (stop the server first). Plain API calls are
**not** saved unless they send `"save": true`, so other projects do not fill your gallery by accident.

Notes: the pictures it makes from training are colour and layout impressions of your captions (see "What training means" below), not new
drawings. With an API key set, the page asks for it once (kept in this browser only). Training uploads are limited to 200 MB here
(`--max-upload-mb`). Progressive JPEGs are not readable; the Train tab lists skipped files with the reason.

## HTTP API (Postman and other projects)

```bash
python3 serve.py --model my_model.json          # http://127.0.0.1:8000  (--model is optional; it enables /train)
```

**Postman:** Import -> choose `api/postman_collection.json` (or Import -> Link -> `http://127.0.0.1:8000/openapi.json`).
Collection variables: `baseUrl` (default `http://127.0.0.1:8000`) and `apiKey` (only if you started the server with one).
Send "Generate image (JSON -> PNG)": Postman shows the picture in the response body. For training use
"Train: upload zip (form-data)": Body -> `data` -> Select File -> a zip; Send; then "Training job status" (it fills `jobId`).

| Endpoint | What it does |
|---|---|
| `GET /health` | liveness (no key needed) |
| `POST /generate` | JSON `{"prompt","size","width","height","seed","format":"png\|bmp","learned":"auto\|always\|off","response":"binary\|base64"}` -> image bytes, or JSON with `image_base64` |
| `GET /generate?prompt=...&size=512` | same, handy in a browser |
| `POST /create` | creative mode: `{"prompt","temperature":0..1,"population","generations","alternatives","max_seconds", ...image fields}` -> image (headers `X-PixelMath-Prompt/-Seed/-Score`) or, with `response=base64`, JSON incl. `creation` (what it thought, scores, rejected variations, alternatives) |
| `POST /imagine` | random concept mash-up judged by the critic: `{"anchor":"cat" (optional),"temperature","attempts", ...}` |
| `GET /gallery`, `GET /gallery/<id>`, `GET /gallery/<id>/image\|thumb`, `POST /gallery/<id>/favourite`, `DELETE /gallery[/<id>]` | saved pictures (needs a database; save with `"save": true` on `/generate`, `/create`, `/imagine`) |
| `GET /dataset`, `GET /dataset/<id>/image`, `POST /dataset/delete`, `DELETE /dataset/<id>`, `POST /dataset/<id>/caption` | list, preview, remove and re-caption trained images (removing or editing retrains the model as a job) |
| `POST /parse` | how a prompt is understood (entities, colours, time, unknown words, words the model knows) |
| `GET /model` | trained model info |
| `POST /train` | multipart field `data` = zip (images + `captions.csv` / `.txt` / `captions.json`), optional `epochs`, `lr`, `l2`, `val_frac`, `fresh`, `grid`, `seed`, `refit`; or a raw `application/zip` body. Returns `202` + `job_id` |
| `GET /jobs/<id>`, `GET /jobs` | training progress (`queued/extracting/reading/training/done/error`, plus `interrupted` after a restart), metrics, skipped files; with a database also old jobs |
| `POST /spec`, `POST /spec/business`, `GET /spec/businesses` | pictures for the [picture spec](#picture-spec-website-pictures-by-slot): one picture at its slot's size, all 20 of a business as a zip, the business list |
| `GET /openapi.json` | OpenAPI 3 spec |

From another project:

```bash
curl -X POST http://127.0.0.1:8000/generate -H "Content-Type: application/json" \
     -d '{"prompt":"red house under a sunset sky","size":512}' -o out.png
curl -X POST http://127.0.0.1:8000/train -F "data=@my_data.zip" -F epochs=80          # then poll /jobs/<job_id>
```

```python
import json, urllib.request
req = urllib.request.Request("http://127.0.0.1:8000/generate", method="POST",
        data=json.dumps({"prompt": "blue ocean with a boat", "size": 256}).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": "..."})   # key only if the server needs one
open("out.png", "wb").write(urllib.request.urlopen(req).read())
```

```js
const r = await fetch("http://127.0.0.1:8000/generate", {method: "POST", headers: {"Content-Type": "application/json"},
                      body: JSON.stringify({prompt: "mandala", size: 256, response: "base64"})});
const {image_base64, mime} = await r.json();            // from a browser page start the server with --cors-origin https://your.site
```

Errors are always JSON: `{"error": {"code": "...", "message": "..."}}` with 400/401/403/404/405/409/413/415/501/503.
Unknown JSON fields are rejected (a typo like `sise` gives a 400 instead of being ignored).

**Safe defaults:** listens on `127.0.0.1` only; `--host 0.0.0.0` is refused unless you set an API key (`PIXELMATH_API_KEY=...`,
sent as `X-API-Key` or `Authorization: Bearer`); Host-header check against DNS rebinding in local mode; CORS is off unless
`--cors-origin`; **cross-site request forgery is refused**: a POST/PUT/PATCH/DELETE that carries an `Origin` header other than the
server's own (same host and port as the `Host` header) or the `--cors-origin` value, or that carries `Sec-Fetch-Site: cross-site`,
gets 403 `cross_origin`, and so does a `GET /generate` with `Sec-Fetch-Site: cross-site` (another site's `<img src>`) unless
`--cors-origin` is set; requests without those headers (curl, Postman, scripts, other backends) are unaffected; image size capped (`--max-size`, default 1024); at most `--max-concurrent` (2) renders at once, others queue
up to `--queue-wait` (10 s) then get 503; JSON bodies <= 64 KB; uploads <= 100 MB and <= 300 MB unzipped, <= 64 MB per file
(`--max-upload-mb`, `--max-unzipped-mb`), each uploaded image <= 16 megapixels (bigger ones are skipped and listed); zips are unpacked with zip-slip, zip-bomb, symlink and file-count protection and
only images/captions are extracted; one training job at a time (409); a failed job never touches the existing model;
tracebacks never reach clients. It is a plain HTTP server on Python's standard library, so for use over the internet put it behind
a TLS reverse proxy (the API key is otherwise sent in clear text) and add rate limiting there.

## Creative mode (it thinks before it draws)

A plain render is deterministic: one prompt, one picture, and a fixed checker could only say yes or no. Creative mode wraps
the renderer in a loop that **proposes, judges and improves** (`pixelmath/creative.py`, still standard library only):

| Idea | What it does here |
|---|---|
| **Temperature** (`--temperature 0..1`, API `temperature`) | At 0 the engine always takes the single safest choice, so you get exactly the plain render. Above 0 it picks among the *top three* candidates for each decision (extra prop, setting, final winner), the best one still most likely. Higher = bolder. |
| **Markov chain of props** | A table of "which prop follows which" (built in from the concepts, venue interiors and decor rules; `Chain.learn_captions()` and a loaded `--model` add what *your* captions pair together). New props are sampled from it, so a laptop gets a coffee cup or a plant, a tractor gets a cow, not a toothbrush. |
| **Genetic search** (`--population`, `--generations`) | Each candidate is a small *genome*: extra props, time of day / weather / sky colour / background colour / palette words, layout seed. The critic ranks a population, the best survive, children mix the genes of two parents (crossover) and get random changes (mutation), with one fresh immigrant per generation. |
| **Critic** (replaces the fixed validation) | Hard gates, never negotiable: nothing the prompt asked for may be dropped, recoloured or shrunk, the quoted text and the picture type must stay, every requested prop must really be drawn, the image must not be blank. Soft scores: clarity, colour richness and harmony, balance, how well the props go together (the chain), and novelty against the other candidates (weighted more as temperature rises). |
| **Mash-ups** (`--imagine`, `/imagine`) | Two ideas that rarely meet (or your `anchor` plus a random one), judged by the same critic; about a quarter of random pairs are thrown away (for example, a prop that the scene cannot draw), the first good one is polished by the search. |

```bash
python3 -m pixelmath "laptop and coffee cup" --temperature 0.8 --seed 3 -o out.png
#   thinking: tried 26 candidates ... chosen genome -> extras: monitor; bg: on a violet background ... score 0.825 vs plain render 0.701
python3 -m pixelmath cat --imagine -o mashup.png          # "cat" is kept, the other idea is random
python3 examples/creative_gallery.py gallery.png          # plain vs creative, side by side
curl -s localhost:8000/create -H 'Content-Type: application/json' \
     -d '{"prompt":"tractor","temperature":0.8,"response":"base64","size":256}'
```

Every result is reproducible: the printed prompt plus `--seed` through the plain renderer gives the same picture, and the
same arguments give the same creative result (unless a `max_seconds` budget cuts the search short). A creative result never scores
below the plain render of the same prompt. Cost: roughly 25 small renders, about 1 to 3 seconds.

**Honest limits:** this recombines the props, scenes and colours the engine already has; it can find combinations you
would not have written, but it cannot invent a new drawing or a new object, and the critic measures structure and colour, not
taste, so some mash-ups are strange (an excavator next to a sofa). Pictures made only of shapes with explicit colours vary just
their layout seed. Photo-realism is still out of reach.

## Generative maths pictures and colour theory

Four ideas for more creativity were checked against what the engine already had:

| Idea | Verdict |
|---|---|
| Smooth noise instead of `random()` pixels | The engine already used smooth (value) noise for skies and terrain. Added true 2D **Perlin gradient noise** (`Noise.perlin2/fbm2`) for the new pictures; the existing scenes were left alone so their output does not change. |
| Fractals, L-systems, flow fields | **New** (`pixelmath/generative.py`), see below. |
| Colour-theory palettes | **New** (`pixelmath/palette.py`). Abstract, tile, mandala and shape pictures used golden-ratio hue stepping; they now use a harmony rule anchored on your colour. |
| Validation as a filter over many variations | Already the creative critic; added `--explore N` / API `explore` to screen hundreds of ideas cheaply first. |

| Say | Draws (mode) |
|---|---|
| `mandelbrot`, `julia`, `fractal` | escape-time Mandelbrot / Julia sets with smooth colouring, from a list of known-rich regions with random zoom (`fractal`) |
| `fractal tree`, `lsystem`, `fern`, `snowflake` / `koch`, `dragon`, `sierpinski` | recursive tree, Barnsley fern (IFS), Koch snowflake, dragon curve, Sierpinski triangle (`lsystem`) |
| `flow field`, `swirl` | about a thousand strokes following a Perlin vector field (`flow`) |
| `plasma`, `perlin noise`, `texture`, `marble` | domain-warped Perlin noise, marble veins (`texture`) |
| `analogous`, `complementary`, `triadic`, `tetradic`, `monochrome`, `split complementary` | the colour rule for any of the above, and for abstract / tiles / mandala / shapes. Your own colour is the base hue (`red mandelbrot complementary`), otherwise the base hue comes from the prompt, so the same prompt always gets the same palette |

Every seed is a different picture (a different region, branching, field). In creative mode the colour rule, the base hue and the
seed are genes, so the critic can throw away empty or muddy variations. `--explore 300` first judges 300 random ideas at thumbnail
size (about 10 ms each) and breeds from the best few; `python3 examples/generative_gallery.py out.png` draws a sheet of all kinds
([business_check/generative_gallery.png](business_check/generative_gallery.png)). Fractals are computed on at most 320 px and textures on
160 px, then smoothly enlarged (a full-size Mandelbrot in pure Python would take minutes); L-systems and flow fields are drawn at the
real size. A flow field takes about 2 s at 384 px.

## Studio: premium website pictures for 123 business niches

```bash
python3 -m pixelmath "wood fired pizza on a board" --studio -o hero.jpg                       # one picture, niche read from the prompt
python3 -m pixelmath "gym with dumbbells in red light" --studio --text-zone left --width 1280 --height 640 -o hero.jpg
python3 -m pixelmath "dental clinic reception, calm blue" --set 6 -o site_pictures/ --accent "#2e86de" --mood cool
python3 -m pixelmath --list-niches
curl -s localhost:8000/set -H 'Content-Type: application/json' -d '{"prompt":"bakery","count":6,"accent":"#d98e32","text_zone":"left"}' -o site.zip
```

What it is: for a website's first screen, About section and gallery. Not clip-art stickers but layered scenes: an out-of-focus backdrop (depth
of field), a sharp middle layer with contact shadows and ambient occlusion, soft foreground accents, a key light, mood grading, vignette and film
grain. 123 niches (restaurants and street food, cafes, bakeries, retail and boutiques, clinics, dental, eye care, physio, ayurveda, gym, yoga, spa, salon,
mehendi, tattoo, pets, SaaS, apps, law, accounting, insurance, architects, consulting, recruitment, coworking, schools, tuition, music, driving school,
real estate, construction, plumbing, painting, welding, AC repair, movers, security, solar, farm, car repair / wash / showroom, tyres, taxi, hotel, photography,
weddings, events, tent house, catering, travel, visa, NGO, logistics, pest control, laundry, water purifier, scrap, funeral, notary, temple, DJ, video editing,
drone, PG hostel, farm stay, cloud kitchen, tiffin, chai stall, banquet hall, bridal makeup and more), each with its own props,
backdrop and surface. Pure Python, no model, no internet. It is illustrated, not photo-realistic.

| You control | How |
|---|---|
| Colours | `--accent #hex|name` (the whole picture follows it; walls, floor, accents, signage) |
| Mood | `--mood warm|cool|dark|light` (grading, light colour, practical lights in dark) |
| Text space | `--text-zone left|center|bottom`: the subject moves away from that area and a soft panel is added only if needed so the text has contrast >= 4.5:1; the report tells you which text colour to use (`text_color`) |
| Prompt | English, Hinglish and Hindi (Devanagari) are understood. "gym ... in red light" = dark mood + red accent; "calm blue" = cool + blue. |

**A prompt that fits no niche never gets a wrong picture:** you get a neutral abstract in the accent colour and `fallback: true` in the report.

**Sets** (`--set N`, `make_set(prompt, count, seed)`, `POST /set`): 3 to 8 pictures for one site in one style (same palette, mood, light): hero
1280x640 with the text zone, about 640x600, then gallery tiles (close-up, detail, wide, mirrored ...). Any two pictures must differ by at least 14 of 63
bits of a perceptual hash, otherwise the later one is drawn again.

**The judge** runs on every picture and the answer is in `report`: `scores` (subject visible, text contrast, detail density, colours, duplicate
distance), `redrawn` (how many extra tries the judge asked for), `fallback`, `contrast`, `text_color`, and for sets `min_distance`, `palette_family`.

**File size:** pictures are written as JPEG by a pure-Python baseline encoder (`pixelmath/jpegwrite.py`: 4:2:0, optimised Huffman tables, quality
lowered automatically until the file fits): hero < 60 KB, about < 40 KB, tiles < 25 KB.

**Training:** `train.py` reads a `manifest.jsonl` with `{"image", "caption", "niche", "mood"}` lines. Besides the colour model it trains a niche
classifier (naive Bayes) that is stored in the model file. The studio uses it to understand indirect or messy prompts and, just as important, to veto a keyword
match that the whole sentence contradicts. The data of this project is in `studio_data/` (pictures drawn by the engine's own niche generators + captions
written by the author: `captions_train.json`, `prompts_train.json`, `captions_negative.json`); `examples/make_studio_dataset.py` rebuilds it,
`tools/export_niche_nb.py` ships the classifier inside the package (`pixelmath/studio/niche_nb.json`), `examples/studio_eval.py` measures everything below.
The classifier only needs captions, so `python3 tools/export_niche_nb.py --captions` builds it straight from the caption files (the same result as
`make_studio_dataset.py` + `train.py`, without drawing 7000 pictures). **The shipped classifier is trained on the author's captions only:** the picture
spec's captions (`spec_train.json`) are added only with `PIXELMATH_CLIENT_SPEC=1` (measured below: leaving them out changes `blind_v4` by 0.4 points).

**Measured** (`python3 examples/studio_eval.py --model studio_model.json --sheets`, results in `samples/studio_eval.json`, proof sheets
`samples/studio-<niche>.jpg` for restaurant-italian, gym, dental, saas, kurti-store, salon, bakery, yoga, real-estate, school):

The numbers come from five sets of prompts. Only `blind_v4` has never been used to fix anything; each earlier set was used for some fix after it was first measured, so its figure is optimistic.
**Since 2026-10-31 the shipped classifier is trained only on the author's captions** (before, 1618 captions from the picture spec were in it as well; they were
removed, and the 26 niches that had only spec captions got 24 new author-written captions each, written without looking at the spec or the keyword lists).
Measured on 2026-10-31 with the classifier before and after that change (same matcher, same thresholds, `examples/blind_eval.py`):

| Prompt set | Prompts | Right niche (before -> **now**) | Fallback | Wrong niche | Off-niche prompts wrongly matched |
|---|---|---|---|---|---|
| `holdout_prompts.json`, 97 original niches (used to find keyword gaps) | 582 | 96.4% -> **96.7%** | 3.4% -> 3.3% | 0.2% -> **0.0%** | 2 -> 2 of 36 |
| `blind_v2.json` (used to add vocabulary and pick the thresholds) | 582 | 94.0% -> **93.6%** | 5.5% -> 5.5% | 0.5% -> 0.9% | 2 -> 1 of 40 |
| `blind_v3.json` (its misses were fixed afterwards) | 485 | 96.3% -> **96.9%** | 3.7% -> 3.1% | 0.0% -> 0.0% | 2 -> 2 of 40 |
| **`blind_v4.json` (written blind, never used for any fix)** | 485 | 92.4% -> **92.0%** | 5.8% -> 6.0% | 1.9% -> **2.1% (10 prompts)** | 10 -> **9 of 40** |
| `holdout_prompts.json`, the 26 newer niches (subject-only captions from the picture spec, no business named) | 130 | 47.7% -> 47.7% | 37.7% -> 36.2% | 14.6% -> 16.2% | |

Keywords alone (no classifier) on the 97-niche hold-out: 70.1% right, 27.0% fallback, 2.9% wrong. The figure first published for `blind_v4` was 92.2% / 6.0% / 1.9%,
9 of 40; the matcher has changed a little since, hence the "before" column. The change is within two prompts on every set: `blind_v4` lost two right answers
and gained one wrong one (10 instead of 9), and one fewer off-niche prompt gets a niche picture.

Read `blind_v4` as the honest figure for prompts a client types: about 92% right, 6% refused (safe), and about 2% a wrong niche. Its wrong matches are neighbouring
niches (coaching vs school, logistics vs movers, recruitment vs consulting, "modular kitchen" vs carpentry) and 9 of 40 off-niche or scene-only prompts (a mushroom farm,
a cup of tea by a window, an autumn path) still got a niche picture; the fallback is meant to catch those, so this is the main open weakness of the prompt
matcher. The last row is hard on purpose (a hero caption such as a house and a shield names no business) and was not used to train anything.
A website generator that passes the business *type* (`pixelmath/studio/site.py`) does not go through this matcher at all.
Every miss is listed by `python3 examples/blind_eval.py studio_data/blind_v4.json show`.
Colour prediction on 97 hold-out pictures (RMSE 0-255, lower is better): untrained 60.6, average picture 57.6, **trained 33.6**.

| Pictures: 97 niche prompts x 3 seeds (256x160) | |
|---|---|
| right subject | **94.8%** (276 of 291) |
| fallback | 5.2% (15) |
| **wrong subject** | **0** |
| off-niche prompts, 108 pictures: neutral fallback | 102 of 108 (the 6 others are the cricket stadium and robot-arm prompts, near real niches) |

Weak spots: fallbacks on the old hold-out are mostly Hindi and Hinglish phrasing the keyword lists do not know yet (add words in `pixelmath/studio/vocab.py`,
retrain with `examples/make_studio_dataset.py`, `train.py --fresh`, `tools/export_niche_nb.py`). The newer 47 niches are less polished than the first 50
(for example catering, recruitment, architect); in a hero the subject fills about 40% of the width (the right side, so the headline keeps the left).

Sets of 6 (hero 1280x640 + about + 4 tiles), 10 niches: time 6.5 to 8.7 s (limit 20), min perceptual distance 14 to 24 bits (limit 14), palette family 0.76 to 0.96,
hero text contrast 4.73 to 6.26 (limit 4.5), hero 31395 to 50083 bytes (limit 60000), largest tile 24715 bytes (limit 25000), judge ok in all.

**Real-example check** (16 client-style prompts through `POST /scene` and a `POST /set`, pictures and reports in `samples/real_examples/`): it found
and fixed these bugs, each now covered by a test: "underwater scuba diving school" drew the *school* scene (the word "school" alone was decisive: now a
lookalike-word guard, avoid terms and near-miss training captions make it a fallback); "bike showroom" / "furniture showroom" drew the car showroom
("showroom" alone is no longer decisive); the Hindi plural खिलौनों did not match खिलौने (word-stem matching); a fallback picture was redrawn
needlessly (smooth is the point of a fallback; only contrast is judged now); a 1280x640 picture from `/scene` was squeezed to the 25 KB tile budget
(the budget now follows the picture size); the Italian restaurant hero showed a hard edge where its table ended (backdrop extended).

What these numbers do not say: the prompts are the kind a client types for these 97 niches; unusual businesses fall back (that is the intended behaviour, not
a failure), and the engine draws illustrations, not photographs. Two of the ten sets sit exactly at the distance limit (14 bits) and tiles are within
0.3 KB of their 25 KB budget: the judge redraws or lowers JPEG quality when needed, but there is no spare room. Neighbouring niches can still be swapped
for each other on borderline wording ("furniture showroom" gives interior design, "pilates studio" gives yoga): the hold-out shows no such case, real prompts will.

## Picture spec: website pictures by slot

The owner's picture spec (`Image-AI-training.pdf`, 62 pages) says how every website of the site generator asks for its pictures, and it ships with the
package (`pixelmath/studio/spec_data.json` and `spec_prompts.json`, built from `studio_data/spec/` by `python3 tools/build_spec_data.py`):

* a **system prompt**: one clear subject with calm space for a headline, **no text, letters, numbers, logos, watermarks or real brands**, simple illustrated
  characters instead of recognisable people, one drawing style, one light and one palette for all pictures of a site;
* a **STYLE LINE** added to every request ("friendly flat illustration, clean vector shapes, soft shading, one clear subject, rich but harmonious colours, no text, ...",
  `pixelmath.studio.spec.STYLE_LINE`);
* **25 design styles** (minimal, cyberpunk, glass, luxe dark, trust navy, ...): 18 mean a light page, 7 a dark one;
* **99 businesses x 20 pictures** and **20 generic business types x 10 pictures** (hero x3, about, gallery x6) for businesses without a pack: 2180 prompts,
  each `"<subject>, for a <business> website"` plus the style line and `Palette: accent #x on #y`; 95 businesses have two palettes, 4 have one.

| Slot | Size | What is drawn |
|---|---|---|
| `hero-1`..`hero-3` | 1600x900 | the business's scene, subject right or centre, empty left for the headline (contrast >= 4.5:1 for the reported text colour) |
| `about` | 1200x900 | the scene from another camera |
| `gallery-1`..`gallery-6` | 900x900 | close-ups, details, wide and mirrored crops of the scene |
| `card-1`..`card-6` | 800x600 | more crops (zoom, pan, mirror) |
| `team-1`..`team-3` | 600x600 | "portrait of a friendly <role>, illustrated character, shoulders up": outfit from the role and the business |
| `background` | 1600x900 | soft abstract texture in the palette (dots, waves, rings, grid or diagonals), no subject |

```python
from pixelmath.studio.spec import render, render_business, full_request
res = render("Termite drilling (pest control), for a pest control website. Palette: accent #1565c0 on #f5f6f7.", slot="gallery-2", fmt="jpeg")
res.data, res.report                       # JPEG bytes (900x900) and the report: niche, how it was found, palette, mood, camera, bytes
render_business("pest_control", "out/pest_control", sheet="out/pest_control/sheet.jpg")     # all 20 pictures + manifest.json + contact sheet
```
```bash
curl -s localhost:8000/spec/businesses                                             # the 99 business ids with niche and palettes
curl -s localhost:8000/spec -H 'Content-Type: application/json' -d '{"prompt":"Smiling patient, for a dental clinic website","slot":"hero-1"}' -o hero.jpg
curl -s localhost:8000/spec/business -H 'Content-Type: application/json' -d '{"business":"dental_clinic"}' -o dental.zip     # about a minute
python3 examples/spec_render_all.py                    # (source checkout) all 99 businesses + 20 types -> samples/spec_run/ (about 17 min with 9 workers)
python3 examples/spec_check.py                         # checks every picture against the spec, writes samples/spec_run/index.html
```

`POST /spec` takes `{prompt, slot?, seed?, accent?, bg?, niche?, design_style?, format?, response?}` (the slot is inferred from a team / background prompt,
else hero); `POST /spec/business` takes `{business, palette?: 0|1, seed?, format?}`. Like every POST they answer 403 `cross_origin` to a browser request from
another site, and 501 `spec_unavailable` only if the spec's data files are missing from the installation. `PIXELMATH_SPEC_DIR` (a folder with
`spec_data.json`, and `spec_prompts.json` or the full `image_ai_spec.json`) replaces the shipped data.

How it works:

* **The business decides the scene.** `"for a <business> website"` is looked up (exact spec name, business type, or all words of a name); only an unknown business
  goes to the prompt matcher. The subject text alone does not identify the business (212 of 297 hero prompts share no word with it: "shield and house" for pest control),
  so it is not used to guess the niche. All 2180 prompts resolve to the mapped niche. 26 businesses had no niche before 1.6 and were drawn as new niches
  (pest control, laundry, water purifier, funeral, notary, temple, DJ, video editing, drone, PG hostel, farm stay, cloud kitchen, tiffin, chai stall, banquet hall,
  bridal makeup, car rental, bike garage, mobile repair, gift shop, loan agent, diagnostic lab, counselling, nutritionist, animal welfare, scrap): 123 niches now.
* **The slot decides size, camera and text zone**; pictures of one business differ by at least 8 of 63 perceptual-hash bits (a too-similar one is drawn again).
  The studio draws one illustrated scene per business, so a gallery picture shows the business's props from another camera, not the exact object in the caption.
* **Palette:** accent from the prompt; a dark background gives a dark picture, a light one the niche's own mood. A style the engine cannot draw (photo-like, 3D, sketch)
  is reported in `report.style_note` and the flat illustration is used.
* **No text anywhere:** the studio (`stage.NO_TEXT`) never draws letters or numbers; a test renders every niche with the text drawer watched.

Measured (`examples/spec_eval.py`, `examples/spec_check.py`): 2180 of 2180 production requests reach the right niche; all 2180 pictures rendered with 0 problems
(size = slot size, file within budget, hero contrast >= 4.5, no neutral fallback, judge ok); average / largest file: hero 64 / 100 KB, about 61 / 70, gallery 47 / 56,
card 34 / 38, team 14 / 19, background 23 / 39. Without the business name (552 held-out subject-only prompts) only 48% reach the right niche (gallery 92%, card 29%,
hero 21%): a limit, which is why the request must name the business, as the spec guarantees. The full analysis is in `studio_data/spec/ANALYSIS.md`.

### Website bridge: pictures that fit a generated business site

`pixelmath/studio/site.py` is for a website generator (for example Core-Craft AI). It takes the business, not a prompt:

```python
from pixelmath.studio.site import site_pictures
out = site_pictures({"business_type": "dental", "profile": None, "brand": "Harmony Dental", "mood": "calm"},
                    {"primary": "#0e7490", "dark": False}, seed=1, count=6, out_dir="site/images", text="braces implants", subdir="images")
# out["images"]["hero"|"about"|"tiles"] -> {src, width, height, bytes, alt, text_color, contrast}; out["niche"], out["fallback"], out["mood"]
```

* Business type (77 Core-Craft types) and sub-niche (profile) map to a picture niche; the business words refine it (a "school" that says "JEE tuition" gets
  the tuition scene, a "garage" that says "car wash" the wash scene, "events" + "mandap" the wedding scene).
* The site's primary colour becomes the picture accent and its mood the picture mood (a dark site gets a dark picture).
* The hero keeps the left side free for the headline and reports the headline colour (`text_color`) with contrast >= 4.5:1.
* A business with no fitting niche gets a neutral abstract in the brand colour and `fallback: true`, never a wrong scene.
* Files are written as `images/hero.jpg`, `about.jpg`, `tile-N.jpg` plus `images.json`: about 110 to 190 KB of pictures per site instead of base64 inside the page.

Tested on 54 real sites generated by Core-Craft (`samples/final_sites/` holds the last 30: open `<site>/preview.html`) (restaurant, dental, bakery, gym, yoga, SaaS, kurti, salon, tattoo, taxi, hotel, catering, physio, architect,
driving school, pet shop, furniture, welding, south Indian restaurant, optical, mehendi, coworking, robotics lab, plumber): every one got its own niche,
no fallback, hero contrast 4.56 to 13.2. `tests/test_site.py` covers the mapping and the files.

**Adding a niche** (about 100 lines): write `@sprop` props and a `@niche(...)` scene function in a new module of `pixelmath/studio/niches/`; see
`stage.py` (docstring), `craft.py` and the reference `niches/food.py`; check it with `python3 examples/check_niches.py sheet.png your-niche`.

## How it works

| Part | File | Job |
|---|---|---|
| Tokenizer, parser, vectorizer | `tokenizer.py` | English/Hinglish/Devanagari text -> entities (object, colour, size, position, count) + scene flags; 32-number hashed text vector |
| Style network | `neural.py` | Tiny fixed-seed MLP -> per-prompt hue/brightness/grain variation (untrained) |
| Scene composer + painters | `compose.py`, `painter.py`, `raster.py` | Anti-aliased signed-distance shapes, noise terrain, glow; draws sun, sea, city, trees, shapes, mandalas... |
| **Learned model** | `learn.py` | Word -> appearance model trained from *your* images (below) |
| Image readers | `imageread.py` | PNG (all types, Adam7), BMP, baseline JPEG, written from scratch |
| File writers | `imagefile.py` | PNG and BMP bytes, atomic write |
| Training command | `trainer.py` / `train.py` | CLI described below |

Routing: if the built-in lexicon understands the prompt, the procedural painters draw it. If it understands
nothing (e.g. "aqua mossy") and a trained model knows a word of it, the model draws it. `--learned always`
prefers the model whenever it knows any word; `--learned off` ignores it.

## Training on your own data

### What "training" means here (read this first)

The model learns, from your (image, caption) pairs, **what each word looks like at colour-grid level**:
palette, brightness, where the light and dark regions sit. It is a bag-of-words linear regressor from
words to a 16x16 colour grid (trained with AdaGrad, held-out validation, early stopping). It combines words
it learned separately: after seeing "aqua mossy" and "coral sandy" it can draw "aqua sandy".

It **cannot** learn detailed shapes or objects. Output from the learned path is a smooth colour/lighting field
with procedural texture, not a drawing of a dog. Detailed objects come from the procedural painters; to add a
new object, add a painter (`painter.py`) and its words (`tokenizer.py`). Learning real detail needs
GPU-scale neural networks, which is outside "pure Python, no external model".

### Data format

Put images (`.png`, `.jpg`, `.jpeg`, `.bmp`) in a folder. Captions are found in this order:

1. `captions.csv` in that folder, columns `file,caption` (also accepted: `filename/image/path/name` and
   `text/prompt/description/label`) or `captions.json` (`{"a.png": "caption"}`).
2. A `.txt` next to the image with the same name (`a.png` + `a.txt`).
3. The folder and file name (`sunset/beach_01.jpg` -> "sunset beach"). Works, but descriptive captions train much better.

Folder names are added to every caption inside that folder (`wallpapers/Big_Sur.jpg` -> "wallpaper big sur"),
so name folders by a real label or keep them neutral. A `captions.csv` / `captions.json` may sit in the data root
or in any sub-folder. Unsupported files (webp, heic, gif, tiff, truncated or corrupt images) are listed as skipped,
never silently used.

Tips: caption what is *visible* ("orange sky over dark mountains, calm lake"); 50+ varied images is a sensible
start; digits are ignored; one word can be shared by many images (that is how it learns the word's look).

### Commands

```bash
python3 examples/make_demo_dataset.py demo_data         # optional: a ready-made tiny dataset
python3 train.py demo_data --model demo_model.json      # first run creates the model
python3 train.py new_images --model demo_model.json     # later: add new data, old data is kept
python3 train.py my_data --model m.json --fresh         # start over (old file is kept as m.json.bak)
python3 train.py my_data --model m.json --preview prev/ # also save what the model predicts
```

Options: `--epochs 80`, `--lr 0.3`, `--l2 1e-4`, `--val-frac 0.15`, `--patience 8`, `--grid 16`
(new models only), `--no-refit`, `--seed`, `--words N`.

The training samples are stored inside the model file, so every run retrains on old + new data together
(no forgetting). Adding the same images again is a no-op. Each save also writes `<model>.bak`.

### Reading the report

```
held-out check (10 images never trained on): rmse 6.6 vs 63.8 for the 'average image' baseline -> 99% lower error
```

15% of the data is held out and never trained on; the number compares the model's error on it with the error of
just predicting the average image. Under ~10% improvement means it learned little (more or more varied data
needed). With a small dataset the single-split number is **noisy** (22 held-out images gave 44-60% across runs on the same data;
a 6-split cross-validation gave 30%): trust it as a rough signal, and expect it to stabilise as you add data. It is
optimistic if your dataset has many near-duplicate images (same caption, same scene).
After choosing the best epoch, the model is retrained on all data for that many epochs (`--no-refit` to skip).
Below 10 samples no held-out check is possible and training mostly memorises (a warning is printed).

### What was verified

* **Real external data, clean-room:** 136 real wallpaper photos (HEIC converted to JPEG, captions from file names such
  as `Catalina_Sunset`, `Chroma_Red_Light`) plus 10 real photos with a `captions.csv`, mixed with deliberately broken
  files, trained from a fresh copy of the project on Python 3.9 and then used from 3.14 and updated with 3.13.
  Words learned the right colours from the photos (red hue 0 deg, orange 15, yellow 53, blue 209, purple 246,
  pink 337; `dark` came out near black, `light` pale). Cross-validated gain over the average-image baseline on
  this small noisy set: about 30%, flat across learning rates 0.03-0.3, so the defaults were left unchanged.
  What the model draws is a *blurry colour/layout field* (e.g. "colorful candles orange background" gives an orange
  top and coloured vertical stripes), as described above.
* Synthetic data with known answers: held-out word pairs never seen together were drawn with RMSE 5.0/255
  vs 80.9 for the average image; new words added later learned the right colours.
* Hard random-prototype data (500 samples, 80 words): held-out RMSE 8.5 vs 42.3 baseline (noise floor ~7.7).
* Readers: PNG matrix of every colour type x bit depth x filter type x Adam7; BMP 8/24/32-bit; real 4K photos
  (PNG and JPEG) give thumbnails within 1.8/255 of the exact box average; JPEG vs PNG of the same photo within 2/255.

### Reader limits

* JPEG: baseline/sequential Huffman only (cameras and web). Progressive and arithmetic JPEG, WebP, HEIC, TIFF
  are rejected with a clear message per file (the run continues and lists skipped files). Re-save as PNG.
* Size: at most 40 megapixels per image for `train.py` (a 24 MP camera photo is fine) and 16 megapixels per image uploaded to
  the server; larger images are skipped with a clear reason, before anything is allocated. Decoding is pure Python, so the
  worst case at the server limit (a 16 MP, 16-bit RGBA PNG) takes about 4 s and about 330 MB of RAM; an 8-bit 16 MP PNG about 170 MB.
* EXIF rotation is ignored (a phone photo stored sideways trains sideways). CMYK JPEG is unsupported.
* PNG alpha is composited on white. Images are centre-cropped to a square before shrinking.
* Pure Python speed: a 4K photo loads in ~2 s (JPEG) to ~4 s (PNG); a 500-sample, 80-epoch training run (16x16 grid) takes about
  35 s. JPEG decoding reads only block averages (1/8 scale), which is all a thumbnail needs.

## Production notes

Checked in an audit of this project:

| Area | Result |
|---|---|
| Crash resistance | Fuzzed with 1500+ random prompts incl. empty, binary, Devanagari, 20k-char and 6000-digit inputs at several sizes; one real crash found (huge digit string) and fixed, kept as a regression test |
| Determinism | Same prompt + seed gives byte-identical output on Python 3.9, 3.13, 3.14 |
| Limits | Prompt <= 2000 chars; size 16..2048 px per side (2048x2048 = ~14 s, ~600 MB RAM; 4096 would need ~2.4 GB so it is refused); counts capped at 24 |
| Errors | Bad extension, unwritable path, missing/corrupt model, bad image: clear message and exit code, no tracebacks |
| Files | Images and models are written to a temp file then renamed, so an interrupted run never leaves a half-written file |
| Model file | Plain JSON (no pickle, nothing executable); strictly validated on load (format, version, shapes, finite numbers) |
| Speed | 512x512 ~1 s, 1024x1024 ~3 s |
| Hostile input | 12,000 randomly corrupted PNG/BMP/JPEG files and 1,500 corrupted model files: every one either decodes or is rejected with a clear error; no crashes, no hangs, peak RAM 38 MB for those (small) files (a bug where a forged PNG header allocated 300 MB was found and fixed). A *valid* huge image is a different case: decoding needs several bytes per pixel, so images are capped at 40 MP (`train.py`) and 16 MP (server uploads); a 778 KB 10000x10000 16-bit PNG is now refused instantly instead of taking 2 GB and 24 s |
| Interrupts and bad paths | Ctrl-C leaves the model file untouched with a short message; unwritable or missing model folder is detected *before* training starts; corrupt model suggests `--fresh` |
| Tests | 203 unit/integration tests (`python3 -m unittest discover -s tests`, about 3.5 min) |

Wheel: `python -m build --wheel` (setuptools >= 77) gives a wheel with only the `pixelmath` package, its data files
(web interface, `studio/niche_nb.json`, the picture spec's `studio/spec_data.json` and `studio/spec_prompts.json`) and the licence texts; it was
installed in a fresh venv and `pixelmath`, `pixelmath --studio`, `render()` / `render_business()` of the picture spec and the `/spec` endpoints were run
from it. Your models, databases, `samples/`, `studio_data/` (the spec's sources stay in `studio_data/spec/`), `examples/`, `tools/` and `tests/` are not
in it, and the shipped niche classifier is trained on the author's captions only.
Not verified: Windows/Linux (developed on macOS), Python 3.8 or earlier (declared `>=3.9`). Nothing external is needed,
so `python3 -m pixelmath` and `python3 train.py` also work straight from the folder.

Your training images stay on your machine (nothing is sent anywhere). Whether you may train on a given image is
your responsibility.

**Licence:** the project is MIT licensed (`LICENSE`, Copyright (c) 2026 ayushmishra950). The picture spec (`Image-AI-training.pdf`, the data derived
from it in `studio_data/spec/`, `studio_data/spec_train.json`, `spec_holdout.json` and the package's `studio/spec_data.json` / `spec_prompts.json`) is the
owner's own document, so there is no third-party restriction on it. The Devanagari letter skeletons in
`pixelmath/devanagari.py` are derived from Noto Sans Devanagari and stay under the SIL Open Font License 1.1 (text in
`LICENSES/OFL-NotoSansDevanagari.txt`, also shipped inside the package as `pixelmath/LICENSES/`), so the package licence is
`MIT AND OFL-1.1`.

## What it can draw (procedural path)

**Business props (flat-illustration style, 138 of them, see `business_check/props_gallery.png`)**

| Area | Props |
|---|---|
| Food and drink | pizza, coffee/tea cup, croissant, bread, burger, cake, cupcake, ice cream, plate of pasta, wine glass |
| Retail | shoes, shopping bag, gift box, t-shirt, watch, sale tag, shopping cart |
| Tech and office | laptop, monitor/dashboard, phone, tablet, camera, headphones, book, document, certificate, globe, pencil, chart, light bulb, graduation cap |
| People | person, student, doctor, chef, businessperson, team, yoga/meditation, wedding couple |
| Vehicles | car, truck/van, bus, bicycle, airplane |
| Buildings | hotel/resort, villa, apartment, university/school, hospital/clinic, cafe, bakery, restaurant, shop/boutique |
| Home | sofa, lamp, plant, bed, chair, bookshelf |
| Wellness, events, trust, web | lotus, candles, balloons, trophy, dumbbell, medical cross, suitcase, bouquet, tent, chat bubbles, review card, shield, coins, map pin |
| Pets and farm animals | dog, cat, rabbit, goldfish, parrot, cow, sheep, horse, chicken, elephant |
| Machinery and energy | tractor, excavator, tower crane, forklift, wind turbine, solar panels, factory |
| Tools and trades | wrench, hammer, screwdriver, drill, saw, paint roller, tap/faucet, toolbox, ladder, hard hat, scissors, sewing machine, thread spool, plug, gear, comb, broom, bucket |
| Playground, sports, kids, workers | swing, slide, seesaw, football, cricket set, child, construction worker |
| Emergency and rescue | ambulance, fire truck, police car, firefighter, police officer, fire hydrant, fire extinguisher |
| Dental and medical kit | tooth, toothbrush, dental chair, dentist, pills, stethoscope, syringe, thermometer |
| Winter sports | skier, ice skater, snowboard, skis, ice skate, snowman, sled, ice hockey |

Words, plurals, Hinglish (`kitab`, `gaadi`, `dukaan`...) and phrases (`coffee shop`, `ice cream`, `gift box`) map to props, and
**business concepts** bring a small composition: `translation` (globe + documents + chat), `assignment` (documents + pencil + book),
`software` (monitor + laptop), `marketing` (chart + laptop), `wellness` (lotus + candles + plant), `wedding`, `party`, `travel`,
`legal`, `education`, `healthcare`, `office`, and trades and services: `plumber`, `carpenter`, `electrician`, `painter`, `construction`, `mechanic`/`garage`, `repair`/`workshop`, `tailor`, `salon`/`barber`, `cleaning`, `pets`/`vet`, `farm`, `zoo`/`safari`, `playground`/`park`, `sports`, `energy`/`solar`, `emergency`/`fire`/`safety`, `dental`, `pharmacy`, `healthcare`, `skiing`, `skating`, `winter sports` (snow and ice ground are added automatically). Colours bind to the next noun (`red car`, `blue sofa`).

**Where things are drawn:** props go into a **scene** (a desk, a cafe table, a room, a studio, a party, a garden arch, depending on
what you asked for) or, when the prompt has outdoor words, buildings, vehicles or a time of day, into the **landscape**
(`car driving on a road at sunset`, `dairy farm with cows`, `construction site with a crane`, `ice skating rink`). When a scene is crowded the layout drops the extra props of a concept first (`secondary`), puts small things such as tools in a foreground row of their own and keeps everything inside the picture. Tools go on a workbench (workshop scene), pets on a floor. Saying `interior`, `inside`, `table` or `desk` draws a venue from the inside
(`restaurant dining table` -> plates, glass, candle on a table).

**Older renderers:** sun, moon, stars, clouds, rainbow, mountains, hills, trees, palm trees, islands, forest, house, city, sea,
beach, desert, flowers, birds, boat, road, planet, galaxy; day/sunset/dawn/night, snow, rain, fog, cyberpunk, space; shapes
(circle, square, triangle, star, heart, ring, polygons); mandala, geometric patterns, abstract art (palette from any colour words,
e.g. `blue abstract background`).

Words outside the lexicon are ignored (`--explain` lists them) unless a trained model knows them.

### Readable text
Put text in quotes and it is written into the picture with built-in stroke fonts (no font files):
Latin capitals and digits (`. , ! ? - & % + : / ( ) $` and the rupee sign), **Hindi/Devanagari** (consonants, vowels, matras, half forms, conjuncts,
reph, digits) and **103 common Chinese characters**. Lowercase Latin is drawn as capitals; unsupported characters (Arabic, Thai, rare Chinese) are
dropped and the CLI/API says so.

```bash
python3 -m pixelmath 'coffee shop sign "BEAN & BREW"' -o shop.png        # on the shop sign (also hotel signs and sale tags)
python3 -m pixelmath 'tea shop sign "चाय की दुकान"' -o chai.png           # Hindi on the sign
python3 -m pixelmath 'blue circle logo "ACME" on white background' -o logo.png
python3 -m pixelmath 'poster "SUMMER SALE" "UP TO 50% OFF" red background' -o poster.png   # headline + subtitle
python3 -m pixelmath 'coffee shop "咖啡 COFFEE"' -o cafe.png
```
The first quoted text goes on a sign/tag if the scene has one, otherwise it becomes the headline (dark or light automatically, with a soft
plate on busy backgrounds); a logo shape carries its text in the middle. Up to 3 texts, 40 characters each.

**Honest limits of the non-Latin fonts.** They are hand-drawn stroke fonts, always checked by eye, not a typographer's work:
* Devanagari reads correctly for ordinary Hindi words (all consonants, matras, half forms, a set of common conjuncts such as ज्ञ, क्ष,
  द्य, ह्म, ष्ट, reph and rakar), but it is a **single-stroke skeleton font, not a typographic font**: every letter is drawn with one
  pen weight, so fine details of the original design (stroke contrast, small lobes and terminals) are lost, and the rarer conjuncts and
  combinations of several signs are approximations that were not all inspected. The glyph skeletons were derived (centre-line
  extraction plus manual clean-up) from Noto Sans Devanagari Regular, (c) The Noto Project Authors, SIL Open Font License 1.1. No font
  file or outline data is shipped; the licence text is in `LICENSES/OFL-NotoSansDevanagari.txt` and the derivation is described in the
  PROVENANCE note of `pixelmath/devanagari.py` (dev tool: `tools/ttf_outlines.py`, see `tools/README.md`). Keep that notice if you
  redistribute the module.
* Chinese covers 103 simple/common characters. Phrases such as 咖啡, 茶, 酒, 面, 饭菜, 美食, 公司, 医院, 学校, 开业大吉 work; **欢迎光临 (光, 临
  missing) and 特价 (价 withheld) do not**: missing characters are dropped, and ones that looked wrong (他 年 车 长 新 折 价 我 肉 光 药 热 福 冷 你 家 在)
  are deliberately withheld.
* Whenever such text is drawn the CLI prints a note and the API returns `warnings` (JSON) or an `X-PixelMath-Warning` header: proof-read it.

### Adding your own prop (about 20 lines)
Create a function in `pixelmath/props/*.py` that draws in unit space (`c.rect/circle/ellipse/poly/path/arc/ring`, origin at the base,
height 1) and register it with `@prop("name", aspect=..., place="ground|table|sky", nominal=..., words=(...))`. Then
`python3 examples/props_gallery.py gallery.png --names name` to look at it, and the tests check that it stays inside its declared
box, takes colours, is reachable by a word and does not clash with existing words.

### Learned style for prop scenes
With a trained model (`--model`), prop scenes borrow the **backdrop colours** the model associates with your prompt words
(mode `scene+style`; `learned: blend` forces it, `off` disables it). Objects stay sharp because they are drawn by the painters; only
the palette comes from your images. See `business_check/own_images_blend_demo.png` (rows: your photos, model-only image, props without
model, props with the model's palette).

## History: issues found in the original reference code

1. The prompt changed one number only, so output was noise unrelated to the text.
2. `math.tan()` exploded (values > 1000) and saturated the blue channel.
3. Its BMP header was 50 bytes but declared a pixel offset of 54 (corrupt file).
4. BMP rows need 4-byte padding and BGR order; both were missing.
5. "Pure NumPy" contradicted "zero dependencies"; this version uses no NumPy.

`zlib` is Python's standard-library DEFLATE compressor, which the PNG format itself requires.
