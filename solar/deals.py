"""This week's sale items at nearby grocery stores, from their weekly ads on Flipp."""
import json
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}
BASE = "https://backflipp.wishabi.com/flipp"
STORES = {"fred meyer": "Fred Meyer", "new seasons": "New Seasons", "grocery outlet": "Grocery Outlet"}
PER_STORE = 60


def _get(path, **params):
    url = f"{BASE}/{path}?" + urllib.parse.urlencode({"locale": "en-us", **params})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _num(x):
    try:
        return float(str(x).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def _flyers(postal_code):
    for path in ("data", "flyers"):
        try:
            data = _get(path, postal_code=postal_code)
        except Exception:
            continue
        flyers = data.get("flyers") if isinstance(data, dict) else data
        if flyers:
            return flyers
    raise RuntimeError("Flipp didn't return any weekly ads")


def weekly(postal_code):
    """Sale items from each store's current weekly ad, biggest discounts first."""
    found, notes = {}, []
    flyers = _flyers(postal_code)
    merchants = sorted({f.get("merchant") or f.get("merchant_name") or "?" for f in flyers})
    for f in flyers:
        merchant = (f.get("merchant") or f.get("merchant_name") or "").lower()
        store = next((name for key, name in STORES.items() if key in merchant), None)
        if not store or store in found:
            continue
        try:
            data = _get(f"flyers/{f['id']}")
        except Exception as e:
            notes.append(f"{store}: {e}")
            continue
        time.sleep(0.5)
        items = []
        for it in (data.get("items") if isinstance(data, dict) else data) or []:
            name = (it.get("name") or "").strip()
            if not name or it.get("display_type") not in (None, 1):
                continue
            now = _num(it.get("current_price") or it.get("price"))
            was = _num(it.get("original_price"))
            pct = round((1 - now / was) * 100) if now and was and was > now else None
            price_text = " ".join(str(p) for p in (it.get("pre_price_text"), it.get("price_text") or it.get("price"),
                                                   it.get("post_price_text")) if p).strip()
            items.append({"name": name, "price": price_text or None, "was": was, "pct_off": pct,
                          "deal": (it.get("sale_story") or "").strip() or None,
                          "image": it.get("cutout_image_url") or it.get("clean_image_url"),
                          "until": (it.get("valid_to") or f.get("valid_to") or "")[:10] or None})
        items.sort(key=lambda x: (-(x["pct_off"] or 0), x["deal"] is None, x["name"]))
        found[store] = {"store": store, "until": (f.get("valid_to") or "")[:10] or None,
                        "items": items[:PER_STORE], "total": len(items)}
    missing = [s for s in STORES.values() if s not in found]
    if not found:
        raise RuntimeError("none of the stores have a weekly ad on Flipp; ads found: " + ", ".join(merchants[:40])
                           + (f" ({'; '.join(notes)})" if notes else ""))
    return {"stores": list(found.values()), "missing": missing, "notes": notes,
            "merchants": merchants if missing else None}

