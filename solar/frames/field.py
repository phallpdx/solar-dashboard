"""Sheet ground: the vise-scale scroll field laid around the panel windows of one sheet.

    from solar.frames import field
    svg = field.field(618, 714, holes=[(x, y, w, h), ...], seed=page_seed, motif="fleuron")

holes are the rectangles to leave transparent: each panel's box plus its inlay edge (kpanel.panel_edge's
b = 4 on every side).  motif is "fleuron" | "shell" | "rosette" or a callable(cv, x, y, size) for the
section's own motif, or a section name ("river", "today", ...) to use SECTION_MOTIFS[section]; it is set at
the centre of the longest run, smaller shells and rosettes at the others.

SECTION_MOTIFS (defined in solar/scroll.py, re-exported here) maps each section to its own engraved emblem:
a module-level callable(cv, x, y, size), (x, y) the centre, size about 62 px (76 in the largest areas).
border=False leaves off the double inlay line round the sheet edge.  One SVG per sheet; rasterise once."""
from ._common import scroll

SECTION_MOTIFS = scroll.SECTION_MOTIFS


def field(w, h, holes=(), seed=0, motif="fleuron", border=True):
    return scroll.field(w, h, holes, seed=seed, motif=motif, border=border)
