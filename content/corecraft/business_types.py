"""Business-type taxonomy and prompt parsing (stdlib: re only).

A type says what a business is (label, keywords in English / Hinglish / Devanagari), which copy family
('niche' = kind of frames in template_data) it uses, and which plural offerings it typically sells.
Offerings listed here are TYPICAL for the type, not facts about the user's business, so the engine
flags them for review (content['needs_review']); anything the user names in the prompt wins.
"""
import re

# id: (label, niche, keywords, offerings, customers, (cta1, cta2), mood)
T = {}


def add(tid, label, niche, keys, offers, people, ctas, mood):
    T[tid] = {"id": tid, "label": label, "niche": niche, "keys": keys.split(","), "offers": offers.split() if offers else None,
              "people": people, "ctas": ctas, "mood": mood}


# ---- care & wellbeing --------------------------------------------------------------------------------------
add("dental", "Dental Clinic", "care", "dental,dentist,dentistry,teeth,tooth,orthodont,root canal,braces,दांत,डेंटल,दंत", "check-ups cleanings whitening braces aligners fillings implants crowns extractions dentures", "patients", ("Book an Appointment", "Call the Clinic"), "calm")
add("clinic", "Medical Clinic", "care", "clinic,doctor,hospital,nursing home,polyclinic,medical centre,medical center,diagnostic,pathology,health centre,क्लिनिक,डॉक्टर,अस्पताल,अस्पताल", "consultations check-ups tests screenings vaccinations treatments follow-ups", "patients", ("Book an Appointment", "Call the Clinic"), "calm")
add("ayurveda", "Ayurvedic Clinic", "care", "ayurved,ayurveda,ayurvedic,panchakarma,herbal,naturopath,homeopath,homeopathy,आयुर्वेद", "consultations therapies massages treatments remedies programs", "patients", ("Book a Consultation", "Call the Clinic"), "friendly")
add("physio", "Physiotherapy Centre", "care", "physio,physiotherapy,physiotherapist,rehab,rehabilitation,chiropract,फिजियो", "sessions assessments exercises treatments programs", "patients", ("Book a Session", "Call the Centre"), "calm")
add("salon", "Hair & Beauty Salon", "care", "salon,parlour,parlor,beauty,barber,makeup,unisex,hair,सैलून,पार्लर,ब्यूटी", "haircuts colouring facials manicures pedicures waxing treatments makeovers", "clients", ("Book an Appointment", "Call the Salon"), "playful")
add("spa", "Spa & Wellness Centre", "care", "spa,massage,wellness centre,wellness center,स्पा,मसाज", "massages facials therapies treatments packages rituals", "guests", ("Book a Treatment", "Call the Spa"), "elegant")
add("vet", "Veterinary Clinic", "care", "vet,veterinary,animal hospital,pet clinic,पशु", "check-ups vaccinations grooming treatments consultations", "pet owners", ("Book a Visit", "Call the Clinic"), "friendly")

# ---- professional services ---------------------------------------------------------------------------------
add("law", "Law Firm", "pro", "law firm,lawyer,advocate,attorney,legal,vakil,litigation,वकील,कानूनी", "consultations agreements filings opinions representations", "clients", ("Book a Consultation", "Call the Firm"), "calm")
add("accounting", "Accounting Firm", "pro", "accounting,accountant,chartered accountant,ca firm,gst,income tax,audit,bookkeeping,taxation,tax filing,लेखा", "returns filings audits registrations statements reports consultations", "clients", ("Book a Consultation", "Get a Quote"), "calm")
add("architect", "Architecture Studio", "pro", "architect,architecture,architectural,आर्किटेक्ट", "designs plans drawings layouts renderings consultations", "clients", ("Book a Consultation", "See Our Work"), "elegant")
add("interior", "Interior Design Studio", "pro", "interior,decorator,home decor,furnishing,इंटीरियर", "designs layouts renovations makeovers consultations", "homeowners", ("Book a Consultation", "See Our Work"), "elegant")
add("realestate", "Real Estate Agency", "pro", "real estate,property,broker,realtor,flats,villas,plots,apartments,प्रॉपर्टी,रियल एस्टेट", "flats villas plots apartments rentals listings", "buyers", ("View Listings", "Talk to an Agent"), "calm")
add("insurance", "Insurance & Finance Advisor", "pro", "insurance,loan,mutual fund,financial advisor,wealth,investment advisor,बीमा", "plans policies loans investments consultations", "families", ("Get a Quote", "Talk to an Advisor"), "calm")
add("marketing", "Digital Marketing Agency", "pro", "digital marketing,marketing agency,seo,social media,advertising,branding agency,ad agency", "campaigns strategies audits reports websites ads", "businesses", ("Get a Free Audit", "Talk to Us"), "bold")
add("consulting", "Consulting Firm", "pro", "consulting,consultant,advisory,management consultancy,business setup", "strategies audits workshops reports consultations plans", "businesses", ("Book a Consultation", "Get a Quote"), "calm")
add("recruitment", "Recruitment Agency", "pro", "recruitment,staffing,placement,manpower,hiring agency,hr consultancy,hr agency,hiring,job consultancy", "placements interviews listings roles shortlists", "employers", ("Hire Talent", "Find a Job"), "calm")
add("coworking", "Coworking Space", "pro", "coworking,co-working,shared office,office space,cowork", "desks cabins rooms passes memberships events", "members", ("Book a Tour", "See Plans"), "cool")

# ---- home, vehicle & field services ------------------------------------------------------------------------
add("plumbing", "Plumbing Service", "business", "plumb,plumber,plumbing,pipe,drain,नल", "repairs installations inspections estimates appointments pipes drains faucets heaters fixtures upgrades packages", "homeowners", ("Get a Free Quote", "Call Now"), "calm")
add("electrician", "Electrical Service", "business", "electrician,electrical,wiring,electric,बिजली,इलेक्ट्रीशियन", "repairs installations inspections upgrades fixtures estimates", "homeowners", ("Get a Free Quote", "Call Now"), "calm")
add("painting", "Painting Service", "business", "painter,painting,paint,whitewash,पेंट", "repaints coatings finishes textures estimates", "homeowners", ("Get a Free Quote", "Call Now"), "playful")
add("carpentry", "Carpentry & Woodwork", "business", "carpenter,carpentry,woodwork,modular kitchen,wardrobe", "cabinets wardrobes kitchens fittings repairs designs", "homeowners", ("Get a Free Quote", "See Our Work"), "warm")
add("ac", "AC & Appliance Repair", "business", "ac repair,air conditioner,hvac,refrigerator,appliance,washing machine", "repairs installations inspections replacements checkups", "homeowners", ("Book a Visit", "Call Now"), "cool")
add("cleaning", "Cleaning & Pest Control", "business", "cleaning,pest control,pest,housekeeping,maid,disinfection,sanitiz,laundry,dry clean,सफाई", "cleanups inspections treatments packages appointments", "homeowners", ("Get a Free Quote", "Book a Visit"), "friendly")
add("construction", "Construction Company", "business", "construction,builder,contractor,civil,renovation,building contractor,निर्माण,बिल्डर", "homes renovations extensions estimates inspections projects", "homeowners", ("Get a Free Quote", "See Projects"), "bold")
add("solar", "Solar Installation", "business", "solar,solar panel,rooftop solar,सोलर", "installations inspections upgrades estimates packages systems", "homeowners", ("Get a Free Quote", "Book a Site Visit"), "cool")
add("movers", "Packers & Movers", "business", "packers,movers,shifting,relocation,पैकर्स", "moves packages estimates inspections quotes", "families", ("Get a Free Quote", "Call Now"), "bold")
add("garage", "Car Repair Garage", "business", "garage,car repair,mechanic,automobile,car wash,car detailing,bike service,bike repair,two wheeler,scooter,car service,गैराज,गाड़ी", "repairs inspections replacements checkups upgrades packages washes", "drivers", ("Book a Service", "Call Now"), "bold")
add("courier", "Courier & Logistics", "business", "courier,logistics,delivery service,shipping,cargo,transport,कूरियर", "deliveries shipments pickups packages quotes", "senders", ("Get a Quote", "Track a Parcel"), "bold")
add("landscape", "Garden & Lawn Care", "business", "lawn,garden,landscap,nursery,माली", "lawns installations upgrades estimates appointments", "homeowners", ("Get a Free Quote", "Call Now"), "friendly")

# ---- retail ------------------------------------------------------------------------------------------------
add("clothing", "Clothing Boutique", "shop", "clothing,clothes,uniform,uniforms,fashion boutique,clothing boutique,fashion,apparel,garment,kapde,kapda,showroom~,saree,कपड़े,बुटीक,फैशन", "dresses jackets scarves sweaters shirts suits sarees kurtas jeans accessories bags", "shoppers", ("Shop Now", "Visit the Store"), "playful")
add("jewellery", "Jewellery Store", "shop", "jewel,jewelry,jewellery,ornament,gold,diamond,ज्वेलरी,गहने", "rings necklaces bracelets earrings pendants bangles watches chains charms studs", "shoppers", ("Shop Now", "Visit the Store"), "elegant")
add("furniture", "Furniture Showroom", "store", "furniture,sofa,sofas,bed frames,फर्नीचर", "sofas beds tables chairs wardrobes cabinets shelves desks", "shoppers", ("Visit the Showroom", "Get a Quote"), "warm")
add("mobile", "Mobile & Electronics Store", "store", "mobile~,phone~,laptop,electronics,gadget,smartphone,mobile phone,mobile shop,mobile store,phone shop,phone repair,मोबाइल", "phones accessories chargers earphones cases covers repairs", "shoppers", ("Shop Now", "Visit the Store"), "cool")
add("grocery", "Grocery Store", "store", "organic,farm,grocery,vegetables,fruits,kirana,dairy,milk,किराना,जैविक", "vegetables fruits grains pulses spices snacks", "families", ("Order Now", "Visit the Store"), "friendly")
add("books", "Bookstore & Stationery", "store", "bookstore,book shop,stationery,books,पुस्तक,स्टेशनरी", "books notebooks pens supplies gifts", "readers", ("Shop Now", "Visit the Store"), "friendly")
add("gifts", "Gift & Flower Shop", "shop", "florist,flower,gift shop,bouquet,gifts,फूल", "bouquets gifts hampers arrangements plants", "shoppers", ("Order Now", "Visit the Store"), "playful")
add("petshop", "Pet Shop", "store", "pet shop,pet store,pet supplies,dog food,pet,dog grooming", "toys collars treats leashes beds supplies", "pet owners", ("Shop Now", "Visit the Store"), "friendly")
add("optical", "Optical Store", "store", "optician,optical,eyeglasses,spectacles,contact lenses,eyewear,चश्मा", "frames lenses eyeglasses sunglasses", "shoppers", ("Book an Eye Test", "Visit the Store"), "cool")
add("pharmacy", "Pharmacy", "store", "pharmacy,chemist,medical store,medicines,दवाई,मेडिकल", "medicines vitamins supplements essentials", "customers", ("Order Medicines", "Visit the Store"), "calm")
add("shop", "Online Store", "shop", "shop~,store~,boutique~,ecommerce,e-commerce,online store,dukaan~,दुकान~,handmade~,gift~", "collections gifts sets bundles pieces accessories essentials favourites", "shoppers", ("Shop Now", "Browse Collection"), "playful")

# ---- food --------------------------------------------------------------------------------------------------
add("restaurant", "Restaurant", "restaurant", "restaurant,dhaba,bistro,diner,eatery,food court,रेस्टोरेंट,ढाबा,pizza,burger", None, "guests", ("Reserve a Table", "View the Menu"), "warm")
add("cafe", "Café", "restaurant", "cafe,café,coffee,tea,chai,कैफे,चाय", None, "guests", ("Visit Us", "View the Menu"), "warm")
add("bakery", "Bakery", "restaurant", "bakery,cake,cakes,pastry,pastries,birthday cake,बेकरी,केक", "cakes pastries cookies muffins bagels doughnuts breads brownies cupcakes", "guests", ("Order a Cake", "View the Menu"), "warm")
add("sweets", "Sweet Shop", "restaurant", "mithai,sweets,sweet shop,halwai,मिठाई", "sweets laddoos barfis snacks hampers boxes", "families", ("Order Now", "Visit the Shop"), "warm")
add("catering", "Catering Service", "restaurant", "catering,caterer,tiffin,cloud kitchen,meal service,केटरिंग", "menus platters packages parties thalis", "hosts", ("Get a Quote", "View Menus"), "warm")

# ---- learning ----------------------------------------------------------------------------------------------
add("school", "Coaching & Tuition Centre", "education", "school,coaching,tuition,tutor,academy~,institute~,classes,class 10,class 12,study,कोचिंग,स्कूल,ट्यूशन", "classes lessons workshops tutorials quizzes exams assignments worksheets chapters batches", "students", ("Enroll Now", "Book a Free Demo"), "friendly")
add("playschool", "Play School & Daycare", "education", "play school,playschool,preschool,daycare,nursery school,kindergarten,creche,प्लेस्कूल", "classes activities crafts stories games", "parents", ("Book a Visit", "Call the School"), "playful")
add("driving", "Driving School", "education", "driving school,driving,learner licence,driving licence,ड्राइविंग", "lessons sessions packages tests", "learners", ("Book a Lesson", "Call Now"), "bold")
add("music", "Music & Dance Academy", "education", "music class,dance class,guitar,piano,dance academy,singing,संगीत", "classes lessons workshops recitals", "students", ("Book a Trial Class", "Call Now"), "playful")

# ---- creative & events -------------------------------------------------------------------------------------
add("photography", "Photography Studio", "portfolio", "photograph,photo studio,pre-wedding,videograph,फोटोग्राफी,फोटो", "photos albums galleries shoots prints portraits frames edits sessions videos films", "clients", ("Book a Shoot", "See Our Work"), "elegant")
add("design", "Design Studio", "portfolio", "designer,graphic design,logo design,brand design,logo,branding studio,branding,illustrat,डिजाइन", "logos designs illustrations sketches posters packaging projects mockups", "clients", ("Start a Project", "See Our Work"), "elegant")
add("printing", "Printing Studio", "portfolio", "printing,print shop,flex,banner,visiting card,प्रिंटिंग", "prints banners cards brochures stickers invitations", "clients", ("Get a Quote", "See Samples"), "bold")
add("events", "Event Planning", "hosting", "wedding planner,event management,event planner,decorator,dj,party planner,wedding,शादी,इवेंट", "weddings parties events decorations setups shows", "hosts", ("Plan My Event", "See Our Work"), "playful")

# ---- travel & hospitality ----------------------------------------------------------------------------------
add("travel", "Travel Agency", "hosting", "travel,tour,tours,holiday,tourism,trip,ट्रैवल,टूर", "tours packages itineraries bookings trips getaways", "travellers", ("Plan My Trip", "Get a Quote"), "friendly")
add("hotel", "Hotel & Stay", "hosting", "hotel,resort,homestay,guest house,lodge,hostel,pg accommodation,accommodation,dormitory,होटल,रिसॉर्ट", "rooms suites stays packages experiences", "guests", ("Check Availability", "Call Us"), "warm")
add("taxi", "Cab & Taxi Service", "hosting", "taxi,cab,car rental,bike rental,vehicle rental,rickshaw,chauffeur,cab booking,टैक्सी", "rides transfers trips rentals tours packages", "travellers", ("Book a Ride", "Call Now"), "bold")

add("tattoo", "Tattoo Studio", "care", "tattoo,piercing,body art,टैटू", "tattoos piercings designs cover-ups touch-ups consultations sketches stencils aftercare-kits flash-sheets", "clients", ("Book a Session", "See Our Work"), "bold")
add("gaming", "Gaming Zone", "hosting", "gaming cafe,gaming,game zone,esports,ps5,arcade,video games,गेमिंग", "games consoles tournaments sessions memberships parties snacks controllers headsets leagues", "players", ("Book a Slot", "See Pricing"), "bold")
add("icecream", "Ice Cream Parlour", "restaurant", "ice cream,icecream,gelato,sundae,kulfi,आइसक्रीम", "scoops sundaes shakes cones sticks waffles toppings flavours kulfis falooda", "guests", ("Visit Us", "View the Menu"), "playful")

add("security", "Security Systems", "business", "cctv,security system,security systems,alarm,surveillance,access control,सीसीटीवी", "installations cameras alarms upgrades inspections systems recorders sensors", "homeowners", ("Get a Free Quote", "Book a Site Visit"), "cool")
add("mehendi", "Mehendi & Bridal Artist", "care", "mehendi,mehndi,henna,bridal makeup,bridal artist,मेहंदी", "designs bridal-looks party-looks patterns consultations trials hairstyles nail-art makeovers saree-drapes", "clients", ("Book a Date", "See Our Work"), "playful")
add("tailor", "Tailoring & Alterations", "business", "tailor,tailoring,stitching,alterations,boutique tailor,दर्ज़ी,सिलाई", "stitching alterations blouses suits kurtas uniforms fittings sarees lehengas shirts trousers", "customers", ("Book a Fitting", "Call Now"), "elegant")
add("astrology", "Astrology & Guidance", "pro", "astrologer,astrology,horoscope,vastu,tarot,ज्योतिष,वास्तु", "readings consultations charts remedies reports predictions matchings muhurats guidances", "clients", ("Book a Reading", "Call Now"), "calm")
add("visa", "Visa & Immigration Consultants", "pro", "visa,visa consultant,visa consultancy,visa services,immigration,study abroad,passport,overseas education", "applications documents interviews consultations checklists slots visas forms statements guides", "applicants", ("Book a Consultation", "Check Eligibility"), "calm")
add("tenthouse", "Tent House & Rentals", "hosting", "tent house,rental~,sound system,light rental,furniture rental,stage rental,कैटरिंग टेंट", "tents stages lights speakers chairs tables setups carpets mandaps", "hosts", ("Get a Quote", "Check Availability"), "bold")
add("welding", "Fabrication & Welding", "business", "welding,fabrication,steel,metal work,gates,grills,workshop", "gates grills railings frames repairs installations designs sheds staircases", "customers", ("Get a Free Quote", "Call Now"), "bold")
add("tyres", "Tyre & Auto Accessories", "business", "tyre,tire,wheel alignment,auto accessories,car accessories,battery shop", "tyres batteries alignments accessories upgrades replacements wheels rims wipers", "drivers", ("Book a Service", "Call Now"), "bold")

# ---- fitness, tech, community ------------------------------------------------------------------------------
add("sports", "Sports Academy", "fitness", "cricket,football,badminton,tennis,swimming,cricket coaching,football coaching,badminton coaching,tennis coaching,swimming classes,swimming coaching,sports academy,sports coaching,karate,martial arts,skating,क्रिकेट", "batches sessions drills matches camps tournaments nets fitness-tests", "players", ("Join a Batch", "Book a Trial"), "bold")
add("gym", "Gym & Fitness Studio", "fitness", "gym,fitness,workout,trainer,crossfit,zumba,जिम,फिटनेस", None, "members", ("Start Free Trial", "Book a Session"), "bold")
add("yoga", "Yoga Studio", "fitness", "yoga,meditation,retreat,pilates,teacher training,योग,ध्यान", "classes sessions stretches routines retreats workshops meditations programs", "students", ("Book a Class", "View the Schedule"), "friendly")
add("software", "Software Company", "tech", "software,saas,app,startup,developer,it consulting,it company,web development,app development,mobile app,website development,cloud,api,platform,tech,सॉफ्टवेयर", None, "teams", ("Get Started", "Request a Demo"), "cool")
add("ngo", "Non-profit Organisation", "org", "ngo,charity,foundation,trust,donation,nonprofit,non-profit,social work,एनजीओ,दान,फाउंडेशन", "programs drives campaigns events workshops", "supporters", ("Donate Now", "Volunteer"), "friendly")

# more typical offerings, appended so every type has a pool wide enough for a full page
_MORE = {
    "clinic": "referrals prescriptions reports", "ayurveda": "diets massages detox-plans", "physio": "assessments stretches rehabilitation-plans",
    "salon": "haircuts styling treatments packages", "spa": "scrubs wraps packages gift-vouchers", "vet": "vaccinations screenings treatments boarding",
    "law": "notices petitions appeals contracts documents hearings", "accounting": "invoices payrolls ledgers statements consultations",
    "architect": "elevations models approvals site-visits", "interior": "mood-boards estimates furnishings makeovers", "realestate": "rentals site-visits valuations documents homes",
    "insurance": "claims renewals policies covers premiums riders", "marketing": "posts videos newsletters landing-pages", "consulting": "assessments roadmaps trainings",
    "recruitment": "candidates openings referrals contracts", "coworking": "workstations lounges meeting-rooms day-passes", "electrician": "wiring switches lights panels",
    "painting": "interiors exteriors waterproofing touch-ups", "carpentry": "doors shelves beds tables", "ac": "services gas-refills cleanings parts",
    "cleaning": "deep-cleans sanitisations floors kitchens", "construction": "plans permits foundations finishes", "solar": "panels batteries maintenance-plans",
    "movers": "boxes vehicles storage-plans", "garage": "services tyres batteries detailing", "courier": "tracking returns documents parcels",
    "landscape": "plants trims gardens maintenance-plans", "furniture": "mattresses dining-sets", "mobile": "screen-guards batteries upgrades",
    "grocery": "eggs juices staples", "books": "diaries textbooks stories", "gifts": "cards balloons chocolates", "petshop": "foods cages grooming",
    "optical": "lenses contact-lenses eye-tests cases", "pharmacy": "prescriptions devices supplies", "sweets": "festival-boxes namkeen cakes",
    "catering": "buffets desserts live-counters", "playschool": "rhymes outings celebrations", "driving": "licences practice-sessions theory-classes",
    "music": "grades auditions performances", "printing": "posters flyers labels", "events": "invitations stages lighting", "travel": "visas flights hotels cruises",
    "hotel": "restaurants amenities offers", "taxi": "airport-pickups outstation-trips city-rides", "ngo": "donations volunteers scholarships",
}
_MORE2 = {
    "driving": "refreshers renewals road-tests mock-tests", "interior": "kitchens bedrooms living-rooms wardrobes", "movers": "relocations car-transports bike-transports", "music": "instruments batches camps", "optical": "eye-tests cases cleaners prescriptions lens-coatings",
    "pharmacy": "refills prescriptions", "ngo": "fundraisers awareness-camps meal-drives", "ayurveda": "herbs oils diets", "physio": "taping massages posture-checks",
    "vet": "dental-cleanings surgeries nutrition-plans", "coworking": "tours lockers", "landscape": "pots irrigation-systems", "taxi": "chauffeurs day-rentals",
}
for _k, _v in _MORE2.items():
    _MORE[_k] = _MORE.get(_k, "") + " " + _v
for _k, _v in _MORE.items():
    T[_k]["offers"] += [w.replace("-", " ") for w in _v.split() if w.replace("-", " ") not in T[_k]["offers"]]

# process words, not things a business sells: they make poor feature titles ("Our appointments are chosen with care")
_NOT_OFFERINGS = {"appointments", "estimates", "quotes", "bookings", "reviews", "follow-ups", "follow ups", "referrals"}
for _t in T.values():
    if _t["offers"]:
        _t["offers"] = list(dict.fromkeys(w for w in _t["offers"] if w not in _NOT_OFFERINGS))

# words that name WHO a service is for (never offerings)
AUDIENCE = set("women men woman man kids kid children child students student families family homes home offices office businesses business startups sellers seller beginners seniors couples teens girls boys adults everyone professionals companies owners".split())
CITIES = set("""mumbai delhi bangalore bengaluru hyderabad ahmedabad chennai kolkata pune jaipur surat lucknow kanpur nagpur indore bhopal patna vadodara ludhiana agra nashik faridabad meerut rajkot varanasi srinagar amritsar ranchi gurgaon gurugram noida chandigarh coimbatore kochi kerala goa udaipur jodhpur dehradun rishikesh shimla manali mysore mysuru vizag visakhapatnam thane navi london dubai singapore toronto sydney""".split())


def _norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()


TRADE_WORDS = {"supplier", "suppliers", "wholesaler", "trader", "traders", "distributor", "distributors", "manufacturer", "manufacturers"}
HEAD_SPLIT = re.compile(r"\s(?:with|offering|offers|including|for|selling|providing|specializing|specialising|in|at|near|that|which|who|called|named)\s", re.I)


def _score(text, t):
    p = " " + _norm(text) + " "
    score = 0.0
    for k in t["keys"]:
        weak = k.endswith("~")   # modifier words ("boutique hotel") count for less than head nouns
        k = _norm(k.rstrip("~"))
        if not k:
            continue
        hit = (re.search(r"(?<![a-z])" + re.escape(k) + (r"(?![a-z])" if len(k) <= 4 else ""), p) if k.isascii()
               else re.search(r"(?<![\u0900-\u097f])" + re.escape(k), p))   # Devanagari keys match at a word start, so "नल" is not found inside "पैनल"
        if hit:
            score += (0.4 if weak else 1.0) + 0.5 * k.count(" ") + (0.2 if len(k) > 6 else 0)
    return score


def type_scores(prompt):
    """Rule score of every business type for a prompt (keyword hits, the head clause counting extra)."""
    first = re.split(r"[,:;]", prompt, maxsplit=1)[0]   # the first clause says what the business is; later ones list its services
    head = HEAD_SPLIT.split(" " + first + " ", maxsplit=1)[0]
    tail_words = " ".join(head.split()[-2:])   # the head noun of an English noun phrase comes last: "... online store", "... dental clinic"
    last = head.split()[-1].lower().strip(".") if head.split() else ""
    trade = last in TRADE_WORDS   # "... supplier / wholesaler": the business sells goods, whatever the goods are for
    out = {}
    for tid, t in T.items():
        if trade and t["niche"] not in ("shop", "store"):
            out[tid] = 0.0
            continue
        out[tid] = 1.5 * _score(head, t) + _score(prompt, t) + 1.0 * min(_score(tail_words, t), 1.5)
    return out


def detect_type(prompt):
    """Best-matching business type id and its confidence (0 = nothing matched).
    The head clause ("dental clinic" in "dental clinic in Pune offering braces") counts extra, so listed
    extras ("... with rooms, spa and restaurant") do not outvote what the business is."""
    best, best_score = None, 0.0
    for tid, score in type_scores(prompt).items():
        if score > best_score:
            best, best_score = tid, score
    return best, best_score


# ---- prompt parsing ------------------------------------------------------------------------------------------
LEAD = re.compile(r"\b(?:offering|offers|offer|providing|provides|provide|specializ(?:es|ing) in|specialis(?:es|ing) in|including|selling|sells|dealing in|deals in|services? (?:like|such as)|for|with)\b\s+(.+)", re.I)
SPLIT = re.compile(r"\s*(?:,|&|\band\b|\baur\b|/|\+|\sऔर\s)\s*", re.I)
PLACE = re.compile(r"\b(?:in|at|near|based in|from|around)\s+([A-Za-z][A-Za-z .'-]{2,30}?)(?=$|[,.;]|\s+(?:offering|offers|for|with|and|selling|providing|that|who)\b)", re.I)
FILLER = {"our", "the", "best", "all", "your", "a", "an", "good", "quality", "top", "many", "various", "different", "more", "and", "also", "some"}


def _clean_item(x):
    ws = [w for w in re.findall(r"[A-Za-z0-9&'-]+", x) if w.lower() not in FILLER]
    return " ".join(ws)


def parse_prompt(prompt):
    """Facts the user actually stated: place, listed offerings, audience, phone, email, years."""
    facts = {"items": [], "place": None, "audience": None, "phone": None, "email": None, "years": None}
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", prompt)
    if m:
        facts["email"] = m.group(0)
    m = re.search(r"(?<!\d)(\+?\d[\d ()-]{8,16}\d)(?!\d)", prompt)
    if m:
        facts["phone"] = m.group(1).strip()
    m = re.search(r"(\d{1,2})\+?\s*(?:years|yrs|saal|साल)", prompt, re.I) or re.search(r"since\s+(19\d\d|20\d\d)", prompt, re.I)
    if m:
        facts["years"] = m.group(0).strip()
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d ()-]{8,16}\d", " ", prompt)
    for m in PLACE.finditer(text):
        cand = m.group(1).strip(" .")
        low = cand.lower()
        words = low.split()
        if low in CITIES or (cand[:1].isupper() and not set(words) & AUDIENCE) or (words and words[0] in CITIES):
            facts["place"] = " ".join(w.capitalize() if w.islower() else w for w in cand.split())
            break
    # offerings: phrases after trigger words, split on commas / "and"
    items = []
    for m in LEAD.finditer(text):
        tail = re.split(r"[.;\n|!?]", m.group(1), maxsplit=1)[0]   # one sentence only
        tail = re.split(r"\b(?:call|contact|phone|whatsapp|mail|email|e-mail|since|open|timings?|visit)\b", tail, maxsplit=1, flags=re.I)[0]
        tail = re.split(r"\b(?:in|at|near|based in)\b\s+[A-Za-z]", tail, maxsplit=1)[0]
        parts = [_clean_item(p) for p in SPLIT.split(tail)]
        is_aud = lambda p: bool(p) and set(p.lower().split()) <= (AUDIENCE | {"small", "local", "new", "young", "working", "senior", "medium"})
        aud = [p for p in parts if is_aud(p)]
        if aud and not facts["audience"]:
            facts["audience"] = aud[0]
        parts = [p for p in parts if p and 1 <= len(p.split()) <= 4 and not is_aud(p) and re.fullmatch(r"[A-Za-z][A-Za-z0-9&' -]*", p)]
        if m.group(0).lower().split()[0] in ("for", "with") and len(parts) < 2:
            continue   # a bare "for X" / "with X" is usually the audience or a detail, not a list of offerings
        for p in parts:
            if p.lower() not in {i.lower() for i in items} and not (p.lower() in CITIES):
                items.append(p)
    facts["items"] = items[:6]
    return facts


ROLE_WORDS = set("dealer supplier dealers suppliers shop store service services company agency centre center laboratory lab house studio provider manufacturer firm institute".split())
NOISE = set("website site web page services service company business firm my our your online best new good professional top the a an of for in at near with and or to is are i we want need make build create looking provide providing offering offers selling sells based".split())


def fallback_items(prompt, place=None):
    """For a business of unknown type: the noun phrases the user wrote, so the copy is at least about their words."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+|\+?\d[\d ()-]{8,16}\d", " ", prompt)
    chunks, cur = [], []
    for w in re.findall(r"[A-Za-z0-9&'-]+|[,.;]", text):
        if w in ",.;" or w.lower() in NOISE or w.lower() in AUDIENCE or (place and w.lower() in place.lower().split()):
            if cur:
                chunks.append(" ".join(cur))
            cur = []
        else:
            cur.append(w)
    if cur:
        chunks.append(" ".join(cur))
    out = []
    for c in chunks:
        ws = c.split()
        if len(ws) >= 3 and ws[-1].lower() in ROLE_WORDS:   # "Bike Accessories Dealer" -> the offering is "Bike Accessories"
            c = " ".join(ws[:-1])
        if 1 <= len(c.split()) <= 4 and not c.isdigit() and re.search(r"[A-Za-z]{3}", c) and c.lower() not in {o.lower() for o in out}:
            out.append(c)
    return out[:4]


# ---- inferring the copy family of a business that is not in the list ----------------------------------------
KIND_CUES = {
    "care": "clinic hospital therapy therapist wellness healing counselling counseling doctor medical health dental salon parlour parlor spa massage skin hair beauty makeup nail physio क्लिनिक अस्पताल डॉक्टर",
    "pro": "firm consultancy consultant consulting advisor adviser agency lawyer advocate attorney accountant legal tax audit insurance finance broker architect valuer surveyor vastu",
    "business": "repair repairs installation service services maintenance contractor plumber electrician cleaning pest delivery transport mechanic carpenter painter technician laundry packers workshop fitter",
    "store": "grocery pharmacy mart supermarket kirana chemist",
    "shop": "shop store showroom boutique market dealer trader wholesaler supplier outlet bazaar दुकान",
    "restaurant": "restaurant cafe bakery kitchen catering food sweets juice bar dhaba tiffin eatery",
    "education": "school academy classes coaching institute training tutor tuition college course lessons स्कूल कोचिंग",
    "portfolio": "studio photography design art artist film video production print illustration",
    "hosting": "hotel travel tours tour events event wedding rental cab taxi resort stay hostel gaming homestay",
    "fitness": "gym yoga fitness sports dance martial swimming crossfit जिम योग",
    "tech": "software app saas web digital cloud ai startup platform developer developers",
    "org": "ngo foundation trust charity society association community club एनजीओ",
}
CUE_PRIORITY = ["org", "tech", "care", "pro", "education", "fitness", "restaurant", "hosting", "portfolio", "store", "shop", "business"]


def infer_kind(prompt):
    """(copy family, label, hits) for a business type that is not listed, from the nouns in its description."""
    head = HEAD_SPLIT.split(" " + prompt + " ", maxsplit=1)[0]
    words = re.findall(r"[A-Za-z\u0900-\u097F]+", head.lower())
    hits = {}
    for kind, cues in KIND_CUES.items():
        cs = set(cues.split())
        n = sum(1 for w in words if w in cs)
        n += sum(1 for w in re.findall(r"[A-Za-z\u0900-\u097F]+", prompt.lower()) if w in cs) * 0.3   # words in the tail count a little
        if words and words[-1] in cs:
            n += 1.0   # the last word is the head noun: "... installation", "... studio"
        if n:
            hits[kind] = n
    if not hits:
        return None, None, 0.0
    best = max(hits, key=lambda k: (hits[k], -CUE_PRIORITY.index(k)))
    keep = [w for w in head.split() if w.lower() not in NOISE and w.lower() not in ("and", "&")]
    label = " ".join(w if w.isupper() else w.capitalize() for w in (keep[-3:] if len(keep) > 3 else keep)) or "Business"
    return best, label, hits[best]


# ---- Hindi prompts ---------------------------------------------------------------------------------------------
HI_CITIES = "दिल्ली मुंबई बेंगलुरु हैदराबाद अहमदाबाद चेन्नई कोलकाता पुणे जयपुर सूरत लखनऊ कानपुर नागपुर इंदौर भोपाल पटना वडोदरा लुधियाना आगरा नासिक फरीदाबाद मेरठ राजकोट वाराणसी अमृतसर रांची गुरुग्राम नोएडा चंडीगढ़ कोच्चि गोवा उदयपुर जोधपुर देहरादून ऋषिकेश शिमला मनाली मैसूर विशाखापत्तनम कोटा".split()
HI_SPLIT = re.compile(r"\s*(?:,|،|;|:|\sऔर\s|\sएवं\s|/|&)\s*")


def parse_hindi(prompt, type_keys=()):
    """Place and listed services from a Devanagari prompt: 'दिल्ली में दांतों का क्लिनिक, इम्प्लांट, ब्रेसेज़ और रूट कैनाल'."""
    facts = {"place": None, "items": []}
    for city in HI_CITIES:
        if city in prompt:
            facts["place"] = city
            break
    body = re.split(r"[।.\n]", prompt, maxsplit=1)[0]   # the first sentence describes the business; later ones carry phone, hours...
    chunks = [c.strip(" .।") for c in HI_SPLIT.split(body) if c.strip(" .।")]
    type_words = {k.rstrip("~") for k in type_keys if not k.isascii()} | set(HI_CITIES) | {"में", "के", "की", "का", "के लिए"}   # only the detected type's own words are "not a service"
    items = []
    for c in chunks[1:] if len(chunks) > 1 else []:
        c = re.sub(r"^(?:और|तथा)\s+", "", c)
        if 1 <= len(c.split()) <= 4 and c not in items and not all(w in type_words for w in c.split()):
            items.append(c)
    facts["items"] = items[:6]
    return facts


# ---- more types (autosales, robotics, pottery, skin, eye) ---------------------------------------------------------
add("autosales", "Vehicle Showroom", "shop", "bike showroom,motorcycle showroom,bike dealership,two wheeler showroom,car showroom,car dealership,car dealer,used cars,second hand car,scooter dealer,motorcycle dealer,bike dealer,बाइक शोरूम,कार डीलरशिप",
    "motorcycles scooters helmets accessories test-rides finance servicing spares riding-gear gloves jackets", "riders", ("Book a Test Ride", "Visit the Showroom"), "bold")
add("robotics", "Robotics & STEM Lab", "education", "robotics,robotic,stem lab,arduino,drone workshop,coding lab,रोबोटिक्स", "workshops kits projects classes challenges sessions sensors robots drones coding-labs competitions camps", "students", ("Book a Demo", "See the Workshops"), "cool")
add("pottery", "Pottery Studio", "portfolio", "pottery,ceramic,ceramics,clay studio,clay art,kumhar,मिट्टी के बर्तन,कुम्हार", "workshops classes pieces mugs bowls glazes sessions plates vases kits", "makers", ("Book a Session", "See the Studio"), "warm")
add("skin", "Skin Clinic", "care", "skin clinic,dermatologist,dermatology,skin doctor,skin specialist,acne,pigmentation,त्वचा", "consultations treatments peels facials procedures assessments programs sessions", "patients", ("Book a Consultation", "Call the Clinic"), "calm")
add("eye", "Eye Clinic", "care", "eye clinic,eye hospital,eye specialist,eye doctor,ophthalmology,ophthalmologist,cataract,lasik,aankhon,netra,आंखों,आँखों,नेत्र", "eye-tests consultations surgeries lenses screenings glasses frames treatments assessments", "patients", ("Book an Eye Test", "Call the Clinic"), "calm")
for _tid in ("autosales", "robotics", "pottery", "skin", "eye"):
    T[_tid]["offers"] = [w.replace("-", " ") for w in T[_tid]["offers"]]


from .keywords_extra import EXTRA_KEYS   # noqa: E402

for _tid, _ks in EXTRA_KEYS.items():
    T[_tid]["keys"] = list(dict.fromkeys(T[_tid]["keys"] + [k.strip() for k in _ks.split(",") if k.strip()]))
