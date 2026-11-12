"""python3 tools/engrave/gen.py <slug> : run solar/plates/<slug>.py at the sizes the page needs, check budgets."""
import importlib.util, json, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); T = os.path.join(R, "tools", "engrave")
sys.path[:0] = [os.path.join(R, "solar")]
slug = sys.argv[1]
items = {i["file"][:-5]: i for i in json.load(open(os.path.join(T, "page-items.json")))}
rooms = json.load(open(os.path.join(T, "rooms.json")))
ctx = dict(items.get(slug, {"file": slug + ".html", "title": slug}), slug=slug, date="2026-11-12", sheet=0)
spec = importlib.util.spec_from_file_location("plate_" + slug.replace("-", "_"), os.path.join(R, "solar", "plates", slug + ".py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
W = 526
sizes = sorted({(W, r["h"]) for r in rooms.get(slug + ".html", []) if r.get("h")} | {(W, h) for h in (60, 90, 130, 180, 240, 320, 420, 548)}, key=lambda x: x[1])
out = os.path.join(T, "out", slug); os.makedirs(out, exist_ok=True)
for f in os.listdir(out): os.remove(os.path.join(out, f))
import snap_svg, time
bad = []
for w, h in sizes:
    t0 = time.time(); svg = snap_svg.snap(m.plate(w, h, dict(ctx))); dt = time.time() - t0
    open(os.path.join(out, f"z-{w}x{h}.svg"), "w").write(svg)
    n = len(re.findall(r"<(?!/|\?|!)", svg)); kb = len(svg.encode()) / 1024
    vb = re.search(r'viewBox="([^"]+)"', svg); iss = []
    if n > 600: iss.append(f"{n} elements > 600")
    if kb > 200: iss.append(f"{kb:.0f} KB > 200")
    if dt > 1: iss.append(f"{dt:.1f}s > 1s")
    if "<text" in svg: iss.append("<text>")
    if re.search(r"<(mask|filter|foreignObject)", svg): iss.append("mask/filter")
    if not vb or [float(x) for x in vb.group(1).split()][2:] != [w, h]: iss.append("viewBox")
    print(f"z-{w}x{h}.svg {n:4d} el {kb:6.1f} KB {'; '.join(iss) or 'ok'}"); bad += iss
sys.exit(1 if bad else 0)
