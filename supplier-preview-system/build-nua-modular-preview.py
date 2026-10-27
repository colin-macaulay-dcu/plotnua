#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE NUA MODULAR PRIVATE SUPPLIER PREVIEW (v3, 27 Oct 2026).

TEMPLATE: supplier-preview-system/template-provider-led.html, the shared
Supplier Preview System v2 template (refresh-ui-kit.py v2): PlotNua's premium
dark design around production Your Plot Results. This builder fills tokens and
inserts content only; it carries no CSS of its own.

FOUNDER DECISIONS, 27 OCTOBER 2026
  13:43  private preview, An Extra Room + Additional Home, placeholders until
         image permission is confirmed; no public deployment
  13:59  brand-proximity hold lifted (CRM); premium dark design; Results demo
         faithful to production; content and safeguards preserved
  14:23  direction approved; re-verify the supplier's site; regenerate from the
         updated shared template; prepare private hosting; nothing deployed

IMAGERY STATE A (27 Oct 2026, 15:45 founder instruction): permission
requested 13:40 UTC (Gmail 1a17d976ddf345a4) and GRANTED by Sean Lannen at
15:29 UTC (Gmail 1a17dfb25a1be992): "Ya no problem at all - use whatever you
need." IPO recHiUyd9FkxqeW5e, Granted — Founder Confirmed; rights record
"Nua Modular" in image-rights-records.json. Only the two photographs
enumerated there are used, hot-linked unmodified from nuamodular.com and
credited "© Nua Modular". G0 refuses any other image, a manifest without the
live grant, or a different credit. Not used: nua-ultra-real-field.jpg (the
yard photograph with a replaced background) and the nua-pod-* renders of
other designs. No genuine interior photograph is published, so none is used.

EVIDENCE: re-read live in a browser on 27 October 2026 —
  https://www.nuamodular.com/nua-ultra.html  (specification table)
  https://www.nuamodular.com/                (range, process, enquiry form)
  * "Price on request" (specification) vs "Nua Ultra (€70,000)" (enquiry form)
  * Footprint 38.7 m², 11.4 × 3.4 m; overall height 3.30 m; 1 or 2-bed;
    2–4 occupants; single-lift, fully assembled
  * the hero labels the same 38.7 m² "INTERNAL AREA" — the site gives one
    figure two labels, so the internal floor area is still to be confirmed
  * "Optional: Fitted kitchen · …"; hot water "serving bathroom and optional
    kitchen"; fully fitted en-suite as standard
  * "delivered and installed across Ireland"; "lift the pod into position in
    a single day"; "We handle planning permission where required"
  Not used (unverified supplier assurances): certification, warranty, lead
  time, fixed-price claim.

BRAND PROXIMITY: "Nua" never stands alone on the page (G13), so the supplier
can never read as part of PlotNua.

Run: python3 build-nua-modular-preview.py [--out PATH]
  default output is the staging path; nothing is written to the deployed tree
  unless --out names it explicitly (used only by the prepared release).
"""

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template-provider-led.html"
TEMPLATE_SHA = "444b9ceebed72394cc5ee9c0a9497dcfaaeda541fd31c3e6ae2e377eee9bc1ff"

OUT = pathlib.Path("/tmp/plotnua-stage/nua-modular-preview.html")
if "--out" in sys.argv:
    OUT = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])

SUPPLIER = "Nua Modular"
EVIDENCE_DATE = "27 October 2026"
PREPARED = "27 October 2026"
SUPPLIER_SITE = "https://www.nuamodular.com/"
ULTRA_URL = SUPPLIER_SITE + "nua-ultra.html"
CREDIT = "© Nua Modular"

RIGHTS_RECORD = "PREVIEW-NUA-MODULAR-20261027"
GRANT_DATE = "27 October 2026"
PERMITTED_PREFIX = "https://www.nuamodular.com/brand_assets/nua-ultra-real-"
# Must equal approved_assets in image-rights-records.json, in order (G0).
NUA_IMAGES = [
    {"url": "https://www.nuamodular.com/brand_assets/nua-ultra-real-yard-cloudy.jpg",
     "alt": "Photograph of a Nua Ultra unit standing on gravel in a fenced yard "
            "under a cloudy sky: a long, rounded dark-grey module with a wide "
            "panoramic window along its side and a glazed end wall"},
    {"url": "https://www.nuamodular.com/brand_assets/nua-ultra-real-yard.jpg",
     "alt": "Photograph of the same Nua Ultra unit in the yard in low sunshine, "
            "seen from the glazed end, its panoramic side window reflecting "
            "the yard"},
]
# The photographs are portrait; the frame is 4:3 (3:2 on phones). Framing
# only -- the file is never cropped or altered -- so the whole unit stays in
# view rather than the sky above it.
FRAMING = "object-position:50% 70%"
SLOT = ('        <div class="results-hero-media">\n'
        '          <div class="pn-photo-slot"><b>Your image here</b></div>\n'
        '        </div>\n')

FROZEN_JOURNEY = [
    ("Discover", "See what a property like theirs could do."),
    ("Check", "What would actually work in their garden."),
    ("Explore", "Look at real options in detail."),
    ("Compare", "Weigh them up side by side."),
    ("Decide", "Settle on what to pursue."),
    ("Connect", "When ready, connect with a provider."),
]

BANNED_CLAIM_PHRASES = [
    "prices from", "starting at", "from only", "fixed price",
    "typical cost", "ballpark",
    "internal area of", "floor area of", "living space of",
    "planning exempt", "no planning permission", "does not need planning",
    "planning not required", "exempted development", "planning approved",
    "planning guaranteed", "class 3",
    "warranty", "year guarantee", "certified", "certification", "tüv",
    "iso", "ce marked",
    "lead time", "weeks from", "within weeks", "turnaround",
    "the nest",
]
BANNED_TONE_PHRASES = [
    "the wrong one", "ask for the wrong", "start at the wrong",
    "picks the wrong", "thought it through", "confused", "naive",
    "ill-informed", "waste your time", "wasting your time",
    "we know better", "put them right", "set them straight",
]
AREA_GAP = "internal floor area is still to be confirmed"
MUST_SAY = [
    ("price on request", "the specification table's own price wording"),
    ("&euro;70,000", "the enquiry-form figure, shown only as a question"),
    ("footprint", "38.7 m² must stay labelled as the footprint"),
    (AREA_GAP, "the gap must be visible, not inferred away"),
    ("where it&rsquo;s required", "the supplier's own planning wording"),
    ("local authority", "who actually decides; PlotNua does not"),
]

FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,
    "DEMO_HEADING": "How an Irish homeowner could reach Nua Modular",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your own pages publish. They would first "
                 "discover a possibility for their property, work through "
                 "whether it fits and what to check, and only then reach "
                 "suppliers &mdash; so by the time this screen appears the "
                 "thinking has already happened.",
    "OFFER_NAME": "Nua Ultra &mdash; one or two bedrooms",
    "VERIFIED_PRICE": "Price on request",
    "VERIFIED_PRICE_BASIS": "As published on the Nua Ultra specification. "
                            "Nua Modular quote each project after a "
                            "consultation.",
    "VERIFIED_FACT_1_LABEL": "What it is",
    "VERIFIED_FACT_1_VALUE": "A fully finished, factory-built pod with "
                             "living, sleeping, bathroom and wardrobe, for "
                             "two to four people",
    "VERIFIED_FACT_2_LABEL": "Size",
    "VERIFIED_FACT_2_VALUE": "11.4 &times; 3.4&nbsp;m footprint, 3.30&nbsp;m "
                             "overall height",
    "VERIFIED_FACT_3": "Fully fitted en-suite as standard; fitted kitchen, "
                       "underfloor heating and an accessibility package are "
                       "options",
    "VERIFIED_FACT_4": "Delivered fully assembled and lifted into position "
                       "in a single day, anywhere in Ireland",
    "VERIFIED_FACT_5": "Consultation, design, factory production and "
                       "installation from one point of contact, with "
                       "planning permission handled where it&rsquo;s "
                       "required",
    "THINGS_TO_CHECK": "the size shown is the footprint; the "
                       + AREA_GAP + ". Nua Modular handle planning "
                       "permission where it&rsquo;s required; whether a pod "
                       "needs it depends on the property and how it will be "
                       "used, and that&rsquo;s for the local authority to "
                       "decide. Delivery is by truck and crane, so access to "
                       "the site is worth checking early.",
    "HOMEOWNER_LOCALITY": "Co. Cork",
    "PERSONALISATION": "Shown for a homeowner in Co. Cork, from the location "
                       "they gave us. We don&rsquo;t ask about the size of "
                       "the garden, crane access or where the services run "
                       "&mdash; so we wouldn&rsquo;t pretend to know. Those "
                       "stay as things for your consultation.",
    "WHY_1_LABEL": "The right moment",
    "WHY_1_TEXT": "Homeowners on An Extra Room and Additional Home have "
                  "already decided they need more space at home. PlotNua "
                  "helps them explore what that could look like on their own "
                  "property, so when they reach Nua Modular they know what "
                  "they want to talk about.",
    "WHY_2_LABEL": "The practical questions, already raised",
    "WHY_2_TEXT": "A finished pod arriving by crane is a different "
                  "proposition from a build on site. We put access, services "
                  "and planning in front of the homeowner as things to check, "
                  "so they&rsquo;re part of the conversation from the start.",
    "WHY_3_LABEL": "Arriving with a developed idea",
    "WHY_3_TEXT": "By the time a homeowner reaches you through PlotNua, they "
                  "have looked at what their own property could take and "
                  "worked out what kind of space they want. They arrive with "
                  "a developed idea rather than an open question.",
    "CLOSING_PROPOSITION": "Does this represent Nua Modular accurately for "
                           "an Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, tell us and we&rsquo;ll correct it before "
                       "anything is published.",
    "DATE": PREPARED,
}

# Inserted between the demonstration and the frozen journey band (the Modulux
# pattern). Premium Discovery components only; no CSS.
SECTIONS = """<!-- WHERE NUA MODULAR FITS — the two journeys named in every email to Sean -->
<section aria-labelledby="nm-fit-h">
  <div class="pd-head">
    <span class="pd-kicker">Where Nua Modular fits</span>
    <h2 class="pd-h2" id="nm-fit-h">Two journeys where Nua Modular fits</h2>
    <p>Homeowners come to PlotNua with a need rather than a product in mind.
       Two of the journeys they explore line up closely with what Nua Modular
       builds.</p>
  </div>
  <div class="pd-grid is-stretch">
    <article class="pd-card pd-s-6">
      <span class="pd-kicker">Journey</span>
      <h3 class="pd-h3">An Extra Room</h3>
      <p>For a household that needs more space without moving or extending
         the house: a home office, a room for guests, a studio. The Nua Ultra
         arrives finished, with its own en-suite, and is lifted into place in
         a day.</p>
    </article>
    <article class="pd-card pd-s-6">
      <span class="pd-kicker">Journey</span>
      <h3 class="pd-h3">Additional Home</h3>
      <p>For a family thinking about a second, self-contained place on the
         property: a family annexe, multi-generational living or a permanent
         residence. You also publish a barrier-free version with a ramp, wider
         doorways and reinforced bathroom supports, which matters to families
         planning for an older relative.</p>
    </article>
  </div>
</section>

<!-- THREE QUESTIONS — the supplier's own inconsistencies, asked, not resolved -->
<section aria-labelledby="nm-ask-h">
  <div class="pd-head">
    <span class="pd-kicker">Before publishing</span>
    <h2 class="pd-h2" id="nm-ask-h">Three things we&rsquo;d ask before publishing</h2>
    <p>These are the three things we&rsquo;d like to check with you before the
       page goes live.</p>
  </div>
  <div class="pd-grid is-stretch">
    <article class="pd-card pd-card--note pd-s-4">
      <span class="pd-tag">01</span>
      <h3 class="pd-h4">Which price to show</h3>
      <p>Your specification table says price on request, and your enquiry
         form lists the Nua Ultra at &euro;70,000. Which would you like a
         homeowner to see, and what does the figure include &mdash; VAT,
         delivery, the lift, the connections?</p>
    </article>
    <article class="pd-card pd-card--note pd-s-4">
      <span class="pd-tag">02</span>
      <h3 class="pd-h4">Inside space</h3>
      <p>Your Nua Ultra page shows 38.7&nbsp;m&sup2; as the internal area, and
         the specification table gives the same figure as the footprint
         (11.4 &times; 3.4&nbsp;m). We&rsquo;ve shown it as the footprint, so
         the """ + AREA_GAP + """. Which is it?</p>
    </article>
    <article class="pd-card pd-card--note pd-s-4">
      <span class="pd-tag">03</span>
      <h3 class="pd-h4">The kitchen</h3>
      <p>A fitted kitchen is listed as an option. For someone looking at the
         Nua Ultra as a self-contained home rather than an extra room, is it
         usually part of the order?</p>
    </article>
  </div>
</section>
"""

QUESTION_STYLE_NOTE = None  # (no CSS: the template's shell styles pd-* via the design system)


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def imagery_block():
    """The hero media: the BIOBUILDS state-A pattern, with the credit in
    every frame of the gallery."""
    hero = NUA_IMAGES[0]
    out = ['        <div class="results-hero-media has-pn-gallery">',
           '          <img src="%s" alt="%s" loading="lazy" style="%s">'
           % (hero["url"], hero["alt"], FRAMING),
           '          <span class="pn-image-credit">%s</span>' % CREDIT,
           '        </div>',
           '        <div class="pn-gal-strip">']
    for n, i in enumerate(NUA_IMAGES):
        out.append('          <button type="button" class="pn-gal-thumb%s" '
                   'aria-pressed="%s" aria-label="View photograph %d of %d" '
                   'data-full="%s" data-alt="%s" data-credit="%s">'
                   '<img src="%s" alt="" style="%s"></button>'
                   % (" is-on" if n == 0 else "", "true" if n == 0 else "false",
                      n + 1, len(NUA_IMAGES), i["url"],
                      i["alt"].replace('"', "&quot;"), CREDIT, i["url"], FRAMING))
    out.append('        </div>')
    return "\n".join(out) + "\n"


def main():
    raw = TEMPLATE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != TEMPLATE_SHA:
        die("the shared template has changed since this preview was "
            "approved (sha %s). Re-check before rebuilding."
            % hashlib.sha256(raw).hexdigest()[:12])
    src = raw.decode("utf-8")

    # G0 · IMAGERY: exactly the enumerated grant, served by Nua Modular.
    rights = json.loads((HERE.parent / "image-rights-records.json")
                        .read_text(encoding="utf-8"))
    row = [r for r in rights["records"] if r.get("organisation_name") == SUPPLIER]
    if len(row) != 1:
        die("there must be exactly one Nua Modular rights record.")
    row = row[0]
    if row.get("atlas_permission_ref") != RIGHTS_RECORD \
            or (row.get("permission") or {}).get("state") != "GRANTED":
        die("the Nua Modular rights record is not the granted permission %s."
            % RIGHTS_RECORD)
    enumerated = [(a["url"], a["alt"]) for a in row.get("approved_assets") or []]
    if enumerated != [(i["url"], i["alt"]) for i in NUA_IMAGES]:
        die("the images differ from the enumerated approved_assets.")
    for i in NUA_IMAGES:
        if not i["url"].startswith(PERMITTED_PREFIX):
            die("image outside the permitted Nua Modular prefix: " + i["url"])
        if "real-field" in i["url"]:
            die("nua-ultra-real-field.jpg is a composited scene, not a "
                "photograph of the unit where it stands.")
    if row.get("required_credit") != CREDIT:
        die("the rights record requires the credit %r." % row.get("required_credit"))
    sys.path.insert(0, str(HERE))
    from preview_image_treatment import live_grant
    if not live_grant(HERE.parent, "nuamodular.com", CREDIT):
        die("image-rights-manifest.json carries no live Nua Modular grant; "
            "regenerate it from the records first.")

    # G1 · strip the template's filling instructions.
    block = re.search(r"\n<!--\s*[═=]{10,}.*?PROVIDER-LED.*?[═=]{10,}\s*-->\n",
                      src, re.S)
    if not block:
        die("the template's instruction comment was not found.")
    src = src.replace(block.group(0), "\n")

    # G1b · open on the demonstration.
    hero = re.search(r"\n<div class=\"wrap\">\n  <header class=\"hero\">.*?"
                     r"\n  </header>\n</div>\n", src, re.S)
    if not hero or "{{PROPOSITION}}" not in hero.group(0):
        die("the introductory hero block was not found.")
    src = src.replace(hero.group(0), "\n")

    # D3 · the template's frozen journey wording, exactly.
    frozen = re.findall(r'<div class="jstep[^"]*"><b>(.*?)</b><span>(.*?)</span>', src)
    if [tuple(x) for x in frozen] != [tuple(x) for x in FROZEN_JOURNEY]:
        die("the journey wording differs from the template's frozen band.")

    # G2 · journey band below the demo, Nua Modular sections between them.
    jm = re.search(r"\n<!-- FROZEN.*?\n<div class=\"journey\">.*?\n</div>\n",
                   src, re.S)
    if not jm:
        die("the frozen journey band was not found.")
    journey = jm.group(0)
    src = src.replace(journey, "\n")
    why_anchor = "<!-- WHY THIS COULD BE USEFUL"
    if src.count(why_anchor) != 1:
        die("the 'why' section anchor is not unique.")
    # the journey band is full-bleed: close and reopen the .wrap around it
    src = src.replace(why_anchor, SECTIONS + "\n</div>\n" + journey.strip("\n")
                      + "\n<div class=\"wrap\">\n\n" + why_anchor)

    old_head = "<h2>What we&rsquo;d like to explore</h2>"
    if src.count(old_head) != 1:
        die("the closing heading was not found exactly once.")
    src = src.replace(old_head, "<h2>Before anything goes live</h2>")

    # G0b · the image position, from the one list.
    if src.count(SLOT) != 1:
        die("the template's image position was not found exactly once.")
    src = src.replace(SLOT, imagery_block())

    attribution = (
        '<p class="credit-line">Everything on this page is published by %s '
        'and was read from <a href="%s" rel="noopener">your Nua Ultra '
        'page</a> and <a href="%s" rel="noopener">nuamodular.com</a> on %s. '
        'The two photographs of the Nua Ultra are %s&rsquo;s own, shown '
        'unaltered from <a href="%s" rel="noopener">nuamodular.com</a> with '
        'your permission of %s. %s</p>\n\n'
        % (SUPPLIER, ULTRA_URL, SUPPLIER_SITE, EVIDENCE_DATE, SUPPLIER,
           SUPPLIER_SITE, GRANT_DATE, CREDIT))
    if src.count("<footer>\n") != 1:
        die("the footer anchor is not unique.")
    src = src.replace("<footer>\n", attribution + "<footer>\n")

    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in src and key not in ("PROPOSITION", "LEDE"):
            die("token %s is not in the template." % needle)
        src = src.replace(needle, value)
    leftover = sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", src)))
    if leftover:
        die("unfilled tokens remain: " + ", ".join(leftover))

    # ── GUARDS ────────────────────────────────────────────────────────────
    for d in ("noindex", "nofollow", "noarchive", "nosnippet", "noimageindex"):
        if d not in src:
            die("robots directive '%s' is missing." % d)
    if 'class="pn-id pn-id--dark pn-sp"' not in src:
        die("the premium dark design is not active.")
    if src.count('<div class="pn-yp"><section id="screen-match-results">') != 1 \
            or src.count('<div class="results-hero" id="matchPrimary">') != 1:
        die("the demonstration is not inside production's Results chain.")
    if 'class="pn-photo-slot"' in src or "<b>your image here</b>" in src.lower():
        die("the empty image position survived alongside the photographs.")
    imgs = re.findall(r'<img\b[^>]*\bsrc="([^"]*)"', src)
    allowed = {i["url"] for i in NUA_IMAGES}
    if not imgs or set(imgs) - allowed:
        die("an image outside the enumerated grant: %s"
            % sorted(set(imgs) - allowed))
    if src.count('<span class="pn-image-credit">%s</span>' % CREDIT) != 1:
        die("the photograph does not carry the credit %r." % CREDIT)
    if any(re.search(r'\balt=""', m) for m in
           re.findall(r'<img\b[^>]*>', src.split('<div class="pn-gal-strip">')[0])):
        die("the main photograph has no alt text.")
    for s, t in FROZEN_JOURNEY:
        if "<b>%s</b><span>%s</span>" % (s, t) not in src:
            die("the frozen journey step %r was altered." % s)

    visible = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.S | re.I)
    visible = re.sub(r"<script\b.*?</script>", " ", visible, flags=re.S | re.I)
    text_only = re.sub(r"<[^>]+>", " ", visible)
    low = re.sub(r"\s+", " ", visible).lower()
    low_text = re.sub(r"\s+", " ", text_only).lower()

    for other in ("Modulux", "Cosy Cabins", "Hutsmith", "TRIQ", "BIOBUILDS",
                  "Superior Pergola", "Honka", "Irish Sauna", "Harvia",
                  "OGNYX", "TimberIN", "TeachNua", "Steeltech", "EcoPods",
                  "Booths"):
        if other.lower() in src.lower():
            die("another supplier's content reached the page: " + other)

    for phrase in BANNED_CLAIM_PHRASES:
        if re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", low_text):
            die("the visible page makes an unevidenced claim: %r" % phrase)
    for needle, why in MUST_SAY:
        if needle not in low:
            die("missing required wording %r: %s" % (needle, why))
    if "which is it?" not in low_text:
        die("the internal-area question to Nua Modular is no longer asked.")
    if re.search(r"(m&sup2;|m²|m2)\s*(inside|internal)|internal (floor )?area is \d", low):
        die("the page states an internal area the supplier has not settled.")
    if 'class="pv-bar"><div class="wrap">\n  <strong>' in src or "--pn-paper:#FBFAF5" in src:
        die("the old light preview shell came back.")
    if low.count(AREA_GAP) < 2:
        die("the internal-area gap must be stated both in the homeowner's "
            "things to check and in the questions to Nua Modular.")
    if low.count("&euro;70,000") != 1:
        die("the €70,000 figure must appear exactly once, inside the "
            "question, never as the displayed price.")
    price_band = re.search(r'class="results-hero-price">([^<]*)<', src)
    if not price_band or price_band.group(1) != "Price on request":
        die("the displayed price must be 'Price on request'.")

    for pattern, what in (
            (r'<source[^>]+srcset=', "a <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s; only enumerated <img> "
                "photographs are permitted." % what)
    if 'href="%s"' % SUPPLIER_SITE not in src:
        die("the page does not link back to %s itself." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the credit.")

    for word in ("partner", "approved supplier", "recommended",
                 "trusted supplier", "preferred supplier", "endorsed",
                 "commission", "referral", "exclusive"):
        if word in low_text:
            die("the page implies a relationship or mechanism: " + word)
    for phrase in BANNED_TONE_PHRASES:
        if phrase in low_text:
            die("tone: %r" % phrase)

    flat = re.sub(r"\s+", " ", text_only)
    for m in re.finditer(r"(?<![A-Za-z])nua(?![A-Za-z])", flat, re.I):
        after = flat[m.end():m.end() + 10].strip().lower()
        if not (after.startswith("modular") or after.startswith("ultra")):
            die("the bare word 'Nua' appears (%r). Always 'Nua Modular' or "
                "'Nua Ultra', so it never reads as part of PlotNua."
                % flat[max(0, m.start() - 30):m.end() + 30])
    if re.search(r"plotnua'?s? (own )?(nua|sister|sub-brand)", low_text):
        die("the page links PlotNua and Nua Modular as related.")

    if low_text.count("illustrative preview") != 1:
        die("the page must identify itself as an illustrative preview once.")
    for need in ("an extra room", "additional home",
                 "before anything goes live", "private preview"):
        if need not in low_text:
            die("required content missing: %r" % need)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("NUA MODULAR PRIVATE PREVIEW · v3 (shared template v2)")
    print("=" * 74)
    print("  ok    built from template-provider-led.html %s" % TEMPLATE_SHA[:12])
    print("  ok    premium dark design; production Results chain, CSS and skin")
    print("  ok    %d enumerated Nua Modular photographs, credited %s "
          "(granted %s)" % (len(NUA_IMAGES), CREDIT, GRANT_DATE))
    print("  ok    facts re-verified on nuamodular.com, %s" % EVIDENCE_DATE)
    print("  ok    price contradiction and area labelling asked, not resolved")
    print("  ok    'Nua' never stands alone; no partner, referral or "
          "commission wording")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
