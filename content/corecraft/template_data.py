"""Hand-written taxonomy and niche frames for template_model.

Slots: {a} {b} {c} = main nouns, {x} = a service/extra noun, {j} = adjective ({A},{J} capitalised).
The learned crawl data (corecraft/data/fillers.json) ranks these nouns by how characteristic they are of the niche;
words that are not on these lists never reach the page, which keeps crawl noise ("communities", "messages") out.
"""

NICHE = {
    "restaurant": {
        "main": "burgers toppings fries potatoes chips dishes meals sandwiches bowls patties drinks greens veggies treats coffees teas breakfasts lunches dinners desserts pastries pizzas noodles tacos soups smoothies juices cakes cookies muffins bagels curries kebabs snacks platters combos brews salads waffles doughnuts wraps".split(),
        "extra": "rewards orders deals discounts locations".split(),
        "adj": ["fresh", "hand-crafted", "seasonal", "homemade", "made-to-order"],
        "hero": ["{J} {a}, served daily", "Come hungry. Leave happy.", "Where {a} are made fresh", "Good {a}, good company", "{A} worth coming back for", "Made fresh, made for you"],
        "tagline": ["{J} {a} and {j} {b}, every day.", "Our kitchen is always busy with {a} and {b}.", "Fresh {a}, warm welcome.", "Treat yourself to {a} you will remember.", "Hungry for {a}? We have you covered.", "{A}, {b}, and a seat at the table.", "Order {a} online or drop in and say hello."],
        "feature": ["Made fresh every morning, our {a} never sit around.", "Our {a} are made to order, so they arrive hot.", "Hand-picked ingredients go into every one of our {a}.", "Love {a}? You will want to try them all.", "Perfect {a} for lunch, dinner, or anything in between.", "A favourite with regulars: our {a}.", "Pair our {a} with our {b} for the full experience."],
        "open": ["Every day starts with {j} {a} and a warm welcome.", "Our kitchen turns out {a}, {b}, and {c} from morning to night.", "We cook {a} the way we would at home.", "Our menu is built around {a} and {b}.", "{A} and {b} are what we do best."],
        "close": ["Stop by, grab a seat, and let us take care of the rest.", "We keep our {c} simple and our portions generous.", "Come hungry; our {c} are worth the wait.", "Ask us about our {c}; we love to talk food.", "Bring your friends, because our {c} are made for sharing."],
    },
    "fitness": {
        "main": "classes workouts programs sessions routines exercises drills circuits stretches bootcamps lessons movements activities machines weights dumbbells kettlebells pilates bikes mats rowers warm-ups cool-downs challenges cardio-sessions core-sessions".replace("-", " ").split(),
        "extra": "memberships facilities studios clubs gyms rooms plans".split(),
        "adj": ["coach-led", "high-energy", "beginner-friendly", "full-body"],
        "hero": ["Build strength with {a}", "Your goals. Our {a}.", "Move better with {a}", "Show up. We handle the {a}.", "{A} that keep you coming back"],
        "tagline": ["Real {a} for real progress.", "{J} {a} and {b} for every level.", "From your first {a} to your personal best.", "{A} and {b}, built around your goals.", "Whatever your level, we have {a} to match.", "Find {a} you actually enjoy."],
        "feature": ["{J} {a} built for every fitness level.", "Our {a} keep you moving and keep it fun.", "Mix up your week with our {a}.", "Starting out or levelling up, our {a} fit.", "Track your progress across all our {a}.", "Short on time? Our {a} get it done in under an hour.", "Add our {a} to your routine and feel the difference.", "Pair our {a} with {b} for balanced progress."],
        "open": ["We help you get stronger with {a}, {b}, and {c}.", "Every member gets a plan built around {a} and {b}.", "Our coaches focus on {a} so you can focus on results.", "{A} and {b} are the backbone of what we do."],
        "close": ["Small habits add up, and we help you build them.", "Our {c} are tough but friendly.", "Whatever your starting point, we meet you there.", "Come try our {c} and bring a friend.", "Your goals set the pace, and our {c} keep you going."],
    },
    "tech": {
        "main": "workflows apps integrations dashboards automations templates pipelines alerts tickets files documents tasks projects campaigns meetings conversations insights systems platforms applications databases endpoints deployments backups reports notifications forms".split(),
        "extra": "sessions goals".split(),
        "adj": ["reliable", "secure", "scalable", "simple"],
        "hero": ["Ship faster with better {a}", "Your {a}, finally in sync", "Make your {a} work harder", "Simple {a} for busy teams", "Build on {a} that scale"],
        "tagline": ["{A} and {b} that work the way you do.", "Connect your {a} and {b} in minutes.", "Less busywork. More {a}.", "One place for your {a}, {b}, and {c}.", "Automate {a} and focus on what matters.", "Scale your {a} without the headaches."],
        "feature": ["Keep your {a} organised in one place.", "Connect your {a} with the software your team likes.", "Automate repetitive {a} and save hours each week.", "Track every one of your {a} in real time.", "Secure by default: your {a} stay protected.", "Set up your {a} in minutes, no code required.", "See how your {a} perform with clear charts."],
        "open": ["We build tools that simplify {a}, {b}, and {c}.", "Teams use us to manage {a} and {b} without the chaos.", "Our platform brings your {a} and {b} together.", "From {a} to {b}, everything runs in one place."],
        "close": ["Security and speed are built in, not bolted on.", "Our support team is only a message away.", "Start small and scale as your {c} grow.", "Change how you handle {c}, one step at a time."],
    },
    "portfolio": {
        "main": "galleries photos images prints videos layouts templates designs albums shoots sketches illustrations logos projects films themes animations visuals".split(),
        "extra": "bookings invoices contracts sessions collections sites pages blogs packages studios appointments".split(),
        "adj": ["thoughtful", "bold", "honest", "handcrafted"],
        "hero": ["Work that speaks for itself", "Stories told through {a}", "Capturing {a} with intent", "Selected {a}, thoughtfully made", "{A} with a point of view"],
        "tagline": ["{J} {a} for brands with a story.", "From first sketch to final {a}.", "{A}, {b}, and a little imagination.", "Quietly bold {a}, carefully made.", "Thoughtful {a} that stand out."],
        "feature": ["Browse a selection of our favourite {a}.", "Every one of our {a} starts with a conversation.", "Custom {a} made to fit your brand.", "See how our {a} come together, step by step.", "Commission {a} made just for you.", "Pair our {a} with {b} for a complete story."],
        "open": ["I create {a}, {b}, and {c} for people with a story to tell.", "Every project begins with listening, then moves into {a}.", "My work spans {a}, {b}, and {c}.", "Clients come for the {a} and stay for the collaboration."],
        "close": ["Detail matters, from typography to timing.", "Every choice serves the story you want people to remember.", "Let us talk about your next project.", "I take on a limited number of {c} each season.", "Great work takes time, and I give every project plenty."],
    },
    "education": {
        "main": "courses lessons skills programs modules lectures quizzes exams workshops tutorials assignments masterclasses languages labs guides projects classes worksheets chapters papers tests topics seminars".split(),
        "extra": "sessions goals".split(),
        "adj": ["clear", "practical", "step-by-step", "hands-on"],
        "hero": ["Learn {a} at your own pace", "Master new {a}", "Where {a} come alive", "Learn today, lead tomorrow", "Build confidence with {a}"],
        "tagline": ["{J} {a} and patient teachers.", "{A} that turn curiosity into confidence.", "From your first {a} to the final exam.", "Practical {a} for real progress.", "Learn at your pace with {a} made simple."],
        "feature": ["Step-by-step {a} that build real confidence.", "Work through {a} and get feedback right away.", "Our {a} are designed by experienced mentors.", "Revisit our {a} any time you need a refresher.", "Short {a} fit around school, work, and life.", "Prepare with {a} that follow real exam patterns."],
        "open": ["We teach {a}, {b}, and {c} in small, friendly steps.", "Our teaching mixes {a} with plenty of practice.", "Students come to us for {a} and leave with confidence.", "{A} and {b} are at the heart of every class."],
        "close": ["Every student gets the time and attention they need.", "We track progress so effort never goes unseen.", "Our {c} adapt to your pace.", "Parents stay informed with regular updates on {c}.", "We celebrate every step forward, big or small."],
    },
    "shop": {
        "main": "diamonds earrings necklaces bracelets pendants rings watches sneakers shoes boots sweaters shirts suits bags dresses jackets scarves wallets candles cushions towels sandals clothes accessories glasses frames pillows mattresses gifts sets bundles collections pieces".split(),
        "extra": "arrivals".split(),
        "adj": ["handpicked", "timeless", "everyday", "well-made"],
        "hero": ["Find {a} you will love", "New {a}, just arrived", "{A} for every day", "Little luxuries: {a} and more", "{J} {a}, made to last"],
        "tagline": ["Curated {a} at prices that feel fair.", "{J} {a}, delivered with care.", "{A} and {b} made to be loved.", "Treat yourself to {a} worth keeping.", "Beautiful {a} for every occasion."],
        "feature": ["Choose from our {a}, picked for quality and character.", "Our {a} are made to last and made to love.", "Gift-ready {a}, wrapped with care.", "New {a} arrive all the time, so check back often.", "Love your {a}, or send them back within thirty days.", "Pair our {a} with {b} for a complete look."],
        "open": ["We curate {a}, {b}, and {c} from makers we trust.", "Every one of our {a} is chosen for quality and character.", "From {a} to {b}, we keep prices fair and materials honest.", "{A} and {b} are our specialty."],
        "close": ["Orders ship quickly and arrive carefully packed.", "Not happy? Send it back, no questions asked.", "Our {c} are chosen so you buy less and enjoy it more.", "Free shipping on orders over a small minimum.", "Every order comes with a note from our team."],
    },
    "business": {
        "main": "repairs installations inspections upgrades cleanups appointments estimates packages services projects guides documents contracts lawns windows offices surfaces pipes drains faucets heaters fixtures checkups replacements consultations".split(),
        "extra": [],
        "adj": ["reliable", "local", "friendly", "professional"],
        "hero": ["Trusted {a}, done properly", "{A} you can rely on", "Reliable {a} when you need them", "Local {a}, honest advice", "Quality {a}, fair prices"],
        "tagline": ["Straightforward {a} and honest advice.", "Clear pricing for {a} and {b}.", "{J} {a}, every time.", "{A} and {b}, done right the first time.", "Your problem solved with {j} {a}."],
        "feature": ["Honest pricing on all our {a}, no surprises.", "Need {a}? We usually reply the same day.", "Our {a} come with a satisfaction guarantee.", "Book {a} online in minutes.", "Skilled specialists handle every one of our {a}.", "We stand behind our {a} long after the job is done."],
        "open": ["We deliver {a}, {b}, and {c} with fair pricing and steady communication.", "Customers call us for {a} and recommend us for the service.", "Our team handles {a} and {b} from start to finish.", "{A}, {b}, and {c} are what we do every day."],
        "close": ["We listen first, then deliver a clear plan.", "Customers return because we keep our word.", "Our {c} are guaranteed, and so is our attention to detail.", "Call or message us and we will get back to you quickly.", "Fair prices and clear quotes come as standard."],
    },
}

# prompt trigger (prefix) -> nouns that fit that sub-topic, so "jewellery" never gets "mattresses"
SUBTOPICS = {
    "shop": [
        (("jewel", "ring", "diamond", "earring", "necklace", "bracelet", "pendant"), "rings necklaces bracelets earrings pendants diamonds watches gifts pieces collections charms studs hoops chains bangles brooches anklets".split()),
        (("bed", "mattress", "sleep", "pillow", "linen"), "mattresses pillows towels cushions candles sets bundles".split()),
        (("shoe", "sneaker", "boot", "footwear", "sandal"), "sneakers shoes boots sandals collections".split()),
        (("cloth", "fashion", "wear", "dress", "apparel", "boutique"), "dresses jackets scarves sweaters shirts suits clothes accessories bags".split()),
        (("home", "decor", "candle", "gift"), "candles cushions towels gifts sets bundles collections pieces".split()),
    ],
    "restaurant": [
        (("coffee", "cafe", "tea", "brew", "chai", "espresso"), "coffees teas brews pastries muffins bagels cakes cookies drinks snacks smoothies juices croissants lattes".split()),
        (("pizza", "italian"), "pizzas toppings combos salads desserts drinks".split()),
        (("burger", "grill", "bbq", "steak"), "burgers fries sandwiches wraps chips patties drinks".split()),
        (("bakery", "cake", "pastry", "dessert"), "cakes pastries cookies muffins bagels doughnuts desserts".split()),
        (("vegan", "healthy", "salad", "vegetarian"), "salads bowls greens veggies smoothies juices soups".split()),
    ],
    "fitness": [
        (("yoga", "pilates", "meditat"), "classes sessions stretches routines pilates".split()),
        (("gym", "weight", "strength", "muscle"), "weights dumbbells kettlebells machines workouts lifts".split()),
        (("box", "martial", "karate", "mma"), "drills circuits bootcamps workouts classes".split()),
    ],
    "business": [
        (("plumb", "pipe", "drain"), "repairs installations inspections estimates appointments pipes drains faucets heaters fixtures upgrades packages".split()),
        (("lawn", "garden", "landscap"), "lawns installations upgrades estimates appointments".split()),
        (("clean", "maid", "janitor"), "cleanups surfaces windows offices appointments estimates packages".split()),
        (("legal", "law", "attorney", "lawyer"), "documents contracts guides articles appointments".split()),
        (("electric", "wiring"), "repairs installations inspections upgrades fixtures estimates".split()),
    ],
    "education": [
        (("cod", "python", "program", "software", "web"), "courses projects tutorials lessons skills labs".split()),
        (("language", "english", "spanish", "french", "german"), "lessons languages quizzes exams workshops books".split()),
        (("math", "science", "physic", "chemist"), "lessons quizzes exams workshops books assignments".split()),
    ],
    "portfolio": [
        (("wedding", "event", "portrait"), "photos albums galleries shoots prints".split()),
        (("design", "brand", "logo", "illustrat"), "logos designs illustrations sketches projects".split()),
        (("film", "video", "cinema"), "films videos shoots projects".split()),
    ],
}
