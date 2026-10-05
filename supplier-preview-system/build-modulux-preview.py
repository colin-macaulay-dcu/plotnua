#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE MODULUX PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
Reused, not forked. The same certified provider-led system that built the
TRIQBRIQ, Hutsmith, Honka, BIOBUILDS, Cosy Cabins and Irish Sauna Company
previews. No new template, no redesign, no new CSS.

*** WHY PROVIDER-LED, AND WHY THAT IS NOT A JUDGEMENT CALL. ***

Modulux publishes CATEGORIES, not products: garden rooms, garden offices,
modular homes, garden sheds, garden apartments, leisure pods. No model names,
no dimensions, no prices — a quote follows a site visit and a design stage.
SUPPLIER-PREVIEW-SYSTEM-V1.md §1 routes exactly that shape to Variant B, and
PlotNua's own Atlas record already reached the same conclusion independently:
ATLAS-SUPPLIER-DISCOVERY-MISSING-BATCH-14 §3.4 records "Atlas intake
justified? Not as a Product supplier. No products exist to record", and
ADDITIONAL-HOME-FOUNDATION-IMPLEMENTATION-REPORT routes Modulux as an
Independent Maker with the standing instruction "Do not manufacture
Products". This builder honours that: it invents no model, no dimension and
no price, and G8 refuses the vocabulary that would smuggle one in.

*** IMAGERY STATE C. NO IMAGERY. ***

Modulux has never been contacted. There is no correspondence, no row in
supplier-contact-register.json and no row in image-rights-records.json.
Image rights are therefore UNKNOWN, and UNKNOWN IS NOT GRANTED. Their site
carries real project photography and a gallery; none of it may be
downloaded, re-hosted, hotlinked or shown, and the page being private
changes nothing — the publish-time rights gate treats every external image
on every deployed .html as published, because a homeowner who reaches the URL
can see it. Obtaining that permission is part of what the outreach is for.
G0 refuses any attempt to fill the image list while the outcome is unknown,
and G9 proves the absence on the OUTPUT rather than trusting the input.

*** THE TRAP IN THIS SUPPLIER, AND IT IS THE PLANNING QUESTION. ***

Modulux publishes the most useful sentence PlotNua has found on any Irish
garden-building site: "A garden apartment is habitable accommodation, so
unlike many garden rooms it will normally need planning permission." And
then: "Your local authority is the only body that can confirm what is
required on your site."

That is PlotNua's own firewall, published by a supplier. The failure mode
here is not overclaiming a product — it is SOFTENING that sentence into
"planning handled, no need to worry". So this builder does something the
other builders do not: it REQUIRES both halves of the planning position to
appear on the page, in Modulux's own terms, and refuses the build if either
is missing. A guard that only forbids is not enough when the valuable thing
is a statement rather than its absence.

Run: python3 build-modulux-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/modulux-preview.html")
       if STAGE else SITE / "modulux-preview.html")

SUPPLIER = "Modulux"
EVIDENCE_DATE = "5 October 2026"
SUPPLIER_SITE = "https://www.modulux.ie/"
APARTMENT_URL = SUPPLIER_SITE + "garden-apartments.html"
HOMES_URL = SUPPLIER_SITE + "modular-homes-ireland.html"
CREDIT = "© Modulux"

# IMAGERY STATE C. Empty by governance, not by oversight. G0 enforces it.
MODULUX_IMAGES = []

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT ───────────────────────────────────
# Phrases, not bare words. Modulux publishes a great deal about HOW they
# work and almost nothing that is a number, so this list is built around the
# four kinds of number a reader would most want and the site does not give.
BANNED_CLAIM_PHRASES = [
    # MONEY. Not one figure is published anywhere on the site.
    "&euro;", "€", "prices from", "starting at", "from only",
    "fixed price", "ballpark of", "typical cost",
    # PRODUCTS AND DIMENSIONS. Categories only. The standing Atlas
    # instruction is "Do not manufacture Products", and a model name or a
    # floor area is how one gets manufactured by accident.
    "m&sup2;", "sq m", "square metres", "square meters",
    "off the shelf", "catalogue of", "model range", "our models",
    # PLANNING. Their own position is conditional in both directions and the
    # local authority decides. PlotNua must not resolve it either way.
    "planning exempt", "no planning permission", "does not need planning",
    "planning not required", "exempted development", "planning approved",
    "we guarantee planning", "planning guaranteed",
    # TIME. "It depends on the size and the specification" is the whole of
    # what the site says about duration.
    "lead time", "weeks from", "within weeks", "turnaround",
    # ASSURANCES. Not established anywhere on the site.
    "warranty", "year guarantee", "we guarantee", "certified",
    "certification", "agrément", "agrement", "nsai",
]

# ── TONE. FOUNDER CORRECTION, 5 OCTOBER 2026. ─────────────────────────────
# PlotNua's role is DISCOVER -> UNDERSTAND -> NARROW -> DECIDE. It is never
# CUSTOMER IS WRONG -> PLOTNUA CORRECTS THEM. A supplier-facing page that
# sells PlotNua by making homeowners sound naive, confused or time-wasting is
# selling the wrong thing, and it would read as perfectly competent copy while
# doing it — which is why this is a guard and not a style note.
#
# PHRASES, NOT THE WORD "WRONG". This page legitimately asks Modulux to tell
# us if an editorial decision of OURS is the wrong call, and a bare-word ban
# would gag that while catching nothing it was aimed at.
BANNED_TONE_PHRASES = [
    "the wrong one", "ask for the wrong", "start at the wrong",
    "picks the wrong", "thought it through", "think it through properly",
    "don&rsquo;t know what they need", "do not know what they need",
    "confused", "naive", "ill-informed",
    "waste your time", "wasting your time", "waste of your time",
    "we know better", "put them right", "set them straight",
]

# Modulux's own words, both halves, and the build fails without them.
PLANNING_MUST_SAY = [
    ("will normally need planning permission",
     "Modulux's own distinction between a garden room and habitable "
     "accommodation. Dropping it turns their honesty into PlotNua's silence."),
    ("local authority is the only body",
     "Modulux's own caveat, and PlotNua's own firewall. A page that says "
     "planning is handled without saying who actually decides is worse than "
     "a page that says nothing."),
]

# The absence of a price must be VISIBLE, not merely un-stated. A reader who
# does not notice that no price exists will assume one was omitted.
PRICE_MUST_SAY = [
    "quoted per project",
    "no price list",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE INSERTED SECTION ───────────────────────────────────────────────────
# Follows the Irish Sauna Company precedent exactly: ONE section, placed
# between the demonstration and the frozen journey band, built only from
# markup the template already styles — <section>, h2, h3, p and .pn-open.
# No new CSS, no new component.
#
# WHAT IT CARRIES, and why this rather than a product list: the single most
# interesting thing about Modulux to PlotNua is that one supplier covers four
# genuinely different answers to the same need, which gives PlotNua real range
# to explore with a homeowner before anything is decided.
#
# TONE, founder correction of 5 October 2026. PlotNua's role is
# DISCOVER -> UNDERSTAND -> NARROW -> DECIDE. It is never
# CUSTOMER IS WRONG -> PLOTNUA CORRECTS THEM. The first version of this
# section opened "most people start at the wrong one", which made the
# homeowner the problem and PlotNua the fix. That framing is retired and must
# not come back: see G12.
LADDER = """<!-- THE LADDER — why this supplier is unusual to PlotNua. Four published
     categories, each answering a different need, in Modulux's own words. Not
     a catalogue: no model, dimension or price appears here because none is
     published. -->
<section>
  <h2>Different possibilities for different needs</h2>
  <p>A homeowner may know they need more space without yet knowing what form
     that space should take. A garden room, a dedicated office, a
     self-contained garden apartment and a modular home can answer very
     different needs. Modulux offers all four, giving PlotNua a useful range of
     possibilities to explore with the homeowner before they decide what to
     pursue.</p>
  <div class="pn-open">
    <ul>
      <li><b>A garden room.</b> Outdoor living space, plastered inside like
          the rest of the house and insulated to Building Regulations, so it
          works in February as well as July.</li>
      <li><b>A garden office.</b> The same shell with a comprehensive
          electrics package and wood laminate flooring, for someone who needs
          to work away from the kitchen table.</li>
      <li><b>A garden apartment.</b> Not a bigger garden room &mdash; a
          self-contained place to live, with bedrooms, a kitchen, a bathroom
          and its own front door, connected to the mains.</li>
      <li><b>A modular home.</b> A complete home built to the current
          building regulations for living accommodation, finished throughout
          and ready to move into.</li>
    </ul>
  </div>
  <h2>Three things we would ask before publishing</h2>
  <p>These are the three things we&rsquo;d like to check with you before the
     page goes live.</p>
  <div class="pn-open">
    <ul>
      <li><b>Where the line falls.</b> Your site says a garden room is often
          not a planning matter and a garden apartment normally is. For
          someone who wants a bedroom in the garden but not a kitchen, which
          side of that line do they usually end up on &mdash; and is that a
          conversation you&rsquo;d rather have at the site visit than on a
          web page?</li>
      <li><b>What a homeowner should have ready.</b> The visit and measure is
          free and access is the first thing you check. Is there anything
          worth having to hand before that call &mdash; a rough size, a photo,
          where the house services run &mdash; that would make the first
          conversation more useful to you?</li>
      <li><b>How much of the range to show.</b> You also build insulated
          garden sheds and leisure pods. We&rsquo;ve kept this page to the
          four above because those are the ones a homeowner reaches through
          PlotNua, but tell us if that&rsquo;s the wrong call.</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Every statement traces to modulux.ie, read live 5 October 2026.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Modulux",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your own pages publish. They would first "
                 "discover a possibility for their property, work through "
                 "whether it fits and what to check, and only then reach "
                 "suppliers &mdash; so by the time this screen appears the "
                 "thinking has already happened.",


    "OFFER_NAME": "Garden apartment &mdash; one or two bedrooms",
    "VERIFIED_PRICE": "Quoted per project",
    "VERIFIED_PRICE_BASIS": "Modulux publish no price list. The visit and "
                            "measure is free of charge, and a written quote "
                            "against a written specification follows the "
                            "design stage.",

    "VERIFIED_FACT_1_LABEL": "What it is",
    "VERIFIED_FACT_1_VALUE": "A self-contained place to live &mdash; "
                             "bedrooms, a kitchen, a bathroom and its own "
                             "front door, connected to the mains",
    "VERIFIED_FACT_2_LABEL": "Scale",
    "VERIFIED_FACT_2_VALUE": "One or two bedrooms. The layout follows the "
                             "site rather than a catalogue, and is set out on "
                             "a drawing before anything is ordered",
    "VERIFIED_FACT_3": "Built to the current building regulations for living "
                       "accommodation, insulated floor, walls and roof, and "
                       "professionally plastered and painted throughout",
    "VERIFIED_FACT_4": "Foundations, heating, lighting, painting and the "
                       "mains utility connections back to the house are part "
                       "of the work",
    "VERIFIED_FACT_5": "Design, building regulations, planning permission and "
                       "on-site construction handled as one project, with "
                       "Modulux as the single point of contact",

    # THE ONE HONEST LINE. It carries both required statements: that no price
    # is published, and Modulux's own planning position in both halves.
    "THINGS_TO_CHECK": "there is no figure on this page because Modulux "
                       "publish no price list &mdash; work is quoted per "
                       "project after the visit and the design stage. And "
                       "Modulux&rsquo;s own planning position belongs here "
                       "rather than in small print: a garden apartment is "
                       "habitable accommodation, so unlike many garden rooms "
                       "it will normally need planning permission. Modulux "
                       "handle that application as part of the project, and "
                       "say plainly that your local authority is the only "
                       "body that can confirm what is required on your site.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. The journey asks for an
    # Eircode and simplifyLocalityDisplay() reduces it to exactly this. It
    # asks nothing about garden size, access, boundaries or services, and on
    # this supplier the temptation is unusually strong because all four
    # genuinely decide the job. None of them may be implied.
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "Shown for a homeowner in Co. Meath, from the location "
                       "they gave us. We don&rsquo;t ask them about the size "
                       "of the garden, the access or where the services run "
                       "&mdash; so we wouldn&rsquo;t pretend to know. Those "
                       "stay as things for your site visit.",

    "WHY_1_LABEL": "A MORE CONSIDERED STARTING POINT",
    "WHY_1_TEXT": "You offer several different responses to the need for more "
                  "space. PlotNua helps the homeowner explore what each one "
                  "could mean for their property, so when they reach Modulux "
                  "they have a clearer sense of what they want to "
                  "investigate.",
    "WHY_2_LABEL": "THE PLANNING QUESTION, ALREADY RAISED",
    "WHY_2_TEXT": "Your site draws the line between a garden room and "
                  "habitable accommodation more clearly than anything else we "
                  "have read in this market. We show it rather than bury it, "
                  "so the planning question is already part of how the "
                  "homeowner is thinking by the time they contact you.",
    # TONE, same correction. The first version sold PlotNua by contrast with
    # how homeowners otherwise behave -- "not having typed a category into a
    # search box", "a different kind of enquiry from a directory click". That
    # makes ordinary behaviour the lesser thing and PlotNua the remedy, which
    # is the same framing as the ladder heading in a quieter register. The
    # replacement describes the state of the enquiry, not the shortcomings of
    # the person.
    "WHY_3_LABEL": "ARRIVING WITH A DEVELOPED IDEA",
    "WHY_3_TEXT": "By the time a homeowner reaches you through PlotNua, they "
                  "have looked at what their own property could take and "
                  "worked out that a separate building is what they want. "
                  "They arrive with a developed idea rather than an open "
                  "question, and that is the kind of enquiry we are trying to "
                  "send you.",

    "CLOSING_PROPOSITION": "Does this represent Modulux accurately for an "
                           "Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, tell us and we&rsquo;ll correct it before "
                       "anything is published.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    if MODULUX_IMAGES:
        die("Modulux imagery was added to this builder, but Modulux has "
            "never been contacted and no permission exists. UNKNOWN is not "
            "GRANTED, and the publish-time rights gate refuses external "
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
    # demonstration: the first thing Modulux sees is their own result.
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
    # the ladder section between them. ONE anchored edit.
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
                      LADDER + "\n" + journey.strip("\n")
                      + "\n\n" + why_anchor)

    # G3 · IMAGERY STATE C. The held panel is relabelled so it reads as a
    # deliberate position rather than a missing asset.
    # G3 · THE IMAGE POSITION CARRIES NO COPY (certified, 5 Oct
    # 2026). The relabel that stood here rewrote the slot heading into a
    # sentence about photography. There is no heading and no sentence
    # now; the rights gate is unchanged and still fails closed.

    # G3c · ATTRIBUTION. Every statement is their published information, so
    # the page says where it came from and links back.
    attribution = (
        '          <p class="credit-line">Everything on this page is published '
        'by %s and was read from '
        '<a href="%s" rel="noopener">your garden apartments page</a>, '
        '<a href="%s" rel="noopener">your modular homes page</a> and '
        '<a href="%s" rel="noopener">modulux.ie</a> on %s. '
        'No %s photography is used anywhere on this page. '
        '%s'
        '</p>\n'
        % (SUPPLIER, APARTMENT_URL, HOMES_URL, SUPPLIER_SITE, EVIDENCE_DATE,
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

    # G5 · PRIVACY. Non-negotiable, and doubly so here: nothing was granted
    # and the supplier does not yet know the page exists.
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

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Irish Sauna", "Harvia", "OGNYX", "TankTribe",
                  "ModHome", "Delta Homes", "Cabins4U"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support: %r. Modulux publish categories and a process, "
                "not models, dimensions, prices, timescales or assurances."
                % phrase)

    # G8b · THE PLANNING POSITION MUST BE STATED, both halves. This is the
    # one guard this builder has that the others do not, and the reason is in
    # the module docstring: the valuable thing here is a statement, so the
    # guard has to require it rather than merely forbid its opposite.
    for needle, why in PLANNING_MUST_SAY:
        if needle not in low:
            die("the page is missing Modulux's own planning wording (%r). %s"
                % (needle, why))

    # G8c · AND THE ABSENCE OF A PRICE MUST BE VISIBLE.
    for needle in PRICE_MUST_SAY:
        if needle not in low:
            die("the page does not make the absence of a published price "
                "explicit (%r). A reader who does not notice that no price "
                "exists will assume PlotNua left it out." % needle)

    # G9 · NO IMAGERY, PROVEN ON THE OUTPUT and not merely on the input list.
    for pattern, what in (
            (r'<img[^>]+src="https?://', "an external <img>"),
            (r'<source[^>]+srcset="https?://', "an external <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"[^>]+content="https?://', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s. No external imagery may appear "
                "on this preview: Modulux has granted nothing." % what)
    # A REAL LINK TO THE SITE ROOT, not the word in a sentence and not merely
    # a deep link that happens to share the domain.
    #
    # THE CLOSING QUOTE IS LOAD-BEARING. The first version of this check was a
    # prefix test, 'href="https://www.modulux.ie', which the garden-apartments
    # and modular-homes deep links both satisfy — so removing the root link
    # entirely still passed, and the capability proof caught it. A guard whose
    # message says "links back to the site" has to test that, not "mentions
    # the domain somewhere".
    if 'href="%s"' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s itself. Even with no imagery, "
            "the supplier's own site is where everything came from, a deep "
            "link to one page is not the same thing, and a mention in prose "
            "is not a link." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the %r credit." % CREDIT)

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL IMPLICATION.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed", "commission",
                 "exclusive"):
        if word in low:
            die("the page implies a relationship that does not exist: " + word)

    # G12 · TONE. The homeowner is never the problem PlotNua solves.
    for phrase in BANNED_TONE_PHRASES:
        if phrase in low:
            die("the page makes the homeowner sound naive, confused or "
                "time-wasting: %r. PlotNua's role is discover, understand, "
                "narrow, decide — not correcting bad customer decisions. "
                "Founder correction, 5 October 2026." % phrase)
    # And the replacement framing must be PRESENT, not merely the old one
    # absent: deleting the sentence would satisfy a forbid-only guard.
    if "different possibilities for different needs" not in low:
        die("the ladder section has lost its approved heading. Removing the "
            "framing is not the same as correcting it.")

    # G11 · THE PREVIEW MUST SAY WHAT IT IS.
    if "illustrative preview" not in low:
        die("the page does not identify itself as an illustrative preview.")
    if "before anything goes live" not in low:
        die("the pre-publication review ask is missing from the page.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("MODULUX PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    16 guards passed")
    print("  ok    0 external images — imagery state C, never contacted")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no price, model, dimension, timescale or assurance claim")
    print("  ok    planning position stated in both halves, in their words")
    print("  ok    the absence of a published price is explicit")
    print("  ok    tone: the homeowner is never the problem PlotNua solves")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
