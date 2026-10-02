#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE COSY CABINS PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
Reused, not forked. This is the same certified provider-led preview system
that built the TRIQBRIQ, Hutsmith, Honka and BIOBUILDS previews; the only
new code here is the second-possibility section, because no previous
supplier needed to be shown across two different homeowner outcomes.

WHY PROVIDER-LED. Cosy Cabins has genuine leverage in more than one PlotNua
journey -- garden room / garden office, creative studio, and wellness /
garden retreat. A product-led preview would have to pick one and would
misrepresent the company. SUPPLIER-PREVIEW-SYSTEM-V1 §1 therefore selects
variant B.

*** THE IMAGERY DECISION, AND WHY THERE IS NONE. ***

Bruno replied "PREVIEW please" on 2 October 2026. The outreach he was
answering offered him two replies: "YES" for permission to feature Cosy
Cabins and use selected website imagery, or "PREVIEW" to see the page
first. He chose PREVIEW. He did not say YES.

So Atlas holds Permission Outcome "Unknown -- Awaiting Reply", and that is
correct. UNKNOWN is not GRANTED.

This was tested against the real gate rather than assumed. A fixture page
carrying two cosycabins.ie images, with all five robots directives, the
credit and the link back, was run through
atlas-tools/validate-image-rights.js --scan-html:

    0 publishable · 2 refused · GATE FAILED

and again with an HONEST manifest row added, carrying the outcome Atlas
actually holds and the supplier's own Wix prefix /media/9ba815_:

    REFUSE ... the permission outcome is "Unknown — Awaiting Reply".
    NOT A GRANT

The gate has no page-level exemption and does not consult noindex: every
external image on every deployed .html is treated as published, because a
homeowner who reaches the URL can see it. The ONLY way to pass imagery
would be to write a live-grant outcome into the manifest for a supplier who
has not granted one -- which is converting PREVIEW into GRANTED, and is
exactly what the founder's instruction forbids.

THEREFORE: IMAGERY STATE C. The page carries no Cosy Cabins imagery and the
held panel says so plainly, in a way that is useful to Bruno rather than
apologetic -- it tells him his pictures are not being used until he says
they can be. COSY_CABINS_IMAGES stays empty, and G0 refuses any attempt to
fill it while the permission outcome is unknown.

Run: python3 build-cosy-cabins-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/cosy-cabins-preview.html") if STAGE
       else SITE / "cosy-cabins-preview.html")

SUPPLIER = "Cosy Cabins"
SUPPLIER_LEGAL = "Cosy Cabins Limited"
EVIDENCE_DATE = "2 October 2026"
SUPPLIER_SITE = "https://www.cosycabins.ie/"
CREDIT = "© Cosy Cabins Limited"

# IMAGERY STATE C. Empty by governance, not by oversight. See the module
# docstring. G0 enforces it.
COSY_CABINS_IMAGES = []

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT ───────────────────────────────────
# These are phrases, not bare words, and that distinction is load-bearing.
# "insulation" MUST be sayable: insulation is a real, separately priced
# option on the garden room and naming its price is one of the most useful
# honest facts on the page. What may not be said is that the product IS
# insulated. A guard that banned the bare word would force the page to hide
# the very thing a homeowner needs to know.
BANNED_CLAIM_PHRASES = [
    "fully insulated", "insulated garden room", "is insulated",
    "well insulated", "u-value", "u value",
    "planning exempt", "exempt from planning", "no planning permission",
    "planning permission is not", "does not need planning",
    "lead time", "lead-time", "weeks from order", "delivery time",
    "warranty", "guaranteed for", "year guarantee",
    "nationwide", "across ireland", "anywhere in ireland",
    "certified", "certification",
    "year-round use", "year round use",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE SECOND POSSIBILITY ─────────────────────────────────────────────────
# A DISTINCT SECTION, NOT A SECOND PRODUCT IN THE SAME HERO. Garden rooms
# and saunas are different homeowner outcomes reached from different starting
# points, and collapsing them into one "range" would be the single easiest
# way to misrepresent this supplier. It is deliberately shorter than the
# demonstration above: the point is to show the cross-category reach, not to
# run the whole result twice.
#
# WELLNESS LEADS, GARDEN ROOM FOLLOWS. Founder-reframed 2026-10-02. Bruno
# replied to the HOME WELLNESS outreach -- outdoor saunas, garden retreat --
# so the sauna is the result he is shown first and the garden room is the
# extra reach he did not ask about. The earlier build had these the other way
# round, which answered a question he had not asked.
#
# Markup reuses the template's existing classes only -- <section>, h2, and
# ul.pn-facts -- so it inherits the page's type, spacing and responsive
# behaviour and introduces no new CSS.
SECOND_POSSIBILITY = """<!-- THE SECOND POSSIBILITY — the cross-category reach, after the wellness
     result the supplier was actually contacted about. Keep it shorter than
     the demonstration above, and keep the two categories separate. Every
     figure is first-party.

     SUPPLIER-FACING LANGUAGE, founder-set 2026-10-02. Plain paragraphs, not
     a label/value fact list: the earlier version invented labels such as
     "Structure" and "Priced separately" that the supplier never used. The
     two open points are asked as QUESTIONS, in the words a person would
     use, with no internal governance vocabulary.

     Markup is <section>, h2, h3, p, b, br and .pn-open — all already in the
     template's stylesheet, so this introduces no new CSS. .pn-open is the
     template's own open-questions component, which renders each item with a
     dash and is exactly what these two are. -->
<section>
  <h2>Another way Cosy Cabins could appear</h2>
  <p>PlotNua first reached you through your sauna range, but Cosy Cabins
     could also appear in a separate garden-room journey.</p>
  <p>A homeowner looking for a home office, studio or extra space in the
     garden may arrive through a completely different route, and your
     garden-room range gives us another relevant way to introduce Cosy
     Cabins.</p>
  <p><b>Athlone Garden Room 4.5m &times; 2.5m</b><br>From &euro;10,940 inc. VAT</p>
  <p>45mm solid timber walls, 19mm tongue-and-groove floor and roof boards,
     Scandinavian spruce, and double-glazed tilt-and-turn windows and
     doors.</p>
  <p>Construction by your team is listed separately at &euro;1,900, along
     with a number of other options and upgrades.</p>
  <h3>A couple of things we would like to confirm</h3>
  <p>Before anything goes in front of homeowners, could you clarify:</p>
  <div class="pn-open">
    <ul>
      <li>Is roof and wall insulation included as standard, or is it an
          optional upgrade?</li>
      <li>The page says &ldquo;Fully Built By Our Team&rdquo;, while
          construction is also listed as a &euro;1,900 extra. How should we
          describe that accurately?</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Voice: plain, direct, the way Colin would put it to Bruno. Every figure
# traces to cosycabins.ie read live on 2 October 2026. No claim about
# insulation as a property, planning, lead times, warranties or nationwide
# coverage -- those are either not published or contradicted on the
# supplier's own site, and the contradictions go to Bruno as questions.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Cosy Cabins",
    # The template already carries its own "Illustrative preview" tag beside
    # the heading, so the lede does not repeat the words. G11 guards that tag
    # rather than this sentence; the proof found the duplication by removing
    # the phrase here and still building, which is what a guard with two
    # satisfying sources looks like.
    "DEMO_LEDE": "A shortened "
                 "example of what a homeowner would see, built only from what "
                 "Cosy Cabins publishes. They would first discover a "
                 "possibility for their property, work through whether it "
                 "fits and what to check, and only then reach suppliers. "
                 "By the time this screen appears, that thinking has already "
                 "happened.",

    # IMAGERY STATE C. This line is the honest version of an empty panel.
    "PHOTO_SLOT_LINE": "We have not used any Cosy Cabins photography on this "
                       "page. You asked to see the preview before anything is "
                       "published, so your images stay yours until you tell "
                       "us otherwise. This is where they would sit, credited "
                       "to Cosy Cabins and linked back to cosycabins.ie.",

    # THE WELLNESS RESULT LEADS. Bruno answered the home-wellness outreach,
    # so the framed example is the sauna. The garden room moved to the
    # second-possibility section below.
    "OFFER_NAME": "Sauna 2m",
    "VERIFIED_PRICE": "from &euro;4,800",
    "VERIFIED_PRICE_BASIS": "as published by Cosy Cabins, inc. VAT, with "
                            "assembly by your own team inside that figure. A "
                            "&ldquo;from&rdquo; price for the smallest of six "
                            "sizes.",

    "VERIFIED_FACT_1_LABEL": "Size",
    "VERIFIED_FACT_1_VALUE": "2m total length, 1.7m sauna length, "
                             "2.10m diameter",
    "VERIFIED_FACT_2_LABEL": "Published for",
    "VERIFIED_FACT_2_VALUE": "a group of 2&ndash;4 people",
    "VERIFIED_FACT_3": "Electric Harvia 9kW stove with 20&ndash;30kg of sauna "
                       "stones",
    "VERIFIED_FACT_4": "Black alder benches, brown tempered glass door and a "
                       "bitumen shingle roof",
    "VERIFIED_FACT_5": "Assembly by Cosy Cabins is included in the published "
                       "figure",

    # ONE HONEST LINE, and the most useful sentence on the page. What sits
    # outside the headline figure is the difference between a listing and a
    # decision.
    "THINGS_TO_CHECK": "assembly is inside this figure, which is not true of "
                       "every garden building. What sits outside it: delivery "
                       "is free within 50km of Cavan Town and &euro;1.50 per "
                       "km beyond, and a solid-fuel stove (+&euro;600), half "
                       "or full panoramic glass (+&euro;600 or +&euro;900) "
                       "and a trailer (+&euro;3,000) are priced separately. "
                       "The range runs to six sizes, &euro;4,800 to "
                       "&euro;8,800 inc. VAT.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. The journey asks for an
    # Eircode and simplifyLocalityDisplay() reduces it to exactly this. It
    # asks nothing about site, access, orientation or ground conditions, so
    # nothing else on this page may be personalised however well it would
    # read.
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "Shown for a homeowner in Co. Meath, from the location "
                       "they gave us. Whether they fall inside your 50km "
                       "delivery radius is the kind of thing we would put in "
                       "front of them rather than leave to the first phone "
                       "call.",

    "WHY_1_LABEL": "THEY ARRIVE HAVING THOUGHT ABOUT IT",
    "WHY_1_TEXT": "A homeowner reaches this screen after working out what "
                  "kind of space they are actually after and roughly what it "
                  "costs. You are not starting the conversation from nothing.",
    "WHY_2_LABEL": "YOUR FACTS, IN CONTEXT",
    "WHY_2_TEXT": "Your published sizes and prices sit inside the homeowner&rsquo;s "
                  "own decision rather than in a directory entry, next to "
                  "what they still need to check. The product facts shown "
                  "here are drawn from your published information.",
    "WHY_3_LABEL": "MORE THAN ONE WAY IN",
    "WHY_3_TEXT": "We came to you about home wellness, but Cosy Cabins can "
                  "appear in the garden-room and studio journeys as well. "
                  "Most suppliers we look at only fit one, so you would be "
                  "reachable by people arriving from three different "
                  "starting points rather than the one we contacted you "
                  "about.",

    "CLOSING_PROPOSITION": "Does this represent Cosy Cabins accurately for an "
                           "Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, let us know and we&rsquo;ll correct it "
                       "before publication.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    # This is the guard that makes the docstring's reasoning enforceable
    # rather than a note somebody can ignore in six weeks.
    if COSY_CABINS_IMAGES:
        die("Cosy Cabins imagery was added to this builder, but the Atlas "
            "Permission Outcome is 'Unknown — Awaiting Reply'. Bruno "
            "replied PREVIEW, not YES. UNKNOWN is not GRANTED, and the "
            "publish-time rights gate refuses these images on any deployed "
            "page. Get written permission and a manifest row first.")

    # G1 · Strip the template's filling instructions (they carry {{TOKEN}}).
    block = re.search(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                      src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero so the page opens on the
    # demonstration: the first thing Bruno sees is his own result.
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
    # the second-possibility section between them. ONE anchored edit, so the
    # page order is: demonstration, sauna, journey, why, close.
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
                      SECOND_POSSIBILITY + "\n" + journey.strip("\n")
                      + "\n\n" + why_anchor)

    # G3 · IMAGERY STATE C. The held panel is relabelled so it reads as a
    # deliberate position rather than a missing asset.
    ask = "<b>Your project photography here</b>"
    if src.count(ask) != 1:
        die("the photo-slot heading was not found exactly once. Nothing "
            "written.")
    src = src.replace(ask, "<b>Your imagery is not used on this page</b>")

    # G3c · ATTRIBUTION. Every figure on this page is Cosy Cabins' own
    # published information, so the page says where it came from and links
    # back, exactly as it would if imagery were being used. The same line
    # states that no imagery is used, so the rights position is readable on
    # the page itself rather than only in Atlas.
    attribution = (
        '          <p class="credit-line">Every figure on this page is '
        'published by %s and was read from '
        '<a href="%sgarden-rooms/athlone-garden-room-4.5m-x-2.5m" '
        'rel="noopener">their Athlone garden room page</a> and '
        '<a href="%ssaunas/sauna-2m" rel="noopener">their Sauna 2m page</a> '
        'on %s. No Cosy Cabins imagery is used anywhere on this page. '
        '%s &middot; <a href="%s" rel="noopener">cosycabins.ie</a></p>\n'
        % (SUPPLIER_LEGAL, SUPPLIER_SITE, SUPPLIER_SITE, EVIDENCE_DATE,
           CREDIT, SUPPLIER_SITE))
    foot = "<footer>\n"
    if src.count(foot) != 1:
        die("the footer anchor is not unique. Nothing written.")
    src = src.replace(foot, attribution + foot)

    # G3b · THE CLOSING HEADING is hardcoded in the template, not a token,
    # so it is replaced by exact string. The section is the pre-publication
    # review ask, and the heading has to say so or the two sentences under
    # it read as a change of subject.
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

    # G5 · PRIVACY. Non-negotiable on a supplier preview, and doubly so here:
    # this supplier has granted nothing at all.
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
    low = visible.lower()

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Hutsmith", "Yard Box", "Power Sheds", "TRIQ", "BIOBUILDS",
                  "Superior Pergola", "Honka", "MyCabin", "Dudley", "Mateus"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM. Cosy Cabins' own site contradicts itself on
    # insulation, on installation and on nationwide delivery. PlotNua does
    # not resolve a supplier's contradiction by picking the flattering side.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support: %r. Either it is unpublished, or the "
                "supplier's own site contradicts it." % phrase)

    # G9 · NO IMAGERY, PROVEN ON THE OUTPUT and not merely on the input list.
    # G0 checks the builder's intent; this checks the artefact. An image that
    # arrived through the template, a stray CSS url() or an og:image would
    # all fail the rights gate at publish time, so they fail here first.
    for pattern, what in (
            (r'<img[^>]+src="https?://', "an external <img>"),
            (r'<source[^>]+srcset="https?://', "an external <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"[^>]+content="https?://', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s. No external imagery may appear "
                "on this preview while permission is unknown." % what)
    # A REAL LINK, not the word in a sentence. The first draft of this check
    # tested for the bare string "cosycabins.ie", which the held-panel prose
    # satisfies on its own -- so the page could have shipped citing the
    # supplier's site in text while linking nowhere.
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s. Even with no imagery, the "
            "supplier's own site is where every figure came from, and a "
            "mention in prose is not a link." % SUPPLIER_SITE)
    if src.count(CREDIT) < 1:
        die("the attribution line is missing the %r credit." % CREDIT)

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL IMPLICATION. Nothing
    # has been agreed with Cosy Cabins and the page must not suggest it has.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed", "commission",
                 "exclusive"):
        if word in low:
            die("the page implies a relationship that does not exist: " + word)

    # G11 · THE PREVIEW MUST SAY WHAT IT IS. An illustrative mock-up that
    # does not announce itself is the thing most likely to be mistaken for a
    # live listing by the one person whose judgement this page exists to get.
    if "illustrative preview" not in low:
        die("the page does not identify itself as an illustrative preview.")
    if "before anything goes live" not in low:
        die("the pre-publication review ask is missing from the page.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("COSY CABINS PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    12 guards passed")
    print("  ok    0 external images — imagery state C, permission unknown")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no insulation, planning, lead-time, warranty or "
          "nationwide claim")
    print("  ok    garden room and sauna kept as separate possibilities")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
