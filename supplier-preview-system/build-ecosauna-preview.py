#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE ECOSAUNA PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
VARIANT:  B, provider-led. Reused, not forked: the same certified system that
built the Sauna Experts, Irish Sauna Company and BIOBUILDS previews. The only
addition is a five-product range section, on the BIOBUILDS pattern, because
EcoSauna publish five product types and the supplier asked to see how
EcoSauna "would be featured".

*** THE RECONCILIATION, DONE BEFORE ANYTHING WAS WRITTEN (18 Oct 2026). ***

Atlas already holds EcoSauna: ORG-000218 "EcoSauna Ireland", rec7or5nAX2Z57tiN,
website https://www.ecosauna.ie/, from the 2 October 2026 home-wellness
outreach intake. That outreach went to info@ecosauna.ie and BOUNCED. The
record is reused; no second identity is created.

The reply that started this preview came on 18 October 2026 from
ecosauna2022hottub@gmail.com ("EcoSauna Team"), Gmail thread
1a14e93ff0d46b6b: "we'd be happy to take a look at a private preview".
That is a request to SEE the page. It is not a grant of imagery, publication,
partnership, commission or advertising, and the page says none of those.

THE SENDER'S LINK TO ecosauna.ie IS AWAITING SUPPLIER CONFIRMATION. The
gmail address does not appear on ecosauna.ie, whose published contacts are
info@ecosauna.ie (bounced) and 087 204 5337. A separate Estonian manufacturer,
Ecosauna Project OÜ (ecosauna.ee), also exists. The preview is about the
business at www.ecosauna.ie, because that is where every fact comes from; the
identity question goes to the founder, not onto the page.

No repository file mentioned EcoSauna before this build (full-tree search on
origin/main 6d3ad0a), and image-rights-records.json holds no row for them.

*** FIRST-PARTY EVIDENCE, read 18 October 2026. ***

www.ecosauna.ie is a client-rendered app. Every figure below was read from
the code the live site serves (/assets/index-Cy6LUy6E.js, 721,030 bytes,
fetched 18 Oct 2026): the product catalogue its configurator renders as
"Starting from €…", the option price table it adds on top, and its own
delivery, base-preparation and price-notice text. Evidence is kept outside
the repo with the release folder.

*** THE TRAPS IN THIS SUPPLIER. ***

1 · TWO SETS OF STARTING PRICES. The configurator shows the Barrel Sauna
    from €3,300, the Hot Tub from €2,300 and the Plunge Pool from €1,100.
    The same site's Ireland pages say "starting at €2,800", "starting at
    €3,100" and "starting from €1,950". Both are first-party and they
    disagree. The page shows the configurator's figures, labelled as such,
    and ASKS which is right rather than choosing silently.

2 · VAT IS NOT STATED anywhere on the site. Prices carry no VAT basis on the
    page beyond "as shown in the configurator", and the question is asked.

3 · THE SITE CARRIES CUSTOMER QUOTES, A PLANNING-EXEMPTION STATEMENT, HEALTH
    CLAIMS AND A "15 INSTALLATIONS IN <COUNTY>" TEMPLATE LINE. None is
    verified and none may appear here. G8 refuses them.

4 · ORIGIN IS NOT ESTABLISHED. The site calls itself a "manufacturer and
    supplier" in Ireland but does not say where the units are built, and a
    separate Estonian Ecosauna exists. G8 refuses any origin claim.

5 · NATIONWIDE DELIVERY IS THEIR CLAIM. "All 32 counties" is published by
    EcoSauna and not verified by PlotNua, so G8b requires it to be
    attributed in their name rather than stated as ours.

*** IMAGERY STATE C. NO IMAGERY. ***

The reply was a request to see the page. UNKNOWN IS NOT GRANTED. Atlas
Image Permission Outreach WELLNESS-FIRST-ECOSAUNA-20261002 reads "Unknown —
Awaiting Reply". The site's product images are served from mapleapplehost.com
and ecosauna.ie and none may be downloaded, re-hosted, hotlinked or shown.
G0 refuses a filled image list; G9 proves absence on the OUTPUT.

Run: python3 build-ecosauna-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/ecosauna-preview.html")
       if STAGE else SITE / "ecosauna-preview.html")

SUPPLIER = "EcoSauna"
EVIDENCE_DATE = "18 October 2026"
SUPPLIER_SITE = "https://www.ecosauna.ie/"
PRODUCTS_URL = SUPPLIER_SITE + "?view=PRODUCTS"
WIZARD_URL = SUPPLIER_SITE + "?view=WIZARD"
DISCOVERY_URL = "https://plotnua.ie/discovery-garden-retreat.html"
CREDIT = "© EcoSauna"
TBC_TEXT = "To be confirmed by EcoSauna"

# IMAGERY STATE C. Empty by governance, not by oversight. G0 enforces it.
ECO_IMAGES = []

# ── THE RANGE ──────────────────────────────────────────────────────────────
# The five product types EcoSauna's configurator offers, in the site's own
# order. "from" is the configurator's own "Starting from" figure for the
# product's first (standard) configuration. "install" is the configurator's
# installation option price range; None means the configurator lists no
# installation option for that product, and the page says so plainly.
RANGE = [
    {"name": "Barrel Sauna",
     "spec": "Six sizes, from 2m &times; 1.6m (4 people) to 2m &times; 3.5m "
             "(8+ people). Spruce or Thermowood; firewood or electric stove.",
     "from": "&euro;3,300", "install": "&euro;600&ndash;&euro;800 by size"},
    {"name": "Cube Sauna",
     "spec": "Seven sizes, from 1.4m &times; 1.6m &times; 2m high (electric "
             "stove) to 2m &times; 3.5m. Spruce or Thermowood; glass wall, "
             "porch and changing room among the extras.",
     "from": "&euro;3,200", "install": "&euro;650&ndash;&euro;850 by size"},
    {"name": "Hot Tub",
     "spec": "Five sizes, from 1m &times; 2m for two people to 2.25m "
             "diameter for 8+, with an inside or outside stove. Insulated "
             "cover and air jets among the extras.",
     "from": "&euro;2,300", "install": None},
    {"name": "Plunge Pool",
     "spec": "1.05m diameter &times; 1.10m high. Listed with a lid, stair, "
             "drainage system, timber outside and fibreglass inside.",
     "from": "&euro;1,100", "install": None},
    {"name": "Phytosauna",
     "spec": "Herbal steam cabin, 130cm &times; 78cm &times; 78cm, 65kg, in "
             "knot-free Thermo Aspen. Listed with a 3-level seat, armrest, "
             "footrest, steam supply and drain.",
     "from": "&euro;2,100", "install": None},
]

# THE EVIDENCE RECORD the range is checked against. Five product types in the
# configurator, and exactly three of them with no installation option listed.
# G11 compares RANGE with these, so a renamed product or an invented value
# is refused rather than silently rendered.
EXPECTED_PRODUCTS = ("Barrel Sauna", "Cube Sauna", "Hot Tub", "Plunge Pool",
                     "Phytosauna")
EXPECTED_NO_INSTALL_OPTION = ("Hot Tub", "Plunge Pool", "Phytosauna")

RANGE_CSS = """<style>
/* THE RANGE -- EcoSauna, 18 Oct 2026. Tokens only; stacks below 640px.
   Same range pattern as the other provider-led previews. */
.pn-range{ margin-top:var(--pn-md); border-top:1px solid var(--pn-hair); }
.pn-range-row{ display:grid; grid-template-columns:1.1fr 2.6fr .8fr 1.1fr;
  gap:6px var(--pn-md); padding:14px 0; border-bottom:1px solid var(--pn-hair);
  align-items:baseline; }
.pn-range-head{ font-size:var(--pn-w-caption); letter-spacing:.12em;
  text-transform:uppercase; color:var(--pn-body); padding:10px 0; }
.pn-range-row b{ color:var(--pn-voice); font-weight:600; }
.pn-range-tbc{ color:var(--pn-body); font-style:italic; }
.wrap section > p a, .pn-range-note a{ color:var(--pn-voice);
  text-underline-offset:2px; }
.pn-range-note{ font-size:var(--pn-w-body-sm); color:var(--pn-body);
  margin-top:var(--pn-md); max-width:70ch; }
@media (max-width:640px){
  .pn-range-head{ display:none; }
  .pn-range-row{ grid-template-columns:1fr 1fr; }
  .pn-range-row > :first-child{ grid-column:1 / -1; }
  .pn-range-row [data-k]::before{ content:attr(data-k); display:block;
    font-size:var(--pn-w-meta); letter-spacing:.12em; text-transform:uppercase;
    color:var(--pn-body); }
  .pn-range-row [data-k="Published specification"]{ grid-column:1 / -1; }
}
</style>
"""


def cell(v, label):
    if v is None:
        return '<span data-k="%s" class="pn-range-tbc">%s</span>' % (label, TBC_TEXT)
    return '<span data-k="%s">%s</span>' % (label, v)


def range_block():
    rows = ['    <div class="pn-range-row pn-range-head" aria-hidden="true">'
            '<span>Product</span><span>Published specification</span>'
            '<span>Starts at</span><span>Installation option</span></div>']
    for m in RANGE:
        rows.append('    <div class="pn-range-row" role="listitem"><b>%s</b>%s%s%s</div>'
                    % (m["name"], cell(m["spec"], "Published specification"),
                       cell(m["from"], "Starts at"),
                       cell(m["install"], "Installation option")))
    return ("<!-- THE RANGE -- the five EcoSauna product types, for the\n"
            "     supplier to confirm. Built from RANGE in\n"
            "     build-ecosauna-preview.py; read %s. -->\n"
            "<section>\n"
            "  <h2>The five EcoSauna products</h2>\n"
            "  <p>This is how we&rsquo;d set out your range, using the sizes "
            "and starting prices in <a href=\"%s\" rel=\"noopener\">your online "
            "configurator</a>. Please check each line.</p>\n"
            "  <div class=\"pn-range\" role=\"list\">\n%s\n  </div>\n"
            "  <p class=\"pn-range-note\">Starting prices are the figures your "
            "configurator shows for each product&rsquo;s standard "
            "configuration. Sizes, timber, extras and installation are priced "
            "on top. Your configurator says the total is an estimate, and that "
            "the final price and the delivery charge, which depends on "
            "location, are confirmed when you&rsquo;re contacted.</p>\n"
            "</section>\n"
            % (EVIDENCE_DATE, WIZARD_URL, "\n".join(rows)))


# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT, OR THAT ARE MARKETING ────────────
BANNED_CLAIM_PHRASES = [
    # SUPERLATIVE AND RANKING. Their site uses "premier" and "leading".
    "premier", "the leading", "leading provider", "number one", "best price",
    "cheapest", "top-tier", "pinnacle", "luxury",
    # ORIGIN. Not established; a separate Estonian Ecosauna exists.
    "manufactured in ireland", "made in ireland", "irish made", "irish-made",
    "irish built", "irish-built", "handcrafted in", "we manufacture",
    "built in ireland", "estonia",
    # COMMERCIAL TERMS NOT PUBLISHED AS TERMS.
    "warranty of", "year warranty", "comprehensive warranty",
    "guaranteed for", "we guarantee", "lead time of", "free delivery",
    "delivery included", "inc. vat", "including vat", "incl. vat",
    "ex vat", "excluding vat",
    # PLANNING. Their site says garden saunas are generally exempt. A PlotNua
    # page never says that; only the local authority can.
    "planning exempt", "exempted development", "no planning permission",
    "does not need planning", "don't need planning",
    # HEALTH. Their pages make wellness claims; a PlotNua page does not.
    "inflammation", "immune", "cures", "treats", "detox", "healing",
    "cardiovascular", "respiratory",
    # TESTIMONIALS AND TEMPLATED TRACK RECORD.
    "highly recommended", "stellar customer service", "blown away",
    "installations in the", "completed over", "loved by",
    # HEATER BRAND. Published in marketing copy, not in the configurator's
    # stove choices; left off rather than half-stated.
    "harvia",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
OPEN_QUESTIONS = """<!-- THE OPEN QUESTIONS — the three things the supplier's own site leaves
     open, asked as questions and not resolved. Each one names what the site
     does say first. -->
<section>
  <h2>Three things we would ask before publishing</h2>
  <p>These are the three things we&rsquo;d like to check with you before the
     page goes live.</p>
  <div class="pn-open">
    <ul>
      <li><b>Which starting prices.</b> Your configurator starts the Barrel
          Sauna at &euro;3,300, the Hot Tub at &euro;2,300 and the Plunge Pool
          at &euro;1,100. Some of your Ireland pages give different starting
          figures: &euro;2,800 for a barrel sauna, &euro;3,100 for a hot tub
          and &euro;1,950 for a plunge pool. Which should a homeowner see, and
          do your prices include VAT?</li>
      <li><b>Delivery and timing.</b> Your configurator prices delivery by
          location and confirms it on contact, and your county pages say a
          custom order usually arrives within 4 to 6 weeks. Is there a
          typical delivery range we could show, and does that timescale hold
          across the whole range?</li>
      <li><b>Installation and cover.</b> Installation is a priced option on
          the Barrel and Cube Saunas. Is it also offered for the Hot Tub,
          Plunge Pool and Phytosauna? And what would you like a homeowner to
          know about the warranty on each?</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Every figure traces to www.ecosauna.ie, read 18 October 2026.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach EcoSauna",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your own website publishes. They arrive "
                 "through <a href=\"%s\" rel=\"noopener\"><i>Garden "
                 "Retreat</i></a> &mdash; our Discovery on garden saunas, hot "
                 "tubs and cold plunges in Ireland &mdash; work through what "
                 "their garden could take and what to check, and only then "
                 "reach suppliers. By the time this screen appears the "
                 "thinking has already happened." % DISCOVERY_URL,

    "OFFER_NAME": "Barrel Sauna",
    "VERIFIED_PRICE": "From &euro;3,300",
    "VERIFIED_PRICE_BASIS": "From &euro;3,300 is the starting figure "
                            "EcoSauna&rsquo;s online configurator shows for "
                            "the Barrel Sauna, in the 2m &times; 1.6m size "
                            "and spruce. Larger sizes, Thermowood, extras and "
                            "installation are priced on top, and EcoSauna "
                            "say the configured total is an estimate, with "
                            "the final price and delivery confirmed on "
                            "contact. EcoSauna say they deliver to all 32 "
                            "counties.",

    "VERIFIED_FACT_1_LABEL": "Capacity",
    "VERIFIED_FACT_1_VALUE": "4 people in the 2m &times; 1.6m; 8+ in the "
                             "2m &times; 3.5m",
    "VERIFIED_FACT_2_LABEL": "Sizes",
    "VERIFIED_FACT_2_VALUE": "Six, from 2m &times; 1.6m to 2m &times; 3.5m",
    "VERIFIED_FACT_3": "Firewood or electric stove",
    "VERIFIED_FACT_4": "Spruce as standard; Thermowood from +&euro;450",
    "VERIFIED_FACT_5": "Installation option from &euro;600",

    "THINGS_TO_CHECK": "the figure is the starting configuration, not a "
                       "quote, and delivery is priced by location. "
                       "EcoSauna&rsquo;s own guidance is that the base is "
                       "ready before they arrive: a level concrete pad of at "
                       "least 100mm, a heavy-duty timber deck, or compacted "
                       "gravel with paving flags. An electric stove needs a "
                       "certified electrician to run the supply. And a point "
                       "of ours rather than yours: the local authority is the "
                       "only body that can confirm what a particular site "
                       "requires.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY (simplifyLocalityDisplay).
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "Shown for a homeowner in Co. Meath, from the location "
                       "they gave us. We don&rsquo;t ask them about the base, "
                       "the access or where the power runs, so we "
                       "wouldn&rsquo;t pretend to know. Those stay as things "
                       "to check with you.",

    "WHY_1_LABEL": "YOUR CONFIGURATOR, UNDERSTOOD FIRST",
    "WHY_1_TEXT": "A homeowner sees what the starting price is and what adds "
                  "to it &mdash; size, Thermowood, extras, installation "
                  "&mdash; before they open your configurator, so the "
                  "estimate they build is one they expected.",
    "WHY_2_LABEL": "THE BASE BEFORE DELIVERY DAY",
    "WHY_2_TEXT": "Your own base guidance sits next to the price, so the pad "
                  "or deck is something they&rsquo;ve planned for rather "
                  "than something they find out about when the trailer is "
                  "booked.",
    "WHY_3_LABEL": "REACHED THROUGH GARDEN WELLNESS",
    "WHY_3_TEXT": "A homeowner arrives here having decided they want a sauna, "
                  "a hot tub or a cold plunge in their garden, not having "
                  "typed your name into a search box. That is the kind of "
                  "enquiry we are trying to send you.",

    "CLOSING_PROPOSITION": "Does this represent EcoSauna accurately for an "
                           "Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing &mdash; a price, a size, what installation "
                       "covers &mdash; tell us and we&rsquo;ll correct it "
                       "before anything is published.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    if ECO_IMAGES:
        die("EcoSauna imagery was added to this builder, but the reply asked "
            "to see a private preview, which is not a grant. UNKNOWN is not "
            "GRANTED. Get written permission and a manifest row first.")

    # G1 · Strip the template's filling instructions.
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Open on the demonstration.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero:
        die("the introductory hero block was not found. Not guessing.")
    if "{{PROPOSITION}}" not in hero.group(0) or "{{LEDE}}" not in hero.group(0):
        die("the matched hero block does not carry the headline tokens.")
    src = src.replace(hero.group(0), "\n")

    # G2 · Range, open questions, then the frozen journey band, before "why".
    jm = re.search(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                   src, re.S)
    if not jm:
        die("the frozen journey band was not found. Not guessing.")
    journey = jm.group(0)
    src = src.replace(journey, "\n")
    why_anchor = "<!-- WHY THIS COULD BE USEFUL"
    if src.count(why_anchor) != 1:
        die("the 'why' section anchor is not unique. Nothing written.")
    src = src.replace(why_anchor,
                      range_block() + "\n" + OPEN_QUESTIONS + "\n"
                      + journey.strip("\n") + "\n\n" + why_anchor)
    if src.count("</head>") != 1:
        die("the </head> anchor is not unique. Nothing written.")
    src = src.replace("</head>", RANGE_CSS + "</head>")

    # G3 · THE IMAGE POSITION CARRIES EXACTLY THE NEUTRAL LABEL (§10.2).
    PLACEHOLDER = "<b>Your image here</b>"
    slot = re.search(r'<div class="pn-photo-slot"[^>]*>(.*?)</div>',
                     src, flags=re.S)
    if not slot:
        die("the photo slot was not found. The template has moved.")
    if slot.group(1).strip() != PLACEHOLDER:
        die("the image position must carry exactly %r and nothing else."
            % PLACEHOLDER)

    # G3c · ATTRIBUTION AND LINK BACK.
    attribution = (
        '          <p class="credit-line">Every figure on this page is '
        'published by %s and was read from '
        '<a href="%s" rel="noopener">your products</a>, '
        '<a href="%s" rel="noopener">your online configurator</a> and '
        '<a href="%s" rel="noopener">ecosauna.ie</a> on %s. '
        'No %s photography is used anywhere on this page. '
        '%s'
        '</p>\n'
        % (SUPPLIER, PRODUCTS_URL, WIZARD_URL, SUPPLIER_SITE, EVIDENCE_DATE,
           SUPPLIER, CREDIT))
    foot = "<footer>\n"
    if src.count(foot) != 1:
        die("the footer anchor is not unique. Nothing written.")
    src = src.replace(foot, attribution + foot)

    # G3b · THE CLOSING HEADING.
    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once.")
    src = src.replace(old_head, "<h2>Before anything goes live</h2>")

    # G4 · Fill every token; refuse if one is missing or left behind.
    fill = {k: v for k, v in FILL.items() if k not in ("PROPOSITION", "LEDE")}
    for key, value in fill.items():
        needle = "{{%s}}" % key
        if needle not in src:
            die("token %s is not in the template. The template has moved."
                % needle)
        src = src.replace(needle, value)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", src)))
    if leftover:
        die("unfilled tokens remain: " + ", ".join(leftover))

    # G5 · PRIVACY.
    for directive in ("noindex", "nofollow", "noarchive", "nosnippet",
                      "noimageindex"):
        if directive not in src:
            die("the robots directive '%s' is missing." % directive)

    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    low = re.sub(r"\s+", " ", visible).lower()

    # G3d · THE RIGHTS PROCESS IS NOT NARRATED.
    for phrase in ("where they would sit", "where your imagery would go",
                   "where your photography would", "stay yours until",
                   "images stay yours", "imagery waits until",
                   "until you tell us otherwise",
                   "before anything is published, so your"):
        if phrase in low:
            die("the page narrates the image-rights process: %r." % phrase)
    if "<h3" in src:
        die("an h3 appeared; the template has no style for it.")

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Irish Sauna", "OGNYX", "TankTribe", "Tanktribe",
                  "Modulux", "Switch Electrical", "Sigenergy", "Auroom",
                  "Sauna Experts", "Hansa24"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if src.count(journey.strip("\n")) != 1:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM, NO BORROWED MARKETING.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support, or repeats the supplier's marketing as "
                "PlotNua's: %r." % phrase)

    # G8b · NATIONWIDE DELIVERY ATTRIBUTED, NOT ASSERTED.
    if "ecosauna say they deliver to all 32 counties" not in low:
        die("nationwide delivery must be attributed to EcoSauna in their "
            "name; PlotNua has not verified it.")
    if "nationwide" in low:
        die("'nationwide' appears unattributed. Use the attributed 32-county "
            "sentence only.")

    # G8c · THE PLANNING FIREWALL. Their site says garden saunas are
    # generally exempt; this page must carry PlotNua's own position instead.
    if "local authority is the only body that can confirm" not in low:
        die("the planning firewall is missing.")

    # G8d · ESTIMATE STATUS. The configurator calls its total an estimate;
    # the page must not present a starting price as a quote.
    if "estimate" not in low or "not a quote" not in low:
        die("the page does not say the figures are starting estimates.")

    # G9 · NO IMAGERY, PROVEN ON THE OUTPUT.
    for pattern, what in (
            (r'<img[^>]+src="https?://', "an external <img>"),
            (r'<source[^>]+srcset="https?://', "an external <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s." % what)
    if "mapleapplehost" in src.lower() or "wp-content" in src.lower():
        die("a reference to EcoSauna's image hosting reached the page.")
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the %r credit." % CREDIT)
    if 'href="%s"' % DISCOVERY_URL not in src:
        die("the Garden Retreat Discovery link is missing.")

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL MECHANISM.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed", "commission",
                 "exclusive", "affiliate", "sponsored", "advert",
                 "buy now", "add to basket", "checkout", "referral"):
        if word in low:
            die("the page implies a relationship or mechanism that does not "
                "exist: " + word)
    if re.search(r"<form\b|<input\b|<textarea\b", src, re.I):
        die("the page carries a form or input. No lead capture is active.")

    # G11 · THE PREVIEW SAYS WHAT IT IS; THE RANGE IS COMPLETE.
    if "illustrative preview" not in low:
        die("the page does not identify itself as an illustrative preview.")
    if "before anything goes live" not in low:
        die("the pre-publication review ask is missing from the page.")
    if tuple(m["name"] for m in RANGE) != EXPECTED_PRODUCTS:
        die("the range does not match the five configurator products.")
    if tuple(m["name"] for m in RANGE if m["install"] is None) \
            != EXPECTED_NO_INSTALL_OPTION:
        die("an installation value appeared or disappeared that the "
            "configurator does not publish.")
    for m in RANGE:
        if ">%s<" % m["name"] not in visible:
            die("product %s is missing from the range." % m["name"])
        if m["from"] not in visible:
            die("the starting price of %s is missing." % m["name"])
    n_tbc = sum(1 for m in RANGE if m["install"] is None)
    if visible.count(TBC_TEXT) != n_tbc:
        die("'%s' appears %d times for %d unpublished values."
            % (TBC_TEXT, visible.count(TBC_TEXT), n_tbc))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("ECOSAUNA PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    19 guards passed")
    print("  ok    0 external images — imagery state C, permission unknown")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    5 products; %d installation values to be confirmed" % n_tbc)
    print("  ok    no partnership, commission, form, testimonial, origin, "
          "health or planning claim")
    print("  ok    32-county delivery attributed; planning firewall present")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
