#!/usr/bin/env python3
"""
DISC-022 The Hidden Cars · hero pair (founder instruction, 31 Oct 2026: "The two approved images are now saved in
the DISC-022: The Hidden Cars folder ... Preserve the approved images without unnecessary editing").

  BEFORE   assets/disc022/img/PlotNua_Hidden_Cars_BEFORE.png              the street, family car on the driveway
  POSSIBLE assets/disc022/img/PlotNua_Underground_Car_Lift_Possible.png   the same street, the driveway a car lift

Both files are the founder's, byte for byte (1678 x 937 PNG), each carrying its own OpenAI C2PA credential
recording an AI generation; they are declared from that metadata (Governance 2.0, Rule 2) and the page carries the
approved disclosure beneath the hero. The pair aligns as supplied (feature match: scale 0.9999, shift under 0.3 px),
so nothing is composited, cropped or stretched. WebP re-encodings (1678 / 1408 / 960 px) are served to browsers
that take WebP; the PNG itself is the <img> fallback. The page is built by build-release7-hero-sliders.py.

  python3 atlas-tools/build-disc022-hero-pair.py          build (files, register)
  python3 atlas-tools/build-disc022-hero-pair.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, re, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc022/img/"
SRC = {"BEFORE": D + "PlotNua_Hidden_Cars_BEFORE.png", "POSSIBLE": D + "PlotNua_Underground_Car_Lift_Possible.png"}
SHA = {"BEFORE": "6e04d954965f53d76468dd1839c3fe8e9a73e78a0b98d293a51b5736054b4b25",
       "POSSIBLE": "6e5d120b8624cc03a0126f7b3f7ba00052a2bb55dae1c7b5516d519d94141b45"}
SIZES = "(max-width:1024px) and (orientation:portrait) 150vw, max(100vw, 132svh)"
W, H = 1678, 937
def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, w):
    if w != im.width:
        im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "WEBP", quality=80, method=6); return b.getvalue()


def webps(role):
    im = Image.open(ROOT / SRC[role]).convert("RGB")
    base = SRC[role][:-4]
    return {base + "-1678.webp": (enc(im, 1678), "webp-reencode", "Pillow %s, WebP quality 80, method 6" % PIL_VERSION),
            base + "-1408.webp": (enc(im, 1408), "webp-resize", "Pillow %s, WebP quality 80, method 6, Lanczos resize to 1408px wide" % PIL_VERSION),
            base + "-960.webp": (enc(im, 960), "webp-resize", "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION)}


def read_c2pa(path):
    import c2pa
    with c2pa.Reader(str(path)) as r:
        j = json.loads(r.json())
    m = j["manifests"][j["active_manifest"]]
    acts = [a for x in m.get("assertions", []) if "actions" in x["label"] for a in x["data"]["actions"]]
    ai = any(a.get("action") == "c2pa.created" and "trainedAlgorithmicMedia" in str(a.get("digitalSourceType", "")) for a in acts)
    sig = m.get("signature_info", {})
    codes = sorted({s["code"] for s in (j.get("validation_status") or [])})
    return ai, sig.get("issuer"), sig.get("time"), len(m.get("ingredients", [])), j.get("validation_state"), codes


def main():
    for role, a in SRC.items():
        if sha((ROOT / a).read_bytes()) != SHA[role]:
            sys.exit("REFUSED: %s is not the founder's file (sha256)" % a)
    files = {}
    for role in SRC:
        for a, v in webps(role).items():
            files[a] = (role,) + v
    reg = json.loads(REG.read_text(encoding="utf-8"))
    if CHECK:
        recs = {r["asset"] for r in reg["records"]}
        der = {d["asset"]: d for d in reg["derivatives"]}
        bad = [a for a in SRC.values() if a not in recs]
        bad += [a for a, (role, data, *_r) in files.items()
                if a not in der or not (ROOT / a).exists() or sha((ROOT / a).read_bytes()) != der[a]["sha256"] or der[a]["sha256"] != sha(data)]
        print("DISC-022 HERO PAIR · " + ("OK (2 founder files declared, %d WebP reproducible)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for role, a in SRC.items():
        if a in {r["asset"] for r in reg["records"]}: continue
        ai, issuer, time, ings, state, codes = read_c2pa(ROOT / a)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        data = (ROOT / a).read_bytes()
        val = state if not codes else "%s (c2pa-python reports: %s; the claim signature and data hash validate)" % (state, ", ".join(codes))
        reg["records"].append({
            "asset": a, "sha256": SHA[role], "bytes": len(data), "pixels": [W, H], "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (discovery-hidden-cars.html), hero %s" % role,
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; actions: c2pa.created (digital source type trainedAlgorithmicMedia), c2pa.converted, c2pa.watermarked.unbound; validation %s." % (issuer, time, val),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out."},
            "permitted_surfaces": ["discovery"], "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": "2026-10-31", "subject": "Founder's Hidden Cars hero pair, supplied whole (Release 7)"}})
    for a, (role, data, method, encoder) in files.items():
        (ROOT / a).write_bytes(data)
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": SRC[role], "sha256": SHA[role]}, "method": method, "encoder": encoder, "made": "2026-10-31",
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                 "note": "WebP re-encoding removes the embedded C2PA credential. The derivative carries NO signed credential and must never be described as having one. The original PNG (unchanged, the <picture> fallback) keeps it."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("built: 2 records, %d WebP" % len(files))


if __name__ == "__main__":
    main()
