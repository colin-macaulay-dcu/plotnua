#!/usr/bin/env python3
"""
DISC-001 Garden Retreat · final hero pair (founder instruction, 31 Oct 2026: "We have completed the new
Before/Possible image pair... Use the complete images. Do not split, crop, stretch or combine them").

  BEFORE   assets/disc001/img/Garden-Retreat-BEFORE-FINAL.png    the garden with an empty lawn
  POSSIBLE assets/disc001/img/Garden-Retreat-POSSIBLE-FINAL.png  the same garden with sauna, hot tub, plunge pool

Both files are the founder's, byte for byte (1698 x 926 PNG), each carrying its own OpenAI C2PA credential
recording an AI generation; they are declared from that metadata (Governance 2.0, Rule 2) and the hero
carries the AI-generated illustration label. WebP re-encodings (1698 / 1408 / 960 px) are served to
browsers that take WebP; the PNG itself is the <img> fallback. Nothing is cropped, stretched or combined.

The Release 4 hero (45a270b7 warmed -> 7d5f5718) is replaced; the warmed copy and its record are withdrawn
(no page shows it). 45a270b7 and 7d5f5718 themselves are unchanged and keep their other uses.

  python3 atlas-tools/build-disc001-final-hero-pair.py          build (files, register, page)
  python3 atlas-tools/build-disc001-final-hero-pair.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, re, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
PAGE = ROOT / "discovery-garden-retreat.html"
CHECK = "--check" in sys.argv
D = "assets/disc001/img/"
SRC = {"BEFORE": D + "Garden-Retreat-BEFORE-FINAL.png", "POSSIBLE": D + "Garden-Retreat-POSSIBLE-FINAL.png"}
SHA = {"BEFORE": "f638b8ac57f777e0817a7213a5cd5b1374a91f1af564d31eb8bcf8200a0da89b",
       "POSSIBLE": "2317209dac7d7f3d120bfed1f4bb08a2381988f25bb67a9e08b70bb0522e626f"}
WARM = [D + "DISC-001-HERO-BEFORE-WARM.jpg", D + "DISC-001-HERO-BEFORE-WARM-1408.webp", D + "DISC-001-HERO-BEFORE-WARM-960.webp"]
SIZES = "(max-width:1024px) and (orientation:portrait) 150vw, max(100vw, 132svh)"
W, H = 1698, 926
ALT = {"BEFORE": "Before: an attractive Irish back garden at golden hour with an empty lawn, a stone path, ferns, grasses and mature trees, and houses beyond the boundary wall.",
       "POSSIBLE": "The same garden as it could be: a timber sauna cabin, a hot tub and a plunge pool on curved decking at the end of the lawn, softly lit at dusk."}


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, w):
    if w != im.width:
        im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "WEBP", quality=80, method=6); return b.getvalue()


def webps(role):
    im = Image.open(ROOT / SRC[role]).convert("RGB")
    base = SRC[role][:-4]
    return {base + "-1698.webp": (enc(im, 1698), "webp-reencode", "Pillow %s, WebP quality 80, method 6" % PIL_VERSION),
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


def picture(role, prio):
    base = SRC[role][:-4]
    srcset = ", ".join("%s-%d.webp %dw" % (base, w, w) for w in (960, 1408, 1698))
    idattr = ' id="dHeroImg" class="on"' if role == "POSSIBLE" else ""
    fp = ' fetchpriority="high"' if prio else ""
    return ('        <picture>\n          <source type="image/webp" srcset="%s" sizes="%s">\n'
            '          <img%s%s src="%s" width="%d" height="%d" decoding="async" alt="%s">\n        </picture>\n'
            % (srcset, SIZES, idattr, fp, SRC[role], W, H, ALT[role]))


def page(t):
    fig = re.search(r'<figure class="pn-compare pn-compare--hero"[\s\S]*?</figure>', t).group(0)
    nf = re.sub(r'(<div class="pn-compare__possible">\n)[\s\S]*?(      </div>\n      <div class="pn-compare__before">)',
                lambda m: m.group(1) + picture("POSSIBLE", False) + m.group(2), fig, count=1)
    nf = re.sub(r'(<div class="pn-compare__before">\n)[\s\S]*?(      </div>\n      <span class="pn-compare__line")',
                lambda m: m.group(1) + picture("BEFORE", True) + m.group(2), nf, count=1)
    if "pn-compare__ai" not in nf:
        nf = nf.replace('      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>\n',
                        '      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>\n      <p class="pn-compare__ai">AI-generated illustration</p>\n', 1)
    nf = re.sub(r'aria-label="Compare the garden[^"]*"',
                'aria-label="Compare the garden with its empty lawn and with a sauna, hot tub and plunge pool. Higher values show more of the garden before."', nf, count=1)
    nf = nf.replace('style="--pnc-focus:62% 50%"', 'style="--pnc-focus:78% 50%"', 1)   # phones: keep sauna, hot tub and pool in frame
    t = t.replace(fig, nf, 1)
    t = re.sub(r'<link rel="preload" as="image" type="image/webp" imagesrcset="assets/disc001/img/DISC-001-HERO-BEFORE-WARM-960\.webp 960w, assets/disc001/img/DISC-001-HERO-BEFORE-WARM-1408\.webp 1408w" imagesizes="[^"]*" fetchpriority="high">',
               '<link rel="preload" as="image" type="image/webp" imagesrcset="%s-960.webp 960w, %s-1408.webp 1408w, %s-1698.webp 1698w" imagesizes="%s" fetchpriority="high">'
               % ((SRC["BEFORE"][:-4],) * 3 + (SIZES,)), t, count=1)
    t = re.sub(r"Same garden, one framing: one modest step, then\n       the full retreat\.[\s\S]*?are unchanged\. -->",
               "Same garden, one framing: an empty lawn, then\n       the full retreat. The founder's final pair (31 Oct 2026), used whole: Garden-Retreat-BEFORE-FINAL.png and\n       Garden-Retreat-POSSIBLE-FINAL.png (atlas-tools/build-disc001-final-hero-pair.py). -->", t, count=1)
    return t


def main():
    for role, a in SRC.items():
        if sha((ROOT / a).read_bytes()) != SHA[role]:
            sys.exit("REFUSED: %s is not the founder's file (sha256)" % a)
    files = {}
    for role in SRC:
        for a, v in webps(role).items():
            files[a] = (role,) + v
    reg = json.loads(REG.read_text(encoding="utf-8"))
    cur = PAGE.read_text(encoding="utf-8")
    if CHECK:
        recs = {r["asset"] for r in reg["records"]}
        der = {d["asset"]: d for d in reg["derivatives"]}
        bad = [a for a in SRC.values() if a not in recs]
        bad += [a for a, (role, data, *_r) in files.items()
                if a not in der or not (ROOT / a).exists() or sha((ROOT / a).read_bytes()) != der[a]["sha256"] or der[a]["sha256"] != sha(data)]
        bad += [w for w in WARM if (ROOT / w).exists() or w in der]
        if page(cur) != cur or "DISC-001-HERO-BEFORE-WARM" in cur: bad.append(PAGE.name)
        print("DISC-001 FINAL HERO PAIR · " + ("OK (2 founder files, %d WebP; page current)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for role, a in SRC.items():
        if a in {r["asset"] for r in reg["records"]}: continue
        ai, issuer, time, ings, state, codes = read_c2pa(ROOT / a)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        data = (ROOT / a).read_bytes()
        val = state if not codes else "%s (c2pa-python reports: %s; the claim signature and data hash validate)" % (state, ", ".join(codes))
        reg["records"].append({
            "asset": a, "sha256": SHA[role], "bytes": len(data), "pixels": [W, H], "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (discovery-garden-retreat.html), hero %s" % role,
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; actions: c2pa.created (digital source type trainedAlgorithmicMedia), c2pa.converted, c2pa.watermarked.unbound; validation %s." % (issuer, time, val),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE",
            "reference_disclosure": {"status": "UNCERTAIN", "statement": "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out."},
            "permitted_surfaces": ["discovery"], "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": "2026-10-31", "subject": "Founder's final Garden Retreat hero pair, supplied whole"}})
    for a, (role, data, method, encoder) in files.items():
        (ROOT / a).write_bytes(data)
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": SRC[role], "sha256": SHA[role]}, "method": method, "encoder": encoder, "made": "2026-10-31",
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                 "note": "WebP re-encoding removes the embedded C2PA credential. The derivative carries NO signed credential and must never be described as having one. The original PNG (unchanged, the <picture> fallback) keeps it."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] not in WARM]
    for w in WARM:
        if (ROOT / w).exists(): (ROOT / w).unlink()
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PAGE.write_text(page(cur), encoding="utf-8")
    print("built: 2 records, %d WebP, page updated, warmed copy withdrawn" % len(files))


if __name__ == "__main__":
    main()
