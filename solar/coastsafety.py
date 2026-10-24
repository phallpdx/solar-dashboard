"""Is it safe to dig clams or catch crab at the coast? Oregon Department of Agriculture biotoxin
closures, plus ODFW's yearly ocean crabbing closure."""
import datetime as dt
import html
import re
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (solar-dashboard personal dashboard)"}
URL = "https://www.oregon.gov/oda/programs/foodsafety/shellfish/pages/shellfishclosures.aspx"
KINDS = ["Razor clams", "Mussels", "Bay clams", "Crab", "Scallops"]


def _text(page):
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page))).strip()


def parse(page):
    text = _text(page)
    start = text.find("Sport shellfish harvesting biotoxin status")
    if start < 0:
        raise RuntimeError("ODA page layout changed (no status section)")
    text = text[start:]
    updated = re.search(r"last updated:?\s*(\d{1,2}/\d{1,2}/\d{2,4})", text)
    out = []
    for i, kind in enumerate(KINDS):
        m = re.search(r"\b" + kind + r"\b", text[1:]) if kind != "Crab" else re.search(r"\bCrab Sport crab", text)
        if not m:
            continue
        s = m.start() + (1 if kind != "Crab" else 0)
        nxt = [text.find(" " + k + " ", s + len(kind)) for k in KINDS[i + 1:]] + [text.find("Commercial shellfish", s)]
        nxt = [n for n in nxt if n > s]
        chunk = text[s:min(nxt) if nxt else s + 600]
        status = "Closed" if " CLOSED " in f" {chunk} " else "Open" if " OPEN " in f" {chunk} " else None
        if not status:
            continue
        sentence = re.search(r"(The sport harvest[^.]*\.|Sport crab harvesting[^.]*\.)", chunk)
        why = None
        if status == "Closed":
            reason = re.search(r"for ([^.]*?(domoic acid|paralytic shellfish toxin|PSP|DSP|biotoxin)[^.]*)", chunk, re.I)
            why = reason.group(1) if reason else None
            where = re.search(r"CLOSED\s+(from [^.]*?)(?: for |\.)", chunk)
            why = "; ".join(x for x in ((where.group(1) if where else None), why) if x)
        out.append({"kind": kind, "status": status, "detail": why})
    if not out:
        raise RuntimeError("couldn't read any shellfish statuses")
    return {"items": out, "updated": updated.group(1) if updated else None, "url": URL}


def status():
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return parse(resp.read().decode("utf-8", "replace"))


def crab_season(today):
    """Oregon's ocean crabbing closes Oct 16 to Nov 30 every year; bays, estuaries and jetties stay open."""
    if (today.month == 10 and today.day >= 16) or today.month == 11:
        return "Ocean crabbing is closed until Dec 1 (it closes every Oct 16). Bays, jetties and docks stay open."
    return None
