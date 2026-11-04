#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - DON MODULAR HOMES SUPPLIER SHOWCASE (founder instruction, 4 Nov 2026: private supplier preview).

Builds suppliers/don-modular-homes.html from supplier-preview-system/showcases/don-modular-homes/showcase.json,
reusing the shared supplier-showcase styling.

RIGHTS. Don Modular Homes' written YES of 2 Oct 2026 (C2-FIRST-DON-MODULAR-20261002). Every governed Don
image is a COMPUTER-GENERATED VISUALISATION: each is labelled "Visualisation" and the page says so
plainly; none may be presented as a photograph of a completed build. Hotlinked unmodified from
donmodularhomes.ie/images/, credited '(c) Don Modular Homes'.

FACTS. The five Atlas product records. Prices: the supplier's single published rate (EUR 2,400/m2 fully
fitted) and its published size ranges, re-checked on the supplier's prices page on 4 Nov 2026. VAT
treatment is not stated and site works are quoted separately; both are said on the page.

PREVIEW. Built noindex with a private-preview band while PREVIEW = True.

Run: python3 supplier-preview-system/build-don-modular-homes-showcase.py [--check]
"""
import html, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "don-modular-homes"
DATA = json.loads((HERE / "showcase.json").read_text(encoding="utf-8"))
E = lambda s: html.escape(str(s), quote=True)
LIVE = "https://plotnua.ie/"
VIA = "via=don-modular-homes"   # attribution marker on PlotNua's own guided route (ignored by the Journey)


def img_src(img, bundle):
    return img["local"] if bundle else img["origin"]


def imgs():
    return {i["id"]: i for i in DATA["images"]}



DOC = None


def guard():
    """Facts guard: Atlas products only; every image a supplier visualisation labelled as one; prices
    only the supplier's published rate and ranges (Atlas pricing rows, re-checked 4 Nov 2026)."""
    s = DATA["supplier"]
    for i in DATA["images"]:
        for k in ("origin", "sourcePage", "sha256", "alt", "kind", "atlasAsset", "caption"):
            if not i.get(k):
                sys.exit(f"FAIL: image {i['id']} lacks {k}")
        if not i["origin"].startswith("https://donmodularhomes.ie/images/"):
            sys.exit(f"FAIL: image {i['id']} is not from the supplier's own site")
        if i["kind"] != "Visualisation" or not i["alt"].startswith("Visualisation:"):
            sys.exit(f"FAIL: image {i['id']} must be labelled as a visualisation")
    allowed = {"From €60,480 (25.2 m²) to €88,320 (36.8 m²)", "From €60,480 to €95,040", "From €96,000 to €132,480",
               "From €168,000 to €264,000", "From €240,000 to €336,000"}
    for p in DATA["products"]:
        if dict(p["specs"]).get("Price") not in allowed:
            sys.exit(f"FAIL: {p['name']}: price is not one the supplier publishes")
        if not p["source"].startswith(s["website"]):
            sys.exit(f"FAIL: {p['name']} specs are not sourced to the supplier site")
    if DATA["rate"] != "€2,400 per m², fully fitted":
        sys.exit("FAIL: the published rate has changed; re-check the supplier's prices page")
    rec = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
           if r["organisation_name"] == s["name"]]
    if len(rec) != 1 or not rec[0]["permission_outcome"].startswith("Granted"):
        sys.exit("FAIL: no live rights record for Don Modular Homes; nothing is built")
    if rec[0]["required_credit"] != s["credit"]:
        sys.exit("FAIL: the page credit differs from the rights record's required credit")


PREVIEW = True   # founder: private supplier preview first. Set False (and rebuild) when the founder releases it.


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<title>{title}</title>
<!-- PRIVATE STAGING PAGE. Built by supplier-preview-system/build-don-modular-homes-showcase.py. Not linked, not in the
     sitemap, not published. Supplier photographs are under a publication hold (showcase.json). Do not hand-edit. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{css}assets/identity/pn-identity.css">
<link rel="stylesheet" href="{css}assets/identity/pn-premium-discovery.css">
"""

CSS = """<style>
/* Don Modular Homes showcase - scoped to .mp (shared supplier-showcase styling). Uses the site's --p4-* identity tokens. Supplier
   images are shown WHOLE: natural aspect ratio, never cropped, filtered, rounded or overlaid. */
.mp{ --ink:var(--p4-ivory,#F2EBE0); --soft:var(--p4-lime,#E7DED0); --stone:var(--p4-stone,#C2BDB5);
  --bronze:var(--p4-bronze-text,#B39272); --line:var(--p4-line2,#4A4B4F); --card:var(--p4-deep,#2C2E30);
  --well:var(--p4-well,#2D2E31); --serif:var(--p4-serif,'Instrument Serif',Georgia,serif);
  --sans:var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif);
  color:var(--soft); font-family:var(--sans); }
.mp *{ box-sizing:border-box; }
.mp-w{ max-width:1240px; margin:0 auto; padding:0 clamp(18px,3.4vw,44px); }
.mp-bar{ border-bottom:1px solid var(--line); }
.mp-bar .mp-w{ display:flex; justify-content:space-between; align-items:center; gap:16px; padding-top:16px; padding-bottom:16px; }
.mp-brand{ font-family:var(--serif); font-size:26px; color:var(--ink); text-decoration:none; letter-spacing:-.01em; }
.mp-back{ font-size:14px; color:var(--soft); text-decoration:none; border-bottom:1px solid var(--line); padding-bottom:2px; }
.mp-back:hover, .mp-brand:hover{ color:var(--ink); }
.mp-hold{ border-bottom:1px solid var(--line); font-size:12.5px; letter-spacing:.04em; color:var(--stone); }
.mp-hold .mp-w{ padding-top:12px; padding-bottom:12px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.mp-hold b{ font-weight:700; letter-spacing:.16em; text-transform:uppercase; font-size:11px; color:var(--bronze); }
.mp-k{ margin:0 0 18px; font-size:11.5px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--bronze); }
.mp-hero{ padding:clamp(40px,7vw,96px) 0 clamp(36px,5vw,72px); }
.mp-hero .mp-w{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(28px,5vw,80px); align-items:center; }
.mp-h1{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(44px,6.4vw,92px); line-height:1.02; letter-spacing:-.01em; margin:0 0 22px; }
.mp-lede{ font-size:clamp(17px,1.5vw,20px); line-height:1.6; max-width:34ch; margin:0 0 28px; color:var(--ink); }
.mp-meta{ list-style:none; margin:0; padding:18px 0 0; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:8px 26px; font-size:13.5px; color:var(--stone); }
.mp-fig{ margin:0; }
.mp-fig img{ display:block; width:100%; height:auto; background:var(--well); }
.mp-hero .mp-fig img{ max-height:78vh; width:auto; max-width:100%; margin-left:auto; }
.mp-cap{ margin:10px 0 0; font-size:12.5px; line-height:1.5; color:var(--stone); display:flex; gap:10px; flex-wrap:wrap; }
.mp-cap .mp-kind{ font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:10.5px; color:var(--bronze); padding-top:2px; }
.mp-cap a{ color:inherit; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.mp-hero .mp-cap{ justify-content:flex-end; }
.mp-sec{ padding:clamp(48px,7vw,104px) 0; border-top:1px solid var(--line); }
.mp-h2{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(32px,4vw,54px); line-height:1.08; margin:0 0 18px; }
.mp-p{ font-size:17px; line-height:1.75; max-width:62ch; margin:0; }
.mp-head{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(20px,5vw,80px); align-items:end; margin-bottom:clamp(30px,4vw,56px); }
/* the collection: masonry by columns, so every photograph keeps its own shape */
.mp-col{ columns:3 300px; column-gap:clamp(16px,2vw,28px); }
.mp-col .mp-fig{ break-inside:avoid; margin:0 0 clamp(26px,3vw,40px); }
/* models */
.mp-models{ display:grid; gap:clamp(18px,2vw,28px); }
.mp-model{ display:grid; grid-template-columns:minmax(0,7fr) minmax(0,5fr); gap:clamp(20px,4vw,56px); background:var(--card); border:1px solid var(--line); border-radius:24px; padding:clamp(22px,3.4vw,44px); }
.mp-model.no-plan{ grid-template-columns:1fr; }
.mp-model h3{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(30px,3.2vw,42px); margin:0 0 6px; line-height:1.1; }
.mp-model .mp-kind2{ margin:0 0 16px; font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); }
.mp-model .mp-sum{ font-size:16.5px; line-height:1.65; margin:0 0 22px; max-width:56ch; color:var(--ink); }
.mp-spec{ margin:0; display:grid; grid-template-columns:minmax(110px,150px) 1fr; border-top:1px solid var(--line); }
.mp-spec dt, .mp-spec dd{ padding:11px 0; border-bottom:1px solid var(--line); margin:0; font-size:14.5px; line-height:1.55; }
.mp-spec dt{ font-size:11px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--stone); padding-top:14px; padding-right:14px; }
.mp-src{ margin:14px 0 0; font-size:12.5px; color:var(--stone); }
.mp-src a{ color:inherit; }
.mp-plan{ align-self:start; background:#F4F2EE; border-radius:14px; padding:10px; }
.mp-plan img{ background:transparent; }
.mp-plan .mp-cap{ color:#55565A; padding:0 4px 2px; }
.mp-plan .mp-cap .mp-kind{ color:#7A6248; }
.mp-notes{ display:grid; grid-template-columns:1fr 1fr; gap:clamp(18px,3vw,44px); margin-top:clamp(28px,3vw,44px); }
.mp-note{ border-top:1px solid var(--line); padding-top:16px; }
.pn-pd .mp .mp-note h3{ margin:0 0 8px; font-family:var(--sans); line-height:1.4; font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); }
.mp-note p{ margin:0; font-size:15px; line-height:1.7; }
.mp-well{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,7fr); gap:clamp(24px,4vw,64px); align-items:center; }
.mp-well .mp-p{ max-width:52ch; }
.mp-price{ display:inline-block; margin:22px 0 10px; padding:10px 18px; border:1px solid var(--line); border-radius:999px; font-size:12px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--bronze); }
.mp-pnote{ margin:0; font-size:14px; line-height:1.6; color:var(--stone); max-width:52ch; }
.mp-also{ margin-top:22px; font-size:15px; color:var(--stone); }
/* the guided route reuses the Discovery two-option component (pn-two-option.css) as-is */
.mp-route .pn-two{ max-width:none; }
.mp-fine{ margin:26px 0 0; font-size:13.5px; line-height:1.7; color:var(--stone); max-width:78ch; }
.mp-rec{ padding:34px 0 64px; border-top:1px solid var(--line); font-size:13.5px; line-height:1.7; color:var(--stone); }
.mp-rec p{ margin:0 0 6px; max-width:80ch; }
.mp-rec a{ color:inherit; }
@media (max-width:900px){
  .mp-hero .mp-w, .mp-head, .mp-model, .mp-notes, .mp-well{ grid-template-columns:1fr; }
  .mp-hero .mp-fig img{ max-height:none; width:100%; }
  .mp-hero .mp-cap{ justify-content:flex-start; }
}
@media (max-width:560px){ .mp-spec{ grid-template-columns:1fr; } .mp-spec dt{ border-bottom:0; padding-bottom:0; } }
</style>
"""


PUBLIC_HEAD = """<!DOCTYPE html>
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
<title>Don Modular Homes: steel-framed modular homes and garden rooms | PlotNua</title>
<meta name="description" content="Don Modular Homes builds one steel-framed, factory-finished design from a 25 m² garden room to a four-bedroom home at €2,400 per m² fully fitted. See sizes, published prices and the supplier's visualisations.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://plotnua.ie/suppliers/garden-room-ireland.html">
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotnua-mark-master.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/suppliers/garden-room-ireland.html">
<meta property="og:title" content="Don Modular Homes | PlotNua">
<meta property="og:description" content="One steel-framed modular design, from garden room to four-bedroom home.">
<meta property="og:image" content="{og}">
<!-- Built by supplier-preview-system/build-don-modular-homes-showcase.py from showcase.json. Do not hand-edit.
     Supplier imagery: Don Modular Homes' written YES of 2 Oct 2026 (image-rights-records.json, Don Modular Homes). Every image is a computer-generated visualisation. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../assets/identity/pn-premium-discovery.css">
"""

BAR = """<nav class="mp-bar" aria-label="PlotNua"><div class="mp-w"><a class="mp-brand" href="../">PlotNua</a>
<a class="mp-back" href="../discovery-living-in-the-garden.html#explore-makers"><span aria-hidden="true">&larr;</span> Living in the Garden</a></div></nav>
"""


def fig(i, bundle, credit_href, first=False, cls=""):
    lazy = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
    return (f'<figure class="mp-fig{cls}"><img src="{E(img_src(i, bundle))}" alt="{E(i["alt"])}" width="{i["w"]}" height="{i["h"]}" '
            f'{lazy} decoding="async" referrerpolicy="no-referrer" data-pn-slot="{E(i["id"])}" data-pn-origin="{E(i["origin"])}">'
            f'<figcaption class="mp-cap"><span class="mp-kind">{E(i["kind"])}</span>'
            f'<span>{E(i.get("caption",""))} <a href="{E(credit_href)}" rel="noopener" target="_blank">{E(DATA["supplier"]["credit"])}</a></span></figcaption></figure>')


def wellness_section(bundle):
    w, I, s = DATA["wellness"], imgs(), DATA["supplier"]
    return (f'''<section class="mp-sec" id="wellness" aria-labelledby="mp-wl-h"><div class="mp-w"><div class="mp-well">
  <div><p class="mp-k">Wellness</p><h2 class="mp-h2" id="mp-wl-h">{E(w["title"])}</h2>
  <p class="mp-p">{E(w["body"])}</p>
  <p class="mp-price">{E(w["price"])}</p>
  <p class="mp-pnote">{E(w["priceNote"])}</p></div>
  {fig(I[w["image"]], bundle, s["creditHref"])}
</div></div></section>
''')


def showcase():
    s = DATA["supplier"]
    hero = next(i for i in DATA["images"] if i["role"] == "hero")
    coll = [i for i in DATA["images"] if i["role"] == "collection"]
    inside = [i for i in DATA["images"] if i["role"] == "interior"]
    models = []
    for p in DATA["products"]:
        price = dict(p["specs"])["Price"]
        dl = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in p["specs"] if k != "Price")
        models.append(
            f'<article class="mp-model no-plan" aria-label="{E(p["name"])}"><div>'
            f'<h3>{E(p["name"])}</h3><p class="mp-kind2">{E(p["kind"])}</p><p class="mp-sum">{E(p["summary"])}</p>'
            f'<dl class="mp-spec">{dl}<dt>Published price</dt><dd>{E(price)}</dd></dl>'
            f'<p class="mp-src">As published by {E(s["name"])} &middot; checked 4 Nov 2026 &middot; VAT not stated</p></div></article>')
    j = "".join(f'<li><a class="pn-two-b" href="{E(h)}">{E(l)} <span aria-hidden="true">&rarr;</span></a></li>' for l, h in journeys("../"))
    head = PUBLIC_HEAD.replace("{og}", E(hero["origin"]))
    if PREVIEW:
        head = head.replace('<meta name="robots" content="index, follow">',
                            '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">')
    band = ('<div class="mp-hold"><div class="mp-w"><b>Private preview</b><span>Prepared for Don Modular Homes to review. '
            'Not yet published on PlotNua.</span></div></div>\n') if PREVIEW else ""
    return (head + CSS + """<style>
.mp-range{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr)); gap:clamp(16px,2vw,24px); }
.mp-range .mp-model h3{ font-size:clamp(26px,2.4vw,34px); }
.mp-range .mp-spec{ grid-template-columns:1fr; }
.mp-range .mp-spec dt{ border-bottom:0; padding-bottom:0; }
.mp-in{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:clamp(16px,2vw,26px); align-items:start; }
.mp-viz{ margin:0; padding:14px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); font-size:14px; line-height:1.6; color:var(--stone); }
.mp-viz b{ font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:11px; color:var(--bronze); margin-right:8px; }
.mp-rate{ display:grid; grid-template-columns:minmax(0,4fr) minmax(0,8fr); gap:clamp(20px,4vw,56px); background:var(--card); border:1px solid var(--line); border-radius:24px; padding:clamp(22px,3.4vw,44px); margin-bottom:clamp(20px,2.4vw,32px); }
.mp-rate .mp-rate-n{ font-family:var(--serif); color:var(--ink); font-size:clamp(34px,4vw,56px); line-height:1.05; margin:0; }
.mp-rate h3{ margin:0 0 8px; font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); }
.mp-rate p{ margin:0 0 14px; font-size:15px; line-height:1.7; }
@media (max-width:900px){ .mp-rate{ grid-template-columns:1fr; } }
</style>
""" +
f"""<link rel="stylesheet" href="../assets/components/pn-two-option.css?v=1">
</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main" class="mp">
{BAR}{band}
<section class="mp-hero" aria-labelledby="mp-h1"><div class="mp-w">
  <div>
    <p class="mp-k">Maker &middot; Living in the Garden</p>
    <h1 class="mp-h1" id="mp-h1">{E(s["name"])}</h1>
    <p class="mp-lede">{E(DATA["intro"])}</p>
    <ul class="mp-meta" role="list"><li>Steel-framed modular homes</li><li>Garden room to four bedrooms</li><li>Factory finished</li></ul>
  </div>
  {fig(hero, False, s["creditHref"], first=True)}
</div></section>
<div class="mp-w"><p class="mp-viz" role="note"><b>Visualisations</b>{E(DATA["visualNote"])}</p></div>

<section class="mp-sec" id="collection" aria-labelledby="mp-col-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">The design</p><h2 class="mp-h2" id="mp-col-h">One building, many sizes.</h2></div>
  <p class="mp-p">{E(DATA["standfirst"])}</p></div>
  <div class="mp-col">{"".join(fig(i, False, s["creditHref"]) for i in coll)}</div>
</div></section>

<section class="mp-sec" id="interiors" aria-labelledby="mp-in-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">Interiors</p><h2 class="mp-h2" id="mp-in-h">Finished inside, not a shell.</h2></div>
  <p class="mp-p">The bathroom, kitchen, heating and finishes are fitted in the factory and included in the rate.</p></div>
  <div class="mp-in">{"".join(fig(i, False, s["creditHref"]) for i in inside)}</div>
</div></section>

<section class="mp-sec" id="models" aria-labelledby="mp-mod-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">Sizes and prices</p><h2 class="mp-h2" id="mp-mod-h">Priced by the square metre.</h2></div>
  <p class="mp-p">Don Modular Homes publishes one rate for every size. The figures below are the supplier&rsquo;s own, read from its website and re-checked on 4 November 2026.</p></div>
  <div class="mp-rate"><p class="mp-rate-n">{E(DATA["rate"])}</p><div>
    <h3>Included</h3><p>{E(DATA["included"])}</p>
    <h3>Quoted separately</h3><p>{E(DATA["excludedCosts"])}</p></div></div>
  <div class="mp-range">{"".join(models)}</div>
  <div class="mp-notes">
    <div class="mp-note"><h3>The whole cost</h3><p>Ask for a written quote that includes the base, delivery, crane, installation, connections and VAT, so you can compare like with like.</p></div>
    <div class="mp-note"><h3>Planning</h3><p>{E(DATA["planningNote"])}</p></div>
  </div>
</div></section>

<section class="mp-sec mp-route" id="enquire" aria-labelledby="mp-en-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">Next step</p><h2 class="mp-h2" id="mp-en-h">Could this work on your plot?</h2></div>
  <p class="mp-p">Before you contact any maker, PlotNua can help you work out what your garden can take and which options fit how you&rsquo;d use it. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Compare Don Modular Homes with the other makers on PlotNua, side by side.</p>
      <a class="pn-two-a" href="../discovery-living-in-the-garden.html#explore-makers">Browse makers and products <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p><p class="pn-two-t">Tell us what you&rsquo;re looking for. We&rsquo;ll use our Atlas research to help you find options that match your preferences and budget.</p>
      <ul class="pn-two-btns" role="list">{j}</ul></div>
  </div>
  <p class="mp-fine">PlotNua is free for homeowners. Inclusion here is not a recommendation, there is no paid placement, and recommendations cannot be bought.</p>
</div></section>

<footer class="mp-rec"><div class="mp-w">
  <p>Visualisations: {E(s["name"])}, from <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">donmodularhomes.ie</a>. Don Modular Homes keeps ownership of its imagery.</p>
  <p>Sizes, specifications and prices as published on the supplier&rsquo;s website, recorded in PlotNua&rsquo;s Atlas and re-checked on 4 November 2026. They can change; confirm them with Don Modular Homes.</p>
</div></footer>
</main>
</body>
</html>
""")


def journeys(prefix):
    return [("A garden room", f"{prefix}your-plot.html?discovery=garden-room&{VIA}"),
            ("A garden home", f"{prefix}your-plot.html?discovery=residential&{VIA}")]


def main():
    guard()
    out = ROOT / "suppliers" / "don-modular-homes.html"
    txt = showcase()
    if "--check" in sys.argv:
        same = out.exists() and out.read_text(encoding="utf-8") == txt
        print(("CHECK OK " if same else "STALE    ") + "suppliers/don-modular-homes.html")
        sys.exit(0 if same else 1)
    out.write_text(txt, encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
