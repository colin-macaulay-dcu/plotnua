#!/usr/bin/env python3
"""
Guards for the Premium Supplier Gallery prototype (pass2/supplier-galleries).

Reads the BUILT page, not the builder's intentions, and checks it against
independent sources (image-rights-records.json and the live Garden Retreat
explorer config). Then mutates the page in memory to prove each guard can fail.

  G1  every supplier image is an APPROVED asset of a PUBLISHABLE grant, exact URL
  G2  every image carries its required credit, linked to the permitted domain
  G3  every image carries a medium label matching the asset (Photograph / Visualisation)
  G4  images are never cropped: no object-fit:cover / clip on .pn-sg images in the CSS
  G5  makers in the gallery == makers in the live Discovery explorer (no invented supplier)
  G6  a 'sponsored' card must show a visible "Sponsored" label (none exist today)
  G7  a maker with a commercial offer in the live config shows a disclosure
  G8  no link to a private supplier preview, no endorsement words
  G9  page is noindex and not linked from any public page
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "prototypes/supplier-gallery/garden-retreat.html"
CSS = ROOT / "assets/components/pn-supplier-gallery.css"
BANNED = re.compile(r"\b(vetted|approved supplier|certified|recommended supplier|preferred supplier|best|top[- ]rated)\b", re.I)


def rights():
    out = {}
    for r in json.loads((ROOT / "image-rights-records.json").read_text())["records"]:
        if r.get("public_visibility") == "PUBLISHABLE" and r.get("asset_approval_state") == "APPROVED" and r["permission_outcome"].startswith("Granted"):
            for a in r.get("approved_assets") or []:
                out[a["url"]] = (r, a)
    return out


def live():
    s = (ROOT / "discovery-garden-retreat.html").read_text()
    cfg = json.loads(re.search(r'id="mx-data">(.*?)</script>', s, re.S).group(1))
    names, offers = set(), set()
    for t in cfg["tabs"]:
        for m in t["makers"]:
            names.add(m["m"])
            if m.get("o"):
                offers.add(m["m"])
    return names, offers


def unesc(s):
    return s.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")


def checks(page, css):
    R = rights(); names, offers = live(); fails = []
    cards = re.findall(r'<article class="pn-sg-card" aria-label="([^"]+)">(.*?)</article>', page, re.S)
    for name, body in cards:
        name = unesc(name)
        for src in re.findall(r'<img src="([^"]+)"', body):
            src = unesc(src)
            if src not in R:
                fails.append(f"G1 {name}: image not an approved asset of a publishable grant: {src[:80]}"); continue
            rec, asset = R[src]
            if rec["organisation_name"] != name:
                fails.append(f"G1 {name}: image belongs to {rec['organisation_name']}")
            cred = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)<', body.split("pn-sg-cap", 1)[-1])
            if not cred or unesc(cred.group(2)) != rec["required_credit"] or rec["permitted_domain"] not in cred.group(1):
                fails.append(f"G2 {name}: required credit '{rec['required_credit']}' with link to {rec['permitted_domain']} missing")
            kind = re.search(r'class="pn-sg-kind">([^<]+)<', body)
            if not kind or kind.group(1).lower() != (asset.get("kind") or "").lower():
                fails.append(f"G3 {name}: medium label missing or wrong (asset kind {asset.get('kind')})")
        if 'data-sg-placement="sponsored"' in body and "Sponsored</span>" not in body:
            fails.append(f"G6 {name}: sponsored without label")
        if name in offers and "pn-sg-tag--rel" not in body:
            fails.append(f"G7 {name}: commercial relationship not disclosed")
        if BANNED.search(re.sub(r"<[^>]+>", " ", body)):
            fails.append(f"G8 {name}: endorsement wording")
    for li in re.findall(r'<li data-sg-placement="sponsored">(.*?)</li>', page, re.S):
        if "Sponsored</span>" not in li:
            fails.append("G6 sponsored slot without visible label")
    shown = {unesc(n) for n, _ in cards}
    if shown != names:
        fails.append(f"G5 gallery makers {sorted(shown ^ names)} differ from the live Discovery")
    if re.search(r'href="[^"]*-preview\.html', page):
        fails.append("G8 link to a private supplier preview")
    if re.search(r"\.pn-sg[^{]*img[^{]*\{[^}]*(object-fit\s*:\s*cover|clip-path|border-radius)", css):
        fails.append("G4 CSS crops or alters supplier images")
    if 'name="robots" content="noindex' not in page:
        fails.append("G9 prototype is indexable")
    for f in ROOT.glob("*.html"):
        if "prototypes/supplier-gallery" in f.read_text(errors="ignore"):
            fails.append(f"G9 {f.name} links to the prototype")
    return fails, len(cards)


def main():
    page, css = PAGE.read_text(), CSS.read_text()
    fails, n = checks(page, css)
    print(f"real build: {n} cards, {len(fails)} failures")
    for f in fails: print("  FAIL", f)

    tank = "https://images.squarespace-cdn.com/content/v1/67ac8d737a7c665f57f5babe/ab9c9630-7b25-441f-9559-b711ff7f6d5b/IMG_2531.JPG"
    mutations = {
        "G1 unapproved image": (page.replace(tank, tank.replace("IMG_2531", "IMG_9999"), 1), css),
        "G2 credit removed": (page.replace(">© OGNYX<", ">OGNYX<", 1), css),
        "G3 medium relabelled": (page.replace('pn-sg-kind">Visualisation', 'pn-sg-kind">Photograph', 1), css),
        "G4 crop in CSS": (page, css + "\n.pn-sg-mount img{ object-fit:cover; }"),
        "G5 invented supplier": (page.replace('aria-label="Pineca Ireland"', 'aria-label="Invented Saunas Ltd"', 1), css),
        "G6 unlabelled sponsor": (page.replace('data-sg-placement="editorial"', 'data-sg-placement="sponsored"', 1), css),
        "G7 disclosure removed": (re.sub(r'<span class="pn-sg-tag pn-sg-tag--rel">[^<]*</span>', "", page), css),
        "G8 preview link": (page.replace('href="https://www.tanktribe.ie/"', 'href="tanktribe-preview.html"', 1), css),
        "G8 endorsement": (page.replace("Outdoor saunas.</p>", "The best outdoor saunas.</p>", 1), css),
        "G9 indexable": (page.replace('content="noindex, nofollow"', 'content="index"'), css),
    }
    proved = 0
    for label, (p, c) in mutations.items():
        f, _ = checks(p, c)
        ok = any(x.startswith(label[:2]) for x in f)
        proved += ok
        print(f"  {'PROVED ' if ok else 'NOT PROVED'} {label}")
    print(f"mutations: {proved}/{len(mutations)} caught")
    sys.exit(0 if not fails and proved == len(mutations) else 1)


if __name__ == "__main__":
    main()
