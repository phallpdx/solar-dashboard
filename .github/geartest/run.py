import json, urllib.request, urllib.parse
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/hal+json", "Accept-Version": "3.0"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}
d = get("https://api.reverb.com/api/listings/all?query=gibson+les+paul+junior&per_page=2&show_only_sold=true")
json.dump(d, open("out/sold.json", "w"), indent=1)
json.dump(get("https://api.reverb.com/api/csps?query=gibson+les+paul+junior&per_page=5"), open("out/csps.json", "w"), indent=1)
json.dump(get("https://api.reverb.com/api/listings/all?query=gibson+les+paul+junior&per_page=2"), open("out/live.json", "w"), indent=1)
json.dump(get("https://api.reverb.com/api/listings/all?query=gibson+les+paul+junior&per_page=2&show_only_sold=true&year_min=2015"), open("out/yearmin.json", "w"), indent=1)
json.dump(get("https://api.reverb.com/api/listings/all?query=gibson+les+paul+junior&per_page=2&show_only_sold=true&sort=sold_at|desc"), open("out/soldsort.json", "w"), indent=1)
