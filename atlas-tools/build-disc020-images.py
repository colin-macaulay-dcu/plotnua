#!/usr/bin/env python3
"""DISC-020 · Stay in the House You Love: web images and their provenance (founder Phase 2 build
authorisation, 4 Nov 2026; built on dev/disc020-stay-in-the-house, NOT deployed).

SOURCES: the founder's two approved masters, added unchanged and declared AI_ILLUSTRATION from each file's
signed C2PA credential (Governance 2.0, Rule 2). Nothing is generated here.
  01 BEFORE    assets/disc020/img/DISC-020-01-BEFORE-MASTER.png    the living room without a lift
               (founder file "Stay-in-the-House-You-Love-02-Reveal.png", saved 4 Nov 2026 15:22 under an older
               filename by accident; identified by content and sha256, never by that filename)
  02 POSSIBLE  assets/disc020/img/DISC-020-02-POSSIBLE-MASTER.png  the same room with a bronze-framed residential lift
               (founder file "a_realistic_high_resolution_interior_living_room.png")
Both are ChatGPT (OpenAI) outputs. Neither carries a visible generator mark, so no pixel is retouched.

ROUTINE EDITS (Governance 2.0, Rule 3), each recorded as a derivative bound to its unchanged master:
  * resizing (Lanczos) and encoding to WebP / JPEG;
  * the phone hero copies are a 4:5 crop of the full height at x 480-1230 (Phase 2B; was 450-1200): the stair through the doorway
    (x ~500-690) and the whole lift with its ceiling bulkhead (x 895-1186) stay in view, the lift 44 px clear of the edge; both crops use the same window, so the pair
    stays aligned to the pixel;
  * the Library card copies and the 1200 x 630 social card are taken from the POSSIBLE.

  python3 atlas-tools/build-disc020-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc020-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc020/img/"
DATE = "2026-11-04"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

MASTERS = {   # role -> (path, sha256, what)
    "BEFORE": (D + "DISC-020-01-BEFORE-MASTER.png", "084810b37ee43baabfe483f515f6a1d912621ab85c4f178db4913ea239f6abfb",
               "DISC-020 hero BEFORE: a warm contemporary Irish living room (armchair, sofa, bookcase, landscape prints) "
               "with a doorway to the hall and staircase; no lift. Founder file saved by accident as "
               "Stay-in-the-House-You-Love-02-Reveal.png, identified by content and sha256"),
    "POSSIBLE": (D + "DISC-020-02-POSSIBLE-MASTER.png", "6057a461ba5dfdea6fadaa2653500a46cbca60b96b4fcd84bb7874daca4d8814",
                 "DISC-020 hero POSSIBLE: the same living room with a glazed residential lift in slim bronze framing "
                 "standing against the back wall and rising through the ceiling"),
}
MOBILE_X0, MOBILE_W = 480, 750        # 4:5 phone crop of the 937 px height: stair and lift both in view, lift clear of the edge (Phase 2B)
DESK = (768, 1024, 1376, 1678)


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def available():
    out = {}
    for role, (p, h, what) in MASTERS.items():
        f = ROOT / p
        if not f.exists() or sha(f.read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
        out[role] = (p, h, what)
    a, b = (Image.open(ROOT / out[r][0]).size for r in ("BEFORE", "POSSIBLE"))
    if a != b: sys.exit("REFUSED: the hero pair does not share one geometry (%s vs %s)" % (a, b))
    return out


def outputs(masters):
    files = {}
    for role, (p, h, what) in masters.items():
        rgb = Image.open(ROOT / p).convert("RGB")
        W, H = rgb.size
        stem = D + "DISC-020-%s" % role
        for w in DESK:
            files["%s-%d.webp" % (stem, w)] = (enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                                               "Lanczos resize to %d px wide" % w if w != W else "no resize")
        files["%s-1024.jpg" % stem] = (enc(rgb, "JPEG", 1024, quality=88, progressive=True, optimize=True),
                                       "Pillow %s, JPEG quality 88, progressive" % PIL_VERSION, role, "Lanczos resize to 1024 px wide")
        m = rgb.crop((MOBILE_X0, 0, MOBILE_X0 + MOBILE_W, H))
        op = "4:5 crop x %d-%d (the full height), no resize" % (MOBILE_X0, MOBILE_X0 + MOBILE_W)
        files["%s-M-%d.webp" % (stem, MOBILE_W)] = (enc(m, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role, op)
        files["%s-M-%d.jpg" % (stem, MOBILE_W)] = (enc(m, "JPEG", quality=86, progressive=True, optimize=True), "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role, op)
        if role == "POSSIBLE":
            # Discovery Library card copies, named as build-library-card-webp.py names them for this source,
            # so that builder reuses them (it never re-encodes a recorded file)
            for w in (480, 960):
                files["assets/library/img/DISC-020-02-POSSIBLE-MASTER-%dw.webp" % w] = (
                    enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                    "Lanczos resize to %d px wide (Discovery Library card)" % w)
            ch = round(W * 630 / 1200); y0 = (H - ch) // 2
            og = rgb.crop((0, y0, W, y0 + ch)).resize((1200, 630), Image.LANCZOS)
            files[D + "DISC-020-og-1200x630.jpg"] = (enc(og, "JPEG", quality=86, progressive=True, optimize=True),
                                                    "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role,
                                                    "crop y %d-%d to 1200:630, Lanczos resize to 1200 x 630" % (y0, y0 + ch))
    return files


def main():
    masters = available()
    reg = json.loads(REG.read_text(encoding="utf-8"))
    files = outputs(masters)
    have = {d["asset"]: d for d in reg["derivatives"]}
    recs = {r["asset"] for r in reg["records"]}
    if CHECK:
        bad = [m[0] for m in masters.values() if m[0] not in recs]
        for a, (data, *_r) in files.items():
            f = ROOT / a
            if not f.exists() or a not in have or have[a]["sha256"] != sha(f.read_bytes()) or sha(f.read_bytes()) != sha(data):
                bad.append(a)
        stray = [str(p.relative_to(ROOT)) for p in (ROOT / D).iterdir()
                 if str(p.relative_to(ROOT)) not in files and str(p.relative_to(ROOT)) not in {m[0] for m in MASTERS.values()}]
        print("DISC-020 IMAGES · " + ("OK (%d credentialed masters declared, %d derivatives, reproducible)" % (len(masters), len(files))
                                      if not bad and not stray else "FAIL %s %s" % (bad, stray)))
        sys.exit(1 if bad or stray else 0)
    for role, (a, h, what) in masters.items():
        if a in recs: continue
        ai, issuer, time, n, linked, state = D16.read_c2pa(ROOT / a)
        if state != "Valid":
            import c2pa
            with c2pa.Reader(str(ROOT / a)) as r: vr = json.loads(r.json()).get("validation_results", {}).get("activeManifest", {})
            fails = sorted({f["code"] for f in vr.get("failure", [])}); oks = {f["code"] for f in vr.get("success", [])}
            if not set(fails) <= {"signingCredential.untrusted", "signingCredential.invalid"} or not {"claimSignature.validated", "assertion.dataHash.match"} <= oks:
                sys.exit("REFUSED: %s: the credential's claim signature or data hash does not verify (%s)" % (a, fails))
            state += (" (%s: the reader does not trust the signing certificate (not on its trust list; an extended key usage it requires is missing); the claim signature and the data hash "
                      "verify, so the file is unchanged since the issuer signed it)" % ", ".join(fails))
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        rd = ("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. "
              "The BEFORE was signed after the POSSIBLE (15:17 vs 15:12 UTC, 4 Nov 2026) and its source filename suggests it was "
              "made from the same scene; that relationship is not asserted.")
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / a).size), "class": "AI_ILLUSTRATION",
            "what": what + " (founder's master; the page shows its prepared copies)",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s." % (issuer, time, n, linked, state),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI (ChatGPT), per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE", "reference_disclosure": {"status": rd[0], "statement": rd[1]},
            "permitted_surfaces": ["discovery", "library-card"] if role == "POSSIBLE" else ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "founder_approval": "Approved by the founder as the DISC-020 hero pair (Phase 2 instruction, 4 Nov 2026)",
            "introduced": {"date": DATE, "subject": "DISC-020 Stay in the House You Love, founder Phase 2 build authorisation"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = masters[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": masters[role][1]},
             "method": "crop" if " crop " in " " + op else "optimise",
             "edit": {"description": "DISC-020 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc020-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Resizing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-020 IMAGES · written: %d masters, %d derivatives" % (len(masters), len(files)))


if __name__ == "__main__":
    main()
