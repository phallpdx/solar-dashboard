"""Engraved frames for the Morning Edition, drawn by the engraving studio (branch claude/engrave-frames).

One module per family. Each exposes
    frame(w, h, ctx=None) -> str     a complete <svg> exactly w x h CSS px, slot white, outside transparent
    insets(w, h, ctx=None) -> (t, r, b, l)   the band widths (pad text by these + 2 px)
kpanel also exposes panel_edge(w, h, open_top, open_bottom, seed).

Every frame is composed fresh by solar/scroll.py for its exact size and seed (ctx["seed"]): no tiles, no
nine-slice, no stretching.  ctx keys: seed (any hashable), variant ("plain" | "lit"), band (override the
band widths, a number or a (t, r, b, l) tuple).
"""
FAMILIES = ("chip", "button", "sections", "runhead", "banner", "tile", "tablehead", "barbase", "gauge",
            "divider", "initial", "kpanel", "field")
