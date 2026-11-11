"""H6 v7 · cloud lettering v2 (11 Nov 2026): cumulus letters for 'Discover what’s possible.' that condense in the sky.

Deterministic and procedural: no generative AI, no new photograph. The only input is the hero photograph already in the
repo (assets/h6/img/H6v7-before-1670.webp), from which the sky band below is cropped and measured.
Band (master pixels): x 730..1550, y 0..224, the open sky between the tree and the neighbouring roofs.
Outputs (assets/h6/img/):
  H6v7-cloud-src.webp     the band as photographed (what the visitor sees first)
  H6v7-cloud-fill.webp    the band with the foreground painted out: the cloud that drifts (never drags a roof along)
  H6v7-cloud-plate.webp   the band as clear blue sky (a smooth fit to the photograph's own blue pixels)
  H6v7-cloud-colour.webp  the lit cumulus lettering, 2x band resolution
  H6v7-cloud-density.webp 2x, greyscale: cloud density of the letters
  H6v7-cloud-data.webp    lossless, 1x: R = when each billow condenses (0 first .. 1 last), G = open sky,
                          B = the words as loose cloud masses (what the drifting cloud gathers into before the letters condense)
  H6v7-cloud-field.webp   lossless, half band resolution: R,G = the gathering drift toward the words (+128), B = where the sky thins
How the letters are made: the words are set in a heavy serif and rebuilt as a heap of overlapping spherical puffs: a
continuous tube along every stroke, body puffs sized to the stroke, then smaller billows on the sunlit crowns, as in a
real cumulus. Each puff gets its own moment to condense (spatially correlated, body before crowns), so the words build
billow by billow rather than fading in. The heap is lit by a high sun (bright crowns, soft grey-blue bases, glowing thin
fringes) in this sky's own cloud colours, measured from the band.
Run from the repo root: python3 atlas-tools/h6v7/pipeline/clouds.py [--still OUT.png]"""
import numpy as np, cv2, os, sys
from PIL import Image, ImageDraw, ImageFont
IMG = 'assets/h6/img/'
BX, BY, BW, BH, K = 730, 0, 820, 224, 2
W2, H2 = BW * K, BH * K
rng = np.random.default_rng(11)

full = np.array(Image.open(IMG + 'H6v7-before-1670.webp').convert('RGB'))
src8 = full[BY:BY + BH, BX:BX + BW].copy(); src = src8.astype(np.float32)
# ---- open sky vs foreground (branches, roofs, chimney, antenna, trees): the same rule as sky.py (v1)
bgr = cv2.cvtColor(src8, cv2.COLOR_RGB2BGR)
lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32); hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
fg = ((hsv[..., 0] > 25) & (hsv[..., 0] < 95) & (hsv[..., 1] > 45)) | (lab[..., 0] < 105) | ((hsv[..., 0] < 22) & (hsv[..., 1] > 60))
fg = cv2.morphologyEx(fg.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
fg = cv2.dilate(fg, np.ones((5, 5), np.uint8))
sky = cv2.GaussianBlur(1 - fg.astype(np.float32), (0, 0), 0.8)
# the band's open edges (left, right, bottom) fade to the untouched photograph; the top is the image edge
yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
edge = np.clip(xx / 24, 0, 1) * np.clip((BW - 1 - xx) / 24, 0, 1) * np.clip((BH - 1 - yy) / 20, 0, 1)
sky *= edge

# ---- clear-sky plate: smooth fit of the photograph's own blue pixels
blue = ((src[..., 2] - src[..., 0]) > 70) & (sky > 0.9)
A = np.stack([np.ones_like(xx), xx / BW, yy / BH, (yy / BH) ** 2], -1)
plate = np.zeros_like(src)
for c in range(3):
    coef, *_ = np.linalg.lstsq(A[blue], src[..., c][blue], rcond=None); plate[..., c] = A @ coef
haze = np.clip((yy / BH - 0.3) / 0.7, 0, 1)[..., None]
plate = np.clip(plate * (1 - 0.22 * haze) + np.array([226, 233, 241], np.float32) * 0.22 * haze, 0, 255)

# ---- the words
SS = 4
font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc', 74 * SS * K, index=0)
cv = Image.new('L', (W2 * SS, H2 * SS), 0); d = ImageDraw.Draw(cv)
TRACK = 0.05 * 74 * SS * K
for t, y, cx in (('Discover', 4, 0.5), ('what’s possible.', 92, 0.5)):
    ws = [d.textlength(ch, font=font) for ch in t]; w = sum(ws) + TRACK * (len(t) - 1); x = W2 * SS * cx - w / 2
    for ch, cw in zip(t, ws): d.text((x, y * SS * K), ch, font=font, fill=255); x += cw + TRACK
txt = np.array(cv.resize((W2, H2), Image.LANCZOS)).astype(np.float32) / 255
inside = (txt > 0.5).astype(np.uint8)
sdf = cv2.distanceTransform(inside, cv2.DIST_L2, 5) - cv2.distanceTransform(1 - inside, cv2.DIST_L2, 5)
core = sdf + 2.0 * K

def fbm(oct, base, seed, shape=(H2, W2)):
    g = np.random.default_rng(seed); h_, w_ = shape; n = np.zeros(shape, np.float32); amp = 1.0; tot = 0
    for o in range(oct):
        s = base / (2 ** o); a = g.standard_normal((int(h_ / s) + 3, int(w_ / s) + 3)).astype(np.float32)
        n += amp * cv2.resize(a, (w_ + int(3 * s), h_ + int(3 * s)), interpolation=cv2.INTER_CUBIC)[:h_, :w_]; tot += amp; amp *= 0.55
    return n / tot
when_field = np.clip(fbm(2, 60.0 * K, 5) * 0.9 + 0.5, 0, 1)      # spatially correlated birth times: the formation travels

# ---- the heap of puffs; O records when the puff that forms each pixel condenses
H = (np.sqrt(np.clip(core, 0, None)) * np.sqrt(2.0 * K * 6)).astype(np.float32)
O = np.where(H > 0, 0.06 + 0.30 * when_field, 1.0).astype(np.float32)
def puff(cx, cy, r, t0, lift=0.0):
    x0, x1 = int(max(0, cx - r - 1)), int(min(W2, cx + r + 2)); y0, y1 = int(max(0, cy - r - 1)), int(min(H2, cy + r + 2))
    if x1 <= x0 or y1 <= y0: return
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d2 = (gx - cx) ** 2 + (gy - cy) ** 2
    cap = np.where(d2 <= r * r, np.sqrt(np.maximum(0, r * r - d2)) + lift, 0)
    win = cap > H[y0:y1, x0:x1]
    H[y0:y1, x0:x1][win] = cap[win]
    O[y0:y1, x0:x1][win] = np.minimum(1, t0 + 0.10 * np.sqrt(d2[win]) / r)   # each billow swells from its centre
ys, xs = np.where(core > 1.0)
for i in rng.permutation(len(xs))[: len(xs) // 12]:
    x, y = xs[i], ys[i]; r = core[y, x] * rng.uniform(0.85, 1.12) + rng.uniform(0.3, 1.4) * K
    puff(x + rng.normal(0, 0.6), y + rng.normal(0, 0.6), r, 0.10 + 0.40 * when_field[y, x] + rng.uniform(0, 0.08))
gy_, gx_ = np.gradient(cv2.GaussianBlur(H, (0, 0), 2))
rim = (H > 0) & (H < 0.45 * cv2.dilate(H, np.ones((9, 9), np.uint8)))
ys, xs = np.where(rim)
for i in rng.permutation(len(xs))[: len(xs) // 8]:
    x, y = xs[i], ys[i]
    up = -gy_[y, x] / (np.hypot(gx_[y, x], gy_[y, x]) + 1e-4)
    if up < 0.05 or rng.random() > 0.35 + 0.65 * up: continue
    r = rng.uniform(2.0, 5.0) * K * (0.75 + 0.5 * up)
    puff(x + rng.normal(0, 1.0), y + rng.normal(0, 1.0), r, 0.45 + 0.35 * when_field[y, x] + rng.uniform(0, 0.1), lift=H[y, x] * 0.55)
H = cv2.GaussianBlur(H, (0, 0), 0.7 * K)
O = cv2.GaussianBlur(O, (0, 0), 0.6 * K)
detail = fbm(4, 7.0 * K, 3)
dens = np.clip((H + detail * 1.4 * K - 0.6 * K) / (3.0 * K), 0, 1); dens = dens * dens * (3 - 2 * dens)
dens *= np.clip(0.9 + 0.1 * fbm(3, 5.0 * K, 4), 0, 1)
dens *= np.clip(0.80 + 0.32 * fbm(2, 36.0 * K, 41), 0.62, 1)   # natural variation: some billows thinner than others
dens *= cv2.GaussianBlur(cv2.dilate((H > 0).astype(np.float32), np.ones((5, 5), np.uint8)), (0, 0), 1.5)

# ---- vertical position within each run of cloud (0 crown .. 1 base): cumulus bases sit in their own shade
vert = np.zeros_like(H)
for x in range(W2):
    ys_ = np.where(dens[:, x] > 0.05)[0]
    if len(ys_) < 2: continue
    for r in np.split(ys_, np.where(np.diff(ys_) > 1)[0] + 1):
        if len(r) > 1: vert[r, x] = np.linspace(0, 1, len(r))
vert = cv2.GaussianBlur(vert, (0, 0), 2.5 * K)
base = np.clip((vert - 0.55) / 0.45, 0, 1)
dens = dens * (1 - base) + cv2.GaussianBlur(dens, (0, 0), 1.8 * K) * base          # soft, flatter bases

# ---- light: high sun, wrap lighting (vapour scatters light round the edges, so silhouettes don't go dark)
Hs = cv2.GaussianBlur(H + detail * 0.9 * K, (0, 0), 0.8 * K)
gy, gx = np.gradient(Hs); nz = np.full_like(Hs, 1.15)
nrm = np.sqrt(gx * gx + gy * gy + nz * nz); nx, ny, nzz = -gx / nrm, -gy / nrm, nz / nrm
L = np.array([-0.30, -0.80, 0.52]); L /= np.linalg.norm(L)
ndl = nx * L[0] + ny * L[1] + nzz * L[2]
wrap = np.clip((ndl + 0.45) / 1.45, 0, 1)
sh = np.zeros_like(Hs); step = 1.6 * K
dx, dy = L[0] / np.hypot(L[0], L[1]), L[1] / np.hypot(L[0], L[1]); rise = L[2] / np.hypot(L[0], L[1])
for k in range(1, 14):
    M = np.float32([[1, 0, dx * step * k], [0, 1, dy * step * k]])
    ahead = cv2.warpAffine(Hs, M, (W2, H2), flags=cv2.INTER_LINEAR, borderValue=0)
    sh = np.maximum(sh, (ahead - Hs - rise * step * k * 0.55) / (4.0 * K))
shadow = 1 - np.clip(sh, 0, 1) * 0.6
ao = np.clip(1 - (cv2.GaussianBlur(Hs, (0, 0), 6 * K) - Hs) / (6.0 * K), 0.65, 1)
light = np.clip((0.25 + 0.85 * wrap * shadow) * ao * (1 - 0.42 * vert ** 1.5), 0, 1)
# this sky's own cloud colours (band percentiles): base shade, body, sunlit crown
SHADE = np.array([166, 176, 194], np.float32); BODY = np.array([221, 226, 235], np.float32); CROWN = np.array([253, 252, 250], np.float32)
t = light[..., None]
col = np.where(t < 0.6, SHADE + (BODY - SHADE) * (t / 0.6), BODY + (CROWN - BODY) * ((t - 0.6) / 0.4).clip(0, 1))
fr = ((1 - dens) * (dens > 0.02))[..., None]
col = np.clip(col * (1 - 0.45 * fr) + CROWN * 0.45 * fr, 0, 255)
O[dens < 0.01] = 1

# ---- band fields: drift toward the words, and where the surrounding cloud thins (its material went into the words)
m1 = cv2.resize(dens, (BW, BH), interpolation=cv2.INTER_AREA)
pot = cv2.GaussianBlur(m1, (0, 0), 40)
py, px = np.gradient(pot); g = np.hypot(px, py).max() + 1e-6
thin = cv2.GaussianBlur(cv2.dilate((m1 > 0.05).astype(np.float32), np.ones((9, 9), np.uint8)), (0, 0), 10)
thin = np.clip(thin * 1.2, 0, 1) * np.clip(0.8 + 0.3 * fbm(2, 40.0, 21, (BH, BW)), 0, 1) * sky

# ---- write
sky2 = cv2.resize(sky, (W2, H2), interpolation=cv2.INTER_LINEAR)
Image.fromarray(src8).save(IMG + 'H6v7-cloud-src.webp', quality=94, method=6)
# the band with branches, roofs, chimney and antenna painted out (sky only), so drifting cloud never drags them along
fill = cv2.inpaint(src8, (cv2.dilate(fg, np.ones((7, 7), np.uint8)) > 0).astype(np.uint8), 9, cv2.INPAINT_TELEA)
fill = np.where(cv2.dilate(fg, np.ones((7, 7), np.uint8))[..., None] > 0, cv2.GaussianBlur(fill, (0, 0), 4), src8)
Image.fromarray(fill.astype(np.uint8)).save(IMG + 'H6v7-cloud-fill.webp', quality=90, method=6)
Image.fromarray(plate.round().astype(np.uint8)).save(IMG + 'H6v7-cloud-plate.webp', quality=92, method=6)
Image.fromarray(col.round().astype(np.uint8)).save(IMG + 'H6v7-cloud-colour.webp', quality=88, method=6)
Image.fromarray((dens * 255).round().astype(np.uint8), 'L').save(IMG + 'H6v7-cloud-density.webp', quality=88, method=6)
O1 = cv2.resize(O, (BW, BH), interpolation=cv2.INTER_AREA)
# B: the letters as loose cloud masses (heavily blurred and broken up): what the incoming cloud gathers into first
mass = cv2.GaussianBlur(cv2.dilate(m1, np.ones((5, 5), np.uint8)), (0, 0), 6.5)
mass = np.clip(mass / max(mass.max(), 1e-6) * 1.35, 0, 1) * np.clip(0.7 + 0.5 * fbm(3, 18.0, 31, (BH, BW)), 0, 1)
Image.fromarray(np.dstack([O1 * 255, sky * 255, np.clip(mass, 0, 1) * 255]).round().astype(np.uint8)).save(IMG + 'H6v7-cloud-data.webp', lossless=True, method=6)
fld = np.dstack([np.clip(px / g * 127 + 128, 0, 255), np.clip(py / g * 127 + 128, 0, 255), thin * 255])
Image.fromarray(cv2.resize(fld, (BW // 2, BH // 2), interpolation=cv2.INTER_AREA).round().astype(np.uint8)).save(IMG + 'H6v7-cloud-field.webp', lossless=True, method=6)   # smooth: half resolution is plenty
for f in ('src', 'fill', 'plate', 'colour', 'density', 'data', 'field'): print(f, os.path.getsize(IMG + 'H6v7-cloud-%s.webp' % f))
if '--still' in sys.argv:   # review still: the formed words over the thinned photograph
    s2 = cv2.resize(src, (W2, H2), interpolation=cv2.INTER_CUBIC); p2 = cv2.resize(plate, (W2, H2), interpolation=cv2.INTER_CUBIC)
    th2 = cv2.resize(thin, (W2, H2))[..., None] * 0.88; a = dens[..., None]; m = sky2[..., None]
    out = (s2 * (1 - th2) + p2 * th2) * (1 - a) + col * a
    Image.fromarray((out * m + s2 * (1 - m)).clip(0, 255).astype(np.uint8)).save(sys.argv[sys.argv.index('--still') + 1])
