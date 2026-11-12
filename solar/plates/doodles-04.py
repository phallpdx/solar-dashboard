"""doodles-04 "Your bookshelf": a reader's desk at candle-light, engraved inside the house cartouche.
Shelves of modelled spines behind; an open book (drop-cap P on the left page, a tiny Mt. Hood plate
on the right) on a grained desk beside a stack of books and a candle whose glow is cut as a
sunburst; a spider (Tchaikovsky's) drops on its thread into the light. Tall plates add a pedestal
tablet engraved with 40 tally strokes (40 books to read)."""
import sys
import math
import random
import engraving_codex as C

_n, _d = C._n, C._d
PI = math.pi


def _lerp(p, q, f):
    return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)


# ------------------------------------------------------------------ pieces of the scene

def _spine(cv, x, yb, sw, sh, tilt, rng, tone):
    """A book standing on its tail at (x, yb), width sw, height sh, leaning by tilt (rad, + to the right
    about its lower right corner when tilt > 0 else lower left)."""
    ca, sa = math.cos(tilt), math.sin(tilt)
    px = x + sw if tilt > 0 else x

    def P(u, v):  # u across 0..1, v up 0..1
        lx, ly = x + u * sw - px, -v * sh
        return (px + lx * ca - ly * sa, yb + lx * sa + ly * ca)
    poly = [P(0, 0), P(1, 0), P(1, 1), P(0, 1)]
    cv.obj([poly], 1.)
    # rounded spine: dense rules at both edges, a highlight just left of centre
    us = []
    u = .5 / sw
    while u < 1:
        us.append(u)
        if u < .22:
            step = 1.5
        elif u < .42:
            step = 3. if tone < 2 else 2.
        elif u < .58:
            step = 4.5 if tone == 0 else 2.
        elif u < .75:
            step = 2.
        else:
            step = 1.5
        u += step / sw
    for u in us:
        if tone == 0 and .44 < u < .56:
            continue
        cv.hair([P(u, .02), P(u, .98)])
    # head and tail bands, and raised cords
    for v in (.08, .11, .89, .92):
        cv.line([P(0, v), P(1, v)])
    if sh > 18 and rng.random() < .7:
        for v in (.3, .55):
            cv.hair([P(0, v), P(1, v)])
            cv.hair([P(0, v + .025), P(1, v + .025)])
    if tone == 2:  # dark morocco: cross rules
        v = .13
        while v < .87:
            cv.hair([P(0, v), P(1, v)])
            v += 2. / sh
    if sw > 6 and sh > 16 and rng.random() < .6:  # title label
        lab = [P(.18, .64), P(.82, .64), P(.82, .78), P(.18, .78)]
        cv.obj([lab], .5)
        cv.hair([P(.3, .71), P(.7, .71)])
    return poly


def _shelf_row(cv, x0, x1, yb, rh, rng, lean_ok=True):
    x = x0 + rng.uniform(-3, 0)
    while x < x1:
        sw = rng.choice((4.5, 5.5, 6., 7., 8., 9.5))
        sh = rh * rng.uniform(.62, .92)
        tone = rng.choice((0, 0, 1, 1, 2))
        if lean_ok and rng.random() < .07 and x + sw * 2 < x1:
            _spine(cv, x, yb, sw, sh * .95, .32, rng, tone)
            x += sw + sh * .95 * math.sin(.32) + .5
            continue
        _spine(cv, x, yb, sw, sh, 0., rng, tone)
        x += sw + rng.choice((0., 0., .5, 1.))


def _board(cv, x0, x1, y, t=4.):
    poly = [(x0, y), (x1, y), (x1, y + t), (x0, y + t)]
    cv.obj([poly], 1.)
    cv.hair([(x0, y + 1.5), (x1, y + 1.5)])
    cv.hair([(x0, y + 3), (x1, y + 3)])
    cv.heavy([(x0, y + t + .7), (x1, y + t + .7)])


def _halo(cv, fx, fy, R, rng):
    """Candle glow: the ruled ground thins out toward the flame, and short rays burst from it."""
    disc = C._ell_pts(fx, fy, R, R, 56)
    cv.obj([disc], 0)
    y = fy - R + .75
    k = 0
    while y < fy + R:
        dy = abs(y - fy)
        half = math.sqrt(max(0., R * R - dy * dy))
        lev = (0, 2, 1, 3)[k % 4]
        r_in = R * (.42 + .14 * lev)
        if dy < r_in:
            hin = math.sqrt(r_in * r_in - dy * dy)
            cv.line([(fx - half, y), (fx - hin, y)]) if lev == 0 else cv.hair([(fx - half, y), (fx - hin, y)])
            cv.line([(fx + hin, y), (fx + half, y)]) if lev == 0 else cv.hair([(fx + hin, y), (fx + half, y)])
        else:
            (cv.line if lev == 0 else cv.hair)([(fx - half, y), (fx + half, y)])
        y += 1.5
        k += 1
    n = max(24, int(R * 1.4) // 2 * 2)
    for i in range(n):
        a = TAU * i / n + .05
        r0 = R * (.1 if i % 2 == 0 else .16)
        r1 = R * (.5 if i % 2 == 0 else rng.uniform(.26, .36))
        cv.hair([(fx + r0 * math.cos(a), fy + r0 * math.sin(a)), (fx + r1 * math.cos(a), fy + r1 * math.sin(a))])


TAU = 2 * PI


def _book(cv, cx, gy, bw, ph, rng, deco=True):
    """An open book seen from the front, gutter foot at (cx, gy), each leaf bw wide, ph tall."""
    thick = max(2.5, ph * .16)

    def top(s, t):
        return (cx + s * bw * t, gy - ph - ph * .2 * math.sin(PI * t) + ph * .08 * t + ph * .1 * (1 - t) ** 3)

    def bot(s, t):
        return (cx + s * bw * t, gy - ph * .14 * math.sin(PI * t * .9) + ph * .1 * (1 - t) ** 3 * 0)

    def blk(s, t, f=1.):
        b = bot(s, t)
        return (b[0] + s * f * 1.5, b[1] + thick * f * (.35 + .65 * t))
    T = [i / 30 for i in range(31)]
    # cover boards (dark leather), then the page blocks
    for s in (-1, 1):
        cov = [(cx, gy + 1.5)] + [(blk(s, t, 1.)[0] + s * 1.8 * t, blk(s, t, 1.)[1] + 1.8) for t in T] + \
              [(cx + s * (bw + 3.3), gy - ph * .3)] + [(cx + s * bw * .5, gy - ph * .1)]
        cov = [(cx, gy + 1.5)] + [(blk(s, t, 1.)[0] + s * 1.8 * t, blk(s, t, 1.)[1] + 1.8) for t in T] + \
              [(bot(s, 1.)[0] + s * 3.3, bot(s, 1.)[1] - 2)]
        cv.obj([cov], 1.)
        cv.hair(C.hatch_poly(cov, 0, 1.5))
        blkp = [bot(s, t) for t in T] + [blk(s, t) for t in T[::-1]]
        cv.obj([blkp], 1.)
        f = .25
        while f < 1:
            cv.hair([blk(s, t, f) for t in T[3:]])
            f += .25
    marg_t, marg_f = .1, .14
    for s in (-1, 1):
        page = [top(s, t) for t in T] + [bot(s, t) for t in T[::-1]]
        cv.obj([page], 1.)
        # gutter shadow: rules parallel to the gutter, closing up into it
        t = .006
        while t < .16:
            cv.hair([_lerp(top(s, t), bot(s, t), .02), _lerp(top(s, t), bot(s, t), .98)])
            t += (1.1 + 6 * t) / bw
        # page curl shade along the outer edge
        cv.hair([_lerp(top(s, .97), bot(s, .97), .03), _lerp(top(s, .97), bot(s, .97), .97)])
        # the text block, as words
        cap = None
        pic = None
        if deco and s < 0:
            cap = (.6, .9, marg_f, .5)        # drop cap P
        if deco and s > 0 and ph > 16:
            pic = (.26, .86, marg_f, .5)       # plate: Mt. Hood
        nl = max(4, int(ph * .78 / 1.9))
        for k in range(nl):
            f = marg_f + (1 - 2 * marg_f) * k / (nl - 1)
            t0, t1 = .17, .9
            if cap and cap[2] - .02 <= f <= cap[3] + .02:
                t1 = cap[0] - .03
            if pic and pic[2] - .02 <= f <= pic[3] + .02:
                continue
            if k == nl // 2 or k == nl - 1:
                t1 = t0 + (t1 - t0) * rng.uniform(.35, .7)
            t = t0
            while t < t1:
                L = rng.uniform(2.5, 7.5) / bw
                e = min(t1, t + L)
                if e - t > .8 / bw:
                    cv.hair([_lerp(top(s, t), bot(s, t), f), _lerp(top(s, (t + e) / 2), bot(s, (t + e) / 2), f),
                             _lerp(top(s, e), bot(s, e), f)])
                t = e + 1.3 / bw
        if cap:
            q = lambda t, f: _lerp(top(s, t), bot(s, t), f)
            box = [q(cap[0], cap[2]), q(cap[1], cap[2]), q(cap[1], cap[3]), q(cap[0], cap[3])]
            cv.obj([box], .5)
            x0, y0 = box[1][0] + .8, box[1][1] + .8
            x1, y1 = box[0][0] - .8, box[3][1] - .8
            wdt, hgt = x1 - x0, y1 - y0
            sx = x0 + wdt * .32
            cv.heavy([(sx, y0 + hgt * .08), (sx, y0 + hgt * .92)])
            cv.line([(sx - wdt * .14, y0 + hgt * .92), (sx + wdt * .16, y0 + hgt * .92)])
            bowl = [(sx - wdt * .1, y0 + hgt * .1)] + [(sx + wdt * .1 + wdt * .38 * math.sin(PI * j / 12),
                     y0 + hgt * .3 - hgt * .2 * math.cos(PI * j / 12)) for j in range(13)] + [(sx, y0 + hgt * .5)]
            cv.heavy(bowl)
            cv.hair(C.hatch_poly([(x0, y1), (x0 + wdt * .2, y1), (x0, y1 - hgt * .3)], 45, 1.5))
            cv.hair([(x1 - wdt * .3, y1 - .4), (x1 - .4, y1 - .4), (x1 - .4, y1 - hgt * .3)])
        if pic:
            q = lambda t, f: _lerp(top(s, t), bot(s, t), f)
            frame = [q(pic[0], pic[2]), q(pic[1], pic[2]), q(pic[1], pic[3]), q(pic[0], pic[3])]
            cv.obj([frame], .5)
            # sky: horizontal rules; the mountain white with a shaded flank
            cv.hair(C.hatch_poly(frame, 0, 1.5, inset=.3))
            xa, xb = frame[0][0], frame[1][0]
            ya, yb2 = (frame[0][1] + frame[1][1]) / 2, (frame[2][1] + frame[3][1]) / 2
            pw, phh = xb - xa, yb2 - ya
            peak = (xa + pw * .52, ya + phh * .18)
            mtn = [(xa + .4, yb2 - .4), (xa + pw * .3, ya + phh * .62), peak, (xa + pw * .75, ya + phh * .6), (xb - .4, yb2 - .4)]
            cv.obj([mtn], .5)
            cv.hair(C.hatch_poly([peak, (xa + pw * .75, ya + phh * .6), (xb - .4, yb2 - .4), (xa + pw * .55, yb2 - .4)], 70, 1.5))
            cv.hair([(xa + pw * .4, ya + phh * .42), (xa + pw * .47, ya + phh * .5), (xa + pw * .55, ya + phh * .4)])
    # ribbon bookmark from the gutter
    rl = ph * .9
    rib = [(cx - 1.3, gy - ph * .55), (cx + 1.3, gy - ph * .55), (cx + 2.3, gy + rl * .55), (cx + 1.6, gy + rl * .5),
           (cx + .4, gy + rl * .62), (cx + .2, gy + rl * .45), (cx - .9, gy + rl * .5)]
    cv.obj([rib], .5)
    cv.hair(C.hatch_poly(rib, 60, 1.5))
    cv.line([(cx, gy - ph * .55), (cx, gy - ph * 1.08)])


def _stack(cv, x, yb, w, rng, hs):
    """Books lying flat, spines to us (heights hs): returns top y."""
    y = yb
    for bh in hs:
        bwid = w * rng.uniform(.82, 1.)
        bx = x + (w - bwid) / 2 + rng.uniform(-2, 2)
        face = [(bx, y), (bx + bwid, y), (bx + bwid, y - bh), (bx, y - bh)]
        rnd = [(bx, y), (bx + bwid, y), (bx + bwid + 1.2, y - bh / 2), (bx + bwid, y - bh), (bx, y - bh), (bx - 1.2, y - bh / 2)]
        cv.obj([rnd], 1.)
        v = 1.
        while v < bh - .5:
            m = abs(v / bh - .38)
            if m > .1:
                cv.hair([(bx + .5, y - v), (bx + bwid - .5, y - v)])
            v += 1.5 if m > .25 else 2.
        for e in (.07, .1, .9, .93):
            cv.line([(bx + bwid * e, y), (bx + bwid * e, y - bh)])
        if rng.random() < .7:
            lab = [(bx + bwid * .4, y - bh * .25), (bx + bwid * .6, y - bh * .25), (bx + bwid * .6, y - bh * .75), (bx + bwid * .4, y - bh * .75)]
            cv.obj([lab], .5)
            cv.hair([(bx + bwid * .44, y - bh / 2), (bx + bwid * .56, y - bh / 2)])
        y -= bh
    # top cover in perspective
    top = [(bx, y), (bx + bwid, y), (bx + bwid - 2, y - 3), (bx + 2, y - 3)]
    cv.obj([top], 1.)
    cv.hair(C.hatch_poly(top, 0, 1.5))
    return y - 3


def _specs(cv, x, y, r):
    """Round reading spectacles lying on the desk (seen low, so the rims are flat ellipses)."""
    for dx in (-r * 1.25, r * 1.25):
        rim = C._ell_pts(x + dx, y, r, r * .5, 28)
        inner = C._ell_pts(x + dx, y, r - 1.2, r * .5 - 1.1, 28)
        cv.obj([rim], 1.)
        cv.line(inner + [inner[0]])
        cv.hair(C.hatch_poly(inner, -20, 1.5, phase=.3)[1::2])
    cv.line([(x - r * .3, y - r * .3), (x, y - r * .45), (x + r * .3, y - r * .3)])
    cv.line([(x - r * 2.2, y - r * .2), (x - r * 3.6, y - r * .9), (x - r * 4.3, y - r * .5)])
    cv.line([(x + r * 2.2, y - r * .2), (x + r * 3.4, y - r * 1.1), (x + r * 3.9, y - r * .7)])


def _candle(cv, x, yb, cw, ch, rng):
    """Chamberstick: dish, candle, wick; returns the flame centre."""
    dish = C._ell_pts(x, yb - 1.5, cw * 2.1, 2.6, 30)
    cv.obj([C._ell_pts(x + cw * 2.1 + 1.5, yb - 3.5, 2.6, 2.6, 16)], 1.)  # finger ring
    cv.obj([dish], 1.)
    cv.hair(C.hatch_poly(dish, 0, 1.5, phase=.5))
    cv.hair(C._ell_pts(x, yb - 2.6, cw * 1.6, 1.3, 24, PI, TAU))
    body = [(x - cw / 2, yb - 2.5), (x + cw / 2, yb - 2.5), (x + cw / 2, yb - ch), (x - cw / 2, yb - ch)]
    cv.obj([body], 1.)
    u = .5
    while u < cw:
        f = u / cw
        if f < .2 or f > .62:
            cv.hair([(x - cw / 2 + u, yb - ch + 1.5), (x - cw / 2 + u, yb - 3)])
        u += 1.5 if (f < .12 or f > .78) else 2.
    drip = [(x + cw * .15, yb - ch), (x + cw * .35, yb - ch), (x + cw * .3, yb - ch + ch * .3), (x + cw * .22, yb - ch + ch * .32)]
    cv.obj([drip], .5)
    cv.hair(C._ell_pts(x, yb - ch, cw / 2, 1.2, 16, 0, PI))
    fy = yb - ch - 2.2
    fh = max(6., cw * 1.6)
    fl = [(x + (cw * .38) * math.sin(PI * i / 16) * (1 - i / 16) ** .6 * 1.6, fy - fh * i / 16) for i in range(17)]
    fl = fl + [(2 * x - p[0], p[1]) for p in fl[::-1]]
    cv.obj([fl], 1.)
    cv.obj([C._ell_pts(x, fy - fh * .22, cw * .14, fh * .18, 12)], .5)
    cv.line([(x, yb - ch), (x, fy - fh * .1)])
    return (x, fy - fh * .4)


def _spider(fx, top_y, by, s=1.):
    """Black spider on its thread; raw svg (drawn above the canvas)."""
    o = f'<path d="M{_n(fx)},{_n(top_y)}V{_n(by - 2 * s)}" stroke="#000" stroke-width=".5"/>'
    body = _d(C._ell_pts(fx, by + 1.6 * s, 1.9 * s, 2.4 * s, 14), True, 0) + _d(C._ell_pts(fx, by - .9 * s, 1.2 * s, 1.2 * s, 10), True, 0)
    o += f'<path d="{body}" fill="#000" stroke="none"/>'
    legs = []
    for sd in (-1, 1):
        for k, (a, b) in enumerate(((-.9, -1.6), (-.35, -.6), (.25, .5), (.8, 1.4))):
            ax, ay = fx + sd * .9 * s, by - .6 * s + k * .45 * s
            kx, ky = ax + sd * 2.6 * s, ay + a * 2.2 * s - 1.2 * s
            ex, ey = kx + sd * 1.4 * s, ky + b * 1.9 * s + 2.2 * s
            legs.append(f"M{_n(ax)},{_n(ay)}L{_n(kx)},{_n(ky)}L{_n(ex)},{_n(ey)}")
    o += f'<path d="{"".join(legs)}" stroke="#000" stroke-width=".5" fill="none"/>'
    return o


def _desk_scene(cx, cy, a, b, seed, uid):
    """The whole field of a cartouche whose inner superellipse half-axes are a, b."""
    rng = random.Random(seed)
    field = C._superellipse(cx, cy, a - 4.6, b - 4.6)
    fd = _d(field, True, .1)
    x0, x1, y0, y1 = cx - a, cx + a, cy - b, cy + b
    H = 2 * b
    desk_h = min(max(H * .2, 12), 40)
    ty = y1 - desk_h                               # desk top surface (back edge)
    cv = Canvas = C.Canvas()
    # shelves behind
    rh = min(max(H * .3, 26), 46)
    yb = ty + 1
    rows = []
    while yb > y0 - rh * .3:
        rows.append(yb)
        yb -= rh + 4
    for i, yb in enumerate(rows):
        _shelf_row(cv, x0, x1, yb, rh, random.Random(seed * 31 + i))
        if i:
            pass
    # proportions of the desk group
    bw = min(a * (.44 if b < a * .75 else .56), H * .42, 92)
    ph = bw * .62
    gx = cx - a * .02
    gy = ty + desk_h * .48
    cdx = gx + bw + max(13, a * .19)
    cwid = max(4.5, bw * .15)
    srng = random.Random(seed * 7 + 1)
    hs = [srng.choice((5., 6., 7.5)) * max(1., bw / 50) for _ in range(3 if H > 90 else 2)]
    sbase = gy + desk_h * .25
    stop_y = sbase - sum(hs) - 3
    cht = min(ph * 1.25, (stop_y - y0) * .55)
    # candle glow
    flame_guess = (cdx, stop_y + 2 - cht - 2.2 - max(6., cwid * 1.6) * .4)
    R = min(cht * .95, a * .3, (gy - y0) * .7)
    _halo(cv, flame_guess[0], flame_guess[1], R, rng)
    for i, yb in enumerate(rows[1:]):
        _board(cv, x0, x1, yb)
    # desk with grain
    desk = [(x0 - 2, ty), (x1 + 2, ty), (x1 + 2, y1 + 2), (x0 - 2, y1 + 2)]
    cv.obj([desk], 1.)
    k = 0
    y = ty + 1.5
    front = y1 - min(6., desk_h * .3)
    while y < front - .5:
        amp = .5 + .4 * math.sin(k * 1.7)
        cv.hair([(x, y + amp * math.sin(x * .07 + k * .9) + .4 * math.sin(x * .23 + k)) for x in range(int(x0) - 2, int(x1) + 3, 3)])
        y += 2. if (k % 5) else 1.5
        k += 1
    for kx in (cx - a * .62, cx + a * .55):
        kn = C._ell_pts(kx, ty + desk_h * .45, 4.5, 1.6, 16)
        cv.hair(kn + [kn[0]])
    cv.heavy([(x0 - 2, front), (x1 + 2, front)])
    y = front + 1.5
    while y < y1 + 2:
        cv.line([(x0 - 2, y), (x1 + 2, y)])
        y += 1.5
    # cast shadows on the desk, falling away from the candle (to the left)
    sh = [(gx - bw - 1, gy + 2), (gx + bw, gy + 2), (gx + bw - 6, gy - desk_h * .05), (gx - bw - desk_h * .6, gy - desk_h * .05)]
    cv.obj([], 0)
    cv.hair(C.hatch_poly(sh, -30, 1.5))
    # spectacles laid on the desk at the left
    _specs(cv, gx - bw - max(13, a * .16), gy + desk_h * .05, max(4.5, bw * .13))
    # the candle stands on a stack of books at the right
    sw = cwid * 4.6
    _stack(cv, cdx - sw / 2, sbase, sw, srng, hs)
    _book(cv, gx, gy, bw, ph, random.Random(seed * 13 + 5))
    fx, fy = _candle(cv, cdx, stop_y + 2, cwid, cht, rng)
    body = (f'<clipPath id="{uid}"><path d="{fd}"/></clipPath><g clip-path="url(#{uid})">'
            f'<path d="{fd}" fill="{C.pat("G")}" stroke="none"/>' + cv.svg())
    # spider dropping into the light from the shelf above
    spx = flame_guess[0] - R * .55
    spy = flame_guess[1] - R * .1
    top = max(y0, rows[1] if len(rows) > 1 else y0)
    if R > 14:
        body += _spider(spx, y0 - 2, spy, max(.7, min(1.2, R / 40)))
    body += "</g>"
    return body


def _book_medallion(cx, cy, rx, ry, seed, uid):
    """Small central motif for the band: an open book in a ruled sunburst, filling the medallion."""
    rng = random.Random(seed)
    el = C._ell_pts(cx, cy, rx, ry, 64)
    fd = _d(el, True, .1)
    cv = C.Canvas()
    cv.obj([el], 0)
    n = 96
    for i in range(n):
        an = TAU * i / n
        r0 = .25 if i % 2 else .1
        cv.hair([(cx + rx * r0 * math.cos(an), cy - ry * .2 + ry * r0 * math.sin(an)),
                 (cx + rx * 1.1 * math.cos(an), cy - ry * .2 + ry * 1.1 * math.sin(an))])
    bw = rx * .6
    ph = min(ry * .8, bw * .62)
    _book(cv, cx, cy + ph * .55, bw, ph, rng, deco=ph > 13)
    return (f'<clipPath id="{uid}"><path d="{fd}"/></clipPath><g clip-path="url(#{uid})">'
            + cv.svg() + "</g>")


# ------------------------------------------------------------------ layouts (house frames, bespoke fill)

def _cart_axes(w, h):
    bw = max(5., min(w, h) * .07)
    return w / 2 - bw * 1.6, h / 2 - bw * 1.6


def _layout_band(w, h, seed):
    o = []
    top = 7.
    o.append(C.bead_moulding(0, 3.5, w, 1.5))
    gh = h - top - 2
    o.append(C.dark_ground((0, top, w, gh), "G"))
    gap = min(gh * 1.9, 120)
    o.append(C._clip(C._uid("bk", w, h, seed), 0, top, w, gh,
                     C.scroll_band(0, top, w, gh, seed, gap * .78, r_scale=1.15 * max(1., 62. / gh))))
    cx, cy = w / 2, top + gh / 2
    rx, ry = gap / 2, gh / 2 - 1
    o.append(C._medallion(cx, cy, rx, ry))
    o.append(_book_medallion(cx, cy, rx - 3.5, ry - 3.5, seed, C._uid("bkm", w, h, seed)))
    o.append(f'<path d="M0,{_n(h - .5)}h{_n(w)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def _layout_medium(w, h, seed):
    rng = random.Random(seed)
    o = []
    em = min(12., 6 + h * .025)
    o.append(C.egg_and_dart(0, 0, w, em))
    foot = 7.
    gy0, gy1 = em + 1, h - foot
    gh = gy1 - gy0
    o.append(C.dark_ground((0, gy0, w, gh), "G"))
    cw = min(w * .46, gh * 1.95)
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
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("bkm", w, h, seed), 0, gy0, w, gh, cv.svg()))
    ch = gh + 4
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_axes(cw, ch)
    o.append(_desk_scene(cx, cy, a, b, seed, C._uid("bkd", w, h, seed)))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tally_tablet(tx, ty, tw, th):
    """40 books to read: eight gates of five, cut into a ruled tablet."""
    o = [f'<path d="M{_n(tx + 1)},{_n(ty + 1)}h{_n(tw - 2)}v{_n(th - 2)}h{_n(-tw + 2)}z" fill="{C.pat("L")}" stroke="none"/>']
    g = 8
    gw = min(tw * .9 / g, th * 1.3)
    x = tx + (tw - gw * g) / 2
    m = ""
    hh = th * .56
    yt = ty + (th - hh) / 2
    for i in range(g):
        x0 = x + i * gw + gw * .18
        sp = gw * .13
        for k in range(4):
            m += f"M{_n(x0 + k * sp)},{_n(yt)}v{_n(hh)}"
        m += f"M{_n(x0 - sp * .6)},{_n(yt + hh * .8)}L{_n(x0 + sp * 3.6)},{_n(yt + hh * .2)}"
    o.append(f'<path d="{m}" stroke="#fff" stroke-width="2.5" fill="none"/>')
    o.append(f'<path d="{m}" stroke="#000" stroke-width="1" fill="none"/>')
    return "".join(o)


def _layout_tall(w, h, seed):
    rng = random.Random(seed)
    o = []
    density = .8
    ped_h = min(max(h * .17, 48), 86.)
    frieze = min(max(h * .1, 28), 56.) if h >= 440 else 0.
    top_free = min(h * .055, 26.)
    px0, py0 = 6., top_free
    pw = w - 12
    ph = h - top_free - ped_h - frieze + ped_h * .3
    o.append(f'<path d="M{_n(px0 - 3.5)},{_n(py0 - 3.5)}h{_n(pw + 7)}v{_n(ph + 7)}h{_n(-pw - 7)}z" fill="#fff" stroke="#000" stroke-width="1"/>')
    o.append(f'<path d="M{_n(px0 - 1.5)},{_n(py0 - 1.5)}h{_n(pw + 3)}v{_n(ph + 3)}h{_n(-pw - 3)}z" fill="none" stroke="#000" stroke-width=".5"/>')
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .56, ph * .64
    cx, cy = w / 2, py0 + ph * .45
    occ = [("r", cx - cw / 2 + 6, cy - ch / 2 + 6, cx + cw / 2 - 6, cy + ch / 2 - 6)]
    cv = C.Canvas()
    main = C.Canvas()
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
    o.append(C._clip(C._uid("bkt", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    c, _, _ = C.cartouche(cx, cy, cw, ch, rng.randrange(1 << 20))
    o.append(c)
    a, b = _cart_axes(cw, ch)
    o.append(_desk_scene(cx, cy, a, b, seed, C._uid("bkd", w, h, seed)))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, cen = C.ribbon_banner(cx, cy + ch * .47, cw * 1.3, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    lines = "".join(_d([(x, y + dy) for x, y in cen[2:-2]], tol=.2) for dy in (-bh * .2, 0, bh * .2))
    o.append(f'<path d="{lines}" stroke="#000" stroke-width=".5" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, (tx, ty, tw, th) = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tally_tablet(tx + 2, ty + 2, tw - 3, th - 3))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("bkf", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    seed = sum(map(ord, (ctx or {}).get("date", ""))) + 404
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed)
    return C.svg_doc(w, h, body)
