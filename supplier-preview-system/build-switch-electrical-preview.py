#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE SWITCH ELECTRICAL PRIVATE SUPPLIER PREVIEW.

TEMPLATE: supplier-preview-system/template-provider-led.html
Reused, not forked. The same certified provider-led system that built the
TRIQBRIQ, Hutsmith, Honka, BIOBUILDS, Cosy Cabins, Irish Sauna Company and
Modulux previews. No new template, no redesign, no new CSS.

*** THE RECONCILIATION, DONE BEFORE ANYTHING WAS WRITTEN. ***

Switch Electrical Limited appears NOWHERE in PlotNua: not in Atlas, not in
atlas-match-pool.json, not in the recognition pool, not in any supplier or
contact register, not in image-rights-records.json. A full-tree search for
"switch electrical" returned nothing. So there is no existing relationship to
reflect and none may be implied -- this preview introduces a company PlotNua
has read and nothing more.

Where they are RELEVANT is not in doubt: solar PV, battery storage and home EV
charging is the subject of the live Discovery "The House as a Power Station".
That is the homeowner route named on this page, and it is named because it
exists, not to suggest Switch Electrical is in it.

*** IMAGERY STATE C. NO IMAGERY. ***

The reply was "Preview pls". That is a request to SEE the page, not a grant.
UNKNOWN IS NOT GRANTED. Their site carries real installation photography --
roof installs, Sigenergy batteries and inverters on Irish walls -- and none of
it may be downloaded, re-hosted, hotlinked or shown. The page being private
changes nothing: the publish-time rights gate treats every external image on
every deployed .html as published, because a homeowner who reaches the URL can
see it. G0 refuses any attempt to fill the image list, and G9 proves the
absence on the OUTPUT rather than trusting the input.

*** THE TRAP IN THIS SUPPLIER, AND IT IS MONEY. ***

Every other preview in this system risks overclaiming a product. This one
risks overclaiming a RETURN. The supplier's own homepage says "cut your
electricity bills" and carries three customer reviews mentioning bill
reductions; repeating any of that as a PlotNua statement would be an
unevidenced savings claim about a stranger's house. So:

  * no saving, payback, return or bill figure appears anywhere;
  * the grant is described by its published STRUCTURE (€700/kWp on the first
    2 kWp, €200/kWp to 4 kWp, capped at €1,800), never as money the homeowner
    will receive, because the amount depends on a system size nobody has
    sized yet;
  * the three published eligibility conditions travel WITH the grant figure,
    not in a footnote;
  * G8b REQUIRES the word "survey" on the page. Saying what they fit without
    saying that the system is sized on site is how a preview quietly implies
    that solar suits a property it has never seen.

SERVICE AREA. Dublin, Louth, Meath, Kildare, Wicklow "and across Leinster",
in their own words. Not nationwide, not "across Ireland", and G8 refuses both.

THE OWNER'S NAME is published on their About page and is deliberately NOT in
the homeowner-facing copy: the preview is about the business. It is recorded
here instead -- the company is owner-led by Lee Kidd, a qualified electrician.

Run: python3 build-switch-electrical-preview.py [--stage]
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/switch-electrical-preview.html")
       if STAGE else SITE / "switch-electrical-preview.html")

SUPPLIER = "Switch Electrical"
EVIDENCE_DATE = "5 October 2026"
SUPPLIER_SITE = "https://switchelectrical.ie/"
SERVICES_URL = SUPPLIER_SITE + "services"
GRANT_URL = SUPPLIER_SITE + "seai-solar-grant"
ABOUT_URL = SUPPLIER_SITE + "about"
CREDIT = "© Switch Electrical Ltd"

# IMAGERY STATE C. Empty by governance, not by oversight. G0 enforces it.
SWITCH_IMAGES = []

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT ───────────────────────────────────
# Phrases, not bare words. "free" is NOT banned: the free survey, the free
# quote and the free BER are all published. "guarantee" is not banned either,
# because the Clean Export Guarantee is the name of a real scheme -- what is
# banned is PlotNua guaranteeing something.
BANNED_CLAIM_PHRASES = [
    # MONEY. The single biggest risk on this page.
    "save you", "savings of", "guaranteed saving", "will save",
    "pay for itself", "pays for itself", "payback", "return on investment",
    "free electricity", "cut your bills", "lower your bills",
    "reduce your bills", "slash", "half your",
    # THE GRANT AS CASH IN HAND. It depends on a system size nobody has sized.
    "you will receive &euro;1,800", "you will get &euro;1,800",
    "worth &euro;1,800", "&euro;1,800 off your",
    # SERVICE AREA. Theirs is Leinster, stated five counties and no more.
    "nationwide", "across ireland", "all of ireland", "anywhere in ireland",
    "countrywide",
    # SUITABILITY WITHOUT ASSESSMENT.
    "suitable for your home", "suits your roof", "will work on your",
    "any roof", "every home",
    # RANKING AND SUPERLATIVE.
    "cheapest", "best price", "number one", "the leading", "top rated",
    # THE USUAL UNPUBLISHED THREE.
    "planning exempt", "no planning permission", "does not need planning",
    "warranty", "guaranteed for", "year guarantee",
    "lead time of", "weeks from confirmed order",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
# Not a second product section. Three things their own site leaves open, asked
# as questions. Markup is <section>, h2, h3, p and .pn-open, all already in the
# template's stylesheet, so this introduces no new CSS.
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
      <li><b>What a typical install costs.</b> Your site publishes no price,
          which makes sense when every roof is different and the quote follows
          the survey. Is there a range you&rsquo;re comfortable with us showing
          a homeowner before they call, or would you rather the first figure
          they see is yours?</li>
      <li><b>Where Leinster ends.</b> The site names Dublin, Louth, Meath,
          Kildare and Wicklow, then says &ldquo;and across Leinster&rdquo;. If
          a homeowner in Laois or Wexford reaches this screen, do you want to
          be on it?</li>
      <li><b>Battery and EV without solar.</b> The services page lists battery
          storage and EV charger installation in their own right, and the
          Sigenergy platform ties all three together. Do you take on a battery
          or a charger on its own, or do they follow a solar install?</li>
    </ul>
  </div>
</section>
"""

# ── THE COPY ───────────────────────────────────────────────────────────────
# Every figure traces to switchelectrical.ie, read live 5 October 2026.
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,

    "DEMO_HEADING": "How an Irish homeowner could reach Switch Electrical",
    "DEMO_LEDE": "A shortened example of what a homeowner would see, built "
                 "only from what your own pages publish. They arrive through "
                 "<i>The House as a Power Station</i> &mdash; our Discovery "
                 "about generating, storing and using electricity at home "
                 "&mdash; work through what their property could take, and "
                 "only then reach installers. By the time this screen appears "
                 "the thinking has already happened.",

    # PHOTO_SLOT_LINE WAS REMOVED, 5 Oct 2026, with the token it filled.
    # It carried a paragraph explaining that no Switch Electrical photography
    # was used, that their images stayed theirs, and where the pictures would
    # eventually sit. Under the certified rule the image position carries no
    # copy at all: a preview is the experience the supplier is invited into,
    # not a document explaining how it was built. The rights gate is
    # unchanged and still fails closed.

    "OFFER_NAME": "Solar PV, battery storage and EV charging",
    "VERIFIED_PRICE": "Quoted after a free survey",
    # THE DETAIL RELOCATED OUT OF FACTS 4 AND 5 LANDS HERE, not because it
    # was surplus but because the three bold slots are proof points and this
    # is the prose that explains how the engagement actually runs. Nothing
    # was dropped: the single-day install, the BER on completion, the phone
    # monitoring and the single-app point are all still on the page, in the
    # place where a reader slows down rather than scans.
    "VERIFIED_PRICE_BASIS": "Switch Electrical publish no price list. The "
                            "survey and the quote are free, and the system is "
                            "sized to the roof and to how the household "
                            "actually uses electricity. The SEAI Solar "
                            "Electricity Grant is separate money and is paid "
                            "by SEAI to the homeowner, not to the installer. "
                            "Installation is usually a single day on site, "
                            "followed by switch-on, a BER on completion and "
                            "monitoring set up on the homeowner&rsquo;s "
                            "phone; generation, storage and car charging are "
                            "then watched and managed in one Sigenergy app.",

    "VERIFIED_FACT_1_LABEL": "What they fit",
    "VERIFIED_FACT_1_VALUE": "Solar PV, battery storage and home EV chargers, "
                             "plus the electrical work around them &mdash; "
                             "consumer unit upgrades, fuse board work and "
                             "inverter systems",
    "VERIFIED_FACT_2_LABEL": "Where",
    "VERIFIED_FACT_2_VALUE": "Based in Dublin. Dublin, Louth, Meath, Kildare "
                             "and Wicklow are named, and the site adds "
                             "&ldquo;and across Leinster&rdquo;",
    # FACTS 3-5 ARE SHORT BOLD PROOF POINTS, not sentences. The template
    # gives these three slots a <b> and no value span, so anything long
    # renders as a wall of bold body text and buries the label/value pair
    # above it -- worst at 390px, where .pn-facts li stacks. They are now
    # scannable at a glance and the explanation lives in the prose.
    # NOTHING VERIFIED WAS LOST. The grant's own requirement for an
    # SEAI-registered installer is already stated verbatim in
    # THINGS_TO_CHECK below, so dropping it from fact 3 removes a
    # duplication rather than a fact.
    "VERIFIED_FACT_3": "SEAI-registered installer No. 50744 &middot; Safe "
                       "Electric No. A6580",
    "VERIFIED_FACT_4": "Free survey, free quote, SEAI grant paperwork handled",
    "VERIFIED_FACT_5": "Battery, inverter and EV charging on one Sigenergy "
                       "platform",

    # THE ONE HONEST LINE. It carries the grant's real structure and all three
    # published eligibility conditions, because a figure without them is the
    # part a homeowner would misread.
    "THINGS_TO_CHECK": "there is no price on this page because Switch "
                       "Electrical publish none &mdash; the figure follows the "
                       "survey. The grant is not a flat amount either: SEAI "
                       "pay &euro;700 per kWp on the first 2 kWp and &euro;200 "
                       "per kWp up to 4 kWp, capped at &euro;1,800, so what a "
                       "household gets depends on a system nobody has sized "
                       "yet. Three conditions come with it, all published: the "
                       "home must have been built and occupied before 2021, "
                       "the work must be done by an SEAI-registered installer, "
                       "and a BER assessment is carried out after the works. "
                       "Export payments under the Clean Export Guarantee come "
                       "from the electricity supplier, not from the installer.",

    # PERSONALISATION GUARDRAIL §6 — LOCALITY ONLY. The journey asks for an
    # Eircode and simplifyLocalityDisplay() reduces it to exactly this. It asks
    # nothing about the roof, its pitch, its orientation, the shading or the
    # existing consumer unit -- and on a solar supplier every one of those is
    # a temptation, because every one of them genuinely decides the job.
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "Shown for a homeowner in Co. Meath, from the location "
                       "they gave us. We don&rsquo;t ask them which way the "
                       "roof faces, what shades it or what their consumer unit "
                       "looks like &mdash; so we wouldn&rsquo;t pretend to "
                       "know. Those stay as things for your survey.",

    "WHY_1_LABEL": "THE GRANT, UNDERSTOOD BEFORE THE CALL",
    "WHY_1_TEXT": "The SEAI grant is the first thing a homeowner asks about "
                  "and the thing they most often have wrong. We show how it "
                  "is actually calculated and what it depends on, so the "
                  "conversation starts past the misunderstanding rather than "
                  "inside it.",
    "WHY_2_LABEL": "ONE TRADE, THREE JOBS",
    "WHY_2_TEXT": "Panels, a battery and a charger are usually three separate "
                  "decisions for a homeowner and one job for an electrician. "
                  "Your own pages make that case clearly, and it is easier to "
                  "make on a page the homeowner is already using to think "
                  "with.",
    "WHY_3_LABEL": "ARRIVING WITH A DEVELOPED IDEA",
    "WHY_3_TEXT": "By the time a homeowner reaches you through PlotNua, they "
                  "have looked at what their own property could take and "
                  "decided this is worth pricing. They arrive with a developed "
                  "idea rather than an open question, and that is the kind of "
                  "enquiry we are trying to send you.",

    "CLOSING_PROPOSITION": "Does this represent Switch Electrical accurately "
                           "for an Irish homeowner?",
    "CLOSING_SUPPORT": "If anything on this page is wrong, out of date or "
                       "missing, tell us and we&rsquo;ll correct it before "
                       "anything is published.",

    "DATE": EVIDENCE_DATE,
}


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY MAY NOT APPEAR WHILE PERMISSION IS UNKNOWN.
    if SWITCH_IMAGES:
        die("Switch Electrical imagery was added to this builder, but the "
            "reply was \"Preview pls\" — a request to see the page, not a "
            "grant. UNKNOWN is not GRANTED, and the publish-time rights gate "
            "refuses external images on any deployed page. Get written "
            "permission and a manifest row first.")

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

    # G3 · THE IMAGE POSITION CARRIES NO COPY. Certified rule, 5 Oct 2026.
    # This replaces the old relabel step, which wrote a governance paragraph
    # into the hero. The guard now runs the other way: it refuses if the
    # image position has acquired any copy at all, and refuses if the
    # rights-process vocabulary has leaked anywhere into the visible page.
    slot = re.search(r'<div class="pn-photo-slot"[^>]*>(.*?)</div>',
                     src, flags=re.S)
    if not slot:
        die("the photo slot was not found. The template has moved.")
    if slot.group(1).strip():
        die("the image position carries copy: %r. Under the certified rule "
            "it stays empty, and the rights process is not narrated to the "
            "supplier." % slot.group(1).strip()[:90])

    # G3c · ATTRIBUTION. Every statement is their published information, so
    # the page says where it came from and links back.
    attribution = (
        '          <p class="credit-line">Everything on this page is published '
        'by %s and was read from '
        '<a href="%s" rel="noopener">your services page</a>, '
        '<a href="%s" rel="noopener">your SEAI grant page</a> and '
        '<a href="%s" rel="noopener">switchelectrical.ie</a> on %s. '
        'The grant figures are SEAI&rsquo;s. '
        'No %s photography is used anywhere on this page. '
        '%s'
        '</p>\n'
        % (SUPPLIER, SERVICES_URL, GRANT_URL, SUPPLIER_SITE, EVIDENCE_DATE,
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

    # PREVIEW-POLISH-001 WAS REMOVED WITH THE SECTION IT STYLED.
    # It injected an h3 size rule because "Where your imagery would go" read
    # as body copy. That subsection is gone under the certified rule, the
    # page now has no h3 at all, and a CSS rule with nothing to style is
    # dead weight in a file a supplier can View Source on. A guard below
    # asserts the element really is absent, so this is a removal with a
    # proof rather than an assumption.

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

    # G3d · THE RIGHTS PROCESS IS NOT NARRATED TO THE SUPPLIER.
    # Certified rule, 5 Oct 2026. The gate stays fail-closed in code; what it
    # must not do is appear in the copy. These phrases are the ones the old
    # photo-slot paragraph and the "Where your imagery would go" subsection
    # used, so the guard is pointed at the exact failure that happened rather
    # than at a vague idea of process language. The factual line in the
    # credit footer that no photography is used is deliberately NOT caught:
    # it is a one-clause statement of fact in the attribution, not a passage
    # explaining the permission workflow.
    for phrase in ("where they would sit", "where your imagery would go",
                   "where your photography would", "stay yours until",
                   "images stay yours", "imagery waits until",
                   "until you tell us otherwise",
                   "before anything is published, so your"):
        if phrase in low:
            die("the page narrates the image-rights process to the supplier: "
                "%r. The gate stays fail-closed in code; it does not get "
                "explained in the copy." % phrase)
    if "<h3" in src:
        die("an h3 appeared. The imagery subsection was removed under the "
            "certified rule and its CSS rule was removed with it, so a new "
            "h3 would render unstyled.")

    # G6 · NO OTHER SUPPLIER'S CONTENT. Sigenergy is deliberately absent from
    # this list: it is the platform Switch Electrical publish as the kit they
    # fit, and naming the manufacturer is the accurate thing to do, not a leak.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Irish Sauna", "Harvia", "OGNYX", "TankTribe",
                  "Modulux", "Sauna Experts"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · The frozen journey band travelled byte-for-byte.
    if journey.strip("\n") not in src:
        die("the frozen journey band was altered in transit, not relocated.")

    # G8 · NO UNEVIDENCED CLAIM.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support, or states as PlotNua's what is the supplier's "
                "own marketing: %r." % phrase)

    # G8b · THE ASSESSMENT MUST BE STATED, not merely not-contradicted.
    # Describing what a solar installer fits, without saying that the system
    # is sized on site, implies suitability for a property nobody has seen.
    # This is the positive half of the suitability rule and the reason the
    # bans above are not enough on their own.
    if "survey" not in low:
        die("the page never mentions a survey. Listing what Switch Electrical "
            "fit without saying the system is sized on site implies the work "
            "suits a property nobody has looked at.")
    if "seai" not in low:
        die("the page does not name SEAI, so the grant figures read as the "
            "installer's offer rather than a state scheme's.")
    if "before 2021" not in low:
        die("the page states the grant without its published eligibility "
            "conditions. The figure without the conditions is the half a "
            "homeowner misreads.")

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
    print("SWITCH ELECTRICAL PRIVATE PREVIEW")
    print("=" * 74)
    print("  ok    15 guards passed")
    print("  ok    0 external images — imagery state C, permission unknown")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    no saving, payback, bill, nationwide or suitability claim")
    print("  ok    survey, SEAI and the 2021 eligibility condition all stated")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY. The deployed tree is untouched and the "
              "publication gate is unaffected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
