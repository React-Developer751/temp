"""Small English agreement helpers for text built from a person's own words ("cakes", "home delivery", "root canal treatment").
is_plural(phrase) guesses whether a noun phrase takes a plural verb; agree() and forms() give the matching words (is/are, was/were, it/them, this/these).
Stdlib only, no word lists beyond the few irregular cases below."""
import re

PLURAL_ONLY = {"people", "children", "men", "women", "teeth", "feet", "mice", "geese", "clothes", "goods", "jeans", "trousers", "glasses", "spectacles", "sweets",
               "groceries", "supplies", "essentials", "savings", "premises", "outskirts", "staff", "police", "cattle", "kids"}
SINGULAR_S = {"news", "series", "species", "physics", "mathematics", "maths", "economics", "athletics", "aerobics", "gymnastics", "diabetes", "measles", "lens", "gas",
              "bus", "yes", "basis", "analysis", "thesis", "status", "campus", "bonus", "canvas", "chassis", "mattress", "address", "class", "glass", "grass", "dress",
              "fitness", "wellness", "business", "access", "process", "progress", "success", "christmas", "sangeet", "aids", "abs", "plus", "tennis", "billiards", "darts",
              "politics", "logistics", "electronics", "graphics", "ethics", "acoustics", "robotics", "dynamics", "aesthetics", "mechanics", "statistics", "linguistics"}
UNCOUNTABLE = {"equipment", "furniture", "jewellery", "jewelry", "software", "hardware", "advice", "information", "luggage", "clothing", "makeup", "decor", "care", "support",
               "help", "delivery", "service", "food", "bread", "rice", "tea", "coffee", "chai", "milk", "fruit", "water", "music", "art", "work", "training", "coaching",
               "tuition", "insurance", "cover", "storage", "parking", "seating", "wifi", "wi-fi", "machinery", "stationery", "paperwork", "tax", "gst", "mehendi", "henna"}
_TAIL = re.compile(r"(?:ss|us|is|ous|ics)$")


def _words(phrase):
    return [w for w in re.split(r"[\s/-]+", re.sub(r"[^\w\s/'-]", " ", str(phrase))) if w]


def is_plural(phrase):
    """True when the phrase reads as plural: "cakes", "breads and cookies", "SUVs", "children's toys"; False for "home delivery", "root canal treatment", "fitness"."""
    words = _words(phrase)
    if not words:
        return False
    low = [w.lower() for w in words]
    if "and" in low[1:-1] and _plural_word(words[low.index("and") - 1]):   # "pastries and cupcakes", "sedans and SUVs"
        return True
    return _plural_word(words[-1])


def _plural_word(w):
    low = w.lower().strip("'")
    if low in PLURAL_ONLY:
        return True
    if low in SINGULAR_S or low in UNCOUNTABLE or len(low) < 3:
        return False
    if re.fullmatch(r"[A-Z]{2,}s", w):   # SUVs, ATMs
        return True
    if w.isupper():   # AC, CCTV, GST
        return False
    if low.endswith("ing"):   # cleaning, catering
        return False
    return low.endswith("s") and not _TAIL.search(low)


def agree(phrase, singular, plural):
    return plural if is_plural(phrase) else singular


def forms(phrase):
    """{"it", "is", "was", "this", "has", "does", "its"} for the phrase: "cakes" -> them/are/were/these/have/do/their."""
    p = is_plural(phrase)
    return {"it": "them" if p else "it", "It": "They" if p else "It", "they": "they" if p else "it", "is": "are" if p else "is", "was": "were" if p else "was",
            "this": "these" if p else "this", "has": "have" if p else "has", "does": "do" if p else "does", "its": "their" if p else "its"}


def a_an(word):
    """The indefinite article for a word ("an AC visit", "a used car", "an hour")."""
    w = str(word).strip()
    if not w:
        return "a"
    first = w.split()[0]
    if first.isupper() and len(first) > 1:
        return "an" if first[0] in "AEFHILMNORSX" else "a"
    low = first.lower()
    if low.startswith(("hour", "honest", "heir")):
        return "an"
    if low.startswith(("uni", "use", "usu", "eu", "one", "once", "ur")):
        return "a"
    return "an" if low[:1] in "aeiou" else "a"
