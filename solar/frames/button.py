"""Buttons (Prev / Next, More, Skip ...): a plaque with rolled scroll ears (a big volute, a smaller counter
scroll and acanthus in each); head and foot a fine double inlay.  ctx "point": "left" (Prev) or "right"
(Next) turns that ear into a pointed ogee so the button points the way it goes."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (4, 22, 4, 22)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    pt = ctx.get("point")
    kind = ("point" if pt == "left" else "roll", "point" if pt == "right" else "roll")
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("button", w, h, ctx), kind=kind)
    return cv.svg()
