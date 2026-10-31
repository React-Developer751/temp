"""Public sites per sub-niche (profile). Only public pages are read; robots.txt is respected by fetch_profiles.py.
About one site in five (by hash of its host) is held out: it is fetched into data/profile_holdout.json and never trained on."""
PROFILE_SOURCES = {
    # food
    "italian": ["https://www.zizzi.co.uk", "https://www.prezzorestaurants.co.uk", "https://www.bellaitalia.co.uk", "https://www.askitalian.co.uk", "https://www.francomanca.co.uk",
                "https://www.pizzaexpress.com", "https://www.papajohns.com", "https://www.littlecaesars.com", "https://www.carluccios.com", "https://www.pizzahut.com", "https://www.olivegarden.com"],
    "north_indian": ["https://www.dishoom.com", "https://www.barbequenation.com", "https://www.bikanervala.com", "https://www.haldirams.com", "https://www.karimhotels.com", "https://www.punjabigrill.in",
                     "https://www.rajdhanirestaurants.com", "https://www.chickinn.com", "https://www.mcdonaldsindia.com"],
    "south_indian": ["https://www.saravanabhavan.com", "https://www.mtrfoods.com", "https://www.aabsweets.com", "https://www.sangeethaveg.com", "https://www.udupigrand.com", "https://www.ricebowl.in",
                     "https://www.murugansidli.com"],
    "chinese": ["https://www.pandaexpress.com", "https://www.wagamama.com", "https://www.chingsecret.com", "https://www.wowmomo.com", "https://www.hakkasan.com", "https://www.yauatcha.com",
                "https://www.pfchangs.com", "https://www.dinetai.com"],
    "street_food": ["https://www.faasos.io", "https://www.wowmomo.com", "https://www.burgerking.in", "https://www.pavbhaji.in", "https://www.streetfoodfestival.in", "https://www.nandosindia.in"],
    "bakery": ["https://www.theobroma.in", "https://www.monginis.net", "https://www.greggs.co.uk", "https://www.gailsbread.co.uk", "https://www.krispykreme.com", "https://www.nothingbundtcakes.com",
               "https://www.insomniacookies.com", "https://www.breadtalk.com", "https://www.paul-uk.com"],
    "tea_cafe": ["https://www.chaayos.com", "https://www.chaipoint.com", "https://www.chaisuttabar.com", "https://www.cafecoffeeday.com", "https://www.bluetokaicoffee.com", "https://www.costa.co.uk",
                 "https://www.caffenero.com", "https://www.twinings.co.uk", "https://www.teabox.com"],
    "bar": ["https://www.brewdog.com", "https://www.fullers.co.uk", "https://www.greeneking.co.uk", "https://www.tgifridays.com", "https://www.hardrockcafe.com", "https://www.slugandlettuce.co.uk"],
    # health
    "dental": ["https://www.clovedental.in", "https://www.mydentist.co.uk", "https://www.mouthhealthy.org", "https://www.colgate.com", "https://www.dentalhealth.org", "https://www.bupa.co.uk",
               "https://www.dentistry.co.uk", "https://www.smiledirectclub.com"],
    "skin": ["https://www.kayaclinic.com", "https://www.olivaclinic.com", "https://www.aad.org", "https://dermnetnz.org", "https://www.skinvision.com", "https://www.vlccwellness.com"],
    "eye": ["https://www.dragarwal.com", "https://www.maxivisioneyehospitals.com", "https://www.lvpei.org", "https://www.specsavers.co.uk", "https://www.aao.org", "https://www.nei.nih.gov",
            "https://www.visionexpress.com"],
    "physio": ["https://www.csp.org.uk", "https://www.choosept.com", "https://www.physio-pedia.com", "https://www.nhs.uk/conditions/physiotherapy", "https://www.physio.co.uk", "https://www.bupa.co.uk/health-information"],
    # fitness
    "crossfit": ["https://www.crossfit.com", "https://www.f45training.com", "https://www.orangetheory.com", "https://www.barrys.com"],
    "yoga": ["https://www.yogaalliance.org", "https://www.artofliving.org", "https://www.yogajournal.com", "https://www.corepoweryoga.com", "https://www.yogaworks.com", "https://www.isha.sadhguru.org"],
    "zumba": ["https://www.zumba.com", "https://www.cult.fit", "https://www.dancefitness.com", "https://www.jazzercise.com"],
    # retail
    "kurti": ["https://www.fabindia.com", "https://www.biba.in", "https://www.wforwoman.com", "https://www.aurelia.in", "https://www.libas.in", "https://www.globaldesi.in"],
    "saree": ["https://www.nalli.com", "https://www.pothys.com", "https://www.kalanikethan.com", "https://www.taneira.com", "https://www.mysilkroute.com", "https://www.cbazaar.com"],
    "electronics": ["https://www.croma.com", "https://www.reliancedigital.in", "https://www.vijaysales.com", "https://www.currys.co.uk", "https://www.argos.co.uk", "https://www.bestbuy.com"],
    "books": ["https://www.crossword.in", "https://www.bookswagon.com", "https://www.waterstones.com", "https://www.blackwells.co.uk", "https://www.booktopia.com.au", "https://www.bookshop.org"],
    "autosales": ["https://www.heromotocorp.com", "https://www.bajajauto.com", "https://www.tvsmotor.com", "https://www.royalenfield.com", "https://www.honda2wheelersindia.com", "https://www.marutisuzuki.com",
                  "https://www.yamaha-motor-india.com", "https://www.carwale.com"],
    "tyres": ["https://www.mrftyres.com", "https://www.ceat.com", "https://www.apollotyres.com", "https://www.michelin.in", "https://www.bridgestone.com", "https://www.kwik-fit.com"],
    # learning, creative
    "robotics": ["https://www.makeblock.com", "https://education.lego.com", "https://www.arduino.cc", "https://www.firstinspires.org", "https://www.stemrobotics.com", "https://www.codingal.com"],
    "pottery": ["https://www.ceramicartsnetwork.org", "https://www.americanceramics.org", "https://www.claycentre.com", "https://www.mudcolour.com", "https://www.potterycrafters.com"],
}

# second batch: recipe, guide and information sites for the thinly covered profiles (public pages only, robots.txt respected)
_MORE = {
    "italian": ["https://www.giallozafferano.com", "https://www.bbcgoodfood.com/recipes/collection/italian-recipes", "https://www.seriouseats.com/italian-recipes"],
    "north_indian": ["https://www.vegrecipesofindia.com", "https://www.cookwithmanali.com", "https://www.indianhealthyrecipes.com"],
    "south_indian": ["https://www.hebbarskitchen.com", "https://www.archanaskitchen.com", "https://www.sinfullyspicy.com"],
    "chinese": ["https://thewoksoflife.com", "https://www.chinasichuanfood.com", "https://www.omnivorescookbook.com"],
    "street_food": ["https://www.indianhealthyrecipes.com/pani-puri-recipe", "https://www.cookwithmanali.com/pav-bhaji", "https://www.vegrecipesofindia.com/vada-pav-recipe"],
    "bakery": ["https://www.kingarthurbaking.com", "https://sallysbakingaddiction.com", "https://www.bbcgoodfood.com/recipes/collection/cake-recipes"],
    "tea_cafe": ["https://www.teaforturmeric.com", "https://www.bbcgoodfood.com/recipes/collection/tea-recipes", "https://www.indianhealthyrecipes.com/masala-chai-recipe"],
    "bar": ["https://www.liquor.com", "https://www.diffordsguide.com", "https://www.bbcgoodfood.com/recipes/collection/cocktail-recipes"],
    "kurti": ["https://www.utsavfashion.com", "https://www.craftsvilla.com", "https://www.indianclothstore.com"],
    "saree": ["https://www.utsavfashion.com/saree", "https://www.craftsvilla.com/sarees"],
    "dental": ["https://www.nidcr.nih.gov", "https://www.nhs.uk/conditions/dental-health", "https://www.mouthhealthy.org/all-topics-a-z"],
    "electronics": ["https://www.gsmarena.com", "https://www.which.co.uk/reviews"],
}
for _p, _urls in _MORE.items():
    PROFILE_SOURCES[_p] = PROFILE_SOURCES.get(_p, []) + [u for u in _urls if u not in PROFILE_SOURCES.get(_p, [])]
