import datetime
import json
import sys

sys.path.insert(0, ".")
from solar import gear  # noqa: E402

today = datetime.date(2026, 11, 4)
TITLES = ["2022 Gibson Les Paul Jr", "Gibson Custom Shop Historic 1957 Les Paul Goldtop", "Fender Thinline Telecaster",
          "Mesa Boogie Lonestar 2x12", "Fender Chris Shiflett Telecaster Deluxe Shoreline Gold",
          "Gretsch G2655T Streamliner with Bigsby", "Ibanez AD-80 Analog Delay", "Earthquaker x Death by Audio Time Shadows",
          "Boss DS-1 distortion", "1965 Fender Deluxe Reverb", "Fender 68 Custom Deluxe Reverb"]


def show(title, c):
    if c.get("unsure"):
        print(f"  UNSURE  {title}: {c['unsure']}")
        return
    print(f"  ${c['typical']:,} middle of {c['n']} sales [{c['category']}] for {title}  (q: {c['query']})")
    print(f"     last ${c['last']:,} {c['last_title']} ({c['last_date']}); avg ${c['avg']:,}; {c['recent']} sold/90d, {c['active']} live")
    for e in c["examples"]:
        print(f"     e.g. ${e['price']:,} {e['title']} ({e['date']})")


print("== fixed titles")
for t in TITLES:
    try:
        show(t, gear.comps(t, today))
    except Exception as e:  # noqa: BLE001
        print("  ERROR", t, e)
print("== live Craigslist scan")
found = gear.listings()
cache = {}
picks = gear.deals(found, cache, reverb_budget=40, today=today)
print(len(found), "listings,", len(cache), "looked up")
for k, v in cache.items():
    t = next((x["title"] for x in found if "v5 " + " ".join(gear._words(x["title"])) == k), k)
    p = next((x["price"] for x in found if x["title"] == t), None)
    print(f"- ${p} {t}")
    show(t, v["comp"])
print("== picks")
for d in picks:
    print(f"  ${d['price']} {d['title']}: usual ${d.get('typical')} ({d.get('pct_off')}% under) flip {d.get('flip_profit')}")
json.dump({"picks": picks, "unsure": gear.deals.unsure}, open("out/picks.json", "w"), indent=1)
