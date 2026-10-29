#!/usr/bin/env python3
"""INGEST · PlotArt gallery export -> public gallery package (Phase 1, 29 Oct 2026)

    python3 atlas-tools/plotart-gallery-ingest.py EXPORT_DIR PACKAGES_ROOT

EXPORT_DIR    gallery.json + the artist's original photographs (what PlotArt Studio exports).
PACKAGES_ROOT the folder of gallery packages; this gallery is written to PACKAGES_ROOT/<slug>/,
              and every other package there is used for duplicate detection.

Exit codes: 0 package written (it may still carry BLOCK findings, which stop PUBLICATION but not a
private preview); 2 export refused (structure or privacy) and nothing written.
See atlas-tools/plotart_gallery.py for the rules.
"""
import json, os, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plotart_gallery as G  # noqa: E402

PROCESSING = ["camera rotation (EXIF orientation) applied", "colour converted to sRGB where a profile was embedded",
              "all metadata removed (EXIF, GPS, XMP, ICC)", "never cropped or upscaled",
              "WebP quality %d at up to %s px on the long edge" % (G.WEBP_QUALITY, "/".join(map(str, G.SIZES)))]


def main(export_dir, root):
    try:
        g = G.validate_export(json.load(open(os.path.join(export_dir, "gallery.json"), encoding="utf-8")))
    except (G.Refused, ValueError, OSError) as e:
        print("REFUSED: %s" % e)
        return 2
    a, pub = g["artist"], g["publication"]
    slug = a["slug"]
    other_sha, other_dh, my_sha, my_dh = {}, {}, {}, {}   # duplicate detection across every package
    if os.path.isdir(root):
        for other in sorted(os.listdir(root)):
            p = os.path.join(root, other, "package.json")
            if other != slug and os.path.exists(p):
                for r in json.load(open(p, encoding="utf-8"))["provenance_sources"]:
                    other_sha.setdefault(r["source_sha256"], "the gallery of " + other)
                    other_dh.setdefault(r["dhash"], "an image in the gallery of " + other)
    tmp = tempfile.mkdtemp(prefix="pa-ingest-")
    img_dir = os.path.join(tmp, slug, "img")
    blocks, warns, sources, prov = [], [], [], []

    def take(entry, stem, subject, work=None):
        src = os.path.join(export_dir, entry["file"])
        if not os.path.isfile(src) or os.path.islink(src):
            blocks.append("%s: file %s is missing from the export" % (stem, entry["file"]))
            return None
        rec, b, w = G.process_image(src, img_dir, stem, G.MIN_PORTRAIT_EDGE if subject == "portrait" else G.MIN_LONG_EDGE)
        blocks.extend("%s: %s" % (stem, x) for x in b)
        warns.extend("%s: %s" % (stem, x) for x in w)
        if "derivatives" not in rec:
            return None
        sha, dh = rec["source_sha256"], rec["dhash"]
        if sha in other_sha:
            blocks.append("%s: this exact photograph is already in %s (rights check needed)" % (stem, other_sha[sha]))
        elif sha in my_sha:
            warns.append("%s: the same photograph is also used for %s" % (stem, my_sha[sha]))
        else:
            near = [v for d, v in list(other_dh.items()) + list(my_dh.items()) if G.hamming(d, dh) <= 4]
            if near:
                warns.append("%s: looks very similar to %s (check it isn't a duplicate)" % (stem, near[0]))
        my_sha.setdefault(sha, stem)
        my_dh.setdefault(dh, stem)
        sources.append({"source_sha256": sha, "dhash": dh, "stem": stem})
        for d in rec["derivatives"]:
            prov.append({
                "asset": "plotart/artists/%s/img/%s" % (slug, d["file"]), "sha256": d["sha256"], "bytes": d["bytes"],
                "pixels": d["pixels"], "class": "ARTIST_SUPPLIED_ARTWORK", "subject": subject,
                "artist_slug": slug, "work_slug": work["slug"] if work else None,
                "source_sha256": sha, "processing": PROCESSING, "colour": rec["colour"],
                "photographer": entry["photographer"], "photo_credit": entry.get("photo_credit"),
                "ai_involvement": work["ai_involvement"] if work else "none",
                "licence_version": pub.get("licence_version"), "permission_ref": pub.get("permission_ref"),
                "permitted_surfaces": ["plotart-artist-gallery", "plotart-virtual-gallery"]})
        return {"role": entry["role"], "alt": entry["alt"], "photo_credit": entry.get("photo_credit") if entry["photographer"] == "other_with_permission" else None,
                "aspect": rec["aspect"], "pixels": rec["pixels"], "derivatives": [{k: d[k] for k in ("file", "long_edge", "pixels")} for d in rec["derivatives"]]}

    portrait = take(a["portrait"], "portrait", "portrait") if a.get("portrait") else None
    works = []
    for w in sorted(g["works"], key=lambda x: (x.get("order", 999), x["id"])):
        imgs = []
        order = sorted(w["images"], key=lambda i: i["role"] != "main")
        for n, i in enumerate(order, 1):
            r = take(i, "%s-%d" % (w["slug"], n), "artwork", w)
            if r:
                imgs.append(r)
        ww = {k: w.get(k) for k in ("id", "slug", "title", "year", "medium", "materials", "h_cm", "w_cm", "d_cm",
                                     "price_eur", "price_on_request", "availability", "description",
                                     "ai_involvement", "ai_note", "ai_founder_decision")}
        ww["images"] = imgs
        if w["ai_involvement"] == "generated" and w.get("ai_founder_decision") != "approved":
            warns.append("%s: declared as entirely prompt-generated; needs your eligibility decision" % w["slug"])
        if w["availability"] == "available" and w.get("price_eur") is None and not w.get("price_on_request"):
            warns.append("%s: available but has no price; it will show 'Price on request'" % w["slug"])
        works.append(ww)
    art = {k: a.get(k) for k in ("slug", "display_name", "founding", "practice", "medium", "statement", "bio", "website", "instagram")}
    art["county"] = a.get("county") if a.get("county_public") else None
    art["portrait"] = portrait
    pkg = {"schema": G.PACKAGE_SCHEMA, "artist": art, "works": works,
           "publication": {k: pub.get(k) for k in sorted(G.PUB_KEYS)},
           "checks": {"blocks": blocks, "warns": warns},
           "provenance": prov, "provenance_sources": sources}
    pkg["checks"]["publication_blocks"] = G.publication_blocks(pkg)
    os.makedirs(os.path.join(tmp, slug), exist_ok=True)      # even when no image could be processed
    json.dump(pkg, open(os.path.join(tmp, slug, "package.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    dest = os.path.join(root, slug)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(root, exist_ok=True)
    shutil.move(os.path.join(tmp, slug), dest)
    shutil.rmtree(tmp, ignore_errors=True)
    pb = pkg["checks"]["publication_blocks"]
    print("INGEST · %s · %d artwork(s), %d image file(s) · %d block(s), %d warning(s) · %s" % (
        slug, len(works), len(prov), len(pb), len(warns), "PUBLISHABLE" if not pb else "NOT PUBLISHABLE (preview only)"))
    for x in pb:
        print("  BLOCK  " + x)
    for x in warns:
        print("  WARN   " + x)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])))
