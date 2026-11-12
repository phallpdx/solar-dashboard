import sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solar'))
import scroll
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
cases = {
 'kpanel': (539, 130, (9, 9, 9, 9), None, ('fleuron', None, 'shell', None)),
 'tile': (230, 64, (8, 8, 8, 8), None, ('rosette', None, None, None)),
 'chip': (100, 26, (5, 11, 5, 11), 'scroll', (None,) * 4),
 'button': (150, 38, (7, 16, 7, 16), 'roll', ('shell', None, None, None)),
 'runhead': (130, 28, (5, 14, 5, 14), 'point', (None,) * 4),
 'banner': (460, 40, (9, 26, 9, 26), 'scroll', ('fleuron', None, 'shell', None)),
}
for k, (w, h, ins, ends, centre) in cases.items():
    t = time.time(); cv = scroll.Canvas(w, h)
    scroll.band_rect(cv, 0, 0, w, h, ins, seed=k, centre=centre, ends=ends)
    s = cv.svg(); open(f'{out}/{k}.svg', 'w').write(s)
    print(k, len(s) // 1024, 'KB', round(time.time() - t, 2))
cv = scroll.Canvas(539, 570); scroll.band_rect(cv, 0, 0, 539, 570, (9,) * 4, seed='big', centre=('fleuron', 'rosette', 'shell', 'rosette'))
s = cv.svg(); open(f'{out}/kpanel_big.svg', 'w').write(s); print('big', len(s) // 1024)
