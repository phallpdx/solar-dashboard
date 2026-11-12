"""music-04 'New music out' (new albums: Shygirl 'Swallow!', Steven Wilson 'Requiem for a Village',
QOTSA, Kiwanuka ...). The vignette: a new LP sliding from its sleeve and rising like a sun over a
little village (Requiem for a Village) under a sunburst; the sleeve carries an engraved swallow
(Swallow!). The ribbon banner carries a bar of swing rhythm in place of lettering, the pedestal
tablet a sound-wave cut fresh from the date. Easter eggs: Parker's 'P' on the record label and a
pair of crossed drumsticks behind the cartouche, their bead tips breaking into the scrollwork."""
import sys
import math
import random
import engraving_codex as C

_n, _d, _CR = C._n, C._d, C._CR
PI, TAU = math.pi, 2 * math.pi


# ------------------------------------------------------------------------------------------
# small geometry
# ------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=None):
    n = n or max(24, int(r * 1.2))
    return C._ell_pts(cx, cy, r, r, n)[:-1]


def _arc(cx, cy, r, a0, a1):
    n = max(3, int(abs(a1 - a0) * r / 2.5))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _rot(pts, cx, cy, s, ang, flip=False):
    c, si = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        if flip:
            x = -x
        out.append((cx + s * (x * c - y * si), cy + s * (x * si + y * c)))
    return out


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", "") + "music-04"))


# ------------------------------------------------------------------------------------------
# the subject
# ------------------------------------------------------------------------------------------

def _sunburst(cv, cx, cy, box, n=36):
    """Alternating dark and light rays from (cx, cy) filling box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    R = math.hypot(max(cx - x0, x1 - cx), max(cy - y0, y1 - cy)) + 4
    cv.obj([[(x0 - 2, y0 - 2), (x1 + 2, y0 - 2), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]], 0)
    for i in range(n):
        a0, a1 = TAU * i / n, TAU * (i + 1) / n
        am = (a0 + a1) / 2
        wedge = [(cx, cy)] + _arc(cx, cy, R, a0, a1)
        if i % 2:
            cv.hair(C.hatch_poly(wedge, math.degrees(am), 1.5))
        else:
            cv.hair(C.hatch_poly(wedge, math.degrees(am), 3., inset=1.))


def _village(cv, x0, x1, base, gh, seed):
    """A dark skyline: rolling ground, cottages and a church with a steeple (Requiem for a Village)."""
    rng = random.Random(seed)
    W = x1 - x0
    pts = [(x0 - 2, base + 4)]
    x = x0 - 2
    steeple_at = x0 + W * rng.uniform(.2, .32)
    done = False
    while x < x1 + 2:
        if not done and x > steeple_at:
            # the church: nave, tower, spire
            nw, nh = gh * .9, gh * .55
            pts += [(x, base - gh * .25), (x, base - gh * .25 - nh), (x + nw * .5, base - gh * .25 - nh * 1.5),
                    (x + nw, base - gh * .25 - nh)]
            tx = x + nw
            pts += [(tx, base - gh * 1.4), (tx + gh * .18, base - gh * 2.6), (tx + gh * .36, base - gh * 1.4),
                    (tx + gh * .36, base - gh * .25)]
            x = tx + gh * .36 + 2
            done = True
            continue
        hw = rng.uniform(.5, .9) * gh
        hh = rng.uniform(.35, .6) * gh
        gy = base - gh * (.12 + .14 * math.sin((x - x0) / W * 5.3 + seed % 7))
        pts += [(x, gy), (x, gy - hh), (x + hw / 2, gy - hh - hw * .45), (x + hw, gy - hh), (x + hw, gy)]
        x += hw + rng.uniform(1.5, gh * .5)
    pts += [(x1 + 2, base + 4)]
    pts += [(x1 + 2, base + gh * 3), (x0 - 2, base + gh * 3)]
    cv.obj([pts], 1.)
    cv.hair(C.hatch_poly(pts, 0, 1.5))
    cv.hair(C.hatch_poly(pts, 90, 3))
    cv.hair(C.hatch_poly([(x0 - 2, base + 1), (x1 + 2, base + 1), (x1 + 2, base + gh * 3), (x0 - 2, base + gh * 3)], 90, 3))


_SW_R = [(0, -1.0), (.09, -.9), (.12, -.62), (.5, -.66), (.92, -.56), (1.3, -.3), (.88, -.4), (.5, -.33),
         (.15, -.2), (.13, .1), (.42, .8), (.09, .32), (0, .27)]
_SWALLOW = _SW_R + [(-x, y) for x, y in _SW_R[::-1][1:-1]]


def _swallow(cv, cx, cy, s, ang):
    """A barn swallow seen from above, wings swept, tail forked."""
    p = _rot(_SWALLOW, cx, cy, s, ang)
    cv.obj([p], 1.)
    for side in (-1, 1):
        wing = _rot([(side * .12, -.62), (side * .5, -.66), (side * .92, -.56), (side * 1.3, -.3),
                     (side * .88, -.4), (side * .5, -.33), (side * .15, -.2)], cx, cy, s, ang)
        cv.hair(C.hatch_poly(wing, math.degrees(ang) - side * 12, 1.5))
        cv.hair(C.hatch_poly(wing, math.degrees(ang) + 90 - side * 30, 3))
        for k in range(4):     # primaries
            f = .35 + k * .2
            cv.hair(_rot([(side * f, -.62 + .02 * k), (side * (f + .25), -.42 + .03 * k)], cx, cy, s, ang))
    body = _rot([(0, -1.0), (.12, -.62), (.15, -.2), (.13, .1), (0, .27), (-.13, .1), (-.15, -.2), (-.12, -.62)], cx, cy, s, ang)
    cv.line(C.hatch_poly(body, math.degrees(ang) + 90, 1.5))
    for side in (-1, 1):
        tail = _rot([(side * .13, .1), (side * .42, .8), (side * .09, .32)], cx, cy, s, ang)
        cv.hair(C.hatch_poly(tail, math.degrees(ang) + 90 - side * 20, 1.5))
    throat = _rot([(-.07, -.78), (.07, -.78), (.09, -.55), (-.09, -.55)], cx, cy, s, ang)
    cv.obj([throat], 0)
    cv.hair(C.hatch_poly(throat, math.degrees(ang), 3))


def _sleeve(cv, cx, cy, S, ang, seed):
    half = S / 2
    sq = lambda k: _rot([(-k, -k), (k, -k), (k, k), (-k, k)], cx, cy, 1, ang)
    cv.obj([sq(half)], 1.5)
    inner = sq(half - 4)
    cv.hair(C.hatch_poly(sq(half), math.degrees(ang) + 90, 3))       # card grain on the border
    cv.obj([inner], 1.)
    cv.hair(C.hatch_poly(inner, math.degrees(ang) + 45, 2))
    cv.hair(C.hatch_poly(inner, math.degrees(ang) - 45, 3))
    # a pale moon behind the bird
    mx, my = _rot([(-.17 * S, -.05 * S)], cx, cy, 1, ang)[0]
    m = _circ(mx, my, S * .24)
    cv.obj([m], .5)
    cv.hair(C.hatch_poly(m, math.degrees(ang), 3))
    bx, by = _rot([(-.18 * S, .02 * S)], cx, cy, 1, ang)[0]
    _swallow(cv, bx, by, S * .34, ang - .45)


def _p_monogram(cx, cy, r):
    """A script 'P' (polylines in a radius-r box)."""
    stem = [(cx - .2 * r, cy - .55 * r), (cx - .22 * r, cy + .2 * r), (cx - .3 * r, cy + .6 * r),
            (cx - .5 * r, cy + .7 * r)]
    bowl = [(cx - .55 * r, cy - .35 * r)] + [
        (cx + .05 * r + .38 * r * math.cos(t), cy - .25 * r + .32 * r * math.sin(t))
        for t in [-PI * .95 + PI * 1.95 * i / 16 for i in range(17)]]
    return [stem, bowl]


def _record(cv, cx, cy, R, seed):
    disc = _circ(cx, cy, R, 96)
    cv.obj([disc], 1.5)
    rl = R * .34
    rng = random.Random(seed)
    gaps = sorted(rng.uniform(.45, .92) for _ in range(4))
    hi = (-2.25, .9)            # the two sheen wedges
    k = 0
    r = rl + 3
    while r < R - 1.5:
        f = (r - rl) / (R - rl)
        if any(abs(f - g) < .015 for g in gaps):
            cv.line(_arc(cx, cy, r, 0, TAU))      # the band between tracks
            r += 2
            continue
        if k % 2 == 0:
            cv.hair(_arc(cx, cy, r, 0, TAU))
        else:
            hw = .2 + .12 * math.sin(f * PI)
            segs = [(hi[0] + hw, hi[1] - hw), (hi[1] + hw, hi[0] + TAU - hw)]
            for a0, a1 in segs:
                cv.hair(_arc(cx, cy, r, a0, a1))
        k += 1
        r += 1.5
    cv.line(_arc(cx, cy, R - 1.5, 0, TAU))
    # dead wax and the label
    cv.obj([_circ(cx, cy, rl + 2)], .5)
    cv.hair([_arc(cx, cy, rl + 1, 0, TAU)])
    lab = _circ(cx, cy, rl)
    cv.obj([lab], 1.)
    rr = rl * .72
    q = rl - 1.5
    while q > rr:
        cv.hair(_arc(cx, cy, q, 0, TAU))
        q -= 3
    cv.line(_arc(cx, cy, rr, 0, TAU))
    cv.hair(C.hatch_poly(_circ(cx, cy, rr - 1), 0, 3))
    if rl > 9:
        cv.obj([], 0)
        cv.heavy(_p_monogram(cx + rl * .05, cy, rr * .82))
    cv.obj([_circ(cx, cy, max(1.2, rl * .1), 12)], 1.5)
    cv.heavy([_arc(cx, cy, max(.5, rl * .05), 0, TAU)])


def vignette(x, y, w, h, field_poly, seed, kind):
    """kind 'disc': record only (medallion); 'full': sleeve + record over the village."""
    cv = C.Canvas()
    xs = [p[0] for p in field_poly]
    ys = [p[1] for p in field_poly]
    box = (min(xs), min(ys), max(xs), max(ys))
    fx0, fy0, fx1, fy1 = box
    fw, fh = fx1 - fx0, fy1 - fy0
    if kind == "disc":
        R = min(fw, fh) / 2 - 5
        cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
        _sunburst(cv, cx, cy, box, 28)
        _record(cv, cx, cy, R, seed)
        return cv.svg()
    R = min(fh * .36, fw * .3)
    cx = fx0 + fw * .62
    cy = fy0 + fh * .47
    _sunburst(cv, cx, cy, box, 40)
    _village(cv, fx0, fx1, fy0 + fh * .9, max(8., fh * .085), seed)
    S = R * 2.05
    sx, sy = cx - R * 1.05, cy - R * .05
    _sleeve(cv, sx, sy, S, -.12, seed)
    _record(cv, cx, cy, R, seed)
    return cv.svg()


# ------------------------------------------------------------------------------------------
# Parker's drumsticks, crossed behind the cartouche
# ------------------------------------------------------------------------------------------

def _drumstick(cv, x0, y0, x1, y1, wd):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    n = 24
    left, right = [], []
    for i in range(n + 1):
        u = i / n
        t = wd * (1 - .55 * C._smooth(.55, .97, u))
        px, py = x0 + ux * L * u, y0 + uy * L * u
        left.append((px + nx * t, py + ny * t))
        right.append((px - nx * t, py - ny * t))
    body = left + right[::-1]
    cv.obj([body], 1.)
    for f in (-.6, -.25):
        cv.hair([(x0 + ux * L * u + nx * wd * f * (1 - .55 * C._smooth(.55, .97, u)),
                  y0 + uy * L * u + ny * wd * f * (1 - .55 * C._smooth(.55, .97, u))) for u in [i / 20 for i in range(21)]])
    cv.hair(C.hatch_poly(body, math.degrees(math.atan2(uy, ux)) + 70, 3))
    for f in (.55, .78):
        cv.line([(x0 + ux * L * u + nx * wd * f * (1 - .55 * C._smooth(.55, .97, u)),
                  y0 + uy * L * u + ny * wd * f * (1 - .55 * C._smooth(.55, .97, u))) for u in [i / 20 for i in range(21)]])
    tip = _circ(x1 + ux * wd * .9, y1 + uy * wd * .9, wd * 1.15, 18)
    cv.obj([tip], 1.)
    cv.hair(C.hatch_poly(tip, 0, 1.5, 0, .3)[len(C.hatch_poly(tip, 0, 1.5, 0, .3)) // 2:])


def _crossed_sticks(cv, cx, cy, cw, ch):
    wd = max(2.5, min(cw, ch) * .024)
    for s in (-1, 1):
        x0, y0 = cx + s * cw * .38, cy + ch * .42
        x1, y1 = cx - s * cw * .62, cy - ch * .55
        _drumstick(cv, x0, y0, x1, y1, wd)


# ------------------------------------------------------------------------------------------
# banner lettering: a bar of swing rhythm; tablet: a sound wave
# ------------------------------------------------------------------------------------------

def _swing_bar(cv, centre, h, seed):
    n = len(centre) - 1
    def at(u, s):
        i = min(n - 1, int(u * n))
        f = u * n - i
        (ax, ay), (bx, by) = centre[i], centre[i + 1]
        px, py = ax + (bx - ax) * f, ay + (by - ay) * f
        L = math.hypot(bx - ax, by - ay) or 1
        return px - (by - ay) / L * s, py + (bx - ax) / L * s
    sp = max(1.5, h * .13)
    u0, u1 = .14, .86
    cv.obj([], 0)
    for k in range(-2, 3):
        cv.hair([at(u0 + (u1 - u0) * i / 40, k * sp) for i in range(41)])
    for u in (u0, u1, .5):
        cv.line([at(u, -2 * sp), at(u, 2 * sp)])
    cv.heavy([at(u0 + .012, -2 * sp), at(u0 + .012, 2 * sp)])
    rng = random.Random(seed)
    # ride pattern: ding, ding-a, ding, ding-a, in two bars
    steps = [0, 1, 1.67, 2, 3, 3.67]
    for bar in (0, 1):
        b0 = u0 + .03 + bar * (u1 - u0) / 2
        bw = (u1 - u0) / 2 - .05
        for st in steps:
            u = b0 + bw * st / 4.
            line = rng.choice((0, 1, 1, 2)) * .5
            hx, hy = at(u, line * sp)
            rx, ry = sp * .75, sp * .55
            head = [(hx + rx * math.cos(t) * math.cos(-.35) - ry * math.sin(t) * math.sin(-.35),
                     hy + rx * math.cos(t) * math.sin(-.35) + ry * math.sin(t) * math.cos(-.35))
                    for t in [TAU * i / 12 for i in range(12)]]
            cv.obj([head], 1.)
            cv.heavy([head + [head[0]]])
            cv.line([(hx + rx * .9, hy), (hx + rx * .9, hy - sp * 3.2)])
        # beam the swung pairs
        for st0, st1 in ((1, 1.67), (3, 3.67)):
            ua, ub = b0 + bw * st0 / 4, b0 + bw * st1 / 4
            pa, pb = at(ua, 0), at(ub, 0)
            cv.heavy([(pa[0] + sp * .7, min(pa[1], pb[1]) - sp * 3.2 + 1), (pb[0] + sp * .7, min(pa[1], pb[1]) - sp * 3.2 + 1)])


def _wave_tablet(tx, ty, tw, th, seed):
    rng = random.Random(seed)
    o = [f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="{C.pat("L")}" stroke="none"/>']
    cy = ty + th / 2
    d = []
    n = int((tw - 10) / 2)
    ph = [rng.uniform(0, TAU) for _ in range(4)]
    for i in range(n):
        x = tx + 5 + i * 2
        u = i / n
        env = math.sin(PI * u) ** .6
        a = env * (.35 + .25 * math.sin(u * 23 + ph[0]) + .2 * math.sin(u * 61 + ph[1]) + .15 * math.sin(u * 137 + ph[2]))
        a = max(.2, min(1, abs(a) * 1.4)) * (th / 2 - 2)
        d.append(f"M{_n(x)},{_n(cy - a)}V{_n(cy + a)}")
    o.append(f'<path d="{"".join(d)}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(tx + 3)},{_n(cy)}h{_n(tw - 6)}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts (copied from engraving_codex and made bespoke)
# ------------------------------------------------------------------------------------------

def _clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_d(poly, True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _cart_field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return C._superellipse(cx, cy, a + .5, b + .5)


def _band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    field = C._ell_pts(cx, cy, rx - 1.5, ry - 1.5, 64)[:-1]
    o.append(_clip_poly(C._uid("bv", w, h, seed), field, vignette(cx - rx, cy - ry, 2 * rx, 2 * ry, field, seed, "disc")))
    o.append(f'<path d="{_d(field + [field[0]], tol=.1)}" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def _medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .42, gh * 1.5)
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
                   max_n=int(12 * density), edge=.7, cv=cv)
    cv.extend(main)
    ch = gh + 4
    _crossed_sticks(cv, cx, cy, cw, ch)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field = _cart_field(cx, cy, cw, ch)
    o.append(_clip_poly(C._uid("mv", w, h, seed), field, vignette(0, 0, 0, 0, field, seed, "full")))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    # the plate hangs from the text on a light diagonal ground, so no bare paper shows above it
    o.append(f'<path d="M0,0h{_n(w)}v{_n(top_free + 2)}h{_n(-w)}z" fill="{C.pat("D")}" stroke="none"/>')
    o.append(C.bead_moulding(0, 2.5, w, 1., fillet=False))
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(11, ph * .04), rmax=r1 * .9,
                   max_n=int(10 * density), edge=.6, cv=cv)
    cv.extend(main)
    _crossed_sticks(cv, cx, cy, cw, ch)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    field = _cart_field(cx, cy, cw, ch)
    o.append(_clip_poly(C._uid("tv", w, h, seed), field, vignette(0, 0, 0, 0, field, seed, "full")))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    bcv = C.Canvas()
    _swing_bar(bcv, centre, bh, seed)
    o.append(bcv.svg())
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, h - py), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_wave_tablet(tx + 2, ty + 2, tw - 3, th - 3, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("f", w, h, seed), 0, fy, w, fh - 2,
                         C.scroll_band(0, fy, w, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1.5)}h{_n(w)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = _seed(ctx)
    if h < 110:
        body = _band(w, h, seed)
    elif h <= 260:
        body = _medium(w, h, seed)
    else:
        body = _tall(w, h, seed)
    return C.svg_doc(w, h, body)
