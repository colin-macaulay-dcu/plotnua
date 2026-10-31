#!/usr/bin/env python3
"""
PASS 2 · RELEASE 5 · hero slider pairs, routine pair preparation (Governance 2.0, Rule 3; founder approval
31 Oct 2026: "Prepare the aligned pair and implement the existing Before/Possible hero slider").

Each Discovery already shows both pictures; they are the same scene, framed slightly differently:

  Driveway Income (DISC-014)      BEFORE b5cbac3f (empty driveway)  POSSIBLE 4a4a1e4b (two cars parked)
                                   the Possible sits ~48 px lower and 1.8% taller
  Your Home on Screen (DISC-021)  BEFORE ea3f24ee (the house)       POSSIBLE 80614bf6 (a small shoot)
                                   the Possible sits ~11 px higher and 1% smaller

Operation, per pair (deterministic):
  1. the POSSIBLE is mapped onto the BEFORE's frame by a fixed homography (measured once with SIFT + RANSAC
     on the static scene and pinned below), Lanczos resampling;
  2. both pictures are cropped to the same rectangle, the largest one the mapped POSSIBLE fully covers at the
     source's aspect ratio. Nothing is painted, masked or generated; the BEFORE is only cropped.
Outputs (assets/<disc>/img/): <ID>-HERO-{BEFORE,POSSIBLE}.jpg (quality 92) and -full.webp / -960.webp
(quality 80, method 6). Recorded as derivatives (BEFORE: crop; POSSIBLE: pair-preparation) bound to their
unchanged sources. The sources and their other uses are untouched.

  python3 atlas-tools/build-release5-hero-pairs.py          build files + register derivatives
  python3 atlas-tools/build-release5-hero-pairs.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
PAIRS = {
    "DISC-014": dict(dir="assets/disc014/img", before="assets/img/b5cbac3fff9072d4.jpg", possible="assets/img/4a4a1e4b08edaada.jpg",
                     H=[[1.001139, 0.000441, -0.336122], [-0.000259, 1.018013, -48.002527], [0.0, 1e-06, 1.0]],
                     crop=(32, 0, 1343, 732), name="Driveway Income"),
    "DISC-021": dict(dir="assets/disc021/img", before="assets/img/ea3f24eedab76294.jpg", possible="assets/img/80614bf6b2d7d79a.jpg",
                     H=[[0.997415, -0.003423, 0.095865], [0.000492, 0.989823, 10.732516], [2e-06, -6e-06, 1.0]],
                     crop=(11, 12, 1385, 755), name="Your Home on Screen"),
}


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def outputs(disc, p):
    A = cv2.imread(str(ROOT / p["before"])); B = cv2.imread(str(ROOT / p["possible"]))
    H = np.array(p["H"], dtype=np.float64)
    W = cv2.warpPerspective(B, H, (A.shape[1], A.shape[0]), flags=cv2.INTER_LANCZOS4)
    cov = cv2.warpPerspective(np.full(B.shape[:2], 255, np.uint8), H, (A.shape[1], A.shape[0]), flags=cv2.INTER_NEAREST)
    x, y, w, h = p["crop"]
    if not (cov[y:y + h, x:x + w] == 255).all():
        sys.exit("REFUSED: %s crop is not fully covered by the mapped POSSIBLE" % disc)
    out = {}
    for role, img, src, method in (("BEFORE", A, p["before"], "crop"), ("POSSIBLE", W, p["possible"], "pair-preparation")):
        rgb = Image.fromarray(cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_BGR2RGB))
        base = "%s/%s-HERO-%s" % (p["dir"], disc, role)
        out[base + ".jpg"] = (enc(rgb, "JPEG", quality=92, progressive=True, optimize=True), "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION, src, method, role)
        out[base + "-full.webp"] = (enc(rgb, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, src, method, role)
        out[base + "-960.webp"] = (enc(rgb.resize((960, round(960 * h / w)), Image.LANCZOS), "WEBP", quality=80, method=6),
                                   "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION, src, method, role)
    return out


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    have = {d["asset"]: d for d in reg["derivatives"]}
    bad, files = [], {}
    for disc, p in PAIRS.items():
        for a in (p["before"], p["possible"]):
            if sha((ROOT / a).read_bytes()) != legacy[a]["sha256"]:
                sys.exit("REFUSED: %s differs from the register -- nothing written" % a)
        for a, v in outputs(disc, p).items():
            files[a] = v + (disc, p)
    if CHECK:
        for a, (data, *_r) in files.items():
            f = ROOT / a
            if not f.exists() or a not in have or have[a]["sha256"] != sha(f.read_bytes()) or sha(f.read_bytes()) != sha(data):
                bad.append(a)
        print("RELEASE 5 HERO PAIRS · " + ("OK (%d files, reproducible)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for a, (data, encoder, src, method, role, disc, p) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        x, y, w, h = p["crop"]
        if method == "crop":
            desc = ("Before/Possible pair preparation for the %s hero slider (Governance 2.0, Rule 3): the BEFORE cropped to "
                    "the frame it shares with the aligned POSSIBLE. Pixels unchanged." % p["name"])
            op = "Crop x %d-%d, y %d-%d of the source (no resampling)." % (x, x + w, y, y + h)
        else:
            desc = ("Before/Possible pair preparation for the %s hero slider (Governance 2.0, Rule 3): the POSSIBLE mapped onto "
                    "the BEFORE's framing and cropped to the shared frame, so the two pictures align. Nothing painted, masked or generated." % p["name"])
            op = ("Homography %s (measured with SIFT + RANSAC on the static scene), Lanczos resampling, then crop x %d-%d, y %d-%d."
                  % (json.dumps(p["H"]), x, x + w, y, y + h))
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": legacy[src]["sha256"]}, "method": method,
             "edit": {"description": desc, "operation": op, "verified_by": "atlas-tools/build-release5-hero-pairs.py --check"},
             "encoder": encoder, "made": "2026-10-31",
             "content_credentials": {"source_file_embeds_c2pa": False, "derivative_embeds_c2pa": False,
                 "note": "The source carries no embedded credential. This file inherits the source's LEGACY_UNDECLARED state and declares nothing."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
        print("written", a, len(data))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
