#!/usr/bin/env python3
"""snap_svg.py - enforce the e-ink rules (eink-guide.md) on SVG mechanically. Stdlib only.

    from snap_svg import snap
    out = snap(svg_text, display_width=None, name="")   # -> svg_text

CLI:
    snap_svg.py in.svg [-o out.svg] [--display-width 200] [--report]
    snap_svg.py --inplace --backup-dir orig  a.svg b.svg ...   (keeps originals)

What it changes (geometry otherwise untouched):
  * stroke-width (attributes + inline style), measured in DISPLAYED CSS px
    (viewBox -> display width x ancestor transforms x pattern scales):
      <= 1.75 css px -> nearest of 0.5 / 1 / 1.5 (min 0.5);  heavier strokes -> nearest 0.5
      (whole device px), so deliberate heavy rules are not crushed to 1.5.
  * every fill / stroke / stop-color / flood-color / color -> one of the 16 exact greys
    (luma, rounded to k*0x11; anything >= #f8f8f8 -> #fff).
  * opacity / fill-opacity / stroke-opacity / stop-opacity -> blended onto white, snapped, removed.
  * <pattern patternUnits="userSpaceOnUse"> tiles: displayed pitch -> 1, 1.5, 2 or 3 css px
    (tiles > 3.5 css px -> nearest 0.5 css px = whole device px). Content is rescaled with
    the tile by a wrapping <g transform="scale(..)">, and x/y offsets with it.
  * shape-rendering="crispEdges" on axis-aligned straight hatching inside patterns
    (lines/rects/H-V paths, when the pattern is not rotated off 90-degree multiples).
Display width is inferred from the file name when not given:
    emblem -> 200, headpiece/plate/tailpiece/cartouche -> 560, cover/morning-plate -> 570,
    frame -> 618, otherwise the svg's own width attribute (1:1).
"""
import re, sys, math, os, shutil, argparse
import xml.etree.ElementTree as ET

SVG = 'http://www.w3.org/2000/svg'; XL = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG); ET.register_namespace('xlink', XL)
Q = lambda t: f'{{{SVG}}}{t}'
SHAPES = {'path','rect','circle','ellipse','line','polyline','polygon','text','tspan','textPath','use'}
NOPAINT_CONTAINERS = {'clipPath','mask','marker','symbol'}   # still processed, CTM approximated

NAMED = {'black':(0,0,0),'white':(255,255,255),'gray':(128,128,128),'grey':(128,128,128),
         'silver':(192,192,192),'darkgray':(169,169,169),'darkgrey':(169,169,169),'lightgray':(211,211,211),
         'lightgrey':(211,211,211),'dimgray':(105,105,105),'dimgrey':(105,105,105),'gainsboro':(220,220,220),
         'whitesmoke':(245,245,245),'red':(255,0,0),'green':(0,128,0),'blue':(0,0,255),'navy':(0,0,128),
         'maroon':(128,0,0),'ivory':(255,255,240),'linen':(250,240,230),'beige':(245,245,220)}
PAINT_PROPS = ('fill','stroke','stop-color','flood-color','lighting-color','color')
OPAC_PROPS = ('opacity','fill-opacity','stroke-opacity','stop-opacity','flood-opacity')

STATS = {}
def _count(k, n=1): STATS[k] = STATS.get(k, 0) + n

# ---------------------------------------------------------------- numbers / colours
def fmt(v):
    s = f'{v:.4f}'.rstrip('0').rstrip('.'); return s if s not in ('', '-0') else '0'

def parse_color(s):
    s = s.strip().lower()
    if s.startswith('#'):
        h = s[1:]
        if len(h) in (3, 4): return tuple(int(c*2, 16) for c in h[:3])
        if len(h) in (6, 8): return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return None
    m = re.match(r'rgba?\(([^)]*)\)', s)
    if m:
        p = [x.strip() for x in m.group(1).replace('/', ',').split(',') if x.strip()]
        try:
            rgb = tuple(round(float(x[:-1])*2.55) if x.endswith('%') else int(float(x)) for x in p[:3])
            a = float(p[3][:-1])/100 if len(p) > 3 and p[3].endswith('%') else (float(p[3]) if len(p) > 3 else 1.0)
            return rgb + (a,) if a < 1 else rgb
        except ValueError: return None
    return NAMED.get(s)

def snap_grey(rgb, alpha=1.0):
    y = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]
    if len(rgb) > 3: alpha *= rgb[3]
    y = 255 - alpha*(255 - y)                     # blend onto white paper
    if y >= 0xf8: return '#fff'
    k = int(round(y/17.0)); v = f'{k*17:02x}'
    return '#' + (v[0]*3 if v[0] == v[1] else v*3)

# ---------------------------------------------------------------- style helpers
def get_style(el):
    st = {}
    for part in (el.get('style') or '').split(';'):
        if ':' in part:
            k, v = part.split(':', 1); st[k.strip()] = v.strip()
    return st
def set_style(el, st):
    if st: el.set('style', ';'.join(f'{k}:{v}' for k, v in st.items()))
    elif 'style' in el.attrib: del el.attrib['style']
def prop(el, k):
    st = get_style(el)
    return st[k] if k in st else el.get(k)
def set_prop(el, k, v):
    st = get_style(el)
    if k in st:
        if v is None: del st[k]
        else: st[k] = v
        set_style(el, st)
        if k in el.attrib and v is not None: el.set(k, v)
    if v is None:
        el.attrib.pop(k, None)
    elif k not in st:
        el.set(k, v)

def tag(el): return el.tag.split('}')[-1]

# ---------------------------------------------------------------- transforms
def parse_transform(t):
    """-> 2x3 matrix (a,b,c,d,e,f)"""
    M = (1, 0, 0, 1, 0, 0)
    for name, args in re.findall(r'(\w+)\s*\(([^)]*)\)', t or ''):
        v = [float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', args)]
        if name == 'matrix' and len(v) == 6: N = tuple(v)
        elif name == 'translate': N = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == 'scale': N = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == 'rotate':
            a = math.radians(v[0]); c, s = math.cos(a), math.sin(a)
            N = (c, s, -s, c, 0, 0)
            if len(v) == 3:
                cx, cy = v[1], v[2]; N = mul(mul((1,0,0,1,cx,cy), N), (1,0,0,1,-cx,-cy))
        elif name == 'skewX': N = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        elif name == 'skewY': N = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        else: continue
        M = mul(M, N)
    return M
def mul(A, B):
    a,b,c,d,e,f = A; A2,B2,C2,D2,E2,F2 = B
    return (a*A2+c*B2, b*A2+d*B2, a*C2+c*D2, b*C2+d*D2, a*E2+c*F2+e, b*E2+d*F2+f)
def mscale(M): return math.sqrt(abs(M[0]*M[3] - M[1]*M[2])) or 1.0
def axis_aligned(M, tol=1e-3): return abs(M[1]) < tol and abs(M[2]) < tol or abs(M[0]) < tol and abs(M[3]) < tol

# ---------------------------------------------------------------- snapping rules
FINE_MAX = 0.75   # strokes below this (css px) become 0.5; set lower (e.g. 0.6) to push AA curves to 1 px
def snap_stroke_css(d):
    if d <= 0: return d
    if d < FINE_MAX: return 0.5
    if d <= 1.75: return min((1.0, 1.5), key=lambda c: (abs(c-d), c))
    return max(0.5, round(d*2)/2)
def snap_pitch_css(p):
    if p <= 3.5: return min((1.0, 1.5, 2.0, 3.0), key=lambda c: (abs(c-p), -c))
    return round(p*2)/2

def num(s):
    if s is None: return None
    m = re.match(r'\s*([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)\s*(px)?\s*$', s)
    return float(m.group(1)) if m else None

# ---------------------------------------------------------------- passes
def guess_display_width(name, root):
    n = (name or '').lower()
    for key, w in (('emblem', 200), ('headpiece', 560), ('tailpiece', 560), ('cartouche', 560),
                   ('cover', 570), ('morning-plate', 570), ('frame', 618), ('plate', 560)):
        if key in n: return w
    cls = (root.get('class') or '') + ' ' + (root.get('id') or '')
    for key, w in (('emblem', 200), ('headpiece', 560), ('tailpiece', 560), ('morning-plate', 570), ('frame', 618)):
        if key in cls: return w
    return num(root.get('width'))

def doc_scale(root, display_width):
    vb = root.get('viewBox')
    vbw = float(re.split(r'[\s,]+', vb.strip())[2]) if vb else num(root.get('width'))
    if not vbw or not display_width: return 1.0
    return display_width / vbw

def pass_patterns(root, S):
    for pat in root.iter(Q('pattern')):
        if (pat.get('patternUnits') or 'objectBoundingBox') != 'userSpaceOnUse': continue
        w, h = num(pat.get('width')), num(pat.get('height'))
        if not w or not h: continue
        PT = parse_transform(pat.get('patternTransform'))
        # displayed pitch along the tile's own axes
        sx = S*math.hypot(PT[0], PT[1]); sy = S*math.hypot(PT[2], PT[3])
        dw, dh = w*sx, h*sy
        fx, fy = snap_pitch_css(dw)/dw, snap_pitch_css(dh)/dh
        if abs(fx-1) < 1e-3 and abs(fy-1) < 1e-3: continue
        _count('pattern tiles snapped')
        pat.set('width', fmt(w*fx)); pat.set('height', fmt(h*fy))
        for k, f in (('x', fx), ('y', fy)):
            v = num(pat.get(k))
            if v: pat.set(k, fmt(v*f))
        if pat.get('viewBox'): continue              # content follows the tile automatically
        kids = list(pat)
        g = ET.Element(Q('g'), {'transform': f'scale({fmt(fx)} {fmt(fy)})', 'data-snap': 'pitch'})
        for k in kids: pat.remove(k); g.append(k)
        pat.append(g)

def is_axis_straight(el):
    t = tag(el)
    if t == 'rect': return True
    if t == 'line':
        x1, y1, x2, y2 = (num(el.get(k)) or 0 for k in ('x1', 'y1', 'x2', 'y2'))
        return abs(x1-x2) < 1e-6 or abs(y1-y2) < 1e-6
    if t in ('polyline', 'polygon'):
        v = [float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', el.get('points') or '')]
        pts = list(zip(v[0::2], v[1::2]))
        return all(abs(a[0]-b[0]) < 1e-6 or abs(a[1]-b[1]) < 1e-6 for a, b in zip(pts, pts[1:]))
    if t == 'path':
        d = el.get('d') or ''
        if re.search(r'[CcSsQqTtAa]', d): return False
        x = y = sx = sy = 0.0
        for c in re.findall(r'[MmLlHhVvZz][^MmLlHhVvZz]*', d):
            op = c[0]; v = [float(n) for n in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?', c[1:])]
            if op in 'Zz': x, y = sx, sy; continue
            if op in 'Hh':
                for n in v: x = x+n if op == 'h' else n
                continue
            if op in 'Vv':
                for n in v: y = y+n if op == 'v' else n
                continue
            for i in range(0, len(v)-1, 2):
                nx, ny = (x+v[i], y+v[i+1]) if op.islower() else (v[i], v[i+1])
                line = op in 'Ll' or i > 0
                if line and abs(nx-x) > 1e-6 and abs(ny-y) > 1e-6: return False
                x, y = nx, ny
                if op in 'Mm' and i == 0: sx, sy = x, y
        return True
    return False

def pass_crisp(root, S):
    for pat in root.iter(Q('pattern')):
        PT = parse_transform(pat.get('patternTransform'))
        if not axis_aligned(PT): continue
        shapes = [e for e in pat.iter() if tag(e) in SHAPES]
        if shapes and all(is_axis_straight(e) for e in shapes):
            for e in shapes:
                if e.get('shape-rendering') is None: e.set('shape-rendering', 'crispEdges'); _count('crispEdges added')

def walk(el, M, inh, S, parent_map):
    """inh: inherited fill, stroke, fill-op, stroke-op, op-mult, stroke-width(user, scale-at-decl)"""
    t = tag(el)
    if t == 'pattern':                     # pattern content lives in the referencing element's space
        M = mul((S, 0, 0, S, 0, 0), parse_transform(el.get('patternTransform')))
        inh = dict(fill=(0,0,0), stroke=None, fo=1.0, so=1.0, op=1.0, sw=1.0)
    else:
        M = mul(M, parse_transform(el.get('transform')))
    inh = dict(inh)
    # --- paint inheritance
    for k, key in (('fill', 'fill'), ('stroke', 'stroke')):
        v = prop(el, k)
        if v is not None:
            vv = v.strip().lower()
            if vv in ('none', 'transparent'): inh[key] = None
            elif vv.startswith('url(') or vv in ('currentcolor', 'inherit'): inh[key] = 'keep'
            else:
                c = parse_color(v)
                if c is not None: inh[key] = c
                else: _count('unparsed colour ' + v)
    for k, key in (('fill-opacity', 'fo'), ('stroke-opacity', 'so')):
        v = num(prop(el, k))
        if v is not None: inh[key] = v
    opv = num(prop(el, 'opacity'))
    if opv is not None: inh['op'] = inh['op']*opv
    swv = prop(el, 'stroke-width')
    if swv is not None and num(swv) is not None: inh['sw'] = num(swv)

    sc = mscale(M)
    # --- stroke width: snap where declared, and pin on shapes whose scale differs
    stroked = inh['stroke'] is not None
    if swv is not None and num(swv) is not None:
        d = num(swv)*sc
        nd = snap_stroke_css(d)
        if d > 0 and abs(nd-d) > 1e-3:
            set_prop(el, 'stroke-width', fmt(nd/sc)); _count('stroke-width snapped')
            inh['sw'] = nd/sc
    elif t in SHAPES and stroked:
        d = inh['sw']*sc; nd = snap_stroke_css(d)
        if d > 0 and abs(nd-d) > 1e-3:
            el.set('stroke-width', fmt(nd/sc)); _count('stroke-width pinned on shape')

    # --- colours
    alpha_f = inh['fo']*inh['op']; alpha_s = inh['so']*inh['op']
    for k in PAINT_PROPS:
        v = prop(el, k)
        if v is None: continue
        c = parse_color(v)
        if c is None: continue
        a = alpha_s if k == 'stroke' else alpha_f if k == 'fill' else 1.0
        if k == 'stop-color':
            so = num(prop(el, 'stop-opacity')); a = (so if so is not None else 1.0)*inh['op']
        nv = snap_grey(c, a)
        if nv != v.strip().lower(): _count('colour snapped')
        set_prop(el, k, nv)
    if t in SHAPES:   # bake inherited translucency onto shapes that did not declare their own colour
        if prop(el, 'fill') is None and isinstance(inh['fill'], tuple) and alpha_f < 1:
            el.set('fill', snap_grey(inh['fill'], alpha_f)); _count('opacity baked')
        if prop(el, 'stroke') is None and isinstance(inh['stroke'], tuple) and alpha_s < 1:
            el.set('stroke', snap_grey(inh['stroke'], alpha_s)); _count('opacity baked')
    for k in OPAC_PROPS:
        if prop(el, k) is not None: set_prop(el, k, None); _count('opacity removed')

    for ch in list(el):
        if isinstance(ch.tag, str): walk(ch, M, inh, S, parent_map)

def snap_root(root, display_width=None, name=''):
    dw = display_width or guess_display_width(name, root)
    S = doc_scale(root, dw)
    pass_patterns(root, S)
    walk(root, (S, 0, 0, S, 0, 0), dict(fill=(0,0,0), stroke=None, fo=1.0, so=1.0, op=1.0, sw=1.0), S, None)
    pass_crisp(root, S)
    root.set('data-eink-snap', f'display {fmt(dw or 0)}px scale {fmt(S)}')
    return S

def snap(svg_text, display_width=None, name=''):
    """Snap one SVG document, or every top-level <svg>...</svg> inside an HTML/text fragment."""
    STATS.clear()
    def one(s):
        root = ET.fromstring(s)
        snap_root(root, display_width, name)
        return ET.tostring(root, encoding='unicode')
    t = svg_text.lstrip()
    if t.startswith('<svg') or t.startswith('<?xml'):
        return one(re.sub(r'^\s*<\?xml[^>]*\?>', '', svg_text))
    out, i = [], 0     # fragments: snap each top-level svg
    for m in re.finditer(r'<svg\b', svg_text):
        if m.start() < i: continue
        depth, j = 0, m.start()
        for mm in re.finditer(r'<svg\b|</svg>', svg_text[m.start():]):
            depth += 1 if mm.group(0) != '</svg>' else -1
            if depth == 0: j = m.start() + mm.end(); break
        out.append(svg_text[i:m.start()]); out.append(one(svg_text[m.start():j])); i = j
    out.append(svg_text[i:])
    return ''.join(out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+'); ap.add_argument('-o', '--out')
    ap.add_argument('--display-width', type=float)
    ap.add_argument('--inplace', action='store_true'); ap.add_argument('--backup-dir', default='orig')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--fine-max', type=float, default=0.75, help='strokes thinner than this (css px) -> 0.5, others >= 1')
    a = ap.parse_args()
    global FINE_MAX; FINE_MAX = a.fine_max
    for f in a.files:
        src = open(f, encoding='utf-8').read(); mt = os.path.getmtime(f)
        if a.inplace and 'data-eink-snap' in src[:2000]:
            print(f'{f}: already snapped, skipped', file=sys.stderr); continue
        out = snap(src, a.display_width, os.path.basename(f))
        if a.inplace:
            bdir = os.path.join(os.path.dirname(f) or '.', a.backup_dir); os.makedirs(bdir, exist_ok=True)
            bk = os.path.join(bdir, os.path.basename(f))
            shutil.copy2(f, bk)          # fresh (unsnapped) generation -> refresh the original
            if os.path.getmtime(f) != mt: print(f'SKIP {f}: changed while snapping'); continue
            open(f, 'w', encoding='utf-8').write(out)
        elif a.out: open(a.out, 'w', encoding='utf-8').write(out)
        else: sys.stdout.write(out)
        if a.report or a.inplace: print(f'{f}: ' + ', '.join(f'{k} {v}' for k, v in sorted(STATS.items())), file=sys.stderr)

if __name__ == '__main__':
    main()
