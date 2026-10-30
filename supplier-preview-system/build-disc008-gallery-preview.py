#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER - PRIVATE GALLERY PREVIEWS FOR FEATURE-HELD DISC-008 MAKERS.

Founder instruction, 30 Oct 2026 ("Supplier gallery: final clean-up and next
phase", Phase 2): prepare private previews for Garden Room Ireland and Don
Modular Homes using the existing PlotNua gallery design. Both stay on
featureHold; nothing is published; no supplier is contacted.

WHAT A PREVIEW IS. The live Living in the Garden supplier gallery, rendered by
the PRODUCTION builder (atlas-tools/build-supplier-gallery.py, imported, not
copied) from the live page's own explorer data and the governed garden-room
imagery, with ONE in-memory change: the named maker's featureHold is lifted
for this rendering only. The editorial file, the live page, the shared gallery
component and every rights record are read, never written. The supplier sees
exactly the card the gallery would show: the same image, label, credit, link
and wording, among the makers already featured.

PRIVACY. Each page is noindex/nofollow, linked from nowhere, not in the
sitemap, and lives in supplier-preview-system/gallery-previews/ (outside the
site root, so the gallery guard's G9 - "no gallery on an unconfigured public
page" - is not engaged by a private page). Not deployed without founder
approval.

Run: python3 supplier-preview-system/build-disc008-gallery-preview.py [--check]
"""
import copy, hashlib, html, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "supplier-preview-system" / "gallery-previews"
PAGE = "discovery-living-in-the-garden.html"
E = lambda s: html.escape(str(s), quote=True)

# The only per-supplier facts here are restatements of the evidence on record.
SUPPLIERS = {
    "Garden Room Ireland": {
        "slug": "garden-room-ireland",
        "permission": ("On 2 October 2026 you replied “YES” to our request to feature Garden Room Ireland "
                       "and use selected images from your website to illustrate your products, with a clear credit "
                       "and a link back to you."),
        "medium_note": "A photograph of your QC6, as published on your own website.",
    },
    "Don Modular Homes": {
        "slug": "don-modular-homes",
        "permission": ("On 2 October 2026 you replied “Yes” to our request to feature Don Modular Homes "
                       "and use selected images from your website to illustrate relevant products and possibilities, "
                       "with a clear credit and a link back to you."),
        "medium_note": ("A computer-generated visualisation published on your own website. It is labelled "
                        "“Visualisation” wherever it appears, and is never presented as a photograph of a completed build."),
    },
}


def load_builder():
    spec = importlib.util.spec_from_file_location("sg", ROOT / "atlas-tools" / "build-supplier-gallery.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def render(sg, maker):
    sg.D = sg.DISCOVERIES[PAGE]
    ed = json.loads((sg.DATA / sg.D["editorial"]).read_text(encoding="utf-8"))
    if maker not in ed["makers"] or not ed["makers"][maker].get("featureHold"):
        sys.exit(f"FAIL: {maker} is not a feature-held maker in the live editorial file")
    ed_prev = copy.deepcopy(ed)
    ed_prev["makers"][maker].pop("featureHold")          # in memory only, for this preview
    sup = sg.collect(ROOT / PAGE, ed_prev)
    me = next(s for s in sup if s["name"] == maker)
    if not me["image"]:
        sys.exit(f"FAIL: {maker} has no governed image on the live page; no preview is built")
    head = json.loads(sg.HEADINGS.read_text(encoding="utf-8"))["discoveries"][PAGE]
    return ed_prev, head, sup, me


def page(sg, maker, ed, head, sup, me):
    s = SUPPLIERS[maker]
    img = me["image"]
    gallery_html = sg.gallery(ed, head, sup)
    # On the live page "View all suppliers" jumps to the Maker Explorer below the gallery. This
    # preview has no explorer, so the same link points to the live page's explorer instead.
    n = gallery_html.count('href="#explore-makers" data-sg-jump')
    if not n:
        sys.exit("FAIL: the live gallery's View-all link was not found")
    gallery_html = gallery_html.replace('href="#explore-makers" data-sg-jump',
                                        'href="https://plotnua.ie/discovery-living-in-the-garden.html#explore-makers" target="_blank" rel="noopener noreferrer"')
    v = sg.D["asset_v"]
    featured = [x["name"] for x in sup if x["image"] and not x["held"]][: ed["featuredMax"]]
    others = ", ".join(n for n in featured if n != maker)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<title>PlotNua &mdash; private gallery preview for {E(maker)}</title>
<!-- PRIVATE PAGE. noindex, nofollow, noarchive, nosnippet, noimageindex. Linked from nowhere; not in the
     sitemap. Built by supplier-preview-system/build-disc008-gallery-preview.py from the live Living in the
     Garden gallery (production builder, imported) with this maker's featureHold lifted IN MEMORY ONLY.
     Nothing on the live site is changed by this page. Do not hand-edit. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../../assets/identity/pn-identity.css">
<link rel="stylesheet" href="../../assets/identity/pn-premium-discovery.css">
<style>
  /* page frame for this private preview only; the gallery itself is the shared component, unmodified */
  /* the live Discovery article column, as pn-premium-discovery.css sets it on Living in the Garden */
  #pn-main > .article{{ max-width:var(--pd-max, 1240px); margin:0 auto; padding:0 clamp(16px,3vw,40px); box-sizing:border-box; }}
  .pv-wrap{{ }}
  .pv-head{{ padding:56px 0 8px; }}
  .pv-kicker{{ font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--p4-stone, #C2BDB5); margin:0 0 14px; }}
  .pv-head h1{{ font-family:'Instrument Serif',Georgia,serif; font-weight:400; font-size:clamp(30px,4vw,46px); line-height:1.15; margin:0 0 16px; }}
  .pv-head p, .pv-notes p, .pv-notes li{{ font-size:16px; line-height:1.75; max-width:62ch; }}
  .pv-head p + p{{ margin-top:12px; }}
  .pv-notes{{ padding:8px 0 72px; }}
  .pv-notes h2{{ font-family:'Instrument Serif',Georgia,serif; font-weight:400; font-size:clamp(24px,2.6vw,30px); margin:40px 0 14px; }}
  .pv-notes dl{{ display:grid; grid-template-columns:minmax(120px,190px) 1fr; gap:10px 24px; margin:0; max-width:760px; }}
  .pv-notes dt{{ font-size:12px; letter-spacing:.12em; text-transform:uppercase; opacity:.75; padding-top:4px; }}
  .pv-notes dd{{ margin:0; font-size:15.5px; line-height:1.65; overflow-wrap:anywhere; }}
  .pv-notes ul{{ margin:0; padding-left:20px; }}
  .pv-rule{{ border:0; border-top:1px solid var(--rule, #4A4B4F); margin:8px 0 0; }}
  @media (max-width:720px){{ .pv-notes dl{{ grid-template-columns:1fr; gap:2px 0; }} .pv-notes dd{{ margin-bottom:12px; }} }}
</style>
</head>
<body class="pn-id pn-id--dark pn-pd">
<main id="pn-main">
<div class="article"><div class="pv-wrap pv-head">
  <p class="pv-kicker">Private preview &middot; prepared for {E(maker)}</p>
  <h1>How {E(maker)} would appear on PlotNua</h1>
  <p>This is the &ldquo;{E(head["heading"])}&rdquo; gallery from PlotNua&rsquo;s <i>Living in the Garden</i> Discovery, shown with {E(maker)} included alongside the makers already featured ({E(others)}). Nothing here is published yet.</p>
  <p>The order of the cards changes on every visit, so no maker is placed above another. Inclusion is not a recommendation, and there is no paid placement.</p>
</div>
<link rel="stylesheet" href="../../assets/components/pn-supplier-gallery.css?v={E(v)}">
{gallery_html}
<script src="../../assets/components/pn-supplier-gallery.js?v={E(v)}" defer></script>
<div class="pv-wrap pv-notes">
  <hr class="pv-rule">
  <h2>Your card, in detail</h2>
  <dl>
    <dt>Image</dt><dd>{E(s["medium_note"])} Shown whole, never cropped or altered, and loaded from your own website.</dd>
    <dt>Label</dt><dd>{E(img["kind"])}</dd>
    <dt>Credit</dt><dd>{E(img["credit"])}, linked to {E(img["creditHref"])}</dd>
    <dt>Description</dt><dd>&ldquo;{E(me["description"])}&rdquo;</dd>
    <dt>Explore supplier</dt><dd>Opens {E(me["explore"])} in a new tab.</dd>
    <dt>Not shown</dt><dd>No prices, no location and no logo.</dd>
  </dl>
  <h2>Your permission</h2>
  <p>{E(s["permission"])} You keep ownership of your imagery, and if you ask us to change or remove anything, we will.</p>
  <h2>What we&rsquo;d ask</h2>
  <p>If this looks right, a simple reply is all we need. If you&rsquo;d like a different image, different wording or changes to anything else, tell us and we&rsquo;ll update it before anything goes live.</p>
</div>
</div>
</main>
</body>
</html>
"""


def main():
    sg = load_builder()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok_all = True
    for maker, s in SUPPLIERS.items():
        ed, head, sup, me = render(sg, maker)
        out = page(sg, maker, ed, head, sup, me)
        path = OUT_DIR / f"{s['slug']}-gallery-preview.html"
        if "--check" in sys.argv:
            ok = path.exists() and path.read_text(encoding="utf-8") == out
            ok_all &= ok
            print(f"{'CHECK OK' if ok else 'STALE  '} {path.relative_to(ROOT)}")
            continue
        path.write_text(out, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}: {me['image']['kind']} · {me['image']['credit']} → {me['image']['creditHref']}")
    if "--check" in sys.argv:
        sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
