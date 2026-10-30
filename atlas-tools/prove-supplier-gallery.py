#!/usr/bin/env python3
"""
Guards for the Premium Supplier Gallery (v1), first page discovery-garden-retreat.html.

Reads the BUILT page, not the builder's intentions, and checks it against
independent sources (image-rights-records.json and the live Garden Retreat
explorer config). Then mutates the page in memory to prove each guard can fail.

  G1  every supplier image is an APPROVED asset of a PUBLISHABLE grant, exact URL, or the
      approved_delivery_variants URL recorded against that exact asset on the same record
  G2  every image carries its required credit, linked to the permitted domain
  G3  every image carries a medium label matching the asset (Photograph / Visualisation)
  G4  images are never cropped: no object-fit:cover / clip on .pn-sg images in the CSS
  G5  makers in the gallery == makers in the live Discovery explorer (no invented supplier)
  G6  a 'sponsored' card must show a visible "Sponsored" label (none exist today)
  G7  a maker with a commercial offer in the live config shows a disclosure
  G8  no link to a private supplier preview, no endorsement words
  G9  the gallery appears exactly once, on Garden Retreat only, directly before the Maker Explorer
  G10 every external link opens in a new tab with rel="noopener noreferrer"
  G11 every location line is backed by evidence in the editorial file; none for OGNYX
      (founder rule 30 Oct 2026: its confirmation does not clearly authorise public display)
  G12 Tanktribe shows the CORE photograph (IMG_8495), never IMG_2531 (founder decision 30 Oct 2026)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "discovery-garden-retreat.html"
B_START, B_END = "<!-- PN-SUPPLIER-GALLERY v1", "<!-- /PN-SUPPLIER-GALLERY -->"
EXPLORER = "<!-- 6c · PLOTNUA-MAKER-EXPLORER-V1"
CSS = ROOT / "assets/components/pn-supplier-gallery.css"
BANNED = re.compile(r"\b(vetted|approved supplier|certified|recommended supplier|preferred supplier|best|top[- ]rated)\b", re.I)


def rights():
    out = {}
    for r in json.loads((ROOT / "image-rights-records.json").read_text())["records"]:
        if r.get("public_visibility") == "PUBLISHABLE" and r.get("asset_approval_state") == "APPROVED" and r["permission_outcome"].startswith("Granted"):
            assets = {a["url"]: a for a in r.get("approved_assets") or []}
            for a in assets.values():
                out[a["url"]] = (r, a)
            for v in r.get("approved_delivery_variants") or []:
                if v.get("of") in assets:          # a variant counts only for its own asset
                    out[v["url"]] = (r, assets[v["of"]])
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


def region(page):
    i, j = page.find(B_START), page.find(B_END)
    return page[i:j] if i >= 0 and j > i else ""


def checks(full, css):
    R = rights(); names, offers = live(); fails = []
    # G9 placement, then every other check reads the gallery region only
    if full.count(B_START) != 1 or full.count(B_END) != 1:
        fails.append("G9 gallery region missing or duplicated on Garden Retreat")
    elif not re.match(r"\s*" + re.escape(EXPLORER), full[full.index(B_END) + len(B_END):]):
        fails.append("G9 gallery is not directly before the Maker Explorer")
    for f in ROOT.glob("*.html"):
        if f.name != PAGE.name and "data-pn-supplier-gallery" in f.read_text(errors="ignore"):
            fails.append(f"G9 gallery found on {f.name}: not authorised beyond Garden Retreat")
    page = region(full)
    cards = re.findall(r'<article class="pn-sg-(?:card|entry)[^"]*" aria-label="([^"]+)">(.*?)</article>', page, re.S)
    for name, body in cards:
        name = unesc(name)
        for src in re.findall(r'<img src="([^"]+)"', body):
            src = unesc(src)
            if src not in R:
                fails.append(f"G1 {name}: image not an approved asset of a publishable grant: {src[:80]}"); continue
            rec, asset = R[src]
            if rec["organisation_name"] != name:
                fails.append(f"G1 {name}: image belongs to {rec['organisation_name']}")
            cred = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)<', body.split('class="pn-sg-cap"', 1)[-1])
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
    for a in re.findall(r'<a [^>]*href="https?://[^"]+"[^>]*>', page):
        if 'target="_blank"' not in a or 'rel="noopener noreferrer"' not in a:
            fails.append(f"G10 external link without new-tab security attributes: {a[:80]}")
    ed = json.loads((ROOT / "atlas-tools/supplier-gallery/garden-retreat.editorial.json").read_text())
    for name, body in cards:
        nm = unesc(name)
        if "pn-sg-loc" in body or "<dt>Made in" in body or "<dt>Registered" in body or "<dt>Based" in body:
            b = (ed["makers"].get(nm) or {}).get("base")
            if not b or not b.get("evidence") or nm == "OGNYX":
                fails.append(f"G11 {nm}: location shown without authorised evidence")
    if "IMG_2531" in page or "IMG_8495" not in page:
        fails.append("G12 Tanktribe image is not the CORE photograph IMG_8495")
    shown = {unesc(n) for n, _ in cards}
    if shown != names:
        fails.append(f"G5 gallery makers {sorted(shown ^ names)} differ from the live Discovery")
    if re.search(r'href="[^"]*-preview\.html', page):
        fails.append("G8 link to a private supplier preview")
    if re.search(r"\.pn-sg[^{]*img[^{]*\{[^}]*(object-fit\s*:\s*cover|clip-path|border-radius)", css):
        fails.append("G4 CSS crops or alters supplier images")
    return fails, len(cards)


def main():
    page, css = PAGE.read_text(), CSS.read_text()
    fails, n = checks(page, css)
    print(f"real build: {n} cards, {len(fails)} failures")
    for f in fails: print("  FAIL", f)

    tank = "https://images.squarespace-cdn.com/content/v1/67ac8d737a7c665f57f5babe/2d930a20-ec94-4b5f-8af4-159501335d62/IMG_8495.jpg"
    mutations = {
        "G1 unapproved image": (page.replace(tank, tank.replace("IMG_8495", "IMG_9999"), 1), css),
        "G1 unrecorded size variant": (page.replace("IMG_8495.jpg?format=1000w", "IMG_8495.jpg?format=2500w", 1), css),
        "G2 credit removed": (page.replace(">© OGNYX<", ">OGNYX<", 1), css),
        "G3 medium relabelled": (page.replace('pn-sg-kind">Visualisation', 'pn-sg-kind">Photograph', 1), css),
        "G4 crop in CSS": (page, css + "\n.pn-sg-mount img{ object-fit:cover; }"),
        "G5 invented supplier": (page.replace('aria-label="Pineca Ireland"', 'aria-label="Invented Saunas Ltd"', 1), css),
        "G6 unlabelled sponsor": (page.replace('data-sg-placement="editorial"', 'data-sg-placement="sponsored"', 1), css),
        "G7 disclosure removed": (re.sub(r'<span class="pn-sg-tag pn-sg-tag--rel">[^<]*</span>', "", page), css),
        "G8 preview link": (page.replace('href="https://www.tanktribe.ie/"', 'href="tanktribe-preview.html"', 1), css),
        "G8 endorsement": (page.replace("Outdoor saunas.</p>", "The best outdoor saunas.</p>", 1), css),
        "G10 link security dropped": (page.replace('rel="noopener noreferrer" target="_blank"', 'target="_blank"', 1), css),
        "G11 OGNYX location shown": (page.replace('aria-label="OGNYX"><figure class="pn-sg-fig">', 'aria-label="OGNYX"><p class="pn-sg-loc"><b>Registered in</b> Bray</p><figure class="pn-sg-fig">', 1), css),
        "G12 Carlsberg image back": (page.replace("2d930a20-ec94-4b5f-8af4-159501335d62/IMG_8495.jpg", "ab9c9630-7b25-441f-9559-b711ff7f6d5b/IMG_2531.JPG"), css),
        "G9 gallery moved after explorer": (page.replace(EXPLORER, "<p>moved</p>\n  " + EXPLORER, 1), css),
        "G9 gallery duplicated": (page.replace(B_END, B_END + "\n" + B_START + " dup -->", 1), css),
    }
    proved = 0
    for label, (p, c) in mutations.items():
        f, _ = checks(p, c)
        ok = any(x.split(" ")[0] == label.split(" ")[0] for x in f)
        proved += ok
        print(f"  {'PROVED ' if ok else 'NOT PROVED'} {label}")
    print(f"mutations: {proved}/{len(mutations)} caught")
    sys.exit(0 if not fails and proved == len(mutations) else 1)


if __name__ == "__main__":
    main()
