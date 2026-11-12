"""Status chip (HIDDEN, OUT NOW, CLOSED ...): a tabula ansata.  The scroll lives in pointed ogee ears, each
holding a volute rolling toward the word with a smaller scroll winding against it and acanthus in the pockets;
the head and foot are a fine double inlay only (3 px).  'lit' (status ON): a pearl boss in each ear tip and a
second fine rule round the slot."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (3, 18, 3, 18)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (l, r), t, seed_of("chip", w, h, ctx), kind="point",
                  lit=ctx.get("variant") == "lit")
    return cv.svg()
