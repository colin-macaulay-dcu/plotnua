"""Power Station device sprites for the daylight scene, transplanted from the previously approved H6 photographic assets
(battery and EV charger from H6-layer-power-station-1677.webp; heat-pump unit from H6-garden-base-v6-1677.webp), re-graded
from the warm evening light to the daylight BEFORE photograph (wall/patio tone statistics), with soft contact shadows.
Writes small RGBA WebP sprites (2x for sharpness) + a preview composite. No generated imagery."""
import numpy as np, cv2, json
from PIL import Image
IMG = '/home/claude/plotnua/assets/h6/img/'
B = cv2.cvtColor(cv2.imread('in/hero-before-master.png'), cv2.COLOR_BGR2RGB).astype(np.float32)
L = np.array(Image.open(IMG + 'H6-layer-power-station-1677.webp').convert('RGBA')).astype(np.float32)
OB = np.array(Image.open(IMG + 'H6-garden-base-v6-1677.webp').convert('RGB')).astype(np.float32)

def regrade(rgb, ref):
    """match per-channel mean/std of the object to a neutral daylight version of itself: remove the warm cast, set the
    luminance to the reference surface's light level"""
    lum = rgb.mean(2, keepdims=True)
    neutral = lum + (rgb - lum) * 0.35                     # strip most of the evening colour cast
    tgt_mean = ref.reshape(-1, 3).mean(0); tgt_l = tgt_mean.mean()
    k = tgt_l * 1.0 / max(1, np.percentile(neutral, 90))   # the object's lit face ~ the surface light level
    out = neutral * k * 0.96 + (tgt_mean - tgt_l) * 0.25    # a hint of the scene's own tint
    return np.clip(out, 0, 255)

sprites = {}
# battery: alpha from the approved layer
bat = L[381:417, 220:241]; a_b = bat[..., 3] / 255
sprites['battery'] = (regrade(bat[..., :3], B[350:385, 748:768]), a_b, (749.5, 353.0, 16.5, 28.5))
# charger
ch = L[388:408, 244:255]; a_c = ch[..., 3] / 255
sprites['charger'] = (regrade(ch[..., :3], B[350:385, 700:720]) * 0.62, a_c, (704.0, 357.0, 8.0, 14.5))
# heat pump: rectangular unit in the old base, matte by its box with rounded 1px edges
hp = OB[302:333, 762:808]
m = np.zeros(hp.shape[:2], np.float32); m[1:30, 1:45] = 1; m = cv2.GaussianBlur(m, (0, 0), 0.6)
sprites['heatpump'] = (regrade(hp, B[400:440, 690:770]) * 1.02, m, (781.0, 413.0, 44.0, 30.0))

out = {}
prev = B.copy()
for name, (rgb, a, (x, y, w, h)) in sprites.items():
    S = 2  # sprite resolution: 2x its on-image size
    W2, H2 = int(round(w * S)), int(round(h * S))
    rgb2 = cv2.resize(rgb, (W2, H2), interpolation=cv2.INTER_CUBIC); a2 = cv2.resize(a, (W2, H2), interpolation=cv2.INTER_CUBIC)
    # soft contact shadow (light from upper left): offset down-right, blurred, inside the sprite canvas padding
    pad = int(6 * S)
    canvas = np.zeros((H2 + pad, W2 + pad, 4), np.float32)
    sh = np.zeros((H2 + pad, W2 + pad), np.float32); sh[int(2 * S):int(2 * S) + H2, int(2.5 * S):int(2.5 * S) + W2] = np.clip(a2, 0, 1)
    sh = cv2.GaussianBlur(sh, (0, 0), 2.2 * S) * 0.33
    canvas[..., 3] = sh
    aa = np.clip(a2, 0, 1)[..., None]
    canvas[:H2, :W2, :3] = rgb2 * aa + canvas[:H2, :W2, :3] * (1 - aa)
    canvas[:H2, :W2, 3] = aa[..., 0] + canvas[:H2, :W2, 3] * (1 - aa[..., 0])
    canvas[..., 3] *= 255
    im = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), 'RGBA')
    p = (IMG if name == 'heatpump' else 'out/devices/') + 'H6v7-device-%s.webp' % name; im.save(p, 'WEBP', quality=90, method=6, exact=True)
    ow, oh = (W2 + pad) / S, (H2 + pad) / S
    out[name] = dict(x=x, y=y, w=round(ow, 2), h=round(oh, 2), file='assets/h6/img/H6v7-device-%s.webp' % name)
    # preview composite at image scale
    small = cv2.resize(canvas, (int(round(ow)), int(round(oh))), interpolation=cv2.INTER_AREA)
    xi, yi = int(round(x)), int(round(y)); al = small[..., 3:4] / 255
    region = prev[yi:yi + small.shape[0], xi:xi + small.shape[1]]
    prev[yi:yi + small.shape[0], xi:xi + small.shape[1]] = region * (1 - al) + small[..., :3] * al
json.dump(out, open('out/devices.json', 'w'), indent=1)
cv2.imwrite('out/devices-preview.png', cv2.cvtColor(cv2.resize(prev[320:470, 680:850], None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4).astype(np.uint8), cv2.COLOR_RGB2BGR))
print(json.dumps(out, indent=1))
