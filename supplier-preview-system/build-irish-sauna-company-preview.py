#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE IRISH SAUNA COMPANY PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
Reused, not forked. Same certified provider-led system that built the
TRIQBRIQ, Hutsmith, Honka, BIOBUILDS and Cosy Cabins previews.

*** THE IMAGERY DECISION, AND WHY THERE IS NONE. ***

Brona replied on 2 October 2026: "I'd be happy to take a look at the private
preview first, particularly to see how our products, specifications and
pricing would be presented." The outreach she was answering offered two
replies -- "YES" for permission to feature the company and use selected
website imagery, or "PREVIEW" to see the page first. She asked for the
preview. She did not say YES.

Atlas therefore holds Permission Outcome "Unknown -- Awaiting Reply", and
UNKNOWN is not GRANTED. The publish-time rights gate has no page-level
exemption and does not consult noindex: every external image on every
deployed .html is treated as published, because a homeowner who reaches the
URL can see it. This was proven empirically on the Cosy Cabins build, where
an honest manifest row carrying the outcome Atlas actually holds was still
refused with "the permission outcome is Unknown -- Awaiting Reply. NOT A
GRANT". The only way to pass imagery would be to write a live-grant outcome
for a supplier who has not granted one.

THEREFORE: IMAGERY STATE C. No imagery, and the held panel says so in the
terms Brona will care about -- her images stay hers until she approves the
approach. G0 refuses any attempt to fill the image list while the outcome is
unknown.

*** WHAT MAKES THIS SUPPLIER DIFFERENT, AND THE TRAP IN IT. ***

Irish Sauna Company does two separate things:

  MANUFACTURES, in Corr na Mona, Co. Galway: commercial mobile saunas on
  genuine Ifor Williams chassis, and accommodation pods.

  SUPPLIES, as a reseller: premium Harvia garden saunas for private gardens.

The homeowner-facing garden range is HARVIA product. Both residential product
pages say so verbatim: "Manufactured by Harvia. Supplied in Ireland by Irish
Sauna Company." Describing a garden sauna as Irish-built would be false and
would be the single easiest way to embarrass PlotNua in front of this
supplier. G8's forbidden list is therefore built around ORIGIN claims.

AND NOTE WHAT IS *NOT* FORBIDDEN HERE: insulation. On the Cosy Cabins garden
rooms it is a paid upgrade and the guard bans it. On this product it is
published three times -- the feature strip, the included list and the
specification table -- so it is an evidenced fact and may be stated. A guard
list copied between suppliers would either lie or gag; this one is per
supplier for that reason.

Run: python3 build-irish-sauna-company-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/irish-sauna-company-preview.html")
       if STAGE else SITE / "irish-sauna-company-preview.html")

SUPPLIER = "Irish Sauna Company"
EVIDENCE_DATE = "2 October 2026"
SUPPLIER_SITE = "https://irishsaunacompany.com/"
PRODUCT_URL = SUPPLIER_SITE + "products/harvia-legend-electric-outdoor-sauna"
RANGE_URL = SUPPLIER_SITE + "collections/residential-outdoor-saunas-ireland"
CREDIT = "© Irish Sauna Company"

# IMAGERY STATE C. Empty by governance, not by oversight. G0 enforces it.
ISC_IMAGES = []

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT ───────────────────────────────────
# Phrases, not bare words, and the omissions are as deliberate as the
# entries. See the module docstring on insulation.
BANNED_CLAIM_PHRASES = [
    # ORIGIN. The garden range is Harvia's, not theirs.
    "irish built", "irish-built", "built in galway", "manufactured in galway",
    "we manufacture", "handcrafted in", "irish made", "irish-made",
    # SERVICE. Nothing published says they install or connect.
    "installation included", "we install", "installed by irish sauna",
    "fitted by our", "turnkey installation",
    # MONEY. Shipping is excluded from every listed price, explicitly.
    "delivery included", "shipping included", "free delivery",
    # TIME. Published for the Alpina only, and not for this model.
    #
    # THIS ONE CAUGHT ITS OWN FIRST BUILD, correctly. The open-questions copy
    # originally read "the Alpina View Large publishes a lead time of roughly
    # eight to nine weeks" -- an evidenced fact, properly attributed, but the
    # phrase is the same one a false claim would use. The copy was reworded to
    # "a timescale of" rather than the ban narrowed: a blunt guard with
    # slightly constrained prose is worth more than a clever guard with a hole
    # in it, because the prose is reviewed and the guard is not.
    "lead time of", "weeks from confirmed order", "weeks from order",
    # THE USUAL UNPUBLISHED THREE.
    "planning exempt", "no planning permission", "does not need planning",
    "warranty", "guaranteed for", "year guarantee",
    "certified", "certification",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
# NOT A SECOND PRODUCT SECTION. Brona asked to see how products,
# specifications and pricing would be presented, so the page leads with one
# fully specified product and then asks the three things her own site leaves
# open. Each question names what the site does say, so it reads as attention
# rather than as a complaint.
#
# Markup is <section>, h2, h3, p and .pn-open -- all already in the
# template's stylesheet, so this introduces no new CSS. .pn-open is the
# template's own open-questions component and renders each item with a dash.
OPEN_QUESTIONS = """<!-- THE OPEN QUESTIONS — the three things the supplier's own site leaves
     open, asked as questions and not resolved. Each one names what the site
     does say first. Do not answer these here; the point is that PlotNua
     asks rather than guesses. -->
<section>
  <h2>Three things we would ask before publishing</h2>
  <p>These are the three things we&rsquo;d like to check with you before the
     page goes live.</p>
  <div class="pn-open">
    <ul>
      <li><b>Installation.</b> The Legend page says the final electrical
          connection must be made by a suitably qualified electrician, and
          the Alpina page says site cabling, trenching, consumer-board
          alterations and the final connection are arranged by the customer.
          Does Irish Sauna Company offer positioning and connection as a
          service, or is that always the homeowner&rsquo;s own contractor?</li>
      <li><b>Timing.</b> The Alpina View Large publishes a timescale of
          roughly eight to nine weeks. The Legend Electric publishes none.
          Is there a typical timescale for it, and does the autumn/winter
          build-slot notice on your site apply to the Harvia garden saunas
          or only to the mobile saunas you build in Galway?</li>
      <li><b>Delivery.</b> Shipping is excluded from every listed price and
          quoted per customer, which makes sense for a 1,150kg module. Is
          there a typical range, or a way of putting it, that we could show
          a homeowner up front so the figure on screen is not the whole
          story by accident?</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Every figure traces to irishsaunacompany.com, read live 2 October 2026.
# Specification-forward, because that is what Brona asked to see.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Irish Sauna Company",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your product page publishes. They would "
                 "first discover a possibility for their property, work "
                 "through whether it fits and what to check, and only then "
                 "reach suppliers &mdash; so by the time this screen appears "
                 "the thinking has already happened.",


    "OFFER_NAME": "Harvia Legend Electric Outdoor Sauna",
    "VERIFIED_PRICE": "&euro;17,880",
    "VERIFIED_PRICE_BASIS": "inc. VAT, exactly as published. Manufactured by "
                            "Harvia and supplied in Ireland by Irish Sauna "
                            "Company.",

    "VERIFIED_FACT_1_LABEL": "Capacity",
    "VERIFIED_FACT_1_VALUE": "4&ndash;6 people &mdash; comfortable for four "
                             "adults, seating for up to six bathers",
    "VERIFIED_FACT_2_LABEL": "Footprint",
    "VERIFIED_FACT_2_VALUE": "2.25m &times; 2.30m, 2550mm high",
    "VERIFIED_FACT_3": "Harvia Legend Pro PO11 11kW electric heater, with "
                       "sauna stones, on a 400V 3N~ supply",
    "VERIFIED_FACT_4": "Insulated outdoor construction, panoramic glazing, "
                       "pre-installed LED lighting and liftable benches",
    "VERIFIED_FACT_5": "12m&sup3; calculated sauna volume, approx. 1,150kg, "
                       "Harvia product code SHL3499",

    # ONE HONEST LINE, and on this page the most useful sentence on it: the
    # listed price is the sauna, and the supplier says so plainly themselves.
    "THINGS_TO_CHECK": "the listed price is the sauna. Shipping is not "
                       "included and is quoted separately before an order is "
                       "confirmed, which at roughly 1,150kg depends on access "
                       "and unloading. The homeowner also provides the "
                       "prepared level base, the access for positioning and "
                       "the electrical supply, with the final connection made "
                       "by a suitably qualified electrician.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. The journey asks for an
    # Eircode and simplifyLocalityDisplay() reduces it to exactly this. It
    # asks nothing about site, access, ground conditions or electrical
    # supply, so nothing else here may be personalised however well it would
    # read -- and on this product the temptation is real, because access and
    # supply genuinely matter.
    "HOMEOWNER_LOCALITY": "Co. Clare",
    "PERSONALISATION": "Shown for a homeowner in Co. Clare, from the location "
                       "they gave us. We do not ask them about site access or "
                       "their electrical supply, so we would not pretend to "
                       "know either &mdash; those stay as things to check with "
                       "you.",

    "WHY_1_LABEL": "YOUR SPECIFICATION, NOT OUR SUMMARY",
    "WHY_1_TEXT": "Your product page publishes a full specification table, "
                  "which most suppliers we look at do not. A homeowner sees "
                  "the heater, the supply, the volume and the weight as you "
                  "published them, so the first conversation can start past "
                  "the basics.",
    "WHY_2_LABEL": "THE PRICE, WITH WHAT SITS OUTSIDE IT",
    "WHY_2_TEXT": "We show the listed figure and, next to it, that shipping "
                  "is quoted separately and the base and electrical work are "
                  "the homeowner&rsquo;s. People who understand that before "
                  "they call are easier to quote for than people who find out "
                  "afterwards.",
    "WHY_3_LABEL": "REACHED THROUGH WELLNESS",
    "WHY_3_TEXT": "A homeowner arrives here having decided they want a garden "
                  "retreat, not having typed your name into a search box. "
                  "That is a different kind of enquiry from a directory "
                  "click, and it is the one we are trying to send you.",

    "CLOSING_PROPOSITION": "Does this represent Irish Sauna Company "
                           "accurately for an Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, let us know and we&rsquo;ll correct it "
                       "before publication.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    if ISC_IMAGES:
        die("Irish Sauna Company imagery was added to this builder, but the "
            "Atlas Permission Outcome is 'Unknown — Awaiting Reply'. "
            "Brona asked to see the preview, she did not say YES. UNKNOWN is "
            "not GRANTED, and the publish-time rights gate refuses these "
            "images on any deployed page. Get written permission and a "
            "manifest row first.")

    # G1 · Strip the template's filling instructions (they carry {{TOKEN}}).
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero so the page opens on the
    # demonstration: the first thing Brona sees is her own result.
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

    # G3 · IMAGERY STATE C. The held panel is relabelled so it reads as a
    # deliberate position rather than a missing asset.
    # G3 · THE IMAGE POSITION CARRIES NO COPY (certified, 5 Oct
    # 2026). The relabel that stood here rewrote the slot heading into a
    # sentence about photography. There is no heading and no sentence
    # now; the rights gate is unchanged and still fails closed.

    # G3c · ATTRIBUTION. Every figure is their published information, so the
    # page says where it came from and links back. The same line carries the
    # origin fact, because a reader who sees "Harvia" in the product name
    # deserves to know who makes it and who supplies it.
    attribution = (
        '          <p class="credit-line">Every figure on this page is '
        'published by %s and was read from '
        '<a href="%s" rel="noopener">their Harvia Legend Electric page</a> '
        'and <a href="%s" rel="noopener">their garden sauna range</a> on %s. '
        'The Legend is manufactured by Harvia and supplied in Ireland by %s. '
        'No %s imagery is used anywhere on this page. '
        '%s &middot; <a href="%s" rel="noopener">irishsaunacompany.com</a>'
        '</p>\n'
        % (SUPPLIER, PRODUCT_URL, RANGE_URL, EVIDENCE_DATE, SUPPLIER,
           SUPPLIER, CREDIT, SUPPLIER_SITE))
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

    # G5 · PRIVACY. Non-negotiable, and doubly so here: nothing was granted.
    for directive in ("noindex", "nofollow", "noarchive", "nosnippet",
                      "noimageindex"):
        if directive not in src:
            die("the robots directive '%s' is missing." % directive)

    # The visible page: comments, <style> and <script> stripped, because the
    # template documents its own layout in CSS comments and a guard that
    # cannot tell commentary from a claim will refuse its own correct build.
    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    low = re.sub(r"\s+", " ", visible).lower()

    # G6 · NO OTHER SUPPLIER'S CONTENT. Harvia is deliberately absent from
    # this list: it is the manufacturer of the product being shown and naming
    # it is the accurate thing to do, not a leak.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Bruno", "Mateus"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support: %r. Either it is unpublished for this model, or "
                "it belongs to the supplier's Galway-built mobile saunas "
                "rather than this Harvia garden sauna." % phrase)

    # G8b · THE ORIGIN MUST BE STATED, not merely not-misstated. Naming a
    # Harvia product without saying who makes it and who supplies it invites
    # exactly the wrong inference from a page headed "Irish Sauna Company".
    if "manufactured by harvia" not in low:
        die("the page does not state that the Legend is manufactured by "
            "Harvia. Omitting it lets a reader assume Irish Sauna Company "
            "builds it, which their own page contradicts.")
    if "supplied in ireland by irish sauna company" not in low:
        die("the page does not state that the Legend is supplied in Ireland "
            "by Irish Sauna Company, which is the supplier's own wording and "
            "the half of the origin that is about them.")

    # G9 · NO IMAGERY, PROVEN ON THE OUTPUT and not merely on the input list.
    for pattern, what in (
            (r'<img[^>]+src="https?://', "an external <img>"),
            (r'<source[^>]+srcset="https?://', "an external <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"[^>]+content="https?://', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s. No external imagery may appear "
                "on this preview while permission is unknown." % what)
    # A REAL LINK, not the word in a sentence.
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s. Even with no imagery, the "
            "supplier's own site is where every figure came from, and a "
            "mention in prose is not a link." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the %r credit." % CREDIT)

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL IMPLICATION.
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
    print("IRISH SAUNA COMPANY PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    14 guards passed")
    print("  ok    0 external images — imagery state C, permission unknown")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    origin stated: manufactured by Harvia, supplied by %s"
          % SUPPLIER)
    print("  ok    no Irish-built, installation, delivery, lead-time, "
          "warranty or planning claim")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
