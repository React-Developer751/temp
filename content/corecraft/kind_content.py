"""Copy families for kinds of business that template_data does not cover (care, pro, hosting, org),
frames that work for ANY phrase the user typed (singular, plural or uncountable), and the fixed
page blocks per kind: steps, FAQ and highlights. Nothing here states a fact about a specific business:
no prices, hours, awards, counts or testimonials."""
from .template_data import NICHE

NICHE["care"] = {
    "main": [], "extra": [], "adj": ["gentle", "caring", "friendly", "experienced"],
    "hero": ["Gentle care for {a}", "Friendly experts for {a}", "Caring for you, one visit at a time", "Better {a}, kinder care", "Feel better with {a}"],
    "tagline": ["{J} care for {a} and {b}.", "{A}, {b}, and a warm welcome.", "Experienced people, honest advice, and {a} done well.", "Your comfort comes first with every one of our {a}.", "Book {a} in minutes and walk in at ease."],
    "feature": ["Our {a} start with a conversation and a clear plan.", "Every one of our {a} is explained in plain language.", "{J} care for your {a}, from first visit to follow-up.", "Comfortable, unhurried {a} with a team that listens.", "Ask us about {a} and get a straight answer.", "We tailor our {a} to what you actually need.", "Pair our {a} with {b} for lasting results."],
    "open": ["We provide {a}, {b}, and {c} with care and attention.", "Our team brings real experience to {a} and {b}.", "People visit us for {a} and stay for the way we treat them.", "{A} and {b} are at the heart of what we do."],
    "close": ["We explain every step so you always know what comes next.", "Your comfort and privacy come first, every visit.", "Booking is simple, and follow-up is part of the service.", "Questions are always welcome; just ask.", "We take the time to listen before we do anything else."],
}
NICHE["pro"] = {
    "main": [], "extra": [], "adj": ["clear", "practical", "trusted", "personal"],
    "hero": ["Advice you can act on", "Clear {a}, honest advice", "Trusted help with {a}", "{A} handled properly", "Straight answers on {a}", "Experienced hands for {a}"],
    "tagline": ["Practical {a} from people who know the details.", "{A}, {b}, and honest advice.", "Clear guidance on {a} and {b}.", "From the first call to the final result: {a}.", "Experienced help with {a}, without the jargon."],
    "feature": ["Plain-language guidance on {a}.", "Every one of our {a} starts with listening.", "Transparent pricing for {a}, agreed up front.", "Personal attention on every one of your {a}.", "Get {a} handled by people who do it every day.", "We keep you informed at each step of your {a}.", "Combine {a} with {b} for a complete plan."],
    "open": ["We help clients with {a}, {b}, and {c}.", "Our team handles {a} and {b} from start to finish.", "Clients come to us for {a} and stay for the clarity.", "{A}, {b}, and {c} are what we do every day."],
    "close": ["We listen first, explain clearly, and keep you informed.", "Confidentiality and clear communication come as standard.", "Fees are explained up front, so there are no surprises.", "Reach out and we will tell you honestly how we can help."],
}
NICHE["hosting"] = {
    "main": [], "extra": [], "adj": ["memorable", "hassle-free", "personal", "well-planned"],
    "hero": ["Plan {a} without the stress", "Memorable {a}, made easy", "Your {a}, handled with care", "Where great {a} begin", "{A} worth remembering", "Leave the {a} to us"],
    "tagline": ["{J} {a} and {b}, planned around you.", "From the first idea to the last detail: {a}.", "Everything for {a}, in one place.", "{A}, {b}, and a team that cares about the details.", "Sit back while we take care of {a}."],
    "feature": ["Tailor-made {a}, planned around your wishes.", "Every one of our {a} is shaped to fit your budget.", "We handle the details of your {a} so you do not have to.", "Browse our {a} and pick what suits you.", "{J} {a} with a friendly team on hand.", "Mix and match {a} with {b} for something special."],
    "open": ["We organise {a}, {b}, and {c} with care.", "From {a} to {b}, we look after every detail.", "Guests choose us for {a} and remember us for the welcome.", "{A} and {b} are our specialty."],
    "close": ["Tell us your plan, and we will shape the rest.", "A friendly team looks after you from start to finish.", "Every detail is checked, so you can enjoy the moment.", "Get in touch and we will put together a plan."],
}
NICHE["org"] = {
    "main": [], "extra": [], "adj": ["community-led", "transparent", "local", "dedicated"],
    "hero": ["Together, we can change lives", "Small acts, lasting change", "Support our {a}", "Join our {a} today", "Make a difference with {a}", "Change starts with {a}"],
    "tagline": ["{J} {a} that bring real change.", "Be part of our {a} and {b}.", "Your support powers our {a}.", "Turning care into action through {a}.", "{A} and {b}, led by the community."],
    "feature": ["Join our {a} and help someone today.", "Our {a} are run by dedicated volunteers.", "See how our {a} make a difference.", "Every contribution supports our {a}.", "Learn how you can take part in our {a}.", "We share the story behind each of our {a}."],
    "open": ["We run {a}, {b}, and {c} for the community.", "Our work centres on {a} and {b}.", "People join us for {a} and stay for the cause.", "{A}, {b}, and {c} are at the heart of our mission."],
    "close": ["Every donation and every hour of help is put to good use.", "We keep our work open, honest, and accountable.", "Get involved, because change starts with people.", "Volunteers and donors make all of this possible."],
}

# Frames for phrases the user typed: must read well with "teeth whitening", "braces" and "GST filing" alike.
ANY = {
    "hero": ["{A} you can trust", "Expert help with {a}", "{A}, done right", "Your trusted partner for {a}", "Straightforward {a}, made simple",
             "Care and know-how for {a}", "{A}: simple, honest, and well done", "Make {a} the easy part", "Real people, real help with {a}", "{A} without the hassle", "Better results with {a}"],
    "tagline": ["Friendly experts for {a} and {b}.", "Everything you need for {a}.", "{A} and {b}, handled with care.", "Clear advice on {a} and more.", "Trusted help with {a}, from start to finish.",
                "{A}, {b}, and {c}, all under one roof.", "Honest help with {a} and {b}.", "From {a} to {b}, we have you covered.", "Where {a} gets the attention it deserves.",
                "Good advice and good service for {a}.", "Your questions about {a}, answered."],
    "feature": [
        "Expert help with {a}, from the first call to the final result.", "{A}: clear advice, fair pricing, and friendly follow-up.",
        "Everything you need to know about {a}, explained simply.", "Ask us about {a} and get a straight answer.",
        "Get {a} handled by people who do it every day.", "Book {a} online or call us, whichever is easier.",
        "Honest advice on {a}, with no pressure.", "We make {a} simple, from start to finish.", "Personal attention for all your questions about {a}.",
        "Clear steps, clear prices, and no surprises with {a}.", "Learn what {a} involves before you decide.", "Tell us about your {a} needs and we will take it from there.",
        "We keep you updated at every stage of {a}.", "{A} done carefully, with time for your questions.", "Start with a quick chat about {a}.",
        "Straight talk and sensible options for {a}.", "Rely on us for {a}, week after week.", "Whatever you need from {a}, just ask.",
    ],
    "open": ["We help people with {a}, {b}, and {c}.", "From {a} to {b}, we are here for you.", "{A}, {b}, and {c} are what we do every day.", "Our team handles {a} and {b} from start to finish.",
             "Many of our customers come to us for {a} and {b}.", "We specialise in {a}, along with {b} and {c}.", "Day to day, we focus on {a}, {b}, and {c}.", "Our work covers {a} and {b}, and we are happy to talk about {c}."],
    "close": ["We listen first, explain clearly, and keep you informed.", "Get in touch and we will tell you honestly how we can help.", "Clear communication and fair prices come as standard.",
              "Every enquiry gets a personal reply.", "We take the time to understand what you need.", "You will always know what to expect from us.", "No pressure, no jargon, just clear help.",
              "Tell us what you need and we will point you in the right direction."],
}

STEPS = {
    "care": [("Book a visit", "Pick a time online or call us and tell us what you need."), ("Meet the team", "We listen, assess, and explain your options in plain language."), ("Follow up", "We check in afterwards so you keep making progress.")],
    "pro": [("Tell us what you need", "Share your situation in a short call or message."), ("Get a clear plan", "We explain the options, the steps, and the fees up front."), ("We take it from here", "We do the work and keep you updated until it is done.")],
    "business": [("Tell us the problem", "Call or message us with a few details about the job."), ("Get a quote", "We explain what the work involves and what it is likely to cost."), ("We get it done", "A skilled professional completes the work and checks it with you.")],
    "shop": [("Browse", "Look through the range online or in store."), ("Choose", "Pick what you like and ask us anything."), ("Enjoy", "Take it home, or ask us about delivery.")],
    "restaurant": [("Pick your favourites", "Look through the menu and choose what you fancy."), ("Order or drop in", "Order ahead or come by and take a seat."), ("Enjoy", "Good food, served the way it should be.")],
    "education": [("Ask for a demo", "Tell us what you want to learn and ask about a trial."), ("Meet your mentor", "We match you with a teacher and a plan."), ("Learn and grow", "Practise, get feedback, and track your progress.")],
    "portfolio": [("Share your idea", "Tell us what you have in mind and when you need it."), ("We plan and create", "We turn the idea into a clear plan, then make it."), ("Review and finalise", "You give feedback, and we polish until it is right.")],
    "hosting": [("Tell us your plan", "Share your dates, ideas, and rough budget."), ("We shape the details", "We put together options and look after the arrangements."), ("Enjoy the moment", "Relax while the team takes care of the day.")],
    "fitness": [("Visit and try", "Come in, look around, and ask us anything."), ("Get your plan", "We suggest a routine that fits your goals and level."), ("Train and track", "Show up regularly and watch your progress build.")],
    "tech": [("Sign up", "Create an account or ask us for a demo."), ("Connect your tools", "Bring your data and apps together in one place."), ("Start shipping", "Work faster with fewer manual steps.")],
    "org": [("Learn about our work", "Read about what we do and who we help."), ("Choose how to help", "Donate, volunteer, or spread the word."), ("See the impact", "We share updates so you know where your support goes.")],
}
FAQ_THIRD = {
    "care": ("What should I bring to my first visit?", "Bring any records or documents you have and tell us what you would like help with."),
    "pro": ("What information should I have ready?", "Any documents related to your case or project help; we will tell you exactly what we need."),
    "business": ("Do you give estimates?", "Get in touch with details of the job and we will explain what the work involves and the likely cost."),
    "shop": ("Can I return or exchange something?", "Ask us about the return and exchange policy before you buy; we are happy to explain."),
    "restaurant": ("Can I order in advance?", "Contact us with your requirements and we will confirm what is possible."),
    "education": ("Can I try a class first?", "Ask us about a demo session and we will tell you what is available."),
    "portfolio": ("How far ahead should I book?", "The earlier the better; contact us with your date and we will confirm availability."),
    "hosting": ("How far ahead should I plan?", "The earlier the better; contact us with your dates and we will confirm availability."),
    "fitness": ("Do I need any experience?", "No. Sessions suit different levels, and we will help you find the right starting point."),
    "tech": ("Can I try before I commit?", "Ask us about a demo or trial and we will tell you what is available."),
    "org": ("How can I help?", "You can donate, volunteer, or spread the word; get in touch to learn more."),
}
FAQ_COMMON = [
    ("How do I get started?", "Use the button on this page or the contact details, tell us what you need, and we will reply with the next steps."),
    ("What does it cost?", "That depends on what you need. Get in touch and we will explain the options clearly before you decide."),
]
FAQ_LAST = ("How can I contact you?", "Use the contact details on this page and you will hear from us.")

HIGHLIGHTS = {
    "care": [("Caring team", "Friendly people who explain every step."), ("Clear advice", "Plain-language answers to your questions."), ("Easy booking", "Simple to reach and simple to schedule.")],
    "pro": [("Clear guidance", "Straight answers without the jargon."), ("Personal attention", "Your matter is handled by people who know it."), ("Up-front fees", "We explain costs before work begins.")],
    "business": [("Honest quotes", "You know what the job involves before it starts."), ("Skilled people", "Work done properly and checked with you."), ("Easy to reach", "Call or message and we will respond.")],
    "shop": [("Chosen with care", "A range picked for quality and value."), ("Friendly help", "Ask us anything before you buy."), ("Easy to order", "Simple ways to shop and get in touch.")],
    "restaurant": [("Made with care", "Good ingredients and honest cooking."), ("Warm welcome", "A place to relax with friends and family."), ("Easy to order", "Order ahead or drop in.")],
    "education": [("Patient teaching", "Small steps, clear explanations."), ("Real practice", "Learn by doing, with feedback."), ("Progress you can see", "Regular check-ins keep you on track.")],
    "portfolio": [("Thoughtful work", "Every project starts with listening."), ("Clear process", "You know what happens at each stage."), ("Made to fit", "Work shaped around your needs.")],
    "hosting": [("Every detail covered", "We look after the arrangements."), ("Planned around you", "Your wishes shape the plan."), ("A friendly team", "Easy to talk to, easy to work with.")],
    "fitness": [("Friendly coaches", "Support for every level."), ("Real plans", "Routines built around your goals."), ("Easy to start", "Come in and try it for yourself.")],
    "tech": [("Simple to use", "Clear tools that stay out of your way."), ("Secure by design", "Built with safety in mind."), ("Real support", "Reach a person when you need one.")],
    "org": [("Open and honest", "We share what we do and why."), ("Community-led", "Our work is shaped by the people we serve."), ("Everyone can help", "Donate, volunteer, or spread the word.")],
}
NAME_BANK = {
    "care": ["Bright", "Gentle", "Serene", "Harmony", "Evergreen", "Wellspring"],
    "pro": ["Summit", "Clarity", "Anchor", "Meridian", "Vertex", "Prime"],
    "hosting": ["Horizon", "Voyage", "Compass", "Golden", "Seasons", "Wanderly"],
    "org": ["Hope", "Unity", "Sunrise", "Asha", "Seva", "Bridge"],
    "business": ["Prime", "Anchor", "Reliable", "Swift", "Trusty", "Metro"],
}

# typical offerings that top up a type's own list (never presented as facts; see needs_review)
KIND_COMMON = {
    "care": "consultations check-ups treatments plans".split(),
    "pro": "consultations plans assessments".split(),
    "business": "inspections repairs upgrades packages".split(),
    "hosting": "packages options experiences plans".split(),
    "org": "programs events drives campaigns workshops".split(),
    "shop": "collections gifts sets bundles".split(),
    "restaurant": "specials combos snacks drinks".split(),
    "education": "classes lessons workshops sessions".split(),
    "portfolio": "projects sessions packages collections".split(),
    "fitness": "classes sessions programs plans".split(),
    "tech": "workflows dashboards integrations reports".split(),
}

# everyday retail (grocery, pharmacy, books, electronics, furniture, pets, optical): plain, practical tone
NICHE["store"] = {
    "main": [], "extra": [], "adj": ["fresh", "reliable", "affordable", "everyday"],
    "hero": ["Everyday {a}, fair prices", "Find the {a} you need", "{J} {a}, stocked daily", "{A} for the whole family", "Your neighbourhood stop for {a}", "Shop {a} with confidence"],
    "tagline": ["Quality {a} at fair prices.", "Everything from {a} to {b}.", "{J} {a} and {b}, close to home.", "Stocked with care: {a} for every need.", "{A} and {b}, all in one place."],
    "feature": ["Browse our {a} and pick what you need.", "Our {a} are chosen for quality and value.", "Ask us about {a}; we are happy to help.", "{J} {a} for every need.", "Looking for {a}? Chances are we have them.", "Pair our {a} with {b} and save a trip."],
    "open": ["We stock {a}, {b}, and {c} for everyday life.", "People visit us for {a} and come back for the {b}.", "From {a} to {b}, we keep the shelves ready.", "{A} and {b} are what we do best."],
    "close": ["Friendly help is always on hand.", "We keep prices fair and quality high.", "Ask us if you cannot find something.", "Drop in, or get in touch to ask about stock.", "Regular customers tell us they come back for the service."],
}
STEPS["store"] = STEPS["shop"]
FAQ_THIRD["store"] = FAQ_THIRD["shop"]
HIGHLIGHTS["store"] = HIGHLIGHTS["shop"]
NAME_BANK["store"] = ["Fresh", "Daily", "Everyday", "Prime", "Metro", "Green"]
KIND_COMMON["store"] = []

# neutral nouns for a business whose type is not in the list: usable by every business of that copy family
KIND_NEUTRAL = {
    "care": "consultations check-ups treatments plans sessions programs".split(),
    "pro": "consultations plans assessments reports documents guides".split(),
    "business": "installations repairs inspections upgrades packages services".split(),
    "hosting": "packages options experiences plans events stays".split(),
    "org": "programs events drives campaigns workshops".split(),
    "shop": "collections gifts sets bundles pieces accessories essentials favourites".split(),
    "store": "essentials favourites bundles supplies".split(),
    "restaurant": "specials combos snacks drinks desserts".split(),
    "education": "classes lessons workshops sessions tutorials".split(),
    "portfolio": "projects sessions packages collections".split(),
    "fitness": "classes sessions programs plans workouts".split(),
    "tech": "workflows dashboards integrations reports".split(),
}
