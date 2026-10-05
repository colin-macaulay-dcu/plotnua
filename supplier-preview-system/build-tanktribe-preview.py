#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE TANKTRIBE PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html, reused.

*** THIS ONE HAS IMAGERY, AND THAT IS THE DIFFERENCE. ***

Tanktribe replied YES on 2 October 2026: explicit permission to feature them
and use selected website imagery with clear credit and a link back. Atlas
holds "Granted -- Founder Confirmed" on WELLNESS-FIRST-TANKTRIBE-20261002 and
all six governed assets are Publication Status "Approved", so this is imagery
STATE A -- the first of these previews since BIOBUILDS to carry photographs.

The rights record and the scoped manifest row come from
.github/scripts/build-tanktribe-grant.py. The scope matters: Tanktribe's site
is Squarespace, so the photographs are served from images.squarespace-cdn.com,
a host shared with every Squarespace site in the world. The grant is scoped to
their own namespace /content/v1/67ac8d737a7c665f57f5babe/.

*** THE AI-ASSET EXCLUSION. *** tanktribe.ie also publishes files named
"ChatGPT Image ...". Those are NOT governed and must never appear. The grant
covers Tanktribe's photography; showing an AI-generated image as a product
photograph would misrepresent what a homeowner would actually receive. G0b
refuses the build if one reaches the image list, by filename and by any
AI-suggesting token.

*** AND THE SEND GATE STILL APPLIES. *** Permission to use imagery is not
permission to email the supplier an unreviewed page.
SUPPLIER-PREVIEW-SYSTEM-V1 §10.1: build, prove, deploy, hand the URL to the
founder, STOP. Nothing in this file sends anything, and a clean run here is
not approval to send.

Run: python3 build-tanktribe-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/tanktribe-preview.html") if STAGE
       else SITE / "tanktribe-preview.html")

SUPPLIER = "Tanktribe"
EVIDENCE_DATE = "2 October 2026"
PERMISSION_DATE = "2 October 2026"
SUPPLIER_SITE = "https://www.tanktribe.ie/"
CREDIT = "© Tanktribe"
PERMITTED_PREFIX = ("https://images.squarespace-cdn.com/content/v1/"
                    "67ac8d737a7c665f57f5babe/")

# ── THE SIX GOVERNED ASSETS ────────────────────────────────────────────────
# Every one is Publication Status "Approved" in Atlas and every one is a
# photograph. WILD TUB leads because it is the primary example; CORE follows
# as the cold-plunge example. Alt text describes what is visible.
TANKTRIBE_IMAGES = [
    # FOUNDER-SET ORDER, 2 Oct 2026, CORE-FIRST. The hero image is the
    # PRODUCT CARD's image, not a page banner: it sits inside the same
    # <section> as the product name and price. So the framed product and the
    # first image have to be the same thing, or the page shows a €510 cold
    # plunge under a €1,485 WILD TUB heading. That binding is why the hero
    # could not simply be swapped while WILD TUB stayed framed.
    #
    # IMG_8495 leads because it is the only governed asset that is a single
    # tub, unmistakably a cold plunge, with no competing wordmark and no
    # identifiable face. The two coil shots stay at 5 and 6 so the WILD TUB
    # wood-fired function remains visually evidenced.
    #
    # ALT TEXT IS THE ATLAS DESCRIPTION, VERBATIM, for all six. All six were
    # corrected on 2 Oct 2026 after each image was opened and looked at; the
    # originals were written from the product pages and the filenames and
    # every one of them was wrong or materially incomplete.
    {"url": PERMITTED_PREFIX + "2d930a20-ec94-4b5f-8af4-159501335d62/"
            "IMG_8495.jpg",
     "alt": "Overhead view of a Tanktribe CORE galvanised stock tank on a "
            "timber deck, filled with iced water, with a person lying "
            "submerged in it"},
    {"url": PERMITTED_PREFIX + "1760048787936-G7C8NEDHMKBFMZPTGO00/"
            "IMG_8455.jpg",
     "alt": "A man sitting in a Tanktribe CORE galvanised stock tank "
            "filled with iced water on a timber deck, with TANKKD "
            "branding on the side of the tank"},
    {"url": PERMITTED_PREFIX + "bc66569f-f2d9-431e-bf62-7f0bb6e1a3b9/"
            "DSC_2111.jpg",
     "alt": "Four galvanised stock tanks lined up on grass beside water, "
            "each with a person sitting in iced water, with TANKKD "
            "branding on two of the tanks"},
    {"url": PERMITTED_PREFIX + "ab9c9630-7b25-441f-9559-b711ff7f6d5b/"
            "IMG_2531.JPG",
     "alt": "Close view from beside the Tanktribe WILD TUB showing the "
            "water surface, timber ledge, tub rim and garden background"},
    {"url": PERMITTED_PREFIX + "b9e11038-bd53-49c8-984b-65ed12892e43/"
            "IMG_2580%2B3.JPG",
     "alt": "Close-up of the Tanktribe WILD TUB wood-fired heating coil "
            "burning on gravel"},
    {"url": PERMITTED_PREFIX + "33335f39-c5fe-48af-9c3a-f6f6cc4e8c8e/"
            "IMG_2518.JPG",
     "alt": "Close-up of the Tanktribe WILD TUB wood-fired heating coil "
            "burning on a paving slab"},
]

# Tokens that would mean an AI-generated asset had reached the list.
AI_ASSET_TOKENS = ["chatgpt", "ai-generated", "ai_image", "midjourney",
                   "dall-e", "dalle", "stable-diffusion", "generated_image"]

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT ───────────────────────────────────
# Cold water and wood-fired heating invite health and safety claims that
# Tanktribe does not make and PlotNua must not. The VAT phrasing is banned
# because the published prices do not state their VAT treatment.
BANNED_CLAIM_PHRASES = [
    "inc. vat", "including vat", "ex vat", "excluding vat", "plus vat",
    "health benefit", "therapeutic", "medically", "clinically",
    "improves recovery", "reduces inflammation", "boosts immunity",
    "safe for", "doctor", "treatment",
    "installation included", "we install", "free delivery",
    "planning exempt", "no planning permission",
    "lead time of", "weeks from order",
    "warranty", "guaranteed for", "certified", "certification",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
# Plain questions, at the bottom, in the words a person would use.
# ── THE SECOND POSSIBILITY ─────────────────────────────────────────────────
# WILD TUB, moved here on 2 Oct 2026 when CORE became the framed product. It
# is a DISTINCT SECTION, not a second product in the same hero: the hero card
# carries one name, one price and one image, and they must agree.
#
# The wood-fired function stays visually evidenced -- IMG_2531 and IMG_2580+3
# are the coil images and they are 4th and 5th in the gallery above, which the
# paragraph points at. Markup is <section>, h2, p, b, br -- all template
# classes, no new CSS.
# IMG_2580+3, the wood-fired heating coil. Indexed out of the governed
# list rather than written out again, so it cannot drift from Atlas, and
# asserted by filename so a reorder cannot silently change which image
# illustrates the wood-fired claim.
WILD_TUB_COIL = TANKTRIBE_IMAGES[4]
if "IMG_2580" not in WILD_TUB_COIL["url"]:
    die("the WILD TUB section's supporting image is no longer the heating-coil "
        "photograph (%s). The section claims the picture shows the coil." % WILD_TUB_COIL["url"])

SECOND_POSSIBILITY = """<!-- THE SECOND POSSIBILITY — the wood-fired tub, after the cold plunge a
     homeowner would meet first. Shorter than the demonstration above. Every
     figure is first-party. -->
<section>
  <h2>Another way Tanktribe could appear</h2>
  <p>A homeowner who wants heat as well as cold reaches a different product,
     and the WILD TUB is the clearest answer in your range for somebody who
     has not decided whether they want hot, cold or both.</p>
  <p><b>Tanktribe WILD TUB</b><br>From &euro;1,485</p>
  <p>A wood-fired hot tub when the heating coil is lit, and a cold plunge when
     it is not. No electricity is needed for the heating, and one tub covers
     both halves of a hot-and-cold routine rather than needing two.</p>
  <!-- INLINE STYLES, DELIBERATELY. .results-hero-media and .pn-image-credit
       are both scoped '.pn-stage .…' in the kit, and this section sits OUTSIDE
       the stage, so borrowing those class names would have produced an
       unstyled full-natural-width image -- fine at 1440 and overflowing at
       390. The geometry is copied from the stage rules (4/3, 14px radius,
       cover) so the two images read as the same component. -->
  <div style="position:relative; max-width:460px; aspect-ratio:4/3;
              border-radius:14px; overflow:hidden; margin:18px 0 0;
              box-shadow:0 14px 28px -14px rgba(36,53,31,.18);">
    <img src="%s" alt="%s" loading="lazy"
         style="width:100%%; height:100%%; object-fit:cover; display:block;">
    <span style="position:absolute; left:0; right:0; bottom:0; padding:16px 14px 8px;
                 font-size:10.5px; letter-spacing:.02em; color:#fff;
                 background:linear-gradient(0deg, rgba(20,34,26,.62) 0%%,
                   rgba(20,34,26,0) 100%%);">%s</span>
  </div>
</section>
""" % (WILD_TUB_COIL["url"], WILD_TUB_COIL["alt"], CREDIT)

OPEN_QUESTIONS = """<!-- THE OPEN QUESTIONS — the points the supplier's own site leaves open,
     asked and not resolved. Each names what the site does say first. -->
<section>
  <h2>A few things we would ask before publishing</h2>
  <p>These are the three things we&rsquo;d like to check with you before the
     page goes live.</p>
  <div class="pn-open">
    <ul>
      <li><b>VAT.</b> Your prices are published as &ldquo;from&rdquo;
          figures without stating whether VAT is included. Which is it, so we
          show the right thing?</li>
      <!-- "commission the tub" in the engineering sense collided with G10's
           ban on "commission" in the commercial sense. Third collision of
           this build, and the third time the copy moved rather than the
           guard: these bans are blunt on purpose, and a blunt guard with
           slightly constrained prose is worth more than a clever guard with
           a hole in it. -->
      <li><b>Delivery and setup.</b> Is delivery quoted separately, and do you
          position the tub and get it running, or is that the
          homeowner&rsquo;s own job once it arrives?</li>
      <li><b>What each one needs on site.</b> CORE implies a level base and
          water access; the WILD TUB additionally implies sensible clearance
          around the flue. Is there a standard list you would want a homeowner
          to have thought about before they call?</li>
      <li><b>FLOW and ACTIVE.</b> We have shown CORE as the simple
          cold-plunge option and mentioned FLOW and ACTIVE as the filtration
          and temperature-controlled steps up. Is that the right way round to
          describe them?</li>
    </ul>
  </div>
</section>
"""

FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Tanktribe",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what Tanktribe publishes. They would first "
                 "discover a possibility for their property, work through "
                 "whether it fits and what to check, and only then reach "
                 "suppliers &mdash; so by the time this screen appears the "
                 "thinking has already happened.",


    # CORE IS THE FRAMED PRODUCT, founder-set 2 Oct 2026 (option 1). The
    # hero image is the product CARD's image -- same <section> as the name
    # and the price -- so the framed product and the first image have to be
    # the same thing, or the page shows a 510 euro cold plunge under a
    # 1,485 euro WILD TUB heading. WILD TUB moves to its own section below.
    "OFFER_NAME": "CORE",
    "VERIFIED_PRICE": "from &euro;510",
    # "VAT treatment" collided with G8's ban on "treatment" -- a medical
    # word on a cold-water product. The guard is right to be blunt there, so
    # the copy moved rather than the ban.
    "VERIFIED_PRICE_BASIS": "as published by Tanktribe. The page does not "
                            "say whether VAT is included, so neither do "
                            "we.",

    "VERIFIED_FACT_1_LABEL": "What it is",
    "VERIFIED_FACT_1_VALUE": "a natural cold plunge built around a galvanised "
                             "steel stock tank, for outdoor use",
    "VERIFIED_FACT_2_LABEL": "How it runs",
    "VERIFIED_FACT_2_VALUE": "no pump and no chiller &mdash; fresh water, and "
                             "ice if a homeowner wants it colder",
    "VERIFIED_FACT_3": "The simplest configuration in the range, and the one "
                       "that needs least done to the garden",
    "VERIFIED_FACT_4": "FLOW adds filtration from &euro;850 and ACTIVE adds "
                       "temperature control from &euro;1,939, so there is "
                       "somewhere to go afterwards",
    "VERIFIED_FACT_5": "The WILD TUB, from &euro;1,485, is the wood-fired "
                       "option: a hot tub with the coil lit and a cold plunge "
                       "without it",

    "THINGS_TO_CHECK": "the published figure is a &ldquo;from&rdquo; price, and "
                       "the page does not say whether VAT is included, so a "
                       "homeowner should confirm both. Delivery, siting and "
                       "how the water is kept fresh without filtration are "
                       "the other things worth asking about before ordering.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY.
    "HOMEOWNER_LOCALITY": "Co. Wicklow",
    "PERSONALISATION": "Shown for a homeowner in Co. Wicklow, from the "
                       "location they gave us. We do not ask them about their "
                       "garden surface, water access or where a flue could "
                       "safely go, so we would not pretend to know &mdash; "
                       "those stay as things to raise with you.",

    "WHY_1_LABEL": "A FIRST STEP SOMEBODY WILL ACTUALLY TAKE",
    "WHY_1_TEXT": "CORE is the least committing thing in your range for a "
                  "homeowner who has been reading about cold water and has not "
                  "decided how far in they want to go. At &euro;510, with no "
                  "pump and no chiller, it is a decision they can make.",
    "WHY_2_LABEL": "A LADDER, NOT A LIST",
    "WHY_2_TEXT": "CORE, FLOW and ACTIVE read as a progression &mdash; fill "
                  "it yourself, then filtration, then temperature control. "
                  "That is a genuinely useful way to meet somebody at "
                  "whatever point they have reached.",
    "WHY_3_LABEL": "REACHED THROUGH WELLNESS",
    "WHY_3_TEXT": "A homeowner arrives here having decided they want a garden "
                  "retreat, not having typed your name into a search box. "
                  "That is a different kind of enquiry from a directory click.",

    "CLOSING_PROPOSITION": "Does this represent Tanktribe accurately for an "
                           "Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, let us know and we&rsquo;ll correct it "
                       "before publication.",

    "DATE": EVIDENCE_DATE,
}


def imagery_block():
    """The hero media inner HTML. One list decides the state."""
    if not TANKTRIBE_IMAGES:
        return None, ("Tanktribe imagery, authorised %s." % PERMISSION_DATE)
    hero, rest = TANKTRIBE_IMAGES[0], TANKTRIBE_IMAGES[1:]
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
    return "\n".join(out), None


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · EVERY IMAGE MUST BE INSIDE THE GRANTED SCOPE, UNMODIFIED.
    if len(TANKTRIBE_IMAGES) != 6:
        die("expected the 6 governed Approved assets, found %d. Atlas holds "
            "six; a different number means the list and Atlas disagree."
            % len(TANKTRIBE_IMAGES))
    for i in TANKTRIBE_IMAGES:
        if not i["url"].startswith(PERMITTED_PREFIX):
            die("image outside Tanktribe's granted Squarespace namespace: "
                + i["url"] + ". The bare CDN host is shared with every "
                "Squarespace site in the world.")
        if not i["url"].startswith("https://"):
            die("image is not https: " + i["url"])

    # G0b · NO AI-LABELLED ASSET. The grant covers their photography, and an
    # AI-generated image shown as a product photograph would misrepresent
    # what a homeowner would actually receive.
    for i in TANKTRIBE_IMAGES:
        blob = (i["url"] + " " + i["alt"]).lower()
        for tok in AI_ASSET_TOKENS:
            if tok in blob:
                die("an AI-labelled asset reached the image list (%r in %s). "
                    "tanktribe.ie publishes 'ChatGPT Image ...' files; they "
                    "are not governed and must never be shown as product "
                    "photography." % (tok, i["url"]))

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

    # G2 · Relocate the frozen journey band; open questions sit between.
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
                      SECOND_POSSIBILITY + "\n" + OPEN_QUESTIONS + "\n" + journey.strip("\n")
                      + "\n\n" + why_anchor)

    # G3 · IMAGERY STATE A.
    imgs, held = imagery_block()
    if imgs is None:
        die("the image list is empty, but Tanktribe granted imagery. A held "
            "slot here would understate what they agreed to.")
    slot = re.search(r'        <div class="results-hero-media">\n'
                     r'          <div class="pn-photo-slot"[^>]*>.*?</div>\n'
                     r'        </div>\n', src, re.S)
    if not slot:
        die("the held media wrapper was not found, so state A cannot replace "
            "it. Nothing written.")
    src = src.replace(slot.group(0), imgs + "\n")
    FILL.pop("PHOTO_SLOT_LINE", None)

    # G3c · CREDIT AND LINK BACK, the two things Tanktribe actually asked for.
    # A LITERAL © CHARACTER, never &copy;: the rights gate scans raw HTML for
    # the exact credit token, so the entity form would read as credited to a
    # person while the gate saw no credit at all.
    credit_line = (
        '          <p class="credit-line">%s. Images used with permission '
        'given %s, unmodified and served from '
        '<a href="%s" rel="noopener">tanktribe.ie</a>. If Tanktribe ask for '
        'any of them to be changed or removed, we change or remove them. '
        'Every figure on this page is published by Tanktribe and was read on '
        '%s.</p>\n' % (CREDIT, PERMISSION_DATE, SUPPLIER_SITE, EVIDENCE_DATE))
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
    # TANKKD is deliberately NOT in this list: it is the stock-tank
    # manufacturer whose wordmark is visible on two governed CORE
    # photographs, and naming it in alt text is accurate rather than a leak
    # — the same call made for Harvia on the Irish Sauna Company preview.
    for other in ("Cosy Cabins", "Irish Sauna Company", "Hutsmith",
                  "Yard Box", "Power Sheds", "TRIQ", "BIOBUILDS",
                  "Superior Pergola", "Honka", "MyCabin", "Harvia"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM. Cold water invites health claims; Tanktribe
    # does not make them and neither will PlotNua.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support: %r. Cold-water and wood-fired products attract "
                "health, safety and tax claims that this supplier has not "
                "made." % phrase)

    # G9 · THE CREDIT AND THE LINK BACK, proven on the artefact.
    #
    # THE CONSTANT IS CHECKED BEFORE IT IS COUNTED. src.count("") returns the
    # page length, so an emptied CREDIT would make a count-only guard pass
    # while shipping an uncredited page -- the one thing the supplier asked
    # for. That mistake was made once on the BIOBUILDS builder; it is not
    # being made again.
    if CREDIT != "© Tanktribe":
        die("the required credit constant is not '© Tanktribe' but %r. "
            "The grant requires that exact wording." % CREDIT)
    if "&copy;" in src:
        die("the credit is written as the HTML entity &copy;. The rights gate "
            "scans raw HTML for a literal ©, so the entity form would "
            "read as credited while the gate saw no credit.")
    if src.count(CREDIT) < 2:
        die("state A without the %s credit present at least twice (the image "
            "caption and the rights line)." % CREDIT)
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s, which is half of what "
            "Tanktribe asked for. A mention in prose is not a link."
            % SUPPLIER_SITE)
    # Six in the strip, the hero repeated as its own first thumbnail, and one
    # coil image in the WILD TUB section below: 6 + 1 + 1.
    EXPECTED_IMGS = len(TANKTRIBE_IMAGES) + 2
    if len(re.findall(r'<img[^>]+src="' + re.escape(PERMITTED_PREFIX), src)) \
            != EXPECTED_IMGS:
        die("the rendered image count is not the governed list plus the hero "
            "repeat in the thumbnail strip plus the WILD TUB coil image "
            "(expected %d). Something was dropped or duplicated."
            % EXPECTED_IMGS)
    stray = [u for u in re.findall(r'<img[^>]+src="(https?://[^"]+)"', src)
             if not u.startswith(PERMITTED_PREFIX)]
    if stray:
        die("an image outside the granted scope reached the page: " + stray[0])

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
    print("TANKTRIBE PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    14 guards passed")
    print("  ok    %d governed Approved images, all inside the granted "
          "Squarespace namespace" % len(TANKTRIBE_IMAGES))
    print("  ok    0 AI-labelled assets")
    print("  ok    credit %r present %d times, and the link back is a link"
          % (CREDIT, src.count(CREDIT)))
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no VAT, health, installation, delivery or warranty claim")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched.")
    print("SEND GATE: §10.1 — hand the URL to the founder and STOP. A "
          "clean run is not approval to email the supplier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
