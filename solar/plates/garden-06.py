"""garden-06 (Mushroom forecast) plate.

Today's mushroom is the matsutake: white, a thick shaggy ring on the stem, in sandy soil under
Douglas fir in the Cascades, with two weeks of rain on the way; golden chanterelles do well too.
Per the edition plan: a vignette of about a quarter sheet, ARCHED, the matsutake and its buttons
pushing through fir duff under two Douglas firs, a golden chanterelle beside them, Mt. Hood behind
a band of rain clouds. Easter egg: a stump sawn level and laced like a drum (and the dog's paw
print in the duff).
"""
import sys
import math
import random
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
        pitch = 1.8 if t < .2 else 2.2 if t < .55 else 3.
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
        # each billow a modelled dome, painted back to front: its crown left white to the light
        # (upper left), its body turned in arcs that close toward the shadowed lower right, a
        # dark seam of close lines at its base
        for bx, by, br in sorted(bl, key=lambda b: b[2]):
            circ = [(bx + br * _m.cos(a), min(cy + 1., by + br * _m.sin(a))) for a in [2 * _SPI * i / 40 for i in range(40)]]
            cv.obj([circ], .5)
            arcs = []
            k = 0
            rr = br * .9
            while rr > br * .3:
                a0 = -.35 - .25 * k / 4
                a1 = _SPI * (.95 - .04 * k)
                seg = []
                for i in range(15):
                    a = a0 + (a1 - a0) * i / 14
                    px, py = bx + rr * _m.cos(a) + br * .08, by + rr * _m.sin(a) * .9 + br * .1
                    if py < cy:
                        seg.append((px, py))
                if len(seg) > 1:
                    arcs.append(seg)
                k += 1
                rr -= 1.5 if k < 3 else 2. if k < 6 else 3.
            # the lit crown is not left bare: open arcs follow the dome round the top, widening
            # toward the light and broken only at a small highlight (upper left)
            hx, hy = bx - br * .35, by - br * .45
            rr = br * .97
            while rr > br * .2:
                seg = []
                for i in range(19):
                    a = _SPI * (1.02 + .96 * i / 18)
                    px, py = bx + rr * _m.cos(a), by + rr * _m.sin(a) * .92
                    if (px - hx) ** 2 + (py - hy) ** 2 < (br * .22 + 1.5) ** 2 or py > cy:
                        if len(seg) > 1:
                            arcs.append(seg)
                        seg = []
                    else:
                        seg.append((px, py))
                if len(seg) > 1:
                    arcs.append(seg)
                rr -= 4.5
            cv.hair(arcs)
            sh = [(x, max(y, cy - br * .3)) for x, y in circ]
            cv.hair(_C.hatch_poly(sh, 0, 1.5, .3))
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
    """Beads set along a closed path, each a drawn pearl: a white bead ringed in a hairline, a
    swelling crescent of shade toward the lower right and a lit eye left white (two paths)."""
    n = len(poly)
    segs = []
    L = 0.
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        s = _m.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, s, L))
        L += s
    nb = max(3, int(L / (2 * r + gap)))
    P = L / nb
    beads, shade = [], []
    k = 0
    for i in range(nb):
        t = i * P
        while k < len(segs) - 1 and segs[k][3] + segs[k][2] < t:
            k += 1
        a, b, s, l0 = segs[k]
        u = (t - l0) / (s or 1)
        x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        m = 10 if r > 1.2 else 8
        beads.append([(x + r * _m.cos(2 * _SPI * j / m), y + r * _m.sin(2 * _SPI * j / m)) for j in range(m)])
        if r >= .9:
            outer = [(x + r * _m.cos(a_), y + r * _m.sin(a_)) for a_ in [-.4 + 2.4 * j / 6 for j in range(7)]]
            inner = [(x + r * .25 + r * .7 * _m.cos(a_), y + r * .25 + r * .7 * _m.sin(a_))
                     for a_ in [2. - 2.4 * j / 6 for j in range(7)]]
            shade.append(outer + inner)
    o = f'<path d="{"".join(_SD(p, True, 0) for p in beads)}" fill="#fff" stroke="#000" stroke-width="{".5" if r < 1.2 else "1"}"/>'
    if shade:
        o += f'<path d="{"".join(_SD(p, True, 0) for p in shade)}" fill="#000"/>'
    return o


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
# Depth (art direction, Nov 12 second pass): swelling lines and form-following tone. Every stroke
# stays 0.5 / 1 / 1.5 px; a swell is built the burin's way, a 1 px cut flanked by hair cuts laid
# tight against it on the shadow side over the middle of its run, so it thickens and tapers.
# ------------------------------------------------------------------------------------------------

def _offset_pl(pts, d):
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = _m.hypot(tx, ty) or 1.
        out.append((pts[i][0] - ty / L * d, pts[i][1] + tx / L * d))
    return out


def _sub(pts, t0, t1):
    n = len(pts)
    i0, i1 = int(t0 * (n - 1)), int(_m.ceil(t1 * (n - 1)))
    return pts[i0:i1 + 1]


def _dres(pts, step=1.5):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = _m.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(L / step))
        for j in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out


def swell(cv, pts, side=1, weight=2):
    """A swelling cut along pts: 1 px throughout, thickened on `side` (+1 left of travel, -1 right)
    over its middle by `weight` (1-3) hair cuts set .55 px apart, each shorter than the last."""
    if len(pts) < 2:
        return
    pts = _dres(pts, 1.5)
    cv.line(pts)
    spans = ((.12, .88), (.25, .75), (.38, .62))
    for k in range(min(3, weight)):
        sub = _sub(pts, *spans[k])
        if len(sub) > 1:
            cv.hair(_offset_pl(sub, side * .55 * (k + 1)))


def swell_outline(cv, poly, light=(-1., -1.), weight=2):
    """Outline a closed form with a swelling contour: thin where it faces the light, swelling on
    the side away from it (the engraver's shadow line)."""
    n = len(poly)
    if n < 3:
        return
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    lx, ly = light
    L = _m.hypot(lx, ly) or 1.
    lx, ly = lx / L, ly / L
    run = []
    pts = _dres(poly + [poly[0]], 1.5)
    for p in pts:
        dx, dy = p[0] - cx, p[1] - cy
        dl = _m.hypot(dx, dy) or 1.
        if (dx * lx + dy * ly) / dl < -.15:
            run.append(p)
        else:
            if len(run) > 3:
                _swell_in(cv, run, cx, cy, weight)
            run = []
    if len(run) > 3:
        _swell_in(cv, run, cx, cy, weight)


def _swell_in(cv, run, cx, cy, weight):
    # thicken toward the inside of the form
    a, b = run[0], run[-1]
    m = run[len(run) // 2]
    tx, ty = b[0] - a[0], b[1] - a[1]
    side = 1 if (-ty * (cx - m[0]) + tx * (cy - m[1])) > 0 else -1
    spans = ((.08, .92), (.22, .78), (.36, .64))
    for k in range(min(3, weight)):
        sub = _sub(run, *spans[k])
        if len(sub) > 1:
            cv.hair(_offset_pl(sub, side * .55 * (k + 1)))


def form_hatch(poly, cx, cy, r0, r1, pitch=2., a0=0., a1=2 * _m.pi, sq=1., n=28):
    """Hatch that follows a rounded form: arcs about (cx, cy) from radius r0 to r1 every `pitch`,
    clipped to poly (the lit side is left to the caller by choosing a0..a1)."""
    out = []
    r = r0
    while r <= r1:
        arc = [(cx + r * _m.cos(a0 + (a1 - a0) * i / n), cy + r * sq * _m.sin(a0 + (a1 - a0) * i / n))
               for i in range(n + 1)]
        out += _clip_pl_poly(arc, poly)
        r += pitch
    return out


def _in_poly(x, y, poly):
    c = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            c = not c
        j = i
    return c


def _clip_pl_poly(pl, poly):
    out, run = [], []
    for p in _dres(pl, 1.):
        if _in_poly(p[0], p[1], poly):
            run.append(p)
        else:
            if len(run) > 1:
                out.append(run)
            run = []
    if len(run) > 1:
        out.append(run)
    return out


def stipple(poly, pitch, seed=0, r=.35):
    """Dots on a jittered grid inside poly, as tiny closed ticks (a stroke of 1 px, ~1 px long)."""
    rng = _r.Random(seed)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    out = []
    y = min(ys)
    row = 0
    while y < max(ys):
        x = min(xs) + (pitch / 2 if row % 2 else 0)
        while x < max(xs):
            px, py = x + rng.uniform(-.3, .3) * pitch, y + rng.uniform(-.3, .3) * pitch
            if _in_poly(px, py, poly):
                out.append([(px, py), (px + .6, py + .3)])
            x += pitch
        y += pitch * .87
        row += 1
    return out


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
# Planned forms (edition plan 1.6; art direction of Nov 12): every plate is cut to its page's form
# and shape and stands free on the paper. No black field, no filler: the scene is the plate, its
# edge either dissolves into white the way Bewick's tailpieces do, or is held by a frame built
# from the page's own motifs (passed in by the page).
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
        # a lunette band: both edges arched, the ends cut square
        arch = sh * .14
        n = 48
        top, bot = [], []
        for i in range(n + 1):
            t = i / n
            x = cx - rx + 2 * rx * t
            b = arch * _m.sin(_SPI * t)
            top.append((x, cy - ry + arch - b))
            bot.append((x, cy + ry - b))
        return top + bot[::-1]
    # irregular: a soft, lobed silhouette
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
    """Where the shape sits in the w x h box: (cx, cy, sw, sh)."""
    pad = 2.
    sh = h - 2 * pad
    if shape == "roundel":
        sw = min(sh, w * .62)
        sh = min(sh, sw)
    elif shape == "oval":
        frac = .55 if form == "tailpiece" else .62
        sw = min(sh * (2.3 if form == "tailpiece" else 1.45), w * frac)
        sh = min(sh, sw * 1.05)
    elif shape == "arched":
        sw = min(sh * 1.3, w * .6)
        sh = min(sh, sw * 1.45)
    elif shape == "banner":
        sw = w * (.96 if form == "headpiece" else .6)
        sh = min(sh, sw * .32)
    else:
        sw = {"headpiece": w * .97, "tailpiece": min(w * .6, sh * 3.4)}.get(form, min(w * .7, sh * 1.8))
        sh = min(sh, sw * .95)
    return w / 2, h / 2, sw, sh


def ragged(poly, band, seed=0, sides=None):
    """The Bewick edge as a cut: the outline resampled every px or so and each point pushed inward
    by its own random depth (most near the rim, a few deep), so the scene's lines end raggedly and
    the engraving fades into whatever lies under the plate. sides(x, y) limits it to part of the edge."""
    rng = _r.Random(seed)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        seg = _m.hypot(b[0] - a[0], b[1] - a[1])
        steps = max(1, int(seg / 1.3))
        tx, ty = (b[0] - a[0]) / (seg or 1), (b[1] - a[1]) / (seg or 1)
        nx, ny = -ty, tx
        if (cx - a[0]) * nx + (cy - a[1]) * ny < 0:
            nx, ny = -nx, -ny
        for k in range(steps):
            t = k / steps
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if sides is not None and not sides(x, y):
                out.append((x, y))
                continue
            d = band * (rng.random() ** 1.8) * (.6 + .4 * _m.sin(x * .07 + y * .05) ** 2)
            out.append((x + nx * d, y + ny * d))
    return out


def form_plate(w, h, ctx, scene, shape="oval", form="vignette", seed=0, arms=False, frame=None, ft=0.,
               fade=10., fade_sides=None):
    """A planned plate, w x h: the subject in its `shape`, sized for its `form`, standing free on the
    paper. frame(cx, cy, sw, sh, outer, inner, mode) -> svg draws the page's own frame over the
    scene's edge (ft: how far it reaches in). fade: the width of the dissolving edge (0 for none).
    arms=True (section fronts) sets the Somaster dedication cartouche at the foot.
    scene(X, Y, W, H, mode, clip_poly) -> svg; mode 's' (h < 110), 'm' (to 260) or 't'."""
    mode = "s" if h < 110 else ("m" if h <= 260 else "t")
    cx, cy, sw, sh = _form_geom(form, shape, w, h)
    ah = 0.
    if arms:
        ah = max(24., min(48., h * .17))
        sh = min(sh, h - 4 - ah * .6)
        cy = 2 + sh / 2
        if shape == "roundel":
            sw = min(sw, sh)
    outer = _shape_poly(shape, cx, cy, sw, sh, seed)
    inner = _shape_poly(shape, cx, cy, sw - 2 * ft, sh - 2 * ft, seed) if ft else outer
    ixs = [p[0] for p in inner]
    iys = [p[1] for p in inner]
    X, Y = min(ixs), min(iys)
    W, H = max(ixs) - X, max(iys) - Y
    # the cut: outside it the plate is transparent, so the page's own light ground shows through;
    # with fade the cut is ragged, every line ending at its own depth, so the engraving dissolves
    # into that ground instead of stopping at a rule (no white is laid anywhere)
    cut = ragged(inner, min(fade, H * .25), seed + 77, fade_sides) if fade else inner
    o = [scene(X, Y, W, H, mode, cut)]
    if frame:
        o.append(frame(cx, cy, sw, sh, outer, inner, mode))
    if arms:
        import arms as _A
        aw = ah * .86
        ax, ay = cx - aw / 2, h - ah - 1
        plq = _kell(cx, ay + ah / 2, aw / 2 + 4, ah / 2 + 2.5, 48)
        o.append(f'<path d="{_SD(plq, True, .1)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(bead_ring(_kell(cx, ay + ah / 2, aw / 2 + 2.2, ah / 2 + .8, 64), .75, .7))
        o.append(f'<g transform="translate({_SN(ax)} {_SN(ay)})">{_A.arms(aw, ah, seed)}</g>')
    return _tidy(_C.svg_doc(w, h, "".join(o)))


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


# ------------------------------------------------------------------------------------------------
# The finished plate (house rules of Nov 12): stroke widths 0.5 / 1 / 1.5 only, no scale
# transforms, no dash arrays. Canvas paths are written in quarter or half px under a scale();
# here they are rewritten in plain px (half-px grid, drift-free) and their widths set to the px
# they actually print at. Unused house patterns are dropped.
# ------------------------------------------------------------------------------------------------

import re as _re
_TOK = _re.compile(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)")


def _rescale_d(d, k):
    """Path data d (M m L l H h V v Z z only) scaled by k onto a half-px grid, written relative."""
    toks = _TOK.findall(d)
    out = []
    i = 0
    cx = cy = 0.        # current point, source units
    sx = sy = 0.
    px = py = 0          # last emitted point, half px
    cmd = None
    first = True

    def emit(c, ax, ay):
        nonlocal px, py, first
        hx, hy = int(round(ax * k * 2)), int(round(ay * k * 2))
        if first:
            out.append(("M", f"{_SN(hx / 2)} {_SN(hy / 2)}"))
            first = False
        else:
            dx, dy = (hx - px) / 2, (hy - py) / 2
            out.append((c, f"{_SN(dx)} {_SN(dy)}"))
        px, py = hx, hy

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if t in "Zz":
                out.append(("z", ""))
                cx, cy = sx, sy
                px, py = int(round(sx * k * 2)), int(round(sy * k * 2))
                continue
            continue
        if cmd in "Mm":
            x, y = float(toks[i]), float(toks[i + 1]); i += 2
            if cmd == "m" and not first:
                x, y = cx + x, cy + y
            cx, cy = x, y; sx, sy = x, y
            emit("m", x, y)
            cmd = "l" if cmd == "m" else "L"
        elif cmd in "Ll":
            x, y = float(toks[i]), float(toks[i + 1]); i += 2
            if cmd == "l":
                x, y = cx + x, cy + y
            cx, cy = x, y
            emit("l", x, y)
        elif cmd in "HhVv":
            v = float(toks[i]); i += 1
            if cmd == "H": cx = v
            elif cmd == "h": cx += v
            elif cmd == "V": cy = v
            else: cy += v
            emit("l", cx, cy)
        else:
            raise ValueError("path command " + str(cmd))
    res = []
    prev = None
    for c, v in out:
        if c == "l" and prev in ("l", "m"):
            res.append(" " + v)
        else:
            res.append(c + v)
        prev = c
    return "".join(res).replace(" -", "-")


def _snapw(v):
    return min((.5, 1., 1.5), key=lambda c: abs(c - v))


def _tidy(svg):
    def one(m):
        tag = m.group(0)
        sc = _re.search(r' transform="scale\(([\d.]+)\)"', tag)
        k = 1.
        if sc:
            k = float(sc.group(1))
            tag = tag.replace(sc.group(0), "")
            tag = _re.sub(r' d="([^"]*)"', lambda q: f' d="{_rescale_d(q.group(1), k)}"', tag, 1)
        tag = _re.sub(r'stroke-width="([\d.]+)"', lambda q: f'stroke-width="{_SN(_snapw(float(q.group(1)) * k))}"', tag)
        return tag

    svg = _re.sub(r"<path\b[^>]*>", one, svg)
    used = set(_re.findall(r"url\(#([^)]+)\)", svg))
    svg = _re.sub(r'<pattern id="([^"]+)".*?</pattern>', lambda q: q.group(0) if q.group(1) in used else "", svg,
                  flags=_re.S)
    svg = svg.replace("<defs></defs>", "")
    return svg
# ---- end studio helpers ----


PI, TAU = math.pi, 2 * math.pi
_n, _d, _E = C._n, C._d, C._ell_pts
CR = ' shape-rendering="crispEdges"'


# ----------------------------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------------------------

def ell(cx, cy, rx, ry, n=40):
    return _E(cx, cy, rx, ry, n)[:-1]


def scale_about(poly, ox, oy, k):
    return [(ox + (x - ox) * k, oy + (y - oy) * k) for x, y in poly]


def bezq(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]


# ----------------------------------------------------------------------------------------------
# path lettering (no <text>)
# ----------------------------------------------------------------------------------------------

def _arc(cx, cy, rx, ry, a0, a1, n=10):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


GL = {
    "A": (.72, [[(0, 1), (.36, 0), (.72, 1)], [(.15, .64), (.57, .64)]]),
    "C": (.68, [_arc(.36, .5, .34, .5, -40, -320, 14)]),
    "E": (.56, [[(.56, 0), (0, 0), (0, 1), (.56, 1)], [(0, .5), (.44, .5)]]),
    "F": (.54, [[(.54, 0), (0, 0), (0, 1)], [(0, .5), (.42, .5)]]),
    "G": (.72, [_arc(.37, .5, .35, .5, -40, -320, 14) + [(.72, .58), (.42, .58)]]),
    "K": (.64, [[(0, 0), (0, 1)], [(.62, 0), (0, .62)], [(.2, .44), (.64, 1)]]),
    "M": (.84, [[(0, 1), (0, 0), (.42, .72), (.84, 0), (.84, 1)]]),
    "N": (.7, [[(0, 1), (0, 0), (.7, 1), (.7, 0)]]),
    "O": (.78, [_arc(.39, .5, .39, .5, 0, 360, 18)]),
    "P": (.6, [[(0, 1), (0, 0), (.36, 0)] + _arc(.34, .27, .26, .27, -90, 90, 8) + [(0, .54)]]),
    "R": (.64, [[(0, 1), (0, 0), (.36, 0)] + _arc(.34, .27, .26, .27, -90, 90, 8) + [(0, .54)], [(.3, .54), (.64, 1)]]),
    "S": (.62, [[(.6, .14), (.48, .03), (.3, 0), (.12, .05), (.04, .2), (.12, .38), (.32, .48), (.52, .58), (.62, .76),
                 (.56, .93), (.38, 1), (.18, .98), (.02, .86)]]),
    "T": (.66, [[(0, 0), (.66, 0)], [(.33, 0), (.33, 1)]]),
    "U": (.68, [[(0, 0), (0, .68)] + _arc(.34, .66, .34, .34, 180, 0, 10)[1:] + [(.68, 0)]]),
    " ": (.4, []),
}


def lettering(text, x, y, size, ycurve=None, track=.28):
    """Polylines for text with cap height `size`, left at x, cap top at y (+ ycurve(x))."""
    out = []
    cx = x
    for ch in text:
        adv, strokes = GL[ch]
        dy = ycurve(cx + adv * size / 2) if ycurve else 0
        for s in strokes:
            out.append([(cx + px * size, y + dy + py * size) for px, py in s])
        cx += (adv + track) * size
    return out, cx - x - track * size


def text_width(text, size, track=.28):
    return sum((GL[c][0] + track) * size for c in text) - track * size


def pd(pls, tol=.1):
    return "".join(_d(p, tol=tol) for p in pls if len(p) > 1)


# ----------------------------------------------------------------------------------------------
# the subject: mushrooms and their forest
# ----------------------------------------------------------------------------------------------

def matsutake(cv, cx, gy, R, rng, stage=1.):
    """A matsutake standing on ground line gy, cap radius R. stage 1 mature (domed cap, gills
    showing under an in-rolled lip), stage < .5 a button (round cap clamped to the stem)."""
    mature = stage > .5
    hw = R * (.25 if mature else .32)
    sh = R * (1.15 if mature else .35)
    yt = gy - sh
    lean = R * .06 * rng.uniform(-1, 1)
    Hc = R * (.68 if mature else .9)
    e = R * .17

    def sx(u, v):  # u 0 base .. 1 top, v -1..1 across
        w = hw * (1.08 - .12 * u + .12 * math.sin(PI * min(1, u * 1.6)) * (1 - u))
        return cx + lean * u + v * w, gy + 2 - (sh + 2 + e) * u
    left = [sx(i / 16, -1) for i in range(17)]
    right = [sx(i / 16, 1) for i in range(17)]
    cv.obj([left + right[::-1]], 1.)
    for v in (-.55, -.15, .2, .45, .62, .76, .86, .94):
        cv.hair([sx(i / 14, v) for i in range(15)])
    cv.heavy([sx(i / 14, .98) for i in range(15)])
    for k in range(int(sh / 3.2)):
        u = rng.uniform(.05, .7)
        v = rng.uniform(-.7, .6)
        px, py = sx(u, v)
        s = R * .05
        cv.hair([(px - s, py - s * .7), (px, py), (px + s * .9, py - s * .6)])
    if mature:
        ru0, ru1 = .62, .86
        top = [sx(ru1, -1.25 + 2.5 * i / 10) for i in range(11)]
        bot = []
        for i in range(13):
            v = 1 - 2 * i / 12
            x, y = sx(ru0, v * 1.3)
            bot.append((x, y + (2.2 if i % 2 else -.6) * R / 40))
        cv.obj([top + bot], 1.)
        for i in range(1, 12):
            v = -1.2 + 2.4 * i / 12
            a, b = sx(ru1 - .02, v), sx(ru0 + .02, v * 1.05)
            (cv.line if v > .55 else cv.hair)([a, b])
        cv.heavy([(x, y + .8) for x, y in bot[:7]])
    ccx = cx + lean
    if mature:
        disk = ell(ccx, yt, R * .9, e, 48)
        cv.obj([disk], 1.)
        n = int(PI * R * .9 / 1.6)
        for i in range(1, n):
            th = PI * i / n
            p = (ccx + R * .9 * math.cos(th), yt + e * math.sin(th))
            q = (ccx + hw * .9 * math.cos(th), yt - e * .1)
            cv.hair([q, p])
        cv.line([(ccx + R * .9 * math.cos(PI * i / 20), yt + e * .35 * math.sin(PI * i / 20)) for i in range(21)])
    prof = [(ccx + R * t, yt - Hc * (1 - t * t) ** .55) for t in [-1 + 2 * i / 40 for i in range(41)]]
    lipy = e * (.35 if mature else .9)
    lip = [(ccx + R * math.cos(th), yt + lipy * math.sin(th)) for th in [PI * i / 24 for i in range(25)]]
    dome = prof + lip[1:-1]
    cv.obj([dome], 1.)
    ox, oy = ccx - R * .32, yt - Hc * .72
    k = .9
    while k > .18:
        ring = scale_about(dome, ox, oy, k)
        cv.hair(ring + [ring[0]])
        k -= .085 if k > .5 else .11
    rside = [p for p in prof if p[0] > ccx + R * .05] + [p for p in lip[1:-1] if p[0] > ccx + R * .05]
    if len(rside) > 3:
        cv.hair(C.hatch_poly(rside, 45, 3., .3))
        low = [p for p in rside if p[1] > yt - Hc * .45]
        if len(low) > 3:
            cv.hair(C.hatch_poly(low, -45, 3., 1.2))
    cv.heavy(lip)
    cv.hair([(x, y - 1.6) for x, y in lip[2:-2]])
    for j in range(3):
        cv.line([(ccx + (R - .3 - j * .8) * math.cos(th), yt + lipy * math.sin(th) - .2 - j * .7)
                 for th in [PI * i / 24 for i in range(0, 9)]])
    for k in range(int(R * 1.6)):
        t = rng.uniform(-.82, .82)
        f = rng.uniform(.2, .8) ** .8
        px = ccx + R * t * .96
        py = yt - Hc * f * (1 - t * t) ** .55
        s = R * (.035 + .05 * f)
        ang = math.atan2(py - (yt + R * .6), px - ccx)
        ux, uy = math.cos(ang), math.sin(ang)
        a = (px + ux * s - uy * s * .7, py + uy * s + ux * s * .7)
        b = (px + ux * s + uy * s * .7, py + uy * s - ux * s * .7)
        (cv.line if f > .75 and rng.random() < .5 else cv.hair)([a, (px, py), b])
    return (ccx, yt - Hc)


def chanterelle(cv, cx, gy, s, rng):
    """A golden chanterelle: a trumpet with a wavy rim and forked false gills running down the
    stem; its top a shallow funnel."""
    yr = gy - s * 1.25
    ry = s * .28
    ph = rng.uniform(0, TAU)

    def rim(th):
        w = 1 + .07 * math.sin(5 * th + ph) + .04 * math.sin(9 * th + ph * 2)
        return (cx + s * w * math.cos(th), yr + ry * w * math.sin(th) + s * .04 * math.sin(4 * th + ph))
    lb = bezq(rim(PI), (cx - s * .2, yr + s * .25), (cx - s * .17, gy + 1), 14)
    rb = bezq(rim(0), (cx + s * .2, yr + s * .25), (cx + s * .17, gy + 1), 14)
    front = [rim(PI * i / 30) for i in range(31)]
    body = front + lb[1:] + rb[::-1][:-1]
    cv.obj([body], 1.)
    for i in range(1, 15):
        th = PI * i / 15
        p0 = rim(th)
        tgt = (cx + (p0[0] - cx) * .18, gy - s * .35)
        mid = (cx + (p0[0] - cx) * .45, yr + s * .4)
        curve = bezq(p0, mid, tgt, 10)
        (cv.line if p0[0] > cx + s * .45 else cv.hair)(curve)
        if i % 2 and .3 < th < PI - .3:
            q0 = rim(th + PI / 30)
            cv.hair(bezq(q0, ((q0[0] + mid[0]) / 2, (q0[1] + mid[1]) / 2 + 2), curve[4], 6))
    cv.heavy(rb)
    top = [rim(TAU * i / 48) for i in range(48)]
    cv.obj([top], 1.)
    for k in (.86, .7, .54, .38, .22):
        ring = [(cx + (x - cx) * k, yr + s * .05 * (1 - k) + (y - yr) * k) for x, y in top]
        cv.hair(ring + [ring[0]])
    inner = [(cx + (x - cx) * .9, yr + (y - yr) * .9) for x, y in top if y < yr + ry * .2]
    if len(inner) > 3:
        cv.hair(C.hatch_poly(inner, 0, 1.5, .25))
    cv.heavy(front)


def pine_trunk(cv, x, y0, y1, w0, w1, rng):
    """A lodgepole pine trunk in platy bark, lit from the left."""
    cv.obj([[(x - w1 / 2, y0), (x - w0 / 2, y1), (x + w0 / 2, y1), (x + w1 / 2, y0)]], 1.)
    H = y1 - y0

    def at(u, v):
        w = w1 + (w0 - w1) * u
        return (x + v * w / 2, y0 + H * u)
    for v in (-.6, -.2, .25, .5, .68, .82, .92):
        cv.hair([at(u / 20, v + .03 * math.sin(u * 1.7)) for u in range(21)])
    for d in (.97, .88):
        cv.line([at(u / 20, d) for u in range(21)])
    yy = y0 + 3
    while yy < y1 - 2:
        u = (yy - y0) / H
        a, b = rng.uniform(-.9, -.2), rng.uniform(.1, .8)
        cv.hair([at(u, a), at(u + 1 / H, b)])
        yy += rng.uniform(3, 6)


def fir(cv, x, y0, y1, wmax, rng):
    """A true fir: a straight dark trunk carrying tiers of drooping boughs, each bough shaded dark
    beneath with a needle fringe, lit along its top; upper tiers lap over lower ones."""
    H = y1 - y0
    cv.obj([[(x - 1.5, y0 + H * .05), (x - 2.5, y1), (x + 2.5, y1), (x + 1.5, y0 + H * .05)]], 1.)
    cv.line(C.hatch_poly([(x - 1.5, y0), (x - 2.5, y1), (x + 2.5, y1), (x + 1.5, y0)], 90, 1.5))
    n = max(4, int(H / 13))
    for k in range(n):
        f = k / (n - 1)                      # 0 bottom .. 1 top
        yk = y1 - H * .12 - (H * .86) * f
        wk = wmax * (1 - f) ** .9 * .5 + 3
        dk = min(16., H * .09) * (1.1 - .5 * f)
        for side in (-1, 1):
            tip = (x + side * wk, yk + dk * .9)
            topc = bezq((x, yk - dk * .25), (x + side * wk * .55, yk - dk * .2), tip, 10)
            m = max(4, int(wk / 3))
            fringe = []
            for i in range(m + 1):
                t = i / m
                bx = x + side * wk * (1 - t)
                by = yk + dk * .9 * (1 - t) + dk * .55 * math.sin(PI * t) ** .5
                fringe.append((bx, by + (2.2 if i % 2 else 0)))
            poly = topc + fringe[1:]
            cv.obj([poly], 1.)
            cv.hair(C.hatch_poly(poly, 0, 1.5, .25))
            cv.line(C.hatch_poly([p for p in poly if p[1] > yk + dk * .25] or poly, 0, 2., 0))
            for i in range(1, m, 1):
                t = i / m
                p0 = (x + side * wk * (1 - t) * .95, yk + dk * .9 * (1 - t) - dk * .15)
                cv.hair([p0, (p0[0] - side * 2, p0[1] + dk * .45)])
            cv.heavy(fringe)
    cv.obj([[(x - 1.2, y0 - 2), (x, y0 - 8), (x + 1.2, y0 - 2), (x, y0 + 6)]], 1.)


def needle_tuft(cv, x, y, ang, L, n=9):
    for i in range(n):
        a = ang + (i - (n - 1) / 2) * .17
        cv.hair([(x, y), (x + L * math.cos(a), y + L * math.sin(a))])


def branch(cv, x, y, ang, L, rng, droop=.25):
    pts = bezq((x, y), (x + L * .5 * math.cos(ang), y + L * .5 * math.sin(ang) - L * .1),
               (x + L * math.cos(ang + droop), y + L * math.sin(ang + droop)), 10)
    cv.line(pts)
    for i in range(3, 11, 2):
        px, py = pts[i]
        for sgn in (-1, 1):
            needle_tuft(cv, px, py, ang + droop * i / 10 + sgn * .9 - PI / 2 * .3, L * .16, 7)
    needle_tuft(cv, pts[-1][0], pts[-1][1], ang + droop, L * .22, 11)


def cloud(cv, x0, x1, base, h, rng):
    n = max(3, int((x1 - x0) / (h * .55)))
    cs = [(x0 + (x1 - x0) * (i + .5) / n + rng.uniform(-3, 3), h * rng.uniform(.4, .95)) for i in range(n)]
    cs = [(c, min(r, (c - x0) * .9, (x1 - c) * .9)) for c, r in cs]

    def top(x):
        m = 0
        for c, r in cs:
            if abs(x - c) < r:
                m = max(m, math.sqrt(r * r - (x - c) ** 2))
        return base - m
    k = int(x1 - x0)
    pts = [(x0 + (x1 - x0) * i / k, top(x0 + (x1 - x0) * i / k)) for i in range(k + 1)]
    poly = pts + [(x, base + 2 - 3 * abs(math.sin(x * .09))) for x in [x1 - (x1 - x0) * i / 30 for i in range(31)]]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly([(x, max(y, base - h * .35)) for x, y in pts] + [(x1, base + 2), (x0, base + 2)], 0, 1.5, .25))
    lowb = [(x, base + 2 - 3 * abs(math.sin(x * .09))) for x in [x0 + (x1 - x0) * i / 30 for i in range(31)]]
    cv.line(C.hatch_poly([(x, max(y, base - h * .1)) for x, y in pts] + lowb[::-1], 0, 2., 0))
    for c, r in cs:
        for f in (.82, .64):
            cv.hair(_E(c + r * .1, base - r * .1, r * f, r * f * .9, 14, PI * 1.2, PI * 2.05))
    return poly


def paw_print(cv, x, y, s):
    """Parker's dog was here: one paw pressed into the sand."""
    pad = [(x - s * .55, y + s * .35), (x - s * .3, y - s * .1), (x, y - s * .25), (x + s * .3, y - s * .1),
           (x + s * .55, y + s * .35), (x + s * .3, y + s * .55), (x, y + s * .45), (x - s * .3, y + s * .55)]
    toes = [ell(x + dx * s, y + dy * s, s * .2, s * .26, 12) for dx, dy in ((-.62, -.55), (-.22, -.9), (.22, -.9), (.62, -.55))]
    for p in [pad] + toes:
        cv.obj([p], 1.)
        cv.line(C.hatch_poly(p, 0, 1.5, .25))


def pine_cone(cv, x, y, s, ang=-.3):
    ca, sa = math.cos(ang), math.sin(ang)
    poly = [(x + ca * px - sa * py, y + sa * px + ca * py) for px, py in ell(0, 0, s, s * .5, 24)]
    cv.obj([poly], 1.)
    cv.hair(C.hatch_poly(poly, 45 + math.degrees(ang), 2.))
    cv.hair(C.hatch_poly(poly, -45 + math.degrees(ang), 2.5))
    for i in range(-3, 4):
        px = i * s * .26
        cv.line([(x + ca * (px - s * .1) - sa * s * .45, y + sa * (px - s * .1) + ca * s * .45),
                 (x + ca * (px + s * .1) - sa * s * .45, y + sa * (px + s * .1) + ca * s * .45)])


def ridge_y(ridge, x):
    for (ax, ay), (bx, by) in zip(ridge, ridge[1:]):
        if ax <= x <= bx:
            return ay + (by - ay) * (x - ax) / ((bx - ax) or 1)
    return ridge[-1][1]


def forest_floor(cv, X, y0, W, y1, seed, dens=1.):
    """Douglas-fir duff engraved, not patterned: fallen needles in little crossed drifts, small
    near the horizon and long in front, with a shadow stroke under each drift and a scatter of
    punched dots of sand."""
    rng = random.Random(seed)
    cv.obj([[(X - 3, y0), (X + W + 3, y0), (X + W + 3, y1 + 3), (X - 3, y1 + 3)]], 0)
    y = y0 + 1.5
    while y < y1 + 2:
        f = (y - y0) / max(1., y1 - y0)
        L = 2.5 + 6 * f
        x = X - 3 + rng.uniform(0, L)
        while x < X + W + 3:
            a = rng.uniform(-.5, .5)
            for k in range(rng.randint(1, 3)):
                b = a + rng.uniform(-.9, .9)
                ll = L * rng.uniform(.6, 1.)
                cv.hair([(x, y), (x + ll * math.cos(b), y + ll * math.sin(b) * .45)])
            if rng.random() < .2:
                cv.line([(x - L * .3, y + 1.2), (x + L * .5, y + 1.2)])
            x += L * rng.uniform(1.1, 2.) / dens
        y += 2.2 + 3.5 * f


def drum_stump(cv, x, gy, s):
    """Easter egg: a fir stump sawn level and cut like a snare drum: rings for a head, two hoops,
    the lugs and the zig-zag of the tension rope round its bark."""
    rx, ry, hh = s, s * .3, s * 1.1
    body = [(x - rx, gy - hh)] + [(x + rx * math.cos(a), gy + ry * math.sin(a)) for a in [PI - PI * i / 16 for i in range(17)][::-1]][::-1] + [(x + rx, gy - hh)]
    body = [(x - rx, gy - hh), (x - rx, gy)] + [(x - rx * math.cos(PI * i / 16), gy + ry * math.sin(PI * i / 16)) for i in range(17)] + [(x + rx, gy - hh)]
    cv.obj([body], 1.)
    cv.hair(C.hatch_poly([(x + rx * .25, gy - hh), (x + rx, gy - hh), (x + rx, gy + ry * .6), (x + rx * .25, gy + ry * .9)], 90, 1.5))
    for yy in (gy - hh + ry * .9, gy - ry * .2):
        cv.line([(x - rx * math.cos(PI * i / 16), yy + ry * math.sin(PI * i / 16)) for i in range(17)])
    n = 6
    zz = []
    for i in range(n + 1):
        t = i / n
        zz.append((x - rx * math.cos(PI * t), (gy - hh + ry * .9 if i % 2 == 0 else gy - ry * .2) + ry * math.sin(PI * t)))
    cv.hair(zz)
    head = [(x + rx * math.cos(a), gy - hh + ry * math.sin(a)) for a in [2 * PI * i / 24 for i in range(24)]]
    cv.obj([head], .5)
    for k in (.66, .33):
        cv.hair([(x + rx * k * math.cos(a), gy - hh + ry * k * math.sin(a)) for a in [2 * PI * i / 16 for i in range(17)]])


def scene(X, Y, W, H, seed, detail=1.):
    """The vignette into the box (X, Y, W, H): an SVG fragment (the caller clips it)."""
    rng = random.Random(seed)
    o = []
    yh = Y + H * .56
    back = KCanvas()
    # the sky over the Cascades: engraved, darkening to the zenith; the rain clouds come below
    engraved_sky(back, X - 2, Y - 2, W + 4, yh - Y + 4, seed + 1, clouds=0, maxc=1)
    back.obj([], 0)
    for (a, b, cb) in ((X - 4, X + W * .46, Y + H * .26), (X + W * .7, X + W + 4, Y + H * .2)):
        xx = a
        while xx < b:
            yy = cb + rng.uniform(0, 6)
            while yy < yh:
                ln = rng.uniform(5, 10)
                back.hair([(xx + (yy - cb) * .27, yy), (xx + (yy + ln - cb) * .27, yy + ln)])
                yy += ln + rng.uniform(3, 7)
            xx += 3
    # Mt. Hood
    px, py = X + W * .6, Y + H * .16
    mL, mR = X + W * .12, X + W * 1.05
    ridge = [(mL, yh), (X + W * .3, yh - H * .1), (X + W * .42, yh - H * .2), (X + W * .5, py + H * .14),
             (X + W * .56, py + H * .03), (px, py), (X + W * .63, py + H * .04), (X + W * .7, py + H * .13),
             (X + W * .8, yh - H * .2), (X + W * .92, yh - H * .1), (mR, yh)]
    mtn = ridge + [(mR, yh + 6), (mL, yh + 6)]
    back.obj([mtn], 1.)
    back.hair(C.hatch_poly(mtn, 0, 2., .25))
    back.hair(C.hatch_poly([p for p in mtn if p[0] >= px - 1] + [(px, yh + 6)], 45, 3.))
    snowline = []
    for i in range(15):
        t = i / 14
        x = X + W * (.47 + .26 * t)
        cy = py + H * (.17 + .12 * math.sin(PI * t) ** .5) * (1 - abs(t - .5) * .7)
        ry_ = ridge_y(ridge, x)
        snowline.append((x, max(cy + (H * .05 if i % 2 else 0), ry_ + 1.5)))
    top = [p for p in ridge if snowline[0][0] <= p[0] <= snowline[-1][0]]
    snow = top + snowline[::-1]
    back.obj([snow], .5)
    back.hair(C.hatch_poly([p for p in snow if p[0] >= px - .5] + [(px, snowline[7][1])], 45, 2.))
    for i in range(15):
        bx, by = snowline[i]
        sxp = px + (bx - px) * .45
        syp = py + abs(sxp - px) * (H * .14) / (W * .06) * .55 + 1.5
        if syp < by - 3:
            g = bezq((sxp, syp), ((sxp + bx) / 2 + (1.5 if i % 2 else -1.5), (syp + by) / 2), (bx, by), 8)
            (back.line if bx > px and i % 2 else back.hair)(g)
    cloud(back, X - 6, X + W * .46, Y + H * .26, H * .2, rng)
    cloud(back, X + W * .7, X + W + 6, Y + H * .2, H * .17, rng)
    fx = X - 4
    fpts = [(X - 4, yh + H * .07)]
    while fx < X + W + 4:
        hh = H * rng.uniform(.05, .11)
        fpts += [(fx, yh + H * .02), (fx + 2.5, yh + H * .02 - hh), (fx + 5, yh + H * .02)]
        fx += rng.uniform(4, 7)
    fpts.append((X + W + 4, yh + H * .07))
    back.obj([fpts], .5)
    back.line(C.hatch_poly(fpts, 0, 2., 0))
    o.append(back.svg())
    # sandy soil: stipple
    gy0 = yh + H * .06
    soil = [(X - 4 + (W + 8) * i / 30, gy0 + H * .025 * math.sin(i * .9 + seed)) for i in range(31)]
    soil += [(X + W + 4, Y + H + 4), (X - 4, Y + H + 4)]
    fr = KCanvas()
    forest_floor(fr, X, gy0, W, Y + H, seed + 9, .8 * detail + .2)
    fr.obj([soil], .5)
    forest_floor(fr, X, gy0 + 2, W, Y + H, seed + 9, .8 * detail + .2)
    fr.line(soil[:31])
    for i in range(int(18 * detail)):
        sx_, sy_ = rng.uniform(X, X + W), rng.uniform(gy0 + 4, Y + H)
        ln = rng.uniform(6, 16)
        fr.hair(bezq((sx_, sy_), (sx_ + ln / 2, sy_ - 1.5), (sx_ + ln, sy_), 6))
    for i in range(int(16 * detail)):
        sx_, sy_ = rng.uniform(X, X + W), rng.uniform(gy0 + 6, Y + H)
        a = rng.uniform(-.6, .6)
        ln = rng.uniform(6, 11)
        for dd in (-1, 1):
            fr.hair([(sx_, sy_), (sx_ + ln * math.cos(a + dd * .12), sy_ + ln * math.sin(a + dd * .12))])
    R1 = min(W * .21, H * .28)
    gm = Y + H * .88
    for (sx_, sw_) in ((X + W * .42 + R1 * .5, R1 * .8), (X + W * .63 + R1 * .35, R1 * .55)):
        shp = ell(sx_, gm + 1, sw_, R1 * .1, 24)
        fr.obj([shp], 0)
        fr.line(C.hatch_poly(shp, 0, 2., 0))
    pine_cone(fr, X + W * .34, Y + H * .955, W * .04)
    drum_stump(fr, X + W * .87, Y + H * .97, W * .05)
    paw_print(fr, X + W * .6, Y + H * .94, W * .036)
    chanterelle(fr, X + W * .8, Y + H * .86, R1 * .48, rng)
    matsutake(fr, X + W * .24, Y + H * .9, R1 * .42, rng, .3)
    matsutake(fr, X + W * .63, gm - 3, R1 * .7, rng, 1.)
    matsutake(fr, X + W * .42, gm, R1, rng, 1.)
    bx, by = X + W * .24, Y + H * .9
    for a in (.2, .9, 2.4, 3.0):
        fr.line([(bx + R1 * .42 * math.cos(a), by + 1 + R1 * .1 * math.sin(a)),
                 (bx + R1 * .7 * math.cos(a), by + 2 + R1 * .18 * math.sin(a))])
    o.append(fr.svg())
    return "".join(o)


def small_scene(X, Y, W, H, seed):
    """For the band's medallion: a matsutake and a chanterelle on sand, rain behind."""
    rng = random.Random(seed)
    o = []
    sk = KCanvas()
    engraved_sky(sk, X - 2, Y - 2, W + 4, H * .75, seed + 1, clouds=0, maxc=0)
    o.append(sk.svg())
    gy = Y + H * .72
    cv = KCanvas()
    forest_floor(cv, X, gy, W, Y + H, seed + 9, .7)
    cv.line([(X - 2, gy), (X + W + 2, gy)])
    fir(cv, X + W * .1, Y + H * .05, gy + 2, W * .3, rng)
    R = min(W * .2, H * .34)
    chanterelle(cv, X + W * .72, gy + 2, R * .55, rng)
    matsutake(cv, X + W * .4, gy + 2, R, rng, 1.)
    o.append(cv.svg())
    return "".join(o)


def crest(cx, cy, size, seed):
    """A matsutake rising from an acanthus calyx."""
    cv = C.Canvas()
    rng = random.Random(seed)
    base = -PI / 2
    n = 2
    for j in range(n, 0, -1):
        for side in (-1, 1):
            sp = j / (n + .4)
            a = base + side * sp * 1.35
            ln = size * (1.0 - .25 * sp) * rng.uniform(.95, 1.03)
            b = side * (.5 + .6 * sp)
            C._finger(cv, cx + side * size * .05, cy, a, ln, ln * .12, b, b * 5.5)
    matsutake(cv, cx, cy - size * .1, size * .46, rng, 1.)
    r = size * .13
    cv.obj([ell(cx, cy, r * 1.6, r, 28)], 1.)
    cv.hair(C.hatch_poly(ell(cx, cy + r * .3, r * 1.4, r * .55, 20), 0, 1.5))
    return cv.svg()


# ----------------------------------------------------------------------------------------------
# layouts (adapted from engraving_codex, every surface engraved)
# ----------------------------------------------------------------------------------------------

def field_of(cx, cy, w, h):
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return (cx - a, cy - b, 2 * a, 2 * b)


def clip_d(cid, d, body):
    return f'<clipPath id="{cid}"><path d="{d}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def banner(cx, cy, w, h, seed, text="MATSUTAKE", arch=.04):
    bsvg, centre = C.ribbon_banner(cx, cy, w, h, arch, seed)
    size = h * .52
    tw = text_width(text, size)
    if tw > w * .62:
        size *= w * .62 / tw
        tw = text_width(text, size)

    def yc(x):
        return min(centre, key=lambda p: abs(p[0] - x))[1] - cy
    pls, _ = lettering(text, cx - tw / 2, cy - size / 2, size, yc)
    return bsvg + f'<path d="{pd(pls)}" stroke="#000" stroke-width="1" fill="none"/>'


def tablet_fill(tx, ty, tw, th, text="PRO AMORE FUNGORUM"):
    o = [f'<path d="M{_n(tx + 2)},{_n(ty + 2)}h{_n(tw - 3)}v{_n(th - 3)}h{_n(-tw + 3)}z" fill="{C.pat("L")}" stroke="none"/>']
    size = min(th * .56, 9.)
    if size >= 4:
        t = text_width(text, size, .34)
        pls, _ = lettering(text, tx + (tw - t) / 2, ty + (th - size) / 2 + .5, size, None, .34)
        o.append(f'<path d="M{_n(tx + (tw - t) / 2 - 4)},{_n(ty + (th - size) / 2 - 1)}h{_n(t + 8)}v{_n(size + 3)}h{_n(-t - 8)}z" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{pd(pls)}" stroke="#000" stroke-width="1" fill="none"/>')
        for sx in (-1, 1):
            x0 = tx + tw / 2 + sx * (t / 2 + 10)
            x1 = tx + tw / 2 + sx * (tw / 2 - 6)
            ym = ty + th / 2
            o.append(f'<path d="M{_n(x0)},{_n(ym)}L{_n(x1)},{_n(ym)}" stroke="#000" stroke-width="1"/>')
            for xd in (x0, x1):
                o.append(f'<path d="{_d(ell(xd, ym, 1.5, 1.5, 8), True, 0)}" fill="#000"/>')
    return "".join(o)


def layout_tall(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(C.bead_moulding(0, 3, w, 1.5))
    o.append(C.dark_ground((0, 6.5, w, py0), "L"))
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
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
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(10, ph * .035), rmax=r1 * .9,
                   max_n=int(14 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(cx, cy, cw, ch)
    o.append(clip_d(C._uid("gv", w, h, seed), field, scene(fx, fy, fw, fh, seed)))
    o.append(crest(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), rng.randrange(1 << 20)))
    o.append(banner(cx, cy + ch * .47, cw * 1.4, min(17, ph * .055), rng.randrange(1 << 20)))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    o.append(C.dark_ground((0, py, w, ped_h), "L"))
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(tablet_fill(tx, ty, tw, th))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((0, fy, w, fh), "L"))
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("gf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def layout_medium(w, h, seed, density=1.):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .44, gh * 1.6)
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .07), rmax=r * .8,
                   max_n=int(10 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("gm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, _, field = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    fx, fy, fw, fh = field_of(cx, cy, cw, gh + 4)
    o.append(clip_d(C._uid("gmv", w, h, seed), field,
                    scene(fx, fy, fw, fh, seed, .6) if fh > 70 else small_scene(fx, fy, fw, fh, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    gap = min(gh * 1.7, 120)
    o.append(C._clip(C._uid("gb", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .8, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    inner = _d(ell(cx, cy, rx - 4.5, ry - 4.5, 64), True, 0)
    o.append(clip_d(C._uid("gbv", w, h, seed), inner, small_scene(cx - rx, cy - ry, 2 * rx, 2 * ry, seed)))
    o.append(f'<path d="{inner}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _fir_arch(cx, cy, sw, sh, outer, inner, mode, ft=8., seed=0):
    """The frame, from the forest the mushrooms grow under: two Douglas-fir boughs rise up the
    sides of the arch and meet at its crown, each twig set with needles in two ranks, cones
    hanging with their three-pointed bracts, and a button matsutake as the keystone."""
    rng = _r.Random(seed + 5)
    cv = KCanvas()
    rx, ry = sw / 2, sh / 2
    rise = min(rx * .9, sh * .5)
    spring = cy - ry + rise
    d = ft * .5
    def arcpt(a):
        return (cx + (rx - d) * _m.cos(a), spring - (rise - d) * _m.sin(a))
    boughs = []
    for sg in (-1, 1):
        pts = [(cx + sg * (rx - d), cy + ry - 1)]
        n = 12
        for i in range(1, n + 1):
            pts.append((cx + sg * (rx - d), cy + ry - 1 - (cy + ry - 1 - spring) * i / n))
        for i in range(1, 27):
            a = _m.pi / 2 - sg * (_m.pi / 2) * (1 - i / 26.)
            pts.append(arcpt(a))
        boughs.append((sg, _dres(pts, 2.)))
    cones = []
    for sg, pts in boughs:
        n = len(pts)
        wl = [max(.5, ft * .16 * (1 - .6 * i / n)) for i in range(n)]
        R = _C._Rib(pts, wl, wl)
        cv.obj([R.outline()], 1.)
        cv.hair(R.contour(.4 * sg, 0, 1))
        # twigs: alternate sides, set at a slant toward the crown, needles in two ranks
        step = max(3., ft * .55)
        L = 0.
        k = 0
        for i in range(1, n):
            L += _m.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            if L < step:
                continue
            L = 0.
            k += 1
            tx, ty = pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]
            tl = _m.hypot(tx, ty) or 1.
            tx, ty = tx / tl, ty / tl
            side = 1 if k % 2 else -1
            nx, ny = -ty * side, tx * side
            tlen = ft * rng.uniform(.75, 1.)
            ax, ay = pts[i]
            tw = [(ax + (tx * .6 + nx * .8) * tlen * u, ay + (ty * .6 + ny * .8) * tlen * u) for u in (0, .5, 1)]
            cv.line([tw[0], tw[2]])
            nd = []
            m = max(3, int(tlen / 1.8))
            for j in range(1, m + 1):
                u = j / (m + .5)
                bx, by = ax + (tw[2][0] - ax) * u, ay + (tw[2][1] - ay) * u
                ln = ft * .32 * (1 - .4 * u)
                dx, dy = (tw[2][0] - ax) / tlen, (tw[2][1] - ay) / tlen
                for s2 in (-1, 1):
                    ex, ey = dx * .55 - dy * s2 * .85, dy * .55 + dx * s2 * .85
                    nd.append([(bx, by), (bx + ex * ln, by + ey * ln)])
            cv.hair(nd)
            if k % 9 == 4 and len(cones) < 6:
                cones.append((tw[1][0], tw[1][1] + ft * .2))
    for x, y in cones:
        cr, ch = ft * .32, ft * .85
        cone = [(x + cr * _m.cos(a), y + ch * .5 + ch * .5 * _m.sin(a)) for a in [2 * _m.pi * i / 16 for i in range(16)]]
        cv.obj([cone], 1.)
        # scales in crossing spirals, the bract tips a little ticks
        cv.hair(_C.hatch_poly(cone, 35, 1.3))
        cv.hair(_C.hatch_poly(cone, -35, 1.6))
        swell_outline(cv, cone, (-1., -1.), 1)
    # the keystone: a button matsutake standing at the crown
    kx, ky = cx, cy - ry + d * .6
    cap = [(kx + ft * .75 * _m.cos(a), ky + ft * .2 - ft * .6 * _m.sin(a)) for a in [_m.pi * i / 16 for i in range(17)]]
    stem = [(kx - ft * .3, ky + ft * .2), (kx + ft * .3, ky + ft * .2), (kx + ft * .35, ky + ft * 1.1), (kx - ft * .35, ky + ft * 1.1)]
    cv.obj([stem], 1.)
    cv.hair(_C.hatch_poly([(kx, ky + ft * .2), (kx + ft * .3, ky + ft * .2), (kx + ft * .35, ky + ft * 1.1), (kx, ky + ft * 1.1)], 90, 1.))
    cv.obj([cap], 1.)
    cv.hair(form_hatch(cap, kx - ft * .3, ky - ft * .3, ft * .5, ft * 1.6, 1.1, -.3, 2.4, 1., 18))
    swell_outline(cv, cap, (-1., -1.), 2)
    # a cushion of moss at each foot
    for sg in (-1, 1):
        x0 = cx + sg * (rx - d)
        y0 = cy + ry - 1
        tufts = []
        for j in range(14):
            bx = x0 - sg * j * ft * .18 + rng.uniform(-.5, .5)
            ln = ft * rng.uniform(.4, .9)
            a = -_m.pi / 2 + rng.uniform(-.6, .6)
            tufts.append([(bx, y0), (bx + _m.cos(a) * ln, y0 + _m.sin(a) * ln)])
        cv.hair(tufts)
    return cv.svg()


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 6

    def sc(X, Y, W, H, mode, inner):
        body = small_scene(X, Y, W, H, seed) if mode == "s" else scene(X, Y, W, H, seed, 1. if mode == "t" else .8)
        return clip_to(f"gdn{mode}{int(H)}", inner, body)

    ft = max(5., min(14., h * .06))
    return form_plate(w, h, ctx, sc, "arched", "vignette", seed,
                      frame=lambda *a: _fir_arch(*a, ft=ft, seed=seed), ft=ft, fade=0.)
