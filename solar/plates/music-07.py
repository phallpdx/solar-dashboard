"""music-07 "Meet a local artist": the house Codex frame round a bespoke vignette of today's artist.

Today (and whenever the page names a writer): an open book lies on a ruled table, its pages set
with engraved lines of type, a combination wrench crossing behind it and a toothed gear rising like
a sun over the horizon (Palahniuk wrote Fight Club while working as a diesel mechanic).
The subject follows the page text: a writer gets the book, a musician a record, anyone else a
painter's palette; "mechanic"/"diesel" adds the wrench and gear sun.
Tall plates letter the artist's name on the ribbon and LOCAL ARTIST OF THE DAY on the pedestal
tablet, drawn as engraved paths.
Easter egg: Parker's crossed drumsticks lie on the table beside the book.
"""
import sys
import math
import random
import re
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI, TAU = math.pi, 2 * math.pi


# ----------------------------------------------------------------------------------------------
# the page's subject
# ----------------------------------------------------------------------------------------------

def _subject(ctx):
    s = ((ctx or {}).get("sample") or "")
    low = s.lower()
    if re.search(r"novel|book|writer|author|poet|essay|memoir", low):
        kind = "book"
    elif re.search(r"band|music|song|singer|jazz|drum|album|record|guitar|rapper|composer", low):
        kind = "record"
    else:
        kind = "palette"
    mech = bool(re.search(r"mechanic|diesel|engine|machin|welder", low))
    name = ""
    m = re.search(r"Of the day\s+(.*)", s)
    if m:
        words = []
        for wd in m.group(1).split():
            if wd[:1].isupper() or wd in ("&", "de", "van", "von"):
                words.append(wd)
            else:
                break
        name = " ".join(words[:4])
    name = "".join(ch for ch in name.upper() if ch in _G or ch == " ")
    return kind, mech, name.strip()


# ----------------------------------------------------------------------------------------------
# a little stroke alphabet for engraved lettering (glyphs on a 4 x 6 grid, y down)
# ----------------------------------------------------------------------------------------------

_G = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 6), (0, 0), (2.8, 0), (3.6, .8), (3.6, 2.2), (2.8, 3), (0, 3)], [(2.8, 3), (3.8, 3.8), (3.8, 5.2), (3, 6), (0, 6)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.6, 6), (4, 4.6), (4, 1.4), (2.6, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (2.8, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (2.8, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.4), (2.4, 3.4)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.3, 2.6), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3.6), (4, 0), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)], [(2.4, 4.4), (4.2, 6.4)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.2), (3, 3.2), (0, 3.2)], [(2, 3.2), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1, 6), (2, 2.4), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "&": [[(4, 6), (1, 2), (1, .8), (2, 0), (3, .8), (3, 1.6), (0, 4), (0, 5), (1, 6), (2.6, 6), (4, 3.6)]],
    ".": [[(1.8, 5.6), (2.2, 6)]],
    "-": [[(1, 3), (3, 3)]],
    "'": [[(2, 0), (1.6, 1.6)]],
}


def _letters(text, cx, cy, cap, centre=None):
    """Polylines spelling text centred on (cx, cy), cap px tall; centre: an optional list of
    points (a ribbon's centre line) to bend the baseline along. Returns (polylines, width)."""
    k = cap / 6
    adv = [(2.6 if ch == " " else 4) + 2.2 for ch in text]
    W = (sum(adv) - 2.2) * k
    x = cx - W / 2
    out = []

    def yoff(px):
        if not centre:
            return 0.
        for i in range(1, len(centre)):
            if centre[i][0] >= px:
                a, b = centre[i - 1], centre[i]
                t = (px - a[0]) / ((b[0] - a[0]) or 1)
                return a[1] + (b[1] - a[1]) * t - cy
        return centre[-1][1] - cy

    for ch, a in zip(text, adv):
        for st in _G.get(ch, []):
            out.append([(x + px * k, cy - cap / 2 + py * k + yoff(x + px * k)) for px, py in st])
        x += a * k
    return out, W


def _lettering(text, cx, cy, cap, centre=None, sw=1.):
    pl, W = _letters(text, cx, cy, cap, centre=centre)
    d = "".join(_d(p, tol=0) for p in pl)
    return (f'<path d="{d}" stroke="#fff" stroke-width="{_n(sw + 2)}"/>'
            f'<path d="{d}" stroke="#000" stroke-width="{_n(sw)}"/>'), W


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


# ----------------------------------------------------------------------------------------------
# the vignette pieces (all draw into Canvases; later canvases paint over earlier ones)
# ----------------------------------------------------------------------------------------------

def _gear_sun(cv, cx, cy, R, teeth):
    """A toothed gear half-risen over the horizon: turned rings on its face, shaded tooth flanks,
    a black hub and bolt holes."""
    pts = []
    n = teeth * 4
    for i in range(n + 1):
        a = PI + PI * i / n
        r = R if (i % 4) in (1, 2) else R * .86
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    poly = pts + [(cx + R * .86, cy + 1), (cx - R * .86, cy + 1)]
    cv.obj([poly], 1.)
    r = R * .8
    while r > R * .22:
        cv.hair(_ell(cx, cy, r, r, 48, PI, TAU))
        r -= 1.5 if r < R * .45 else 3.
    cv.line(_ell(cx, cy, R * .82, R * .82, 48, PI, TAU))
    for i in range(teeth):
        a0 = PI + PI * (4 * i + 1) / n
        a1 = PI + PI * (4 * i + 2) / n
        p0 = (cx + R * math.cos(a0), cy + R * math.sin(a0))
        p1 = (cx + R * math.cos(a1), cy + R * math.sin(a1))
        q0 = (cx + R * .86 * math.cos(a0), cy + R * .86 * math.sin(a0))
        q1 = (cx + R * .86 * math.cos(a1), cy + R * .86 * math.sin(a1))
        cv.hair(C.hatch_poly([q0, p0, p1, q1], math.degrees((a0 + a1) / 2) + 90, 1.5))
    hub = _ell(cx, cy, R * .2, R * .2, 24, PI, TAU) + [(cx + R * .2, cy + 1), (cx - R * .2, cy + 1)]
    cv.obj([hub], 1.)
    cv.line(C.hatch_poly(hub, 0, .8))


def _rays(cv, cx, cy, R0, x0, y0, x1, y1, n=28):
    """Ray wedges, each hatched across, radiating over the ruled sky."""
    far = max(x1 - x0, y1 - y0) * 1.5
    for i in range(0, n, 2):
        a = PI + PI * (i + .5) / n
        da = PI / n * .5
        wdg = [(cx + R0 * math.cos(a - da * .3), cy + R0 * math.sin(a - da * .3)),
               (cx + far * math.cos(a - da), cy + far * math.sin(a - da)),
               (cx + far * math.cos(a + da), cy + far * math.sin(a + da)),
               (cx + R0 * math.cos(a + da * .3), cy + R0 * math.sin(a + da * .3))]
        cv.obj([wdg], 0)
        cv.hair(C.hatch_poly(wdg, math.degrees(a) + 90, 1.5))


def _wrench(cv, p0, p1, wd):
    """A combination wrench from p0 (open jaw) to p1 (ring end), steel shaded along its length."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    R = wd * 1.3

    def at(t, s):
        hw = wd / 2 * (1 - .2 * math.sin(PI * t)) * s
        return (p0[0] + dx * t + nx * hw, p0[1] + dy * t + ny * hw)

    T = [k / 24 for k in range(25)]
    sh = [at(t, 1) for t in T] + [at(t, -1) for t in T[::-1]]
    sw = R * .9
    a1 = math.asin(min(.95, sw / 2 / R))
    base = math.atan2(-uy, -ux)
    jaw = [(p0[0] + R * math.cos(base + a1 + (TAU - 2 * a1) * i / 28),
            p0[1] + R * math.sin(base + a1 + (TAU - 2 * a1) * i / 28)) for i in range(29)]
    c0 = (p0[0] - ux * R * .1, p0[1] - uy * R * .1)
    jaw += [(c0[0] - nx * sw / 2, c0[1] - ny * sw / 2), (c0[0] + nx * sw / 2, c0[1] + ny * sw / 2)]
    ring = _ell(p1[0], p1[1], R * .95, R * .95, 32)
    cv.obj([sh], 1.)
    for s in (.55, .2, -.15):
        cv.hair([at(t, s) for t in T[2:23]])
    for s in (-.45, -.7):
        cv.line([at(t, s) for t in T[2:23]])
    for P, poly, rad in ((p0, jaw, R), (p1, ring, R * .95)):
        cv.obj([poly], 1.)
        for rr in (.82, .66):
            cv.hair([(P[0] + rad * rr * math.cos(a), P[1] + rad * rr * math.sin(a))
                     for a in [base + .85 + (PI * .95 - .85) * k / 14 for k in range(15)]])
        cv.line([(P[0] + rad * .9 * math.cos(a), P[1] + rad * .9 * math.sin(a))
                 for a in [base + PI * 1.1 + PI * .6 * k / 12 for k in range(13)]])
    hexp = [(p1[0] + R * .5 * math.cos(a), p1[1] + R * .5 * math.sin(a)) for a in [TAU * k / 6 + .3 for k in range(6)]]
    cv.obj([hexp], 1.)
    cv.line(C.hatch_poly(hexp, 0, .8))


def _pen(cv, p0, p1, wd):
    """A fountain pen from p0 (nib) to p1 (cap end): turned barrel shaded along its length, a
    cap band, the clip, and a split steel nib."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux

    def at(t, s, hw):
        return (p0[0] + dx * t + nx * hw * s, p0[1] + dy * t + ny * hw * s)

    nib_t = .16
    nib = [at(0, 0, 0), at(nib_t, 1, wd * .42), at(nib_t + .02, 0, 0), at(nib_t, -1, wd * .42)]
    T = [nib_t + (1 - nib_t) * k / 20 for k in range(21)]

    def hw(t):
        return wd / 2 * (.72 + .28 * min(1, (t - nib_t) / .12)) * (1 - .15 * max(0, t - .85) / .15)

    body = [at(t, 1, hw(t)) for t in T] + [at(t, -1, hw(t)) for t in T[::-1]]
    cv.obj([nib], 1.)
    cv.hair(C.hatch_poly(nib, math.degrees(math.atan2(uy, ux)) + 90, 1.5))
    cv.line([at(.02, 0, 0), at(nib_t - .02, 0, 0)])
    cv.obj([body], 1.)
    for sv in (.5, .15):
        cv.hair([at(t, sv, hw(t)) for t in T[1:-1]])
    for sv in (-.4, -.65):
        cv.line([at(t, sv, hw(t)) for t in T[1:-1]])
    for tb in (.56, .6):
        cv.line([at(tb, 1, hw(tb)), at(tb, -1, hw(tb))])
    clip = [at(.62, .55, hw(.62)), at(.95, .55, hw(.95)), at(.95, .2, hw(.95)), at(.66, .2, hw(.66))]
    cv.obj([clip], 1.)
    cv.hair(C.hatch_poly(clip, math.degrees(math.atan2(uy, ux)), 1.5))


def _mt_hood(cv, x, base, w, h):
    """Mt. Hood on the horizon: a snow-capped cone, lit flank ruled lightly, shadow flank dark."""
    pk = (x + w * .48, base - h)
    pts = [(x, base + 1), (x + w * .2, base - h * .3), (x + w * .36, base - h * .72), pk,
           (x + w * .6, base - h * .76), (x + w * .78, base - h * .32), (x + w, base + 1)]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, 0, 2.))
    shade = [pk, (x + w * .6, base - h * .76), (x + w * .78, base - h * .32), (x + w, base + 1), (x + w * .55, base + 1)]
    cv.line(C.hatch_poly(shade, 0, 1.5))
    snow = [(x + w * .36, base - h * .72), pk, (x + w * .6, base - h * .76), (x + w * .52, base - h * .66),
            (x + w * .46, base - h * .74), (x + w * .41, base - h * .64)]
    cv.obj([snow], 1.)


def _nut(cv, cx, cy, r):
    """A hex nut lying on the table: shaded flats, a lit top face, a black bore."""
    top = [(cx + r * math.cos(a), cy - r * .45 + r * .45 * math.sin(a)) for a in [TAU * k / 6 for k in range(6)]]
    body = [(cx - r, cy - r * .45), (cx - r, cy + r * .05), (cx - r * .5, cy + r * .44), (cx + r * .5, cy + r * .44),
            (cx + r, cy + r * .05), (cx + r, cy - r * .45)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly(body, 90, 1.5))
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 0, 3, 1))
    hole = _ell(cx, cy - r * .45, r * .42, r * .2, 16)
    cv.obj([hole], 1.)
    cv.line(C.hatch_poly(hole, 0, .8))


def _drumsticks(cv, cx, cy, L):
    """Parker's crossed drumsticks (the Easter egg): tapered sticks with turned bead tips."""
    for s in (-1, 1):
        a = s * .5
        ux, uy = math.cos(a), math.sin(a) * .75
        ul = math.hypot(ux, uy)
        ux, uy = ux / ul, uy / ul
        nx, ny = -uy, ux
        p0 = (cx - ux * L / 2, cy - uy * L / 2)
        pl, pr = [], []
        for i in range(13):
            t = i / 12
            hw = max(.8, L * .04 * (1 - .6 * t ** 1.5))
            px, py = p0[0] + ux * L * t, p0[1] + uy * L * t
            pl.append((px + nx * hw, py + ny * hw))
            pr.append((px - nx * hw, py - ny * hw))
        cv.obj([pl + pr[::-1]], 1.)
        cv.hair([_lerp(a_, b_, .7) for a_, b_ in zip(pl, pr)][:11])
        tip = (p0[0] + ux * L * 1.04, p0[1] + uy * L * 1.04)
        bead = _ell(tip[0], tip[1], L * .05 + .6, L * .04 + .5, 12)
        cv.obj([bead], 1.)
        cv.hair(C.hatch_poly(bead, 30, 1.5))


def _book(cv, cx, by, B, rng):
    """An open book on the table: black boards, page blocks with stacked fore-edges, curving pages
    set with lines of engraved type (chapter head, drop cap), a shadowed gutter, a ribbon marker."""
    lift = B * .13
    ph = B * .34
    dep = max(3., B * .05)

    def cur(u):
        return math.sin(PI * .75 * min(max(u, 0), 1)) ** .6

    def top(u):
        return by - ph - lift * cur(u)

    def bot(u):
        return by - lift * .55 * cur(u)

    def pt(s, u, v):
        return (cx + s * B / 2 * u, top(u) * (1 - v) + bot(u) * v)

    U = [k / 30 for k in range(31)]
    for s in (-1, 1):
        ex = B / 2 + max(2., B * .025)
        cov = ([(cx, by + dep * .2 + 3)] + [(cx + s * ex * u, bot(u) + dep * u + 3) for u in U[1:]] +
               [(cx + s * ex, top(1) + 2)] + [(cx + s * ex * u, top(u) + 2) for u in U[::-1]])
        cv.obj([cov], 1.)
        cv.line(C.hatch_poly(cov, 0, .8))
    nl = max(4, int(ph / 3.))
    for s in (-1, 1):
        blk = ([(cx + s * B / 2 * u, bot(u) + dep * u) for u in U] +
               [(cx + s * B / 2, top(1) + dep * .3)] + [(cx + s * B / 2 * u, top(u)) for u in U[::-1]])
        cv.obj([blk], 1.)
        k = 1.
        while k < dep - .4:
            cv.hair([(cx + s * B / 2 * u, bot(u) + k * u) for u in U[3:]])
            k += 1.5
        page = [pt(s, u, 1) for u in U] + [pt(s, u, 0) for u in U[::-1]]
        cv.obj([page], 1.)
        V = [m / 16 for m in range(17)]
        gw = [pt(s, 0, 0), pt(s, .025, 0), pt(s, .025, 1), pt(s, 0, 1)]
        cv.line(C.hatch_poly(gw, 90, .8))
        for j, uu in enumerate([.035, .05, .068, .09, .115, .145, .18, .22]):
            (cv.line if j < 3 else cv.hair)([pt(s, uu, v) for v in V])
        for uu in (.955, .98):
            cv.hair([pt(s, uu, v) for v in V])
        for li in range(nl):
            v = (li + 1.2) / (nl + .8)
            if s < 0 and li < 2:
                if li == 1:
                    cv.line([pt(s, u, v) for u in [.36 + .38 * m / 10 for m in range(11)]])
                continue
            if s > 0 and li == nl - 1:
                continue
            u = .34 if (s < 0 and li in (2, 3)) else .22
            uend = .9 if li % 6 != 5 else .58
            while u < uend:
                u1 = min(uend, u + rng.uniform(.04, .15))
                cv.hair([pt(s, uu, v) for uu in [u + (u1 - u) * m / 4 for m in range(5)]])
                u = u1 + .024
        if s < 0:
            v0, v1 = 2.6 / (nl + .8), 4.4 / (nl + .8)
            dcp = [pt(s, .3, v0), pt(s, .22, v0), pt(s, .22, v1), pt(s, .3, v1)]
            cv.obj([dcp], 1.)
            cv.line(C.hatch_poly(dcp, 0, .8))
    cv.line([(cx, by - ph), (cx, by + 1)])


def _record(cv, cx, cy, R):
    """A long-player lying on the table: grooves of fine rings with a lit sector, label, spindle."""
    ry = R * .42
    cv.obj([_ell(cx, cy, R, ry, 64)], 1.)
    r = R * .97
    while r > R * .38:
        cv.hair(_ell(cx, cy, r, r * .42, 64, PI * 1.25, PI * 2.95))
        r -= 1.5
    lab = _ell(cx, cy, R * .36, ry * .36, 32)
    cv.obj([lab], 1.)
    cv.hair(C.hatch_poly(lab, 0, 2))
    sp = _ell(cx, cy, 1.8, 1.1, 10)
    cv.obj([sp], 1.)
    cv.line(C.hatch_poly(sp, 0, .8))


def _palette(cv, cx, cy, R):
    pts = [(cx + R * (1 + .08 * math.sin(3 * a)) * math.cos(a), cy + R * .5 * (1 + .08 * math.sin(3 * a)) * math.sin(a))
           for a in [TAU * i / 48 for i in range(48)]]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, -20, 3))
    hole = _ell(cx + R * .45, cy + R * .1, R * .14, R * .08, 16)
    cv.obj([hole], 1.)
    cv.line(C.hatch_poly(hole, 0, .8))
    for k in range(6):
        a = PI * 1.05 + PI * .85 * k / 5
        b = _ell(cx + R * .7 * math.cos(a), cy + R * .35 * math.sin(a), R * .09, R * .055, 12)
        cv.obj([b], 1.)
        cv.hair(C.hatch_poly(b, 45 * (k % 3), [1.5, 2, 3][k % 3]))


def _scene(fx, fy, fw, fh, clip_d, ctx, seed, big):
    """The engraved vignette filling the field bbox (fx, fy, fw, fh), clipped to clip_d."""
    kind, mech, _ = _subject(ctx)
    rng = random.Random(seed)
    cx = fx + fw / 2
    hor = fy + fh * (.5 if big else .56)
    o = [f'<path d="M{_n(fx)},{_n(fy)}h{_n(fw)}v{_n(hor - fy + 1)}h{_n(-fw)}z" fill="{C.pat("L")}" stroke="none"/>']
    cvb = C.Canvas()
    B = min(fw * (.8 if big else .6), fh * 1.2)
    by = hor + (fy + fh - hor) * (.5 if big else .42)
    R = min(fw * .3, (hor - fy) * .95)
    _rays(cvb, cx, hor, R * 1.06, fx, fy, fx + fw, hor, 30 if big else 22)
    if mech:
        _gear_sun(cvb, cx, hor, R, 11 if big else 8)
    else:
        disc = _ell(cx, hor, R * .8, R * .8, 40, PI, TAU) + [(cx + R * .8, hor + 1), (cx - R * .8, hor + 1)]
        cvb.obj([disc], 1.)
        cvb.hair(C.hatch_poly(disc, 0, 2))
    mh = (hor - fy) * (.34 if big else .3)
    _mt_hood(cvb, fx + fw * .02, hor, fw * .3, mh)
    hills = [(fx + fw * .62, hor + 1)] + [(fx + fw * (.62 + .4 * t / 20), hor - mh * .28 * math.sin(PI * t / 20) ** .7 - mh * .08 * math.sin(t))
                                          for t in range(21)] + [(fx + fw + 2, hor + 1)]
    cvb.obj([hills], 1.)
    cvb.hair(C.hatch_poly(hills, 0, 1.5))
    tab = [(fx - 2, hor), (fx + fw + 2, hor), (fx + fw + 2, fy + fh + 2), (fx - 2, fy + fh + 2)]
    cvb.obj([tab], 1.)
    cvb.hair(C.hatch_poly(tab, 0, 2., .5))
    for k in range(-11, 12):
        cvb.hair([(cx + k * fw * .045, hor), (cx + k * fw * .16, fy + fh + 2)])
    o.append(cvb.svg())
    cv = C.Canvas()
    if kind == "book":
        sh = [(cx - B * .56, by + B * .03), (cx + B * .56, by + B * .03), (cx + B * .66, by + B * .11), (cx - B * .46, by + B * .12)]
        cv.obj([sh], 0)
        cv.line(C.hatch_poly(sh, 0, 1.5))
        _book(cv, cx, by, B, rng)
        # the writer's pen lying across the right-hand page
        pg = by - B * .34 * .5 - B * .13 * .6
        _pen(cv, (cx + B * .1, pg + B * .1), (cx + B * .46, pg - B * .1), max(3.5, B * .055))
        if mech:
            # the mechanic's wrench lying on the table in front
            wy = by + (fy + fh - by) * .42
            _wrench(cv, (cx - B * .5, wy + B * .03), (cx + B * .02, wy - B * .01), max(3.5, B * .055))
    elif kind == "record":
        _record(cv, cx, by - B * .05, B * .45)
    else:
        _palette(cv, cx, by - B * .02, B * .42)
        if mech:
            _wrench(cv, (cx - B * .55, by + B * .1), (cx + B * .55, by - B * .15), max(3., B * .05))
    # Easter egg: Parker's crossed drumsticks lying on the table in front, right of centre
    L = max(16., B * .27)
    _drumsticks(cv, cx + B * .34, by + (fy + fh - by) * .45, L)
    o.append(cv.svg())
    cid = C._uid("v", fx, fy, fw, fh, seed)
    return f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath><g clip-path="url(#{cid})">{"".join(o)}</g>'


# ----------------------------------------------------------------------------------------------
# layouts (the house frames, with the whole cartouche field handed to the vignette)
# ----------------------------------------------------------------------------------------------

def _bead_ring(cx, cy, a, b):
    bp = C._superellipse(cx, cy, a, b)
    d = _d(bp + [bp[0]], tol=.15)
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1.5" stroke-dasharray="0 4.5" stroke-linecap="round"/>')


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 2.2, 160)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    clip = _d(_ell(cx, cy, rx - 4.5, ry - 4.5, 64), True)
    o.append(_scene(cx - rx + 4, cy - ry + 4, 2 * rx - 8, 2 * ry - 8, clip, ctx, seed, False))
    o.append(f'<path d="{_d(_ell(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, ctx):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.7)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=10, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed, h > 200))
    o.append(_bead_ring(cx, cy, a - 3.2, b - 3.2))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, ctx):
    rng = random.Random(seed)
    _, _, name = _subject(ctx)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .6
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=7, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, inner, ctx, seed, True))
    o.append(_bead_ring(cx, cy, a - 3.2, b - 3.2))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(18, ph * .055)
    bcy = cy + ch * .47
    bsvg, centre = C.ribbon_banner(cx, bcy, cw * 1.45, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    if name:
        cap = bh * .5
        lim = cw * 1.45 * .64
        _, W = _letters(name, cx, bcy, cap)
        if W > lim:
            cap *= lim / W
        o.append(_lettering(name, cx, bcy, cap, centre=centre, sw=1.)[0])
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(f'<path d="M{_n(tx + 2.5)},{_n(ty + 2.5)}h{_n(tw - 4)}v{_n(th - 4)}h{_n(-tw + 4)}z" fill="{C.pat("L")}" stroke="none"/>')
    cap = min(th * .5, 11)
    _, W = _letters("LOCAL ARTIST OF THE DAY", 0, 0, cap)
    if W > tw * .8:
        cap *= tw * .8 / W
    t, W = _lettering("LOCAL ARTIST OF THE DAY", w / 2, ty + th / 2 + .8, cap, sw=1.5 if cap > 8 else 1.)
    o.append(t)
    for sx in (-1, 1):
        x = w / 2 + sx * (W / 2 + cap * .9)
        o.append(f'<path d="{_d(_ell(x, ty + th / 2 + .8, cap * .2, cap * .2, 12), True)}" fill="#000"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed, ctx)
    elif h <= 260:
        body = _layout_medium(w, h, seed, ctx)
    else:
        body = _layout_tall(w, h, seed, ctx)
    return C.svg_doc(w, h, body)
