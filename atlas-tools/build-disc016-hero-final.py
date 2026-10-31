#!/usr/bin/env python3
"""
DISC-016 Above and Beyond · final hero polish (founder instruction, 31 Oct 2026: "The existing Before/Possible
images are APPROVED... Remove the football from both images using the smallest possible localised edit...
Investigate restoring the AI-generated illustration label... do not assume credentials survive image editing").

SOURCES: the founder's credentialed masters (Documents/PlotNua/Images/Discoveries/DISC-016 Above and Beyond),
added unchanged and declared from their own Google C2PA credentials (Governance 2.0, Rule 2):
  assets/disc016/img/Above-and-Beyond-01-Before.png           (the same picture as b53d75f9, losslessly)
  assets/disc016/img/Above-and-Beyond-04-Two-Pod-Reveal.png   (the same picture as aecece07)

HERO COPIES (routine edits, Rule 3), each derived from its master; editing removes the credential, so the copies
carry none and say so; the record of the master carries the AI classification and the hero shows the label:
  1. the faint generator mark removed exactly as in Release 3 (build-disc016-hero-mark-removal.py's operation:
     star mask at (1288, 649), reverse alpha blend, 3 px edge inpaint);
  2. the football removed from each picture by taking the lawn from the OTHER picture at the same place: the two
     masters align to 0.3 px and the ball sits on plain lawn in the other picture, so nothing is invented and the
     pair stays aligned. BEFORE ball: ellipse centre (707, 676), axes 15 x 13; POSSIBLE ball: centre (799, 589),
     axes 12 x 11; 2 px feather; the borrowed lawn is shifted in level to the local surround (sigma 6).
Outputs: assets/disc016/img/DISC-016-HERO-{BEFORE,POSSIBLE}-FINAL.jpg (quality 92) + -1408.webp + -960.webp.
The Release 3 -MR copies are withdrawn with their records.

  python3 atlas-tools/build-disc016-hero-final.py          build (files, register, page)
  python3 atlas-tools/build-disc016-hero-final.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, re, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
PAGE = ROOT / "discovery-above-and-beyond.html"
CHECK = "--check" in sys.argv
D = "assets/disc016/img/"
MASTER = {"BEFORE": (D + "Above-and-Beyond-01-Before.png", "e15eeb6dbf36a3830d8a64d5330cfc5f5cde72b56848f24d31bd2a6c2f868d9a"),
          "POSSIBLE": (D + "Above-and-Beyond-04-Two-Pod-Reveal.png", "5555da5ffe50770303549cd8e15bfbfe1ffcf75e786bb091d25b059c95d8ff4b")}
BALL = {"BEFORE": ((707, 676), (15, 13)), "POSSIBLE": ((799, 589), (12, 11))}
MR = [D + "DISC-016-HERO-%s-MR%s" % (r, s) for r in ("BEFORE", "POSSIBLE") for s in (".jpg", "-1408.webp", "-960.webp")]
SIZES = "(max-width:1024px) and (orientation:portrait) 150vw, max(100vw, 132svh)"

# The Release 3 mark-removal operation, unchanged (from build-disc016-hero-mark-removal.py, now retired).
CX, CY, R, P, SS = 1288.0, 649.0, 27.0, 0.62, 4


def star(h, w):
    y, x = np.mgrid[0:h * SS, 0:w * SS].astype(np.float32) / SS
    f = (np.abs(x - CX) / R) ** P + (np.abs(y - CY) / R) ** P
    return cv2.resize((f <= 1).astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)


def clean_mark(bgr):
    T = star(*bgr.shape[:2])
    inside = T > 0.99
    ring = (cv2.dilate((T > 0).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0) & (T == 0)
    im = bgr.astype(np.float32)
    mi, mo = im[inside].mean(0), im[ring].mean(0)
    a = float(np.clip(((mi - mo) / (255 - mo)).mean(), 0, 0.9))
    A = (a * T)[..., None]
    rec = np.clip((im - A * 255) / (1 - A), 0, 255).astype(np.uint8)
    edge = cv2.dilate((((T > 0.02) & (T < 0.98)).astype(np.uint8) * 255), np.ones((3, 3), np.uint8))
    return cv2.inpaint(rec, edge, 3, cv2.INPAINT_TELEA)


def sha(b): return hashlib.sha256(b).hexdigest()


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def ball_out(img, other, role):
    (cx, cy), (ax, ay) = BALL[role]
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.float32)
    cv2.ellipse(m, (cx, cy), (ax, ay), 0, 0, 360, 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    ring = np.zeros((h, w), np.uint8); cv2.ellipse(ring, (cx, cy), (ax + 14, ay + 14), 0, 0, 360, 1, -1)
    ring = (ring > 0) & (m < 0.01)
    I, O = img.astype(np.float32), other.astype(np.float32)
    shift = I[ring].mean(0) - O[ring].mean(0)          # level of the surround, per channel
    out = I * (1 - m[..., None]) + (O + shift) * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8), int((m > 0.004).sum())


def build_images():
    raw = {r: cv2.imread(str(ROOT / p)) for r, (p, _) in MASTER.items()}
    clean = {r: clean_mark(raw[r]) for r in raw}
    out, px = {}, {}
    out["BEFORE"], px["BEFORE"] = ball_out(clean["BEFORE"], clean["POSSIBLE"], "BEFORE")
    out["POSSIBLE"], px["POSSIBLE"] = ball_out(clean["POSSIBLE"], clean["BEFORE"], "POSSIBLE")
    files = {}
    for role, img in out.items():
        rgb = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        base = D + "DISC-016-HERO-%s-FINAL" % role
        files[base + ".jpg"] = (role, enc(rgb, "JPEG", quality=92, progressive=True, optimize=True), "Pillow %s, JPEG quality 92, progressive" % PIL_VERSION)
        files[base + "-1408.webp"] = (role, enc(rgb, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION)
        files[base + "-960.webp"] = (role, enc(rgb, "WEBP", 960, quality=80, method=6), "Pillow %s, WebP quality 80, method 6, Lanczos resize to 960px wide" % PIL_VERSION)
    return files, px


def read_c2pa(path):
    """AI generation is read from the credential chain: the active manifest (Google: opened, visible watermark
    added, converted to PNG) and, through its parentOf ingredients, the manifests embedded in the same file."""
    import c2pa
    with c2pa.Reader(str(path)) as r:
        j = json.loads(r.json())
    ms = j["manifests"]
    def acts(m): return [a for x in m.get("assertions", []) if "actions" in x["label"] for a in x["data"]["actions"]]
    seen, todo, ai, n, linked = set(), [j["active_manifest"]], False, 0, 0
    while todo:
        k = todo.pop()
        if k in seen or k not in ms: continue
        seen.add(k); m = ms[k]
        ai = ai or any(a.get("action") == "c2pa.created" and "trainedAlgorithmicMedia" in str(a.get("digitalSourceType", "")) for a in acts(m))
        for i in m.get("ingredients", []):
            n += 1
            if i.get("active_manifest") in ms: linked += 1; todo.append(i["active_manifest"])
    sig = ms[j["active_manifest"]].get("signature_info", {})
    return ai, sig.get("issuer"), sig.get("time"), n, linked, j.get("validation_state")


def page(t):
    for role in ("BEFORE", "POSSIBLE"):
        old, new = D + "DISC-016-HERO-%s-MR" % role, D + "DISC-016-HERO-%s-FINAL" % role
        t = t.replace(old + ".jpg", new + ".jpg").replace(old + "-1408.webp", new + "-1408.webp").replace(old + "-960.webp", new + "-960.webp")
    fig = re.search(r'<figure class="pn-compare pn-compare--hero"[\s\S]*?</figure>', t).group(0)
    if "pn-compare__ai" not in fig:
        nf = fig.replace('      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>\n',
                         '      <p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>\n      <p class="pn-compare__ai">AI-generated illustration</p>\n', 1)
        t = t.replace(fig, nf, 1)
    return t


def main():
    for role, (p, h) in MASTER.items():
        if sha((ROOT / p).read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
    files, px = build_images()
    reg = json.loads(REG.read_text(encoding="utf-8"))
    cur = PAGE.read_text(encoding="utf-8")
    if CHECK:
        recs = {r["asset"] for r in reg["records"]}; der = {d["asset"]: d for d in reg["derivatives"]}
        bad = [p for p, _ in MASTER.values() if p not in recs]
        bad += [a for a, (role, data, _e) in files.items() if a not in der or not (ROOT / a).exists()
                or sha((ROOT / a).read_bytes()) != der[a]["sha256"] or der[a]["sha256"] != sha(data)]
        bad += [m for m in MR if (ROOT / m).exists() or m in der]
        if page(cur) != cur or "-MR" in re.search(r'<header class="d-hero[\s\S]*?</header>', cur).group(0): bad.append(PAGE.name)
        print("DISC-016 FINAL HERO · " + ("OK (2 credentialed masters declared, %d hero files reproducible, label on page)" % len(files) if not bad else "FAIL %s" % bad))
        sys.exit(1 if bad else 0)
    for role, (p, h) in MASTER.items():
        if p in {r["asset"] for r in reg["records"]}: continue
        ai, issuer, time, n, linked, state = read_c2pa(ROOT / p)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % p)
        if n == 0: rd = ("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out.")
        elif linked == n: rd = ("CREDENTIALED", "The credential records %d input image(s), each carrying its own signed credential." % n)
        else: rd = ("UNCERTAIN", "The credential records %d input image(s), %d without any credential, title or hash: not identifiable from the file." % (n, n - linked))
        data = (ROOT / p).read_bytes()
        reg["records"].append({
            "asset": p, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / p).size), "class": "AI_ILLUSTRATION",
            "what": "Discovery illustration (discovery-above-and-beyond.html), hero %s master; the page shows its edited copy" % role,
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; active manifest: opened, visible watermark added, converted to PNG; its credential chain (all manifests embedded in the file) records c2pa.created by Google Generative AI with digital source type trainedAlgorithmicMedia; %d ingredient link(s) in the chain, %d credentialed; validation %s. Founder's master file, the same picture as assets/img/%s (lossless original of that JPEG)." % (issuer, time, n, linked, state, "b53d75f9dff4af2e.jpg" if role == "BEFORE" else "aecece07994fe0db.jpg"),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE", "reference_disclosure": {"status": rd[0], "statement": rd[1]},
            "permitted_surfaces": ["discovery"], "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": "2026-10-31", "subject": "Founder's credentialed DISC-016 master, added for the hero copies"}})
    for a, (role, data, encoder) in files.items():
        (ROOT / a).write_bytes(data)
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": MASTER[role][0], "sha256": MASTER[role][1]}, "method": "artefact-removal",
             "edit": {"description": "Hero copy for the Above and Beyond slider (Governance 2.0, Rule 3): the faint generator mark removed (as in Release 3) and the football removed (founder instruction, 31 Oct 2026). Nothing else changed.",
                      "operation": "Mark: star mask centred (1288, 649), reverse alpha blend, 3 px Telea inpaint on its edge. Football: ellipse centre %s, axes %s, 2 px feather, filled with the other master's lawn at the same place (the pair aligns to 0.3 px), level-matched to the surround; %d px. No generative fill." % (BALL[role][0], BALL[role][1], px[role]),
                      "verified_by": "atlas-tools/build-disc016-hero-final.py --check"},
             "encoder": encoder, "made": "2026-10-31",
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                 "note": "Editing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential and must never be described as having one; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] not in MR]
    for m in MR:
        if (ROOT / m).exists(): (ROOT / m).unlink()
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PAGE.write_text(page(cur), encoding="utf-8")
    print("built: masters declared, %d hero files, -MR copies withdrawn, label added" % len(files))


if __name__ == "__main__":
    main()
