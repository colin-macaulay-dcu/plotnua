#!/usr/bin/env python3
"""
DISC-025 The Borrowed Garden · hero slider (Pass 2 Release 4, founder approval 30 Oct 2026)
Before/Possible pair from the page's own pictures, which align at sub-pixel level (SIFT, median 0.34 px):

  BEFORE   59d566ff7c3a50e8.jpg  the lawn as it is today -- but the file carries PlotNua's own burned-in
           "PLOTNUA DISCOVERY / Potential Asset" annotation (leader line, dot, two lines of text on a white
           glow). A slider must not show a label that is wiped away with the lawn, so the hero uses a copy
           with that annotation removed (Governance 2.0, Rule 3: routine artefact removal of PlotNua's own
           image; it is not a third-party notice). The source and its other use on the page are unchanged.
  POSSIBLE faeb58a1d6a8ed1a.jpg  the same garden with raised beds (the page's current hero), plus WebP
           re-encodings for the slider.

  Annotation removal, deterministic, confined to the box x 650-1100, y 425-565 (feathered edges reach
  at most 16 px beyond it; --check refuses any change outside x 630-1120, y 405-585):
    1. the white glow is modelled as white blended at opacity a(x,y): a is the low-pass excess brightness
       over the lawn around the box (normalised convolution, sigma 45, outside the box only), smoothed;
       lawn = (observed - a*255) / (1 - a). This keeps the lawn's own texture.
    2. the text, leader line and dot (fixed shapes) are replaced by the lawn 90 px below, colour-matched
       to the surrounding lawn (sigma 18), with a 3 px feather. No generative fill.

  python3 atlas-tools/build-disc025-hero-before.py          build files + register derivatives
  python3 atlas-tools/build-disc025-hero-before.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
SRC = "assets/img/59d566ff7c3a50e8.jpg"
POS = "assets/img/faeb58a1d6a8ed1a.jpg"
OUT = "assets/disc025/img/DISC-025-HERO-BEFORE"
BOX = (650, 425, 1100, 565)
LIMIT = (630, 405, 1120, 585)
CHECK = "--check" in sys.argv
DESC = ("Before/Possible pair preparation for the Borrowed Garden hero (Governance 2.0, Rule 3): removal of "
        "PlotNua's own burned-in 'PLOTNUA DISCOVERY / Potential Asset' annotation (leader line, dot, two lines "
        "of text and its white glow) from the lawn, so the BEFORE can sit under a slider. Nothing else changed.")
OPER = ("Confined to x 650-1100, y 425-565 (feather reaches at most x 630-1120, y 405-585). The glow is reversed "
        "as white at a measured, spatially varying opacity (low-pass excess over the surrounding lawn); the text, "
        "line and dot are replaced by the same lawn 90 px lower, colour-matched to their surroundings, 3 px "
        "feather. No generative fill. Every pixel outside the limit is the decoded source pixel before encoding.")


def sha(b): return hashlib.sha256(b).hexdigest()


def clean(I8):
    I = I8.astype(np.float32); H, W = I.shape[:2]
    x0, y0, x1, y1 = BOX
    box = np.zeros((H, W), np.float32); box[y0:y1, x0:x1] = 1
    w = 1 - box
    B0 = cv2.GaussianBlur(I * w[..., None], (0, 0), 45) / np.maximum(cv2.GaussianBlur(w, (0, 0), 45), 1e-3)[..., None]
    L = cv2.GaussianBlur(I, (0, 0), 9)
    a = np.clip(((L - B0) / (255 - B0)).mean(2), 0, 0.85) * box
    a = cv2.GaussianBlur(a, (0, 0), 4)[..., None]
    J = np.clip((I - a * 255) / np.maximum(1 - a, 0.15), 0, 255)
    ox, oy = 600, 380
    m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (ox + 200, oy + 68), (ox + 468, oy + 101), 255, -1)
    cv2.rectangle(m, (ox + 240, oy + 98), (ox + 434, oy + 136), 255, -1)
    cv2.line(m, (ox + 86, oy + 151), (ox + 150, oy + 86), 255, 9)
    cv2.line(m, (ox + 148, oy + 86), (ox + 205, oy + 86), 255, 9)
    cv2.circle(m, (ox + 87, oy + 151), 11, 255, -1)
    src = np.roll(J, -90, 0)
    wd = (1 - cv2.dilate(m, np.ones((9, 9), np.uint8)) / 255.0).astype(np.float32)
    mu_d = cv2.GaussianBlur(J * wd[..., None], (0, 0), 18) / np.maximum(cv2.GaussianBlur(wd, (0, 0), 18), 1e-3)[..., None]
    src2 = src - cv2.GaussianBlur(src, (0, 0), 18) + mu_d
    f = np.clip(cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 3) * 1.6, 0, 1)[..., None]
    out = np.clip(J * (1 - f) + src2 * f, 0, 255).astype(np.uint8)
    lx0, ly0, lx1, ly1 = LIMIT
    keep = np.ones((H, W), bool); keep[ly0:ly1, lx0:lx1] = False
    out[keep] = I8[keep]          # hard guarantee: nothing outside the limit changes
    return out


def enc(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    for a in (SRC, POS):
        if sha((ROOT / a).read_bytes()) != legacy[a]["sha256"]:
            sys.exit("REFUSED: %s differs from the register -- nothing written" % a)
    I8 = cv2.imread(str(ROOT / SRC))
    out = clean(I8)
    d = np.abs(out.astype(int) - I8.astype(int)).max(2)
    ys, xs = np.nonzero(d)
    lx0, ly0, lx1, ly1 = LIMIT
    if len(xs) and (xs.min() < lx0 or ys.min() < ly0 or xs.max() >= lx1 or ys.max() >= ly1):
        sys.exit("REFUSED: a change outside the edit limit")
    rgb = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    files = {
        OUT + ".jpg": (enc(rgb, "JPEG", quality=92, progressive=True, optimize=True),
                       "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION, SRC, "artefact-removal"),
        OUT + "-1408.webp": (enc(rgb, "WEBP", quality=80, method=6),
                             "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, SRC, "artefact-removal"),
        OUT + "-960.webp": (enc(rgb.resize((960, 524), Image.LANCZOS), "WEBP", quality=80, method=6),
                            "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION, SRC, "artefact-removal"),
    }
    prgb = Image.open(ROOT / POS).convert("RGB")
    files["assets/img/faeb58a1d6a8ed1a.webp"] = (enc(prgb, "WEBP", quality=80, method=6),
        "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, POS, "webp-reencode")
    files["assets/img/faeb58a1d6a8ed1a-960w.webp"] = (enc(prgb.resize((960, 524), Image.LANCZOS), "WEBP", quality=80, method=6),
        "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION, POS, "webp-resize")
    have = {x["asset"]: x for x in reg["derivatives"]}
    bad = []
    if CHECK:
        for a, (data, *_r) in files.items():
            p = ROOT / a
            if not p.exists() or a not in have or have[a]["sha256"] != sha(p.read_bytes()):
                bad.append(a)
            elif sha(p.read_bytes()) != sha(data):
                bad.append(a + " (not reproducible)")
        print("DISC-025 HERO BEFORE · " + ("OK (%d files; edit confined to the limit)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    (ROOT / OUT).parent.mkdir(parents=True, exist_ok=True)
    for a, (data, encoder, src, method) in files.items():
        (ROOT / a).write_bytes(data)
        im = Image.open(io.BytesIO(data))
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(im.size),
             "derived_from": {"asset": src, "sha256": legacy[src]["sha256"]}, "method": method}
        if method == "artefact-removal":
            e["edit"] = {"description": DESC, "operation": OPER, "box_xyxy": list(BOX), "limit_xyxy": list(LIMIT),
                         "changed_pixels": int((d > 0).sum()), "changed_share_of_image": round(float((d > 0).mean()), 6),
                         "verified_by": "atlas-tools/build-disc025-hero-before.py --check"}
        e["encoder"] = encoder
        e["made"] = "2026-10-30"
        e["content_credentials"] = {"source_file_embeds_c2pa": False, "derivative_embeds_c2pa": False,
            "note": "The source carries no embedded credential. This file inherits the source's LEGACY_UNDECLARED state and declares nothing."}
        reg["derivatives"] = [x for x in reg["derivatives"] if x["asset"] != a] + [e]
        print("written", a, len(data))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
