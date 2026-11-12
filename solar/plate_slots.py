"""Bespoke plate slots, from the edition plan (/mnt/project-files/kindle/redesign/edition-plan.md, 1.6 and
Part 2): each page's engraving has a planned form, size, shape and place, never "all the room that is left".

A page's art is found by the cards it carries (its heading ids, so the plan survives pages being
reordered or merged) or, for a section front, by its section. Each slot, as `for_page` returns it:

    form   "headpiece", "vignette", "plate" (full-width), "tailpiece", "device" (marginal roundel),
           "front" (a section front's vignette) or "none" (gap frieze only: no plate at all)
    pos    "head"         at the top of the page body, above the title
           "after:.cls" / "after:#id" / "before:..."   in the flow, next to that element
           "tail"         in the room after the last panel of its sheet, top-aligned under it
           "margin"       a roundel on the frame's side band, beside the largest panel gap
    sheet  for tail: a sheet index, or -1 for the last sheet (the plan: the last sheet carries the plate)
    w, h   size in CSS px, from the form's share of the sheet (never enlarged to fill)
    shape  "rect", "oval", "circle" (roundel), "arch" (arched top), "banner" (ribbon), "lunette",
           "irregular", "cut"
    subject, egg   passed to the engraver as ctx["subject"] and ctx["egg"]
    arms   True on section fronts: the Somaster dedication cartouche, about 30 px, at the vignette's foot

Room the art does not use goes, in order, to wider panel gaps, one carved frieze in the largest gap,
and the engraved frame ground below the plate.
"""

COLUMN = 526
SHEET = 600          # the text area of a sheet, the base for a form's share

# section front vignettes: shape and subject (plan Part 2, "Front vignette")
FRONTS = {
    "today": ("oval", "the island's morning sky over the barn and weather vane, with today's actual sky"),
    "roads": ("circle", "the commute: the St. Johns Bridge and US-30 with the Sauvie Island bridge"),
    "family": ("irregular", "a blanket fort under a pine"),
    "solar": ("circle", "the panel array with a radiant sun, the house behind"),
    "garden": ("irregular", "a food-forest hedge with hazel catkins"),
    "river": ("lunette", "the Columbia with a ship at anchor off the island"),
    "nearby": ("circle", "the night sky over the barn with the moon in today's phase"),
    "news": ("arch", "a press room, or the Oregonian clock tower"),
    "markets": ("arch", "a ticker tape over the Willamette"),
    "civics": ("arch", "the Oregon Capitol's gilded pioneer"),
    "sports": ("circle", "whoever plays today: a hoop and basketball"),
    "music": ("irregular", "a jazz trio with drums, bass and horn"),
    "local": ("arch", "the St. Johns Bridge with storefronts"),
    "watch": ("oval", "a cinema proscenium"),
    "almanac": ("circle", "an armillary sphere and an hourglass"),
    "science": ("arch", "a telescope and a microscope"),
    "delights": ("irregular", "a cabinet of curiosities"),
    "world": ("arch", "Wat Arun in Lanna repousse style"),
    "coast": ("lunette", "Haystack Rock or Tillamook Head"),
}

# per page, keyed by the card heading ids the plan names (any one matches)
CARDS = [
    (("today-card",), dict(form="headpiece", share=.10, shape="irregular", pos="head",
                           subject="clouds or sun as today's sky actually is, with the vane on the barn", egg="the weather vane is a heron")),
    (("brief-h",), dict(form="tailpiece", share=.08, shape="oval", subject="a butler's salver holding coffee", egg="a dog biscuit on the salver")),
    (("wx-h", "yard-h"), dict(form="device", shape="circle", subject="an anemometer cup", egg="a raindrop shaped as a jazz eighth note")),
    (("cal-h",), dict(form="tailpiece", share=.08, shape="arch", subject="a desk calendar leaf", egg="a crossed-drumsticks bookmark")),
    (("plan-h",), dict(form="vignette", share=.20, shape="oval", subject="an admit-one ticket and a ZooLights lantern", egg='a ticket stub numbered "315"')),
    (("fc-h",), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="a week of weather glyphs carved into a ribbon", egg="the dog under an umbrella on the wettest day")),
    (("drive-h",), dict(form="device", shape="circle", subject="a milestone post", egg='"SAUVIE 0 MI" carved on the post')),
    (("ski-h", "mtn-h"), dict(form="vignette", share=.25, shape="arch",
                              subject="Mt. Hood above Timberline Lodge, the snow level at today's freezing height", egg="a snow-stake marked in drumstick segments")),
    (("fire-h", "quake-h"), dict(form="tailpiece", share=.08, shape="banner", subject="a fire lookout on a ridge, a seismograph line as the ridge", egg="the seismograph trace is a bar of swing rhythm")),
    (("play-h", "bug-h"), dict(form="tailpiece", share=.08, shape="oval", subject="a pinecone bird feeder", egg="a toddler-size drum")),
    (("out-h",), dict(form="vignette", share=.22, shape="arch", subject="the Christmas Ships, or the nearest dated event", egg="a tiny Blazers pinwheel on a ship's mast")),
    (("t-now", "loads-h"), dict(form="vignette", share=.22, shape="oval", subject="the sun at today's elevation over the array, an EV and a washer in the yard", egg="a ride cymbal as the sun's disc")),
    (("bill-h", "wins-h"), dict(form="tailpiece", share=.08, shape="banner", subject="a ledger and a coin stack", egg="the coin is stamped with the Somaster castle")),
    (("grid-h",), dict(form="vignette", share=.20, shape="arch", subject="Bonneville Dam with transmission towers", egg="a heron on the spillway")),
    (("mo-h",), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="30 tally-marks carved as fence posts", egg="a dog paw print in the dirt")),
    (("look-h",), dict(form="vignette", share=.18, shape="oval", subject="the prairie edge with a brush pile, smoking only when burning is OK", egg="a kestrel on a fence post")),
    (("birds-h",), dict(form="vignette", share=.25, shape="oval", subject="the rarest confirmed bird today at its named place", egg="the heron watching from the reeds")),
    (("mush-h",), dict(form="vignette", share=.25, shape="arch", subject="today's pick under Douglas fir", egg="a tiny drum-shaped stump")),
    (("columbia-h", "moor-h"), dict(form="headpiece", share=.10, shape="banner", pos="head", subject="river waves, a bulk carrier when one is moored", egg="the St. Johns Bridge in the distance")),
    (("fish-h",), dict(form="tailpiece", share=.08, shape="oval", subject="a leaping coho", egg="a fishing float painted like a Blazers pinwheel")),
    (("sunset-h",), dict(form="none", egg="in the frieze, Mt. Hood at sunset")),
    (("moon-h",), dict(form="plate", share=.35, shape="circle", subject="today's moon phase over the Columbia", egg="the dog howling on the bank")),
    (("sky-h",), dict(form="tailpiece", share=.08, shape="irregular", subject="a Leonid streak, or the nearest sky event", egg="a constellation that traces a P")),
    (("localnews-h",), dict(form="tailpiece", share=.08, shape="banner", subject="the Portland skyline from the river", egg="the St. Johns Bridge")),
    (("bignews-h",), dict(form="device", shape="circle", subject="a globe", egg="a kranok flame on the globe's stand")),
    (("stories-h", "reviews-h"), dict(form="vignette", share=.20, shape="oval", subject="a turntable and speaker", egg="a drum kit reflected in the speaker cone")),
    (("mkt-h",), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="a bull and bear face-off", egg="the bull wears a Blazers pinwheel")),
    (("he-h",), dict(form="tailpiece", share=.08, shape="circle", subject="a helium balloon over the Saskatchewan plant", egg="the balloon is tied with a drumstick")),
    (("re-h",), dict(form="vignette", share=.18, shape="arch", subject="an island farmhouse", egg="the dog on the porch")),
    (("reps-h",), dict(form="device", shape="circle", subject="the Capitol dome", egg="the P monogram on the flag")),
    (("elect-h",), dict(form="vignette", share=.22, shape="oval", subject="an Oregon ballot drop box", egg="a heron as a weathervane on the box")),
    (("rec-h", "drum-h", "bday-h"), dict(form="plate", share=.40, shape="circle", sheet=0,
                                         subject="the record's actual era: a turntable with the album cover", egg="crossed sticks under the tonearm")),
    (("alb-h",), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="a row of record spines", egg='a spine reading "SOMASTER"')),
    (("jazz-h",), dict(form="vignette", share=.20, shape="arch", subject="the Jack London Revue stage", egg="the ride cymbal engraved with a P")),
    (("gig-h", "show-h"), dict(form="tailpiece", share=.08, shape="banner", subject="a ticket ribbon", egg='the dog\'s head as the "O" in a marquee')),
    (("finds-h",), dict(form="vignette", share=.20, shape="oval", subject="the lead find", egg="a Thai chili among the walnuts")),
    (("open-h",), dict(form="none")),
    (("big-h",), dict(form="tailpiece", share=.08, shape="banner", subject="the Moda Center or the convention center", egg="a Blazers pinwheel banner")),
    (("liq-h",), dict(form="vignette", share=.20, shape="arch", subject="a bottle shelf", egg="a bottle labelled with the Somaster castle")),
    (("br-h",), dict(form="device", shape="circle", subject="a disc", egg='the Criterion "C" turned into a P')),
    (("tv-h",), dict(form="tailpiece", share=.08, shape="oval", subject="a TV set", egg="a heron on the screen")),
    (("kidmov-h", "clsmov-h"), dict(form="vignette", share=.22, shape="arch", subject="a scene from the classic film", egg="a crow shaped as a drumstick")),
    (("hist-h",), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="a calendar dial", egg="11/11 written as drumsticks")),
    (("hol-h",), dict(form="vignette", share=.25, shape="oval", subject="the next holiday", egg="an elephant on the bank")),
    (("near-h", "oldpdx-h"), dict(form="none")),
    (("sci-h", "science-h"), dict(form="tailpiece", share=.08, shape="irregular", sheet=-1, subject="the lead story's subject", egg="a gravitational wave drawn as a swing-rhythm bar")),
    (("potd-h", "art-h"), dict(form="none")),
    (("poem-h",), dict(form="plate", share=.35, shape="arch", subject="the poem's own image", egg="the dog")),
    (("good-h",), dict(form="tailpiece", share=.08, shape="oval", subject="a sunrise", egg="the dog")),
    (("read-h",), dict(form="vignette", share=.22, shape="arch", subject="a reading chair by lamplight", egg="a Thai lotus lamp")),
    (("books-h", "shelf-h"), dict(form="headpiece", share=.08, shape="banner", pos="head", subject="a book spine row", egg="a spine reading SOMASTER")),
    (("bkk-h", "thai-h"), dict(form="vignette", share=.22, shape="oval", subject="today's phrase made visual on a Lanna silver tray", egg="a kinnari playing a drum, hidden in the foliage")),
    (("coast-summary", "minus-h"), dict(form="headpiece", share=.10, shape="banner", pos="head", subject="a banner of breakers", egg="the Somaster castle as a sandcastle")),
    (("surf-h",), dict(form="vignette", share=.20, shape="oval", subject="Seaside Cove cobble point with a surfer", egg="a surfboard with a pinwheel")),
    (("shell-h", "cev-h"), dict(form="tailpiece", share=.08, shape="oval", subject="a razor clam and a Dungeness crab", egg="the crab holding drumsticks")),
    (("whale-h",), dict(form="plate", share=.40, shape="arch", subject="a gray whale spouting off Cape Lookout", egg="the dog on the headland")),
]

# pages the plan names by subject rather than by card id: slug, or slug prefix
SLUGS = [
    ("sports-01", dict(form="vignette", share=.25, shape="arch", subject="today's matchup: the Blazers pinwheel against the visitors at the Moda Center",
                       egg="a drummer in the crowd")),
    ("sports-", dict(form="tailpiece", share=.08, shape="banner", subject="a scarf ribbon in Timbers and Vikings stripes", egg="a chequered flag")),
    ("science-", dict(form="tailpiece", share=.08, shape="irregular", subject="the lead story's subject", egg="a gravitational wave drawn as a swing-rhythm bar")),
]


def _size(form, share, shape):
    if form == "headpiece":
        return COLUMN, int(max(90, min(100, share * SHEET * 1.2)))   # a band under 90 px cannot hold a scene
    if form == "tailpiece":
        h = int(max(40, min(70, share * SHEET)))
        return (h if shape == "circle" else int(COLUMN * .5)), h
    if form == "device":
        return 38, 38
    h = int(share * SHEET)
    if form == "plate":
        return (min(COLUMN, h) if shape == "circle" else COLUMN), h
    w = {"oval": 1.6, "circle": 1., "arch": 1.3, "banner": 2.6, "lunette": 2.2, "irregular": 1.5}.get(shape, 1.6) * h
    return int(min(COLUMN, w)), h


def for_page(slug, html=""):
    """The slots for one page: its section front's vignette, or the plan's entry for the cards it carries."""
    if slug in FRONTS:
        shape, subject = FRONTS[slug]
        import re
        m = re.search(r'class="kfhead[^"]*" data-n="(\d+)"|data-n="(\d+)"', html)
        n = int(next(g for g in m.groups() if g)) if m else 6
        # a front is one sheet: the vignette takes what the teaser list leaves (as the stock head plate did)
        h = 150 if n <= 3 else 118 if n <= 5 else 100 if n <= 7 else 84
        w = int(min(COLUMN, {"oval": 1.6, "circle": 1., "arch": 1.3, "lunette": 2.2, "irregular": 1.5}.get(shape, 1.6) * h))
        return [dict(form="front", pos="after:.kfhead", w=w, h=h, shape=shape, subject=subject, egg="", arms=True)]
    hit = next((spec for ids, spec in CARDS if any(f'id="{i}"' in html for i in ids)), None) \
        or next((spec for key, spec in SLUGS if slug == key or (key.endswith("-") and slug.startswith(key))), None)
    for spec in [hit] if hit else []:
        if True:
            d = dict(spec)
            if d["form"] == "none":
                return [d]
            d.setdefault("pos", "margin" if d["form"] == "device" else "tail")
            d.setdefault("sheet", -1)
            d.setdefault("shape", "rect")
            d.setdefault("subject", "")
            d.setdefault("egg", "")
            d["w"], d["h"] = _size(d["form"], d.get("share", .2), d["shape"])
            return [d]
    return []
