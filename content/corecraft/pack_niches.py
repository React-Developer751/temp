"""Hand-written layer that turns the author's 77 business types (corecraft/business_types.py) into niche packs: which text bank (family) each type uses and its
sample prices. training/build_niches.py reads this and writes corecraft/data/author_niches.json (the default list, niches.json, uses corecraft/pack_spec.py).
Prices are sample figures in USD (the generator converts them); they are flagged as samples on every page built from a pack."""

FAMILY = {}
for _fam, _ids in {
    "home": "plumbing electrician painting ac cleaning solar movers security landscape",
    "auto": "garage courier taxi tyres autosales",
    "project": "carpentry construction tailor welding architect interior marketing photography design printing",
    "retail": "clothing jewellery furniture mobile grocery books gifts petshop optical pharmacy shop",
    "food": "restaurant cafe",
    "food_order": "bakery sweets icecream",
    "clinic": "dental clinic ayurveda physio vet skin eye",
    "session": "salon spa tattoo mehendi gym yoga sports gaming",
    "pro": "law accounting insurance consulting recruitment astrology visa",
    "edu": "school playschool driving music robotics pottery",
    "events": "events tenthouse catering",
    "stay": "travel hotel coworking",
    "property": "realestate",
    "nonprofit": "ngo",
    "software": "software",
}.items():
    for _i in _ids.split():
        FAMILY[_i] = _fam

# three plans per family: (USD price, period). A type with no prices of its own (see PRICES) gets its family's ladder.
FAMILY_PRICES = {
    "home": [(8, "/visit"), (25, "/job"), (60, "/project")], "auto": [(6, "/check"), (20, "/service"), (60, "/full service")],
    "project": [(0, "/consultation"), (120, "/small project"), (400, "/full project")], "retail": [(5, "/item"), (20, "/gift set"), (50, "/bundle")],
    "food": [(4, "/main course"), (8, "/combo"), (25, "/family table")], "food_order": [(3, "/small order"), (10, "/party box"), (30, "/celebration order")],
    "clinic": [(5, "/consultation"), (15, "/checkup"), (40, "/care plan")], "session": [(5, "/session"), (30, "/month"), (80, "/quarter")],
    "pro": [(0, "/consultation"), (40, "/review"), (150, "/full support")], "edu": [(12, "/month"), (30, "/month"), (80, "/term")],
    "events": [(150, "/event"), (500, "/wedding"), (1500, "/large wedding")], "stay": [(20, "/night"), (90, "/weekend"), (200, "/week")],
    "property": [(0, "/consultation"), (30, "/property search"), (80, "/full service")], "nonprofit": [(2, "/month"), (10, "/month"), (30, "/month")],
    "software": [(9, "/month"), (29, "/month"), (79, "/month")],
}

# types whose family ladder does not fit (sample figures)
PRICES = {
    "garage": [(8, "/check"), (35, "/car service"), (90, "/full service")], "tyres": [(5, "/alignment"), (40, "/tyre"), (90, "/battery")],
    "autosales": [(0, "/test ride"), (20, "/inspection"), (50, "/paperwork support")], "spa": [(12, "/massage"), (30, "/spa ritual"), (70, "/day package")],
    "gaming": [(2, "/hour"), (15, "/month pass"), (40, "/party slot")], "petshop": [(3, "/treat pack"), (15, "/food bag"), (40, "/starter kit")],
    "optical": [(0, "/eye test"), (25, "/frame and lenses"), (80, "/premium lenses")], "eye": [(5, "/eye test"), (15, "/consultation"), (60, "/care plan")],
    "consulting": [(0, "/consultation"), (150, "/assessment"), (500, "/project")], "design": [(40, "/logo"), (150, "/brand kit"), (400, "/project")],
    "welding": [(15, "/repair"), (120, "/gate"), (350, "/shed")], "construction": [(0, "/site visit"), (300, "/design stage"), (1200, "/renovation")],
    "pottery": [(10, "/class"), (30, "/month"), (80, "/term")], "robotics": [(15, "/workshop"), (40, "/month"), (100, "/term")],
    "tenthouse": [(60, "/small setup"), (200, "/party setup"), (600, "/wedding setup")], "salon": [(4, "/cut"), (12, "/colour"), (25, "/spa treatment")],
    "grocery": [(3, "/small order"), (20, "/weekly order"), (50, "/family order")], "pharmacy": [(0, "/delivery"), (5, "/refill plan"), (15, "/family plan")],
    "sweets": [(5, "/box"), (15, "/festive box"), (40, "/large order")], "icecream": [(2, "/scoop"), (5, "/shake"), (15, "/party tub")],
    "photography": [(60, "/shoot"), (250, "/event"), (600, "/wedding")], "mehendi": [(15, "/simple design"), (60, "/party look"), (150, "/bridal look")],
    "astrology": [(5, "/question"), (20, "/chart reading"), (50, "/full consultation")],
}

# the page mood of a family (type packs; a niche pack uses the mood of its business type)
FAMILY_MOOD = {"home": "friendly", "auto": "bold", "project": "elegant", "retail": "playful", "food": "warm", "food_order": "warm", "clinic": "calm", "session": "elegant",
               "pro": "calm", "edu": "friendly", "events": "elegant", "stay": "warm", "property": "elegant", "nonprofit": "warm", "software": "cool"}

# a word that ties an offering many trades share to this trade ("Repairs" -> "AC Repairs", "Consultations" -> "Skin Consultations")
QUALIFIER = {
    "dental": "Dental", "clinic": "Health", "ayurveda": "Ayurvedic", "physio": "Physio", "salon": "Salon", "spa": "Spa", "vet": "Pet", "law": "Legal", "accounting": "Tax",
    "architect": "Architectural", "interior": "Interior", "realestate": "Property", "insurance": "Insurance", "marketing": "Marketing", "consulting": "Business", "recruitment": "Hiring",
    "coworking": "Office", "plumbing": "Plumbing", "electrician": "Electrical", "painting": "Paint", "carpentry": "Wood", "ac": "AC", "cleaning": "Cleaning", "construction": "Building",
    "solar": "Solar", "movers": "Moving", "garage": "Car", "courier": "Courier", "landscape": "Garden", "clothing": "Fashion", "jewellery": "Jewellery", "furniture": "Furniture",
    "mobile": "Phone", "grocery": "Grocery", "books": "Book", "gifts": "Gift", "petshop": "Pet", "optical": "Optical", "pharmacy": "Pharmacy", "shop": "Online", "restaurant": "House",
    "cafe": "Cafe", "bakery": "Custom", "sweets": "Mithai", "catering": "Catering", "school": "Coaching", "playschool": "Preschool", "driving": "Driving", "music": "Music",
    "photography": "Photo", "design": "Design", "printing": "Print", "events": "Event", "travel": "Travel", "hotel": "Hotel", "taxi": "Cab", "tattoo": "Tattoo", "gaming": "Gaming",
    "icecream": "Ice Cream", "security": "Security", "mehendi": "Mehendi", "tailor": "Tailoring", "astrology": "Astrology", "visa": "Visa", "tenthouse": "Rental", "welding": "Metal",
    "tyres": "Tyre", "sports": "Sports", "gym": "Gym", "yoga": "Yoga", "software": "Software", "ngo": "Community", "autosales": "Vehicle", "robotics": "Robotics", "pottery": "Pottery",
    "skin": "Skin", "eye": "Eye",
}
