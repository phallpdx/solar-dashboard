import json, urllib.request, urllib.parse
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/hal+json", "Accept-Version": "3.0"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}
for s in ["published_at|desc", "price|desc", "created_at|desc"]:
    d = get("https://api.reverb.com/api/listings/all?" + urllib.parse.urlencode({"query": "gibson les paul junior", "per_page": 8, "show_only_sold": "true", "sort": s}))
    print(s, [(x["published_at"][:10], x["price"]["amount"], x["year"]) for x in d.get("listings", [])], d.get("error"))
for k in ("category", "product_type"):
    d = get("https://api.reverb.com/api/listings/all?" + urllib.parse.urlencode({"query": "gibson les paul junior", "per_page": 3, "show_only_sold": "true", k: "electric-guitars"}))
    print(k, d.get("total"), [c["full_name"] for x in d.get("listings", []) for c in x["categories"]])
x = d["listings"][0] if d.get("listings") else {}
print(sorted(x.keys()))
print(json.dumps(x.get("_links"))[:1500])
