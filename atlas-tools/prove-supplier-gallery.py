#!/usr/bin/env python3
"""
Guards for the Premium Supplier Gallery (v1): discovery-garden-retreat.html (first page)
and discovery-living-in-the-garden.html (DISC-008, founder approval to develop 30 Oct 2026).
A page may carry the gallery only if it has an editorial file in atlas-tools/supplier-gallery/.

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
  G13 DISC-008: only ÖÖD House, Powersheds and Yardbox carry an image (founder instruction 30 Oct
      2026); Garden Room Ireland and Don Modular Homes stay text-only until their previews are addressed
  G14 Garden Retreat's gallery region is byte-identical to the founder-approved release (sha256 pin)
"""
import hashlib
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "discovery-garden-retreat.html"
EDITORIALS = {json.loads(f.read_text(encoding="utf-8"))["discovery"]: f
              for f in sorted((ROOT / "atlas-tools/supplier-gallery").glob("*.editorial.json"))}
GR_REGION_SHA = "bc70d9aad57cc5b190fa1742c2c6591cfa7909687a188dede38f6ae0c832a6ea"   # production aca0556
LITG = "discovery-living-in-the-garden.html"
LITG_IMAGED = {"ÖÖD House", "Powersheds", "Yardbox"}
LITG_HELD = {"Garden Room Ireland", "Don Modular Homes"}
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


def names_of(r):
    return {r["organisation_name"], *(r.get("maker_name_aliases") or [])}


def live(page_name="discovery-garden-retreat.html"):
    s = (ROOT / page_name).read_text()
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


def checks(full, css, page_name="discovery-garden-retreat.html", others=None):
    R = rights(); names, offers = live(page_name); fails = []
    # G9 placement, then every other check reads the gallery region only
    if full.count(B_START) != 1 or full.count(B_END) != 1:
        fails.append(f"G9 gallery region missing or duplicated on {page_name}")
    elif not re.match(r"\s*" + re.escape(EXPLORER), full[full.index(B_END) + len(B_END):]):
        fails.append("G9 gallery is not directly before the Maker Explorer")
    for f in ROOT.glob("*.html"):
        text = (others or {}).get(f.name) or f.read_text(errors="ignore")
        if f.name not in EDITORIALS and "data-pn-supplier-gallery" in text:
            fails.append(f"G9 gallery found on {f.name}: no editorial file authorises it")
    page = region(full)
    cards = re.findall(r'<article class="pn-sg-(?:card|entry)[^"]*" aria-label="([^"]+)">(.*?)</article>', page, re.S)
    for name, body in cards:
        name = unesc(name)
        for src in re.findall(r'<img src="([^"]+)"', body):
            src = unesc(src)
            if src not in R:
                fails.append(f"G1 {name}: image not an approved asset of a publishable grant: {src[:80]}"); continue
            rec, asset = R[src]
            if name not in names_of(rec):
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
    ed = json.loads(EDITORIALS[page_name].read_text())
    for name, body in cards:
        nm = unesc(name)
        if "pn-sg-loc" in body or "<dt>Made in" in body or "<dt>Registered" in body or "<dt>Based" in body:
            b = (ed["makers"].get(nm) or {}).get("base")
            if not b or not b.get("evidence") or nm == "OGNYX":
                fails.append(f"G11 {nm}: location shown without authorised evidence")
    if page_name == PAGE.name:
        if "IMG_2531" in page or "IMG_8495" not in page:
            fails.append("G12 Tanktribe image is not the CORE photograph IMG_8495")
        i, j = full.find(B_START), full.find(B_END)
        if i < 0 or j < 0 or hashlib.sha256(full[i:j + len(B_END)].encode()).hexdigest() != GR_REGION_SHA:
            fails.append("G14 Garden Retreat gallery region differs from the approved release")
    if page_name == LITG:
        imaged = {unesc(n) for n, b in cards if "<img " in b}
        if imaged - LITG_IMAGED:
            fails.append(f"G13 DISC-008 images shown for {sorted(imaged - LITG_IMAGED)}: founder approved ÖÖD House, Powersheds and Yardbox only")
        for n, b in cards:
            if unesc(n) in LITG_HELD and ("<img " in b or 'class="pn-sg-card"' in b):
                fails.append(f"G13 {unesc(n)} featured or imaged before its preview is addressed")
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
    print(f"real build: {PAGE.name}: {n} cards, {len(fails)} failures")
    for f in fails: print("  FAIL", f)
    litg = (ROOT / LITG).read_text()
    lf, ln = checks(litg, css, LITG)
    print(f"real build: {LITG}: {ln} cards, {len(lf)} failures")
    for f in lf: print("  FAIL", f)
    fails += lf

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
    pw = "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/1610PALCTIMWDDW_d5c78ede-b4ff-441b-926e-8198c72f4ce4.png"
    gri = "https://static.wixstatic.com/media/fef4b6_b797b39e52a24c2782c27a0f7d4ea2e5~mv2.jpg"
    held_card = re.search(r'<article class="pn-sg-entry is-text" aria-label="Garden Room Ireland">', litg)
    litg_mut = {
        "G1 DISC-008 unapproved image": litg.replace(pw, pw.replace("1610PALC", "1611PALC"), 1),
        "G2 DISC-008 credit removed": litg.replace(">Image: Powersheds<", ">Powersheds<", 1),
        "G2 DISC-008 credit link dropped": litg.replace('href="https://www.yardbox.co.uk/" rel="noopener noreferrer" target="_blank">Image: Yard Box', 'href="https://example.com/" rel="noopener noreferrer" target="_blank">Image: Yard Box', 1),
        "G3 DISC-008 visualisation relabelled": litg.replace('pn-sg-kind">Visualisation', 'pn-sg-kind">Photograph', 1),
        "G5 DISC-008 invented supplier": litg.replace('aria-label="Hansa24 Group"', 'aria-label="Invented Garden Rooms Ltd"', 1),
        "G8 DISC-008 endorsement": litg.replace("Apex log cabins, in", "The best Apex log cabins, in", 1),
        "G13 DISC-008 held supplier imaged": (litg.replace(held_card.group(0), held_card.group(0).replace("is-text", "has-img") +
                                              f'<figure class="pn-sg-thumb"><div class="pn-sg-mount"><img src="{gri}" alt="x"></div></figure>', 1)
                                              if held_card else litg + "<!-- no GRI entry -->"),
        "G9 DISC-008 gallery moved after explorer": litg.replace(EXPLORER, "<p>moved</p>\n  " + EXPLORER, 1),
    }
    proved = 0
    for label, p in litg_mut.items():
        f, _ = checks(p, css, LITG)
        ok = any(x.split(" ")[0] == label.split(" ")[0] for x in f)
        proved += ok
        print(f"  {'PROVED ' if ok else 'NOT PROVED'} {label}")
    # an unauthorised page carrying the gallery
    f, _ = checks(page, css, others={"discovery-hidden-bins.html": "<section data-pn-supplier-gallery></section>"})
    ok = any("G9" in x and "hidden-bins" in x for x in f); proved += ok
    print(f"  {'PROVED ' if ok else 'NOT PROVED'} G9 gallery on an unauthorised page")
    # Garden Retreat region pin
    f, _ = checks(page.replace("Meet the makers.", "Meet the makers!", 1), css)
    ok = any(x.startswith("G14") for x in f); proved += ok
    print(f"  {'PROVED ' if ok else 'NOT PROVED'} G14 Garden Retreat region changed")
    total = len(mutations) + len(litg_mut) + 2
    for label, (p, c) in mutations.items():
        f, _ = checks(p, c)
        ok = any(x.split(" ")[0] == label.split(" ")[0] for x in f)
        proved += ok
        print(f"  {'PROVED ' if ok else 'NOT PROVED'} {label}")
    print(f"mutations: {proved}/{total} caught")
    sys.exit(0 if not fails and proved == total else 1)


if __name__ == "__main__":
    main()
