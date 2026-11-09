"""9 Nov 2026 fix pass over the 8 Nov layers (run after layers.py, before export.py).
1. Garden Room alone: rebuild the pod's lower right end where pool reeds hid it (vertical cladding continued from clean rows
   above, ambient darkening, rounded bottom-right corner, contact shadow on the BEFORE lawn) -- replaces the smeared patch.
2. Garden Retreat alone: rebuild the gravel pad where the pool's reeds stood (gravel texture copied in 8x8 blocks from clean
   gravel of the same pad), give the pad a defined front edge onto the BEFORE lawn; no reed fragments.
ALL is unchanged where the pool layer is on top (it carries the reeds)."""
import numpy as np, cv2, json
B = cv2.imread('in/hero-before-master.png').astype(np.float32)
A = cv2.imread('out/possible-aligned.png').astype(np.float32)
H, W = B.shape[:2]
M = dict(np.load('out/mattes.npz'))
SRCPOD = np.load('out/src-garden-room.npy').astype(np.float32)
REED = np.load('out/pod-reedmask.npy')
hsv = cv2.cvtColor(A.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.int32)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
yy, xx = np.mgrid[0:H, 0:W]
rng = np.random.default_rng(7)

# ---------------- 1. pod lower right end ----------------
X0, X1, YB = 1196, 1332, 489           # cladding columns, pod bottom row (measured on clean columns 1244-1340)
ell_cx, ell_cy, rx, ry = X1 - 28, YB - 22, 28.0, 22.0
def inside_pod(x, y):
    if y > YB or x > X1 - 1: return False
    if x > ell_cx and y > ell_cy:
        return ((x - ell_cx) / rx) ** 2 + ((y - ell_cy) / ry) ** 2 <= 1.0
    return True
P = SRCPOD.copy(); gm = M['garden_room'].copy()
for x in range(X0, X1 + 4):
    col = REED[:, x] if x < W else None
    occ = np.where(REED[430:500, x])[0]
    if len(occ) == 0: continue
    top = min(438, 430 + occ.min())
    ref = A[404:434, x]                                 # one clean band of ribs above every reed tip           # clean cladding rows just above the occlusion (vertical ribs)
    if len(ref) < 6: continue
    n = len(ref)
    for y in range(top - 1, 506):
        if inside_pod(x, y):
            k = (y - top) % (2 * n); k = k if k < n else 2 * n - 1 - k   # mirror tiling keeps ribs continuous
            c = ref[n - 1 - k].copy()
            dark = 1.0 - 0.22 * np.clip((y - (YB - 14)) / 14.0, 0, 1)       # ambient darkening toward the plinth
            if x > ell_cx and y > ell_cy:                                    # the end turns away from the light
                dark *= 1.0 - 0.18 * np.clip(((x - ell_cx) / rx) ** 2 + ((y - ell_cy) / ry) ** 2, 0, 1)
            P[y, x] = c * dark
            gm[y, x] = 1.0
        else:
            P[y, x] = 0
            gm[y, x] = 0.0
# soften the silhouette edge of the rebuilt corner by 1px
edge = np.zeros((H, W), np.float32); edge[440:506, X0:X1 + 4] = gm[440:506, X0:X1 + 4]
edge = cv2.GaussianBlur(edge, (0, 0), 0.7)
gm[440:506, ell_cx.__int__():X1 + 4] = edge[440:506, int(ell_cx):X1 + 4]
# contact shadow on the lawn under the cladding (black, alpha ramp) -- the deck part keeps its photographed shadow
for x in range(X0, X1):
    for y in range(YB + 1, YB + 10):
        if gm[y, x] > 0.5: continue
        a = 0.38 * (1 - (y - YB - 1) / 9.0) ** 1.6
        fall = np.clip((X1 - 6 - x) / 10.0, 0, 1)
        gm[y, x] = max(gm[y, x], a * fall); P[y, x] = 0
# anything left of the reed mask below the pod bottom on the cladding side: lawn shows (no remnant reeds)
low = (yy > YB) & (yy < 506) & (xx > X1) & (xx < X1 + 14)
gm[(yy >= 440) & (yy < 506) & (xx > X1 + 1) & (xx < 1350)] = 0
low = (yy > YB + 9) & (yy < 506) & (xx >= X0) & (xx < X1 + 12) & REED
gm[low] = 0
M['garden_room'] = gm; SRCPOD = P

# ---------------- 2. retreat gravel pad ----------------
edge_pts = [(1336, 499), (1400, 511), (1460, 527), (1530, 547), (1600, 556), (1670, 562)]
ex = np.array([p[0] for p in edge_pts]); ey = np.array([p[1] for p in edge_pts])
edge_y = np.interp(np.arange(W), ex, ey) + np.interp(np.arange(W), np.arange(0, W, 6), rng.normal(0, 0.9, len(range(0, W, 6))))
reg = (xx >= 1336) & (yy >= 466) & (yy <= 570)
reedish = ((h > 22) & (h < 95) & (s > 60) & (v > 58)) | ((h >= 16) & (h <= 40) & (s > 80) & (v > 110))
reedish = cv2.dilate(reedish.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
gravel_like = reg & ~reedish & (s < 60) & (v > 70) & (v < 200)
# keep objects (sauna, tub, steps, stove, logs) out of the "to fill" set: fill only reed pixels on the pad, below the objects
objects = (yy < 470) | ((xx >= 1488) & (xx < 1572) & (yy < 540)) | ((xx >= 1600) & (yy < 548) & (xx < 1640)) | ((xx >= 1625) & (yy < 562) & (yy > 520))
pad = reg & (yy <= edge_y[xx]) & ~objects
fill = pad & reedish
# gravel = low frequency (illumination, inpainted across the reed holes) + high frequency (grain, mirror-tiled from the
# one fully clean 32x10 patch of this pad at 1358,494); no block copying, so no tile seams
R = A.copy()
hole = cv2.dilate(fill.astype(np.uint8), np.ones((3, 3), np.uint8))
known = (reg & ~hole.astype(bool) & ~objects & (yy <= edge_y[xx] + 2))
lo = cv2.GaussianBlur(A, (0, 0), 3.0)
lo_u8 = np.clip(lo, 0, 255).astype(np.uint8)
holes_all = (reg & ~known).astype(np.uint8)
low = cv2.inpaint(lo_u8, holes_all, 9, cv2.INPAINT_TELEA).astype(np.float32)
low = cv2.GaussianBlur(low, (0, 0), 2.0)
P0 = A[494:504, 1358:1390]; P0hi = P0 - cv2.GaussianBlur(P0, (0, 0), 3.0)
tile = np.vstack([np.hstack([P0hi, P0hi[:, ::-1]]), np.hstack([P0hi[::-1], P0hi[::-1, ::-1]])])   # 20 x 64
th, tw = tile.shape[:2]
hi = np.zeros_like(A)
for y0 in range(450, 580, th):
    off = int(rng.integers(0, tw))
    for x0 in range(1320 - off, W, tw):
        ya, xa = max(y0, 0), max(x0, 0); yb, xb = min(y0 + th, H), min(x0 + tw, W)
        hi[ya:yb, xa:xb] = tile[ya - y0:yb - y0, xa - x0:xb - x0]
# a little desaturation keeps the fill as neutral as the photographed gravel
syn = low + hi * 1.05
gray = syn.mean(2, keepdims=True); syn = gray + (syn - gray) * 0.85
fm = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 0.8)[..., None]
R = np.where(reg[..., None], A * (1 - fm) + syn * fm, A)
SRCRET = R
rm = M['garden_retreat'].copy()
right = (xx >= 1336) & (yy >= 466) & (yy <= 575)
pad_alpha = np.clip(edge_y[xx] + 0.8 - yy, 0, 1.6) / 1.6
newm = np.where(right, np.maximum(np.where(objects & right, rm, 0), pad_alpha * (yy >= 466)), rm)
# objects keep their own (photographed) matte; the pad is everything above the new front edge
newm = np.where(right & ~objects, pad_alpha, newm)
# a soft lip shadow where gravel meets lawn
lip = right & (yy > edge_y[xx]) & (yy < edge_y[xx] + 4)
R = np.where(lip[..., None], 0, R); SRCRET = R; newm = np.where(lip, 0.22 * (1 - (yy - edge_y[xx]) / 4.0), newm)
M['garden_retreat'] = np.clip(newm, 0, 1).astype(np.float32)

np.savez_compressed('out/mattes.npz', **M)
np.save('out/src-garden-room.npy', np.clip(SRCPOD, 0, 255).astype(np.uint8))
np.save('out/src-garden-retreat.npy', np.clip(SRCRET, 0, 255).astype(np.uint8))
order = json.load(open('out/layers-report.json'))['order']
NOREF = cv2.imread('out/pool-noreflection.png').astype(np.float32)
SRC = {k: A for k in order}; SRC['garden-room'] = SRCPOD; SRC['garden-retreat'] = SRCRET; SRC['natural-swimming-pool'] = NOREF
def comp(keys):
    out = B.copy()
    for k in order:
        if k in keys: a = M[k.replace('-', '_')][..., None]; out = out * (1 - a) + SRC[k] * a
    return out
for k in order: cv2.imwrite('out/comp-%s.png' % k, comp([k]).astype(np.uint8))
allc = comp(order); cv2.imwrite('out/comp-all.png', allc.astype(np.uint8)); cv2.imwrite('out/comp-clear.png', comp([]).astype(np.uint8))
for pair in [('garden-room', 'garden-retreat'), ('garden-room', 'natural-swimming-pool'), ('garden-retreat', 'natural-swimming-pool')]:
    cv2.imwrite('out/comp-%s+%s.png' % pair, comp(list(pair)).astype(np.uint8))
u = np.zeros((H, W), bool)
for k in order: u |= M[k.replace('-', '_')] > 0.98
err = np.abs(allc - A).max(2)
print('ALL vs POSSIBLE inside features: mean %.3f p99 %.1f' % (err[u].mean(), np.percentile(err[u], 99)))
print('CLEAR == BEFORE:', np.array_equal(comp([]).astype(np.uint8), B.astype(np.uint8)))
