"""Elections and representatives for home.

- Districts: US Census geocoder (from HOME_ADDRESS, or the rounded home spot), keyless
- Members of Congress: the unitedstates/congress-legislators data, keyless
- Their recent floor votes: House Clerk and Senate roll call XML, keyless
- Bills they sponsored: Congress.gov API (needs a free CONGRESS_KEY from api.data.gov)
- Oregon legislators and their bills: Open States (needs a free OPENSTATES_KEY)
- In the news: Google News RSS, keyless
- Elections and what's on the ballot: Google Civic Information API (GOOGLE_CIVIC_KEY), with Oregon's
  regular election dates kept here as a fallback
"""
import datetime as dt
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}
CENSUS = "https://geocoding.geo.census.gov/geocoder/geographies/"
LEGISLATORS = "https://unitedstates.github.io/congress-legislators/legislators-current.json"

# Oregon's regular election dates (ORS 254.056 and 255.335): general elections the first Tuesday after
# the first Monday in November of even years, primaries the third Tuesday in May of even years, and
# special district elections the third Tuesday in May of odd years. Registration closes 21 days before.
OREGON_STATEWIDE = [
    ("Governor", "Tina Kotek", "Democratic", "https://www.oregon.gov/gov/"),
    ("Secretary of State", "Tobias Read", "Democratic", "https://sos.oregon.gov/"),
    ("Attorney General", "Dan Rayfield", "Democratic", "https://www.doj.state.or.us/"),
    ("State Treasurer", "Elizabeth Steiner", "Democratic", "https://www.oregon.gov/treasury/"),
]
VOTE_LINKS = [("Check your registration and ballot", "https://sos.oregon.gov/voting/Pages/myvote.aspx"),
              ("Ballot drop sites", "https://sos.oregon.gov/voting/Pages/drop-box-locator.aspx")]


def _open(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def _json(url):
    with _open(url) as r:
        return json.load(r)


def _xml(url):
    with _open(url) as r:
        return ET.fromstring(r.read())


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    return d + dt.timedelta(days=(weekday - d.weekday()) % 7 + 7 * (n - 1))


def oregon_elections(today, years=3):
    out = []
    for y in range(today.year, today.year + years):
        if y % 2 == 0:
            out.append((_nth_weekday(y, 5, 1, 3), "Oregon primary election"))
            out.append((_nth_weekday(y, 11, 0, 1) + dt.timedelta(days=1), "General election"))
        else:
            out.append((_nth_weekday(y, 5, 1, 3), "Special district election (school boards, local measures)"))
    return [{"date": d.isoformat(), "name": n, "register_by": (d - dt.timedelta(days=21)).isoformat(),
             "ballots_mailed": (d - dt.timedelta(days=18)).isoformat()} for d, n in sorted(out) if d >= today]


# ---------------------------------------------------------------- districts and people

def _layer(geos, *words):
    for name, rows in geos.items():
        if rows and all(w.lower() in name.lower() for w in words):
            return rows[0]
    return None


def districts(address=None, lat=None, lon=None):
    """Congressional and state legislative districts, plus county, for home."""
    params = {"benchmark": "Public_AR_Current", "vintage": "Current_Current", "layers": "all", "format": "json"}
    if address:
        data = _json(CENSUS + "onelineaddress?" + urllib.parse.urlencode({**params, "address": address}))
        matches = data["result"].get("addressMatches") or []
        if not matches:
            raise RuntimeError("Census geocoder couldn't match the home address")
        geos = matches[0]["geographies"]
    else:
        data = _json(CENSUS + "coordinates?" + urllib.parse.urlencode({**params, "x": lon, "y": lat}))
        geos = data["result"]["geographies"]
    cd = _layer(geos, "Congressional Districts")
    upper, lower = _layer(geos, "Legislative Districts", "Upper"), _layer(geos, "Legislative Districts", "Lower")
    county = _layer(geos, "Counties")
    num = lambda row: int(re.sub(r"\D", "", row.get("BASENAME") or row.get("NAME") or "") or 0) if row else None
    return {"state": "OR", "congress": num(cd), "senate": num(upper), "house": num(lower),
            "county": county.get("NAME") if county else None}


def congress_members(state, district):
    people = []
    for p in _json(LEGISLATORS):
        t = p["terms"][-1]
        if t["state"] != state or (t["type"] == "rep" and t.get("district") != district):
            continue
        people.append({
            "name": p["name"].get("official_full") or f"{p['name']['first']} {p['name']['last']}",
            "role": "U.S. Senator" if t["type"] == "sen" else f"U.S. Representative, District {district}",
            "chamber": "senate" if t["type"] == "sen" else "house",
            "party": t.get("party"), "url": t.get("url"), "phone": t.get("phone"),
            "contact": t.get("contact_form") or t.get("url"), "term_ends": t.get("end"),
            "bioguide": p["id"]["bioguide"], "lis": p["id"].get("lis"),
        })
    return sorted(people, key=lambda x: x["chamber"] != "senate")


def state_legislators(lat, lon, key):
    data = _json("https://v3.openstates.org/people.geo?" + urllib.parse.urlencode({"lat": lat, "lng": lon, "apikey": key}))
    out = []
    for p in data.get("results") or []:
        role = p.get("current_role") or {}
        if role.get("org_classification") not in ("upper", "lower"):
            continue
        out.append({"name": p["name"], "party": p.get("party"),
                    "role": f"State {'Senator' if role['org_classification'] == 'upper' else 'Representative'}, District {role.get('district')}",
                    "chamber": "state-" + role["org_classification"], "url": p.get("openstates_url"),
                    "email": p.get("email"), "openstates_id": p["id"]})
    return sorted(out, key=lambda x: x["chamber"] != "state-upper")


def state_bills(person_id, key, n=4):
    data = _json("https://v3.openstates.org/bills?" + urllib.parse.urlencode(
        {"jurisdiction": "Oregon", "sponsor": person_id, "sort": "updated_desc", "per_page": n, "apikey": key}))
    return [{"id": b["identifier"], "title": b["title"], "action": b.get("latest_action_description"),
             "date": (b.get("latest_action_date") or "")[:10], "url": b.get("openstates_url")}
            for b in data.get("results") or []]


def sponsored(bioguide, key, n=4):
    data = _json(f"https://api.congress.gov/v3/member/{bioguide}/sponsored-legislation?" + urllib.parse.urlencode(
        {"api_key": key, "limit": n, "format": "json"}))
    out = []
    for b in data.get("sponsoredLegislation") or []:
        if not b.get("number"):  # amendments have no bill number
            continue
        kind = (b.get("type") or "").lower()
        act = b.get("latestAction") or {}
        out.append({"id": f"{b.get('type')} {b['number']}", "title": b.get("title"), "date": act.get("actionDate"),
                    "action": act.get("text"),
                    "url": f"https://www.congress.gov/bill/{b['congress']}th-congress/{'house' if kind.startswith('h') else 'senate'}-bill/{b['number']}"
                    if kind in ("hr", "s") else None})
    return out


def news(name, n=3):
    q = urllib.parse.quote(f'"{name}" Oregon')
    with _open(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en") as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.iter("item"):
        title = item.findtext("title") or ""
        src = item.findtext("source")
        if src and title.endswith(" - " + src):
            title = title[: -len(src) - 3]
        out.append({"title": title, "url": item.findtext("link"), "source": src,
                    "date": dt.datetime.strptime(item.findtext("pubDate"), "%a, %d %b %Y %H:%M:%S %Z").date().isoformat()
                    if item.findtext("pubDate") else None})
        if len(out) >= n:
            break
    return out


# ---------------------------------------------------------------- floor votes

def _iso(text, *formats):
    text = re.sub(r"\s+", " ", (text or "").strip())
    for f in formats:
        try:
            return dt.datetime.strptime(text, f).date().isoformat()
        except ValueError:
            pass
    return text or None


def _congress_session(today):
    return (today.year - 1789) // 2 + 1, 1 if today.year % 2 else 2


def _exists(url):
    """The Clerk answers some missing roll calls with a 200 page, so look for a real vote in the body."""
    try:
        with _open(url, timeout=20) as r:
            return b"<rollcall-vote" in r.read(2000)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def _latest_house_roll(year, hint):
    """Highest roll call number for the year: walk up from the last one seen, or search from scratch."""
    url = lambda n: f"https://clerk.house.gov/evs/{year}/roll{n:03d}.xml"
    lo = hint or 0
    if lo and not _exists(url(lo)):  # a bad hint from an earlier run
        lo = 0
    if not lo:
        hi = 1
        while hi < 4096 and _exists(url(hi)):
            lo, hi = hi, hi * 2
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if _exists(url(mid)) else (lo, mid)
    while _exists(url(lo + 1)):
        lo += 1
    return lo


def house_votes(today, bioguide, cache, n=6):
    """The rep's position on the latest House roll calls. cache keeps parsed votes between runs."""
    last = _latest_house_roll(today.year, cache.get("house_last") if cache.get("house_year") == today.year else 0)
    cache.update(house_year=today.year, house_last=last)
    seen = cache.setdefault("house", {})
    out = []
    for num in range(last, max(0, last - 12), -1):
        key = f"{today.year}-{num}"
        if key not in seen:
            root = _xml(f"https://clerk.house.gov/evs/{today.year}/roll{num:03d}.xml")
            meta = root.find("vote-metadata")
            if meta is None:
                continue
            seen[key] = {"num": num, "date": _iso(meta.findtext("action-date"), "%d-%b-%Y"), "bill": (meta.findtext("legis-num") or "").strip(),
                         "question": meta.findtext("vote-question"), "result": meta.findtext("vote-result"),
                         "desc": (meta.findtext("vote-desc") or "").strip(),
                         "url": f"https://clerk.house.gov/evs/{today.year}/roll{num:03d}.xml",
                         "positions": {r.find("legislator").get("name-id"): r.findtext("vote")
                                       for r in root.iter("recorded-vote")}}
        v = seen[key]
        if bioguide in v["positions"]:
            out.append({k: v[k] for k in ("date", "bill", "question", "result", "desc", "url")} | {"vote": v["positions"][bioguide]})
        if len(out) >= n:
            break
    for k in sorted(seen, key=lambda k: int(k.split("-")[1]))[:-30]:
        seen.pop(k)
    return out


def senate_votes(today, lis_ids, cache, n=6):
    """Each senator's position on the latest Senate roll calls, keyed by LIS id."""
    congress, session = _congress_session(today)
    menu = _xml(f"https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_{congress}_{session}.xml")
    seen = cache.setdefault("senate", {})
    rows = []
    for v in list(menu.iter("vote"))[:10]:
        num = v.findtext("vote_number")
        key = f"{congress}-{session}-{num}"
        if key not in seen:
            root = _xml(f"https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{num}.xml")
            seen[key] = {"num": int(num), "date": _iso((root.findtext("vote_date") or "").split(",")[0] + "," + ((root.findtext("vote_date") or "").split(",") + [""])[1], "%B %d, %Y"), "bill": v.findtext("issue"),
                         "question": root.findtext("question") or v.findtext("question"), "result": v.findtext("result"),
                         "desc": (v.findtext("title") or "").strip(),
                         "url": f"https://www.senate.gov/legislative/LIS/roll_call_votes/vote{congress}{session}/vote_{congress}_{session}_{num}.htm",
                         "positions": {m.findtext("lis_member_id"): m.findtext("vote_cast") for m in root.iter("member")}}
        rows.append(seen[key])
    for k in sorted(seen, key=lambda k: int(k.split("-")[-1]))[:-30]:
        seen.pop(k)
    return {lis: [{k: v[k] for k in ("date", "bill", "question", "result", "desc", "url")} | {"vote": v["positions"][lis]}
                  for v in rows if lis in v["positions"]][:n] for lis in lis_ids}


# ---------------------------------------------------------------- elections and ballot

def civic_elections(address, key, today):
    """Upcoming elections Google knows about for this address, with the contests on the ballot."""
    data = _json("https://www.googleapis.com/civicinfo/v2/elections?" + urllib.parse.urlencode({"key": key}))
    out = []
    for e in data.get("elections") or []:
        if e["id"] == "2000" or e.get("electionDay", "") < today.isoformat():  # 2000 is Google's test election
            continue
        try:
            info = _json("https://www.googleapis.com/civicinfo/v2/voterinfo?" + urllib.parse.urlencode(
                {"key": key, "address": address, "electionId": e["id"], "officialOnly": "false"}))
        except urllib.error.HTTPError:
            continue  # not an election for this address
        contests = []
        for c in info.get("contests") or []:
            if c.get("type") == "Referendum" or c.get("referendumTitle"):
                contests.append({"kind": "measure", "title": c.get("referendumTitle"), "subtitle": c.get("referendumSubtitle"),
                                 "url": c.get("referendumUrl")})
            else:
                contests.append({"kind": "race", "title": c.get("office"),
                                 "candidates": [{"name": x.get("name"), "party": x.get("party")} for x in c.get("candidates") or []][:6]})
        admin = ((info.get("state") or [{}])[0].get("electionAdministrationBody") or {})
        out.append({"date": e["electionDay"], "name": e["name"], "contests": contests[:30],
                    "info_url": admin.get("electionInfoUrl"), "ballot_url": admin.get("ballotInfoUrl")})
    return out
