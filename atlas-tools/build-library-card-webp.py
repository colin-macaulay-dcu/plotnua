#!/usr/bin/env python3
"""
DISCOVERY LIBRARY · card-sized WebP delivery (founder instruction, 1 Nov 2026: "Discovery Library image
optimisation, Phase 1"; prepared on a branch, NOT deployed).

The Library showed every card image as its full-size JPEG (1376-1536 px, up to ~1.1 MB) in a slot about
240-520 px wide. This builder adds two hash-bound WebP derivatives per card source and serves them through
the established derivative <picture> layer (see derivative_picture_layer.py):

    <span class="lib-shot"><picture style="display:contents"><source type="image/webp" srcset="..." sizes="...">
      <img ...the card's existing tag, byte for byte...></picture></span>

  * the SOURCE is the card's existing image, unchanged, still the <img> fallback (P12 g);
  * -480w.webp and -960w.webp beside an assets/img/ source; for a source in a Discovery's own folder
    (assets/discNNN/), in assets/library/img/ so that Discovery's governed file set is untouched;
  * resized only (Lanczos), never cropped or upscaled; a source already 960 px
    wide gets a same-size re-encode; a -960w.webp already recorded for a source is reused, never re-encoded;
  * every new file is recorded in image-provenance-records.json -> derivatives (Governance 2.0): it inherits
    its source's provenance state, declares nothing, and does not change the legacy count;
  * the provenance hold is respected: a held source is refused outright;
  * nothing else on the page changes: card order, titles, lines, categories, labels, alt text and the
    AI disclosures are untouched (checked below).

  python3 atlas-tools/build-library-card-webp.py          build
  python3 atlas-tools/build-library-card-webp.py --check  verify, write nothing
"""
import hashlib, io, json, pathlib, re, sys
from PIL import Image, __version__ as PIL_VERSION

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "discoveries.html"
REG = ROOT / "image-provenance-records.json"
CHECK = "--check" in sys.argv
DATE = "2026-11-01"
QUALITY = 80
WIDTHS = (480, 960)
# measured card slot widths (img clientWidth, object-fit:cover): <=600 px one column ~86vw (200 px tall);
# 601-900 two columns ~42vw; >900 three columns, 238-320 px (230 px tall)
SIZES = "(max-width:600px) 86vw, (max-width:900px) 42vw, 320px"
WRAP_OPEN = '<picture style="display:contents"><source type="image/webp" srcset="%s" sizes="%s">'
# (1 Nov 2026) a declared AI image's card also carries its disclosure chip after the picture
# (build-library-card-labels.py); it is part of the closing group and is never touched here
CHIP = r'(?:<span class="lib-aichip">[^<]*</span>)?'
CARD = re.compile(r'(<a class="lib-card" href="[^"]+"[^>]*>\s*<span class="lib-shot">)(<img src="([^"]+)" alt="[^"]*"[^>]*>)(' + CHIP + r'</span>)')
WRAPPED = re.compile(r'(<a class="lib-card" href="[^"]+"[^>]*>\s*<span class="lib-shot">)<picture style="display:contents">'
                     r'<source type="image/webp" srcset="([^"]+)" sizes="([^"]+)">(<img src="([^"]+)" alt="[^"]*"[^>]*>)</picture>(' + CHIP + r'</span>)')
NOTE = ("Card-sized delivery for the Discovery Library (1 Nov 2026). A WebP re-encoding of one enumerated source, "
        "bound to its sha256; it inherits the source's provenance state and declares nothing. The derivative carries "
        "NO signed credential and must never be described as having one; the source stays on the page as the fallback.")


def sha(b): return hashlib.sha256(b).hexdigest()


def die(m):
    print("REFUSED: %s -- nothing written" % m); sys.exit(1)


def encode(im, w):
    if w != im.width:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.convert("RGB").save(b, "WEBP", quality=QUALITY, method=6)
    return b.getvalue(), im.size


def fidelity(src_im, data, size):
    import numpy as np
    from skimage.metrics import structural_similarity, peak_signal_noise_ratio
    ref = src_im if src_im.size == size else src_im.resize(size, Image.LANCZOS)
    a = np.asarray(ref.convert("RGB"), dtype=np.uint8)
    b = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), dtype=np.uint8)
    return round(float(structural_similarity(a, b, channel_axis=2)), 4), round(float(peak_signal_noise_ratio(a, b)), 2)


LIB_DIR = "assets/library/img/"


def name(src, w):
    # a card source in assets/img/ keeps the established sibling naming (<stem>-<w>w.webp, reusing any recorded
    # -960w file); a source in a Discovery's own folder (assets/discNNN/) gets its card derivatives in
    # assets/library/img/, so each Discovery's governed file set is left exactly as it is
    stem = src.rsplit(".", 1)[0]
    if not src.startswith("assets/img/"):
        stem = LIB_DIR + stem.rsplit("/", 1)[1]
    return "%s-%dw.webp" % (stem, w)


def unwrap(t):
    return WRAPPED.sub(lambda m: m.group(1) + m.group(4) + m.group(6), t)


def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    sources = {e["asset"]: e for e in reg["records"] + reg["legacy_undeclared"]}
    der = {d["asset"]: d for d in reg["derivatives"]}
    held = {h["source"] for h in reg.get("derivative_holds", [])}
    cur = PAGE.read_text(encoding="utf-8")
    base = unwrap(cur)                                   # the page as it is without this layer
    cards = CARD.findall(base)
    if len(cards) != 16:   # 16 since DISC-015 (development build, 1 Nov 2026)
        die("expected 16 Discovery cards with the governed <img src alt> shape, found %d" % len(cards))
    new_files, new_recs, plan = {}, [], {}
    for _, tag, src, _ in cards:
        if src in held: die("%s is on provenance hold" % src)
        if src not in sources: die("%s is not in the provenance register" % src)
        if src in der: die("%s is itself a derivative (no chains)" % src)
        raw = (ROOT / src).read_bytes()
        if sha(raw) != sources[src]["sha256"]: die("%s does not match its register hash" % src)
        im = Image.open(io.BytesIO(raw)); im.load()
        outs = []
        for w in WIDTHS:
            out = name(src, min(w, im.width)) if w <= im.width else None
            if out is None: continue
            outs.append((out, min(w, im.width)))
            if out in der:                                # already recorded: reuse, never re-encode
                if not (ROOT / out).exists() or sha((ROOT / out).read_bytes()) != der[out]["sha256"]:
                    die("%s is recorded but its file is missing or changed" % out)
                if der[out]["derived_from"]["asset"] != src: die("%s is recorded from another source" % out)
                continue
            data, size = encode(im, min(w, im.width))
            if size[0] > im.width: die("%s would upscale" % out)
            if abs(size[0] / size[1] - im.width / im.height) > 0.005: die("%s would crop" % out)
            s, p = fidelity(im, data, size)
            if s < 0.90: die("%s fidelity below SSIM 0.90 (%s)" % (out, s))
            if b"jumdc2pa" in data: die("%s unexpectedly embeds C2PA" % out)
            new_files[out] = data
            new_recs.append({
                "asset": out, "sha256": sha(data), "bytes": len(data), "pixels": list(size),
                "derived_from": {"asset": src, "sha256": sources[src]["sha256"]},
                "method": "webp-reencode" if size[0] == im.width else "webp-resize",
                "encoder": "Pillow %s, WebP quality %d, method 6%s" % (
                    PIL_VERSION, QUALITY, "" if size[0] == im.width else ", Lanczos resize to %dpx wide" % size[0]),
                "fidelity": {"ssim": s, "psnr_db": p, "measured_against": "source at the same pixel size"},
                "made": DATE,
                "lineage_basis": "Discovery Library card image (discoveries.html). Inherits the source's provenance "
                                 "state (%s); re-encoding only." % (sources[src].get("class") or sources[src].get("status")),
                "content_credentials": {"source_file_embeds_c2pa": b"jumdc2pa" in raw, "derivative_embeds_c2pa": False,
                                        "note": NOTE}})
        if len(outs) < 2 and im.width > 480: die("%s: expected two widths" % src)
        plan[src] = ", ".join("%s %dw" % (o, w) for o, w in outs)
    # the page with the layer
    built = CARD.sub(lambda m: m.group(1) + WRAP_OPEN % (plan[m.group(3)], SIZES) + m.group(2) + "</picture>" + m.group(4), base)
    if unwrap(built) != base: die("the layer would change something other than the card image wrapper")
    if CHECK:
        bad = []
        if cur != built: bad.append("discoveries.html is not built")
        if new_recs or new_files: bad.append("%d derivative(s) not yet recorded" % len(new_recs))
        print("LIBRARY CARD WEBP · " + ("OK (16 cards, %d derivatives served)" % sum(len(v.split(", ")) for v in plan.values())
                                        if not bad else "FAIL: %s" % "; ".join(bad)))
        sys.exit(1 if bad else 0)
    for f, d in new_files.items():
        (ROOT / f).parent.mkdir(parents=True, exist_ok=True); (ROOT / f).write_bytes(d)
    reg["derivatives"] += new_recs
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PAGE.write_text(built, encoding="utf-8")
    print("built: %d new derivatives recorded; 16 cards wrapped" % len(new_recs))


if __name__ == "__main__":
    main()
