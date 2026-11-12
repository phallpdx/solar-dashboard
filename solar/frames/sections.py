"""The SECTIONS menu button: compact sibling of the button, a scrolled plaque whose foot carries a small
downward fleuron (the menu opens downward)."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (5, 12, 6, 12)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    ins = insets(w, h, ctx)
    cv = canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed_of("sections", w, h, ctx), centre=(None, None, "fleuron", None),
                     ends="roll", raised=True, motif_min=2.2)
    return cv.svg()
