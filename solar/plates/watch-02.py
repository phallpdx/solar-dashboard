"""watch-02 "Something to watch: new on streaming": the late-night set.

A mid-century walnut television, carved in the house relief, stands at the heart of the acanthus:
grain cut in bulino round two knots, a speaker grille and knurled channel knobs, splayed legs. On its
curved screen, ruled like scan lines, plays the page's picks by night: the "Midnight Diner" itself,
a little Tokyo izakaya with its noren curtain, paper lantern and kitchen steam, telegraph wires and
the city's rooftops under tonight's real moon (the "Nocturne"). Easter egg: the rabbit-ear antenna
is a pair of Parker's drumsticks, bead tips and all.
Tall plates add a ribbon of five engraved stars ("highly rated") and, in the pedestal tablet, a
streaming scrub bar with its play button. Short plates set a small set in the centre of a frieze.
"""
import sys
import math
import random
import engraving_codex as C

_d, _n, _ell = C._d, C._n, C._ell_pts
PI, TAU = math.pi, 2 * math.pi
CR = ' shape-rendering="crispEdges"'


# ------------------------------------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------------------------------------

def P(polys, fill="#fff", stroke="none", sw=None, extra=""):
    d = "".join(_d(p, True, .1) for p in polys if len(p) > 2)
    if not d:
        return ""
    s = f' stroke="{stroke}"' + (f' stroke-width="{sw}"' if sw else "")
    return f'<path d="{d}" fill="{fill}"{s}{extra}/>'


def PP(polys, fill, stroke="none", sw=None, extra=""):
    """Pattern fill over white (patterns are transparent between their lines)."""
    if str(fill).startswith("url("):
        return P(polys, "#fff") + P(polys, fill, stroke, sw, extra)
    return P(polys, fill, stroke, sw, extra)


def L(pls, sw=.5, color="#000", extra=""):
    d = "".join(_d(p, False, .15) for p in pls if len(p) > 1)
    if not d:
        return ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{extra}/>'


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _se(cx, cy, a, b, e=4., n=96):
    return C._superellipse(cx, cy, a, b, e, n)


def _span(poly, y):
    """x-intersections of a horizontal line with a polygon (sorted)."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 <= y < y1) or (y1 <= y < y0):
            xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return sorted(xs)


def _moon_phase(date):
    """0 new .. .5 full .. 1, from the ISO date (synodic month from a known new moon)."""
    try:
        y, m, d = (int(v) for v in date[:10].split("-"))
    except Exception:
        return .3
    import datetime
    days = (datetime.date(y, m, d) - datetime.date(2000, 1, 6)).days + .75
    return (days / 29.530589) % 1.


def _seed(ctx):
    return sum(map(ord, (ctx or {}).get("date", ""))) + 21


# ------------------------------------------------------------------------------------------------
# the picture on the screen: the Midnight Diner by night
# ------------------------------------------------------------------------------------------------

def _star(cx, cy, r, k=.42, rot=-PI / 2):
    return [(cx + (r if i % 2 == 0 else r * k) * math.cos(rot + PI * i / 5),
             cy + (r if i % 2 == 0 else r * k) * math.sin(rot + PI * i / 5)) for i in range(10)]


def picture(x, y, w, h, date, seed, cid):
    """Engraved night scene filling the box x,y,w,h (drawn under a clipPath id cid)."""
    rng = random.Random(seed)
    o = []
    small = h < 40
    # sky: deep ruled, lightening toward the horizon in two steps (scan lines)
    o.append(PP([_rect(x, y, w, h)], C.pat("G")))
    gy = y + h * .84                          # street line
    hz = y + h * .56
    o.append(f'<path d="M{_n(x)},{_n(hz - h * .06)}h{_n(w)}v{_n(h * .5)}h{_n(-w)}z" fill="#fff"/>')
    o.append(f'<path d="M{_n(x)},{_n(hz - h * .06)}h{_n(w)}v{_n(h * .5)}h{_n(-w)}z" fill="{C.pat("M")}"/>')
    # stars
    if not small:
        st = []
        for i in range(int(w * h / 900) + 4):
            sx, sy = x + rng.uniform(.04, .96) * w, y + rng.uniform(.05, .42) * h
            r = rng.choice((1., 1., 1.5, 2.))
            st.append([(sx - r, sy), (sx + r, sy)])
            st.append([(sx, sy - r), (sx, sy + r)])
        o.append(L(st, 1 if small else .5, "#fff"))
    # moon, real phase
    ph = _moon_phase(date)
    mr = max(3.5, h * .13)
    mx, my = x + w * .80, y + h * .2
    o.append(P([_ell(mx, my, mr + 1.5, mr + 1.5, 40)[:-1]], C.pat("M")))          # a faint halo
    o.append(PP([_ell(mx, my, mr, mr, 40)[:-1]], C.pat("M")))     # earthshine
    k = math.cos(TAU * ph)
    s = 1 if ph < .5 else -1
    if abs(ph - 0) > .03 and abs(ph - 1) > .03:
        lim = [(mx + s * mr * math.cos(t), my + mr * math.sin(t)) for t in [(-PI / 2 + PI * i / 24) for i in range(25)]]
        ter = [(mx + s * mr * k * math.cos(t), my + mr * math.sin(t)) for t in [(PI / 2 - PI * i / 24) for i in range(25)]]
        lit = lim + ter
        o.append(P([lit], "#fff"))
        o.append(P([lit], C.pat("L")))
        if mr > 6 and .3 < ph < .7:
            cr = []
            for (u, v, rr) in ((.25, -.3, .22), (-.2, .25, .17), (.35, .35, .12), (-.35, -.1, .1)):
                cx2, cy2 = mx + u * mr, my + v * mr
                # only craters on the lit side
                if (cx2 - mx) * s > -mr * k * math.sqrt(max(0., 1 - (v) ** 2)) * 1.0 + 1:
                    cr.append(_ell(cx2, cy2, rr * mr, rr * mr * .85, 14))
            o.append(L(cr, .5))
    # telegraph pole and sagging wires
    if not small:
        pxl = x + w * .12
        o.append(L([[(pxl, gy + 1), (pxl, y + h * .14)]], 1.5))
        o.append(L([[(pxl - 6, y + h * .19), (pxl + 6, y + h * .19)], [(pxl - 4.5, y + h * .25), (pxl + 4.5, y + h * .25)]], 1))
        wires = []
        for j, (yy, sag) in enumerate(((.19, .07), (.25, .09), (.19, .12))):
            x0, y0 = pxl + (6 if j != 1 else 4.5) * (1 if j < 2 else -1), y + h * yy
            x1 = x + w + 2 if j < 2 else x - 2
            y1 = y + h * (yy + .06)
            wires.append([(x0 + (x1 - x0) * t / 20, y0 + (y1 - y0) * t / 20 + h * sag * math.sin(PI * t / 20)) for t in range(21)])
        o.append(L(wires, .5))
    # far rooftops: a black silhouette of the city, lit windows cut in white
    rx = x - 2
    sky = [(x - 2, gy)]
    wins = []
    signs = []
    while rx < x + w + 2:
        bw = rng.uniform(.07, .14) * w
        bh = h * rng.uniform(.14, .30)
        top = gy - bh
        if rng.random() < .3:            # a pitched roof
            sky += [(rx, top + 3), (rx + bw / 2, top - 2), (rx + bw, top + 3)]
        else:
            sky += [(rx, top), (rx + bw, top)]
        if not small:
            for wy in range(int(top + 4), int(gy - h * .25), 4):
                for wx in range(int(rx + 2), int(rx + bw - 3), 4):
                    if rng.random() < .25:
                        wins.append(_rect(wx, wy, 1.5, 1.5))
            if rng.random() < .35 and bw > 10:
                sx0 = rx + bw * .7
                signs.append((sx0, top + 3, min(4., bw * .25), min(bh * .6, h * .22)))
        rx += bw
    sky += [(x + w + 2, gy)]
    o.append(P([sky], "#000"))
    if wins:
        o.append(P(wins, "#fff"))
    for (sx0, sy0, sw0, sh0) in signs:          # vertical shop signs (tategaki), lit
        o.append(P([_rect(sx0, sy0, sw0, sh0)], "#fff", "#000", ".5"))
        o.append(L([[(sx0 + sw0 / 2, sy0 + 1.5 + j * 3), (sx0 + sw0 / 2, sy0 + 2.5 + j * 3)] for j in range(int((sh0 - 2) / 3))], 1))
    # the diner
    dw, dh = w * .40, h * .36
    dx, dy = x + w * .46 - dw / 2, gy - dh
    # neighbouring two-storey houses, cross-hatched, with lit upper windows
    for sd in (-1, 1):
        nbw = w * .2
        nbx = dx - nbw + 2 if sd < 0 else dx + dw - 2
        nbh = dh * (1.35 if sd < 0 else 1.15)
        nb = _rect(nbx, gy - nbh, nbw, nbh)
        o.append(PP([nb], C.pat("X" if sd < 0 else "D"), "#000", ".5"))
        o.append(L([[(nbx - 1.5, gy - nbh), (nbx + nbw + 1.5, gy - nbh)]], 1.5))
        ww = []
        for i in range(3):
            wx0 = nbx + nbw * (.12 + .3 * i)
            ww.append(_rect(wx0, gy - nbh * .82, nbw * .18, nbh * .2))
        o.append(P(ww, "#fff", "#000", ".5"))
        o.append(L([[(r[0][0] + (r[1][0] - r[0][0]) / 2, r[0][1]), (r[0][0] + (r[1][0] - r[0][0]) / 2, r[2][1])] for r in ww], .5))
        if sd < 0 and not small:   # a lit vertical sign on the corner
            sgx, sgw = nbx + nbw - 5, 4
            o.append(P([_rect(sgx, gy - nbh * .55, sgw, nbh * .45)], "#fff", "#000", ".5"))
            o.append(L([[(sgx + 2, gy - nbh * .55 + 2 + j * 3), (sgx + 2, gy - nbh * .55 + 3 + j * 3)] for j in range(int((nbh * .45 - 3) / 3))], 1))
    o.append(PP([_rect(dx, dy, dw, dh)], C.pat("V"), "#000", ".5"))          # slatted wood front
    ev = h * .08                                                            # eave
    eave = [(dx - dw * .12, dy + ev * .35), (dx + dw * .08, dy - ev), (dx + dw * .92, dy - ev), (dx + dw * 1.12, dy + ev * .35)]
    o.append(PP([eave], C.pat("X"), "#000", "1"))
    o.append(L([[(dx - dw * .12, dy + ev * .35 + .5), (dx + dw * 1.12, dy + ev * .35 + .5)]], 1.5))
    # doorway glowing from inside
    door = _rect(dx + dw * .25, dy + dh * .22, dw * .5, dh * .78)
    o.append(PP([door], C.pat("L"), "#000", "1"))
    if not small:
        # counter and two stools in silhouette inside
        cx0, cw0 = door[0][0], dw * .5
        o.append(P([_rect(cx0, gy - dh * .34, cw0, dh * .07)], "#000"))
        for f in (.3, .7):
            o.append(L([[(cx0 + cw0 * f, gy - dh * .27), (cx0 + cw0 * f, gy)]], 1))
            o.append(L([[(cx0 + cw0 * f - 2, gy - dh * .27), (cx0 + cw0 * f + 2, gy - dh * .27)]], 1.5))
    # noren: three panels hanging from the top of the door, a black mon on the centre one
    nx0, ny0 = door[0][0] - 1, door[0][1]
    nw, nh = dw * .5 + 2, dh * .36
    pan = []
    for i in range(3):
        px0 = nx0 + nw * i / 3 + .5
        pan.append([(px0, ny0), (px0 + nw / 3 - 1, ny0), (px0 + nw / 3 - 1, ny0 + nh), (px0, ny0 + nh)])
    o.append(P(pan, "#fff", "#000", ".5"))
    o.append(L([[(nx0 + nw * (i + .5) / 3, ny0 + 1), (nx0 + nw * (i + .5) / 3, ny0 + nh - 1)] for i in (0, 2)], .5))
    mon = min(nw / 3, nh) * .28
    o.append(P([_ell(nx0 + nw / 2, ny0 + nh * .5, mon, mon, 16)[:-1]], "#000"))
    o.append(L([[(nx0 - 1, ny0 - .5), (nx0 + nw + 1, ny0 - .5)]], 1))
    # paper lantern (akachochin) at the right of the door, glowing
    lx, ly = dx + dw * .88, dy + dh * .38
    lr, lh = max(2.2, dw * .07), max(3., dh * .2)
    lan = _ell(lx, ly, lr, lh, 24)[:-1]
    if not small:
        rays = []
        for i in range(14):
            a = TAU * i / 14
            rays.append([(lx + (lr + 2) * math.cos(a), ly + (lh + 2) * math.sin(a)),
                         (lx + (lr + 4.5) * math.cos(a), ly + (lh + 4.5) * math.sin(a))])
        o.append(L(rays, .5, "#fff"))
    o.append(P([lan], "#fff", "#000", ".5"))
    ribs = [[(lx + lr * math.sqrt(max(0., 1 - (t / lh) ** 2)) * u, ly + t) for u in (-1, 1)]
            for t in [lh * (-.66 + .33 * j) for j in range(5)]]
    o.append(L(ribs, .5))
    o.append(L([[(lx - lr * .6, ly - lh), (lx + lr * .6, ly - lh)], [(lx - lr * .6, ly + lh), (lx + lr * .6, ly + lh)]], 1.5))
    o.append(L([[(lx, ly - lh), (lx, dy + ev * .35)]], .5))
    # kitchen steam from a vent pipe on the roof
    vx = dx + dw * .2
    o.append(L([[(vx, dy - ev + .5), (vx, dy - ev - h * .06)]], 1.5))
    if not small:
        steam = []
        for j in range(2):
            x0 = vx + j * 3 - 1
            steam.append([(x0 + 2.2 * math.sin(t * .5 + j), dy - ev - h * .07 - t * 1.2) for t in range(int(h * .18))])
        o.append(L(steam, 1, "#fff"))
    # wet street with the doorway's reflection
    o.append(PP([_rect(x - 2, gy, w + 4, y + h - gy + 2)], C.pat("G")))
    rf = []
    for j, yy in enumerate(range(int(gy + 2), int(y + h), 2)):
        ww = dw * .5 * (1 - .12 * j)
        if ww <= 1:
            break
        cxr = dx + dw / 2 + rng.uniform(-1.5, 1.5)
        rf.append([(cxr - ww / 2, yy + .25), (cxr - ww / 2 + ww * .4, yy + .25)])
        rf.append([(cxr - ww / 2 + ww * .55, yy + .25), (cxr + ww / 2, yy + .25)])
        lxr = lx + rng.uniform(-1, 1)
        rf.append([(lxr - 1.5, yy + .25), (lxr + 1.5, yy + .25)])
    o.append(L(rf, .5, "#fff", CR))
    o.append(L([[(x - 2, gy), (x + w + 2, gy)]], 1))
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# the television set
# ------------------------------------------------------------------------------------------------

def _grain(poly, y0, y1, seed, pitch=2.):
    """Walnut grain: wavy lines across poly, swirling round two knots."""
    rng = random.Random(seed)
    xs = [p[0] for p in poly]
    X0, X1 = min(xs), max(xs)
    knots = [(X0 + (X1 - X0) * rng.uniform(.15, .4), y0 + (y1 - y0) * rng.uniform(.3, .7), rng.uniform(3, 5)),
             (X0 + (X1 - X0) * rng.uniform(.6, .88), y0 + (y1 - y0) * rng.uniform(.25, .75), rng.uniform(2.5, 4))]
    out = []
    y = y0 + 1.25
    row = 0
    ph = rng.uniform(0, 6)
    while y < y1 - 1:
        sp = _span(poly, y)
        for j in range(0, len(sp) - 1, 2):
            a, b = sp[j] + 1.2, sp[j + 1] - 1.2
            if b - a < 2:
                continue
            pts = []
            n = max(2, int((b - a) / 2.5))
            for i in range(n + 1):
                xx = a + (b - a) * i / n
                dy = .5 * math.sin(xx * .045 + row * .21 + ph) + .3 * math.sin(xx * .13 - row * .4)
                for kx, ky, kr in knots:
                    ddx, ddy = xx - kx, y - ky
                    g = math.exp(-(ddx * ddx) / (2 * (kr * 3) ** 2))
                    if abs(ddy) < kr * 3.2:
                        dy += math.copysign(kr * .9, ddy if ddy else 1) * g * (1 - abs(ddy) / (kr * 3.2))
                pts.append((xx, y + dy))
            out.append(pts)
        y += pitch
        row += 1
    rings = []
    for kx, ky, kr in knots:
        for f in (.35, .7):
            rings.append(_ell(kx, ky, kr * 2.2 * f + .6, kr * f + .4, 18))
    return out, rings


def _drumstick(cx, cy, ang, length, wb):
    """A drumstick from its butt at (cx, cy) along ang: tapered shaft, shoulder, bead tip.
    Returns (shaft polygon, bead polygon, grain lines, shadow line, bead centre)."""
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    L_ = length

    def at(t, s):
        return (cx + ux * t + vx * s, cy + uy * t + vy * s)

    def hw(t):
        u = t / L_
        if u < .7:
            return wb / 2
        return wb / 2 * (1 - .62 * C._smooth(.7, .97, u))

    ts = [L_ * i / 30 for i in range(31)]
    left = [at(t, hw(t)) for t in ts]
    right = [at(t, -hw(t)) for t in ts[::-1]]
    shaft = left + right
    br = wb * .62
    bc = at(L_ + br * .7, 0)
    bead = [(bc[0] + ux * br * 1.25 * math.cos(a) + vx * br * math.sin(a),
             bc[1] + uy * br * 1.25 * math.cos(a) + vy * br * math.sin(a)) for a in [TAU * i / 20 for i in range(20)]]
    grain = [[at(t, wb * .12) for t in ts[2:20]], [at(t, -wb * .05) for t in ts[6:26]]]
    shade = [at(t, -hw(t) * .62) for t in ts[1:29]]
    return shaft, bead, grain, shade, bc


def tv_set(cx, top, W, H, seed, date, legs=0., antenna=0., uid="tv", detail=True):
    """The set: cabinet W x H whose top edge is at `top`, centred on cx; legs (px) below it,
    drumstick antennas (px) above. Returns (svg, screen centre)."""
    rng = random.Random(seed)
    o = []
    bot = top + H
    cy = top + H / 2
    # --- antennas behind the cabinet top (drumsticks!)
    if antenna > 8:
        bx, by = cx + W * .16, top + 1
        dr = max(4., W * .055)
        for a in (-PI / 2 - .55, -PI / 2 + .42):
            length = min(antenna / abs(math.sin(a)) - dr * 1.6, W * .62)
            shaft, bead, grain, shade, bc = _drumstick(bx, by - dr * .4, a, length, max(3., W * .034))
            o.append(P([shaft], "#fff", "#000", "1"))
            o.append(L(grain, .5))
            o.append(L([shade], 1))
            o.append(P([bead], "#fff", "#000", "1"))
            o.append(L([[(bc[0] + .5, bc[1] + 1), (bc[0] + 1.2, bc[1] + .2)]], 1))
        dome = _ell(bx, by, dr * 1.25, dr, 24, PI, TAU)
        o.append(P([dome + [(bx + dr * 1.25, by), (bx - dr * 1.25, by)]], "#fff", "#000", "1"))
        arcs = [_ell(bx, by, dr * 1.25 * f, dr * f, 16, PI * 1.05, TAU * .97) for f in (.45, .7)]
        o.append(L(arcs, .5))
        o.append(P([_ell(bx + dr * .45, by - dr * .35, dr * .5, dr * .55, 12, -PI * .45, PI * .55)], "#000"))
    # --- legs
    if legs > 4:
        lp = []
        shade = []
        for s in (-1, 1):
            lx0 = cx + s * W * .34
            lw0, lw1 = max(3., W * .03), max(1.6, W * .014)
            lx1 = lx0 + s * legs * .32
            leg = [(lx0 - lw0, bot - 2), (lx0 + lw0, bot - 2), (lx1 + lw1, bot + legs - 2), (lx1 - lw1, bot + legs - 2)]
            lp.append(leg)
            shade.append([(lx0 + lw0 * .4 * s, bot), (lx1 + lw1 * .4 * s, bot + legs - 3)])
            shade.append([(lx0 - lw0 * .2 * s, bot), (lx1 - lw1 * .2 * s, bot + legs - 3)])
            o.append(P([[(lx1 - lw1 - .4, bot + legs - 4), (lx1 + lw1 + .4, bot + legs - 4), (lx1 + lw1 + .4, bot + legs), (lx1 - lw1 - .4, bot + legs)]], "#000"))
        o.append(P(lp, "#fff", "#000", "1"))
        o.append(L(shade, .5))
        # shadow cast on the ground under the set
    # --- cabinet
    cab = _se(cx, cy, W / 2, H / 2, 6., 120)
    o.append(P([_se(cx + 1.5, cy + 2, W / 2, H / 2, 6., 96)], "#000"))              # cast shadow
    o.append(P([cab], "#fff"))
    gl, rings = _grain(cab, top, bot, seed)
    o.append(L(gl + rings, .5))
    # volume: cross-hatch the lower third and the right end, solid shadow along the bottom
    lower = [p for p in cab if p[1] > cy + H * .18]
    if len(lower) > 3:
        o.append(L(C.hatch_poly(lower, 45, 3), .5))
    rend = [p for p in cab if p[0] > cx + W * .44]
    if len(rend) > 3:
        o.append(L(C.hatch_poly(rend, -45, 3), .5))
    o.append(L([[p for p in _se(cx, cy, W / 2 - 1.2, H / 2 - 1.2, 6., 120) if p[1] > cy + H * .44 and abs(p[0] - cx) < W * .47]], 1.5))
    o.append(P([cab], "none", "#000", "1.5"))
    # top highlight (a turned edge)
    o.append(L([[p for p in _se(cx, cy, W / 2 - 2.5, H / 2 - 2.5, 6., 120) if p[1] < cy - H * .44 and abs(p[0] - cx) < W * .45]], .5))
    # --- screen bezel and tube
    sw = W * .63
    sx = cx - W / 2 + W * .055 + sw / 2
    sh = H * .78
    sy = cy - H * .01
    bw = max(3., H * .05)
    outer = _se(sx, sy, sw / 2 + bw, sh / 2 + bw, 4.2)
    inner = _se(sx, sy, sw / 2, sh / 2, 3.4)
    o.append(P([outer], "#fff", "#000", "1"))
    rl = [(_se(sx, sy, sw / 2 + bw * f, sh / 2 + bw * f, 4.2 - .8 * (1 - f)) + []) for f in (.35, .62, .85)]
    o.append(L([r + [r[0]] for r in rl], .5))
    o.append(L(C.hatch_poly([p for p in outer if p[0] < sx - sw * .1 or p[1] > sy + sh * .3], 45, 3), .5) if False else "")
    # picture, clipped to the tube
    cid = C._uid(uid, W, H, seed)
    pic = picture(sx - sw / 2, sy - sh / 2, sw, sh, date, seed, cid)
    o.append(f'<clipPath id="{cid}"><path d="{_d(inner, True, .1)}"/></clipPath><g clip-path="url(#{cid})">{pic}'
             # the tube's dark curved rim and a glare on its glass
             f'{P([_se(sx, sy, sw / 2 + 2, sh / 2 + 2, 3.4), _se(sx, sy, sw / 2 - 1.5, sh / 2 - 1.5, 3.4)[::-1]], "#000")}'
             f'</g>')
    gl_pts = _ell(sx - sw * .22, sy - sh * .22, sw * .22, sh * .2, 20, PI * 1.05, PI * 1.45)
    o.append(L([gl_pts], 1, "#fff"))
    o.append(P([inner], "none", "#000", "1"))
    # --- control panel to the right of the tube
    px0 = sx + sw / 2 + bw + W * .03
    px1 = cx + W / 2 - W * .05
    pw = px1 - px0
    if pw > 8:
        py0, py1 = top + H * .12, bot - H * .12
        panel = _se((px0 + px1) / 2, (py0 + py1) / 2, pw / 2, (py1 - py0) / 2, 5.)
        o.append(PP([panel], C.pat("M"), "#000", "1"))
        # speaker grille: vertical cloth over two thirds
        gx0, gx1 = px0 + pw * .14, px1 - pw * .14
        gy0, gy1 = py0 + (py1 - py0) * .07, py0 + (py1 - py0) * .45
        grille = _se((gx0 + gx1) / 2, (gy0 + gy1) / 2, (gx1 - gx0) / 2, (gy1 - gy0) / 2, 4.)
        o.append(PP([grille], C.pat("V"), "#000", ".5"))
        o.append(L([[((gx0 + gx1) / 2 - (gx1 - gx0) * .38, yy), ((gx0 + gx1) / 2 + (gx1 - gx0) * .38, yy)]
                    for yy in [gy0 + (gy1 - gy0) * f for f in (.25, .5, .75)]], 1))
        # two knurled knobs: channel above volume
        kr = min(pw * .3, (py1 - gy1) * .2)
        ks = []
        for j, f in enumerate((.36, .74)):
            kx, ky = (px0 + px1) / 2, gy1 + (py1 - gy1) * f
            ks.append((kx, ky))
            o.append(P([_ell(kx + .8, ky + 1.2, kr + .8, kr + .8, 28)[:-1]], "#000"))
            o.append(P([_ell(kx, ky, kr, kr, 28)[:-1]], "#fff", "#000", "1"))
            nt = max(10, int(kr * TAU / 2.2))
            ticks = [[(kx + kr * .72 * math.cos(TAU * i / nt), ky + kr * .72 * math.sin(TAU * i / nt)),
                      (kx + kr * .98 * math.cos(TAU * i / nt), ky + kr * .98 * math.sin(TAU * i / nt))] for i in range(nt)]
            o.append(L(ticks, .5))
            o.append(P([_ell(kx, ky, kr * .45, kr * .45, 16)[:-1]], C.pat("D"), "#000", ".5"))
            a = -PI / 2 + (rng.uniform(-1.2, 1.2) if j else .9)
            o.append(L([[(kx, ky), (kx + kr * .62 * math.cos(a), ky + kr * .62 * math.sin(a))]], 1.5))
            o.append(P([_ell(kx + kr * .35, ky + kr * .1, kr * .55, kr * .7, 14, -PI * .25, PI * .6)], "none", "#000", "1") if kr > 5 else "")
        # channel scale round the upper knob
        if detail and kr > 3.5:
            kx, ky = ks[0]
            sc = [[(kx + (kr + 1.5) * math.cos(a), ky + (kr + 1.5) * math.sin(a)),
                   (kx + (kr + (3.5 if i % 3 == 0 else 2.5)) * math.cos(a), ky + (kr + (3.5 if i % 3 == 0 else 2.5)) * math.sin(a))]
                  for i, a in enumerate(-PI * 1.25 + PI * 1.5 * i / 12 for i in range(13))]
            o.append(L(sc, .5))
    return "".join(o), (sx, sy, sw, sh)


# ------------------------------------------------------------------------------------------------
# lettering-free tokens for banner and tablet
# ------------------------------------------------------------------------------------------------

def _banner_stars(centre, hh):
    n = len(centre)
    o = []
    rows = "".join(_d([(px, py + off) for px, py in centre[1:-1]], tol=.1) for off in (-hh * .62, hh * .62))
    o.append(f'<path d="{rows}" stroke="#000" stroke-width=".5" fill="none"/>')
    stars = []
    dots = []
    for i in range(5):
        px, py = centre[int(n * (.3 + .1 * i))]
        stars.append(_star(px, py, hh * .55))
    for f in (.18, .22, .78, .82):
        px, py = centre[int(n * f)]
        dots.append(_ell(px, py, .9, .9, 8)[:-1])
    o.append(P(stars, "#000"))
    o.append(P(dots, "#000"))
    # a little hatch to warm the plain face between the rules
    lines = []
    for j in range(1, n - 2):
        if .25 < j / n < .75:
            continue
        px, py = centre[j]
        lines.append([(px, py - hh * .45), (px, py + hh * .45)])
    o.append(L(lines[::2], .5))
    return "".join(o)


def _scrub_bar(tx, ty, tw, th, seed):
    """A streaming player's controls engraved in the tablet: play button, scrub bar, ticks."""
    o = [PP([_rect(tx + 2, ty + 2, tw - 4, th - 4)], C.pat("L"))]
    cy = ty + th / 2
    pr = min(th * .32, 9)
    pcx = tx + pr + 8
    o.append(P([_ell(pcx, cy, pr, pr, 28)[:-1]], "#fff", "#000", "1"))
    o.append(P([[(pcx - pr * .35, cy - pr * .5), (pcx + pr * .55, cy), (pcx - pr * .35, cy + pr * .5)]], "#000"))
    bx0, bx1 = pcx + pr + 8, tx + tw - 10
    bh = max(2.5, th * .14)
    prog = .62
    o.append(P([_rect(bx0, cy - bh / 2, bx1 - bx0, bh)], "#fff", "#000", ".5"))
    o.append(P([_rect(bx0, cy - bh / 2, (bx1 - bx0) * prog, bh)], "#000"))
    o.append(P([_rect(bx0 + (bx1 - bx0) * prog, cy - bh / 2 + .5, (bx1 - bx0) * .14, bh - 1)], C.pat("D")))
    kx = bx0 + (bx1 - bx0) * prog
    o.append(P([_ell(kx, cy, bh * 1.1, bh * 1.1, 18)[:-1]], "#fff", "#000", "1"))
    ticks = [[(bx0 + (bx1 - bx0) * i / 10, cy + bh), (bx0 + (bx1 - bx0) * i / 10, cy + bh + (2.5 if i % 5 == 0 else 1.5))] for i in range(11)]
    o.append(L(ticks, .5))
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts
# ------------------------------------------------------------------------------------------------

def _paper(w, h):
    return f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>'


def _layout_band(w, h, seed, date):
    o = [_paper(w, h)]
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh + 2), "G"))
    H = gh - 6
    W = H * 1.6
    gap = W + 18
    o.append(C._clip(C._uid("b", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap, r_scale=1.15 * max(1., 62. / gh))))
    tv, _ = tv_set(w / 2, top + 3, W, H, seed, date, 0, 0, "tvb", detail=gh > 60)
    o.append(tv)
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed, date, density=1.):
    rng = random.Random(seed)
    o = [_paper(w, h)]
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    legs = gh * .1
    H = gh * .6
    W = min(H * 1.55, w * .42)
    H = W / 1.55
    ant = gh - H - legs - 3
    top = gy1 - legs - H
    cx = w / 2
    occ = [("r", cx - W / 2 - 2, top - 4, cx + W / 2 + 2, gy1), ("r", cx - W * .25, gy0, cx + W * .45, top)]
    r = min(gh * .46, (w - W) / 4.1)
    cv = C.Canvas()
    main = C.Canvas()
    for side in (-1, 1):
        vx = cx + side * (W / 2 + r * 1.02)
        vy = gy0 + gh * .5
        C._pair_unit(main, vx, vy, r, side, random.Random(seed * 3 + side), 0, 1.4, .9, True)
        occ.append(("c", vx + side * r * .1, vy, r * .95))
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=int(8 * density), edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    tv, _ = tv_set(cx, top, W, H, seed, date, legs, ant, "tvm")
    o.append(tv)
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _layout_tall(w, h, seed, date, density=1.):
    rng = random.Random(seed)
    o = [_paper(w, h)]
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if (h >= 440 and density >= .9) else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 2)},{_n(py0 - 2)}h{_n(pw + 4)}v{_n(ph + 4)}h{_n(-pw - 4)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    W = min(pw * .56, ph * .56 * 1.5)
    H = W / 1.5
    cx = w / 2
    legs = min(ph * .09, 30)
    top = py0 + ph * .5 - H / 2 - legs * .2
    ant = top - py0 + top_free * .6
    bot = top + H
    occ = [("r", cx - W / 2 - 4, top - 4, cx + W / 2 + 4, bot + legs), ("r", cx - W * .05, top - W * .2, cx + W * .4, top)]
    cv = C.Canvas()
    main = C.Canvas()
    r1 = min(pw * .18, ph * .25)
    for side in (-1, 1):
        vx = cx + side * (W * .5 + r1 * .75)
        vy = py0 + ph - r1 * 1.1
        C._pair_unit(main, vx, vy, r1, side, random.Random(seed * 5 + side), 10, 1.45, .8, True)
        occ.append(("c", vx, vy, r1))
    r2 = min(pw * .15, ph * .21)
    for side in (-1, 1):
        vx = cx + side * (W * .5 + r2 * .75)
        vy = py0 + r2 * 1.1
        C._pair_unit(main, vx, vy, r2, side, random.Random(seed * 7 + side), -10, 1.4, .8, False)
        occ.append(("c", vx, vy, r2))
    C.fill_scrolls(px0, py0, pw, ph, occ, rng.randrange(1 << 20), rmin=max(12, ph * .045), rmax=r1 * .9,
                   max_n=int(9 * density), edge=.6, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    tv, _ = tv_set(cx, top, W, H, seed, date, legs, ant, "tvt")
    o.append(tv)
    bh = min(16, ph * .05)
    by = min(bot + legs + bh * .9, py0 + ph - bh)
    bsvg, centre = C.ribbon_banner(cx, by, W * 1.25, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(_banner_stars(centre, bh / 2))
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_scrub_bar(tx + 1, ty + 1, tw - 2, th - 2, seed))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = _seed(ctx)
    date = ctx.get("date", "2026-11-11")
    if h < 110:
        body = _layout_band(w, h, seed, date)
    elif h <= 260:
        body = _layout_medium(w, h, seed, date)
    else:
        body = _layout_tall(w, h, seed, date)
    return C.svg_doc(w, h, body)
