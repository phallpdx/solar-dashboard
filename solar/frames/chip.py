"""Status chip (HIDDEN, OUT NOW, CLOSED ...): a tabula ansata.  Dovetail ears, each holding a volute that
rolls toward the word; a running fine scroll above and below.  'lit' (status ON): the ears are cut solid
and carry a pearl boss, and a second bright inlay runs round the slot, so the chip reads heavier."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (6, 11, 6, 11)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("chip", w, h, ctx), centre=(None,) * 4, ends="point",
                     lit=ctx.get("variant") == "lit")
    return cv.svg()
