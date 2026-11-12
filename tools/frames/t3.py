import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for b in (9, 12, 16):
    cv = scroll.Canvas(300, 90)
    scroll.band_rect(cv, 0, 0, 300, 90, (b,) * 4, seed=b, centre=('fleuron', None, 'shell', None))
    open(f'{out}/kp{b:02d}.svg', 'w').write(cv.svg())
