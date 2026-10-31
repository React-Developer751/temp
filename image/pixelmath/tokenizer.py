"""Module 1 - Native linguistic tokenizer, parser and vectorizer.

Pure Python, no external model. Turns a prompt (English / Hinglish) into:
  * a structured ParsedPrompt (entities with colour / size / position / count,
    plus scene flags such as time of day, weather, style), and
  * a fixed-length numeric vector (hashed character n-grams) for Module 2.
"""
import math
import re
import unicodedata
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Lexicon
# --------------------------------------------------------------------------
_RGB = {
    "red": (220, 38, 38), "blue": (37, 99, 235), "green": (22, 163, 74),
    "yellow": (250, 204, 21), "orange": (249, 115, 22), "purple": (147, 51, 234),
    "pink": (236, 72, 153), "white": (248, 248, 248), "black": (14, 14, 18),
    "gray": (113, 113, 122), "brown": (120, 72, 40), "gold": (234, 179, 8),
    "silver": (192, 196, 204), "cyan": (6, 182, 212), "magenta": (217, 70, 239),
    "teal": (13, 148, 136), "navy": (30, 41, 100), "maroon": (127, 29, 29),
    "beige": (231, 216, 186), "lime": (132, 204, 22), "turquoise": (64, 224, 208),
    "violet": (139, 92, 246), "indigo": (79, 70, 229), "crimson": (185, 28, 60),
}
_COLOR_ALIASES = {
    "laal": "red", "lal": "red", "scarlet": "red", "ruby": "red",
    "neela": "blue", "nila": "blue", "azure": "blue",
    "hara": "green", "hari": "green", "emerald": "green",
    "peela": "yellow", "pila": "yellow", "narangi": "orange",
    "baingani": "purple", "jamuni": "purple", "gulabi": "pink",
    "safed": "white", "kaala": "black", "kala": "black", "kali": "black",
    "bhura": "brown", "grey": "gray", "golden": "gold", "sunehra": "gold",
    "chandi": "silver",
}
COLORS = {k: tuple(c / 255.0 for c in v) for k, v in _RGB.items()}
for _alias, _target in _COLOR_ALIASES.items():
    COLORS[_alias] = COLORS[_target]

SHAPES = {
    "circle": "circle", "round": "circle", "ball": "circle", "gola": "circle",
    "square": "square", "box": "square", "cube": "square",
    "rectangle": "rectangle", "rect": "rectangle",
    "triangle": "triangle", "star": "star", "heart": "heart", "dil": "heart",
    "ring": "ring", "donut": "ring", "diamond": "diamond", "rhombus": "diamond",
    "pentagon": "pentagon", "hexagon": "hexagon", "octagon": "octagon",
}

OBJECTS = {
    "sun": "sun", "suraj": "sun", "sunshine": "sun",
    "moon": "moon", "chand": "moon", "chaand": "moon",
    "stars": "stars", "starry": "stars", "taare": "stars", "sitare": "stars",
    "cloud": "cloud", "badal": "cloud", "baadal": "cloud",
    "mountain": "mountain", "pahad": "mountain", "pahar": "mountain",
    "hill": "hill",
    "tree": "tree", "ped": "tree", "palm": "palm", "coconut": "palm", "island": "island",
    "forest": "forest", "jungle": "forest", "woods": "forest",
    "house": "house", "home": "house", "ghar": "house", "hut": "house",
    "cottage": "house", "cabin": "house",
    "city": "city", "skyline": "city", "town": "city", "building": "city",
    "skyscraper": "city", "shehar": "city",
    "sea": "sea", "ocean": "sea", "samundar": "sea", "water": "sea",
    "lake": "sea", "river": "sea", "nadi": "sea", "waves": "sea",
    "beach": "beach", "desert": "desert", "registan": "desert",
    "grass": "grass", "field": "grass", "meadow": "grass", "khet": "grass",
    "garden": "grass", "lawn": "grass",
    "flower": "flower", "phool": "flower", "rose": "flower", "tulip": "flower",
    "bird": "bird", "panchi": "bird", "chidiya": "bird", "eagle": "bird",
    "rainbow": "rainbow", "indradhanush": "rainbow",
    "road": "road", "street": "road", "highway": "road", "sadak": "road",
    "planet": "planet", "saturn": "planet", "mars": "planet",
    "boat": "boat", "ship": "boat", "sailboat": "boat",
}
# nouns that name a scene region rather than a drawable thing
REGION_WORDS = {
    "background": "background", "backdrop": "background", "bg": "background",
    "sky": "sky", "aasman": "sky", "asman": "sky", "aakash": "sky",
    "ground": "ground", "floor": "ground", "land": "ground",
}
TIMES = {
    "night": "night", "raat": "night", "midnight": "night", "dark": "night",
    "sunset": "sunset", "dusk": "sunset", "evening": "sunset", "shaam": "sunset",
    "sunrise": "dawn", "dawn": "dawn", "morning": "dawn", "subah": "dawn",
    "day": "day", "daytime": "day", "noon": "day", "afternoon": "day",
    "sunny": "day",
}
FLAGS = {
    "cyberpunk": "cyberpunk", "neon": "cyberpunk", "futuristic": "cyberpunk",
    "synthwave": "cyberpunk", "scifi": "cyberpunk",
    "snow": "snow", "snowy": "snow", "winter": "snow", "baraf": "snow",
    "rain": "rain", "rainy": "rain", "barish": "rain", "baarish": "rain",
    "storm": "rain", "stormy": "rain",
    "fog": "fog", "foggy": "fog", "mist": "fog", "misty": "fog",
    "space": "space", "galaxy": "galaxy", "cosmos": "space",
    "universe": "space", "nebula": "space",
    "mandala": "mandala", "radial": "mandala",
    "pattern": "tiles", "geometric": "tiles", "grid": "tiles", "tile": "tiles",
    "tiles": "tiles", "bauhaus": "tiles",
    "abstract": "abstract", "art": "abstract",
    "pine": "conifer", "conifer": "conifer", "fir": "conifer",
    # generative maths pictures (generative.py)
    "fractal": "fractal", "fractals": "fractal", "mandelbrot": "mandelbrot", "julia": "julia",
    "lsystem": "lsystem", "koch": "koch", "snowflake": "koch", "fern": "fern", "dragon": "dragon",
    "sierpinski": "sierpinski", "flow": "flow", "flowfield": "flow", "swirl": "flow", "turbulence": "flow",
    "plasma": "texture", "perlin": "texture", "noise": "texture", "texture": "texture", "marble": "marble",
    # colour-theory palette rules (palette.py)
    "analogous": "scheme_analogous", "complementary": "scheme_complementary", "triadic": "scheme_triadic",
    "tetradic": "scheme_tetradic", "monochrome": "scheme_monochrome", "monochromatic": "scheme_monochrome",
    "splitcomplementary": "scheme_split",
}
SIZES = {
    "big": 1.45, "large": 1.45, "huge": 1.8, "giant": 1.8, "bada": 1.45,
    "bade": 1.45, "small": 0.6, "tiny": 0.45, "little": 0.6, "chhota": 0.6,
    "chota": 0.6, "mini": 0.5, "medium": 1.0,
}
POSITIONS = {
    "left": "left", "right": "right", "top": "top", "upper": "top",
    "bottom": "bottom", "lower": "bottom", "center": "center",
    "centre": "center", "middle": "center",
}
COUNTS = {
    "one": 1, "ek": 1, "two": 2, "do": 2, "pair": 2, "couple": 2,
    "three": 3, "teen": 3, "four": 4, "char": 4, "five": 5, "paanch": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "many": 6, "multiple": 6, "several": 5, "lots": 8,
}
STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "with", "and", "is", "are", "to",
    "by", "for", "from", "under", "over", "near", "behind", "beside", "side",
    "corner", "colored", "coloured", "color", "colour", "rang", "ka", "ki",
    "ke", "hai", "ek", "image", "picture", "photo", "drawing", "painting",
    "scene", "view", "style", "generate", "make", "create", "draw", "show",
    "beautiful", "nice", "amazing", "simple", "some", "tall", "wide", "bright",
}
# Devanagari (Hindi script) words. Written through NFC so nukta forms match user input.
_HI = {
    "color": {"लाल": "red", "नीला": "blue", "हरा": "green", "पीला": "yellow", "सफेद": "white",
              "काला": "black", "गुलाबी": "pink", "नारंगी": "orange", "बैंगनी": "purple",
              "भूरा": "brown", "सुनहरा": "gold"},
    "object": {"सूरज": "sun", "चांद": "moon", "चाँद": "moon", "तारे": "stars", "बादल": "cloud",
               "पहाड़": "mountain", "पेड़": "tree", "जंगल": "forest", "घर": "house", "शहर": "city",
               "समुद्र": "sea", "नदी": "sea", "झील": "sea", "फूल": "flower", "पक्षी": "bird",
               "चिड़िया": "bird", "इंद्रधनुष": "rainbow", "सड़क": "road", "ग्रह": "planet",
               "नाव": "boat", "रेगिस्तान": "desert", "घास": "grass"},
    "shape": {"दिल": "heart", "गोला": "circle", "चौकोर": "square", "त्रिकोण": "triangle",
              "तारा": "star"},
    "time": {"रात": "night", "शाम": "sunset", "सुबह": "dawn", "दिन": "day"},
    "flag": {"बर्फ": "snow", "बारिश": "rain", "कोहरा": "fog"},
}
_N = lambda s: unicodedata.normalize("NFC", s)       # noqa: E731
for _w, _t in _HI["color"].items():
    COLORS[_N(_w)] = COLORS[_t]
for _w, _t in _HI["object"].items():
    OBJECTS[_N(_w)] = _t
for _w, _t in _HI["shape"].items():
    SHAPES[_N(_w)] = _t
for _w, _t in _HI["time"].items():
    TIMES[_N(_w)] = _t
for _w, _t in _HI["flag"].items():
    FLAGS[_N(_w)] = _t
COUNTS.update({_N("एक"): 1, _N("दो"): 2, _N("तीन"): 3, _N("चार"): 4, _N("पांच"): 5})
STOPWORDS.update(_N(w) for w in ("और", "का", "की", "के", "में", "पर", "से", "है", "एक", "वाला"))

MAX_PROMPT_CHARS = 2000

# business props and concepts (see props/): merge without overriding the older, hand-tuned words
from .props import CONCEPTS as _CONCEPTS, CONCEPT_FLAGS as _CONCEPT_FLAGS, WORDS as _PROP_WORDS  # noqa: E402
for _w, _n in _PROP_WORDS.items():
    OBJECTS.setdefault(_w, _n)

# multi-word phrases collapsed into one known word before tokenizing
PHRASES = {
    "coffee shop": "coffeeshop", "tea shop": "teashop", "ice cream": "icecream", "gift box": "giftbox",
    "shopping bag": "shoppingbag", "shopping cart": "cart", "real estate": "realestate", "medical clinic": "clinic",
    "dental clinic": "clinic", "birthday cake": "cake", "wedding cake": "cake", "birthday party": "party",
    "birthday balloons": "balloon", "price tag": "tag", "business meeting": "meeting", "fitness center": "gym",
    "fitness centre": "gym", "yoga studio": "yogi", "yoga class": "yogi", "web design": "website",
    "online shopping": "ecommerce", "e-commerce": "ecommerce", "mobile app": "mobile", "customer support": "support",
    "customer service": "support", "customer review": "review", "customer reviews": "review", "hair salon": "salon",
    "beauty salon": "salon", "travel agency": "travel", "living room": "sofa",
    "coffee beans": "coffee", "pet shop": "petshop", "fire truck": "firetruck", "fire engine": "firetruck", "fire safety": "extinguisher", "police car": "policecar", "patrol car": "policecar", "police patrol car": "policecar", "police van": "policecar", "dental chair": "dentalchair", "ambulance van": "ambulance", "ice skating": "iceskating", "ice rink": "rink", "skating rink": "rink", "ski resort": "skiresort", "snow board": "snowboard", "winter sports": "wintersports", "ice hockey": "icehockey", "fire station": "fire", "fire brigade": "fire", "oral health": "oralhealth", "dental clinic": "dental", "dental care": "dental", "house painting": "painter house", "wall painting": "painter", "home painting": "painter house", "painting service": "painter", "painting services": "painter", "painting contractor": "painter", "pet store": "petshop", "pet care": "pets", "green energy": "greenenergy", "solar panel": "solarpanel", "wind turbine": "windmill", "sewing machine": "sewingmachine", "power tools": "tools", "toolbox": "toolbox", "wedding couple": "wedding", "study abroad": "education", "student visa": "education",
    "l-system": "lsystem", "l system": "lsystem", "flow field": "flowfield", "split complementary": "splitcomplementary",
    "graduation cap": "gradcap", "graduation hat": "gradcap", "gift shop": "shop", "book shop": "shop", "book store": "shop",
}
_PHRASE_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(PHRASES, key=len, reverse=True)) + r")\b")

# default instance counts when a noun is written in plural without a number
PLURAL_DEFAULT = {"tree": 4, "flower": 14, "cloud": 4, "bird": 5, "mountain": 3}


# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------
@dataclass
class Token:
    word: str
    kind: str          # color shape object region time flag size position count stop unknown
    value: object = None
    plural: bool = False


@dataclass
class Entity:
    kind: str                  # "object" | "shape"
    name: str
    color: tuple = None
    size: float = 1.0
    position: str = None
    count: int = 1
    secondary: bool = False      # came from a concept expansion beyond its first two props: dropped first when the picture is crowded


@dataclass
class ParsedPrompt:
    text: str
    tokens: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    time: str = None
    flags: set = field(default_factory=set)
    background: tuple = None
    sky_color: tuple = None
    ground_color: tuple = None
    loose_colors: list = field(default_factory=list)   # colours not tied to any object (brand colours)
    texts: list = field(default_factory=list)          # "quoted" strings to be written into the image

    def by_name(self):
        out = {}
        for e in self.entities:
            out.setdefault(e.name, []).append(e)
        return out

    @property
    def unknown_words(self):
        return [t.word for t in self.tokens if t.kind == "unknown"]


# --------------------------------------------------------------------------
# Tokenizer + parser
# --------------------------------------------------------------------------
_WORD_RE = re.compile(r"[a-z]+|[0-9]+|[\u0900-\u097f]+")


def _words(prompt):
    text = unicodedata.normalize("NFC", prompt.lower())
    text = _PHRASE_RE.sub(lambda m: PHRASES[m.group(1)], text)
    return _WORD_RE.findall(text)


def _classify(word):
    plural = False
    if word in OBJECTS and word not in ("stars",):
        pass
    elif word not in COLORS and word not in SHAPES and word.endswith("s") and len(word) > 3:
        stem = word[:-1]
        if stem in OBJECTS or stem in SHAPES:
            word, plural = stem, True
        elif word.endswith("es") and word[:-2] in OBJECTS:
            word, plural = word[:-2], True
    if word.isascii() and word.isdigit():
        return Token(word, "count", 24 if len(word) > 3 else max(1, min(int(word), 24)))
    if word in COLORS:
        return Token(word, "color", COLORS[word])
    if word in SHAPES:
        return Token(word, "shape", SHAPES[word], plural)
    if word in OBJECTS:
        return Token(word, "object", OBJECTS[word], plural)
    if word in REGION_WORDS:
        return Token(word, "region", REGION_WORDS[word])
    if word in TIMES:
        return Token(word, "time", TIMES[word])
    if word in FLAGS:
        return Token(word, "flag", FLAGS[word])
    if word in SIZES:
        return Token(word, "size", SIZES[word])
    if word in POSITIONS:
        return Token(word, "position", POSITIONS[word])
    if word in COUNTS:
        return Token(word, "count", COUNTS[word])
    if word in STOPWORDS:
        return Token(word, "stop")
    return Token(word, "unknown")


def tokenize(prompt):
    return [_classify(w) for w in _words(prompt)]


def _next_significant(tokens, i):
    """First token after i that is not a stopword / colour / size / count."""
    for t in tokens[i + 1:]:
        if t.kind in ("stop", "color", "size", "count", "position"):
            continue
        return t
    return None


_QUOTE_RE = re.compile("[\"\u201c\u201d]([^\"\u201c\u201d]{1,80})[\"\u201c\u201d]|(?<![A-Za-z0-9])[\'\u2018]([^\'\u2019]{1,80})[\'\u2019](?![A-Za-z0-9])")


def extract_texts(prompt):
    """Split "quoted text" out of a prompt: returns (prompt without the quoted parts, [cleaned texts])."""
    from .text import clean
    found = []
    for m in _QUOTE_RE.finditer(prompt):
        t = clean(m.group(1) or m.group(2))
        if t:
            found.append(t)
    return _QUOTE_RE.sub(" ", prompt), found[:3]


def parse(prompt):
    stripped, texts = extract_texts(prompt)
    tokens = tokenize(stripped)
    result = ParsedPrompt(text=prompt, tokens=tokens, texts=texts)
    pending = {"color": None, "size": 1.0, "position": None, "count": None}
    last = None
    expanded = set()                                           # a concept written twice ("ice skating rink") expands once

    def reset():
        pending.update(color=None, size=1.0, position=None, count=None)

    for i, tok in enumerate(tokens):
        kind = tok.kind
        if kind == "color":
            nxt = _next_significant(tokens, i)
            if nxt is not None and nxt.kind in ("object", "shape", "region"):
                pending["color"] = tok.value
            elif nxt is None and last is not None and last.color is None:
                last.color = tok.value            # "sun in red"
            else:
                # "red door", "blue abstract background": not tied to a known object, so it never recolours
                # the scene, but pattern/abstract renderers use it as the palette
                result.loose_colors.append(tok.value)
        elif kind == "size":
            pending["size"] = tok.value
        elif kind == "count":
            pending["count"] = tok.value
        elif kind == "position":
            nxt = _next_significant(tokens, i)
            if nxt is not None and nxt.kind in ("object", "shape"):
                pending["position"] = tok.value
            elif last is not None and last.position is None:
                last.position = tok.value         # "sun on the left"
        elif kind == "region":
            if tok.value == "background" and pending["color"]:
                result.background = pending["color"]
            elif tok.value == "sky" and pending["color"]:
                result.sky_color = pending["color"]
            elif tok.value == "ground" and pending["color"]:
                result.ground_color = pending["color"]
            reset()
        elif kind in ("object", "shape"):
            count = pending["count"]
            if count is None:
                count = PLURAL_DEFAULT.get(tok.value, 3) if tok.plural else 1
            if tok.value.startswith("@"):
                if tok.value in expanded:
                    reset()
                    continue
                expanded.add(tok.value)
                result.flags |= _CONCEPT_FLAGS.get(tok.value[1:], set())
            names = _CONCEPTS[tok.value[1:]][1] if tok.value.startswith("@") else (tok.value,)
            for k, nm in enumerate(names):                      # a concept word expands into several props
                ent = Entity(kind, nm, pending["color"] if k == 0 else None, pending["size"],
                             pending["position"], count if len(names) == 1 else 1, secondary=k >= 2)
                result.entities.append(ent)
                last = ent
            reset()
        elif kind == "time":
            result.time = tok.value
        elif kind == "flag":
            result.flags.add(tok.value)
    return result


# --------------------------------------------------------------------------
# Vectorizer
# --------------------------------------------------------------------------
def fnv1a(text):
    """Deterministic 32-bit hash (Python's built-in hash() is salted per run)."""
    h = 2166136261
    for byte in text.encode("utf-8"):
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return h


def vectorize(prompt, dim=32):
    """Unit-length hashed bag of word + character n-grams (+ ASCII statistics)."""
    vec = [0.0] * dim
    for w in _words(prompt):
        padded = "<%s>" % w
        grams = [w] + [padded[k:k + n] for n in (2, 3) for k in range(len(padded) - n + 1)]
        for g in grams:
            h = fnv1a(g)
            vec[h % dim] += 1.0 if (h >> 16) & 1 else -1.0
    ascii_sum = sum(ord(c) for c in prompt)
    for i in range(dim):
        vec[i] += 0.25 * math.sin(ascii_sum * (i + 1) * 0.001 + len(prompt))
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
