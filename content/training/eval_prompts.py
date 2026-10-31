"""60 fresh prompts (15 niches x 4; English, Hinglish, Hindi) with the services each one names.
Used only by training/evaluate.py: none of these prompts was used to build or tune the engine.
Each row: (niche, language, prompt, services that must appear on the page).
"""

EVAL = [
    # italian
    ("italian", "en", "Italian restaurant Forno Rosso, Mumbai, wood fired pizza, fresh pasta, tiramisu, weekend brunch, open 12pm to 11pm, online booking",
     ["wood fired pizza", "fresh pasta", "tiramisu", "weekend brunch"]),
    ("italian", "en", "Trattoria Bella Vita in Pune serving risotto, lasagna, bruschetta and gelato. Call 9822012345", ["risotto", "lasagna", "bruschetta", "gelato"]),
    ("italian", "hinglish", "mera Italian restaurant Casa Verde hai Delhi mein, pizza, pasta aur garlic bread, raat 11 baje tak khula, home delivery", ["pizza", "pasta", "garlic bread"]),
    ("italian", "hi", "बेंगलुरु में इटैलियन रेस्टोरेंट: पिज़्ज़ा, पास्ता, तिरामिसू और गार्लिक ब्रेड", ["पिज़्ज़ा", "पास्ता", "तिरामिसू", "गार्लिक ब्रेड"]),
    # north indian
    ("north_indian", "en", "North Indian restaurant Dhaba Express in Jaipur, butter chicken, dal makhani, paneer tikka, naan, biryani, free home delivery", ["butter chicken", "dal makhani", "paneer tikka", "naan", "biryani"]),
    ("north_indian", "en", "Punjabi dhaba called Sher-e-Punjab, Ludhiana, tandoori chicken, chole bhature, lassi and rajma chawal, open 9am to 11pm", ["tandoori chicken", "chole bhature", "lassi", "rajma chawal"]),
    ("north_indian", "hinglish", "mujhe ek restaurant ki website chahiye, naam Royal Rasoi, Lucknow mein, kebab, biryani, thali aur gulab jamun, parties bhi", ["kebab", "biryani", "thali", "gulab jamun"]),
    ("north_indian", "hi", "नोएडा में पंजाबी ढाबा: बटर चिकन, दाल तड़का, तंदूरी रोटी और लस्सी, रात 11 बजे तक खुला", ["बटर चिकन", "दाल तड़का", "तंदूरी रोटी", "लस्सी"]),
    # south indian
    ("south_indian", "en", "South Indian restaurant Udupi Bhavan, Chennai, masala dosa, idli, vada, filter coffee, pure veg, open 7am to 10pm", ["masala dosa", "idli", "vada", "filter coffee"]),
    ("south_indian", "en", "Dosa corner in Bangalore selling rava dosa, uttapam, pongal and sambar, takeaway available", ["rava dosa", "uttapam", "pongal", "sambar"]),
    ("south_indian", "hinglish", "mera South Indian tiffin centre Hyderabad mein hai, idli, dosa, upma aur rasam, subah 7 se raat 10 tak", ["idli", "dosa", "upma", "rasam"]),
    ("south_indian", "hi", "चेन्नई में दक्षिण भारतीय रेस्टोरेंट: मसाला डोसा, इडली, वड़ा और सांभर", ["मसाला डोसा", "इडली", "वड़ा", "सांभर"]),
    # chinese
    ("chinese", "en", "Chinese restaurant Golden Wok in Kolkata, hakka noodles, manchurian, momos, hot and sour soup, online booking", ["hakka noodles", "manchurian", "momos", "hot and sour soup"]),
    ("chinese", "en", "Indo Chinese food joint called Wok Station, Ahmedabad, schezwan noodles, fried rice, chilli paneer and spring roll", ["schezwan noodles", "fried rice", "chilli paneer", "spring roll"]),
    ("chinese", "hinglish", "mera Chinese restaurant Dragon House hai Surat mein, noodles, momos aur manchurian, home delivery, raat 10 baje tak", ["noodles", "momos", "manchurian"]),
    ("chinese", "hi", "इंदौर में चाइनीज़ रेस्टोरेंट: हक्का नूडल्स, मोमोज़, मंचूरियन और फ्राइड राइस", ["हक्का नूडल्स", "मोमोज़", "मंचूरियन", "फ्राइड राइस"]),
    # bakery
    ("bakery", "en", "Bakery called Sweet Crumbs in Pune, custom cakes, cupcakes, brownies, sourdough bread, eggless cakes, home delivery", ["custom cakes", "cupcakes", "brownies", "sourdough bread", "eggless cakes"]),
    ("bakery", "en", "Cake shop Baker's Basket, Delhi, birthday cakes, cookies, pastries and croissants, open 9am to 9pm", ["birthday cakes", "cookies", "pastries", "croissants"]),
    ("bakery", "hinglish", "mujhe ek bakery ki website chahiye, naam Cake Corner, Jaipur mein, cakes, pastries aur cookies, eggless bhi", ["cakes", "pastries", "cookies"]),
    ("bakery", "hi", "लखनऊ में बेकरी: केक, पेस्ट्री, ब्राउनी और कुकीज़", ["केक", "पेस्ट्री", "ब्राउनी", "कुकीज़"]),
    # tea cafe
    ("tea_cafe", "en", "Chai cafe Kulhad Wala in Delhi, masala chai, cutting chai, bun maska, maggi, open 8am to 11pm", ["masala chai", "cutting chai", "bun maska", "maggi"]),
    ("tea_cafe", "en", "Coffee shop Bean There in Bangalore serving cappuccino, cold coffee, sandwiches and brownies, free wifi", ["cappuccino", "cold coffee", "sandwiches", "brownies"]),
    ("tea_cafe", "hinglish", "mera chai cafe Chai Point Jaipur mein hai, masala chai, green tea aur samosa, subah 8 se raat 10 tak", ["masala chai", "green tea", "samosa"]),
    ("tea_cafe", "hi", "पुणे में चाय कैफे: मसाला चाय, कटिंग चाय, मैगी और सैंडविच", ["मसाला चाय", "कटिंग चाय", "मैगी", "सैंडविच"]),
    # dental
    ("dental", "en", "Dental clinic called Smile Hub in Pune offering braces, dental implants, root canal and teeth whitening, call 9876543210", ["braces", "dental implants", "root canal", "teeth whitening"]),
    ("dental", "en", "Dentist in Chandigarh for kids dentistry, aligners, crowns and wisdom tooth removal, free consultation, open 10am to 7pm", ["kids dentistry", "aligners", "crowns", "wisdom tooth removal"]),
    ("dental", "hinglish", "mujhe ek dental clinic ki website chahiye, Bright Smiles, Nagpur mein, braces, implants, cleaning aur whitening", ["braces", "implants", "cleaning", "whitening"]),
    ("dental", "hi", "दिल्ली में दांतों का क्लिनिक: डेंटल इम्प्लांट, ब्रेसेज़, रूट कैनाल और दांत की सफाई", ["डेंटल इम्प्लांट", "ब्रेसेज़", "रूट कैनाल", "दांत की सफाई"]),
    # skin
    ("skin", "en", "Skin clinic DermaCare in Mumbai, acne treatment, pigmentation, laser hair removal, hair fall treatment, free consultation", ["acne treatment", "pigmentation", "laser hair removal", "hair fall treatment"]),
    ("skin", "en", "Dermatologist in Hyderabad for chemical peel, scar treatment, mole removal and anti-ageing, online booking", ["chemical peel", "scar treatment", "mole removal", "anti-ageing"]),
    ("skin", "hinglish", "mera skin clinic Glow Skin hai Jaipur mein, acne, pigmentation aur hair fall ka ilaj", ["acne", "pigmentation", "hair fall"]),
    ("skin", "hi", "लखनऊ में त्वचा क्लिनिक: मुहांसे का इलाज, पिग्मेंटेशन, लेज़र हेयर रिमूवल और स्कार ट्रीटमेंट", ["मुहांसे का इलाज", "पिग्मेंटेशन", "लेज़र हेयर रिमूवल", "स्कार ट्रीटमेंट"]),
    # gym / crossfit
    ("gym", "en", "CrossFit box Iron Forge in Delhi, WODs, olympic lifting, strength training, personal training, free trial", ["wods", "olympic lifting", "strength training", "personal training"]),
    ("gym", "en", "Gym FitHub in Bangalore, weight training, cardio, group classes and zumba, open 5am to 10pm", ["weight training", "cardio", "group classes", "zumba"]),
    ("gym", "hinglish", "mera gym Muscle Factory hai Pune mein, weight training, cardio aur personal training, free trial", ["weight training", "cardio", "personal training"]),
    ("gym", "hi", "जयपुर में जिम: वेट ट्रेनिंग, कार्डियो, ज़ुम्बा और पर्सनल ट्रेनिंग", ["वेट ट्रेनिंग", "कार्डियो", "ज़ुम्बा", "पर्सनल ट्रेनिंग"]),
    # yoga
    ("yoga", "en", "Yoga studio Prana in Rishikesh, hatha yoga, vinyasa, pranayama, meditation and prenatal yoga, book a class online", ["hatha yoga", "vinyasa", "pranayama", "meditation", "prenatal yoga"]),
    ("yoga", "en", "Yoga centre called Shanti in Mumbai offering power yoga, yin yoga, restorative yoga and yoga classes for beginners", ["power yoga", "yin yoga", "restorative yoga"]),
    ("yoga", "hinglish", "mujhe ek yoga studio ki website chahiye, naam Om Yoga, Delhi mein, hatha yoga, pranayama aur meditation", ["hatha yoga", "pranayama", "meditation"]),
    ("yoga", "hi", "ऋषिकेश में योग केंद्र: हठ योग, प्राणायाम, ध्यान और योग क्लास", ["हठ योग", "प्राणायाम", "ध्यान", "योग क्लास"]),
    # kurti
    ("kurti", "en", "Ladies kurti boutique Rani Boutique in Jaipur, cotton kurtis, anarkali, palazzo sets, chikankari, free shipping, COD, easy returns", ["cotton kurtis", "anarkali", "palazzo sets", "chikankari"]),
    ("kurti", "en", "Kurti shop Ethnic Threads in Lucknow selling block print, party wear, kurta sets and dupattas, kurtis starting Rs 599", ["block print", "party wear", "kurta sets", "dupattas"]),
    ("kurti", "hinglish", "mera kurti showroom Style Hub hai Surat mein, cotton kurtis, anarkali aur palazzo sets, COD available", ["cotton kurtis", "anarkali", "palazzo sets"]),
    ("kurti", "hi", "जयपुर में कुर्ती शोरूम: कॉटन कुर्ती, अनारकली, पलाज़ो सेट और दुपट्टे", ["कॉटन कुर्ती", "अनारकली", "पलाज़ो सेट", "दुपट्टे"]),
    # electronics
    ("electronics", "en", "Electronics store TechZone in Delhi, smartphones, laptops, headphones, smartwatches, easy EMI, warranty", ["smartphones", "laptops", "headphones", "smartwatches"]),
    ("electronics", "en", "Mobile and electronics shop Gadget World in Indore selling televisions, speakers, chargers and accessories, open 10am to 9pm", ["televisions", "speakers", "chargers", "accessories"]),
    ("electronics", "hinglish", "mera electronics showroom Digital Plaza hai Pune mein, smartphones, laptops aur televisions, EMI available", ["smartphones", "laptops", "televisions"]),
    ("electronics", "hi", "नागपुर में इलेक्ट्रॉनिक्स स्टोर: स्मार्टफोन, लैपटॉप, टीवी और हेडफोन", ["स्मार्टफोन", "लैपटॉप", "टीवी", "हेडफोन"]),
    # software
    ("software", "en", "SaaS startup InvoiceFlow, Bangalore, invoicing, payment reminders, expense tracking and reports, free trial", ["invoicing", "payment reminders", "expense tracking", "reports"]),
    ("software", "en", "Software development company CodeCraft in Pune offering web apps, mobile apps, API integrations and cloud migration", ["web apps", "mobile apps", "api integrations", "cloud migration"]),
    ("software", "hinglish", "mera software startup TaskNest hai Hyderabad mein, task tracking, team chat aur reports, free trial", ["task tracking", "team chat", "reports"]),
    ("software", "hi", "बेंगलुरु में सॉफ्टवेयर कंपनी: वेब ऐप, मोबाइल ऐप, इनवॉइसिंग और रिपोर्ट", ["वेब ऐप", "मोबाइल ऐप", "इनवॉइसिंग", "रिपोर्ट"]),
    # education
    ("education", "en", "Coaching institute Gyan Academy in Kota, IIT JEE coaching, NEET preparation, class 11 and 12 maths and physics, free demo class", ["iit jee coaching", "neet preparation", "maths", "physics"]),
    ("education", "en", "Tuition centre Bright Minds in Delhi for maths tuition, science tuition, English speaking and board exam preparation", ["maths tuition", "science tuition", "english speaking", "board exam preparation"]),
    ("education", "hinglish", "mera coaching institute Success Point hai Jaipur mein, maths, science aur English, free demo class", ["maths", "science", "english"]),
    ("education", "hi", "पटना में कोचिंग सेंटर: गणित, विज्ञान, अंग्रेज़ी और बोर्ड परीक्षा की तैयारी", ["गणित", "विज्ञान", "अंग्रेज़ी", "बोर्ड परीक्षा की तैयारी"]),
    # plumbing / home services
    ("plumbing", "en", "Plumber Quick Fix in Mumbai, leakage repair, bathroom fitting, pipe fitting and water tank cleaning, free quote, open 8am to 8pm", ["leakage repair", "bathroom fitting", "pipe fitting", "water tank cleaning"]),
    ("plumbing", "en", "Plumbing contractor called Aqua Works, Chennai, drain cleaning, geyser installation, tap repair and motor repair, call 9840012345", ["drain cleaning", "geyser installation", "tap repair", "motor repair"]),
    ("plumbing", "hinglish", "mujhe ek plumber ki website chahiye, naam Sharma Plumbing, Delhi mein, leakage, bathroom fitting aur tap repair, free quote", ["leakage", "bathroom fitting", "tap repair"]),
    ("plumbing", "hi", "पुणे में प्लंबर: लीकेज मरम्मत, बाथरूम फिटिंग, नल की मरम्मत और पाइप फिटिंग", ["लीकेज मरम्मत", "बाथरूम फिटिंग", "नल की मरम्मत", "पाइप फिटिंग"]),
]


# A second, smaller set written after the fixes above: a check that the writer is not just tuned to the 60 prompts.
FRESH = [
    ("italian", "en", "Pizzeria Napoli in Goa serving margherita pizza, calzone, lasagna and panna cotta, takeaway available", ["margherita pizza", "calzone", "lasagna", "panna cotta"]),
    ("north_indian", "hinglish", "mera dhaba Punjabi Tadka hai Amritsar mein, sarson da saag, makki di roti, lassi aur paneer tikka, parties bhi", ["sarson da saag", "makki di roti", "lassi", "paneer tikka"]),
    ("south_indian", "en", "South Indian tiffin centre Annapoorna, Coimbatore, idli, ghee dosa, pongal, medu vada and filter coffee, open 6am to 10pm", ["idli", "ghee dosa", "pongal", "medu vada", "filter coffee"]),
    ("chinese", "hi", "मुंबई में चाइनीज़ रेस्टोरेंट: ड्रैगन चिकन, स्प्रिंग रोल, हॉट एंड सोर सूप और नूडल्स", ["ड्रैगन चिकन", "स्प्रिंग रोल", "हॉट एंड सोर सूप", "नूडल्स"]),
    ("bakery", "en", "Bakery called Flour & Butter in Hyderabad, croissants, sourdough, cheesecake and macarons, home delivery", ["croissants", "sourdough", "cheesecake", "macarons"]),
    ("tea_cafe", "hinglish", "mera tea cafe Chai Adda hai Bhopal mein, masala chai, bun maska, maggi aur cold coffee, subah 7 se raat 10 tak", ["masala chai", "bun maska", "maggi", "cold coffee"]),
    ("dental", "en", "Dental clinic SmilePoint in Kochi, teeth cleaning, veneers, braces, gum treatment, online booking, call 9847012345", ["teeth cleaning", "veneers", "braces", "gum treatment"]),
    ("skin", "hi", "दिल्ली में स्किन क्लिनिक: मुहांसे का इलाज, चेहरे की सफाई, लेज़र ट्रीटमेंट और बालों का झड़ना", ["मुहांसे का इलाज", "चेहरे की सफाई", "लेज़र ट्रीटमेंट", "बालों का झड़ना"]),
    ("gym", "en", "Fitness studio Power House in Gurgaon, zumba, personal training, weight training and cardio, free trial, open 5am to 10pm", ["zumba", "personal training", "weight training", "cardio"]),
    ("yoga", "hinglish", "mera yoga centre Pranayam hai Haridwar mein, hatha yoga, ashtanga, meditation aur yoga classes", ["hatha yoga", "ashtanga", "meditation", "yoga classes"]),
    ("kurti", "en", "Boutique Kurti Kart in Indore selling straight kurtis, anarkali, kurta sets and dupattas, free shipping, COD, easy returns", ["straight kurtis", "anarkali", "kurta sets", "dupattas"]),
    ("electronics", "en", "Electronics shop Smart Mart in Ranchi, smartphones, tvs, headphones and air conditioners, EMI available, warranty", ["smartphones", "tvs", "headphones", "air conditioners"]),
    ("software", "hinglish", "mera software startup LedgerLite hai Pune mein, bookkeeping, GST reports aur payroll, free trial", ["bookkeeping", "gst reports", "payroll"]),
    ("education", "en", "Coaching classes Topper Zone in Lucknow for class 10 maths, science, English and board exam preparation, free demo class", ["maths", "science", "english", "board exam preparation"]),
    ("plumbing", "hi", "नोएडा में प्लंबर: गीजर इंस्टॉलेशन, नल की मरम्मत, बाथरूम फिटिंग और ड्रेन सफाई", ["गीजर इंस्टॉलेशन", "नल की मरम्मत", "बाथरूम फिटिंग", "ड्रेन सफाई"]),
    (None, "hinglish", "mujhe ek bike showroom ki website chahiye, naam Speed Motors, Jaipur mein, Hero aur Honda bikes, test ride, finance", ["test ride", "finance"]),
    (None, "en", "Robotics lab RoboKids in Pune, robot kits, arduino workshops, coding and drone building, free demo class", ["robot kits", "arduino workshops", "coding", "drone building"]),
    (None, "en", "Pottery studio Clay & Co in Jaipur, wheel throwing, hand building, glazing and weekend workshops", ["wheel throwing", "hand building", "glazing", "weekend workshops"]),
    (None, "hinglish", "mera tyre shop Wheel World hai Nagpur mein, wheel alignment, puncture repair aur new tyres, subah 9 se raat 8 tak", ["wheel alignment", "puncture repair", "new tyres"]),
    (None, "en", "Packers and movers called Safe Move in Bangalore, house shifting, car transport, storage, free quote, call 9811122233", ["house shifting", "car transport", "storage"]),
    (None, "hi", "जयपुर में किराना स्टोर: आटा, दाल, चावल और सब्जी, होम डिलीवरी", ["आटा", "दाल", "चावल", "सब्जी"]),
    (None, "en", "Ladies beauty parlour Glam Studio in Delhi, bridal makeup, facials, hair spa and threading, online booking", ["bridal makeup", "facials", "hair spa", "threading"]),
    (None, "en", "Travel agency Wanderlust in Kochi, Kerala tour packages, Goa trips, honeymoon packages and visa help", ["kerala tour packages", "goa trips", "honeymoon packages", "visa help"]),
    (None, "en", "Law firm Verma & Associates in Delhi for property disputes, family law, wills and cheque bounce cases", ["property disputes", "family law", "wills", "cheque bounce cases"]),
]
