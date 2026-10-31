#!/usr/bin/env python3
"""
DISC-023 A Home for Art · hero slider pair (Pass 2 Release 6, founder approval 31 Oct 2026):
  BEFORE   the empty living-room wall   (site copy 5dc201be; master DISC-023-02-Potential-Asset.jpeg)
  POSSIBLE the same room with a landscape painting above the fireplace (site copy c0f5bfcd; master DISC-023-01-Hero.jpeg)

The founder's credentialed masters are added unchanged and declared AI illustrations from their own Google
C2PA credentials (Governance 2.0, Rule 2). The pair aligns at 0.22 px (one framing); nothing is warped or cropped.

BEFORE copy: PlotNua's own burned-in "PLOTNUA DISCOVERY / Potential Asset" label (two lines of text, an underline
and an arrow on the plain plaster wall) is removed (Rule 3, routine artefact removal of PlotNua's own image):
dark strokes found inside x 555-875, y 128-290 against the local median, plus the underline and arrow drawn as
fixed shapes, dilated 2 px, filled by OpenCV Telea inpainting (radius 6) from the surrounding plaster. Nothing
else changes (--check refuses any change outside x 555-875, y 128-290). POSSIBLE copy: WebP re-encodings only;
the master JPEG is the <img> fallback.

  python3 atlas-tools/build-disc023-hero-pair.py          build files + register records/derivatives
  python3 atlas-tools/build-disc023-hero-pair.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)
D = "assets/disc023/img/"
BEF = D + "A-Home-for-Art-01-Before-MASTER.jpeg"
POS = D + "A-Home-for-Art-02-Possible-MASTER.jpeg"
MASTERS = {BEF: ("f4aa42181044211221b1f89f6c1ec9708d55fe09c70e6a726697514a6182c178", "5dc201bef1868b84.jpg", "BEFORE"),
           POS: ("b8b0af40d9e6c64e936376b068865c0b105a5daa4112405d972f6856e6a1ed33", "c0f5bfcde033dea3.jpg", "POSSIBLE")}
BOX = (555, 128, 875, 290)


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def clean(A):
    x0, y0, x1, y1 = BOX
    g = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY)
    med = cv2.medianBlur(g, 31).astype(np.float32)
    m = np.zeros(g.shape, np.uint8)
    roi = g.astype(np.float32) < med - 10
    m[y0:y1, x0:x1] = roi[y0:y1, x0:x1].astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    cv2.line(m, (596, 199), (777, 199), 255, 5); cv2.line(m, (775, 199), (856, 276), 255, 6); cv2.circle(m, (852, 272), 11, 255, -1)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    m[:y0, :] = 0; m[y1:, :] = 0; m[:, :x0] = 0; m[:, x1:] = 0
    out = cv2.inpaint(A, m, 6, cv2.INPAINT_TELEA)
    return out, int((np.abs(out.astype(int) - A.astype(int)).max(2) > 0).sum())


def build():
    A = cv2.imread(str(ROOT / BEF))
    out, px = clean(A)
    d = np.abs(out.astype(int) - A.astype(int)).max(2); ys, xs = np.nonzero(d)
    x0, y0, x1, y1 = BOX
    if len(xs) and (xs.min() < x0 or ys.min() < y0 or xs.max() >= x1 or ys.max() >= y1): sys.exit("REFUSED: change outside the box")
    rgb = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    prgb = Image.open(ROOT / POS).convert("RGB")
    f = {}
    f[D + "DISC-023-HERO-BEFORE.jpg"] = (BEF, "artefact-removal", enc(rgb, "JPEG", quality=92, progressive=True, optimize=True), "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION)
    f[D + "DISC-023-HERO-BEFORE-1408.webp"] = (BEF, "artefact-removal", enc(rgb, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION)
    f[D + "DISC-023-HERO-BEFORE-960.webp"] = (BEF, "artefact-removal", enc(rgb, "WEBP", 960, quality=80, method=6), "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION)
    f[D + "DISC-023-HERO-POSSIBLE-1408.webp"] = (POS, "webp-reencode", enc(prgb, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION)
    f[D + "DISC-023-HERO-POSSIBLE-960.webp"] = (POS, "webp-resize", enc(prgb, "WEBP", 960, quality=80, method=6), "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION)
    return f, px


def main():
    for a, (h, _s2, _r) in MASTERS.items():
        if sha((ROOT / a).read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % a)
    files, px = build()
    reg = json.loads(REG.read_text(encoding="utf-8"))
    have = {d["asset"]: d for d in reg["derivatives"]}
    if CHECK:
        recs = {r["asset"] for r in reg["records"]}
        bad = [m for m in MASTERS if m not in recs]
        bad += [a for a, (_s3, _m, data, _e) in files.items() if a not in have or not (ROOT / a).exists()
                or sha((ROOT / a).read_bytes()) != have[a]["sha256"] or have[a]["sha256"] != sha(data)]
        print("DISC-023 HERO PAIR · " + ("OK (2 credentialed masters declared, %d files reproducible; edit confined to the box)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for a, (h, site, role) in MASTERS.items():
        if a in {r["asset"] for r in reg["records"]}: continue
        ai, issuer, time, n, linked, state = D16.read_c2pa(ROOT / a)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        rd = (("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out.") if n == 0 else
              ("CREDENTIALED", "The credential records %d input image(s), each carrying its own signed credential." % n) if linked == n else
              ("UNCERTAIN", "The credential records %d input image(s), %d without any credential, title or hash: not identifiable from the file." % (n, n - linked)))
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / a).size), "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (discovery-a-home-for-art.html), hero %s master" % role,
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created by Google Generative AI with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Founder's master file, the same picture as assets/img/%s (whose bytes carry no credential)." % (issuer, time, n, linked, state, site),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE", "reference_disclosure": {"status": rd[0], "statement": rd[1]},
            "permitted_surfaces": ["discovery"], "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": "2026-10-31", "subject": "Founder's credentialed DISC-023 master, added for the Release 6 hero"}})
    for a, (src, method, data, encoder) in files.items():
        (ROOT / a).parent.mkdir(parents=True, exist_ok=True); (ROOT / a).write_bytes(data)
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": MASTERS[src][0]}, "method": method}
        if method == "artefact-removal":
            e["edit"] = {"description": "Hero BEFORE for the A Home for Art slider (Governance 2.0, Rule 3): PlotNua's own burned-in 'PLOTNUA DISCOVERY / Potential Asset' label (text, underline and arrow) removed from the plaster wall. Nothing else changed.",
                         "operation": "Dark strokes inside x 555-875, y 128-290 (against a 31 px median) plus the underline and arrow as fixed shapes, dilated, filled by OpenCV Telea inpainting (radius 6) from the surrounding plaster; %d px. No generative fill." % px,
                         "box_xyxy": list(BOX), "verified_by": "atlas-tools/build-disc023-hero-pair.py --check"}
        e.update({"encoder": encoder, "made": "2026-10-31",
                  "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                      "note": "Editing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}})
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
        print("written", a, len(data))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
