#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER — THE HUTSMITH PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
VARIANT:  B, provider-led
No bespoke layout, no new design language, no hand-editing of the emitted
HTML. Change the copy here and re-run.

WHY PROVIDER-LED. Hutsmith's own route is "Configure my cabin" plus a site
survey, and they publish no cabin price. That is a provider relationship, not
one priced product carrying the conversation, which is what SUPPLIER-PREVIEW-
SYSTEM-V1 §1 puts in variant B.

FIRST-PARTY EVIDENCE, read 1 October 2026:
    https://hutsmith.co.uk/          home
    https://hutsmith.co.uk/about     about
    https://hutsmith.co.uk/design    details / specification
    https://hutsmith.co.uk/saunas    saunas, with published prices

── IMAGERY ────────────────────────────────────────────────────────────────
Dudley Radford has GRANTED permission. The state is therefore decided by one
list, HUTSMITH_IMAGES, and nothing else:

    empty  -> the certified held slot, worded as authorised-and-awaiting.
              NOT "not yet authorised", which would now be untrue.
    filled -> certified state A: first-party <img> in .results-hero-media
              exactly as yardbox-preview.html does it, plus the credit line,
              and G9 then REQUIRES a live Hutsmith rights record.

It is empty today because no Hutsmith image URL could be read first-party.
/cabins and /frequent-questions return no body text to the fetch available
here; the in-app browser is refused by the host; the Chrome extension is not
connected; the WordPress REST route and both sitemap conventions return
nothing. Four independent routes, all closed. Inventing an image URL, or
lifting one from a search summary, would be a fabricated first-party fact,
so the slot stays honest until a real URL is in hand. Add the URLs to
HUTSMITH_IMAGES, add the rights record, re-run: no other edit is needed.

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
EVIDENCE_DATE = "1 October 2026"
PERMISSION_DATE = "30 September 2026"

# ── IMAGERY ────────────────────────────────────────────────────────────────
# Each entry: {"url": <a real hutsmith.co.uk URL>, "alt": <plain description>}
# Only hutsmith.co.uk / its own CDN. Unmodified. Credit stays on the page.
HUTSMITH_IMAGES = [
    {"url": "https://images.squarespace-cdn.com/content/v1/6952720a1e68c05bac7f54fe/"
            "8d8ab49b-c296-45cf-96d9-67d1989f4e22/SDOR-+DMR+-+Aldbury+-+6A.jpg?format=1500w",
     "alt": "A Hutsmith cabin in black timber, in a garden"},
    {"url": "https://images.squarespace-cdn.com/content/v1/6952720a1e68c05bac7f54fe/"
            "b24eee9f-8fd7-4b4d-8d90-70443115dae9/Hutsmith+Harbourne45176aa.JPG?format=1500w",
     "alt": "The plywood-lined interior of a Hutsmith cabin used as a home office"},
]

# Hutsmith's own Squarespace content store. 6952720a1e68c05bac7f54fe is the
# site id of hutsmith.com, so this path is as first-party as hutsmith.com
# itself -- exactly how yardbox-preview.html carries Yard Box's images from
# their own Squarespace store.
HUTSMITH_IMAGE_ROOTS = (
    "images.squarespace-cdn.com/content/v1/6952720a1e68c05bac7f54fe/",
    "hutsmith.com/",
    "hutsmith.co.uk/",
)

# ── THE COPY ───────────────────────────────────────────────────────────────
# Voice: short, ordinary, confident. Never sound written. No "imagine", no
# poetic phrasing, no mirrored constructions, no abstract strategy language.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    # NO OPENING HERO AT ALL. The brand wordmark, the headline and the
    # supporting line are removed outright, not reworded -- a replacement
    # slogan was explicitly ruled out. After the private-preview bar the page
    # goes straight to the demonstration, so the first substantive thing
    # Dudley sees is the Hutsmith result itself. {{PROPOSITION}} and {{LEDE}}
    # therefore no longer exist and are absent from this fill set.

    # Concrete, not speculative. No "imagine".
    "DEMO_HEADING": "How an Irish homeowner would reach Hutsmith",
    "DEMO_LEDE": "This is the PlotNua interface a homeowner would see. The "
                 "Hutsmith details come from your own published pages.",

    "PHOTO_SLOT_LINE": "",   # set below, by imagery state

    "OFFER_NAME": "Bespoke cabins",

    # Hutsmith publishes a real price against every completed project on
    # hutsmith.com/portfolio, so the band is theirs, not an estimate. It is
    # named as sterling and as completed-project prices, not a price list and
    # not an Irish quotation.
    "VERIFIED_PRICE": "&pound;33,500 &ndash; &pound;162,000",
    "VERIFIED_PRICE_BASIS": "the range Hutsmith publishes against their own "
                            "completed projects. Sterling, not converted, and "
                            "not an Irish quotation.",

    # PERSONALISATION GUARDRAIL §6. Locality comes from the Eircode lookup,
    # the look from the journey's own appearance question. Nothing here
    # touches aspect, orientation or surface, which PlotNua does not capture.
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "In keeping with the natural-timber look they preferred.",

    # All five from hutsmith.com, read 1 October 2026. Note what this
    # corrects: Hutsmith is the design studio, and the cabins are built by a
    # named licensed construction partner. Saying "built in the Hutsmith
    # workshop" full stop, as the older hutsmith.co.uk pages imply, would
    # misdescribe their own business to them.
    "VERIFIED_FACT_1_LABEL": "What Hutsmith do",
    "VERIFIED_FACT_1_VALUE": "Architectural design, from first ideas to technical drawings",
    "VERIFIED_FACT_2_LABEL": "Who builds it",
    "VERIFIED_FACT_2_VALUE": "Your Space Cabins, their licensed construction partner",
    "VERIFIED_FACT_3": "Built in the workshop and dropped on site; modular wall sections where access is tight",
    "VERIFIED_FACT_4": "Two to four weeks on site, depending on scale and complexity",
    "VERIFIED_FACT_5": "&pound;90 site survey, refundable on sale, and &pound;295 for design development",

    "THINGS_TO_CHECK": "ground works, access for the drop, and what the survey "
                       "and the build partner look like outside the UK.",

    # WHY THIS IS USEFUL TO HUTSMITH. Commercial, and no claim that lead
    # quality or conversion has been proven.
    "WHY_1_LABEL": "Better informed enquiries",
    "WHY_1_TEXT": "Homeowners have already worked through what could suit their "
                  "property before they reach Hutsmith.",
    "WHY_2_LABEL": "Clearer intent",
    "WHY_2_TEXT": "They arrive with a better idea of the size, use and type of "
                  "building they are considering.",
    "WHY_3_LABEL": "A route into the Irish market",
    "WHY_3_TEXT": "PlotNua can put Hutsmith in front of Irish homeowners who may "
                  "not otherwise find a UK supplier while comparing local options.",

    # CLOSING. Practical, not literary. Note the deliberate wording: "before
    # any homeowner enquiry reaches you" rather than "before we send genuine
    # enquiries your way", because the second promises enquiries that are not
    # flowing yet and §8 forbids presenting the enquiry route as operational.
    "CLOSING_PROPOSITION": "You&rsquo;ve confirmed that Hutsmith can supply "
                           "Ireland. Before any homeowner enquiry reaches you, "
                           "we want the practical details right for an Irish "
                           "customer.",
    "CLOSING_SUPPORT": "If you can confirm those points, PlotNua can present "
                       "Hutsmith more accurately to Irish homeowners.",

    "DATE": EVIDENCE_DATE,
}

# Only genuinely unestablished items belong here.
STILL_TO_CONFIRM = [
    "Delivery cost to Ireland",
    "Site survey arrangements for Ireland, and whether the &pound;90 fee still applies",
    "Base and ground preparation requirements",
    "Whether Your Space Cabins build in Ireland, or whether a local partner would",
    "Typical lead time for an Irish order",
]

FORBIDDEN = [
    # NOTE: bare "partner" is NOT here. Hutsmith's own cabins are built by
    # "Your Space Cabins, their licensed construction partner" -- that is
    # Hutsmith's fact about their own business, and refusing it would force
    # the page to misdescribe them. What must never appear is PlotNua being
    # cast as a partner, which G10b checks positionally instead.
    "preferred supplier", "approved supplier",
    "recommended supplier", "trusted supplier", "endorse", "endorsement",
    "exclusive", "exclusivity", "commission", "agent", "reseller", "dealer",
    "listing fee", "sole channel", "only through",
    "irish showroom", "irish office", "irish installer", "irish projects",
    "no planning permission", "planning permission is not",
    # Banned from the corrected copy by name.
    "imagine",
]

REQUIRED = [
    'content="noindex, nofollow, noarchive, nosnippet, noimageindex"',
    "Private preview",
    "Prepared for Hutsmith",
    "Republic of Ireland",
    "What we still need to confirm",
]

# Slogans and marketing statements that must never stand in for the removed
# hero. A replacement headline was explicitly ruled out.
BANNED_SLOGANS = [
    "in front of irish homeowners",
    "see what", "unlock", "discover what your", "helping homeowners discover",
    "the irish market awaits", "your route to ireland",
]


def low_so_far(s):
    """Lowercased visible text of the region ABOVE the demonstration only.

    That is the only place a replacement hero could sit, and scoping it there
    matters: the approved why-point legitimately reads "put Hutsmith in front
    of Irish homeowners", and the frozen journey band legitimately reads "See
    what a property like theirs could do". Checking the whole body would
    refuse both.
    """
    start = s.find('<div class="pv-bar"')
    end = s.find('class="pn-stage"')      # everything before the result card
    if start < 0 or end < 0:
        return ""
    return re.sub(r"<[^>]+>", " ", s[start:end]).lower()


def imagery_block():
    """The hero media inner HTML, decided solely by HUTSMITH_IMAGES."""
    if not HUTSMITH_IMAGES:
        return None, ("Hutsmith photography, authorised %s. Your own cabin "
                      "images go here, credited to Hutsmith and served from "
                      "your site." % PERMISSION_DATE)
    imgs = "\n".join(
        '          <img src="%s" alt="%s" loading="lazy">' % (i["url"], i["alt"])
        for i in HUTSMITH_IMAGES)
    return imgs, None


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G1 · Strip the template's filling instructions (they carry {{TOKEN}}).
    block = re.search(
        r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
        src, re.S)
    if not block:
        print("REFUSED. The template's instruction comment was not found where "
              "expected; the strip anchor has moved. Not guessing.")
        return 1
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero entirely: the PlotNua wordmark, the
    # headline and the supporting line. Not reworded -- removed. The page then
    # opens on the demonstration.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero:
        print("REFUSED. The introductory hero block was not found where "
              "expected. Not guessing.")
        return 1
    if "{{PROPOSITION}}" not in hero.group(0) or "{{LEDE}}" not in hero.group(0):
        print("REFUSED. The matched hero block is not the one carrying the "
              "headline tokens. Not guessing.")
        return 1
    src = src.replace(hero.group(0), "\n")

    # G2 · Move the frozen journey band BELOW the demonstration, so Hutsmith
    # is the first thing on the page rather than a band of PlotNua process.
    # The band's own markup is carried across untouched -- relocated, not
    # rewritten -- and G7 proves that byte-for-byte.
    jm = re.search(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                   src, re.S)
    if not jm:
        print("REFUSED. The frozen journey band was not found. Not guessing.")
        return 1
    journey = jm.group(0)
    src = src.replace(journey, "\n")
    why_anchor = "<!-- WHY THIS COULD BE USEFUL"
    if src.count(why_anchor) != 1:
        print("REFUSED. The 'why' section anchor is not unique. Nothing written.")
        return 1
    src = src.replace(why_anchor, journey.strip("\n") + "\n\n" + why_anchor)

    # G3 · Imagery. One list decides the state.
    imgs, held_line = imagery_block()
    if imgs is None:
        FILL["PHOTO_SLOT_LINE"] = held_line
        # The template's bold line asks the supplier for photography. Dudley
        # has already given it, so that wording is now wrong. It is not a
        # token, so it is replaced here by exact string.
        ask = "<b>Your project photography here</b>"
        if src.count(ask) != 1:
            print("REFUSED. The photo-slot heading was not found exactly once. "
                  "Nothing written.")
            return 1
        src = src.replace(ask, "<b>Hutsmith photography</b>")
    else:
        slot = re.search(r'          <div class="pn-photo-slot">.*?</div>\n',
                         src, re.S)
        if not slot:
            print("REFUSED. The held photo slot was not found, so state A "
                  "cannot replace it. Nothing written.")
            return 1
        src = src.replace(slot.group(0), imgs + "\n")
        # The slot carrying {{PHOTO_SLOT_LINE}} has just been removed, so the
        # token no longer exists and must not be in the fill set -- otherwise
        # G4's "token must be present" check refuses a correct state-A build.
        FILL.pop("PHOTO_SLOT_LINE", None)
        # The state-A credit line, as yardbox-preview.html carries it.
        credit = ('          <p class="credit-line">Images: Hutsmith, used with '
                  'written permission from Dudley Radford, %s, unmodified, and '
                  'served from Hutsmith&rsquo;s own site. If Hutsmith ask for any '
                  'of them to be changed or removed, we change or remove them.</p>\n'
                  % PERMISSION_DATE)
        foot = "<footer>\n"
        if src.count(foot) != 1:
            print("REFUSED. The footer anchor is not unique. Nothing written.")
            return 1
        src = src.replace(foot, credit + foot)

    # G4 · Fill every token.
    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src:
            print("REFUSED. Token %s is not in the template. Nothing written." % needle)
            return 1
        src = src.replace(needle, value)

    # G5 · Ireland availability, attributed to Hutsmith and dated.
    anchor = "          <ul class=\"pn-facts\">\n"
    if src.count(anchor) != 1:
        print("REFUSED. The facts list anchor is not unique. Nothing written.")
        return 1
    src = src.replace(anchor, anchor +
                      "            <li><b>Republic of Ireland &mdash; confirmed "
                      "available by Hutsmith, %s</b></li>\n" % EVIDENCE_DATE)

    # G6 · The closing section: practical, with the open items as a list.
    old_h2 = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_h2) != 1:
        print("REFUSED. The closing heading was not found exactly once. "
              "Nothing written.")
        return 1
    src = src.replace(old_h2, "<h2>What we still need to confirm</h2>")
    items = "\n".join("      <li><b>%s</b></li>" % i for i in STILL_TO_CONFIRM)
    close_anchor = '<p class="close-statement">%s</p>' % FILL["CLOSING_PROPOSITION"]
    if src.count(close_anchor) != 1:
        print("REFUSED. The closing statement anchor is not unique. "
              "Nothing written.")
        return 1
    src = src.replace(close_anchor, close_anchor +
                      '\n    <ul class="pn-facts">\n' + items + "\n    </ul>")

    # G7 · The frozen journey band must have survived the move byte-for-byte.
    if journey.strip("\n") not in src:
        print("REFUSED. The frozen journey band was altered by the move, not "
              "just relocated. Nothing written.")
        return 1
    # ...and must now sit after the demonstration.
    if src.index('class="journey"') < src.index('class="pn-stage"'):
        print("REFUSED. The journey band is still above the demonstration.")
        return 1

    # G8 · No token may survive.
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", src)
    if left:
        print("REFUSED. Unreplaced tokens survive: %s" % sorted(set(left)))
        return 1

    # G9 · If imagery is published, a live rights record must back it, and
    # every URL must be Hutsmith's own domain.
    if HUTSMITH_IMAGES:
        import json
        rec = SITE / "image-rights-records.json"
        data = json.loads(rec.read_text(encoding="utf-8"))
        live = [r for r in data["records"]
                if r.get("organisation_name") == SUPPLIER
                and not r.get("withdrawal_effective_at")]
        if not live:
            print("REFUSED. Imagery is set but no live Hutsmith record exists "
                  "in image-rights-records.json. Nothing written.")
            return 1
        for i in HUTSMITH_IMAGES:
            if not any(r in i["url"] for r in HUTSMITH_IMAGE_ROOTS):
                print("REFUSED. Image URL is not on a Hutsmith first-party "
                      "path: %s" % i["url"])
                return 1
        if "credit-line" not in src:
            print("REFUSED. Imagery is published with no credit line.")
            return 1

    # G10 · No forbidden claim.
    low = src.lower()
    hits = [p for p in FORBIDDEN if p in low]
    if hits:
        print("REFUSED. The output carries forbidden claim wording: %s" % hits)
        return 1

    # G10b · PlotNua must never be cast as a partner. Checked by proximity
    # rather than by the bare word, so Hutsmith's own construction partner
    # survives and "PlotNua has partnered with Hutsmith" does not.
    text = re.sub(r"<[^>]+>", " ", src).lower()
    for m in re.finditer(r"partner", text):
        window = text[max(0, m.start() - 90):m.start() + 90]
        if "plotnua" in window:
            print("REFUSED. PlotNua is cast as a partner: ...%s..."
                  % window.strip()[:120])
            return 1

    # G11 · No other supplier's content.
    others = ["koto", "haku", "triq", "power sheds", "powersheds", "yard box",
              "yardbox", "capsule castle", "honka", "superior pergola",
              "iglucraft", "shomera", "luka", "intumodular"]
    stray = [o for o in others if o in low]
    if stray:
        print("REFUSED. Another supplier's content is present: %s" % stray)
        return 1

    # G12a · The "asking for photography" wording must never survive, in any
    # state, now that permission is granted.
    if "Your project photography here" in src:
        print("REFUSED. The page still asks Hutsmith for photography they "
              "have already granted.")
        return 1

    # G12b · The introductory hero must be gone, and nothing may have taken
    # its place. The first substantive element after the preview bar has to be
    # the demonstration heading.
    if '<header class="hero">' in src or 'class="brand"' in src:
        print("REFUSED. The introductory hero is still present.")
        return 1
    if src.count("<h1") or src.count("<h1>"):
        print("REFUSED. An <h1> is present, so a replacement headline was "
              "introduced where the hero used to be.")
        return 1
    slog = [s for s in BANNED_SLOGANS if s in low_so_far(src)]
    if slog:
        print("REFUSED. A marketing slogan replaced the removed hero: %s" % slog)
        return 1
    bar = src.find('class="pv-bar"')
    demo = src.find("How an Irish homeowner would reach Hutsmith")
    stage = src.find('class="pn-stage"')
    if not (bar < demo < stage):
        print("REFUSED. The page no longer runs preview bar -> demonstration "
              "heading -> result.")
        return 1

    # G12 · Required strings.
    for need in REQUIRED:
        if need not in src:
            print("REFUSED. A required string is missing: %r" % need)
            return 1

    OUT.write_text(src, encoding="utf-8")
    state = "A (authorised, %d image(s))" % len(HUTSMITH_IMAGES) \
        if HUTSMITH_IMAGES else "held slot (authorised, no URL obtainable yet)"
    print("BUILT  %s" % OUT.name)
    print("  template            template-provider-led.html, variant B")
    print("  %d bytes, %d lines" % (len(src.encode()), src.count("\n") + 1))
    print("  imagery state       %s" % state)
    print("  journey band        moved below the demonstration, byte-identical")
    print("  forbidden claims    0  (%d patterns checked)" % len(FORBIDDEN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
