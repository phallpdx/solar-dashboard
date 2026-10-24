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
