"""Engraved page frames for the Kindle Morning Edition. Stdlib only; every public function returns SVG.

Security-printing vocabulary, drawn for a black-and-white e-ink panel (Kindle Paperwhite 11, Chrome 75):
crisp black strokes only (no gradients, opacity or grey fills), fine lines 0.6-0.9 px, and no transforms
(the page reset forces `transform:none !important`), so every coordinate is baked. Line weights match the
Evening Edition (solar/kindle_evening.py): W0 .6 hairline, W1 1 rule, W2 1.6 heavy rule.

Public API
    page_frame(width=618, height=618, seed=0, section_key="", band=20, top_legend=None, bottom_legend=None)
    frame_metrics(width=618, height=618, band=20)   -> dict: corner slot centres/diameter, safe reading rect
    guilloche_panel(width, height, seed, legend=None)
    microtext_line(text, width, seed)
    rosette(seed, size, slot=0)
"""
import hashlib
import math
import random

W0, W1, W2 = .6, 1, 1.6       # hairline, rule, heavy rule (Evening Edition weights)
WF = .7                        # guilloche strand weight: inside the 0.6-0.9 e-ink window
SLOT = 32                      # corner slot diameter (px), for the vignettes other engravers supply
K = 'stroke="#000"'
SERIF = "Georgia,'Times New Roman',serif"
TAU = 2 * math.pi


# ---- number and path encoding -------------------------------------------------------------------

def _n(x):
    """One decimal, no trailing .0, no leading zero: 0.5 -> .5, -0.5 -> -.5, 3.0 -> 3."""
    s = f"{x:.1f}"
    if s in ("-0.0", "0.0"):
        return "0"
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def _join(nums):
    """Join path numbers with the fewest separators the SVG grammar allows."""
    out = ""
    for s in nums:
        if out and not (s.startswith("-") or (s.startswith(".") and "." in _last_num(out))):
            out += " "
        out += s
    return out


def _last_num(s):
    i = len(s)
    while i > 0 and (s[i - 1].isdigit() or s[i - 1] == "."):
        i -= 1
    return s[i:]


def _poly(pts, close=False):
    """Absolute points -> compact relative path data. Deltas are taken between *rounded* points, so the
    path never drifts however long it is."""
    r = [(round(x, 1), round(y, 1)) for x, y in pts]
    d = [r[0]]
    for p in r[1:]:
        if p != d[-1]:
            d.append(p)
    nums = []
    for (x0, y0), (x1, y1) in zip(d, d[1:]):
        nums += [_n(x1 - x0), _n(y1 - y0)]
    return "M" + _join([_n(d[0][0]), _n(d[0][1])]) + ("l" + _join(nums) if nums else "") + ("z" if close else "")


def _rng(*parts):
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _uid(*parts):
    return "g" + hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:6]


def _svg(w, h, inner, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{_n(w)}" height="{_n(h)}" viewBox="0 0 {_n(w)} {_n(h)}" aria-hidden="true">'
            + (f"<defs>{defs}</defs>" if defs else "") + inner + "</svg>")


def _path(d, sw, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" {K} stroke-width="{sw}"{extra}/>'


def _use(ref, x, y):
    # <use x y> is an implicit translation, not a CSS transform, so the reset leaves it alone
    return f'<use xlink:href="#{ref}" href="#{ref}" x="{_n(x)}" y="{_n(y)}"/>'


# ---- waves: the engine-turned strands ---------------------------------------------------------------

def _wave(a, b, c, amp, period, phase, vertical=False):
    """A sine-like wave along one axis from a to b, centred on c (quadratic t-chain: tiny output).
    phase is in px. Returns path data."""
    half = period / 2
    s = a - (phase % period) - period
    n = int(math.ceil((b - s) / half)) + 1
    if vertical:
        head = f"M{_join([_n(c), _n(s)])}q{_join([_n(-2 * amp), _n(half / 2), '0', _n(half)])}"
        tail = "t" + " ".join(f"0 {_n(half)}" for _ in range(n - 1))
    else:
        head = f"M{_join([_n(s), _n(c)])}q{_join([_n(half / 2), _n(-2 * amp), _n(half), '0'])}"
        tail = "t" + " ".join(f"{_n(half)} 0" for _ in range(n - 1))
    return head + tail


def _rope_params(seed, section_key):
    """Per-section rope recipe: cohesive (same anatomy) but eclectic (different lathe settings)."""
    r = _rng("rope", seed, section_key)
    period = r.choice([10, 11, 12, 13, 14, 16])
    phases = r.choice([3, 4, 4, 5, 6])
    lines = 2 if phases <= 3 else 1
    if phases == 4:
        lines = r.choice([1, 2])
    return {
        "period": period,
        "phases": phases,
        "lines": lines,
        "gap": r.choice([1.2, 1.3, 1.4]),
        "second": r.choice(["none", "half", "third", "half"]) if phases * lines <= 5 else "none",
        "beads": r.choice(["pearl", "dentil", "reel", "pearl-dot", "dentil-x"]),
        "drift": r.random() * period,
        "rosette": r.randrange(1 << 30),
        "cart": r.choice(["ogee", "shield", "lozenge"]),
    }


def _rope_band(x0, x1, cy, half_h, p, vertical=False):
    """Interwoven strands: `phases` sine strands equally out of phase, each cut as `lines` parallel
    hairlines, over an optional shallower counter-wave. Returns one merged path."""
    lines, gap = p["lines"], p["gap"]
    spread = (lines - 1) * gap
    amp = half_h - spread / 2 - .5
    ds = []
    for i in range(p["phases"]):
        ph = p["drift"] + p["period"] * i / p["phases"]
        for j in range(lines):
            ds.append(_wave(x0, x1, cy - spread / 2 + j * gap, amp, p["period"], ph, vertical))
    if p["second"] != "none":
        per = p["period"] / (2 if p["second"] == "half" else 3)
        for ph in (0, per / 2):
            ds.append(_wave(x0, x1, cy, amp * .38, per, ph + p["drift"], vertical))
    return "".join(ds)


# ---- rosettes -------------------------------------------------------------------------------------

def _trochoid(cx, cy, r_in, r_out, lobes, rot=0.0, retro=True, step=1.7):
    """z(t) = A e^{it} + B e^{i(+/-)q t}: a looped guilloche ring filling the annulus r_in..r_out."""
    A, B = (r_out + r_in) / 2, (r_out - r_in) / 2
    q = lobes - 1 if retro else lobes + 1
    sgn = -1 if retro else 1
    # arc length per lobe ~ 2*pi*A/lobes + 4B; sample to ~step px
    n = max(lobes * 10, int((TAU * A + 4 * B * lobes) / step))
    pts = []
    for k in range(n):
        t = TAU * k / n
        x = A * math.cos(t + rot) + B * math.cos(sgn * q * t + rot * (1 + sgn * q) * 0 + lobes * rot)
        y = A * math.sin(t + rot) + B * math.sin(sgn * q * t + lobes * rot)
        pts.append((cx + x, cy + y))
    return _poly(pts, True)


def _wavering(cx, cy, rm, amp, lobes, phase=0.0, step=1.7, mod=0.0, modk=0):
    """Polar wave ring r = rm + amp*sin(lobes*t + phase) (+ an optional slow modulation)."""
    n = max(lobes * 8, int(TAU * (rm + amp) / step))
    pts = []
    for k in range(n):
        t = TAU * k / n
        r = rm + amp * math.sin(lobes * t + phase) + (mod * math.sin(modk * t) if modk else 0)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return _poly(pts, True)


def _circle(cx, cy, r, sw, fill="none"):
    return f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{fill}" {K} stroke-width="{sw}"/>'


def _scallop(cx, cy, r, n, depth):
    pts = []
    m = n * 10
    for k in range(m):
        t = TAU * k / m
        rr = r - depth * abs(math.sin(n * t / 2)) ** .6
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return _poly(pts, True)


def _braid(cx, cy, rm, amp, lobes, phase=0.0):
    """Polar wave ring r = rm + amp*sin(lobes*t + phase), one quadratic per half lobe (compact: the
    big rosettes are built from these)."""
    n = 2 * lobes
    d = math.pi / lobes
    t0 = -phase / lobes
    rc = 2 * (rm + amp) - rm * math.cos(d / 2)
    rc2 = 2 * (rm - amp) - rm * math.cos(d / 2)
    pts = [(cx + rm * math.cos(t0), cy + rm * math.sin(t0))]
    r0 = (round(pts[0][0], 1), round(pts[0][1], 1))
    nums, prev = [], r0
    for k in range(n):
        tm, t1 = t0 + (k + .5) * d, t0 + (k + 1) * d
        rr = rc if k % 2 == 0 else rc2
        c = (round(cx + rr * math.cos(tm), 1), round(cy + rr * math.sin(tm), 1))
        e = (round(cx + rm * math.cos(t1), 1), round(cy + rm * math.sin(t1), 1))
        nums += [_n(c[0] - prev[0]), _n(c[1] - prev[1]), _n(e[0] - prev[0]), _n(e[1] - prev[1])]
        prev = e
    return "M" + _join([_n(r0[0]), _n(r0[1])]) + "q" + _join(nums) + "z"


def _rosette_body(cx, cy, R, seed, slot=0.0, step=1.7, sparse=1.0):
    """A multi-layer guilloche rosette of outer radius R. With slot > 0 the centre is left white and
    empty (a ring of that diameter) for a vignette. Small rosettes use looped trochoids; large ones are
    braided from phase-shifted wave rings, rose-engine style."""
    r = _rng("rosette", seed)
    out = []
    rim = R
    scal = r.choice([0, 16, 20, 24]) if R < 40 else r.choice([0, 36, 44, 52])
    depth = max(1.0, R * .04)
    if scal:
        out.append(_path(_scallop(cx, cy, rim, scal, depth), W1, "#fff"))
    else:
        out.append(_circle(cx, cy, rim - .5, W1, "#fff"))
        out.append(_circle(cx, cy, rim - 2.2, W0))
    r_lo = slot / 2 + 1.4 if slot else R * .1
    inner = rim - (2.8 if scal == 0 else depth + 1.1)
    span = inner - r_lo
    nl = 1 if span < 9 else (2 if span < 28 else (3 if span < 80 else 4))
    # unequal layers: outer band widest
    wts = [1.25, 1, .85, .75][:nl]
    tot = sum(wts)
    edges = [inner]
    for wt in wts:
        edges.append(edges[-1] - span * wt / tot)
    for li in range(nl):
        ro, ri = edges[li] - .4, edges[li + 1] + .4
        if li:
            out.append(_circle(cx, cy, edges[li], W1 if (li == 1 and R > 60) else W0))
        mid = (ro + ri) / 2
        amp = (ro - ri) / 2
        last = li == nl - 1 and not slot
        ds = []
        if R < 40 and not last:
            lobes = max(10, int(TAU * mid / (r.choice([3.4, 4.0, 4.6]) * sparse)))
            copies = 2 if (ro - ri) > 4 else 1
            retro = r.random() < .6
            for c in range(copies):
                ds.append(_trochoid(cx, cy, ri, ro, lobes, TAU * c / (copies * lobes), retro, step * sparse ** .5))
        elif last:  # the central flower
            lobes = r.choice([8, 10, 12, 14, 16]) if R > 30 else r.choice([6, 8, 10])
            ds.append(_braid(cx, cy, mid, amp, lobes, 0))
            ds.append(_braid(cx, cy, mid, amp, lobes, math.pi))
            if R > 50:
                ds.append(_braid(cx, cy, mid * .62, amp * .5, lobes * 2, 0))
                ds.append(_braid(cx, cy, mid * .62, amp * .5, lobes * 2, math.pi))
        else:
            pitch = (5.4 + mid * r.choice([.05, .07, .09])) * sparse
            lobes = max(10, int(TAU * mid / pitch))
            m = r.choice([2, 3]) if amp < 10 else r.choice([3, 4])
            for c in range(m):   # nested amplitudes, so the crests do not pile into a black ring
                ds.append(_braid(cx, cy, mid, amp * (1 - .14 * c), lobes, TAU * c / m))
            if r.random() < .5 and 5 < amp and sparse < 1.2:   # an inner counter-braid at double frequency
                for c in range(2):
                    ds.append(_braid(cx, cy, mid, amp * .45, lobes * 2, math.pi * c + .5))
        out.append(_path("".join(ds), WF))
    if slot:
        out.append(_circle(cx, cy, slot / 2 + .9, W1, "#fff"))
    else:
        out.append(_circle(cx, cy, max(1.4, R * .035), W0, "#000"))
    return "".join(out)


def rosette(seed, size, slot=0):
    """A standalone guilloche rosette, `size` px square. slot > 0 keeps an empty centre of that diameter."""
    R = size / 2 - .8
    return _svg(size, size, _rosette_body(size / 2, size / 2, R, seed, slot))


# ---- small ornaments --------------------------------------------------------------------------------

def _star(cx, cy, r, w=None):
    w = r * .2 if w is None else w
    return (f"M{_join([_n(cx), _n(cy - r)])}Q{_join([_n(cx + w), _n(cy - w), _n(cx + r), _n(cy)])}"
            f"Q{_join([_n(cx + w), _n(cy + w), _n(cx), _n(cy + r)])}Q{_join([_n(cx - w), _n(cy + w), _n(cx - r), _n(cy)])}"
            f"Q{_join([_n(cx - w), _n(cy - w), _n(cx), _n(cy - r)])}Z")


def _beads(x0, x1, c, size, style, vertical=False, skip=()):
    """The inner beaded / dentil rule. Returns (stroked d, filled d)."""
    pitch = {"pearl": 4.2, "pearl-dot": 4.2, "dentil": 3.6, "dentil-x": 3.6, "reel": 7.4}[style]
    n = int((x1 - x0) / pitch)
    off = x0 + ((x1 - x0) - n * pitch) / 2 + pitch / 2
    st, fi = [], []
    rr = size / 2
    for i in range(n):
        u = off + i * pitch
        if any(a - pitch / 2 < u < b + pitch / 2 for a, b in skip):
            continue
        P = (lambda a, b: (b, a)) if vertical else (lambda a, b: (a, b))
        if style in ("pearl", "pearl-dot") or (style == "reel" and True):
            if style == "reel":
                # bead, then a reel (short bar pair)
                x, y = P(u - pitch / 4, c)
                st.append(_circ_d(x, y, rr))
                a, b = P(u + pitch / 4 - .8, c - rr * .8)
                a2, b2 = P(u + pitch / 4 + .8, c + rr * .8)
                fi.append(_rect_d(min(a, a2), min(b, b2), abs(a2 - a), abs(b2 - b)))
            else:
                x, y = P(u, c)
                if style == "pearl-dot" and i % 2:
                    fi.append(_circ_d(x, y, .8))
                else:
                    st.append(_circ_d(x, y, rr))
        else:
            # dentil: a solid black block every pitch
            bw = pitch * .5
            a, b = P(u - bw / 2, c - rr)
            a2, b2 = P(u + bw / 2, c + rr)
            fi.append(_rect_d(min(a, a2), min(b, b2), abs(a2 - a), abs(b2 - b)))
            if style == "dentil-x" and i % 4 == 0:
                pass
    return "".join(st), "".join(fi)


def _circ_d(x, y, r):
    return (f"M{_join([_n(x - r), _n(y)])}a{_join([_n(r), _n(r), '0', '1', '0', _n(2 * r), '0'])}"
            f"a{_join([_n(r), _n(r), '0', '1', '0', _n(-2 * r), '0'])}")


def _rect_d(x, y, w, h):
    return f"M{_join([_n(x), _n(y)])}h{_n(w)}v{_n(h)}h{_n(-w)}z"


def _sunburst(cx, cy, r0, half, n):
    """Radial hairlines from r0 out to the square of half-size `half` around (cx, cy)."""
    segs = []
    for k in range(n):
        t = TAU * (k + .5) / n
        c, s = math.cos(t), math.sin(t)
        L = half / max(abs(c), abs(s))
        segs.append(f"M{_join([_n(cx + r0 * c), _n(cy + r0 * s)])}L{_join([_n(cx + L * c), _n(cy + L * s)])}")
    return "".join(segs)


def _text(x, y, s, size, length, anchor="start", weight=600, adjust="spacingAndGlyphs"):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{_n(x)}" y="{_n(y)}" font-family="{SERIF}" font-size="{size}" font-weight="{weight}" '
            f'fill="#000" stroke="none" text-anchor="{anchor}" textLength="{_n(length)}" '
            f'lengthAdjust="{adjust}">{s}</text>')


def _text_w(s, size):
    """Rough width of uppercase Georgia at `size`, generous so textLength only ever adds air."""
    w = 0
    for ch in s:
        if ch == " ":
            w += .3
        elif ch in ".,:;'·":
            w += .32
        elif ch.isdigit():
            w += .62
        elif ch in "MW":
            w += .92
        elif ch == "I":
            w += .38
        elif ch.isupper():
            w += .72
        else:
            w += .55
    return w * size


# ---- cartouches ------------------------------------------------------------------------------------

def _cartouche_h(cx, cy, hw, hh, style):
    """Horizontal cartouche outline centred at (cx, cy): half-width hw, half-height hh."""
    if style == "lozenge":
        return (f"M{_join([_n(cx - hw), _n(cy)])}L{_join([_n(cx - hw + hh * 1.3), _n(cy - hh)])}"
                f"H{_n(cx + hw - hh * 1.3)}L{_join([_n(cx + hw), _n(cy)])}L{_join([_n(cx + hw - hh * 1.3), _n(cy + hh)])}"
                f"H{_n(cx - hw + hh * 1.3)}Z")
    if style == "shield":
        k = hh * 1.6
        return (f"M{_join([_n(cx - hw), _n(cy - hh)])}H{_n(cx + hw)}"
                f"Q{_join([_n(cx + hw - k), _n(cy), _n(cx + hw), _n(cy + hh)])}H{_n(cx - hw)}"
                f"Q{_join([_n(cx - hw + k), _n(cy), _n(cx - hw), _n(cy - hh)])}Z")
    k = hh * 1.9  # ogee ends
    return (f"M{_join([_n(cx - hw), _n(cy)])}C{_join([_n(cx - hw + k * .25), _n(cy - hh), _n(cx - hw + k * .5), _n(cy - hh * .2), _n(cx - hw + k), _n(cy - hh)])}"
            f"H{_n(cx + hw - k)}C{_join([_n(cx + hw - k * .5), _n(cy - hh * .2), _n(cx + hw - k * .25), _n(cy - hh), _n(cx + hw), _n(cy)])}"
            f"C{_join([_n(cx + hw - k * .25), _n(cy + hh), _n(cx + hw - k * .5), _n(cy + hh * .2), _n(cx + hw - k), _n(cy + hh)])}"
            f"H{_n(cx - hw + k)}C{_join([_n(cx - hw + k * .5), _n(cy + hh * .2), _n(cx - hw + k * .25), _n(cy + hh), _n(cx - hw), _n(cy)])}Z")


def _swap(d):
    """Swap x/y in absolute path data made only of M/L/H/V/C/Q/Z with numbers (for vertical cartouches)."""
    import re
    toks = re.findall(r"[A-Za-z]|-?\d*\.?\d+", d)
    out, cmd, nums = [], None, []

    def flush():
        if cmd is None:
            return
        if cmd in "HV":
            out.append(("V" if cmd == "H" else "H") + _join(nums))
        else:
            sw = []
            for i in range(0, len(nums), 2):
                sw += [nums[i + 1], nums[i]]
            out.append(cmd + _join(sw))
    for t in toks:
        if t.isalpha():
            flush()
            cmd, nums = t, []
            if t in "Zz":
                out.append(t)
                cmd = None
        else:
            nums.append(t)
    flush()
    return "".join(out)


def _volute(x, y, s, dirn):
    """A small C-scroll curl ending in a dot, opening away from the cartouche (dirn = +1 or -1)."""
    d = (f"M{_join([_n(x), _n(y)])}c{_join([_n(dirn * 2.5 * s), _n(-3 * s), _n(dirn * 6 * s), _n(-3.4 * s), _n(dirn * 6.6 * s), _n(-.6 * s)])}"
         f"c{_join([_n(dirn * .4 * s), _n(1.8 * s), _n(dirn * -1.6 * s), _n(2.4 * s), _n(dirn * -2.2 * s), _n(1 * s)])}"
         f"M{_join([_n(x), _n(y)])}c{_join([_n(dirn * 2.5 * s), _n(3 * s), _n(dirn * 6 * s), _n(3.4 * s), _n(dirn * 6.6 * s), _n(.6 * s)])}"
         f"c{_join([_n(dirn * .4 * s), _n(-1.8 * s), _n(dirn * -1.6 * s), _n(-2.4 * s), _n(dirn * -2.2 * s), _n(-1 * s)])}")
    return d


# ---- the page frame --------------------------------------------------------------------------------

def frame_metrics(width=618, height=618, band=20):
    """Where things sit. corner: side of each corner block; slots: centres of the empty 32 px corner slots;
    safe: the rectangle (x, y, w, h) clear of all ornament (cartouches protrude <= 2 px past the band)."""
    C = _corner(band)
    slots = [(C / 2, C / 2), (width - C / 2, C / 2), (C / 2, height - C / 2), (width - C / 2, height - C / 2)]
    g = band + 3
    return {"band": band, "corner": C, "slot_diameter": SLOT, "slots": slots,
            "safe": (g, g, width - 2 * g, height - 2 * g),
            "safe_clear_of_corners": (g, C + 2, width - 2 * g, height - 2 * C - 4)}


def _corner(band):
    return max(SLOT + 24, round(band * 2.8))


def page_frame(width=618, height=618, seed=0, section_key="", band=20, top_legend=None, bottom_legend=None):
    """A full-page engraved border (an absolutely positioned background layer behind the reading area).

    Outside in: heavy rule, hairline, an interwoven guilloche rope band, hairline, a beaded / dentil rule,
    inner rule. Corner blocks: a sunburst ground under a guilloche rosette with an empty 32 px slot.
    Midpoints: cartouches (top: the section legend, bottom: a serial number derived from the date seed,
    sides: small medallions). The rope's lathe settings vary with section_key and seed."""
    w, h, b = width, height, band
    p = _rope_params(seed, section_key)
    uid = _uid(seed, section_key, w, h, b)
    C = _corner(b)
    o1, o2 = .8, 2.6                     # heavy rule, hairline
    rope_lo, rope_hi = 3.6, b * .64      # rope zone (band coordinates)
    hl2 = rope_hi + 1.0                  # hairline under the rope
    bead_c = (hl2 + b - .5) / 2          # beaded rule centre
    bead_sz = max(1.6, (b - .5) - hl2 - 2.2)
    inner = b - .5                       # inner rule
    parts = []

    # outer rules (full perimeter)
    parts.append(_path(f"M{_n(o1)},{_n(o1)}H{_n(w - o1)}V{_n(h - o1)}H{_n(o1)}Z", W2))
    hl = (f"M{_n(o2)},{_n(o2)}H{_n(w - o2)}V{_n(h - o2)}H{_n(o2)}Z"
          f"M{_n(hl2)},{_n(hl2)}H{_n(w - hl2)}V{_n(h - hl2)}H{_n(hl2)}Z")
    parts.append(_path(hl, W0))
    parts.append(_path(f"M{_n(inner)},{_n(inner)}H{_n(w - inner)}V{_n(h - inner)}H{_n(inner)}Z", W1))

    # rope: strands run corner block to corner block on each side (the blocks mask the ends)
    rc, rh = (rope_lo + rope_hi) / 2, (rope_hi - rope_lo) / 2
    a0, ax, ay = C - 6, w - C + 6, h - C + 6
    rope = (_rope_band(a0, ax, rc, rh, p) + _rope_band(a0, ax, h - rc, rh, p)
            + _rope_band(a0, ay, rc, rh, p, True) + _rope_band(a0, ay, w - rc, rh, p, True))
    clip = (f'<clipPath id="{uid}c"><path d="M{_n(o2 + .6)},{_n(o2 + .6)}H{_n(w - o2 - .6)}V{_n(h - o2 - .6)}H{_n(o2 + .6)}Z'
            f'M{_n(hl2 - .6)},{_n(hl2 - .6)}V{_n(h - hl2 + .6)}H{_n(w - hl2 + .6)}V{_n(hl2 - .6)}Z"/></clipPath>')
    parts.append(f'<g clip-path="url(#{uid}c)">{_path(rope, WF)}</g>')

    geo = _cart_geom(w, h, b, seed, section_key, top_legend, bottom_legend)
    # beaded / dentil rule
    st, fi = "", ""
    for vert, c in ((False, bead_c), (False, h - bead_c), (True, bead_c), (True, w - bead_c)):
        L = h if vert else w
        cut = geo["hv"] if vert else (geo["hw_bot"] if c > b else geo["hw_top"])
        L2 = L / 2
        bw_ = (inner - o2) / 2 * 1.5 * (1 - (bead_c - (inner + o2) / 2) / ((inner - o2) / 2)) + bead_sz / 2 + .8
        skip = [(L2 - cut - 14, L2 + cut + 14), (L * .25 - bw_, L * .25 + bw_), (L * .75 - bw_, L * .75 + bw_)]
        s1, f1 = _beads(C + 2, L - C - 2, c, bead_sz, p["beads"], vert, skip)
        st += s1
        fi += f1
    if st:
        parts.append(_path(st, WF, "#fff"))
    if fi:
        parts.append(f'<path d="{fi}" fill="#000"/>')

    # bosses at the quarter points break the long runs of rope, as on a note's border
    bh = (inner - o2) / 2
    bc = (inner + o2) / 2
    bw = bh * 1.5
    bd, bi, bs = "", "", ""
    for vert, L, c in ((False, w, bc), (False, w, h - bc), (True, h, bc), (True, h, w - bc)):
        for f in (.25, .75):
            u = L * f
            P = (lambda a, q: (q, a)) if vert else (lambda a, q: (a, q))
            pts = [P(u - bw, c), P(u, c - bh), P(u + bw, c), P(u, c + bh)]
            bd += "M" + "L".join(_join([_n(x), _n(y)]) for x, y in pts) + "Z"
            pts = [P(u - bw + 3, c), P(u, c - bh + 2), P(u + bw - 3, c), P(u, c + bh - 2)]
            bi += "M" + "L".join(_join([_n(x), _n(y)]) for x, y in pts) + "Z"
            x, y = P(u, c)
            bs += _star(x, y, bh * .62, bh * .14)
            for sgn in (-1, 1):
                x, y = P(u + sgn * (bw + 3.2), c)
                bs += _circ_d(x, y, 1.1)
    parts.append(_path(bd, W1, "#fff") + _path(bi, W0) + f'<path d="{bs}" fill="#000"/>')

    # corner blocks: defined once, used four times
    m = C / 2
    blk = [f'<rect x="{_n(o2)}" y="{_n(o2)}" width="{_n(C - o2)}" height="{_n(C - o2)}" fill="#fff" {K} stroke-width="{W1}"/>']
    # inner frame of the block, then sunburst ground
    blk.append(f'<rect x="{_n(o2 + 2)}" y="{_n(o2 + 2)}" width="{_n(C - o2 - 4)}" height="{_n(C - o2 - 4)}" fill="none" {K} stroke-width="{W0}"/>')
    R = m - o2 - 1.6
    blk.append(_path(_sunburst(m, m, R - 2, m - o2 - 2.4, 72), W0))
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        blk.append(f'<path d="{_star(m + sx * (m - 7.2), m + sy * (m - 7.2), 3.4, .7)}" fill="#000"/>')
    blk.append(_rosette_body(m, m, R, p["rosette"], SLOT, 1.6))
    defs = clip + f'<g id="{uid}k">{"".join(blk)}</g>'
    for x, y in ((0, 0), (w - C, 0), (0, h - C), (w - C, h - C)):
        parts.append(_use(f"{uid}k", x, y))

    # cartouches
    parts.append(_cartouches(w, h, b, p, geo))
    return _svg(w, h, "".join(parts), defs)


def _serial(seed, section_key):
    r = _rng("serial", seed, section_key)
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    return f"{r.choice(letters)}{r.choice(letters)} {r.randrange(10**6, 10**7)}"


def _cart_geom(w, h, b, seed, section_key, top_legend, bottom_legend):
    hh = b / 2 + 1.5
    top = (top_legend if top_legend is not None else (section_key or "Morning Edition")).upper()
    bot = bottom_legend if bottom_legend is not None else f"No. {_serial(seed, section_key)}"
    hw = [max(64, _text_w(t, 11) / 2 + hh * 2.2 + 6) for t in (top, bot)]
    return {"hh": hh, "top": top, "bot": bot, "hw_top": hw[0], "hw_bot": hw[1], "hv": max(40, min(64, h * .09))}


def _cartouches(w, h, b, p, g):
    out = []
    style = p["cart"]
    hh = g["hh"]
    m0, m1 = 3.3, b - 1.1          # the band interior between outer hairline and inner rule
    stars, dots = "", ""
    for cy, legend, hw, y0 in ((b / 2 + .5, g["top"], g["hw_top"], m0), (h - b / 2 - .5, g["bot"], g["hw_bot"], h - m1)):
        tw = _text_w(legend, 11)
        cx = w / 2
        out.append(f'<path d="{_rect_d(cx - hw - 14, y0, 2 * hw + 28, m1 - m0)}" fill="#fff"/>')
        for sg in (-1, 1):
            stars += _star(cx + sg * (hw + 6.2), cy, 3.4, .6)
            dots += _circ_d(cx + sg * (hw + 11.4), cy, 1.1)
        out.append(_path(_cartouche_h(cx, cy, hw, hh, style), W1, "#fff"))
        out.append(_path(_cartouche_h(cx, cy, hw - 2.4, hh - 2.2, style), W0))
        sx = tw / 2 + 7
        stars += _star(cx - sx, cy, 2.6, .5) + _star(cx + sx, cy, 2.6, .5)
        out.append(_text(cx, cy + 3.9, legend, 11, tw, "middle", 700))
    # side medallions: a vertical cartouche holding a small rosette between stars
    hv = g["hv"]
    for cx, x0 in ((b / 2 + .5, m0), (w - b / 2 - .5, w - m1)):
        cy = h / 2
        hwid = b / 2 + 1.5
        out.append(f'<path d="{_rect_d(x0, cy - hv - 14, m1 - m0, 2 * hv + 28)}" fill="#fff"/>')
        for sg in (-1, 1):
            stars += _star(cx, cy + sg * (hv + 6.2), 3.4, .6)
            dots += _circ_d(cx, cy + sg * (hv + 11.4), 1.1)
        out.append(_path(_swap(_cartouche_h(cy, cx, hv, hwid, style)), W1, "#fff"))
        out.append(_path(_swap(_cartouche_h(cy, cx, hv - 2.4, hwid - 2.2, style)), W0))
        rr = hwid - 3.4
        out.append(_rosette_body(cx, cy, rr, p["rosette"] + 7, 0, 1.4))
        for sg in (-1, 1):
            stars += _star(cx, cy + sg * (rr + 9), 3.2, .6) + _star(cx, cy + sg * (rr + 18), 2.2, .4)
            dots += _circ_d(cx, cy + sg * (rr + 25), .9)
    out.append(f'<path d="{stars}{dots}" fill="#000"/>')
    return "".join(out)


def _vvolute(x, y, s, dirn):
    """Vertical version of _volute (curl opens along y)."""
    return (f"M{_join([_n(x), _n(y)])}c{_join([_n(-3 * s), _n(dirn * 2.5 * s), _n(-3.4 * s), _n(dirn * 6 * s), _n(-.6 * s), _n(dirn * 6.6 * s)])}"
            f"c{_join([_n(1.8 * s), _n(dirn * .4 * s), _n(2.4 * s), _n(dirn * -1.6 * s), _n(1 * s), _n(dirn * -2.2 * s)])}"
            f"M{_join([_n(x), _n(y)])}c{_join([_n(3 * s), _n(dirn * 2.5 * s), _n(3.4 * s), _n(dirn * 6 * s), _n(.6 * s), _n(dirn * 6.6 * s)])}"
            f"c{_join([_n(-1.8 * s), _n(dirn * .4 * s), _n(-2.4 * s), _n(dirn * -1.6 * s), _n(-1 * s), _n(dirn * -2.2 * s)])}")


# ---- microtext ---------------------------------------------------------------------------------------

def microtext_line(text, width, seed):
    """A security-printing microtext rule: the text repeated in 11 px capitals between fine rules, fitted
    exactly to `width` (textLength), with a seed-chosen rule style. 18 px tall."""
    r = _rng("micro", seed, text)
    size = 11
    sep = r.choice(["  ·  ", "  ◆  ", "  ·  "])
    unit = text.upper().strip() + sep
    pad = 4
    avail = width - 2 * pad
    # run the legend continuously from a seed-chosen word, cut at a word boundary, and let
    # textLength spread the remainder as letter spacing (never stretching the glyphs)
    words = (unit * (int(avail / max(1, _text_w(unit, size))) + 3)).split(" ")
    k = r.randrange(max(1, len(unit.split(" ")) - 1))
    words = words[k:]
    body = ""
    for wd in words:
        nxt = (body + " " + wd) if body else wd
        if _text_w(nxt, size) * .94 > avail:
            break
        body = nxt
    body = body.strip(" ·◆")
    tw = avail
    H = 18
    style = r.choice(["double", "beaded", "wave"])
    parts = []
    if style == "double":
        parts.append(_path(f"M0,.8H{_n(width)}M0,{_n(H - .8)}H{_n(width)}", W1))
        parts.append(_path(f"M0,2.6H{_n(width)}M0,{_n(H - 2.6)}H{_n(width)}", W0))
        base = 12.6
    elif style == "beaded":
        parts.append(_path(f"M0,.5H{_n(width)}M0,{_n(H - .5)}H{_n(width)}", W1))
        parts.append(f'<path d="M2,2.3H{_n(width - 1)}" {K} stroke-width="1.4" stroke-linecap="round" stroke-dasharray="0 3.2"/>')
        base = 13.4
    else:
        parts.append(_path(f"M0,.5H{_n(width)}M0,{_n(H - .5)}H{_n(width)}", W1))
        parts.append(_path(_wave(0, width, 2.2, .8, 5, 0), WF))
        base = 13.6
    # the text is fitted to the measured width; any spare width is shared at the ends by small stars
    parts.append(_text(width / 2, base, body, size, tw, "middle", 600, "spacing"))
    return _svg(width, H, "".join(parts))


# ---- guilloche panel ---------------------------------------------------------------------------------

def guilloche_panel(width, height, seed, legend=None):
    """A banknote-style panel of overlapping guilloche for the empty tail of a sheet, 80 to 400 px tall.

    Anatomy (all scaled from the height so it reads as intentional at every size): heavy rule and
    hairline; from 150 px a rope border with corner fans; a chain-link lathe ground (two wave families
    in counter-phase, one seamless pattern tile); a rope ribbon across the middle carrying a central
    rosette and, when the width allows, two flanking rosettes; an optional 11 px legend."""
    w, h = width, height
    r = _rng("panel", seed, w, h)
    uid = _uid("panel", seed, w, h)
    rp = _rope_params(seed, "panel")
    parts, defs = [], []
    parts.append(_path(_rect_d(.8, .8, w - 1.6, h - 1.6), W2))
    parts.append(_path(_rect_d(3, 3, w - 6, h - 6), W0))
    fx, fy, fw, fh = 4.6, 4.6, w - 9.2, h - 9.2

    tall = h >= 150
    if tall:  # rope border inside the frame
        rb2 = 4.6
        e = fx + rb2 + .8
        brp = dict(rp, lines=1, second="none", phases=3)
        clip = (f'<clipPath id="{uid}b"><path d="M{_n(fx)},{_n(fy)}H{_n(fx + fw)}V{_n(fy + fh)}H{_n(fx)}Z'
                f'M{_n(fx + 2 * rb2 + 1.6)},{_n(fy + 2 * rb2 + 1.6)}V{_n(fy + fh - 2 * rb2 - 1.6)}'
                f'H{_n(fx + fw - 2 * rb2 - 1.6)}V{_n(fy + 2 * rb2 + 1.6)}Z"/></clipPath>')
        defs.append(clip)
        rope = (_rope_band(fx, fx + fw, e, rb2, brp) + _rope_band(fx, fx + fw, h - e, rb2, brp)
                + _rope_band(fy, fy + fh, e, rb2, brp, True) + _rope_band(fy, fy + fh, w - e, rb2, brp, True))
        parts.append(f'<g clip-path="url(#{uid}b)">{_path(rope, WF)}</g>')
        gi = 2 * rb2 + 1.6
        parts.append(_path(_rect_d(fx + gi, fy + gi, fw - 2 * gi, fh - 2 * gi), W1))
        fx, fy, fw, fh = fx + gi + .5, fy + gi + .5, fw - 2 * gi - 1, fh - 2 * gi - 1

    # ground: chain-link lathe work, one seamless tile
    P = r.choice([10, 11, 12, 13])
    pitch = r.choice([4.8, 5.2, 5.6])
    A = pitch * r.choice([.32, .38, .44])
    tile = _tile_wave(P, pitch, A, 0) + _tile_wave(P, pitch, A, P / 2)
    defs.append(f'<pattern id="{uid}p" width="{_n(P)}" height="{_n(pitch)}" patternUnits="userSpaceOnUse"'
                f' x="{_n(fx)}" y="{_n(fy)}">{_path(tile, WF)}</pattern>')
    parts.append(f'<rect x="{_n(fx)}" y="{_n(fy)}" width="{_n(fw)}" height="{_n(fh)}" fill="url(#{uid}p)"/>')

    cx, cy = w / 2, h / 2
    leg = 5 if legend and h >= 120 else 0
    portrait = h > w * 1.15
    # lay out along the long axis: a centre rosette, and two flanking ones when there is room
    Lm, Lc = (fh - 2 * leg, fw) if portrait else (fw, fh - 2 * leg)
    Rc = min(Lc / 2 - 3, Lm * .2)
    room = Lm / 2 - Rc - 6
    Rs = min(Rc * .62, (room - 24) / 2, Lc / 2 - 6)
    offs = [(0, Rc)]
    if Rs >= 14:
        off = Rc + 14 + Rs if tall else min(Lm / 2 - Rs - 12, Rc + Rs + max(30, Lm * .1))
        offs += [(-off, Rs), (off, Rs)]
    xs = [((cx, cy + o) if portrait else (cx + o, cy), R) for o, R in offs]
    # rope ribbon along the long axis, behind the rosettes
    rb = max(4.5, min(9, min(w, h) * .045))
    rrp = dict(rp, lines=1, second="none", phases=max(3, rp["phases"]))
    if portrait:
        parts.append(f'<path d="{_rect_d(cx - rb - 1.6, fy, 2 * rb + 3.2, fh)}" fill="#fff" {K} stroke-width="{W0}"/>')
        parts.append(_path(_rope_band(fy, fy + fh, cx, rb, rrp, True), WF))
    else:
        parts.append(f'<path d="{_rect_d(fx, cy - rb - 1.6, fw, 2 * rb + 3.2)}" fill="#fff" {K} stroke-width="{W0}"/>')
        parts.append(_path(_rope_band(fx, fx + fw, cy, rb, rrp), WF))
    if tall:  # corner fans in the field
        fan_r = min(fh, fw) * .2
        fans, outl = "", ""
        for (x0, y0, a0) in ((fx, fy, 0), (fx + fw, fy, math.pi / 2), (fx + fw, fy + fh, math.pi), (fx, fy + fh, 1.5 * math.pi)):
            def pt(rad, t):
                return f"{_n(x0 + rad * math.cos(t))},{_n(y0 + rad * math.sin(t))}"
            outl += f"M{_n(x0)},{_n(y0)}L{pt(fan_r, a0)}A{_n(fan_r)},{_n(fan_r)} 0 0 1 {pt(fan_r, a0 + math.pi / 2)}Z"
            for k in range(1, 16):
                t = a0 + math.pi / 2 * k / 16
                fans += f"M{pt(fan_r * .3, t)}L{pt(fan_r - 4.4, t)}"
            fans += f"M{pt(fan_r - 3, a0)}A{_n(fan_r - 3)},{_n(fan_r - 3)} 0 0 1 {pt(fan_r - 3, a0 + math.pi / 2)}"
            fans += f"M{pt(fan_r * .3, a0)}A{_n(fan_r * .3)},{_n(fan_r * .3)} 0 0 1 {pt(fan_r * .3, a0 + math.pi / 2)}"
        parts.append(_path(outl, W1, "#fff") + _path(fans, W0))
    seeds = [r.randrange(1 << 30) for _ in xs]
    base = sum(len(p) for p in parts) + sum(len(d) for d in defs)
    for sparse in (1.0, 1.25, 1.55, 1.9, 2.4, 3.0):
        ros = "".join(_rosette_body(x, y, R, sd, 0, 1.6 if R < 60 else 2.0, sparse) for ((x, y), R), sd in zip(xs, seeds))
        if base + len(ros) < 38000:
            break
    else:  # still too rich: keep only the central rosette
        ros = _rosette_body(cx, cy, xs[0][1], seeds[0], 0, 2.0, 1.6)
    parts.append(ros)
    if legend and h >= 120:
        lg = legend.upper()
        tw = _text_w(lg, 11)
        y = h - 6.2 if tall else fy + fh - 6
        parts.append(f'<path d="{_rect_d(w / 2 - tw / 2 - 16, y - 11, tw + 32, 15.4)}" fill="#fff" {K} stroke-width="{W1}"/>')
        parts.append(f'<path d="{_star(w / 2 - tw / 2 - 8, y - 3.5, 3, .6)}{_star(w / 2 + tw / 2 + 8, y - 3.5, 3, .6)}" fill="#000"/>')
        parts.append(_text(w / 2, y, lg, 11, tw, "middle", 600))
    return _svg(w, h, "".join(parts), "".join(defs))


def _tile_wave(P, pitch, A, phase):
    """Seamless pattern tile (P wide, pitch tall): one sine row, repeated above and below so the crests
    that cross the tile seam are drawn on both sides of it."""
    return "".join(_wave(0, P, pitch * .5 + k * pitch, A, P, phase) for k in (-1, 0, 1))
