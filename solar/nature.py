"""What's happening out in the food forest and the native prairie, and what to look for.

Willamette Valley timing, for Sauvie Island. Each day shows a rotating few from the month,
plus anything this week's weather sets off.
"""
import datetime as dt

# month -> list of things to look for
FOREST = {
    1: ["Hazelnut catkins lengthen and dangle. Look closely for the tiny red tufts of the female flowers on the same branches.",
        "Indian plum (osoberry) is often the first shrub to leaf out, a bright green flicker in the bare woods.",
        "Check under the mulch near trunks for vole runways and gnawed bark.",
        "Robins and varied thrushes are working over any fruit left hanging.",
        "Look for fat, round flower buds versus slim, pointed leaf buds on the apples to plan pruning."],
    2: ["Red-flowering currant starts blooming late in the month, and the first rufous hummingbirds arrive for it.",
        "Indian plum flowers hang in little white tassels.",
        "Stinging nettle shoots come up, and young tops make great soup if you wear gloves.",
        "Peach and plum buds swell and show color at the tips.",
        "Garlic and rhubarb noses poke through the mulch."],
    3: ["Plums, cherries and pears start to bloom. Watch who visits on warm afternoons.",
        "Blue orchard mason bees come out once days pass about 55°F.",
        "Western tent caterpillar egg masses are shiny bands on twigs. Pinch them off before bud break.",
        "Aphids gather on new tips, and ladybugs and hoverfly larvae show up a week or two later.",
        "Currants and gooseberries leaf out early, with small dangling flowers."],
    4: ["Apples and blueberries bloom. Count bee species on a sunny afternoon.",
        "Comfrey flowers draw bumblebees all day.",
        "Serviceberry blooms in a white cloud.",
        "Look for ladybug larvae (tiny black-and-orange alligators) on aphid colonies, and leave them be.",
        "Tree swallows return and hunt over open ground."],
    5: ["Fruit sets. Look for tiny swelling fruits behind the dropped petals.",
        "Elderberry opens its flat white flower heads late in the month.",
        "Honeyberries (haskap) ripen first, the earliest fruit of the year.",
        "Strawberries ripen, and so do the slugs and robins who want them.",
        "Cedar waxwings travel in flocks looking for early fruit."],
    6: ["\"June drop\": apples and pears shed extra fruitlets. It's normal self-thinning.",
        "Cherries, goumi and honeyberries ripen.",
        "Summer raspberries start late in the month.",
        "Red currants and gooseberries color up.",
        "Mulberries stain everything, including the birds."],
    7: ["Blueberries and raspberries peak, with blackberries close behind.",
        "Watch soft fruit for spotted wing drosophila: tiny larvae in ripe berries. Pick often and pick clean.",
        "Hazelnut husks fatten up.",
        "Dig a finger into the mulch. It should still be damp an inch down.",
        "Fig brebas (the early crop) ripen on last year's wood."],
    8: ["Plums, peaches and early apples ripen.",
        "Yellowjackets find fallen fruit. Pick up drops or let the chickens have them.",
        "Elderberries turn deep purple.",
        "Seaberry branches glow orange.",
        "The main fig crop starts to soften."],
    9: ["Hazelnuts drop. Jays and squirrels will race you for them.",
        "Apples, pears and grapes come in. Taste-test before picking: seeds turn brown when ripe.",
        "Cross orbweaver spider webs are everywhere at dawn, beaded with dew.",
        "Pawpaws ripen. Ripe ones give a little and smell like banana custard.",
        "Fall-bearing raspberries are cropping."],
    10: ["Medlars, quince, persimmons and late apples hang on as the leaves turn.",
         "Mushrooms pop up in wood-chip paths after the first soaking rains, a sign the soil fungi are busy.",
         "Nitrogen fixers like goumi and seaberry hold their leaves longer than the fruit trees.",
         "Varied thrushes come down from the mountains with their eerie one-note song.",
         "Hardy kiwi ripens. Let them soften on the counter."],
    11: ["Leaves drop. Look for scab spots on apple leaves to see which trees need extra cleanup.",
         "Medlars blet (go soft and brown), which is when they're good to eat.",
         "Persimmons glow on bare branches after leaf fall.",
         "Next year's hazelnut catkins are already formed, tight and green.",
         "Kale and collards sweeten after frost."],
    12: ["Bushtits, chickadees and kinglets glean insect eggs off the bare branches, free pest control.",
         "Moss and lichen thrive on trunks. They're harmless.",
         "Look for mummified fruit still hanging and pull it, since it carries brown rot spores.",
         "Rose hips and leftover crabapples feed the robins.",
         "Hazelnut catkins start to loosen on mild days."],
}

PRAIRIE = {
    1: ["Bald eagles perch along the sloughs. Sauvie Island is one of the best eagle spots near Portland in winter.",
        "Bunchgrass crowns stay green at the base. Count the tufts to see how the stand is filling in.",
        "Soft soil makes this the easiest time to pull blackberry and Scotch broom seedlings.",
        "Northern harriers fly low and tilting over the grass hunting voles."],
    2: ["Camas leaves come up like thin green blades.",
        "Western meadowlarks start singing on mild mornings.",
        "Look for the first western buttercups in sunny spots.",
        "Tundra swans and sandhill cranes are still feeding in the island's fields."],
    3: ["Spring gold (a low yellow lomatium) and western buttercup brighten the grass.",
        "Shooting stars may nod pink in damper spots.",
        "Queen bumblebees zigzag low over the ground looking for nest sites in old vole holes.",
        "Camas buds form at the top of the stems."],
    4: ["Camas blooms: the prairie's big blue moment, usually mid-April into May.",
        "Sea blush paints patches pink.",
        "Blue-eyed grass opens on sunny days only.",
        "Listen for meadowlarks and savannah sparrows, which nest right in the grass."],
    5: ["Oregon sunshine and lupines bloom. Look for small blue butterflies on the lupine.",
        "Checker-mallow sends up pink spikes.",
        "Camas finishes and its seed pods fatten.",
        "Bumblebees are everywhere. Try counting how many kinds you see."],
    6: ["Grasses head out. Roemer's fescue and tufted hairgrass throw up seed heads.",
        "Farewell-to-spring opens pink cups as the prairie starts to dry.",
        "Yarrow and tarweed bloom, and tarweed smells sticky-sweet in the heat.",
        "Seed collecting starts: bag a few heads of anything that's turned papery."],
    7: ["The prairie goes gold. Summer dormancy is normal, so don't water it.",
        "Gumweed opens sticky yellow flowers.",
        "Grasshoppers jump ahead of you and crickets take over at night.",
        "Collect seed from camas, lupine and checker-mallow when the pods rattle."],
    8: ["Goldenrod and gumweed carry the pollinators through late summer.",
        "Goldfinches pick seed heads clean.",
        "Douglas aster starts its purple bloom.",
        "Watch fire danger. Dry grass plus wind is the island's main fire risk."],
    9: ["Douglas aster is a late-season lifeline for bees.",
        "First fall rains green up the bunchgrasses from the base, the prairie's \"second spring\".",
        "Sandhill cranes come through. Listen for their rattling calls overhead.",
        "This is a good window to mow or rake thatch once seed has dropped."],
    10: ["Sow native wildflower seed with the fall rains. Many need a cold, wet winter to sprout.",
         "Bunchgrasses green up fast now. It's easy to spot gaps to overseed.",
         "Northern harriers return to hunt the fields.",
         "Sandhill cranes gather on the island, some staying all winter."],
    11: ["Tundra swans arrive. Sauvie Island hosts thousands, and you'll hear them before you see them.",
         "Camas bulbs are quietly growing roots underground.",
         "Look for Scotch broom and blackberry creeping in from the edges, and dig them while the soil is soft.",
         "American kestrels hover over the grass hunting."],
    12: ["Swans, geese and cranes fill the island's fields, and bald eagles watch over them.",
         "The wildflower seed you sowed is sitting through the cold, which it needs to germinate.",
         "Harriers and red-tailed hawks hunt the vole runs in the grass.",
         "Frost highlights spider webs and seed heads at dawn, so it's worth a walk."],
}


def _weather_notes(day, forecast, recent_rain):
    """A couple of notes set off by this week's weather."""
    notes = []
    days = forecast or []
    nxt = days[:3]
    frost = next((d for d in nxt if d.get("lo") is not None and d["lo"] <= 32), None)
    m = day.month
    if frost:
        when = "tonight" if frost is days[0] else dt.date.fromisoformat(frost["date"]).strftime("%A night")
        notes.append(f"Frost likely {when} ({frost['lo']}°). Persimmons and medlars sweeten after it, and the prairie's seed heads will sparkle at dawn."
                     if m >= 10 or m <= 3 else f"Frost possible {when} ({frost['lo']}°). Watch blossoms and tender new growth.")
    if recent_rain >= 0.5 and m in (9, 10, 11, 12):
        notes.append(f"{recent_rain:.1f} in of rain in the last few days. Check the wood-chip paths and the prairie edges for mushrooms.")
    today = days[0] if days else {}
    if 2 <= m <= 4 and (today.get("hi") or 0) >= 58 and (today.get("rain_pct") or 0) < 40:
        notes.append(f"A warm, dry {today.get('hi')}° day: mason bees and queen bumblebees will be out. Watch the blossoms in the afternoon.")
    if (today.get("hi") or 0) >= 90:
        notes.append("A hot one. The prairie is fine dormant, but check the mulch under young fruit trees.")
    if max((d.get("gust") or 0) for d in nxt) >= 40 if nxt else False:
        notes.append("Strong gusts ahead. Check stakes and tree ties, and look for broken limbs afterward.")
    return notes


def look_for(day, forecast=None, recent_rain=0.0, n=3):
    """Today's few things to look for in each place, rotating through the month."""
    def rotate(items, salt):
        start = (day.toordinal() * n + salt) % len(items)
        return [items[(start + i) % len(items)] for i in range(min(n, len(items)))]
    notes = _weather_notes(day, forecast, recent_rain)
    said = " ".join(notes).lower()
    fresh = lambda items: [t for t in items if not any(w in said and w in t.lower() for w in ("mushroom", "frost", "medlar"))]
    return {"month": day.strftime("%B"), "forest": rotate(fresh(FOREST[day.month]), 0),
            "prairie": rotate(fresh(PRAIRIE[day.month]), 1), "weather": notes}
