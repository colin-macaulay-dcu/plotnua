#!/usr/bin/env python3
"""DISC-036 · Extend the House: hero web images and their provenance (founder hero authorisation, private preview
only, 5 Nov 2026; built on dev/disc036-extend-the-house, NOT deployed). Adapted from build-disc035-images.py.

SOURCES: the founder's two approved masters, added unchanged and declared AI_ILLUSTRATION from each file's
signed C2PA credential (Governance 2.0, Rule 2). Nothing is generated here.
  01 BEFORE    assets/disc036/img/DISC-036-01-BEFORE-MASTER.png    supplied in "PlotNua/17 Build" under ChatGPT's own
               filename a_high_resolution_realistic_photo_cg_style_exteri.png (identified by content and sha256,
               not by name; the brief's name DISC-036-Extend-the-House-BEFORE.png was not in the folder)
  02 POSSIBLE  assets/disc036/img/DISC-036-02-POSSIBLE-MASTER.png  DISC-036-Extend-the-House-POSSIBLE.png
Both are ChatGPT (OpenAI) outputs. Neither carries a visible generator mark, so no pixel is retouched.

THE PAIR WAS GENERATED SEPARATELY (signed 13:52:59 and 13:57:34 UTC, 5 Nov 2026). Measured on the masters before the
build (see the integration report): roofline, chimneys, upstairs windows, gable and the neighbouring house agree to a
median of about 2-3 px (dense optical flow 1.9-2.8 px median in those regions; edge-template landmarks 0-6 px), with
no scale or perspective drift. Nothing is warped or resampled to "fix" it. The BEFORE is 1672 px wide and the
POSSIBLE 1671 px: every web copy of BOTH is taken from the common 1671 x 941 frame. The BEFORE loses its LEFT-most
pixel column (x 1-1672), which measured marginally closer than the right (Rule 3 pair preparation).

ROUTINE EDITS (Governance 2.0, Rule 3), each recorded as a derivative bound to its unchanged master:
  * resizing (Lanczos) and encoding to WebP / JPEG;
  * the common-frame crop above, applied to the BEFORE;
  * the phone hero copies are a 4:5 crop of the full height at x 480-1233 (the glazed rear wall, the roof light and
    the dining table stay in view); both crops use the same window, so the pair stays aligned;
  * the Library card copies and the 1200 x 630 social card are taken from the POSSIBLE.

  python3 atlas-tools/build-disc036-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc036-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc036/img/"
DATE = "2026-11-05"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

MASTERS = {   # role -> (path, sha256, what)
    "BEFORE": (D + "DISC-036-01-BEFORE-MASTER.png", "34ab61ab82485a4f9f9e2e0c9c9bd5a8616b7f2ea39bb311c7b917ab0715c973",
               "DISC-036 hero BEFORE: the rear of a rendered two-storey semi-detached Irish house in evening sun, with a stone patio, "
               "a dining table, potted plants, a lawn, timber fences and a side garden on the left with a gate"),
    "POSSIBLE": (D + "DISC-036-02-POSSIBLE-MASTER.png", "258395fb357c21641e4a9f08fe1517b0f146cadb06315446cbf458ea8f92b769",
                 "DISC-036 hero POSSIBLE: the same house with a contemporary single-storey wrap-around extension across the back and "
                 "down the side garden: an asymmetric glazed roof, charcoal framing, vertical timber cladding and floor-to-ceiling "
                 "glazing onto an open-plan kitchen, dining and living room"),
}
CHAPTERS = {}   # DISC-036 has no chapter images: the chapter drawings are PlotNua vectors
CARD = (480, 768, 1024)
MOBILE_X0, MOBILE_W = 480, 753        # 4:5 phone crop of the 941 px height: glazed rear wall, roof light, dining table in view
COMMON = (1671, 941)                  # the pair's common frame (BEFORE 1672 wide, POSSIBLE 1671)
LEFT = {"BEFORE": 1, "POSSIBLE": 0}   # the BEFORE drops its left-most column (measured closer than the right)
DESK = (768, 1024, 1376, 1671)


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
    for role, (p, h, what) in CHAPTERS.items():
        f = ROOT / p
        if not f.exists() or sha(f.read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
        if Image.open(f).size != (1536, 1024): sys.exit("REFUSED: %s is not 1536 x 1024" % p)
        out[role] = (p, h, what)
    a, b = (Image.open(ROOT / out[r][0]).size for r in ("BEFORE", "POSSIBLE"))
    if a != (1672, 941) or b != COMMON: sys.exit("REFUSED: the hero pair is not the measured 1672/1671 x 941 pair (%s vs %s)" % (a, b))
    return out


def outputs(masters):
    files = {}
    for role in CHAPTERS:
        rgb = Image.open(ROOT / masters[role][0]).convert("RGB")
        stem = D + "DISC-036-%s" % role
        for w in CARD:
            op = "Lanczos resize to %d px wide (chapter card, whole image, 3:2 kept)" % w
            files["%s-%d.webp" % (stem, w)] = (enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role, op)
            files["%s-%d.jpg" % (stem, w)] = (enc(rgb, "JPEG", w, quality=86, progressive=True, optimize=True), "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role, op)
    for role, (p, h, what) in masters.items():
        if role in CHAPTERS: continue
        full = Image.open(ROOT / p).convert("RGB")
        x0 = LEFT[role]
        rgb = full.crop((x0, 0, x0 + COMMON[0], COMMON[1]))          # the pair's common frame
        frame = "" if full.size == COMMON else "crop to the pair's common frame x %d-%d, then " % (x0, x0 + COMMON[0])
        W, H = rgb.size
        stem = D + "DISC-036-%s" % role
        for w in DESK:
            files["%s-%d.webp" % (stem, w)] = (enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                                               frame + ("Lanczos resize to %d px wide" % w if w != W else "no resize"))
        files["%s-1024.jpg" % stem] = (enc(rgb, "JPEG", 1024, quality=88, progressive=True, optimize=True),
                                       "Pillow %s, JPEG quality 88, progressive" % PIL_VERSION, role, frame + "Lanczos resize to 1024 px wide")
        m = rgb.crop((MOBILE_X0, 0, MOBILE_X0 + MOBILE_W, H))
        op = "4:5 crop x %d-%d (the full height), no resize" % (MOBILE_X0, MOBILE_X0 + MOBILE_W)   # inside the common frame
        files["%s-M-%d.webp" % (stem, MOBILE_W)] = (enc(m, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role, op)
        files["%s-M-%d.jpg" % (stem, MOBILE_W)] = (enc(m, "JPEG", quality=86, progressive=True, optimize=True), "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role, op)
        if role == "POSSIBLE":
            # Discovery Library card copies, named as build-library-card-webp.py names them for this source,
            # so that builder reuses them (it never re-encodes a recorded file)
            for w in (480, 960):
                files["assets/library/img/DISC-036-02-POSSIBLE-MASTER-%dw.webp" % w] = (
                    enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                    frame + "Lanczos resize to %d px wide (Discovery Library card)" % w)
            ch = round(W * 630 / 1200); y0 = (H - ch) // 2
            og = rgb.crop((0, y0, W, y0 + ch)).resize((1200, 630), Image.LANCZOS)
            files[D + "DISC-036-og-1200x630.jpg"] = (enc(og, "JPEG", quality=86, progressive=True, optimize=True),
                                                    "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role,
                                                    frame + "crop y %d-%d to 1200:630, Lanczos resize to 1200 x 630" % (y0, y0 + ch))
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
                 if str(p.relative_to(ROOT)) not in files and str(p.relative_to(ROOT)) not in {m[0] for m in list(MASTERS.values()) + list(CHAPTERS.values())}]
        print("DISC-036 IMAGES · " + ("OK (%d credentialed masters declared, %d derivatives, reproducible)" % (len(masters), len(files))
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
        chapter = role in CHAPTERS
        rd = ("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. "
              "A chapter image, generated on its own (signed %s); it is not part of a Before/Possible pair." % (time or "")) if chapter else ("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. "
              "The founder states the two were generated separately; the POSSIBLE was signed after the BEFORE (13:57:34 vs 13:52:59 UTC, "
              "5 Nov 2026). The house, roof, chimneys, upstairs windows and neighbouring house agree to a median of about 2-3 px, measured before the build.")
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
            "founder_approval": ("(not used)" if chapter
                                 else "Approved by the founder as the DISC-036 hero pair (final hero integration brief, private preview only, 5 Nov 2026)"),
            "introduced": {"date": DATE, "subject": "DISC-036 Extend the House, founder hero integration authorisation (private preview only)"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = masters[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": masters[role][1]},
             "method": "crop" if " crop " in " " + op else "optimise",
             "edit": {"description": "DISC-036 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc036-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Resizing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-036 IMAGES · written: %d masters, %d derivatives" % (len(masters), len(files)))


if __name__ == "__main__":
    main()
