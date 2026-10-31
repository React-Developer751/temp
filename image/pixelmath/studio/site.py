"""Pictures for a generated business website: the bridge between a website generator and the studio.

A website generator knows what it built (business type, sub-niche, brand, services, colours, language). This module turns that into a set of
pictures that match the business: it picks the studio niche (never a lookalike: an unknown business gets a neutral abstract in the brand
colour and a report that says so), follows the site's colours and mood, leaves a calm area for the hero headline with guaranteed contrast, and
writes hero / about / gallery files plus an `images.json` the page can use (src, size, alt text, headline colour).

    from pixelmath.studio.site import site_pictures
    result = site_pictures({"business_type": "dental", "brand": "Harmony Dental", "mood": "calm"}, {"primary": "#0e7490"}, seed=1, out_dir="site/images")
    result["images"]["hero"]["src"], result["images"]["hero"]["text_color"], result["fallback"]
"""
import json
import os

from .api import make_set
from .niches import NICHES, load_all

# Core-Craft style business type id -> studio niche id. Types a website generator may have that the studio cannot draw map to None
# (they then get the honest neutral abstract). Keep this table next to the niches: adding a niche = one line here.
TYPE_TO_NICHE = {
    # care and wellbeing
    "dental": "dental", "clinic": "clinic-doctor", "ayurveda": "ayurveda", "physio": "physio", "salon": "salon", "spa": "spa", "vet": "pet-clinic",
    "skin": "skin-clinic", "eye": "eye-clinic", "mehendi": "mehendi", "tattoo": "tattoo",
    # professional services
    "law": "law-firm", "accounting": "accounting-finance", "architect": "architect", "interior": "interior-design", "realestate": "real-estate",
    "insurance": "insurance", "marketing": "digital-agency", "consulting": "consulting", "recruitment": "recruitment", "coworking": "coworking",
    "astrology": "astrology", "visa": "visa",
    # home, vehicle and field services
    "plumbing": "plumbing", "electrician": "electrician", "painting": "painting", "carpentry": "carpentry", "ac": "ac-repair", "cleaning": "cleaning",
    "construction": "construction", "solar": "solar-energy", "movers": "movers", "garage": "car-repair", "courier": "logistics", "landscape": "landscape",
    "welding": "welding", "tyres": "tyres", "security": "security", "tailor": "tailor",
    # retail
    "clothing": "fashion-boutique", "jewellery": "jewellery", "furniture": "furniture", "mobile": "mobile-store", "grocery": "grocery", "books": "bookstore",
    "gifts": "florist", "petshop": "petshop", "optical": "optical", "pharmacy": "pharmacy", "shop": "ecommerce", "autosales": "bike-showroom",
    # food
    "restaurant": "restaurant", "cafe": "cafe", "bakery": "bakery", "sweets": "sweet-shop", "catering": "catering", "icecream": "ice-cream",
    # learning
    "school": "coaching-tuition", "playschool": "playschool", "driving": "driving-school", "music": "music-academy", "robotics": "robotics-lab",
    "sports": "sports-academy",
    # creative, events, travel
    "photography": "photography", "design": "design-studio", "printing": "printing", "pottery": "pottery", "events": "event-party", "tenthouse": "tent-house",
    "travel": "travel-agency", "hotel": "hotel", "taxi": "taxi", "gaming": "gaming-zone",
    # fitness, tech, community
    "gym": "gym", "yoga": "yoga", "software": "saas", "ngo": "ngo",
}
# a sub-niche ("profile") is more precise than the type
PROFILE_TO_NICHE = {
    "italian": "restaurant-italian", "north_indian": "indian-thali", "south_indian": "south-indian", "chinese": "chinese-restaurant",
    "street_food": "street-food", "bar": "bar-lounge", "bakery": "bakery", "tea_cafe": "cafe",
    "dental": "dental", "skin": "skin-clinic", "eye": "eye-clinic", "physio": "physio", "crossfit": "gym", "yoga": "yoga", "zumba": "gym",
    "kurti": "kurti-store", "saree": "saree-boutique", "electronics": "mobile-store", "books": "bookstore", "autosales": "bike-showroom",
    "tyres": "tyres", "robotics": "robotics-lab", "pottery": "pottery",
}
# words in the business text that refine a type into a more exact niche: (type, words, niche)
TEXT_REFINE = (
    ("school", ("school", "classroom", "kindergarten", "cbse", "icse", "स्कूल"), "school"),
    ("clinic", ("skin", "derma", "acne", "facial", "त्वचा"), "skin-clinic"),
    ("clinic", ("diagnostic", "pathology", "blood test", "lab test", "पैथोलॉजी"), "diagnostic-lab"),
    ("clinic", ("counselling", "counseling", "therapist", "psycholog", "काउंसलिंग"), "counselling"),
    ("clinic", ("dietitian", "nutritionist", "diet plan", "डाइटीशियन"), "nutritionist"),
    ("vet", ("rescue", "shelter", "stray", "animal welfare"), "animal-welfare"),
    ("taxi", ("car rental", "self drive", "self-drive", "rent a car", "car hire", "car on rent"), "car-rental"),
    ("hotel", ("homestay", "home stay", "farm stay", "farmstay", "farmhouse"), "farm-stay"),
    ("hotel", ("paying guest", "hostel", "pg accommodation"), "pg-hostel"),
    ("garage", ("bike", "scooter", "two wheeler", "motorcycle"), "bike-garage"),
    ("insurance", ("loan agent", "home loan", "personal loan", "business loan", "loan advisor", "loan consultant"), "loan-finance"),
    ("mobile", ("mobile repair", "phone repair", "screen replacement", "mobile service centre"), "mobile-repair"),
    ("photography", ("drone", "aerial"), "drone-photography"),
    ("design", ("video editing", "video editor", "reel editing"), "video-editing"),
    ("salon", ("bridal makeup", "makeup artist", "bridal artist"), "bridal-makeup"),
    ("cafe", ("chai stall", "chai tapri", "tea stall", "chai point"), "chai-stall"),
    ("restaurant", ("cloud kitchen", "ghost kitchen"), "cloud-kitchen"),
    ("catering", ("tiffin", "dabba"), "tiffin-service"),
    ("events", ("banquet", "function hall", "marriage hall", "party hall"), "banquet-hall"),
    ("events", ("dj sound", "dj and sound", "wedding dj"), "dj-sound"),
    ("garage", ("car wash", "carwash", "detailing", "कार वॉश"), "car-wash"),
    ("autosales", ("car showroom", "car dealer", "cars", "कार शोरूम"), "car-showroom"),
    ("events", ("wedding", "mandap", "shaadi", "marriage", "शादी", "विवाह"), "wedding"),
    ("salon", ("barber", "gents salon", "beard", "shave", "नाई"), "barber"),
    ("software", ("mobile app", "android", "ios app", "app development"), "mobile-app"),
    ("cafe", ("juice", "smoothie", "shake"), "juice-bar"),
    ("restaurant", ("burger", "fast food", "fries", "sandwich"), "fast-food"),
    ("restaurant", ("sushi", "japanese", "ramen"), "sushi"),
    ("restaurant", ("thali", "dhaba", "punjabi", "mughlai", "biryani"), "indian-thali"),
    ("grocery", ("farm", "tractor", "crop", "kisan", "खेती"), "agriculture-farm"),
    ("shop", ("toy", "toys", "kids toys"), "toy-store"),
    ("clothing", ("shoe", "shoes", "footwear", "sneaker"), "shoe-store"),
    ("gifts", ("toy", "toys"), "toy-store"),
)
# Core-Craft mood words -> studio mood (None = keep the niche's own mood)
MOOD_MAP = {"calm": "cool", "cool": "cool", "warm": "warm", "friendly": "light", "playful": "light", "elegant": None, "bold": None}


def niche_for(business, text=""):
    """-> (niche_id or None, why). `business` has business_type and optionally profile; `text` is the owner's prompt/brand/services."""
    load_all()
    low = (text or "").lower()
    t, profile = business.get("business_type") or business.get("type"), business.get("profile")
    for tid, words, nid in TEXT_REFINE:
        if t == tid and nid in NICHES and any(w in low for w in words):
            return nid, "type %s + words in the text" % t
    if profile in PROFILE_TO_NICHE and PROFILE_TO_NICHE[profile] in NICHES:
        return PROFILE_TO_NICHE[profile], "sub-niche %s" % profile
    nid = TYPE_TO_NICHE.get(t)
    if nid and nid in NICHES:
        return nid, "business type %s" % t
    return None, "no picture niche for business type %r" % (t,)


def mood_for(business, palette, niche_id):
    if palette and palette.get("dark"):
        return "dark"
    m = MOOD_MAP.get(business.get("mood"))
    return m or (NICHES[niche_id].mood if niche_id in NICHES else "light")


def alt_text(business, niche_id, role):
    title = NICHES[niche_id].title if niche_id in NICHES else None
    brand = business.get("brand") or ""
    base = {"hero": "Illustration for %s" % brand, "about": "About %s" % brand}.get(role, "%s gallery picture" % brand)
    return ("%s: %s" % (base, title) if title else base).strip(": ")


def site_pictures(business, palette=None, seed=0, count=6, text_zone="left", out_dir=None, text="", fmt="jpeg", model=None, subdir=""):
    """Pictures for one generated site. Returns a dict:

    niche, fallback, reason, mood, accent, report (the judge's set report), images {hero, about, tiles: [...]}; every image has
    file, src (relative path inside the site), width, height, bytes, alt, text_color (colour for text over it), contrast.
    With `out_dir` the files and images.json are written there.
    """
    business = dict(business)
    palette = palette or {}
    niche_id, why = niche_for(business, text)
    accent = palette.get("primary") or palette.get("accent")
    mood = mood_for(business, palette, niche_id)
    prompt = text or business.get("brand") or business.get("type_label") or "website"
    results, rep = make_set(prompt, count, seed, accent=accent, mood=mood, text_zone=text_zone, niche=niche_id or "none", fmt=fmt, model=model)
    ext = "jpg" if fmt == "jpeg" else "png"
    prefix = (subdir.strip("/") + "/") if subdir else ""
    images, tiles = {}, []
    for r in results:
        role = r.report["role"]
        name = "hero" if role == "hero" else "about" if role == "about" else "tile-%d" % (len(tiles) + 1)
        item = {"file": "%s.%s" % (name, ext), "src": "%s%s.%s" % (prefix, name, ext), "width": r.canvas.w, "height": r.canvas.h, "bytes": r.report["bytes"],
                "alt": alt_text(business, niche_id, role), "text_color": r.report.get("text_color"), "contrast": r.report.get("contrast"),
                "role": role, "seed": r.report["seed"]}
        if role == "tile":
            tiles.append(item)
        else:
            images[role] = item
        item["_data"] = r.data
    images["tiles"] = tiles
    out = {"niche": niche_id if not rep["fallback"] else None, "requested_niche": niche_id, "fallback": rep["fallback"], "reason": why, "mood": mood,
           "accent": rep["accent"], "text_zone": text_zone, "report": {k: v for k, v in rep.items() if k != "images"}}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        for it in [images["hero"], images["about"]] + tiles:
            with open(os.path.join(out_dir, it["file"]), "wb") as fh:
                fh.write(it["_data"])
    for it in [images["hero"], images["about"]] + tiles:
        it.pop("_data", None)
    out["images"] = images
    if out_dir:
        with open(os.path.join(out_dir, "images.json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    return out
