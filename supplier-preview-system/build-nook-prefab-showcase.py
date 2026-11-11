#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - NOOK PREFAB SUPPLIER SHOWCASE (supplier-approved 11 Nov 2026).

Builds suppliers/nook-prefab.html. It is the private preview NOOK approved (6 Nov 2026, local only; built by
build-nook-preview.py in the founder's Documents/PlotNua/03 Website folder) made public, with NOOK's one
requested change and nothing else of substance:
  - build time 8-13 weeks ("the larger models can take a little longer"; Dimple Lalwani, NOOK, 11 Nov 2026,
    Gmail 1a1ca03c0388c1c8), replacing the brochure's 8-10 weeks;
  - the "awaiting NOOK's confirmation" preview notes removed, because NOOK confirmed the September 2026
    brochure starting prices in the same email, "with taxes, delivery and installation shown as extra";
  - the private-preview bar and noindex removed; the site's Cookiebot, GA4, canonical and share image added.

IMAGES. Six images NOOK supplied by email (6 Nov 2026, Gmail 1a1b08cf25c1fcb1) and NOOK's written permission to
host them on PlotNua (11 Nov 2026): optimised copies under assets/suppliers/nook-prefab/ (resize + recompress,
metadata stripped; original hashes in showcases/nook-prefab/image-copies.json). Each copy is declared in
image-provenance-records.json as a SUPPLIER_IMAGE pointing at NOOK's rights record (ORG-000209); the provenance
guard's P2 binds the bytes, P4 the live grant. One photograph, five visualisations, each labelled; every image
carries the credit "Image: NOOK Prefab" linked to nookprefab.com. No other imagery, no AI imagery.

COMMERCIAL. PlotNua has proposed referral terms; NOOK has NOT agreed them. guard() refuses any percentage,
discount, offer, exclusivity or commission wording on the page.

Run: python3 supplier-preview-system/build-nook-prefab-showcase.py [--check]
"""
import hashlib, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "nook-prefab"
OUT = ROOT / "suppliers" / "nook-prefab.html"
IMG = "assets/suppliers/nook-prefab"
CSS = (HERE / "showcase.css").read_text(encoding="utf-8")
E = lambda s: html.escape(str(s), quote=True)
PN = "../"
ORG = "NOOK Prefab (espacio NOOK)"
CREDIT = "Image: NOOK Prefab"
DOSSIER = "https://nookprefab.com/pages/garden-room-brochure"
SITE = "https://nookprefab.com/?utm_source=plotnua&amp;utm_medium=referral&amp;utm_campaign=supplier-showcase"
BUILD = "8–13 weeks"

IMAGES = {   # stem: (kind, w, h, alt, caption)   w, h = the hosted 1600 px copy
 "nook-20-oak-garden-room": ("Visualisation", 1600, 1600,
   "A NOOK 20 garden room clad in oak-toned timber, with a full-height sliding glass front and a covered porch opening onto a timber deck, set on a lawn among mature trees and flowering borders.",
   "NOOK 20 in oak, with porch and deck"),
 "nook-10-installed-spain": ("Photograph", 1600, 1066,
   "A finished NOOK 10 in timber cladding with a full-height sliding glass front, installed in a sunny walled garden in Spain, with outdoor sofas on the lawn.",
   "A NOOK 10 installed in Spain"),
 "nook-20-black-home-office": ("Visualisation", 1600, 1600,
   "A NOOK 20 clad in black timber at the end of a garden, its glass front showing a home office with a desk, shelving and track lighting, beside an olive tree in a planter.",
   "NOOK 20 in black, as a home office"),
 "nook-20-interior-kitchen-bathroom": ("Visualisation", 1600, 900,
   "Inside a NOOK 20: a pale oak-lined room with a sofa and rug, a fitted kitchen under a garden-facing window, a bathroom behind an oak partition, and glass doors to the garden.",
   "NOOK 20 inside · bathroom and kitchen layout"),
 "nook-20-interior-window-seat": ("Visualisation", 1600, 900,
   "Inside a NOOK 20: an oak-lined room with a cushioned window seat set into the joinery under a garden window, a sofa, a rug and floor cushions.",
   "NOOK 20 inside · with a built-in window seat"),
 "nook-20-interior-bedroom-bathroom": ("Visualisation", 1600, 900,
   "Inside a NOOK 20: a double bed against a pale wall with artwork, an oak-clad bathroom partition, a sofa and coffee table, and sliding glass doors onto the garden.",
   "NOOK 20 inside · the layout NOOK calls bedroom with bathroom"),
}
HERO = "nook-20-oak-garden-room"
GALLERY = ["nook-10-installed-spain", "nook-20-black-home-office", "nook-20-interior-kitchen-bathroom",
           "nook-20-interior-window-seat", "nook-20-interior-bedroom-bathroom"]

MODELS = [
 ("NOOK 10", "A room of your own", "One finished room, delivered in one piece: an office, a studio or a quiet room at the end of the garden.",
  [("Size", "4 × 2.50 m · about 10 m² footprint"), ("Usable space", "8.07 m²"),
   ("Heights", "2.50 m outside / 2.10 m inside, or 2.90 m outside / 2.50 m inside"),
   ("Inside", "Sliding glass doors, lighting, sockets and electrical panel, laminate floor, drainage channels, and pre-installation for heating and cooling"),
   ("Outside", "Thermo-treated timber in black or oak, or Millboard composite"),
   ("Built", f"In {BUILD}; craned in and connected in hours")],
  39000),
 ("NOOK 20", "Two rooms, one building", "Two NOOK 10s joined along the long side or end to end, so it suits a wide garden or a long, narrow one.",
  [("Size", "4 × 5 m or 8 × 2.50 m · about 20 m² footprint"), ("Usable space", "About 17.5 m²"),
   ("Layouts", "Open plan · bedroom with bathroom · bathroom and kitchen · bathroom and NOOK Corner"),
   ("Inside", "As NOOK 10, plus an optional bathroom, kitchen and built-in furniture"),
   ("Outside", "Thermo-treated timber in black or oak, or Millboard composite"),
   ("Built", f"In {BUILD}; craned in and connected in hours")],
  59000),
]
# SEO Opportunity 1 (founder approval, 11 Nov 2026): an internal PlotNua guide link, only on the model
# NOOK itself describes as "an office, a studio or a quiet room at the end of the garden" (NOOK 10).
GUIDE = {"NOOK 10": ("Using it as a garden office?", "Read PlotNua’s guide to garden offices in Ireland",
                     "../garden-offices-ireland.html")}
PRICE_NOTE = ("Starting price for the unit, ex works. Taxes (VAT), delivery, foundations and installation are extra; "
              "NOOK quotes the delivered price for your address.")


def pic(stem, eager=False):
    kind, w, h, alt, cap = IMAGES[stem]
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<figure class="nk-fig"><picture>'
            f'<source type="image/webp" srcset="{PN}{IMG}/{stem}-800.webp 800w, {PN}{IMG}/{stem}-1600.webp 1600w" sizes="(max-width:900px) 100vw, 50vw">'
            f'<img src="{PN}{IMG}/{stem}-1600.jpg" alt="{E(alt)}" width="{w}" height="{h}" {load} decoding="async" data-nook-image="{stem}" data-kind="{kind}"></picture>'
            f'<figcaption class="nk-cap"><span class="nk-kind">{kind}</span><span>{E(cap)} · '
            f'<a href="{SITE}" rel="noopener" target="_blank">{E(CREDIT)}</a></span></figcaption></figure>')


def model(m):
    name, kind, summ, spec, price = m
    size = dict(spec)["Size"].split(" · ")[0]
    usable = dict(spec)["Usable space"]
    dl = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in spec)
    return (f'<article class="nk-model no-plan" aria-label="{E(name)}"><div><h3>{E(name)}</h3><p class="nk-kind2">{E(kind)}</p>'
            f'<p class="nk-key"><span>{E(size)}</span><span>{E(usable)} usable</span></p>'
            f'<p class="nk-sum">{E(summ)}</p>'
            + (f'<p class="nk-guide">{E(GUIDE[name][0])} <a href="{E(GUIDE[name][2])}">{E(GUIDE[name][1])}</a></p>'
               if name in GUIDE else "") +
            f'<p class="nk-price">From €{price:,}</p><p class="nk-pnote">{E(PRICE_NOTE)}</p>'
            f'<details class="nk-more" open><summary>Full specifications</summary><dl class="nk-spec">{dl}</dl></details></div></article>')


EXTRA_CSS = """
.nk-buy{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:clamp(18px,3vw,40px); }
.nk-buy li{ border-top:1px solid var(--line); padding-top:16px; }
.nk-buy b{ display:block; margin:0 0 8px; font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); }
.nk-buy span{ font-size:15.5px; line-height:1.7; }
.nk-key{ display:flex; flex-wrap:wrap; gap:6px 18px; margin:0 0 14px; font-size:15px; color:var(--ink); }
.nk-key span + span::before{ content:"·"; margin-right:18px; color:var(--stone); }
.nk-model .nk-price{ margin:6px 0 10px; }
.nk-more{ margin-top:22px; }
.nk-more summary{ cursor:pointer; list-style:none; display:inline-flex; align-items:center; gap:10px; padding:10px 0; font-size:12px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--ink); border-bottom:1px solid var(--line); }
.nk-more summary::-webkit-details-marker{ display:none; }
.nk-more summary::after{ content:"+"; font-size:16px; color:var(--bronze); }
.nk-more[open] summary::after{ content:"\\2212"; }
.nk-more[open] summary{ margin-bottom:14px; }
.nk-guide{ margin:-4px 0 14px; font-size:14px; line-height:1.55; color:var(--stone); }
.nk-guide a{ color:var(--ink); text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.nk-p a, .nk-cap a{ color:inherit; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.nk-g2, .nk-g3{ display:grid; gap:clamp(16px,2vw,28px); align-items:start; }
.nk-g2{ grid-template-columns:3fr 2fr; margin-bottom:clamp(26px,3vw,44px); }
.nk-g3{ grid-template-columns:repeat(3,minmax(0,1fr)); }
@media (max-width:900px){ .nk-buy, .nk-g2, .nk-g3{ grid-template-columns:1fr; } }
"""

HEAD = """<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="UTF-8">
<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="8a5219c1-0f84-4a7e-9c17-d22fab76adc1" data-blockingmode="auto" type="text/javascript"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-PKKJ0RK6N8"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-PKKJ0RK6N8');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NOOK Prefab: factory-built garden rooms delivered finished | PlotNua</title>
<meta name="description" content="NOOK Prefab's NOOK 10 and NOOK 20 garden rooms, made in Spain and delivered finished: sizes, layouts, starting prices and what is extra, checked by PlotNua.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://plotnua.ie/suppliers/nook-prefab.html">
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotnua-mark-master.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/suppliers/nook-prefab.html">
<meta property="og:title" content="NOOK Prefab | PlotNua">
<meta property="og:description" content="Garden rooms made in Spain and delivered finished: NOOK 10 and NOOK 20, with sizes, layouts and starting prices.">
<meta property="og:image" content="https://plotnua.ie/assets/suppliers/nook-prefab/nook-20-oak-garden-room-1600.jpg">
<!-- Built by supplier-preview-system/build-nook-prefab-showcase.py. Do not hand-edit.
     Supplier imagery: NOOK Prefab's written permission to host its supplied images on PlotNua, 11 Nov 2026
     (image-rights-records.json, ORG-000209; image-provenance-records.json, SUPPLIER_IMAGE). -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../assets/identity/pn-premium-discovery.css">
<link rel="stylesheet" href="../assets/components/pn-two-option.css?v=1">
"""


def page():
    gallery = ('<div class="nk-g2">' + "".join(pic(s) for s in GALLERY[:2]) + '</div>'
               '<div class="nk-g3">' + "".join(pic(s) for s in GALLERY[2:]) + '</div>')
    models = "".join(model(m) for m in MODELS)
    return HEAD + f"""<style>{CSS}{EXTRA_CSS}</style>
</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main" class="nk">
<nav class="nk-bar" aria-label="PlotNua"><div class="nk-w"><a class="nk-brand" href="{PN}">PlotNua</a>
<a class="nk-back" href="{PN}discovery-living-in-the-garden.html#explore-makers"><span aria-hidden="true">&larr;</span> Living in the Garden</a></div></nav>

<section class="nk-hero" aria-labelledby="nk-h1"><div class="nk-w">
  <div>
    <p class="nk-k">Maker &middot; Living in the Garden</p>
    <h1 class="nk-h1" id="nk-h1">NOOK Prefab</h1>
    <p class="nk-lede">Garden rooms made in Spain and delivered finished: built in the factory, craned into your garden in one piece, and connected in hours.</p>
    <ul class="nk-meta" role="list"><li>Made in Spain</li><li>Sold direct to Irish homeowners</li><li>Arrives finished</li></ul>
  </div>
  {pic(HERO, eager=True)}
</div></section>

<section class="nk-sec" id="collection" aria-labelledby="nk-col-h"><div class="nk-w">
  <div class="nk-head"><div><p class="nk-k">The collection</p><h2 class="nk-h2" id="nk-col-h">Finished before it leaves the factory.</h2></div>
  <p class="nk-p">Every NOOK is built and fitted out in NOOK&rsquo;s production base in Spain, then delivered in one piece. Insulated walls, roof and floor and double glazing with argon are standard, so it can be used all year. Inside, the oak joinery, bathroom and kitchen are part of the building, not added on site.</p></div>
  {gallery}
</div></section>

<section class="nk-sec" id="models" aria-labelledby="nk-mod-h"><div class="nk-w">
  <div class="nk-head"><div><p class="nk-k">The models</p><h2 class="nk-h2" id="nk-mod-h">One room, or two.</h2></div>
  <p class="nk-p">The specifications and starting prices below are NOOK&rsquo;s own, from its 2026 brochure, confirmed by NOOK. PlotNua has not changed or added to them. <a href="{DOSSIER}" rel="noopener" target="_blank">See NOOK&rsquo;s full range and brochure</a>.</p></div>
  <div class="nk-models">{models}</div>
  <div class="nk-notes">
    <div class="nk-note"><h3>What the price covers</h3><p>NOOK&rsquo;s starting prices are for the finished unit at the factory. They are not a quote for your garden: taxes (VAT), delivery, foundations (screw piles, an existing level concrete base, or concrete pads) and installation are extra, and NOOK quotes them for your specific address. NOOK guarantees residential units for 3 years, plus each component&rsquo;s own manufacturer warranty.</p></div>
    <div class="nk-note"><h3>Planning in Ireland</h3><p>A garden room of up to 30&thinsp;m&sup2; can be built without planning permission in Ireland if it meets every condition, including that nobody lives or sleeps in it. NOOK designs a bedroom-with-bathroom layout, but using any garden building as somewhere to live or sleep needs planning permission. Check your plans with your local authority before you order.</p></div>
  </div>
</div></section>

<section class="nk-sec" id="ireland" aria-labelledby="nk-ie-h"><div class="nk-w">
  <div class="nk-head"><div><p class="nk-k">Buying from Ireland</p><h2 class="nk-h2" id="nk-ie-h">Direct from the maker.</h2></div>
  <p class="nk-p">NOOK is opening the Irish market itself. There is no distributor: you deal with NOOK from your first call to handover.</p></div>
  <ul class="nk-buy" role="list">
    <li><b>A price for your address</b><span>NOOK quotes the delivered price against your exact address, once it knows the access for the truck and crane.</span></li>
    <li><b>Arrives in one piece</b><span>Each NOOK is made in Spain in {BUILD}, arrives finished, and is craned into place.</span></li>
    <li><b>Your site checked first</b><span>Send NOOK a few photos of your garden and it will tell you what&rsquo;s possible before you commit.</span></li>
  </ul>
</div></section>

<section class="nk-sec nk-route" id="enquire" aria-labelledby="nk-en-h"><div class="nk-w">
  <div class="nk-head"><div><p class="nk-k">Next step</p><h2 class="nk-h2" id="nk-en-h">Is a NOOK right for your garden?</h2></div>
  <p class="nk-p">Before you contact any maker, PlotNua can help you work out what your garden can take and which options fit how you&rsquo;d use it. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Compare NOOK with other garden-room makers on PlotNua, side by side.</p>
      <a class="pn-two-a" href="{PN}discovery-living-in-the-garden.html#explore-makers">Browse makers and products <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p><p class="pn-two-t">Tell us what you&rsquo;re looking for. We&rsquo;ll use our Atlas research to help you find options that match your preferences and budget.</p>
      <ul class="pn-two-btns" role="list"><li><a class="pn-two-b" href="{PN}your-plot.html?discovery=garden-room&amp;via=nook-prefab">A garden room <span aria-hidden="true">&rarr;</span></a></li></ul></div>
  </div>
  <p class="nk-fine">PlotNua is free for homeowners. Inclusion here is not a recommendation, there is no paid placement, and recommendations cannot be bought.</p>
</div></section>

<footer class="nk-rec"><div class="nk-w">
  <p>Photograph and visualisations: NOOK Prefab, supplied to PlotNua and hosted with NOOK&rsquo;s permission, from <a href="{SITE}" rel="noopener" target="_blank">nookprefab.com</a>. NOOK keeps ownership of its imagery. Images marked &ldquo;Visualisation&rdquo; are architectural visualisations, not photographs.</p>
  <p>Product details and starting prices from NOOK&rsquo;s 2026 brochure (prices updated September 2026), confirmed by NOOK on 11 November 2026, with the build time NOOK gave PlotNua ({BUILD}). Prices and specifications can change; NOOK&rsquo;s proposal for your address prevails.</p>
  <p><a href="{PN}terms.html#legal-information">Terms &amp; legal information</a></p>
</div></footer>
</main>
<script>/* Full specifications start open on desktop and folded on phones. No storage, no tracking. */
if (window.matchMedia && window.matchMedia("(max-width:900px)").matches) {{
  document.querySelectorAll("details.nk-more").forEach(function (d) {{ d.removeAttribute("open"); }});
}}</script>
</body>
</html>
"""


def guard(s):
    fails = []
    rec = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
           if r["organisation_name"] == ORG]
    if len(rec) != 1 or not rec[0]["permission_outcome"].startswith("Granted") or rec[0].get("public_visibility") != "PUBLISHABLE":
        fails.append("no live, publishable rights record for NOOK Prefab")
    elif rec[0].get("required_credit") != CREDIT:
        fails.append("the page credit differs from the rights record's required credit")
    prov = {r["asset"]: r for r in json.loads((ROOT / "image-provenance-records.json").read_text(encoding="utf-8"))["records"]}
    for a in sorted(set(re.findall(r'(?:\.\./|https://plotnua\.ie/)(assets/suppliers/nook-prefab/[^"\s,]+)', s))):
        p = ROOT / a
        r = prov.get(a)
        if not p.exists() or not r or r.get("class") != "SUPPLIER_IMAGE" or r.get("sha256") != hashlib.sha256(p.read_bytes()).hexdigest():
            fails.append(f"{a} is not a declared, hash-bound SUPPLIER_IMAGE")
        elif rec and (r.get("rights_ref") or {}).get("organisation_code") != rec[0]["organisation_code"]:
            fails.append(f"{a} points at another organisation's grant")
    body = re.sub(r"<style>.*?</style>|<script.*?</script>|<!--.*?-->", "", s, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    if re.search(r"\d\s?%|\bdiscount|\bexclusiv|\bcommission|\breferral fee|\boffer\b|\bsave\b", text, re.I):
        fails.append("a rate, discount, offer, exclusivity or commission wording is on the page (NOOK has not agreed terms)")
    if re.search(r"\bhabitable\b|\bpermitted (dwelling|residen)|\bapproved (dwelling|home)|\blive[- ]in\b", text, re.I):
        fails.append("habitation wording")
    if re.search(r"8\s*[–-]\s*10 weeks|8 to 10 weeks", text): fails.append("the superseded 8-10 week build time")
    if text.count(BUILD) != 4: fails.append("the 8-13 week build time must appear on both models, in Buying from Ireland and in the footer")
    if re.search(r"preview|awaiting", text, re.I): fails.append("preview wording left on the public page")
    for m in re.finditer(r"<img [^>]*>", s):
        if 'data-kind="Photograph"' not in m.group(0) and 'data-kind="Visualisation"' not in m.group(0): fails.append("image without a kind")
    if len(set(re.findall(r'data-nook-image="([^"]+)"', s))) != 6 or s.count("data-nook-image=") != 6: fails.append("not exactly the six supplied images, once each")
    if len(re.findall(r'data-kind="Photograph"', s)) != 1: fails.append("only the NOOK 10 in Spain is a photograph")
    if s.count(f">{CREDIT}</a>") != 6: fails.append("every image must carry the linked credit")
    if s.count('<details class="nk-more" open>') != 2: fails.append("specifications must stay on the page (expandable)")
    if "googletagmanager.com/gtag/js?id=G-PKKJ0RK6N8" not in s or 'id="Cookiebot"' not in s or 'content="index, follow"' not in s:
        fails.append("Cookiebot, GA4 and index,follow are required on a public page")
    for t in ("From €39,000", "From €59,000", "8.07 m²", "17.5 m²", "ex works", "Taxes (VAT), delivery, foundations and installation are extra",
              "NOOK quotes the delivered price for your address", "craned", "no distributor", "somewhere to live or sleep needs planning permission"):
        if t not in text: fails.append("missing verified fact: " + t)
    if text.count(PRICE_NOTE) != 2: fails.append("each price must carry its exclusions immediately beneath it")
    return fails


def main():
    s = page()
    f = guard(s)
    if f:
        sys.exit("REFUSED: " + "; ".join(f))
    planted = ((s.replace("From €39,000", "From €39,000 · 5% off"), "rate/discount"),
               (s.replace("there is no paid placement", "NOOK pays PlotNua a commission"), "commission"),
               (s.replace(BUILD, "8–10 weeks", 1), "old build time"),
               (s.replace("somewhere to live or sleep", "habitable space"), "habitation"),
               (s.replace('data-kind="Visualisation"', 'data-kind="Photograph"', 1), "photo count"),
               (s.replace(f">{CREDIT}</a>", ">NOOK</a>", 1), "credit"),
               (s.replace(PRICE_NOTE, "Price includes delivery.", 1), "price exclusions"),
               (s.replace("nook-20-oak-garden-room-1600.jpg", "nook-20-oak-garden-room-1600-x.jpg", 1), "undeclared image"),
               (s.replace('id="Cookiebot"', 'id="cb"'), "consent"))
    for bad, why in planted:
        assert guard(bad), "guard missed: " + why
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == s
        print(("CHECK OK " if ok else "STALE    ") + str(OUT.relative_to(ROOT)))
        sys.exit(0 if ok else 1)
    OUT.write_text(s, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} · guard OK, {len(planted)}/{len(planted)} planted faults caught")


if __name__ == "__main__":
    main()
