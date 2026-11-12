"""Music and shows: a spinning record with its tonearm, crossed drumsticks behind it (Parker's sticks),
set in the house cartouche between carved acanthus. Tall plates add a snare drum in front."""
import sys
import math
import random
import engraving_codex as C

TAU = 2 * math.pi
_n = C._n


def _circ(cx, cy, r, n=None, a0=0., a1=TAU):
    n = n or max(24, int(abs(a1 - a0) * r / 1.6))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _ell(cx, cy, rx, ry, n=None, a0=0., a1=TAU):
    n = n or max(24, int(abs(a1 - a0) * max(rx, ry) / 1.6))
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _inside(poly, x, y):
    c = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (x1 - x0) * (y - y0) / (y1 - y0):
            c = not c
    return c


def _seg_keep(lines, keep, step=.8):
    """Split 2-point lines, keeping the parts where keep(x, y) is true."""
    out = []
    for (x0, y0), (x1, y1) in lines:
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        cur = []
        for i in range(n + 1):
            t = i / n
            p = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if keep(*p):
                cur.append(p)
            else:
                if len(cur) > 1:
                    out.append([cur[0], cur[-1]])
                cur = []
        if len(cur) > 1:
            out.append([cur[0], cur[-1]])
    return out


# ----------------------------------------------------------------------------------------------
# the subject pieces (all drawn into one Canvas, in paint order)
# ----------------------------------------------------------------------------------------------

def drumstick(cv, x0, y0, x1, y1, wid):
    """A turned hickory stick from butt (x0, y0) to bead tip (x1, y1): taper, shoulder, olive bead,
    lengthwise bulino shading dark on the lower side, grain flecks."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    if ny < 0:                       # +normal points down: the shadow side
        nx, ny = -nx, -ny
    bead_r = wid * .62
    neck = L - bead_r * 1.7

    def half(t):                     # t: distance from butt
        if t < L * .7:
            return wid / 2
        if t < neck:
            k = (t - L * .7) / (neck - L * .7)
            return wid / 2 * (1 - .62 * k * k ** .3)
        return wid * .19

    ts = [neck * i / 24 for i in range(25)]
    up = [(x0 + ux * t - nx * half(t), y0 + uy * t - ny * half(t)) for t in ts]
    dn = [(x0 + ux * t + nx * half(t), y0 + uy * t + ny * half(t)) for t in ts]
    body = up + dn[::-1]
    cv.obj([body], 1.)
    for f, hv in ((.88, 2), (.72, 1), (.56, 0), (.40, 0), (.24, 0), (-.62, 0)):
        pl = [(x0 + ux * t + nx * half(t) * f, y0 + uy * t + ny * half(t) * f) for t in ts[1:-1]]
        (cv.heavy if hv == 2 else cv.line if hv else cv.hair)(pl)
    # butt end: a small ellipse cap
    cap = _ell(0, 0, wid * .22, wid / 2, 20)
    cv.hair([[(x0 + ux * p[0] + nx * p[1], y0 + uy * p[0] + ny * p[1]) for p in cap]])
    # the olive bead
    bx, by = x0 + ux * (L - bead_r), y0 + uy * (L - bead_r)
    bead = [(bx + ux * bead_r * 1.05 * math.cos(a) + nx * bead_r * .78 * math.sin(a),
             by + uy * bead_r * 1.05 * math.cos(a) + ny * bead_r * .78 * math.sin(a))
            for a in [TAU * i / 28 for i in range(28)]]
    cv.obj([bead], 1.)
    cv.hair(_seg_keep(C.hatch_poly(bead, math.degrees(math.atan2(uy, ux)), 1.5),
                      lambda x, y: (x - bx) * nx + (y - by) * ny > -bead_r * .05))


def record_svg(cx, cy, R, seed=0):
    """A black LP seen face on: a solid vinyl disc cut with fine white groove rules, three darker
    track gaps, a bow-tie of sheen (white with black hairline grooves) and a bright rim. Raw SVG."""
    rng = random.Random(seed)
    rl = R * .34
    o = [f'<path d="{C._d(_circ(cx, cy, R), True, .1)}" fill="#000" stroke="none"/>']
    rs = []
    r = R - 2.4
    gaps = set(rng.sample(range(4, max(7, int((R - rl) / 1.5) - 3)), 3))
    k = 0
    while r > rl + 2.5:
        k += 1
        if k not in gaps:
            rs.append(r)
        r -= 1.5
    sheen = (math.radians(222), math.radians(42))
    wd, wc = .42, .13                   # soft sheen half-width; its bright core
    thin, thick = [], []
    for r in rs:
        for s in sheen:
            a0, a1 = s + wd + .03 * math.sin(r), s + math.pi - wd - .03 * math.sin(r * 1.3)
            thin.append(C._d(_circ(cx, cy, r, None, a0, a1), tol=.15))
            thick.append(C._d(_circ(cx, cy, r, None, s - wd, s - wc), tol=.15))
            thick.append(C._d(_circ(cx, cy, r, None, s + wc, s + wd), tol=.15))
    o.append(f'<path d="{"".join(thin)}" stroke="#fff" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{"".join(thick)}" stroke="#fff" stroke-width="1" fill="none"/>')
    wed = []
    for s in sheen:
        pts = _circ(cx, cy, R - 2, 12, s - wc, s + wc) + _circ(cx, cy, rl + 2, 4, s + wc * .5, s - wc * .5)
        wed.append(C._d(pts, True, .1))
    o.append(f'<path d="{"".join(wed)}" fill="#fff" stroke="none"/>')
    ln = []
    r = R - 2.6
    while r > rl + 2.6:
        f = (r - rl) / (R - rl)
        ww = wc * (.5 + .5 * f)
        for s in sheen:
            ln.append(C._d(_circ(cx, cy, r, None, s - ww, s + ww), tol=.15))
        r -= 1.5
    o.append(f'<path d="{"".join(ln)}" stroke="#000" stroke-width=".5" fill="none"/>')
    o.append(f'<path d="{C._d(_circ(cx, cy, R - 1.1), True, .1)}" stroke="#fff" stroke-width=".5" fill="none"/>')
    return "".join(o)


def record_label(cv, cx, cy, R):
    """The paper label: ring, shadow crescent in bulino, printed rules and a small P monogram."""
    rl = R * .34
    lab = _circ(cx, cy, rl)
    cv.obj([lab], 1.)
    cv.hair(_circ(cx, cy, rl - 1.6))
    cv.hair(_seg_keep(C.hatch_poly(lab, 30, 1.5),
                      lambda x, y: math.hypot(x - (cx - rl * .28), y - (cy - rl * .3)) > rl * .98))
    for s in (-1, 1):
        cv.hair([(cx + s * rl * .28, cy + rl * .18), (cx + s * rl * .62, cy + rl * .18)])
        cv.hair([(cx + s * rl * .28, cy + rl * .34), (cx + s * rl * .5, cy + rl * .34)])
    # the P monogram, above the spindle
    m = rl * .4
    px, py = cx - m * .3, cy - rl * .74
    cv.heavy([(px, py), (px, py + m * 1.15)])
    cv.line([(px, py)] + [(px + m * .3 + m * .3 * math.cos(a), py + m * .3 + m * .3 * math.sin(a))
                          for a in [-math.pi / 2 + math.pi * i / 10 for i in range(11)]] + [(px, py + m * .6)])
    cv.hair([(px - m * .25, py + m * 1.15), (px + m * .25, py + m * 1.15)])
    return lab


def tonearm(cv, px, py, hx, hy, R):
    """Pivot base at (px, py) with counterweight, S-free straight arm to a headshell resting at (hx, hy)."""
    ang = math.atan2(hy - py, hx - px)
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    # counterweight behind the pivot
    cw = R * .16
    wx, wy = px - ux * cw * 1.4, py - uy * cw * 1.4
    wpoly = [(wx + ux * cw * .55 * sx + nx * cw * .62 * sy, wy + uy * cw * .55 * sx + ny * cw * .62 * sy)
             for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    cv.obj([wpoly], 1.)
    cv.hair(C.hatch_poly(wpoly, math.degrees(ang) + 90, 1.5))
    # the arm
    aw = max(1.6, R * .045)
    L = math.hypot(hx - px, hy - py)
    arm = [(px + nx * aw, py + ny * aw), (px + ux * L + nx * aw * .8, py + uy * L + ny * aw * .8),
           (px + ux * L - nx * aw * .8, py + uy * L - ny * aw * .8), (px - nx * aw, py - ny * aw)]
    cv.obj([arm], 1.)
    cv.hair([(px + nx * aw * .45, py + ny * aw * .45), (px + ux * L + nx * aw * .4, py + uy * L + ny * aw * .4)])
    # headshell: a small block turned 25 degrees off the arm, with a finger lift
    ha = ang + .45
    hu, hv = math.cos(ha), math.sin(ha)
    hl, hw = R * .2, R * .085
    shell = [(hx + hu * a - hv * b, hy + hv * a + hu * b) for a, b in ((-hl * .2, -hw), (hl, -hw * .7), (hl, hw * .7), (-hl * .2, hw))]
    cv.obj([shell], 1.)
    cv.hair(C.hatch_poly(shell, math.degrees(ha) + 90, 1.5))
    cv.line([(hx + hu * hl * .6 - hv * hw, hy + hv * hl * .6 + hu * hw),
             (hx + hu * hl * .6 - hv * hw * 2.4, hy + hv * hl * .6 + hu * hw * 2.4)])
    # pivot base: a turned boss
    br = R * .2
    base = _circ(px, py, br)
    cv.obj([base], 1.)
    cv.hair(_circ(px, py, br * .78))
    cv.hair(_seg_keep(C.hatch_poly(base, 0, 1.5), lambda x, y: math.hypot(x - px + br * .3, y - py + br * .3) > br * .8))
    top = _circ(px, py, br * .45)
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 90, 1.5))


def snare(cv, cx, top, rx, depth):
    """A snare drum seen a little from above: batter head, chrome hoops, wood shell shaded as a
    cylinder, tension lugs and the throw-off. Returns the head ellipse."""
    ry = rx * .26
    cyt, cyb = top, top + depth
    shell = [(cx + rx, cyt)] + _ell(cx, cyb, rx, ry, 48, 0, math.pi) + [(cx - rx, cyt)]
    cv.obj([shell], 1.)
    x = cx - rx + .8
    while x < cx + rx - .8:
        t = (x - cx) / rx
        e = math.sqrt(max(0, 1 - t * t))
        cv.hair([(x, cyt + ry * e + 3.5), (x, cyb + ry * e - 3.5)])
        # cylinder: dense at both turned edges, open where the light strikes (left of centre)
        x += 1.5 if (t > .3 or t < -.8) else 2
    # chrome hoops: a black band with a white bevel line
    for yy, s in ((cyt, 1), (cyb, -1)):
        arc = _ell(cx, yy, rx, ry, 48, 0, math.pi)
        band = arc + [(p[0], p[1] + s * 3.4) for p in arc][::-1]
        cv.obj([band], 1.)
        cv.line([(p[0], p[1] + s * 2.4) for p in _ell(cx, yy, rx, ry, 48, .08, math.pi - .08)])
        cv.hair(_seg_keep(C.hatch_poly(band, 90, 1.5), lambda x, y: x > cx + rx * .3 or x < cx - rx * .75))
    # lugs: turned tube lugs with tension rods
    for i in range(7):
        a = math.pi * (i + .5) / 7
        lx = cx + rx * math.cos(a)
        e = math.sin(a)
        yt = cyt + ry * e + 3.4
        yb = cyb + ry * e - 3.4
        lw = 2.4 * (.35 + .65 * e)
        mid = (yt + yb) / 2
        hh = depth * .17
        lug = _ell(lx, mid, lw, hh, 16)
        cv.line([(lx, yt), (lx, mid - hh)])
        cv.line([(lx, mid + hh), (lx, yb)])
        cv.obj([lug], 1.)
        cv.hair([(lx + lw * .45, mid - hh * .7), (lx + lw * .45, mid + hh * .7)])
    # throw-off on the front: small lever plate
    tx, ty = cx + rx * .08, cyt + ry + depth * .5 + ry * .0
    plate = [(tx - 3, ty - 4), (tx + 3, ty - 4), (tx + 3, ty + 4), (tx - 3, ty + 4)]
    cv.obj([plate], 1.)
    cv.hair(C.hatch_poly(plate, 0, 1.5))
    # batter head: coated, so lightly ruled all over, darker toward the back rim
    head = _ell(cx, cyt, rx, ry, 64)
    cv.obj([head], 1.)
    cv.hair(_ell(cx, cyt, rx - 3, ry - 1.1, 64))
    cv.hair(C.hatch_poly(_ell(cx, cyt, rx - 3.5, ry - 1.4, 64)[:-1], 0, 3, .5))
    cv.hair(_seg_keep(C.hatch_poly(_ell(cx, cyt, rx - 3.5, ry - 1.4, 64)[:-1], 0, 3, 2),
                      lambda x, y: y < cyt - ry * .25))
    return head


def floor(cv, fld, y0, cx):
    """The bandstand: boards running back to a vanishing point, ruled closer toward the back."""
    xs = [p[0] for p in fld]
    ys = [p[1] for p in fld]
    x0, x1, yb = min(xs) - 2, max(xs) + 2, max(ys) + 2
    poly = [(x0, y0), (x1, y0), (x1, yb), (x0, yb)]
    cv.obj([poly], 1.)
    vy = y0 - (yb - y0) * 2.2
    for i in range(-14, 15):
        bx = cx + i * 9
        cv.hair([(cx + (bx - cx) * .3, y0), (bx + (bx - cx) * 1.8, yb + 40)])
    y = y0 + 1.5
    g = 1.5
    while y < yb:
        cv.hair([(x0, y), (x1, y)])
        g = min(3, g * 1.12)
        y += g


# ----------------------------------------------------------------------------------------------
# the vignette: fills the whole cartouche field (no white)
# ----------------------------------------------------------------------------------------------

def _rays(cx, cy, r0, fld, n):
    """Spotlight glory behind the record: alternating long and short rays out to the field edge."""
    xs = [p[0] for p in fld]
    ys = [p[1] for p in fld]
    far = max(max(xs) - cx, cx - min(xs), max(ys) - cy, cy - min(ys)) * 1.5
    out = []
    for i in range(n):
        a = TAU * i / n
        r1 = far if i % 2 == 0 else r0 + 6 + (i % 4 == 1) * 8
        out.append([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))])
    return out


def vignette(fld, kind, seed):
    """fld: the field polygon (we fill all of it); kind: 'band', 'medium' or 'tall'."""
    xs = [p[0] for p in fld]
    ys = [p[1] for p in fld]
    fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
    fw, fh = fx1 - fx0, fy1 - fy0
    back = C.Canvas()
    back.obj([], 0)
    front = C.Canvas()
    front.obj([], 0)
    if kind == "tall":
        R = min(fw * .3, fh * .27)
        cx, cy = (fx0 + fx1) / 2, fy0 + fh * .33
    elif kind == "band":
        R = min(fw, fh) * .42
        cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
    else:
        R = min(fh * .40, fw * .3)
        cx, cy = (fx0 + fx1) / 2 - R * .12, (fy0 + fy1) / 2
    back.hair(_rays(cx, cy, R + 1.5, fld, 144 if kind != "band" else 72))
    if kind in ("medium", "band"):
        # Parker's sticks crossed behind the record, tips out to the upper corners
        for s in (-1, 1):
            a = math.radians(-27) if s > 0 else math.radians(180 + 27)
            reach = (fw / 2 - 15) / math.cos(math.radians(27))
            tx, ty = cx + R * .12 + reach * math.cos(a), cy + reach * math.sin(a)
            bx, by = cx + R * .12 - reach * math.cos(a), cy - reach * math.sin(a)
            drumstick(back, bx, by + 3, tx, ty + 3, max(5., R * .17))
    rec = record_svg(cx, cy, R, seed)
    record_label(front, cx, cy, R)
    if kind == "tall":
        sy = cy + R * .9
        srx = R * 1.18
        floor(front, fld, sy + R * .62, cx)
        snare(front, cx, sy, srx, R * .5)
        # sticks resting crossed on the batter head
        for s in (-1, 1):
            bx, by = cx - s * srx * .95, sy + srx * .26 * .55
            tx, ty = cx + s * srx * .62, sy - srx * .26 * .75
            ang = math.atan2(ty - by, tx - bx)
            drumstick(front, bx - math.cos(ang) * 6, by - math.sin(ang) * 6, tx, ty, max(5., R * .13))
    if kind != "band":
        tonearm(front, cx + R * 1.1, cy - R * .8, cx + R * .56, cy + R * .2, R)
    cid = C._uid("music", fx0, fy0, fw, fh, kind)
    return (f'<clipPath id="{cid}"><path d="{C._d(fld, True, 0)}"/></clipPath><g clip-path="url(#{cid})">'
            + back.svg() + rec + front.svg() + '</g>')


# ----------------------------------------------------------------------------------------------
# lettering-free inscriptions for the tall plate: a bar of swing on the ribbon, a keyboard on the tablet
# ----------------------------------------------------------------------------------------------

def upright_bass(cv, x, base, H, rng):
    """The upright bass leaning on its rib: a waisted body in contour lines, f-holes, bridge,
    tailpiece, the long neck and the scroll at the head."""
    W = H * .36
    ks = ((0, .62), (.08, .92), (.26, 1.), (.46, .8), (.56, .66), (.66, .74), (.8, .76), (.92, .5), (1., .16))

    def hw(t):
        for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                return W * .5 * (v0 + (v1 - v0) * u * u * (3 - 2 * u))
        return W * .5 * ks[-1][1]
    n = 30
    bh = H * .58
    lean = .1
    P_ = lambda u, v: (x + u + (base - v) * lean, v)
    right = [P_(hw(i / n), base - bh * i / n) for i in range(n + 1)]
    left = [P_(-hw(i / n), base - bh * i / n) for i in range(n + 1)]
    body = right + left[::-1]
    cv.obj([body], 1.)
    for k in range(1, 7):
        f = 1 - k * .12
        cv.hair([P_(hw(i / n) * f + W * .02 * k, base - bh * i / n) for i in range(2, n - 2)])
    sh = [P_(hw(i / n) * .3, base - bh * i / n) for i in range(n + 1)] + right[::-1]
    cv.hair(C.hatch_poly(sh, 75, 1.5, rng.random()))
    cv.hair(C.hatch_poly([P_(hw(i / n) * .62, base - bh * i / n) for i in range(n + 1)] + right[::-1], -30, 2, rng.random()))
    cv.hair(C.hatch_poly(left[::-1][:n // 2] + [P_(-hw(i / n) * .7, base - bh * i / n) for i in range(n // 2, n + 1)][::-1], 70, 3, rng.random()))
    for sd in (-1, 1):
        fx = x + sd * W * .16
        f = [P_(sd * W * .16 + sd * .8 * math.sin(t * 5), base - bh * (.32 + .22 * t)) for t in [j / 10 for j in range(11)]]
        cv.line(f)
    cv.line([P_(-W * .2, base - bh * .3), P_(W * .2, base - bh * .3)])
    cv.obj([[P_(-W * .06, base - bh * .05), P_(W * .06, base - bh * .05), P_(W * .045, base - bh * .25), P_(-W * .045, base - bh * .25)]], 1.)
    cv.hair(C.hatch_poly([P_(-W * .06, base - bh * .05), P_(W * .06, base - bh * .05), P_(W * .045, base - bh * .25), P_(-W * .045, base - bh * .25)], 90, 1.5))
    nk = [P_(-W * .05, base - bh), P_(W * .05, base - bh), P_(W * .04, base - H * .95), P_(-W * .04, base - H * .95)]
    cv.obj([nk], 1.)
    cv.line(C.hatch_poly(nk, 90, 1.5))
    fb = [P_(-W * .035, base - bh * .62), P_(W * .035, base - bh * .62), P_(W * .03, base - bh), P_(-W * .03, base - bh)]
    cv.obj([fb], 1.)
    cv.line(C.hatch_poly(fb, 90, 1.5))
    sc = P_(0, base - H * .97)
    cv.obj([C._ell_pts(sc[0], sc[1], W * .07, W * .09, 14)[:-1]], 1.)
    cv.line(C._ell_pts(sc[0] + 1, sc[1], W * .035, W * .045, 10))
    for k in range(4):
        cv.hair([P_(-W * .015 * (k - 1.5), base - bh * .3), P_(-W * .01 * (k - 1.5), base - H * .93)])
    cv.line([P_(0, base), P_(0, base + H * .04)])


def ride_cymbal(cv, cx, cy, r, stand_to, rng):
    """A ride on its stand, tipped toward us: lathe rings, the bell, a lit crescent."""
    cv.obj([], 0)
    cv.line([(cx, cy), (cx, stand_to)])
    cv.hair([[(cx, stand_to), (cx + sd * r * .45, stand_to + r * .1)] for sd in (-1, 1)])
    e = C._ell_pts(cx, cy, r, r * .28, 48)[:-1]
    cv.obj([e], 1.)
    k = .9
    while k > .2:
        cv.hair(C._ell_pts(cx, cy, r * k, r * .28 * k, 40))
        k -= .09
    cv.hair(C.hatch_poly([q for q in e if q[0] > cx + r * .2] + [(cx + r * .2, cy)], 80, 1.5, rng.random()))
    cv.obj([C._ell_pts(cx, cy - r * .03, r * .17, r * .08, 16)[:-1]], 1.)


def trumpet(cv, x, y, L, rng):
    """A trumpet lying on its side: bell, valves, the wrapped leadpipe and mouthpiece."""
    br = L * .14
    bell = [(x + L, y - br), (x + L * .82, y - br * .25), (x + L * .35, y - br * .15), (x + L * .35, y + br * .15),
            (x + L * .82, y + br * .25), (x + L, y + br)]
    cv.obj([bell], 1.)
    cv.hair(C.hatch_poly([(x + L * .35, y + .2), (x + L * .82, y + br * .25), (x + L, y + br), (x + L, y + .2)], 0, 1.5))
    cv.line(C._ell_pts(x + L, y, br * .3, br, 18))
    loop = [(x + L * .35, y - br * .15), (x + L * .1, y - br * .15), (x + L * .02, y + br * .6), (x + L * .1, y + br * 1.3),
            (x + L * .6, y + br * 1.3), (x + L * .6, y + br * 1.0), (x + L * .12, y + br * 1.0), (x + L * .08, y + br * .6),
            (x + L * .12, y + br * .15), (x + L * .35, y + br * .15)]
    cv.obj([loop], 1.)
    for k in range(3):
        vx = x + L * (.4 + .07 * k)
        v = [(vx - L * .022, y - br * .9), (vx + L * .022, y - br * .9), (vx + L * .022, y + br * 1.5), (vx - L * .022, y + br * 1.5)]
        cv.obj([v], 1.)
        cv.hair(C.hatch_poly(v, 90, 1.5))
        cv.obj([C._ell_pts(vx, y - br * 1.05, L * .03, L * .012, 10)[:-1]], 1.)
    cv.obj([[(x - L * .12, y - br * .1), (x + L * .1, y - br * .06), (x + L * .1, y + br * .06), (x - L * .12, y + br * .1)]], 1.)


def trio(fld, kind, seed):
    """Music and shows front: the jazz trio's bandstand between sets, lit by one spot on a dark
    stage. The upright bass leans at the left, the kit (snare and the ride) sits behind, the
    trumpet rests on a stool at the right. Parker's own sticks lie across the snare."""
    if kind in ("band", "device"):
        return vignette(fld, "band", seed)
    xs = [p[0] for p in fld]
    ys = [p[1] for p in fld]
    fx0, fx1, fy0, fy1 = min(xs), max(xs), min(ys), max(ys)
    fw, fh = fx1 - fx0, fy1 - fy0
    cx = (fx0 + fx1) / 2
    rng = random.Random(seed)
    o = []
    floor_y = fy0 + fh * .8
    cv = C.Canvas()
    # the curtain: folds cut in close vertical lines, each fold rounded by a second set that
    # crowds into its trough, darkest at the wings and opening toward the spot
    cv.obj([[(fx0 - 2, fy0 - 2), (fx1 + 2, fy0 - 2), (fx1 + 2, floor_y + 1), (fx0 - 2, floor_y + 1)]], 0)
    fold = max(7., fw / 40)
    curtain, trough = [], []
    xx = fx0 - 2
    while xx < fx1 + 2:
        u = (xx - fx0) / fw
        wing = abs(u - .5) * 2
        ph = ((xx - fx0) % fold) / fold
        sway = 1.2 * math.sin(xx * .05)
        curtain.append([(xx + sway * (yy - fy0) / fh, yy) for yy in (fy0 - 2, (fy0 + floor_y) / 2, floor_y + 1)])
        if ph > .55 or wing > .7:
            trough.append([(xx + .75 + sway * (yy - fy0) / fh, yy) for yy in (fy0 - 2, floor_y + 1)])
        xx += 1.5 if (ph > .45 or wing > .55) else 3.
    cv.hair(curtain)
    cv.hair(trough)
    # the valance: a scalloped pelmet along the top, swags shaded underneath
    sw_ = fw / 9
    for k in range(10):
        bx = fx0 + k * sw_ - sw_ / 2
        sg = [(bx + sw_ * t, fy0 + fh * .02 + fh * .07 * math.sin(math.pi * t)) for t in [j / 12 for j in range(13)]]
        cv.obj([[(bx, fy0 - 2)] + sg + [(bx + sw_, fy0 - 2)]], 1.)
        cv.hair(C.hatch_poly([(bx, fy0 - 2)] + sg + [(bx + sw_, fy0 - 2)], 0, 1.5))
        cv.line([(q[0], q[1] - 1.2) for q in sg[2:-2]])
    # the spot: a white pool on the boards and a cone of light
    sx = cx + fw * .02
    cone = [(sx - fw * .04, fy0 - 2), (sx + fw * .04, fy0 - 2), (sx + fw * .36, floor_y + fh * .08), (sx - fw * .36, floor_y + fh * .08)]
    cv.obj([cone], 0)
    cv.hair(C.hatch_poly(cone, 90, 3, .5))
    stage = [(fx0 - 2, floor_y), (fx1 + 2, floor_y), (fx1 + 2, fy1 + 2), (fx0 - 2, fy1 + 2)]
    cv.obj([stage], .5)
    yy, g = floor_y + 1.5, 1.5
    while yy < fy1 + 2:
        cv.hair([(fx0 - 2, yy), (fx1 + 2, yy)])
        g = min(3., g * 1.18)
        yy += g
    for k in range(-12, 13):
        cv.hair([(cx + k * fw * .02, floor_y), (cx + k * fw * .07, fy1 + 2)])
    pool = C._ell_pts(sx, floor_y + (fy1 - floor_y) * .4, fw * .34, (fy1 - floor_y) * .45, 40)[:-1]
    cv.obj([pool], 0)
    cv.hair(C.hatch_poly(pool, 0, 3, .3))
    H = fh * .98
    S = min(H, fw * .9)
    ride_cymbal(cv, cx + S * .05, floor_y - S * .52, S * .2, floor_y + 2, rng)
    upright_bass(cv, cx - S * .38, floor_y + S * .02, S * .78, rng)
    stx = cx + S * .42
    cv.obj([[(stx - S * .12, floor_y - S * .2), (stx + S * .12, floor_y - S * .2), (stx + S * .12, floor_y - S * .17), (stx - S * .12, floor_y - S * .17)]], 1.)
    for sd in (-1, 1):
        cv.line([(stx + sd * S * .1, floor_y - S * .17), (stx + sd * S * .13, floor_y + S * .03)])
    trumpet(cv, stx - S * .16, floor_y - S * .25, S * .36, rng)
    snare(cv, cx + S * .08, floor_y - S * .14, S * .16, S * .1)
    for sd in (-1, 1):
        drumstick(cv, cx + S * .08 - sd * S * .15, floor_y - S * .1, cx + S * .08 + sd * S * .1, floor_y - S * .2, max(3., S * .02))
    o.append(cv.svg())
    return "".join(o)


def swing_on_ribbon(centre, h):
    """A five-line percussion staff along the ribbon face carrying the ride-cymbal swing pattern
    (x heads: ding, ding-a ding, ding-a) with a percussion clef, common time and bar lines."""
    n = len(centre) - 1

    def at(u, s):                       # u 0..1 along, s -1..1 across (+ = down)
        f = u * n
        i = min(int(f), n - 1)
        t = f - i
        x0, y0 = centre[i]
        x1, y1 = centre[i + 1]
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        return (x + nx * s * h / 2, y + ny * s * h / 2)
    o_h, o_l, o_f = [], [], []
    u0, u1 = .05, .95
    sp = .2                             # staff line spacing in s units (5 lines: -.4 .. .4)
    for k in range(5):
        s = -.4 + k * sp
        o_h.append(C._d([at(u0 + (u1 - u0) * i / 60, s) for i in range(61)], tol=.1))
    # percussion clef: two short heavy bars
    for du in (.012, .022):
        o_f.append(C._d([at(u0 + du, -.2), at(u0 + du, .2)], tol=0))
    # bar lines (double at the end)
    seg = (u1 - u0 - .05) / 2
    bars = [u0 + .05 + seg, u1 - .006, u1]
    for b in bars:
        o_l.append(C._d([at(b, -.4), at(b, .4)], tol=0))
    # notes: per bar beats 1, 2 (+ swung a), 3, 4 (+ a): x heads on the top space, stems up
    for bi in range(2):
        b0 = u0 + .05 + bi * seg
        beat = seg / 4.25
        hits = [(0, 0), (1, 0), (1 + 2 / 3, 1), (2, 0), (3, 0), (3 + 2 / 3, 1)]
        for k, (bt, sub) in enumerate(hits):
            u = b0 + beat * (bt + .45)
            px, py = at(u, -.5)
            r = h * .09
            o_l.append(C._d([(px - r, py - r), (px + r, py + r)], tol=0) + C._d([(px - r, py + r), (px + r, py - r)], tol=0))
            o_h.append(C._d([(px + r, py), at(u + .0005, -1.25)], tol=0))
        # beams joining the swung pairs, with a tiny triplet bracket
        for b_ in (1, 3):
            ua, ub = b0 + beat * (b_ + .45), b0 + beat * (b_ + 2 / 3 + .45)
            o_f.append(C._d([at(ua, -1.2), at(ub, -1.2)], tol=0))
        # snare backbeat (2 and 4) on the third space, filled heads; kick on 1 and 3 low
        for bt, s in ((1, .1), (3, .1), (0, .5), (2, .5)):
            u = b0 + beat * (bt + .45)
            px, py = at(u - .004, s)
            o_f.append(C._d(_ell(px, py, h * .085, h * .065, 10), True, 0))
    return (f'<path d="{"".join(o_h)}" stroke="#000" stroke-width=".5" fill="none"/>'
            f'<path d="{"".join(o_l)}" stroke="#000" stroke-width="1" fill="none"/>'
            f'<path d="{"".join(o_f)}" stroke="#000" stroke-width="1.5" fill="#000"/>')


def keyboard(tx, ty, tw, th):
    """A piano keyboard set into the pedestal tablet: ruled white keys, black keys shaded with a
    highlight edge, a felt rail above."""
    pad = 2.
    x0, y0, w, h = tx + pad, ty + pad, tw - 2 * pad, th - 2 * pad
    rail = max(2., h * .16)
    n = max(14, int(round(w / 6.2)))
    kw = w / n
    o = [f'<path d="M{_n(x0)},{_n(y0)}h{_n(w)}v{_n(rail)}h{_n(-w)}z" fill="{C.pat("X")}" stroke="#000" stroke-width=".5"/>']
    ky = y0 + rail
    kh = h - rail
    lines = "".join(f"M{_n(x0 + kw * i)},{_n(ky)}v{_n(kh)}" for i in range(1, n))
    o.append(f'<path d="{lines}" stroke="#000" stroke-width=".5"/>')
    # a shadow rule along the key fronts and light ruling in the lower third of the keys
    o.append(f'<path d="M{_n(x0)},{_n(ky + kh - 1.5)}h{_n(w)}M{_n(x0)},{_n(ky + kh * .62)}h{_n(w)}" stroke="#000" stroke-width=".5"/>')
    blk = []
    for i in range(n - 1):
        if i % 7 in (0, 1, 3, 4, 5):
            bx = x0 + kw * (i + 1) - kw * .3
            blk.append(f"M{_n(bx)},{_n(ky)}h{_n(kw * .6)}v{_n(kh * .58)}h{_n(-kw * .6)}z")
    o.append(f'<path d="{"".join(blk)}" fill="#000" stroke="none"/>')
    o.append(f'<path d="M{_n(x0)},{_n(y0)}h{_n(w)}v{_n(h)}h{_n(-w)}z" stroke="#000" stroke-width="1" fill="none"/>')
    return "".join(o)


def _tall_overlays(w, h):
    top_free = min(h * .055, 26.)
    py0 = top_free
    pw = w - 12
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    ph = h - top_free - ped_h - frieze + ped_h * .3
    cw, ch = pw * .44, ph * .58
    cx, cy = w / 2, py0 + ph * .45
    bw_, bh_ = cw * 1.4, min(16, ph * .05)
    face_w = bw_ * .7
    n = 40
    bcy = cy + ch * .47
    centre = [(cx - face_w / 2 + face_w * i / n, bcy - .04 * bw_ * math.sin(math.pi * i / n)) for i in range(n + 1)]
    o = [swing_on_ribbon(centre, bh_)]
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    # the pedestal's tablet (same arithmetic as engraving_codex.pedestal)
    kb = max(5, min(10, ped_h * .11))
    inset = w * .035
    slab = ped_h * .42
    fy = py + kb + slab * .22
    fh = slab - slab * .22
    th, tw = fh * .6, w * .56
    tx, ty = (w - tw) / 2, fy + (fh - th) / 2
    o.append(keyboard(tx + 1.5, ty + 1.5, tw - 1.5, th - 1.5))
    return "".join(o)


def trumpet_bell(cv, xm, yc, rm, L, side, seed):
    """A brass bell lying along the frieze, its mouth at xm facing outward (side -1: mouth at the left
    end), flaring from a slim lead pipe; acanthus fronds sprout from the rim and curl back over it."""
    rt = max(2.2, rm * .085)
    rng = random.Random(seed)

    def rad(d):
        return rt + (rm - rt) * math.exp(-d / (L * .16))
    n = 60
    ds = [L * (i / n) ** 1.6 for i in range(n + 1)]
    X = lambda d: xm - side * d
    top = [(X(d), yc - rad(d)) for d in ds]
    bot = [(X(d), yc + rad(d)) for d in ds]
    body = top + bot[::-1]
    cv.obj([body], 1.)
    # bulino along the flare: dense on the shadow (lower) side, a bright band high on the bell
    for f in (-.92, -.8, -.3, .05, .3, .48, .62, .74, .84, .92):
        pl = [(X(d), yc + f * rad(d)) for d in ds[1:-1]]
        (cv.line if f in (.84,) else cv.hair)(pl)
    for d in [L * .05 * k for k in range(1, 4)]:     # flare rings near the mouth
        cv.hair([(X(d) + side * .0, yc - rad(d) * .97), (X(d), yc + rad(d) * .97)])
    # garland ferrule where the bell meets the pipe
    dg = L * .58
    for k, dd in enumerate((dg - 2.5, dg, dg + 2.5)):
        (cv.heavy if k == 1 else cv.line)([(X(dd), yc - rad(dd) - 1), (X(dd), yc + rad(dd) + 1)])
    # the mouth: a turned-over rim, its throat in deep cross-hatch
    rx = rm * .2
    mouth = _ell(xm, yc, rx, rm, 40)
    cv.obj([mouth], 1.5)
    inner = _ell(xm, yc, rx * .7, rm * .86, 40)[:-1]
    cv.hair(_ell(xm, yc, rx * .85, rm * .93, 40))
    cv.hair(C.hatch_poly(inner, 0, 1.5))
    cv.hair(C.hatch_poly(inner, 60 * side, 2))
    # acanthus sprouting from the rim, lying back along the bell and curling over it
    for sy in (-1, 1):
        heading = 18 * sy if side < 0 else 180 - 18 * sy
        C.acanthus_frond(xm - side * rx * .2, yc + sy * rm * .9, heading, rm * 1.25,
                         n=3, spread=22, bend=.5 * side * sy, curl=3.8 * side * sy,
                         seed=rng.randrange(1 << 20), cv=cv)


def _medium(w, h, seed, fill_fn):
    """The house medium layout (engraving_codex._layout_medium) with a trumpet bell at each end, its
    rim sprouting acanthus, and the record cartouche at the centre."""
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .4, gh * 1.45)
    cx, cy = w / 2, (gy0 + gy1) / 2
    occ = [("r", cx - cw / 2 + 4, gy0, cx + cw / 2 - 4, gy1)]
    r = min(gh * .46, (w - cw) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    bells = C.Canvas()
    rm = min(gh * .36, 46)
    blen = max(70., (w - cw) / 2 - r * 1.2)
    for side in (-1, 1):
        vx = cx + side * (cw / 2 + r)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
        xm = rm * .2 + 3 if side < 0 else w - rm * .2 - 3
        trumpet_bell(bells, xm, vy, rm, blen, side, seed + side)
        occ.append(("r", 0, gy0, rm * 1.5, gy1) if side < 0 else ("r", w - rm * 1.5, gy0, w, gy1))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(bells)
    cv.extend(main)
    o.append(C._clip(C._uid("mm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    c, (ix, iy, iw, ih), _ = C.cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20))
    o.append(c)
    o.append(fill_fn(ix, iy, iw, ih))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def proscenium(cx, cy, rx, ry):
    """The vignette's silhouette is the bandstand itself: the valance's swags along the top,
    the curtain falling to either side, the stage apron's curve along the foot."""
    pts = []
    n = 9
    for k in range(n):
        x0 = cx - rx * .86 + 2 * rx * .86 * k / n
        for j in range(8):
            t = j / 8
            pts.append((x0 + 2 * rx * .86 / n * t, cy - ry + ry * .07 * math.sin(math.pi * t) ** .7))
    pts.append((cx + rx * .86, cy - ry))
    for j in range(1, 13):
        t = j / 12
        pts.append((cx + rx * (.86 + .14 * math.sin(math.pi / 2 * t)), cy - ry + ry * 1.45 * t))
    for j in range(25):
        a = j / 24 * math.pi
        pts.append((cx + rx * math.cos(a), cy + ry * .45 + ry * .55 * math.sin(a)))
    for j in range(1, 13):
        t = 1 - j / 12
        pts.append((cx - rx * (.86 + .14 * math.sin(math.pi / 2 * t)), cy - ry + ry * 1.45 * t))
    return pts


def tape_frame(cx, cy, rx, ry, fld, mode, seed):
    """The frame is the music's own: two tape reels at the lower corners, the tape running off
    one, over the top of the vignette along its rim, and onto the other."""
    cv = C.Canvas()
    rr = min(ry * .36, 30.)
    if rr < 9:
        return ""
    reels = [(cx - rx + rr * .9, cy + ry - rr * .95), (cx + rx - rr * .9, cy + ry - rr * .95)]
    tape = [(reels[0][0], reels[0][1] + rr * .78)] + [(reels[0][0] + (reels[1][0] - reels[0][0]) * t,
             reels[0][1] + rr * .78 + 2.5 * math.sin(math.pi * t)) for t in [j / 30 for j in range(1, 30)]] + [(reels[1][0], reels[1][1] + rr * .55)]
    L, R = [], []
    for i, q in enumerate(tape):
        a, b = tape[max(0, i - 1)], tape[min(len(tape) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        L.append((q[0] - ty / tl * 1.6, q[1] + tx / tl * 1.6))
        R.append((q[0] + ty / tl * 1.6, q[1] - tx / tl * 1.6))
    cv.obj([L + R[::-1]], 1.)
    cv.hair([((l[0] + r[0]) / 2, (l[1] + r[1]) / 2) for l, r in zip(L, R)][1:-1])
    rng = random.Random(seed)
    for k, (x, y) in enumerate(reels):
        cv.obj([_circ(x, y, rr)[:-1]], 1.)
        pack = rr * (.78 if k == 0 else .55)
        r = pack
        while r > rr * .3:
            cv.hair(_circ(x, y, r))
            r -= 1.5
        cv.hair(C.hatch_poly(_circ(x + rr * .2, y + rr * .2, pack * .9)[:-1], 45, 1.5, rng.random()))
        for j in range(3):
            a0 = j * TAU / 3 + k
            win = [(x + rr * .38 * math.cos(a0 + t), y + rr * .38 * math.sin(a0 + t)) for t in [-.5 + i / 8 for i in range(9)]]
            win += [(x + rr * .9 * math.cos(a0 + t), y + rr * .9 * math.sin(a0 + t)) for t in [.5 - i / 8 for i in range(9)]]
            cv.obj([win], 1.)
            cv.hair(C.hatch_poly(win, 30, 3, .5))
        cv.obj([_circ(x, y, rr * .22)[:-1]], 1.)
        cv.line(_circ(x, y, rr * .1))
        for j in range(6):
            a0 = j * TAU / 6
            cv.line([(x + rr * .1 * math.cos(a0), y + rr * .1 * math.sin(a0)), (x + rr * .2 * math.cos(a0), y + rr * .2 * math.sin(a0))])
    return cv.svg()


# ==== STUDIO FRAME (batch 2) ====================================================================
# King-tier frame, copied into this plate so it can be cut to the page (house rule: the shared
# modules stay untouched). Fine English scroll as on the GRS vise and Ken Hunt's panels: dozens of
# small logarithmic spirals grown from one stem, each branching into the next and carrying its own
# shaded leaves, packed over a punched matte ground; white "gold-line" wire borders and beading
# frame every panel; the subject sits in an inlaid medallion ringed with beads.
import math as _m
import random as _rnd
import engraving_codex as _C

_PI = _m.pi
_TAU = 2 * _m.pi
_sm = _C._smooth


def _st_mat_tile():
    """An 8 px matte tile: black punched with 1 px white dots set evenly (blue noise)."""
    rng = _rnd.Random(91)
    pts = []
    tries = 0
    while len(pts) < 13 and tries < 4000:
        tries += 1
        p = (rng.randrange(16) * .5, rng.randrange(16) * .5)
        ok = True
        for q in pts:
            dx = min(abs(p[0] - q[0]), 8 - abs(p[0] - q[0]))
            dy = min(abs(p[1] - q[1]), 8 - abs(p[1] - q[1]))
            if dx * dx + dy * dy < 3.6:
                ok = False
                break
        if ok:
            pts.append(p)
    return "".join(f"M{_C._n(x)},{_C._n(y)}h1v1h-1z" for x, y in pts)


_ST_DEFS = ('<defs><pattern id="s2m" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<path d="M0,0h8v8h-8z" fill="#000"/><path d="{_st_mat_tile()}" fill="#fff"/></pattern>'
            '<pattern id="s2o" width="2" height="2" patternUnits="userSpaceOnUse"><path d="M0,0h.5v.5h-.5zM1,1h.5v.5h-.5z" fill="#000"/></pattern></defs>')


def st_matte(d):
    """The punched matte ground over path data d."""
    return f'<path d="{d}" fill="url(#s2m)" stroke="none"/>'


def st_rect_d(x, y, w, h):
    return f"M{_C._n(x)},{_C._n(y)}h{_C._n(w)}v{_C._n(h)}h{_C._n(-w)}z"


# ---------------------------------------------------------------------------------------------
# the fine scroll: spirals, leaves, growth from one stem
# ---------------------------------------------------------------------------------------------

def _spiral(px, py, head, R, s, turns):
    """A log spiral leaving (px, py) heading `head`, first radius R, turning toward side s
    (+1 = the +normal side), winding `turns` into an eye at .13 R. -> (pts, centre, radii)."""
    th = _TAU * turns
    b = _m.log(1 / .13) / th
    a0 = _m.atan2(s * R, -b * R)
    rot = head - a0
    cr, sr = _m.cos(rot), _m.sin(rot)
    pts, rad = [], []
    t = 0.
    while True:
        r = R * _m.exp(-b * t)
        lx, ly = r * _m.cos(t) - R, s * r * _m.sin(t)
        pts.append((px + lx * cr - ly * sr, py + lx * sr + ly * cr))
        rad.append(r)
        if t >= th:
            break
        t = min(th, t + max(.05, 1.4 / r))
    return pts, (px - R * cr, py - R * sr), rad


def _tangent(pts, i):
    a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
    return _m.atan2(b[1] - a[1], b[0] - a[0])


class _Grid:
    def __init__(self, cell=24.):
        self.c = cell
        self.g = {}
        self.maxr = 0.

    def add(self, x, y, r, oid):
        self.g.setdefault((int(x // self.c), int(y // self.c)), []).append((x, y, r, oid))
        self.maxr = max(self.maxr, r)

    def clear(self, x, y, r, slack, ignore):
        reach = r + self.maxr
        c = self.c
        for i in range(int((x - reach) // c), int((x + reach) // c) + 1):
            for j in range(int((y - reach) // c), int((y + reach) // c) + 1):
                for qx, qy, qr, oid in self.g.get((i, j), ()):
                    if oid != ignore and (qx - x) ** 2 + (qy - y) ** 2 < ((r + qr) * slack) ** 2:
                        return False
        return True


def st_sweep(x, y, ang, L, k0, k1=None, n=None):
    """A sweeping stem: from (x, y) heading ang (radians), L long, curvature k0 -> k1 (1/px)."""
    k1 = k0 if k1 is None else k1
    return _C._euler(x, y, ang, L, lambda u: k0 + (k1 - k0) * u, n or max(8, int(L / 2)))


class ScrollField:
    """Grows fine scroll over a region. inside(x, y) says where scroll may grow. Scrolls branch
    from stems and from one another, each sized to the room it finds, until the field is packed."""

    def __init__(self, inside, rmin=7., rmax=30., seed=0, slack=.88):
        self.inside = inside
        self.rmin, self.rmax = rmin, rmax
        self.rng = _rnd.Random(seed)
        self.grid = _Grid(20.)
        self.slack = slack
        self.items = []
        self.queue = []

    def _ok(self, c, R, parent):
        if not self.inside(c[0], c[1]):
            return False
        if parent is not None and self.items[parent][1] == "scroll":
            pc, pR = self.items[parent][2][1], self.items[parent][2][4]
            if (pc[0] - c[0]) ** 2 + (pc[1] - c[1]) ** 2 < ((pR + R) * .78) ** 2:
                return False
        for k in range(8):
            a = k * _TAU / 8
            if not self.inside(c[0] + R * .55 * _m.cos(a), c[1] + R * .55 * _m.sin(a)):
                return False
        return self.grid.clear(c[0], c[1], R, self.slack, parent)

    def stem(self, pts, w0=2.2, w1=1.2, leaves=True, gen=0):
        """A sweeping lead, the source the scrolls grow from (points run from the root out)."""
        oid = len(self.items)
        for p in pts[::2]:
            self.grid.add(p[0], p[1], 2.5, oid)
        self.items.append((gen, "stem", (pts, w0, w1, leaves)))
        self.queue.append((gen, oid, "stem", pts, 0, None))
        return oid

    def scroll(self, px, py, head, R, s, gen=0, parent=None, turns=None, force=False):
        turns = turns or self.rng.uniform(1.25, 1.55)
        pts, c, rad = _spiral(px, py, head, R, s, turns)
        if not force and not self._ok(c, R, parent):
            return False
        oid = len(self.items)
        self.grid.add(c[0], c[1], R, oid)
        self.items.append((gen, "scroll", (pts, c, rad, s, R)))
        self.queue.append((gen, oid, "scroll", pts, s, (c, R)))
        return True

    def grow(self, max_items=300):
        rng = self.rng
        qi = 0
        while qi < len(self.queue) and len(self.items) < max_items:
            gen, oid, kind, pts, s, info = self.queue[qi]
            qi += 1
            n = len(pts)
            cand = []
            if kind == "scroll":
                c, R = info
                for f in (.03, .14, .27, .4, .52):
                    i = int(f * (n - 1))
                    q = pts[i]
                    tau = _tangent(pts, i)
                    rh = _m.hypot(q[0] - c[0], q[1] - c[1])
                    cand.append((q, tau, -s, self.rmax))
                    cand.append((q, tau + _PI, s, self.rmax * .8))
            else:
                for i in range(3, n - 2, 4):
                    q = pts[i]
                    tau = _tangent(pts, i)
                    for sd in (1, -1):
                        cand.append((q, tau + sd * .15, -sd, self.rmax))
                        cand.append((q, tau + _PI - sd * .2, sd, self.rmax * .7))
                rng.shuffle(cand)
            for q, head, cs, top in cand:
                Rc = min(self.rmax, top)
                while Rc >= self.rmin:
                    if self.scroll(q[0], q[1], head + cs * rng.uniform(-.05, .2), Rc, cs, gen + 1, oid):
                        break
                    Rc *= .82
        return self

    def _branch_to(self, oid, cx, cy, R):
        """A scroll centred at (cx, cy) whose stem leads in from the nearest coil of item oid,
        joining it tangentially, so every scroll grows out of another."""
        it = self.items[oid]
        pts = it[2][0]
        if it[1] == "scroll":
            pc, pR, rad = it[2][1], it[2][4], it[2][2]
            idx = [i for i in range(0, len(pts), 2) if rad[i] > pR * .45 and
                   (pts[i][0] - pc[0]) * (cx - pts[i][0]) + (pts[i][1] - pc[1]) * (cy - pts[i][1]) > 0] or list(range(0, len(pts) // 3))
        else:
            idx = list(range(0, len(pts), 2))
        bi = min(idx, key=lambda i: (pts[i][0] - cx) ** 2 + (pts[i][1] - cy) ** 2)
        q = pts[bi]
        tau = _tangent(pts, bi)
        ua = _m.atan2(q[1] - cy, q[0] - cx)
        S = (cx + R * _m.cos(ua), cy + R * _m.sin(ua))
        hx, hy = _m.cos(tau), _m.sin(tau)
        if hx * (S[0] - q[0]) + hy * (S[1] - q[1]) < 0:
            hx, hy = -hx, -hy
        turns = self.rng.uniform(1.25, 1.55)
        th = _TAU * turns
        bb = _m.log(1 / .13) / th
        best = None
        for sg in (1, -1):
            tx = -bb * _m.cos(ua) - sg * _m.sin(ua)
            ty = -bb * _m.sin(ua) + sg * _m.cos(ua)
            dot = tx * hx + ty * hy
            if best is None or dot > best[0]:
                best = (dot, sg, tx, ty)
        _, sg, tx, ty = best
        tl = _m.hypot(tx, ty)
        tx, ty = tx / tl, ty / tl
        L = _m.hypot(S[0] - q[0], S[1] - q[1])
        lead = []
        if L > 1.5:
            k = L * .45 + 2
            p1 = (q[0] + hx * k, q[1] + hy * k)
            p2 = (S[0] - tx * k, S[1] - ty * k)
            m = max(3, int(L / 1.5))
            for i in range(m):
                t = i / m
                a, b_, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                lead.append((a * q[0] + b_ * p1[0] + c * p2[0] + d * S[0], a * q[1] + b_ * p1[1] + c * p2[1] + d * S[1]))
        sp, rad = [], []
        t = 0.
        while True:
            r = R * _m.exp(-bb * t)
            ph = ua + sg * t
            sp.append((cx + r * _m.cos(ph), cy + r * _m.sin(ph)))
            rad.append(r)
            if t >= th:
                break
            t = min(th, t + max(.05, 1.4 / r))
        allp = lead + sp
        allr = [R] * len(lead) + rad
        noid = len(self.items)
        self.grid.add(cx, cy, R, noid)
        self.items.append((it[0] + 1, "scroll", (allp, (cx, cy), allr, sg, R)))
        return True

    def fill(self, x, y, w, h, step=5., max_items=320):
        """Pack the field: find the widest free spot, branch a scroll into it from the nearest
        scroll's outer coil, repeat until no gap of about rmin is left."""
        rng = self.rng
        P = []
        nx, ny = max(2, int(w / step)), max(2, int(h / step))
        for j in range(ny):
            for i in range(nx):
                px, py = x + (i + .5) * w / nx, y + (j + .5) * h / ny
                if self.inside(px, py):
                    P.append([px, py, 1e9, None])
        if not P:
            return self
        cell = {}
        for k, p in enumerate(P):
            cell.setdefault((int(p[0] // 30), int(p[1] // 30)), []).append(k)

        def upd(oid, cx, cy, R, reach=None):
            reach = R + (reach or self.rmax * 3)
            for i in range(int((cx - reach) // 30), int((cx + reach) // 30) + 1):
                for j in range(int((cy - reach) // 30), int((cy + reach) // 30) + 1):
                    for k in cell.get((i, j), ()):
                        p = P[k]
                        d = _m.hypot(p[0] - cx, p[1] - cy) - R
                        if d < p[2]:
                            p[2], p[3] = d, oid
        obs = []
        for oid, it in enumerate(self.items):
            if it[1] == "scroll":
                obs.append((it[2][1][0], it[2][1][1], it[2][4], oid))
            else:
                obs.extend((q[0], q[1], 2.5, oid) for q in it[2][0][::5])
        for p in P:
            for ox, oy, orr, oid in obs:
                d = _m.hypot(p[0] - ox, p[1] - oy) - orr
                if d < p[2]:
                    p[2], p[3] = d, oid
        import heapq
        hp = [(-p[2], k) for k, p in enumerate(P)]
        heapq.heapify(hp)
        while len(self.items) < max_items and hp:
            nd, k = heapq.heappop(hp)
            best = P[k]
            if -nd != best[2]:
                heapq.heappush(hp, (-best[2], k))
                continue
            if best[2] < self.rmin * 1.15:
                break
            px, py, D, oid = best
            if oid is None:
                continue
            R = min(self.rmax, D * .97) * rng.uniform(.9, 1.)
            self._branch_to(oid, px, py, R)
            upd(len(self.items) - 1, px, py, R)
            for kk in cell.get((int(px // 30), int(py // 30)), ()):
                heapq.heappush(hp, (-P[kk][2], kk))
        return self

    def draw(self, cv, egg=None, egg_gen=2):
        """Paint the branches first so each parent lies over its children. egg(cv, x, y, r) is
        cut into the eye of one scroll of generation egg_gen (the first big enough)."""
        rng = _rnd.Random(7)
        order = sorted(range(len(self.items)), key=lambda k: -self.items[k][0])
        egg_done = egg is None
        for k in order:
            gen, kind, data = self.items[k]
            if kind == "stem":
                pts, w0, w1, lv = data
                _draw_stem(cv, pts, w0, w1, rng, lv)
                continue
            pts, c, rad, s, R = data
            use = None
            if not egg_done and gen >= egg_gen and R > 14:
                use, egg_done = egg, True
            _draw_scroll(cv, pts, c, rad, s, R, rng, use)


def _leaf(cv, x, y, ang, L, W, bend, curl, rng, lobes=None):
    """A fine-scroll leaf: a curved blade scalloped on its outer edge and turning over at the tip,
    fine parallel cuts on its shadow side, a bright cut edge, a centre vein."""
    n = max(8, int(L / 1.2))
    sp = _C._euler(x, y, ang, L, lambda u: (bend + curl * _sm(.55, 1., u) ** 2 * 3.2) / L, n)
    c = 1 if bend >= 0 else -1
    nl = lobes or (3 if L > 14 else 2)
    ph = rng.uniform(0, .3)
    wo, wi = [], []
    for i in range(n + 1):
        u = i / n
        pr = min(1., u / .22) ** .6 * (1 - u) ** .7 * 1.35
        v = (u * nl + ph) % 1.
        wo.append(W * pr * (.6 + .4 * _m.sin(_PI * v) ** .6) + .3)
        wi.append(W * pr * .85 + .3)
    R = _C._Rib(sp, wi if c > 0 else wo, wo if c > 0 else wi)
    cv.obj([R.outline()], .5)
    cv.hair(_C._fill_lines(R, .22 * c, .92 * c, 1.5, .06, .9, 2))
    if W > 2.4:
        cv.hair(R.contour(-.05 * c, .12, .72))
    for j in range(nl):
        u = (j - ph) / nl
        if .18 < u < .85 and R.width(u, -c) > 1.8:
            cv.hair([R.at(u, -.95 * c), R.at(u + .05, -.4 * c)])
    return R


def _draw_stem(cv, pts, w0, w1, rng, leaves):
    n = len(pts)
    W = [w0 + (w1 - w0) * i / max(1, n - 1) for i in range(n)]
    R = _C._Rib(pts, W, W)
    if leaves:
        L = R.L
        u = .06
        sd = 1
        while u < .94:
            i = int(u * (n - 1))
            q = R.at(u, sd * .8)
            ll = rng.uniform(9, 13)
            _leaf(cv, q[0], q[1], _tangent(pts, i) + sd * .55, ll, ll * .22, -sd * .5, sd * 2.2, rng)
            sd = -sd
            u += rng.uniform(13, 18) / L
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(-.4, 0., 1.))
    cv.hair(R.contour(-.8, 0., 1.))


def _draw_scroll(cv, pts, c, rad, s, R, rng, egg=None):
    n = len(pts)
    hw0 = max(1., min(3.2, R * .13))
    W = [max(.6, hw0 * (rad[i] / R) ** .55) for i in range(n)]
    Rb = _C._Rib(pts, W, W)
    # where the coil proper starts (after any lead-in)
    k0 = 0
    while k0 < n - 1 and rad[k0 + 1] >= R - 1e-6:
        k0 += 1
    span = n - 1 - k0
    nlv = 1 if R < 10 else (2 if R < 16 else 3)
    fs = (.03, .2, .36)[:nlv]
    for j, f in enumerate(fs[::-1]):
        i = k0 + int(f * span)
        q = Rb.at(i / (n - 1), -s)
        ll = rad[i] * rng.uniform(.8, .95)
        _leaf(cv, q[0], q[1], _tangent(pts, i) - s * .55, ll, ll * .25, s * .9, -s * rng.uniform(1.2, 1.8), rng)
    if k0 > 6:
        i = k0 // 2
        q = Rb.at(i / (n - 1), s)
        ll = min(R * .7, 12.)
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .6, ll, ll * .24, -s * .7, s * 1.6, rng)
    cv.obj([Rb.outline()], .5)
    cv.hair(Rb.contour(.5 * s, 0., .92))
    if hw0 > 1.8:
        cv.hair(Rb.contour(.82 * s, 0., .8))
        cv.hair(Rb.contour(-.55 * s, .0, .35))
    if R > 15:
        i = k0 + int(.55 * span)
        q = Rb.at(i / (n - 1), s)
        ll = rad[i] * .95
        _leaf(cv, q[0], q[1], _tangent(pts, i) + s * .35, ll, ll * .2, s * 1.6, s * .3, rng, 2)
    ex, ey = pts[-1]
    if egg:
        egg(cv, ex, ey, max(5., R * .4))
    else:
        rr = max(1.1, W[-1] * 1.4)
        cv.obj([_C._ell_pts(ex, ey, rr, rr, 10)[:-1]], .5)
        cv.line(_C._ell_pts(ex, ey, .3, .3, 4))


# ---------------------------------------------------------------------------------------------
# borders, beading, medallion, arms
# ---------------------------------------------------------------------------------------------

def st_wire(d):
    """A gold-line (wire inlay) border along path d: white wire, black, white wire on a black bed."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="5"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="3"/>'
            f'<path d="{d}" fill="none" stroke="#000" stroke-width="1"/>')


def st_beads(d, pitch=3.5, r=1.):
    """A row of white beads on a black fillet along path d."""
    return (f'<path d="{d}" fill="none" stroke="#000" stroke-width="{_C._n(2 * r + 2)}"/>'
            f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_C._n(2 * r)}" stroke-linecap="round" '
            f'stroke-dasharray="0 {_C._n(pitch)}"/>')


def st_ell_d(cx, cy, rx, ry, n=96):
    return _C._d(_C._ell_pts(cx, cy, rx, ry, n), True, .1)


def st_poly_d(poly):
    return _C._d(list(poly), True, .1)


def st_medallion(cx, cy, rx, ry):
    """An inlaid portrait medallion: wire, a ring of beads, wire. -> (svg, field polygon)."""
    o = [f'<path d="{st_ell_d(cx, cy, rx + 7, ry + 7)}" fill="#000" stroke="none"/>',
         st_wire(st_ell_d(cx, cy, rx + 5.5, ry + 5.5)),
         st_beads(st_ell_d(cx, cy, rx + 1.5, ry + 1.5, 180), 3.5, 1.),
         f'<path d="{st_ell_d(cx, cy, rx - .5, ry - .5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), _C._ell_pts(cx, cy, rx - 1.2, ry - 1.2, 120)[:-1]


def st_arch(cx, top, bot, half, n=48):
    """An arched (round-headed) panel polygon: the binding's central panel."""
    r = half
    pts = [(cx - half, bot)]
    for i in range(n + 1):
        a = _PI + _PI * i / n
        pts.append((cx + r * _m.cos(a), top + r + r * _m.sin(a)))
    pts.append((cx + half, bot))
    return pts


def st_arch_medallion(cx, top, bot, half):
    o = [f'<path d="{st_poly_d(st_arch(cx, top - 7, bot + 7, half + 7))}" fill="#000" stroke="none"/>',
         st_wire(st_poly_d(st_arch(cx, top - 5.5, bot + 5.5, half + 5.5))),
         st_beads(st_poly_d(st_arch(cx, top - 1.5, bot + 1.5, half + 1.5, 96)), 3.5, 1.),
         f'<path d="{st_poly_d(st_arch(cx, top + .5, bot - .5, half - .5))}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_arch(cx, top + 1.2, bot - 1.2, half - 1.2, 72)


def st_shape_pts(shape, cx, cy, rx, ry, g=0., n=120, ph=0.):
    """The outline of a shaped panel grown outward by g: oval, roundel, arch or irregular."""
    if shape == "arch":
        return st_arch(cx, cy - ry - g, cy + ry + g, rx + g, max(24, n // 2))
    if shape == "roundel":
        rx = ry = min(rx, ry)
    pts = []
    for i in range(n):
        t = _TAU * i / n
        k = 1.
        if shape == "irregular":
            k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
        pts.append((cx + (rx * k + g) * _m.cos(t), cy + (ry * k + g) * _m.sin(t)))
    return pts


def st_shape_in(shape, x, y, cx, cy, rx, ry, g=0., ph=0.):
    if shape == "arch":
        if y >= cy - ry + rx:
            return abs(x - cx) < rx + g and y < cy + ry + g
        return _m.hypot(x - cx, y - (cy - ry + rx)) < rx + g
    if shape == "roundel":
        rx = ry = min(rx, ry)
    t = _m.atan2((y - cy) / max(ry, 1), (x - cx) / max(rx, 1))
    k = 1.
    if shape == "irregular":
        k = 1 + .07 * _m.sin(5 * t + ph) + .035 * _m.sin(9 * t + 2 * ph) + .02 * _m.cos(13 * t)
    return ((x - cx) / (rx * k + g)) ** 2 + ((y - cy) / (ry * k + g)) ** 2 < 1


def st_shaped_medallion(shape, cx, cy, rx, ry, ph=0.):
    """A shaped inlaid panel: black bed, wire, beads, white fillet. -> (svg, field polygon)."""
    if shape == "oval":
        return st_medallion(cx, cy, rx, ry)
    P = lambda g, n=120: st_poly_d(st_shape_pts(shape, cx, cy, rx, ry, g, n, ph))
    o = [f'<path d="{P(7)}" fill="#000" stroke="none"/>', st_wire(P(5.5)), st_beads(P(1.5, 180), 3.5, 1.),
         f'<path d="{P(-.5)}" fill="none" stroke="#fff" stroke-width="1"/>']
    return "".join(o), st_shape_pts(shape, cx, cy, rx, ry, -1.2, 120, ph)


def st_dedication(cx, foot, hh):
    """The small Somaster dedication cartouche at a front vignette's foot (about 30 px)."""
    return st_arms(cx, foot - hh / 2, hh * .5, hh * .5, mantling=True)


def st_device(w, h, seed, hk):
    """A marginal device (a 40-60 px roundel): the subject in a beaded roundel, the corners of
    the block cut away to the matte with a leaf in each spandrel."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - (4.5 if min(w, h) < 64 else 7.5)
    cv = StCanvas()
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = cx + sx * (w / 2 - 3), cy + sy * (h / 2 - 3)
            a = _m.atan2(cy - py, cx - px)
            if _m.hypot(px - cx, py - cy) > r + 9:
                L = max(4., (_m.hypot(px - cx, py - cy) - r - 6) * 1.1)
                _leaf(cv, px, py, a, L, L * .42, .5 * sx * sy, .35, _rnd.Random(seed + sx * 3 + sy))
    o.append(cv.svg())
    o.append(st_wire(st_rect_d(1.5, 1.5, w - 3, h - 3)))
    o.append(f'<path d="{st_ell_d(cx, cy, r + 3.5, r + 3.5)}" fill="#000"/>'
             f'<path d="{st_ell_d(cx, cy, r + 2, r + 2)}" fill="none" stroke="#fff" stroke-width="1" stroke-dasharray="1 1.5"/>'
             f'<path d="{st_ell_d(cx, cy, r - .2, r - .2)}" fill="none" stroke="#fff" stroke-width="1"/>')
    fld = _C._ell_pts(cx, cy, r - .9, r - .9, 72)[:-1]
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2d{w}x{h}v", fld, hk["field"](fld, "device") + st_rim(fld, 2.5)))
    return "".join(o)


def st_clip_poly(cid, poly, body):
    return f'<clipPath id="{cid}"><path d="{_C._d(list(poly), True, 0)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_clip_rect(cid, x, y, w, h, body):
    return f'<clipPath id="{cid}"><path d="{st_rect_d(x, y, w, h)}"/></clipPath><g clip-path="url(#{cid})">{body}</g>'


def st_sun(cv, cx, cy, r, rays=16):
    disc = _C._ell_pts(cx, cy, r, r, 28)[:-1]
    for k in range(rays):
        a = k * _TAU / rays
        ln = r * (1.9 if k % 2 == 0 else 1.5)
        w = _PI / rays * .7
        tri = [(cx + r * .9 * _m.cos(a - w), cy + r * .9 * _m.sin(a - w)), (cx + ln * _m.cos(a), cy + ln * _m.sin(a)),
               (cx + r * .9 * _m.cos(a + w), cy + r * .9 * _m.sin(a + w))]
        cv.obj([tri], .5)
        cv.hair([(cx + r * _m.cos(a + w * .4), cy + r * _m.sin(a + w * .4)), (cx + ln * .9 * _m.cos(a), cy + ln * .9 * _m.sin(a))])
    cv.obj([disc], .5)
    cv.hair([p for p in _C.hatch_poly(disc, 45, 1.5) if p[0][0] + p[0][1] > cx + cy - r * .3])


def _stick(cv, x0, y0, x1, y1, w):
    a = _m.atan2(y1 - y0, x1 - x0)
    n = 16
    pts = [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]
    W = [w * (1 - .55 * _sm(.6, .95, i / n)) for i in range(n + 1)]
    R = _C._Rib(pts, W, W)
    cv.obj([R.outline()], .5)
    cv.hair(R.contour(.6, .02, .93))
    tx, ty = x1 + _m.cos(a) * w * .5, y1 + _m.sin(a) * w * .5
    cv.obj([_C._ell_pts(tx, ty, w * 1.1, w * .8, 12)[:-1]], .5)


def st_crossed_sticks(cv, cx, cy, L, w=1.3, ang=0.):
    """Parker's crossed drumsticks, bead tips up."""
    for sd in (-1, 1):
        a = ang - _PI / 2 + sd * .62
        dx, dy = _m.cos(a) * L / 2, _m.sin(a) * L / 2
        _stick(cv, cx - dx, cy - dy, cx + dx, cy + dy, w)


_FLEUR = [(0, -1), (.13, -.72), (.16, -.42), (.1, -.15), (.24, -.2), (.42, -.42), (.62, -.48), (.78, -.38),
          (.8, -.18), (.68, -.02), (.54, .04), (.62, -.12), (.6, -.26), (.48, -.26), (.34, -.08), (.22, .1),
          (.36, .1), (.36, .22), (.14, .22), (.2, .5), (.38, .72), (.2, .7), (.08, .54), (0, .62)]


def _fleur(cx, cy, s):
    """A fleur-de-lis about 2s tall, as one closed polygon."""
    right = [(cx + x * s, cy + y * s) for x, y in _FLEUR]
    left = [(cx - x * s, cy + y * s) for x, y in _FLEUR[::-1]][1:-1]
    return right + left


def _heater(cx, top, w, h, n=24):
    """A heater shield outline: straight chief, sides curving to the point."""
    pts = [(cx - w / 2, top), (cx + w / 2, top)]
    for i in range(n + 1):
        t = i / n
        pts.append((cx + w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    for i in range(n, -1, -1):
        t = i / n
        pts.append((cx - w / 2 * (1 - t ** 1.8), top + h * .42 + h * .58 * _m.sin(t * _PI / 2)))
    return pts


def st_arms(cx, cy, rx, ry, mantling=True):
    """Parker's arms, Somaster: Or, a castle between five fleurs-de-lis sable. A heater shield,
    Or as an even field of fine dots (Petra Sancta), the charges sable cut in solid black with
    white mortar lines; acanthus mantling springs from behind the shield's top corners."""
    o = []
    sh = min(ry * 2, rx * 2.3)
    sw = sh * .84
    top = cy - sh / 2
    shield = _heater(cx, top, sw, sh)
    if mantling:
        cv = _C.Canvas()
        rng = _rnd.Random(5)
        for sd in (-1, 1):
            for k, (a, L) in enumerate(((-.3, .9), (.25, .8), (.85, .7), (1.35, .55))):
                ang = (_PI / 2 - (a + 1.2)) if sd > 0 else (_PI / 2 + (a + 1.2))
                x0, y0 = cx + sd * sw * .42, top + sh * .1 + k * sh * .12
                _leaf(cv, x0, y0, -ang + _PI if False else (a * sd + (0 if sd > 0 else _PI)), sh * L * .55, sh * L * .12,
                      sd * .8, -sd * 2., rng, 3)
        o.append(cv.svg())
    d = st_poly_d(shield)
    o.append(f'<path d="{d}" fill="#000" stroke="#000" stroke-width="3"/>')
    o.append(f'<path d="{d}" fill="#fff" stroke="#fff" stroke-width="1"/>')
    o.append(f'<path d="{d}" fill="url(#s2o)" stroke="#000" stroke-width=".5"/>')
    blk = []
    s = sh * .085
    for fx, fy in ((-.26, .14), (0, .14), (.26, .14), (-.36, .55), (.36, .55)):
        blk.append(_fleur(cx + fx * sw, top + fy * sh + s * .1, s))
    # the castle: two towers and a curtain wall, crenellated, an arched gate with a portcullis
    cw, chh = sw * .46, sh * .3
    bx0, by1 = cx - cw / 2, top + sh * .72
    tw, th = cw * .24, chh * 1.3
    mer = tw / 5
    for tx in (bx0, bx0 + cw - tw):
        ty = by1 - th
        pts = [(tx, by1), (tx, ty)]
        for k in range(5):
            x = tx + k * mer
            if k % 2 == 0:
                pts += [(x, ty - mer), (x + mer, ty - mer)]
            else:
                pts += [(x, ty), (x + mer, ty)]
        pts += [(tx + tw, ty), (tx + tw, by1)]
        blk.append(pts)
    wy = by1 - chh * .72
    wx0, wx1 = bx0 + tw - .2, bx0 + cw - tw + .2
    nm = max(3, int((wx1 - wx0) / mer))
    mm = (wx1 - wx0) / nm
    pts = [(wx0, by1), (wx0, wy)]
    for k in range(nm):
        x = wx0 + k * mm
        if k % 2 == 1:
            pts += [(x, wy - mer * .9), (x + mm, wy - mer * .9)]
        else:
            pts += [(x, wy), (x + mm, wy)]
    pts += [(wx1, wy), (wx1, by1)]
    blk.append(pts)
    o.append(f'<path d="{"".join(st_poly_d(p) for p in blk)}" fill="#000" stroke="none"/>')
    # white work in the sable: mortar courses, tower windows, the gate and its portcullis
    lines = []
    for k in range(1, 6):
        y = by1 - k * chh * .2
        lines.append([(bx0 + 1, y), (bx0 + tw - 1, y)])
        lines.append([(bx0 + cw - tw + 1, y), (bx0 + cw - 1, y)])
        if y > wy + 1:
            lines.append([(wx0 + 1, y), (wx1 - 1, y)])
    gw, gh = cw * .2, chh * .55
    gate = [(cx - gw / 2, by1)] + [(cx - gw / 2 * _m.cos(t * _PI / 12), by1 - gh * .6 - gw / 2 * _m.sin(t * _PI / 12)) for t in range(13)] + [(cx + gw / 2, by1)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in lines)}" stroke="#fff" stroke-width="1" fill="none"/>')
    o.append(f'<path d="{st_poly_d(gate)}" fill="#fff" stroke="none"/>')
    pc = [[(cx + gw * (k / 4 - .5) * .8, by1 - gh * .95), (cx + gw * (k / 4 - .5) * .8, by1)] for k in range(5)]
    pc += [[(cx - gw * .45, by1 - gh * .3 * k), (cx + gw * .45, by1 - gh * .3 * k)] for k in (1, 2)]
    o.append(f'<path d="{"".join(_C._d(l, tol=0) for l in pc)}" stroke="#000" stroke-width=".5" fill="none"/>')
    for tx in (bx0 + tw / 2, bx0 + cw - tw / 2):
        o.append(f'<path d="M{_C._n(tx)},{_C._n(by1 - th * .75)}v{_C._n(th * .22)}" stroke="#fff" stroke-width="1"/>')
    return "".join(o)


def st_sky(x0, y0, x1, y1, seed, avoid=None, clouds=None, top_dark=.32, pitch=(2., 2., 3., 3.)):
    """A Dore sky, not a ruled one: long lines that swell over billowing cloud banks (lit tops
    left white, undersides shaded), dark and cross-cut at the zenith, opening toward the horizon.
    Returns (hair polylines, line polylines). avoid(x, y) breaks the lines (moon, towers)."""
    rng = _rnd.Random(seed)
    W, H = x1 - x0, y1 - y0
    if clouds is None:
        clouds = []
        n = max(2, int(W / 80) + 1)
        for i in range(n):
            cx = x0 + W * (i + rng.uniform(.2, .8)) / n
            cy = y0 + H * rng.uniform(.3, .75)
            clouds.append((cx, cy, W / n * rng.uniform(.45, .7), H * rng.uniform(.09, .16)))
    hair, heavy = [], []

    def cloud_at(x, y):
        for cx, cy, rx, ry in clouds:
            dx = (x - cx) / rx
            if abs(dx) < 1:
                top = cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))
                bot = cy + ry * .35 * (1 - dx * dx) ** .5
                if top <= y <= bot:
                    return (y - top) / max(.5, bot - top)
        return None
    y = y0 + .75
    while y < y1:
        f = (y - y0) / max(1., H)
        p = pitch[min(len(pitch) - 1, int(f * len(pitch)))]
        run = []
        x = x0
        while x <= x1 + 3:
            yy = y
            for ccx, ccy, crx, cry in clouds:
                dx = (x - ccx) / (crx * 1.5)
                if abs(dx) < 1 and y > ccy:
                    yy += cry * .22 * (1 - dx * dx) ** 2 * max(0., 1 - (y - ccy) / (cry * 3))
            cf = cloud_at(x, yy)
            lit = cf is not None and cf < .55
            if lit or (avoid and avoid(x, yy)):
                if len(run) > 1:
                    hair.append(run)
                run = []
            else:
                run.append((x, yy))
            x += 3.
        if len(run) > 1:
            hair.append(run)
        y += p
    # cloud edges: billowed tops, shaded bellies
    for cx, cy, rx, ry in clouds:
        top = []
        for i in range(41):
            dx = -1 + 2 * i / 40
            top.append((cx + dx * rx, cy - ry * (1 - dx * dx) ** .5 * (1 + .25 * _m.sin(dx * 9 + cx))))
        hair.append(top)
        for k in range(1, 4):
            arc = []
            for i in range(31):
                dx = -.85 + 1.7 * i / 30
                arc.append((cx + dx * rx * (1 - .12 * k), cy - ry * (1 - dx * dx) ** .5 * (.55 - .14 * k) + ry * .1 * k))
            hair.append(arc)
    # the zenith: cross-cut so the sky deepens upward
    zt = y0 + H * top_dark
    for ln in _C.hatch_poly([(x0, y0), (x1, y0), (x1, zt), (x0, zt)], 30, 3.):
        if avoid:
            a_, b_ = ln
            seg, cur = [], []
            for i in range(int(_m.dist(a_, b_) / 2) + 2):
                t = i / max(1, int(_m.dist(a_, b_) / 2) + 1)
                q = (a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t)
                if avoid(*q):
                    if len(cur) > 1:
                        hair.append(cur)
                    cur = []
                else:
                    cur.append(q)
            if len(cur) > 1:
                hair.append(cur)
        else:
            hair.append(ln)
    return hair, heavy


def st_rim(fld, depth=12., uid="r"):
    """Light emerging from dark: concentric cuts round the inside of a medallion field, close and
    heavy at the rim, thinning inward, so the subject glows out of a dark surround."""
    cx = sum(p[0] for p in fld) / len(fld)
    cy = sum(p[1] for p in fld) / len(fld)
    size = min(max(abs(p[0] - cx) for p in fld), max(abs(p[1] - cy) for p in fld))
    o1, o5 = [], []
    d = .75
    while d < depth:
        k = 1 - d / size
        ring = [(cx + (p[0] - cx) * k, cy + (p[1] - cy) * k) for p in fld]
        (o1 if d < depth * .35 else o5).append(_C._d(ring + [ring[0]], tol=.2))
        d += 2. if d < depth * .35 else 1.5 + (d / depth) * 1.5
    return (f'<path d="{"".join(o1)}" fill="none" stroke="#000" stroke-width="1"/>'
            f'<path d="{"".join(o5)}" fill="none" stroke="#000" stroke-width=".5"/>')


# ---------------------------------------------------------------------------------------------
# Easter eggs cut into a scroll's eye: egg(cv, x, y, r) draws inside a disc of radius r
# ---------------------------------------------------------------------------------------------

def _egg_disc(cv, x, y, r):
    cv.obj([_C._ell_pts(x, y, r, r, 28)[:-1]], 1.)
    cv.hair(_C._ell_pts(x, y, r - 1.2, r - 1.2, 28))


def egg_sticks(cv, x, y, r):
    """Parker's crossed drumsticks."""
    _egg_disc(cv, x, y, r)
    st_crossed_sticks(cv, x, y + r * .05, r * 1.45, max(.6, r * .09))


def egg_P(cv, x, y, r):
    """A "P" monogram, cut as a stem and a bowl with a flourish."""
    _egg_disc(cv, x, y, r)
    h = r * 1.1
    cv.line([(x - h * .22, y + h * .5), (x - h * .22, y - h * .5)])
    bowl = [(x - h * .22, y - h * .5)] + [(x - h * .05 + h * .3 * _m.sin(t * _PI / 10), y - h * .25 - h * .25 * _m.cos(t * _PI / 10)) for t in range(11)] + [(x - h * .22, y)]
    cv.line(bowl)
    cv.hair([(x - h * .45, y + h * .5), (x + h * .05, y + h * .5)])
    cv.hair([(x - h * .22, y + h * .5), (x - h * .5, y + h * .62), (x - h * .62, y + h * .45)])


def egg_note(cv, x, y, r):
    """A swing eighth-note pair (jazz)."""
    _egg_disc(cv, x, y, r)
    s = r * .32
    for dx in (-1, 1):
        hx, hy = x + dx * s * 1.1 - s * .4, y + s * 1.1
        cv.obj([_C._ell_pts(hx, hy, s * .55, s * .38, 12)[:-1]], .5)
        cv.line(_C._ell_pts(hx, hy, s * .3, s * .15, 8))
        cv.line([(hx + s * .5, hy), (hx + s * .5, y - s * 1.5)])
    cv.heavy([(x - s * .6 + s * .1, y - s * 1.5), (x + s * 1.6 + s * .1, y - s * 1.5)])


def egg_cymbal(cv, x, y, r):
    """A tiny ride cymbal on its stand, lathe rings and a bell."""
    _egg_disc(cv, x, y, r)
    cy = y - r * .15
    cv.obj([_C._ell_pts(x, cy, r * .8, r * .22, 24)[:-1]], .5)
    for k in (1, 2, 3):
        cv.hair(_C._ell_pts(x, cy, r * .8 * k / 4, r * .22 * k / 4, 20))
    cv.obj([_C._ell_pts(x, cy - r * .08, r * .16, r * .1, 10)[:-1]], .5)
    cv.line([(x, cy + r * .2), (x, y + r * .7)])
    cv.hair([(x, y + r * .55), (x - r * .35, y + r * .78)])
    cv.hair([(x, y + r * .55), (x + r * .35, y + r * .78)])


def egg_hood(cv, x, y, r):
    """Mt. Hood: the snow cone, its glaciers and a timber line."""
    _egg_disc(cv, x, y, r)
    pk = [(x - r * .82, y + r * .45), (x - r * .1, y - r * .55), (x + r * .05, y - r * .6), (x + r * .82, y + r * .45)]
    cv.obj([pk], .5)
    cv.hair([(x - r * .02, y - r * .5), (x - r * .25, y + r * .05)])
    cv.hair([(x + r * .05, y - r * .5), (x + r * .3, y + r * .1)])
    cv.hair(_C.hatch_poly([(x + r * .05, y - r * .58), (x + r * .82, y + r * .45), (x + r * .25, y + r * .45)], 60, 1.5))
    for k in range(7):
        tx = x - r * .7 + k * r * .23
        cv.line([(tx, y + r * .62), (tx, y + r * .38)])


def egg_pinwheel(cv, x, y, r):
    """The Blazers pinwheel: five pairs of swept bars turning about a hub."""
    _egg_disc(cv, x, y, r)
    for k in range(5):
        a = k * _TAU / 5 - _PI / 2
        for off in (-.12, .12):
            p0 = (x + r * .18 * _m.cos(a + off), y + r * .18 * _m.sin(a + off))
            p1 = (x + r * .78 * _m.cos(a + off + .35), y + r * .78 * _m.sin(a + off + .35))
            cv.line([p0, p1])


def egg_heron(cv, x, y, r):
    """A Sauvie Island heron's head and S neck, crest plume and dagger bill."""
    _egg_disc(cv, x, y, r)
    neck = [(x - r * .1, y + r * .8), (x - r * .35, y + r * .3), (x - r * .05, y - r * .05), (x - r * .25, y - r * .4)]
    cv.line(neck)
    cv.line([(x - r * .05 + r * .15, y + r * .8), (x - r * .2 + r * .12, y + r * .3), (x + r * .12, y - r * .02), (x - r * .1, y - r * .35)])
    hd = _C._ell_pts(x - r * .2, y - r * .45, r * .16, r * .11, 12)[:-1]
    cv.obj([hd], .5)
    cv.line([(x - r * .05, y - r * .48), (x + r * .65, y - r * .38)])
    cv.hair([(x - r * .32, y - r * .5), (x - r * .7, y - r * .55)])


def egg_dog(cv, x, y, r):
    """Parker's dog, head on its paws, curled asleep in the eye of the scroll."""
    _egg_disc(cv, x, y, r)
    body = _C._ell_pts(x + r * .05, y + r * .15, r * .72, r * .42, 24)[:-1]
    cv.obj([body], .5)
    cv.hair(_C._fill_lines(_C._Rib([(x - r * .6, y + r * .15), (x + r * .7, y + r * .15)], [r * .38, r * .38], [r * .38, r * .38]), -.3, -.95, 1.5, .1, .9, 2))
    head = _C._ell_pts(x - r * .38, y - r * .05, r * .26, r * .2, 16)[:-1]
    cv.obj([head], .5)
    cv.obj([[(x - r * .48, y - r * .2), (x - r * .3, y - r * .45), (x - r * .22, y - r * .16)]], .5)
    cv.line(_C._ell_pts(x - r * .6, y - r * .02, .5, .5, 4))
    cv.hair([(x - r * .45, y - r * .06), (x - r * .36, y - r * .04)])
    cv.hair([(x + r * .7, y + r * .1), (x + r * .55, y + r * .45), (x + r * .1, y + r * .52)])


def egg_kranok(cv, x, y, r):
    """A Thai kranok flame: three flame tongues curling up out of a lotus calyx."""
    _egg_disc(cv, x, y, r)
    for sd, L, a in ((0, 1., -_PI / 2), (-1, .7, -_PI / 2 - .55), (1, .7, -_PI / 2 + .55)):
        bx = x + sd * r * .12
        rib = _C._euler(bx, y + r * .5, a, r * L, lambda u, s_=sd or 1: s_ * 2.2 * _sm(.5, 1, u) / (r * L), 12)
        W = [r * .16 * (1 - i / 12) ** .7 + .3 for i in range(13)]
        R = _C._Rib(rib, W, W)
        cv.obj([R.outline()], .5)
        cv.hair(R.contour(.4, .05, .85))
    cv.obj([_C._ell_pts(x, y + r * .55, r * .3, r * .14, 14)[:-1]], .5)


def egg_panel(cv, x, y, r):
    """A solar panel on its rack: a grid of cells, one ray of sun."""
    _egg_disc(cv, x, y, r)
    q = [(x - r * .7, y + r * .2), (x + r * .45, y + r * .2), (x + r * .7, y - r * .35), (x - r * .45, y - r * .35)]
    cv.obj([q], .5)
    for k in range(1, 4):
        t = k / 4
        cv.hair([(q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1]), (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1])])
    cv.hair([((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2), ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)])
    cv.line([(x - r * .1, y + r * .2), (x - r * .1, y + r * .65)])
    cv.line([(x - r * .4, y + r * .65), (x + r * .25, y + r * .65)])


# ---------------------------------------------------------------------------------------------
# lettering: engraved Roman capitals as strokes (no <text>)
# ---------------------------------------------------------------------------------------------

_OV = [(.5 + .5 * _m.cos(_TAU * i / 20 - _PI / 2), .5 + .5 * _m.sin(_TAU * i / 20 - _PI / 2)) for i in range(21)]
_GL = {
    "A": ([[(0, 1), (.5, 0), (1, 1)], [(.22, .62), (.78, .62)]], .85),
    "B": ([[(0, 0), (0, 1), (.7, 1), (.9, .85), (.9, .65), (.7, .5), (0, .5)], [(0, 0), (.62, 0), (.82, .12), (.82, .38), (.62, .5)]], .75),
    "C": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .85)]], .8),
    "D": ([[(0, 0), (0, 1), (.55, 1), (.92, .72), (.92, .28), (.55, 0), (0, 0)]], .8),
    "E": ([[(.85, 0), (0, 0), (0, 1), (.85, 1)], [(0, .5), (.65, .5)]], .7),
    "F": ([[(.85, 0), (0, 0), (0, 1)], [(0, .5), (.65, .5)]], .65),
    "G": ([[(.95, .15), (.72, 0), (.3, 0), (0, .25), (0, .75), (.3, 1), (.72, 1), (.95, .8), (.95, .55), (.55, .55)]], .82),
    "H": ([[(0, 0), (0, 1)], [(1, 0), (1, 1)], [(0, .5), (1, .5)]], .8),
    "I": ([[(.5, 0), (.5, 1)]], .3),
    "J": ([[(.8, 0), (.8, .78), (.6, 1), (.2, 1), (0, .8)]], .6),
    "K": ([[(0, 0), (0, 1)], [(.9, 0), (0, .62)], [(.3, .42), (.95, 1)]], .78),
    "L": ([[(0, 0), (0, 1), (.85, 1)]], .65),
    "M": ([[(0, 1), (0, 0), (.5, .65), (1, 0), (1, 1)]], 1.),
    "N": ([[(0, 1), (0, 0), (1, 1), (1, 0)]], .82),
    "O": ([_OV], .9),
    "P": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)]], .72),
    "Q": ([_OV, [(.6, .72), (1, 1.06)]], .9),
    "R": ([[(0, 1), (0, 0), (.7, 0), (.9, .15), (.9, .35), (.7, .5), (0, .5)], [(.45, .5), (.95, 1)]], .76),
    "S": ([[(.9, .12), (.7, 0), (.25, 0), (.05, .15), (.05, .35), (.25, .47), (.75, .53), (.95, .66), (.95, .85), (.75, 1), (.25, 1), (.05, .88)]], .7),
    "T": ([[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]], .78),
    "U": ([[(0, 0), (0, .75), (.25, 1), (.75, 1), (1, .75), (1, 0)]], .8),
    "V": ([[(0, 0), (.5, 1), (1, 0)]], .82),
    "W": ([[(0, 0), (.25, 1), (.5, .35), (.75, 1), (1, 0)]], 1.1),
    "X": ([[(0, 0), (1, 1)], [(1, 0), (0, 1)]], .8),
    "Y": ([[(0, 0), (.5, .5), (1, 0)], [(.5, .5), (.5, 1)]], .8),
    "Z": ([[(0, 0), (1, 0), (0, 1), (1, 1)]], .76),
    "0": ([[(.5 + .45 * _m.cos(_TAU * i / 20), .5 + .5 * _m.sin(_TAU * i / 20)) for i in range(21)]], .65),
    "1": ([[(.25, .2), (.55, 0), (.55, 1)], [(.25, 1), (.85, 1)]], .55),
    "2": ([[(.05, .2), (.25, 0), (.75, 0), (.95, .2), (.95, .4), (0, 1), (1, 1)]], .65),
    "3": ([[(.05, .1), (.3, 0), (.75, 0), (.95, .2), (.9, .4), (.5, .5), (.9, .6), (.95, .8), (.75, 1), (.3, 1), (.05, .9)]], .65),
    "4": ([[(.75, 1), (.75, 0), (0, .7), (1, .7)]], .65),
    "5": ([[(.9, 0), (.15, 0), (.05, .45), (.6, .4), (.95, .6), (.95, .8), (.7, 1), (.25, 1), (.05, .9)]], .65),
    "6": ([[(.85, .05), (.5, 0), (.15, .2), (.05, .6), (.15, .9), (.5, 1), (.85, .9), (.95, .7), (.8, .5), (.45, .45), (.1, .6)]], .65),
    "7": ([[(0, 0), (1, 0), (.35, 1)]], .62),
    "8": ([[(.5, .5), (.15, .38), (.1, .15), (.3, 0), (.7, 0), (.9, .15), (.85, .38), (.5, .5), (.1, .65), (.05, .85), (.3, 1), (.7, 1), (.95, .85), (.9, .65), (.5, .5)]], .65),
    "9": ([[(.9, .4), (.55, .55), (.15, .45), (.05, .25), (.2, .05), (.55, 0), (.9, .2), (.95, .5), (.8, .85), (.45, 1), (.15, .95)]], .65),
    "-": ([[(.1, .55), (.9, .55)]], .5),
    "·": ([[(.45, .5), (.55, .5)]], .35),
    ".": ([[(.45, .95), (.55, .95)]], .3),
    ",": ([[(.5, .9), (.35, 1.15)]], .3),
    ":": ([[(.5, .3), (.5, .32)], [(.5, .9), (.5, .92)]], .3),
    "'": ([[(.5, 0), (.4, .25)]], .25),
    "/": ([[(1, 0), (0, 1)]], .55),
    "&": ([[(1, 1), (.2, .35), (.25, .08), (.5, 0), (.7, .1), (.7, .3), (.1, .7), (.15, .95), (.5, 1), (.85, .7)]], .8),
    "°": ([[(.3 + .2 * _m.cos(_TAU * i / 10), .15 + .15 * _m.sin(_TAU * i / 10)) for i in range(11)]], .45),
    "%": ([[(1, 0), (0, 1)], [(.2 + .15 * _m.cos(_TAU * i / 10), .18 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)],
           [(.8 + .15 * _m.cos(_TAU * i / 10), .82 + .16 * _m.sin(_TAU * i / 10)) for i in range(11)]], .75),
    " ": ([], .45),
}


def st_text_w(text, h, track=.32):
    t = [ch if ch in _GL else " " for ch in text.upper()]
    return sum(_GL[ch][1] * h * .78 for ch in t) + track * h * max(0, len(t) - 1)


def st_letter(text, h, centre=None, cx=0., cy=0., track=.32, sw=None, fit=None):
    """Monoline engraved capitals h tall, centred on (cx, cy) or along the polyline `centre`.
    fit shrinks the lettering to that width. -> svg path."""
    t = [ch if ch in _GL else " " for ch in text.upper()]
    if fit:
        tw = st_text_w(text, h, track)
        if tw > fit:
            h *= fit / tw
    tw = st_text_w(text, h, track)
    if centre:
        acc = [0.]
        for i in range(1, len(centre)):
            acc.append(acc[-1] + _m.dist(centre[i], centre[i - 1]))
        tot = acc[-1]

        def at(sv):
            sv = max(0., min(tot, sv))
            for i in range(1, len(acc)):
                if acc[i] >= sv:
                    f = (sv - acc[i - 1]) / max(1e-6, acc[i] - acc[i - 1])
                    p0, p1 = centre[i - 1], centre[i]
                    return p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f, _m.atan2(p1[1] - p0[1], p1[0] - p0[0])
            return centre[-1][0], centre[-1][1], 0.
        pos = (tot - tw) / 2
    else:
        pos = -tw / 2
    d = []
    for ch in t:
        strokes, wf = _GL[ch]
        gw = wf * h * .78
        if centre:
            mx, my, a = at(pos + gw / 2)
        else:
            mx, my, a = cx + pos + gw / 2, cy, 0.
        ca, sa = _m.cos(a), _m.sin(a)
        for st in strokes:
            pts = []
            for gx, gy in st:
                lx, ly = (gx - .5) * gw, (gy - .5) * h
                pts.append((mx + lx * ca - ly * sa, my + lx * sa + ly * ca))
            d.append(_C._d(pts, tol=.05))
        pos += gw + track * h
    w = sw or (1. if h >= 7 else .5)
    return f'<path d="{"".join(d)}" fill="none" stroke="#000" stroke-width="{_C._n(w)}"/>'


def st_tablet_text(tx, ty, tw, th, lines):
    """Lines of lettering in a tablet, over a dotted Or ground cut back behind each line."""
    o = [f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>']
    n = len(lines)
    lh = min(th / (n * 1.6 + .4), 11.)
    for i, ln in enumerate(lines):
        cy = ty + th * (i + .5) / n
        w = min(tw - 8, st_text_w(ln, lh) + lh * 1.4)
        o.append(f'<path d="{st_rect_d(tx + (tw - w) / 2, cy - lh * .85, w, lh * 1.7)}" fill="#fff" stroke="#000" stroke-width=".5"/>')
        o.append(st_letter(ln, lh, cx=tx + tw / 2, cy=cy, fit=tw - 12))
    return "".join(o)


def st_doc(w, h, body):
    return _C.svg_doc(w, h, _ST_DEFS + body)
# ==== END STUDIO FRAME ==========================================================================
# ==== STUDIO LAYOUTS ============================================================================


def _in_ell(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


def st_border(w, h, inset=3.):
    """The plate's own gold-line border and an inner row of beads, all four edges."""
    return (st_wire(st_rect_d(inset, inset, w - 2 * inset, h - 2 * inset))
            + st_beads(st_rect_d(inset + 4.5, inset + 4.5, w - 2 * inset - 9, h - 2 * inset - 9), 3.5, 1.))


def _st_clip_runs(pl, mask, x0, y0, W, H, out, step=1.5):
    """_clip_runs at a 1.5 px test step (lines are cut cleanly enough; half the work)."""
    px, py = pl[0]
    pts = [pl[0]]
    for q in pl[1:]:
        dx, dy = q[0] - px, q[1] - py
        L = _m.hypot(dx, dy)
        if L > step:
            k = int(L / step)
            for j in range(1, k + 1):
                t = j / (k + 1)
                pts.append((px + dx * t, py + dy * t))
        pts.append(q)
        px, py = q
    run = []
    for (x, y) in pts:
        xi, yi = int(x - x0), int(y - y0)
        if 0 <= xi < W and 0 <= yi < H and mask[yi][xi]:
            if len(run) > 1:
                out.append(run)
            run = []
        else:
            run.append((x, y))
    if len(run) > 1:
        out.append(run)


class StCanvas(_C.Canvas):
    """The house Canvas, emitting with a slightly coarser simplification for the fine cuts so a
    packed field of scroll stays inside the byte budget (the eye cannot see 0.15 px)."""

    def svg(self, tol_fill=.95, tol_hair=.65, tol_line=.55):
        if not self.objs:
            return ""
        xs = [p[0] for o in self.objs for poly in o[0] for p in poly] or [0.]
        ys = [p[1] for o in self.objs for poly in o[0] for p in poly] or [0.]
        x0, y0 = int(_m.floor(min(xs))) - 2, int(_m.floor(min(ys))) - 2
        W, H = int(max(xs)) - x0 + 3, int(max(ys)) - y0 + 3
        mask = [bytearray(W) for _ in range(H)]
        out = {.5: [], 1.: [], 1.5: []}
        for polys, ow, strokes in reversed(self.objs):
            for wd, lines in strokes.items():
                for pl in lines:
                    _st_clip_runs(pl, mask, x0, y0, W, H, out[wd])
            if ow:
                for poly in polys:
                    _st_clip_runs(poly + [poly[0]], mask, x0, y0, W, H, out[float(ow)])
            for poly in polys:
                _C._fill_mask(poly, mask, x0, y0, W, H)
        res = []
        pen = _C._Pen()
        for polys, _, _ in self.objs:
            for poly in polys:
                pen.add(poly if _C._area(poly) >= 0 else poly[::-1], True, tol_fill)
        if pen.o:
            res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="#fff" stroke="none"/>')
        for wd in (.5, 1., 1.5):
            if out[wd]:
                pen = _C._Pen()
                for pl in out[wd]:
                    if len(pl) > 2 or _m.dist(pl[0], pl[-1]) > .6:
                        pen.add(pl, False, tol_hair if wd < 1 else tol_line)
                res.append(f'<path transform="scale(.25)" d="{pen.d()}" fill="none" stroke="#000" stroke-width="{_C._n(wd * 4)}"/>')
        return "".join(res)


def _scroll_layer(field, uid, x, y, w, h, egg=None, egg_gen=2):
    cv = StCanvas()
    field.draw(cv, egg, egg_gen)
    return st_clip_rect(uid, x, y, w, h, cv.svg())


def st_band(w, h, seed, hk):
    """h < 110: a carved band. An inlaid medallion holds the subject; from it a stem runs to
    either edge, the fine scroll branching off it to fill the band."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2 + hk.get("dx", 0.), h / 2
    ry = max(4., h / 2 - 8.5) if h >= 40 else max(4., h / 2 - 7.2)
    rx = min(w * .2, max(ry * 1.5, ry * hk.get("aspect", 1.7)))
    if h < 40:
        ins = 5.
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 2 < y < fy1 + 2 and not _in_ell(x, y, cx, cy, rx + 12, ry + 12)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(3.5 if h < 40 else 4.5, gh * .12), rmax=max(4.6, gh * .32), seed=seed, slack=.9)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        L = (w / 2 - rx - 14) * 1.05
        x0 = cx + sd * (rx + 9)
        a = 0. if sd > 0 else _PI
        pts = []
        n = int(L / 2)
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + sd * L * u, cy + gh * .18 * _m.sin(u * _TAU * (L / (gh * 2.2)) + (0 if sd > 0 else 1.3))))
        F.stem(pts, 1.6, 1.0, leaves=False)
    F.grow(8)
    F.fill(fx0 - 4, fy0 - 2, fx1 - fx0 + 8, fy1 - fy0 + 4, 3., hk.get("max_items", 160))
    o.append(_scroll_layer(F, f"s2b{w}x{h}", 0, 0, w, h, hk.get("egg"), 1))
    o.append(st_border(w, h, 1.5 if h < 40 else 3.))
    m, fld = st_medallion(cx, cy, rx, ry)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2b{w}x{h}v", fld, hk["field"](fld, "band") + st_rim(fld, hk.get("rim", 5.))))
    return "".join(o)


def st_medium(w, h, seed, hk):
    """110-260: the medallion between two panels of fine scroll, each grown from a stem that
    sweeps out of the medallion's foot; gold-line border and beading round the plate."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    cx, cy = w / 2, h / 2
    shape = hk.get("shape", "oval")
    ded = 15. if hk.get("dedication") else 0.
    ry = h / 2 - ins - 6
    rx = min(w * hk.get("cw", .21), ry * hk.get("aspect", 1.45))
    if shape == "roundel":
        rx = ry
    if shape == "arch":
        rx = min(rx, ry * 1.1)
    ph = (seed % 97) * .07
    fx0, fy0, fx1, fy1 = ins, ins, w - ins, h - ins

    def inside(x, y):
        return fx0 - 4 < x < fx1 + 4 and fy0 - 3 < y < fy1 + 3 and not st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph) and not (ded and abs(x - cx) < 34 and y > h - ins - 2 * ded - 6)
    gh = fy1 - fy0
    F = ScrollField(inside, rmin=max(6., gh * .055), rmax=min(26., gh * .2), seed=seed, slack=.88)
    rng = _rnd.Random(seed)
    for sd in (-1, 1):
        a0 = _PI / 2 + sd * .25 * _PI
        x0, y0 = cx + (rx + 10) * _m.cos(_PI / 2 - sd * .9), cy + (ry + 10) * _m.sin(_PI / 2 - sd * .9)
        head = 0. if sd > 0 else _PI
        L = (w / 2 - rx - 20)
        k = -sd * .9 / L
        F.stem(st_sweep(x0, y0, head + sd * .35, L * 1.05, k * 1.5, -k * 1.2), 2., 1.1)
        x1, y1 = cx + (rx + 10) * _m.cos(-_PI / 2 + sd * .9), cy + (ry + 10) * _m.sin(-_PI / 2 + sd * .9)
        F.stem(st_sweep(x1, y1, head - sd * .35, L * .8, -k * 1.5, k), 1.8, 1.)
    F.grow(10)
    F.fill(fx0 - 4, fy0 - 3, fx1 - fx0 + 8, fy1 - fy0 + 6, 4., hk.get("max_items", 260))
    o.append(_scroll_layer(F, f"s2m{w}x{h}", 0, 0, w, h, hk.get("egg"), 2))
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(f"s2m{w}x{h}v", fld, hk["field"](fld, "medium") + st_rim(fld, hk.get("rim", 9.))))
    if ded:
        o.append(st_dedication(cx, h - 3, 2 * ded))
    if hk.get("crest"):
        o.append(hk["crest"](cx, cy - ry - 2, min(14., ins + 4), "medium"))
    return "".join(o)


def st_pedestal(x, y, w, h, seed, hk, uid):
    """The base: knurled cornice, a frieze panel (gold-line border, fine scroll from the centre
    out) round a sunk tablet, a second knurled bar, beading. -> svg"""
    o = []
    kb = 6.
    o.append(_C.knurled_bar(x, y, w, kb))
    py0, py1 = y + kb + 1, y + h - kb - 5
    ph = py1 - py0
    tw, th = min(w * .5, 300.), ph - 10
    tx, ty = x + (w - tw) / 2, py0 + 5
    o.append(st_matte(st_rect_d(x, py0, w, ph)))

    def inside(px, py):
        return x + 6 < px < x + w - 6 and py0 + 2 < py < py1 - 2 and not (tx - 8 < px < tx + tw + 8)
    F = ScrollField(inside, rmin=max(4.5, ph * .16), rmax=ph * .4, seed=seed + 11, slack=.9)
    for sd in (-1, 1):
        xs = tx - 6 if sd < 0 else tx + tw + 6
        L = (w - tw) / 2 - 14
        pts = [(xs + sd * L * i / 30, py0 + ph / 2 + ph * .15 * _m.sin(i / 30 * _TAU * (L / (ph * 2)))) for i in range(31)]
        F.stem(pts, 1.4, .9, leaves=False)
    F.grow(6)
    F.fill(x + 6, py0 + 2, w - 12, ph - 4, 3., 120)
    o.append(_scroll_layer(F, uid + "p", x, py0, w, ph))
    o.append(st_wire(st_rect_d(x + 2.5, py0 + 1.5, w - 5, ph - 3)))
    o.append(f'<path d="{st_rect_d(tx - 3, ty - 3, tw + 6, th + 6)}" fill="#000"/>')
    o.append(st_beads(st_rect_d(tx - 1.5, ty - 1.5, tw + 3, th + 3), 3.5, 1.))
    o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="#fff" stroke="none"/>')
    if hk.get("tablet"):
        o.append(hk["tablet"](tx, ty, tw, th))
    elif hk.get("tablet_lines"):
        o.append(st_tablet_text(tx, ty, tw, th, hk["tablet_lines"]))
    else:
        o.append(f'<path d="{st_rect_d(tx, ty, tw, th)}" fill="url(#s2o)" stroke="none"/>')
    o.append(_C.knurled_bar(x + 4, py1, w - 8, kb))
    o.append(st_beads(f"M{_C._n(x + 3)},{_C._n(y + h - 2.5)}h{_C._n(w - 6)}", 3.5, 1.))
    return "".join(o)


def st_tall(w, h, seed, hk):
    """> 260: the full plate. The scene in a great inlaid medallion (an arched panel on a section
    front, like the binding) over a ribbon banner and the dedication cartouche with Parker's arms
    (placeholder); fine scroll grown from a stem rising either side of the arms packs the field;
    a pedestal; under it, when tall, a frieze of the same scroll."""
    o = [st_matte(st_rect_d(0, 0, w, h))]
    ins = 10.
    ped_h = min(max(h * .13, 40), 62.)
    fz = min(max(h * .09, 30), 50.) if (h >= 440 and hk.get("frieze", True)) else 0.
    py = h - ped_h - fz - ins * (1 if fz else .6)
    shape = hk.get("shape") or ("arch" if hk.get("arch") else "oval")
    arch = shape == "arch"
    rx = w * hk.get("cw", .3)
    top = ins + 12
    bot = py - (62 if py > 300 else 46)
    ry = (bot - top) / 2
    if shape == "roundel":
        rx = ry = min(rx * 1.25, ry)
        top = bot - 2 * ry
    cx, cy = w / 2, top + ry
    ph = (seed % 97) * .07
    ay = bot + 4
    ary = min(26., (py - ay) * .4)
    arx = ary * 1.25
    aby = py - ary - 8

    def inside(x, y):
        if not (ins - 4 < x < w - ins + 4 and ins - 3 < y < py - 3):
            return False
        if st_shape_in(shape, x, y, cx, cy, rx, ry, 13, ph):
            return False
        if abs(x - cx) < rx * 1.05 + 10 and bot - 4 < y < bot + 16:
            return False
        if _in_ell(x, y, cx, aby, arx + 10, ary + 9):
            return False
        return True
    F = ScrollField(inside, rmin=hk.get("rmin", 8.), rmax=min(hk.get("rmax", 30.), w * .058), seed=seed, slack=.88)
    for sd in (-1, 1):
        x0, y0 = cx + sd * (arx + 8), aby + ary * .3
        F.stem(st_sweep(x0, y0, (0. if sd > 0 else _PI) - sd * .25, (py - ins) * .55 + w * .1,
                        -sd * .004, -sd * .022), 3., 1.6)
        F.stem(st_sweep(cx + sd * (rx * .7), ins + 4, (0. if sd > 0 else _PI) + sd * .15, w * .3, sd * .004, sd * .02), 2.6, 1.4)
    F.grow(4)
    F.fill(ins - 4, ins - 3, w - 2 * ins + 8, py - ins, 6., hk.get("max_items", 340))
    uid = f"s2t{w}x{h}"
    o.append(_scroll_layer(F, uid, 0, 0, w, py, hk.get("egg"), 2))
    if fz:
        fy0 = py + ped_h + 2
        fh = h - ins - fy0

        def inside2(x, y):
            return ins - 4 < x < w - ins + 4 and fy0 < y < fy0 + fh and abs(x - w / 2) > fh * .7
        G = ScrollField(inside2, rmin=max(4.5, fh * .15), rmax=fh * .4, seed=seed + 5, slack=.9)
        for sd in (-1, 1):
            L = w / 2 - fh * .7 - 8
            G.stem([(w / 2 + sd * (fh * .7 + L * i / 40), fy0 + fh / 2 + fh * .17 * _m.sin(i / 40 * _TAU * (L / (fh * 2.1)))) for i in range(41)],
                   1.5, 1., leaves=False)
        G.grow(6)
        G.fill(ins - 4, fy0, w - 2 * ins + 8, fh, 4., 140)
        o.append(_scroll_layer(G, uid + "f", 0, fy0, w, fh, hk.get("egg2"), 1))
        cvp = _C.Canvas()
        _C.palmette(w / 2, fy0 + 1, fh * .8, False, seed, cv=cvp)
        o.append(cvp.svg())
    o.append(st_border(w, h))
    m, fld = st_shaped_medallion(shape, cx, cy, rx, ry, ph)
    o.append(m)
    o.append(f'<path d="{st_poly_d(fld)}" fill="#fff" stroke="none"/>')
    o.append(st_clip_poly(uid + "v", fld, hk["field"](fld, "tall") + st_rim(fld, hk.get("rim", 14.))))
    if hk.get("crest"):
        o.append(hk["crest"](cx, top - 3, top - 4, "tall"))
    bh = min(16., (py - bot) * .4)
    bs, centre = _C.ribbon_banner(cx, bot + 2, rx * 2.5, bh, .035, seed)
    o.append(bs)
    if hk.get("banner"):
        o.append(hk["banner"](centre, bh))
    elif hk.get("motto"):
        o.append(st_letter(hk["motto"], bh * .55, centre=centre[4:-4], fit=_m.dist(centre[4], centre[-5]) * .92))
    if hk.get("dedication"):
        o.append(st_arms(cx, aby, arx, ary))
    else:
        # not a front: a small inlaid cartouche carries the page's own device instead of the arms
        em, efl = st_medallion(cx, aby, arx * .78, ary * .78)
        o.append(em)
        o.append(f'<path d="{st_poly_d(efl)}" fill="url(#s2o)" stroke="none"/>')
        if hk.get("egg"):
            ecv = StCanvas()
            hk["egg"](ecv, cx, aby, ary * .62)
            o.append(ecv.svg())
    o.append(st_pedestal(0, py, w, ped_h, seed, hk, uid))
    return "".join(o)


def st_dissolve(poly, seed, depth=9., step=1.25):
    """Bewick's dissolving edge: white broken rings laid over the outer few px of a vignette, the
    white taking more of each ring toward the rim, so the cut lines crumble out into the paper."""
    rng = _rnd.Random(seed)
    n = int(depth / step)
    cx = sum(q[0] for q in poly) / len(poly)
    cy = sum(q[1] for q in poly) / len(poly)
    o = []
    for k in range(n):
        f = 1 - k / n                       # 1 at the rim, toward 0 inside
        g = k * step + .4
        ring = []
        for (x, y) in poly:
            dx, dy = x - cx, y - cy
            L = _m.hypot(dx, dy) or 1
            ring.append((x - dx / L * g, y - dy / L * g))
        segs = []
        for _ in range(4):
            on = rng.uniform(1, 5) * (.3 + 1.9 * f * f)
            off = rng.uniform(3, 9) * (1.3 - f)
            segs += [on, max(.3, off)]
        da = " ".join(_C._n(v) for v in segs)
        o.append(f'<path d="{st_poly_d(ring)}" fill="none" stroke="#fff" stroke-width="{_C._n(step + .25)}" '
                 f'stroke-dasharray="{da}" stroke-dashoffset="{_C._n(rng.uniform(0, 40))}"/>')
    o.append(f'<path d="{st_poly_d(poly)}" fill="none" stroke="#fff" stroke-width="2"/>')
    return "".join(o)


def st_vignette(w, h, seed, hk):
    """The free-standing vignette: the scene itself is the plate, cut to its shape and crumbling
    out into the paper at the rim; any ornament is drawn from the subject (hk['frame'])."""
    shape = hk.get("shape", "oval")
    pad = hk.get("pad", 2.)
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - pad, h / 2 - pad
    rx = min(rx, ry * hk.get("max_aspect", 3.2))
    ph = (seed % 97) * .07
    fld = hk["shape_fn"](cx, cy, rx, ry) if hk.get("shape_fn") else st_shape_pts(shape, cx, cy, rx, ry, 0., 160, ph)
    if shape == "irregular" and not hk.get("shape_fn"):
        s = max(max(abs(q[0] - cx) / (w / 2 - pad) for q in fld), max(abs(q[1] - cy) / (h / 2 - pad) for q in fld))
        fld = [(cx + (q[0] - cx) / s, cy + (q[1] - cy) / s) for q in fld]
    mode = "band" if h < 110 else ("medium" if h <= 260 else "tall")
    o = [f'<path d="{st_rect_d(0, 0, w, h)}" fill="#fff"/>']
    if hk.get("under"):
        o.append(hk["under"](cx, cy, rx, ry, fld, mode))
    o.append(st_clip_poly(f"s2v{w}x{h}", fld, hk["field"](fld, mode)))
    o.append(st_dissolve(fld, seed, hk.get("dissolve", min(7., 3 + min(w, h) * .025))))
    if hk.get("frame"):
        o.append(hk["frame"](cx, cy, rx, ry, fld, mode))
    if hk.get("dedication") and h >= 110:
        dh = min(30., h * .16)
        o.append(f'<path d="{st_ell_d(cx, h - dh / 2 - 1.5, dh * .62, dh * .55)}" fill="#fff"/>')
        o.append(st_dedication(cx, h - 1.5, dh))
    return "".join(o)


def st_plate(w, h, seed, hk):
    base = _C.Canvas
    if hk.get("vignette"):
        return _st_plate(w, h, seed, hk)
    _C.Canvas = StCanvas
    try:
        return _st_plate(w, h, seed, hk)
    finally:
        _C.Canvas = base


def _st_plate(w, h, seed, hk):
    if hk.get("vignette"):
        body = st_vignette(w, h, seed, hk)
    elif h <= 72 and w <= 110 and hk.get("device", True):
        body = st_device(w, h, seed, hk)
    elif h < 110:
        body = st_band(w, h, seed, hk)
    elif h <= 260:
        body = st_medium(w, h, seed, hk)
    else:
        body = st_tall(w, h, seed, hk)
    return st_doc(w, h, body)
# ==== END STUDIO LAYOUTS ========================================================================


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    hk = dict(vignette=True, pad=4., shape_fn=proscenium, frame=lambda cx, cy, rx, ry, fld, mode: tape_frame(cx, cy, rx, ry, fld, mode, seed),
              field=lambda fld, mode: trio(fld, mode, seed), egg=egg_cymbal, shape="irregular", dedication=True, cw=.27,
              aspect=1.9, rmin=9., rmax=30.,
              banner=swing_on_ribbon,
              tablet=lambda tx, ty, tw, th: keyboard(tx + 1, ty + 1, tw - 2, th - 2))
    return st_plate(w, h, seed, hk)
