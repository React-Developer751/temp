"""Team portraits: a friendly illustrated character, shoulders up, in the palette of its business.

No photo, no real face, no text: simple shapes (head, hair, shoulders, collar) plus one accessory that tells the job (hard hat, chef hat,
stethoscope, headset, cap, tie, glasses). `render_portrait(role, width, height, seed, pal, niche)` returns a graded Canvas.
"""
import random
import re

from ..raster import mix, scale
from .palette import WHITE
from .stage import Stage

SKIN = ((0.97, 0.82, 0.70), (0.92, 0.73, 0.58), (0.84, 0.63, 0.46), (0.72, 0.50, 0.34), (0.58, 0.39, 0.26), (0.45, 0.30, 0.20))
HAIR = ((0.09, 0.07, 0.06), (0.20, 0.13, 0.09), (0.33, 0.20, 0.11), (0.52, 0.52, 0.55), (0.12, 0.09, 0.15), (0.45, 0.27, 0.12))
EYE = (0.12, 0.09, 0.08)

# role words -> outfit
OUTFITS = (
    ("medical", ("doctor", "nurse", "physician", "dentist", "surgeon", "physiotherapist", "pharmacist", "lab", "vet", "dermatologist", "paediatric", "specialist doctor")),
    ("chef", ("chef", "cook", "baker", "barista", "kitchen", "halwai", "pastry", "brewer", "bartender")),
    ("hardhat", ("engineer", "site", "foreman", "mason", "electrician", "plumber", "welder", "installer", "technician", "mechanic", "carpenter", "painter",
                 "fabricator", "supervisor", "loader", "gardener", "fitter", "pest", "termite")),
    ("headset", ("support", "receptionist", "coordinator", "dispatcher", "helpdesk", "customer", "telecaller", "front desk", "booking")),
    ("cap", ("driver", "guard", "courier", "delivery", "rider", "chauffeur")),
    ("suit", ("advocate", "lawyer", "consultant", "accountant", "advisor", "adviser", "manager", "agent", "officer", "director", "notary", "founder", "partner",
              "counsel", "analyst", "ca ", "recruiter", "banker", "broker", "planner")),
    ("glasses", ("designer", "editor", "photographer", "developer", "artist", "writer", "analyst", "producer", "videographer", "pilot", "illustrator")),
    ("coach", ("coach", "trainer", "instructor", "teacher", "tutor", "mentor", "faculty", "yoga")),
    ("apron", ("florist", "tailor", "stylist", "barber", "assistant", "shopkeeper", "salesperson", "sales", "packer", "cashier", "groomer")),
)
NICHE_OUTFIT = {
    "medical": ("dental", "clinic-doctor", "eye-clinic", "skin-clinic", "physio", "pharmacy", "pet-clinic", "diagnostic-lab", "ayurveda", "nutritionist"),
    "chef": ("restaurant", "restaurant-italian", "cafe", "bakery", "cloud-kitchen", "tiffin-service", "catering", "south-indian", "chinese-restaurant", "sushi",
             "fast-food", "indian-thali", "street-food", "chai-stall", "sweet-shop", "ice-cream", "juice-bar", "bar-lounge"),
    "hardhat": ("construction", "plumbing", "electrician", "welding", "painting", "carpentry", "ac-repair", "pest-control", "movers", "car-repair", "tyres",
                "solar-energy", "landscape", "bike-garage", "water-purifier", "scrap-recycling", "car-wash"),
    "suit": ("law-firm", "accounting-finance", "insurance", "consulting", "recruitment", "real-estate", "visa", "loan-finance", "notary-documents", "architect"),
    "cap": ("security", "taxi", "car-rental", "logistics"),
}
SHIRT_ROLE = {"medical": (0.97, 0.98, 0.99), "chef": (0.98, 0.98, 0.97)}


TRADE_NICHES = ("construction", "plumbing", "electrician", "welding", "painting", "carpentry", "ac-repair", "pest-control", "movers", "car-repair", "tyres", "solar-energy",
                "landscape", "bike-garage", "water-purifier", "scrap-recycling", "car-wash", "laundry", "cleaning", "farm-stay", "banquet-hall", "tent-house")


def _has(words, text):
    return any(re.search(r"\b%s\b" % re.escape(w.strip()), text) for w in words)


def outfit_for(role, niche=None):
    """Role words first (whole words), then the business: a software 'engineer' wears glasses, a site 'engineer' a hard hat."""
    low = (role or "").lower()
    name = None
    for cand, words in OUTFITS:
        if _has(words, low):
            name = cand
            break
    if name == "hardhat" and niche not in TRADE_NICHES:                 # a hard hat belongs to a trade or site, not to a software, DJ or printing team
        name = "glasses" if _has(("engineer", "technician", "specialist", "fitter"), low) else "apron" if "supervisor" in low else "shirt"
    if name in (None, "apron", "shirt", "headset", "coach") and niche:
        for kind, ids in NICHE_OUTFIT.items():
            if niche in ids and not (name == "headset" or name == "coach"):
                if kind != "hardhat" or name is None:
                    return kind if kind != "hardhat" else "hardhat"
    if name:
        return name
    for kind, ids in NICHE_OUTFIT.items():
        if niche in ids:
            return kind
    return "shirt"


def _portrait(S, role, niche, accent_key):
    P, rng = S.pal, random.Random(S.seed * 131 + 7)
    outfit = outfit_for(role, niche)
    skin = rng.choice(SKIN)
    hair = rng.choice(HAIR)
    style = rng.choice(("short", "short", "side", "long", "bun", "curly", "bald"))
    beard = style in ("short", "side", "bald", "curly") and rng.random() < 0.38
    glasses = outfit == "glasses" or rng.random() < 0.22
    shirt = SHIRT_ROLE[outfit] if outfit in SHIRT_ROLE else mix(P.accent, P.ink, 0.12)
    skin_d = scale(skin, 0.80)
    # backdrop: the palette's wall with a soft accent disc behind the head
    with S.far():
        S.wall(P.wall_top, P.wall_bot, 1.0)
        S.soft(1.0, 0.45, 0.55, 0.55, P.accent_light, 0.55, 1.4)
        S.soft(1.35, 0.1, 0.4, 0.4, P.accent2, 0.30, 1.2)
        S.bokeh(10, 0.2, 0.0, 1.8, 1.0, [P.accent_light, P.light], 0.015, 0.05, 0.18)
    S.circle(1.0, 0.50, 0.40, mix(P.accent_light, WHITE, 0.25), alpha=0.35, lift=0, soft=2.0)
    S.shadow(1.0, 1.0, 0.7, 0.12, 0.22)
    # shoulders and torso
    S.ellipse(1.0, 1.04, 0.47, 0.36, shirt, lift=0.10)
    S.ellipse(0.93, 0.88, 0.18, 0.10, mix(shirt, WHITE, 0.16), alpha=0.30, lift=0, soft=6.0)          # soft key-light sheen on the left shoulder
    # neck + head
    S.rect(1.0, 0.72, 0.13, 0.17, skin_d, r=0.04, lift=0.04)
    S.ellipse(1.0, 0.465, 0.172, 0.208, skin, lift=0.07)
    S.ellipse(0.832, 0.485, 0.028, 0.048, skin_d, lift=0.03)
    S.ellipse(1.168, 0.485, 0.028, 0.048, skin_d, lift=0.03)
    # hair behind the head (long / bun)
    if style == "long":
        S.ellipse(1.0, 0.52, 0.21, 0.30, hair, lift=0.05)
        S.ellipse(1.0, 0.465, 0.172, 0.208, skin, lift=0.07)
    if style == "bun":
        S.circle(1.0, 0.215, 0.07, hair, lift=0.08)
    # collar and chest details, by outfit
    if outfit in ("suit", "glasses", "coach", "shirt", "headset", "cap", "apron"):
        S.poly([(0.90, 0.64), (1.10, 0.64), (1.0, 0.80)], WHITE if outfit in ("suit", "coach") else mix(shirt, WHITE, 0.55), alpha=0.95, soft=1.0)
        S.poly([(0.86, 0.70), (0.93, 0.68), (1.0, 0.82), (0.90, 0.96)], scale(shirt, 0.86), alpha=0.9, soft=1.0)
        S.poly([(1.14, 0.70), (1.07, 0.68), (1.0, 0.82), (1.10, 0.96)], scale(shirt, 0.86), alpha=0.9, soft=1.0)
    if outfit == "suit":
        tie = mix(P.accent_dark, P.ink, 0.2)
        S.poly([(0.985, 0.74), (1.015, 0.74), (1.03, 0.97), (1.0, 1.02), (0.97, 0.97)], tie, soft=1.0)
        S.poly([(0.97, 0.72), (1.03, 0.72), (1.015, 0.755), (0.985, 0.755)], scale(tie, 0.8), soft=1.0)
    if outfit == "medical":
        S.poly([(0.91, 0.64), (1.09, 0.64), (1.0, 0.78)], mix(P.accent, WHITE, 0.15), alpha=0.95, soft=1.0)                # scrub top under the white coat
        S.poly([(0.86, 0.70), (0.93, 0.68), (1.0, 0.82), (0.90, 1.0)], WHITE, soft=1.0)
        S.poly([(1.14, 0.70), (1.07, 0.68), (1.0, 0.82), (1.10, 1.0)], WHITE, soft=1.0)
        steth = (0.22, 0.24, 0.27)                                                                                           # stethoscope round the neck
        S.line(0.90, 0.69, 0.93, 0.90, 0.016, steth)
        S.line(1.10, 0.69, 1.07, 0.90, 0.016, steth)
        S.line(0.93, 0.90, 1.0, 0.97, 0.016, steth)
        S.line(1.07, 0.90, 1.0, 0.97, 0.016, steth)
        S.circle(1.0, 0.985, 0.028, (0.62, 0.65, 0.68), lift=0.15)
    if outfit == "chef":
        S.poly([(0.88, 0.70), (1.0, 0.76), (1.12, 0.70), (1.12, 0.78), (1.0, 0.84), (0.88, 0.78)], P.accent, alpha=0.95, soft=1.0)       # neckerchief
        for k in range(3):
            S.circle(0.96 + 0.04 * k, 0.93 + 0.01 * k, 0.012, scale(WHITE, 0.82), lift=0.1)                                              # jacket buttons
    if outfit == "hardhat":
        vest = (0.98, 0.62, 0.12)
        S.poly([(0.80, 0.70), (0.92, 0.66), (0.94, 1.0), (0.66, 1.0)], vest, soft=1.0)
        S.poly([(1.20, 0.70), (1.08, 0.66), (1.06, 1.0), (1.34, 1.0)], vest, soft=1.0)
        S.poly([(0.72, 0.90), (1.28, 0.90), (1.30, 0.94), (0.70, 0.94)], (0.94, 0.94, 0.90), alpha=0.9, soft=1.0)                      # reflective band
    if outfit == "apron":
        S.poly([(0.90, 0.78), (1.10, 0.78), (1.18, 1.02), (0.82, 1.02)], mix(P.accent, P.paper, 0.3), soft=1.0)
        S.line(0.90, 0.78, 0.88, 0.68, 0.014, mix(P.accent, P.paper, 0.3))
        S.line(1.10, 0.78, 1.12, 0.68, 0.014, mix(P.accent, P.paper, 0.3))
    if outfit == "coach":
        S.line(0.96, 0.76, 0.99, 0.92, 0.008, (0.9, 0.9, 0.9))                                                                        # whistle lanyard
        S.rect(1.0, 0.94, 0.045, 0.028, (0.85, 0.85, 0.88), r=0.01, lift=0.1)
    # hair (front)
    if style in ("short", "side", "curly"):
        S.ellipse(1.0, 0.335, 0.178, 0.105, hair, lift=0.06)
        S.ellipse(0.842, 0.405, 0.03, 0.08, hair, lift=0.04)
        S.ellipse(1.158, 0.405, 0.03, 0.08, hair, lift=0.04)
        if style == "side":
            S.poly([(0.84, 0.36), (1.0, 0.30), (1.16, 0.36), (1.12, 0.31), (1.0, 0.27), (0.88, 0.31)], hair, soft=1.0)
        if style == "curly":
            for k in range(7):
                S.circle(0.85 + 0.05 * k, 0.30 + 0.015 * (k % 2), 0.045, hair, lift=0.08)
    elif style == "long":
        S.ellipse(1.0, 0.33, 0.185, 0.095, hair, lift=0.05)
        S.ellipse(0.845, 0.52, 0.04, 0.17, hair, lift=0.04)
        S.ellipse(1.155, 0.52, 0.04, 0.17, hair, lift=0.04)
    elif style == "bun":
        S.ellipse(1.0, 0.34, 0.178, 0.10, hair, lift=0.06)
    elif style == "bald":
        S.ellipse(0.835, 0.43, 0.022, 0.06, hair, lift=0.03)
        S.ellipse(1.165, 0.43, 0.022, 0.06, hair, lift=0.03)
    # face
    for sx in (-1, 1):
        S.ellipse(1.0 + sx * 0.066, 0.478, 0.016, 0.02, EYE, lift=0)
        S.circle(1.0 + sx * 0.060, 0.471, 0.005, WHITE, lift=0)
        S.line(1.0 + sx * 0.098, 0.440, 1.0 + sx * 0.040, 0.432 + (0.004 if sx < 0 else 0), 0.011, scale(hair, 0.9))
        S.circle(1.0 + sx * 0.105, 0.545, 0.034, (0.93, 0.45, 0.42), alpha=0.28, lift=0, soft=6.0)
    S.ellipse(1.0, 0.525, 0.012, 0.022, skin_d, alpha=0.55, lift=0, soft=2.0)
    S.line(0.955, 0.585, 0.985, 0.60, 0.011, (0.62, 0.22, 0.20))                                                                   # smile
    S.line(0.985, 0.60, 1.015, 0.60, 0.011, (0.62, 0.22, 0.20))
    S.line(1.015, 0.60, 1.045, 0.585, 0.011, (0.62, 0.22, 0.20))
    if beard:
        S.poly([(0.845, 0.55), (0.90, 0.64), (1.0, 0.68), (1.10, 0.64), (1.155, 0.55), (1.12, 0.60), (1.0, 0.625), (0.88, 0.60)], hair, alpha=0.92, soft=1.0)
    if glasses:
        gl = (0.14, 0.14, 0.18)
        for sx in (-1, 1):
            S.ellipse(1.0 + sx * 0.066, 0.478, 0.048, 0.040, WHITE, alpha=0.10, lift=0, soft=1.0)
            for a0 in range(0, 360, 30):
                import math
                a1 = a0 + 30
                S.line(1.0 + sx * 0.066 + 0.048 * math.cos(math.radians(a0)), 0.478 + 0.040 * math.sin(math.radians(a0)),
                       1.0 + sx * 0.066 + 0.048 * math.cos(math.radians(a1)), 0.478 + 0.040 * math.sin(math.radians(a1)), 0.008, gl)
        S.line(0.986, 0.472, 1.014, 0.472, 0.008, gl)
    # headwear / headset
    if outfit == "hardhat":
        helmet = (0.98, 0.78, 0.15) if accent_key % 2 else mix(P.accent, WHITE, 0.2)
        S.ellipse(1.0, 0.285, 0.19, 0.12, helmet, lift=0.10)
        S.rect(1.0, 0.335, 0.40, 0.022, scale(helmet, 0.82), r=0.011, lift=0.05)
        S.rect(1.0, 0.205, 0.05, 0.05, scale(helmet, 0.9), r=0.02, lift=0.05)
    if outfit == "chef":
        S.rect(1.0, 0.285, 0.30, 0.07, WHITE, r=0.02, lift=0.05)
        for dx, dy, r in ((-0.10, 0.20, 0.08), (0.0, 0.16, 0.10), (0.10, 0.20, 0.08)):
            S.circle(1.0 + dx, dy, r, WHITE, lift=0.07)
    if outfit == "cap":
        capc = mix(P.accent_dark, P.ink, 0.35)
        S.ellipse(1.0, 0.30, 0.185, 0.10, capc, lift=0.08)
        S.ellipse(1.0, 0.345, 0.25, 0.026, scale(capc, 0.85), lift=0.05)
    if outfit == "headset":
        hs = (0.18, 0.19, 0.23)
        S.line(0.828, 0.50, 0.835, 0.34, 0.016, hs)
        S.line(0.835, 0.34, 1.0, 0.255, 0.016, hs)
        S.line(1.0, 0.255, 1.165, 0.34, 0.016, hs)
        S.line(1.165, 0.34, 1.172, 0.50, 0.016, hs)
        S.rect(0.826, 0.50, 0.03, 0.08, hs, r=0.014, lift=0.1)
        S.rect(1.174, 0.50, 0.03, 0.08, hs, r=0.014, lift=0.1)
        S.line(1.172, 0.54, 1.10, 0.62, 0.010, hs)
        S.circle(1.10, 0.62, 0.014, hs, lift=0.1)
    S.glow(0.90, 0.36, 0.30, S.pal.light, 0.10)


def render_portrait(role, width=600, height=600, seed=0, pal=None, niche=None):
    """-> Canvas (graded, with grain). `pal` is a studio Palette (make_palette(accent, mood))."""
    S = Stage(width, height, pal, seed)
    _portrait(S, role, niche, seed)
    return S.finish(grain=0.012, vignette=0.18)
