#!/usr/bin/env python3
"""
Garden Retreat (DISC-001) · hero slider BEFORE, warmed (Pass 2 Release 4, founder instruction 30 Oct 2026:
"Warm the Before image slightly so its colour temperature is closer to the golden-hour Possible image.
Do not substantially change the lighting, architecture, landscaping or sauna.")

Routine colour correction (Governance 2.0, Rule 3) of 45a270b7716e4a94.jpg for the hero slider only; the
source and its other use on the page are unchanged. One global white-balance shift applied identically to
every pixel, in linear light: red x1.05, green x1.00, blue x0.86, then back to sRGB. Nothing is masked,
moved, added or removed; brightness and contrast are otherwise unchanged. The sky's red/blue ratio moves
from 1.10 towards the Possible's 1.30 (about halfway), so the change is a warmer daylight, not golden hour.

  python3 atlas-tools/build-disc001-hero-before-warm.py          build files + register derivatives
  python3 atlas-tools/build-disc001-hero-before-warm.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, sys
import numpy as np
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
SRC = "assets/img/45a270b7716e4a94.jpg"
OUT = "assets/disc001/img/DISC-001-HERO-BEFORE-WARM"
GAINS = (1.05, 1.00, 0.86)
CHECK = "--check" in sys.argv
DESC = ("Colour correction for the Garden Retreat hero slider (founder instruction, 30 Oct 2026): the BEFORE warmed "
        "slightly towards the golden-hour POSSIBLE. One global white-balance shift, identical for every pixel; nothing "
        "masked, moved, added or removed.")
OPER = ("Linear-light channel gains R x1.05, G x1.00, B x0.86 (sRGB decode, gain, clip, sRGB encode). No local edit, "
        "no generative step; geometry identical to the source.")


def sha(b): return hashlib.sha256(b).hexdigest()


def warm(rgb8):
    x = rgb8.astype(np.float64) / 255.0
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    lin = np.clip(lin * np.array(GAINS), 0, 1)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return np.clip(np.round(s * 255), 0, 255).astype(np.uint8)


def enc(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    if sha((ROOT / SRC).read_bytes()) != legacy[SRC]["sha256"]:
        sys.exit("REFUSED: %s differs from the register -- nothing written" % SRC)
    im = Image.fromarray(warm(np.asarray(Image.open(ROOT / SRC).convert("RGB"))))
    files = {
        OUT + ".jpg": (enc(im, "JPEG", quality=92, progressive=True, optimize=True), "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION),
        OUT + "-1408.webp": (enc(im, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION),
        OUT + "-960.webp": (enc(im.resize((960, 524), Image.LANCZOS), "WEBP", quality=80, method=6),
                            "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION),
    }
    have = {x["asset"]: x for x in reg["derivatives"]}
    if CHECK:
        bad = [a for a, (data, _) in files.items()
               if not (ROOT / a).exists() or a not in have or have[a]["sha256"] != sha((ROOT / a).read_bytes())
               or sha((ROOT / a).read_bytes()) != sha(data)]
        print("DISC-001 HERO BEFORE WARM · " + ("OK (%d files, reproducible)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    (ROOT / OUT).parent.mkdir(parents=True, exist_ok=True)
    for a, (data, encoder) in files.items():
        (ROOT / a).write_bytes(data)
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": SRC, "sha256": legacy[SRC]["sha256"]}, "method": "colour-correction",
             "edit": {"description": DESC, "operation": OPER, "gains_linear_rgb": list(GAINS),
                      "verified_by": "atlas-tools/build-disc001-hero-before-warm.py --check"},
             "encoder": encoder, "made": "2026-10-30",
             "content_credentials": {"source_file_embeds_c2pa": False, "derivative_embeds_c2pa": False,
                 "note": "The source carries no embedded credential. This file inherits the source's LEGACY_UNDECLARED state and declares nothing."}}
        reg["derivatives"] = [x for x in reg["derivatives"] if x["asset"] != a] + [e]
        print("written", a, len(data))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
