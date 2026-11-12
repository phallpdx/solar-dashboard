"""today-01 "Good morning" plate. Per the edition plan: a headpiece of about a tenth of the sheet,
an irregular band above the title, the data being the hero. Today's sky as it actually is (read
from the page: sun, part cloud, cloud or rain) over the Multnomah Channel, Mt. Hood far off, and
the island barn with its flag up. Easter egg: the barn's weather vane is a heron."""
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

from engraving_codex import Canvas, hatch_poly, pat, _n, _d, _ell_pts, _Rib, _clip, _uid

TAU = math.tau


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _xf(pts, ox, oy, s, flip=1):
    return [(ox + flip * x * s, oy + y * s) for x, y in pts]


def _solid(cv, poly, pitch=.8, ang=0):
    cv.line(hatch_poly(poly, ang, pitch))


def _cloud_poly(x0, x1, base, puffs, sag=1.5):
    """Upper envelope of puffs [(cx, r)] sitting on a slightly sagging base line."""
    top = []
    x = x0
    while x <= x1 + .01:
        best = base
        for cx, r in puffs:
            dx = x - cx
            if abs(dx) < r:
                yy = base - r * .55 - math.sqrt(r * r - dx * dx) * .75
                best = min(best, yy)
        top.append((x, best))
        x += 1.
    bot = [(x, base + sag * math.sin(math.pi * (x - x0) / max(1, x1 - x0))) for x, _ in top[::-1]]
    return top + bot


def _wavy(x0, x1, y, amp, per, ph, rng, gap_p=.12, gmin=2, gmax=6, avoid=()):
    """A water line from x0 to x1 broken into runs (sparkle gaps)."""
    out, cur = [], []
    x = x0
    while x <= x1:
        yy = y + amp * math.sin((x / per + ph) * TAU)
        blocked = any(a <= x <= b for a, b in avoid)
        if blocked:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            x += 1
            continue
        cur.append((x, yy))
        if rng.random() < gap_p / 3:
            if len(cur) > 1:
                out.append(cur)
            cur = []
            x += rng.uniform(gmin, gmax)
            continue
        x += 1.5
    if len(cur) > 1:
        out.append(cur)
    return out


# ------------------------------------------------------------------------------------------------
# figures
# ------------------------------------------------------------------------------------------------

def _heron(cv, fx, fy, s, rng, detail=1.):
    """Great blue heron standing, facing left, feet at (fx, fy), about s px tall."""
    P = lambda pts: _xf(pts, fx, fy, s)
    lw = max(.5, s * .006)
    # legs (behind body), in the water
    for dx in (0., .07):
        cv.obj([P([(dx - .008, -.03), (dx + .02, -.5), (dx + .036, -.5), (dx + .008, -.03)])], .5)
        cv.line(P([(dx, -.03), (dx + .016, -.27), (dx + .03, -.5)]))
        cv.heavy(P([(dx + .012, -.25), (dx + .02, -.27)]))
    # tail plumes hanging back
    tail = P([(.16, -.47), (.33, -.36), (.31, -.33), (.27, -.35), (.25, -.31), (.12, -.43)])
    cv.obj([tail], 1.)
    cv.hair(hatch_poly(tail, 40, 1.5))
    # body: tilted teardrop
    bc = (fx + .05 * s, fy - .56 * s)
    body = []
    for i in range(40):
        t = TAU * i / 40
        rx = .2 * s * (1 + .18 * math.cos(t))
        body.append((bc[0] + rx * math.cos(t), bc[1] + .085 * s * math.sin(t)))
    body = _rot(body, bc[0], bc[1], math.radians(26))
    cv.obj([body], 1.)
    # feather contour lines following the body (bulino), dense on the belly
    for k in range(1, 8):
        f = 1 - k * .11
        ring = []
        for i in range(0, 41):
            t = math.pi * .05 + math.pi * .9 * i / 40
            rx = .2 * s * f * (1 + .18 * math.cos(t))
            ring.append((bc[0] + rx * math.cos(t), bc[1] + .085 * s * f * math.sin(t) + .012 * s * (1 - f)))
        cv.hair(_rot(ring, bc[0], bc[1], math.radians(26)))
    # the wing: dark folded wing over the back with primaries
    wing = []
    for i in range(30):
        t = math.pi + math.pi * i / 29
        wing.append((bc[0] + .03 * s + .19 * s * math.cos(t), bc[1] - .005 * s + .06 * s * math.sin(t)))
    wing += [(bc[0] + .26 * s, bc[1] + .04 * s), (bc[0] + .2 * s, bc[1] + .045 * s), (bc[0] - .12 * s, bc[1] + .02 * s)]
    wing = _rot(wing, bc[0], bc[1], math.radians(26))
    cv.obj([wing], 1.)
    cv.hair(hatch_poly(wing, 22, 1.5))
    cv.hair(hatch_poly(wing, -30, 3))
    for k in range(4):   # primary tips
        a = bc[0] + (.08 + k * .045) * s
        cv.line(_rot([(a, bc[1] + .0 * s), (a + .07 * s, bc[1] + .045 * s)], bc[0], bc[1], math.radians(26)))
    # neck: an S rib
    neck = [(-.08, -.6), (-.12, -.66), (-.1, -.72), (-.04, -.77), (-.03, -.82), (-.07, -.87), (-.1, -.92), (-.09, -.96)]
    pts = []
    for i in range(len(neck) - 1):
        for j in range(5):
            t = j / 5
            pts.append((neck[i][0] + (neck[i + 1][0] - neck[i][0]) * t, neck[i][1] + (neck[i + 1][1] - neck[i][1]) * t))
    pts.append(neck[-1])
    pts = P(pts)
    nn = len(pts)
    wl = [s * (.06 - .03 * i / nn) for i in range(nn)]
    R = _Rib(pts, wl, wl)
    cv.obj([R.outline()], 1.)
    cv.hair(R.contour(.55, 0., 1.))
    cv.hair(R.contour(.8, 0., 1.))
    cv.line(R.contour(-.5, .05, .95))          # the dark stripe down the front of the neck
    cv.hair(R.contour(-.75, 0., 1.))
    # breast plumes hanging from the neck base
    for k in range(7):
        x0 = fx + (-.17 + k * .02) * s
        cv.hair([(x0, fy - .62 * s), (x0 - .01 * s, fy - (.5 - .01 * k) * s)])
    # head and bill
    hx, hy = fx - .09 * s, fy - .965 * s
    head = _ell_pts(hx, hy, .05 * s, .032 * s, 24)[:-1]
    bill = [(hx - .03 * s, hy - .012 * s), (hx - .25 * s, hy + .022 * s), (hx - .03 * s, hy + .016 * s)]
    cv.obj([bill], 1.)
    cv.hair([(hx - .03 * s, hy + .004 * s), (hx - .22 * s, hy + .02 * s)])
    cv.obj([head], 1.)
    cv.hair(hatch_poly(head, 0, 1.5))
    crest = [(hx - .01 * s, hy - .02 * s), (hx + .16 * s, hy - .035 * s), (hx + .17 * s, hy - .025 * s), (hx + .02 * s, hy - .004 * s)]
    cv.obj([crest], 0)
    _solid(cv, crest, .8, -5)
    eye = _ell_pts(hx - .015 * s, hy - .002 * s, max(1., .009 * s), max(1., .009 * s), 10)[:-1]
    cv.obj([eye], 0)
    cv.line(_ell_pts(hx - .015 * s, hy - .002 * s, max(.5, .005 * s), max(.5, .005 * s), 8))


def _dog(cv, fx, fy, s, facing=-1):
    """Parker's dog, sitting on the bank watching the heron, about s px tall; fur in bulino ruling,
    a floppy black ear, a white eye."""
    T = lambda pts: [(fx - facing * x * s, fy + y * s) for x, y in pts]
    body = T([(.22, 0), (.25, -.2), (.2, -.42), (.1, -.6), (.07, -.8), (.0, -.9), (-.1, -.89), (-.2, -.83),
              (-.29, -.79), (-.3, -.74), (-.22, -.7), (-.12, -.68), (-.12, -.5), (-.1, -.25), (-.1, 0),
              (-.03, 0), (-.02, -.25), (.04, -.15), (.08, 0)])
    tail = T([(.2, -.03), (.36, -.06), (.42, -.02), (.38, .0), (.2, .0)])
    cv.obj([tail], 1.)
    cv.hair(hatch_poly(tail, 80, 1.5))
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 75, 1.5))
    cv.hair(hatch_poly(T([(.25, -.05), (.22, -.4), (.1, -.6), (.12, -.2), (.2, -.02)]), -20, 1.5))
    ear = T([(.03, -.85), (.08, -.66), (.02, -.62), (-.03, -.8)])
    cv.obj([ear], 1.)
    _solid(cv, ear)
    nose = T([(-.3, -.77), (-.27, -.75), (-.3, -.73)])
    cv.obj([nose], 1.)
    _solid(cv, nose, .6)
    ex, ey = T([(-.12, -.8)])[0]
    cv.obj([_ell_pts(ex, ey, 1.2, 1.2, 8)[:-1]], 1.)
    cv.line([(ex - .2, ey), (ex + .2, ey)])
    cv.line(T([(-.1, -.5), (-.1, -.02)]))


def _barn(cv, bx, by, s, rng):
    """Gambrel-roofed island barn, base centre (bx, by), s px tall, boarded walls, a flag on a pole."""
    w = s * 1.15
    wall = [(bx - w / 2, by), (bx - w / 2, by - s * .5), (bx + w / 2, by - s * .5), (bx + w / 2, by)]
    roof = [(bx - w / 2 - s * .05, by - s * .5), (bx - w * .36, by - s * .82), (bx, by - s), (bx + w * .36, by - s * .82),
            (bx + w / 2 + s * .05, by - s * .5)]
    cv.obj([wall], 1.)
    cv.hair(hatch_poly(wall, 90, 1.5))           # board siding
    cv.obj([roof], 1.)
    cv.hair(hatch_poly(roof, 0, 1.5))
    cv.hair(hatch_poly(roof, 60, 3))
    door = [(bx - s * .17, by), (bx - s * .17, by - s * .34), (bx + s * .17, by - s * .34), (bx + s * .17, by)]
    cv.obj([door], 1.)
    cv.hair(hatch_poly(door, 90, 3))
    cv.line([door[0], door[2]])
    cv.line([door[1], door[3]])
    loft = [(bx - s * .08, by - s * .58), (bx - s * .08, by - s * .72), (bx + s * .08, by - s * .72), (bx + s * .08, by - s * .58)]
    cv.obj([loft], 1.)
    _solid(cv, loft)
    # crossed drumsticks leaning on the wall (Easter egg)
    if False:
        sx = bx + w * .34
        cv.line([(sx - s * .08, by), (sx + s * .06, by - s * .3)])
        cv.line([(sx + s * .08, by), (sx - s * .06, by - s * .3)])
        for q in ((sx + s * .06, by - s * .3), (sx - s * .06, by - s * .3)):
            cv.obj([_ell_pts(q[0], q[1], 1.2, 1.2, 8)[:-1]], 1.)
    # flag pole and flag, waving right
    px = bx - w / 2 - s * .35
    top = by - s * 1.55
    cv.obj([[(px - .7, by), (px - .7, top), (px + .7, top), (px + .7, by)]], .5)
    cv.line([(px, by), (px, top)])
    cv.obj([_ell_pts(px, top - 1, 1.3, 1.3, 8)[:-1]], 1.)
    fw, fh = s * .62, s * .38
    def fp(u, v):
        return (px + .8 + u * fw, top + 1 + v * fh + math.sin(u * 5.5) * fh * .12 * u)
    outline = [fp(i / 20, 0) for i in range(21)] + [fp(1 - i / 20, 1) for i in range(21)]
    cv.obj([outline], 1.)
    for k in range(7):   # seven red stripes as dense ruling
        v0, v1 = (2 * k) / 13, (2 * k + 1) / 13
        for vv in (v0 + (v1 - v0) * .25, v0 + (v1 - v0) * .75) if fh > 20 else ((v0 + v1) / 2,):
            cv.hair([fp(i / 20, vv) for i in range(21)] if k < 4 and False else [fp(i / 20, vv) for i in range(21)])
    canton = [fp(i / 20 * .42, 0) for i in range(9)] + [fp(.42 - i / 20 * .42, 7 / 13) for i in range(9)]
    cv.obj([canton], .5)
    cv.hair(hatch_poly(canton, 45, 1.5))
    cv.hair(hatch_poly(canton, -45, 1.5))


def _hood(cv, cx, base, H, rng):
    """Mt. Hood: a sharp summit, glaciers, the east face shaded."""
    L = [(cx - H * 1.9, base), (cx - H * 1.2, base - H * .3), (cx - H * .7, base - H * .55), (cx - H * .35, base - H * .78),
         (cx - H * .12, base - H * .93), (cx, base - H), (cx + H * .08, base - H * .92), (cx + H * .28, base - H * .8),
         (cx + H * .45, base - H * .62), (cx + H * .7, base - H * .5), (cx + H * 1.3, base - H * .25), (cx + H * 2., base)]
    cv.obj([L], 1.)
    # snowline: ragged; below it forested slopes dense
    sl = []
    for i in range(25):
        u = i / 24
        x = cx - H * 1.25 + u * H * 2.3
        y = base - H * (.32 + .1 * math.sin(u * 9 + 1) + .06 * rng.random())
        sl.append((x, y))
    low = [(cx - H * 1.9, base)] + sl + [(cx + H * 2., base)]
    lowp = [p for p in low]
    cv.obj([lowp], 0)
    cv.hair(hatch_poly(lowp, 0, 1.5))
    cv.hair(hatch_poly(lowp, 70, 3))
    cv.hair(L)
    # shaded east face: diagonal hatch from summit
    east = [(cx, base - H), (cx + H * .08, base - H * .92), (cx + H * .28, base - H * .8), (cx + H * .45, base - H * .62),
            (cx + H * .7, base - H * .5), (cx + H * .9, base - H * .42), (cx + H * .1, base - H * .45)]
    cv.hair(hatch_poly(east, 65, 2))
    # glaciers / couloirs on the lit face
    for k in range(6):
        a = cx - H * (.05 + k * .13)
        cv.hair([(cx - H * .02 * k, base - H * (.97 - .05 * k)), (a - H * .05, base - H * (.55 - .02 * k))])
    cv.hair(hatch_poly([(cx, base - H), (cx - H * .7, base - H * .55), (cx - H * .9, base - H * .45), (cx - H * .2, base - H * .5)], 0, 3))


def _treeline(cv, x0, x1, hz, th, rng):
    """Far shore: a row of firs and cottonwoods sitting on the horizon."""
    top = []
    x = x0
    while x <= x1:
        kind = rng.random()
        if kind < .6:   # fir: a spire
            hh = th * rng.uniform(.6, 1.)
            ww = hh * .35
            top += [(x, hz - hh * .25), (x + ww / 2, hz - hh), (x + ww, hz - hh * .25)]
            x += ww * rng.uniform(.6, .9)
        else:           # round cottonwood
            r = th * rng.uniform(.3, .5)
            for i in range(7):
                a = math.pi + math.pi * i / 6
                top.append((x + r + r * math.cos(a), hz - th * .25 - r * .8 + r * .8 * math.sin(a) * 1.2))
            x += 2 * r
    top = [(x0, hz)] + [(min(max(p[0], x0), x1), p[1]) for p in top] + [(x1, hz), (x1, hz + 2), (x0, hz + 2)]
    cv.obj([top], .5)
    cv.hair(hatch_poly(top, 0, 1.5))
    cv.hair(hatch_poly(top, 70, 2))
    cv.line([(x0, hz + 1), (x1, hz + 1)])


# ------------------------------------------------------------------------------------------------
# the scene
# ------------------------------------------------------------------------------------------------

def scene(x, y, w, h, clip_d, seed=0, detail=1.):
    """The page's subject inside the box, clipped to clip_d. Fills every pixel with engraving."""
    rng = random.Random(seed)
    cv = Canvas()
    hz = y + h * (.6 if h > 60 else .62)
    box = [(x - 2, y - 2), (x + w + 2, y - 2), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    # sky: ruled, darkest at the top
    cv.obj([], 0)
    bands = [(y - 2, y + h * .14, 1.5), (y + h * .14, y + h * .34, 2.), (y + h * .34, hz + 1, 3.)]
    for a, b, p in bands:
        cv.hair(hatch_poly([(x - 2, a), (x + w + 2, a), (x + w + 2, b), (x - 2, b)], 0, p, a % p))
    # the sun, low and veiled, golden light breaking through in rays
    sx, sy = x + w * .6, hz - h * .17
    sr = max(5., min(w, h) * .085)
    nr = 15
    for i in range(nr):
        if i % 2:
            continue
        a0 = math.pi + math.pi * (i + .1) / nr
        a1 = math.pi + math.pi * (i + .9) / nr
        R = max(w, h) * 1.2
        wedge = [(sx + sr * 1.15 * math.cos(a0), sy + sr * 1.15 * math.sin(a0)), (sx + R * math.cos(a0), sy + R * math.sin(a0)),
                 (sx + R * math.cos(a1), sy + R * math.sin(a1)), (sx + sr * 1.15 * math.cos(a1), sy + sr * 1.15 * math.sin(a1))]
        cv.obj([wedge], 0)
        am = (a0 + a1) / 2
        for f in (-.28, 0., .28):
            aa = am + f * (a1 - a0)
            cv.hair([(sx + sr * 1.4 * math.cos(aa), sy + sr * 1.4 * math.sin(aa)), (sx + R * math.cos(aa), sy + R * math.sin(aa))])
        cv.hair(hatch_poly(wedge, 0, 3, 1.5))
    disc = _ell_pts(sx, sy, sr, sr, 40)[:-1]
    cv.obj([disc], 1.)
    cv.hair(hatch_poly(disc, 0, 3, .5))
    cv.hair(_ell_pts(sx, sy, sr * 1.15, sr * 1.15, 40))
    # cloud banks, far to near
    clouds = []
    rows = [(.2, .5, 1.0), (.36, .7, .9), (.5, .55, .75)] if h > 90 else [(.32, .6, .8)]
    sun_gap = (sx - sr * 2.2, sx + sr * 2.2)
    for row, (vv, cover, sc) in enumerate(rows):
        base = y + h * vv
        xx = x - w * .1 + rng.uniform(0, w * .15)
        while xx < x + w:
            cw = w * rng.uniform(.18, .34) * sc
            if rng.random() < cover and not (row == len(rows) - 1 and xx < sun_gap[1] and xx + cw > sun_gap[0]):
                r0 = max(4., h * .09 * sc)
                puffs = []
                px = xx
                while px < xx + cw:
                    r = r0 * rng.uniform(.6, 1.15)
                    puffs.append((px + r * .6, r))
                    px += r * rng.uniform(.8, 1.2)
                clouds.append((base, xx, px + r0 * .3, puffs))
            xx += cw * rng.uniform(.9, 1.3)
    for base, cx0, cx1, puffs in clouds:
        poly = _cloud_poly(min(c - r for c, r in puffs) + .5, max(c + r for c, r in puffs) - .5, base, puffs)
        cv.obj([poly], .5)
        # light upper ruling, inset to keep a lit rim
        cv.hair(hatch_poly(poly, 0, 3, 1., inset=2.))
        # dark underside
        under = [(cx0, base - (puffs[0][1] * .5)), (cx1, base - (puffs[-1][1] * .5)), (cx1, base + 3), (cx0, base + 3)]
        rm = max(r for _, r in puffs)
        cv.hair([ln for ln in hatch_poly(poly, 0, 3, 2.5, inset=1.) if ln[0][1] > base - rm * .7])
        cv.hair([ln for ln in hatch_poly(poly, 0, 1.5, 1.75, inset=.5) if ln[0][1] > base - rm * .3])
        # puff rims: a contour just inside each puff's lit top
        for pcx, r in puffs:
            if r > 4:
                pcy = base - r * .55
                arc = [(pcx + r * .8 * math.cos(t), pcy - r * .75 * .8 * math.sin(t))
                       for t in [math.radians(a) for a in range(150, 25, -10)]]
                cv.hair([q for q in arc if q[1] < base - 1])
    # Mt. Hood, beyond the channel
    if h > 70:
        _hood(cv, x + w * .74, hz + 1, h * .26, rng)
    # far shore trees
    _treeline(cv, x - 2, x + w + 2, hz + 1, max(4., h * .1), rng)
    # water
    wy0 = hz + 3
    water = [(x - 2, wy0), (x + w + 2, wy0), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]
    cv.obj([water], 0)
    hx = x + w * .25
    yy = wy0 + 1
    k = 0
    while yy < y + h + 2:
        depth = (yy - wy0) / max(1., y + h - wy0)
        pitch = 2. if depth < .5 else 1.5
        avoid = []
        if yy < wy0 + h * .18:   # the sun's broken reflection
            half = sr * (1.1 - depth)
            avoid = [(sx - half, sx + half)] if k % 2 == 0 else []
        segs = _wavy(x - 2, x + w + 2, yy, .35, 14, rng.random(), rng, .12 + .1 * (1 - depth), avoid=avoid)
        if avoid:
            # short dashes in the reflection column
            dx = sx - avoid[0][0]
            q = sx - dx
            while q < sx + dx:
                L = rng.uniform(1.5, 4)
                segs.append([(q, yy), (q + L, yy)])
                q += L + rng.uniform(1.5, 3)
        cv.hair(segs)
        yy += pitch
        k += 1
    # foreground: the island bank at low tide, mud flats stippled, grass tufts
    by = y + h * .86
    bank = [(x - 2, y + h + 2)]
    for i in range(41):
        u = i / 40
        bank.append((x - 2 + u * (w + 4), by - h * (.05 * math.sin(u * 3.2 + .4) + .04 * (u > .55) * math.sin((u - .55) * 7)) - h * .03 * (u > .6)))
    bank.append((x + w + 2, y + h + 2))
    cv.obj([bank], 1.)
    cv.hair(hatch_poly(bank, 12, 2))
    cv.hair(hatch_poly(bank, -20, 3))
    # mud flat at the water's edge
    for i in range(int(w * .5 * detail)):
        u = rng.random()
        px = x + u * w
        bt = by - h * (.05 * math.sin(u * 3.2 + .4)) + rng.uniform(-1, 1)
        cv.line([(px, bt - 2 + rng.uniform(-1, 1)), (px + rng.uniform(1.5, 3), bt - 2)])
    # grass tufts along the bank's crest
    for i in range(int(w / 3)):
        u = rng.random()
        px = x + u * w
        idx = min(40, int(u * 40 + .5))
        bt = bank[1 + idx][1]
        for j in range(3):
            L = h * rng.uniform(.03, .07)
            a = -math.pi / 2 + rng.uniform(-.5, .5)
            cv.hair([(px + j, bt + 1), (px + j + L * math.cos(a), bt + 1 + L * math.sin(a))])
    # barn with the flag (Veterans Day), dog on the bank
    if h > 70:
        bx = x + w * .84
        bb = bank[1 + int(.84 * 40)][1] + h * .02
        _barn(cv, bx, bb, h * .16, rng)
        _dog(cv, x + w * .6, bank[1 + int(.6 * 40)][1] + h * .02, h * .16, -1)
    # the heron in the shallows, its reflection broken in the water
    if h > 45:
        hs = h * (.52 if h > 120 else .6)
        hy = hz + h * .14
        # reflection
        refl = []
        for k in range(int(hs * .25)):
            ry = hy + 2 + k * 1.5
            L = hs * .12 * (1 - k / (hs * .25))
            refl.append([(hx - L * .5 + rng.uniform(-1, 1), ry), (hx + L * .5 + rng.uniform(-1, 1), ry)])
        cv.line(refl)
        _heron(cv, hx, hy, hs, rng, detail)
        # ripples round the legs
        for k in range(3):
            r = hs * (.04 + .03 * k)
            cv.hair(_ell_pts(hx + hs * .04, hy, r * 2, r * .4, 24)[3:22])
    cid = _uid("v", x, y, w, h, seed)
    return (f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{cv.svg()}</g>')


# ------------------------------------------------------------------------------------------------
# bespoke furniture: the sun crest, the star tablet, the toned banner
# ------------------------------------------------------------------------------------------------

def _sun_crest(cx, cy, r, seed):
    """The rising sun above the cartouche: a half disc with alternating long/short rays, palmette
    fingers springing either side."""
    cv = Canvas()
    for side in (-1, 1):
        C.acanthus_frond(cx + side * r * .7, cy + r * .05, 90 - side * 90 - side * 12, r * 1.9, 3, 30, bend=-side * .9, cv=cv, seed=seed + side)
    rays = []
    for i in range(17):
        a = math.pi + math.pi * (i + .5) / 17
        L = r * (1.75 if i % 2 == 0 else 1.35)
        wd = .07
        rays.append([(cx + r * .9 * math.cos(a - wd), cy + r * .9 * math.sin(a - wd)), (cx + L * math.cos(a), cy + L * math.sin(a)),
                     (cx + r * .9 * math.cos(a + wd), cy + r * .9 * math.sin(a + wd))])
    cv.obj(rays, 1.)
    for ry in rays:
        cv.hair([ry[0], ry[1]])
        cv.hair(hatch_poly(ry, 0, 1.5))
    disc = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in [math.pi + math.pi * i / 30 for i in range(31)]]
    cv.obj([disc], 1.)
    cv.hair(_ell_pts(cx, cy, r * .78, r * .78, 30)[15:31])
    cv.hair(hatch_poly(disc, 0, 2, .5, inset=1.5))
    # a face: two closed eyes and a smile, engraved
    for sx in (-1, 1):
        cv.line([(cx + sx * r * .42 - r * .1, cy - r * .42), (cx + sx * r * .42, cy - r * .36), (cx + sx * r * .42 + r * .1, cy - r * .42)])
    cv.line([(cx - r * .25, cy - r * .16), (cx, cy - r * .08), (cx + r * .25, cy - r * .16)])
    return cv.svg()


def _star(cx, cy, r):
    return [(cx + (r if i % 2 == 0 else r * .42) * math.cos(-math.pi / 2 + math.pi * i / 5),
             cy + (r if i % 2 == 0 else r * .42) * math.sin(-math.pi / 2 + math.pi * i / 5)) for i in range(10)]


def _star_tablet(tx, ty, tw, th):
    """Veterans Day: thirteen white stars on a ruled ground across the tablet."""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="{pat("G")}" stroke="none"/>']
    n = 13
    r = min(th * .36, tw / n * .36)
    d = "".join(_d(_star(tx + tw * (i + .5) / n, ty + th / 2 + r * .1, r), True, 0) for i in range(n))
    o.append(f'<path d="{d}" fill="#fff" stroke="#000" stroke-width=".5"/>')
    # laurel ticks between stars
    t = "".join(f"M{_n(tx + tw * i / n)},{_n(ty + th * .3)}v{_n(th * .4)}" for i in range(1, n))
    o.append(f'<path d="{t}" stroke="#000" stroke-width=".5"/>')
    return "".join(o)


def _banner_face(cx, cy, w, h, arch, centre):
    top = [(px, py - h / 2 + 1.2) for px, py in centre]
    bot = [(px, py + h / 2 - 1.2) for px, py in centre[::-1]]
    face = f'<path d="{_d(top + bot, True, 0)}" fill="{pat("L")}" stroke="none"/>'
    # a row of small stars along the face for the day
    n = 9
    stars = ""
    r = h * .22
    for i in range(n):
        p = centre[int((i + .5) / n * (len(centre) - 1))]
        stars += _d(_star(p[0], p[1], r), True, 0)
    return face + f'<path d="{stars}" fill="#fff" stroke="#000" stroke-width=".5"/>'


# ------------------------------------------------------------------------------------------------
# layouts (from the house frame_plate, adapted: no bare paper, the vignette fills the whole field)
# ------------------------------------------------------------------------------------------------

def _medallion_scene(cx, cy, rx, ry, seed):
    outer = _ell_pts(cx, cy, rx + 1, ry + 1, 64)
    ring = _d(outer, True) + _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64)[::-1], True)
    field = _d(_ell_pts(cx, cy, rx - 2, ry - 2, 64), True)
    o = [f'<path d="{_d(outer, True)}" fill="#fff" stroke="none"/>']
    o.append(scene(cx - rx, cy - ry, rx * 2, ry * 2, field, seed, .6))
    o.append(f'<path d="{ring}" fill="#000" stroke="none" fill-rule="evenodd"/>')
    o.append(f'<path d="{_d(_ell_pts(cx, cy, rx - 3.5, ry - 3.5, 64), True)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(f'<path d="M0,0h{_n(w)}v{_n(top)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>')
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 2.2, 150)
    o.append(_clip(_uid("b", w, h, seed), 0, top, w, gh,
                   C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    o.append(_medallion_scene(w / 2, top + gh / 2, gap / 2, gh / 2 - 1, seed))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"/>')
    return "".join(o)


def _layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.7)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv, main = Canvas(), Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    fx0, fx1, fy0, fy1 = _bbox(field)
    o.append(c)
    o.append(scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, seed, .8))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _bbox(d):
    import re
    # field path is "M x,y l dx,dy ..." in tenths-free numbers; walk it
    nums = re.findall(r"-?\d*\.?\d+", d)
    vals = [float(v) for v in nums]
    x, y = vals[0], vals[1]
    xs, ys = [x], [y]
    for i in range(2, len(vals) - 1, 2):
        x += vals[i]
        y += vals[i + 1]
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)


def _layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = [f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{pat("L")}" stroke="none"/>']
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .7
    cx, cy = w / 2, py0 + ph * .46
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv, main = Canvas(), Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(14, ph * .05), rmax=r1 * .9,
                   max_n=int(6 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    fx0, fx1, fy0, fy1 = _bbox(field)
    o.append(c)
    o.append(scene(fx0, fy0, fx1 - fx0, fy1 - fy0, field, seed, 1.))
    sr = min(ch * .1 + top_free * .5, 34)
    o.append(_sun_crest(cx, cy - ch / 2 + 5, sr, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bw = cw * 1.4
    bsvg, centre = C.ribbon_banner(cx, cy + ch * .47, bw, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_face(cx, cy + ch * .47, bw, bh, .04, centre))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_star_tablet(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_clip(_uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                       C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
    return "".join(o)


def _heron_vane(cv, x, y, s):
    """Easter egg: the barn's weather vane is a heron: a rod with cardinal arms and a heron in
    silhouette on top, bill into the wind."""
    cv.line([(x, y), (x, y - s * 1.1)])
    cv.hair([(x - s * .32, y - s * .45), (x + s * .32, y - s * .45)])
    cv.obj([_ell_pts(x, y - s * .45, s * .05 + .6, s * .05 + .6, 8)[:-1]], 1.)
    hy = y - s * 1.1
    k = s * .5
    body = [(x - k * .7, hy - k * .1), (x - k * .2, hy - k * .45), (x + k * .35, hy - k * .4), (x + k * .5, hy - k * .2),
            (x + k * .25, hy + k * .05), (x - k * .3, hy + k * .05)]
    cv.obj([body], 1.)
    cv.hair(hatch_poly(body, 30, 1.5))
    neck = [(x + k * .35, hy - k * .4), (x + k * .2, hy - k * .8), (x + k * .45, hy - k * 1.05), (x + k * .6, hy - k * 1.05)]
    cv.line(neck)
    cv.line([(x + k * .6, hy - k * 1.05), (x + k * 1.15, hy - k * .95)])
    cv.hair([(x - k * .05, hy + k * .05), (x - k * .05, hy + k * .35)])
    cv.hair([(x + k * .12, hy + k * .05), (x + k * .12, hy + k * .35)])


def _cond(ctx):
    smp = ((ctx or {}).get("sample", "") or "").lower()
    m = re.search(r"(clear|sunny|mostly sunny|partly cloudy|mostly cloudy|cloudy|overcast|fog|showers|rain|drizzle|snow)", smp)
    return m.group(1) if m else "cloudy"


def head_scene(x, y, w, h, seed, cond, mode):
    """The headpiece: today's sky as it is, over the channel and the island barn, whose vane is
    a heron. Every surface engraved: sky, water in broken wavelets, the bank in grass tufts."""
    rng = random.Random(seed)
    cv = KCanvas()
    hz = y + h * .66
    sunny = cond in ("clear", "sunny", "mostly sunny")
    partly = cond == "partly cloudy"
    wet = cond in ("showers", "rain", "drizzle")
    nclouds = 0 if sunny else (2 if partly else 4)
    sx, sy = x + w * .3, y + h * .38
    sr = max(4., h * .16)
    engraved_sky(cv, x - 2, y - 2, w + 4, hz - y + 3, seed + 5, clouds=nclouds, maxc=nclouds,
                 sun=(sx, sy, sr * 1.25) if (sunny or partly) else None)
    if sunny or partly:
        cv.obj([_ell_pts(sx, sy, sr, sr, 32)[:-1]], 1.)
        cv.hair([_ell_pts(sx, sy, sr * .7, sr * .7, 24)])
        for k in range(16):
            a = math.pi * 2 * k / 16
            r1 = sr * (1.9 if k % 2 else 1.5)
            cv.line([(sx + sr * 1.3 * math.cos(a), sy + sr * 1.3 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))])
    if wet:
        # rain falling in slanted broken strokes from the cloud base
        for k in range(int(w / 4)):
            rx_ = x + rng.uniform(0, w)
            ry_ = y + h * rng.uniform(.25, .5)
            cv.hair([(rx_, ry_), (rx_ - 2, ry_ + h * .12)])
    if h > 45:
        _hood(cv, x + w * .18, hz + 1, h * .28, rng)
    _treeline(cv, x - 2, x + w + 2, hz + 1, max(4., h * .1), rng)
    wy0 = hz + 3
    cv.obj([[(x - 2, wy0), (x + w + 2, wy0), (x + w + 2, y + h + 2), (x - 2, y + h + 2)]], 0)
    yy = wy0 + 1.5
    while yy < y + h + 2:
        depth = (yy - wy0) / max(1., y + h - wy0)
        cv.hair(_wavy(x - 2, x + w + 2, yy, .35, 14, rng.random(), rng, .22 + .1 * (1 - depth)))
        yy += 2. if depth < .5 else 1.5
    # the island bank, right, in grass; the barn on it
    bx0 = x + w * .56
    by = y + h * .84
    bank = [(bx0, y + h + 2)] + [(bx0 + (x + w + 2 - bx0) * i / 20, by - h * .06 * math.sin(math.pi * min(1, i / 6))) for i in range(21)] + [(x + w + 2, y + h + 2)]
    cv.obj([bank], 1.)
    meadow_tufts(cv, bx0, by - h * .05, x + w + 2 - bx0, y + h + 2, seed + 3, .9)
    cv.obj([[(bx0 - 2, y + h + 4), (bx0, by), (bx0 + 6, by - h * .05), (bx0 - 6, y + h + 4)]], .5)
    s = h * .42
    bxc = x + w * .76
    _barn(cv, bxc, by - h * .02, s, rng)
    _heron_vane(cv, bxc, by - h * .02 - s, s * .38)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    cond = _cond(ctx)

    def sc(X, Y, W, H, mode, inner):
        return clip_to(f"tdy{mode}{int(H)}", inner, head_scene(X, Y, W, H, seed, cond, mode))

    # the edition plan: a headpiece of about a tenth of the sheet, an irregular band above the title
    return form_plate(w, h, ctx, sc, "irregular", "headpiece", seed)
