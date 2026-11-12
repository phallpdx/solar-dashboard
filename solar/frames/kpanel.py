"""Edges of the white .kpanel text panels: a band of fine scroll drawn OUTSIDE the panel's white, a fleuron
rising from the middle of the head, a shell hanging at the foot, volutes turning the corners.  A side cut
by the sheet edge gets no band; its corners end in small scrolled terminals instead."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (18, 18, 18, 18)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    """The whole box w x h, band inside it (slot = w - l - r by h - t - b)."""
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    open_sides = tuple(s for s in ("top", "bottom") if ctx.get("open_" + s))
    # the biggest panels: coarser path fit and fewer pocket leaflets until the file is inside 200 KB
    tol, gmin = (0.2, 2.4) if w + h > 900 else (None, None)
    for _ in range(4):
        cv = canvas(w, h)
        if tol:
            cv.tol, cv.gap_min = tol, gmin
        scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("kpanel", w, h, ctx),
                         centre=("fleuron", "rosette" if h > 200 else None, "shell", "rosette" if h > 200 else None),
                         open_sides=open_sides)
        svg = cv.svg()
        if len(svg) <= 196 * 1024:
            break
        tol, gmin = (tol or 0.1) + 0.06, (gmin or 1.4) + 0.8
    return svg


def panel_edge(w, h, open_top=False, open_bottom=False, seed=0, b=None):
    """frame-detail's call: the band for a white panel w x h, drawn outside it, SVG (w + 2b) x (h + 2b)."""
    b = b or DEFAULT[0]
    return frame(w + 2 * b, h + 2 * b, {"seed": seed, "band": b, "open_top": open_top, "open_bottom": open_bottom})
# (the very tallest panels open the stipple slightly to stay inside the 200 KB file budget)
