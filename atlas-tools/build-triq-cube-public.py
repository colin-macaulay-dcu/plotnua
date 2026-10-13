#!/usr/bin/env python3
"""
TRIQ QUBE · PUBLIC PAGE — BOUNDED BUILDER (12 October 2026)

PRODUCT NAME CORRECTION, 13 October 2026. TRIQBRIQ AG (Christian Klerner)
confirmed the product is "TRIQ QUBE", not "TRIQ CUBE". The visible name and
metadata use TRIQ QUBE. The frozen preview, which still says CUBE, is NOT
edited: its approved blocks are lifted verbatim and the product name is then
corrected as one explicit, gated step (NAME_FIX below), exactly as this
builder already rewords one heading and drops the "Made in Germany" claim.
DELIVERY EVIDENCE (13 October 2026, TRIQBRIQ AG in writing): international
delivery in principle, Irish delivery subject to individual confirmation; the
founder-approved wording replaces two "not established" panel items (DELIVERY
below, with its own gate).
Identifiers are deliberately kept: the URL triq-cube.html (existing links),
the page marker, and the GA4 product_id 'triq-cube' (so the first-month
outbound report to TRIQBRIQ is one continuous series).

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

# PRODUCT NAME CORRECTION (13 Oct 2026, manufacturer-confirmed): TRIQ QUBE.
# Applied to visible text only; identifiers (URL, marker, GA4 product_id) keep
# "triq-cube". Each lifted block is corrected before it is placed.
NAME_FIX = (("TRIQ&nbsp;CUBE", "TRIQ&nbsp;QUBE"), ("TRIQ CUBE", "TRIQ QUBE"))
def name_fix(s):
    for a, b in NAME_FIX:
        s = s.replace(a, b)
    return s
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

IMG, PRICE_SPEC_PUB, EQUIP_PUB, OPEN_PUB = (name_fix(IMG), name_fix(PRICE_SPEC_PUB),
                                           name_fix(EQUIP_PUB), name_fix(OPEN_PUB))

# DELIVERY EVIDENCE, 13 October 2026. Christian Klerner (TRIQBRIQ AG), in
# writing: "In principle, our building kit is available for delivery
# worldwide. We would be happy to review specific delivery addresses
# individually with each prospective customer upon enquiry." The two panel
# items that said Irish supply/delivery was not established are replaced by
# the FOUNDER-APPROVED wording below, word for word. Still NOT claimed: Irish
# delivery as guaranteed, any shipping price or time, Irish installation, or
# the German price as an Irish delivered price ("No Irish price" and
# "Installation" items stay unchanged).
DELIVERY_OLD = (
    "      <li><strong>Irish availability is not yet confirmed.</strong> PlotNua holds no confirmation that the TRIQ&nbsp;QUBE can be supplied to the Republic of Ireland.</li>\n"
    "      <li><strong>Delivery to Ireland is not established.</strong> Atlas records where a building is made, not who will deliver and install it here. Those are different facts and PlotNua will not treat one as the other.</li>\n")
DELIVERY_TEXT = ("International delivery is available in principle. Delivery to Ireland is subject to "
                 "individual confirmation by TRIQBRIQ AG based on the customer's delivery address. "
                 "Contact the manufacturer to confirm delivery arrangements and obtain a quotation.")
DELIVERY_NEW = "      <li><strong>Delivery to Ireland.</strong> " + DELIVERY_TEXT.replace("'", "&rsquo;") + "</li>\n"
if OPEN_PUB.count(DELIVERY_OLD) != 1: die("DELIVERY: the two superseded panel items were not found exactly once")
OPEN_PUB = OPEN_PUB.replace(DELIVERY_OLD, DELIVERY_NEW)

# CONSTRUCTION STORY, 13 October 2026 (founder decision: "Built differently").
# Facts are TRIQBRIQ's own, from triqbriq.de/triq/ (TRIQ QUBE page) and
# triqbriq.de/en/triqbriq-system/ (read 13 Oct 2026), each attributed on the
# page. Imagery: five further official triqbriq.de images, hot-linked and
# unmodified, each credited "© TRIQBRIQ AG", within the written grant of
# 22 September 2026 (images from triqbriq.de, used in featuring TRIQBRIQ).
# An image whose file name credits an outside photographer was deliberately
# NOT used (rights unclear).
BUILT_CSS = """/* ── BUILT DIFFERENTLY · construction story (13 Oct 2026) ───────── */
.built-lede{ font-size:var(--pn-w-body-lg); max-width:62ch; }
.built-keys{ display:flex; flex-wrap:wrap; gap:8px; margin:var(--pn-space-md) 0 0; padding:0; }
.built-keys li{ list-style:none; font-size:var(--pn-w-caption); letter-spacing:.04em; padding:6px 12px;
  border:1px solid var(--pn-wild); border-radius:2px; color:var(--pn-wild); }
.build-flow{ list-style:none; margin:var(--pn-space-xl) 0 0; padding:0; }
.build-step{ display:grid; grid-template-columns:minmax(0,7fr) minmax(0,5fr); gap:var(--pn-space-xl);
  align-items:center; padding:var(--pn-space-xl) 0; border-top:1px solid var(--pn-hair); }
.build-step:nth-child(even) .build-media{ order:2; }
.build-pair{ display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,1fr); gap:14px; align-items:end; }
.build-step--tall .build-media figure{ max-width:360px; margin:0 auto; }
.build-step--final{ grid-template-columns:minmax(0,1fr); gap:var(--pn-space-lg); }
.build-step--final.build-step .build-media{ order:0; }
.build-step--final .build-text{ display:grid; grid-template-columns:minmax(0,5fr) minmax(0,7fr); gap:var(--pn-space-xl); align-items:start; }
.build-label{ display:flex; align-items:baseline; gap:12px; font-size:var(--pn-w-meta); font-weight:600;
  letter-spacing:.18em; text-transform:uppercase; color:var(--pn-stone); margin:0 0 14px; }
.build-no{ font-family:'Fraunces',Georgia,serif; font-weight:300; font-size:44px; line-height:.8;
  letter-spacing:0; color:var(--pn-wild); }
.build-text h3{ font-size:var(--pn-s-statement); line-height:1.18; margin:0 0 12px; }
.build-text p{ font-size:var(--pn-w-body-lg); }
.built-source{ font-size:var(--pn-w-body-sm); color:var(--pn-stone); border-top:1px solid var(--pn-hair);
  padding-top:var(--pn-space-sm); max-width:none; }
@media (max-width:820px){
  .build-step, .build-step--final .build-text{ grid-template-columns:minmax(0,1fr); gap:var(--pn-space-md); }
  .build-step{ padding:var(--pn-space-lg) 0; }
  .build-step:nth-child(even) .build-media{ order:0; }
  .build-step--tall .build-media figure{ max-width:300px; }
  .build-no{ font-size:36px; }
}
"""
BUILT = """<section class="built" aria-labelledby="built-title">
  <div class="stage-no">Built differently</div>
  <h2 id="built-title">A garden office built from solid-wood blocks</h2>
  <p class="built-lede">The TRIQ&nbsp;QUBE isn&rsquo;t a timber frame clad in panels. Its walls are stacked from solid-wood building blocks that TRIQBRIQ calls BRIQs. Here is how they come together, as TRIQBRIQ describes it.</p>
  <ul class="built-keys" aria-label="The construction system at a glance">
    <li>Solid softwood blocks</li><li>Beechwood dowels</li><li>No glue, no mortar, no screws</li><li>Can be taken apart and reused</li>
  </ul>

  <ol class="build-flow">
    <li class="build-step">
      <div class="build-media build-pair">
        <figure>
          <img src="https://triqbriq.de/wp-content/uploads/2024/01/briq-25-50-1.png" width="1361" height="907" loading="lazy" decoding="async"
               alt="A single TRIQBRIQ BRIQ seen from the side: solid softwood pieces with two pegged studs on top and dowel holes through it">
          <figcaption><span>A single BRIQ</span><span class="credit">© TRIQBRIQ AG</span></figcaption>
        </figure>
        <figure>
          <img src="https://triqbriq.de/wp-content/uploads/2023/02/IMG_7644-scaled-e1676563466189.jpg" width="1141" height="1141" loading="lazy" decoding="async"
               alt="TRIQBRIQ BRIQs stacked on wooden pallets, ready for delivery">
          <figcaption><span>BRIQs stacked on pallets</span><span class="credit">© TRIQBRIQ AG</span></figcaption>
        </figure>
      </div>
      <div class="build-text">
        <div class="build-label"><span class="build-no">01</span> The building blocks</div>
        <h3>Solid wood, cut to fit</h3>
        <p>Each BRIQ is a block of solid softwood. TRIQBRIQ makes them partly from timber that would otherwise mostly be burned for energy, such as storm-damaged wood and surplus construction timber, on a robot-assisted line that cuts every block to a precise fit. The BRIQs leave the factory stacked on pallets.</p>
      </div>
    </li>

    <li class="build-step">
      <div class="build-media">
        <figure>
          <img src="https://triqbriq.de/wp-content/uploads/2024/03/Verriegelung-Holzbausteine-1.jpg" width="1920" height="1080" loading="lazy" decoding="async"
               alt="Close-up of two BRIQs being joined: a stud fits into the block above and a round beechwood dowel locks them together">
          <figcaption><span>A beechwood dowel locking two BRIQs together</span><span class="credit">© TRIQBRIQ AG</span></figcaption>
        </figure>
      </div>
      <div class="build-text">
        <div class="build-label"><span class="build-no">02</span> How they connect</div>
        <h3>Wood locked into wood</h3>
        <p>The BRIQs fit together through studs and blind holes, and beechwood dowels lock them in place. There is no glue, no mortar and no screws: every connection is wood in wood.</p>
      </div>
    </li>

    <li class="build-step build-step--tall">
      <div class="build-media">
        <figure>
          <img src="https://triqbriq.de/wp-content/uploads/2019/11/Proof-of-concept-anbau-53.jpg" width="1365" height="2048" loading="lazy" decoding="async"
               alt="A building crew laying BRIQs course by course to raise solid-timber walls on a TRIQBRIQ construction site">
          <figcaption><span>BRIQ walls going up on TRIQBRIQ&rsquo;s Frankfurt pilot project</span><span class="credit">© TRIQBRIQ AG</span></figcaption>
        </figure>
      </div>
      <div class="build-text">
        <div class="build-label"><span class="build-no">03</span> How the structure comes together</div>
        <h3>Laid like bricks, with no drying time</h3>
        <p>The BRIQs are laid course by course, like bricks, into a solid-timber wall, and there is nothing to dry or cure. TRIQBRIQ says a TRIQ&nbsp;QUBE arrives as a kit and can stand within a single day. Who would assemble it in Ireland is not yet established; see below.</p>
        <p>Because nothing is glued, TRIQBRIQ says a structure built this way can later be taken apart and its timber reused.</p>
      </div>
    </li>

    <li class="build-step build-step--final">
      <div class="build-media">
        <figure>
          <img src="https://triqbriq.de/wp-content/uploads/2026/08/TRIQ-QUBE_Tiny-House-Park.jpg" width="1264" height="848" loading="lazy" decoding="async"
               alt="A finished TRIQ QUBE with a covered deck and outdoor seating, set among planted gardens">
          <figcaption><span>The finished TRIQ&nbsp;QUBE</span><span class="credit">© TRIQBRIQ AG</span></figcaption>
        </figure>
      </div>
      <div class="build-text">
        <div class="build-head">
          <div class="build-label"><span class="build-no">04</span> The finished TRIQ&nbsp;QUBE</div>
          <h3>The blocks are the building</h3>
        </div>
        <p>The result is a 9&nbsp;m² garden office whose solid-timber walls are its structure. TRIQBRIQ says the solid wood helps regulate indoor temperature and humidity. Its published price, specification and what PlotNua hasn&rsquo;t established for Ireland follow below.</p>
      </div>
    </li>
  </ol>
  <p class="built-source">Source: TRIQBRIQ&rsquo;s own TRIQ&nbsp;QUBE and TRIQBRIQ-System pages on triqbriq.de, read 13 October 2026. PlotNua reports what TRIQBRIQ says and has not tested these claims.</p>
</section>
"""
BUILT_IMAGES = (
    "https://triqbriq.de/wp-content/uploads/2024/01/briq-25-50-1.png",
    "https://triqbriq.de/wp-content/uploads/2023/02/IMG_7644-scaled-e1676563466189.jpg",
    "https://triqbriq.de/wp-content/uploads/2024/03/Verriegelung-Holzbausteine-1.jpg",
    "https://triqbriq.de/wp-content/uploads/2019/11/Proof-of-concept-anbau-53.jpg",
    "https://triqbriq.de/wp-content/uploads/2026/08/TRIQ-QUBE_Tiny-House-Park.jpg",
)

TITLE = "TRIQ QUBE garden office by TRIQBRIQ AG | PlotNua"
DESC = ("The TRIQ QUBE (TRIQ Office 3×3): a 9 m² solid-timber garden office from TRIQBRIQ AG, "
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
{BUILT_CSS}</style>
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
  <h1>TRIQ&nbsp;QUBE by TRIQBRIQ&nbsp;AG</h1>
  <p class="standfirst">A 9&nbsp;m² garden office from TRIQBRIQ AG in Stuttgart, built from solid timber rather than panels. Below is what TRIQBRIQ publishes about it, and what PlotNua hasn't yet been able to establish for a buyer in Ireland.</p>
</header>

<section style="padding-top:0">
{IMG}
</section>

{BUILT}

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
    <p><strong>TRIQBRIQ handles all product-specific and technical consultation, the transaction and fulfilment</strong>, and purchases complete on the official TRIQ product page. If you have a question about the TRIQ&nbsp;QUBE, TRIQBRIQ is the right place to ask it.</p>
    <p>PlotNua does not advise on the TRIQ&nbsp;QUBE, does not quote for it, and does not take payment.</p>

    <a class="handoff-btn" href="{PRODUCT_URL}" target="_blank" rel="noopener" data-outbound="triqbriq" data-loc="handoff">Continue to TRIQBRIQ →</a>
    <span class="handoff-note">Opens TRIQBRIQ's product page on triqbriq.de in a new tab.</span>
  </div>
</section>

<section>
  <p class="next-link">Weighing up a garden room more generally? <a href="discovery-living-in-the-garden.html">Explore Living in the Garden →</a></p>
</section>

<footer class="page-notes">
  <p><strong>Imagery.</strong> The photographs on this page are official TRIQBRIQ website imagery, reproduced with TRIQBRIQ AG's written permission and credited “© TRIQBRIQ AG” as required. Sources: <a href="https://triqbriq.de/wp-content/uploads/2025/12/Exterior-3x3-1-scaled.jpg" data-outbound="triqbriq" data-loc="image_source">Exterior-3x3-1</a> and <a href="https://triqbriq.de/wp-content/uploads/2025/12/Interior-3x3-1-scaled.jpg" data-outbound="triqbriq" data-loc="image_source">Interior-3x3-1</a>, both published on the official product page <a href="{PRODUCT_URL}" data-outbound="triqbriq" data-loc="source_note">triqbriq.de/produkt/triq-gartenoffice-3x3</a>; the five construction photographs are published on TRIQBRIQ&rsquo;s TRIQ&nbsp;QUBE, TRIQBRIQ-System, Massivholzhaus and Produktion pages on triqbriq.de. Images are served from TRIQBRIQ's own website and are unmodified.</p>
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
# NAME gate (13 Oct 2026): the superseded product name must not appear anywhere
# a visitor or a search engine can read it (comments and scripts excluded, so
# the marker and the GA4 product_id identifier may keep "triq-cube").
visible = re.sub(r"<!--.*?-->|<script.*?</script>", "", page, flags=re.S)
if re.search(r"TRIQ(\s|&nbsp;|\u00a0)*CUBE", visible, re.I): die("GATE NAME: 'TRIQ CUBE' still visible")
if "<h1>TRIQ&nbsp;QUBE by TRIQBRIQ&nbsp;AG</h1>" not in page: die("GATE NAME: heading must name the TRIQ QUBE")
if "product_id: 'triq-cube'" not in page: die("GATE NAME: GA4 product_id identifier must be kept for report continuity")
# DELIVERY gate (13 Oct 2026): the approved wording once, the superseded claims
# gone, and nothing that promises Irish delivery, a shipping price or time, or
# installation.
# BUILT gates (13 Oct 2026): the story sits between the opening photographs and
# the factual product information; every construction image is an official
# triqbriq.de image from the approved list and carries the credit.
if page.count(BUILT) != 1: die("GATE BUILT: construction story must appear exactly once")
i_img = page.index('Interior-3x3-1-scaled.jpg'); i_b = page.index('id="built-title"'); i_f = page.index('<h2>Factual product information</h2>')
if not (i_img < i_b < i_f): die("GATE BUILT: story must sit after the opening photographs and before the product information")
b_imgs = re.findall(r'<img src="([^"]+)"', BUILT)
if tuple(b_imgs) != BUILT_IMAGES: die("GATE BUILT: construction images differ from the approved list")
if BUILT.count('<span class="credit">\u00a9 TRIQBRIQ AG</span>') != len(b_imgs): die("GATE BUILT: every construction image needs the \u00a9 TRIQBRIQ AG credit")
if re.search(r"Schwier|data-outbound|<a ", BUILT): die("GATE BUILT: no unclear-rights image and no links inside the story")
if re.search(r"TRIQ(\s|&nbsp;)*CUBE", BUILT, re.I): die("GATE BUILT: product name must be TRIQ QUBE")
if page.count(DELIVERY_NEW) != 1: die("GATE DELIVERY: approved delivery wording must appear exactly once")
for gone in ("holds no confirmation that the TRIQ", "Delivery to Ireland is not established"):
    if gone in page: die("GATE DELIVERY: superseded wording still present: " + gone)
for bad in ("guaranteed", "free delivery", "free shipping", "delivery included", "installation included",
            "installed in Ireland", "Irish delivered price is", "ships to Ireland", "delivers to Ireland"):
    if bad.lower() in page.lower(): die("GATE DELIVERY: overclaim present: " + bad)
li = DELIVERY_NEW
if re.search(r"€|EUR|\d+\s*(day|week|month)", li, re.I): die("GATE DELIVERY: no shipping price or delivery time may be stated")
if "PlotNua does not restate it as an Irish delivered price" not in page: die("GATE DELIVERY: German-price caveat must stay")
for keep in ("<strong>No Irish price.</strong>", "<strong>Installation.</strong>"):
    if keep not in page: die("GATE DELIVERY: must keep the item " + keep)

mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
print("preview sha256", sha)
if mode == "--apply":
    OUT.write_text(page, encoding="utf-8"); print("APPLIED ->", OUT.name, len(page), "bytes")
else:
    print("CHECK OK", len(page), "bytes")
