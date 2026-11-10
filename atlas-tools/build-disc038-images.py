#!/usr/bin/env python3
"""DISC-038 · The Hidden Shelter: the hero pair and its web copies (Stage 4, 8 Nov 2026; branch dev/disc038-hidden-shelter,
private preview, NOT deployed).

SOURCES: the founder's ChatGPT pair, from Documents/PlotNua/Images/Discoveries/DISC-038-Hidden-Shelter/
DISC-038-Hidden-Shelter-Hero-Pair/ (the "DISC-038-Hidden-Shelter-Hero-Pair" package), added UNCHANGED under governed names and
declared AI_ILLUSTRATION from each file's own signed C2PA credential (Governance 2.0, Rule 2). Nothing is generated here.

  package file            governed master                        size          C2PA signed (OpenAI OpCo, LLC)
  DISC-038-BEFORE.png     DISC-038-01-BEFORE-MASTER.png          1536 x 1024   2026-11-08 20:17 UTC
  DISC-038-POSSIBLE.png   DISC-038-02-POSSIBLE-MASTER.png        1536 x 1024   2026-11-08 20:08 UTC

ROUTINE EDITS (Governance 2.0, Rule 3), the SAME for both views, each recorded as a derivative bound to its unchanged master:
  * hero copies: crop y 64-1024 (the full width), which removes faint generated lettering at y 30-56 over the tree canopy
    (x 365-465), then Lanczos resize of that 1536 x 960 frame to 768/1024/1376/1536 px WebP and 1024 px JPEG;
  * phone copies: the 4:5 window x 640-1459 at the full height (819 x 1024, no resize), centred on the shelter entrance;
    the lettering lies outside it;
  * the 1200 x 630 social card, from the POSSIBLE only: crop y 64-1024, resize to 1200 x 750, crop y 60-690.
No pixel is painted, retouched or inpainted; no content is added.

  python3 atlas-tools/build-disc038-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc038-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc038/img/"
DATE = "2026-11-08"
PKG = "DISC-038-Hidden-Shelter-Hero-Pair"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

TOP = 64            # first row kept in the hero copies (the lettering ends at y 56)
MX0, MW = 640, 819  # phone window
MASTERS = {   # role -> (path, sha256, package file, what)
    "BEFORE": (D + "DISC-038-01-BEFORE-MASTER.png",
               "205b4a5887b9fbdd92c406791bdf38206249f95e5da13a799b30952c400c8334", "DISC-038-BEFORE.png",
               "DISC-038 hero BEFORE: the back garden of a contemporary rendered Irish house at dusk, with lit glazed doors, a stone "
               "patio with a dining table, chairs and a lantern, potted hydrangeas, a broad lawn, lit planting of lavender, grasses and "
               "ferns with boulders, mature trees and a tall hedge, under a pink sunset sky"),
    "POSSIBLE": (D + "DISC-038-02-POSSIBLE-MASTER.png",
                 "b5b14231fc36a5a8163e9ccc43f10dda812870873ca297040638497932d76774", "DISC-038-POSSIBLE.png",
                 "DISC-038 hero POSSIBLE: the same garden with an engineered underground shelter entrance in the planting beside the "
                 "patio, its concrete-edged steel lid raised on struts, a lit concrete stair descending to a warmly lit room with a sofa, "
                 "shelves and a table; a generic illustrated entrance, no brand, product or mark visible"),
}


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt):
    b = io.BytesIO()
    if fmt == "webp":
        im.save(b, "WEBP", quality=82, method=6); return b.getvalue(), "Pillow %s, WebP quality 82, method 6" % PIL_VERSION
    im.save(b, "JPEG", quality=86, optimize=True, progressive=True); return b.getvalue(), "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION


def build():
    files = {}   # asset -> (bytes, encoder, role, operation)
    for role, (a, h, _pkg, _w) in MASTERS.items():
        src = Image.open(ROOT / a).convert("RGB")
        hero = src.crop((0, TOP, 1536, 1024))
        for w in (768, 1024, 1376, 1536):
            im = hero if w == 1536 else hero.resize((w, round(w * hero.height / hero.width)), Image.LANCZOS)
            op = "crop y %d-1024 (full width; removes the generated lettering at y 30-56)%s" % (TOP, ", no resize" if w == 1536 else ", Lanczos resize to %d px wide" % w)
            files[D + "DISC-038-%s-%d.webp" % (role, w)] = enc(im, "webp") + (role, op)
        files[D + "DISC-038-%s-1024.jpg" % role] = enc(hero.resize((1024, 640), Image.LANCZOS), "jpg") + (role, "crop y %d-1024 (full width; removes the generated lettering at y 30-56), Lanczos resize to 1024 px wide" % TOP)
        files[D + "DISC-038-%s-M-819.webp" % role] = enc(src.crop((MX0, 0, MX0 + MW, 1024)), "webp") + (role, "4:5 crop x %d-%d (the full height), no resize; the same window for both views" % (MX0, MX0 + MW))
        if role == "POSSIBLE":
            og = hero.resize((1200, 750), Image.LANCZOS).crop((0, 60, 1200, 690))
            files[D + "DISC-038-og-1200x630.jpg"] = enc(og, "jpg") + (role, "crop y %d-1024, Lanczos resize to 1200 x 750, crop y 60-690 to 1200 x 630 (social card from the hero POSSIBLE)" % TOP)
    return files


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    bad = []
    for role, (a, h, pkg, _w) in MASTERS.items():
        p = ROOT / a
        if not p.exists():
            if CHECK: bad.append("missing master " + a); continue
            sys.exit("REFUSED: %s is missing; copy the package file %s here unchanged first" % (a, pkg))
        if sha(p.read_bytes()) != h: bad.append("master changed: " + a)
    if bad: print("DISC-038 IMAGES · FAIL", bad); sys.exit(1)
    files = build()
    if CHECK:
        recs = {r["asset"]: r for r in reg["records"]}; ders = {d["asset"]: d for d in reg["derivatives"]}
        for role, (a, h, _p, _w) in MASTERS.items():
            if a not in recs or recs[a]["sha256"] != h: bad.append("no record " + a)
        for a, (data, *_r) in files.items():
            if not (ROOT / a).exists() or sha((ROOT / a).read_bytes()) != sha(data): bad.append("not reproducible " + a)
            if a not in ders or ders[a]["sha256"] != sha(data): bad.append("no derivative record " + a)
        print("DISC-038 IMAGES · " + ("OK (2 credentialed masters, %d derivatives, reproducible)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    recs = {r["asset"] for r in reg["records"]}
    for role, (a, h, pkg, what) in MASTERS.items():
        reg["records"] = [r for r in reg["records"] if r["asset"] != a]
        ai, issuer, time, n, linked, state = D16.read_c2pa(ROOT / a)
        if state != "Valid":
            import c2pa
            with c2pa.Reader(str(ROOT / a)) as r: vr = json.loads(r.json()).get("validation_results", {}).get("activeManifest", {})
            fails = sorted({f["code"] for f in vr.get("failure", [])}); oks = {f["code"] for f in vr.get("success", [])}
            if not set(fails) <= {"signingCredential.untrusted", "signingCredential.invalid"} or not {"claimSignature.validated", "assertion.dataHash.match"} <= oks:
                sys.exit("REFUSED: %s: the credential's claim signature or data hash does not verify (%s)" % (a, fails))
            state += (" (%s: the reader does not trust the signing certificate (not on its trust list; an extended key usage it requires is missing); "
                      "the claim signature and the data hash verify, so the file is unchanged since the issuer signed it)" % ", ".join(fails))
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": [1536, 1024], "class": "AI_ILLUSTRATION",
            "what": what + " (founder's master; the page shows its prepared copies)",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Supplied by the founder as '%s' in the package %s (8 Nov 2026), renamed unchanged." % (issuer, time, n, linked, state, pkg, PKG),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI (ChatGPT), per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": (
                "The credential records no input image. Signed nine minutes after the POSSIBLE, which suggests it was made from it, but that is not a verified masked edit. "
                "Measured against the POSSIBLE (8 Nov 2026): the house matches at 0 px offset and the patio and dining set agree closely; fine texture differs "
                "throughout, as in any regenerated image; the hedge, trees and sky differ in detail; the lawn, borders and planting in the middle and right of the "
                "garden differ substantially (open lawn and a curved border where the POSSIBLE has the entrance and its planting). The founder accepts these "
                "differences (Stage 4 brief, 8 Nov 2026: minor differences acceptable, pixel-perfect alignment not required)." if role == "BEFORE" else
                "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. Approved by the founder as the "
                "DISC-038 hero POSSIBLE (Stage 4 brief, 8 Nov 2026); its paired BEFORE was signed nine minutes later.")},
            "permitted_surfaces": ["discovery", "library-card"] if role == "POSSIBLE" else ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "founder_approval": "Approved by the founder as the DISC-038 hero %s for the standard Before/Possible slider (Stage 4 brief, 'founder-approved image direction', 8 Nov 2026); private preview only, production use awaits the founder's release approval" % role,
            "introduced": {"date": DATE, "subject": "DISC-038 The Hidden Shelter, Stage 4 hero integration (not deployed)"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = MASTERS[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": MASTERS[role][1]},
             "method": "crop",
             "edit": {"description": "DISC-038 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc038-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Cropping, resizing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-038 IMAGES · written: 2 masters, %d derivatives" % len(files))


if __name__ == "__main__":
    main()
