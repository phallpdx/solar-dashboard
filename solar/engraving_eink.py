"""E-ink engraving helpers for the Evening Edition (Kindle Paperwhite 11: 300 ppi, 16 greys, DPR ~2).

The medium in one paragraph: one CSS px is two device px, so 0.5 CSS px is exactly one physical
pixel -- banknote-fine hairlines are free. Widths that are not multiples of 0.5 CSS px land as an
antialiased grey pixel next to a black one, which on a 16-level panel is a *real* grey, not mush:
so sub-pixel width is a tone control, the way an engraver controls tone by the depth of the cut.
Repeating patterns whose pitch is not a multiple of 0.5 CSS px beat against the pixel grid and
show moire bands; pitches that are multiples of 0.5 (1, 1.5, 2 ...) do not, when unrotated.
Large solid blacks ghost after a full refresh, so tone is built from line density instead.

Public API (all return SVG fragments or path data; coordinates are CSS px when the SVG has no
viewBox scaling -- see `px_scale` if it does):

  snap(v, step=.5)                       snap a width / pitch / coordinate to the device grid
  grey16(t)                              '#rrggbb' quantised to one of the panel's 16 levels
  safe_pitch(p)                          nearest moire-safe hatch pitch (multiple of 0.5 CSS px)
  swell_line(points, w0, w1, ...)        tapered / swelling burin stroke as a filled <path>
  swell_d(points, widths)                the same, path data only, per-point widths
  tonal_hatch(shape_d, tone_fn, seed, box, ...)   parallel lines whose width follows tone
  contour_hatch(lines, tone_fn, pitch)   swelling strokes along any family of curves
  mezzotint(shape_d, tone_fn, seed, box, ...)     stochastic rocker-ground stipple
  hairline_crosshatch(shape_d, box, ...) ghost-safe "dark" fill: 1-device-px crosshatch
  engraved_portrait_moon(phase, r, ...)  showpiece: bulino-modelled moon, phase-correct
  demo(path)                             writes the comparison sheet to /tmp/claude-0/shots/team/eink_demo.html

Standard library only.
"""
import math
import random

BLACK = "#000"


# ---------------------------------------------------------------- numbers and the device grid

def _f(v, nd=2):
    s = ("%." + str(nd) + "f") % v
    s = s.rstrip("0").rstrip(".") if "." in s else s
    if s in ("-0", ""):
        s = "0"
    return s


def snap(v, step=0.5):
    """Snap to the device-pixel grid (0.5 CSS px = 1 physical px at DPR 2)."""
    return round(v / step) * step


def safe_pitch(p, step=0.5):
    """A hatch pitch that will not alias at DPR 2: a whole number of device pixels, at least 2."""
    return max(2 * step, snap(p, step))


def grey16(t):
    """Darkness t in [0, 1] -> one of the panel's 16 exact grey levels (0x00, 0x11 ... 0xff).
    Off-level greys get dithered by the Kindle's waveform; on-level greys are flat and clean."""
    t = min(1.0, max(0.0, t))
    lvl = 15 - int(round(t * 15))
    h = "%02x" % (lvl * 17)
    return "#" + h * 3


def px_scale(css_width, viewbox_width):
    """User units per CSS px for an SVG drawn at css_width with a viewBox viewbox_width wide.
    Multiply hairline widths by this so 0.5 CSS px stays one device pixel after scaling."""
    return viewbox_width / float(css_width)


# ---------------------------------------------------------------- swelling burin strokes

def _normals(pts):
    n = len(pts)
    out = []
    for i in range(n):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        out.append((-dy / L, dx / L))
    return out


def swell_d(points, widths, nd=2):
    """Closed outline of a stroke whose full width at points[i] is widths[i] (path data).
    Round-ish ends come from the widths tapering to ~0 at the ends."""
    if len(points) < 2:
        return ""
    nr = _normals(points)
    left = [(x + nx * w / 2, y + ny * w / 2) for (x, y), (nx, ny), w in zip(points, nr, widths)]
    right = [(x - nx * w / 2, y - ny * w / 2) for (x, y), (nx, ny), w in zip(points, nr, widths)]
    ring = left + right[::-1]
    d = "M%s %s" % (_f(ring[0][0], nd), _f(ring[0][1], nd))
    px, py = ring[0]
    for x, y in ring[1:]:
        d += "l%s %s" % (_f(x - px, nd), _f(y - py, nd))
        px, py = px + float(_f(x - px, nd)), py + float(_f(y - py, nd))
    return d + "z"


def swell_line(points, w0, w1, profile="swell", wmax=None, fill=BLACK, nd=2):
    """A burin cut as a filled path. profile:
      'taper' -> width runs linearly w0 -> w1 (a cut that enters deep and lifts out),
      'swell' -> w0 at both ends, swelling to w1 in the middle (the classic lozenge line),
      'entry' -> w0 -> w1 with a sine ease, sharp point at the start (a flick cut).
    Widths are CSS px; 0.5 = one device pixel."""
    n = len(points)
    ws = []
    for i in range(n):
        t = i / (n - 1.0) if n > 1 else 0
        if profile == "taper":
            w = w0 + (w1 - w0) * t
        elif profile == "entry":
            w = w0 + (w1 - w0) * math.sin(t * math.pi / 2)
        else:
            w = w0 + (w1 - w0) * math.sin(t * math.pi)
        ws.append(w)
    return '<path d="%s" fill="%s"/>' % (swell_d(points, ws, nd), fill)


def _runs(points, widths, wmin):
    """Split a polyline where the width falls below wmin (the burin lifts: paper shows)."""
    run_p, run_w, out = [], [], []
    for p, w in zip(points, widths):
        if w >= wmin:
            run_p.append(p)
            run_w.append(w)
        else:
            if len(run_p) > 1:
                out.append((run_p, run_w))
            run_p, run_w = [], []
    if len(run_p) > 1:
        out.append((run_p, run_w))
    # taper the ends of each run so cuts start and finish in a point, as a real burin does
    for rp, rw in out:
        rw[0] *= 0.35
        rw[-1] *= 0.35
    return out


def contour_hatch(lines, tone_fn, pitch, wmin=0.12, gain=0.92, gamma=1.0, nd=2):
    """Swelling strokes along any family of curves (each a list of (x, y)). Width at a point is
    pitch * gain * tone(x, y)**gamma, so line coverage == tone: light areas thin to hairlines and
    break off into paper, shadows swell until neighbouring cuts nearly touch. Returns path data."""
    d = []
    for pts in lines:
        ws = [pitch * gain * (max(0.0, min(1.0, tone_fn(x, y))) ** gamma) for x, y in pts]
        for rp, rw in _runs(pts, ws, wmin):
            d.append(swell_d(rp, rw, nd))
    return "".join(d)


def tonal_hatch(shape_d, tone_fn, seed=0, box=None, angle=-30.0, pitch=1.5, step=1.0,
                clip_id=None, wmin=0.12, gain=0.92, wobble=0.0):
    """Straight-line engraving whose line *width* follows tone (bulino / intaglio), clipped to
    shape_d. tone_fn(x, y) -> darkness 0..1 in the same coordinates. box = (x0, y0, x1, y1) to
    cover; pitch is snapped to the device grid. wobble (CSS px) adds a slight hand tremor seeded
    by `seed` so a plate never looks machine-ruled. Returns <clipPath> + <path>."""
    rng = random.Random("th:%s" % seed)
    x0, y0, x1, y1 = box
    pitch = safe_pitch(pitch)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    R = math.hypot(x1 - x0, y1 - y0) / 2 + pitch
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)          # along the cut
    vx, vy = -uy, ux                           # across the cuts
    lines = []
    k = int(R / pitch)
    for j in range(-k, k + 1):
        off = j * pitch
        ph = rng.uniform(0, 6.28)
        pts = []
        s = -R
        while s <= R:
            wob = wobble * math.sin(s / 9.0 + ph)
            x = cx + ux * s + vx * (off + wob)
            y = cy + uy * s + vy * (off + wob)
            if x0 - 2 <= x <= x1 + 2 and y0 - 2 <= y <= y1 + 2:
                pts.append((x, y))
            elif pts:
                lines.append(pts)
                pts = []
            s += step
        if pts:
            lines.append(pts)
    cid = clip_id or "th%s" % abs(hash(("th", seed, angle))) % 10 ** 6
    return ('<clipPath id="%s"><path d="%s"/></clipPath><path clip-path="url(#%s)" fill="%s" d="%s"/>'
            % (cid, shape_d, cid, BLACK, contour_hatch(lines, tone_fn, pitch, wmin, gain)))


def mezzotint(shape_d, tone_fn, seed=0, box=None, cell=1.0, clip_id=None, gamma=1.0):
    """Rocker-ground mezzotint: one jittered dot per cell, dot area proportional to tone, so the
    page shows a velvety grain rather than a halftone grid (no moire, no regular texture to beat
    with the pixel grid). Dots are squares snapped to whole device px -- at 300 ppi a 1x1 or 2x2
    device-pixel speck is the grain itself. Returns <clipPath> + <path>."""
    rng = random.Random("mz:%s" % seed)
    x0, y0, x1, y1 = box
    d = []
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            jx, jy = rng.uniform(0, cell), rng.uniform(0, cell)
            t = max(0.0, min(1.0, tone_fn(x + jx, y + jy))) ** gamma
            # area t*cell^2 -> side; plus a little random burr so equal tones are not equal dots
            side = cell * math.sqrt(t) * rng.uniform(0.8, 1.2)
            side = snap(side, 0.5)
            if side > 0 and rng.random() < 0.15 + 0.85 * t:
                px, py = snap(x + jx - side / 2), snap(y + jy - side / 2)
                d.append("M%s %sh%sv%sh-%sz" % (_f(px, 1), _f(py, 1), _f(side, 1), _f(side, 1), _f(side, 1)))
            x += cell
        y += cell
    cid = clip_id or "mz%s" % abs(hash(("mz", seed))) % 10 ** 6
    return ('<clipPath id="%s"><path d="%s"/></clipPath><path clip-path="url(#%s)" fill="%s" '
            'shape-rendering="crispEdges" d="%s"/>' % (cid, shape_d, cid, BLACK, "".join(d)))


def hairline_crosshatch(shape_d, box, pitch=2.0, angles=(45, -45), clip_id=None, width=0.5):
    """Ghost-safe 'black': crossed 1-device-px hairlines at a moire-safe pitch. Reads as a deep
    dark grey at arm's length, refreshes cleanly, and keeps texture -- use it wherever the art
    currently has a solid fill larger than a few px (moon dark side, hulls, silhouettes)."""
    x0, y0, x1, y1 = box
    pitch = safe_pitch(pitch)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    R = math.hypot(x1 - x0, y1 - y0) / 2 + pitch
    d = []
    for ang in angles:
        a = math.radians(ang)
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        k = int(R / pitch)
        for j in range(-k, k + 1):
            o = j * pitch
            ax, ay = cx + vx * o - ux * R, cy + vy * o - uy * R
            d.append("M%s %sl%s %s" % (_f(ax, 1), _f(ay, 1), _f(2 * R * ux, 1), _f(2 * R * uy, 1)))
    cid = clip_id or "hx%s" % abs(hash(("hx", shape_d[:40], angles))) % 10 ** 6
    return ('<clipPath id="%s"><path d="%s"/></clipPath><path clip-path="url(#%s)" fill="none" '
            'stroke="%s" stroke-width="%s" d="%s"/>' % (cid, shape_d, cid, BLACK, _f(width), "".join(d)))


def circle_d(cx, cy, r):
    return "M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 -%s 0z" % (
        _f(cx - r), _f(cy), _f(r), _f(r), _f(2 * r), _f(r), _f(r), _f(2 * r))


# ---------------------------------------------------------------- the showpiece

# Rough lunar maria as (longitude, latitude, radius) in degrees on the near side, darkness 0..1.
_MARIA = [(-57, 18, 20, .55), (-20, 28, 15, .60), (14, 26, 10, .55), (25, 11, 10, .50),
          (35, -6, 13, .50), (-15, -18, 13, .45), (52, 17, 7, .55), (-38, -5, 18, .45),
          (0, 8, 7, .40), (-5, -42, 4, .25)]
_CRATERS = [(-11, -43, 4.5), (-20, 10, 4.5), (-38, 8, 2.8), (28, -12, 3.5), (-48, -28, 4), (40, 30, 3)]


def _albedo_dark(lon, lat):
    """Extra darkness from maria (soft-edged), 0..~0.6."""
    t = 0.0
    for mlon, mlat, mr, k in _MARIA:
        dd = math.hypot((lon - mlon) * math.cos(math.radians(lat)), lat - mlat)
        if dd < mr * 1.4:
            t = max(t, k * min(1.0, (mr * 1.4 - dd) / (mr * 0.6)))
    for clon, clat, cr in _CRATERS:
        dd = math.hypot((lon - clon) * math.cos(math.radians(lat)), lat - clat)
        if dd < cr:
            t = max(t, 0.35 * (1 - dd / cr)) if dd > cr * .55 else max(t, .0)
    return t


def engraved_portrait_moon(phase, r=110, cx=None, cy=None, seed=0, pitch=1.5, tilt=10, pa=-24,
                           standalone=True, label=True):
    """A bulino-engraved moon. The lit hemisphere is cut in swelling lines that run along the
    moon's own parallels (projected, so they curve over the globe and describe the form), their
    width set by Lambertian light from the true phase angle plus mare albedo. The night side is a
    1-device-px crosshatch with faint earthshine, never a solid black (no ghosting). The limb is a
    swelling contour, heaviest on the dark side as an engraver would cut it.
    phase: 0 new, .25 first quarter, .5 full, .75 last quarter. r in CSS px."""
    phase %= 1.0
    cx = snap(r + 16 if cx is None else cx)
    cy = snap(r + 16 if cy is None else cy)
    e = 2 * math.pi * phase
    L = (math.sin(e), 0.0, -math.cos(e))     # sun direction, viewer is +z
    Ln = math.sqrt(sum(c * c for c in L))
    L = tuple(c / Ln for c in L)
    tau = math.radians(tilt)
    uid = "pm%d_%d" % (int(phase * 1000), abs(hash(seed)) % 10000)

    def lit(nx, ny, nz):
        return nx * L[0] + ny * L[1] + nz * L[2]

    def tone_sphere(x, y):
        X, Y = (x - cx) / r, (y - cy) / r
        q = 1 - X * X - Y * Y
        if q <= 0:
            return 0.0
        Z = math.sqrt(q)
        # back to lunar lon/lat (undo tilt about x axis)
        yy = Y * math.cos(tau) + Z * math.sin(tau)
        zz = -Y * math.sin(tau) + Z * math.cos(tau)
        lat = math.degrees(math.asin(max(-1, min(1, -yy))))
        lon = math.degrees(math.atan2(X, zz))
        lam = lit(X, Y, Z)
        if lam <= 0:
            return -1.0                                     # night side marker
        bright = lam ** 0.55                                # lunar regolith is flat-ish
        tone = (1 - bright) * 0.72 + _albedo_dark(lon, lat) * (0.35 + 0.5 * bright)
        tone += 0.10 * (1 - Z) ** 3                          # a breath of limb darkening
        return max(0.0, min(1.0, tone))

    # family of curves: parallels of latitude, tilted towards the viewer
    lines = []
    # parallels chosen so that, down the central meridian, the cuts land exactly `pitch` apart
    # on screen and on whole device pixels (snap(cy)) -- otherwise the varying spacing beats
    # against the pixel rows and paints false contour rings over the face.
    pitch = safe_pitch(pitch)
    nlat = int(r / pitch)
    for i in range(-nlat + 1, nlat):
        s = i * pitch / r
        if abs(s) >= 1:
            continue
        phi = math.asin(s) + tau                             # undo the tilt at lambda = 0
        if phi > math.pi / 2:
            continue
        pts = []
        lam = -math.pi
        while lam <= math.pi + 1e-9:
            x = math.cos(phi) * math.sin(lam)
            y0 = math.sin(phi)
            z0 = math.cos(phi) * math.cos(lam)
            y = y0 * math.cos(tau) - z0 * math.sin(tau)
            z = y0 * math.sin(tau) + z0 * math.cos(tau)
            if z > 0:
                pts.append((cx + r * x, cy - r * y))
            elif len(pts) > 1:
                lines.append(pts)
                pts = []
            elif pts:
                pts = []
            lam += max(0.02, 2.0 / (r * max(.15, math.cos(phi))))
        if len(pts) > 1:
            lines.append(pts)

    # Turn the whole family to the moon's position angle. Near-horizontal cuts whose width
    # varies put their edges at a slowly drifting sub-pixel row offset, which shows as vertical
    # banding at DPR 2; a cut at ~25 degrees samples the pixel grid evenly and the bands vanish.
    if pa:
        ca, sa = math.cos(math.radians(pa)), math.sin(math.radians(pa))
        lines = [[(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]
                 for pts in lines]

    def tone_lit(x, y):
        t = tone_sphere(x, y)
        return 0.0 if t < 0 else t

    body = contour_hatch(lines, tone_lit, pitch, wmin=0.14, gain=0.9, gamma=1.15, nd=1)
    disc = circle_d(cx, cy, r)

    # night side: the disc minus the lit region, as a terminator path
    k = math.cos(e)                                          # terminator ellipse x-scale
    if 0.02 < phase < 0.98 and abs(phase - .5) > 0.02:
        waxing = phase < .5
        rx = abs(k) * r
        sweep_limb = 0 if waxing else 1
        sweep_t = (0 if k > 0 else 1) if waxing else (1 if k > 0 else 0)
        night = "M%s %sA%s %s 0 0 %d %s %sA%s %s 0 0 %d %s %sZ" % (
            _f(cx), _f(cy - r), _f(r), _f(r), sweep_limb, _f(cx), _f(cy + r),
            _f(max(rx, .01)), _f(r), sweep_t, _f(cx), _f(cy - r))
    elif phase <= 0.02 or phase >= 0.98:
        night = disc
    else:
        night = ""
    parts = []
    if night:
        parts.append(hairline_crosshatch(night, (cx - r, cy - r, cx + r, cy + r), pitch=2.0,
                                         angles=(30, -60), clip_id=uid + "n"))
        # earthshine: maria faintly visible as an extra hairline direction inside the night
        es = []
        for pts in lines[::2]:
            seg = [p for p in pts if _albedo_dark(*_lonlat(p, cx, cy, r, tau)) > .3]
            if len(seg) > 1:
                es.append(seg)
        parts.append('<clipPath id="%sne"><path d="%s"/></clipPath><path clip-path="url(#%sne)" '
                     'fill="none" stroke="#000" stroke-width=".5" d="%s"/>' % (
                         uid, night, uid, "".join("M" + "L".join("%s %s" % (_f(x, 1), _f(y, 1)) for x, y in s)
                                                  for s in _split_gaps(es))))
    parts.append('<path fill="#000" d="%s"/>' % body)

    # limb: a swelling contour, heavy on the night side, a hairline on the lit side
    limb_pts, limb_w = [], []
    N = 360
    for i in range(N + 1):
        a = 2 * math.pi * i / N
        X, Y = math.cos(a), math.sin(a)
        lamb = lit(X, Y, 0.0)
        limb_pts.append((cx + (r + .25) * X, cy + (r + .25) * Y))
        limb_w.append(0.5 + 1.6 * max(0.0, -lamb) ** .7)
    parts.append('<path fill="#000" d="%s"/>' % swell_d(limb_pts, limb_w))
    # a fine double bezel, banknote style: hairline, gap, heavier rule, gap, hairline
    for dr, w in ((5, .5), (7.5, 1.0), (10, .5)):
        parts.append('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#000" stroke-width="%s"/>'
                     % (_f(cx), _f(cy), _f(r + dr), _f(w)))
    # micro-beads on the bezel (each bead = a 1 x 1 CSS px square at device-grid positions)
    nb = int(2 * math.pi * (r + 12.5) / 3)
    beads = "".join("M%s %sh1v1h-1z" % (_f(snap(cx + (r + 12.5) * math.cos(2 * math.pi * i / nb)) - .5, 1),
                                         _f(snap(cy + (r + 12.5) * math.sin(2 * math.pi * i / nb)) - .5, 1))
                    for i in range(nb))
    parts.append('<path d="%s"/>' % beads)
    svg = "".join(parts)
    if not standalone:
        return svg
    W = H = 2 * (r + 16)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="%s %s %s %s">%s</svg>'
            % (_f(W), _f(H), _f(cx - W / 2), _f(cy - H / 2), _f(W), _f(H), svg))


def _lonlat(p, cx, cy, r, tau):
    X, Y = (p[0] - cx) / r, (p[1] - cy) / r
    Z = math.sqrt(max(0.0, 1 - X * X - Y * Y))
    yy = Y * math.cos(tau) + Z * math.sin(tau)
    zz = -Y * math.sin(tau) + Z * math.cos(tau)
    return math.degrees(math.atan2(X, zz)), math.degrees(math.asin(max(-1, min(1, -yy))))


def _split_gaps(segs, gap=3.0):
    out = []
    for s in segs:
        cur = [s[0]]
        for a, b in zip(s, s[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) > gap:
                if len(cur) > 1:
                    out.append(cur)
                cur = []
            cur.append(b)
        if len(cur) > 1:
            out.append(cur)
    return out


# ---------------------------------------------------------------- demo sheet

def _svg(w, h, body, extra=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"%s>%s</svg>'
            % (w, h, w, h, extra, body))


def _hairline_ladder():
    """Widths x sub-pixel offsets, crispEdges vs geometricPrecision."""
    b = []
    widths = (0.25, 0.5, 0.75, 1.0, 1.5)
    for row, mode in enumerate(("geometricPrecision", "crispEdges")):
        y0 = 14 + row * 70
        b.append('<text x="2" y="%d" font-size="8" font-family="serif">%s</text>' % (y0 - 4, mode))
        for i, w in enumerate(widths):
            for j, off in enumerate((0, .25)):
                x = 4 + i * 56 + j * 26
                d = "".join("M%s %sv50" % (_f(x + 0.5 * k * 4 + off), y0) for k in range(5))
                b.append('<path d="%s" stroke="#000" stroke-width="%s" shape-rendering="%s"/>' % (d, w, mode))
        for i, w in enumerate(widths):
            b.append('<text x="%d" y="%d" font-size="7" font-family="serif">%s</text>' % (4 + i * 56, y0 + 60, w))
    return _svg(290, 150, "".join(b))


def _moire_strip():
    """Pattern pitches 1.0 / 1.25 / 1.5 / 1.75 at 0 and 30 degrees: does it alias at 2x?"""
    b, defs = [], []
    for i, p in enumerate((1.0, 1.25, 1.5, 1.75, 2.0)):
        for j, ang in enumerate((0, 30)):
            pid = "mp%d%d" % (i, j)
            defs.append('<pattern id="%s" width="%s" height="%s" patternUnits="userSpaceOnUse" '
                        'patternTransform="rotate(%s)"><path d="M0 %sH%s" stroke="#000" stroke-width=".5"/></pattern>'
                        % (pid, p, p, ang, _f(p / 2), p))
            b.append('<rect x="%d" y="%d" width="52" height="52" fill="url(#%s)"/>' % (4 + i * 57, 4 + j * 64, pid))
        b.append('<text x="%d" y="130" font-size="8" font-family="serif">%s</text>' % (8 + i * 57, p))
    return _svg(290, 136, "<defs>%s</defs>%s" % ("".join(defs), "".join(b)))


def _ball(kind):
    r, cx, cy = 40, 46, 46
    L = (-.55, -.5, .67)

    def tone(x, y):
        X, Y = (x - cx) / r, (y - cy) / r
        q = 1 - X * X - Y * Y
        if q <= 0:
            return 0
        lam = min(1, max(0, X * L[0] + Y * L[1] + math.sqrt(q) * L[2]))
        return min(1, (1 - lam) ** 1.2 * 1.05)
    d = circle_d(cx, cy, r)
    box = (cx - r, cy - r, cx + r, cy + r)
    if kind == "flat":
        body = ('<defs><pattern id="fh" width="1.6" height="1.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                '<path d="M0 .8H1.6" stroke="#000" stroke-width=".55"/></pattern></defs>'
                '<path d="%s" fill="url(#fh)"/>' % d)
    elif kind == "tonal":
        body = tonal_hatch(d, tone, 1, box, angle=-35, pitch=1.5, clip_id="tb", wobble=.25)
    elif kind == "mezzo":
        body = mezzotint(d, tone, 2, box, cell=1.0, clip_id="mzb")
    else:
        body = "".join('<clipPath id="g%d"><path d="%s"/></clipPath>' % (0, d)) + \
            "".join('<rect clip-path="url(#g0)" x="%d" y="0" width="%d" height="92" fill="%s"/>'
                    % (cx - r + i * 5, 5, grey16(tone(cx - r + i * 5 + 2.5, cy - 20))) for i in range(16))
    body += '<path d="%s" fill="none" stroke="#000" stroke-width=".5"/>' % d
    return _svg(92, 92, body)


def _swell_samples():
    b = []
    for i, (w0, w1, prof) in enumerate(((0, 2.2, "swell"), (1.8, 0, "taper"), (0, 1.6, "entry"))):
        pts = [(6 + t * 1.8, 12 + i * 22 + 7 * math.sin(t / 9.0)) for t in range(150)]
        b.append(swell_line(pts, w0, w1, prof))
    # a bulino "flick" fan: 24 cuts radiating, each a lozenge
    for k in range(24):
        a = -math.pi / 2 + (k - 11.5) * .06
        pts = [(140 + math.cos(a) * s, 80 + math.sin(a) * s) for s in range(4, 70, 2)]
        b.append(swell_line(pts, 0, .3 + 1.0 * abs(math.sin(k / 3.0)), "swell"))
    return _svg(290, 84, "".join(b))


def _grey_ramp():
    b = "".join('<rect x="%d" y="0" width="18" height="20" fill="%s"/>' % (i * 18, grey16(i / 15.0)) for i in range(16))
    return _svg(288, 20, b)


def demo(path="/tmp/claude-0/shots/team/eink_demo.html"):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    moons = "".join('<figure>%s<figcaption>phase %s</figcaption></figure>'
                    % (engraved_portrait_moon(p, 62, seed=p), p) for p in (.18, .38, .62))
    html = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=618">
<title>E-ink engraving tests</title>
<style>
body{margin:0;padding:10px 12px;background:#fff;color:#000;font:14px/1.3 Georgia,serif;width:594px}
h2{font-size:15px;margin:10px 0 4px;letter-spacing:.06em;text-transform:uppercase}
p{margin:0 0 4px;font-size:12px}
.row{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap}
figure{margin:0;text-align:center}figcaption{font-size:11px}
.hero{text-align:center}
</style></head><body>
<h2>The showpiece: bulino moon</h2>
<p>Swelling cuts along the moon's own parallels; width = light. Night side is 1-device-px crosshatch, not black.</p>
<div class="hero">%s</div>
<div class="row">%s</div>
<h2>Same ball, four ways</h2>
<div class="row">
<figure>%s<figcaption>flat pattern (today)</figcaption></figure>
<figure>%s<figcaption>tonal_hatch</figcaption></figure>
<figure>%s<figcaption>mezzotint</figcaption></figure>
<figure>%s<figcaption>grey16 bands</figcaption></figure>
</div>
<h2>Burin strokes: swell_line</h2>%s
<h2>Hairlines: width x offset</h2><p>Left of each pair on the device grid, right shifted 0.25 CSS px.</p>%s
<h2>Hatch pitch moire (0.5px lines)</h2><p>Top unrotated, bottom 30&deg;.</p>%s
<h2>The 16 panel greys</h2>%s
</body></html>""" % (engraved_portrait_moon(.3, 150, seed=1), moons,
                     _ball("flat"), _ball("tonal"), _ball("mezzo"), _ball("grey"),
                     _swell_samples(), _hairline_ladder(), _moire_strip(), _grey_ramp())
    with open(path, "w") as fh:
        fh.write(html)
    return path


if __name__ == "__main__":
    print(demo())
