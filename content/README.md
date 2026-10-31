# Core-Craft AI

One short description of a business (English, Hinglish or Hindi) in, a React static website out.
Pure Python standard library: no dependencies, no external AI, no API, no internet at run time.

## Install

```bash
pip install corecraft-ai        # Python 3.9+, no dependencies
corecraft "dental clinic in Pune, braces, implants" --out sites --seed 1
corecraft --pack "Create a website for a plumber in Jaipur"
```

```python
from corecraft.content_engine import generate_content
page = generate_content("bakery in Jaipur, cakes, cookies", seed=1)   # the page text as a dict (what content.json holds)
```

The `corecraft` command and `python3 main.py` (repo checkout) are the same CLI. With no prompt it asks for one; when stdin is not a terminal
(a script or a pipe) it exits with an error instead of waiting.

## Use (repo checkout)

```bash
python3 main.py "Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu, open 12pm to 11pm, online booking"
python3 main.py "mujhe ek dental clinic chahiye Pune mein, braces, implants" --out sites --seed 1
python3 main.py "bakery in Delhi" --facts my_facts.json
```

Output (in `output/<brand>/`): `preview.html` (open directly), `App.jsx` + `index.html` + `styles.css` (React; `index.html` loads React from a CDN in the browser),
`content.json`, `palette.json`, generated images/assets.

`--facts` is a JSON object: `name, city, services[], phone, email, address, hours[], prices[{name,price}], testimonials[{name,text}], team[{name,role}], whatsapp, years, tagline`.
Anything in it wins over what is read from the prompt. As a library: `from corecraft.content_engine import generate_content`.

## Web UI (check and train, repo checkout only)

```bash
python3 webui.py        # then open http://127.0.0.1:8765  (this computer only)
```

`webui.py` and `training/` are not in the pip package. The UI listens on 127.0.0.1 only and refuses requests that do not come from it,
so another web page open in the same browser cannot read it or retrain the model:
- `Host` must be `127.0.0.1:<port>`, `localhost:<port>` or `[::1]:<port>` (403 otherwise: stops DNS rebinding).
- A POST/PUT/DELETE with an `Origin` other than the UI's own, or with `Sec-Fetch-Site: cross-site`, gets 403 (CSRF).
- POST bodies must be `Content-Type: application/json` (415 otherwise; a cross-site form or `text/plain` post cannot be JSON),
  with a plain non-negative `Content-Length` (400 otherwise) of at most 200 kB (413).
- The generated preview is served with `Content-Security-Policy: sandbox allow-scripts` inside a sandboxed iframe, so a page's own
  script cannot call the API; the UI cannot be framed by other sites (`X-Frame-Options: SAMEORIGIN`).

- **Generate & check**: type a prompt (optionally real details), see the page preview and a report: type + confidence, city, hours, services read, offers, what is missing, review notes.
- **Wrong type?** Pick the right one and save it as a training example (`data/feedback.json`).
- Retraining writes the detector to `corecraft/data/detector.json`, the file the engine reads.
- **Train** tab: retrains the detector on the shipped labels plus your corrections (about 15 s, offline). The new model is kept only if its score on the held-out prompts does not drop; otherwise the old one is restored.

Training teaches business-type detection only. Wording comes from the hand-written frames in `corecraft/voice_*.py`.

## Niche content packs

A pack is the whole text of one kind of business in the JSON shape of the owner's spec document ("Content AI: training prompts"): hero titles, 6 features, steps, FAQ,
pricing, gallery, team, testimonials, blog, marquee, and a menu for food. It is written from a plain request.

```bash
python3 main.py --pack "Create a website for a pest control in Jaipur"           # prints the pack (JSON)
python3 main.py --pack "mujhe termite treatment ki website banakar do" --out packs/pest.json
python3 main.py --pack-site "Create a website for a bakery called Sweet Crumbs in Pune" --out sites   # pack -> website
python3 training/import_niches.py data/niche_spec_source.txt   # spec document text -> corecraft/data/niche_spec.json
python3 training/build_niches.py            # rebuilds corecraft/data/niches.json (99 + 20) and author_niches.json (77 + 16)
python3 training/export_packs.py            # output/niche_packs/batch-1..10.json + type-packs.json, checked (--author: the 77-type list)
python3 training/eval_requests.py [--fresh] # request understanding on the spec's 594 requests (--author: the same against the 77-type list)
python3 webui.py                            # "Content pack" tab
```

- **Default list: 99 niches + 20 business types** from the owner's own spec document, in `corecraft/data/niches.json` (ships in the package). Each niche has its label,
  six services, keywords (English, Hinglish, Devanagari) and the six ways of asking from the spec; `corecraft/pack_spec.py` adds the hand-written layer (text bank, sample
  prices, button, team, menu for food). `training/build_niches.py` writes the file from `corecraft/data/niche_spec.json` + `pack_spec.py`; rerun it after changing either.
- **The author's 77 business types** (`corecraft/business_types.py`) are in `corecraft/data/author_niches.json` (also in the package). Nine of them have no spec niche
  (optical shop, eye hospital, tyre shop, welding, graphic design, business consulting, gaming cafe, pottery and robotics classes): a request for one of these trades gets
  that type's pack, with a note. The spec's own requests never reach this fallback (tested). `CORECRAFT_NICHE_FILE=author` (or `pack_writer.use_niche_file("author")`)
  uses the whole 77-type list instead of the spec list; `CORECRAFT_NICHE_FILE=/path/file.json` uses any file in the same format.
- `corecraft/pack_request.py` reads the request (English, Hinglish, Hindi, typos) and finds the niche; `pack_writer.py` writes the pack from the niche's six services plus hand-written
  text banks (`pack_families_*.py`); `pack_check.py` is the spec's rules as code (counts, lengths, Title Case, no emoji or "!", no invented numbers, awards or ratings, no repeated text, USD prices).
- "Create a modern website for <one of the 20 business types>" gets that type's general pack. A trade neither list covers (say, "taxidermy studio") gets the general
  local business pack and a note naming the word it did not know; a request with no trade at all gets the same pack with a "does not name a trade" note.
- Request understanding: 594/594 of the spec's requests; 93.9% when the words of each request are removed from its niche first (hold-out); 51/52 fresh hand-written requests.
- Prices in a pack are sample figures (USD, the generator converts them); testimonials are generic samples. A named business replaces `{brand}`; a named city goes once into the hero subtitles.
- A pack is checked before it is returned (`PackError` if it ever fails: that would be a bug, never bad input). Names and cities from a request are cleaned (no markup, braces, links);
  a city too long for the subtitle rules moves to the contact text. `--pack-site` uses the image engine when it is installed and falls back to the built-in artwork when it is not.
- Not built: Hindi (Devanagari) packs. A Hindi request is understood, but the pack comes back in English with a note.

## What it promises

- Uses only facts you gave (name, city, services, offers, hours, prices, phone, address). Nothing is invented; what is missing is listed in `missing`.
- Every page passes validators: no placeholders, no repeated 6-word span, no other niche's words, every named service present.
- Same prompt + same seed gives the same page. Input is cleaned (markup, braces, newlines, very long text) and bad `--facts` files give a clear error.
- `needs_review` tells you when to check: invented brand name, unsure business type, typical offerings used, no city.
- No business name given: the heading says what the business is and where ("Dental Clinic, Pune"). Nothing is made up; `needs_review` says to add your name (and suggests one from a business email domain, never uses it).
- Typos: words that name the kind of business ("resturant", "salun", "gim") are corrected everywhere; inside the detected trade a one-letter slip in an unknown word ("makup", "cardeo") is corrected too. Real names and dishes are left alone, and every change is listed in `needs_review`.
- Services typed with no commas ("dog food cat food aquarium fish toys") are cut with known phrases and word shape. On 16 fresh prompts I did not tune on, 66% of services came out right (3% without it), and the page always notes how the run was cut so you can add commas.
- Whole sentences work too ("We are a bakery in Jaipur. We make cakes and cookies. You can order on WhatsApp.").

## Limits (read these)

- 77 business types, 23 sub-niches (cuisines, dental/skin/eye, yoga/gym ...). An unlisted type gets neutral copy and a `needs_review` note.
- Copy comes from hand-written frames filled with your words. It reads well, but it is not a human copywriter: give 3+ real services for the best page.
- Business-type detection scored 97% on the author's own hold-out set; it has not been measured on outside traffic. Low confidence is flagged, not hidden.
- Hindi pages use Hindi frames only; Hinglish is read, and written as English.
- No prices, reviews or team are shown unless you supply them.

## Checks

```bash
python3 -m unittest discover -p "test_*.py"   # 100+ tests
python3 training/evaluate.py                  # accuracy / quality numbers
python3 training/check_copy.py                # no 6-word span copied from training pages
```

Typo vocabulary: `python3 training/build_vocab.py` rebuilds `corecraft/data/vocab.json`.

Retraining (optional, needs internet only for `fetch_*`): `training/train.py`, `training/train_templates.py`. Training data lives in `data/`;
the files the engine reads at run time live in `corecraft/data/`.

Pictures: when the PixelMath image engine is installed (`import pixelmath` works) pages get real pictures; in a repo checkout it is also
found at `../image/pixelmath` next to this folder (loaded by path, never when running from site-packages). Otherwise pages keep the built-in SVG artwork.

## Data and licensing

Code: MIT (see `LICENSE`). The pip package ships only the runtime word lists and detector (`corecraft/data/`: `detector.json`, `vocab.json`,
`fillers.json`, `profile_vocab.json`) and the two niche lists (`niches.json`: the 99 niches + 20 types of the owner's spec document; `author_niches.json`: the author's 77 types). Scraped training text (`data/corpus*.json`, `data/profile_*.json`,
the n-gram `data/model.json`), fetch logs, your corrections (`data/feedback.json`), `training/`, `webui.py`, the tests and `output/` stay in
the repo and are not in the package. Example names and phone numbers in the tests are invented (555-01xx numbers).

## Build (maintainers)

```bash
python3 -m build            # dist/corecraft_ai-1.0.0-py3-none-any.whl and .tar.gz
```
