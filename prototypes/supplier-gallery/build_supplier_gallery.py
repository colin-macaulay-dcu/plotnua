#!/usr/bin/env python3
"""
PLOTNUA - PREMIUM SUPPLIER GALLERY - prototype builder (v0.2)
Branch pass2/supplier-galleries. NOT IN PRODUCTION.
v0.1 30 Oct 2026 (design approved by founder 30 Oct 2026); v0.2 30 Oct 2026 refinements.

Builds prototypes/supplier-gallery/garden-retreat.html from:

  1. the LIVE Garden Retreat maker-explorer config
     (discovery-garden-retreat.html, <script id="mx-data">) -> which makers, their
     published product counts by category, their websites, their lead image and
     any existing commercial relationship;
  2. image-rights-records.json -> whether an image may be shown at all (PUBLISHABLE
     record, APPROVED asset, exact URL enumerated, required credit);
  3. garden-retreat.editorial.json -> PlotNua's own wording, the evidence behind any
     location line, and an optional choice among a maker's ALREADY APPROVED assets;
  4. discovery-headings.json -> the per-Discovery heading and introduction (the
     component itself is identical on every Discovery).

Nothing about a supplier is typed into this file.

Usage:  python3 prototypes/supplier-gallery/build_supplier_gallery.py [--check]
"""
import html, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DISCOVERY = ROOT / "discovery-garden-retreat.html"
RIGHTS = ROOT / "image-rights-records.json"
EDITORIAL = HERE / "garden-retreat.editorial.json"
HEADINGS = HERE / "discovery-headings.json"
OUT = HERE / "garden-retreat.html"
DATA_OUT = HERE / "garden-retreat.gallery.json"

E = lambda s: html.escape(str(s), quote=True)

TAB_LABEL = {"saunas": ("sauna", "saunas"), "hotTubs": ("hot tub", "hot tubs"), "coldPlunges": ("cold plunge", "cold plunges")}
DESC_NOUN = {"saunas": "outdoor saunas", "hotTubs": "hot tubs", "coldPlunges": "cold plunges"}  # the live explorer's own product types
# Candidate mount shapes. The builder picks the one that shows the featured
# images LARGEST on average (whole image always visible, never cropped).
MOUNTS = [(1, 1), (5, 6), (4, 5), (3, 4), (2, 3)]

ARROW_L = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>'
ARROW_R = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>'
EXT = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M6 3h7v7M13 3L4 12"/></svg>'
NEWTAB = '<span class="pn-sg-vh"> (opens in a new tab)</span>'


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
    makers, live_imgs = {}, {}
    for tab in cfg["tabs"]:
        key = tab["key"]
        for m in tab["makers"]:
            rec = makers.setdefault(m["m"], {"name": m["m"], "products": {}, "cats": {}, "sites": set(), "lead": None, "offer": None})
            for p in m["p"]:
                rec["products"][p[0]] = True
                rec["cats"][key] = rec["cats"].get(key, 0) + 1
                if len(p) > 5 and isinstance(p[5], dict):
                    if p[5].get("site"):
                        rec["sites"].add(p[5]["site"])
                    for i in p[5].get("img") or []:
                        live_imgs[i["src"]] = i
            if m.get("l"):
                live_imgs[m["l"]["src"]] = m["l"]
                rec["lead"] = rec["lead"] or m["l"]
            if m.get("o"):
                rec["offer"] = True

    out = []
    for name in sorted(makers, key=lambda n: n.casefold()):
        rec = makers[name]
        e = ed["makers"].get(name, {})
        cats = [(TAB_LABEL[k][1] if n != 1 else TAB_LABEL[k][0], n) for k, n in rec["cats"].items()]
        site = sorted(rec["sites"])[0] if rec["sites"] else None

        # image: an editorial choice among this maker's approved assets, else the live lead image
        src = e.get("image") or (rec["lead"] or {}).get("src")
        image = None
        if src:
            hit = approved.get(src)
            if e.get("image") and (not hit or hit[0] != name):
                sys.exit(f"FAIL: editorial image for {name} is not an approved asset of its own publishable grant")
            live = live_imgs.get(src)
            if hit and hit[0] == name and live and live.get("credit") == hit[1].get("required_credit"):
                image = {"src": src, "alt": live["alt"], "kind": live["kind"], "w": live["w"], "h": live["h"],
                         "credit": live["credit"], "creditHref": live["creditHref"]}
            elif e.get("image"):
                sys.exit(f"FAIL: {name}: chosen image has no live alt/dimensions/credit to reuse")

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


def best_mount(images):
    """The mount shape that shows the featured images largest on average (contain, no crop)."""
    def fill(mw, mh, w, h):
        r, m = w / h, mw / mh
        return (r / m) if r < m else (m / r)   # share of the mount's area the image covers
    return max(MOUNTS, key=lambda m: (sum(fill(m[0], m[1], i["w"], i["h"]) for i in images), m == (1, 1)))


def tags_html(s):
    t = []
    if s["placement"] == "sponsored":
        t.append('<span class="pn-sg-tag pn-sg-tag--sponsored">Sponsored</span>')
    if s["relationship"]:
        t.append(f'<span class="pn-sg-tag pn-sg-tag--rel">{E(s["relationship"]["label"])}</span>')
    return f'<div class="pn-sg-tags">{"".join(t)}</div>' if t else ""


def credit_html(img):
    return (f'<p class="pn-sg-cap"><span class="pn-sg-kind">{E(img["kind"])}</span>'
            f'<a href="{E(img["creditHref"])}" rel="noopener noreferrer" target="_blank">{E(img["credit"])}{NEWTAB}</a></p>')


def cta_html(s, compact=False):
    if not s["explore"]:
        return ""
    return (f'<p class="pn-sg-cta"><a href="{E(s["explore"])}" rel="noopener noreferrer" target="_blank" '
            f'aria-label="Explore {E(s["name"])} on {E(s["site"] or "its website")} (opens in a new tab)">'
            f'<span>{"Visit website" if compact else "Explore supplier"}</span>{EXT}</a></p>')


def img_tag(img, first):
    prio = ' fetchpriority="high"' if first else ""
    return (f'<img src="{E(img["src"])}" alt="{E(img["alt"])}" width="{img["w"]}" height="{img["h"]}" '
            f'loading="{"eager" if first else "lazy"}"{prio} decoding="async" referrerpolicy="no-referrer">')


def featured_card(s, first):
    """Focused: photograph, name, short description, verified location, Explore. Credit and labels kept."""
    img = s["image"]
    base = (f'<p class="pn-sg-loc"><b>{E(s["base"]["label"])}</b> {E(s["base"]["text"])}</p>') if s["base"] else ""
    rel = f'<p class="pn-sg-rel">{E(s["relationship"]["detail"])}</p>' if s["relationship"] else ""
    return (f'<article class="pn-sg-card" aria-label="{E(s["name"])}">'
            f'<figure class="pn-sg-fig"><div class="pn-sg-mount">{img_tag(img, first)}</div>'
            f'<figcaption>{credit_html(img)}</figcaption></figure>'
            f'<div class="pn-sg-body">{tags_html(s)}<h3 class="pn-sg-name">{E(s["name"])}</h3>'
            f'<p class="pn-sg-desc">{E(s["description"])}</p>{base}{rel}{cta_html(s)}</div></article>')


def index_entry(s):
    """Directory entry. Licensed image -> small mounted thumbnail with its credit.
    No licensed image -> a typographic entry: no frame, no placeholder, no invented visual."""
    img = s["image"]
    media = (f'<figure class="pn-sg-thumb"><div class="pn-sg-mount">{img_tag(img, False)}</div></figure>') if img else ""
    facts = []
    if s["base"]:
        facts.append(f'<div><dt>{E(s["base"]["label"])}</dt><dd>{E(s["base"]["text"])}</dd></div>')
    facts.append('<div><dt>On PlotNua</dt><dd>' + ", ".join(f'{c["count"]} {E(c["label"])}' for c in s["categories"]) + '</dd></div>')
    if s["site"]:
        facts.append(f'<div><dt>Website</dt><dd>{E(s["site"])}</dd></div>')
    rel = f'<p class="pn-sg-rel">{E(s["relationship"]["detail"])}</p>' if s["relationship"] else ""
    cap = credit_html(img) if img else ""
    return (f'<article class="pn-sg-entry{" has-img" if img else " is-text"}" aria-label="{E(s["name"])}">{media}'
            f'<div class="pn-sg-entry-body">{tags_html(s)}<h4 class="pn-sg-name">{E(s["name"])}</h4>'
            f'<p class="pn-sg-desc">{E(s["description"])}</p><dl class="pn-sg-facts">{"".join(facts)}</dl>'
            f'{rel}{cap}{cta_html(s, compact=True)}</div></article>')


def gallery(ed, head, sup):
    featured = [s for s in sup if s["image"]][: ed["featuredMax"]]
    mw, mh = best_mount([s["image"] for s in featured]) if featured else (1, 1)
    total = len(sup)
    more = total > len(featured)
    items = "".join(f'<li data-sg-placement="{s["placement"]}">{featured_card(s, i == 0)}</li>' for i, s in enumerate(featured))
    if more:
        items += (f'<li data-sg-end><div class="pn-sg-card pn-sg-card--end"><p class="pn-sg-end-n">{total}</p>'
                  f'<p class="pn-sg-end-t">{E(head["endLine"])}</p>'
                  f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="sg-all-gr" '
                  f'data-sg-open="View all suppliers" data-sg-close="Hide the full list"><span data-sg-label>View all suppliers</span></button></div></li>')
    grid = "".join(f"<li>{index_entry(s)}</li>" for s in sup)
    n_img = sum(1 for s in sup if s["image"])
    view_all = (f'<button type="button" class="pn-sg-all" data-sg-all aria-controls="sg-all-gr" '
                f'data-sg-open="View all {total} suppliers" data-sg-close="Hide the full list">'
                f'<span data-sg-label>View all {total} suppliers</span></button>') if more else ""
    grid_note = ed["gridNote"] if n_img < total else ed.get("gridNoteAllImaged", "")
    return f'''<section class="pn-sg" id="suppliers" data-pn-supplier-gallery data-discovery="{E(ed["discovery"])}" aria-labelledby="sg-h" style="--sg-mount-ratio:{mw} / {mh}">
  <div class="pn-sg-wrap">
    <header class="pn-sg-head">
      <div>
        <span class="pn-sg-kicker">{E(head["kicker"])}</span>
        <h2 class="pn-sg-h2" id="sg-h">{E(head["heading"])}</h2>
        <p class="pn-sg-intro">{E(head["intro"])}</p>
        <p class="pn-sg-note">{E(ed["selectionNote"])}</p>
      </div>
      <div class="pn-sg-controls">
        <button type="button" class="pn-sg-arrow" data-sg-prev aria-label="Previous supplier" aria-controls="sg-track">{ARROW_L}</button>
        <button type="button" class="pn-sg-arrow" data-sg-next aria-label="Next supplier" aria-controls="sg-track">{ARROW_R}</button>
        {view_all}
      </div>
    </header>
  </div>
  <ul class="pn-sg-track" id="sg-track" tabindex="0" role="list" aria-label="Featured suppliers, scroll horizontally">{items}</ul>
  <div class="pn-sg-wrap">
    <div class="pn-sg-grid-wrap" id="sg-all-gr">
      <div class="pn-sg-grid-head">
        <h3 class="pn-sg-h3" tabindex="-1">All {total} suppliers</h3>
        <p class="pn-sg-note">{E(grid_note)}</p>
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
{preconnect}
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
    heads = json.loads(HEADINGS.read_text(encoding="utf-8"))["discoveries"]
    head = heads.get(ed["discovery"])
    if not head:
        sys.exit(f"FAIL: no heading set for {ed['discovery']} in discovery-headings.json")
    hosts = sorted({urlparse(s["image"]["src"]).netloc for s in sup if s["image"]})
    pre = "\n".join(f'<link rel="preconnect" href="https://{h}">' for h in hosts)
    page = PAGE.format(gallery=gallery(ed, head, sup), preconnect=pre)
    data = json.dumps({"discovery": ed["discovery"], "heading": head, "suppliers": sup}, ensure_ascii=False, indent=1) + "\n"
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == page and DATA_OUT.read_text(encoding="utf-8") == data
        print("build is current" if ok else "FAIL: prototype is stale; rebuild")
        sys.exit(0 if ok else 1)
    OUT.write_text(page, encoding="utf-8")
    DATA_OUT.write_text(data, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(sup)} suppliers, {sum(1 for s in sup if s['image'])} with licensed imagery")


if __name__ == "__main__":
    main()
