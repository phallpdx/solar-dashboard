"""civics-02 "Election coming up": an engraved Oregon vote-by-mail plate.

Per the edition plan: a vignette of about a fifth of the sheet, an OVAL. In it an Oregon official
ballot drop box takes a ballot at the edge of the valley fields, the river and Mt. Hood beyond,
under an engraved sky; fine scroll wings carry the ornament out to the margins.
Easter egg: a heron weathervane turns on the drop box's hood.
"""
import sys
import math
import random
import re
import engraving_codex as C

# ---- studio helpers (batch 8): engraved grounds, rolled acanthus, rinceau, engraved sky ----
# Copied into each plate (the house library stays untouched). Pure stdlib, deterministic.
import math as _m
import random as _r
import engraving_codex as _C

_SN, _SD = _C._n, _C._d
_SPI = _m.pi


def _sm(e0, e1, x):
    t = min(1., max(0., (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _shape_d(shape):
    if isinstance(shape, tuple) and len(shape) == 4:
        x, y, w, h = shape
        return f"M{_SN(x)},{_SN(y)}h{_SN(w)}v{_SN(h)}h{_SN(-w)}z", (x, y, x + w, y + h)
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    return _SD(shape, True, 0), (min(xs), min(ys), max(xs), max(ys))


def _stip_pat(pid, size, n, seed, big=0):
    """A white punch-dot tile (whole CSS px squares on whole px, so 2x2 device px each)."""
    rng = _r.Random(seed)
    pts = []
    tries = 0
    while len(pts) < n and tries < 400:
        tries += 1
        x, y = rng.randrange(size), rng.randrange(size)
        if all(min(abs(x - a), size - abs(x - a)) + min(abs(y - b), size - abs(y - b)) >= 3 for a, b in pts):
            pts.append((x, y))
    d = "".join(f"M{x},{y}h1v1h-1z" for x, y in pts[big:])
    d += "".join(f"M{x},{y}h1.5v1.5h-1.5z" for x, y in pts[:big])
    return (f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
            f'<path d="{d}" fill="#fff"/></pattern>')


def _curl_pts(x, y, ang, L, k0, k1, n=None):
    """A tendril: heading ang, length L, curvature rising from k0 to k1 (1/px) into a tight curl."""
    n = n or max(6, int(L / 1.5))
    ds = L / n
    a = ang
    pts = [(x, y)]
    for i in range(n):
        u = (i + .5) / n
        a += (k0 + (k1 - k0) * u ** 2.2) * ds
        x += _m.cos(a) * ds
        y += _m.sin(a) * ds
        pts.append((x, y))
    return pts


def engraved_ground(shape, seed=0, density=1., cid=None):
    """The cut-away ground as a master cuts it: solid black, punched all over with fine white
    stipple, with faint white background tendrils winding through it (each ending in a curl and
    throwing off little leaflets), a scatter of tiny florets and sparkle cuts. White lines are 1 CSS
    px so they survive the panel; no flat black larger than ~9 px is left anywhere."""
    d, (x0, y0, x1, y1) = _shape_d(shape)
    rng = _r.Random(seed * 7919 + 17)
    pid = "sg" + format(_C.zlib.crc32(repr((x0, y0, x1, y1, seed)).encode()) & 0xffffff, "x")
    o = [f'<defs>{_stip_pat(pid + "a", 9, 6, seed + 1, 1)}{_stip_pat(pid + "b", 11, 4, seed + 2)}</defs>',
         f'<path d="{d}" fill="#000" stroke="none"/>',
         f'<path d="{d}" fill="url(#{pid}a)" stroke="none"/>',
         f'<path d="{d}" fill="url(#{pid}b)" stroke="none"/>']
    tend, flor = [], []
    sp = 34. / max(.3, density) ** .5
    j = 0
    yy = y0 + rng.uniform(0, sp * .5)
    while yy < y1 + 6:
        xx = x0 - rng.uniform(0, sp)
        while xx < x1 + 6:
            px, py = xx + rng.uniform(-7, 7), yy + rng.uniform(-7, 7)
            kind = rng.random()
            if kind < .7:
                # a tendril: a long easy sweep tightening into a curl, two or three leaflets off it
                ang = rng.uniform(0, 2 * _SPI)
                sg = rng.choice((-1, 1))
                L = rng.uniform(22, 34)
                pts = _curl_pts(px, py, ang, L, sg * .01, sg * .34)
                tend.append(pts)
                for t in (.22, .48, .7)[:2 + (rng.random() < .4)]:
                    i = int(t * (len(pts) - 1))
                    a = _m.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
                    sd = -sg if (i % 2) else sg
                    lf = _curl_pts(pts[i][0], pts[i][1], a - sd * .9, rng.uniform(3.5, 5.5), sd * .25, sd * .9, 5)
                    tend.append(lf)
            elif kind < .86:
                # a tiny floret: five petal cuts round a dark heart
                r = rng.uniform(1.8, 2.4)
                a0 = rng.uniform(0, 1.3)
                for k in range(5):
                    a = a0 + k * 2 * _SPI / 5
                    flor.append([(px + _m.cos(a) * 1.2, py + _m.sin(a) * 1.2), (px + _m.cos(a) * (1.2 + r), py + _m.sin(a) * (1.2 + r))])
            else:
                r = rng.uniform(1.5, 2.2)
                flor.append([(px - r, py), (px + r, py)])
                flor.append([(px, py - r), (px, py + r)])
            xx += sp * rng.uniform(.85, 1.15)
        yy += sp * .6
        j += 1
    td = "".join(_SD(p, tol=.2) for p in tend)
    fd = "".join(_SD(p, tol=0) for p in flor)
    cid = cid or pid + "c"
    o.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">'
             f'<path d="{td}{fd}" stroke="#fff" stroke-width="1" fill="none"/></g>')
    return "".join(o)


def engraved_panel(shape, seed=0, tone=1):
    """A flat panel (a moulding face, a slab, a tablet surround) engraved rather than ruled: fine
    stipple-graded diagonal bulino that breaks into a running vine of white tendrils. tone 0 light,
    1 mid. Used wherever a plain ruled panel used to be."""
    d, (x0, y0, x1, y1) = _shape_d(shape)
    pid = "sp" + format(_C.zlib.crc32(repr((x0, y0, x1, y1, seed, tone)).encode()) & 0xffffff, "x")
    if tone:
        return engraved_ground(shape, seed, .7)
    rng = _r.Random(seed)
    # light: black stipple dots on white with hairline tendrils
    pts = []
    while len(pts) < 5:
        x, y = rng.randrange(6), rng.randrange(6)
        if (x, y) not in pts:
            pts.append((x, y))
    tile = "".join(f"M{x},{y}h.5v.5h-.5z" for x, y in pts)
    o = [f'<defs><pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse"><path d="{tile}" fill="#000"/></pattern></defs>',
         f'<path d="{d}" fill="#fff" stroke="none"/><path d="{d}" fill="url(#{pid})" stroke="none"/>']
    tend = []
    x = x0 - 4
    while x < x1 + 4:
        y = y0 + (y1 - y0) * rng.uniform(.25, .75)
        tend.append(_curl_pts(x, y, rng.uniform(-.6, .6), rng.uniform(14, 22), rng.choice((-1, 1)) * .05, rng.choice((-1, 1)) * .45))
        x += rng.uniform(12, 18)
    o.append(f'<clipPath id="{pid}c"><path d="{d}"/></clipPath><g clip-path="url(#{pid}c)">'
             f'<path d="{"".join(_SD(p, tol=.2) for p in tend)}" stroke="#000" stroke-width=".5" fill="none"/></g>')
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# rolled acanthus: broad lobed leaves with veins, eyes between the lobes and a turned-over tip
# ------------------------------------------------------------------------------------------------

def _euler_k(x, y, ang, L, kfun, n):
    ds = L / n
    pts = [(x, y)]
    a = ang
    for i in range(n):
        a += kfun((i + .5) / n) * ds
        x += _m.cos(a) * ds
        y += _m.sin(a) * ds
        pts.append((x, y))
    return pts


def _lobe_w(v, minor=3):
    """Width factor across one major lobe (v 0..1): a rounded lobe pinched hard at each notch,
    its rim scalloped into `minor` small rounded fingers that point toward the tip."""
    v = min(1., max(0., v))
    major = .34 + .66 * _m.sin(_SPI * v ** .8) ** .5
    q = (v * minor) % 1.
    sc = .86 + .14 * _m.sin(_SPI * q ** .7) ** .5
    return major * sc


def _body(cv, R, out_s, lobes, u_a, u_b, ph, Wmax, dark=1., turn=True, minor=3):
    """Shade an acanthus body laid on rib R: veins, lobe fans, eyes, inner shadow, turned tip."""
    Lr = R.L
    inn = -out_s
    # inner (shadow) half: form lines, denser toward the concave edge
    for s in (.2, .4, .56, .7, .82, .92):
        cv.hair(R.contour(inn * s, .03, .97, minw=1.7 / max(.08, .2 if s <= .2 else min(.2, s - .0) * .8)))
    _C._shadow(cv, R, inn, min(2.8, Wmax * .4) * dark, .08, .92)
    # central vein: a cut groove, black on its shadow side, a hair on its lit side
    cv.line(R.contour(inn * .05, .05, .92, minw=1.))
    cv.hair(R.contour(out_s * .14, .08, .85, minw=3.5))
    notch = [u_a + (k - ph) / lobes * (u_b - u_a) for k in range(1, lobes)]
    bounds = [u_a] + notch + [u_b]
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        if b - a < .02:
            continue
        span = b - a
        wm = R.width((a + b) / 2, out_s)
        if wm < 2.4:
            continue
        # fan of cuts from the vein into the lobe: the secondary vein, and modelling lines either
        # side that cup the lobe (shadow toward its root, its rim left white)
        nf = 2 if wm < 5 else 3 if wm < 8 else 4
        for f in range(nf):
            t = (f + .5) / nf
            u0 = a + span * (.05 + .3 * t)
            u1 = a + span * (.15 + .8 * t)
            reach = .78 if f == nf // 2 else .62
            p = [R.at(u0, out_s * .06), R.at((u0 + u1) / 2, out_s * .38), R.at(u1, out_s * reach)]
            (cv.line if (f == nf // 2 and wm > 6) else cv.hair)(p)
        # the lobe's cupped root, shaded in short cuts along the notch side
        if wm > 4:
            for g in (.0, .06):
                cv.hair([R.at(a + span * g, out_s * .2), R.at(a + span * (g + .12), out_s * .55)])
    # the eyes drilled at the notches
    for u in notch:
        if R.width(u, out_s) < 2:
            continue
        p0 = R.at(u, out_s * .95)
        p1 = R.at(u - 2.4 / Lr, out_s * .55)
        p2 = R.at(u + 1.4 / Lr, out_s * .7)
        cv.obj([[p0, p2, p1]], 0)
        cv.heavy([p0, p1])
        cv.line([p0, p2, p1, R.at(u - 1.2 / Lr, out_s * .78)])
    if turn:
        # the tip turned over: its underside dark
        cv.line(R.contour(inn * .3, .84, .99, minw=.7))
        cv.line(R.contour(inn * .62, .82, .98, minw=.7))
        cv.hair(R.contour(out_s * .3, .88, .99, minw=.7))


def leaf(cv, x, y, ang, L, W, bend=.8, curl=2.6, lobes=None, seed=0, dark=1., turn=True):
    """One acanthus leaf from (x, y), heading ang (radians), length L, max half-width W. bend is
    the sweep in radians (sign = which way it curls); the tip rolls over by `curl` radians. Its
    convex edge is cut into rounded, scalloped lobes with a drilled eye at each notch; a central
    vein runs to the tip with a fan of cuts into every lobe; the shadowed half is ruled along the
    form and darkens into the curl, the lobe rims stay white."""
    rng = _r.Random(seed)
    sg = 1 if bend + curl >= 0 else -1
    n = max(24, int(L / 1.))
    pts = _euler_k(x, y, ang, L, lambda u: (bend + curl * _sm(.6, 1., u) ** 2 * 2.4) / L, n)
    lobes = lobes or max(2, min(5, int(L / (W * 1.5) + .5)))
    u_a, u_b = .14, .88
    ph = rng.uniform(-.06, .06)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        e = W * (u / .4) ** .5 if u < .4 else W * (1 - _sm(.4, 1., u) * .85)
        e = max(.5, e * (.5 + .5 * _sm(0, .1, u)))
        if u_a < u < u_b:
            v = ((u - u_a) / (u_b - u_a)) * lobes + ph
            wo.append(max(.5, e * _lobe_w(v % 1.)))
        else:
            wo.append(e * (.7 if u >= u_b else 1.))
        wi.append(max(.5, e * (.55 + .08 * _m.sin(u * 9 + seed))))
    if sg > 0:
        R = _C._Rib(pts, wi, wo)
        out_s = -1
    else:
        R = _C._Rib(pts, wo, wi)
        out_s = 1
    cv.obj([R.outline()], 1.)
    _body(cv, R, out_s, lobes, u_a, u_b, ph, W, dark, turn)
    for u in (.025, .05):
        if R.width(u, 1) + R.width(u, -1) > 3:
            cv.hair([R.at(u, -.9), R.at(u + .012, .9)])
    return R


def spiral_eye(cv, x, y, r, sg=1):
    """A tight spiral eye with a beaded centre."""
    cv.obj([_C._ell_pts(x, y, r + .9, r + .9, 20)[:-1]], 0)
    for k in range(int(r / .9) + 1):
        rr = r - k * .9
        if rr < .6:
            break
        cv.line(_C._ell_pts(x, y, rr, rr, max(8, int(rr * 5)), 0, 2 * _SPI * .8))
    br = max(.9, min(1.6, r * .38))
    cv.obj([_C._ell_pts(x + sg * .2, y - .2, br, br, 10)[:-1]], 1.)


def volute(cv, cx, cy, r, a0=180., turns=1.5, flip=False, seed=0, tail=0., tail_bend=0., stem=None,
           leaves=3, leaf_scale=1., inner=True, blade=.34):
    """A volute of rolled acanthus: a round-carved stem winds into a tight spiral eye with a beaded
    centre; its outside grows a broad lobed blade (veined, eyed, shaded like a leaf) and broad
    leaves spring from it, sweeping toward the eye and overlapping; one leaf rolls into the curl.
    Returns the stem points (root first)."""
    rng = _r.Random(seed)
    pts = _C.volute_spine(cx, cy, r, a0, turns, flip, tail, tail_bend, .14)
    n = len(pts)
    i = n // 2
    a, b = pts[i - 1], pts[i + 1]
    ins = 1 if (-(b[1] - a[1])) * (cx - pts[i][0]) + (b[0] - a[0]) * (cy - pts[i][1]) > 0 else -1
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + _m.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]))
    tot = S[-1]
    W0 = stem or max(1.6, r * .14)
    lobes = max(2, int(tot * .62 / (r * .55)))
    u_a, u_b = .05, .68
    ph = rng.uniform(0, .3)
    ws, wb = [], []
    for k in range(n):
        u = S[k] / tot
        w = max(.8, W0 * (1 - .7 * u ** 1.2) * (.3 + .7 * _sm(0, .08, u)))
        env = blade * r * _sm(0, .14, u) * (1 - _sm(.35, .7, u))
        ws.append(w)
        if u_a < u < u_b:
            v = ((u - u_a) / (u_b - u_a)) * lobes + ph
            wb.append(max(w, w + env * _lobe_w(v % 1.)))
        else:
            wb.append(w)
    R = _C._Rib(pts, ws if ins > 0 else wb, wb if ins > 0 else ws)
    cv.obj([R.outline()], 1.)
    # stem: rounded, shadow toward the inside of the curl
    for s in (.35, .62, .84):
        cv.hair(R.contour(s * ins, 0., .98, minw=1.4 / max(.1, (1 - s) * .6)))
    _C._shadow(cv, R, ins, W0 * .45, 0., .97)
    # the blade on the outside: fan cuts, eyes, a vein along the stem's edge
    out_s = -ins
    cv.line(R.contour(out_s * (W0 / max(1, W0 + blade * r)) * 1.1, .1, .62, minw=W0 + 2))
    Lr = R.L
    notch = [u_a + (k - ph) / lobes * (u_b - u_a) for k in range(1, lobes + 1)]
    bounds = [u_a] + [u for u in notch if u < u_b] + [u_b]
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        span = b - a
        wm = R.width((a + b) / 2, out_s)
        if wm < W0 + 2.5:
            continue
        nf = 3 if wm < 9 else 4
        for f in range(nf):
            t = (f + .5) / nf
            u0, u1 = a + span * (.05 + .3 * t), a + span * (.15 + .8 * t)
            cv.hair([R.at(u0, out_s * .3), R.at((u0 + u1) / 2, out_s * .55), R.at(u1, out_s * .82)])
        cv.hair(R.contour(out_s * .45, a + span * .02, a + span * .3, minw=4))
    for u in notch:
        if u >= u_b or R.width(u, out_s) < W0 + 2:
            continue
        p0 = R.at(u, out_s * .95)
        p1 = R.at(u - 2.4 / Lr, out_s * .6)
        p2 = R.at(u + 1.4 / Lr, out_s * .74)
        cv.heavy([p0, p1])
        cv.line([p0, p2, p1])
    # leaves springing from the blade, laid eye-first so those nearer the root lie on top
    spots = []
    u = .1 + (tail * r / tot if tail else 0) * .25
    for j in range(leaves):
        if u > .66:
            break
        k = min(n - 2, int(u * (n - 1)))
        p, q = pts[max(0, k - 1)], pts[k + 1]
        ta = _m.atan2(q[1] - p[1], q[0] - p[0])
        rad = _m.hypot(pts[k][0] - cx, pts[k][1] - cy)
        ll = min(r * 1.6, max(r * .8, rad * 1.35)) * leaf_scale * rng.uniform(.88, 1.06)
        spots.append((R.at(u, out_s * .55), ta, ll, rad))
        u += ll * .42 / tot
    for base, ta, ll, rad in spots[::-1]:
        sweep = ins * (ll / max(rad, 4) * .6 + .25)
        leaf(cv, base[0], base[1], ta - ins * rng.uniform(.3, .5), ll, ll * rng.uniform(.26, .32), sweep,
             ins * rng.uniform(1.4, 2.2), seed=rng.randrange(1 << 20))
    if inner:
        u = .55
        k = int(u * (n - 1))
        p, q = pts[k - 1], pts[k + 1]
        ta = _m.atan2(q[1] - p[1], q[0] - p[0])
        base = R.at(u, ins * .2)
        ll = r * .72 * leaf_scale
        leaf(cv, base[0], base[1], ta + ins * .25, ll, ll * .22, ins * 1.5, ins * 1.8, lobes=2,
             seed=rng.randrange(1 << 20), dark=1.2)
    ex, ey = pts[-1]
    spiral_eye(cv, ex, ey, max(2.2, r * .11), ins)
    return pts


def rinceau(cv, x0, y0, ang, length, breadth, seed=0, mirror=False, r_scale=1., turns=1.4, first_down=True,
            leaves=3):
    """A continuous running scroll along a line from (x0, y0) heading ang degrees: each volute
    springs from the tail of the one before, curling alternately to either side, every one a
    different size and leafage (never a stamp), the run finishing in a terminal curl."""
    rng = _r.Random(seed)
    th = _m.radians(ang)
    dx, dy = _m.cos(th), _m.sin(th)
    nx, ny = (dy, -dx) if mirror else (-dy, dx)
    r = breadth * .4 * r_scale
    n = max(1, int(round(length / (r * 2.3))))
    P = length / n
    r = min(r, P * .47)
    units = []
    along = 0.
    sizes = [rng.uniform(.84, 1.08) for _ in range(n)]
    tot = sum(sizes)
    for i in range(n):
        Pi = length * sizes[i] / tot
        down = (i % 2 == 0) == first_down
        ri = min(r * sizes[i] ** .7, Pi * .5, breadth * .47)
        off = (breadth / 2 - ri * 1.02) * (1 if down else -1)
        c_al = along + Pi * .6
        a0, flip = (-90, False) if down else (90, True)
        if mirror:
            a0, flip = -a0, not flip
        units.append((x0 + dx * c_al + nx * off * .35, y0 + dy * c_al + ny * off * .35, ri, a0 + ang, flip,
                      (.9 if down else -.9) * (1 if not mirror else 1), (Pi * .58) / ri, rng.randrange(1 << 20)))
        along += Pi
    for cx, cy, ri, a0, flip, tb, tl, sd in units[::-1]:
        volute(cv, cx, cy, ri, a0, turns, flip, sd, tail=tl, tail_bend=tb, stem=ri * .15,
               leaves=leaves if ri > 20 else 2)
    return units


# ------------------------------------------------------------------------------------------------
# engraved sky: graded lines that part round modelled cloud banks
# ------------------------------------------------------------------------------------------------

def engraved_sky(cv, X, Y, W, H, seed=0, clouds=3, sun=None, maxc=6):
    """Sky for a vignette X..X+W, Y..Y+H: engraved, never merely ruled. Cumulus banks built of
    billows (each a modelled dome: a lit crown left white, its underside rolled in curved cuts
    that close toward the base, a dark seam beneath), lines between them that tighten toward the
    zenith and ripple, parting round every cloud. sun=(x, y, r) cuts a disc with rings."""
    rng = _r.Random(seed)
    cv.obj([[(X - 2, Y - 2), (X + W + 2, Y - 2), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]], 0)
    nb = max(clouds, min(maxc, int(W * H / 9000)))
    rows = max(1, int(H / 50))
    banks = []
    for k in range(nb):
        row = k % rows
        cy = Y + H * (row + rng.uniform(.5, .85)) / rows
        cols = max(1, (nb + rows - 1) // rows)
        cx = X + W * ((k // rows) + rng.uniform(.2, .8)) / cols
        span = min(W * rng.uniform(.12, .2), 70)
        hgt = min(H / rows * .6, span * .55)
        bl = []
        nbl = rng.randint(3, 5)
        for b in range(nbl):
            u = (b + .5) / nbl
            br = hgt * (.5 + .5 * _m.sin(_SPI * u)) * rng.uniform(.8, 1.)
            bl.append((cx - span * .85 + 1.7 * span * u, cy - br * .5, br))
        banks.append((cx, cy, span, bl))

    def top_of(bl, x):
        t = None
        for bx, by, br in bl:
            if abs(x - bx) < br:
                v = by - (br * br - (x - bx) ** 2) ** .5
                t = v if t is None or v < t else t
        return t

    shapes = []
    for cx, cy, span, bl in banks:
        xs = [cx - span * 1.3 + i * 1.5 for i in range(int(span * 2.6 / 1.5) + 1)]
        tops = [(x, top_of(bl, x)) for x in xs]
        tops = [(x, t) for x, t in tops if t is not None and t < cy]
        if len(tops) < 3:
            continue
        x0, x1 = tops[0][0], tops[-1][0]
        base = [(x, cy + 1.5 * _m.sin(_SPI * (x - x0) / max(1., x1 - x0))) for x, _ in tops[::-1]]
        shapes.append((tops + base, tops, cy, bl, x0, x1))

    def inside(px, py):
        for poly, tops, cy, bl, x0, x1 in shapes:
            if x0 - 1 <= px <= x1 + 1 and py <= cy + 2.5:
                t = top_of(bl, px)
                if t is not None and py >= t - 1:
                    return True
        if sun and _m.hypot(px - sun[0], py - sun[1]) < sun[2] + 2:
            return True
        return False

    y = Y + .5
    lines = []
    while y < Y + H + 2:
        t = (y - Y) / max(1., H)
        pitch = 1.5 if t < .2 else 2. if t < .55 else 3.
        run = []
        x = X - 2
        while x <= X + W + 2:
            yy = y + .7 * _m.sin(x / 19. + y * .37)
            if inside(x, yy):
                if len(run) > 1:
                    lines.append(run)
                run = []
            else:
                if not run or (x - run[-1][0]) >= 6 or inside(x + 2, yy):
                    run.append((x, yy))
                elif len(run) > 1 and x - run[-2][0] < 6:
                    run[-1] = (x, yy)
                else:
                    run.append((x, yy))
            x += 2.
        if len(run) > 1:
            lines.append(run)
        y += pitch
    cv.hair(lines)
    for poly, tops, cy, bl, x0, x1 in sorted(shapes, key=lambda s: s[2]):
        cv.obj([poly], .5)
        # the body rolled in curved cuts that bow with the base, stopping short of each crown so
        # a lit rim stays white; denser toward the shadowed base
        cuts = []
        v = cy - .5
        while True:
            seg = []
            any_ = False
            for x, tp in tops:
                u = (x - x0) / max(1., x1 - x0)
                yy = v + 1.6 * _m.sin(_SPI * u) - 1.2
                rim = 1.8 + (cy - tp) * .22
                if yy > tp + rim:
                    seg.append((x, yy))
                    any_ = True
                elif len(seg) > 1:
                    cuts.append(seg)
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                cuts.append(seg)
            if not any_:
                break
            v -= 1.5 if cy - v < 5 else 2. if cy - v < 11 else 3.
        cv.hair(cuts)
        # the billows' crowns where they fold over one another
        for bx, by, br in bl:
            arc = [(bx + br * .92 * _m.cos(a), by + br * .92 * _m.sin(a)) for a in [_SPI * (1.15 + .7 * i / 8) for i in range(9)]]
            arc = [p for p in arc if (top_of(bl, p[0]) or -1e9) < p[1] - 1.5]
            if len(arc) > 1:
                cv.hair(arc)
        cv.line([(x0 + 2, cy + .8), (x1 - 2, cy + .8)])
    if sun:
        sx, sy, sr = sun
        cv.obj([_C._ell_pts(sx, sy, sr, sr, 32)[:-1]], 1.)
        cv.hair([_C._ell_pts(sx, sy, sr * f, sr * f, 28) for f in (.75, .5)])
    return shapes


def meadow_tufts(cv, x, y0, w, y1, seed=0, dens=1.):
    """A meadow engraved as grass, not ruled: rows of tufts receding to the horizon, each tuft a
    fan of curved blades, small and close far off, large and open in front, a shadow stroke at
    every root."""
    rng = _r.Random(seed)
    cv.obj([[(x - 2, y0), (x + w + 2, y0), (x + w + 2, y1 + 2), (x - 2, y1 + 2)]], 0)
    tufts, roots = [], []
    yy = y0 + 1.5
    while yy < y1 + 2:
        t = (yy - y0) / max(1., y1 - y0)
        s = 1.8 + 7. * t ** 1.3
        step = (3. + 6. * t) / dens
        xx = x - 2 + rng.uniform(0, step)
        while xx < x + w + 2:
            n = 3 + (s > 5)
            pl = []
            for k in range(n):
                a = -_SPI / 2 + (k - (n - 1) / 2) * .34 + rng.uniform(-.12, .12)
                L = s * rng.uniform(.7, 1.1) * (1 - .18 * abs(k - (n - 1) / 2))
                bx = xx + k * .7
                pl += [(bx, yy), (bx + _m.cos(a) * L, yy + _m.sin(a) * L)]
            tufts.append(pl)
            if t > .45:
                roots.append([(xx - s * .2, yy + .4), (xx + s * .5, yy + .4)])
            xx += step * rng.uniform(.8, 1.25)
        yy += 2. if t < .3 else 3. if t < .65 else 4.
    cv.hair(tufts)
    cv.line(roots)

# ------------------------------------------------------------------------------------------------
# KING TIER: a dense field of fine scroll grown from one stem, on a punched matte
# ------------------------------------------------------------------------------------------------

import heapq as _hq


class _Grid:
    """Free-space clearance on a g-px grid over a region (polygons, minus obstacles)."""

    def __init__(self, x0, y0, x1, y1, g=3.):
        self.x0, self.y0, self.g = x0, y0, g
        self.nx, self.ny = int((x1 - x0) / g) + 1, int((y1 - y0) / g) + 1
        self.inside = bytearray(self.nx * self.ny)
        self.d = [0.] * (self.nx * self.ny)

    def cell(self, i):
        return self.x0 + (i % self.nx + .5) * self.g, self.y0 + (i // self.nx + .5) * self.g

    def fill_poly(self, poly, val=1):
        n = len(poly)
        g = self.g
        for j in range(self.ny):
            yc = self.y0 + (j + .5) * g
            xs = []
            for k in range(n):
                ax, ay = poly[k]
                bx, by = poly[(k + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for a in range(0, len(xs) - 1, 2):
                i0 = max(0, int((xs[a] - self.x0) / g + .5))
                i1 = min(self.nx, int((xs[a + 1] - self.x0) / g + .5))
                for i in range(i0, i1):
                    self.inside[j * self.nx + i] = val

    def clearance(self):
        """Chamfer distance (px) from every inside cell to the nearest outside cell."""
        nx, ny, g = self.nx, self.ny, self.g
        BIG = 1e9
        d = [0. if not self.inside[i] else BIG for i in range(nx * ny)]
        a, b = g, g * 1.4142
        for j in range(ny):
            for i in range(nx):
                k = j * nx + i
                if d[k] == 0.:
                    continue
                v = d[k]
                if i > 0: v = min(v, d[k - 1] + a)
                else: v = min(v, a * .5)
                if j > 0:
                    v = min(v, d[k - nx] + a)
                    if i > 0: v = min(v, d[k - nx - 1] + b)
                    if i < nx - 1: v = min(v, d[k - nx + 1] + b)
                else:
                    v = min(v, a * .5)
                d[k] = v
        for j in range(ny - 1, -1, -1):
            for i in range(nx - 1, -1, -1):
                k = j * nx + i
                if d[k] == 0.:
                    continue
                v = d[k]
                if i < nx - 1: v = min(v, d[k + 1] + a)
                else: v = min(v, a * .5)
                if j < ny - 1:
                    v = min(v, d[k + nx] + a)
                    if i < nx - 1: v = min(v, d[k + nx + 1] + b)
                    if i > 0: v = min(v, d[k + nx - 1] + b)
                else:
                    v = min(v, a * .5)
                d[k] = v
        self.d = d

    def stamp(self, cx, cy, r, reach):
        """A disc (cx, cy, r) is now occupied: lower clearances within `reach` of it."""
        g = self.g
        i0 = max(0, int((cx - r - reach - self.x0) / g))
        i1 = min(self.nx - 1, int((cx + r + reach - self.x0) / g) + 1)
        j0 = max(0, int((cy - r - reach - self.y0) / g))
        j1 = min(self.ny - 1, int((cy + r + reach - self.y0) / g) + 1)
        d = self.d
        nx = self.nx
        x0, y0 = self.x0 + .5 * g - cx, self.y0 + .5 * g - cy
        for j in range(j0, j1 + 1):
            dy = y0 + j * g
            dy2 = dy * dy
            row = j * nx
            for i in range(i0, i1 + 1):
                k = row + i
                dk = d[k]
                if dk > 0:
                    dx = x0 + i * g
                    t = dk + r
                    q = dx * dx + dy2
                    if q < t * t:
                        v = q ** .5 - r
                        d[k] = v if v > 0 else 0.


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        s = 1 - t
        out.append((s ** 3 * p0[0] + 3 * s * s * t * p1[0] + 3 * s * t * t * p2[0] + t ** 3 * p3[0],
                    s ** 3 * p0[1] + 3 * s * s * t * p1[1] + 3 * s * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def fine_leaf(cv, x, y, ang, L, W, sg, seed=0, lobes=None, ow=.5):
    """A small acanthus leaf for fine scroll: lobed outer edge with notch eyes, a vein, fine
    parallel cuts on its shadow half, a bright cut edge; 0.5 px work throughout."""
    rng = _r.Random(seed)
    n = max(10, int(L / 1.2))
    bend = sg * rng.uniform(.5, .9)
    curl = sg * rng.uniform(.9, 1.5)
    pts = _euler_k(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 2.4) / L, n)
    lobes = lobes or max(2, min(4, int(L / (W * 1.6) + .5)))
    u_a, u_b = .12, .9
    ph = rng.uniform(-.08, .08)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        e = W * (u / .42) ** .5 if u < .42 else W * (1 - _sm(.42, 1., u) ** 1.3 * .82)
        e = max(.45, e * (.45 + .55 * _sm(0, .12, u)))
        if u_a < u < u_b:
            v = ((u - u_a) / (u_b - u_a)) * lobes + ph
            wo.append(max(.45, e * _lobe_w(v % 1., 2)))
        else:
            wo.append(e)
        wi.append(max(.45, e * .58))
    if sg > 0:
        R = _C._Rib(pts, wi, wo)
        out_s = -1
    else:
        R = _C._Rib(pts, wo, wi)
        out_s = 1
    cv.obj([R.outline()], ow)
    inn = -out_s
    # shadow half: fine parallel cuts across the form, 1.5 px apart, longest at the leaf's belly
    Lr = R.L
    u = .08
    cuts, run, flip = [], [], False
    while u < .93:
        wv = R.width(u, inn)
        if wv > .9:
            a, b = R.at(u, inn * .06), R.at(u + .7 / Lr, inn * .99)
            run += [b, a] if flip else [a, b]
            flip = not flip
        elif len(run) > 1:
            cuts.append(run)
            run, flip = [], False
        u += 1.5 / Lr
    if len(run) > 1:
        cuts.append(run)
    for c in cuts:
        cv.hair(c)
    # the shadow edge cut black (it also parts the leaf from any white beneath it)
    cv.line(R.inset(inn, lambda u: .5 if R.width(u, inn) > .9 else None, .03, .95))
    # vein
    cv.hair(R.contour(inn * .04, .06, .86, minw=1.))
    # lobe cuts (one per lobe) and notch eyes
    notch = [u_a + (k - ph) / lobes * (u_b - u_a) for k in range(1, lobes)]
    bounds = [u_a] + notch + [u_b]
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        if R.width((a + b) / 2, out_s) > 2.4:
            cv.hair([R.at(a + (b - a) * .15, out_s * .08), R.at(a + (b - a) * .6, out_s * .6)])
    for u in notch:
        if R.width(u, out_s) > 1.8:
            cv.line([R.at(u, out_s * .95), R.at(u - 1.6 / R.L, out_s * .5)])
    return R


def _fine_scroll(cv, spine, r, sg, w0, rng, leaves=True):
    """Draw one fine scroll on its spine (tail + spiral): a white stem cut with a black shadow
    line inside the curl, fine leaves sprouting outside, a tight curl with a bead."""
    n = len(spine)
    S = [0.]
    for k in range(1, n):
        S.append(S[-1] + _m.hypot(spine[k][0] - spine[k - 1][0], spine[k][1] - spine[k - 1][1]))
    tot = S[-1] or 1.
    ws = [max(.55, w0 * (1 - .62 * (S[k] / tot) ** 1.3)) for k in range(n)]
    R = _C._Rib(spine, ws, ws)
    lv = []
    if leaves:
        # leaves along the outer turn, on the outside of the curl, pointing toward the eye
        nl = 2 + (r > 11)
        for j in range(nl):
            u = .12 + .5 * (j + rng.uniform(.15, .55)) / nl
            k = min(n - 2, int(u * (n - 1)))
            p, q = spine[k], spine[k + 1]
            ta = _m.atan2(q[1] - p[1], q[0] - p[0])
            ll = r * rng.uniform(1.0, 1.35) * (1.08 - .35 * j / nl)
            base = R.at(u, -sg * .7)
            lv.append((base, ta - sg * rng.uniform(.45, .75), ll, ll * rng.uniform(.32, .38), -sg))
    # leaves first (they lie under the stem at their root), then the stem
    for base, a, ll, lw, s in lv:
        fine_leaf(cv, base[0], base[1], a, ll, lw, s, rng.randrange(1 << 20))
    cv.obj([R.outline()], .5)
    cv.line(R.inset(sg, lambda u: .55 if R.width(u, sg) > .9 else None, .0, .97))
    if w0 > 1.6:
        cv.hair(R.contour(-sg * .45, .02, .7, minw=1.8))
    ex, ey = spine[-1]
    br = max(.8, min(1.5, r * .09))
    cv.obj([_C._ell_pts(ex, ey, br + .7, br + .7, 10)[:-1]], 0)
    cv.line(_C._ell_pts(ex, ey, br, br, 10))
    return R


def scroll_field(cv, region, holes=(), roots=(), seed=0, rmin=6., rmax=22., max_n=260, egg=None,
                 g=3., spacing=1.12):
    """Fill `region` (a polygon) with fine scroll, King tier: every scroll is a true logarithmic
    spiral ending in a tight beaded curl, springing by a smooth tail from a stem already laid (the
    roots first, so the whole field flows from one source), with fine shaded leaves along it.
    holes: polygons kept clear (a medallion, a figure). roots: polylines of main stems (drawn as
    stems). egg(cv, x, y, r): called once at the biggest gap to carve an Easter egg in place of a
    scroll. Painted so the parent stems lie over their children."""
    rng = _r.Random(seed)
    xs = [p[0] for p in region]
    ys = [p[1] for p in region]
    G = _Grid(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, g)
    G.fill_poly(region, 1)
    for h in holes:
        G.fill_poly(h, 0)
    G.clearance()
    reach = rmax * spacing + g * 2
    G.d = [min(v, reach) for v in G.d]
    # stems: sample points with tangents, in buckets for nearest queries
    B = 14.
    buckets = {}

    def add_stem(pts, rr):
        for k in range(0, len(pts) - 1, 2):
            p, q = pts[k], pts[k + 1]
            t = _m.atan2(q[1] - p[1], q[0] - p[0])
            buckets.setdefault((int(p[0] // B), int(p[1] // B)), []).append((p[0], p[1], t))
        for k in range(0, len(pts), 4):
            G.stamp(pts[k][0], pts[k][1], rr, reach)

    def nearest(x, y, rmn):
        bi, bj = int(x // B), int(y // B)
        best, bp = 1e9, None
        for rad in range(1, 9):
            for i in range(bi - rad, bi + rad + 1):
                for j in range(bj - rad, bj + rad + 1):
                    for p in buckets.get((i, j), ()):
                        dd = _m.hypot(p[0] - x, p[1] - y)
                        if rmn < dd < best:
                            best, bp = dd, p
            if bp is not None and best < rad * B:
                break
        return bp, best

    draws = []
    for rt in roots:
        w0 = 2.
        add_stem(rt, w0 + 1.5)
        draws.append(("root", rt, w0))
    heap = [(-G.d[i], i) for i in range(len(G.d)) if G.d[i] > rmin]
    _hq.heapify(heap)
    count = 0
    egg_done = egg is None
    while heap and count < max_n:
        nd, i = _hq.heappop(heap)
        cur = G.d[i]
        if cur < -nd - 1e-6:
            if cur > rmin:
                _hq.heappush(heap, (-cur, i))
            continue
        if cur < rmin:
            break
        cx, cy = G.cell(i)
        r = min(rmax, cur / spacing) * rng.uniform(.9, 1.)
        if not egg_done and r > rmin * 1.6:
            egg(cv, cx, cy, r)
            egg_done = True
            G.stamp(cx, cy, r * 1.05, reach)
            continue
        bp, dq = nearest(cx, cy, r * .6)
        if bp is None:
            # nothing to spring from yet: a free root scroll
            sg = rng.choice((-1, 1))
            a0 = rng.uniform(0, 2 * _SPI)
            spine = _C.volute_spine(cx, cy, r, _m.degrees(a0), 1.3, sg < 0, 0, 0, .14)
        else:
            qx, qy, qt = bp
            v = _m.atan2(qy - cy, qx - cx)
            best = None
            for sg in (-1, 1):
                for td in (qt, qt + _SPI):
                    # leave the stem heading td, arrive on the circle tangentially
                    a0 = v - sg * .9
                    Sx, Sy = cx + r * _m.cos(a0), cy + r * _m.sin(a0)
                    ts = a0 + sg * _SPI / 2
                    ch = _m.atan2(Sy - qy, Sx - qx)
                    e1 = abs(_m.atan2(_m.sin(td - ch), _m.cos(td - ch)))
                    e2 = abs(_m.atan2(_m.sin(ts - ch), _m.cos(ts - ch)))
                    sc = e1 + e2 * .8
                    if best is None or sc < best[0]:
                        best = (sc, sg, td, a0, (Sx, Sy), ts)
            _, sg, td, a0, (Sx, Sy), ts = best
            L = _m.hypot(Sx - qx, Sy - qy)
            h1 = L * .45
            tail = _bez((qx, qy), (qx + _m.cos(td) * h1, qy + _m.sin(td) * h1),
                        (Sx - _m.cos(ts) * h1, Sy - _m.sin(ts) * h1), (Sx, Sy), max(4, int(L / 2)))
            sp = _C.volute_spine(cx, cy, r, _m.degrees(a0), rng.uniform(1.55, 1.8), sg < 0, 0, 0, .1)
            spine = tail[:-1] + sp
        w0 = max(1.1, min(2.6, r * .15))
        draws.append(("s", spine, r, sg if bp is not None else sg, w0, rng.randrange(1 << 20)))
        G.stamp(cx, cy, r * 1.02, reach)
        add_stem(spine[:len(spine) * 2 // 3], w0 + .5)
        count += 1
    # leaves grown into whatever gaps remain, each from the nearest stem
    fill = []
    fmin = max(2.6, rmin * .42)
    heap = [(-G.d[i], i) for i in range(len(G.d)) if G.d[i] > fmin]
    _hq.heapify(heap)
    while heap and len(fill) < max_n * 1.6:
        nd, i = _hq.heappop(heap)
        cur = G.d[i]
        if cur < -nd - 1e-6:
            if cur > fmin:
                _hq.heappush(heap, (-cur, i))
            continue
        if cur < fmin:
            break
        cx, cy = G.cell(i)
        bp, dq = nearest(cx, cy, 0.)
        if bp is None or dq > cur * 4 + 6:
            G.stamp(cx, cy, cur, reach)
            continue
        qx, qy, qt = bp
        a = _m.atan2(cy - qy, cx - qx)
        L = min(dq + cur * .9, rmax * 1.25)
        sg = 1 if _m.sin(a - qt) > 0 else -1
        fill.append((qx, qy, a - sg * .35, L, max(1.4, min(L * .36, cur * .8, rmax * .4)), sg, rng.randrange(1 << 20)))
        G.stamp(cx, cy, cur * 1.1, reach)
        G.stamp((qx + cx) / 2, (qy + cy) / 2, dq * .35, reach)
    for qx, qy, a, L, W, sg, sd in fill:
        fine_leaf(cv, qx, qy, a, L, W, sg, sd)
    # paint: smallest (latest) scrolls first, so parents lie over their children; roots on top
    for d in draws[::-1]:
        if d[0] == "s":
            _, spine, r, sg, w0, sd = d
            _fine_scroll(cv, spine, r, sg if sg else 1, w0, _r.Random(sd))
    for d in draws:
        if d[0] == "root":
            _, rt, w0 = d
            R = _C._Rib(rt, [w0] * len(rt), [w0] * len(rt))
            cv.obj([R.outline()], .5)
            cv.line(R.inset(1, lambda u: .55, 0, 1))
            cv.hair(R.contour(-.4, 0, 1, minw=1.5))
    return count


def matte(shape, seed=0, cid=None):
    """The punched matte between fine scrolls: black, punched with fine white dots (2 tiles that
    do not repeat together), so no flat black larger than ~8 px survives."""
    d, (x0, y0, x1, y1) = _shape_d(shape)
    pid = "mt" + format(_C.zlib.crc32(repr((x0, y0, x1, y1, seed)).encode()) & 0xffffff, "x")
    return (f'<defs>{_stip_pat(pid + "a", 7, 6, seed + 1)}{_stip_pat(pid + "b", 10, 5, seed + 2, 1)}</defs>'
            f'<path d="{d}" fill="#000" stroke="none"/>'
            f'<path d="{d}" fill="url(#{pid}a)" stroke="none"/>'
            f'<path d="{d}" fill="url(#{pid}b)" stroke="none"/>')


def gold_border(poly, close=True):
    """Fine gold-line (wire inlay) border following a shape: a 1 px line, a white gap, then a
    0.5 px line outside it. Returns path data pieces (thick, thin) to stroke."""
    return _SD(poly + ([poly[0]] if close else []), tol=.1)


def _offset_poly(poly, d):
    """Offset a convex-ish closed polygon by d (outward positive for a ccw-on-screen? no: uses
    centroid direction)."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i - 1], poly[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = _m.hypot(tx, ty) or 1
        nx, ny = ty / tl, -tx / tl
        p = poly[i]
        if (p[0] - cx) * nx + (p[1] - cy) * ny < 0:
            nx, ny = -nx, -ny
        out.append((p[0] + nx * d, p[1] + ny * d))
    return out


def bead_ring(poly, r=1.5, gap=1.):
    """Beads set along a closed path, cut as dashed strokes (3 elements whatever the count):
    a black ring, the white bead, and a black shading crescent toward lower right."""
    L = sum(_m.hypot(poly[(i + 1) % len(poly)][0] - poly[i][0], poly[(i + 1) % len(poly)][1] - poly[i][1])
            for i in range(len(poly)))
    nb = max(3, int(L / (2 * r + gap)))
    P = L / nb
    d = _SD(poly + [poly[0]], tol=.05)
    da = f'stroke-dasharray="0 {_SN(P)}" stroke-linecap="round" fill="none"'
    sh = _SD([(x + r * .35, y + r * .35) for x, y in poly] + [(poly[0][0] + r * .35, poly[0][1] + r * .35)], tol=.05)
    return (f'<path d="{d}" stroke="#000" stroke-width="{_SN(2 * r + 1)}" {da}/>'
            f'<path d="{d}" stroke="#fff" stroke-width="{_SN(2 * r)}" {da}/>'
            f'<path d="{sh}" stroke="#000" stroke-width="{_SN(max(1., r * .8))}" {da}/>')


def _kell(cx, cy, rx, ry, n=72):
    return [(cx + rx * _m.cos(2 * _SPI * i / n), cy + ry * _m.sin(2 * _SPI * i / n)) for i in range(n)]


def medallion_ring(cx, cy, rx, ry, bead=1.5):
    """An inlaid portrait medallion's frame: gold wire line outside, a beaded ring, a sunk black
    fillet and a fine inner wire. Returns (svg, inner_ellipse_poly) - fill the inner with the scene."""
    o = []
    outer = _kell(cx, cy, rx, ry)
    bw = bead * 2 + 4.5
    o.append(f'<path d="{_SD(outer, True, .1)}" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_SD(_kell(cx, cy, rx - 1.5, ry - 1.5), True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(bead_ring(_kell(cx, cy, rx - 2.5 - bead, ry - 2.5 - bead, 120), bead, .8))
    o.append(f'<path d="{_SD(_kell(cx, cy, rx - bw + .2, ry - bw + .2), True, .1)}{_SD(_kell(cx, cy, rx - bw - 1.6, ry - bw - 1.6)[::-1], True, .1)}" fill="#000" fill-rule="evenodd" stroke="none"/>')
    inner = _kell(cx, cy, rx - bw - 1.6, ry - bw - 1.6)
    o.append(f'<path d="{_SD(inner, True, .1)}" fill="#fff" stroke="none"/>')
    return "".join(o), inner


def wire_frame(x, y, w, h, bead=1.25):
    """A panel frame: an outer 1 px gold line, a white gap, a bead row, a 0.5 px inner wire.
    Returns svg (draw it OVER the field edge)."""
    o = []
    o.append(f'<path d="M{_SN(x + .5)},{_SN(y + .5)}h{_SN(w - 1)}v{_SN(h - 1)}h{_SN(-(w - 1))}z" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def clip_to(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_SD(poly, True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def _kclip(pl, mask, x0, y0, W, H, out):
    """Split polyline pl into the runs not covered by mask, testing every px along it but keeping
    only its own vertices and the break points (so little is left to simplify)."""
    run = []
    px, py = pl[0]

    def free(x, y):
        xi, yi = int(x - x0), int(y - y0)
        return not (0 <= xi < W and 0 <= yi < H and mask[yi][xi])

    if free(px, py):
        run.append((px, py))
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        k = int(abs(dx) + abs(dy))
        state = bool(run)
        for j in range(1, k + 1):
            t = j / (k + 1)
            x, y = px + dx * t, py + dy * t
            f = free(x, y)
            if f != state:
                if f:
                    run = [(x, y)]
                else:
                    run.append((x, y))
                    if len(run) > 1:
                        out.append(run)
                    run = []
                state = f
        f = free(q[0], q[1])
        if f:
            if not state:
                run = []
            run.append(q)
        else:
            if state and len(run) > 0:
                run.append(q)
                if len(run) > 1:
                    out.append(run)
            run = []
        px, py = q
    if len(run) > 1:
        out.append(run)


def _radial(pts, d):
    """Drop points closer than d to the last kept one (keeps the ends): a cheap pre-thinning so
    the Douglas-Peucker pass has little left to do."""
    if len(pts) < 4:
        return pts
    out = [pts[0]]
    lx, ly = pts[0]
    d2 = d * d
    for p in pts[1:-1]:
        if (p[0] - lx) ** 2 + (p[1] - ly) ** 2 >= d2:
            out.append(p)
            lx, ly = p
    out.append(pts[-1])
    return out


class KCanvas(_C.Canvas):
    """The house Canvas, emitting path data in half-px units (one device pixel): the same
    occlusion, about a quarter fewer bytes, so the fine field fits the budget."""

    def svg(self):
        if not self.objs:
            return ""
        C = _C
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for w, lines in strokes.items():
                for pl in lines:
                    _kclip(pl, mask, x0, y0, W, H, out[w])
            if ow:
                for poly in polys:
                    _kclip(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                C._fill_mask(poly, mask, x0, y0, W, H)
        q = C._Q
        C._Q = 2
        try:
            T = ' transform="scale(.5)"'
            res = []
            pen = C._Pen()
            for polys, _, _ in self.objs:
                for poly in polys:
                    pen.add(_radial(poly if C._area(poly) >= 0 else poly[::-1], 1.1), True, .7)
            if pen.o:
                res.append(f'<path{T} d="{pen.d()}" fill="#fff" stroke="none"/>')
            for w in (.5, 1., 1.5):
                if out[w]:
                    pen = C._Pen()
                    for pl in out[w]:
                        pen.add(_radial(pl, 1.1), False, .6)
                    res.append(f'<path{T} d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_SN(w * 2)}"/>')
        finally:
            C._Q = q
        return "".join(res)


# ------------------------------------------------------------------------------------------------
# stroke lettering (paths only): serifed capitals on a 4 x 6 grid, drawn 1.5 px with a cut shadow
# ------------------------------------------------------------------------------------------------
_KG = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.8, 4), (3.2, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.3), (2.3, 3.3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(0, 0), (0, 6)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.3, 2.7), (4, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)], [(2.6, 4.6), (4.2, 6.4)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2.4), (3.8, 6), (5, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2.3, 0), (2.3, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "6": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6),
           (4, 5), (4, 4), (3, 3)]],
    "9": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (4, 3)]],
    "-": [[(.5, 3), (3.5, 3)]],
    ".": [[(1, 5.6), (1, 6)]],
    "&": [[(4, 6), (1, 2), (1, .8), (2, 0), (3, .8), (3, 1.8), (0, 4.4), (0, 5.2), (1, 6), (2.6, 6), (4, 4)]],
    "'": [[(1, 0), (.7, 1.5)]],
    "*": [[(2, 1.5), (2, 4.5)], [(.7, 2.2), (3.3, 3.8)], [(3.3, 2.2), (.7, 3.8)]],
    "%": [[(0, 6), (4, 0)], [(.2, .3), (1.4, .3), (1.4, 1.7), (.2, 1.7), (.2, .3)],
          [(2.6, 4.3), (3.8, 4.3), (3.8, 5.7), (2.6, 5.7), (2.6, 4.3)]],
    "?": [[(.2, 1.2), (1, .1), (2.6, 0), (3.6, .9), (3.4, 2.1), (2, 3), (2, 4.2)], [(2, 5.6), (2, 6)]],
    "!": [[(1, 0), (1, 4.2)], [(1, 5.6), (1, 6)]],
}
_SERIF = set("ABDEFHIKLMNPRTUVWXYZ1")


def _kgw(ch):
    if ch == " ":
        return 2.4
    g = _KG.get(ch)
    return max(p[0] for s in g for p in s) if g else 3.


def ktext_width(s, size):
    k = size / 6.
    return sum((_kgw(c) + 1.9) * k for c in s) - 1.9 * k


def kletters(s, x, y, size, along=None):
    """Polylines for s, cap height size, top-left (x, y); with serifs on the stems. along(px) ->
    (X, Y, angle) bends the line of text along a curve (the centre of the line)."""
    k = size / 6.
    out = []
    cx = 0.
    for ch in s:
        g = _KG.get(ch, [])
        gw = _kgw(ch)
        strokes = [list(st) for st in g]
        if ch in _SERIF:
            sw = .7
            for st in g:
                for gx, gy in (st[0], st[-1]):
                    if gy in (0, 6) and (gx in (0, 4, 5, 2.3, 2) or ch in "IT1"):
                        strokes.append([(gx - sw, gy), (gx + sw, gy)])
        for stroke in strokes:
            pl = []
            for gx, gy in stroke:
                lx, ly = cx + gx * k, gy * k - size / 2
                if along:
                    mid = cx + gw * k / 2
                    X, Y, a = along(mid)
                    dx = lx - mid
                    pl.append((X + dx * _m.cos(a) - ly * _m.sin(a), Y + dx * _m.sin(a) + ly * _m.cos(a)))
                else:
                    pl.append((x + lx, y + ly + size / 2))
            out.append(pl)
        cx += (gw + 1.9) * k
    return out


def letter_svg(lines, w=1.5, shadow=True):
    d = "".join(_SD(p, tol=0) for p in lines if len(p) > 1)
    o = ""
    if shadow:
        ds = "".join(_SD([(x + .8, y + .8) for x, y in p], tol=0) for p in lines if len(p) > 1)
        o += f'<path d="{ds}" stroke="#000" stroke-width=".5" fill="none"/>'
    return o + f'<path d="{d}" stroke="#000" stroke-width="{_SN(w)}" fill="none" stroke-linecap="square"/>'


def ribbon_text(cx, cy, w, h, text, arch=.05, seed=0):
    """A caption ribbon (house banner) lettered along its face in engraved capitals."""
    bsvg, centre = _C.ribbon_banner(cx, cy, w, h, arch, seed)
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + _m.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    size = min(h * .52, 9.)
    while ktext_width(text, size) > L[-1] * .9 and size > 3:
        size -= .5
    tw = ktext_width(text, size)
    off = (L[-1] - tw) / 2
    dn = 0.

    def along(px):
        s = off + px
        for i in range(1, len(L)):
            if L[i] >= s:
                t = (s - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                a = _m.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
                # sit the capitals on the face, clear of its shadowed upper hem
                return (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t - _m.sin(a) * dn,
                        centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t + _m.cos(a) * dn, a)
        return centre[-1][0], centre[-1][1], 0.

    return bsvg + letter_svg(kletters(text, 0, 0, size, along), 1.5 if size >= 6 else 1., size >= 6)


# ------------------------------------------------------------------------------------------------
# medallion interior: light out of dark, and the arms placeholder
# ------------------------------------------------------------------------------------------------

def vignette_dark(cx, cy, rx, ry, depth=.22, cid="kv"):
    """Darkness gathering at the medallion's rim so the subject glows out of it: lines following
    the oval, swelling in weight toward the rim, cross-hatched in the outer band. Arc path data,
    so it costs almost nothing."""
    def e(a, b):
        return f"M{_SN(cx - a)},{_SN(cy)}a{_SN(a)},{_SN(b)} 0 1,0 {_SN(2 * a)},0a{_SN(a)},{_SN(b)} 0 1,0 {_SN(-2 * a)},0"
    n = int(min(rx, ry) * depth / 1.5)
    heavy = "".join(e(rx - k * 1.5 + .5, ry - k * 1.5 + .5) for k in range(min(2, n)))
    thin = "".join(e(rx - k * 1.5 + .5, ry - k * 1.5 + .5) for k in range(2, n))
    # the outer band crossed by a second set of rings, offset half a pitch and set slightly off
    # centre, so the cross-hatch is laid along the form rather than ruled
    m = int(min(rx, ry) * depth * .5 / 3)
    cross = "".join(e(rx - k * 3 - .25, ry - k * 3 - 1.25) for k in range(m))
    return (f'<path d="{heavy}" stroke="#000" stroke-width="1" fill="none"/>'
            f'<path d="{thin}" stroke="#000" stroke-width=".5" fill="none"/>'
            f'<path d="{cross}" stroke="#000" stroke-width=".5" fill="none" transform="translate(0 .75)"/>')


def arms_placeholder(cx, cy, rx, ry, seed=0):
    """The dedication cartouche held for Parker's family arms (pending): a beaded oval shield
    with crossed drumsticks over a rayed sun. Not invented arms - a placeholder."""
    cv = KCanvas()
    sh = _kell(cx, cy, rx, ry, 48)
    cv.obj([sh], 1.)
    # rayed sun
    sr = min(rx, ry) * .42
    sx, sy = cx, cy - ry * .08
    rays = []
    for k in range(16):
        a = k * _SPI / 8
        r1 = sr * (1.25 if k % 2 else 1.6)
        rays.append([(sx + _m.cos(a) * sr * 1.05, sy + _m.sin(a) * sr * 1.05), (sx + _m.cos(a) * min(r1, rx * .9), sy + _m.sin(a) * min(r1, ry * .85))])
    cv.line(rays)
    disc = _kell(sx, sy, sr, sr, 28)
    cv.obj([disc], 1.)
    cv.hair(_C.hatch_poly(_kell(sx + sr * .25, sy + sr * .25, sr * .7, sr * .7, 20), 45, 1.5))
    # crossed drumsticks with ball tips, over the sun
    L = min(rx, ry) * 1.55
    for sg in (-1, 1):
        a = _SPI / 2 + sg * .62
        p0 = (cx - _m.cos(a) * L * .5, cy + ry * .1 - _m.sin(a) * L * .5)
        p1 = (cx + _m.cos(a) * L * .5, cy + ry * .1 + _m.sin(a) * L * .5)
        hw0, hw1 = max(.9, L * .045), max(.5, L * .02)
        nx, ny = -_m.sin(a), _m.cos(a)
        stick = [(p0[0] + nx * hw0, p0[1] + ny * hw0), (p1[0] + nx * hw1, p1[1] + ny * hw1),
                 (p1[0] - nx * hw1, p1[1] - ny * hw1), (p0[0] - nx * hw0, p0[1] - ny * hw0)]
        cv.obj([stick], .5)
        cv.hair([(p0[0] - nx * hw0 * .4, p0[1] - ny * hw0 * .4), (p1[0] - nx * hw1 * .3, p1[1] - ny * hw1 * .3)])
        tip = (p1[0] + _m.cos(a) * 1.2, p1[1] + _m.sin(a) * 1.2)
        cv.obj([_kell(tip[0], tip[1], max(1.2, L * .05), max(1., L * .042), 10)], .5)
    o = [f'<path d="{_SD(_kell(cx, cy, rx + 4.5, ry + 4.5), True, .1)}" fill="#000" stroke="none"/>',
         bead_ring(_kell(cx, cy, rx + 3, ry + 3, 72), 1.2, .7),
         f'<path d="{_SD(_kell(cx, cy, rx + 5, ry + 5), True, .1)}" fill="none" stroke="#000" stroke-width="1"/>',
         cv.svg()]
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# the King plate: medallion subject in a fine-scroll field, gold-lined and shaped, at every height
# ------------------------------------------------------------------------------------------------

def _cut_rect(x, y, w, h, c):
    return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c), (x + w - c, y + h), (x + c, y + h),
            (x, y + h - c), (x, y + c)]


def _wave_root(x0, y0, x1, y1, amp, n=60, ph=0.):
    out = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + amp * _m.sin(_SPI * 1.6 * t + ph) * _sm(0, .15, t)
        out.append((x, y))
    return out


def _corner_rosette(cv, x, y, r, seed):
    """A small tooled fleuron for a cut corner: four rolled leaves round a beaded boss."""
    rng = _r.Random(seed)
    for k in range(4):
        a = k * _SPI / 2 + _SPI / 4
        fine_leaf(cv, x, y, a, r, r * .38, 1 if k % 2 else -1, rng.randrange(1 << 20), 2, ow=.5)
    cv.obj([_kell(x, y, r * .26, r * .26, 14)], .5)
    cv.hair(_C.hatch_poly(_kell(x + r * .06, y + r * .06, r * .17, r * .17, 10), 45, 1.5))


def king_plate(w, h, ctx, scene, egg=None, caption="", seed=0, front=None, land=None):
    """A complete plate, w x h, King tier.
    scene(X, Y, W, H, mode, clip_poly) -> svg of the subject, drawn inside clip_poly (an oval);
    mode 's' band, 'm' medium, 't' tall. egg(cv, x, y, r) carves the Easter egg into the field.
    caption: ribbon lettering (tall). front: title text for a section front (tall and medium)."""
    rng = _r.Random(seed)
    o = []
    if h < 110:
        mode = "s"
        rim = 4.
        fx0, fy0, fx1, fy1 = 0, rim, w, h - rim
        ry = (fy1 - fy0) / 2 - 1
        rx = min(ry * 1.7, 96.)
        mcx, mcy = w / 2, (fy0 + fy1) / 2
        region = [(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]
        rmin, rmax = 4.5, min(16., (fy1 - fy0) * .3)
        roots = [_wave_root(mcx + s * (rx - 2), mcy, mcx + s * (w / 2 + 4), mcy + s * 2, (fy1 - fy0) * .2, 70, rng.uniform(0, 1))
                 for s in (-1, 1)]
    elif h <= 260:
        mode = "m"
        rim = 5.5
        fx0, fy0, fx1, fy1 = 0, rim, w, h - rim
        ry = (fy1 - fy0) / 2 - 2
        rx = min(ry * 1.32, w * .24)
        mcx, mcy = w / 2, (fy0 + fy1) / 2
        c = min(16., h * .1)
        region = _cut_rect(fx0, fy0, fx1 - fx0, fy1 - fy0, c)
        rmin, rmax = 5., 19.
        roots = [_wave_root(mcx + s * (rx - 3), mcy + ry * .35, mcx + s * (w / 2 + 6), mcy - ry * .15, ry * .32, 80, rng.uniform(0, 1))
                 for s in (-1, 1)]
    else:
        mode = "t"
        rim = 6.
        base_h = min(44., h * .11)
        fx0, fy0, fx1, fy1 = 0, rim, w, h - base_h
        rx = w * .41
        ry = min((fy1 - fy0) / 2 - 22, rx * 1.02)
        mcx, mcy = w / 2, fy0 + 6 + ry + max(0., ((fy1 - fy0) - 2 * ry - 44) * .45)
        c = min(26., h * .06)
        region = _cut_rect(fx0, fy0, fx1 - fx0, fy1 - fy0 + 8, c)
        area = (fx1 - fx0) * (fy1 - fy0)
        rmin, rmax = 5., 19.
        rmin, rmax = 5., 18.
        roots = []
        for s in (-1, 1):
            roots.append(_wave_root(mcx + s * rx * .55, fy1 - 4, mcx + s * (w / 2 + 6), fy0 + (fy1 - fy0) * .3, rx * .22, 90, rng.uniform(0, 1)))
    hole = _kell(mcx, mcy, rx + 3, ry + 3, 64)
    holes = [hole]
    if mode == "t":
        holes.append([(mcx - rx * 1.05, mcy + ry - 6), (mcx + rx * 1.05, mcy + ry - 6), (mcx + rx * 1.05, mcy + ry + 20),
                      (mcx - rx * 1.05, mcy + ry + 20)])
        arms_r = min(18., base_h * .45)
        holes.append(_kell(mcx, fy1 - 2, arms_r * 1.5, arms_r + 6, 32))
    # scroll size scales with the free area, so every height carries about the same count of
    # scrolls (fine and dense, within the byte budget)
    def _pa(p):
        return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
    free = _pa(region) - sum(_pa(hp) for hp in holes)
    kk = max(1., min(1.7, (max(1., free) / 60000.) ** .5))
    if mode == "m":
        rmin, rmax = rmin * kk, rmax * kk
    # the subject first, so the field can be sized to the bytes that remain (the field costs
    # about 1.45 bytes per px^2 of free ground at rmax 20.5, falling as 1/rmax^2)
    ring, inner = medallion_ring(mcx, mcy, rx, ry, 1.25 if mode == "s" else 1.5)
    xs = [p[0] for p in inner]
    ys = [p[1] for p in inner]
    X, Y = min(xs), min(ys)
    W, H = max(xs) - X, max(ys) - Y
    if mode == "t" and land and H > W * land:
        # a landscape keeps landscape proportions: it sits in the lower part of the oval and an
        # engraved sky, banked with cumulus along the seam, fills the dome above it
        H2 = W * land
        sk = KCanvas()
        top_h = H - H2 + 6
        engraved_sky(sk, X, Y, W, top_h, seed + 3, clouds=3)
        for k in range(4):
            bx = X + W * (k + .5) / 4
            sk.obj([_kell(bx, Y + top_h - 3, W * .14, 7.5, 28)], .5)
            for f in (.7, .4):
                sk.hair([(bx + W * .14 * f * _m.cos(a), Y + top_h - 3 + 7.5 * f * _m.sin(a)) for a in [_SPI * (1 + i / 10) for i in range(11)]])
        scene_svg = clip_to(f"ks{seed % 9973}", inner, sk.svg()) + scene(X, Y + H - H2, W, H2, mode, inner)
    else:
        scene_svg = scene(X, Y, W, H, mode, inner)
    budget = 177000 - len(scene_svg) - (34000 if mode == "t" else 9000)
    # what a scroll costs (with its leaves and the leaves grown round it) at this scale
    per = 1400 * (rmax / 19.) ** 1.15
    # 1. the matte ground across the whole plate, then the field of fine scroll grown from the roots
    o.append(matte((0, 0, w, h), seed))
    fseed = rng.randrange(1 << 20)
    maxn = int(max(28, min(150, budget / per)))

    def field(nmax):
        cv = KCanvas()
        scroll_field(cv, region, holes, roots, fseed, rmin=rmin, rmax=rmax, egg=egg, max_n=nmax,
                     g=3. if mode != "t" else 3.5)
        return clip_to(f"kf{seed % 9973}{mode}", region, cv.svg())

    fi = len(o)
    o.append(field(maxn))
    # 2. gold-line borders following the shaped outline, beading on the long edges
    if mode == "s":
        for yy in (0, h - rim):
            o.append(f'<path d="M0,{_SN(yy)}h{_SN(w)}v{_SN(rim)}h{_SN(-w)}z" fill="#fff" stroke="none"/>')
        o.append(bead_ring([(0, 2), (w, 2)], 1., .8).replace('stroke-width="3"', 'stroke-width="3"'))
        o.append(bead_ring([(0, h - 2), (w, h - 2)], 1., .8))
        o.append(f'<path d="M0,{_SN(rim - .5)}h{_SN(w)}M0,{_SN(h - rim + .5)}h{_SN(w)}" stroke="#000" stroke-width="1"/>')
    else:
        outer = [(0, 0), (w, 0), (w, h), (0, h)]
        # the paper round the shaped field: corner pieces carry tooled fleurons on matte
        cc = KCanvas()
        if mode in ("m", "t"):
            cr = c * .55
            for qx, qy in ((c * .38, fy0 + c * .38), (w - c * .38, fy0 + c * .38), (c * .38, region[5][1] - c * .38),
                           (w - c * .38, region[5][1] - c * .38)):
                _corner_rosette(cc, qx, qy, cr, rng.randrange(1 << 20))
        o.append(cc.svg())
        o.append(f'<path d="{_SD(region, True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_SD(_offset_poly(region, -2.), True, 0)}" fill="none" stroke="#fff" stroke-width="1"/>')
        o.append(f'<path d="{_SD(_offset_poly(region, -3.), True, 0)}" fill="none" stroke="#000" stroke-width=".5"/>')
        # top rim: a bead row hanging under the text above
        o.append(f'<path d="M0,0h{_SN(w)}v{_SN(rim)}h{_SN(-w)}z" fill="#fff" stroke="none"/>')
        o.append(bead_ring([(0, rim / 2), (w, rim / 2)], 1.25, .8))
        o.append(f'<path d="M0,{_SN(rim - .5)}h{_SN(w)}" stroke="#000" stroke-width="1"/>')
        if mode == "m":
            o.append(f'<path d="M0,{_SN(h - rim)}h{_SN(w)}v{_SN(rim)}h{_SN(-w)}z" fill="#fff" stroke="none"/>')
            o.append(bead_ring([(0, h - rim / 2), (w, h - rim / 2)], 1.25, .8))
            o.append(f'<path d="M0,{_SN(h - rim + .5)}h{_SN(w)}" stroke="#000" stroke-width="1"/>')
    # 3. the medallion and its subject
    o.append(ring)
    o.append(scene_svg)
    o.append(clip_to(f"kv{seed % 9973}{mode}", inner, vignette_dark(mcx, mcy, W / 2, H / 2, .16 if mode != "s" else .1)))
    # 4. tall: caption ribbon, the arms placeholder, and the base
    if mode == "t":
        if caption:
            o.append(ribbon_text(mcx, mcy + ry + 6, rx * 2.3, 15., caption, .035, rng.randrange(1 << 20)))
        by = fy1 + 4
        o.append(f'<path d="M0,{_SN(by)}h{_SN(w)}v{_SN(h - by)}h{_SN(-w)}z" fill="#fff" stroke="none"/>')
        kb = 6.
        o.append(_C.knurled_bar(0, by, w, kb))
        fr_y, fr_h = by + kb + 1, h - by - kb * 2 - 2
        if fr_h > 8:
            fr = [(0, fr_y), (w, fr_y), (w, fr_y + fr_h), (0, fr_y + fr_h)]
            o.append(matte((0, fr_y, w, fr_h), seed + 5))
            fc = KCanvas()
            scroll_field(fc, fr, [_kell(mcx, fr_y + fr_h / 2, 40, fr_h, 24)],
                         [_wave_root(mcx + s * 36, fr_y + fr_h / 2, mcx + s * (w / 2 + 4), fr_y + fr_h / 2, fr_h * .2, 60)
                          for s in (-1, 1)], rng.randrange(1 << 20), rmin=6., rmax=min(13., fr_h * .5), max_n=16)
            o.append(clip_to(f"kb{seed % 9973}", fr, fc.svg()))
        o.append(_C.knurled_bar(0, h - kb, w, kb))
        o.append(arms_placeholder(mcx, fy1 - 2, arms_r * 1.15, arms_r, seed))
    if front and mode != "s":
        size = min(14., ry * .2)
        tw = ktext_width(front, size)
        while tw > rx * 1.7 and size > 6:
            size -= .5
            tw = ktext_width(front, size)
        ty = mcy - ry * .62 - size / 2 if mode == "t" else mcy - size / 2
        o.append(f'<path d="M{_SN(mcx - tw / 2 - 5)},{_SN(ty - 4)}h{_SN(tw + 10)}v{_SN(size + 8)}h{_SN(-tw - 10)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="M{_SN(mcx - tw / 2 - 3)},{_SN(ty - 2)}h{_SN(tw + 6)}v{_SN(size + 4)}h{_SN(-tw - 6)}z" fill="none" stroke="#000" stroke-width=".5"/>')
        o.append(letter_svg(kletters(front, mcx - tw / 2, ty, size), 1.5, True))
    doc = _C.svg_doc(w, h, "".join(o))
    over = len(doc.encode()) - 201000
    if over > 0:
        fb = len(o[fi])
        o[fi] = field(int(maxn * max(.3, (fb - over - 4000) / fb) * .95))
        doc = _C.svg_doc(w, h, "".join(o))
    return doc


# ------------------------------------------------------------------------------------------------
# Planned forms (edition plan 1.6): every plate is cut to its page's form and shape, never a
# generic band. The subject sits in its shape (oval, roundel, arched top, banner or irregular
# silhouette); fine scroll on punched matte grows out of it in tapering wings that carry the
# ornament to the edges of the box without boxing it in.
# ------------------------------------------------------------------------------------------------

def _shape_poly(shape, cx, cy, sw, sh, seed=0):
    rx, ry = sw / 2, sh / 2
    if shape in ("oval", "roundel"):
        return _kell(cx, cy, rx, ry, 120)
    if shape == "arched":
        rise = min(rx * .9, sh * .5)
        spring = cy - ry + rise
        pts = [(cx - rx, cy + ry), (cx + rx, cy + ry), (cx + rx, spring)]
        for i in range(1, 60):
            a = _SPI * i / 60
            pts.append((cx + rx * _m.cos(a), spring - rise * _m.sin(a)))
        pts.append((cx - rx, spring))
        return pts
    if shape == "banner":
        arch = sh * .14
        n = 48
        top, bot = [], []
        for i in range(n + 1):
            t = i / n
            x = cx - rx + 2 * rx * t
            b = arch * _m.sin(_SPI * t)
            top.append((x, cy - ry + arch - b))
            bot.append((x, cy + ry - b))
        nd = min(sh * .3, rx * .12)
        return (top + [(cx + rx - nd, (top[-1][1] + bot[-1][1]) / 2)] + bot[::-1]
                + [(cx - rx + nd, (top[0][1] + bot[0][1]) / 2)])
    # irregular: a soft, lobed silhouette (a vignette that breaks its own edge)
    rng = _r.Random(seed)
    ph = [rng.uniform(0, 6.3) for _ in range(4)]
    pts = []
    for i in range(140):
        a = 2 * _SPI * i / 140
        c, s = _m.cos(a), _m.sin(a)
        k = (abs(c) ** 3.2 + abs(s) ** 3.2) ** (-1 / 3.2)
        wob = (1 + .04 * _m.sin(3 * a + ph[0]) + .03 * _m.sin(7 * a + ph[1]) + .018 * _m.sin(13 * a + ph[2])
               + .012 * _m.sin(29 * a + ph[3]))
        pts.append((cx + rx * c * k * wob, cy + ry * s * k * wob * (.96 if s > 0 else 1.)))
    return pts


def _form_geom(form, shape, w, h):
    """Where the shape sits in the w x h box: (cx, cy, sw, sh, wing half-height at the shape)."""
    pad = 2.
    sh = h - 2 * pad
    if shape == "roundel":
        sw = min(sh, w * .62)
        sh = min(sh, sw)
    elif shape == "oval":
        frac = .4 if form == "tailpiece" else .5
        sw = min(sh * (1.8 if form == "tailpiece" else 1.42), w * frac)
        sh = min(sh, sw * 1.05)
    elif shape == "arched":
        sw = min(sh * 1.3, w * .52)
        sh = min(sh, sw * 1.45)
    elif shape == "banner":
        sw = w * (.9 if form == "headpiece" else .54)
        sh = min(sh, sw * .3)
    else:
        sw = {"headpiece": w * .97, "tailpiece": w * .52}.get(form, min(w * .6, sh * 1.7))
        sh = min(sh, sw * .95)
    wing = sh * {"headpiece": .36, "tailpiece": .3}.get(form, .34)
    return w / 2, h / 2, sw, sh, wing


def _wing(cx, cy, ex, xe, hw0, hw1, s):
    """A tapering wing from the shape's flank (x = ex) out to the box edge (x = xe): concave top
    and bottom edges that close to a fine point."""
    n = 30
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        x = ex + (xe - ex) * t
        hw = hw1 + (hw0 - hw1) * (1 - t) ** 1.7
        top.append((x, cy - hw))
        bot.append((x, cy + hw))
    return top + bot[::-1]


def form_plate(w, h, ctx, scene, shape="oval", form="vignette", seed=0, arms=False):
    """A planned plate, w x h: the subject in its `shape`, sized for its `form` (vignette, front,
    headpiece, tailpiece, plate), fine scroll wings on punched matte, a gold-wire and bead frame,
    and (arms=True, section fronts) the Somaster dedication cartouche at the foot.
    scene(X, Y, W, H, mode, clip_poly) -> svg; mode 's' (h < 110), 'm' (to 260) or 't'."""
    rng = _r.Random(seed)
    mode = "s" if h < 110 else ("m" if h <= 260 else "t")
    cx, cy, sw, sh, hw0 = _form_geom(form, shape, w, h)
    if arms:
        # leave the foot clear for the dedication cartouche
        ah = max(22., min(46., h * .16))
        sh = min(sh, h - 4 - ah * .55)
        cy = 2 + sh / 2
        hw0 = min(hw0, sh * .34)
    outer = _shape_poly(shape, cx, cy, sw, sh, seed)
    xs = [p[0] for p in outer]
    rx = (max(xs) - min(xs)) / 2
    framed = shape != "irregular"
    bead = 1. if sh < 70 else 1.25 if sh < 160 else 1.5
    bw = bead * 2 + 4.5 if framed else 0.
    inner = _shape_poly(shape, cx, cy, sw - 2 * (bw + 1.6), sh - 2 * (bw + 1.6), seed) if framed else outer
    ixs = [p[0] for p in inner]
    iys = [p[1] for p in inner]
    X, Y = min(ixs), min(iys)
    W, H = max(ixs) - X, max(iys) - Y
    scene_svg = scene(X, Y, W, H, mode, inner)
    o = []
    # 1. wings of fine scroll on matte, carried out to both edges
    hw1 = max(2.5, sh * .05)
    wings = []
    ex0 = rx * .86
    ys_at = []
    for i in range(len(outer)):
        (x1, y1), (x2, y2) = outer[i - 1], outer[i]
        xq = cx + rx * .97
        if (x1 - xq) * (x2 - xq) <= 0 and x1 != x2:
            ys_at.append(y1 + (y2 - y1) * (xq - x1) / (x2 - x1))
    wy = cy
    if len(ys_at) >= 2:
        # the wings spring from the flank where the shape is deep enough to take them
        wy = (min(ys_at) + max(ys_at)) / 2
        hw0 = min(hw0, (max(ys_at) - min(ys_at)) / 2 - 2)
    hw0 = max(hw0, 3.)
    for s in (-1, 1):
        ex = cx + s * ex0
        xe = w / 2 + s * (w / 2)
        if abs(xe - ex) > 30:
            wings.append(_wing(cx, wy, ex, xe, hw0, hw1, s))
    rmin = 3.2 if hw0 < 14 else 4. if hw0 < 30 else 4.5
    rmax = max(rmin * 1.6, min(16., hw0 * .62))
    budget = 177000 - len(scene_svg) - 12000
    per = 1400 * (rmax / 19.) ** 1.15
    maxn = int(max(10, min(150, budget / per)))
    fseed = rng.randrange(1 << 20)

    def field(nmax):
        out = []
        for k, wg in enumerate(wings):
            sgn = -1 if wg[0][0] < cx else 1
            root = _wave_root(cx + sgn * rx * .9, wy, wg[len(wg) // 4][0], wy + sgn * 1.5, hw0 * .35, 70, fseed % 7 + k)
            cv = KCanvas()
            scroll_field(cv, wg, [outer], [root], fseed + k, rmin=rmin, rmax=rmax, max_n=max(4, nmax // 2),
                         g=2.5 if hw0 < 20 else 3.)
            out.append(f'<path d="{_SD(wg, True, 0)}" fill="none" stroke="#000" stroke-width="1"/>')
            out.append(clip_to(f"fw{seed % 9973}{mode}{k}", wg, cv.svg()))
        return "".join(out)

    for k, wg in enumerate(wings):
        o.append(matte(wg, seed + k))
    fi = len(o)
    o.append(field(maxn))
    # 2. the frame of the shape: gold wire, a bead row, a sunk black fillet, a fine inner wire
    if framed:
        def ins(d):
            return _shape_poly(shape, cx, cy, sw - 2 * d, sh - 2 * d, seed)
        o.append(f'<path d="{_SD(outer, True, .1)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_SD(ins(1.5), True, .1)}" fill="none" stroke="#000" stroke-width=".5"/>')
        o.append(bead_ring(ins(2.5 + bead), bead, .8))
        o.append(f'<path d="{_SD(ins(bw - .2), True, .1)}{_SD(ins(bw + 1.6)[::-1], True, .1)}" fill="#000" fill-rule="evenodd" stroke="none"/>')
        o.append(f'<path d="{_SD(inner, True, .1)}" fill="#fff" stroke="none"/>')
    else:
        o.append(f'<path d="{_SD(outer, True, .1)}" fill="#fff" stroke="none"/>')
    # 3. the subject, darkening toward its rim so it glows out of the frame
    o.append(scene_svg)
    if framed:
        n = 2 if mode == "s" else 4
        rims = []
        for k in range(n):
            rims.append(_SD(_shape_poly(shape, cx, cy, W - 2 * (.5 + 1.5 * k), H - 2 * (.5 + 1.5 * k), seed), True, .1))
        o.append(f'<path d="{rims[0]}" fill="none" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{"".join(rims[1:])}" fill="none" stroke="#000" stroke-width=".5"/>')
    else:
        # an irregular vignette has no frame: its lines simply stop at a lobed, ragged edge
        pass
    # 4. section fronts: the Somaster arms in a small beaded cartouche at the foot
    if arms:
        import arms as _A
        ah = max(22., min(46., h * .16))
        aw = ah * .86
        ax, ay = cx - aw / 2, h - ah - 1
        plq = _kell(cx, ay + ah / 2, aw / 2 + 4, ah / 2 + 2.5, 48)
        o.append(f'<path d="{_SD(plq, True, .1)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(bead_ring(_kell(cx, ay + ah / 2, aw / 2 + 2.2, ah / 2 + .8, 64), .75, .7))
        o.append(f'<g transform="translate({_SN(ax)} {_SN(ay)})">{_A.arms(aw, ah, seed)}</g>')
    doc = _C.svg_doc(w, h, "".join(o))
    over = len(doc.encode()) - 201000
    if over > 0:
        fb = len(o[fi])
        o[fi] = field(int(maxn * max(.25, (fb - over - 4000) / fb) * .95))
        doc = _C.svg_doc(w, h, "".join(o))
    return doc


# ------------------------------------------------------------------------------------------------
# Easter eggs, carved as a small relief roundel where a scroll would have grown
# ------------------------------------------------------------------------------------------------

def _egg_roundel(cv, x, y, r):
    cv.obj([_kell(x, y, r, r, 40)], 1.)
    cv.hair(_kell(x, y, r - 1.5, r - 1.5, 40) + [(x + r - 1.5, y)])


def _P(x, y, r, a, b):
    return (x + a * r, y + b * r)


def egg_drumsticks(cv, x, y, r):
    """Crossed drumsticks with ball tips over a tiny ride cymbal."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    cy = _kell(x, y + r * .15, r * .62, r * .2, 28)
    cv.obj([cy], .5)
    cv.hair([[_P(x, y + r * .15, r, -.5 * f, 0), _P(x, y + r * .15, r, .5 * f, 0)] for f in (.5, 1.)])
    cv.obj([_kell(x, y + r * .08, r * .1, r * .05, 10)], .5)
    for sg in (-1, 1):
        p0, p1 = _P(x, y, r, -.62 * sg, .62), _P(x, y, r, .55 * sg, -.6)
        cv.obj([[(p0[0] - .8, p0[1]), (p1[0] - .4, p1[1]), (p1[0] + .4, p1[1]), (p0[0] + .8, p0[1])]], .5)
        cv.obj([_kell(p1[0], p1[1], 1.2, 1., 8)], .5)


def egg_notes(cv, x, y, r):
    """A bar of swing: two beamed eighth notes."""
    r = min(r, 13.)
    _egg_roundel(cv, x, y, r)
    for k, (a, b) in enumerate(((-.35, .4), (.3, .25))):
        hx, hy = _P(x, y, r, a, b)
        cv.obj([_kell(hx, hy, r * .16, r * .11, 12)], .5)
        cv.line(_C.hatch_poly(_kell(hx, hy, r * .14, r * .09, 10), 0, .8, .4))
        cv.line([(hx + r * .14, hy), (hx + r * .14, hy - r * .72)])
    cv.heavy([_P(x, y, r, -.21, -.33), _P(x, y, r, .44, -.48)])


def egg_P(cv, x, y, r):
    """A P monogram cut in a roundel."""
    r = min(r, 12.)
    _egg_roundel(cv, x, y, r)
    cv.heavy([_P(x, y, r, -.25, .55), _P(x, y, r, -.25, -.55), _P(x, y, r, .15, -.55), _P(x, y, r, .38, -.38),
              _P(x, y, r, .38, -.12), _P(x, y, r, .15, .02), _P(x, y, r, -.25, .02)])
    cv.hair([_P(x, y, r, -.45, .55), _P(x, y, r, -.05, .55)])


def egg_hood(cv, x, y, r):
    """Mt. Hood, snow cap and shadowed east flank."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    pk = [_P(x, y, r, -.75, .45), _P(x, y, r, -.08, -.6), _P(x, y, r, .05, -.62), _P(x, y, r, .75, .45)]
    cv.obj([pk], .5)
    sh = [_P(x, y, r, .02, -.6), _P(x, y, r, .75, .45), _P(x, y, r, .2, .45), _P(x, y, r, .12, -.1)]
    cv.hair(_C.hatch_poly(sh, 70, 1.5))
    cv.hair(_C.hatch_poly([_P(x, y, r, -.8, .2), _P(x, y, r, .8, .2), _P(x, y, r, .8, .6), _P(x, y, r, -.8, .6)], 0, 1.5))


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron standing in the shallows."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    body = [_P(x, y, r, -.35, -.05), _P(x, y, r, .2, -.2), _P(x, y, r, .45, .05), _P(x, y, r, .05, .18)]
    cv.obj([body], .5)
    cv.hair(_C.hatch_poly(body, 30, 1.5))
    cv.line([_P(x, y, r, -.3, -.05), _P(x, y, r, -.42, -.35), _P(x, y, r, -.25, -.55), _P(x, y, r, -.32, -.62)])
    cv.line([_P(x, y, r, -.34, -.62), _P(x, y, r, -.7, -.56)])
    cv.hair([[_P(x, y, r, .0, .15), _P(x, y, r, -.05, .6)], [_P(x, y, r, .1, .15), _P(x, y, r, .15, .6)]])
    cv.hair([[_P(x, y, r, -.7, .62), _P(x, y, r, .7, .62)], [_P(x, y, r, -.5, .72), _P(x, y, r, .5, .72)]])


def egg_dog(cv, x, y, r):
    """His dog, curled asleep, nose to tail, fur in fine cuts."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    body = _kell(x, y + r * .08, r * .62, r * .42, 24)
    cv.obj([body], .5)
    cv.hair([_kell(x, y + r * .08, r * .62 * f, r * .42 * f, 20, )[:14] for f in (.75, .5)])
    head = _kell(x - r * .32, y - r * .05, r * .24, r * .2, 14)
    cv.obj([head], .5)
    cv.obj([[_P(x, y, r, -.48, -.18), _P(x, y, r, -.4, -.42), _P(x, y, r, -.28, -.2)]], .5)
    cv.line([_P(x, y, r, -.55, .0), _P(x, y, r, -.53, .02)])
    cv.line([_P(x, y, r, .55, .1), _P(x, y, r, .3, .42), _P(x, y, r, -.1, .44)])


def egg_elephant(cv, x, y, r):
    """A Thai elephant, trunk raised, with a patterned saddle cloth."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    body = [_P(x, y, r, -.45, .1), _P(x, y, r, -.35, -.25), _P(x, y, r, .3, -.3), _P(x, y, r, .5, -.05),
            _P(x, y, r, .45, .45), _P(x, y, r, .3, .45), _P(x, y, r, .28, .15), _P(x, y, r, -.2, .15),
            _P(x, y, r, -.22, .45), _P(x, y, r, -.38, .45)]
    cv.obj([body], .5)
    cv.line([_P(x, y, r, -.42, -.05), _P(x, y, r, -.62, .1), _P(x, y, r, -.7, -.2), _P(x, y, r, -.6, -.4)])
    cloth = [_P(x, y, r, -.1, -.28), _P(x, y, r, .25, -.3), _P(x, y, r, .22, .05), _P(x, y, r, -.08, .05)]
    cv.obj([cloth], .5)
    cv.hair(_C.hatch_poly(cloth, 45, 1.5))
    cv.hair([_P(x, y, r, -.3, -.12), _P(x, y, r, -.18, .0)])


def egg_bridge(cv, x, y, r):
    """The St. Johns Bridge: two gothic towers and the cable sag."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    for a in (-.38, .38):
        cv.obj([[_P(x, y, r, a - .07, .35), _P(x, y, r, a - .05, -.5), _P(x, y, r, a, -.62), _P(x, y, r, a + .05, -.5),
                 _P(x, y, r, a + .07, .35)]], .5)
    cv.hair([_P(x, y, r, -.9, -.1)] + [_P(x, y, r, -.38 + .76 * t, -.5 + .5 * math_sin2(t)) for t in [i / 8 for i in range(9)]] + [_P(x, y, r, .9, -.1)])
    cv.line([_P(x, y, r, -.9, .2), _P(x, y, r, .9, .2)])
    cv.hair(_C.hatch_poly([_P(x, y, r, -.9, .35), _P(x, y, r, .9, .35), _P(x, y, r, .9, .8), _P(x, y, r, -.9, .8)], 0, 2))


def math_sin2(t):
    return _m.sin(_SPI * t)


def egg_pinwheel(cv, x, y, r):
    """A Blazers pinwheel: two interlocked swirls of five stripes each."""
    r = min(r, 12.)
    _egg_roundel(cv, x, y, r)
    for sg in (-1, 1):
        cx = x + sg * r * .2
        for k in range(5):
            rr = r * (.14 + .1 * k)
            a0 = _SPI / 2 if sg > 0 else -_SPI / 2
            cv.line([(cx + rr * _m.cos(a0 + t * _SPI), y + rr * _m.sin(a0 + t * _SPI)) for t in [i / 10 for i in range(11)]])


def egg_solar(cv, x, y, r):
    """A tiny solar panel tilted to a rayed sun."""
    r = min(r, 13.)
    _egg_roundel(cv, x, y, r)
    cv.obj([_kell(x + r * .35, y - r * .35, r * .18, r * .18, 12)], .5)
    cv.hair([[_P(x, y, r, .35 + .26 * _m.cos(a), -.35 + .26 * _m.sin(a)), _P(x, y, r, .35 + .4 * _m.cos(a), -.35 + .4 * _m.sin(a))] for a in [k * _SPI / 4 for k in range(8)]])
    pan = [_P(x, y, r, -.65, .1), _P(x, y, r, .1, -.05), _P(x, y, r, .3, .4), _P(x, y, r, -.45, .55)]
    cv.obj([pan], .5)
    cv.hair(_C.hatch_poly(pan, 15, 1.5))
    cv.line([_P(x, y, r, -.18, .48), _P(x, y, r, -.18, .7)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame rising from a scroll."""
    r = min(r, 14.)
    _egg_roundel(cv, x, y, r)
    fl = [_P(x, y, r, -.35, .5), _P(x, y, r, -.4, .0), _P(x, y, r, -.15, -.35), _P(x, y, r, .05, -.65), _P(x, y, r, .1, -.3),
          _P(x, y, r, .38, -.25), _P(x, y, r, .25, .05), _P(x, y, r, .42, .2), _P(x, y, r, .2, .5)]
    cv.obj([fl], .5)
    cv.hair([_P(x, y, r, -.2, .45), _P(x, y, r, -.2, .0), _P(x, y, r, 0, -.3)])
    cv.hair([_P(x, y, r, .05, .45), _P(x, y, r, .1, .1), _P(x, y, r, .25, -.05)])
    spiral_eye(cv, x - r * .05, y + r * .25, r * .14, 1)
# ---- end studio helpers ----


_n, _d = C._n, C._d
PI = math.pi

# ------------------------------------------------------------------------------------------------
# stroke lettering (paths only), grid 4 wide x 6 tall, y down
# ------------------------------------------------------------------------------------------------
_G = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(.7, 4), (3.3, 4)]],
    "B": [[(0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)], [(0, 0), (3, 0), (3.8, .8), (3.8, 2.2), (3, 3)]],
    "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.3), (2.3, 3.3)]],
    "I": [[(0, 0), (0, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2.5, 4), (5, 0), (5, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "W": [[(0, 0), (1.2, 6), (2.5, 2.4), (3.8, 6), (5, 0)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.5)], [(1.3, 2.7), (4, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "1": [[(1, 1), (2.3, 0), (2.3, 6)], [(1, 6), (3.6, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]],
    "3": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1.5, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]],
    "5": [[(4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "6": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)]],
    "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6),
           (4, 5), (4, 4), (3, 3)]],
    "9": [[(0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (4, 3)]],
    "*": [[(1.5, 2.5), (2.5, 3.5)], [(2.5, 2.5), (1.5, 3.5)]],
}


def _gw(ch):
    if ch == " ":
        return 2.6
    if ch == "*":
        return 4.
    return max(p[0] for s in _G.get(ch, [[(0, 0), (4, 0)]]) for p in s)


def text_width(s, size):
    k = size / 6.
    return sum((_gw(c) + 2.) * k for c in s) - 2. * k


def letter_lines(s, x, y, size, along=None):
    """Polylines for string s, cap height `size`, left/top at (x, y). If along is a function
    t(px) -> (X, Y, angle) mapping a horizontal offset to a point on a curve, letters follow it."""
    k = size / 6.
    out = []
    cx = 0.
    for ch in s:
        g = _G.get(ch, [])
        gw = _gw(ch)
        for stroke in g:
            pl = []
            for gx, gy in stroke:
                lx, ly = cx + gx * k, gy * k - size / 2
                if along:
                    mid = cx + gw * k / 2
                    X, Y, a = along(mid)
                    dx = lx - mid
                    pl.append((X + dx * math.cos(a) - ly * math.sin(a), Y + dx * math.sin(a) + ly * math.cos(a)))
                else:
                    pl.append((x + lx, y + ly + size / 2))
            out.append(pl)
        cx += (gw + 2.) * k
    return out


def _polyd(pls, tol=0):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ------------------------------------------------------------------------------------------------
# page facts (read the day's text)
# ------------------------------------------------------------------------------------------------

def _facts(ctx):
    s = (ctx or {}).get("sample", "") or ""
    m = re.search(r"(\d{1,4})\s+days", s)
    days = m.group(1) if m else ""
    m = re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*,\s+([A-Z][a-z]{2})\w*\s+(\d{1,2})", s)
    date = (m.group(2).upper() + " " + m.group(3)) if m else ""
    return days, date


# ------------------------------------------------------------------------------------------------
# small geometry
# ------------------------------------------------------------------------------------------------

def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _ell(cx, cy, rx, ry, n=28, a0=0., a1=2 * PI):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + (0 if a1 - a0 >= 2 * PI - 1e-6 else 1))]


def _H(cv, poly, ang, pitch, phase=0., inset=0., w=.5):
    ls = C.hatch_poly(poly, ang, pitch, phase, inset)
    (cv.hair if w == .5 else cv.line if w == 1 else cv.heavy)(ls)


def _solid(cv, poly):
    """A black mass made of 1 px lines 0.8 apart."""
    cv.line(C.hatch_poly(poly, 0, .8, .4))


# ------------------------------------------------------------------------------------------------
# the scene pieces (all draw into a Canvas, painter's order)
# ------------------------------------------------------------------------------------------------

def _sky(cv, X, Y, W, H, hy, seed=0):
    # engraved sky: graded lines parting round modelled cumulus over the valley
    engraved_sky(cv, X, Y, W, hy - Y + 2, seed, clouds=3 if W > 150 else 2)


def _clouds(cv, X, Y, W, H, hy, rng):
    for k in range(2):
        cx = X + W * (.14 + .72 * k) + rng.uniform(-4, 4)
        cy = Y + (hy - Y) * (.3 + .1 * k)
        rw = W * (.12 - .02 * k)
        rh = rw * .42
        pts = [(cx + rw, cy)]
        ph = rng.uniform(0, 1)
        for i in range(61):
            u = i / 60
            x = cx + rw - 2 * rw * u
            sc = abs(math.sin(PI * (3.5 * u + ph))) ** .5
            pts.append((x, cy - rh * math.sin(PI * u) ** .7 * (.62 + .38 * sc)))
        pts.append((cx - rw, cy))
        cv.obj([pts], .5)
        belly = [(cx - rw, cy), (cx + rw, cy), (cx + rw * .8, cy - rh * .35), (cx - rw * .8, cy - rh * .35)]
        _H(cv, belly, 0, 1.5)
        _H(cv, [(x, y) for x, y in pts], 0, 3, 1.)


def _heron(cv, x, y, s, flip=False):
    """A great blue heron in flight, Sauvie Island style: neck folded back, dagger bill, legs
    trailing straight out behind, broad arched wings on the up-stroke."""
    f = -1 if flip else 1
    P = lambda a, b: (x + f * a * s, y + b * s)
    wing = [P(-1.2, -.3), P(-.2, -2.2), P(1.2, -3.4), P(3.2, -3.9), P(5.2, -3.4), P(4.2, -2.6), P(2.8, -2.2),
            P(1.6, -1.2), P(1.4, -.4)]
    cv.obj([wing], .5)
    _H(cv, wing, 0, 1.5)
    cv.hair([P(.2, -1.6), P(1.6, -2.9), P(3.4, -3.4)])
    body = [P(-2.4, -.4), P(-.8, -1.), P(1.8, -.8), P(3.2, -.2), P(1.8, .5), P(-1.2, .5)]
    cv.obj([body], .5)
    _solid(cv, body)
    cv.heavy([P(-2.2, -.5), P(-3.3, -1.1), P(-2.9, -1.9), P(-3.6, -2.)])
    head = _ell(*P(-3.8, -2.0), .55 * s, .45 * s, 8)
    cv.obj([head], .5)
    _solid(cv, head)
    cv.line([P(-4.2, -2.0), P(-6.2, -1.8)])
    cv.line([P(3.1, -.2), P(7.2, .3)])
    cv.hair([P(3.0, .1), P(7.0, .8)])


def _hood(cv, mx, base, half, top, seed, light_left=False):
    """Mt. Hood: a steep snow cone with a lopsided summit, dark rock ribs and glaciers radiating
    down, its shaded flank hatched along the slope, and dark forested foothills below the snowline."""
    rng = random.Random(seed)
    Hh = base - top

    def wid(y, side):
        t = min(1., max(0., (y - top) / Hh))
        k = 1.0 if side > 0 else 1.12
        return half * k * (.72 * t ** .85 + .28 * t ** 2.5) + 2.6

    ys = [top + Hh * (i / 30) ** 1.2 for i in range(31)]
    right = [(mx + wid(y, 1) + (.6 * math.sin(i * 1.7) if i > 3 else 0), y) for i, y in enumerate(ys)]
    left = [(mx - wid(y, -1) - (.6 * math.sin(i * 2.3) if i > 3 else 0), y) for i, y in enumerate(ys)]
    summit = [(mx - 2.4, top + 1.5), (mx - .8, top), (mx + .8, top + .4), (mx + 2.6, top + 1.4)]
    poly = summit + right[1:] + left[1:][::-1]
    cv.obj([poly], 1.)
    # snowline, ragged, lower on the gullies
    sy = top + Hh * .58
    nz = 18
    zig = []
    for i in range(nz + 1):
        u = i / nz
        x = mx - wid(sy, -1) + (wid(sy, -1) + wid(sy, 1)) * u
        yj = sy + (Hh * .1 * (1 if i % 2 else -.35)) * (.6 + .4 * rng.random())
        zig.append((x, yj))
    zig[0] = (mx - wid(sy, -1), sy)
    zig[-1] = (mx + wid(sy, 1), sy)
    rk = [p for p in right if p[1] > sy]
    lk = [p for p in left if p[1] > sy]
    low = zig + rk + lk[::-1]
    _H(cv, low, 0, 1.5)
    _H(cv, low, 75, 3)
    # shadow flank (east): hatch along the fall line, two densities
    sgn = -1 if light_left else 1
    ridge = [(mx + .8 + sgn * (Hh * .1) * t ** 1.3 + 1.2 * math.sin(t * 11), top + .4 + (sy - top + 2) * t)
             for t in [i / 14 for i in range(15)]]
    edge = right if not light_left else left
    flank = ridge + [p for p in edge if top + 1 < p[1] <= sy + 2][::-1]
    _H(cv, flank, 90 + sgn * 22, 2)
    _H(cv, flank, 90 - sgn * 50, 3)
    cv.heavy(ridge[:10])
    # rock ribs on the lit face: wedges from near the summit down into the snow
    for k in range(6):
        f = (k + .7) / 6.5
        x0 = mx - sgn * (1.5 + f * 2.5)
        y0 = top + 2 + Hh * .05 * k
        L = (sy - y0) * (.55 + .4 * rng.random())
        dx = -sgn * wid(y0 + L, -sgn) * f * .9
        tip = (x0 + dx, y0 + L)
        w0 = .9 + .5 * rng.random()
        wedge = [(x0, y0), (x0 + dx * .5 + w0, y0 + L * .5), tip, (x0 + dx * .5 - w0 * .3, y0 + L * .5)]
        cv.obj([wedge], 0)
        cv.line([(x0, y0), (x0 + dx * .5, y0 + L * .5), tip])
        cv.hair([(x0 + 1.5 * -sgn, y0 + 3), (x0 + dx * .55 + 1.6 * -sgn, y0 + L * .55)])
    # crevasse ticks
    for k in range(10):
        y = top + Hh * (.12 + .32 * rng.random())
        x = mx - sgn * wid(y, -sgn) * rng.uniform(.2, .85)
        cv.hair([(x - 1.5, y), (x + 1.5, y + .4)])


def _trees(cv, x0, x1, y, h, rng, dark=True):
    """A treeline of firs along y: a black-shadowed band of zig-zag crowns."""
    pts = [(x0, y + h)]
    x = x0
    while x < x1:
        tw = rng.uniform(2.4, 4.)
        th = h * rng.uniform(.6, 1.)
        pts += [(x, y + h * .5), (x + tw / 2, y + h - th), (x + tw, y + h * .5)]
        x += tw * .8
    pts.append((x1, y + h))
    cv.obj([pts], .5)
    _H(cv, pts, 0, 1.5 if dark else 2)
    _H(cv, pts, 90, 2)


def _fields(cv, X, Y, W, H, hy, vx):
    """Willamette valley floor: sectors ruled to a vanishing point, alternately ploughed (furrows
    to the vanishing point) and in grass (rows closing toward the horizon), a winding river."""
    g = [(X - 2, hy), (X + W + 2, hy), (X + W + 2, Y + H + 2), (X - 2, Y + H + 2)]
    cv.obj([g], 0)
    bot = Y + H + 2
    bounds = [X - W * 2.2, X - W * .6, X + W * .1, vx - W * .06, vx + W * .2, X + W * .78, X + W * 1.5, X + W * 3]
    rows = []
    yy, step = hy + 1.5, 2.
    while yy < bot:
        rows.append(yy)
        step *= 1.15
        yy += max(2., min(step, 3.))
    for i in range(len(bounds) - 1):
        b0, b1 = bounds[i], bounds[i + 1]
        sec = [(vx + (b0 - vx) * .02, hy), (vx + (b1 - vx) * .02, hy), (b1, bot), (b0, bot)]
        if i in (1, 5):
            # ploughed: furrows to the vanishing point, about 3 px apart at the front
            n = max(2, int(abs(b1 - b0) / 3.))
            cv.hair([[(vx + (b0 + (b1 - b0) * j / n - vx) * .02, hy + .5), (b0 + (b1 - b0) * j / n, bot)] for j in range(n + 1)])
        else:
            ls = []
            for ry in rows:
                t = (ry - hy) / (bot - hy)
                xa, xb = vx + (b0 - vx) * t, vx + (b1 - vx) * t
                ls.append([(xa, ry), (xb, ry)])
            cv.hair(ls)
        cv.hair([sec[0], sec[3]])


def _river(cv, X, Y, W, H, hy):
    pts_l, pts_r = [], []
    for i in range(21):
        t = i / 20
        y = hy + 1 + (Y + H + 2 - hy) * t ** 1.4
        cx = X + W * (.12 + .1 * math.sin(t * 5.2 + .4)) - W * .1 * t
        hw = 1 + W * .07 * t ** 1.3
        pts_l.append((cx - hw, y))
        pts_r.append((cx + hw, y))
    poly = pts_l + pts_r[::-1]
    cv.obj([poly], .5)
    _H(cv, poly, 0, 3, 1.)
    cv.hair(pts_r)


def _road(cv, X, Y, W, H, hy, vx):
    p = [(vx - 1, hy + 1), (vx + 1, hy + 1), (vx + W * .16, Y + H + 2), (vx - W * .05, Y + H + 2)]
    cv.obj([p], .5)
    _H(cv, p, 90, 3)


def _dropbox(cv, bx, base, s, rng, label=True):
    """An Oregon official ballot drop box: steel cabinet on a plinth, sloped hood over the slot,
    a ballot envelope going in. s = width of the front face."""
    bh = s * 1.25           # cabinet height
    d = s * .32             # side depth (seen to the right)
    dy = d * .45
    top = base - bh - s * .18
    # cast shadow on the ground, falling right
    sh = [(bx + s, base), (bx + s + d, base - dy), (bx + s + d + s * .9, base - dy * .2), (bx + s * 1.6, base + s * .14),
          (bx, base + s * .1)]
    cv.obj([sh], 0)
    _H(cv, sh, 0, 1.5)
    _H(cv, sh, 90, 3)
    # plinth
    pl = [(bx - s * .06, base - s * .18), (bx + s * 1.06, base - s * .18), (bx + s * 1.06, base), (bx - s * .06, base)]
    pls = [(bx + s * 1.06, base - s * .18), (bx + s * 1.06 + d, base - s * .18 - dy), (bx + s * 1.06 + d, base - dy),
           (bx + s * 1.06, base)]
    cv.obj([pl], 1.)
    _H(cv, pl, 0, 2)
    cv.obj([pls], 1.)
    _solid(cv, pls)
    # side of the cabinet (in shadow)
    side = [(bx + s, top), (bx + s + d, top - dy), (bx + s + d, base - s * .18 - dy), (bx + s, base - s * .18)]
    cv.obj([side], 1.)
    _H(cv, side, 90, 1.5)
    _H(cv, side, 30, 2)
    # front face: brushed steel, vertical rules, darker toward the corner
    fr = [(bx, top), (bx + s, top), (bx + s, base - s * .18), (bx, base - s * .18)]
    cv.obj([fr], 1.)
    _H(cv, [(bx + s * .62, top), (bx + s, top), (bx + s, base - s * .18), (bx + s * .62, base - s * .18)], 90, 2, .5)
    _H(cv, [(bx + s * .82, top), (bx + s, top), (bx + s, base - s * .18), (bx + s * .82, base - s * .18)], 0, 2)
    _H(cv, [(bx, top), (bx + s * .62, top), (bx + s * .62, base - s * .18), (bx, base - s * .18)], 90, 3, .5)
    cv.hair([[(bx + 1.5, top + 1.5), (bx + 1.5, base - s * .18 - 1.5)]])
    # door seam and handle
    cv.line([(bx + s * .08, top + bh * .42), (bx + s * .92, top + bh * .42)])
    hx = bx + s * .5
    hd = [(hx - s * .09, top + bh * .48), (hx + s * .09, top + bh * .48), (hx + s * .09, top + bh * .52),
          (hx - s * .09, top + bh * .52)]
    cv.obj([hd], .5)
    _solid(cv, hd)
    # label plate on the door: a ballot box tick and VOTE lettering
    if label:
        lx, ly, lw, lh = bx + s * .14, top + bh * .58, s * .72, bh * .3
        lab = _rect(lx, ly, lw, lh)
        cv.obj([lab], 1.)
        _H(cv, lab, 0, 3, .5, inset=.3)
        size = min(lh * .42, lw / 4.4 * .9)
        tw = text_width("VOTE", size)
        if size >= 3.5:
            ll = letter_lines("VOTE", lx + (lw - tw) / 2, ly + lh * .14, size)
            cv.obj([_rect(lx + (lw - tw) / 2 - 1.5, ly + lh * .1, tw + 3, size + 2)], 0)
            cv.line(ll)
            # little star rule below
            cv.hair([(lx + 2, ly + lh * .78), (lx + lw - 2, ly + lh * .78)])
    # hood over the slot, sloping back
    hood_f = [(bx - s * .05, top - s * .02), (bx + s * 1.05, top - s * .02), (bx + s * 1.05, top + s * .05),
              (bx - s * .05, top + s * .05)]
    hr = s * .22
    hood_t = [(bx - s * .05, top - s * .02), (bx + s * 1.05, top - s * .02), (bx + s * 1.05 + d, top - s * .02 - dy - hr),
              (bx - s * .05 + d, top - s * .02 - dy - hr)]
    hood_s = [(bx + s * 1.05, top - s * .02), (bx + s * 1.05 + d, top - s * .02 - dy - hr), (bx + s * 1.05 + d, top + s * .05 - dy),
              (bx + s * 1.05, top + s * .05)]
    cv.obj([hood_t], 1.)
    _H(cv, hood_t, 0, 2)
    cv.obj([hood_s], 1.)
    _solid(cv, hood_s)
    # the slot: black mouth under the hood lip
    slot = [(bx + s * .14, top + s * .05), (bx + s * .86, top + s * .05), (bx + s * .86, top + s * .05 + max(2.2, s * .07)),
            (bx + s * .14, top + s * .05 + max(2.2, s * .07))]
    cv.obj([hood_f], 1.)
    _H(cv, hood_f, 0, 1.5)
    cv.obj([slot], 0)
    _solid(cv, slot)
    # the ballot going in (stays above the slot, tilted)
    ew, eh = s * .62, s * .42
    ex, ey = bx + s * .52, top + s * .06
    a = -.32
    ca, sa = math.cos(a), math.sin(a)
    E = lambda u, v: (ex + u * ca - v * sa, ey + u * sa + v * ca)
    env = [E(-ew / 2, 0), E(ew / 2, 0), E(ew / 2, -eh), E(-ew / 2, -eh)]
    cv.obj([env], 1.)
    _H(cv, [E(-ew / 2, 0), E(ew / 2, 0), E(ew / 2, -eh * .35), E(-ew / 2, -eh * .35)], 0, 3, inset=.4)
    cv.hair([E(-ew / 2, -eh), E(0, -eh * .45), E(ew / 2, -eh)])
    # the voter's X
    bxc, byc = E(-ew * .2, -eh * .55)
    k = eh * .28
    for sg in (-1, 1):
        cv.line([(bxc - k, byc + sg * k), (bxc + k, byc - sg * k)])
    # a second ballot already falling in, its edge showing in the slot
    cv.hair([(bx + s * .2, top + s * .085), (bx + s * .45, top + s * .085)])
    return top - s * .3 - dy


def _capitol(cv, cx, base, s, rng):
    """The Oregon State Capitol: marble wings, colonnaded front, a fluted cylindrical drum and
    lantern, the Golden Pioneer on top. s = width of the drum."""
    # wings
    ww = s * 3.4
    wh = s * .62
    wings = _rect(cx - ww / 2, base - wh, ww, wh)
    cv.obj([wings], 1.)
    _H(cv, wings, 0, 3, .5)
    # windows: rows of dark slits
    rows = []
    for r in range(2):
        yy = base - wh * (.78 - .4 * r)
        x = cx - ww / 2 + 4
        while x < cx + ww / 2 - 4:
            if abs(x - cx) > s * .75:
                rows.append(_rect(x, yy, 1.6, wh * .24))
            x += 4.
    cv.obj(rows, 0)
    for p in rows:
        _solid(cv, p)
    cv.line([(cx - ww / 2, base - wh + 2), (cx + ww / 2, base - wh + 2)])
    # front block with colonnade
    fw, fh = s * 1.5, s * .92
    fb = _rect(cx - fw / 2, base - fh, fw, fh)
    cv.obj([fb], 1.)
    _H(cv, _rect(cx - fw / 2, base - fh, fw, fh * .22), 0, 2)
    cols = []
    for i in range(7):
        x = cx - fw / 2 + fw * (i + .5) / 7
        cols.append(_rect(x - 1.2, base - fh * .74, 2.4, fh * .58))
    gaps = []
    for i in range(6):
        x0 = cx - fw / 2 + fw * (i + .5) / 7 + 1.2
        x1 = cx - fw / 2 + fw * (i + 1.5) / 7 - 1.2
        gaps.append(_rect(x0, base - fh * .74, x1 - x0, fh * .58))
    cv.obj(gaps, 0)
    for g in gaps:
        _H(cv, g, 0, 1.5)
        _H(cv, g, 90, 2)
    # steps
    for k in range(4):
        sy = base - fh * .16 + k * fh * .04
        cv.hair([(cx - fw / 2 - k * 2, sy), (cx + fw / 2 + k * 2, sy)])
    # drum
    dh = s * 1.05
    dt = base - fh - dh
    drum = _rect(cx - s / 2, dt, s, dh)
    cv.obj([drum], 1.)
    fl = []
    for i in range(1, 22):
        t = i / 22
        x = cx - s / 2 * math.cos(PI * t)
        fl.append([(x, dt + dh * .12), (x, dt + dh * .92)])
    cv.hair(fl)
    sh = _rect(cx + s * .18, dt, s * .32, dh)
    _H(cv, sh, 0, 2)
    cv.line([(cx - s / 2, dt + dh * .1), (cx + s / 2, dt + dh * .1)])
    cv.line([(cx - s / 2, dt + dh * .94), (cx + s / 2, dt + dh * .94)])
    # stepped cap and lantern
    cap = [(cx - s * .5, dt), (cx - s * .38, dt - s * .1), (cx + s * .38, dt - s * .1), (cx + s * .5, dt)]
    cv.obj([cap], 1.)
    _H(cv, cap, 0, 2)
    lw, lh = s * .3, s * .3
    lan = _rect(cx - lw / 2, dt - s * .1 - lh, lw, lh)
    cv.obj([lan], 1.)
    _H(cv, lan, 90, 2)
    _H(cv, _rect(cx + lw * .1, dt - s * .1 - lh, lw * .4, lh), 0, 1.5)
    # the Golden Pioneer: a striding axeman in gilt (white figure, black shading)
    py = dt - s * .1 - lh
    ph = s * .42
    fig = [(cx - ph * .12, py), (cx + ph * .14, py), (cx + ph * .12, py - ph * .55), (cx + ph * .18, py - ph * .75),
           (cx + ph * .06, py - ph * .86), (cx - ph * .1, py - ph * .76), (cx - ph * .14, py - ph * .5)]
    head = _ell(cx + ph * .02, py - ph * .93, ph * .09, ph * .09, 10)
    cv.obj([fig, head], 1.)
    _H(cv, fig, 90, 1.5, .25)
    cv.line([(cx - ph * .2, py - ph * .95), (cx + ph * .2, py - ph * .55)])  # axe handle over shoulder
    axe = [(cx - ph * .2, py - ph * .95), (cx - ph * .3, py - ph * .85), (cx - ph * .25, py - ph * 1.05)]
    cv.obj([axe], .5)
    _solid(cv, axe)
    return dt


def _heron_vane(cv, x, y, s):
    """Easter egg: a heron weathervane on the drop box's hood, bill into the wind."""
    cv.line([(x, y), (x, y - s * 1.1)])
    cv.hair([(x - s * .32, y - s * .45), (x + s * .32, y - s * .45)])
    cv.obj([_ell(x, y - s * .45, s * .05 + .6, s * .05 + .6, 8)], 1.)
    hy = y - s * 1.1
    k = s * .5
    body = [(x - k * .7, hy - k * .1), (x - k * .2, hy - k * .45), (x + k * .35, hy - k * .4), (x + k * .5, hy - k * .2),
            (x + k * .25, hy + k * .05), (x - k * .3, hy + k * .05)]
    cv.obj([body], 1.)
    _H(cv, body, 30, 1.5)
    cv.line([(x + k * .35, hy - k * .4), (x + k * .2, hy - k * .8), (x + k * .45, hy - k * 1.05), (x + k * .6, hy - k * 1.05)])
    cv.line([(x + k * .6, hy - k * 1.05), (x + k * 1.15, hy - k * .95)])
    cv.hair([(x - k * .05, hy + k * .05), (x - k * .05, hy + k * .35)])
    cv.hair([(x + k * .12, hy + k * .05), (x + k * .12, hy + k * .35)])


def _scene(X, Y, W, H, mode, seed, field_d):
    """The oval vignette: an Oregon ballot drop box taking a ballot on the edge of the valley
    fields, Mt. Hood beyond, a heron weathervane on the box's hood. Every surface engraved."""
    rng = random.Random(seed)
    cv = KCanvas()
    hy = Y + H * (.56 if mode != "t" else .6)
    _sky(cv, X, Y, W, H, hy, seed)
    _hood(cv, X + W * .3, hy + 1, W * .36, Y + H * (.2 if mode != "s" else .25), seed, light_left=False)
    _trees(cv, X - 2, X + W + 2, hy - H * .04, H * .045, rng)
    vx = X + W * .3
    _fields(cv, X, Y, W, H, hy, vx)
    _river(cv, X, Y, W, H, hy)
    s = min(W * .22, H * .33)
    bx = X + W * .56 - s / 2
    vy = _dropbox(cv, bx, Y + H * .95, s, rng, label=mode != "s")
    _heron_vane(cv, bx + s * 1.1, vy + s * .1, s * .4)
    body = cv.svg()
    cid = C._uid("civfield", X, Y, W, H, mode)
    return f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


# ------------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex so the cartouche field and every margin is engraved)
# ------------------------------------------------------------------------------------------------

def _field(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return a, b, _d(C._superellipse(cx, cy, a, b), True, 0)


def _layout_band(w, h, seed, ctx):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.5, 110)
    o.append(C._clip(C._uid("cvb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    fd = _d(_ell(cx, cy, rx - 4.5, ry - 4.5, 64), True, 0)
    k = .7071
    iw, ih = (rx - 4.5) * 2 * k * 1.15, (ry - 4.5) * 2 * k * 1.1
    o.append(_scene(cx - iw / 2, cy - ih / 2, iw, ih, "s", seed, fd).replace(
        "<g clip", f'<path d="{fd}" fill="{C.pat("L")}" stroke="none"/><g clip', 1))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
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
    cw = min(w * .42, gh * 1.75)
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
    o.append(C._clip(C._uid("cvm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, "m", seed, fd))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _banner_letters(centre, text, h):
    if not text:
        return ""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.hypot(centre[i][0] - centre[i - 1][0], centre[i][1] - centre[i - 1][1]))
    size = min(h * .5, 9.)
    tw = text_width(text, size)
    off = (L[-1] - tw) / 2

    def along(px):
        s = off + px
        for i in range(1, len(L)):
            if L[i] >= s:
                t = (s - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                a = math.atan2(centre[i][1] - centre[i - 1][1], centre[i][0] - centre[i - 1][0])
                return (centre[i - 1][0] + (centre[i][0] - centre[i - 1][0]) * t,
                        centre[i - 1][1] + (centre[i][1] - centre[i - 1][1]) * t, a)
        return centre[-1][0], centre[-1][1], 0.

    ll = letter_lines(text, 0, 0, size, along)
    return f'<path d="{_polyd(ll)}" stroke="#000" stroke-width="1.5" fill="none"/>'


def _layout_tall(w, h, seed, ctx):
    days, date = _facts(ctx)
    rng = random.Random(seed)
    o = []
    # the whole room is cut away first: no paper shows anywhere
    o.append(C.dark_ground((0, 0, w, h), "M"))
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    em = 9.
    o.append(C.egg_and_dart(0, 0, w, em))
    px0, py0 = 6., em + 5
    pw = w - 12
    ph = h - py0 - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .46, ph * .7
    cx, cy = w / 2, py0 + ph * .47
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
                   max_n=5, edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("cvt", w, h, seed), px0, py0, pw, ph, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b, fd = _field(cx, cy, cw, ch)
    o.append(_scene(cx - a, cy - b, 2 * a, 2 * b, "t", seed, fd))
    o.append(C.palmette(cx, cy - ch / 2 + 6, min(ch * .14, 40), True, rng.randrange(1 << 20)))
    bh = min(17, ph * .055)
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .5, cw * 1.5, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_letters(centre, ("VOTE " + date) if date else "VOTE BY MAIL", bh))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    # the tablet: ruled, lettered with today's countdown
    o.append(f'<path d="M{_n(tx + 2.5)},{_n(ty + 2.5)}h{_n(tw - 3.5)}v{_n(th - 3.5)}h{_n(-(tw - 3.5))}z" fill="{C.pat("L")}" stroke="none"/>')
    label = (days + " DAYS") if days else "OREGON VOTES"
    size = min(th * .6, 14.)
    if size >= 4:
        txw = text_width(label, size)
        lx, ly = tx + (tw - txw) / 2, ty + (th - size) / 2 + .5
        o.append(f'<path d="M{_n(lx - 3)},{_n(ly - 1.5)}h{_n(txw + 6)}v{_n(size + 3)}h{_n(-(txw + 6))}z" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{_polyd(letter_lines(label, lx, ly, size))}" stroke="#000" stroke-width="1.5" fill="none"/>')
        o.append(f'<path d="{_polyd(letter_lines(label, lx + .9, ly + .9, size))}" stroke="#000" stroke-width=".5" fill="none"/>')
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C._clip(C._uid("cvf", w, h, seed), 0, fy, w, fh - 2,
                         C.dark_ground((0, fy, w, fh), "G") +
                         C.scroll_band(w * .02, fy, w * .96, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M0,{_n(h - 1)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    days, date = _facts(ctx)

    def scene(X, Y, W, H, mode, inner):
        return _scene(X, Y, W, H, mode, seed, _d(inner, True, 0))

    # the edition plan: a vignette of about a fifth of the sheet, an oval
    return form_plate(w, h, ctx, scene, "oval", "vignette", seed)
