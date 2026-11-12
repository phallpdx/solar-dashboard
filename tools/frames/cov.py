import sys, os, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
S = sys.argv[1]; os.makedirs(S, exist_ok=True)
for H in (16, 9):
    for dens, nm in ((0.0001, 'only'), (None, 'ground')):
        cv = scroll.Canvas(300, H)
        kw = {} if dens is None else {'density': dens}
        scroll.strip(cv, scroll.Run([(0, H / 2), (300, H / 2)], H), seed=3, **kw)
        open(f'{S}/s{H}{nm}.svg', 'w').write(cv.svg())
