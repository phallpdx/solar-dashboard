"""Diversions (delights) plate: "something to read, something to talk about, and a picture".
The vignette is an engraved open book lying in a mountain meadow: the day's picture (a Tatra-like
range under a ruled sky with the moon of the day), the book open on its spine, and Flanders poppies
(the verse) growing beside it. Easter egg: a swung pair of eighth notes printed on the right page.
Short: carved scroll frieze round an oval medallion. Medium/tall: the house frame round the scene.
"""
import sys
import math
import random
import engraving_codex as C

_n, _d, hatch = C._n, C._d, C.hatch_poly


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", "")))


def _moon_phase(date):
    try:
        y, m, d = (int(v) for v in date[:10].split("-"))
        # days since a known new moon 2000-01-06
        import datetime
        days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days
        return (days % 29.530588) / 29.530588
    except Exception:
        return .3


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ----------------------------------------------------------------------------------------------
# the scene
# ----------------------------------------------------------------------------------------------

def _sky(cv, x, y, w, h, hy, moon):
    """Ruled sky: wide light lines high, closing to 2 px at the horizon; the moon cut out."""
    cv.obj([], 0)
    mx, my, mr = x + w * .66, y + h * .1, max(3.5, min(w, h) * .055)
    lines = []
    yy = y + 1
    while yy < hy:
        t = (yy - y) / max(1, hy - y)
        lines.append(yy)
        yy += 3 if t < .55 else 2
    for yy in lines:
        dy = yy - my
        if abs(dy) < mr + 1.5:
            dx = math.sqrt(max(0, (mr + 1.5) ** 2 - dy * dy))
            cv.hair([[(x, yy), (mx - dx, yy)], [(mx + dx, yy), (x + w, yy)]])
        else:
            cv.hair([(x, yy), (x + w, yy)])
    # moon: crescent shaded by phase (lit part white, dark part close-ruled)
    disc = C._ell_pts(mx, my, mr, mr, 32)[:-1]
    cv.obj([disc], .5)
    k = math.cos(moon * 2 * math.pi)            # 1 new, -1 full
    term = [(mx + mr * k * math.sin(a) * (1 if moon < .5 else -1), my - mr * math.cos(a))
            for a in [i * math.pi / 16 for i in range(17)]]
    side = -1 if moon < .5 else 1
    dark = term + [(mx + side * mr * math.sin(a), my + mr * math.cos(a)) for a in [i * math.pi / 16 for i in range(17)]]
    if abs(k) < .97 or k > 0:
        cv.hair(hatch(dark, 0, 1.5))


def _ridge(rng, x, w, base, top):
    """A Tatra-like ridge: a few main summits joined by saddles, roughened by midpoint displacement."""
    n = max(3, int(w / 60))
    ctrl = [(x - 3, base - (base - top) * rng.uniform(.2, .35))]
    for i in range(n):
        cx = x + w * (i + rng.uniform(.3, .7)) / n
        ctrl.append((cx, top + (base - top) * rng.uniform(0, .35)))
        if i < n - 1:
            ctrl.append((x + w * (i + 1 + rng.uniform(-.1, .1)) / n, top + (base - top) * rng.uniform(.4, .6)))
    ctrl.append((x + w + 3, base - (base - top) * rng.uniform(.15, .3)))
    pts = ctrl
    amp = (base - top) * .18
    for _ in range(4):
        nxt = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            m = ((a[0] + b[0]) / 2 + rng.uniform(-.1, .1) * (b[0] - a[0]),
                 (a[1] + b[1]) / 2 + rng.uniform(-1, 1) * amp)
            nxt += [m, b]
        pts = nxt
        amp *= .5
    pts = [(px, min(base - 1, max(top - 2, py))) for px, py in pts]
    peaks = [p for p in ctrl[1:-1:2]]
    return pts, peaks


def _mountains(cv, rng, x, w, base, top):
    ridge, peaks = _ridge(rng, x, w, base, top)
    body = ridge + [(x + w + 3, base + 2), (x - 3, base + 2)]
    cv.obj([body], 0)
    cv.hair(hatch(body, 62, 3))
    for a, b in zip(ridge, ridge[1:]):
        if b[1] > a[1] + .2:                       # falls to the right: the face in shadow
            depth = (base - a[1]) * .85
            face = [a, b, (b[0] - (b[1] - a[1]) * .3, b[1] + depth), (a[0] - (b[1] - a[1]) * .3, a[1] + depth)]
            cv.hair(hatch(face, 70, 1.5))
            cv.hair(hatch(face, -20, 3))
    for cx, pk in peaks:                          # snow gullies running down from each summit
        for j in range(4):
            sx = cx + (j - 1.5) * 3
            cv.hair([(sx, pk + 3 + abs(j - 1.5)), (sx - 1.5 + j * .6, pk + 9 + j * 1.5), (sx - 2.5 + j, pk + 14 + j)])
    cv.line(ridge)


def _forest(cv, rng, x, w, base, hgt):
    """A row of spruces along the foot of the range, each shaded on its right."""
    trees = []
    xx = x - 3
    while xx < x + w + 3:
        th = hgt * rng.uniform(.45, 1.)
        trees.append((xx, th))
        xx += hgt * rng.uniform(.3, .75)
    belt = [(x - 2, base), (x + w + 2, base), (x + w + 2, base + hgt * .35), (x - 2, base + hgt * .35)]
    cv.obj([belt], 0)
    cv.hair(hatch(belt, 0, 1.5))
    for tx, th in sorted(trees, key=lambda t: t[1]):
        tw = th * .32
        poly = [(tx, base - th), (tx + tw, base + 1), (tx - tw, base + 1)]
        cv.obj([poly], .5)
        cv.hair(hatch([(tx, base - th), (tx + tw, base + 1), (tx, base + 1)], 90, 1.5))
        for k in range(1, 4):                      # bough tiers
            yy = base - th + th * k / 4
            hw = tw * k / 4
            cv.hair([(tx - hw, yy), (tx, yy - th * .08), (tx + hw * .4, yy - th * .02)])


def _meadow(cv, x, y0, w, y1):
    m = [(x - 2, y0), (x + w + 2, y0), (x + w + 2, y1 + 2), (x - 2, y1 + 2)]
    cv.obj([m], 0)
    yy, k = y0 + 1, 0
    while yy < y1 + 2:
        t = (yy - y0) / max(1, y1 - y0)
        segs = []
        xx = x - 2 + (k * 7) % 11
        while xx < x + w:
            L = 6 + (k * 13 + int(xx)) % 9
            segs.append([(xx, yy), (xx + L, yy)])
            xx += L + 2.2
        cv.hair(segs)
        yy += 2 if t > .35 else 3
        k += 1


def _poppy(cv, x, y, s, lean, seed):
    """A field poppy seen from the side on a curved stem rising from (x, y), about s tall: an open
    cup of four crinkled petals, the far ones dark, a black heart showing at the mouth."""
    rng = random.Random(seed)
    lean_side = 1 if lean > 0 else -1
    stem = [(x + lean * s * .3 * (t * t), y - s * t) for t in [i / 14 for i in range(15)]]
    hx, hy = stem[-1]
    cv.obj([], 0)
    cv.line(stem)
    for side, t in ((lean_side, .2), (lean_side, .42)):         # serrated leaves, on the open side
        bx, by = stem[int(t * 14)]
        L = s * (.3 if t < .3 else .22)
        leaf = [(bx, by)]
        for k in range(1, 6):
            u = k / 6
            leaf.append((bx + side * L * u, by - L * .5 * math.sin(u * math.pi) - (1.5 if k % 2 else 0) - L * .15 * u))
        leaf.append((bx + side * L, by - L * .2))
        for k in range(5, 0, -1):
            u = k / 6
            leaf.append((bx + side * L * u, by - L * .1 * u + L * .05 * math.sin(u * math.pi)))
        cv.obj([leaf], .5)
        cv.hair(hatch(leaf, 80 * side, 1.5))
    r = s * .2
    if s < 34:                                   # small: a dark cup with a white lip and black heart
        cup = [(hx - r * 1.1, hy - r * .9)] + [(hx - r * 1.1 + r * 2.2 * k / 8, hy - r * .9 - (r * .15 if k % 2 else 0)) for k in range(9)]
        cup += [(hx + r * .9, hy - r * .1), (hx + r * .3, hy + r * .35), (hx - r * .3, hy + r * .35), (hx - r * .9, hy - r * .1)]
        cv.obj([cup], 1.)
        cv.hair(hatch(cup, 90, 1.5))
        cv.hair(hatch(cup, 20, 2))
        heart = C._ell_pts(hx, hy - r * .85, r * .6, r * .18, 12)[:-1]
        cv.obj([heart], 1.)
        cv.heavy(hatch(heart, 0, .9))
        return
    mouth = hy - r * .55
    def petal(cx0, wdt, top, dark):
        pts = [(hx + cx0 - wdt * .25, hy + r * .25)]
        for k in range(9):
            u = k / 8
            px = hx + cx0 - wdt / 2 + wdt * u
            py = top - math.sin(u * math.pi) * r * .25 + (r * .06 if k % 2 else 0)
            pts.append((px, py))
        pts.append((hx + cx0 + wdt * .25, hy + r * .25))
        cv.obj([pts], 1. if dark else .5)
        if dark:
            cv.hair(hatch(pts, 80, 1.5))
            cv.hair(hatch(pts, -10, 2))
        else:
            for k in range(5):
                u = .15 + .7 * k / 4
                cv.hair([(hx + cx0 + (u - .5) * wdt * .35, hy + r * .2), (hx + cx0 + (u - .5) * wdt * .9, top + r * .12)])
            cv.hair(hatch([(hx + cx0 - wdt * .5, hy - r * .1), (hx + cx0 + wdt * .5, hy - r * .1),
                           (hx + cx0 + wdt * .25, hy + r * .25), (hx + cx0 - wdt * .25, hy + r * .25)], 0, 1.5))
    petal(-r * .45, r * 1.3, mouth - r * .45, True)      # far petals, in shadow
    petal(r * .45, r * 1.3, mouth - r * .35, True)
    heart = C._ell_pts(hx, mouth, r * .55, r * .2, 16)[:-1]
    cv.obj([heart], 1.)
    cv.heavy(hatch(heart, 0, .9))
    petal(-r * .55, r * 1.25, mouth - r * .05, False)   # near petals, lit
    petal(r * .55, r * 1.25, mouth + r * .05, False)
    bud = [stem[10], (stem[10][0] - lean * s * .15 - .5 * s * .1, stem[10][1] - s * .12)]
    cv.line(bud)
    b = C._ell_pts(bud[1][0], bud[1][1] + r * .1, r * .22, r * .38, 12)[:-1]
    cv.obj([b], .5)
    cv.hair(hatch(b, 70, 1.5))


def _book(cv, cx, top, W, H, rng, egg=True):
    """An open book on its spine: cover below, page stacks, curved pages ruled with text."""
    hw = W / 2
    sag = H * .14
    def pt(side, t, v):   # side -1 left/+1 right; t 0 spine..1 edge; v 0 top..1 bottom of page
        yy = top + sag * (1 - t) ** 2 * 1.0 - sag * .2 * t + H * v
        xx = cx + side * hw * t * (1 - .04 * v)
        return (xx, yy)
    cover = [(cx - hw - 1.5, top + H * .7), (cx - hw - 2, top + H + 4), (cx, top + H + 7 + sag * .2),
             (cx + hw + 2, top + H + 4), (cx + hw + 1.5, top + H * .7)]
    cv.obj([cover + [(cx, top + H)]], 1.)
    cv.heavy(hatch(cover + [(cx, top + H)], 0, .9))
    for side in (-1, 1):
        # page stack: the block's edge lines under the outer page
        stack = [pt(side, t, 1) for t in [i / 16 for i in range(17)]]
        blk = stack + [(stack[-1][0] + side * 2.5, stack[-1][1] + 4), (cx, top + H + 5)]
        cv.obj([blk], .5)
        for k in range(1, 4):
            cv.hair([(p[0] + side * k * .6, p[1] + k * 1.3) for p in stack[2:]])
        page = [pt(side, t / 20, 0) for t in range(21)] + [pt(side, 1 - t / 20, 1) for t in range(21)]
        cv.obj([page], 1.)
        # text lines (words with gaps), shading near the gutter
        nl = max(3, int(H / 3.2))
        for li in range(nl):
            v = .12 + .78 * li / max(1, nl - 1)
            t = .14
            seg = []
            while t < .88:
                L = rng.uniform(.06, .17)
                t1 = min(.88, t + L)
                if not (li == nl - 1 and t > .5):
                    seg.append([pt(side, tt, v) for tt in (t, (t + t1) / 2, t1)])
                t = t1 + .035
            cv.hair(seg)
        gut = [pt(side, t / 10 * .12, 0) for t in range(11)] + [pt(side, .12 - t / 10 * .12, 1) for t in range(11)]
        cv.hair(hatch(gut, 90, 1.5))
        # page curl shading at the outer edge
        cv.hair([[pt(side, .95, .05), pt(side, .97, .95)]])
    # spine shadow
    cv.line([pt(1, 0, v / 8) for v in range(9)])
    if egg:   # swung eighth-note pair on the right page, among the lines
        v0 = .38
        ax, ay = pt(1, .6, v0 + .3)
        bx, by = pt(1, .76, v0 + .27)
        hh = H * .3
        r = max(1.3, H * .06)
        for (nx, ny) in ((ax, ay), (bx, by)):
            head = C._ell_pts(nx, ny, r * 1.25, r * .85, 12)[:-1]
            cv.obj([head], .5)
            cv.heavy(hatch(head, 0, .9))
            cv.line([(nx + r * 1.1, ny), (nx + r * 1.1, ny - hh)])
        cv.heavy([(ax + r * 1.1, ay - hh), (bx + r * 1.1, by - hh)])


def scene(x, y, w, h, seed, date, clip_d=None, cid="dl"):
    """Fill box x,y,w,h (clipped to clip_d if given) with the whole engraved scene."""
    rng = random.Random(seed * 31 + int(w) * 7 + int(h))
    hy = y + h * .5
    cv = C.Canvas()
    _sky(cv, x, y, w, h, hy + 2, _moon_phase(date))
    _mountains(cv, rng, x, w, hy + h * .04, y + h * .12)
    _forest(cv, rng, x, w, hy + h * .1, min(h * .1, 16))
    _meadow(cv, x, hy + h * .13, w, y + h)
    # book: as large as the box allows, lying in the foreground
    BW = min(w * (.62 if w > h * 1.4 else .82), h * 1.25)
    BH = BW * .3
    btop = y + h - BH - 9 - BW * .04
    _book(cv, x + w / 2, btop, BW, BH, rng)
    # poppies either side, rising from the meadow in front of the book's corners
    ps = max(16, min(h * .36, BH * 1.45))
    for side in (-1, 1):
        for j in range(2 if w > 140 else 1):
            px = x + w / 2 + side * min(BW / 2 - ps * .05 + ps * .28 * j, w * (.36 + .06 * j))
            _poppy(cv, px, y + h + 2, ps * (1 - .25 * j), side * (.2 + .25 * j), seed + j * 7 + side)
    body = cv.svg()
    if clip_d:
        return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'
    return body


# ----------------------------------------------------------------------------------------------
# layouts
# ----------------------------------------------------------------------------------------------

def _band(w, h, seed, date):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.3, 190)
    o.append(C._clip(C._uid("db", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .82, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    outer = C._ell_pts(cx, cy, rx + 1, ry + 1, 72)
    o.append(f'<path d="{_d(outer, True)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{_d(outer, True)}{_d(C._ell_pts(cx, cy, rx - 2, ry - 2, 72)[::-1], True)}" fill="#000" fill-rule="evenodd"/>')
    inner = _d(C._ell_pts(cx, cy, rx - 3.5, ry - 3.5, 72), True)
    o.append(scene(cx - rx, cy - ry, rx * 2, ry * 2, seed, date, inner, C._uid("dv", w, h, seed)))
    o.append(f'<path d="{inner}" fill="none" stroke="#000" stroke-width=".5"/>')
    bp = C._ell_pts(cx, cy, rx - .2, ry - .2, 90)
    o.append(f'<path d="{_d(bp, True)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="0 3.5" stroke-linecap="round"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return C.svg_doc(w, h, "".join(o))


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _seed(ctx)
    date = ctx.get("date", "")
    if h < 110:
        return _band(w, h, seed, date)

    def fill(ix, iy, iw, ih):
        # recover the cartouche field (superellipse) from its inscribed rect and fill it all
        k = 2 ** (-1 / 2.6)
        a, b = iw / 2 / k + 6, ih / 2 / k + 6
        cx, cy = ix + iw / 2, iy + ih / 2
        field = _d(C._superellipse(cx, cy, a - .3, b - .3), True, .1)
        return scene(cx - a, cy - b, 2 * a, 2 * b, seed, date, field, C._uid("dvf", w, h, seed))
    svg = C.frame_plate(w, h, seed, fill, density=.8 if h > 260 else 1.)
    if h > 260:   # the pedestal's sunk tablet carries a shelf of the day's books instead of lettering
        ped_h = min(max(h * .17, 48), 86.)
        _, (tx, ty, tw, th) = C.pedestal(0, h - ped_h, w, ped_h, 0)
        svg = svg[:-6] + _shelf(tx + 2, ty + 2, tw - 3, th - 3, seed) + "</svg>"
    return svg


def _shelf(x, y, w, h, seed):
    """A row of book spines standing in the tablet: ruled cloth, gilt bands, one leaning volume."""
    rng = random.Random(seed * 13 + 5)
    cv = C.Canvas()
    back = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    cv.obj([back], 0)
    cv.hair(C.hatch_poly(back, 0, 1.5))
    xx = x + 2
    k = 0
    while xx < x + w - 6:
        bw = rng.uniform(4, 8.5)
        bh = h * rng.uniform(.72, 1.)
        if k % 9 == 5 and xx + bh * .5 < x + w - 4:   # a leaning book
            lean = bh * .45
            poly = [(xx, y + h), (xx + bw, y + h), (xx + bw + lean, y + h - bh * .9), (xx + lean, y + h - bh * .9)]
            cv.obj([poly], .5)
            cv.hair(C.hatch_poly(poly, 30, 2))
            xx += bw + lean + 1
        else:
            poly = [(xx, y + h - bh), (xx + bw, y + h - bh), (xx + bw, y + h), (xx, y + h)]
            cv.obj([poly], .5)
            tone = k % 3
            if tone == 0:
                cv.hair(C.hatch_poly(poly, 90, 1.5))
            elif tone == 1:
                cv.hair(C.hatch_poly([(xx + bw * .55, y + h - bh), (xx + bw, y + h - bh), (xx + bw, y + h), (xx + bw * .55, y + h)], 90, 1.5))
            else:
                cv.hair(C.hatch_poly(poly, 90, 3))
            for f in (.18, .82):
                yy = y + h - bh + bh * f
                cv.line([(xx + .5, yy), (xx + bw - .5, yy)])
            xx += bw + .8
        k += 1
    cv.line([(x, y + h - .5), (x + w, y + h - .5)])
    return cv.svg()
