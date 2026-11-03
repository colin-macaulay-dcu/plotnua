#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - PRIVATE STAGING: THE MOBILE PODS SUPPLIER SHOWCASE (founder brief, 3 Nov 2026).

Builds two PRIVATE pages from supplier-preview-system/showcases/the-mobile-pods/showcase.json:

  1. the-mobile-pods-showcase.html   - the premium supplier showcase (hero, curated photo
     collection, models with verified specifications, free guided route, recognition);
  2. the-mobile-pods-disc008-preview.html - the LIVE Living in the Garden supplier gallery,
     rendered by the PRODUCTION builder (atlas-tools/build-supplier-gallery.py, imported,
     not copied), with a Mobile Pods card added IN MEMORY ONLY. Nothing live is written.

PUBLICATION HOLD. The supplier's explicit permission to publish its photographs on
plotnua.ie is awaiting confirmation (showcase.json "publication"). These pages are
noindex/nofollow, linked from nowhere, outside the sitemap, and are built only on a
development branch; they are never merged to main while the hold stands.

IMAGES. Two delivery modes, one data file:
  default            - image src = the supplier's own published URL (images[].origin).
                       Used for the branch copy, so NO supplier photograph is copied
                       into the public repository.
  --bundle DIR       - image src = images[].local (optimised copies, whole frame, no crop),
                       for the private staging bundle given to the founder.
Swapping in the supplier's higher-resolution originals = replace images[].local / origin
for the same slot id. No page code changes.

Run: python3 supplier-preview-system/build-mobile-pods-showcase.py [--bundle DIR] [--check]
"""
import copy, html, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "supplier-preview-system" / "showcases" / "the-mobile-pods"
DATA = json.loads((HERE / "showcase.json").read_text(encoding="utf-8"))
E = lambda s: html.escape(str(s), quote=True)
LIVE = "https://plotnua.ie/"
VIA = "via=the-mobile-pods"   # attribution marker on PlotNua's own guided route (ignored by the Journey)


def img_src(img, bundle):
    return img["local"] if bundle else img["origin"]


def imgs():
    return {i["id"]: i for i in DATA["images"]}


def guard():
    """Facts guard: no invented prices, names or endorsements; every image sourced."""
    s = DATA["supplier"]
    for i in DATA["images"]:
        for k in ("origin", "sourcePage", "sha256", "alt", "kind", "local"):
            if not i.get(k):
                sys.exit(f"FAIL: image {i['id']} lacks {k}")
        if not i["origin"].startswith("https://themobilepods.ie/wp-content/uploads/"):
            sys.exit(f"FAIL: image {i['id']} is not from the supplier's own site")
    allowed_prices = {"From €40,406 inc. VAT (turnkey), as published by the supplier",
                      "From €48,152.37 inc. VAT (turnkey), as published by the supplier",
                      "Not published; quoted per design"}
    for p in DATA["products"]:
        if p["name"] not in {"Deluxe21", "Deluxe25+", "Custom builds"}:
            sys.exit(f"FAIL: product name {p['name']} is not one the supplier publishes")
        for k, v in p["specs"]:
            if "€" in v or "price" in k.lower():
                if v not in allowed_prices:
                    sys.exit(f"FAIL: unverified price text for {p['name']}: {v}")
        if not p["source"].startswith(s["website"]):
            sys.exit(f"FAIL: {p['name']} specs are not sourced to the supplier site")
    if not DATA["publication"]["status"].startswith("HOLD"):
        sys.exit("FAIL: this builder only runs while the publication hold is recorded")


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<title>{title}</title>
<!-- PRIVATE STAGING PAGE. Built by supplier-preview-system/build-mobile-pods-showcase.py. Not linked, not in the
     sitemap, not published. Supplier photographs are under a publication hold (showcase.json). Do not hand-edit. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{css}assets/identity/pn-identity.css">
<link rel="stylesheet" href="{css}assets/identity/pn-premium-discovery.css">
"""

CSS = """<style>
/* The Mobile Pods showcase - scoped to .mp. Uses the site's --p4-* identity tokens. Supplier
   images are shown WHOLE: natural aspect ratio, never cropped, filtered, rounded or overlaid. */
.mp{ --ink:var(--p4-ivory,#F2EBE0); --soft:var(--p4-lime,#E7DED0); --stone:var(--p4-stone,#C2BDB5);
  --bronze:var(--p4-bronze-text,#B39272); --line:var(--p4-line2,#4A4B4F); --card:var(--p4-deep,#2C2E30);
  --well:var(--p4-well,#2D2E31); --serif:var(--p4-serif,'Instrument Serif',Georgia,serif);
  --sans:var(--p4-sans,'Hanken Grotesk',system-ui,sans-serif);
  color:var(--soft); font-family:var(--sans); }
.mp *{ box-sizing:border-box; }
.mp-w{ max-width:1240px; margin:0 auto; padding:0 clamp(18px,3.4vw,44px); }
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
.mp-also{ margin-top:22px; font-size:15px; color:var(--stone); }
/* the guided route reuses the Discovery two-option component (pn-two-option.css) as-is */
.mp-route .pn-two{ max-width:none; }
.mp-fine{ margin:26px 0 0; font-size:13.5px; line-height:1.7; color:var(--stone); max-width:78ch; }
.mp-rec{ padding:34px 0 64px; border-top:1px solid var(--line); font-size:13.5px; line-height:1.7; color:var(--stone); }
.mp-rec p{ margin:0 0 6px; max-width:80ch; }
.mp-rec a{ color:inherit; }
@media (max-width:900px){
  .mp-hero .mp-w, .mp-head, .mp-model, .mp-notes{ grid-template-columns:1fr; }
  .mp-hero .mp-fig img{ max-height:none; width:100%; }
  .mp-hero .mp-cap{ justify-content:flex-start; }
}
@media (max-width:560px){ .mp-spec{ grid-template-columns:1fr; } .mp-spec dt{ border-bottom:0; padding-bottom:0; } }
</style>
"""


def fig(i, bundle, credit_href, first=False, cls=""):
    lazy = 'loading="eager" fetchpriority="high"' if first else 'loading="lazy"'
    return (f'<figure class="mp-fig{cls}"><img src="{E(img_src(i, bundle))}" alt="{E(i["alt"])}" width="{i["w"]}" height="{i["h"]}" '
            f'{lazy} decoding="async" referrerpolicy="no-referrer" data-pn-slot="{E(i["id"])}" data-pn-origin="{E(i["origin"])}">'
            f'<figcaption class="mp-cap"><span class="mp-kind">{E(i["kind"])}</span>'
            f'<span>{E(i.get("caption",""))} <a href="{E(credit_href)}" rel="noopener" target="_blank">{E(DATA["supplier"]["credit"])}</a></span></figcaption></figure>')


def journeys(prefix):
    return [("A garden home", f"{prefix}your-plot.html?discovery=residential&{VIA}"),
            ("A garden room", f"{prefix}your-plot.html?discovery=garden-room&{VIA}")]


def showcase(bundle):
    s, I = DATA["supplier"], imgs()
    hero = next(i for i in DATA["images"] if i["role"] == "hero")
    coll = [i for i in DATA["images"] if i["role"] == "collection"]
    css_prefix = "" if bundle else "../../../"
    prefix = LIVE  # guided route always targets the live Journey (PlotNua's own, tracked)
    models = []
    for p in DATA["products"]:
        dl = "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in p["specs"])
        plan = (f'<div class="mp-plan">{fig(I[p["plan"]], bundle, s["creditHref"])}</div>') if p["plan"] else ""
        models.append(
            f'<article class="mp-model{"" if plan else " no-plan"}" aria-label="{E(p["name"])}"><div>'
            f'<h3>{E(p["name"])}</h3><p class="mp-kind2">{E(p["kind"])}</p><p class="mp-sum">{E(p["summary"])}</p>'
            f'<dl class="mp-spec">{dl}</dl>'
            f'<p class="mp-src">As published by {E(s["name"])} &middot; checked {E(p["checked"][8:10])} Nov 2026</p></div>{plan}</article>')
    j = "".join(f'<li><a class="pn-two-b" href="{E(h)}">{E(l)} <span aria-hidden="true">&rarr;</span></a></li>' for l, h in journeys(prefix))
    two_css = "assets/components/pn-two-option.css" if bundle else "../../../assets/components/pn-two-option.css"
    return (HEAD.format(title="The Mobile Pods &mdash; PlotNua supplier showcase (private staging)", css=css_prefix) + CSS +
f"""<link rel="stylesheet" href="{two_css}?v=1">
</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main" class="mp">
<div class="mp-hold"><div class="mp-w"><b>Private staging</b><span>Not published. Supplier photographs are held from plotnua.ie until written publication permission is recorded.</span></div></div>

<section class="mp-hero" aria-labelledby="mp-h1"><div class="mp-w">
  <div>
    <p class="mp-k">Supplier showcase &middot; Living in the Garden</p>
    <h1 class="mp-h1" id="mp-h1">{E(s["name"])}</h1>
    <p class="mp-lede">{E(DATA["intro"])}</p>
    <ul class="mp-meta" role="list"><li>{E(s["county"])}</li><li>Timber-frame pods and garden homes</li><li>Built to order</li></ul>
  </div>
  {fig(hero, bundle, s["creditHref"], first=True)}
</div></section>

<section class="mp-sec" id="collection" aria-labelledby="mp-col-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">The collection</p><h2 class="mp-h2" id="mp-col-h">Built, delivered, lived in.</h2></div>
  <p class="mp-p">{E(DATA["standfirst"])}</p></div>
  <div class="mp-col">{"".join(fig(i, bundle, s["creditHref"]) for i in coll)}</div>
</div></section>

<section class="mp-sec" id="models" aria-labelledby="mp-mod-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">The models</p><h2 class="mp-h2" id="mp-mod-h">Two starting points, then yours.</h2></div>
  <p class="mp-p">The specifications below are the supplier&rsquo;s own, as published on its website. PlotNua has not changed or added to them.</p></div>
  <div class="mp-models">{"".join(models)}</div>
  <p class="mp-also">{E(DATA["alsoMakes"])}</p>
  <div class="mp-notes">
    <div class="mp-note"><h3>What the price covers</h3><p>{E(DATA["costNote"])}</p></div>
    <div class="mp-note"><h3>Planning</h3><p>{E(DATA["planningNote"])}</p></div>
  </div>
</div></section>

<section class="mp-sec mp-route" id="enquire" aria-labelledby="mp-en-h"><div class="mp-w">
  <div class="mp-head"><div><p class="mp-k">Next step</p><h2 class="mp-h2" id="mp-en-h">Is a pod right for your plot?</h2></div>
  <p class="mp-p">Before you contact any maker, PlotNua can help you work out what your garden can take and which options fit how you&rsquo;d use it. It&rsquo;s free.</p></div>
  <div class="pn-two" role="group" aria-label="Two ways to explore">
    <div class="pn-two-opt"><p class="pn-two-k">Explore yourself</p><p class="pn-two-t">Compare The Mobile Pods with other garden-home and garden-room makers on PlotNua, side by side.</p>
      <a class="pn-two-a" href="{LIVE}discovery-living-in-the-garden.html#explore-makers">Browse makers and products <span aria-hidden="true">&rarr;</span></a></div>
    <div class="pn-two-opt is-help"><p class="pn-two-k">Let PlotNua do the homework</p><p class="pn-two-t">Tell us what you&rsquo;re looking for. We&rsquo;ll use our Atlas research to help you find options that match your preferences and budget.</p>
      <ul class="pn-two-btns" role="list">{j}</ul></div>
  </div>
  <p class="mp-fine">PlotNua is free for homeowners. Inclusion here is not a recommendation, there is no paid placement, and recommendations cannot be bought.</p>
</div></section>

<footer class="mp-rec"><div class="mp-w">
  <p>Photography and floor plans: {E(s["name"])}, from <a href="{E(s["creditHref"])}" rel="noopener" target="_blank">themobilepods.ie</a>. The supplier keeps ownership of its imagery.</p>
  <p>Product details checked against the supplier&rsquo;s website on 3 November 2026. Prices and specifications can change; confirm them with the supplier.</p>
</div></footer>
</main>
</body>
</html>
""")


def disc008(bundle):
    """The live DISC-008 gallery, production builder, plus a Mobile Pods card in memory."""
    spec = importlib.util.spec_from_file_location("sg", ROOT / "atlas-tools" / "build-supplier-gallery.py")
    sg = importlib.util.module_from_spec(spec); spec.loader.exec_module(sg)
    d = DATA["disc008"]
    sg.D = sg.DISCOVERIES[d["page"]]
    ed = json.loads((sg.DATA / sg.D["editorial"]).read_text(encoding="utf-8"))
    sup = sg.collect(ROOT / d["page"], ed)
    if any(x["name"] == DATA["supplier"]["name"] for x in sup):
        sys.exit("FAIL: The Mobile Pods is already in the live explorer; this preview path is obsolete")
    i = imgs()[d["image"]]
    show = "the-mobile-pods-showcase.html"
    card = {"name": DATA["supplier"]["name"], "description": d["description"], "base": None,
            "categories": [{"label": "garden homes", "count": 2}], "productCount": 2,
            "site": "PlotNua", "explore": show,
            "image": {"src": img_src(i, bundle), "alt": i["alt"], "kind": i["kind"], "w": i["w"], "h": i["h"],
                      "credit": "Image: The Mobile Pods", "creditHref": DATA["supplier"]["creditHref"], "asset": i["origin"]},
            "logo": None, "placement": "editorial", "relationship": None, "held": False}
    ed2 = copy.deepcopy(ed)
    ed2["featuredMax"] = ed["featuredMax"] + 1     # in memory only: show it beside the live three
    sup2 = sorted(sup + [card], key=lambda x: x["name"].casefold())
    head = json.loads(sg.HEADINGS.read_text(encoding="utf-8"))["discoveries"][d["page"]]
    cfg = sg.load_explorer(ROOT / d["page"])
    g = sg.gallery(ed2, head, sup2, cfg)
    # the card's CTA goes to PlotNua's own showcase (same tab), not off-site
    g = g.replace(f'<a href="{show}" rel="noopener noreferrer" target="_blank" aria-label="Explore The Mobile Pods on PlotNua (opens in a new tab)">',
                  f'<a href="{show}" aria-label="Explore The Mobile Pods on PlotNua">', 1)
    k = g.index(f'<a href="{show}"')
    g = g[:k] + g[k:].replace(f"<span>Explore supplier</span>{sg.EXT}", "<span>Explore supplier</span><span aria-hidden=\"true\"> &rarr;</span>", 1)
    g = g.replace('href="#explore-makers" data-sg-jump', f'href="{LIVE}discovery-living-in-the-garden.html#explore-makers" target="_blank" rel="noopener noreferrer"')
    g = g.replace('href="your-plot.html?', f'href="{LIVE}your-plot.html?')
    pre = "" if bundle else "../../../"
    v = sg.D["asset_v"]
    return (HEAD.format(title="PlotNua &mdash; Living in the Garden with The Mobile Pods (private staging)", css=pre) +
f"""<style>#pn-main > .article{{ max-width:var(--pd-max,1240px); margin:0 auto; padding:0 clamp(16px,3vw,40px); }}
.pv-head{{ padding:48px 0 8px; }} .pv-head p{{ font-size:15.5px; line-height:1.7; max-width:66ch; color:#C2BDB5; }}
.pv-head b{{ font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:#B39272; }}</style>
<link rel="stylesheet" href="{pre}assets/components/pn-supplier-gallery.css?v={v}">
</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main"><div class="article">
<div class="pv-head"><p><b>Private staging &middot; DISC-008 integration preview</b></p>
<p>The live &ldquo;{E(head["heading"])}&rdquo; gallery from <i>Living in the Garden</i>, rendered by the production builder, with The Mobile Pods added beside the makers already featured. Its card links to PlotNua&rsquo;s own showcase page rather than off-site. The headline figures are the live explorer&rsquo;s and do not yet count The Mobile Pods. Nothing here is published.</p></div>
{g.replace('href="assets/components/', f'href="{pre}assets/components/')}
<script src="{pre}assets/components/pn-supplier-gallery.js?v={v}" defer></script>
</div></main>
</body>
</html>
""")


def main():
    guard()
    bundle = None
    if "--bundle" in sys.argv:
        bundle = Path(sys.argv[sys.argv.index("--bundle") + 1]).resolve()
    out_dir = bundle or HERE
    pages = {"the-mobile-pods-showcase.html": showcase(bool(bundle)),
             "the-mobile-pods-disc008-preview.html": disc008(bool(bundle))}
    ok = True
    for name, txt in pages.items():
        p = out_dir / name
        if "--check" in sys.argv:
            same = p.exists() and p.read_text(encoding="utf-8") == txt
            ok &= same
            print(("CHECK OK " if same else "STALE    ") + str(p))
        else:
            p.write_text(txt, encoding="utf-8")
            print("wrote", p)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
