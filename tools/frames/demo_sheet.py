"""python3 tools/frames/demo_sheet.py OUTDIR : a full 618 x 714 sheet, three panels set in a scroll field."""
import sys, os, time, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
from solar.frames import kpanel
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, B = 618, 714, 4
panels = [(44, 44, 530, 184), (44, 264, 530, 148), (44, 448, 530, 150)]   # white panel boxes
holes = [(x - B, y - B, w + 2 * B, h + 2 * B) for x, y, w, h in panels]
t = time.time()
fsvg = scroll.field(W, H, holes, seed=int(sys.argv[2]) if len(sys.argv) > 2 else 1)
print('field %.1f KB %.2f s' % (len(fsvg) / 1024, time.time() - t))
open(os.path.join(out, 'field.svg'), 'w').write(fsvg)
parts = [fsvg]
for k, (x, y, w, h) in enumerate(panels):
    e = kpanel.panel_edge(w, h, seed=k)
    open(os.path.join(out, 'edge%d.svg' % k), 'w').write(e)
    parts.append(e.replace('<svg ', '<svg x="%d" y="%d" ' % (x - B, y - B), 1).replace(' xmlns="http://www.w3.org/2000/svg"', ''))
inner = '<rect x="%d" y="%d" width="%d" height="%d" fill="#fff"/>'
body = ''.join(inner % p for p in panels)
sheet = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><rect width="%d" height="%d" fill="#fff"/>' % (W, H, W, H, W, H)
         + body + ''.join(p.replace(' xmlns="http://www.w3.org/2000/svg"', '', 1) if i == 0 else p for i, p in enumerate(parts)) + '</svg>')
open(os.path.join(out, 'sheet.svg'), 'w').write(sheet)
