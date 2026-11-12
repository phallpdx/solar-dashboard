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


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7
    if h < 110:
        kind = "band"
    elif h <= 260:
        kind = "medium"
    else:
        kind = "tall"

    def fill(x, y, bw, bh):
        cx, cy = x + bw / 2, y + bh / 2
        if kind == "band":
            fld = _ell(cx, cy, bw / 2 / .7071 + 3, bh / 2 / .7071 + 3, 64)[:-1]
        else:
            k = 2 ** (-1 / 2.6)
            fld = C._superellipse(cx, cy, bw / 2 / k + 6.6, bh / 2 / k + 6.6)
        return vignette(fld, kind, seed)

    if kind == "medium":
        return C.svg_doc(w, h, _medium(w, h, seed, fill))
    svg = C.frame_plate(w, h, seed, fill, .9 if kind == "tall" else 1.)
    if kind == "tall":
        svg = svg[:-6] + _tall_overlays(w, h) + "</svg>"
    return svg
