#!/usr/bin/env python3
"""
PASS 2 · RELEASE 5 · hero slider pairs, routine pair preparation (Governance 2.0, Rule 3; founder approval
31 Oct 2026: "Prepare the aligned pair and implement the existing Before/Possible hero slider").

Each Discovery already shows both pictures; they are the same scene, framed slightly differently:

  Driveway Income (DISC-014)      BEFORE b5cbac3f (empty driveway)  POSSIBLE 4a4a1e4b (two cars parked)
  Your Home on Screen (DISC-021)  BEFORE ea3f24ee (the house)       POSSIBLE 80614bf6 (a small shoot)

SOURCES (31 Oct 2026 final review): where the founder holds the credentialed master of a picture, the hero is
made from the master, which is added unchanged and declared an AI illustration from its own Google C2PA
credential (Governance 2.0, Rule 2); the site's JPEG is a credential-stripped re-encoding of the same picture.
  DISC-014 BEFORE   assets/disc014/img/Driveway-Income-01-Before-MASTER.jpeg      (= b5cbac3f, credentialed)
  DISC-014 POSSIBLE assets/disc014/img/Driveway-Income-02-Possible-MASTER.jpeg    (= 4a4a1e4b, credentialed)
  DISC-021 BEFORE   assets/disc021/img/Your-Home-On-Screen-01-Before-MASTER.png   (= ea3f24ee, credentialed)
  DISC-021 POSSIBLE assets/img/80614bf6b2d7d79a.jpg  (its master on file carries no credential: stays legacy)

Operation, per pair (deterministic):
  0. DISC-021 only: the faint visible generator mark (a four-point sparkle at (1288, 649), present in both
     pictures) is removed exactly as on Above and Beyond (build-disc016-hero-final.py: star mask, reverse alpha
     blend, 3 px edge inpaint);
  1. the POSSIBLE is mapped onto the BEFORE's frame by a fixed homography (measured once with SIFT + RANSAC on
     the static scene and pinned below), Lanczos resampling;
  2. both pictures are cropped to the same rectangle, the largest one the mapped POSSIBLE fully covers at the
     source's aspect ratio. Nothing is painted or generated.
Outputs (assets/<disc>/img/): <ID>-HERO-{BEFORE,POSSIBLE}.jpg (quality 92) and -full.webp / -960.webp. Recorded
as derivatives bound to their unchanged sources; editing removes credentials, and the copies say so.

  python3 atlas-tools/build-release5-hero-pairs.py          build files + register records/derivatives
  python3 atlas-tools/build-release5-hero-pairs.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # clean_mark, read_c2pa (no side effects)

MASTERS = {   # path -> (sha256, the site JPEG it is the original of)
    "assets/disc014/img/Driveway-Income-01-Before-MASTER.jpeg": ("8cdc36598291f2949e370a84d3b4d4134a68fdffc82bf2100c5fabfa72253604", "b5cbac3fff9072d4.jpg"),
    "assets/disc014/img/Driveway-Income-02-Possible-MASTER.jpeg": ("76941f793c2c6b6b22080891c31dc49aaf9247024fd43cad711f0e09fb7c04ef", "4a4a1e4b08edaada.jpg"),
    "assets/disc021/img/Your-Home-On-Screen-01-Before-MASTER.png": ("87db40a77518a650eeefa058bc3f8c0b236e58d055147bc6830c78631a305a7c", "ea3f24eedab76294.jpg"),
}
PAIRS = {
    "DISC-014": dict(dir="assets/disc014/img", before="assets/disc014/img/Driveway-Income-01-Before-MASTER.jpeg",
                     possible="assets/disc014/img/Driveway-Income-02-Possible-MASTER.jpeg",
                     H=[[1.001139, 0.000441, -0.336122], [-0.000259, 1.018013, -48.002527], [0.0, 1e-06, 1.0]],
                     crop=(32, 0, 1343, 732), name="Driveway Income", mark=False),
    "DISC-021": dict(dir="assets/disc021/img", before="assets/disc021/img/Your-Home-On-Screen-01-Before-MASTER.png",
                     possible="assets/img/80614bf6b2d7d79a.jpg",
                     H=[[0.997415, -0.003423, 0.095865], [0.000492, 0.989823, 10.732516], [2e-06, -6e-06, 1.0]],
                     crop=(11, 12, 1385, 755), name="Your Home on Screen", mark=True),
}


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, **kw):
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def outputs(disc, p):
    A = cv2.imread(str(ROOT / p["before"])); B = cv2.imread(str(ROOT / p["possible"]))
    if p["mark"]:
        A, B = D16.clean_mark(A), D16.clean_mark(B)
    H = np.array(p["H"], dtype=np.float64)
    W = cv2.warpPerspective(B, H, (A.shape[1], A.shape[0]), flags=cv2.INTER_LANCZOS4)
    cov = cv2.warpPerspective(np.full(B.shape[:2], 255, np.uint8), H, (A.shape[1], A.shape[0]), flags=cv2.INTER_NEAREST)
    x, y, w, h = p["crop"]
    if not (cov[y:y + h, x:x + w] == 255).all():
        sys.exit("REFUSED: %s crop is not fully covered by the mapped POSSIBLE" % disc)
    out = {}
    for role, img, src in (("BEFORE", A, p["before"]), ("POSSIBLE", W, p["possible"])):
        method = "crop" if (role == "BEFORE" and not p["mark"]) else "pair-preparation"
        rgb = Image.fromarray(cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_BGR2RGB))
        base = "%s/%s-HERO-%s" % (p["dir"], disc, role)
        out[base + ".jpg"] = (enc(rgb, "JPEG", quality=92, progressive=True, optimize=True), "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION, src, method, role)
        out[base + "-full.webp"] = (enc(rgb, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, src, method, role)
        out[base + "-960.webp"] = (enc(rgb.resize((960, round(960 * h / w)), Image.LANCZOS), "WEBP", quality=80, method=6),
                                   "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION, src, method, role)
    return out


def src_sha(reg, a):
    for e in reg["records"] + reg["legacy_undeclared"]:
        if e["asset"] == a: return e["sha256"]
    return None


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    for a, (h, site) in MASTERS.items():
        if sha((ROOT / a).read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % a)
    legacy = {e["asset"]: e for e in reg["legacy_undeclared"]}
    if sha((ROOT / "assets/img/80614bf6b2d7d79a.jpg").read_bytes()) != legacy["assets/img/80614bf6b2d7d79a.jpg"]["sha256"]:
        sys.exit("REFUSED: 80614bf6 differs from the register")
    files = {}
    for disc, p in PAIRS.items():
        for a, v in outputs(disc, p).items():
            files[a] = v + (disc, p)
    have = {d["asset"]: d for d in reg["derivatives"]}
    if CHECK:
        recs = {r["asset"] for r in reg["records"]}
        bad = [m for m in MASTERS if m not in recs]
        for a, (data, *_r) in files.items():
            f = ROOT / a
            if not f.exists() or a not in have or have[a]["sha256"] != sha(f.read_bytes()) or sha(f.read_bytes()) != sha(data):
                bad.append(a)
        print("RELEASE 5 HERO PAIRS · " + ("OK (3 credentialed masters declared, %d files, reproducible)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for a, (h, site) in MASTERS.items():
        if a in {r["asset"] for r in reg["records"]}: continue
        ai, issuer, time, n, linked, state = D16.read_c2pa(ROOT / a)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        rd = (("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out.") if n == 0 else
              ("CREDENTIALED", "The credential records %d input image(s), each carrying its own signed credential." % n) if linked == n else
              ("UNCERTAIN", "The credential records %d input image(s), %d without any credential, title or hash: not identifiable from the file." % (n, n - linked)))
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / a).size), "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (hero master); the page shows its pair-prepared copy",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created by Google Generative AI with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Founder's master file, the same picture as assets/img/%s (whose bytes carry no credential)." % (issuer, time, n, linked, state, site),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE", "reference_disclosure": {"status": rd[0], "statement": rd[1]},
            "permitted_surfaces": ["discovery"], "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": "2026-10-31", "subject": "Founder's credentialed master, added for the Release 5 hero copies"}})
    for a, (data, encoder, src, method, role, disc, p) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        x, y, w, h = p["crop"]
        mark = " the faint visible generator mark removed (star mask at (1288, 649), as on Above and Beyond)," if p["mark"] else ""
        if role == "BEFORE":
            desc = "Before/Possible pair preparation for the %s hero slider (Governance 2.0, Rule 3):%s the BEFORE cropped to the frame it shares with the aligned POSSIBLE." % (p["name"], mark)
            op = "%sCrop x %d-%d, y %d-%d of the source (no resampling)." % ("Mark removal, then " if p["mark"] else "", x, x + w, y, y + h)
        else:
            desc = ("Before/Possible pair preparation for the %s hero slider (Governance 2.0, Rule 3):%s the POSSIBLE mapped onto the BEFORE's framing and "
                    "cropped to the shared frame, so the two pictures align. Nothing painted or generated." % (p["name"], mark))
            op = "%sHomography %s (SIFT + RANSAC on the static scene), Lanczos resampling, then crop x %d-%d, y %d-%d." % (
                "Mark removal, then " if p["mark"] else "", json.dumps(p["H"]), x, x + w, y, y + h)
        cred = src in MASTERS
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": src_sha(reg, src)}, "method": method,
             "edit": {"description": desc, "operation": op, "verified_by": "atlas-tools/build-release5-hero-pairs.py --check"},
             "encoder": encoder, "made": "2026-10-31",
             "content_credentials": {"source_file_embeds_c2pa": cred, "derivative_embeds_c2pa": False,
                 "note": ("Editing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."
                          if cred else "The source carries no embedded credential. This file inherits the source's LEGACY_UNDECLARED state and declares nothing.")}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
        print("written", a, len(data))
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
