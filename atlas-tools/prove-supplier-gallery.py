#!/usr/bin/env python3
"""
Guards for the Premium Supplier Gallery (v1.1): every page configured in
atlas-tools/build-supplier-gallery.py (Garden Retreat; Living in the Garden).

Reads the BUILT pages, not the builder's intentions, and checks them against
independent sources (image-rights-records.json, image-rights-manifest.json, the
governed garden-room imagery and each page's live Maker Explorer config). Then
mutates each page in memory to prove each guard can fail.

  G1  every supplier image is authorised by the page's image authority:
        approved_assets - an APPROVED asset of a PUBLISHABLE grant, exact URL, or the
          approved_delivery_variants URL recorded against that exact asset;
        universe - the governed garden-room block for that URL, inside its permitted
          prefix, under a live grant whose required credit matches (the rule
          build-maker-explorer.py G3 applies to the same images)
  G2  every image carries its required credit, linked to the supplier's own domain
  G3  every image carries the right medium label (Photograph / Visualisation)
  G4  images are never cropped: no object-fit:cover / clip / radius on .pn-sg images
  G5  makers: full directory == the live explorer's makers (Garden Retreat);
      explorer mode (Living in the Garden, founder D1/D3): featured makers are the
      live explorer's, EVERY maker with an authorised lead image is featured, there
      is no duplicate directory, and "View all" targets the page's Maker Explorer
  G6  a 'sponsored' card must show a visible "Sponsored" label (none exist today)
  G7  a maker with a commercial offer in the live config shows a disclosure
  G8  no link to a private supplier preview, no endorsement words
  G9  each gallery appears exactly once, directly before the Maker Explorer, and only
      on configured pages
  G10 every external link opens in a new tab with rel="noopener noreferrer"
  G11 every location line is backed by evidence in the editorial file; none for OGNYX
  G12 Garden Retreat: Tanktribe shows IMG_8495 (founder decision 30 Oct 2026)
  G13 Living in the Garden: no editorial image override (founder D4)
  G14 Living in the Garden: every external link on a card stays on that maker's
      granted domain (founder D2 narrow exception)
"""
import importlib.util, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
B_START, B_END = "<!-- PN-SUPPLIER-GALLERY v1", "<!-- /PN-SUPPLIER-GALLERY -->"
EXPLORER = "<!-- 6c · PLOTNUA-MAKER-EXPLORER-V1"
CSS = ROOT / "assets/components/pn-supplier-gallery.css"
BANNED = re.compile(r"\b(vetted|approved supplier|certified|recommended supplier|preferred supplier|best|top[- ]rated)\b", re.I)
LIVE = {"Granted — Founder Confirmed", "Granted with Conditions — Founder Confirmed", "Granted — Supplier Confirmed (one-click)"}
norm = lambda s: re.sub(r"[^0-9a-z]", "", s.casefold())

_spec = importlib.util.spec_from_file_location("sgb", ROOT / "atlas-tools/build-supplier-gallery.py")
_b = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_b)
PAGES = _b.DISCOVERIES          # the configured pages (read, not duplicated)


def approved():
    out = {}
    for r in json.loads((ROOT / "image-rights-records.json").read_text())["records"]:
        if r.get("public_visibility") == "PUBLISHABLE" and r.get("asset_approval_state") == "APPROVED" and r["permission_outcome"].startswith("Granted"):
            assets = {a["url"]: a for a in r.get("approved_assets") or []}
            for a in assets.values():
                out[a["url"]] = (r["organisation_name"], r["required_credit"], [r["permitted_domain"]], a.get("kind") or "")
            for v in r.get("approved_delivery_variants") or []:
                if v.get("of") in assets:          # a variant counts only for its own asset
                    a = assets[v["of"]]
                    out[v["url"]] = (r["organisation_name"], r["required_credit"], [r["permitted_domain"]], a.get("kind") or "")
    return out


def governed():
    grants = {r["organisation_name"].casefold(): r for r in json.loads((ROOT / "image-rights-manifest.json").read_text())["rows"]
              if r.get("permission_outcome") in LIVE and not r.get("withdrawal_effective_at")}
    u = json.loads((ROOT / "garden-room-recommendation-universe-v1.json").read_text())
    out = {}
    for p in (u["products"] if isinstance(u, dict) else u):
        for b in (p.get("imagerySet") or ([p["imagery"]] if p.get("imagery") else [])):
            g = grants.get((b.get("supplier") or "").casefold())
            if not g or not b["url"].startswith(b.get("permittedPrefix") or "\0") or b.get("credit") != g.get("required_credit"):
                continue
            if not _b.grant_covers(g, b["url"]):
                continue
            doms = [g["permitted_domain"]] + ([urlparse(b["linkBack"]).netloc] if b.get("linkBack") else [])
            kind = "Visualisation" if (b.get("alt") or "").startswith("Visualisation") else "Photograph"
            out[b["url"]] = (b["supplier"], b["credit"], doms, kind)
    return out


def live(page_text):
    cfg = json.loads(re.search(r'id="mx-data">(.*?)</script>', page_text, re.S).group(1))
    names, offers, leads = set(), set(), {}
    for t in cfg["tabs"]:
        for m in t["makers"]:
            names.add(m["m"])
            if m.get("o"):
                offers.add(m["m"])
            if m.get("l"):
                leads.setdefault(m["m"], m["l"]["src"])
    return names, offers, leads


def unesc(s):
    return s.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")


def region(page):
    i, j = page.find(B_START), page.find(B_END)
    return page[i:j] if i >= 0 and j > i else ""


def checks(name, full, css):
    cfgp = PAGES[name]; fails = []
    AUTH = approved() if cfgp["authority"] == "approved_assets" else governed()
    names, offers, leads = live(full)
    if full.count(B_START) != 1 or full.count(B_END) != 1:
        fails.append(f"G9 {name}: gallery region missing or duplicated")
    elif not re.match(r"\s*" + re.escape(EXPLORER), full[full.index(B_END) + len(B_END):]):
        fails.append(f"G9 {name}: gallery is not directly before the Maker Explorer")
    page = region(full)
    cards = re.findall(r'<article class="pn-sg-(?:card|entry)[^"]*" aria-label="([^"]+)">(.*?)</article>', page, re.S)
    for nm, body in cards:
        nm = unesc(nm)
        for src in re.findall(r'<img src="([^"]+)"', body):
            src = unesc(src)
            if src not in AUTH:
                fails.append(f"G1 {name} {nm}: image not authorised ({cfgp['authority']}): {src[:80]}"); continue
            owner, credit, doms, kind = AUTH[src]
            if norm(owner) != norm(nm):
                fails.append(f"G1 {name} {nm}: image belongs to {owner}")
            cred = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)<', body.split('class="pn-sg-cap"', 1)[-1])
            if not cred or unesc(cred.group(2)) != credit or not any(d in cred.group(1) for d in doms):
                fails.append(f"G2 {name} {nm}: required credit '{credit}' linked to {doms} missing")
            k = re.search(r'class="pn-sg-kind">([^<]+)<', body)
            if not k or k.group(1).lower() != kind.lower():
                fails.append(f"G3 {name} {nm}: medium label missing or wrong (expected {kind})")
        if 'data-sg-placement="sponsored"' in body and "Sponsored</span>" not in body:
            fails.append(f"G6 {name} {nm}: sponsored without label")
        if nm in offers and "pn-sg-tag--rel" not in body:
            fails.append(f"G7 {name} {nm}: commercial relationship not disclosed")
        if BANNED.search(re.sub(r"<[^>]+>", " ", body)):
            fails.append(f"G8 {name} {nm}: endorsement wording")
    for li in re.findall(r'<li data-sg-placement="sponsored">(.*?)</li>', page, re.S):
        if "Sponsored</span>" not in li:
            fails.append(f"G6 {name}: sponsored slot without visible label")
    for a in re.findall(r'<a [^>]*href="https?://[^"]+"[^>]*>', page):
        if 'target="_blank"' not in a or 'rel="noopener noreferrer"' not in a:
            fails.append(f"G10 {name}: external link without new-tab security attributes: {a[:80]}")
    ed = json.loads((ROOT / "atlas-tools/supplier-gallery" / cfgp["editorial"]).read_text())
    for nm, body in cards:
        nm = unesc(nm)
        if "pn-sg-loc" in body or "<dt>Made in" in body or "<dt>Registered" in body or "<dt>Based" in body:
            b = (ed["makers"].get(nm) or {}).get("base")
            if not b or not b.get("evidence") or nm == "OGNYX":
                fails.append(f"G11 {name} {nm}: location shown without authorised evidence")
    shown = {unesc(n) for n, _ in cards}
    if cfgp["directory"] == "full":
        if shown != names:
            fails.append(f"G5 {name}: gallery makers {sorted(shown ^ names)} differ from the live Discovery")
    else:
        if not shown <= names:
            fails.append(f"G5 {name}: gallery shows makers not on the live Discovery: {sorted(shown - names)}")
        licensed = {m for m, src in leads.items() if src in AUTH and norm(AUTH[src][0]) == norm(m)}
        if shown != licensed:
            fails.append(f"G5 {name}: featured {sorted(shown)} != every licensed maker {sorted(licensed)} (founder D1)")
        if "pn-sg-entry" in page or "<details" in page:
            fails.append(f"G5 {name}: a duplicate supplier directory is present (founder D3)")
        jumps = re.findall(r'<a class="pn-sg-all" href="([^"]+)" data-sg-jump>', page)
        if not jumps or any(h != "#explore-makers" for h in jumps) or 'id="explore-makers"' not in full:
            fails.append(f"G5 {name}: 'View all' does not go to the page's Maker Explorer")
        for nm, body in cards:
            srcs = [unesc(x) for x in re.findall(r'<img src="([^"]+)"', body)]
            doms = {d.lower() for x in srcs if x in AUTH for d in AUTH[x][2]}
            for h in re.findall(r'<a [^>]*href="(https?://[^"]+)"', body):
                host = (urlparse(unesc(h)).hostname or "").lower()
                if not any(host == d or host.endswith("." + d) for d in doms):
                    fails.append(f"G14 {name} {unesc(nm)}: external link {h} is off the granted domain")
        if any("image" in (v or {}) for v in ed["makers"].values()):
            fails.append(f"G13 {name}: editorial image override present (founder D4)")
    if name == "discovery-garden-retreat.html" and ("IMG_2531" in page or "IMG_8495" not in page):
        fails.append("G12 Tanktribe image is not the CORE photograph IMG_8495")
    if re.search(r'href="[^"]*-preview\.html', page):
        fails.append(f"G8 {name}: link to a private supplier preview")
    if re.search(r"\.pn-sg[^{]*img[^{]*\{[^}]*(object-fit\s*:\s*cover|clip-path|border-radius)", css):
        fails.append("G4 CSS crops or alters supplier images")
    return fails, len(cards)


def stray_galleries():
    return [f"G9 gallery found on {f.name}: not a configured page" for f in ROOT.glob("*.html")
            if f.name not in PAGES and "data-pn-supplier-gallery" in f.read_text(errors="ignore")]


GR_TANK = "https://images.squarespace-cdn.com/content/v1/67ac8d737a7c665f57f5babe/2d930a20-ec94-4b5f-8af4-159501335d62/IMG_8495.jpg"
MUTATIONS = {
    "discovery-garden-retreat.html": lambda p, c: {
        "G1 unapproved image": (p.replace(GR_TANK, GR_TANK.replace("IMG_8495", "IMG_9999"), 1), c),
        "G1 unrecorded size variant": (p.replace("IMG_8495.jpg?format=1000w", "IMG_8495.jpg?format=2500w", 1), c),
        "G2 credit removed": (p.replace(">© OGNYX<", ">OGNYX<", 1), c),
        "G3 medium relabelled": (p.replace('pn-sg-kind">Visualisation', 'pn-sg-kind">Photograph', 1), c),
        "G4 crop in CSS": (p, c + "\n.pn-sg-mount img{ object-fit:cover; }"),
        "G5 invented supplier": (p.replace('aria-label="Pineca Ireland"', 'aria-label="Invented Saunas Ltd"', 1), c),
        "G6 unlabelled sponsor": (p.replace('data-sg-placement="editorial"', 'data-sg-placement="sponsored"', 1), c),
        "G7 disclosure removed": (re.sub(r'<span class="pn-sg-tag pn-sg-tag--rel">[^<]*</span>', "", p), c),
        "G8 preview link": (p.replace('href="https://www.tanktribe.ie/"', 'href="tanktribe-preview.html"', 1), c),
        "G8 endorsement": (p.replace("Outdoor saunas.</p>", "The best outdoor saunas.</p>", 1), c),
        "G10 link security dropped": (p.replace('rel="noopener noreferrer" target="_blank"', 'target="_blank"', 1), c),
        "G11 OGNYX location shown": (p.replace('aria-label="OGNYX"><figure class="pn-sg-fig">', 'aria-label="OGNYX"><p class="pn-sg-loc"><b>Registered in</b> Bray</p><figure class="pn-sg-fig">', 1), c),
        "G12 Carlsberg image back": (p.replace("2d930a20-ec94-4b5f-8af4-159501335d62/IMG_8495.jpg", "ab9c9630-7b25-441f-9559-b711ff7f6d5b/IMG_2531.JPG"), c),
        "G9 gallery moved after explorer": (p.replace(EXPLORER, "<p>moved</p>\n  " + EXPLORER, 1), c),
        "G9 gallery duplicated": (p.replace(B_END, B_END + "\n" + B_START + " dup -->", 1), c),
    },
    "discovery-living-in-the-garden.html": lambda p, c: {
        "G1 unlicensed image on a licensed maker": (p.replace("don-modular-home-forest-setting.webp", "some-other-don-image.webp", 1), c),
        "G1 image outside the governed prefix": (p.replace("https://static.wixstatic.com/media/fef4b6_", "https://static.wixstatic.com/media/aaaaaa_", 1), c),
        "G2 credit removed": (p.replace(">Image: Powersheds<", ">Powersheds<", 1), c),
        "G2 credit link to another domain": (p.replace('href="https://yardbox.co.uk/" rel="noopener noreferrer" target="_blank">Image: Yard Box', 'href="https://example.com/" rel="noopener noreferrer" target="_blank">Image: Yard Box', 1), c),
        "G3 Visualisation relabelled as Photograph": (p.replace('pn-sg-kind">Visualisation', 'pn-sg-kind">Photograph', 1), c),
        "G5 a licensed maker dropped": (re.sub(r'<li data-sg-placement="editorial"><article class="pn-sg-card" aria-label="Powersheds">.*?</article></li>', "", p, count=1, flags=re.S), c),
        "G5 invented supplier": (p.replace('aria-label="Yardbox"', 'aria-label="Invented Garden Rooms Ltd"', 1), c),
        "G5 duplicate directory added": (p.replace('</ul>\n</section>', '</ul><details class="pn-sg-grid-wrap"><summary>x</summary></details>\n</section>', 1), c),
        "G5 View all no longer goes to the explorer": (p.replace('href="#explore-makers" data-sg-jump', 'href="#suppliers" data-sg-jump', 1), c),
        "G6 unlabelled sponsor": (p.replace('data-sg-placement="editorial"', 'data-sg-placement="sponsored"', 1), c),
        "G8 endorsement": (p.replace("an insulated steel garden room.</p>", "the best insulated steel garden room.</p>", 1), c),
        "G10 link security dropped": (p.replace('rel="noopener noreferrer" target="_blank"', 'target="_blank"', 1), c),
        "G11 location without evidence": (p.replace('aria-label="Powersheds"><figure class="pn-sg-fig">', 'aria-label="Powersheds"><p class="pn-sg-loc"><b>Made in</b> Somewhere</p><figure class="pn-sg-fig">', 1), c),
        "G9 gallery moved after explorer": (p.replace(EXPLORER, "<p>moved</p>\n  " + EXPLORER, 1), c),
        "G9 gallery duplicated": (p.replace(B_END, B_END + "\n" + B_START + " dup -->", 1), c),
        "G14 Explore link off the granted domain": (p.replace('<a href="https://oodhouse.com/" rel="noopener noreferrer" target="_blank" aria-label=', '<a href="https://oodhouse.example.net/" rel="noopener noreferrer" target="_blank" aria-label=', 1), c),
    },
}


def main():
    css = CSS.read_text()
    total_fails, proved, planted = [], 0, 0
    total_fails += stray_galleries()
    for name in PAGES:
        page = (ROOT / name).read_text()
        fails, n = checks(name, page, css)
        print(f"{name}: real build {n} cards, {len(fails)} failures")
        for f in fails: print("  FAIL", f)
        total_fails += fails
        for label, (p, c) in MUTATIONS[name](page, css).items():
            planted += 1
            if p == page and c == css:
                print(f"  NOT PROVED {label} (mutation did not apply)"); continue
            f, _ = checks(name, p, c)
            ok = any(x.split(" ")[0] == label.split(" ")[0] for x in f)
            proved += ok
            print(f"  {'PROVED ' if ok else 'NOT PROVED'} {label}")
    for f in stray_galleries(): print("  FAIL", f)
    print(f"mutations: {proved}/{planted} caught")
    sys.exit(0 if not total_fails and proved == planted else 1)


if __name__ == "__main__":
    main()
