#!/usr/bin/env python3
"""DISC-015 · The Underground Swimming Pool: web images and their provenance (founder Phase 2 build
authorisation, 1 Nov 2026; built on dev/disc015-underground-swimming-pool, NOT deployed).

SOURCES: the founder's own masters, added unchanged and declared AI_ILLUSTRATION from each file's signed C2PA
credential (Governance 2.0, Rule 2). Nothing is generated here.
  01 BEFORE      assets/disc015/img/DISC-015-01-BEFORE-MASTER.png     (Google generative AI, 10 Aug 2026)
  03 POOL        assets/disc015/img/DISC-015-03-POOL-MASTER.png       (Google generative AI, 10 Aug 2026)
  04 POSSIBLE    assets/disc015/img/DISC-015-04-POSSIBLE-MASTER.png   (Google generative AI, 10 Aug 2026)
  02 CONSTRUCTION assets/disc015/img/DISC-015-02-CONSTRUCTION-MASTER.png  (the founder-approved
                 DISC-015-Construction-Final.png; built only once the file is present and its sha256 is pinned
                 below. The superseded Construction-Revised.png and draft.png are never used.)

ROUTINE EDITS (Governance 2.0, Rule 3), each recorded as a derivative bound to its unchanged master:
  * the visible generator mark (a four-point sparkle, centre (1256, 648), radius 27, the same place on all
    three Google masters) is removed: star mask, reverse alpha blend, 3 px Telea inpaint on its edge -- the
    Above and Beyond operation (build-disc016-hero-final.py) with this mark's measured position;
  * resizing (Lanczos) and encoding to WebP / JPEG (no AVIF: the provenance guard's P12 cannot read AVIF
    derivative headers, so AVIF copies would need their own records; WebP is served everywhere);
  * the phone hero copies are a 4:5 crop of the full frame at 76 % across (the whole rooflight and the rear
    extension stay in view); the hero pair is aligned to the pixel (01 and 04 share their geometry exactly);
  * the social card is a 1200 x 630 crop of the POOL.
No pixel is painted or generated beyond the mark removal.

  python3 atlas-tools/build-disc015-images.py          build files + register records/derivatives
  python3 atlas-tools/build-disc015-images.py --check  verify, write nothing
"""
import hashlib, importlib.util, io, json, pathlib, sys
import numpy as np, cv2
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
D = "assets/disc015/img/"
DATE = "2026-11-01"
_s = importlib.util.spec_from_file_location("d16", ROOT / "atlas-tools/build-disc016-hero-final.py")
D16 = importlib.util.module_from_spec(_s); _s.loader.exec_module(D16)   # read_c2pa (no side effects)

MASTERS = {   # role -> (path, sha256, what, mark)
    "BEFORE": (D + "DISC-015-01-BEFORE-MASTER.png", "74cbd0763534ed4f66835ca38e0af15e6b2832bcda37eb03bdf6dc744396c0e2",
               "DISC-015 hero BEFORE: an ordinary Irish suburban back garden (lawn, patio, planting, neighbouring houses)", True),
    "POOL": (D + "DISC-015-03-POOL-MASTER.png", "869e4fdb7e6f55a67c87ecf9393c687c28e2197470d9437aba960f5e2e7fe1c5",
             "DISC-015 underground reveal: an indoor swimming pool in a stone-finished chamber lit by a long rooflight", True),
    "POSSIBLE": (D + "DISC-015-04-POSSIBLE-MASTER.png", "cf3552a6d4bbacbf5a2aaae25b37b54d7e919756c57742bf9967f14c04d472f1",
                 "DISC-015 hero POSSIBLE: the same garden restored, with a long, narrow glazed rooflight set into the lawn", True),
    # The founder-approved construction image. Pin its sha256 here when the file is added (None = not yet supplied).
    "CONSTRUCTION": (D + "DISC-015-02-CONSTRUCTION-MASTER.png", None,
                     "DISC-015 construction stage: the same garden excavated, with the concrete pool chamber, part-cast roof slab and rooflight opening", False),
}
CX, CY, R, P, SS = 1256.0, 648.0, 27.0, 0.62, 4
MOBILE_X = 0.76          # 4:5 phone crop position across the frame
DESK = (768, 1024, 1376)


def sha(b): return hashlib.sha256(b).hexdigest()


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


def enc(im, fmt, w=None, **kw):
    if w and w != im.width: im = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, fmt, **kw); return b.getvalue()


def available():
    out = {}
    for role, (p, h, what, mark) in MASTERS.items():
        f = ROOT / p
        if h is None:
            if f.exists(): sys.exit("REFUSED: %s is present but its sha256 is not pinned in MASTERS" % p)
            continue
        if not f.exists() or sha(f.read_bytes()) != h: sys.exit("REFUSED: %s is not the founder's master (sha256)" % p)
        out[role] = (p, h, what, mark)
    return out


def outputs(masters):
    files = {}
    for role, (p, h, what, mark) in masters.items():
        bgr = cv2.imread(str(ROOT / p))
        if mark: bgr = clean_mark(bgr)
        rgb = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        W, H = rgb.size
        mk = "the visible generator mark removed (star mask at (1256, 648), radius 27), then " if mark else ""
        stem = D + "DISC-015-%s" % role
        widths = [w for w in DESK if w < W] + [W] if W <= max(DESK) else list(DESK)
        for w in sorted(set(widths)):
            files["%s-%d.webp" % (stem, w)] = (enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                                               mk + ("Lanczos resize to %d px wide" % w if w != W else "no resize"))
        jw = 1024 if role in ("BEFORE", "POSSIBLE") else min(W, 1376)
        files["%s-%d.jpg" % (stem, jw)] = (enc(rgb, "JPEG", jw, quality=88, progressive=True, optimize=True),
                                           "Pillow %s, JPEG quality 88, progressive" % PIL_VERSION, role, mk + "Lanczos resize to %d px wide" % jw)
        if role in ("BEFORE", "POSSIBLE"):
            cw = round(H * 0.8); x0 = round((W - cw) * MOBILE_X)
            m = rgb.crop((x0, 0, x0 + cw, H))
            op = mk + "4:5 crop x %d-%d (the full height), no resize" % (x0, x0 + cw)
            files["%s-M-%d.webp" % (stem, cw)] = (enc(m, "WEBP", quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role, op)
        if role == "POOL":
            # Discovery Library card copies, named as build-library-card-webp.py names them for this source, so
            # that builder reuses them (it never re-encodes a recorded file); here they carry the mark removal
            for w in (480, 960):
                files["assets/library/img/DISC-015-03-POOL-MASTER-%dw.webp" % w] = (
                    enc(rgb, "WEBP", w, quality=80, method=6), "Pillow %s, WebP quality 80, method 6" % PIL_VERSION, role,
                    mk + "Lanczos resize to %d px wide (Discovery Library card)" % w)
            ch = round(W * 630 / 1200); y0 = (H - ch) // 2
            og = rgb.crop((0, y0, W, y0 + ch)).resize((1200, 630), Image.LANCZOS)
            files[D + "DISC-015-og-1200x630.jpg"] = (enc(og, "JPEG", quality=86, progressive=True, optimize=True),
                                                    "Pillow %s, JPEG quality 86, progressive" % PIL_VERSION, role,
                                                    mk + "crop y %d-%d to 1200:630, Lanczos resize to 1200 x 630" % (y0, y0 + ch))
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
        print("DISC-015 IMAGES · " + ("OK (%d credentialed masters declared, %d derivatives, reproducible%s)" % (
            len(masters), len(files), "; construction image NOT YET SUPPLIED" if "CONSTRUCTION" not in masters else "")
            if not bad and not stray else "FAIL %s %s" % (bad, stray)))
        sys.exit(1 if bad or stray else 0)
    for role, (a, h, what, mark) in masters.items():
        if a in recs: continue
        ai, issuer, time, n, linked, state = D16.read_c2pa(ROOT / a)
        if not ai: sys.exit("REFUSED: %s: the credential does not record an AI generation" % a)
        rd = (("UNCERTAIN", "The credential records no input image. Credentials do not record conversation context, so inputs cannot be ruled out.") if n == 0 else
              ("CREDENTIALED", "The credential records %d input image(s), each carrying its own signed credential." % n) if linked == n else
              ("UNCERTAIN", "The credential records %d input image(s), %d without any credential, title or hash." % (n, n - linked)))
        data = (ROOT / a).read_bytes()
        reg["records"].append({
            "asset": a, "sha256": h, "bytes": len(data), "pixels": list(Image.open(ROOT / a).size), "class": "AI_ILLUSTRATION",
            "what": what + " (founder's master; the page shows its prepared copies)",
            "depicts_named_product": False, "depicts_named_organisation": False,
            "origin": {"basis": "C2PA_EMBEDDED",
                       "evidence": "Embedded C2PA manifest, read with c2pa-python: issuer %s, signed %s; the credential chain records c2pa.created with digital source type trainedAlgorithmicMedia; %d ingredient link(s), %d credentialed; validation %s." % (issuer, time, n, linked, state),
                       "declared_under": "Governance 2.0, Rule 2 (30 Oct 2026)"},
            "generated": {"tool": "%s generative AI, per the file's own signed C2PA credential" % issuer, "date": (time or "")[:10]},
            "prompt_status": "UNAVAILABLE", "reference_disclosure": {"status": rd[0], "statement": rd[1]},
            "permitted_surfaces": ["discovery", "library-card"] if role == "POOL" else ["discovery"],
            "content_credentials": {"embeds_c2pa": True},
            "introduced": {"date": DATE, "subject": "DISC-015 The Underground Swimming Pool, founder Phase 2 build authorisation"}})
    for a, (data, encoder, role, op) in files.items():
        f = ROOT / a; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
        src = masters[role][0]
        e = {"asset": a, "sha256": sha(data), "bytes": len(data), "pixels": list(Image.open(io.BytesIO(data)).size),
             "derived_from": {"asset": src, "sha256": masters[role][1]},
             "method": "crop" if " crop " in " " + op else ("artefact-removal" if masters[role][3] else "optimise"),
             "edit": {"description": "DISC-015 web copy (Governance 2.0, Rule 3): " + op + ".", "operation": op,
                      "verified_by": "atlas-tools/build-disc015-images.py --check"},
             "encoder": encoder, "made": DATE,
             "content_credentials": {"source_file_embeds_c2pa": True, "derivative_embeds_c2pa": False,
                                     "note": "Editing and re-encoding remove the embedded C2PA credential. This copy carries NO signed credential; the master keeps it, and its record carries the AI classification."}}
        reg["derivatives"] = [d for d in reg["derivatives"] if d["asset"] != a] + [e]
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("DISC-015 IMAGES · written: %d masters, %d derivatives" % (len(masters), len(files)))


if __name__ == "__main__":
    main()
