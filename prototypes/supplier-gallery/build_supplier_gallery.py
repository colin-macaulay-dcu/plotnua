#!/usr/bin/env python3
"""
PLOTNUA - PREMIUM SUPPLIER GALLERY - prototype builder (v0.1)
Branch pass2/supplier-galleries, 30 Oct 2026. NOT IN PRODUCTION.

Builds prototypes/supplier-gallery/garden-retreat.html from three inputs:

  1. the LIVE Garden Retreat maker-explorer config
     (discovery-garden-retreat.html, <script id="mx-data">)  -> which makers,
     their published product counts by category, their websites, their lead
     image, and any existing commercial relationship;
  2. image-rights-records.json -> whether that lead image may be shown at all
     (PUBLISHABLE record, APPROVED asset, exact URL listed, required credit);
  3. garden-retreat.editorial.json -> PlotNua's own wording and the evidence
     behind any location line.

Nothing about a supplier is typed into this file. A maker whose image is not
an approved asset of a publishable grant is still listed, by name only.

Usage:  python3 prototypes/supplier-gallery/build_supplier_gallery.py [--check]
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DISCOVERY = ROOT / "discovery-garden-retreat.html"
RIGHTS = ROOT / "image-rights-records.json"
EDITORIAL = HERE / "garden-retreat.editorial.json"
OUT = HERE / "garden-retreat.html"
DATA_OUT = HERE / "garden-retreat.gallery.json"

E = lambda s: html.escape(str(s), quote=True)

TAB_LABEL = {"saunas": ("sauna", "saunas"), "hotTubs": ("hot tub", "hot tubs"), "coldPlunges": ("cold plunge", "cold plunges")}

DESC_NOUN = {"saunas": "outdoor saunas", "hotTubs": "hot tubs", "coldPlunges": "cold plunges"}  # the live explorer's own product types

ARROW_L = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>'
ARROW_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
EXT = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 3h7v7M13 3L4 12"/></svg>'


def load_explorer():
    s = DISCOVERY.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" class="pn-mx-config" id="mx-data">(.*?)</script>', s, re.S)
    if not m:
        sys.exit("FAIL: Garden Retreat explorer config not found")
    return json.loads(m.group(1))


def approved_index():
    """URL -> (org name, record, asset) for every APPROVED asset of a PUBLISHABLE grant."""
    idx = {}
    for r in json.loads(RIGHTS.read_text(encoding="utf-8"))["records"]:
        if not r.get("permission_outcome", "").startswith("Granted"):
            continue
        if r.get("public_visibility") != "PUBLISHABLE" or r.get("asset_approval_state") != "APPROVED":
            continue
        for a in r.get("approved_assets") or []:
            idx[a["url"]] = (r["organisation_name"], r, a)
    return idx


def collect():
    cfg = load_explorer()
    ed = json.loads(EDITORIAL.read_text(encoding="utf-8"))
    approved = approved_index()
    makers = {}
    for tab in cfg["tabs"]:
        key = tab["key"]
        for m in tab["makers"]:
            rec = makers.setdefault(m["m"], {"name": m["m"], "products": {}, "cats": {}, "sites": set(), "lead": None, "offer": None})
            for p in m["p"]:
                rec["products"][p[0]] = True
                rec["cats"][key] = rec["cats"].get(key, 0) + 1
                if len(p) > 5 and isinstance(p[5], dict) and p[5].get("site"):
                    rec["sites"].add(p[5]["site"])
            if m.get("l") and not rec["lead"]:
                rec["lead"] = m["l"]
            if m.get("o"):
                rec["offer"] = True

    out = []
    for name in sorted(makers, key=lambda n: n.casefold()):
        rec = makers[name]
        e = ed["makers"].get(name, {})
        cats = [(TAB_LABEL[k][1] if n != 1 else TAB_LABEL[k][0], n) for k, n in rec["cats"].items()]
        site = sorted(rec["sites"])[0] if rec["sites"] else None
        image = None
        if rec["lead"]:
            hit = approved.get(rec["lead"]["src"])
            if hit and hit[0] == name and rec["lead"].get("credit") == hit[1].get("required_credit"):
                L = rec["lead"]
                image = {"src": L["src"], "alt": L["alt"], "kind": L["kind"], "w": L["w"], "h": L["h"],
                         "credit": L["credit"], "creditHref": L["creditHref"]}
        explore = image["creditHref"] if image else (f"https://{site}/" if site else None)
        desc = e.get("description") or (join([DESC_NOUN[k] for k in rec["cats"]]) + ".")
        rel = ed.get("relationships", {}).get(name)
        if rec["offer"] and not rel:
            sys.exit(f"FAIL: {name} has a commercial offer in the live config but no disclosure in the editorial file")
        out.append({
            "name": name,
            "description": desc,
            "base": e.get("base"),
            "categories": [{"label": c, "count": n} for c, n in cats],
            "productCount": len(rec["products"]),
            "site": site,
            "explore": explore,
            "image": image,
            "logo": None,                 # no logo permission is recorded for any supplier
            "placement": "editorial",     # 'sponsored' is reserved; none exist
            "relationship": rel,
        })
    return ed, out


def join(words):
    words = [w[0].upper() + w[1:] if i == 0 else w for i, w in enumerate(words)]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def cats_line(s):
    return " · ".join(f'{c["count"]} {c["label"]}' for c in s["categories"])


def card(s, featured, first=False):
    tags = []
    if s["placement"] == "sponsored":
        tags.append('<span class="pn-sg-tag pn-sg-tag--sponsored">Sponsored</span>')
    if s["relationship"]:
        tags.append(f'<span class="pn-sg-tag pn-sg-tag--rel">{E(s["relationship"]["label"])}</span>')
    img = s["image"]
    if img:
        loading = 'eager' if first else 'lazy'
        media = (f'<figure class="pn-sg-fig"><div class="pn-sg-mount">'
                 f'<img src="{E(img["src"])}" alt="{E(img["alt"])}" width="{img["w"]}" height="{img["h"]}" loading="{loading}" decoding="async" referrerpolicy="no-referrer">'
                 f'</div><figcaption class="pn-sg-cap"><span class="pn-sg-kind">{E(img["kind"])}</span>'
                 f'<a href="{E(img["creditHref"])}" rel="noopener" target="_blank">{E(img["credit"])}<span class="pn-sg-vh"> (opens in a new tab)</span></a></figcaption></figure>')
    else:
        media = (f'<div class="pn-sg-plate" aria-hidden="true"><p class="pn-sg-plate-initial">{E(s["name"][0])}</p>'
                 f'<p class="pn-sg-plate-note">Imagery not licensed to PlotNua</p></div>')
    meta = []
    if s["base"]:
        meta.append(f'<li><b>{E(s["base"]["label"])}</b><span>{E(s["base"]["text"])}</span></li>')
    meta.append(f'<li><b>On PlotNua</b><span>{E(cats_line(s))}</span></li>')
    if s["site"]:
        meta.append(f'<li><b>Website</b><span>{E(s["site"])}</span></li>')
    rel = f'<p class="pn-sg-rel">{E(s["relationship"]["detail"])}</p>' if s["relationship"] else ""
    cta = ""
    if s["explore"]:
        cta = (f'<div class="pn-sg-cta"><a href="{E(s["explore"])}" rel="noopener" target="_blank" '
               f'aria-label="Explore {E(s["name"])} on {E(s["site"] or "its website")} (opens in a new tab)">'
               f'<span>Explore supplier</span>{EXT}</a></div>')
    hn = "h3" if featured else "h4"
    return (f'<article class="pn-sg-card" aria-label="{E(s["name"])}">{media}<div class="pn-sg-body">'
            f'{"<div class=pn-sg-tags>" + "".join(tags) + "</div>" if tags else ""}'
            f'<{hn} class="pn-sg-name">{E(s["name"])}</{hn}><p class="pn-sg-desc">{E(s["description"])}</p>'
            f'<ul class="pn-sg-meta">{"".join(meta)}</ul>{rel}{cta}</div></article>')


def gallery(ed, sup):
    featured = [s for s in sup if s["image"]][: ed["featuredMax"]]
    total = len(sup)
    more = total > len(featured)
    items = "".join(f'<li data-sg-placement="{s["placement"]}">{card(s, True, i == 0)}</li>' for i, s in enumerate(featured))
    if more:
        items += (f'<li data-sg-end><div class="pn-sg-card pn-sg-card--end"><p class="pn-sg-end-n">{total}</p>'
                  f'<p class="pn-sg-end-t">makers in this Discovery, A&nbsp;to&nbsp;Z.</p>'
                  f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="sg-all-gr" '
                  f'data-sg-open="View all suppliers" data-sg-close="Hide the full list"><span data-sg-label>View all suppliers</span></button></div></li>')
    grid = "".join(f"<li>{card(s, False)}</li>" for s in sup)
    view_all = (f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="sg-all-gr" '
                f'data-sg-open="View all {total} suppliers" data-sg-close="Hide the full list">'
                f'<span data-sg-label>View all {total} suppliers</span></button>') if more else ""
    return f'''<section class="pn-sg" id="suppliers" data-pn-supplier-gallery aria-labelledby="sg-h">
  <div class="pn-sg-wrap">
    <header class="pn-sg-head">
      <div>
        <span class="pn-sg-kicker">{E(ed["kicker"])}</span>
        <h2 class="pn-sg-h2" id="sg-h">{E(ed["heading"])}</h2>
        <p class="pn-sg-intro">{E(ed["intro"])}</p>
        <p class="pn-sg-note">{E(ed["selectionNote"])}</p>
      </div>
      <div class="pn-sg-controls">
        <button type="button" class="pn-sg-arrow" data-sg-prev aria-label="Previous maker" aria-controls="sg-track">{ARROW_L}</button>
        <button type="button" class="pn-sg-arrow" data-sg-next aria-label="Next maker" aria-controls="sg-track">{ARROW_R}</button>
        {view_all}
      </div>
    </header>
  </div>
  <ul class="pn-sg-track" id="sg-track" tabindex="0" role="list" aria-label="Featured makers, scroll horizontally">{items}</ul>
  <div class="pn-sg-wrap">
    <div class="pn-sg-grid-wrap" id="sg-all-gr">
      <div class="pn-sg-grid-head">
        <h3 class="pn-sg-h3" tabindex="-1">All {total} suppliers</h3>
        <p class="pn-sg-note">{E(ed["gridNote"])}</p>
      </div>
      <ul class="pn-sg-grid" role="list">{grid}</ul>
    </div>
  </div>
</section>'''


PAGE = '''<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#2A2622">
<title>PROTOTYPE · Supplier gallery · Garden Retreat · PlotNua</title>
<!-- PROTOTYPE ONLY. pass2/supplier-galleries. Not linked from any page, not for publication.
     Generated by prototypes/supplier-gallery/build_supplier_gallery.py; do not hand-edit. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../../assets/components/pn-supplier-gallery.css">
<style>
  body{{ margin:0; background:#1B1C1E; }}
  .proto-bar{{ font:600 13px/1.4 'Hanken Grotesk',system-ui,sans-serif; letter-spacing:.06em; color:#1B1C1E; background:#CF8566; padding:10px 20px; text-align:center; }}
  .proto-ctx{{ max-width:1240px; margin:0 auto; padding:56px clamp(16px,3vw,40px) 0; font-family:'Hanken Grotesk',system-ui,sans-serif; color:#C2BDB5; font-size:15px; }}
  .proto-ctx a{{ color:#CF8566; }}
</style>
</head>
<body class="pn-id">
<div class="proto-bar" role="note">PROTOTYPE — Premium Supplier Gallery · Garden Retreat · not published</div>
<main id="pn-main">
<p class="proto-ctx">Shown here as it would sit inside <a href="../../discovery-garden-retreat.html">Garden Retreat</a>, directly before “Explore makers and products”.</p>
{gallery}
</main>
<script src="../../assets/components/pn-supplier-gallery.js" defer></script>
</body>
</html>
'''


def main():
    ed, sup = collect()
    page = PAGE.format(gallery=gallery(ed, sup))
    data = json.dumps({"discovery": ed["discovery"], "suppliers": sup}, ensure_ascii=False, indent=1) + "\n"
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == page and DATA_OUT.read_text(encoding="utf-8") == data
        print("build is current" if ok else "FAIL: prototype is stale; rebuild")
        sys.exit(0 if ok else 1)
    OUT.write_text(page, encoding="utf-8")
    DATA_OUT.write_text(data, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(sup)} suppliers, {sum(1 for s in sup if s['image'])} with licensed imagery")


if __name__ == "__main__":
    main()
