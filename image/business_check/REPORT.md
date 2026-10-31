# Business-prompt check (v1.2: props, scenes, concepts)

Two prompt sets, rated by eye on the rendered images.

| Set | GOOD | PARTIAL | NO | Note |
|---|---|---|---|---|
| Development set (32 prompts, used while building the props) | 32 | 0 | 0 | tuning set: **not** a fair measure |
| Holdout set (28 new prompts, never used while building) - first run | 20 | 6 | 2 | the fair measure |
| Holdout set after fixing 3 generic bugs the run exposed (sofa from the word `interior`, 3 planes from `tickets`, unrelated props from `adventure`) | 23 | 3 | 2 | |

Of the 28 holdout prompts, 4 were chosen to be outside the vocabulary (pets, tractor, plumber, tailor/sewing machine): none of those drew its subject. On the 24 prompts inside the vocabulary the first run scored 20 GOOD (83%) and after the three fixes 23 GOOD (96%).

GOOD = the main subject is recognisable and sensibly composed. PARTIAL = setting right but the subject missing. NO = prompt not understood.

## Still not covered (updated in v1.3, see the end of this file)

Anything outside the 138 props and 37 concepts: submarines, astronauts, robots, scooters and motorbikes, specific brands or products, Chinese beyond the 103 characters (光 临 价 are examples of common ones missing), faces with detail and photo-realism. Devanagari is experimental (see README). Each missing thing needs a painter (README, 'Adding your own prop') or a real image model, which this project deliberately does not use. Output is flat-illustration style, not photographic.

## Training on your own images

A model trained on 5 party-shop photos (`own_images_blend_demo.png`): row 1 your photos, row 2 the model alone (blurry look-alikes), row 3 prop scenes without the model, row 4 prop scenes with the model's learned backdrop palette (warmer orange/sand tones where those photos had them). Objects stay sharp because painters draw them; the model only supplies palette. It does not learn object shapes.

Files: `props_gallery.png` (all 138 props), `sheet1_prompts_01-16.png`, `sheet2_prompts_17-32.png`, `holdout_sheet1_01-16.png`, `holdout_sheet2_17-28.png`, `images/` and `holdout_images/` (512x320). Re-run: `python3 business_check/run_business_check.py` and `python3 business_check/run_holdout_check.py`.

## Development set

| # | Prompt | Understood | Grade | What was drawn |
|---|---|---|---|---|
| 1 | luxury beach resort at sunset | beach, hotel, sunset | **GOOD** | hotel on the beach at sunset |
| 2 | hotel in the mountains at night | hotel, 3 mountain, night | **GOOD** | hotel in front of mountains, night |
| 3 | tropical island with palm trees and blue sea | island, palm, 4 tree, 25/63/eb sea | **GOOD** | island with palms in a blue sea |
| 4 | camping tent in the forest | tent, forest | **GOOD** | tent in a forest |
| 5 | fresh pizza | pizza | **GOOD** | pizza on a table with glass and pasta |
| 6 | coffee shop | cafe | **GOOD** | cafe storefront |
| 7 | bakery with fresh bread | bakery, bread | **GOOD** | bakery storefront (+ loaf) |
| 8 | restaurant dining table | restaurant | **GOOD** | restaurant interior: plate, glass, candles |
| 9 | modern house with a garden | house, grass | **GOOD** | house on a lawn |
| 10 | city apartment buildings at dusk | city, apartment, 3 city, sunset | **GOOD** | apartment tower and skyline at dusk |
| 11 | red house with a tree | dc/26/26 house, tree | **GOOD** | exactly as asked |
| 12 | villa near the sea | villa, sea | **GOOD** | modern villa by the sea |
| 13 | software company dashboard | monitor, laptop | **GOOD** | dashboard on monitor + laptop on a desk |
| 14 | futuristic cyberpunk city at night | city, night, cyberpunk | **GOOD** | neon city |
| 15 | blue abstract technology background | abstract | **GOOD** | blue abstract backdrop |
| 16 | laptop on a desk | laptop | **GOOD** | laptop on a desk with coffee and plant |
| 17 | yoga studio | yogi | **GOOD** | meditating figure in a studio |
| 18 | green nature meditation | yogi | **GOOD** | yoga figure with plants and candles |
| 19 | mandala pattern | mandala, tiles | **GOOD** | mandala |
| 20 | doctor and medical clinic | doctor, hospital | **GOOD** | doctor in front of a hospital |
| 21 | students studying with books | 3 student, 3 book | **GOOD** | students with graduation caps and books |
| 22 | certified translation documents | document, globe, chat, 3 document | **GOOD** | globe, documents with seals, chat bubbles |
| 23 | graduation cap | gradcap | **GOOD** | graduation cap |
| 24 | university campus | university | **GOOD** | university building |
| 25 | red shoes product photo | 3 dc/26/26 shoe | **GOOD** | red sneakers with a sale tag |
| 26 | gift box | giftbox | **GOOD** | gift box with balloons, party backdrop |
| 27 | shopping bag sale | shoppingbag, tag | **GOOD** | shopping bag and sale tag |
| 28 | red heart | dc/26/26 heart | **GOOD** | red heart |
| 29 | car driving on a road at sunset | car, road, sunset | **GOOD** | red car on a road at sunset |
| 30 | wedding celebration | weddingcouple, bouquet, balloons, cake, giftbox | **GOOD** | wedding couple under a floral arch with cake, gifts, balloons |
| 31 | birthday balloons | balloons | **GOOD** | balloons with bunting and confetti |
| 32 | blue circle logo on white background | 25/63/eb circle | **GOOD** | blue circle logo mark |

## Holdout set

| # | Prompt | Understood | Grade | What was drawn |
|---|---|---|---|---|
| 1 | dental clinic with friendly dentist | hospital, doctor | **GOOD** | clinic building with a doctor |
| 2 | italian pasta restaurant interior | plate, restaurant | **GOOD** | restaurant interior (first run also showed an unwanted sofa: fixed) |
| 3 | pharmacy medicine | doctor, medicalcross | **GOOD** | doctor + medical cross |
| 4 | freshly baked croissants and coffee | 3 croissant, coffee_cup | **GOOD** | croissants and coffee |
| 5 | online learning platform on laptop | monitor, laptop, student, book, certificate | **GOOD** | laptop, monitor, student, book, certificate |
| 6 | mobile app on smartphone | phone | **GOOD** | phone + chat |
| 7 | digital marketing analytics report | monitor, laptop, chart, document | **GOOD** | chart, laptop, report |
| 8 | security shield insurance | shield | **GOOD** | shield |
| 9 | luxury watch product shot | watch | **GOOD** | watch |
| 10 | ecommerce shopping cart | cart | **GOOD** | cart |
| 11 | birthday party cake and balloons | balloons, cake, giftbox, 3 balloons | **GOOD** | cake, balloons, gifts |
| 12 | flower shop bouquet | flower, shop, bouquet | **GOOD** | shop with a flower and bouquet |
| 13 | gym with dumbbells | dumbbell, 3 dumbbell | **GOOD** | dumbbells |
| 14 | spa lotus candles relaxation | lotus, candle, plant, 3 candle, yogi | **GOOD** | lotus, candles, plant, yoga |
| 15 | law firm documents and lawyer | businessman, document, shield, 3 document | **GOOD** | lawyer, documents, shield |
| 16 | customer reviews five stars | review, 5 star | **GOOD** | review card with five stars |
| 17 | school bus on the road | bus, road | **GOOD** | school bus on a road |
| 18 | travel agency airplane tickets | airplane, suitcase, globe, 3 airplane | **GOOD** | airplane + globe + suitcase (first run drew 3 overlapping planes: fixed) |
| 19 | car dealership red car | car, dc/26/26 car | **GOOD** | red car |
| 20 | bicycle shop | bicycle, shop | **GOOD** | bicycle in front of a shop |
| 21 | real estate villa with swimming pool | villa | **GOOD** | villa with pool |
| 22 | mountain hiking adventure with tent | mountain, tent | **GOOD** | mountains and a tent (first run added unrelated plane/globe: fixed) |
| 23 | wedding photography | weddingcouple, bouquet, camera | **GOOD** | couple, arch, bouquet, camera |
| 24 | kids playground | 3 person | **PARTIAL** | people only: no playground |
| 25 | pet shop with dogs | shop | **PARTIAL** | a shop: no dogs |
| 26 | farm tractor in wheat field | grass | **NO** | a plain grass field: no tractor/wheat |
| 27 | plumber fixing pipes | - | **NO** | abstract art: nothing understood |
| 28 | tailor shop sewing machine | shop | **PARTIAL** | a shop: no tailoring/sewing machine |

## Holdout set 2 (v1.3: animals, machinery, trades, playground, readable text)

36 new prompts written after the v1.2 report and never used while building the new painters. First run: 31 GOOD / 3 PARTIAL / 2 NO. It exposed two real faults, fixed afterwards: animals, machines and people shared one row and overlapped or were cut by the picture edge (now one slot allocation, front/back rows, kept inside the frame), and `house painting services` never reached the painter concept (`painting` is a stop word; phrases added). After the fixes: **32 GOOD / 2 PARTIAL / 2 NO**. The last four prompts (fire fighters, ambulance, dentist tooth, ice skating rink) were chosen to be outside the vocabulary: none drew its subject (2 PARTIAL, 2 NO). Of the 32 in-vocabulary prompts all 32 were GOOD.

Images: `holdout2_images/`, sheets `holdout2_sheet1_01-16.png`, `holdout2_sheet2_17-32.png`, `holdout2_sheet3_33-36.png`. Re-run: `python3 business_check/run_holdout2_check.py`.

| # | Prompt | Understood | Grade | What was drawn |
|---|---|---|---|---|
| 1 | veterinary clinic with a dog and a cat | dog, cat, hospital | **GOOD** | clinic building, dog, cat |
| 2 | goldfish aquarium shop | fish, shop | **GOOD** | shop + goldfish |
| 3 | horse riding school | horse | **GOOD** | horse (school ignored) |
| 4 | dairy farm with cows | cow, tractor, sheep | **GOOD** | cows, sheep, tractor (herd overlaps a little) |
| 5 | sheep grazing on a green hill | sheep, hill | **GOOD** | sheep on a hill |
| 6 | safari wildlife elephant | elephant, parrot | **GOOD** | elephant + parrot |
| 7 | construction site with a crane and excavator | crane, excavator, worker, hardhat | **GOOD** | crane, excavator, worker, hard hat |
| 8 | tractor ploughing a field | tractor, grass | **GOOD** | tractor in a field |
| 9 | solar energy company with solar panels | solarpanel, windmill | **GOOD** | solar panels + turbine |
| 10 | wind turbines on a hill at sunset | windmill, hill, sunset | **GOOD** | three turbines at sunset |
| 11 | warehouse forklift logistics | forklift, truck | **GOOD** | forklift + truck |
| 12 | factory manufacturing | factory | **GOOD** | factory with chimneys |
| 13 | plumber fixing a leaking tap | worker, faucet, wrench, toolbox | **GOOD** | worker with plumbing tools in a workshop |
| 14 | carpenter workshop with saw and hammer | saw, hammer, toolbox, wrench, screwdriver, drill | **GOOD** | saw, hammer, drill, toolbox on a bench (small) |
| 15 | electrician wiring a house | worker, plug, lightbulb, house | **GOOD** | worker, plug, bulb, house |
| 16 | house painting services | paintroller, bucket, ladder, house | **GOOD** | house, ladder, roller, bucket (first run: house only) |
| 17 | tailor shop with sewing machine | sewingmachine, spool, tshirt, scissors, shop | **GOOD** | shop front with sewing machine, spool, shirt, scissors |
| 18 | hair salon scissors and comb | scissors, comb, plant | **GOOD** | scissors, comb, plant |
| 19 | home cleaning service | house, broom, bucket | **GOOD** | house, broom, bucket |
| 20 | car repair garage | car, toolbox, wrench, hammer, screwdriver, drill, gear | **GOOD** | car with tools around it (busy) |
| 21 | kids playground with swings and slide | child, swing, slide, seesaw | **GOOD** | swings, slide, seesaw, kids |
| 22 | cricket academy | cricket, university | **GOOD** | school building with bat and stumps |
| 23 | football tournament trophy | football, cricket, trophy | **GOOD** | football, trophy, cricket set |
| 24 | kindergarten children playing | swing, slide, seesaw, child | **GOOD** | playground with a child |
| 25 | coffee shop sign "COFFEE HOUSE" | cafe | **GOOD** | sign reads COFFEE HOUSE |
| 26 | grand opening poster "GRAND OPENING" "FREE COFFEE FOR ALL" | - | **GOOD** | poster headline + subtitle |
| 27 | logo for "GREEN LEAF" organic store | plant, shop | **GOOD** | sign reads GREEN LEAF, plant |
| 28 | sale banner "FLAT 50% OFF" red background | tag | **GOOD** | FLAT 50% OFF headline + tag |
| 29 | bakery "FRESH BREAD DAILY" sign | bakery | **GOOD** | sign reads FRESH BREAD DAILY |
| 30 | price tag "₹499" | tag | **GOOD** | tag reads the rupee price |
| 31 | hotel "SEA VIEW RESORT" beach | hotel, beach | **GOOD** | hotel sign SEA VIEW RESORT on a beach |
| 32 | birthday party "HAPPY BIRTHDAY" | balloons, cake, giftbox | **GOOD** | HAPPY BIRTHDAY with cake, gift, balloons |
| 33 | fire fighters rescue | - | **NO** | abstract art: nothing understood |
| 34 | ambulance | doctor, medicalcross | **PARTIAL** | doctor + medical cross, no ambulance vehicle |
| 35 | dentist tooth | doctor | **PARTIAL** | doctor only, no tooth |
| 36 | ice skating rink | - | **NO** | abstract art: nothing understood |

## Holdout set 3 (v1.4: emergency, dental/medical, winter, Hindi and Chinese text, crowded scenes)

32 new prompts written before the v1.4 painters existed. **First run: 23 GOOD / 7 PARTIAL / 2 NO.** It exposed generic faults, fixed afterwards: `fire truck` also drew a generic truck, `police patrol car` drew an officer and a red car, `dental chair` added an extra chair, and `training` summoned a dumbbell (phrases and words fixed). After the fixes: **26 GOOD / 4 PARTIAL / 2 NO**. The four unsupported-by-design prompts (submarine, astronaut, pizza scooter, robot) gave 0 GOOD (2 PARTIAL, 2 NO). Hindi text worked on every Hindi prompt; Chinese worked for 茶 and 咖啡 but only partly for 欢迎光临 and 特价.

Images: `holdout3_images/`, sheets `holdout3_sheet1_01-16.png`, `holdout3_sheet2_17-32.png`. Re-run: `python3 business_check/run_holdout3_check.py`.

| # | Prompt | Understood | Grade | What was drawn |
|---|---|---|---|---|
| 1 | fire station with fire truck and firefighters | firetruck, firefighter, hydrant | **GOOD** | fire truck, two firefighters, hydrant (first run: an extra white truck overlapped) |
| 2 | ambulance rushing to hospital | ambulance, hospital | **GOOD** | ambulance in front of a hospital |
| 3 | police patrol car on the road | policecar, road | **GOOD** | police car on a road (first run: officer + red car) |
| 4 | fire safety training extinguisher | extinguisher | **GOOD** | fire extinguisher (sparse; first run: cluttered with a dumbbell) |
| 5 | dentist clinic with a happy tooth | dentist, hospital, tooth | **GOOD** | dentist, tooth and medical cross in a clinic |
| 6 | dental chair and toothbrush | dentalchair, toothbrush | **GOOD** | dental chair, toothbrush, tooth, dentist (first run: an extra chair) |
| 7 | pharmacy pills and syringe | pills, syringe, medicalcross | **GOOD** | pills, syringe, medical cross |
| 8 | doctor with stethoscope and thermometer | doctor, stethoscope, thermometer | **GOOD** | doctor, stethoscope, thermometer |
| 9 | ski resort with a skier on the mountain | skier, snowboard, ski, mountain, snow | **GOOD** | skier, snowboard, skis on a snowy mountain |
| 10 | ice skating rink with a skater | skater, iceskate, snow | **GOOD** | skater and ice skate on ice |
| 11 | snowman in winter | snowman, snow | **GOOD** | snowman in falling snow |
| 12 | snowboard shop | snowboard, shop | **GOOD** | shop with a snowboard |
| 13 | ice hockey match | hockey | **GOOD** | crossed hockey sticks and puck on ice |
| 14 | sledding on a snowy hill | sled, hill, snow | **GOOD** | sled on snow |
| 15 | tea shop sign "चाय की दुकान" | cafe | **GOOD** | sign reads the Hindi words |
| 16 | poster "स्वागत है" welcome | - | **GOOD** | Hindi headline on a poster |
| 17 | banner "नमस्ते" with flowers | flower | **GOOD** | Hindi headline above flowers |
| 18 | sale poster "सेल" "50% छूट" | tag | **GOOD** | Hindi tag and headline |
| 19 | chinese restaurant sign "欢迎光临" | restaurant | **PARTIAL** | restaurant sign shows only 欢迎 (光 and 临 are not available) |
| 20 | tea shop "茶" sign | cafe | **GOOD** | sign shows 茶 |
| 21 | poster "特价" red background | - | **PARTIAL** | headline shows only 特 (价 is withheld) |
| 22 | coffee shop "咖啡 COFFEE" | cafe | **GOOD** | sign reads 咖啡 COFFEE |
| 23 | car mechanic garage with tools | car, wrench, gear, toolbox, screwdriver, hammer, drill | **GOOD** | car with tools in a foreground row |
| 24 | farm with tractor cows and sheep | tractor, cow, sheep | **GOOD** | tractor, cows, sheep |
| 25 | construction workers with crane and excavator | crane, excavator, worker, hardhat, team | **GOOD** | crane, excavator, workers |
| 26 | online shop with phone laptop and shopping cart | monitor, laptop, shop, phone, cart | **GOOD** | shop with laptop, phone, cart |
| 27 | school with students books and playground | student, book, swing, slide, seesaw, child | **GOOD** | students, books, playground (no school building) |
| 28 | hospital with doctor nurse and ambulance | hospital, doctor, ambulance | **GOOD** | hospital, doctor, ambulance |
| 29 | submarine under the sea | sea | **PARTIAL** | only the sea: no submarine |
| 30 | astronaut on the moon | moon | **NO** | plain landscape: no astronaut |
| 31 | pizza delivery scooter | pizza, truck, bicycle | **PARTIAL** | pizza, delivery truck, bicycle: no scooter |
| 32 | robot | - | **NO** | abstract art: nothing understood |
