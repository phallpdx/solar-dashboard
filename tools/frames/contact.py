"""python3 tools/frames/contact.py DIR OUT.png : contact sheet on #ddd.

For each frame in DIR (meta.json from sheet.py): the frame large (rendered at 6x) and at real Kindle size
(2x device pixels, posterised to the panel's 16 greys), with its audit numbers.  The head of the sheet sets
crops of Parker's references beside the engine's band at a similar scale."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import check

D, OUT = sys.argv[1], sys.argv[2]
REFS = '/mnt/project-files/kindle/redesign/refs/'
meta = json.load(open(os.path.join(D, 'meta.json')))
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except Exception:
    font = small = ImageFont.load_default()
W = 3400
rows = []


def q16(im):
    bg = Image.new('RGBA', im.size, (221, 221, 221, 255)); bg.alpha_composite(im)
    g = bg.convert('L').point(lambda v: min(255, round(v / 17) * 17))
    return g.convert('RGB')


def on_ddd(im):
    bg = Image.new('RGBA', im.size, (221, 221, 221, 255)); bg.alpha_composite(im)
    return bg.convert('RGB')


# head: references against the engine at a similar scale
head = []
try:
    v = Image.open(REFS + 'parker-ref-vise.jpg').convert('RGB').crop((80, 470, 700, 640))
    r = Image.open(REFS + 'parker-ref-revolver.jpg').convert('RGB').crop((150, 700, 520, 860))
    head = [('reference: vise band (crop)', v.resize((v.size[0] * 2, v.size[1] * 2))),
            ('reference: revolver frame (crop)', r.resize((r.size[0] * 2, r.size[1] * 2)))]
except Exception as e:
    print('refs missing', e)
big = [m for m in meta if m['fam'] == 'kpanel'][0]
eng = Image.open(os.path.join(D, big['name'] + '@6.png')).convert('RGBA')
head.append(('engine: kpanel band at 6x (the vise crop is shown at roughly 3x the engine field height)', on_ddd(eng.crop((0, 0, min(eng.size[0], 1240), min(eng.size[1], 340))))))
for m in meta:
    p6 = Image.open(os.path.join(D, m['name'] + '@6.png')).convert('RGBA')
    p2 = Image.open(os.path.join(D, m['name'] + '.png')).convert('RGBA')
    a = check.audit(os.path.join(D, m['name'] + '.svg'))
    rows.append((m, on_ddd(p6) if p6.size[0] <= W - 40 else on_ddd(p6.crop((0, 0, W - 40, p6.size[1]))), q16(p2), a))
H = 40 + sum(im.size[1] + 40 for _, im in head) + sum(max(b.size[1], 0) + s.size[1] + 70 for _, b, s, _ in rows)
sheet = Image.new('RGB', (W, H), (221, 221, 221))
dr = ImageDraw.Draw(sheet)
y = 20
dr.text((20, y), 'Engraved frames: fine-scroll engine (solar/scroll.py), branch claude/engrave-frames', fill=0, font=font); y += 30
for label, im in head:
    dr.text((20, y), label, fill=0, font=small); y += 18
    sheet.paste(im, (20, y)); y += im.size[1] + 22
for m, b, s, a in rows:
    dr.text((20, y), '%s  %dx%d  %s   %.1f KB, %.2f s, band ink %.0f%%, largest white outside slot %.1f px   %s' % (
        m['fam'], m['w'], m['h'], m['ctx'] or '', a['kb'], m['sec'], a['band'] * 100, a['white'],
        '; '.join(a['issues']) or 'checks ok'), fill=0, font=small)
    y += 20
    sheet.paste(b, (20, y))
    dr.text((20, y + b.size[1] + 4), 'real size on the Kindle (device pixels, 16 greys):', fill=0, font=small)
    sheet.paste(s, (20, y + b.size[1] + 22))
    y += b.size[1] + s.size[1] + 50
sheet = sheet.crop((0, 0, W, y))
sheet.save(OUT, optimize=True)
print(OUT, sheet.size)
