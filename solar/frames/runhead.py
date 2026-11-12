"""Running-head label (TODAY, ROADS AND MOUNTAINS, SHEET 1 OF 3): a label cartouche whose ends are twin
acanthus volutes meeting in a bud, fine scroll running along the head and foot."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (5, 14, 5, 14)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("runhead", w, h, ctx), centre=(None,) * 4, ends="scroll")
    return cv.svg()
