"""delights-01 -- Wikipedia Picture of the Day: "Koscielec view 2", the panorama from Koscielec
towards Swinica in the Tatra National Park, on Poland's National Independence Day (11 November).

The vignette is that view, cut in line: ruled sky with drifting cloud, the far Tatra ridge in
flat aerial ruling, the jagged twin summit of Swinica modelled face by face (lit faces in open
fall-line hatch, shadow faces in close hatch and cross-hatch, dark couloirs, first November snow
on the ledges), Czarny Staw Gasienicowy below it in broken water lines, and the dark crags of
Koscielec in the foreground with dwarf-pine tufts. A white-and-red Polish flag flies on the
summit of Swinica for Independence Day. Easter egg: Parker's dog sits on the Koscielec crag
looking out at the view (tall and medium plates). The banner of the tall plate is lettered in
drawn Roman capitals MCMXVIII (1918, the year of independence).
"""
import sys
import math
import random
import engraving_codex as C

_n = C._n


def _lerp(a, b, t):
    return a + (b - a) * t


def _ridge(pts, rng, depth, rough):
    """Midpoint-displace a ridge polyline for crag detail (y displaced, deterministic)."""
    for _ in range(depth):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            out.append(((x0 + x1) / 2 + rng.uniform(-.12, .12) * L, (y0 + y1) / 2 + rng.uniform(-rough, rough) * L))
            out.append((x1, y1))
        pts = out
        rough *= .62
    return pts


def _poly_y_at(pl, x):
    for (x0, y0), (x1, y1) in zip(pl, pl[1:]):
        if x0 <= x <= x1 or x1 <= x <= x0:
            if abs(x1 - x0) < 1e-6:
                return min(y0, y1)
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pl[0][1] if x < pl[0][0] else pl[-1][1]


def _hlines(poly, pitch, phase=.25):
    return C.hatch_poly(poly, 0, pitch, phase)


def _broken(lines, rng, keep=.8, seg=(6, 22)):
    """Break straight lines into dashes (water shimmer)."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = x1 - x0
        t = 0.
        while t < L:
            s = rng.uniform(*seg)
            if rng.random() < keep:
                out.append([(x0 + t, y0), (x0 + min(L, t + s), y1)])
            t += s + rng.uniform(1.5, 5)
    return out


def _dash(lines, rng, on=(5, 16), off=(2, 5), keep=1.):
    """Break 2-point lines into dashes: on/off length ranges in px; keep = share of dashes kept."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 1:
            continue
        t = rng.uniform(0, off[1])
        while t < L:
            s = rng.uniform(*on)
            if rng.random() < keep:
                a, b = t / L, min(L, t + s) / L
                out.append([(_lerp(x0, x1, a), _lerp(y0, y1, a)), (_lerp(x0, x1, b), _lerp(y0, y1, b))])
            t += s + rng.uniform(*off)
    return out


def _dog(x, y, s):
    """Parker's dog sitting in profile, facing right, feet at (x, y), s px tall."""
    P = [(-.40, 0), (-.47, -.1), (-.48, -.22), (-.43, -.34), (-.32, -.43), (-.2, -.52), (-.1, -.62),
         (-.06, -.74), (0, -.84), (.08, -.9), (.18, -.9), (.25, -.85), (.38, -.8), (.45, -.76), (.45, -.71),
         (.36, -.68), (.24, -.66), (.18, -.6), (.2, -.48), (.22, -.36), (.19, -.26), (.18, -.14), (.19, -.03),
         (.27, -.02), (.27, 0), (.08, 0), (.08, -.14), (.02, -.08), (-.12, -.05), (-.1, 0)]
    tail = [(-.42, -.03), (-.56, -.05), (-.62, -.13), (-.58, -.2)]
    ear = [(.02, -.84), (-.08, -.8), (-.12, -.64), (-.06, -.6), (.04, -.72), (.08, -.82)]
    body = [(x + px * s, y + py * s) for px, py in P]
    return body, [(x + px * s, y + py * s) for px, py in tail], [(x + px * s, y + py * s) for px, py in ear]


def _flag(cv, x, y, s):
    """Polish flag on a pole planted at (x, y): white over red (red = close ruling)."""
    top = y - s
    cv.obj([], 0)
    cv.line([(x, y), (x, top - s * .08)])
    fw, fh = s * .62, s * .2
    wave = lambda t: math.sin(t * math.pi * 1.6) * s * .035
    up = [(x + fw * i / 8, top + wave(i / 8)) for i in range(9)]
    mid = [(px, py + fh) for px, py in up]
    lo = [(px, py + 2 * fh) for px, py in up]
    white = up + mid[::-1]
    red = mid + lo[::-1]
    cv.obj([white], .5)
    cv.obj([red], .5)
    cv.hair(C.hatch_poly(red, 45, 1.5))


def _scene(cv, X, Y, W, H, seed, detail):
    """The Swinica panorama laid into box X, Y, W, H (the clip trims it to the field)."""
    rng = random.Random(seed)
    U = lambda u: X + u * W
    V = lambda v: Y + v * H
    box = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]

    # -- sky: closer ruling at the zenith, opening toward the horizon
    cv.obj([box], 0)
    zen = [(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, V(.16)), (X - 2, V(.16))]
    hor = [(X - 2, V(.16)), (X + W + 2, V(.16)), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.hair(_hlines(zen, 2))
    cv.hair(_hlines(hor, 3))
    # sun low in the November south-west sky, behind the left shoulder
    if detail > .4:
        sx, sy, sr = U(.2), V(.24), min(W, H) * .06
        disc = C._ell_pts(sx, sy, sr, sr, 30)[:-1]
        cv.obj([disc], .5)
        cv.hair([[(sx + sr * 1.25 * math.cos(a), sy + sr * 1.25 * math.sin(a)),
                  (sx + sr * (1.7 + .5 * (k % 2)) * math.cos(a), sy + sr * (1.7 + .5 * (k % 2)) * math.sin(a))]
                 for k in range(16) for a in [k * math.pi / 8 + .1]])
        cv.hair(C.hatch_poly(disc, 0, 3, .25 + 1.5)[1::2])
    # clouds: soft white banks with ruled undersides
    if detail > .3:
        for k in range(3 if detail > .7 else 2):
            cx = U(rng.uniform(.35, .95) if k else .72)
            cy = V(rng.uniform(.07, .2))
            cw, ch = W * rng.uniform(.18, .3), max(5., H * .045)
            pts = []
            for i in range(25):
                t = math.pi * i / 24
                bump = 1 + .25 * abs(math.sin(t * 5 + k))
                pts.append((cx - cw / 2 + cw * i / 24, cy - ch * math.sin(t) * bump))
            pts += [(cx + cw / 2 - cw * i / 6, cy + ch * .35 * math.sin(i / 6 * math.pi) * .3) for i in range(7)]
            cv.obj([pts], .5)
            cv.hair(C.hatch_poly(pts, 0, 2, .25)[-3:])

    # -- far ridge (Kozi Wierch / Granaty to the left, Kasprowy side to the right)
    far = _ridge([(X - 4, V(.47)), (U(.1), V(.36)), (U(.24), V(.41)), (U(.38), V(.33)), (U(.8), V(.36)),
                  (U(.9), V(.31)), (X + W + 4, V(.4))], rng, 4, .18)
    farp = far + [(X + W + 4, V(.7)), (X - 4, V(.7))]
    cv.obj([farp], .5)
    cv.hair(_hlines(farp, 1.5))

    # -- Swinica: twin summit, sharp main peak right of centre. Nodes alternate saddle/summit;
    #    each summit drops a spur and each saddle a gully, and the faces between are cut lit
    #    (rising to the right: light from the south-west) or in shadow.
    key = [(X - 6, V(.6), 0), (U(.14), V(.47), 1), (U(.22), V(.5), 0), (U(.36), V(.31), 1),
           (U(.42), V(.35), 0), (U(.5), V(.21), 1), (U(.56), V(.26), 0), (U(.64), V(.12), 1),
           (U(.7), V(.22), 0), (U(.76), V(.27), 1), (U(.84), V(.4), 0), (U(.92), V(.38), 1),
           (X + W + 6, V(.52), 0)]
    base = V(.74)
    hx = U(.64)
    rr = random.Random(seed * 3 + 11)
    segs = []
    ridge = [key[0][:2]]
    for (x0, y0, _), (x1, y1, _) in zip(key, key[1:]):
        s = _ridge([(x0, y0), (x1, y1)], rr, 3 if detail > .5 else 2, .07)
        segs.append(s)
        ridge += s[1:]
    drops = []
    for x, y, kind in key:
        out = (x - hx) * (.32 if kind else .22)
        L = [(x + out * t + (rr.uniform(-1, 1) * 2 if 0 < t < 1 else 0), _lerp(y, base, t)) for t in [j / 8 for j in range(9)]]
        drops.append(_ridge(L, rr, 1, .04))
    mass = ridge + [(X + W + 6, base), (X - 6, base)]
    cv.obj([mass], 1.)
    for i, s in enumerate(segs):
        face = s + drops[i + 1][1:] + drops[i][::-1][:-1]
        lit = key[i + 1][1] < key[i][1]
        dx = drops[i + 1][-1][0] - drops[i + 1][0][0] + drops[i][-1][0] - drops[i][0][0]
        ang = math.degrees(math.atan2(2 * (base - V(.3)), dx))
        ang = max(55., min(125., ang))
        if lit:
            cv.hair(_dash(C.hatch_poly(face, ang, 3, rr.random() * 3), rr, (4, 14), (3, 7), .8))
            if detail > .5:
                # strata: broken contour strokes across the lit rock
                cv.hair(_dash(C.hatch_poly(face, 30 if ang < 90 else 150, 6, rr.random() * 6), rr, (2, 7), (4, 12), .55))
        else:
            cv.hair(C.hatch_poly(face, ang, 1.5, rr.random() * 1.5))
            cv.hair(C.hatch_poly(face, ang + (62 if ang < 90 else -62), 3, .5))
    # crest line, spurs and gullies cut in heavier line
    for i, (x, y, kind) in enumerate(key):
        d = drops[i]
        if kind:
            cv.line(d[:6])
        elif 0 < i < len(key) - 1:
            cv.heavy(d[:5])
    # first November snow lying in the shadowed gullies: white streaks cut through the shading
    if detail > .5:
        sn = random.Random(seed + 5)
        for i, (x, y, kind) in enumerate(key):
            if kind or i in (0, len(key) - 1):
                continue
            d = drops[i]
            for k in range(3):
                t0 = sn.uniform(.08, .5)
                p0 = d[int(t0 * 8)]
                p1 = d[min(8, int(t0 * 8) + 1)]
                off = (k - 1) * 3.5 + 2.5
                L = sn.uniform(.5, 1.)
                q0 = (p0[0] + off, p0[1] + 1)
                q1 = (_lerp(p0[0], p1[0], L) + off, _lerp(p0[1], p1[1], L))
                cv.obj([[q0, (q1[0] - .7, q1[1]), (q1[0] + .7, q1[1] + 1.5), (q0[0] + 1.6, q0[1] + 1)]], 0)
    # talus: scree cones fanning out under every gully, breaking the walls' foot
    tal = random.Random(seed + 77)
    ty = V(.6)
    top = [(X - 6, ty + 4)]
    for i, (x, y, kind) in enumerate(key[1:-1], 1):
        if kind:
            g = drops[i][int(.84 * (len(drops[i]) - 1))]
            top.append((g[0], g[1] + 2 + tal.uniform(0, 3)))
        else:
            g = drops[i][int(.66 * (len(drops[i]) - 1))]
            top.append((g[0], g[1] + tal.uniform(-2, 3)))
    top.append((X + W + 6, ty + 6))
    smooth = []
    for a, b in zip(top, top[1:]):
        for j in range(6):
            t = j / 6
            smooth.append((_lerp(a[0], b[0], t), _lerp(a[1], b[1], t) + math.sin(t * math.pi) * 3))
    smooth.append(top[-1])
    apron = smooth + [(X + W + 6, base + 2), (X - 6, base + 2)]
    cv.obj([apron], .5)
    cv.hair(_dash(C.hatch_poly(apron, 60, 3, .5), tal, (1, 3), (2, 6), .9))
    cv.hair(_dash(C.hatch_poly(apron, 120, 3, 1.5), tal, (1, 2.5), (3, 8), .7))
    # the summit flag for Independence Day
    px, py = U(.64), V(.13)
    _flag(cv, px, py + 1, max(8., H * .1))

    # -- Czarny Staw Gasienicowy in the cirque below
    ly0, ly1 = V(.72), V(.82)
    lake = [(U(.18 + .04 * math.sin(i)), 0) for i in range(0)]
    lake = [(U(.5 + .36 * math.cos(t)), _lerp(ly0, ly1, .5) + (ly1 - ly0) * .5 * math.sin(t))
            for t in [2 * math.pi * i / 40 for i in range(40)]]
    cv.obj([lake], .5)
    wl = _hlines(lake, 1.5)
    cv.hair(_broken(wl, random.Random(seed + 9), .85))
    # moraine slopes framing the lake
    for side in (-1, 1):
        sl = [(U(.5 + side * .62), V(.66)), (U(.5 + side * .3), V(.76)), (U(.5 + side * .25), V(.86)),
              (U(.5 + side * .7), V(.9))]
        cv.obj([sl], .5)
        cv.hair(C.hatch_poly(sl, 45 if side < 0 else 135, 2))

    # -- Koscielec crags in the foreground
    fg_top = [(X - 4, V(.6)), (U(.05), V(.585)), (U(.11), V(.62)), (U(.16), V(.6)), (U(.24), V(.7)),
              (U(.36), V(.82)), (U(.5), V(.9)), (U(.66), V(.88)), (U(.78), V(.84)), (U(.9), V(.8)),
              (X + W + 4, V(.78))]
    fg_top = _ridge(fg_top, random.Random(seed + 21), 2, .06)
    fg = fg_top + [(X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]
    cv.obj([fg], 1.)
    cv.hair(C.hatch_poly(fg, 45, 2))
    bed = random.Random(seed + 41)
    for k in range(1, 40):
        dy = k * 3
        pl = [(x, y + dy + math.sin(x * .05 + k * .7) * 1.5) for x, y in fg_top]
        cv.hair(_dash([[a, b] for a, b in zip(pl, pl[1:])], bed, (3, 12), (1.5, 4), .75))
    cr = random.Random(seed + 33)
    # strata of the crag: the crest line repeated down the slope as broken cracks
    for k in range(1, 8):
        dy = k * 7 + cr.uniform(-2, 2)
        pl = [(x, y + dy + math.sin(x * .07 + k) * 2) for x, y in fg_top]
        segs = []
        for a, b in zip(pl, pl[1:]):
            if cr.random() < .6:
                segs.append([a, b])
        cv.heavy(segs)
    # lit rim along the crest
    rim = [(x, y + 1.5) for x, y in fg_top]
    cv.obj([fg_top + rim[::-1]], 0)
    # dwarf pine (kosodrzewina): dark cushions on the slope, lit on the south-west
    if detail > .4:
        for k in range(int(16 * detail)):
            x = U(cr.uniform(.12, .98))
            y = _poly_y_at(fg_top, x) + cr.uniform(4, 30)
            r = cr.uniform(3, 6)
            bush = [(x + r * 1.5 * math.cos(t) * (1 + .18 * math.sin(5 * t + k)), y + r * .8 * math.sin(t) * (1 + .18 * math.sin(5 * t + k)))
                    for t in [2 * math.pi * j / 18 for j in range(18)]]
            cv.obj([bush], .5)
            cv.hair(C.hatch_poly(bush, 45, 1.5))
            cv.hair(C.hatch_poly(bush, 135, 3, .5))
            cv.obj([[(x - r * 1.1, y - r * .2), (x - r * .3, y - r * .7), (x + r * .1, y - r * .6), (x - r * .6, y)]], 0)
    return fg_top


def _vignette_fn(mode, seed):
    def fill(x, y, w, h):
        cv = C.Canvas()
        if mode == "band":
            k = .7071
            rx, ry = w / 2 / k + 5 - 2.5, h / 2 / k + 5 - 2.5
            cx, cy = x + w / 2, y + h / 2
            field = C._ell_pts(cx, cy, rx, ry, 64)[:-1]
            detail = .3
        else:
            k = 2 ** (-1 / 2.6)
            a, b = w / 2 / k + 6, h / 2 / k + 6
            cx, cy = x + w / 2, y + h / 2
            field = C._superellipse(cx, cy, a - 2, b - 2)
            rx, ry = a - 2, b - 2
            detail = 1. if mode == "tall" else .8
        X, Y, W, H = cx - rx, cy - ry, 2 * rx, 2 * ry
        fg = _scene(cv, X, Y, W, H, seed, detail)
        body = cv.svg()
        extra = ""
        if mode != "band":
            yy = _poly_y_at(fg, X + W * .15)
            t = min(.999, abs(yy - cy) / ry)
            xext = rx * (1 - t ** 2.6) ** (1 / 2.6)
            dx = max(cx - xext + 16, X + W * .06)
            dy = _poly_y_at(fg, dx) + 1.5
            dbody, tail, ear = _dog(dx, dy, max(12., H * .1))
            extra = (f'<path d="{C._d(dbody, True, .05)}" fill="#000" stroke="#fff" stroke-width="1"/>'
                     f'<path d="{C._d(tail, False, .05)}" fill="none" stroke="#000" stroke-width="1.5"/>'
                     f'<path d="{C._d(ear, True, .05)}" fill="#000" stroke="#fff" stroke-width=".5"/>')
        cid = C._uid("tatra", x, y, w, h, mode)
        return (f'<clipPath id="{cid}"><path d="{C._d(field, True, .1)}"/></clipPath>'
                f'<g clip-path="url(#{cid})">{body}{extra}</g>')
    return fill


# --- banner lettering: MCMXVIII drawn as strokes ------------------------------------------------

def _glyph(ch, x, y, s):
    """A Roman capital at (x, baseline y), cap height s. Returns (polylines, advance)."""
    w = s * .78
    if ch == "M":
        return [[(x, y), (x + w * .08, y - s), (x + w * .5, y - s * .1), (x + w * .92, y - s), (x + w, y)]], w * 1.12
    if ch == "C":
        r = s / 2
        return [[(x + r * .9 + r * math.cos(a), y - r + r * math.sin(a))
                 for a in [math.radians(40 + 280 * i / 14) for i in range(15)]]], s * .82
    if ch == "X":
        return [[(x, y - s), (x + w * .8, y)], [(x + w * .8, y - s), (x, y)]], w * 1.0
    if ch == "V":
        return [[(x, y - s), (x + w * .4, y), (x + w * .8, y - s)]], w * 1.0
    if ch == "I":
        return [[(x, y - s), (x, y)]], s * .3
    if ch == "T":
        return [[(x, y - s), (x + w * .8, y - s)], [(x + w * .4, y - s), (x + w * .4, y)]], w * 1.0
    if ch == "A":
        return [[(x, y), (x + w * .42, y - s), (x + w * .84, y)], [(x + w * .18, y - s * .38), (x + w * .66, y - s * .38)]], w * 1.05
    if ch == "R":
        bowl = [(x + w * .4 + w * .32 * math.cos(a), y - s * .74 + s * .26 * math.sin(a))
                for a in [math.radians(-90 + 180 * i / 10) for i in range(11)]]
        return [[(x, y), (x, y - s), (x + w * .4, y - s)] + bowl + [(x, y - s * .48)],
                [(x + w * .36, y - s * .48), (x + w * .76, y)]], w * 1.0
    if ch == "Y":
        return [[(x, y - s), (x + w * .4, y - s * .5), (x + w * .8, y - s)], [(x + w * .4, y - s * .5), (x + w * .4, y)]], w * 1.0
    if ch == ".":
        return [[(x + s * .05, y - s * .5), (x + s * .15, y - s * .6), (x + s * .25, y - s * .5), (x + s * .15, y - s * .4), (x + s * .05, y - s * .5)]], s * .5
    return [], s * .5


def _letter_banner(w, h, seed, density):
    """Recompute where frame_plate's tall layout puts the ribbon and letter it."""
    rng = random.Random(seed)
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    py0 = top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    bh = min(16, ph * .05)
    _, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, 0)
    s = bh * .5
    word = "MCMXVIII"
    adv = [_glyph(c, 0, 0, s)[1] for c in word]
    tot = sum(adv) - (adv[-1] - s * .3)
    x = cx - tot / 2
    lines = []
    n = len(centre) - 1
    x0c, x1c = centre[0][0], centre[-1][0]
    for c, a in zip(word, adv):
        gl, _ = _glyph(c, 0, 0, s)
        mid = x + a / 2
        t = (mid - x0c) / (x1c - x0c) * n
        i = max(0, min(n - 1, int(t)))
        yc = _lerp(centre[i][1], centre[i + 1][1], t - i)
        for pl in gl:
            lines.append([(x + px, yc + s / 2 + py) for px, py in pl])
        x += a
    d = "".join(C._d(pl, False, .05) for pl in lines)
    return f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>'


def _word(word, cx, y, s):
    adv = [_glyph(c, 0, 0, s)[1] for c in word]
    x = cx - (sum(adv) - adv[-1] * .6) / 2
    out = []
    for c, a in zip(word, adv):
        out += _glyph(c, x, y, s)[0]
        x += a
    return out


def _letter_tablet(w, h, seed, density):
    """Engrave the pedestal's tablet: ruled ground and TATRY . XI . XI (the Tatras, 11 November)."""
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    ph = h - top_free - ped_h - frieze + ped_h * .3
    py = top_free + ph - ped_h * .3 + 4 if frieze else h - ped_h
    _, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, 0)
    ix, iy, iw, ih = tx + 2, ty + 2, tw - 3, th - 3
    o = [f'<path d="M{_n(ix)},{_n(iy)}h{_n(iw)}v{_n(ih)}h{_n(-iw)}z" fill="{C.pat("S")}" stroke="none"/>']
    s = min(ih * .66, 12)
    pl = _word("TATRY  .  XI  .  XI", w / 2, iy + ih / 2 + s / 2, s)
    halo = "".join(C._d(p, False, .05) for p in pl)
    o.append(f'<path d="{halo}" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>')
    o.append(f'<path d="{halo}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def plate(w, h, ctx):
    date = (ctx or {}).get("date", "")
    seed = sum(map(ord, date)) or 7
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    density = .85 if mode == "tall" else 1.
    svg = C.frame_plate(w, h, seed, _vignette_fn(mode, seed), density=density)
    if mode == "tall":
        svg = svg[:-6] + _letter_banner(w, h, seed, density) + _letter_tablet(w, h, seed, density) + svg[-6:]
    return svg
