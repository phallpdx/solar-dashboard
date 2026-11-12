"""python3 tools/frames/contact.py DIR OUT.png : contact sheet on #ddd.

For each frame in DIR (meta.json from sheet.py): the frame large (rendered at 6x) and at real Kindle size
(2x device pixels, posterised to the panel's 16 greys), with its audit numbers.  The head of the sheet sets
crops of Parker's references beside the engine's band at a similar scale."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFont
import check

D, OUT = sys.argv[1], sys.argv[2]
SHEET = sys.argv[3] if len(sys.argv) > 3 else None
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


# head: references and engine at the SAME physical scale.  The Kindle PW11 is 300 ppi and draws at DPR 2, so one
# device pixel is 1/300 in.  The reference photos are rescaled to 300 ppi from the size of the object in them:
#   vise: the GRS ball (assumed 4.4 in across) spans ~710 px of the photo  -> ~161 px/in -> x1.86
#   revolver: the 1851 Navy cylinder (assumed 1.6 in long) spans ~400 px      -> ~250 px/in -> x1.20
# (estimates from catalogue sizes, good to about +-15 %).  Engine crops are the 2x renders, untouched.
VISE_PPI, REV_PPI = 161.0, 250.0
head = []   # (label, image) shown at 1:1 device pixels
def ref(path, box, ppi):
    im = Image.open(REFS + path).convert('RGB').crop(box)
    k = 300.0 / ppi
    return im.resize((round(im.size[0] * k), round(im.size[1] * k)), Image.LANCZOS)
def dev(name, box=None):
    im = Image.open(os.path.join(D, name + '.png')).convert('RGBA')
    return q16(im.crop(box) if box else im)
byfam = {}
for m in meta:
    byfam.setdefault(m['fam'], []).append(m)
try:
    head += [('reference: vise band, rescaled to 300 ppi', ref('parker-ref-vise.jpg', (80, 470, 640, 640), VISE_PPI)),
             ('reference: revolver frame, rescaled to 300 ppi', ref('parker-ref-revolver.jpg', (150, 700, 520, 860), REV_PPI))]
except Exception as e:
    print('refs missing', e)
kp = byfam['kpanel'][0]
head += [('engine: a corner of the full sheet (field, panel inlay edge), device pixels 1:1, 16 greys', q16(Image.open(os.path.join(SHEET, 'sheet.png')).convert('RGBA').crop((0, 0, 1040, 300)))),
         ('engine: banner 526x80, device pixels 1:1, 16 greys', dev(byfam['banner'][0]['name'])),
         ('engine: button 200x40 (Prev) and 96x40 (More), chip 96x30, device pixels 1:1, 16 greys', None)]
row = [dev(byfam['button'][0]['name']), dev(byfam['button'][2]['name']), dev(byfam['chip'][0]['name'])]
strip_w = sum(i.size[0] for i in row) + 40 * (len(row) - 1)
strip = Image.new('RGB', (strip_w, max(i.size[1] for i in row)), (221, 221, 221))
xx = 0
for i in row:
    strip.paste(i, (xx, 0)); xx += i.size[0] + 40
head[-1] = (head[-1][0], strip)
MAG = 3
def mag(im, photo):
    return im.resize((im.size[0] * MAG, im.size[1] * MAG), Image.LANCZOS if photo else Image.NEAREST)
# the sheet: a full 618 x 714 page, three panels in a scroll field (tools/frames/demo_sheet.py), device px
sheet_rows = []
if SHEET:
    sp = Image.open(os.path.join(SHEET, 'sheet.png')).convert('RGBA')
    sp = q16(sp)
    vfull = ref('parker-ref-vise.jpg', (40, 330, 760, 680), VISE_PPI)
    sheet_rows.append(('S1. A full Kindle sheet (618 x 714 CSS px = 1236 x 1428 device px), three panels set in one scroll field, '
                       '1:1 device pixels, 16 greys; beside it the vise at the same physical scale (300 ppi)', [sp, vfull]))
    asp = os.path.join(SHEET, 'asym.png')
    if len(sys.argv) > 4 and os.path.exists(os.path.join(sys.argv[4], 'asym.png')):
        ap = q16(Image.open(os.path.join(sys.argv[4], 'asym.png')).convert('RGBA'))
        sheet_rows.append(('S1b. An asymmetric sheet (scroll field only, panel windows transparent shown grey): large open areas composed '
                           'about their own centre lines, 1:1 device pixels', [ap]))
    s3 = sp.crop((0, 1150, 1100, 1428))
    s3 = s3.resize((s3.size[0] * MAG, s3.size[1] * MAG), Image.NEAREST)
    v3 = ref('parker-ref-vise.jpg', (80, 470, 640, 640), VISE_PPI)
    v3 = v3.resize((v3.size[0] * MAG, v3.size[1] * MAG), Image.LANCZOS)
    sheet_rows.append(('S2. The sheet\'s foot field at %dx (nearest neighbour)' % MAG, [s3.crop((0, 0, min(s3.size[0], W - 40), s3.size[1]))]))
    sheet_rows.append(('S3. The vise band at the same %dx' % MAG, [v3.crop((0, 0, min(v3.size[0], W - 40), v3.size[1]))]))
for m in meta:
    p6 = Image.open(os.path.join(D, m['name'] + '@6.png')).convert('RGBA')
    p2 = Image.open(os.path.join(D, m['name'] + '.png')).convert('RGBA')
    a = check.audit(os.path.join(D, m['name'] + '.svg'))
    rows.append((m, on_ddd(p6) if p6.size[0] <= W - 40 else on_ddd(p6.crop((0, 0, W - 40, p6.size[1]))), q16(p2), a))
H = 400 + sum(sum(0 for _ in ims) + max(i.size[1] for i in ims) + 60 for _, ims in sheet_rows) + sum(im.size[1] * (1 + MAG) + 80 for _, im in head) + sum(max(b.size[1], 0) + s.size[1] + 70 for _, b, s, _ in rows)
sheet = Image.new('RGB', (W, H), (221, 221, 221))
dr = ImageDraw.Draw(sheet)
y = 20
dr.text((20, y), 'Engraved frames: fine-scroll engine (solar/scroll.py), branch claude/engrave-frames', fill=0, font=font); y += 30
for label, ims in sheet_rows:
    dr.text((20, y), label, fill=0, font=small); y += 18
    xx = 20
    for im in ims:
        sheet.paste(im, (xx, y)); xx += im.size[0] + 40
    y += max(i.size[1] for i in ims) + 30
dr.text((20, y), 'A. Same physical scale: one pixel = one Kindle device pixel (1/300 in). View this part at 100 %.', fill=0, font=font); y += 28
for label, im in head:
    dr.text((20, y), label, fill=0, font=small); y += 18
    sheet.paste(im, (20, y)); y += im.size[1] + 22
dr.text((20, y), 'B. The same crops magnified %dx (photos smooth, engine nearest-neighbour), still at equal scale to each other.' % MAG, fill=0, font=font); y += 28
for k, (label, im) in enumerate(head):
    im = mag(im, k < 2)
    if im.size[0] > W - 40:
        im = im.crop((0, 0, W - 40, im.size[1]))
    dr.text((20, y), label + ' (x%d)' % MAG, fill=0, font=small); y += 18
    sheet.paste(im, (20, y)); y += im.size[1] + 22
dr.text((20, y), 'C. Every family: at 6x (top) and at real size (device pixels, 16 greys).', fill=0, font=font); y += 28
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
