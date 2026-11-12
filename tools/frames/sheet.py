"""python3 tools/frames/sheet.py OUTDIR : render every family at its sizes into OUTDIR/*.svg."""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import importlib
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
CASES = [
    ('chip', 96, 30, {}), ('chip', 80, 30, {'variant': 'lit', 'seed': 2}), ('chip', 140, 30, {'seed': 3}),
    ('button', 200, 40, {'point': 'left'}), ('button', 200, 40, {'point': 'right', 'seed': 2}), ('button', 96, 40, {'seed': 3}),
    ('button', 300, 52, {'seed': 4}),
    ('sections', 118, 26, {}),
    ('runhead', 110, 26, {}), ('runhead', 132, 26, {'seed': 2}),
    ('banner', 526, 80, {}),
    ('tile', 250, 110, {}), ('tile', 506, 100, {'seed': 2}),
    ('tablehead', 506, 34, {}),
    ('barbase', 506, 14, {}),
    ('gauge', 88, 12, {}),
    ('divider', 140, 16, {}),
    ('initial', 74, 74, {}),
    ('kpanel', 547 + 36, 160 + 36, {'band': 18}), ('kpanel', 547 + 36, 120 + 36, {'band': 18, 'open_bottom': True, 'seed': 2}),
    ('kpanel', 529 + 36, 560 + 36, {'band': 18, 'seed': 5}),
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
