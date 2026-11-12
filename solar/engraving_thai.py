"""Thai engraving for the Kindle morning paper: lai thai, kranok flames, nielloware (khrueang thom)
bands, a temple gable (na ban) with chofa, lai thai rosettes and six bulino-style vignettes.

Same cabinet as solar/kindle_evening.py: three line weights (W0 hairline .6, W1 rule 1, W2 heavy
rule 1.6), K = 'stroke="#000"', coordinates rounded to one decimal by _n(), tone only from hatching
patterns (never grey, opacity, gradients or blur). Every function returns an SVG string. No SVG
`transform` attributes anywhere: motifs are drawn once in local coordinates and baked onto the page
by _tp() (an affine applied to the path data), or placed with <use x= y=> (a translation that the
CSS reset `transform:none !important` cannot touch).

Seeds: pass seed_from_date(date) so every morning's ornament differs subtly (tip flick, unit pitch,
petal counts, tooth shape) while the design stays the same. Each seed also hides a few small
personal touches (a surfboard in one kranok flame, a "P" in a corner, crossed drumsticks in a
rosette, a dog among the garuda's feathers...) for a close look.

Public API
    seed_from_date(d=None) -> int
    kranok_border(width, height, seed, band=22) -> <svg>   full frame, corners, mid-side medallions
    kranok_band(width, height, seed) -> <svg>               horizontal divider
    gable_frame(width, height, seed) -> <svg>               na ban header; title area left blank
    gable_title_box(width, height) -> (x, y, w, h)          where to set the title inside it
    rosette(seed, size) -> <svg>                            lai thai rosette for corners/medallions
    thai_vignettes(seed=None) -> {key: <svg viewBox 0 0 120 80>}
        keys: wat_arun, elephant, naga, garuda, lotus_bud, sala (ids prefixed with the key)
"""
import datetime
import math
import random
import re

W0, W1, W2 = .6, 1, 1.6
K = 'stroke="#000"'
XL = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'


def _n(x):
    s = f"{x:.1f}"
    if s == "-0.0":
        return "0"
    return s[:-2] if s.endswith(".0") else s


def seed_from_date(d=None):
    """The day's seed: same all day, different every day."""
    d = d or datetime.date.today()
    return d.year * 10000 + d.month * 100 + d.day


# ------------------------------------------------------------------------------------- geometry
def _mat(tx=0., ty=0., rot=0., sx=1., sy=None):
    """Affine (a, b, c, d, e, f): x' = a x + c y + e, y' = b x + d y + f. Scale, then rotate, then move."""
    sy = sx if sy is None else sy
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (c * sx, s * sx, -s * sy, c * sy, tx, ty)


def _mul(m1, m2):
    """m1 after m2."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _ap(m, x, y):
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


_TOK = re.compile(r"[MLCQZ]|-?(?:\d+\.?\d*|\.\d+)")


def _tp(d, m):
    """Bake an affine into absolute path data (M L C Q Z only)."""
    out, nums = [], []

    def flush():
        for i in range(0, len(nums) - 1, 2):
            x, y = _ap(m, nums[i], nums[i + 1])
            out.append(f"{_n(x)},{_n(y)}")
        nums.clear()

    for t in _TOK.findall(d):
        if t in "MLCQZ":
            flush()
            out.append(t)
        else:
            nums.append(float(t))
    flush()
    s = " ".join(out)
    return re.sub(r"([MLCQZ]) ", r"\1", s).replace(" -", "-")


def _poly(pts, close=True):
    d = "M" + " ".join(f"{_n(x)},{_n(y)}" for x, y in pts)
    return d + ("Z" if close else "")


def _circ(cx, cy, r, fill="#fff", sw=W0, stroke=True):
    st = f' {K} stroke-width="{_n(sw)}"' if stroke else ""
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{fill}"{st}/>'


def _svg(w, h, inner, cls="", vb=None):
    return (f'<svg {XL} class="kthai {cls}" width="{_n(w)}" height="{_n(h)}" '
            f'viewBox="{vb or f"0 0 {_n(w)} {_n(h)}"}" aria-hidden="true">{inner}</svg>')


# ------------------------------------------------------------------------------- tone patterns
def _patterns(p):
    """Engraver's tones, all black lines >= .6 on white, seamless, no patternTransform.
    {p}h light horizontal, {p}hd dense horizontal, {p}v vertical, {p}d 45deg, {p}b -45deg, {p}x cross,
    {p}xd dense cross, {p}s stipple."""
    def diag(s, back=False):
        if back:
            return f"M0,0L{_n(s)},{_n(s)}M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(s * 1.5)}M{_n(s / 2)},{_n(-s / 2)}L{_n(s * 1.5)},{_n(s / 2)}"
        return f"M0,{_n(s)}L{_n(s)},0M{_n(-s / 2)},{_n(s / 2)}L{_n(s / 2)},{_n(-s / 2)}M{_n(s / 2)},{_n(s * 1.5)}L{_n(s * 1.5)},{_n(s / 2)}"
    pat = '<pattern id="{id}" width="{w}" height="{h}" patternUnits="userSpaceOnUse">{c}</pattern>'
    L = f'fill="none" {K} stroke-width=".6"'
    return "".join([
        pat.format(id=p + "h", w=4, h=2.6, c=f'<path d="M0,1.3H4" {L}/>'),
        pat.format(id=p + "hl", w=4, h=3.6, c=f'<path d="M0,1.8H4" {L}/>'),
        pat.format(id=p + "hd", w=4, h=1.8, c=f'<path d="M0,.9H4" {L}/>'),
        pat.format(id=p + "v", w=2.4, h=4, c=f'<path d="M1.2,0V4" {L}/>'),
        pat.format(id=p + "d", w=3, h=3, c=f'<path d="{diag(3)}" {L}/>'),
        pat.format(id=p + "b", w=3, h=3, c=f'<path d="{diag(3, True)}" {L}/>'),
        pat.format(id=p + "x", w=3, h=3, c=f'<path d="{diag(3)}{diag(3, True)}" {L}/>'),
        pat.format(id=p + "xd", w=2.2, h=2.2, c=f'<path d="{diag(2.2)}{diag(2.2, True)}" {L}/>'),
        pat.format(id=p + "s", w=3, h=3, c='<circle cx=".75" cy=".75" r=".45"/><circle cx="2.25" cy="2.25" r=".45"/>'),
    ])


# ------------------------------------------------------------------------------------ motifs
# The kranok (lai kranok sam tua): base at (0,0), belly along +x, the flame tip flicking up and back at
# about (18,-13), two licks (yod) along the back, an eye-curl at the base and the inner son line.
# Width 20.5, height 13.
def _kranok_paths(var=0):
    tip = [(-13, 17.6), (-13.6, 16.6), (-12.4, 18.6)][var % 3]
    d = (f"M0,0C6,1 13,.4 17,-2.6C20.4,-5.2 21,-9.6 {tip[1]},{tip[0]}C18,-10.6 17.4,-8.8 15.4,-7.8"
         "C16.2,-8.8 16.2,-10 15.2,-11C14.6,-8.6 13.4,-7 11.2,-6.4C11.8,-7.2 11.8,-8.4 10.8,-9.2"
         "C10.2,-7.2 8.6,-5.8 6.6,-5.6C4,-5.4 1,-5.6 .2,-3.6C-.2,-2.4-.3,-1.2 0,0Z")
    inner = ("M4.8,-2.6C4.8,-3.6 3.4,-3.8 2.8,-3C2.2,-2.2 2.8,-1 4.2,-1C8,-1 13.4,-1.6 16.4,-4.4"
             "C18.2,-6.2 18.6,-8.6 18,-10.8M7.4,-3.4C10.6,-3.6 13.4,-4.4 15,-5.8")
    return d, inner


# A tiny surfboard (Easter egg) laid along a flame's son line, local kranok coordinates.
_SURF = "M5.6,-2.2C8,-3.4 12.4,-3.6 15.4,-3C12.6,-1.8 8.4,-1.2 5.6,-2.2Z"
_SURF_STRINGER = "M6.6,-2.3C9.4,-2.8 12,-2.9 14.4,-2.9"


def _kranok(m, fill="#fff", line=None, var=0, lw=None, surf=False, ink="#000"):
    """A kranok baked by matrix m. In niello (fill white on a black ground) the son lines are black;
    pass fill="#000", ink="#fff" for a black flame with white son lines."""
    d, inner = _kranok_paths(var)
    sc = math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))
    lw = lw or max(.6, .55 * sc)
    out = f'<path d="{_tp(d, m)}" fill="{fill}"' + (f' {K} stroke-width="{_n(line)}"/>' if line else '/>')
    if surf:
        out += (f'<path d="{_tp(inner.split("M7.4")[0], m)}" fill="none" stroke="{ink}" stroke-width="{_n(lw)}"/>'
                f'<path d="{_tp(_SURF, m)}" fill="{ink}"/>')
    else:
        out += f'<path d="{_tp(inner, m)}" fill="none" stroke="{ink}" stroke-width="{_n(lw)}"/>'
    return out


def _prajam(cx, cy, r, ground="#000", petal="#fff", rot=45, eye=True):
    """Dok prajam: four pointed petals in a lozenge, each with a son line."""
    g = ""
    for i in range(4):
        m = _mat(cx, cy, rot + 90 * i, r / 10)
        g += f'<path d="{_tp("M1.2,0C2.4,-3.6 6,-3.8 10,0C6,3.8 2.4,3.6 1.2,0Z", m)}" fill="{petal}"/>'
        g += f'<path d="{_tp("M3,0C5,-.6 6.8,-.4 8.2,0", m)}" fill="none" stroke="{ground}" stroke-width="{_n(max(.6, r * .07))}"/>'
    if eye:
        g += _circ(cx, cy, r * .2, petal, stroke=False) + _circ(cx, cy, max(.6, r * .08), ground, stroke=False)
    return g


def _p_mark(x, y, s, fill="#000"):
    """A tiny engraved 'P' monogram, s px tall, top-left at (x, y)."""
    w = s * .62
    return (f'<path d="M{_n(x + s * .12)},{_n(y + s)}V{_n(y)}H{_n(x + w * .55)}'
            f'C{_n(x + w * 1.05)},{_n(y)} {_n(x + w * 1.05)},{_n(y + s * .52)} {_n(x + w * .55)},{_n(y + s * .52)}H{_n(x + s * .12)}" '
            f'fill="none" stroke="{fill}" stroke-width="{_n(max(.6, s * .16))}"/>')


# ------------------------------------------------------------------------------- the border
def _field_unit(U, k, top, bot, var, flip=False, surf=False):
    """One unit of the interlocking run, local (u along, v across), u in [0, U): a standing kranok and
    its twin turned half round, their tips hooked into each other (kranok khao kan), and a seed pearl
    in the gap before the next pair."""
    sx = -1 if flip else 1
    Lk = 20.5 * k
    up = _mat(0, bot, 0, k * sx, k)
    dn = _mat(Lk * sx, top, 0, -k * sx, -k)
    pearl = _circ(sx * (Lk + (U - Lk) / 2), (top + bot) / 2, max(.7, k * 1.4), "#fff", stroke=False)
    return _kranok(up, var=var, surf=surf) + _kranok(dn, var=var) + pearl


def kranok_border(width, height, seed, band=22):
    """A nielloware frame: heavy and hairline rules; a black ground with interlocking white kranok pairs
    running from each corner block to a mid-side cartouche; kra jang teeth along the inner edge; a
    prajam flower in each corner. Tiles to any length: each run's pitch is stretched to hold whole units."""
    rnd = random.Random(seed * 7 + 1)
    W, H, b = float(width), float(height), float(band)
    s = b / 22
    p = f"tkb{seed % 997}-"
    var = rnd.randrange(3)
    top, bot = 3.6 * s, 15 * s         # niello field, across the band
    k = rnd.choice((.6, .62, .64)) * s
    U0 = 20.5 * k + rnd.choice((2.6, 3.2, 3.8)) * s
    cb = bot + 1.1 * s                 # corner block / inner rule line
    tooth = rnd.randrange(2)
    egg = rnd.randrange(3)             # 0 surfboard flame, 1 'P' in a corner, 2 both
    egg_side, egg_corner = rnd.randrange(4), rnd.randrange(4)
    sides = [((1, 0, 0, 1, 0, 0), W), ((0, 1, -1, 0, W, 0), H),
             ((-1, 0, 0, -1, W, H), W), ((0, -1, 1, 0, 0, H), H)]
    M = 2.3 * b                        # mid-side cartouche length
    defs, uses, body, ground = [], [], [], []
    for si, (sm, L) in enumerate(sides):
        lin = sm[:4] + (0, 0)
        half = (L / 2 - M / 2 - 6.4 * s) - cb
        n = max(1, round(half / U0))
        U = half / n
        st = _mul(lin, (U / U0, 0, 0, 1, 0, 0))
        for fl in (0, 1):
            uid = f"{p}u{si}{fl}"
            defs.append(f'<g id="{uid}">{_bake_group(_field_unit(U0, k, top, bot, var, flip=bool(fl)), st)}</g>')
            for i in range(n):
                u = cb + i * U if not fl else L - cb - i * U
                if egg in (0, 2) and si == egg_side and fl == 0 and i == n // 2:
                    m = _mul(sm, _mul((1, 0, 0, 1, u, 0), (U / U0, 0, 0, 1, 0, 0)))
                    body.append(_bake_group(_field_unit(U0, k, top, bot, var, surf=True), m))
                    continue
                x, y = _ap(sm, u, 0)
                uses.append(f'<use xlink:href="#{uid}" x="{_n(x)}" y="{_n(y)}"/>')
        ground.append(_poly([_ap(sm, cb, top), _ap(sm, L - cb, top), _ap(sm, L - cb, bot), _ap(sm, cb, bot)]))
    g = f'<path d="{" ".join(ground)}" fill="#000"/>' + "".join(uses) + "".join(body)
    for si, (sm, L) in enumerate(sides):
        g += _medallion(sm, L / 2, (top + bot) / 2, M / 2, (bot - top) / 2 + 2.4 * s, s)
    for inset, w in ((.8 * s, W2), (2.6 * s, W0), (cb, W1)):
        g += (f'<rect x="{_n(inset)}" y="{_n(inset)}" width="{_n(W - 2 * inset)}" height="{_n(H - 2 * inset)}" '
              f'fill="none" {K} stroke-width="{_n(w)}"/>')
    # kra jang teeth on the inner edge: one pattern per side, pitch stretched to fit the run
    tb, td = cb + .5 * s, 4.6 * s
    for si, (sm, L) in enumerate(sides):
        Lr = L - 2 * cb - 2 * td
        n = max(1, round(Lr / (5.2 * s)))
        P = Lr / n
        lin = sm[:4] + (0, 0)
        tile = _tp(_tooth(P, td, tooth, s), lin)
        box = [_ap(lin, 0, 0), _ap(lin, P, 0), _ap(lin, 0, td), _ap(lin, P, td)]
        dx, dy = -min(q[0] for q in box), -min(q[1] for q in box)
        tw, th = (P, td) if si % 2 == 0 else (td, P)
        c0, c1 = _ap(sm, cb + td, tb), _ap(sm, L - cb - td, tb + td)
        x0, y0, x1, y1 = min(c0[0], c1[0]), min(c0[1], c1[1]), max(c0[0], c1[0]), max(c0[1], c1[1])
        tid = f"{p}t{si}"
        defs.append(f'<pattern id="{tid}" x="{_n(x0)}" y="{_n(y0)}" width="{_n(tw)}" height="{_n(th)}" '
                    f'patternUnits="userSpaceOnUse"><path d="{_tp(tile, (1, 0, 0, 1, dx, dy))}"/></pattern>')
        g += f'<rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(x1 - x0)}" height="{_n(y1 - y0)}" fill="url(#{tid})"/>'
    for ci, (cx, cy, sx, sy) in enumerate(((0, 0, 1, 1), (W, 0, -1, 1), (W, H, -1, -1), (0, H, 1, -1))):
        g += _corner(cx, cy, sx, sy, s, top, bot, cb, p_mark=(egg in (1, 2) and ci == egg_corner))
    return _svg(W, H, f"<defs>{''.join(defs)}</defs>{g}", "kthai-border")


def _bake_group(svg, m):
    """Bake an affine into every path d in an SVG snippet (paths only)."""
    return re.sub(r'd="([^"]+)"', lambda mm: f'd="{_tp(mm.group(1), m)}"', svg)


def _tooth(P, td, kind, s):
    """One kra jang tooth in side-local coords: base along v=0, pointing +v (inward), width P."""
    c = P / 2
    w = min(P * .42, 2.2 * s)
    if kind == 0:   # spearhead with a flicked tip
        d = (f"M{_n(c - w)},0C{_n(c - w * .9)},{_n(td * .45)} {_n(c - w * .2)},{_n(td * .6)} {_n(c + w * .25)},{_n(td)}"
             f"C{_n(c + w * .1)},{_n(td * .6)} {_n(c + w * .95)},{_n(td * .4)} {_n(c + w)},0Z")
    else:           # bud: rounded lotus-petal tooth
        d = (f"M{_n(c - w)},0C{_n(c - w)},{_n(td * .6)} {_n(c - w * .3)},{_n(td * .7)} {_n(c)},{_n(td)}"
             f"C{_n(c + w * .3)},{_n(td * .7)} {_n(c + w)},{_n(td * .6)} {_n(c + w)},0Z")
    return d + f"M{_n(c - .5 * s)},{_n(td * .02)}"  # (no-op move keeps the tile path well formed)


def _medallion(sm, u, v, a, r, s):
    """A pointed (ogee) cartouche across the band at (u, v) of a side: white, double-lined, a prajam inside
    and kranok flames licking out to either side."""
    d = (f"M{-a},0C{-a * .7},{-r * .15} {-a * .45},{-r} 0,{-r}C{a * .45},{-r} {a * .7},{-r * .15} {a},0"
         f"C{a * .7},{r * .15} {a * .45},{r} 0,{r}C{-a * .45},{r} {-a * .7},{r * .15} {-a},0Z")
    m = _mul(sm, (1, 0, 0, 1, u, v))
    d2 = _tp(d, _mul(m, (.86, 0, 0, .8, 0, 0)))
    g = (f'<path d="{_tp(d, m)}" fill="#fff" {K} stroke-width="{W1}"/>'
         f'<path d="{d2}" fill="none" {K} stroke-width="{W0}"/>')
    cx, cy = _ap(m, 0, 0)
    g += _prajam(cx, cy, r * .62, ground="#fff", petal="#000", eye=False) + _circ(cx, cy, max(1, r * .14), "#fff")
    # pearls strung off the cartouche's points onto the niello
    for sx in (1, -1):
        for du, rr in ((2.2, 1.3), (5, .8)):
            x, y = _ap(m, sx * (a + du * s), 0)
            g += _circ(x, y, rr * s, "#fff", stroke=False)
    return g


def _corner(cx, cy, sx, sy, s, top, bot, cb, p_mark=False):
    """Corner block: a niello square where the two fields cross, a white prajam over a black one, and
    in the inner angle a bud with two seeds (or, some mornings, a tiny engraved P)."""
    def P(x, y):
        return cx + sx * x, cy + sy * y
    g = f'<path d="{_poly([P(top, top), P(cb, top), P(cb, cb), P(top, cb)])}" fill="#000"/>'
    m = (top + cb) / 2
    mx, my = P(m, m)
    r = (cb - top) / 2
    g += _prajam(mx, my, r * .98, rot=45)
    g += _prajam(mx, my, r * .48, rot=0, ground="#fff", petal="#000", eye=False) + _circ(mx, my, r * .15, "#fff")
    bx, by = P(cb + 3.4 * s, cb + 3.4 * s)
    if p_mark:
        g += _p_mark(bx - 1.6 * s, by - 2.4 * s, 5 * s)
    else:
        g += _circ(bx, by, 1.5 * s, "#000", stroke=False)
        for tx, ty in (P(cb + 6.6 * s, cb + 1.6 * s), P(cb + 1.6 * s, cb + 6.6 * s)):
            g += _circ(tx, ty, .8 * s, "#000", stroke=False)
    return g


# ------------------------------------------------------------------------------- the rosette
def _drumsticks(cx, cy, r):
    """Easter egg: a pair of drumsticks crossed in an X, tips up."""
    g = ""
    for sgn in (1, -1):
        x0, y0 = cx + sgn * r * .75, cy + r * .75
        x1, y1 = cx - sgn * r * .7, cy - r * .7
        g += f'<path d="M{_n(x0)},{_n(y0)}L{_n(x1)},{_n(y1)}" {K} stroke-width="{_n(max(.7, r * .2))}" stroke-linecap="round"/>'
        g += _circ(x1, y1, max(.5, r * .16), "#000", stroke=False)
    return g


def _rosette_g(cx, cy, R, rnd, egg=False):
    """Lai thai rosette (dok mai thai): a beaded niello ring, a pinwheel of white kranok on black, a white
    disc with a ring of pointed lotus petals, a pollen eye. Returns SVG elements."""
    nk = rnd.choice((8, 10, 12))
    npet = rnd.choice((8, 12))
    tilt = rnd.choice((24, 30, 36))
    var = rnd.randrange(3)
    g = _circ(cx, cy, R, "#000", sw=W1)
    # bead ring
    nb = max(12, int(2 * math.pi * R * .88 / max(2.6, R * .16)))
    rb = R * .89
    for i in range(nb):
        a = 2 * math.pi * i / nb
        g += _circ(cx + rb * math.cos(a), cy + rb * math.sin(a), max(.6, R * .045), "#fff", stroke=False)
    g += _circ(cx, cy, R * .8, "none", sw=max(.6, R * .025)).replace('stroke="#000"', 'stroke="#fff"')
    # pinwheel of kranok
    kk = R * (.36 if nk == 8 else .3 if nk == 10 else .26) / 13
    for i in range(nk):
        a = 360 * i / nk
        ar = math.radians(a)
        bx, by = cx + R * .44 * math.cos(ar), cy + R * .44 * math.sin(ar)
        g += _kranok(_mat(bx, by, a - tilt - 28, kk), var=var)
    # inner disc and lotus petals
    ri = R * .42
    g += _circ(cx, cy, ri, "#fff", sw=max(.6, R * .03))
    for i in range(npet):
        m = _mat(cx, cy, 360 * i / npet - 90, ri / 10)
        g += f'<path d="{_tp("M2.6,0C4,-1.8 6.6,-2.2 9,0C6.6,2.2 4,1.8 2.6,0Z", m)}" fill="#000"/>'
    g += _circ(cx, cy, ri * .3, "#fff", sw=max(.6, R * .03))
    if egg:
        g += _drumsticks(cx, cy, ri * .26)
    else:
        g += _circ(cx, cy, max(.6, ri * .1), "#000", stroke=False)
    return g


def rosette(seed, size):
    """A lai thai rosette, size x size, for corners or medallions. Some seeds hide crossed drumsticks
    in its eye."""
    rnd = random.Random(seed * 13 + 5)
    egg = rnd.random() < .5
    R = size / 2 - .8
    return _svg(size, size, _rosette_g(size / 2, size / 2, R, rnd, egg), "kthai-rosette")


# ------------------------------------------------------------------------------- the divider
def kranok_band(width, height, seed, centre="rosette"):
    """A horizontal divider: a niello field of interlocking kranok pairs running in from both ends to a
    central rosette, ruled above and below, kra jang teeth standing up and hanging down, prajam blocks
    at the ends."""
    rnd = random.Random(seed * 11 + 3)
    W, H = float(width), float(height)
    s = H / 26
    p = f"tkd{seed % 997}-"
    td = 4.2 * s
    top, bot = td + 2.4 * s, H - td - 2.4 * s
    fh = bot - top
    k = fh / 11.4 * rnd.choice((.6, .62, .64))
    var = rnd.randrange(3)
    U0 = 20.5 * k + rnd.choice((2.6, 3.2, 3.8)) * k / .6
    cx, cy = W / 2, H / 2
    R = H / 2 - .4
    eb = fh                          # end block size
    half = cx - R - 4 * s - eb
    n = max(1, round(half / U0))
    U = half / n
    defs, uses = [], []
    for fl in (0, 1):
        uid = f"{p}u{fl}"
        defs.append(f'<g id="{uid}">{_bake_group(_field_unit(U0, k, 0, fh, var, flip=bool(fl)), (U / U0, 0, 0, 1, 0, 0))}</g>')
        for i in range(n):
            x = eb + i * U if not fl else W - eb - i * U
            uses.append(f'<use xlink:href="#{uid}" x="{_n(x)}" y="{_n(top)}"/>')
    g = f'<rect x="{_n(eb)}" y="{_n(top)}" width="{_n(W - 2 * eb)}" height="{_n(fh)}"/>' + "".join(uses)
    for y, w in ((top - 1.1 * s, W1), (bot + 1.1 * s, W1)):
        g += f'<path d="M0,{_n(y)}H{_n(W)}" {K} stroke-width="{w}"/>'
    # teeth above and below via patterns, phase-locked to the centre
    n2 = max(1, round((W - 2 * eb) / (5.2 * s)))
    P = (W - 2 * eb) / n2
    tooth = rnd.randrange(2)
    up = _tp(_tooth(P, td, tooth, s), (1, 0, 0, -1, 0, td))
    dn = _tooth(P, td, tooth, s)
    defs.append(f'<pattern id="{p}tu" x="{_n(eb)}" y="0" width="{_n(P)}" height="{_n(td)}" patternUnits="userSpaceOnUse"><path d="{up}"/></pattern>'
                f'<pattern id="{p}td" x="{_n(eb)}" y="{_n(H - td)}" width="{_n(P)}" height="{_n(td)}" patternUnits="userSpaceOnUse"><path d="{dn}"/></pattern>')
    g += (f'<rect x="{_n(eb)}" y="0" width="{_n(W - 2 * eb)}" height="{_n(td)}" fill="url(#{p}tu)"/>'
          f'<rect x="{_n(eb)}" y="{_n(H - td)}" width="{_n(W - 2 * eb)}" height="{_n(td)}" fill="url(#{p}td)"/>')
    # end blocks
    for x0 in (0, W - eb):
        g += f'<rect x="{_n(x0)}" y="{_n(top)}" width="{_n(eb)}" height="{_n(fh)}"/>' + _prajam(x0 + eb / 2, cy, fh / 2 * .96)
    # the central rosette sits on a white ground that interrupts the field and rules
    g += _circ(cx, cy, R + 2.6 * s, "#fff", stroke=False)
    if centre == "rosette":
        g += _rosette_g(cx, cy, R, random.Random(seed * 17), egg=rnd.random() < .35)
    else:
        g += _circ(cx, cy, R, "#000", sw=W1) + _prajam(cx, cy, R * .9, rot=0)
    for sx in (1, -1):
        g += _circ(cx + sx * (R + 2.2 * s), cy, 1.1 * s, "#000", stroke=False)
    return _svg(W, H, f"<defs>{''.join(defs)}</defs>{g}", "kthai-band")


# ------------------------------------------------------------------------------- the gable
# Chofa: the slender bird-headed finial on the apex, local (0,0) at the apex, rising to -y, the beak to +x.
_CHOFA = ("M-2.4,0C-2.6,-9-1.8,-19 2,-26.4C4.6,-31.4 9.6,-33.4 13.4,-31C11.6,-30.6 10.2,-30 9.4,-29"
          "C11.4,-28.6 12.6,-27 12.2,-25.4C10.6,-26.8 8.4,-27 6.6,-25.4C3.6,-21.6 2.6,-12 2.6,0Z")
_CHOFA_IN = "M0,-2C0,-10 .6,-18 3.6,-23.6C5.4,-27 8,-29 10.6,-29.6"
# a bai raka fin: base along +x (toward the apex) on the board's outer edge, leaning up-slope, outward = -y
_FIN = "M0,0Q2.4,-1.6 5,-6Q4,-2.6 5.4,0Z"


def _geom(W, H):
    """Shared layout of the gable: scale, base frieze, title panel."""
    s = W / 570
    bh = max(14, round(H * .09))
    yb = H - bh - 2 * s
    th = max(34 * s, H * .3)
    tw = W * .6
    return s, bh, yb, ((W - tw) / 2, yb - th, tw, th)


def gable_title_box(width, height):
    """(x, y, w, h) of the blank title panel inside gable_frame(width, height)."""
    x, y, w, h = _geom(float(width), float(height))[3]
    return (round(x + 5, 1), round(y + 5, 1), round(w - 10, 1), round(h - 10, 1))


def _qb(p0, p1, p2, n):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def _offset(pts, d):
    """Offset a polyline by d along its left normal (screen coords)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        out.append((x - ty / L * d, y + tx / L * d))
    return out


def _seg_dist(px, py, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy or 1
    t = max(0, min(1, ((px - a[0]) * vx + (py - a[1]) * vy) / L2))
    return math.hypot(px - a[0] - t * vx, py - a[1] - t * vy)


def _inside(px, py, poly):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _spiral_pts(cx, cy, R, turns, start, cw, n=None):
    n = n or max(10, int(turns * 16))
    out = []
    for i in range(n + 1):
        t = i / n
        th = start + cw * 2 * math.pi * turns * t
        r = R * (1 - .8 * t) ** 1.1
        out.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return out


def _scroll(cx, cy, R, start, cw, var, surf=False):
    """Lai kranok plew: a spiralling stem (white, edged black) ending in a curl, kranok flames
    sprouting from its outer side and shrinking toward the eye."""
    pts = _spiral_pts(cx, cy, R * .74, 1.2, start, cw)
    d = _poly(pts, False)
    sw = max(1.4, R * .11)
    g = (f'<path d="{d}" fill="none" {K} stroke-width="{_n(sw + 1.4)}" stroke-linecap="round"/>'
         f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{_n(sw)}" stroke-linecap="round"/>')
    nfl = 3 if R > 11 else 2
    for j in range(nfl):
        t = .04 + j * .22
        i = int(t * (len(pts) - 1))
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        size = R * (1 - .7 * t) / 20.5 * 1.05
        m = _mat(x0, y0, ang, size, size * cw)
        g += _kranok(m, fill="#fff", line=W0, var=var, lw=W0, surf=surf and j == 0)
    ex, ey = pts[-1]
    g += _circ(ex, ey, max(1, R * .09), "#000", stroke=False)
    return g


def _tier(cx, ya, xe, ye, tv, sag):
    """Left board of one roof tier: outer and inner edge polylines from the apex to the eave."""
    p1 = (cx - (cx - xe) * sag, ye - (ye - ya) * .12)
    outer = _qb((cx, ya), p1, (xe, ye), 16)
    inner = _offset(outer, -tv)
    return outer, inner


def gable_frame(width, height, seed):
    """A temple gable (na ban) header. Two stacked roof tiers, each with sagging niello bargeboards
    (lamyong) combed with bai raka fins, a chofa on its apex and hang hong flames curling up at its
    eaves; the front tympanum filled with spiralling kranok scrolls on a cross-hatched ground around
    a central rosette; below it a lintel, two lotus-capital pillars and a redented (yo mum) title
    panel left blank; a kranok divider along the base. gable_title_box() gives the panel."""
    rnd = random.Random(seed * 5 + 9)
    W, H = float(width), float(height)
    s, bh, yb, (px, py, pw, ph) = _geom(W, H)
    p = f"tkg{seed % 997}-"
    cx = W / 2
    var = rnd.randrange(3)
    sag = rnd.choice((.3, .34, .38))
    tv = 8 * s
    defs = [_patterns(p)]
    # tiers: back (higher, shorter) and front (lower, reaching down beside the panel)
    ya1 = 30 * s
    ya2 = ya1 + max(14 * s, (py - ya1) * .2)
    back = _tier(cx, ya1, W * .1, py - 16 * s, tv * .9, sag)
    front = _tier(cx, ya2, W * .03, py + 3 * s, tv, sag)

    def mirror(pts):
        return [(2 * cx - x, y) for x, y in pts]
    g = ""
    # back tier: its tympanum strip as roof-tile hatching
    bi = back[1]
    strip = bi + mirror(bi)[::-1]
    g += f'<path d="{_poly(strip)}" fill="url(#{p}h)"/>'
    # front tympanum region: under the front inner edges, above the lintel
    fo, fi = front
    lint = py - 7 * s
    reg = [q for q in fi if q[1] <= lint]
    reg = reg + [(reg[-1][0], lint), (2 * cx - reg[-1][0], lint)] + mirror(reg)[::-1]
    g += f'<path d="{_poly(fo + mirror(fo)[::-1])}" fill="#fff"/>'
    g += f'<path d="{_poly(reg)}" fill="url(#{p}x)"/>'
    defs.append(f'<clipPath id="{p}c"><path d="{_poly(reg)}"/></clipPath>')
    # rosette under the apex
    top_in = fi[0][1]
    rR = min((lint - top_in) * .3, 24 * s)
    rcy = top_in + (lint - top_in) * .52
    # scrolls packed into the left half, mirrored
    edges = [(reg[i], reg[i - 1]) for i in range(len(reg))]

    def clear(x, y):
        if not _inside(x, y, reg):
            return -1
        d = min(_seg_dist(x, y, a, b) for a, b in edges)
        d = min(d, math.hypot(x - cx, y - rcy) - rR - 3.5 * s, cx - x + 1.5 * s)
        return d
    cand = []
    st = 2.5 * s
    for i in range(int(cx / st)):
        for j in range(int((lint - top_in) / st) + 1):
            x, y = i * st, top_in + j * st
            c = clear(x, y)
            if c > 4 * s:
                cand.append([x, y, c])
    scrolls = []
    Rmax = min(22 * s, (lint - top_in) * .3)
    while cand and len(scrolls) < 9:
        x, y, c = max(cand, key=lambda q: q[2])
        if c < 5 * s:
            break
        r = min(c, Rmax)
        scrolls.append((x, y, r))
        cand = [[a, b, min(cc, math.hypot(a - x, b - y) - r - 1.6 * s)] for a, b, cc in cand]
        cand = [q for q in cand if q[2] > 4 * s]
    left = ""
    surf_i = rnd.randrange(len(scrolls)) if scrolls and rnd.random() < .5 else -1
    right_extra = ""
    for i, (x, y, r) in enumerate(scrolls):
        cw = 1 if ((x * 7 + y * 3) // 1 + seed) % 2 else -1
        st_ = rnd.uniform(0, 6.28)
        left += _scroll(x, y, r - .4 * s, st_, cw, var)
        if i == surf_i:   # its mirror twin carries the surfboard
            right_extra = (i, _scroll(2 * cx - x, y, r - .4 * s, math.pi - st_, -cw, var, surf=True))
    right = _mirror_use(f"{p}sl", cx) + (right_extra[1] if right_extra else "")  # surf twin over its plain twin
    g += f'<g clip-path="url(#{p}c)"><g id="{p}sl">{left}</g>{right}</g>'
    g += _circ(cx, rcy, rR + 2.2 * s, "#fff", sw=W1) + _rosette_g(cx, rcy, rR, random.Random(seed * 3), egg=rnd.random() < .35)
    # the boards: niello with a white bead line, fins on the outer edge, then chofa and hang hong
    chofa = ""
    for (o, i_), ya, big in ((back, ya1, .85), (front, ya2, 1)):
        g += f'<g id="{p}b{int(big * 10)}">'
        for M in (lambda q: q,):
            oo, ii = M(o), M(i_)
            g += f'<path d="{_poly(oo + ii[::-1])}" fill="#000"/>'
            mid = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(oo, ii)]
            g += f'<path d="{_poly(mid[1:], False)}" fill="none" stroke="#fff" stroke-width="{W0}" stroke-dasharray="2.2 1.4"/>'
            # bai raka fins, leaning toward the apex
            fins = ""
            acc, step = 0, 6.2 * s
            for k in range(len(oo) - 1, 0, -1):
                a, b = oo[k], oo[k - 1]
                seg = math.hypot(b[0] - a[0], b[1] - a[1])
                ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
                while acc < seg:
                    t = acc / seg
                    x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                    flip = 1 if b[0] > a[0] else -1
                    fins += _tp(_FIN, _mat(x, y, ang, 1.1 * s * big, 1.1 * s * big * flip))
                    acc += step
                acc -= seg
            g += f'<path d="{fins}" fill="#000"/>'
            if big == 1:   # rabai: a valance of hanging flame drops under the front eaves, out past the panel
                drops, acc = "", 0
                for k in range(len(ii) - 1, 0, -1):
                    a, b = ii[k], ii[k - 1]
                    seg = math.hypot(b[0] - a[0], b[1] - a[1])
                    while acc < seg:
                        t = acc / seg
                        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                        if x > px - 6 * s:
                            acc = 1e9
                            break
                        if x > a[0] or k < len(ii) - 1 or acc > 6 * s:
                            drops += _tp("M-1.7,0Q-1.3,2.6 0,5Q1.3,2.6 1.7,0Z", _mat(x, y - .4, 0, s * (1.2 if int(acc / (4.6 * s)) % 2 else .8)))
                        acc += 4.6 * s
                    if acc >= 1e9:
                        break
                    acc -= seg
                g += _pth(drops, "#000", 0)
            # hang hong at the eave: a black kranok curling up and out
            ex, ey = oo[-1]
            ix, iy = ii[-1]
            sx = -1 if ex < cx else 1
            if big == 1:   # a temple bell (kradiang) with its bodhi-leaf clapper, hung inside the eave
                bx, by = ix + (cx - ix) * .06, iy - 2 * s
                bm = _mat(bx, by, 0, s)
                g += _pth(_tp("M0,0L0,9", bm), sw=W0)
                g += _pth(_tp("M-2.6,13.4C-2.6,10.4-1.6,9 0,9C1.6,9 2.6,10.4 2.6,13.4Z", bm), "#000", 0)
                g += _pth(_tp("M0,13.4L0,15.4M0,15.4C-2.2,17-1.8,19.6 0,21.4C1.8,19.6 2.2,17 0,15.4Z", bm), "#fff", W0)
            km = _mat((ex + ix) / 2 - sx * 1 * s, max(ey, iy) + 1.5 * s, -14 * sx, 1.25 * s * big * sx, 1.25 * s * big)
            g += _kranok(km, fill="#000", ink="#fff", var=var)
        g += "</g>" + _mirror_use(f"{p}b{int(big * 10)}", cx)
        cm = _mat(cx, ya + 1.5 * s, 0, (1.1 if big < 1 else .7) * s)
        chofa += (f'<path d="{_tp(_CHOFA, cm)}" fill="#000"/>'
              f'<path d="{_tp(_CHOFA_IN, cm)}" fill="none" stroke="#fff" stroke-width="{W0}"/>'
              f'<path d="{_tp("M-7,2C-5,-1.4-2,-2.4 0,-2.4C2,-2.4 5,-1.4 7,2Z", cm)}" fill="#000"/>')
    g += chofa
    # lintel, pillars and the title panel
    g += (f'<rect x="{_n(px - 10 * s)}" y="{_n(lint)}" width="{_n(pw + 20 * s)}" height="{_n(5 * s)}" fill="url(#{p}hd)" {K} stroke-width="{W0}"/>'
          f'<path d="M{_n(px - 12 * s)},{_n(lint)}H{_n(px + pw + 12 * s)}" {K} stroke-width="{W1}"/>')
    for x0 in (px - 9 * s, px + pw + 2 * s):
        g += (f'<rect x="{_n(x0)}" y="{_n(py + 4 * s)}" width="{_n(7 * s)}" height="{_n(yb - py - 4 * s)}" fill="url(#{p}v)" {K} stroke-width="{W0}"/>'
              + f'<path d="{_tp("M-1,0C-1,-2 1,-4 3.5,-4.4C6,-4 8,-2 8,0Z", _mat(x0 - .5 * s, py + 4 * s, 0, s))}" fill="#000"/>')
    g += _yomum(px, py, pw, ph, 6 * s)
    band = kranok_band(W, bh, seed, centre="prajam").replace("<svg ", f'<svg x="0" y="{_n(H - bh)}" ', 1)
    g += band
    return _svg(W, H, f"<defs>{''.join(defs)}</defs>{g}", "kthai-gable")


def _mirror_use(ref, cx):
    """The mirror image of #ref about x = cx. The page reset forbids transform attributes, so this is
    the one place a transform is used, as an inline !important style (which outranks the reset)."""
    return f'<use xlink:href="#{ref}" style="transform:matrix(-1,0,0,1,{_n(2 * cx)},0) !important"/>'


def _yomum(x, y, w, h, r):
    """A redented (yo mum, stepped-corner) panel: white, framed by a rule and a hairline."""
    def path(x, y, w, h, r):
        q = r / 2
        pts = [(x + r, y), (x + w - r, y), (x + w - r, y + q), (x + w - q, y + q), (x + w - q, y + r), (x + w, y + r),
               (x + w, y + h - r), (x + w - q, y + h - r), (x + w - q, y + h - q), (x + w - r, y + h - q), (x + w - r, y + h),
               (x + r, y + h), (x + r, y + h - q), (x + q, y + h - q), (x + q, y + h - r), (x, y + h - r),
               (x, y + r), (x + q, y + r), (x + q, y + q), (x + r, y + q)]
        return _poly(pts)
    return (f'<path d="{path(x, y, w, h, r)}" fill="#fff" {K} stroke-width="{W1}"/>'
            f'<path d="{path(x + 2.4, y + 2.4, w - 4.8, h - 4.8, r)}" fill="none" {K} stroke-width="{W0}"/>')


# =============================================================================== vignettes
# 120 x 80, bulino manner: tone from parallel lines and patterned hatch, every id prefixed by the key.
VB = "0 0 120 80"


def _pth(d, fill="none", sw=W0, extra=""):
    st = f' {K} stroke-width="{_n(sw)}"' if sw else ""
    return f'<path d="{d}" fill="{fill}"{st}{extra}/>'


def _vsvg(key, inner, defs=""):
    return (f'<svg {XL} class="kthai-vig" viewBox="{VB}" width="120" height="80" aria-hidden="true">'
            f'<defs>{_patterns(key + "-")}{defs}</defs>{inner}</svg>')


def _sky_lines(cx, cy, rx, ry, y0, y1, step, rnd, sw=W0, gap_fn=None):
    """Engraved sky: horizontal rules inside an ellipse, ends ragged, spacing widening upward."""
    d, y = [], y1
    while y > y0:
        t = (y - cy) / ry
        if abs(t) < 1:
            hw = rx * math.sqrt(1 - t * t) * rnd.uniform(.86, 1)
            x0, x1 = cx - hw, cx + hw
            if gap_fn:
                for a, b in gap_fn(y, x0, x1):
                    if b - a > 1:
                        d.append(f"M{_n(a)},{_n(y)}H{_n(b)}")
            else:
                d.append(f"M{_n(x0)},{_n(y)}H{_n(x1)}")
        y -= step * (1 + (y1 - y) / (y1 - y0) * .9)
    return f'<path d="{"".join(d)}" {K} stroke-width="{_n(sw)}"/>'


def _water(x0, x1, y0, y1, rnd, cx=60, rx=58, gaps=()):
    """River: broken horizontal strokes, closer together toward the viewer, with wavelet ticks."""
    d, y, i = [], y0, 0
    while y < y1:
        t = (y - y0) / (y1 - y0)
        hw = rx * math.sqrt(max(0, 1 - ((y - y0) / (y1 - y0 + 4)) ** 2 * .9))
        a, b = max(x0, cx - hw), min(x1, cx + hw)
        x = a + rnd.uniform(0, 3)
        while x < b:
            ln = rnd.uniform(6, 20)
            e = min(b, x + ln)
            if not any(g0 < (x + e) / 2 < g1 and gy0 <= y <= gy1 for g0, g1, gy0, gy1 in gaps):
                d.append(f"M{_n(x)},{_n(y)}H{_n(e)}")
            x = e + rnd.uniform(1.2, 3.5)
        y += 2.6 - 1.2 * t
        i += 1
    return f'<path d="{"".join(d)}" {K} stroke-width="{W0}"/>'


# ---------------------------------------------------------------------------- wat arun
def _prang(m, p, var=0):
    """A Khmer-style prang: four steep terraces with balustrades, a corn-cob body of tiers with niches,
    a bulb and a trident spire. Local: base centre (0,0), 50 tall. Light from the left."""
    g = ""
    for j, (hw, y0, y1) in enumerate(((16, -4, 0), (13.4, -8, -4), (11, -12, -8), (9, -15.5, -12))):
        g += _pth(_tp(f"M{-hw},{y1}L{-hw + .8},{y0}L{hw - .8},{y0}L{hw},{y1}Z", m), "#fff", W0)
        g += _pth(_tp(f"M{hw * .3},{y1}L{hw * .3},{y0}L{hw - .8},{y0}L{hw},{y1}Z", m), f"url(#{p}v)", 0)
        g += _pth(_tp(f"M{-hw + .8},{y0 + 1}L{hw - .8},{y0 + 1}", m), sw=W0)
        g += _pth(_tp(f"M-1.4,{y1}L-1.4,{y0 + 1}L1.4,{y0 + 1}L1.4,{y1}Z", m), "#000", 0) if j < 3 else ""
    y_f, y_n = -15.5, -42

    def hw(y):
        t = (y_f - y) / (y_f - y_n)
        return 1.3 + 6.4 * math.cos(t * math.pi / 2) ** .75 + 1.2 * math.sin(t * math.pi) * (1 - t)
    ys = [y_f + (y_n - y_f) * i / 18 for i in range(19)]
    right = [(hw(y), y) for y in ys][::-1]
    g += _pth(_tp(_poly([(-hw(y), y) for y in ys] + right), m), "#fff", W1)
    g += _pth(_tp(_poly([(hw(y) * .25, y) for y in ys] + right), m), f"url(#{p}v)", 0)
    g += _pth(_tp(_poly([(hw(y) * .7, y) for y in ys] + right), m), f"url(#{p}hd)", 0)
    nt = 8
    for i in range(1, nt + 1):
        y = y_f + (y_n - y_f) * i / nt
        w = hw(y)
        g += _pth(_tp(f"M{-w},{y}Q0,{y + 1.2} {w},{y}", m), sw=.8 if i % 2 else W0)
        ny = y - (y_n - y_f) / nt / 2
        if i < nt:
            nw = max(.5, hw(ny) * .17)
            g += _pth(_tp(f"M{-nw},{ny + 1}L{-nw},{ny - .2}Q0,{ny - 1.6} {nw},{ny - .2}L{nw},{ny + 1}Z", m), "#000", 0)
    g += _pth(_tp("M-1.8,-42C-2.4,-44-1,-45.4 0,-45.8C1,-45.4 2.4,-44 1.8,-42Z", m), "#000", 0)
    g += _pth(_tp("M0,-45.8L0,-51M-1.4,-49.4Q-1.4,-47.6 0,-47.6Q1.4,-47.6 1.4,-49.4", m), sw=.8)
    return g


def _longtail(x, y, rnd, surf=False):
    """A long-tail boat (ruea hang yao) heading left: high garlanded prow, boatman at the stern, the
    engine's long shaft trailing into a plume of spray."""
    g = ""
    hull = f"M{x - 27},{y - 9}C{x - 24},{y - 3} {x - 18},{y + 1} {x - 8},{y + 1.4}L{x + 10},{y + 1}C{x + 13},{y + .6} {x + 15},{y - .4} {x + 16},{y - 2}L{x - 14},{y - 2}C{x - 19},{y - 2.6} {x - 23},{y - 4.4} {x - 27},{y - 9}Z"
    g += _pth(_tp(hull, (1, 0, 0, 1, 0, 0)), "#000", .6)
    g += _pth(f"M{_n(x - 22)},{_n(y - 3.4)}C{_n(x - 17)},{_n(y - .6)} {_n(x - 4)},{_n(y - .2)} {_n(x + 14)},{_n(y - 1)}", sw=W0).replace(K, 'stroke="#fff"')
    # garland at the prow
    g += _circ(x - 26.4, y - 9.4, 1, "#fff", sw=.6)
    # passengers' heads and a canopy pole
    for dx in (-12, -7, -2):
        g += _circ(x + dx, y - 3.4, 1, "#000", stroke=False)
    # boatman
    bx = x + 12
    g += _pth(f"M{_n(bx)},{_n(y - 2)}L{_n(bx + .6)},{_n(y - 7)}M{_n(bx + .6)},{_n(y - 6)}L{_n(bx + 3)},{_n(y - 3.6)}", sw=1)
    g += _pth(f"M{_n(bx - 1.6)},{_n(y - 7.6)}Q{_n(bx + .6)},{_n(y - 9.6)} {_n(bx + 2.8)},{_n(y - 7.6)}Z", "#000", 0)
    # engine and shaft with spray
    g += f'<rect x="{_n(bx + 1.6)}" y="{_n(y - 4.6)}" width="3" height="2.2" fill="#000"/>'
    g += _pth(f"M{_n(bx + 3)},{_n(y - 3.4)}L{_n(bx + 15)},{_n(y + 2.6)}", sw=.8)
    spray = "".join(_circ(bx + 15 + rnd.uniform(-1, 4), y + 2 + rnd.uniform(-2.6, .6), rnd.choice((.35, .45)), "#000", stroke=False) for _ in range(9))
    g += spray
    if surf:   # a surfboard riding along the gunwale
        g += _pth(f"M{_n(x - 13)},{_n(y - 3)}C{_n(x - 10)},{_n(y - 4.6)} {_n(x - 2)},{_n(y - 4.6)} {_n(x + 2)},{_n(y - 3)}Z", "#fff", .6)
    # reflection of the hull
    g += _pth(f"M{_n(x - 20)},{_n(y + 3)}H{_n(x + 8)}M{_n(x - 16)},{_n(y + 4.6)}H{_n(x + 4)}", sw=W0)
    return g


def _vig_wat_arun(rnd, eggs):
    p = "wat_arun-"
    g = ""
    # dawn: rays from behind the prang, then sky rules
    cx, cy = 60, 30
    rays = ""
    for i in range(29):
        a = math.radians(184 + i * 172 / 28)
        r0, r1 = 14, 60 if i % 2 else 48
        rays += f"M{_n(cx + r0 * math.cos(a))},{_n(cy + r0 * math.sin(a))}L{_n(cx + r1 * math.cos(a))},{_n(cy + r1 * math.sin(a) * .8)}"
    defs = f'<clipPath id="{p}sky"><path d="M2,54C2,20 30,2 60,2C90,2 118,20 118,54Z"/></clipPath>'
    g += f'<g clip-path="url(#{p}sky)"><path d="{rays}" {K} stroke-width="{W0}"/>'
    g += _sky_lines(60, 54, 60, 52, 34, 53, 2.2, rnd) + "</g>"
    g += _circ(cx, cy, 11, "#fff", stroke=False) + _circ(cx, cy, 11, "none", sw=W0)
    # the far bank: trees as stippled mounds, a gallery wall
    g += _pth("M4,54C10,50 16,51 20,52C24,49 28,50 32,52L88,52C92,49 98,50 102,52C106,50 112,51 116,54Z", f"url(#{p}s)", 0)
    g += _pth("M18,54L18,51L102,51L102,54Z", "#fff", W0) + _pth("M18,52.4H102", sw=W0)
    for x in range(20, 101, 3):
        g += _pth(f"M{x},52.6V54", sw=W0)
    # prangs: small, small, then the great central one
    g += _prang(_mat(30, 54, 0, .5), p) + _prang(_mat(90, 54, 0, .5), p)
    g += _prang(_mat(60, 54.4, 0, .98), p)
    # bank line and river
    g += _pth("M2,54.6H118", sw=W1)
    g += _water(2, 118, 57, 80, rnd, gaps=((44, 76, 56, 70),))
    # the prang's broken reflection
    refl = ""
    for i, y in enumerate(range(57, 72, 2)):
        w = 9 - i * .9
        refl += f"M{_n(60 - w + rnd.uniform(-1, 1))},{y}H{_n(60 - w * .2)}M{_n(60 + w * .1)},{y}H{_n(60 + w + rnd.uniform(-1, 1))}"
    g += f'<path d="{refl}" {K} stroke-width=".8"/>'
    g += _longtail(40, 70, rnd, surf=eggs.get("boat_surf"))
    return _vsvg("wat_arun", g, defs)


# ---------------------------------------------------------------------------- elephant
_ELE = ("M37,14C42,13.6 46,16 49,18.6C58,14 72,13 82,18C89,22 93,32 92,44C92,52 91,62 91,70L81,70C81,64 80.6,59 80,55"
        "C74,56.6 64,57 59,56C58.6,61 58.6,66 58.6,70L47,70C47,64 46,56 45,50C43,49 41,48 39.6,46.6"
        "C37.6,47.6 36.4,50 36.4,54C36.6,58 37.6,61 36,64C34.4,66.4 31,66 30.6,63.4C30.4,62 31.6,61 32.6,61.6"
        "C33.4,59 32.6,55 31.6,51C30.2,45 28.8,38 29.2,31C29.6,25 31,17.6 37,14Z")
_EAR = "M41,22C50,21 54,30 51,40C49,45 44,45 42.4,41C41.8,37 43,33 42,28C41.6,26 41,24 41,22Z"
_CLOTH = "M51,17.4C60,15.4 72,15.6 82,19.4C84,26 84.4,36 83,44C74,46.4 61,46.4 52,44.6C50.6,36 50.4,26 51,17.4Z"


def _vig_elephant(rnd, eggs):
    p = "elephant-"
    defs = f'<clipPath id="{p}body"><path d="{_ELE}"/></clipPath>'
    g = ""
    # distant palms and a chedi on the horizon, then the ground
    g += _pth("M4,58H116", sw=W0)
    g += _pth("M100,58L100,52L103,52L103,58ZM101.5,52L101.5,44M99.4,50Q101.5,47 103.6,50", "#fff", W0)
    g += _pth("M101.5,44C100.6,47 99.6,49 99.4,50L103.6,50C103.4,49 102.4,47 101.5,44Z", "#000", 0)
    for px_, ph_ in ((10, 22), (17, 17), (110, 19)):
        g += _pth(f"M{px_},58Q{px_ + 1},{58 - ph_ / 2} {px_},{58 - ph_}", sw=.8)
        fr = "".join(f"M{px_},{58 - ph_}q{_n(dx * .5)},{_n(-2 + abs(dx) * .3)} {_n(dx)},{_n(abs(dx) * .5 - 1)}" for dx in (-5, -3.4, -1.4, 1.4, 3.4, 5))
        g += _pth(fr, sw=W0)
    g += _pth("M4,61.4H116M4,65.2H116", sw=W0).replace("H116M4,65.2", "H24M98,61.4H116M4,65.2")
    g += _pth("M8,70.4H112", sw=W1)
    sh = "".join(f"M{_n(40 + i * 1.5 + rnd.uniform(-1, 1))},{_n(71.6 + i * 1.6)}H{_n(98 - i * 2 + rnd.uniform(-1, 1))}" for i in range(4))
    g += f'<path d="{sh}" {K} stroke-width="{W0}"/>'
    tufts = "".join(f"M{x},{70.4}l{rnd.choice((-1, 1)) * .8},-2.2" for x in range(12, 110, 5) if not 28 < x < 94)
    g += f'<path d="{tufts}" {K} stroke-width="{W0}"/>'
    # far legs, in shadow
    g += _pth("M61,54C61,60 62,66 62,70L69,70C69,64 69,58 70,54Z", f"url(#{p}b)", W0)
    g += _pth("M75,54C76,60 76,66 76,70L82,70L82,58Z", f"url(#{p}b)", W0)
    # body, modelled with horizontal rules and a crosshatched belly
    g += _pth(_ELE, "#fff", W1)
    g += f'<g clip-path="url(#{p}body)">'
    arcs = "".join(f"M{_n(x)},12Q{_n(x - 5 + (x - 28) * .06)},40 {_n(x + 1)},72" for x in [30 + i * 2.6 for i in range(25)] if x > 44 or x < 34)
    g += f'<path d="{arcs}" fill="none" {K} stroke-width="{W0}"/>'
    g += _pth("M44,47C56,53 74,53 93,42L93,58C80,58 60,58 44,52Z", f"url(#{p}d)", 0)
    g += _pth("M84,20C90,26 93,36 92,46L86,50Z", f"url(#{p}d)", 0)
    g += _pth("M52,56L52,72L59,72L59,56ZM85,52L85,72L92,72L92,52Z", f"url(#{p}v)", 0)
    g += "</g>"
    # trunk wrinkles, eye, tusk
    g += "".join(_pth(f"M{_n(29.6 + i * .25)},{_n(40 + i * 3.2)}q{_n(1.6 + i * .1)},.9 {_n(3 + i * .2)},0", sw=W0) for i in range(6))
    g += _pth("M39.6,46.8C37,49 33.4,50.2 30.4,49.4C33.4,48.6 36,47 38.4,45Z", "#fff", W0)
    g += _pth("M34,28.6q1.6,-1.2 3,0q-1.4,1.1 -3,0Z", "#000", .6)
    # ear: hatched flap with a fringe line
    g += _pth(_EAR, f"url(#{p}b)", W0) + _pth("M42.6,24C48,26 50,33 48,40", sw=W0)
    # headdress: a net over the brow, a crown knob and a pendant
    g += _pth("M30,27C31,21 35,18.6 41,19.2C40,23 37,26 30,27Z", f"url(#{p}x)", W0)
    g += _circ(36.6, 17.6, 1.4, "#000", stroke=False) + _circ(30.6, 30.4, .9, "#000", stroke=False)
    # caparison: white cloth, kranok-flame border, tassel fringe, the howdah (busabok) above
    g += _pth(_CLOTH, "#fff", W1)
    g += _pth("M53,40.2C61,42 74,42 82.4,40", sw=W0) + _pth("M52.4,44.6C61,46.4 74,46.4 83,44L82.4,40C74,42 61,42 53,40.2Z", "#000", 0)
    for i in range(9):
        x = 54.4 + i * 3.4
        g += _kranok(_mat(x, 44.6 - .3 * math.sin(i), 0, .16), var=1)
        g += _pth(f"M{_n(x + 1.6)},{_n(46 + .2 * math.sin(i))}l0,2.4", sw=W0) + _circ(x + 1.6, 48.8, .6, "#000", stroke=False)
    g += _pth("M53.6,20.4C61,18.6 72,18.8 80.6,22C82.2,28 82.4,34 81.4,38.6C73,40.6 61,40.6 54.2,39C53,33 53,26 53.6,20.4Z", f"url(#{p}s)", W0)
    g += _pth("M56,23C62,21.6 71,21.8 78.4,24.4C79.6,29 79.6,33 79,36.4C72,38 62,38 56.4,36.8C55.6,32 55.4,27 56,23Z", "#fff", W0)
    g += _prajam(67, 30.4, 6.4, ground="#fff", petal="#000", eye=False) + _circ(67, 30.4, 1.2, "#fff")
    if eggs.get("P"):
        g += _p_mark(65.6, 28.8, 3.2, "#fff")
    g += _pth("M53,20.6C61,18.8 72,19 81,22", sw=W0)
    # busabok: plinth, posts, tiered roof, spire
    g += _pth("M57,16.4L57,13L77,13L77,17.6Z", "#fff", W0) + _pth("M66,13L77,13L77,17.6L66,16.6Z", f"url(#{p}v)", 0)
    g += _pth("M58.6,13V7M75.4,13V7M63,13V8.4M71,13V8.4", sw=.8)
    g += _pth("M55,7.6L67,1.6L79,7.6Z", "#fff", W0) + _pth("M67,1.6L79,7.6L67,7.6Z", f"url(#{p}h)", 0)
    g += _pth("M55,7.6q-1.6,-.6 -2.2,-2.4M79,7.6q1.6,-.6 2.2,-2.4M67,1.6L67,-.2", sw=.8)
    # tail
    g += _pth("M92,34C94,40 95,46 94.6,52", sw=W0) + _pth("M94.6,52l-.8,3l1.6,0Z", "#000", .6)
    # toenails
    for x in (48, 51, 54, 82.4, 85.4, 88.4):
        g += _pth(f"M{x},70q1.2,-1.6 2.4,0", sw=W0)
    return _vsvg("elephant", g, defs)


# ---------------------------------------------------------------------------- naga
_NH_UP = ("M60,16C54,13 48,13.6 44,16.6C40,15 34,15.6 30,17.6C26,18.6 23,19.6 22,21.8C21,24 22,26 24,26"
          "C30,27.6 38,28.8 46.4,29.6C50,26 56,22 60,16Z")
_NH_JAW = "M46.4,31C40,31.8 33,32.4 28,31.8C25,31.6 23.6,33.6 25.4,35.4C30,37.6 40,38.4 50,40C49,36 48,33 46.4,31Z"
_NH_MOUTH = "M24.6,26.4C30,28 38,29.2 46.4,29.8L46.4,31C40,31.8 33,32.4 28,31.8C26.6,31.6 25.4,31.6 24.6,31Z"


def _naga_head(m, tone="#fff", var=0, crest=True):
    """A naga head in profile, facing left, snout curling up, jaws open with fangs, a flame crest down
    the back of the crown. Local coordinates as drawn at full size (snout ~22, crown ~60)."""
    g = ""
    if crest:
        for i, (x, y, a, sc) in enumerate(((47, 15.4, -40, .62), (54, 14.6, -18, .7), (61, 18, 6, .66), (66, 25, 30, .6), (69.4, 33, 52, .52), (71, 41, 70, .44))):
            g += _kranok(_mul(m, _mat(x, y, a, sc)), fill="#000", ink="#fff", var=var, lw=.6)
    g += _pth(_tp(_NH_MOUTH, m), "#000", 0)
    for fx in (27, 31, 35):  # fangs
        g += _pth(_tp(f"M{fx},27.1L{fx + 1.2},30.2L{fx + 2.2},27.5Z", m), "#fff", 0)
    g += _pth(_tp(_NH_UP, m), tone, W1) + _pth(_tp(_NH_JAW, m), tone, W1)
    # the nose curl, brow and eye, lip ridge, jaw beard
    g += _pth(_tp("M24.4,25C26.6,24.8 27.2,22.4 25.6,21.6C24.4,21 23.4,22.4 24.6,23.2", m), sw=.8)
    g += _pth(_tp("M48.6,17.6C44,18 41,19.4 39.6,22.4C42,20.4 45,20 48,21", m), "#000", 0)
    g += _pth(_tp("M40.6,22.6Q43.6,21 46.6,23Q43.6,24.6 40.6,22.6Z", m), "#fff", W0)
    x, y = _ap(m, 43.6, 22.8)
    g += _circ(x, y, max(.6, .9 * math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))), "#000", stroke=False)
    g += _pth(_tp("M28,25.2C34,26.2 40,27 46,27.6M30,19.4C34,18.2 38,17.6 42,18", m), sw=W0)
    g += _pth(_tp("M30,34.6C34,36 40,37 47,37.6M34,36.4l-.6,2.2M38,37l-.4,2.4M42,37.4l-.2,2.4", m), sw=W0)
    return g


def _vig_naga(rnd, eggs):
    p = "naga-"
    sc_pat = (f'<pattern id="{p}sc" width="3.2" height="2.6" patternUnits="userSpaceOnUse">'
              f'<path d="M0,2.6Q1.6,-.4 3.2,2.6M-1.6,1.3Q0,-1.7 1.6,1.3M1.6,1.3Q3.2,-1.7 4.8,1.3" fill="none" {K} stroke-width=".6"/></pattern>')
    g = ""
    var = rnd.randrange(3)
    # sky rules, and the stair climbing away to the right
    g += _sky_lines(60, 40, 60, 38, 2, 40, 2.4, rnd, gap_fn=lambda y, a, b: [(a, min(b, 18 + y * .2))] if y < 34 else [(a, b)])
    steps = "".join(f"M{_n(74 + i * 6)},{_n(66 - i * 5)}h6v-5" for i in range(8))
    g += _pth("M74,66" + "".join(f"h6v-5" for _ in range(8)) + "V74H74Z", "#fff", 0)
    g += _pth("M74,66" + "".join(f"h6v-5" for _ in range(8)) + "V74H74Z", f"url(#{p}h)", 0) + _pth(steps, sw=W0)
    # two heads behind, receding (cross-hatched), then the neck and the main head
    neck = ("M60,16C68,22 72,34 72,46C72,54 72,60 76,64C88,56 104,44 119,36L119,48C104,56 92,66 80,74"
            "L58,74C58,68 60,62 58,54C56,48 53,43 50,40C49,36 48,33 46.4,30Z")
    g += _pth(neck, f"url(#{p}sc)", W1)
    throat = "M50,40C53,43 56,48 58,54C60,62 58,68 58,74L64,74C64,66 64,58 62,52C60,46 57,41 53,38Z"
    g += _pth(throat, "#fff", W0)
    g += _pth("".join(f"M{_n(51 + i * 1.2)},{_n(40.4 + i * 4)}l{_n(5.6 - abs(i - 3) * .2)},{_n(-1.6 + i * .1)}" for i in range(8)), sw=W0)
    g += _pth("M76,64C88,56 104,44 119,36L119,40C104,48 90,58 79,66Z", f"url(#{p}d)", 0)
    g += _naga_head(_mat(0, 0, 0, 1), "#fff", var)
    # plinth and ground
    g += _pth("M40,74H96V77H40Z", f"url(#{p}v)", W0) + _pth("M4,77.4H116", sw=W1)
    return _vsvg("naga", g, sc_pat)


# ---------------------------------------------------------------------------- garuda
def _dog(x, y, s=1.0, face=1):
    """Easter egg: a tiny dog in profile (ears up, tail up), about 6 x 4.4 at s=1, feet on y,
    white with a hairline edge so it hides among feathers or scales."""
    d = ("M0,0L0,-2.2L-1,-3.4L-.6,-4.2L.2,-3.8L.6,-4.6L1,-3.6L4.4,-3.4L5.2,-4.6L5.4,-4.2L5,-2.6L5,0"
         "L4.2,0L4.2,-1.8L1.4,-1.8L1.4,0Z")
    return _pth(_tp(d, (s * face, 0, 0, s, x, y)), "#fff", W0)


def _vig_garuda(rnd, eggs):
    p = "garuda-"
    var = rnd.randrange(3)
    L = ""
    # wing: coverts in scales, then long primaries as kranok-tipped feathers, then the arm in front
    wing = "M53,30C46,20 34,10 12,3.6C8.6,2.8 6.4,5 8,7.4C16,20 30,32 52,40Z"
    L += _pth(wing, f"url(#{p}sc)", W1)
    L += _pth("M50,33C42,26 30,18 16,12", sw=W0) + _pth("M48,36.6C40,30 28,22 14,15", sw=W0)
    for i in range(11):
        t = i / 10
        bx, by = 9 + t * 40, 8 + t * 30
        ang = 122 - t * 38
        ln = .74 - t * .26
        L += _kranok(_mat(bx, by, ang, ln, -ln * .62), fill="#fff", line=W0, var=var, lw=W0)
    # arm raised: upper arm out, forearm up, hand open beside the crown
    L += _pth("M53,29C48,30 44,31 41,31.4C39,31.6 37.6,30 38,28L39.4,17C39.6,15.6 42,15.6 42,17L42.4,27C45,27 49,26 53,25Z", "#fff", W0)
    L += _pth("M41,31.4C39,31.6 37.6,30 38,28L39.4,17C39.6,16.4 40.4,16 41,16.4L40.4,28.6C42,29.6 46,29 53,28L53,29C48,30 44,31 41,31.4Z", f"url(#{p}d)", 0)
    L += _pth("M38.4,17.4C37,15 37.4,12 38.4,11.4C38.6,13 39,14 39.6,14.6C39.4,12.4 40,10.4 41,10C41,12 41.2,13.6 41.8,14.6C42.2,13 43,12 44,12C43.6,13.6 43,15.6 42.2,17.4Z", "#fff", W0)
    L += _pth("M37.6,24.4H42.8M38.2,21.6H42.4", sw=.8)   # armlets
    # leg: thigh in feathers, shin, talons gripping
    L += _pth("M55,46C50,48 45,52 44,57C43.4,60 45,62 48,62L52,62C52,58 54,54 58,52Z", f"url(#{p}sc)", W0)
    L += _pth("M46,61.6L46.6,68.4L50.4,68.4L51,61.6Z", f"url(#{p}h)", W0)
    L += _pth("M46.6,68.4C44,69 42,70.6 41.6,72.6C43,71.4 44.6,71 46,71M48.4,68.4L48,73M50.4,68.4C52,69.4 53,71 53,72.6", sw=.9)
    # tail fan between the legs
    L += _pth("M58,52C56,58 54,66 54,74C56,73 58,73.6 60,74.6L60,52Z", "#fff", W0)
    L += _pth("M57,56C56,62 55.6,68 56,72.6M59,54V74", sw=W0)
    # torso, belt, necklace
    L += _pth("M53,25C52,32 52.6,40 55,46L60,47L60,25Z", "#fff", W0)
    L += _pth("M55.6,27C54.6,33 55,40 57,45L60,45.6L60,27Z", f"url(#{p}hl)", 0)
    L += _pth("M54.4,42.4L60,43.4V46L55.2,45Z", "#000", 0)
    L += _pth("M53.6,26.6Q56,31 60,31.6", sw=1) + _circ(55.4, 29.4, .7, "#000", stroke=False)
    R = _bake_group(L, (-1, 0, 0, 1, 120, 0))
    # standing on clouds (lai mek): rows of curling scrolls
    g = ""
    for i, (cx, cy, r) in enumerate(((22, 72, 5), (32, 70, 6.4), (44, 73, 4.6), (76, 73, 4.6), (88, 70, 6.4), (98, 72, 5))):
        cw = 1 if cx < 60 else -1
        pts = _spiral_pts(cx, cy, r, 1.1, math.pi, cw)
        g += _pth(_poly(pts, False), sw=.8)
    g += _pth("M14,76.4C30,74 44,75 60,76.6C76,75 90,74 106,76.4", sw=W0)
    g += _pth("M24,78.6H96", sw=W0)
    g += L + R
    # head: face, eyes, the hooked beak, the tall crown (chada)
    g += _pth("M54.4,19C54,14 56.6,11 60,11C63.4,11 66,14 65.6,19C65,23 62.6,25 60,25C57.4,25 55,23 54.4,19Z", "#fff", W0)
    g += _pth("M60,16.6C58.6,18.6 58.2,21 58.6,23.6C59,25.4 59.8,27 60,28.4C60.2,27 61,25.4 61.4,23.6C61.8,21 61.4,18.6 60,16.6Z", "#000", 0)
    for sx in (-1, 1):
        g += _pth(f"M{_n(60 + sx * 1.4)},{_n(15.4)}Q{_n(60 + sx * 3.4)},{_n(13.6)} {_n(60 + sx * 5)},{_n(15.6)}Q{_n(60 + sx * 3.4)},{_n(17)} {_n(60 + sx * 1.4)},{_n(15.4)}Z", "#fff", W0)
        g += _circ(60 + sx * 3.4, 15.5, .8, "#000", stroke=False)
    g += _pth("M55.4,12.4L56.6,8.6L58.2,7.4L59,3.4L60,.6L61,3.4L61.8,7.4L63.4,8.6L64.6,12.4Z", "#fff", W0)
    g += _pth("M56.6,8.6H63.4M58.2,7.4H61.8M56,10.6H64", sw=W0) + _pth("M60,.6L61,3.4L61.8,7.4L60,7.4Z", f"url(#{p}v)", 0)
    if eggs.get("dog") is not None:   # a dog among the coverts, on the left wing or the right
        side, slot = eggs["dog"] % 2, eggs["dog"] // 2 % 3
        x, y = (24 + slot * 6, 17.4 + slot * 4)
        g += _dog(x if side == 0 else 120 - x, y, 1.15, 1 if side == 0 else -1)
    sc_pat = (f'<pattern id="{p}sc" width="3.2" height="2.6" patternUnits="userSpaceOnUse">'
              f'<path d="M0,2.6Q1.6,-.4 3.2,2.6M-1.6,1.3Q0,-1.7 1.6,1.3M1.6,1.3Q3.2,-1.7 4.8,1.3" fill="none" {K} stroke-width=".6"/></pattern>')
    return _vsvg("garuda", g, sc_pat)


# ---------------------------------------------------------------------------- lotus bud
def _cub(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _split(c, t0, t1):
    """The piece of cubic c (4 points) between t0 and t1, as 4 control points."""
    def at(c, t):
        a = [((1 - t) * c[i][0] + t * c[i + 1][0], (1 - t) * c[i][1] + t * c[i + 1][1]) for i in range(3)]
        b = [((1 - t) * a[i][0] + t * a[i + 1][0], (1 - t) * a[i][1] + t * a[i + 1][1]) for i in range(2)]
        m = ((1 - t) * b[0][0] + t * b[1][0], (1 - t) * b[0][1] + t * b[1][1])
        return [c[0], a[0], b[0], m], [m, b[1], a[2], c[3]]
    right = at(c, t0)[1]
    return at(right, (t1 - t0) / (1 - t0))[0]


def _cd(c, move=True):
    s = f"M{_n(c[0][0])},{_n(c[0][1])}" if move else ""
    return s + "C" + " ".join(f"{_n(x)},{_n(y)}" for x, y in c[1:])


def _petal(e1, e2, n, u0=.12, u1=.88, fill="#fff", t0=.08, t1=.9):
    """A petal bounded by two cubic edges sharing base and tip, veined with n bulino lines that blend
    from one edge to the other and stop short of base and tip, as a burin would."""
    rev = [e2[3], e2[2], e2[1], e2[0]]
    g = _pth(_cd(e1) + _cd(rev, False)[0:] + "Z", fill, W1)
    v = ""
    for k in range(n):
        u = u0 + (u1 - u0) * k / max(1, n - 1)
        cp = [((1 - u) * a[0] + u * b[0], (1 - u) * a[1] + u * b[1]) for a, b in zip(e1, e2)]
        v += _cd(_split(cp, t0 + .04 * (k % 2), t1 - .03 * (k % 3)))
    return g + _pth(v, sw=W0)


def _bud(cx, base, h, w, shade_n=(13, 7)):
    """A closed lotus bud (bua tum): two wrapping petals, veined, the right one in shadow, the left
    one's free edge curling across the front."""
    tip = (cx + w * .04, base - h)
    rb, lb = (cx - w * .1, base), (cx + w * .1, base)
    right_o = [rb, (cx + w * 1.15, base - h * .14), (cx + w * .95, base - h * .66), tip]
    right_i = [rb, (cx - w * .2, base - h * .3), (cx, base - h * .7), tip]
    left_o = [lb, (cx - w * 1.15, base - h * .14), (cx - w * .95, base - h * .66), tip]
    left_i = [lb, (cx + w * .62, base - h * .3), (cx + w * .3, base - h * .78), tip]
    g = _petal(right_o, right_i, shade_n[0], .05, .95)
    g += _petal(left_o, left_i, shade_n[1], .3, .92)
    g += _pth(f"M{_n(cx - w * .4)},{_n(base - h * .02)}Q{_n(cx)},{_n(base + h * .1)} {_n(cx + w * .4)},{_n(base - h * .02)}L{_n(cx + w * .14)},{_n(base + h * .1)}L{_n(cx - w * .14)},{_n(base + h * .1)}Z", "#000", 0)
    return g


def _vig_lotus_bud(rnd, eggs):
    p = "lotus_bud-"
    g = ""
    # pond: rules, with gaps where the pad lies
    g += _water(2, 118, 58, 80, rnd, gaps=((62, 116, 56, 72),))
    # the pad: a broad leaf on the water, notched, veined, its far half hatched
    pad = "M64,64C64,58 76,55 90,55C104,55 116,58 116,63C116,68 104,71 90,71C82,71 74,70 70,68L90,63L67,66C65,65.4 64,64.6 64,64Z"
    g += _pth(pad, f"url(#{p}h)", W1)
    g += _pth("M66,62C70,57 80,55.4 90,55.4C102,55.4 112,57.6 115.4,61L90,63Z", f"url(#{p}hd)", 0)
    g += _pth("M66,62C70,57 80,55.4 90,55.4C102,55.4 112,57.6 115.4,61", sw=W0)
    g += _pth("".join(f"M90,63L{_n(90 + 24 * math.cos(a))},{_n(63 + 7 * math.sin(a))}" for a in [math.radians(x) for x in range(-170, 180, 30)] if not 95 < math.degrees(a) < 180), "none", W0).replace(K, 'stroke="#fff"').replace('stroke-width=".6"', 'stroke-width="1"')
    # stems
    g += _pth("M57,58C56,64 54,72 55,80M60,58C59,64 57,72 58,80", sw=W0) + _pth("M57.2,60L58,80", sw=W0)
    g += _pth("M28,49C30,58 33,68 32,80M30,49C32,58 35,68 34,80", sw=W0)
    for y in range(62, 79, 4):
        g += _circ(55.6 + (y - 60) * -.08, y, .45, "#000", stroke=False)
    # a rolled young leaf at the left, hatched
    g += _pth("M10,58C10,50 16,44 22,46C18,48 16,52 17,58Z", f"url(#{p}d)", W0) + _pth("M17,58C16,62 15,68 16,80", sw=W0)
    # the buds: a small one, and the great one
    g += _bud(29, 50, 18, 6, (4, 2))
    g += _bud(58.4, 58, 50, 15)
    # a dragonfly
    df = "M93,17L106,22"
    g += _pth(df, sw=1.2) + _circ(92.4, 16.8, 1.2, "#000", stroke=False)
    for (a, b) in ((-62, 9), (-34, 8), (118, 9), (146, 8)):
        x0, y0 = 95.4, 17.8
        ar = math.radians(a)
        x1, y1 = x0 + b * math.cos(ar), y0 + b * math.sin(ar)
        g += _pth(f"M{x0},{y0}Q{_n((x0 + x1) / 2 + 1.6 * math.sin(ar))},{_n((y0 + y1) / 2 - 1.6 * math.cos(ar))} {_n(x1)},{_n(y1)}"
                  f"Q{_n((x0 + x1) / 2 - 1.6 * math.sin(ar))},{_n((y0 + y1) / 2 + 1.6 * math.cos(ar))} {x0},{y0}Z", "#fff", W0)
    return _vsvg("lotus_bud", g)


# ---------------------------------------------------------------------------- sala
def _vig_sala(rnd, eggs):
    p = "sala-"
    g = ""
    cx = 56
    # sky rules on the right, a sugar palm at the left
    g += _sky_lines(64, 52, 62, 50, 4, 50, 2.4, rnd, gap_fn=lambda y, a, b: [(a, min(b, 26)), (max(a, 88), b)])
    g += _pth("M14,58C15,46 15,30 13,18M16,58C17,46 17,30 15,18", sw=W0) + _pth("M14,58C15,46 15,30 13,18L15,18C17,30 17,46 16,58Z", f"url(#{p}h)", 0)
    fr = "".join(f"M14,18Q{_n(14 + dx * .5)},{_n(12 + abs(dx) * .1)} {_n(14 + dx)},{_n(18 + abs(dx) * .35 - 4)}" for dx in (-11, -8, -5, -2, 2, 5, 8, 11))
    g += _pth(fr, sw=.8) + _circ(14, 19, 1.4, "#000", stroke=False)
    # platform over the water, posts below
    g += _pth("M24,52H90V55H24Z", "#fff", W1) + _pth("M58,52H90V55H58Z", f"url(#{p}v)", 0)
    g += _pth("M28,55V64M44,55V64M70,55V64M86,55V64", sw=1.2)
    # pillars, tapering, shaded right
    for x in (32, 48, 64, 80):
        g += _pth(f"M{x - 1.6},52L{x - 1.2},28L{x + 1.2},28L{x + 1.6},52Z", "#fff", W0)
        g += _pth(f"M{x},52L{x},28L{x + 1.2},28L{x + 1.6},52Z", f"url(#{p}hd)", 0)
        g += _pth(f"M{x - 2.2},28.2Q{x},26.2 {x + 2.2},28.2Z", "#000", 0)  # lotus capital
    # balustrade between the pillars
    rail = "M30,45H82M30,46.4H82"
    bal = "".join(f"M{x},46.4V52" for x in range(35, 80, 3) if x % 16 not in (0, 15, 1))
    g += _pth(rail + bal, sw=W0)
    if eggs.get("sala_surf"):   # a surfboard propped against a pillar
        g += _pth("M83.4,52C83,44 84,38 85.6,35C87,38 87.6,44 86.8,52Z", "#fff", W0) + _pth("M85.2,36.4L85.2,51", sw=W0)
    # roof: a lower flaring tier, then the gable with niello boards, fins, chofa and hang hong
    g += _pth("M18,30C30,27 40,22 46,16L66,16C72,22 82,27 94,30L94,31.6C82,29.4 70,26 60,22L52,22C42,26 30,29.4 18,31.6Z", "#000", 0)
    g += _pth("M24,28.6C34,26 42,21.6 47,17.4H65C70,21.6 78,26 88,28.6", sw=W0).replace(K, 'stroke="#fff"')
    for sx in (-1, 1):
        ex = cx + sx * 38
        g += _kranok(_mat(ex, 30.4, -20 * sx, .26 * sx, .26), fill="#000", ink="#fff", var=1, lw=.6)
    # gable
    tri = f"M{cx},5L{cx + 13},21L{cx - 13},21Z"
    g += _pth(tri, f"url(#{p}x)", 0)
    g += _circ(cx, 15.4, 2.6, "#fff", sw=W0) + _prajam(cx, 15.4, 2.2, ground="#fff", petal="#000", eye=False)
    for sx in (-1, 1):
        board = f"M{cx},2.4L{cx + sx * 17},22.6L{cx + sx * 15},23.4L{cx},5.4Z"
        g += _pth(board, "#000", 0)
        fins = ""
        for i in range(1, 8):
            t = i / 8.4
            x, y = cx + sx * 17 * t, 2.4 + 20.2 * t
            fins += _tp(_FIN, _mat(x, y, -50 if sx < 0 else -130, .55, .55 * (-1 if sx > 0 else 1)))
        g += _pth(fins, "#000", 0)
        g += _kranok(_mat(cx + sx * 16.4, 23, -10 * sx, .3 * sx, .3), fill="#000", ink="#fff", var=0, lw=.6)
    cm = _mat(cx, 3, 0, .34)
    g += _pth(_tp(_CHOFA, cm), "#000", 0)
    # water and reflections
    g += _water(2, 118, 60, 80, rnd, gaps=((26, 88, 60, 66),))
    refl = "".join(f"M{x - 1.4},{y}H{x + 1.6}" for x in (32, 48, 64, 80) for y in (61, 63.4, 66))
    g += _pth(refl + "M26,60H88", sw=W0)
    return _vsvg("sala", g)


def thai_vignettes(seed=None):
    """Six engraved Thai vignettes, each a complete <svg viewBox="0 0 120 80">, ids prefixed by key.
    The seed (default: today's) moves the hidden touches: a surfboard on the long-tail boat or the sala,
    a P on the elephant's caparison, a dog among the garuda's feathers."""
    seed = seed_from_date() if seed is None else seed
    r = random.Random(seed * 3 + 2)
    eggs = {"boat_surf": r.random() < .5, "P": r.random() < .5, "dog": r.randrange(6),
            "sala_surf": r.random() < .5}
    out = {}
    for k in ("wat_arun", "elephant", "naga", "garuda", "lotus_bud", "sala"):
        out[k] = globals()["_vig_" + k](random.Random(seed * 31 + len(k)), eggs)
    return out
