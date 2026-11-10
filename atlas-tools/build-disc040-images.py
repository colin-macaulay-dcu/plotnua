#!/usr/bin/env python3
"""DISC-040 · The Home You Build: the hero pair and its web copies (Stage 2, 10 Nov 2026; branch dev/disc040-the-home-you-build,
private preview, NOT deployed).

SOURCES: the founder's ChatGPT pair, from Documents/PlotNua/Images/Discoveries/"DISC - 039 Self Build"/
DISC-040-Final-Photoreal-Hero-Pair.zip (the folder name says 039; the Discovery is DISC-040, the founder confirmed). Added
UNCHANGED under governed names and declared AI_ILLUSTRATION from each file's own signed C2PA credential (Governance 2.0,
Rule 2). Nothing is generated here.

  package file            governed master                        size         C2PA signed (OpenAI OpCo, LLC)
  DISC-040-BEFORE.png     DISC-040-01-BEFORE-MASTER.png          1670 x 941   2026-11-10 18:03:33 UTC
  DISC-040-POSSIBLE.png   DISC-040-02-POSSIBLE-MASTER.png        1670 x 941   2026-11-10 18:03:37 UTC

ROUTINE EDITS (Governance 2.0, Rule 3), the SAME for both views, each recorded as a derivative bound to its unchanged master:
  * hero copies: the full frame, Lanczos resize to 768/1024/1376/1536 px WebP and 1024 px JPEG (aspect kept, no upscaling);
  * phone copies: the 4:5 window x 820-1573 at the full height (753 x 941, no resize), on the gable and the field gate;
  * the 1200 x 630 social card, from the POSSIBLE only: resize to 1200 x 676, crop y 23-653.
No pixel is painted, retouched or inpainted; no content is added.

  python3 atlas-tools/build-disc040-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc040-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc040/img/"
DATE = "2026-11-10"
PKG = "DISC-040-Final-Photoreal-Hero-Pair.zip"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

MX0, MW, H = 820, 753, 941   # phone window
MASTERS = {   # role -> (path, sha256, package file, what)
    "BEFORE": (D + "DISC-040-01-BEFORE-MASTER.png",
               "e8e14bf07e30c01794a6fb99db3c0c5f0ee30722ac4b02cf1200f3ec3ce78d2e", "DISC-040-BEFORE.png",
               "DISC-040 hero BEFORE: an undeveloped green field in rural Ireland under an overcast sky, seen from a country road, behind a "
               "mossy dry-stone wall with a galvanised five-bar field gate between stone piers; a large tree at left, hedgerows and rolling "
               "hills beyond; no building"),
    "POSSIBLE": (D + "DISC-040-02-POSSIBLE-MASTER.png",
                 "f96e17aa66ea2291f2c24d3137e8e3375d62b2a255a5473174d7b6925552df17", "DISC-040-POSSIBLE.png",
                 "DISC-040 hero POSSIBLE: the same view with a contemporary single-storey self-built home on the field: stone and "
                 "timber-clad walls, a dark slate roof with rooflights and a flue, a fully glazed gable, a gravel drive behind the gate, "
                 "a lawn and planting; a generic illustrated house, no brand, product or mark visible"),
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
        W0, H0 = src.size
        for w in (768, 1024, 1376, 1536):
            im = src.resize((w, round(w * H0 / W0)), Image.LANCZOS)
            op = "full frame, Lanczos resize to %d px wide (aspect kept)" % w
            files[D + "DISC-040-%s-%d.webp" % (role, w)] = enc(im, "webp") + (role, op)
        files[D + "DISC-040-%s-1024.jpg" % role] = enc(src.resize((1024, round(1024 * H0 / W0)), Image.LANCZOS), "jpg") + (role, "full frame, Lanczos resize to 1024 px wide (aspect kept)")
        files[D + "DISC-040-%s-M-753.webp" % role] = enc(src.crop((MX0, 0, MX0 + MW, H)), "webp") + (role, "4:5 crop x %d-%d (the full height), no resize; the same window for both views" % (MX0, MX0 + MW))
        if role == "POSSIBLE":
            og = src.resize((1200, 676), Image.LANCZOS).crop((0, 23, 1200, 653))
            files[D + "DISC-040-og-1200x630.jpg"] = enc(og, "jpg") + (role, "Lanczos resize to 1200 x 676, crop y 23-653 to 1200 x 630 (social card from the hero POSSIBLE)")
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
    if bad: print("DISC-040 IMAGES · FAIL", bad); sys.exit(1)
    files = build()
    if CHECK:
        recs = {r["asset"]: r for r in reg["records"]}; ders = {d["asset"]: d for d in reg["derivatives"]}
        for role, (a, h, _p, _w) in MASTERS.items():
            if a not in recs or recs[a]["sha256"] != h: bad.append("no record " + a)
        for a, (data, *_r) in files.items():
            if not (ROOT / a).exists() or sha((ROOT / a).read_bytes()) != sha(data): bad.append("not reproducible " + a)
            if a not in ders or ders[a]["sha256"] != sha(data): bad.append("no derivative record " + a)
        print("DISC-040 IMAGES · " + ("OK (2 credentialed masters, %d derivatives, reproducible)" % len(files) if not bad else "FAIL %s" % bad))
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
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / a).size), "class": "AI_ILLUSTRATION",
            "what": what + " (founder's master; the page shows its prepared copies)",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Supplied by the founder as '%s' in the package %s (10 Nov 2026, folder 'DISC - 039 Self Build'), renamed unchanged." % (issuer, time, n, linked, state, pkg, PKG),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI (ChatGPT), per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": (
                "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. "
                "Signed about four seconds before the POSSIBLE. Compared with the POSSIBLE (10 Nov 2026): the same road, wall, gate, left-hand tree and hills "
                "at a closely similar viewpoint; the wall line sits about 20 px higher and fine detail differs throughout, as in any regenerated image. The "
                "founder accepts minor differences (Stage 2 brief, 10 Nov 2026)." if role == "BEFORE" else
                "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. Approved by the founder "
                "as the DISC-040 hero POSSIBLE (Stage 2 brief, 10 Nov 2026); its paired BEFORE was signed about four seconds earlier.")},
            "permitted_surfaces": ["discovery", "library-card"] if role == "POSSIBLE" else ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "founder_approval": "Approved by the founder as the DISC-040 hero %s for the standard Before/Possible slider (Stage 2 brief, 10 Nov 2026: 'Approved working hero images. Proceed with integration.'); generated with ChatGPT image generation, as the founder states and the credential confirms; private preview only, production use awaits the founder's release approval" % role,
            "introduced": {"date": DATE, "subject": "DISC-040 The Home You Build, Stage 2 hero integration (not deployed)"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = MASTERS[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": MASTERS[role][1]},
             "method": "crop",
             "edit": {"description": "DISC-040 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc040-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Cropping, resizing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-040 IMAGES · written: 2 masters, %d derivatives" % len(files))


if __name__ == "__main__":
    main()
