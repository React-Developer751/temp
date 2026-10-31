"""Quality gates for a generated page. Each check returns a list of problems; an empty list means the page may be shown.

- placeholders   : Sample, Lorem, example.com, 555, John/Jane, 123, "Your main dishes", "Starter or soup" ... unless the prompt contains them
- repeats        : no 6-word span (and no whole sentence) may appear twice on a page
- wrong niche    : dishes of another cuisine, or words from another kind of business, unless the person wrote them
- help frames    : "we help people with ..." only on service kinds (professional, home, community)
- filler voice   : "passionate", "world-class", "welcome to our website" ...
- named services : every service the person named appears on the page
"""
import re

from .profiles import FOREIGN, PROFILES, SERVICE_KINDS
from .voice_data import VOICE

PLACEHOLDERS = [
    r"\bsample\b", r"\blorem\b", r"\bipsum\b", r"example\.(?:com|org|net)", r"\b555\b", r"\(555\)", r"\bjohn\b", r"\bjane\b", r"\bjohn\s+snow\b", r"\b123\b",
    r"your main dishes", r"starter or soup", r"your name here", r"\binsert\b.{0,20}\bhere\b", r"\btbd\b", r"\bplaceholder\b", r"\bxxx+\b", r"\bfoo\b", r"\bbar baz\b",
    r"lunch thali", r"home style curry", r"results that speak for themselves", r"\bacme\b", r"\bdoe\b",
]
FILLER_VOICE = [r"\bpassionate\b", r"world-class", r"welcome to our website", r"state-of-the-art", r"cutting-edge", r"best-in-class", r"second to none",
                r"top-notch", r"one-stop", r"we are committed to", r"customer satisfaction is our", r"your trusted partner"]
HELP_FRAMES = [r"\bhelp(?:s)? (?:people|you|clients|customers) with\b", r"whatever you need from", r"\bhelp(?:s)? with (?:everything|all)\b"]

KIND_FOREIGN = {
    "food": "patients patient treatment treatments therapy diagnosis clinic appointment appointments prescription workout workouts curriculum enrol enroll invoice invoices cart checkout",
    "health": "menu dish dishes cuisine chef kitchen recipe recipes pizza pasta thali curry table tables workout workouts cart checkout",
    "beauty": "patients patient dish dishes menu workout workouts cart checkout diagnosis",
    "fitness": "patients patient dish dishes menu appointment appointments diagnosis cart checkout",
    "retail": "patients patient treatment diagnosis workout workouts dish dishes menu",
    "software": "patients patient dish dishes menu workout workouts diagnosis appointment appointments",
    "education": "patients patient dish dishes menu workout workouts diagnosis cart checkout",
    "home": "patients patient dish dishes menu workout workouts diagnosis",
    "trades": "patients patient dish dishes menu workout workouts diagnosis cuisine",
    "travel": "patients patient dish dishes workout workouts diagnosis",
    "events": "patients patient workout workouts diagnosis",
    "creative": "patients patient dish dishes menu workout workouts diagnosis",
    "pro": "patients patient dish dishes menu workout workouts cuisine",
    "org": "patients dish dishes menu workout workouts",
}


def words(s):
    return re.findall(r"[a-zऀ-ॿ0-9]+", s.lower())   # apostrophes split words ("you'd" -> you, d) so a contraction cannot hide a repeat


def _forms(w):
    out = {w}
    if w.endswith("s") and len(w) > 3:
        out.add(w[:-1])
    else:
        out.add(w + "s")
    return out


def leaves_of(content):
    """(path, text, from_user) for every sentence-bearing field of a page."""
    out = []

    def add(path, text, user=False):
        if isinstance(text, str) and text.strip():
            out.append((path, text, user))
    for k in ("hero_heading", "tagline", "cta_title", "cta_text", "cta_primary", "cta_secondary", "features_title", "steps_title", "faq_title", "stats_title", "blog_title", "about_title"):
        add(k, content.get(k))
    for i, p in enumerate(content.get("about", [])):
        add("about.%d" % i, p)
    for i, f in enumerate(content.get("features", [])):
        add("features.%d.title" % i, f.get("title"), True)   # titles echo the person's own words
        add("features.%d.text" % i, f.get("text"))
    for i, f in enumerate(content.get("highlights", [])):
        add("highlights.%d.text" % i, f.get("text"))
        add("highlights.%d.title" % i, f.get("title"))
    for i, f in enumerate(content.get("steps", [])):
        add("steps.%d.text" % i, f.get("text"))
        add("steps.%d.title" % i, f.get("title"))
    for i, f in enumerate(content.get("faq", [])):
        add("faq.%d.q" % i, f.get("q"))
        add("faq.%d.a" % i, f.get("a"))
    for i, f in enumerate(content.get("blog", [])):
        add("blog.%d.title" % i, f.get("title"))
        add("blog.%d.excerpt" % i, f.get("excerpt"))
    return out


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_placeholders(leaves, allowed_text):
    allowed = allowed_text.lower()
    issues = []
    for path, text, _ in leaves:
        low = text.lower()
        for rx in PLACEHOLDERS + FILLER_VOICE:
            m = re.search(rx, low)
            if m and m.group(0) not in allowed:
                issues.append("placeholder/filler %r in %s" % (m.group(0), path))
    return issues


def check_repeats(leaves, n=6, allowed_text=""):
    """Spans the person typed (an opening-hours line, an address) may appear in several places: that is their text, not repetition."""
    own = " " + " ".join(words(allowed_text)) + " "
    seen, issues = {}, []
    for path, text, user in leaves:
        if user:
            continue
        ws = words(text)
        mine = set()
        for i in range(len(ws) - n + 1):
            sh = " ".join(ws[i:i + n])
            if " " + sh + " " in own:
                continue
            if sh in mine:
                issues.append("repeated %d-word span inside %s: %r" % (n, path, sh))
                break
            mine.add(sh)
        for sh in mine:
            if sh in seen and seen[sh] != path:
                issues.append("repeated %d-word span in %s and %s: %r" % (n, seen[sh], path, sh))
                break
        for sh in mine:
            seen.setdefault(sh, path)
    sent = {}
    for path, text, user in leaves:
        if user:
            continue
        for s in _sentences(text):
            key = " ".join(words(s))
            if len(key.split()) >= 4:
                if key in sent and sent[key] != path:
                    issues.append("sentence repeated in %s and %s: %r" % (sent[key], path, s))
                sent.setdefault(key, path)
    return issues


_VOICE_WORDS = {}


def voice_words(kind):
    """Every word the kind's own voice uses: those are never foreign on a page of that kind ("consultation" on a dental page)."""
    if kind not in _VOICE_WORDS:
        out = set()

        def walk(x):
            if isinstance(x, str):
                out.update(words(x))
            elif isinstance(x, (list, tuple)):
                for y in x:
                    walk(y)
            elif isinstance(x, dict):
                for y in x.values():
                    walk(y)
        walk(VOICE.get(kind, {}))
        _VOICE_WORDS[kind] = out
    return _VOICE_WORDS[kind]


def check_wrong_niche(leaves, kind, profile, allowed_text):
    allowed = set(words(allowed_text))
    bad = set(KIND_FOREIGN.get(kind, "").split())
    if profile in FOREIGN:
        bad |= FOREIGN[profile] - voice_words(kind)
    issues = []
    for path, text, user in leaves:
        if user:
            continue
        for w in words(text):
            if w in bad and not (_forms(w) & allowed):
                issues.append("word %r belongs to another niche (%s)" % (w, path))
    return issues


def check_help_frames(leaves, kind):
    if kind in SERVICE_KINDS:
        return []
    issues = []
    for path, text, user in leaves:
        if user:
            continue
        for rx in HELP_FRAMES:
            if re.search(rx, text.lower()):
                issues.append("service-style 'help' frame on a %s page (%s)" % (kind, path))
    return issues


def _norm(s):
    return re.sub(r"[^a-zऀ-ॿ0-9]+", " ", s.lower().replace("-", " ")).strip()


def check_services(leaves, items, limit=6):
    blob = " " + " ".join(_norm(t) for _, t, _ in leaves) + " "
    issues = []
    for it in items[:limit]:
        if " " + _norm(it) + " " not in blob:
            issues.append("named service %r is missing from the page" % it)
    return issues


def check_lengths(content):
    issues = []
    if len(content.get("hero_heading", "")) > 78:
        issues.append("hero heading is longer than 78 characters")
    if len(content.get("tagline", "")) > 220:
        issues.append("subtitle is longer than 220 characters")
    return issues


def validate_page(content, kind, profile, allowed_text, items, exempt=""):
    leaves = leaves_of(content)
    return (check_lengths(content) + check_placeholders(leaves, allowed_text) + check_repeats(leaves, allowed_text=exempt) + check_wrong_niche(leaves, kind, profile, allowed_text)
            + check_help_frames(leaves, kind) + check_services(leaves, items))
