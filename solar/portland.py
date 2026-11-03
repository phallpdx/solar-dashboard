"""Portland here always means Portland, Oregon. News searches and the research runs sometimes pick up
Portland, Maine (South Portland, the Press Herald and so on); this finds those items so they can be dropped."""
import json
import re

# Things that only show up in stories about Maine. "City, Maine" covers the towns around Portland, Maine.
MAINE = re.compile(
    r"\bportland,?\s+maine\b|\bportland,\s*me\b\.?|\bsouth portland\b|,\s*maine\b|\bmaine sunday telegram\b|"
    r"\bpress ?herald\b|pressherald\.com|portlandmaine|portland-maine|mainetoday|newscentermaine|wmtw|wgme|\bwcsh|"
    r"bangordailynews|mainepublic|mainebiz|portland phoenix|\bcasco bay\b|\bmunjoy hill\b", re.I)
# "Maine" next to "Portland" is about Maine too, unless it's a Maine lobster or Maine Coon on a Portland, Oregon menu.
MAINE_WORD = re.compile(r"\bmaine\b(?!\s+(lobster|coon|root|cod|blueberr\w*|potato\w*))", re.I)
PORTLAND = re.compile(r"\bportland\b", re.I)


def _text(x):
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)


def about_maine(x):
    """True when an item (a string, or a dict or list of them) is about Portland, Maine or nearby."""
    t = _text(x)
    return bool(MAINE.search(t) or (MAINE_WORD.search(t) and PORTLAND.search(t)))


def scrub(data):
    """Drops every list entry that's about Portland, Maine, at any depth. Nested lists are cleaned first, so
    an event isn't lost over one bad source link; it goes only if what's left still points to Maine."""
    if isinstance(data, dict):
        return {k: scrub(v) for k, v in data.items()}
    if isinstance(data, list):
        out = []
        for v in data:
            v = scrub(v)
            if isinstance(v, (dict, str)) and about_maine(v):
                continue
            out.append(v)
        return out
    return data
