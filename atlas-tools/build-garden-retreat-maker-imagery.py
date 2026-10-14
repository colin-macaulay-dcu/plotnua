#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — GARDEN RETREAT · A VISUAL INTRODUCTION TO THE LISTED MAKER

Founder decision, 14 October 2026: "Proceed with public presentation of OGNYX
using the four images authorised by Fabian." One editorial section, placed
directly above Garden Retreat's maker explorer, showing what the listed
products look like. It reuses PlotNua's established credited-figure pattern
(triq-cube.html: <figure>, an image served from the supplier's own domain, a
<figcaption> with the description and the credit) and the page's own tokens.

DATA-DRIVEN. The images are read from image-rights-records.json, OGNYX
approved_assets -- never typed here -- so the page can only ever show what the
rights record enumerates, in the record's own alt text.

WRITES discovery-garden-retreat.html: one scoped stylesheet block and one
section, both between markers. Nothing else on the page changes.

GUARDS
  V1 exactly the enumerated images, each once, src identical to the record
  V2 every figure carries the credit "© OGNYX" as a link to https://www.ognyx.com/
  V3 a visualisation is captioned AND alt-texted as a visualisation; a
     photograph is captioned as a photograph
  V4 no alteration: no object-fit:cover, filter, transform, clip-path, blend or
     inline style can reach these images; natural aspect ratio, shown whole
  V5 no claim the evidence does not support (delivery, installation, lead time,
     stock, VAT, health) and no endorsement vocabulary
  V6 every image shows a product that is PUBLIC in wellness-universe-v1.json
     (ELIGIBLE and PUBLISHABLE) -- never one of the twelve held
  V7 placement: after "Where this is sold in Ireland", directly before the
     maker explorer; exactly one section
  V8 the rest of the page is byte-identical to git HEAD
  V9 external links open safely (target _blank with rel noopener noreferrer)

  python3 atlas-tools/build-garden-retreat-maker-imagery.py --check | --apply
"""
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE_NAME = "discovery-garden-retreat.html"
PAGE = ROOT / PAGE_NAME
RECORDS = ROOT / "image-rights-records.json"
WELLNESS = ROOT / "wellness-universe-v1.json"
SITE = "https://www.ognyx.com/"
CREDIT = "© OGNYX"

CSS_B = "/* PLOTNUA-GR-MAKER-IMAGERY-CSS-BEGIN"
CSS_E = "/* PLOTNUA-GR-MAKER-IMAGERY-CSS-END */\n"
HTML_B = "  <!-- PLOTNUA-GR-MAKER-IMAGERY-BEGIN"
HTML_E = "  <!-- PLOTNUA-GR-MAKER-IMAGERY-END -->\n"
CSS_ANCHOR = "/* PLOTNUA A11Y VISUAL v1 · END */\n</style>"
HTML_ANCHOR = "  <!-- 6c · PLOTNUA-MAKER-EXPLORER-V1"

# Caption text per enumerated asset (short, homeowner-facing). Keyed by the
# Atlas asset id the rights record carries, so a caption cannot drift onto a
# different image.
CAPTIONS = {
    "recdcMBs7onIACLiO": "Stainless steel cold plunge tub for one",
    "recOfcMW6ZjQh8PHj": "The same tub, from above",
    "reczY9wkymWQg9df3": "1.6m outdoor sauna",
    "reccvs54yEV48AY7R": "Round hot tub with an integrated wood-fired stove",
}
# Intrinsic pixel sizes as served (width=1024), measured 14 Oct 2026, so the
# browser reserves each figure's space before the image arrives and nothing
# below it (the maker explorer, its #explore-makers anchor) jumps. Declared
# size only: the image is still shown whole at its natural ratio.
DIMS = {
    "recdcMBs7onIACLiO": (1024, 1026),
    "recOfcMW6ZjQh8PHj": (1024, 1031),
    "reczY9wkymWQg9df3": (1024, 1022),
    "reccvs54yEV48AY7R": (1024, 1024),
}
KIND_LABEL = {"photograph": "Photograph", "visualisation": "Visualisation"}

CSS = CSS_B + """ · Garden Retreat, the maker's own images (14 Oct 2026).
   PlotNua's credited-figure pattern (as on triq-cube.html), in this page's own
   tokens. The images are shown WHOLE at their natural aspect ratio: no
   object-fit crop, no filter, no transform -- unmodified, as authorised. */
  .gr-mi-grid{ display:grid; grid-template-columns:1fr; gap:28px; margin:34px 0 8px; }
  @media (min-width:720px){ .gr-mi-grid{ grid-template-columns:1fr 1fr; gap:32px 28px; } }
  .gr-mi-fig{ margin:0; }
  .gr-mi-fig img{ display:block; width:100%; height:auto; border-radius:3px;
    background:var(--cream); }
  .gr-mi-cap{ display:grid; grid-template-columns:1fr auto; align-items:start; gap:4px 16px;
    margin-top:10px; font-size:14px; line-height:1.5; color:var(--soft); }
  .gr-mi-kind{ display:block; font-size:11px; letter-spacing:.14em; text-transform:uppercase;
    color:var(--accent); margin-bottom:2px; }
  .gr-mi-credit{ align-self:end; }
  .gr-mi-cap .gr-mi-credit{ font-weight:600; letter-spacing:.04em; color:var(--ink); white-space:nowrap;
    text-decoration:underline; text-underline-offset:3px; text-decoration-thickness:1px; }
  .gr-mi-credit:hover,.gr-mi-credit:focus-visible{ color:var(--accent); }
  .gr-mi-note{ font-size:15px; line-height:1.6; color:var(--soft); max-width:62ch; margin-top:22px; }
""" + CSS_E


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def assets():
    recs = json.loads(RECORDS.read_text(encoding="utf-8"))["records"]
    row = [r for r in recs if r.get("organisation_name") == "OGNYX"]
    if len(row) != 1:
        die("V1 no single OGNYX rights record")
    a = row[0].get("approved_assets") or []
    if len(a) != 4:
        die("V1 the record does not enumerate exactly four images")
    if row[0].get("required_credit") != CREDIT:
        die("V2 the record's required credit is not %r" % CREDIT)
    return a


def section(A):
    figs = []
    # Group order: the plunge pair, then the sauna, then the hot tub -- the
    # order the page itself takes (sauna, hot tub, cold plunge) is editorial;
    # here the two photographs lead so the first thing seen is a real object.
    order = sorted(A, key=lambda a: (a["kind"] != "photograph", a["product_code"], not a.get("primary")))
    for a in order:
        cap = CAPTIONS.get(a["atlas_asset"])
        if not cap:
            die("V1 no caption for asset %s" % a["atlas_asset"])
        kind = KIND_LABEL[a["kind"]]
        figs.append(
            '      <figure class="gr-mi-fig">\n'
            '        <img src="%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async">\n'
            '        <figcaption class="gr-mi-cap"><span><span class="gr-mi-kind">%s</span> %s</span>'
            '<a class="gr-mi-credit" href="%s" target="_blank" rel="noopener noreferrer">%s</a></figcaption>\n'
            '      </figure>\n'
            % (html.escape(a["url"], quote=True), html.escape(a["alt"], quote=True),
               DIMS[a["atlas_asset"]][0], DIMS[a["atlas_asset"]][1], kind,
               html.escape(cap), SITE, CREDIT))
    return (HTML_B + " · the maker's own images, founder decision 14 Oct 2026.\n"
            "       Generated by atlas-tools/build-garden-retreat-maker-imagery.py from the\n"
            "       OGNYX approved_assets in image-rights-records.json; do not hand-edit. -->\n"
            '  <section class="article-section reveal" id="what-these-look-like">\n'
            '    <div class="kicker">What These Look Like</div>\n'
            "    <h2>Three of the listed products, in the maker&rsquo;s own images</h2>\n"
            "    <p>The saunas, hot tubs and cold plunges listed below are from OGNYX, and these\n"
            "      four images are OGNYX&rsquo;s, shown with its permission. Two are photographs of\n"
            "      a cold plunge tub. Two are computer-generated visualisations: they show how a\n"
            "      sauna and a hot tub look, not a real installation.</p>\n"
            '    <div class="gr-mi-grid">\n' + "".join(figs) + "    </div>\n"
            '    <p class="gr-mi-note">Each image shows a product, not a finished garden in\n'
            "      Ireland. PlotNua has not established delivery to your address, installation or\n"
            "      timing for any of these; that is for the maker to confirm. Images\n"
            '      &copy;&nbsp;OGNYX, shown as supplied, from <a href="%s" target="_blank"\n'
            '      rel="noopener noreferrer">ognyx.com</a>.</p>\n'
            "  </section>\n\n" % SITE + HTML_E)


def strip(src):
    for b, e in ((CSS_B, CSS_E), (HTML_B, HTML_E)):
        src = re.sub(re.escape(b) + r"[\s\S]*?" + re.escape(e), "", src)
    return src


def build(cur, A):
    base = strip(cur)
    if base.count(CSS_ANCHOR) != 1 or base.count(HTML_ANCHOR) != 1:
        die("V7 page anchors not found exactly once")
    out = base.replace(CSS_ANCHOR, CSS + CSS_ANCHOR, 1)
    return out.replace(HTML_ANCHOR, section(A) + HTML_ANCHOR, 1)


def guards(out, A):
    sec = out[out.index(HTML_B):out.index(HTML_E)]
    css = out[out.index(CSS_B):out.index(CSS_E)]
    imgs = re.findall(r"<img\b[^>]*>", sec)
    # V1
    srcs = [html.unescape(re.search(r'src="([^"]+)"', i).group(1)) for i in imgs]
    if sorted(srcs) != sorted(a["url"] for a in A):
        die("V1 the section's images are not exactly the enumerated four")
    if len(re.findall(r"https?://(?:www\.)?ognyx\.com/[^\"']+\.(?:png|jpe?g|webp)", out)) != 4:
        die("V1 an OGNYX image appears more than once, or elsewhere on the page")
    # V2
    figs = re.findall(r"<figure\b[\s\S]*?</figure>", sec)
    for f in figs:
        if ('href="%s"' % SITE) not in f or (">%s</a>" % CREDIT) not in f:
            die("V2 a figure lacks the linked credit")
    # V3
    by = {a["url"]: a for a in A}
    for f in figs:
        a = by[html.unescape(re.search(r'src="([^"]+)"', f).group(1))]
        alt = html.unescape(re.search(r'alt="([^"]*)"', f).group(1))
        label = re.search(r'class="gr-mi-kind">([^<]+)<', f).group(1)
        if a["kind"] == "visualisation" and (label != "Visualisation" or not alt.startswith("Visualisation")):
            die("V3 a visualisation is not labelled as one")
        if a["kind"] == "photograph" and label != "Photograph":
            die("V3 a photograph is not captioned as one")
    # V4
    for i in imgs:
        if "style=" in i:
            die("V4 an inline style reaches an image")
    css_code = re.sub(r"/\*[\s\S]*?\*/", " ", css + CSS_E)
    m = re.search(r"(?<![-\w])(object-fit|filter|transform|clip-path|mix-blend-mode|mask)\s*:", css_code)
    if m:
        die("V4 %s could alter an authorised image" % m.group(1))
    # V5
    vis = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<!--[\s\S]*?-->", " ", sec))).lower()
    for bad in ("free delivery", "delivery included", "delivered to", "we install", "installation included",
                "fully installed", "lead time of", "in stock", "vat included", "including vat", "health",
                "therapeutic", "recommended", "best ", "top pick", "trusted", "endorse", "featured",
                "partner", "sponsored", "approved by", "certified", "vetted"):
        if bad in vis:
            die("V5 unsupported claim or endorsement wording: %r" % bad.strip())
    if "has not established delivery" not in vis:
        die("V5 the delivery/installation/timing position must be stated as not established")
    # V6
    W = json.loads(WELLNESS.read_text(encoding="utf-8"))
    public = {p["productCode"] for p in W["products"]
              if p["qualification"]["state"] == "ELIGIBLE" and p["publicVisibility"] == "PUBLISHABLE"}
    for a in A:
        if a["product_code"] not in public:
            die("V6 an image shows %s, which is not public" % a["product_code"])
    # V7
    if out.count('id="what-these-look-like"') != 1:
        die("V7 the section is not present exactly once")
    i_sold, i_me, i_ex = (out.index("Where this is sold in Ireland"),
                          out.index('id="what-these-look-like"'), out.index('id="explore-makers"'))
    if not (i_sold < i_me < i_ex) or out.index(HTML_E) + len(HTML_E) != out.index(HTML_ANCHOR):
        die("V7 placement: after 'Where this is sold in Ireland', directly before the explorer")
    # V8
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + PAGE_NAME],
                              capture_output=True, text=True, check=True).stdout
        if strip(head) != strip(out):
            die("V8 the rest of the page differs from git HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  V8 skipped: git HEAD not available")
    # V9
    for a_tag in re.findall(r"<a\b[^>]*>", sec):
        if 'target="_blank"' in a_tag and 'rel="noopener noreferrer"' not in a_tag:
            die("V9 an external link opens without rel=noopener noreferrer")


def main():
    if "--apply" not in sys.argv and "--check" not in sys.argv:
        print(__doc__); sys.exit(1)
    A = assets()
    cur = PAGE.read_text(encoding="utf-8")
    out = build(cur, A)
    guards(out, A)
    if "--check" in sys.argv:
        if out != cur:
            print("CHECK FAILED: %s is out of date; run --apply" % PAGE_NAME); sys.exit(1)
        print("Garden Retreat maker imagery · CHECK OK — V1-V9 pass"); return
    PAGE.write_text(out, encoding="utf-8")
    print("Garden Retreat maker imagery · APPLIED — V1-V9 pass")


if __name__ == "__main__":
    main()
