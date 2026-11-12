"""Table head row (PEAK / TODAY / TOMORROW ...): a band of fine scroll along the head, closed below by a
bright double inlay line, the ends rolled into small volute terminals.  Open at the sides."""
from ._common import scroll, ctx_of, seed_of, band, canvas

DEFAULT = (7, 0, 3, 0)


def insets(w, h, ctx=None):
    return band(ctx_of(ctx), DEFAULT)


def frame(w, h, ctx=None):
    ctx = ctx_of(ctx)
    t, r, b, l = insets(w, h, ctx)
    cv = canvas(w, h)
    rng = scroll.rng_for("thead", seed_of("tablehead", w, h, ctx))
    e = max(t + 2, 9)  # end terminal width
    cv.slot = (0, t, w, h - t - b)
    cv.clip = scroll._rect_d(0, 0, w, h)
    cv.over("W", scroll._rect_d(0, t, w, h - b))
    # head band: black ground, scroll lane between a 0.5 rule and a bright inlay
    cv.add("K", "M%s 0H%sV%sH%sZ" % (e, w - e, t, e))
    run = scroll.Run([(e, (t - 1.5) / 2 + 0.5), (w - e, (t - 1.5) / 2 + 0.5)], t - 2.5)
    scroll._compose_side(cv, run, ("thead", ctx.get("seed", 0)), "shell" if w > 200 else None, 0, motif_min=6)
    cv.over("R05", "M%s .25H%s" % (e, w - e))
    cv.over("S1", "M%s %sH%s" % (e, t - 1.5, w - e))
    cv.over("R1", "M%s %sH%s" % (e - 2, t - 0.5, w - e + 2))
    # foot: double inlay (1 px rule, bright channel, 0.5 rule)
    cv.over("R1", "M%s %sH%s" % (e - 2, h - b + 0.5, w - e + 2))
    cv.over("R05", "M%s %sH%s" % (e, h - 0.25, w - e))
    # terminals: a volute at each end, turning down toward the row
    for left in (True, False):
        X = e * 0.5 if left else w - e * 0.5
        cv.circle("K", X, t / 2 + 1, e * 0.48)
        scroll.volute(cv, X, t / 2 + 1, e * 0.42, 1 if left else -1, 0.0 if left else 3.14159, rng, wmax=1.0)
    return cv.svg()
