#!/usr/bin/env python3
"""
DISC-016 Above and Beyond · hero slider · visible-mark removal (Pass 2 Release 3,
founder instruction 30 Oct 2026: "Do not introduce the faint Gemini watermark into the
new Above and Beyond slider assets. If removal requires a new image derivative, prepare
it for review with provenance records. Do not silently alter the source images.")

PREPARED FOR FOUNDER REVIEW. NOT A P12 DERIVATIVE.
  The two legacy sources carry a faint, semi-transparent four-point sparkle (the Gemini
  visible mark) at the same place, about (1288, 648) in 1408 x 768. This script makes NEW
  files for the hero slider only. The sources are read, hash-checked and never written.

  Operation, per source (deterministic):
    1. a four-point star mask, |dx/r|^p + |dy/r|^p <= 1, centre (1288, 649), r 27, p 0.62,
       anti-aliased by 4x supersampling (the same mask for both images);
    2. reverse alpha blending: the mark is modelled as white at a uniform opacity a, so
       original = (observed - a*T*255) / (1 - a*T); a is measured per image from the mean
       inside the star against a 7-pixel ring outside it;
    3. a 3-pixel Telea inpaint on the star's anti-aliased edge band only (seam).
  Every pixel outside the star's bounding box (dilated by 2 px) is the source pixel,
  unchanged; --check verifies this on the lossless intermediate.

  Outputs (assets/disc016/img/): DISC-016-HERO-{BEFORE,POSSIBLE}-MR.jpg (fallback, quality
  92), -MR-1408.webp and -MR-960.webp (quality 80, method 6). Recorded in
  governance/DISC-016-HERO-MARK-REMOVAL-REVIEW-DRAFT-2026-10-30.json.

  python3 atlas-tools/build-disc016-hero-mark-removal.py          build
  python3 atlas-tools/build-disc016-hero-mark-removal.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/disc016/img"
DRAFT = ROOT / "governance/DISC-016-HERO-MARK-REMOVAL-REVIEW-DRAFT-2026-10-30.json"
CHECK = "--check" in sys.argv
SOURCES = {
    "BEFORE": ("assets/img/b53d75f9dff4af2e.jpg", "b53d75f9dff4af2e"),
    "POSSIBLE": ("assets/img/aecece07994fe0db.jpg", "aecece07994fe0db"),
}
CX, CY, R, P, SS = 1288.0, 649.0, 27.0, 0.62, 4


def sha(b): return hashlib.sha256(b).hexdigest()


def star(h, w):
    y, x = np.mgrid[0:h * SS, 0:w * SS].astype(np.float32) / SS
    f = (np.abs(x - CX) / R) ** P + (np.abs(y - CY) / R) ** P
    return cv2.resize((f <= 1).astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)


def clean(bgr):
    h, w = bgr.shape[:2]
    T = star(h, w)
    inside = T > 0.99
    ring = (cv2.dilate((T > 0).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0) & (T == 0)
    im = bgr.astype(np.float32)
    mi, mo = im[inside].mean(0), im[ring].mean(0)
    a = float(np.clip(((mi - mo) / (255 - mo)).mean(), 0, 0.9))
    A = (a * T)[..., None]
    rec = np.clip((im - A * 255) / (1 - A), 0, 255).astype(np.uint8)
    edge = cv2.dilate((((T > 0.02) & (T < 0.98)).astype(np.uint8) * 255), np.ones((3, 3), np.uint8))
    out = cv2.inpaint(rec, edge, 3, cv2.INPAINT_TELEA)
    ys, xs = np.where(T > 0)
    box = [int(xs.min()) - 2, int(ys.min()) - 2, int(xs.max()) + 3, int(ys.max()) + 3]
    return out, round(a, 4), box


def enc(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def main():
    reg = json.loads((ROOT / "image-provenance-records.json").read_text(encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    files, recs = {}, []
    for role, (src, stem) in SOURCES.items():
        raw = (ROOT / src).read_bytes()
        if src not in legacy or legacy[src]["sha256"] != sha(raw):
            print("REFUSED: %s is not the registered legacy file" % src); sys.exit(1)
        bgr = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        out, a, box = clean(bgr)
        diff = np.any(out != bgr, axis=2)
        x0, y0, x1, y1 = box
        outside = diff.copy(); outside[y0:y1, x0:x1] = False
        if outside.any():
            print("REFUSED: %s changed pixels outside the mark's box" % src); sys.exit(1)
        rgb = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        base = "assets/disc016/img/DISC-016-HERO-%s-MR" % role
        variants = [(base + ".jpg", enc(rgb, "JPEG", quality=92, optimize=True, progressive=True), rgb.size),
                    (base + "-1408.webp", enc(rgb, "WEBP", quality=80, method=6), rgb.size)]
        small = rgb.resize((960, round(rgb.height * 960 / rgb.width)), Image.LANCZOS)
        variants.append((base + "-960.webp", enc(small, "WEBP", quality=80, method=6), small.size))
        for path, data, size in variants:
            files[path] = data
            recs.append({"asset": path, "sha256": sha(data), "bytes": len(data), "pixels": list(size), "role": role})
        recs.append({"source": {"asset": src, "sha256": sha(raw), "state": "LEGACY_UNDECLARED", "embeds_c2pa": b"jumdc2pa" in raw},
                     "role": role, "measured_mark_opacity": a, "changed_box_xyxy": box,
                     "changed_pixels": int(diff.sum()), "changed_share_of_image": round(float(diff.mean()), 6)})
    if CHECK:
        bad = [p for p, d in files.items() if not (ROOT / p).exists() or (ROOT / p).read_bytes() != d]
        print("DISC-016 MARK REMOVAL · " + ("OK" if not bad else "DIFFERS: %s" % bad)); sys.exit(1 if bad else 0)
    OUT.mkdir(parents=True, exist_ok=True)
    for p, d in files.items(): (ROOT / p).write_bytes(d)
    draft = json.loads(DRAFT.read_text(encoding="utf-8")) if DRAFT.exists() else {}
    draft["build_output"] = {"tool": "atlas-tools/build-disc016-hero-mark-removal.py",
                             "libraries": "OpenCV %s, Pillow %s, NumPy %s" % (cv2.__version__, PIL_VERSION, np.__version__),
                             "mask": {"centre": [CX, CY], "radius_px": R, "exponent": P, "supersample": SS},
                             "files": recs}
    DRAFT.write_text(json.dumps(draft, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in recs: print(r)


if __name__ == "__main__":
    main()
