"""Extra matcher vocabulary added on top of each niche's own lists (applied by niches.load_all()).

Found by running blind client-style prompts through the matcher: Roman-letter Hindi (kheton, kitaabon, dant), short plain phrases ("teeth cleaning",
"puppies for sale"), plural forms, and a few businesses that sound like a niche but are not ("shipyard", "ski resort", honey farm).
{niche_id: {"strong": (...), "weak": (...), "avoid": (...)}}. Keep entries specific: a bare generic word here would summon the wrong niche.
"""
EXTRA = {
    "agriculture-farm": {"weak": ("kheti", "kheton", "fasal", "crop field", "crops"), "avoid": ("madhumakkhi", "honey", "beekeeping", "मधुमक्खी", "शहद")},
    "bike-showroom": {"weak": ("motorbikes", "bikes", "motorcycles")},
    "car-showroom": {"avoid": ("motorbike", "motorbikes", "motorcycle", "motorcycles", "scooter", "two wheeler", "दोपहिया", "दुपहिया")},
    "event-party": {"avoid": ("hot air balloon", "hot air balloons", "balloon ride", "air balloon", "गर्म हवा के गुब्बारे")},
    "barber": {"strong": ("gents haircut", "gents hair cut", "mens haircut", "men's haircut", "gents hair")},
    "bookstore": {"strong": ("kitaabon ki dukaan", "kitabon ki dukaan", "kitaab ki dukaan", "book shop")},
    "cafe": {"weak": ("cappuccino", "croissant", "latte", "espresso")},
    "car-wash": {"strong": ("car washing", "car washing service", "vehicle washing")},
    "catering": {"strong": ("banquet table", "chafing dishes")},
    "cleaning": {"weak": ("mopping", "mop", "spray bottles", "housekeeping", "cleaner in uniform", "sweeping")},
    "coaching-tuition": {"weak": ("equation", "jee", "neet", "teacher explains")},
    "consulting": {"strong": ("business consultants", "management consultants", "business consulting")},
    "dental": {"strong": ("teeth cleaning", "dant ke doctor", "dant doctor"), "weak": ("teeth", "dant", "dantaon")},
    "digital-agency": {"weak": ("campaign", "campaign mockups", "brainstorming", "social media campaign")},
    "fashion-boutique": {"strong": ("designer wear", "ladies designer wear", "designer kapde", "designer kapdon"), "weak": ("designer", "kapdon", "kapde")},
    "hotel": {"avoid": ("ski", "snowy slopes", "skiing")},
    "logistics": {"avoid": ("vessel", "shipyard", "ship yard", "shipbuilding")},
    "petshop": {"strong": ("puppies for sale", "pups for sale", "aquarium shop", "aquarium store", "aquarium ki dukaan", "ornamental fish", "fish tank shop", "एक्वेरियम की दुकान"),
               "weak": ("puppies", "puppy", "kittens")},
    "restaurant": {"weak": ("dining hall", "khane", "khana", "dining")},
    "skin-clinic": {"strong": ("glow treatment", "facial and glow"), "weak": ("facial", "glow")},
}


# Words that separate the niches added for the client's picture spec from the older neighbours that already claimed them (found by running the
# spec's training captions through the keyword matcher; the held-out spec prompts were not used).
EXTRA_SPEC = {
    "farm-stay": {"strong": ("farm stay", "farmstay", "homestay", "home stay", "village stay", "rural stay", "farmhouse stay", "फार्म स्टे", "होमस्टे")},
    "agriculture-farm": {"avoid": ("farm stay", "farmstay", "homestay", "home stay", "फार्म स्टे", "होमस्टे")},
    "hotel": {"avoid": ("homestay", "home stay", "farm stay", "pg", "paying guest", "hostel")},
    "tiffin-service": {"strong": ("tiffin", "tiffin box", "dabba service", "dabba", "meal subscription", "lunch box delivery", "टिफिन", "डब्बा सर्विस")},
    "catering": {"avoid": ("tiffin", "टिफिन")},
    "indian-thali": {"avoid": ("tiffin", "टिफिन")},
    "banquet-hall": {"strong": ("banquet hall", "banquet", "function hall", "marriage hall", "party hall", "wedding venue", "venue booking", "बैंक्वेट हॉल", "मैरिज हॉल")},
    "wedding": {"avoid": ("banquet hall", "function hall", "party hall", "venue booking", "बैंक्वेट हॉल")},
    "bike-garage": {"strong": ("bike garage", "bike repair", "scooter repair", "two wheeler garage", "bike service", "scooter service", "bike and scooter garage", "बाइक गैराज")},
    "car-repair": {"avoid": ("bike garage", "bike repair", "scooter", "two wheeler", "motorcycle", "बाइक गैराज")},
    "drone-photography": {"strong": ("drone photography", "drone shoot", "drone videography", "aerial photography", "aerial videography", "drone", "drone operator", "ड्रोन")},
    "photography": {"avoid": ("drone", "aerial", "ड्रोन")},
    "dj-sound": {"strong": ("dj", "dj sound", "dj and sound", "dj setup", "dj night", "sound and light", "wedding dj", "डीजे")},
    "event-party": {"avoid": ("dj sound", "dj and sound", "wedding dj", "डीजे")},
    "nutritionist": {"strong": ("dietitian", "nutritionist", "diet plan", "diet chart", "weight loss diet", "nutrition consultant", "डाइटीशियन", "आहार योजना")},
    "clinic-doctor": {"avoid": ("dietitian", "nutritionist", "diet plan", "diet chart", "डाइटीशियन")},
    "bridal-makeup": {"strong": ("bridal makeup", "bridal makeup artist", "makeup artist", "bridal artist", "bride makeup", "दुल्हन मेकअप", "ब्राइडल मेकअप")},
    "salon": {"avoid": ("bridal makeup", "makeup artist", "bridal artist", "ब्राइडल मेकअप")},
    "mobile-repair": {"strong": ("mobile repair", "phone repair", "screen replacement", "mobile service centre", "mobile service center", "phone screen repair", "मोबाइल रिपेयर")},
    "mobile-store": {"avoid": ("mobile repair", "phone repair", "screen replacement", "मोबाइल रिपेयर")},
    "car-rental": {"strong": ("car rental", "self drive", "self-drive", "rent a car", "car hire", "car on rent", "cars on rent", "कार रेंटल")},
    "taxi": {"avoid": ("car rental", "self drive", "self-drive", "rent a car", "car hire", "car on rent", "cars on rent", "कार रेंटल")},
    "loan-finance": {"strong": ("loan agent", "loan advisor", "home loan", "personal loan", "business loan", "loan against property", "loan consultant", "लोन एजेंट")},
    "insurance": {"avoid": ("loan agent", "loan advisor", "home loan", "personal loan", "business loan", "लोन एजेंट")},
    "accounting-finance": {"avoid": ("loan agent", "loan advisor", "home loan", "personal loan", "business loan")},
    "pg-hostel": {"strong": ("pg", "pg accommodation", "paying guest", "hostel", "student hostel", "girls hostel", "boys hostel", "पीजी", "हॉस्टल")},
    "cloud-kitchen": {"strong": ("cloud kitchen", "ghost kitchen", "delivery kitchen", "online food kitchen", "क्लाउड किचन")},
    "restaurant": {"avoid": ("cloud kitchen", "ghost kitchen", "क्लाउड किचन")},
    "fast-food": {"avoid": ("cloud kitchen", "ghost kitchen")},
    "scrap-recycling": {"strong": ("scrap", "scrap dealer", "kabadi", "recycling", "scrap recycling", "waste recycling", "कबाड़ी", "रीसाइक्लिंग")},
    "animal-welfare": {"strong": ("animal welfare", "animal rescue", "stray animals", "dog shelter", "animal shelter", "pashu seva", "पशु सेवा")},
    "ngo": {"avoid": ("animal welfare", "animal rescue", "stray animals", "dog shelter", "animal shelter")},
    "temple": {"strong": ("temple trust", "mandir", "temple", "dharamshala", "annadaan", "मंदिर", "मंदिर ट्रस्ट")},
    "counselling": {"strong": ("counselling", "counselling centre", "therapy practice", "therapist", "mental health counselling", "काउंसलिंग")},
    "funeral-services": {"strong": ("funeral", "funeral services", "last rites", "antim sanskar", "अंतिम संस्कार")},
    "pest-control": {"strong": ("pest control", "termite treatment", "cockroach control", "deemak", "पेस्ट कंट्रोल", "दीमक")},
    "laundry": {"strong": ("laundry", "dry cleaning", "dry cleaner", "ironing service", "धुलाई और प्रेस")},
    "cleaning": {"avoid": ("laundry", "dry cleaning", "dry cleaner")},
    "water-purifier": {"strong": ("water purifier", "ro service", "ro purifier", "water filter service", "वाटर प्यूरीफायर")},
    "plumbing": {"avoid": ("water purifier", "ro service", "ro purifier")},
    "video-editing": {"strong": ("video editing", "video editor", "post production", "reel editing", "video edit", "वीडियो एडिटिंग")},
    "gift-shop": {"strong": ("gift shop", "gift store", "gift hamper", "gift items", "return gifts", "गिफ्ट शॉप")},
    "diagnostic-lab": {"strong": ("diagnostic lab", "pathology lab", "blood test", "lab tests", "diagnostic centre", "diagnostic center", "पैथोलॉजी लैब")},
    "notary-documents": {"strong": ("notary", "notary public", "documentation service", "affidavit", "stamp paper", "नोटरी", "एफिडेविट")},
}


def apply(niches):
    for nid, extra in list(EXTRA.items()) + list(EXTRA_SPEC.items()):
        n = niches.get(nid)
        if n is None:
            raise KeyError("vocab for unknown niche %s" % nid)
        for field in ("strong", "weak", "avoid"):
            add = tuple(w for w in extra.get(field, ()) if w not in getattr(n, field))
            if add:
                setattr(n, field, getattr(n, field) + add)
