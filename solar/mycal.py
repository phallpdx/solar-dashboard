"""Parker's own calendar for the next week, from private iCal links (the CALENDAR_ICS secret, one URL per line).

In Google Calendar: Settings, pick the calendar, "Secret address in iCal format". Handles all-day and timed
events, time zones, and the common repeat rules (daily, weekly on given days, monthly, yearly).
"""
import datetime as dt
import urllib.request
from zoneinfo import ZoneInfo

UA = {"User-Agent": "solar-dashboard (personal home dashboard)"}
HOME_TZ = ZoneInfo("America/Los_Angeles")
DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def _fetch(url):
    url = url.strip().replace("webcal://", "https://", 1)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def _when(value, params):
    """iCal date or date-time -> (aware datetime in home time, all_day)."""
    if len(value) == 8:
        return dt.datetime.strptime(value, "%Y%m%d").replace(tzinfo=HOME_TZ), True
    t = dt.datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        t = t.replace(tzinfo=dt.timezone.utc)
    else:
        try:
            t = t.replace(tzinfo=ZoneInfo(params.get("TZID", "America/Los_Angeles")))
        except Exception:
            t = t.replace(tzinfo=HOME_TZ)
    return t.astimezone(HOME_TZ), False


def _parse(text):
    text = text.replace("\r\n", "\n").replace("\n ", "").replace("\n\t", "")
    for block in text.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]
        ev = {"exdates": set()}
        for line in block.split("\n"):
            head, sep, value = line.partition(":")
            if not sep:
                continue
            name, *rest = head.split(";")
            params = dict(p.split("=", 1) for p in rest if "=" in p)
            value = value.strip()
            if name in ("DTSTART", "DTEND", "RECURRENCE-ID"):
                ev[name] = _when(value, params)
            elif name == "EXDATE":
                ev["exdates"].update(_when(v, params)[0] for v in value.split(","))
            elif name in ("SUMMARY", "LOCATION", "RRULE", "UID", "STATUS"):
                ev[name] = value.replace("\\,", ",").replace("\\;", ";").replace("\\n", " ")
        if "DTSTART" in ev and ev.get("STATUS") != "CANCELLED":
            yield ev


def _add_months(t, n):
    m = t.month - 1 + n
    y, m = t.year + m // 12, m % 12 + 1
    try:
        return t.replace(year=y, month=m)
    except ValueError:  # e.g. the 31st in a short month: skip that month
        return None


def _starts(ev, window_end):
    """Every start time of this event between the event's own start and window_end."""
    first = ev["DTSTART"][0]
    rule = dict(p.split("=", 1) for p in ev.get("RRULE", "").split(";") if "=" in p)
    if not rule:
        yield first
        return
    freq, step = rule.get("FREQ"), int(rule.get("INTERVAL", 1))
    count = int(rule["COUNT"]) if "COUNT" in rule else None
    until = _when(rule["UNTIL"], {})[0] if "UNTIL" in rule else None
    bydays = [DAYS.index(d[-2:]) for d in rule.get("BYDAY", "").split(",") if d[-2:] in DAYS]
    made, i = 0, 0
    while i < 5000:
        if freq == "DAILY":
            batch = [first + dt.timedelta(days=i * step)]
        elif freq == "WEEKLY":
            week = first + dt.timedelta(weeks=i * step)
            monday = week - dt.timedelta(days=week.weekday())
            batch = sorted(monday + dt.timedelta(days=d) for d in (bydays or [first.weekday()]))
            batch = [b for b in batch if b >= first]
        elif freq == "MONTHLY":
            batch = [b for b in [_add_months(first, i * step)] if b]
        elif freq == "YEARLY":
            batch = [b for b in [_add_months(first, 12 * i * step)] if b]
        else:
            yield first
            return
        for t in batch:
            if (until and t > until) or (count is not None and made >= count) or t > window_end:
                return
            made += 1
            if t not in ev["exdates"]:
                yield t
        i += 1


def upcoming(urls, now_utc, days=7):
    now = now_utc.astimezone(HOME_TZ)
    day0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = day0 + dt.timedelta(days=days)
    events, moved = [], set()
    parsed = []
    for url in [u for u in urls.splitlines() if u.strip()]:
        parsed += list(_parse(_fetch(url)))
    for ev in parsed:  # a changed single instance of a repeating event replaces the original one
        if "RECURRENCE-ID" in ev:
            moved.add((ev.get("UID"), ev["RECURRENCE-ID"][0]))
    for ev in parsed:
        all_day = ev["DTSTART"][1]
        length = (ev["DTEND"][0] - ev["DTSTART"][0]) if "DTEND" in ev else dt.timedelta(days=1 if all_day else 0)
        for t in _starts(ev, window_end):
            if "RECURRENCE-ID" not in ev and (ev.get("UID"), t) in moved:
                continue
            end = t + length
            if end <= (day0 if all_day else now) or t >= window_end:
                continue
            events.append({"date": max(t, day0).date().isoformat(), "all_day": all_day,
                           "start": None if all_day else t.isoformat(), "end": None if all_day else end.isoformat(),
                           "last_day": (end - dt.timedelta(days=1)).date().isoformat() if all_day and length.days > 1 else None,
                           "title": ev.get("SUMMARY") or "Busy", "where": ev.get("LOCATION") or None})
    events.sort(key=lambda e: (e["date"], not e["all_day"], e["start"] or ""))
    return events[:40]
