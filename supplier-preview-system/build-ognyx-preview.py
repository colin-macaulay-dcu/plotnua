#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE OGNYX PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html, reused.

*** IMAGERY IS PREVIEW-ONLY HERE, AND THAT IS THE DIFFERENCE. ***

Fabian at OGNYX asked to see the preview before proceeding and invited
"any example imagery, product presentation and links you propose to use".
That is written permission for THIS PAGE. It is not publication permission:
Atlas Permission Outcome stays "Unknown — Awaiting Reply".

The preview-scoped rights record comes from
.github/scripts/build-ognyx-grant.py, and what keeps it to this one page is
atlas-tools/prove-preview-only-containment.mjs, which refuses an OGNYX image
anywhere else in the tree. The rights gate was not weakened to make this
possible; the record was made narrower than the gate would enforce.

*** THREE CATEGORIES, ONE FRAMED PRODUCT. *** OGNYX sell cold plunges,
saunas and hot tubs, and the point of the preview is that they can support
several Garden Retreat routes. But the hero image IS the product card's
image -- same <section> as the name and the price -- so the framed product
and the first image must be the same thing. The cold plunge is framed because
it is the only one of the three with genuine first-party PHOTOGRAPHS of the
product; the sauna and hot tub follow in their own sections.

*** PHOTOGRAPH VERSUS VISUALISATION. *** Every image below was opened and
looked at. Filenames are no guide here: the files named "Screenshot..." are
the real photographs and the ones named after the product are the renders.
Two of the four are visualisations and the page says so, because a render
shown as a photograph misrepresents what a homeowner would receive.

*** THE SEND GATE APPLIES. *** SUPPLIER-PREVIEW-SYSTEM-V1 §10.1: build,
prove, deploy, hand the URL to the founder, STOP. Nothing here sends
anything, and a clean run is not approval to email Fabian.

Run: python3 build-ognyx-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/ognyx-preview.html") if STAGE
       else SITE / "ognyx-preview.html")

SUPPLIER = "OGNYX"
EVIDENCE_DATE = "2 October 2026"
PERMISSION_DATE = "2 October 2026"
SUPPLIER_SITE = "https://www.ognyx.com/"
CREDIT = "© OGNYX"
PERMITTED_PREFIX = "https://www.ognyx.com/cdn/shop/files/"

PLUNGE_URL = ("https://www.ognyx.com/products/"
              "stainless-steel-cold-plunge-tub-for-one")
SAUNA_URL = "https://www.ognyx.com/products/1-6m-outdoor-sauna-for-3-persons"
TUB_URL = ("https://www.ognyx.com/products/"
           "round-hot-tub-with-integrated-wood-fired-stove-for-5-people")

# ── THE FOUR IMAGES, EACH ONE ACTUALLY LOOKED AT ──────────────────────────
# Inspected in a browser on 2 October 2026. Alt text describes what is
# visible and nothing else: no inference from the filename, the product title
# or the page it sits on. None of the four contains a person or third-party
# branding. Images 3 and 4 are visualisations, not photographs, and the page
# labels them.
OGNYX_IMAGES = [
    # 1 — PHOTOGRAPH. The hero, and the strongest accurate first-party
    #     photograph of any of the three products.
    {"url": PERMITTED_PREFIX + "Screenshot2025-08-13at21.01.07.png"
            "?v=1755111942&width=1024",
     "kind": "photograph",
     "alt": "Photograph of the OGNYX stainless steel cold plunge tub, clad "
            "in vertical timber staves with two steel hoops and a stainless "
            "inner rim, standing on gravel with a timber step stool beside "
            "it"},
    # 2 — PHOTOGRAPH. The stainless interior, which is the material claim.
    {"url": PERMITTED_PREFIX + "Screenshot2025-08-13at21.01.20.png"
            "?v=1755111942&width=1024",
     "kind": "photograph",
     "alt": "Photograph looking down into the same empty cold plunge tub, "
            "showing the stainless steel interior, the timber staves and the "
            "two steel hoops, on gravel"},
    # 3 — VISUALISATION. Barrel sauna exterior in a garden setting.
    {"url": PERMITTED_PREFIX + "Screenshot2025-08-11at18.27.16"
            "_33889bd3-cb18-4369-83b3-b0be9a8d8586.png"
            "?v=1754936822&width=1024",
     "kind": "visualisation",
     "alt": "Visualisation of the OGNYX 1.6m outdoor barrel sauna on a "
            "timber deck in a garden, with a glass door, a dark shingled "
            "roof and garden furniture beside it"},
    # 4 — VISUALISATION. Carries a caption bar burned into the image by
    #     OGNYX reading "Ø 2M FOR 5 PERS". Recorded rather than cropped
    #     around: the images are used unmodified.
    {"url": PERMITTED_PREFIX + "Screenshot2025-08-12at19.20.47.png"
            "?v=1755025372&width=1024",
     "kind": "visualisation",
     "alt": "Visualisation of the OGNYX round hot tub, clad in timber with a "
            "stainless chimney rising from the integrated stove inside it "
            "and a timber step stool alongside, beside a swimming pool. The "
            "image carries OGNYX's own caption bar reading Ø 2M FOR 5 PERS"},
]

# ── CLAIMS THIS PAGE MUST NOT MAKE ─────────────────────────────────────────
# OGNYX sell wellness products and their own copy uses "health benefits of
# cold immersion" and "therapeutic". PlotNua does not repeat a health claim
# to a homeowner, whoever first wrote it. The delivery, VAT and lead-time
# bans exist because their published policies are deliberately conditional:
# free delivery applies to eligible saunas "where stated", VAT is confirmed
# at checkout, and production time varies by configuration. Stating any of
# them flatly would turn a conditional into a promise.
BANNED_CLAIM_PHRASES = [
    "health benefit", "therapeutic", "improves recovery", "boosts",
    "reduces inflammation", "immune", "detox", "cures", "treats ",
    "inc. vat", "including vat", "vat included", "ex. vat", "plus vat",
    "free delivery", "delivery is free", "delivery included",
    "installation included", "we install", "fully installed",
    "assembled on site", "warranty included", "guaranteed",
    "in stock", "next day", "ships in", "lead time of",
]

AI_ASSET_TOKENS = ["chatgpt", "midjourney", "ai-generated", "ai generated",
                   "dall-e", "stable diffusion"]


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── G0a · THE COUNT, CHECKED BEFORE ANYTHING INDEXES THE LIST ─────────────
# This sits above OTHER_CATEGORIES because that block indexes OGNYX_IMAGES[2]
# and [3] at import time. With the check only inside main(), removing an asset
# raised IndexError before any guard ran -- and a builder that CRASHES has not
# refused, it has merely failed. Found by the guard-capability proof, which is
# what that proof is for.
if len(OGNYX_IMAGES) != 4:
    die("expected the 4 inspected assets, found %d. Each one was opened and "
        "looked at; a different number means the list changed without that "
        "happening." % len(OGNYX_IMAGES))

# ── THE OTHER TWO CATEGORIES ───────────────────────────────────────────────
# A SECTION EACH, not a second price in the same hero. The brief is that
# OGNYX can support several Garden Retreat routes, and the way to show that
# honestly is to show the three products separately with their own published
# figures. Markup is <section>, h2, h3, p, b, br and .pn-open — all already
# in the template's stylesheet, so no new CSS. The two images here are
# inline-styled on purpose: .results-hero-media and .pn-image-credit are both
# scoped '.pn-stage .…' and these sections sit outside the stage, so the class
# names alone would ship unstyled natural-width images that overflow at 390.
def media(img):
    return (
        '  <div style="position:relative; max-width:460px; aspect-ratio:4/3;\n'
        '              border-radius:14px; overflow:hidden; margin:18px 0 0;\n'
        '              box-shadow:0 14px 28px -14px rgba(36,53,31,.18);">\n'
        '    <img src="%s" alt="%s" loading="lazy"\n'
        '         style="width:100%%; height:100%%; object-fit:cover; '
        'display:block;">\n'
        '    <span style="position:absolute; left:0; right:0; bottom:0;\n'
        '                 padding:16px 14px 8px; font-size:10.5px; '
        'color:#fff;\n'
        '                 background:linear-gradient(0deg, '
        'rgba(20,34,26,.62) 0%%,\n'
        '                   rgba(20,34,26,0) 100%%);">%s</span>\n'
        '  </div>\n' % (img["url"], img["alt"].replace('"', "&quot;"), CREDIT))


OTHER_CATEGORIES = """<!-- THE OTHER TWO CATEGORIES. Shown as their own sections so each one
     carries its own published price and specification. Every figure is from
     the OGNYX product page linked in the heading, read on %s. -->
<section>
  <h2>The sauna</h2>
  <p><b>1.6m Outdoor Sauna for 3 people</b><br>€2,850</p>
  <p>Model S16E. 160 &times; 200 &times; 210 cm assembled, 200 &times; 120
     &times; 150 cm flat-packed, around 500 kg. Steam room 4.2 m&sup3; with a
     stated capacity of about two to three people. Wood thickness 40 mm,
     spruce body, thermowood benches, tempered glass door, bitumen shingle
     roof and stainless steel hoops. Heating time is given as about an hour.</p>
  <p>It is available flat-packed or fully assembled, and the configurator
     covers the electric stove, a glass or mirror front wall and lighting.</p>
%s  <p><a href="%s" rel="noopener">See the sauna on ognyx.com</a></p>
</section>

<section>
  <h2>The hot tub</h2>
  <p><b>Round Hot Tub with integrated wood-fired stove for 5 people</b><br>€2,440</p>
  <p>Model Round &Oslash;2.0 with integrated stove. Stated capacity four to
     six people, 1,100 litres, 265 kg, 1.1 m high and 0.83 m deep. A
     fiberglass bath planked with 18 mm thermowood, with a 30 kW stainless
     steel stove inside the tub, a chimney guard, waterproof plywood flooring
     and a drain valve. The configurator covers a bubble and hydro massage
     system, LED lighting, an electric heater and a filter.</p>
%s  <p><a href="%s" rel="noopener">See the hot tub on ognyx.com</a></p>
</section>
""" % (EVIDENCE_DATE,
       media(OGNYX_IMAGES[2]), SAUNA_URL,
       media(OGNYX_IMAGES[3]), TUB_URL)

# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
# FOUR, and every one survived a read of the OGNYX shipping policy and terms
# of 2 September 2026. Questions that policy already answers were dropped:
# "do you install?" is answered (assembly is the customer's unless agreed;
# installation needs a separate quotation), and so is the general dispatch
# window. What is left is what those documents leave conditional.
OPEN_QUESTIONS = """<!-- THE OPEN QUESTIONS — only what the OGNYX site does not already answer. -->
<section>
  <h2>A few things we would ask before publishing</h2>
  <p>Everything above is from your own pages, so where they stop we stop too.
     These four are the points a homeowner would ask us about.</p>
  <div class="pn-open">
    <ul>
      <li><b>VAT.</b> Your terms say the total payable, with any applicable
          VAT, is shown before checkout. Is the figure on the product page
          itself the VAT-inclusive price for an Irish buyer, or does it
          change at checkout?</li>
      <!-- G8 refused two earlier drafts of this one: "delivery is free" and
           "delivery included" are both banned phrases, because OGNYX's own
           policy makes each of them conditional. The copy moved; the bans
           stayed. -->
      <li><b>Delivery within Ireland.</b> Your shipping policy makes standard
          delivery free of charge for eligible saunas where the product page
          says so. For these three products and an Irish address, is delivery
          part of the price or quoted separately?</li>
      <li><b>Positioning and assembly.</b> You list assembled delivery,
          positioning and lifting as services needing a separate quotation.
          Is there a typical Irish package and an indicative figure we could
          show, or is it quoted case by case?</li>
      <li><b>Lead time.</b> Production time is stated as varying by
          configuration. For these three in a standard specification, what
          would you tell an Irish homeowner to expect from order to
          delivery?</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Plain, short, product-led, supplier-facing. No invented homeowner. Every
# figure traces to the OGNYX page linked beside it, read on 2 October 2026.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How OGNYX could appear within PlotNua",
    "DEMO_LEDE": "Here is a simple example of how OGNYX could appear within "
                 "PlotNua. It uses your published products, prices and "
                 "specifications, and nothing else.",


    "OFFER_NAME": "Stainless Steel Cold Plunge Tub for One",
    "VERIFIED_PRICE": "&euro;2,310",
    "VERIFIED_PRICE_BASIS": "exactly as published on ognyx.com. The product "
                            "page does not state whether the figure is "
                            "VAT-inclusive, so neither do we.",

    "VERIFIED_FACT_1_LABEL": "Size",
    "VERIFIED_FACT_1_VALUE": "86 cm diameter, 105 cm high, 400-litre capacity",
    "VERIFIED_FACT_2_LABEL": "Build",
    "VERIFIED_FACT_2_VALUE": "stainless steel interior inside an 18 mm "
                             "thermowood exterior",
    "VERIFIED_FACT_3": "The basic set includes the tub with thermowood "
                       "planking, waterproof plywood flooring, two stainless "
                       "steel hoops, a thermowood bench and a drain",
    "VERIFIED_FACT_4": "A cooler, a cover, stairs and an electric chiller are "
                       "listed as options; the chiller both cools and heats",
    "VERIFIED_FACT_5": "Designed for one person",

    "THINGS_TO_CHECK": "the page does not say whether the price includes "
                       "VAT, and delivery within Ireland, positioning and "
                       "lead time are the other things a homeowner would "
                       "want settled before ordering.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. Nothing here claims a
    # capability PlotNua does not have.
    "HOMEOWNER_LOCALITY": "Co. Wicklow",
    "PERSONALISATION": "Shown for a homeowner in Co. Wicklow, from the "
                       "location they gave us. We do not ask them about "
                       "ground conditions, drainage or power, so we would "
                       "not pretend to know &mdash; those stay as things to "
                       "raise with you.",

    "WHY_1_LABEL": "THREE ROUTES, ONE SUPPLIER",
    "WHY_1_TEXT": "A homeowner looking at a garden retreat does not arrive "
                  "knowing whether they want a sauna, a hot tub or cold "
                  "water. OGNYX cover all three, so the same supplier stays "
                  "relevant whichever way the thinking goes.",
    "WHY_2_LABEL": "AN IRISH COMPANY",
    "WHY_2_TEXT": "OGNYX LIMITED is registered in Ireland, in Bray, Co. "
                  "Wicklow. For an Irish homeowner comparing outdoor "
                  "wellness options, that is a material difference from "
                  "ordering from abroad.",
    "WHY_3_LABEL": "REACHED THROUGH WELLNESS",
    "WHY_3_TEXT": "A homeowner arrives here having decided they want a "
                  "garden retreat, not having typed your name into a search "
                  "box. That is a different kind of enquiry from a directory "
                  "click.",

    "CLOSING_PROPOSITION": "Does this represent OGNYX accurately for an Irish "
                           "homeowner?",
    "CLOSING_SUPPORT": "If anything here is wrong, out of date or missing, "
                       "tell us and we&rsquo;ll correct it. Nothing is "
                       "published until you say so.",

    "DATE": EVIDENCE_DATE,
}


def imagery_block():
    """The hero media inner HTML. The cold plunge photographs lead."""
    if not OGNYX_IMAGES:
        return None
    hero, rest = OGNYX_IMAGES[0], OGNYX_IMAGES[1:]
    out = ['        <div class="results-hero-media has-pn-gallery">',
           '          <img src="%s" alt="%s" loading="lazy">'
           % (hero["url"], hero["alt"]),
           '          <span class="pn-image-credit">%s</span>' % CREDIT,
           '        </div>']
    if rest:
        every = [hero] + rest
        out.append('        <div class="pn-gal-strip">')
        for n, i in enumerate(every):
            out.append('          <button type="button" class="pn-gal-thumb%s" '
                       'aria-pressed="%s" aria-label="View image %d of %d" '
                       'data-full="%s" data-alt="%s" data-credit="%s">'
                       '<img src="%s" alt=""></button>'
                       % (" is-on" if n == 0 else "",
                          "true" if n == 0 else "false",
                          n + 1, len(every),
                          i["url"], i["alt"].replace('"', "&quot;"), CREDIT,
                          i["url"]))
        out.append('        </div>')
    return "\n".join(out)


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · EVERY IMAGE INSIDE THE PERMITTED SCOPE, UNMODIFIED.
    # The count is already settled by G0a above, before the category blocks
    # index the list. This is the per-asset check.
    for i in OGNYX_IMAGES:
        if not i["url"].startswith(PERMITTED_PREFIX):
            die("image outside OGNYX's own file namespace: " + i["url"])
        if not i["url"].startswith("https://"):
            die("image is not https: " + i["url"])
        if i["kind"] not in ("photograph", "visualisation"):
            die("image %s is neither a photograph nor a visualisation (%r). "
                "Every asset must be classified, because the page says which "
                "is which." % (i["url"], i["kind"]))

    # G0b · NO AI-LABELLED ASSET.
    for i in OGNYX_IMAGES:
        blob = (i["url"] + " " + i["alt"]).lower()
        for tok in AI_ASSET_TOKENS:
            if tok in blob:
                die("an AI-labelled asset reached the image list (%r in %s)."
                    % (tok, i["url"]))

    # G0c · A VISUALISATION MUST SAY SO IN ITS OWN ALT TEXT.
    # The alt text is what a screen-reader user and the Atlas record both
    # get. A render described as a photograph is the misrepresentation this
    # whole classification exists to stop.
    for i in OGNYX_IMAGES:
        if i["kind"] == "visualisation" \
                and "visualisation" not in i["alt"].lower():
            die("a visualisation's alt text does not say it is one: "
                + i["url"] + ". Showing a render as a photograph "
                "misrepresents what a homeowner would receive.")
        if i["kind"] == "photograph" \
                and "photograph" not in i["alt"].lower():
            die("a photograph's alt text does not say so: " + i["url"]
                + ". The distinction is only honest if it is made on both "
                "sides.")

    # G1 · Strip the template's filling instructions.
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero:
        die("the introductory hero block was not found. Not guessing.")
    if "{{PROPOSITION}}" not in hero.group(0) or "{{LEDE}}" not in hero.group(0):
        die("the matched hero block does not carry the headline tokens.")
    src = src.replace(hero.group(0), "\n")
    FILL.pop("PROPOSITION", None)
    FILL.pop("LEDE", None)

    # G2 · Relocate the frozen journey band; the other categories and the
    # questions sit between.
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
                      OTHER_CATEGORIES + "\n" + OPEN_QUESTIONS + "\n"
                      + journey.strip("\n") + "\n\n" + why_anchor)

    # G3 · IMAGERY, PREVIEW-SCOPED.
    imgs = imagery_block()
    if imgs is None:
        die("the image list is empty, but Fabian asked to see the imagery we "
            "propose. A held slot here would not answer what he asked.")
    slot = re.search(r'        <div class="results-hero-media">\n'
                     r'          <div class="pn-photo-slot"[^>]*>.*?</div>\n'
                     r'        </div>\n', src, re.S)
    if not slot:
        die("the held media wrapper was not found, so the imagery cannot "
            "replace it. Nothing written.")
    src = src.replace(slot.group(0), imgs + "\n")
    FILL.pop("PHOTO_SLOT_LINE", None)

    # G3c · CREDIT, LINK BACK, AND THE SCOPE IN PLAIN WORDS.
    # A LITERAL © CHARACTER, never &copy;: the rights gate scans raw HTML for
    # the exact credit token, so the entity form would read as credited to a
    # person while the gate saw no credit at all.
    credit_line = (
        '          <p class="credit-line">%s. Images are used unmodified and '
        'served from <a href="%s" rel="noopener">ognyx.com</a>, with '
        'permission given %s to prepare this preview. They are used on this '
        'page only and are not published anywhere else; if OGNYX ask for any '
        'of them to be changed or removed, we change or remove them. Every '
        'figure on this page is published by OGNYX and was read on %s.</p>\n'
        % (CREDIT, SUPPLIER_SITE, PERMISSION_DATE, EVIDENCE_DATE))
    foot = "<footer>\n"
    if src.count(foot) != 1:
        die("the footer anchor is not unique. Nothing written.")
    src = src.replace(foot, credit_line + foot)

    # G3b · THE CLOSING HEADING is hardcoded in the template, not a token.
    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once. Nothing written.")
    src = src.replace(old_head, "<h2>Before anything goes live</h2>")

    # G4 · Fill every token; refuse if one is missing or left behind.
    for key, value in FILL.items():
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

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Cosy Cabins", "Irish Sauna Company", "Hutsmith",
                  "Yard Box", "Power Sheds", "TRIQ", "BIOBUILDS",
                  "Superior Pergola", "Honka", "MyCabin", "Harvia",
                  "Tanktribe", "TANKKD"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support: %r. OGNYX's own policies leave VAT, delivery, "
                "installation and lead time conditional, and their product "
                "copy makes health claims PlotNua does not repeat." % phrase)

    # G8b · THE VISUALISATIONS MUST BE LABELLED ON THE PAGE, not only in the
    # image list. An honest classification that never reaches the reader is
    # not a classification.
    vis = sum(1 for i in OGNYX_IMAGES if i["kind"] == "visualisation")
    if low.count("visualisation") < vis:
        die("the page shows %d visualisation(s) but says 'visualisation' "
            "fewer times than that. A render presented as a photograph is "
            "the one thing this classification exists to prevent." % vis)

    # G9 · THE CREDIT AND THE LINK BACK, proven on the artefact.
    #
    # THE CONSTANT IS CHECKED BEFORE IT IS COUNTED. src.count("") returns the
    # page length, so an emptied CREDIT would make a count-only guard pass
    # while shipping an uncredited page.
    if CREDIT != "© OGNYX":
        die("the required credit constant is not '© OGNYX' but %r. The "
            "rights record requires that exact wording." % CREDIT)
    if "&copy;" in src:
        die("the credit is written as the HTML entity &copy;. The rights gate "
            "scans raw HTML for a literal ©, so the entity form would read "
            "as credited while the gate saw no credit.")
    if src.count(CREDIT) < 2:
        die("imagery without the %s credit present at least twice (the image "
            "caption and the rights line)." % CREDIT)
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s. A mention in prose is not a "
            "link." % SUPPLIER_SITE)
    # Four in the strip, the hero repeated as its own first thumbnail, and
    # the sauna and hot tub images in their own sections: 4 + 1 + 2.
    EXPECTED_IMGS = len(OGNYX_IMAGES) + 3
    if len(re.findall(r'<img[^>]+src="' + re.escape(PERMITTED_PREFIX), src)) \
            != EXPECTED_IMGS:
        die("the rendered image count is not the four assets plus the hero "
            "repeat in the thumbnail strip plus the two category images "
            "(expected %d). Something was dropped or duplicated."
            % EXPECTED_IMGS)
    stray = [u for u in re.findall(r'<img[^>]+src="(https?://[^"]+)"', src)
             if not u.startswith(PERMITTED_PREFIX)]
    if stray:
        die("an image outside the permitted scope reached the page: "
            + stray[0])

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
    print("OGNYX PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    15 guards passed")
    print("  ok    %d inspected images, all served from ognyx.com"
          % len(OGNYX_IMAGES))
    print("  ok    %d photograph(s), %d visualisation(s), each labelled"
          % (len(OGNYX_IMAGES) - vis, vis))
    print("  ok    credit %r present %d times, and the link back is a link"
          % (CREDIT, src.count(CREDIT)))
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no VAT, health, delivery, installation or lead-time claim")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched.")
    print("SEND GATE: §10.1 — hand the URL to the founder and STOP. A clean "
          "run is not approval to email the supplier.")


main()
