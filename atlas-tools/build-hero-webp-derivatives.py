#!/usr/bin/env python3
"""
SEO PHASE 1b · HERO WEBP DERIVATIVES (founder-approved build, 16 Oct 2026;
NOT approved for deployment until the founder says so)
===========================================================================
Makes WebP copies of the hero images the pages already paint first, records
each copy against its source in image-provenance-records.json, and serves
the copy through <picture> with the original JPEG as the fallback.

  python3 atlas-tools/build-hero-webp-derivatives.py           build
  python3 atlas-tools/build-hero-webp-derivatives.py --check   verify, write nothing

WHAT A DERIVATIVE IS, AND IS NOT
  * A re-encoding of ONE existing, enumerated source file: same picture, same
    framing, same aspect ratio. Never a crop, never an upscale, never a new
    photograph.
  * Hash-bound twice: its own sha256, and the sha256 of the exact source bytes
    it was made from. If the source changes, the derivative is stale and the
    provenance guard (P12) refuses.
  * It inherits the source's provenance state. It cannot be declared, carries
    no class, no label and no rights field, and grants nothing.
  * It lives in the register's own `derivatives` list, NOT in
    legacy_undeclared, so the backlog count (the ratchet) does not move.
  * It may appear only where its source already appears: every <picture>
    keeps the original <img> as its fallback (P12 checks every page).

The source files are not modified. Their sha256 is asserted before and after.
"""
import hashlib
import io
import json
import pathlib
import re
import sys

from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
QUALITY = 80
SMALL_W = 960
DATE = "2026-10-16"   # derivatives first made; holds and credential notes added 2026-10-17

# Source image -> (pages that paint it as the hero, `sizes` for that page).
# `sizes` describes the rendered width: object-fit:cover heroes at 88svh are
# wider than the viewport on a phone (height x 1.83), plate heroes are 100vw.
HEROES = {
    "assets/img/9785fd991d2488e9.jpg": {"index.html": "100vw"},
    "assets/img/5e17a24f46cdab9e.jpg": {"discovery-living-in-the-garden.html": "max(100vw, 161vh)"},
    "assets/img/7d5f5718cf9cd3da.jpg": {"discovery-garden-retreat.html": "max(100vw, 161vh)"},
    "assets/img/9805382f8164228a.jpg": {"discovery-hidden-bins.html": "100vw"},
    "assets/img/b5cbac3fff9072d4.jpg": {"discovery-driveway-income.html": "max(100vw, 161vh)"},
}

# HOMEPAGE CARD IMAGES (founder SEO directive, 19 Oct 2026: "optimise oversized
# homepage images where image rights permit derivative files"). These two are
# Discovery Library cards on the homepage, lazy-loaded, about 1 MB each -- the
# two heaviest files on the page. Same rule as the heroes: a derivative only
# where the source's lineage is established (BASIS below). The card <img> is
# matched by its lazy loading inside .d-card-media, on the listed page only.
# `sizes` follows the card CSS: the card is 78% / 56% / 34% of the viewport
# wide and 50vh (min 320px) tall with object-fit:cover, so on a portrait screen
# the image is drawn at its height x 1.83 -- often wider than the card.
CARDS = {
    "assets/img/ce9da2e51c945693.jpg": {"index.html":
        "(min-width:1000px) max(34vw, 92vh, 587px), (min-width:640px) max(56vw, 92vh, 587px), max(78vw, 92vh, 587px)"},
    "assets/img/8b20a0968b1fc5a1.jpg": {"index.html":
        "(min-width:1000px) max(34vw, 92vh, 587px), (min-width:640px) max(56vw, 92vh, 587px), max(78vw, 92vh, 587px)"},
}
MADE = {"assets/img/ce9da2e51c945693.jpg": "2026-10-19",
        "assets/img/8b20a0968b1fc5a1.jpg": "2026-10-19"}

# PROVENANCE HOLD (founder instruction, 17 Oct 2026). A source whose lineage is
# not adequately established gets NO derivative: the page keeps serving the
# original JPEG. --check refuses if a held source has a derivative anywhere.
HELD = {
    "assets/img/8c60a8f27eb9c697.jpg":
        "Living in the Garden 'Possible' plate. Its signed Google C2PA credential "
        "records a second generation input ('Input ingredient 1') with no credential, "
        "format, title or hash. It could not be identified from project records "
        "(1,101 local images scanned, no match). Held until identified.",
}

# How each released source's lineage is established (evidence:
# governance/hero-image-content-credentials-evidence-2026-10-16.json).
BASIS = {
    "assets/img/9785fd991d2488e9.jpg": "Signed Google C2PA credential in the deployed file itself (byte-identical to master The-Future.jpeg): created by Google Generative AI, no input ingredients.",
    "assets/img/5e17a24f46cdab9e.jpg": "Signed Google C2PA credential in master DISC-008-01-Recognition.png (perceptual match 0/256): created by Google Generative AI, no input ingredients; then a visible watermark added.",
    "assets/img/7d5f5718cf9cd3da.jpg": "Master DISC-001-Hero-MASTER.png (perceptual match 0/256) is the credentialed DISC-001-Hero.png (signed Google C2PA: created by Google Generative AI, no input ingredients) mirror-extended 16 px each side: centre 1376 px pixel-identical, edges reflected, no generative fill. Documented in commit 08237ff (26 Sep 2026) and re-verified 17 Oct 2026.",
    "assets/img/9805382f8164228a.jpg": "Signed Google C2PA credential in the deployed file itself (byte-identical to master DISC-029-IMAGE-01-PROBLEM-MASTER.jpeg): created by Google Generative AI, no input ingredients.",
    "assets/img/b5cbac3fff9072d4.jpg": "Signed Google C2PA credential in master 'DISC-014 Image 01 \u2014 Potential Asset.jpeg' (perceptual match 0/256): created by Google Generative AI, no input ingredients.",
    "assets/img/ce9da2e51c945693.jpg": "Signed Google C2PA credential in the deployed file itself (validation state Valid, issuer Google LLC, 28 Aug 2026): created by Google Generative AI, no input ingredients. Evidence: governance/c2pa-source-credentials/deployed-ce9da2e51c945693.jpg.c2pa.json (read 19 Oct 2026).",
    "assets/img/8b20a0968b1fc5a1.jpg": "Signed Google C2PA credential in the deployed file itself (validation state Valid, issuer Google LLC, 1 Sep 2026): created by Google Generative AI from one input ingredient that itself carries a signed Google credential with no further ingredients; every ingredient in the chain is credentialed. Evidence: governance/c2pa-source-credentials/deployed-8b20a0968b1fc5a1.jpg.c2pa.json (read 19 Oct 2026).",
}
CREDENTIAL_NOTE = ("WebP re-encoding removes the embedded C2PA credential. The derivative "
                   "carries NO signed credential and must never be described as having one. "
                   "The original JPEG (unchanged, still served as the <picture> fallback) and "
                   "the source credential evidence are retained.")


def has_c2pa(data):
    return b"jumdc2pa" in data


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(1)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def encode(im, width):
    if width != im.width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITY, method=6)
    return buf.getvalue(), im.size


def fidelity(src_im, webp_bytes, size):
    """SSIM / PSNR of the WebP against the source at the same pixel size."""
    import numpy as np
    from skimage.metrics import structural_similarity, peak_signal_noise_ratio
    ref = src_im if src_im.size == size else src_im.resize(size, Image.LANCZOS)
    a = np.asarray(ref.convert("RGB"), dtype=np.uint8)
    b = np.asarray(Image.open(io.BytesIO(webp_bytes)).convert("RGB"), dtype=np.uint8)
    return (round(float(structural_similarity(a, b, channel_axis=2)), 4),
            round(float(peak_signal_noise_ratio(a, b)), 2))


def picture_markup(page_src, src, sizes, small, full, full_w):
    srcset = "%s %dw, %s %dw" % (small, SMALL_W, full, full_w)
    m = list(re.finditer(r'<img\b[^>]*\bsrc="%s"[^>]*>' % re.escape(src), page_src))
    return m, srcset


def main():
    reg_text = REGISTER.read_text(encoding="utf-8")
    reg = json.loads(reg_text)
    entries = {e["asset"]: e for e in reg["records"] + reg["legacy_undeclared"]}
    legacy_before = len(reg["legacy_undeclared"])

    derivs, pages, files = [], {}, {}
    for src, page_sizes in list(HEROES.items()) + list(CARDS.items()):
        if src not in entries:
            die("%s is not an enumerated asset in the provenance register" % src)
        p = ROOT / src
        raw = p.read_bytes()
        if sha(raw) != entries[src]["sha256"]:
            die("%s bytes do not match the register; refusing to derive from it" % src)
        im = Image.open(io.BytesIO(raw))
        im.load()
        stem = src[:-4]
        for width, suffix in ((im.width, ""), (SMALL_W, "-%dw" % SMALL_W)):
            out = "%s%s.webp" % (stem, suffix)
            existing = ROOT / out
            if existing.exists():
                data = existing.read_bytes()      # never re-encode a recorded file
                size = Image.open(io.BytesIO(data)).size
            else:
                data, size = encode(im, width)
            if size[0] > im.width:
                die("%s would upscale its source" % out)
            if abs(size[0] / size[1] - im.width / im.height) > 0.005:
                die("%s would change the aspect ratio (crop)" % out)
            ssim, psnr = fidelity(im, data, size)
            files[out] = data
            derivs.append({
                "asset": out,
                "sha256": sha(data),
                "bytes": len(data),
                "pixels": list(size),
                "derived_from": {"asset": src, "sha256": entries[src]["sha256"]},
                "method": "webp-reencode" if size[0] == im.width else "webp-resize",
                "encoder": "Pillow %s, WebP quality %d, method 6%s"
                           % (PIL_VERSION, QUALITY, "" if size[0] == im.width
                              else ", Lanczos resize to %dpx wide" % size[0]),
                "fidelity": {"ssim": ssim, "psnr_db": psnr,
                             "measured_against": "source at the same pixel size"},
                "made": MADE.get(src, DATE),
                "lineage_basis": BASIS[src],
                "content_credentials": {
                    "source_file_embeds_c2pa": has_c2pa(raw),
                    "derivative_embeds_c2pa": has_c2pa(data),
                    "note": CREDENTIAL_NOTE if has_c2pa(raw) else (
                        "The deployed source JPEG already carries no embedded credential "
                        "(the signed credential is on the master, recorded in the evidence "
                        "file). The derivative carries NO signed credential and must never "
                        "be described as having one."),
                },
            })
            if has_c2pa(data):
                die("%s unexpectedly embeds C2PA data; a copied manifest would be "
                    "invalid for these bytes" % out)
        for page, sizes in page_sizes.items():
            pages.setdefault(page, []).append((src, sizes, "%s-%dw.webp" % (stem, SMALL_W),
                                               "%s.webp" % stem, im.width, src in CARDS))

    if set(HELD) & (set(HEROES) | set(CARDS)):
        die("a held source is also listed for derivation")
    for src in HELD:
        stem = src[:-4]
        for f in (ROOT / "assets/img").glob(pathlib.Path(stem).name + "*.webp"):
            die("held source %s has a derivative on disk: %s" % (src, f.name))
        for page in ROOT.glob("*.html"):
            if pathlib.Path(stem).name + ".webp" in page.read_text(encoding="utf-8") or \
               pathlib.Path(stem).name + "-%dw.webp" % SMALL_W in page.read_text(encoding="utf-8"):
                die("held source %s has a derivative referenced on %s" % (src, page.name))
    missing = [s for s in list(HEROES) + list(CARDS) if s not in BASIS]
    if missing:
        die("no recorded lineage basis for %s" % missing)

    # Fidelity floor: a derivative that visibly degrades is not a derivative.
    low = [d for d in derivs if d["fidelity"]["ssim"] < 0.90]
    if low:
        die("fidelity below SSIM 0.90: %s" % [d["asset"] for d in low])

    # --- the pages: wrap the hero <img> in <picture>, point the preload at WebP
    new_pages = {}
    for page, items in pages.items():
        t = (ROOT / page).read_text(encoding="utf-8")
        orig = t
        for src, sizes, small, full, full_w, is_card in items:
            srcset = "%s %dw, %s %dw" % (small, SMALL_W, full, full_w)
            source = '<source type="image/webp" srcset="%s" sizes="%s">' % (srcset, sizes)
            if source in t:
                continue
            m = list(re.finditer(r'<img\b[^>]*\bsrc="%s"[^>]*>' % re.escape(src), t))
            # only the hero occurrence: the first <img> with that src carrying
            # fetchpriority or the cmp class (the comparison plates)
            if is_card:
                # the card occurrence: lazy-loaded, directly inside .d-card-media
                hero = [x for x in m if 'loading="lazy"' in x.group(0)
                        and t[max(0, x.start() - 40):x.start()].rstrip().endswith('<div class="d-card-media">')]
            else:
                hero = [x for x in m if 'fetchpriority="high"' in x.group(0) or "cmp-" in x.group(0)]
            if len(hero) != 1:
                die("%s: expected exactly one %s <img> for %s, found %d"
                    % (page, "card" if is_card else "hero", src, len(hero)))
            tag = hero[0].group(0)
            # display:contents keeps the existing CSS (.d-hero img, .cmp img,
            # .hero-photo) applying to the <img> exactly as before.
            t = t.replace(tag, '<picture style="display:contents">%s%s</picture>' % (source, tag), 1)
            pre_old = '<link rel="preload" as="image" href="%s" fetchpriority="high">' % src
            if pre_old in t:
                t = t.replace(pre_old,
                              '<link rel="preload" as="image" type="image/webp" imagesrcset="%s" '
                              'imagesizes="%s" fetchpriority="high">' % (srcset, sizes), 1)
        if t != orig:
            new_pages[page] = t

    # --- the register: add/refresh the derivatives list; legacy untouched
    reg_new = dict(reg)
    reg_new["derivatives_note"] = (
        "HASH-BOUND DERIVATIVES (SEO Phase 1b, 16 Oct 2026). Each entry is a "
        "re-encoding of ONE enumerated source file, bound to that source's exact "
        "sha256. A derivative inherits its source's provenance state, carries no "
        "class, label or rights field, and is not counted in legacy_undeclared, so "
        "the ratchet is unchanged. The guard (P12) refuses a derivative whose "
        "source changed, that crops or upscales, that is not WebP, or that appears "
        "on a page without its source as the fallback.")
    reg_new["derivatives"] = sorted(derivs, key=lambda d: d["asset"])
    reg_new["derivative_holds"] = [{"source": s, "reason": r, "since": "2026-10-17"}
                                   for s, r in sorted(HELD.items())]
    if len(reg_new["legacy_undeclared"]) != legacy_before:
        die("the backlog count would change")
    reg_out = json.dumps(reg_new, indent=2, ensure_ascii=True) + "\n"

    pending = []
    for f, data in files.items():
        if not (ROOT / f).exists() or (ROOT / f).read_bytes() != data:
            pending.append(f)
    if reg_out != reg_text:
        pending.append(REGISTER.name)
    pending += sorted(new_pages)

    if CHECK:
        if pending:
            die("CHECK: not in the Phase 1b state: %s" % ", ".join(pending))
        print("HERO WEBP DERIVATIVES · CHECK OK — %d derivatives of %d sources, "
              "backlog %d (unchanged), nothing written" % (len(derivs), len(HEROES) + len(CARDS), legacy_before))
        return

    for f, data in files.items():
        if not (ROOT / f).exists():
            (ROOT / f).write_bytes(data)
            print("  wrote %s (%d KB)" % (f, len(data) // 1024))
    for page, t in new_pages.items():
        (ROOT / page).write_text(t, encoding="utf-8")
        print("  wrote %s" % page)
    if reg_out != reg_text:
        REGISTER.write_text(reg_out, encoding="utf-8")
        print("  wrote %s" % REGISTER.name)
    # sources untouched
    for src in list(HEROES) + list(CARDS):
        if sha((ROOT / src).read_bytes()) != entries[src]["sha256"]:
            die("a source file changed during the build (%s)" % src)
    print("HERO WEBP DERIVATIVES · built — %d derivatives, backlog %d (unchanged)"
          % (len(derivs), legacy_before))


if __name__ == "__main__":
    main()
