"""python3 tools/frames/sheet.py OUTDIR : render every family at its sizes into OUTDIR/*.svg."""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import importlib
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
CASES = [
    ('chip', 96, 26, {}), ('chip', 70, 26, {'variant': 'lit', 'seed': 2}), ('chip', 140, 26, {'seed': 3}),
    ('button', 150, 38, {}), ('button', 84, 38, {'seed': 2}), ('button', 220, 38, {'seed': 3}),
    ('sections', 104, 28, {}),
    ('runhead', 90, 28, {}), ('runhead', 250, 28, {'seed': 2}),
    ('banner', 460, 40, {}),
    ('tile', 254, 62, {}), ('tile', 210, 58, {'seed': 2}),
    ('tablehead', 526, 26, {}),
    ('barbase', 506, 12, {}),
    ('gauge', 80, 12, {}),
    ('divider', 526, 14, {}),
    ('initial', 46, 46, {}),
    ('kpanel', 547, 160, {}), ('kpanel', 547, 120, {'open_bottom': True, 'seed': 2}),
]
meta = []
for i, (fam, w, h, ctx) in enumerate(CASES):
    m = importlib.import_module('solar.frames.' + fam)
    t = time.time(); svg = m.frame(w, h, ctx); dt = time.time() - t
    name = '%02d-%s-%dx%d' % (i, fam, w, h)
    open(os.path.join(out, name + '.svg'), 'w').write(svg)
    meta.append(dict(name=name, fam=fam, w=w, h=h, ctx=ctx, sec=round(dt, 3), kb=round(len(svg) / 1024, 1)))
    print('%-34s %6.1f KB %5.2f s' % (name, len(svg) / 1024, dt))
json.dump(meta, open(os.path.join(out, 'meta.json'), 'w'))
