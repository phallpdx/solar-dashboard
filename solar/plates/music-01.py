"""music-01 "Put this record on": the record plate.

Short  : a scroll frieze flowing out of a medallion that IS a record (grooves, sheen, label),
         crossed drumsticks behind it.
Medium : a 12-inch LP set in a carved roundel as the cartouche, a tonearm laid on its grooves,
         big acanthus volutes flowing out to both ends; crossed drumsticks behind it (egg) and
         tonight's moon phase engraved on the label (Night Palace).
Tall   : a gramophone scene in the cartouche, with a bar of swing ride rhythm cut into the
         pedestal tablet (egg).
"""
import sys
import math
import random
import datetime
import engraving_codex as C

_n, _d, _ell = C._n, C._d, C._ell_pts
PI = math.pi


# ------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------

def _circ(cx, cy, r):
    """A circle as two arcs (compact path data)."""
    return (f"M{_n(cx - r)},{_n(cy)}a{_n(r)},{_n(r)} 0 1,0 {_n(2 * r)},0"
            f"a{_n(r)},{_n(r)} 0 1,0 {_n(-2 * r)},0z")


def _arc(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    big = 1 if (a1 - a0) % (2 * PI) > PI else 0
    return f"M{_n(x0)},{_n(y0)}A{_n(r)},{_n(r)} 0 {big},1 {_n(x1)},{_n(y1)}"


def _moon_phase(date):
    try:
        d = datetime.datetime.strptime(date[:10], "%Y-%m-%d") + datetime.timedelta(hours=12)
    except Exception:
        return .3
    ref = datetime.datetime(2000, 1, 6, 18, 14)
    return ((d - ref).total_seconds() / 86400. / 29.530588) % 1.


def _moon(cx, cy, r, phase, uid):
    """Moon at its phase: dark part ruled, lit part white with stipple seas, outlined."""
    e = math.cos(2 * PI * phase)
    side = 1 if phase < .5 else -1
    lit = []
    for i in range(25):
        t = -PI / 2 + PI * i / 24
        lit.append((cx + side * r * math.cos(t), cy + r * math.sin(t)))
    for i in range(25):
        t = PI / 2 - PI * i / 24
        lit.append((cx + side * e * r * math.cos(t), cy + r * math.sin(t)))
    o = [f'<path d="{_circ(cx, cy, r)}" fill="{C.pat("M")}" stroke="none"/>',
         f'<path d="{_d(lit, True, .1)}" fill="#fff" stroke="none"/>']
    seas = [(.25, -.3, .28), (-.2, .15, .22), (.3, .35, .18)]
    sd = "".join(_circ(cx + a * r, cy + b * r, c * r) for a, b, c in seas)
    o.append(f'<clipPath id="{uid}"><path d="{_d(lit, True, .1)}"/></clipPath>'
             f'<path clip-path="url(#{uid})" d="{sd}" fill="{C.pat("S")}" stroke="none"/>')
    o.append(f'<path d="{_circ(cx, cy, r)}" fill="none" stroke="#000" stroke-width="1"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# the record
# ------------------------------------------------------------------------------------------

def record(cx, cy, R, phase=.3, uid="rec", label=True, detail=1.):
    """A black LP: white groove rings (.5 px at 1.5 pitch), track bands, two sheen sectors where
    the grooves are cut wider, an edge highlight, and a ruled label carrying the moon phase."""
    o = [f'<path d="{_circ(cx, cy, R)}" fill="#000" stroke="none"/>']
    RL = R * .34
    r0, r1 = RL + 3.5, R - 2.5
    gaps = {5, 12, 20, 26}
    rings, sheen = [], []
    k = 0
    r = r0
    a1, a2 = math.radians(-58), math.radians(122)
    while r < r1:
        if k not in gaps:
            rings.append(_circ(cx, cy, r))
            w = .32 * (1 - .4 * (r - r0) / max(1, r1 - r0))
            sheen.append(_arc(cx, cy, r, a1 - w, a1 + w) + _arc(cx, cy, r, a2 - w, a2 + w))
        k += 1
        r += 1.5 if detail >= 1 else 2.
    o.append(f'<path d="{"".join(rings)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(sheen)}" fill="none" stroke="#fff" stroke-width="1" stroke-linecap="butt"/>')
    o.append(f'<path d="{_circ(cx, cy, R - 1)}" fill="none" stroke="#fff" stroke-width=".5"/>')
    if label:
        o.append(f'<path d="{_circ(cx, cy, RL + 1.2)}" fill="#fff" stroke="none"/>')
        o.append(f'<path d="{_circ(cx, cy, RL)}" fill="{C.pat("L")}" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_circ(cx, cy, RL - 2.5)}" fill="none" stroke="#000" stroke-width=".5"/>')
        if RL > 14:
            mr = RL * .3
            o.append(f'<path d="{_circ(cx, cy - RL * .5, mr + 1.5)}" fill="#fff" stroke="none"/>')
            o.append(_moon(cx, cy - RL * .5, mr, phase, uid + "m"))
            st = ""
            for sx, sy, s in ((-.55, -.5, 1.4), (.55, -.42, 1.1), (-.42, -.2, .8), (.46, -.75, .8)):
                x, y = cx + sx * RL, cy + sy * RL
                st += f"M{_n(x - s)},{_n(y)}h{_n(2 * s)}M{_n(x)},{_n(y - s)}v{_n(2 * s)}"
            o.append(f'<path d="{st}" stroke="#000" stroke-width=".5" fill="none"/>')
            sc = C.Canvas()
            sticks = RL > 22
            L = RL * .62
            for sgn in ((-1, 1) if sticks else ()):
                an = math.radians(-90 + sgn * 38)
                ux, uy = math.cos(an), math.sin(an)
                bx_, by_ = cx, cy + RL * .5
                drumstick(sc, bx_ - ux * L * .5 + sgn * 0, by_ - uy * L * .5, bx_ + ux * L * .5, by_ + uy * L * .5, max(1.6, RL * .07))
            o.append(sc.svg())
        o.append(f'<path d="{_circ(cx, cy, 3)}" fill="#fff" stroke="#000" stroke-width="1"/>')
        o.append(f'<path d="{_circ(cx, cy, 1.6)}" fill="#000" stroke="none"/>')
    return "".join(o)


def tonearm(px, py, nx, ny, s=1.):
    """A tonearm pivoting at (px, py) and resting its stylus at (nx, ny)."""
    cv = C.Canvas()
    ang = math.atan2(ny - py, nx - px)
    L = math.hypot(nx - px, ny - py)
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux

    def P(a, b):
        return (px + ux * a + vx * b, py + uy * a + vy * b)
    cw = [P(-7 * s, 5 * s), P(-19 * s, 5 * s), P(-19 * s, -5 * s), P(-7 * s, -5 * s)]
    cv.obj([cw], 1.)
    for t in range(9, 19, 2):
        cv.hair([P(-t * s, 5 * s), P(-t * s, -5 * s)])
    cv.heavy([P(-7 * s, -4.2 * s), P(-19 * s, -4.2 * s)])
    hw = 2.2 * s
    spine = []
    for i in range(31):
        t = i / 30
        spine.append(P(L * .9 * t, math.sin(t * PI) * L * .06))
    left = [(x + vx * hw, y + vy * hw) for x, y in spine]
    right = [(x - vx * hw, y - vy * hw) for x, y in spine]
    cv.obj([left + right[::-1]], 1.)
    cv.line([(x + vx * hw * .55, y + vy * hw * .55) for x, y in spine])
    cv.hair([(x + vx * hw * .1, y + vy * hw * .1) for x, y in spine])
    ex, ey = spine[-1]
    hs = 5 * s
    a2 = ang + .35
    ux2, uy2 = math.cos(a2), math.sin(a2)
    vx2, vy2 = -uy2, ux2
    shell = [(ex + vx2 * hs * .7, ey + vy2 * hs * .7), (ex + ux2 * hs * 2.6 + vx2 * hs * .9, ey + uy2 * hs * 2.6 + vy2 * hs * .9),
             (ex + ux2 * hs * 2.6 - vx2 * hs * .9, ey + uy2 * hs * 2.6 - vy2 * hs * .9), (ex - vx2 * hs * .7, ey - vy2 * hs * .7)]
    cv.obj([shell], 1.)
    for hl in C.hatch_poly(shell, math.degrees(a2) + 90, 1.5):
        cv.hair(hl)
    cv.heavy([shell[1], shell[2]])
    fx, fy = ex + ux2 * hs * 1.2 - vx2 * hs * .9, ey + uy2 * hs * 1.2 - vy2 * hs * .9
    cv.line([(fx, fy), (fx - vx2 * hs * .9 + ux2 * 2, fy - vy2 * hs * .9 + uy2 * 2)])
    rr = 7 * s
    cv.obj([_ell(px, py, rr, rr, 40)[:-1]], 1.)
    q = rr - 1.5
    while q > 1.6:
        cv.hair(_ell(px, py, q, q, 32))
        q -= 1.5
    cv.heavy(_ell(px, py, rr - .6, rr - .6, 32, PI * .1, PI * .9))
    cv.obj([_ell(px, py, 2.2, 2.2, 12)[:-1]], 1.)
    cv.line(_ell(px, py, 1., 1., 8))
    return cv.svg()


# ------------------------------------------------------------------------------------------
# drumsticks (into a canvas)
# ------------------------------------------------------------------------------------------

def drumstick(cv, x0, y0, x1, y1, w=5.):
    """A turned hickory stick from butt (x0, y0) to tip (x1, y1): white body, grain lines along it,
    shadow on one side, an oval bead tip."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    vx, vy = -uy, ux

    def hw(t):
        return w / 2 * (1 - .62 * C._smooth(.7, .96, t))
    n = 40
    ts = [i / n * .96 for i in range(n + 1)]
    L_ = [(x0 + ux * L * t + vx * hw(t), y0 + uy * L * t + vy * hw(t)) for t in ts]
    R_ = [(x0 + ux * L * t - vx * hw(t), y0 + uy * L * t - vy * hw(t)) for t in ts]
    tx, ty = x0 + ux * L * .975, y0 + uy * L * .975
    a, b = w * .55, w * .36
    tip = [(tx + ux * a * math.cos(t) + vx * b * math.sin(t), ty + uy * a * math.cos(t) + vy * b * math.sin(t))
           for t in [2 * PI * i / 20 for i in range(20)]]
    cv.obj([L_ + R_[::-1]], 1.)
    for f in (-.72, -.42, -.12, .3):
        cv.hair([(x0 + ux * L * t + vx * hw(t) * f, y0 + uy * L * t + vy * hw(t) * f) for t in ts])
    cv.heavy([(x0 + ux * L * t + vx * hw(t) * .8, y0 + uy * L * t + vy * hw(t) * .8) for t in ts])
    cv.obj([tip], 1.)
    cv.hair([(tx - ux * a * .5 + vx * b * .4, ty - uy * a * .5 + vy * b * .4), (tx + ux * a * .5 + vx * b * .4, ty + uy * a * .5 + vy * b * .4)])


# ------------------------------------------------------------------------------------------
# a bar of swing ride rhythm (staff, ride-cymbal x-heads, swung eighths): an egg
# ------------------------------------------------------------------------------------------

def swing_bar(x, y, w, h):
    o = []
    sp = min(h / 5.2, 4.5)
    top = y + h / 2 - 2 * sp
    st = "".join(f"M{_n(x + 4)},{_n(top + i * sp)}h{_n(w - 8)}" for i in range(5))
    bars = f"M{_n(x + 4)},{_n(top)}v{_n(4 * sp)}M{_n(x + w - 4)},{_n(top)}v{_n(4 * sp)}"
    o.append(f'<path d="{st}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{bars}" stroke="#000" stroke-width="1" fill="none"/>')
    o.append(f'<path d="M{_n(x + w - 7)},{_n(top)}v{_n(4 * sp)}" stroke="#000" stroke-width="1.5"/>')
    cx0 = x + 10
    o.append(f'<path d="M{_n(cx0)},{_n(top + sp)}v{_n(2 * sp)}M{_n(cx0 + 3)},{_n(top + sp)}v{_n(2 * sp)}" stroke="#000" stroke-width="1.5"/>')

    def four(fx, fy, s):
        return f"M{_n(fx + s * .4)},{_n(fy + s)}V{_n(fy - s)}L{_n(fx - s * .6)},{_n(fy + s * .3)}H{_n(fx + s * .8)}"
    tx = x + 22
    o.append(f'<path d="{four(tx, top + sp, sp * .95)}{four(tx, top + 3 * sp, sp * .95)}" stroke="#000" stroke-width="1" fill="none"/>')
    x0, x1 = x + 34, x + w - 14
    beat = (x1 - x0) / 4
    ry = top - sp * .5
    heads, stems, beams = [], [], []
    s = sp * .42
    for bi in range(4):
        bx = x0 + bi * beat + beat * .2
        notes = [bx] if bi % 2 == 0 else [bx, bx + beat * .62]
        for nx_ in notes:
            heads.append(f"M{_n(nx_ - s)},{_n(ry - s)}l{_n(2 * s)},{_n(2 * s)}M{_n(nx_ - s)},{_n(ry + s)}l{_n(2 * s)},{_n(-2 * s)}")
            stems.append(f"M{_n(nx_ + s)},{_n(ry)}v{_n(-sp * 2.6)}")
        if len(notes) == 2:
            beams.append(f"M{_n(notes[0] + s)},{_n(ry - sp * 2.6)}H{_n(notes[1] + s)}")
            hx = bx
            hy = top + 4 * sp + sp * .5
            heads.append(f"M{_n(hx - s)},{_n(hy - s)}l{_n(2 * s)},{_n(2 * s)}M{_n(hx - s)},{_n(hy + s)}l{_n(2 * s)},{_n(-2 * s)}")
    o.append(f'<path d="{"".join(heads)}" stroke="#000" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{"".join(stems)}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{"".join(beams)}" stroke="#000" stroke-width="1.5" fill="none" stroke-linecap="butt"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# roundel moulding round the record
# ------------------------------------------------------------------------------------------

def roundel(cx, cy, R, bw):
    """A carved ring moulding from R to R+bw: white band with contour lines, black sunk fillet
    on the inside, a bead row."""
    o = [f'<path d="{_circ(cx, cy, R + bw)}{_circ(cx, cy, R)}" fill="#fff" stroke="#000" stroke-width="1" fill-rule="evenodd"/>']
    o.append(f'<path d="{"".join(_circ(cx, cy, R + bw * f) for f in (.6, .72, .84, .93))}" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(f'<path d="{_circ(cx, cy, R + bw * .46)}" fill="none" stroke="#000" stroke-width="1"/>')
    sh = "".join(_arc(cx, cy, R + bw * f, PI * -.05, PI * .7) for f in (.66, .78, .9))
    o.append(f'<path d="{sh}" fill="none" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="{_circ(cx, cy, R + bw * .15)}" fill="none" stroke="#000" stroke-width="{_n(bw * .3)}"/>')
    rb = R + bw * .3
    n = int(2 * PI * rb / 4.2)
    o.append(f'<path d="{_circ(cx, cy, rb)}" fill="none" stroke="#000" stroke-width="1.5" '
             f'stroke-dasharray="0 {_n(2 * PI * rb / n)}" stroke-linecap="round"/>')
    return "".join(o)


# ------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------

def _band(w, h, seed, phase):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    R = gh / 2 - 1.5
    cx, cy = w / 2, top + gh / 2
    st = C.Canvas()
    L = R * 1.75
    for sgn in (-1, 1):
        a = math.radians(-90 + sgn * 66)
        ux, uy = math.cos(a), math.sin(a)
        drumstick(st, cx - ux * L, cy - uy * L, cx + ux * L, cy + uy * L, max(3.5, gh * .085))
    sb = C.Canvas()
    C.scroll_band(0, top, w, gh, seed, R * 2 + 28, cv=sb, r_scale=1.15 * max(1., 62. / gh))
    sb.extend(st)
    o.append(C._clip(C._uid("mb", w, h, seed), 0, top, w, gh, sb.svg()))
    bw = max(3.5, gh * .06)
    o.append(roundel(cx, cy, R - bw, bw))
    o.append(record(cx, cy, R - bw, phase, C._uid("mr", w, h), label=True, detail=1 if R > 30 else 0))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _medium(w, h, seed, phase):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cx, cy = w / 2, (gy0 + gy1) / 2
    bw = max(6., gh * .045)
    R = gh / 2 + 2 - bw
    cw = 2 * (R + bw)
    occ = [("c", cx, cy, R + bw + 4)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r * .95)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(8, gh * .06), rmax=r * .8,
                   max_n=14, edge=.55, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("mm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    o.append(roundel(cx, cy, R, bw))
    o.append(record(cx, cy, R, phase, C._uid("mrec", w, h)))
    pa = math.radians(32)
    px, py = cx + (R + bw * .5) * math.cos(pa), cy + (R + bw * .5) * math.sin(pa)
    na = math.radians(-22)
    nx, ny = cx + R * .74 * math.cos(na), cy + R * .74 * math.sin(na)
    fc = C.Canvas()
    for k, (dg, ln, sg) in enumerate(((5, gh * .3, 1), (70, gh * .26, -1), (-30, gh * .2, 1))):
        C.acanthus_frond(px, py, dg, ln, 2, 24, .9 * sg, 4.4 * sg, seed + 11 * k, cv=fc)
    o.append(C._clip(C._uid("mp", w, h, seed), 0, gy0, w, gh, fc.svg()))
    o.append(tonearm(px, py, nx, ny, max(.9, gh / 130)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


# ------------------------------------------------------------------------------------------
# the tall scene: a gramophone with acanthus sprouting from its horn, his dog listening
# ------------------------------------------------------------------------------------------

_DOG_SIT = ("M.6,0C-.4,-1.6 -.2,-4 1.4,-5.2C2.6,-6 3.6,-6.6 4.3,-7.7L4.6,-9.5C4.8,-10.5 5.9,-10.9 6.7,-10.5"
            "L7.3,-9.7L8.9,-9.3C9.6,-9.1 9.6,-8.2 8.9,-8L7.4,-7.6C6.9,-6.6 6.9,-5.3 7,-4.3L7.2,-.4L7.8,0"
            "H5.9L5.8,-3.2L4.4,-1.6L4.6,-.4L5.2,0Z")


def _parse_poly(d, x, y, s):
    """Flatten an absolute M/L/H/V/C/Z path to points, placed at (x, y) and scaled by s."""
    import re
    toks = re.findall(r"[MLHVCZ]|-?\d*\.?\d+", d)
    pts, i, cur, cmd = [], 0, (0., 0.), None
    while i < len(toks):
        t = toks[i]
        if t in "MLHVCZ":
            cmd = t
            i += 1
            if t == "Z":
                continue
        if cmd in "ML":
            cur = (float(toks[i]), float(toks[i + 1]))
            pts.append(cur)
            i += 2
        elif cmd == "H":
            cur = (float(toks[i]), cur[1])
            pts.append(cur)
            i += 1
        elif cmd == "V":
            cur = (cur[0], float(toks[i]))
            pts.append(cur)
            i += 1
        elif cmd == "C":
            c1 = (float(toks[i]), float(toks[i + 1]))
            c2 = (float(toks[i + 2]), float(toks[i + 3]))
            e = (float(toks[i + 4]), float(toks[i + 5]))
            for k in range(1, 9):
                t_ = k / 8
                a, b = (1 - t_) ** 3, 3 * (1 - t_) ** 2 * t_
                c, dd = 3 * (1 - t_) * t_ ** 2, t_ ** 3
                pts.append((a * cur[0] + b * c1[0] + c * c2[0] + dd * e[0], a * cur[1] + b * c1[1] + c * c2[1] + dd * e[1]))
            cur = e
            i += 6
        else:
            i += 1
    return [(x + px * s, y + py * s) for px, py in pts]


def dog(cv, x, y, s):
    """His dog sitting, facing right, feet at (x, y): fur in bulino lines that follow the body."""
    poly = _parse_poly(_DOG_SIT, x, y, s)
    cv.obj([poly], 1.)
    # fur: curved strokes running down the back and chest, denser on the shadow (rear) side
    for hl in C.hatch_poly(poly, 75, 2.):
        cv.hair(hl)
    rear = [(x - 1 * s, y), (x + 3.2 * s, y - 7 * s), (x + 4.4 * s, y - 2 * s), (x + 4.6 * s, y)]
    for hl in C.hatch_poly(rear, 15, 1.5):
        cv.hair(hl)
    # haunch line, ear (black), eye, collar
    cv.line([(x + 1 * s, y - 1.2 * s), (x - .2 * s, y - 2.8 * s), (x + .4 * s, y - 4.4 * s), (x + 2 * s, y - 5 * s)])
    ear = [(x + 5.0 * s, y - 9.6 * s), (x + 5.9 * s, y - 9.7 * s), (x + 6.0 * s, y - 8.0 * s), (x + 5.4 * s, y - 7.3 * s)]
    cv.obj([ear], 1.)
    cv.line(C.hatch_poly(ear, 0, .8))
    cv.obj([_ell(x + 7.5 * s, y - 9.0 * s, .45 * s, .45 * s, 10)[:-1]], 0)
    cv.line(_ell(x + 7.5 * s, y - 9.0 * s, .2 * s, .2 * s, 8))
    cv.heavy([(x + 4.5 * s, y - 7.6 * s), (x + 6.9 * s, y - 6.6 * s)])
    cv.obj([_ell(x + 9.0 * s, y - 8.75 * s, .35 * s, .35 * s, 10)[:-1]], 0)
    cv.line(_ell(x + 9.0 * s, y - 8.75 * s, .15 * s, .15 * s, 6))


def gramophone(fx, fy, fw, fh, phase, uid, seed):
    o = []
    rng = random.Random(seed)
    # night sky (Night Palace) and the room: mid ruled ground everywhere first
    o.append(f'<path d="M{_n(fx)},{_n(fy)}h{_n(fw)}v{_n(fh)}h{_n(-fw)}z" fill="{C.pat("M")}" stroke="none"/>')
    # a tall arched window behind, with the moon in it
    wx0, wx1 = fx + fw * .52, fx + fw * .92
    wy0, wy1 = fy + fh * .04, fy + fh * .55
    wr = (wx1 - wx0) / 2
    win = [(wx0, wy1)] + [((wx0 + wx1) / 2 - wr * math.cos(PI * i / 20), wy0 + wr - wr * math.sin(PI * i / 20)) for i in range(21)] + [(wx1, wy1)]
    o.append(f'<path d="{_d(win, True, .1)}" fill="{C.pat("G")}" stroke="#000" stroke-width="1.5"/>')
    mx, my, mr = (wx0 + wx1) / 2 + wr * .25, wy0 + wr * 1.0, wr * .32
    halo = "".join(_circ(mx, my, mr + 3 + 2.5 * k) for k in range(3))
    o.append(f'<path d="{_circ(mx, my, mr + 2)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{halo}" fill="none" stroke="#fff" stroke-width=".5"/>')
    o.append(_moon(mx, my, mr, phase, uid + "mn"))
    stars = ""
    for k in range(7):
        sx = wx0 + 6 + (wx1 - wx0 - 12) * rng.random()
        sy = wy0 + 6 + (wy1 - wy0 - 12) * rng.random()
        if math.hypot(sx - mx, sy - my) < mr + 10:
            continue
        r_ = rng.choice((1., 1.5, 2.))
        stars += f"M{_n(sx - r_)},{_n(sy)}h{_n(2 * r_)}M{_n(sx)},{_n(sy - r_)}v{_n(2 * r_)}"
    o.append(f'<path d="{stars}" stroke="#fff" stroke-width="1" fill="none"/>')
    # window bars
    bars = f"M{_n((wx0 + wx1) / 2)},{_n(wy0)}V{_n(wy1)}M{_n(wx0)},{_n(wy0 + wr + (wy1 - wy0 - wr) * .45)}H{_n(wx1)}"
    o.append(f'<path d="{bars}" stroke="#fff" stroke-width="1.5" fill="none"/>')
    o.append(f'<path d="{bars}" stroke="#000" stroke-width=".5" fill="none"/>')
    # wainscot: vertical boards under the window line
    wy = fy + fh * .6
    o.append(f'<path d="M{_n(fx)},{_n(wy)}h{_n(fw)}v{_n(fh * .2)}h{_n(-fw)}z" fill="{C.pat("V")}" stroke="none"/>')
    o.append(f'<path d="M{_n(fx)},{_n(wy)}h{_n(fw)}M{_n(fx)},{_n(wy + 2)}h{_n(fw)}" stroke="#000" stroke-width="1" fill="none"/>')
    # floor: boards in perspective
    fl = fy + fh * .8
    o.append(f'<path d="M{_n(fx)},{_n(fl)}h{_n(fw)}v{_n(fh * .2)}h{_n(-fw)}z" fill="{C.pat("L")}" stroke="none"/>')
    vpx, vpy = fx + fw * .5, fy - fh * .6
    fd = ""
    for k in range(-16, 17):
        x0 = fx + fw / 2 + k * fw / 14
        t = (fy + fh - fl) / (fy + fh - vpy)
        fd += f"M{_n(x0 + (vpx - x0) * t)},{_n(fl)}L{_n(x0)},{_n(fy + fh)}"
    o.append(f'<path d="{fd}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{"".join(f"M{_n(fx)},{_n(fl + q)}h{_n(fw)}" for q in (1.5, 4, 7.5, 12, 18, 26, 36))}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="M{_n(fx)},{_n(fl)}h{_n(fw)}" stroke="#000" stroke-width="1.5" fill="none"/>')

    cv = C.Canvas()
    # cabinet
    bx0, bx1 = fx + fw * .40, fx + fw * .84
    by0, by1 = fy + fh * .64, fy + fh * .86
    dep = fh * .07
    sk = fw * .05
    topf = [(bx0, by0), (bx1, by0), (bx1 - sk, by0 - dep), (bx0 - sk, by0 - dep)]
    front = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
    side = [(bx0, by0), (bx0 - sk, by0 - dep), (bx0 - sk, by1 - dep), (bx0, by1)]
    cv.obj([front], 1.)
    for k in range(int((by1 - by0) / 1.5)):
        yy = by0 + 1 + k * 1.5
        if k % 7 in (3,):
            continue
        cv.hair([(bx0 + 1 + i * (bx1 - bx0 - 2) / 30, yy + .5 * math.sin(i * .7 + k * 1.3)) for i in range(31)])
    pin = 5
    pnl = [(bx0 + pin, by0 + pin), (bx1 - pin, by0 + pin), (bx1 - pin, by1 - pin), (bx0 + pin, by1 - pin)]
    cv.obj([pnl], 1.)
    cv.hair(C.hatch_poly(pnl, 0, 1.5, .5))
    cv.heavy([pnl[0], pnl[1]])
    cv.heavy([pnl[0], pnl[3]])
    # feet
    for fxp in (bx0 + 4, bx1 - 4):
        cv.obj([[(fxp - 4, by1), (fxp + 4, by1), (fxp + 2.5, by1 + 5), (fxp - 2.5, by1 + 5)]], 1.)
        cv.line(C.hatch_poly([(fxp - 4, by1), (fxp + 4, by1), (fxp + 2.5, by1 + 5), (fxp - 2.5, by1 + 5)], 90, 1.5))
    cv.obj([side], 1.)
    cv.line(C.hatch_poly(side, 90, 1.5))
    cv.obj([topf], 1.)
    cv.hair(C.hatch_poly(topf, 0, 3))
    # crank on the right
    cx_, cy_ = bx1 + 2, by0 + (by1 - by0) * .45
    cv.obj([[(cx_, cy_ - 1.5), (cx_ + 9, cy_ - 1.5), (cx_ + 9, cy_ + 1.5), (cx_, cy_ + 1.5)]], 1.)
    cv.obj([[(cx_ + 7.5, cy_), (cx_ + 10.5, cy_), (cx_ + 10.5, cy_ + 12), (cx_ + 7.5, cy_ + 12)]], 1.)
    cv.line([(cx_ + 9, cy_ + 1), (cx_ + 9, cy_ + 11)])
    cv.obj([_ell(cx_ + 9, cy_ + 13.5, 3, 2.2, 12)[:-1]], 1.)
    cv.line(C.hatch_poly(_ell(cx_ + 9, cy_ + 13.5, 3, 2.2, 12)[:-1], 0, 1.))
    # platter and record (an ellipse on the top face)
    pcx, pcy = (bx0 + bx1) / 2 - sk / 2 - fw * .03, by0 - dep / 2
    prx, pry = (bx1 - bx0) * .38, dep * .42
    cv.obj([_ell(pcx, pcy, prx, pry, 60)[:-1]], 1.)
    pd = [_ell(pcx, pcy, prx - 1.2, pry - .5, 60)[:-1]]
    cv.obj(pd, 0)
    k = 0
    while pry - 1.2 - k * .5 > 1.2:
        cv.line(_ell(pcx, pcy, prx - 1.2 - k * 1.5, pry - 1. - k * .5, 60))
        k += 1
    cv.obj([_ell(pcx, pcy, prx * .3, pry * .3, 30)[:-1]], 1.)
    cv.hair(C.hatch_poly(_ell(pcx, pcy, prx * .3, pry * .3, 30)[:-1], 0, 1.5))
    # tonearm on the deck
    tax, tay = bx1 - sk * .8 - 6, by0 - dep * .75
    cv.obj([_ell(tax, tay, 3.5, 2, 12)[:-1]], 1.)
    cv.heavy([(tax, tay), (tax - prx * .55, tay + pry * .1), (tax - prx * .7, tay + pry * .55)])
    # the horn: neck rising from the back of the deck, then a flared cone opening to the left
    nx, ny = bx1 - sk - fw * .07, by0 - dep
    elbow = (nx + fw * .01, fy + fh * .42)
    hw = 3.
    neck = [(nx, ny), (nx + 1.5, (ny + elbow[1]) / 2), (elbow[0], elbow[1] + 4)]
    cv.obj([[(x - hw, y) for x, y in neck] + [(x + hw, y) for x, y in neck][::-1]], 1.)
    cv.line([(x + hw * .5, y) for x, y in neck])
    cv.hair([(x + hw * .05, y) for x, y in neck])
    mcx, mcy = fx + fw * .2, fy + fh * .27
    mry = fh * .2
    mrx = fw * .075
    # centre line: a gentle rising curve from the elbow to the mouth
    ax = []
    n = 40
    for i in range(n + 1):
        t = i / n
        qx = (1 - t) ** 2 * elbow[0] + 2 * (1 - t) * t * (elbow[0] - fw * .18) + t * t * mcx
        qy = (1 - t) ** 2 * elbow[1] + 2 * (1 - t) * t * (elbow[1] - fh * .02) + t * t * mcy
        ax.append((qx, qy))
    rad = [3.2 + (mry - 3.2) * (i / n) ** 2.6 for i in range(n + 1)]
    Rb = C._Rib(ax, rad, rad)
    cv.obj([Rb.outline()], 1.)
    # petal seams along the cone, shading heavier underneath, rings of the flare across it
    for s in (.8, .55, .28, 0., -.28, -.55, -.8):
        cv.line(Rb.contour(s, 0., 1.)) if s in (.55, 0., -.55) else cv.hair(Rb.contour(s, 0., 1.))
    for s in (-.4, -.66, -.9, -.12, -.94):
        cv.hair(Rb.contour(s, .15, 1.))
    for s in (-.72, -.86):
        cv.line(Rb.contour(s, .1, 1.))
    for u in (.25, .45, .6, .72, .82, .9, .96):
        cv.hair([Rb.at(u, s / 10) for s in range(-10, 11)])
    # mouth: a narrow tall ellipse facing left, rim rolled, throat dark inside
    tilt = math.radians(8)

    def mouth(t, k=1.):
        ex, ey = mrx * k * math.cos(t), mry * k * math.sin(t)
        return (mcx + ex * math.cos(tilt) - ey * math.sin(tilt), mcy + ex * math.sin(tilt) + ey * math.cos(tilt))
    rim = [mouth(2 * PI * i / 72) for i in range(72)]
    cv.obj([rim], 1.5)
    inner = [mouth(2 * PI * i / 72, .86) for i in range(72)]
    cv.obj([inner], 1.)
    cv.line(C.hatch_poly(inner, 8, 1.5))
    for kk in (.7, .52):
        cv.hair([mouth(2 * PI * i / 48, kk) for i in range(49)])
    th = [mouth(2 * PI * i / 24, .25) for i in range(24)]
    cv.obj([th], 0)
    for q in range(4):
        cv.line([mouth(2 * PI * i / 24, .25 - q * .055) for i in range(25)])
    cv.hair([mouth(2 * PI * i / 72, .93) for i in range(72)])
    # acanthus sprouting from the lip of the bell, curling outward
    for t, ang, ln, sg in ((-PI * .5, -115, fw * .26, 1), (PI * .42, 150, fw * .2, -1), (PI * .97, 178, fw * .14, 1)):
        px, py = mouth(t, 1.02)
        C.acanthus_frond(px, py, ang, ln, 3, 26, .9 * sg, 4.5 * sg, seed + int(ang), cv=cv)
    # his dog, sitting at the left, listening to the horn
    dog(cv, fx + fw * .05, fl + fh * .1, fh * .36 / 11.)
    return "".join(o) + cv.svg()


def _tall(w, h, seed, phase, density=1.):
    from engraving_codex import (_pair_unit, Canvas, dark_ground, fill_scrolls, cartouche, palmette,
                                 ribbon_banner, pedestal, scroll_band, _clip, _uid, _CR)
    rng = random.Random(seed)
    o = []
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = Canvas()
    main = Canvas()
    r1 = min(pw * .17, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r1 * .55)
        vy = py0 + ph - r1 * 1.1
        _pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .14, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (cw * .5 + r2 * .55)
        vy = py0 + r2 * 1.1
        _pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .04), rmax=r1 * .9,
                 max_n=int(9 * density), edge=.55, cv=cv)
    cv.extend(main)
    o.append(_clip(_uid("mt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, inner_d = cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    bw = max(5., min(cw, ch) * .07)
    a, b = cw / 2 - bw * 1.6, ch / 2 - bw * 1.6
    cid = _uid("mtc", w, h, seed)
    o.append(f'<clipPath id="{cid}"><path d="{inner_d}"/></clipPath><g clip-path="url(#{cid})">'
             + gramophone(cx - a, cy - b, 2 * a, 2 * b, phase, cid, seed) + "</g>")
    o.append(palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bsvg, face = ribbon_banner(cx, cy + ch * .5, cw * 1.3, min(16, ph * .05), .04, rng.randrange(1 << 20))
    o.append(bsvg)
    # the banner face carries a running bar of eighth notes (the jazz line, no lettering)
    bh = min(16, ph * .05)
    notes = ""
    for i in range(3, len(face) - 3, 3):
        x_, y_ = face[i]
        yy = y_ + bh * (.18 if (i // 3) % 2 else -.05)
        notes += _circ(x_, yy + bh * .1, bh * .14)
    o.append(f'<path d="{notes}" fill="#000" stroke="none"/>')
    stems = "".join(f"M{_n(face[i][0] + bh * .14)},{_n(face[i][1] + bh * ((.18 if (i // 3) % 2 else -.05) + .1))}V{_n(face[i][1] - bh * .32)}"
                    for i in range(3, len(face) - 3, 3))
    o.append(f'<path d="{stems}" stroke="#000" stroke-width=".5" fill="none"/>')
    beam = _d([(face[i][0] + bh * .14, face[i][1] - bh * .32) for i in range(3, len(face) - 3, 3)], tol=.1)
    o.append(f'<path d="{beam}" stroke="#000" stroke-width="1" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(swing_bar(tx + 3, ty + 2, tw - 6, th - 4))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(_clip(_uid("mf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                       scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2, r_scale=1.15, n=2)))
        o.append(palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{_CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    date = ctx.get("date", "")
    seed = sum(map(ord, date)) + 7 * int(ctx.get("sheet", 0) or 0)
    phase = _moon_phase(date)
    if h < 110:
        body = _band(w, h, seed, phase)
    elif h <= 260:
        body = _medium(w, h, seed, phase)
    else:
        body = _tall(w, h, seed, phase, .8 if h < 440 else 1.)
    return C.svg_doc(w, h, body)
