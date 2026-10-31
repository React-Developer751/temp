"""The general packs of the author's list (corecraft/data/author_niches.json), one per text-bank family (plus "general" for a request that names no trade).
The default list has the spec's own 20 business types instead (corecraft/pack_spec.py SPEC_TYPES).
It must be true for every business of the family, so the six "items" are ways of working (clear quotes, easy booking), not one trade.
training/build_niches.py adds the keywords (from the business types of the family) and writes them into corecraft/data/author_niches.json."""

TYPES = {   # theme -> (label, family, six general items, sample prices, button)
    "home": ("Home and field service", "home", ["Clear Quotes", "Local Team", "Tidy Work", "Time Slots", "Plain Explanations", "Follow Up Care"],
             [(8, "/visit"), (25, "/job"), (60, "/project")], "Book A Home Visit"),
    "auto": ("Vehicle and transport service", "auto", ["Clear Estimates", "Slot Booking", "Plain Explanations", "Update Messages", "Careful Handling", "Friendly Service"],
             [(6, "/check"), (20, "/service"), (60, "/full service")], "Book A Slot"),
    "project": ("Design and build studio", "project", ["Brief First Approach", "Draft Reviews", "Clear Timelines", "Format Delivery", "Revision Rounds", "Friendly Collaboration"],
                [(0, "/consultation"), (120, "/small project"), (400, "/full project")], "Start Your Project"),
    "retail": ("Neighbourhood shop", "retail", ["Careful Selection", "Helpful Staff", "Easy Exchange Advice", "Gift Wrapping", "Order Ahead", "Fair Prices"],
               [(5, "/item"), (20, "/gift set"), (50, "/bundle")], "Visit The Shop"),
    "food": ("Restaurant and cafe", "food", ["Fresh Cooking", "Easy Ordering", "Table Reservations", "Dietary Questions Welcome", "Takeaway Options", "Friendly Service"],
             [(4, "/main course"), (8, "/combo"), (25, "/family table")], "Order Or Reserve"),
    "food_order": ("Bakery and sweets", "food_order", ["Fresh Batches", "Order Ahead", "Party Boxes", "Gift Packing", "Pickup Or Delivery", "Ingredient Questions Welcome"],
                   [(3, "/small order"), (10, "/party box"), (30, "/celebration order")], "Place An Order"),
    "clinic": ("Clinic and care", "clinic", ["Easy Appointments", "Time For Questions", "Plain Explanations", "Follow Up Guidance", "Clear Fees", "Calm Waiting Area"],
               [(5, "/consultation"), (15, "/checkup"), (40, "/care plan")], "Book An Appointment"),
    "session": ("Beauty and fitness studio", "session", ["Relaxed Sessions", "Personal Plans", "Easy Booking", "Clean Spaces", "Friendly Team", "Aftercare Tips"],
                [(5, "/session"), (30, "/month"), (80, "/quarter")], "Book A Session"),
    "pro": ("Advisory and professional firm", "pro", ["Clear First Call", "Plain Advice", "Written Next Steps", "Fees Told Upfront", "Private Handling", "Regular Updates"],
            [(0, "/consultation"), (40, "/review"), (150, "/full support")], "Book A Consultation"),
    "edu": ("Classes and coaching", "edu", ["Demo Class Option", "Small Batches", "Regular Practice", "Progress Updates", "Doubt Clearing", "Flexible Timings"],
            [(12, "/month"), (30, "/month"), (80, "/term")], "Book A Demo Class"),
    "events": ("Events and celebrations", "events", ["Planning Support", "Checklist Approach", "Vendor Coordination", "Decor Ideas", "Day Of Support", "Clear Quotes"],
               [(150, "/event"), (500, "/wedding"), (1500, "/large wedding")], "Plan Your Event"),
    "stay": ("Travel and stay", "stay", ["Custom Plans", "Clear Inclusions", "Easy Booking", "Local Tips", "Flexible Dates", "Quick Replies"],
             [(20, "/night"), (90, "/weekend"), (200, "/week")], "Check Dates"),
    "property": ("Property and rentals", "property", ["Clear Listings", "Honest Details", "Viewing Support", "Paperwork Guidance", "Cost Explanations", "Friendly Advice"],
                 [(0, "/consultation"), (30, "/property search"), (80, "/full service")], "Book A Viewing"),
    "nonprofit": ("Community organisation", "nonprofit", ["Open Reporting", "Volunteer Roles", "Donation Options", "Community Programmes", "Event Updates", "Easy Contact"],
                  [(2, "/month"), (10, "/month"), (30, "/month")], "Support Our Work"),
    "software": ("Software and IT", "software", ["Clear Onboarding", "Simple Setup", "Friendly Support", "Regular Updates", "Careful Data Handling", "Flexible Plans"],
                 [(9, "/month"), (29, "/month"), (79, "/month")], "Book A Demo"),
    "general": ("Neighbourhood business", "home", ["Friendly Local Service", "Clear Pricing", "Easy Contact", "Honest Advice", "On Time Updates", "Quick Replies"],
                [(5, "/job"), (20, "/job"), (60, "/job")], "Contact Us Today"),
}
GENERAL_KEYWORDS = ["local business", "small business", "neighbourhood business", "family business", "local shop", "local service", "own business", "startup business"]
TYPE_MENU = ("On The Menu", "A simple menu of fresh favourites, made to order. Ask the team about ingredients or any dietary need.",
             [("Starters", ["Soup of the day", "Veg spring rolls", "Grilled paneer | with mint dip", "Crispy corn", "Fresh salad"]),
              ("Main Course", ["Dal and rice", "Paneer curry", "Veg pulao | gently spiced", "Pasta of the day", "Grilled sandwich", "Chef's special | ask the team"]),
              ("Desserts", ["Gulab jamun | with warm syrup", "Ice cream", "Brownie", "Fruit custard", "Kulfi | on a stick"]),
              ("Drinks", ["Masala chai", "Cold coffee", "Fresh lime soda", "Lassi | sweet or salted", "Seasonal juice"])])
ORDER_MENU = ("Fresh Today", "Small batches made through the day, with boxes for parties and gifts. Order ahead for bigger days.",
              [("Cakes And Bakes", ["Chocolate cake", "Vanilla sponge", "Fruit cake", "Cupcake box", "Brownie"]),
               ("Sweets", ["Kaju katli", "Besan ladoo", "Rasgulla", "Milk barfi", "Gulab jamun"]),
               ("Cold Treats", ["Vanilla scoop", "Mango kulfi", "Chocolate sundae", "Milkshake", "Falooda"])])
TYPE_MENUS = {"food": TYPE_MENU, "food_order": ORDER_MENU}
