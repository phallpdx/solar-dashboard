"""Write a plain, e-ink friendly morning page (kindle.html) from dashboard.json.

The Kindle browser is old and slow, so the page is rendered here with no
JavaScript, no images and only basic CSS: big black text on white.

    python -m solar.kindle data/dashboard.json _site/kindle.html
"""

import datetime as dt
import html
import json
import sys
from zoneinfo import ZoneInfo


def esc(x):
    return html.escape(str(x))


def day_name(iso, today):
    d = dt.date.fromisoformat(iso[:10])
    if d == today:
        return "Today"
    if d == today + dt.timedelta(days=1):
        return "Tomorrow"
    return d.strftime("%A")


def clock(iso):
    t = dt.datetime.fromisoformat(iso)
    return t.strftime("%-I:%M %p").replace(":00 ", " ").lower()


def hour(hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    t = f"{h % 12 or 12}" + (f":{m:02d}" if m else "")
    return t + (" am" if h < 12 else " pm")


def section(title, rows):
    rows = [r for r in rows if r]
    if not rows:
        return ""
    return f"<h2>{esc(title)}</h2>\n" + "\n".join(rows)


def weather(d, today):
    w = d.get("weather") or {}
    rows = []
    if w.get("temp_f") is not None:
        bits = [f"<b class=big>{round(w['temp_f'])}°</b>"]
        if w.get("wind_mph") is not None:
            bits.append(f"wind {esc(w.get('wind_dir') or '')} {round(w['wind_mph'])} mph")
        if w.get("humidity") is not None:
            bits.append(f"{round(w['humidity'])}% humidity")
        rows.append("<p>" + " &nbsp; ".join(bits) + "</p>")
    ahead = (d.get("yard") or {}).get("ahead") or []
    if ahead:
        items = []
        for a in ahead[:3]:
            rain = a.get("rain_in")
            rain = f", rain {rain:.2f} in" if rain else ", dry"
            items.append(f"<li><b>{esc(day_name(a['date'], today))}</b>: "
                         f"high {round(a['hi'])}°, low {round(a['lo'])}°{rain}</li>")
        rows.append("<ul>" + "".join(items) + "</ul>")
    al = d.get("alerts") or {}
    for a in (al.get("official") or [])[:3]:
        name = a.get("event") or a.get("headline") or a.get("title")
        if name:
            rows.append(f"<p class=alert>⚠ {esc(name)}</p>")
    air = (d.get("outside") or {}).get("air") or {}
    if air.get("aqi") is not None:
        rows.append(f"<p>Air quality: {esc(air.get('label') or '')} ({round(air['aqi'])})</p>")
    return section("Weather", rows)


def calendar(d, today):
    ev = [e for e in d.get("calendar") or [] if e.get("date")]
    tomorrow = (today + dt.timedelta(days=1)).isoformat()
    rows = []
    for label, day in (("Today", today.isoformat()), ("Tomorrow", tomorrow)):
        todays = [e for e in ev if e["date"] == day]
        if not todays:
            continue
        items = []
        for e in todays[:6]:
            when = "All day" if e.get("all_day") or not e.get("start") else clock(e["start"])
            where = e.get("where")
            where = f" <span class=dim>· {esc(where)}</span>" if where and not where.startswith("http") else ""
            items.append(f"<li><b>{esc(when)}</b> {esc(e.get('title') or '')}{where}</li>")
        rows.append(f"<h3>{label}</h3><ul>{''.join(items)}</ul>")
    return section("Calendar", rows)


def commute(d):
    items = []
    for c in d.get("commute") or []:
        if c.get("minutes") is None:
            continue
        delay = c.get("delay") or 0
        note = f" <b>(+{delay} min)</b>" if delay >= 5 else ""
        items.append(f"<li>{esc(c['label'])}: {c['minutes']} min{note}</li>")
    return section("Drive times", ["<ul>" + "".join(items) + "</ul>" if items else ""])


def solar(d, today):
    rows = []
    yday = (today - dt.timedelta(days=1)).isoformat()
    y = next((x for x in d.get("days") or [] if x.get("date") == yday), None)
    if y and y.get("produced") is not None:
        ly = y.get("last_year")
        ly = f" (last year: {round(ly)} kWh)" if ly else ""
        rows.append(f"<p>Yesterday the panels made <b>{round(y['produced'])} kWh</b>{ly}.</p>")
    s = (d.get("solar") or {}).get("summary") or {}
    if s.get("month") is not None:
        rows.append(f"<p>This month so far: {round(s['month'])} kWh.</p>")
    b = d.get("bill") or {}
    if b.get("cycle_day"):
        line = f"PG&amp;E bill: day {b['cycle_day']} of {b['cycle_days']}"
        if b.get("cost") is not None:
            line += f", ${b['cost']:.2f} so far"
        elif b.get("solar_value_cycle") is not None:
            line += f", solar has saved ${b['solar_value_cycle']:.2f}"
        rows.append(f"<p>{line}.</p>")
    g = d.get("grid") or {}
    if g.get("peak") or g.get("cleanest"):
        bits = []
        if g.get("peak"):
            bits.append(f"avoid big loads {esc(g['peak'])}")
        if g.get("cleanest"):
            bits.append(f"cleanest power {esc(g['cleanest'])}")
        rows.append("<p>Grid: " + "; ".join(bits) + ".</p>")
    for l in d.get("loads") or []:
        if l.get("date") == today.isoformat() and l.get("from"):
            rows.append(f"<p>Best time to run big appliances today: {hour(l['from'])} to {hour(l['to'])}.</p>")
    return section("Solar and power", rows)


def headlines(d):
    news = d.get("news") or {}
    rows = []
    for key, label in (("big", "Big news"), ("local", "Local news")):
        items = [it for it in news.get(key) or [] if it.get("title")][:5]
        if items:
            lis = "".join(f"<li>{esc(it['title'])} <span class=dim>· {esc(it.get('source') or '')}</span></li>"
                          for it in items)
            rows.append(f"<h3>{label}</h3><ul>{lis}</ul>")
    return section("Headlines", rows)


def extras(d, today):
    rows = []
    facts = (d.get("almanac") or {}).get("facts") or []
    if facts:
        rows.append("<ul>" + "".join(f"<li>{esc(f)}</li>" for f in facts[:3]) + "</ul>")
    p = d.get("poem") or {}
    if p.get("text") and p.get("date") == today.isoformat():
        lines = p["text"].strip().split("\n")
        body = "<br>".join(esc(x) for x in lines[:20])
        more = " …" if len(lines) > 20 else ""
        rows.append(f"<h3>{esc(p.get('title') or 'Poem')}</h3><p class=poem>{body}{more}</p>"
                    f"<p class=dim>{esc(p.get('poet') or '')}</p>")
    return section("For your morning", rows)


CSS = """
body{background:#fff;color:#000;font-family:Georgia,serif;font-size:1.25em;line-height:1.4;margin:0 4%;}
h1{font-size:1.9em;margin:.4em 0 0}
h2{font-size:1.35em;border-bottom:3px solid #000;margin:1.1em 0 .3em;padding-bottom:.1em}
h3{font-size:1.05em;margin:.6em 0 .1em}
p{margin:.3em 0} ul{margin:.2em 0;padding-left:1.2em} li{margin:.15em 0}
.big{font-size:2.2em} .dim{color:#444} .alert{font-weight:bold;border:3px solid #000;padding:.3em}
.poem{font-style:italic} .foot{margin:1.5em 0;color:#444;font-size:.85em}
a{color:#000}
"""


def render(d):
    tz = ZoneInfo((d.get("solar") or {}).get("timezone") or "America/Los_Angeles")
    today = dt.date.fromisoformat(d["today"]) if d.get("today") else dt.datetime.now(tz).date()
    hol = [h["name"] for h in d.get("holidays") or [] if h.get("date") == today.isoformat() and h.get("country") == "USA"]
    sub = f"<p><b>{esc(', '.join(hol))}</b></p>" if hol else ""
    made = ""
    if d.get("generated_at"):
        t = dt.datetime.fromisoformat(d["generated_at"]).astimezone(tz)
        made = t.strftime("%a %-I:%M %p").replace(" 0", " ")
    parts = []
    for fn in (lambda: weather(d, today), lambda: calendar(d, today), lambda: commute(d),
               lambda: solar(d, today), lambda: headlines(d), lambda: extras(d, today)):
        try:
            parts.append(fn())
        except Exception as e:  # one bad field should not blank the page
            print(f"kindle: skipped a section: {e!r}", file=sys.stderr)
    body = "\n".join(p for p in parts if p)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning</title><style>{CSS}</style></head>
<body>
<h1>{today.strftime('%A, %B')} {today.day}</h1>
{sub}
{body}
<p class=foot>Updated {esc(made)}. <a href="index.html">Full dashboard</a></p>
</body></html>
"""


def main(src, dest):
    with open(src) as f:
        d = json.load(f)
    with open(dest, "w") as f:
        f.write(render(d))


if __name__ == "__main__":
    main(*sys.argv[1:3])
