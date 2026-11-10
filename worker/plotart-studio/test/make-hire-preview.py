#!/usr/bin/env python3
"""TEST ONLY · builds a PRIVATE local preview of the Art for Hire page (Stage 3B-4). Never publishes anything.

  python3 test/make-hire-preview.py PREVIEW_DIR --api URL [--fixture] [--form]

PREVIEW_DIR becomes a copy of the site's PlotArt pages (the repository is not touched), with the fourth gallery tab applied
by atlas-tools/plotart-hire-nav.py and the page built by atlas-tools/plotart-hire-page.py.
  without --fixture : the REAL state today: no work is listed for hire, so the page shows its empty state.
  with --fixture    : SYNTHETIC test artists ("Fixture Artist A/B/C") with generated abstract test images, used only to
                      check card layout, the live check and the enquiry dialog. They are not real artists or artworks and
                      never leave the preview. The catalogue is written to PREVIEW_DIR/fixture-catalogue.json."""
import argparse
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FIXTURE = [  # (artist slug, name, county, [(work id, title, medium, h, w, (px w, px h), colours)])
    ("fixture-artist-a", "Fixture Artist A", "Dublin", [("wfixa1", "Test work A1", "Oil on linen", 120, 90, (900, 1200), ((174, 98, 69), (39, 40, 42))),
                                                      ("wfixa2", "Test work A2", "Acrylic on board", 60, 80, (1200, 900), ((151, 120, 90), (231, 222, 208)))]),
    ("fixture-artist-b", "Fixture Artist B", "Galway", [("wfixb1", "Test work B1", "Monoprint, acrylic and lacquer on paper", 100, 100, (1200, 1200), ((60, 92, 120), (231, 222, 208))),
                                                      ("wfixb2", "Test work B2", "Charcoal on paper", 70, 50, (857, 1200), ((40, 40, 40), (210, 205, 195)))]),
    ("fixture-artist-c", "Fixture Artist C", "Cork", [("wfixc1", "Test work C1", "Oil on canvas", 150, 200, (1200, 900), ((120, 140, 90), (27, 28, 30))),
                                                    ("wfixc2", "Test work C2", "Mixed media", 40, 30, (900, 1200), ((200, 160, 60), (44, 46, 48)))]),
]


def image(path, size, colours):
    from PIL import Image, ImageDraw
    w, h = size
    im = Image.new("RGB", size, colours[1])
    d = ImageDraw.Draw(im)
    for k in range(1, 5):
        m = k * min(w, h) // 11
        d.rectangle([m, m, w - m, h - m], outline=colours[0], width=max(4, min(w, h) // 90))
    d.ellipse([w * .3, h * .35, w * .7, h * .65], fill=colours[0])
    d.text((24, h - 48), "TEST IMAGE · not an artwork", fill=(242, 235, 224))
    im.save(path, "WEBP", quality=82)


def fixture(prev):
    items = []
    for slug, name, county, works in FIXTURE:
        d = os.path.join(prev, "plotart", "artists", slug, "img")
        os.makedirs(d, exist_ok=True)
        ws = []
        for wid, title, medium, hcm, wcm, px, col in works:
            ders = []
            for le in (600, 1200):
                f = "%s-%d.webp" % (wid, le)
                sc = le / max(px)
                pix = (round(px[0] * sc), round(px[1] * sc))
                image(os.path.join(d, f), pix, col)
                ders.append({"file": f, "long_edge": le, "pixels": list(pix)})
            ws.append({"id": wid, "slug": wid, "title": title, "medium": medium, "h_cm": hcm, "w_cm": wcm, "d_cm": None, "availability": "available",
                       "images": [{"role": "main", "alt": "Synthetic test image for %s (not an artwork)" % title, "derivatives": ders}]})
            items.append({"artwork_id": wid, "artist_id": "a" + slug.replace("-", ""), "artist_slug": slug, "work_slug": wid,
                          "hire": {"county": county, "framing": "framed", "glazed": 0, "weight_band": "5_15kg", "collection": "ask", "deliver_km": None,
                                   "availability": "now", "available_from": None, "screen_use": "none", "photo_use": "none", "price": "Price on request"}})
        json.dump({"artist": {"slug": slug, "display_name": name}, "publication": {"state": "approved"}, "works": ws},
                  open(os.path.join(prev, "plotart", "artists", slug, "gallery.json"), "w"), indent=1)
    return {"generated_at": "2026-11-10T22:00:00Z", "items": items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prev")
    ap.add_argument("--api", required=True)
    ap.add_argument("--fixture", action="store_true")
    ap.add_argument("--form", action="store_true")
    a = ap.parse_args()
    prev = os.path.abspath(a.prev)
    shutil.rmtree(prev, ignore_errors=True)
    os.makedirs(prev)
    shutil.copytree(os.path.join(REPO, "plotart"), os.path.join(prev, "plotart"))
    for f in ("assets", "index.html", "privacy.html", "terms.html", "contact.html", "discoveries.html", "discovery-a-home-for-art.html"):
        src = os.path.join(REPO, f)
        if os.path.exists(src):
            os.symlink(src, os.path.join(prev, f))
    cat = fixture(prev) if a.fixture else {"generated_at": "2026-11-10T22:00:00Z", "items": []}
    json.dump(cat, open(os.path.join(prev, "fixture-catalogue.json" if a.fixture else "catalogue.json"), "w"), indent=1)
    r = subprocess.run([sys.executable, os.path.join(REPO, "atlas-tools", "plotart-hire-nav.py"), prev], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    print(r.stdout.strip().splitlines()[-1])
    cmd = [sys.executable, os.path.join(REPO, "atlas-tools", "plotart-hire-page.py"), prev, "--catalogue",
           os.path.join(prev, "fixture-catalogue.json" if a.fixture else "catalogue.json"), "--api", a.api] + (["--enquiries-form"] if a.form else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    print(r.stdout.strip())


if __name__ == "__main__":
    main()
