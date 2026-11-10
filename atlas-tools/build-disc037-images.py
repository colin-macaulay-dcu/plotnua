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

CHAPTER 04 (added 8 Nov 2026, Stage 4): DISC-037-06-GREENHOUSE-STORES-SUNSHINE-MASTER.png, 1536 x 1024, from the founder's
package DISC-037-Remaining-Three-Images-2026-11-08.zip, added unchanged under its own name.
HERO (Stage 7, 8 Nov 2026): the approved POSSIBLE (DISC-037-02-POSSIBLE-APPROVED.png) and the founder-chosen BEFORE v2
(DISC-037-01-BEFORE-CANDIDATE-v2.png, Stage 6 package), added unchanged. Neither pair tried in Stages 4-6 met the slider
alignment standard, so the founder approved a DISC-037-only presentation: two labelled views with a crossfade. Desktop
copies are whole images; the phone copies use one identical centred 4:5 window; the social card is made from the POSSIBLE.

HERO (Stage 11, 8 Nov 2026): the founder's preferred new pair, DISC-037-BEFORE-candidate.png / DISC-037-POSSIBLE-candidate.png
(package DISC-037-slider-candidate-review.zip), added unchanged as DISC-037-01-BEFORE-WIDE-MASTER.png / -02-POSSIBLE-WIDE-MASTER.png,
1672 x 452 each. They carry no content credentials, so they are declared in the founder-attested form (see the records), not
from C2PA. Shown in the standard slider. Both copies drop the same top 6 rows (a pale strip along the POSSIBLE's top edge, a
leftover of the founder-side label removal) and nothing else; phones get one identical 16:9 window from the same strip.
The Stage 7-10 pair stays recorded: its POSSIBLE still makes the Library card and the social card (unchanged at Stage 11).

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
    "06-GREENHOUSE-STORES-SUNSHINE": (D + "DISC-037-06-GREENHOUSE-STORES-SUNSHINE-MASTER.png",
        "3f2e20a7989511e2762ae0594ff19a11525a5cc5fdac94f672bb1b3e0d7fa68e", (1536, 1024), "DISC-037-06-GREENHOUSE-STORES-SUNSHINE-MASTER.png",
        "DISC-037 chapter 04 image, The Greenhouse That Stores Sunshine: inside a timber lean-to glasshouse against a stone wall on a frosty, "
        "sunny winter morning, with dark water barrels fed by a downpipe, staging of salads and herbs in pots and trays, and a timber raised bed "
        "under a propped-open glazed lid; a generic illustrated greenhouse, no brand or mark visible"),
    "07-LIVING-ROOF-WILD-GARDEN": (D + "DISC-037-07-LIVING-ROOF-WILD-GARDEN-MASTER.png",
        "4b21a577cf252084dc3c7d73ce96067622c0ff58214e7ba2d3cf535f702c212e", (1536, 1024), "05-Living-Roof-and-Wild-Garden.png",
        "DISC-037 chapter 05 image, The Living Roof and Wild Garden: a timber garden building with a flowering sedum and wildflower "
        "roof, foxgloves, ferns and daisies in front and a dry-stone wall at the side"),
}
# THE STAGE 7-10 HERO PAIR (founder decision 8 Nov 2026; replaced in the hero at Stage 11). Both masters are retired with their
# records: the BEFORE (DISC-037-01-BEFORE-MASTER.png) at Stage 11, the POSSIBLE (DISC-037-02-POSSIBLE-MASTER.png) at Stage 11D
# (proposed), when the Library card, social card and structured-data image moved to the Stage 11 POSSIBLE. Both stay in git
# history and in the founder's folder. History: the pair was: shown as two labelled views with a crossfade (NOT the standard
# comparison slider; the pair did not meet the slider alignment standard, and the founder approved this DISC-037-only
# presentation). Both are added unchanged: the approved POSSIBLE and the Stage 6 BEFORE v2 (founder's choice).
CARD = {}   # Stage 11D (proposed): the Stage 7-10 POSSIBLE master is retired with its record; nothing references it any more
HERO = {   # Stage 11: role -> (path, sha256, size, package file, what). Records are founder-attested (no C2PA), added separately.
    "BEFORE": (D + "DISC-037-01-BEFORE-WIDE-MASTER.png",
        "3c653de3367f6868a416797dfa1391b592fd4e23039e24bd2a613e49b0633e84", (1672, 452), "DISC-037-BEFORE-candidate.png",
        "DISC-037 hero BEFORE (Stage 11): an ordinary garden at a contemporary white-rendered Irish home"),
    "POSSIBLE": (D + "DISC-037-02-POSSIBLE-WIDE-MASTER.png",
        "8f85339993dbb2d01477f26655944fa79834f1ed3ae030a5ccd986b6f6de54b9", (1672, 452), "DISC-037-POSSIBLE-candidate.png",
        "DISC-037 hero POSSIBLE (Stage 11): the same garden made productive"),
}
HERO_TOP = 6                          # both copies drop the same top 6 rows (pale strip on the POSSIBLE)
HERO_WIDTHS = (1024, 1376, 1672)
MOBILE_X0, MOBILE_W = 647, 793        # identical 16:9 window for both views (full remaining height, 446 px)
CARD_X0 = 670                         # Stage 11D: Library card window x 670-1630 of the POSSIBLE (proposed)
OG_X0 = 590                           # Stage 11D: social card window x 590-1440 of the POSSIBLE (proposed)
WEBP = (480, 768, 1024, 1376)
JPEG = (768, 1024)


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def available():
    for role, (p, h, size, *_r) in list(CHAPTERS.items()) + list(CARD.items()) + list(HERO.items()):
        f = ROOT / p
        if not f.exists() or sha(f.read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
        if Image.open(f).size != size: sys.exit("REFUSED: %s is not %d x %d" % ((p,) + size))
    m = dict(CHAPTERS); m.update({"CARD-" + k: v for k, v in CARD.items()}); m.update(HERO)
    return m


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
    for role, (p, h, size, *_r) in HERO.items():
        strip = Image.open(ROOT / p).convert("RGB"); W, H = strip.size
        strip = strip.crop((0, HERO_TOP, W, H)); H -= HERO_TOP
        stem = D + "DISC-037-HERO-%s" % role
        for w in HERO_WIDTHS:
            op = ("crop y %d-%d (drops the top %d rows; the same crop on both views), " % (HERO_TOP, HERO_TOP + H, HERO_TOP)) + \
                 ("Lanczos resize to %d px wide (hero, whole width)" % w if w != W else "no resize (hero, whole width)")
            files["%s-%d.webp" % (stem, w)] = (enc(strip, "WEBP", w, quality=82, method=6), "Pillow %s, WebP quality 82, method 6" % PIL_VERSION, role, op)
        files["%s-1024.jpg" % stem] = (enc(strip, "JPEG", 1024, quality=88, progressive=True, optimize=True), "Pillow %s, JPEG quality 88, progressive" % PIL_VERSION, role,
                                       "crop y %d-%d (drops the top %d rows; the same crop on both views), Lanczos resize to 1024 px wide (hero, whole width)" % (HERO_TOP, HERO_TOP + H, HERO_TOP))
        m = strip.crop((MOBILE_X0, 0, MOBILE_X0 + MOBILE_W, H))
        op = "crop y %d-%d and x %d-%d (a 16:9 window: beds, glasshouse and pantry), no resize; the same window for both views" % (HERO_TOP, HERO_TOP + H, MOBILE_X0, MOBILE_X0 + MOBILE_W)
        files["%s-M-%d.webp" % (stem, MOBILE_W)] = (enc(m, "WEBP", quality=82, method=6), "Pillow %s, WebP quality 82, method 6" % PIL_VERSION, role, op)
        files["%s-M-%d.jpg" % (stem, MOBILE_W)] = (enc(m, "JPEG", quality=88, progressive=True, optimize=True), "Pillow %s, JPEG quality 88, progressive" % PIL_VERSION, role, op)
        if role == "POSSIBLE":
            # Stage 11D (proposed, 10 Nov 2026): the Library card and the social card from the new POSSIBLE.
            # Card: one 960 x 446 window (beds, bean poles, glasshouse, water butts, the open pantry), no upscaling; the
            # card frame (about 1.6:1, 200 px tall) shows its centre. The WebPs are named after the master, as
            # build-library-card-webp.py names a Discovery card's copies. The card's <img> fallback is the hero's own
            # DISC-037-HERO-POSSIBLE-1024.jpg, because the Library rule requires the card image to appear on the page.
            c = strip.crop((CARD_X0, 0, CARD_X0 + 960, H))
            op = "crop y %d-%d and x %d-%d (Discovery Library card window: beds, glasshouse and pantry)" % (HERO_TOP, HERO_TOP + H, CARD_X0, CARD_X0 + 960)
            for w in (480, 960):
                files["assets/library/img/DISC-037-02-POSSIBLE-WIDE-MASTER-%dw.webp" % w] = (
                    enc(c, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                    op + (", no resize" if w == 960 else ", Lanczos resize to %d px wide" % w))
            # Social card: the standard 1200:630 shape at the strip's native height (850 x 446), never enlarged (gate P12).
            ow = round(H * 1200 / 630)
            og = strip.crop((OG_X0, 0, OG_X0 + ow, H))
            files[D + "DISC-037-og-%dx%d.jpg" % (ow, H)] = (enc(og, "JPEG", quality=86, progressive=True, optimize=True),
                "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role,
                "crop y %d-%d and x %d-%d (1200:630 shape: beds, glasshouse and pantry), no resize (social card)" % (HERO_TOP, HERO_TOP + H, OG_X0, OG_X0 + ow))
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
        print("DISC-037 IMAGES · " + ("OK (%d masters declared: %d credentialed, %d founder-attested; %d derivatives, reproducible)" % (len(masters), len(masters) - len(HERO), len(HERO), len(files))
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
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s. Supplied by the founder as '%s' in the package %s (8 Nov 2026), %s." % (issuer, time, n, linked, state, pkg,
                           ("DISC-037-Stage-6-BEFORE-Alignment-Test.zip" if role in HERO else "DISC-037-Remaining-Three-Images-2026-11-08.zip") if pkg.startswith("DISC-037-") else "DISC-037-Resourceful-Garden-Chapter-Images",
                           ("renamed unchanged" if role in HERO else "added unchanged under its own name") if pkg.startswith("DISC-037-") else "renamed unchanged"),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI (ChatGPT), per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": ({"status": "UNCERTAIN", "statement": "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out. A chapter image, generated on its own (signed %s); it is not part of a Before/Possible pair." % (time or "")}
                                     if role not in HERO else
                                     {"status": "UNCERTAIN", "statement": "The credential records no input image. The founder states (Stage 6, 8 Nov 2026) that the POSSIBLE was made first and approved, and that this BEFORE was then created separately by removing the resourceful-garden features; it is not a verified masked edit. Measured: the cottage aligns at a median of 0 px and the trees, wall and horizon within 2 px, but the patio dining set, patio edge and lawn light differ, so the pair is shown as two labelled views with a crossfade, not as a comparison slider (founder decision, Stage 7)." if role == "BEFORE" else
                                      "The credential records no input image. Approved by the founder as the DISC-037 hero POSSIBLE (Stages 5-7, 8 Nov 2026); its paired BEFORE was made afterwards. Shown as one of two labelled views with a crossfade, not as a comparison slider (founder decision, Stage 7)."}),
            "permitted_surfaces": ["discovery", "library-card"] if role == "POSSIBLE" else ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "founder_approval": ("Supplied by the founder as a DISC-037 chapter image for the Stage 3 private preview (8 Nov 2026); production use awaits the founder's release approval"
                                 if role not in HERO else "Approved by the founder as the DISC-037 hero %s for the two-view crossfade presentation (Stage 7 founder decision, private preview only, 8 Nov 2026); production use awaits the founder's release approval" % role),
            "introduced": {"date": DATE, "subject": "DISC-037 The Resourceful Garden, %s (not deployed)" % ("Stage 3 private preview" if role not in HERO else "Stage 7 hero presentation")}})
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
    # Stage 11: copies this builder no longer makes (the Stage 7-10 hero copies) are removed with their records.
    known = set(files) | {m[0] for m in masters.values()}
    for q in sorted((ROOT / D).iterdir()):
        a = str(q.relative_to(ROOT))
        if a not in known:
            q.unlink(); reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-037 IMAGES · written: %d masters, %d derivatives" % (len(masters), len(files)))


if __name__ == "__main__":
    main()
