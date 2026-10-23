"""Read Portland General Electric (PGE) usage CSV exports (Opower / Green Button format).

Handles interval files (15-minute or hourly rows with START TIME), daily
files, and billing-period files (START DATE / END DATE), with either USAGE or
IMPORT/EXPORT columns. Returns a list of rows:
{"date": "YYYY-MM-DD", "hour": int|None, "import": kWh, "export": kWh, "cost": $|None}
Billing rows also carry "bill": True, "start" and "end", with "date" = end.
"""
import csv
import glob
import os


def _num(text):
    text = (text or "").strip().replace("$", "").replace(",", "")
    if not text:
        return None
    neg = text.startswith("(") and text.endswith(")")
    try:
        value = float(text.strip("()"))
    except ValueError:
        return None
    return -value if neg else value


def read_file(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    start = next((i for i, l in enumerate(lines) if l.upper().startswith("TYPE,")), None)
    if start is None:
        return []
    rows = []
    for rec in csv.DictReader(lines[start:]):
        rec = {k.strip().upper(): (v or "") for k, v in rec.items() if k}
        if "ELECTRIC" not in rec.get("TYPE", "").upper():
            continue
        imp, exp = _num(rec.get("IMPORT (KWH)")), _num(rec.get("EXPORT (KWH)"))
        if imp is None and exp is None:
            usage = _num(rec.get("USAGE (KWH)") or rec.get("USAGE"))
            if usage is None:
                continue
            imp, exp = max(usage, 0.0), max(-usage, 0.0)
        if rec.get("START DATE") and rec.get("END DATE") and not rec.get("DATE"):
            rows.append({
                "bill": True,
                "start": rec["START DATE"].strip(),
                "end": rec["END DATE"].strip(),
                "date": rec["END DATE"].strip(),
                "hour": None,
                "import": imp or 0.0,
                "export": abs(exp or 0.0),
                "cost": _num(rec.get("COST")),
            })
            continue
        start_time = rec.get("START TIME", "").strip()
        rows.append({
            "date": rec.get("DATE", "").strip(),
            "hour": int(start_time.split(":")[0]) if start_time else None,
            "import": imp or 0.0,
            "export": abs(exp or 0.0),
            "cost": _num(rec.get("COST")),
        })
    return rows


def strip_personal_info(path):
    """Drop the name/address/account lines above the TYPE header, in place."""
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    start = next((i for i, l in enumerate(lines) if l.upper().startswith("TYPE,")), None)
    if start:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines[start:]) + "\n")


def read_folder(folder):
    """All CSVs in a folder, newest file wins for any overlapping date."""
    by_date = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv")), key=os.path.getmtime):
        strip_personal_info(path)
        rows = read_file(path)
        for date in {r["date"] for r in rows}:
            by_date[date] = [r for r in rows if r["date"] == date]
    return [r for d in sorted(by_date) for r in by_date[d]]
