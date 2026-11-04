#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - GARDENHOUSE24 SUPPLIER SHOWCASE (founder authorisation, 4 Nov 2026).

Builds suppliers/gardenhouse24.html from supplier-preview-system/showcases/gardenhouse24/showcase.json.
Follows the Mobile Pods showcase (supplier-preview-system/build-mobile-pods-showcase.py); the gallery
cards on Garden Retreat and Living in the Garden are built by atlas-tools/build-supplier-gallery.py
("showcaseMakers"), not here.

RIGHTS. Builds only while image-rights-records.json holds a live, PUBLISHABLE record for
Gardenhouse24 Ireland whose required credit is the page credit, and every image URL is on the
supplier's domain or its declared delivery host + prefix. Images are hotlinked, so the Image
Rights Gate checks each one. Photographs and visualisations are labelled as such.

FACTS. guard() refuses a product with no supplier source, a price that is not a whole euro figure
from the data file, or an image tied to a product the data file does not list. Nothing is typed
into the page that is not in showcase.json.

JOURNEY. No outbound sales button. Option A browses within PlotNua; Option B is PlotNua's free
help: the existing Journey for garden rooms and cabins, the existing WhatsApp route for saunas and
hot tubs. Both carry the attribution marker via=gardenhouse24 / ref GH24.

Run: python3 supplier-preview-system/build-gardenhouse24-showcase.py [--check]
"""
import html, json, sys
from pathlib import Path
from urllib.parse import urlparse, quote

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "gardenhouse24"
DATA = json.loads((HERE / "showcase.json").read_text(encoding="utf-8"))
OUT = ROOT / "suppliers" / "gardenhouse24.html"
E = lambda s: html.escape(str(s), quote=True)
VIA = "via=gardenhouse24"
WHATSAPP = "https://wa.me/353834036695"   # PlotNua's own WhatsApp (atlas-tools/pn_header.py WHATSAPP)


def eur(n):
    return "€{:,}".format(int(n))


def guard():
    s = DATA["supplier"]
    recs = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
            if r["organisation_name"] == s["atlasName"]]
    if len(recs) != 1 or not recs[0]["permission_outcome"].startswith("Granted") or recs[0].get("public_visibility") != "PUBLISHABLE":
        sys.exit("FAIL: no live, publishable rights record for Gardenhouse24 Ireland; nothing is built")
    r = recs[0]
    if r["required_credit"] != s["credit"]:
        sys.exit("FAIL: the page credit differs from the rights record's required credit")
    scopes = [(d["host"], d["path_prefix"]) for d in r.get("permitted_delivery_hosts") or []]
    names = {p["name"] for p in DATA["products"]}
    ids = {i["id"] for i in DATA["images"]}
    for i in DATA["images"]:
        u = urlparse(i["origin"])
        on_domain = u.hostname in (r["permitted_domain"], "www." + r["permitted_domain"])
        if u.scheme != "https" or not (on_domain or any(u.hostname == h and u.path.startswith(px) for h, px in scopes)):
            sys.exit(f"FAIL: image {i['id']} is outside the grant's domain and delivery scope")
        if i["kind"] not in ("Photograph", "Visualisation") or i["product"] not in names or not i.get("sha256"):
            sys.exit(f"FAIL: image {i['id']}: medium, product or provenance missing")
        if i["kind"] == "Visualisation" and not i["alt"].startswith("Visualisation"):
            sys.exit(f"FAIL: image {i['id']}: a visualisation must say so in its alt text")
    for p in DATA["products"]:
        if not p["source"].startswith(s["website"]):
            sys.exit(f"FAIL: {p['name']}: specifications are not sourced to the supplier's site")
        if not isinstance(p["price"], int) or (p["installation"] is not None and not isinstance(p["installation"], int)):
            sys.exit(f"FAIL: {p['name']}: prices must be the whole-euro figures recorded in the data file")
        if set(p["images"]) - ids:
            sys.exit(f"FAIL: {p['name']}: unknown image slot")
    return r


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
<title>Gardenhouse24: garden rooms, log cabins, saunas and hot tubs | PlotNua</title>
<meta name="description" content="Gardenhouse24's Nordic-spruce garden rooms, log cabins, outdoor saunas and wood-fired hot tubs: listed prices, sizes and what each price includes, checked by PlotNua.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://plotnua.ie/suppliers/gardenhouse24.html">
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotnua-mark-master.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/suppliers/gardenhouse24.html">
<meta property="og:title" content="Gardenhouse24 | PlotNua">
<meta property="og:description" content="Garden rooms, log cabins, outdoor saunas and hot tubs from Gardenhouse24, with prices and sizes checked by PlotNua.">
<meta property="og:image" content="{og}">
<!-- Built by supplier-preview-system/build-gardenhouse24-showcase.py from showcase.json. Do not hand-edit.
     Supplier imagery: Gardenhouse24's written Instagram permission, 4 Nov 2026 (image-rights-records.json). -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../assets/identity/pn-premium-discovery.css">
<link rel="stylesheet" href="../assets/components/pn-two-option.css?v=1">
"""

CSS = """<style>
/* Gardenhouse24 showcase - scoped to .gh. The site's --p4-* identity tokens; no new identity.
   Supplier images are shown WHOLE: natural aspect ratio, never cropped, filtered, rounded or overlaid. */
.gh{ --ink:var(--p4-ivory,#F2EBE0); --soft:var(--p4-lime,#E7DED0); --stone:var(--p4-stone,#C2BDB5);
  --bronze:var(--p4-bronze-text,#B39272); --line:var(--p4-line2,#4A4B4F); --card:var(--p4-deep,#2C2E30);
  --well:var(--p4-well,#2D2E31); --serif:var(--p4-serif,'Instrument Serif',Georgia,serif);
  --sans:var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif); color:var(--soft); font-family:var(--sans); }
.gh *{ box-sizing:border-box; }
.gh-w{ max-width:1280px; margin:0 auto; padding:0 clamp(18px,3.4vw,48px); }
.gh-bar{ border-bottom:1px solid var(--line); }
.gh-bar .gh-w{ display:flex; justify-content:space-between; align-items:center; gap:16px; padding-top:16px; padding-bottom:16px; flex-wrap:wrap; }
.gh-brand{ font-family:var(--serif); font-size:26px; color:var(--ink); text-decoration:none; }
.gh-back{ display:flex; gap:18px; flex-wrap:wrap; }
.gh-back a{ font-size:14px; color:var(--soft); text-decoration:none; border-bottom:1px solid var(--line); padding-bottom:2px; }
.gh-back a:hover, .gh-brand:hover{ color:var(--ink); }
.gh-k{ margin:0 0 16px; font-size:11.5px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--bronze); }
.gh-hero{ padding:clamp(36px,6vw,84px) 0 clamp(30px,4vw,56px); }
.gh-hero .gh-w{ display:grid; grid-template-columns:minmax(0,4fr) minmax(0,7fr); gap:clamp(28px,4.5vw,72px); align-items:end; }
.gh-h1{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(44px,5.4vw,80px); line-height:1; letter-spacing:-.015em; overflow-wrap:anywhere; margin:0 0 22px; }
.gh-lede{ font-size:clamp(17px,1.45vw,20px); line-height:1.6; margin:0 0 26px; color:var(--ink); max-width:36ch; }
.gh-meta{ list-style:none; margin:0; padding:18px 0 0; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:8px 24px; font-size:13.5px; color:var(--stone); }
.gh-jump{ list-style:none; margin:26px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:10px; }
.gh-jump a{ display:inline-block; padding:9px 16px; border:1px solid var(--line); border-radius:999px; color:var(--ink); text-decoration:none; font-size:14px; }
.gh-jump a:hover{ border-color:var(--bronze); }
.gh-fig{ margin:0; }
.gh-fig img{ display:block; width:100%; height:auto; background:var(--well); }
.gh-cap{ margin:10px 0 0; font-size:12.5px; line-height:1.5; color:var(--stone); display:flex; gap:10px; flex-wrap:wrap; align-items:baseline; }
.gh-cap .gh-kind{ font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:10.5px; color:var(--bronze); }
.gh-cap a{ color:inherit; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.gh-sec{ padding:clamp(48px,7vw,104px) 0; border-top:1px solid var(--line); }
.gh-h2{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(32px,4vw,56px); line-height:1.06; margin:0 0 16px; }
.gh-p{ font-size:17px; line-height:1.75; max-width:64ch; margin:0; }
.gh-head{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(20px,5vw,80px); align-items:end; margin-bottom:clamp(30px,4vw,56px); }
/* the collection keeps every photograph's own shape */
.gh-col{ columns:3 300px; column-gap:clamp(16px,2vw,28px); }
.gh-col .gh-fig{ break-inside:avoid; margin:0 0 clamp(26px,3vw,40px); }
/* categories and products */
.gh-cat + .gh-cat{ margin-top:clamp(56px,7vw,96px); }
.gh-cat-h{ display:flex; justify-content:space-between; align-items:baseline; gap:20px; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:16px; margin-bottom:clamp(22px,3vw,34px); }
.gh-cat-h h3{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(28px,3vw,40px); margin:0; }
.gh-cat-h p{ margin:0; color:var(--stone); font-size:15px; }
.gh-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(340px,1fr)); gap:clamp(18px,2vw,28px); }
.gh-prod{ background:var(--card); border:1px solid var(--line); border-radius:22px; padding:clamp(18px,2.2vw,26px); display:flex; flex-direction:column; gap:14px; }
.gh-prod .gh-fig{ margin:0 0 4px; }
.gh-prod .gh-fig img{ border-radius:0; }
.gh-prod h4{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(26px,2.4vw,32px); margin:0; line-height:1.1; }
.gh-sum{ margin:0; font-size:15.5px; line-height:1.6; color:var(--ink); }
.gh-spec{ margin:0; display:grid; grid-template-columns:minmax(96px,128px) 1fr; border-top:1px solid var(--line); }
.gh-spec dt, .gh-spec dd{ padding:9px 0; border-bottom:1px solid var(--line); margin:0; font-size:14px; line-height:1.5; }
.gh-spec dt{ font-size:10.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--stone); padding-top:12px; padding-right:12px; }
.gh-price{ margin-top:auto; display:grid; grid-template-columns:1fr 1fr; gap:10px; padding-top:6px; }
.gh-price div{ border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.gh-price b{ display:block; font-family:var(--serif); font-weight:400; font-size:26px; color:var(--ink); line-height:1.1; }
.gh-price span{ display:block; font-size:12px; color:var(--stone); margin-top:4px; line-height:1.4; }
.gh-src{ margin:0; font-size:12px; color:var(--stone); }
.gh-src a{ color:inherit; }
.gh-costs{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:0 clamp(20px,3vw,44px); }
.gh-cost{ border-top:1px solid var(--line); padding:16px 0 20px; }
.pn-pd .gh .gh-cost h3, .pn-pd .gh .gh-note h3{ margin:0 0 8px; font-family:var(--sans); font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); line-height:1.4; }
.gh-cost p, .gh-note p{ margin:0; font-size:15px; line-height:1.7; }
.gh-fine{ margin:26px 0 0; font-size:13.5px; line-height:1.7; color:var(--stone); max-width:80ch; }
.gh-notes{ display:grid; grid-template-columns:1fr 1fr; gap:clamp(18px,3vw,44px); }
.gh-note{ border-top:1px solid var(--line); padding-top:16px; }
.gh-route .pn-two{ max-width:none; }
.gh-rec{ padding:34px 0 64px; border-top:1px solid var(--line); font-size:13.5px; line-height:1.7; color:var(--stone); }
.gh-rec p{ margin:0 0 6px; max-width:84ch; }
.gh-rec a{ color:inherit; }
@media (max-width:960px){ .gh-hero .gh-w, .gh-head, .gh-notes{ grid-template-columns:1fr; } }
@media (max-width:560px){ .gh-grid{ grid-template-columns:1fr; } .gh-spec{ grid-template-columns:1fr; } .gh-spec dt{ border-bottom:0; padding-bottom:0; } .gh-price{ grid-template-columns:1fr; } }
</style>
"""


def fig(i, first=False):
    s = DATA["supplier"]
    lazy = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
    return (f'<figure class="gh-fig"><img src="{E(i["origin"])}" alt="{E(i["alt"])}" width="{i["w"]}" height="{i["h"]}" '
            f'{lazy} decoding="async" referrerpolicy="no-referrer" data-pn-slot="{E(i["id"])}">'
            f'<figcaption class="gh-cap"><span class="gh-kind">{E(i["kind"])}</span>'
            f'<span>{E(i["caption"])} <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">{E(s["credit"])}</a></span></figcaption></figure>')


def lead(p, hero_id):
    """A product card's photograph: its first image that is not the page's hero (no image twice)."""
    return next((i for i in p["images"] if i != hero_id), None)


def product(p, I, hero_id):
    li = lead(p, hero_id)
    img = fig(I[li]) if li else ""
    dl = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in p["specs"])
    inst = (f'<div><b>{eur(p["installation"])}</b><span>Optional installation by the supplier</span></div>'
            if p["installation"] else '<div><b>&mdash;</b><span>No installation price is listed</span></div>')
    return (f'<article class="gh-prod" aria-label="{E(p["name"])}">{img}<h4>{E(p["name"])}</h4>'
            f'<p class="gh-sum">{E(p["summary"])}</p><dl class="gh-spec">{dl}<dt>Lead time</dt><dd>{E(p["leadTime"])}</dd></dl>'
            f'<div class="gh-price"><div><b>{eur(p["price"])}</b><span>Listed kit price, from</span></div>{inst}</div>'
            f'<p class="gh-src">As listed by {E(DATA["supplier"]["name"])} &middot; checked {int(p["checked"][8:10])} Nov 2026</p></article>')


def build():
    guard()
    s, I = DATA["supplier"], {i["id"]: i for i in DATA["images"]}
    hero = next(i for i in DATA["images"] if i["role"] == "hero")
    used = {lead(p, hero["id"]) for p in DATA["products"]}
    coll = [i for i in DATA["images"] if i["role"] == "collection" and i["id"] not in used]   # each image once
    cats = []
    for c in DATA["categories"]:
        ps = [p for p in DATA["products"] if p["category"] == c["id"]]
        cats.append(f'<section class="gh-cat" id="{E(c["id"])}" aria-labelledby="{E(c["id"])}-h"><div class="gh-cat-h">'
                    f'<h3 id="{E(c["id"])}-h">{E(c["title"])}</h3><p>{E(c["line"])}</p></div>'
                    f'<div class="gh-grid">{"".join(product(p, I, hero["id"]) for p in ps)}</div></section>')
    jump = "".join(f'<li><a href="#{E(c["id"])}">{E(c["title"])}</a></li>' for c in DATA["categories"])
    costs = "".join(f'<div class="gh-cost"><h3>{E(k)}</h3><p>{E(v)}</p></div>' for k, v in DATA["costs"]["items"])
    notes = "".join(f'<div class="gh-note"><h3>{E(k)}</h3><p>{E(v)}</p></div>' for k, v in DATA["considerations"])
    wa = WHATSAPP + "?text=" + quote("Hi PlotNua, I'm looking at Gardenhouse24 saunas and hot tubs on PlotNua and would like some help (ref GH24).")
    routes = (f'<li><a class="pn-two-b" href="../your-plot.html?discovery=garden-room&amp;{VIA}">A garden room or cabin <span aria-hidden="true">&rarr;</span></a></li>'
              f'<li><a class="pn-two-b" href="{E(wa)}" target="_blank" rel="noopener">A sauna or hot tub, on WhatsApp <span aria-hidden="true">&rarr;</span></a></li>')
    return (HEAD.replace("{og}", E(hero["origin"])) + CSS + f"""</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main" class="gh">
<nav class="gh-bar" aria-label="PlotNua"><div class="gh-w"><a class="gh-brand" href="../">PlotNua</a>
<div class="gh-back"><a href="../discovery-garden-retreat.html#suppliers"><span aria-hidden="true">&larr;</span> Garden Retreat</a><a href="../discovery-living-in-the-garden.html#suppliers"><span aria-hidden="true">&larr;</span> Living in the Garden</a></div></div></nav>

<section class="gh-hero" aria-labelledby="gh-h1"><div class="gh-w">
  <div>
    <p class="gh-k">Maker &middot; Garden Retreat &middot; Living in the Garden</p>
    <h1 class="gh-h1" id="gh-h1">{E(s["name"])}</h1>
    <p class="gh-lede">{E(DATA["intro"])}</p>
    <ul class="gh-meta" role="list"><li>Showroom in {E(s["showroom"])}</li><li>Nordic spruce, solid log construction</li><li>Delivered across mainland Ireland</li></ul>
    <ul class="gh-jump" role="list">{jump}</ul>
  </div>
  {fig(hero, first=True)}
</div></section>

<section class="gh-sec" id="collection" aria-labelledby="gh-col-h"><div class="gh-w">
  <div class="gh-head"><div><p class="gh-k">The collection</p><h2 class="gh-h2" id="gh-col-h">Built, finished and lived in.</h2></div>
  <p class="gh-p">{E(DATA["standfirst"])}</p></div>
  <div class="gh-col">{"".join(fig(i) for i in coll)}</div>
</div></section>

<section class="gh-sec" id="products" aria-labelledby="gh-pr-h"><div class="gh-w">
  <div class="gh-head"><div><p class="gh-k">The range</p><h2 class="gh-h2" id="gh-pr-h">Twelve products, four ways to use the garden.</h2></div>
  <p class="gh-p">Sizes, specifications and prices are the supplier&rsquo;s own, as listed on its website. PlotNua has not changed or added to them. Where the supplier publishes no photograph of a product, none is shown.</p></div>
  {"".join(cats)}
</div></section>

<section class="gh-sec" id="costs" aria-labelledby="gh-co-h"><div class="gh-w">
  <div class="gh-head"><div><p class="gh-k">Before you budget</p><h2 class="gh-h2" id="gh-co-h">{E(DATA["costs"]["title"])}</h2></div>
  <p class="gh-p">A listed price is the starting point, not the total. These are the costs the supplier itemises separately.</p></div>
  <div class="gh-costs">{costs}</div>
  <p class="gh-fine">{E(DATA["costs"]["note"])}</p>
</div></section>

<section class="gh-sec" id="considerations" aria-labelledby="gh-cn-h"><div class="gh-w">
  <div class="gh-head"><div><p class="gh-k">For Irish homeowners</p><h2 class="gh-h2" id="gh-cn-h">Worth checking first.</h2></div>
  <p class="gh-p">General points, not an assessment of your property.</p></div>
  <div class="gh-notes">{notes}</div>
</div></section>

<section class="gh-sec gh-route" id="enquire" aria-labelledby="gh-en-h"><div class="gh-w">
  <div class="gh-head"><div><p class="gh-k">Next step</p><h2 class="gh-h2" id="gh-en-h">Two ways to go from here.</h2></div>
  <p class="gh-p">Browse at your own pace, or let PlotNua help you work out which options suit how you&rsquo;d use the space, and then put you in touch with Gardenhouse24. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Compare Gardenhouse24 with other makers of garden rooms, saunas and hot tubs on PlotNua, side by side.</p>
      <a class="pn-two-a" href="../discovery-living-in-the-garden.html#explore-makers">Garden rooms and cabins <span aria-hidden="true">&rarr;</span></a>
      <a class="pn-two-a" href="../discovery-garden-retreat.html#suppliers">Saunas and hot tubs <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p><p class="pn-two-t">Tell us what you&rsquo;re looking for. We&rsquo;ll help you narrow the options and, when you&rsquo;re ready, introduce you to Gardenhouse24.</p>
      <ul class="pn-two-btns" role="list">{routes}</ul></div>
  </div>
  <p class="gh-fine">PlotNua is free for homeowners. PlotNua does not sell these products and cannot guarantee a supplier&rsquo;s availability or prices; you buy directly from the supplier. Inclusion here is not a recommendation, there is no paid placement, and recommendations cannot be bought.</p>
</div></section>

<footer class="gh-rec"><div class="gh-w">
  <p>Photography and visualisations: {E(s["name"])}, from <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">gardenhouse24.ie</a>, used with the supplier&rsquo;s permission. The supplier keeps ownership of its imagery.</p>
  <p>Product details checked against the supplier&rsquo;s website on 4 November 2026. Prices and specifications can change; confirm them with the supplier.</p>
</div></footer>
</main>
</body>
</html>
""")


def main():
    txt = build()
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print(("CHECK OK " if ok else "STALE    ") + str(OUT.relative_to(ROOT)))
        sys.exit(0 if ok else 1)
    OUT.write_text(txt, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
