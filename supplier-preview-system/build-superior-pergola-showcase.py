#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - SUPERIOR PERGOLA IRELAND SUPPLIER SHOWCASE (staging, 4 Nov 2026).

Builds suppliers/superior-pergola-ireland.html from
supplier-preview-system/showcases/superior-pergola-ireland/showcase.json.
Follows the Gardenhouse24 showcase (build-gardenhouse24-showcase.py).

RIGHTS. Builds only while image-rights-records.json holds a live, PUBLISHABLE record for
Superior Pergola Ireland whose required credit is the page credit, and every image URL sits
on the supplier's domain or on its declared delivery host + prefix (b3819663.assetcdn.net
/2.0/3819663/ - that account namespace only, never the whole CDN). Every image names its
Atlas asset record. The credit beside each photograph and in the footer is a working link
to superiorpergola.ie: PlotNua's own undertaking of 29 Sep 2026.

FACTS. guard() refuses a product without an Atlas record, a price that is not a whole euro
figure from the data file, an image tied to a product the data file does not list, and an
image used twice. Nothing is typed into the page that is not in showcase.json.

COMMERCIAL. The referral fee is disclosed in words only; no rate is written anywhere in this
builder, its data file or the page (CM1 in the guard). The homeowner-saving panel is OFF:
with offer.enabled false it renders nothing at all - not hidden markup, nothing. It refuses
to render a saving without a whole-number percent, basisConfirmed true and conditions.
--preview-offer writes a separate, clearly marked review copy OUTSIDE the repository so the
founder can see the panel; it never touches suppliers/.

JOURNEY. No outbound sales button. Option A stays inside PlotNua; Option B is PlotNua's free
help over its existing WhatsApp and email, carrying ref superior-pergola-ireland. No form,
no new data store: PlotNua asks for explicit consent before sending anything to the supplier.

Run: python3 supplier-preview-system/build-superior-pergola-showcase.py [--check]
     python3 supplier-preview-system/build-superior-pergola-showcase.py --preview-offer OUT.html
"""
import html, json, re, sys
from pathlib import Path
from urllib.parse import urlparse, quote

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "superior-pergola-ireland"
DATA = json.loads((HERE / "showcase.json").read_text(encoding="utf-8"))
OUT = ROOT / "suppliers" / "superior-pergola-ireland.html"
E = lambda s: html.escape(str(s), quote=True)
WHATSAPP = "https://wa.me/353834036695"   # PlotNua's own WhatsApp (atlas-tools/pn_header.py WHATSAPP)
EMAIL = "hello@plotnua.ie"


def eur(n):
    return "€{:,}".format(int(n))


def guard(offer_preview=False):
    s = DATA["supplier"]
    recs = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
            if r["organisation_name"] == s["atlasName"]]
    if len(recs) != 1 or not recs[0]["permission_outcome"].startswith("Granted") or recs[0].get("public_visibility") != "PUBLISHABLE":
        sys.exit("FAIL: no live, publishable rights record for Superior Pergola Ireland; nothing is built")
    r = recs[0]
    if r["organisation_record"] != s["atlasRecord"]:
        sys.exit("FAIL: the rights record belongs to a different Atlas organisation")
    if r["required_credit"] != s["credit"]:
        sys.exit("FAIL: the page credit differs from the rights record's required credit")
    if urlparse(s["creditHref"]).hostname != "www.superiorpergola.ie":
        sys.exit("FAIL: the credit must link to superiorpergola.ie (PlotNua's undertaking of 29 Sep 2026)")
    scopes = [(d["host"], d["path_prefix"]) for d in r.get("permitted_delivery_hosts") or [] if d.get("path_prefix")]
    names = {p["name"] for p in DATA["products"]}
    ids, origins = set(), set()
    for i in DATA["images"]:
        if i["id"] in ids or i["origin"] in origins:
            sys.exit(f"FAIL: image {i['id']} appears twice; each photograph is shown once")
        ids.add(i["id"]); origins.add(i["origin"])
        u = urlparse(i["origin"])
        on_domain = u.hostname in (r["permitted_domain"], "www." + r["permitted_domain"])
        if u.scheme != "https" or not (on_domain or any(u.hostname == h and u.path.startswith(px) for h, px in scopes)):
            sys.exit(f"FAIL: image {i['id']} is outside the grant's domain and delivery scope")
        if i["kind"] != "Photograph" or not re.fullmatch(r"rec[A-Za-z0-9]{14}", i.get("asset") or ""):
            sys.exit(f"FAIL: image {i['id']}: medium or Atlas asset record missing")
        if i["product"] is not None and i["product"] not in names:
            sys.exit(f"FAIL: image {i['id']}: tied to a product the data file does not list")
        if i["product"] is None and i["role"] != "collection":
            sys.exit(f"FAIL: image {i['id']}: an image with no product can only sit in the collection")
        if (i["w"] is None) != (i["h"] is None):
            sys.exit(f"FAIL: image {i['id']}: width and height are recorded together or not at all")
    for p in DATA["products"]:
        if not re.fullmatch(r"rec[A-Za-z0-9]{14}", p.get("atlas") or ""):
            sys.exit(f"FAIL: {p['name']}: no Atlas product record")
        if not isinstance(p["price"], int):
            sys.exit(f"FAIL: {p['name']}: prices must be the whole-euro figures recorded in the data file")
        if set(p["images"]) - ids:
            sys.exit(f"FAIL: {p['name']}: unknown image slot")
    if sum(1 for i in DATA["images"] if i["role"] == "hero") != 1:
        sys.exit("FAIL: exactly one hero image")
    o = DATA["offer"]
    if o["enabled"] or offer_preview:
        if not (isinstance(o["percent"], int) or offer_preview) or not o["conditions"]:
            sys.exit("FAIL: a homeowner saving needs a whole-number percent and its conditions")
        if o["enabled"] and (not o["basisConfirmed"] or not o["wording"]):
            sys.exit("FAIL: the saving cannot go live until its basis is confirmed and its wording approved")
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
<title>Superior Pergola Ireland: aluminium pergolas, verandas and porches | PlotNua</title>
<meta name="description" content="Superior Pergola Ireland's made-to-measure aluminium pergolas, verandas and porches: published starting prices, roof options and how a quote works, checked by PlotNua.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://plotnua.ie/suppliers/superior-pergola-ireland.html">
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotnua-mark-master.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/suppliers/superior-pergola-ireland.html">
<meta property="og:title" content="Superior Pergola Ireland | PlotNua">
<meta property="og:description" content="Made-to-measure aluminium pergolas, verandas and porches from Superior Pergola Ireland, with starting prices and roof options checked by PlotNua.">
<meta property="og:image" content="{og}">
<!-- Built by supplier-preview-system/build-superior-pergola-showcase.py from showcase.json. Do not hand-edit.
     Supplier imagery: Superior Pergola Ireland's written email permission, 29 Sep 2026 (image-rights-records.json). -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../assets/identity/pn-premium-discovery.css">
<link rel="stylesheet" href="../assets/components/pn-two-option.css?v=1">
"""

CSS = """<style>
/* Superior Pergola Ireland showcase - scoped to .sp. The site's --p4-* identity tokens; no new identity.
   Supplier images are shown WHOLE: natural aspect ratio, never cropped, filtered, rounded or overlaid. */
.sp{ --ink:var(--p4-ivory,#F2EBE0); --soft:var(--p4-lime,#E7DED0); --stone:var(--p4-stone,#C2BDB5);
  --bronze:var(--p4-bronze-text,#B39272); --line:var(--p4-line2,#4A4B4F); --card:var(--p4-deep,#2C2E30);
  --well:var(--p4-well,#2D2E31); --serif:var(--p4-serif,'Instrument Serif',Georgia,serif);
  --sans:var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif); color:var(--soft); font-family:var(--sans); }
.sp *{ box-sizing:border-box; }
.sp-w{ max-width:1280px; margin:0 auto; padding:0 clamp(18px,3.4vw,48px); }
.sp-bar{ border-bottom:1px solid var(--line); }
.sp-bar .sp-w{ display:flex; justify-content:space-between; align-items:center; gap:16px; padding-top:16px; padding-bottom:16px; flex-wrap:wrap; }
.sp-brand{ font-family:var(--serif); font-size:26px; color:var(--ink); text-decoration:none; }
.sp-back{ display:flex; gap:18px; flex-wrap:wrap; }
.sp-back a{ font-size:14px; color:var(--soft); text-decoration:none; border-bottom:1px solid var(--line); padding-bottom:2px; }
.sp-back a:hover, .sp-brand:hover{ color:var(--ink); }
.sp-k{ margin:0 0 16px; font-size:11.5px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--bronze); }
.sp-hero{ padding:clamp(36px,6vw,84px) 0 clamp(30px,4vw,56px); }
.sp-hero .sp-w{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(28px,4.5vw,72px); align-items:end; }
.sp-h1{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(40px,4.6vw,72px); line-height:1.02; letter-spacing:-.015em; overflow-wrap:break-word; margin:0 0 22px; }
.sp-lede{ font-size:clamp(17px,1.45vw,20px); line-height:1.6; margin:0 0 26px; color:var(--ink); max-width:38ch; }
.sp-meta{ list-style:none; margin:0; padding:18px 0 0; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:8px 24px; font-size:13.5px; color:var(--stone); }
.sp-jump{ list-style:none; margin:26px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:10px; }
.sp-jump a{ display:inline-block; padding:9px 16px; border:1px solid var(--line); border-radius:999px; color:var(--ink); text-decoration:none; font-size:14px; }
.sp-jump a:hover{ border-color:var(--bronze); }
.sp-fig{ margin:0; }
.sp-fig img{ display:block; width:100%; height:auto; background:var(--well); }
.sp-hero .sp-fig img{ max-height:78vh; width:auto; max-width:100%; margin-left:auto; }
.sp-cap{ margin:10px 0 0; font-size:12.5px; line-height:1.5; color:var(--stone); display:flex; gap:10px; flex-wrap:wrap; align-items:baseline; }
.sp-cap .sp-kind{ font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:10.5px; color:var(--bronze); }
.sp-cap a{ color:inherit; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.sp-sec{ padding:clamp(48px,7vw,104px) 0; border-top:1px solid var(--line); }
.sp-h2{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(32px,4vw,56px); line-height:1.06; margin:0 0 16px; }
.sp-p{ font-size:17px; line-height:1.75; max-width:64ch; margin:0; }
.sp-head{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(20px,5vw,80px); align-items:end; margin-bottom:clamp(30px,4vw,56px); }
.sp-col{ columns:3 280px; column-gap:clamp(16px,2vw,28px); }
.sp-col .sp-fig{ break-inside:avoid; margin:0 0 clamp(26px,3vw,40px); }
.sp-cat + .sp-cat{ margin-top:clamp(56px,7vw,96px); }
.sp-cat-h{ display:flex; justify-content:space-between; align-items:baseline; gap:20px; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:16px; margin-bottom:clamp(22px,3vw,34px); }
.sp-cat-h h3{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(28px,3vw,40px); margin:0; }
.sp-cat-h p{ margin:0; color:var(--stone); font-size:15px; }
.sp-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:clamp(18px,2vw,28px); }
.sp-prod{ background:var(--card); border:1px solid var(--line); border-radius:22px; padding:clamp(18px,2.2vw,26px); display:flex; flex-direction:column; gap:14px; }
.sp-prod h4{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(26px,2.4vw,32px); margin:0; line-height:1.1; }
.sp-sum{ margin:0; font-size:15.5px; line-height:1.6; color:var(--ink); }
.sp-spec{ margin:0; display:grid; grid-template-columns:minmax(96px,128px) 1fr; border-top:1px solid var(--line); }
.sp-spec dt, .sp-spec dd{ padding:9px 0; border-bottom:1px solid var(--line); margin:0; font-size:14px; line-height:1.5; }
.sp-spec dt{ font-size:10.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--stone); padding-top:12px; padding-right:12px; }
.sp-price{ margin-top:auto; border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.sp-price b{ display:block; font-family:var(--serif); font-weight:400; font-size:28px; color:var(--ink); line-height:1.1; }
.sp-price span{ display:block; font-size:12px; color:var(--stone); margin-top:4px; line-height:1.4; }
.sp-src{ margin:0; font-size:12px; color:var(--stone); }
.sp-steps{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr)); gap:0 clamp(20px,3vw,44px); counter-reset:sp; }
.sp-steps li{ border-top:1px solid var(--line); padding:16px 0 20px; counter-increment:sp; }
.pn-pd .sp .sp-steps h3, .pn-pd .sp .sp-note h3{ margin:0 0 8px; font-family:var(--sans); font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); line-height:1.4; }
.pn-pd .sp .sp-steps h3::before{ content:counter(sp, decimal-leading-zero) "  "; color:var(--stone); }
.sp-steps p, .sp-note p{ margin:0; font-size:15px; line-height:1.7; }
.sp-fine{ margin:26px 0 0; font-size:13.5px; line-height:1.7; color:var(--stone); max-width:80ch; }
.sp-notes{ display:grid; grid-template-columns:1fr 1fr; gap:clamp(18px,3vw,44px); }
.sp-note{ border-top:1px solid var(--line); padding-top:16px; }
.sp-route .pn-two{ max-width:none; }
.sp-offer{ margin:0 0 16px; border:1px solid var(--bronze); border-radius:14px; padding:14px 16px; }
.sp-offer b{ display:block; font-family:var(--serif); font-weight:400; font-size:24px; color:var(--ink); line-height:1.15; }
.sp-offer ul{ margin:8px 0 0; padding:0 0 0 18px; font-size:13px; line-height:1.55; color:var(--stone); }
.sp-rec{ padding:34px 0 64px; border-top:1px solid var(--line); font-size:13.5px; line-height:1.7; color:var(--stone); }
.sp-rec p{ margin:0 0 6px; max-width:84ch; }
.sp-rec a{ color:inherit; }
@media (max-width:960px){ .sp-hero .sp-w, .sp-head, .sp-notes{ grid-template-columns:1fr; } .sp-hero .sp-fig img{ max-height:none; width:100%; } }
@media (max-width:560px){ .sp-grid{ grid-template-columns:1fr; } .sp-spec{ grid-template-columns:1fr; } .sp-spec dt{ border-bottom:0; padding-bottom:0; } }
</style>
"""


def fig(i, first=False):
    s = DATA["supplier"]
    lazy = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
    dims = f' width="{i["w"]}" height="{i["h"]}"' if i["w"] else ""
    return (f'<figure class="sp-fig"><img src="{E(i["origin"])}" alt="{E(i["alt"])}"{dims} '
            f'{lazy} decoding="async" referrerpolicy="no-referrer" data-pn-slot="{E(i["id"])}">'
            f'<figcaption class="sp-cap"><span class="sp-kind">{E(i["kind"])}</span>'
            f'<span>{E(i["caption"])} <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">{E(s["credit"])}</a></span></figcaption></figure>')


def product(p, I):
    img = fig(I[p["images"][0]]) if p["images"] else ""
    dl = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in p["specs"])
    unit = f' {E(p["priceUnit"])}' if p["priceUnit"] else ""
    return (f'<article class="sp-prod" aria-label="{E(p["name"])}">{img}<h4>{E(p["name"])}</h4>'
            f'<p class="sp-sum">{E(p["summary"])}</p><dl class="sp-spec">{dl}</dl>'
            f'<div class="sp-price"><b>From {eur(p["price"])}{unit}</b><span>Published starting price, including fitting. '
            f'Your price is set after the supplier measures up.</span></div>'
            f'<p class="sp-src">As published by {E(DATA["supplier"]["name"])}</p></article>')


def offer_html(preview=False):
    o = DATA["offer"]
    if not (o["enabled"] or preview):
        return ""
    pct = o["percent"] if isinstance(o["percent"], int) else 4
    tag = '<p class="sp-k" style="margin:0 0 6px;color:#E8B04A">Review copy - not live</p>' if preview else ""
    conds = "".join(f"<li>{E(c)}</li>" for c in o["conditions"])
    words = o["wording"] or f"{pct}% off your Superior Pergola Ireland quote when PlotNua introduces you"
    return (f'<div class="sp-offer" data-pn-offer="{E(DATA["referral"]["attribution"])}">{tag}'
            f'<p class="sp-k" style="margin:0 0 6px">{E(o["headline"])}</p><b>{E(words)}</b><ul>{conds}</ul></div>')


def build(offer_preview=False):
    guard(offer_preview)
    s, I, ref = DATA["supplier"], {i["id"]: i for i in DATA["images"]}, DATA["referral"]
    hero = next(i for i in DATA["images"] if i["role"] == "hero")
    used = {p["images"][0] for p in DATA["products"] if p["images"]} | {hero["id"]}
    coll = [i for i in DATA["images"] if i["id"] not in used]          # each image once
    cats = []
    for c in DATA["categories"]:
        ps = [p for p in DATA["products"] if p["category"] == c["id"]]
        cats.append(f'<section class="sp-cat" id="{E(c["id"])}" aria-labelledby="{E(c["id"])}-h"><div class="sp-cat-h">'
                    f'<h3 id="{E(c["id"])}-h">{E(c["title"])}</h3><p>{E(c["line"])}</p></div>'
                    f'<div class="sp-grid">{"".join(product(p, I) for p in ps)}</div></section>')
    jump = "".join(f'<li><a href="#{E(c["id"])}">{E(c["title"])}</a></li>' for c in DATA["categories"])
    jump += '<li><a href="#quote">How a quote works</a></li>'
    meta = "".join(f"<li>{E(f)}</li>" for f in DATA["facts"])
    q = DATA["quoting"]
    steps = "".join(f'<li><h3>{E(k)}</h3><p>{E(v)}</p></li>' for k, v in q["steps"])
    notes = "".join(f'<div class="sp-note"><h3>{E(k)}</h3><p>{E(v)}</p></div>' for k, v in DATA["considerations"])
    wa = WHATSAPP + "?text=" + quote(ref["whatsappText"])
    mail = f"mailto:{EMAIL}?subject=" + quote(ref["emailSubject"])
    routes = (f'<li><a class="pn-two-b" href="{E(wa)}" target="_blank" rel="noopener">Ask on WhatsApp <span aria-hidden="true">&rarr;</span></a></li>'
              f'<li><a class="pn-two-b" href="{E(mail)}">Email PlotNua <span aria-hidden="true">&rarr;</span></a></li>')
    return (HEAD.replace("{og}", E(hero["origin"])) + CSS + f"""</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main" class="sp">
<nav class="sp-bar" aria-label="PlotNua"><div class="sp-w"><a class="sp-brand" href="../">PlotNua</a>
<div class="sp-back"><a href="../discoveries.html"><span aria-hidden="true">&larr;</span> All Discoveries</a><a href="../discovery-living-in-the-garden.html#suppliers"><span aria-hidden="true">&larr;</span> Living in the Garden</a></div></div></nav>

<section class="sp-hero" aria-labelledby="sp-h1"><div class="sp-w">
  <div>
    <p class="sp-k">Maker &middot; Pergolas, verandas and porches</p>
    <h1 class="sp-h1" id="sp-h1">{E(s["name"])}</h1>
    <p class="sp-lede">{E(DATA["intro"])}</p>
    <ul class="sp-meta" role="list">{meta}</ul>
    <ul class="sp-jump" role="list">{jump}</ul>
  </div>
  {fig(hero, first=True)}
</div></section>

<section class="sp-sec" id="products" aria-labelledby="sp-pr-h"><div class="sp-w">
  <div class="sp-head"><div><p class="sp-k">The range</p><h2 class="sp-h2" id="sp-pr-h">Five ranges, all made to measure.</h2></div>
  <p class="sp-p">{E(DATA["standfirst"])}</p></div>
  {"".join(cats)}
</div></section>

<section class="sp-sec" id="collection" aria-labelledby="sp-col-h"><div class="sp-w">
  <div class="sp-head"><div><p class="sp-k">More of their work</p><h2 class="sp-h2" id="sp-col-h">Roofs, glass and finishes.</h2></div>
  <p class="sp-p">The same frame with a different roof or sides makes a very different space. Each photograph is the supplier&rsquo;s own.</p></div>
  <div class="sp-col">{"".join(fig(i) for i in coll)}</div>
</div></section>

<section class="sp-sec" id="quote" aria-labelledby="sp-q-h"><div class="sp-w">
  <div class="sp-head"><div><p class="sp-k">Before you ask for a price</p><h2 class="sp-h2" id="sp-q-h">{E(q["title"])}</h2></div>
  <p class="sp-p">{E(q["lede"])}</p></div>
  <ol class="sp-steps" role="list">{steps}</ol>
  <p class="sp-fine">{E(q["note"])}</p>
</div></section>

<section class="sp-sec" id="considerations" aria-labelledby="sp-cn-h"><div class="sp-w">
  <div class="sp-head"><div><p class="sp-k">For Irish homeowners</p><h2 class="sp-h2" id="sp-cn-h">Worth checking first.</h2></div>
  <p class="sp-p">General points, not an assessment of your property.</p></div>
  <div class="sp-notes">{notes}</div>
</div></section>

<section class="sp-sec sp-route" id="enquire" aria-labelledby="sp-en-h"><div class="sp-w">
  <div class="sp-head"><div><p class="sp-k">Next step</p><h2 class="sp-h2" id="sp-en-h">Two ways to go from here.</h2></div>
  <p class="sp-p">Look around at your own pace, or let PlotNua help you work out what would suit your space and then introduce you to Superior Pergola Ireland. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Go back through the range and the quote checklist above, or see what else a garden can hold.</p>
      <a class="pn-two-a" href="#products">The range <span aria-hidden="true">&rarr;</span></a>
      <a class="pn-two-a" href="../discovery-living-in-the-garden.html">Living in the Garden <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p>{offer_html(offer_preview)}<p class="pn-two-t">Tell us about the space and how you&rsquo;d use it. We&rsquo;ll help you settle the roof, sides and size, and, only if you say yes, send your enquiry to Superior Pergola Ireland as a PlotNua introduction.</p>
      <ul class="pn-two-btns" role="list">{routes}</ul></div>
  </div>
  <p class="sp-fine">PlotNua is free for homeowners. We never pass your name or contact details to a supplier without asking you first. PlotNua does not sell these products and cannot guarantee a supplier&rsquo;s availability or prices; you buy directly from the supplier. PlotNua may receive a referral fee from Superior Pergola Ireland if you go ahead after a PlotNua introduction; it is paid by the supplier, and it does not decide which suppliers PlotNua shows or how. Inclusion here is not a recommendation.</p>
</div></section>

<footer class="sp-rec"><div class="sp-w">
  <p>Photography: {E(s["name"])}, from <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">superiorpergola.ie</a>, used with the supplier&rsquo;s permission. The supplier keeps ownership of its photographs.</p>
  <p>Product details and starting prices as published on superiorpergola.ie (prices read 29 September 2026; ranges read 16 October 2026). Prices and specifications can change; confirm them with the supplier.</p>
</div></footer>
</main>
</body>
</html>
""")


def main():
    if "--preview-offer" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--preview-offer") + 1]).resolve()
        if ROOT in dest.parents:
            sys.exit("FAIL: the offer review copy is written outside the repository only")
        dest.write_text(build(offer_preview=True), encoding="utf-8")
        print("wrote review copy", dest)
        return
    txt = build()
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print(("CHECK OK " if ok else "STALE    ") + str(OUT.relative_to(ROOT)))
        sys.exit(0 if ok else 1)
    OUT.write_text(txt, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
