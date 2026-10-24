"""What to plant outside soon around Portland.

Every window comes from OSU Extension's "Growing Your Own" (EM 9027) planting-date table, Region 2
(western valleys, Portland to Roseburg), with its row and plant spacing.
"""
import datetime as dt

SOURCE = {"name": "OSU Extension: Growing Your Own (EM 9027)",
          "url": "https://extension.oregonstate.edu/catalog/em-9027-growing-your-own"}

# (start month, day), (end month, day), name, how, kind. A window may wrap past New Year.
PLANTING = [
    ((9, 1), (2, 28), "Garlic", "Rows 18 in apart, cloves 3 in apart", "Vegetable"),
    ((9, 1), (10, 1), "Crimson clover", "Winter cover crop: ½ lb of seed per 1,000 sq ft, no later than Oct 1; water it in", "Cover crop"),
    ((4, 1), (4, 15), "Fava beans or Austrian winter peas", "Spring cover crop: ½ lb of seed per 1,000 sq ft in early April", "Cover crop"),
    ((2, 1), (3, 31), "Asparagus", "One-year crowns, rows 60 in apart, 12 in apart in the row", "Vegetable"),
    ((2, 1), (5, 31), "Peas", "Rows 36 in (bush) or 48 in (vine) apart, seeds 2 in apart", "Vegetable"),
    ((3, 1), (6, 30), "Beets", "Rows 12 in apart, 1 to 2 in apart in the row", "Vegetable"),
    ((3, 1), (7, 15), "Carrots", "Rows 12 in apart, 2 in apart in the row", "Vegetable"),
    ((3, 1), (8, 31), "Broccoli", "Transplants (6 weeks to grow); 12 to 24 in apart", "Vegetable"),
    ((3, 1), (5, 31), "Leeks", "Rows 24 in apart, 2 in apart in the row", "Vegetable"),
    ((3, 1), (5, 31), "Onions", "Rows 12 in apart, 3 in apart; transplants take 10 weeks to grow", "Vegetable"),
    ((3, 1), (9, 30), "Radishes", "Rows 12 in apart, 1 in apart in the row", "Vegetable"),
    ((3, 1), (4, 30), "Rhubarb", "Crown pieces, 36 in apart in rows 48 in apart", "Vegetable"),
    ((4, 1), (6, 30), "Cabbage", "Transplants (6 weeks to grow); 24 in apart", "Vegetable"),
    ((4, 1), (7, 31), "Chard", "Rows 24 in apart, 12 in apart in the row", "Vegetable"),
    ((4, 1), (6, 30), "Sweet corn", "At least 4 rows, 36 in apart, 15 in between plants", "Vegetable"),
    ((4, 1), (8, 31), "Leaf lettuce", "Rows 12 in apart, 6 in apart in the row", "Vegetable"),
    ((4, 1), (6, 30), "Potatoes", "Rows 30 in apart, 12 in apart in the row", "Vegetable"),
    ((4, 1), (4, 30), "Spinach", "Rows 12 in apart, 3 in apart in the row", "Vegetable"),
    ((9, 1), (9, 30), "Spinach", "Rows 12 in apart, 3 in apart in the row", "Vegetable"),
    ((4, 1), (9, 30), "Turnips", "Rows 24 in apart, 2 in apart in the row", "Vegetable"),
    ((5, 1), (7, 31), "Snap beans", "Rows 12 to 24 in apart; bush 2 to 6 in apart, pole 12 to 24 in", "Vegetable"),
    ((5, 1), (6, 30), "Cucumbers", "Transplants (4 weeks to grow); 24 in apart in rows 48 in apart", "Vegetable"),
    ((5, 1), (7, 31), "Kale", "Rows 24 in apart, 24 in apart in the row", "Vegetable"),
    ((5, 1), (6, 30), "Peppers", "Transplants (10 weeks to grow); 12 to 18 in apart", "Vegetable"),
    ((5, 1), (6, 30), "Summer squash", "Transplants (4 weeks to grow); 24 in apart in rows 48 in apart", "Vegetable"),
    ((5, 1), (5, 31), "Winter squash", "Transplants (4 weeks to grow); 48 in apart in rows 72 in apart", "Vegetable"),
    ((5, 1), (5, 31), "Tomatoes", "Transplants (8 weeks to grow); 24 to 36 in apart", "Vegetable"),
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
        out.append("Lots of rain in the next few days. Wait for the soil to drain before you dig; working wet soil compacts it.")
    dry = [d for d in days[:5] if (d.get("rain_pct") or 0) < 30]
    if len(dry) >= 2 and not wet >= 1:
        first = dt.date.fromisoformat(dry[0]["date"])
        out.append(f"Good planting weather from {first:%a}: a few dry days.")
    if soil_f is not None:
        out.append(f"Soil is about {soil_f}°F at 2 inches.")
    return out


# Food forest care by month for wet-winter western Oregon, using permaculture methods only (chop and drop,
# sheet mulch, living mulch, habitat, guilds; no sprays). Every task links the page that backs it up.
WALDEN = ("Walden Effect: chop 'n drop", "https://www.waldeneffect.org/blog/Chop___39__n_drop")
COMFREY = ("Walden Effect: comfrey for mulch", "https://waldeneffect.org/blog/Comfrey_for_compost_and_mulch")
VOLES = ("Penn State Extension: voles", "https://extension.psu.edu/orchard-wildlife-integrated-management-of-voles-in-orchards")
CANKER = ("OSU: bacterial canker", "https://solvepestproblems.oregonstate.edu/plant-problems/bacterial-canker-and-blast")
RASPBERRY = ("OSU: growing raspberries", "https://extension.oregonstate.edu/sites/extd8/files/documents/12281/growingraspberries.pdf")
# (months, task, why, sources)
FOREST = [
    ((10, 11), "Chop and drop spent perennials around the trees",
     "Cut them and let them lie as mulch. Keep it a few inches off the trunks so voles can't hide against the bark.", [WALDEN, VOLES]),
    ((10, 11, 12, 1, 2), "Leave hollow and pithy stems standing",
     "Small carpenter bees and mason bees nest in old raspberry, elderberry and rose stems.",
     [("Xerces Society: stem-nesting bees", "https://www.xerces.org/blog/how-to-safely-relocate-stem-nesting-bees")]),
    ((10, 11), "Mow-shred fallen apple and pear leaves where they lie",
     "Scab spends the winter on fallen leaves; shredding them speeds up their breakdown.",
     [("OSU: apple scab", "https://extension.oregonstate.edu/news/how-manage-apple-scab-during-oregons-wet-spring-months")]),
    ((10, 11), "Sheet mulch new beds with cardboard, then leaves, compost or wood chips",
     "Fall is ideal: it breaks down over winter and is ready to plant into by spring.",
     [("OSU: sheet mulching", "https://extension.oregonstate.edu/gardening/techniques/sheet-mulch-lasagna-composting")]),
    ((10, 11), "Put hardware cloth guards around young trunks",
     "Voles girdle trees in winter. Set the cloth 4 to 6 inches into the ground and 18 to 24 inches high.", [VOLES]),
    ((10, 11), "Take hardwood cuttings of currants, gooseberries and elderberry",
     "They root from dormant stems: free plants for the next guild.",
     [("Iowa State: hardwood cuttings", "https://yardandgarden.extension.iastate.edu/faq/which-plants-can-be-propagated-hardwood-stem-cuttings"),
      ("OSU: fall cuttings", "https://extension.oregonstate.edu/es/node/134791/printable/print")]),
    ((10, 11, 12, 1, 2), "Thin summer raspberries to 4 or 5 canes per foot",
     "Do it while they're dormant, and cut out any canes that already fruited.", [RASPBERRY]),
    ((10, 11, 12), "Don't prune cherries, plums or peaches",
     "Cuts made in wet weather let bacterial canker in. Summer pruning is best.", [CANKER]),
    ((11, 12), "Put a rain shelter over peach trees after the leaves drop",
     "Keeping the buds dry until mid-May prevents peach leaf curl, no spray needed.",
     [("RHS: peach leaf curl", "https://www.rhs.org.uk/disease/peach-leaf-curl")]),
    ((11,), "Spread 3 to 4 inches of leaves over bare soil",
     "Suppresses winter weeds and feeds the soil.",
     [("OSU: November garden calendar", "https://extension.oregonstate.edu/catalog/em-9615-november-garden-calendar")]),
    ((1, 2, 3), "Prune apples and pears in late winter",
     "Pruning while they're dormant, after the worst cold, cuts the risk of frost damage. Healthy prunings can go into a hugelkultur mound; leave out diseased wood.",
     [("OSU: prune apples in late winter", "https://extension.oregonstate.edu/es/news/prune-apple-trees-late-winter-stronger-growth-better-fruit"),
      ("Clemson: hugelkultur", "https://hgic.clemson.edu/hugelkultur-gardening/")]),
    ((1, 2), "If stone fruit needs a cut, wait for a dry week",
     "OSU says to hold dormant pruning until January or February, when no rain is expected for at least a week.", [CANKER]),
    ((1, 2), "Cut fall-bearing raspberries to the ground",
     "For one fall crop, cut every cane down while the plants are dormant.", [RASPBERRY]),
    ((2, 3), "Plant bare-root trees with a nitrogen fixer like goumi in the guild",
     "Early spring is the ideal time for bare-root trees; plant them while dormant. Goumi fixes nitrogen with root bacteria.",
     [("OSU: when to plant fruit trees", "https://extension.oregonstate.edu/ask-extension/featured/should-i-plant-fruit-trees-fall-or-spring"),
      ("Philadelphia Orchard Project: goumi", "https://www.phillyorchards.org/2021/06/07/spotlight-on-goumi-berry-nitrogen-fixer-extraordinaire/")]),
    ((4, 5), "Sow small-flowered plants like dill and phacelia in the guilds",
     "They feed the beneficial insects that hunt pests.",
     [("NMSU: insectary plants", "https://pubs.nmsu.edu/_h/H169/")]),
    ((5, 6), "Thin apples and pears to one fruit per spur",
     "Do it early, before the fruit is dime-sized (usually within 20 days of petal fall), for bigger fruit and fewer broken limbs.",
     [("OSU: fruit thinning", "https://extension.oregonstate.edu/gardening/berries-fruit/fruit-thinning")]),
    ((5, 6, 7, 8, 9), "Chop and drop comfrey every few weeks",
     "Lay the leaves around the tree. Grow the comfrey out past the tree's spread so it doesn't compete with it.", [COMFREY]),
    ((6, 7, 8), "Prune cherries, plums and peaches in dry summer weather",
     "Summer is the safe window for stone fruit.", [CANKER]),
    ((7, 8), "Cut out raspberry canes that just fruited", "Right after the last harvest.", [RASPBERRY]),
    ((9,), "Sow crimson clover on bare ground by October 1",
     "A winter cover crop that fixes nitrogen. Water it in so it's growing before the cold.",
     [("OSU: Growing Your Own", "https://extension.oregonstate.edu/catalog/em-9027-growing-your-own")]),
]


def forest_tasks(today):
    month = today.month
    nxt = month % 12 + 1
    item = lambda t, w, s: {"task": t, "why": w, "sources": [{"name": n, "url": u} for n, u in s]}
    now = [item(t, w, s) for months, t, w, s in FOREST if month in months]
    coming = [item(t, w, s) for months, t, w, s in FOREST if nxt in months and month not in months]
    return {"month": today.strftime("%B"), "next_month": dt.date(2000, nxt, 1).strftime("%B"), "now": now, "next": coming}


BURN_LINE = "503-621-1242"  # Sauvie Island Fire District 30 burn information line
BURN_SOURCE = "https://patch.com/oregon/gresham/multnomah-county-fire-departments-districts-lift-burn-ban"


def burn_check(today, days, alerts, aqi):
    """Is today a sensible day to burn yard debris? Fire districts set the actual daily status, so this
    reads the conditions they look at and points to the burn line."""
    if not days:
        return None
    d = days[0]
    no, ok = [], []
    events = " ".join((a.get("event") or "") for a in alerts or []).lower()
    if (6, 15) <= (today.month, today.day) <= (9, 30):
        no.append("Summer fire season, when Multnomah County fire districts often ban burning")
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
            "verdict": "Poor day to burn" if no else "Conditions look OK to burn", "source": BURN_SOURCE}
