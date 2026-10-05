#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE SAUNA EXPERTS PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
Reused, not forked. The same certified provider-led system that built the
TRIQBRIQ, Hutsmith, Honka, BIOBUILDS, Cosy Cabins, Irish Sauna Company and
Modulux previews. No new template, no redesign, no new CSS.

*** THE RECONCILIATION, DONE BEFORE ANYTHING WAS WRITTEN. ***

Sauna Experts Limited appears NOWHERE in PlotNua: not in Atlas, not in the
match or recognition pools, not in any supplier or contact register, not in
image-rights-records.json. A full-tree search for "sauna experts" and
"saunaexperts" returned nothing. There is no existing relationship to reflect
and none may be implied.

Where they are relevant is the live Discovery "Garden Retreat", which is the
same homeowner route the Cosy Cabins and Irish Sauna Company previews sit on.
That route is named because it exists, not to suggest Sauna Experts are in it.

*** WHY PROVIDER-LED EVEN THOUGH ONE PRODUCT IS FULLY SPECIFIED. ***

The Outdoor Sauna Chill publishes a complete specification and a price, which
on its own would point to Variant A. But the business is a custom builder with
a large shop behind it -- heaters, timber, controls, accessories, cabins -- and
§1 says that when the relationship is with a provider rather than a product,
Variant B is the one that makes fewer claims. This follows the Irish Sauna
Company precedent exactly: provider-led template, one fully specified product
carrying the demonstration.

*** IMAGERY STATE C. NO IMAGERY. ***

The reply was "PREVIEW". That is a request to SEE the page, not a grant.
UNKNOWN IS NOT GRANTED. Their product pages and gallery carry their own
photography of the units they build; none of it may be downloaded, re-hosted,
hotlinked or shown, and the page being private changes nothing, because the
publish-time rights gate treats every external image on every deployed .html
as published. G0 refuses any attempt to fill the image list and G9 proves the
absence on the OUTPUT rather than trusting the input.

*** THE TRAPS IN THIS SUPPLIER. THERE ARE THREE. ***

1 · SUPERLATIVES. Their site calls them "Ireland's Number One Sauna Shop",
    "the highest rated sauna supplier in Ireland", "Ireland's Top Sauna
    Manufacturer" and "the most professional". Those are their marketing and
    are nobody's verified fact. Repeating one as PlotNua's own would convert
    a claim we have not checked into a ranking we appear to endorse, on a page
    that exists to show editorial independence. G8 refuses all of them.

2 · THE EXPERIENCE FIGURE CONTRADICTS ITSELF. The homepage says the custom
    saunas are made "by sauna experts with over 20 years of experience" and,
    four paragraphs down, that the company was "founded by two passionate
    brothers with over 16 years of experience". Both are first-party and they
    disagree, so neither is used. An unknown stays unknown; it does not get
    averaged.

3 · IRISH MANUFACTURE IS THEIR CLAIM, NOT OUR FINDING. "All of our saunas are
    designed and manufactured in Ireland" is published by them and is exactly
    the kind of statement the Irish Sauna Company build had to be careful
    about in the other direction. PlotNua has not verified it, so the page
    attributes it in their own words rather than asserting it, and G8b
    REQUIRES the attribution to be present -- a guard that only forbids is no
    use when the thing that matters is a form of words.

THE HARVIA RELATIONSHIP IS DELIBERATELY NOT ON THE PAGE. They announce an
official partnership with Harvia in their site banner. It is their claim, we
have not verified it with Harvia, and the word "partner" is exactly what G10
refuses in order to keep PlotNua partnership implications off these pages. The
Harvia FACTS that matter to a homeowner are on the page instead: the Chill is
built around a Harvia woodburning stove, shield, base and chimney kit, which
is published on the product's own specification.

Run: python3 build-sauna-experts-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/sauna-experts-preview.html")
       if STAGE else SITE / "sauna-experts-preview.html")

SUPPLIER = "Sauna Experts"
EVIDENCE_DATE = "5 October 2026"
SUPPLIER_SITE = "https://saunaexperts.ie/"
PRODUCT_URL = SUPPLIER_SITE + "shop/custom-made-sauna-units/outdoor-sauna-chill-woodburner/"
CUSTOM_URL = SUPPLIER_SITE + "product-category/custom-made-sauna-units/"
CREDIT = "© Sauna Experts"

# IMAGERY STATE C. Empty by governance, not by oversight. G0 enforces it.
SE_IMAGES = []

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT, OR THAT ARE MARKETING ────────────
# Two different kinds in one list, on purpose. Some of these are unevidenced;
# the superlatives are worse than unevidenced -- they are the supplier's own
# sales copy, which PlotNua repeating would read as a ranking.
BANNED_CLAIM_PHRASES = [
    # SUPERLATIVE AND RANKING. Theirs to say, never ours.
    "number one", "highest rated", "best sauna", "ireland's top",
    "ireland's best", "most professional", "the leading", "top rated",
    "market leader", "cheapest", "best price",
    # THE CONTRADICTORY EXPERIENCE FIGURE.
    "20 years of experience", "16 years of experience", "over 20 years",
    "over 16 years",
    # UNPUBLISHED COMMERCIAL TERMS.
    "warranty", "guaranteed for", "year guarantee", "we guarantee",
    "lead time of", "weeks from confirmed order", "weeks from order",
    "free delivery", "delivery included",
    # PLANNING. Their site says nothing about it, and neither may we.
    "planning exempt", "no planning permission", "does not need planning",
    # HEALTH. Their blog makes wellness claims; a PlotNua page does not.
    "cures", "treats", "medically", "proven to reduce",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
OPEN_QUESTIONS = """<!-- THE OPEN QUESTIONS — the three things the supplier's own site leaves
     open, asked as questions and not resolved. Each one names what the site
     does say first. Do not answer these here; the point is that PlotNua
     asks rather than guesses. -->
<section>
  <h2>Three things we would ask before publishing</h2>
  <p>Everything above comes from your own product page, so where it stops we
     stop too. These are the three points a homeowner would ask us about, and
     we&rsquo;d rather have your answer than our best guess.</p>
  <div class="pn-open">
    <ul>
      <li><b>What the &euro;25,000 covers on site.</b> The listing says
          nationwide delivery, sauna installation and support with building
          advisory. Does the published figure include delivery and the build,
          or are those quoted separately once you have seen the garden?</li>
      <li><b>The base and the power.</b> The specification says the electrical
          systems and lighting are wired and certified by a qualified
          electrician, and the Chill Tub runs on a 13 amp supply. What does
          the homeowner need to have ready &mdash; a level base, a spur, an
          outdoor socket &mdash; before you arrive?</li>
      <li><b>Custom versus catalogue.</b> The Chill and the Mobile Sauna are
          published units, but the business is a custom builder. If someone
          wants a different size or a different layout, does the conversation
          start from one of these, or from a blank sheet?</li>
    </ul>
  </div>
  <h3>Where your imagery would go</h3>
  <p>The space beside the specification is where your photography of the
     finished units would sit, credited to Sauna Experts and linked back to
     your site. We haven&rsquo;t used any of it. You asked to see the approach
     first, so the imagery waits until you&rsquo;ve told us you&rsquo;re happy
     with it.</p>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Every figure traces to saunaexperts.ie, read live 5 October 2026.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Sauna Experts",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your own product page publishes. They arrive "
                 "through <i>Garden Retreat</i> &mdash; our Discovery about "
                 "putting a room, a studio or a wellness building in the "
                 "garden &mdash; work through whether it fits and what to "
                 "check, and only then reach suppliers. By the time this "
                 "screen appears the thinking has already happened.",

    "PHOTO_SLOT_LINE": "No Sauna Experts photography is used on this page. "
                       "You asked to see the approach before anything is "
                       "published, so your images stay yours until you tell "
                       "us otherwise. This is where they would sit, credited "
                       "to Sauna Experts and linked back to saunaexperts.ie.",

    "OFFER_NAME": "Outdoor Sauna Chill &mdash; Woodburner",
    "VERIFIED_PRICE": "&euro;25,000",
    # PREVIEW-IDENTITY-001 ORPHANED THIS LINE, and the page showed it.
    # The template's own note calls this slot a fragment -- "including
    # fitting", "as published, ex VAT" -- because it used to sit directly
    # after the price. The identity band moved the price up to the top, so
    # the fragment was left starting a paragraph on its own, lowercase and
    # with no subject: "exactly as published on the product page...". It
    # now carries its own subject and reads as a sentence. Switch
    # Electrical's basis was already written as a full sentence, which is
    # why only this page showed the fault.
    "VERIFIED_PRICE_BASIS": "The &euro;25,000 is exactly as published on the "
                            "product page, which "
                            "also lists the unit as in stock. Sauna Experts "
                            "say their saunas are designed and manufactured "
                            "in Ireland. The published specification also "
                            "lists two-level Black Alder benches, a "
                            "bronze-tinted glass door and integrated LED "
                            "lighting inside; a charred Nordic Spruce "
                            "exterior, steel-clad roof, double glazing, a lit "
                            "porch and Thermo Spruce decking outside; and "
                            "Siberian Larch cladding to the plunge area.",

    "VERIFIED_FACT_1_LABEL": "Capacity",
    "VERIFIED_FACT_1_VALUE": "2&ndash;4 people in the sauna room",
    "VERIFIED_FACT_2_LABEL": "Footprint",
    "VERIFIED_FACT_2_VALUE": "4m &times; 2.4m overall, with a sauna room of "
                             "1.8m &times; 1.85m and a cold plunge area of "
                             "1.9m &times; 2.1m",
    # FACTS 3-5 ARE SHORT BOLD PROOF POINTS, not sentences. The template
    # gives these three slots a <b> and no value span, so anything long
    # renders as a wall of bold body text and buries the Capacity and
    # Footprint pair above it -- worst at 390px, where .pn-facts li stacks.
    # The timber, bench, door, lighting, roof, glazing, porch, decking and
    # plunge-cladding detail is NOT lost: it moves verbatim into the price
    # basis prose, which is where what-the-figure-covers belongs.
    # The opening string fragment of each is left untouched on purpose --
    # the guard-capability proof anchors its sabotages to them.
    "VERIFIED_FACT_3": "Harvia woodburning stove with sauna stones, "
                       "shield, base and chimney kit",
    "VERIFIED_FACT_4": "Fully insulated with a vapour barrier; Thermo Aspen "
                       "lining",
    "VERIFIED_FACT_5": "Chill Tub holds 400 litres, adjustable down to "
                       "3&deg;C",

    # THE ONE HONEST LINE. It carries what the figure does and does not settle,
    # and PlotNua's own planning position -- which this supplier's site does
    # not address, so it is stated as ours rather than attributed to them.
    "THINGS_TO_CHECK": "the published figure is the unit. The listing says "
                       "nationwide delivery, sauna installation and support "
                       "with building advisory, but does not say which of "
                       "those sit inside the &euro;25,000, so we would not "
                       "guess for a homeowner. The electrical systems and "
                       "lighting are wired and certified by a qualified "
                       "electrician, and the Chill Tub runs on a 13 amp "
                       "supply, so the garden needs power as well as a base. "
                       "And a point of ours rather than yours: nothing on "
                       "your site addresses planning, and the local authority "
                       "is the only body that can confirm what a particular "
                       "site requires.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. The journey asks for an
    # Eircode and simplifyLocalityDisplay() reduces it to exactly this. It
    # asks nothing about the garden, the access or the electrical supply, and
    # on a 4m unit with a plunge tub all three genuinely decide the job.
    "HOMEOWNER_LOCALITY": "Co. Kildare",
    "PERSONALISATION": "Shown for a homeowner in Co. Kildare, from the "
                       "location they gave us. We don&rsquo;t ask them about "
                       "the garden, the access or where the power runs "
                       "&mdash; so we wouldn&rsquo;t pretend to know. Those "
                       "stay as things for your site visit.",

    "WHY_1_LABEL": "YOUR SPECIFICATION, NOT OUR SUMMARY",
    "WHY_1_TEXT": "Your product page publishes the timber, the stove, the "
                  "dimensions and the tub&rsquo;s technical detail, which "
                  "most suppliers in this market do not. A homeowner sees "
                  "those as you published them, so the first conversation "
                  "can start past the basics.",
    "WHY_2_LABEL": "THE PRICE, WITH WHAT SITS AROUND IT",
    "WHY_2_TEXT": "We show the published figure and, beside it, the things "
                  "it does not settle &mdash; the base, the power and what "
                  "delivery and installation involve. People who understand "
                  "that before they call are easier to quote for than people "
                  "who find out afterwards.",
    "WHY_3_LABEL": "ARRIVING WITH A DEVELOPED IDEA",
    "WHY_3_TEXT": "By the time a homeowner reaches you through PlotNua, they "
                  "have looked at what their own garden could take and "
                  "decided a sauna is what they want. They arrive with a "
                  "developed idea rather than an open question, and that is "
                  "the kind of enquiry we are trying to send you.",

    "CLOSING_PROPOSITION": "Does this represent Sauna Experts accurately for "
                           "an Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, tell us and we&rsquo;ll correct it before "
                       "anything is published.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    if SE_IMAGES:
        die("Sauna Experts imagery was added to this builder, but the reply "
            "was \"PREVIEW\" — a request to see the page, not a grant. "
            "UNKNOWN is not GRANTED, and the publish-time rights gate refuses "
            "external images on any deployed page. Get written permission and "
            "a manifest row first.")

    # G1 · Strip the template's filling instructions (they carry {{TOKEN}}).
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero so the page opens on the
    # demonstration: the first thing they see is their own result.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero:
        die("the introductory hero block was not found. Not guessing.")
    if "{{PROPOSITION}}" not in hero.group(0) or "{{LEDE}}" not in hero.group(0):
        die("the matched hero block does not carry the headline tokens.")
    src = src.replace(hero.group(0), "\n")
    FILL.pop("PROPOSITION", None)
    FILL.pop("LEDE", None)

    # G2 · Relocate the frozen journey band below the demonstration and put
    # the open-questions section between them. ONE anchored edit.
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
                      OPEN_QUESTIONS + "\n" + journey.strip("\n")
                      + "\n\n" + why_anchor)

    # G3 · IMAGERY STATE C.
    ask = "<b>Your project photography here</b>"
    if src.count(ask) != 1:
        die("the photo-slot heading was not found exactly once. Nothing "
            "written.")
    src = src.replace(ask, "<b>Your imagery is not used on this page</b>")

    # G3c · ATTRIBUTION.
    attribution = (
        '          <p class="credit-line">Every figure on this page is '
        'published by %s and was read from '
        '<a href="%s" rel="noopener">your Outdoor Sauna Chill page</a>, '
        '<a href="%s" rel="noopener">your custom sauna units</a> and '
        '<a href="%s" rel="noopener">saunaexperts.ie</a> on %s. '
        'No %s photography is used anywhere on this page. '
        '%s'
        '</p>\n'
        % (SUPPLIER, PRODUCT_URL, CUSTOM_URL, SUPPLIER_SITE, EVIDENCE_DATE,
           SUPPLIER, CREDIT))
    foot = "<footer>\n"
    if src.count(foot) != 1:
        die("the footer anchor is not unique. Nothing written.")
    src = src.replace(foot, attribution + foot)

    # G3b · THE CLOSING HEADING is hardcoded in the template, not a token.
    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once, so it cannot be "
            "replaced. Nothing written.")
    src = src.replace(old_head, "<h2>Before anything goes live</h2>")

    # G4 · Fill every token; refuse if one is missing or one is left behind.
    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src:
            die("token %s is not in the template. The template has moved."
                % needle)
        src = src.replace(needle, value)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", src)))
    if leftover:
        die("unfilled tokens remain: " + ", ".join(leftover))

    # PREVIEW-POLISH-001 · h3 HAS NO SIZE RULE IN THE TEMPLATE.
    # h1 and h2 are both given an explicit size; h3 inherits only the serif
    # family and weight 400, so it falls back to the browser default and
    # "Where your imagery would go" read as body copy beside the section h2.
    # One restrained rule, built from the type token that already exists
    # (--pn-s-quote, 19px) rather than a new size, and NO box, rule, border
    # or colour change. INJECTED PER PAGE ON PURPOSE: the shared certified
    # template is used by ~105 built previews and is not touched here.
    if src.count("</style>") != 1:
        die("expected exactly one </style> to anchor the h3 rule, found %d. "
            "The template's shape has changed and this edit will not guess."
            % src.count("</style>"))
    src = src.replace(
        "</style>",
        "h3{ font-size:var(--pn-s-quote); line-height:1.25;\n"
        "  margin:var(--pn-md) 0 6px; max-width:34ch; }\n</style>", 1)

    # G5 · PRIVACY.
    for directive in ("noindex", "nofollow", "noarchive", "nosnippet",
                      "noimageindex"):
        if directive not in src:
            die("the robots directive '%s' is missing." % directive)

    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    low = re.sub(r"\s+", " ", visible).lower()

    # G6 · NO OTHER SUPPLIER'S CONTENT. Harvia is deliberately absent from this
    # list: the Chill is built around a Harvia stove, shield, base and chimney
    # kit on the supplier's own specification, and naming the stove maker is
    # the accurate thing to do, not a leak.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Irish Sauna", "OGNYX", "TankTribe",
                  "Modulux", "Switch Electrical", "Sigenergy", "Auroom"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM, AND NO BORROWED SUPERLATIVE.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support, or repeats the supplier's own marketing as "
                "PlotNua's: %r." % phrase)

    # G8b · IRISH MANUFACTURE MUST BE ATTRIBUTED, NOT ASSERTED. This is the
    # positive half: the forbidden list cannot catch a true-sounding sentence
    # that drops the attribution, and the attribution is the whole difference
    # between reporting their claim and making it ours.
    if "sauna experts say their saunas are designed and manufactured in ireland" not in low:
        die("the page states or implies Irish manufacture without attributing "
            "it to the supplier. PlotNua has not verified where these units "
            "are built; Sauna Experts publish that they are designed and "
            "manufactured in Ireland, and the page must say whose claim it is.")

    # G8c · THE PLANNING POSITION. Their site is silent on planning, so the
    # page must carry PlotNua's own firewall rather than leaving a homeowner
    # to assume a 4m garden building is automatically fine.
    if "local authority is the only body that can confirm" not in low:
        die("the page does not carry the planning firewall. The supplier's "
            "site says nothing about planning, which is exactly why ours has "
            "to.")

    # G9 · NO IMAGERY, PROVEN ON THE OUTPUT.
    for pattern, what in (
            (r'<img[^>]+src="https?://', "an external <img>"),
            (r'<source[^>]+srcset="https?://', "an external <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"[^>]+content="https?://', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s. No external imagery may appear "
                "on this preview while permission is unknown." % what)
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s. Even with no imagery, the "
            "supplier's own site is where every figure came from, and a "
            "mention in prose is not a link." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the %r credit." % CREDIT)

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL IMPLICATION. The word
    # "partner" is refused outright, which is why the supplier's own Harvia
    # partnership banner is not reproduced here. See the module docstring.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed", "commission",
                 "exclusive"):
        if word in low:
            die("the page implies a relationship that does not exist: " + word)

    # G11 · THE PREVIEW MUST SAY WHAT IT IS.
    if "illustrative preview" not in low:
        die("the page does not identify itself as an illustrative preview.")
    if "before anything goes live" not in low:
        die("the pre-publication review ask is missing from the page.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("SAUNA EXPERTS PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    16 guards passed")
    print("  ok    0 external images — imagery state C, permission unknown")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no borrowed superlative, no experience figure, no warranty")
    print("  ok    Irish manufacture attributed; planning firewall present")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
