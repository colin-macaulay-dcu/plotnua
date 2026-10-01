#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER — THE HUTSMITH PRIVATE SUPPLIER PREVIEW.

Variant B, provider-led, straight from template-provider-led.html. No bespoke
layout, no new design language, no hand-editing of the emitted HTML: change the
copy here and re-run.

WHY PROVIDER-LED. Hutsmith's own route is "Configure my cabin" plus a site
survey, and they publish no cabin price. That is a provider relationship, not
one priced product carrying the conversation, so SUPPLIER-PREVIEW-SYSTEM-V1 §1
puts it in variant B.

EVERY FACT BELOW CAME OFF A HUTSMITH PAGE READ FOR THIS BUILD, 1 October 2026:
    https://hutsmith.co.uk/          home
    https://hutsmith.co.uk/about     about
    https://hutsmith.co.uk/design    details / specification
    https://hutsmith.co.uk/saunas    saunas, with published prices

WHAT IS DELIBERATELY ABSENT, AND WHY. /cabins and /frequent-questions could not
be read for this build -- they return no body text to the fetch available here,
and the browser could not reach the domain at all. So the cabin type names,
their dimensions, the lead time, and the delivery charges are NOT on this page.
Search engines will happily summarise those pages, and §2 is explicit that
third-party relays are not evidence. A gap stays a gap; on a provider-led
preview it is simply absent.

IMAGERY IS AUTHORISED BUT NOT YET PLACED. Dudley Radford granted it by email.
The held panel is therefore worded as an invitation with the permission already
given -- not as "not yet authorised", which would be untrue. No Hutsmith image
is referenced, because the image URLs could not be read first-party for this
build, and inventing an image URL would be worse than an empty panel.

NOT PUBLISHED, AND THE COMMISSION STAYS OFF THE PAGE. Dudley raised commission.
Nothing is agreed, so the page says nothing about it, and nothing on it casts
PlotNua as an agent, reseller, dealer, partner or exclusive channel.

Run: python3 build-hutsmith-preview.py
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"
OUT = SITE / "hutsmith-preview.html"

SUPPLIER = "Hutsmith"

# ── THE COPY ────────────────────────────────────────────────────────────────
# Voice test, §7: would Colin say this to Dudley, in person?
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    # The PlotNua hero lines. §12 calls these rarely changed; they are the
    # same two lines every preview has carried.
    "PROPOSITION": "Helping homeowners discover what their property could do.",
    "LEDE": "And make better-informed decisions about what comes next.",

    "DEMO_HEADING": "Imagine an Irish homeowner reaching Hutsmith like this.",
    "DEMO_LEDE": "The screen below is the real PlotNua interface. "
                 "Everything it says about Hutsmith came off your own site.",

    # IMAGERY STATE: authorised by Dudley, not yet placed. Worded accordingly.
    "PHOTO_SLOT_LINE": "You&rsquo;ve said yes to us using your website imagery, "
                       "so one of your own cabin photographs would sit here, "
                       "credited to Hutsmith and linked back to you.",

    "OFFER_NAME": "Modular cabins",

    # QUOTE-ONLY. Hutsmith publishes no cabin price, so none is invented. The
    # sauna prices they DO publish are named as sterling and ex VAT, and
    # explicitly not restated as an Irish delivered price (§8).
    "VERIFIED_PRICE": "Price on enquiry",
    "VERIFIED_PRICE_BASIS": "Hutsmith publishes no cabin price &mdash; the route is "
                            "&ldquo;Configure my cabin&rdquo; and a site survey. The "
                            "published sauna sizes run &pound;24,000 to &pound;30,000 + VAT, "
                            "sterling, not converted, and not an Irish quotation.",

    # PERSONALISATION GUARDRAIL §6. Locality comes from the Eircode lookup and
    # the appearance preference from the journey's own question. Nothing here
    # touches aspect, orientation or surface, which PlotNua does not capture.
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "In keeping with the natural-timber look they preferred.",

    "VERIFIED_FACT_1_LABEL": "Cladding",
    "VERIFIED_FACT_1_VALUE": "External larch, grown in the highlands of Scotland",
    "VERIFIED_FACT_2_LABEL": "Built",
    "VERIFIED_FACT_2_VALUE": "In the Hutsmith workshop, then assembled on site",
    "VERIFIED_FACT_3": "Double glazed windows, multipoint locking, airflow breathable membrane",
    "VERIFIED_FACT_4": "Full internal high grade ply, with bespoke ply shelving",
    "VERIFIED_FACT_5": "Standard electric pack &mdash; three double sockets, USB charger, LED lighting",

    "THINGS_TO_CHECK": "what the ground needs, how a module reaches the garden, "
                       "and what a survey and delivery look like outside the UK.",

    "WHY_1_LABEL": "More context",
    "WHY_1_TEXT": "By the time someone reaches Hutsmith they have already worked "
                  "through what their property can take and what they want from it.",
    "WHY_2_LABEL": "Clearer intent",
    "WHY_2_TEXT": "They arrive with a size, a look and a budget band in mind, so the "
                  "first conversation starts further along than a cold enquiry does.",
    "WHY_3_LABEL": "A better starting point",
    "WHY_3_TEXT": "Irish homeowners comparing timber cabins have no easy way to see a "
                  "maker like you next to the local options. PlotNua gives them one.",

    "CLOSING_PROPOSITION": "Before anything else, one practical question: what would a "
                           "Hutsmith cabin actually need to land in an Irish garden "
                           "&mdash; the survey, the delivery, the base &mdash; and is that "
                           "work you&rsquo;d want?",
    "CLOSING_SUPPORT": "Your survey fee is published for the UK and your delivery "
                       "charges are measured from the workshop, so Ireland changes "
                       "something in both. Working out what, before a homeowner asks, "
                       "seems the useful next step.",

    "DATE": "1 October 2026",
}

# Phrases that must never reach a supplier-facing page (§8, plus the founder's
# explicit commercial boundary for this build). Checked against the OUTPUT, so
# a careless edit to FILL cannot slip one through.
FORBIDDEN = [
    "partner", "partnership", "preferred supplier", "approved supplier",
    "recommended supplier", "trusted supplier", "endorse", "endorsement",
    "exclusive", "exclusivity", "commission", "agent", "reseller", "dealer",
    "listing fee", "sole channel", "only through",
    # Ireland facts nobody has evidenced.
    "irish showroom", "irish office", "irish installer", "irish projects",
    # The planning claim Hutsmith makes for UK flat roofs must not cross over.
    "no planning permission", "planning permission is not",
]

# Things that MUST be present, because their absence is the failure mode.
REQUIRED = [
    'content="noindex, nofollow, noarchive, nosnippet, noimageindex"',
    "Private preview",
    "Prepared for Hutsmith",
    "Republic of Ireland",
]


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G1 · Strip the template's own filling instructions. They carry {{TOKEN}}
    # and {{VERIFIED_FACT_N}} as examples, and every shipped preview drops this
    # block, so a surviving comment means the strip anchor moved.
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        print("REFUSED. The template's instruction comment was not found where "
              "expected; the strip anchor has moved. Not guessing.")
        return 1
    src = src.replace(block.group(0), "\n")

    # G2 · Fill. Every key must actually appear, or the token was renamed.
    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src:
            print("REFUSED. Token %s is not in the template. Nothing written." % needle)
            return 1
        src = src.replace(needle, value)

    # G3 · Record the one thing Hutsmith told us that their website does not
    # say: that they can serve the Republic of Ireland. It goes in the facts
    # list, attributed to the supplier, not asserted as a website fact.
    anchor = ("          <ul class=\"pn-facts\">\n")
    if src.count(anchor) != 1:
        print("REFUSED. The facts list anchor is not unique. Nothing written.")
        return 1
    src = src.replace(anchor, anchor +
                      "            <li><b>Republic of Ireland &mdash; confirmed "
                      "available by Hutsmith, 1 October 2026</b></li>\n")

    # G4 · No token may survive.
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", src)
    if left:
        print("REFUSED. Unreplaced tokens survive: %s" % sorted(set(left)))
        return 1

    # G5 · No forbidden claim.
    low = src.lower()
    hits = [p for p in FORBIDDEN if p in low]
    if hits:
        print("REFUSED. The output carries forbidden claim wording: %s" % hits)
        return 1

    # G6 · No other supplier's content. The template is shared, so a stray
    # name from a previous build is a real failure mode.
    others = ["koto", "haku", "triq", "power sheds", "powersheds", "yard box",
              "yardbox", "capsule castle", "honka", "superior pergola",
              "iglucraft", "shomera"]
    stray = [o for o in others if o in low]
    if stray:
        print("REFUSED. Another supplier's content is present: %s" % stray)
        return 1

    # G7 · No external image anywhere. Imagery is authorised but unplaced, and
    # an image slipping in without a rights-manifest grant would fail the gate.
    ext = re.findall(r'<img[^>]+src="(?!data:)[^"]*"', src)
    if ext:
        print("REFUSED. The page references an image: %s" % ext[:3])
        return 1

    # G8 · Required strings.
    for need in REQUIRED:
        if need not in src:
            print("REFUSED. A required string is missing: %r" % need)
            return 1

    OUT.write_text(src, encoding="utf-8")
    print("BUILT  %s" % OUT.name)
    print("  %d bytes, %d lines" % (len(src.encode()), src.count("\n") + 1))
    print("  tokens replaced     %d" % len(FILL))
    print("  external images     0  (imagery authorised, not yet placed)")
    print("  forbidden claims    0  (%d patterns checked)" % len(FORBIDDEN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
