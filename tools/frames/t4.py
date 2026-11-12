import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for name, w, h, e, t, kind, lit in (("chip", 110, 26, 24, 3, "point", False), ("chipL", 110, 26, 24, 3, "point", True),
                                     ("button", 170, 40, 34, 4, "roll", False), ("run", 200, 30, 30, 3, "scroll", False),
                                     ("gauge", 90, 34, 26, 3, "round", False), ("tail", 200, 40, 34, 3, "tail", False)):
    cv = scroll.Canvas(w, h)
    scroll.plaque(cv, 0, 0, w, h, (e, e), t, seed=len(name), kind=kind, lit=lit)
    s = cv.svg(); open(f'{out}/{name}.svg', 'w').write(s); print(name, len(s))
