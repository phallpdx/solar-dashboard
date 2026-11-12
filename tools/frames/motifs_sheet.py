"""python3 tools/frames/motifs_sheet.py WORKDIR OUT.png : contact sheet of the section motifs (SECTION_MOTIFS).

Every motif is drawn on the black ground at its field sizes (62 px, the usual; 76 px, the largest open area),
rendered as the build does (2x, crispEdges) and quantised to the four shipping greys (white, #ccc, #888, black).
A. 1:1, one pixel = one Kindle device pixel.  B. The same pixels magnified 3x, nearest-neighbour.
C. A full sheet with a section motif in its field, 1:1, and that field's size as a 2-bit PNG."""
import io, os, re, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from PIL import Image, ImageDraw, ImageFont
from solar import scroll as S

HERE = os.path.dirname(os.path.abspath(__file__))
work, out = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
for f in os.listdir(work):
    if f.endswith(('.svg', '.png')):
        os.remove(os.path.join(work, f))
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
except OSError:
    font = small = ImageFont.load_default()
SIZES = (62, 76)
LEVELS = (0, 0x88, 0xcc, 0xff)


def crisp(svg):
    return svg.replace('<svg ', '<svg shape-rendering="crispEdges" ', 1)


def grey4(im):
    """The build's four greys: #ccc/#bbb print light, #aaa/#888 mid."""
    g = im.convert('L')
    return g.point(lambda v: 255 if v > 229 else 0xcc if v >= 0xbb else 0x88 if v >= 0x44 else 0)


for name, fn in S.SECTION_MOTIFS.items():
    for s in SIZES:
        W = int(s * 1.25) + 8
        cv = S.Canvas(W, W)
        cv.tol = 0.2
        cv.model = True
        cv.add('K', S._rect_d(0, 0, W, W))
        fn(cv, W / 2, W / 2, s)
        open(os.path.join(work, '%s-%d.svg' % (name, s)), 'w').write(crisp(cv.svg()))

# C: the demo layout's field with a section motif at its centre crossing
B = 4
panels = [(44, 44, 530, 184), (44, 264, 530, 148), (44, 448, 530, 150)]
holes = [(x - B, y - B, w + 2 * B, h + 2 * B) for x, y, w, h in panels]
CTX = 'river'
at = []
_dm = S._draw_motif
S._draw_motif = lambda cv, m, x, y, s, rng: (at.append((x, y, s)), _dm(cv, m, x, y, s, rng))
fsvg = S.field(618, 714, holes, seed=1, motif=CTX, cache=False)
S._draw_motif = _dm
inner = ''.join('<rect x="%d" y="%d" width="%d" height="%d" fill="#fff"/>' % p for p in panels)
sheet = ('<svg xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" width="618" height="714" viewBox="0 0 618 714">'
         '<rect width="618" height="714" fill="#fff"/>' + inner
         + re.sub(r'^\s*<\?xml[^>]*>\s*', '', fsvg).replace(' xmlns="http://www.w3.org/2000/svg"', '', 1) + '</svg>')
open(os.path.join(work, 'zsheet.svg'), 'w').write(sheet)
subprocess.run(['node', os.path.join(HERE, 'render.js'), work, '2'], check=True)

tiles = {}
for name in S.SECTION_MOTIFS:
    for s in SIZES:
        im = Image.open(os.path.join(work, '%s-%d.png' % (name, s))).convert('RGBA')
        bg = Image.new('RGB', im.size, '#000')
        bg.paste(im, (0, 0), im)
        tiles[name, s] = grey4(bg)
ctx = Image.open(os.path.join(work, 'zsheet.png')).convert('RGBA')
bg = Image.new('RGB', ctx.size, '#fff')
bg.paste(ctx, (0, 0), ctx)
ctx = grey4(bg)
buf = io.BytesIO()
pal = Image.new('P', (1, 1))
pal.putpalette([v for L in LEVELS for v in (L, L, L)] + [0] * (768 - 12))
ctx.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE).save(buf, 'PNG', bits=2, optimize=True)
ctx_kb = len(buf.getvalue()) / 1024

names = list(S.SECTION_MOTIFS)
M = 3
PAD = 24
colsA = 10
tA = {s: tiles[names[0], s].size[0] for s in SIZES}
tB = tA[SIZES[0]] * M
colsB = 5
Wd = max(PAD * 2 + colsA * (tA[SIZES[-1]] + 16), PAD * 2 + colsB * (tB + 20), PAD * 2 + 1236 + 24 + 6 * 76 + 40)
Hd = (60 + sum(2 * (tA[s] + 40) + 40 for s in SIZES) + 40
      + ((len(names) + colsB - 1) // colsB) * (tB + 40) + 60 + 1428 + 80)
sh = Image.new('L', (Wd, Hd), 0xdd)
dr = ImageDraw.Draw(sh)
y = PAD
dr.text((PAD, y), 'Section motifs: SECTION_MOTIFS in solar/scroll.py (re-exported by solar/frames/field.py), '
        'branch claude/engrave-motifs. Shown in the four shipping greys.', fill=0, font=font)
y += 36
dr.text((PAD, y), 'A. 1:1, one pixel = one Kindle device pixel. View at 100 %.', fill=0, font=font)
y += 30
for s in SIZES:
    dr.text((PAD, y), 'size %d px (%s)' % (s, 'the usual field size' if s == 62 else 'the largest open areas'), fill=0, font=small)
    y += 20
    for i, n in enumerate(names):
        r, c = divmod(i, colsA)
        x = PAD + c * (tA[s] + 16)
        yy = y + r * (tA[s] + 22)
        sh.paste(tiles[n, s], (x, yy))
        dr.text((x, yy + tA[s] + 2), n, fill=0, font=small)
    y += 2 * (tA[s] + 22) + 20
y += 10
dr.text((PAD, y), 'B. The same pixels magnified %dx, nearest-neighbour (size %d).' % (M, SIZES[0]), fill=0, font=font)
y += 30
for i, n in enumerate(names):
    r, c = divmod(i, colsB)
    x = PAD + c * (tB + 20)
    yy = y + r * (tB + 40)
    t = tiles[n, SIZES[0]]
    sh.paste(t.resize((t.size[0] * M, t.size[1] * M), Image.NEAREST), (x, yy))
    dr.text((x, yy + tB + 4), n, fill=0, font=small)
y += ((len(names) + colsB - 1) // colsB) * (tB + 40) + 10
dr.text((PAD, y), 'C. In its field: demo layout with motif="%s", 1:1 device pixels, four greys; right, the motif area at %dx. '
        'Field as 2-bit PNG: %.1f KB (cap 100 KB).' % (CTX, M, ctx_kb), fill=0, font=font)
y += 30
sh.paste(ctx, (PAD, y))
mx, my_, ms = at[0]
hw = int(ms * 1.4)
box = (int(mx * 2) - hw, int(my_ * 2) - hw, int(mx * 2) + hw, int(my_ * 2) + hw)
crop = ctx.crop(box)
sh.paste(crop.resize((crop.size[0] * M, crop.size[1] * M), Image.NEAREST), (PAD + 1236 + 24, y))
sh = sh.crop((0, 0, Wd, y + 1428 + PAD))
sh.save(out, optimize=True)
print(out, sh.size, 'context field %.1f KB' % ctx_kb)
