"""Market snapshot: S&P 500 and friends from Yahoo Finance's public chart data."""
import datetime as dt
import json
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}
SYMBOLS = [
    ("^GSPC", "S&P 500", "index"),
    ("^DJI", "Dow", "index"),
    ("^IXIC", "Nasdaq", "index"),
    ("^TNX", "10-year Treasury", "yield"),
    ("CL=F", "Oil (WTI)", "usd"),
    ("GC=F", "Gold", "usd"),
    ("BTC-USD", "Bitcoin", "usd"),
]


def _chart(symbol, range_="1y"):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?"
           + urllib.parse.urlencode({"range": range_, "interval": "1d"}))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    points = [(t, c) for t, c in zip(result["timestamp"], closes) if c is not None]
    meta = result["meta"]
    return meta, points


def snapshot():
    out = []
    year = dt.date.today().year
    for symbol, name, kind in SYMBOLS:
        try:
            meta, points = _chart(symbol)
        except Exception:
            continue
        price = meta.get("regularMarketPrice") or points[-1][1]
        prev = meta.get("chartPreviousClose") if len(points) < 2 else points[-2][1]
        # If today's bar is already the last point, compare with the one before it.
        if points and abs(points[-1][1] - price) > 1e-9:
            prev = points[-1][1]
        jan1 = next((c for t, c in points if dt.datetime.utcfromtimestamp(t).year == year), None)
        out.append({
            "symbol": symbol, "name": name, "kind": kind,
            "price": round(price, 2),
            "day_pct": round((price / prev - 1) * 100, 2) if prev else None,
            "ytd_pct": round((price / jan1 - 1) * 100, 1) if jan1 else None,
            "spark": [round(c, 2) for _, c in points[-30:]] if symbol == "^GSPC" else None,
            "high_52w": round(max(c for _, c in points), 2) if points else None,
            "as_of": dt.datetime.utcfromtimestamp(meta.get("regularMarketTime") or points[-1][0])
                       .replace(tzinfo=dt.timezone.utc).isoformat(),
        })
        time.sleep(0.3)
    if not out:
        raise RuntimeError("no market data returned")
    return out
