#!/usr/bin/env python3
"""
POSSIBILITY REVEAL · HOMEPAGE IMAGE ENCODINGS (Phase 4, 19 Oct 2026)
===========================================================================
Makes the nine web encodings the homepage Reveal paints (3 widths x AVIF,
WebP, JPEG) from ONE locked master, and records exactly how.

  python3 atlas-tools/build-possibility-reveal-images.py --source PATH   build
  python3 atlas-tools/build-possibility-reveal-images.py --check          verify files against the record
  python3 atlas-tools/build-possibility-reveal-images.py --check --source PATH
                                                     verify, and re-encode to prove it is reproducible

THE SOURCE is the founder-locked L2A output `L1-plus-L2A.png` (Possibility
Reveal L2A LOCK RECORD, 18 Oct 2026), held outside the repository. It is
identified by its PIXEL sha256, because copies saved to the Mac carry an extra
metadata block and so differ in FILE hash (documented in the lock record).

WHAT AN ENCODING IS, AND IS NOT
  * The same picture at the same framing: a Lanczos resize to one of three
    widths, then a lossy encode. Never a crop, never an upscale, no editing.
  * Hash-bound: each file's sha256 and the source's pixel sha256 are recorded.
  * It carries NO provenance declaration and grants nothing. Whether these
    files may be published is decided by image-provenance-records.json and its
    guard (validate-image-provenance.js), not here.
"""
import hashlib, io, json, pathlib, sys
# Pillow/NumPy are needed only to build or to re-encode (--source). The plain
# --check runs without them (CI): every file is hash-bound to a record whose
# pixel sizes, aspect and fidelity were verified when it was built.
try:
    import numpy as np
    from PIL import Image, __version__ as PIL_VERSION, features
except ImportError:  # pragma: no cover
    np = Image = features = None; PIL_VERSION = "n/a"

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/possibility-reveal/img"
RECORD = OUT / "encodings.json"
SOURCE_NAME = "L1-plus-L2A.png (Possibility Reveal L2A LOCKED, 18 Oct 2026)"
SOURCE_PIXEL_SHA = "5dd29abea1a7cd9aba4f0b1db05a562a46d555f888a922f721a44e03ec0988a0"
SOURCE_SIZE = (2752, 1536)
WIDTHS = (1376, 2064, 2752)
FORMATS = {   # name: (Pillow format, save kwargs)
    "avif": ("AVIF", {"quality": 62, "speed": 4}),
    "webp": ("WEBP", {"quality": 80, "method": 6}),
    "jpg":  ("JPEG", {"quality": 84, "optimize": True, "progressive": True, "subsampling": 2}),
}
SSIM_FLOOR = 0.95
CHECK = "--check" in sys.argv
SRC = None
if "--source" in sys.argv:
    SRC = pathlib.Path(sys.argv[sys.argv.index("--source") + 1])


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(1)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def ssim(a, b):
    from skimage.metrics import structural_similarity
    return round(float(structural_similarity(np.asarray(a), np.asarray(b), channel_axis=2)), 4)


def encode_all(src_im):
    out = {}
    for w in WIDTHS:
        im = src_im if w == src_im.width else src_im.resize((w, round(src_im.height * w / src_im.width)), Image.LANCZOS)
        for ext, (fmt, kw) in FORMATS.items():
            buf = io.BytesIO(); im.save(buf, fmt, **kw); data = buf.getvalue()
            dec = Image.open(io.BytesIO(data)).convert("RGB")
            if dec.size != im.size: die("house-L1-L2A-%d.%s decoded at %s, expected %s" % (w, ext, dec.size, im.size))
            if b"jumdc2pa" in data: die("an encoding unexpectedly embeds C2PA data")
            out["house-L1-L2A-%d.%s" % (w, ext)] = (data, im.size, ssim(im, dec))
    return out


def load_source():
    if not SRC or not SRC.exists(): die("--source PATH to the locked L1-plus-L2A.png is required")
    im = Image.open(SRC); im.load(); im = im.convert("RGB")
    if im.size != SOURCE_SIZE: die("source is %s, expected %s" % (im.size, SOURCE_SIZE))
    if sha(np.asarray(im).tobytes()) != SOURCE_PIXEL_SHA: die("source pixels do not match the locked L2A output")
    return im


def main():
    if (SRC or not CHECK) and (features is None or not features.check("avif")):
        die("building or re-encoding needs Pillow with AVIF support")
    if CHECK:
        rec = json.loads(RECORD.read_text(encoding="utf-8"))
        bad = []
        names = sorted("house-L1-L2A-%d.%s" % (w, e) for w in WIDTHS for e in FORMATS)
        if sorted(rec["files"]) != names: bad.append("the record does not list exactly the nine encodings")
        for n in names:
            p = OUT / n
            if not p.exists(): bad.append(n + " missing"); continue
            data = p.read_bytes(); r = rec["files"].get(n, {})
            if sha(data) != r.get("sha256"): bad.append(n + " bytes differ from the record")
            px = r.get("pixels") or [0, 1]
            if abs(px[0] / px[1] - SOURCE_SIZE[0] / SOURCE_SIZE[1]) > 0.002: bad.append(n + " aspect ratio differs (crop)")
            if px[0] > SOURCE_SIZE[0]: bad.append(n + " wider than the source (upscale)")
            if b"jumdc2pa" in data: bad.append(n + " embeds a credential")
        extra = [p.name for p in OUT.iterdir() if p.is_file() and p.name not in names and p.name != RECORD.name]
        if extra: bad.append("unrecorded files in the folder: %s" % extra)
        if rec.get("source", {}).get("pixel_sha256") != SOURCE_PIXEL_SHA: bad.append("record names a different source")
        if SRC:
            fresh = encode_all(load_source())
            for n, (data, _, _) in fresh.items():
                if sha(data) != rec["files"][n]["sha256"]: bad.append(n + " does not re-encode bit-identically here")
        if bad: die("CHECK: " + "; ".join(bad))
        print("POSSIBILITY REVEAL IMAGES · CHECK OK — 9 encodings match the record%s"
              % (" and re-encode bit-identically from the locked source" if SRC else ""))
        return
    src = load_source()
    enc = encode_all(src)
    low = [n for n, (_, _, s) in enc.items() if s < SSIM_FLOOR]
    if low: die("fidelity below SSIM %.2f: %s" % (SSIM_FLOOR, low))
    OUT.mkdir(parents=True, exist_ok=True)
    rec = {
        "schema": "plotnua.possibility-reveal.encodings.v1",
        "what_this_is": "How the nine homepage Reveal images were made. Not a provenance declaration and not a permission: see image-provenance-records.json.",
        "source": {"name": SOURCE_NAME, "pixel_sha256": SOURCE_PIXEL_SHA, "pixels": list(SOURCE_SIZE),
                   "note": "Founder-locked composite: BEFORE master + L1 (Gemini edit, deterministic repair) + L2A (deterministic renderers). Held outside the repository; identified by pixel sha256 because Mac copies add a metadata block."},
        "method": "Pillow %s: RGB, Lanczos resize to the target width (no crop, no upscale), then encode." % PIL_VERSION,
        "encoders": {e: {"format": f, "params": kw} for e, (f, kw) in FORMATS.items()},
        "files": {n: {"sha256": sha(d), "bytes": len(d), "pixels": list(sz), "ssim_vs_source_at_same_size": s,
                      "embeds_c2pa": False} for n, (d, sz, s) in sorted(enc.items())},
    }
    for n, (d, _, _) in enc.items():
        (OUT / n).write_bytes(d)
    RECORD.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print("POSSIBILITY REVEAL IMAGES · built 9 encodings, %d KB in total"
          % (sum(len(d) for d, _, _ in enc.values()) // 1024))


if __name__ == "__main__":
    main()
