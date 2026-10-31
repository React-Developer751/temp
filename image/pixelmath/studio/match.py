"""Prompt -> niche, mood, accent. Keyword scoring (English, Hinglish, Devanagari), with an honest "I do not know" answer."""
import re
import unicodedata

from ..tokenizer import COLORS
from .niches import NICHES, load_all

STRONG, WEAK, AVOID = 3.0, 1.0, 4.0
MIN_STRONG, MIN_MARGIN = 3.0, 1.0
RIVAL_LEAD = 6.0                  # with two niches both hitting strong words, the winner needs this much more evidence
MOOD_WORDS = {
    "dark": ("dark", "dramatic", "moody", "night", "neon", "low light", "black", "andhera", "रात", "अंधेरा", "cinematic"),
    "light": ("bright", "airy", "white", "minimal", "sunny", "clean", "pastel", "light and airy", "roshan", "उजला"),
    "cool": ("calm", "cool", "serene", "icy", "peaceful", "relaxing", "ठंडा", "shant", "शांत"),
    "warm": ("warm", "cozy", "cosy", "golden", "rustic", "sunset", "homely", "garam", "गरम", "सुनहरा"),
}
_TOKEN = re.compile(r"[a-z0-9]+|[ऀ-ॿ]+")


def normalise(text):
    """Lowercase, NFC, and fold the Devanagari spellings people mix up (chandrabindu = anusvara, nukta dropped, chandra-e = e)."""
    t = unicodedata.normalize("NFC", text.lower())
    return t.replace("\u0901", "\u0902").replace("\u093c", "").replace("\u0945", "\u0947")


def stem(w):
    for suf in ("ing", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[:-len(suf)]
    return w


_DEVA_ENDINGS = "ेंोौाीिुूँं"


def deva_stem(w):
    """Strip Hindi inflection endings (खिलौने / खिलौनों -> खिलौन, दांत / दांतों -> दांत): at most two trailing vowel signs."""
    for plural in ("ियों", "ियाँ", "ियां", "ियाें"):                    # feminine plurals: कुर्तियों / कुर्तियाँ -> कुर्ती, साड़ियों -> साड़ी
        if len(w) > len(plural) + 1 and w.endswith(plural):
            w = w[:-len(plural)] + "ी"
            break
    for _ in range(2):
        if len(w) > 3 and w[-1] in _DEVA_ENDINGS:
            w = w[:-1]
    return w


def _is_deva(term):
    return any("\u0900" <= ch <= "\u097f" for ch in term)


def _has(term, text, tokens, stems):
    term = normalise(term)
    if " " in term:
        if _is_deva(term):
            return term in text
        return re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text) is not None
    if _is_deva(term):
        # Hindi inflects (दांत, दांतों; खिलौने, खिलौनों): compare word stems, whole words only, never fragments
        ts = deva_stem(term)
        return term in tokens or (len(ts) >= 3 and any(deva_stem(t) == ts or (t.startswith(term) and len(t) - len(term) <= 3) for t in tokens if _is_deva(t)))
    return term in tokens or stem(term) in stems


GENERIC_PURITY = 0.55         # a "strong" single word whose captions spread over many niches counts only as a weak hint


def score_niches(prompt, purity=None):
    """{niche_id: (score, strong_hits, weak_hits, avoided)} for every niche with any hit. `purity(term)` (optional) demotes generic words."""
    load_all()
    text = normalise(prompt)
    tokens = set(_TOKEN.findall(text))
    stems = {stem(t) for t in tokens}
    out = {}
    for nid, n in NICHES.items():
        strong = [t for t in n.strong if _has(t, text, tokens, stems)]
        weak = [t for t in n.weak if _has(t, text, tokens, stems)]
        if purity is not None:
            generic = [t for t in strong if " " not in t and purity(t) < GENERIC_PURITY and purity(stem(normalise(t))) < GENERIC_PURITY]
            strong = [t for t in strong if t not in generic]
            weak = weak + generic
        avoided = [t for t in n.avoid if _has(t, text, tokens, stems)]
        if not (strong or weak):
            continue
        # a longer phrase is better evidence than a single word
        s = sum(STRONG + 0.5 * (len(t.split()) - 1) for t in strong) + WEAK * len(weak) - AVOID * len(avoided)
        out[nid] = (s, strong, weak, avoided)
    return out


NB_TEMP = 1.0                                                 # >1 softens the (over-confident) naive Bayes log-odds


def _keyword_only(ranked, info):
    """The rules used when there is no classifier: a strong hit with a clear lead, or several weak hints."""
    if not ranked:
        return (None, dict(info, reason="no niche word recognised"))
    best, (s1, strong, weak, avoided) = ranked[0]
    s2 = ranked[1][1][0] if len(ranked) > 1 else 0.0
    rival_strong = len(ranked) > 1 and any(not any(t in w for w in strong) for t in ranked[1][1][1])      # a rival hit a strong word that is not just part of the winner's longer phrase
    if s1 >= MIN_STRONG and s1 - s2 >= MIN_MARGIN and not (rival_strong and s1 - s2 < RIVAL_LEAD):
        return (best, dict(info, reason="keywords: " + ", ".join(strong + weak)))
    if s1 >= 2.0 and s1 - s2 >= 1.5 and len(weak) >= 2:
        return (best, dict(info, reason="several hints: " + ", ".join(weak)))
    return (None, dict(info, reason="ambiguous or only weak hints"))


VETO_GAP = 3.0                    # keywords name a niche but the classifier prefers another by more than this (log-odds, tempered): not trusted
NB_ONLY_PROB, NB_ONLY_MARGIN = 0.95, 0.5     # chosen by a grid over three blind prompt sets: 0.99 refused ~1 in 10 good prompts, 0.90 let more off-niche ones through
NB_AGREE_PROB = 0.60               # lower bar when some keyword (even a weak hint) points at the same niche as the classifier


def match_niche(prompt, classifier=None):
    """-> (niche_id or None, info).

    Without a classifier: keyword rules only (a strong hit with a clear lead, or several weak hints).
    With one (callable prompt -> (log-probabilities, known words), see classifier.py), the sentence as a whole is checked:
      * the keyword answer stands unless the classifier gives that niche almost no chance (veto -> fallback);
      * with no keyword answer, the classifier alone may answer only when it is very sure and clearly ahead;
      * "none" ahead, or an unclear race, means fallback. Never a guess.
    """
    from .classifier import posterior
    purity = getattr(classifier, "purity", None)
    scores = score_niches(prompt, purity)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1][0])
    info = {"candidates": [(k, round(v[0], 2)) for k, v in ranked[:3]]}
    kw_id, kw_info = _keyword_only(ranked, info)
    nb = classifier(prompt) if classifier else None
    if not nb or nb[1] < 2:
        return kw_id, kw_info
    logp, known = nb
    tempered = {k: v / NB_TEMP for k, v in logp.items()}
    post = posterior(tempered)
    probs = {k: p for p, k in post}
    (p1, top), margin = post[0], post[0][0] - post[1][0]
    info["classifier"] = (top, round(p1, 3), known)
    if kw_id:
        if top != kw_id and kw_id in tempered and max(tempered.values()) - tempered[kw_id] > VETO_GAP:
            if top != "none" and margin >= NB_ONLY_MARGIN and p1 >= NB_ONLY_PROB and top in scores and scores[top][0] > 0 and not scores[top][3]:
                return (top, dict(info, reason="classifier (%.2f) overrules keywords %s: a keyword hint also points at %s" % (p1, kw_id, top), learned=True))
            return (None, dict(info, reason="keywords say %s but the classifier prefers %s" % (kw_id, top)))
        return (kw_id, dict(kw_info, classifier=info["classifier"]))
    if top == "none":
        return (None, dict(info, reason="classifier: not one of the niches"))
    if top in scores and scores[top][3]:                       # the prompt contains a word that means "not this niche": the classifier alone may not bring it back
        return (None, dict(info, reason="classifier prefers %s but the prompt contains %s" % (top, ", ".join(scores[top][3]))))
    support = top in scores and scores[top][0] > 0 and (scores[top][1] or scores[top][2])
    if margin >= NB_ONLY_MARGIN and (p1 >= NB_ONLY_PROB or (support and p1 >= NB_AGREE_PROB)):
        return (top, dict(info, reason="trained classifier (%.2f)%s" % (p1, " + keyword hint" if support else ""), learned=True))
    return (None, dict(info, reason=kw_info["reason"] if not ranked else "unclear: best guess %s at %.2f" % (top, p1)))


def infer_look(prompt):
    """Mood and accent colour named in the prompt: ("dark", (r, g, b)) etc., None where the prompt says nothing."""
    text = normalise(prompt)
    tokens = _TOKEN.findall(text)
    mood = None
    for m, words in MOOD_WORDS.items():
        if any((w in text) if (" " in w or any("ऀ" <= ch <= "ॿ" for ch in w)) else (w in tokens) for w in words):
            mood = m if mood is None else mood
    accent = None
    for i, t in enumerate(tokens):
        if t in COLORS and t not in ("white", "black", "gray", "grey", "silver", "beige"):
            accent = COLORS[t]
            if i + 1 < len(tokens) and tokens[i + 1] == "light" and mood is None:
                mood = "dark"                                       # "gym in red light": coloured light on a dark room
            break
    return mood, accent
