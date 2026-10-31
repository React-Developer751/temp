"""What things ARE: one-line, public-knowledge descriptions of dishes, treatments, classes and products, grouped by sub-niche.

Descriptions define the item ("A thin, stretchy base with tomato, cheese and toppings"); they never claim anything about a
particular business (no "freshly made daily", no "award-winning"). Items a person types are looked up here; anything not found
gets a neutral line from the kind's voice instead. Dishes of one cuisine are never offered to another: see FOREIGN in profiles.py.
"""

_RAW = {
    "italian": """
wood fired pizza = Baked in a wood-fired oven, so the crust blisters and the edges char.
pizza = A thin, stretchy base with tomato, cheese and toppings of your choice.
fresh pasta = Pasta made from flour and egg, rolled and cut instead of dried.
pasta = Spaghetti, penne or filled shapes, tossed in a sauce that suits them.
tiramisu = Coffee-soaked sponge layered with mascarpone cream and cocoa.
risotto = Creamy rice cooked slowly in stock and finished with butter and cheese.
lasagna = Layers of pasta, ragù and béchamel, baked until golden.
lasagne = Layers of pasta, ragù and béchamel, baked until golden.
bruschetta = Toasted bread rubbed with garlic and topped with tomato and olive oil.
gelato = Dense, silky Italian ice cream, served a little softer than usual.
panna cotta = A set cream dessert with vanilla, served with fruit or caramel.
garlic bread = Warm bread with garlic butter, good next to any pasta.
focaccia = Soft olive-oil bread with a dimpled top and flaky salt.
calzone = A pizza folded over cheese and toppings, baked until puffed.
carbonara = Pasta with egg, hard cheese, black pepper and cured pork.
gnocchi = Soft potato dumplings tossed in a simple sauce.
ravioli = Filled pasta parcels served with sauce or butter.
minestrone = A thick vegetable and bean soup.
arancini = Crisp fried rice balls with a soft, cheesy centre.
antipasti = Small plates to start: cured meats, cheese, olives and vegetables.
caprese = Tomato, mozzarella and basil with olive oil.
cannoli = Crisp pastry tubes filled with sweet ricotta.
affogato = A scoop of gelato drowned in hot espresso.
weekend brunch = A slow weekend meal; ask for the brunch menu when you book.
brunch = A late-morning meal with something sweet, something savoury and coffee.
espresso = A small, strong shot of coffee to finish the meal.
wine = A glass or bottle to go with the food; ask for a suggestion.
""",
    "north_indian": """
butter chicken = Tandoori chicken in a creamy tomato and butter gravy.
dal makhani = Black lentils simmered slowly with butter and cream.
paneer tikka = Paneer marinated in spices and grilled in the tandoor.
naan = Soft leavened bread baked against the walls of a tandoor.
tandoori roti = Whole-wheat bread baked in the tandoor.
biryani = Layered rice and meat or vegetables, cooked slowly with whole spices.
chole bhature = Spiced chickpeas with puffed, fried bread.
rajma chawal = Kidney-bean curry served over steamed rice.
kebab = Spiced, marinated meat or vegetables, grilled on skewers.
seekh kebab = Minced meat on skewers, grilled over charcoal.
tandoori chicken = Chicken marinated in yoghurt and spices and roasted in a tandoor.
palak paneer = Paneer in a smooth spinach gravy.
kadai paneer = Paneer with peppers in a thick, spiced tomato gravy.
dal tadka = Yellow lentils finished with a sizzling garlic and cumin tempering.
lassi = A cold yoghurt drink, sweet or salted.
gulab jamun = Soft milk dumplings soaked in sugar syrup.
thali = A platter of small portions: dals, vegetables, bread and rice.
rogan josh = Slow-cooked lamb in a red, aromatic Kashmiri-style gravy.
raita = Cooling yoghurt with cucumber or boondi.
shahi paneer = Paneer in a rich, mildly sweet cashew and cream gravy.
curry = A spiced gravy built from onions, tomatoes and ground spices.
tandoori = Marinated, then roasted at high heat in a clay oven.
""",
    "south_indian": """
masala dosa = A crisp rice-and-lentil crepe filled with spiced potato.
dosa = A thin, crisp crepe made from fermented rice and lentil batter.
idli = Soft steamed rice-and-lentil cakes, served with sambar and chutney.
vada = Crisp, savoury lentil doughnuts, soft inside.
medu vada = Crisp, savoury lentil doughnuts, soft inside.
sambar = A tangy lentil and vegetable stew.
uttapam = A thick, soft pancake topped with onions and tomatoes.
filter coffee = Strong coffee brewed through a metal filter and mixed with hot milk.
pongal = Soft rice and lentils cooked with pepper, cumin and ghee.
upma = Roasted semolina cooked with vegetables and mustard seeds.
rasam = A peppery, tangy lentil soup.
curd rice = Soft rice mixed with yoghurt and tempering.
lemon rice = Rice tossed with lemon, peanuts and curry leaves.
appam = A lacy-edged, soft-centred rice pancake.
meals = A plate of rice with sambar, rasam, vegetables and curd.
rava dosa = A lacy, crisp crepe made with semolina.
mysore pak = A rich sweet made of gram flour, ghee and sugar.
chutney = A fresh ground side of coconut or tomato for dipping.
""",
    "chinese": """
hakka noodles = Stir-fried noodles with vegetables and soy.
noodles = Stir-fried or soupy noodles with vegetables and your choice of protein.
fried rice = Rice wok-tossed with egg, vegetables and soy sauce.
manchurian = Crisp fried balls or florets in a tangy soy and garlic sauce.
momos = Steamed or fried dumplings with a spicy dipping sauce.
dumplings = Thin wrappers filled with meat or vegetables, steamed or pan-fried.
spring roll = A crisp roll of shredded vegetables.
hot and sour soup = A peppery, tangy soup thick with vegetables.
chilli paneer = Paneer tossed in a hot garlic and chilli sauce.
chilli chicken = Chicken fried and tossed with peppers in a spicy sauce.
sweet corn soup = A gently sweet, thick soup with corn.
schezwan noodles = Noodles tossed in a fiery Sichuan-style chilli sauce.
dim sum = Small steamed or fried bites served in baskets.
manchow soup = A thick soup topped with crisp fried noodles.
honey chilli potato = Crisp potato strips in a sticky sweet and spicy glaze.
""",
    "street_food": """
pani puri = Crisp hollow shells filled with spiced water, potato and chutneys.
golgappa = Crisp hollow shells filled with spiced water, potato and chutneys.
pav bhaji = Mashed spiced vegetables served with buttered pav.
vada pav = A spiced potato fritter in a soft bun with chutney.
bhel puri = Puffed rice tossed with chutneys, onion and sev.
sev puri = Crisp discs topped with potato, chutneys and sev.
samosa = A crisp pastry stuffed with spiced potato and peas.
kachori = A flaky fried pastry with a spicy lentil filling.
dahi puri = Crisp shells filled with yoghurt, chutneys and sev.
chaat = A snack of crisp bites with yoghurt, chutneys and spices.
aloo tikki = Crisp-fried spiced potato patties.
kathi roll = Flatbread rolled around grilled fillings and chutney.
egg roll = A flaky paratha wrapped around egg and onions.
jalebi = Crisp spirals soaked in saffron sugar syrup.
dabeli = A sweet-spicy potato mix in a bun, topped with peanuts and pomegranate.
masala chai = Tea simmered with milk and spices.
""",
    "bakery": """
custom cakes = Cakes made to your flavour, size and design; share the idea when you order.
birthday cakes = Cakes for celebrations; tell us the name, the age and the flavour.
cakes = Sponges layered with cream, fruit or chocolate, for any occasion.
cupcakes = Small single-serve cakes with a swirl of frosting.
brownies = Dense, fudgy chocolate squares.
cookies = Baked in batches, crisp at the edge and soft in the middle.
bread = Loaves baked for sandwiches and the breakfast table.
sourdough = Bread raised with a long-fermented starter for a tangy crumb.
sourdough bread = Bread raised with a long-fermented starter for a tangy crumb.
croissants = Flaky, buttery layers of laminated pastry.
pastries = Individual sweet bakes with cream, fruit or chocolate.
doughnuts = Soft rings of fried dough, glazed or filled.
muffins = Soft, quick-baked cakes studded with fruit or chocolate.
pies = Pastry cases with sweet or savoury fillings.
tarts = Buttery pastry shells filled with custard or fruit.
macarons = Light almond meringue sandwiches with a creamy filling.
eggless cakes = Cakes baked without eggs, in the same flavours.
cheesecake = A creamy set cake on a biscuit base.
""",
    "tea_cafe": """
masala chai = Tea simmered with milk, ginger and warming spices.
chai = Tea brewed with milk, served hot and strong.
cutting chai = A small, strong glass of tea, easy to share.
coffee = Brewed fresh, black or with milk.
cold coffee = Chilled coffee blended with milk and ice.
cappuccino = Espresso topped with steamed milk and foam.
latte = Espresso with plenty of steamed milk.
iced tea = Brewed tea served over ice with lemon or fruit.
green tea = A light, unfermented tea.
sandwiches = Bread with a filling; ask what is available today.
bun maska = A soft bun split and filled with butter, made for dipping in chai.
maggi = A quick, comforting bowl of instant maggi cooked with vegetables and spices.
hot chocolate = Cocoa and steamed milk, topped with cream.
""",
    "bar": """
cocktails = Mixed drinks built from spirits, citrus and syrups.
mocktails = Alcohol-free drinks with fruit, herbs and soda.
beer = Draught or bottled, served cold.
craft beer = Beer brewed in small batches, with more flavour.
wine = Red, white or sparkling by the glass or bottle.
whisky = Neat, on the rocks or in a cocktail.
bar snacks = Small plates to go with a drink.
live music = A band or DJ on selected nights; ask for the schedule.
happy hour = Offers on selected drinks at set times; ask for details.
""",
    "dental": """
braces = Metal or clear brackets that straighten teeth gradually.
dental implants = A titanium post and crown that replace a missing tooth.
implants = A titanium post and crown that replace a missing tooth.
root canal = Cleans out an infected tooth and seals it so it can be saved.
teeth whitening = Lifts stains so teeth look lighter.
whitening = Lifts stains so teeth look lighter.
cleaning = Removes plaque and tartar that brushing misses.
scaling = Removes tartar build-up from the teeth and gums.
check-up = A routine exam to spot problems early.
fillings = Repair cavities with tooth-coloured material.
crowns = A cap that covers and protects a weak or damaged tooth.
dentures = Removable replacement teeth.
aligners = Clear trays that move teeth step by step.
extractions = Removing a tooth that cannot be saved.
wisdom tooth removal = Taking out a wisdom tooth that is impacted or painful.
kids dentistry = Check-ups and care designed for children's teeth.
gum treatment = Treats swollen or bleeding gums.
veneers = Thin shells bonded to the front of teeth.
""",
    "skin": """
acne treatment = A plan to calm breakouts and reduce new ones.
pigmentation = Treatments that even out dark patches.
laser hair removal = Uses light to reduce unwanted hair over a few sessions.
hair fall treatment = Looks for the cause of thinning and builds a care plan.
chemical peel = A solution applied to lift dull, uneven skin.
skin consultation = A first visit to look at your skin and agree a plan.
mole removal = Removes moles for medical or cosmetic reasons after assessment.
facial = A deep-cleansing skin session with a mask and massage.
scar treatment = Reduces the look of acne and surgical scars over time.
anti-ageing = Care aimed at fine lines, firmness and sun damage.
eczema = Treatment and care plans for dry, itchy, inflamed skin.
""",
    "eye": """
eye test = Checks your vision and whether you need glasses.
eye tests = Checks your vision and whether you need glasses.
cataract surgery = Replaces a clouded lens with a clear artificial one.
lasik = Laser surgery that reshapes the cornea to reduce dependence on glasses.
glaucoma = Checks and treatment for raised pressure in the eye.
contact lenses = Fitting and advice on lenses that sit on the eye.
dry eye = Treatment for tired, gritty, watering eyes.
kids eye care = Vision checks designed for children.
retina = Checks and treatment for the light-sensing layer at the back of the eye.
spectacles = Frames and lenses made to your prescription.
squint = Assessment and treatment for eyes that do not line up.
""",
    "physio": """
back pain = Exercises and hands-on treatment for an aching back.
neck pain = Gentle mobilisation and exercises for a stiff or sore neck.
knee pain = Strengthening and movement work for sore or injured knees.
sports injury = Treatment and rehab to get you moving again.
sports injuries = Treatment and rehab to get you moving again.
post-surgery rehab = Guided exercises to rebuild strength after an operation.
posture correction = Exercises and habits that ease strain from sitting and standing.
physiotherapy = Movement-based treatment for pain, injury and recovery.
electrotherapy = Gentle electrical stimulation used to ease pain.
stroke rehabilitation = Structured exercises to regain movement and balance.
""",
    "crossfit": """
wods = Workouts of the day that mix lifting, gymnastics and cardio.
olympic lifting = Technique-led barbell lifts such as the snatch and the clean and jerk.
strength training = Heavy, structured lifting to build strength.
conditioning = Timed efforts that build stamina and pace.
gymnastics = Pull-ups, handstands and body-weight skills.
open gym = Space to train on your own between classes.
coach-led classes = A coach runs the warm-up, the lifts and the workout together.
personal training = One-to-one coaching around your goals.
""",
    "yoga": """
hatha yoga = Slow, steady postures with attention to breath.
vinyasa = Flowing sequences that link movement and breath.
pranayama = Breathing practices to steady the mind.
meditation = Sitting practice to quiet and focus the mind.
ashtanga = A set sequence of postures practised in the same order.
yin yoga = Long-held, floor-based poses for deep stretch.
prenatal yoga = Gentle practice shaped for pregnancy.
power yoga = A strong, faster-paced practice that builds strength.
restorative yoga = Supported, restful poses for recovery.
yoga classes = Group sessions led by a teacher, for different levels.
""",
    "zumba": """
zumba = Dance-based cardio to Latin and pop music.
aerobics = Rhythmic cardio routines that raise the heart rate.
hip hop = Dance classes built on grooves and street-dance moves.
bollywood dance = Film-style choreography, energetic and fun.
cardio dance = A sweaty, high-energy dance workout.
dance fitness = Workouts that feel like a party.
""",
    "kurti": """
straight kurti = A straight-cut tunic to wear with pants or leggings.
anarkali = A flared, floor-skimming kurti that moves when you do.
palazzo sets = A kurti with wide-leg trousers, sold as a set.
party wear = Dressier kurtis with embroidery or heavier fabric.
chikankari = Fine hand-embroidered work from Lucknow, light on the skin.
block print = Fabric printed with carved wooden blocks in repeating patterns.
cotton kurtis = Soft, breathable kurtis for everyday wear.
kurtis = Tunic-style tops, from everyday cotton to festive wear.
kurta sets = A kurta with matching bottoms and dupatta.
dupattas = Scarves to finish an outfit.
""",
    "saree": """
silk sarees = Woven silk drapes for weddings and festivals.
cotton sarees = Light, breathable and easy to wear every day.
banarasi = Heavy brocade weaves with gold or silver zari.
kanjivaram = Rich silk sarees with contrast borders, woven in Tamil Nadu.
georgette = Light, flowing fabric that drapes softly.
bandhani = Tie-dyed dots in bright colours, from Gujarat and Rajasthan.
bridal sarees = Heavily worked sarees for weddings.
sarees = Six yards of fabric in weaves from every region.
blouse pieces = Fabric cut to match your saree.
""",
    "electronics": """
smartphones = Phones from several brands, with advice on which suits you.
laptops = Laptops for study, work and play.
televisions = Screens in several sizes, with sound and apps built in.
tvs = Screens in several sizes, with sound and apps built in.
headphones = Wired and wireless, for music and calls.
speakers = Portable and home speakers.
smartwatches = Watches that track steps, sleep and notifications.
chargers = Chargers and cables for phones and laptops.
accessories = Cases, screen guards, cables and small add-ons.
air conditioners = Split and window units for cooling a room.
refrigerators = Single-door and double-door fridges for homes.
washing machines = Top-load and front-load machines.
""",
    "books": """
textbooks = Books for school and college courses.
fiction = Novels and stories to lose an evening in.
children's books = Picture books and early readers.
stationery = Notebooks, pens and everything for the desk.
notebooks = Ruled, plain and spiral notebooks.
competitive exam books = Guides and practice papers for entrance exams.
comics = Illustrated stories for all ages.
novels = Long-form fiction across genres.
""",
    "autosales": """
motorcycles = Bikes for commuting, touring and weekends.
bikes = Two-wheelers for the daily commute and the open road.
scooters = Easy, light two-wheelers for city riding.
electric scooters = Battery-powered scooters that charge at home.
used bikes = Pre-owned bikes; ask about condition and papers.
test ride = Ride before you decide; ask for a slot.
finance = Ways to spread the cost; ask what is available.
accessories = Helmets, guards, covers and add-ons.
helmets = Protective headgear in several sizes and styles.
""",
    "tyres": """
wheel alignment = Sets the wheels to the right angles so the car tracks straight.
wheel balancing = Evens out weight around the wheel to stop vibration.
puncture repair = Finds and fixes leaks in tubeless and tube tyres.
tubeless tyres = Tyres that hold air without an inner tube.
new tyres = Fresh rubber in the sizes and brands we stock.
nitrogen filling = Tyres filled with nitrogen instead of ordinary air.
tyre rotation = Moves tyres between positions to wear them evenly.
""",
    "robotics": """
robot kits = Parts and instructions to build a working robot.
arduino = A small programmable board for sensors, lights and motors.
coding = Writing the instructions that make a robot or a game work.
drone building = Assembling and tuning a small flying machine.
sensors = Parts that let a robot sense light, distance or touch.
stem workshops = Hands-on sessions that mix science, technology and making.
""",
    "pottery": """
wheel throwing = Shaping clay on a spinning wheel into bowls and cups.
hand building = Making forms by pinching, coiling and slabbing clay.
glazing = Painting or dipping pieces in glaze before the final firing.
kiln firing = Baking clay and glaze at high heat so they set.
ceramic mugs = Handmade mugs, each a little different.
clay = Natural, earthy material that holds whatever shape you give it.
weekend workshops = Short, beginner-friendly sessions at the wheel or table.
""",
}


def _parse(block):
    out = {}
    for line in block.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


LEX = {profile: _parse(raw) for profile, raw in _RAW.items()}


def _toks(s):
    return [t[:-1] if t.endswith("s") and len(t) > 3 else t for t in s.lower().replace("-", " ").replace("'", "").split()]


def describe(item, profile):
    """Description for an item in a profile, or None. The longest matching key wins ("wood fired pizza" over "pizza")."""
    table = LEX.get(profile)
    if not table:
        return None
    it = _toks(item)
    iset = set(it)
    best, blen = None, 0
    for key, desc in table.items():
        kt = _toks(key)
        if kt == it or (set(kt) <= iset and len(kt) >= blen) or (len(it) <= len(kt) and set(it) <= set(kt) and len(it) >= 1 and len(kt) <= len(it) + 1):
            score = len(kt) + (2 if kt == it else 0)
            if score > blen:
                best, blen = desc, score
    return best
