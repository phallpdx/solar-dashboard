"""Panel edge (.kpanel): a bright double inlay line on a narrow black band, like the gold lines that bound
the scroll fields on the references, with a small volute turning each corner.  The ornate border of a panel
is the scroll field around it (solar.scroll.field); this is only its edge.  A side cut by the sheet edge
(open_top / open_bottom) is left off, and its corners with it."""
import math
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (4, 4, 4, 4)
CORNER = 9.0  # the corner block: b px of band plus 5 px into the panel's own corner


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    """The whole box w x h with the inlay band inside it; the slot (w - 2b) x (h - 2b) is transparent."""
    ctx = ctx_of(ctx)
    b = insets(w, h, ctx)[0]
    cv = canvas(w, h)
    rng = scroll.rng_for("kpanel", seed_of("kpanel", w, h, ctx))
    f = scroll._f
    ot, ob = bool(ctx.get("open_top")), bool(ctx.get("open_bottom"))
    cv.slot = (b, b, w - 2 * b, h - 2 * b)
    # the black band: outer rect clockwise, inner counter-clockwise
    cv.add("K", scroll._rect_d(0, 0, w, h) + "M%s %sV%sH%sV%sZ" % (f(b), f(b), f(h - b), f(w - b), f(b)))
    # two bright lines: a 1 px inlay and a 0.5 px one inside it, black between and on both sides
    cv.add("S1", scroll._rect_d(1.25, 1.25, w - 1.25, h - 1.25))
    cv.add("S05", scroll._rect_d(b - 1.0, b - 1.0, w - b + 1.0, h - b + 1.0))
    s = CORNER if b <= 5 else b + 5
    for cx, cy, top in ((0, 0, True), (w, 0, True), (0, h, False), (w, h, False)):
        if (top and ot) or (not top and ob):
            continue
        sx = 1 if cx == 0 else -1
        sy = 1 if cy == 0 else -1
        x0, x1 = sorted((cx, cx + sx * s))
        y0, y1 = sorted((cy, cy + sy * s))
        cv.add("K", scroll._rect_d(x0, y0, x1, y1))
        cv.add("S05", scroll._rect_d(x0 + 0.75, y0 + 0.75, x1 - 0.75, y1 - 0.75))
        R = s * 0.36
        mx, my = cx + sx * s / 2, cy + sy * s / 2
        sc = scroll.Scroll(mx, my, R, sx * sy, math.atan2(-sy, -sx), 1.35, 0.2)
        scroll.draw_scroll(cv, sc, rng, bw=1.2, inner=False)
    if ot or ob:
        cv.clip = scroll._rect_d(0, b if ot else 0, w, h - b if ob else h)
    return cv.svg()


def panel_edge(w, h, open_top=False, open_bottom=False, seed=0, b=None):
    """frame-detail's call: the inlay edge for a white panel w x h, drawn outside it, SVG (w + 2b) x (h + 2b).
    Leave the field's hole as the panel plus b on every side."""
    b = b or DEFAULT[0]
    return frame(w + 2 * b, h + 2 * b, {"seed": seed, "band": b, "open_top": open_top, "open_bottom": open_bottom})
