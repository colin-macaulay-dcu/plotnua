#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNDED BUILDER — THE BIOBUILDS PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
VARIANT:  B, provider-led

WHY PROVIDER-LED, with two priced products in Atlas. BIOBUILDS publish a
range -- Nest 24, Wanderlust 48, Serenity 95, Sanctuary 142, Bloom 190 --
priced per square metre and configured to the buyer's size. Atlas carries two
of them as products. That is a provider relationship with a catalogue, not
one product carrying the whole conversation, so SUPPLIER-PREVIEW-SYSTEM-V1 §1
puts it in variant B. Wanderlust 48 leads the demonstration because it is the
entry model and the one an Irish homeowner is most likely to meet first.

FIRST-PARTY EVIDENCE, read 2 October 2026:
    https://www.biobuilds.com/ie        Ireland landing page
    https://www.biobuilds.com/catalog   model sizes and turnkey prices
    https://www.biobuilds.com/design    configurator, €/m² basis, inclusions

ATLAS:
    ORG-000153   BIOBUILDS                 recjNpnrIr2KT5BWh
    PROD-000523  BIOBUILDS Wanderlust      recIBexeX8au55mVn   €105,000 / €163,000
    PROD-000524  BIOBUILDS Serenity        reczLG8Iw4k7TY2Nq   €191,000 / €306,000
    PROD-001172  BIOBUILDS Nest 24         rec30WJRNrhVjDtkf   €74,300 / €101,100
    PROD-001215  BIOBUILDS Sanctuary       recV5stNWzbeL1L7A   €278,000 / €444,000
    PROD-001216  BIOBUILDS Bloom           recjdCtvV26NtbNA0   €354,000 / €572,000

    ALL FIVE MODELS, 16 October 2026. The preview now carries the whole Irish
    range so Mateus can confirm all five before anything is published. Every
    figure in RANGE below was re-read from BIOBUILDS' own Irish pages on
    16 October 2026 (biobuilds.com/ie/design#<model>, the rendered model
    panel; biobuilds.com/ie/catalog and /ie/faq for the per-floorplan area
    ranges and the inclusion wording). Evidence is kept outside the repo in
    ~/atlas-research/biobuilds-1016/. A value the supplier does not publish
    is written as None and the page shows "To be confirmed by BIOBUILDS";
    nothing is inferred.

    SUPPLIER CORRECTION, 11 October 2026. BIOBUILDS asked for the prices to be
    replaced before publication. Two finishes per model now, both Irish prices
    including 23% VAT, with transport and assembly on prepared ground screws
    included. The superseded single prices and the €2,400/m² fully-fitted
    figure are withdrawn. Equipment inclusions are aligned to the supplier's
    published Turnkey specification (biobuilds.com/ie/turnkey, read
    11 October 2026): kitchen furniture and appliances are NOT included.

── IMAGERY, AND THE ONE THING THAT MAKES THIS BUILD DIFFERENT ─────────────
The 34 governed BIOBUILDS assets are Publication Status "Reference Only —
Not Published", and BIOBUILDS is deliberately ABSENT from
image-rights-manifest.json, because the grant is conditional on BIOBUILDS
reviewing the listing before it goes live.

atlas-tools/validate-image-rights.js marks EVERY external image on EVERY
.html file in the deployed tree as publication_status 'Published' -- its own
comment reads "a homeowner can see it" -- and refuses any whose organisation
has no manifest row. There is no page-level exemption and noindex is not
consulted. So a state-A build of this page CANNOT be deployed while the
manifest row is absent. That is the gate working, not failing.

This builder therefore writes wherever it is told and never decides to
deploy:

    (default)  -> repo root, the certified location, ready to commit
    --stage    -> a staging path outside the repo, which changes nothing in
                  the deployed tree and leaves the publication gate green

Run with --stage until the founder has decided whether the manifest row is
added. Nothing here changes Atlas, the manifest, or any Publication Status.

── MEDIUM ────────────────────────────────────────────────────────────────
BIOBUILDS do not state whether their model imagery is photography or
architectural visualisation, and PlotNua has not established it. Guard G8
refuses the build if any of the banned medium words reaches the page.

Run: python3 build-biobuilds-preview.py [--stage]
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/biobuilds-preview.html") if STAGE
       else SITE / "biobuilds-preview.html")

SUPPLIER = "BIOBUILDS"
EVIDENCE_DATE = "2 October 2026"
REVISION_DATE = "16 October 2026"
RANGE_READ_DATE = "16 October 2026"
PERMISSION_DATE = "2 October 2026"
PERMITTED_PREFIX = "https://www.biobuilds.com/"
CREDIT = "© BIOBUILDS"
# SUPPLIER CORRECTION, 11 October 2026. BIOBUILDS asked that catalogue images
# be captioned "BIOBUILDS model imagery". The rights grant separately REQUIRES
# the credit "© BIOBUILDS", and the G-guard below counts it, so the caption
# does not replace the credit: both appear in the one overlay band, and
# data-credit carries the same string so a gallery swap cannot drop either.
IMAGE_CAPTION = "BIOBUILDS model imagery"
CAPTION_CREDIT = IMAGE_CAPTION + " &middot; " + CREDIT

# MEDIUM IS NOT ESTABLISHED. Every one of these would assert something about
# the imagery that BIOBUILDS has not said and PlotNua has not verified.
BANNED_MEDIUM_WORDS = [
    "photograph", "photography", "photo ", "completed build", "completed home",
    "finished installation", "CGI", "render", "rendering", "visualisation",
    "visualization",
]

# ── IMAGERY ────────────────────────────────────────────────────────────────
# A REPRESENTATIVE SUBSET, NOT ALL 34. Eight, in the founder's priority
# order: Wanderlust first because it leads the demonstration, Serenity
# second because it is the other Atlas product, then the two that show how
# the thing is actually made. The rest of the governed set stays in Atlas.
#
# Alt text describes what is visible and nothing about the medium.
BIOBUILDS_IMAGES = [
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "wanderlust-catalog.3-furbv0o-vtc.jpg",
     "alt": "Wanderlust 48 by BIOBUILDS: a dark timber-clad single-storey "
            "home on a deck at dusk, with outdoor seating"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "wanderlust-48-int-catalog.0d9n8s-fzmg7q.jpg",
     "alt": "Inside Wanderlust 48: kitchen and dining area with a slatted "
            "timber ceiling and glazing onto open fields"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "wanderlust-48-bedroom.02gun-re0wb_5.jpg",
     "alt": "Wanderlust 48 bedroom with full-height glazing onto the "
            "landscape and a slatted timber ceiling"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "serenity-catalog.2xcd8x45pacpa.jpg",
     "alt": "Serenity 95 by BIOBUILDS: a dark-clad home with a timber deck "
            "and outdoor seating on a lawn"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "serenity-95-int-catalog.0uuneoqa7y-h8.jpg",
     "alt": "Inside Serenity 95: a living room with sofa and armchairs and "
            "sliding glazing onto a meadow"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "serenity-95-bathroom.1nmu58m7tl0_u.jpg",
     "alt": "Serenity 95 bathroom with marble-effect walls, a walk-in "
            "shower and an oval backlit mirror"},
    # SANCTUARY AND BLOOM, 16 October 2026. Exactly the four assets already
    # enumerated for these products in image-rights-records.json
    # (approved_assets), with the alt text governed there. Nest 24 has no
    # approved asset, so it has no image; none is added.
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "sanctuary-yakisugi.1d2u4sny4bcpk.jpg",
     "alt": "The BIOBUILDS Sanctuary seen from outside, a timber-clad house "
            "in Yakisugi cladding with extensive glazing."},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "142-int-semi.0jp8pj_h42n45.jpg",
     "alt": "Inside the BIOBUILDS Sanctuary, an open living space with "
            "timber finishes and glazing to the garden."},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "bloom-yakisugi.0160b2ky8hgph.jpg",
     "alt": "The BIOBUILDS Bloom seen from outside, a larger timber-clad "
            "house in Yakisugi cladding."},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "190-int-semi.3vnsegejmoyvy.jpg",
     "alt": "Inside the BIOBUILDS Bloom, an open-plan living space with "
            "timber finishes."},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "wall-section-3.0.26fqr4wmqyq13.jpg",
     "alt": "Cutaway of the BIOBUILDS timber wall build-up, showing the "
            "insulation, board layers and membrane"},
    {"url": "https://www.biobuilds.com/_next/static/immutable/media/"
            "prefab-48-crane-lift.2fhf6txqe9e82.jpg",
     "alt": "A wrapped BIOBUILDS module suspended from crane slings during "
            "installation"},
]

# ── THE RANGE ──────────────────────────────────────────────────────────────
# All five BIOBUILDS models offered on the Irish configurator, in size order.
# Read from the supplier's own Irish pages on RANGE_READ_DATE. Prices are the
# Irish prices including 23% VAT exactly as shown on each model panel; area is
# the interior floor area as published, with the per-floorplan range where
# BIOBUILDS publish one. None means "not published" and renders as
# TBC_TEXT -- never a guess.
TBC_TEXT = "To be confirmed by BIOBUILDS"
RANGE = [
    {"name": "Nest 24", "anchor": "nest-24", "area": "16.84 m&sup2;",
     "ef": "&euro;74,300", "tk": "&euro;101,100"},
    {"name": "Wanderlust 48", "anchor": "wanderlust-48", "area": "35.54 m&sup2;",
     "ef": "&euro;105,000", "tk": "&euro;163,000"},
    {"name": "Serenity 95", "anchor": "serenity-95",
     "area": "77.06&ndash;78.21 m&sup2;, by floorplan",
     "ef": "&euro;191,000", "tk": "&euro;306,000"},
    {"name": "Sanctuary 142", "anchor": "sanctuary-142",
     "area": "120.41&ndash;121.54 m&sup2;, by floorplan",
     "ef": "&euro;278,000", "tk": "&euro;444,000"},
    {"name": "Bloom 190", "anchor": "bloom-190",
     "area": "162.68&ndash;164.19 m&sup2;, by floorplan",
     "ef": "&euro;354,000", "tk": "&euro;572,000"},
]

RANGE_CSS = """<style>
/* THE RANGE -- added 16 Oct 2026. Tokens only; stacks below 640px. */
.pn-range{ margin-top:var(--pn-md); border-top:1px solid var(--pn-hair); }
.pn-range-row{ display:grid; grid-template-columns:1.3fr 1.6fr 1fr 1fr;
  gap:6px var(--pn-md); padding:14px 0; border-bottom:1px solid var(--pn-hair);
  align-items:baseline; }
.pn-range-head{ font-size:var(--pn-w-caption); letter-spacing:.12em;
  text-transform:uppercase; color:var(--pn-stone); padding:10px 0; }
.pn-range-row b{ color:var(--pn-voice); font-weight:600; }
.pn-range-tbc{ color:var(--pn-stone); font-style:italic; }
.pn-range-note{ font-size:var(--pn-w-body-sm); color:var(--pn-stone);
  margin-top:var(--pn-md); max-width:70ch; }
@media (max-width:640px){
  .pn-range-head{ display:none; }
  .pn-range-row{ grid-template-columns:1fr 1fr; }
  .pn-range-row > :first-child{ grid-column:1 / -1; }
  .pn-range-row [data-k]::before{ content:attr(data-k); display:block;
    font-size:var(--pn-w-meta); letter-spacing:.12em; text-transform:uppercase;
    color:var(--pn-stone); }
  .pn-range-row [data-k="Interior floor area"]{ grid-column:1 / -1; }
}
</style>
"""


def cell(v, label):
    if v is None:
        return '<span data-k="%s" class="pn-range-tbc">%s</span>' % (label, TBC_TEXT)
    return '<span data-k="%s">%s</span>' % (label, v)


def range_block():
    rows = ['    <div class="pn-range-row pn-range-head" aria-hidden="true">'
            '<span>Model</span><span>Interior floor area</span>'
            '<span>Exterior Finished</span><span>Turnkey</span></div>']
    for m in RANGE:
        rows.append('    <div class="pn-range-row" role="listitem"><b>%s</b>%s%s%s</div>'
                    % (m["name"], cell(m["area"], "Interior floor area"),
                       cell(m["ef"], "Exterior Finished"),
                       cell(m["tk"], "Turnkey")))
    return ("<!-- THE RANGE -- all five BIOBUILDS models for Ireland, for the\n"
            "     supplier to confirm. Built from RANGE in\n"
            "     build-biobuilds-preview.py; read %s. -->\n"
            "<section>\n"
            "  <h2>The five BIOBUILDS models</h2>\n"
            "  <p>These are the Irish prices and interior floor areas we have "
            "taken from <a href=\"https://www.biobuilds.com/ie/design\" "
            "rel=\"noopener\">biobuilds.com/ie</a>. Please check each line.</p>\n"
            "  <div class=\"pn-range\" role=\"list\">\n%s\n  </div>\n"
            "  <p class=\"pn-range-note\">All prices are as published by "
            "BIOBUILDS for Ireland and include 23%% VAT and transport to "
            "Ireland. Installation on prepared ground screws is included. "
            "Foundations, utility connections and site works are quoted per "
            "project. Turnkey is finished inside and out; kitchen connections "
            "are prepared, and kitchen furniture and appliances are not "
            "included. The number in each model name is BIOBUILDS&rsquo; own "
            "model name, not its floor area.</p>\n"
            "</section>\n"
            % (RANGE_READ_DATE, "\n".join(rows)))


# ── THE COPY ───────────────────────────────────────────────────────────────
# Voice: ordinary, direct, the way Colin would say it to Mateus. Nothing
# about the medium of the imagery. No certification claim, no thermal claim,
# no Irish planning claim -- those are in the review note instead.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner would reach BIOBUILDS",
    # THE THIRD SENTENCE IS THE SHORTENED-EXAMPLE NOTE. It belongs in the
    # lede rather than in a new element below the stage: the reader meets it
    # BEFORE they form a judgement about how thin Results looks, and adding
    # a node under .pn-stage would be a structural change to the mock-up,
    # which this pass is not allowed to make.
    # THE LEDE IS THE CLARIFICATION AND NOTHING ELSE. Founder-authorised on
    # 2026-10-02: the two framing sentences that stood here before were
    # removed, not shortened. Do not reintroduce explanatory copy around it.
    "DEMO_LEDE": "This is a shortened example of the Results "
                 "experience &mdash; a homeowner would see additional "
                 "property-specific checks, comparison information and "
                 "supporting detail as they continue through PlotNua.",


    "OFFER_NAME": "Wanderlust 48",
    "VERIFIED_PRICE": "&euro;105,000 exterior finished &middot; "
                      "&euro;163,000 turnkey",
    "VERIFIED_PRICE_BASIS": "Irish prices published by BIOBUILDS, including "
                            "23% VAT. Transport and assembly on prepared "
                            "ground screws are included. Foundations, utility "
                            "connections and site works are quoted per "
                            "project.",

    "VERIFIED_FACT_1_LABEL": "Interior floor area",
    "VERIFIED_FACT_1_VALUE": "35.54 m&sup2;",
    "VERIFIED_FACT_2_LABEL": "Bedrooms",
    "VERIFIED_FACT_2_VALUE": "1&ndash;2",
    # 16 Oct 2026: the Serenity line is superseded by the five-model range
    # section, which carries every model's prices; this slot now points there.
    "VERIFIED_FACT_3": "Also for Ireland: Nest 24, Serenity 95, Sanctuary 142 "
                       "and Bloom 190 &mdash; prices below",
    # Aligned to biobuilds.com/ie/turnkey, read 11 October 2026. Only what the
    # supplier publishes. The withdrawn line claimed a kitchen, air
    # conditioning and underfloor heating: the kitchen is expressly excluded,
    # and neither air conditioning nor underfloor heating appears in the
    # specification, so neither is claimed.
    "VERIFIED_FACT_4": "Turnkey is finished inside and out, including "
                       "interior finishes and bathroom fixtures. Kitchen "
                       "furniture and appliances are not included.",
    # The template carries FIVE fact slots. {{VERIFIED_FACT_N}} appears only
    # inside the instruction comment that G1 strips, so a sixth fact has
    # nowhere to go -- the Serenity figure lives in WHY_3_TEXT instead,
    # where it reads as range context rather than a sixth spec line.
    "VERIFIED_FACT_5": "Delivery to the Republic of Ireland confirmed by "
                       "BIOBUILDS",

    # ONE HONEST LINE. The published price is the home; the two costs that
    # are genuinely not in it are named, because a homeowner who finds that
    # out later finds it out badly. No planning claim -- PlotNua has not
    # established the Irish planning position for these and will not imply
    # one here.
    "THINGS_TO_CHECK": "foundations, utility connections and site works are "
                       "quoted per project, and kitchen furniture and "
                       "appliances are not included.",

    # PERSONALISATION GUARDRAIL §6 — locality only. The journey asks for an
    # Eircode and simplifyLocalityDisplay() turns it into exactly this. It
    # asks nothing about site, orientation or access, so nothing else here
    # may be personalised.
    "HOMEOWNER_LOCALITY": "Co. Galway",
    "PERSONALISATION": "Shown for a homeowner in Co. Galway, from the "
                       "location they gave us.",

    "WHY_1_LABEL": "MORE CONTEXT",
    "WHY_1_TEXT": "By the time someone reaches you they have already worked "
                  "out roughly what they want, what size, and what they can "
                  "spend. You are not starting from nothing.",
    "WHY_2_LABEL": "CLEARER INTENT",
    "WHY_2_TEXT": "A modular home is a long decision. People arrive at it "
                  "slowly. We would rather send you three people who have "
                  "thought about it than thirty who have not.",
    "WHY_3_LABEL": "A BETTER STARTING POINT",
    "WHY_3_TEXT": "Your published sizes and prices are already in front of "
                  "them &mdash; five models, from &euro;74,300 for Nest 24 "
                  "to &euro;354,000 for Bloom 190, exterior finished &mdash; "
                  "so the first conversation can be about their site rather "
                  "than your catalogue.",

    # THE ENDING IS NOW THE REVIEW ASK, not a commercial question. The grant
    # is conditional on BIOBUILDS seeing the listing first, so the last thing
    # on the page is the thing we actually need from them.
    "CLOSING_PROPOSITION": "Thank you for reviewing the original preview.",
    # Two paragraphs. The token sits inside a single <p>, so the break is
    # written as a closing and opening tag rather than a second token.
    "CLOSING_SUPPORT": "We&rsquo;ve updated this page to reflect your "
                       "feedback, including the revised Irish pricing, "
                       "what&rsquo;s included in each configuration and the "
                       "image captions. It now covers all five models "
                       "&mdash; Nest 24, Wanderlust 48, Serenity 95, "
                       "Sanctuary 142 and Bloom 190 &mdash; with the Irish "
                       "prices and interior floor areas published on "
                       "biobuilds.com."
                       "</p>\n  <p>"
                       "Please check the details for each of the five models "
                       "and confirm they are accurate, or let us know what "
                       "needs adjusting. Once you&rsquo;re happy that "
                       "everything is correct for all five, we can discuss "
                       "making BIOBUILDS visible to Irish homeowners on "
                       "PlotNua.",

    # DATE is gone from FILL because its only use, the footer line, now
    # carries REVISION_DATE written in at G3c. G4 refuses on a token it is
    # given but cannot find, and it was right to: leaving this here crashed
    # the build rather than writing a page with a stale date in it.
}


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


def imagery_block():
    """The hero media inner HTML. One list decides the state."""
    if not BIOBUILDS_IMAGES:
        return None, ("BIOBUILDS imagery, authorised %s. Your own images go "
                      "here, credited to BIOBUILDS and served from your site."
                      % PERMISSION_DATE)
    hero, rest = BIOBUILDS_IMAGES[0], BIOBUILDS_IMAGES[1:]
    out = ['        <div class="results-hero-media has-pn-gallery">',
           '          <img src="%s" alt="%s" loading="lazy">' % (hero["url"], hero["alt"]),
           '          <span class="pn-image-credit">%s</span>' % CAPTION_CREDIT,
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
                          i["url"], i["alt"].replace('"', "&quot;"), CAPTION_CREDIT,
                          i["url"]))
        out.append('        </div>')
    return "\n".join(out), None


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · EVERY IMAGE MUST BE FIRST-PARTY BIOBUILDS, UNMODIFIED.
    for i in BIOBUILDS_IMAGES:
        if not i["url"].startswith(PERMITTED_PREFIX):
            die("image outside the permitted BIOBUILDS prefix: " + i["url"])
        if not i["url"].startswith("https://"):
            die("image is not https: " + i["url"])

    # G1 · Strip the template's filling instructions (they carry {{TOKEN}}).
    block = re.search(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                      src, re.S)
    if not block:
        die("the template's instruction comment was not found. Not guessing.")
    src = src.replace(block.group(0), "\n")

    # G1b · Remove the introductory hero. The page opens on the demonstration,
    # so the first thing BIOBUILDS sees is their own result.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero:
        die("the introductory hero block was not found. Not guessing.")
    if "{{PROPOSITION}}" not in hero.group(0) or "{{LEDE}}" not in hero.group(0):
        die("the matched hero block does not carry the headline tokens.")
    src = src.replace(hero.group(0), "\n")
    FILL.pop("PROPOSITION", None)
    FILL.pop("LEDE", None)

    # G2 · Move the frozen journey band below the demonstration. Relocated
    # byte-for-byte, never rewritten; G7 proves that.
    jm = re.search(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                   src, re.S)
    if not jm:
        die("the frozen journey band was not found. Not guessing.")
    journey = jm.group(0)
    src = src.replace(journey, "\n")
    why_anchor = "<!-- WHY THIS COULD BE USEFUL"
    if src.count(why_anchor) != 1:
        die("the 'why' section anchor is not unique. Nothing written.")
    src = src.replace(why_anchor, journey.strip("\n") + "\n\n" + why_anchor)

    # G2b · THE RANGE, between the demonstration and the journey band. The
    # journey band itself is untouched; the range is inserted before it.
    if src.count(journey.strip("\n")) != 1:
        die("the relocated journey band is not unique. Nothing written.")
    src = src.replace(journey.strip("\n"),
                      range_block() + "\n" + journey.strip("\n"))
    if src.count("</head>") != 1:
        die("the </head> anchor is not unique. Nothing written.")
    src = src.replace("</head>", RANGE_CSS + "</head>")

    # G3 · Imagery.
    imgs, held_line = imagery_block()
    if imgs is None:
        # G3 · THE IMAGE POSITION CARRIES NO COPY (certified,
        # 5 Oct 2026). Nothing to do here any more: the template now
        # ships the correct restrained empty panel, so the right
        # action in the no-imagery case is none at all. THIS BRANCH
        # IS THE FAIL-CLOSED PATH and it stays fail-closed.
        pass
    else:
        slot = re.search(r'        <div class="results-hero-media">\n'
                         r'          <div class="pn-photo-slot"[^>]*>.*?</div>\n'
                         r'        </div>\n', src, re.S)
        if not slot:
            die("the held media wrapper was not found, so state A cannot "
                "replace it. Nothing written.")
        src = src.replace(slot.group(0), imgs + "\n")
        FILL.pop("PHOTO_SLOT_LINE", None)
        # A LITERAL © CHARACTER, never &copy;. The rights gate scans raw HTML
        # for the exact credit token, so the entity form would leave the page
        # looking credited to a reader while the gate saw no credit at all.
        # The link back is half of what BIOBUILDS actually asked for.
        credit = ('          <p class="credit-line">%s. Images used with '
                  'permission given %s, unmodified and served from '
                  '<a href="https://www.biobuilds.com/" rel="noopener">'
                  'biobuilds.com</a>. If BIOBUILDS ask for any of them to be '
                  'changed or removed, we change or remove them.</p>\n'
                  % (CREDIT, PERMISSION_DATE))
        foot = "<footer>\n"
        if src.count(foot) != 1:
            die("the footer anchor is not unique. Nothing written.")
        src = src.replace(foot, credit + foot)

    # G3b · THE CLOSING HEADING. "What we'd like to explore" is hardcoded in
    # the template, not a token, so it is replaced by exact string. The
    # section is now the pre-publication review ask, and the heading has to
    # say so or the two new sentences under it read as a change of subject.
    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once, so it cannot be "
            "replaced. Nothing written.")
    src = src.replace(old_head, "<h2>Updated BIOBUILDS Preview</h2>")

    # G3c · THE FOOTER. The template's shape is "Private preview prepared for
    # NAME . DATE". This is no longer the first preview, so the footer says so
    # and carries the revision date. SUPPLIER_NAME and DATE are still filled
    # at G4, so this replacement runs against the unfilled template line.
    old_foot = ("  <p>Private preview prepared for {{SUPPLIER_NAME}} "
                "&middot; {{DATE}}</p>")
    if src.count(old_foot) != 1:
        die("the footer line was not found exactly once, so it cannot be "
            "replaced. Nothing written.")
    src = src.replace(old_foot, "  <p>{{SUPPLIER_NAME}} &middot; Updated "
                                "private preview &middot; %s</p>"
                                % REVISION_DATE)

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

    # G5 · PRIVACY. Non-negotiable on a supplier preview.
    for directive in ("noindex", "nofollow", "noarchive", "nosnippet",
                      "noimageindex"):
        if directive not in src:
            die("the robots directive '%s' is missing." % directive)

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Hutsmith", "Yard Box", "Power Sheds", "TRIQ", "Superior "
                  "Pergola", "Dudley", "Cormac"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · MEDIUM NOT ESTABLISHED. The page must not say, or imply, whether
    # the imagery is photography or a visualisation.
    #
    # IT READS THE VISIBLE PAGE, NOT THE FILE. The first version scanned the
    # raw HTML and refused this very build: template-provider-led.html
    # explains its own layout in CSS comments that say "photograph", and a
    # guard that cannot tell the template's internal commentary from a claim
    # about BIOBUILDS' imagery will refuse every correct build after this one
    # too. Comments, <style> and <script> are stripped first; what is left is
    # what a reader actually sees.
    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    low = visible.lower()
    for w in BANNED_MEDIUM_WORDS:
        if w.lower() in low:
            die("the visible page asserts the medium of the imagery with the "
                "word %r. BIOBUILDS has not stated it and PlotNua has not "
                "established it." % w.strip())

    # G9 · STATE A REQUIRES THE CREDIT ON THE PAGE, as a literal ©.
    #
    # THE CONSTANT IS CHECKED BEFORE IT IS COUNTED. The first version only
    # counted occurrences, and src.count("") returns the page length, so
    # emptying CREDIT made the guard pass while shipping a page with no
    # credit at all -- the one thing BIOBUILDS actually asked for. A guard
    # whose subject can be deleted out from under it is not a guard.
    if imgs is not None:
        if CREDIT != "© BIOBUILDS":
            die("the required credit constant is not '© BIOBUILDS' but %r. "
                "The grant requires that exact wording." % CREDIT)
        if "&copy;" in src:
            die("the credit is written as the HTML entity &copy;. The rights "
                "gate scans raw HTML for a literal ©, so the entity form "
                "would read as credited while the gate saw no credit.")
        if src.count(CREDIT) < 2:
            die("state A without the %s credit present at least twice (the "
                "image caption and the rights line)." % CREDIT)
        if "biobuilds.com" not in src:
            die("state A without the link back to biobuilds.com, which is "
                "half of what BIOBUILDS asked for.")

    # G10 · NO PARTNERSHIP IMPLICATION.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed"):
        if word in low:
            die("the page implies a relationship that does not exist: " + word)

    # G11 · ALL FIVE MODELS, EACH WITH ITS FIGURES OR AN EXPLICIT TBC.
    if len(RANGE) != 5:
        die("the range does not carry exactly five models.")
    for m in RANGE:
        if m["name"] not in visible:
            die("model %s is missing from the visible page." % m["name"])
        for k in ("area", "ef", "tk"):
            if m[k] is not None and m[k] not in visible:
                die("%s %s value is missing from the page." % (m["name"], k))
    n_tbc = sum(1 for m in RANGE for k in ("area", "ef", "tk") if m[k] is None)
    if visible.count(TBC_TEXT) != n_tbc:
        die("'%s' appears %d times for %d unpublished values."
            % (TBC_TEXT, visible.count(TBC_TEXT), n_tbc))
    for word in (" is live", "now live", "live on plotnua", "published on plotnua"):
        if word in low:
            die("the page says something is live: " + word)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("BIOBUILDS PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    11 guards passed")
    print("  ok    %d governed BIOBUILDS images, all under %s"
          % (len(BIOBUILDS_IMAGES), PERMITTED_PREFIX))
    print("  ok    credit %r present %d times" % (CREDIT, src.count(CREDIT)))
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    medium not asserted anywhere on the page")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
