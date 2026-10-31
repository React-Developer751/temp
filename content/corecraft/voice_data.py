"""Aggregates the per-kind voice banks and holds the shared sentence patterns.

A pattern is (items needed, facts needed, template). Facts: city, name, hours, offer, phone. The writer keeps only the patterns
whose needs are met, so a page about a business that gave no hours simply never uses an "open until" sentence.
"""
from .voice_a import BEAUTY, FITNESS, FOOD, HEALTH
from .voice_b import EDUCATION, HOME, RETAIL, SOFTWARE
from .voice_c import CREATIVE, EVENTS, ORG, PRO, TRADES, TRAVEL

VOICE = {"food": FOOD, "health": HEALTH, "beauty": BEAUTY, "fitness": FITNESS, "retail": RETAIL, "software": SOFTWARE, "education": EDUCATION,
         "home": HOME, "trades": TRADES, "travel": TRAVEL, "events": EVENTS, "creative": CREATIVE, "pro": PRO, "org": ORG}

HERO_TITLE = [
    (1, (), "{I1}{place}"),
    (1, ("name",), "{Name}: {i1}{place}"),
    (1, (), "{I1}{place}: {tail}"),
    (2, (), "{I1} and {i2}{place}"),
    (2, ("city",), "{city_s} {i1} and {i2}"),
    (2, ("name",), "{Name}: {i1} and {i2}{place}"),
    (2, (), "{I1} and {i2}, {tail}"),
    (3, (), "{I1}, {i2} and {i3}{place}"),
    (3, ("name",), "{Name} for {i1}, {i2} and {i3}{place}"),
    (0, ("noitems",), "{Label}{place}"),
    (0, ("name", "noitems"), "{Name}{place}: {Label}"),
    (1, ("name", "city"), "{Name}, {city}: {Label}"),
]

HERO_SUB = [
    (1, (), "{subj} {verb} {list}{place}. {closer}"),
    (1, ("hours",), "{subj} {verb} {list}{place}, open {hours}."),
    (1, ("offer",), "{subj} {verb} {list}{place}, with {offers_list_l}."),
    (2, (), "Looking for {i1}{place}? {subj} {verb} {it1}, along with {i2}."),
    (1, (), "{subj} {verb} {list}{place}."),
    (1, (), "{come} {i1}{place}. {closer}"),
    (2, ("city",), "{I1} and {i2} in {city}. {closer}"),
    (1, ("hours", "offer"), "{Offer1}, open {hours}: {subj} {verb} {list}{place}."),
    (0, ("noitems",), "{Label}{place}. {closer}"),
    (0, ("norest",), "{closer} {invite}"),
    (0, ("norest", "offer"), "{Offers_sentence} {closer}"),
    (0, ("norest",), "{act1} and tell us what you need."),
]

ABOUT_A = [
    (1, (), "{subj} {verb} {list}{place}. {closer}"),
    (1, (), "{closer} {subj} {verb} {list}{place}."),
    (2, (), "On the list: {list}. {subj} {verb} them{place}. {closer}"),
    (2, (), "It starts with {i1}. {subj} {verb} {rest_list} too{place}."),
    (1, (), "People come to {subj_obj} for {list2}{place}. {closer}"),
    (1, ("offer",), "{subj} {verb} {list}{place}, with {offers_list_l}. {closer}"),
    (2, (), "{I1} and {i2}: {subj} {verb} them{place}. {closer}"),
    (1, (), "One focus: {list}{place}. {closer}"),
    (0, ("noitems",), "{Label}{place}. {closer}"),
    (0, ("noitems",), "{closer} {invite}"),
]

ABOUT_B = [
    (0, ("hours",), "We're open {hours}. {closer2}"),
    (0, ("offer",), "{Offers_sentence} {closer2}"),
    (0, (), "{invite} {closer2}"),
    (0, ("city",), "You'll find {subj_obj} in {city}. {invite}"),
    (0, ("phone",), "Call {phone} to {act1_l}. {closer2}"),
    (0, ("hours", "offer"), "{Offers_sentence} We're open {hours}."),
    (0, ("city", "hours"), "You'll find {subj_obj} in {city}, open {hours}. {invite}"),
    (0, ("city", "offer"), "In {city}: {offers_list_l}. {invite}"),
    (0, (), "{closer2} {invite}"),
]

CTA_TITLES = ["Ready when you are", "Let's talk", "Your next step is one message away", "Come and see for yourself", "Start with a conversation",
              "Tell us what you need", "Say hello", "We'd like to hear from you"]
STATS_TITLES = ["At a glance", "The basics", "Good to know", "Quick facts", "In short", "Details at a glance", "Where and when", "Find us"]
STEPS_TITLES = ["How it works", "Getting started", "Three simple steps", "What happens next", "From first message to finish"]
FAQ_TITLES = ["Questions we get asked", "Frequently asked questions", "Good questions", "Before you ask", "Quick answers"]
BLOG_TITLES = ["From the journal", "Notes and guides", "Worth reading", "Short guides", "Our notes"]
FEATURE_TITLES = {
    "food": ["On the menu", "What we serve", "From the kitchen", "Menu highlights", "What to order"],
    "health": ["What we treat", "Care we offer", "Treatments", "How we can help you", "Services"],
    "beauty": ["Services", "What we offer", "Our treatments", "Book a service", "Looks and treatments"],
    "fitness": ["Classes and training", "What you can train", "Sessions", "Programmes", "Ways to train"],
    "retail": ["What we stock", "In the store", "Browse the range", "What you'll find", "Shop by category"],
    "software": ["What it does", "Features", "Built for your workflow", "What you can automate", "Inside the product"],
    "education": ["What we teach", "Courses and batches", "Subjects", "Programmes", "Learn with us"],
    "home": ["What we handle", "Services", "Jobs we take on", "How we can help", "Our work"],
    "trades": ["What we fix", "Jobs we take on", "Services", "Repairs and installs", "Our work"],
    "travel": ["Trips and services", "Where we can take you", "What we plan", "Services", "Ways to travel"],
    "events": ["What we plan", "Services", "Events we run", "Ways we can help", "Our work"],
    "creative": ["What we make", "Our work", "Services", "Projects we take on", "Ways to work together"],
    "pro": ["How we can help", "Services", "Areas we advise on", "What we handle", "Our expertise"],
    "org": ["Our work", "Programmes", "What we do", "Ways to help", "Projects"],
}


# Neutral lines safe for every kind of business. They widen each pool, so two pages of the same niche share fewer sentences.
GENERIC = dict(
    closers=["Ask if anything is unclear.", "A real person replies to every message.", "Take a look around and ask us anything.", "No pressure; ask whatever you like.",
             "We'd rather you knew exactly what to expect.", "Tell us what matters most to you.", "Small questions are welcome too.", "Message first if you prefer."],
    invites=["Send a short message and we'll take it from there.", "Ask us anything before you decide.", "Tell us what you have in mind.", "Tell us what suits you and we'll confirm.",
             "Ask for details before you commit.", "Tell us who it is for and we'll suggest options.", "Ask what's included before you decide.", "Message us a few notes and we'll reply."],
    highlights=[("Straight answers", "Ask and we'll say it plainly."), ("A real person replies", "Not a form that goes nowhere."), ("Clear next steps", "You'll know what comes next."),
                ("Questions welcome", "Big or small."), ("No hard sell", "Take your time."), ("Easy to reach", "Message or call."), ("Local and personal", "Run by people you can talk to."),
                ("Details explained", "Before anything begins.")],
    blog=[("How to choose a good {label_l}", "Five questions worth asking before you decide."), ("Making the most of your first visit", "A short list to bring with you."),
          ("Questions to ask before you book", "Plain answers beat long brochures."), ("What a good first conversation covers", "And what to expect afterwards."),
          ("Why we answer every message", "Replies are part of the service."), ("A short guide to {i1}", "The basics, in plain words."), ("Planning ahead", "How to give yourself time."),
          ("Small things that make a difference", "Notes from everyday experience."), ("What to bring when you get in touch", "A short list that saves a second message."),
          ("Reading the small print", "Where to look and what to ask."), ("When to ask for a second opinion", "And how to do it politely."), ("Keeping track of your plans", "A simple way to stay organised."),
          ("What a fair price looks like", "Questions that make quotes easier to compare."), ("Why local matters", "A few reasons to choose someone nearby."), ("How long things really take", "Setting expectations on both sides."),
          ("Notes on getting started", "The first steps, without the jargon.")],
    faq=[("Can I change my plans?", ["Tell us as early as you can and we'll look at what's possible.", "Message us and we'll explain the options."], None, None),
         ("Do you reply to messages?", ["Yes; use the contact details on this page and we'll reply.", "Send a message and you'll hear from us."], None, None),
         ("Can I ask questions before I decide?", ["Of course; that's what the first conversation is for.", "Yes; ask as many as you like."], None, None),
         ("How do I pay?", ["Ask us when you book and we'll explain the options.", "Message us and we'll tell you how payment works."], None, None),
         ("Is there anything I should prepare?", ["Ask us and we'll tell you what to have ready.", "We'll tell you what to bring or prepare when you get in touch."], None, None),
         ("Can someone else book for me?", ["Yes; just tell us who the booking is for.", "Of course; share the details and we'll take it from there."], None, None),
         ("What if I'm not sure what I need?", ["Tell us what you're trying to achieve and we'll point you in the right direction.", "Describe the situation and we'll suggest where to start."], None, None)],
    feat=["We'll explain how {i} {works} and what to expect, before you decide.", "Tell us what you're after and we'll show you where {i} {fits} in.", "Curious about {i}? We're happy to talk {it} through.",
          "{I}, explained clearly, with the details you need to decide.", "Not sure about {i}? A short conversation usually settles it.", "Bring your questions about {i}; a real person answers.",
          "We'll explain {i} in plain words, without the jargon.", "One message about {i} is enough to get a clear answer."],
)


# verbs of the business itself where the kind's default would sound wrong ("We shoot pottery", "We fix new tyres")
TYPE_VERBS = {
    "software": (("builds", "delivers"), ("build", "deliver")),
    "bakery": (("bakes", "sells"), ("bake", "sell")), "pottery": (("makes", "teaches"), ("make", "teach")), "photography": (("shoots", "captures"), ("shoot", "capture")),
    "design": (("designs", "creates"), ("design", "create")), "printing": (("prints", "produces"), ("print", "produce")), "tyres": (("fits", "repairs"), ("fit", "repair")),
    "taxi": (("provides", "runs"), ("provide", "run")), "hotel": (("offers", "hosts"), ("offer", "host")), "sweets": (("makes", "sells"), ("make", "sell")),
    "icecream": (("serves", "scoops"), ("serve", "scoop")), "pharmacy": (("stocks", "supplies"), ("stock", "supply")), "optical": (("fits", "stocks"), ("fit", "stock")),
    "gaming": (("runs", "hosts"), ("run", "host")), "tenthouse": (("rents out", "sets up"), ("rent out", "set up")), "coworking": (("offers", "runs"), ("offer", "run")),
    "realestate": (("sells", "lists"), ("sell", "list")), "insurance": (("advises on", "arranges"), ("advise on", "arrange")), "recruitment": (("finds", "places"), ("find", "place")),
    "catering": (("cooks", "caters"), ("cook", "cater")), "courier": (("delivers", "moves"), ("deliver", "move")), "security": (("installs", "maintains"), ("install", "maintain")),
    "landscape": (("looks after", "plants"), ("look after", "plant")), "tailor": (("stitches", "alters"), ("stitch", "alter")), "mehendi": (("designs", "applies"), ("design", "apply")),
    "tattoo": (("designs", "inks"), ("design", "ink")), "movers": (("handles", "moves"), ("handle", "move")), "garage": (("fixes", "services"), ("fix", "service")),
    "jewellery": (("sells", "crafts"), ("sell", "craft")), "clothing": (("stocks", "sells"), ("stock", "sell")), "books": (("stocks", "sells"), ("stock", "sell")),
}
SERVICE_LIKE = r"\b(?:ride|rides|finance|financing|servicing|service|services|repair|repairs|installation|installations|delivery|booking|trial|demo|consultation|maintenance|training|lessons?|classes|alignment|fitting|cleaning|customisation|customization|warranty|exchange|alteration|alterations|stitching|exam|test|tests)\b"
