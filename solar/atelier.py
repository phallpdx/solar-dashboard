"""The Evening Edition's art direction: where ornament goes, and how it meets the type.

This module owns composition only. The scrollwork itself is cut by `engraving_hand` (acanthus scrolls,
running scrolls, region fills) and the pictures by `scene_river`, `scene_city` and `scene_music`;
each is called through an adapter with a plain fallback, so a page always builds.

The rules of the page:

* The page's ground is one whole engraving of foliage the size of the screen. Plaques and plates are laid
  over it with room between them, so every box is bordered by drawing and no room is left as a tint.
* One moulding everywhere: heavy rule, a light gap, fine rule. Text plaques carry it as CSS rings;
  art panels, cartouches, the frame and the initial draw the same three lines.
* Scrollwork lives only in regions whose shape is known when it is drawn: the four bands of the frame
  (the page's title plaque is set into the top band and the scrolls spring from it), the bottom panel
  (drawn once for each height it can take, never cropped) and the initial.

Everything here is a stand-alone SVG written to the edition's art/ folder and used as a CSS image, so
the reader's CSS reset cannot touch it, the pages and kindle.css stay small, and a page fetches only
the one panel that fits its free room.
"""
import importlib
import re
import zlib
from urllib.parse import quote

PAGE_W = 618
BAND = 36           # the frame's band, all four sides
PLAQUE = 6          # a text plaque's moulding reaches this far outside its box
PANEL_W = 542       # art panels: the 530 px measure plus the moulding either side
HEIGHTS = (60, 90, 120, 160, 220, 300, 400)   # the bottom panel is drawn for each of these, so it is never cropped or padded
FRIEZE_H, FRIEZE2_H, BEAD_H = 26, 44, 12

XMLNS = 'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'


def _n(x):
    s = f"{x:.1f}"
    return s[:-2] if s.endswith(".0") else s


def data_uri(svg):
    return 'url("data:image/svg+xml,%s")' % quote(svg.replace('"', "'"), safe=" =:/,.-'()<>;!*+@?&_~")


def _mod(name):
    try:
        return importlib.import_module(f".{name}", __package__)
    except Exception:  # noqa: BLE001
        return None


def _seed(*parts):
    return zlib.crc32("|".join(str(p) for p in parts).encode()) % 100000


# ---- the two grounds and the moulding -------------------------------------------------------------
def field_tile():
    """The page field between plaques: a drawn ground (the engraver's, when it offers one; else an
    imbricated scale ground), small enough that a straight edge can meet it anywhere."""
    m = _mod("engraving_hand")
    for name in ("texture_tile", "ground_tile", "diaper_tile"):
        if m and hasattr(m, name):
            try:
                t = getattr(m, name)()
                if isinstance(t, (tuple, list)) and len(t) == 3:
                    return t
            except Exception:  # noqa: BLE001
                pass
    # the deep punched ground: cut away to black, then matted with staggered rows of punch marks
    return (f'<svg {XMLNS} width="5" height="5" viewBox="0 0 5 5"><rect width="5" height="5"/>'
            '<path d="M1.25 1.25h0M3.75 3.75h0" stroke="#fff" stroke-width="1" stroke-linecap="round"/></svg>', 5, 5)


DEFS = ('<defs>'
        '<pattern id="am" width="3" height="3" patternUnits="userSpaceOnUse">'
        '<path d="M-1 1L1-1M0 3L3 0M2 4L4 2M-1 2L1 4M0 0L3 3M2-1L4 1" stroke="#000" stroke-width=".5"/></pattern>'
        '<pattern id="af" width="3" height="3" patternUnits="userSpaceOnUse">'
        '<path d="M-1 1L1-1M0 3L3 0M2 4L4 2" stroke="#000" stroke-width=".5"/></pattern>'
        '</defs>')


def _matte(x, y, w, h, rx=0):
    return f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}"{f" rx={chr(34)}{_n(rx)}{chr(34)}" if rx else ""} fill="url(#am)"/>'


def moulding(x, y, w, h, rx=0, fill="none", heavy=1.0):
    """The house moulding round a box, drawn inward from (x, y, w, h): heavy rule, light gap, fine rule.
    `fill` is what lies inside the fine rule."""
    def r(i, sw, f, stroke="#000"):
        rr = max(0, rx - i) if rx else 0
        return (f'<rect x="{_n(x + i)}" y="{_n(y + i)}" width="{_n(w - 2 * i)}" height="{_n(h - 2 * i)}"'
                + (f' rx="{_n(rr)}"' if rr else "") + f' fill="{f}" stroke="{stroke}" stroke-width="{sw}"/>')
    a = heavy / 2
    return r(a, heavy, "#fff") + r(heavy + 1.75, .5, fill)


def oval_moulding(cx, cy, rx, ry, fill="none", heavy=1.0):
    a = heavy / 2
    return (f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(rx - a)}" ry="{_n(ry - a)}" fill="#fff" stroke="#000" stroke-width="{heavy}"/>'
            f'<ellipse cx="{_n(cx)}" cy="{_n(cy)}" rx="{_n(rx - heavy - 1.75)}" ry="{_n(ry - heavy - 1.75)}" fill="{fill}" stroke="#000" stroke-width=".5"/>')


MOULD_IN = 3.0  # the moulding's depth with a 1 px heavy rule: where the inside begins


# ---- adapters: the engraver's hand ------------------------------------------------------------------
_UID = [0]


def _scope(markup):
    """Give a block of markup its own id space, so two blocks in one drawing never collide."""
    ids = set(re.findall(r'\bid="([^"]+)"', markup))
    if not ids:
        return markup
    _UID[0] += 1
    p = f"q{_UID[0]}"
    markup = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{p}{m.group(1)}"', markup)
    markup = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{p}{m.group(1)})' if m.group(1) in ids else m.group(0), markup)
    return re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}{m.group(1)}"' if m.group(1) in ids else m.group(0), markup)


def _strip_svg(s):
    s = s.strip()
    if s.startswith("<svg") or s.startswith("<?xml"):
        s = re.sub(r"^.*?<svg[^>]*>", "", s, count=1, flags=re.S)
        s = re.sub(r"</svg>\s*$", "", s)
    return s


def _hand(fn, *a, **kw):
    """Call one of the engraver's primitives; unknown keyword arguments are dropped one by one, and a
    missing module or a failure gives an empty string (the region keeps its ground)."""
    m = _mod("engraving_hand")
    f = getattr(m, fn, None) if m else None
    if not f:
        return ""
    kw = dict(kw)
    while True:
        try:
            return _scope(f(*a, **kw))
        except TypeError as e:
            bad = re.search(r"unexpected keyword argument '(\w+)'", str(e))
            if bad and bad.group(1) in kw:
                kw.pop(bad.group(1))
                continue
            return ""
        except Exception:  # noqa: BLE001
            return ""


GROUND = dict(matte_style="pearl")   # the engraver's drawn ground inside ornament, when it has one


def running_scroll(x, y, w, h, orientation="h", seed=0, symmetric=False, **kw):
    return (_hand("running_scroll", x, y, w, h, orientation, seed, symmetric, **dict(GROUND, **kw))
            or _hand("running_scroll", x, y, w, h, orientation, seed, symmetric, **kw))


def fill_region(w, h, seed=0, hole=None, x=0, y=0, **kw):
    return _hand("fill_region", w, h, seed, hole=hole, x=x, y=y, **kw)


_CORNER_EGG = {"tl": "p", "tr": "paw", "bl": "dog", "br": "heron"}


def corner(size, x, y, quadrant, seed=0, **kw):
    """A corner boss: the engraver's ground and one whole scroll, a mark hidden in its eye."""
    sc = _hand("scroll", x + size / 2, y + size / 2, size / 2 - 5, terminal=_CORNER_EGG.get(quadrant, "flower"),
               direction=1 if quadrant in ("tl", "br") else -1, seed=seed)
    return moulding(x, y, size, size, fill="#fff", heavy=1.5) + sc


# ---- adapters: the pictures -------------------------------------------------------------------------
_SCENES = {
    "river": ("scene_river", "dusk"), "night": ("scene_river", "night"), "dog": ("scene_river", "goodnight"),
    "bridge": ("scene_city", "bridge"), "sky": ("scene_city", "sky"),
    "jazz": ("scene_music", "jazz"), "lotus": ("scene_music", "lotus"),
}
# what hides in the scroll eyes on each page (left half first)
EGGS = {"river": ("heron", "paw"), "night": ("p", "heron"), "dog": ("dog", "paw"), "bridge": ("p", "paw"),
        "sky": ("heron", "p"), "jazz": ("drumsticks", "p"), "lotus": ("bud", "dog")}


FOREST = ("lotus", "night", "dog")


def ground(x, y, w, h, style="pearl"):
    """The engraver's drawn ground for a region (so no sliver is ever a plain tint); a cross-cut only if
    the engraver's module is missing."""
    return _hand("matte", w, h, x, y, style=style) or _matte(x, y, w, h)


def _old_plate(theme, w, h, seed, moon):
    try:
        if theme == "jazz":
            return _mod("plate_jazz").plate(w, h, seed)
        if theme == "lotus":
            return _mod("plate_thai").lotus(w, h, seed)
        if theme in ("bridge", "sky"):
            return _mod("plate_thai").bridge(w, h, seed, moon)
        return _mod("plate_river").plate(w, h, seed, moon)
    except Exception:  # noqa: BLE001
        return ""


def scene(theme, w, h, seed=0, moon=.5, **extra):
    """Child markup filling a w x h box edge to edge (the scene engravers', else the old plate)."""
    name, variant = _SCENES.get(theme, _SCENES["river"])
    m = _mod(name)
    if m and hasattr(m, "scene"):
        for kw in (dict(variant=variant, moon_phase=moon, **extra), dict(variant=variant, moon_phase=moon), dict(variant=variant)):
            try:
                return _scope(m.scene(w, h, seed=seed, **kw))
            except TypeError:
                continue
            except Exception:  # noqa: BLE001
                break
    old = _old_plate(theme, int(w), int(h), seed, moon)
    return _scope(_strip_svg(old)) if old else ""


# ---- the frame --------------------------------------------------------------------------------------
FW = BAND - 5.5     # the scroll field inside a band (between the sheet-edge rule and the inside moulding)
FX = 2.0


def _band_edges(w, h):
    """The frame's own lines: a heavy rule on the sheet's edge and the house moulding on the inside."""
    b = BAND

    def ring(i, sw, col):
        return (f'<rect x="{_n(b - i)}" y="{_n(b - i)}" width="{_n(w - 2 * (b - i))}" height="{_n(h - 2 * (b - i))}" '
                f'fill="none" stroke="{col}" stroke-width="{sw}"/>')
    return (f'<rect x=".75" y=".75" width="{_n(w - 1.5)}" height="{_n(h - 1.5)}" fill="none" stroke="#000" stroke-width="1.5"/>'
            + ring(1.75, 1.5, "#fff") + ring(.5, 1, "#000") + ring(2.75, .5, "#000"))


def border(w, h, seed=0):
    """The page frame: four equal bands, a scroll running up the left side and mirrored on the right,
    the bottom band springing from a paw at its centre, a boss in each corner. The middle of the top
    band is left for each page's own title plaque and scrolls (`top_band`)."""
    b = BAND
    side = h - 2 * b
    n = max(4, round(side / FW))
    left = running_scroll(FX, b, FW, side, "v", seed, False, eggs=[(n // 3, "dog"), (2 * n // 3, "heron")])
    art = (f'<g id="S">{left}</g><use xlink:href="#S" href="#S" transform="matrix(-1 0 0 1 {w} 0)"/>'
           + running_scroll(b, h - FX - FW, w - 2 * b, FW, "h", seed + 1, True, centre="paw")
           + corner(FW + 1, FX, FX, "tl", seed) + corner(FW + 1, w - FX - FW - 1, FX, "tr", seed)
           + corner(FW + 1, FX, h - FX - FW - 1, "bl", seed) + corner(FW + 1, w - FX - FW - 1, h - FX - FW - 1, "br", seed))
    return (f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}'
            + ground(0, 0, w, b) + ground(0, h - b, w, b) + ground(0, b, b, side) + ground(w - b, b, b, side)
            + art + _band_edges(w, h) + '</svg>')


TOP_W = PAGE_W - 2 * (BAND - 3)   # the per-page piece of the top band, between the corner bosses


def label_width(label):
    plain = re.sub(r"&\w+;|&#\d+;", "x", label)
    return int(min(TOP_W - 160, round((len(plain) * 9.9 + 44) / 12) * 12))


def top_band(label_w, seed=0):
    """The top band of the frame for one page, between the corners: the title plaque set into it and a
    running scroll either side of the plaque."""
    b, w = BAND, TOP_W
    c = w / 2
    x1 = c - label_w / 2
    run_w = x1 - 3 - 2
    art = (running_scroll(3, FX, run_w, FW, "h", seed, False, eggs=[(1, "p")])
           + running_scroll(c + label_w / 2 + 2, FX, run_w, FW, "h", seed, False, eggs=[(2, "drumsticks")]))
    return (f'<svg {XMLNS} width="{w}" height="{b}" viewBox="0 0 {w} {b}">{DEFS}'
            + ground(0, 0, w, b) + art
            + f'<path d="M0 .75H{w}" stroke="#000" stroke-width="1.5"/>'
            f'<path d="M0 {b - 1.75}H{w}" stroke="#fff" stroke-width="1.5"/>'
            f'<path d="M2.5 {b - .5}H{w - 2.5}" stroke="#000" stroke-width="1"/>'
            f'<path d="M0 {b - 2.75}H{w}" stroke="#000" stroke-width=".5"/>'
            + moulding(x1, 3.5, label_w, b - 8.5, fill="#fff", heavy=1.5) + '</svg>')


# ---- the bottom panel -------------------------------------------------------------------------------
HOLE_IN = 7.0   # the engraver's cartouche frame: the clear opening is inset this far


def _cartouche(w, h):
    """Where the picture sits in a w x h panel: (x, y, cw, ch, shape). Small panels take an oval; tall
    ones a rectangle the scrolls can climb round, set a little below centre so a crest can form above."""
    if h < 120:
        ch = h - 14
        cw = min(w * .42, ch * 3.0)
        return (w - cw) / 2, (h - ch) / 2, cw, ch, "oval"
    if h < 180:
        ch = h - 22
        cw = min(w * .46, ch * 2.4)
        return (w - cw) / 2, (h - ch) / 2, cw, ch, "oval"
    ch = round(h * .60)
    cw = min(w * .56, ch * 2.0)
    return (w - cw) / 2, (h - ch) / 2 + h * .03, cw, ch, "rect"


def _vignette(x, y, w, h, theme, seed, moon, cid, **extra):
    """The scene itself in the house moulding at (x, y, w, h): no surround, nothing between it and its frame."""
    i = MOULD_IN + 1
    sw, sh = w - 2 * i, h - 2 * i
    pic = scene(theme, sw, sh, seed, moon, **extra)
    return (moulding(x, y, w, h, fill="#fff", heavy=1.5)
            + f'<clipPath id="{cid}"><rect width="{_n(sw)}" height="{_n(sh)}"/></clipPath>'
            f'<g transform="translate({_n(x + i)} {_n(y + i)})"><g clip-path="url(#{cid})"><rect width="{_n(sw)}" height="{_n(sh)}" fill="#fff"/>{pic}</g></g>'
            f'<rect x="{_n(x + i)}" y="{_n(y + i)}" width="{_n(sw)}" height="{_n(sh)}" fill="none" stroke="#000" stroke-width="1"/>')


def panel(w, h, theme, seed=0, moon=.5, hole=None, eggs=None, **extra):
    """One composed plate, drawn for exactly w x h. Under 150 px tall it is the scene itself, full width
    in the house moulding (the engravers' frieze compositions). From 150 px up the scene sits in a
    rectangular cartouche at least 60% of the plate's width, with scrollwork (or the white-line forest)
    in the spandrels. `hole` overrides the cartouche (x, y, w, h, shape)."""
    head = f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}'
    if hole is None and h < 150:
        return head + _vignette(0, 0, w, h, theme, seed, moon, "ac", **extra) + '</svg>'
    if hole is None:
        cw = round(w * .62)
        ch = min(h - 2 * MOULD_IN - 12, round(cw * .8))
        hole = ((w - cw) / 2, (h - ch) / 2, cw, ch, "rect")
    x, y, cw, ch, shape = (round(v) if not isinstance(v, str) else v for v in hole)
    return (head + moulding(0, 0, w, h, fill="#fff")
            + _plate_block(MOULD_IN, MOULD_IN, w - 2 * MOULD_IN, h - 2 * MOULD_IN, (x - MOULD_IN, y - MOULD_IN, cw, ch, shape),
                           theme, seed, moon, EGGS.get(theme, ()) if eggs is None else eggs, "ac", **extra) + '</svg>')


def _plate_block(bx, by, bw, bh, hole, theme, seed, moon, eggs, cid, **extra):
    """Scrollwork filling the box (bx, by, bw, bh) round a cartouche `hole` (relative to the box), with
    the theme's scene clipped into the cartouche's opening."""
    hx, hy, cw, ch, shape = hole
    fill = ""
    if theme in FOREST:   # the Thai and night pages: a white-line forest with creatures in it
        fill = _hand("forest_fill", bw, bh, seed, hole=hole, x=bx, y=by, eggs=eggs)
    fill = fill or fill_region(bw, bh, seed, hole=hole, x=bx, y=by, eggs=eggs)
    x, y = bx + hx, by + hy
    sx, sy, sw, sh = x + HOLE_IN, y + HOLE_IN, cw - 2 * HOLE_IN, ch - 2 * HOLE_IN
    pic = scene(theme, sw, sh, seed, moon, **extra)
    if shape == "oval":
        clip = f'<ellipse cx="{_n(sw / 2)}" cy="{_n(sh / 2)}" rx="{_n(sw / 2)}" ry="{_n(sh / 2)}"/>'
        edge = f'<ellipse cx="{_n(x + cw / 2)}" cy="{_n(y + ch / 2)}" rx="{_n(sw / 2)}" ry="{_n(sh / 2)}" fill="none" stroke="#000" stroke-width="1"/>'
        own = oval_moulding(x + cw / 2, y + ch / 2, cw / 2, ch / 2, heavy=1.5)
    else:
        clip = f'<rect width="{_n(sw)}" height="{_n(sh)}"/>'
        edge = f'<rect x="{_n(sx)}" y="{_n(sy)}" width="{_n(sw)}" height="{_n(sh)}" fill="none" stroke="#000" stroke-width="1"/>'
        own = moulding(x, y, cw, ch, heavy=1.5)
    return (f'<clipPath id="{cid}">{clip}</clipPath>' + ground(bx, by, bw, bh) + (fill or own)
            + f'<g transform="translate({_n(sx)} {_n(sy)})"><g clip-path="url(#{cid})"><rect width="{_n(sw)}" height="{_n(sh)}" fill="#fff"/>{pic}</g></g>'
            + edge)


def plate(w, h, theme, seed=0, moon=.5, **extra):
    """A small plate to set beside text: the scene in an oval, the spandrels filled with ornament."""
    return panel(w, h, theme, seed, moon, hole=(7, 7, w - 14, h - 14, "oval"), eggs=(), **extra)


def arms(w, h, seed=0):
    """The family arms (engraved once, by the Morning Edition, in solar/arms.py) as child markup for a
    w x h box, or an empty string until that module lands."""
    m = _mod("arms")
    f = getattr(m, "arms", None) if m else None
    if not f:
        return ""
    try:
        return _scope(_strip_svg(f(w, h, seed=seed)))
    except Exception:  # noqa: BLE001
        return ""


ARMS_W = 164    # the place of honour: the cartouche that holds the arms


def _arms_box(x, y, cw, ch, seed):
    """The arms on the deep ground inside the cartouche whose moulding is already drawn at (x, y, cw, ch)."""
    sx, sy, sw, sh = x + HOLE_IN, y + HOLE_IN, cw - 2 * HOLE_IN, ch - 2 * HOLE_IN
    inner = arms(sw, sh, seed)
    if not inner:
        r = min(sw, sh) / 2 - 2
        inner = (_hand("scroll", sw / 2, sh / 2, r, terminal="p", seed=seed)
                 or f'<circle cx="{_n(sw / 2)}" cy="{_n(sh / 2)}" r="{_n(r)}" fill="none" stroke="#000" stroke-width="1"/>')
    return (f'<clipPath id="ab"><rect width="{_n(sw)}" height="{_n(sh)}"/></clipPath>'
            f'<g transform="translate({_n(sx)} {_n(sy)})"><g clip-path="url(#ab)"><rect width="{_n(sw)}" height="{_n(sh)}" fill="#fff"/>{ground(0, 0, sw, sh, "deep")}{inner}</g></g>'
            f'<rect x="{_n(sx)}" y="{_n(sy)}" width="{_n(sw)}" height="{_n(sh)}" fill="none" stroke="#000" stroke-width="1"/>')


def arms_panel(w, h, seed=0, flank=None, moon=.5):
    """The place of honour on the cover and the last page. `flank` = (left theme, right theme).
    Up to 220 px tall: one row, the arms in the centre cartouche, a rectangular view either side.
    Taller: the arms above in scrollwork (or the forest), the two views side by side beneath, so each
    view stays a landscape large enough to read."""
    m = MOULD_IN
    flank = flank or ("river", "bridge")
    out = [f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}', moulding(0, 0, w, h, fill="#fff"),
           ground(m, m, w - 2 * m, h - 2 * m, "deep")]
    cw = ARMS_W
    x = round((w - cw) / 2)
    if h < 200:
        y, ch = m + 1, h - 2 * m - 2
        bw = x - m - 4
        out.append(_vignette(m + 1, y, bw, ch, flank[0], seed, moon, "al"))
        out.append(_vignette(w - m - 1 - bw, y, bw, ch, flank[1], seed + 1, moon, "ar"))
        out.append(moulding(x, y, cw, ch, heavy=1.5))
        out.append(_arms_box(x, y, cw, ch, seed))
    else:
        ah = 112 if h < 260 else 132 if h < 340 else 156
        hole = (x - m, 3, cw, ah - 6, "rect")
        top = ""
        if flank[0] in FOREST:
            top = _hand("forest_fill", w - 2 * m, ah, seed + 2, hole=hole, x=m, y=m, creatures=("dog", "heron", "paw", "p"))
        out.append(top or fill_region(w - 2 * m, ah, seed + 2, hole=hole, x=m, y=m, eggs=("dog", "heron"))
                   or moulding(x, m + 3, cw, ah - 6, heavy=1.5))
        out.append(_arms_box(x, m + 3, cw, ah - 6, seed))
        y0 = m + ah + 2
        bh = h - m - 1 - y0
        bw = (w - 2 * m - 2 - 4) / 2
        out.append(_vignette(m + 1, y0, bw, bh, flank[0], seed, moon, "al"))
        out.append(_vignette(w - m - 1 - bw, y0, bw, bh, flank[1], seed + 1, moon, "ar"))
    return "".join(out) + '</svg>'


def frieze(w, h=FRIEZE_H, seed=0, centre="flower"):
    """A symmetric frieze for a sliver of room: it springs from a motif at its centre."""
    m = MOULD_IN
    art = running_scroll(m, m, w - 2 * m, h - 2 * m, "h", seed, True, centre=centre)
    return (f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}' + moulding(0, 0, w, h, fill="#fff")
            + ground(m, m, w - 2 * m, h - 2 * m) + art + '</svg>')


def bead(w, h=BEAD_H):
    """The narrowest band: a row of pearls between two mouldings, a lozenge at the centre."""
    m = MOULD_IN
    cy = h / 2
    r = (h - 2 * m) / 2 - .5
    n = int((w - 2 * m - 2) // (2 * r + 2)) | 1
    step = (w - 2 * m - 2) / n
    x0 = m + 1 + step / 2
    return (f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}">{DEFS}' + moulding(0, 0, w, h, fill="#000")
            + f'<circle id="p" cx="{_n(x0)}" cy="{_n(cy)}" r="{_n(r)}" fill="#fff" stroke="#000" stroke-width=".5"/>'
            + "".join(f'<use xlink:href="#p" href="#p" x="{_n(step * i)}"/>' for i in range(1, n))
            + "".join(f'<circle cx="{_n(x0 + step * i)}" cy="{_n(cy)}" r=".75"/>' for i in range(n)) + '</svg>')


def initial(size=66, seed=0):
    """The ground of a drop initial: the house moulding and a knot of scrollwork. The letter itself is
    set by the page, in the text face, over it."""
    m = MOULD_IN
    s = size - 2 * m
    art = fill_region(s, s, seed, hole=None, x=m, y=m, rmax=s * .34)
    return (f'<svg {XMLNS} width="{size}" height="{size}" viewBox="0 0 {size} {size}">{DEFS}' + moulding(0, 0, size, size, fill="#fff")
            + ground(m, m, s, s) + art + '</svg>')


# ---- the page's ground ---------------------------------------------------------------------------
def page_field(w=PAGE_W, h=714, seed=0):
    """The page's ground: one whole engraving of leaves, fronds and blossom the size of the screen.
    Plaques and plates are laid over it, so whatever room a page leaves shows drawing, never a tint."""
    m = _mod("engraving_hand")
    art = m.forest_fill(w, h, seed=seed, creatures=("bird", "paw", "p")) if m else ""
    return f'<svg {XMLNS} width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}"/>{art}</svg>'


# ---- files and CSS ----------------------------------------------------------------------------------
RINGS = "0 0 0 2.5px #fff,0 0 0 3px #000,0 0 0 4.5px #fff,0 0 0 6px #000"
ART = "art"


def write(out_dir, name, svg):
    """Write one drawing to the edition's art folder; returns its URL relative to the pages and the CSS."""
    import os
    d = os.path.join(out_dir, ART)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w") as f:
        f.write(svg)
    return f"{ART}/{name}"


CSS_ART_BUDGET = 0   # every drawing is a file under art/ (the build rasterises them); nothing is inlined into kindle.css


def page_css(out_dir, seed=0, inner_h=618, cover_h=646):
    """Draw the shared art (field, frames, friezes, bead, initial) and return the CSS that places it.
    Page-independent pieces go into kindle.css as data URIs while they fit CSS_ART_BUDGET (so they cost
    no page bytes and no extra requests); anything beyond that is written to the art folder."""
    spent = [0]

    def u(name, svg):
        d = data_uri(svg)
        if spent[0] + len(d) <= CSS_ART_BUDGET:
            spent[0] += len(d)
            return d
        return f"url({write(out_dir, name, svg)})"
    fh = max(inner_h + 44, cover_h) + 52
    pieces = {
        "field": ("field.svg", page_field(PAGE_W, fh, seed)),
        "field1": ("field-1.svg", page_field(PAGE_W, fh, seed + 101)), "field2": ("field-2.svg", page_field(PAGE_W, fh, seed + 202)),
        "frame": ("frame.svg", border(PAGE_W, inner_h, seed)), "cover": ("frame-cover.svg", border(PAGE_W, cover_h, seed)),
    }
    url = {k: u(*v) for k, v in sorted(pieces.items(), key=lambda kv: len(kv[1][1]))}
    return (
        f"html:root.kev{{background:#000 {url['field']} 0 0/{PAGE_W}px {fh}px no-repeat !important}}\n"
        f"html:root.kev.kf1{{background-image:{url['field1']} !important}}html:root.kev.kf2{{background-image:{url['field2']} !important}}\n"
        f"html.kev body:not(.kcontents){{background:{url['frame']} 0 44px/{PAGE_W}px {inner_h}px no-repeat !important}}\n"
        f"html.kev body.kcontents{{background:{url['cover']} 0 0/{PAGE_W}px {cover_h}px no-repeat !important}}\n"
    )
