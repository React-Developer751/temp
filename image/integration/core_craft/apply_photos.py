"""Apply the photo integration to a Core-Craft working copy: python3 apply_photos.py <path-to-core-craft>"""
import os
import sys

root = sys.argv[1]


def edit(rel, fn):
    path = os.path.join(root, rel)
    s = open(path, encoding="utf-8").read()
    t = fn(s)
    if t == s:
        raise SystemExit("no change made to " + rel)
    open(path, "w", encoding="utf-8").write(t)


def rep(s, old, new, count=1):
    if old not in s:
        raise SystemExit("anchor not found: " + old[:70])
    return s.replace(old, new, count)


def design(s):
    s = rep(s, 'JSX_TEMPLATE = Template(', '''HERO_PHOTO = """<section className="hero hero-photo" style={{ "--hero-fg": DATA.photos.hero.text_color }}>
        <img className="hero-img" src={DATA.photos.hero.src} alt={DATA.photos.hero.alt} width={DATA.photos.hero.width} height={DATA.photos.hero.height} fetchpriority="high" />
        <div className="hero-text">
          <p className="eyebrow">{DATA.eyebrow}</p>
          <h1>{DATA.hero_heading}</h1>
          <p className="lead">{DATA.tagline}</p>
          <div className="btn-row">
            <a className="btn btn-primary" href="#contact">{DATA.cta_primary}</a>
            <a className="btn btn-ghost" href="#features">{DATA.cta_secondary}</a>
          </div>
        </div>
      </section>"""

JSX_TEMPLATE = Template(''')
    s = rep(s, '''function About() {
  return (
    <section id="about" className="section about">
      <h2>{DATA.about_title}</h2>
      {DATA.about.map((p, i) => (
        <p key={i}>{p}</p>
      ))}''', '''function About() {
  return (
    <section id="about" className={"section about" + (DATA.photos ? " about-photo-layout" : "")}>
      {DATA.photos && (
        <figure className="about-photo">
          <img src={DATA.photos.about.src} alt={DATA.photos.about.alt} width={DATA.photos.about.width} height={DATA.photos.about.height} loading="lazy" decoding="async" />
        </figure>
      )}
      <div className="about-text">
      <h2>{DATA.about_title}</h2>
      {DATA.about.map((p, i) => (
        <p key={i}>{p}</p>
      ))}''')
    s = rep(s, '''          ))}
        </ul>
      )}
    </section>
  );
}

function Highlights() {''', '''          ))}
        </ul>
      )}
      </div>
    </section>
  );
}

function Gallery() {
  if (!DATA.photos || DATA.photos.tiles.length === 0) return null;
  return (
    <section id="gallery" className="section gallery">
      <h2>{DATA.ui.gallery}</h2>
      <div className="gallery-grid">
        {DATA.photos.tiles.map((t) => (
          <figure key={t.src}>
            <img src={t.src} alt={t.alt} width={t.width} height={t.height} loading="lazy" decoding="async" />
          </figure>
        ))}
      </div>
    </section>
  );
}

function Highlights() {''')
    s = rep(s, "        <Features />\n        <Pricing />", "        <Features />\n        <Gallery />\n        <Pricing />")
    s = rep(s, '.eyebrow { text-transform: uppercase;', '''.hero-photo { position: relative; padding: 0; min-height: 360px; aspect-ratio: 2 / 1; max-height: 86vh; overflow: hidden; display: flex; align-items: center; }
.hero-photo .hero-img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.hero-photo .hero-text { position: relative; width: 44%; margin-left: 5%; color: var(--hero-fg); }
.hero-photo .eyebrow, .hero-photo .lead { color: var(--hero-fg); opacity: .92; }
.hero-photo .btn-ghost { color: var(--hero-fg); border-color: var(--hero-fg); }
.hero-photo h1 { font-size: clamp(1.8rem, 3.6vw, 3.2rem); }
.about-photo-layout { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr); gap: 40px; align-items: center; }
.about-photo img, .gallery-grid img { width: 100%; height: auto; display: block; border-radius: var(--radius); }
.about-photo { margin: 0; }
.gallery-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; }
.gallery-grid img { aspect-ratio: 4 / 3; object-fit: cover; }
.gallery-grid figure { margin: 0; }
.eyebrow { text-transform: uppercase;''')
    s = rep(s, "@media (max-width: 800px) { .hero-split { grid-template-columns: 1fr; } nav { display: none; } }",
            "@media (max-width: 800px) { .hero-split { grid-template-columns: 1fr; } nav { display: none; } .hero-photo { display: block; aspect-ratio: auto; max-height: none; min-height: 0; }"
            " .hero-photo .hero-img { position: static; height: auto; } .hero-photo .hero-text { width: auto; margin: 0; padding: 28px 6vw; color: var(--text); }"
            " .hero-photo .eyebrow, .hero-photo .lead { color: var(--muted); opacity: 1; } .hero-photo .btn-ghost { color: var(--text); border-color: var(--primary); }"
            " .about-photo-layout { grid-template-columns: 1fr; } }")
    s = rep(s, '''def build_jsx(content, assets, rng):
    hero = rng.choice([HERO_SPLIT, HERO_CENTER])
    layout = rng.choice(["cards", "list"])
    data = dict(content)
    data.update({"hero": assets["hero"], "logo": assets["logo"], "icons": assets["icons"]})
    jsx = JSX_TEMPLATE.substitute(data=js_json(data), hero=hero, feature_layout=layout)
    return jsx, {"hero": "split" if hero is HERO_SPLIT else "center", "features": layout}''', '''def build_jsx(content, assets, rng, photos=None):
    hero = rng.choice([HERO_SPLIT, HERO_CENTER])
    layout = rng.choice(["cards", "list"])
    data = dict(content)
    data.update({"hero": assets["hero"], "logo": assets["logo"], "icons": assets["icons"]})
    if photos:
        hero = HERO_PHOTO
        data["photos"] = photos["images"]
    jsx = JSX_TEMPLATE.substitute(data=js_json(data), hero=hero, feature_layout=layout)
    return jsx, {"hero": "photo" if photos else ("split" if hero is HERO_SPLIT else "center"), "features": layout}''')
    s = rep(s, "def build_preview_body(content, assets, layout):", "def build_preview_body(content, assets, layout, photos=None):")
    s = rep(s, '''    hero = '<section class="hero hero-%s">%s</section>' % (layout["hero"], text + art if layout["hero"] == "split" else art + text)''',
            '''    hero = '<section class="hero hero-%s">%s</section>' % (layout["hero"], text + art if layout["hero"] == "split" else art + text)
    about_photo = gallery = ""
    if photos:
        ph = photos["images"]
        img = lambda i, lazy: '<img src="%s" alt="%s" width="%d" height="%d"%s>' % (e(i["src"], quote=True), e(i["alt"], quote=True), i["width"], i["height"],
                                                                                   ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"')
        hero = ('<section class="hero hero-photo" style="--hero-fg:%s">%s%s</section>' % (e(ph["hero"]["text_color"] or "#ffffff", quote=True), img(ph["hero"], False).replace("<img ", '<img class="hero-img" ', 1), text))
        about_photo = '<figure class="about-photo">%s</figure>' % img(ph["about"], True)
        if ph["tiles"]:
            gallery = ('<section id="gallery" class="section gallery"><h2>%s</h2><div class="gallery-grid">%s</div></section>\\n'
                       % (e(ui["gallery"]), "".join("<figure>%s</figure>" % img(t, True) for t in ph["tiles"])))''')
    s = rep(s, '''<section id="about" class="section about"><h2>%s</h2>%s%s</section>\\n'
        '<section id="features" class="section features %s"><h2>%s</h2><div class="grid">%s</div></section>\\n%s\\n%s\\n%s\\n%s\\n%s\\n%s\\n\'''',
            '''<section id="about" class="section about%s">%s<div class="about-text"><h2>%s</h2>%s%s</div></section>\\n'
        '<section id="features" class="section features %s"><h2>%s</h2><div class="grid">%s</div></section>\\n%s%s\\n%s\\n%s\\n%s\\n%s\\n%s\\n\'''')
    s = rep(s, '''hero, highlights, e(content["about_title"]), about, stats_html,
           layout["features"], e(content["features_title"]), feats, pricing, steps,''',
            '''hero, highlights, " about-photo-layout" if photos else "", about_photo, e(content["about_title"]), about, stats_html,
           layout["features"], e(content["features_title"]), feats, gallery, pricing, steps,''')
    s = rep(s, "def generate_site(content, assets, out_dir, seed=None):", "def generate_site(content, assets, out_dir, seed=None, photos=None):")
    s = rep(s, "    jsx, layout = build_jsx(content, assets, rng)\n", "    jsx, layout = build_jsx(content, assets, rng, photos)\n")
    s = rep(s, "build_preview_body(content, assets, layout), **meta)", "build_preview_body(content, assets, layout, photos), **meta)")
    return s


edit("corecraft/design_engine.py", design)
edit("corecraft/content_engine.py", lambda s: rep(s, '"lang": "en", "about": "About", "faq": "FAQ",', '"lang": "en", "about": "About", "gallery": "Gallery", "faq": "FAQ",'))
edit("corecraft/lang_hi.py", lambda s: rep(s, '"lang": "hi", "about": "हमारे बारे में", "faq"', '"lang": "hi", "about": "हमारे बारे में", "gallery": "गैलरी", "faq"'))


def pipeline(s):
    s = rep(s, "from . import asset_engine, content_engine, design_engine", "from . import asset_engine, content_engine, design_engine, photo_engine")
    s = rep(s, 'def run(prompt, out_root="output", seed=None, facts=None, lang=None):', 'def run(prompt, out_root="output", seed=None, facts=None, lang=None, photos=True, photo_count=6):')
    s = rep(s, '''    out_dir = Path(out_root) / slugify(content["brand"])
    result = design_engine.generate_site(content, assets, out_dir, seed)''', '''    out_dir = Path(out_root) / slugify(content["brand"])
    pics = photo_engine.generate_photos(content, assets, out_dir, seed, photo_count) if photos else None
    if pics is not None and pics["fallback"]:
        content["needs_review"] = list(content.get("needs_review", [])) + [
            "No picture style fits this kind of business (%s): the pictures are a neutral abstract in the brand colour, not a wrong scene." % pics["reason"]]
    result = design_engine.generate_site(content, assets, out_dir, seed, pics)''')
    s = rep(s, '''    result.update({"brand": content["brand"],''', '''    result.update({"photos": None if pics is None else {k: pics[k] for k in ("niche", "fallback", "reason", "mood", "report")},
                   "brand": content["brand"],''')
    return s


edit("corecraft/pipeline.py", pipeline)


def main(s):
    s = rep(s, '    ap.add_argument("--name"), ap.add_argument("--city")', '''    ap.add_argument("--no-photos", action="store_true", help="keep the built-in SVG artwork instead of pictures from the image engine")
    ap.add_argument("--photo-count", type=int, default=6, help="pictures per site: hero, about and the rest as gallery (3 to 8, default 6)")
    ap.add_argument("--name"), ap.add_argument("--city")''')
    s = rep(s, "r = pipeline.run(prompt, a.out, a.seed, facts or None, a.lang)", "r = pipeline.run(prompt, a.out, a.seed, facts or None, a.lang, photos=not a.no_photos, photo_count=a.photo_count)")
    return s


edit("main.py", main)
print("applied")
