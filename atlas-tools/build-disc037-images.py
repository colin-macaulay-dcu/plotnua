#!/usr/bin/env python3
"""DISC-037 · The Resourceful Garden: web images and their provenance (Stage 3 private preview, 8 Nov 2026;
built on dev/disc037-resourceful-garden, NOT deployed, production release NOT authorised).

SOURCES: the founder's four chapter images from the package "DISC-037-Resourceful-Garden-Chapter-Images"
(Images/Discoveries/DISC-037 — The Resourceful Garden/), added UNCHANGED under governed names and declared
AI_ILLUSTRATION from each file's signed C2PA credential (Governance 2.0, Rule 2). Nothing is generated here.

  package file                              governed master                                     size
  01-Garden-That-Feeds-You.png              DISC-037-03-GARDEN-THAT-FEEDS-YOU-MASTER.png        1672 x 941
  02-Underground-Pantry.png                 DISC-037-04-UNDERGROUND-PANTRY-MASTER.png           1672 x 941
  03-Waste-Into-Something-Wonderful.png     DISC-037-05-WASTE-INTO-WONDERFUL-MASTER.png         1536 x 1024
  05-Living-Roof-and-Wild-Garden.png        DISC-037-07-LIVING-ROOF-WILD-GARDEN-MASTER.png      1536 x 1024

MISSING, NOT SUBSTITUTED (founder's package README): chapter 04, The Greenhouse That Stores Sunshine
(DISC-037-06-...). The hero pair (DISC-037-01-BEFORE / 02-POSSIBLE) has not been supplied either. The page
shows labelled empty slots for all three; this builder refuses nothing for their absence and invents nothing.

ROUTINE EDITS (Governance 2.0, Rule 3), each recorded as a derivative bound to its unchanged master:
  * resizing (Lanczos) of the WHOLE image, aspect kept, to 480/768/1024/1376 px WebP and 768/1024 px JPEG;
  * the 1200 x 630 social card: a centred crop of chapter 01 (PROVISIONAL, to be replaced by the hero POSSIBLE).

  python3 atlas-tools/build-disc037-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc037-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc037/img/"
DATE = "2026-11-08"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

CHAPTERS = {   # role -> (path, sha256, size, package file, what)
    "03-GARDEN-THAT-FEEDS-YOU": (D + "DISC-037-03-GARDEN-THAT-FEEDS-YOU-MASTER.png",
        "ad0dccabf61fad8940955c6249dbbc2ead8c7a54b497195765d0fbce2701cd07", (1672, 941), "01-Garden-That-Feeds-You.png",
        "DISC-037 chapter 01 image, The Garden That Feeds You: timber raised beds of kale, lettuce, chard and herbs with gravel paths, "
        "foxgloves and a fruit tree in the foreground, a polytunnel behind and rolling farmland beyond"),
    "04-UNDERGROUND-PANTRY": (D + "DISC-037-04-UNDERGROUND-PANTRY-MASTER.png",
        "d949f6c6c620f8ca88b6a9f7ad5753a9438701a0a57db16dde4c0ffd7342a640", (1672, 941), "02-Underground-Pantry.png",
        "DISC-037 chapter 02 image, The Underground Pantry: a grass-covered mound in a planted garden with its curved hatch open on "
        "shelves of jars and crates, reached by stepping stones; a generic illustrated store, no brand or mark visible"),
    "05-WASTE-INTO-WONDERFUL": (D + "DISC-037-05-WASTE-INTO-WONDERFUL-MASTER.png",
        "dfbbf9fc07383dd64a9e673a15b725d8210bb680339fef6090aa6563c2fbbf7b", (1536, 1024), "03-Waste-Into-Something-Wonderful.png",
        "DISC-037 chapter 03 image, Waste Into Something Wonderful: slatted timber compost bays, a dark plastic compost bin, a green "
        "stacking bin and a tub of peelings on a gravel path among planting; no brand or mark legible"),
    "07-LIVING-ROOF-WILD-GARDEN": (D + "DISC-037-07-LIVING-ROOF-WILD-GARDEN-MASTER.png",
        "4b21a577cf252084dc3c7d73ce96067622c0ff58214e7ba2d3cf535f702c212e", (1536, 1024), "05-Living-Roof-and-Wild-Garden.png",
        "DISC-037 chapter 05 image, The Living Roof and Wild Garden: a timber garden building with a flowering sedum and wildflower "
        "roof, foxgloves, ferns and daisies in front and a dry-stone wall at the side"),
}
WEBP = (480, 768, 1024, 1376)
JPEG = (768, 1024)
OG_FROM = "03-GARDEN-THAT-FEEDS-YOU"


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def available():
    for role, (p, h, size, *_r) in CHAPTERS.items():
        f = ROOT / p
        if not f.exists() or sha(f.read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
        if Image.open(f).size != size: sys.exit("REFUSED: %s is not %d x %d" % ((p,) + size))
    return CHAPTERS


def outputs():
    files = {}
    for role, (p, h, size, *_r) in CHAPTERS.items():
        rgb = Image.open(ROOT / p).convert("RGB")
        stem = D + "DISC-037-%s" % role
        for w in WEBP:
            op = "Lanczos resize to %d px wide (whole image, aspect kept)" % w
            files["%s-%d.webp" % (stem, w)] = (enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role, op)
        for w in JPEG:
            op = "Lanczos resize to %d px wide (whole image, aspect kept)" % w
            files["%s-%d.jpg" % (stem, w)] = (enc(rgb, "JPEG", w, quality=86, progressive=True, optimize=True), "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role, op)
        if role == OG_FROM:
            W, H = rgb.size; ch = round(W * 630 / 1200); y0 = (H - ch) // 2
            og = rgb.crop((0, y0, W, y0 + ch)).resize((1200, 630), Image.LANCZOS)
            files[D + "DISC-037-og-1200x630.jpg"] = (enc(og, "JPEG", quality=86, progressive=True, optimize=True),
                "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role,
                "crop y %d-%d to 1200:630, Lanczos resize to 1200 x 630 (provisional social card until the hero POSSIBLE is supplied)" % (y0, y0 + ch))
    return files


def main():
    masters = available()
    reg = json.loads(REG.read_text(encoding="utf-8"))
    files = outputs()
    have = {d["asset"]: d for d in reg["derivatives"]}
    recs = {r["asset"] for r in reg["records"]}
    if CHECK:
        bad = [m[0] for m in masters.values() if m[0] not in recs]
        for a, (data, *_r) in files.items():
            f = ROOT / a
            if not f.exists() or a not in have or have[a]["sha256"] != sha(f.read_bytes()) or sha(f.read_bytes()) != sha(data):
                bad.append(a)
        known = set(files) | {m[0] for m in masters.values()}
        stray = [str(q.relative_to(ROOT)) for q in (ROOT / D).iterdir() if str(q.relative_to(ROOT)) not in known]
        print("DISC-037 IMAGES · " + ("OK (%d credentialed masters declared, %d derivatives, reproducible)" % (len(masters), len(files))
                                      if not bad and not stray else "FAIL %s %s" % (bad, stray)))
        sys.exit(1 if bad or stray else 0)
    for role, (a, h, size, pkg, what) in masters.items():
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
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(size), "class": "AI_ILLUSTRATION",
            "what": what + " (founder's master; the page shows its prepared copies)",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Supplied by the founder as '%s' in the package DISC-037-Resourceful-Garden-Chapter-Images (8 Nov 2026), renamed unchanged." % (issuer, time, n, linked, state, pkg),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI (ChatGPT), per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. A chapter image, generated on its own (signed %s); it is not part of a Before/Possible pair." % (time or "")},
            "permitted_surfaces": ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "founder_approval": "Supplied by the founder as a DISC-037 chapter image for the Stage 3 private preview (8 Nov 2026); production use awaits the founder's release approval",
            "introduced": {"date": DATE, "subject": "DISC-037 The Resourceful Garden, Stage 3 private preview (not deployed)"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = masters[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": masters[role][1]},
             "method": "crop" if " crop " in " " + op else "optimise",
             "edit": {"description": "DISC-037 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc037-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Resizing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-037 IMAGES · written: %d masters, %d derivatives" % (len(masters), len(files)))


if __name__ == "__main__":
    main()
