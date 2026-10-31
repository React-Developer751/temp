"""Business props. Importing this package registers every prop in `REGISTRY` and builds `WORDS`."""
from .core import REGISTRY, Prop, draw_prop  # noqa: F401
from . import food, retail, tech, people, vehicles, home, misc, buildings, animals, machinery, tools, playground, emergency, medical, winter  # noqa: F401

# Words that are too generic or ambiguous to summon a prop ("business", "photo", "light", ...).
DROP = {
    "photo", "photos", "film", "best", "top", "first", "aid", "care", "caring", "treatment", "light", "lights",
    "room", "rooms", "study", "studying", "reading", "business", "company", "firm", "agency", "group", "nature",
    "garden", "cross", "checkout", "shopping", "moving", "parcel", "bag", "backpack", "congratulations", "surprise",
    "love", "romance", "romantic", "valentine", "stars", "rose", "flowers", "affordable", "cheap", "near", "local",
    "visit", "branch", "branches", "booking", "holiday", "vacation", "tourist", "tour", "tours", "tourism",
    "award", "awards", "wellbeing", "whatsapp", "cottage", "home", "homes", "skyscraper", "school", "college",
    "present", "gifting", "stay", "luxury", "society", "rent", "rental", "tenant", "tutoring", "coaching",
    "talk", "speak", "speaking", "explore", "adventure", "happy", "stall", "market", "outlet", "kitchen",
}

# Business concepts: one word summons a small composition of props.
CONCEPTS = {
    "translation": (("translation", "translate", "translator", "language", "multilingual", "localization", "localisation",
                     "interpreter", "interpretation", "international", "global", "world", "worldwide", "earth"),
                    ("globe", "document", "chat")),
    "assignment": (("assignment", "essay", "thesis", "dissertation", "homework", "coursework", "assignments"),
                   ("document", "pencil", "book")),
    "software": (("software", "saas", "app", "website", "web", "online", "digital", "startup", "coding", "programming", "it"),
                 ("monitor", "laptop")),
    "marketing": (("marketing", "seo", "advertising", "branding", "sales", "revenue", "profit", "analytics", "growth",
                   "statistics", "kpi", "investment", "economy", "finance", "financial"), ("chart", "laptop")),
    "wellness": (("wellness", "spa", "ayurveda", "ayurvedic", "herbal", "aromatherapy", "massage"), ("lotus", "candle", "plant")),
    "wedding": (("wedding", "bride", "groom", "marriage", "bridal", "engagement", "married", "newlyweds", "honeymoon", "shaadi", "vivah"),
                ("weddingcouple", "bouquet")),
    "party": (("party", "celebration", "celebrate", "festival", "carnival", "anniversary", "event", "decoration", "birthday", "janamdin"),
              ("balloons", "cake", "giftbox")),
    "travel": (("travel", "trip", "journey", "luggage", "baggage", "tourism", "tourist", "holiday", "vacation", "tour"),
               ("airplane", "suitcase", "globe")),
    "legal": (("lawyer", "law", "legal", "court", "attorney", "notary", "notarised", "notarized", "advocate"),
              ("businessman", "document", "shield")),
    "education": (("education", "learning", "course", "elearning", "tutoring", "coaching", "classroom", "exam"),
                  ("student", "book", "certificate")),
    "pets": (("pet", "petcare", "veterinary", "vet", "grooming", "kennel", "adoption"), ("dog", "cat")),
    "petshop": (("petshop",), ("shop", "dog", "cat")),
    "farm": (("farm", "farming", "agriculture", "agricultural", "ranch", "farmer", "livestock", "krishi"), ("tractor", "cow", "sheep")),
    "zoo": (("zoo", "safari", "wildlife"), ("elephant", "parrot")),
    "plumbing": (("plumber", "plumbing", "pipe", "leak", "drainage"), ("worker", "faucet", "wrench", "toolbox")),
    "carpentry": (("carpenter", "carpentry", "woodwork", "woodworking", "joinery"), ("saw", "hammer", "toolbox")),
    "electrical": (("electrician", "electrical", "wiring"), ("worker", "plug", "lightbulb")),
    "painting": (("painter", "decorator", "whitewash", "repainting", "paint", "renovation"), ("paintroller", "bucket", "ladder")),
    "construction": (("construction", "builder", "civil", "infrastructure", "contractor", "developer"), ("crane", "excavator", "worker", "hardhat")),
    "mechanic": (("mechanic", "garage", "servicing"), ("wrench", "gear", "toolbox", "screwdriver")),
    "repair": (("repair", "workshop", "hardware", "tools", "handyman", "maintenance", "diy"), ("toolbox", "wrench", "hammer", "screwdriver", "drill")),
    "tailoring": (("tailor", "tailoring", "stitching", "sewing", "alteration", "darzi"), ("sewingmachine", "spool", "tshirt", "scissors")),
    "salon": (("salon", "barber", "haircut", "hairdresser", "beauty", "parlour", "parlor"), ("scissors", "comb", "plant")),
    "cleaning": (("cleaning", "cleaner", "housekeeping", "laundry", "maid", "janitor"), ("broom", "bucket")),
    "playground": (("playground", "park", "kindergarten", "amusement"), ("swing", "slide", "seesaw", "child")),
    "sports": (("sports", "sport", "game", "stadium", "athletics", "tournament"), ("football", "cricket", "trophy")),
    "energy": (("energy", "power", "renewable", "greenenergy"), ("solarpanel", "windmill")),
    "emergency": (("emergency", "rescue", "emergencies", "firstresponder"), ("ambulance", "firetruck", "policecar")),
    "fire": (("fire", "blaze", "firefighting"), ("firetruck", "firefighter", "hydrant")),
    "safety": (("safety", "protective"), ("extinguisher", "hardhat", "shield")),
    "office": (("office", "workplace", "corporate", "coworking", "workspace"), ("monitor", "laptop", "plant")),
    "healthcare": (("health", "healthcare", "medical", "hygiene", "checkup"), ("doctor", "medicalcross", "stethoscope")),
    "pharmacy": (("pharmacy", "medicine", "chemist", "dawakhana", "drugstore"), ("pills", "syringe", "medicalcross")),
    "dental": (("dental", "orthodontics", "braces", "oralhealth"), ("dentist", "tooth", "toothbrush", "dentalchair")),
    "skiing": (("skiing", "skiresort", "slope", "snowboarding", "winterresort"), ("skier", "snowboard", "ski"), ("snow",)),
    "skating": (("skating", "iceskating", "skatingrink", "rink", "figureskating"), ("skater", "iceskate"), ("snow",)),
    "wintersports": (("wintersports", "wintersport"), ("skier", "skater", "snowboard"), ("snow",)),
}
HINGLISH = {"kitab": "book", "paisa": "coins", "khana": "plate", "kursi": "chair", "palang": "bed", "ghadi": "watch",
            "joote": "shoe", "vidyarthi": "student", "gubbare": "balloons", "dukaan": "shop", "gaadi": "car",
            "chai": "coffee_cup", "dhaba": "restaurant", "mithai": "cake"}

WORDS = {}
DUPLICATES = []
for _p in REGISTRY.values():
    _ws = [w for w in _p.words if w not in DROP]
    # simple plurals are handled by the tokenizer ("cars" -> car), so list singular forms only
    _ws = [w for w in _ws if not ((w.endswith("s") and w[:-1] in _ws) or (w.endswith("es") and w[:-2] in _ws))]
    _p.words = tuple(dict.fromkeys(_ws))
    for _w in _p.words:
        if _w in WORDS and WORDS[_w] != _p.name:
            DUPLICATES.append((_w, WORDS[_w], _p.name))
        else:
            WORDS[_w] = _p.name

CONCEPT_FLAGS = {n: set(v[2]) for n, v in CONCEPTS.items() if len(v) > 2}
for _name, _val in CONCEPTS.items():
    _words, _props = _val[0], _val[1]
    for _w in _words:
        for _p in REGISTRY.values():                     # a concept word replaces the same word on a single prop
            if _w in _p.words:
                _p.words = tuple(x for x in _p.words if x != _w)
        WORDS[_w] = "@" + _name
for _w, _n in HINGLISH.items():
    WORDS[_w] = _n
