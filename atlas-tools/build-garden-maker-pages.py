#!/usr/bin/env python3
"""Build two bounded, text-only maker guides; --check writes nothing.

Public primary-source facts are frozen in maker-pages/source-evidence.json.
No network, Airtable, matching, supplier eligibility or image-rights write.
Drafts are noindex/nofollow and absent from discovery surfaces. Published pages
require the founder's narrow approval and the existing rights-first publication
derivation. Existing identity/header renderers are reused. No permission is invented.
"""
import datetime as dt
import importlib.util
import json
import re
import sys
import subprocess
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "atlas-tools/maker-pages"
PARENT = "discovery-living-in-the-garden.html"
SOURCE_URLS = {
    "concept-standard": "https://www.conceptmodular.ie/showcase/standard-office",
    "concept-signature": "https://www.conceptmodular.ie/showcase/signature-office",
    "concept-collection": "https://www.conceptmodular.ie/solutions",
    "all-in-one-single": "https://allinonecabins.ie/single-room-cabins/",
}
PAGES = {
    "concept-modular-garden-offices.html": {
        "template": "concept-modular.html",
        "title": "Concept Modular Garden Offices: Prices & Specifications | PlotNua",
        "h1": "Concept Modular garden offices",
        "description": "Compare Concept Modular's Standard and Signature garden offices: published prices excluding VAT, fit-out differences and site costs to confirm.",
        "lead": "Standard or Signature? Compare the published office specifications, then check what it will cost to put one in your garden.",
        "about": "Concept Modular garden offices",
    },
    "all-in-one-cabins-garden-rooms.html": {
        "template": "all-in-one-cabins.html",
        "title": "All In One Cabins: Garden Cabin Prices & Sizes | PlotNua",
        "h1": "All In One Cabins: Boderg, Corry and Kilglass",
        "description": "Compare the Boderg, Corry and Kilglass cabins: published starting prices, kit and installation questions, VAT uncertainty and a Corry size discrepancy.",
        "lead": "Three flatpack cabins, three starting prices. Work out what each quotation needs to include before choosing a garden room.",
        "about": "All In One Cabins single-room cabins",
    },
}


def publication_approved(evidence):
    state = evidence["publication_status"]
    if state == "DRAFT":
        return False
    if state != "PUBLISHED" or evidence["listing_basis"] != "PUBLIC_INFORMATION_TEXT_ONLY":
        raise ValueError("unknown publication state or editorial basis")
    register = json.loads((DATA / "publication.json").read_text())
    decision = register["decision"]
    if (decision["state"] != "APPROVED" or decision["scope"] != "Garden Rooms"
            or decision["authorised_by"] != "Colin MacAulay"
            or decision["decision_date"] != "2026-10-26"
            or set(decision["pages"]) != set(PAGES)):
        raise ValueError("the two exact maker guides require their narrow founder approval")
    expected = {"All In One Cabins", "Concept Modular"}
    if {o["name"] for o in register["organisations"]} != expected:
        raise ValueError("publication scope must contain exactly the two approved makers")
    # Import the canonical rights-first derivation. A new objection, decline or
    # review hold in a rights record wins over the editorial register.
    js = '''import fs from 'node:fs';
import {derivePublicInformationListing} from './atlas-tools/publication-gate.mjs';
const reg=JSON.parse(fs.readFileSync(0,'utf8'));
const rows=JSON.parse(fs.readFileSync('image-rights-records.json','utf8')).records;
const results=reg.organisations.map(o=>({name:o.name,...derivePublicInformationListing(o.name,rows,reg,'Garden Rooms')}));
console.log(JSON.stringify(results));'''
    result = subprocess.run(["node", "--input-type=module", "-e", js], cwd=ROOT,
                            input=json.dumps(register), text=True, capture_output=True, check=True)
    results = json.loads(result.stdout)
    if any(r["visibility"] != "PUBLISHABLE" or r["basis"] != "PUBLIC_INFORMATION" for r in results):
        raise ValueError("editorial publication refused by the rights-first gate: "+result.stdout.strip())
    return True


def load_identity():
    spec = importlib.util.spec_from_file_location("maker_identity", ROOT / "atlas-tools/build-identity-stage1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HOME_THEME = re.search(r'<meta name="theme-color" content="([^"]+)"',
                                  (ROOT / "index.html").read_text()).group(1)
    return module


def render(page, profile, evidence, identity, published=False):
    checked = dt.date.fromisoformat(evidence["checked"])
    checked_long = f"{checked.day} {checked:%B %Y}"
    facts, sources = evidence["facts"], evidence["sources"]
    eur = lambda n: "€" + format(n, ",")
    body = Template((DATA / profile["template"]).read_text()).substitute(
        checked_long=checked_long,
        standard_price=eur(facts["concept-standard"]["price_eur"]),
        signature_price=eur(facts["concept-signature"]["price_eur"]),
        site_works=eur(facts["concept-site-works"]["from_eur"])+"–"+eur(facts["concept-site-works"]["to_eur"]),
        boderg_price=eur(facts["all-in-one-single"]["boderg_eur"]),
        corry_price=eur(facts["all-in-one-single"]["corry_eur"]),
        kilglass_price=eur(facts["all-in-one-single"]["kilglass_eur"]),
        standard_url=escape(sources["concept-standard"]["url"], quote=True),
        signature_url=escape(sources["concept-signature"]["url"], quote=True),
        collection_url=escape(sources["concept-collection"]["url"], quote=True),
        single_room_url=escape(sources["all-in-one-single"]["url"], quote=True),
    )
    # Reuse the released consent/GA configuration and canonical search component.
    released = (ROOT / "garden-room-prices-ireland.html").read_text()
    consent = released.split("<head>\n", 1)[1].split('<meta charset="UTF-8">', 1)[0]
    rail = re.search(r"<!-- PLOTNUA SEARCH RAIL v1 · BEGIN.*?<!-- PLOTNUA SEARCH RAIL v1 · END -->", released, re.S).group()
    url = "https://plotnua.ie/" + page
    robots = "index, follow" if published else "noindex, nofollow"
    review = "" if published else '<p class="mp-review"><strong>Review draft.</strong> This page has not been approved for publication.</p>'
    graph = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": url+"#webpage", "url": url,
         "name": profile["h1"], "description": profile["description"],
         "inLanguage": "en-IE", "dateModified": evidence["checked"],
         "about": {"@type": "Thing", "name": profile["about"]},
         "isPartOf": {"@id": "https://plotnua.ie/#website"},
         "publisher": {"@id": "https://plotnua.ie/#organisation"},
         "breadcrumb": {"@id": url+"#breadcrumb"}},
        {"@type": "BreadcrumbList", "@id": url+"#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/"},
            {"@type": "ListItem", "position": 2, "name": "Living in the Garden", "item": "https://plotnua.ie/"+PARENT},
            {"@type": "ListItem", "position": 3, "name": profile["h1"]}]}]}
    raw = f'''<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="UTF-8">
{consent}<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(profile['title'])}</title>
<meta name="description" content="{escape(profile['description'], quote=True)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#1F3B2E">
<link rel="icon" href="/favicon.ico">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:title" content="{escape(profile['title'], quote=True)}">
<meta property="og:description" content="{escape(profile['description'], quote=True)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="en_IE">
<link rel="stylesheet" href="assets/identity/pn-maker-guide.css">
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, indent=2)}</script>
</head>
<body>
<a href="index.html" class="brand-mark" aria-label="PlotNua home"><img src="assets/brand/plotnua-icon-transparent.svg" alt="" width="34" height="34"></a>
{rail}
<main id="pn-main">
  <div class="mp-hero">
    <a class="mp-parent" href="{PARENT}">← Explore Living in the Garden</a>
    <div class="pd-kicker">A PlotNua Maker Guide · Part of Living in the Garden</div>
    <h1>{escape(profile['h1'])}</h1>
    <p class="mp-lead">{escape(profile['lead'])}</p>
    <p class="mp-meta">Published sources checked <time datetime="{evidence['checked']}">{checked_long}</time></p>
{review}
  </div>
{body}
  <section class="pd-section mp-section" id="explore-the-discovery">
    <div class="pd-wrap">
      <div class="pd-card pd-card--raised mp-copy">
        <div class="pd-kicker">Keep exploring</div>
        <h2 class="pd-h3">What could work in your garden?</h2>
        <p>Return to <a href="{PARENT}">Living in the Garden</a> for the wider picture,
          <a href="{PARENT}#explore-makers">explore the researched makers</a>, or use the
          <a href="garden-room-prices-ireland.html#quote-checklist">garden room quote checklist</a>
          to compare what different prices cover.</p>
      </div>
    </div>
  </section>
</main>
<footer class="mp-foot" aria-label="PlotNua information">
  <a href="about.html">About PlotNua</a><a href="contact.html">Contact</a>
  <a href="privacy.html">Privacy</a><a href="terms.html">Terms</a>
</footer>
<script src="assets/identity/pn-premium.js" defer></script>
</body>
</html>
'''
    return identity.build(page, raw)


def main():
    if set(sys.argv[1:]) - {"--check"}:
        raise ValueError("only --check is supported")
    evidence = json.loads((DATA / "source-evidence.json").read_text())
    if evidence["supplier_permission_asserted"] is not False or evidence["imagery"] != "none":
        raise ValueError("no permission assertion and no supplier imagery are required")
    published = publication_approved(evidence)
    age = (dt.date.today() - dt.date.fromisoformat(evidence["checked"])).days
    if not 0 <= age <= 30:
        raise ValueError("recheck the primary pages: evidence is future-dated or more than 30 days old")
    if set(evidence["sources"]) != set(SOURCE_URLS):
        raise ValueError("the four reviewed primary sources are required")
    for key, url in SOURCE_URLS.items():
        source = evidence["sources"][key]
        if source["url"] != url or source["verification"] != "DIRECT_PRIMARY_HTTP_200" or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ValueError("source identity, verification or snapshot hash differs: "+key)
    for key in ["concept-standard", "concept-signature", "concept-site-works"]:
        if evidence["facts"][key]["vat"] != "EXCLUDED":
            raise ValueError("Concept Modular VAT must remain excluded")
    cabins = evidence["facts"]["all-in-one-single"]
    if cabins["vat"] != "UNCONFIRMED" or cabins["price_type"] != "FROM" or cabins["corry_area_conflict_unresolved"] is not True:
        raise ValueError("cabin starting-price, VAT and unresolved-size limitations must survive")
    identity = load_identity()
    sitemap = (ROOT / "sitemap.xml").read_text()
    parent = (ROOT / PARENT).read_text()
    search = (ROOT / "search-index-v1.json").read_text()
    outputs = {}
    for page, profile in PAGES.items():
        if not published and any(page in text for text in [sitemap, parent, search]):
            raise ValueError(f"draft is exposed through a public discovery surface: {page}")
        if published and "--check" in sys.argv:
            routes = [r for r in json.loads(search)["records"] if r.get("route") == page]
            if (sitemap.count("<loc>https://plotnua.ie/"+page+"</loc>") != 1
                    or parent.count('href="'+page+'"') != 1
                    or len(routes) != 1 or routes[0]["type"] != "possibility"):
                raise ValueError("published guide needs exactly one sitemap entry, parent link and informational Search record: "+page)
        outputs[page] = render(page, profile, evidence, identity, published)
    changed = [p for p, text in outputs.items() if not (ROOT / p).exists() or (ROOT / p).read_text() != text]
    if "--check" in sys.argv:
        if changed: raise ValueError("generated guide differs: "+", ".join(changed))
    else:
        for page in changed: (ROOT / page).write_text(outputs[page])
    print(f"MAKER PILOT · {'CHECK OK' if '--check' in sys.argv else 'BUILT'}: two {'published text-only guides' if published else 'noindex review drafts'}; rights-first gate preserved")


if __name__ == "__main__":
    try: main()
    except (ValueError, KeyError) as e:
        print("MAKER PILOT · REFUSED: "+str(e)); sys.exit(2)
