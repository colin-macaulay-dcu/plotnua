#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - THE POD FACTORY SUPPLIER SHOWCASE (founder brief, 11 Nov 2026).

Builds suppliers/the-pod-factory.html from supplier-preview-system/showcases/the-pod-factory/showcase.json.
Adapted from build-arctic-wellness-showcase.py: same structure, styling and guards. The Living in the
Garden card is built by atlas-tools/build-showcase-cards.py, not here.

RIGHTS. Builds only while image-rights-records.json holds a live, PUBLISHABLE record for The Pod Factory
whose required credit is the page credit, and every image URL (and every responsive variant) sits inside
the grant's declared delivery scope (www.thepodfactory.ie/wp-content/uploads/). Images are hotlinked
unmodified; the Image Rights Gate checks each. Only photographs, each with a SHA-256 and a source page.

PREVIEW. While PREVIEW = True the page is built noindex with a private-preview band, and its Living in
the Garden card is marked "preview" (left off the Discovery). Releasing: founder approval, PREVIEW = False,
remove "preview" from the card, rebuild, add the sitemap entry.

FACTS. guard() refuses a product with no supplier source, a price that is not a whole-euro figure from the
data file (or a range whose top is not above its bottom), or an image tied to a product the file does not list.
Products with no listed price say "Price on enquiry". Nothing is typed into the page that is not in showcase.json.

JOURNEY. No outbound sales button. Option A browses within PlotNua; Option B is PlotNua's free help on the
existing WhatsApp route, carrying the attribution marker via=the-pod-factory / ref PF.

Run: python3 supplier-preview-system/build-the-pod-factory-showcase.py [--check]
"""
import html, json, sys
from pathlib import Path
from urllib.parse import urlparse, quote

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "the-pod-factory"
DATA = json.loads((HERE / "showcase.json").read_text(encoding="utf-8"))
OUT = ROOT / "suppliers" / "the-pod-factory.html"
PREVIEW = False  # founder approval and production release, 11 Nov 2026 (was True for the private preview)
E = lambda s: html.escape(str(s), quote=True)
VIA = "via=the-pod-factory"
WHATSAPP = "https://wa.me/353834036695"   # PlotNua's own WhatsApp (atlas-tools/pn_header.py WHATSAPP)


def eur(n):
    return "€{:,}".format(int(n))


def guard():
    s = DATA["supplier"]
    recs = [r for r in json.loads((ROOT / "image-rights-records.json").read_text(encoding="utf-8"))["records"]
            if r["organisation_name"] == s["atlasName"]]
    if len(recs) != 1 or not recs[0]["permission_outcome"].startswith("Granted") or recs[0].get("public_visibility") != "PUBLISHABLE":
        sys.exit("FAIL: no live, publishable rights record for The Pod Factory; nothing is built")
    r = recs[0]
    if r["required_credit"] != s["credit"]:
        sys.exit("FAIL: the page credit differs from the rights record's required credit")
    scopes = [(d["host"], d["path_prefix"]) for d in r.get("permitted_delivery_hosts") or []]
    names = {p["name"] for p in DATA["products"]}
    ids = {i["id"] for i in DATA["images"]}
    if len(ids) != len(DATA["images"]):
        sys.exit("FAIL: duplicate image id")
    for i in DATA["images"]:
        for url in [i["origin"]] + [v[0] for v in i.get("variants", [])]:
            u = urlparse(url)
            if u.scheme != "https" or not any(u.hostname == h and u.path.startswith(px) for h, px in scopes):
                sys.exit(f"FAIL: image {i['id']} ({url}) is outside the grant's delivery scope")
        if i["kind"] != "Photograph" or not i.get("sha256") or not (i.get("sourcePage") or "").startswith(s["website"]) or (i["product"] is not None and i["product"] not in names):
            sys.exit(f"FAIL: image {i['id']}: only photographs, with provenance and a listed product (or none)")
        if not i["alt"] or not i["caption"]:
            sys.exit(f"FAIL: image {i['id']}: alt text and caption are required")
    for p in DATA["products"]:
        if not p["source"].startswith(s["website"]):
            sys.exit(f"FAIL: {p['name']}: specifications are not sourced to the supplier's site")
        if p["price"] is not None and not isinstance(p["price"], int):
            sys.exit(f"FAIL: {p['name']}: prices must be the whole-euro figures recorded in the data file")
        if p["priceHigh"] is not None and (p["price"] is None or not isinstance(p["priceHigh"], int) or p["priceHigh"] <= p["price"]):
            sys.exit(f"FAIL: {p['name']}: a price range needs a whole-euro top above its bottom")
        if set(p["images"]) - ids:
            sys.exit(f"FAIL: {p['name']}: unknown image slot")
    for i in DATA["images"]:
        if i["product"] and i["id"] not in next(p for p in DATA["products"] if p["name"] == i["product"])["images"] and i["role"] != "collection":
            sys.exit(f"FAIL: image {i['id']}: tied to a product that does not show it")
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
<title>The Pod Factory: garden pods, modular homes and extensions from Co. Meath | PlotNua</title>
<meta name="description" content="The Pod Factory's steel-framed garden studios, garden pods, modular homes and extensions, built in Co. Meath and craned into place: sizes, layouts and what to ask, checked by PlotNua.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://plotnua.ie/suppliers/the-pod-factory.html">
<meta name="theme-color" content="#27282A">
<link rel="icon" href="/assets/brand/plotnua-mark-master.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:locale" content="en_IE">
<meta property="og:url" content="https://plotnua.ie/suppliers/the-pod-factory.html">
<meta property="og:title" content="The Pod Factory | PlotNua">
<meta property="og:description" content="Garden pods, modular homes and extensions from The Pod Factory in Co. Meath, with sizes and layouts checked by PlotNua.">
<meta property="og:image" content="{og}">
<!-- Built by supplier-preview-system/build-the-pod-factory-showcase.py from showcase.json. Do not hand-edit.
     Supplier imagery: The Pod Factory's written permission to showcase its products, 11 Nov 2026 (image-rights-records.json). -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../assets/identity/pn-premium-discovery.css">
<link rel="stylesheet" href="../assets/components/pn-two-option.css?v=1">
"""

PREVIEW_CSS = """<style>.aw-hold{ background:#3A3326; border-bottom:1px solid #6B5A3A; color:#F2EBE0; font-family:'Hanken Grotesk',system-ui,sans-serif; font-size:13.5px; }
.aw-hold .aw-w{ max-width:1280px; margin:0 auto; padding:10px clamp(18px,3.4vw,48px); display:flex; gap:12px; flex-wrap:wrap; }
.aw-hold b{ letter-spacing:.14em; text-transform:uppercase; font-size:11px; color:#E2C08D; }</style>
"""

CSS = """<style>
/* The Pod Factory showcase - scoped to .aw (class names shared with the earlier showcase builders). The site's --p4-* identity tokens; no new identity.
   Supplier images are shown WHOLE: natural aspect ratio, never cropped, filtered, rounded or overlaid. */
.aw{ --ink:var(--p4-ivory,#F2EBE0); --soft:var(--p4-lime,#E7DED0); --stone:var(--p4-stone,#C2BDB5);
  --bronze:var(--p4-bronze-text,#B39272); --line:var(--p4-line2,#4A4B4F); --card:var(--p4-deep,#2C2E30);
  --well:var(--p4-well,#2D2E31); --serif:var(--p4-serif,'Instrument Serif',Georgia,serif);
  --sans:var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif); color:var(--soft); font-family:var(--sans); }
.aw *{ box-sizing:border-box; }
.aw-w{ max-width:1280px; margin:0 auto; padding:0 clamp(18px,3.4vw,48px); }
.aw-bar{ border-bottom:1px solid var(--line); }
.aw-bar .aw-w{ display:flex; justify-content:space-between; align-items:center; gap:16px; padding-top:16px; padding-bottom:16px; flex-wrap:wrap; }
.aw-brand{ font-family:var(--serif); font-size:26px; color:var(--ink); text-decoration:none; }
.aw-back{ display:flex; gap:18px; flex-wrap:wrap; }
.aw-back a{ font-size:14px; color:var(--soft); text-decoration:none; border-bottom:1px solid var(--line); padding-bottom:2px; }
.aw-back a:hover, .aw-brand:hover{ color:var(--ink); }
.aw-k{ margin:0 0 16px; font-size:11.5px; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:var(--bronze); }
.aw-hero{ padding:clamp(36px,6vw,84px) 0 clamp(30px,4vw,56px); }
.aw-hero .aw-w{ display:grid; grid-template-columns:minmax(0,4fr) minmax(0,7fr); gap:clamp(28px,4.5vw,72px); align-items:end; }
.aw-h1{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(44px,5.4vw,80px); line-height:1; letter-spacing:-.015em; overflow-wrap:anywhere; margin:0 0 22px; }
.aw-lede{ font-size:clamp(17px,1.45vw,20px); line-height:1.6; margin:0 0 26px; color:var(--ink); max-width:36ch; }
.aw-meta{ list-style:none; margin:0; padding:18px 0 0; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:8px 24px; font-size:13.5px; color:var(--stone); }
.aw-jump{ list-style:none; margin:26px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:10px; }
.aw-jump a{ display:inline-block; padding:9px 16px; border:1px solid var(--line); border-radius:999px; color:var(--ink); text-decoration:none; font-size:14px; }
.aw-jump a:hover{ border-color:var(--bronze); }
.aw-fig{ margin:0; }
.aw-fig img{ display:block; width:100%; height:auto; background:var(--well); }
.aw-cap{ margin:10px 0 0; font-size:12.5px; line-height:1.5; color:var(--stone); display:flex; gap:10px; flex-wrap:wrap; align-items:baseline; }
.aw-cap .aw-kind{ font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:10.5px; color:var(--bronze); }
.aw-cap a{ color:inherit; text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.aw-sec{ padding:clamp(48px,7vw,104px) 0; border-top:1px solid var(--line); }
.aw-h2{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(32px,4vw,56px); line-height:1.06; margin:0 0 16px; }
.aw-p{ font-size:17px; line-height:1.75; max-width:64ch; margin:0; }
.aw-head{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,6fr); gap:clamp(20px,5vw,80px); align-items:end; margin-bottom:clamp(30px,4vw,56px); }
/* the collection keeps every photograph's own shape */
.aw-col{ columns:3 300px; column-gap:clamp(16px,2vw,28px); }
.aw-col .aw-fig{ break-inside:avoid; margin:0 0 clamp(26px,3vw,40px); }
/* categories and products */
.aw-cat + .aw-cat{ margin-top:clamp(56px,7vw,96px); }
.aw-cat-h{ display:flex; justify-content:space-between; align-items:baseline; gap:20px; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:16px; margin-bottom:clamp(22px,3vw,34px); }
.aw-cat-h h3{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(28px,3vw,40px); margin:0; }
.aw-cat-h p{ margin:0; color:var(--stone); font-size:15px; }
.aw-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(340px,1fr)); gap:clamp(18px,2vw,28px); }
.aw-prod{ background:var(--card); border:1px solid var(--line); border-radius:22px; padding:clamp(18px,2.2vw,26px); display:flex; flex-direction:column; gap:14px; }
.aw-prod .aw-fig{ margin:0 0 4px; }
.aw-prod .aw-fig img{ border-radius:0; }
.aw-prod h4{ font-family:var(--serif); font-weight:400; color:var(--ink); font-size:clamp(26px,2.4vw,32px); margin:0; line-height:1.1; }
.aw-sum{ margin:0; font-size:15.5px; line-height:1.6; color:var(--ink); }
.aw-spec{ margin:0; display:grid; grid-template-columns:minmax(96px,128px) 1fr; border-top:1px solid var(--line); }
.aw-spec dt, .aw-spec dd{ padding:9px 0; border-bottom:1px solid var(--line); margin:0; font-size:14px; line-height:1.5; }
.aw-spec dt{ font-size:10.5px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--stone); padding-top:12px; padding-right:12px; }
.aw-price{ margin-top:auto; display:grid; grid-template-columns:1fr; gap:10px; padding-top:6px; }
.aw-price div{ border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.aw-price b{ display:block; font-family:var(--serif); font-weight:400; font-size:26px; color:var(--ink); line-height:1.1; }
.aw-price span{ display:block; font-size:12px; color:var(--stone); margin-top:4px; line-height:1.4; }
.aw-src{ margin:0; font-size:12px; color:var(--stone); }
.aw-src a{ color:inherit; }
.aw-guide{ margin:0; font-size:14px; line-height:1.55; color:var(--stone); }
.aw-guide a{ color:var(--ink); text-decoration:underline; text-decoration-color:var(--line); text-underline-offset:3px; }
.aw-costs{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:0 clamp(20px,3vw,44px); }
.aw-cost{ border-top:1px solid var(--line); padding:16px 0 20px; }
.pn-pd .aw .aw-cost h3, .pn-pd .aw .aw-note h3{ margin:0 0 8px; font-family:var(--sans); font-size:11.5px; font-weight:700; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); line-height:1.4; }
.aw-cost p, .aw-note p{ margin:0; font-size:15px; line-height:1.7; }
.aw-fine{ margin:26px 0 0; font-size:13.5px; line-height:1.7; color:var(--stone); max-width:80ch; }
.aw-notes{ display:grid; grid-template-columns:1fr 1fr; gap:clamp(18px,3vw,44px); }
.aw-note{ border-top:1px solid var(--line); padding-top:16px; }
.aw-route .pn-two{ max-width:none; }
/* Supplier's own booking facility (added at the supplier's request, 11 Nov 2026). Bronze, the supplier side;
   sage stays PlotNua's own help. */
.aw-book{ margin:18px 0 0; display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:14px 24px;
  padding:20px 22px; border:1px solid var(--line); border-radius:16px; background:var(--card); }
.aw-book-t{ margin:0; flex:1 1 320px; min-width:0; }
.aw-book-t b{ display:block; margin:0 0 4px; font-weight:700; font-size:11.5px; letter-spacing:.18em; text-transform:uppercase; color:var(--bronze); }
.aw-book-t span{ display:block; font-size:15px; line-height:1.55; color:var(--soft); }
.aw-book-b{ display:inline-flex; align-items:center; gap:8px; min-height:44px; padding:0 18px; border-radius:999px;
  border:1px solid rgba(179,146,114,.7); background:rgba(179,146,114,.10); color:var(--ink); text-decoration:none;
  font-weight:600; font-size:14.5px; transition:background .2s ease, border-color .2s ease; }
.aw-book-b:hover{ border-color:var(--bronze); background:rgba(179,146,114,.20); }
.aw-book-b:focus-visible{ outline:2px solid #CF8566; outline-offset:3px; }
@media (max-width:560px){ .aw-book-b{ width:100%; justify-content:center; text-align:center; padding:10px 18px; line-height:1.35; } }
@media (prefers-reduced-motion:reduce){ .aw-book-b{ transition:none; } }
.aw-rec{ padding:34px 0 64px; border-top:1px solid var(--line); font-size:13.5px; line-height:1.7; color:var(--stone); }
.aw-rec p{ margin:0 0 6px; max-width:84ch; }
.aw-rec a{ color:inherit; }
@media (max-width:960px){ .aw-hero .aw-w, .aw-head, .aw-notes{ grid-template-columns:1fr; } }
@media (max-width:560px){ .aw-grid{ grid-template-columns:1fr; } .aw-spec{ grid-template-columns:1fr; } .aw-spec dt{ border-bottom:0; padding-bottom:0; } .aw-price{ grid-template-columns:1fr; } }
.aw-pnote{ margin:-6px 0 0; font-size:12.5px; line-height:1.5; color:var(--stone); }
.aw-prod{ gap:12px; }
.aw-prod .aw-price{ margin-top:0; padding-top:0; }
.aw-type{ margin:-6px 0 0; font-size:11px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--bronze); }
.aw-more summary{ cursor:pointer; list-style:none; font-size:12px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--ink); padding:10px 0; display:inline-flex; gap:8px; align-items:center; }
.aw-more summary::-webkit-details-marker{ display:none; }
.aw-more summary::after{ content:"+"; color:var(--bronze); font-size:16px; }
.aw-more[open] summary::after{ content:"\\2212"; }
.aw-more[open] summary{ margin-bottom:2px; }
.aw-src{ margin-top:auto !important; }
@media (max-width:560px){
  .aw-prod{ padding:18px; border-radius:18px; }
  .aw-prod h4{ font-size:26px; }
  .aw-sum{ font-size:15px; }
  .aw .aw-spec{ grid-template-columns:minmax(84px,104px) 1fr; }
  .aw .aw-spec dt{ border-bottom:1px solid var(--line); padding:10px 10px 10px 0; font-size:10px; }
  .aw .aw-spec dd{ padding:9px 0; font-size:14px; }
  .aw-price b{ font-size:24px; }
}
.aw-price b.aw-enq{ font-size:22px; }
</style>
"""


def srcset(i):
    v = [f"{E(u)} {w}w" for u, w in i.get("variants", [])] + [f"{E(i['origin'])} {i['w']}w"]
    return ", ".join(v)


def fig(i, first=False, sizes="(max-width:960px) 100vw, 60vw"):
    s = DATA["supplier"]
    lazy = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
    return (f'<figure class="aw-fig"><img src="{E(i["origin"])}" srcset="{srcset(i)}" sizes="{sizes}" alt="{E(i["alt"])}" width="{i["w"]}" height="{i["h"]}" '
            f'{lazy} decoding="async" referrerpolicy="no-referrer" data-pn-slot="{E(i["id"])}">'
            f'<figcaption class="aw-cap"><span class="aw-kind">{E(i["kind"])}</span>'
            f'<span>{E(i["caption"])} <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">{E(s["credit"])}</a></span></figcaption></figure>')


def price_html(p):
    if p["price"] is None:
        return '<div><b class="aw-enq">Price on enquiry</b><span>Bespoke; priced per project. No price list is published.</span></div>'
    top = f' &ndash; {eur(p["priceHigh"])}' if p["priceHigh"] else ""
    return f'<div><b>{eur(p["price"])}{top}</b><span>Listed unit price. VAT not stated; quoted with installation.</span></div>'


KEY = 3   # specifications always visible on a card; the rest sit under "More details"


def product(p, I, used):
    """Readability (founder review, 10 Nov 2026): name, type, one-line summary and the price first;
    the three key specifications always visible; any further specifications under "More details"
    (open on wide screens, folded on phones). Nothing is dropped or added."""
    li = next((i for i in p["images"] if i not in used), None)
    if li:
        used.add(li)
    img = fig(I[li], sizes="(max-width:560px) 100vw, (max-width:1100px) 50vw, 380px") if li else ""
    row = lambda kv: f"<dt>{E(kv[0])}</dt><dd>{E(kv[1])}</dd>"
    key, more = p["specs"][:KEY], p["specs"][KEY:]
    rest = (f'<details class="aw-more" open><summary>More details</summary><dl class="aw-spec">{"".join(row(kv) for kv in more)}</dl></details>'
            if more else "")
    note = f'<p class="aw-pnote">{E(p["priceNote"])}</p>' if p.get("priceNote") else ""
    # SEO Opportunity 1 (founder approval, 11 Nov 2026): an internal PlotNua guide link, only on a
    # product whose own published uses support it (Pod 17: "Home office", supplier's garden-office page).
    g = p.get("guide")
    guide = (f'<p class="aw-guide">{E(g["lead"])} <a href="{E(g["href"])}">{E(g["text"])}</a></p>'
             if g else "")
    return (f'<article class="aw-prod" aria-label="{E(p["name"])}">{img}<h4>{E(p["name"])}</h4>'
            f'<p class="aw-type">{E(p["kind"])}</p>'
            f'<p class="aw-sum">{E(p["summary"])}</p>{guide}'
            f'<div class="aw-price">{price_html(p)}</div>{note}'
            f'<dl class="aw-spec">{"".join(row(kv) for kv in key)}</dl>{rest}'
            f'<p class="aw-src">As published by {E(DATA["supplier"]["name"])} &middot; <a href="{E(p["source"])}" rel="noopener" target="_blank">product page</a> &middot; checked {int(p["checked"][8:10])} Nov 2026</p></article>')


def build():
    guard()
    s, I = DATA["supplier"], {i["id"]: i for i in DATA["images"]}
    hero = next(i for i in DATA["images"] if i["role"] == "hero")
    used = {hero["id"]}
    cats = []
    for c in DATA["categories"]:
        ps = [p for p in DATA["products"] if p["category"] == c["id"]]
        cats.append(f'<section class="aw-cat" id="{E(c["id"])}" aria-labelledby="{E(c["id"])}-h"><div class="aw-cat-h">'
                    f'<h3 id="{E(c["id"])}-h">{E(c["title"])}</h3><p>{E(c["line"])}</p></div>'
                    f'<div class="aw-grid">{"".join(product(p, I, used) for p in ps)}</div></section>')
    coll = [i for i in DATA["images"] if i["role"] == "collection" and i["id"] not in used]   # each image once
    n = len(DATA["products"])
    words = {5: "Five"}.get(n, str(n))
    jump = "".join(f'<li><a href="#{E(c["id"])}">{E(c["title"])}</a></li>' for c in DATA["categories"])
    costs = "".join(f'<div class="aw-cost"><h3>{E(k)}</h3><p>{E(v)}</p></div>' for k, v in DATA["costs"]["items"])
    notes = "".join(f'<div class="aw-note"><h3>{E(k)}</h3><p>{E(v)}</p></div>' for k, v in DATA["considerations"])
    wa = WHATSAPP + "?text=" + quote("Hi PlotNua, I'm looking at The Pod Factory's pods on PlotNua and would like some help (ref PF).")
    routes = f'<li><a class="pn-two-b" href="{E(wa)}" target="_blank" rel="noopener" data-pn-via="{VIA}">Ask PlotNua on WhatsApp <span aria-hidden="true">&rarr;</span></a></li>'
    head = HEAD.replace("{og}", E(hero["origin"]))
    if PREVIEW:
        head = head.replace('<meta name="robots" content="index, follow">',
                            '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">')
    band = ('<div class="aw-hold"><div class="aw-w"><b>Private preview</b><span>Prepared for founder review. '
            'Not yet published on PlotNua.</span></div></div>\n') if PREVIEW else ""
    return (head + CSS + (PREVIEW_CSS if PREVIEW else "") + f"""</head>
<body class="pn-id pn-id--dark pn-pd">
{band}<main id="pn-main" class="aw">
<nav class="aw-bar" aria-label="PlotNua"><div class="aw-w"><a class="aw-brand" href="../">PlotNua</a>
<div class="aw-back"><a href="../discovery-living-in-the-garden.html#suppliers"><span aria-hidden="true">&larr;</span> Living in the Garden</a></div></div></nav>

<section class="aw-hero" aria-labelledby="aw-h1"><div class="aw-w">
  <div>
    <p class="aw-k">Maker &middot; Living in the Garden</p>
    <h1 class="aw-h1" id="aw-h1">{E(s["name"])}</h1>
    <p class="aw-lede">{E(DATA["intro"])}</p>
    <ul class="aw-meta" role="list"><li>Based in {E(s["base"])}</li><li>Steel-framed, factory-built pods</li><li>Delivered and craned in across Ireland</li></ul>
    <ul class="aw-jump" role="list">{jump}</ul>
  </div>
  {fig(hero, first=True)}
</div></section>

<section class="aw-sec" id="collection" aria-labelledby="aw-col-h"><div class="aw-w">
  <div class="aw-head"><div><p class="aw-k">Finished pods</p><h2 class="aw-h2" id="aw-col-h">Built in the factory, lived in at home.</h2></div>
  <p class="aw-p">{E(DATA["standfirst"])}</p></div>
  <div class="aw-col">{"".join(fig(i, sizes="(max-width:700px) 100vw, (max-width:1100px) 50vw, 400px") for i in coll)}</div>
</div></section>

<section class="aw-sec" id="products" aria-labelledby="aw-pr-h"><div class="aw-w">
  <div class="aw-head"><div><p class="aw-k">The range</p><h2 class="aw-h2" id="aw-pr-h">{words} pods, made in Meath.</h2></div>
  <p class="aw-p">Sizes, rooms and finishes are the supplier&rsquo;s own, as published on its website. PlotNua has not changed or added to them. The Pod Factory publishes no prices: every pod is bespoke and quoted per project.</p></div>
  {"".join(cats)}
</div></section>

<section class="aw-sec" id="costs" aria-labelledby="aw-co-h"><div class="aw-w">
  <div class="aw-head"><div><p class="aw-k">Before you budget</p><h2 class="aw-h2" id="aw-co-h">{E(DATA["costs"]["title"])}</h2></div>
  <p class="aw-p">There is no published price to compare. A quote for your site is the starting point; ask what it includes.</p></div>
  <div class="aw-costs">{costs}</div>
  <p class="aw-fine">{E(DATA["costs"]["note"])}</p>
</div></section>

<section class="aw-sec" id="considerations" aria-labelledby="aw-cn-h"><div class="aw-w">
  <div class="aw-head"><div><p class="aw-k">For Irish homeowners</p><h2 class="aw-h2" id="aw-cn-h">Worth checking first.</h2></div>
  <p class="aw-p">General points, not an assessment of your property.</p></div>
  <div class="aw-notes">{notes}</div>
</div></section>

<section class="aw-sec aw-route" id="enquire" aria-labelledby="aw-en-h"><div class="aw-w">
  <div class="aw-head"><div><p class="aw-k">Next step</p><h2 class="aw-h2" id="aw-en-h">Two ways to go from here.</h2></div>
  <p class="aw-p">Browse at your own pace, or let PlotNua help you work out what would suit your garden and how you&rsquo;d use it, and then put you in touch with The Pod Factory. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Compare The Pod Factory with other garden room and garden home makers on PlotNua, side by side.</p>
      <a class="pn-two-a" href="../discovery-living-in-the-garden.html#suppliers">Garden rooms and garden homes <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p><p class="pn-two-t">Tell us what you&rsquo;re looking for. We&rsquo;ll help you narrow the options and, when you&rsquo;re ready, introduce you to The Pod Factory.</p>
      <ul class="pn-two-btns" role="list">{routes}</ul></div>
  </div>
  <div class="aw-book"><p class="aw-book-t"><b>See the pods in person</b><span>{E(s["name"])} offers showroom visits in {E(s["base"])}. Appointments are booked directly with {E(s["name"])} through its own booking page; PlotNua does not arrange or manage them.</span></p>
    <a class="aw-book-b" href="{E(s["bookingHref"])}" target="_blank" rel="noopener">Book an appointment with {E(s["name"])} <span aria-hidden="true">&rarr;</span></a></div>
  <p class="aw-fine">PlotNua is free for homeowners. PlotNua does not sell these products and cannot guarantee a supplier&rsquo;s availability or prices; you buy directly from the supplier. Inclusion here is not a recommendation or an endorsement, there is no paid placement, and recommendations cannot be bought.</p>
</div></section>

<footer class="aw-rec"><div class="aw-w">
  <p>Photography: {E(s["name"])}, from <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">thepodfactory.ie</a>, used with the supplier&rsquo;s permission. The supplier keeps ownership of its imagery.</p>
  <p>Product details checked against the supplier&rsquo;s website on 11 November 2026. Prices and specifications can change; confirm them with the supplier.</p>
  <p><a href="/terms.html#legal-information">Terms &amp; legal information</a></p>
</div></footer>
</main>
<script>/* readability: "More details" folds on phones (content stays in the page) */
if (window.matchMedia && matchMedia("(max-width:700px)").matches) document.querySelectorAll("details.aw-more").forEach(function (d) {{ d.removeAttribute("open"); }});
</script>
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
