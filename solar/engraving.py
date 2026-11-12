"""Procedural engraving for the Evening Edition: rose-engine guilloche, seeded by the night.

A rose engine turns a blank against a cutter guided by a cam; each pass traces a polar curve
r(t) = r0 + sum(a * sin(n * t + phase)), and the plate is turned a few degrees between passes. Here
one pass is drawn once (in <defs>) and the other passes are <use> copies, rotated, so a dense
rosette costs a few kilobytes. Every choice (lobes, amplitudes, the number of passes) comes from a
random.Random seeded by the date, so no two nights' plates are the same.
"""
import math
import random

K = 'stroke="#000"'


def n1(x):
    s = f"{x:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return "0" if s in ("", "-0", "-") else s


def rng_for(night, salt=""):
    return random.Random(f"{night.isoformat()}:{salt}")


def cam(r0, terms, samples=240):
    """One closed pass of the cutter: a polar curve about (0, 0), as path data."""
    pts = []
    for i in range(samples):
        t = 2 * math.pi * i / samples
        r = r0 + sum(a * math.sin(n * t + ph) for a, n, ph in terms)
        pts.append((r * math.cos(t), r * math.sin(t)))
    d = f"M{n1(pts[0][0])},{n1(pts[0][1])}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d += f"l{n1(x1 - x0)},{n1(y1 - y0)}"
    return d + "Z"


def passes(pid, d, k, sweep, sw=.5):
    """The pass `d` and k - 1 copies, the plate turned by sweep / k degrees between each."""
    out = f'<path id="{pid}" d="{d}" fill="none" {K} stroke-width="{sw}"/>'
    for i in range(1, k):
        out += f'<use href="#{pid}" xlink:href="#{pid}" transform="rotate({n1(sweep * i / k)})"/>'
    return out


def rosette(rng, pid, R=40):
    """A watch-dial rosette in three zones (outer cam band, compound cam, inner epitrochoid), rings
    between, a white boss at the centre for a numeral. Drawn about (0, 0)."""
    s = R / 40
    n_out = rng.choice((18, 20, 22, 24, 26))
    k_out = rng.choice((4, 5, 6))
    m = rng.choice((7, 8, 9, 10, 11))
    k_mid = rng.choice((4, 5, 6))
    p = rng.choice((9, 10, 12, 14))
    k_in = rng.choice((3, 4))
    ph = rng.uniform(0, math.pi)
    outer = cam(35.2 * s, [(2.6 * s, n_out, 0), (.7 * s, 2 * n_out, ph)], n_out * 10)
    mid = cam(28.4 * s, [(2.6 * s, m, 0), (1.0 * s, 3 * m, ph)], 220)
    inner = cam(22 * s, [(1.7 * s, p, 0), (rng.uniform(.3, .8) * s, 2 * p, ph)], 200)
    beads = "".join(f'<circle cx="{n1(39.4 * s * math.cos(a))}" cy="{n1(39.4 * s * math.sin(a))}" r=".6"/>'
                    for a in (2 * math.pi * i / 60 for i in range(60)))
    return (f'<circle r="{n1(R)}" fill="#fff" {K} stroke-width="1.6"/>'
            + passes(f"{pid}o", outer, k_out, 360 / n_out)
            + f'<circle r="{n1(31.6 * s)}" fill="none" {K} stroke-width=".6"/>'
            + passes(f"{pid}m", mid, k_mid, 360 / m)
            + f'<circle r="{n1(25.2 * s)}" fill="none" {K} stroke-width=".6"/>'
            + passes(f"{pid}i", inner, k_in, 360 / p, .45)
            + f'<circle r="{n1(38.2 * s)}" fill="none" {K} stroke-width=".6"/>' + beads
            + f'<circle r="{n1(18.6 * s)}" fill="#fff" {K} stroke-width="1"/>'
            + f'<circle r="{n1(17 * s)}" fill="none" {K} stroke-width=".5"/>')


def ring(rng, pid, r_in, r_out):
    """A plain guilloche ring between two radii (for the moon's medallion)."""
    n = rng.choice((24, 30, 36, 40))
    k = rng.choice((3, 4))
    mid, amp = (r_in + r_out) / 2, (r_out - r_in) / 2 - .7
    d = cam(mid, [(amp * .8, n, 0), (amp * .2, 3 * n, rng.uniform(0, 3))], n * 8)
    return passes(pid, d, k, 360 / n, .45)


def band(rng, pid, w, h):
    """A straight guilloche ribbon, w x h: barleycorn waves, phase-shifted copies. Drawn from (0, 0)."""
    period = rng.choice((14, 16, 18, 20))
    k = rng.choice((3, 4))
    mod = rng.choice((3, 4, 5)) * period
    amp = h / 2 - .9
    pts, x = [], -period
    while x <= w + period:
        a = amp * (.62 + .38 * math.cos(2 * math.pi * x / mod))
        pts.append((x, h / 2 + a * math.sin(2 * math.pi * x / period)))
        x += period / 12
    d = f"M{n1(pts[0][0])},{n1(pts[0][1])}" + "".join(f"l{n1(b[0] - a[0])},{n1(b[1] - a[1])}" for a, b in zip(pts, pts[1:]))
    out = f'<path id="{pid}" d="{d}" fill="none" {K} stroke-width=".45"/>'
    for i in range(1, k):
        out += f'<use href="#{pid}" xlink:href="#{pid}" transform="translate({n1(period * i / k)},0)"/>'
    return out


def stars(rng, n, box, avoid=()):
    """A deterministic star field: (x, y, r) inside box = (x0, y0, x1, y1), clear of the (x, y, r) in avoid."""
    x0, y0, x1, y1 = box
    out, tries = [], 0
    while len(out) < n and tries < n * 20:
        tries += 1
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if any((x - a) ** 2 + (y - b) ** 2 < (c + 3) ** 2 for a, b, c in avoid):
            continue
        out.append((x, y, rng.choice((.45, .5, .5, .6, .75))))
    return out
