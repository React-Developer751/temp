"""Reads the facts a person actually wrote: name, city, services/dishes, offers, hours, prices, phone, e-mail, years.

Works on English, Hinglish (Roman Hindi) and Devanagari text, on free-form comma lists as well as sentences
("Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu, open 12pm to 11pm, online booking").
Nothing is invented: a field that is not found stays empty and is reported by the caller as missing.
Stdlib only (re).
"""
import re

from .business_types import AUDIENCE, CITIES, HI_CITIES, T, parse_hindi, parse_prompt

# ---- cleaning ---------------------------------------------------------------------------------------------------
REQUEST = re.compile(
    r"^\s*(?:(?:please\s+)?(?:i\s+(?:want|need)|we\s+(?:want|need)|make|create|build|design|generate|write)\s+(?:me\s+)?(?:a|an|the)?\s*(?:website|site|web\s*page|webpage)\s+(?:for|of)\s+(?:my|our|a|an|the)?\s*"
    r"|(?:mujhe|humein|hume)\s+(?:ek\s+)?|(?:mera|meri|mere|hamara|hamari|hamare|apna|apni)\s+|(?:ek\s+)?(?:website|site)\s+(?:banani|banana|banao|chahiye|bana\s+do)\s+(?:hai\s+)?(?:for|ke\s+liye)?\s*"
    r"|मुझे\s+(?:एक\s+)?|मेरा\s+|मेरी\s+|मेरे\s+|हमारा\s+|हमारी\s+)+", re.I)
TAIL_FILLER = re.compile(r"\s*(?:ki|ka|ke|की|का|के)?\s*(?:website|site|वेबसाइट)\s*(?:banani|banana|banao|bana\s+do|chahiye|hai|है|चाहिए|बनानी|बनाना|बनाओ)?\s*(?:hai|है)?\s*$", re.I)
FILLER_WORDS = set("phone mobile call contact whatsapp email number no mail telephone mujhe humein hume ek mera meri mere hamara hamari hamare apna apni chahiye banani banana banao hai hain ka ki ke ko se me mein par wala wali wale liye "
                   "orders order prices price rates rate booking bookings enquiry enquiries call us contact us website site webpage page bana do dijiye karni karna please i want need a an the my our for of is are".split())
HI_FILLER = set("फोन मोबाइल कॉल संपर्क ईमेल नंबर व्हाट्सएप मुझे एक मेरा मेरी मेरे हमारा हमारी चाहिए बनानी बनाना बनाओ है हैं का की के को से में पर वाला वाली वाले लिए वेबसाइट साइट".split())
GENERIC_WORDS = set("service services shop store company business firm centre center agency studio point".split())

# ---- offers: what a business says it provides besides its main services ------------------------------------------
OFFERS = [
    ("online_booking", r"online\s+(?:booking|reservation|appointment)s?|appointments?\s+(?:are\s+)?(?:available\s+)?online|book(?:ing)?\s+online|table\s+booking|reservations?|appointment\s+booking|online\s+table|ऑनलाइन\s+(?:बुकिंग|अपॉइंटमेंट)|online\s+booking",
     "Online booking", "ऑनलाइन बुकिंग"),
    ("home_delivery", r"(?<!cash on )(?<!on )(?:free\s+|home\s+|doorstep\s+)?deliver(?:y|ies)(?:\s+available)?|we\s+deliver|ghar\s+tak\s+delivery|होम\s+डिलीवरी|घर\s+तक\s+डिलीवरी|डिलीवरी", "Home delivery", "होम डिलीवरी"),
    ("free_shipping", r"free\s+shipping|shipping\s+free|free\s+delivery\s+across|फ्री\s+शिपिंग", "Free shipping", "फ्री शिपिंग"),
    ("cod", r"\bcod\b|cash\s+on\s+delivery|कैश\s+ऑन\s+डिलीवरी", "Cash on delivery", "कैश ऑन डिलीवरी"),
    ("returns", r"easy\s+returns?|\d+\s*[- ]?day\s+returns?|returns?\s+accepted|return\s+policy|exchange\s+(?:available|policy)|वापसी|एक्सचेंज", "Easy returns", "आसान वापसी"),
    ("free_trial", r"free\s+(?:trial|demo)(?:\s+class)?|(?:demo|trial)\s+(?:class\s+)?(?:is\s+)?free|trial\s+class|demo\s+class|free\s+first\s+(?:class|session|visit|lesson)|first\s+(?:class|session|visit|lesson)\s+(?:is\s+)?free|फ्री\s+(?:ट्रायल|डेमो)", "Free trial", "फ्री ट्रायल"),
    ("new_patients", r"(?:accepting\s+)?new\s+(?:patients|clients|customers)\s+(?:are\s+)?(?:welcome|accepted)|accepting\s+new\s+(?:patients|clients)|नए\s+(?:मरीजों|ग्राहकों)\s+का\s+स्वागत", "New patients welcome", "नए मरीजों का स्वागत"),
    ("online_order", r"order(?:ing)?\s+online|online\s+order(?:ing|s)?|ऑनलाइन\s+ऑर्डर", "Order online", "ऑनलाइन ऑर्डर"),
    ("pickup", r"(?:curbside\s+|store\s+)?pick-?\s?up|पिकअप", "Pickup", "पिकअप"),
    ("financing", r"(?:special\s+|easy\s+)?financing(?:\s+(?:available|options))?|finance\s+options?|फाइनेंस", "Financing", "फाइनेंस"),
    ("admissions", r"admissions?\s+(?:are\s+)?open|admissions?\s+(?:going\s+on|started)|प्रवेश\s+(?:जारी|चालू)", "Admissions open", "प्रवेश जारी"),
    ("donate", r"donate\s+online|online\s+donations?|donations?\s+online|donate\s+now|ऑनलाइन\s+दान", "Donate online", "ऑनलाइन दान"),
    ("cashless", r"cashless\s+(?:insurance|treatment|claims?)|insurance\s+accepted|tpa", "Cashless insurance", "कैशलेस बीमा"),
    ("same_day", r"same[\s-]day\s+(?:emergenc\w+|appointments?|service|treatment|care)(?:\s+(?:treatment|care|service|visits?))?", "Same-day help", "उसी दिन सेवा"),
    ("free_consult", r"free\s+(?:consultation|quote|estimate|checkup|check-up|site\s+visit|site\s+survey|survey|inspection)|first\s+(?:consultation|meeting|visit|checkup)\s+(?:is\s+)?free|मुफ्त\s+परामर्श|फ्री\s+कंसल्टेशन", "Free consultation", "मुफ़्त परामर्श"),
    ("takeaway", r"take\s?-?away|takeout|dine[\s-]?in", "Takeaway", "टेकअवे"),
    ("parties", r"parties|(?:private\s+)?party\s+(?:bookings?|orders?|hall|space|dining)|birthday\s+parties|group\s+bookings?|kitty|banquet", "Parties and groups", "पार्टी और ग्रुप बुकिंग"),
    ("vegetarian", r"pure\s+veg|vegetarian|veg\s+only|jain\s+food|शुद्ध\s+शाकाहारी|शाकाहारी", "Vegetarian options", "शाकाहारी विकल्प"),
    ("emi", r"\b(?:no\s+cost\s+|easy\s+)?emi\b", "Easy EMI", "आसान EMI"),
    ("warranty", r"warranty|guarantee", "Warranty", "वारंटी"),
    ("walk_in", r"walk[\s-]?ins?(?:\s+welcome)?", "Walk-ins welcome", "वॉक-इन का स्वागत"),
    ("wifi", r"free\s+wi-?fi", "Free Wi-Fi", "फ्री Wi-Fi"),
    ("parking", r"(?:free\s+)?parking", "Parking", "पार्किंग"),
    ("home_visit", r"home\s+(?:visit|service)s?|ghar\s+par\s+service|घर\s+पर\s+सेवा", "Home visits", "घर पर सेवा"),
]
OFFER_RE = [(oid, re.compile(rx, re.I), en, hi) for oid, rx, en, hi in OFFERS]

# ---- hours -----------------------------------------------------------------------------------------------------
DAY = r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*"
CLOCK = r"\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?"
HOURS_RES = [
    re.compile(r"\b(?:open(?:s|ing)?|timings?|hours?)\b\s*[:\-]?\s*((?:" + DAY + r"\s*(?:-|to|–)\s*" + DAY + r"\s*)?" + CLOCK + r"\s*(?:-|–|to|till|until)\s*" + CLOCK + r")", re.I),
    re.compile(r"\b((?:" + DAY + r"\s*(?:-|to|–)\s*" + DAY + r"\s*)?\d{1,2}(?::\d{2})?\s*(?:am|pm)\s*(?:-|–|to|till|until)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", re.I),
    re.compile(r"\b(24\s*[x/]\s*7|24\s*hours?|open\s+daily|all\s+days)\b", re.I),
    re.compile(r"((?:सुबह|दोपहर|शाम|रात)?\s*\d{1,2}\s*(?:बजे)?\s*(?:से|-|to)\s*(?:सुबह|दोपहर|शाम|रात)?\s*\d{1,2}\s*(?:बजे)?\s*(?:तक)?)"),
    re.compile(r"((?:सुबह|दोपहर|शाम|रात)\s*\d{1,2}\s*बजे\s*तक(?:\s*खुला)?)"),
    re.compile(r"\b((?:subah|dopahar|shaam|raat)\s*\d{1,2}\s*baje\s*tak(?:\s*(?:khula|open))?)\b", re.I),
    re.compile(r"\b((?:subah|dopahar|shaam|raat)?\s*\d{1,2}\s*(?:baje)?\s*(?:se|to|-)\s*(?:subah|dopahar|shaam|raat)?\s*\d{1,2}\s*(?:baje|tak)?)\s*(?:tak|khula|open)\b", re.I),
]
PRICE_RE = re.compile(r"((?:₹|rs\.?|inr|\$|£|€)\s?\d[\d,]*(?:\.\d+)?(?:\s?/-)?|\d[\d,]*\s?(?:rupees|rupaye|रुपये|रुपए))", re.I)
PHONE_RE = re.compile(r"(?<![\w.])(\+?\(?\d[\d ()-]{8,16}\d)(?!\w)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

ADDRESS_RE = re.compile(r"\b(\d{1,5}[A-Za-z]?\s+(?:[A-Z][\w.'-]*\s+){1,3}(?:Street|St|Road|Rd|Avenue|Ave|Walk|Lane|Ln|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Place|Pl|Marg|Nagar|Chowk|Circle|Highway|Hwy)\b\.?)")
STATES = set("""alabama alaska arizona arkansas california colorado connecticut delaware florida georgia hawaii idaho illinois indiana iowa kansas kentucky louisiana maine maryland massachusetts michigan
minnesota mississippi missouri montana nebraska nevada ohio oklahoma oregon pennsylvania tennessee texas utah vermont virginia washington wisconsin wyoming ontario quebec alberta""".split())
PAIRS = ["spay and neuter", "bed and breakfast", "arts and crafts", "hair and beauty", "health and fitness", "pick and drop", "buy and sell", "repair and maintenance", "sales and service",
         "hair and skin", "nuts and bolts", "fish and chips", "tea and coffee", "bed and bath", "read and write", "heating and cooling", "heating and air conditioning", "wills and probate"]
PLACES = set("""himachal kullu manali shimla kerala goa kashmir ladakh rajasthan punjab gujarat bengal assam sikkim uttarakhand andaman varanasi rishikesh kedarnath char dham jaisalmer munnar ooty coorg
darjeeling leh spiti kutch swedish thai balinese moroccan himalayan ayurvedic punjabi kashmiri bengali tamil telugu marathi gujarati""".split())
FREE_SHIP = re.compile(r"(free\s+(?:shipping|delivery))\s+(?:above|over|on\s+orders?\s+(?:above|over|of))\s+((?:₹|rs\.?|\$|£|€)\s?\d[\d,]*)", re.I)
ROLE_WORDS_ITEM = set("dentist doctor lawyer advocate teacher designer photographer plumber electrician mechanic tailor chef trainer coach consultant freelancer developer artist".split())
KEEP_CAPS = set("python java javascript react angular english hindi french german spanish japanese chinese italian ielts toefl sat gre gmat".split())
STATE_ABBR = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC ON BC AB".split())

CITY_MORE = """agra ahmedabad ajmer aligarh allahabad prayagraj amritsar aurangabad bareilly bengaluru bangalore bhopal bhubaneswar bikaner chandigarh chennai coimbatore dehradun delhi dhanbad
durgapur faridabad ghaziabad goa gorakhpur gurgaon gurugram guwahati gwalior haridwar hyderabad indore jabalpur jaipur jalandhar jammu jamshedpur jodhpur kanpur kochi kolhapur kolkata kota
lucknow ludhiana madurai mangalore meerut mumbai mysore mysuru nagpur nashik navi noida patna pondicherry puducherry pune raipur rajkot ranchi rishikesh salem shimla siliguri srinagar surat
thane thiruvananthapuram trivandrum tiruchirappalli udaipur ujjain vadodara varanasi vijayawada visakhapatnam vizag warangal manali ooty darjeeling kerala london dubai singapore toronto
sydney manchester birmingham leeds glasgow edinburgh bristol liverpool newcastle mississauga melbourne""".split()
WORLD_CITIES = set("""austin portland seattle boston chicago houston dallas denver miami atlanta phoenix sacramento nashville orlando honolulu philadelphia detroit minneapolis cleveland pittsburgh charlotte
columbus cincinnati indianapolis calgary vancouver ottawa montreal perth brisbane adelaide auckland wellington dublin cardiff belfast johannesburg nairobi lagos karachi lahore dhaka kathmandu colombo""".split())
WORLD_CITIES |= {"san francisco", "san diego", "san jose", "los angeles", "new york", "las vegas", "salt lake city", "new delhi", "kuala lumpur", "hong kong", "cape town"}
ALL_CITIES = set(c.lower() for c in CITIES) | set(CITY_MORE) | WORLD_CITIES | {c for c in HI_CITIES}
WEEKDAYS = set("monday tuesday wednesday thursday friday saturday sunday weekend weekends weekday weekdays".split())
NATIONALITY = set("""italian indian chinese thai mexican french japanese korean american continental mughlai punjabi south north gujarati rajasthani bengali kerala hyderabadi lucknowi
desi pan asian indo mediterranean lebanese turkish greek spanish""".split())
LEAD_ITEMS = re.compile(r"\b(?:offering|offers|offer|providing|provides|provide|specializ(?:es|ing)\s+in|specialis(?:es|ing)\s+in|including|selling|sells|serving|serves|known\s+for|famous\s+for|dealing\s+in|deals\s+in|"
                        r"menu\s+includes?|services?\s+(?:like|such\s+as|include)|we\s+(?:do|sell|offer|provide|serve)|for|with)\b\s+(.+)", re.I)
SPLIT = re.compile(r"\s*(?:,|;|\||&|\band\b|\baur\b|\bya\b|\bor\b|\bplus\b|/|\+|\sऔर\s|\sएवं\s|\sया\s)\s*", re.I)
WALA = re.compile(r"^(.*?)\s+(?:wala|wali|wale|वाला|वाली|वाले)\s+(.*)$", re.I)
TRAILING_MEIN = re.compile(r"\s+(?:mein|me|में|मे|ka|ki|ke|का|की|के)\s*$", re.I)


def _norm_space(s):
    return re.sub(r"\s+", " ", s).strip(" ,.;:-|।")


def strip_request(prompt):
    p = prompt.strip()
    if not re.match(r"(?:Apna|Apni|Mera|Meri|Mere|Hamara|Hamari|Hamare)\s+(?:[A-Z][\w&'-]*\s+){1,4}?(?=[A-Z][\w&'-]*\s*[,:.–-])|(?:Apna|Apni|Mera|Meri|Mere|Hamara|Hamari|Hamare)\s+(?:[A-Z][\w&'-]*\s*){2,5}[,:.–-]", p):
        p = REQUEST.sub("", p)   # "Apna Medical Store, Lucknow" is a name; "mera cafe ..." is a request
    p = TAIL_FILLER.sub("", p)
    p = re.sub(r"\s*(?:ki|ka|ke)?\s*(?:website|site)\s+(?:banani|banana|banao|chahiye)\s*(?:hai)?\s*[:,]?\s+(?=\S)", ", ", p, flags=re.I)   # "coaching institute ki website chahiye: Pragati Classes, Kota"
    return p.strip()


HEADS = set("""food fish toys shoes bags repair repairs service services treatment treatments cleaning installation replacement recovery training classes class cut colour color makeup facial care wash painting
fitting wiring design shoot shoots photography cakes cookies bread pastries brownies sandals socks belts accessories supplies medicines products items rings chains sarees kurtis shirts jeans books pens
tyres tyre batteries battery lights fans pumps tanks pipes tap taps removal whitening braces implants crowns dentures scaling massage spa waxing threading bleach
guard cover covers case charger cable glass board boards bulb lamp lock locks door doors window windows paint colour polish
course courses test tests reflexology puncture scrub therapy checkup lessons lesson session sessions""".split())
WEAK_HEADS = set("course courses test tests care session sessions lesson lessons checkup therapy class classes work works service".split())   # rarely a service on their own
SUBJECTS = set("maths math science english hindi physics chemistry biology history commerce accounts economics geography sanskrit".split())
INGREDIENTS = set("design tyre tyres battery engine brake foot fish chicken mutton paneer egg eggs prawn prawns crab veg lamb pork beef cheese corn mushroom aloo gobi".split())


_KNOWN = {}


def _known():
    """Item-like phrases (typical offerings and dish/service names) and keywords of every trade, for cutting a list typed without commas."""
    if not _KNOWN:
        from .business_types import T
        from . import lexicon
        items, keys = set(), set()
        for t in T.values():
            items.update(o.lower() for o in (t.get("offers") or []))
            keys.update(k.rstrip("~").lower() for k in t["keys"] if k.isascii())
        for prof in lexicon.LEX.values():
            items.update(k.lower() for k in prof)
        _KNOWN.update({"items": items, "keys": keys})
    return _KNOWN


DISH_HEADS = set("""curry fry masala kadi rice roll tikka kebab biryani soup salad sandwich burger noodles pizza pasta cake cakes bread polish""".split())


NOT_HEADS = {"wedding", "evening", "morning", "building", "clothing", "offering", "something", "anything", "everything", "nothing", "spring", "string", "sibling", "ceiling", "darling"}


def _is_head(w):
    w = w.lower()
    return w in HEADS or w in DISH_HEADS or (re.search(r"(?:ing|tion|ment|ery|age)$", w) is not None and len(w) > 5 and w not in NOT_HEADS)


def _plural(w):
    w = w.lower()
    return w.endswith("s") and not w.endswith("ss") and len(w) > 3


def _seg_score(seg, kn):
    """How much a run of words looks like ONE service name (known phrase > modifier + head noun > plural noun > bare word)."""
    ph = " ".join(seg).lower()
    sg = ph.rstrip("s")
    if (ph in kn["items"] or sg in kn["items"]) and len(seg) > 1:
        return 4.0 + len(seg)
    if len(seg) == 1:
        w = seg[0]
        if w[:1].isupper() or re.match(r"[a-z]+[A-Z]", w):
            return 2.0   # a capitalised or camel-case word on its own is a brand or product ("Samsung", "iPhone")
        if ph in ("after", "before", "pre", "post", "non", "self", "over", "under", "per"):
            return -2.0   # a word that cannot stand alone as a service
        if ph in WEAK_HEADS:
            return -1.0
        if ph in SUBJECTS:
            return 1.5
        if _plural(w) or _is_head(w):
            return 2.0
        if ph in kn["items"] or sg in kn["items"]:
            return 1.5
        return 1.0 if ph in kn["keys"] or sg in kn["keys"] else 0.0
    if ph in kn["keys"] or sg in kn["keys"]:
        return 2.0 + len(seg) * 0.5
    if _is_cap(seg[0]) and seg[0].lower() not in KEEP_CAPS | NATIONALITY | PLACES:
        return 0.0   # "Samsung accessories": a brand then a product, two services
    if _is_head(seg[-1]) or _plural(seg[-1]):
        if not any((_plural(w) or _is_head(w)) and w.lower() not in INGREDIENTS for w in seg[:-1]):
            return 4.5 if len(seg) == 2 else 4.2   # modifier(s) + head noun: "dog food", "aquarium fish", "interior cleaning"
        return 0.5
    return 0.0


def _common(w):
    """True for an everyday English word (so a capital on it is only the start of a sentence, not a brand)."""
    from . import typos
    return typos._load()[0].get(w.lower(), 0) >= 60 and w.lower() not in KEEP_CAPS | PLACES


MODIFIERS = set("after before pre post non self hair body skin face nail nails hand foot home car bike pet baby kids men women ladies gents bridal party wedding birthday office house shop online mobile sports girls boys school formal casual".split())
STANDALONE = set("meditation pranayama aerobics facial massage manicure pedicure waxing threading haircut bleach cleanup spa".split())   # a service on its own even though it could also end a phrase


def _is_cap(w):
    return w[:1].isupper() or re.match(r"[a-z]+[A-Z]", w) is not None


def _segment(text, min_words=4, allow_short=True):
    """Cut a run of words typed without separators into service names, using known phrases first and word shape second.
    "dog food cat food aquarium fish toys" -> dog food | cat food | aquarium fish | toys. Returns [text] when it is better left whole."""
    words = text.split()
    n = len(words)
    kn = _known()
    if words[0][:1].isupper() and words[0][1:].islower() and _common(words[0]):
        words[0] = words[0].lower()   # "General dental care": a capital that only starts the sentence
    best = {0: (0.0, [])}
    for i in range(1, n + 1):
        cand = None
        for k in (1, 2, 3):
            if i - k < 0 or (i - k) not in best:
                continue
            seg = words[i - k:i]
            if k > 1 and any(_is_cap(w) for w in seg[1:]) and _is_cap(seg[0]):
                continue   # two capitalised words side by side ("iPhone Samsung") are two names
            sc = best[i - k][0] + _seg_score(seg, kn) - 1.0 - 0.01 * (1 if k == 1 else 0)   # on a tie, fewer and longer names win
            if cand is None or sc > cand[0]:
                cand = (sc, best[i - k][1] + [" ".join(seg)])
        if cand:
            best[i] = cand
    if n not in best:
        return [text]
    score, parts = best[n]
    if n < min_words and not allow_short:
        return [text]   # the person already put commas between their services: "idli sambar" stays one
    known = lambda w: w.lower() in kn["items"] or w.lower().rstrip("s") in kn["items"]   # noqa: E731
    if (n == 2 and not _is_head(words[0]) and (not _is_head(words[1]) or words[1].lower() in STANDALONE) and not _plural(words[1]) and words[0].lower() not in MODIFIERS
            and (known(words[0]) or words[0].lower() in kn["keys"]) and known(words[1])):
        return list(words)   # "haircut facial": two known services side by side
    if n == 2 and _plural(words[0]) and _plural(words[1]) and words[0].lower() not in MODIFIERS and not words[0].lower().endswith("'s"):
        return list(words)   # "kurtis sarees": two plural nouns
    if len(parts) < 2:
        return [text]
    if n >= min_words:
        return parts if all(len(p.split()) <= 5 for p in parts) else [text]
    return parts if score > _seg_score(words, kn) + 2.5 else [text]   # 2-3 words: only cut when every part is clearly a service of its own


def _locality_city(chunk):
    """"Chandni Chowk Delhi" -> ("Chandni Chowk", "Delhi"): an area followed by its city."""
    ws = chunk.replace(".", " ").split()
    if len(ws) >= 2 and ws[-1].lower() in ALL_CITIES and all(w[:1].isupper() for w in ws[:-1]) and " ".join(ws).lower() not in ALL_CITIES:
        return " ".join(ws[:-1]), ws[-1]
    return None


DESCRIPTORS = set("""gym bakery garage pharmacy hotel spa sweets jewellers jeweller boutique parlour parlor accountants accountant advocates advocate lawyers lawyer dentists dentist doctors doctor clinic clinics hospital restaurant cafe salon parlour parlor studio agency company firm shop store centre center
institute academy school consultants consultant architects architect engineers engineer contractors contractor dealers dealer""".split())


LEAD_VERB = (r"(?:do|have|make|sell|offer|provide|serve|design|stock|repair|teach|cook|bake|sew|handle|manufacture|supply|install|run|deal\s+in|specialize\s+in|specialise\s+in|"
             r"also\s+(?:do|make|sell|offer|provide|serve|take))")
SENT_DROP = re.compile(r"^(?:you\s+can\s+(?:order|book|reach|contact|call|message)|contact\s+(?:me|us)|call\s+(?:me|us)|reach\s+(?:me|us)|visit\s+(?:us|our)|thank|thanks|please|feel\s+free|"
                       r"it\s+is(?:\s+and\s+it\s+is)?\s*$|we\s+are\s*$)", re.I)


def _rewrite_sentences(p):
    """"We are a bakery in Jaipur. We make cakes and pastries. You can order on WhatsApp." -> "bakery in Jaipur. cakes and pastries."
    Sentences that only say how to reach the business are dropped; lead-ins like "We offer" / "Our company provides" are removed."""
    p = re.sub(r"^\s*(?:hi|hello|hey|namaste|namaskar|dear\s+\w+)\b[\s,!.]*", "", p, flags=re.I)
    p = re.sub(r"\b(?:i\s+(?:need|want)|we\s+(?:need|want)|looking\s+for|i\s+am\s+looking\s+for)\s+(?:a\s+)?(?:website|site)\s+for\s+(?:my|our|a|an|the)?\s*", "", p, flags=re.I)
    p = re.sub(r"\b(?:it|this)\s+is\s+(called|named)\b", r"\1", p, flags=re.I)
    p = re.sub(r"\band\s+(?:it|we)\s+(?:is|are)\s+(?:located\s+|based\s+|situated\s+)?(in|at)\b", r"\1", p, flags=re.I)
    p = re.sub(r"\b(?:and|,)\s+we\s+" + LEAD_VERB + r"\s+", ", ", p, flags=re.I)
    out = []
    for sent in re.split(r"(?<=[.!?])\s+(?=[A-Za-z])", p):
        t = sent.strip()
        if not t or (SENT_DROP.match(t) and not re.search(r"@|\d[\d ()-]{7,}", t)):   # a "contact me at ..." line that holds an email or phone is kept for those
            continue
        m = re.match(r"(?:located|based|situated)\s+(?:in|at|near)\s+(.+?)[.!]*$", t, re.I)
        if m:
            t = "in " + m.group(1)
        t = re.sub(r"^along\s+with\s+that,?\s+", "", t, flags=re.I)
        t = re.sub(r"^(?:our\s+)?(?:main\s+)?(?:services|treatments|products|specialties|specialities|menu|offerings)\s+(?:include|includes|are|:)\s*:?\s*", "", t, flags=re.I)
        t = re.sub(r"^(?:we|i)\s+are\s+(?:a|an)\s+", "", t, flags=re.I)
        t = re.sub(r"^(?:we|i)\s+run\s+(?:a|an|the)\s+(?:small\s+|new\s+)?", "", t, flags=re.I)
        t = re.sub(r"^(?:we|i)\s+" + LEAD_VERB + r"\s+", "", t, flags=re.I)
        t = re.sub(r"^our\s+(?:company|firm|team|shop|store|clinic|studio|agency|centre|center)\s+(?:provides|offers|sells|does|handles|specialises\s+in|specializes\s+in|makes|serves)\s+", "", t, flags=re.I)
        t = re.sub(r"^i\s+am\s+(?:a|an)\s+", "", t, flags=re.I)
        t = re.sub(r"^(?:we\s+)?(?:also\s+)?(?:take|accept)\s+(custom\s+orders?)\s+for\s+.*$", r"\1", t, flags=re.I)
        t = re.sub(r"\b(?:every|each)\s+(?:morning|day|evening|week)\b", "", t, flags=re.I)
        t = re.sub(r"\s+for\s+(?:birthdays?|weddings?|parties|events?|occasions?|festivals?|offices?|businesses|companies|homes)(?:\s+(?:and|aur)\s+\w+)?(\s+in\b)?", lambda m_: "," + (" in" if m_.group(1) else ""), t, flags=re.I)
        t = re.sub(r"\b(?:all\s+kinds\s+of|a\s+(?:wide\s+)?(?:variety|range)\s+of|different\s+types\s+of|various)\s+", "", t, flags=re.I)
        out.append(t)
    return "\n".join(out) if out else p


def _city_text(chunk):
    return TRAILING_MEIN.sub("", re.sub(r"^(?:in|at|near)\s+", "", chunk.strip(), flags=re.I)).strip(" .")


def _is_city(chunk):
    c = re.sub(r"^(?:in|at|near)\s+", "", chunk.lower().strip(" ."))
    c = TRAILING_MEIN.sub("", c).strip()
    return c in ALL_CITIES


CONNECTORS = {"of", "the", "&", "and", "n"}


def _title_run(tokens, exclude, type_words=frozenset()):
    """Longest run of capitalised words that are not type words, cuisines, cities or fillers: the business name.
    A capitalised type word may close the name ("Rani Boutique", "Smile Hub"), and "of/the/&" may join words ("Taste of Delhi")."""
    best, cur = [], []
    n = len(tokens)
    for i, w in enumerate(tokens):
        bare = re.sub(r"[^\w&'-]", "", w)
        low = bare.lower()
        cap = bool(bare) and bare[0].isupper()
        if cap and low not in exclude:
            cur.append(bare)
        elif cap and cur and low in type_words:          # trailing type word, e.g. "Rani Boutique"
            cur.append(bare)
        elif low in CONNECTORS and cur and i + 1 < n and tokens[i + 1][:1].isupper():
            cur.append(bare if bare == "&" else low)
        elif cap and cur and cur[-1] in ("of", "the", "&", "and", "n"):   # "Taste of Delhi": a city after a connector belongs to the name
            cur.append(bare)
        else:
            if cur and cur[-1] in ("of", "the", "&", "and", "n"):
                cur.pop()
            if len(cur) > len(best):
                best = cur
            cur = []
    if cur and cur[-1] in ("of", "the", "&", "and", "n"):
        cur.pop()
    if len(cur) > len(best):
        best = cur
    return " ".join(best[:5]) if best else None


MORE_HOURS = re.compile(r"\s*[,;&]?\s*((?:" + DAY + r"\s*(?:-|to|–)\s*" + DAY + r"|" + DAY + r")\s*" + CLOCK + r"\s*(?:-|–|to|till|until)\s*" + CLOCK + r")", re.I)
DAILY = re.compile(r"\b(?:daily|every\s*day|7\s+days(?:\s+a\s+week)?|seven\s+days(?:\s+a\s+week)?)\b", re.I)


def _find_hours(text):
    for rx in HOURS_RES:
        m = rx.search(text)
        if m:
            span = m.group(1) if m.lastindex else m.group(0)
            hours, (a, b) = _norm_space(span), m.span()
            while True:   # "Mon-Wed 8am-5pm, Thu 8am-3pm": every further day range belongs to the hours too
                more = MORE_HOURS.match(text, b)
                if not more:
                    break
                hours += ", " + _norm_space(more.group(1))
                b = more.end()
            return hours, (a, b)
    return None, None


PERIOD = {"subah": "am", "सुबह": "am", "dopahar": "pm", "दोपहर": "pm", "shaam": "pm", "शाम": "pm", "raat": "pm", "रात": "pm"}


def hours_for_english(h):
    """Hinglish hours ("subah 9 se raat 9 tak") as English ("9am to 9pm"); anything else is returned unchanged."""
    if not h:
        return h
    m = re.fullmatch(r"\s*(subah|dopahar|shaam|raat)?\s*(\d{1,2})\s*(?:baje)?\s*(?:se|to|-)\s*(subah|dopahar|shaam|raat)?\s*(\d{1,2})\s*(?:baje|tak)?(?:\s*(?:tak|khula|open))?\s*", h, re.I)
    if not m:
        m = re.fullmatch(r"\s*(?:(subah|dopahar|shaam|raat)\s*)?(\d{1,2})\s*baje\s*tak(?:\s*(?:khula|open))?\s*", h, re.I)
        if m:
            period = PERIOD.get(m.group(1).lower(), "") if m.group(1) else ""
            return "until %s%s" % (m.group(2), period)
        return h
    p1, a, p2, b = m.group(1), m.group(2), m.group(3), m.group(4)
    sfx1 = PERIOD.get((p1 or "").lower(), "")
    sfx2 = PERIOD.get((p2 or "").lower(), "") or sfx1
    return "%s%s to %s%s" % (a, sfx1, b, sfx2)


def find_offers(text):
    out, seen = [], set()
    for oid, rx, en, hi in OFFER_RE:
        if oid in seen:
            continue
        m = rx.search(text)
        if m:
            seen.add(oid)
            if oid == "free_trial" and "first" in m.group(0).lower():
                en = "Free first class"
            out.append({"id": oid, "text": en, "text_hi": hi})
    return out


def extract_facts(prompt, facts=None, type_keys=(), type_label=""):
    """-> dict(name, city, items, offers, hours, prices, phone, email, years, audience, type_chunk, chunks).
    `facts` (from a JSON file or flags) always wins over what is read from the prompt."""
    facts = facts or {}
    raw = prompt
    out = {"name": None, "city": None, "items": [], "offers": [], "hours": None, "prices": [], "phone": None, "email": None, "years": None, "audience": None,
           "type_chunk": "", "address": None, "cut": [], "source": {}}
    p = _rewrite_sentences(strip_request(prompt))
    em, ph = EMAIL_RE.search(p), None
    if em:
        out["email"] = em.group(0)
        p = p.replace(em.group(0), " ")
    pm = PHONE_RE.search(p)
    if pm:
        out["phone"] = pm.group(1).strip()
        p = p.replace(pm.group(0), " ")
    ym = re.search(r"(?:with\s+)?(\d{1,2})\+?\s*(?:years|yrs|saal|साल)(?:\s+of\s+(?:experience|service|trust))?|since\s+(19\d\d|20\d\d)", p, re.I)
    if ym:
        out["years"] = re.sub(r"^with\s+", "", ym.group(0).strip(), flags=re.I)
        p = p.replace(ym.group(0), " ")
    am = ADDRESS_RE.search(p)
    if am:
        out["address"] = _norm_space(am.group(1))
        p = p.replace(am.group(0), " ")
    hours, span = _find_hours(p)
    if hours:
        out["hours"] = hours
        p = p[:span[0]] + "\n" + p[span[1]:]
        p = re.sub(r"\b(?:open(?:s|ing)?|timings?|hours?|khula|खुला)\b\s*[:\-]?", " ", p, flags=re.I)
    if hours or re.search(r"\bopen\b", p, re.I):
        p = DAILY.sub(" ", p)
    ship = None
    sm = FREE_SHIP.search(p)
    if sm:   # "free shipping above Rs 999" is an offer with a condition, not a price
        amount = _norm_space(sm.group(2))
        ship = {"id": "free_shipping", "text": "Free shipping above " + amount, "text_hi": amount + " से ऊपर फ्री शिपिंग"}
        p = p.replace(sm.group(0), " ")
    prices, rest = [], p
    for m in PRICE_RE.finditer(p):
        before = p[:m.start()]
        if re.search(r"\b(?:above|over|minimum|min|upto|up\s+to|orders?\s+of)\W*$", before, re.I):
            continue   # "free shipping above Rs 999" is a condition of an offer, not a price
        name = re.split(r"[,;.]|\band\b|\baur\b", before)[-1]
        name = re.sub(r"\b(?:for|at|starts?|starting|from|only|just|@|rs|prices?|cost|rates?)\b\W*$", "", _norm_space(name), flags=re.I).strip()
        name = re.sub(r"^(?:prices?|rates?)$", "", name, flags=re.I)
        word = re.search(r"\b(starting|starts?|from|onwards)\b\W*(?:at|from)?\W*$", before, re.I)
        cleaned = re.sub(r"\b(?:starting|starts?|from|onwards)\b\W*(?:at|from)?\W*$", "", name, flags=re.I).strip()
        price = ("from " if word else "") + _norm_space(m.group(1))
        prices.append({"name": (cleaned.capitalize() if cleaned else ("Starting price" if not prices else "Price")), "price": price})
    if prices:
        out["prices"] = prices
        rest = PRICE_RE.sub(" ", p)
        for pr in prices:
            if pr["name"] and pr["name"] != "Starting price" and pr["name"] != "Price":
                rest = re.sub(r"(?:,|;)?\s*" + re.escape(pr["name"]) + r"\s*(?:for|at|starts?\s+at|from|:|-)?\s*(?=,|;|$)", " ", rest, count=1, flags=re.I)
        p = rest
    out["offers"] = find_offers(p)
    if ship:
        out["offers"] = [o for o in out["offers"] if o["id"] != "free_shipping"] + [ship]

    # quoted / "called X" names first
    nm = re.search(r"[\"“'‘]([^\"”'’]{2,40})[\"”'’]", p)
    hi_name = re.search(r"नाम\s+(?:है\s+)?([ऀ-ॿ]+(?:\s+[ऀ-ॿ]+){0,2}?)(?=\s*[,।.]|\s+(?:है|हैं|में|मे)(?![ऀ-ॿ])|$)", p)
    called = re.search(r"(?:called|named|name\s+is|naam(?:\s+hai)?|नाम(?:\s+है)?)\s+[\"“']?([A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*){0,3})", p)
    if nm:
        out["name"] = nm.group(1).strip()
        p = p.replace(nm.group(0), " ")
    elif hi_name:
        out["name"] = hi_name.group(1).strip()
        p = re.sub(r"(?:[ऀ-ॿ]+\s+(?:का|की|के)\s+)?" + re.escape(hi_name.group(0)) + r"(?:\s+(?:है|हैं))?", " ", p, count=1)   # "दुकान का नाम Y है" goes whole
    elif called:
        out["name"] = called.group(1).strip()
        p = p.replace(called.group(0), " ")

    # split into chunks on commas, "aur", "and" ...; "X wala Y" gives an item and the rest
    chunks = []
    p_ = p
    for pair in PAIRS:   # "spay and neuter" is one service
        p_ = re.sub(pair.replace(" and ", r"\s+and\s+"), lambda m: m.group(0).replace(" and ", "\x02"), p_, flags=re.I)
    p_ = re.sub(r"\s[-–—]\s", ", ", p_)   # "Urban Threads boutique - kurtis, sarees": a spaced dash is a comma
    p_ = re.sub(r"\b(Dr|St|Mr|Mrs|Ms|Prof|No|Co|Ltd|Inc|Pvt|LLP|Corp|Bros|Jr|Sr)\.\s", "\\1\x01", p_)
    p_ = re.sub(r"(?<=[A-Za-z0-9])\.\s+(?=[A-Z])", "\n", p_)   # sentence ends are chunk ends: "... Brookvale, Ohio. General dental care ..."
    for seg in re.split(r"[\n;|।:]|,(?![^()]*\))", p_):
        for c in re.split(r"\s+(?:aur|और)\s+|(?<=[a-z])\s+&\s+(?=[a-z])", seg):   # "&" joins two services, but "Verma & Associates" is one name
            c = _norm_space(c).replace("\x01", ". ")
            if c:
                chunks.append(c)
    flat = []
    for c in chunks:
        w = WALA.match(c)
        if w:
            flat += [_norm_space(w.group(1)), _norm_space(w.group(2))]
        else:
            flat.append(c)
    split_flat = []
    for c in flat:   # "pet shop in bangalore dog food cat food toys": what follows the city is the list of services
        done = False
        for m in re.finditer(r"\b(?:in|at|near)\s+", c, re.I):
            ws = c[m.end():].split()
            for n in (3, 2, 1):
                known_city = " ".join(ws[:n]).lower() in ALL_CITIES or (n == 1 and ws[0][:1].isupper() and ws[0].isalpha() and len(ws) > 3)   # an unlisted town: "in Anand fresh milk paneer ..."
                if len(ws) > n + 1 and known_city and ws[n][:1].islower() and ws[n].lower() not in ("and", "aur", "for", "with", "open", "since", "call", "from", "mein", "me"):
                    split_flat += [c[:m.end()] + " ".join(ws[:n]), " ".join(ws[n:])]
                    done = True
                    break
            if done:
                break
        if not done:
            split_flat.append(c)
    flat = split_flat
    state_city = None
    for i in range(1, len(flat)):
        if (flat[i] in STATE_ABBR or flat[i].lower() in STATES) and re.fullmatch(r"[A-Z][a-z.'-]+(?:\s+[A-Z][a-z.'-]+){0,2}", flat[i - 1]):
            state_city = flat[i - 1]   # "Happy Paws Clinic, Austin, TX"
            flat[i - 1] = ""
            break
    chunks = [c for c in flat if c and c.lower() not in STATES and c not in STATE_ABBR]   # a state after the city is part of the place, not a service

    keys = {k.rstrip("~").lower() for k in type_keys}
    keys |= {w.lower() for w in re.findall(r"[A-Za-z]+", type_label)} if type_label else set()
    type_idx = None
    for i, c in enumerate(chunks):
        low = " " + c.lower() + " "
        if any((" " + k + " " in low) or (k in low and not k.isascii()) or (k.isascii() and re.search(r"(?<![a-z])" + re.escape(k), low)) for k in keys if len(k) > 2):
            type_idx = i
            break
    NAME_LIKE = r"[A-Z][\w&'-]*(?:\s+(?:[A-Z][\w&'-]*|&|of|the|and)){0,5}"
    name_from_chunk = False

    def _hits(text):
        t_ = " " + text.lower() + " "
        return any((" " + k + " " in t_) or (k in t_ and not k.isascii()) or (k.isascii() and re.search(r"(?<![a-z])" + re.escape(k), t_)) for k in keys if len(k) > 2)
    if len(chunks) > 1 and not out["name"] and re.fullmatch(NAME_LIKE, chunks[0]) and not _is_city(chunks[0]):
        c0, nxt = chunks[0], chunks[1]
        ws0 = c0.split()
        all_type = all(w.lower() in (keys | GENERIC_WORDS | NATIONALITY | CONNECTORS) for w in ws0)
        if re.match(r"(?:a|an|the)\s", nxt, re.I):
            out["name"], chunks[0], type_idx = c0, "", 1   # "Stillwater, a yoga studio in Northgate"
        elif not all_type and (len(ws0) >= 2 or "&" in ws0):
            if _hits(nxt) or _is_city(nxt) or _locality_city(nxt):   # "Tandoori Nights, North Indian restaurant ...", "Rao & Associates, chartered accountants", "Mobile Mania, Surat"
                out["name"], chunks[0], name_from_chunk = c0, "", True
                if type_idx in (None, 0):
                    type_idx = 1 if _hits(nxt) else type_idx
    if type_idx is None:
        type_idx = next((i for i, c in enumerate(chunks) if c), 0) if chunks else None
    type_chunk = chunks[type_idx] if type_idx is not None else ""
    out["type_chunk"] = type_chunk.replace("\x02", " and ")
    if type_idx and not out["name"] and re.match(r"(?:a|an|the)\s", type_chunk, re.I):
        prev = chunks[type_idx - 1]
        if re.fullmatch(r"[A-Z][\w&'-]*(?:\s+[A-Z][\w&'-]*){0,4}", prev) and not _is_city(prev) and not (set(prev.lower().split()) & (keys | NATIONALITY)):
            out["name"] = prev
            chunks[type_idx - 1] = ""

    # city
    city = None
    pm_ = re.search(r"\b(?:in|at|near|based\s+in|from|around)\s+([A-Z][A-Za-z.'-]+(?:[ \t]+[A-Z][A-Za-z.'-]+){0,2})", p) or re.search(r"\b(?:in|at|near)\s+([a-z]+(?:[ \t][a-z]+)?)\b", p)
    if pm_ and (pm_.group(1).lower() in ALL_CITIES or pm_.group(1)[0].isupper()):
        cand = re.split(r"\.\s", pm_.group(1).strip())[0].rstrip(".'-")
        low = cand.lower()
        if low in ALL_CITIES or (cand[0].isupper() and low not in WEEKDAYS and low not in AUDIENCE and low.split()[0] not in AUDIENCE):
            city = cand
    locality = None
    if city and len(city.split()) > 1 and city.lower() not in ALL_CITIES and city.split()[0].lower() in ALL_CITIES:
        locality, city = " ".join(city.split()[1:]), city.split()[0]   # "in Delhi Nehru Place": the city comes first, then the area
    if city and city.lower() not in ALL_CITIES:   # "in Koramangala, Bengaluru": the area comes first, the city after it
        for i, c in enumerate(chunks):
            if i != type_idx and _is_city(c):
                locality, city = city, _city_text(c)
                chunks[i] = ""
                break
    if city is None and state_city:
        city = state_city
    if city is None:
        for i, c in enumerate(chunks):
            if i != type_idx and _is_city(c):
                city = _city_text(c)
                chunks[i] = ""
                j = i - 1
                while j >= 0 and not chunks[j]:
                    j -= 1
                if j >= 0 and j != type_idx and re.fullmatch(r"[A-Z][a-z.'-]+(?:\s+[A-Z][a-z.'-]+){0,2}", chunks[j]) and not _is_city(chunks[j]):
                    if not out["name"] and (not any(chunks[:j]) or (j - 1 == type_idx and not re.search(r"[A-Z]", chunks[type_idx]))):   # the first thing in the prompt, before the city, is the name: "... chahiye: Pragati Classes, Kota"
                        out["name"], chunks[j] = chunks[j], ""
                    else:
                        locality, chunks[j] = chunks[j], ""   # "Sharma Sweets, Karol Bagh, Delhi"
                break
    if city is None:
        for i, c in enumerate(chunks):
            lc = _locality_city(c) if i != type_idx and c else None
            if lc:
                locality, city, chunks[i] = lc[0], lc[1], ""
                break
    if city is None:   # "<city> mein" / "<city> में" anywhere, incl. inside the type chunk
        m = re.search(r"([A-Za-zऀ-ॿ]+)\s+(?:mein|me|में|मे)\b", p)
        if m and m.group(1).lower() in ALL_CITIES:
            city = m.group(1)
    if city is None:
        for w in re.findall(r"[A-Za-zऀ-ॿ]+", type_chunk):
            if w.lower() in ALL_CITIES:
                city = w
                break
    if locality and not out["address"]:
        out["address"] = locality
    if city:
        out["city"] = " ".join(x.capitalize() if x.islower() and x.isascii() else x for x in city.split())

    # items: after trigger words inside the type chunk, plus the remaining plain chunks
    items = []
    cut = []   # runs of words that were cut into services without any separator between them

    def add_item(x):
        x = x.replace("\x02", " and ")

        x = re.split(r"[.!?]|\b(?:call|contact(?!\s+lens)|phone|whatsapp|mail|email|since|open)\b", x, maxsplit=1, flags=re.I)[0]
        x = re.sub(r"\s+(?:starting|starts?|from|onwards|only|just)\s*$", "", x.strip(), flags=re.I)
        x = _norm_space(re.sub(r"^(?:and|aur|our|the|best|all|your|a|an|also)\s+", "", _norm_space(x), flags=re.I))
        x = TRAILING_MEIN.sub("", x).strip()
        x = re.sub(r"^(?:(?:we|i|you|they)\s+(?:also\s+|can\s+)?)?(?:" + LEAD_VERB + r"|offering|providing|offers|provides|specializing\s+in|selling|sells|serving|serves|stocking|dealing\s+in|deals\s+in)\s+", "", x, flags=re.I)
        x = re.sub(r"^(?:\w+)\s+(?:ki|ke|ka)\s+(classes|class|tuition|coaching|batches)\b.*$", lambda m_: m_.group(0).split()[0] + " " + m_.group(1), x, flags=re.I)   # "English ki classes 6th se 12th tak"
        x = re.sub(r"\s+(?:available|online)\s*$", "", x, flags=re.I) if len(x.split()) > 2 else x
        hm = re.match(r"(?:(?:a|an|the)\s+)?([a-z][a-z ]{1,28}?)\s+(?:with|offering|offers|including|featuring|having)\s+(.+)$", x, re.I)
        if hm and set(hm.group(1).lower().split()) <= (keys | GENERIC_WORDS | {w.lower() for w in re.findall(r"[A-Za-z]+", type_label or "")}):
            x = hm.group(2)   # "a gym with weight training" -> "weight training"
        if re.match(r"(?:we|i|it|you|they|my|our|hi|hello|located|based|situated|website\s+for|site\s+for)\b", x, re.I) and not re.match(r"(?:our|my)\s+\w+\s+\w+", x, re.I):
            return   # a fragment of a sentence ("It is", "you can order on", "my gym"), not a service
        if re.match(r"\d{1,2}(?:st|nd|rd|th)\b", x, re.I) or re.search(r"\b(?:se|to)\s+\d{1,2}(?:st|nd|rd|th)?\s*(?:tak)?$", x, re.I) and re.match(r"\d", x):
            return   # "9th se 12th": the classes taught, not a service
        if x.lower() in ROLE_WORDS_ITEM:
            return   # "dentist" says who they are, not what they do
        if re.findall(r"[a-z]+", x.lower()) and set(re.findall(r"[a-z]+", x.lower())) <= (NATIONALITY | {"food", "cuisine", "dishes"}):
            return   # a cuisine ("Chinese", "Thai food") names a style, not a dish
        if len(x.split()) >= 2 and x.isascii() and not re.search(r"\d|\b(?:to|of|in|for|and|with|on|at|from|by|the|a|an|or|aur)\b", x, re.I):
            segs = _segment(x, min_words=4, allow_short=len(plain) <= 1)
            if len(segs) > 1:   # "dog food cat food aquarium fish toys" -> dog food | cat food | aquarium fish | toys
                cut.append(segs)
                for seg in segs:
                    add_item(seg)
                return
        if re.match(r"(?:book|call|order|message|msg|chat|reach|visit|dm|text)\s+(?:us\s+)?(?:on|via|at|through|me|us|now)?\b", x, re.I) and len(x.split()) <= 3:
            return   # "Book on WhatsApp 98200 ..." is how to reach them, not a service
        ws = x.split()
        if not (1 <= len(ws) <= 5) or not re.search(r"[A-Za-zऀ-ॿ]{2}", x):
            return
        low = x.lower()
        if low.split()[-1] in AUDIENCE and len(low.split()) <= 3 and low.split()[-1] not in ("homes", "offices"):
            return   # "school kids", "college students", "small businesses": who it is for, not what is offered
        bad = (low in ALL_CITIES or low in STATES or x in STATE_ABBR or low in FILLER_WORDS or set(low.split()) <= (FILLER_WORDS | AUDIENCE | GENERIC_WORDS) or low in WEEKDAYS or re.fullmatch(r"[\d\s.,:-]+", low)
               or set(x.split()) <= HI_FILLER)
        if not bad and low not in {i.lower() for i in items}:
            items.append(x)

    plain = [i for i, c in enumerate(chunks) if c and i != type_idx and not _is_city(c) and not OFFER_ONLY(c)]
    list_like = len(plain) >= 2
    list_parts = sum(len(SPLIT.split(chunks[i])) for i in plain)   # services still to come, counting "a, b and c" as three
    label_words = {w.lower() for w in re.findall(r"[A-Za-z]+", type_label or "")[-1:]}   # "Dental Clinic" -> clinic: a chunk ending in it describes the business
    for i, c in enumerate(chunks):
        if not c:
            continue
        if i == type_idx:
            m = LEAD_ITEMS.search(c)
            # "for X" / "with X" is only a service when more services follow ("... for kids dentistry, aligners, crowns")
            if m and not (m.group(0).lower().startswith(("for", "with")) and len(SPLIT.split(m.group(1))) < 2 and not plain):
                tail = re.split(r"\b(?:in|at|near|based\s+in|open|call|contact|mail|email)\b\s+", m.group(1), maxsplit=1, flags=re.I)[0]
                for part in SPLIT.split(tail):
                    add_item(part)
            elif (not m and list_parts >= 2 and len(c.split()) <= 3 and c.split()[-1].lower().rstrip("s") not in {d.rstrip("s") for d in DESCRIPTORS | label_words}
                  and (c.isascii() or (out["name"] and len(c.split()) <= 3 and not re.search(r"\b(?:में|मे|का|की|के|है|हैं)\b", c))) and not re.search(r"\b(?:in|at|near)\b", c, re.I) and not re.match(r"(?:a|an|the)\s", c, re.I)
                  and (name_from_chunk or not any(w[:1].isupper() and not (w.isupper() and len(w) <= 5) for w in c.split()))):
                add_item(c)   # "Speedy Motors, used cars, car service": the chunk after the name is a service, not a description
            continue
        if _is_city(c) or OFFER_ONLY(c) or (not list_like and set(re.findall(r"[A-Za-z\u0900-\u097F]+", c.lower())) <= (keys | NATIONALITY | FILLER_WORDS | HI_FILLER | GENERIC_WORDS)):
            continue   # a second mention of the business type ("सैलून और ब्यूटी पार्लर"), a city or an offer is not a service
        for part in SPLIT.split(c):
            add_item(part)
    # items from a later "offering ..." clause in other chunks are already covered; drop items that are just the offer phrases
    offer_words = [(o["text"].lower()) for o in out["offers"]]
    items = [i for i in items if not any(rx.fullmatch(i) for _, rx, _, _ in OFFER_RE) and i.lower() not in offer_words]
    if items:   # the first service of a sentence ("Custom cakes, wedding cakes ...") is capitalised by the sentence, not by being a proper noun
        w0 = items[0].split()[0]
        rest_words = items[0].split()[1:]
        others = items[1:]
        if (w0[:1].isupper() and w0[1:].islower() and all(w.islower() or not w.isalpha() for w in rest_words) and w0.lower() not in KEEP_CAPS | (NATIONALITY - {"desi", "pan", "indo", "south", "north", "continental", "asian"}) | PLACES
                and not _is_city(w0) and (len(items) == 1 or sum(o[:1].islower() for o in others) * 2 >= len(others))):
            items[0] = w0.lower() + items[0][len(w0):]

    # name: a capitalised run inside the type chunk (not a cuisine, city or type word)
    if not out["name"]:
        excl = set(keys) | NATIONALITY | WEEKDAYS | {c.lower() for c in ALL_CITIES} | FILLER_WORDS | {w.lower() for w in re.findall(r"[A-Za-z]+", type_label or "")}
        excl |= {"for", "in", "at", "with", "and", "of", "the", "best", "online", "new", "we", "our", "my", "i", "a", "an"}
        if out["city"] and raw.lower().count(out["city"].lower()) < 2:
            excl |= {w.lower() for w in out["city"].split()}   # "hardware store in Anand": Anand is the town, not the name
        if locality:
            excl |= {w.lower() for w in locality.split()}   # "Delhi Nehru Place": the area is not the business name
        if out["city"] and raw.lower().count(out["city"].lower()) >= 2:   # "Jaipur Motors in Jaipur": the first mention is part of the name
            excl.discard(out["city"].lower())
        base = LEAD_ITEMS.split(type_chunk)[0] if type_chunk else ""
        out["name"] = _title_run(re.findall(r"[A-Za-z&'-]+", base), excl, keys | GENERIC_WORDS) or _title_run(re.findall(r"[A-Za-z&'-]+", " ".join(chunks[:1])), excl, keys | GENERIC_WORDS)
        if out["name"] and out["name"].lower() in {k for k in keys}:
            out["name"] = None
    out["items"] = items[:8]
    out["cut"] = cut

    # fall back to the older sentence-style reader for anything the chunk reader missed
    old = parse_prompt(raw)
    if not out["items"]:
        out["items"] = [i for i in old["items"] if i.lower() not in FILLER_WORDS][:6]
    if not out["city"] and old.get("place"):
        out["city"] = old["place"]
    out["audience"] = old.get("audience")
    if not out["phone"] and old.get("phone"):
        out["phone"] = old["phone"]
    if not out["years"] and old.get("years"):
        out["years"] = old["years"]
    if any("ऀ" <= ch <= "ॿ" for ch in raw):
        hp = parse_hindi(raw, type_keys)
        out["city"] = out["city"] or hp["place"]
        if not out["items"]:
            out["items"] = hp["items"]
    # explicit facts win
    for key in ("name", "city", "phone", "email", "years", "audience", "hours", "address", "whatsapp"):
        if facts.get(key):
            out[key] = str(facts[key]).strip()
            out["source"][key] = "facts"
    if facts.get("services"):
        out["items"] = [str(s).strip() for s in facts["services"] if str(s).strip()]
        out["source"]["items"] = "facts"
    if facts.get("offers"):
        extra = []
        for o in facts["offers"]:
            hit = find_offers(str(o))
            extra += hit or [{"id": "custom", "text": str(o).strip(), "text_hi": str(o).strip()}]
        out["offers"] = extra
        out["source"]["offers"] = "facts"
    if facts.get("prices"):
        out["prices"] = [{"name": str(r["name"]), "price": str(r["price"])} for r in facts["prices"] if isinstance(r, dict) and r.get("name") and r.get("price")]
        out["source"]["prices"] = "facts"
    for key in ("name", "city", "items", "offers", "hours", "prices", "phone", "email", "years"):
        if out[key] and key not in out["source"]:
            out["source"][key] = "prompt"
    return out


def OFFER_ONLY(chunk):
    """True when a chunk is nothing but an offer phrase ("online booking", "free shipping")."""
    c = chunk.strip()
    return (any(rx.fullmatch(c) for _, rx, _, _ in OFFER_RE) or (bool(find_offers(c)) and len(c.split()) <= 3)
            or (bool(find_offers(c)) and len(c.split()) <= 7 and bool(re.search(r"\b(?:available|is|are|welcome|accepted|hai|free)\b", c, re.I))))
