"""Voice changes for sub-niches whose kind voice would sound wrong: a bakery is not a table-booking restaurant, yoga is not a rep-counting gym."""
from .voice_data import VOICE

_FOOD_FAQ = {f[0]: f for f in VOICE["food"]["faq"]}
_FIT_FAQ = {f[0]: f for f in VOICE["fitness"]["faq"]}

BAKERY = dict(
    who="customers", does=("bakes", "makes"), do=("bake", "make"), ing=("Baking", "Making"), come="Order",
    act=("Place an order", "See what's baked"), act_online=("Order online", "See what's baked"),
    book_how_online="Order online", book_how="Message us to place an order",
    tails=["baked fresh", "made for the occasion", "sweet and simple", "from the oven", "for every celebration"],
    closers=["Order early for a big day.", "Fresh from the oven is the best kind.", "Save a slice for later.", "Ask the team what is baked today.", "Something sweet makes any day better.",
             "Tell us the occasion and we'll help you choose.", "Every bake is better shared.", "Bring a sweet tooth."],
    invites=["Tell us the date and how many you need to feed.", "Message us the occasion and we'll suggest what suits it.", "Ask what is fresh today.", "Tell us about any dietary need before you order.",
             "Share the day you need it and we'll confirm what's possible.", "Ask for a recommendation when you visit.", "Order ahead for a celebration.", "Message us your idea and we'll talk it through."],
    feat=["Ask the team what goes into {i}; they like the question.", "A good place to start if you like {i}.", "Order {i} for the occasion, or keep {it} to yourself.",
          "Curious about {i}? Ask, and we'll talk you through {it}.", "Tell us the date and we'll say what we can do with {i}.", "{I} {is} better shared, so order a little more than you think you need.",
          "Pair {i} with something from the rest of the bakery.", "If {i} {is} why you came, say so when you order."],
    steps=[[("Choose what you like", "Start with {list2_or}, or ask the team for ideas."), ("Tell us the date", "Give us the day and the size, and we'll confirm."), ("Enjoy it fresh", "Collect it, or let someone else do the honours.")],
           [("Share your idea", "Flavour, size, message and the date."), ("We plan the bake", "We confirm the details with you."), ("Celebrate", "Slice, share and enjoy.")],
           [("Pick your treat", "Look through {list2_or} and decide."), ("{book_how}", "Tell us the day you need it."), ("Pick it up and enjoy", "Fresh and ready for the day.")]],
    faq=[("Can I order something for a particular day?", ["Tell us the date, the size and what you'd like, and we'll say what we can do.", "Message us the day you need it and we'll confirm."], None, None),
         ("How can I order something?", ["{book_how}, and tell us the date.", "Use the contact details on this page and say what you'd like."], "online_order", ["You can order online, or contact us directly.", "Online ordering is available whenever it suits you."]),
         ("Can I collect my order?", ["Ask us when you order and we'll tell you what's possible.", "Message us and we'll arrange a time."], "pickup", ["Yes, pickup is available; tell us when you'll come.", "You can pick up your order; message us the time."]),
         _FOOD_FAQ["Do you offer delivery or takeaway?"], _FOOD_FAQ["I have an allergy. Can you help?"], _FOOD_FAQ["When are you open?"], _FOOD_FAQ["Where are you?"],
         ("Can I ask about {i1}?", ["Of course; ask us what goes into {it1} and how to order.", "Yes; tell us what you'd like to know about {i1}."], "item", None)],
    highlights=[("Baked fresh", "Made for the day, not for the shelf."), ("Made to order", "Tell us the occasion and we'll plan around it."), ("Ask the team", "They like questions about what's baked."),
                ("For celebrations", "Share the date and the numbers."), ("Something sweet", "A treat for any day."), ("Easy to order", "Say what you'd like and we'll take it from there.")],
    blog=[("Ordering a cake for a celebration", "How early to order and what to tell the baker."), ("What to try on a first visit", "Start with {i1}, then follow your sweet tooth."),
          ("Planning a birthday spread", "Choose the day, the numbers and one bake everyone will share."), ("A short guide to {i1}", "What it is, how it is usually enjoyed and what goes with it."),
          ("Why fresh matters", "The case for {i1} on the day {they1} {is1} baked."), ("Pairing {i1} with the rest of the bakery", "A few simple combinations to try."),
          ("Choosing for a crowd", "Sizes, slices and ordering without worry."), ("Sweet or savoury first? A debate", "On starting with {i1} or finishing with {it1}.")],
    cta_text=["{act1} and tell us the occasion.", "Something sweet? {act1}.", "Your order is one message away.", "Ask about {i1} when you {act1_l}.", "Tell us the date; we'll handle the rest.",
              "{act1}, or message us your plans.", "Plan a celebration around {i1}.", "Start with a treat; finish with another."],
    _generic=True,
)

YOGA = dict(
    who="students", does=("teaches", "guides", "holds"), do=("teach", "guide", "hold"), ing=("Teaching", "Guiding"), come="Practise with us for",
    act=("Start a free class", "Book a class"), act_online=("Book a class online", "See the schedule"),
    book_how_online="Book a class online", book_how="Message us to book a class",
    tails=["breath by breath", "at your own pace", "calm and steady", "on the mat", "for body and mind"],
    closers=["Show up; we'll guide the rest.", "Every body starts somewhere.", "A little practice goes a long way.", "Bring a mat if you have one.", "Teachers watch your breath, not the clock.",
             "Progress is felt before it is seen.", "No experience needed to start.", "Come once and see how it feels."],
    invites=["Tell us your goal and we'll point you to the right class.", "Ask about a first class and see if it suits you.", "Message us your schedule and we'll plan around it.",
             "Tell the teacher about any injury before you start.", "Ask what to wear and bring.", "Bring a friend; it helps to start together.", "Ask us which class is best for a beginner.",
             "Tell us how many days a week you can practise."],
    feat=["{I} {is} guided from the first breath to the last; ask which level suits you.", "New to {i}? Tell the teacher and they'll guide you.", "Ask what a {i} class looks like before you join.",
          "{I}: show up, follow the teacher, and notice how you feel.", "We'll explain {i} before you begin and adjust {it} as you go.", "Curious about {i}? Come for a class and see.",
          "Tell us your goal and we'll show you where {i} fits.", "{I} {is} for every level; the teacher adjusts as you go."],
    steps=[[("Book a class", "{book_how}, and tell us your goal."), ("Meet your teacher", "We'll talk about your experience and any injuries."), ("Practise and settle in", "Show up, follow the guidance and notice the change.")],
           [("Try a class", "Ask about a first class and pick a time."), ("Find your style", "We suggest {list2_or} to fit your goal and your week."), ("Keep going", "Regular classes, regular check-ins.")],
           [("Say hello", "Message us your goal and schedule."), ("Settle in and learn", "The teacher introduces {list2_or} and checks your alignment."), ("Build the habit", "Come back; practice is built class by class.")]],
    faq=[("Do I need experience?", ["No; teachers adjust every class to your level.", "Tell the teacher you are new and they'll guide you from the start."], None, None),
         ("Can I try a class first?", ["Ask us when you book and we'll tell you what is available.", "Message us and we'll arrange the first visit."], "free_trial", ["Yes, a free first class is available; ask us to book it.", "You can start with a free class."]),
         ("What should I wear and bring?", ["Comfortable clothes you can move in; bring water and a mat if you have one.", "Wear what you can stretch in; bring water."], None, None),
         _FIT_FAQ["I have an injury. Can I still train?"], _FIT_FAQ["How do I book?"], _FIT_FAQ["When are you open?"], _FIT_FAQ["Where are you?"],
         ("Can I ask about {i1}?", ["Of course; ask what a class looks like.", "Yes; tell us what you'd like to know about {i1}."], "item", None)],
    highlights=[("Teacher-led", "Someone is watching your alignment."), ("Every level", "Classes scale to you."), ("Calm space", "Slow down and breathe."), ("Easy to start", "Come once and see."),
                ("Feel the change", "Small shifts that add up."), ("Practise together", "Bring a friend.")],
    blog=[("Starting out: your first month", "What to expect, how often to come and how to ease in."), ("What to know before {i1}", "A short guide for beginners."), ("{I1} vs {i2}: which first?", "A plain comparison."),
          ("Rest matters as much as {i1}", "Sleep, food and quiet days."), ("Practice around a busy week", "How to keep the habit when life gets full."), ("Questions to ask a teacher", "Before you commit to anything."),
          ("How to notice progress", "Simple signs that tell the truth."), ("Warming up properly for {i1}", "The five minutes that protect the next hour.")],
    cta_text=["{act1} and tell us your goal.", "Try {i1} once and see.", "Your first class starts with a message.", "{act1}; we'll guide the rest.", "Ask which class suits a beginner.",
              "Ready? {act1}.", "Start with {i1}.", "Show up; we'll handle the rest."],
    _generic=True,
)

def _swap(x, pairs):
    if isinstance(x, str):
        for a, b in pairs:
            x = x.replace(a, b)
        return x
    if isinstance(x, (list, tuple)):
        return type(x)(_swap(y, pairs) for y in x)
    return x


SWEETS = {k: _swap(v, [("See what's baked", "See the sweets"), ("Ordering a cake for a celebration", "Ordering sweets for a celebration"), ("Order early for a big day", "Order early for a festival"),
                       ("Fresh from the oven", "Fresh from the kitchen"), ("Save a slice for later", "Save a piece for later"), ("Slice, share and enjoy", "Share and enjoy"), ("Planning a birthday spread", "Planning a festival spread"),
                       ("what's baked", "what's fresh"), ("what is baked today", "what is fresh today"), ("baked fresh", "made fresh"), ("Baked fresh", "Made fresh"), ("from the oven", "from the kitchen"),
                       ("We plan the bake", "We plan the order"), ("Baking", "Making"), ("bakes", "makes"), ("bake", "make"), ("Bake", "Make"), ("bakery", "shop"), ("a slice", "a piece"), ("baked", "made")])
          for k, v in BAKERY.items()}
SWEETS["act"] = ("Place an order", "See the sweets")
SWEETS["act_online"] = ("Order online", "See the sweets")
SWEETS["_generic"] = True

SCHOOL = dict(
    who="families", does=("teaches", "guides"), do=("teach", "guide"), ing=("Teaching", "Guiding"), come="Learn",
    act=("Ask about admission", "See the classes"), act_online=("Apply online", "See the classes"),
    book_how_online="Apply online", book_how="Message us to ask about admission",
    tails=["step by step", "in a caring classroom", "with time for questions", "one year at a time", "beyond the textbook"],
    closers=["Every child starts from where they are.", "Questions are welcome from parents too.", "Visit and see a classroom for yourself.", "Learning is better with encouragement.",
             "Parents are kept in the loop.", "Small steps, then bigger ones.", "Come and meet the teachers.", "Ask until it makes sense."],
    invites=["Tell us your child's age and class and we'll explain the next step.", "Ask about timings and the school day.", "Message us to arrange a visit.", "Ask how parents are kept informed.",
             "Tell us what matters most to you in a school.", "Ask what the first day looks like.", "Share your questions before you decide.", "Ask how to apply."],
    feat=["Ask how {i} fits into the school day.", "Curious about {i}? Come and see {it} in action.", "{I} {is} part of what children do here; ask how {they} {works}.", "Ask who teaches {i} and how progress is shared.",
          "New to {i}? Ask the teachers how children are eased in.", "Tell us what your child enjoys and we'll show where {i} fits.", "Ask us about {i} when you visit.", "{I}: ask how {they} {is} taught and how {they} {is} checked."],
    steps=[[("Ask about admission", "{book_how}, and tell us your child's age and class."), ("Visit the school", "Meet the teachers and see the classrooms."), ("Join the class", "We confirm the details and the first day with you.")],
           [("Tell us about your child", "Share the age, the class and anything we should know."), ("Meet the team", "We explain the school day and answer your questions."), ("Settle in", "Teachers help your child find their feet.")],
           [("Get in touch", "Message us or use the contact details on this page."), ("See for yourself", "Walk through the school and meet the teachers."), ("Begin the year", "We guide you through the first weeks.")]],
    faq=[("How do I ask about admission?", ["{book_how}, and tell us your child's age and class.", "Use the contact details on this page and tell us which class you have in mind."], "admissions",
          ["Admissions are open; use the contact details on this page to start.", "Yes, admissions are open; message us to begin."]),
         ("Can I visit the school first?", ["Of course; message us and we'll arrange a time.", "Yes; ask us for a convenient time to visit."], None, None),
         ("How are parents kept informed?", ["Ask us when you visit and we'll explain how updates are shared.", "Message us and we'll tell you how teachers keep in touch."], None, None),
         ("Which classes do you teach?", ["Ask us about the classes you have in mind and we'll explain.", "Tell us your child's age and we'll point you to the right class."], None, None),
         ("When are you open?", ["We're open {hours}.", "Our hours are {hours}."], "hours", None),
         ("Where are you?", ["We're in {city}; get in touch for directions.", "Find us in {city}. Message us and we'll send directions."], "city", None),
         ("Can I ask about {i1}?", ["Of course; ask how it is taught.", "Yes; tell us what you'd like to know about {i1}."], "item", None),
         ("Can I ask questions before I decide?", ["Of course; that's what the first conversation is for.", "Yes; ask as many as you like."], None, None)],
    highlights=[("Caring teachers", "Someone knows your child by name."), ("Every child", "Learning scaled to where they are."), ("Parents in the loop", "Updates you can rely on."), ("Visit first", "See a classroom before you decide."),
                ("Beyond the textbook", "Activities alongside lessons."), ("Easy to ask", "Questions are always welcome.")],
    blog=[("Choosing a school: questions to ask", "A short list for parents before they decide."), ("What to know before {i1}", "A short guide for families."), ("The first week: what to expect", "How children settle into a new class."),
          ("Helping your child with homework", "Routines that make evenings calmer."), ("Why {i1} matters", "A plain look at what children gain."), ("Talking to teachers", "How to get the most from a meeting."),
          ("Preparing for a new year", "Small steps that help everyone."), ("Balancing study and play", "Why both matter.")],
    cta_text=["{act1} and tell us your child's class.", "Visit and see for yourself.", "Your first question is one message away.", "{act1}; we'll explain the next step.", "Ask how {i1} works.",
              "Ready? {act1}.", "Start with {i1}; ask the rest.", "Come and meet the teachers."],
    _generic=True,
)


HOTEL = dict(
    who="guests", does=("offers", "hosts"), do=("offer", "host"), ing=("Offering", "Hosting"), come="Stay for",
    act=("Check availability", "See the rooms"), act_online=("Book a room online", "See the rooms"),
    book_how_online="Book a room online", book_how="Message us your dates to book a room",
    tails=["a comfortable stay", "away from the rush", "made to feel at home", "rest well", "for a few days or a few weeks"],
    closers=["Rest well; we'll take care of the rest.", "Tell us your dates and we'll do the planning.", "Arrive tired, leave rested.", "Ask us what is close by.", "Every guest is looked after personally.",
             "Come for a night or stay a week.", "Questions before you arrive are welcome.", "Your room is one message away."],
    invites=["Tell us your dates and how many are coming.", "Ask what is included before you book.", "Message us if you need anything arranged before you arrive.", "Tell us if anyone needs special arrangements.",
             "Ask about getting here and where to go nearby.", "Share your plans and we'll suggest what suits.", "Ask us about the rooms before you decide.", "Tell us what matters most for your stay."],
    feat=["Ask about {i} when you book.", "{I} {is} part of the stay; ask us how {they} {works}.", "Curious about {i}? Ask us before you arrive.", "Tell us if {i} matters to you and we'll confirm.",
          "Ask what comes with {i}.", "If {i} {is} why you are coming, say so when you book.", "Ask us what to expect from {i}.", "{I}: message us for the details."],
    steps=[[("Pick your dates", "Tell us when you arrive and when you leave."), ("Choose what suits you", "Look through {list2_or} and tell us what you'd like."), ("Arrive and settle in", "We'll confirm the details before you come.")],
           [("Send your dates", "{book_how}, and say how many are coming."), ("We confirm", "We reply with what is available."), ("Enjoy your stay", "Rest, explore and ask us for anything you need.")],
           [("Ask your questions", "Anything about the rooms, the place or getting here."), ("Book", "Tell us the dates that work."), ("Come and relax", "We'll have things ready.")]],
    faq=[("How do I book a room?", ["{book_how}, and tell us how many are coming.", "Use the contact details on this page and tell us your dates."], "online_booking", ["You can book online, or contact us directly.", "Online booking is available."]),
         ("Can I ask for something special?", ["Of course; tell us when you book and we'll say what we can do.", "Message us before you arrive and we'll see what's possible."], None, None),
         ("Can you help with getting here?", ["Ask us when you book and we'll explain how to reach us.", "Message us and we'll send directions."], "pickup", ["Yes, pickup is available; tell us when you arrive.", "We can arrange a pickup; message us your arrival time."]),
         ("Is there anything included with the room?", ["Ask us when you book and we'll list what comes with your stay.", "Message us and we'll tell you what is included."], None, None),
         ("When can I reach you?", ["We're open {hours}.", "Our hours are {hours}."], "hours", None),
         ("Where are you?", ["We're in {city}; get in touch for directions.", "Find us in {city}. Message us and we'll send directions."], "city", None),
         ("Can I ask about {i1}?", ["Of course; ask us what it involves.", "Yes; tell us what you'd like to know about {i1}."], "item", None),
         ("Can I ask questions before I book?", ["Of course; that's what the first message is for.", "Yes; ask as many as you like."], None, None)],
    highlights=[("Easy to book", "Tell us your dates and we'll take it from there."), ("Look after you", "Someone is always on hand."), ("Rest well", "A quiet room after a long day."),
                ("Ask us anything", "Questions before you arrive are welcome."), ("Come as you are", "A night or a long stay."), ("Know before you go", "We'll tell you what is included.")],
    blog=[("What to know before you book a stay", "A short list of questions worth asking."), ("Making the most of {i1}", "A few simple ideas for your visit."), ("Planning a trip with the family", "Dates, rooms and what to pack."),
          ("A short guide to getting here", "Simple tips for arriving without stress."), ("Why {i1} makes a difference", "What it adds to a stay."), ("Travelling light", "What you really need for a few days away."),
          ("Choosing the right room", "Questions to ask before you decide."), ("What to do nearby", "Ask us; we love the question.")],
    cta_text=["{act1} and tell us your dates.", "Planning a stay? {act1}.", "Your room is one message away.", "Ask about {i1} when you {act1_l}.", "Tell us your dates; we'll do the rest.",
              "{act1}, or message us your plans.", "Stay a night; stay a week.", "Come and rest."],
    _generic=True,
)

PHARMACY = dict(
    who="customers", does=("stocks", "supplies"), do=("stock", "supply"), ing=("Stocking", "Supplying"), come="Find",
    act=("Order medicines", "Visit the store"), act_online=("Order online", "Visit the store"),
    book_how_online="Order online", book_how="Message us what you need",
    tails=["when you need it", "with advice at the counter", "close to home", "ask the pharmacist", "everyday health"],
    closers=["Ask the pharmacist if you are unsure.", "Bring the prescription and we'll take it from there.", "Questions about a medicine are always welcome.", "Everyday health, close to home.",
             "Message us what you need and we'll confirm.", "Check the strength and dose with the pharmacist.", "Ask before you buy; it takes a minute.", "Always read the label."],
    invites=["Message us what you need and we'll confirm.", "Send the prescription and we'll get it ready.", "Ask the pharmacist about anything on the label.", "Tell us if you need something for someone at home.",
             "Ask what is in stock before you come.", "Tell us what you usually take and we'll check availability.", "Ask for a recommendation at the counter.", "Share what you're looking for and we'll help."],
    feat=["Ask what is in stock for {i}.", "{I} {is} available; ask the pharmacist about {it}.", "Need {i}? Message us before you come.", "Ask us about {i} and we'll check.",
          "Tell us what you need in {i} and we'll help.", "If {i} {is} what you need, ask at the counter.", "Ask about {i}; we'll tell you what we have.", "{I}: message us for availability."],
    steps=[[("Tell us what you need", "Send the name, or the prescription."), ("We check and confirm", "We tell you what is in stock."), ("Collect or receive", "Pick it up, or ask about delivery.")],
           [("Send your list", "Message us the items you need."), ("We prepare it", "We pack it and confirm."), ("Get it", "Come by or ask how it can reach you.")],
           [("Ask the pharmacist", "Any question about a medicine or product."), ("Choose", "Look through {list2_or} with us."), ("Take it home", "With clear instructions.")]],
    faq=[("How do I order?", ["{book_how}, and send the prescription if one is needed.", "Use the contact details on this page and tell us what you need."], "online_order", ["You can order online, or contact us directly.", "Online ordering is available."]),
         ("Do you deliver?", ["Ask us what is possible for your area and we'll tell you honestly.", "Message us your location and we'll say what we can do."], "home_delivery", ["Yes, home delivery is available.", "We deliver; message us your location."]),
         ("Do I need a prescription?", ["For prescription medicines, bring or send the prescription; the pharmacist will guide you.", "Ask us when you order and we'll tell you."], None, None),
         ("Can I ask about a medicine?", ["Of course; ask the pharmacist anything about it.", "Yes; message us and we'll explain."], None, None),
         ("When are you open?", ["We're open {hours}.", "Our hours are {hours}."], "hours", None),
         ("Where are you?", ["We're in {city}; get in touch for directions.", "Find us in {city}. Message us and we'll send directions."], "city", None),
         ("Can I ask about {i1}?", ["Of course; ask us what we have.", "Yes; tell us what you'd like to know about {i1}."], "item", None),
         ("Can you check if something is in stock?", ["Message us the name and we'll confirm.", "Ask before you come; we'll check."], None, None)],
    highlights=[("Ask the pharmacist", "Questions are always welcome."), ("Close to home", "Everyday needs, easy to reach."), ("Check before you come", "Message us and we'll confirm stock."),
                ("Clear advice", "Instructions explained at the counter."), ("Easy to order", "Tell us what you need."), ("For the family", "Something for everyone at home.")],
    blog=[("Questions to ask your pharmacist", "A short list worth keeping."), ("Storing medicines safely at home", "Simple habits that help."), ("Reading a label properly", "What to look for before you take anything."),
          ("A short guide to {i1}", "What it is and when people ask about it."), ("Keeping a family medicine box", "What to keep, and how to check it."), ("Why {i1} needs a conversation", "Ask before you buy."),
          ("Planning your monthly medicines", "How to avoid last-minute trips."), ("Travelling with medicines", "A few simple rules.")],
    cta_text=["{act1} and tell us what you need.", "Need something? {act1}.", "Your order is one message away.", "Ask about {i1} when you {act1_l}.", "Tell us what you need; we'll check.",
              "{act1}, or message us.", "Ask the pharmacist first.", "Check stock before you come."],
    _generic=True,
)

TEA = dict(does=("serves", "brews", "pours"), do=("serve", "brew", "pour"), ing=("Serving", "Brewing"), come="Come for",
           act=("Visit us", "See the menu"), act_online=("Order online", "See the menu"),
           invites=["Tell us when you're coming and we'll make room.", "Ask for a recommendation when you arrive.", "Ask what is freshly made today.", "Message us if you're coming with a group.",
                    "Ask what pairs well with your cup.", "Tell us if anyone has a dietary need.", "Bring a friend and ask what to try.", "Ask the team what they would order."],
           cta_text=["{act1} and ask what's fresh.", "Start with a cup; ask about {i1}.", "Your next cup is one message away.", "Ask about {i1} when you {act1_l}.", "Come as you are; we'll handle the rest.",
                     "{act1}, or message us your plans.", "Try {i1} and tell us what you think.", "Stay a while; nobody is rushing you."], _generic=True)

_BEAUTY_FAQ = {f[0]: f for f in VOICE["beauty"]["faq"]}

TATTOO = dict(
    act=("Book an appointment", "Call the studio"), act_online=("Book an appointment online", "Call the studio"),
    tails=["with time for you", "drawn around your idea", "unhurried", "from sketch to aftercare", "one design at a time"],
    closers=["Bring a reference if you have one.", "Take a seat; we'll start with a chat.", "We sketch first, then we begin.", "Ask what to expect before you book.",
             "Your design, your time.", "No two designs are the same.", "Tell us the idea and we'll draw it up.", "Ask about aftercare before you leave."],
    invites=["Book a time and tell us the design you have in mind.", "Message us a reference picture or a sketch.", "Tell us where on the body you are thinking of, and the size.",
             "Ask about timings before you book.", "Bring a friend if you like.", "Ask about cover-ups and touch-ups.", "Say what you have in mind and we'll suggest options.",
             "Message us if you are unsure about a design."],
    feat=["Tell us what you want from {i}; we'll suggest what fits.", "{I}: start with a chat about the design and where it goes.", "Booking {i}? Bring a reference for what you have in mind.",
          "We take time over {i}, and we ask before we begin.", "{I} {is} planned around you, not a template.", "Not sure about {i}? Ask for a consultation first.",
          "Pair {i} with a touch-up visit if it suits you.", "Ask what to expect from {i} before you book."],
    highlights=[("Sketch first", "Every design starts with a chat and a drawing."), ("Planned around you", "Not a template."), ("Unhurried", "Time for the details."),
                ("Questions welcome", "Ask how the studio works before you book."), ("Aftercare explained", "You leave knowing how to look after it."), ("Bring your ideas", "References welcome.")],
    faq=[_BEAUTY_FAQ["How do I book an appointment?"],
         ("Can I bring my own design?", ["Yes; a reference or sketch helps us understand what you have in mind.", "Please do; it makes the first chat easier."], None, None),
         ("Can you cover up an old tattoo?", ["Ask us when you book and we'll tell you what is possible.", "Send a photo and we'll advise."], None, None),
         ("How long will my appointment take?", ["It depends on the design and size; we'll tell you when you book.", "Ask us when you book and we'll give you an idea."], None, None),
         ("What about aftercare?", ["We'll explain how to look after it before you leave.", "Ask us and we'll walk you through it."], None, None),
         _BEAUTY_FAQ["When are you open?"], _BEAUTY_FAQ["Where are you?"], _BEAUTY_FAQ["Can I ask about {i1}?"]],
    blog=[("How to explain the design you want", "References, words and the one question to ask your artist."), ("Getting ready for {i1}", "What to do the day before."),
          ("Looking after a new tattoo", "Simple habits for the first weeks."), ("{I1} or {i2}: how to choose", "A plain guide to deciding."),
          ("Questions to ask before {i1}", "A short list worth bringing."), ("Choosing a placement and size", "How the spot on the body changes the design."),
          ("Planning a cover-up", "What to ask before you commit."), ("Your first visit", "What happens from the first chat to the last step.")],
    _generic=True,
)

SPA = dict(
    act=("Book a treatment", "Call the spa"), act_online=("Book a treatment online", "Call the spa"),
    invites=["Book a time and tell us what you'd like.", "Message us the treatment you have in mind.", "Ask about timings before you book.", "Bring a friend if you like.",
             "Tell us if it is for a special day.", "Ask which treatment suits you.", "Message us if you are unsure which service to pick.", "Say how long you have and we'll suggest options."],
    highlights=[("Listening first", "Every visit starts with a chat."), ("Planned around you", "Not a template."), ("Unhurried", "Time to switch off."),
                ("Come as you are", "No rush, no pressure."), ("Easy to book", "Message or call; we'll find a time."), ("Ask first", "Questions about a treatment are welcome.")],
    faq=[f if not f[0].startswith("Do you do bridal") else ("Do you offer packages or gift visits?", ["Ask us when you book and we'll tell you what is possible.", "Tell us the occasion and we'll advise."], None, None)
         for f in VOICE["beauty"]["faq"]],
    _generic=True,
)

PROFILE_VOICE = {"bakery": BAKERY, "yoga": YOGA, "tea_cafe": TEA}
TYPE_VOICE = {"tattoo": TATTOO, "spa": SPA, "sweets": SWEETS, "school": SCHOOL, "playschool": dict(SCHOOL, come="Enrol in"), "hotel": HOTEL, "pharmacy": PHARMACY}


def profile_voice(kind, profile, type_id=None):
    """The kind's voice with the sub-niche's own fields laid over it (or None when the kind voice is right as it is)."""
    over = TYPE_VOICE.get(type_id) or PROFILE_VOICE.get(profile)
    if not over:
        return None
    base = dict(VOICE[kind])
    base.update(over)
    return base
