"""What to plant outside soon around Portland (USDA zone 8b; Sauvie Island runs a little colder and wetter).

Windows follow OSU Extension's Willamette Valley planting calendar, with average last frost
around mid-April and first frost around mid-November on the island.
"""
import datetime as dt

# (start month, day), (end month, day), name, how, kind. A window may wrap past New Year.
PLANTING = [
    ((10, 1), (11, 30), "Garlic", "Plant cloves 2 in deep, pointy end up; harvest next July", "Vegetable"),
    ((10, 1), (11, 30), "Shallots and multiplier onions", "Set bulbs just below the surface", "Vegetable"),
    ((10, 1), (11, 15), "Fava beans", "Sow 2 in deep; they overwinter and fix nitrogen", "Vegetable"),
    ((2, 15), (3, 31), "Fava beans", "Sow 2 in deep as soon as soil can be worked", "Vegetable"),
    ((9, 1), (10, 31), "Crimson clover and vetch", "Broadcast on empty beds, rake in lightly", "Cover crop"),
    ((9, 1), (11, 15), "Cereal (winter) rye", "Broadcast on empty beds; the hardiest late cover crop", "Cover crop"),
    ((10, 1), (12, 15), "Native wildflower seed", "Camas, lupine, Oregon sunshine, clarkia, poppy: scatter on bare soil; winter cold wakes them", "Native"),
    ((10, 1), (11, 30), "Spring bulbs", "Tulips, daffodils, crocus: 3 times as deep as the bulb is tall", "Bulb"),
    ((11, 1), (3, 15), "Native shrubs and trees", "Bare-root or potted: Oregon grape, red-flowering currant, Nootka rose, snowberry; winter rain does the watering", "Native"),
    ((9, 1), (10, 31), "Spinach, mâche and arugula", "Sow under a cloche or row cover for winter salads", "Vegetable"),
    ((9, 1), (10, 15), "Overwintering onions", "Plant starts now for an early summer harvest", "Vegetable"),
    ((1, 15), (3, 15), "Bare-root fruit trees and berries", "Plant while dormant; stake new trees", "Fruit"),
    ((2, 15), (4, 15), "Peas", "Sow 1 in deep along a trellis", "Vegetable"),
    ((2, 15), (4, 15), "Spinach", "Direct sow; it bolts once days get long", "Vegetable"),
    ((3, 1), (5, 15), "Lettuce, arugula and radishes", "Sow small batches every 2 weeks", "Vegetable"),
    ((3, 1), (4, 30), "Onion sets and leeks", "Plant sets 1 in deep, 4 in apart", "Vegetable"),
    ((3, 1), (4, 30), "Strawberries, asparagus and rhubarb", "Plant crowns while the soil is cool and moist", "Fruit"),
    ((3, 15), (5, 15), "Potatoes", "Plant seed potatoes 4 in deep once soil reaches 45°F", "Vegetable"),
    ((3, 15), (7, 15), "Carrots and beets", "Keep the seedbed moist until they sprout", "Vegetable"),
    ((3, 15), (4, 30), "Broccoli, cabbage and kale starts", "Transplant out; cover if a hard frost is coming", "Vegetable"),
    ((2, 15), (3, 31), "Tomatoes and peppers (indoors)", "Start seeds inside under lights, 6 to 8 weeks before planting out", "Start indoors"),
    ((5, 15), (6, 15), "Tomatoes and peppers", "Plant out once nights stay above 50°F", "Vegetable"),
    ((5, 15), (6, 30), "Beans, squash, cucumbers and corn", "Direct sow in warm soil (60°F or more)", "Vegetable"),
    ((6, 1), (6, 30), "Basil", "Needs warm nights; plant in full sun", "Herb"),
    ((7, 1), (8, 15), "Fall kale, chard, broccoli and cabbage", "Sow or transplant now for fall and winter harvests", "Vegetable"),
    ((8, 1), (9, 30), "Lettuce, radishes and turnips", "Fall sowings; shade seedlings in heat waves", "Vegetable"),
    ((8, 15), (9, 30), "Spinach", "Fall sowing for winter and early spring", "Vegetable"),
]


def _in_window(md, start, end):
    return start <= md <= end if start <= end else (md >= start or md <= end)


def plant_now(today, days_ahead=21):
    """Things whose planting window is open now or opens within the next few weeks."""
    out = []
    for start, end, name, how, kind in PLANTING:
        opens_in = None
        for i in range(days_ahead + 1):
            d = today + dt.timedelta(days=i)
            if _in_window((d.month, d.day), start, end):
                opens_in = i
                break
        if opens_in is None:
            continue
        # Days left in the window (walk forward from when it opens).
        left = 0
        d = today + dt.timedelta(days=opens_in)
        while _in_window((d.month, d.day), start, end) and left < 200:
            d += dt.timedelta(days=1)
            left += 1
        until = (d - dt.timedelta(days=1)).isoformat()
        out.append({"name": name, "how": how, "kind": kind, "opens_in": opens_in, "until": until,
                    "closing_soon": opens_in == 0 and left <= 14})
    out.sort(key=lambda x: (x["opens_in"] > 0, not x["closing_soon"], x["kind"] == "Start indoors", x["until"]))
    return out


def tips(days, soil_f):
    """Practical notes from the coming week's forecast."""
    out = []
    frost = [d for d in days[:7] if d.get("lo") is not None and d["lo"] <= 32]
    if frost:
        coldest = min(frost, key=lambda d: d["lo"])
        out.append(f"Frost coming (low of {coldest['lo']}° on {dt.date.fromisoformat(coldest['date']):%a}). "
                   "Cover tender greens and hold off on new transplants.")
    wet = sum(d.get("rain_in") or 0 for d in days[:3])
    if wet >= 1:
        out.append("Lots of rain in the next few days. Wait for the soil to drain before you dig or sow.")
    dry = [d for d in days[:5] if (d.get("rain_pct") or 0) < 30]
    if len(dry) >= 2 and not wet >= 1:
        first = dt.date.fromisoformat(dry[0]["date"])
        out.append(f"Good planting weather from {first:%a}: a few dry days.")
    if soil_f is not None:
        out.append(f"Soil is about {soil_f}°F at 2 inches." +
                   (" Too cold for most seeds to sprout fast; garlic, favas and cover crops don't mind." if soil_f < 50 else ""))
    return out


# Food forest care by month for wet-winter western Oregon (OSU Extension and WSU guidance).
# (months, task, why)
FOREST = [
    ((10, 11), "Pick up dropped and mummified fruit", "Removes overwintering brown rot and pests"),
    ((10, 11), "Rake or shred apple and pear leaves", "Cuts next year's scab; a 5% urea spray at leaf fall helps too"),
    ((10, 11), "Copper spray on apples and pears before heavy rains", "Prevents anthracnose cankers"),
    ((10, 11), "Cut spent summer raspberry canes to the ground", "Thin new canes to 4 to 6 per foot and tie them up"),
    ((10, 11), "Leave trailing blackberry canes on the ground", "Train them onto the trellis in late February"),
    ((10, 11), "Mulch 3 to 4 inches of wood chips, kept back from trunks", "Add vole guards around young trunks"),
    ((10, 11), "Plant potted perennials and garlic", "Use mounds in wet spots"),
    ((10, 11, 12, 1, 2), "Don't prune cherries, plums or peaches", "Wet-season cuts invite bacterial canker; wait for dry summer weather"),
    ((10, 11, 12, 1, 2, 3), "No nitrogen fertilizer", "It pushes soft growth that freezes; feed in spring"),
    ((11, 12), "Copper or lime sulfur on peaches and nectarines at leaf fall", "Prevents peach leaf curl"),
    ((1, 2, 3), "Prune apples, pears, blueberries, grapes and currants", "Do it while they're dormant"),
    ((1, 2), "Cut fall-bearing raspberries to the ground", "They fruit on new canes"),
    ((1, 2), "Repeat the leaf curl spray before buds swell", "Second and last peach and nectarine spray"),
    ((2, 3), "Horticultural oil at delayed-dormant", "Smothers overwintering aphid and scale eggs"),
    ((1, 2, 3), "Plant bare-root trees and shrubs", "Cheapest and easiest time to plant"),
    ((2,), "Train blackberry canes onto the trellis", "Late February, before buds break"),
    ((4, 5), "Fertilize as growth starts", "Compost or a balanced organic feed"),
    ((6, 7, 8), "Prune stone fruit in dry weather after harvest", "Safe window for cherries, plums and peaches"),
    ((6, 7, 8), "Remove raspberry canes that just fruited", "Right after harvest"),
    ((6, 7, 8), "Water deeply once a week in dry spells", "New plantings especially"),
    ((9,), "Copper spray on apples and pears before the rains", "First anthracnose protection of the season"),
    ((9,), "Harvest and store apples and pears", "Pick pears firm and ripen them indoors"),
]


def forest_tasks(today):
    month = today.month
    nxt = month % 12 + 1
    now = [{"task": t, "why": w} for months, t, w in FOREST if month in months]
    coming = [{"task": t, "why": w} for months, t, w in FOREST if nxt in months and month not in months]
    return {"month": today.strftime("%B"), "next_month": dt.date(2000, nxt, 1).strftime("%B"), "now": now, "next": coming}


BURN_LINE = "503-621-1242"  # Sauvie Island Fire District 30 burn information line


def burn_check(today, days, alerts, aqi):
    """Is today a sensible day to burn yard debris? Fire districts set the actual daily status, so this
    reads the conditions they look at and points to the burn line."""
    if not days:
        return None
    d = days[0]
    no, ok = [], []
    events = " ".join((a.get("event") or "") for a in alerts or []).lower()
    if (6, 15) <= (today.month, today.day) <= (9, 30):
        no.append("It's summer burn ban season in Multnomah County")
    if "red flag" in events:
        no.append("Red Flag Warning for fire weather")
    if "stagnation" in events or "air quality" in events:
        no.append("Air stagnation or air quality alert")
    if aqi is not None and aqi > 100:
        no.append(f"Air quality is poor (AQI {aqi})")
    if (d.get("gust") or 0) >= 20:
        no.append(f"Gusts up to {d['gust']} mph")
    if (d.get("rain_in") or 0) >= 0.3:
        ok.append("Wet day, so a pile won't spread, but damp debris smokes a lot")
    elif not no:
        ok.append(f"Light wind (gusts {d.get('gust') or 0} mph) and decent air")
    return {"good": not no, "reasons": no or ok, "phone": BURN_LINE,
            "verdict": "Poor day to burn" if no else "Conditions look OK to burn"}
