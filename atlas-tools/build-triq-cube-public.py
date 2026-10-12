#!/usr/bin/env python3
"""
TRIQ CUBE · PUBLIC PAGE — BOUNDED BUILDER (12 October 2026)

Founder decision, 12 October 2026: TRIQBRIQ AG's product management approved
the landing page (Christian Klerner, email of 12 October 2026). The approved
page may proceed to public publication.

triq-cube-preview.html stays FROZEN (SUPPLIER-PREVIEW-SYSTEM-V1 §12). This
builder never writes it. It READS the approved blocks out of it verbatim and
assembles the public page triq-cube.html around them, with the standard
PlotNua public chrome (Cookiebot, GA4 G-PKKJ0RK6N8, favicons, brand mark,
search rail, footer).

Lifted verbatim from the approved preview (each must occur exactly once):
  IMG    the two official images with their "© TRIQBRIQ AG" credits
  PRICE  the published price card, options and the German-price basis note
  SPEC   the specification table (heading reworded: "How Atlas would record
         it" -> "Published specification"; TRIQ is not an Atlas product)
  EQUIP  the published equipment card and its chips (minus "Made in
         Germany", and the spec loses "Country of manufacture": founder
         decision 13 Oct 2026, claim not verifiable on triqbriq.de)
  OPEN   "What PlotNua has not established", every gap unchanged (one
         supplier-addressed sentence dropped: "A homeowner sees this panel too.")

Not carried over: stages 3-5 (My Plot / Compare / Decide). They described
capabilities the TRIQ CUBE does not have on PlotNua yet (it is not an Atlas
product), so publishing them would claim a capability PlotNua lacks.

The handoff control the preview showed inert ("Continue to TRIQBRIQ ->") is
made live, to the exact URL TRIQBRIQ asked for:
  https://triqbriq.de/produkt/triq-gartenoffice-3x3/
Every link to triqbriq.de fires one GA4 event, supplier_outbound_click, with
no personal data. Referrer is NOT suppressed (no noreferrer), so TRIQBRIQ's
own analytics can see plotnua.ie as the source.

  python3 atlas-tools/build-triq-cube-public.py --check | --apply
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "triq-cube-preview.html"
ABOUT = ROOT / "about.html"
OUT = ROOT / "triq-cube.html"
PREVIEW_SHA = "b06354ed4dfc66fadc10a787d572c191e3ca4ad4538be81485f8a06bf2e438a5"
PRODUCT_URL = "https://triqbriq.de/produkt/triq-gartenoffice-3x3/"
CANON = "https://plotnua.ie/triq-cube.html"
MARK = "PLOTNUA-TRIQ-CUBE-PUBLIC-V1"

def die(m): print("REFUSED: " + m); sys.exit(2)
def one(src, pat, lab):
    m = re.findall(pat, src, flags=re.S)
    if len(m) != 1: die(f"{lab}: expected exactly one match in the approved preview, found {len(m)}")
    return m[0]

pv = PREVIEW.read_text(encoding="utf-8")
sha = hashlib.sha256(pv.encode()).hexdigest()
if PREVIEW_SHA != "PINNED_AT_FIRST_RUN" and sha != PREVIEW_SHA:
    die("the frozen preview has changed since this builder was pinned")

IMG = one(pv, r'(  <div class="grid2" style="margin-top:var\(--pn-space-md\)">\n    <figure>.*?</figure>\n    <figure>.*?</figure>\n  </div>)', "IMG")
PRICE_SPEC = one(pv, r'(  <div class="grid2" style="margin-top:var\(--pn-space-md\)">\n    <div class="card">\n      <h3>Published price</h3>.*?</table>\n    </div>\n  </div>)', "PRICE+SPEC")
EQUIP = one(pv, r'(  <div class="card" style="margin-top:var\(--pn-space-md\)">\n    <h3>Published equipment</h3>.*?</ul>\n  </div>)', "EQUIP")
OPEN = one(pv, r'(  <div class="open-panel" style="margin-top:var\(--pn-space-md\)">\n    <h3 style="margin-bottom:4px">What PlotNua has not established</h3>.*?</ul>\n  </div>)', "OPEN")
# One sentence addressed the supplier reader of the preview ("A homeowner sees
# this panel too."). On the public page the reader IS the homeowner, so it is
# dropped. Nothing else in the panel changes.
OPEN_DROP = " A homeowner sees this panel too."
if OPEN.count(OPEN_DROP) != 1: die("OPEN: supplier-addressed sentence anchor")
OPEN_PUB = OPEN.replace(OPEN_DROP, "")
CSS = one(pv, r'<style>\n(.*?)</style>', "CSS")
for need in ("© TRIQBRIQ AG", "Exterior-3x3-1-scaled.jpg", "Interior-3x3-1-scaled.jpg"):
    if need not in IMG: die("IMG block lost " + need)
if IMG.count("© TRIQBRIQ AG") != 2: die("IMG must carry two credits")
SPEC_OLD = "<h3>How Atlas would record it</h3>"
if PRICE_SPEC.count(SPEC_OLD) != 1: die("SPEC heading anchor")
PRICE_SPEC_PUB = PRICE_SPEC.replace(SPEC_OLD, "<h3>Published specification</h3>")

# FOUNDER DECISION, 13 October 2026: remove the "Made in Germany" claim unless
# it can be independently verified; keep the factual manufacturer location.
# Checked on triqbriq.de the same night: the product page does not state where
# the TRIQ Office 3x3 is made; the production page names a Stammwerk in
# Tuebingen and licensed production in Austria (with more countries planned),
# and never ties this product to a country. So both forms of the claim go:
# the "Made in Germany" chip and the "Country of manufacture: Germany" row.
# "Manufacturer: TRIQBRIQ AG, Stuttgart" stays (the AG's published address).
ROW_COUNTRY = "        <tr><th>Country of manufacture</th><td>Germany</td></tr>\n"
CHIP_MIG = "      <li class=\"known\">Made in Germany</li>\n"
ROW_MAKER = "<tr><th>Manufacturer</th><td>TRIQBRIQ AG, Stuttgart</td></tr>"
if PRICE_SPEC_PUB.count(ROW_COUNTRY) != 1: die("country-of-manufacture row anchor")
if PRICE_SPEC_PUB.count(ROW_MAKER) != 1: die("manufacturer location row must be kept")
PRICE_SPEC_PUB = PRICE_SPEC_PUB.replace(ROW_COUNTRY, "")
if EQUIP.count(CHIP_MIG) != 1: die("Made in Germany chip anchor")
EQUIP_PUB = EQUIP.replace(CHIP_MIG, "")

ab = ABOUT.read_text(encoding="utf-8")
HEAD_TAGS = one(ab, r'^(<!DOCTYPE html>.*?gtag\(\'config\', \'G-PKKJ0RK6N8\'\);\n</script>\n)', "about head tags")
# The rail is the canonical stub, nofade variant (as on discoveries.html): this
# page's brand mark does not fade in, so the pill must not wait for it.
RAIL = one((ROOT / "discoveries.html").read_text(encoding="utf-8"),
           r'(<!-- PLOTNUA SEARCH RAIL v1 · BEGIN.*?<!-- PLOTNUA SEARCH RAIL v1 · END -->)', "rail")
if 'data-pns-nofade="true"' not in RAIL: die("rail: expected the nofade variant")
FOOTER = one(ab, r'(<footer>\n  <div class="footer-inner">.*?</footer>)', "footer")
FAVICONS = one(ab, r'(<!-- Favicons — PlotNua Brand Package v1\.0 -->.*?<meta name="theme-color" content="#1F3B2E">)', "favicons")

TITLE = "TRIQ CUBE garden office by TRIQBRIQ AG | PlotNua"
DESC = ("The TRIQ CUBE (TRIQ Office 3×3): a 9 m² solid-timber garden office from TRIQBRIQ AG, "
        "Stuttgart. Published price, specification and what isn't yet established for Ireland.")

page = HEAD_TAGS + f'''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{CANON}">
<!-- {MARK} · built by atlas-tools/build-triq-cube-public.py from the approved preview -->

{FAVICONS}

<!-- Open Graph · PlotNua's own image: TRIQBRIQ's permission does not cover social use -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="PlotNua">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="https://plotnua.ie/assets/og/plotnua-og-image-1200x630.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{CANON}">
<meta property="og:locale" content="en_IE">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="https://plotnua.ie/assets/og/plotnua-og-image-1200x630.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300..700&family=Work+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
/* ── PUBLIC CHROME (shared PlotNua brand mark + footer) ─────────── */
:root{{ --ink:#1F3B2E; --paper:#F5F2E8; --brand-ivory:#F2EFE6; --brand-sage:#8FAF8A; }}
body{{ overflow-x:hidden; }}
header.masthead{{ padding-top:104px; }}
.brand-mark{{ position:fixed; top:22px; left:22px; z-index:50; display:flex; align-items:center;
  justify-content:center; width:46px; height:46px; padding:0; background:var(--brand-ivory);
  border-radius:12px; box-shadow:0 1px 3px rgba(31,59,46,.16), 0 0 0 1px rgba(31,59,46,.07);
  text-decoration:none; }}
.brand-mark img{{ display:block; width:34px; height:34px; border-radius:8px; }}
@media(max-width:720px){{ .brand-mark{{ top:16px; left:16px; width:40px; height:40px; }}
  .brand-mark img{{ width:30px; height:30px; }} header.masthead{{ padding-top:88px; }} }}
.handoff-btn{{ display:inline-block; background:var(--pn-on-dark); color:var(--pn-voice);
  border:1px solid var(--pn-on-dark); border-radius:2px; padding:13px 22px;
  margin-top:var(--pn-space-sm); font-size:var(--pn-w-body); font-weight:500;
  text-decoration:none; transition:background .2s ease, color .2s ease; }}
.handoff-btn:hover{{ background:transparent; color:var(--pn-on-dark); }}
.handoff-btn:focus-visible{{ outline:2px solid var(--pn-on-dark); outline-offset:3px; }}
.handoff-note{{ display:block; font-size:var(--pn-w-body-sm); color:rgba(245,242,232,.72); margin-top:10px; }}
.next-link{{ font-size:var(--pn-w-body); }}
footer.page-notes{{ margin-top:var(--pn-space-section); padding:var(--pn-space-lg) 0 var(--pn-space-lg);
  border-top:1px solid var(--pn-hair); font-size:var(--pn-w-body-sm); color:var(--pn-stone); }}
footer.page-notes p{{ max-width:76ch; }}
footer.site{{ background:linear-gradient(180deg, var(--paper) 0%, var(--ink) 110px, var(--ink) 100%);
  color:#B7AF9C; padding:72px 7vw 40px; margin-top:var(--pn-space-xl); }}
footer.site .footer-inner{{ max-width:1040px; margin:0 auto; }}
footer.site .footer-top{{ display:flex; flex-direction:column; align-items:center; text-align:center; margin-bottom:64px; }}
footer.site .footer-mark{{ display:flex; align-items:center; justify-content:center; gap:14px; }}
footer.site .footer-mark img{{ display:block; width:40px; height:40px; }}
footer.site .footer-word{{ font-family:'Fraunces',serif; font-weight:600; font-size:21px; color:var(--brand-ivory); }}
footer.site .footer-cols{{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:40px 32px; text-align:left; }}
footer.site .footer-col h2{{ font-family:'Work Sans',sans-serif; font-size:11px; font-weight:500; letter-spacing:.14em;
  text-transform:uppercase; color:var(--brand-sage); margin:0 0 20px; }}
footer.site .footer-col ul{{ list-style:none; margin:0; padding:0; }}
footer.site .footer-col li{{ margin-bottom:13px; }}
footer.site .footer-col a{{ color:#B7AF9C; text-decoration:none; font-size:14px; }}
footer.site .footer-col a:hover{{ color:var(--brand-ivory); }}
footer.site .footer-col p{{ font-size:14px; color:#B7AF9C; line-height:1.7; }}
footer.site .footer-base{{ margin-top:64px; text-align:center; font-size:11.5px; letter-spacing:.04em; color:#A39D8E; }}
@media(max-width:820px){{ footer.site .footer-cols{{ grid-template-columns:repeat(2, minmax(0,1fr)); text-align:center; gap:40px 24px; }} }}
@media(max-width:520px){{ footer.site .footer-cols{{ grid-template-columns:1fr; gap:36px; }} }}
</style>
</head>
<body>

<a href="index.html" class="brand-mark" id="brandMark" aria-label="PlotNua — Home">
  <img src="assets/brand/plotnua-mark-master.svg" alt="" width="34" height="34">
</a>
{RAIL}

<div class="wrap">

<header class="masthead">
  <div class="masthead-row">
    <div class="brand">PlotNua</div>
    <div class="eyebrow" style="margin:0">Garden Room · Garden office</div>
  </div>
  <h1>TRIQ&nbsp;CUBE by TRIQBRIQ&nbsp;AG</h1>
  <p class="standfirst">A 9&nbsp;m² garden office from TRIQBRIQ AG in Stuttgart, built from solid timber rather than panels. Below is what TRIQBRIQ publishes about it, and what PlotNua hasn't yet been able to establish for a buyer in Ireland.</p>
</header>

<section style="padding-top:0">
{IMG}
</section>

<section>
  <div class="stage-no">From the manufacturer</div>
  <h2>Factual product information</h2>
  <p>PlotNua publishes what the manufacturer publishes, attributed to the manufacturer. Everything below is taken from the official TRIQ&nbsp;Office&nbsp;3×3 product page. PlotNua adds no interpretation, no rating and no opinion on the product.</p>

{PRICE_SPEC_PUB}

{EQUIP_PUB}

{OPEN_PUB}
</section>

<section>
  <div class="handoff">
    <div class="eyebrow" style="color:rgba(245,242,232,.62)">Questions and purchase</div>
    <h2>Continue with TRIQBRIQ</h2>
    <p><strong>TRIQBRIQ handles all product-specific and technical consultation, the transaction and fulfilment</strong>, and purchases complete on the official TRIQ product page. If you have a question about the TRIQ&nbsp;CUBE, TRIQBRIQ is the right place to ask it.</p>
    <p>PlotNua does not advise on the TRIQ&nbsp;CUBE, does not quote for it, and does not take payment.</p>

    <a class="handoff-btn" href="{PRODUCT_URL}" target="_blank" rel="noopener" data-outbound="triqbriq" data-loc="handoff">Continue to TRIQBRIQ →</a>
    <span class="handoff-note">Opens TRIQBRIQ's product page on triqbriq.de in a new tab.</span>
  </div>
</section>

<section>
  <p class="next-link">Weighing up a garden room more generally? <a href="discovery-living-in-the-garden.html">Explore Living in the Garden →</a></p>
</section>

<footer class="page-notes">
  <p><strong>Imagery.</strong> The two photographs above are official TRIQBRIQ website imagery, reproduced with TRIQBRIQ AG's written permission and credited “© TRIQBRIQ AG” as required. Sources: <a href="https://triqbriq.de/wp-content/uploads/2025/12/Exterior-3x3-1-scaled.jpg" data-outbound="triqbriq" data-loc="image_source">Exterior-3x3-1</a> and <a href="https://triqbriq.de/wp-content/uploads/2025/12/Interior-3x3-1-scaled.jpg" data-outbound="triqbriq" data-loc="image_source">Interior-3x3-1</a>, both published on the official product page <a href="{PRODUCT_URL}" data-outbound="triqbriq" data-loc="source_note">triqbriq.de/produkt/triq-gartenoffice-3x3</a>. Images are served from TRIQBRIQ's own website and are unmodified.</p>
  <p><strong>Product information.</strong> Every figure and specification on this page is taken from that same official product page, read on 22 September 2026 and checked again on 12 October 2026. PlotNua has added nothing to it.</p>
  <p><strong>Independence.</strong> PlotNua is an independent platform operated by Colin MacAulay. TRIQBRIQ is not a PlotNua partner, and PlotNua does not describe it as approved, recommended or preferred.</p>
</footer>

</div>

{FOOTER.replace("<footer>", '<footer class="site">', 1)}

<script>
/* {MARK} · outbound measurement. One GA4 event per click on a triqbriq.de
   link, with no personal data: which supplier, which product, which link on
   the page, and where it went. Runs only through the site's existing gtag,
   which Cookiebot holds back until the visitor consents to statistics. */
(function () {{
  document.querySelectorAll('a[data-outbound="triqbriq"]').forEach(function (a) {{
    a.addEventListener('click', function () {{
      if (typeof window.gtag !== 'function') return;
      window.gtag('event', 'supplier_outbound_click', {{
        supplier_id: 'triqbriq',
        product_id: 'triq-cube',
        link_location: a.getAttribute('data-loc'),
        link_url: a.href,
        link_domain: 'triqbriq.de',
        outbound: true
      }});
    }});
  }});
}})();
</script>
</body>
</html>
'''

# ── gates ────────────────────────────────────────────────────────────────────
for lab, blk in (("IMG", IMG), ("PRICE+SPEC", PRICE_SPEC_PUB), ("EQUIP", EQUIP_PUB), ("OPEN", OPEN_PUB)):
    if page.count(blk) != 1: die(f"GATE {lab}: approved block not present exactly once")
if "noindex" in page: die("GATE: noindex left on the public page")
for gone in ("Made in Germany", "Country of manufacture"):
    if gone in page: die("GATE: unverified manufacture claim present: " + gone)
if "TRIQBRIQ AG, Stuttgart" not in page: die("GATE: manufacturer location missing")
if "Private preview" in page or 'onclick="return false' in page: die("GATE: preview-only control left on the page")
if page.count(f'href="{PRODUCT_URL}"') != 2: die("GATE: product URL must appear twice (CTA + source note)")
if "noreferrer" in page: die("GATE: noreferrer would hide plotnua.ie from TRIQBRIQ's analytics")
if page.count("© TRIQBRIQ AG") < 3: die("GATE: credit")
for banned in ("partner of", "recommended by PlotNua", "approved by PlotNua", "preferred supplier", "available in Ireland", "delivers to Ireland"):
    if banned.lower() in page.lower(): die("GATE: overclaim phrase present: " + banned)
if page.count("supplier_outbound_click") != 1: die("GATE: exactly one event definition")
if len(re.findall(r'<a [^>]*data-outbound="triqbriq"', page)) != 4: die("GATE: four tagged triqbriq.de links expected")
if page.count('G-PKKJ0RK6N8') != 2: die("GATE: GA4 tag must be the site's existing one, once")

mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
print("preview sha256", sha)
if mode == "--apply":
    OUT.write_text(page, encoding="utf-8"); print("APPLIED ->", OUT.name, len(page), "bytes")
else:
    print("CHECK OK", len(page), "bytes")
