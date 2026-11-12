"""watch-01 "4K Blu-ray deals" (Criterion 50% off): a 4K disc with its iridescent track sheen
sliding out of its case before a film reel, the film unspooling into an acanthus curl, set in the
house cartouche on a projector-beam glory.  Easter egg: one frame of the film shows Parker's dog."""
import sys
import math
import random
import engraving_codex as C

TAU = math.tau
_n = C._n
_d = C._d


# ------------------------------------------------------------------------------------------------
# small geometry helpers
# ------------------------------------------------------------------------------------------------

def _circ(cx, cy, r, n=None, a0=0., a1=TAU):
    n = n or max(16, int(abs(a1 - a0) * r / 2.2))
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def _ring_d(cx, cy, r0, r1):
    """Annulus as even-odd path data."""
    return _d(_circ(cx, cy, r1)[:-1], True, .1) + _d(_circ(cx, cy, r0)[:-1][::-1], True, .1)


def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _rot(pts, cx, cy, a):
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def _arcs_by_tone(cx, cy, r0, r1, pitch, tone):
    """Concentric track rings from r0 to r1; tone(theta) -> 0 dense, 1 mid, 2 light, 3 none.
    Ring i is drawn where (i % (1, 2, 4)[tone]) == 0."""
    out = []
    i = 0
    r = r0
    steps = 120
    while r <= r1:
        cur = []
        for k in range(steps + 1):
            th = TAU * k / steps
            t = tone(th)
            on = i % (1, 2, 4, 6)[t] == 0
            if on:
                cur.append((cx + r * math.cos(th), cy + r * math.sin(th)))
            elif cur:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
        if len(cur) > 1:
            out.append(cur)
        r += pitch
        i += 1
    return out


# ------------------------------------------------------------------------------------------------
# lettering as strokes ("4K"), the dog egg
# ------------------------------------------------------------------------------------------------

_FONT = {   # stroke glyphs on a unit cap height, (advance, strokes)
    "4": (.62, [[(.48, 1), (.48, 0), (0, .66), (.62, .66)]]),
    "K": (.6, [[(0, 0), (0, 1)], [(.58, 0), (.02, .58)], [(.2, .42), (.6, 1)]]),
    "5": (.58, [[(.56, 0), (.08, 0), (.04, .44), (.3, .38), (.5, .46), (.58, .66), (.52, .88), (.3, 1), (.02, .92)]]),
    "0": (.58, [[(.29, 0), (.1, .1), (.02, .5), (.1, .9), (.29, 1), (.48, .9), (.56, .5), (.48, .1), (.29, 0)]]),
    "%": (.7, [[(.62, 0), (.08, 1)], [(.16, .04), (.04, .16), (.16, .3), (.28, .16), (.16, .04)],
               [(.54, .7), (.42, .84), (.54, .98), (.66, .84), (.54, .7)]]),
    "O": (.7, [[(.35, 0), (.1, .1), (.0, .5), (.1, .9), (.35, 1), (.6, .9), (.7, .5), (.6, .1), (.35, 0)]]),
    "F": (.5, [[(.48, 0), (0, 0), (0, 1)], [(0, .48), (.38, .48)]]),
    " ": (.4, []),
}


def _text_strokes(txt, x, y, s, track=.22):
    out = []
    for ch in txt:
        adv, strokes = _FONT[ch]
        out += [[(x + px * s, y + py * s) for px, py in st] for st in strokes]
        x += (adv + track) * s
    return out


def _text_width(txt, s, track=.22):
    return sum((_FONT[c][0] + track) * s for c in txt) - track * s


def _text_on(centre, txt, s, track=.3):
    """Letter txt centred along a polyline (the banner's face centre), upright to the local tangent."""
    L = [0.]
    for i in range(1, len(centre)):
        L.append(L[-1] + math.dist(centre[i - 1], centre[i]))
    tw = _text_width(txt, s, track)
    u = (L[-1] - tw) / 2
    out = []

    def at(v):
        for i in range(1, len(L)):
            if L[i] >= v:
                t = (v - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                p0, p1 = centre[i - 1], centre[i]
                return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t), math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        return centre[-1], 0.
    for ch in txt:
        adv, strokes = _FONT[ch]
        (px, py), a = at(u + adv * s / 2)
        for st in strokes:
            pts = [((gx - adv / 2) * s, (gy - .5) * s) for gx, gy in st]
            out.append([(px + X * math.cos(a) - Y * math.sin(a), py + X * math.sin(a) + Y * math.cos(a)) for X, Y in pts])
        u += (adv + track) * s
    return out


def _glyph_4k(x, y, s):
    return _text_strokes("4K", x, y, s, .25)


def _dog(cx, cy, s):
    """Tiny profile of a dog's head facing right (outline polys + strokes), s ~ frame height."""
    head = _circ(cx - s * .05, cy, s * .28, 18)
    snout = [(cx + s * .1, cy - s * .12), (cx + s * .42, cy - s * .02), (cx + s * .42, cy + s * .14),
             (cx + s * .08, cy + s * .2)]
    ear = [(cx - s * .2, cy - s * .2), (cx - s * .02, cy - s * .32), (cx - s * .3, cy + s * .2)]
    neck = [(cx - s * .3, cy + s * .1), (cx + s * .02, cy + s * .2), (cx - s * .02, cy + s * .48),
            (cx - s * .42, cy + s * .48)]
    return [neck, head, snout, ear]


# ------------------------------------------------------------------------------------------------
# the vignette: glory ground, reel, film strip, case, disc
# ------------------------------------------------------------------------------------------------

def _glory(cx, cy, R, field_d, cid):
    """Projector-beam rays behind the subject: alternating mid/light ruled wedges, inside the field."""
    dk, lt = [], []
    n = 28
    for i in range(n):
        a0, a1 = TAU * i / n, TAU * (i + 1) / n
        wedge = [(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                 (cx + R * math.cos(a1), cy + R * math.sin(a1))]
        (dk if i % 2 else lt).append(_d(wedge, True, 0))
    return (f'<clipPath id="{cid}"><path d="{field_d}"/></clipPath><g clip-path="url(#{cid})">'
            f'<path d="{field_d}" fill="{C.pat("L")}" stroke="none"/>'
            f'<path d="{"".join(dk)}" fill="{C.pat("M")}" stroke="none"/>'
            f'<path d="{"".join(lt)}" fill="{C.pat("D")}" stroke="none"/>')


def _reel(cv, cx, cy, R, rot):
    """Metal film reel: rim, wound film, five spoke windows (left for black fill), hub."""
    blacks = []
    cv.obj([_circ(cx, cy, R)], 1.)
    # wound film: dense rings
    cv.hair(_arcs_by_tone(cx, cy, R * .42, R * .93, 1.5, lambda t: 0))
    cv.line([_circ(cx, cy, R * .95)])
    # flange face over the film, with windows
    face = _circ(cx, cy, R * .8)
    win = []
    for k in range(5):
        a = rot + TAU * k / 5
        pts = []
        for j in range(13):
            th = a - .42 + .84 * j / 12
            pts.append((cx + R * .72 * math.cos(th), cy + R * .72 * math.sin(th)))
        for j in range(13):
            th = a + .3 - .6 * j / 12
            pts.append((cx + R * .36 * math.cos(th), cy + R * .36 * math.sin(th)))
        win.append(pts)
    cv.obj([_circ(cx, cy, R * .99)], 1.)
    cv.hair(C.hatch_poly(_circ(cx, cy, R * .99), 30, 2))
    cv.hair(_arcs_by_tone(cx, cy, R * .86, R * .97, 1.5, lambda t: 0 if math.sin(t - .8) > 0 else 2))
    cv.line([_circ(cx, cy, R * .84)])
    for w in win:
        blacks.append(_d(w, True, .1))
    # through the windows the wound film shows: dense rings, drawn on top as their own objects
    for w in win:
        cv.obj([w], 1.)
        cv.hair(_arcs_by_tone(cx, cy, R * .38, R * .74, 1.5, lambda t: 0))
    cv.obj([_circ(cx, cy, R * .22)], 1.)
    cv.hair(_arcs_by_tone(cx, cy, R * .08, R * .2, 1.5, lambda t: 0 if math.sin(t + .8) > 0 else 2))
    blacks.append(_d(_circ(cx, cy, R * .07), True, .1))
    for k in range(3):
        a = rot + TAU * k / 3
        blacks.append(_d(_rot(_rect(cx + R * .07, cy - R * .02, R * .05, R * .04), cx, cy, a), True, 0))
    return blacks


def _strip_path(pts, sw):
    """Offset a centreline into per-frame quads. Returns list of (quad, centre, ang)."""
    # resample at equal arc length
    L = [0.]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.dist(pts[i - 1], pts[i]))
    fl = sw * .78
    quads = []
    s = 0.
    j = 0

    def at(s):
        nonlocal j
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        t = (s - L[j]) / max(1e-6, L[j + 1] - L[j])
        p0, p1 = pts[j], pts[j + 1]
        return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t), math.atan2(p1[1] - p0[1], p1[0] - p0[0])

    while s + fl <= L[-1]:
        (a, ta), (b, tb) = at(s), at(s + fl)
        na = (-math.sin(ta) * sw / 2, math.cos(ta) * sw / 2)
        nb = (-math.sin(tb) * sw / 2, math.cos(tb) * sw / 2)
        q = [(a[0] + na[0], a[1] + na[1]), (b[0] + nb[0], b[1] + nb[1]),
             (b[0] - nb[0], b[1] - nb[1]), (a[0] - na[0], a[1] - na[1])]
        c, tc = at(s + fl / 2)
        quads.append((q, c, tc))
        s += fl
    return quads


def _frame_pic(cv, m, c, fw, fh, ta, fr):
    """Stills from today's list: 0 Cinderella's castle, 1 crossed katana (Seven Samurai),
    2 Mt. Hood, 3 a lit screen; drawn in the frame's own rotated space."""
    X, Y = c
    R = lambda pts: _rot([(X + px * fw, Y + py * fh) for px, py in pts], X, Y, ta)
    deg = math.degrees(ta)
    if m == 0:
        cv.hair(C.hatch_poly(fr, deg + 90, 3))
        castle = R([(-.42, .5), (-.42, .0), (-.3, -.22), (-.18, .0), (-.1, .0), (-.1, -.12), (.0, -.48),
                    (.1, -.12), (.1, .0), (.18, .0), (.3, -.22), (.42, .0), (.42, .5)])
        cv.obj([castle], .5)
        cv.hair(C.hatch_poly(castle, deg + 90, 1.5, .5))
    elif m == 1:
        cv.hair(C.hatch_poly(fr, deg, 3))
        cv.line([R([(-.38, .42), (.36, -.42)]), R([(.38, .42), (-.36, -.42)])])
        cv.heavy([R([(-.3, .2), (-.18, .36)]), R([(.3, .2), (.18, .36)])])
    elif m == 2:
        cv.hair(C.hatch_poly(fr, deg, 3))
        mt = R([(-.48, .5), (-.12, -.36), (.0, -.44), (.1, -.3), (.48, .5)])
        cv.obj([mt], .5)
        cv.hair(C.hatch_poly(R([(.0, -.2), (.1, -.3), (.48, .5), (.12, .5)]), deg + 90, 1.5))
    else:
        cv.hair(C.hatch_poly(fr, deg + 45, 1.5))
        scr = R([(-.34, -.3), (.34, -.3), (.34, .3), (-.34, .3)])
        cv.obj([scr], .5)
        cv.hair(C.hatch_poly(scr, deg, 3))


def _film(cv, centre, sw, egg_at, rng):
    """Film strip along a centreline: dark base with sprocket holes, picture frames ruled light;
    one frame carries the dog."""
    blacks = []
    quads = _strip_path(centre, sw)
    for i, (q, c, ta) in enumerate(quads):
        cv.obj([q], 1.)
        cv.hair(C.hatch_poly(q, math.degrees(ta) + 90, 1.5))
        # sprocket holes on both edges
        for side in (-1, 1):
            for k in (-.25, .25):
                hx = c[0] + math.cos(ta) * sw * .78 * k - math.sin(ta) * side * sw * .39
                hy = c[1] + math.sin(ta) * sw * .78 * k + math.cos(ta) * side * sw * .39
                hole = _rot(_rect(hx - sw * .07, hy - sw * .05, sw * .14, sw * .1), hx, hy, ta)
                cv.obj([hole], .5)
        # picture frame
        fw, fh = sw * .62, sw * .5
        fr = _rot(_rect(c[0] - fw / 2, c[1] - fh / 2, fw, fh), c[0], c[1], ta)
        cv.obj([fr], .5)
        if i == egg_at:
            cv.hair(C.hatch_poly(fr, math.degrees(ta), 1.5))
            dog = [_rot(p, c[0], c[1], ta) for p in _dog(c[0], c[1] + fh * .05, fh)]
            cv.obj(dog, .5)
            cv.hair([_rot([(c[0] + fh * .12, c[1] - fh * .04), (c[0] + fh * .13, c[1] - fh * .03)], c[0], c[1], ta)])
        else:
            _frame_pic(cv, i % 4, c, fw, fh, ta, fr)
    return blacks


def _case(cv, x, y, w, h):
    """Keep case standing behind the disc: shell, dark header band, cover panel."""
    cv.obj([_rect(x, y, w, h)], 1.)
    cv.hair(C.hatch_poly(_rect(x, y, w, h), 90, 3))
    band = _rect(x + 1.5, y + 1.5, w - 3, h * .14)
    cv.obj([band], .5)
    cv.hair(C.hatch_poly(band, 0, 1.5))
    cover = _rect(x + w * .08, y + h * .19, w * .84, h * .76)
    cv.obj([cover], .5)
    cv.hair(C.hatch_poly(cover, 45, 2))
    cv.hair(C.hatch_poly(cover, -45, 3))
    cv.line([_rect(x + w * .08, y + h * .19, w * .84, h * .76) + [(x + w * .08, y + h * .19)]])
    # spine ridges on the right
    for k in range(3):
        cv.hair([(x + w - 3 - k * 1.5, y + h * .17), (x + w - 3 - k * 1.5, y + h * .97)])
    return band


def _disc(cv, cx, cy, R, sheen):
    """The 4K disc: tracks shaded by a bow-tie sheen (dense where dark, sparse where it catches
    the light), clear hub ring, mirror band, centre hole (filled black by the caller)."""
    cv.obj([_circ(cx, cy, R)], 1.)

    def tone(th):
        v = math.cos(2 * (th - sheen))
        if v > .55:
            return 0
        if v > -.1:
            return 1
        if v > -.75:
            return 2
        return 3
    cv.hair(_arcs_by_tone(cx, cy, R * .38, R * .97, 1.5, tone))
    # printed label plate across the top of the disc, "4K" engraved in it
    s = R * .17
    tw = _text_width("4K", s, .25)
    lx, ly = cx - tw / 2, cy - R * .78
    lab = _rect(lx - s * .45, ly - s * .3, tw + s * .9, s * 1.6)
    cv.obj([lab], .5)
    cv.hair(C.hatch_poly(lab, 0, 3))
    cv.heavy(_text_strokes("4K", lx, ly, s, .25))
    # radial glints in the light quadrants
    for k in (1, -1):
        for d in (-.06, 0, .06):
            th = sheen + k * math.pi / 2 + d + math.pi * (k < 0)
            cv.hair([(cx + R * .42 * math.cos(th), cy + R * .42 * math.sin(th)),
                     (cx + R * .9 * math.cos(th), cy + R * .9 * math.sin(th))])
    cv.line([_circ(cx, cy, R * .985)])
    cv.line([_circ(cx, cy, R * .36)])
    cv.hair([_circ(cx, cy, R * .33)])
    # clear plastic hub: light rings
    cv.hair(_arcs_by_tone(cx, cy, R * .2, R * .3, 1.5, lambda t: 1 if math.sin(t - sheen) > 0 else 3))
    cv.line([_circ(cx, cy, R * .19)])
    return _d(_circ(cx, cy, R * .12), True, .1)


def _film_centre(x0, y0, xb, yb, ex, rc):
    """Film centreline: drops from the reel (x0, y0), sweeps along the bottom (y = yb) to ex and
    rolls up into an acanthus-like curl of radius rc."""
    pts = []
    # cubic from reel down to the bottom run
    p0, p1, p2, p3 = (x0, y0), (x0 - rc * .6, yb - rc * .2), (x0 + rc * .4, yb), (xb, yb)
    for i in range(24):
        t = i / 24
        u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    for i in range(20):
        pts.append((xb + (ex - xb) * i / 20, yb))
    ccx, ccy = ex, yb - rc
    for i in range(41):
        t = i / 40
        a = math.pi / 2 - t * math.radians(215)
        r = rc * (1 - .3 * t)
        pts.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return pts


def vignette(cx, cy, a, b, field_d, seed, mode):
    """Fill the cartouche field (superellipse half-axes a, b centred cx, cy)."""
    rng = random.Random(seed)
    cid = C._uid("w1", cx, cy, a, b, mode)
    o = []
    o.append(_glory(cx, cy, math.hypot(a, b) * 1.2, field_d, cid))
    cv = C.Canvas()
    blacks = []
    sheen = .5 + rng.random() * .4
    if mode == "band":
        R = min(a, b) * .9
        blacks.append(_disc(cv, cx, cy, R, sheen))
        o.append(cv.svg())
    else:
        tall = mode == "tall"
        if tall:
            R = min(b * .5, a * .52)
            dx, dy = cx + a * .1, cy + b * .1
            Rr = R * .82
            rx, ry = cx - a * .4, cy - b * .4
            cw_, ch_ = R * 1.45, R * 1.95
            case_x, case_y = dx - R * .05, cy - b * .9
            sw = max(14., R * .3)
            yb = cy + b * .7
        else:
            R = min(b * .74, a * .48)
            dx, dy = cx + a * .04, cy - b * .1
            Rr = R * .78
            rx, ry = dx - a * .5, dy - b * .2
            cw_, ch_ = R * 1.6, R * 2.15
            case_x, case_y = dx + R * .1, dy - ch_ * .5
            sw = max(13., R * .32)
            yb = cy + b * .6
        blacks += _reel(cv, rx, ry, Rr, rng.random())
        band = _case(cv, case_x, case_y, cw_, ch_)
        rc = sw * 1.7
        centre = _film_centre(rx - Rr * .55, ry + Rr * .75, rx + Rr * .3, yb, cx + a * .66, rc)
        egg = 4 + rng.randrange(3)
        _film(cv, centre, sw, egg, rng)
        blacks.append(_disc(cv, dx, dy, R, sheen))
        o.append(cv.svg())
        # header band lettering on the case, white strokes on the dark band
        bx, by = band[0]
        bh = band[3][1] - by
        o.append(f'<path d="{"".join(_d(p, tol=0) for p in _glyph_4k(bx + cw_ - bh * 1.4, by + bh * .2, bh * .6))}" '
                 f'stroke="#fff" stroke-width="1.5" fill="none"/>')
    o.append(f'<path d="{"".join(blacks)}" fill="#000" stroke="none"/>')
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------------------------------------
# layouts (house layouts, but the vignette gets the whole field so nothing stays white)
# ------------------------------------------------------------------------------------------------

def _field_cartouche(cx, cy, w, h, seed, mode):
    svg, _, fd = C.cartouche(cx, cy, w, h, seed)
    bw = max(5., min(w, h) * .07)
    a, b = w / 2 - bw * 1.6, h / 2 - bw * 1.6
    return svg + vignette(cx, cy, a, b, fd, seed, mode)


def _layout_band(w, h, seed):
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
    fd = _d(C._ell_pts(cx, cy, rx - 2, ry - 2, 64), True, 0)
    o.append(vignette(cx, cy, rx - 2, ry - 2, fd, seed, "band"))
    o.append(f'<path d="{_d(C._ell_pts(cx, cy, rx - 4, ry - 4, 64), True)}" fill="none" stroke="#000" stroke-width=".5"/>')
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
    C.fill_scrolls(0, gy0, w, gh, occ, rng.randrange(1 << 20), rmin=max(9, gh * .08), rmax=r * .8,
                   max_n=8, edge=.7, cv=cv)
    cv.extend(main)
    o.append(C._clip(C._uid("m", w, h, seed), 0, gy0, w, gh, cv.svg()))
    o.append(_field_cartouche(cx, cy, cw, gh + 4, rng.randrange(1 << 20), "medium"))
    o.append(C.knurled_bar(0, h - foot, w, foot))
    return "".join(o)


def _tablet_film(tx, ty, tw, th):
    """The pedestal's sunk tablet carries a running strip of film: black base, sprocket rows,
    frames ruled in alternating tones."""
    tx, ty, tw, th = tx + 2, ty + 2, tw - 3, th - 3
    o = [f'<path d="M{_n(tx)},{_n(ty)}h{_n(tw)}v{_n(th)}h{_n(-tw)}z" fill="#000" stroke="none"/>']
    holes, fr_a, fr_b = [], [], []
    hs = max(1.5, th * .14)
    pitch = hs * 2.4
    n = int((tw - 2) / pitch)
    x0 = tx + (tw - n * pitch) / 2 + pitch * .3
    for i in range(n):
        x = x0 + i * pitch
        holes.append(f"M{_n(x)},{_n(ty + th * .07)}h{_n(hs)}v{_n(hs * .9)}h{_n(-hs)}z")
        holes.append(f"M{_n(x)},{_n(ty + th * .93 - hs * .9)}h{_n(hs)}v{_n(hs * .9)}h{_n(-hs)}z")
    fh = th * .5
    fw = fh * 1.35
    m = int(tw / (fw + 3))
    fx0 = tx + (tw - m * (fw + 3) + 3) / 2
    for i in range(m):
        d = f"M{_n(fx0 + i * (fw + 3))},{_n(ty + (th - fh) / 2)}h{_n(fw)}v{_n(fh)}h{_n(-fw)}z"
        (fr_a if i % 2 else fr_b).append(d)
    o.append(f'<path d="{"".join(holes)}" fill="#fff" stroke="none"/>')
    o.append(f'<path d="{"".join(fr_a)}" fill="{C.pat("L")}" stroke="#fff" stroke-width=".5"/>')
    o.append(f'<path d="{"".join(fr_b)}" fill="{C.pat("D")}" stroke="#fff" stroke-width=".5"/>')
    return "".join(o)


def _layout_tall(w, h, seed, density=1.):
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
    o.append(C.dark_ground((px0, py0, pw, ph), "G"))
    cw, ch = pw * .5, ph * .63
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
    o.append(C._clip(C._uid("t", w, h, seed), px0, py0 - top_free, pw, ph + top_free, cv.svg()))
    o.append(_field_cartouche(cx, cy, cw, ch, rng.randrange(1 << 20), "tall"))
    o.append(C.palmette(cx, cy - ch / 2 + 7, min(ch * .2 + top_free, 62), True, rng.randrange(1 << 20)))
    bh = min(16, ph * .05)
    bsvg, bc = C.ribbon_banner(cx, cy + ch * .47, cw * 1.4, bh, .04, rng.randrange(1 << 20))
    o.append(bsvg)
    o.append(f'<path d="{"".join(_d(p, tol=0) for p in _text_on(bc, "50% OFF", bh * .56))}" '
             f'stroke="#000" stroke-width="1.5" fill="none"/>')
    py = py0 + ph - ped_h * .3 + 4 if frieze else h - ped_h
    p, tab = C.pedestal(0, py, w, ped_h, rng.randrange(1 << 20))
    o.append(p)
    o.append(_tablet_film(*tab))
    fy = py + ped_h
    fh = h - fy
    if fh > 14:
        o.append(C.dark_ground((w * .06, fy, w * .88, fh - 2), "G"))
        o.append(C._clip(C._uid("f", w, h, seed), w * .06, fy, w * .88, fh - 2,
                         C.scroll_band(w * .06, fy, w * .88, fh - 2, rng.randrange(1 << 20), fh * 1.2,
                                       r_scale=1.15, n=2)))
        o.append(C.palmette(w / 2, fy + 1, fh * .85, False, rng.randrange(1 << 20)))
        o.append(f'<path d="M{_n(w * .06)},{_n(h - 1.5)}h{_n(w * .88)}" stroke="#000" stroke-width="1"{C._CR}/>')
    return "".join(o)


def plate(w, h, ctx):
    ctx = ctx or {}
    seed = sum(map(ord, ctx.get("date", ""))) + 7 * int(ctx.get("sheet", 0) or 0)
    if h < 110:
        body = _layout_band(w, h, seed)
    elif h <= 260:
        body = _layout_medium(w, h, seed)
    else:
        body = _layout_tall(w, h, seed, .8 if h < 500 else 1.)
    # light ruled paper ground under everything: no bare white survives between the pieces
    body = f'<path d="M0,0h{_n(w)}v{_n(h)}h{_n(-w)}z" fill="{C.pat("L")}" stroke="none"/>' + body
    return C.svg_doc(w, h, body)
